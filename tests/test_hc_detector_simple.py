#!/usr/bin/env python3
"""
Simple test script for High Conviction Token Detector
"""

import asyncio
import sys
import os

# Add current directory to path
sys.path.append(os.getcwd())

async def run_single_scan():
    """Run a single scan cycle with proper error handling"""
    try:
        print("🚀 Starting High Conviction Token Detector test...")
        
        # Import with error handling
        try:
            from scripts.high_conviction_token_detector import HighConvictionTokenDetector
            print("✅ Import successful")
        except Exception as e:
            print(f"❌ Import failed: {e}")
            return None
        
        # Initialize detector
        try:
            detector = HighConvictionTokenDetector(debug_mode=True)
            print("✅ Detector initialized")
        except Exception as e:
            print(f"❌ Detector initialization failed: {e}")
            return None
        
        # Run detection cycle
        try:
            print("🔍 Starting detection cycle...")
            result = await detector.run_detection_cycle()
            
            print(f"\n✅ Scan completed!")
            print(f"📊 Status: {result.get('status', 'unknown')}")
            print(f"🔍 Total analyzed: {result.get('total_analyzed', 0)}")
            print(f"🎯 High conviction candidates: {result.get('high_conviction_candidates', 0)}")
            print(f"🆕 New candidates: {result.get('new_candidates', 0)}")
            print(f"📱 Alerts sent: {result.get('alerts_sent', 0)}")
            print(f"⏱️ Duration: {result.get('cycle_duration_seconds', 0):.1f}s")
            
            return result
            
        except Exception as e:
            print(f"❌ Detection cycle failed: {e}")
            import traceback
            traceback.print_exc()
            return None
            
        finally:
            # Cleanup
            try:
                await detector.cleanup()
                print("✅ Cleanup completed")
            except Exception as e:
                print(f"⚠️ Cleanup error: {e}")
                
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        import traceback
        traceback.print_exc()
        return None

if __name__ == '__main__':
    result = asyncio.run(run_single_scan())
    if result:
        print("\n🎉 Test completed successfully!")
    else:
        print("\n💥 Test failed!")
        sys.exit(1) 