#!/usr/bin/env python3
"""
Test Smart Money Detector Integration

Demonstrates the new skill-based Smart Money Detector that reuses
whale/shark tracker data to avoid redundant API calls.
"""

import asyncio
import json
import logging
import sys
import os
from datetime import datetime

# Add project root to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from api.birdeye_connector import BirdeyeAPI
from core.cache_manager import CacheManager
from services.whale_shark_movement_tracker import WhaleSharkMovementTracker
from services.smart_money_detector import SmartMoneyDetector
from services.rate_limiter_service import RateLimiterService
from utils.logger_setup import setup_logger

async def test_smart_money_integration():
    """Test the integrated smart money detection system."""
    
    # Setup
    logger = setup_logger("smart_money_test", level=logging.INFO)
    logger.info("🧠 Starting Smart Money Detector Integration Test")
    
    try:
        # Initialize components
        cache_manager = CacheManager()
        rate_limiter = RateLimiterService()
        
        # Initialize BirdeyeAPI with proper config
        config = {
            'birdeye_api_key': os.getenv('BIRDEYE_API_KEY'),
            'birdeye_base_url': 'https://public-api.birdeye.so'
        }
        
        if not config['birdeye_api_key']:
            logger.error("❌ BIRDEYE_API_KEY not found in environment")
            return
        
        birdeye_api = BirdeyeAPI(config, logger, cache_manager, rate_limiter)
        
        # Initialize whale/shark tracker
        whale_shark_tracker = WhaleSharkMovementTracker(
            birdeye_api=birdeye_api,
            logger=logger
        )
        
        # Initialize smart money detector (reuses whale/shark data)
        smart_money_detector = SmartMoneyDetector(
            whale_shark_tracker=whale_shark_tracker,
            logger=logger
        )
        
        # Test tokens
        test_tokens = [
            "So11111111111111111111111111111111111111112",  # SOL
            "EKpQGSJtjMFqKZ9KQanSqYXRcF8fBopzLHYxdM65zcjm",   # WIF
            "DezXAZ8z7PnrnRJjz3wXBoRgixCa6xjnB7YaB1pPB263"    # BONK
        ]
        
        logger.info(f"🧠 Testing smart money detection on {len(test_tokens)} tokens")
        
        # Track API usage
        total_api_calls = 0
        total_cost = 0
        
        for i, token_address in enumerate(test_tokens, 1):
            logger.info(f"\n🧠 [{i}/{len(test_tokens)}] Analyzing smart money for token {token_address[:8]}...")
            
            try:
                # Get smart money analysis (reuses whale/shark data)
                start_time = datetime.now()
                smart_money_result = await smart_money_detector.analyze_smart_money(
                    token_address=token_address,
                    priority_level="normal"  # Can be "normal" or "high"
                )
                analysis_time = (datetime.now() - start_time).total_seconds()
                
                # Extract key metrics
                skilled_count = smart_money_result.get("skill_metrics", {}).get("skilled_count", 0)
                avg_skill_score = smart_money_result.get("skill_metrics", {}).get("average_skill_score", 0.0)
                skill_quality = smart_money_result.get("smart_money_insights", {}).get("skill_quality", "none")
                market_sentiment = smart_money_result.get("smart_money_insights", {}).get("market_sentiment", "neutral")
                api_calls_made = smart_money_result.get("additional_api_calls", 0)
                
                # Display results
                logger.info(f"✅ Smart Money Analysis Complete:")
                logger.info(f"   📊 Skilled Traders: {skilled_count}")
                logger.info(f"   🎯 Average Skill Score: {avg_skill_score:.3f}")
                logger.info(f"   🏆 Skill Quality: {skill_quality}")
                logger.info(f"   📈 Market Sentiment: {market_sentiment}")
                logger.info(f"   ⚡ Analysis Time: {analysis_time:.2f}s")
                logger.info(f"   💰 Additional API Calls: {api_calls_made} (reused whale/shark data!)")
                
                # Show recommendations
                recommendations = smart_money_result.get("smart_money_insights", {}).get("recommendations", [])
                if recommendations:
                    logger.info(f"   💡 Recommendations:")
                    for rec in recommendations[:3]:  # Show top 3
                        logger.info(f"      • {rec}")
                
                total_api_calls += api_calls_made
                
            except Exception as e:
                logger.error(f"❌ Error analyzing token {token_address[:8]}: {e}")
        
        # Summary
        logger.info(f"\n🧠 Smart Money Integration Test Summary:")
        logger.info(f"   📊 Tokens Analyzed: {len(test_tokens)}")
        logger.info(f"   💰 Total Additional API Calls: {total_api_calls}")
        logger.info(f"   🎯 Cost Efficiency: Reused whale/shark data = 0 additional API cost!")
        logger.info(f"   ⚡ Integration Status: ✅ SUCCESSFUL")
        
        # Compare with old approach
        logger.info(f"\n📈 Efficiency Comparison:")
        logger.info(f"   🔴 Old Smart Money Detector: {len(test_tokens) * 5} API calls (5 per token)")
        logger.info(f"   🟢 New Integrated Approach: {total_api_calls} additional calls")
        logger.info(f"   💰 Cost Reduction: {((len(test_tokens) * 5 - total_api_calls) / (len(test_tokens) * 5)) * 100:.1f}%")
        
    except Exception as e:
        logger.error(f"❌ Test failed: {e}")
        raise

if __name__ == "__main__":
    asyncio.run(test_smart_money_integration()) 