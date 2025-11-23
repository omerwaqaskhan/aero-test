#!/bin/bash

# Quick test script for search API

echo "Testing Search API..."
echo "===================="
echo ""

# Test 1: Health check
echo "1. Testing health endpoint..."
curl -s http://localhost:8000/api/v1/search-booking/health
echo ""
echo ""

# Test 2: Search endpoint
echo "2. Testing search endpoint..."
curl -s "http://localhost:8000/api/v1/search-booking/search?destination=New%20York&check_in=2024-11-15&check_out=2024-11-17&guests=2&rooms=1" | jq '.' 2>/dev/null || curl -s "http://localhost:8000/api/v1/search-booking/search?destination=New%20York&check_in=2024-11-15&check_out=2024-11-17&guests=2&rooms=1"
echo ""
echo ""

# Test 3: Check if endpoint exists
echo "3. Checking if endpoint is registered..."
curl -s http://localhost:8000/docs | grep -i "search-booking" || echo "Endpoint not found in docs"
echo ""

echo "Done!"

