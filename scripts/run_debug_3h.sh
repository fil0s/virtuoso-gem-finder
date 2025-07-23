#!/bin/bash
# Enhanced debug session script for virtuoso_gem_hunter
# Captures all analysis, API calls, errors, and issues

echo "=========================================="
echo "    VIRTUOSO GEM HUNTER DEBUG SESSION"
echo "=========================================="

echo "🔍 Setting up enhanced debug environment..."

# Create debug directory structure
mkdir -p logs
mkdir -p debug/api_responses debug/whale_data debug/trader_data debug/token_analysis

# Set timestamp for this debug session
TIMESTAMP=$(date +"%Y%m%d_%H%M%S")
DEBUG_LOG="logs/debug_session_${TIMESTAMP}.log"
ERROR_LOG="logs/error_session_${TIMESTAMP}.log"
API_LOG="logs/api_calls_${TIMESTAMP}.log"
TRACE_LOG="logs/trace_session_${TIMESTAMP}.log"
PERF_LOG="logs/performance_${TIMESTAMP}.log"
MEMORY_LOG="logs/memory_${TIMESTAMP}.log"
CPU_LOG="logs/cpu_${TIMESTAMP}.log"
LATENCY_LOG="logs/latency_${TIMESTAMP}.log"

echo "Debug logs will be saved to: $DEBUG_LOG"
echo "Error logs will be saved to: $ERROR_LOG"
echo "API call logs will be saved to: $API_LOG"
echo "Trace logs will be saved to: $TRACE_LOG"
echo "Performance logs will be saved to: $PERF_LOG"
echo "Memory usage logs will be saved to: $MEMORY_LOG"
echo "CPU usage logs will be saved to: $CPU_LOG"
echo "Latency logs will be saved to: $LATENCY_LOG"

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

