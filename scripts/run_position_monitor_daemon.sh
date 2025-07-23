#!/bin/bash

# Position Monitor Daemon Control Script
# Manages the position tracking and exit signal monitoring daemon

# Configuration
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$SCRIPT_DIR"
DAEMON_SCRIPT="$PROJECT_DIR/scripts/position_monitor.py"
PID_FILE="$PROJECT_DIR/data/position_monitor.pid"
LOG_FILE="$PROJECT_DIR/logs/position_monitor.log"
CONFIG_FILE="$PROJECT_DIR/config/config.yaml"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
PURPLE='\033[0;35m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

# Emojis for better UX
ROCKET="🚀"
STOP="🛑"
INFO="ℹ️"
SUCCESS="✅"
ERROR="❌"
WARNING="⚠️"
MONITOR="📊"
GEAR="⚙️"

# Ensure directories exist
mkdir -p "$(dirname "$PID_FILE")"
mkdir -p "$(dirname "$LOG_FILE")"

print_header() {
    echo -e "${BLUE}"
    echo "╔══════════════════════════════════════════════════════════════╗"
    echo "║                    Position Monitor Daemon                   ║"
    echo "║              Track Positions & Monitor Exit Signals         ║"
    echo "╚══════════════════════════════════════════════════════════════╝"
    echo -e "${NC}"
}

print_usage() {
    echo -e "${CYAN}Usage: $0 {start|stop|restart|status|logs|test|install-service|help}${NC}"
    echo ""
    echo -e "${YELLOW}Commands:${NC}"
    echo -e "  ${GREEN}start${NC}           Start the position monitor daemon"
    echo -e "  ${RED}stop${NC}            Stop the position monitor daemon"
    echo -e "  ${YELLOW}restart${NC}         Restart the position monitor daemon"
    echo -e "  ${BLUE}status${NC}          Show daemon status and statistics"
    echo -e "  ${PURPLE}logs${NC}           Show recent log entries"
    echo -e "  ${CYAN}test${NC}            Run a single monitoring cycle (test mode)"
    echo -e "  ${GEAR}install-service${NC} Install as systemd service (Linux only)"
    echo -e "  ${INFO}help${NC}            Show this help message"
    echo ""
    echo -e "${YELLOW}Examples:${NC}"
    echo -e "  $0 start                    # Start monitoring daemon"
    echo -e "  $0 test                     # Test single monitoring cycle"
    echo -e "  $0 logs                     # View recent logs"
    echo -e "  $0 status                   # Check daemon status"
}

check_dependencies() {
    # Check if Python script exists
    if [ ! -f "$DAEMON_SCRIPT" ]; then
        echo -e "${ERROR} Position monitor script not found: $DAEMON_SCRIPT"
        return 1
    fi
    
    # Check if config exists
    if [ ! -f "$CONFIG_FILE" ]; then
        echo -e "${WARNING} Config file not found: $CONFIG_FILE"
        echo -e "${INFO} Please ensure your configuration is set up properly"
        return 1
    fi
    
    # Check Python environment
    if ! command -v python3 &> /dev/null; then
        echo -e "${ERROR} Python 3 is required but not installed"
        return 1
    fi
    
    return 0
}

get_pid() {
    if [ -f "$PID_FILE" ]; then
        cat "$PID_FILE"
    else
        echo ""
    fi
}

is_running() {
    local pid=$(get_pid)
    if [ -n "$pid" ] && kill -0 "$pid" 2>/dev/null; then
        return 0
    else
        return 1
    fi
}

