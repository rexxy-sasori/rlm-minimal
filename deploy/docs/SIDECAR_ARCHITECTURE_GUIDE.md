# Sidecar Architecture Guide for RLM

> **Note:** This is Architecture 2 (Same-Pod Execution) in the [main RLM Architecture Guide](/Users/rexsasori/rlm-minimal/rlm/ARCHITECTURE_GUIDE.md). Refer to the main guide for architecture comparison, pros/cons, and use cases.

## Overview

The sidecar architecture provides a secure, stateful execution environment for RLM inference by colocating the RLM inference service with a WASM manager in the same Kubernetes pod. This pattern ensures:

- ✅ **State persistence** across multiple code executions
- ✅ **Complete isolation** between RLM and execution environments
- ✅ **Low latency** communication (localhost within pod)
- ✅ **Scalable** session management
- ✅ **Secure** sandboxed execution

## Architecture Diagram

```
┌─────────────────────────────────────────────────────────────────┐
│                      KUBERNETES POD                             │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │                                                         │   │
│  │  ┌─────────────────────────────────────────────────┐    │   │
│  │  │              RLM Inference (Container 1)        │    │   │
│  │  │                                                 │    │   │
│  │  │  • LLM Model                                    │    │   │
│  │  │  • Code Generation                              │    │   │
│  │  │  • Concurrent Sessions (Session IDs)            │    │   │
│  │  │  • REPL Factory (Local to Pod)                  │    │   │
│  │  └─────────────────────────────────────────────────┘    │   │
│  │                         │                               │    │   │
│  │                         ▼ (localhost:8080)              │    │   │
│  │  ┌─────────────────────────────────────────────────┐    │   │
│  │  │           WASM Manager (Container 2)            │    │   │
│  │  │                                                 │    │   │
│  │  │  • Session Management                           │    │   │
│  │  │  • Multiple WASM Runtime Instances              │    │   │
│  │  │  • State Persistence per Session                │    │   │
│  │  │  • Pyodide Sandboxes (1 per RLM session)        │    │   │
│  │  │                                                 │    │   │
│  │  │  ┌──────────┐ ┌──────────┐ ┌──────────┐        │    │   │
│  │  │  │ Session  │ │ Session  │ │ Session  │        │    │   │
│  │  │  │ WASM #1  │ │ WASM #2  │ │ WASM #N  │        │    │   │
│  │  │  └──────────┘ └──────────┘ └──────────┘        │    │   │
│  │  └─────────────────────────────────────────────────┘    │   │
│  │                                                         │   │
│  └─────────────────────────────────────────────────────────┘   │
│                          │                                     │
│                          ▼                                     │
│              Network Policy (Pod-level)                        │
└─────────────────────────────────────────────────────────────────┘
```

## Components

### 1. RLM Inference Container

**Image:** `rlm-inference:latest`
**Port:** 8000
**Responsibilities:**
- LLM model execution
- Code generation during reasoning
- Session management
- REPL factory for creating sidecar connections
- HTTP API for inference requests

### 2. WASM Manager Container

**Image:** `wasm-manager:latest`
**Port:** 8080
**Responsibilities:**
- Session management
- Multiple isolated WASM runtimes
- State persistence per session
- Pyodide sandbox execution
- HTTP API for session operations

## Communication Flow

1. **RLM Inference** generates code during reasoning
2. **SidecarREPLFactory** creates a SidecarREPLEnv
3. **SidecarREPLEnv** initializes:
   - Creates new WASM session via `POST /session`
   - Gets session ID from response
4. **RLM** sends code to execute:
   ```python
   # Example:
   result = repl_env.code_execution("x = 42")
   ```
5. **SidecarREPLEnv** sends to WASM Manager:
   ```python
   # Internally:
   response = requests.post(
       "http://localhost:8080/session/{session_id}/execute",
       json={"code": "x = 42"}
   )
   ```
6. **WASM Manager** executes in isolated Pyodide runtime
7. **Result** returned to RLM
8. **State persists** for subsequent executions in same session
9. **Cleanup** when RLM completes:
   ```python
   await repl_env.cleanup()  # Deletes session
   ```

## Deployment

### Kubernetes Deployment

```bash
# Apply sidecar deployment
kubectl apply -f deploy/k8s/rlm-sidecar-deployment.yaml

# Check pods
kubectl get pods -l app=rlm,component=sidecar

# Check services
kubectl get services -l app=rlm,component=sidecar
```

### Docker Build

```bash
# Build RLM inference image
docker build -t rlm-inference:latest -f deploy/docker/Dockerfile.rlm-sidecar .

# Build WASM manager image
docker build -t wasm-manager:latest -f deploy/docker/Dockerfile.wasm-manager .
```

## Configuration

### Environment Variables

**RLM Inference Container:**
- `WASM_MANAGER_SERVICE_URL`: `http://localhost:8080` (fixed for sidecar)
- `MODEL_PATH`: Path to LLM models
- `LOG_LEVEL`: Logging level (INFO, DEBUG)

