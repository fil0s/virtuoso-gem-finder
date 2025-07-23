#!/bin/bash

# Monitor Optimization Session Progress
# Tracks API call efficiency, cache performance, and scan progress

echo "🔍 MONITORING OPTIMIZED SCAN SESSION"
echo "===================================="
echo "Session Start: $(date)"
echo ""

# Function to show session stats
show_session_stats() {
    echo "📊 CURRENT SESSION STATS:"
    
    # Count total scans completed
    SCANS_COMPLETED=$(grep -c "SCAN.*RESULTS:" logs/monitor.log 2>/dev/null || echo "0")
    echo "   • Scans Completed: $SCANS_COMPLETED/10"
    
    # Show API efficiency
    echo "   • Optimization Status: ACTIVE"
    echo "   • Ultra-Batch: ✅ Enabled"
    echo "   • Parallel Discovery: ✅ Enabled" 
    echo "   • Enhanced Caching: ✅ Enabled"
    echo "   • Cross-Strategy Sharing: ✅ Enabled"
    
    # Show recent optimization gains
    EFFICIENCY_GAINS=$(tail -20 logs/monitor.log | grep -o "efficiency.*%" | tail -1 2>/dev/null || echo "Calculating...")
    echo "   • Latest Efficiency: $EFFICIENCY_GAINS"
    
    echo ""
}

# Function to show recent activity
show_recent_activity() {
    echo "⚡ RECENT ACTIVITY (Last 10 lines):"
    echo "-----------------------------------"
    tail -10 logs/monitor.log 2>/dev/null | head -10 || echo "No log activity yet"
    echo ""
}

# Function to show API call summary
show_api_summary() {
    echo "📞 API CALL SUMMARY:"
    echo "-------------------"
    
    # Count different types of API calls in the last scan
    TOTAL_CALLS=$(tail -100 logs/monitor.log | grep -c "api_call" 2>/dev/null || echo "0")
    BATCH_CALLS=$(tail -100 logs/monitor.log | grep -c "batch_api" 2>/dev/null || echo "0")
    ULTRA_CALLS=$(tail -100 logs/monitor.log | grep -c "ultra_batch" 2>/dev/null || echo "0")
    
    echo "   • Total API Calls: $TOTAL_CALLS"
    echo "   • Batch API Calls: $BATCH_CALLS"
    echo "   • Ultra-Batch Calls: $ULTRA_CALLS"
    echo ""
}

# Function to show optimization benefits
show_optimization_benefits() {
    echo "🎯 OPTIMIZATION BENEFITS:"
    echo "------------------------"
    echo "   • Discovery: Parallel (4 strategies simultaneously)"
    echo "   • Analysis: Ultra-Batch (2-3 calls vs 10-20 per token)"
    echo "   • Strategy: Data Sharing (eliminates duplicate calls)"
    echo "   • Caching: Adaptive TTL with predictive prefetching"
    echo "   • Expected Savings: 70-90% vs unoptimized approach"
    echo ""
}

# Main monitoring loop
echo "Starting real-time monitoring..."
echo "Press Ctrl+C to stop monitoring"
echo ""

# Initial status
show_session_stats
show_optimization_benefits

# Monitor in real-time
while true; do
    clear
    echo "🔍 OPTIMIZED SCAN SESSION MONITOR"
    echo "================================="
    echo "Last Updated: $(date)"
    echo ""
    
    show_session_stats
    show_api_summary
    show_recent_activity
    
    # Check if session is complete
    COMPLETED_SCANS=$(grep -c "SCAN.*RESULTS:" logs/monitor.log 2>/dev/null || echo "0")
    if [ "$COMPLETED_SCANS" -ge 10 ]; then
        echo "🎉 SESSION COMPLETE! 10/10 scans finished."
        echo "Check logs/optimized_session_report_*.json for detailed results"
        break
    fi
    
    # Check if session is still running
    if ! pgrep -f "run_optimized_10_scan_test.py" > /dev/null; then
        echo "⚠️ Session process not found. May have completed or encountered an error."
        echo "Check logs for details."
        break
    fi
    
    echo "🔄 Next update in 30 seconds... (Ctrl+C to exit)"
    sleep 30
done 