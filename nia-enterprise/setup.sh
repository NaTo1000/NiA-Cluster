#!/bin/bash
# Quick setup script for NiA-Enterprise

set -e

echo "================================================"
echo "  NiA-Enterprise Quick Setup"
echo "================================================"
echo ""

# Check prerequisites
echo "Checking prerequisites..."

# Check Docker
if ! command -v docker &> /dev/null; then
    echo "❌ Docker is not installed. Please install Docker first."
    exit 1
fi
echo "✓ Docker is installed"

# Check Docker Compose
if ! command -v docker-compose &> /dev/null && ! docker compose version &> /dev/null; then
    echo "❌ Docker Compose is not installed. Please install Docker Compose first."
    exit 1
fi
echo "✓ Docker Compose is installed"

# Check kubectl (optional)
if command -v kubectl &> /dev/null; then
    echo "✓ kubectl is installed"
else
    echo "⚠ kubectl not found (optional for K8s deployment)"
fi

echo ""
echo "================================================"
echo "  Setup Options"
echo "================================================"
echo ""
echo "1. Development Setup (Docker Compose)"
echo "2. Production Setup (Kubernetes)"
echo "3. Generate Certificates"
echo "4. Install Python Dependencies"
echo ""

read -p "Select option (1-4): " option

case $option in
    1)
        echo ""
        echo "Setting up Development Environment..."
        
        # Install Python dependencies
        echo "Installing Python dependencies..."
        pip install -r requirements.txt
        
        # Build Docker image
        echo "Building Docker image..."
        docker build -t nia-enterprise:latest -f docker/Dockerfile.prod .
        
        # Start services
        echo "Starting services with Docker Compose..."
        cd docker
        docker-compose -f docker-compose.prod.yml up -d
        
        echo ""
        echo "✓ Development environment is ready!"
        echo ""
        echo "Access points:"
        echo "  - Relay (Primary): http://localhost:4040"
        echo "  - Relay (Secondary): http://localhost:4041"
        echo "  - Grafana: http://localhost:3000 (admin/admin)"
        echo "  - Prometheus: http://localhost:9092"
        echo "  - HAProxy Stats: http://localhost:8404/stats"
        echo ""
        echo "View logs:"
        echo "  docker-compose -f docker/docker-compose.prod.yml logs -f"
        echo ""
        ;;
        
    2)
        echo ""
        echo "Setting up Production Environment (Kubernetes)..."
        
        if ! command -v kubectl &> /dev/null; then
            echo "❌ kubectl is required for Kubernetes deployment"
            exit 1
        fi
        
        # Create namespace
        echo "Creating namespace..."
        kubectl apply -f k8s/namespace.yaml
        
        # Apply configurations
        echo "Applying configurations..."
        kubectl apply -f k8s/configmap.yaml
        kubectl apply -f k8s/secrets.yaml
        
        # Deploy services
        echo "Deploying services..."
        kubectl apply -f k8s/relay-deployment.yaml
        kubectl apply -f k8s/node-deployment.yaml
        kubectl apply -f k8s/services.yaml
        
        # Wait for deployments
        echo "Waiting for deployments to be ready..."
        kubectl wait --for=condition=ready pod \
          -l app=nia-relay -n nia-enterprise --timeout=300s
        
        echo ""
        echo "✓ Production environment deployed!"
        echo ""
        echo "Check status:"
        echo "  kubectl get all -n nia-enterprise"
        echo ""
        echo "View logs:"
        echo "  kubectl logs -n nia-enterprise -l app=nia-relay -f"
        echo ""
        ;;
        
    3)
        echo ""
        echo "Generating TLS Certificates..."
        
        if ! command -v openssl &> /dev/null; then
            echo "❌ OpenSSL is required for certificate generation"
            exit 1
        fi
        
        ./scripts/generate-certs.sh
        
        echo ""
        echo "✓ Certificates generated in certs/ directory"
        echo ""
        ;;
        
    4)
        echo ""
        echo "Installing Python Dependencies..."
        
        if ! command -v pip &> /dev/null; then
            echo "❌ pip is not installed. Please install Python and pip first."
            exit 1
        fi
        
        pip install -r requirements.txt
        pip install -r requirements-prod.txt
        
        echo ""
        echo "✓ Python dependencies installed"
        echo ""
        echo "Run relay:"
        echo "  python cluster_manager_enterprise.py --mode relay --cluster test"
        echo ""
        echo "Run node:"
        echo "  python cluster_manager_enterprise.py --mode node --cluster test \\"
        echo "    --node node1 --relay-host localhost --relay-port 4040 --lan-port 5001"
        echo ""
        ;;
        
    *)
        echo "Invalid option"
        exit 1
        ;;
esac

echo "================================================"
echo "  Setup Complete!"
echo "================================================"
echo ""
echo "Next steps:"
echo "  - Review documentation in docs/"
echo "  - Configure monitoring (Prometheus/Grafana)"
echo "  - Set up backups"
echo "  - Review security settings"
echo ""
echo "For help, visit: https://docs.nia-enterprise.io"
echo ""
