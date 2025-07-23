#!/usr/bin/env python3
"""
Test Strategy Fixes

This script tests the fixes for:
1. Price Momentum Strategy - graduated price change thresholds
2. Smart Money Whale Strategy - relaxed thresholds

Both strategies should now be able to discover tokens.
"""

import os
import sys
import asyncio
import json
import time
import logging
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Any

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from api.birdeye_connector import BirdeyeAPI
from services.logger_setup import LoggerSetup
from utils.structured_logger import get_structured_logger

# Import the fixed strategies
from core.strategies.price_momentum_strategy import PriceMomentumStrategy
from core.strategies.smart_money_whale_strategy import SmartMoneyWhaleStrategy


class StrategyFixTester:
    """Test the fixes for Price Momentum and Smart Money Whale strategies."""
    
    def __init__(self):
        """Initialize the strategy fix tester."""
        self.logger_setup = LoggerSetup("StrategyFixTester")
        self.logger = self.logger_setup.logger
        self.structured_logger = get_structured_logger('StrategyFixTester')
        
        # Test configuration
        self.test_timestamp = int(time.time())
        self.test_results = {}
        
    async def run_strategy_fix_tests(self) -> Dict[str, Any]:
        """Run tests for both fixed strategies."""
        self.logger.info("🔧 Starting Strategy Fix Tests")
        self.logger.info("=" * 70)
        
        # Initialize Birdeye API
        birdeye_api = await self._initialize_birdeye_api()
        scan_id = f"strategy_fix_test_{self.test_timestamp}"
        
        try:
            # Test 1: Price Momentum Strategy
            self.logger.info("🎯 Test 1: Price Momentum Strategy (Graduated Thresholds)")
            price_momentum_results = await self._test_price_momentum_strategy(birdeye_api, scan_id)
            
            # Test 2: Smart Money Whale Strategy
            self.logger.info("🐋 Test 2: Smart Money Whale Strategy (Relaxed Thresholds)")
            smart_money_whale_results = await self._test_smart_money_whale_strategy(birdeye_api, scan_id)
            
            # Compile final results
            final_results = {
                "test_metadata": {
                    "timestamp": self.test_timestamp,
                    "test_date": datetime.fromtimestamp(self.test_timestamp).isoformat(),
                    "scan_id": scan_id
                },
                "price_momentum_strategy": price_momentum_results,
                "smart_money_whale_strategy": smart_money_whale_results,
                "summary": self._generate_test_summary(price_momentum_results, smart_money_whale_results)
            }
            
            # Save results
            await self._save_test_results(final_results)
            
            return final_results
            
        except Exception as e:
            self.logger.error(f"❌ Error in strategy fix tests: {e}")
            raise
    
    async def _initialize_birdeye_api(self) -> BirdeyeAPI:
        """Initialize BirdeyeAPI with required dependencies."""
        import os
        from core.cache_manager import CacheManager
        from services.rate_limiter_service import RateLimiterService
        
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
        
        # Create logger for BirdeyeAPI
        birdeye_logger = LoggerSetup("BirdeyeAPI")
        birdeye_api = BirdeyeAPI(config, birdeye_logger, cache_manager, rate_limiter)
        
        self.logger.info("✅ BirdeyeAPI initialized successfully")
        return birdeye_api
    
    async def _test_price_momentum_strategy(self, birdeye_api: BirdeyeAPI, scan_id: str) -> Dict[str, Any]:
        """Test the fixed Price Momentum Strategy."""
        start_time = time.time()
        
        try:
            # Initialize strategy
            strategy = PriceMomentumStrategy(logger=self.logger)
            
            # Execute strategy
            tokens = await strategy.execute(birdeye_api, scan_id=f"{scan_id}_price_momentum")
            execution_time = time.time() - start_time
            
            # Analyze results
            analysis = self._analyze_price_momentum_results(tokens)
            
            results = {
                "execution_successful": True,
                "tokens_found": len(tokens),
                "execution_time": execution_time,
                "analysis": analysis,
                "sample_tokens": tokens[:3] if tokens else [],  # First 3 tokens for inspection
                "error": None
            }
            
            self.logger.info(f"✅ Price Momentum Strategy: {len(tokens)} tokens found in {execution_time:.2f}s")
            
            if tokens:
                # Show graduated threshold examples
                for token in tokens[:3]:
                    strategy_analysis = token.get("strategy_analysis", {})
                    symbol = token.get("symbol", "Unknown")
                    actual_change = strategy_analysis.get("actual_price_change", 0)
                    max_allowed = strategy_analysis.get("max_allowed_price_change", 0)
                    market_cap = token.get("marketCap", 0)
                    
                    self.logger.info(f"   📊 {symbol}: {actual_change:.1f}% change (max: {max_allowed:.1f}%, mcap: ${market_cap:,.0f})")
            
            return results
            
        except Exception as e:
            execution_time = time.time() - start_time
            self.logger.error(f"❌ Price Momentum Strategy failed: {e}")
            
            return {
                "execution_successful": False,
                "tokens_found": 0,
                "execution_time": execution_time,
                "analysis": {},
                "sample_tokens": [],
                "error": str(e)
            }
    
    async def _test_smart_money_whale_strategy(self, birdeye_api: BirdeyeAPI, scan_id: str) -> Dict[str, Any]:
        """Test the fixed Smart Money Whale Strategy."""
        start_time = time.time()
        
        try:
            # Initialize strategy
            strategy = SmartMoneyWhaleStrategy(logger=self.logger)
            
            # Execute strategy
            tokens = await strategy.execute(birdeye_api, scan_id=f"{scan_id}_smart_money_whale")
            execution_time = time.time() - start_time
            
            # Analyze results
            analysis = self._analyze_smart_money_whale_results(tokens)
            
            results = {
                "execution_successful": True,
                "tokens_found": len(tokens),
                "execution_time": execution_time,
                "analysis": analysis,
                "sample_tokens": tokens[:3] if tokens else [],  # First 3 tokens for inspection
                "error": None,
                "relaxed_thresholds": strategy.whale_smart_money_criteria
            }
            
            self.logger.info(f"✅ Smart Money Whale Strategy: {len(tokens)} tokens found in {execution_time:.2f}s")
            
            if tokens:
                # Show threshold examples
                for token in tokens[:3]:
                    symbol = token.get("symbol", "Unknown")
                    whale_analysis = token.get("whale_analysis", {})
                    smart_money_analysis = token.get("smart_money_analysis", {})
                    
                    whale_count = len(whale_analysis.get("whales", []))
                    smart_traders = smart_money_analysis.get("skill_metrics", {}).get("skilled_count", 0)
                    confluence = token.get("confluence_score", 0)
                    
                    self.logger.info(f"   🐋 {symbol}: {whale_count} whales, {smart_traders} skilled traders, {confluence:.2f} confluence")
            
            return results
            
        except Exception as e:
            execution_time = time.time() - start_time
            self.logger.error(f"❌ Smart Money Whale Strategy failed: {e}")
            
            return {
                "execution_successful": False,
                "tokens_found": 0,
                "execution_time": execution_time,
                "analysis": {},
                "sample_tokens": [],
                "error": str(e),
                "relaxed_thresholds": {}
            }
    
    def _analyze_price_momentum_results(self, tokens: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Analyze Price Momentum Strategy results."""
        if not tokens:
            return {"token_count": 0}
        
        # Analyze graduated thresholds usage
        threshold_usage = {"micro": 0, "small": 0, "medium": 0, "large": 0}
        price_changes = []
        market_caps = []
        
        for token in tokens:
            strategy_analysis = token.get("strategy_analysis", {})
            max_allowed = strategy_analysis.get("max_allowed_price_change", 0)
            actual_change = strategy_analysis.get("actual_price_change", 0)
            market_cap = token.get("marketCap", 0)
            
            price_changes.append(actual_change)
            market_caps.append(market_cap)
            
            # Categorize by threshold tier
            if max_allowed >= 2000:
                threshold_usage["micro"] += 1
            elif max_allowed >= 1000:
                threshold_usage["small"] += 1
            elif max_allowed >= 500:
                threshold_usage["medium"] += 1
            else:
                threshold_usage["large"] += 1
        
        return {
            "token_count": len(tokens),
            "threshold_tier_usage": threshold_usage,
            "price_change_stats": {
                "min": min(price_changes) if price_changes else 0,
                "max": max(price_changes) if price_changes else 0,
                "avg": sum(price_changes) / len(price_changes) if price_changes else 0
            },
            "market_cap_stats": {
                "min": min(market_caps) if market_caps else 0,
                "max": max(market_caps) if market_caps else 0,
                "avg": sum(market_caps) / len(market_caps) if market_caps else 0
            },
            "graduated_thresholds_working": any(max_allowed > 50 for max_allowed in 
                                              [t.get("strategy_analysis", {}).get("max_allowed_price_change", 0) for t in tokens])
        }
    
    def _analyze_smart_money_whale_results(self, tokens: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Analyze Smart Money Whale Strategy results."""
        if not tokens:
            return {"token_count": 0}
        
        whale_counts = []
        smart_trader_counts = []
        confluence_scores = []
        
        for token in tokens:
            whale_analysis = token.get("whale_analysis", {})
            smart_money_analysis = token.get("smart_money_analysis", {})
            
            whale_count = len(whale_analysis.get("whales", []))
            smart_traders = smart_money_analysis.get("skill_metrics", {}).get("skilled_count", 0)
            confluence = token.get("confluence_score", 0)
            
            whale_counts.append(whale_count)
            smart_trader_counts.append(smart_traders)
            confluence_scores.append(confluence)
        
        return {
            "token_count": len(tokens),
            "whale_stats": {
                "min": min(whale_counts) if whale_counts else 0,
                "max": max(whale_counts) if whale_counts else 0,
                "avg": sum(whale_counts) / len(whale_counts) if whale_counts else 0
            },
            "smart_trader_stats": {
                "min": min(smart_trader_counts) if smart_trader_counts else 0,
                "max": max(smart_trader_counts) if smart_trader_counts else 0,
                "avg": sum(smart_trader_counts) / len(smart_trader_counts) if smart_trader_counts else 0
            },
            "confluence_stats": {
                "min": min(confluence_scores) if confluence_scores else 0,
                "max": max(confluence_scores) if confluence_scores else 0,
                "avg": sum(confluence_scores) / len(confluence_scores) if confluence_scores else 0
            },
            "relaxed_thresholds_working": len(tokens) > 0
        }
    
    def _generate_test_summary(self, price_momentum_results: Dict[str, Any], 
                              smart_money_whale_results: Dict[str, Any]) -> Dict[str, Any]:
        """Generate test summary."""
        
        # Overall success
        both_successful = (price_momentum_results["execution_successful"] and 
                          smart_money_whale_results["execution_successful"])
        
        # Token discovery
        total_tokens = price_momentum_results["tokens_found"] + smart_money_whale_results["tokens_found"]
        
        # Fix effectiveness
        price_momentum_fixed = (price_momentum_results["execution_successful"] and 
                               price_momentum_results["tokens_found"] > 0)
        smart_money_whale_fixed = (smart_money_whale_results["execution_successful"] and 
                                  smart_money_whale_results["tokens_found"] > 0)
        
        return {
            "overall_success": both_successful,
            "strategies_tested": 2,
            "strategies_successful": sum([price_momentum_results["execution_successful"], 
                                        smart_money_whale_results["execution_successful"]]),
            "total_tokens_discovered": total_tokens,
            "fixes_applied": {
                "price_momentum_strategy": {
                    "fix_type": "graduated_price_change_thresholds",
                    "fix_successful": price_momentum_fixed,
                    "tokens_found": price_momentum_results["tokens_found"]
                },
                "smart_money_whale_strategy": {
                    "fix_type": "relaxed_thresholds",
                    "fix_successful": smart_money_whale_fixed,
                    "tokens_found": smart_money_whale_results["tokens_found"]
                }
            },
            "fix_success_rate": sum([price_momentum_fixed, smart_money_whale_fixed]) / 2,
            "recommendation": "Both strategies fixed" if both_successful and total_tokens > 0 
                            else "Additional tuning may be needed"
        }
    
    async def _save_test_results(self, results: Dict[str, Any]):
        """Save test results to file."""
        try:
            # Create results directory
            results_dir = Path("scripts/results")
            results_dir.mkdir(exist_ok=True)
            
            # Save detailed results
            timestamp_str = datetime.fromtimestamp(self.test_timestamp).strftime("%Y%m%d_%H%M%S")
            results_file = results_dir / f"strategy_fix_test_{timestamp_str}.json"
            
            with open(results_file, 'w') as f:
                json.dump(results, f, indent=2, default=str)
            
            self.logger.info(f"📊 Test results saved to: {results_file}")
            
        except Exception as e:
            self.logger.error(f"Error saving test results: {e}")


async def main():
    """Main function to run strategy fix tests."""
    print("🔧 Starting Strategy Fix Tests")
    print("=" * 70)
    
    try:
        tester = StrategyFixTester()
        results = await tester.run_strategy_fix_tests()
        
        # Print summary to console
        print("\n" + "=" * 70)
        print("📊 STRATEGY FIX TEST RESULTS")
        print("=" * 70)
        
        summary = results["summary"]
        
        print(f"\n✅ Overall Success: {summary['overall_success']}")
        print(f"🎯 Strategies Tested: {summary['strategies_tested']}")
        print(f"📈 Total Tokens Discovered: {summary['total_tokens_discovered']}")
        print(f"🔧 Fix Success Rate: {summary['fix_success_rate']:.1%}")
        
        print(f"\n🎯 Price Momentum Strategy:")
        pm_fix = summary["fixes_applied"]["price_momentum_strategy"]
        print(f"   Fix Type: {pm_fix['fix_type']}")
        print(f"   Fix Successful: {pm_fix['fix_successful']}")
        print(f"   Tokens Found: {pm_fix['tokens_found']}")
        
        print(f"\n🐋 Smart Money Whale Strategy:")
        smw_fix = summary["fixes_applied"]["smart_money_whale_strategy"]
        print(f"   Fix Type: {smw_fix['fix_type']}")
        print(f"   Fix Successful: {smw_fix['fix_successful']}")
        print(f"   Tokens Found: {smw_fix['tokens_found']}")
        
        print(f"\n💡 Recommendation: {summary['recommendation']}")
        
        print("\n✅ Strategy fix tests complete! Check scripts/results/ for detailed results.")
        
    except Exception as e:
        print(f"❌ Error in main execution: {e}")
        raise


if __name__ == "__main__":
    asyncio.run(main()) 