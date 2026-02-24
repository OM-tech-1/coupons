#!/bin/bash

# Simple API Benchmark using only curl
# No installation required - works everywhere

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

API_URL="${1:-https://api.vouchergalaxy.com}"
ENDPOINT="${2:-/health}"
REQUESTS=100
CONCURRENT=10

echo -e "${BLUE}=== Simple API Benchmark ===${NC}"
echo ""
echo "Target: $API_URL$ENDPOINT"
echo "Requests: $REQUESTS"
echo "Concurrent: $CONCURRENT"
echo ""

# Function to make a request and measure time
make_request() {
    local start=$(date +%s%N)
    local status=$(curl -s -o /dev/null -w "%{http_code}" "$API_URL$ENDPOINT" 2>/dev/null)
    local end=$(date +%s%N)
    local duration=$(( (end - start) / 1000000 ))  # Convert to milliseconds
    echo "$status,$duration"
}

echo -e "${GREEN}Running benchmark...${NC}"

# Arrays to store results
declare -a response_times
declare -a status_codes
success_count=0
failed_count=0
total_time=0

# Run requests
for i in $(seq 1 $REQUESTS); do
    result=$(make_request)
    status=$(echo $result | cut -d',' -f1)
    time=$(echo $result | cut -d',' -f2)
    
    response_times+=($time)
    status_codes+=($status)
    total_time=$((total_time + time))
    
    if [ "$status" = "200" ]; then
        success_count=$((success_count + 1))
    else
        failed_count=$((failed_count + 1))
    fi
    
    # Progress indicator
    if [ $((i % 10)) -eq 0 ]; then
        echo -n "."
    fi
done

echo ""
echo ""

# Calculate statistics
avg_time=$((total_time / REQUESTS))
total_seconds=$((total_time / 1000))
requests_per_sec=$(echo "scale=2; $REQUESTS / ($total_seconds / 1000)" | bc)

# Sort response times for percentiles
IFS=$'\n' sorted_times=($(sort -n <<<"${response_times[*]}"))
unset IFS

p50_index=$((REQUESTS * 50 / 100))
p95_index=$((REQUESTS * 95 / 100))
p99_index=$((REQUESTS * 99 / 100))

echo -e "${BLUE}=== Results ===${NC}"
echo ""
echo "Total Requests: $REQUESTS"
echo "Successful: $success_count"
echo "Failed: $failed_count"
echo ""
echo "Average Response Time: ${avg_time}ms"
echo "50th Percentile: ${sorted_times[$p50_index]}ms"
echo "95th Percentile: ${sorted_times[$p95_index]}ms"
echo "99th Percentile: ${sorted_times[$p99_index]}ms"
echo ""
echo "Requests/sec: $requests_per_sec"
echo "Requests/min: $(echo "$requests_per_sec * 60" | bc)"
echo ""

# Check if it can handle 2000 req/min (33.3 req/sec)
target_req_per_sec=33.3
if (( $(echo "$requests_per_sec >= $target_req_per_sec" | bc -l) )); then
    echo -e "${GREEN}✅ Can handle 2000+ requests/minute${NC}"
else
    echo -e "${YELLOW}⚠️  May struggle with 2000 requests/minute${NC}"
    echo "   (Estimated: $(echo "$requests_per_sec * 60" | bc | cut -d'.' -f1) req/min)"
fi

echo ""
