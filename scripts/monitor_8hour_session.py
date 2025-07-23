#!/usr/bin/env python3
"""
8-Hour Session Monitor

This script monitors the progress of the 8-hour optimized scan session.
It shows real-time progress, performance metrics, and cost tracking.
"""

import os
import sys
import time
import json
from datetime import datetime, timedelta
from pathlib import Path

# Add project root to Python path
project_root = Path(__file__).parent.parent.absolute()
sys.path.insert(0, str(project_root))

def monitor_session_progress():
    """Monitor the 8-hour session progress."""
    print("🔍 8-Hour Session Monitor")
    print("=" * 50)
    
    # Session configuration
    total_scans = 8
    interval_minutes = 60
    total_duration_hours = 8
    
    # Calculate expected completion time (approximate)
    start_time = datetime.now()
    expected_completion = start_time + timedelta(hours=total_duration_hours)
    
    print(f"📊 Session Overview:")
    print(f"   • Total scans: {total_scans}")
    print(f"   • Interval: {interval_minutes} minutes")
    print(f"   • Total duration: {total_duration_hours} hours")
    print(f"   • Started: {start_time.strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"   • Expected completion: {expected_completion.strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"   • Next scan: Every hour on the hour")
    
    # Monitor log files for progress
    logs_dir = project_root / "logs"
    performance_dir = project_root / "data" / "performance_monitoring"
    
    print(f"\n📂 Monitoring directories:")
    print(f"   • Logs: {logs_dir}")
    print(f"   • Performance: {performance_dir}")
    
    print(f"\n🔄 Monitoring session progress...")
    print(f"   Press Ctrl+C to stop monitoring (session will continue)")
    
    scan_count = 0
    last_scan_time = None
    
    while True:
        try:
            current_time = datetime.now()
            elapsed = current_time - start_time
            
            # Check for log files
            log_files = list(logs_dir.glob("virtuoso_gem_hunter*.log"))
            
            # Check for performance files
            perf_files = list(performance_dir.glob("*.json")) if performance_dir.exists() else []
            
            # Display current status
            print(f"\r⏰ {current_time.strftime('%H:%M:%S')} | "
                  f"Elapsed: {str(elapsed).split('.')[0]} | "
                  f"Scans: {scan_count}/{total_scans} | "
                  f"Logs: {len(log_files)} | "
                  f"Perf: {len(perf_files)}", end="", flush=True)
            
            # Check if we should have had a new scan
            minutes_elapsed = elapsed.total_seconds() / 60
            expected_scans = int(minutes_elapsed / interval_minutes) + 1
            
            if expected_scans > scan_count and expected_scans <= total_scans:
                scan_count = expected_scans
                last_scan_time = current_time
                print(f"\n🔍 Scan {scan_count} should be running...")
            
            # Check if session should be complete
            if elapsed.total_seconds() > (total_duration_hours * 3600 + 300):  # 5 min buffer
                print(f"\n✅ Session should be complete!")
                break
            
            time.sleep(10)  # Update every 10 seconds
            
        except KeyboardInterrupt:
            print(f"\n\n⚠️ Monitoring stopped by user")
            print(f"📊 Final status:")
            print(f"   • Elapsed time: {str(elapsed).split('.')[0]}")
            print(f"   • Expected scans completed: {scan_count}/{total_scans}")
            print(f"   • Session continues running in background")
            break
        except Exception as e:
            print(f"\n❌ Monitoring error: {e}")
            time.sleep(30)  # Wait longer on error

def check_session_status():
    """Check if the session is still running."""
    try:
        # Check for running Python processes
        import subprocess
        result = subprocess.run(['pgrep', '-f', 'run_optimized_10_scan_test.py'], 
                              capture_output=True, text=True)
        
        if result.returncode == 0:
            pids = result.stdout.strip().split('\n')
            print(f"✅ Session is running (PIDs: {', '.join(pids)})")
            return True
        else:
            print(f"❌ Session not found running")
            return False
    except Exception as e:
        print(f"⚠️ Could not check session status: {e}")
        return None

def show_recent_logs():
    """Show recent log entries."""
    logs_dir = project_root / "logs"
    if not logs_dir.exists():
        print("❌ Logs directory not found")
        return
    
    log_files = list(logs_dir.glob("virtuoso_gem_hunter*.log"))
    if not log_files:
        print("❌ No log files found")
        return
    
    # Get the most recent log file
    latest_log = max(log_files, key=lambda f: f.stat().st_mtime)
    
    print(f"📄 Recent entries from {latest_log.name}:")
    print("-" * 50)
    
    try:
        with open(latest_log, 'r') as f:
            lines = f.readlines()
            # Show last 10 lines
            for line in lines[-10:]:
                print(line.strip())
    except Exception as e:
        print(f"❌ Error reading log file: {e}")

if __name__ == "__main__":
    print("🚀 8-Hour Optimized Scan Session Monitor")
    print("=" * 60)
    
    # Check session status
    session_running = check_session_status()
    
    if session_running:
        print("\n🔄 Starting monitoring...")
        monitor_session_progress()
    else:
        print("\n⚠️ Session doesn't appear to be running")
        print("📄 Showing recent logs instead:")
        show_recent_logs() 