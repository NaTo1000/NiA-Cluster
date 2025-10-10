# Disaster Recovery Plan

## Overview

This document outlines the disaster recovery procedures for NiA-Enterprise.

## Recovery Objectives

- **RTO (Recovery Time Objective)**: 15 minutes
- **RPO (Recovery Point Objective)**: 5 minutes
- **Availability Target**: 99.95%

## Disaster Scenarios

### 1. Single Relay Failure

**Impact**: Minimal - Load balancer redirects to healthy relay

**Recovery Steps**:
```bash
# 1. Verify other relays are healthy
kubectl get pods -n nia-enterprise -l app=nia-relay

# 2. Check HPA will auto-scale
kubectl get hpa -n nia-enterprise

# 3. Monitor node reconnections
kubectl logs -n nia-enterprise -l app=nia-node
```

**Expected Recovery Time**: < 1 minute (automatic)

### 2. Complete Relay Cluster Failure

**Impact**: High - All nodes disconnected

**Recovery Steps**:
```bash
# 1. Check cluster status
kubectl get nodes
kubectl get pods -n nia-enterprise

# 2. Restore from backup if needed
./scripts/restore.sh backups/latest.tar.gz

# 3. Restart relay deployment
kubectl rollout restart deployment/nia-relay -n nia-enterprise

# 4. Wait for relays to be ready
kubectl wait --for=condition=ready pod \
  -l app=nia-relay -n nia-enterprise --timeout=300s

# 5. Verify nodes reconnect
kubectl logs -n nia-enterprise -l app=nia-relay | grep "registered"
```

**Expected Recovery Time**: 5-10 minutes

### 3. Kubernetes Cluster Failure

**Impact**: Critical - Complete service outage

**Recovery Steps**:
```bash
# 1. Provision new cluster or restore existing
# (Cloud-specific commands)

# 2. Restore configuration
kubectl apply -f k8s/namespace.yaml
kubectl apply -f k8s/configmap.yaml
kubectl apply -f k8s/secrets.yaml

# 3. Restore from backup
./scripts/restore.sh backups/latest.tar.gz

# 4. Deploy services
kubectl apply -f k8s/relay-deployment.yaml
kubectl apply -f k8s/node-deployment.yaml
kubectl apply -f k8s/services.yaml

# 5. Verify deployment
kubectl get all -n nia-enterprise
```

**Expected Recovery Time**: 15-30 minutes

### 4. Data Center Failure

**Impact**: Critical - Regional outage

**Recovery Steps**:
```bash
# 1. Activate disaster recovery site
# Update DNS to point to DR region

# 2. Restore from latest backup
aws s3 cp s3://nia-backups/latest.tar.gz .
./scripts/restore.sh latest.tar.gz

# 3. Deploy to DR cluster
kubectl config use-context dr-cluster
kubectl apply -f k8s/

# 4. Verify services
curl https://relay-dr.nia-enterprise.io/health

# 5. Notify stakeholders
```

**Expected Recovery Time**: 30-60 minutes

### 5. Data Corruption

**Impact**: Medium - Invalid state requiring restore

**Recovery Steps**:
```bash
# 1. Identify corruption extent
kubectl exec -n nia-enterprise relay-pod-xxx -- \
  python -c "import verification; verification.check_data_integrity()"

# 2. Stop affected services
kubectl scale deployment nia-relay -n nia-enterprise --replicas=0

# 3. Restore from last known good backup
./scripts/restore.sh backups/pre-corruption.tar.gz

# 4. Verify data integrity
# Run integrity checks

# 5. Restart services
kubectl scale deployment nia-relay -n nia-enterprise --replicas=2
```

**Expected Recovery Time**: 10-20 minutes

## Backup Strategy

### Automated Backups

#### Configuration Backup
```bash
# Daily backup at 2 AM
0 2 * * * /app/scripts/backup.sh
```

#### State Backup (if applicable)
```bash
# Backup every 5 minutes
*/5 * * * * /app/scripts/backup-state.sh
```

### Backup Retention
- Hourly backups: Keep 24 hours
- Daily backups: Keep 7 days
- Weekly backups: Keep 4 weeks
- Monthly backups: Keep 12 months

### Backup Verification
```bash
# Weekly backup restore test
./scripts/test-restore.sh backups/weekly-latest.tar.gz
```

### Backup Storage

#### Local Backups
```bash
# Store in persistent volume
/backups/
  ├── hourly/
  ├── daily/
  ├── weekly/
  └── monthly/
```

