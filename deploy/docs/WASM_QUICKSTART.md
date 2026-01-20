# WASM REPL Quick Start Guide

This guide helps you quickly set up and deploy the WASM-based REPL environment for RLM in Kubernetes.

## What's Included

- **WASM Executor**: [repl_wasm.py](rlm/repl_wasm.py) - Core WASM execution engine using Pyodide
- **HTTP Service**: [repl_wasm_service.py](rlm/repl_wasm_service.py) - HTTP server for remote execution
- **k8s Deployment**: [wasm-repl-deployment.yaml](k8s/wasm-repl-deployment.yaml) - Kubernetes deployment config
- **Docker Image**: [Dockerfile.wasm](Dockerfile.wasm) - Container image definition
- **Requirements**: [requirements-wasm.txt](requirements-wasm.txt) - Python dependencies
- **Tests**: [test_wasm_repl.py](tests/test_wasm_repl.py) - Test suite
- **Documentation**: [WASM_REPL_SETUP.md](k8s/doc/WASM_REPL_SETUP.md) - Complete documentation

## Quick Deployment (5 Steps)

### Step 1: Build the Docker Image

```bash
docker build -f Dockerfile.wasm -t rlm-minimal-wasm:latest .
```

### Step 2: Create LLM Secret

```bash
kubectl create secret generic llm-secrets \
  --from-literal=api-key="your-actual-api-key-here"
```

### Step 3: Deploy to Kubernetes

```bash
kubectl apply -f k8s/wasm-repl-deployment.yaml
```

### Step 4: Verify Deployment

```bash
# Check pods are running
kubectl get pods -l app=wasm-repl

# Get service IP
kubectl get service wasm-repl-service
```

### Step 5: Test the Service

```bash
# Replace <service-ip> with your actual service IP
curl -X POST http://<service-ip>/execute \
  -H "Content-Type: application/json" \
  -d '{
    "code": "print(\"Hello from WASM!\")\nx = 42\nprint(f\"The answer is {x}\")",
    "context": {},
    "timeout": 30
  }'
```

## Local Testing (Without k8s)

### Install Dependencies

```bash
pip install -r requirements-wasm.txt
```

### Run the Service

```bash
python -m rlm.repl_wasm_service --host 0.0.0.0 --port 8000
```

### Test Locally

```bash
curl -X POST http://localhost:8000/execute \
  -H "Content-Type: application/json" \
  -d '{"code": "print(\"Test\")", "context": {}}'
```

## Key Features

### 1. Sandboxed Execution
- Code runs in isolated WASM environment
- No direct access to host system
- Resource limits prevent abuse

### 2. HTTP API
- Simple REST API for code execution
- Health and readiness endpoints
- JSON-based requests/responses

### 3. Kubernetes Native
- Horizontal scaling support
- Health checks and liveness probes
- ConfigMaps and Secrets for configuration
- Resource requests and limits

### 4. Async Support
- Fully async/await based
- Concurrent execution support
- Timeout handling

### 5. Fallback Mode
- Automatically falls back to local Python when Pyodide not available
- Works in any Python environment
- No WASM runtime required for development

## Configuration

### Environment Variables

| Variable | Description | Default |
|----------|-------------|--------|
| `LLM_API_KEY` | Your LLM API key | Required |
| `LLM_BASE_URL` | LLM API base URL | https://api.openai.com/v1 |
| `LLM_MODEL` | Default LLM model | gpt-5-mini |
| `MAX_DEPTH` | Max recursion depth | 3 |
| `EXECUTION_TIMEOUT` | Code timeout (seconds) | 30 |

### k8s Resource Tuning

Edit [wasm-repl-deployment.yaml](k8s/wasm-repl-deployment.yaml):

```yaml
resources:
  requests:
    memory: "512Mi"   # Adjust based on your needs
    cpu: "500m"
  limits:
    memory: "1Gi"     # Adjust based on your needs
    cpu: "1000m"
```

## Scaling

### Manual Scaling

```bash
kubectl scale deployment wasm-repl-deployment --replicas=5
```

### Autoscaling

See [WASM_REPL_SETUP.md](k8s/doc/WASM_REPL_SETUP.md) for HPA configuration.

## Security Best Practices

1. **Never commit API keys** to version control
2. **Use k8s Secrets** for sensitive data
3. **Set resource limits** to prevent resource exhaustion
4. **Enable network policies** to restrict access
5. **Use TLS** for external access (via Ingress)

## Troubleshooting

### Pods Not Starting

```bash
# Check pod status and events
kubectl describe pod <pod-name>

# Check logs
kubectl logs <pod-name>
```

### Pyodide Initialization Issues

- Increase `initialDelaySeconds` in liveness probe
- Check network connectivity to Pyodide CDN
- Ensure sufficient memory allocation

### Timeout Errors

- Increase `EXECUTION_TIMEOUT` environment variable
- Optimize your code for faster execution
- Check resource limits

## Integration with RLM

### Using WASM REPL in Your Code

```python
import asyncio
from rlm.repl_wasm import WASMREPLEnv

async def execute_with_wasm():
    # Initialize WASM environment
    wasm_env = WASMREPLEnv(max_depth=3, timeout=30)
    await wasm_env.initialize()
    
    # Execute code
    result = await wasm_env.code_execution("""
print('Executing in WASM!')
x = 42 + 10
print(f'Result: {x}')
    """)
    
    print(result.stdout)
    
    # Cleanup
    await wasm_env.cleanup()

asyncio.run(execute_with_wasm())
```

## Performance Tips

1. **Reuse executors**: Create one executor and reuse it for multiple executions
2. **Set appropriate timeouts**: Don't set timeouts too high or too low
3. **Use context injection**: Pass variables via context instead of recreating them
4. **Monitor resource usage**: Use kubectl top to track pod resource usage
5. **Scale horizontally**: Add more replicas for higher throughput

## Next Steps

1. Read the [complete documentation](k8s/doc/WASM_REPL_SETUP.md)
2. Check out the [test suite](tests/test_wasm_repl.py) for usage examples
3. Explore the [k8s deployment](k8s/wasm-repl-deployment.yaml) configuration options
4. Customize the [Dockerfile](Dockerfile.wasm) for your specific needs

## Support

For issues or questions:
- Check the [documentation](k8s/doc/WASM_REPL_SETUP.md)
- Review the [test suite](tests/test_wasm_repl.py)
- Examine [k8s examples](k8s/)

## License

Same as RLM project.
