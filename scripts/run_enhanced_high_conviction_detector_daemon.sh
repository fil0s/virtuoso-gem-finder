#!/bin/bash

# Enhanced High Conviction Token Detector Daemon with Emerging Token Discovery
# This script runs the enhanced detector with Jupiter/Meteora integration as a background daemon

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PIDFILE="$SCRIPT_DIR/enhanced_high_conviction_detector_daemon.pid"
LOGFILE="$SCRIPT_DIR/logs/enhanced_high_conviction_detector_daemon.log"

# Function to check if daemon is running
is_running() {
    if [ -f "$PIDFILE" ]; then
        local pid=$(cat "$PIDFILE")
        if ps -p "$pid" > /dev/null 2>&1; then
            return 0
        else
            rm -f "$PIDFILE"
            return 1
        fi
    fi
    return 1
}

# Function to start the enhanced daemon
start_daemon() {
    if is_running; then
        echo "❌ Enhanced high conviction detector daemon is already running (PID: $(cat $PIDFILE))"
        return 1
    fi

    echo "🚀 Starting enhanced high conviction token detector daemon with emerging discovery..."
    
    # Create logs directory
    mkdir -p "$SCRIPT_DIR/logs"
    
    # Check if configuration exists
    if [ ! -f "$SCRIPT_DIR/config/config.yaml" ]; then
        echo "❌ Configuration file not found: $SCRIPT_DIR/config/config.yaml"
        echo "   Please copy config.example.yaml to config.yaml and configure it"
        return 1
    fi
    
    # Check if environment variables are set
    if [ -z "$BIRDEYE_API_KEY" ]; then
        echo "⚠️  Warning: BIRDEYE_API_KEY not set"
    fi
    
    if [ -z "$TELEGRAM_BOT_TOKEN" ] || [ -z "$TELEGRAM_CHAT_ID" ]; then
        echo "⚠️  Warning: Telegram credentials not set (TELEGRAM_BOT_TOKEN, TELEGRAM_CHAT_ID)"
    fi
    
    # Start the enhanced detector in background
    cd "$SCRIPT_DIR"
    nohup bash -c "
        source venv/bin/activate
        export PYTHONPATH=$SCRIPT_DIR:\$PYTHONPATH
        python scripts/high_conviction_token_detector.py --interval 15 --emerging-enabled
    " > "$LOGFILE" 2>&1 &
    
    local pid=$!
    echo $pid > "$PIDFILE"
    
    # Wait a moment to check if it started successfully
    sleep 5
    if is_running; then
        echo "✅ Enhanced high conviction detector daemon started successfully (PID: $pid)"
        echo "🌟 Features enabled: Cross-platform analysis + Jupiter/Meteora emerging discovery"
        echo "📋 Logs: $LOGFILE"
        echo "🛑 Stop with: $0 stop"
        echo "📊 Status with: $0 status"
        return 0
    else
        echo "❌ Failed to start enhanced high conviction detector daemon"
        rm -f "$PIDFILE"
        echo "📋 Check logs for errors: $LOGFILE"
        return 1
    fi
}

# Function to stop the daemon
stop_daemon() {
    if ! is_running; then
        echo "❌ Enhanced high conviction detector daemon is not running"
        return 1
    fi

    local pid=$(cat "$PIDFILE")
    echo "🛑 Stopping enhanced high conviction detector daemon (PID: $pid)..."
    
    # Try graceful shutdown first
    kill -TERM "$pid" 2>/dev/null
    
    # Wait up to 15 seconds for graceful shutdown
    local count=0
    while [ $count -lt 15 ] && ps -p "$pid" > /dev/null 2>&1; do
        sleep 1
        count=$((count + 1))
    done
    
    # Force kill if still running
    if ps -p "$pid" > /dev/null 2>&1; then
        echo "⚠️ Graceful shutdown failed, forcing termination..."
        kill -KILL "$pid" 2>/dev/null
        sleep 2
    fi
    
    rm -f "$PIDFILE"
    echo "✅ Enhanced high conviction detector daemon stopped"
}

# Function to restart the daemon
restart_daemon() {
    echo "🔄 Restarting enhanced high conviction detector daemon..."
    stop_daemon
    sleep 3
    start_daemon
}

