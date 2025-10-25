# Docker Cloud Build Integration

This document describes the Google Cloud Build integration for NiA-Cluster, enabling quick builds in containerized VM environments.

## Overview

Docker Cloud Build (Google Cloud Build) provides:
- **Fast, parallel builds** in containerized environments
- **Automatic caching** for faster subsequent builds
- **Multi-architecture support** (amd64, arm64)
- **Security scanning** with Trivy integration
- **Direct deployment** to Google Kubernetes Engine (GKE)
- **Build artifacts** storage and management

## Quick Start

### Prerequisites

1. **Google Cloud SDK** installed:
   ```bash
   # Install gcloud CLI
   curl https://sdk.cloud.google.com | bash
   exec -l $SHELL
   gcloud init
   ```

2. **Authenticate with Google Cloud**:
   ```bash
   gcloud auth login
   gcloud config set project YOUR_PROJECT_ID
   ```

3. **Enable required APIs**:
   ```bash
   gcloud services enable cloudbuild.googleapis.com
   gcloud services enable containerregistry.googleapis.com
   gcloud services enable container.googleapis.com  # For GKE
   ```

### Building with Cloud Build

#### Option 1: Submit to Cloud Build (Recommended)

Use the provided script to submit builds to Google Cloud Build:

```bash
# Build the main cluster-suite image
./submit-cloud-build.sh root YOUR_PROJECT_ID

# Build the nia-enterprise image
./submit-cloud-build.sh enterprise YOUR_PROJECT_ID

# Build both images
./submit-cloud-build.sh both YOUR_PROJECT_ID
```

#### Option 2: Manual gcloud Command

```bash
# Build cluster-suite
gcloud builds submit --config=cloudbuild.yaml .

# Build nia-enterprise
cd nia-enterprise
gcloud builds submit --config=cloudbuild.yaml .
```

#### Option 3: Local Cloud Build (Testing)

Test cloudbuild.yaml configurations locally before pushing to cloud:

```bash
# Install cloud-build-local
gcloud components install cloud-build-local

# Run local build
./build-cloud-local.sh root        # Build cluster-suite
./build-cloud-local.sh enterprise  # Build nia-enterprise
```

## Configuration Files

### Root Project: `cloudbuild.yaml`

Builds the main `cluster-suite` Docker image with the following steps:
1. Build Docker image with multi-tagging (SHA + latest)
2. Run basic tests (help command, validation)
3. Push images to Google Container Registry (GCR)
4. Optional: Build with docker-compose for integration testing

**Key Features:**
- Parallel build execution
- High-CPU machine type (N1_HIGHCPU_8)
- Docker layer caching
- 20-minute timeout

### NiA-Enterprise: `nia-enterprise/cloudbuild.yaml`

Production-grade build configuration with advanced features:
1. Multi-stage Docker build
2. Security scanning with Trivy
3. Container structure tests
4. Multi-architecture builds (amd64, arm64)
5. Automatic deployment to GKE (optional)
6. Build artifacts storage

**Key Features:**
- Production optimizations
- Security best practices
- GKE deployment automation
- Build artifact archival

## Build Triggers

### Automatic Builds

Set up automatic builds on code changes:

```bash
# Create a build trigger for the main branch
gcloud builds triggers create github \
  --repo-name=NiA-Cluster \
  --repo-owner=NaTo1000 \
  --branch-pattern="^main$" \
  --build-config=cloudbuild.yaml \
  --description="Build cluster-suite on main branch"

# Create a trigger for nia-enterprise
gcloud builds triggers create github \
  --repo-name=NiA-Cluster \
  --repo-owner=NaTo1000 \
  --branch-pattern="^main$" \
  --build-config=nia-enterprise/cloudbuild.yaml \
  --included-files="nia-enterprise/**" \
  --description="Build nia-enterprise on main branch changes"
```

### Manual Trigger Execution

```bash
# List triggers
gcloud builds triggers list

# Run a specific trigger
gcloud builds triggers run TRIGGER_NAME --branch=main
```

## Customization

### Build Substitutions

Override default values using substitutions:

```bash
# Custom cluster configuration
gcloud builds submit \
  --config=cloudbuild.yaml \
  --substitutions=_CLUSTER_NAME=production,_RELAY_PORT=8080 \
  .

# Enable GKE deployment for enterprise
gcloud builds submit \
  --config=cloudbuild.yaml \
  --substitutions=_ENABLE_DEPLOYMENT=true,_GKE_CLUSTER=my-cluster,_GKE_REGION=us-central1 \
  ./nia-enterprise
```

### Available Substitutions

**Root cloudbuild.yaml:**
- `_CLUSTER_NAME`: Cluster name (default: myfleet)
- `_RELAY_PORT`: Relay server port (default: 4040)

**Enterprise cloudbuild.yaml:**
- `_CLUSTER_NAME`: Cluster name (default: production)
- `_RELAY_PORT`: Relay server port (default: 4040)
- `_ENABLE_DEPLOYMENT`: Enable GKE deployment (default: false)
- `_GKE_REGION`: GKE region (default: us-central1)
- `_GKE_CLUSTER`: GKE cluster name (default: nia-cluster)
- `_ARTIFACT_BUCKET`: GCS bucket for artifacts (default: PROJECT_ID-build-artifacts)

## Viewing Builds

### List Recent Builds

