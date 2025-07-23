#!/usr/bin/env python3
"""
Real-time Performance Monitor for Early Token Detection System
Tracks API calls, response times, success rates, and system performance during sustained testing.
"""

import time
import json
import re
import os
from datetime import datetime, timedelta
from collections import defaultdict, deque
from typing import Dict, List, Any
import argparse

class PerformanceMonitor:
    def __init__(self, log_file: str = "logs/virtuoso_gem_hunter.log"):
        self.log_file = log_file
        self.start_time = time.time()
        self.metrics = {
            'api_calls': defaultdict(int),
            'response_times': defaultdict(list),
            'success_count': 0,
            'error_count': 0,
            'tokens_analyzed': 0,
            'tokens_discovered': 0,
            'cache_hits': 0,
            'cache_misses': 0,
            'endpoints_used': defaultdict(int),
            'hourly_stats': defaultdict(lambda: defaultdict(int)),
            'recent_calls': deque(maxlen=100)  # Last 100 API calls
        }
        self.last_position = 0
        
    def parse_log_line(self, line: str) -> Dict[str, Any]:
        """Parse a log line and extract relevant metrics"""
        try:
            # Look for API call events
            if '"event": "api_call"' in line:
                # Extract JSON from log line
                json_start = line.find('{"')
                if json_start != -1:
                    json_str = line[json_start:]
                    data = json.loads(json_str)
                    return {
                        'type': 'api_call',
                        'endpoint': data.get('endpoint', ''),
                        'response_time': data.get('response_time_ms', 0),
                        'status_code': data.get('status_code', 0),
                        'result': data.get('result', ''),
                        'timestamp': data.get('asctime', '')
                    }
            
            # Look for cache events
            elif '"event": "cache_get"' in line:
                json_start = line.find('{"')
                if json_start != -1:
                    json_str = line[json_start:]
                    data = json.loads(json_str)
                    return {
                        'type': 'cache',
                        'result': data.get('result', ''),
                        'timestamp': data.get('asctime', '')
                    }
            
            # Look for scan metrics
            elif '"event": "scan_metrics"' in line:
                json_start = line.find('{"')
                if json_start != -1:
                    json_str = line[json_start:]
                    data = json.loads(json_str)
                    return {
                        'type': 'scan_metrics',
                        'tokens_discovered': data.get('tokens_discovered', 0),
                        'tokens_analyzed': data.get('tokens_analyzed', 0),
                        'promising_tokens': data.get('promising_tokens', 0),
                        'api_calls_this_cycle': data.get('api_calls_this_cycle', 0),
                        'timestamp': data.get('asctime', '')
                    }
                    
        except (json.JSONDecodeError, KeyError):
            pass
            
        return {}
    
    def update_metrics(self, parsed_data: Dict[str, Any]):
        """Update metrics based on parsed log data"""
        if parsed_data.get('type') == 'api_call':
            endpoint = parsed_data['endpoint']
            response_time = parsed_data['response_time']
            status_code = parsed_data['status_code']
            result = parsed_data['result']
            
            # Update API call counts
            self.metrics['api_calls'][endpoint] += 1
            self.metrics['endpoints_used'][endpoint] += 1
            
            # Track response times
            self.metrics['response_times'][endpoint].append(response_time)
            
            # Track success/error rates
            if result == 'success' and 200 <= status_code < 300:
                self.metrics['success_count'] += 1
            else:
                self.metrics['error_count'] += 1
            
            # Add to recent calls
            self.metrics['recent_calls'].append({
                'endpoint': endpoint,
                'response_time': response_time,
                'status_code': status_code,
                'result': result,
                'timestamp': time.time()
            })
            
            # Update hourly stats
            hour = datetime.now().hour
            self.metrics['hourly_stats'][hour]['api_calls'] += 1
            self.metrics['hourly_stats'][hour]['total_response_time'] += response_time
            
        elif parsed_data.get('type') == 'cache':
            if parsed_data['result'] == 'hit':
                self.metrics['cache_hits'] += 1
            else:
                self.metrics['cache_misses'] += 1
                
        elif parsed_data.get('type') == 'scan_metrics':
            self.metrics['tokens_discovered'] = parsed_data['tokens_discovered']
            self.metrics['tokens_analyzed'] = parsed_data['tokens_analyzed']
    
    def read_new_logs(self):
        """Read new log entries since last check"""
        try:
            with open(self.log_file, 'r') as f:
                f.seek(self.last_position)
                new_lines = f.readlines()
                self.last_position = f.tell()
                
                for line in new_lines:
                    parsed = self.parse_log_line(line)
                    if parsed:
                        self.update_metrics(parsed)
                        
        except FileNotFoundError:
            print(f"Log file {self.log_file} not found")
        except Exception as e:
            print(f"Error reading log file: {e}")
    
    def calculate_stats(self) -> Dict[str, Any]:
        """Calculate comprehensive performance statistics"""
        runtime = time.time() - self.start_time
        total_calls = self.metrics['success_count'] + self.metrics['error_count']
        
        # Calculate average response times per endpoint
        avg_response_times = {}
        for endpoint, times in self.metrics['response_times'].items():
            if times:
                avg_response_times[endpoint] = sum(times) / len(times)
        
        # Calculate success rate
        success_rate = (self.metrics['success_count'] / total_calls * 100) if total_calls > 0 else 0
        
        # Calculate calls per minute
        calls_per_minute = (total_calls / runtime * 60) if runtime > 0 else 0
        
        # Calculate cache hit rate
        total_cache_ops = self.metrics['cache_hits'] + self.metrics['cache_misses']
        cache_hit_rate = (self.metrics['cache_hits'] / total_cache_ops * 100) if total_cache_ops > 0 else 0
        
        # Get recent performance (last 10 calls)
        recent_calls = list(self.metrics['recent_calls'])[-10:]
        recent_avg_response = sum(call['response_time'] for call in recent_calls) / len(recent_calls) if recent_calls else 0
        
        return {
            'runtime_seconds': runtime,
            'runtime_minutes': runtime / 60,
            'total_api_calls': total_calls,
            'successful_calls': self.metrics['success_count'],
            'failed_calls': self.metrics['error_count'],
            'success_rate_percent': success_rate,
            'calls_per_minute': calls_per_minute,
            'cache_hits': self.metrics['cache_hits'],
            'cache_misses': self.metrics['cache_misses'],
            'cache_hit_rate_percent': cache_hit_rate,
            'tokens_discovered': self.metrics['tokens_discovered'],
            'tokens_analyzed': self.metrics['tokens_analyzed'],
            'avg_response_times': avg_response_times,
            'recent_avg_response_ms': recent_avg_response,
            'endpoints_used': dict(self.metrics['endpoints_used']),
            'hourly_breakdown': dict(self.metrics['hourly_stats'])
        }
    
    def print_dashboard(self):
        """Print a real-time performance dashboard"""
        stats = self.calculate_stats()
        
        print("\n" + "="*80)
        print("🚀 VIRTUOSO GEM HUNTER - REAL-TIME PERFORMANCE DASHBOARD")
        print("="*80)
        
        print(f"⏱️  Runtime: {stats['runtime_minutes']:.1f} minutes")
        print(f"📞 Total API Calls: {stats['total_api_calls']}")
        print(f"✅ Success Rate: {stats['success_rate_percent']:.1f}% ({stats['successful_calls']}/{stats['total_api_calls']})")
        print(f"⚡ Call Rate: {stats['calls_per_minute']:.1f} calls/minute")
        print(f"⏱️  Recent Avg Response: {stats['recent_avg_response_ms']:.0f}ms")
        
        print(f"\n🎯 CACHE PERFORMANCE:")
        print(f"   Hit Rate: {stats['cache_hit_rate_percent']:.1f}% ({stats['cache_hits']}/{stats['cache_hits'] + stats['cache_misses']})")
        
        print(f"\n🔍 TOKEN ANALYSIS:")
        print(f"   Discovered: {stats['tokens_discovered']}")
        print(f"   Analyzed: {stats['tokens_analyzed']}")
        
        print(f"\n📊 TOP ENDPOINTS BY USAGE:")
        sorted_endpoints = sorted(stats['endpoints_used'].items(), key=lambda x: x[1], reverse=True)
        for endpoint, count in sorted_endpoints[:5]:
            avg_time = stats['avg_response_times'].get(endpoint, 0)
            print(f"   {endpoint}: {count} calls (avg: {avg_time:.0f}ms)")
        
        print(f"\n⏰ HOURLY BREAKDOWN:")
        current_hour = datetime.now().hour
        for hour in range(max(0, current_hour-2), current_hour+1):
            if hour in stats['hourly_breakdown']:
                hour_stats = stats['hourly_breakdown'][hour]
                calls = hour_stats.get('api_calls', 0)
                total_time = hour_stats.get('total_response_time', 0)
                avg_time = total_time / calls if calls > 0 else 0
                print(f"   {hour:02d}:00 - {calls} calls (avg: {avg_time:.0f}ms)")
        
        print("="*80)
    
    def save_analytics_report(self, output_file: str):
        """Save comprehensive analytics report to file"""
        stats = self.calculate_stats()
        
        report = {
            'test_session': {
                'start_time': datetime.fromtimestamp(self.start_time).isoformat(),
                'end_time': datetime.now().isoformat(),
                'duration_minutes': stats['runtime_minutes']
            },
            'performance_metrics': stats,
            'detailed_endpoint_analysis': {},
            'recommendations': []
        }
        
        # Detailed endpoint analysis
        for endpoint, times in self.metrics['response_times'].items():
            if times:
                report['detailed_endpoint_analysis'][endpoint] = {
                    'total_calls': len(times),
                    'avg_response_ms': sum(times) / len(times),
                    'min_response_ms': min(times),
                    'max_response_ms': max(times),
                    'p95_response_ms': sorted(times)[int(len(times) * 0.95)] if len(times) > 20 else max(times)
                }
        
        # Generate recommendations
        if stats['success_rate_percent'] < 95:
            report['recommendations'].append("Consider investigating API failures - success rate below 95%")
        
        if stats['recent_avg_response_ms'] > 1000:
            report['recommendations'].append("Recent response times are high - consider optimizing API calls")
        
        if stats['cache_hit_rate_percent'] < 30:
            report['recommendations'].append("Low cache hit rate - consider adjusting cache TTL settings")
        
        with open(output_file, 'w') as f:
            json.dump(report, f, indent=2)
        
        print(f"\n📊 Analytics report saved to: {output_file}")

