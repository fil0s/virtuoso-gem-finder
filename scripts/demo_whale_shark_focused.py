#!/usr/bin/env python3
"""
Whale/Shark Focused Analysis Demo

Simple demonstration of the new whale/shark movement tracker
showing clear, actionable insights with minimal API calls.
"""

import asyncio
import json
import time
from typing import Dict, Any

from services.whale_shark_movement_tracker import WhaleSharkMovementTracker
from api.birdeye_connector import BirdeyeAPI
from utils.logger_setup import LoggerSetup


async def demo_whale_shark_analysis():
    """Demonstrate whale/shark focused analysis."""
    
    print("🐋 Whale/Shark Movement Analysis Demo")
    print("=" * 50)
    print("Focus: Efficient whale & shark tracking with minimal API calls")
    print("Classifications: Whales (>$100k), Sharks ($10k-$100k), Fish (<$10k)")
    print()
    
    # Initialize components
    logger_setup = LoggerSetup(__name__)
    logger = logger_setup.logger
    
    # Initialize dependencies
    from core.config_manager import ConfigManager
    from core.cache_manager import CacheManager
    from services.rate_limiter_service import RateLimiterService
    
    config_manager = ConfigManager()
    config = config_manager.get_config()
    cache_manager = CacheManager(ttl_default=300)
    rate_limiter = RateLimiterService()
    
    # Initialize Birdeye API
    birdeye_config = config.get('BIRDEYE_API', {})
    birdeye_api = BirdeyeAPI(
        config=birdeye_config,
        logger=logger,
        cache_manager=cache_manager,
        rate_limiter=rate_limiter
    )
    
    whale_shark_tracker = WhaleSharkMovementTracker(birdeye_api, logger)
    
    # Demo tokens
    demo_tokens = [
        ("So11111111111111111111111111111111111111112", "SOL"),
        ("EKpQGSJtjMFqKZ9KQanSqYXRcF8fBopzLHYxdM65zcjm", "WIF"),
        ("DezXAZ8z7PnrnRJjz3wXBoRgixCa6xjnB7YaB1pPB263", "BONK")
    ]
    
    total_api_calls = 0
    total_cost = 0
    
    for i, (token_address, symbol) in enumerate(demo_tokens, 1):
        print(f"🎯 Analyzing {symbol} ({i}/{len(demo_tokens)})")
        print("-" * 30)
        
        try:
            # Standard analysis (1 API call)
            start_time = time.time()
            analysis = await whale_shark_tracker.analyze_whale_shark_movements(
                token_address, priority_level="normal"
            )
            end_time = time.time()
            
            # Track efficiency
            api_calls_used = analysis["api_efficiency"]["api_calls_used"]
            total_api_calls += api_calls_used
            total_cost += api_calls_used * 30  # 30 CU per call
            
            # Display results
            print(f"⚡ API Efficiency: {api_calls_used} call(s), {api_calls_used * 30} CU")
            print(f"⏱️  Execution Time: {end_time - start_time:.2f}s")
            print()
            
            # Whale Analysis
            whale_analysis = analysis["whale_analysis"]
            print(f"🐋 WHALES DETECTED: {whale_analysis['count']}")
            if whale_analysis['count'] > 0:
                print(f"   Total Volume: ${whale_analysis['total_volume']:,.0f}")
                print(f"   Collective Bias: {whale_analysis['collective_bias'].title()}")
                
                # Show top whales
                for j, whale in enumerate(whale_analysis['top_whales'][:2], 1):
                    print(f"   #{j}: ${whale['volume']:,.0f} volume, {whale['directional_bias']}")
                    print(f"       Buy/Sell: {whale['buy_ratio']:.1%}/{whale['sell_ratio']:.1%}")
            else:
                print("   No whales detected")
            print()
            
            # Shark Analysis
            shark_analysis = analysis["shark_analysis"]
            print(f"🦈 SHARKS DETECTED: {shark_analysis['count']}")
            if shark_analysis['count'] > 0:
                print(f"   Total Volume: ${shark_analysis['total_volume']:,.0f}")
                print(f"   Collective Bias: {shark_analysis['collective_bias'].title()}")
                
                # Show top sharks
                for j, shark in enumerate(shark_analysis['top_sharks'][:2], 1):
                    print(f"   #{j}: ${shark['volume']:,.0f} volume, {shark['directional_bias']}")
                    print(f"       Buy/Sell: {shark['buy_ratio']:.1%}/{shark['sell_ratio']:.1%}")
            else:
                print("   No sharks detected")
            print()
            
            # Market Structure
            market_structure = analysis["market_structure"]
            print(f"🏗️  MARKET STRUCTURE: {market_structure['structure_type'].replace('_', ' ').title()}")
            print(f"   Whale Dominance: {market_structure['whale_dominance']:.1%}")
            print(f"   Shark Presence: {market_structure['shark_presence']:.1%}")
            print(f"   Market Control: {market_structure['market_control'].replace('_', ' ').title()}")
            print()
            
            # Trading Insights
            insights = analysis["trading_insights"]
            print(f"💡 TRADING INSIGHTS:")
            print(f"   Recommended Action: {insights['recommended_action'].replace('_', ' ').title()}")
            print(f"   Confidence Level: {insights['confidence_level'].title()}")
            print(f"   Risk Assessment: {insights['risk_assessment'].title()}")
            
            if insights['signals']:
                print(f"   Signals: {', '.join(insights['signals'])}")
            
            if insights['key_observations']:
                print(f"   Key Observations:")
                for obs in insights['key_observations']:
                    print(f"     • {obs}")
            print()
            
        except Exception as e:
            print(f"❌ Error analyzing {symbol}: {e}")
        
        print("=" * 50)
        print()
    
    # Summary
    print("📊 DEMO SUMMARY")
    print("-" * 20)
    print(f"Total Tokens Analyzed: {len(demo_tokens)}")
    print(f"Total API Calls: {total_api_calls}")
    print(f"Total Cost: {total_cost} CU")
    print(f"Average per Token: {total_api_calls/len(demo_tokens):.1f} calls, {total_cost/len(demo_tokens):.0f} CU")
    print()
    
    # Efficiency comparison
    old_approach_calls = len(demo_tokens) * 5  # 5 calls per token in old approach
    old_approach_cost = old_approach_calls * 30
    
    print("🔄 EFFICIENCY COMPARISON")
    print("-" * 25)
    print(f"Old Approach: {old_approach_calls} calls, {old_approach_cost} CU")
    print(f"New Approach: {total_api_calls} calls, {total_cost} CU")
    print(f"Savings: {old_approach_calls - total_api_calls} calls ({(old_approach_calls - total_api_calls)/old_approach_calls:.1%})")
    print(f"Cost Reduction: {old_approach_cost - total_cost} CU ({(old_approach_cost - total_cost)/old_approach_cost:.1%})")
    print()
    
    print("✅ KEY BENEFITS:")
    print("  • Clear whale vs shark classification")
    print("  • Directional bias analysis (accumulating/distributing)")
    print("  • Market structure insights")
    print("  • Actionable trading recommendations")
    print("  • 60-80% reduction in API calls")
    print("  • Focused on what matters: large trader movements")
    print()
    
    print("🎯 CONCLUSION:")
    print("The whale/shark focused approach provides clearer, more actionable")
    print("insights with dramatically fewer API calls. Perfect for understanding")
    print("what big money is doing without the noise of irrelevant timeframes.")


