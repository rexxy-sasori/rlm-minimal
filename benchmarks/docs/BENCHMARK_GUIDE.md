# RLM Benchmark Runner with Sidecar WASM Pattern

This guide explains how to use the `run_benchmarks.py` script to evaluate RLM (Recursive Language Models) performance on long-context benchmarks using the sidecar WASM pattern.

## Overview

The benchmark runner uses:
- **RLM_REPL**: Recursive Language Model with REPL environment
- **Sidecar WASM Pattern**: Secure, isolated code execution in a separate container
- **Three Benchmarks**: OOLONG, Deep Research (BrowseComp-Plus), and RULER

## Architecture

### Async Mode Architecture (Recommended)

```
┌─────────────────────────────────────────────────────────────┐
│  run_benchmarks.py (Async Mode)                             │
│                                                             │
│  ┌─────────────────────────────────────────────────────┐   │
│  │  Async Task Coordinator                             │   │
│  │  - Manages concurrency (semaphore)                  │   │
│  │  - Distributes tasks to RLM pool                    │   │
│  └─────────────────────────────────────────────────────┘   │
│                          │                                  │
│          ┌───────────────┼───────────────┐                 │
│          ▼               ▼               ▼                 │
│  ┌─────────────┐ ┌─────────────┐ ┌─────────────┐           │
│  │  RLM_REPL   │ │  RLM_REPL   │ │  RLM_REPL   │           │
│  │  (Pool 1)   │ │  (Pool 2)   │ │  (Pool 3)   │           │
│  └─────────────┘ └─────────────┘ └─────────────┘           │
│          │               │               │                 │
│          └───────────────┼───────────────┘                 │
│                          ▼                                  │
│  ┌─────────────────────────────────────────────────────┐   │
│  │  WASM Manager (Sidecar Process)                     │   │
│  │  - localhost:8080                                   │   │
│  │  - Session management                               │   │
│  │  - Parallel code execution                          │   │
│  └─────────────────────────────────────────────────────┘   │
│                                                             │
│  Features:                                                 │
│  - Processes long context (1M+ tokens) in parallel        │
│  - Configurable concurrency (--concurrency)               │
│  - RLM pool for task distribution (--pool-size)           │
│  - Tracks job completion time per task                    │
│  - Uses asyncio for efficient I/O                        │
└─────────────────────────────────────────────────────────────┘
```

### Sync Mode Architecture (Legacy)

```
┌─────────────────────────────────────────────────────────────┐
│  run_benchmarks.py (Sync Mode)                              │
│                                                             │
│  ┌─────────────────┐    ┌─────────────────────┐           │
│  │  RLM_REPL       │    │  WASM Manager       │           │
│  │  (Main Process) │◄──►│  (Sidecar Process)  │           │
│  │                 │    │  localhost:8080     │           │
│  └─────────────────┘    └─────────────────────┘           │
│                                                             │
│  - Processes tasks sequentially                            │
│  - Single RLM instance                                     │
│  - No parallel execution                                   │
└─────────────────────────────────────────────────────────────┘
```

## Prerequisites

1. **Python 3.10+** installed
2. **LLM API Key** (OpenAI or compatible)
3. **WASM Manager Service** running (see below)
4. **Dependencies installed**:

```bash
pip install -r requirements.txt
```

## Starting the WASM Manager Service

Before running benchmarks, start the WASM manager service:

### Option 1: Local Development

```bash
# Start WASM manager on localhost:8080
python -m rlm.wasm.wasm_manager
```

### Option 2: Docker

```bash
docker run -d -p 8080:8080 --name wasm-manager rlm-minimal-wasm:latest
```

### Option 3: Kubernetes (Sidecar Pattern)

Deploy using the sidecar deployment manifest:

```bash
kubectl apply -f deploy/k8s/rlm-sidecar-deployment.yaml
```

## Quick Start

