# NiA-Enterprise

Enterprise-grade distributed clustering system with advanced security, monitoring, and high availability features.

## Overview

NiA-Enterprise is a production-ready, enterprise-grade version of the NiA-Cluster system. It provides a robust, scalable, and secure platform for managing distributed node clusters with advanced features for enterprise deployments.

## Key Enterprise Features

### 🔒 Security & Authentication
- **mTLS Support**: Mutual TLS authentication between relay and nodes
- **API Key Management**: Secure API key authentication system
- **Role-Based Access Control (RBAC)**: Fine-grained permission management
- **Audit Logging**: Comprehensive audit trails for compliance
- **Secret Management**: Integration with HashiCorp Vault and AWS Secrets Manager

### 📊 Monitoring & Observability
- **Prometheus Metrics**: Comprehensive metrics export
- **Grafana Dashboards**: Pre-built monitoring dashboards
- **Distributed Tracing**: OpenTelemetry integration
- **Log Aggregation**: ELK/Loki stack integration
- **Health Checks**: Advanced health monitoring endpoints

### 🚀 High Availability & Scalability
- **Multi-Relay Architecture**: Active-active relay configuration
- **Auto-Scaling**: Kubernetes HPA support
- **Load Balancing**: Built-in load balancing with service mesh support
- **Failover**: Automatic failover and recovery mechanisms
- **Zero-Downtime Deployments**: Rolling updates and blue-green deployments

### ⚡ Performance Optimization
- **Packet Sharding**: High-performance packet fragmentation for large messages
- **Double Packet Shuffle**: Optimized transmission ordering for burst error protection
- **Quantum Superposition Optimization**: Quantum-inspired probabilistic routing for optimal path selection
- **Parallel Processing**: Efficient concurrent shard handling
- **Adaptive Routing**: Performance-based route optimization through measurement feedback

### 🛠️ Operations & Management
- **Configuration Management**: Centralized configuration with hot-reload
- **Backup & Restore**: Automated backup solutions
- **Disaster Recovery**: Comprehensive DR procedures
- **Multi-Environment Support**: Dev, staging, production environments
- **GitOps Ready**: Integration with ArgoCD and Flux

### 📦 Deployment Options
- **Kubernetes**: Production-ready Kubernetes manifests
- **Docker Swarm**: High-availability swarm configuration
- **Cloud-Native**: AWS ECS, GCP Cloud Run, Azure Container Instances
- **On-Premise**: Traditional VM and bare-metal deployment guides

## Quick Start

### Prerequisites
- Docker 20.10+
- Kubernetes 1.24+ (for K8s deployment)
- Helm 3.0+ (optional)
- kubectl configured with cluster access

### Option 1: Docker Compose (Development)
```bash
cd docker
docker-compose up -d
```

### Option 2: Kubernetes (Production)
```bash
# Create namespace
kubectl create namespace nia-enterprise

# Apply configurations
kubectl apply -f k8s/namespace.yaml
kubectl apply -f k8s/configmap.yaml
kubectl apply -f k8s/secrets.yaml
kubectl apply -f k8s/relay-deployment.yaml
kubectl apply -f k8s/node-deployment.yaml
kubectl apply -f k8s/services.yaml
kubectl apply -f k8s/ingress.yaml

# Verify deployment
kubectl get pods -n nia-enterprise
```

### Option 2b: Google Cloud Build (Kubernetes Deployment)
```bash
# Build and deploy to GKE with Cloud Build
cd ..
./submit-cloud-build.sh enterprise YOUR_PROJECT_ID

# Or use Makefile
make cloud-deploy-enterprise PROJECT_ID=YOUR_PROJECT_ID GKE_CLUSTER=nia-cluster

# Or direct gcloud command with deployment enabled
gcloud builds submit \
  --config=cloudbuild.yaml \
  --substitutions=_ENABLE_DEPLOYMENT=true,_GKE_CLUSTER=nia-cluster,_GKE_REGION=us-central1 \
  ./nia-enterprise
```

See [../CLOUD_BUILD.md](../CLOUD_BUILD.md) for complete Cloud Build documentation.

### Option 3: Helm Chart
```bash
helm repo add nia-enterprise https://charts.nia-enterprise.io
helm install my-cluster nia-enterprise/nia-enterprise \
  --namespace nia-enterprise \
  --create-namespace \
  --values values.yaml
```

