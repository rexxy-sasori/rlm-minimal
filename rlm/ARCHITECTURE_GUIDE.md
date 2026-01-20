# RLM Architecture Guide

RLM supports two distinct architectures for executing generated code during inference.

## Architecture Overview

```
RLM Package Structure
├── rlm/
│   ├── local/              # Local execution architecture
│   │   ├── repl.py         # Local REPL environment
│   │   ├── rlm_repl.py     # RLM with local execution
│   │   └── __init__.py
│   ├── remote/             # Remote execution architecture
│   │   ├── repl_remote.py  # Remote REPL client
│   │   ├── rlm_service.py  # RLM HTTP service
│   │   └── __init__.py
│   ├── wasm/               # WASM execution engine
│   │   ├── repl_wasm.py    # WASM executor
│   │   ├── repl_wasm_service.py  # WASM HTTP service
│   │   └── __init__.py
│   ├── utils/              # Shared utilities
│   ├── logger/             # Logging components
│   └── rlm.py              # Base RLM class
```

## Architecture 1: Local Execution (Default)

### How It Works

```
┌─────────────────────────────────────────────┐
│         RLM Inference Process               │
│                                             │
│  ┌─────────────────────────────────────┐   │
│  │  LLM API Client                     │   │
│  └────────────┬────────────────────────┘   │
│               │ Generate code               │
│               ▼                             │
│  ┌─────────────────────────────────────┐   │
│  │  Code Execution (Local)             │   │
│  │  - Same process as inference        │   │
│  │  - Direct Python execution          │   │
│  └────────────┬────────────────────────┘   │
│               │ Return results             │
│               ▼                             │
│  ┌─────────────────────────────────────┐   │
│  │  RLM Logic (Orchestration)          │   │
│  └─────────────────────────────────────┘   │
└─────────────────────────────────────────────┘
```

### Pros
- ✅ Simple setup - no additional services required
- ✅ Low latency - same process execution
- ✅ Easy debugging - everything in one place
- ✅ No network overhead

### Cons
- ❌ Security risk - code runs in same process as LLM
- ❌ No isolation - malicious code can access LLM API keys
- ❌ Resource contention - code execution competes with LLM
- ❌ Not suitable for production with untrusted code

### Use Cases
- Development and testing
- Local experimentation
- Trusted code environments
- Low-security requirements

### Usage Example

```python
from rlm.local import RLM_REPL

# Initialize RLM with local execution
rlm = RLM_REPL(
    api_key="your-key",
    model="gpt-5",
    max_depth=3
)

# Run inference
context = "You are a helpful assistant..."
query = "What is 42 + 10?"

result = rlm.completion(context, query)
print(result)
```

### Files
- `rlm/local/repl.py` - Local REPL environment
- `rlm/local/rlm_repl.py` - RLM with local execution
- `rlm/local/__init__.py` - Module exports

## Architecture 2: Remote WASM Execution (Secure)

### How It Works

```
┌─────────────────────────────────────────────────────────────────┐
│                     Kubernetes Cluster                          │
│                                                                 │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │              RLM Inference Deployment                    │   │
│  │  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐     │   │
│  │  │  RLM Pod 1  │  │  RLM Pod 2  │  │  RLM Pod 3  │     │   │
│  │  │  (LLM API  │  │  (LLM API  │  │  (LLM API  │     │   │
│  │  │   + Logic) │  │   + Logic) │  │   + Logic) │     │   │
│  │  └─────────────┘  └─────────────┘  └─────────────┘     │   │
│  │         ▲                                                  │   │
│  │         │ HTTP API Calls                                   │   │
│  │         ▼                                                  │   │
│  └─────────────────────────────────────────────────────────┘   │
│                              │                                  │
│                              ▼                                  │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │           WASM Execution Service (Stateless)            │   │
│  │  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐     │   │
│  │  │ WASM Pod 1  │  │ WASM Pod 2  │  │ WASM Pod 3  │     │   │
│  │  │  (Pyodide  │  │  (Pyodide  │  │  (Pyodide  │     │   │
│  │  │   Sandbox) │  │   Sandbox) │  │   Sandbox) │     │   │
│  │  └─────────────┘  └─────────────┘  └─────────────┘     │   │
│  └─────────────────────────────────────────────────────────┘   │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

### Data Flow

```
1. User sends query to RLM service
   │
   ▼
2. LLM generates Python code
   │
   ▼
3. RLM sends code to WASM service via HTTP POST /execute
   │
   ▼
4. WASM service executes code in Pyodide sandbox
   │
   ▼
5. Results returned (stdout, stderr, variables)
   │
   ▼
6. RLM continues inference with results
   │
   ▼
7. Final answer returned to user
```

### Pros
- ✅ Maximum security - complete isolation
- ✅ LLM API keys never exposed to execution plane
- ✅ Resource isolation - no contention
- ✅ Scalable - scale RLM and WASM independently
- ✅ Production-ready - suitable for untrusted code
- ✅ Defense in depth - multiple security layers

### Cons
- ❌ More complex setup - requires k8s deployment
- ❌ Network latency - HTTP communication overhead
- ❌ Additional infrastructure - WASM service required

### Use Cases
- Production deployment
- Multi-tenant environments
- Executing untrusted code
- High-security requirements
- Kubernetes-based infrastructure

### Usage Example

#### RLM Inference Service

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
context = "You are a helpful assistant..."
query = "What is 42 + 10?"

result = rlm.completion(context, query)
print(result)
```

#### WASM Execution Service

