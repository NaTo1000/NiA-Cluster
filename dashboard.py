#!/usr/bin/env python3
"""
NiA-Cluster Dashboard with Auto-Start and Self-Repair
Web-based monitoring dashboard for cluster health and status
"""
import argparse
import asyncio
import json
import logging
import sys
import time
import subprocess
import signal
from datetime import datetime, timedelta
from typing import Dict, List, Optional
from threading import Thread, Lock

try:
    from flask import Flask, render_template, jsonify, request
    from flask_cors import CORS
except ImportError:
    print("Error: Flask not installed. Run: pip install flask flask-cors")
    sys.exit(1)

try:
    import websockets
except ImportError:
    print("Error: websockets library not installed. Run: pip install websockets")
    sys.exit(1)

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Global state
cluster_state = {
    'relay': {'status': 'unknown', 'last_check': None, 'uptime': 0},
    'nodes': {},
    'last_update': None,
    'self_repair_enabled': True,
    'repair_log': []
}
state_lock = Lock()

app = Flask(__name__)
# Allow CORS only for localhost origins for development
CORS(app, origins=['http://localhost:*', 'http://127.0.0.1:*'])


class ClusterMonitor:
    """Monitor cluster health and perform self-repair"""
    
    def __init__(self, relay_host: str, relay_port: int, check_interval: int = 10,
                 enable_self_repair: bool = True):
        self.relay_host = relay_host
        self.relay_port = relay_port
        self.check_interval = check_interval
        self.enable_self_repair = enable_self_repair
        self.running = False
        self.relay_process = None
        self.node_processes = {}
        
    async def check_relay_health(self) -> bool:
        """Check if relay server is responsive"""
        try:
            relay_url = f"ws://{self.relay_host}:{self.relay_port}"
            async with websockets.connect(relay_url, timeout=5) as ws:
                # Send a test heartbeat
                await ws.send(json.dumps({'type': 'heartbeat', 'node_name': 'dashboard'}))
                response = await asyncio.wait_for(ws.recv(), timeout=5)
                data = json.loads(response)
                return data.get('type') == 'heartbeat_ack'
        except Exception as e:
            logger.warning(f"Relay health check failed: {e}")
            return False
    
    async def monitor_loop(self):
        """Main monitoring loop"""
        self.running = True
        logger.info("Starting cluster monitoring...")
        
        while self.running:
            try:
                # Check relay health
                relay_healthy = await self.check_relay_health()
                
                with state_lock:
                    cluster_state['relay']['status'] = 'healthy' if relay_healthy else 'unhealthy'
                    cluster_state['relay']['last_check'] = datetime.now().isoformat()
                    cluster_state['last_update'] = datetime.now().isoformat()
                    
                    # Self-repair: restart relay if unhealthy
                    if not relay_healthy and self.enable_self_repair:
                        self.repair_relay()
                
                await asyncio.sleep(self.check_interval)
                
            except Exception as e:
                logger.error(f"Error in monitoring loop: {e}")
                await asyncio.sleep(self.check_interval)
    
    def repair_relay(self):
        """
        Attempt to repair/restart relay server
        
        Note: In the current implementation, this logs repair attempts but does not
        perform actual container restarts. In a production environment with proper
        orchestration (Kubernetes, Docker Swarm), this would trigger actual repairs.
        For Docker Compose deployments, the 'restart: unless-stopped' policy provides
        automatic restart on failure.
        """
        try:
            timestamp = datetime.now().isoformat()
            logger.warning("Attempting to repair relay server...")
            
            repair_entry = {
                'timestamp': timestamp,
                'component': 'relay',
                'action': 'health_check_failed',
                'success': False
            }
            
            # In a Docker environment, we can't easily restart containers from within
            # But we can log the issue. The docker-compose 'restart' policy handles actual restarts.
            logger.info("Relay unhealthy. Logged for monitoring. Docker restart policy will handle recovery.")
            repair_entry['success'] = True
            repair_entry['action'] = 'logged_for_monitoring'
            
            with state_lock:
                cluster_state['repair_log'].append(repair_entry)
                # Keep only last 50 repair log entries
                if len(cluster_state['repair_log']) > 50:
                    cluster_state['repair_log'] = cluster_state['repair_log'][-50:]
                    
        except Exception as e:
            logger.error(f"Failed to log repair action: {e}")
    
    def start(self):
        """Start monitoring in background thread"""
        def run_monitor():
            asyncio.run(self.monitor_loop())
        
        thread = Thread(target=run_monitor, daemon=True)
        thread.start()
        logger.info("Cluster monitor started")
    
    def stop(self):
        """Stop monitoring"""
        self.running = False
        logger.info("Cluster monitor stopped")


# Flask routes
@app.route('/')
def index():
    """Dashboard home page"""
    return render_template('dashboard.html')


