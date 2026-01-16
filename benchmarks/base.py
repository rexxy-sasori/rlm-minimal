from abc import ABC, abstractmethod
from typing import Dict, Any, List, Optional
import time
import json

class BaseBenchmark(ABC):
    """Abstract base class for all benchmarks."""
    
    def __init__(self, config: Dict[str, Any]):
        """Initialize benchmark with configuration."""
        self.config = config
        self.results = []
        self.start_time = None
        self.end_time = None
    
    @abstractmethod
    def load_dataset(self):
        """Load and prepare benchmark dataset."""
        pass
    
    @abstractmethod
    def evaluate(self, model):
        """Run evaluation on a given model."""
        pass
    
    @abstractmethod
    def compute_metrics(self, results: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Calculate performance metrics."""
        pass
    
    def report(self, results: List[Dict[str, Any]]):
        """Generate human-readable report."""
        metrics = self.compute_metrics(results)
        report = self._generate_report(results, metrics)
        print(report)
        return report
    
    def _generate_report(self, results: List[Dict[str, Any]], metrics: Dict[str, Any]) -> str:
        """Generate basic report structure."""
        report_lines = [
            f"{'='*60}",
            f"{self.__class__.__name__} Results",
            f"{'='*60}",
        ]
        
        for key, value in metrics.items():
            report_lines.append(f"{key}: {value}")
        
        report_lines.append(f"{'='*60}")
        report_lines.append(f"Total tasks: {len(results)}")
        
        if self.start_time and self.end_time:
            duration = self.end_time - self.start_time
            report_lines.append(f"Evaluation time: {duration:.2f} seconds")
        
        report_lines.append(f"{'='*60}")
        return "\n".join(report_lines)
    
    def start_timer(self):
        """Start evaluation timer."""
        self.start_time = time.time()
    
    def stop_timer(self):
        """Stop evaluation timer."""
        self.end_time = time.time()
    
    def save_results(self, filename: str):
        """Save results to JSON file."""
        data = {
            "benchmark": self.__class__.__name__,
            "config": self.config,
            "results": self.results,
            "metrics": self.compute_metrics(self.results),
            "start_time": self.start_time,
            "end_time": self.end_time,
            "duration": self.end_time - self.start_time if self.start_time and self.end_time else None,
        }
        
        with open(filename, 'w') as f:
            json.dump(data, f, indent=2)
    
    def load_results(self, filename: str) -> List[Dict[str, Any]]:
        """Load results from JSON file."""
        with open(filename, 'r') as f:
            data = json.load(f)
        self.results = data.get("results", [])
        return self.results
