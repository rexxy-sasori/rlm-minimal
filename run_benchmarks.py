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


def run_oolong_benchmark(model, num_examples: int = 10) -> Dict[str, Any]:
    """Run the OOLONG benchmark."""
    print("\n" + "="*80)
    print("OOLONG BENCHMARK")
    print("="*80)
    
    benchmark = OOLONGBenchmark(num_examples=num_examples)
    
    print(f"\nRunning OOLONG benchmark with {num_examples} examples...")
    print("This benchmark tests difficult long-context tasks including:")
    print("  - Fact retrieval")
    print("  - Multi-hop reasoning")
    print("  - Comparative analysis")
    print("  - Summarization")
    print("  - Inference")
    
    results = benchmark.run_benchmark(model, max_examples=num_examples)
    
    print(f"\nOOLONG Results:")
    print(f"  Accuracy: {results['accuracy']:.2%}")
    print(f"  Correct: {results['correct']}/{results['total']}")
    
    return {
        "name": "OOLONG",
        "results": results
    }


def run_deep_research_benchmark(model, num_examples: int = 5, papers_per_example: int = 3) -> Dict[str, Any]:
    """Run the Deep Research benchmark."""
    print("\n" + "="*80)
    print("DEEP RESEARCH BENCHMARK (BrowseComp-Plus)")
    print("="*80)
    
    benchmark = DeepResearchBenchmark(
        num_examples=num_examples,
        papers_per_example=papers_per_example
    )
    
    print(f"\nRunning Deep Research benchmark with {num_examples} examples...")
    print(f"Each example contains {papers_per_example} research papers")
    print("This benchmark tests complex research tasks including:")
    print("  - Literature review")
    print("  - Competitive analysis")
    print("  - Technical evaluation")
    print("  - Market research")
    print("  - Scientific synthesis")
    
    results = benchmark.run_benchmark(model, max_examples=num_examples)
    
    print(f"\nDeep Research Results:")
    print(f"  Average Score: {results['average_score']:.2%}")
    print(f"  Total Examples: {results['total']}")
    
    return {
        "name": "Deep Research (BrowseComp-Plus)",
        "results": results
    }


def run_ruler_benchmark(model, num_examples: int = 20) -> Dict[str, Any]:
    """Run the RULER benchmark."""
    print("\n" + "="*80)
    print("RULER BENCHMARK (Needle-in-Haystack)")
    print("="*80)
    
    benchmark = RULERBenchmark(num_examples=num_examples)
    
    print(f"\nRunning RULER benchmark with {num_examples} examples...")
    print("This benchmark tests needle-in-haystack retrieval across:")
    print("  - Different context lengths (1K to 10M+ tokens)")
    print("  - Different needle positions (beginning, middle, end, distributed)")
    print("  - Different needle types (factual, numerical, entities, dates, quotes)")
    
    results = benchmark.run_benchmark(model, max_examples=num_examples)
    
    print(f"\nRULER Results:")
    print(f"  Accuracy: {results['accuracy']:.2%}")
    print(f"  Correct: {results['correct']}/{results['total']}")
    
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


def run_all_benchmarks(model, num_examples: int = 10) -> Dict[str, Any]:
    """Run all benchmarks."""
    print("\n" + "#"*80)
    print("RLM BENCHMARK SUITE")
    print("#"*80)
    print("Running comprehensive benchmark suite for Recursive Language Models")
    
    all_results = {}
    
    try:
        oolong_results = run_oolong_benchmark(model, num_examples)
        all_results["oolong"] = oolong_results
    except Exception as e:
        print(f"\nError running OOLONG benchmark: {e}")
        all_results["oolong"] = {"error": str(e)}
    
    try:
        deep_research_results = run_deep_research_benchmark(model, num_examples // 2)
        all_results["deep_research"] = deep_research_results
    except Exception as e:
        print(f"\nError running Deep Research benchmark: {e}")
        all_results["deep_research"] = {"error": str(e)}
    
    try:
        ruler_results = run_ruler_benchmark(model, num_examples)
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
        '--papers-per-example', '-p',
        type=int,
        default=3,
        help='Number of papers per Deep Research example (default: 3)'
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
            results = run_oolong_benchmark(rlm, args.num_examples)
        elif args.benchmark == 'deep_research':
            results = run_deep_research_benchmark(
                rlm, 
                args.num_examples, 
                args.papers_per_example
            )
        elif args.benchmark == 'ruler':
            results = run_ruler_benchmark(rlm, args.num_examples)
        elif args.benchmark == 'all':
            results = run_all_benchmarks(rlm, args.num_examples)
        
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
