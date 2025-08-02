#!/bin/bash

# LangChain Chat Agent Backend Startup Script

set -e

echo "🚀 Starting LangChain Chat Agent Backend..."

# Check if Python is available
if ! command -v python3 &> /dev/null; then
    echo "❌ Python 3 is not installed. Please install Python 3.8+ first."
    exit 1
fi

# Check if pip is available
if ! command -v pip &> /dev/null && ! command -v pip3 &> /dev/null; then
    echo "❌ pip is not installed. Please install pip first."
    exit 1
fi

# Create virtual environment if it doesn't exist
if [ ! -d "venv" ]; then
    echo "📦 Creating virtual environment..."
    python3 -m venv venv
fi

# Activate virtual environment
echo "🔧 Activating virtual environment..."
source venv/bin/activate

# Install dependencies
echo "📥 Installing dependencies..."
pip install -r requirements.txt

# Check if .env file exists
if [ ! -f ".env" ]; then
    echo "⚙️  Creating .env file from template..."
    cp .env.example .env
    echo "📝 Please edit .env file with your configuration!"
    echo "   - Set ZHIPUAI_API_KEY if you want to use Zhipu AI"
    echo "   - Configure OLLAMA_URL if using custom Ollama instance"
fi

# Check if Ollama is running (optional)
if command -v curl &> /dev/null; then
    OLLAMA_URL=$(grep OLLAMA_URL .env | cut -d '=' -f2 | tr -d '"' || echo "http://localhost:11434")
    if curl -s "$OLLAMA_URL/api/tags" > /dev/null 2>&1; then
        echo "✅ Ollama is running and accessible"
    else
        echo "⚠️  Ollama is not accessible at $OLLAMA_URL"
        echo "   - Make sure Ollama is installed and running: ollama serve"
        echo "   - Pull a model: ollama pull llama3.2"
    fi
fi

echo ""
echo "🎉 Setup completed!"
echo ""
echo "To start the backend:"
echo "  python3 main.py"
echo ""
echo "Or with uvicorn:"
echo "  uvicorn main:app --host 0.0.0.0 --port 8000 --reload"
echo ""
echo "API will be available at: http://localhost:8000"
echo "Documentation at: http://localhost:8000/docs"