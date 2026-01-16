from typing import Dict, Any, List, Optional
import json
import os
import matplotlib.pyplot as plt
import numpy as np

class BenchmarkAnalyzer:
    """Analyzes and visualizes benchmark results."""
    
    def __init__(self, results_dir: str = "results"):
        """Initialize analyzer with results directory."""
        self.results_dir = results_dir
        self.results = {}
    
    def load_results(self, benchmark_name: str):
        """Load results for a specific benchmark."""
        results_file = os.path.join(self.results_dir, f"{benchmark_name}_results.json")
        
        if not os.path.exists(results_file):
            raise FileNotFoundError(f"Results file not found: {results_file}")
        
        with open(results_file, 'r') as f:
            data = json.load(f)
        
        self.results[benchmark_name] = data
        return data
    
    def load_all_results(self):
        """Load results for all benchmarks in the directory."""
        results_files = [f for f in os.listdir(self.results_dir) if f.endswith("_results.json")]
        
        for file_name in results_files:
            benchmark_name = file_name.replace("_results.json", "")
            self.load_results(benchmark_name)
        
        return self.results
    
    def analyze_accuracy(self, benchmark_name: str) -> Dict[str, Any]:
        """Analyze accuracy metrics for a benchmark."""
        if benchmark_name not in self.results:
            self.load_results(benchmark_name)
        
        data = self.results[benchmark_name]
        results = data.get("results", [])
        
        if not results:
            return {"error": "No results found"}
        
        # Overall accuracy
        correct = sum(1 for r in results if r.get("correct", False))
        total = len(results)
        overall_accuracy = correct / total if total > 0 else 0
        
        # Task type accuracy (if applicable)
        task_accuracy = {}
        if any("task_type" in r for r in results):
            task_types = set(r.get("task_type", "unknown") for r in results)
            for task_type in task_types:
                type_results = [r for r in results if r.get("task_type") == task_type]
                if type_results:
                    type_correct = sum(1 for r in type_results if r.get("correct", False))
                    task_accuracy[task_type] = type_correct / len(type_results)
        
        # Context length analysis
        length_accuracy = {}
        if any("context_length" in r for r in results):
            # Group by context length ranges
            length_ranges = [
                (0, 100000, "0-100K"),
                (100000, 1000000, "100K-1M"),
                (1000000, 5000000, "1M-5M"),
                (5000000, 10000000, "5M-10M"),
                (10000000, float('inf'), "10M+")
            ]
            
            for min_len, max_len, label in length_ranges:
                range_results = [r for r in results if min_len <= r.get("context_length", 0) < max_len]
                if range_results:
                    range_correct = sum(1 for r in range_results if r.get("correct", False))
                    length_accuracy[label] = range_correct / len(range_results)
        
        # Time analysis
        total_time = sum(r.get("time_taken", 0) for r in results)
        avg_time_per_task = total_time / total if total > 0 else 0
        
        # Token analysis
        total_tokens = sum(r.get("tokens_processed", 0) for r in results)
        avg_tokens_per_task = total_tokens / total if total > 0 else 0
        
        analysis = {
            "overall_accuracy": overall_accuracy,
            "total_tasks": total,
            "correct_tasks": correct,
            "task_accuracy": task_accuracy,
            "length_accuracy": length_accuracy,
            "average_time_per_task": avg_time_per_task,
            "total_time": total_time,
            "average_tokens_per_task": avg_tokens_per_task,
            "total_tokens": total_tokens
        }
        
        return analysis
    
    def compare_benchmarks(self) -> Dict[str, Any]:
        """Compare multiple benchmarks."""
        if not self.results:
            self.load_all_results()
        
        comparison = {}
        
        for benchmark_name, data in self.results.items():
            analysis = self.analyze_accuracy(benchmark_name)
            comparison[benchmark_name] = analysis
        
        return comparison
    
    def generate_accuracy_chart(self, benchmark_name: str, output_file: str = "accuracy_chart.png"):
        """Generate accuracy chart for benchmark."""
        analysis = self.analyze_accuracy(benchmark_name)
        
        # Create figure
        plt.figure(figsize=(12, 6))
        
        # Plot task type accuracy
        if analysis.get("task_accuracy"):
            task_types = list(analysis["task_accuracy"].keys())
            accuracies = list(analysis["task_accuracy"].values())
            
            plt.subplot(1, 2, 1)
            plt.bar(task_types, accuracies)
            plt.title(f"Task Type Accuracy - {benchmark_name}")
            plt.xlabel("Task Type")
            plt.ylabel("Accuracy")
            plt.ylim(0, 1)
            plt.xticks(rotation=45, ha='right')
        
        # Plot context length accuracy
        if analysis.get("length_accuracy"):
            lengths = list(analysis["length_accuracy"].keys())
            accuracies = list(analysis["length_accuracy"].values())
            
            plt.subplot(1, 2, 2)
            plt.bar(lengths, accuracies)
            plt.title(f"Context Length Accuracy - {benchmark_name}")
            plt.xlabel("Context Length")
            plt.ylabel("Accuracy")
            plt.ylim(0, 1)
        
        plt.tight_layout()
        plt.savefig(output_file)
        plt.close()
        
        return output_file
    
    def generate_comparison_chart(self, output_file: str = "comparison_chart.png"):
        """Generate comparison chart for multiple benchmarks."""
        comparison = self.compare_benchmarks()
        
        if not comparison:
            return None
        
        # Create figure
        plt.figure(figsize=(10, 6))
        
        # Get benchmark names and overall accuracies
        benchmarks = list(comparison.keys())
        accuracies = [data.get("overall_accuracy", 0) for data in comparison.values()]
        
        # Plot bar chart
        bars = plt.bar(benchmarks, accuracies)
        plt.title("Benchmark Accuracy Comparison")
        plt.xlabel("Benchmark")
        plt.ylabel("Overall Accuracy")
        plt.ylim(0, 1)
        
        # Add accuracy labels on bars
        for bar, accuracy in zip(bars, accuracies):
            height = bar.get_height()
            plt.text(bar.get_x() + bar.get_width()/2., height + 0.02,
                    f'{accuracy:.2f}',
                    ha='center', va='bottom')
        
        plt.tight_layout()
        plt.savefig(output_file)
        plt.close()
        
        return output_file
    
    def generate_detailed_report(self, benchmark_name: str) -> str:
        """Generate detailed analysis report for benchmark."""
        analysis = self.analyze_accuracy(benchmark_name)
        
        report_lines = [
            f"{'='*80}",
            f"Detailed Analysis Report: {benchmark_name}",
            f"{'='*80}",
            f"Overall Accuracy: {analysis.get('overall_accuracy', 0):.2%}",
            f"Total Tasks: {analysis.get('total_tasks', 0)}",
            f"Correct Tasks: {analysis.get('correct_tasks', 0)}",
            f"Average Time per Task: {analysis.get('average_time_per_task', 0):.2f}s",
            f"Average Tokens per Task: {analysis.get('average_tokens_per_task', 0):.0f}",
        ]
        
        if analysis.get("task_accuracy"):
            report_lines.extend([
                f"{'='*80}",
                f"Task Type Accuracy:",
            ])
            for task_type, acc in analysis["task_accuracy"].items():
                report_lines.append(f"  {task_type}: {acc:.2%}")
        
        if analysis.get("length_accuracy"):
            report_lines.extend([
                f"{'='*80}",
                f"Context Length Accuracy:",
            ])
            for length, acc in analysis["length_accuracy"].items():
                report_lines.append(f"  {length}: {acc:.2%}")
        
        report_lines.extend([
            f"{'='*80}",
            f"Analysis complete",
            f"{'='*80}",
        ])
        
        return "\n".join(report_lines)
    
    def generate_summary_report(self) -> str:
        """Generate summary report of all benchmarks."""
        comparison = self.compare_benchmarks()
        
        report_lines = [
            f"{'='*80}",
            f"Benchmark Summary Analysis",
            f"{'='*80}",
        ]
        
        for benchmark_name, analysis in comparison.items():
            report_lines.append(f"=== {benchmark_name} ===")
            report_lines.append(f"Accuracy: {analysis.get('overall_accuracy', 0):.2%}")
            report_lines.append(f"Tasks: {analysis.get('total_tasks', 0)}")
            report_lines.append(f"Avg Time: {analysis.get('average_time_per_task', 0):.2f}s")
            report_lines.append("")
        
        report_lines.append(f"{'='*80}")
        report_lines.append("Summary complete")
        report_lines.append(f"{'='*80}")
        
        return "\n".join(report_lines)