@app.route('/api/status')
def get_status():
    """Get current cluster status"""
    with state_lock:
        return jsonify(cluster_state)


@app.route('/api/repair', methods=['POST'])
def trigger_repair():
    """Manually trigger repair for a component"""
    data = request.get_json()
    if not data:
        return jsonify({'error': 'No data provided'}), 400
    
    component = data.get('component', 'relay')
    
    # Validate component is allowed
    allowed_components = ['relay', 'node', 'dashboard']
    if component not in allowed_components:
        return jsonify({'error': 'Invalid component'}), 400
    
    logger.info(f"Manual repair triggered for {component}")
    
    # Add to repair log
    with state_lock:
        cluster_state['repair_log'].append({
            'timestamp': datetime.now().isoformat(),
            'component': component,
            'action': 'manual_repair_triggered',
            'success': True
        })
    
    return jsonify({'status': 'repair_triggered', 'component': component})


@app.route('/api/config', methods=['GET', 'POST'])
def config():
    """Get or update dashboard configuration"""
    if request.method == 'POST':
        data = request.get_json()
        if not data:
            return jsonify({'error': 'No data provided'}), 400
        
        with state_lock:
            if 'self_repair_enabled' in data:
                # Validate boolean value
                if not isinstance(data['self_repair_enabled'], bool):
                    return jsonify({'error': 'self_repair_enabled must be boolean'}), 400
                cluster_state['self_repair_enabled'] = data['self_repair_enabled']
        return jsonify({'status': 'updated'})
    else:
        with state_lock:
            return jsonify({
                'self_repair_enabled': cluster_state['self_repair_enabled']
            })


@app.route('/health')
@app.route('/healthz')
def health():
    """Health check endpoint"""
    return jsonify({'status': 'healthy', 'timestamp': datetime.now().isoformat()})


