-- TimescaleDB Schema for RLM Latency Tracking
-- Focus: Code execution latency and LLM interaction latency

CREATE EXTENSION IF NOT EXISTS timescaledb;
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- Main latency events table
CREATE TABLE latency_events (
    time TIMESTAMPTZ NOT NULL,
    event_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    
    -- Query and run identification
    query_id TEXT NOT NULL,
    run_id TIMESTAMPTZ NOT NULL,
    
    -- Event classification
    event_type TEXT NOT NULL, -- 'llm_interaction', 'code_execution', 'tool_call', 'processing'
    event_subtype TEXT, -- More specific type: 'root_llm', 'recursive_llm', 'python_execution', etc.
    
    -- Timing data
    duration_ms DOUBLE PRECISION NOT NULL,
    start_time TIMESTAMPTZ NOT NULL,
    end_time TIMESTAMPTZ NOT NULL,
    
    -- Context
    iteration INTEGER, -- Conversation step/iteration
    depth INTEGER, -- Recursion depth
    
    -- Event-specific metadata
    metadata JSONB,
    
    -- Status
    success BOOLEAN NOT NULL,
    error_message TEXT,
    error_type TEXT,
    
    -- Source information
    source_component TEXT,
    source_function TEXT
);

-- Create hypertable for time-series optimization
SELECT create_hypertable('latency_events', 'time',
    chunk_time_interval => INTERVAL '1 hour',
    if_not_exists => TRUE);

-- Indexes for fast queries
CREATE INDEX idx_latency_query_id ON latency_events (query_id, time DESC);
CREATE INDEX idx_latency_run_id ON latency_events (run_id, time DESC);
CREATE INDEX idx_latency_event_type ON latency_events (event_type, time DESC);
CREATE INDEX idx_latency_event_subtype ON latency_events (event_subtype, time DESC);
CREATE INDEX idx_latency_success ON latency_events (success, time DESC);
CREATE INDEX idx_latency_metadata_gin ON latency_events USING GIN (metadata);
CREATE INDEX idx_latency_duration ON latency_events (duration_ms DESC, time DESC);

-- Composite indexes for common query patterns
CREATE INDEX idx_latency_query_run ON latency_events (query_id, run_id, time DESC);
CREATE INDEX idx_latency_query_event ON latency_events (query_id, event_type, time DESC);
CREATE INDEX idx_latency_run_event ON latency_events (run_id, event_type, time DESC);

-- LLM interactions table (detailed)
CREATE TABLE llm_interactions (
    time TIMESTAMPTZ NOT NULL,
    interaction_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    
    query_id TEXT NOT NULL,
    run_id TIMESTAMPTZ NOT NULL,
    
    -- LLM details
    model TEXT NOT NULL,
    model_type TEXT, -- 'root', 'recursive'
    
    -- Token counts
    prompt_tokens INTEGER,
    completion_tokens INTEGER,
    total_tokens INTEGER,
    
    -- Timing
    duration_ms DOUBLE PRECISION NOT NULL,
    start_time TIMESTAMPTZ NOT NULL,
    end_time TIMESTAMPTZ NOT NULL,
    
    -- Context size
    context_messages INTEGER,
    context_tokens INTEGER,
    
    -- Response details
    response_length INTEGER,
    has_tool_calls BOOLEAN,
    tool_call_count INTEGER,
    
    -- Status
    success BOOLEAN NOT NULL,
    error_message TEXT,
    error_type TEXT,
    
    -- Metadata
    metadata JSONB
);

SELECT create_hypertable('llm_interactions', 'time',
    chunk_time_interval => INTERVAL '1 hour',
    if_not_exists => TRUE);

CREATE INDEX idx_llm_query_id ON llm_interactions (query_id, time DESC);
CREATE INDEX idx_llm_run_id ON llm_interactions (run_id, time DESC);
CREATE INDEX idx_llm_model ON llm_interactions (model, time DESC);
CREATE INDEX idx_llm_model_type ON llm_interactions (model_type, time DESC);
CREATE INDEX idx_llm_duration ON llm_interactions (duration_ms DESC, time DESC);
CREATE INDEX idx_llm_metadata_gin ON llm_interactions USING GIN (metadata);

-- Code executions table (detailed)
CREATE TABLE code_executions (
    time TIMESTAMPTZ NOT NULL,
    execution_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    
    query_id TEXT NOT NULL,
    run_id TIMESTAMPTZ NOT NULL,
    
    -- Execution details
    execution_number INTEGER NOT NULL,
    code TEXT NOT NULL,
    code_hash TEXT, -- For deduplication
    
    -- Output
    stdout TEXT,
    stderr TEXT,
    output_length INTEGER,
    
    -- Timing
    duration_ms DOUBLE PRECISION NOT NULL,
    start_time TIMESTAMPTZ NOT NULL,
    end_time TIMESTAMPTZ NOT NULL,
    
    -- Status
    success BOOLEAN NOT NULL,
    error_message TEXT,
    error_type TEXT,
    
    -- Metadata
    metadata JSONB
);

