# Recursive RLM Logging with TimescaleDB

This document describes the enhanced log format for tracking recursive RLM calls with depth > 1 in TimescaleDB.

## Overview

When RLM_REPL makes recursive calls (depth > 1), we need to track:
- **Hierarchical relationships** between parent and child recursive calls
- **Depth awareness** (current_depth and max_depth)
- **Model specificity** (which model is used at each depth)
- **Causality chain** (traceability through the recursion tree)
- **Performance metrics** (latency at each level independently)

## Enhanced Log Format

### Key New Fields

| Field | Type | Description |
|-------|------|-------------|
| `recursion_id` | String | Unique ID for this recursive call (format: `rec_{depth}_{uuid}`) |
| `parent_recursion_id` | String (Optional) | Parent recursion ID for tree structure |
| `current_depth` | Integer | Current recursion depth (0 = root) |
| `max_depth` | Integer | Maximum allowed recursion depth |
| `model` | String | Model used at this depth |
| `model_index` | Integer (Optional) | Index in recursive_models list |

### Data Classes

#### LatencyRecord
```python
@dataclass
class LatencyRecord:
    query_id: str                    # Root query identifier
    run_id: datetime                 # Root run timestamp
    recursion_id: str                # Unique ID for this recursive call
    parent_recursion_id: Optional[str]  # Parent recursion ID
    event_type: str                  # 'llm_interaction', 'code_execution', etc.
    event_subtype: Optional[str]     # 'prompt', 'completion', 'python_exec', etc.
    duration_ms: Optional[float]
    start_time: Optional[datetime]
    end_time: Optional[datetime]
    iteration: Optional[int]         # Conversation iteration
    current_depth: Optional[int]     # Current recursion depth
    max_depth: Optional[int]         # Maximum allowed depth
    model: Optional[str]             # Model used at this depth
    model_index: Optional[int]       # Index in recursive_models list
    metadata: Optional[Dict[str, Any]]
    success: bool = True
    error_message: Optional[str]
    error_type: Optional[str]
    source_component: Optional[str]
    source_function: Optional[str]
```

#### LLMInteractionRecord
```python
@dataclass
class LLMInteractionRecord:
    query_id: str
    run_id: datetime
    recursion_id: str
    parent_recursion_id: Optional[str]
    model: str                       # Model used
    model_index: Optional[int]       # Index in recursive_models list
    model_type: Optional[str]        # 'root', 'recursive', 'sub_rlm'
    current_depth: Optional[int]
    max_depth: Optional[int]
    prompt_tokens: Optional[int]
    completion_tokens: Optional[int]
    total_tokens: Optional[int]
    cached_tokens: Optional[int] = 0
    uncached_prompt_tokens: Optional[int]
    prompt_token_price: Optional[float]
    completion_token_price: Optional[float]
    total_cost: Optional[float]
    duration_ms: Optional[float]
    start_time: Optional[datetime]
    end_time: Optional[datetime]
    context_messages: Optional[int]
    context_tokens: Optional[int]
    response_length: Optional[int]
    iteration: Optional[int]
    has_tool_calls: Optional[bool]
    tool_call_count: Optional[int]
    success: bool = True
    error_message: Optional[str]
    error_type: Optional[str]
    metadata: Optional[Dict[str, Any]]
```

#### CodeExecutionRecord
```python
@dataclass
class CodeExecutionRecord:
    query_id: str
    run_id: datetime
    recursion_id: str
    parent_recursion_id: Optional[str]
    execution_number: int
    code: str
    current_depth: Optional[int]
    max_depth: Optional[int]
    model: Optional[str]
    stdout: Optional[str]
    stderr: Optional[str]
    output_length: Optional[int]
    duration_ms: Optional[float]
    start_time: Optional[datetime]
    end_time: Optional[datetime]
    iteration: Optional[int]
    success: bool = True
    error_message: Optional[str]
    error_type: Optional[str]
    metadata: Optional[Dict[str, Any]]
```

## Usage Example

### Initialization

```python
from rlm.logger.timescale_client import TimescaleDBClient
from datetime import datetime, timezone

# Initialize client
client = TimescaleDBClient(
    db_url="postgresql://user:password@localhost:5432/rlm_logs",
    pool_size=10
)

# Set root context (depth 0)
query_id = "benchmark-001"
run_id = datetime.now(timezone.utc)

root_recursion_id = client.generate_recursion_id(current_depth=0)

client.set_context(
    query_id=query_id,
    run_id=run_id,
    current_depth=0,
    max_depth=3,
    recursion_id=root_recursion_id,
    parent_recursion_id=None,
    model="gpt-5",
    model_index=None
)

client.initialize_query_run(query_id, run_id)
```

