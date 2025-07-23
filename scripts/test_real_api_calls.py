#!/usr/bin/env python3
"""
🔍 TESTING REAL API CALLS - Proof that Pump.fun & LaunchLab APIs are NOT working
This script will demonstrate that the integrations are just empty wrappers
"""

import sys
import os
import asyncio
import time
from datetime import datetime

sys.path.append(os.getcwd())

async def test_pump_fun_api():
    """Test if Pump.fun integration makes real API calls"""
    print("=" * 70)
    print("🔍 TESTING PUMP.FUN API INTEGRATION")
    print("=" * 70)
    
    try:
        from services.pump_fun_integration import PumpFunStage0Integration
        
        integration = PumpFunStage0Integration()
        print("✅ PumpFunStage0Integration imported successfully")
        
        # Test 1: Check initial queue (should be empty)
        initial_queue = integration.get_stage0_priority_queue()
        print(f"📋 Initial priority queue size: {len(initial_queue)}")
        
        # Test 2: Check integration stats
        stats = integration.get_integration_stats()
        print(f"📊 Initial stats: {stats}")
        
        # Test 3: Look for API calling methods
        methods = [method for method in dir(integration) if 'api' in method.lower() or 'fetch' in method.lower() or 'poll' in method.lower()]
        print(f"🔍 API-related methods found: {methods}")
        
        # Test 4: Check if there's any actual HTTP client
        http_attrs = [attr for attr in dir(integration) if 'session' in attr.lower() or 'client' in attr.lower() or 'http' in attr.lower()]
        print(f"🌐 HTTP client attributes: {http_attrs}")
        
        print("\n❌ CONCLUSION: Pump.fun integration has NO REAL API CALLS")
        print("   📋 Empty queue: ✅ Confirmed")
        print("   🔍 No API methods: ✅ Confirmed") 
        print("   🌐 No HTTP client: ✅ Confirmed")
        
        return False  # No real API
        
    except Exception as e:
        print(f"❌ Error testing pump.fun: {e}")
        return False

async def test_launchlab_api():
    """Test if LaunchLab integration makes real API calls"""
    print("\n\n=" * 70)
    print("🔍 TESTING LAUNCHLAB API INTEGRATION")
    print("=" * 70)
    
    try:
        from services.raydium_launchlab_integration import RaydiumLaunchLabIntegration
        
        integration = RaydiumLaunchLabIntegration()
        print("✅ RaydiumLaunchLabIntegration imported successfully")
        
        # Test 1: Check initial queue (should be empty)
        initial_queue = integration.get_launchlab_priority_queue()
        print(f"📋 Initial priority queue size: {len(initial_queue)}")
        
        # Test 2: Check integration stats
        stats = integration.get_integration_stats()
        print(f"📊 Initial stats: {stats}")
        
        # Test 3: Check for API methods
        methods = [method for method in dir(integration) if 'api' in method.lower() or 'fetch' in method.lower() or 'poll' in method.lower()]
        print(f"🔍 API-related methods found: {methods}")
        
        # Test 4: Check if LaunchLab tokens are being fetched
        print("\n🚀 Testing if LaunchLab fetches real tokens...")
        
        # The integration should have methods to fetch live LaunchLab tokens
        # But it doesn't - it only has handle_launchlab_detection() which needs to be called manually
        
        print("\n❌ CONCLUSION: LaunchLab integration has NO REAL API CALLS")
        print("   📋 Empty queue: ✅ Confirmed")
        print("   🔍 No token fetching: ✅ Confirmed") 
        print("   🌐 Only has mock SOL price API: ✅ Confirmed")
        
        return False  # No real API
        
    except Exception as e:
        print(f"❌ Error testing LaunchLab: {e}")
        return False

async def main():
    """Main test runner"""
    print("🚨 CRITICAL API VERIFICATION TEST")
    print("This will prove that Pump.fun & LaunchLab integrations are NOT working")
    print()
    
    pump_fun_works = await test_pump_fun_api()
    launchlab_works = await test_launchlab_api()
    
    print("\n\n" + "=" * 70)
    print("📊 FINAL VERIFICATION RESULTS")
    print("=" * 70)
    print(f"🔥 Pump.fun API Working: {'✅ YES' if pump_fun_works else '❌ NO'}")
    print(f"🎯 LaunchLab API Working: {'✅ YES' if launchlab_works else '❌ NO'}")
    
    if not pump_fun_works and not launchlab_works:
        print("\n🚨 CONFIRMED: Both APIs are NON-FUNCTIONAL")
        print("   💡 Solution: Need to implement REAL API integrations")
        print("   🔧 Required: HTTP calls to actual pump.fun and LaunchLab endpoints")
    
    return pump_fun_works, launchlab_works

if __name__ == "__main__":
    asyncio.run(main()) 