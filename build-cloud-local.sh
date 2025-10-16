#!/bin/bash
# Quick build script using Google Cloud Build locally
# This allows testing cloudbuild.yaml configurations before pushing to Cloud

set -e

# Colors for output
GREEN='\033[0;32m'
BLUE='\033[0;34m'
RED='\033[0;31m'
NC='\033[0m' # No Color

echo -e "${BLUE}======================================"
echo "NiA-Cluster Cloud Build (Local)"
echo "======================================"
echo -e "${NC}"

# Check if cloud-build-local is installed
if ! command -v cloud-build-local &> /dev/null; then
    echo -e "${RED}Error: cloud-build-local is not installed${NC}"
    echo ""
    echo "To install cloud-build-local, run:"
    echo "  gcloud components install cloud-build-local"
    echo ""
    echo "Or download from:"
    echo "  https://github.com/GoogleCloudPlatform/cloud-build-local"
    echo ""
    exit 1
fi

# Parse arguments
BUILD_TARGET=${1:-root}

if [ "$BUILD_TARGET" = "root" ]; then
    echo -e "${GREEN}Building NiA-Cluster (root) with Cloud Build...${NC}"
    cloud-build-local --config=cloudbuild.yaml \
        --dryrun=false \
        --substitutions=_CLUSTER_NAME=myfleet,_RELAY_PORT=4040 \
        .
elif [ "$BUILD_TARGET" = "enterprise" ]; then
    echo -e "${GREEN}Building NiA-Enterprise with Cloud Build...${NC}"
    cd nia-enterprise
    cloud-build-local --config=cloudbuild.yaml \
        --dryrun=false \
        --substitutions=_CLUSTER_NAME=production,_ENABLE_DEPLOYMENT=false \
        .
else
    echo -e "${RED}Unknown build target: $BUILD_TARGET${NC}"
    echo ""
    echo "Usage: $0 [root|enterprise]"
    echo "  root       - Build the main cluster-suite image"
    echo "  enterprise - Build the nia-enterprise image"
    exit 1
fi

echo ""
echo -e "${GREEN}======================================"
echo "Build completed successfully!"
echo "======================================"
echo -e "${NC}"