#### Remote Backups
```bash
# S3
aws s3 sync /backups s3://nia-enterprise-backups/

# Azure Blob
az storage blob upload-batch \
  -d backups -s /backups

# Google Cloud Storage
gsutil -m rsync -r /backups gs://nia-enterprise-backups/
```

## Monitoring and Alerts

### Critical Alerts

1. **Relay Down**
   - Alert: PagerDuty/Slack
   - Action: Auto-scale + manual investigation

2. **High Error Rate**
   - Alert: > 5% error rate
   - Action: Investigate logs, may trigger rollback

3. **Certificate Expiry**
   - Alert: 30 days before expiry
   - Action: Renew certificates

4. **Backup Failure**
   - Alert: Backup job failed
   - Action: Investigate and retry

### Alert Configuration
```yaml
# Prometheus Alert Rules
groups:
- name: nia-enterprise
  rules:
  - alert: RelayDown
    expr: up{job="nia-relay"} == 0
    for: 1m
    labels:
      severity: critical
    annotations:
      summary: "Relay instance down"
      
  - alert: HighErrorRate
    expr: rate(nia_errors_total[5m]) > 0.05
    for: 5m
    labels:
      severity: warning
```

## Failover Procedures

### Manual Failover to DR Site

```bash
# 1. Verify DR site readiness
curl https://relay-dr.nia-enterprise.io/health

# 2. Update DNS records
# Change relay.nia-enterprise.io to DR IP

# 3. Monitor traffic shift
watch -n 1 'kubectl get pods -n nia-enterprise'

# 4. Verify node connections
kubectl logs -n nia-enterprise -l app=nia-relay -f
```

### Failback to Primary Site

```bash
# 1. Verify primary site recovery
curl https://relay.nia-enterprise.io/health

# 2. Sync any DR data changes to primary
./scripts/sync-dr-to-primary.sh

# 3. Update DNS to point back to primary
# Change relay.nia-enterprise.io to primary IP

# 4. Monitor traffic shift
watch -n 1 'kubectl top pods -n nia-enterprise'

# 5. Decommission DR resources
kubectl scale deployment -n nia-enterprise --replicas=0
```

## Testing

### DR Test Schedule
- **Monthly**: Backup restore test
- **Quarterly**: Simulated relay failure
- **Semi-annually**: Full DR site activation
- **Annually**: Complete disaster simulation

### DR Test Checklist
- [ ] Verify backup integrity
- [ ] Test restore procedure
- [ ] Validate failover process
- [ ] Check monitoring and alerts
- [ ] Verify documentation accuracy
- [ ] Time recovery procedures
- [ ] Document lessons learned

## Communication Plan

### During Disaster

#### Internal Communication
- Slack: #nia-incident-response
- Email: incident-team@nia-enterprise.io
- Phone: Conference bridge for critical issues

#### External Communication
- Status page: https://status.nia-enterprise.io
- Email: Updates to registered contacts
- Twitter: @NiaEnterprise

### Communication Template
```
Subject: [INCIDENT] NiA-Enterprise Service Disruption

Status: Investigating / Identified / Monitoring / Resolved
Impact: [Description of impact]
Started: [Timestamp]
Updated: [Timestamp]

Details:
[Detailed description]

Next Update: [Time of next update]

- NiA-Enterprise Operations Team
```

## Post-Incident Review

### Review Process
1. **Timeline**: Document events
2. **Root Cause**: Identify cause
3. **Impact**: Assess impact
4. **Response**: Evaluate response
5. **Improvements**: Action items
6. **Documentation**: Update procedures

### Review Template
```markdown
# Incident Review: [Date]

## Summary
[Brief summary]

## Timeline
- HH:MM - Event occurred
- HH:MM - Alert triggered
- HH:MM - Team engaged
- HH:MM - Issue resolved

## Root Cause
[Detailed root cause]

## Impact
- Duration: XX minutes
- Users affected: XX
- Data loss: None/Some/Details

## Response Evaluation
- What went well
- What could be improved

## Action Items
- [ ] Action 1 - Owner - Due date
- [ ] Action 2 - Owner - Due date
```

## Contact Information

### DR Team
- Lead: dr-lead@nia-enterprise.io
- On-Call: +1-800-NIA-DR
- Escalation: cto@nia-enterprise.io

### External Contacts
- Cloud Provider Support
- DNS Provider Support
- CDN Provider Support

## Additional Resources

- [AWS Disaster Recovery](https://aws.amazon.com/disaster-recovery/)
- [Azure Site Recovery](https://azure.microsoft.com/en-us/services/site-recovery/)
- [GCP Disaster Recovery](https://cloud.google.com/solutions/dr-scenarios-planning-guide)
