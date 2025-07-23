#!/usr/bin/env python3
"""
Early Gem Optimized Routing Test
Validates that the new routing system catches early gems while optimizing costs
"""
import asyncio
import logging
import sys

# Suppress verbose logging
logging.getLogger().setLevel(logging.ERROR)

sys.path.append('.')

async def test_early_gem_routing():
    print("🔍 Testing Early Gem Optimized Smart Routing")
    print("=" * 50)
    
    try:
        try:
    from early_gem_detector import EarlyGemDetector
except ImportError:
    from src.detectors.early_gem_detector import EarlyGemDetector
        detector = EarlyGemDetector(debug_mode=False)
        
        # Test cases representing different token scenarios
        test_cases = [
            {
                'name': 'Mega-cap token (SOL)',
                'market_cap': 15000000000,  # $15B
                'volume_24h': 1000000000,   # $1B volume
                'liquidity': 500000000,
                'expected_tier': 'established',
                'should_minimize_birdeye': True,
                'early_gem_potential': False
            },
            {
                'name': 'High-potential early gem',
                'market_cap': 75000,        # $75K MC
                'volume_24h': 25000,        # $25K volume  
                'liquidity': 30000,
                'expected_tier': 'high_potential',
                'should_minimize_birdeye': False,
                'early_gem_potential': True
            },
            {
                'name': 'Emerging gem candidate', 
                'market_cap': 25000,        # $25K MC
                'volume_24h': 8000,         # $8K volume
                'liquidity': 15000,
                'expected_tier': 'emerging',
                'should_minimize_birdeye': False,
                'early_gem_potential': True
            },
            {
                'name': 'Very early micro gem',
                'market_cap': 5000,         # $5K MC
                'volume_24h': 2000,         # $2K volume
                'liquidity': 8000,
                'expected_tier': 'micro',
                'should_minimize_birdeye': False,  # Still gets light analysis!
                'early_gem_potential': True
            },
            {
                'name': 'Almost-zero activity token',
                'market_cap': 1000,         # $1K MC
                'volume_24h': 100,          # $100 volume
                'liquidity': 500,
                'expected_tier': 'micro',
                'should_minimize_birdeye': False,  # Still gets light analysis!
                'early_gem_potential': False
            }
        ]
        
        routing_results = []
        early_gem_detection_results = []
        
        print("\n🎯 Routing Analysis:")
        print("-" * 80)
        
        for test_case in test_cases:
            routing_decision = detector._determine_birdeye_routing_tier(
                test_case['market_cap'],
                test_case['volume_24h'], 
                test_case['liquidity']
            )
            
            tier_correct = routing_decision['tier'] == test_case['expected_tier']
            routing_results.append(tier_correct)
            
            # Check if early gems get appropriate analysis
            gets_birdeye_analysis = routing_decision['tier'] in ['high_potential', 'emerging', 'micro']
            early_gem_coverage = not test_case['early_gem_potential'] or gets_birdeye_analysis
            early_gem_detection_results.append(early_gem_coverage)
            
            status = "✅" if tier_correct else "❌"
            gem_status = "💎" if test_case['early_gem_potential'] else "🏢"
            analysis_type = {
                'established': '📊 DexScreener only',
                'high_potential': '💎 Full Birdeye',
                'emerging': '🔍 Selective Birdeye', 
                'micro': '🔬 Light Birdeye'
            }.get(routing_decision['tier'], '❓ Unknown')
            
            print(f"{status} {gem_status} {test_case['name']}")
            print(f"    MC: ${test_case['market_cap']:,} | Vol: ${test_case['volume_24h']:,}")
            print(f"    Tier: {routing_decision['tier']} | Analysis: {analysis_type}")
            print(f"    Early Gem Covered: {'✅' if early_gem_coverage else '❌'}")
            print()
        
        # Summary analysis
        routing_accuracy = sum(routing_results) / len(routing_results) * 100
        early_gem_coverage = sum(early_gem_detection_results) / len(early_gem_detection_results) * 100
        
        print(f"📊 Results Summary:")
        print(f"   🎯 Routing Accuracy: {routing_accuracy:.0f}% ({sum(routing_results)}/{len(routing_results)})")
        print(f"   💎 Early Gem Coverage: {early_gem_coverage:.0f}% ({sum(early_gem_detection_results)}/{len(early_gem_detection_results)})")
        
        # Cost analysis
        print(f"\n💰 Cost Impact Analysis:")
        potential_early_gems = sum(1 for tc in test_cases if tc['early_gem_potential'])
        gems_getting_analysis = sum(1 for tc, result in zip(test_cases, early_gem_detection_results) 
                                  if tc['early_gem_potential'] and result)
        established_tokens = sum(1 for tc in test_cases if not tc['early_gem_potential'])
        established_optimized = sum(1 for tc, decision in zip(test_cases, 
                                   [detector._determine_birdeye_routing_tier(tc['market_cap'], tc['volume_24h'], tc['liquidity']) 
                                    for tc in test_cases])
                                  if not tc['early_gem_potential'] and decision['tier'] == 'established')
        
        print(f"   💎 Early gems getting analysis: {gems_getting_analysis}/{potential_early_gems}")
        print(f"   🏢 Established tokens optimized: {established_optimized}/{established_tokens}")
        
        # Overall success criteria
        success = (
            routing_accuracy >= 90 and      # 90%+ routing accuracy
            early_gem_coverage >= 95 and    # 95%+ early gem coverage
            gems_getting_analysis == potential_early_gems  # All early gems covered
        )
        
        if success:
            print(f"\n🚀 SUCCESS: Early gem optimized routing working perfectly!")
            print(f"   ✅ No early gems will be missed")
            print(f"   ✅ Cost optimization maintained for established tokens")
            print(f"   ✅ Balanced approach: detection + efficiency")
        else:
            print(f"\n⚠️  Issues detected in routing logic")
            
        return success
        
    except Exception as e:
        print(f"❌ Test failed: {e}")
        return False

async def main():
    success = await test_early_gem_routing()
    
    print(f"\n" + "="*60)
    if success:
        print("🎯 EARLY GEM ROUTING: OPTIMIZED ✅")
        print("💎 All early gems will receive appropriate analysis")
        print("💰 Cost optimization maintained for established tokens") 
        print("⚖️ Perfect balance between detection and efficiency")
    else:
        print("❌ ROUTING ISSUES DETECTED")
        print("🔧 Review thresholds and routing logic")
    
    return success

if __name__ == "__main__":
    asyncio.run(main())