### Run All Benchmarks (Async Mode - Recommended)

```bash
python run_benchmarks.py \
  --api-key YOUR_LLM_KEY \
  --model gpt-4o \
  --async \
  --concurrency 5 \
  --pool-size 3 \
  --max-tasks 10 \
  --output-dir results/run1
```

### Run Specific Benchmark (Async Mode)

```bash
# OOLONG benchmark with async
python run_benchmarks.py \
  --api-key YOUR_LLM_KEY \
  --benchmark oolong \
  --async \
  --concurrency 5 \
  --max-tasks 20

# Deep Research benchmark with async
python run_benchmarks.py \
  --api-key YOUR_LLM_KEY \
  --benchmark deep_research \
  --async \
  --concurrency 3 \
  --max-tasks 5

# RULER benchmark with async
python run_benchmarks.py \
  --api-key YOUR_LLM_KEY \
  --benchmark ruler \
  --async \
  --concurrency 10 \
  --max-tasks 30
```

### Run Synchronously (Legacy Mode)

```bash
# Run all benchmarks synchronously
python run_benchmarks.py \
  --api-key YOUR_LLM_KEY \
  --model gpt-4o \
  --max-tasks 10
```

## Command-Line Options

### Required Parameters

- `--api-key`: LLM API key (or set `LLM_API_KEY` environment variable)

### Optional Parameters

- `--model`: LLM model name (default: `gpt-5`)
- `--base-url`: LLM API base URL (default: from `LLM_BASE_URL` env var)
- `--max-depth`: Maximum recursion depth (default: `3`)
- `--benchmark`: Benchmark to run (`oolong`, `deep_research`, `ruler`, `all`) (default: `all`)
- `--max-tasks`: Maximum number of tasks per benchmark (default: `10`)
- `--wasm-url`: Sidecar WASM manager URL (default: `http://localhost:8080`)
- `--wasm-timeout`: WASM execution timeout in seconds (default: `30`)
- `--output-dir`: Output directory for results (default: `results`)
- `--enable-logging`: Enable detailed logging
- `--no-save`: Don't save results to files

### Async Mode Parameters (Recommended)

- `--async`: Enable asyncio for parallel task processing (recommended for better performance)
- `--concurrency`: Maximum number of concurrent tasks (default: `5`)
- `--pool-size`: Number of RLM instances in pool (default: `3`)

## Environment Variables

You can configure the benchmark runner using environment variables:

```bash
export LLM_API_KEY="your-key-here"
export LLM_MODEL="gpt-4o"
export LLM_BASE_URL="https://api.openai.com/v1"
export WASM_MANAGER_SERVICE_URL="http://localhost:8080"
```

## Examples

### Example 1: Full Benchmark Suite (Async Mode - Recommended)

```bash
python run_benchmarks.py \
  --api-key sk-xxx \
  --model gpt-4o \
  --async \
  --concurrency 5 \
  --pool-size 3 \
  --max-depth 3 \
  --max-tasks 10 \
  --output-dir results/full-suite \
  --enable-logging
```

### Example 2: Long Context Evaluation with Async

```bash
python run_benchmarks.py \
  --api-key sk-xxx \
  --model gpt-5 \
  --benchmark ruler \
  --async \
  --concurrency 10 \
  --pool-size 5 \
  --max-tasks 50 \
  --wasm-timeout 60
```

### Example 3: Custom WASM Service with Async

```bash
python run_benchmarks.py \
  --api-key sk-xxx \
  --wasm-url http://wasm-service:8080 \
  --async \
  --concurrency 5 \
  --max-tasks 20
```

### Example 4: High Concurrency for Large Datasets

```bash
python run_benchmarks.py \
  --api-key sk-xxx \
  --model gpt-4o \
  --async \
  --concurrency 10 \
  --pool-size 5 \
  --max-tasks 100 \
  --wasm-timeout 120 \
  --output-dir results/high-concurrency
```

