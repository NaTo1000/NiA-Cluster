# Operations Manual

## Production Operations Guide

### Daily Operations

#### Health Checks
```bash
# Check relay status
kubectl get pods -n nia-enterprise -l app=nia-relay

# Check node status
kubectl get pods -n nia-enterprise -l app=nia-node

# View relay logs
kubectl logs -n nia-enterprise -l app=nia-relay --tail=100

# Check metrics
curl http://relay.nia-enterprise.io:8080/health
```

#### Monitoring
- Access Grafana: https://grafana.nia-enterprise.io
- Access Prometheus: https://prometheus.nia-enterprise.io
- Check alerts: Review Prometheus AlertManager

### Scaling Operations

#### Manual Scaling
```bash
# Scale relay instances
kubectl scale deployment nia-relay -n nia-enterprise --replicas=5

# Scale nodes
kubectl scale deployment nia-node -n nia-enterprise --replicas=10
```

#### Auto-Scaling Configuration
```bash
# Update HPA
kubectl edit hpa nia-relay-hpa -n nia-enterprise

# View current scaling
kubectl get hpa -n nia-enterprise
```

### Deployment Operations

#### Rolling Update
```bash
# Update image
kubectl set image deployment/nia-relay \
  relay=nia-enterprise:v1.1.0 \
  -n nia-enterprise

# Monitor rollout
kubectl rollout status deployment/nia-relay -n nia-enterprise

# Rollback if needed
kubectl rollout undo deployment/nia-relay -n nia-enterprise
```

#### Blue-Green Deployment
```bash
# Deploy green environment
kubectl apply -f k8s/green-deployment.yaml

# Verify green environment
kubectl get pods -n nia-enterprise -l version=green

# Switch traffic
kubectl patch service nia-relay-service -n nia-enterprise \
  -p '{"spec":{"selector":{"version":"green"}}}'

# Remove blue environment
kubectl delete -f k8s/blue-deployment.yaml
```

### Backup and Recovery

#### Manual Backup
```bash
# Run backup script
./scripts/backup.sh

# Verify backup
ls -lh backups/
```

#### Restore from Backup
```bash
# List available backups
ls backups/

# Restore
./scripts/restore.sh backups/nia-enterprise-backup-20240101_120000.tar.gz
```

#### Database Backup (if applicable)
```bash
# Export data
kubectl exec -n nia-enterprise postgres-0 -- pg_dump -U nia > backup.sql

# Import data
kubectl exec -i -n nia-enterprise postgres-0 -- psql -U nia < backup.sql
```

### Troubleshooting

#### Common Issues

**1. Node Cannot Connect to Relay**
```bash
# Check relay service
kubectl get svc -n nia-enterprise

# Check network policies
kubectl get networkpolicies -n nia-enterprise

# Verify DNS
kubectl run -it --rm debug --image=busybox --restart=Never -- nslookup nia-relay-service

# Check relay logs
kubectl logs -n nia-enterprise -l app=nia-relay
```

**2. High Latency**
```bash
# Check resource usage
kubectl top pods -n nia-enterprise

# Check HPA status
kubectl get hpa -n nia-enterprise

# View metrics in Grafana
# Look at p95/p99 latency graphs
```

**3. Memory Issues**
```bash
# Check memory usage
kubectl top pods -n nia-enterprise

# Increase memory limits
kubectl set resources deployment nia-relay -n nia-enterprise \
  --limits=memory=1Gi --requests=memory=512Mi

# Force restart
kubectl rollout restart deployment/nia-relay -n nia-enterprise
```

**4. Certificate Expiration**
```bash
# Check certificate expiry
openssl x509 -in certs/server.crt -noout -dates

# Renew certificate (cert-manager)
kubectl delete certificate nia-tls-secret -n nia-enterprise
kubectl apply -f k8s/certificates.yaml
```

### Maintenance Windows

#### Planned Maintenance
1. **Notify stakeholders** 24 hours in advance
2. **Create backup** before starting
3. **Enable maintenance mode** (optional)
4. **Perform updates**
5. **Verify functionality**
6. **Disable maintenance mode**
7. **Monitor for issues**

#### Emergency Maintenance
1. **Assess impact**
2. **Quick backup** if possible
3. **Apply fix**
4. **Verify**
5. **Document incident**

### Security Operations

#### Certificate Management
```bash
# Generate new certificates
./scripts/generate-certs.sh

# Update Kubernetes secrets
kubectl create secret tls nia-tls-secret \
  --cert=certs/server.crt \
  --key=certs/server.key \
  -n nia-enterprise \
  --dry-run=client -o yaml | kubectl apply -f -
```

#### API Key Rotation
```bash
# Generate new API keys
python -c "import secrets; print(secrets.token_urlsafe(32))"

# Update secrets
kubectl edit secret nia-secrets -n nia-enterprise

# Restart services to pickup new keys
kubectl rollout restart deployment -n nia-enterprise
```

#### Security Scanning
```bash
# Scan images for vulnerabilities
trivy image nia-enterprise:latest

# Scan Kubernetes manifests
kubesec scan k8s/*.yaml

# Check for CVEs
grype nia-enterprise:latest
```

### Performance Tuning

#### Optimize Relay Performance
```bash
# Increase connection pool
# Edit deployment environment variables
kubectl set env deployment/nia-relay \
  MAX_CONNECTIONS=20000 \
  -n nia-enterprise

# Tune kernel parameters (node level)
sysctl -w net.core.somaxconn=4096
sysctl -w net.ipv4.tcp_max_syn_backlog=4096
```

#### Database Optimization (if applicable)
```sql
-- Create indexes
CREATE INDEX idx_node_cluster ON nodes(cluster_name);
CREATE INDEX idx_message_timestamp ON messages(timestamp);

-- Analyze query performance
EXPLAIN ANALYZE SELECT * FROM nodes WHERE cluster_name = 'production';

-- Vacuum and analyze
VACUUM ANALYZE;
```

### Disaster Recovery

#### Recovery Procedures
See [Disaster Recovery Guide](disaster-recovery.md) for detailed procedures.

Quick recovery steps:
1. Assess damage
2. Restore from backup
3. Verify data integrity
4. Restart services
5. Validate functionality
6. Monitor closely

### Logging and Auditing

#### Access Logs
```bash
# View relay logs
kubectl logs -n nia-enterprise -l app=nia-relay -f

# Export logs
kubectl logs -n nia-enterprise -l app=nia-relay \
  --since=24h > relay-logs.txt
```

#### Audit Logs
```bash
# View security audit log
kubectl exec -n nia-enterprise relay-pod-xxx -- \
  cat /var/log/audit.log
```

### Capacity Planning

#### Monitoring Resource Usage
- Track CPU/Memory trends
- Monitor connection growth
- Analyze message throughput
- Review storage usage

#### Scaling Triggers
- **CPU** > 70% sustained: Add relay instances
- **Memory** > 80%: Increase limits or scale
- **Connection count** > 8000 per relay: Scale out
- **Latency** > 500ms p99: Investigate and scale

### Contact Information

#### On-Call Engineers
- Primary: oncall@nia-enterprise.io
- Secondary: oncall-backup@nia-enterprise.io
- Escalation: engineering-lead@nia-enterprise.io

#### Support Channels
- Slack: #nia-enterprise-ops
- Email: support@nia-enterprise.io
- Phone: 1-800-NIA-HELP

### Runbooks
- [Node Connection Issues](runbooks/node-connection.md)
- [High Latency Response](runbooks/high-latency.md)
- [Certificate Renewal](runbooks/cert-renewal.md)
- [Database Issues](runbooks/database.md)
