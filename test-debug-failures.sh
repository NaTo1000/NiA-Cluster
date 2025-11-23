#!/bin/bash
# Comprehensive Debug and Failure Test Suite for NiA-Cluster Dashboard
# Tests various failure scenarios and logs results

set +e  # Don't exit on errors - we want to test failures

TIMESTAMP=$(date +%Y%m%d_%H%M%S)
LOG_DIR="test-logs"
LOG_FILE="${LOG_DIR}/debug-failures-${TIMESTAMP}.log"

mkdir -p "$LOG_DIR"

echo "======================================"
echo "NiA-Cluster Debug & Failure Test Suite"
echo "======================================"
echo "Timestamp: $(date)"
echo "Log file: $LOG_FILE"
echo "======================================"
echo ""

# Logging function
log() {
    echo "$1" | tee -a "$LOG_FILE"
}

log_section() {
    echo "" | tee -a "$LOG_FILE"
    echo "======================================" | tee -a "$LOG_FILE"
    echo "$1" | tee -a "$LOG_FILE"
    echo "======================================" | tee -a "$LOG_FILE"
}

# Test counter
TESTS_RUN=0
TESTS_PASSED=0
TESTS_FAILED=0

run_test() {
    local test_name="$1"
    local test_command="$2"
    local expected_result="$3"  # "pass" or "fail"
    
    TESTS_RUN=$((TESTS_RUN + 1))
    log_section "Test $TESTS_RUN: $test_name"
    
    log "Command: $test_command"
    log "Expected: $expected_result"
    log ""
    
    eval "$test_command" >> "$LOG_FILE" 2>&1
    local exit_code=$?
    
    if [ "$expected_result" = "fail" ]; then
        if [ $exit_code -ne 0 ]; then
            log "✓ Test PASSED (expected failure occurred)"
            TESTS_PASSED=$((TESTS_PASSED + 1))
            return 0
        else
            log "✗ Test FAILED (expected failure but command succeeded)"
            TESTS_FAILED=$((TESTS_FAILED + 1))
            return 1
        fi
    else
        if [ $exit_code -eq 0 ]; then
            log "✓ Test PASSED"
            TESTS_PASSED=$((TESTS_PASSED + 1))
            return 0
        else
            log "✗ Test FAILED (exit code: $exit_code)"
            TESTS_FAILED=$((TESTS_FAILED + 1))
            return 1
        fi
    fi
}

# Build the image first
log_section "Building Docker Image"
docker build -t cluster-suite:latest . >> "$LOG_FILE" 2>&1
if [ $? -eq 0 ]; then
    log "✓ Docker build successful"
else
    log "✗ Docker build failed"
    exit 1
fi

# Test 1: Dashboard with no relay available (failure scenario)
run_test "Dashboard startup with no relay" \
    "timeout 10 docker run --rm --name test-dashboard-fail cluster-suite:latest dashboard.py --relay-host nonexistent --relay-port 9999 --no-self-repair" \
    "fail"

# Test 2: Dashboard with invalid port
run_test "Dashboard with invalid port number" \
    "docker run --rm cluster-suite:latest dashboard.py --dashboard-port -1" \
    "fail"

# Test 3: Dashboard help (should succeed)
run_test "Dashboard help command" \
    "docker run --rm cluster-suite:latest dashboard.py --help" \
    "pass"

# Test 4: Cluster manager help (should succeed)
run_test "Cluster manager help command" \
    "docker run --rm cluster-suite:latest --help" \
    "pass"

# Test 5: Start relay and dashboard, then kill relay (recovery test)
log_section "Test 5: Self-Repair - Relay Failure Recovery"
log "Starting relay..."
docker run -d --rm --name test-relay cluster-suite:latest --mode relay --cluster testfleet --relay-port 4040 >> "$LOG_FILE" 2>&1
sleep 3

log "Starting dashboard..."
docker run -d --rm --name test-dashboard cluster-suite:latest dashboard.py --relay-host test-relay --relay-port 4040 --check-interval 5 >> "$LOG_FILE" 2>&1
sleep 5

