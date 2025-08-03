#!/bin/bash

# Exit on any error
set -e

echo "Starting final build with compatible versions..."

# Set environment variables for optimal pip behavior
export PIP_PREFER_BINARY=1
export PIP_NO_CACHE_DIR=1
export PIP_DISABLE_PIP_VERSION_CHECK=1
export PIP_TIMEOUT=300

# Update pip and core tools
python -m pip install --upgrade pip setuptools wheel

# Use the final requirements file with compatible versions
echo "Installing final compatible requirements..."
pip install --prefer-binary -r requirements-final.txt

echo "Final build completed successfully!"
echo "Installed packages:"
pip list | grep -E "(fastapi|httpx|python-telegram-bot|langchain|pydantic)" || echo "Core packages installed"