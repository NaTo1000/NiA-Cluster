# Makefile for NiA-Cluster Cloud Build operations
# Provides convenient commands for building and deploying with Google Cloud Build

.PHONY: help cloud-build-root cloud-build-enterprise cloud-build-both local-build-root local-build-enterprise docker-build docker-test clean

# Default target
.DEFAULT_GOAL := help

# Variables
PROJECT_ID ?= $(shell gcloud config get-value project 2>/dev/null)
GKE_CLUSTER ?= nia-cluster
GKE_REGION ?= us-central1
CLUSTER_NAME ?= myfleet
RELAY_PORT ?= 4040

help: ## Show this help message
	@echo "NiA-Cluster Cloud Build Commands"
	@echo "================================="
	@echo ""
	@echo "Usage: make [target]"
	@echo ""
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "  \033[36m%-25s\033[0m %s\n", $$1, $$2}'
	@echo ""
	@echo "Environment Variables:"
	@echo "  PROJECT_ID    - GCP Project ID (current: $(PROJECT_ID))"
	@echo "  GKE_CLUSTER   - GKE cluster name (default: nia-cluster)"
	@echo "  GKE_REGION    - GKE region (default: us-central1)"
	@echo "  CLUSTER_NAME  - Cluster name (default: myfleet)"
	@echo "  RELAY_PORT    - Relay port (default: 4040)"

cloud-build-root: ## Submit root project to Cloud Build
	@if [ -z "$(PROJECT_ID)" ]; then \
		echo "ERROR: PROJECT_ID not set. Run: make cloud-build-root PROJECT_ID=your-project"; \
		exit 1; \
	fi
	@echo "Submitting cluster-suite build to Cloud Build..."
	gcloud builds submit \
		--config=cloudbuild.yaml \
		--substitutions=_CLUSTER_NAME=$(CLUSTER_NAME),_RELAY_PORT=$(RELAY_PORT) \
		--project=$(PROJECT_ID) \
		.

cloud-build-enterprise: ## Submit nia-enterprise to Cloud Build
	@if [ -z "$(PROJECT_ID)" ]; then \
		echo "ERROR: PROJECT_ID not set. Run: make cloud-build-enterprise PROJECT_ID=your-project"; \
		exit 1; \
	fi
	@echo "Submitting nia-enterprise build to Cloud Build..."
	gcloud builds submit \
		--config=cloudbuild.yaml \
		--substitutions=_CLUSTER_NAME=production,_ENABLE_DEPLOYMENT=false \
		--project=$(PROJECT_ID) \
		./nia-enterprise

cloud-build-both: cloud-build-root cloud-build-enterprise ## Submit both projects to Cloud Build

cloud-deploy-enterprise: ## Build and deploy nia-enterprise to GKE
	@if [ -z "$(PROJECT_ID)" ]; then \
		echo "ERROR: PROJECT_ID not set. Run: make cloud-deploy-enterprise PROJECT_ID=your-project"; \
		exit 1; \
	fi
	@echo "Building and deploying nia-enterprise to GKE..."
	gcloud builds submit \
		--config=cloudbuild.yaml \
		--substitutions=_CLUSTER_NAME=production,_ENABLE_DEPLOYMENT=true,_GKE_CLUSTER=$(GKE_CLUSTER),_GKE_REGION=$(GKE_REGION) \
		--project=$(PROJECT_ID) \
		./nia-enterprise

local-build-root: ## Test cloud build locally (root)
	@echo "Testing root cloud build locally..."
	./build-cloud-local.sh root

local-build-enterprise: ## Test cloud build locally (enterprise)
	@echo "Testing enterprise cloud build locally..."
	./build-cloud-local.sh enterprise

docker-build: ## Build Docker images locally
	@echo "Building cluster-suite locally..."
	docker build -t cluster-suite:latest .
	@echo ""
	@echo "Building nia-enterprise locally..."
	docker build -f nia-enterprise/docker/Dockerfile.prod -t nia-enterprise:latest ./nia-enterprise

docker-test: ## Run local Docker tests
	@echo "Running tests..."
	./test.sh

docker-run-relay: ## Run relay server locally
	docker run --rm --name cluster_relay cluster-suite:latest \
		--mode relay --cluster $(CLUSTER_NAME) --relay-port $(RELAY_PORT)

docker-compose-up: ## Start cluster with docker-compose
	docker compose up --build

docker-compose-down: ## Stop cluster
	docker compose down

cloud-list-builds: ## List recent cloud builds
	@if [ -z "$(PROJECT_ID)" ]; then \
		echo "ERROR: PROJECT_ID not set"; \
		exit 1; \
	fi
	gcloud builds list --limit=10 --project=$(PROJECT_ID)

