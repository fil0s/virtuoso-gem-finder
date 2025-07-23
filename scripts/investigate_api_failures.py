#!/usr/bin/env python3
"""
Comprehensive API Failure Investigation Script
Analyzes all API failures from recent scans to identify root causes
"""

import json
import re
from datetime import datetime, timedelta
from collections import defaultdict, Counter
import sys
import os

# Add current directory to path
sys.path.append(os.getcwd())

def analyze_log_failures():
    """Analyze failures from log file"""
    
    print("🔍 COMPREHENSIVE API FAILURE ANALYSIS")
    print("=" * 60)
    
    # Read recent log entries
    log_file = "logs/virtuoso_gem_hunter.log"
    
    if not os.path.exists(log_file):
        print(f"❌ Log file not found: {log_file}")
        return
    
    # Analyze last 24 hours of logs
    cutoff_time = datetime.now() - timedelta(hours=24)
    
    failures = {
        'birdeye': [],
        'jupiter': [],
        'dexscreener': [],
        'rugcheck': [],
        'meteora': [],
        'general': []
    }
    
    error_patterns = {
        'api_error_400': r'API Error 400.*?for (.*?): (.*?)$',
        'connection_timeout': r'Connection timeout to host (.*?)$',
        'client_error': r'Client error for (.*?): (.*?)$',
        'invalid_format': r'list_address is invalid format',
        'http_error': r'HTTP ([45]\d{2})',
        'api_error_general': r'API Error for (.*?): (\d+) - (.*?)$'
    }
    
    with open(log_file, 'r') as f:
        lines = f.readlines()
    
    # Parse failures
    for line in lines:
        # Skip old entries (simple timestamp check)
        if '2025-06-23' not in line:
            continue
            
        line = line.strip()
        
        # Check for each error pattern
        for error_type, pattern in error_patterns.items():
            match = re.search(pattern, line)
            if match:
                failure_info = {
                    'type': error_type,
                    'line': line,
                    'timestamp': extract_timestamp(line),
                    'match': match.groups() if match.groups() else []
                }
                
                # Categorize by API
                if 'birdeye' in line.lower() or 'birdeye' in str(match.groups()).lower():
                    failures['birdeye'].append(failure_info)
                elif 'jupiter' in line.lower():
                    failures['jupiter'].append(failure_info)
                elif 'dexscreener' in line.lower():
                    failures['dexscreener'].append(failure_info)
                elif 'rugcheck' in line.lower():
                    failures['rugcheck'].append(failure_info)
                elif 'meteora' in line.lower():
                    failures['meteora'].append(failure_info)
                else:
                    failures['general'].append(failure_info)
                break
    
    # Display analysis
    total_failures = sum(len(fails) for fails in failures.values())
    print(f"📊 TOTAL FAILURES FOUND: {total_failures}")
    print()
    
    for api, api_failures in failures.items():
        if api_failures:
            print(f"🔴 {api.upper()} FAILURES ({len(api_failures)}):")
            print("-" * 40)
            
            # Group by error type
            error_counts = Counter(f['type'] for f in api_failures)
            for error_type, count in error_counts.most_common():
                print(f"  • {error_type}: {count} occurrences")
            
            print()
            
            # Show recent examples
            print(f"📋 Recent {api.upper()} Failure Examples:")
            for i, failure in enumerate(api_failures[-3:], 1):  # Last 3
                print(f"  {i}. {failure['type']}")
                if failure['match']:
                    print(f"     Details: {failure['match']}")
                print(f"     Time: {failure['timestamp']}")
                print()
    
    return failures

