# Token Cache Tracking with TimescaleDB

## Overview

Comprehensive token cache tracking for LLM interactions where `cached_tokens` is available in `prompt_tokens_details` from the API response.

## Key Features

- **Track cached tokens**: Monitor how many tokens are reused from cache
- **Cost analysis**: Calculate savings from token cache usage
- **Cache effectiveness**: Measure cache hit rates per query/run
- **Evolution tracking**: See how cache usage changes across iterations
- **Per-model aggregation**: Analyze cache effectiveness by model

## Schema Additions

### llm_interactions Table

```sql
-- Token cache tracking (from prompt_tokens_details)
cached_tokens INTEGER DEFAULT 0,
uncached_prompt_tokens INTEGER,

-- Token pricing (for cost calculation)
prompt_token_price DOUBLE PRECISION, -- Price per 1k tokens
completion_token_price DOUBLE PRECISION, -- Price per 1k tokens
total_cost DOUBLE PRECISION, -- Calculated cost for this interaction
```

### token_cache_optimization Table

```sql
CREATE TABLE token_cache_optimization (
    time TIMESTAMPTZ NOT NULL,
    query_id TEXT NOT NULL,
    run_id TIMESTAMPTZ NOT NULL,
    
    -- Cache effectiveness
    total_prompt_tokens INTEGER,
    total_cached_tokens INTEGER,
    cache_savings_tokens INTEGER,
    cache_savings_percentage DOUBLE PRECISION,
    
    -- Cost savings
    original_cost DOUBLE PRECISION,
    cached_cost DOUBLE PRECISION,
    cost_savings DOUBLE PRECISION,
    cost_savings_percentage DOUBLE PRECISION,
    
    -- Interaction breakdown
    total_interactions INTEGER,
    interactions_with_cache INTEGER,
    interactions_without_cache INTEGER,
    
    -- Per-iteration cache analysis
    cache_evolution JSONB,
    
    PRIMARY KEY (query_id, run_id)
);
```

## Quick Start

### 1. Initialize Client

```python
from datetime import datetime, timezone
from rlm.logger import TimescaleDBClient, LLMInteractionRecord

client = TimescaleDBClient("postgresql://user:password@localhost:5432/rlm_logs")
```

### 2. Track LLM Response with Cache

```python
query_id = "benchmark-query-001"
run_id = datetime.now(timezone.utc)

client.set_context(query_id=query_id, run_id=run_id)
client.initialize_query_run(query_id, run_id)

# Your LLM API call
response = openai.ChatCompletion.create(
    model="gpt-5",
    messages=messages
)

# Extract cache info from response
usage = response["usage"]
cached_tokens = usage["prompt_tokens_details"]["cached_tokens"]

# Create record
record = LLMInteractionRecord(
    query_id=query_id,
    run_id=run_id,
    model="gpt-5",
    model_type="root",
    prompt_tokens=usage["prompt_tokens"],
    completion_tokens=usage["completion_tokens"],
    total_tokens=usage["total_tokens"],
    cached_tokens=cached_tokens,  # Track cached tokens
    uncached_prompt_tokens=usage["prompt_tokens"] - cached_tokens,
    prompt_token_price=0.0015,  # $0.0015 per 1k tokens
    completion_token_price=0.006,  # $0.006 per 1k tokens
    duration_ms=150.5,
    start_time=start_time,
    end_time=end_time,
    success=True
)

client.record_llm_interaction(record)
client.complete_query_run(query_id, run_id)
```

### 3. Get Cache Metrics

```python
# Get cache summary
cache_summary = client.get_token_cache_summary(query_id, run_id)
print(f"Cache hit rate: {cache_summary['cache_hit_rate']:.2%}")
print(f"Total cost: ${cache_summary['total_cost']:.4f}")
print(f"Cache savings: {cache_summary['cache_savings_tokens']} tokens")

# Calculate and store optimization
client.calculate_and_store_cache_optimization(query_id, run_id)

# Get detailed optimization report
optimization = client.get_token_cache_optimization(query_id, run_id)
print(f"Cost savings: ${optimization['cost_savings']:.4f} ({optimization['cost_savings_percentage']:.1%})")
print(f"Cache savings: {optimization['cache_savings_percentage']:.1%}")

# Show cache evolution per iteration
for entry in optimization['cache_evolution']:
    print(f"Iteration {entry['iteration']}: Cache hit {entry['cache_hit_rate']:.1%}")
```

