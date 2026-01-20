# RLM Benchmarks

This directory contains the benchmark suite for RLM (Recursive Language Models) with sidecar WASM pattern.

## Directory Structure

```
benchmarks/
├── docs/                      # Benchmark documentation
│   ├── BENCHMARK_GUIDE.md     # User guide with usage examples
│   ├── BENCHMARK_ANALYSIS.md  # Analysis methodology
│   ├── DATASET_SETUP.md       # Dataset preparation guide
│   └── KUBERNETES_DEPLOYMENT.md # K8s deployment guide
├── __init__.py                # Package exports
├── run_benchmarks.py          # Main benchmark runner CLI
├── base.py                    # Base benchmark classes
├── config.py                  # Configuration classes
├── runner.py                  # Benchmark runner implementation
├── analysis.py                # Result analysis utilities
├── oolong.py                  # OOLONG benchmark implementation
├── deep_research.py           # Deep Research benchmark implementation
└── ruler.py                   # RULER benchmark implementation
```

## Quick Start

### From Project Root

```bash
# Use the convenience script
./run_benchmarks.sh --api-key YOUR_KEY --model gpt-4o --async --concurrency 5

# Or run directly
python benchmarks/run_benchmarks.py --api-key YOUR_KEY --model gpt-4o --async
```

### From Benchmarks Directory

```bash
cd benchmarks
python run_benchmarks.py --api-key YOUR_KEY --model gpt-4o --async
```

## Available Benchmarks

1. **OOLONG**: Difficult long-context benchmark (1M+ tokens)
2. **Deep Research**: Complex research tasks with browsing
3. **RULER**: Needle-in-haystack evaluation

## Async Mode (Recommended)

The benchmark runner supports asyncio for parallel task processing:

```bash
python benchmarks/run_benchmarks.py \
  --api-key YOUR_KEY \
  --model gpt-4o \
  --async \
  --concurrency 5 \
  --pool-size 3 \
  --max-tasks 10
```

### Async Architecture

- **Concurrency Control**: Configurable with `--concurrency` (default: 5)
- **RLM Pool**: Multiple RLM instances distribute workload (`--pool-size`, default: 3)
- **Semaphore**: Limits parallel tasks to prevent resource exhaustion
- **Task Distribution**: Round-robin assignment across RLM pool

## Programmatic Usage

```python
from benchmarks import OOLONGBenchmark, DeepResearchBenchmark
from rlm.local.rlm_repl import RLM_REPL

# Create RLM instance
rlm = RLM_REPL(
    api_key="your_key",
    model="gpt-4o"
)

# Run specific benchmark
oolong = OOLONGBenchmark(rlm)
results = oolong.run(max_tasks=10)

print(results.summary())
```

## Configuration

See [BENCHMARK_GUIDE.md](docs/BENCHMARK_GUIDE.md) for detailed configuration options.

## Dependencies

```bash
pip install -r requirements.txt
```

The benchmark suite requires:
- Python 3.10+
- asyncio
- OpenAI SDK
- RLM package

## Sidecar WASM Pattern

All benchmarks use the sidecar WASM pattern for secure, isolated code execution:

- **WASM Manager**: Runs as sidecar container at `http://localhost:8080`
- **Session Management**: Each RLM instance gets its own WASM session
- **Isolation**: Code execution in sandboxed WASM environment
- **Security**: No direct code execution in Python process

See [BENCHMARK_GUIDE.md](docs/BENCHMARK_GUIDE.md) for deployment details.
