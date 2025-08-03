#!/bin/bash

# Exit on any error
set -e

echo "Starting Python-safe build process..."

# Set environment variables for optimal pip behavior with newer Python
export PIP_PREFER_BINARY=1
export PIP_NO_CACHE_DIR=1
export PIP_DISABLE_PIP_VERSION_CHECK=1
export PIP_TIMEOUT=300
export PYTHONDONTWRITEBYTECODE=1

# Ensure we're using the right Python version
echo "Python version: $(python3 --version)"

# Update pip and essential tools
python3 -m pip install --upgrade pip setuptools wheel

# Install packages one by one to identify issues
echo "Installing core dependencies..."

# Install in order of dependency
python3 -m pip install --prefer-binary pydantic==2.10.0
python3 -m pip install --prefer-binary fastapi==0.115.0
python3 -m pip install --prefer-binary uvicorn[standard]==0.32.0
python3 -m pip install --prefer-binary httpx==0.27.0
python3 -m pip install --prefer-binary requests==2.32.0
python3 -m pip install --prefer-binary python-dotenv==1.0.1
python3 -m pip install --prefer-binary python-multipart==0.0.12
python3 -m pip install --prefer-binary beautifulsoup4==4.12.3
python3 -m pip install --prefer-binary aiofiles==24.1.0
python3 -m pip install --prefer-binary httpx-sse==0.4.0
python3 -m pip install --prefer-binary PyJWT==2.10.0
python3 -m pip install --prefer-binary PyPDF2==3.0.1

echo "Installing Telegram bot..."
python3 -m pip install --prefer-binary python-telegram-bot==21.9

echo "Installing LangChain components (minimal)..."
python3 -m pip install --prefer-binary langchain-core==0.3.21

echo "Python-safe build completed successfully!"
echo "Installed packages:"
python3 -m pip list