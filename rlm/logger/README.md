# RLM Logger Package

Comprehensive logging solution for RLM (Recursive Language Model) with TimescaleDB integration for latency tracking.

## Features

- **ColorfulLogger**: Console logging with ANSI colors for better readability
- **REPLEnvLogger**: Rich-formatted logging for code executions (Jupyter-style)
- **TimescaleDBClient**: Database-backed latency tracking for:
  - Code execution latency
  - LLM interaction latency
  - Query and run-level aggregation
  - Real-time metrics

## Installation

### 1. Install TimescaleDB

```bash
# Using Docker
docker run -d --name timescaledb -p 5432:5432 \
  -e POSTGRES_PASSWORD=password \
  timescale/timescaledb:latest-pg16

# Or install locally (see TimescaleDB documentation)
```

### 2. Create Database

```sql
CREATE DATABASE rlm_logs;
\c rlm_logs
CREATE EXTENSION timescaledb;
```

### 3. Run Schema Migration

```bash
psql -h localhost -U postgres -d rlm_logs -f rlm/logger/timescale_schema.sql
```

### 4. Install Python Dependencies

```bash
pip install psycopg2-binary python-dotenv
```

## Quick Start

### Basic Usage

```python
from datetime import datetime, timezone
from rlm.logger.timescale_client import TimescaleDBClient

# Initialize client
client = TimescaleDBClient(
    "postgresql://user:password@localhost:5432/rlm_logs",
    pool_size=10
)

# Query ID from benchmark dataset
query_id = "benchmark-query-001"

# Run ID from main script timestamp
run_id = datetime.now(timezone.utc)

# Set context
client.set_context(query_id=query_id, run_id=run_id)

# Initialize query run
client.initialize_query_run(query_id, run_id)

# Track latency with context manager
with client.track_latency(
    event_type="llm_interaction",
    event_subtype="root_llm",
    metadata={"model": "gpt-5"}
):
    # Your code here
    response = llm.completion(messages)

# Complete query run
client.complete_query_run(query_id, run_id)

# Get metrics
metrics = client.get_latency_metrics(query_id, run_id)
print(metrics)

# Close client
client.close()
```

### Using Decorators

```python
from rlm.logger.timescale_client import TimescaleDBClient

client = TimescaleDBClient("postgresql://...")
client.set_context(query_id="query-001", run_id=datetime.now(timezone.utc))

@client.track_latency_decorator(
    event_type="llm_interaction",
    event_subtype="recursive_llm"
)
def call_recursive_llm(prompt):
    # Function implementation
    return llm.completion(prompt)

@client.track_latency_decorator(
    event_type="code_execution",
    event_subtype="python_execution"
)
def execute_code(code):
    # Function implementation
    return exec(code)

# Usage
response = call_recursive_llm("Hello")
result = execute_code("2 + 2")
```

### Detailed Records

```python
from rlm.logger.timescale_client import (
    TimescaleDBClient,
    LLMInteractionRecord,
    CodeExecutionRecord
)

client = TimescaleDBClient("postgresql://...")

# LLM Interaction
llm_record = LLMInteractionRecord(
    query_id="query-001",
    run_id=datetime.now(timezone.utc),
    model="gpt-5",
    model_type="root",
    prompt_tokens=1500,
    completion_tokens=200,
    total_tokens=1700,
    duration_ms=500.5,
    start_time=start_time,
    end_time=end_time,
    has_tool_calls=True,
    tool_call_count=2,
    success=True
)
client.record_llm_interaction(llm_record)

# Code Execution
code_record = CodeExecutionRecord(
    query_id="query-001",
    run_id=datetime.now(timezone.utc),
    execution_number=1,
    code="print('hello')",
    stdout="hello",
    stderr="",
    duration_ms=12.3,
    start_time=start_time,
    end_time=end_time,
    success=True
)
client.record_code_execution(code_record)
```

## RLM Integration

### Using RLM_REPL_With_Timescale

```python
import os
from rlm.logger.rlm_integration import RLM_REPL_With_Timescale

# Initialize RLM with TimescaleDB tracking
rlm = RLM_REPL_With_Timescale(
    api_key=os.getenv("OPENAI_API_KEY"),
    model="gpt-5",
    enable_logging=True,
    enable_timescale=True,
    timescale_db_url="postgresql://user:password@localhost:5432/rlm_logs"
)

# Run with query_id from benchmark dataset
query_id = "benchmark-001"
context = ["Document content here..."]
query = "What is the main topic?"

result = rlm.completion(
    context=context,
    query=query,
    query_id=query_id  # From benchmark dataset
)

# Get latency metrics
summary = rlm.get_latency_summary()
metrics = rlm.get_latency_metrics()

print(f"Total duration: {summary['total_duration_ms']:.2f}ms")
print(f"LLM interactions: {summary['total_llm_interactions']}")
print(f"Code executions: {summary['total_code_executions']}")

rlm.close()
```

