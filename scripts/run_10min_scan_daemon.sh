#!/bin/bash

# 10-Minute Token Scanner Daemon
# This script can run the token scanner as a background daemon process
# with automatic restart capabilities and process management

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PIDFILE="$SCRIPT_DIR/scanner_daemon.pid"
LOGFILE="$SCRIPT_DIR/logs/scanner_daemon.log"

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
        echo "❌ Scanner daemon is already running (PID: $(cat $PIDFILE))"
        return 1
    fi

    echo "🚀 Starting 10-minute token scanner daemon..."
    
    # Create logs directory
    mkdir -p "$SCRIPT_DIR/logs"
    
    # Start the scanner in background
    cd "$SCRIPT_DIR"
    nohup bash -c "
        source venv/bin/activate
        export SCAN_INTERVAL_MINUTES=10
        export ENHANCED_TIMEFRAMES=true
        python monitor.py run --enhanced-timeframes true
    " > "$LOGFILE" 2>&1 &
    
    local pid=$!
    echo $pid > "$PIDFILE"
    
    # Wait a moment to check if it started successfully
    sleep 3
    if is_running; then
        echo "✅ Scanner daemon started successfully (PID: $pid)"
        echo "📋 Logs: $LOGFILE"
        echo "🛑 Stop with: $0 stop"
        return 0
    else
        echo "❌ Failed to start scanner daemon"
        rm -f "$PIDFILE"
        return 1
    fi
}

# Function to stop the daemon
stop_daemon() {
    if ! is_running; then
        echo "❌ Scanner daemon is not running"
        return 1
    fi

    local pid=$(cat "$PIDFILE")
    echo "🛑 Stopping scanner daemon (PID: $pid)..."
    
    # Try graceful shutdown first
    kill -TERM "$pid" 2>/dev/null
    
    # Wait up to 10 seconds for graceful shutdown
    local count=0
    while [ $count -lt 10 ] && ps -p "$pid" > /dev/null 2>&1; do
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
    echo "✅ Scanner daemon stopped"
}

# Function to restart the daemon
restart_daemon() {
    echo "🔄 Restarting scanner daemon..."
    stop_daemon
    sleep 2
    start_daemon
}

# Function to show daemon status
status_daemon() {
    if is_running; then
        local pid=$(cat "$PIDFILE")
        echo "✅ Scanner daemon is running (PID: $pid)"
        
        # Show process info
        echo "📊 Process Info:"
        ps -p "$pid" -o pid,ppid,cmd,etime,pcpu,pmem 2>/dev/null || echo "   Unable to get process info"
        
        # Show recent log entries
        if [ -f "$LOGFILE" ]; then
            echo ""
            echo "📋 Recent Log Entries (last 10 lines):"
            tail -n 10 "$LOGFILE"
        fi
        
        return 0
    else
        echo "❌ Scanner daemon is not running"
        return 1
    fi
}

# Function to show logs
show_logs() {
    if [ -f "$LOGFILE" ]; then
        echo "📋 Scanner Daemon Logs:"
        echo "======================"
        if [ "$1" = "follow" ] || [ "$1" = "-f" ]; then
            tail -f "$LOGFILE"
        else
            tail -n 50 "$LOGFILE"
        fi
    else
        echo "❌ Log file not found: $LOGFILE"
    fi
}

# Function to create systemd service
create_systemd_service() {
    local service_name="token-scanner"
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
Description=10-Minute Token Scanner with RugCheck Security
After=network.target
Wants=network-online.target

[Service]
Type=simple
User=$user
WorkingDirectory=$SCRIPT_DIR
Environment=SCAN_INTERVAL_MINUTES=10
Environment=ENHANCED_TIMEFRAMES=true
ExecStart=$SCRIPT_DIR/venv/bin/python $SCRIPT_DIR/monitor.py run --enhanced-timeframes true
Restart=always
RestartSec=30
StandardOutput=append:$SCRIPT_DIR/logs/systemd_scanner.log
StandardError=append:$SCRIPT_DIR/logs/systemd_scanner.log

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
    echo "🛡️ 10-Minute Token Scanner Daemon Control"
    echo "=========================================="
    echo ""
    echo "Usage: $0 {start|stop|restart|status|logs|install-service|help}"
    echo ""
    echo "Commands:"
    echo "  start           Start the scanner daemon"
    echo "  stop            Stop the scanner daemon"
    echo "  restart         Restart the scanner daemon"
    echo "  status          Show daemon status and recent logs"
    echo "  logs            Show recent logs (add -f to follow)"
    echo "  install-service Create systemd service (requires sudo)"
    echo "  help            Show this help message"
    echo ""
    echo "Examples:"
    echo "  $0 start                    # Start daemon"
    echo "  $0 logs -f                  # Follow logs in real-time"
    echo "  sudo $0 install-service     # Install as system service"
    echo ""
    echo "Features:"
    echo "  • 10-minute scan intervals"
    echo "  • RugCheck security filtering"
    echo "  • Background daemon operation"
    echo "  • Automatic restart on failure"
    echo "  • Structured logging"
    echo "  • Systemd integration"
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
    install-service)
        create_systemd_service
        ;;
    help|--help|-h)
        show_help
        ;;
    *)
        echo "❌ Invalid command: $1"
        echo ""
        show_help
        exit 1
        ;;
esac 