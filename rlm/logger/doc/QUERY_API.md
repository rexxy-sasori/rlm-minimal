# Query API Reference

This document describes all the methods available to query and retrieve records using `query_id` and `run_id`.

## Overview

Given a `(query_id, run_id)` pair, you can extract all related records including:
- LLM interactions
- Code executions
- Latency events
- Token cache statistics
- Performance metrics

## Available Methods

### 1. Get LLM Interactions

```python
def get_llm_interactions(self, query_id: str, run_id: datetime) -> List[Dict[str, Any]]:
    """
    Get all LLM interactions for a specific query run.
    
    Args:
        query_id: The query identifier
        run_id: The run timestamp
    
    Returns:
        List of LLM interaction records
    """
```

**Example:**
```python
interactions = client.get_llm_interactions(query_id, run_id)
for interaction in interactions:
    print(f"Model: {interaction['model']}")
    print(f"Duration: {interaction['duration_ms']:.2f} ms")
    print(f"Cached Tokens: {interaction['cached_tokens']}")
```

### 2. Get Code Executions

```python
def get_code_executions(self, query_id: str, run_id: datetime) -> List[Dict[str, Any]]:
    """
    Get all code executions for a specific query run.
    
    Args:
        query_id: The query identifier
        run_id: The run timestamp
    
    Returns:
        List of code execution records
    """
```

**Example:**
```python
executions = client.get_code_executions(query_id, run_id)
for execution in executions:
    print(f"Duration: {execution['duration_ms']:.2f} ms")
    print(f"Success: {execution['success']}")
```

### 3. Get Latency Events

```python
def get_latency_events(self, query_id: str, run_id: datetime, 
                       event_type: Optional[str] = None) -> List[Dict[str, Any]]:
    """
    Get all latency events for a specific query run.
    
    Args:
        query_id: The query identifier
        run_id: The run timestamp
        event_type: Optional filter by event type (e.g., 'llm', 'code')
    
    Returns:
        List of latency event records
    """
```

**Example:**
```python
# Get all events
events = client.get_latency_events(query_id, run_id)

# Get only LLM events
llm_events = client.get_latency_events(query_id, run_id, event_type='llm')

# Get only code events
code_events = client.get_latency_events(query_id, run_id, event_type='code')
```

### 4. Get Latency Metrics

```python
def get_latency_metrics(self, query_id: str, run_id: datetime) -> Dict[str, Any]:
    """
    Get comprehensive latency metrics for a query run.
    
    Args:
        query_id: The query identifier
        run_id: The run timestamp
    
    Returns:
        Dictionary containing aggregated metrics
    """
```

**Example:**
```python
metrics = client.get_latency_metrics(query_id, run_id)
print(f"Total LLM Duration: {metrics['total_llm_duration_ms']:.2f} ms")
print(f"Avg Code Duration: {metrics['avg_code_duration_ms']:.2f} ms")
print(f"Total Cost: ${metrics['total_cost']:.6f}")
```

**Returned metrics include:**
- `total_llm_interactions`: Count of LLM calls
- `total_code_executions`: Count of code executions
- `total_latency_events`: Total number of events
- `total_llm_duration_ms`: Sum of all LLM durations
- `avg_llm_duration_ms`: Average LLM duration
- `min_llm_duration_ms`: Fastest LLM call
- `max_llm_duration_ms`: Slowest LLM call
- `total_code_duration_ms`: Sum of all code durations
- `avg_code_duration_ms`: Average code execution time
- `min_code_duration_ms`: Fastest code execution
- `max_code_duration_ms`: Slowest code execution
- `total_prompt_tokens`: Total prompt tokens used
- `total_completion_tokens`: Total completion tokens
- `total_cached_tokens`: Total cached tokens
- `total_cost`: Total cost of LLM calls

### 5. Get Slowest LLM Interactions

```python
def get_slowest_llm_interactions(self, query_id: str, run_id: datetime, 
                                 n: int = 10) -> List[Dict[str, Any]]:
    """
    Get the slowest LLM interactions for a query run.
    
    Args:
        query_id: The query identifier
        run_id: The run timestamp
        n: Number of slowest interactions to return (default: 10)
    
    Returns:
        List of slowest LLM interactions, sorted by duration
    """
```

**Example:**
```python
slowest = client.get_slowest_llm_interactions(query_id, run_id, n=5)
for i, interaction in enumerate(slowest, 1):
    print(f"{i}. {interaction['model']}: {interaction['duration_ms']:.2f} ms")
```

### 6. Get Slowest Code Executions

```python
def get_slowest_code_executions(self, query_id: str, run_id: datetime, 
                                n: int = 10) -> List[Dict[str, Any]]:
    """
    Get the slowest code executions for a query run.
    
    Args:
        query_id: The query identifier
        run_id: The run timestamp
        n: Number of slowest executions to return (default: 10)
    
    Returns:
        List of slowest code executions, sorted by duration
    """
```

**Example:**
```python
slowest = client.get_slowest_code_executions(query_id, run_id, n=5)
for i, execution in enumerate(slowest, 1):
    print(f"{i}. {execution['duration_ms']:.2f} ms")
```

### 7. Get Token Cache Summary

```python
def get_token_cache_summary(self, query_id: str, run_id: datetime) -> Optional[Dict[str, Any]]:
    """
    Get token cache optimization summary for a query run.
    
    Args:
        query_id: The query identifier
        run_id: The run timestamp
    
    Returns:
        Dictionary containing cache statistics and cost savings
    """
```

