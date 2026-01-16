"""
Benchmark Runner for RLM (Recursive Language Models)

This script runs the benchmarks mentioned in the RLM blog post:
1. OOLONG - Difficult long-context benchmark
2. Deep Research (BrowseComp-Plus) - Complex research tasks
3. RULER - Needle-in-haystack evaluation
"""

import argparse
import json
from typing import Dict, Any

from benchmarks.oolong import OOLONGBenchmark
from benchmarks.deep_research import DeepResearchBenchmark
from benchmarks.ruler import RULERBenchmark


def run_oolong_benchmark(model, config: Dict[str, Any] = None) -> Dict[str, Any]:
    """Run the OOLONG benchmark."""
    print("\n" + "="*80)
    print("OOLONG BENCHMARK")
    print("="*80)
    
    if config is None:
        config = {"max_tasks": 10}
    
    benchmark = OOLONGBenchmark(config)
    
    print(f"\nRunning OOLONG benchmark with {config.get('max_tasks', 10)} examples...")
    print("This benchmark tests difficult long-context tasks including:")
    print("  - Fact retrieval")
    print("  - Multi-hop reasoning")
    print("  - Comparative analysis")
    print("  - Summarization")
    print("  - Inference")
    
    results = benchmark.evaluate(model)
    metrics = benchmark.compute_metrics(results)
    
    print(f"\nOOLONG Results:")
    print(f"  Accuracy: {metrics.get('overall_accuracy', 'N/A')}")
    print(f"  Correct: {metrics.get('correct_tasks', 0)}/{metrics.get('total_tasks', 0)}")
    
    return {
        "name": "OOLONG",
        "results": results,
        "metrics": metrics
    }


def run_deep_research_benchmark(model, config: Dict[str, Any] = None) -> Dict[str, Any]:
    """Run the Deep Research benchmark."""
    print("\n" + "="*80)
    print("DEEP RESEARCH BENCHMARK (BrowseComp-Plus)")
    print("="*80)
    
    if config is None:
        config = {"max_tasks": 5}
    
    benchmark = DeepResearchBenchmark(config)
    
    print(f"\nRunning Deep Research benchmark with {config.get('max_tasks', 5)} examples...")
    print("This benchmark tests complex research tasks including:")
    print("  - Literature review")
    print("  - Competitive analysis")
    print("  - Technical evaluation")
    print("  - Market research")
    print("  - Scientific synthesis")
    
    results = benchmark.evaluate(model)
    metrics = benchmark.compute_metrics(results)
    
    print(f"\nDeep Research Results:")
    print(f"  Accuracy: {metrics.get('overall_accuracy', 'N/A')}")
    print(f"  Correct: {metrics.get('correct_tasks', 0)}/{metrics.get('total_tasks', 0)}")
    
    return {
        "name": "Deep Research",
        "results": results,
        "metrics": metrics
    }


def run_ruler_benchmark(model, config: Dict[str, Any] = None) -> Dict[str, Any]:
    """Run the RULER benchmark."""
    print("\n" + "="*80)
    print("RULER BENCHMARK (Needle-in-Haystack)")
    print("="*80)
    
    if config is None:
        config = {"max_tasks": 20}
    
    benchmark = RULERBenchmark(config)
    
    print(f"\nRunning RULER benchmark with {config.get('max_tasks', 20)} examples...")
    print("This benchmark tests needle-in-haystack retrieval across:")
    print("  - Different context lengths (1K to 10M+ tokens)")
    print("  - Different needle positions (beginning, middle, end, distributed)")
    print("  - Different needle types (factual, numerical, entities, dates, quotes)")
    
    results = benchmark.evaluate(model)
    metrics = benchmark.compute_metrics(results)
    
    print(f"\nRULER Results:")
    print(f"  Accuracy: {metrics.get('overall_accuracy', 'N/A')}")
    print(f"  Correct: {metrics.get('correct_tasks', 0)}/{metrics.get('total_tasks', 0)}")
    
    print("\nRunning position analysis...")
    position_results = benchmark.run_position_analysis(model)
    
    print("\nRunning length analysis...")
    length_results = benchmark.run_length_analysis(model)
    
    return {
        "name": "RULER",
        "results": results,
        "position_analysis": position_results,
        "length_analysis": length_results
    }


def run_all_benchmarks(model, config: Dict[str, Any] = None) -> Dict[str, Any]:
    """Run all benchmarks."""
    print("\n" + "#"*80)
    print("RLM BENCHMARK SUITE")
    print("#"*80)
    print("Running comprehensive benchmark suite for Recursive Language Models")
    
    if config is None:
        config = {"max_tasks": 10}
    
    all_results = {}
    
    try:
        oolong_config = config.copy()
        oolong_config["max_tasks"] = config.get("max_tasks", 10)
        oolong_results = run_oolong_benchmark(model, oolong_config)
        all_results["oolong"] = oolong_results
    except Exception as e:
        print(f"\nError running OOLONG benchmark: {e}")
        all_results["oolong"] = {"error": str(e)}
    
    try:
        deep_research_config = config.copy()
        deep_research_config["max_tasks"] = config.get("max_tasks", 10) // 2
        deep_research_results = run_deep_research_benchmark(model, deep_research_config)
        all_results["deep_research"] = deep_research_results
    except Exception as e:
        print(f"\nError running Deep Research benchmark: {e}")
        all_results["deep_research"] = {"error": str(e)}
    
    try:
        ruler_config = config.copy()
        ruler_config["max_tasks"] = config.get("max_tasks", 10)
        ruler_results = run_ruler_benchmark(model, ruler_config)
        all_results["ruler"] = ruler_results
    except Exception as e:
        print(f"\nError running RULER benchmark: {e}")
        all_results["ruler"] = {"error": str(e)}
    
    print("\n" + "#"*80)
    print("BENCHMARK SUMMARY")
    print("#"*80)
    
    for name, results in all_results.items():
        if "error" in results:
            print(f"{name.upper()}: FAILED - {results['error']}")
        else:
            if "accuracy" in results.get("results", {}):
                acc = results["results"]["accuracy"]
                print(f"{name.upper()}: Accuracy = {acc:.2%}")
            elif "average_score" in results.get("results", {}):
                score = results["results"]["average_score"]
                print(f"{name.upper()}: Average Score = {score:.2%}")
    
    return all_results


