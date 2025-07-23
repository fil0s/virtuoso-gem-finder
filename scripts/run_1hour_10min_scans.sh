#!/bin/bash

# 1-Hour Token Scanner (10-minute intervals)
# Runs continuous token discovery every 10 minutes for 1 hour total
# Approximately 6 scan cycles with RugCheck security filtering

echo "🛡️ 1-HOUR TOKEN SCANNER (10-MINUTE INTERVALS)"
echo "=============================================="

# Check if virtual environment exists
if [ ! -d "venv" ]; then
    echo "❌ Virtual environment not found. Please run setup_environment.sh first."
    exit 1
fi

# Activate virtual environment
echo "🔧 Activating virtual environment..."
source venv/bin/activate

# Check if environment file exists
if [ ! -f ".env" ]; then
    echo "❌ .env file not found. Please create it with your API keys."
    echo "   You can copy from config/env.template"
    exit 1
fi

# Check for required API key
if ! grep -q "BIRDEYE_API_KEY=" .env || grep -q "BIRDEYE_API_KEY=$" .env; then
    echo "❌ BIRDEYE_API_KEY not found or empty in .env file"
    echo "   Please add your Birdeye API key to the .env file"
    exit 1
fi

# Create necessary directories
mkdir -p logs data debug

echo "✅ Environment checks passed"
echo ""

# Display session configuration
echo "📊 SESSION CONFIGURATION"
echo "========================"
echo "   • Total Runtime: 1 hour"
echo "   • Scan Interval: 10 minutes"
echo "   • Expected Scans: ~6 cycles"
echo "   • Security Filtering: RugCheck API enabled"
echo "   • Token Discovery: All strategies active"
echo "   • Enhanced Timeframes: Enabled"
echo ""

# Set environment variables for 10-minute scanning
export SCAN_INTERVAL_MINUTES=10
export ENHANCED_TIMEFRAMES=true

# Display security features
echo "🛡️ SECURITY FEATURES ACTIVE"
echo "============================"
echo "   • RugCheck API integration for token security analysis"
echo "   • Automatic filtering of honeypots and rug pulls"
echo "   • Risk level classification (SAFE/LOW/MEDIUM/HIGH/CRITICAL)"
echo "   • Deal-breaker detection (blacklist functions, proxy contracts)"
echo "   • Conservative approach: Unknown risk = Filtered out"
echo ""

# Display timeline
current_time=$(date +"%H:%M:%S")
end_time=$(date -d "+1 hour" +"%H:%M:%S")

echo "⏰ SCANNING TIMELINE"
echo "==================="
echo "   • Start Time: $current_time"
echo "   • End Time: $end_time"
echo "   • Duration: 1 hour"
echo "   • Scan #1: $current_time (starting now)"
echo "   • Scan #2: $(date -d "+10 minutes" +"%H:%M:%S")"
echo "   • Scan #3: $(date -d "+20 minutes" +"%H:%M:%S")"
echo "   • Scan #4: $(date -d "+30 minutes" +"%H:%M:%S")"
echo "   • Scan #5: $(date -d "+40 minutes" +"%H:%M:%S")"
echo "   • Scan #6: $(date -d "+50 minutes" +"%H:%M:%S")"
echo ""

echo "🚀 STARTING 1-HOUR SCANNING SESSION"
echo "==================================="
echo "This will run token discovery every 10 minutes for 1 hour with:"
echo "   ✅ RugCheck security filtering"
echo "   ✅ Enhanced timeframe analysis"
echo "   ✅ Structured logging"
echo "   ✅ Telegram alerts (if configured)"
echo "   ✅ Automatic stop after 1 hour"
echo ""

# Function to handle cleanup on exit
cleanup() {
    echo ""
    echo "🛑 Scanning session ended"
    echo "📊 Session complete - check logs/ directory for detailed results"
    exit 0
}

# Set up signal handlers
trap cleanup SIGINT SIGTERM

# Start the monitor with 1-hour runtime and 10-minute intervals
echo "⏰ Starting 1-hour session with 10-minute scan intervals..."
echo "🛡️ All tokens will be security-filtered through RugCheck API"
echo "📊 Results will be logged to logs/ directory"
echo "🛑 Session will automatically stop after 1 hour"
echo ""

# Run the monitor with 1-hour runtime limit
python monitor.py run --runtime-hours 1 --enhanced-timeframes true

# Check exit code
if [ $? -eq 0 ]; then
    echo ""
    echo "✅ 1-hour scanning session completed successfully"
    echo ""
    echo "📊 SESSION SUMMARY"
    echo "=================="
    echo "   • Duration: 1 hour"
    echo "   • Scan interval: 10 minutes"
    echo "   • Expected scans: ~6 cycles"
    echo "   • Security filtering: RugCheck enabled"
    echo "   • Logs location: logs/ directory"
    echo "   • Data location: data/ directory"
else
    echo ""
    echo "❌ Session exited with error code $?"
    echo "📋 Check logs for error details"
fi

echo ""
echo "🔗 RugCheck API: https://api.rugcheck.xyz/swagger/index.html"
echo "📋 For detailed analysis, check the structured logs in logs/ directory" 