"""
Completion Tracking Example

This demonstrates how to track when a query starts, completes,
and calculate the total duration.
"""

import os
import sys
from datetime import datetime, timezone
from typing import Dict, Any

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from rlm.logger import TimescaleDBClient


# Initialize client
DB_URL = os.getenv("TIMESCALE_DB_URL", "postgresql://user:password@localhost:5432/rlm_logs")
client = TimescaleDBClient(DB_URL, pool_size=10)


def example_1_basic_completion_tracking():
    """Basic example: Track query from start to finish."""
    print("\n" + "="*70)
    print("Example 1: Basic Completion Tracking")
    print("="*70)
    
    # Your query_id
    query_id = "benchmark-query-001"
    run_id = datetime.now(timezone.utc)
    
    print(f"\nQuery ID: {query_id}")
    print(f"Run ID: {run_id}")
    
    # Step 1: Initialize the query run
    print("\n1. Initializing query run...")
    client.initialize_query_run(
        query_id,
        run_id,
        metadata={
            "model": "gpt-4o",
            "max_iterations": 20,
            "description": "Needle in haystack example"
        }
    )
    
    # Step 2: ... Run your query with LLM interactions and code executions ...
    print("\n2. Running query (simulating LLM calls and code execution)...")
    
    # Simulate some work
    import time
    time.sleep(0.1)
    
    # Step 3: Complete the query run
    print("\n3. Completing query run...")
    client.complete_query_run(query_id, run_id, status='completed')
    
    # Step 4: Get the summary
    print("\n4. Getting query run summary...")
    summary = client.get_query_run_summary(query_id, run_id)
    
    if summary:
        print(f"\nQuery Run Summary:")
        print(f"  Status: {summary['status']}")
        print(f"  Started: {summary['start_time']}")
        print(f"  Completed: {summary['end_time']}")
        print(f"  Total Duration: {summary['total_duration_ms']:.2f} ms")
        print(f"  LLM Interactions: {summary['total_llm_interactions']}")
        print(f"  Code Executions: {summary['total_code_executions']}")
        print(f"  Error Count: {summary['error_count']}")
        print(f"  Error Rate: {summary['error_rate']:.2%}" if summary['error_rate'] else "  Error Rate: N/A")


def example_2_detailed_summary():
    """Example: Get detailed summary with all metrics."""
    print("\n" + "="*70)
    print("Example 2: Detailed Query Run Summary")
    print("="*70)
    
    query_id = "benchmark-query-001"
    run_id = datetime.now(timezone.utc)
    
    # Initialize and complete (in real usage, this would have actual data)
    client.initialize_query_run(query_id, run_id)
    client.complete_query_run(query_id, run_id)
    
    # Get summary
    summary = client.get_query_run_summary(query_id, run_id)
    
    if summary:
        print(f"\nDetailed Summary for {query_id}:")
        print("\nTiming:")
        print(f"  Start Time: {summary['start_time']}")
        print(f"  End Time: {summary['end_time']}")
        print(f"  Total Duration: {summary['total_duration_ms']:.2f} ms")
        
        print("\nEvent Counts:")
        print(f"  LLM Interactions: {summary['total_llm_interactions']}")
        print(f"  Code Executions: {summary['total_code_executions']}")
        print(f"  Tool Calls: {summary['total_tool_calls']}")
        
        print("\nLLM Latency Metrics (ms):")
        print(f"  Average: {summary['avg_llm_latency_ms']:.2f}")
        print(f"  P50: {summary['p50_llm_latency_ms']:.2f}")
        print(f"  P90: {summary['p90_llm_latency_ms']:.2f}")
        print(f"  P99: {summary['p99_llm_latency_ms']:.2f}")
        
        print("\nCode Execution Latency Metrics (ms):")
        print(f"  Average: {summary['avg_code_latency_ms']:.2f}")
        print(f"  P50: {summary['p50_code_latency_ms']:.2f}")
        print(f"  P90: {summary['p90_code_latency_ms']:.2f}")
        print(f"  P99: {summary['p99_code_latency_ms']:.2f}")
        
        print("\nToken Metrics:")
        print(f"  Total LLM Tokens: {summary['total_llm_tokens']}")
        print(f"  Prompt Tokens: {summary['total_prompt_tokens']}")
        print(f"  Completion Tokens: {summary['total_completion_tokens']}")
        print(f"  Cached Tokens: {summary['total_cached_tokens']}")
        print(f"  Cache Hit Rate: {summary['cache_hit_rate']:.2%}" if summary['cache_hit_rate'] else "  Cache Hit Rate: N/A")
        
        print("\nCost Metrics:")
        print(f"  Total Cost: ${summary['total_cost']:.6f}" if summary['total_cost'] else "  Total Cost: N/A")
        print(f"  Avg Cost per Interaction: ${summary['avg_cost_per_interaction']:.6f}" if summary['avg_cost_per_interaction'] else "  Avg Cost per Interaction: N/A")
        
        print("\nError Metrics:")
        print(f"  Error Count: {summary['error_count']}")
        print(f"  Error Rate: {summary['error_rate']:.2%}" if summary['error_rate'] else "  Error Rate: N/A")


