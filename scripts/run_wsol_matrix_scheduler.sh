#!/bin/bash

# WSOL Matrix Scheduler Daemon Script
# Runs the automated WSOL matrix refresh service with monitoring

set -e

# Configuration
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PID_FILE="$SCRIPT_DIR/wsol_matrix_scheduler.pid"
LOG_FILE="$SCRIPT_DIR/logs/wsol_matrix_scheduler.log"
ERROR_LOG="$SCRIPT_DIR/logs/wsol_matrix_scheduler_error.log"
PYTHON_SCRIPT="$SCRIPT_DIR/services/wsol_matrix_scheduler.py"
REFRESH_INTERVAL=45  # minutes
MAX_RESTARTS=5
RESTART_DELAY=30  # seconds

# Ensure log directory exists
mkdir -p "$SCRIPT_DIR/logs"

# Function to show usage
show_usage() {
    echo "🔄 WSOL Matrix Scheduler Daemon"
    echo ""
    echo "Usage: $0 {start|stop|restart|status|logs|monitor}"
    echo ""
    echo "Commands:"
    echo "  start    - Start the scheduler daemon"
    echo "  stop     - Stop the scheduler daemon"
    echo "  restart  - Restart the scheduler daemon"
    echo "  status   - Show scheduler status and performance metrics"
    echo "  logs     - Show recent log entries"
    echo "  monitor  - Real-time log monitoring"
    echo ""
    echo "Options:"
    echo "  --interval N  - Set refresh interval to N minutes (default: 45)"
    echo ""
    exit 1
}

# Function to check if scheduler is running
is_running() {
    if [ -f "$PID_FILE" ]; then
        local pid=$(cat "$PID_FILE")
        if ps -p "$pid" > /dev/null 2>&1; then
            return 0
        else
            rm -f "$PID_FILE"
            return 1
        fi
    fi
    return 1
}

# Function to start the scheduler
start_scheduler() {
    if is_running; then
        echo "⚠️  WSOL Matrix Scheduler is already running (PID: $(cat $PID_FILE))"
        return 1
    fi
    
    echo "🚀 Starting WSOL Matrix Scheduler..."
    echo "   📁 Working Directory: $SCRIPT_DIR"
    echo "   🔄 Refresh Interval: $REFRESH_INTERVAL minutes" 
    echo "   📝 Log File: $LOG_FILE"
    
    # Start the scheduler in background
    cd "$SCRIPT_DIR"
    nohup python3 "$PYTHON_SCRIPT" --interval "$REFRESH_INTERVAL" \
        >> "$LOG_FILE" 2>> "$ERROR_LOG" &
    
    local pid=$!
    echo "$pid" > "$PID_FILE"
    
    # Wait a moment to see if it starts successfully
    sleep 2
    if is_running; then
        echo "✅ WSOL Matrix Scheduler started successfully (PID: $pid)"
        echo "   📊 Use '$0 status' to check performance metrics"
        echo "   📋 Use '$0 logs' to view logs"
        return 0
    else
        echo "❌ Failed to start WSOL Matrix Scheduler"
        if [ -f "$ERROR_LOG" ]; then
            echo "Recent errors:"
            tail -5 "$ERROR_LOG"
        fi
        return 1
    fi
}

# Function to stop the scheduler
stop_scheduler() {
    if ! is_running; then
        echo "⚠️  WSOL Matrix Scheduler is not running"
        return 1
    fi
    
    local pid=$(cat "$PID_FILE")
    echo "⏹️  Stopping WSOL Matrix Scheduler (PID: $pid)..."
    
    # Send SIGTERM
    kill "$pid" 2>/dev/null || true
    
    # Wait for graceful shutdown
    local count=0
    while [ $count -lt 10 ] && ps -p "$pid" > /dev/null 2>&1; do
        sleep 1
        count=$((count + 1))
    done
    
    # Force kill if still running
    if ps -p "$pid" > /dev/null 2>&1; then
        echo "⚡ Force killing scheduler..."
        kill -9 "$pid" 2>/dev/null || true
        sleep 1
    fi
    
    rm -f "$PID_FILE"
    echo "✅ WSOL Matrix Scheduler stopped"
}

# Function to restart the scheduler
restart_scheduler() {
    echo "🔄 Restarting WSOL Matrix Scheduler..."
    stop_scheduler
    sleep 2
    start_scheduler
}