# Function to show enhanced daemon status
status_daemon() {
    if is_running; then
        local pid=$(cat "$PIDFILE")
        echo "✅ Enhanced high conviction detector daemon is running (PID: $pid)"
        echo "🌟 Features: Cross-platform + Jupiter/Meteora emerging discovery"
        
        # Show process info
        echo "📊 Process Info:"
        ps -p "$pid" -o pid,ppid,cmd,etime,pcpu,pmem 2>/dev/null || echo "   Unable to get process info"
        
        # Show recent log entries with token discovery indicators
        if [ -f "$LOGFILE" ]; then
            echo ""
            echo "📋 Recent Log Entries (last 20 lines):"
            tail -n 20 "$LOGFILE" | grep -E "(Jupiter|Meteora|detected|✅|❌|🎯|🌟)" || tail -n 20 "$LOGFILE"
        fi
        
        return 0
    else
        echo "❌ Enhanced high conviction detector daemon is not running"
        return 1
    fi
}

# Function to show logs with emerging token filtering
show_logs() {
    if [ -f "$LOGFILE" ]; then
        echo "📋 Enhanced High Conviction Detector Daemon Logs:"
        echo "=============================================="
        if [ "$1" = "follow" ] || [ "$1" = "-f" ]; then
            tail -f "$LOGFILE"
        elif [ "$1" = "api" ] || [ "$1" = "-a" ]; then
            echo "🌟 Filtering for API activity:"
            grep -E "(Jupiter|Meteora|API|detected|🎯|🌟)" "$LOGFILE" | tail -n 50
        else
            tail -n 100 "$LOGFILE"
        fi
    else
        echo "❌ Log file not found: $LOGFILE"
    fi
}

# Function to test enhanced single run
test_run() {
    echo "🧪 Running enhanced detection cycle for testing..."
    echo "🌟 Testing: Cross-platform analysis + Jupiter/Meteora emerging discovery"
    
    # Check if configuration exists
    if [ ! -f "$SCRIPT_DIR/config/config.yaml" ]; then
        echo "❌ Configuration file not found: $SCRIPT_DIR/config/config.yaml"
        return 1
    fi
    
    cd "$SCRIPT_DIR"
    source venv/bin/activate
    export PYTHONPATH=$SCRIPT_DIR:$PYTHONPATH
    python scripts/high_conviction_token_detector.py --single-run --emerging-enabled
}

# Function to test pure scoring system
test_scoring() {
    echo "🧪 Testing pure scoring system..."
    
    cd "$SCRIPT_DIR"
    source venv/bin/activate
    export PYTHONPATH=$SCRIPT_DIR:$PYTHONPATH
    python scripts/cross_platform_token_analyzer.py
}

# Function to monitor token discovery
monitor_discovery() {
    echo "🌟 Monitoring token discovery activity..."
    echo "📊 Showing real-time scoring and discovery stats"
    
    if [ -f "$LOGFILE" ]; then
        tail -f "$LOGFILE" | grep -E "(Jupiter|Meteora|detected|score|🎯|🌟|📊)" --line-buffered
    else
        echo "❌ Log file not found. Start the daemon first."
    fi
}

# Function to show performance stats
show_stats() {
    echo "📊 Enhanced Detector Performance Statistics:"
    echo "==========================================="
    
    if [ -f "$LOGFILE" ]; then
        echo "🔍 Recent Detection Cycles:"
        grep "detection cycle completed" "$LOGFILE" | tail -n 5
        
        echo ""
        echo "🌟 Token Discovery Activity:"
        grep -c "tokens analyzed" "$LOGFILE" | tail -1 && echo " tokens analyzed" || echo "0 tokens analyzed"
        grep -c "high conviction" "$LOGFILE" | tail -1 && echo " high conviction tokens found" || echo "0 high conviction tokens found"
        
        echo ""
        echo "🎯 High Conviction Alerts:"
        grep -c "Alert sent" "$LOGFILE" && echo " alerts sent" || echo "0 alerts sent"
        
        echo ""
        echo "🪐 Jupiter API Activity:"
        grep -c "Jupiter" "$LOGFILE" && echo " Jupiter API calls" || echo "0 Jupiter API calls"
        
        echo ""
        echo "🌊 Meteora API Activity:"
        grep -c "Meteora" "$LOGFILE" && echo " Meteora API calls" || echo "0 Meteora API calls"
    else
        echo "❌ No log file found. Start the daemon to collect statistics."
    fi
}

