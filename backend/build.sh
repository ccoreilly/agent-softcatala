#!/bin/bash

# Exit on any error
set -e

echo "Starting build process..."

# Set pip configuration for better wheel handling (but allow source builds when needed)
export PIP_PREFER_BINARY=1
export PIP_NO_CACHE_DIR=1

# Update pip to latest version
python -m pip install --upgrade pip

# Install wheel and setuptools first
pip install wheel setuptools

# Install requirements with prefer-binary (but allow source builds for problematic packages)
echo "Installing requirements with prefer-binary..."
pip install --prefer-binary --upgrade -r requirements.txt

echo "Build completed successfully!"