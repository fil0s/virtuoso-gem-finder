#!/usr/bin/env python3
"""
Debug Whale/Shark Classification Script

This script tests the whale/shark classification logic with real trader data
to identify exactly why traders with $8M+ volumes are not being classified as whales.

Usage: python scripts/debug_whale_shark_classification.py
"""

import asyncio
import sys
import os
from typing import Dict, List, Any

# Add project root to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from api.birdeye_connector import BirdeyeAPI
from services.whale_shark_movement_tracker import WhaleSharkMovementTracker
from services.logger_setup import LoggerSetup


class WhaleSharkClassificationDebugger:
    """Debug whale/shark classification with real data"""
    
    def __init__(self):
        self.logger_setup = LoggerSetup("WhaleSharkDebugger")
        self.logger = self.logger_setup.logger
        self.birdeye_api = None
        self.whale_tracker = None
        
        # Test tokens with known high-volume traders
        self.test_tokens = [
            "9doRRAik5gvhbEwjbZDbZR6GxXSAfdoomyJR57xKpump",  # $51M total volume, $8.36M top trader
            "JosjEXh69RckgSs2AWsN1xN8zmiSHxBuJjHLURJnHhg",   # $59M total volume, $16.63M top trader
        ]
        
    async def initialize_services(self):
        """Initialize services"""
        try:
            self.logger.info("🔧 Initializing services...")
            
            # Initialize required components
            from core.config_manager import ConfigManager
            from core.cache_manager import CacheManager
            from services.rate_limiter_service import RateLimiterService
            
            config_manager = ConfigManager()
            config = config_manager.get_section("BIRDEYE_API")
            cache_manager = CacheManager()
            rate_limiter = RateLimiterService()
            
            # Initialize BirdEye API with all required parameters
            self.birdeye_api = BirdeyeAPI(config, self.logger, cache_manager, rate_limiter)
            self.whale_tracker = WhaleSharkMovementTracker(self.birdeye_api, self.logger)
            
            self.logger.info("✅ Services initialized successfully")
            return True
            
        except Exception as e:
            self.logger.error(f"❌ Failed to initialize services: {e}")
            return False
    
    async def debug_classification_logic(self, token_address: str):
        """Debug the classification logic step by step"""
        self.logger.info(f"\n🔍 DEBUGGING CLASSIFICATION FOR {token_address[:8]}...")
        self.logger.info("=" * 60)
        
        # Get raw trader data
        traders_data = await self.birdeye_api.get_top_traders_optimized(
            token_address=token_address,
            time_frame="24h",
            sort_by="volume",
            sort_type="desc",
            limit=10
        )
        
        if not traders_data:
            self.logger.error(f"❌ No trader data for {token_address[:8]}")
            return
        
        self.logger.info(f"📊 Got {len(traders_data)} traders")
        
        # Get classification thresholds
        thresholds = self.whale_tracker.classification_thresholds
        self.logger.info(f"\n🎯 Classification Thresholds:")
        self.logger.info(f"   whale_min_volume: ${thresholds['whale_min_volume']:,}")
        self.logger.info(f"   shark_min_volume: ${thresholds['shark_min_volume']:,}")
        self.logger.info(f"   min_trades: {thresholds['min_trades']}")
        self.logger.info(f"   whale_min_avg_trade: ${thresholds['whale_min_avg_trade']:,}")
        self.logger.info(f"   shark_min_avg_trade: ${thresholds['shark_min_avg_trade']:,}")
        
        # Test each trader
        whales_found = 0
        sharks_found = 0
        
        for i, trader in enumerate(traders_data, 1):
            self.logger.info(f"\n📈 TRADER {i}:")
            
            # Extract data
            volume = trader.get("volume", 0) or 0
            trade_count = trader.get("trade", 0) or 0
            trader_address = trader.get("owner", trader.get("address", "unknown"))
            
            # Calculate derived metrics
            avg_trade_size = volume / max(trade_count, 1)
            
            self.logger.info(f"   Address: {trader_address[:8]}...")
            self.logger.info(f"   Volume: ${volume:,.2f}")
            self.logger.info(f"   Trade Count: {trade_count}")
            self.logger.info(f"   Avg Trade Size: ${avg_trade_size:,.2f}")
            
            # Test classification step by step
            self.logger.info(f"   🔍 Classification Tests:")
            
            # Volume test
            if volume >= thresholds["whale_min_volume"]:
                self.logger.info(f"   ✅ Volume test: PASS (${volume:,.0f} >= ${thresholds['whale_min_volume']:,})")
                
                # Trade count test
                if trade_count >= thresholds["min_trades"]:
                    self.logger.info(f"   ✅ Min trades test: PASS ({trade_count} >= {thresholds['min_trades']})")
                    
                    # Avg trade size test
                    if avg_trade_size >= thresholds["whale_min_avg_trade"]:
                        self.logger.info(f"   ✅ Avg trade size test: PASS (${avg_trade_size:,.0f} >= ${thresholds['whale_min_avg_trade']:,})")
                        self.logger.info(f"   🐋 RESULT: WHALE")
                        whales_found += 1
                    else:
                        self.logger.info(f"   ❌ Avg trade size test: FAIL (${avg_trade_size:,.0f} < ${thresholds['whale_min_avg_trade']:,})")
                        self.logger.info(f"   🐟 RESULT: FISH (failed avg trade size)")
                else:
                    self.logger.info(f"   ❌ Min trades test: FAIL ({trade_count} < {thresholds['min_trades']})")
                    self.logger.info(f"   🐟 RESULT: FISH (failed min trades)")
                    
            elif volume >= thresholds["shark_min_volume"]:
                self.logger.info(f"   ✅ Shark volume test: PASS (${volume:,.0f} >= ${thresholds['shark_min_volume']:,})")
                
                # Test shark criteria
                if trade_count >= thresholds["min_trades"] and avg_trade_size >= thresholds["shark_min_avg_trade"]:
                    self.logger.info(f"   🦈 RESULT: SHARK")
                    sharks_found += 1
                else:
                    self.logger.info(f"   🐟 RESULT: FISH (failed shark criteria)")
            else:
                self.logger.info(f"   ❌ Volume test: FAIL (${volume:,.0f} < ${thresholds['shark_min_volume']:,})")
                self.logger.info(f"   🐟 RESULT: FISH (below volume threshold)")
        
        # Summary
        self.logger.info(f"\n📊 CLASSIFICATION SUMMARY:")
        self.logger.info(f"   🐋 Whales found: {whales_found}")
        self.logger.info(f"   🦈 Sharks found: {sharks_found}")
        self.logger.info(f"   🐟 Fish: {len(traders_data) - whales_found - sharks_found}")
        
        # Compare with actual service result
        self.logger.info(f"\n🔄 Testing actual service...")
        service_result = await self.whale_tracker.analyze_whale_shark_movements(token_address, "normal")
        actual_whales = service_result.get("whale_analysis", {}).get("count", 0)
        actual_sharks = service_result.get("shark_analysis", {}).get("count", 0)
        
        self.logger.info(f"   Service result - Whales: {actual_whales}, Sharks: {actual_sharks}")
        
        if whales_found != actual_whales or sharks_found != actual_sharks:
            self.logger.error(f"   ❌ MISMATCH! Debug logic differs from service logic")
        else:
            self.logger.info(f"   ✅ MATCH! Debug logic matches service logic")
            
        return {
            "debug_whales": whales_found,
            "debug_sharks": sharks_found,
            "service_whales": actual_whales,
            "service_sharks": actual_sharks,
            "match": whales_found == actual_whales and sharks_found == actual_sharks
        }
    
    def suggest_threshold_fixes(self, results: List[Dict]):
        """Suggest threshold fixes based on debug results"""
        self.logger.info(f"\n💡 THRESHOLD FIX RECOMMENDATIONS:")
        self.logger.info("=" * 60)
        
        total_debug_whales = sum(r["debug_whales"] for r in results)
        total_service_whales = sum(r["service_whales"] for r in results)
        
        if total_service_whales == 0 and total_debug_whales == 0:
            self.logger.info("🔧 ISSUE: No whales found even with high-volume traders")
            self.logger.info("   Suggested fixes:")
            self.logger.info("   1. Reduce min_trades from 5 to 1-3")
            self.logger.info("   2. Reduce whale_min_avg_trade from $5k to $1k")
            self.logger.info("   3. Focus on volume-based classification")
            
        self.logger.info(f"\n🎯 Recommended new thresholds:")
        self.logger.info(f"   whale_min_volume: $100,000 (keep current)")
        self.logger.info(f"   min_trades: 1 (reduce from 5)")
        self.logger.info(f"   whale_min_avg_trade: $1,000 (reduce from $5,000)")
        
    async def run_debug(self):
        """Run the complete debug analysis"""
        self.logger.info("🔍 Starting Whale/Shark Classification Debug")
        self.logger.info("=" * 70)
        
        if not await self.initialize_services():
            return
        
        results = []
        
        for token_address in self.test_tokens:
            result = await self.debug_classification_logic(token_address)
            if result:
                results.append(result)
        
        # Generate recommendations
        self.suggest_threshold_fixes(results)
        
        self.logger.info(f"\n✅ Debug analysis complete!")


async def main():
    """Main function"""
    debugger = WhaleSharkClassificationDebugger()
    await debugger.run_debug()


if __name__ == "__main__":
    asyncio.run(main()) 