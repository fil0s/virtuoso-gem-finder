#!/usr/bin/env python3
"""
Debug Smart Money Detection Script

This script tests the SmartMoneyDetector's skill calculation logic with real trader data
to identify exactly why it's returning 0 smart traders despite having whales with millions in volume.

Usage: python scripts/debug_smart_money_detection.py
"""

import asyncio
import sys
import os
from typing import Dict, List, Any

# Add project root to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from api.birdeye_connector import BirdeyeAPI
from services.whale_shark_movement_tracker import WhaleSharkMovementTracker
from services.smart_money_detector import SmartMoneyDetector
from services.logger_setup import LoggerSetup
from core.config_manager import ConfigManager
from core.cache_manager import CacheManager
from services.rate_limiter_service import RateLimiterService


class SmartMoneyDetectionDebugger:
    """Debug smart money detection with real trader data"""
    
    def __init__(self):
        self.logger_setup = LoggerSetup("SmartMoneyDebugger")
        self.logger = self.logger_setup.logger
        self.config_manager = ConfigManager()
        self.birdeye_api = None
        self.whale_tracker = None
        self.smart_money_detector = None
        
        # Test token with known whale activity
        self.test_token = "9doRRAik5gvhbEwjbZDbZR6GxXSAfdoomyJR57xKpump"
    
    async def initialize_services(self):
        """Initialize services"""
        try:
            self.logger.info("🔧 Initializing services...")
            
            # Initialize supporting services
            config = self.config_manager.get_section("BIRDEYE_API")
            cache_manager = CacheManager()
            rate_limiter = RateLimiterService()
            
            # Initialize BirdEye API
            self.birdeye_api = BirdeyeAPI(config, self.logger, cache_manager, rate_limiter)
            
            # Initialize whale tracker
            whale_logger_setup = LoggerSetup("WhaleTracker")
            whale_logger = whale_logger_setup.logger
            self.whale_tracker = WhaleSharkMovementTracker(self.birdeye_api, whale_logger)
            
            # Initialize smart money detector
            smart_logger_setup = LoggerSetup("SmartMoneyDetector")
            smart_logger = smart_logger_setup.logger
            self.smart_money_detector = SmartMoneyDetector(self.whale_tracker, smart_logger)
            
            self.logger.info("✅ All services initialized successfully")
            return True
            
        except Exception as e:
            self.logger.error(f"❌ Failed to initialize services: {e}")
            return False
    
    async def debug_smart_money_detection(self):
        """Debug the complete smart money detection process"""
        try:
            self.logger.info(f"🧠 Starting Smart Money Detection Debug for {self.test_token[:8]}...")
            self.logger.info("=" * 70)
            
            # Step 1: Get whale data
            self.logger.info("📊 Step 1: Getting whale/shark data...")
            whale_data = await self.whale_tracker.analyze_whale_shark_movements(
                self.test_token, priority_level='normal'
            )
            
            if not whale_data:
                self.logger.error("❌ No whale data available")
                return
            
            # Extract trader data
            whale_analysis = whale_data.get("whale_analysis", {})
            shark_analysis = whale_data.get("shark_analysis", {})
            whales = whale_analysis.get("top_whales", [])
            sharks = shark_analysis.get("top_sharks", [])
            all_traders = whales + sharks
            
            self.logger.info(f"✅ Found {len(whales)} whales and {len(sharks)} sharks")
            self.logger.info(f"📈 Total traders to analyze: {len(all_traders)}")
            
            if not all_traders:
                self.logger.error("❌ No traders found in whale/shark data")
                return
            
            # Step 2: Debug skill calculation for each trader
            self.logger.info("\n🔍 Step 2: Analyzing individual trader skills...")
            self.logger.info("-" * 50)
            
            skill_results = []
            current_thresholds = self.smart_money_detector.smart_money_criteria
            
            self.logger.info(f"🎯 Current Smart Money Thresholds:")
            self.logger.info(f"   skill_score_threshold: {current_thresholds['skill_score_threshold']}")
            self.logger.info(f"   optimal_trade_size_min: ${current_thresholds['optimal_trade_size_min']:,}")
            self.logger.info(f"   optimal_trade_size_max: ${current_thresholds['optimal_trade_size_max']:,}")
            self.logger.info(f"   balance_consistency: {current_thresholds['balance_consistency']}")
            self.logger.info("")
            
            for i, trader in enumerate(all_traders[:5], 1):  # Debug first 5 traders
                self.logger.info(f"🔍 Trader {i}: {trader.get('address', 'Unknown')[:8]}...")
                
                # Extract basic metrics - check ALL possible field names
                volume = trader.get("volume", 0)
                trade_count = trader.get("trade", trader.get("trade_count", 0))
                volume_buy = trader.get("volumeBuy", trader.get("volume_buy", 0))
                volume_sell = trader.get("volumeSell", trader.get("volume_sell", 0))
                avg_trade_size = volume / max(trade_count, 1)
                
                # Debug: Show ALL available fields in trader data
                self.logger.info(f"   🔍 Available fields: {list(trader.keys())}")
                self.logger.info(f"   🔍 Raw trader data: {trader}")
                
                self.logger.info(f"   💰 Volume: ${volume:,.0f}")
                self.logger.info(f"   📊 Trades: {trade_count}")
                self.logger.info(f"   📈 Avg Trade: ${avg_trade_size:,.0f}")
                self.logger.info(f"   🟢 Buy Volume: ${volume_buy:,.0f}")
                self.logger.info(f"   🔴 Sell Volume: ${volume_sell:,.0f}")
                
                # Calculate individual skill components
                skill_analysis = self.smart_money_detector._analyze_individual_trader_skill(trader)
                
                self.logger.info(f"   🧠 Skill Breakdown:")
                self.logger.info(f"      Trading Efficiency: {skill_analysis['trading_efficiency']:.3f}")
                self.logger.info(f"      Behavioral Consistency: {skill_analysis['behavioral_consistency']:.3f}")
                self.logger.info(f"      Risk Management: {skill_analysis['risk_management']:.3f}")
                self.logger.info(f"      Timing Skill: {skill_analysis['timing_skill']:.3f}")
                self.logger.info(f"   🎯 Overall Skill Score: {skill_analysis['skill_score']:.3f}")
                self.logger.info(f"   📊 Skill Level: {skill_analysis['skill_level']}")
                
                # Check if passes threshold
                passes_threshold = skill_analysis['skill_score'] >= current_thresholds['skill_score_threshold']
                self.logger.info(f"   ✅ Passes Threshold ({current_thresholds['skill_score_threshold']}): {passes_threshold}")
                
                skill_results.append({
                    'trader': trader,
                    'skill_analysis': skill_analysis,
                    'passes_threshold': passes_threshold
                })
                
                self.logger.info("")
            
            # Step 3: Test with relaxed thresholds
            self.logger.info("\n🎯 Step 3: Testing with relaxed thresholds...")
            self.logger.info("-" * 50)
            
            # Test different threshold levels
            test_thresholds = [0.6, 0.5, 0.4, 0.3, 0.2]
            
            for threshold in test_thresholds:
                passing_count = sum(1 for r in skill_results if r['skill_analysis']['skill_score'] >= threshold)
                self.logger.info(f"   Threshold {threshold}: {passing_count}/{len(skill_results)} traders would pass")
            
            # Step 4: Generate recommendations
            self.logger.info("\n💡 Step 4: Recommendations...")
            self.logger.info("-" * 50)
            
            if len([r for r in skill_results if r['passes_threshold']]) == 0:
                max_score = max(r['skill_analysis']['skill_score'] for r in skill_results)
                optimal_threshold = max_score * 0.9
                self.logger.info(f"🎯 Suggested optimal threshold: {optimal_threshold:.3f}")
                self.logger.info(f"📊 This would identify the top skilled traders while being realistic")
            
            return skill_results
            
        except Exception as e:
            self.logger.error(f"❌ Debug error: {e}")
            return None


async def main():
    """Main debug function"""
    debugger = SmartMoneyDetectionDebugger()
    
    if not await debugger.initialize_services():
        return
    
    await debugger.debug_smart_money_detection()
    
    # Cleanup
    if debugger.birdeye_api:
        await debugger.birdeye_api.close()


if __name__ == "__main__":
    asyncio.run(main()) 