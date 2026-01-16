# Kubernetes Deployment Setup - Complete Summary

## Overview

This document summarizes all changes made to set up Kubernetes deployment for RLM benchmarks with proper dataset management.

## Changes Made

### 1. Created Files

#### scripts/setup_datasets.py (NEW)
**Purpose**: Unified dataset setup script for all benchmarks

**Key Features**:
- ✅ **BrowseComp-Plus**: Official dataset from Hugging Face (Tevatron/browsecomp-plus)
- ✅ **OOLONG**: Official repository clone (abertsch72/oolong) with dependency installation
- ✅ **RULER**: Directory setup for synthetic generation
- ✅ Command-line interface with flexible options
- ✅ Automatic dependency installation
- ✅ Fallback to synthetic data if official setup fails

**Usage**:
```bash
python scripts/setup_datasets.py --dataset all --data-dir data
python scripts/setup_datasets.py --dataset oolong --data-dir data
python scripts/setup_datasets.py --dataset browsecomp_plus --data-dir data
```

#### scripts/build_with_datasets.sh (NEW)
**Purpose**: Convenience script to build Docker images with preloaded datasets

**Usage**:
```bash
./scripts/build_with_datasets.sh rlm-minimal:full all
./scripts/build_with_datasets.sh rlm-minimal:oolong oolong
```

#### k8s/benchmark-deployment.yaml (NEW)
**Purpose**: Kubernetes deployment for running RLM benchmarks

**Key Features**:
- ✅ Supports both synthetic and official datasets
- ✅ Init container to check for official datasets
- ✅ Persistent Volume Claim (PVC) integration
- ✅ Environment variables for configuration
- ✅ Resource requests and limits
- ✅ Secret management for API keys

**Configuration**:
```yaml
Environment Variables:
- BENCHMARK_TYPE: oolong | deep_research | ruler | all | demo
- NUM_EXAMPLES: Number of examples to run
- USE_OFFICIAL_DATASETS: true | false
- DATA_DIR: /data
- OPENAI_API_KEY: From secret
```

#### k8s/dataset-init-job.yaml (NEW)
**Purpose**: Kubernetes Job to initialize official datasets

**Key Features**:
- ✅ Uses built-in setup_datasets.py script
- ✅ PVC for persistent dataset storage
- ✅ Configurable dataset type
- ✅ Resource management

**Usage**:
```bash
kubectl apply -f k8s/dataset-init-job.yaml
kubectl create job dataset-init --from=cronjob/dataset-init-job
```

#### k8s/README.md (NEW)
**Purpose**: Complete documentation for Kubernetes deployment

**Contents**:
- Quick start guide
- Available benchmarks explanation
- Configuration options
- Monitoring and troubleshooting
- Resource requirements

#### k8s/DATASET_SETUP.md (NEW)
**Purpose**: Detailed dataset setup guide

**Contents**:
- Synthetic vs Official data comparison
- Step-by-step setup instructions
- Environment variables reference
- Troubleshooting guide
- Migration guide

### 2. Modified Files

#### Dockerfile (MODIFIED)
**Changes**:
- Added script execution permissions
- Added build argument for dataset preloading
- Integrated setup_datasets.py for build-time initialization

**New Features**:
```dockerfile
ARG SETUP_DATASETS=false
RUN if [ "$SETUP_DATASETS" = "true" ]; then \
    python scripts/setup_datasets.py --dataset all; \
fi
```

**Usage**:
```bash
docker build --build-arg SETUP_DATASETS=true -t rlm-minimal:full .
```

#### doc/BENCHMARK_ANALYSIS.md (MODIFIED)
**Changes**:
- Updated OOLONG setup instructions to use setup_datasets.py
- Updated BrowseComp-Plus setup instructions to use setup_datasets.py
- Added information about unified setup approach

### 3. Deleted Files

#### scripts/setup_oolong.py (DELETED)
**Reason**: Functionality integrated into setup_datasets.py
**Replacement**: `python scripts/setup_datasets.py --dataset oolong`

#### scripts/setup_browsecomp_plus.py (DELETED)
**Reason**: Functionality integrated into setup_datasets.py  
**Replacement**: `python scripts/setup_datasets.py --dataset browsecomp_plus`

## Architecture Overview

```
┌─────────────────────────────────────────────────────────────┐
│                    Docker Image                             │
│  ┌─────────────────────────────────────────────────────┐    │
│  │  Application Code                                   │    │
│  │  ├── rlm/                                           │    │
│  │  ├── benchmarks/                                    │    │
│  │  └── scripts/                                       │    │
│  │      ├── setup_datasets.py ◄─── Unified Setup       │    │
│  │      └── build_with_datasets.sh                     │    │
│  └─────────────────────────────────────────────────────┘    │
│                                                             │
│  Build Options:                                             │
│  - Without datasets (default)                               │
│  - With preloaded datasets (--build-arg SETUP_DATASETS=true)│
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│                  Kubernetes Cluster                         │
│  ┌─────────────────┐    ┌─────────────────────────────┐    │
│  │ dataset-init-job│    │ benchmark-deployment        │    │
│  │ (Optional)      │    │                             │    │
│  │                 │    │  ┌───────────────────────┐  │    │
│  │ • Downloads     │───▶│  │ Init Container        │  │    │
│  │ • Stores in PVC │    │  │ (Dataset Check)       │  │    │
│  └─────────────────┘    │  └───────────────────────┘  │    │
│                         │              │              │    │
│                         │              ▼              │    │
│                         │  ┌───────────────────────┐  │    │
│                         │  │ Main Container        │  │    │
│                         │  │ (Benchmark Runner)    │  │    │
│                         │  └───────────────────────┘  │    │
│                         │              │              │    │
│                         │              ▼              │    │
│                         │  ┌───────────────────────┐  │    │
│                         │  │ Volumes:              │  │    │
│                         │  │ • results (emptyDir)  │  │    │
│                         │  │ • dataset (PVC)       │  │    │
│                         │  └───────────────────────┘  │    │
│                         └─────────────────────────────┘    │
└─────────────────────────────────────────────────────────────┘
```

