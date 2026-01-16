#!/usr/bin/env python3
"""
Model comparison example for RLM benchmarks.
Demonstrates how to compare multiple models on the same benchmark.
"""

import sys
import os

# Add project root to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from benchmarks.runner import BenchmarkRunner
from rlm.rlm_repl import RLM_REPL

def create_mock_model(name):
    """Create mock model for demonstration."""
    from unittest.mock import Mock
    model = Mock()
    
    # Create different responses based on model name
    if name == "gpt-5-mini":
        # Simulate good performance
        model.completion.return_value = {
            "choices": [{"message": {"content": "Found the needle: NEEDLE:TEST123"}}]
        }
    elif name == "gpt-5":
        # Simulate moderate performance
        model.completion.return_value = {
            "choices": [{"message": {"content": "The needle is probably somewhere in the context"}}]
        }
    else:
        # Simulate poor performance
        model.completion.return_value = {
            "choices": [{"message": {"content": "I couldn't find the needle"}}]
        }
    
    return model

def main():
    """Run model comparison example."""
    print("=== RLM Benchmark Model Comparison Example ===\n")
    
    # Create benchmark runner
    runner = BenchmarkRunner()
    
    # Add RULER benchmark
    print("Adding RULER benchmark...")
    runner.add_benchmark("ruler", {
        "max_tasks": 10,
        "context_lengths": [1000, 5000],
        "verbose": True
    })
    
    # Create models for comparison
    print("\nCreating models for comparison...")
    
    # Try to initialize real models, fallback to mock
    models = {}
    
    try:
        # Try to create real RLM models
        models["RLM (gpt-5-mini)"] = RLM_REPL(model_name="gpt-5-mini")
        print("Created real RLM model: gpt-5-mini")
    except Exception as e:
        print(f"Error creating real model: {e}")
        print("Using mock models for demonstration...\n")
        
        # Create mock models
        models["RLM (gpt-5-mini)"] = create_mock_model("gpt-5-mini")
        models["GPT-5 (baseline)"] = create_mock_model("gpt-5")
        models["GPT-4o (control)"] = create_mock_model("gpt-4o")
    
    # Run model comparison
    print("\nRunning model comparison...")
    print("=" * 70)
    
    comparison_results = runner.compare_models(
        models=models,
        benchmark_name="ruler",
        output_dir="comparison_results"
    )
    
    print("\n" + "=" * 70)
    print("Model comparison completed!")
    print(f"Comparison results saved to: comparison_results/")
    print(f"Models compared: {list(models.keys())}")
    
    # Show comparison summary
    print("\n=== Comparison Summary ===")
    for model_name, results in comparison_results.items():
        correct = sum(1 for r in results if r.get("correct", False))
        total = len(results)
        accuracy = correct / total if total > 0 else 0
        print(f"{model_name}: {correct}/{total} ({accuracy:.2%}) correct")
    
    print("\nDetailed comparison report saved to: comparison_results/ruler_comparison_report.txt")

if __name__ == "__main__":
    main()