```python
# Run as HTTP service
python -m rlm.wasm.repl_wasm_service --host 0.0.0.0 --port 8000
```

Or deploy via k8s:

```bash
kubectl apply -f deploy/k8s/wasm-repl-deployment.yaml
```

### Files
- `rlm/remote/repl_remote.py` - Remote REPL client
- `rlm/remote/rlm_service.py` - RLM HTTP service
- `rlm/wasm/repl_wasm.py` - WASM executor
- `rlm/wasm/repl_wasm_service.py` - WASM HTTP service

## Architecture Comparison

| Feature | Local Execution | Remote WASM Execution |
|---------|----------------|----------------------|
| **Security** | Low - same process | High - complete isolation |
| **Complexity** | Simple - no extra services | Complex - k8s deployment |
| **Latency** | Low - same process | Higher - network overhead |
| **Scalability** | Limited | Excellent - independent scaling |
| **Isolation** | None | Complete - WASM sandbox |
| **LLM Key Safety** | At risk | Protected - never exposed |
| **Resource Management** | Shared | Dedicated quotas |
| **Setup Time** | Minutes | Hours (k8s deployment) |
| **Debugging** | Easy | More complex |
| **Production Ready** | No | Yes |
| **Use Case** | Development/Testing | Production/High Security |

## Which Architecture Should You Choose?

### Choose Local Execution If:
- You're developing or testing
- You trust the generated code
- You need minimal setup
- You're working in a single-machine environment
- Low latency is critical

### Choose Remote WASM Execution If:
- You're deploying to production
- You need to execute untrusted code
- Security is a top priority
- You're running in Kubernetes
- You need to scale independently
- You have compliance requirements

## Migration Guide

### From Local to Remote

1. **Deploy WASM service**:
   ```bash
   kubectl apply -f deploy/k8s/wasm-repl-deployment.yaml
   ```

2. **Update your code**:
   ```python
   # Before (local)
   from rlm.local import RLM_REPL
   rlm = RLM_REPL(model="gpt-5")
   
   # After (remote)
   from rlm.remote import RemoteREPLFactory
   from rlm.local import RLM_REPL
   
   factory = RemoteREPLFactory(wasm_service_url="http://wasm-service:8000")
   rlm = RLM_REPL(model="gpt-5")
   ```

3. **Apply network policies**:
   ```bash
   kubectl apply -f deploy/k8s/network-policies.yaml
   ```

## Deployment Options

### Option A: Local Development

```bash
# Install dependencies
pip install -r requirements.txt

# Run local RLM
python -c "
from rlm.local import RLM_REPL
rlm = RLM_REPL(model='gpt-5')
result = rlm.completion('context', 'query')
print(result)
"
```

### Option B: Local with Remote WASM

```bash
# Terminal 1: Start WASM service
python -m rlm.wasm.repl_wasm_service --port 8000

# Terminal 2: Run RLM with remote execution
WASM_SERVICE_URL=http://localhost:8000 python -c "
from rlm.remote import RemoteREPLFactory
from rlm.local import RLM_REPL

factory = RemoteREPLFactory(wasm_service_url='http://localhost:8000')
rlm = RLM_REPL(model='gpt-5')
result = rlm.completion('context', 'query')
print(result)
"
```

### Option C: Kubernetes Deployment

See [DEPLOYMENT_GUIDE.md](../deploy/docs/DEPLOYMENT_GUIDE.md) for complete instructions.

## Security Considerations

### Local Execution
- Only execute code you trust
- Never expose to untrusted inputs
- Consider as development-only

### Remote WASM Execution
- Use network policies to restrict traffic
- Store secrets in k8s Secrets
- Enable audit logging
- Regular security updates
- Monitor resource usage

## Performance Tips

### Local Execution
- Reuse RLM instances
- Batch similar queries
- Monitor memory usage

### Remote WASM Execution
- Use connection pooling
- Set appropriate timeouts
- Scale WASM replicas based on load
- Deploy RLM and WASM in same AZ
- Use HTTP/2 for multiplexing

## Monitoring

### Local Execution
- Log to stdout/stderr
- Use Python profiling
- Monitor process metrics

### Remote WASM Execution
- Use Prometheus for metrics
- Use Grafana for dashboards
- Monitor k8s pod metrics
- Track HTTP request latency
- Alert on error rates

## Troubleshooting

### Local Execution Issues
- Check Python version compatibility
- Verify LLM API key is set
- Review error logs
- Check memory usage

### Remote Execution Issues
- Verify WASM service is running
- Check network connectivity
- Review HTTP error codes
- Monitor WASM pod health
- Check network policies

## Best Practices

### General
- Always validate generated code
- Set appropriate timeouts
- Use logging for debugging
- Test with known inputs

### Local Execution
- Use for development only
- Never in production
- Limit code complexity
- Monitor resource usage

### Remote Execution
- Use k8s for deployment
- Enable network policies
- Use HPA for scaling
- Monitor all components
- Regular security audits

## Resources

- [Deployment Guide](../deploy/docs/DEPLOYMENT_GUIDE.md)
- [Secure Architecture](../deploy/docs/SECURE_ARCHITECTURE_SUMMARY.md)
- [WASM Quick Start](../deploy/docs/WASM_QUICKSTART.md)
- [k8s Configuration](../deploy/k8s/)
- [Docker Images](../deploy/docker/)

## Support

For issues or questions:
1. Check this guide
2. Review the deployment documentation
3. Examine the test suite
4. Check k8s logs and metrics
5. Review security best practices
