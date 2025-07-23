#!/usr/bin/env python3
"""
🧪 Test Script for Emerging Token Discovery System
Simple test to validate the emerging token discovery functionality
"""

import asyncio
import logging
import sys
import os

# Add parent directory to path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from emerging_token_discovery_system import EmergingTokenDiscoverySystem


async def test_emerging_discovery():
    """Test the emerging token discovery system"""
    
    # Setup logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s'
    )
    logger = logging.getLogger(__name__)
    
    logger.info("🧪 Starting Emerging Token Discovery Test")
    logger.info("=" * 60)
    
    try:
        # Initialize the discovery system
        discovery_system = EmergingTokenDiscoverySystem(logger=logger)
        
        # Run the discovery
        results = await discovery_system.run_emerging_token_discovery()
        
        # Display summary
        if results.get('status') == 'SUCCESS':
            discovery_results = results.get('discovery_results', {})
            
            logger.info("\n✅ TEST RESULTS:")
            logger.info(f"   • Meteora Emerging: {discovery_results.get('meteora_emerging_count', 0)}")
            logger.info(f"   • Jupiter Emerging: {discovery_results.get('jupiter_emerging_count', 0)}")
            logger.info(f"   • Cross-Platform: {discovery_results.get('cross_platform_count', 0)}")
            logger.info(f"   • Risk Filtered: {discovery_results.get('risk_filtered_count', 0)}")
            
            # Show top emerging tokens if any
            emerging_tokens = results.get('emerging_tokens', {})
            cross_platform = emerging_tokens.get('cross_platform', [])
            
            if cross_platform:
                logger.info(f"\n🎯 TOP CROSS-PLATFORM EMERGING TOKENS:")
                for i, token in enumerate(cross_platform[:5], 1):
                    symbol = token.get('symbol', 'Unknown')
                    score = token.get('total_score', 0)
                    risk = token.get('risk_assessment', {}).get('overall_risk', 'UNKNOWN')
                    logger.info(f"   {i}. {symbol} (Score: {score:.1f}, Risk: {risk})")
            
            logger.info("\n🎉 Emerging token discovery test completed successfully!")
            
        else:
            logger.error(f"❌ Test failed: {results.get('error', 'Unknown error')}")
            
        return results
        
    except Exception as e:
        logger.error(f"💥 Test error: {e}")
        return {'status': 'ERROR', 'error': str(e)}


if __name__ == "__main__":
    asyncio.run(test_emerging_discovery()) 