### Tracking Root Level (Depth 0)

```python
# Track root LLM interaction
with client.track_latency(
    event_type="llm_interaction",
    event_subtype="root_prompt",
    source_component="RLM_REPL",
    source_function="_call_llm"
):
    response = llm.completion(messages)
```

### Entering Recursive Call (Depth 1)

```python
# Enter recursive call context
recursion_id_1 = client.enter_recursive_call(
    current_depth=1,
    max_depth=3,
    model="gpt-5-mini",
    model_index=0
)

# Track LLM interaction at depth 1
with client.track_latency(
    event_type="llm_interaction",
    event_subtype="recursive_prompt",
    source_component="RLM_REPL",
    source_function="_call_llm"
):
    response = llm.completion(messages)
```

### Entering Another Recursive Call (Depth 2)

```python
# Enter another recursive call context
recursion_id_2 = client.enter_recursive_call(
    current_depth=2,
    max_depth=3,
    model="gpt-4",
    model_index=1
)

# Track LLM interaction at depth 2
with client.track_latency(
    event_type="llm_interaction",
    event_subtype="recursive_prompt",
    source_component="RLM_REPL",
    source_function="_call_llm"
):
    response = llm.completion(messages)
```

### Base Case (Depth 3 - Sub_RLM)

```python
# Enter base case context (Sub_RLM)
recursion_id_3 = client.enter_recursive_call(
    current_depth=3,
    max_depth=3,
    model="gpt-3.5-turbo",
    model_index=2
)

# Track Sub_RLM LLM interaction
with client.track_latency(
    event_type="llm_interaction",
    event_subtype="sub_rlm_prompt",
    source_component="Sub_RLM",
    source_function="_call_llm"
):
    response = llm.completion(messages)

# Complete query run
client.complete_query_run(query_id, run_id)
client.close()
```

## Querying Recursive Data

### Get All Events for a Query Run

```sql
SELECT 
    time,
    recursion_id,
    parent_recursion_id,
    current_depth,
    max_depth,
    model,
    event_type,
    event_subtype,
    duration_ms,
    success
FROM latency_events
WHERE query_id = 'benchmark-001' 
  AND run_id = '2024-01-19 10:00:00'
ORDER BY current_depth, time;
```

### Get Recursion Tree for a Query Run

```sql
WITH RECURSIVE recursion_tree AS (
    SELECT 
        recursion_id,
        parent_recursion_id,
        current_depth,
        model,
        event_type,
        duration_ms,
        time,
        ARRAY[recursion_id] AS path
    FROM latency_events
    WHERE query_id = 'benchmark-001'
      AND run_id = '2024-01-19 10:00:00'
      AND parent_recursion_id IS NULL
      AND current_depth = 0
    
    UNION ALL
    
    SELECT 
        le.recursion_id,
        le.parent_recursion_id,
        le.current_depth,
        le.model,
        le.event_type,
        le.duration_ms,
        le.time,
        rt.path || le.recursion_id
    FROM latency_events le
    JOIN recursion_tree rt ON le.parent_recursion_id = rt.recursion_id
    WHERE le.query_id = 'benchmark-001'
      AND le.run_id = '2024-01-19 10:00:00'
)
SELECT * FROM recursion_tree ORDER BY current_depth, time;
```

### Get Latency by Depth and Model

```sql
SELECT 
    current_depth,
    model,
    COUNT(*) AS event_count,
    AVG(duration_ms) AS avg_latency_ms,
    PERCENTILE_CONT(0.5) WITHIN GROUP (ORDER BY duration_ms) AS p50_latency_ms,
    PERCENTILE_CONT(0.9) WITHIN GROUP (ORDER BY duration_ms) AS p90_latency_ms,
    PERCENTILE_CONT(0.99) WITHIN GROUP (ORDER BY duration_ms) AS p99_latency_ms
FROM latency_events
WHERE query_id = 'benchmark-001'
  AND run_id = '2024-01-19 10:00:00'
  AND event_type = 'llm_interaction'
GROUP BY current_depth, model
ORDER BY current_depth;
```

### Get Token Usage by Depth

