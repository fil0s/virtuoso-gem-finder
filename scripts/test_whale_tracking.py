#!/usr/bin/env python3
"""
Test script for whale tracking functionality.
This validates the whale movement tracker's ability to discover, track,
and monitor whale wallets efficiently.
"""

import os
import sys
import asyncio
import logging
from typing import Dict, List, Any, Optional
from pathlib import Path

# Add project root to path for imports
sys.path.append(str(Path(__file__).parent.parent))

# Load environment variables
from dotenv import load_dotenv
load_dotenv()

# Import required modules
from api.birdeye_connector import BirdeyeAPI
from services.whale_discovery_service import WhaleDiscoveryService
from services.whale_movement_tracker import WhaleMovementTracker
from core.cache_manager import CacheManager
from services.rate_limiter_service import RateLimiterService

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger("WhaleTrackingTest")

async def test_whale_tracking():
    """Test whale tracking functionality"""
    logger.info("Starting whale tracking test")
    
    try:
        # Initialize required services
        cache_manager = CacheManager()
        rate_limiter = RateLimiterService()
        
        # Initialize API connector
        api_key = os.environ.get("BIRDEYE_API_KEY")
        masked_key = f"{api_key[:8]}...{api_key[-4:]}" if api_key and len(api_key) > 12 else "NOT_SET"
        logger.info(f"🔑 BirdEye API key loaded: {masked_key}")
        
        # Initialize BirdeyeAPI with required parameters
        birdeye_api = BirdeyeAPI(
            config={
                "api_key": api_key,
                "request_timeout_seconds": 30,
                "use_rate_limiting": True
            },
            logger=logger,
            cache_manager=cache_manager,
            rate_limiter=rate_limiter
        )
        
        # Initialize whale discovery service
        whale_discovery_service = WhaleDiscoveryService(
            birdeye_api=birdeye_api,
            logger=logger
        )
        
        # Initialize whale movement tracker
        whale_tracker = WhaleMovementTracker(
            birdeye_api=birdeye_api,
            whale_discovery_service=whale_discovery_service,
            logger=logger
        )
        
        logger.info("Services initialized successfully")
        
        # 1. Test whale discovery
        logger.info("Testing whale discovery...")
        discovered_whales = await whale_discovery_service.discover_whales(max_discoveries=5)
        logger.info(f"Discovered {len(discovered_whales)} whales")
        
        if discovered_whales:
            logger.info(f"Sample whale: {discovered_whales[0]['address'][:10]}...")
        
        # 2. Test adding whales for tracking
        if discovered_whales:
            # Add first 3 discovered whales (or all if less than 3)
            for i, whale in enumerate(discovered_whales[:3]):
                whale_address = whale['address']
                logger.info(f"Adding whale {i+1}: {whale_address[:10]}... for tracking")
                await whale_tracker.add_whale_for_tracking(whale_address)
        else:
            # Add some known large Solana wallets for testing
            test_whales = [
                "Ey9WXVtsjDLrRFz6QAmXJiUFiDX6iKZgRpXRoTDJvkAF",  # Large DEX wallet
                "9vYWHBPz817wJdQpE8u3h8UoY3sZ16ZXdCcvLB7jY4Dj",  # Solana foundation
                "3QuGYeeiAuAQxNVqTKzNCSgFTYbYaEvas5kBiWzasSNc"   # Known whale
            ]
            for i, whale_address in enumerate(test_whales):
                logger.info(f"Adding test whale {i+1}: {whale_address[:10]}... for tracking")
                await whale_tracker.add_whale_for_tracking(whale_address)
        
        # 3. Check tracking status
        stats = whale_tracker.get_tracking_stats()
        logger.info(f"Tracking stats: {stats['tracked_whales']} whales")
        
        # 4. Start monitoring in background
        logger.info("Starting whale monitoring (10 seconds)...")
        
        # Create task and run for 10 seconds
        monitoring_task = asyncio.create_task(whale_tracker.start_monitoring(check_interval_seconds=5))
        
        # Wait for 10 seconds to let the monitoring run
        await asyncio.sleep(10)
        
        # Cancel the monitoring task
        monitoring_task.cancel()
        
        try:
            await monitoring_task
        except asyncio.CancelledError:
            logger.info("Monitoring task cancelled")
        
        # 5. Check movements if any
        recent_movements = whale_tracker.get_recent_movements(hours=24)
        logger.info(f"Recent movements: {len(recent_movements)}")
        
        # 6. Check alerts if any
        active_alerts = whale_tracker.get_active_alerts()
        logger.info(f"Active alerts: {len(active_alerts)}")
        
        # Final stats
        final_stats = whale_tracker.get_tracking_stats()
        logger.info(f"Final tracking stats: {final_stats}")
        
        logger.info("Whale tracking test completed successfully")
        
    except Exception as e:
        logger.error(f"Error in whale tracking test: {e}")
        raise

async def main():
    """Main entry point"""
    try:
        await test_whale_tracking()
    except Exception as e:
        logger.error(f"Test failed: {e}")
        sys.exit(1)

if __name__ == "__main__":
    asyncio.run(main()) 