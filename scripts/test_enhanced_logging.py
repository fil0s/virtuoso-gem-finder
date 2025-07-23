#!/usr/bin/env python3
"""
Test script to demonstrate enhanced batch enrichment logging
"""

import asyncio
import logging
import sys
import os

# Add the project root to Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from scripts.early_gem_detector import EarlyGemDetector

def setup_logging():
    """Setup logging to show enhanced output"""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.StreamHandler(sys.stdout)
        ]
    )
    return logging.getLogger(__name__)

async def test_enhanced_logging():
    """Test the enhanced batch enrichment logging"""
    logger = setup_logging()
    logger.info("🧪 Testing Enhanced Batch Enrichment Logging")
    logger.info("=" * 60)
    
    # Create detector instance
    detector = EarlyGemDetector(debug_mode=True)
    
    # Create mock tokens for testing
    mock_tokens = [
        {
            'address': '7GCihgDB8fe6KNjn2MYtkzZcRjQy3t9GHdC8uHYmW2hr',
            'symbol': 'POPCAT',
            'name': 'Popcat',
            'source': 'moralis_graduated',
            'needs_enrichment': True
        },
        {
            'address': 'DezXAZ8z7PnrnRJjz3wXBoRgixCa6xjnB7YaB1pPB263',
            'symbol': 'BONK',
            'name': 'Bonk',
            'source': 'sol_bonding_detector',
            'needs_enrichment': True
        },
        {
            'address': 'EPjFWdd5AufqSSqeM2qN1xzybapC8G4wEGGkZwyTDt1v',
            'symbol': 'USDC',
            'name': 'USD Coin',
            'source': 'moralis_bonding',
            'needs_enrichment': True
        }
    ]
    
    logger.info(f"📊 Mock tokens created: {len(mock_tokens)} tokens")
    logger.info("")
    
    try:
        # Test the enhanced batch enrichment
        enriched = await detector._enrich_graduated_tokens(mock_tokens)
        
        logger.info("")
        logger.info("🎉 Test completed successfully!")
        logger.info(f"📊 Enriched {len(enriched)} tokens")
        
    except Exception as e:
        logger.error(f"❌ Test failed: {e}")
        raise

if __name__ == "__main__":
    asyncio.run(test_enhanced_logging()) 