## Dataset Sources

### Official Datasets

1. **BrowseComp-Plus**
   - Source: Hugging Face (Tevatron/browsecomp-plus)
   - Components: queries.jsonl, corpus.jsonl
   - Size: ~10-20 GB
   - Setup: Automatic download via setup_datasets.py

2. **OOLONG**
   - Source: GitHub (abertsch72/oolong)
   - Components: Repository clone with dependencies
   - Setup: Automatic git clone + pip install

3. **RULER**
   - Source: Synthetic generation
   - Setup: Directory creation only

## Quick Start Guides

### Option 1: Quick Testing (Synthetic Data)
```bash
# Build image without datasets
docker build -t rlm-minimal:latest .

# Deploy to Kubernetes
kubectl apply -f k8s/benchmark-deployment.yaml

# Run benchmark
kubectl set env deployment/rlm-benchmark BENCHMARK_TYPE=oolong
```

### Option 2: Production (Official Data - Build Time)
```bash
# Build with preloaded datasets
./scripts/build_with_datasets.sh rlm-minimal:full all

# Deploy (no dataset initialization needed)
kubectl apply -f k8s/benchmark-deployment.yaml
kubectl set env deployment/rlm-benchmark USE_OFFICIAL_DATASETS=true
```

### Option 3: Production (Official Data - Runtime)
```bash
# Build without datasets
docker build -t rlm-minimal:latest .

# Initialize datasets via Job
kubectl apply -f k8s/dataset-init-job.yaml
kubectl create job dataset-init --from=cronjob/dataset-init-job

# Deploy with official data
kubectl apply -f k8s/benchmark-deployment.yaml
kubectl set env deployment/rlm-benchmark USE_OFFICIAL_DATASETS=true
```

## Configuration Reference

### Environment Variables

| Variable | Description | Default |
|----------|-------------|----------|
| `BENCHMARK_TYPE` | Benchmark to run | `oolong` |
| `NUM_EXAMPLES` | Number of examples | `10` |
| `USE_OFFICIAL_DATASETS` | Use official datasets | `false` |
| `DATA_DIR` | Dataset directory | `/data` |
| `OUTPUT_FILE` | Results file path | `/results/benchmark-results.json` |
| `LLM_MODEL` | Primary LLM model | `gpt-4o` |
| `LLM_RECURSIVE_MODEL` | Recursive LLM model | `gpt-4o` |
| `OPENAI_API_KEY` | OpenAI API key | (required) |

### Kubernetes Resources

| Resource | Request | Limit |
|----------|---------|-------|
| CPU | 100m | 500m |
| Memory | 512Mi | 2Gi |
| Storage (PVC) | 50Gi | - |

## Verification Steps

### 1. Check Scripts
```bash
ls -la scripts/
# Should show: setup_datasets.py, build_with_datasets.sh, docker_build.sh

# Check executability
file scripts/setup_datasets.py
# Should show: Python script, ASCII text executable
```

### 2. Check Kubernetes Files
```bash
ls -la k8s/
# Should show: benchmark-deployment.yaml, dataset-init-job.yaml, README.md, DATASET_SETUP.md
```

### 3. Test Setup Script
```bash
# Show help
python scripts/setup_datasets.py --help

# Test dry run (without downloading)
python scripts/setup_datasets.py --dataset oolong --data-dir /tmp/test --force
```

### 4. Build Docker Image
```bash
# Test build without datasets
docker build -t rlm-minimal:test .

# Verify scripts are included
docker run --rm rlm-minimal:test ls -la scripts/
```

## Troubleshooting

### Issue: Dataset not found
**Solution**: Run dataset initialization job
```bash
kubectl create job dataset-init --from=cronjob/dataset-init-job
```

### Issue: Permission denied
**Solution**: Make scripts executable
```bash
chmod +x scripts/*.py scripts/*.sh
```

### Issue: PVC not available
**Solution**: Create PVC first
```bash
kubectl apply -f k8s/dataset-init-job.yaml
```

## Summary

✅ **Unified Setup**: Single script for all datasets  
✅ **Official Sources**: Uses official OOLONG and BrowseComp-Plus  
✅ **Flexible Deployment**: Multiple options for different use cases  
✅ **Well Documented**: Comprehensive README and guides  
✅ **Production Ready**: Kubernetes deployment with proper resource management  
✅ **Maintainable**: Clean architecture with no duplication  

All changes are now in sync and ready for use!