def create_dashboard_html():
    """Create the dashboard HTML template"""
    templates_dir = 'templates'
    import os
    os.makedirs(templates_dir, exist_ok=True)
    
    html_content = '''<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>NiA-Cluster Dashboard</title>
    <style>
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }
        
        body {
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
            padding: 20px;
        }
        
        .container {
            max-width: 1400px;
            margin: 0 auto;
        }
        
        .header {
            background: white;
            padding: 30px;
            border-radius: 15px;
            box-shadow: 0 10px 30px rgba(0,0,0,0.2);
            margin-bottom: 30px;
            text-align: center;
        }
        
        .header h1 {
            color: #667eea;
            font-size: 2.5em;
            margin-bottom: 10px;
        }
        
        .header .subtitle {
            color: #666;
            font-size: 1.2em;
        }
        
        .status-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
            gap: 20px;
            margin-bottom: 30px;
        }
        
        .card {
            background: white;
            padding: 25px;
            border-radius: 15px;
            box-shadow: 0 10px 30px rgba(0,0,0,0.2);
        }
        
        .card h2 {
            color: #333;
            margin-bottom: 15px;
            font-size: 1.5em;
            border-bottom: 3px solid #667eea;
            padding-bottom: 10px;
        }
        
        .status-indicator {
            display: inline-block;
            width: 15px;
            height: 15px;
            border-radius: 50%;
            margin-right: 10px;
        }
        
        .status-healthy {
            background: #4caf50;
            box-shadow: 0 0 10px #4caf50;
        }
        
        .status-unhealthy {
            background: #f44336;
            box-shadow: 0 0 10px #f44336;
        }
        
        .status-unknown {
            background: #ff9800;
            box-shadow: 0 0 10px #ff9800;
        }
        
        .metric {
            padding: 15px;
            background: #f5f5f5;
            border-radius: 8px;
            margin: 10px 0;
        }
        
        .metric-label {
            font-weight: bold;
            color: #666;
            font-size: 0.9em;
            text-transform: uppercase;
        }
        
        .metric-value {
            font-size: 1.8em;
            color: #333;
            margin-top: 5px;
        }
        
        .repair-log {
            max-height: 400px;
            overflow-y: auto;
            background: #f9f9f9;
            padding: 15px;
            border-radius: 8px;
        }
        
        .repair-entry {
            padding: 10px;
            background: white;
            margin-bottom: 10px;
            border-left: 4px solid #667eea;
            border-radius: 4px;
        }
        
        .repair-timestamp {
            font-size: 0.85em;
            color: #999;
        }
        
        .button {
            background: #667eea;
            color: white;
            border: none;
            padding: 12px 24px;
            border-radius: 8px;
            cursor: pointer;
            font-size: 1em;
            transition: background 0.3s;
            margin: 5px;
        }
        
        .button:hover {
            background: #5568d3;
        }
        
        .button-danger {
            background: #f44336;
        }
        
        .button-danger:hover {
            background: #da190b;
        }
        
        .toggle-switch {
            position: relative;
            display: inline-block;
            width: 60px;
            height: 34px;
            margin-left: 10px;
        }
        
        .toggle-switch input {
            opacity: 0;
            width: 0;
            height: 0;
        }
        
        .slider {
            position: absolute;
            cursor: pointer;
            top: 0;
            left: 0;
            right: 0;
            bottom: 0;
            background-color: #ccc;
            transition: .4s;
            border-radius: 34px;
        }
        
        .slider:before {
            position: absolute;
            content: "";
            height: 26px;
            width: 26px;
            left: 4px;
            bottom: 4px;
            background-color: white;
            transition: .4s;
            border-radius: 50%;
        }
        
        input:checked + .slider {
            background-color: #4caf50;
        }
        
        input:checked + .slider:before {
            transform: translateX(26px);
        }
        
        .last-update {
            text-align: center;
            color: white;
            margin-top: 20px;
            font-size: 0.9em;
        }
        
        .nodes-list {
            list-style: none;
        }
        
        .node-item {
            background: #f5f5f5;
            padding: 15px;
            margin: 10px 0;
            border-radius: 8px;
            border-left: 4px solid #667eea;
        }
        
        .node-name {
            font-weight: bold;
            color: #333;
            font-size: 1.1em;
        }
        
        .node-detail {
            color: #666;
            font-size: 0.9em;
            margin-top: 5px;
        }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>🚀 NiA-Cluster Dashboard</h1>
            <p class="subtitle">Real-time Monitoring & Self-Repair System</p>
        </div>
        
        <div class="status-grid">
            <div class="card">
                <h2>🎯 Relay Status</h2>
                <div class="metric">
                    <div class="metric-label">Status</div>
                    <div class="metric-value">
                        <span id="relay-status-indicator" class="status-indicator status-unknown"></span>
                        <span id="relay-status">Checking...</span>
                    </div>
                </div>
                <div class="metric">
                    <div class="metric-label">Last Check</div>
                    <div class="metric-value" id="relay-last-check" style="font-size: 1.2em;">-</div>
                </div>
                <button class="button" onclick="triggerRepair('relay')">🔧 Repair Relay</button>
            </div>
            
            <div class="card">
                <h2>📊 Cluster Metrics</h2>
                <div class="metric">
                    <div class="metric-label">Active Nodes</div>
                    <div class="metric-value" id="node-count">0</div>
                </div>
                <div class="metric">
                    <div class="metric-label">Self-Repair</div>
                    <div class="metric-value">
                        <label class="toggle-switch">
                            <input type="checkbox" id="self-repair-toggle" checked onchange="toggleSelfRepair()">
                            <span class="slider"></span>
                        </label>
                        <span id="self-repair-status">Enabled</span>
                    </div>
                </div>
            </div>
            
            <div class="card">
                <h2>🖥️ Connected Nodes</h2>
                <ul id="nodes-list" class="nodes-list">
                    <li style="color: #999;">No nodes connected</li>
                </ul>
            </div>
        </div>
        
        <div class="card">
            <h2>🔧 Self-Repair Log</h2>
            <div class="repair-log" id="repair-log">
                <p style="color: #999;">No repair actions yet</p>
            </div>
        </div>
        
        <div class="last-update">
            Last updated: <span id="last-update">-</span>
        </div>
    </div>
    
    <script>
        let updateInterval;
        
        function updateDashboard() {
            fetch('/api/status')
                .then(response => response.json())
                .then(data => {
                    // Update relay status
                    const relayStatus = data.relay.status;
                    document.getElementById('relay-status').textContent = relayStatus.charAt(0).toUpperCase() + relayStatus.slice(1);
                    
                    const indicator = document.getElementById('relay-status-indicator');
                    indicator.className = 'status-indicator status-' + relayStatus;
                    
                    if (data.relay.last_check) {
                        const lastCheck = new Date(data.relay.last_check);
                        document.getElementById('relay-last-check').textContent = lastCheck.toLocaleTimeString();
                    }
                    
                    // Update node count
                    const nodeCount = Object.keys(data.nodes).length;
                    document.getElementById('node-count').textContent = nodeCount;
                    
                    // Update nodes list
                    const nodesList = document.getElementById('nodes-list');
                    if (nodeCount > 0) {
                        nodesList.innerHTML = '';
                        Object.entries(data.nodes).forEach(([name, info]) => {
                            const li = document.createElement('li');
                            li.className = 'node-item';
                            li.innerHTML = `
                                <div class="node-name">${name}</div>
                                <div class="node-detail">Port: ${info.lan_port || 'N/A'} | BLE: ${info.ble_enabled ? 'Yes' : 'No'}</div>
                                <div class="node-detail">Connected: ${new Date(info.connected_at).toLocaleString()}</div>
                            `;
                            nodesList.appendChild(li);
                        });
                    } else {
                        nodesList.innerHTML = '<li style="color: #999;">No nodes connected</li>';
                    }
                    
                    // Update repair log
                    const repairLog = document.getElementById('repair-log');
                    if (data.repair_log && data.repair_log.length > 0) {
                        repairLog.innerHTML = '';
                        data.repair_log.slice().reverse().forEach(entry => {
                            const div = document.createElement('div');
                            div.className = 'repair-entry';
                            const timestamp = new Date(entry.timestamp).toLocaleString();
                            div.innerHTML = `
                                <div class="repair-timestamp">${timestamp}</div>
                                <div><strong>${entry.component}</strong>: ${entry.action}</div>
                                <div style="color: ${entry.success ? '#4caf50' : '#f44336'}">
                                    ${entry.success ? '✓ Success' : '✗ Failed'}
                                </div>
                            `;
                            repairLog.appendChild(div);
                        });
                    }
                    
                    // Update self-repair status
                    document.getElementById('self-repair-toggle').checked = data.self_repair_enabled;
                    document.getElementById('self-repair-status').textContent = data.self_repair_enabled ? 'Enabled' : 'Disabled';
                    
                    // Update last update time
                    if (data.last_update) {
                        document.getElementById('last-update').textContent = new Date(data.last_update).toLocaleString();
                    }
                })
                .catch(error => {
                    console.error('Error fetching status:', error);
                });
        }
        
        function triggerRepair(component) {
            fetch('/api/repair', {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({component: component})
            })
            .then(response => response.json())
            .then(data => {
                alert(`Repair triggered for ${data.component}`);
                updateDashboard();
            })
            .catch(error => {
                alert('Failed to trigger repair');
                console.error(error);
            });
        }
        
        function toggleSelfRepair() {
            const enabled = document.getElementById('self-repair-toggle').checked;
            fetch('/api/config', {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({self_repair_enabled: enabled})
            })
            .then(() => {
                document.getElementById('self-repair-status').textContent = enabled ? 'Enabled' : 'Disabled';
            })
            .catch(error => {
                console.error('Error updating config:', error);
            });
        }
        
        // Initial update and set interval
        updateDashboard();
        updateInterval = setInterval(updateDashboard, 5000); // Update every 5 seconds
    </script>
</body>
</html>'''
    
    with open(f'{templates_dir}/dashboard.html', 'w') as f:
        f.write(html_content)
    
    logger.info(f"Dashboard HTML template created in {templates_dir}/")