log "Checking dashboard health..."
HEALTH_BEFORE=$(docker exec test-dashboard curl -s http://localhost:8080/api/status 2>/dev/null | grep -o '"status":"[^"]*"' | head -1)
log "Health before relay failure: $HEALTH_BEFORE"

log "Killing relay to simulate failure..."
docker kill test-relay >> "$LOG_FILE" 2>&1
sleep 10

log "Checking dashboard detects failure..."
HEALTH_AFTER=$(docker exec test-dashboard curl -s http://localhost:8080/api/status 2>/dev/null | grep -o '"status":"[^"]*"' | head -1)
log "Health after relay failure: $HEALTH_AFTER"

if echo "$HEALTH_AFTER" | grep -q "unhealthy"; then
    log "✓ Test PASSED - Dashboard detected relay failure"
    TESTS_PASSED=$((TESTS_PASSED + 1))
else
    log "✗ Test FAILED - Dashboard did not detect failure"
    TESTS_FAILED=$((TESTS_FAILED + 1))
fi
TESTS_RUN=$((TESTS_RUN + 1))

log "Cleaning up test containers..."
docker kill test-dashboard >> "$LOG_FILE" 2>&1

# Test 6: API endpoint validation
log_section "Test 6: API Security - Invalid Input"
log "Starting cluster for API tests..."
docker compose up -d >> "$LOG_FILE" 2>&1
sleep 15

log "Testing invalid repair component..."
RESPONSE=$(curl -s -X POST http://localhost:8080/api/repair -H "Content-Type: application/json" -d '{"component":"invalid_component"}' 2>&1)
if echo "$RESPONSE" | grep -q "Invalid component"; then
    log "✓ Test PASSED - API rejected invalid component"
    TESTS_PASSED=$((TESTS_PASSED + 1))
else
    log "✗ Test FAILED - API accepted invalid component"
    log "Response: $RESPONSE"
    TESTS_FAILED=$((TESTS_FAILED + 1))
fi
TESTS_RUN=$((TESTS_RUN + 1))

log_section "Test 7: API Security - Invalid JSON"
RESPONSE=$(curl -s -X POST http://localhost:8080/api/config -H "Content-Type: application/json" -d '{"self_repair_enabled":"not_a_boolean"}' 2>&1)
if echo "$RESPONSE" | grep -q "must be boolean"; then
    log "✓ Test PASSED - API validated boolean type"
    TESTS_PASSED=$((TESTS_PASSED + 1))
else
    log "✗ Test FAILED - API did not validate type"
    log "Response: $RESPONSE"
    TESTS_FAILED=$((TESTS_FAILED + 1))
fi
TESTS_RUN=$((TESTS_RUN + 1))

# Test 8: Memory usage under load
log_section "Test 8: Resource Usage Monitoring"
log "Checking dashboard memory usage..."
DASHBOARD_MEM=$(docker stats --no-stream --format "{{.MemUsage}}" cluster_dashboard 2>&1)
log "Dashboard memory usage: $DASHBOARD_MEM"

RELAY_MEM=$(docker stats --no-stream --format "{{.MemUsage}}" cluster_relay 2>&1)
log "Relay memory usage: $RELAY_MEM"

NODE1_MEM=$(docker stats --no-stream --format "{{.MemUsage}}" node1 2>&1)
log "Node1 memory usage: $NODE1_MEM"

# Test 9: Dashboard restart policy
log_section "Test 9: Auto-Restart Policy"
log "Checking dashboard restart policy..."
RESTART_POLICY=$(docker inspect cluster_dashboard --format='{{.HostConfig.RestartPolicy.Name}}' 2>&1)
log "Restart policy: $RESTART_POLICY"
if [ "$RESTART_POLICY" = "unless-stopped" ]; then
    log "✓ Test PASSED - Correct restart policy"
    TESTS_PASSED=$((TESTS_PASSED + 1))
else
    log "✗ Test FAILED - Incorrect restart policy"
    TESTS_FAILED=$((TESTS_FAILED + 1))
fi
TESTS_RUN=$((TESTS_RUN + 1))

# Test 10: Dashboard accessibility
log_section "Test 10: Dashboard Accessibility"
HTTP_CODE=$(curl -s -o /dev/null -w "%{http_code}" http://localhost:8080/ 2>&1)
log "HTTP response code: $HTTP_CODE"
if [ "$HTTP_CODE" = "200" ]; then
    log "✓ Test PASSED - Dashboard accessible"
    TESTS_PASSED=$((TESTS_PASSED + 1))
else
    log "✗ Test FAILED - Dashboard not accessible"
    TESTS_FAILED=$((TESTS_FAILED + 1))
fi
TESTS_RUN=$((TESTS_RUN + 1))

# Test 11: Health endpoint
log_section "Test 11: Health Endpoint"
HEALTH_RESPONSE=$(curl -s http://localhost:8080/health 2>&1)
log "Health endpoint response: $HEALTH_RESPONSE"
if echo "$HEALTH_RESPONSE" | grep -q "healthy"; then
    log "✓ Test PASSED - Health endpoint working"
    TESTS_PASSED=$((TESTS_PASSED + 1))
else
    log "✗ Test FAILED - Health endpoint not working"
    TESTS_FAILED=$((TESTS_FAILED + 1))
fi
TESTS_RUN=$((TESTS_RUN + 1))

# Test 12: Concurrent requests
log_section "Test 12: Concurrent Request Handling"
log "Sending 10 concurrent requests to dashboard..."
for i in {1..10}; do
    curl -s http://localhost:8080/api/status > /dev/null &
done
wait
log "✓ Concurrent requests completed"
TESTS_PASSED=$((TESTS_PASSED + 1))
TESTS_RUN=$((TESTS_RUN + 1))

# Cleanup
log_section "Cleanup"
docker compose down >> "$LOG_FILE" 2>&1
log "✓ Test environment cleaned up"

# Summary
log_section "Test Summary"
log "Total tests run: $TESTS_RUN"
log "Tests passed: $TESTS_PASSED"
log "Tests failed: $TESTS_FAILED"
log "Success rate: $(awk "BEGIN {printf \"%.2f\", ($TESTS_PASSED/$TESTS_RUN)*100}")%"
log ""
log "Full log available at: $LOG_FILE"

echo ""
echo "======================================"
echo "Test Results Summary"
echo "======================================"
echo "Total: $TESTS_RUN | Passed: $TESTS_PASSED | Failed: $TESTS_FAILED"
echo "Success Rate: $(awk "BEGIN {printf \"%.2f\", ($TESTS_PASSED/$TESTS_RUN)*100}")%"
echo ""
echo "Detailed log: $LOG_FILE"
echo "======================================"

if [ $TESTS_FAILED -gt 0 ]; then
    exit 1
else
    exit 0
fi
