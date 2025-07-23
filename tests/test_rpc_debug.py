#!/usr/bin/env python3
"""
Quick test of the enhanced RPC monitor with debug logging
"""

import asyncio
import sys
import time
from services.pump_fun_rpc_monitor import PumpFunRPCMonitor

async def test_enhanced_rpc():
    """Test the enhanced RPC monitor with short run"""
    print("🔥 Testing Enhanced RPC Monitor with Debug")
    print("=" * 50)
    
    monitor = PumpFunRPCMonitor(debug_mode=True)
    
    # Track any tokens detected
    tokens_detected = []
    
    async def on_new_token(token_data):
        tokens_detected.append(token_data)
        print(f"\n🚨 TOKEN DETECTED: {token_data['symbol']} (${token_data['market_cap']:,})")
        print(f"   🎯 Address: {token_data['token_address']}")
        print(f"   🔍 Method: {token_data['detection_method']}")
        print(f"   📊 Processing #: {token_data['debug_info']['processing_number']}")
    
    monitor.set_callbacks(on_new_token=on_new_token)
    
    try:
        print("🚀 Starting 2-minute enhanced RPC test...")
        print("   🐛 Debug mode: ENABLED")
        print("   📊 Watching for pump.fun events...")
        print()
        
        # Start monitoring in background
        monitoring_task = asyncio.create_task(monitor.start_monitoring())
        
        # Run for 2 minutes
        await asyncio.sleep(120)
        
        print("\n⏰ Test time completed")
        
        # Get debug summary
        debug_summary = monitor.get_debug_summary()
        
        print("\n📊 TEST RESULTS:")
        print("=" * 30)
        print(f"🔌 Connection: {'CONNECTED' if debug_summary['connection_health']['is_connected'] else 'DISCONNECTED'}")
        print(f"📥 Messages Received: {debug_summary['event_processing']['messages_received']}")
        print(f"🎯 Program Notifications: {debug_summary['event_processing']['program_notifications']}")
        print(f"📊 Account Updates: {debug_summary['event_processing']['account_updates']}")
        print(f"🔍 Parse Attempts: {debug_summary['event_processing']['parsing_attempts']}")
        print(f"✅ Successful Parses: {debug_summary['event_processing']['successful_parses']}")
        print(f"📈 Parse Success Rate: {debug_summary['event_processing']['parse_success_rate']:.1f}%")
        print(f"🚨 Tokens Detected: {debug_summary['token_detection']['tokens_detected']}")
        print(f"📊 Debug Events: {debug_summary['token_detection']['debug_events_count']}")
        
        if tokens_detected:
            print(f"\n🎯 DETECTED TOKENS ({len(tokens_detected)}):")
            for i, token in enumerate(tokens_detected, 1):
                print(f"   {i}. {token['symbol']} - {token['detection_method']}")
        else:
            print("\n⚠️ No tokens detected during test period")
            print("   💡 This could be normal - token launches are sporadic")
            
        # Check recent debug events
        if debug_summary['recent_debug_events']:
            print(f"\n🐛 RECENT DEBUG EVENTS:")
            for event in debug_summary['recent_debug_events'][-3:]:
                print(f"   • {event['type']} at {event['timestamp']}")
        
    except KeyboardInterrupt:
        print("\n⏹️ Test interrupted by user")
    except Exception as e:
        print(f"\n❌ Test error: {e}")
        import traceback
        traceback.print_exc()
    finally:
        await monitor.cleanup()
        print("\n✅ Enhanced RPC test completed")

if __name__ == "__main__":
    asyncio.run(test_enhanced_rpc())
