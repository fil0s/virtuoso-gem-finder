#!/usr/bin/env python3
"""
API Call Monitor - Real-time monitoring of BirdEye API calls

This script monitors the virtuoso_gem_hunter.log file and provides real-time
statistics about API calls, rate limiting, and performance metrics.
"""

import re
import time
import argparse
from collections import defaultdict, Counter
from datetime import datetime, timedelta
from pathlib import Path

class APICallMonitor:
    def __init__(self, log_file_path: str):
        self.log_file_path = Path(log_file_path)
        self.api_calls = []
        self.api_stats = defaultdict(int)
        self.rate_limit_info = {}
        self.start_time = datetime.now()
        
        # Regex patterns for parsing log entries
        self.api_request_pattern = re.compile(
            r'(\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2},\d{3}).*API Request: (.+?)$'
        )
        self.api_success_pattern = re.compile(
            r'(\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2},\d{3}).*✅ Success: (.+?) - (.+?)$'
        )
        self.rate_limit_pattern = re.compile(
            r"'x-ratelimit-remaining': '(\d+)', 'x-ratelimit-reset': '(\d+)'"
        )
        
    def parse_timestamp(self, timestamp_str: str) -> datetime:
        """Parse timestamp from log entry"""
        return datetime.strptime(timestamp_str, '%Y-%m-%d %H:%M:%S,%f')
    
    def monitor_file(self, follow: bool = True, show_details: bool = False):
        """Monitor log file for API calls"""
        print(f"🔍 Monitoring API calls from: {self.log_file_path}")
        print(f"⏰ Started at: {self.start_time.strftime('%Y-%m-%d %H:%M:%S')}")
        print("=" * 80)
        
        if not self.log_file_path.exists():
            print(f"❌ Log file not found: {self.log_file_path}")
            return
        
        # Read existing content first
        with open(self.log_file_path, 'r') as f:
            content = f.read()
            self._process_content(content, show_details)
        
        if follow:
            self._follow_file(show_details)
    
    def _process_content(self, content: str, show_details: bool = False):
        """Process log content for API calls"""
        lines = content.split('\n')
        
        for line in lines:
            self._process_line(line, show_details)
    
    def _process_line(self, line: str, show_details: bool = False):
        """Process a single log line"""
        # Check for API requests
        api_request_match = self.api_request_pattern.search(line)
        if api_request_match:
            timestamp_str, endpoint = api_request_match.groups()
            timestamp = self.parse_timestamp(timestamp_str)
            
            self.api_calls.append({
                'timestamp': timestamp,
                'type': 'request',
                'endpoint': endpoint,
                'line': line
            })
            self.api_stats[f"request_{endpoint}"] += 1
            
            if show_details:
                print(f"📤 {timestamp.strftime('%H:%M:%S')} - Request: {endpoint}")
        
        # Check for API success responses
        api_success_match = self.api_success_pattern.search(line)
        if api_success_match:
            timestamp_str, endpoint, response_info = api_success_match.groups()
            timestamp = self.parse_timestamp(timestamp_str)
            
            self.api_calls.append({
                'timestamp': timestamp,
                'type': 'success',
                'endpoint': endpoint,
                'response_info': response_info,
                'line': line
            })
            self.api_stats[f"success_{endpoint}"] += 1
            
            if show_details:
                print(f"✅ {timestamp.strftime('%H:%M:%S')} - Success: {endpoint} - {response_info}")
        
        # Check for rate limit info
        rate_limit_match = self.rate_limit_pattern.search(line)
        if rate_limit_match:
            remaining, reset_time = rate_limit_match.groups()
            self.rate_limit_info = {
                'remaining': int(remaining),
                'reset_time': int(reset_time),
                'timestamp': datetime.now()
            }
    
    def _follow_file(self, show_details: bool = False):
        """Follow log file for new entries"""
        with open(self.log_file_path, 'r') as f:
            f.seek(0, 2)  # Go to end of file
            
            while True:
                line = f.readline()
                if line:
                    self._process_line(line, show_details)
                else:
                    time.sleep(0.5)  # Wait before checking again
    
    def print_statistics(self):
        """Print current API call statistics"""
        current_time = datetime.now()
        runtime = current_time - self.start_time
        
        # Count different types of calls
        total_requests = sum(1 for call in self.api_calls if call['type'] == 'request')
        total_successes = sum(1 for call in self.api_calls if call['type'] == 'success')
        
        # Count by endpoint
        endpoint_counts = Counter()
        for call in self.api_calls:
            if call['type'] == 'request':
                endpoint_counts[call['endpoint']] += 1
        
        # Recent activity (last 5 minutes)
        recent_cutoff = current_time - timedelta(minutes=5)
        recent_calls = [call for call in self.api_calls if call['timestamp'] > recent_cutoff]
        
        print("\n" + "=" * 80)
        print("📊 API CALL STATISTICS")
        print("=" * 80)
        print(f"⏰ Runtime: {runtime}")
        print(f"📤 Total Requests: {total_requests}")
        print(f"✅ Total Successes: {total_successes}")
        print(f"📈 Success Rate: {(total_successes/total_requests*100):.1f}%" if total_requests > 0 else "N/A")
        print(f"🔥 Recent Activity (5m): {len(recent_calls)} calls")
        
        if self.rate_limit_info:
            print(f"🚦 Rate Limit Remaining: {self.rate_limit_info['remaining']}")
        
        print("\n📋 CALLS BY ENDPOINT:")
        for endpoint, count in endpoint_counts.most_common():
            print(f"  {endpoint}: {count}")
        
        # Calculate calls per minute
        if runtime.total_seconds() > 60:
            calls_per_minute = total_requests / (runtime.total_seconds() / 60)
            print(f"\n⚡ Average Rate: {calls_per_minute:.2f} calls/minute")
        
        print("=" * 80)

def main():
    parser = argparse.ArgumentParser(description='Monitor API calls from early token monitor')
    parser.add_argument('--log-file', '-f', 
                       default='logs/virtuoso_gem_hunter.log',
                       help='Path to log file to monitor')
    parser.add_argument('--follow', '-F', action='store_true',
                       help='Follow log file for new entries')
    parser.add_argument('--details', '-d', action='store_true',
                       help='Show detailed API call information')
    parser.add_argument('--stats-interval', '-i', type=int, default=60,
                       help='Print statistics every N seconds (default: 60)')
    
    args = parser.parse_args()
    
    monitor = APICallMonitor(args.log_file)
    
    if args.follow:
        # Start monitoring in background and print stats periodically
        import threading
        
        def monitor_thread():
            monitor.monitor_file(follow=True, show_details=args.details)
        
        # Start monitoring thread
        monitor_thread = threading.Thread(target=monitor_thread, daemon=True)
        monitor_thread.start()
        
        # Print stats periodically
        try:
            while True:
                monitor.print_statistics()
                time.sleep(args.stats_interval)
        except KeyboardInterrupt:
            print("\n\n👋 Monitoring stopped by user")
    else:
        # Just analyze existing log content
        monitor.monitor_file(follow=False, show_details=args.details)
        monitor.print_statistics()

if __name__ == '__main__':
    main() 