# TimescaleDB Latency Tracking - Quick Start Guide

## Overview

This guide helps you quickly set up TimescaleDB for tracking:
- **Code execution latency**
- **LLM interaction latency**
- Using `query_id` (from benchmark dataset) and `run_id` (from main script timestamp)

## Installation & Setup

### 1. Start TimescaleDB (Docker)

```bash
docker run -d --name timescaledb -p 5432:5432 \
  -e POSTGRES_PASSWORD=password \
  timescale/timescaledb:latest-pg16
```

### 2. Create Database and Schema

```bash
# Connect to database
psql -h localhost -U postgres -W

# In psql shell:
CREATE DATABASE rlm_logs;
\c rlm_logs
\i rlm/logger/timescale_schema.sql
\q
```

### 3. Install Python Dependencies

```bash
pip install -r rlm/logger/requirements.txt
```

## Minimal Example

```python
from datetime import datetime, timezone
from rlm.logger import TimescaleDBClient

# Initialize client
client = TimescaleDBClient(
    "postgresql://postgres:password@localhost:5432/rlm_logs"
)

# Query ID from your benchmark dataset
query_id = "benchmark-001"

# Run ID from main script timestamp
run_id = datetime.now(timezone.utc)

# Set context
client.set_context(query_id=query_id, run_id=run_id)
client.initialize_query_run(query_id, run_id)

# Track LLM interaction
with client.track_latency(
    event_type="llm_interaction",
    event_subtype="root_llm"
):
    # Your LLM call here
    response = llm.completion(messages)

# Track code execution
with client.track_latency(
    event_type="code_execution",
    event_subtype="python_execution"
):
    # Your code execution here
    result = exec(code)

# Complete and get metrics
client.complete_query_run(query_id, run_id)
metrics = client.get_latency_metrics(query_id, run_id)

print(f"LLM avg latency: {metrics['llm_interaction']['avg_duration_ms']:.2f}ms")
print(f"Code avg latency: {metrics['code_execution']['avg_duration_ms']:.2f}ms")

client.close()
```

## RLM Integration Example

```python
import os
from rlm.logger.rlm_integration import RLM_REPL_With_Timescale

# Initialize RLM with TimescaleDB
rlm = RLM_REPL_With_Timescale(
    api_key=os.getenv("OPENAI_API_KEY"),
    enable_logging=True,
    enable_timescale=True,
    timescale_db_url="postgresql://postgres:password@localhost:5432/rlm_logs"
)

# Run with benchmark query
query_id = "benchmark-001"  # From your dataset
context = ["Your document context..."]
query = "Your question..."

result = rlm.completion(
    context=context,
    query=query,
    query_id=query_id  # Track with query ID
)

# Get latency summary
summary = rlm.get_latency_summary()
print(f"Total time: {summary['total_duration_ms']:.2f}ms")
print(f"LLM calls: {summary['total_llm_interactions']}")
print(f"Code execs: {summary['total_code_executions']}")

rlm.close()
```

## Key Concepts

### query_id
- **Source**: Your benchmark dataset
- **Purpose**: Identify which query is being executed
- **Example**: `"benchmark-001"`, `"dataset-query-123"`

### run_id
- **Source**: Main script timestamp
- **Purpose**: Identify when the query was run
- **Example**: `datetime.now(timezone.utc)`

### Event Types
- `"llm_interaction"`: LLM API calls
- `"code_execution"`: Python code execution
- `"tool_call"`: Other tool invocations

### Event Subtypes
- `"root_llm"`: Main LLM calls
- `"recursive_llm"`: Recursive/child LLM calls
- `"python_execution"`: Python code execution

## Environment Variables

Create a `.env` file:

```env
# Database
TIMESCALE_DB_URL=postgresql://postgres:password@localhost:5432/rlm_logs

# LLM
OPENAI_API_KEY=your-key-here
LLM_MODEL=gpt-5
LLM_BASE_URL=https://api.openai.com/v1
```

Load it:

```python
from dotenv import load_dotenv
load_dotenv()
```

## Viewing Data

### Using psql

```sql
-- Query run summary
SELECT * FROM query_run_summaries 
WHERE query_id = 'benchmark-001' 
ORDER BY run_id DESC;

-- LLM interactions
SELECT * FROM llm_interactions 
WHERE query_id = 'benchmark-001' 
ORDER BY time DESC;

-- Code executions
SELECT * FROM code_executions 
WHERE query_id = 'benchmark-001' 
ORDER BY execution_number;

-- Latency metrics
SELECT 
    event_type,
    COUNT(*) as count,
    AVG(duration_ms) as avg_ms,
    PERCENTILE_CONT(0.9) WITHIN GROUP (ORDER BY duration_ms) as p90_ms
FROM latency_events 
WHERE query_id = 'benchmark-001'
GROUP BY event_type;
```

### Using Python Client

```python
# Get summary
summary = client.get_query_run_summary(query_id, run_id)

# Get detailed metrics
metrics = client.get_latency_metrics(query_id, run_id)

# Get slowest operations
slow_llm = client.get_slowest_llm_interactions(query_id, run_id, n=10)
slow_code = client.get_slowest_code_executions(query_id, run_id, n=10)
```

## Common Patterns

### Pattern 1: Benchmark Script

```python
from datetime import datetime, timezone
from rlm.logger import TimescaleDBClient

client = TimescaleDBClient(os.getenv("TIMESCALE_DB_URL"))
run_id = datetime.now(timezone.utc)

for query in benchmark_dataset:
    query_id = query["id"]
    client.set_context(query_id=query_id, run_id=run_id)
    client.initialize_query_run(query_id, run_id)
    
    # Execute query
    result = process_query(query)
    
    client.complete_query_run(query_id, run_id)

client.close()
```

### Pattern 2: Decorators

```python
@client.track_latency_decorator(
    event_type="llm_interaction",
    event_subtype="root_llm"
)
def call_llm(messages):
    return llm.completion(messages)

@client.track_latency_decorator(
    event_type="code_execution",
    event_subtype="python_execution"
)
def execute_code(code):
    return exec(code)
```

### Pattern 3: Detailed Records

```python
from rlm.logger import LLMInteractionRecord, CodeExecutionRecord

# LLM Record
llm_record = LLMInteractionRecord(
    query_id=query_id,
    run_id=run_id,
    model="gpt-5",
    prompt_tokens=1500,
    completion_tokens=200,
    duration_ms=500.5,
    success=True
)
client.record_llm_interaction(llm_record)

# Code Record
code_record = CodeExecutionRecord(
    query_id=query_id,
    run_id=run_id,
    execution_number=1,
    code="print('hello')",
    stdout="hello",
    duration_ms=12.3,
    success=True
)
client.record_code_execution(code_record)
```

## Troubleshooting

### Connection Issues

```python
# Test connection
try:
    client = TimescaleDBClient(DB_URL)
    print("Connection successful!")
except Exception as e:
    print(f"Connection failed: {e}")
```

### Schema Issues

```sql
-- Verify tables exist
\dt

-- Verify hypertables
SELECT * FROM timescaledb_information.hypertables;
```

### Performance Issues

- Increase `pool_size` (default: 10)
- Use `auto_commit=True` for better performance
- Batch inserts with `_execute_many()`

## Next Steps

1. Read the full [README](rlm/logger/README.md)
2. Check out [examples](rlm/logger/timescale_examples.py)
3. Explore [RLM integration](rlm/logger/rlm_integration.py)

## Support

For issues or questions:
- Check the README.md
- Review the example code
- Check TimescaleDB documentation
