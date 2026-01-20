# Secure Architecture for RLM with WASM Code Execution

## Problem Statement

During RLM inference, the LLM generates Python code that needs to be executed. This creates a security risk:
- Arbitrary code execution in the same pod as LLM inference
- Potential data exfiltration or pod compromise
- Resource exhaustion from malicious code

## Solution: Separate Execution Plane

The secure architecture separates **LLM inference** from **code execution** into distinct components:

```
┌─────────────────────────────────────────────────────────────────┐
│                     Kubernetes Cluster                          │
│                                                                 │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │              RLM Inference Deployment                    │   │
│  │  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐     │   │
│  │  │  RLM Pod 1  │  │  RLM Pod 2  │  │  RLM Pod 3  │     │   │
│  │  │  (LLM +     │  │  (LLM +     │  │  (LLM +     │     │   │
│  │  │   Logic)    │  │   Logic)    │  │   Logic)    │     │   │
│  │  └─────────────┘  └─────────────┘  └─────────────┘     │   │
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

Traffic Flow:
1. User sends query to RLM Inference Service
2. LLM generates Python code
3. RLM sends code to WASM Execution Service (HTTP API)
4. WASM service executes code in sandbox
5. Results returned to RLM
6. RLM continues inference or returns final answer
```

## Architecture Components

### 1. RLM Inference Plane

**Location**: Separate deployment (`k8s/rlm-deployment.yaml`)

**Responsibilities**:
- LLM API calls (OpenAI or compatible)
- Prompt engineering and context management
- Recursive logic orchestration
- Code generation (but NOT execution)
- Communication with WASM execution service

**Security**: 
- No code execution capability
- Minimal permissions
- Network policy: only egress to LLM API and WASM service

### 2. WASM Execution Plane

**Location**: Separate deployment (`k8s/wasm-repl-deployment.yaml`)

**Responsibilities**:
- Receive code for execution via HTTP API
- Execute code in Pyodide WASM sandbox
- Return results (stdout, stderr, variables)
- Enforce resource limits and timeouts

**Security**:
- Isolated WASM sandbox
- No access to LLM API keys
- No access to sensitive data
- Resource quotas per execution
- Network policy: only ingress from RLM service

## Security Features

### Network Isolation

```yaml
# Network policy for WASM service
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata:
  name: wasm-repl-network-policy
spec:
  podSelector:
    matchLabels:
      app: wasm-repl
  policyTypes:
  - Ingress
  ingress:
  - from:
    - podSelector:
        matchLabels:
          app: rlm-inference
    ports:
    - protocol: TCP
      port: 8000
```

### Resource Isolation

```yaml
# Per-pod resource limits
resources:
  requests:
    memory: "512Mi"
    cpu: "500m"
  limits:
    memory: "1Gi"
    cpu: "1000m"
```

### Per-Execution Limits

```python
# In wasm executor
timeout: 30 seconds  # Max execution time
memory_limit: 256Mi  # Max memory per execution
cpu_shares: 256      # CPU allocation
```

### Secrets Management

- **LLM API Keys**: Only in RLM inference pods (k8s Secret)
- **WASM Service**: No access to LLM keys
- **Communication**: mTLS between RLM and WASM service (optional)

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
    │ 1. Generate code                            │
    │                                            │
    ▼                                            │
┌──────────────────┐                             │
│  Code Generated  │                             │
└──────────────────┘                             │
    │                                            │
    │ 2. Send to WASM Service                    │
    │                                            │
    ▼                                            │
┌──────────────────┐                             │
│  HTTP Request    │                             │
│  POST /execute   │                             │
└──────────────────┘                             │
    │                                            │
    ▼                                            │
┌─────────────┐                                  │
│ WASM Pod    │  3. Execute in sandbox           │
│ (Sandbox)   │                                  │
└─────────────┘                                  │
    │                                            │
    │ 4. Return results                          │
    │                                            │
    ▼                                            │
┌──────────────────┐                             │
│  HTTP Response   │                             │
│  {stdout, stderr,│                             │
│   locals, time}  │                             │
└──────────────────┘                             │
    │                                            │
    ▼                                            │
┌─────────────┐                                  │
│  RLM Pod    │ ◄────────────────────────────────┘
│  (Inference)│  5. Continue inference
└─────────────┘
    │
    │ 6. Final answer
    ▼
User Response
```

## Deployment Strategy

### Step 1: Deploy WASM Execution Service

```bash
# Create secrets (if needed for WASM service)
kubectl create secret generic wasm-secrets \
  --from-literal=api-key="internal-key"

# Deploy WASM service
kubectl apply -f k8s/wasm-repl-deployment.yaml

# Verify
kubectl get pods -l app=wasm-repl
```

### Step 2: Deploy RLM Inference Service

```bash
# Create LLM API key secret
kubectl create secret generic llm-secrets \
  --from-literal=api-key="your-llm-key"

# Deploy RLM
kubectl apply -f k8s/rlm-deployment.yaml

# Verify
kubectl get pods -l app=rlm-inference
```

### Step 3: Configure Network Policies

```bash
# Apply network isolation
kubectl apply -f k8s/network-policies.yaml
```

## Implementation Changes

### Update RLM to Use Remote Execution

```python
# rlm/repl.py - Replace local execution with remote

