# Sidecar Architecture Guide for RLM

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
        await factory.destroy_session(session_id)

# Run test
asyncio.run(test_state())
```

## API Endpoints

### WASM Manager API

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/session` | POST | Create new WASM session |
| `/session/{session_id}/execute` | POST | Execute code in session |
| `/session/{session_id}` | DELETE | Destroy session |
| `/sessions` | GET | List active sessions |
| `/sessions` | DELETE | Cleanup all sessions |

### RLM Inference API

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/infer` | POST | Run RLM inference |
| `/health` | GET | Health check |
| `/ready` | GET | Readiness check |

## Security

### Network Policies

- **Ingress:** Only allow access to RLM API from authorized services
- **Egress:** RLM can only communicate with WASM Manager on localhost
- **WASM Manager:** Only accepts requests from localhost (RLM)

### Sandboxing

- **Pyodide Runtime:** Isolated Python execution
- **No Filesystem Access:** WASM cannot access host files
- **No Network Access:** WASM cannot make network requests
- **Memory Limits:** Each WASM instance has memory limits
- **Execution Timeouts:** Prevent infinite loops

## Performance

### Latency Comparison

| Operation | Local Execution | Remote WASM | Sidecar WASM |
|-----------|----------------|-------------|--------------|
| Session Creation | <1ms | 50-100ms | <10ms |
| Code Execution | <1ms | 100-200ms | 10-30ms |
| Session Cleanup | <1ms | 50-100ms | <10ms |

### Scalability

- **Horizontal Scaling:** Deploy multiple pods for increased throughput
- **Session Isolation:** Each pod manages its own sessions
- **Resource Efficiency:** WASM runtimes share memory where possible

## Troubleshooting

### Common Issues

| Issue | Possible Cause | Solution |
|-------|----------------|----------|
| Session not found | Session expired or cleaned up | Create new session |
| Pyodide loading failed | Network issue | Check internet access in pod |
| Memory limit exceeded | Too many concurrent sessions | Increase WASM Manager memory |
| Execution timeout | Infinite loop in code | Set shorter timeouts |

### Logging

```bash
# Check RLM logs
kubectl logs <pod-name> -c rlm-inference

# Check WASM Manager logs
kubectl logs <pod-name> -c wasm-manager
```

### Debugging

```bash
# Port forward to RLM API
kubectl port-forward <pod-name> 8000:8000

# Port forward to WASM Manager
kubectl port-forward <pod-name> 8080:8080

# Test WASM Manager directly
curl -X POST http://localhost:8080/session
curl -X POST http://localhost:8080/session/{session_id}/execute -d '{"code": "1 + 1"}'
```

## Best Practices

1. **Use sidecar pattern** for production deployments
2. **Set appropriate resource limits** based on expected load
3. **Monitor session counts** to avoid resource exhaustion
4. **Implement proper cleanup** to avoid orphaned sessions
5. **Use network policies** to restrict access
6. **Rotate sessions** periodically for security
7. **Test with realistic workloads** before production

## Conclusion

The sidecar architecture provides an optimal balance of:
- **Security** (isolated execution)
- **Performance** (low latency)
- **Functionality** (state persistence)
- **Scalability** (session management)

This pattern is recommended for production deployments where secure, stateful code execution is required during RLM inference.

## References

- [Kubernetes Sidecar Pattern](https://kubernetes.io/docs/concepts/workloads/pods/#workload-resources-for-managing-pods)
- [Pyodide Documentation](https://pyodide.org/en/stable/)
- [FastAPI Documentation](https://fastapi.tiangolo.com/)
- [RLM Architecture Guide](../rlm/ARCHITECTURE_GUIDE.md)