## Analytics Queries

### Get Query Run Summary

```python
summary = client.get_query_run_summary(query_id, run_id)
print(f"Total duration: {summary['total_duration_ms']:.2f}ms")
print(f"Avg LLM latency: {summary['avg_llm_latency_ms']:.2f}ms")
print(f"Avg code latency: {summary['avg_code_latency_ms']:.2f}ms")
```

### Get Latency Metrics

```python
metrics = client.get_latency_metrics(query_id, run_id)

for event_type, data in metrics.items():
    print(f"\n{event_type}:")
    print(f"  Count: {data['count']}")
    print(f"  Avg: {data['avg_duration_ms']:.2f}ms")
    print(f"  P50: {data['p50_duration_ms']:.2f}ms")
    print(f"  P90: {data['p90_duration_ms']:.2f}ms")
    print(f"  P99: {data['p99_duration_ms']:.2f}ms")
```

### Get Slowest Operations

```python
# Slowest LLM interactions
slow_llm = client.get_slowest_llm_interactions(query_id, run_id, n=10)

# Slowest code executions
slow_code = client.get_slowest_code_executions(query_id, run_id, n=10)
```

### Get All Events

```python
# All latency events
events = client.get_latency_events(query_id, run_id)

# Filter by type
llm_events = client.get_latency_events(query_id, run_id, event_type="llm_interaction")
code_events = client.get_latency_events(query_id, run_id, event_type="code_execution")

# LLM interactions
interactions = client.get_llm_interactions(query_id, run_id)

# Code executions
executions = client.get_code_executions(query_id, run_id)
```

## Environment Variables

```bash
# Database connection
TIMESCALE_DB_URL=postgresql://user:password@localhost:5432/rlm_logs

# LLM configuration
LLM_MODEL=gpt-5
LLM_BASE_URL=https://api.openai.com/v1
LLM_RECURSIVE_MODEL=gpt-5-mini
LLM_RECURSIVE_BASE_URL=https://api.openai.com/v1
```

## Schema Overview

### Main Tables

1. **latency_events**: All latency events (hypertable)
2. **llm_interactions**: Detailed LLM interaction data
3. **code_executions**: Detailed code execution data
4. **query_run_summaries**: Aggregated metrics per query run

### Indexes

- Time-based indexes for fast range queries
- Composite indexes for query/run patterns
- GIN indexes for JSONB metadata
- Full-text search indexes

### Continuous Aggregates

- **latency_metrics_minute**: Real-time latency metrics aggregated by minute

### Data Retention

- 90-day retention policy
- Automatic compression after 7 days
- Automatic partition dropping

## Performance Tips

1. **Connection Pooling**: Use pool_size=10-20 for production
2. **Batch Writes**: Use `_execute_many` for bulk inserts
3. **Context Management**: Use `client.connection()` for transactions
4. **Indexing**: Leverage existing indexes for queries
5. **Compression**: Old data is automatically compressed

## Example: Benchmark Script

```python
import time
from datetime import datetime, timezone
from rlm.logger.timescale_client import TimescaleDBClient

def run_benchmark():
    client = TimescaleDBClient("postgresql://...")
    
    # Run ID from script start time
    run_id = datetime.now(timezone.utc)
    
    # Process benchmark queries
    for query in benchmark_dataset:
        query_id = query["id"]
        client.set_context(query_id=query_id, run_id=run_id)
        client.initialize_query_run(query_id, run_id)
        
        # Execute query
        result = process_query(query["context"], query["question"])
        
        client.complete_query_run(query_id, run_id)
    
    # Generate report
    generate_report(run_id)
    client.close()
```

## API Reference

### TimescaleDBClient

#### Initialization

```python
client = TimescaleDBClient(db_url, pool_size=10, auto_commit=True)
```

#### Context Management

```python
client.set_context(query_id, run_id, iteration, depth)
```

#### Recording Methods

```python
client.record_latency(record)
client.record_llm_interaction(record)
client.record_code_execution(record)
```

#### Query Run Management

```python
client.initialize_query_run(query_id, run_id, metadata)
client.update_query_run_summary(query_id, run_id)
client.complete_query_run(query_id, run_id, status)
```

#### Analytics Methods

```python
client.get_query_run_summary(query_id, run_id)
client.get_latency_metrics(query_id, run_id)
client.get_latency_events(query_id, run_id, event_type)
client.get_llm_interactions(query_id, run_id)
client.get_code_executions(query_id, run_id)
client.get_slowest_llm_interactions(query_id, run_id, n)
client.get_slowest_code_executions(query_id, run_id, n)
```

#### Context Managers

```python
with client.track_latency(event_type, event_subtype, metadata):
    # Code to track
```

#### Decorators

```python
@client.track_latency_decorator(event_type, event_subtype, metadata)
def my_function():
    # Function implementation
```

## License

MIT

## Contributing

Contributions are welcome! Please submit a Pull Request.
