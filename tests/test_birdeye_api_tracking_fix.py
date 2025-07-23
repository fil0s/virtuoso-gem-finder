#!/usr/bin/env python3
"""
Test script to verify Birdeye API tracking fix
"""

import asyncio
import sys
import os
import logging

# Add current directory to path
sys.path.append(os.getcwd())

async def test_birdeye_api_tracking():
    """Test that Birdeye API calls are properly tracked"""
    
    print("🔍 Testing Birdeye API Tracking Fix")
    print("=" * 50)
    
    try:
        # Import detector
        from scripts.high_conviction_token_detector import HighConvictionTokenDetector
        
        # Initialize detector with debug mode
        detector = HighConvictionTokenDetector(debug_mode=True)
        
        # Check initial Birdeye API stats
        initial_stats = detector._get_birdeye_api_stats()
        print(f"📊 Initial Birdeye API stats: {initial_stats}")
        
        # Check session stats
        session_birdeye_stats = detector.session_stats['api_usage_by_service']['birdeye']
        print(f"📋 Initial session Birdeye stats: {session_birdeye_stats['total_calls']} calls")
        
        # Run one detection cycle
        print("\n🚀 Running one detection cycle...")
        result = await detector.run_detection_cycle()
        
        # Check final stats
        final_stats = detector._get_birdeye_api_stats()
        print(f"\n📊 Final Birdeye API stats: {final_stats}")
        
        final_session_stats = detector.session_stats['api_usage_by_service']['birdeye']
        print(f"📋 Final session Birdeye stats: {final_session_stats['total_calls']} calls")
        
        # Compare
        calls_made = final_stats['calls'] - initial_stats['calls']
        session_calls_tracked = final_session_stats['total_calls']
        
        print(f"\n🔍 Analysis:")
        print(f"  • API calls made this cycle: {calls_made}")
        print(f"  • Session calls tracked: {session_calls_tracked}")
        print(f"  • Tracking working: {'✅ YES' if session_calls_tracked > 0 else '❌ NO'}")
        
        # Show result summary
        print(f"\n📈 Cycle Results:")
        print(f"  • Status: {result.get('status', 'unknown')}")
        print(f"  • Tokens analyzed: {result.get('total_analyzed', 0)}")
        print(f"  • High conviction: {result.get('high_conviction_candidates', 0)}")
        print(f"  • Duration: {result.get('cycle_duration_seconds', 0):.1f}s")
        
        # Cleanup
        await detector.cleanup()
        
        return session_calls_tracked > 0
        
    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == '__main__':
    success = asyncio.run(test_birdeye_api_tracking())
    if success:
        print("\n🎉 Birdeye API tracking fix is working!")
        sys.exit(0)
    else:
        print("\n💥 Birdeye API tracking fix needs more work!")
        sys.exit(1) 