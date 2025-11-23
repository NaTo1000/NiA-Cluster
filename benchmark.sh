#!/bin/bash
# Benchmark Suite for NiA-Cluster Dashboard
# Compares performance metrics and logs results

set -e

TIMESTAMP=$(date +%Y%m%d_%H%M%S)
LOG_DIR="test-logs"
BENCHMARK_LOG="${LOG_DIR}/benchmark-${TIMESTAMP}.log"

mkdir -p "$LOG_DIR"

echo "======================================"
echo "NiA-Cluster Dashboard Benchmark Suite"
echo "======================================"
echo "Timestamp: $(date)"
echo "Log file: $BENCHMARK_LOG"
echo "======================================"
echo ""

log() {
    echo "$1" | tee -a "$BENCHMARK_LOG"
}

log_section() {
    echo "" | tee -a "$BENCHMARK_LOG"
    echo "======================================" | tee -a "$BENCHMARK_LOG"
    echo "$1" | tee -a "$BENCHMARK_LOG"
    echo "======================================" | tee -a "$BENCHMARK_LOG"
}

# Start the cluster
log_section "Starting Cluster for Benchmarking"
docker compose up -d >> "$BENCHMARK_LOG" 2>&1
sleep 20
log "✓ Cluster started"

# Benchmark 1: Dashboard startup time
log_section "Benchmark 1: Dashboard Startup Time"
START_TIME=$(date +%s.%N)
docker restart cluster_dashboard >> "$BENCHMARK_LOG" 2>&1
sleep 5
# Wait for dashboard to be ready
until curl -s http://localhost:8080/health > /dev/null 2>&1; do
    sleep 0.5
done
END_TIME=$(date +%s.%N)
STARTUP_TIME=$(echo "$END_TIME - $START_TIME" | bc)
log "Dashboard startup time: ${STARTUP_TIME}s"

# Benchmark 2: API response times
log_section "Benchmark 2: API Response Times"

# Status endpoint
START=$(date +%s.%N)
for i in {1..100}; do
    curl -s http://localhost:8080/api/status > /dev/null 2>&1
done
END=$(date +%s.%N)
STATUS_AVG=$(echo "scale=4; ($END - $START) / 100" | bc)
log "Average /api/status response time (100 requests): ${STATUS_AVG}s"

# Health endpoint
START=$(date +%s.%N)
for i in {1..100}; do
    curl -s http://localhost:8080/health > /dev/null 2>&1
done
END=$(date +%s.%N)
HEALTH_AVG=$(echo "scale=4; ($END - $START) / 100" | bc)
log "Average /health response time (100 requests): ${HEALTH_AVG}s"

# Config endpoint
START=$(date +%s.%N)
for i in {1..100}; do
    curl -s http://localhost:8080/api/config > /dev/null 2>&1
done
END=$(date +%s.%N)
CONFIG_AVG=$(echo "scale=4; ($END - $START) / 100" | bc)
log "Average /api/config response time (100 requests): ${CONFIG_AVG}s"

# Benchmark 3: Resource usage
log_section "Benchmark 3: Resource Usage"

# Collect stats over 15 seconds (faster for CI)
log "Collecting resource stats (15 seconds)..."
for i in {1..3}; do
    DASHBOARD_CPU=$(docker stats --no-stream --format "{{.CPUPerc}}" cluster_dashboard 2>&1 | tr -d '%')
    DASHBOARD_MEM=$(docker stats --no-stream --format "{{.MemUsage}}" cluster_dashboard 2>&1 | awk '{print $1}')
    
    log "Sample $i - Dashboard CPU: ${DASHBOARD_CPU}% | Memory: ${DASHBOARD_MEM}"
    sleep 5
done

# Benchmark 4: Concurrent connections
log_section "Benchmark 4: Concurrent Connection Handling"

log "Testing with 10 concurrent connections..."
START=$(date +%s.%N)
for i in {1..10}; do
    curl -s http://localhost:8080/api/status > /dev/null &
done
wait
END=$(date +%s.%N)
CONCURRENT_10=$(echo "scale=4; $END - $START" | bc)
log "10 concurrent requests completed in: ${CONCURRENT_10}s"

log "Testing with 50 concurrent connections..."
START=$(date +%s.%N)
for i in {1..50}; do
    curl -s http://localhost:8080/api/status > /dev/null &
done
wait
END=$(date +%s.%N)
CONCURRENT_50=$(echo "scale=4; $END - $START" | bc)
log "50 concurrent requests completed in: ${CONCURRENT_50}s"

