# RLM Minimal

Minimal implementation of RLM (Recursive Language Model) with two execution architectures for secure code execution and LLM interaction.

## 🏗️ Two Architectures

RLM supports two distinct architectures for executing generated code during inference:

### Architecture 1: Local Execution (Development)
- **Code runs in the same process** as RLM inference
- **Simple setup** - no additional services required
- **Low latency** - direct execution
- **Use case**: Development, testing, trusted code environments

```python
from rlm.local import RLM_REPL

rlm = RLM_REPL(model="gpt-5")
result = rlm.completion(context, query)
```

### Architecture 2: Remote WASM Execution (Production)
- **Code runs in separate WASM execution plane** via HTTP API
- **Complete isolation** between inference and execution
- **Maximum security** - LLM API keys never exposed to execution environment
- **Use case**: Production deployment, multi-tenant environments, untrusted code

```python
from rlm.remote import RemoteREPLFactory
from rlm.local import RLM_REPL

factory = RemoteREPLFactory(wasm_service_url="http://wasm-service:8000")
rlm = RLM_REPL(model="gpt-5")
result = rlm.completion(context, query)
```

## ✨ Features

- **Code Execution**: Execute Python code in sandboxed environment (local or WASM)
- **LLM Integration**: Interact with various LLM models (OpenAI and compatible)
- **Recursive Reasoning**: Multi-step reasoning with configurable depth
- **Logging**: Comprehensive logging with TimescaleDB integration
- **Token Cache Tracking**: Monitor LLM token cache usage and cost savings
- **Production Ready**: Kubernetes deployment with secure isolation
- **Scalable**: Independent scaling of inference and execution planes

## 🚀 Quick Start

### Option 1: Local Execution (Quickest)

```bash
# Install dependencies
pip install -r requirements.txt

# Run example
python examples/basic_usage.py
```

### Option 2: Remote WASM Execution (Production)

```bash
# Terminal 1: Start WASM service
python -m rlm.wasm.repl_wasm_service --host 0.0.0.0 --port 8000

# Terminal 2: Use RLM with remote execution
python -c "
from rlm.remote import RemoteREPLFactory
from rlm.local import RLM_REPL

factory = RemoteREPLFactory(wasm_service_url='http://localhost:8000')
rlm = RLM_REPL(model='gpt-5')
result = rlm.completion('context', 'What is 42 + 10?')
print(result)
"
```

### Option 3: Sidecar Architecture (Recommended for Production)

```bash
# Build Docker images
docker build -t rlm-inference:latest -f deploy/docker/Dockerfile.rlm-sidecar .
docker build -t wasm-manager:latest -f deploy/docker/Dockerfile.wasm-manager .

# Deploy to Kubernetes
kubectl apply -f deploy/k8s/rlm-sidecar-deployment.yaml

# Test state persistence
python examples/sidecar_state_persistence.py
```

### Option 4: Kubernetes Deployment (Legacy)

See [DEPLOYMENT_GUIDE.md](deploy/docs/DEPLOYMENT_GUIDE.md) for complete instructions.

```bash
# Deploy to k8s
kubectl apply -f deploy/k8s/wasm-repl-deployment.yaml
kubectl apply -f deploy/k8s/rlm-deployment.yaml
kubectl apply -f deploy/k8s/network-policies.yaml
```

## 📚 Documentation

### Architecture Guides (3 Architectures)
- **[Architecture Guide](rlm/ARCHITECTURE_GUIDE.md)**: Complete guide to all three architectures with comparison tables
  - **Architecture 1**: Local Execution (same process)
  - **Architecture 2**: Same-Pod Execution (sidecar pattern)
  - **Architecture 3**: Different-Pod Execution (remote)
- **[Sidecar Architecture Guide](deploy/docs/SIDECAR_ARCHITECTURE_GUIDE.md)**: Detailed Architecture 2 guide with deployment instructions
- **[Secure WASM Architecture Summary](deploy/docs/SECURE_WASM_ARCHITECTURE_SUMMARY.md)**: Architecture 3 quick deployment guide
- **[Secure Architecture](k8s/doc/SECURE_ARCHITECTURE.md)**: Architecture 3 security details

