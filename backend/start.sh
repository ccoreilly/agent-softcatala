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

# Check for required environment variables
echo "🔍 Checking environment configuration..."

# Check if either OLLAMA_URL or ZHIPUAI_API_KEY is set
OLLAMA_URL_SET=""
ZHIPU_KEY_SET=""

if [ -n "$OLLAMA_URL" ]; then
    OLLAMA_URL_SET="yes"
    echo "✅ OLLAMA_URL environment variable is set: $OLLAMA_URL"
fi

if [ -n "$ZHIPUAI_API_KEY" ]; then
    ZHIPU_KEY_SET="yes"
    echo "✅ ZHIPUAI_API_KEY environment variable is set"
fi

# Check .env file if it exists
if [ -f ".env" ]; then
    echo "📋 Found .env file, checking for additional configuration..."
    if [ -z "$OLLAMA_URL_SET" ] && grep -q "^OLLAMA_URL=" .env; then
        OLLAMA_URL_FROM_FILE=$(grep "^OLLAMA_URL=" .env | cut -d'=' -f2 | tr -d ' "'"'"'')
        if [ -n "$OLLAMA_URL_FROM_FILE" ]; then
            OLLAMA_URL_SET="yes"
            echo "✅ OLLAMA_URL found in .env file: $OLLAMA_URL_FROM_FILE"
        fi
    fi
    
    if [ -z "$ZHIPU_KEY_SET" ] && grep -q "^ZHIPUAI_API_KEY=" .env; then
        ZHIPU_KEY_FROM_FILE=$(grep "^ZHIPUAI_API_KEY=" .env | cut -d'=' -f2 | tr -d ' "'"'"'')
        if [ -n "$ZHIPU_KEY_FROM_FILE" ]; then
            ZHIPU_KEY_SET="yes"
            echo "✅ ZHIPUAI_API_KEY found in .env file"
        fi
    fi
fi

# Validate that at least one provider is configured
if [ -z "$OLLAMA_URL_SET" ] && [ -z "$ZHIPU_KEY_SET" ]; then
    echo "❌ No LLM providers configured!"
    echo ""
    echo "Please set at least one of the following:"
    echo "  Option 1 - Environment variables:"
    echo "    export OLLAMA_URL=http://localhost:11434"
    echo "    export ZHIPUAI_API_KEY=your_zhipu_api_key"
    echo ""
    echo "  Option 2 - Create .env file:"
    echo "    cp .env.example .env"
    echo "    # Edit .env file with your configuration"
    echo ""
    echo "  Option 3 - Quick Ollama setup:"
    echo "    OLLAMA_URL=http://localhost:11434 python3 main.py"
    echo ""
    exit 1
fi

# Check if Ollama is accessible (if OLLAMA_URL is set)
if [ -n "$OLLAMA_URL_SET" ] && command -v curl &> /dev/null; then
    # Get OLLAMA_URL from environment or .env file
    if [ -n "$OLLAMA_URL" ]; then
        OLLAMA_CHECK_URL="$OLLAMA_URL"
    elif [ -f ".env" ]; then
        OLLAMA_CHECK_URL=$(grep "^OLLAMA_URL=" .env | cut -d'=' -f2 | tr -d ' "'"'"'' || echo "http://localhost:11434")
    else
        OLLAMA_CHECK_URL="http://localhost:11434"
    fi
    
    if curl -s "$OLLAMA_CHECK_URL/api/tags" > /dev/null 2>&1; then
        echo "✅ Ollama is running and accessible at $OLLAMA_CHECK_URL"
    else
        echo "⚠️  Ollama is not accessible at $OLLAMA_CHECK_URL"
        echo "   - Make sure Ollama is installed and running: ollama serve"
        echo "   - Pull a model: ollama pull llama3.2"
        echo "   - The service will still start but may fail at runtime"
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