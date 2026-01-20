"""
Benchmark Runner for RLM (Recursive Language Models) with Sidecar WASM Pattern

This script runs benchmarks using RLM_REPL with sidecar WASM execution:
1. OOLONG - Difficult long-context benchmark
2. Deep Research (BrowseComp-Plus) - Complex research tasks
3. RULER - Needle-in-haystack evaluation

Uses sidecar WASM pattern for secure, isolated code execution.
Supports asyncio for parallel task processing with configurable concurrency.
"""

import argparse
import asyncio
import json
import os
import time
from typing import Dict, Any, Optional, List, Coroutine
from concurrent.futures import ThreadPoolExecutor, as_completed

from benchmarks.oolong import OOLONGBenchmark
from benchmarks.deep_research import DeepResearchBenchmark
from benchmarks.ruler import RULERBenchmark
from rlm.local.rlm_repl import RLM_REPL
from rlm.remote.repl_sidecar import SidecarREPLFactory, SidecarExecutionConfig


def create_rlm_repl_with_sidecar(
    api_key: Optional[str] = None,
    model: str = "gpt-5",
    base_url: Optional[str] = None,
    max_depth: int = 3,
    wasm_service_url: str = "http://localhost:8080",
    wasm_timeout: int = 30,
    enable_logging: bool = False
) -> RLM_REPL:
    """
    Create RLM_REPL instance with sidecar WASM pattern.
    
    Args:
        api_key: LLM API key
        model: LLM model name
        base_url: LLM API base URL
        max_depth: Maximum recursion depth
        wasm_service_url: Sidecar WASM manager URL
        wasm_timeout: WASM execution timeout
        enable_logging: Enable detailed logging
    
    Returns:
        RLM_REPL instance with sidecar REPL factory
    """
    print(f"\nInitializing RLM_REPL with sidecar WASM...")
    print(f"  Model: {model}")
    print(f"  Max Depth: {max_depth}")
    print(f"  WASM Service: {wasm_service_url}")
    print(f"  WASM Timeout: {wasm_timeout}s")
    
    sidecar_config = SidecarExecutionConfig(
        wasm_service_url=wasm_service_url,
        timeout=wasm_timeout,
        session_ttl=3600
    )
    
    repl_factory = SidecarREPLFactory(config=sidecar_config)
    
    rlm = RLM_REPL(
        api_key=api_key,
        model=model,
        base_url=base_url,
        max_depth=max_depth,
        enable_logging=enable_logging,
        repl_factory=repl_factory
    )
    
    print("✓ RLM_REPL with sidecar WASM initialized successfully")
    return rlm


def create_rlm_pool(
    api_key: str,
    model: str,
    base_url: Optional[str],
    max_depth: int,
    wasm_service_url: str,
    wasm_timeout: int,
    enable_logging: bool,
    pool_size: int
) -> List[RLM_REPL]:
    """
    Create a pool of RLM_REPL instances for parallel processing.
    
    Args:
        api_key: LLM API key
        model: LLM model name
        base_url: LLM API base URL
        max_depth: Maximum recursion depth
        wasm_service_url: Sidecar WASM manager URL
        wasm_timeout: WASM execution timeout
        enable_logging: Enable detailed logging
        pool_size: Number of RLM instances to create
    
    Returns:
        List of RLM_REPL instances
    """
    print(f"\nCreating RLM pool with {pool_size} instances...")
    
    pool = []
    for i in range(pool_size):
        print(f"  Creating RLM instance {i + 1}/{pool_size}...")
        rlm = create_rlm_repl_with_sidecar(
            api_key=api_key,
            model=model,
            base_url=base_url,
            max_depth=max_depth,
            wasm_service_url=wasm_service_url,
            wasm_timeout=wasm_timeout,
            enable_logging=enable_logging
        )
        pool.append(rlm)
    
    print(f"✓ RLM pool created successfully")
    return pool