def main():
    parser = argparse.ArgumentParser(description='Monitor Early Token Detection System Performance')
    parser.add_argument('--log-file', default='logs/virtuoso_gem_hunter.log', help='Path to log file')
    parser.add_argument('--interval', type=int, default=30, help='Update interval in seconds')
    parser.add_argument('--duration', type=int, default=1800, help='Total monitoring duration in seconds')
    parser.add_argument('--output', help='Output file for analytics report')
    
    args = parser.parse_args()
    
    monitor = PerformanceMonitor(args.log_file)
    
    print("🚀 Starting Performance Monitor...")
    print(f"📊 Monitoring: {args.log_file}")
    print(f"⏱️  Update interval: {args.interval} seconds")
    print(f"🕐 Duration: {args.duration / 60:.1f} minutes")
    
    start_time = time.time()
    
    try:
        while time.time() - start_time < args.duration:
            monitor.read_new_logs()
            monitor.print_dashboard()
            time.sleep(args.interval)
            
    except KeyboardInterrupt:
        print("\n⏹️  Monitoring stopped by user")
    
    # Generate final report
    if args.output:
        monitor.save_analytics_report(args.output)
    else:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_file = f"scripts/analysis/performance_report_{timestamp}.json"
        monitor.save_analytics_report(output_file)

if __name__ == "__main__":
    main() 