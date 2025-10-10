# NiA-Enterprise Quick Reference

## 🚀 Quick Start Commands

### Development Setup
```bash
cd nia-enterprise
./setup.sh
# Select option 1 for development
```

### Docker Compose
```bash
cd nia-enterprise
docker build -t nia-enterprise:latest -f docker/Dockerfile.prod .
cd docker
docker-compose -f docker-compose.prod.yml up -d
```

### Kubernetes
```bash
cd nia-enterprise
kubectl apply -f k8s/
kubectl get pods -n nia-enterprise
```

### Local Python
```bash
cd nia-enterprise
pip install -r requirements.txt

# Terminal 1: Start relay
python cluster_manager_enterprise.py --mode relay --cluster dev --relay-port 4040

# Terminal 2: Start node
python cluster_manager_enterprise.py --mode node --cluster dev --node node1 \
  --relay-host localhost --relay-port 4040 --lan-port 5001 --enable-ble
```

## 📋 Common Commands

### View Logs
```bash
# Docker Compose
docker-compose -f docker/docker-compose.prod.yml logs -f relay-primary

# Kubernetes
kubectl logs -n nia-enterprise -l app=nia-relay -f
```

### Check Health
```bash
curl http://localhost:8080/health
```

### Check Metrics
```bash
curl http://localhost:9090/metrics
```

### Scale Services
```bash
# Kubernetes
kubectl scale deployment nia-relay -n nia-enterprise --replicas=5
kubectl scale deployment nia-node -n nia-enterprise --replicas=10
```

### Backup & Restore
```bash
./scripts/backup.sh
./scripts/restore.sh backups/latest.tar.gz
```

## 🔑 Important Files

| File | Purpose |
|------|---------|
| `README.md` | Main documentation |
| `GETTING_STARTED.md` | Quick start guide |
| `cluster_manager_enterprise.py` | Main application |
| `setup.sh` | Automated setup |
| `docker/docker-compose.prod.yml` | Production stack |
| `k8s/*.yaml` | Kubernetes manifests |
| `docs/` | Detailed documentation |

## 🌐 Access URLs (Docker Compose)

| Service | URL | Credentials |
|---------|-----|-------------|
| Relay Primary | http://localhost:4040 | - |
| Relay Secondary | http://localhost:4041 | - |
| Health Check | http://localhost:8080/health | - |
| Metrics | http://localhost:9090/metrics | - |
| Grafana | http://localhost:3000 | admin/admin |
| Prometheus | http://localhost:9092 | - |
| HAProxy Stats | http://localhost:8404/stats | - |

## 🔒 Security Features

### Enable TLS
```bash
./scripts/generate-certs.sh
python cluster_manager_enterprise.py --mode relay --cluster secure \
  --enable-tls --tls-cert certs/server.crt --tls-key certs/server.key
```

### Use API Keys
```bash
# Create api-keys.json
echo '{"node1": "sk_live_abc123"}' > config/api-keys.json

# Start relay
python cluster_manager_enterprise.py --mode relay --cluster secure \
  --api-keys config/api-keys.json

# Connect node
python cluster_manager_enterprise.py --mode node --cluster secure \
  --node node1 --relay-host localhost --relay-port 4040 \
  --lan-port 5001 --api-key sk_live_abc123
```

## 📊 Monitoring

### Prometheus Queries
```promql
# Connected nodes
nia_node_connections

# Message rate
rate(nia_messages_total[5m])

# Error rate
rate(nia_errors_total[5m])
```

### View Grafana Dashboards
1. Open http://localhost:3000
2. Login: admin/admin
3. Browse dashboards

## 🛠️ Troubleshooting

### Node can't connect
```bash
# Check relay is running
kubectl get pods -n nia-enterprise
docker ps | grep relay

# Check logs
kubectl logs -n nia-enterprise -l app=nia-relay
docker logs relay-primary
```

### High latency
```bash
# Check resource usage
kubectl top pods -n nia-enterprise

# Scale up
kubectl scale deployment nia-relay -n nia-enterprise --replicas=5
```

### Certificate issues
```bash
# Check expiry
openssl x509 -in certs/server.crt -noout -dates

# Regenerate
./scripts/generate-certs.sh
```

## 📚 Documentation

| Document | Description |
|----------|-------------|
| [README.md](README.md) | Main documentation |
| [GETTING_STARTED.md](GETTING_STARTED.md) | Quick start guide |
| [docs/architecture.md](docs/architecture.md) | System architecture |
| [docs/operations.md](docs/operations.md) | Operations manual |
| [docs/security.md](docs/security.md) | Security guide |
| [docs/disaster-recovery.md](docs/disaster-recovery.md) | DR procedures |

## 🆘 Support

- Email: support@nia-enterprise.io
- Docs: https://docs.nia-enterprise.io
- Status: https://status.nia-enterprise.io

---

**Need help?** Check the full documentation in the `docs/` directory or run `./setup.sh` for guided setup.
