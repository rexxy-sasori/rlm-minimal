"""
Usage examples for TimescaleDB Latency Tracking Client

This demonstrates how to integrate the client with RLM for tracking:
- Code execution latency
- LLM interaction latency
- Using query_id (from benchmark dataset) and run_id (from main script timestamp)
"""

import os
import sys
from datetime import datetime, timezone
from typing import List, Dict, Any

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from rlm.logger.timescale_client import (
    TimescaleDBClient,
    LatencyRecord,
    LLMInteractionRecord,
    CodeExecutionRecord
)


# Initialize client (configure your database URL)
DB_URL = os.getenv("TIMESCALE_DB_URL", "postgresql://user:password@localhost:5432/rlm_logs")
client = TimescaleDBClient(DB_URL, pool_size=10)


def example_1_basic_tracking():
    """Basic example: Tracking LLM and code execution latency."""
    print("\n" + "="*60)
    print("Example 1: Basic Latency Tracking")
    print("="*60)

    # Query ID from benchmark dataset
    query_id = "benchmark-query-001"
    
    # Run ID from main script timestamp
    run_id = datetime.now(timezone.utc)

    # Set context for the current query run
    client.set_context(query_id=query_id, run_id=run_id, iteration=0, depth=0)

    # Initialize query run summary
    client.initialize_query_run(query_id, run_id, metadata={"model": "gpt-5"})

    # Track LLM interaction
    print("\nTracking LLM interaction...")
    with client.track_latency(
        event_type="llm_interaction",
        event_subtype="root_llm",
        metadata={"model": "gpt-5", "tokens": 1000}
    ):
        # Simulate LLM call
        import time
        time.sleep(0.5)

    # Track code execution
    print("\nTracking code execution...")
    with client.track_latency(
        event_type="code_execution",
        event_subtype="python_execution",
        metadata={"code_length": 50}
    ):
        # Simulate code execution
        time.sleep(0.2)

    # Complete query run
    client.complete_query_run(query_id, run_id, status="completed")

    # Get results
    print("\nQuery Run Summary:")
    summary = client.get_query_run_summary(query_id, run_id)
    if summary:
        print(f"  Total duration: {summary['total_duration_ms']:.2f}ms")
        print(f"  LLM interactions: {summary['total_llm_interactions']}")
        print(f"  Code executions: {summary['total_code_executions']}")
        print(f"  Avg LLM latency: {summary['avg_llm_latency_ms']:.2f}ms")
        print(f"  Avg code latency: {summary['avg_code_latency_ms']:.2f}ms")


def example_2_decorator_usage():
    """Using decorators for automatic latency tracking."""
    print("\n" + "="*60)
    print("Example 2: Decorator Usage")
    print("="*60)

    query_id = "benchmark-query-002"
    run_id = datetime.now(timezone.utc)

    client.set_context(query_id=query_id, run_id=run_id)
    client.initialize_query_run(query_id, run_id)

    # Decorator for LLM calls
    @client.track_latency_decorator(
        event_type="llm_interaction",
        event_subtype="recursive_llm",
        metadata={"model": "gpt-5-mini"}
    )
    def call_llm(messages: List[Dict[str, str]]) -> str:
        """Simulated LLM call."""
        import time
        time.sleep(0.3)
        return "LLM response"

    # Decorator for code execution
    @client.track_latency_decorator(
        event_type="code_execution",
        event_subtype="python_execution"
    )
    def execute_code(code: str) -> str:
        """Simulated code execution."""
        import time
        time.sleep(0.1)
        return "Execution result"

    # Use decorated functions
    print("\nCalling LLM...")
    call_llm([{"role": "user", "content": "Hello"}])

    print("\nExecuting code...")
    execute_code("print('hello')")

    client.complete_query_run(query_id, run_id)

    # Get latency metrics
    print("\nLatency Metrics:")
    metrics = client.get_latency_metrics(query_id, run_id)
    for event_type, data in metrics.items():
        print(f"  {event_type}:")
        print(f"    Count: {data['count']}")
        print(f"    Avg: {data['avg_duration_ms']:.2f}ms")
        print(f"    P90: {data['p90_duration_ms']:.2f}ms")