## API Reference

### LLMInteractionRecord

```python
@dataclass
class LLMInteractionRecord:
    query_id: str
    run_id: datetime
    model: str
    model_type: Optional[str] = None
    prompt_tokens: Optional[int] = None
    completion_tokens: Optional[int] = None
    total_tokens: Optional[int] = None
    
    # Token cache tracking
    cached_tokens: Optional[int] = 0
    uncached_prompt_tokens: Optional[int] = None
    
    # Token pricing for cost calculation
    prompt_token_price: Optional[float] = None
    completion_token_price: Optional[float] = None
    total_cost: Optional[float] = None
    
    # ... other fields
```

### Token Cache Analytics Methods

#### get_token_cache_summary(query_id, run_id)

Get token cache summary for a query run.

**Returns**:
```python
{
    'total_prompt_tokens': 5000,
    'total_completion_tokens': 500,
    'total_tokens': 5500,
    'total_cached_tokens': 3000,
    'total_uncached_tokens': 2000,
    'cache_hit_rate': 0.6,  # 60%
    'total_cost': 0.0125,
    'avg_cost_per_interaction': 0.0025,
    'total_interactions': 5,
    'interactions_with_cache': 5,
    'interactions_without_cache': 0,
    'cache_savings_tokens': 3000,
    'cache_savings_percentage': 60.0
}
```

#### calculate_and_store_cache_optimization(query_id, run_id)

Calculate and store detailed token cache optimization metrics including:
- Token savings
- Cost savings
- Per-iteration cache evolution

#### get_token_cache_optimization(query_id, run_id)

Get detailed token cache optimization report.

**Returns**:
```python
{
    'total_prompt_tokens': 5000,
    'total_cached_tokens': 3000,
    'cache_savings_tokens': 3000,
    'cache_savings_percentage': 60.0,
    'original_cost': 0.0150,
    'cached_cost': 0.0125,
    'cost_savings': 0.0025,
    'cost_savings_percentage': 16.7,
    'total_interactions': 5,
    'interactions_with_cache': 5,
    'interactions_without_cache': 0,
    'cache_evolution': [
        {'iteration': 1, 'prompt_tokens': 1000, 'cached_tokens': 200, 'cache_hit_rate': 0.2},
        {'iteration': 2, 'prompt_tokens': 1200, 'cached_tokens': 500, 'cache_hit_rate': 0.42},
        # ...
    ]
}
```

#### get_top_cache_savings(limit=10)

Get queries with highest token cache savings.

#### get_cache_effectiveness_by_model()

Get token cache effectiveness aggregated by model.

**Returns**:
```python
[
    {
        'model': 'gpt-5',
        'total_interactions': 100,
        'total_prompt_tokens': 150000,
        'total_cached_tokens': 90000,
        'avg_cache_hit_rate': 0.6,
        'total_cost': 1.50
    },
    # ...
]
```

## Real-World Example

