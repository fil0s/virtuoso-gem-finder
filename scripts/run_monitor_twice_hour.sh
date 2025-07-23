#!/bin/bash
# Run Virtuoso Gem Hunter with 30-minute interval (twice per hour)
# All features fully operational

echo "=========================================="
echo "    VIRTUOSO GEM HUNTER - TWICE HOURLY"
echo "=========================================="

echo "🔍 Setting up monitoring environment..."

# Create required directory structure
mkdir -p logs
mkdir -p data/discovery_results
mkdir -p data/whale_movements
mkdir -p data/trader_performance
mkdir -p data/strategy_executions

# Set timestamp for this monitoring session
TIMESTAMP=$(date +"%Y%m%d_%H%M%S")
LOG_FILE="logs/monitor_session_${TIMESTAMP}.log"
ERROR_LOG="logs/error_session_${TIMESTAMP}.log"

echo "Monitor logs will be saved to: $LOG_FILE"
echo "Error logs will be saved to: $ERROR_LOG"

# Check if config.yaml exists
if [ ! -f "config/config.yaml" ]; then
    echo "❌ ERROR: config.yaml not found. Copy from config.example.yaml first."
    exit 1
fi

# Check if .env exists, create from template if needed
if [ ! -f ".env" ]; then
    echo "⚠️ .env file not found, creating from template..."
    cp config/env.template .env
    echo "⚠️ IMPORTANT: Edit .env file to add your API keys before running!"
    exit 1
fi

# Process environment variables from .env
if [ -f ".env" ]; then
    echo "🔑 Processing API keys from .env file..."
    
    # Extract and clean API keys
    BIRDEYE_API_KEY=$(grep -E "^BIRDEYE_API_KEY\s*=" .env | cut -d '=' -f2 | sed -E 's/^["'\''[:space:]]*//;s/["'\''[:space:]]*$//')
    TELEGRAM_BOT_TOKEN=$(grep -E "^TELEGRAM_BOT_TOKEN\s*=" .env | cut -d '=' -f2 | sed -E 's/^["'\''[:space:]]*//;s/["'\''[:space:]]*$//')
    TELEGRAM_CHAT_ID=$(grep -E "^TELEGRAM_CHAT_ID\s*=" .env | cut -d '=' -f2 | sed -E 's/^["'\''[:space:]]*//;s/["'\''[:space:]]*$//')
    HELIUS_API_KEY=$(grep -E "^HELIUS_API_KEY\s*=" .env | cut -d '=' -f2 | sed -E 's/^["'\''[:space:]]*//;s/["'\''[:space:]]*$//')
    
    # Export cleaned keys
    if [ ! -z "$BIRDEYE_API_KEY" ]; then
        BIRDEYE_API_KEY=$(echo "$BIRDEYE_API_KEY" | tr -d '"' | tr -d "'" | xargs)
        export BIRDEYE_API_KEY="$BIRDEYE_API_KEY"
        
        if [ ${#BIRDEYE_API_KEY} -gt 12 ]; then
            echo "✅ Loaded BirdEye API key: ${BIRDEYE_API_KEY:0:8}...${BIRDEYE_API_KEY: -4}"
        else
            echo "⚠️ BirdEye API key may be too short: ${#BIRDEYE_API_KEY} characters"
        fi
    else
        echo "⚠️ WARNING: BIRDEYE_API_KEY not found in .env file"
    fi
    
    if [ ! -z "$TELEGRAM_BOT_TOKEN" ] && [ ! -z "$TELEGRAM_CHAT_ID" ]; then
        TELEGRAM_BOT_TOKEN=$(echo "$TELEGRAM_BOT_TOKEN" | tr -d '"' | tr -d "'" | xargs)
        TELEGRAM_CHAT_ID=$(echo "$TELEGRAM_CHAT_ID" | tr -d '"' | tr -d "'" | xargs)
        
        export TELEGRAM_BOT_TOKEN="$TELEGRAM_BOT_TOKEN"
        export TELEGRAM_CHAT_ID="$TELEGRAM_CHAT_ID"
        echo "✅ Loaded Telegram credentials"
    fi
    
    if [ ! -z "$HELIUS_API_KEY" ]; then
        HELIUS_API_KEY=$(echo "$HELIUS_API_KEY" | tr -d '"' | tr -d "'" | xargs)
        export HELIUS_API_KEY="$HELIUS_API_KEY"
        echo "✅ Loaded Helius API key"
    fi
fi

# Run preflight check
echo "=========================================="
echo "    RUNNING PRE-FLIGHT CHECKS"
echo "=========================================="
python debug_preflight.py --run-preflight

# Check if preflight was successful
if [ $? -ne 0 ]; then
    echo "❌ Pre-flight check failed. Fix issues before running monitor."
    exit 1
fi

# Create a temporary config override file with 30-minute interval
echo "=========================================="
echo "    CONFIGURING 30-MINUTE INTERVAL"
echo "=========================================="

CONFIG_OVERRIDE="config/config.override.yaml"

cat > $CONFIG_OVERRIDE << EOL
# Temporary config override for twice-hourly monitoring
TOKEN_DISCOVERY:
  scan_interval_minutes: 30  # Run every 30 minutes (twice per hour)
  max_tokens: 50  # Increased token discovery for each run

TRADER_DISCOVERY:
  enabled: true
  discovery_interval_scans: 1  # Run trader discovery on every scan
  max_traders_per_discovery: 20

WHALE_TRACKING:
  enabled: true
  tracking_interval_scans: 1  # Track whale movements on every scan

ANALYSIS:
  enable_comprehensive: true  # Enable all analysis features
EOL

echo "Created temporary config override at $CONFIG_OVERRIDE"
echo "Set scan interval to 30 minutes (twice per hour)"

# Set environment variables
export USE_CONFIG_OVERRIDE=1
export CONFIG_OVERRIDE_PATH=$CONFIG_OVERRIDE
export PYTHONPATH="${PYTHONPATH:+${PYTHONPATH}:}$(pwd)"

echo "📚 PYTHONPATH set to: $PYTHONPATH"
echo "🔧 Config override enabled: $CONFIG_OVERRIDE_PATH"

echo "=========================================="
echo "    STARTING TWICE-HOURLY MONITOR"
echo "=========================================="

# Run with full error capture
(python monitor.py run --discovery-now 2>&1 | tee -a "$LOG_FILE") 3>&1 1>&2 2>&3 | tee "$ERROR_LOG"

# Capture exit code
EXIT_CODE=$?

echo "=========================================="
echo "    MONITOR PROCESS COMPLETE"
echo "=========================================="
echo "Exit code: $EXIT_CODE"

if [ $EXIT_CODE -eq 0 ]; then
    echo "✅ Monitor completed successfully"
else
    echo "⚠️ Monitor exited with error code $EXIT_CODE"
    echo "   Check $ERROR_LOG for details"
fi

# Clean up the temporary config override
rm -f $CONFIG_OVERRIDE
echo "Removed temporary config override"

echo "=========================================="
echo "    MONITOR SESSION SUMMARY"
echo "=========================================="
echo "📁 Log files:"
echo "   - $LOG_FILE"
echo "   - $ERROR_LOG" 