**WASM Manager Container:**
- `PYODIDE_URL`: Pyodide CDN URL
- `MAX_SESSIONS`: Maximum concurrent sessions
- `SESSION_TTL`: Session time-to-live (seconds)
- `LOG_LEVEL`: Logging level

### Kubernetes Resources

- **CPU:** RLM (1-2 cores), WASM Manager (500m-1 core)
- **Memory:** RLM (2-4Gi), WASM Manager (1-2Gi)
- **Storage:** 10Gi for models (PersistentVolumeClaim)

## Usage

### Basic Usage

```python
from rlm.remote import create_sidecar_repl_factory
from rlm.local.rlm_repl import RLM_REPL

# Create sidecar REPL factory
factory = create_sidecar_repl_factory()

# Create RLM with sidecar factory
rlm = RLM_REPL(
    model="gpt-5",
    max_depth=2,
    enable_logging=True,
    repl_factory=factory
)

# Run inference
result = rlm.completion(
    context="Calculate the Fibonacci sequence up to 10 terms",
    query="What is the 8th Fibonacci number?"
)
```

### State Persistence Example

```python
import asyncio
from rlm.remote import create_sidecar_repl_factory

async def test_state():
    factory = create_sidecar_repl_factory()
    
    # Create session
    session_id = await factory.create_session()
    
    try:
        # Step 1: Define variable
        await factory.execute_in_session(session_id, "x = 42")
        
        # Step 2: Use variable (persists!)
        result = await factory.execute_in_session(session_id, "x * 2")
        print(f"Result: {result}")  # Output: 84
        
        # Step 3: Modify variable
        await factory.execute_in_session(session_id, "x = x + 10")
        
        # Step 4: Verify change (persists!)
        result = await factory.execute_in_session(session_id, "x")
        print(f"New x: {result}")  # Output: 52
    
    finally:
        # Cleanup session
        await factory.delete_session(session_id)

# Run
asyncio.run(test_state())
```

## Monitoring

### Metrics

**RLM Inference Container:**
- `rlm_inference_requests_total`: Total inference requests
- `rlm_inference_duration_seconds`: Inference duration histogram
- `rlm_code_generated_total`: Total code generation events

**WASM Manager Container:**
- `wasm_sessions_active`: Active sessions count
- `wasm_execution_duration_seconds`: Execution duration histogram
- `wasm_execution_errors_total`: Execution errors count

### Logging

```yaml
# Example log aggregation
apiVersion: v1
kind: ConfigMap
metadata:
  name: rlm-sidecar-log-config
data:
  logstash.conf: |
    input {
      kubernetes {
        container => "rlm-inference"
      }
      kubernetes {
        container => "wasm-manager"
      }
    }
```

## Troubleshooting

### Common Issues

| Issue | Cause | Solution |
|-------|-------|----------|
| Session creation fails | WASM manager not ready | Check container health: `kubectl exec <pod> -c wasm-manager -- curl http://localhost:8080/health` |
| High latency | Resource constraints | Increase CPU/memory limits in deployment |
| Session timeout | Session TTL expired | Increase `SESSION_TTL` environment variable |
| Connection refused | Port mismatch | Verify WASM manager is listening on port 8080 |

### Debug Commands

```bash
# Check pod status
kubectl describe pod <pod-name>

# Check logs from both containers
kubectl logs <pod-name> -c rlm-inference
kubectl logs <pod-name> -c wasm-manager

# Exec into containers
kubectl exec -it <pod-name> -c rlm-inference -- bash
kubectl exec -it <pod-name> -c wasm-manager -- bash

# Test WASM manager API
kubectl exec <pod-name> -c rlm-inference -- curl http://localhost:8080/health
```

## Security

### Network Policies

```yaml
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata:
  name: rlm-sidecar-network-policy
spec:
  podSelector:
    matchLabels:
      app: rlm
      component: sidecar
  policyTypes:
  - Ingress
  - Egress
  ingress:
  - from:
    - ipBlock:
        cidr: 10.0.0.0/8
    ports:
    - protocol: TCP
      port: 8000
  egress:
  - to:
    - ipBlock:
        cidr: 0.0.0.0/0
    ports:
    - protocol: TCP
      port: 443
```

### Pod Security Policies

```yaml
apiVersion: policy/v1beta1
kind: PodSecurityPolicy
metadata:
  name: rlm-sidecar-psp
spec:
  privileged: false
  allowPrivilegeEscalation: false
  requiredDropCapabilities:
  - ALL
  volumes:
  - 'emptyDir'
  - 'secret'
  runAsUser:
    rule: 'MustRunAsNonRoot'
  seLinux:
    rule: 'RunAsAny'
```

## References

- [Main RLM Architecture Guide](/Users/rexsasori/rlm-minimal/rlm/ARCHITECTURE_GUIDE.md)
- [Deployment Guide](DEPLOYMENT_GUIDE.md)
- [Kubernetes Sidecar Pattern](https://kubernetes.io/docs/concepts/workloads/pods/)
- [Pyodide Documentation](https://pyodide.org/)
