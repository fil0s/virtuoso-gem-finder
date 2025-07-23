#!/usr/bin/env python3
"""
Test script to verify the threshold fix is working correctly
"""

import sys
import os

# Add current directory to path
sys.path.append(os.getcwd())

def test_threshold_loading():
    """Test that the detector loads the correct threshold"""
    print("🧪 Testing High Conviction Threshold Fix")
    print("=" * 50)
    
    try:
        from early_gem_detector import EarlyGemDetector
        
        # Test with debug mode to see threshold logging
        print("🔧 Initializing detector with debug mode...")
        detector = EarlyGemDetector(debug_mode=True)
        
        print(f"✅ Detector initialized successfully")
        print(f"🎯 High conviction threshold: {detector.high_conviction_threshold}")
        
        # Expected: 35.0 (from early_gem_hunting config)
        # Previous: 85.0 (from general alert_score_threshold)
        
        if detector.high_conviction_threshold == 35.0:
            print("✅ THRESHOLD FIX SUCCESSFUL!")
            print("   🎯 Using early gem hunting threshold (35.0)")
            print("   🚨 Should now find high conviction tokens")
        elif detector.high_conviction_threshold == 85.0:
            print("❌ THRESHOLD STILL BROKEN!")
            print("   🚨 Still using general alert threshold (85.0)")
            print("   📉 Will continue to find 0 high conviction tokens")
        else:
            print(f"⚠️ UNEXPECTED THRESHOLD: {detector.high_conviction_threshold}")
            print("   🔍 Check config file for custom settings")
            
        # Test with some sample scores
        print("\n📊 Sample score analysis:")
        test_scores = [25.0, 35.0, 40.0, 50.0, 65.0, 85.0]
        
        for score in test_scores:
            is_high_conviction = score >= detector.high_conviction_threshold
            status = "✅ HIGH CONVICTION" if is_high_conviction else "❌ Below threshold"
            print(f"   Score {score:5.1f}: {status}")
            
        print(f"\n🎯 Expected results with threshold {detector.high_conviction_threshold}:")
        expected_high_conviction = [s for s in test_scores if s >= detector.high_conviction_threshold]
        print(f"   📈 High conviction scores: {expected_high_conviction}")
        print(f"   📊 High conviction count: {len(expected_high_conviction)}")
        
    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_threshold_loading()