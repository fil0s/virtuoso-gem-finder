#!/usr/bin/env python3
"""
🧪 LIVE INTEGRATION TESTS
Test our actual Pump.fun and LaunchLab integration services
"""

import sys
import os
import asyncio
import time
from datetime import datetime

sys.path.append(os.getcwd())

async def test_pump_fun_integration():
    """Test actual Pump.fun integration service"""
    
    print("🔥 TESTING PUMP.FUN INTEGRATION SERVICE")
    print("=" * 60)
    
    try:
        from services.pump_fun_integration import PumpFunStage0Integration
        
        # Initialize integration
        pump_fun = PumpFunStage0Integration()
        
        print("✅ Pump.fun Integration initialized successfully")
        print(f"   📊 Graduation Threshold: ${pump_fun.GRADUATION_THRESHOLD:,}")
        print(f"   🔥 Supply Burn: ${pump_fun.SUPPLY_BURN_AMOUNT:,}")
        print(f"   🎯 Stage 0 queue length: {len(pump_fun.stage0_priority_queue)}")
        
        # Test bonding curve analysis
        mock_token_data = {
            'token_address': 'MOCK123PumpFunTestToken456',
            'market_cap': 5000,
            'timestamp': time.time()
        }
        
        print("\n🧪 Testing Bonding Curve Analysis:")
        
        # Test Stage 0 analysis
        stage_analysis = pump_fun.get_bonding_curve_stage_analysis(5000)
        print(f"   🎯 Stage: {stage_analysis['stage']}")
        print(f"   💰 Profit Potential: {stage_analysis['profit_potential']}")
        print(f"   🎲 Position Size: {stage_analysis['position_size_pct']:.1f}%")
        print(f"   🚀 Strategy: {stage_analysis['strategy']}")
        
        # Test bonding curve tracking
        pump_fun.track_bonding_curve_progression('MOCK123', 5000)
        pump_fun.track_bonding_curve_progression('MOCK123', 5500)
        pump_fun.track_bonding_curve_progression('MOCK123', 6200)
        
        velocity_data = pump_fun.calculate_bonding_curve_velocity('MOCK123')
        print(f"\n   ⚡ Velocity Analysis:")
        print(f"      💰 Velocity: ${velocity_data['velocity_per_hour']:,.0f}/hour")
        print(f"      📊 Confidence: {velocity_data['confidence']:.1%}")
        print(f"      🎯 Prediction: {velocity_data['prediction']}")
        
        # Test integration stats
        stats = pump_fun.get_integration_stats()
        print(f"\n📊 Integration Stats:")
        print(f"   🔢 Tokens Processed: {stats['stage0_tokens_processed']}")
        print(f"   🚨 Graduation Signals: {stats['graduation_signals_sent']}")
        print(f"   📈 Queue Length: {stats['priority_queue_length']}")
        
        return True
        
    except ImportError as e:
        print(f"❌ Import error: {e}")
        return False
    except Exception as e:
        print(f"❌ Test error: {e}")
        return False

async def test_launchlab_integration():
    """Test actual LaunchLab integration service"""
    
    print("\n🚀 TESTING LAUNCHLAB INTEGRATION SERVICE")
    print("=" * 60)
    
    try:
        from services.raydium_launchlab_integration import RaydiumLaunchLabIntegration
        
        # Initialize integration
        launchlab = RaydiumLaunchLabIntegration()
        
        print("✅ LaunchLab Integration initialized successfully")
        print(f"   📊 Graduation Threshold: {launchlab.GRADUATION_THRESHOLD_SOL} SOL")
        print(f"   💰 USD Equivalent: ${launchlab.GRADUATION_THRESHOLD_USD:,}")
        print(f"   ⚠️ Warning Threshold: {launchlab.WARNING_THRESHOLD_SOL} SOL")
        print(f"   🚨 Critical Threshold: {launchlab.CRITICAL_THRESHOLD_SOL} SOL")
        
        # Test SOL price fetching
        sol_price = await launchlab.get_current_sol_price()
        print(f"   💰 Current SOL Price: ${sol_price:.2f}")
        
        # Test SOL calculation
        mock_market_cap = 6000  # $6K market cap
        sol_analysis = launchlab.calculate_sol_raised(mock_market_cap, sol_price)
        
        print("\n🧪 Testing SOL Bonding Curve Analysis:")
        print(f"   💰 Market Cap: ${mock_market_cap:,}")
        print(f"   📊 Estimated SOL Raised: {sol_analysis['estimated_sol_raised']:.2f} SOL")
        print(f"   📈 Graduation Progress: {sol_analysis['graduation_progress_pct']:.1f}%")
        print(f"   ⏳ SOL Remaining: {sol_analysis['sol_remaining']:.2f} SOL")
        
        # Test stage analysis
        stage_analysis = launchlab.get_launchlab_stage_analysis(sol_analysis['estimated_sol_raised'])
        print(f"\n   🎯 Stage Analysis:")
        print(f"      🏷️ Stage: {stage_analysis['stage']}")
        print(f"      💰 Profit Potential: {stage_analysis['profit_potential']}")
        print(f"      ⚠️ Risk Level: {stage_analysis['risk_level']}")
        print(f"      🎲 Position Size: {stage_analysis['position_size_pct']:.1f}%")
        print(f"      🚀 Strategy: {stage_analysis['strategy']}")
        print(f"      🚪 Exit: {stage_analysis['exit_recommendation']}")
        
        # Test integration stats
        stats = launchlab.get_integration_stats()
        print(f"\n📊 Integration Stats:")
        print(f"   🔢 Tokens Processed: {stats['launchlab_tokens_processed']}")
        print(f"   🚨 Graduation Signals: {stats['graduation_signals_sent']}")
        print(f"   📈 Queue Length: {stats['priority_queue_length']}")
        print(f"   👀 Watch List: {stats['graduation_watch_list_length']}")
        
        return True
        
    except ImportError as e:
        print(f"❌ Import error: {e}")
        return False
    except Exception as e:
        print(f"❌ Test error: {e}")
        return False

async def run_integration_tests():
    """Run all integration tests"""
    
    print("🧪 COMPREHENSIVE INTEGRATION TESTS")
    print("=" * 80)
    print("Testing our actual Pump.fun and LaunchLab integration services")
    print()
    
    # Test Pump.fun
    pump_fun_success = await test_pump_fun_integration()
    
    # Test LaunchLab
    launchlab_success = await test_launchlab_integration()
    
    # Summary
    print("\n📊 INTEGRATION TEST SUMMARY")
    print("=" * 60)
    
    pump_status = "✅ OPERATIONAL" if pump_fun_success else "❌ FAILED"
    launchlab_status = "✅ OPERATIONAL" if launchlab_success else "❌ FAILED"
    
    print(f"🔥 Pump.fun Integration: {pump_status}")
    print(f"🚀 LaunchLab Integration: {launchlab_status}")
    
    if pump_fun_success and launchlab_success:
        print("\n🎯 OVERALL STATUS: ✅ BOTH INTEGRATIONS FULLY OPERATIONAL")
        print("🚀 Ready for early gem detection with dual-platform coverage!")
    else:
        print("\n🎯 OVERALL STATUS: ⚠️ SOME INTEGRATIONS NEED ATTENTION")
    
    return pump_fun_success and launchlab_success

if __name__ == "__main__":
    asyncio.run(run_integration_tests())
