#!/usr/bin/env python3
"""
6-Hour Test Progress Monitor
===========================

Monitor the progress of the running 6-hour cross-platform test
"""

import os
import json
import glob
from datetime import datetime
import time

def find_latest_log():
    """Find the most recent test log file"""
    log_files = glob.glob("../logs/cross_platform_6hour_test_*.log")
    if not log_files:
        return None
    return max(log_files, key=os.path.getctime)

def find_latest_results():
    """Find the most recent results files"""
    result_files = glob.glob("results/cross_platform_analysis_*.json")
    if not result_files:
        return []
    return sorted(result_files, key=os.path.getctime, reverse=True)[:5]  # Last 5 results

def parse_log_for_stats(log_file):
    """Parse log file for basic statistics"""
    if not os.path.exists(log_file):
        return None
    
    stats = {
        'total_runs': 0,
        'successful_runs': 0,
        'failed_runs': 0,
        'last_run_time': None,
        'test_start_time': None
    }
    
    try:
        with open(log_file, 'r') as f:
            for line in f:
                if 'Starting 6-hour cross-platform analyzer test' in line:
                    stats['test_start_time'] = line.split(' - ')[0]
                elif 'Starting analysis run #' in line:
                    run_num = int(line.split('#')[1].split()[0])
                    stats['total_runs'] = max(stats['total_runs'], run_num)
                elif 'completed in' in line and 'Run #' in line:
                    stats['successful_runs'] += 1
                    stats['last_run_time'] = line.split(' - ')[0]
                elif 'failed:' in line and 'Run #' in line:
                    stats['failed_runs'] += 1
    except Exception as e:
        print(f"Error parsing log: {e}")
    
    return stats

def analyze_recent_results(result_files):
    """Analyze recent result files"""
    if not result_files:
        return None
    
    analysis = {
        'total_tokens': 0,
        'high_conviction_tokens': 0,
        'total_cost_savings': 0.0,
        'avg_execution_time': 0.0,
        'cache_hit_rate': 0.0
    }
    
    valid_results = 0
    
    for result_file in result_files:
        try:
            with open(result_file, 'r') as f:
                data = json.load(f)
            
            if 'error' not in data:
                valid_results += 1
                analysis['total_tokens'] += data.get('correlations', {}).get('total_tokens', 0)
                analysis['high_conviction_tokens'] += len(data.get('correlations', {}).get('high_conviction_tokens', []))
                analysis['total_cost_savings'] += data.get('cache_statistics', {}).get('estimated_cost_savings_usd', 0.0)
                analysis['avg_execution_time'] += data.get('execution_time_seconds', 0.0)
                analysis['cache_hit_rate'] += data.get('cache_statistics', {}).get('hit_rate_percent', 0.0)
        
        except Exception as e:
            print(f"Error reading {result_file}: {e}")
    
    if valid_results > 0:
        analysis['avg_execution_time'] /= valid_results
        analysis['cache_hit_rate'] /= valid_results
    
    return analysis, valid_results

def main():
    """Main monitoring function"""
    print("🔍 6-Hour Cross-Platform Test Monitor")
    print("=" * 40)
    
    # Check if test is running
    log_file = find_latest_log()
    if not log_file:
        print("❌ No test log found. Is the test running?")
        return
    
    print(f"📝 Monitoring log: {os.path.basename(log_file)}")
    
    # Parse log statistics
    log_stats = parse_log_for_stats(log_file)
    if not log_stats:
        print("❌ Could not parse log file")
        return
    
    # Calculate elapsed time
    if log_stats['test_start_time']:
        try:
            start_time = datetime.strptime(log_stats['test_start_time'], '%Y-%m-%d %H:%M:%S,%f')
            elapsed = datetime.now() - start_time
            elapsed_hours = elapsed.total_seconds() / 3600
            remaining_hours = max(0, 6 - elapsed_hours)
        except:
            elapsed_hours = 0
            remaining_hours = 6
    else:
        elapsed_hours = 0
        remaining_hours = 6
    
    print(f"\n⏰ Time Progress:")
    print(f"   Elapsed: {elapsed_hours:.2f} hours")
    print(f"   Remaining: {remaining_hours:.2f} hours")
    print(f"   Progress: {(elapsed_hours/6)*100:.1f}%")
    
    print(f"\n🔄 Run Statistics:")
    print(f"   Total runs: {log_stats['total_runs']}")
    print(f"   Successful: {log_stats['successful_runs']}")
    print(f"   Failed: {log_stats['failed_runs']}")
    
    if log_stats['total_runs'] > 0:
        success_rate = (log_stats['successful_runs'] / log_stats['total_runs']) * 100
        print(f"   Success rate: {success_rate:.1f}%")
    
    if log_stats['last_run_time']:
        print(f"   Last run: {log_stats['last_run_time']}")
    
    # Analyze recent results
    result_files = find_latest_results()
    if result_files:
        analysis, valid_count = analyze_recent_results(result_files)
        
        print(f"\n📊 Recent Performance (last {valid_count} runs):")
        print(f"   Avg tokens per run: {analysis['total_tokens'] / max(1, valid_count):.1f}")
        print(f"   Total high-conviction: {analysis['high_conviction_tokens']}")
        print(f"   Avg execution time: {analysis['avg_execution_time']:.2f}s")
        print(f"   Cache hit rate: {analysis['cache_hit_rate']:.1f}%")
        print(f"   Total cost savings: ${analysis['total_cost_savings']:.4f}")
    
    # Expected completion
    if remaining_hours > 0:
        expected_completion = datetime.now().replace(microsecond=0) + \
                            datetime.timedelta(hours=remaining_hours).replace(microsecond=0)
        print(f"\n🎯 Expected completion: {expected_completion}")
    else:
        print(f"\n✅ Test should be completed!")
    
    print(f"\n📁 Results directory: scripts/results/")
    print(f"📝 Log file: {log_file}")

if __name__ == "__main__":
    main() 