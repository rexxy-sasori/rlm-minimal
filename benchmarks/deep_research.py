from .base import BaseBenchmark
from .config import DeepResearchConfig
from typing import Dict, Any, List, Optional
import random
import time
import json
import os
from datasets import load_dataset, Dataset
import subprocess
import sys

class DeepResearchBenchmark(BaseBenchmark):
    """Deep Research benchmark implementation for BrowseComp-Plus style tasks."""
    
    def __init__(self, config: Dict[str, Any]):
        """Initialize Deep Research benchmark."""
        if isinstance(config, DeepResearchConfig):
            config = config.to_dict()
        super().__init__(config)
        self.research_topics = [
            "artificial intelligence safety",
            "renewable energy technologies",
            "medical research breakthroughs",
            "climate change mitigation",
            "space exploration",
            "quantum computing",
            "blockchain technology",
            "synthetic biology",
            "neuroscience advances",
            "sustainable agriculture"
        ]
        self.dataset = []
    
    def load_dataset(self):
        """Load or generate Deep Research dataset."""
        # Check if using BrowseComp-Plus
        use_browsecomp_plus = self.config.get("use_browsecomp_plus", False)
        
        if use_browsecomp_plus:
            self._load_browsecomp_plus_dataset()
        else:
            dataset_path = self.config.get("dataset_path")
            
            if dataset_path and os.path.exists(dataset_path):
                self._load_from_file(dataset_path)
            else:
                self._generate_synthetic_dataset()
        
        # Ensure we don't exceed max tasks
        if len(self.dataset) > self.config.get("max_tasks", 30):
            self.dataset = self.dataset[:self.config.get("max_tasks", 30)]
    
    def _setup_browsecomp_plus(self, output_dir: str = "data"):
        """Setup BrowseComp-Plus dataset."""
        os.makedirs(output_dir, exist_ok=True)
        
        # Download queries and relevance judgments
        print("Downloading BrowseComp-Plus dataset...")
        try:
            # Check if datasets is installed
            subprocess.run([sys.executable, "-m", "pip", "install", "datasets"], 
                          check=True, capture_output=True)
            
            # Download and decrypt dataset
            decrypt_script = """
from datasets import load_dataset
import json
import os

# Download queries
print("Downloading queries...")
queries = load_dataset("Tevatron/browsecomp-plus", split="queries")
queries.to_json(os.path.join("data", "queries.jsonl"), lines=True)

# Download corpus (not obfuscated)
print("Downloading corpus...")
corpus = load_dataset("Tevatron/browsecomp-plus-corpus", split="train")
corpus.to_json(os.path.join("data", "corpus.jsonl"), lines=True)

print("BrowseComp-Plus setup completed successfully!")
"""
            
            with open("download_browsecomp_plus.py", "w") as f:
                f.write(decrypt_script)
            
            subprocess.run([sys.executable, "download_browsecomp_plus.py"], 
                          check=True, capture_output=True)
            
            os.remove("download_browsecomp_plus.py")
            return True
        except Exception as e:
            print(f"Error setting up BrowseComp-Plus: {e}")
            return False
    
    def _load_browsecomp_plus_dataset(self):
        """Load BrowseComp-Plus dataset."""
        data_dir = self.config.get("browsecomp_plus_data_dir", "data")
        
        # Check if dataset is already downloaded
        if not os.path.exists(os.path.join(data_dir, "queries.jsonl")):
            if not self._setup_browsecomp_plus(data_dir):
                print("Falling back to synthetic dataset generation...")
                self._generate_synthetic_dataset()
                return
        
        try:
            print("Loading BrowseComp-Plus dataset...")
            
            # Load queries
            queries = load_dataset("json", data_files=os.path.join(data_dir, "queries.jsonl"), split="train")
            
            # Load corpus
            corpus = load_dataset("json", data_files=os.path.join(data_dir, "corpus.jsonl"), split="train")
            
            # Convert to dictionaries for faster access
            corpus_dict = {item["docid"]: item for item in corpus}
            
            # Process tasks
            self.dataset = []
            max_tasks = self.config.get("max_tasks", 30)
            
            for i, query in enumerate(queries):
                if i >= max_tasks:
                    break
                
                # Get relevant documents for this query
                relevant_docids = query.get("relevant_docids", [])
                sources = []
                
                # Collect relevant sources
                for docid in relevant_docids[:5]:  # Use up to 5 relevant documents
                    if docid in corpus_dict:
                        doc = corpus_dict[docid]
                        sources.append({
                            "type": "research_paper",
                            "title": doc.get("title", "Unknown Title"),
                            "content": doc.get("text", ""),
                            "docid": docid
                        })
                
                if sources:
                    task = {
                        "topic": query.get("topic", "general_research"),
                        "sources": sources,
                        "query": query.get("query", ""),
                        "correct_answer": query.get("answer", ""),
                        "context": self._format_sources_for_context(sources),
                        "context_length": len(self._format_sources_for_context(sources)),
                        "query_id": query.get("query_id", str(i)),
                        "relevant_docids": relevant_docids
                    }
                    self.dataset.append(task)
            
            print(f"Loaded {len(self.dataset)} BrowseComp-Plus tasks")
            
            if not self.dataset:
                print("No tasks loaded, falling back to synthetic dataset...")
                self._generate_synthetic_dataset()
                
        except Exception as e:
            print(f"Error loading BrowseComp-Plus dataset: {e}")
            print("Falling back to synthetic dataset generation...")
            self._generate_synthetic_dataset()
    
    def _load_from_file(self, dataset_path: str):
        """Load dataset from JSON file."""
        with open(dataset_path, 'r') as f:
            self.dataset = json.load(f)
    
    def _generate_synthetic_dataset(self):
        """Generate synthetic Deep Research dataset."""
        self.dataset = []
        
        max_tasks = self.config.get("max_tasks", 3)
        tasks_per_topic = max(1, max_tasks // len(self.research_topics))
        
        for topic in self.research_topics:
            for i in range(tasks_per_topic):
                task = self.generate_research_task(topic)
                self.dataset.append(task)
        
        # Ensure we reach at least the requested number of tasks
        while len(self.dataset) < max_tasks:
            topic = random.choice(self.research_topics)
            task = self.generate_research_task(topic)
            self.dataset.append(task)
        
        random.shuffle(self.dataset)
    
    def generate_research_task(self, topic: str) -> Dict[str, Any]:
        """Generate a single deep research task."""
        # Generate multiple information sources
        sources = self._generate_multiple_sources(topic)
        
        # Generate research question
        question = self._generate_research_question(topic, sources)
        
        # Generate correct answer by synthesizing information
        correct_answer = self._synthesize_answer(sources, question)
        
        task = {
            "topic": topic,
            "sources": sources,
            "query": question,
            "correct_answer": correct_answer,
            "context": self._format_sources_for_context(sources),
            "context_length": len(self._format_sources_for_context(sources))
        }
        
        return task
    
    def _generate_multiple_sources(self, topic: str) -> List[Dict[str, Any]]:
        """Generate multiple information sources for research."""
        sources = []
        
        # Generate different types of sources
        source_types = [
            ("research_paper", self._generate_research_paper),
            ("news_article", self._generate_news_article),
            ("blog_post", self._generate_blog_post),
            ("technical_report", self._generate_technical_report),
            ("expert_opinion", self._generate_expert_opinion)
        ]
        
        # Generate 3-5 sources
        num_sources = random.randint(3, 5)
        selected_types = random.sample(source_types, min(num_sources, len(source_types)))
        
        for source_type, generator in selected_types:
            source = generator(topic)
            source["type"] = source_type
            sources.append(source)
        
        return sources
    
    def _generate_research_paper(self, topic: str) -> Dict[str, Any]:
        """Generate research paper source."""
        abstract = self._generate_research_abstract(topic)
        findings = self._generate_research_findings(topic)
        
        return {
            "title": f"Research Paper: {topic.title()} - Recent Advances",
            "authors": [f"Dr. {self._generate_name()}", f"Prof. {self._generate_name()}"],
            "abstract": abstract,
            "findings": findings,
            "publication_date": f"2024-{random.randint(1, 12):02d}-{random.randint(1, 28):02d}",
            "journal": f"Journal of {topic.title().replace(' ', '')} Research"
        }
    
    def _generate_news_article(self, topic: str) -> Dict[str, Any]:
        """Generate news article source."""
        headline = self._generate_news_headline(topic)
        content = self._generate_news_content(topic)
        
        return {
            "title": headline,
            "author": f"Journalist {self._generate_name()}",
            "content": content,
            "publication_date": f"2024-{random.randint(1, 12):02d}-{random.randint(1, 28):02d}",
            "publication": random.choice(["Science Daily", "Nature News", "Technology Review", "The Guardian", "New York Times"])
        }
    
    def _generate_blog_post(self, topic: str) -> Dict[str, Any]:
        """Generate blog post source."""
        title = self._generate_blog_title(topic)
        content = self._generate_blog_content(topic)
        
        return {
            "title": title,
            "author": f"Blogger {self._generate_name()}",
            "content": content,
            "publication_date": f"2024-{random.randint(1, 12):02d}-{random.randint(1, 28):02d}",
            "blog": f"{topic.replace(' ', '')} Insider"
        }
    
    def _generate_technical_report(self, topic: str) -> Dict[str, Any]:
        """Generate technical report source."""
        summary = self._generate_report_summary(topic)
        details = self._generate_report_details(topic)
        
        return {
            "title": f"Technical Report: {topic.title()} Analysis",
            "authors": [f"Engineer {self._generate_name()}", f"Researcher {self._generate_name()}"],
            "summary": summary,
            "details": details,
            "publication_date": f"2024-{random.randint(1, 12):02d}-{random.randint(1, 28):02d}",
            "organization": random.choice(["MIT Technology Review", "Stanford Research Institute", "NASA", "CERN", "National Labs"])
        }
    
    def _generate_expert_opinion(self, topic: str) -> Dict[str, Any]:
        """Generate expert opinion source."""
        opinion = self._generate_expert_statement(topic)
        background = self._generate_expert_background(topic)
        
        return {
            "title": f"Expert Opinion on {topic.title()}",
            "expert": f"Dr. {self._generate_name()}",
            "background": background,
            "opinion": opinion,
            "publication_date": f"2024-{random.randint(1, 12):02d}-{random.randint(1, 28):02d}",
            "source": random.choice(["Expert Panel Discussion", "Interview", "Keynote Speech", "Podcast"])
        }
    
    def _generate_research_abstract(self, topic: str) -> str:
        """Generate research paper abstract."""
        sentences = [
            f"This study examines recent developments in {topic}.",
            f"We conducted experiments to evaluate {topic.replace(' ', '')} technologies.",
            f"Our findings suggest a promising direction for future {topic} research.",
            f"The results indicate significant improvements in {topic.replace(' ', '')} methodologies.",
            f"We propose a novel approach to address {topic} challenges."
        ]
        return " ".join(sentences)
    
    def _generate_research_findings(self, topic: str) -> List[str]:
        """Generate research paper findings."""
        findings = []
        for i in range(3):
            findings.append(f"Finding {i+1}: {self._generate_fact_statement(topic)}")
        return findings
    
    def _generate_news_headline(self, topic: str) -> str:
        """Generate news headline."""
        verbs = ["Breakthrough", "Advance", "Discovery", "Progress", "Innovation"]
        verb = random.choice(verbs)
        return f"{verb} in {topic.title()} Promises New Possibilities"
    
    def _generate_news_content(self, topic: str) -> str:
        """Generate news article content."""
        paragraphs = [
            f"A recent development in {topic} has caught the attention of researchers worldwide.",
            f"Experts say this could revolutionize how we approach {topic} challenges.",
            f"The discovery was made by a team of scientists at a leading research institution.",
            f"This breakthrough builds on previous work in the {topic} field.",
            f"Industry leaders are already exploring applications of this new technology."
        ]
        return "\n\n".join(paragraphs)
    
    def _generate_blog_title(self, topic: str) -> str:
        """Generate blog post title."""
        formats = [
            "What You Need to Know About {topic}",
            "The Future of {topic} is Here",
            "Inside Look: {topic} Developments",
            "Expert Insights on {topic}",
            "Navigating the World of {topic}"
        ]
        format_choice = random.choice(formats)
        return format_choice.format(topic=topic.title())
    
    def _generate_blog_content(self, topic: str) -> str:
        """Generate blog post content."""
        paragraphs = [
            f"As someone who's been following {topic} for years, I'm excited about recent developments.",
            f"There are several key trends shaping the future of {topic}.",
            f"One of the most promising areas is {self._generate_subtopic(topic)}.",
            f"However, there are still significant challenges to overcome in {topic}.",
            f"I believe we'll see major progress in {topic} within the next few years."
        ]
        return "\n\n".join(paragraphs)
    
    def _generate_report_summary(self, topic: str) -> str:
        """Generate technical report summary."""
        sentences = [
            f"This report provides a comprehensive analysis of {topic} technologies.",
            f"We evaluate current state-of-the-art approaches to {topic} challenges.",
            f"The report identifies key opportunities and obstacles in {topic} research.",
            f"We recommend several strategies to accelerate progress in {topic}.",
            f"Our analysis suggests a pathway forward for {topic} development."
        ]
        return " ".join(sentences)
    
    def _generate_report_details(self, topic: str) -> List[str]:
        """Generate technical report details."""
        details = []
        for i in range(4):
            details.append(f"Detail {i+1}: {self._generate_technical_statement(topic)}")
        return details
    
    def _generate_expert_statement(self, topic: str) -> str:
        """Generate expert opinion statement."""
        statements = [
            f"Based on my experience in {topic}, I believe we're at a critical juncture.",
            f"The recent work in {topic} shows tremendous promise but requires careful consideration.",
            f"I see both opportunities and risks in the direction {topic} research is taking.",
            f"We need to balance innovation with responsibility in {topic} development.",
            f"The future of {topic} depends on collaboration across disciplines."
        ]
        return " ".join(statements)
    
    def _generate_expert_background(self, topic: str) -> str:
        """Generate expert background information."""
        backgrounds = [
            f"PhD in {topic.replace(' ', '')} with 20 years of research experience",
            f"Leading expert in {topic} with numerous publications",
            f"Former director of {topic.replace(' ', '')} research at a major institution",
            f"Recipient of awards for contributions to {topic} field",
            f"Advisor to governments on {topic} policy"
        ]
        return random.choice(backgrounds)
    
    def _generate_research_question(self, topic: str, sources: List[Dict[str, Any]]) -> str:
        """Generate research question that requires synthesizing information."""
        question_templates = [
            f"What are the current challenges and opportunities in {topic} based on recent developments?",
            f"How do different experts view the future direction of {topic}?",
            f"What breakthroughs in {topic} have been reported in recent sources?",
            f"What are the potential applications of recent {topic} advancements?",
            f"How do the findings from different sources on {topic} compare and contrast?"
        ]
        return random.choice(question_templates)
    
    def _synthesize_answer(self, sources: List[Dict[str, Any]], question: str) -> str:
        """Synthesize correct answer from multiple sources."""
        points = []
        
        # Extract key points from each source
        for i, source in enumerate(sources):
            if source["type"] == "research_paper":
                points.extend(source.get("findings", []))
            elif source["type"] == "news_article":
                points.append(f"News: {source.get('content', '').split('.')[0]}.")
            elif source["type"] == "expert_opinion":
                points.append(f"Expert: {source.get('opinion', '').split('.')[0]}.")
        
        # Synthesize into coherent answer
        answer = "Based on the information from multiple sources:\n\n"
        answer += "\n".join(f"- {point}" for point in points[:5])
        answer += "\n\nThis synthesis indicates a promising direction for future research and applications."
        
        return answer
    
    def _format_sources_for_context(self, sources: List[Dict[str, Any]]) -> str:
        """Format multiple sources into a single context string."""
        context_parts = []
        
        for i, source in enumerate(sources):
            context_parts.append(f"=== SOURCE {i+1}: {source.get('title', 'Unknown')} ===")
            context_parts.append(f"Type: {source.get('type', 'Unknown')}")
            context_parts.append(f"Author: {source.get('author', source.get('expert', 'Unknown'))}")
            context_parts.append(f"Date: {source.get('publication_date', 'Unknown')}")
            
            # Add content based on source type
            if source["type"] == "research_paper":
                context_parts.append(f"Abstract: {source.get('abstract', '')}")
                context_parts.append(f"Findings: {', '.join(source.get('findings', []))}")
            elif source["type"] == "news_article":
                context_parts.append(f"Content: {source.get('content', '')}")
            elif source["type"] == "blog_post":
                context_parts.append(f"Content: {source.get('content', '')}")
            elif source["type"] == "technical_report":
                context_parts.append(f"Summary: {source.get('summary', '')}")
                context_parts.append(f"Details: {', '.join(source.get('details', []))}")
            elif source["type"] == "expert_opinion":
                context_parts.append(f"Background: {source.get('background', '')}")
                context_parts.append(f"Opinion: {source.get('opinion', '')}")
            
            context_parts.append("")
        
        return "\n".join(context_parts)
    
    def _generate_fact_statement(self, topic: str) -> str:
        """Generate factual statement about topic."""
        verbs = ["shows", "demonstrates", "indicates", "suggests", "confirms"]
        objects = ["improvements", "advantages", "challenges", "opportunities", "trends"]
        verb = random.choice(verbs)
        obj = random.choice(objects)
        return f"Recent research {verb} significant {obj} in {topic}."
    
    def _generate_technical_statement(self, topic: str) -> str:
        """Generate technical statement about topic."""
        adjectives = ["technical", "methodological", "practical", "theoretical", "implementation"]
        nouns = ["challenges", "solutions", "approaches", "frameworks", "standards"]
        adjective = random.choice(adjectives)
        noun = random.choice(nouns)
        return f"Addressing {adjective} {noun} is crucial for {topic} progress."
    
    def _generate_subtopic(self, topic: str) -> str:
        """Generate subtopic related to main topic."""
        subtopics = ["applications", "technologies", "research", "implementation", "ethics"]
        return f"{random.choice(subtopics)} of {topic}"
    
    def _generate_name(self) -> str:
        """Generate random name."""
        first_names = ["John", "Jane", "Alex", "Sarah", "Michael", "Emily", "David", "Lisa"]
        last_names = ["Smith", "Johnson", "Brown", "Wilson", "Taylor", "Anderson", "Thomas", "Jackson"]
        return f"{random.choice(first_names)} {random.choice(last_names)}"
    
    def evaluate(self, model):
        """Run Deep Research evaluation on model."""
        if not self.dataset:
            self.load_dataset()
        
        self.start_timer()
        results = []
        
        for i, task in enumerate(self.dataset):
            if i >= self.config.get("max_tasks", 30):
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
                
                # Check if answer is correct
                correct = self._check_answer(response_text, task["correct_answer"])
                
                task_result = {
                    "task_id": i,
                    "topic": task["topic"],
                    "context_length": task["context_length"],
                    "query": task["query"],
                    "correct_answer": task["correct_answer"],
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
                    "topic": task["topic"],
                    "context_length": task["context_length"],
                    "query": task["query"],
                    "correct_answer": task["correct_answer"],
                    "response": "",
                    "correct": False,
                    "time_taken": time.time() - start_time,
                    "error": str(e)
                }
                results.append(task_result)
        
        self.stop_timer()
        self.results = results
        return results
    
    def _check_answer(self, response: str, correct_answer: str) -> bool:
        """Check if model response contains correct information."""
        # Check if key points from correct answer are present
        key_points = correct_answer.lower().split('\n')
        key_points = [p.strip() for p in key_points if p.strip() and not p.strip().startswith('based')]
        
        # Count how many key points are found
        found_points = 0
        for point in key_points[:3]:  # Check first 3 key points
            if point in response.lower():
                found_points += 1
        
        # Consider correct if at least 2 out of 3 key points are found
        return found_points >= 2
    
    def compute_metrics(self, results: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Calculate Deep Research benchmark metrics including BrowseComp-Plus metrics."""
        if not results:
            return {"error": "No results available"}
        
        # Overall accuracy
        correct = sum(1 for r in results if r.get("correct", False))
        total = len(results)
        overall_accuracy = correct / total if total > 0 else 0
        
        # Topic-based accuracy
        topic_accuracy = {}
        topics = set(r.get("topic", "unknown") for r in results)
        for topic in topics:
            topic_results = [r for r in results if r.get("topic") == topic]
            if topic_results:
                topic_correct = sum(1 for r in topic_results if r.get("correct", False))
                topic_accuracy[topic] = topic_correct / len(topic_results)
        
        # Context length analysis
        length_accuracy = {}
        for length in self.config.get("context_lengths", [1000000, 5000000, 10000000]):
            length_results = [r for r in results if r.get("context_length", 0) <= length + 1000000]
            if length_results:
                length_correct = sum(1 for r in length_results if r.get("correct", False))
                length_accuracy[f"{length} tokens"] = length_correct / len(length_results)
        
        # Time analysis
        total_time = sum(r.get("time_taken", 0) for r in results)
        avg_time_per_task = total_time / total if total > 0 else 0
        
        # Token analysis
        total_tokens = sum(r.get("tokens_processed", 0) for r in results)
        avg_tokens_per_task = total_tokens / total if total > 0 else 0
        
        # BrowseComp-Plus metrics
        # Recall calculation (for BrowseComp-Plus tasks)
        recall_scores = []
        for result in results:
            if "relevant_docids" in result and "retrieved_docids" in result:
                relevant = set(result["relevant_docids"])
                retrieved = set(result["retrieved_docids"])
                if relevant:
                    recall = len(relevant.intersection(retrieved)) / len(relevant)
                    recall_scores.append(recall)
        
        average_recall = sum(recall_scores) / len(recall_scores) if recall_scores else 0
        
        # Tool call analysis (if available)
        tool_call_counts = {}
        for result in results:
            if "tool_call_counts" in result:
                for tool, count in result["tool_call_counts"].items():
                    tool_call_counts[tool] = tool_call_counts.get(tool, 0) + count
        
        # Status analysis
        status_counts = {}
        for result in results:
            status = result.get("status", "unknown")
            status_counts[status] = status_counts.get(status, 0) + 1
        
        # Calibration error placeholder (would require confidence scores)
        calibration_error = 0.0  # Placeholder for actual calibration error calculation
        
        metrics = {
            # Original metrics
            "overall_accuracy": f"{overall_accuracy:.2%}",
            "topic_accuracy": topic_accuracy,
            "length_accuracy": length_accuracy,
            "total_tasks": total,
            "correct_tasks": correct,
            "average_time_per_task": f"{avg_time_per_task:.2f}s",
            "total_evaluation_time": f"{total_time:.2f}s",
            "average_tokens_per_task": f"{avg_tokens_per_task:.0f}",
            "total_tokens_processed": f"{total_tokens:,}",
            
            # BrowseComp-Plus metrics
            "accuracy_percent": f"{overall_accuracy * 100:.2f}%",
            "recall_percent": f"{average_recall * 100:.2f}%",
            "calibration_error_percent": f"{calibration_error:.2f}%",
            "tool_call_counts": tool_call_counts,
            "status_counts": status_counts,
            "avg_tool_stats": {tool: count / total for tool, count in tool_call_counts.items()} if total > 0 else {}
        }
        
        return metrics
