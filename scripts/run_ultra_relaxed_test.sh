#!/bin/bash

echo "======================================================================"
echo "     ULTRA RELAXED TIMEFRAME TEST - MAXIMUM TOKEN FLOW MODE         "
echo "======================================================================"

# Load environment variables
if [ -f .env ]; then
    echo "Loading environment variables from .env file..."
    export $(cat .env | grep -v '^#' | xargs)
fi

# Activate virtual environment
echo "Activating virtual environment..."
source venv/bin/activate

echo "Starting ULTRA RELAXED timeframe test..."
echo "⚠️ ULTRA RELAXED FILTERS: Maximum token flow enabled"
echo "⚠️ Enhanced timeframe selection enabled"
echo "⚠️ Bypassing ALL strict filtering"

# Create timestamp for log file
TIMESTAMP=$(date +"%Y%m%d_%H%M%S")
LOG_FILE="logs/monitoring_runs/ultra_relaxed_test_${TIMESTAMP}.log"
echo "Logging to: $LOG_FILE"

# Set ultra-relaxed environment variables
export FORCE_RELAXED_FILTERS=true
export MIN_LIQUIDITY_OVERRIDE=1          # $1 minimum
export MIN_MARKET_CAP_OVERRIDE=1         # $1 minimum  
export MIN_VOLUME_24H_OVERRIDE=1         # $1 minimum
export MIN_MOMENTUM_SCORE_OVERRIDE=1     # Score of 1
export FORCE_ANALYSIS_MODE=true
export BYPASS_TIME_SCHEDULING=true
export ULTRA_RELAXED_SCORING=true        # New flag for ultra-low scoring
export MIN_QUICK_SCORE_OVERRIDE=5        # Score threshold of 5 instead of 40

echo ""
echo "🔧 ULTRA RELAXED SETTINGS:"
echo "   • Minimum Liquidity: $1"
echo "   • Minimum Market Cap: $1" 
echo "   • Minimum Volume: $1"
echo "   • Minimum Score: 5 (vs normal 40)"
echo "   • Force Analysis: Enabled"
echo "   • Time Bypass: Enabled"
echo ""

# Run the monitor with ultra-relaxed settings
python monitor.py debug \
    --runtime-hours 0.25 \
    --enhanced-timeframes true \
    2>&1 | tee "$LOG_FILE"

echo ""
echo "======================================================================"
echo "Ultra relaxed timeframe test completed!"
echo "Log file: $LOG_FILE"
echo "======================================================================" 