async def process_task_async(
    rlm: RLM_REPL,
    task: Dict[str, Any],
    task_index: int
) -> Dict[str, Any]:
    """
    Process a single benchmark task asynchronously.
    
    Args:
        rlm: RLM_REPL instance
        task: Task dictionary containing context and query
        task_index: Index of the task
    
    Returns:
        Results dictionary
    """
    start_time = time.time()
    
    try:
        context = task.get("context", "")
        query = task.get("query", "")
        expected_answer = task.get("answer", "")
        
        result = rlm.completion(context, query)
        
        elapsed_time = time.time() - start_time
        
        is_correct = result.strip().lower() == expected_answer.strip().lower() if expected_answer else None
        
        return {
            "task_index": task_index,
            "query": query,
            "result": result,
            "expected_answer": expected_answer,
            "is_correct": is_correct,
            "execution_time": elapsed_time,
            "success": True
        }
        
    except Exception as e:
        elapsed_time = time.time() - start_time
        return {
            "task_index": task_index,
            "query": task.get("query", ""),
            "error": str(e),
            "execution_time": elapsed_time,
            "success": False
        }


async def process_batch_async(
    rlm_pool: List[RLM_REPL],
    tasks: List[Dict[str, Any]],
    max_concurrency: int
) -> List[Dict[str, Any]]:
    """
    Process a batch of tasks asynchronously with concurrency control.
    
    Args:
        rlm_pool: Pool of RLM_REPL instances
        tasks: List of tasks to process
        max_concurrency: Maximum number of concurrent tasks
    
    Returns:
        List of results
    """
    print(f"\nProcessing {len(tasks)} tasks with max concurrency: {max_concurrency}")
    
    semaphore = asyncio.Semaphore(max_concurrency)
    results = []
    
    async def bounded_process(task, index):
        async with semaphore:
            rlm = rlm_pool[index % len(rlm_pool)]
            return await process_task_async(rlm, task, index)
    
    coroutines = [bounded_process(task, i) for i, task in enumerate(tasks)]
    results = await asyncio.gather(*coroutines)
    
    return results


async def run_oolong_benchmark_async(
    rlm_pool: List[RLM_REPL],
    config: Dict[str, Any] = None,
    output_dir: str = "results",
    max_concurrency: int = 5
) -> Dict[str, Any]:
    """Run the OOLONG benchmark asynchronously with sidecar WASM."""
    print("\n" + "="*80)
    print("OOLONG BENCHMARK (ASYNC)")
    print("="*80)
    
    if config is None:
        config = {"max_tasks": 10}
    
    benchmark = OOLONGBenchmark(config)
    
    print(f"\nLoading OOLONG dataset...")
    benchmark.load_dataset()
    
    tasks = []
    for i in range(min(config.get('max_tasks', 10), len(benchmark.dataset))):
        example = benchmark.dataset[i]
        tasks.append({
            "context": example.context,
            "query": example.query,
            "answer": example.answer
        })
    
    print(f"\nRunning OOLONG benchmark with {len(tasks)} examples (concurrency: {max_concurrency})...")
    print("This benchmark tests difficult long-context tasks including:")
    print("  - Fact retrieval")
    print("  - Multi-hop reasoning")
    print("  - Comparative analysis")
    print("  - Summarization")
    print("  - Inference")
    
    start_time = time.time()
    
    try:
        results = await process_batch_async(rlm_pool, tasks, max_concurrency)
        
        elapsed_time = time.time() - start_time
        
        correct_tasks = sum(1 for r in results if r.get('is_correct'))
        total_tasks = len(results)
        accuracy = correct_tasks / total_tasks if total_tasks > 0 else 0
        
        metrics = {
            "overall_accuracy": f"{accuracy:.2%}",
            "total_tasks": total_tasks,
            "correct_tasks": correct_tasks,
            "average_time_per_task": elapsed_time / total_tasks if total_tasks > 0 else 0
        }
        
        print(f"\nOOLONG Results:")
        print(f"  Accuracy: {metrics['overall_accuracy']}")
        print(f"  Correct: {correct_tasks}/{total_tasks}")
        print(f"  Total Time: {elapsed_time:.2f}s")
        print(f"  Avg Time per Task: {metrics['average_time_per_task']:.2f}s")
        
        if output_dir:
            os.makedirs(output_dir, exist_ok=True)
            output_data = {
                "benchmark": "oolong",
                "config": config,
                "results": results,
                "metrics": metrics,
                "total_time": elapsed_time
            }
            output_file = os.path.join(output_dir, "oolong_results.json")
            with open(output_file, 'w') as f:
                json.dump(output_data, f, indent=2, default=str)
            print(f"  Results saved to: {output_file}")
        
        return {
            "name": "OOLONG",
            "results": results,
            "metrics": metrics,
            "total_time": elapsed_time,
            "avg_time_per_task": metrics['average_time_per_task']
        }
        
    except Exception as e:
        print(f"\n✗ Error running OOLONG benchmark: {e}")
        import traceback
        traceback.print_exc()
        return {
            "name": "OOLONG",
            "error": str(e),
            "total_time": time.time() - start_time
        }