### Deployment Guides
- **[Deployment Guide](deploy/docs/DEPLOYMENT_GUIDE.md)**: Complete production deployment guide
- **[WASM Quick Start](deploy/docs/WASM_QUICKSTART.md)**: WASM execution quick start
- **[WASM REPL Setup](k8s/doc/WASM_REPL_SETUP.md)**: Complete WASM REPL setup guide

### Benchmark Documentation
- **[Benchmark Analysis](benchmarks/docs/BENCHMARK_ANALYSIS.md)**: Analysis of RLM benchmarks (OOLONG, RULER, Deep Research)
- **[Kubernetes Deployment](benchmarks/docs/KUBERNETES_DEPLOYMENT.md)**: Deploy benchmarks to Kubernetes
- **[Dataset Setup](benchmarks/docs/DATASET_SETUP.md)**: Setup benchmark datasets

### Core Documentation
- **[Depth Implementation](doc/DEPTH_IMPLEMENTATION.md)**: Depth parameter implementation details
- **[Query Example](doc/QUERY_EXAMPLE.md)**: Query API usage examples
- **[Dependencies](doc/DEPENDENCIES.md)**: Project dependencies documentation
- **[Change Summary](doc/CHANGE_SUMMARY.md)**: Kubernetes deployment changes summary

### Logging Documentation
- **[Logger README](rlm/logger/README.md)**: Main logger documentation
- **[TimescaleDB Quick Start](rlm/logger/doc/QUICKSTART_TIMESCALE.md)**: Get started with TimescaleDB logging
- **[Token Cache Tracking](rlm/logger/doc/TOKEN_CACHE_TRACKING.md)**: Track token cache usage and cost savings
- **[Query API](rlm/logger/doc/QUERY_API.md)**: Query logged data
- **[Recursive Logging](rlm/logger/doc/RECURSIVE_LOGGING.md)**: Recursive logging implementation

## 📁 Project Structure

```
rlm-minimal/
├── rlm/                          # Main package
│   ├── local/                    # Architecture 1: Local Execution
│   │   ├── repl.py               # Local REPL environment
│   │   ├── rlm_repl.py           # RLM with local execution
│   │   └── rlm_repl_tsdb.py      # RLM with TimescaleDB
│   ├── remote/                   # Architecture 2: Remote Execution
│   │   ├── repl_remote.py        # Remote REPL client
│   │   └── rlm_service.py        # RLM HTTP service
│   ├── wasm/                     # WASM Execution Engine
│   │   ├── repl_wasm.py          # WASM executor (Pyodide)
│   │   └── repl_wasm_service.py  # WASM HTTP service
│   ├── utils/                    # Shared utilities
│   ├── logger/                   # Logging components
│   ├── rlm.py                    # Base RLM class
│   ├── __init__.py               # Package exports
│   ├── ARCHITECTURE_GUIDE.md     # Architecture guide
│   └── STRUCTURE.txt             # Structure diagram
│
├── deploy/                       # Deployment files
│   ├── docker/                   # Docker images
│   │   ├── Dockerfile.rlm        # RLM inference image
│   │   └── Dockerfile.wasm       # WASM execution image
│   ├── k8s/                      # Kubernetes config
│   │   ├── rlm-deployment.yaml           # RLM deployment
│   │   ├── wasm-repl-deployment.yaml     # WASM deployment
│   │   └── network-policies.yaml         # Network security
│   └── docs/                     # Deployment docs
│
├── examples/                     # Example scripts
│   ├── basic_usage.py            # Basic usage example
│   └── model_comparison.py       # Model comparison example
│
├── tests/                        # Test suite
│   └── test_wasm_repl.py         # WASM execution tests
│
├── README.md                     # This file
├── ORGANIZATION_SUMMARY.md       # Reorganization summary
├── requirements.txt              # Core dependencies
└── requirements-wasm.txt         # WASM-specific dependencies
```

## 🛠️ Installation

