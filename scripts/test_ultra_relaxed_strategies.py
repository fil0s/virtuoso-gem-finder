#!/usr/bin/env python3
"""
Test Ultra-Relaxed Strategy Configurations

This script applies even more aggressive filter relaxations to the 4 strategies
that still found 0 tokens in the previous relaxation test.

Target Strategies:
- Recent Listings Strategy
- Price Momentum Strategy  
- Liquidity Growth Strategy
- Smart Money Whale Strategy
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
    RecentListingsStrategy,
    PriceMomentumStrategy,
    LiquidityGrowthStrategy,
    SmartMoneyWhaleStrategy
)
from api.birdeye_connector import BirdeyeAPI
from core.cache_manager import CacheManager
from services.rate_limiter_service import RateLimiterService
from services.logger_setup import LoggerSetup


class UltraRelaxedStrategyTester:
    """Test strategies with ultra-relaxed configurations."""
    
    def __init__(self):
        """Initialize the ultra-relaxed strategy tester."""
        self.logger_setup = LoggerSetup("UltraRelaxedTester")
        self.logger = self.logger_setup.logger
        self.test_timestamp = int(time.time())
        
        # Ultra-relaxed configurations
        self.ultra_relaxed_configs = {
            "Recent Listings Strategy": {
                "api_parameters": {
                    "sort_by": "created_time",
                    "sort_type": "desc", 
                    "min_liquidity": 5000,       # Ultra-relaxed from 50000 (90% reduction)
                    "min_volume_24h_usd": 1000,  # Ultra-relaxed from 10000 (90% reduction)
                    "min_holder": 25,            # Ultra-relaxed from 100 (75% reduction)
                    "limit": 50                  # Increased from 25
                },
                "min_consecutive_appearances": 1,  # Ultra-relaxed from 2
                "processing_relaxations": {
                    "age_limit_hours": 168,      # 7 days instead of 24 hours
                    "holder_concentration_threshold": 0.8,  # Relaxed from 0.6
                    "min_trade_count": 5,        # Ultra-relaxed from 50
                    "suspicious_volume_multiplier": 15.0    # Ultra-relaxed from 5.0
                }
            },
            
            "Price Momentum Strategy": {
                "api_parameters": {
                    "sort_by": "price_change_24h_percent",
                    "sort_type": "desc",
                    "min_liquidity": 10000,      # Ultra-relaxed from 75000 (87% reduction)
                    "min_volume_24h_usd": 5000,  # Ultra-relaxed from 30000 (83% reduction)
                    "min_holder": 50,            # Ultra-relaxed from 300 (83% reduction)
                    "limit": 50                  # Increased from 25
                },
                "min_consecutive_appearances": 1,  # Ultra-relaxed from 2
                "processing_relaxations": {
                    "min_price_change": 5.0,     # Ultra-relaxed from 20.0
                    "max_price_change": 2000.0,  # Ultra-relaxed from 500.0
                    "holder_concentration_threshold": 0.8,  # Relaxed from 0.6
                    "suspicious_volume_multiplier": 15.0    # Ultra-relaxed from 5.0
                }
            },
            
            "Liquidity Growth Strategy": {
                "api_parameters": {
                    "sort_by": "liquidity",
                    "sort_type": "desc",
                    "min_liquidity": 15000,      # Ultra-relaxed from 120000 (87% reduction)
                    "min_volume_24h_usd": 8000,  # Ultra-relaxed from 60000 (87% reduction)
                    "min_holder": 75,            # Ultra-relaxed from 600 (87% reduction)
                    "limit": 50                  # Increased from 25
                },
                "min_consecutive_appearances": 1,  # Ultra-relaxed from 2
                "processing_relaxations": {
                    "min_liquidity_growth": 10.0,  # Ultra-relaxed from 50.0
                    "min_market_cap": 50000,       # Ultra-relaxed from 1000000
                    "holder_concentration_threshold": 0.8,  # Relaxed from 0.6
                    "suspicious_volume_multiplier": 15.0    # Ultra-relaxed from 5.0
                }
            },
            
            "Smart Money Whale Strategy": {
                "api_parameters": {
                    "sort_by": "volume_24h",
                    "sort_type": "desc",
                    "min_liquidity": 20000,      # Ultra-relaxed from 200000 (90% reduction)
                    "min_volume_24h_usd": 15000, # Ultra-relaxed from 100000 (85% reduction)
                    "min_holder": 100,           # Ultra-relaxed from 1000 (90% reduction)
                    "limit": 50                  # Increased from 20
                },
                "min_consecutive_appearances": 1,  # Ultra-relaxed from 2
                "processing_relaxations": {
                    "min_whale_threshold": 5000,    # Ultra-relaxed from 50000
                    "min_smart_money_score": 0.1,   # Ultra-relaxed from 0.3
                    "min_trader_count": 3,          # Ultra-relaxed from 10
                    "holder_concentration_threshold": 0.8,  # Relaxed from 0.6
                    "suspicious_volume_multiplier": 15.0    # Ultra-relaxed from 5.0
                }
            }
        }
    
    async def initialize_api(self) -> BirdeyeAPI:
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
            'rate_limit': 100,
            'request_timeout_seconds': 20,
            'cache_ttl_default_seconds': 300,
            'cache_ttl_error_seconds': 60,
            'max_retries': 3,
            'backoff_factor': 2
        }
        
        birdeye_api = BirdeyeAPI(config, self.logger, cache_manager, rate_limiter)
        self.logger.info("✅ BirdeyeAPI initialized successfully")
        return birdeye_api
    
    async def test_ultra_relaxed_strategies(self):
        """Test all strategies with ultra-relaxed configurations."""
        
        self.logger.info("🚀 TESTING ULTRA-RELAXED STRATEGY CONFIGURATIONS")
        print("🚀 TESTING ULTRA-RELAXED STRATEGY CONFIGURATIONS")
        print("=" * 80)
        
        # Initialize API
        birdeye_api = await self.initialize_api()
        scan_id = f"ultra_relaxed_test_{self.test_timestamp}"
        
        # Test results storage
        test_results = {
            "test_metadata": {
                "timestamp": self.test_timestamp,
                "test_date": datetime.fromtimestamp(self.test_timestamp).isoformat(),
                "scan_id": scan_id,
                "configuration_level": "ultra_relaxed"
            },
            "strategy_results": {},
            "summary": {}
        }
        
        # Test each strategy
        strategies_to_test = [
            (RecentListingsStrategy, "Recent Listings Strategy"),
            (PriceMomentumStrategy, "Price Momentum Strategy"),
            (LiquidityGrowthStrategy, "Liquidity Growth Strategy"),
            (SmartMoneyWhaleStrategy, "Smart Money Whale Strategy")
        ]
        
        total_tokens_found = 0
        successful_strategies = 0
        
        for i, (strategy_class, strategy_name) in enumerate(strategies_to_test, 1):
            print(f"\n🔬 [{i}/4] Testing {strategy_name} with Ultra-Relaxed Config")
            print("-" * 60)
            
            try:
                # Create strategy with ultra-relaxed config
                strategy = await self._create_ultra_relaxed_strategy(strategy_class, strategy_name)
                
                # Capture API stats before
                pre_api_stats = birdeye_api.get_api_call_statistics()
                start_time = time.time()
                
                # Execute strategy
                tokens = await strategy.execute(birdeye_api, scan_id=f"{scan_id}_{strategy_name.lower().replace(' ', '_')}")
                execution_time = time.time() - start_time
                
                # Capture API stats after
                post_api_stats = birdeye_api.get_api_call_statistics()
                api_calls_made = post_api_stats['total_api_calls'] - pre_api_stats['total_api_calls']
                
                # Store results
                test_results["strategy_results"][strategy_name] = {
                    "success": True,
                    "tokens_found": len(tokens),
                    "execution_time": execution_time,
                    "api_calls_made": api_calls_made,
                    "tokens_per_api_call": len(tokens) / api_calls_made if api_calls_made > 0 else 0,
                    "config_applied": self.ultra_relaxed_configs[strategy_name],
                    "sample_tokens": tokens[:3] if tokens else []  # Store sample for analysis
                }
                
                total_tokens_found += len(tokens)
                if len(tokens) > 0:
                    successful_strategies += 1
                
                # Log results
                print(f"✅ {strategy_name}: {len(tokens)} tokens found in {execution_time:.2f}s")
                print(f"   📡 API calls: {api_calls_made}, Efficiency: {len(tokens) / api_calls_made if api_calls_made > 0 else 0:.2f} tokens/call")
                
                if len(tokens) > 0:
                    print(f"   🎯 SUCCESS! Ultra-relaxed config worked for {strategy_name}")
                    # Show sample token
                    sample = tokens[0]
                    print(f"   📊 Sample token: {sample.get('symbol', 'Unknown')} (Score: {sample.get('score', 0):.1f})")
                else:
                    print(f"   ⚠️  Still 0 tokens - may need even more aggressive relaxation")
                
            except Exception as e:
                print(f"❌ {strategy_name} failed: {e}")
                test_results["strategy_results"][strategy_name] = {
                    "success": False,
                    "error": str(e),
                    "tokens_found": 0,
                    "execution_time": 0,
                    "api_calls_made": 0
                }
        
        # Generate summary
        test_results["summary"] = {
            "total_strategies_tested": len(strategies_to_test),
            "successful_strategies": successful_strategies,
            "total_tokens_found": total_tokens_found,
            "success_rate": successful_strategies / len(strategies_to_test),
            "avg_tokens_per_successful_strategy": total_tokens_found / successful_strategies if successful_strategies > 0 else 0,
            "improvement_analysis": self._analyze_improvement(test_results["strategy_results"])
        }
        
        # Save results
        await self._save_test_results(test_results)
        
        # Print summary
        print("\n" + "=" * 80)
        print("📊 ULTRA-RELAXED CONFIGURATION TEST SUMMARY")
        print("=" * 80)
        print(f"🎯 Successful strategies: {successful_strategies}/4")
        print(f"📈 Total tokens discovered: {total_tokens_found}")
        print(f"⚡ Success rate: {successful_strategies/4:.1%}")
        
        if successful_strategies > 0:
            print(f"\n🏆 BREAKTHROUGHS:")
            for strategy_name, result in test_results["strategy_results"].items():
                if result.get("success") and result.get("tokens_found", 0) > 0:
                    print(f"  ✅ {strategy_name}: {result['tokens_found']} tokens")
        
        remaining_failed = 4 - successful_strategies
        if remaining_failed > 0:
            print(f"\n🔧 STILL NEED WORK:")
            for strategy_name, result in test_results["strategy_results"].items():
                if not result.get("success") or result.get("tokens_found", 0) == 0:
                    print(f"  ⚠️  {strategy_name}: Needs extreme relaxation or different approach")
        
        return test_results
    
    async def _create_ultra_relaxed_strategy(self, strategy_class, strategy_name):
        """Create a strategy instance with ultra-relaxed configuration."""
        
        # Get ultra-relaxed config
        config = self.ultra_relaxed_configs[strategy_name]
        
        # Create strategy instance
        strategy = strategy_class(logger=self.logger)
        
        # Apply ultra-relaxed API parameters
        strategy.api_parameters.update(config["api_parameters"])
        
        # Apply ultra-relaxed consecutive appearances
        strategy.min_consecutive_appearances = config["min_consecutive_appearances"]
        
        # Apply ultra-relaxed processing parameters
        processing_relaxations = config.get("processing_relaxations", {})
        
        # Update risk management with relaxed thresholds
        if hasattr(strategy, 'risk_management'):
            for key, value in processing_relaxations.items():
                if key in strategy.risk_management:
                    strategy.risk_management[key] = value
        
        # Add processing relaxations as attributes for custom processing
        for key, value in processing_relaxations.items():
            setattr(strategy, f"ultra_relaxed_{key}", value)
        
        self.logger.info(f"🔧 Applied ultra-relaxed config to {strategy_name}")
        return strategy
    
    def _analyze_improvement(self, strategy_results):
        """Analyze improvement from ultra-relaxed configurations."""
        
        improvements = {}
        
        # Previous results (from relaxed test) - all found 0 tokens
        previous_results = {
            "Recent Listings Strategy": 0,
            "Price Momentum Strategy": 0,
            "Liquidity Growth Strategy": 0,
            "Smart Money Whale Strategy": 0
        }
        
        for strategy_name, result in strategy_results.items():
            if result.get("success"):
                current_tokens = result.get("tokens_found", 0)
                previous_tokens = previous_results.get(strategy_name, 0)
                
                if current_tokens > previous_tokens:
                    improvements[strategy_name] = {
                        "previous": previous_tokens,
                        "current": current_tokens,
                        "improvement": "BREAKTHROUGH" if previous_tokens == 0 else f"+{current_tokens - previous_tokens}",
                        "status": "SUCCESS"
                    }
                else:
                    improvements[strategy_name] = {
                        "previous": previous_tokens,
                        "current": current_tokens,
                        "improvement": "No improvement",
                        "status": "NEEDS_MORE_WORK"
                    }
            else:
                improvements[strategy_name] = {
                    "previous": 0,
                    "current": 0,
                    "improvement": "Failed to execute",
                    "status": "ERROR"
                }
        
        return improvements
    
    async def _save_test_results(self, test_results):
        """Save test results to file."""
        try:
            # Create results directory
            results_dir = Path("scripts/results")
            results_dir.mkdir(exist_ok=True)
            
            # Save results
            timestamp_str = datetime.fromtimestamp(self.test_timestamp).strftime("%Y%m%d_%H%M%S")
            results_file = results_dir / f"ultra_relaxed_strategy_test_{timestamp_str}.json"
            
            with open(results_file, 'w') as f:
                json.dump(test_results, f, indent=2, default=str)
            
            self.logger.info(f"💾 Test results saved to: {results_file}")
            
        except Exception as e:
            self.logger.error(f"Error saving test results: {e}")


async def main():
    """Main function to run ultra-relaxed strategy testing."""
    print("🚀 Starting Ultra-Relaxed Strategy Configuration Testing")
    print("=" * 80)
    
    try:
        tester = UltraRelaxedStrategyTester()
        results = await tester.test_ultra_relaxed_strategies()
        
        print("\n✅ Ultra-relaxed configuration testing complete!")
        return results
        
    except Exception as e:
        print(f"❌ Error in ultra-relaxed testing: {e}")
        raise


if __name__ == "__main__":
    asyncio.run(main()) 