def analyze_birdeye_specific_issues(failures):
    """Deep dive into Birdeye-specific issues"""
    
    print("🐦 BIRDEYE DEEP DIVE ANALYSIS")
    print("=" * 60)
    
    birdeye_failures = failures.get('birdeye', [])
    
    if not birdeye_failures:
        print("✅ No Birdeye failures found")
        return
    
    # Analyze specific issues
    issues = {
        'invalid_address_format': 0,
        'connection_timeouts': 0,
        'http_400_errors': 0,
        'batch_request_issues': 0
    }
    
    problematic_endpoints = Counter()
    timeout_patterns = []
    
    for failure in birdeye_failures:
        failure_line = failure['line']
        
        # Check for specific issues
        if 'list_address is invalid format' in failure_line:
            issues['invalid_address_format'] += 1
            
        if 'Connection timeout' in failure_line:
            issues['connection_timeouts'] += 1
            # Extract URL for pattern analysis
            url_match = re.search(r'https://[^\s]+', failure_line)
            if url_match:
                timeout_patterns.append(url_match.group())
                
        if 'API Error 400' in failure_line:
            issues['http_400_errors'] += 1
            # Extract endpoint
            endpoint_match = re.search(r'for (/[^:]+):', failure_line)
            if endpoint_match:
                problematic_endpoints[endpoint_match.group(1)] += 1
                
        if 'multi_price' in failure_line:
            issues['batch_request_issues'] += 1
    
    print("📊 ISSUE BREAKDOWN:")
    for issue, count in issues.items():
        if count > 0:
            print(f"  • {issue.replace('_', ' ').title()}: {count}")
    
    print()
    
    if problematic_endpoints:
        print("🎯 MOST PROBLEMATIC ENDPOINTS:")
        for endpoint, count in problematic_endpoints.most_common(5):
            print(f"  • {endpoint}: {count} failures")
        print()
    
    # Analyze timeout patterns
    if timeout_patterns:
        print("⏰ TIMEOUT PATTERN ANALYSIS:")
        
        # Extract token counts from URLs
        token_counts = []
        for url in timeout_patterns:
            # Count tokens in list_address parameter
            if 'list_address=' in url:
                address_part = url.split('list_address=')[1].split('&')[0]
                token_count = len(address_part.split(','))
                token_counts.append(token_count)
        
        if token_counts:
            avg_tokens = sum(token_counts) / len(token_counts)
            max_tokens = max(token_counts)
            print(f"  • Average tokens per failed batch: {avg_tokens:.1f}")
            print(f"  • Maximum tokens in failed batch: {max_tokens}")
            print(f"  • Total timeout incidents: {len(timeout_patterns)}")
        
        print()
        
        # Show example URLs (truncated)
        print("📋 EXAMPLE TIMEOUT URLs:")
        for i, url in enumerate(timeout_patterns[:3], 1):
            # Truncate long URLs
            if len(url) > 100:
                url_display = url[:97] + "..."
            else:
                url_display = url
            print(f"  {i}. {url_display}")
        print()

def analyze_jupiter_performance(failures):
    """Analyze Jupiter API performance"""
    
    print("🪙 JUPITER PERFORMANCE ANALYSIS")
    print("=" * 60)
    
    jupiter_failures = failures.get('jupiter', [])
    
    if not jupiter_failures:
        print("✅ No Jupiter failures found in logs")
        print("📊 Jupiter appears to be performing well")
        return
    
    print(f"🔴 Jupiter failures found: {len(jupiter_failures)}")
    
    # Analyze failure patterns
    for failure in jupiter_failures:
        print(f"  • {failure['type']}: {failure['timestamp']}")
        if failure['match']:
            print(f"    Details: {failure['match']}")

