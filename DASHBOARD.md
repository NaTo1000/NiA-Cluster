# NiA-Cluster Dashboard Guide

## Quick Start

### Start with Docker Compose (Easiest)
```bash
docker compose up
```
Dashboard available at: http://localhost:8080

### Start Standalone
```bash
./start-dashboard.sh
```

### Manual Start
```bash
python3 dashboard.py --relay-host localhost --relay-port 4040
```

## Features

### Real-Time Monitoring
- **Relay Status**: Live health check with visual indicators
  - 🟢 Green = Healthy
  - 🔴 Red = Unhealthy
  - 🟠 Amber = Unknown/Checking
- **Node Count**: Number of active nodes in the cluster
- **Connected Nodes**: List of all nodes with details (port, BLE status, connection time)
- **Auto-Refresh**: Dashboard updates every 5 seconds

### Self-Repair System
- **Automatic Health Checks**: Monitors relay every 10 seconds (configurable)
- **Health Monitoring**: Logs connection issues for troubleshooting
- **Docker Integration**: Works with Docker's restart policies for automatic recovery
- **Toggle Control**: Enable/disable self-repair via the UI
- **Repair Log**: Historical log of all health check events

### Manual Controls
- **Repair Button**: Manually trigger repair logging for components
- **Self-Repair Toggle**: Enable/disable automatic monitoring
- **Real-Time Updates**: All changes reflected immediately

## Configuration

### Command Line Options
```bash
python3 dashboard.py [OPTIONS]

Options:
  --relay-host HOST          Relay server hostname (default: localhost)
  --relay-port PORT          Relay server port (default: 4040)
  --dashboard-port PORT      Dashboard web port (default: 8080)
  --dashboard-host HOST      Bind address (default: 0.0.0.0, use 127.0.0.1 for local only)
  --check-interval SECONDS   Health check interval (default: 10)
  --no-self-repair          Disable automatic self-repair
  --debug                   Enable debug logging
```

### Environment Variables (for start-dashboard.sh)
```bash
export RELAY_HOST=localhost
export RELAY_PORT=4040
export DASHBOARD_PORT=8080
export CHECK_INTERVAL=10
./start-dashboard.sh
```

### Docker Compose Configuration
Edit `docker-compose.yml` to customize:
```yaml
dashboard:
  command: --relay-host cluster_relay --relay-port 4040 --dashboard-port 8080 --check-interval 15
  ports:
    - "8080:8080"
```

## API Endpoints

### GET /health
Health check endpoint for monitoring
```bash
curl http://localhost:8080/health
```

### GET /api/status
Get current cluster status
```bash
curl http://localhost:8080/api/status
```

### POST /api/repair
Trigger manual repair
```bash
curl -X POST http://localhost:8080/api/repair \
  -H "Content-Type: application/json" \
  -d '{"component": "relay"}'
```

### GET/POST /api/config
Get or update configuration
```bash
# Get config
curl http://localhost:8080/api/config

# Update config
curl -X POST http://localhost:8080/api/config \
  -H "Content-Type: application/json" \
  -d '{"self_repair_enabled": false}'
```

## Architecture

```
┌─────────────────────────────────────┐
│         Dashboard GUI               │
│         (Flask Web App)             │
│  - Real-time monitoring             │
│  - Self-repair controls             │
│  - Health check logs                │
└──────────┬──────────────────────────┘
           │
           │ WebSocket
           │ Health Checks
           │
┌──────────▼──────────────────────────┐
│       Cluster Relay                 │
│       (WebSocket Server)            │
└──────────┬──────────────────────────┘
           │
     ┌─────┴─────┐
     │           │
┌────▼────┐ ┌───▼─────┐
│  Node1  │ │  Node2  │
└─────────┘ └─────────┘
```

## Self-Repair Behavior

The dashboard implements a **monitoring and logging** approach to self-repair:

1. **Health Checks**: Dashboard connects to relay every 10 seconds
2. **Detection**: If relay is unresponsive, logs the failure
3. **Recovery**: Docker's restart policies handle actual container restarts
4. **Logging**: All events logged in the repair log for troubleshooting

This design:
- ✅ Non-intrusive - doesn't interfere with cluster operations
- ✅ Docker-native - leverages container restart policies
- ✅ Observable - provides clear visibility into health issues
- ✅ Flexible - works in development and production

For production deployments with Kubernetes or Docker Swarm, the repair mechanism can be extended to trigger actual orchestration-level restarts.

## Troubleshooting

### Dashboard won't start
```bash
# Check dependencies
pip install -r requirements.txt

# Verify relay is running
curl -v http://localhost:4040

# Check logs
docker logs cluster_dashboard
```

### Can't access dashboard
```bash
# Check if dashboard is running
docker ps | grep dashboard

# Try local access
curl http://localhost:8080/health

# Check firewall settings
sudo ufw status
```

### Self-repair not working
1. Check that self-repair is enabled in the UI (toggle should be green)
2. Verify relay is accessible: `curl -v ws://localhost:4040`
3. Check dashboard logs for errors: `docker logs cluster_dashboard`
4. Ensure Docker restart policy is set: `docker inspect cluster_relay | grep -A 5 RestartPolicy`

## Security Considerations

### Development
- Default configuration binds to `0.0.0.0` (all interfaces)
- CORS restricted to localhost origins
- Suitable for development and testing

### Production
- Use `--dashboard-host 127.0.0.1` to restrict to local access only
- Place behind reverse proxy (nginx, Apache) with authentication
- Use HTTPS for external access
- Consider VPN or SSH tunneling for remote access

## Examples

### Start for development
```bash
python3 dashboard.py --debug
```

### Start with custom check interval
```bash
python3 dashboard.py --check-interval 30
```

### Start with local-only access
```bash
python3 dashboard.py --dashboard-host 127.0.0.1
```

### Start with self-repair disabled
```bash
python3 dashboard.py --no-self-repair
```

## Integration

### With CI/CD
The dashboard can be used in CI/CD pipelines to verify cluster health:
```bash
# Start cluster
docker compose up -d

# Wait for startup
sleep 10

# Check health
if curl -f http://localhost:8080/api/status | grep -q "healthy"; then
  echo "Cluster is healthy"
else
  echo "Cluster health check failed"
  exit 1
fi
```

### With Monitoring Tools
Dashboard exposes standard endpoints that work with:
- Prometheus (can add metrics endpoint)
- Grafana (for visualization)
- Nagios/Zabbix (for alerting)
- Custom monitoring scripts

## Support

For issues or questions:
1. Check the logs: `docker logs cluster_dashboard`
2. Review the repair log in the dashboard UI
3. Run the test suite: `./test-dashboard.sh`
4. Check GitHub issues for similar problems