```sql
SELECT 
    current_depth,
    model,
    COUNT(*) AS interaction_count,
    SUM(prompt_tokens) AS total_prompt_tokens,
    SUM(completion_tokens) AS total_completion_tokens,
    SUM(total_tokens) AS total_tokens,
    SUM(cached_tokens) AS total_cached_tokens,
    SUM(total_cost) AS total_cost
FROM llm_interactions
WHERE query_id = 'benchmark-001'
  AND run_id = '2024-01-19 10:00:00'
GROUP BY current_depth, model
ORDER BY current_depth;
```

## Visualization Example

### Recursion Tree Structure

For a query with `max_depth=3` and `recursive_models=['gpt-5-mini', 'gpt-4', 'gpt-3.5-turbo']`:

```
Query: "Analyze this data"
Run ID: 2024-01-19T10:00:00

Depth 0 (Root):
├─ recursion_id: rec_0_a1b2c3d4
├─ parent_recursion_id: None
├─ model: gpt-5
├─ current_depth: 0
├─ max_depth: 3
└─ Events:
    ├─ llm_interaction (1200ms)
    └─ code_execution (800ms)

Depth 1 (Recursive Call):
├─ recursion_id: rec_1_e5f6g7h8
├─ parent_recursion_id: rec_0_a1b2c3d4
├─ model: gpt-5-mini (model_index=0)
├─ current_depth: 1
├─ max_depth: 3
└─ Events:
    ├─ llm_interaction (900ms)
    └─ code_execution (600ms)

Depth 2 (Recursive Call):
├─ recursion_id: rec_2_i9j0k1l2
├─ parent_recursion_id: rec_1_e5f6g7h8
├─ model: gpt-4 (model_index=1)
├─ current_depth: 2
├─ max_depth: 3
└─ Events:
    ├─ llm_interaction (1500ms)
    └─ code_execution (1200ms)

Depth 3 (Base Case - Sub_RLM):
├─ recursion_id: rec_3_m3n4o5p6
├─ parent_recursion_id: rec_2_i9j0k1l2
├─ model: gpt-3.5-turbo (model_index=2)
├─ current_depth: 3
├─ max_depth: 3
└─ Events:
    └─ llm_interaction (600ms)
```

## API Reference

### TimescaleDBClient Methods

#### `generate_recursion_id(current_depth: int) -> str`

Generate a unique recursion ID for the given depth.

**Parameters:**
- `current_depth`: Current recursion depth

**Returns:**
- Unique recursion ID string (format: `rec_{depth}_{uuid}`)

**Example:**
```python
recursion_id = client.generate_recursion_id(current_depth=2)
# Returns: "rec_2_a1b2c3d4"
```

#### `enter_recursive_call(current_depth: int, max_depth: int, model: str, model_index: Optional[int] = None) -> str`

Enter a recursive call context. Saves current recursion ID as parent and generates new recursion ID.

**Parameters:**
- `current_depth`: Current recursion depth
- `max_depth`: Maximum allowed depth
- `model`: Model used at this depth
- `model_index`: Index in recursive_models list (optional)

**Returns:**
- New recursion ID

**Example:**
```python
recursion_id = client.enter_recursive_call(
    current_depth=1,
    max_depth=3,
    model="gpt-5-mini",
    model_index=0
)
```

#### `set_context(...)`

Set current logging context with recursion support.

**Parameters:**
- `query_id`: Query identifier from benchmark dataset
- `run_id`: Run identifier (timestamp from main script)
- `iteration`: Current conversation iteration
- `current_depth`: Current recursion depth (0 = root)
- `max_depth`: Maximum allowed recursion depth
- `recursion_id`: Unique ID for this recursive call
- `parent_recursion_id`: Parent recursion ID (for tree structure)
- `model`: Model used at this depth
- `model_index`: Index in recursive_models list

**Example:**
```python
client.set_context(
    query_id="benchmark-001",
    run_id=datetime.now(timezone.utc),
    current_depth=0,
    max_depth=3,
    recursion_id="rec_0_a1b2c3d4",
    parent_recursion_id=None,
    model="gpt-5",
    model_index=None
)
```

## Best Practices

1. **Always set context before tracking**: Ensure `set_context` or `enter_recursive_call` is called before using `track_latency`.

2. **Use `enter_recursive_call` for recursive calls**: This method automatically manages parent-child relationships.

3. **Include model and model_index**: These fields are crucial for analyzing performance by model at different depths.

4. **Complete query runs**: Always call `complete_query_run` to finalize metrics.

