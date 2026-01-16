from typing import Dict, Any, List, Optional
import time
import json
import os
from .base import BaseBenchmark
from .config import get_default_config, ensure_output_dir
from .oolong import OOLONGBenchmark
from .deep_research import DeepResearchBenchmark
from .ruler import RULERBenchmark

class BenchmarkRunner:
    """Orchestrates benchmark execution and result aggregation."""
    
    def __init__(self):
        """Initialize benchmark runner."""
        self.benchmarks = {}
        self.results = {}
        self.start_time = None
        self.end_time = None
    
    def add_benchmark(self, benchmark_name: str, config: Optional[Dict[str, Any]] = None):
        """Add a benchmark to the runner."""
        # Get default config if none provided
        if config is None:
            default_config = get_default_config(benchmark_name)
            config = default_config.to_dict()
        
        # Create benchmark instance
        if benchmark_name == "oolong":
            benchmark = OOLONGBenchmark(config)
        elif benchmark_name == "deep_research":
            benchmark = DeepResearchBenchmark(config)
        elif benchmark_name == "ruler":
            benchmark = RULERBenchmark(config)
        else:
            raise ValueError(f"Unknown benchmark: {benchmark_name}")
        
        self.benchmarks[benchmark_name] = benchmark
    
    def run_all(self, model, output_dir: str = "results"):
        """Run all added benchmarks."""
        self.start_time = time.time()
        
        # Ensure output directory exists
        os.makedirs(output_dir, exist_ok=True)
        
        # Run each benchmark
        for benchmark_name, benchmark in self.benchmarks.items():
            print(f"Running {benchmark_name} benchmark...")
            
            # Load dataset
            benchmark.load_dataset()
            
            # Run evaluation
            results = benchmark.evaluate(model)
            
            # Store results
            self.results[benchmark_name] = results
            
            # Save results to file
            output_file = os.path.join(output_dir, f"{benchmark_name}_results.json")
            benchmark.save_results(output_file)
            
            # Generate report
            report = benchmark.report(results)
            report_file = os.path.join(output_dir, f"{benchmark_name}_report.txt")
            with open(report_file, 'w') as f:
                f.write(report)
            
            print(f"Completed {benchmark_name} benchmark\n")
        
        self.end_time = time.time()
        
        # Generate summary report
        summary_report = self._generate_summary_report()
        summary_file = os.path.join(output_dir, "summary_report.txt")
        with open(summary_file, 'w') as f:
            f.write(summary_report)
        
        print(f"All benchmarks completed in {self.end_time - self.start_time:.2f} seconds")
        print(f"Results saved to: {output_dir}")
        
        return self.results
    
    def run_benchmark(self, benchmark_name: str, model, output_dir: str = "results"):
        """Run a specific benchmark."""
        if benchmark_name not in self.benchmarks:
            raise ValueError(f"Benchmark not found: {benchmark_name}")
        
        # Ensure output directory exists
        os.makedirs(output_dir, exist_ok=True)
        
        benchmark = self.benchmarks[benchmark_name]
        
        print(f"Running {benchmark_name} benchmark...")
        
        # Load dataset
        benchmark.load_dataset()
        
        # Run evaluation
        results = benchmark.evaluate(model)
        
        # Store results
        self.results[benchmark_name] = results
        
        # Save results to file
        output_file = os.path.join(output_dir, f"{benchmark_name}_results.json")
        benchmark.save_results(output_file)
        
        # Generate report
        report = benchmark.report(results)
        report_file = os.path.join(output_dir, f"{benchmark_name}_report.txt")
        with open(report_file, 'w') as f:
            f.write(report)
        
        print(f"Completed {benchmark_name} benchmark")
        print(f"Results saved to: {output_file}")
        
        return results
    
    def _generate_summary_report(self) -> str:
        """Generate summary report of all benchmarks."""
        report_lines = [
            f"{'='*80}",
            f"Benchmark Summary Report",
            f"{'='*80}",
        ]
        
        if self.start_time and self.end_time:
            total_time = self.end_time - self.start_time
            report_lines.append(f"Total Execution Time: {total_time:.2f} seconds")
            report_lines.append("")
        
        for benchmark_name, results in self.results.items():
            benchmark = self.benchmarks[benchmark_name]
            metrics = benchmark.compute_metrics(results)
            
            report_lines.append(f"=== {benchmark_name.upper()} ===")
            report_lines.append(f"Overall Accuracy: {metrics.get('overall_accuracy', 'N/A')}")
            report_lines.append(f"Total Tasks: {metrics.get('total_tasks', 0)}")
            report_lines.append(f"Correct Tasks: {metrics.get('correct_tasks', 0)}")
            
            if 'average_time_per_task' in metrics:
                report_lines.append(f"Avg Time per Task: {metrics['average_time_per_task']}")
            
            report_lines.append("")
        
        report_lines.append(f"{'='*80}")
        report_lines.append("Summary complete")
        report_lines.append(f"{'='*80}")
        
        return "\n".join(report_lines)
    
    def compare_models(self, models: Dict[str, Any], benchmark_name: str, output_dir: str = "results"):
        """Compare multiple models on a single benchmark."""
        if benchmark_name not in self.benchmarks:
            self.add_benchmark(benchmark_name)
        
        # Ensure output directory exists
        os.makedirs(output_dir, exist_ok=True)
        
        benchmark = self.benchmarks[benchmark_name]
        
        # Load dataset once
        benchmark.load_dataset()
        
        comparison_results = {}
        
        for model_name, model in models.items():
            print(f"Running {benchmark_name} benchmark for {model_name}...")
            
            # Run evaluation
            results = benchmark.evaluate(model)
            
            # Store results
            comparison_results[model_name] = results
            
            # Save results to file
            output_file = os.path.join(output_dir, f"{benchmark_name}_{model_name}_results.json")
            # Create temporary benchmark instance for saving
            temp_benchmark = type(benchmark)(benchmark.config)
            temp_benchmark.results = results
            temp_benchmark.save_results(output_file)
        
        # Generate comparison report
        comparison_report = self._generate_comparison_report(benchmark_name, comparison_results)
        comparison_file = os.path.join(output_dir, f"{benchmark_name}_comparison_report.txt")
        with open(comparison_file, 'w') as f:
            f.write(comparison_report)
        
        print(f"Model comparison completed")
        print(f"Comparison report saved to: {comparison_file}")
        
        return comparison_results
    
    def _generate_comparison_report(self, benchmark_name: str, comparison_results: Dict[str, List[Dict[str, Any]]]) -> str:
        """Generate comparison report for multiple models."""
        report_lines = [
            f"{'='*80}",
            f"Model Comparison Report: {benchmark_name}",
            f"{'='*80}",
        ]
        
        # Get benchmark instance
        benchmark = self.benchmarks[benchmark_name]
        
        # Compare metrics
        for model_name, results in comparison_results.items():
            metrics = benchmark.compute_metrics(results)
            
            report_lines.append(f"=== {model_name} ===")
            report_lines.append(f"Overall Accuracy: {metrics.get('overall_accuracy', 'N/A')}")
            report_lines.append(f"Total Tasks: {metrics.get('total_tasks', 0)}")
            report_lines.append(f"Correct Tasks: {metrics.get('correct_tasks', 0)}")
            
            if 'average_time_per_task' in metrics:
                report_lines.append(f"Avg Time per Task: {metrics['average_time_per_task']}")
            
            if 'average_tokens_per_task' in metrics:
                report_lines.append(f"Avg Tokens per Task: {metrics['average_tokens_per_task']}")
            
            report_lines.append("")
        
        # Add comparison table
        report_lines.append(f"{'='*80}")
        report_lines.append("Accuracy Comparison:")
        report_lines.append(f"{'='*80}")
        
        for model_name, results in comparison_results.items():
            metrics = benchmark.compute_metrics(results)
            accuracy = metrics.get('overall_accuracy', 'N/A')
            report_lines.append(f"{model_name}: {accuracy}")
        
        report_lines.append(f"{'='*80}")
        
        return "\n".join(report_lines)

def main():
    """Main function for command-line execution."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Run RLM benchmarks")
    parser.add_argument("--benchmark", choices=["oolong", "deep_research", "ruler", "all"], default="all",
                      help="Which benchmark to run")
    parser.add_argument("--output", default="results",
                      help="Output directory for results")
    # Import model here to avoid circular imports
    from rlm.rlm_repl import RLM_REPL
    
    # Create model instance - uses environment variables by default
    model = RLM_REPL()
    
    # Create runner
    runner = BenchmarkRunner()
    
    # Add benchmarks
    if args.benchmark == "all":
        runner.add_benchmark("oolong")
        runner.add_benchmark("deep_research")
        runner.add_benchmark("ruler")
        runner.run_all(model, args.output)
    else:
        runner.add_benchmark(args.benchmark)
        runner.run_benchmark(args.benchmark, model, args.output)

if __name__ == "__main__":
    main()
