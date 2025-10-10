# Getting Started with NiA-Enterprise

Welcome to NiA-Enterprise! This guide will help you get started quickly.

## What is NiA-Enterprise?

NiA-Enterprise is an enterprise-grade distributed clustering system that enables:
- **Secure Communication**: TLS/mTLS encryption and API key authentication
- **High Availability**: Multi-relay architecture with automatic failover
- **Scalability**: Auto-scaling support for handling thousands of nodes
- **Observability**: Built-in Prometheus metrics and Grafana dashboards
- **Production-Ready**: Kubernetes deployment, monitoring, and DR procedures

## Quick Start

### Prerequisites

- **Docker**: 20.10 or higher
- **Docker Compose**: 2.0 or higher (for development)
- **kubectl**: 1.24 or higher (for production)
- **Python**: 3.11 or higher (for local development)

### Option 1: Automated Setup

Run the setup script:
```bash
./setup.sh
```

Select your preferred option:
1. Development Setup (Docker Compose)
2. Production Setup (Kubernetes)
3. Generate Certificates
4. Install Python Dependencies

### Option 2: Manual Docker Compose Setup

```bash
# 1. Install Python dependencies
pip install -r requirements.txt

# 2. Build Docker image
docker build -t nia-enterprise:latest -f docker/Dockerfile.prod .

# 3. Start the cluster
cd docker
docker-compose -f docker-compose.prod.yml up -d

# 4. Verify services are running
docker-compose -f docker-compose.prod.yml ps

# 5. View logs
docker-compose -f docker-compose.prod.yml logs -f relay-primary
```

### Option 3: Manual Kubernetes Setup

```bash
# 1. Create namespace
kubectl create namespace nia-enterprise

# 2. Apply configurations
kubectl apply -f k8s/namespace.yaml
kubectl apply -f k8s/configmap.yaml
kubectl apply -f k8s/secrets.yaml

# 3. Deploy relay servers
kubectl apply -f k8s/relay-deployment.yaml
kubectl apply -f k8s/services.yaml

# 4. Deploy nodes
kubectl apply -f k8s/node-deployment.yaml

# 5. Verify deployment
kubectl get pods -n nia-enterprise
kubectl get services -n nia-enterprise

# 6. Check logs
kubectl logs -n nia-enterprise -l app=nia-relay -f
```

### Option 4: Local Python Development

```bash
# 1. Install dependencies
pip install -r requirements.txt

# 2. Start a relay server
python cluster_manager_enterprise.py \
  --mode relay \
  --cluster dev \
  --relay-port 4040 \
  --debug

# 3. In another terminal, start a node
python cluster_manager_enterprise.py \
  --mode node \
  --cluster dev \
  --node node1 \
  --relay-host localhost \
  --relay-port 4040 \
  --lan-port 5001 \
  --enable-ble \
  --debug

# 4. Start another node
python cluster_manager_enterprise.py \
  --mode node \
  --cluster dev \
  --node node2 \
  --relay-host localhost \
  --relay-port 4040 \
  --lan-port 5002 \
  --debug
```

## Verify Installation

### Check Health Endpoints

```bash
# Check relay health
curl http://localhost:8080/health

# Expected response:
# {
#   "status": "healthy",
#   "cluster": "production",
#   "nodes_connected": 2,
#   "uptime_seconds": 120,
#   "version": "1.0.0-enterprise"
# }
```

### Check Metrics

```bash
# Check Prometheus metrics
curl http://localhost:9090/metrics

# Access Grafana dashboards
# Open browser: http://localhost:3000
# Login: admin/admin
```

### View Logs

```bash
# Docker Compose
docker-compose -f docker/docker-compose.prod.yml logs -f

# Kubernetes
kubectl logs -n nia-enterprise -l app=nia-relay -f
kubectl logs -n nia-enterprise -l app=nia-node -f
```

## Configuration

### Enable TLS

```bash
# 1. Generate certificates
./scripts/generate-certs.sh

# 2. Start relay with TLS
python cluster_manager_enterprise.py \
  --mode relay \
  --cluster secure \
  --enable-tls \
  --tls-cert certs/server.crt \
  --tls-key certs/server.key

# 3. Connect node with TLS
python cluster_manager_enterprise.py \
  --mode node \
  --cluster secure \
  --node secure-node1 \
  --relay-host localhost \
  --relay-port 4040 \
  --lan-port 5001 \
  --enable-tls
```

### Enable API Key Authentication

