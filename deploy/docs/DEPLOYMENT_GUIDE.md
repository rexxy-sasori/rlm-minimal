# Secure RLM Deployment Guide with WASM Execution Plane

This guide explains how to deploy RLM with a secure, isolated WASM execution plane in Kubernetes.

## Architecture Overview

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

## Key Security Features

1. **Separate Components**: LLM inference and code execution run in separate pods
2. **Network Isolation**: Network policies restrict traffic between components
3. **Resource Limits**: CPU/memory limits prevent resource exhaustion
4. **WASM Sandbox**: Code executes in isolated Pyodide environment
5. **Secrets Management**: Sensitive data stored in k8s Secrets
6. **Non-Root Users**: Containers run as non-root users

## Prerequisites

- Kubernetes cluster (v1.21+)
- kubectl configured
- Docker or container runtime
- LLM API key (OpenAI or compatible)
- Domain name (optional, for Ingress)

## Deployment Steps

### Step 1: Build Docker Images

#### Build WASM Execution Image

```bash
docker build -f deploy/docker/Dockerfile.wasm-repl -t rlm-minimal-wasm:latest .
```

#### Build RLM Inference Image

```bash
docker build -f Dockerfile.rlm -t rlm-minimal:latest .
```

#### (Optional) Push to Registry

```bash
docker tag rlm-minimal:latest your-registry/rlm-minimal:latest
docker tag rlm-minimal-wasm:latest your-registry/rlm-minimal-wasm:latest

docker push your-registry/rlm-minimal:latest
docker push your-registry/rlm-minimal-wasm:latest
```

### Step 2: Create Secrets

#### Create LLM API Key Secret

```bash
kubectl create secret generic llm-secrets \
  --from-literal=api-key="your-actual-llm-api-key"
```

### Step 3: Deploy WASM Execution Service

```bash
# Deploy WASM service
kubectl apply -f k8s/wasm-repl-deployment.yaml

# Verify deployment
kubectl get pods -l app=wasm-repl
kubectl get service wasm-repl-service

# Check logs
kubectl logs -l app=wasm-repl -f
```

### Step 4: Deploy RLM Inference Service

```bash
# Deploy RLM inference
kubectl apply -f k8s/rlm-deployment.yaml

# Verify deployment
kubectl get pods -l app=rlm-inference
kubectl get service rlm-inference-service

# Check logs
kubectl logs -l app=rlm-inference -f
```

### Step 5: Apply Network Policies

```bash
# Apply network isolation
kubectl apply -f k8s/network-policies.yaml

# Verify network policies
kubectl get networkpolicy
```

### Step 6: Test the Deployment

#### Test WASM Service

```bash
# Get WASM service IP
WASM_IP=$(kubectl get service wasm-repl-service -o jsonpath='{.status.loadBalancer.ingress[0].ip}')

# Test code execution
curl -X POST http://$WASM_IP/execute \
  -H "Content-Type: application/json" \
  -d '{
    "code": "print(\"Hello from WASM!\")\nx = 42 + 10\nprint(f\"Result: {x}\")",
    "context": {},
    "timeout": 30
  }'
```

#### Test RLM Inference

```bash
# Get RLM service IP
RLM_IP=$(kubectl get service rlm-inference-service -o jsonpath='{.status.loadBalancer.ingress[0].ip}')

# Test inference
curl -X POST http://$RLM_IP/infer \
  -H "Content-Type: application/json" \
  -d '{
    "query": "What is 42 + 10?",
    "context": "You are a helpful assistant that can execute Python code.",
    "model": "gpt-5",
    "max_depth": 2
  }'
```

## Configuration

### Environment Variables

#### RLM Inference Pods

| Variable | Description | Default |
|----------|-------------|--------|
| `LLM_API_KEY` | Your LLM API key | (from secret) |
| `LLM_BASE_URL` | LLM API base URL | https://api.openai.com/v1 |
| `LLM_MODEL` | Default LLM model | gpt-5 |
| `WASM_SERVICE_URL` | WASM service URL | http://wasm-repl-service:8000 |
| `MAX_DEPTH` | Max recursion depth | 3 |
| `MAX_ITERATIONS` | Max iterations | 20 |
| `EXECUTION_TIMEOUT` | Code timeout (seconds) | 30 |

#### WASM Execution Pods

| Variable | Description | Default |
|----------|-------------|--------|
| `MAX_DEPTH` | Max recursion depth | 3 |
| `EXECUTION_TIMEOUT` | Code timeout (seconds) | 30 |

### Resource Configuration

Edit resource limits in deployment files:

```yaml
resources:
  requests:
    memory: "1Gi"
    cpu: "1000m"
  limits:
    memory: "2Gi"
    cpu: "2000m"
```

## Scaling

### Manual Scaling

```bash
# Scale RLM inference
kubectl scale deployment rlm-inference-deployment --replicas=10

# Scale WASM execution
kubectl scale deployment wasm-repl-deployment --replicas=20
```

### Autoscaling

Create Horizontal Pod Autoscalers:

```yaml
# k8s/rlm-hpa.yaml
apiVersion: autoscaling/v2
kind: HorizontalPodAutoscaler
metadata:
  name: rlm-hpa
spec:
  scaleTargetRef:
    apiVersion: apps/v1
    kind: Deployment
    name: rlm-inference-deployment
  minReplicas: 3
  maxReplicas: 20
  metrics:
  - type: Resource
    resource:
      name: cpu
      target:
        type: Utilization
        averageUtilization: 70
```

