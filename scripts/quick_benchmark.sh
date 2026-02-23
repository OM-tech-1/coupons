#!/bin/bash

# Quick API Benchmark Script
# Tests if the API can handle 2000 requests per minute

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

# Configuration
API_URL="${1:-https://api.vouchergalaxy.com}"
ENDPOINT="${2:-/health}"
REQUESTS_PER_MIN=2000
DURATION=60  # seconds
CONCURRENT=50

echo -e "${BLUE}=== Quick API Benchmark ===${NC}"
echo ""
echo "Target: $API_URL$ENDPOINT"
echo "Goal: $REQUESTS_PER_MIN requests/minute"
echo "Duration: ${DURATION}s"
echo "Concurrent: $CONCURRENT"
echo ""

# Check if apache bench (ab) is installed
if ! command -v ab &> /dev/null; then
    echo -e "${YELLOW}Apache Bench (ab) not found. Installing...${NC}"
    if [[ "$OSTYPE" == "darwin"* ]]; then
        echo "ab is pre-installed on macOS"
    elif [[ "$OSTYPE" == "linux-gnu"* ]]; then
        sudo apt-get install -y apache2-utils
    fi
fi

# Calculate requests
TOTAL_REQUESTS=$((REQUESTS_PER_MIN * DURATION / 60))

echo -e "${GREEN}Starting benchmark...${NC}"
echo ""

# Run apache bench
ab -n $TOTAL_REQUESTS -c $CONCURRENT -t $DURATION "$API_URL$ENDPOINT" > /tmp/benchmark_result.txt 2>&1

# Parse results
echo -e "${BLUE}=== Results ===${NC}"
echo ""

# Extract key metrics
REQUESTS_PER_SEC=$(grep "Requests per second" /tmp/benchmark_result.txt | awk '{print $4}')
TIME_PER_REQUEST=$(grep "Time per request.*mean" /tmp/benchmark_result.txt | head -1 | awk '{print $4}')
FAILED_REQUESTS=$(grep "Failed requests" /tmp/benchmark_result.txt | awk '{print $3}')
TOTAL_COMPLETED=$(grep "Complete requests" /tmp/benchmark_result.txt | awk '{print $3}')

echo "Total Requests: $TOTAL_COMPLETED"
echo "Failed Requests: $FAILED_REQUESTS"
echo "Requests/sec: $REQUESTS_PER_SEC"
echo "Time/request: ${TIME_PER_REQUEST}ms"
echo ""

# Calculate if goal was met
REQUESTS_PER_MIN_ACTUAL=$(echo "$REQUESTS_PER_SEC * 60" | bc)
echo "Actual requests/min: ${REQUESTS_PER_MIN_ACTUAL%.*}"
echo "Target requests/min: $REQUESTS_PER_MIN"
echo ""

# Check if goal was met
if (( $(echo "$REQUESTS_PER_MIN_ACTUAL >= $REQUESTS_PER_MIN" | bc -l) )); then
    echo -e "${GREEN}✅ SUCCESS: API can handle $REQUESTS_PER_MIN requests/minute!${NC}"
else
    echo -e "${RED}❌ FAILED: API can only handle ${REQUESTS_PER_MIN_ACTUAL%.*} requests/minute${NC}"
fi

echo ""
echo "Full report saved to: /tmp/benchmark_result.txt"
echo ""

# Show percentiles
echo -e "${BLUE}Response Time Percentiles:${NC}"
grep "50%\|66%\|75%\|80%\|90%\|95%\|98%\|99%\|100%" /tmp/benchmark_result.txt | head -9

echo ""
