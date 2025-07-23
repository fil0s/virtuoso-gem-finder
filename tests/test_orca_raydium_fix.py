#!/usr/bin/env python3
"""
Quick test to verify Orca and Raydium connectors are working after the fix
"""

import asyncio
import logging
from scripts.cross_platform_token_analyzer import CrossPlatformAnalyzer

async def test_orca_raydium_fix():
    """Test that Orca and Raydium connectors are now working"""
    print("🧪 Testing Orca and Raydium connector fix...")
    
    # Initialize analyzer
    analyzer = CrossPlatformAnalyzer()
    
    try:
        # Test Orca connector
        print("\n🌊 Testing Orca connector...")
        orca_pools = await analyzer.orca.get_trending_pools(min_volume_24h=1000)
        orca_stats = analyzer.orca.get_api_call_statistics()
        
        print(f"✅ Orca: {len(orca_pools)} pools found")
        print(f"📊 Orca stats: {orca_stats.get('total_calls', 0)} calls, {orca_stats.get('successful_calls', 0)} successes")
        
        # Test Raydium connector  
        print("\n⚡ Testing Raydium connector...")
        raydium_pairs = await analyzer.raydium.get_volume_trending_pairs(min_volume_24h=1000)
        raydium_stats = analyzer.raydium.get_api_call_statistics()
        
        print(f"✅ Raydium: {len(raydium_pairs)} pairs found")
        print(f"📊 Raydium stats: {raydium_stats.get('total_calls', 0)} calls, {raydium_stats.get('successful_calls', 0)} successes")
        
        # Test cross-platform analysis (quick version)
        print("\n🔗 Testing full cross-platform data collection...")
        platform_data = await analyzer.collect_all_data()
        
        orca_data = platform_data.get('orca_trending_pools', [])
        raydium_data = platform_data.get('raydium_trending_pairs', [])
        
        print(f"📊 Cross-platform results:")
        print(f"  🌊 Orca pools: {len(orca_data)}")
        print(f"  ⚡ Raydium pairs: {len(raydium_data)}")
        
        # Check if data is now appearing
        if len(orca_data) > 0 or len(raydium_data) > 0:
            print("🎉 SUCCESS: Orca and/or Raydium data is now working!")
        else:
            print("⚠️ WARNING: Still no data from Orca/Raydium - may be API issues")
            
        # Get comprehensive API stats
        all_stats = analyzer.get_api_stats()
        print(f"\n📈 All API Statistics:")
        for platform, stats in all_stats.items():
            calls = stats.get('calls', 0)
            successes = stats.get('successes', 0)
            success_rate = (successes/calls*100) if calls > 0 else 0
            print(f"  {platform}: {calls} calls, {success_rate:.1f}% success")
            
    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback
        print(f"Traceback: {traceback.format_exc()}")
        
    finally:
        await analyzer.close()

if __name__ == "__main__":
    asyncio.run(test_orca_raydium_fix()) 