### Core Dependencies

```bash
pip install -r requirements.txt
```

### WASM Dependencies (for remote execution)

```bash
pip install -r requirements-wasm.txt
```

## 🔧 Configuration

### Environment Variables

```bash
# LLM Configuration
export LLM_API_KEY="your-api-key"
export LLM_BASE_URL="https://api.openai.com/v1"
export LLM_MODEL="gpt-5"

# WASM Service (for remote execution)
export WASM_SERVICE_URL="http://wasm-repl-service:8000"

# Recursion Configuration
export MAX_DEPTH="3"
export MAX_ITERATIONS="20"
```

## 📖 Usage Examples

### Basic Local Execution

```python
from rlm.local import RLM_REPL

# Initialize RLM
rlm = RLM_REPL(
    api_key="your-key",
    model="gpt-5",
    max_depth=3
)

# Run inference
context = "You are a helpful assistant that can execute Python code."
query = "What is the square root of 256?"

result = rlm.completion(context, query)
print(result)
```

### Remote WASM Execution

```python
from rlm.remote import RemoteREPLFactory
from rlm.local import RLM_REPL

# Initialize remote REPL factory
factory = RemoteREPLFactory(
    wasm_service_url="http://wasm-repl-service:8000"
)

# Check if WASM service is healthy
if not factory.health_check():
    print("WASM service not available")

# Use RLM with remote execution
rlm = RLM_REPL(
    api_key="your-key",
    model="gpt-5",
    max_depth=3
)

# Run inference
context = "You are a helpful assistant that can execute Python code."
query = "Calculate 42 * 10 + 58"

result = rlm.completion(context, query)
print(result)
```

### With Logging

```python
from rlm.local import RLM_REPL
from rlm.logger.repl_logger import REPLEnvLogger

# Initialize with logging
rlm = RLM_REPL(
    api_key="your-key",
    model="gpt-5",
    enable_logging=True
)

# Run inference with logging
result = rlm.completion(context, query)
print(result)
```

## 🧪 Testing

```bash
# Run all tests
python -m pytest tests/ -v

# Run specific test
python tests/test_wasm_repl.py

# Run with coverage
python -m pytest tests/ --cov=rlm
```

## 🔒 Security

### Local Execution
- Only execute code you trust
- Never expose to untrusted inputs
- Consider as development-only

### Remote Execution
- Network policies restrict traffic flow
- LLM API keys never reach execution plane
- WASM sandbox provides additional isolation
- Resource limits prevent exhaustion attacks

## 📊 Performance

### Local Execution
- Low latency (same process)
- No network overhead
- Resource contention possible

### Remote Execution
- Network latency (HTTP communication)
- Connection pooling recommended
- Independent scaling of components
- Deploy in same AZ for best performance

## 🤝 Contributing

Contributions are welcome! Please:

1. Fork the repository
2. Create a feature branch
3. Add tests for new features
4. Ensure all tests pass
5. Submit a pull request

## 📝 License

MIT License - see [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- Pyodide for WASM Python execution
- OpenAI for LLM API
- Kubernetes for orchestration
- TimescaleDB for time-series data

## 📞 Support

For issues or questions:
1. Check the [Architecture Guide](rlm/ARCHITECTURE_GUIDE.md)
2. Review the [Deployment Guide](deploy/docs/DEPLOYMENT_GUIDE.md)
3. Examine the [examples](examples/)
4. Run the [test suite](tests/)
5. Create an issue on GitHub

## 🚀 What's Next

1. **Choose Architecture**
   - Local for development
   - Remote WASM for production

2. **Read Documentation**
   - Start with [Architecture Guide](rlm/ARCHITECTURE_GUIDE.md)
   - Then [Deployment Guide](deploy/docs/DEPLOYMENT_GUIDE.md)

3. **Start Coding**
   - Use `from rlm.local import ...` for local execution
   - Use `from rlm.remote import ...` for remote execution

4. **Deploy (if production)**
   - Follow deployment guide
   - Use k8s for orchestration
   - Enable network policies

**Happy coding! 🎉**