```bash
# 1. Create API keys file
cat > config/api-keys.json <<EOF
{
  "node1": "sk_live_abc123def456",
  "node2": "sk_live_xyz789uvw012"
}
EOF

# 2. Start relay with API keys
python cluster_manager_enterprise.py \
  --mode relay \
  --cluster secure \
  --api-keys config/api-keys.json

# 3. Connect node with API key
python cluster_manager_enterprise.py \
  --mode node \
  --cluster secure \
  --node node1 \
  --relay-host localhost \
  --relay-port 4040 \
  --lan-port 5001 \
  --api-key sk_live_abc123def456
```

## Access Services

After deployment, access the following services:

### Development (Docker Compose)
- **Relay Primary**: http://localhost:4040
- **Relay Secondary**: http://localhost:4041
- **Grafana**: http://localhost:3000 (admin/admin)
- **Prometheus**: http://localhost:9092
- **HAProxy Stats**: http://localhost:8404/stats

### Production (Kubernetes)
- **Relay Service**: Depends on LoadBalancer/Ingress configuration
- **Grafana**: Depends on Ingress configuration
- **Prometheus**: Depends on Ingress configuration

Get service endpoints:
```bash
kubectl get services -n nia-enterprise
kubectl get ingress -n nia-enterprise
```

## Common Tasks

### Scale Nodes

```bash
# Kubernetes
kubectl scale deployment nia-node -n nia-enterprise --replicas=10

# Docker Compose
docker-compose -f docker/docker-compose.prod.yml up -d --scale node1=5
```

### View Connected Nodes

```bash
# Check relay logs
kubectl logs -n nia-enterprise -l app=nia-relay | grep "registered"

# Or use health endpoint
curl http://localhost:8080/health
```

### Backup Configuration

```bash
./scripts/backup.sh
```

### Restore from Backup

```bash
./scripts/restore.sh backups/nia-enterprise-backup-20240101_120000.tar.gz
```

## Monitoring

### Grafana Dashboards

1. Open Grafana: http://localhost:3000
2. Login with admin/admin
3. Navigate to Dashboards
4. Import pre-configured dashboards from `config/grafana/dashboards/`

### Prometheus Queries

Example queries:
```promql
# Number of connected nodes
nia_node_connections

# Message rate
rate(nia_messages_total[5m])

# Error rate
rate(nia_errors_total[5m]) / rate(nia_messages_total[5m])
```

## Troubleshooting

### Node Cannot Connect

```bash
# Check relay is running
kubectl get pods -n nia-enterprise -l app=nia-relay

# Check service
kubectl get svc -n nia-enterprise

# Check relay logs
kubectl logs -n nia-enterprise -l app=nia-relay

# Test connectivity
kubectl run -it --rm debug --image=busybox --restart=Never -- \
  nc -zv nia-relay-service 4040
```

### High Latency

```bash
# Check resource usage
kubectl top pods -n nia-enterprise

# Check HPA
kubectl get hpa -n nia-enterprise

# Scale manually if needed
kubectl scale deployment nia-relay -n nia-enterprise --replicas=5
```

### Certificate Issues

```bash
# Check certificate expiry
openssl x509 -in certs/server.crt -noout -dates

# Regenerate if needed
./scripts/generate-certs.sh
```

## Next Steps

1. **Read Documentation**
   - [Architecture Guide](docs/architecture.md)
   - [Security Guide](docs/security.md)
   - [Operations Manual](docs/operations.md)

2. **Configure Monitoring**
   - Set up Prometheus alerts
   - Configure Grafana dashboards
   - Set up PagerDuty/Slack integration

3. **Enable Security Features**
   - Generate production certificates
   - Configure API key authentication
   - Set up secret management (Vault/AWS Secrets Manager)

4. **Plan for Production**
   - Review [Disaster Recovery](docs/disaster-recovery.md) procedures
   - Set up automated backups
   - Configure CI/CD pipeline
   - Perform load testing

## Support

### Documentation
- **Main Docs**: [README.md](README.md)
- **Architecture**: [docs/architecture.md](docs/architecture.md)
- **Operations**: [docs/operations.md](docs/operations.md)
- **Security**: [docs/security.md](docs/security.md)
- **DR**: [docs/disaster-recovery.md](docs/disaster-recovery.md)

### Contact
- **Email**: support@nia-enterprise.io
- **Website**: https://nia-enterprise.io
- **Documentation**: https://docs.nia-enterprise.io
- **Status Page**: https://status.nia-enterprise.io

### Enterprise Support
- **24/7 Support**: +1-800-NIA-SUPPORT
- **Email**: enterprise@nia-enterprise.io
- **Slack**: Enterprise customers receive private Slack channel

## License

This software is licensed under the NiA-Enterprise License.
See [LICENSE](LICENSE) for details.

For enterprise licensing inquiries:
- Email: enterprise@nia-enterprise.io
- Phone: +1-800-NIA-LICENSE

---

**Ready to scale to enterprise?** 🚀

Start with the automated setup: `./setup.sh`
