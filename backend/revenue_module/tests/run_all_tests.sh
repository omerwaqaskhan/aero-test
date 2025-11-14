#!/bin/bash
# Comprehensive test runner for all revenue functionality

set -e  # Exit on error

echo "=========================================="
echo "Running Comprehensive Revenue Module Tests"
echo "=========================================="
echo ""

# Colors for output
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Test counter
PASSED=0
FAILED=0

# Function to run tests and count results
run_test_suite() {
    local test_file=$1
    local test_name=$2
    
    echo -n "Testing $test_name... "
    
    if python -m pytest "$test_file" -v --tb=short > /tmp/test_output.log 2>&1; then
        echo -e "${GREEN}✓ PASSED${NC}"
        PASSED=$((PASSED + 1))
        return 0
    else
        echo -e "${RED}✗ FAILED${NC}"
        FAILED=$((FAILED + 1))
        cat /tmp/test_output.log | tail -20
        return 1
    fi
}

# Change to revenue module directory
cd "$(dirname "$0")/.."

echo "1. Unit Tests - Core Services"
echo "-------------------------------"

run_test_suite "tests/unit/test_subscription_service.py" "Subscription Service"
run_test_suite "tests/unit/test_lead_service.py" "Lead Service"
run_test_suite "tests/unit/test_hotel_listing_service.py" "Hotel Listing Service"
run_test_suite "tests/unit/test_sponsored_placement_service.py" "Sponsored Placement Service"
run_test_suite "tests/unit/test_ad_revenue_service.py" "Ad Revenue Service"
run_test_suite "tests/unit/test_revenue_analytics_service.py" "Revenue Analytics Service"
run_test_suite "tests/unit/test_stripe_service.py" "Stripe Service"
run_test_suite "tests/unit/test_stripe_checkout.py" "Stripe Checkout"
run_test_suite "tests/unit/test_edge_cases.py" "Edge Cases"

echo ""
echo "2. Integration Tests"
echo "-------------------"

run_test_suite "tests/integration/test_revenue_api.py" "Revenue API"
run_test_suite "tests/integration/test_hotel_claim_flow.py" "Hotel Claim Flow"
run_test_suite "tests/integration/test_complete_flows.py" "Complete Flows"
run_test_suite "tests/integration/test_end_to_end.py" "End-to-End Flows"

echo ""
echo "3. Search Integration Tests"
echo "--------------------------"

if [ -f "../search_booking_module/tests/unit/test_sponsored_search.py" ]; then
    run_test_suite "../search_booking_module/tests/unit/test_sponsored_search.py" "Sponsored Search Integration"
else
    echo -e "${YELLOW}⚠ Skipped: Sponsored search tests not found${NC}"
fi

echo ""
echo "=========================================="
echo "Test Summary"
echo "=========================================="
echo -e "Passed: ${GREEN}$PASSED${NC}"
echo -e "Failed: ${RED}$FAILED${NC}"
echo ""

if [ $FAILED -eq 0 ]; then
    echo -e "${GREEN}✓ All tests passed!${NC}"
    exit 0
else
    echo -e "${RED}✗ Some tests failed${NC}"
    exit 1
fi

