# WASM-Based REPL Setup for k8s

This guide explains how to set up a WASM-based REPL environment for executing generated Python code in a Kubernetes cluster.

## Overview

The WASM REPL provides:
- **Sandboxed execution**: Code runs in isolated WASM environment
- **Security**: No direct access to host system resources
- **Scalability**: Easily deployable in k8s with horizontal scaling
- **Performance**: Fast initialization and execution using Pyodide

## Architecture

```
┌─────────────────────────────────────────────────────────┐
│                    k8s Cluster                          │
│  ┌─────────────────┐  ┌─────────────────┐              │
│  │  WASM REPL Pod  │  │  WASM REPL Pod  │              │
│  │  ┌───────────┐  │  │  ┌───────────┐  │              │
│  │  │  Pyodide  │  │  │  │  Pyodide  │  │              │
│  │  │  Runtime  │  │  │  │  Runtime  │  │              │
│  │  └───────────┘  │  │  └───────────┘  │              │
│  └─────────────────┘  └─────────────────┘              │
│  ┌───────────────────────────────────────────┐         │
│  │         Load Balancer (Service)           │         │
│  └───────────────────────────────────────────┘         │
└─────────────────────────────────────────────────────────┘
```

## Prerequisites

- Kubernetes cluster (v1.21+)
- kubectl configured
- Docker or container runtime
- LLM API key (OpenAI or compatible)

## Quick Start

### 1. Build the Docker Image

```bash
docker build -f deploy/docker/Dockerfile.wasm-repl -t rlm-minimal-wasm:latest .
```

### 2. Configure Secrets

Create a secret for your LLM API key:

```bash
kubectl create secret generic llm-secrets \
  --from-literal=api-key="your-actual-api-key-here"
```

### 3. Deploy to k8s

```bash
kubectl apply -f k8s/wasm-repl-deployment.yaml
```

### 4. Verify Deployment

```bash
# Check pods
kubectl get pods -l app=wasm-repl

# Check service
kubectl get service wasm-repl-service

# Check logs
kubectl logs -l app=wasm-repl
```

## Usage

### HTTP API Endpoints

#### Health Check
```bash
curl http://<service-ip>/health
```

#### Readiness Check
```bash
curl http://<service-ip>/ready
```

#### Execute Code
```bash
curl -X POST http://<service-ip>/execute \
  -H "Content-Type: application/json" \
  -d '{
    "code": "print(\"Hello from WASM!\")\nx = 42\ny = 58\nresult = x + y",
    "context": {},
    "timeout": 30
  }'
```

### Example Response

```json
{
  "success": true,
  "stdout": "Hello from WASM!\n",
  "stderr": "",
  "locals": {
    "x": 42,
    "y": 58,
    "result": 100
  },
  "execution_time": 0.123,
  "error": null
}
```

## Configuration

### Environment Variables

| Variable | Description | Default |
|----------|-------------|--------|
| `LLM_API_KEY` | API key for LLM provider | Required |
| `LLM_BASE_URL` | Base URL for LLM API | https://api.openai.com/v1 |
| `LLM_MODEL` | Default LLM model | gpt-5-mini |
| `MAX_DEPTH` | Maximum recursion depth | 3 |
| `EXECUTION_TIMEOUT` | Code execution timeout (seconds) | 30 |

### k8s Resource Configuration

Adjust resources in `wasm-repl-deployment.yaml`:

```yaml
resources:
  requests:
    memory: "512Mi"
    cpu: "500m"
  limits:
    memory: "1Gi"
    cpu: "1000m"
```

## Scaling

### Horizontal Scaling

```bash
# Scale to 5 replicas
kubectl scale deployment wasm-repl-deployment --replicas=5

# Or update the deployment spec
kubectl patch deployment wasm-repl-deployment -p '{"spec":{"replicas":5}}'
```

### Autoscaling

Create a Horizontal Pod Autoscaler:

```yaml
apiVersion: autoscaling/v2
kind: HorizontalPodAutoscaler
metadata:
  name: wasm-repl-hpa
spec:
  scaleTargetRef:
    apiVersion: apps/v1
    kind: Deployment
    name: wasm-repl-deployment
  minReplicas: 2
  maxReplicas: 10
  metrics:
  - type: Resource
    resource:
      name: cpu
      target:
        type: Utilization
        averageUtilization: 70
  - type: Resource
    resource:
      name: memory
      target:
        type: Utilization
        averageUtilization: 80
```

```bash
kubectl apply -f k8s/wasm-repl-hpa.yaml
```

## Security Considerations

1. **API Key Management**: Always store API keys in k8s secrets, not in configuration files
2. **Network Policies**: Restrict access to the WASM REPL service
3. **Resource Limits**: Set appropriate resource limits to prevent resource exhaustion
4. **Pod Security Policies**: Use PSPs or Pod Security Standards to enforce security
5. **TLS**: Use Ingress with TLS for external access

## Monitoring

### Prometheus Metrics

Add annotations for Prometheus scraping:

```yaml
metadata:
  annotations:
    prometheus.io/scrape: "true"
    prometheus.io/port: "8000"
    prometheus.io/path: "/metrics"
```

### Logging

Configure structured logging:

```bash
kubectl logs -l app=wasm-repl -f --tail=100
```

## Troubleshooting

### Pods Not Starting

```bash
# Check pod status
kubectl describe pod <pod-name>

# Check events
kubectl get events --field-selector involvedObject.kind=Pod
```

### Pyodide Initialization Timeout

Increase `initialDelaySeconds` in liveness probe:

```yaml
livenessProbe:
  httpGet:
    path: /health
    port: 8000
  initialDelaySeconds: 60  # Increase this
  periodSeconds: 10
```

### Out of Memory Errors

Increase memory limits:

```yaml
resources:
  limits:
    memory: "2Gi"  # Increase this
```

## Performance Optimization

1. **Pre-warm Pyodide**: Initialize Pyodide during container startup
2. **Connection Pooling**: Reuse HTTP connections
3. **Resource Requests**: Set appropriate requests for better scheduling
4. **Node Affinity**: Schedule on nodes with better performance

## Local Development

### Run Locally

```bash
# Install dependencies
pip install -r requirements-wasm.txt

# Run the service
python -m rlm.repl_wasm_service --host 0.0.0.0 --port 8000
```

### Test Locally

```bash
curl -X POST http://localhost:8000/execute \
  -H "Content-Type: application/json" \
  -d '{"code": "print(\"Test\")", "context": {}}'
```

## Integration with RLM

To use the WASM REPL with RLM, modify the REPL initialization:

```python
from rlm.repl_wasm import WASMREPLEnv

async def main():
    wasm_env = WASMREPLEnv(max_depth=3, timeout=30)
    await wasm_env.initialize()
    
    result = await wasm_env.code_execution("x = 42")
    print(result.stdout)
    
    await wasm_env.cleanup()
```

## Cleanup

```bash
# Delete deployment
kubectl delete deployment wasm-repl-deployment

# Delete service
kubectl delete service wasm-repl-service

# Delete configmap
kubectl delete configmap llm-config

# Delete secret
kubectl delete secret llm-secrets
```

## References

- [Pyodide Documentation](https://pyodide.org/)
- [Kubernetes Documentation](https://kubernetes.io/docs/)
- [RLM Documentation](../README.md)