def example_3_detailed_records():
    """Creating detailed records with custom data."""
    print("\n" + "="*60)
    print("Example 3: Detailed Records")
    print("="*60)

    query_id = "benchmark-query-003"
    run_id = datetime.now(timezone.utc)

    client.set_context(query_id=query_id, run_id=run_id)
    client.initialize_query_run(query_id, run_id)

    # Record LLM interaction with detailed metrics
    print("\nRecording LLM interaction...")
    start_time = datetime.now(timezone.utc)
    
    # Simulate LLM call
    import time
    time.sleep(0.4)
    
    end_time = datetime.now(timezone.utc)
    duration_ms = (end_time - start_time).total_seconds() * 1000

    llm_record = LLMInteractionRecord(
        query_id=query_id,
        run_id=run_id,
        model="gpt-5",
        model_type="root",
        prompt_tokens=1500,
        completion_tokens=200,
        total_tokens=1700,
        duration_ms=duration_ms,
        start_time=start_time,
        end_time=end_time,
        context_messages=5,
        context_tokens=1500,
        response_length=500,
        has_tool_calls=True,
        tool_call_count=2,
        success=True,
        metadata={"temperature": 0.7, "max_tokens": 500}
    )

    interaction_id = client.record_llm_interaction(llm_record)
    print(f"  Interaction ID: {interaction_id}")

    # Record code execution
    print("\nRecording code execution...")
    start_time = datetime.now(timezone.utc)
    time.sleep(0.15)
    end_time = datetime.now(timezone.utc)
    duration_ms = (end_time - start_time).total_seconds() * 1000

    code_record = CodeExecutionRecord(
        query_id=query_id,
        run_id=run_id,
        execution_number=1,
        code="result = 2 + 2\nprint(result)",
        stdout="4",
        stderr="",
        output_length=1,
        duration_ms=duration_ms,
        start_time=start_time,
        end_time=end_time,
        success=True,
        metadata={"language": "python"}
    )

    execution_id = client.record_code_execution(code_record)
    print(f"  Execution ID: {execution_id}")

    client.complete_query_run(query_id, run_id)

    # Retrieve detailed data
    print("\nLLM Interactions:")
    interactions = client.get_llm_interactions(query_id, run_id)
    for i, interaction in enumerate(interactions):
        print(f"  [{i+1}] Model: {interaction['model']}, Duration: {interaction['duration_ms']:.2f}ms")
        print(f"     Tokens: {interaction['total_tokens']}, Tool calls: {interaction['tool_call_count']}")

    print("\nCode Executions:")
    executions = client.get_code_executions(query_id, run_id)
    for i, execution in enumerate(executions):
        print(f"  [{i+1}] Execution #{execution['execution_number']}, Duration: {execution['duration_ms']:.2f}ms")
        print(f"     Output: {execution['stdout']}")


def example_4_error_tracking():
    """Tracking errors and failures."""
    print("\n" + "="*60)
    print("Example 4: Error Tracking")
    print("="*60)

    query_id = "benchmark-query-004"
    run_id = datetime.now(timezone.utc)

    client.set_context(query_id=query_id, run_id=run_id)
    client.initialize_query_run(query_id, run_id)

    # Successful operation
    print("\nSuccessful operation...")
    with client.track_latency("code_execution", "python_execution"):
        import time
        time.sleep(0.1)

    # Failed operation
    print("\nFailed operation (expecting error)...")
    try:
        with client.track_latency("code_execution", "python_execution"):
            time.sleep(0.05)
            raise ValueError("Something went wrong")
    except ValueError as e:
        print(f"  Caught expected error: {e}")

    client.complete_query_run(query_id, run_id, status="completed")

    # Get summary with error information
    print("\nQuery Run Summary with Errors:")
    summary = client.get_query_run_summary(query_id, run_id)
    if summary:
        print(f"  Total events: {summary['total_code_executions']}")
        print(f"  Errors: {summary['error_count']}")
        print(f"  Error rate: {summary['error_rate']:.2%}")

    # Get failed events
    print("\nFailed events:")
    events = client.get_latency_events(query_id, run_id, event_type="code_execution")
    for event in events:
        if not event['success']:
            print(f"  Duration: {event['duration_ms']:.2f}ms")
            print(f"  Error: {event['error_type']}: {event['error_message']}")


