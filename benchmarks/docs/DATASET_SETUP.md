# Dataset Setup Guide for RLM Benchmarks

> **Location:** `/benchmarks/docs/DATASET_SETUP.md`

This guide explains how to set up datasets for running RLM benchmarks, including both official and synthetic dataset options.

## Related Documentation

- [BENCHMARK_ANALYSIS.md](BENCHMARK_ANALYSIS.md) - Benchmark analysis and implementation plan
- [KUBERNETES_DEPLOYMENT.md](KUBERNETES_DEPLOYMENT.md) - Deploy benchmarks to Kubernetes

## Dataset Options

### 1. Synthetic Datasets (Default)
- **No setup required** - Data is generated on-the-fly
- **Fast** - No download time
- **Limited** - Simulated data for testing purposes
- **Best for**: Development, testing, and quick validation

### 2. Official Datasets
- **BrowseComp-Plus** - Real research papers and queries
- **OOLONG** - Difficult long-context benchmark (requires separate setup)
- **RULER** - Generates synthetic needles in haystacks
- **Best for**: Accurate benchmarking and publication results

## Quick Start with Synthetic Data

By default, the benchmark uses synthetic data. No dataset setup is required:

```bash
# Deploy benchmark with synthetic data (default)
kubectl apply -f k8s/benchmark-deployment.yaml
```

## Setup with Official Datasets

### Step 1: Create Persistent Volume Claim (PVC)

First, create a PVC to store the downloaded datasets:

```bash
kubectl apply -f k8s/dataset-init-job.yaml
```

This creates a 50Gi PVC. Adjust the storage size in `dataset-init-job.yaml` if needed.

### Step 2: Run Dataset Initialization Job

The job will automatically download the BrowseComp-Plus dataset:

```bash
kubectl create job dataset-init --from=cronjob/dataset-init-job
```

### Step 3: Monitor Job Progress

```bash
# Check job status
kubectl get jobs

# Check pod status
kubectl get pods -l job-name=dataset-init

# View logs
kubectl logs -f $(kubectl get pods -l job-name=dataset-init -o jsonpath='{.items[0].metadata.name}')
```

### Step 4: Deploy Benchmark with Official Data

Set the environment variable to use official datasets:

```bash
# Deploy with official datasets enabled
kubectl apply -f k8s/benchmark-deployment.yaml
kubectl set env deployment/rlm-benchmark USE_OFFICIAL_DATASETS=true
```

## Dataset Details

### BrowseComp-Plus Dataset

**What's included:**
- `queries.jsonl` - Research queries and relevance judgments
- `corpus.jsonl` - Research papers and documents
- **Size**: ~10-20GB when downloaded

**Source**: Hugging Face Datasets (`Tevatron/browsecomp-plus`)

**Usage**:
```bash
# For Deep Research benchmark
kubectl set env deployment/rlm-benchmark BENCHMARK_TYPE=deep_research
kubectl set env deployment/rlm-benchmark USE_OFFICIAL_DATASETS=true
```

### OOLONG Dataset

**Status**: Requires manual setup

**What's needed:**
- Official OOLONG dataset files
- Contact the dataset authors for access

**Setup**:
```bash
# Create OOLONG directory structure
kubectl exec -it $(kubectl get pods -l app=rlm-benchmark -o jsonpath='{.items[0].metadata.name}') -- mkdir -p /data/oolong

# Copy OOLONG files to the PVC
kubectl cp /local/path/to/oolong/* $(kubectl get pods -l app=rlm-benchmark -o jsonpath='{.items[0].metadata.name}'):/data/oolong/

# Enable OOLONG official data
kubectl set env deployment/rlm-benchmark USE_OFFICIAL_DATASETS=true
kubectl set env deployment/rlm-benchmark BENCHMARK_TYPE=oolong
```

### RULER Dataset

**Status**: Generates synthetic data

**What's included:**
- Synthetic "needles" inserted into random contexts
- Various context lengths (1K to 10M+ tokens)
- Different needle positions (beginning, middle, end)

**No setup required** - Data is generated dynamically during benchmark execution.

## Environment Variables

| Variable | Description | Default |
|----------|-------------|----------|
| `USE_OFFICIAL_DATASETS` | Use downloaded official datasets | `false` |
| `DATA_DIR` | Root directory for datasets | `/data` |
| `OOLONG_DATA_DIR` | OOLONG dataset directory | `/data/oolong` |
| `BROWSECOMP_PLUS_DATA_DIR` | BrowseComp-Plus directory | `/data` |
| `HUGGING_FACE_HUB_TOKEN` | Token for gated datasets | (optional) |

## Managing Datasets

### Check Dataset Status

```bash
# Exec into the benchmark pod
kubectl exec -it $(kubectl get pods -l app=rlm-benchmark -o jsonpath='{.items[0].metadata.name}') -- /bin/bash

# Check if datasets exist
ls -lh /data/

# Check file sizes
du -sh /data/*
```

### Update Datasets

To refresh or update datasets:

```bash
# Delete existing job
kubectl delete job dataset-init

# Re-run initialization
kubectl create job dataset-init --from=cronjob/dataset-init-job
```

### Cleanup Datasets

```bash
# Delete the PVC (WARNING: This deletes all data!)
kubectl delete pvc dataset-pvc

# Recreate PVC
kubectl apply -f k8s/dataset-init-job.yaml
```

## Troubleshooting

### Dataset Not Found Error

If you see:
```
ERROR: Official datasets not found!
```

**Solution**: Run the dataset initialization job first:
```bash
kubectl create job dataset-init --from=cronjob/dataset-init-job
```

### Insufficient Storage

If the PVC is too small:

```bash
# Edit the PVC size in dataset-init-job.yaml
kubectl edit pvc dataset-pvc

# Or delete and recreate with larger size
kubectl delete pvc dataset-pvc
# Modify storage: 100Gi in dataset-init-job.yaml
kubectl apply -f k8s/dataset-init-job.yaml
```

### Hugging Face Authentication

If datasets require authentication:

```bash
# Create secret with your Hugging Face token
kubectl create secret generic llm-secrets \
  --from-literal=openai-api-key="sk-xxx" \
  --from-literal=huggingface-token="hf-xxx"

# Restart the dataset job
kubectl delete job dataset-init
kubectl create job dataset-init --from=cronjob/dataset-init-job
```

## Performance Considerations

### Storage Class

For better performance, use a fast storage class:

```yaml
# In dataset-init-job.yaml
apiVersion: v1
kind: PersistentVolumeClaim
metadata:
  name: dataset-pvc
spec:
  storageClassName: "fast-storage"  # Adjust to your storage class
  accessModes:
    - ReadWriteOnce
  resources:
    requests:
      storage: 50Gi
```

### Dataset Caching

Once downloaded, datasets are cached in the PVC and reused across benchmark runs.

## Migration from Synthetic to Official

To switch from synthetic to official data:

```bash
# 1. Run dataset initialization
kubectl create job dataset-init --from=cronjob/dataset-init-job

# 2. Update deployment to use official data
kubectl set env deployment/rlm-benchmark USE_OFFICIAL_DATASETS=true

# 3. Restart deployment to apply changes
kubectl rollout restart deployment/rlm-benchmark
```

## Summary

- **Synthetic data**: No setup, fast, for testing
- **Official data**: Requires initialization, accurate, for publication
- **PVC**: Persists datasets across runs
- **Job**: Automated dataset download and setup

Choose the dataset type based on your benchmarking needs!
