#!/usr/bin/env python3
"""
Test Strategies with Relaxed Filters

This script applies the recommended filter relaxations from the analysis
and tests each strategy to measure improvement in token discovery.
"""

import asyncio
import json
import time
import sys
from pathlib import Path
from datetime import datetime

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from core.strategies import (
    VolumeMomentumStrategy,
    RecentListingsStrategy, 
    PriceMomentumStrategy,
    LiquidityGrowthStrategy,
    HighTradingActivityStrategy,
    SmartMoneyWhaleStrategy
)
from api.birdeye_connector import BirdeyeAPI
from core.cache_manager import CacheManager
from services.rate_limiter_service import RateLimiterService
from services.logger_setup import LoggerSetup


class RelaxedStrategyTester:
    """Test strategies with systematically relaxed filters."""
    
    def __init__(self):
        self.logger_setup = LoggerSetup("RelaxedFilterTest")
        self.logger = self.logger_setup.logger
        
        # Relaxed configurations based on analysis
        self.relaxed_configs = {
            "Volume Momentum Strategy": {
                "api_parameters": {
                    # Keep current API params - they're reasonable
                    "sort_by": "volume_24h_change_percent",
                    "sort_type": "desc",
                    "min_liquidity": 100000,  # Current
                    "min_volume_24h_usd": 50000,  # Current
                    "min_holder": 500,  # Current
                    "limit": 20
                },
                "min_consecutive_appearances": 2,  # Reduced from 3
                "risk_management_updates": {
                    "suspicious_volume_multiplier": 5.0,  # Increased from 3.0
                    "min_days_since_listing": 1  # Reduced from 2
                }
            },
            
            "Recent Listings Strategy": {
                "api_parameters": {
                    "sort_by": "recent_listing_time",
                    "sort_type": "desc",
                    "min_liquidity": 50000,  # Reduced from 200000
                    "min_trade_24h_count": 300,  # Reduced from 500
                    "min_holder": 100,  # Reduced from 300
                    "limit": 30
                },
                "min_consecutive_appearances": 2,  # Keep current
                "risk_management_updates": {
                    "suspicious_volume_multiplier": 5.0,
                    "min_days_since_listing": 1
                }
            },
            
            "Price Momentum Strategy": {
                "api_parameters": {
                    "sort_by": "price_change_24h_percent",
                    "sort_type": "desc",
                    "min_volume_24h_usd": 50000,  # Reduced from 100000
                    "min_liquidity": 150000,  # Reduced from 300000
                    "min_trade_24h_count": 420,  # Reduced from 700
                    "limit": 25
                },
                "min_consecutive_appearances": 2,  # Keep current
                "risk_management_updates": {
                    "suspicious_volume_multiplier": 5.0,
                    "min_days_since_listing": 1
                }
            },
            
            "Liquidity Growth Strategy": {
                "api_parameters": {
                    "sort_by": "liquidity",
                    "sort_type": "desc",
                    "min_market_cap": 500000,  # Reduced from 1000000
                    "max_market_cap": 100000000,  # Keep current
                    "min_holder": 400,  # Reduced from 1000
                    "min_volume_24h_usd": 100000,  # Reduced from 200000
                    "limit": 50
                },
                "min_consecutive_appearances": 2,  # Reduced from 3
                "risk_management_updates": {
                    "suspicious_volume_multiplier": 5.0,
                    "min_days_since_listing": 1
                }
            },
            
            "High Trading Activity Strategy": {
                "api_parameters": {
                    # Keep current API params - they're reasonable
                    "sort_by": "trade_24h_count",
                    "sort_type": "desc",
                    "min_liquidity": 150000,  # Current
                    "min_volume_24h_usd": 75000,  # Current
                    "min_holder": 400,  # Current
                    "limit": 30
                },
                "min_consecutive_appearances": 2,  # Reduced from 3
                "risk_management_updates": {
                    "suspicious_volume_multiplier": 5.0,
                    "min_days_since_listing": 1
                }
            },
            
            "Smart Money Whale Strategy": {
                "api_parameters": {
                    "sort_by": "volume_24h_usd",
                    "sort_type": "desc",
                    "min_liquidity": 250000,  # Reduced from 500000
                    "min_volume_24h_usd": 500000,  # Reduced from 1000000
                    "min_holder": 400,  # Reduced from 1000
                    "limit": 100
                },
                "min_consecutive_appearances": 2,  # Keep current
                "risk_management_updates": {
                    "suspicious_volume_multiplier": 5.0,
                    "min_days_since_listing": 1
                }
            }
        }
    
    async def test_relaxed_strategies(self):
        """Test all strategies with relaxed filters."""
        
        self.logger.info("🧪 TESTING STRATEGIES WITH RELAXED FILTERS")
        print("🧪 TESTING STRATEGIES WITH RELAXED FILTERS")
        print("=" * 80)
        
        # Initialize Birdeye API
        birdeye_api = await self._initialize_birdeye_api()
        
        strategies = [
            VolumeMomentumStrategy(),
            RecentListingsStrategy(),
            PriceMomentumStrategy(),
            LiquidityGrowthStrategy(),
            HighTradingActivityStrategy(),
            SmartMoneyWhaleStrategy()
        ]
        
        results = {}
        scan_id = f"relaxed_filter_test_{int(time.time())}"
        
        for strategy in strategies:
            strategy_name = strategy.name
            print(f"\n🔍 Testing {strategy_name} with relaxed filters...")
            
            # Apply relaxed configuration
            relaxed_config = self.relaxed_configs.get(strategy_name, {})
            
            if relaxed_config:
                # Update API parameters
                api_params = relaxed_config.get("api_parameters", {})
                strategy.api_parameters.update(api_params)
                
                # Update consecutive appearances
                min_consecutive = relaxed_config.get("min_consecutive_appearances")
                if min_consecutive is not None:
                    strategy.min_consecutive_appearances = min_consecutive
                
                # Update risk management
                risk_updates = relaxed_config.get("risk_management_updates", {})
                strategy.risk_management.update(risk_updates)
                
                print(f"   📝 Applied relaxed parameters:")
                for key, value in api_params.items():
                    print(f"      {key}: {value}")
                if min_consecutive is not None:
                    print(f"      min_consecutive_appearances: {min_consecutive}")
                for key, value in risk_updates.items():
                    print(f"      {key}: {value}")
            
            # Test the strategy
            try:
                start_time = time.time()
                tokens = await strategy.execute(birdeye_api, scan_id=f"{scan_id}_{strategy_name.lower().replace(' ', '_')}")
                execution_time = time.time() - start_time
                
                # Get API statistics
                api_stats = birdeye_api.get_api_call_statistics()
                
                results[strategy_name] = {
                    "tokens_found": len(tokens),
                    "execution_time": execution_time,
                    "success": True,
                    "tokens": tokens[:3] if tokens else [],  # First 3 for preview
                    "api_calls": api_stats.get('total_api_calls', 0),
                    "cache_hits": api_stats.get('cache_hits', 0)
                }
                
                print(f"   ✅ Found {len(tokens)} tokens in {execution_time:.1f}s")
                if tokens:
                    print(f"   🎯 Sample tokens: {[t.get('symbol', 'N/A') for t in tokens[:3]]}")
                
                self.logger.info(f"Relaxed {strategy_name}: {len(tokens)} tokens in {execution_time:.1f}s")
                
            except Exception as e:
                results[strategy_name] = {
                    "tokens_found": 0,
                    "execution_time": 0,
                    "success": False,
                    "error": str(e),
                    "api_calls": 0,
                    "cache_hits": 0
                }
                print(f"   ❌ Error: {e}")
                self.logger.error(f"Error testing relaxed {strategy_name}: {e}")
        
        # Print comprehensive summary
        await self._print_comprehensive_summary(results)
        
        # Save results
        await self._save_test_results(results)
        
        return results
    
    async def _print_comprehensive_summary(self, results):
        """Print comprehensive test results summary."""
        
        print(f"\n📊 RELAXED FILTER TEST RESULTS")
        print("=" * 80)
        
        total_tokens = 0
        successful_strategies = 0
        total_api_calls = 0
        
        # Strategy results
        for strategy_name, result in results.items():
            tokens_found = result["tokens_found"]
            success = result["success"]
            execution_time = result.get("execution_time", 0)
            api_calls = result.get("api_calls", 0)
            
            if success and tokens_found > 0:
                status = "✅"
                successful_strategies += 1
                total_tokens += tokens_found
            elif success:
                status = "⚠️"
                successful_strategies += 1
            else:
                status = "❌"
            
            total_api_calls += api_calls
            
            print(f"{status} {strategy_name}:")
            print(f"   Tokens: {tokens_found}, Time: {execution_time:.1f}s, API calls: {api_calls}")
            
            if not success:
                print(f"   Error: {result.get('error', 'Unknown')}")
        
        print(f"\n🎯 SUMMARY:")
        print(f"   • Successful strategies: {successful_strategies}/6")
        print(f"   • Total tokens discovered: {total_tokens}")
        print(f"   • Average tokens per strategy: {total_tokens/6:.1f}")
        print(f"   • Total API calls used: {total_api_calls}")
        
        if successful_strategies > 1:  # More than just High Trading Activity
            print(f"\n🚀 IMPROVEMENT ACHIEVED!")
            print(f"   • Previously only 1/6 strategies found tokens")
            print(f"   • Now {successful_strategies}/6 strategies are working")
            print(f"   • Filter relaxation was successful!")
        else:
            print(f"\n⚠️  Limited improvement - may need further relaxation")
    
    async def _save_test_results(self, results):
        """Save test results to file."""
        
        try:
            results_dir = Path("scripts/results")
            results_dir.mkdir(exist_ok=True)
            
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            results_file = results_dir / f"relaxed_strategy_test_{timestamp}.json"
            
            # Prepare results for JSON serialization
            json_results = {}
            for strategy_name, result in results.items():
                json_results[strategy_name] = {
                    "tokens_found": result["tokens_found"],
                    "execution_time": result["execution_time"],
                    "success": result["success"],
                    "api_calls": result.get("api_calls", 0),
                    "cache_hits": result.get("cache_hits", 0)
                }
                
                if not result["success"]:
                    json_results[strategy_name]["error"] = result.get("error", "Unknown")
                
                # Include sample tokens (limited data to avoid huge files)
                if result.get("tokens"):
                    json_results[strategy_name]["sample_tokens"] = [
                        {
                            "symbol": token.get("symbol", "N/A"),
                            "address": token.get("address", "N/A"),
                            "score": token.get("score", 0)
                        }
                        for token in result["tokens"][:3]
                    ]
            
            # Add test metadata
            test_metadata = {
                "test_timestamp": timestamp,
                "test_type": "relaxed_filter_test",
                "total_strategies_tested": len(results),
                "successful_strategies": sum(1 for r in results.values() if r["success"]),
                "total_tokens_found": sum(r["tokens_found"] for r in results.values()),
                "relaxed_configs_applied": True
            }
            
            final_results = {
                "metadata": test_metadata,
                "strategy_results": json_results,
                "relaxed_configurations": self.relaxed_configs
            }
            
            with open(results_file, 'w') as f:
                json.dump(final_results, f, indent=2, default=str)
            
            print(f"\n💾 Test results saved to: {results_file}")
            self.logger.info(f"Relaxed strategy test results saved to: {results_file}")
            
        except Exception as e:
            self.logger.error(f"Error saving test results: {e}")
    
    async def _initialize_birdeye_api(self) -> BirdeyeAPI:
        """Initialize BirdeyeAPI with required dependencies."""
        import os
        
        # Check API key
        api_key = os.getenv('BIRDEYE_API_KEY')
        if not api_key:
            raise ValueError("BIRDEYE_API_KEY environment variable not set")
        
        # Initialize services
        cache_manager = CacheManager(ttl_default=300)
        rate_limiter = RateLimiterService()
        
        # Create config for BirdeyeAPI
        config = {
            'api_key': api_key,
            'base_url': 'https://public-api.birdeye.so',
            'rate_limit': 15,  # Use starter package rate limit
            'request_timeout_seconds': 20,
            'cache_ttl_default_seconds': 300,
            'cache_ttl_error_seconds': 60,
            'max_retries': 3,
            'backoff_factor': 2
        }
        
        birdeye_api = BirdeyeAPI(config, self.logger, cache_manager, rate_limiter)
        
        self.logger.info("✅ BirdeyeAPI initialized for relaxed filter testing")
        return birdeye_api


async def main():
    """Main function to test relaxed strategies."""
    
    print("🎯 Starting Relaxed Strategy Filter Testing")
    print("This will test all 6 strategies with systematically relaxed filters")
    print("to improve token discovery rates.\n")
    
    tester = RelaxedStrategyTester()
    results = await tester.test_relaxed_strategies()
    
    print("\n✅ Relaxed filter testing complete!")
    print("Check scripts/results/ for detailed test results.")
    
    return results


if __name__ == "__main__":
    asyncio.run(main()) 