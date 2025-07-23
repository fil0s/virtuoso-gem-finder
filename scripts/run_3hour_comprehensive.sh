#!/bin/bash

# 3-Hour Comprehensive Monitoring Run
# This script runs the virtuoso gem hunter for exactly 3 hours with comprehensive tracking

echo "🚀 STARTING 3-HOUR COMPREHENSIVE MONITORING RUN"
echo "=================================================="
echo "Start time: $(date)"
echo "Expected end time: $(date -v+3H)"
echo "Log file: logs/monitoring_runs/comprehensive_3h_$(date +%Y%m%d_%H%M%S).log"
echo "=================================================="

# Set ultra-relaxed environment variables for maximum API activity
export FORCE_RELAXED_FILTERS=true
export MIN_LIQUIDITY_OVERRIDE=1000
export MIN_MARKET_CAP_OVERRIDE=5000
export MIN_QUICK_SCORE_OVERRIDE=15
export FORCE_ANALYSIS_MODE=true
export BYPASS_TIME_SCHEDULING=false

# Set 3-hour runtime (180 minutes)
export MAX_RUNTIME_HOURS=3.0

# Enhanced logging for API tracking
export LOG_LEVEL=INFO

echo "🔧 Environment Configuration:"
echo "   FORCE_RELAXED_FILTERS: $FORCE_RELAXED_FILTERS"
echo "   MIN_LIQUIDITY_OVERRIDE: $MIN_LIQUIDITY_OVERRIDE"
echo "   MIN_MARKET_CAP_OVERRIDE: $MIN_MARKET_CAP_OVERRIDE"
echo "   MIN_QUICK_SCORE_OVERRIDE: $MIN_QUICK_SCORE_OVERRIDE"
echo "   MAX_RUNTIME_HOURS: $MAX_RUNTIME_HOURS"
echo "=================================================="

# Start the monitor
python monitor.py run --runtime-hours 3.0

echo "=================================================="
echo "🏁 3-HOUR COMPREHENSIVE RUN COMPLETED"
echo "End time: $(date)"
echo "=================================================="

# Generate comprehensive analysis report
echo "📊 Generating comprehensive analysis report..."
python scripts/analysis/comprehensive_status.py

echo "✅ 3-hour comprehensive monitoring run complete!" 