```bash
# List last 10 builds
gcloud builds list --limit=10

# Filter by status
gcloud builds list --filter="status=SUCCESS" --limit=5
```

### View Build Logs

```bash
# Stream logs for a build
gcloud builds log --stream BUILD_ID

# View completed build logs
gcloud builds log BUILD_ID
```

### View Build in Console

```bash
# Open build in web console
gcloud builds describe BUILD_ID --format="value(logUrl)"
```

## CI/CD Integration

### GitHub Actions Integration

The enterprise project includes GitHub Actions workflow (`.github/workflows/ci-cd.yml`) that can trigger Cloud Builds:

```yaml
- name: Trigger Cloud Build
  run: |
    gcloud builds submit \
      --config=cloudbuild.yaml \
      --project=${{ secrets.GCP_PROJECT_ID }}
```

### Jenkins Integration

```groovy
stage('Cloud Build') {
    steps {
        sh '''
            gcloud builds submit \
              --config=cloudbuild.yaml \
              --project=${GCP_PROJECT_ID}
        '''
    }
}
```

## Advanced Features

### Multi-Architecture Builds

The enterprise cloudbuild.yaml includes multi-arch support:

```yaml
- name: 'gcr.io/cloud-builders/docker'
  args:
    - buildx
    - build
    - --platform
    - linux/amd64,linux/arm64
    - -t
    - gcr.io/$PROJECT_ID/nia-enterprise:multiarch
    - --push
```

### Security Scanning

Trivy automatically scans images for vulnerabilities:

```bash
# View security scan results
gsutil cat gs://YOUR_PROJECT_ID-build-artifacts/builds/BUILD_ID/trivy-report.json
```

### Container Structure Tests

Validate image structure and configuration:

```bash
# Run structure tests locally
container-structure-test test \
  --image nia-enterprise:latest \
  --config nia-enterprise/docker/container-structure-test.yaml
```

## Performance Optimization

### Machine Types

Available machine types for faster builds:
- `N1_HIGHCPU_8`: 8 vCPUs (default for root)
- `E2_HIGHCPU_8`: 8 vCPUs (default for enterprise)
- `N1_HIGHCPU_32`: 32 vCPUs (for very large builds)

Change in `cloudbuild.yaml`:
```yaml
options:
  machineType: 'N1_HIGHCPU_32'
```

### Build Cache

Cloud Build automatically caches Docker layers. For faster builds:
```yaml
options:
  cache-from: type=gha
  cache-to: type=gha,mode=max
```

### Worker Pools

Use private worker pools for faster builds and network access:

```bash
# Create a worker pool
gcloud builds worker-pools create fast-pool \
  --region=us-central1 \
  --worker-disk-size=200GB \
  --worker-machine-type=e2-highcpu-8

# Use in cloudbuild.yaml
options:
  pool:
    name: 'projects/$PROJECT_ID/locations/us-central1/workerPools/fast-pool'
```

## Troubleshooting

### Build Timeout

Increase timeout in `cloudbuild.yaml`:
```yaml
timeout: 1800s  # 30 minutes
```

### Permission Denied

Grant Cloud Build service account permissions:
```bash
# Get service account
PROJECT_NUMBER=$(gcloud projects describe $PROJECT_ID --format="value(projectNumber)")
SERVICE_ACCOUNT="${PROJECT_NUMBER}@cloudbuild.gserviceaccount.com"

# Grant permissions
gcloud projects add-iam-policy-binding $PROJECT_ID \
  --member="serviceAccount:${SERVICE_ACCOUNT}" \
  --role="roles/container.developer"
```

### Image Push Failures

Enable Container Registry API:
```bash
gcloud services enable containerregistry.googleapis.com
```

## Cost Optimization

### Build Minutes

Cloud Build includes:
- **120 build-minutes/day** free
- Additional minutes charged per usage

Monitor usage:
```bash
gcloud builds list --format="table(id,createTime,duration)"
```

### Storage Costs

Images in Container Registry incur storage costs. Clean up old images:
```bash
# List images
gcloud container images list --repository=gcr.io/$PROJECT_ID

# Delete old images
gcloud container images delete gcr.io/$PROJECT_ID/cluster-suite:OLD_TAG
```

## Best Practices

1. **Use build triggers** for automatic builds on code changes
2. **Enable caching** to speed up subsequent builds
3. **Run security scans** on all production images
4. **Tag images** with both SHA and semantic versions
5. **Set appropriate timeouts** for different build complexities
6. **Monitor build costs** and optimize machine types
7. **Use worker pools** for builds requiring private network access
8. **Archive build artifacts** for debugging and compliance

## Resources

- [Google Cloud Build Documentation](https://cloud.google.com/build/docs)
- [Cloud Build Pricing](https://cloud.google.com/build/pricing)
- [Container Registry Documentation](https://cloud.google.com/container-registry/docs)
- [Trivy Security Scanner](https://github.com/aquasecurity/trivy)
- [Container Structure Tests](https://github.com/GoogleContainerTools/container-structure-test)

## Support

For issues with Cloud Build integration:
1. Check build logs: `gcloud builds log BUILD_ID`
2. Review cloudbuild.yaml syntax
3. Verify GCP permissions and quotas
4. Consult [Cloud Build Troubleshooting](https://cloud.google.com/build/docs/troubleshooting)
