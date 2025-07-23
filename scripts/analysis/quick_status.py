#!/usr/bin/env python3
"""Quick status check for sustained performance test"""

import json
import re
from datetime import datetime
from collections import defaultdict

def analyze_recent_performance():
    """Analyze recent performance from logs"""
    
    print("🚀 SUSTAINED PERFORMANCE TEST - STATUS CHECK")
    print("="*60)
    
    try:
        with open('logs/virtuoso_gem_hunter.log', 'r') as f:
            lines = f.readlines()
    except FileNotFoundError:
        print("❌ Log file not found")
        return
    
    # Analyze last 1000 lines for recent activity
    recent_lines = lines[-1000:]
    
    api_calls = 0
    success_calls = 0
    response_times = []
    endpoints = defaultdict(int)
    tokens_analyzed = 0
    tokens_discovered = 0
    
    for line in recent_lines:
        # Count JSON API call events
        if '"event": "api_call"' in line:
            api_calls += 1
            
            if '"result": "success"' in line:
                success_calls += 1
            
            # Extract endpoint
            endpoint_match = re.search(r'"endpoint": "([^"]+)"', line)
            if endpoint_match:
                endpoints[endpoint_match.group(1)] += 1
            
            # Extract response time
            time_match = re.search(r'"response_time_ms": (\d+)', line)
            if time_match:
                response_times.append(int(time_match.group(1)))
        
        # Also count standard success log format
        elif '✅ Success:' in line:
            success_calls += 1
            api_calls += 1
            
            # Extract endpoint from success message
            endpoint_match = re.search(r'Success: ([^-]+)', line)
            if endpoint_match:
                endpoint = endpoint_match.group(1).strip()
                endpoints[endpoint] += 1
        
        # Look for token metrics
        if '"tokens_analyzed":' in line:
            match = re.search(r'"tokens_analyzed": (\d+)', line)
            if match:
                tokens_analyzed = max(tokens_analyzed, int(match.group(1)))
        
        if '"tokens_discovered":' in line:
            match = re.search(r'"tokens_discovered": (\d+)', line)
            if match:
                tokens_discovered = max(tokens_discovered, int(match.group(1)))
        
        # Look for scan metrics in standard log format
        if 'tokens remain after quick scoring' in line:
            match = re.search(r'(\d+) tokens remain after quick scoring', line)
            if match:
                tokens_analyzed = max(tokens_analyzed, int(match.group(1)))
        
        if 'tokens discovered' in line and 'analyzed' in line:
            # Look for discovery summary
            discovered_match = re.search(r'(\d+) tokens discovered', line)
            analyzed_match = re.search(r'(\d+) analyzed', line)
            if discovered_match:
                tokens_discovered = max(tokens_discovered, int(discovered_match.group(1)))
            if analyzed_match:
                tokens_analyzed = max(tokens_analyzed, int(analyzed_match.group(1)))
    
    # Calculate metrics
    success_rate = (success_calls / api_calls * 100) if api_calls > 0 else 0
    avg_response = sum(response_times) / len(response_times) if response_times else 0
    min_response = min(response_times) if response_times else 0
    max_response = max(response_times) if response_times else 0
    
    # Display results
    print(f"📞 Recent API Calls: {api_calls}")
    print(f"✅ Success Rate: {success_rate:.1f}% ({success_calls}/{api_calls})")
    if response_times:
        print(f"⏱️  Response Times: avg={avg_response:.0f}ms, min={min_response}ms, max={max_response}ms")
    else:
        print(f"⏱️  Response Times: Not available in recent logs")
    print(f"🔍 Tokens Discovered: {tokens_discovered}")
    print(f"🔬 Tokens Analyzed: {tokens_analyzed}")
    
    print(f"\n📊 TOP ENDPOINTS (Recent Activity):")
    sorted_endpoints = sorted(endpoints.items(), key=lambda x: x[1], reverse=True)
    for endpoint, count in sorted_endpoints[:8]:
        print(f"   {endpoint}: {count} calls")
    
    print(f"\n⏰ Status Time: {datetime.now().strftime('%H:%M:%S')}")
    
    # Performance assessment
    print(f"\n🎯 PERFORMANCE ASSESSMENT:")
    if api_calls == 0:
        print("   ⚠️  No recent API activity detected")
    elif success_rate >= 95:
        print("   ✅ Excellent success rate")
    elif success_rate >= 90:
        print("   ⚠️  Good success rate")
    else:
        print("   ❌ Low success rate - investigate")
    
    if avg_response == 0:
        print("   ℹ️  Response time data not available")
    elif avg_response <= 500:
        print("   ✅ Excellent response times")
    elif avg_response <= 1000:
        print("   ⚠️  Good response times")
    else:
        print("   ❌ Slow response times")
    
    if tokens_analyzed > 0:
        print("   ✅ Tokens making it through analysis pipeline")
    else:
        print("   ⚠️  No tokens analyzed yet")
    
    # System status
    if api_calls > 50:
        print("   ✅ High API activity - system actively working")
    elif api_calls > 10:
        print("   ⚠️  Moderate API activity")
    else:
        print("   ⚠️  Low API activity")
    
    print("="*60)

if __name__ == "__main__":
    analyze_recent_performance() 