#!/bin/bash

# Backend Test Runner Script
# This script runs all backend tests with proper configuration

set -e  # Exit on any error

echo "🧪 Starting Backend Test Suite"
echo "================================"

# Change to backend directory
cd "$(dirname "$0")"

# Check if virtual environment exists and activate it
if [ -d "venv" ]; then
    echo "📦 Activating virtual environment..."
    source venv/bin/activate
elif [ -d ".venv" ]; then
    echo "📦 Activating virtual environment..."
    source .venv/bin/activate
else
    echo "⚠️  No virtual environment found. Install dependencies manually if needed."
fi

# Install dependencies if needed
if [ "$1" = "--install" ] || [ ! -f ".deps_installed" ]; then
    echo "📦 Installing dependencies..."
    pip install -r requirements.txt
    pip install -r requirements-dev.txt
    touch .deps_installed
    echo "✅ Dependencies installed"
fi

# Run linting
echo ""
echo "🔍 Running code quality checks..."
echo "--------------------------------"

# Check for syntax errors and undefined names
echo "Running flake8 (syntax check)..."
flake8 . --count --select=E9,F63,F7,F82 --show-source --statistics --exclude=venv,.venv,tests

# Run additional linting (warnings only)
echo "Running flake8 (style check)..."
flake8 . --count --exit-zero --max-complexity=10 --max-line-length=127 --statistics --exclude=venv,.venv

# Run tests
echo ""
echo "🧪 Running test suite..."
echo "------------------------"

# Run pytest with coverage
python3 -m pytest tests/ -v \
    --cov=. \
    --cov-report=term-missing \
    --cov-report=html:htmlcov \
    --cov-exclude=tests/* \
    --cov-exclude=venv/* \
    --cov-exclude=.venv/* \
    --tb=short

echo ""
echo "✅ All tests completed!"
echo ""
echo "📊 Coverage report generated in: htmlcov/index.html"
echo "🚀 Ready for deployment!"