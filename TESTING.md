# NiA-Cluster Testing & Benchmarking Guide

## Overview

This document describes the comprehensive testing and benchmarking strategy for the NiA-Cluster dashboard and system.

## Test Suites

### 1. Basic Test Suite (`test.sh`)
Basic validation of core functionality:
- Docker image builds correctly
- Help commands work
- Command-line validation
- Basic error handling

**Usage:**
```bash
./test.sh
```

### 2. Dashboard Test Suite (`test-dashboard.sh`)
Comprehensive dashboard functionality tests:
- Dashboard startup and health checks
- API endpoint functionality
- Container orchestration
- Integration with cluster components

**Usage:**
```bash
./test-dashboard.sh
```

**Tests Included:**
- ✓ Help command works
- ✓ Container starts successfully
- ✓ Web interface accessibility
- ✓ Health check endpoint
- ✓ API endpoints functionality
- ✓ Relay monitoring

### 3. Debug & Failure Test Suite (`test-debug-failures.sh`)
Tests failure scenarios and recovery mechanisms:
- Dashboard behavior with no relay
- Invalid input handling
- Relay failure detection
- Self-repair functionality
- API security validation
- Resource usage monitoring
- Auto-restart policy
- Concurrent request handling

**Usage:**
```bash
./test-debug-failures.sh
```

**Failure Scenarios Tested:**
1. **No Relay Available**: Dashboard handles connection failures gracefully
2. **Invalid Port**: Rejects invalid configuration
3. **Relay Failure**: Detects when relay stops responding
4. **API Security**: Validates input and rejects invalid requests
5. **Type Validation**: Ensures proper data types
6. **Concurrent Access**: Handles multiple simultaneous requests

**Output:**
- Creates timestamped log files in `test-logs/` directory
- Provides detailed test results with pass/fail status
- Logs resource usage and performance metrics

### 4. Benchmark Suite (`benchmark.sh`)
Performance and resource usage benchmarks:
- Dashboard startup time
- API response times
- Resource consumption (CPU/memory)
- Concurrent connection handling
- Failure detection latency
- Page load performance

**Usage:**
```bash
./benchmark.sh
```

**Metrics Collected:**
1. **Startup Time**: How long dashboard takes to become available
2. **API Latency**: Average response time for endpoints
   - `/api/status`
   - `/health`
   - `/api/config`
3. **Resource Usage**: CPU and memory consumption over time
4. **Concurrent Handling**: Performance with 10, 50 concurrent requests
5. **Failure Detection**: Time to detect relay failure
6. **Page Load**: Initial dashboard page load time

**Comparison:**
Benchmarks are compared against typical monitoring solutions:
- Prometheus
- Grafana
- Kubernetes Dashboard

## Test Logs

All tests generate detailed logs in the `test-logs/` directory:
- `debug-failures-TIMESTAMP.log` - Debug and failure test results
- `benchmark-TIMESTAMP.log` - Performance benchmark results

## Running All Tests

To run the complete test suite:

```bash
# Basic tests
./test.sh

# Dashboard functionality
./test-dashboard.sh

# Failure scenarios
./test-debug-failures.sh

# Performance benchmarks
./benchmark.sh
```

Or run them all in sequence:
```bash
./test.sh && ./test-dashboard.sh && ./test-debug-failures.sh && ./benchmark.sh
```

## Continuous Integration

The test suites are designed to be run in CI/CD pipelines:

```yaml
# Example GitHub Actions workflow
- name: Run Tests
  run: |
    ./test.sh
    ./test-dashboard.sh
    ./test-debug-failures.sh
    ./benchmark.sh
```

## Interpreting Results

### Success Criteria

**Basic Tests:**
- All validation tests pass
- Docker build succeeds
- Help commands display correctly

**Dashboard Tests:**
- All 6 tests pass
- Dashboard is accessible
- API endpoints respond correctly
- Relay monitoring works

**Debug & Failure Tests:**
- Success rate > 90%
- Failure scenarios handled gracefully
- API security validations pass
- Auto-restart policy configured

**Benchmarks:**
- Startup time < 10s
- API latency < 0.5s
- Failure detection < 30s
- Handles 50+ concurrent requests

### Performance Targets

| Metric | Target | Good | Excellent |
|--------|--------|------|-----------|
| Startup Time | < 10s | < 5s | < 3s |
| API Latency | < 0.5s | < 0.1s | < 0.05s |
| Failure Detection | < 30s | < 15s | < 10s |
| Page Load | < 2s | < 1s | < 0.5s |
| Memory Usage | < 100MB | < 50MB | < 30MB |

## Troubleshooting Tests

### Tests Failing

1. **Docker Build Failures**
   ```bash
   docker build -t cluster-suite:latest .
   # Check for dependency issues
   docker run --rm cluster-suite:latest pip list
   ```

2. **Port Conflicts**
   ```bash
   # Check if ports are already in use
   lsof -i :8080
   lsof -i :4040
   # Kill conflicting processes or use different ports
   ```

3. **Timeout Issues**
   ```bash
   # Increase timeout in test scripts
   # Edit CHECK_INTERVAL or TIMEOUT variables
   ```

### Clean Test Environment

```bash
# Stop all containers
docker compose down

# Remove test containers
docker ps -a | grep test- | awk '{print $1}' | xargs docker rm -f

# Clean up logs
rm -rf test-logs/

# Rebuild from scratch
docker build --no-cache -t cluster-suite:latest .
```

## Best Practices

1. **Run tests in isolation**: Clean environment between test runs
2. **Review logs**: Check `test-logs/` for detailed failure information
3. **Baseline benchmarks**: Run benchmarks on consistent hardware
4. **Regular testing**: Run full suite before each release
5. **Monitor trends**: Track performance over time

## Adding New Tests

To add new test scenarios:

1. **For Functionality**: Add to `test-dashboard.sh`
2. **For Failures**: Add to `test-debug-failures.sh`
3. **For Performance**: Add to `benchmark.sh`

Example test template:
```bash
run_test "Test Description" \
    "command to run" \
    "pass or fail"
```

## Security Testing

Security validations are included in the failure test suite:
- Input validation on all endpoints
- CORS policy enforcement
- Type checking for configuration
- Component whitelist for repairs

## Load Testing

For additional load testing beyond the benchmark suite:

```bash
# Using Apache Bench
ab -n 1000 -c 10 http://localhost:8080/api/status

# Using wrk
wrk -t4 -c100 -d30s http://localhost:8080/api/status
```

## Resource Monitoring

Monitor resource usage during tests:

```bash
# Docker stats
docker stats

# System resources
htop

# Network traffic
iftop
```

## Reporting Issues

When reporting test failures, include:
1. Test script that failed
2. Complete log file from `test-logs/`
3. Docker version and system info
4. Steps to reproduce
5. Expected vs actual behavior

## References

- [Dashboard Guide](DASHBOARD.md)
- [Main README](README.md)
- [Docker Compose Configuration](docker-compose.yml)
