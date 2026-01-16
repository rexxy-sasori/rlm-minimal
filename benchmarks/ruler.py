from .base import BaseBenchmark
from .config import RULERConfig
from typing import Dict, Any, List, Optional
import random
import time
import json
import os

class RULERBenchmark(BaseBenchmark):
    """RULER benchmark implementation for needle-in-haystack testing."""
    
    def __init__(self, config: Dict[str, Any]):
        """Initialize RULER benchmark."""
        if isinstance(config, RULERConfig):
            config = config.to_dict()
        super().__init__(config)
        self.needle_positions = config.get("needle_positions", ["beginning", "middle", "end"])
        self.needles_per_context = config.get("needles_per_context", 1)
        self.dataset = []
    
    def load_dataset(self):
        """Load or generate RULER dataset."""
        self.dataset = []
        context_lengths = self.config.get("context_lengths", [1000, 5000])
        
        # Calculate tasks per combination
        max_tasks = self.config.get("max_tasks", 5)
        tasks_per_combination = max(1, max_tasks // len(context_lengths) // len(self.needle_positions))
        
        for context_length in context_lengths:
            for position in self.needle_positions:
                for i in range(tasks_per_combination):
                    task = self.generate_task(context_length, position)
                    self.dataset.append(task)
        
        # Ensure we reach at least the requested number of tasks
        while len(self.dataset) < max_tasks:
            context_length = random.choice(context_lengths)
            position = random.choice(self.needle_positions)
            task = self.generate_task(context_length, position)
            self.dataset.append(task)
        
        random.shuffle(self.dataset)
        if len(self.dataset) > max_tasks:
            self.dataset = self.dataset[:max_tasks]
    
    def generate_task(self, context_length: int, needle_position: str) -> Dict[str, Any]:
        """Generate a single RULER task."""
        # Generate random haystack
        haystack = self._generate_haystack(context_length)
        
        # Generate random needle
        needle = self._generate_needle()
        
        # Insert needle at specified position
        context, needle_index = self._insert_needle(haystack, needle, needle_position)
        
        task = {
            "context": context,
            "needle": needle,
            "needle_position": needle_position,
            "context_length": len(context),
            "needle_index": needle_index,
            "query": f"Find the random string that starts with 'NEEDLE:' in the context above."
        }
        
        return task
    
    def _generate_haystack(self, target_length: int) -> str:
        """Generate random haystack text."""
        import string
        words = []
        current_length = 0
        
        while current_length < target_length:
            word = ''.join(random.choices(string.ascii_lowercase, k=random.randint(1, 10)))
            words.append(word)
            current_length += len(word) + 1  # +1 for space
        
        haystack = ' '.join(words)
        return haystack[:target_length]
    
    def _generate_needle(self) -> str:
        """Generate random needle string."""
        import string
        random_part = ''.join(random.choices(string.ascii_uppercase + string.digits, k=10))
        return f"NEEDLE:{random_part}"
    
    def _insert_needle(self, haystack: str, needle: str, position: str) -> tuple[str, int]:
        """Insert needle at specified position in haystack."""
        haystack_length = len(haystack)
        needle_length = len(needle)
        
        if position == "beginning":
            index = 0
        elif position == "middle":
            index = haystack_length // 2
        elif position == "end":
            index = haystack_length - needle_length - 100  # Leave some space at end
        else:
            raise ValueError(f"Invalid position: {position}")
        
        # Ensure index is within bounds
        index = max(0, min(index, haystack_length - needle_length))
        
        new_context = haystack[:index] + needle + haystack[index + needle_length:]
        return new_context, index
    
    def evaluate(self, model):
        """Run RULER evaluation on model."""
        if not self.dataset:
            self.load_dataset()
        
        self.start_timer()
        results = []
        
        for i, task in enumerate(self.dataset):
            if i >= self.config.get("max_tasks", 100):
                break
            
            if self.config.get("verbose", False):
                print(f"Evaluating task {i+1}/{len(self.dataset)}...")
            
            start_time = time.time()
            try:
                # Create messages for model
                messages = [
                    {"role": "user", "content": task["query"] + "\n\n" + task["context"]}
                ]
                
                # Get model response
                response = model.completion(messages)
                response_text = response.get("choices", [{}])[0].get("message", {}).get("content", "")
                
                # Check if needle is in response
                correct = task["needle"] in response_text
                
                task_result = {
                    "task_id": i,
                    "context_length": task["context_length"],
                    "needle_position": task["needle_position"],
                    "needle": task["needle"],
                    "response": response_text,
                    "correct": correct,
                    "time_taken": time.time() - start_time,
                    "tokens_processed": len(task["context"]) // 4  # Rough token estimate
                }
                
                results.append(task_result)
                
            except Exception as e:
                print(f"Error evaluating task {i}: {e}")
                task_result = {
                    "task_id": i,
                    "context_length": task["context_length"],
                    "needle_position": task["needle_position"],
                    "needle": task["needle"],
                    "response": "",
                    "correct": False,
                    "time_taken": time.time() - start_time,
                    "error": str(e)
                }
                results.append(task_result)
        
        self.stop_timer()
        self.results = results
        return results
    
    def compute_metrics(self, results: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Calculate RULER benchmark metrics."""
        if not results:
            return {"error": "No results available"}
        
        # Overall accuracy
        correct = sum(1 for r in results if r.get("correct", False))
        total = len(results)
        overall_accuracy = correct / total if total > 0 else 0
        
        # Position-based accuracy
        position_accuracy = {}
        for position in self.needle_positions:
            position_results = [r for r in results if r.get("needle_position") == position]
            if position_results:
                position_correct = sum(1 for r in position_results if r.get("correct", False))
                position_accuracy[position] = position_correct / len(position_results)
        
        # Context length analysis
        length_accuracy = {}
        for length in self.config.get("context_lengths", [100000, 1000000, 10000000]):
            length_results = [r for r in results if r.get("context_length", 0) <= length + 100000]
            if length_results:
                length_correct = sum(1 for r in length_results if r.get("correct", False))
                length_accuracy[f"{length} tokens"] = length_correct / len(length_results)
        
        # Time analysis
        total_time = sum(r.get("time_taken", 0) for r in results)
        avg_time_per_task = total_time / total if total > 0 else 0
        
        # Token analysis
        total_tokens = sum(r.get("tokens_processed", 0) for r in results)
        avg_tokens_per_task = total_tokens / total if total > 0 else 0
        
        metrics = {
            "overall_accuracy": f"{overall_accuracy:.2%}",
            "position_accuracy": position_accuracy,
            "length_accuracy": length_accuracy,
            "total_tasks": total,
            "correct_tasks": correct,
            "average_time_per_task": f"{avg_time_per_task:.2f}s",
            "total_evaluation_time": f"{total_time:.2f}s",
            "average_tokens_per_task": f"{avg_tokens_per_task:.0f}",
            "total_tokens_processed": f"{total_tokens:,}"
        }
        
        # Calculate context rot (degradation from beginning to end)
        if "beginning" in position_accuracy and "end" in position_accuracy:
            beginning_acc = position_accuracy["beginning"]
            end_acc = position_accuracy["end"]
            context_rot = beginning_acc - end_acc
            metrics["context_rot"] = f"{context_rot:.2%}"
        
        return metrics