# Process environment variables from .env to ensure no quotes
# We'll extract, clean, and re-export them to ensure they are properly formatted
if [ -f ".env" ]; then
    echo "🔑 Processing API keys from .env file..."
    
    # Extract and clean API keys with enhanced quote/whitespace removal
    # This uses a more thorough regex to handle different types of quotes and whitespace
    BIRDEYE_API_KEY=$(grep -E "^BIRDEYE_API_KEY\s*=" .env | cut -d '=' -f2 | sed -E 's/^["'\''[:space:]]*//;s/["'\''[:space:]]*$//')
    TELEGRAM_BOT_TOKEN=$(grep -E "^TELEGRAM_BOT_TOKEN\s*=" .env | cut -d '=' -f2 | sed -E 's/^["'\''[:space:]]*//;s/["'\''[:space:]]*$//')
    TELEGRAM_CHAT_ID=$(grep -E "^TELEGRAM_CHAT_ID\s*=" .env | cut -d '=' -f2 | sed -E 's/^["'\''[:space:]]*//;s/["'\''[:space:]]*$//')
    HELIUS_API_KEY=$(grep -E "^HELIUS_API_KEY\s*=" .env | cut -d '=' -f2 | sed -E 's/^["'\''[:space:]]*//;s/["'\''[:space:]]*$//')
    
    # Export cleaned keys and validate
    if [ ! -z "$BIRDEYE_API_KEY" ]; then
        # Further validation to ensure no quotes remain
        BIRDEYE_API_KEY=$(echo "$BIRDEYE_API_KEY" | tr -d '"' | tr -d "'" | xargs)
        export BIRDEYE_API_KEY="$BIRDEYE_API_KEY"
        
        # Log the key format (first 8 chars and last 4 chars only for security)
        if [ ${#BIRDEYE_API_KEY} -gt 12 ]; then
            echo "✅ Loaded BirdEye API key: ${BIRDEYE_API_KEY:0:8}...${BIRDEYE_API_KEY: -4}"
        else
            echo "⚠️ BirdEye API key may be too short: ${#BIRDEYE_API_KEY} characters"
        fi
        
        # Debug: Write the first character as hex to check for invisible characters
        FIRST_CHAR_HEX=$(echo -n "${BIRDEYE_API_KEY:0:1}" | hexdump -v -e '/1 "%02X"')
        echo "🔍 API key first character hex: $FIRST_CHAR_HEX" >> "$DEBUG_LOG"
        echo "🔍 API key format validation: No surrounding quotes" >> "$DEBUG_LOG"
    else
        echo "⚠️ WARNING: BIRDEYE_API_KEY not found in .env file"
    fi
    
    if [ ! -z "$TELEGRAM_BOT_TOKEN" ] && [ ! -z "$TELEGRAM_CHAT_ID" ]; then
        # Further validation to ensure no quotes remain
        TELEGRAM_BOT_TOKEN=$(echo "$TELEGRAM_BOT_TOKEN" | tr -d '"' | tr -d "'" | xargs)
        TELEGRAM_CHAT_ID=$(echo "$TELEGRAM_CHAT_ID" | tr -d '"' | tr -d "'" | xargs)
        
        export TELEGRAM_BOT_TOKEN="$TELEGRAM_BOT_TOKEN"
        export TELEGRAM_CHAT_ID="$TELEGRAM_CHAT_ID"
        echo "✅ Loaded Telegram credentials"
    fi
    
    if [ ! -z "$HELIUS_API_KEY" ]; then
        # Further validation to ensure no quotes remain
        HELIUS_API_KEY=$(echo "$HELIUS_API_KEY" | tr -d '"' | tr -d "'" | xargs)
        export HELIUS_API_KEY="$HELIUS_API_KEY"
        echo "✅ Loaded Helius API key"
    fi
    
    # Verify API key formatting for debugging
    echo "DEBUG: Verifying API key formats:" >> "$DEBUG_LOG"
    echo "BIRDEYE_API_KEY length: ${#BIRDEYE_API_KEY}" >> "$DEBUG_LOG"
    echo "BIRDEYE_API_KEY first/last chars: '${BIRDEYE_API_KEY:0:1}' and '${BIRDEYE_API_KEY: -1}'" >> "$DEBUG_LOG"
    
    # Direct check for quotes in the API key
    if [[ "$BIRDEYE_API_KEY" == *'"'* ]] || [[ "$BIRDEYE_API_KEY" == *"'"* ]]; then
        echo "⚠️ WARNING: Quotes detected in BIRDEYE_API_KEY after cleaning!" >> "$DEBUG_LOG"
    else
        echo "✅ BIRDEYE_API_KEY format looks good (no quotes detected)" >> "$DEBUG_LOG"
    fi
fi

# Run preflight check first
echo "=========================================="
echo "    RUNNING PRE-FLIGHT CHECKS"
echo "=========================================="
python debug_preflight.py --run-preflight

# Check if preflight was successful
if [ $? -ne 0 ]; then
    echo "❌ Pre-flight check failed. Fix issues before running debug session."
    exit 1
fi

echo "=========================================="
echo "    STARTING 3-HOUR DEBUG SESSION"
echo "=========================================="

# Set enhanced debug environment variables
export DEBUG_MODE=1
export LOG_API_CALLS=1
export VERBOSE_LOGGING=1
export DEBUG_SESSION_ID="${TIMESTAMP}"
export SAVE_DEBUG_DATA=1
export ENHANCED_LOGGING=1
export CAPTURE_API_RESPONSES=1
export TRACE_ANALYSIS_PIPELINE=1
export DEBUG_TIMEOUT_EXTENSION=1
export MEASURE_PERFORMANCE=1
export MEMORY_PROFILING=1
export TRACK_LATENCIES=1
export TRACK_CACHE_EVENTS=1
export MEASURE_PIPELINE_STAGES=1
export TRACK_BATCH_EFFICIENCY=1
export CAPTURE_CPU_USAGE=1

# Add current directory to PYTHONPATH for module resolution
export PYTHONPATH="${PYTHONPATH:+${PYTHONPATH}:}$(pwd)"
echo "📚 PYTHONPATH set to: $PYTHONPATH"

# Record environment information
echo "Environment Information:" > "$TRACE_LOG"
echo "- Operating System: $(uname -a)" >> "$TRACE_LOG"
echo "- Python Version: $(python --version 2>&1)" >> "$TRACE_LOG"
echo "- Debug Session ID: ${TIMESTAMP}" >> "$TRACE_LOG"
echo "- Start Time: $(date)" >> "$TRACE_LOG"
echo "- Command: python monitor.py debug --discovery-now --runtime-hours 3 --dashboard" >> "$TRACE_LOG"
echo "- PYTHONPATH: ${PYTHONPATH}" >> "$TRACE_LOG"
echo "- API Keys: BirdEye API Key is $(if [ ! -z "$BIRDEYE_API_KEY" ]; then echo "Set (${#BIRDEYE_API_KEY} chars)"; else echo "Not Set"; fi)" >> "$TRACE_LOG"
echo "-------------------------------------------" >> "$TRACE_LOG"

# Start background process to periodically capture memory and CPU usage
echo "Starting performance monitoring..."
(
  while true; do
    # Get memory usage of Python processes
    MEM_USAGE=$(ps -o rss -p $(pgrep -f "python.*monitor.py") | tail -n +2 | awk '{sum+=$1} END {print sum/1024}')
    echo "$(date +"%Y-%m-%d %H:%M:%S") Memory usage: ${MEM_USAGE:-0} MB" >> "$MEMORY_LOG"
    
    # Get CPU usage of Python processes
    CPU_USAGE=$(ps -o %cpu -p $(pgrep -f "python.*monitor.py") | tail -n +2 | awk '{sum+=$1} END {print sum}')
    echo "$(date +"%Y-%m-%d %H:%M:%S") CPU utilization: ${CPU_USAGE:-0}%" >> "$CPU_LOG"
    
    # Record to trace log for summary generation
    echo "$(date +"%Y-%m-%d %H:%M:%S") Memory usage: ${MEM_USAGE:-0} MB" >> "$DEBUG_LOG"
    echo "$(date +"%Y-%m-%d %H:%M:%S") CPU utilization: ${CPU_USAGE:-0}%" >> "$DEBUG_LOG"
    
    sleep 10  # Check every 10 seconds
  done
) &
MONITOR_PID=$!

# Final API key check before running
echo "=========================================="
echo "    FINAL API KEY VERIFICATION"
echo "=========================================="
# Display the first few and last few characters of the API key
if [ ! -z "$BIRDEYE_API_KEY" ]; then
    KEY_LENGTH=${#BIRDEYE_API_KEY}
    echo "BirdEye API Key: ${BIRDEYE_API_KEY:0:4}...${BIRDEYE_API_KEY: -4} (${KEY_LENGTH} characters)"
    # Make sure there are no quotes or unexpected characters
    if [[ "$BIRDEYE_API_KEY" == *'"'* ]] || [[ "$BIRDEYE_API_KEY" == *"'"* ]]; then
        echo "⚠️ WARNING: API key contains quotes! This may cause issues."
    else
        echo "✅ API key format looks good (no quotes detected)"
    fi
else
    echo "⚠️ WARNING: BIRDEYE_API_KEY is not set!"
fi
echo "=========================================="

# Run with full error capture and real-time analysis
(python monitor.py debug --discovery-now --runtime-hours 3 --dashboard 2>&1 | tee -a "$DEBUG_LOG") 3>&1 1>&2 2>&3 | tee "$ERROR_LOG"

# Capture exit code
EXIT_CODE=$?

# Kill the background monitoring process
kill $MONITOR_PID 2>/dev/null

# Extract API calls from the logs
grep -E "API call|Request to|Response from" "$DEBUG_LOG" > "$API_LOG"

# Extract performance metrics
grep -E "API calls|reduction|efficiency|duration|Memory usage|CPU utilization|Request latency|Token analysis time|Pipeline filtering|Batch efficiency|Rate limit|Cache" "$DEBUG_LOG" > "$PERF_LOG"

# Extract latency information
grep -E "Request latency|response time|API call took" "$DEBUG_LOG" > "$LATENCY_LOG"

# Generate debug session summary
echo "=========================================="
echo "    GENERATING DEBUG SUMMARY"
echo "=========================================="
python debug_preflight.py --session-id "${TIMESTAMP}" --generate-summary

echo "=========================================="
echo "    3-HOUR DEBUG SESSION COMPLETE"
echo "=========================================="
echo "Exit code: $EXIT_CODE"

if [ $EXIT_CODE -eq 0 ]; then
    echo "✅ Monitor completed successfully"
else
    echo "⚠️ Monitor exited with error code $EXIT_CODE"
    echo "   Check $ERROR_LOG for details"
fi

echo "=========================================="
echo "    COLLECTED DEBUG DATA"
echo "=========================================="
echo "📁 Log files:"
echo "   - $DEBUG_LOG"
echo "   - $ERROR_LOG"
echo "   - $API_LOG"
echo "   - $TRACE_LOG"
echo "   - $PERF_LOG"
echo "   - $MEMORY_LOG"
echo "   - $CPU_LOG"
echo "   - $LATENCY_LOG"
echo ""
echo "📊 Summary report: debug_session_summary.md"
echo "=========================================="
echo "🔬 DEBUG SESSION ANALYSIS COMPLETE"
echo "==========================================" 