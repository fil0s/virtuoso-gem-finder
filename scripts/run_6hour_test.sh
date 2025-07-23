#!/bin/bash

# Quick 6-Hour Cross-Platform Test Launcher
# ==========================================

echo "🚀 Starting 6-Hour Cross-Platform Token Analyzer Test"
echo "======================================================"

# Navigate to project directory
cd /Users/ffv_macmini/Desktop/virtuoso_gem_hunter

# Activate virtual environment
source venv/bin/activate

# Start the test in background with logging
nohup python scripts/run_6hour_cross_platform_test.py > 6hour_test_$(date +%Y%m%d_%H%M%S).log 2>&1 &

# Get the process ID
PID=$!

echo "✅ Test started successfully!"
echo "📊 Process ID: $PID"
echo "📝 Log file: 6hour_test_$(date +%Y%m%d_%H%M%S).log"
echo ""
echo "🔍 Monitor progress with:"
echo "   cd /Users/ffv_macmini/Desktop/virtuoso_gem_hunter/scripts"
echo "   python monitor_6hour_test_progress.py"
echo ""
echo "🔄 Continuous monitoring:"
echo "   python monitor_6hour_test_progress.py --watch"
echo ""
echo "📋 Check latest results:"
echo "   python check_latest_results.py"
echo ""
echo "🛑 To stop the test:"
echo "   kill $PID"
echo ""
echo "🎯 Test will run for 6 hours and analyze tokens every 15 minutes" 