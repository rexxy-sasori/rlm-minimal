# Query Records by (query_id, run_id)

Yes! You can easily extract all related code and LLM records using a `(query_id, run_id)` pair.

## Query Completion Tracking

Yes! The system **does** log when a query finishes and calculates the total duration. Here's how:

### Key Methods:

```python
# Initialize a query run
client.initialize_query_run(query_id, run_id, metadata={"model": "gpt-4o"})

# ... Run your query with LLM interactions and code executions ...

# Complete the query run (calculates total duration automatically)
client.complete_query_run(query_id, run_id, status='completed')

# Get the summary with total duration
summary = client.get_query_run_summary(query_id, run_id)
print(f"Total Duration: {summary['total_duration_ms']:.2f} ms")
print(f"Started: {summary['start_time']}")
print(f"Completed: {summary['end_time']}")
print(f"Status: {summary['status']}")
```

### What's Tracked:

- ✅ **Start Time**: When the query began
- ✅ **End Time**: When the query completed
- ✅ **Total Duration**: Calculated automatically (end_time - start_time)
- ✅ **Status**: 'running', 'completed', or 'error'
- ✅ **Metrics**: LLM interactions, code executions, tokens, cost, errors, and more

## Quick Example

```python
from rlm.logger import TimescaleDBClient
from datetime import datetime, timezone

# Initialize client
client = TimescaleDBClient("postgresql://user:password@localhost:5432/rlm_logs")

# Your query_id and run_id
query_id = "benchmark-query-001"
run_id = datetime.now(timezone.utc)  # Or use actual run_id from your data

# Get all LLM interactions
llm_interactions = client.get_llm_interactions(query_id, run_id)
print(f"Found {len(llm_interactions)} LLM interactions")

# Get all code executions
code_executions = client.get_code_executions(query_id, run_id)
print(f"Found {len(code_executions)} code executions")

# Get aggregated metrics
metrics = client.get_latency_metrics(query_id, run_id)
print(f"Total Cost: ${metrics['total_cost']:.6f}")
print(f"Total Duration: {metrics['total_llm_duration_ms'] + metrics['total_code_duration_ms']:.2f} ms")

# Get token cache statistics
cache_summary = client.get_token_cache_summary(query_id, run_id)
print(f"Cache Hit Rate: {cache_summary['cache_hit_rate_percent']:.2f}%")
print(f"Cost Savings: ${cache_summary['cache_cost_savings']:.6f}")

# Cleanup
client.close()
```

## Available Methods

| Method | Description |
|--------|-------------|
| `get_llm_interactions()` | Get all LLM interactions for the query run |
| `get_code_executions()` | Get all code executions for the query run |
| `get_latency_events()` | Get all latency events (filterable by type) |
| `get_latency_metrics()` | Get aggregated performance metrics |
| `get_slowest_llm_interactions()` | Get slowest LLM calls (for optimization) |
| `get_slowest_code_executions()` | Get slowest code executions (for optimization) |
| `get_token_cache_summary()` | Get token cache statistics and cost savings |
| `get_query_run_summary()` | Get query run metadata and status |

## Documentation

- **[Query API Reference](rlm/logger/doc/QUERY_API.md)**: Complete API documentation
- **[Usage Examples](rlm/logger/examples/query_records_example.py)**: Working code examples
- **[Token Cache Tracking](rlm/logger/doc/TOKEN_CACHE_TRACKING.md)**: Token cache optimization
- **[Quick Start Guide](rlm/logger/doc/QUICKSTART_TIMESCALE.md)**: Getting started with TimescaleDB
