# Cloud Build Quick Reference

Quick reference for Google Cloud Build integration with NiA-Cluster.

## Setup

```bash
# Install Google Cloud SDK
curl https://sdk.cloud.google.com | bash

# Authenticate
gcloud auth login
gcloud config set project YOUR_PROJECT_ID

# Enable required APIs
gcloud services enable cloudbuild.googleapis.com containerregistry.googleapis.com
```

## Build Commands

### Submit Builds

```bash
# Using helper script (recommended)
./submit-cloud-build.sh root YOUR_PROJECT_ID       # Build cluster-suite
./submit-cloud-build.sh enterprise YOUR_PROJECT_ID # Build nia-enterprise
./submit-cloud-build.sh both YOUR_PROJECT_ID       # Build both

# Direct gcloud commands
gcloud builds submit --config=cloudbuild.yaml .
gcloud builds submit --config=cloudbuild.yaml ./nia-enterprise
```

### Local Testing

```bash
# Install cloud-build-local
gcloud components install cloud-build-local

# Test locally
./build-cloud-local.sh root
./build-cloud-local.sh enterprise
```

## Build Management

```bash
# List builds
gcloud builds list --limit=10

# View build logs
gcloud builds log BUILD_ID
gcloud builds log --stream BUILD_ID  # Stream live logs

# Cancel a build
gcloud builds cancel BUILD_ID

# Describe a build
gcloud builds describe BUILD_ID
```

## Build Triggers

```bash
# Create trigger for main branch
gcloud builds triggers create github \
  --repo-name=NiA-Cluster \
  --repo-owner=NaTo1000 \
  --branch-pattern="^main$" \
  --build-config=cloudbuild.yaml

# List triggers
gcloud builds triggers list

# Run a trigger manually
gcloud builds triggers run TRIGGER_NAME --branch=main

# Delete a trigger
gcloud builds triggers delete TRIGGER_NAME
```

## Image Management

```bash
# List images
gcloud container images list --repository=gcr.io/$PROJECT_ID

# List tags for an image
gcloud container images list-tags gcr.io/$PROJECT_ID/cluster-suite

# Delete an image
gcloud container images delete gcr.io/$PROJECT_ID/cluster-suite:TAG

# Pull an image
docker pull gcr.io/$PROJECT_ID/cluster-suite:latest
```

## Custom Builds

```bash
# With custom substitutions
gcloud builds submit \
  --config=cloudbuild.yaml \
  --substitutions=_CLUSTER_NAME=production,_RELAY_PORT=8080 \
  .

# With specific machine type
gcloud builds submit \
  --config=cloudbuild.yaml \
  --machine-type=N1_HIGHCPU_32 \
  .

# With custom timeout
gcloud builds submit \
  --config=cloudbuild.yaml \
  --timeout=30m \
  .
```

## GKE Deployment

```bash
# Build and deploy to GKE
gcloud builds submit \
  --config=cloudbuild.yaml \
  --substitutions=_ENABLE_DEPLOYMENT=true,_GKE_CLUSTER=nia-cluster,_GKE_REGION=us-central1 \
  ./nia-enterprise

# Verify deployment
kubectl get pods -n nia-enterprise
kubectl get services -n nia-enterprise
```

## Monitoring

```bash
# View build history
gcloud builds list --format="table(id,status,createTime,duration)"

# View successful builds only
gcloud builds list --filter="status=SUCCESS" --limit=5

# View failed builds
gcloud builds list --filter="status=FAILURE" --limit=5

# Export build logs
gcloud builds log BUILD_ID > build.log
```

## Troubleshooting

```bash
# Check service account permissions
gcloud projects get-iam-policy $PROJECT_ID \
  --flatten="bindings[].members" \
  --filter="bindings.members:cloudbuild.gserviceaccount.com"

# Check API status
gcloud services list --enabled | grep -E "cloudbuild|containerregistry"

# View quota usage
gcloud builds list --format="sum(duration)" --filter="createTime>-P1D"
```

## Cost Management

```bash
# View build costs (approximate)
gcloud builds list \
  --format="table(id,createTime,duration)" \
  --filter="createTime>-P30D"

# Clean up old images
# List images older than 30 days
gcloud container images list-tags gcr.io/$PROJECT_ID/cluster-suite \
  --filter="timestamp.datetime<-P30D" \
  --format="get(digest)"

# Delete old images (be careful!)
for digest in $(gcloud container images list-tags gcr.io/$PROJECT_ID/cluster-suite \
  --filter="timestamp.datetime<-P30D" --format="get(digest)"); do
  gcloud container images delete "gcr.io/$PROJECT_ID/cluster-suite@$digest" --quiet
done
```

## Useful Substitutions

### Root Project
- `_CLUSTER_NAME`: Cluster name (default: myfleet)
- `_RELAY_PORT`: Relay port (default: 4040)

### Enterprise Project
- `_CLUSTER_NAME`: Cluster name (default: production)
- `_ENABLE_DEPLOYMENT`: Enable GKE deployment (default: false)
- `_GKE_CLUSTER`: GKE cluster name (default: nia-cluster)
- `_GKE_REGION`: GKE region (default: us-central1)
- `_ARTIFACT_BUCKET`: Artifact bucket (default: PROJECT_ID-build-artifacts)

## Examples

### Daily Workflow

```bash
# 1. Make code changes
# 2. Test locally
docker build -t cluster-suite:test .

# 3. Submit to cloud build
./submit-cloud-build.sh root my-project

# 4. Monitor build
gcloud builds list --limit=1
gcloud builds log --stream LATEST_BUILD_ID

# 5. Pull and test the built image
docker pull gcr.io/my-project/cluster-suite:latest
docker run --rm gcr.io/my-project/cluster-suite:latest --help
```

### Production Deployment

```bash
# 1. Build with cloud build
gcloud builds submit --config=cloudbuild.yaml ./nia-enterprise

# 2. Deploy to staging GKE
gcloud builds submit \
  --config=cloudbuild.yaml \
  --substitutions=_ENABLE_DEPLOYMENT=true,_GKE_CLUSTER=staging-cluster \
  ./nia-enterprise

# 3. Verify deployment
kubectl get pods -n nia-enterprise

# 4. Deploy to production (with approval)
gcloud builds submit \
  --config=cloudbuild.yaml \
  --substitutions=_ENABLE_DEPLOYMENT=true,_GKE_CLUSTER=production-cluster \
  ./nia-enterprise
```

## Additional Resources

- Full documentation: [CLOUD_BUILD.md](CLOUD_BUILD.md)
- Cloud Build Docs: https://cloud.google.com/build/docs
- Container Registry: https://cloud.google.com/container-registry/docs