def example_3_error_handling():
    """Example: Track failed queries."""
    print("\n" + "="*70)
    print("Example 3: Error Handling and Status Tracking")
    print("="*70)
    
    query_id = "benchmark-query-002"
    run_id = datetime.now(timezone.utc)
    
    print(f"\nSimulating a failed query run...")
    
    client.initialize_query_run(query_id, run_id)
    
    # Simulate an error
    try:
        # ... something goes wrong ...
        raise Exception("Simulated error")
    except Exception as e:
        print(f"\nError occurred: {e}")
        client.complete_query_run(query_id, run_id, status='error')
    
    # Get summary
    summary = client.get_query_run_summary(query_id, run_id)
    
    if summary:
        print(f"\nQuery Run Summary:")
        print(f"  Status: {summary['status']}")
        print(f"  Started: {summary['start_time']}")
        print(f"  Completed: {summary['end_time']}")
        print(f"  Total Duration: {summary['total_duration_ms']:.2f} ms")


def example_4_update_summary():
    """Example: Update summary during long-running queries."""
    print("\n" + "="*70)
    print("Example 4: Update Summary During Execution")
    print("="*70)
    
    query_id = "benchmark-query-003"
    run_id = datetime.now(timezone.utc)
    
    print(f"\nInitializing query run...")
    client.initialize_query_run(query_id, run_id)
    
    # ... perform some operations ...
    print("\nPerforming operations...")
    
    # Update summary to get current metrics
    print("\nUpdating summary (mid-execution)...")
    client.update_query_run_summary(query_id, run_id)
    
    # Get intermediate summary
    summary = client.get_query_run_summary(query_id, run_id)
    print(f"\nIntermediate Summary:")
    print(f"  Status: {summary['status']}")
    print(f"  Current LLM Interactions: {summary['total_llm_interactions']}")
    print(f"  Current Code Executions: {summary['total_code_executions']}")
    
    # ... continue operations ...
    
    # Complete the query
    print("\nCompleting query run...")
    client.complete_query_run(query_id, run_id)


def example_5_batch_summary():
    """Example: Get summaries for multiple query runs."""
    print("\n" + "="*70)
    print("Example 5: Batch Query Run Summaries")
    print("="*70)
    
    # Get summaries for all runs of a query
    query_id = "benchmark-query-001"
    
    print(f"\nGetting all summaries for query: {query_id}")
    
    # Note: This requires a custom query since there's no built-in method
    # for batch retrieval (you can add one if needed)
    
    cursor = client._execute("""
        SELECT * FROM query_run_summaries
        WHERE query_id = %(query_id)s
        ORDER BY start_time DESC
        LIMIT 10
    "", {'query_id': query_id})
    
    results = cursor.fetchall()
    
    if results:
        print(f"\nFound {len(results)} query runs:")
        for i, result in enumerate(results, 1):
            print(f"\n  {i}. Run ID: {result['run_id']}")
            print(f"     Status: {result['status']}")
            print(f"     Duration: {result['total_duration_ms']:.2f} ms")
            print(f"     LLM Calls: {result['total_llm_interactions']}")
            print(f"     Cost: ${result['total_cost']:.6f}" if result['total_cost'] else "     Cost: N/A")


if __name__ == "__main__":
    try:
        # Run all examples
        example_1_basic_completion_tracking()
        example_2_detailed_summary()
        example_3_error_handling()
        example_4_update_summary()
        example_5_batch_summary()
        
        print("\n" + "="*70)
        print("All examples completed successfully!")
        print("="*70)
        
    except Exception as e:
        print(f"\nError: {e}")
        import traceback
        traceback.print_exc()
    finally:
        # Cleanup
        client.close()
