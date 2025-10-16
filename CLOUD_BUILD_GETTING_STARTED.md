# Getting Started with Cloud Build

Quick guide to start using Google Cloud Build with NiA-Cluster in 5 minutes.

## Prerequisites

1. A Google Cloud Platform (GCP) account
2. A GCP project with billing enabled
3. Terminal access with bash

## Step 1: Install Google Cloud SDK (2 minutes)

```bash
# Linux/macOS
curl https://sdk.cloud.google.com | bash
exec -l $SHELL

# Or visit: https://cloud.google.com/sdk/docs/install
```

## Step 2: Authenticate and Setup (1 minute)

```bash
# Login to GCP
gcloud auth login

# Set your project (replace YOUR_PROJECT_ID)
gcloud config set project YOUR_PROJECT_ID

# Enable required APIs
gcloud services enable cloudbuild.googleapis.com
gcloud services enable containerregistry.googleapis.com
```

## Step 3: Submit Your First Build (2 minutes)

### Option A: Using Helper Script (Recommended)

```bash
# Build the cluster-suite image
./submit-cloud-build.sh root YOUR_PROJECT_ID
```

### Option B: Using Makefile

```bash
# Build the cluster-suite image
make cloud-build-root PROJECT_ID=YOUR_PROJECT_ID
```

### Option C: Direct gcloud Command

```bash
# Build the cluster-suite image
gcloud builds submit --config=cloudbuild.yaml .
```

## Step 4: View Your Build

```bash
# List recent builds
gcloud builds list --limit=5

# View build logs (replace BUILD_ID with actual ID from above)
gcloud builds log BUILD_ID
```

## What Just Happened?

Your code was:
1. ✅ Uploaded to Google Cloud Build
2. ✅ Built in a containerized VM environment
3. ✅ Tested automatically
4. ✅ Pushed to Google Container Registry
5. ✅ Ready to deploy anywhere

## Next Steps

### Pull Your Built Image

```bash
# Get your image
docker pull gcr.io/YOUR_PROJECT_ID/cluster-suite:latest

# Run it locally
docker run --rm gcr.io/YOUR_PROJECT_ID/cluster-suite:latest --help
```

### Build the Enterprise Version

```bash
./submit-cloud-build.sh enterprise YOUR_PROJECT_ID
```

### Setup Automatic Builds

```bash
# Create build triggers for automatic CI/CD
make setup-triggers PROJECT_ID=YOUR_PROJECT_ID
```

### Deploy to Kubernetes

```bash
# Build and deploy to GKE in one command
make cloud-deploy-enterprise PROJECT_ID=YOUR_PROJECT_ID GKE_CLUSTER=your-cluster
```

## Common Commands

```bash
# View all available commands
make help

# List built images
make cloud-images PROJECT_ID=YOUR_PROJECT_ID

# View build logs
make cloud-logs PROJECT_ID=YOUR_PROJECT_ID

# Build both projects
make cloud-build-both PROJECT_ID=YOUR_PROJECT_ID

# Clean up old images (older than 30 days)
make clean-cloud-images PROJECT_ID=YOUR_PROJECT_ID DAYS=30
```

## Troubleshooting

### "gcloud: command not found"
```bash
# Install Google Cloud SDK
curl https://sdk.cloud.google.com | bash
```

### "Permission denied"
```bash
# Make sure you're authenticated
gcloud auth login
```

### "API not enabled"
```bash
# Enable required APIs
gcloud services enable cloudbuild.googleapis.com containerregistry.googleapis.com
```

### "Project not set"
```bash
# Set your project
gcloud config set project YOUR_PROJECT_ID
```

## Cost Information

- **Free tier**: 120 build-minutes per day
- **Additional usage**: ~$0.003 per build-minute
- **Storage**: Container Registry storage costs apply

Typical build times:
- cluster-suite: ~2-3 minutes
- nia-enterprise: ~4-6 minutes

## Learn More

- **Comprehensive Guide**: [CLOUD_BUILD.md](CLOUD_BUILD.md)
- **Quick Reference**: [CLOUD_BUILD_QUICK_REF.md](CLOUD_BUILD_QUICK_REF.md)
- **Official Docs**: https://cloud.google.com/build/docs

## Support

- Use `make help` for available commands
- Check `CLOUD_BUILD.md` for detailed documentation
- Visit Google Cloud Build docs for platform-specific help

---

**You're ready to go!** Start building in the cloud with fast, containerized builds. 🚀
