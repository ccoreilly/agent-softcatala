#!/bin/bash

# Exit on any error
set -e

echo "Starting modern build process..."

# Set environment variables for optimal pip behavior
export PIP_PREFER_BINARY=1
export PIP_NO_CACHE_DIR=1
export PIP_DISABLE_PIP_VERSION_CHECK=1
export PIP_TIMEOUT=300

# Update pip and core tools
python -m pip install --upgrade pip setuptools wheel

# Install dependencies with version resolution strategy
echo "Installing requirements with compatible versions..."

# First install core packages that are less likely to have issues
pip install --prefer-binary \
    fastapi==0.115.0 \
    uvicorn[standard]==0.32.0 \
    pydantic==2.10.0 \
    httpx==0.27.0 \
    requests==2.32.0 \
    python-dotenv==1.0.1

# Then install other dependencies
pip install --prefer-binary \
    python-multipart==0.0.12 \
    beautifulsoup4==4.12.3 \
    aiofiles==24.1.0 \
    httpx-sse==0.4.0 \
    PyJWT==2.10.0 \
    PyPDF2==3.0.1 \
    python-telegram-bot==21.9

# Finally install LangChain components (if needed)
echo "Installing LangChain components..."
pip install --prefer-binary \
    langchain-core==0.3.21 \
    langchain-text-splitters==0.3.2

echo "Modern build completed successfully!"