cloud-logs: ## View logs for latest build (use BUILD_ID=xxx for specific build)
	@if [ -z "$(PROJECT_ID)" ]; then \
		echo "ERROR: PROJECT_ID not set"; \
		exit 1; \
	fi
	@if [ -z "$(BUILD_ID)" ]; then \
		echo "Showing logs for latest build..."; \
		BUILD_ID=$$(gcloud builds list --limit=1 --format="value(id)" --project=$(PROJECT_ID)); \
	fi; \
	gcloud builds log $$BUILD_ID --project=$(PROJECT_ID)

cloud-cancel: ## Cancel a build (use BUILD_ID=xxx)
	@if [ -z "$(PROJECT_ID)" ] || [ -z "$(BUILD_ID)" ]; then \
		echo "ERROR: PROJECT_ID and BUILD_ID required. Usage: make cloud-cancel PROJECT_ID=xxx BUILD_ID=yyy"; \
		exit 1; \
	fi
	gcloud builds cancel $(BUILD_ID) --project=$(PROJECT_ID)

cloud-images: ## List container images
	@if [ -z "$(PROJECT_ID)" ]; then \
		echo "ERROR: PROJECT_ID not set"; \
		exit 1; \
	fi
	@echo "Cluster-suite images:"
	gcloud container images list-tags gcr.io/$(PROJECT_ID)/cluster-suite --limit=10 --project=$(PROJECT_ID) 2>/dev/null || echo "No cluster-suite images found"
	@echo ""
	@echo "NiA-Enterprise images:"
	gcloud container images list-tags gcr.io/$(PROJECT_ID)/nia-enterprise --limit=10 --project=$(PROJECT_ID) 2>/dev/null || echo "No nia-enterprise images found"

setup-gcp: ## Setup GCP project (enable APIs, etc.)
	@if [ -z "$(PROJECT_ID)" ]; then \
		echo "ERROR: PROJECT_ID not set. Run: make setup-gcp PROJECT_ID=your-project"; \
		exit 1; \
	fi
	@echo "Setting up GCP project: $(PROJECT_ID)"
	gcloud config set project $(PROJECT_ID)
	@echo "Enabling required APIs..."
	gcloud services enable cloudbuild.googleapis.com --project=$(PROJECT_ID)
	gcloud services enable containerregistry.googleapis.com --project=$(PROJECT_ID)
	gcloud services enable container.googleapis.com --project=$(PROJECT_ID)
	@echo "Setup complete!"

clean: ## Clean up local Docker resources
	@echo "Cleaning up Docker resources..."
	docker system prune -f
	docker volume prune -f

clean-cloud-images: ## Clean up old cloud images (use DAYS=30 to change retention)
	@if [ -z "$(PROJECT_ID)" ]; then \
		echo "ERROR: PROJECT_ID not set"; \
		exit 1; \
	fi
	@DAYS=${DAYS:-30}; \
	echo "Deleting images older than $$DAYS days..."; \
	for image in cluster-suite nia-enterprise; do \
		echo "Processing gcr.io/$(PROJECT_ID)/$$image..."; \
		gcloud container images list-tags gcr.io/$(PROJECT_ID)/$$image \
			--filter="timestamp.datetime<-P$${DAYS}D" \
			--format="get(digest)" \
			--limit=50 \
			--project=$(PROJECT_ID) 2>/dev/null | \
		while read digest; do \
			if [ -n "$$digest" ]; then \
				echo "Deleting gcr.io/$(PROJECT_ID)/$$image@$$digest"; \
				gcloud container images delete "gcr.io/$(PROJECT_ID)/$$image@$$digest" --quiet --project=$(PROJECT_ID); \
			fi; \
		done; \
	done

verify: ## Verify problem statement commands
	./verify-problem-statement.sh

.PHONY: setup-triggers
setup-triggers: ## Setup Cloud Build triggers for GitHub
	@if [ -z "$(PROJECT_ID)" ]; then \
		echo "ERROR: PROJECT_ID not set"; \
		exit 1; \
	fi
	@echo "Creating Cloud Build triggers..."
	gcloud builds triggers create github \
		--repo-name=NiA-Cluster \
		--repo-owner=NaTo1000 \
		--branch-pattern="^main$$" \
		--build-config=cloudbuild.yaml \
		--description="Build cluster-suite on main branch" \
		--project=$(PROJECT_ID) || echo "Trigger may already exist"
	gcloud builds triggers create github \
		--repo-name=NiA-Cluster \
		--repo-owner=NaTo1000 \
		--branch-pattern="^main$$" \
		--build-config=nia-enterprise/cloudbuild.yaml \
		--included-files="nia-enterprise/**" \
		--description="Build nia-enterprise on main branch changes" \
		--project=$(PROJECT_ID) || echo "Trigger may already exist"
	@echo "Triggers created successfully!"