## Architecture

### Production Architecture
```
┌─────────────────────────────────────────────────────────┐
│                    Load Balancer                        │
│                  (Ingress/HAProxy)                      │
└────────────┬────────────────────────┬───────────────────┘
             │                        │
    ┌────────▼────────┐      ┌───────▼────────┐
    │  Relay Primary  │◄────►│ Relay Secondary │
    │  (Active)       │      │  (Active)       │
    └────┬────────────┘      └────────┬────────┘
         │                            │
         │    ┌───────────────────────┘
         │    │
    ┌────▼────▼────────────────────────────┐
    │         Node Pool (Auto-Scaled)       │
    │  ┌─────┐  ┌─────┐  ┌─────┐  ┌─────┐ │
    │  │Node1│  │Node2│  │Node3│  │NodeN│ │
    │  └─────┘  └─────┘  └─────┘  └─────┘ │
    └───────────────────────────────────────┘
              │
    ┌─────────▼──────────┐
    │   Monitoring Stack  │
    │  Prometheus+Grafana │
    └─────────────────────┘
```

## Configuration

### Environment Variables
```bash
# Relay Configuration
RELAY_PORT=4040
RELAY_MODE=production
ENABLE_TLS=true
TLS_CERT_PATH=/certs/server.crt
TLS_KEY_PATH=/certs/server.key

# Authentication
AUTH_ENABLED=true
API_KEY_REQUIRED=true
VAULT_ADDR=https://vault.example.com

# Monitoring
METRICS_ENABLED=true
METRICS_PORT=9090
TRACING_ENABLED=true
JAEGER_ENDPOINT=http://jaeger:14268/api/traces

# High Availability
HA_ENABLED=true
PEER_RELAY_HOSTS=relay-2:4040,relay-3:4040
HEALTH_CHECK_INTERVAL=10s

# Packet Sharding (Quantum Optimization)
ENABLE_SHARDING=true
SHARD_SIZE=1024
SHUFFLE_BLOCK_SIZE=8
```

### Configuration Files
See `config/` directory for:
- `relay.yaml` - Relay server configuration
- `node.yaml` - Node configuration template
- `monitoring.yaml` - Monitoring and alerting rules
- `security.yaml` - Security policies and rules

## Security

### TLS/mTLS Setup
```bash
# Generate certificates
./scripts/generate-certs.sh

# Configure mTLS
export ENABLE_MTLS=true
export CA_CERT_PATH=/certs/ca.crt
```

### Authentication Methods
1. **API Keys**: Static API keys for service accounts
2. **JWT Tokens**: Dynamic token-based authentication
3. **Client Certificates**: Certificate-based authentication
4. **OIDC Integration**: OAuth2/OIDC for user authentication

### Security Best Practices
- All communications encrypted with TLS 1.3
- Regular security updates and vulnerability scanning
- Network segmentation with security groups
- Principle of least privilege for all components
- Secrets stored in external secret managers

## Monitoring & Alerting

### Metrics Available
- Relay: connection count, message throughput, latency
- Nodes: registration status, health, resource usage
- System: CPU, memory, network I/O
- Sharding: shards processed, packets reformed, quantum optimization statistics

### Pre-configured Alerts
- Relay unavailability
- Node connection failures
- High error rates
- Resource exhaustion
- Certificate expiration

### Grafana Dashboards
Access dashboards at: http://grafana:3000
- Cluster Overview
- Relay Performance
- Node Health
- System Resources
- Error Analysis

## High Availability

### Relay Clustering
Multiple relay servers in active-active configuration:
```bash
# Start primary relay
docker run -d --name relay-1 \
  -e HA_ENABLED=true \
  -e PEER_RELAYS=relay-2:4040 \
  nia-enterprise:latest relay

# Start secondary relay
docker run -d --name relay-2 \
  -e HA_ENABLED=true \
  -e PEER_RELAYS=relay-1:4040 \
  nia-enterprise:latest relay
```

### Auto-Scaling
Kubernetes HPA configuration included for automatic scaling based on:
- CPU utilization
- Memory usage
- Custom metrics (connection count)

## Packet Sharding & Quantum Optimization

NiA-Enterprise includes an advanced packet sharding system with quantum-inspired optimization for maximum transmission efficiency.

### How It Works

