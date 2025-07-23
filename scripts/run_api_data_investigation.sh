#!/bin/bash

# API Data Limitations Investigation Runner
# This script investigates why smart trader identification is failing

echo "🔍 Starting API Data Limitations Investigation..."
echo "=================================================="
echo "📊 Analyzing the exact tokens from the recent failed threshold tuning run"
echo "🎯 Investigating BirdEye API responses and whale detection logic"
echo "💡 Generating data-driven threshold recommendations"
echo ""

# Activate virtual environment if it exists
if [ -d "venv" ]; then
    echo "🔧 Activating virtual environment..."
    source venv/bin/activate
fi

# Set environment variables
export PYTHONPATH="${PYTHONPATH}:$(pwd)"

# Run the investigation
echo "🚀 Running API data investigation..."
python scripts/investigate_api_data_limitations.py

echo ""
echo "✅ Investigation complete!"
echo "📝 Check the results file for detailed analysis and recommendations" 