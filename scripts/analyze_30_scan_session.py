#!/usr/bin/env python3
"""
Comprehensive 30-Scan Session Analysis
Analyzes the high conviction detector session data to provide detailed insights
"""

import json
import os
import sys
from datetime import datetime, timedelta
from pathlib import Path
import re
from collections import defaultdict

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

def analyze_log_data():
    """Analyze log data to extract session statistics"""
    
    print("🔍" * 80)
    print("🔍 HIGH CONVICTION DETECTOR - 30 SCAN SESSION ANALYSIS")
    print("🔍" * 80)
    
    # Based on the log output provided, extract key metrics
    session_data = {
        'total_cycles': 30,
        'successful_cycles': 29,
        'success_rate': 96.7,
        'unique_tokens_found': 0,
        'high_conviction_tokens': 0,
        'total_alerts_sent': 0,
        'estimated_cost': 0.0436,
        'discovery_rate': 0.0,
        'cycle_duration_avg': 44.1,  # seconds from last cycle
        'new_candidates_last_cycle': 5
    }
    
    print(f"\n📊 SESSION OVERVIEW:")
    print(f"  🔄 Total Detection Cycles: {session_data['total_cycles']}")
    print(f"  ✅ Successful Cycles: {session_data['successful_cycles']}")
    print(f"  📈 Success Rate: {session_data['success_rate']:.1f}%")
    print(f"  ⏱️  Average Cycle Duration: {session_data['cycle_duration_avg']:.1f}s")
    
    print(f"\n🎯 TOKEN DISCOVERY RESULTS:")
    print(f"  🪙 Total Unique Tokens Found: {session_data['unique_tokens_found']}")
    print(f"  🚀 High Conviction Tokens: {session_data['high_conviction_tokens']}")
    print(f"  📢 Total Alerts Sent: {session_data['total_alerts_sent']}")
    print(f"  🔍 Token Discovery Rate: {session_data['discovery_rate']} tokens/hour")
    print(f"  🆕 New Candidates (Last Cycle): {session_data['new_candidates_last_cycle']}")
    
    print(f"\n💰 COST ANALYSIS:")
    print(f"  💸 Total Estimated Cost: ${session_data['estimated_cost']:.4f}")
    cost_per_cycle = session_data['estimated_cost'] / session_data['total_cycles']
    print(f"  📊 Cost per Cycle: ${cost_per_cycle:.4f}")
    if session_data['unique_tokens_found'] > 0:
        cost_per_token = session_data['estimated_cost'] / session_data['unique_tokens_found']
        print(f"  🎯 Cost per Token: ${cost_per_token:.4f}")
    else:
        print(f"  🎯 Cost per Token: N/A (no tokens found)")
    
    # Calculate session duration (30 cycles * 15 minutes each)
    estimated_duration_hours = (session_data['total_cycles'] * 15) / 60
    print(f"\n⏰ SESSION TIMING:")
    print(f"  🕐 Estimated Duration: {estimated_duration_hours:.1f} hours")
    print(f"  🔄 Cycle Interval: 15 minutes")
    print(f"  ⚡ Total Processing Time: ~{(session_data['cycle_duration_avg'] * session_data['total_cycles'])/60:.1f} minutes")
    
    # Performance Analysis
    print(f"\n📈 PERFORMANCE ANALYSIS:")
    if session_data['success_rate'] >= 95:
        print(f"  ✅ Excellent reliability: {session_data['success_rate']:.1f}% success rate")
    elif session_data['success_rate'] >= 90:
        print(f"  ✅ Good reliability: {session_data['success_rate']:.1f}% success rate")
    else:
        print(f"  ⚠️  Moderate reliability: {session_data['success_rate']:.1f}% success rate")
    
    if session_data['cycle_duration_avg'] <= 60:
        print(f"  ⚡ Fast processing: {session_data['cycle_duration_avg']:.1f}s average cycle time")
    elif session_data['cycle_duration_avg'] <= 120:
        print(f"  ⏱️  Moderate processing: {session_data['cycle_duration_avg']:.1f}s average cycle time")
    else:
        print(f"  🐌 Slow processing: {session_data['cycle_duration_avg']:.1f}s average cycle time")
    
    # Market Analysis
    print(f"\n📊 MARKET ANALYSIS:")
    if session_data['unique_tokens_found'] == 0:
        print(f"  📉 No qualifying tokens found - Market may be in consolidation")
        print(f"  🎯 Cross-platform score threshold (30.0) may be too high for current market")
        print(f"  🔍 Consider lowering thresholds or expanding data sources")
    else:
        print(f"  📈 Active token discovery: {session_data['unique_tokens_found']} tokens found")
    
    # Cost Efficiency Analysis
    print(f"\n💡 COST EFFICIENCY:")
    total_api_calls_estimated = session_data['total_cycles'] * 10  # Rough estimate
    cost_per_api_call = session_data['estimated_cost'] / total_api_calls_estimated if total_api_calls_estimated > 0 else 0
    print(f"  📞 Estimated API Calls: ~{total_api_calls_estimated}")
    print(f"  💸 Cost per API Call: ~${cost_per_api_call:.6f}")
    
    if session_data['estimated_cost'] < 0.10:
        print(f"  ✅ Very cost-efficient operation")
    elif session_data['estimated_cost'] < 0.50:
        print(f"  ✅ Cost-efficient operation")
    else:
        print(f"  ⚠️  Higher cost operation - consider optimization")
    
    # Recommendations
    print(f"\n💡 RECOMMENDATIONS:")
    
    if session_data['unique_tokens_found'] == 0:
        print(f"  🎯 Consider lowering min_cross_platform_score from 30.0 to 20.0")
        print(f"  📊 Review market conditions - may be in low-volatility period")
        print(f"  🔍 Expand token sources or adjust discovery criteria")
        print(f"  ⏰ Consider running during higher market activity periods")
    
    if session_data['new_candidates_last_cycle'] > 0:
        print(f"  🎯 {session_data['new_candidates_last_cycle']} candidates found in last cycle - system is working")
        print(f"  📈 Candidates may not be meeting high conviction threshold (70.0)")
        print(f"  🔧 Consider lowering high conviction threshold to 60.0 for more alerts")
    
    if session_data['success_rate'] < 100:
        failed_cycles = session_data['total_cycles'] - session_data['successful_cycles']
        print(f"  ⚠️  {failed_cycles} failed cycle(s) - investigate error patterns")
        print(f"  🔧 Implement better error handling and retry logic")
    
    print(f"\n🎯 SYSTEM STATUS:")
    print(f"  🟢 System Health: {'Excellent' if session_data['success_rate'] >= 95 else 'Good' if session_data['success_rate'] >= 90 else 'Fair'}")
    print(f"  💰 Cost Control: {'Excellent' if session_data['estimated_cost'] < 0.10 else 'Good'}")
    print(f"  ⚡ Performance: {'Fast' if session_data['cycle_duration_avg'] <= 60 else 'Moderate'}")
    print(f"  🎯 Discovery: {'Low Activity' if session_data['unique_tokens_found'] == 0 else 'Active'}")
    
    # Check for recent session files
    print(f"\n📁 SESSION DATA FILES:")
    data_dir = Path("data")
    session_reports_dir = data_dir / "session_reports"
    
    if session_reports_dir.exists():
        session_files = list(session_reports_dir.glob("hc_detector_*"))
        print(f"  📊 Session Reports Found: {len(session_files)}")
        for file in sorted(session_files, key=lambda x: x.stat().st_mtime, reverse=True)[:3]:
            file_time = datetime.fromtimestamp(file.stat().st_mtime)
            print(f"    • {file.name} ({file_time.strftime('%Y-%m-%d %H:%M:%S')})")
    
    # Check for token registry files
    token_registries = list(data_dir.glob("token_registry_*.json"))
    if token_registries:
        print(f"  🪙 Token Registry Files: {len(token_registries)}")
        latest_registry = max(token_registries, key=lambda x: x.stat().st_mtime)
        file_time = datetime.fromtimestamp(latest_registry.stat().st_mtime)
        print(f"    • Latest: {latest_registry.name} ({file_time.strftime('%Y-%m-%d %H:%M:%S')})")
    
    print(f"\n🔍" * 80)
    print(f"🔍 END 30-SCAN SESSION ANALYSIS")
    print(f"🔍" * 80)
    
    return session_data

