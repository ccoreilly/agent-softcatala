# Use Python 3.11 slim image for better compatibility
FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Install system dependencies including Rust prerequisites
RUN apt-get update && apt-get install -y \
    build-essential \
    curl \
    pkg-config \
    libssl-dev \
    && rm -rf /var/lib/apt/lists/*

# Install Rust and Cargo
RUN curl --proto '=https' --tlsv1.2 -sSf https://sh.rustup.rs | sh -s -- -y
ENV PATH="/root/.cargo/bin:${PATH}"

# Set Cargo environment variables for compatibility
ENV CARGO_HOME=/tmp/cargo
ENV RUSTUP_HOME=/tmp/rustup

# Create cargo directory with proper permissions
RUN mkdir -p /tmp/cargo/registry/cache

# Copy requirements first for better Docker layer caching
COPY requirements.txt .

# Upgrade pip and install wheel
RUN pip install --upgrade pip wheel

# Install Python dependencies with specific flags for Rust packages
RUN pip install --no-cache-dir \
    --prefer-binary \
    --force-reinstall \
    -r requirements.txt

# Copy application code
COPY . .

# Set environment variable for production
ENV PYTHONPATH=/app

# Expose port
EXPOSE 8000

# Run the application
CMD ["python", "main.py"]