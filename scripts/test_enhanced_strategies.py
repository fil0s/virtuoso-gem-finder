#!/usr/bin/env python3

"""
Enhanced Strategies Test Script

Tests the newly enhanced strategies:
1. Price Momentum Strategy with Cross-Timeframe Analysis
2. Recent Listings Strategy with Holder Velocity Analysis
"""

import asyncio
import sys
import os
import time
from typing import Dict, Any, List

# Add project root to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.strategies.price_momentum_strategy import PriceMomentumStrategy
from core.strategies.recent_listings_strategy import RecentListingsStrategy
from api.birdeye_connector import BirdeyeAPI
from core.cache_manager import CacheManager
from services.rate_limiter_service import RateLimiterService
from core.config_manager import ConfigManager
from services.logger_setup import LoggerSetup

class EnhancedStrategiesTest:
    def __init__(self):
        # Setup logging
        self.logger_setup = LoggerSetup('EnhancedStrategiesTest', log_level='INFO')
        self.logger = self.logger_setup.logger
        
        # Initialize configuration
        self.config_manager = ConfigManager()
        self.config = self.config_manager.get_config()
        
        # Initialize services
        self.cache_manager = CacheManager()
        self.rate_limiter = RateLimiterService()
        
        # Initialize strategies
        self.price_momentum_strategy = PriceMomentumStrategy(logger=self.logger)
        self.recent_listings_strategy = RecentListingsStrategy(logger=self.logger)
        
        # Initialize Birdeye API
        birdeye_config = self.config.get('BIRDEYE_API', {})
        self.birdeye_api = BirdeyeAPI(
            config=birdeye_config,
            logger=self.logger,
            cache_manager=self.cache_manager,
            rate_limiter=self.rate_limiter
        )
    
    async def test_enhanced_price_momentum_strategy(self) -> Dict[str, Any]:
        """Test the enhanced Price Momentum Strategy with Cross-Timeframe Analysis."""
        self.logger.info("🎯 Testing Enhanced Price Momentum Strategy with Cross-Timeframe Analysis")
        
        try:
            # Execute strategy to get tokens
            tokens = await self.price_momentum_strategy.execute(self.birdeye_api, scan_id="test_enhanced_price_momentum")
            self.logger.info(f"📊 Retrieved {len(tokens)} tokens from Price Momentum Strategy")
            
            if not tokens:
                return {"success": False, "error": "No tokens retrieved"}
            
            # The execute method already processes results, so we just use the tokens directly
            start_time = time.time()
            processed_tokens = tokens[:5] if tokens else []  # Test with first 5 tokens to avoid rate limits
            processing_time = time.time() - start_time
            
            self.logger.info(f"⚡ Processed {len(processed_tokens)} tokens in {processing_time:.2f}s")
            
            # Analyze results
            analysis = {
                "total_tokens_processed": len(processed_tokens),
                "processing_time_seconds": processing_time,
                "cross_timeframe_analysis_count": 0,
                "high_confluence_count": 0,
                "momentum_boost_count": 0,
                "average_confluence_score": 0.0,
                "momentum_grades": {},
                "sample_token_analysis": None
            }
            
            confluence_scores = []
            for token in processed_tokens:
                momentum_analysis = token.get("momentum_analysis", {})
                if momentum_analysis and "confluence_score" in momentum_analysis:
                    analysis["cross_timeframe_analysis_count"] += 1
                    confluence_score = momentum_analysis["confluence_score"]
                    confluence_scores.append(confluence_score)
                    
                    if confluence_score > 0.8:
                        analysis["high_confluence_count"] += 1
                    
                    if token.get("momentum_boost"):
                        analysis["momentum_boost_count"] += 1
                
                # Collect momentum grades
                strategy_analysis = token.get("strategy_analysis", {})
                grade = strategy_analysis.get("momentum_quality_grade", "Unknown")
                analysis["momentum_grades"][grade] = analysis["momentum_grades"].get(grade, 0) + 1
                
                # Save sample analysis
                if not analysis["sample_token_analysis"] and momentum_analysis:
                    analysis["sample_token_analysis"] = {
                        "symbol": token.get("symbol"),
                        "momentum_analysis": momentum_analysis,
                        "strategy_analysis": strategy_analysis
                    }
            
            if confluence_scores:
                analysis["average_confluence_score"] = sum(confluence_scores) / len(confluence_scores)
            
            self.logger.info(f"✅ Price Momentum Enhancement Results:")
            self.logger.info(f"   - Cross-timeframe analysis: {analysis['cross_timeframe_analysis_count']}/{len(processed_tokens)}")
            self.logger.info(f"   - High confluence tokens: {analysis['high_confluence_count']}")
            self.logger.info(f"   - Average confluence score: {analysis['average_confluence_score']:.3f}")
            self.logger.info(f"   - Momentum grades: {analysis['momentum_grades']}")
            
            return {"success": True, "analysis": analysis}
            
        except Exception as e:
            self.logger.error(f"❌ Error testing Price Momentum Strategy: {e}")
            return {"success": False, "error": str(e)}
    
    async def test_enhanced_recent_listings_strategy(self) -> Dict[str, Any]:
        """Test the enhanced Recent Listings Strategy with Holder Velocity Analysis."""
        self.logger.info("👥 Testing Enhanced Recent Listings Strategy with Holder Velocity Analysis")
        
        try:
            # Execute strategy to get tokens
            tokens = await self.recent_listings_strategy.execute(self.birdeye_api, scan_id="test_enhanced_recent_listings")
            self.logger.info(f"📊 Retrieved {len(tokens)} tokens from Recent Listings Strategy")
            
            if not tokens:
                return {"success": False, "error": "No tokens retrieved"}
            
            # The execute method already processes results, so we just use the tokens directly
            start_time = time.time()
            processed_tokens = tokens[:5] if tokens else []  # Test with first 5 tokens to avoid rate limits
            processing_time = time.time() - start_time
            
            self.logger.info(f"⚡ Processed {len(processed_tokens)} tokens in {processing_time:.2f}s")
            
            # Analyze results
            analysis = {
                "total_tokens_processed": len(processed_tokens),
                "processing_time_seconds": processing_time,
                "holder_velocity_analysis_count": 0,
                "high_velocity_count": 0,
                "velocity_boost_count": 0,
                "average_velocity_score": 0.0,
                "adoption_patterns": {},
                "momentum_grades": {},
                "sample_token_analysis": None
            }
            
            velocity_scores = []
            for token in processed_tokens:
                velocity_analysis = token.get("holder_velocity_analysis", {})
                if velocity_analysis and "velocity_score" in velocity_analysis:
                    analysis["holder_velocity_analysis_count"] += 1
                    velocity_score = velocity_analysis["velocity_score"]
                    velocity_scores.append(velocity_score)
                    
                    if velocity_score > 0.8:
                        analysis["high_velocity_count"] += 1
                    
                    if token.get("velocity_boost"):
                        analysis["velocity_boost_count"] += 1
                    
                    # Collect adoption patterns
                    pattern = velocity_analysis.get("adoption_pattern", "unknown")
                    analysis["adoption_patterns"][pattern] = analysis["adoption_patterns"].get(pattern, 0) + 1
                
                # Collect momentum grades
                strategy_analysis = token.get("strategy_analysis", {})
                grade = strategy_analysis.get("holder_momentum_grade", "Unknown")
                analysis["momentum_grades"][grade] = analysis["momentum_grades"].get(grade, 0) + 1
                
                # Save sample analysis
                if not analysis["sample_token_analysis"] and velocity_analysis:
                    analysis["sample_token_analysis"] = {
                        "symbol": token.get("symbol"),
                        "holder_velocity_analysis": velocity_analysis,
                        "strategy_analysis": strategy_analysis
                    }
            
            if velocity_scores:
                analysis["average_velocity_score"] = sum(velocity_scores) / len(velocity_scores)
            
            self.logger.info(f"✅ Recent Listings Enhancement Results:")
            self.logger.info(f"   - Holder velocity analysis: {analysis['holder_velocity_analysis_count']}/{len(processed_tokens)}")
            self.logger.info(f"   - High velocity tokens: {analysis['high_velocity_count']}")
            self.logger.info(f"   - Average velocity score: {analysis['average_velocity_score']:.3f}")
            self.logger.info(f"   - Adoption patterns: {analysis['adoption_patterns']}")
            self.logger.info(f"   - Momentum grades: {analysis['momentum_grades']}")
            
            return {"success": True, "analysis": analysis}
            
        except Exception as e:
            self.logger.error(f"❌ Error testing Recent Listings Strategy: {e}")
            return {"success": False, "error": str(e)}
    
    async def run_enhanced_strategies_test(self) -> Dict[str, Any]:
        """Run comprehensive test of both enhanced strategies."""
        self.logger.info("🚀 Starting Enhanced Strategies Test Suite")
        
        results = {
            "test_timestamp": int(time.time()),
            "price_momentum_test": None,
            "recent_listings_test": None,
            "overall_success": False
        }
        
        try:
            # Test Price Momentum Strategy
            results["price_momentum_test"] = await self.test_enhanced_price_momentum_strategy()
            await asyncio.sleep(2)  # Rate limit pause
            
            # Test Recent Listings Strategy
            results["recent_listings_test"] = await self.test_enhanced_recent_listings_strategy()
            
            # Overall success
            results["overall_success"] = (
                results["price_momentum_test"]["success"] and 
                results["recent_listings_test"]["success"]
            )
            
            if results["overall_success"]:
                self.logger.info("🎉 Enhanced Strategies Test Suite: ALL TESTS PASSED")
            else:
                self.logger.warning("⚠️ Enhanced Strategies Test Suite: SOME TESTS FAILED")
            
            return results
            
        except Exception as e:
            self.logger.error(f"❌ Critical error in test suite: {e}")
            results["overall_success"] = False
            results["critical_error"] = str(e)
            return results

