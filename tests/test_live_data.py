#!/usr/bin/env python3
"""
Test script to verify live pump.fun data reception
"""

import asyncio
import sys
import signal
import time
from datetime import datetime

sys.path.append('.')
from services.pump_fun_rpc_monitor import PumpFunRPCMonitor

class LiveDataTest:
    def __init__(self):
        self.tokens_detected = []
        self.events_received = 0
        self.start_time = time.time()
        self.running = True
        
    async def on_token_detected(self, token_data):
        """Handle new token detection"""
        self.tokens_detected.append(token_data)
        self.events_received += 1
        
        print(f"🚨 LIVE TOKEN #{len(self.tokens_detected)}")
        print(f"   📛 Symbol: {token_data.get('symbol', 'Unknown')}")
        print(f"   🏠 Address: {token_data.get('token_address', 'Unknown')}")
        print(f"   💰 Market Cap: ${token_data.get('market_cap', 0):,}")
        print(f"   💲 Price: ${token_data.get('price', 0):.8f}")
        print(f"   ⏰ Detected at: {datetime.now().strftime('%H:%M:%S')}")
        print()
        
    def signal_handler(self, signum, frame):
        """Handle Ctrl+C gracefully"""
        print(f"\n📨 Received signal {signum} - stopping test...")
        self.running = False

async def main():
    """Main test function"""
    print("🔥 LIVE PUMP.FUN DATA TEST")
    print("=" * 50)
    print("   🎯 Testing real-time token detection")
    print("   📡 Connecting to Solana mainnet RPC")
    print("   ⏰ Test duration: 60 seconds (or Ctrl+C to stop)")
    print("   🐛 Debug logging: ENABLED")
    print()
    
    test = LiveDataTest()
    
    # Setup signal handler
    signal.signal(signal.SIGINT, test.signal_handler)
    
    # Initialize RPC monitor
    print("📡 Initializing RPC monitor...")
    monitor = PumpFunRPCMonitor(debug_mode=True)
    monitor.set_callbacks(on_new_token=test.on_token_detected)
    
    try:
        print("🚀 Starting live monitoring...")
        print("   💡 TIP: New pump.fun tokens will appear below")
        print("   ⚠️  Press Ctrl+C to stop and see results")
        print()
        
        # Start monitoring task
        monitoring_task = asyncio.create_task(monitor.start_monitoring())
        
        # Run for 60 seconds or until interrupted
        for i in range(60):
            if not test.running:
                break
            await asyncio.sleep(1)
            
            # Show periodic status every 10 seconds
            if (i + 1) % 10 == 0:
                elapsed = time.time() - test.start_time
                stats = monitor.get_performance_stats()
                print(f"📊 STATUS UPDATE ({i+1}s)")
                print(f"   📡 Connected: {stats['is_connected']}")
                print(f"   📥 Events: {stats['events_processed']}")
                print(f"   🚨 Tokens: {len(test.tokens_detected)}")
                print(f"   ⚡ Rate: {stats['events_per_second']:.2f} events/sec")
                print()
        
    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        
    finally:
        print("🔄 Stopping monitor...")
        await monitor.cleanup()
        
        # Final results
        elapsed = time.time() - test.start_time
        stats = monitor.get_performance_stats()
        
        print("\n" + "=" * 50)
        print("📊 LIVE DATA TEST RESULTS")
        print("=" * 50)
        print(f"   ⏰ Test Duration: {elapsed:.1f} seconds")
        print(f"   📡 Connection Status: {stats['is_connected']}")
        print(f"   📥 Total Events: {stats['events_processed']}")
        print(f"   🚨 Tokens Detected: {len(test.tokens_detected)}")
        print(f"   ⚡ Average Rate: {stats['events_per_second']:.2f} events/sec")
        
        if len(test.tokens_detected) > 0:
            print(f"\n✅ LIVE DATA CONFIRMED!")
            print(f"   🎯 Successfully detected {len(test.tokens_detected)} live tokens")
            print(f"   📊 Detection rate: {len(test.tokens_detected)/elapsed*60:.1f} tokens/minute")
            
            # Show last few tokens
            print(f"\n🚨 RECENT DETECTIONS:")
            for i, token in enumerate(test.tokens_detected[-3:], 1):
                print(f"   {i}. {token.get('symbol', 'Unknown')} (${token.get('market_cap', 0):,})")
        else:
            print(f"\n⚠️ NO TOKENS DETECTED")
            print(f"   📝 This could be normal - pump.fun tokens are created irregularly")
            print(f"   🔍 Check RPC connection and event processing")
            
        print("\n🎉 Live data test completed!")

if __name__ == "__main__":
    asyncio.run(main()) 