def main():
    """Main function for analysis."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Analyze RLM benchmark results")
    parser.add_argument("--results-dir", default="results",
                      help="Directory containing benchmark results")
    parser.add_argument("--benchmark", help="Specific benchmark to analyze")
    parser.add_argument("--output", default="analysis",
                      help="Output directory for analysis")
    
    args = parser.parse_args()
    
    # Create output directory
    os.makedirs(args.output, exist_ok=True)
    
    # Initialize analyzer
    analyzer = BenchmarkAnalyzer(args.results_dir)
    
    if args.benchmark:
        # Analyze specific benchmark
        analysis = analyzer.analyze_accuracy(args.benchmark)
        report = analyzer.generate_detailed_report(args.benchmark)
        
        # Save report
        report_file = os.path.join(args.output, f"{args.benchmark}_detailed_analysis.txt")
        with open(report_file, 'w') as f:
            f.write(report)
        
        # Generate chart
        chart_file = os.path.join(args.output, f"{args.benchmark}_accuracy_chart.png")
        analyzer.generate_accuracy_chart(args.benchmark, chart_file)
        
        print(f"Analysis completed for {args.benchmark}")
        print(f"Report saved to: {report_file}")
        print(f"Chart saved to: {chart_file}")
        
    else:
        # Analyze all benchmarks
        comparison = analyzer.compare_benchmarks()
        summary_report = analyzer.generate_summary_report()
        
        # Save summary report
        summary_file = os.path.join(args.output, "summary_analysis.txt")
        with open(summary_file, 'w') as f:
            f.write(summary_report)
        
        # Generate comparison chart
        comparison_chart = os.path.join(args.output, "benchmark_comparison.png")
        analyzer.generate_comparison_chart(comparison_chart)
        
        print(f"Analysis completed for all benchmarks")
        print(f"Summary report saved to: {summary_file}")
        print(f"Comparison chart saved to: {comparison_chart}")

if __name__ == "__main__":
    main()