def run_oolong_benchmark(
    rlm: RLM_REPL,
    config: Dict[str, Any] = None,
    output_dir: str = "results"
) -> Dict[str, Any]:
    """Run the OOLONG benchmark synchronously with RLM_REPL and sidecar WASM."""
    print("\n" + "="*80)
    print("OOLONG BENCHMARK (SYNC)")
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
    
    start_time = time.time()
    
    try:
        results = benchmark.evaluate(rlm)
        metrics = benchmark.compute_metrics(results)
        
        elapsed_time = time.time() - start_time
        
        print(f"\nOOLONG Results:")
        print(f"  Accuracy: {metrics.get('overall_accuracy', 'N/A')}")
        print(f"  Correct: {metrics.get('correct_tasks', 0)}/{metrics.get('total_tasks', 0)}")
        print(f"  Total Time: {elapsed_time:.2f}s")
        print(f"  Avg Time per Task: {elapsed_time/len(results):.2f}s")
        
        if output_dir:
            os.makedirs(output_dir, exist_ok=True)
            output_file = os.path.join(output_dir, "oolong_results.json")
            benchmark.save_results(output_file)
            print(f"  Results saved to: {output_file}")
        
        return {
            "name": "OOLONG",
            "results": results,
            "metrics": metrics,
            "total_time": elapsed_time,
            "avg_time_per_task": elapsed_time / len(results) if results else 0
        }
        
    except Exception as e:
        print(f"\n✗ Error running OOLONG benchmark: {e}")
        import traceback
        traceback.print_exc()
        return {
            "name": "OOLONG",
            "error": str(e),
            "total_time": time.time() - start_time
        }


async def run_deep_research_benchmark_async(
    rlm_pool: List[RLM_REPL],
    config: Dict[str, Any] = None,
    output_dir: str = "results",
    max_concurrency: int = 3
) -> Dict[str, Any]:
    """Run the Deep Research benchmark asynchronously with sidecar WASM."""
    print("\n" + "="*80)
    print("DEEP RESEARCH BENCHMARK (BrowseComp-Plus) (ASYNC)")
    print("="*80)
    
    if config is None:
        config = {"max_tasks": 5}
    
    benchmark = DeepResearchBenchmark(config)
    
    print(f"\nLoading Deep Research dataset...")
    benchmark.load_dataset()
    
    tasks = []
    for i in range(min(config.get('max_tasks', 5), len(benchmark.dataset))):
        example = benchmark.dataset[i]
        tasks.append({
            "context": example.context,
            "query": example.query,
            "answer": example.answer
        })
    
    print(f"\nRunning Deep Research benchmark with {len(tasks)} examples (concurrency: {max_concurrency})...")
    print("This benchmark tests complex research tasks including:")
    print("  - Literature review")
    print("  - Competitive analysis")
    print("  - Technical evaluation")
    print("  - Market research")
    print("  - Scientific synthesis")
    
    start_time = time.time()
    
    try:
        results = await process_batch_async(rlm_pool, tasks, max_concurrency)
        
        elapsed_time = time.time() - start_time
        
        correct_tasks = sum(1 for r in results if r.get('is_correct'))
        total_tasks = len(results)
        accuracy = correct_tasks / total_tasks if total_tasks > 0 else 0
        
        metrics = {
            "overall_accuracy": f"{accuracy:.2%}",
            "total_tasks": total_tasks,
            "correct_tasks": correct_tasks,
            "average_time_per_task": elapsed_time / total_tasks if total_tasks > 0 else 0
        }
        
        print(f"\nDeep Research Results:")
        print(f"  Accuracy: {metrics['overall_accuracy']}")
        print(f"  Correct: {correct_tasks}/{total_tasks}")
        print(f"  Total Time: {elapsed_time:.2f}s")
        print(f"  Avg Time per Task: {metrics['average_time_per_task']:.2f}s")
        
        if output_dir:
            os.makedirs(output_dir, exist_ok=True)
            output_data = {
                "benchmark": "deep_research",
                "config": config,
                "results": results,
                "metrics": metrics,
                "total_time": elapsed_time
            }
            output_file = os.path.join(output_dir, "deep_research_results.json")
            with open(output_file, 'w') as f:
                json.dump(output_data, f, indent=2, default=str)
            print(f"  Results saved to: {output_file}")
        
        return {
            "name": "Deep Research",
            "results": results,
            "metrics": metrics,
            "total_time": elapsed_time,
            "avg_time_per_task": metrics['average_time_per_task']
        }
        
    except Exception as e:
        print(f"\n✗ Error running Deep Research benchmark: {e}")
        import traceback
        traceback.print_exc()
        return {
            "name": "Deep Research",
            "error": str(e),
            "total_time": time.time() - start_time
        }


