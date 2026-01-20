# Secure WASM Architecture for RLM - Summary

> **Note:** This is Architecture 3 (Different-Pod Execution) in the [main RLM Architecture Guide](/Users/rexsasori/rlm-minimal/rlm/ARCHITECTURE_GUIDE.md). Refer to the main guide for architecture comparison, pros/cons, and use cases.

## The Problem

When RLM generates code during inference, executing it directly in the same pod creates security risks:
- Arbitrary code execution in LLM inference environment
- Potential data exfiltration (LLM API keys, sensitive data)
- Pod compromise or resource exhaustion

## The Solution: Separate Execution Plane

**The runtime lives separately from the model** in a dedicated WASM execution plane.

## Architecture

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

## Data Flow

```
User Query
    │
    ▼
┌─────────────┐
│  RLM Pod    │ ─────────────────────────────────┐
│  (Inference)│                                  │
└─────────────┘                                  │
    │                                            │
    │ 1. LLM generates code                      │
    │                                            │
    ▼                                            │
┌──────────────────┐                             │
│  Code Generated  │                             │
└──────────────────┘                             │
    │                                            │
    │ 2. Send code to WASM Service via HTTP      │
    │                                            │
    ▼                                            │
┌──────────────────┐                             │
│  HTTP Request    │                             │
│  POST /execute   │                             │
└──────────────────┘                             │
    │                                            │
    ▼                                            │
┌─────────────┐                                  │
│ WASM Pod    │  3. Execute in Pyodide sandbox   │
│ (Sandbox)   │                                  │
└─────────────┘                                  │
    │                                            │
    │ 4. Return results (stdout, stderr, vars)   │
    │                                            │
    ▼                                            │
┌──────────────────┐                             │
│  HTTP Response   │                             │
└──────────────────┘                             │
    │                                            │
    ▼                                            │
┌─────────────┐                                  │
│  RLM Pod    │ ◄────────────────────────────────┘
│  (Inference)│  5. Continue inference with results
└─────────────┘
    │
    │ 6. Return final answer
    ▼
User Response
```

## Key Components

### 1. RLM Inference Plane

**Files**:
- [Dockerfile.rlm](Dockerfile.rlm) - Container image
- [k8s/rlm-deployment.yaml](k8s/rlm-deployment.yaml) - k8s deployment
- [rlm/rlm_service.py](rlm/rlm_service.py) - HTTP service
- [rlm/repl_remote.py](rlm/repl_remote.py) - Remote REPL client

**Responsibilities**:
- LLM API calls (OpenAI or compatible)
- Prompt engineering and context management
- Code generation (NOT execution)
- Orchestration of recursive calls
- Communication with WASM service

**Security**:
- Has access to LLM API keys
- No code execution capability
- Network policy: only egress to WASM service and LLM API

### 2. WASM Execution Plane

**Files**:
- [Dockerfile.wasm-repl](../deploy/docker/Dockerfile.wasm-repl) - Container image
- [k8s/wasm-repl-deployment.yaml](k8s/wasm-repl-deployment.yaml) - k8s deployment
- [rlm/repl_wasm.py](rlm/repl_wasm.py) - WASM executor
- [rlm/repl_wasm_service.py](rlm/repl_wasm_service.py) - HTTP service

**Responsibilities**:
- Receive code for execution via HTTP API
- Execute code in Pyodide WASM sandbox
- Return results (stdout, stderr, variables)
- Enforce resource limits and timeouts

**Security**:
- Isolated WASM sandbox
- NO access to LLM API keys
- NO access to sensitive data
- Resource quotas per execution
- Network policy: only ingress from RLM service

### 3. Network Security

**File**: [k8s/network-policies.yaml](k8s/network-policies.yaml)

- RLM can only talk to WASM service and LLM API
- WASM service only accepts traffic from RLM
- Default deny all other traffic

## Quick Deployment (6 Steps)

### 1. Build Images

```bash
# Build RLM inference image
docker build -t rlm-inference:latest -f deploy/docker/Dockerfile.rlm .

# Build WASM execution image
docker build -t wasm-repl:latest -f deploy/docker/Dockerfile.wasm-repl .
```

### 2. Deploy to Kubernetes

```bash
# Deploy RLM inference
kubectl apply -f k8s/rlm-deployment.yaml
kubectl apply -f k8s/rlm-service.yaml

# Deploy WASM execution
kubectl apply -f k8s/wasm-repl-deployment.yaml
kubectl apply -f k8s/wasm-repl-service.yaml

# Apply network policies
kubectl apply -f k8s/network-policies.yaml
```

### 3. Configure Environment Variables

```bash
# Set in deployment manifests or via ConfigMap
export LLM_API_KEY="your-key"
export WASM_SERVICE_URL="http://wasm-repl-service:8000"
export LOG_LEVEL="INFO"
```

### 4. Verify Deployment

```bash
# Check pods
kubectl get pods -l app=rlm
kubectl get pods -l app=wasm-repl

# Check services
kubectl get services

# Test WASM service
kubectl exec -it <rlm-pod> -- curl http://wasm-repl-service:8000/health
```

### 5. Test Inference

```bash
# Port forward to RLM service
kubectl port-forward service/rlm-service 8000:8000

# Test with curl
curl -X POST http://localhost:8000/completion \
  -H "Content-Type: application/json" \
  -d '{
    "context": "You are a helpful assistant.",
    "query": "What is 42 + 10?"
  }'
```

### 6. Monitor and Scale

```bash
# View logs
kubectl logs -f deployment/rlm-deployment
kubectl logs -f deployment/wasm-repl-deployment

# Scale deployments
kubectl scale deployment/rlm-deployment --replicas=5
kubectl scale deployment/wasm-repl-deployment --replicas=10
```

## Security Features

### Defense in Depth

| Layer | Mechanism | Purpose |
|-------|-----------|----------|
| **1. Network** | Network policies | Restrict traffic between components |
| **2. Pod** | Isolated pods | Prevent pod-to-pod attacks |
| **3. Container** | Runtime security | Limit container capabilities |
| **4. WASM** | Pyodide sandbox | Isolate code execution |
| **5. Application** | API authentication | Secure API endpoints |

### Resource Protection

```yaml
# Example resource limits
resources:
  requests:
    memory: "1Gi"
    cpu: "500m"
  limits:
    memory: "2Gi"
    cpu: "1000m"
```

## Monitoring

### Metrics to Track

- **RLM Inference**:
  - Request latency
  - Code generation frequency
  - Error rates
  - Concurrent sessions

- **WASM Execution**:
  - Execution duration
  - Sandbox initialization time
  - Memory usage per execution
  - Timeout events

### Logging

```python
# Example structured logging
import logging

logger = logging.getLogger(__name__)

logger.info(
    "Code execution",
    extra={
        "execution_id": "abc123",
        "duration_ms": 42,
        "success": True,
        "stdout_lines": 10,
        "stderr_lines": 0
    }
)
```

## References

- [Main RLM Architecture Guide](/Users/rexsasori/rlm-minimal/rlm/ARCHITECTURE_GUIDE.md)
- [Kubernetes Network Policies](https://kubernetes.io/docs/concepts/services-networking/network-policies/)
- [Pyodide Documentation](https://pyodide.org/)
- [Deployment Guide](DEPLOYMENT_GUIDE.md)
- [WASM Quickstart](WASM_QUICKSTART.md)
