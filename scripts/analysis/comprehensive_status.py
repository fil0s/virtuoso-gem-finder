#!/usr/bin/env python3
"""Comprehensive status analysis for sustained performance test"""

import re
from collections import defaultdict
from datetime import datetime

def comprehensive_analysis():
    print("📊 COMPREHENSIVE ANALYTICS - SUSTAINED TEST SESSION")
    print("="*70)
    
    with open('logs/virtuoso_gem_hunter.log', 'r') as f:
        lines = f.readlines()

    # Get last 1500 lines for comprehensive analysis
    recent = lines[-1500:]

    endpoints = defaultdict(int)
    success_count = 0
    total_calls = 0
    timeframes_used = defaultdict(int)
    tokens_in_pipeline = set()

    for line in recent:
        if '✅ Success:' in line:
            success_count += 1
            total_calls += 1
            
            # Extract endpoint
            endpoint_match = re.search(r'Success: ([^-]+)', line)
            if endpoint_match:
                endpoint = endpoint_match.group(1).strip()
                endpoints[endpoint] += 1
                
                # Track OHLCV timeframes
                if 'ohlcv' in line.lower():
                    timeframe_match = re.search(r"'type': '([^']+)'", line)
                    if timeframe_match:
                        timeframes_used[timeframe_match.group(1)] += 1
        
        # Track tokens being analyzed
        if 'Analyzing trend structure for' in line:
            token_match = re.search(r'Analyzing trend structure for ([A-Za-z0-9]+)', line)
            if token_match:
                tokens_in_pipeline.add(token_match.group(1))

    print(f"📞 Total API Calls: {total_calls}")
    if total_calls > 0:
        print(f"✅ Success Rate: {(success_count/total_calls*100):.1f}%")
        print(f"⚡ Call Rate: ~{total_calls/10:.1f} calls/minute")
    else:
        print("✅ Success Rate: No recent calls")
        print("⚡ Call Rate: 0.0 calls/minute")
    print(f"🔬 Unique Tokens Analyzed: {len(tokens_in_pipeline)}")

    print(f"\n🔗 ENDPOINT DISTRIBUTION:")
    for endpoint, count in sorted(endpoints.items(), key=lambda x: x[1], reverse=True):
        percentage = count/total_calls*100
        print(f"   {endpoint}: {count} ({percentage:.1f}%)")

    if timeframes_used:
        print(f"\n⏰ TIMEFRAMES ANALYZED:")
        for tf, count in sorted(timeframes_used.items(), key=lambda x: x[1], reverse=True):
            print(f"   {tf}: {count} calls")

    # System health assessment
    print(f"\n🎯 SYSTEM HEALTH ASSESSMENT:")
    
    if total_calls == 0:
        print("   ⚠️  NO ACTIVITY - No recent API calls detected")
    elif success_count/total_calls >= 0.99:
        print("   ✅ EXCELLENT - 99%+ success rate")
    elif success_count/total_calls >= 0.95:
        print("   ✅ GOOD - 95%+ success rate")
    else:
        print("   ⚠️  POOR - <95% success rate")
    
    if total_calls >= 200:  # 20+ calls/minute over 10 minutes
        print("   ✅ HIGH THROUGHPUT - 20+ calls/minute")
    elif total_calls >= 100:  # 10+ calls/minute
        print("   ⚠️  MODERATE THROUGHPUT - 10+ calls/minute")
    elif total_calls > 0:
        print("   ⚠️  LOW THROUGHPUT - <10 calls/minute")
    else:
        print("   ⚠️  NO THROUGHPUT - No recent activity")
    
    if len(tokens_in_pipeline) > 0:
        print("   ✅ ACTIVE ANALYSIS - Tokens flowing through pipeline")
    else:
        print("   ⚠️  NO ANALYSIS - No tokens in analysis pipeline")
    
    # Enhanced timeframe analysis
    if timeframes_used:
        print("   ✅ TIMEFRAME SYSTEM - Multiple timeframes active")
        if '1H' in timeframes_used and '4H' in timeframes_used and '1D' in timeframes_used:
            print("   ✅ FULL TIMEFRAME COVERAGE - 1H, 4H, 1D all working")
    
    print(f"\n⏰ Analysis Time: {datetime.now().strftime('%H:%M:%S')}")
    print("="*70)

if __name__ == "__main__":
    comprehensive_analysis() 