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

# Install Rust and Cargo (still needed for some Python packages)
RUN curl --proto '=https' --tlsv1.2 -sSf https://sh.rustup.rs | sh -s -- -y
ENV PATH="/root/.cargo/bin:${PATH}"

# Set Cargo environment variables for compatibility
ENV CARGO_HOME=/tmp/cargo
ENV RUSTUP_HOME=/tmp/rustup

# Create cargo directory with proper permissions
RUN mkdir -p /tmp/cargo/registry/cache

# Install uv
COPY --from=ghcr.io/astral-sh/uv:latest /uv /usr/local/bin/uv

# Copy dependency files first for better Docker layer caching
COPY pyproject.toml .

# Install Python dependencies using uv
RUN uv venv /opt/venv
ENV VIRTUAL_ENV=/opt/venv
ENV PATH="/opt/venv/bin:${PATH}"

# Install dependencies using uv
RUN uv sync --no-dev

# Copy application code
COPY . .

# Set environment variable for production
ENV PYTHONPATH=/app

# Expose port
EXPOSE 8000

# Run the application
CMD ["python", "main.py"]