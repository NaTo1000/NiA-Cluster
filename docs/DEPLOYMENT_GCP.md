# Deploying NiA-Cluster to Google Cloud (GCR + Cloud Run)

This document explains how to configure GitHub Actions to build, push, and deploy NiA-Cluster to Google Cloud Run using a service account.

1) Create a GCP service account
- In the Google Cloud Console, create a service account (e.g., nia-cluster-deploy).
- Grant the following roles to the service account:
  - Cloud Run Admin (roles/run.admin)
  - Storage Admin (roles/storage.admin) OR Artifact Registry Writer if you use Artifact Registry
  - Service Account User (roles/iam.serviceAccountUser)

2) Create and download a JSON key for the service account
- Save the JSON file locally. Do not commit it to the repository.

3) Add secrets to the GitHub repository
- Go to Settings → Secrets and variables → Actions → New repository secret
- Add the following secrets:
  - GCP_SA_KEY -> contents of the service account JSON (paste whole JSON)
  - GCP_PROJECT -> your GCP project id (string)
  - GCP_REGION -> e.g., us-central1

4) Trigger the workflow
- Push to the main branch to run the workflow which builds, pushes and deploys the image.

Contact: natfunkycat@gmail.com (as requested)

Notes:
- Cloud Run is intended for request-driven HTTP services. If NiA-Cluster is a long-running background service with no HTTP, consider using GCE/GKE or running this container on a VM or GKE instead. You can adapt the workflow to push to Artifact Registry or to push images and then run on GKE/ECS.
- Keep secrets out of the repo. Use Secret Manager and GitHub secrets as indicated above.