1. **Packet Sharding**: Large messages are broken into smaller shards for efficient transmission
2. **Double Packet Shuffle**: 
   - Phase 1: Interleaves shards using matrix transposition for burst error protection
   - Phase 2: Applies quantum-optimized reordering for parallel processing efficiency
3. **Quantum Superposition Optimization**: Uses probability amplitudes to maintain multiple potential routing paths, collapsing to optimal choices based on measured performance

### Configuration Options

```bash
# Enable/disable sharding (enabled by default)
--enable-sharding
--disable-sharding

# Shard size in bytes (default: 1024)
--shard-size 1024

# Shuffle block size for double shuffle algorithm (default: 8)
--shuffle-block-size 8
```

### Example Usage

```python
from packet_sharding import PacketShardManager, create_sharding_system

# Create a sharding system
manager = create_sharding_system(shard_size=1024, shuffle_block_size=8)

# Shard a large packet
data = b"Your large message data here..."
shards = manager.shard_packet(data, priority=1)

# Prepare for optimized transmission
prepared_shards = manager.prepare_for_transmission(shards)

# Send shards and receive at destination
for shard in prepared_shards:
    reformed_data = manager.receive_shard(shard)
    if reformed_data:
        print(f"Complete packet received: {len(reformed_data)} bytes")
```

### Performance Benefits

- **Reduced Latency**: Smaller shards allow for parallel transmission
- **Error Resilience**: Interleaved shards protect against burst errors
- **Optimal Routing**: Quantum optimization learns and adapts to network conditions
- **Efficient Reassembly**: Out-of-order shard reception is fully supported

## Backup & Disaster Recovery

### Automated Backups
```bash
# Manual backup
./scripts/backup.sh

# Restore from backup
./scripts/restore.sh backup-2024-01-01.tar.gz
```

### Disaster Recovery Procedure
See `docs/disaster-recovery.md` for detailed DR procedures.

## Development

### Local Development Setup
```bash
# Install dependencies
pip install -r requirements.txt
pip install -r requirements-dev.txt

# Run tests
pytest tests/

# Run linters
flake8 src/
black src/
mypy src/
```

### Building Images
```bash
# Build production image
docker build -t nia-enterprise:latest -f docker/Dockerfile.prod .

# Build development image
docker build -t nia-enterprise:dev -f docker/Dockerfile.dev .
```

## Testing

### Unit Tests
```bash
pytest tests/unit/
```

### Integration Tests
```bash
pytest tests/integration/
```

### Load Testing
```bash
./scripts/load-test.sh
```

### Security Testing
```bash
./scripts/security-scan.sh
```

## Deployment

### CI/CD Pipeline
GitHub Actions workflows provided for:
- Automated testing
- Security scanning
- Docker image building and pushing
- Kubernetes deployment
- Release automation

### Production Deployment Checklist
- [ ] Review security configuration
- [ ] Configure backup schedules
- [ ] Set up monitoring and alerts
- [ ] Test disaster recovery procedures
- [ ] Configure auto-scaling policies
- [ ] Review network security groups
- [ ] Set up log aggregation
- [ ] Configure certificate renewal
- [ ] Document runbooks
- [ ] Train operations team

## Documentation

### Available Documentation
- [Architecture Guide](docs/architecture.md)
- [Security Guide](docs/security.md)
- [Operations Manual](docs/operations.md)
- [API Reference](docs/api-reference.md)
- [Troubleshooting Guide](docs/troubleshooting.md)
- [Disaster Recovery](docs/disaster-recovery.md)
- [Upgrade Guide](docs/upgrade-guide.md)
- [Contributing Guidelines](docs/contributing.md)

## Support & SLA

### Enterprise Support
- 24/7 support hotline
- Dedicated support engineer
- 1-hour response time for critical issues
- Quarterly business reviews
- Custom feature development

### Service Level Agreement
- 99.95% uptime guarantee
- < 100ms response time (p95)
- < 1s end-to-end latency (p99)
- Recovery Time Objective (RTO): 15 minutes
- Recovery Point Objective (RPO): 5 minutes

## License

Enterprise License with commercial support.
Contact: enterprise@nia-cluster.io

## Contact

- Website: https://nia-enterprise.io
- Email: support@nia-enterprise.io
- Documentation: https://docs.nia-enterprise.io
- Status Page: https://status.nia-enterprise.io

---

Built with ❤️ for Enterprise Scale