start_daemon() {
    echo -e "${ROCKET} Starting Position Monitor Daemon..."
    
    if ! check_dependencies; then
        echo -e "${ERROR} Dependency check failed"
        return 1
    fi
    
    if is_running; then
        local pid=$(get_pid)
        echo -e "${WARNING} Position monitor is already running (PID: $pid)"
        return 1
    fi
    
    # Clean up stale PID file
    rm -f "$PID_FILE"
    
    # Start the daemon
    echo -e "${INFO} Starting position monitor daemon..."
    echo -e "${INFO} Config: $CONFIG_FILE"
    echo -e "${INFO} Logs: $LOG_FILE"
    
    # Set PYTHONPATH to include project directory
    export PYTHONPATH="$PROJECT_DIR:$PYTHONPATH"
    
    # Start daemon in background
    cd "$PROJECT_DIR"
    nohup python3 "$DAEMON_SCRIPT" --config "$CONFIG_FILE" > "$LOG_FILE" 2>&1 &
    local daemon_pid=$!
    
    # Save PID
    echo $daemon_pid > "$PID_FILE"
    
    # Wait a moment and check if it's still running
    sleep 3
    if is_running; then
        echo -e "${SUCCESS} Position monitor daemon started successfully!"
        echo -e "${INFO} PID: $daemon_pid"
        echo -e "${INFO} Use '$0 status' to check status"
        echo -e "${INFO} Use '$0 logs' to view logs"
        return 0
    else
        echo -e "${ERROR} Failed to start position monitor daemon"
        echo -e "${INFO} Check logs for details: tail -f $LOG_FILE"
        rm -f "$PID_FILE"
        return 1
    fi
}

stop_daemon() {
    echo -e "${STOP} Stopping Position Monitor Daemon..."
    
    local pid=$(get_pid)
    
    if [ -z "$pid" ]; then
        echo -e "${WARNING} Position monitor daemon is not running"
        return 1
    fi
    
    if ! kill -0 "$pid" 2>/dev/null; then
        echo -e "${WARNING} Process $pid is not running, cleaning up PID file"
        rm -f "$PID_FILE"
        return 1
    fi
    
    echo -e "${INFO} Sending SIGTERM to process $pid..."
    kill -TERM "$pid"
    
    # Wait for graceful shutdown
    local count=0
    while kill -0 "$pid" 2>/dev/null && [ $count -lt 30 ]; do
        echo -e "${INFO} Waiting for graceful shutdown... ($count/30)"
        sleep 1
        count=$((count + 1))
    done
    
    if kill -0 "$pid" 2>/dev/null; then
        echo -e "${WARNING} Process didn't stop gracefully, forcing shutdown..."
        kill -KILL "$pid"
        sleep 2
    fi
    
    rm -f "$PID_FILE"
    echo -e "${SUCCESS} Position monitor daemon stopped"
    return 0
}

restart_daemon() {
    echo -e "${YELLOW} Restarting Position Monitor Daemon...${NC}"
    stop_daemon
    sleep 2
    start_daemon
}

show_status() {
    print_header
    
    local pid=$(get_pid)
    
    if is_running; then
        echo -e "${SUCCESS} Position Monitor Status: ${GREEN}RUNNING${NC}"
        echo -e "${INFO} PID: $pid"
        
        # Get process info
        if command -v ps &> /dev/null; then
            local start_time=$(ps -p "$pid" -o lstart= 2>/dev/null | xargs)
            local cpu_usage=$(ps -p "$pid" -o %cpu= 2>/dev/null | xargs)
            local mem_usage=$(ps -p "$pid" -o %mem= 2>/dev/null | xargs)
            
            echo -e "${INFO} Started: $start_time"
            echo -e "${INFO} CPU Usage: ${cpu_usage}%"
            echo -e "${INFO} Memory Usage: ${mem_usage}%"
        fi
        
        # Show recent activity from logs
        if [ -f "$LOG_FILE" ]; then
            echo ""
            echo -e "${MONITOR} Recent Activity:"
            echo -e "${BLUE}$(tail -n 5 "$LOG_FILE" | grep -E "(Starting|completed|Alerts sent|positions)" | tail -3)${NC}"
        fi
        
    else
        echo -e "${ERROR} Position Monitor Status: ${RED}NOT RUNNING${NC}"
        
        if [ -f "$PID_FILE" ]; then
            echo -e "${WARNING} Stale PID file found: $PID_FILE"
        fi
    fi
    
    # Show configuration info
    echo ""
    echo -e "${GEAR} Configuration:"
    echo -e "${INFO} Config File: $CONFIG_FILE"
    echo -e "${INFO} Log File: $LOG_FILE"
    echo -e "${INFO} PID File: $PID_FILE"
    
    # Show position statistics if possible
    if [ -f "$PROJECT_DIR/data/positions.db" ]; then
        echo ""
        echo -e "${MONITOR} Position Database:"
        echo -e "${INFO} Database: $PROJECT_DIR/data/positions.db"
        
        # Try to get basic stats using sqlite3 if available
        if command -v sqlite3 &> /dev/null; then
            local active_positions=$(sqlite3 "$PROJECT_DIR/data/positions.db" "SELECT COUNT(*) FROM positions WHERE status='active';" 2>/dev/null || echo "N/A")
            local total_users=$(sqlite3 "$PROJECT_DIR/data/positions.db" "SELECT COUNT(DISTINCT user_id) FROM positions;" 2>/dev/null || echo "N/A")
            echo -e "${INFO} Active Positions: $active_positions"
            echo -e "${INFO} Total Users: $total_users"
        fi
    fi
}

