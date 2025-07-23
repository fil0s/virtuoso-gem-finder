#!/bin/bash

# VLR Enhanced DEX Demo Runner
echo "🚀 Starting VLR Enhanced DEX Demo..."

# Activate virtual environment if it exists
if [ -d "venv" ]; then
    echo "📦 Activating virtual environment..."
    source venv/bin/activate
fi

# Set PYTHONPATH to include current directory
export PYTHONPATH="${PYTHONPATH}:$(pwd)"

# Create logs directory if it doesn't exist
mkdir -p logs

echo "🧠 Running VLR Enhanced Demo with integrated intelligence..."
echo "   • High Conviction Token Detector (with VLR scoring)"
echo "   • Cross-Platform Token Analyzer (with VLR optimization)"
echo "   • VLR Optimal Scanner (standalone gem hunting)"
echo ""

# Run the VLR enhanced demo
python3 scripts/run_vlr_enhanced_demo.py

# Check exit code
if [ $? -eq 0 ]; then
    echo ""
    echo "✅ VLR Enhanced Demo completed successfully!"
    echo "🎯 All VLR intelligence systems tested and integrated"
else
    echo ""
    echo "❌ VLR Enhanced Demo encountered errors"
    exit 1
fi

echo ""
echo "📊 Demo complete. Check the results in:"
echo "   • scripts/results/ - JSON results"
echo "   • logs/ - Detailed logs"
echo ""
echo "🧠 VLR Intelligence is now fully integrated across all token discovery systems!" 