**Example:**
```python
cache_summary = client.get_token_cache_summary(query_id, run_id)
if cache_summary:
    print(f"Cache Hit Rate: {cache_summary['cache_hit_rate_percent']:.2f}%")
    print(f"Cost Savings: ${cache_summary['cache_cost_savings']:.6f}")
    print(f"Savings Percentage: {cache_summary['cache_savings_percent']:.2f}%")
```

**Returned metrics include:**
- `total_prompt_tokens`: Total prompt tokens
- `total_cached_tokens`: Tokens served from cache
- `total_uncached_prompt_tokens`: Tokens not from cache
- `cache_hit_rate_percent`: Percentage of tokens from cache
- `total_cost_without_cache`: Hypothetical cost without cache
- `total_cost_with_cache`: Actual cost with cache
- `cache_cost_savings`: Dollar amount saved
- `cache_savings_percent`: Percentage saved

### 8. Get Query Run Summary

```python
def get_query_run_summary(self, query_id: str, run_id: datetime) -> Optional[Dict[str, Any]]:
    """
    Get the query run summary.
    
    Args:
        query_id: The query identifier
        run_id: The run timestamp
    
    Returns:
        Dictionary containing query run metadata
    """
```

**Example:**
```python
summary = client.get_query_run_summary(query_id, run_id)
if summary:
    print(f"Status: {summary['status']}")
    print(f"Iterations: {summary['iterations']}")
    print(f"Metadata: {summary['metadata']}")
```

**Returned fields include:**
- `query_id`: Query identifier
- `run_id`: Run timestamp
- `started_at`: When the run started
- `completed_at`: When the run completed
- `status`: Run status (e.g., 'completed', 'failed')
- `iterations`: Number of iterations
- `metadata`: Additional metadata

## Usage Patterns

### Pattern 1: Complete Query Run Analysis

```python
# Get all data for a query run
llm_interactions = client.get_llm_interactions(query_id, run_id)
code_executions = client.get_code_executions(query_id, run_id)
latency_events = client.get_latency_events(query_id, run_id)
metrics = client.get_latency_metrics(query_id, run_id)
cache_summary = client.get_token_cache_summary(query_id, run_id)

# Analyze the data
total_duration = metrics['total_llm_duration_ms'] + metrics['total_code_duration_ms']
total_tokens = metrics['total_prompt_tokens'] + metrics['total_completion_tokens']

print(f"Total Duration: {total_duration:.2f} ms")
print(f"Total Tokens: {total_tokens}")
print(f"Total Cost: ${metrics['total_cost']:.6f}")
```

### Pattern 2: Performance Optimization

```python
# Find slow operations
slow_llm = client.get_slowest_llm_interactions(query_id, run_id, n=5)
slow_code = client.get_slowest_code_executions(query_id, run_id, n=5)

# Analyze cache effectiveness
cache_summary = client.get_token_cache_summary(query_id, run_id)
if cache_summary:
    hit_rate = cache_summary['cache_hit_rate_percent']
    if hit_rate < 50:
        print(f"Low cache hit rate: {hit_rate:.2f}% - consider optimization")
```

### Pattern 3: Cost Analysis

```python
# Get cost breakdown
metrics = client.get_latency_metrics(query_id, run_id)
cache_summary = client.get_token_cache_summary(query_id, run_id)

print(f"Total Cost: ${metrics['total_cost']:.6f}")
if cache_summary:
    print(f"Cost Saved by Cache: ${cache_summary['cache_cost_savings']:.6f}")
    print(f"Effective Cost: ${metrics['total_cost'] - cache_summary['cache_cost_savings']:.6f}")
```

### Pattern 4: Error Analysis

```python
# Get all failed operations
llm_interactions = client.get_llm_interactions(query_id, run_id)
code_executions = client.get_code_executions(query_id, run_id)

failed_llm = [i for i in llm_interactions if not i['success']]
failed_code = [e for e in code_executions if not e['success']]

print(f"Failed LLM Interactions: {len(failed_llm)}")
print(f"Failed Code Executions: {len(failed_code)}")

for failure in failed_llm:
    print(f"Error: {failure['error_message']}")
```

## Best Practices

1. **Always close the client**: Use `client.close()` when done
2. **Handle None returns**: Methods may return None if no data exists
3. **Use context managers**: Consider using `with TimescaleDBClient(...) as client:`
4. **Batch queries**: For multiple query runs, consider querying in batches
5. **Filter early**: Use event_type filters to reduce data transfer

## Example: Complete Query Run Report

```python
def generate_query_run_report(client, query_id, run_id):
    """Generate a comprehensive report for a query run."""
    
    # Get all data
    metrics = client.get_latency_metrics(query_id, run_id)
    cache_summary = client.get_token_cache_summary(query_id, run_id)
    slow_llm = client.get_slowest_llm_interactions(query_id, run_id, n=3)
    slow_code = client.get_slowest_code_executions(query_id, run_id, n=3)
    
    # Generate report
    report = {
        'query_id': query_id,
        'run_id': run_id.isoformat(),
        'metrics': metrics,
        'cache_analysis': cache_summary,
        'performance_issues': {
            'slow_llm_calls': slow_llm,
            'slow_code_executions': slow_code
        }
    }
    
    return report

# Usage
report = generate_query_run_report(client, query_id, run_id)
print(json.dumps(report, indent=2, default=str))
```
