#!/usr/bin/env python3

import os
import json
import time
from datetime import datetime, timedelta
import glob
import subprocess

def get_test_status():
    """Get the current status of the 6-hour test"""
    # Check if process is running
    try:
        result = subprocess.run(['pgrep', '-f', 'run_6hour_cross_platform_test'], 
                              capture_output=True, text=True)
        process_running = bool(result.stdout.strip())
        if result.stdout.strip():
            pid = result.stdout.strip()
        else:
            pid = None
    except:
        process_running = False
        pid = None
    
    # Check log file
    log_file = None
    if os.path.exists('../6hour_test.log'):
        log_file = '../6hour_test.log'
    else:
        # Look for log files in logs directory
        log_files = glob.glob('../logs/cross_platform_6hour_test_*.log')
        if log_files:
            log_file = max(log_files, key=os.path.getctime)
    
    # Get latest results
    result_files = glob.glob('results/cross_platform_analysis_*.json')
    latest_results = []
    if result_files:
        # Sort by modification time and get last 5
        result_files.sort(key=os.path.getctime, reverse=True)
        latest_results = result_files[:5]
    
    return {
        'process_running': process_running,
        'pid': pid,
        'log_file': log_file,
        'latest_results': latest_results
    }

def parse_log_stats(log_file):
    """Parse basic statistics from log file"""
    if not log_file or not os.path.exists(log_file):
        return {}
    
    stats = {
        'start_time': None,
        'end_time': None,
        'total_runs': 0,
        'successful_runs': 0,
        'failed_runs': 0,
        'last_activity': None,
        'errors': []
    }
    
    try:
        with open(log_file, 'r') as f:
            lines = f.readlines()
            
        for line in lines:
            if 'Starting 6-hour cross-platform analyzer test' in line:
                # Extract timestamp
                timestamp_str = line.split(' - ')[0]
                try:
                    stats['start_time'] = datetime.strptime(timestamp_str, '%Y-%m-%d %H:%M:%S,%f')
                except:
                    pass
            
            elif 'Starting analysis run #' in line:
                stats['total_runs'] += 1
                stats['last_activity'] = line.split(' - ')[0]
            
            elif '✅ Analysis completed' in line:
                stats['successful_runs'] += 1
            
            elif 'Analysis failed' in line or 'ERROR' in line:
                stats['failed_runs'] += 1
                if len(stats['errors']) < 5:  # Keep last 5 errors
                    stats['errors'].append(line.strip())
            
            elif 'Test completed' in line:
                timestamp_str = line.split(' - ')[0]
                try:
                    stats['end_time'] = datetime.strptime(timestamp_str, '%Y-%m-%d %H:%M:%S,%f')
                except:
                    pass
    
    except Exception as e:
        print(f"Error parsing log: {e}")
    
    return stats

def get_latest_results_summary(result_files):
    """Get summary from latest result files"""
    if not result_files:
        return {}
    
    summary = {
        'total_analyses': len(result_files),
        'latest_tokens': 0,
        'latest_high_conviction': 0,
        'latest_execution_time': 0,
        'cache_hit_rate': 0,
        'cost_savings': 0
    }
    
    try:
        # Parse latest result
        with open(result_files[0], 'r') as f:
            latest = json.load(f)
        
        if 'correlations' in latest:
            summary['latest_tokens'] = latest['correlations'].get('total_tokens', 0)
            summary['latest_high_conviction'] = len(latest['correlations'].get('high_conviction_tokens', []))
        
        summary['latest_execution_time'] = latest.get('execution_time_seconds', 0)
        
        if 'cache_statistics' in latest:
            cache_stats = latest['cache_statistics']
            summary['cache_hit_rate'] = cache_stats.get('hit_rate_percent', 0)
            summary['cost_savings'] = cache_stats.get('estimated_cost_savings_usd', 0)
    
    except Exception as e:
        print(f"Error parsing results: {e}")
    
    return summary

def print_status():
    """Print current test status"""
    print("\n🎯 6-Hour Cross-Platform Test Monitor")
    print("=" * 50)
    
    status = get_test_status()
    
    # Process status
    if status['process_running']:
        print(f"✅ Test is RUNNING (PID: {status['pid']})")
    else:
        print("❌ Test is NOT RUNNING")
    
    # Log analysis
    if status['log_file']:
        print(f"📝 Log file: {status['log_file']}")
        stats = parse_log_stats(status['log_file'])
        
        if stats['start_time']:
            print(f"⏰ Started: {stats['start_time'].strftime('%Y-%m-%d %H:%M:%S')}")
            
            # Calculate elapsed and remaining time
            now = datetime.now()
            elapsed = now - stats['start_time']
            remaining = timedelta(hours=6) - elapsed
            
            print(f"⏱️  Elapsed: {str(elapsed).split('.')[0]}")
            if remaining.total_seconds() > 0:
                print(f"⏳ Remaining: {str(remaining).split('.')[0]}")
            else:
                print("🏁 Test should be completed")
        
        print(f"🔄 Total runs: {stats['total_runs']}")
        print(f"✅ Successful: {stats['successful_runs']}")
        print(f"❌ Failed: {stats['failed_runs']}")
        
        if stats['errors']:
            print(f"⚠️  Recent errors: {len(stats['errors'])}")
    
    # Results summary
    if status['latest_results']:
        print(f"\n📊 Results: {len(status['latest_results'])} analysis files")
        summary = get_latest_results_summary(status['latest_results'])
        
        if summary:
            print(f"🪙 Latest tokens analyzed: {summary['latest_tokens']}")
            print(f"💎 High-conviction tokens: {summary['latest_high_conviction']}")
            print(f"⚡ Last execution time: {summary['latest_execution_time']:.1f}s")
            print(f"🚀 Cache hit rate: {summary['cache_hit_rate']:.1f}%")
            print(f"💰 Cost savings: ${summary['cost_savings']:.4f}")
    
    print(f"\n📁 Latest result files:")
    for i, file in enumerate(status['latest_results'][:3]):
        timestamp = os.path.basename(file).split('_')[-1].replace('.json', '')
        print(f"  {i+1}. {timestamp}")

def main():
    """Main monitoring function"""
    if len(os.sys.argv) > 1 and os.sys.argv[1] == '--watch':
        # Continuous monitoring mode
        try:
            while True:
                os.system('clear')  # Clear screen
                print_status()
                print(f"\n🔄 Refreshing every 30 seconds... (Ctrl+C to exit)")
                time.sleep(30)
        except KeyboardInterrupt:
            print("\n👋 Monitoring stopped")
    else:
        # Single status check
        print_status()

if __name__ == "__main__":
    main() 