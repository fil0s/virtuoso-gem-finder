#!/usr/bin/env python3
"""
Monitor the 1-hour High Conviction Detector session
Shows real-time progress and results
"""

import os
import time
import json
import glob
from datetime import datetime, timedelta
import subprocess

def get_latest_session_file():
    """Get the most recent session results file"""
    pattern = "data/session_results_*.json"
    files = glob.glob(pattern)
    if not files:
        return None
    return max(files, key=os.path.getctime)

def check_process_status():
    """Check if the detector process is still running"""
    try:
        # Check for python processes running the detector
        result = subprocess.run(['pgrep', '-f', 'run_1hour_6scans_detector'], 
                              capture_output=True, text=True)
        return len(result.stdout.strip().split('\n')) > 0 if result.stdout.strip() else False
    except:
        return False

def display_session_progress():
    """Display current session progress"""
    print("🎯 HIGH CONVICTION DETECTOR - 1 HOUR SESSION MONITOR")
    print("=" * 60)
    
    # Check if process is running
    is_running = check_process_status()
    print(f"📊 Process Status: {'🟢 RUNNING' if is_running else '🔴 STOPPED'}")
    
    # Check for session results
    session_file = get_latest_session_file()
    
    if session_file:
        try:
            with open(session_file, 'r') as f:
                session_data = json.load(f)
            
            print(f"📁 Session File: {session_file}")
            
            # Parse session info
            start_time = datetime.fromisoformat(session_data['start_time'])
            end_time_str = session_data.get('end_time')
            
            print(f"🕐 Start Time: {start_time.strftime('%H:%M:%S')}")
            
            if end_time_str:
                end_time = datetime.fromisoformat(end_time_str)
                duration = end_time - start_time
                print(f"🕑 End Time: {end_time.strftime('%H:%M:%S')}")
                print(f"⏰ Total Duration: {duration}")
                print(f"✅ SESSION COMPLETED")
            else:
                current_time = datetime.now()
                elapsed = current_time - start_time
                remaining = timedelta(hours=1) - elapsed
                
                print(f"🕐 Current Time: {current_time.strftime('%H:%M:%S')}")
                print(f"⏰ Elapsed: {elapsed}")
                print(f"⏳ Remaining: {remaining}")
                
                if remaining.total_seconds() <= 0:
                    print(f"⏰ SESSION TIME EXPIRED")
            
            # Show scan progress
            total_scans = session_data.get('total_scans', 0)
            successful_scans = session_data.get('successful_scans', 0)
            failed_scans = session_data.get('failed_scans', 0)
            
            print(f"\n🔍 SCAN PROGRESS:")
            print(f"  Total Scans: {total_scans}/6")
            print(f"  Successful: {successful_scans}")
            print(f"  Failed: {failed_scans}")
            
            if total_scans > 0:
                progress = (total_scans / 6) * 100
                print(f"  Progress: {progress:.1f}%")
            
            # Show results
            tokens_analyzed = session_data.get('total_tokens_analyzed', 0)
            candidates = session_data.get('high_conviction_candidates', 0)
            alerts = session_data.get('alerts_sent', 0)
            
            print(f"\n📈 RESULTS SO FAR:")
            print(f"  Tokens Analyzed: {tokens_analyzed}")
            print(f"  High Conviction Candidates: {candidates}")
            print(f"  Alerts Sent: {alerts}")
            
            # Show recent scans
            scan_results = session_data.get('scan_results', [])
            if scan_results:
                print(f"\n📋 RECENT SCANS:")
                for scan in scan_results[-3:]:  # Show last 3 scans
                    scan_num = scan['scan_number']
                    status = scan['status']
                    timestamp = datetime.fromisoformat(scan['timestamp']).strftime('%H:%M:%S')
                    
                    if status == "completed":
                        tokens = scan['tokens_analyzed']
                        candidates = scan['candidates_found']
                        alerts = scan['alerts_sent']
                        print(f"  Scan #{scan_num} ({timestamp}): ✅ {tokens} tokens, {candidates} candidates, {alerts} alerts")
                    elif status == "no_high_conviction":
                        tokens = scan['tokens_analyzed']
                        print(f"  Scan #{scan_num} ({timestamp}): 📊 {tokens} tokens, no candidates")
                    elif status == "no_results":
                        print(f"  Scan #{scan_num} ({timestamp}): 📊 No results")
                    elif status == "failed":
                        error = scan.get('error', 'Unknown')
                        print(f"  Scan #{scan_num} ({timestamp}): ❌ Failed - {error[:50]}...")
            
        except Exception as e:
            print(f"❌ Error reading session file: {e}")
    else:
        print("📁 No session results file found yet")
        print("⏳ Session may still be starting up...")
    
    print("=" * 60)

def main():
    """Main monitoring loop"""
    print("🚀 Starting High Conviction Detector Session Monitor")
    print("Press Ctrl+C to stop monitoring\n")
    
    try:
        while True:
            os.system('clear' if os.name == 'posix' else 'cls')  # Clear screen
            display_session_progress()
            
            # Check if session is complete
            session_file = get_latest_session_file()
            if session_file:
                try:
                    with open(session_file, 'r') as f:
                        session_data = json.load(f)
                    
                    if session_data.get('end_time'):
                        print("\n✅ Session completed! Final results shown above.")
                        break
                except:
                    pass
            
            print("\n🔄 Refreshing in 30 seconds... (Ctrl+C to stop)")
            time.sleep(30)
            
    except KeyboardInterrupt:
        print("\n⌨️ Monitoring stopped by user")

if __name__ == "__main__":
    main() 