SELECT create_hypertable('code_executions', 'time',
    chunk_time_interval => INTERVAL '1 hour',
    if_not_exists => TRUE);

CREATE INDEX idx_code_query_id ON code_executions (query_id, time DESC);
CREATE INDEX idx_code_run_id ON code_executions (run_id, time DESC);
CREATE INDEX idx_code_execution_number ON code_executions (execution_number, time DESC);
CREATE INDEX idx_code_duration ON code_executions (duration_ms DESC, time DESC);
CREATE INDEX idx_code_success ON code_executions (success, time DESC);
CREATE INDEX idx_code_code_hash ON code_executions (code_hash);

-- Query run summary table (for aggregation)
CREATE TABLE query_run_summaries (
    query_id TEXT NOT NULL,
    run_id TIMESTAMPTZ NOT NULL,
    
    -- Timing summary
    start_time TIMESTAMPTZ NOT NULL,
    end_time TIMESTAMPTZ,
    total_duration_ms DOUBLE PRECISION,
    
    -- Event counts
    total_llm_interactions INTEGER DEFAULT 0,
    total_code_executions INTEGER DEFAULT 0,
    total_tool_calls INTEGER DEFAULT 0,
    
    -- LLM metrics
    avg_llm_latency_ms DOUBLE PRECISION,
    p50_llm_latency_ms DOUBLE PRECISION,
    p90_llm_latency_ms DOUBLE PRECISION,
    p99_llm_latency_ms DOUBLE PRECISION,
    total_llm_tokens INTEGER,
    
    -- Code execution metrics
    avg_code_latency_ms DOUBLE PRECISION,
    p50_code_latency_ms DOUBLE PRECISION,
    p90_code_latency_ms DOUBLE PRECISION,
    p99_code_latency_ms DOUBLE PRECISION,
    
    -- Errors
    error_count INTEGER DEFAULT 0,
    error_rate DOUBLE PRECISION,
    
    -- Status
    status TEXT DEFAULT 'running', -- 'running', 'completed', 'error'
    
    -- Metadata
    metadata JSONB,
    
    PRIMARY KEY (query_id, run_id)
);

CREATE INDEX idx_summary_query_id ON query_run_summaries (query_id);
CREATE INDEX idx_summary_run_id ON query_run_summaries (run_id);
CREATE INDEX idx_summary_status ON query_run_summaries (status);

-- Continuous aggregate for real-time latency monitoring
CREATE MATERIALIZED VIEW latency_metrics_minute
WITH (timescaledb.continuous) AS
SELECT
    time_bucket('1 minute', time) AS bucket,
    query_id,
    run_id,
    event_type,
    
    COUNT(*) AS event_count,
    AVG(duration_ms) AS avg_duration_ms,
    PERCENTILE_CONT(0.5) WITHIN GROUP (ORDER BY duration_ms) AS p50_duration_ms,
    PERCENTILE_CONT(0.9) WITHIN GROUP (ORDER BY duration_ms) AS p90_duration_ms,
    PERCENTILE_CONT(0.99) WITHIN GROUP (ORDER BY duration_ms) AS p99_duration_ms,
    MIN(duration_ms) AS min_duration_ms,
    MAX(duration_ms) AS max_duration_ms,
    
    COUNT(*) FILTER (WHERE success = FALSE) AS error_count,
    COUNT(*) FILTER (WHERE success = FALSE) / COUNT(*)::FLOAT AS error_rate
FROM latency_events
GROUP BY bucket, query_id, run_id, event_type
WITH DATA;

SELECT add_continuous_aggregate_policy('latency_metrics_minute',
    start_offset => INTERVAL '1 hour',
    end_offset => INTERVAL '1 minute',
    schedule_interval => INTERVAL '1 minute');

-- Data retention policies (90 days)
SELECT add_retention_policy('latency_events',
    drop_after => INTERVAL '90 days',
    if_not_exists => TRUE);

SELECT add_retention_policy('llm_interactions',
    drop_after => INTERVAL '90 days',
    if_not_exists => TRUE);

SELECT add_retention_policy('code_executions',
    drop_after => INTERVAL '90 days',
    if_not_exists => TRUE);

-- Compression policies for old data
ALTER TABLE latency_events SET (
    timescaledb.compress = true,
    timescaledb.compress_orderby = 'time DESC'
);

SELECT add_compression_policy('latency_events',
    compress_after => INTERVAL '7 days',
    if_not_exists => TRUE);

ALTER TABLE llm_interactions SET (
    timescaledb.compress = true,
    timescaledb.compress_orderby = 'time DESC'
);

SELECT add_compression_policy('llm_interactions',
    compress_after => INTERVAL '7 days',
    if_not_exists => TRUE);

ALTER TABLE code_executions SET (
    timescaledb.compress = true,
    timescaledb.compress_orderby = 'time DESC'
);

SELECT add_compression_policy('code_executions',
    compress_after => INTERVAL '7 days',
    if_not_exists => TRUE);