def check_current_detector_status():
    """Check if the detector is still running"""
    import subprocess
    try:
        result = subprocess.run(['ps', 'aux'], capture_output=True, text=True)
        if 'high_conviction_token_detector' in result.stdout:
            print(f"\n🟢 HIGH CONVICTION DETECTOR STATUS: RUNNING")
            print(f"  ⚡ Detector is actively scanning for tokens")
            print(f"  📊 Next cycle will begin in ~15 minutes")
            print(f"  🛑 To stop: Press Ctrl+C in the detector terminal")
        else:
            print(f"\n🔴 HIGH CONVICTION DETECTOR STATUS: NOT RUNNING")
            print(f"  💡 To restart: python scripts/high_conviction_token_detector.py")
    except Exception as e:
        print(f"\n❓ Could not determine detector status: {e}")

if __name__ == "__main__":
    try:
        session_data = analyze_log_data()
        check_current_detector_status()
        
        print(f"\n📊 SUMMARY:")
        print(f"30 scans completed with {session_data['success_rate']:.1f}% success rate")
        print(f"Cost: ${session_data['estimated_cost']:.4f} | No high-conviction tokens found")
        print(f"System operating efficiently with room for threshold optimization")
        
    except Exception as e:
        print(f"❌ Error analyzing session: {e}")
        import traceback
        traceback.print_exc() 