```python
import openai
from datetime import datetime, timezone
from rlm.logger import TimescaleDBClient

client = TimescaleDBClient(os.getenv("TIMESCALE_DB_URL"))

# Query from benchmark dataset
query_id = "benchmark-001"
run_id = datetime.now(timezone.utc)

client.set_context(query_id=query_id, run_id=run_id)
client.initialize_query_run(query_id, run_id)

# Process conversation
for iteration in range(5):
    client.set_context(iteration=iteration + 1)
    
    # LLM call
    start_time = datetime.now(timezone.utc)
    response = openai.ChatCompletion.create(
        model="gpt-5",
        messages=messages
    )
    end_time = datetime.now(timezone.utc)
    
    # Extract token usage
    usage = response["usage"]
    cached_tokens = usage["prompt_tokens_details"]["cached_tokens"]
    
    # Record with cache tracking
    record = LLMInteractionRecord(
        query_id=query_id,
        run_id=run_id,
        model="gpt-5",
        model_type="root",
        prompt_tokens=usage["prompt_tokens"],
        completion_tokens=usage["completion_tokens"],
        total_tokens=usage["total_tokens"],
        cached_tokens=cached_tokens,
        uncached_prompt_tokens=usage["prompt_tokens"] - cached_tokens,
        prompt_token_price=0.0015,
        completion_token_price=0.006,
        duration_ms=(end_time - start_time).total_seconds() * 1000,
        start_time=start_time,
        end_time=end_time,
        context_messages=len(messages),
        success=True
    )
    
    client.record_llm_interaction(record)

# Complete and analyze
client.complete_query_run(query_id, run_id)
client.calculate_and_store_cache_optimization(query_id, run_id)

# Get results
cache_summary = client.get_token_cache_summary(query_id, run_id)
optimization = client.get_token_cache_optimization(query_id, run_id)

print(f"Total cost: ${cache_summary['total_cost']:.4f}")
print(f"Cache hit rate: {cache_summary['cache_hit_rate']:.2%}")
print(f"Cost savings: ${optimization['cost_savings']:.4f} ({optimization['cost_savings_percentage']:.1%})")
```

## Migration

To add token cache tracking to existing schema:

```sql
-- Add columns to llm_interactions
ALTER TABLE llm_interactions ADD COLUMN cached_tokens INTEGER DEFAULT 0;
ALTER TABLE llm_interactions ADD COLUMN uncached_prompt_tokens INTEGER;
ALTER TABLE llm_interactions ADD COLUMN prompt_token_price DOUBLE PRECISION;
ALTER TABLE llm_interactions ADD COLUMN completion_token_price DOUBLE PRECISION;
ALTER TABLE llm_interactions ADD COLUMN total_cost DOUBLE PRECISION;

-- Create token_cache_optimization table
CREATE TABLE token_cache_optimization (
    time TIMESTAMPTZ NOT NULL,
    query_id TEXT NOT NULL,
    run_id TIMESTAMPTZ NOT NULL,
    total_prompt_tokens INTEGER,
    total_cached_tokens INTEGER,
    cache_savings_tokens INTEGER,
    cache_savings_percentage DOUBLE PRECISION,
    original_cost DOUBLE PRECISION,
    cached_cost DOUBLE PRECISION,
    cost_savings DOUBLE PRECISION,
    cost_savings_percentage DOUBLE PRECISION,
    total_interactions INTEGER,
    interactions_with_cache INTEGER,
    interactions_without_cache INTEGER,
    cache_evolution JSONB,
    PRIMARY KEY (query_id, run_id)
);

SELECT create_hypertable('token_cache_optimization', 'time',
    chunk_time_interval => INTERVAL '1 day',
    if_not_exists => TRUE);

-- Add indexes
CREATE INDEX idx_llm_cached_tokens ON llm_interactions (cached_tokens DESC, time DESC);
CREATE INDEX idx_llm_total_cost ON llm_interactions (total_cost DESC, time DESC);
CREATE INDEX idx_cache_opt_query_id ON token_cache_optimization (query_id, time DESC);
CREATE INDEX idx_cache_opt_savings ON token_cache_optimization (cost_savings DESC, time DESC);
```

## Examples

See [token_cache_example.py](rlm/logger/token_cache_example.py) for complete examples:

1. **Basic Cache Tracking**: Simple example of tracking cached tokens
2. **Cache Evolution**: Track how cache usage changes across iterations
3. **Cost Analysis**: Compare costs with and without cache
4. **Real-World Integration**: Production-ready integration pattern

## Benefits

1. **Cost Optimization**: Understand how much you're saving with token cache
2. **Performance Insights**: See how cache effectiveness changes over time
3. **Model Comparison**: Compare cache effectiveness across different models
4. **Query Analysis**: Identify queries that benefit most from caching
5. **Budget Planning**: Predict costs based on cache usage patterns

## Support

For issues or questions:
- Check the [README](rlm/logger/README.md)
- Review the [examples](rlm/logger/token_cache_example.py)
- Check TimescaleDB documentation
