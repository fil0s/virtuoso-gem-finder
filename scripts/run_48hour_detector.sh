#!/bin/bash

# 48-Hour High Conviction Token Detector Runner
# Runs token detection for 48 hours with scans every 30 minutes (96 total cycles)

echo "🎯 Starting 48-Hour High Conviction Token Detector"
echo "=============================================="
echo "⏰ Duration: 48 hours"
echo "🔄 Interval: 30 minutes (2 scans per hour)"
echo "📊 Total cycles: 96"
echo "🚀 Starting at: $(date)"
echo "=============================================="

# Check if virtual environment exists
if [ -d "venv" ]; then
    echo "✅ Activating virtual environment..."
    source venv/bin/activate
elif [ -d "venv_new" ]; then
    echo "✅ Activating virtual environment (venv_new)..."
    source venv_new/bin/activate
else
    echo "⚠️ No virtual environment found. Running with system Python..."
fi

# Check if required packages are installed
echo "🔍 Checking dependencies..."
python -c "import prettytable; print('✅ prettytable installed')" 2>/dev/null || echo "⚠️ prettytable not installed - tables will be simplified"

# Create logs directory if it doesn't exist
mkdir -p logs

# Generate timestamp for log file
TIMESTAMP=$(date +"%Y%m%d_%H%M%S")
LOG_FILE="logs/48hour_detector_${TIMESTAMP}.log"

echo "📝 Logging to: $LOG_FILE"
echo ""

# Run the detector with both console output and logging
echo "🚀 Launching 48-hour detector..."
python run_48hour_30min_detector.py 2>&1 | tee "$LOG_FILE"

# Check exit code
EXIT_CODE=${PIPESTATUS[0]}

echo ""
echo "=============================================="
if [ $EXIT_CODE -eq 0 ]; then
    echo "✅ 48-hour detector completed successfully!"
    echo "📊 Results logged to: $LOG_FILE"
else
    echo "❌ 48-hour detector failed with exit code: $EXIT_CODE"
    echo "📝 Check log file for details: $LOG_FILE"
fi
echo "🏁 Ended at: $(date)"
echo "=============================================="

exit $EXIT_CODE 