#!/usr/bin/env python3
"""
Quick 10-second test to verify RPC connection
"""

import asyncio
import sys
import time

sys.path.append('.')
from services.pump_fun_rpc_monitor import PumpFunRPCMonitor

async def quick_test():
    print("🔥 QUICK CONNECTION TEST")
    print("=" * 30)
    
    try:
        # Test 1: Can we create the monitor?
        print("📡 Creating RPC monitor...")
        monitor = PumpFunRPCMonitor(debug_mode=False)  # Less verbose
        print("✅ Monitor created successfully")
        
        # Test 2: Can we connect to WebSocket?
        print("🔌 Testing WebSocket connection...")
        
        # Create a simple task to connect
        start_time = time.time()
        connection_task = asyncio.create_task(monitor.start_monitoring())
        
        # Wait 10 seconds
        await asyncio.sleep(10)
        
        # Check connection status
        stats = monitor.get_performance_stats()
        elapsed = time.time() - start_time
        
        print(f"\n📊 QUICK TEST RESULTS:")
        print(f"   ⏰ Test time: {elapsed:.1f} seconds")
        print(f"   📡 Connected: {stats['is_connected']}")
        print(f"   📥 Events received: {stats['events_processed']}")
        print(f"   ⚡ Events/sec: {stats['events_per_second']:.2f}")
        
        if stats['is_connected']:
            print("✅ CONNECTION SUCCESSFUL!")
            if stats['events_processed'] > 0:
                print(f"✅ RECEIVING DATA! ({stats['events_processed']} events)")
            else:
                print("📡 Connected but no events yet (normal)")
        else:
            print("❌ CONNECTION FAILED")
            
    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        
    finally:
        await monitor.cleanup()
        print("🔄 Test completed")

if __name__ == "__main__":
    asyncio.run(quick_test()) 