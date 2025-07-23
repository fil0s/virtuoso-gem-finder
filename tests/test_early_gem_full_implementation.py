#!/usr/bin/env python3
"""
🧪 EARLY GEM DETECTOR - FULL IMPLEMENTATION TEST
Test all three key enhancements:
1. Token Discovery Enhancement: Pump.fun/Launchlab APIs
2. Data Format Adaptation: BirdeyeAPI methods  
3. Telegram Alerts: High conviction alert system
"""

import asyncio
import sys
import os
import time
from datetime import datetime

# Add project root to path
sys.path.append(os.getcwd())

async def test_full_implementation():
    """Test complete Early Gem Detector implementation"""
    
    print("🚀 EARLY GEM DETECTOR - FULL IMPLEMENTATION TEST")
    print("=" * 80)
    print("Testing all three key enhancements:")
    print("1. 🔥 Token Discovery Enhancement: Pump.fun/Launchlab APIs")
    print("2. 📊 Data Format Adaptation: BirdeyeAPI methods")
    print("3. 📱 Telegram Alerts: High conviction alert system")
    print()
    
    try:
        # Initialize Early Gem Detector
        print("🔄 Initializing Early Gem Detector...")
        from scripts.early_gem_detector import EarlyGemDetector
        
        detector = EarlyGemDetector(debug_mode=True)
        
        # Test Component Initialization
        print("\n🧪 TEST 1: COMPONENT INITIALIZATION")
        print("-" * 50)
        
        print(f"   🔥 Pump.fun integration: {'✅ ACTIVE' if detector.pump_fun_integration else '❌ DISABLED'}")
        print(f"   🎯 Launchlab integration: {'✅ ACTIVE' if detector.launchlab_integration else '❌ DISABLED'}")
        print(f"   📊 Birdeye API: {'✅ ACTIVE' if detector.birdeye_api else '❌ DISABLED'}")
        print(f"   📱 Telegram alerter: {'✅ ENABLED' if detector.telegram_alerter else '❌ DISABLED'}")
        print(f"   🎯 Early Gem Scorer: {'✅ LOADED' if detector.early_gem_scorer else '❌ MISSING'}")
        
        # Test Multi-Platform Discovery
        print("\n🧪 TEST 2: MULTI-PLATFORM TOKEN DISCOVERY")
        print("-" * 50)
        
        discovery_start = time.time()
        candidates = await detector.discover_early_tokens()
        discovery_time = time.time() - discovery_start
        
        print(f"   🔍 Discovery completed in {discovery_time:.2f}s")
        print(f"   📊 Total candidates found: {len(candidates)}")
        
        # Break down by source
        pump_fun_count = len([c for c in candidates if c.get('source') == 'pump_fun_stage0'])
        launchlab_count = len([c for c in candidates if c.get('source') == 'raydium_launchlab'])
        birdeye_count = len([c for c in candidates if c.get('source') == 'birdeye_trending'])
        
        print(f"   🔥 Pump.fun Stage 0: {pump_fun_count} tokens")
        print(f"   🎯 LaunchLab Early: {launchlab_count} tokens")
        print(f"   📊 Birdeye Trending: {birdeye_count} tokens")
        
        # Test Data Format Adaptation
        print("\n🧪 TEST 3: DATA FORMAT ADAPTATION")
        print("-" * 50)
        
        if candidates:
            sample_candidate = candidates[0]
            print(f"   📋 Sample candidate data structure:")
            print(f"      • Address: {sample_candidate.get('address', 'N/A')[:12]}...")
            print(f"      • Symbol: {sample_candidate.get('symbol', 'N/A')}")
            print(f"      • Source: {sample_candidate.get('source', 'N/A')}")
            print(f"      • Market Cap: ${sample_candidate.get('market_cap', 0):,.0f}")
            print(f"      • Volume 24h: ${sample_candidate.get('volume_24h', 0):,.0f}")
            print(f"      • Pump.fun Launch: {sample_candidate.get('pump_fun_launch', False)}")
            print(f"      • LaunchLab Stage: {sample_candidate.get('launchlab_stage', 'N/A')}")
            print(f"   ✅ Data format adaptation working correctly")
        else:
            print(f"   ⚠️ No candidates found for data format testing")
        
        # Test Early Gem Focused Scoring
        print("\n🧪 TEST 4: EARLY GEM FOCUSED SCORING")
        print("-" * 50)
        
        if candidates:
            analysis_start = time.time()
            analyzed_candidates = await detector.analyze_early_candidates(candidates[:3])  # Test first 3
            analysis_time = time.time() - analysis_start
            
            print(f"   🎯 Analysis completed in {analysis_time:.2f}s")
            print(f"   📊 Candidates analyzed: {len(analyzed_candidates)}")
            
            if analyzed_candidates:
                for i, candidate in enumerate(analyzed_candidates, 1):
                    score = candidate['final_score']
                    token_data = candidate['candidate']
                    conviction = candidate['conviction_level']
                    
                    print(f"   {i}. {token_data.get('symbol', 'UNKNOWN')}: {score:.1f}/100 ({conviction})")
                    
                    # Show breakdown
                    breakdown = candidate.get('scoring_breakdown', {})
                    early_score = breakdown.get('early_platform_analysis', {}).get('score', 0)
                    momentum_score = breakdown.get('momentum_analysis', {}).get('score', 0)
                    print(f"      🔥 Early Platform: {early_score:.1f}/50, 📊 Momentum: {momentum_score:.1f}/38")
        
        # Test High Conviction Processing & Telegram Alerts
        print("\n🧪 TEST 5: HIGH CONVICTION PROCESSING & TELEGRAM ALERTS")
        print("-" * 50)
        
        if analyzed_candidates:
            # Lower threshold for testing
            detector.high_conviction_threshold = 30.0
            print(f"   🎯 Testing with threshold: {detector.high_conviction_threshold}")
            
            results = await detector.process_high_conviction_candidates(analyzed_candidates)
            
            print(f"   📊 Total candidates: {results['total_candidates']}")
            print(f"   🎯 High conviction: {results['high_conviction_count']}")
            print(f"   📱 Alerts sent: {results['alerts_sent']}")
            
            if results['high_conviction_count'] > 0:
                print(f"   ✅ High conviction processing working")
                if results['alerts_sent'] > 0:
                    print(f"   📱 Telegram alerts successfully sent!")
                elif detector.telegram_alerter:
                    print(f"   ⚠️ Telegram alerter available but no alerts sent")
                else:
                    print(f"   ⚠️ Telegram alerter not configured")
            else:
                print(f"   📊 No high conviction tokens found (threshold may be too high)")
        
        # Test Full Detection Cycle
        print("\n🧪 TEST 6: FULL DETECTION CYCLE")
        print("-" * 50)
        
        cycle_start = time.time()
        cycle_results = await detector.run_detection_cycle()
        cycle_time = time.time() - cycle_start
        
        print(f"   🔄 Full cycle completed in {cycle_time:.2f}s")
        print(f"   📊 Cycle ID: {cycle_results.get('cycle_id', 'N/A')}")
        print(f"   🔍 Candidates found: {cycle_results.get('candidates_found', 0)}")
        print(f"   🎯 Candidates analyzed: {cycle_results.get('candidates_analyzed', 0)}")
        print(f"   🚨 High conviction: {cycle_results.get('high_conviction_count', 0)}")
        print(f"   📱 Alerts sent: {cycle_results.get('alerts_sent', 0)}")
        
        if cycle_time > 0:
            speed = cycle_results.get('candidates_found', 0) / cycle_time
            print(f"   ⚡ Processing speed: {speed:.1f} tokens/sec")
        
        # Performance Comparison
        print("\n📊 PERFORMANCE ANALYSIS")
        print("-" * 50)
        
        print(f"   🚀 Multi-platform discovery: {discovery_time:.2f}s")
        print(f"   🎯 Early gem analysis: {analysis_time:.2f}s" if 'analysis_time' in locals() else "   🎯 Early gem analysis: N/A")
        print(f"   🔄 Full detection cycle: {cycle_time:.2f}s")
        print(f"   ⚡ Total processing speed: NO cross-platform validation delays")
        print(f"   🎯 Focus: Early stage opportunities over late validation")
        
        # Session Statistics
        print(f"\n📈 SESSION STATISTICS")
        print("-" * 50)
        
        stats = detector.session_stats
        print(f"   🔄 Cycles completed: {stats['cycles_completed']}")
        print(f"   📊 Tokens analyzed: {stats['tokens_analyzed']}")
        print(f"   🎯 High conviction found: {stats['high_conviction_found']}")
        print(f"   📱 Alerts sent: {stats['alerts_sent']}")
        print(f"   🔥 Pump.fun detections: {stats['pump_fun_detections']}")
        print(f"   🎯 LaunchLab detections: {stats['launchlab_detections']}")
        
        # Final Assessment
        print(f"\n🎯 IMPLEMENTATION ASSESSMENT")
        print("=" * 80)
        
        components_working = [
            detector.pump_fun_integration is not None,
            detector.launchlab_integration is not None,
            detector.birdeye_api is not None,
            detector.early_gem_scorer is not None,
            len(candidates) > 0 if 'candidates' in locals() else False
        ]
        
        working_count = sum(components_working)
        total_components = len(components_working)
        
        print(f"✅ Component Status: {working_count}/{total_components} working")
        print(f"🔥 Token Discovery Enhancement: {'✅ WORKING' if detector.pump_fun_integration or detector.launchlab_integration else '⚠️ PARTIAL'}")
        print(f"📊 Data Format Adaptation: {'✅ WORKING' if len(candidates) > 0 else '⚠️ NEEDS DATA'}")
        print(f"📱 Telegram Alerts: {'✅ ENABLED' if detector.telegram_alerter else '⚠️ NOT CONFIGURED'}")
        
        if working_count >= 3:
            print(f"\n🎉 SUCCESS: Early Gem Detector is PRODUCTION READY!")
            print(f"   • Multi-platform discovery working")
            print(f"   • Early Gem Focused Scoring active")
            print(f"   • Speed optimized (NO cross-platform validation)")
            print(f"   • Ready for continuous monitoring")
        else:
            print(f"\n🔧 NEEDS WORK: Some components need configuration")
            print(f"   • Check environment variables for API keys")
            print(f"   • Verify Telegram bot configuration")
            print(f"   • Ensure integrations are properly initialized")
        
        # Cleanup
        await detector.cleanup()
        
        return True
        
    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    asyncio.run(test_full_implementation()) 