# Function to create enhanced systemd service
create_systemd_service() {
    local service_name="enhanced-high-conviction-detector"
    local service_file="/etc/systemd/system/${service_name}.service"
    local user=$(whoami)
    
    echo "🔧 Creating enhanced systemd service with emerging token discovery..."
    
    # Check if running as root or with sudo
    if [ "$EUID" -ne 0 ]; then
        echo "❌ Root privileges required to create systemd service"
        echo "   Run with: sudo $0 install-service"
        return 1
    fi
    
    # Create service file
    cat > "$service_file" << EOF
[Unit]
Description=Enhanced High Conviction Token Detector with Emerging Discovery
After=network.target
Wants=network-online.target

[Service]
Type=simple
User=$user
WorkingDirectory=$SCRIPT_DIR
Environment=PYTHONPATH=$SCRIPT_DIR
ExecStart=$SCRIPT_DIR/venv/bin/python $SCRIPT_DIR/scripts/high_conviction_token_detector.py --interval 15 --emerging-enabled
Restart=always
RestartSec=60
StandardOutput=append:$SCRIPT_DIR/logs/systemd_enhanced_detector.log
StandardError=append:$SCRIPT_DIR/logs/systemd_enhanced_detector.log

[Install]
WantedBy=multi-user.target
EOF

    # Reload systemd and enable service
    systemctl daemon-reload
    systemctl enable "$service_name"
    
    echo "✅ Enhanced systemd service created: $service_name"
    echo "🚀 Start with: sudo systemctl start $service_name"
    echo "📊 Status with: sudo systemctl status $service_name"
    echo "📋 Logs with: sudo journalctl -u $service_name -f"
}

# Function to show help
show_help() {
    echo "🌟 Enhanced High Conviction Token Detector Daemon"
    echo "================================================="
    echo "Features: Cross-platform analysis + Jupiter/Meteora emerging discovery"
    echo ""
    echo "Usage: $0 {start|stop|restart|status|logs|test|help}"
    echo ""
    echo "Commands:"
    echo "  start               Start the enhanced daemon"
    echo "  stop                Stop the daemon"
    echo "  restart             Restart the daemon"
    echo "  status              Show daemon status and recent activity"
    echo "  logs [-f|-a]        Show logs (use -f to follow, -a for API activity)"
    echo "  test                Run single enhanced detection cycle"
    echo "  test-scoring        Test pure scoring system"
    echo "  monitor-discovery   Monitor token discovery in real-time"
    echo "  stats               Show performance statistics"
    echo "  install-service     Create systemd service (requires sudo)"
    echo "  help                Show this help message"
    echo ""
    echo "Enhanced Features:"
    echo "  🎯 Cross-platform validation (DexScreener, RugCheck, Birdeye)"
    echo "  🌟 Emerging token discovery (Jupiter, Meteora)"
    echo "  🏷️ Pure scoring system (no categories)"
    echo "  📊 Risk-based scoring and alerts"
    echo "  🔍 287K+ token universe coverage"
    echo ""
    echo "Examples:"
    echo "  $0 start                    # Start enhanced daemon"
    echo "  $0 logs -a                  # Show API activity"
    echo "  $0 monitor-discovery        # Real-time discovery monitoring"
    echo "  $0 test-scoring             # Test the pure scoring system"
}

case "$1" in
    start)
        start_daemon
        ;;
    stop)
        stop_daemon
        ;;
    restart)
        restart_daemon
        ;;
    status)
        status_daemon
        ;;
    logs)
        show_logs "$2"
        ;;
    test)
        test_run
        ;;
    test-scoring)
        test_scoring
        ;;
    monitor-discovery)
        monitor_discovery
        ;;
    stats)
        show_stats
        ;;
    install-service)
        create_systemd_service
        ;;
    help|--help|-h)
        show_help
        ;;
    *)
        echo "❌ Unknown command: $1"
        echo ""
        show_help
        exit 1
        ;;
esac 