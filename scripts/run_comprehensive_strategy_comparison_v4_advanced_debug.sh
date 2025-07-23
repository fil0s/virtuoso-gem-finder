#!/bin/bash

echo "🔬 Advanced Debug Mode - Comprehensive Strategy Comparison V4"
echo "=============================================================="
echo ""

# Ensure we're in the right directory
cd "$(dirname "$0")"

# Load environment variables from .env file if it exists
if [[ -f ".env" ]]; then
    echo "📄 Loading environment variables from .env file..."
    export $(grep -v '^#' .env | xargs)
    echo "✅ Environment variables loaded"
else
    echo "⚠️  Warning: .env file not found"
fi

# Advanced debug environment variables
export PYTHONPATH="${PYTHONPATH}:$(pwd)"
export DEBUG_MODE=true
export LOG_LEVEL=DEBUG
export VERBOSE_LOGGING=true
export INTERACTIVE_DEBUG=true
export PYTHONWARNINGS=default
export PYTHONFAULTHANDLER=1
export PYTHONASYNCIODEBUG=1
export PYTHONMALLOC=debug

echo "🔬 Advanced debug environment variables set:"
echo "   DEBUG_MODE=true"
echo "   LOG_LEVEL=DEBUG" 
echo "   VERBOSE_LOGGING=true"
echo "   INTERACTIVE_DEBUG=true (pause points enabled)"
echo "   PYTHONFAULTHANDLER=1 (crash debugging)"
echo "   PYTHONASYNCIODEBUG=1 (async debugging)"
echo "   PYTHONMALLOC=debug (memory debugging)"
echo ""

# Check if virtual environment is activated
if [[ "$VIRTUAL_ENV" == "" ]]; then
    echo "⚠️  Warning: Virtual environment not detected. Activating..."
    source venv/bin/activate
fi

# Install psutil if not available (required for advanced debugging)
echo "🔧 Checking debug dependencies..."
python -c "import psutil" 2>/dev/null || {
    echo "📦 Installing psutil for advanced memory profiling..."
    pip install psutil
}

# Check for required environment variables
if [[ -z "$BIRDEYE_API_KEY" ]]; then
    echo "❌ Error: BIRDEYE_API_KEY environment variable not set"
    echo "   Please check your .env file or set manually: export BIRDEYE_API_KEY='your_key_here'"
    exit 1
fi

echo "✅ Environment checks passed"
echo ""

# Create debug session directory
DEBUG_SESSION_DIR="debug/session_$(date +%Y%m%d_%H%M%S)"
mkdir -p "$DEBUG_SESSION_DIR"
echo "📁 Debug session directory: $DEBUG_SESSION_DIR"

# Advanced debugging options menu
echo "🎛️  Advanced Debug Options:"
echo "   [1] Full trace mode (very verbose)"
echo "   [2] Memory profiling mode"
echo "   [3] API tracing mode"
echo "   [4] Interactive debugging mode"
echo "   [5] Performance benchmarking mode"
echo "   [6] All debug features (maximum verbosity)"
echo ""

read -p "Select debug mode (1-6) or press Enter for default: " debug_choice

case $debug_choice in
    1)
        echo "🔍 Full Trace Mode Selected"
        export PYTHON_TRACE=1
        PYTHON_FLAGS="-X dev -X tracemalloc=1"
        ;;
    2)
        echo "💾 Memory Profiling Mode Selected"
        export MEMORY_PROFILING=true
        PYTHON_FLAGS="-X tracemalloc=3"
        ;;
    3)
        echo "📡 API Tracing Mode Selected"
        export API_TRACE_MODE=true
        PYTHON_FLAGS="-X dev"
        ;;
    4)
        echo "⏸️ Interactive Debugging Mode Selected"
        export INTERACTIVE_DEBUG=true
        export PAUSE_ON_STRATEGY=true
        PYTHON_FLAGS="-X dev"
        ;;
    5)
        echo "⚡ Performance Benchmarking Mode Selected"
        export PERFORMANCE_BENCHMARK=true
        PYTHON_FLAGS="-X dev -X tracemalloc=2"
        ;;
    6)
        echo "🚀 Maximum Debug Mode Selected (ALL FEATURES)"
        export PYTHON_TRACE=1
        export MEMORY_PROFILING=true
        export API_TRACE_MODE=true
        export PERFORMANCE_BENCHMARK=true
        export PAUSE_ON_STRATEGY=true
        PYTHON_FLAGS="-X dev -X tracemalloc=3 -X importtime"
        ;;
    *)
        echo "📊 Default Debug Mode Selected"
        PYTHON_FLAGS="-u -W all"
        ;;
esac

echo ""
echo "🔍 Starting comprehensive strategy analysis in ADVANCED DEBUG MODE..."
echo "📝 Debug session will be saved to: $DEBUG_SESSION_DIR"
echo "⏱️  This may take longer due to extensive debugging overhead"
echo ""

# Ask for confirmation in advanced modes
if [[ "$debug_choice" == "6" ]] || [[ "$debug_choice" == "1" ]]; then
    read -p "⚠️  Warning: Maximum debug mode generates extensive logs. Continue? (y/N): " confirm
    if [[ "$confirm" != "y" ]] && [[ "$confirm" != "Y" ]]; then
        echo "❌ Debug session cancelled"
        exit 0
    fi
fi

# Record session start
echo "Debug session started at $(date)" > "$DEBUG_SESSION_DIR/session_info.txt"
echo "Debug mode: $debug_choice" >> "$DEBUG_SESSION_DIR/session_info.txt"
echo "Python flags: $PYTHON_FLAGS" >> "$DEBUG_SESSION_DIR/session_info.txt"

# Run with advanced debug flags and capture output
echo "🚀 Launching strategy comparison..."
echo ""

# Redirect stderr to capture debug output
python $PYTHON_FLAGS scripts/comprehensive_strategy_comparison_v4.py 2>&1 | tee "$DEBUG_SESSION_DIR/debug_output.log"

# Save environment info
echo "" >> "$DEBUG_SESSION_DIR/session_info.txt"
echo "=== Environment Info ===" >> "$DEBUG_SESSION_DIR/session_info.txt"
python --version >> "$DEBUG_SESSION_DIR/session_info.txt"
pip list >> "$DEBUG_SESSION_DIR/session_info.txt"

echo ""
echo "📊 Advanced debug analysis complete!"
echo "📁 All debug files saved to: $DEBUG_SESSION_DIR"
echo "🔍 Check the following files for detailed analysis:"
echo "   • debug_output.log - Complete execution log"
echo "   • session_info.txt - Session configuration"
echo "   • debug/session_*/debug_session.json - Detailed debug data"
echo "   • debug/session_*/performance_summary.json - Performance analysis"
echo "   • debug/session_*/api_call_analysis.json - API call patterns"
echo ""
echo "🔧 Use these debug files to optimize strategy performance and troubleshoot issues!" 