async def demo_high_priority_analysis():
    """Demonstrate high-priority analysis with trend detection."""
    
    print("\n🎯 HIGH-PRIORITY ANALYSIS DEMO")
    print("=" * 40)
    print("For high-volume tokens: 2 API calls with trend analysis")
    print()
    
    # Initialize components
    logger_setup = LoggerSetup(__name__)
    logger = logger_setup.logger
    
    # Initialize dependencies
    from core.config_manager import ConfigManager
    from core.cache_manager import CacheManager
    from services.rate_limiter_service import RateLimiterService
    
    config_manager = ConfigManager()
    config = config_manager.get_config()
    cache_manager = CacheManager(ttl_default=300)
    rate_limiter = RateLimiterService()
    
    # Initialize Birdeye API
    birdeye_config = config.get('BIRDEYE_API', {})
    birdeye_api = BirdeyeAPI(
        config=birdeye_config,
        logger=logger,
        cache_manager=cache_manager,
        rate_limiter=rate_limiter
    )
    
    whale_shark_tracker = WhaleSharkMovementTracker(birdeye_api, logger)
    
    # High-volume token example
    token_address = "So11111111111111111111111111111111111111112"  # SOL
    symbol = "SOL"
    
    print(f"🔍 Analyzing {symbol} with HIGH PRIORITY")
    print("-" * 30)
    
    try:
        start_time = time.time()
        analysis = await whale_shark_tracker.analyze_whale_shark_movements(
            token_address, priority_level="high"
        )
        end_time = time.time()
        
        api_calls_used = analysis["api_efficiency"]["api_calls_used"]
        print(f"⚡ API Efficiency: {api_calls_used} calls, {api_calls_used * 30} CU")
        print(f"⏱️  Execution Time: {end_time - start_time:.2f}s")
        print(f"📊 Timeframes: {', '.join(analysis['api_efficiency']['timeframes_analyzed'])}")
        print()
        
        # Show trend analysis if available
        if "trend_analysis" in analysis:
            trend = analysis["trend_analysis"]
            print("📈 TREND ANALYSIS:")
            print(f"   Momentum: {trend['momentum'].replace('_', ' ').title()}")
            
            if trend['trend_signals']:
                print(f"   Trend Signals: {', '.join(trend['trend_signals'])}")
            
            if trend['whale_trend_change']:
                print("   🐋 Whale behavior changed in recent 6h")
            
            if trend['shark_trend_change']:
                print("   🦈 Shark behavior changed in recent 6h")
            print()
        
        # Recent activity comparison
        if "recent_activity" in analysis:
            recent = analysis["recent_activity"]
            print("🕐 RECENT ACTIVITY (6h vs 24h):")
            print(f"   Whales: {recent['6h_whale_count']} (6h) vs {analysis['whale_analysis']['count']} (24h)")
            print(f"   Sharks: {recent['6h_shark_count']} (6h) vs {analysis['shark_analysis']['count']} (24h)")
            print(f"   Whale Volume: ${recent['6h_whale_volume']:,.0f} (6h)")
            print(f"   Shark Volume: ${recent['6h_shark_volume']:,.0f} (6h)")
            print()
        
        # Enhanced trading insights
        insights = analysis["trading_insights"]
        if "trend_momentum" in insights:
            print(f"🚀 ENHANCED INSIGHTS:")
            print(f"   Trend Momentum: {insights['trend_momentum'].replace('_', ' ').title()}")
            print(f"   Action: {insights['recommended_action'].replace('_', ' ').title()}")
            print(f"   Confidence: {insights['confidence_level'].title()}")
            print()
        
    except Exception as e:
        print(f"❌ Error in high-priority analysis: {e}")
    
    print("💡 HIGH-PRIORITY BENEFITS:")
    print("  • Trend momentum detection")
    print("  • Recent vs historical comparison")
    print("  • Enhanced trading signals")
    print("  • Only 2 API calls vs 5 in old approach")
    print("  • Best for tokens with >$1M daily volume")


async def main():
    """Run the whale/shark demo."""
    
    # Standard demo
    await demo_whale_shark_analysis()
    
    # High-priority demo
    await demo_high_priority_analysis()
    
    print("\n🎉 Demo completed! The whale/shark approach provides:")
    print("   • 60-80% fewer API calls")
    print("   • Clear actionable insights")
    print("   • Focus on what matters most")
    print("   • Better cost efficiency")
    print("   • Reduced system complexity")


if __name__ == "__main__":
    asyncio.run(main()) 