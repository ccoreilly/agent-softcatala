#!/bin/bash

# Exit on any error
set -e

echo "Starting safe build process..."

# Set environment variables to prefer wheels and avoid problematic builds
export PIP_PREFER_BINARY=1
export PIP_NO_CACHE_DIR=1
export PIP_DISABLE_PIP_VERSION_CHECK=1

# Update pip to latest version
python -m pip install --upgrade pip

# Install wheel and setuptools
pip install wheel setuptools

# Use the safer requirements file
echo "Installing safe requirements..."
pip install --prefer-binary -r requirements-safe.txt

echo "Safe build completed successfully!"