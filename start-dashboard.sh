#!/bin/bash
# Auto-start script for NiA-Cluster Dashboard
# This script ensures the dashboard starts automatically and stays running

set -e

echo "======================================"
echo "NiA-Cluster Dashboard Auto-Start"
echo "======================================"
echo ""

# Configuration
RELAY_HOST="${RELAY_HOST:-localhost}"
RELAY_PORT="${RELAY_PORT:-4040}"
DASHBOARD_PORT="${DASHBOARD_PORT:-8080}"
CHECK_INTERVAL="${CHECK_INTERVAL:-10}"

# Check if Python is available
if ! command -v python3 &> /dev/null; then
    echo "Error: python3 is not installed"
    exit 1
fi

# Check if required packages are installed
echo "Checking dependencies..."
python3 -c "import flask, flask_cors, websockets" 2>/dev/null || {
    echo "Installing required dependencies..."
    pip install -r requirements.txt
}

echo "✓ Dependencies OK"
echo ""

# Make dashboard.py executable
chmod +x dashboard.py

# Start the dashboard
echo "Starting NiA-Cluster Dashboard..."
echo "Relay: ${RELAY_HOST}:${RELAY_PORT}"
echo "Dashboard: http://localhost:${DASHBOARD_PORT}"
echo ""
echo "Press Ctrl+C to stop"
echo "======================================"
echo ""

# Run dashboard with auto-restart on failure
while true; do
    python3 dashboard.py \
        --relay-host "${RELAY_HOST}" \
        --relay-port "${RELAY_PORT}" \
        --dashboard-port "${DASHBOARD_PORT}" \
        --check-interval "${CHECK_INTERVAL}" || {
        echo ""
        echo "Dashboard stopped. Restarting in 5 seconds..."
        sleep 5
    }
done
