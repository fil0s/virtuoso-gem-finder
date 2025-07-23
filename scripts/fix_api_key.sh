#!/bin/bash

echo "=========================================="
echo "    API KEY FIXER AND DEBUG LAUNCHER"
echo "=========================================="

# Check if .env file exists
if [ ! -f ".env" ]; then
    echo "❌ ERROR: .env file not found!"
    echo "Please create it from the template:"
    echo "   cp config/env.template .env"
    echo "   Then edit .env with your API keys"
    exit 1
fi

# Extract and export API key from .env file
echo "🔑 Extracting API keys from .env file..."
BIRDEYE_API_KEY=$(grep "BIRDEYE_API_KEY" .env | cut -d '=' -f2)

# Strip quotes and whitespace if present
BIRDEYE_API_KEY=$(echo $BIRDEYE_API_KEY | sed 's/^["\t ]*//;s/["\t ]*$//')

# Check if API key was found
if [ -z "$BIRDEYE_API_KEY" ]; then
    echo "❌ ERROR: BIRDEYE_API_KEY not found in .env file!"
    echo "Please add it to your .env file:"
    echo "BIRDEYE_API_KEY=your_api_key_here"
    exit 1
fi

# Export the API key as environment variable
export BIRDEYE_API_KEY="$BIRDEYE_API_KEY"
echo "✅ Successfully loaded BIRDEYE_API_KEY: ${BIRDEYE_API_KEY:0:8}...${BIRDEYE_API_KEY: -4}"

# Look for Telegram credentials too
TELEGRAM_BOT_TOKEN=$(grep "TELEGRAM_BOT_TOKEN" .env | cut -d '=' -f2)
TELEGRAM_CHAT_ID=$(grep "TELEGRAM_CHAT_ID" .env | cut -d '=' -f2)

# Strip quotes and whitespace if present
TELEGRAM_BOT_TOKEN=$(echo $TELEGRAM_BOT_TOKEN | sed 's/^["\t ]*//;s/["\t ]*$//')
TELEGRAM_CHAT_ID=$(echo $TELEGRAM_CHAT_ID | sed 's/^["\t ]*//;s/["\t ]*$//')

if [ ! -z "$TELEGRAM_BOT_TOKEN" ] && [ ! -z "$TELEGRAM_CHAT_ID" ]; then
    export TELEGRAM_BOT_TOKEN="$TELEGRAM_BOT_TOKEN"
    export TELEGRAM_CHAT_ID="$TELEGRAM_CHAT_ID"
    echo "✅ Successfully loaded Telegram credentials"
fi

# Look for Helius API key if present
HELIUS_API_KEY=$(grep "HELIUS_API_KEY" .env | cut -d '=' -f2)
# Strip quotes and whitespace if present
HELIUS_API_KEY=$(echo $HELIUS_API_KEY | sed 's/^["\t ]*//;s/["\t ]*$//')

if [ ! -z "$HELIUS_API_KEY" ]; then
    export HELIUS_API_KEY="$HELIUS_API_KEY"
    echo "✅ Successfully loaded Helius API key"
fi

echo "=========================================="
echo "    LAUNCHING DEBUG SESSION"
echo "=========================================="

# Launch the debug session with the properly exported API key
bash run_debug_3h.sh

echo "=========================================="
echo "    DEBUG SESSION COMPLETED"
echo "==========================================" 