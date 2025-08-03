#!/bin/bash

# LangChain Chat Agent Backend with Telegram Bot Startup Script

set -e

echo "🚀 Starting LangChain Chat Agent Backend with Telegram Bot..."

# Check if .env file exists
if [ ! -f ".env" ]; then
    echo "⚠️  Warning: .env file not found."
    echo "📝 You can either:"
    echo "   1. Create .env from template: cp .env.example .env"
    echo "   2. Set environment variables directly"
    echo ""
    echo "Required environment variables:"
    echo "  - TELEGRAM_BOT_TOKEN: Your Telegram bot token"
    echo "  - At least one of:"
    echo "    * OLLAMA_URL: For local Ollama provider"
    echo "    * ZHIPUAI_API_KEY: For Zhipu AI provider"
    echo ""
fi

# Check for TELEGRAM_BOT_TOKEN
if [ -z "$TELEGRAM_BOT_TOKEN" ]; then
    # Check if it's in .env file
    if [ -f ".env" ] && grep -q "^TELEGRAM_BOT_TOKEN=" .env && ! grep -q "^TELEGRAM_BOT_TOKEN=$" .env && ! grep -q "^#.*TELEGRAM_BOT_TOKEN=" .env; then
        echo "✅ TELEGRAM_BOT_TOKEN found in .env file"
    else
        echo "❌ TELEGRAM_BOT_TOKEN not configured!"
        echo ""
        echo "Please set your Telegram bot token:"
        echo "  Option 1 - Environment variable:"
        echo "    export TELEGRAM_BOT_TOKEN=your_token_here"
        echo ""
        echo "  Option 2 - Add to .env file:"
        echo "    echo 'TELEGRAM_BOT_TOKEN=your_token_here' >> .env"
        echo ""
        echo "To get a token:"
        echo "  1. Message @BotFather on Telegram"
        echo "  2. Create a new bot with /newbot"
        echo "  3. Copy the token and set it as TELEGRAM_BOT_TOKEN"
        echo ""
        exit 1
    fi
else
    echo "✅ TELEGRAM_BOT_TOKEN environment variable is set"
fi

# Check for LLM providers
echo "🔍 Checking LLM provider configuration..."

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
    echo "📋 Checking .env file for additional configuration..."
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
    echo "  - OLLAMA_URL: For local Ollama provider"
    echo "  - ZHIPUAI_API_KEY: For Zhipu AI provider"
    echo ""
    exit 1
fi

# Check if Python is available
if ! command -v python3 &> /dev/null; then
    echo "❌ Python 3 is not installed. Please install Python 3.8+ first."
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

# Install dependencies including Telegram bot support
echo "📥 Installing dependencies with Telegram bot support..."
pip install -r requirements.txt
pip install python-telegram-bot==21.0.1

# Check if Ollama is accessible (if configured)
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
echo "Starting the backend with Telegram bot support..."

# Load environment variables and start the service
if [ -f ".env" ]; then
    source .env
fi

python3 main.py