# Function to show status and performance metrics
show_status() {
    echo "📊 WSOL Matrix Scheduler Status"
    echo "================================"
    
    if is_running; then
        local pid=$(cat "$PID_FILE")
        echo "🟢 Status: RUNNING (PID: $pid)"
        
        # Show process information
        echo "💾 Memory Usage: $(ps -o rss= -p "$pid" | awk '{print int($1/1024)" MB"}' 2>/dev/null || echo "N/A")"
        echo "⏱️  CPU Usage: $(ps -o %cpu= -p "$pid" 2>/dev/null || echo "N/A")%"
        echo "🕐 Start Time: $(ps -o lstart= -p "$pid" 2>/dev/null || echo "N/A")"
        
        # Get scheduler performance metrics
        echo ""
        echo "📈 Performance Metrics:"
        python3 "$PYTHON_SCRIPT" --status 2>/dev/null || echo "   ⚠️ Unable to fetch performance metrics"
        
    else
        echo "🔴 Status: NOT RUNNING"
    fi
    
    echo ""
    echo "📋 Log Files:"
    echo "   📝 Main Log: $LOG_FILE"
    echo "   ❌ Error Log: $ERROR_LOG"
    
    # Show recent log summary
    if [ -f "$LOG_FILE" ]; then
        echo ""
        echo "📄 Recent Activity (last 5 lines):"
        tail -5 "$LOG_FILE" | sed 's/^/   /'
    fi
}

# Function to show logs
show_logs() {
    local lines=${1:-50}
    
    echo "📋 WSOL Matrix Scheduler Logs (last $lines lines)"
    echo "=================================================="
    
    if [ -f "$LOG_FILE" ]; then
        tail -n "$lines" "$LOG_FILE"
    else
        echo "No log file found at $LOG_FILE"
    fi
    
    if [ -f "$ERROR_LOG" ] && [ -s "$ERROR_LOG" ]; then
        echo ""
        echo "❌ Recent Errors:"
        tail -n 10 "$ERROR_LOG"
    fi
}

# Function to monitor logs in real-time
monitor_logs() {
    echo "👁️  Monitoring WSOL Matrix Scheduler logs (Ctrl+C to exit)"
    echo "==========================================================="
    
    if [ -f "$LOG_FILE" ]; then
        tail -f "$LOG_FILE"
    else
        echo "No log file found at $LOG_FILE"
        echo "Start the scheduler first with: $0 start"
    fi
}

# Function to setup systemd service (optional)
setup_systemd() {
    local service_file="/etc/systemd/system/wsol-matrix-scheduler.service"
    
    echo "⚙️  Setting up systemd service..."
    
    sudo tee "$service_file" > /dev/null << EOF
[Unit]
Description=WSOL Matrix Scheduler
After=network.target

[Service]
Type=simple
User=$USER
WorkingDirectory=$SCRIPT_DIR
ExecStart=/usr/bin/python3 $PYTHON_SCRIPT --interval $REFRESH_INTERVAL
Restart=always
RestartSec=30

# Logging
StandardOutput=append:$LOG_FILE
StandardError=append:$ERROR_LOG

[Install]
WantedBy=multi-user.target
EOF

    sudo systemctl daemon-reload
    echo "✅ Systemd service created at $service_file"
    echo "   Enable with: sudo systemctl enable wsol-matrix-scheduler"
    echo "   Start with: sudo systemctl start wsol-matrix-scheduler"
}

# Parse command line arguments
COMMAND=""
while [[ $# -gt 0 ]]; do
    case $1 in
        start|stop|restart|status|logs|monitor|setup-systemd)
            COMMAND="$1"
            shift
            ;;
        --interval)
            REFRESH_INTERVAL="$2"
            shift 2
            ;;
        --lines)
            LOG_LINES="$2"
            shift 2
            ;;
        -h|--help)
            show_usage
            ;;
        *)
            echo "Unknown option: $1"
            show_usage
            ;;
    esac
done

# Execute command
case "$COMMAND" in
    start)
        start_scheduler
        ;;
    stop)
        stop_scheduler
        ;;
    restart)
        restart_scheduler
        ;;
    status)
        show_status
        ;;
    logs)
        show_logs "${LOG_LINES:-50}"
        ;;
    monitor)
        monitor_logs
        ;;
    setup-systemd)
        setup_systemd
        ;;
    "")
        show_usage
        ;;
    *)
        echo "Unknown command: $COMMAND"
        show_usage
        ;;
esac 