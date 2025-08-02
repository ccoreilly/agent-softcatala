#!/bin/bash

# LangChain Chat Agent Backend with Telegram Bot
# This script starts both the HTTP API and Telegram bot

echo "🚀 Starting LangChain Chat Agent Backend with Telegram Bot..."

# Check if .env file exists
if [ ! -f ".env" ]; then
    echo "⚠️  Warning: .env file not found."
    echo "📝 Creating .env from .env.example..."
    cp .env.example .env
    echo "✅ Please edit .env file with your configuration before running again."
    echo ""
    echo "Required configuration:"
    echo "  - TELEGRAM_BOT_TOKEN: Get from @BotFather on Telegram"
    echo "  - OLLAMA_URL: Make sure Ollama is running (default: http://localhost:11434)"
    echo ""
    echo "Optional configuration:"
    echo "  - ZHIPU_API_KEY: For cloud AI models"
    echo "  - SEARCH_API_KEY: For enhanced search capabilities"
    exit 1
fi

# Check if TELEGRAM_BOT_TOKEN is set
if ! grep -q "^TELEGRAM_BOT_TOKEN=" .env || grep -q "^TELEGRAM_BOT_TOKEN=$" .env || grep -q "^#.*TELEGRAM_BOT_TOKEN=" .env; then
    echo "⚠️  Warning: TELEGRAM_BOT_TOKEN not configured in .env file."
    echo "📝 The service will start with HTTP API only."
    echo "🤖 To enable Telegram bot:"
    echo "   1. Create a bot with @BotFather on Telegram"
    echo "   2. Add TELEGRAM_BOT_TOKEN=your_token to .env file"
    echo "   3. Restart the service"
    echo ""
fi

# Check if dependencies are installed
echo "📦 Checking dependencies..."
if ! python3 -c "import telegram" 2>/dev/null; then
    echo "⚠️  python-telegram-bot not found. Installing dependencies..."
    pip3 install -r requirements.txt
    if [ $? -ne 0 ]; then
        echo "❌ Failed to install dependencies. Please run: pip3 install -r requirements.txt"
        exit 1
    fi
fi

# Check if Ollama is running (if using local models)
echo "🔍 Checking Ollama connection..."
OLLAMA_URL=$(grep "^OLLAMA_URL=" .env | cut -d'=' -f2 | tr -d ' "'"'"'')
if [ -z "$OLLAMA_URL" ]; then
    OLLAMA_URL="http://localhost:11434"
fi

if ! curl -s "$OLLAMA_URL/api/tags" > /dev/null 2>&1; then
    echo "⚠️  Warning: Cannot connect to Ollama at $OLLAMA_URL"
    echo "💡 Make sure Ollama is running:"
    echo "   - Install: curl -fsSL https://ollama.ai/install.sh | sh"
    echo "   - Start: ollama serve"
    echo "   - Pull a model: ollama pull llama2"
    echo ""
    echo "🚀 Starting anyway... (you can use cloud providers if configured)"
else
    echo "✅ Ollama connection successful"
fi

# Start the service
echo ""
echo "🎯 Starting services..."
echo "📡 HTTP API will be available at: http://localhost:8000"
echo "🤖 Telegram bot will start if token is configured"
echo "🛑 Press Ctrl+C to stop"
echo ""

# Load environment variables and start
source .env
python3 main.py