#!/usr/bin/env python3
"""
Debug Session Dashboard - Real-time monitoring for 3-hour debug session

This dashboard provides comprehensive monitoring of:
- API call efficiency and batching statistics
- Token discovery and analysis performance
- Whale tracking effectiveness  
- System health and resource usage
"""

import time
import json
import subprocess
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Any
import re
import uuid
import psutil
from utils.structured_logger import get_structured_logger

class DebugSessionDashboard:
    def __init__(self):
        self.session_start = datetime.now()
        self.scan_id = str(uuid.uuid4())
        self.structured_logger = get_structured_logger('DebugSessionDashboard')
        self.log_file = Path("logs/virtuoso_gem_hunter.log")
        self.stats = {
            'api_calls': {
                'total': 0,
                'by_endpoint': {},
                'batched_calls': 0,
                'individual_calls': 0,
                'cache_hits': 0,
                'errors': 0
            },
            'token_discovery': {
                'cycles_completed': 0,
                'tokens_discovered': 0,
                'tokens_analyzed': 0,
                'promising_tokens': 0,
                'average_score': 0
            },
            'whale_tracking': {
                'whales_tracked': 0,
                'movements_detected': 0,
                'alerts_generated': 0,
                'total_value_tracked': 0
            },
            'performance': {
                'avg_cycle_time': 0,
                'api_efficiency': 0,
                'cache_hit_rate': 0,
                'memory_usage': 0
            }
        }
        
        # API call patterns
        self.api_patterns = {
            'request': re.compile(r'🔗 API Request: (.+)'),
            'success': re.compile(r'✅ Success: (.+?) - (.+)'),
            'batch': re.compile(r'BATCH|batch_|ultra_batch'),
            'cache_hit': re.compile(r'cache.*hit|hit.*cache', re.IGNORECASE),
            'error': re.compile(r'ERROR|error', re.IGNORECASE)
        }
        
        # Token discovery patterns
        self.discovery_patterns = {
            'cycle_start': re.compile(r'Starting.*token discovery'),
            'tokens_discovered': re.compile(r'Discovered (\d+) tokens'),
            'tokens_analyzed': re.compile(r'analyzed (\d+).*tokens', re.IGNORECASE),
            'final_score': re.compile(r'FINAL SCORE.*?(\d+\.?\d*)'),
            'promising_found': re.compile(r'(\d+) promising tokens')
        }
        
        # Whale tracking patterns
        self.whale_patterns = {
            'whale_movement': re.compile(r'🐋.*movement', re.IGNORECASE),
            'whale_alert': re.compile(r'whale.*alert', re.IGNORECASE),
            'tracking_stats': re.compile(r'tracked.*(\d+).*whales', re.IGNORECASE)
        }

    def parse_log_file(self):
        """Parse the log file for relevant statistics"""
        if not self.log_file.exists():
            return
        
        try:
            with open(self.log_file, 'r') as f:
                lines = f.readlines()
            
            # Process last 1000 lines for performance
            recent_lines = lines[-1000:] if len(lines) > 1000 else lines
            
            for line in recent_lines:
                self._process_log_line(line)
                
        except Exception as e:
            print(f"Error parsing log file: {e}")

    def _process_log_line(self, line: str):
        """Process a single log line for statistics"""
        # API call tracking
        if self.api_patterns['request'].search(line):
            self.stats['api_calls']['total'] += 1
            endpoint = self.api_patterns['request'].search(line).group(1)
            self.stats['api_calls']['by_endpoint'][endpoint] = \
                self.stats['api_calls']['by_endpoint'].get(endpoint, 0) + 1
            
            if self.api_patterns['batch'].search(line):
                self.stats['api_calls']['batched_calls'] += 1
            else:
                self.stats['api_calls']['individual_calls'] += 1
        
        # Success/Error tracking
        if self.api_patterns['success'].search(line):
            pass  # Success already counted in requests
        elif self.api_patterns['error'].search(line):
            self.stats['api_calls']['errors'] += 1
        
        # Cache hits
        if self.api_patterns['cache_hit'].search(line):
            self.stats['api_calls']['cache_hits'] += 1
        
        # Token discovery tracking
        if self.discovery_patterns['cycle_start'].search(line):
            self.stats['token_discovery']['cycles_completed'] += 1
        
        discovered_match = self.discovery_patterns['tokens_discovered'].search(line)
        if discovered_match:
            self.stats['token_discovery']['tokens_discovered'] += int(discovered_match.group(1))
        
        analyzed_match = self.discovery_patterns['tokens_analyzed'].search(line)
        if analyzed_match:
            self.stats['token_discovery']['tokens_analyzed'] += int(analyzed_match.group(1))
        
        promising_match = self.discovery_patterns['promising_found'].search(line)
        if promising_match:
            self.stats['token_discovery']['promising_tokens'] += int(promising_match.group(1))
        
        # Whale tracking
        if self.whale_patterns['whale_movement'].search(line):
            self.stats['whale_tracking']['movements_detected'] += 1
        
        if self.whale_patterns['whale_alert'].search(line):
            self.stats['whale_tracking']['alerts_generated'] += 1

    def calculate_performance_metrics(self):
        """Calculate derived performance metrics"""
        # API efficiency (batched vs individual)
        total_api_calls = self.stats['api_calls']['batched_calls'] + self.stats['api_calls']['individual_calls']
        if total_api_calls > 0:
            self.stats['performance']['api_efficiency'] = \
                (self.stats['api_calls']['batched_calls'] / total_api_calls) * 100
        
        # Cache hit rate
        total_attempts = self.stats['api_calls']['total'] + self.stats['api_calls']['cache_hits']
        if total_attempts > 0:
            self.stats['performance']['cache_hit_rate'] = \
                (self.stats['api_calls']['cache_hits'] / total_attempts) * 100
        
        # Average token scores (simplified)
        if self.stats['token_discovery']['tokens_analyzed'] > 0:
            self.stats['token_discovery']['average_score'] = \
                (self.stats['token_discovery']['promising_tokens'] / 
                 self.stats['token_discovery']['tokens_analyzed']) * 100

    def get_system_stats(self):
        """Get system resource usage"""
        try:
            # Get memory usage for Python processes
            result = subprocess.run(['ps', 'aux'], capture_output=True, text=True)
            lines = result.stdout.split('\n')
            
            python_memory = 0
            for line in lines:
                if 'python' in line.lower() and 'monitor' in line:
                    parts = line.split()
                    if len(parts) > 5:
                        try:
                            memory_kb = float(parts[5])
                            python_memory += memory_kb
                        except:
                            pass
            
            self.stats['performance']['memory_usage'] = python_memory / 1024  # Convert to MB
            
        except Exception as e:
            print(f"Error getting system stats: {e}")

    def print_dashboard(self):
        """Print the comprehensive dashboard"""
        self.structured_logger.info({
            "event": "dashboard_start",
            "scan_id": self.scan_id,
            "timestamp": int(time.time()),
            "cpu_percent": psutil.cpu_percent(),
            "memory_mb": psutil.virtual_memory().used // 1024 // 1024
        })
        self.parse_log_file()
        self.calculate_performance_metrics()
        self.get_system_stats()
        
        runtime = datetime.now() - self.session_start
        runtime_hours = runtime.total_seconds() / 3600
        
        print("\n" + "="*100)
        print("🔬 3-HOUR DEBUG SESSION DASHBOARD")
        print("="*100)
        print(f"⏰ Runtime: {runtime}")
        print(f"📊 Progress: {runtime_hours:.1f}/3.0 hours ({(runtime_hours/3)*100:.1f}%)")
        print(f"🎯 Session Target: API optimization & enhanced token discovery analysis")
        
        print("\n📡 API CALL STATISTICS:")
        print(f"  📤 Total API Calls: {self.stats['api_calls']['total']}")
        print(f"  🔄 Batched Calls: {self.stats['api_calls']['batched_calls']}")
        print(f"  🔸 Individual Calls: {self.stats['api_calls']['individual_calls']}")
        print(f"  💾 Cache Hits: {self.stats['api_calls']['cache_hits']}")
        print(f"  ❌ Errors: {self.stats['api_calls']['errors']}")
        print(f"  ⚡ API Efficiency: {self.stats['performance']['api_efficiency']:.1f}% batched")
        print(f"  🎯 Cache Hit Rate: {self.stats['performance']['cache_hit_rate']:.1f}%")
        
        print("\n🔍 TOKEN DISCOVERY PERFORMANCE:")
        print(f"  🔄 Discovery Cycles: {self.stats['token_discovery']['cycles_completed']}")
        print(f"  📦 Tokens Discovered: {self.stats['token_discovery']['tokens_discovered']}")
        print(f"  🔬 Tokens Analyzed: {self.stats['token_discovery']['tokens_analyzed']}")
        print(f"  ⭐ Promising Tokens: {self.stats['token_discovery']['promising_tokens']}")
        print(f"  📈 Success Rate: {self.stats['token_discovery']['average_score']:.1f}%")
        
        print("\n🐋 WHALE TRACKING STATUS:")
        print(f"  📊 Tracked Whales: {self.stats['whale_tracking']['whales_tracked']}")
        print(f"  🚀 Movements Detected: {self.stats['whale_tracking']['movements_detected']}")
        print(f"  🚨 Alerts Generated: {self.stats['whale_tracking']['alerts_generated']}")
        
        print("\n💻 SYSTEM PERFORMANCE:")
        print(f"  🧠 Memory Usage: {self.stats['performance']['memory_usage']:.1f} MB")
        print(f"  ⚡ Avg Cycle Time: {self.stats['performance']['avg_cycle_time']:.1f}s")
        
        # Top API endpoints
        if self.stats['api_calls']['by_endpoint']:
            print("\n📋 TOP API ENDPOINTS:")
            sorted_endpoints = sorted(
                self.stats['api_calls']['by_endpoint'].items(),
                key=lambda x: x[1], reverse=True
            )[:5]
            for endpoint, count in sorted_endpoints:
                print(f"  {endpoint}: {count} calls")
        
        # Expected vs Actual Performance
        expected_total_calls = runtime_hours * 200  # Rough estimate
        actual_calls = self.stats['api_calls']['total']
        if expected_total_calls > 0:
            efficiency_vs_expected = (1 - (actual_calls / expected_total_calls)) * 100
            print(f"\n🎯 OPTIMIZATION SUCCESS:")
            print(f"  Expected API calls (old system): ~{expected_total_calls:.0f}")
            print(f"  Actual API calls (optimized): {actual_calls}")
            print(f"  🚀 Reduction achieved: {efficiency_vs_expected:.1f}%")
        
        print("="*100)
        self.structured_logger.info({
            "event": "dashboard_end",
            "scan_id": self.scan_id,
            "timestamp": int(time.time()),
            "cpu_percent": psutil.cpu_percent(),
            "memory_mb": psutil.virtual_memory().used // 1024 // 1024
        })

    def run_dashboard(self, refresh_seconds: int = 30):
        """Run the dashboard with periodic updates"""
        print("🚀 Starting 3-Hour Debug Session Dashboard...")
        print("📊 Updates every 30 seconds | Press Ctrl+C to stop")
        
        try:
            while True:
                # Clear screen
                subprocess.run(['clear'], shell=True)
                
                # Print dashboard
                self.print_dashboard()
                
                # Check if 3 hours completed
                runtime = datetime.now() - self.session_start
                if runtime.total_seconds() >= 3 * 3600:  # 3 hours
                    print("\n🎉 3-HOUR DEBUG SESSION COMPLETED!")
                    break
                
                # Wait for next update
                time.sleep(refresh_seconds)
                
        except KeyboardInterrupt:
            print("\n\n👋 Dashboard stopped by user")

def main():
    dashboard = DebugSessionDashboard()
    dashboard.run_dashboard()

if __name__ == '__main__':
    main() 