### Example 5: Low Concurrency for Resource-Constrained Environments

```bash
python run_benchmarks.py \
  --api-key sk-xxx \
  --model gpt-4o \
  --async \
  --concurrency 2 \
  --pool-size 1 \
  --max-tasks 10 \
  --output-dir results/low-resource
```

## Benchmark Details

### 1. OOLONG Benchmark

**Purpose**: Difficult long-context reasoning tasks

**Task Types**:
- Fact retrieval
- Multi-hop reasoning
- Comparative analysis
- Summarization
- Inference

**Context Length**: 1M - 10M+ tokens

**Command**:
```bash
python run_benchmarks.py --benchmark oolong --max-tasks 10
```

### 2. Deep Research (BrowseComp-Plus)

**Purpose**: Complex research tasks requiring deep analysis

**Task Types**:
- Literature review
- Competitive analysis
- Technical evaluation
- Market research
- Scientific synthesis

**Context Length**: 1M - 10M+ tokens

**Command**:
```bash
python run_benchmarks.py --benchmark deep_research --max-tasks 5
```

### 3. RULER Benchmark

**Purpose**: Needle-in-haystack retrieval evaluation

**Dimensions**:
- Different context lengths (1K to 10M+ tokens)
- Different needle positions (beginning, middle, end, distributed)
- Different needle types (factual, numerical, entities, dates, quotes)

**Command**:
```bash
python run_benchmarks.py --benchmark ruler --max-tasks 20
```

## Output

### Results Directory Structure

```
results/
├── summary.json              # Overall summary
├── oolong_results.json       # OOLONG benchmark results
├── deep_research_results.json # Deep Research results
└── ruler_results.json        # RULER results
```

### Summary JSON Format

```json
{
  "configuration": {
    "max_tasks": 10
  },
  "model": "gpt-4o",
  "max_depth": 3,
  "total_time": 1234.56,
  "benchmarks": {
    "oolong": {
      "name": "OOLONG",
      "metrics": {
        "overall_accuracy": "0.85",
        "total_tasks": 10,
        "correct_tasks": 8
      },
      "total_time": 456.78,
      "avg_time_per_task": 45.68
    },
    ...
  }
}
}
```

### Console Output Example

```
################################################################################
RLM BENCHMARK SUITE - SIDECAR WASM PATTERN
################################################################################
Running comprehensive benchmark suite with sidecar WASM execution

Configuration:
  Model: gpt-4o
  Max Depth: 3
  Max Tasks: 10
  Output Directory: results

================================================================================
OOLONG BENCHMARK
================================================================================

Running OOLONG benchmark with 10 examples...
This benchmark tests difficult long-context tasks including:
  - Fact retrieval
  - Multi-hop reasoning
  - Comparative analysis
  - Summarization
  - Inference

OOLONG Results:
  Accuracy: 0.85
  Correct: 8/10
  Total Time: 456.78s
  Avg Time per Task: 45.68s
  Results saved to: results/oolong_results.json

...

################################################################################
BENCHMARK SUMMARY
################################################################################

Total Execution Time: 1234.56s

OOLONG:
  Status: COMPLETED
  Accuracy: 0.85
  Total Time: 456.78s
  Avg Time/Task: 45.68s

DEEP RESEARCH:
  Status: COMPLETED
  Accuracy: 0.75
  Total Time: 398.24s
  Avg Time/Task: 79.65s

RULER:
  Status: COMPLETED
  Accuracy: 0.90
  Total Time: 379.54s
  Avg Time/Task: 18.98s

✓ Summary saved to: results/summary.json

================================================================================
Benchmark execution completed!
================================================================================
```

## Performance Considerations

### For Long Context (1M+ Tokens)

1. **Increase Timeouts**:
   ```bash
   python run_benchmarks.py --wasm-timeout 60 --max-tasks 5
   ```