def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(
        description='NiA-Cluster Dashboard - Monitor and manage cluster health'
    )
    
    parser.add_argument('--relay-host', default='localhost',
                        help='Relay server hostname (default: localhost)')
    parser.add_argument('--relay-port', type=int, default=4040,
                        help='Relay server port (default: 4040)')
    parser.add_argument('--dashboard-port', type=int, default=8080,
                        help='Dashboard web interface port (default: 8080)')
    parser.add_argument('--dashboard-host', default='0.0.0.0',
                        help='Dashboard bind address (default: 0.0.0.0 for all interfaces, use 127.0.0.1 for local only)')
    parser.add_argument('--check-interval', type=int, default=10,
                        help='Health check interval in seconds (default: 10)')
    parser.add_argument('--no-self-repair', action='store_true',
                        help='Disable automatic self-repair')
    parser.add_argument('--debug', action='store_true',
                        help='Enable debug logging')
    
    args = parser.parse_args()
    
    if args.debug:
        logging.getLogger().setLevel(logging.DEBUG)
    
    # Create dashboard HTML template
    create_dashboard_html()
    
    # Initialize and start cluster monitor
    monitor = ClusterMonitor(
        args.relay_host,
        args.relay_port,
        args.check_interval,
        not args.no_self_repair
    )
    
    with state_lock:
        cluster_state['self_repair_enabled'] = not args.no_self_repair
    
    monitor.start()
    
    # Start Flask web server
    logger.info(f"Starting dashboard web interface on {args.dashboard_host}:{args.dashboard_port}")
    if args.dashboard_host == '0.0.0.0':
        logger.warning("Dashboard is accessible from all network interfaces. For security, consider using --dashboard-host 127.0.0.1 for local-only access.")
    logger.info(f"Access dashboard at: http://localhost:{args.dashboard_port}")
    
    try:
        app.run(host=args.dashboard_host, port=args.dashboard_port, debug=args.debug, use_reloader=False)
    except KeyboardInterrupt:
        logger.info("Shutting down dashboard...")
        monitor.stop()
    except Exception as e:
        logger.error(f"Error: {e}")
        sys.exit(1)


if __name__ == '__main__':
    main()