def analyze_success_rates_from_scan_output():
    """Analyze success rates from recent scan output"""
    
    print("📈 SUCCESS RATE ANALYSIS FROM SCAN OUTPUT")
    print("=" * 60)
    
    # This data comes from the scan output you provided
    api_stats = {
        'birdeye': {'total': 9, 'success_rate': 88.9},
        'dexscreener': {'total': 17, 'success_rate': None},  # Not specified
        'rugcheck': {'total': 1, 'success_rate': None},      # Not specified  
        'jupiter': {'total': 52, 'success_rate': 88.5},
        'meteora': {'total': 1, 'success_rate': None}        # Not specified
    }
    
    print("📊 API PERFORMANCE SUMMARY:")
    for api, stats in api_stats.items():
        total = stats['total']
        success_rate = stats['success_rate']
        
        if success_rate is not None:
            failed = round(total * (1 - success_rate/100))
            success_count = total - failed
            print(f"  • {api.title()}: {success_count}/{total} successful ({success_rate}%) - {failed} failed")
        else:
            print(f"  • {api.title()}: {total} calls (success rate not specified)")
    
    print()
    
    # Calculate overall stats
    total_calls = sum(stats['total'] for stats in api_stats.values())
    known_success_apis = {k: v for k, v in api_stats.items() if v['success_rate'] is not None}
    
    if known_success_apis:
        weighted_success = sum(
            stats['total'] * stats['success_rate'] 
            for stats in known_success_apis.values()
        )
        total_known_calls = sum(stats['total'] for stats in known_success_apis.values())
        overall_success_rate = weighted_success / total_known_calls
        
        print(f"🎯 OVERALL PERFORMANCE:")
        print(f"  • Total API calls: {total_calls}")
        print(f"  • Known success rate: {overall_success_rate:.1f}% (from {total_known_calls} calls)")
        print(f"  • Estimated total failures: ~{round(total_known_calls * (1 - overall_success_rate/100))}")

def provide_failure_recommendations():
    """Provide recommendations to fix failures"""
    
    print("💡 FAILURE RESOLUTION RECOMMENDATIONS")
    print("=" * 60)
    
    recommendations = [
        {
            'issue': 'Birdeye "list_address is invalid format" errors',
            'cause': 'Token addresses not properly formatted or contain invalid characters',
            'solution': 'Add address validation before sending to Birdeye API',
            'priority': 'HIGH',
            'code_fix': 'Implement address sanitization in batch requests'
        },
        {
            'issue': 'Birdeye connection timeouts',
            'cause': 'Batch requests with too many tokens or network latency',
            'solution': 'Reduce batch size from 20 to 10-15 tokens per request',
            'priority': 'HIGH',
            'code_fix': 'Modify BATCH_SIZE constant in birdeye_connector.py'
        },
        {
            'issue': 'Jupiter 88.5% success rate',
            'cause': 'Some tokens may not exist in Jupiter database or rate limiting',
            'solution': 'Add retry logic and better error handling',
            'priority': 'MEDIUM',
            'code_fix': 'Implement exponential backoff for Jupiter API calls'
        },
        {
            'issue': 'Missing success rate data for some APIs',
            'cause': 'API tracking not capturing all response codes',
            'solution': 'Enhance API response tracking',
            'priority': 'LOW',
            'code_fix': 'Add comprehensive response code logging'
        }
    ]
    
    for i, rec in enumerate(recommendations, 1):
        priority_color = "🔴" if rec['priority'] == 'HIGH' else "🟡" if rec['priority'] == 'MEDIUM' else "🟢"
        
        print(f"{i}. {priority_color} {rec['issue']}")
        print(f"   Cause: {rec['cause']}")
        print(f"   Solution: {rec['solution']}")
        print(f"   Code Fix: {rec['code_fix']}")
        print()

def extract_timestamp(log_line):
    """Extract timestamp from log line"""
    timestamp_match = re.search(r'(\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2})', log_line)
    return timestamp_match.group(1) if timestamp_match else "Unknown"

def main():
    """Main analysis function"""
    
    try:
        # Analyze log failures
        failures = analyze_log_failures()
        
        print()
        
        # Deep dive into specific APIs
        analyze_birdeye_specific_issues(failures)
        analyze_jupiter_performance(failures)
        
        print()
        
        # Analyze success rates
        analyze_success_rates_from_scan_output()
        
        print()
        
        # Provide recommendations
        provide_failure_recommendations()
        
        print()
        print("🎯 INVESTIGATION COMPLETE")
        print("=" * 60)
        
    except Exception as e:
        print(f"❌ Error during analysis: {e}")
        import traceback
        traceback.print_exc()

if __name__ == '__main__':
    main() 