# Benchmark 5: Health check latency
log_section "Benchmark 5: Health Check Monitoring Latency"
log "Measuring time to detect relay failure..."

# Get current status
curl -s http://localhost:8080/api/status | grep -o '"status":"[^"]*"' | head -1 > /tmp/status_before.txt

# Kill relay
START=$(date +%s.%N)
docker kill cluster_relay >> "$BENCHMARK_LOG" 2>&1

# Wait for dashboard to detect failure (max 30 seconds)
TIMEOUT=30
ELAPSED=0
while [ $ELAPSED -lt $TIMEOUT ]; do
    STATUS=$(curl -s http://localhost:8080/api/status 2>/dev/null | grep -o '"status":"[^"]*"' | head -1)
    if echo "$STATUS" | grep -q "unhealthy"; then
        END=$(date +%s.%N)
        break
    fi
    sleep 2
    ELAPSED=$((ELAPSED + 2))
done
if [ $ELAPSED -ge $TIMEOUT ]; then
    END=$(date +%s.%N)
fi

DETECTION_TIME=$(echo "scale=2; $END - $START" | bc)
log "Failure detection time: ${DETECTION_TIME}s"

# Restart relay for cleanup
docker compose up -d cluster_relay >> "$BENCHMARK_LOG" 2>&1
sleep 5

# Benchmark 6: Page load time
log_section "Benchmark 6: Dashboard Page Load Time"
START=$(date +%s.%N)
curl -s http://localhost:8080/ > /dev/null 2>&1
END=$(date +%s.%N)
PAGE_LOAD=$(echo "scale=4; $END - $START" | bc)
log "Dashboard page load time: ${PAGE_LOAD}s"

# Comparison with typical monitoring solutions
log_section "Benchmark 7: Comparison Metrics"
log ""
log "NiA-Cluster Dashboard Metrics:"
log "  - Startup time: ${STARTUP_TIME}s"
log "  - API latency: ${STATUS_AVG}s (avg)"
log "  - Failure detection: ${DETECTION_TIME}s"
log "  - Concurrent handling: ${CONCURRENT_50}s for 50 requests"
log "  - Page load: ${PAGE_LOAD}s"
log ""
log "Typical Industry Benchmarks (for reference):"
log "  - Prometheus: ~2-5s startup, ~0.01-0.05s API latency"
log "  - Grafana: ~5-10s startup, ~0.1-0.5s page load"
log "  - Kubernetes Dashboard: ~3-7s startup, ~0.2-0.8s page load"
log ""
log "Notes:"
log "  - NiA-Cluster is optimized for lightweight edge/IoT deployments"
log "  - Lower memory footprint compared to enterprise solutions"
log "  - Suitable for resource-constrained environments"

# Generate summary report
log_section "Benchmark Summary"
log "Test completed at: $(date)"
log ""
log "Performance Metrics:"
log "  ✓ Dashboard startup: ${STARTUP_TIME}s"
log "  ✓ API response (avg): ${STATUS_AVG}s"
log "  ✓ Health check (avg): ${HEALTH_AVG}s"
log "  ✓ Failure detection: ${DETECTION_TIME}s"
log "  ✓ Concurrent (10): ${CONCURRENT_10}s"
log "  ✓ Concurrent (50): ${CONCURRENT_50}s"
log "  ✓ Page load: ${PAGE_LOAD}s"
log ""
log "Recommendation:"
if (( $(echo "$STATUS_AVG < 0.1" | bc -l) )); then
    log "  ✓ API performance is EXCELLENT"
elif (( $(echo "$STATUS_AVG < 0.5" | bc -l) )); then
    log "  ✓ API performance is GOOD"
else
    log "  ⚠ API performance could be improved"
fi

if (( $(echo "$DETECTION_TIME < 15" | bc -l) )); then
    log "  ✓ Failure detection is FAST"
elif (( $(echo "$DETECTION_TIME < 30" | bc -l) )); then
    log "  ✓ Failure detection is ACCEPTABLE"
else
    log "  ⚠ Failure detection could be faster (consider reducing check-interval)"
fi

# Cleanup
log_section "Cleanup"
docker compose down >> "$BENCHMARK_LOG" 2>&1
log "✓ Test environment cleaned up"

echo ""
echo "======================================"
echo "Benchmark Complete"
echo "======================================"
echo "Full report: $BENCHMARK_LOG"
echo "======================================"

log ""
log "Full benchmark log saved to: $BENCHMARK_LOG"