def run_deep_research_benchmark(
    rlm: RLM_REPL,
    config: Dict[str, Any] = None,
    output_dir: str = "results"
) -> Dict[str, Any]:
    """Run the Deep Research benchmark synchronously with RLM_REPL and sidecar WASM."""
    print("\n" + "="*80)
    print("DEEP RESEARCH BENCHMARK (BrowseComp-Plus) (SYNC)")
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
    
    start_time = time.time()
    
    try:
        results = benchmark.evaluate(rlm)
        metrics = benchmark.compute_metrics(results)
        
        elapsed_time = time.time() - start_time
        
        print(f"\nDeep Research Results:")
        print(f"  Accuracy: {metrics.get('overall_accuracy', 'N/A')}")
        print(f"  Correct: {metrics.get('correct_tasks', 0)}/{metrics.get('total_tasks', 0)}")
        print(f"  Total Time: {elapsed_time:.2f}s")
        print(f"  Avg Time per Task: {elapsed_time/len(results):.2f}s")
        
        if output_dir:
            os.makedirs(output_dir, exist_ok=True)
            output_file = os.path.join(output_dir, "deep_research_results.json")
            benchmark.save_results(output_file)
            print(f"  Results saved to: {output_file}")
        
        return {
            "name": "Deep Research",
            "results": results,
            "metrics": metrics,
            "total_time": elapsed_time,
            "avg_time_per_task": elapsed_time / len(results) if results else 0
        }
        
    except Exception as e:
        print(f"\n✗ Error running Deep Research benchmark: {e}")
        import traceback
        traceback.print_exc()
        return {
            "name": "Deep Research",
            "error": str(e),
            "total_time": time.time() - start_time
        }


