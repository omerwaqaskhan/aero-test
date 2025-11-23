#!/bin/bash
# Test runner script for revenue module

echo "Running revenue module unit tests..."
cd "$(dirname "$0")/.."
python -m pytest tests/unit/ -v --tb=short

echo ""
echo "Running revenue module integration tests..."
python -m pytest tests/integration/ -v --tb=short

echo ""
echo "Running all revenue module tests with coverage..."
python -m pytest tests/ -v --cov=revenue_module --cov-report=html --cov-report=term

