# RLM Architecture Guide

RLM supports three distinct architectures for executing generated code during inference, each with different security, performance, and deployment characteristics.

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

## Architecture Comparison

| Feature | Local (Architecture 1) | Same-Pod (Architecture 2) | Different-Pod (Architecture 3) |
|---------|------------------------|---------------------------|--------------------------------|
| **Code Execution** | Same process | Sidecar container | Remote service |
| **Isolation** | None | Container-level | Pod-level + network |
| **Security** | Low | Medium | High |
| **Latency** | Low | Very Low | Medium |
| **State Persistence** | Yes (in-memory) | Yes (session-based) | No (stateless) |
| **Deployment Complexity** | None | Low | Medium |
| **Scalability** | N/A | Pod-level | Independent scaling |
| **Use Case** | Development/Testing | Production (single-tenant) | Production (multi-tenant) |

---

## Architecture 1: Local Execution (Default)

**Code execution and RLM_REPL run in the same process.**

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
- ✅ State persistence across execution

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
- Quick prototyping

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

---

## Architecture 2: Same-Pod (Sidecar) Execution

**Code execution (in WASM) and RLM_REPL run in the same pod but different containers.**

### How It Works

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

### Components

#### 1. RLM Inference Container
- **Image**: `rlm-inference:latest`
- **Port**: 8000
- **Responsibilities**:
  - LLM model execution
  - Code generation during reasoning
  - Session management
  - REPL factory for creating sidecar connections
  - HTTP API for inference requests

#### 2. WASM Manager Container
- **Image**: `wasm-manager:latest`
- **Port**: 8080
- **Responsibilities**:
  - Session management
  - Multiple isolated WASM runtimes
  - State persistence per session
  - Pyodide sandbox execution
  - HTTP API for session operations

### Data Flow

1. **RLM Inference** generates code during reasoning
2. **SidecarREPLFactory** creates a SidecarREPLEnv
3. **SidecarREPLEnv** initializes:
   - Creates new WASM session via `POST /session`
   - Gets session ID from response
4. **RLM** sends code to execute via `POST /session/{session_id}/execute`
5. **WASM Manager** executes in isolated Pyodide runtime
6. **Result** returned to RLM
7. **State persists** for subsequent executions in same session
8. **Cleanup** when RLM completes via `DELETE /session/{session_id}`

### Pros
- ✅ Good security - container isolation
- ✅ LLM API keys never exposed to execution plane
- ✅ Very low latency - localhost communication
- ✅ State persistence per session
- ✅ Resource isolation - no contention
- ✅ Simpler deployment than different-pod

### Cons
- ❌ Requires Kubernetes deployment
- ❌ Pod-level scaling (both containers scale together)
- ❌ More complex than local execution

### Use Cases
- Production deployment (single-tenant)
- Lower-latency requirements
- Session-based applications
- Kubernetes-based infrastructure
- Medium-security requirements

### Files
- `deploy/docs/SIDECAR_ARCHITECTURE_GUIDE.md` - Detailed sidecar guide
- `k8s/rlm-sidecar-deployment.yaml` - Kubernetes deployment
- `rlm/remote/repl_sidecar.py` - Sidecar REPL client

---

## Architecture 3: Different-Pod (Remote) Execution

**Code execution (in WASM) and RLM_REPL run in truly remote pods.**

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

### Components

#### 1. RLM Inference Plane
- **Deployment**: `k8s/rlm-deployment.yaml`
- **Responsibilities**:
  - LLM API calls (OpenAI or compatible)
  - Prompt engineering and context management
  - Code generation (NOT execution)
  - Orchestration of recursive calls
  - Communication with WASM service
- **Security**:
  - Has access to LLM API keys
  - No code execution capability
  - Network policy: only egress to WASM service and LLM API

#### 2. WASM Execution Plane
- **Deployment**: `k8s/wasm-repl-deployment.yaml`
- **Responsibilities**:
  - Receive code for execution via HTTP API
  - Execute code in Pyodide WASM sandbox
  - Return results (stdout, stderr, variables)
  - Enforce resource limits and timeouts
- **Security**:
  - Isolated WASM sandbox
  - NO access to LLM API keys
  - NO access to sensitive data
  - Resource quotas per execution
  - Network policy: only ingress from RLM service

### Pros
- ✅ Maximum security - complete isolation
- ✅ LLM API keys never exposed to execution plane
- ✅ Resource isolation - no contention
- ✅ Scalable - scale RLM and WASM independently
- ✅ Production-ready - suitable for untrusted code
- ✅ Defense in depth - multiple security layers
- ✅ Multi-tenant capable

### Cons
- ❌ More complex setup - requires k8s deployment
- ❌ Network latency - HTTP communication overhead
- ❌ Additional infrastructure - WASM service required
- ❌ Stateless (no session persistence)

### Use Cases
- Production deployment (multi-tenant)
- Executing untrusted code
- High-security requirements
- Kubernetes-based infrastructure
- Independent scaling needs
- Enterprise deployments

### Usage Example

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

### Files
- `deploy/docs/SECURE_WASM_ARCHITECTURE_SUMMARY.md` - Architecture summary
- `k8s/doc/SECURE_ARCHITECTURE.md` - Detailed security guide
- `k8s/rlm-deployment.yaml` - RLM inference deployment
- `k8s/wasm-repl-deployment.yaml` - WASM execution deployment
- `rlm/remote/repl_remote.py` - Remote REPL client
- `rlm/wasm/repl_wasm_service.py` - WASM HTTP service

---

## Architecture Selection Guide

| Requirement | Recommended Architecture |
|-------------|--------------------------|
| Development / Testing | Local (Architecture 1) |
| Quick prototyping | Local (Architecture 1) |
| Lowest latency | Same-Pod (Architecture 2) |
| Session persistence | Same-Pod (Architecture 2) |
| Multi-tenant | Different-Pod (Architecture 3) |
| Highest security | Different-Pod (Architecture 3) |
| Independent scaling | Different-Pod (Architecture 3) |
| Enterprise production | Different-Pod (Architecture 3) |
| Single-tenant production | Same-Pod (Architecture 2) |

---

## Migration Path

```
Local (Architecture 1)
    │
    └───> Same-Pod (Architecture 2)
              │
              └───> Different-Pod (Architecture 3)
```

Start with local execution for development, then migrate to same-pod for production, and finally to different-pod for enterprise-scale deployments.

---

## Related Documentation

- `deploy/docs/DEPLOYMENT_GUIDE.md` - Deployment instructions
- `deploy/docs/WASM_QUICKSTART.md` - WASM quickstart guide
- `k8s/doc/WASM_REPL_SETUP.md` - WASM REPL setup
- `doc/DEPTH_IMPLEMENTATION.md` - Depth implementation details