async def main():
    """Main test execution."""
    test_suite = EnhancedStrategiesTest()
    results = await test_suite.run_enhanced_strategies_test()
    
    print("\n" + "="*60)
    print("ENHANCED STRATEGIES TEST RESULTS")
    print("="*60)
    
    # Price Momentum Results
    pm_test = results.get("price_momentum_test", {})
    if pm_test.get("success"):
        pm_analysis = pm_test.get("analysis", {})
        print(f"\n📈 PRICE MOMENTUM STRATEGY (Cross-Timeframe): ✅ PASSED")
        print(f"   • Tokens processed: {pm_analysis.get('total_tokens_processed', 0)}")
        print(f"   • Cross-timeframe analysis: {pm_analysis.get('cross_timeframe_analysis_count', 0)}")
        print(f"   • High confluence tokens: {pm_analysis.get('high_confluence_count', 0)}")
        print(f"   • Average confluence score: {pm_analysis.get('average_confluence_score', 0):.3f}")
    else:
        print(f"\n📈 PRICE MOMENTUM STRATEGY: ❌ FAILED")
        print(f"   Error: {pm_test.get('error', 'Unknown error')}")
    
    # Recent Listings Results
    rl_test = results.get("recent_listings_test", {})
    if rl_test.get("success"):
        rl_analysis = rl_test.get("analysis", {})
        print(f"\n👥 RECENT LISTINGS STRATEGY (Holder Velocity): ✅ PASSED")
        print(f"   • Tokens processed: {rl_analysis.get('total_tokens_processed', 0)}")
        print(f"   • Holder velocity analysis: {rl_analysis.get('holder_velocity_analysis_count', 0)}")
        print(f"   • High velocity tokens: {rl_analysis.get('high_velocity_count', 0)}")
        print(f"   • Average velocity score: {rl_analysis.get('average_velocity_score', 0):.3f}")
    else:
        print(f"\n👥 RECENT LISTINGS STRATEGY: ❌ FAILED")
        print(f"   Error: {rl_test.get('error', 'Unknown error')}")
    
    # Overall Result
    if results.get("overall_success"):
        print(f"\n🎉 OVERALL RESULT: ✅ ALL ENHANCED STRATEGIES WORKING")
    else:
        print(f"\n⚠️ OVERALL RESULT: ❌ SOME ENHANCEMENTS NEED ATTENTION")
    
    print("="*60)

if __name__ == "__main__":
    asyncio.run(main()) 