#!/usr/bin/env python3
"""
🔍 PUMP.FUN API INTEGRATION STATUS CHECK
Quick verification of pump.fun API stats integration in cycle summaries
"""

import sys
import os
sys.path.append(os.getcwd())

def check_pump_fun_integration():
    print("=" * 80)
    print("🔍 PUMP.FUN API INTEGRATION STATUS CHECK")
    print("=" * 80)
    
    try:
        # Check high conviction detector for pump.fun API tracking
        print("\n1. ✅ Checking High Conviction Detector pump.fun API tracking...")
        from scripts.high_conviction_token_detector import HighConvictionTokenDetector
        
        # Initialize detector briefly
        detector = HighConvictionTokenDetector(debug_mode=True)
        
        # Check session_stats for pump.fun
        pump_fun_in_session = 'pump_fun' in detector.session_stats.get('api_usage_by_service', {})
        pump_fun_in_costs = 'pump_fun' in detector.session_stats.get('cost_analysis', {}).get('cost_breakdown_by_service', {})
        
        print(f"   📊 Pump.fun in API tracking: {'✅' if pump_fun_in_session else '❌'}")
        print(f"   💰 Pump.fun in cost tracking: {'✅' if pump_fun_in_costs else '❌'}")
        
        # Check for pump.fun capture method
        import inspect
        capture_method = detector._capture_api_usage_stats
        source_lines = inspect.getsource(capture_method)
        pump_fun_capture = 'pump_fun' in source_lines.lower()
        
        print(f"   🔍 Pump.fun in _capture_api_usage_stats: {'✅' if pump_fun_capture else '❌'}")
        
        await detector.cleanup()
        
        # Check run_6hour_20min_detector for pump.fun
        print("\n2. ✅ Checking 6-hour detector pump.fun display...")
        
        with open('run_6hour_20min_detector.py', 'r') as f:
            detector_content = f.read()
            
        pump_fun_in_detector = 'pump_fun' in detector_content
        pump_fun_in_api_stats = "'pump_fun':" in detector_content
        
        print(f"   📡 Pump.fun in detector script: {'✅' if pump_fun_in_detector else '❌'}")
        print(f"   📊 Pump.fun in API stats: {'✅' if pump_fun_in_api_stats else '❌'}")
        
        # Summary and recommendations
        print("\n" + "=" * 80)
        print("📋 INTEGRATION STATUS SUMMARY")
        print("=" * 80)
        
        all_checks = [pump_fun_in_session, pump_fun_in_costs, pump_fun_capture, pump_fun_in_detector, pump_fun_in_api_stats]
        passed_checks = sum(all_checks)
        
        print(f"✅ Integration checks passed: {passed_checks}/5")
        
        if passed_checks == 5:
            print("🎉 EXCELLENT: Pump.fun fully integrated!")
            print("   Next step: Verify pump.fun monitor is sending stats to detector")
        elif passed_checks >= 3:
            print("👍 GOOD: Most integration complete")
            print("   Issue: pump.fun stats not being captured in _capture_api_usage_stats")
        else:
            print("⚠️ NEEDS WORK: Integration incomplete")
        
        print("\n🔧 TO FIX MISSING STATS IN CYCLE SUMMARY:")
        print("1. Add pump.fun stats capture to _capture_api_usage_stats method")
        print("2. Connect pump.fun integration to early_token_detector")
        print("3. Ensure pump.fun monitor provides get_integration_stats() method")
        
        return passed_checks == 5
        
    except Exception as e:
        print(f"❌ Error checking integration: {e}")
        return False

# Make it async-compatible
import asyncio

async def main():
    return check_pump_fun_integration()

if __name__ == "__main__":
    result = asyncio.run(main())
    print(f"\n🏁 Integration Status: {'READY' if result else 'NEEDS_FIXES'}")