async def run_ruler_benchmark_async(
    rlm_pool: List[RLM_REPL],
    config: Dict[str, Any] = None,
    output_dir: str = "results",
    max_concurrency: int = 5
) -> Dict[str, Any]:
    """Run the RULER benchmark asynchronously with sidecar WASM."""
    print("\n" + "="*80)
    print("RULER BENCHMARK (Needle-in-Haystack) (ASYNC)")
    print("="*80)
    
    if config is None:
        config = {"max_tasks": 20}
    
    benchmark = RULERBenchmark(config)
    
    print(f"\nLoading RULER dataset...")
    benchmark.load_dataset()
    
    tasks = []
    for i in range(min(config.get('max_tasks', 20), len(benchmark.dataset))):
        example = benchmark.dataset[i]
        tasks.append({
            "context": example.context,
            "query": example.query,
            "answer": example.answer
        })
    
    print(f"\nRunning RULER benchmark with {len(tasks)} examples (concurrency: {max_concurrency})...")
    print("This benchmark tests needle-in-haystack retrieval across:")
    print("  - Different context lengths (1K to 10M+ tokens)")
    print("  - Different needle positions (beginning, middle, end, distributed)")
    print("  - Different needle types (factual, numerical, entities, dates, quotes)")
    
    start_time = time.time()
    
    try:
        results = await process_batch_async(rlm_pool, tasks, max_concurrency)
        
        elapsed_time = time.time() - start_time
        
        correct_tasks = sum(1 for r in results if r.get('is_correct'))
        total_tasks = len(results)
        accuracy = correct_tasks / total_tasks if total_tasks > 0 else 0
        
        metrics = {
            "overall_accuracy": f"{accuracy:.2%}",
            "total_tasks": total_tasks,
            "correct_tasks": correct_tasks,
            "average_time_per_task": elapsed_time / total_tasks if total_tasks > 0 else 0
        }
        
        print(f"\nRULER Results:")
        print(f"  Accuracy: {metrics['overall_accuracy']}")
        print(f"  Correct: {correct_tasks}/{total_tasks}")
        print(f"  Total Time: {elapsed_time:.2f}s")
        print(f"  Avg Time per Task: {metrics['average_time_per_task']:.2f}s")
        
        if output_dir:
            os.makedirs(output_dir, exist_ok=True)
            output_data = {
                "benchmark": "ruler",
                "config": config,
                "results": results,
                "metrics": metrics,
                "total_time": elapsed_time
            }
            output_file = os.path.join(output_dir, "ruler_results.json")
            with open(output_file, 'w') as f:
                json.dump(output_data, f, indent=2, default=str)
            print(f"  Results saved to: {output_file}")
        
        return {
            "name": "RULER",
            "results": results,
            "metrics": metrics,
            "total_time": elapsed_time,
            "avg_time_per_task": metrics['average_time_per_task']
        }
        
    except Exception as e:
        print(f"\n✗ Error running RULER benchmark: {e}")
        import traceback
        traceback.print_exc()
        return {
            "name": "RULER",
            "error": str(e),
            "total_time": time.time() - start_time
        }


def run_ruler_benchmark(
    rlm: RLM_REPL,
    config: Dict[str, Any] = None,
    output_dir: str = "results"
) -> Dict[str, Any]:
    """Run the RULER benchmark synchronously with RLM_REPL and sidecar WASM."""
    print("\n" + "="*80)
    print("RULER BENCHMARK (Needle-in-Haystack) (SYNC)")
    print("="*80)
    
    if config is None:
        config = {"max_tasks": 20}
    
    benchmark = RULERBenchmark(config)
    
    print(f"\nRunning RULER benchmark with {config.get('max_tasks', 20)} examples...")
    print("This benchmark tests needle-in-haystack retrieval across:")
    print("  - Different context lengths (1K to 10M+ tokens)")
    print("  - Different needle positions (beginning, middle, end, distributed)")
    print("  - Different needle types (factual, numerical, entities, dates, quotes)")
    
    start_time = time.time()
    
    try:
        results = benchmark.evaluate(rlm)
        metrics = benchmark.compute_metrics(results)
        
        elapsed_time = time.time() - start_time
        
        print(f"\nRULER Results:")
        print(f"  Accuracy: {metrics.get('overall_accuracy', 'N/A')}")
        print(f"  Correct: {metrics.get('correct_tasks', 0)}/{metrics.get('total_tasks', 0)}")
        print(f"  Total Time: {elapsed_time:.2f}s")
        print(f"  Avg Time per Task: {elapsed_time/len(results):.2f}s")
        
        if output_dir:
            os.makedirs(output_dir, exist_ok=True)
            output_file = os.path.join(output_dir, "ruler_results.json")
            benchmark.save_results(output_file)
            print(f"  Results saved to: {output_file}")
        
        return {
            "name": "RULER",
            "results": results,
            "metrics": metrics,
            "total_time": elapsed_time,
            "avg_time_per_task": elapsed_time / len(results) if results else 0
        }
        
    except Exception as e:
        print(f"\n✗ Error running RULER benchmark: {e}")
        import traceback
        traceback.print_exc()
        return {
            "name": "RULER",
            "error": str(e),
            "total_time": time.time() - start_time
        }