```yaml
# k8s/wasm-hpa.yaml
apiVersion: autoscaling/v2
kind: HorizontalPodAutoscaler
metadata:
  name: wasm-hpa
spec:
  scaleTargetRef:
    apiVersion: apps/v1
    kind: Deployment
    name: wasm-repl-deployment
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

```bash
kubectl apply -f k8s/rlm-hpa.yaml
kubectl apply -f k8s/wasm-hpa.yaml
```

## Monitoring

### Enable Metrics Server

```bash
kubectl apply -f https://github.com/kubernetes-sigs/metrics-server/releases/latest/download/components.yaml
```

### Monitor Pod Metrics

```bash
# View resource usage
kubectl top pod -l app=rlm-inference
kubectl top pod -l app=wasm-repl

# View node usage
kubectl top node
```

### Logging

```bash
# Follow logs for all RLM pods
kubectl logs -l app=rlm-inference -f --tail=100

# Follow logs for all WASM pods
kubectl logs -l app=wasm-repl -f --tail=100

# View logs for specific pod
kubectl logs <pod-name> -f
```

## Security Best Practices

### 1. Network Security

- Network policies are already applied
- Only allow necessary traffic
- Use mTLS for service-to-service communication (optional)

### 2. Secrets Management

- Never commit secrets to version control
- Use k8s Secrets for sensitive data
- Rotate secrets regularly
- Consider using external secrets manager (HashiCorp Vault, AWS Secrets Manager)

### 3. Pod Security

- Run as non-root user (already configured)
- No privileged containers
- Drop all capabilities
- Disable privilege escalation

### 4. Image Security

- Use minimal base images
- Scan images for vulnerabilities (Trivy, Clair)
- Sign images (Cosign)
- Regularly update base images

### 5. Access Control

- Use RBAC to restrict access
- Limit pod service account permissions
- Use OPA Gatekeeper for policy enforcement

## Troubleshooting

### Pods Not Starting

```bash
# Check pod status
kubectl describe pod <pod-name>

# Check events
kubectl get events --field-selector involvedObject.kind=Pod

# Check resource availability
kubectl describe node
```

### WASM Service Unreachable

```bash
# Check if WASM pods are running
kubectl get pods -l app=wasm-repl

# Check service endpoints
kubectl get endpoints wasm-repl-service

# Test connectivity from RLM pod
kubectl exec -it <rlm-pod-name> -- curl http://wasm-repl-service:8000/health
```

### LLM API Errors

```bash
# Check if secret exists
kubectl get secret llm-secrets -o yaml

# Check if environment variable is set
kubectl exec -it <rlm-pod-name> -- env | grep LLM_API_KEY

# Test LLM API connectivity
kubectl exec -it <rlm-pod-name> -- curl -I https://api.openai.com/v1/models
```

### Performance Issues

```bash
# Check resource usage
kubectl top pod -l app=rlm-inference
kubectl top pod -l app=wasm-repl

# Increase replicas
kubectl scale deployment rlm-inference-deployment --replicas=10

# Check HPA status
kubectl describe hpa rlm-hpa
```

## Upgrading

### Rolling Update

```bash
# Update image
kubectl set image deployment/rlm-inference-deployment rlm-container=rlm-minimal:v2
kubectl set image deployment/wasm-repl-deployment wasm-repl-container=rlm-minimal-wasm:v2

# Monitor rollout
kubectl rollout status deployment/rlm-inference-deployment
kubectl rollout status deployment/wasm-repl-deployment

# Rollback if needed
kubectl rollout undo deployment/rlm-inference-deployment
kubectl rollout undo deployment/wasm-repl-deployment
```

## Cleanup

```bash
# Delete deployments
kubectl delete deployment rlm-inference-deployment
kubectl delete deployment wasm-repl-deployment

# Delete services
kubectl delete service rlm-inference-service
kubectl delete service wasm-repl-service

# Delete network policies
kubectl delete networkpolicy rlm-network-policy
kubectl delete networkpolicy wasm-network-policy
kubectl delete networkpolicy default-deny-all

# Delete secrets
kubectl delete secret llm-secrets

# Delete configmaps
kubectl delete configmap llm-config
```

## Advanced Configuration

### Ingress with TLS

```yaml
# k8s/ingress.yaml
apiVersion: networking.k8s.io/v1
kind: Ingress
metadata:
  name: rlm-ingress
  annotations:
    nginx.ingress.kubernetes.io/ssl-redirect: "true"
    cert-manager.io/cluster-issuer: "letsencrypt-prod"
spec:
  tls:
  - hosts:
    - rlm.yourdomain.com
    secretName: rlm-tls
  rules:
  - host: rlm.yourdomain.com
    http:
      paths:
      - path: /
        pathType: Prefix
        backend:
          service:
            name: rlm-inference-service
            port:
              number: 80
```

```bash
kubectl apply -f k8s/ingress.yaml
```

### Prometheus Monitoring

```yaml
# k8s/monitoring.yaml
apiVersion: monitoring.coreos.com/v1
kind: ServiceMonitor
metadata:
  name: rlm-monitor
  labels:
    release: prometheus
spec:
  selector:
    matchLabels:
      app: rlm-inference
  endpoints:
  - port: http
    path: /metrics
    interval: 30s
```

```bash
kubectl apply -f k8s/monitoring.yaml
```

## Conclusion

You now have a secure, scalable deployment of RLM with isolated WASM execution plane. Key benefits:

✅ **Security**: Complete isolation between LLM inference and code execution
✅ **Scalability**: Independent scaling of each component
✅ **Reliability**: High availability with multiple replicas
✅ **Observability**: Comprehensive monitoring and logging
✅ **Maintainability**: Clear separation of concerns

For more details, see:
- [Secure Architecture Documentation](k8s/doc/SECURE_ARCHITECTURE.md)
- [WASM REPL Setup](k8s/doc/WASM_REPL_SETUP.md)
- [k8s Configuration Files](k8s/)