2. **Adjust Max Depth**:
   ```bash
   python run_benchmarks.py --max-depth 2  # Less recursion, faster execution
   ```

3. **Monitor Memory Usage**:
   - WASM manager may require significant memory for large contexts
   - Consider reducing `--max-tasks` if memory is constrained

4. **Parallel Execution**:
   - The script uses asyncio for efficient I/O
   - Each benchmark runs sequentially for accurate timing

### Job Completion Time Tracking

The script tracks:
- **Total time** per benchmark
- **Average time** per task
- **Overall execution time** for all benchmarks

This is critical for evaluating RLM performance on long-context tasks.

## Troubleshooting

### WASM Service Not Available

**Error**: "Failed to create WASM session"

**Solution**:
```bash
# Check if WASM manager is running
curl http://localhost:8080/sessions

# Start WASM manager
python -m rlm.wasm.wasm_manager
```

### API Key Issues

**Error**: "Authentication failed"

**Solution**:
```bash
# Set environment variable
export LLM_API_KEY="your-key-here"

# Or pass via command line
python run_benchmarks.py --api-key your-key-here
```

### Timeout Errors

**Error**: "Request timed out"

**Solution**:
```bash
# Increase timeout
python run_benchmarks.py --wasm-timeout 60
```

### Memory Issues

**Error**: "Out of memory"

**Solution**:
```bash
# Reduce number of tasks
python run_benchmarks.py --max-tasks 5

# Or reduce context length
# (configure in benchmark config)
```

## Advanced Usage

### Custom Benchmark Configuration

You can create custom benchmark configurations:

```python
from run_benchmarks import create_rlm_repl_with_sidecar, run_oolong_benchmark

# Create RLM with sidecar
rlm = create_rlm_repl_with_sidecar(
    api_key="your-key",
    model="gpt-4o",
    max_depth=3,
    wasm_service_url="http://localhost:8080",
    enable_logging=True
)

# Run benchmark with custom config
config = {
    "max_tasks": 20,
    "context_lengths": [1000000, 5000000],
    "timeout": 60
}

results = run_oolong_benchmark(rlm, config, output_dir="results/custom")
```

### Programmatic Usage

```python
from run_benchmarks import (
    create_rlm_repl_with_sidecar,
    run_all_benchmarks
)

# Initialize
rlm = create_rlm_repl_with_sidecar(
    api_key="sk-xxx",
    model="gpt-4o"
)

# Run benchmarks
results = run_all_benchmarks(
    rlm,
    config={"max_tasks": 10},
    output_dir="results/run1"
)

# Access results
print(f"OOLONG Accuracy: {results['oolong']['metrics']['overall_accuracy']}")
print(f"Total Time: {results['oolong']['total_time']:.2f}s")
```

## Integration with CI/CD

You can integrate the benchmark runner into your CI/CD pipeline:

```yaml
# .github/workflows/benchmarks.yml
name: RLM Benchmarks

on: [push, pull_request]

jobs:
  benchmarks:
    runs-on: ubuntu-latest
    
    steps:
    - uses: actions/checkout@v3
    
    - name: Set up Python
      uses: actions/setup-python@v4
      with:
        python-version: '3.11'
    
    - name: Install dependencies
      run: pip install -r requirements.txt
    
    - name: Start WASM Manager
      run: python -m rlm.wasm.wasm_manager &
    
    - name: Run Benchmarks
      env:
        LLM_API_KEY: ${{ secrets.LLM_API_KEY }}
      run: |
        python run_benchmarks.py \
          --model gpt-4o \
          --max-tasks 5 \
          --output-dir results
    
    - name: Upload Results
      uses: actions/upload-artifact@v3
      with:
        name: benchmark-results
        path: results/
```

## Support

For issues or questions:
1. Check the troubleshooting section above
2. Review the code comments in `run_benchmarks.py`
3. Consult the RLM documentation

## License

Same as RLM project.
