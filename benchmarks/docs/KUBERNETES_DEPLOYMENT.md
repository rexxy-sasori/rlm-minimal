# RLM Kubernetes Benchmark Deployment

> **Location:** `/benchmarks/docs/KUBERNETES_DEPLOYMENT.md`

This guide explains how to deploy and run RLM benchmarks in a Kubernetes cluster.

## Related Documentation

- [BENCHMARK_ANALYSIS.md](BENCHMARK_ANALYSIS.md) - Benchmark analysis and implementation plan
- [DATASET_SETUP.md](DATASET_SETUP.md) - Setup benchmark datasets

## Available Benchmarks

- **oolong**: Difficult long-context tasks (fact retrieval, multi-hop reasoning, summarization)
- **deep_research**: Complex research tasks (literature review, competitive analysis, technical evaluation)
- **ruler**: Needle-in-haystack evaluation (testing retrieval across different context lengths)
- **all**: Run all benchmarks sequentially
- **demo**: Show benchmark examples without running a model

## Quick Start

### 1. Prepare Your Secrets

First, update the Secret in `benchmark-deployment.yaml` with your actual OpenAI API key:

```bash
kubectl create secret generic llm-secrets \
  --from-literal=openai-api-key="sk-your-actual-api-key-here"
```

### 2. Deploy the Benchmark

Deploy with default settings (OOLONG benchmark, 10 examples):

```bash
kubectl apply -f deploy/k8s/benchmark-deployment.yaml
```

### 3. Run a Specific Benchmark

To run a different benchmark, modify the `BENCHMARK_TYPE` environment variable:

```bash
# Run RULER benchmark
kubectl set env deployment/rlm-benchmark BENCHMARK_TYPE=ruler

# Run Deep Research benchmark
kubectl set env deployment/rlm-benchmark BENCHMARK_TYPE=deep_research

# Run all benchmarks
kubectl set env deployment/rlm-benchmark BENCHMARK_TYPE=all
```

### 4. Adjust Number of Examples

```bash
# Run with 20 examples
kubectl set env deployment/rlm-benchmark NUM_EXAMPLES=20
```

## Monitoring Progress

### Check Pod Status

```bash
kubectl get pods -l app=rlm-benchmark
```

### View Logs

```bash
# Get the pod name
POD_NAME=$(kubectl get pods -l app=rlm-benchmark -o jsonpath='{.items[0].metadata.name}')

# Stream logs
kubectl logs -f $POD_NAME
```

### Check Results

Results are stored in `/results/benchmark-results.json` inside the container. To retrieve them:

```bash
# Copy results from pod to local machine
kubectl cp $POD_NAME:/results/benchmark-results.json ./benchmark-results.json

# View results
cat benchmark-results.json | jq
```

## Configuration Options

### Environment Variables

| Variable | Description | Default |
|----------|-------------|----------|
| `OPENAI_API_KEY` | Your OpenAI API key (required) | From Secret |
| `LLM_MODEL` | Primary LLM model to use | `gpt-4o` |
| `LLM_RECURSIVE_MODEL` | Recursive LLM model to use | `gpt-4o` |
| `BENCHMARK_TYPE` | Which benchmark to run | `oolong` |
| `NUM_EXAMPLES` | Number of examples to run | `10` |
| `OUTPUT_FILE` | Path to save results | `/results/benchmark-results.json` |

### Resource Requirements

The deployment includes resource requests and limits:
- **CPU**: 100m (request) - 500m (limit)
- **Memory**: 512Mi (request) - 2Gi (limit)

Adjust these based on your cluster resources and benchmark requirements.

## Running Multiple Benchmarks in Parallel

To run different benchmarks simultaneously, create separate deployments with different names:

```bash
# Create deployment for OOLONG
kubectl apply -f deploy/k8s/benchmark-deployment.yaml
kubectl set env deployment/rlm-benchmark BENCHMARK_TYPE=oolong

# Create deployment for RULER (with different name)
kubectl create deployment rlm-benchmark-ruler --image=rlm-minimal:latest --dry-run=client -o yaml > k8s/ruler-deployment.yaml
# Edit the file to set BENCHMARK_TYPE=ruler
kubectl apply -f k8s/ruler-deployment.yaml
```

## Cleaning Up

```bash
# Delete the deployment
kubectl delete deployment rlm-benchmark

# Delete the service
kubectl delete service rlm-benchmark-service

# Delete the secret (optional)
kubectl delete secret llm-secrets
```

## Building the Docker Image

Before deploying, ensure you have built the Docker image:

```bash
docker build -t rlm-minimal:latest .
```

If using a remote cluster, push the image to a registry:

```bash
docker tag rlm-minimal:latest your-registry/rlm-minimal:latest
docker push your-registry/rlm-minimal:latest
```

Then update the image in `benchmark-deployment.yaml`:

```yaml
image: your-registry/rlm-minimal:latest
```

## Notes

- The deployment uses `restartPolicy: Never` since benchmarks are one-time jobs
- Results are stored in an `emptyDir` volume, which is ephemeral. For persistent storage, consider using a PVC
- For production use, consider using Jobs instead of Deployments for better job management
