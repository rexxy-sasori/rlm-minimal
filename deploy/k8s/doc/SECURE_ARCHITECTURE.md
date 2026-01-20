# Secure Architecture for RLM with WASM Code Execution

> **Note:** This is Architecture 3 (Different-Pod Execution) in the [main RLM Architecture Guide](/Users/rexsasori/rlm-minimal/rlm/ARCHITECTURE_GUIDE.md). Refer to the main guide for architecture comparison, pros/cons, and use cases.

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
          app: rlm
    ports:
    - protocol: TCP
      port: 8000
```

```yaml
# Network policy for RLM service
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata:
  name: rlm-network-policy
spec:
  podSelector:
    matchLabels:
      app: rlm
  policyTypes:
  - Ingress
  - Egress
  ingress:
  - from:
    - ipBlock:
        cidr: 0.0.0.0/0
    ports:
    - protocol: TCP
      port: 8000
  egress:
  - to:
    - podSelector:
        matchLabels:
          app: wasm-repl
    ports:
    - protocol: TCP
      port: 8000
  - to:
    - ipBlock:
        cidr: 0.0.0.0/0
    ports:
    - protocol: TCP
      port: 443
```

### Resource Limits

```yaml
# RLM inference pod resources
resources:
  requests:
    memory: "2Gi"
    cpu: "1000m"
  limits:
    memory: "4Gi"
    cpu: "2000m"
```

```yaml
# WASM execution pod resources
resources:
  requests:
    memory: "1Gi"
    cpu: "500m"
  limits:
    memory: "2Gi"
    cpu: "1000m"
```

### Pod Security Policy

```yaml
apiVersion: policy/v1beta1
kind: PodSecurityPolicy
metadata:
  name: rlm-secure-psp
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
  supplementalGroups:
    rule: 'MustRunAs'
    ranges:
    - min: 1
      max: 65535
  fsGroup:
    rule: 'MustRunAs'
    ranges:
    - min: 1
      max: 65535
```

## Defense in Depth

| Security Layer | Implementation |
|----------------|----------------|
| **1. Network** | Kubernetes Network Policies |
| **2. Pod** | Isolated deployments, PSP |
| **3. Container** | Non-root user, read-only filesystem |
| **4. Runtime** | WASM sandbox (Pyodide) |
| **5. Application** | API authentication, rate limiting |
| **6. Code** | Input validation, output sanitization |

## Deployment

### Prerequisites

- Kubernetes cluster (v1.19+)
- kubectl configured
- Container registry access
- LLM API key

### Deployment Steps

```bash
# 1. Create namespace
kubectl create namespace rlm

# 2. Create secrets
kubectl create secret generic rlm-secrets -n rlm \
  --from-literal=llm-api-key="your-key"

# 3. Deploy RLM inference
kubectl apply -n rlm -f k8s/rlm-deployment.yaml
kubectl apply -n rlm -f k8s/rlm-service.yaml

# 4. Deploy WASM execution
kubectl apply -n rlm -f k8s/wasm-repl-deployment.yaml
kubectl apply -n rlm -f k8s/wasm-repl-service.yaml

# 5. Apply network policies
kubectl apply -n rlm -f k8s/network-policies.yaml

# 6. Verify deployment
kubectl get pods -n rlm
kubectl get services -n rlm
```

## Monitoring & Observability

### Prometheus Metrics

```yaml
# Example ServiceMonitor for RLM
apiVersion: monitoring.coreos.com/v1
kind: ServiceMonitor
metadata:
  name: rlm-monitor
spec:
  selector:
    matchLabels:
      app: rlm
  endpoints:
  - port: http
    path: /metrics
```

### Logging

```yaml
# Example Fluentd configuration
apiVersion: v1
kind: ConfigMap
metadata:
  name: rlm-log-config
data:
  fluentd.conf: |
    <source>
      @type tail
      path /var/log/containers/*rlm*.log
      tag kubernetes.rlm
      <parse>
        @type json
      </parse>
    </source>
```

## Compliance Considerations

### Data Protection

- ✅ LLM API keys never exposed to execution plane
- ✅ No sensitive data in WASM sandbox
- ✅ Audit logging for all code execution
- ✅ Encryption in transit (TLS)

### Access Control

- ✅ RBAC for Kubernetes resources
- ✅ Network policies restrict traffic
- ✅ API authentication for external access
- ✅ Principle of least privilege

## References

- [Main RLM Architecture Guide](/Users/rexsasori/rlm-minimal/rlm/ARCHITECTURE_GUIDE.md)
- [Kubernetes Network Policies](https://kubernetes.io/docs/concepts/services-networking/network-policies/)
- [Pyodide Documentation](https://pyodide.org/)
- [Pod Security Policies](https://kubernetes.io/docs/concepts/policy/pod-security-policy/)
- [Deployment Guide](/Users/rexsasori/rlm-minimal/deploy/docs/DEPLOYMENT_GUIDE.md)
- [WASM Quickstart](/Users/rexsasori/rlm-minimal/deploy/docs/WASM_QUICKSTART.md)
