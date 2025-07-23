#!/usr/bin/env python3
"""
Quick Strategy Test Script

A simple script to quickly test individual token discovery strategies
with minimal setup. Perfect for rapid experimentation.
"""

import asyncio
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from core.token_discovery_strategies import (
    VolumeMomentumStrategy,
    RecentListingsStrategy,
    PriceMomentumStrategy,
    LiquidityGrowthStrategy,
    HighTradingActivityStrategy
)
from api.birdeye_connector import BirdeyeAPI
from core.config_manager import get_config_manager
from core.cache_manager import CacheManager
from services.rate_limiter_service import RateLimiterService
from services.logger_setup import LoggerSetup


async def quick_test_strategy(strategy_class, limit=10):
    """Quickly test a single strategy"""
    
    print(f"\n🧪 Quick Testing: {strategy_class.__name__}")
    print("="*60)
    
    # Setup
    logger_setup = LoggerSetup("QuickTest")
    logger = logger_setup.logger
    
    config = get_config_manager().get_config()
    cache_manager = CacheManager()
    rate_limiter = RateLimiterService()
    
    birdeye_api = BirdeyeAPI(
        config=config.get('BIRDEYE_API', {}),
        logger=logger,
        cache_manager=cache_manager,
        rate_limiter=rate_limiter
    )
    
    # Initialize and configure strategy
    strategy = strategy_class(logger=logger)
    
    # Override limit for quick testing
    strategy.api_parameters['limit'] = limit
    
    print(f"Strategy: {strategy.name}")
    print(f"Description: {strategy.description}")
    print(f"Parameters: {strategy.api_parameters}")
    
    # Execute strategy
    try:
        tokens = await strategy.execute(birdeye_api, scan_id="quick_test")
        
        print(f"\n📊 Results: {len(tokens)} tokens found")
        
        if tokens:
            print(f"\nTop {min(5, len(tokens))} tokens:")
            for i, token in enumerate(tokens[:5]):
                symbol = token.get('symbol', 'N/A')
                volume = token.get('volume24h', 0)
                price_change = token.get('priceChange24h', 0)
                market_cap = token.get('marketCap', 0)
                consecutive = token.get('strategy_data', {}).get('consecutive_appearances', 0)
                
                print(f"  {i+1}. {symbol}")
                print(f"     Volume 24h: ${volume:,.0f}")
                print(f"     Price Change 24h: {price_change:.2f}%")
                print(f"     Market Cap: ${market_cap:,.0f}")
                print(f"     Consecutive Appearances: {consecutive}")
                print()
        else:
            print("   No tokens found with current parameters")
            
    except Exception as e:
        print(f"❌ Error testing strategy: {e}")
        logger.error(f"Strategy test error: {e}")


async def test_all_strategies():
    """Test all available strategies quickly"""
    
    print("🚀 Quick Testing All Token Discovery Strategies")
    print("="*80)
    
    strategies = [
        VolumeMomentumStrategy,
        RecentListingsStrategy,
        PriceMomentumStrategy,
        LiquidityGrowthStrategy,
        HighTradingActivityStrategy
    ]
    
    for strategy_class in strategies:
        await quick_test_strategy(strategy_class, limit=5)  # Small limit for speed
        print("\n" + "-"*60)