5. **Use descriptive event_subtype**: Helps in filtering and analyzing specific types of events.

6. **Track source_component and source_function**: Useful for debugging and identifying bottlenecks.

## Migration Guide

### From Non-Recursive to Recursive Logging

**Before (Non-Recursive):**
```python
client.set_context(
    query_id=query_id,
    run_id=run_id,
    iteration=0,
    depth=0
)
```

**After (Recursive):**
```python
recursion_id = client.generate_recursion_id(current_depth=0)

client.set_context(
    query_id=query_id,
    run_id=run_id,
    iteration=0,
    current_depth=0,
    max_depth=1,  # or your max_depth
    recursion_id=recursion_id,
    parent_recursion_id=None,
    model="gpt-5",
    model_index=None
)
```

### Database Schema Migration

Add the new columns to your TimescaleDB tables:

```sql
-- For latency_events table
ALTER TABLE latency_events ADD COLUMN IF NOT EXISTS recursion_id TEXT;
ALTER TABLE latency_events ADD COLUMN IF NOT EXISTS parent_recursion_id TEXT;
ALTER TABLE latency_events ADD COLUMN IF NOT EXISTS current_depth INTEGER;
ALTER TABLE latency_events ADD COLUMN IF NOT EXISTS max_depth INTEGER;
ALTER TABLE latency_events ADD COLUMN IF NOT EXISTS model TEXT;
ALTER TABLE latency_events ADD COLUMN IF NOT EXISTS model_index INTEGER;

-- For llm_interactions table
ALTER TABLE llm_interactions ADD COLUMN IF NOT EXISTS recursion_id TEXT;
ALTER TABLE llm_interactions ADD COLUMN IF NOT EXISTS parent_recursion_id TEXT;
ALTER TABLE llm_interactions ADD COLUMN IF NOT EXISTS current_depth INTEGER;
ALTER TABLE llm_interactions ADD COLUMN IF NOT EXISTS max_depth INTEGER;
ALTER TABLE llm_interactions ADD COLUMN IF NOT EXISTS model_index INTEGER;
ALTER TABLE llm_interactions ADD COLUMN IF NOT EXISTS iteration INTEGER;

-- For code_executions table
ALTER TABLE code_executions ADD COLUMN IF NOT EXISTS recursion_id TEXT;
ALTER TABLE code_executions ADD COLUMN IF NOT EXISTS parent_recursion_id TEXT;
ALTER TABLE code_executions ADD COLUMN IF NOT EXISTS current_depth INTEGER;
ALTER TABLE code_executions ADD COLUMN IF NOT EXISTS max_depth INTEGER;
ALTER TABLE code_executions ADD COLUMN IF NOT EXISTS model TEXT;
ALTER TABLE code_executions ADD COLUMN IF NOT EXISTS iteration INTEGER;

-- Create indexes for better query performance
CREATE INDEX IF NOT EXISTS idx_latency_recursion ON latency_events(recursion_id, parent_recursion_id);
CREATE INDEX IF NOT EXISTS idx_latency_depth ON latency_events(current_depth, max_depth);
CREATE INDEX IF NOT EXISTS idx_llm_recursion ON llm_interactions(recursion_id, parent_recursion_id);
CREATE INDEX IF NOT EXISTS idx_llm_depth ON llm_interactions(current_depth, max_depth);
CREATE INDEX IF NOT EXISTS idx_code_recursion ON code_executions(recursion_id, parent_recursion_id);
CREATE INDEX IF NOT EXISTS idx_code_depth ON code_executions(current_depth, max_depth);
```

## Troubleshooting

### Issue: Missing recursion_id in logs

**Solution:** Ensure `set_context` or `enter_recursive_call` is called before tracking events.

### Issue: Parent recursion ID not set correctly

**Solution:** Use `enter_recursive_call` method which automatically manages parent-child relationships.

### Issue: Cannot query by depth

**Solution:** Check that `current_depth` and `max_depth` columns exist in your database schema.

### Issue: Model index is None

**Solution:** This is expected for the root level (depth 0). Model index should be set for recursive calls (depth >= 1).

## Conclusion

The enhanced recursive logging format provides comprehensive tracking of RLM's recursive behavior, enabling:
- Detailed performance analysis at each recursion level
- Cost tracking by model and depth
- Debugging of recursive call chains
- Optimization of recursion strategies

By following this format and best practices, you can gain deep insights into your RLM system's behavior and performance.
