#!/bin/bash
# Build custom Airflow image for the FHVHV Big Data project
set -e

AIRFLOW_DIR="/mnt/d/Big Data/Project/bigdata-lab/bigdata-lab/airflow"
IMAGE_NAME="bigdata-lab-airflow:fhvhv-v1"

echo "======================================================"
echo "  Building Custom Airflow Image: ${IMAGE_NAME}"
echo "======================================================"

# Build using buildah (comes with containerd/k3s toolchain)
# or use docker if available
if command -v buildah &>/dev/null; then
    echo "[BUILD] Using buildah..."
    buildah build \
        --platform linux/amd64 \
        --tag "${IMAGE_NAME}" \
        "${AIRFLOW_DIR}/docker"
    
    # Import into k3s containerd
    buildah push "${IMAGE_NAME}" "oci-archive:/tmp/airflow-fhvhv.tar:${IMAGE_NAME}"
    k3s ctr images import /tmp/airflow-fhvhv.tar
    rm -f /tmp/airflow-fhvhv.tar
    
elif command -v docker &>/dev/null; then
    echo "[BUILD] Using docker..."
    docker build \
        --platform linux/amd64 \
        --tag "${IMAGE_NAME}" \
        "${AIRFLOW_DIR}/docker"
    
    # Export to k3s
    docker save "${IMAGE_NAME}" | k3s ctr images import -
    
else
    echo "[BUILD] No docker/buildah found, trying pip install approach..."
    # Alternative: install pip packages in existing image via k3s
    echo "ERROR: Cannot build image without docker or buildah"
    exit 1
fi

echo ""
echo "======================================================"
echo "  Image built and imported successfully!"
echo "  Image: ${IMAGE_NAME}"
echo "======================================================"

# Verify image is loaded
echo ""
echo "[VERIFY] Loaded images:"
k3s ctr images list | grep airflow
