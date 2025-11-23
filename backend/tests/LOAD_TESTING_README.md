# Load Testing Guide

This directory contains load testing scripts for the LuftWay Travel Platform.

## Available Tools

### 1. Locust (Python)

**Installation:**
```bash
pip install locust
```

**Usage:**
```bash
# Start Locust web UI
locust -f backend/tests/load_test_locust.py --host=http://localhost:8000

# Or run headless
locust -f backend/tests/load_test_locust.py --host=http://localhost:8000 \
    --users 100 --spawn-rate 10 --run-time 5m --headless
```

Then open http://localhost:8089 in your browser to configure and start tests.

### 2. K6 (JavaScript)

**Installation:**
```bash
# macOS
brew install k6

# Linux
sudo gpg -k
sudo gpg --no-default-keyring --keyring /usr/share/keyrings/k6-archive-keyring.gpg --keyserver hkp://keyserver.ubuntu.com:80 --recv-keys C5AD17C747E3415A3642D57D77C6C491D6AC1D69
echo "deb [signed-by=/usr/share/keyrings/k6-archive-keyring.gpg] https://dl.k6.io/deb stable main" | sudo tee /etc/apt/sources.list.d/k6.list
sudo apt-get update
sudo apt-get install k6

# Or download from https://k6.io/docs/getting-started/installation/
```

**Usage:**
```bash
# Basic run
k6 run backend/tests/load_test_k6.js

# With custom options
k6 run --vus 100 --duration 5m backend/tests/load_test_k6.js

# With environment variable
BASE_URL=http://your-server.com k6 run backend/tests/load_test_k6.js
```

## Test Scenarios

Both scripts test:
- **Search Hotels** (most common - 60% of requests)
- **Hotel Details** (30% of requests)
- **Browse All Hotels** (10% of requests)
- **Health Check** (monitoring)

## Recommended Load Tests

### 1. Smoke Test (Verify system works)
- Users: 10
- Duration: 1 minute
- Purpose: Verify basic functionality

### 2. Load Test (Normal expected load)
- Users: 100
- Duration: 5 minutes
- Purpose: Test under normal conditions

### 3. Stress Test (Find breaking point)
- Users: 500-1000
- Duration: 10 minutes
- Purpose: Find maximum capacity

### 4. Spike Test (Sudden traffic)
- Users: 0 → 500 → 0
- Duration: 5 minutes
- Purpose: Test handling of traffic spikes

## Metrics to Monitor

- **Response Time**: p50, p95, p99 percentiles
- **Error Rate**: Should be < 1%
- **Throughput**: Requests per second
- **Resource Usage**: CPU, Memory, Database connections

## Before Running Tests

1. Ensure all services are running:
   ```bash
   docker compose up -d
   ```

2. Verify database has test data

3. Monitor system resources:
   ```bash
   docker stats
   ```

4. Check application logs:
   ```bash
   docker compose logs -f backend
   ```

## Interpreting Results

- **Response Time < 500ms**: Excellent
- **Response Time 500-1000ms**: Good
- **Response Time > 1000ms**: Needs optimization
- **Error Rate > 1%**: Investigate issues
- **Memory/CPU > 80%**: Scale resources