def example_5_multiple_iterations():
    """Tracking multiple conversation iterations."""
    print("\n" + "="*60)
    print("Example 5: Multiple Iterations")
    print("="*60)

    query_id = "benchmark-query-005"
    run_id = datetime.now(timezone.utc)

    client.set_context(query_id=query_id, run_id=run_id)
    client.initialize_query_run(query_id, run_id)

    # Simulate multiple conversation iterations
    num_iterations = 3
    print(f"\nSimulating {num_iterations} iterations...")

    for iteration in range(num_iterations):
        print(f"\n  Iteration {iteration + 1}:")
        
        # Update context with current iteration
        client.set_context(iteration=iteration + 1)

        # LLM interaction
        print(f"    - LLM interaction...")
        with client.track_latency(
            event_type="llm_interaction",
            event_subtype="root_llm",
            metadata={"iteration": iteration + 1}
        ):
            import time
            time.sleep(0.3 + iteration * 0.1)

        # Code execution (in some iterations)
        if iteration % 2 == 0:
            print(f"    - Code execution...")
            with client.track_latency(
                event_type="code_execution",
                event_subtype="python_execution",
                metadata={"iteration": iteration + 1}
            ):
                time.sleep(0.15)

    client.complete_query_run(query_id, run_id)

    # Get metrics by iteration
    print("\nLatency by Iteration:")
    events = client.get_latency_events(query_id, run_id)
    
    iteration_metrics = {}
    for event in events:
        iter_num = event.get('iteration', 0)
        if iter_num not in iteration_metrics:
            iteration_metrics[iter_num] = []
        iteration_metrics[iter_num].append(event['duration_ms'])

    for iter_num, durations in sorted(iteration_metrics.items()):
        avg_duration = sum(durations) / len(durations)
        print(f"  Iteration {iter_num}: {len(durations)} events, avg {avg_duration:.2f}ms")


def example_6_analytics_queries():
    """Using analytics queries to retrieve insights."""
    print("\n" + "="*60)
    print("Example 6: Analytics Queries")
    print("="*60)

    query_id = "benchmark-query-006"
    run_id = datetime.now(timezone.utc)

    client.set_context(query_id=query_id, run_id=run_id)
    client.initialize_query_run(query_id, run_id)

    # Generate some data
    print("\nGenerating sample data...")
    import time

    for i in range(5):
        with client.track_latency("llm_interaction", "root_llm"):
            time.sleep(0.2 + i * 0.05)

        if i % 2 == 0:
            with client.track_latency("code_execution", "python_execution"):
                time.sleep(0.1 + i * 0.02)

    client.complete_query_run(query_id, run_id)

    # Get comprehensive metrics
    print("\nComprehensive Latency Metrics:")
    metrics = client.get_latency_metrics(query_id, run_id)
    
    for event_type, data in metrics.items():
        print(f"\n  {event_type.upper()}:")
        print(f"    Count: {data['count']}")
        print(f"    Average: {data['avg_duration_ms']:.2f}ms")
        print(f"    P50: {data['p50_duration_ms']:.2f}ms")
        print(f"    P90: {data['p90_duration_ms']:.2f}ms")
        print(f"    P99: {data['p99_duration_ms']:.2f}ms")
        print(f"    Min/Max: {data['min_duration_ms']:.2f}ms / {data['max_duration_ms']:.2f}ms")
        print(f"    Errors: {data['error_count']} ({data['error_rate']:.2%})")

    # Get slowest operations
    print("\nSlowest LLM Interactions:")
    slow_llm = client.get_slowest_llm_interactions(query_id, run_id, n=3)
    for i, interaction in enumerate(slow_llm, 1):
        print(f"  {i}. {interaction['duration_ms']:.2f}ms")

    print("\nSlowest Code Executions:")
    slow_code = client.get_slowest_code_executions(query_id, run_id, n=3)
    for i, execution in enumerate(slow_code, 1):
        print(f"  {i}. {execution['duration_ms']:.2f}ms")


def main():
    """Run all examples."""
    print("\n" + "#"*60)
    print("# TimescaleDB Latency Tracking Client - Usage Examples")
    print("#"*60)

    try:
        example_1_basic_tracking()
        example_2_decorator_usage()
        example_3_detailed_records()
        example_4_error_tracking()
        example_5_multiple_iterations()
        example_6_analytics_queries()

        print("\n" + "#"*60)
        print("# All examples completed successfully!")
        print("#"*60 + "\n")

    except Exception as e:
        print(f"\nError running examples: {e}")
        import traceback
        traceback.print_exc()
    finally:
        client.close()


if __name__ == "__main__":
    main()
