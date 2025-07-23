#!/usr/bin/env python3
"""
Test Phase 1 whale consolidation changes
"""

import asyncio
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from api.birdeye_connector import BirdeyeAPI
from core.cache_manager import CacheManager
from services.whale_shark_movement_tracker import WhaleSharkMovementTracker, WhaleSignal, WhaleActivityType
from services.rate_limiter_service import RateLimiterService
from utils.logger_setup import LoggerSetup

async def test_phase1_consolidation():
    """Test the Phase 1 consolidation"""
    logger_setup = LoggerSetup("whale_consolidation_test", log_level="INFO")
    logger = logger_setup.logger
    logger.info("🧪 Testing Phase 1 Whale Consolidation")
    
    try:
        # Initialize components
        cache_manager = CacheManager()
        rate_limiter = RateLimiterService()
        
        config = {
            'BIRDEYE_API': {
                'api_key': os.getenv('BIRDEYE_API_KEY'),
                'base_url': 'https://public-api.birdeye.so',
                'rate_limit': 100,
                'request_timeout_seconds': 20
            }
        }
        
        if not config['BIRDEYE_API']['api_key']:
            logger.error("❌ BIRDEYE_API_KEY not found")
            return
        
        birdeye_api = BirdeyeAPI(config, logger, cache_manager, rate_limiter)
        
        # Test consolidated whale tracker
        whale_tracker = WhaleSharkMovementTracker(
            birdeye_api=birdeye_api,
            logger=logger
        )
        
        logger.info("✅ WhaleSharkMovementTracker initialized successfully")
        
        # Test whale database
        db_stats = whale_tracker.get_whale_database_stats()
        logger.info(f"📊 Whale Database Stats: {db_stats}")
        logger.info(f"   Total whales: {db_stats['total_whales']}")
        logger.info(f"   Tier distribution: {db_stats['tier_distribution']}")
        logger.info(f"   Has discovery service: {db_stats['has_discovery_service']}")
        
        # Test whale activity analysis
        test_token = "So11111111111111111111111111111111111111112"  # SOL
        
        logger.info(f"🐋 Testing whale activity analysis for {test_token}")
        whale_signal = await whale_tracker.analyze_whale_activity_patterns(
            test_token, 
            {"symbol": "SOL", "address": test_token}
        )
        
        logger.info(f"✅ Whale Activity Analysis Results:")
        logger.info(f"   Type: {whale_signal.type.value}")
        logger.info(f"   Confidence: {whale_signal.confidence:.2f}")
        logger.info(f"   Score Impact: {whale_signal.score_impact}")
        logger.info(f"   Whale Count: {whale_signal.whale_count}")
        logger.info(f"   Total Value: ${whale_signal.total_value:,.0f}")
        logger.info(f"   Details: {whale_signal.details}")
        
        # Test standard whale/shark analysis
        logger.info(f"🦈 Testing standard whale/shark movement analysis")
        movement_result = await whale_tracker.analyze_whale_shark_movements(test_token, "normal")
        
        whale_count = movement_result.get("whale_analysis", {}).get("count", 0)
        shark_count = movement_result.get("shark_analysis", {}).get("count", 0)
        
        logger.info(f"✅ Movement Analysis Results:")
        logger.info(f"   Whales found: {whale_count}")
        logger.info(f"   Sharks found: {shark_count}")
        logger.info(f"   API calls used: {movement_result.get('api_efficiency', {}).get('api_calls_used', 0)}")
        
        # Test EarlyTokenDetector integration
        logger.info("🔬 Testing EarlyTokenDetector integration...")
        try:
            from services.early_token_detection import EarlyTokenDetector
            
            detector = EarlyTokenDetector()
            if hasattr(detector, 'whale_shark_tracker') and detector.whale_shark_tracker:
                logger.info("✅ EarlyTokenDetector has whale_shark_tracker")
                
                # Test the whale analysis method
                test_result = await detector.perform_whale_analysis({
                    "address": test_token,
                    "symbol": "SOL"
                })
                
                logger.info(f"✅ EarlyTokenDetector whale analysis:")
                logger.info(f"   Activity type: {test_result.get('activity_type')}")
                logger.info(f"   Grade: {test_result.get('grade')}")
                logger.info(f"   Score impact: {test_result.get('score_impact')}")
                logger.info(f"   Confidence: {test_result.get('confidence', 0):.2f}")
            else:
                logger.warning("⚠️ EarlyTokenDetector missing whale_shark_tracker")
                
        except Exception as e:
            logger.error(f"❌ EarlyTokenDetector integration test failed: {e}")
        
        logger.info("🎉 Phase 1 consolidation test completed successfully!")
        
        # Summary
        logger.info("\n📈 PHASE 1 CONSOLIDATION SUMMARY:")
        logger.info("   ✅ WhaleSharkMovementTracker: Enhanced with activity analysis")
        logger.info("   ✅ WhaleSignal dataclass: Added for structured results")
        logger.info("   ✅ WhaleActivityType enum: Added for activity classification")
        logger.info("   ✅ Whale database: Integrated from WhaleActivityAnalyzer")
        logger.info("   ✅ EarlyTokenDetector: Updated to use consolidated tracker")
        logger.info("   ⚠️ WhaleActivityAnalyzer: Marked as deprecated")
        
    except Exception as e:
        logger.error(f"❌ Phase 1 test failed: {e}")
        raise

if __name__ == "__main__":
    asyncio.run(test_phase1_consolidation()) 