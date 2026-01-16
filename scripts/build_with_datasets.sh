#!/bin/bash
# Build Docker image with preloaded datasets

set -e

echo "========================================"
echo "Building RLM Docker Image with Datasets"
echo "========================================"
echo ""

# Get parameters
IMAGE_NAME=${1:-rlm-minimal:latest}
DATASET_TYPE=${2:-all}

echo "Image: $IMAGE_NAME"
echo "Dataset: $DATASET_TYPE"
echo ""

if [ "$DATASET_TYPE" = "none" ]; then
    echo "Building without preloaded datasets..."
    docker build -t "$IMAGE_NAME" .
else
    echo "Building with $DATASET_TYPE dataset preloaded..."
    echo "This may take several minutes depending on dataset size."
    echo ""
    
    docker build \
        --build-arg SETUP_DATASETS=true \
        --build-arg DATASET_TYPE="$DATASET_TYPE" \
        -t "$IMAGE_NAME" .
fi

echo ""
echo "========================================"
echo "Build complete!"
echo "========================================"
echo ""
echo "To run benchmarks:"
echo "  docker run -e OPENAI_API_KEY=sk-xxx $IMAGE_NAME python run_benchmarks.py oolong"
echo ""
echo "For Kubernetes deployment:"
echo "  kubectl apply -f k8s/benchmark-deployment.yaml"
echo ""
