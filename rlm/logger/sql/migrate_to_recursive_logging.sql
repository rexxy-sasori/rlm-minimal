-- Migration Script: Add Recursive Logging Fields to Existing Database
-- This script adds the new recursive logging fields to existing tables
-- Run this if you already have TimescaleDB tables created

-- Migration for latency_events table
ALTER TABLE IF EXISTS latency_events 
ADD COLUMN IF NOT EXISTS recursion_id TEXT DEFAULT 'rec_0_default';

ALTER TABLE IF EXISTS latency_events 
ADD COLUMN IF NOT EXISTS parent_recursion_id TEXT;

ALTER TABLE IF EXISTS latency_events 
ADD COLUMN IF NOT EXISTS current_depth INTEGER;

ALTER TABLE IF EXISTS latency_events 
ADD COLUMN IF NOT EXISTS max_depth INTEGER;

ALTER TABLE IF EXISTS latency_events 
ADD COLUMN IF NOT EXISTS model TEXT;

ALTER TABLE IF EXISTS latency_events 
ADD COLUMN IF NOT EXISTS model_index INTEGER;

-- Migrate old 'depth' column to 'current_depth'
UPDATE latency_events 
SET current_depth = depth 
WHERE depth IS NOT NULL AND current_depth IS NULL;

-- Create indexes for latency_events
CREATE INDEX IF NOT EXISTS idx_latency_recursion 
ON latency_events (recursion_id, parent_recursion_id, time DESC);

CREATE INDEX IF NOT EXISTS idx_latency_parent_recursion 
ON latency_events (parent_recursion_id, time DESC);

CREATE INDEX IF NOT EXISTS idx_latency_depth 
ON latency_events (current_depth, max_depth, time DESC);

CREATE INDEX IF NOT EXISTS idx_latency_model_depth 
ON latency_events (model, current_depth, time DESC);

-- Migration for llm_interactions table
ALTER TABLE IF EXISTS llm_interactions 
ADD COLUMN IF NOT EXISTS recursion_id TEXT DEFAULT 'rec_0_default';

ALTER TABLE IF EXISTS llm_interactions 
ADD COLUMN IF NOT EXISTS parent_recursion_id TEXT;

ALTER TABLE IF EXISTS llm_interactions 
ADD COLUMN IF NOT EXISTS model_index INTEGER;

ALTER TABLE IF EXISTS llm_interactions 
ADD COLUMN IF NOT EXISTS current_depth INTEGER;

ALTER TABLE IF EXISTS llm_interactions 
ADD COLUMN IF NOT EXISTS max_depth INTEGER;

ALTER TABLE IF EXISTS llm_interactions 
ADD COLUMN IF NOT EXISTS iteration INTEGER;

-- Create indexes for llm_interactions
CREATE INDEX IF NOT EXISTS idx_llm_recursion 
ON llm_interactions (recursion_id, parent_recursion_id, time DESC);

CREATE INDEX IF NOT EXISTS idx_llm_parent_recursion 
ON llm_interactions (parent_recursion_id, time DESC);

CREATE INDEX IF NOT EXISTS idx_llm_depth 
ON llm_interactions (current_depth, max_depth, time DESC);

CREATE INDEX IF NOT EXISTS idx_llm_model_depth 
ON llm_interactions (model, current_depth, time DESC);

CREATE INDEX IF NOT EXISTS idx_llm_model_index 
ON llm_interactions (model_index, current_depth, time DESC);

-- Migration for code_executions table
ALTER TABLE IF EXISTS code_executions 
ADD COLUMN IF NOT EXISTS recursion_id TEXT DEFAULT 'rec_0_default';

ALTER TABLE IF EXISTS code_executions 
ADD COLUMN IF NOT EXISTS parent_recursion_id TEXT;

ALTER TABLE IF EXISTS code_executions 
ADD COLUMN IF NOT EXISTS current_depth INTEGER;

ALTER TABLE IF EXISTS code_executions 
ADD COLUMN IF NOT EXISTS max_depth INTEGER;

ALTER TABLE IF EXISTS code_executions 
ADD COLUMN IF NOT EXISTS model TEXT;

ALTER TABLE IF EXISTS code_executions 
ADD COLUMN IF NOT EXISTS iteration INTEGER;

-- Create indexes for code_executions
CREATE INDEX IF NOT EXISTS idx_code_recursion 
ON code_executions (recursion_id, parent_recursion_id, time DESC);

CREATE INDEX IF NOT EXISTS idx_code_parent_recursion 
ON code_executions (parent_recursion_id, time DESC);

CREATE INDEX IF NOT EXISTS idx_code_depth 
ON code_executions (current_depth, max_depth, time DESC);

CREATE INDEX IF NOT EXISTS idx_code_model_depth 
ON code_executions (model, current_depth, time DESC);

-- Update NOT NULL constraints (optional, run after backfilling data)
-- WARNING: This will fail if there are NULL values in the columns
-- Uncomment and run only after ensuring all existing data has values

-- ALTER TABLE latency_events 
-- ALTER COLUMN recursion_id SET NOT NULL;

-- ALTER TABLE llm_interactions 
-- ALTER COLUMN recursion_id SET NOT NULL;

-- ALTER TABLE code_executions 
-- ALTER COLUMN recursion_id SET NOT NULL;

-- Optional: Backfill recursion_id for existing data
-- This generates recursion IDs based on query_id and run_id
-- WARNING: This may take a long time on large datasets

-- UPDATE latency_events 
-- SET recursion_id = CONCAT('rec_', COALESCE(current_depth, 0), '_', 
--                         SUBSTRING(MD5(CONCAT(query_id, run_id, event_id::TEXT)), 1, 8))
-- WHERE recursion_id = 'rec_0_default';

-- UPDATE llm_interactions 
-- SET recursion_id = CONCAT('rec_', COALESCE(current_depth, 0), '_', 
--                         SUBSTRING(MD5(CONCAT(query_id, run_id, interaction_id::TEXT)), 1, 8))
-- WHERE recursion_id = 'rec_0_default';

-- UPDATE code_executions 
-- SET recursion_id = CONCAT('rec_', COALESCE(current_depth, 0), '_', 
--                         SUBSTRING(MD5(CONCAT(query_id, run_id, execution_id::TEXT)), 1, 8))
-- WHERE recursion_id = 'rec_0_default';

-- Verify migration
SELECT 'Migration verification:' AS message;

SELECT 
    'latency_events' AS table_name,
    COUNT(*) AS total_rows,
    COUNT(recursion_id) AS rows_with_recursion_id,
    COUNT(current_depth) AS rows_with_current_depth
FROM latency_events
UNION ALL
SELECT 
    'llm_interactions' AS table_name,
    COUNT(*) AS total_rows,
    COUNT(recursion_id) AS rows_with_recursion_id,
    COUNT(current_depth) AS rows_with_current_depth
FROM llm_interactions
UNION ALL
SELECT 
    'code_executions' AS table_name,
    COUNT(*) AS total_rows,
    COUNT(recursion_id) AS rows_with_recursion_id,
    COUNT(current_depth) AS rows_with_current_depth
FROM code_executions;

SELECT 'Migration completed successfully!' AS message;
