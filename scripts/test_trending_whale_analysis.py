#!/usr/bin/env python3
"""
Trending Tokens Whale Analysis Script

This script uses the BirdEye trending tokens endpoint to fetch the top 10 trending tokens
sorted by rank (descending) and performs comprehensive whale analysis on each token.

API Reference: https://docs.birdeye.so/reference/get-defi-token_trending

Usage: python scripts/test_trending_whale_analysis.py
"""

import asyncio
import sys
import os
from typing import Dict, List, Any
import json
from datetime import datetime

# Add project root to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from api.birdeye_connector import BirdeyeAPI
from services.whale_shark_movement_tracker import WhaleSharkMovementTracker
from services.smart_money_detector import SmartMoneyDetector
from services.logger_setup import LoggerSetup
from core.config_manager import ConfigManager
from core.cache_manager import CacheManager
from services.rate_limiter_service import RateLimiterService


class TrendingWhaleAnalyzer:
    """Analyze trending tokens for whale activity"""
    
    def __init__(self):
        self.logger_setup = LoggerSetup("TrendingWhaleAnalyzer")
        self.logger = self.logger_setup.logger
        self.config_manager = ConfigManager()
        self.birdeye_api = None
        self.whale_tracker = None
        self.smart_money_detector = None
        
        # Analysis results
        self.trending_tokens = []
        self.whale_analysis_results = {}
        self.smart_money_results = {}
    
    async def initialize_services(self):
        """Initialize all required services"""
        try:
            self.logger.info("🔧 Initializing services for trending whale analysis...")
            
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
    
    async def fetch_trending_tokens(self, limit: int = 10) -> List[Dict[str, Any]]:
        """
        Fetch trending tokens using BirdEye API
        
        Args:
            limit: Number of trending tokens to fetch (default: 10)
            
        Returns:
            List of trending token data
        """
        try:
            self.logger.info("📈 Fetching trending tokens from BirdEye API...")
            self.logger.info("🔗 Using endpoint: /defi/token_trending")
            self.logger.info(f"📊 Parameters: sort_by=rank, sort_type=asc, limit={limit}")
            
            # Prepare API request parameters
            params = {
                "sort_by": "rank",
                "sort_type": "asc", 
                "limit": limit
            }
            
            # Make API request
            response = await self.birdeye_api.make_request(
                method="GET",
                endpoint="/defi/token_trending",
                params=params
            )
            
            if not response or "data" not in response:
                self.logger.error("❌ No data returned from trending tokens API")
                return []
            
            trending_data = response["data"]
            if not trending_data:
                self.logger.error("❌ No data found in trending tokens response")
                return []
            
            # Handle different response structures
            tokens = []
            if "items" in trending_data:
                tokens = trending_data["items"]
            elif "tokens" in trending_data:
                tokens = trending_data["tokens"]
            elif isinstance(trending_data, list):
                tokens = trending_data
            else:
                self.logger.error(f"❌ Unexpected data structure in trending tokens response: {list(trending_data.keys())}")
                return []
            self.logger.info(f"✅ Successfully fetched {len(tokens)} trending tokens")
            
            # Log trending tokens summary
            self.logger.info("📋 Trending Tokens Summary:")
            for i, token in enumerate(tokens[:5], 1):  # Show top 5
                symbol = token.get("symbol", "Unknown")
                address = token.get("address", "Unknown")
                rank = token.get("rank", "N/A")
                self.logger.info(f"   {i}. {symbol} (Rank: {rank}) - {address[:8]}...")
            
            self.trending_tokens = tokens
            return tokens
            
        except Exception as e:
            self.logger.error(f"❌ Error fetching trending tokens: {e}")
            return []
    
    async def analyze_token_whales(self, token: Dict[str, Any]) -> Dict[str, Any]:
        """
        Analyze whale activity for a single token
        
        Args:
            token: Token data from trending API
            
        Returns:
            Whale analysis results
        """
        try:
            token_address = token.get("address")
            symbol = token.get("symbol", "Unknown")
            rank = token.get("rank", "N/A")
            
            if not token_address:
                self.logger.error(f"❌ No address found for token {symbol}")
                return {}
            
            self.logger.info(f"🐋 Analyzing whales for {symbol} (Rank: {rank})")
            self.logger.info(f"   📍 Address: {token_address}")
            
            # Perform whale analysis
            whale_results = await self.whale_tracker.analyze_whale_shark_movements(
                token_address, priority_level='normal'
            )
            
            if not whale_results:
                self.logger.warning(f"⚠️ No whale data returned for {symbol}")
                return {}
            
            # Extract key metrics
            whale_analysis = whale_results.get("whale_analysis", {})
            whale_count = len(whale_analysis.get("top_whales", []))
            whale_volume = sum(w.get("volume", 0) for w in whale_analysis.get("top_whales", []))
            
            self.logger.info(f"   🐋 Whale Count: {whale_count}")
            self.logger.info(f"   💰 Whale Volume: ${whale_volume:,.0f}")
            
            return {
                "token_info": {
                    "symbol": symbol,
                    "address": token_address,
                    "rank": rank
                },
                "whale_analysis": whale_results,
                "summary": {
                    "whale_count": whale_count,
                    "whale_volume": whale_volume,
                    "has_whales": whale_count > 0
                }
            }
            
        except Exception as e:
            symbol = token.get("symbol", "Unknown")
            self.logger.error(f"❌ Error analyzing whales for {symbol}: {e}")
            return {}
    
    async def analyze_token_smart_money(self, token: Dict[str, Any]) -> Dict[str, Any]:
        """
        Analyze smart money activity for a single token
        
        Args:
            token: Token data from trending API
            
        Returns:
            Smart money analysis results
        """
        try:
            token_address = token.get("address")
            symbol = token.get("symbol", "Unknown")
            
            if not token_address:
                return {}
            
            self.logger.info(f"🧠 Analyzing smart money for {symbol}")
            
            # Perform smart money analysis
            smart_results = await self.smart_money_detector.analyze_smart_money(
                token_address, priority_level='normal'
            )
            
            if not smart_results:
                return {}
            
            # Extract key metrics
            skilled_traders = smart_results.get("skilled_traders", [])
            skill_metrics = smart_results.get("skill_metrics", {})
            smart_count = len(skilled_traders)
            avg_skill = skill_metrics.get("average_skill_score", 0.0)
            
            self.logger.info(f"   🧠 Smart Traders: {smart_count}")
            self.logger.info(f"   📊 Avg Skill Score: {avg_skill:.3f}")
            
            return {
                "smart_money_analysis": smart_results,
                "summary": {
                    "smart_trader_count": smart_count,
                    "average_skill_score": avg_skill,
                    "has_smart_money": smart_count > 0
                }
            }
            
        except Exception as e:
            symbol = token.get("symbol", "Unknown")
            self.logger.error(f"❌ Error analyzing smart money for {symbol}: {e}")
            return {}
    
    async def run_comprehensive_analysis(self):
        """Run comprehensive whale and smart money analysis on trending tokens"""
        try:
            self.logger.info("🚀 Starting Comprehensive Trending Tokens Whale Analysis")
            self.logger.info("=" * 70)
            
            # Step 1: Fetch trending tokens
            tokens = await self.fetch_trending_tokens(limit=10)
            if not tokens:
                self.logger.error("❌ No trending tokens to analyze")
                return
            
            self.logger.info(f"\n📊 Analyzing {len(tokens)} trending tokens for whale activity...")
            self.logger.info("-" * 70)
            
            # Step 2: Analyze each token
            analysis_results = []
            
            for i, token in enumerate(tokens, 1):
                symbol = token.get("symbol", "Unknown")
                rank = token.get("rank", "N/A")
                
                self.logger.info(f"\n🔍 ANALYZING TOKEN {i}/{len(tokens)}: {symbol} (Rank: {rank})")
                self.logger.info("-" * 50)
                
                # Whale analysis
                whale_results = await self.analyze_token_whales(token)
                
                # Smart money analysis (if whales exist)
                smart_results = {}
                if whale_results.get("summary", {}).get("has_whales", False):
                    smart_results = await self.analyze_token_smart_money(token)
                else:
                    self.logger.info(f"   ⏭️ Skipping smart money analysis (no whales)")
                
                # Combine results
                combined_results = {
                    "rank": i,
                    "token": token,
                    "whale_analysis": whale_results,
                    "smart_money_analysis": smart_results,
                    "analysis_timestamp": datetime.now().isoformat()
                }
                
                analysis_results.append(combined_results)
                
                # Brief summary
                whale_count = whale_results.get("summary", {}).get("whale_count", 0)
                smart_count = smart_results.get("summary", {}).get("smart_trader_count", 0)
                whale_volume = whale_results.get("summary", {}).get("whale_volume", 0)
                
                self.logger.info(f"   📈 Summary: {whale_count} whales, {smart_count} smart traders, ${whale_volume:,.0f} whale volume")
            
            # Step 3: Generate comprehensive summary
            self.logger.info("\n🎯 COMPREHENSIVE ANALYSIS SUMMARY")
            self.logger.info("=" * 70)
            
            # Calculate aggregate statistics
            total_tokens = len(analysis_results)
            tokens_with_whales = sum(1 for r in analysis_results if r["whale_analysis"].get("summary", {}).get("has_whales", False))
            tokens_with_smart_money = sum(1 for r in analysis_results if r["smart_money_analysis"].get("summary", {}).get("has_smart_money", False))
            total_whale_volume = sum(r["whale_analysis"].get("summary", {}).get("whale_volume", 0) for r in analysis_results)
            
            self.logger.info(f"📊 Tokens Analyzed: {total_tokens}")
            self.logger.info(f"🐋 Tokens with Whales: {tokens_with_whales}/{total_tokens} ({tokens_with_whales/total_tokens*100:.1f}%)")
            self.logger.info(f"🧠 Tokens with Smart Money: {tokens_with_smart_money}/{total_tokens} ({tokens_with_smart_money/total_tokens*100:.1f}%)")
            self.logger.info(f"💰 Total Whale Volume: ${total_whale_volume:,.0f}")
            
            # Top performers
            self.logger.info("\n🏆 TOP PERFORMERS:")
            
            # Sort by whale volume
            by_whale_volume = sorted(analysis_results, key=lambda x: x["whale_analysis"].get("summary", {}).get("whale_volume", 0), reverse=True)
            self.logger.info("   🐋 By Whale Volume:")
            for i, result in enumerate(by_whale_volume[:3], 1):
                symbol = result["token"].get("symbol", "Unknown")
                volume = result["whale_analysis"].get("summary", {}).get("whale_volume", 0)
                whale_count = result["whale_analysis"].get("summary", {}).get("whale_count", 0)
                self.logger.info(f"      {i}. {symbol}: ${volume:,.0f} ({whale_count} whales)")
            
            # Sort by smart money count
            by_smart_money = sorted(analysis_results, key=lambda x: x["smart_money_analysis"].get("summary", {}).get("smart_trader_count", 0), reverse=True)
            self.logger.info("   🧠 By Smart Money Activity:")
            for i, result in enumerate(by_smart_money[:3], 1):
                symbol = result["token"].get("symbol", "Unknown")
                smart_count = result["smart_money_analysis"].get("summary", {}).get("smart_trader_count", 0)
                avg_skill = result["smart_money_analysis"].get("summary", {}).get("average_skill_score", 0)
                self.logger.info(f"      {i}. {symbol}: {smart_count} smart traders (avg skill: {avg_skill:.3f})")
            
            # Save results
            timestamp = int(datetime.now().timestamp())
            results_file = f"scripts/results/trending_whale_analysis_{timestamp}.json"
            
            with open(results_file, 'w') as f:
                json.dump(analysis_results, f, indent=2, default=str)
            
            self.logger.info(f"\n💾 Results saved to: {results_file}")
            self.logger.info("✅ Trending tokens whale analysis complete!")
            
            return analysis_results
            
        except Exception as e:
            self.logger.error(f"❌ Error in comprehensive analysis: {e}")
            return []


async def main():
    """Main analysis function"""
    analyzer = TrendingWhaleAnalyzer()
    
    if not await analyzer.initialize_services():
        return
    
    await analyzer.run_comprehensive_analysis()
    
    # Cleanup
    if analyzer.birdeye_api:
        await analyzer.birdeye_api.close()


if __name__ == "__main__":
    asyncio.run(main()) 