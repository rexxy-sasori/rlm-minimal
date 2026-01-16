"""
Query Records Example

This demonstrates how to extract all related code and LLM records
for a given (query_id, run_id) pair.
"""

import os
import sys
from datetime import datetime, timezone
from typing import Dict, List, Any

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from rlm.logger import TimescaleDBClient


# Initialize client
DB_URL = os.getenv("TIMESCALE_DB_URL", "postgresql://user:password@localhost:5432/rlm_logs")
client = TimescaleDBClient(DB_URL, pool_size=10)


def example_1_get_all_records_for_query_run():
    """Example: Get all records for a specific query_id and run_id."""
    print("\n" + "="*70)
    print("Example 1: Get All Records for (query_id, run_id)")
    print("="*70)
    
    # Your query_id and run_id
    query_id = "benchmark-query-001"
    run_id = datetime.now(timezone.utc)  # Or use actual run_id from your data
    
    print(f"\nQuery ID: {query_id}")
    print(f"Run ID: {run_id}")
    
    # Get all LLM interactions
    print("\n" + "-"*70)
    print("LLM Interactions:")
    print("-"*70)
    llm_interactions = client.get_llm_interactions(query_id, run_id)
    
    if llm_interactions:
        print(f"Found {len(llm_interactions)} LLM interactions:")
        for i, interaction in enumerate(llm_interactions, 1):
            print(f"\n  Interaction {i}:")
            print(f"    Model: {interaction.get('model')}")
            print(f"    Duration: {interaction.get('duration_ms', 0):.2f} ms")
            print(f"    Prompt Tokens: {interaction.get('prompt_tokens', 0)}")
            print(f"    Completion Tokens: {interaction.get('completion_tokens', 0)}")
            print(f"    Cached Tokens: {interaction.get('cached_tokens', 0)}")
            print(f"    Total Cost: ${interaction.get('total_cost', 0):.6f}")
            print(f"    Success: {interaction.get('success', True)}")
    else:
        print("  No LLM interactions found.")
    
    # Get all code executions
    print("\n" + "-"*70)
    print("Code Executions:")
    print("-"*70)
    code_executions = client.get_code_executions(query_id, run_id)
    
    if code_executions:
        print(f"Found {len(code_executions)} code executions:")
        for i, execution in enumerate(code_executions, 1):
            print(f"\n  Execution {i}:")
            print(f"    Duration: {execution.get('duration_ms', 0):.2f} ms")
            print(f"    Success: {execution.get('success', True)}")
            print(f"    Output Length: {execution.get('output_length', 0)} chars")
            if not execution.get('success', True):
                print(f"    Error: {execution.get('error_message', 'N/A')}")
    else:
        print("  No code executions found.")
    
    # Get all latency events
    print("\n" + "-"*70)
    print("Latency Events:")
    print("-"*70)
    latency_events = client.get_latency_events(query_id, run_id)
    
    if latency_events:
        print(f"Found {len(latency_events)} latency events:")
        for i, event in enumerate(latency_events, 1):
            print(f"\n  Event {i}:")
            print(f"    Type: {event.get('event_type')}")
            print(f"    Subtype: {event.get('event_subtype', 'N/A')}")
            print(f"    Duration: {event.get('duration_ms', 0):.2f} ms")
            print(f"    Iteration: {event.get('iteration', 'N/A')}")
            print(f"    Depth: {event.get('depth', 'N/A')}")
    else:
        print("  No latency events found.")


def example_2_get_detailed_summary():
    """Example: Get a detailed summary for a query run."""
    print("\n" + "="*70)
    print("Example 2: Get Detailed Summary for Query Run")
    print("="*70)
    
    query_id = "benchmark-query-001"
    run_id = datetime.now(timezone.utc)
    
    # Get overall latency metrics
    print("\n" + "-"*70)
    print("Latency Metrics Summary:")
    print("-"*70)
    metrics = client.get_latency_metrics(query_id, run_id)
    
    if metrics:
        print(f"\nTotal LLM Interactions: {metrics.get('total_llm_interactions', 0)}")
        print(f"Total Code Executions: {metrics.get('total_code_executions', 0)}")
        print(f"Total Latency Events: {metrics.get('total_latency_events', 0)}")
        print(f"\nLLM Metrics:")
        print(f"  Total Duration: {metrics.get('total_llm_duration_ms', 0):.2f} ms")
        print(f"  Avg Duration: {metrics.get('avg_llm_duration_ms', 0):.2f} ms")
        print(f"  Min Duration: {metrics.get('min_llm_duration_ms', 0):.2f} ms")
        print(f"  Max Duration: {metrics.get('max_llm_duration_ms', 0):.2f} ms")
        print(f"\nCode Execution Metrics:")
        print(f"  Total Duration: {metrics.get('total_code_duration_ms', 0):.2f} ms")
        print(f"  Avg Duration: {metrics.get('avg_code_duration_ms', 0):.2f} ms")
        print(f"  Min Duration: {metrics.get('min_code_duration_ms', 0):.2f} ms")
        print(f"  Max Duration: {metrics.get('max_code_duration_ms', 0):.2f} ms")
        print(f"\nToken Metrics:")
        print(f"  Total Prompt Tokens: {metrics.get('total_prompt_tokens', 0)}")
        print(f"  Total Completion Tokens: {metrics.get('total_completion_tokens', 0)}")
        print(f"  Total Cached Tokens: {metrics.get('total_cached_tokens', 0)}")
        print(f"  Total Cost: ${metrics.get('total_cost', 0):.6f}")
    else:
        print("  No metrics found for this query run.")


