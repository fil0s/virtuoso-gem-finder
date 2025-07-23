#!/bin/bash

# High Conviction Token Detector Daemon
# This script runs the high conviction token detector as a background daemon process

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PIDFILE="$SCRIPT_DIR/high_conviction_detector_daemon.pid"
LOGFILE="$SCRIPT_DIR/logs/high_conviction_detector_daemon.log"

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

# Function to start the daemon
start_daemon() {
    if is_running; then
        echo "❌ High conviction detector daemon is already running (PID: $(cat $PIDFILE))"
        return 1
    fi

    echo "🚀 Starting high conviction token detector daemon..."
    
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
    
    # Start the detector in background
    cd "$SCRIPT_DIR"
    nohup bash -c "
        source venv/bin/activate
        export PYTHONPATH=$SCRIPT_DIR:\$PYTHONPATH
        python scripts/high_conviction_token_detector.py --interval 15
    " > "$LOGFILE" 2>&1 &
    
    local pid=$!
    echo $pid > "$PIDFILE"
    
    # Wait a moment to check if it started successfully
    sleep 5
    if is_running; then
        echo "✅ High conviction detector daemon started successfully (PID: $pid)"
        echo "📋 Logs: $LOGFILE"
        echo "🛑 Stop with: $0 stop"
        echo "📊 Status with: $0 status"
        return 0
    else
        echo "❌ Failed to start high conviction detector daemon"
        rm -f "$PIDFILE"
        echo "📋 Check logs for errors: $LOGFILE"
        return 1
    fi
}

# Function to stop the daemon
stop_daemon() {
    if ! is_running; then
        echo "❌ High conviction detector daemon is not running"
        return 1
    fi

    local pid=$(cat "$PIDFILE")
    echo "🛑 Stopping high conviction detector daemon (PID: $pid)..."
    
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
    echo "✅ High conviction detector daemon stopped"
}

# Function to restart the daemon
restart_daemon() {
    echo "🔄 Restarting high conviction detector daemon..."
    stop_daemon
    sleep 3
    start_daemon
}

# Function to show daemon status
status_daemon() {
    if is_running; then
        local pid=$(cat "$PIDFILE")
        echo "✅ High conviction detector daemon is running (PID: $pid)"
        
        # Show process info
        echo "📊 Process Info:"
        ps -p "$pid" -o pid,ppid,cmd,etime,pcpu,pmem 2>/dev/null || echo "   Unable to get process info"
        
        # Show recent log entries
        if [ -f "$LOGFILE" ]; then
            echo ""
            echo "📋 Recent Log Entries (last 15 lines):"
            tail -n 15 "$LOGFILE"
        fi
        
        return 0
    else
        echo "❌ High conviction detector daemon is not running"
        return 1
    fi
}

# Function to show logs
show_logs() {
    if [ -f "$LOGFILE" ]; then
        echo "📋 High Conviction Detector Daemon Logs:"
        echo "========================================"
        if [ "$1" = "follow" ] || [ "$1" = "-f" ]; then
            tail -f "$LOGFILE"
        else
            tail -n 100 "$LOGFILE"
        fi
    else
        echo "❌ Log file not found: $LOGFILE"
    fi
}

# Function to test single run
test_run() {
    echo "🧪 Running single detection cycle for testing..."
    
    # Check if configuration exists
    if [ ! -f "$SCRIPT_DIR/config/config.yaml" ]; then
        echo "❌ Configuration file not found: $SCRIPT_DIR/config/config.yaml"
        return 1
    fi
    
    cd "$SCRIPT_DIR"
    source venv/bin/activate
    export PYTHONPATH=$SCRIPT_DIR:$PYTHONPATH
    python scripts/high_conviction_token_detector.py --single-run
}

# Function to create systemd service
create_systemd_service() {
    local service_name="high-conviction-detector"
    local service_file="/etc/systemd/system/${service_name}.service"
    local user=$(whoami)
    
    echo "🔧 Creating systemd service..."
    
    # Check if running as root or with sudo
    if [ "$EUID" -ne 0 ]; then
        echo "❌ Root privileges required to create systemd service"
        echo "   Run with: sudo $0 install-service"
        return 1
    fi
    
    # Create service file
    cat > "$service_file" << EOF
[Unit]
Description=High Conviction Token Detector with Cross-Platform Analysis
After=network.target
Wants=network-online.target

[Service]
Type=simple
User=$user
WorkingDirectory=$SCRIPT_DIR
Environment=PYTHONPATH=$SCRIPT_DIR
ExecStart=$SCRIPT_DIR/venv/bin/python $SCRIPT_DIR/scripts/high_conviction_token_detector.py --interval 15
Restart=always
RestartSec=60
StandardOutput=append:$SCRIPT_DIR/logs/systemd_detector.log
StandardError=append:$SCRIPT_DIR/logs/systemd_detector.log

[Install]
WantedBy=multi-user.target
EOF

    # Reload systemd and enable service
    systemctl daemon-reload
    systemctl enable "$service_name"
    
    echo "✅ Systemd service created: $service_name"
    echo "🚀 Start with: sudo systemctl start $service_name"
    echo "📊 Status with: sudo systemctl status $service_name"
    echo "📋 Logs with: sudo journalctl -u $service_name -f"
}

# Function to show help
show_help() {
    echo "🎯 High Conviction Token Detector Daemon Control"
    echo "================================================"
    echo ""
    echo "Usage: $0 {start|stop|restart|status|logs|test|install-service|help}"
    echo ""
    echo "Commands:"
    echo "  start           Start the detector daemon"
    echo "  stop            Stop the detector daemon"
    echo "  restart         Restart the detector daemon"
    echo "  status          Show daemon status and recent logs"
    echo "  logs            Show recent logs (add -f to follow)"
    echo "  test            Run single detection cycle for testing"
    echo "  install-service Create systemd service (requires sudo)"
    echo "  help            Show this help message"
    echo ""
    echo "Examples:"
    echo "  $0 start                    # Start daemon"
    echo "  $0 test                     # Test single run"
    echo "  $0 logs -f                  # Follow logs in real-time"
    echo "  sudo $0 install-service     # Install as system service"
    echo ""
    echo "Features:"
    echo "  • 15-minute detection intervals"
    echo "  • Cross-platform analysis (DexScreener, RugCheck, Birdeye)"
    echo "  • Detailed Birdeye analysis for high-conviction tokens"
    echo "  • Whale and holder analysis"
    echo "  • Community and boosting information"
    echo "  • Comprehensive Telegram alerts"
    echo "  • Duplicate alert prevention"
    echo "  • Cost-optimized API usage"
    echo ""
    echo "Configuration:"
    echo "  • Copy config.example.yaml to config.yaml"
    echo "  • Set BIRDEYE_API_KEY environment variable"
    echo "  • Set TELEGRAM_BOT_TOKEN and TELEGRAM_CHAT_ID for alerts"
    echo "  • Enable Telegram in config.yaml"
}

# Main command handling
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