show_logs() {
    echo -e "${PURPLE} Position Monitor Logs:${NC}"
    echo -e "${INFO} Log file: $LOG_FILE"
    echo ""
    
    if [ -f "$LOG_FILE" ]; then
        echo -e "${BLUE}Recent entries (last 20 lines):${NC}"
        tail -n 20 "$LOG_FILE"
        echo ""
        echo -e "${INFO} Use 'tail -f $LOG_FILE' to follow logs in real-time"
    else
        echo -e "${WARNING} Log file not found: $LOG_FILE"
        echo -e "${INFO} Start the daemon to generate logs"
    fi
}

test_run() {
    echo -e "${CYAN} Running Position Monitor Test Cycle...${NC}"
    
    if ! check_dependencies; then
        echo -e "${ERROR} Dependency check failed"
        return 1
    fi
    
    if is_running; then
        echo -e "${WARNING} Position monitor daemon is currently running"
        echo -e "${INFO} Stop the daemon first or check logs for ongoing activity"
        return 1
    fi
    
    echo -e "${INFO} Executing single monitoring cycle..."
    echo -e "${INFO} This will analyze all active positions and check for exit signals"
    echo ""
    
    # Set PYTHONPATH and run test
    export PYTHONPATH="$PROJECT_DIR:$PYTHONPATH"
    cd "$PROJECT_DIR"
    
    python3 "$DAEMON_SCRIPT" --config "$CONFIG_FILE" --test-run
    local exit_code=$?
    
    echo ""
    if [ $exit_code -eq 0 ]; then
        echo -e "${SUCCESS} Test cycle completed successfully!"
        echo -e "${INFO} Check the output above for analysis results"
    else
        echo -e "${ERROR} Test cycle failed with exit code: $exit_code"
        echo -e "${INFO} Check the error messages above for details"
    fi
    
    return $exit_code
}

install_service() {
    echo -e "${GEAR} Installing Position Monitor as systemd service...${NC}"
    
    if [ "$EUID" -ne 0 ]; then
        echo -e "${ERROR} Please run with sudo to install systemd service"
        return 1
    fi
    
    if ! command -v systemctl &> /dev/null; then
        echo -e "${ERROR} systemctl not found. This feature requires systemd."
        return 1
    fi
    
    local service_file="/etc/systemd/system/position-monitor.service"
    local current_user=$(logname)
    
    cat > "$service_file" << EOF
[Unit]
Description=Virtuoso Position Monitor Daemon
After=network.target
Wants=network.target

[Service]
Type=simple
User=$current_user
WorkingDirectory=$PROJECT_DIR
Environment=PYTHONPATH=$PROJECT_DIR
ExecStart=/usr/bin/python3 $DAEMON_SCRIPT --config $CONFIG_FILE
Restart=always
RestartSec=10
StandardOutput=append:$LOG_FILE
StandardError=append:$LOG_FILE

[Install]
WantedBy=multi-user.target
EOF
    
    systemctl daemon-reload
    systemctl enable position-monitor.service
    
    echo -e "${SUCCESS} Service installed successfully!"
    echo -e "${INFO} Start with: sudo systemctl start position-monitor"
    echo -e "${INFO} Check status: sudo systemctl status position-monitor"
    echo -e "${INFO} View logs: sudo journalctl -u position-monitor -f"
}

# Main script logic
case "${1:-}" in
    start)
        print_header
        start_daemon
        ;;
    stop)
        print_header
        stop_daemon
        ;;
    restart)
        print_header
        restart_daemon
        ;;
    status)
        show_status
        ;;
    logs)
        show_logs
        ;;
    test)
        test_run
        ;;
    install-service)
        install_service
        ;;
    help|--help|-h)
        print_header
        print_usage
        ;;
    *)
        print_header
        echo -e "${ERROR} Invalid command: ${1:-<empty>}"
        echo ""
        print_usage
        exit 1
        ;;
esac 