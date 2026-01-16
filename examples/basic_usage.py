#!/usr/bin/env python3
"""
Basic usage example for RLM benchmarks.
Demonstrates how to run a single benchmark.
"""

import sys
import os

# Add project root to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from benchmarks.runner import BenchmarkRunner
from rlm.rlm_repl import RLM_REPL

def main():
    """Run basic benchmark example."""
    print("=== RLM Benchmark Basic Usage Example ===\n")
    
    # Initialize RLM model
    print("Initializing RLM model...")
    try:
        model = RLM_REPL(model_name="gpt-5-mini")
        print("RLM model initialized successfully!\n")
    except Exception as e:
        print(f"Error initializing model: {e}")
        print("Using mock model for demonstration...\n")
        # Create mock model
        from unittest.mock import Mock
        model = Mock()
        model.completion.return_value = {
            "choices": [{"message": {"content": "Test response"}}]
        }
    
    # Create benchmark runner
    runner = BenchmarkRunner()
    
    # Add RULER benchmark (simplest for demonstration)
    print("Adding RULER benchmark...")
    runner.add_benchmark("ruler", {
        "max_tasks": 5,
        "context_lengths": [1000, 5000],
        "verbose": True
    })
    
    # Run benchmark
    print("\nRunning RULER benchmark...")
    print("=" * 60)
    
    # Run with reduced context lengths for faster demonstration
    results = runner.run_benchmark("ruler", model, output_dir="example_results")
    
    print("\n" + "=" * 60)
    print("Benchmark completed!")
    print(f"Results saved to: example_results/")
    print(f"Number of tasks evaluated: {len(results)}")
    
    # Show sample result
    if results:
        print("\nSample result:")
        print(f"Task ID: {results[0]['task_id']}")
        print(f"Context Length: {results[0]['context_length']}")
        print(f"Correct: {results[0]['correct']}")
        print(f"Response: {results[0]['response'][:100]}...")

if __name__ == "__main__":
    main()