async def compare_strategies():
    """Compare strategies side by side"""
    
    print("📊 Strategy Comparison")
    print("="*60)
    
    strategies = [
        VolumeMomentumStrategy,
        RecentListingsStrategy,
        PriceMomentumStrategy
    ]
    
    # Setup
    logger_setup = LoggerSetup("StrategyComparison")
    logger = logger_setup.logger
    
    config = get_config_manager().get_config()
    cache_manager = CacheManager()
    rate_limiter = RateLimiterService()
    
    birdeye_api = BirdeyeAPI(
        config=config.get('BIRDEYE_API', {}),
        logger=logger,
        cache_manager=cache_manager,
        rate_limiter=rate_limiter
    )
    
    results = {}
    
    for strategy_class in strategies:
        strategy = strategy_class(logger=logger)
        strategy.api_parameters['limit'] = 10  # Small limit for comparison
        
        try:
            tokens = await strategy.execute(birdeye_api, scan_id=f"compare_{strategy_class.__name__}")
            
            if tokens:
                avg_volume = sum(t.get('volume24h', 0) for t in tokens) / len(tokens)
                avg_price_change = sum(t.get('priceChange24h', 0) for t in tokens) / len(tokens)
                avg_market_cap = sum(t.get('marketCap', 0) for t in tokens) / len(tokens)
            else:
                avg_volume = avg_price_change = avg_market_cap = 0
            
            results[strategy.name] = {
                'tokens_found': len(tokens),
                'avg_volume': avg_volume,
                'avg_price_change': avg_price_change,
                'avg_market_cap': avg_market_cap
            }
            
        except Exception as e:
            print(f"Error with {strategy.name}: {e}")
            results[strategy.name] = {
                'tokens_found': 0,
                'avg_volume': 0,
                'avg_price_change': 0,
                'avg_market_cap': 0,
                'error': str(e)
            }
    
    # Display comparison
    print(f"\n{'Strategy':<30} {'Tokens':<8} {'Avg Volume':<15} {'Avg Price Δ':<12} {'Avg Market Cap':<15}")
    print("-" * 80)
    
    for strategy_name, data in results.items():
        tokens = data['tokens_found']
        volume = f"${data['avg_volume']:,.0f}" if data['avg_volume'] > 0 else "N/A"
        price_change = f"{data['avg_price_change']:.1f}%" if data['avg_price_change'] != 0 else "N/A"
        market_cap = f"${data['avg_market_cap']:,.0f}" if data['avg_market_cap'] > 0 else "N/A"
        
        print(f"{strategy_name:<30} {tokens:<8} {volume:<15} {price_change:<12} {market_cap:<15}")


async def main():
    """Main function with menu"""
    
    if len(sys.argv) > 1:
        command = sys.argv[1].lower()
        
        if command == "all":
            await test_all_strategies()
        elif command == "compare":
            await compare_strategies()
        elif command == "volume":
            await quick_test_strategy(VolumeMomentumStrategy)
        elif command == "recent":
            await quick_test_strategy(RecentListingsStrategy)
        elif command == "price":
            await quick_test_strategy(PriceMomentumStrategy)
        elif command == "liquidity":
            await quick_test_strategy(LiquidityGrowthStrategy)
        elif command == "activity":
            await quick_test_strategy(HighTradingActivityStrategy)
        else:
            print(f"Unknown command: {command}")
            print_usage()
    else:
        print_menu()
        choice = input("\nEnter your choice (1-7): ").strip()
        
        if choice == "1":
            await quick_test_strategy(VolumeMomentumStrategy)
        elif choice == "2":
            await quick_test_strategy(RecentListingsStrategy)
        elif choice == "3":
            await quick_test_strategy(PriceMomentumStrategy)
        elif choice == "4":
            await quick_test_strategy(LiquidityGrowthStrategy)
        elif choice == "5":
            await quick_test_strategy(HighTradingActivityStrategy)
        elif choice == "6":
            await test_all_strategies()
        elif choice == "7":
            await compare_strategies()
        else:
            print("Invalid choice. Please run again.")


def print_menu():
    """Print the interactive menu"""
    print("🧪 Quick Strategy Testing Menu")
    print("="*40)
    print("1. Test Volume Momentum Strategy")
    print("2. Test Recent Listings Strategy")
    print("3. Test Price Momentum Strategy")
    print("4. Test Liquidity Growth Strategy")
    print("5. Test High Trading Activity Strategy")
    print("6. Test All Strategies")
    print("7. Compare Strategies")


def print_usage():
    """Print command line usage"""
    print("Usage:")
    print("  python scripts/quick_strategy_test.py [command]")
    print()
    print("Commands:")
    print("  all       - Test all strategies")
    print("  compare   - Compare strategies side by side")
    print("  volume    - Test Volume Momentum Strategy")
    print("  recent    - Test Recent Listings Strategy")
    print("  price     - Test Price Momentum Strategy")
    print("  liquidity - Test Liquidity Growth Strategy")
    print("  activity  - Test High Trading Activity Strategy")
    print()
    print("Examples:")
    print("  python scripts/quick_strategy_test.py all")
    print("  python scripts/quick_strategy_test.py compare")
    print("  python scripts/quick_strategy_test.py volume")


if __name__ == "__main__":
    asyncio.run(main()) 