class RemoteREPLEnv:
    """REPL environment that uses remote WASM service."""
    
    def __init__(self, wasm_service_url: str):
        self.wasm_service_url = wasm_service_url
        self.session_id = uuid.uuid4().hex
    
    def code_execution(self, code: str) -> REPLResult:
        """Execute code remotely via HTTP."""
        import requests
        
        response = requests.post(
            f"{self.wasm_service_url}/execute",
            json={
                "code": code,
                "session_id": self.session_id,
                "timeout": 30
            },
            timeout=35
        )
        
        result = response.json()
        return REPLResult(
            stdout=result.get('stdout', ''),
            stderr=result.get('stderr', ''),
            locals=result.get('locals', {}),
            execution_time=result.get('execution_time', 0)
        )
```

### Update RLM_REPL Configuration

```python
# rlm/rlm_repl.py - Use remote execution

class RLM_REPL(RLM):
    
    def __init__(self, wasm_service_url: Optional[str] = None, **kwargs):
        self.wasm_service_url = wasm_service_url or os.getenv(
            'WASM_SERVICE_URL', 'http://wasm-repl-service:8000'
        )
        super().__init__(**kwargs)
    
    def setup_context(self, context, query=None):
        # Use remote REPL instead of local
        self.repl_env = RemoteREPLEnv(self.wasm_service_url)
        # ... rest of setup
```

## Scaling Considerations

### Horizontal Scaling

Both components scale independently:

```bash
# Scale RLM inference (handles more concurrent queries)
kubectl scale deployment rlm-inference --replicas=10

# Scale WASM execution (handles more code execution)
kubectl scale deployment wasm-repl --replicas=20
```

### Autoscaling

```yaml
# HPA for RLM (based on CPU)
apiVersion: autoscaling/v2
kind: HorizontalPodAutoscaler
metadata:
  name: rlm-hpa
spec:
  scaleTargetRef:
    apiVersion: apps/v1
    kind: Deployment
    name: rlm-inference
  minReplicas: 3
  maxReplicas: 20
  metrics:
  - type: Resource
    resource:
      name: cpu
      target:
        type: Utilization
        averageUtilization: 70

# HPA for WASM (based on CPU and queue length)
apiVersion: autoscaling/v2
kind: HorizontalPodAutoscaler
metadata:
  name: wasm-hpa
spec:
  scaleTargetRef:
    apiVersion: apps/v1
    kind: Deployment
    name: wasm-repl
  minReplicas: 5
  maxReplicas: 50
  metrics:
  - type: Resource
    resource:
      name: cpu
      target:
        type: Utilization
        averageUtilization: 60
```

## Monitoring and Observability

### Metrics to Track

```
# RLM Inference Metrics
rlm_inference_requests_total
rlm_inference_duration_seconds
rlm_code_generated_total
rlm_code_execution_requests_total

# WASM Execution Metrics
wasm_execution_requests_total
wasm_execution_duration_seconds
wasm_execution_errors_total
wasm_execution_timeout_total
wasm_memory_usage_bytes
wasm_cpu_usage_seconds
```

### Logging

```yaml
# Structured logging configuration
apiVersion: v1
kind: ConfigMap
metadata:
  name: logging-config
data:
  log-level: "INFO"
  log-format: "json"
```

## Disaster Recovery

### Backup Strategy

- No persistent state in WASM pods (stateless)
- RLM inference can be restarted from scratch
- Use k8s rolling updates for zero downtime deployments

### High Availability

```yaml
# Multiple replicas for redundancy
replicas: 3

# Pod disruption budget
apiVersion: policy/v1
kind: PodDisruptionBudget
metadata:
  name: rlm-pdb
spec:
  minAvailable: 2
  selector:
    matchLabels:
      app: rlm-inference
```

## Security Checklist

- [ ] LLM API keys stored in k8s Secrets
- [ ] WASM service has no access to LLM keys
- [ ] Network policies restrict traffic flow
- [ ] Resource limits set on all pods
- [ ] WASM sandbox enabled for code execution
- [ ] Per-execution timeouts enforced
- [ ] No privileged containers
- [ ] Non-root users for all containers
- [ ] Regular security updates for base images
- [ ] Audit logging enabled

## Performance Optimization

1. **Connection Pooling**: Reuse HTTP connections between RLM and WASM
2. **Request Batching**: Batch multiple code executions when possible
3. **Caching**: Cache frequent code patterns
4. **Pre-warming**: Keep WASM instances ready
5. **Load Balancing**: Distribute requests evenly
6. **Proximity**: Deploy RLM and WASM in same AZ for low latency

## Cost Considerations

- **WASM Pods**: Lower cost than RLM pods (no GPU, less memory)
- **Scaling**: Scale WASM independently based on code execution needs
- **Spot Instances**: Use spot instances for WASM execution (stateless)
- **Idle Scaling**: Scale down WASM replicas during low traffic

## Conclusion

This architecture provides:

✅ **Security**: Complete isolation between LLM inference and code execution
✅ **Scalability**: Independent scaling of each component
✅ **Reliability**: Stateless design with redundancy
✅ **Observability**: Comprehensive metrics and logging
✅ **Maintainability**: Clear separation of concerns

The separate execution plane ensures that even if the WASM service is compromised, the LLM API keys and sensitive data remain protected.
