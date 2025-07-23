#!/usr/bin/env python3

import time
import os
import glob
import json
from datetime import datetime, timedelta
import subprocess
import sys

def get_latest_log_file():
    """Find the most recent monitoring log file"""
    # Look for any recent monitoring log files, not just comprehensive_3h
    patterns = [
        "logs/monitoring_runs/comprehensive_3h_*.log",
        "logs/monitoring_runs/*_$(date +%Y%m%d)_*.log",
        "logs/monitoring_runs/*.log"
    ]
    
    all_files = []
    for pattern in patterns:
        files = glob.glob(pattern)
        all_files.extend(files)
    
    if not all_files:
        return None
    
    # Get the most recently modified file
    latest_file = max(all_files, key=os.path.getmtime)
    
    # Check if the file was modified in the last 10 minutes (active session)
    if time.time() - os.path.getmtime(latest_file) < 600:  # 10 minutes
        return latest_file
    
    return None

def extract_api_stats_from_log(log_file):
    """Extract API statistics from log file"""
    if not os.path.exists(log_file):
        return None
    
    try:
        # Run comprehensive status to get current stats
        result = subprocess.run([
            sys.executable, "scripts/analysis/comprehensive_status.py"
        ], capture_output=True, text=True, timeout=30)
        
        if result.returncode == 0:
            output = result.stdout
            # Parse the output for key metrics
            stats = {}
            for line in output.split('\n'):
                if 'Total API Calls:' in line:
                    stats['total_calls'] = int(line.split(':')[1].strip())
                elif 'Success Rate:' in line:
                    stats['success_rate'] = float(line.split(':')[1].strip().replace('%', ''))
                elif 'Call Rate:' in line:
                    rate_str = line.split('~')[1].split(' ')[0]
                    stats['call_rate'] = float(rate_str)
            return stats
    except Exception as e:
        print(f"Error extracting stats: {e}")
    
    return None

def format_duration(seconds):
    """Format duration in human readable format"""
    hours = int(seconds // 3600)
    minutes = int((seconds % 3600) // 60)
    secs = int(seconds % 60)
    return f"{hours:02d}:{minutes:02d}:{secs:02d}"

def track_progress():
    """Track progress of the 3-hour monitoring run"""
    print("🔍 3-HOUR MONITORING PROGRESS TRACKER")
    print("=" * 50)
    
    start_time = datetime.now()
    target_duration = timedelta(hours=3)
    
    # Wait for log file to be created or find existing active session
    log_file = None
    print("⏳ Waiting for active monitoring session...")
    
    # First check if there's already an active session
    log_file = get_latest_log_file()
    if log_file:
        print(f"📄 Found active monitoring session: {log_file}")
        # Adjust start time based on log file creation time
        log_creation_time = datetime.fromtimestamp(os.path.getctime(log_file))
        elapsed_since_creation = start_time - log_creation_time
        if elapsed_since_creation.total_seconds() < 3600:  # Less than 1 hour old
            start_time = log_creation_time
            print(f"📅 Monitoring session started at: {start_time.strftime('%H:%M:%S')}")
        else:
            print(f"⚠️  Log file seems old, waiting for new session...")
            log_file = None
    
    # If no active session found, wait for one to start
    while not log_file:
        log_file = get_latest_log_file()
        if not log_file:
            print("   🔄 Checking for active monitoring session...")
            time.sleep(10)
        else:
            print(f"📄 Found new monitoring session: {log_file}")
            start_time = datetime.now()
    
    print(f"🚀 Tracking started at: {start_time.strftime('%H:%M:%S')}")
    print(f"🎯 Target completion: {(start_time + target_duration).strftime('%H:%M:%S')}")
    print("=" * 50)
    
    # Track progress every 10 minutes
    update_interval = 600  # 10 minutes
    last_update = time.time()
    
    while True:
        current_time = datetime.now()
        elapsed = current_time - start_time
        
        # Check if 3 hours have passed
        if elapsed >= target_duration:
            print("\n🏁 3-hour monitoring period completed!")
            break
        
        # Update every 10 minutes
        if time.time() - last_update >= update_interval:
            remaining = target_duration - elapsed
            progress_pct = (elapsed.total_seconds() / target_duration.total_seconds()) * 100
            
            print(f"\n⏰ Progress Update - {current_time.strftime('%H:%M:%S')}")
            print(f"   📊 Progress: {progress_pct:.1f}% complete")
            print(f"   ⏱️  Elapsed: {format_duration(elapsed.total_seconds())}")
            print(f"   ⏳ Remaining: {format_duration(remaining.total_seconds())}")
            
            # Get current API stats
            stats = extract_api_stats_from_log(log_file)
            if stats:
                print(f"   📞 API Calls: {stats.get('total_calls', 0)}")
                print(f"   ✅ Success Rate: {stats.get('success_rate', 0):.1f}%")
                print(f"   ⚡ Call Rate: {stats.get('call_rate', 0):.1f}/min")
            else:
                print("   📞 API Stats: Gathering data...")
            
            print("-" * 30)
            last_update = time.time()
        
        time.sleep(30)  # Check every 30 seconds
    
    # Final summary
    print("\n📊 FINAL 3-HOUR SUMMARY")
    print("=" * 50)
    final_stats = extract_api_stats_from_log(log_file)
    if final_stats:
        print(f"📞 Total API Calls: {final_stats.get('total_calls', 0)}")
        print(f"✅ Final Success Rate: {final_stats.get('success_rate', 0):.1f}%")
        print(f"⚡ Average Call Rate: {final_stats.get('call_rate', 0):.1f}/min")
        
        # Calculate calls per hour
        total_calls = final_stats.get('total_calls', 0)
        calls_per_hour = total_calls / 3
        print(f"📈 Calls per Hour: {calls_per_hour:.1f}")
    
    print("=" * 50)

if __name__ == "__main__":
    try:
        track_progress()
    except KeyboardInterrupt:
        print("\n⏹️  Progress tracking stopped by user")
    except Exception as e:
        print(f"\n❌ Error in progress tracking: {e}") 