def demo_benchmarks():
    """Demonstrate the benchmarks without running an actual model."""
    print("\n" + "#"*80)
    print("RLM BENCHMARK DEMONSTRATION")
    print("#"*80)
    print("\nThis demo shows example benchmark outputs without running a model.")
    
    print("\n" + "="*80)
    print("OOLONG BENCHMARK - Example")
    print("="*80)
    oolong = OOLONGBenchmark(num_examples=3)
    example = oolong.get_example(0)
    print(f"\nExample 0:")
    print(f"  Task Type: {example.task_type.value}")
    print(f"  Difficulty: {example.difficulty}")
    print(f"  Context Length: {example.context_length} chars")
    print(f"  Query: {example.query}")
    print(f"  Answer: {example.answer}")
    print(f"  Context Preview: {example.context[:200]}...")
    
    print("\n" + "="*80)
    print("DEEP RESEARCH BENCHMARK - Example")
    print("="*80)
    deep_research = DeepResearchBenchmark(num_examples=2, papers_per_example=2)
    example = deep_research.get_example(0)
    print(f"\nExample 0:")
    print(f"  Task Type: {example.task_type.value}")
    print(f"  Number of Papers: {example.num_papers}")
    print(f"  Context Length: {example.context_length} chars")
    print(f"  Query: {example.query}")
    print(f"  Answer: {example.answer}")
    
    print("\n" + "="*80)
    print("RULER BENCHMARK - Example")
    print("="*80)
    ruler = RULERBenchmark(num_examples=5)
    example = ruler.get_example(0)
    print(f"\nExample 0:")
    print(f"  Needle Type: {example.needle_type.value}")
    print(f"  Context Length: {example.context_length} chars")
    print(f"  Distribution: {example.context_distribution.value}")
    print(f"  Needle Position: {example.needle_position}")
    print(f"  Query: {example.query}")
    print(f"  Answer: {example.answer}")
    print(f"  Context Preview: {example.context[:200]}...")
    
    print("\n" + "#"*80)
    print("BENCHMARK DEMONSTRATION COMPLETE")
    print("#"*80)
    print("\nTo run actual benchmarks with RLM:")
    print("  1. Set up your LLM API key in .env")
    print("  2. Initialize RLM_REPL with your model")
    print("  3. Call run_all_benchmarks(rlm_model, num_examples=10)")


def main():
    parser = argparse.ArgumentParser(
        description='Run RLM benchmarks',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Benchmarks available:
  - oolong: Difficult long-context tasks
  - deep_research: Complex research tasks (BrowseComp-Plus)
  - ruler: Needle-in-haystack evaluation
  - all: Run all benchmarks
  - demo: Show benchmark examples without running a model
        """
    )
    
    parser.add_argument(
        'benchmark',
        choices=['oolong', 'deep_research', 'ruler', 'all', 'demo'],
        help='Which benchmark to run'
    )
    
    parser.add_argument(
        '--num-examples', '-n',
        type=int,
        default=10,
        help='Number of examples to run (default: 10)'
    )
    
    parser.add_argument(
        '--config', '-c',
        type=str,
        help='JSON configuration file for benchmarks'
    )
    
    parser.add_argument(
        '--output', '-o',
        type=str,
        help='Output JSON file for results'
    )
    
    args = parser.parse_args()
    
    if args.benchmark == 'demo':
        demo_benchmarks()
        return
    
    # Load configuration
    config = {"max_tasks": args.num_examples}
    
    if args.config:
        with open(args.config, 'r') as f:
            config = json.load(f)
    
    try:
        from rlm.rlm_repl import RLM_REPL
        
        print("Initializing RLM model...")
        rlm = RLM_REPL(
            model="gpt-5",
            recursive_model="gpt-5-mini",
            enable_logging=False,
            max_iterations=10
        )
        
        results = None
        
        if args.benchmark == 'oolong':
            results = run_oolong_benchmark(rlm, config)
        elif args.benchmark == 'deep_research':
            results = run_deep_research_benchmark(rlm, config)
        elif args.benchmark == 'ruler':
            results = run_ruler_benchmark(rlm, config)
        elif args.benchmark == 'all':
            results = run_all_benchmarks(rlm, config)
        
        if args.output and results:
            with open(args.output, 'w') as f:
                json.dump(results, f, indent=2)
            print(f"\nResults saved to {args.output}")
            
    except ImportError as e:
        print(f"\nError importing RLM: {e}")
        print("\nPlease ensure the RLM package is installed and configured.")
        print("For a demo without running a model, use: python run_benchmarks.py demo")
    except Exception as e:
        print(f"\nError running benchmarks: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
