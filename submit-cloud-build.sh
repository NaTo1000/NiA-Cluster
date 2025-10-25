#!/bin/bash
# Submit builds to Google Cloud Build
# This script submits the build to GCP Cloud Build service

set -e

# Colors for output
GREEN='\033[0;32m'
BLUE='\033[0;34m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${BLUE}======================================"
echo "NiA-Cluster Cloud Build Submission"
echo "======================================"
echo -e "${NC}"

# Check if gcloud is installed
if ! command -v gcloud &> /dev/null; then
    echo -e "${RED}Error: gcloud CLI is not installed${NC}"
    echo ""
    echo "Please install the Google Cloud SDK:"
    echo "  https://cloud.google.com/sdk/docs/install"
    echo ""
    exit 1
fi

# Check if user is authenticated
if ! gcloud auth list --filter=status:ACTIVE --format="value(account)" &> /dev/null; then
    echo -e "${YELLOW}Warning: Not authenticated with gcloud${NC}"
    echo "Run: gcloud auth login"
    exit 1
fi

# Parse arguments
BUILD_TARGET=${1:-root}
PROJECT_ID=${2:-$(gcloud config get-value project 2>/dev/null)}

if [ -z "$PROJECT_ID" ]; then
    echo -e "${RED}Error: No GCP project ID specified${NC}"
    echo ""
    echo "Usage: $0 [root|enterprise] [PROJECT_ID]"
    echo ""
    echo "Or set a default project:"
    echo "  gcloud config set project YOUR_PROJECT_ID"
    exit 1
fi

echo -e "${GREEN}Project ID: $PROJECT_ID${NC}"
echo ""

if [ "$BUILD_TARGET" = "root" ]; then
    echo -e "${BLUE}Submitting NiA-Cluster build to Cloud Build...${NC}"
    gcloud builds submit \
        --config=cloudbuild.yaml \
        --substitutions=_CLUSTER_NAME=myfleet,_RELAY_PORT=4040 \
        --project="$PROJECT_ID" \
        .
    
elif [ "$BUILD_TARGET" = "enterprise" ]; then
    echo -e "${BLUE}Submitting NiA-Enterprise build to Cloud Build...${NC}"
    
    # Prompt for deployment option
    read -p "Enable deployment to GKE? (y/N): " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        ENABLE_DEPLOY="true"
        read -p "Enter GKE cluster name [nia-cluster]: " GKE_CLUSTER
        GKE_CLUSTER=${GKE_CLUSTER:-nia-cluster}
        read -p "Enter GKE region [us-central1]: " GKE_REGION
        GKE_REGION=${GKE_REGION:-us-central1}
    else
        ENABLE_DEPLOY="false"
        GKE_CLUSTER="nia-cluster"
        GKE_REGION="us-central1"
    fi
    
    gcloud builds submit \
        --config=cloudbuild.yaml \
        --substitutions="_CLUSTER_NAME=production,_ENABLE_DEPLOYMENT=$ENABLE_DEPLOY,_GKE_CLUSTER=$GKE_CLUSTER,_GKE_REGION=$GKE_REGION,_ARTIFACT_BUCKET=$PROJECT_ID-build-artifacts" \
        --project="$PROJECT_ID" \
        ./nia-enterprise
    
elif [ "$BUILD_TARGET" = "both" ]; then
    echo -e "${BLUE}Submitting both builds to Cloud Build...${NC}"
    echo ""
    
    # Build root first
    echo -e "${YELLOW}1/2: Building cluster-suite...${NC}"
    gcloud builds submit \
        --config=cloudbuild.yaml \
        --substitutions=_CLUSTER_NAME=myfleet,_RELAY_PORT=4040 \
        --project="$PROJECT_ID" \
        .
    
    echo ""
    echo -e "${YELLOW}2/2: Building nia-enterprise...${NC}"
    gcloud builds submit \
        --config=cloudbuild.yaml \
        --substitutions=_CLUSTER_NAME=production,_ENABLE_DEPLOYMENT=false \
        --project="$PROJECT_ID" \
        ./nia-enterprise
    
else
    echo -e "${RED}Unknown build target: $BUILD_TARGET${NC}"
    echo ""
    echo "Usage: $0 [root|enterprise|both] [PROJECT_ID]"
    echo ""
    echo "Examples:"
    echo "  $0 root my-gcp-project       # Build cluster-suite"
    echo "  $0 enterprise my-gcp-project # Build nia-enterprise"
    echo "  $0 both my-gcp-project       # Build both"
    exit 1
fi

echo ""
echo -e "${GREEN}======================================"
echo "Build submitted successfully!"
echo "======================================"
echo -e "${NC}"
echo ""
echo "To view build status:"
echo "  gcloud builds list --project=$PROJECT_ID --limit=5"
echo ""
echo "To view logs:"
echo "  gcloud builds log --stream [BUILD_ID] --project=$PROJECT_ID"
