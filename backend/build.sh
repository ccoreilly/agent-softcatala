#!/bin/bash

# Exit on any error
set -e

echo "Starting build process..."

# Set pip configuration for better wheel handling
export PIP_PREFER_BINARY=1
export PIP_ONLY_BINARY=":all:"
export PIP_NO_CACHE_DIR=1

# Update pip to latest version
python -m pip install --upgrade pip

# Install wheel first
pip install wheel

# Try to install requirements with prefer-binary first
echo "Installing requirements with prefer-binary..."
pip install --prefer-binary --only-binary=:all: -r requirements.txt || {
    echo "Binary installation failed, trying with relaxed restrictions..."
    # If that fails, try with specific packages that might need source builds
    pip install --prefer-binary -r requirements.txt
}

echo "Build completed successfully!"