def example_3_get_token_cache_summary():
    """Example: Get token cache optimization summary."""
    print("\n" + "="*70)
    print("Example 3: Token Cache Optimization Summary")
    print("="*70)
    
    query_id = "benchmark-query-001"
    run_id = datetime.now(timezone.utc)
    
    # Get token cache summary
    print("\n" + "-"*70)
    print("Token Cache Summary:")
    print("-"*70)
    cache_summary = client.get_token_cache_summary(query_id, run_id)
    
    if cache_summary:
        print(f"\nTotal Prompt Tokens: {cache_summary.get('total_prompt_tokens', 0)}")
        print(f"Total Cached Tokens: {cache_summary.get('total_cached_tokens', 0)}")
        print(f"Total Uncached Tokens: {cache_summary.get('total_uncached_prompt_tokens', 0)}")
        print(f"Cache Hit Rate: {cache_summary.get('cache_hit_rate_percent', 0):.2f}%")
        print(f"\nCost Savings from Cache:")
        print(f"  Total Cost Without Cache: ${cache_summary.get('total_cost_without_cache', 0):.6f}")
        print(f"  Total Cost With Cache: ${cache_summary.get('total_cost_with_cache', 0):.6f}")
        print(f"  Savings: ${cache_summary.get('cache_cost_savings', 0):.6f}")
        print(f"  Savings Percentage: {cache_summary.get('cache_savings_percent', 0):.2f}%")
    else:
        print("  No token cache data found.")


def example_4_get_slowest_operations():
    """Example: Get slowest LLM interactions and code executions."""
    print("\n" + "="*70)
    print("Example 4: Get Slowest Operations")
    print("="*70)
    
    query_id = "benchmark-query-001"
    run_id = datetime.now(timezone.utc)
    
    # Get slowest LLM interactions
    print("\n" + "-"*70)
    print("Slowest LLM Interactions (Top 5):")
    print("-"*70)
    slowest_llm = client.get_slowest_llm_interactions(query_id, run_id, n=5)
    
    if slowest_llm:
        for i, interaction in enumerate(slowest_llm, 1):
            print(f"\n  {i}. {interaction.get('model')}: {interaction.get('duration_ms', 0):.2f} ms")
            print(f"     Prompt Tokens: {interaction.get('prompt_tokens', 0)}")
    else:
        print("  No LLM interactions found.")
    
    # Get slowest code executions
    print("\n" + "-"*70)
    print("Slowest Code Executions (Top 5):")
    print("-"*70)
    slowest_code = client.get_slowest_code_executions(query_id, run_id, n=5)
    
    if slowest_code:
        for i, execution in enumerate(slowest_code, 1):
            print(f"\n  {i}. {execution.get('duration_ms', 0):.2f} ms")
            print(f"     Success: {execution.get('success', True)}")
    else:
        print("  No code executions found.")


def example_5_get_query_run_summary():
    """Example: Get query run summary."""
    print("\n" + "="*70)
    print("Example 5: Get Query Run Summary")
    print("="*70)
    
    query_id = "benchmark-query-001"
    run_id = datetime.now(timezone.utc)
    
    # Get query run summary
    print("\n" + "-"*70)
    print("Query Run Summary:")
    print("-"*70)
    summary = client.get_query_run_summary(query_id, run_id)
    
    if summary:
        print(f"\nQuery ID: {summary.get('query_id')}")
        print(f"Run ID: {summary.get('run_id')}")
        print(f"Started At: {summary.get('started_at')}")
        print(f"Completed At: {summary.get('completed_at')}")
        print(f"Status: {summary.get('status')}")
        print(f"Iterations: {summary.get('iterations', 0)}")
        print(f"\nMetadata: {json.dumps(summary.get('metadata', {}), indent=2)}")
    else:
        print("  No query run summary found.")


if __name__ == "__main__":
    try:
        # Run all examples
        example_1_get_all_records_for_query_run()
        example_2_get_detailed_summary()
        example_3_get_token_cache_summary()
        example_4_get_slowest_operations()
        example_5_get_query_run_summary()
        
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
