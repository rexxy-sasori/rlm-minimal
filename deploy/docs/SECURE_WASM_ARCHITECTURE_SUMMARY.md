# Secure WASM Architecture for RLM - Summary

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
- [Dockerfile.wasm](Dockerfile.wasm) - Container image
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
docker build -f Dockerfile.wasm -t rlm-minimal-wasm:latest .
docker build -f Dockerfile.rlm -t rlm-minimal:latest .
```

### 2. Create Secret

```bash
kubectl create secret generic llm-secrets \
  --from-literal=api-key="your-llm-api-key"
```

### 3. Deploy WASM Service

```bash
kubectl apply -f k8s/wasm-repl-deployment.yaml
kubectl get pods -l app=wasm-repl
```

### 4. Deploy RLM Service

```bash
kubectl apply -f k8s/rlm-deployment.yaml
kubectl get pods -l app=rlm-inference
```

### 5. Apply Network Policies

```bash
kubectl apply -f k8s/network-policies.yaml
```

### 6. Test

```bash
# Test WASM
WASM_IP=$(kubectl get service wasm-repl-service -o jsonpath='{.status.loadBalancer.ingress[0].ip}')
curl -X POST http://$WASM_IP/execute \
  -H "Content-Type: application/json" \
  -d '{"code": "print(\"Hello WASM!\")", "context": {}}'

# Test RLM
RLM_IP=$(kubectl get service rlm-inference-service -o jsonpath='{.status.loadBalancer.ingress[0].ip}')
curl -X POST http://$RLM_IP/infer \
  -H "Content-Type: application/json" \
  -d '{"query": "What is 42 + 10?", "context": "You are helpful."}'
```

## Security Features

✅ **Complete Isolation**: LLM inference and code execution in separate pods
✅ **Network Segmentation**: Network policies restrict traffic flow
✅ **WASM Sandbox**: Code runs in isolated Pyodide environment
✅ **Resource Limits**: CPU/memory quotas prevent exhaustion
✅ **Secrets Protection**: LLM keys never reach WASM plane
✅ **Non-Root Users**: All containers run as non-root
✅ **No Privileges**: No privileged containers or capabilities

## Benefits

### Security
- Even if WASM plane is compromised, LLM keys are safe
- No direct code execution in inference environment
- Defense in depth with multiple security layers

### Scalability
- Scale RLM and WASM independently
- Handle more inference requests by scaling RLM
- Handle more code execution by scaling WASM
- Stateless WASM pods can use spot instances

### Reliability
- Rolling updates for zero downtime
- Pod disruption budgets for high availability
- Independent failure domains

### Performance
- WASM execution is fast (Pyodide pre-initialized)
- HTTP communication is efficient
- Connection pooling between services

## Configuration

### Environment Variables

**RLM Inference**:
- `LLM_API_KEY` - LLM API key (from secret)
- `LLM_BASE_URL` - LLM API base URL
- `LLM_MODEL` - Default LLM model
- `WASM_SERVICE_URL` - WASM service URL (http://wasm-repl-service:8000)
- `MAX_DEPTH` - Max recursion depth
- `EXECUTION_TIMEOUT` - Code timeout (30s)

**WASM Execution**:
- `MAX_DEPTH` - Max recursion depth
- `EXECUTION_TIMEOUT` - Code timeout (30s)

### Resource Limits

**RLM Pods**:
- Requests: 1Gi memory, 1 CPU
- Limits: 2Gi memory, 2 CPU

**WASM Pods**:
- Requests: 512Mi memory, 0.5 CPU
- Limits: 1Gi memory, 1 CPU

## Scaling

### Manual Scaling

```bash
kubectl scale deployment rlm-inference-deployment --replicas=10
kubectl scale deployment wasm-repl-deployment --replicas=20
```

### Autoscaling

See [DEPLOYMENT_GUIDE.md](DEPLOYMENT_GUIDE.md) for HPA configuration.

## Monitoring

### Metrics

```bash
# Pod resource usage
kubectl top pod -l app=rlm-inference
kubectl top pod -l app=wasm-repl

# Deployment status
kubectl rollout status deployment/rlm-inference-deployment
kubectl rollout status deployment/wasm-repl-deployment
```

### Logging

```bash
# Follow logs
kubectl logs -l app=rlm-inference -f
kubectl logs -l app=wasm-repl -f
```

## Documentation

- [Deployment Guide](DEPLOYMENT_GUIDE.md) - Complete deployment instructions
- [Secure Architecture](k8s/doc/SECURE_ARCHITECTURE.md) - Detailed architecture explanation
- [WASM Setup](k8s/doc/WASM_REPL_SETUP.md) - WASM-specific documentation
- [Quick Start](WASM_QUICKSTART.md) - Quick start guide

## Key Files

| File | Purpose |
|------|--------|
| [Dockerfile.rlm](Dockerfile.rlm) | RLM inference container |
| [Dockerfile.wasm](Dockerfile.wasm) | WASM execution container |
| [k8s/rlm-deployment.yaml](k8s/rlm-deployment.yaml) | RLM k8s deployment |
| [k8s/wasm-repl-deployment.yaml](k8s/wasm-repl-deployment.yaml) | WASM k8s deployment |
| [k8s/network-policies.yaml](k8s/network-policies.yaml) | Network security |
| [rlm/rlm_service.py](rlm/rlm_service.py) | RLM HTTP service |
| [rlm/repl_remote.py](rlm/repl_remote.py) | Remote REPL client |
| [rlm/repl_wasm.py](rlm/repl_wasm.py) | WASM executor |
| [rlm/repl_wasm_service.py](rlm/repl_wasm_service.py) | WASM HTTP service |
| [tests/test_wasm_repl.py](tests/test_wasm_repl.py) | Test suite |

## Conclusion

**Yes, the runtime lives separately** in a dedicated WASM execution plane. This provides:

✅ **Maximum Security**: Complete isolation between LLM inference and code execution
✅ **Scalability**: Independent scaling of each component
✅ **Reliability**: High availability with multiple replicas
✅ **Maintainability**: Clear separation of concerns
✅ **Observability**: Comprehensive monitoring and logging

The separate execution plane ensures that even if the WASM service is compromised, the LLM API keys and sensitive data remain protected.

---

**To deploy**: Follow the [Deployment Guide](DEPLOYMENT_GUIDE.md)
**To understand**: Read the [Secure Architecture](k8s/doc/SECURE_ARCHITECTURE.md) documentation
**To test**: Run the [test suite](tests/test_wasm_repl.py)
