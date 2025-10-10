# Security Guide

## Overview

NiA-Enterprise implements multiple layers of security to protect your cluster infrastructure.

## Transport Security

### TLS/SSL Configuration

#### Enable TLS on Relay
```bash
# Generate certificates
./scripts/generate-certs.sh

# Start relay with TLS
python cluster_manager_enterprise.py \
  --mode relay \
  --cluster production \
  --enable-tls \
  --tls-cert certs/server.crt \
  --tls-key certs/server.key
```

#### Enable TLS on Node
```bash
python cluster_manager_enterprise.py \
  --mode node \
  --cluster production \
  --node node1 \
  --relay-host relay.example.com \
  --relay-port 4040 \
  --lan-port 5001 \
  --enable-tls
```

### Mutual TLS (mTLS)

For production environments, implement mTLS:
```bash
# Relay configuration
--enable-tls \
--tls-cert certs/server.crt \
--tls-key certs/server.key \
--tls-ca certs/ca.crt \
--require-client-cert

# Node configuration  
--enable-tls \
--tls-client-cert certs/client.crt \
--tls-client-key certs/client.key \
--tls-ca certs/ca.crt
```

## Authentication

### API Key Authentication

#### Create API Keys
```json
{
  "service-1": "sk_live_abc123def456",
  "service-2": "sk_live_xyz789uvw012",
  "admin": "sk_live_admin_secure_key"
}
```

#### Use API Keys
```bash
# Start relay with API key requirement
python cluster_manager_enterprise.py \
  --mode relay \
  --cluster production \
  --api-keys config/api-keys.json

# Connect node with API key
python cluster_manager_enterprise.py \
  --mode node \
  --api-key sk_live_abc123def456 \
  ...
```

### JWT Token Authentication

For dynamic token-based auth:
```python
import jwt

# Generate token
token = jwt.encode(
    {'node_id': 'node1', 'exp': datetime.utcnow() + timedelta(hours=1)},
    'secret_key',
    algorithm='HS256'
)

# Use in connection
--api-key {token}
```

## Authorization

### Role-Based Access Control (RBAC)

Define roles and permissions:
```yaml
roles:
  admin:
    permissions:
      - cluster:*
      - node:*
      - config:*
  
  operator:
    permissions:
      - cluster:read
      - node:read
      - node:restart
  
  node:
    permissions:
      - cluster:read
      - node:self:*
```

### Implementation
```python
class RBACManager:
    def check_permission(self, role, resource, action):
        # Check if role has permission for action on resource
        pass
```

## Network Security

### Kubernetes Network Policies

```yaml
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata:
  name: nia-network-policy
  namespace: nia-enterprise
spec:
  podSelector:
    matchLabels:
      app: nia-relay
  policyTypes:
  - Ingress
  - Egress
  ingress:
  - from:
    - podSelector:
        matchLabels:
          app: nia-node
    ports:
    - protocol: TCP
      port: 4040
  egress:
  - to:
    - podSelector:
        matchLabels:
          app: nia-node
```

### Firewall Rules

#### AWS Security Groups
```bash
# Relay ingress
aws ec2 authorize-security-group-ingress \
  --group-id sg-xxx \
  --protocol tcp \
  --port 4040 \
  --source-group sg-nodes

# Node egress
aws ec2 authorize-security-group-egress \
  --group-id sg-nodes \
  --protocol tcp \
  --port 4040 \
  --destination-group sg-relay
```

## Secrets Management

### HashiCorp Vault Integration

```python
import hvac

client = hvac.Client(url='https://vault.example.com')
client.token = os.environ['VAULT_TOKEN']

# Read API key from Vault
secret = client.secrets.kv.v2.read_secret_version(path='nia/api-keys')
api_key = secret['data']['data']['production']
```

### AWS Secrets Manager

```bash
# Store secret
aws secretsmanager create-secret \
  --name nia-enterprise/api-keys \
  --secret-string file://api-keys.json

# Retrieve secret
aws secretsmanager get-secret-value \
  --secret-id nia-enterprise/api-keys \
  --query SecretString \
  --output text
```

### Kubernetes Secrets

```bash
# Create secret
kubectl create secret generic nia-api-keys \
  --from-file=api-keys.json \
  -n nia-enterprise

# Use in pod
volumeMounts:
- name: secrets
  mountPath: /secrets
  readOnly: true
volumes:
- name: secrets
  secret:
    secretName: nia-api-keys
```

## Audit Logging

### Enable Audit Logging

All security events are logged:
- Authentication attempts (success/failure)
- Authorization decisions
- Configuration changes
- Node registrations/disconnections

### View Audit Logs

```bash
# From container
kubectl logs -n nia-enterprise relay-pod-xxx | grep AUDIT

# From file
kubectl exec -n nia-enterprise relay-pod-xxx -- \
  tail -f /var/log/audit.log
```

### Sample Audit Log Entry
```json
{
  "timestamp": "2024-01-15T10:30:00Z",
  "type": "authentication",
  "user": "node1",
  "action": "login",
  "result": "success",
  "ip_address": "10.0.1.42",
  "user_agent": "NiA-Node/1.0.0"
}
```

## Compliance

### SOC 2 Compliance
- Audit logging enabled
- Encryption in transit (TLS)
- Access controls (RBAC)
- Regular security scans
- Incident response procedures

### GDPR Compliance
- Data minimization
- Right to deletion
- Data portability
- Privacy by design
- Consent management

### HIPAA Compliance
- Encryption at rest and in transit
- Access controls and audit logs
- Business Associate Agreements
- Risk assessments
- Breach notification procedures

## Security Best Practices

### 1. Principle of Least Privilege
- Grant minimal necessary permissions
- Use service accounts with limited scope
- Regularly review and revoke unused permissions

### 2. Defense in Depth
- Multiple security layers
- Network segmentation
- Application-level security
- Infrastructure security

### 3. Regular Updates
```bash
# Update base images
docker pull python:3.11-slim

# Rebuild with latest patches
docker build -t nia-enterprise:latest .

# Update dependencies
pip install --upgrade -r requirements.txt
```

### 4. Vulnerability Scanning
```bash
# Scan Docker images
trivy image nia-enterprise:latest

# Scan dependencies
safety check -r requirements.txt

# Scan code
bandit -r cluster_manager_enterprise.py
```

### 5. Secure Configuration
- No hardcoded secrets
- Use environment variables
- Encrypt sensitive configuration
- Rotate credentials regularly

## Incident Response

### Security Incident Procedure

1. **Detect**: Monitor alerts and logs
2. **Contain**: Isolate affected systems
3. **Investigate**: Analyze logs and evidence
4. **Remediate**: Apply fixes and patches
5. **Recover**: Restore normal operations
6. **Review**: Post-incident analysis

### Contact Security Team
- Email: security@nia-enterprise.io
- Phone: 1-800-NIA-SECURITY
- PGP Key: Available at https://nia-enterprise.io/pgp

## Penetration Testing

### Regular Security Testing
- Annual penetration tests
- Quarterly vulnerability assessments
- Continuous security monitoring
- Bug bounty program

### Report Security Issues
- Email: security@nia-enterprise.io
- Encrypted: Use PGP key
- Response time: 24 hours for critical issues

## Additional Resources

- [OWASP Top 10](https://owasp.org/www-project-top-ten/)
- [CIS Benchmarks](https://www.cisecurity.org/cis-benchmarks/)
- [NIST Cybersecurity Framework](https://www.nist.gov/cyberframework)