async def run_all_benchmarks_async(
    rlm_pool: List[RLM_REPL],
    config: Dict[str, Any] = None,
    output_dir: str = "results",
    max_concurrency: int = 5
) -> Dict[str, Any]:
    """Run all benchmarks asynchronously with RLM pool and sidecar WASM."""
    print("\n" + "#"*80)
    print("RLM BENCHMARK SUITE - SIDECAR WASM PATTERN (ASYNC)")
    print("#"*80)
    print("Running comprehensive benchmark suite with async parallel execution")
    
    if config is None:
        config = {"max_tasks": 10}
    
    all_results = {}
    total_start_time = time.time()
    
    print(f"\nConfiguration:")
    print(f"  Model: {rlm_pool[0].model}")
    print(f"  Max Depth: {rlm_pool[0].max_depth}")
    print(f"  Max Tasks: {config.get('max_tasks', 10)}")
    print(f"  Max Concurrency: {max_concurrency}")
    print(f"  RLM Pool Size: {len(rlm_pool)}")
    print(f"  Output Directory: {output_dir}")
    
    try:
        oolong_config = config.copy()
        oolong_config["max_tasks"] = config.get("max_tasks", 10)
        oolong_results = await run_oolong_benchmark_async(
            rlm_pool, oolong_config, output_dir, max_concurrency
        )
        all_results["oolong"] = oolong_results
    except Exception as e:
        print(f"\n✗ Error running OOLONG benchmark: {e}")
        all_results["oolong"] = {"error": str(e)}
    
    try:
        deep_research_config = config.copy()
        deep_research_config["max_tasks"] = config.get("max_tasks", 10) // 2
        deep_research_results = await run_deep_research_benchmark_async(
            rlm_pool, deep_research_config, output_dir, max(1, max_concurrency // 2)
        )
        all_results["deep_research"] = deep_research_results
    except Exception as e:
        print(f"\n✗ Error running Deep Research benchmark: {e}")
        all_results["deep_research"] = {"error": str(e)}
    
    try:
        ruler_config = config.copy()
        ruler_config["max_tasks"] = config.get("max_tasks", 10)
        ruler_results = await run_ruler_benchmark_async(
            rlm_pool, ruler_config, output_dir, max_concurrency
        )
        all_results["ruler"] = ruler_results
    except Exception as e:
        print(f"\n✗ Error running RULER benchmark: {e}")
        all_results["ruler"] = {"error": str(e)}
    
    total_elapsed_time = time.time() - total_start_time
    
    print("\n" + "#"*80)
    print("BENCHMARK SUMMARY")
    print("#"*80)
    print(f"\nTotal Execution Time: {total_elapsed_time:.2f}s")
    
    for name, results in all_results.items():
        print(f"\n{name.upper()}:")
        if "error" in results:
            print(f"  Status: FAILED - {results['error']}")
        else:
            metrics = results.get("metrics", {})
            accuracy = metrics.get("overall_accuracy", "N/A")
            total_time = results.get("total_time", 0)
            print(f"  Status: COMPLETED")
            print(f"  Accuracy: {accuracy}")
            print(f"  Total Time: {total_time:.2f}s")
            if "avg_time_per_task" in results:
                print(f"  Avg Time/Task: {results['avg_time_per_task']:.2f}s")
    
    if output_dir:
        summary_file = os.path.join(output_dir, "summary.json")
        summary = {
            "configuration": config,
            "model": rlm_pool[0].model,
            "max_depth": rlm_pool[0].max_depth,
            "max_concurrency": max_concurrency,
            "rlm_pool_size": len(rlm_pool),
            "total_time": total_elapsed_time,
            "benchmarks": all_results
        }
        with open(summary_file, 'w') as f:
            json.dump(summary, f, indent=2, default=str)
        print(f"\n✓ Summary saved to: {summary_file}")
    
    return all_results


def run_all_benchmarks(
    rlm: RLM_REPL,
    config: Dict[str, Any] = None,
    output_dir: str = "results"
) -> Dict[str, Any]:
    """Run all benchmarks synchronously with RLM_REPL and sidecar WASM."""
    print("\n" + "#"*80)
    print("RLM BENCHMARK SUITE - SIDECAR WASM PATTERN (SYNC)")
    print("#"*80)
    print("Running comprehensive benchmark suite with sidecar WASM execution")
    
    if config is None:
        config = {"max_tasks": 10}
    
    all_results = {}
    total_start_time = time.time()
    
    print(f"\nConfiguration:")
    print(f"  Model: {rlm.model}")
    print(f"  Max Depth: {rlm.max_depth}")
    print(f"  Max Tasks: {config.get('max_tasks', 10)}")
    print(f"  Output Directory: {output_dir}")
    
    try:
        oolong_config = config.copy()
        oolong_config["max_tasks"] = config.get("max_tasks", 10)
        oolong_results = run_oolong_benchmark(rlm, oolong_config, output_dir)
        all_results["oolong"] = oolong_results
    except Exception as e:
        print(f"\n✗ Error running OOLONG benchmark: {e}")
        all_results["oolong"] = {"error": str(e)}
    
    try:
        deep_research_config = config.copy()
        deep_research_config["max_tasks"] = config.get("max_tasks", 10) // 2
        deep_research_results = run_deep_research_benchmark(rlm, deep_research_config, output_dir)
        all_results["deep_research"] = deep_research_results
    except Exception as e:
        print(f"\n✗ Error running Deep Research benchmark: {e}")
        all_results["deep_research"] = {"error": str(e)}
    
    try:
        ruler_config = config.copy()
        ruler_config["max_tasks"] = config.get("max_tasks", 10)
        ruler_results = run_ruler_benchmark(rlm, ruler_config, output_dir)
        all_results["ruler"] = ruler_results
    except Exception as e:
        print(f"\n✗ Error running RULER benchmark: {e}")
        all_results["ruler"] = {"error": str(e)}
    
    total_elapsed_time = time.time() - total_start_time
    
    print("\n" + "#"*80)
    print("BENCHMARK SUMMARY")
    print("#"*80)
    print(f"\nTotal Execution Time: {total_elapsed_time:.2f}s")
    
    for name, results in all_results.items():
        print(f"\n{name.upper()}:")
        if "error" in results:
            print(f"  Status: FAILED - {results['error']}")
        else:
            metrics = results.get("metrics", {})
            accuracy = metrics.get("overall_accuracy", "N/A")
            total_time = results.get("total_time", 0)
            print(f"  Status: COMPLETED")
            print(f"  Accuracy: {accuracy}")
            print(f"  Total Time: {total_time:.2f}s")
            if "avg_time_per_task" in results:
                print(f"  Avg Time/Task: {results['avg_time_per_task']:.2f}s")
    
    if output_dir:
        summary_file = os.path.join(output_dir, "summary.json")
        summary = {
            "configuration": config,
            "model": rlm.model,
            "max_depth": rlm.max_depth,
            "total_time": total_elapsed_time,
            "benchmarks": all_results
        }
        with open(summary_file, 'w') as f:
            json.dump(summary, f, indent=2, default=str)
        print(f"\n✓ Summary saved to: {summary_file}")
    
    return all_results


def main():
    """Main entry point for benchmark runner."""
    parser = argparse.ArgumentParser(
        description="RLM Benchmark Runner with Sidecar WASM Pattern",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Run all benchmarks with async execution (recommended)
  python run_benchmarks.py --api-key YOUR_KEY --model gpt-4o --async --concurrency 5
  
  # Run specific benchmark with async
  python run_benchmarks.py --benchmark oolong --max-tasks 20 --async --concurrency 3
  
  # Run synchronously (legacy mode)
  python run_benchmarks.py --benchmark ruler --max-tasks 30
  
  # Custom WASM service URL
  python run_benchmarks.py --wasm-url http://wasm-manager:8080 --async
  
  # Enable detailed logging
  python run_benchmarks.py --enable-logging --output-dir results/run1 --async
        """
    )
    
    parser.add_argument(
        "--api-key",
        type=str,
        default=os.getenv("LLM_API_KEY") or os.getenv("OPENAI_API_KEY"),
        help="LLM API key (default: from LLM_API_KEY or OPENAI_API_KEY env var)"
    )
    
    parser.add_argument(
        "--model",
        type=str,
        default=os.getenv("LLM_MODEL", "gpt-5"),
        help="LLM model name (default: gpt-5)"
    )
    
    parser.add_argument(
        "--base-url",
        type=str,
        default=os.getenv("LLM_BASE_URL"),
        help="LLM API base URL (default: from LLM_BASE_URL env var)"
    )
    
    parser.add_argument(
        "--max-depth",
        type=int,
        default=3,
        help="Maximum recursion depth (default: 3)"
    )
    
    parser.add_argument(
        "--benchmark",
        type=str,
        choices=["oolong", "deep_research", "ruler", "all"],
        default="all",
        help="Benchmark to run (default: all)"
    )
    
    parser.add_argument(
        "--max-tasks",
        type=int,
        default=10,
        help="Maximum number of tasks per benchmark (default: 10)"
    )
    
    parser.add_argument(
        "--wasm-url",
        type=str,
        default=os.getenv("WASM_MANAGER_SERVICE_URL", "http://localhost:8080"),
        help="Sidecar WASM manager URL (default: http://localhost:8080)"
    )
    
    parser.add_argument(
        "--wasm-timeout",
        type=int,
        default=30,
        help="WASM execution timeout in seconds (default: 30)"
    )
    
    parser.add_argument(
        "--output-dir",
        type=str,
        default="results",
        help="Output directory for results (default: results)"
    )
    
    parser.add_argument(
        "--enable-logging",
        action="store_true",
        help="Enable detailed logging"
    )
    
    parser.add_argument(
        "--no-save",
        action="store_true",
        help="Don't save results to files"
    )
    
    parser.add_argument(
        "--async",
        dest="use_async",
        action="store_true",
        help="Use asyncio for parallel task processing (recommended)"
    )
    
    parser.add_argument(
        "--concurrency",
        type=int,
        default=5,
        help="Maximum number of concurrent tasks (default: 5)"
    )
    
    parser.add_argument(
        "--pool-size",
        type=int,
        default=3,
        help="Number of RLM instances in pool (default: 3)"
    )
    
    args = parser.parse_args()
    
    if not args.api_key:
        parser.error("API key is required. Use --api-key or set LLM_API_KEY environment variable.")
    
    output_dir = None if args.no_save else args.output_dir
    config = {"max_tasks": args.max_tasks}
    
    if args.use_async:
        print("\n" + "#"*80)
        print("RLM BENCHMARK RUNNER - ASYNC MODE")
        print("#"*80)
        
        rlm_pool = create_rlm_pool(
            api_key=args.api_key,
            model=args.model,
            base_url=args.base_url,
            max_depth=args.max_depth,
            wasm_service_url=args.wasm_url,
            wasm_timeout=args.wasm_timeout,
            enable_logging=args.enable_logging,
            pool_size=args.pool_size
        )
        
        async def run_async_benchmarks():
            if args.benchmark == "oolong":
                results = await run_oolong_benchmark_async(
                    rlm_pool, config, output_dir, args.concurrency
                )
            elif args.benchmark == "deep_research":
                results = await run_deep_research_benchmark_async(
                    rlm_pool, config, output_dir, max(1, args.concurrency // 2)
                )
            elif args.benchmark == "ruler":
                results = await run_ruler_benchmark_async(
                    rlm_pool, config, output_dir, args.concurrency
                )
            else:
                results = await run_all_benchmarks_async(
                    rlm_pool, config, output_dir, args.concurrency
                )
            return results
        
        results = asyncio.run(run_async_benchmarks())
    else:
        print("\n" + "#"*80)
        print("RLM BENCHMARK RUNNER - SYNC MODE")
        print("#"*80)
        
        rlm = create_rlm_repl_with_sidecar(
            api_key=args.api_key,
            model=args.model,
            base_url=args.base_url,
            max_depth=args.max_depth,
            wasm_service_url=args.wasm_url,
            wasm_timeout=args.wasm_timeout,
            enable_logging=args.enable_logging
        )
        
        if args.benchmark == "oolong":
            results = run_oolong_benchmark(rlm, config, output_dir)
        elif args.benchmark == "deep_research":
            results = run_deep_research_benchmark(rlm, config, output_dir)
        elif args.benchmark == "ruler":
            results = run_ruler_benchmark(rlm, config, output_dir)
        else:
            results = run_all_benchmarks(rlm, config, output_dir)
    
    print("\n" + "="*80)
    print("Benchmark execution completed!")
    print("="*80)


if __name__ == "__main__":
    main()
