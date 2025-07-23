#!/bin/bash

# Cross-Platform Token Analyzer Daemon
# Runs analysis every 15 minutes

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

echo "🚀 Starting Cross-Platform Token Analyzer Daemon..."
echo "Will run analysis every 15 minutes"
echo "Press Ctrl+C to stop"
echo "================================================"

# Function to run analysis
run_analysis() {
    echo ""
    echo "🔍 Running analysis at $(date)"
    echo "----------------------------------------"
    
    # Activate virtual environment if it exists
    if [ -d "venv" ]; then
        source venv/bin/activate
    fi
    
    # Run the analysis
    python scripts/cross_platform_token_analyzer.py
    
    if [ $? -eq 0 ]; then
        echo "✅ Analysis completed successfully at $(date)"
    else
        echo "❌ Analysis failed at $(date)"
    fi
    
    echo "⏰ Next analysis in 15 minutes..."
}

# Handle Ctrl+C gracefully
trap 'echo ""; echo "🛑 Daemon stopped by user"; exit 0' INT

# Run initial analysis
run_analysis

# Run analysis every 15 minutes (900 seconds)
while true; do
    sleep 900  # 15 minutes = 900 seconds
    run_analysis
done 