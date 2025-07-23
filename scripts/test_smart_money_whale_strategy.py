#!/usr/bin/env python3
"""
Test Smart Money Whale Strategy

This script tests the new SmartMoneyWhaleStrategy that discovers tokens
based on whale and smart money activity patterns as the primary mechanism.
"""

import asyncio
import os
import sys
import json
from pathlib import Path
from datetime import datetime

# Add project root to path
sys.path.append(str(Path(__file__).parent.parent))

from core.strategies.smart_money_whale_strategy import SmartMoneyWhaleStrategy
from api.birdeye_connector import BirdeyeAPI
from core.cache_manager import CacheManager
from services.rate_limiter_service import RateLimiterService
from services.logger_setup import LoggerSetup


async def test_smart_money_whale_strategy():
    """Test the SmartMoneyWhaleStrategy."""
    
    # Setup logging
    logger_setup = LoggerSetup("SmartMoneyWhaleStrategyTest", log_level="INFO")
    logger = logger_setup.logger
    
    logger.info("🧪 Starting Smart Money Whale Strategy Test")
    
    try:
        # Initialize components
        cache_manager = CacheManager()
        rate_limiter = RateLimiterService()
        
        # Get API key
        api_key = os.getenv('BIRDEYE_API_KEY')
        if not api_key:
            logger.error("❌ BIRDEYE_API_KEY not found in environment")
            return
        
        # Initialize BirdeyeAPI
        birdeye_config = {
            'api_key': api_key,
            'base_url': 'https://public-api.birdeye.so',
            'request_timeout_seconds': 30,
            'use_rate_limiting': True
        }
        
        birdeye_api = BirdeyeAPI(
            config=birdeye_config,
            logger=logger,
            cache_manager=cache_manager,
            rate_limiter=rate_limiter
        )
        
        # Initialize the Smart Money Whale Strategy
        strategy = SmartMoneyWhaleStrategy(logger=logger)
        
        logger.info("✅ Services initialized successfully")
        logger.info(f"🐋🧠 Testing {strategy.name}")
        logger.info(f"📋 Strategy Description: {strategy.description}")
        
        # Display strategy criteria
        logger.info("\n🎯 Strategy Criteria:")
        criteria = strategy.whale_smart_money_criteria
        logger.info(f"   • Min Whale Count: {criteria['min_whale_count']}")
        logger.info(f"   • Min Whale Volume: ${criteria['min_whale_volume']:,}")
        logger.info(f"   • Min Smart Traders: {criteria['min_smart_traders']}")
        logger.info(f"   • Smart Money Skill Threshold: {criteria['smart_money_skill_threshold']:.1%}")
        logger.info(f"   • Min Confluence Score: {criteria['min_confluence_score']:.1%}")
        
        # Execute the strategy
        logger.info("\n🚀 Executing Smart Money Whale Strategy...")
        start_time = datetime.now()
        
        scan_id = f"test_smart_money_whale_{int(start_time.timestamp())}"
        discovered_tokens = await strategy.execute(birdeye_api, scan_id=scan_id)
        
        execution_time = (datetime.now() - start_time).total_seconds()
        
        # Display results
        logger.info(f"\n✅ Strategy execution completed in {execution_time:.2f}s")
        logger.info(f"🎯 Discovered {len(discovered_tokens)} high-conviction tokens")
        
        if discovered_tokens:
            logger.info("\n🏆 TOP SMART MONEY WHALE TOKENS:")
            logger.info("=" * 80)
            
            for i, token in enumerate(discovered_tokens[:10], 1):
                symbol = token.get('symbol', 'UNKNOWN')
                address = token.get('address', '')[:8] + '...'
                
                # Strategy-specific metrics
                combined_score = token.get('combined_whale_smart_money_score', 0)
                confluence_score = token.get('confluence_score', 0)
                whale_count = len(token.get('whale_analysis', {}).get('whales', []))
                smart_traders = token.get('smart_money_analysis', {}).get('skill_metrics', {}).get('skilled_count', 0)
                
                # Strategy analysis
                analysis = token.get('strategy_analysis', {})
                whale_strength = analysis.get('whale_signal_strength', 'unknown')
                smart_money_strength = analysis.get('smart_money_signal_strength', 'unknown')
                confluence_level = analysis.get('confluence_level', 'unknown')
                conviction_level = analysis.get('conviction_level', 'unknown')
                risk_level = analysis.get('risk_assessment', 'unknown')
                
                logger.info(f"\n#{i} {symbol} ({address})")
                logger.info(f"   🎯 Combined Score: {combined_score:.1f}")
                logger.info(f"   🤝 Confluence: {confluence_score:.2f} ({confluence_level})")
                logger.info(f"   🐋 Whales: {whale_count} ({whale_strength} signal)")
                logger.info(f"   🧠 Smart Traders: {smart_traders} ({smart_money_strength} signal)")
                logger.info(f"   💪 Conviction: {conviction_level}")
                logger.info(f"   ⚠️  Risk: {risk_level}")
                
                # Market data
                price = token.get('priceUsd', 0)
                volume_24h = token.get('volume24h', 0)
                liquidity = token.get('liquidity', 0)
                market_cap = token.get('marketCap', 0)
                
                logger.info(f"   💰 Price: ${price:.6f}")
                logger.info(f"   📊 Volume 24h: ${volume_24h:,.0f}")
                logger.info(f"   💧 Liquidity: ${liquidity:,.0f}")
                logger.info(f"   🏦 Market Cap: ${market_cap:,.0f}")
        
        else:
            logger.warning("❌ No tokens discovered by the strategy")
            logger.info("This could mean:")
            logger.info("   • No tokens currently meet the whale + smart money criteria")
            logger.info("   • Market conditions don't favor institutional activity")
            logger.info("   • Strategy parameters may be too restrictive")
        
        # Display strategy performance metrics
        logger.info("\n📈 STRATEGY PERFORMANCE:")
        logger.info("=" * 50)
        
        # Get cost optimization report if available
        try:
            cost_report = strategy.get_cost_optimization_report()
            logger.info(f"   💰 API Efficiency: {cost_report.get('efficiency_grade', 'Unknown')}")
            logger.info(f"   🔄 Batch APIs Used: {cost_report.get('batch_apis_enabled', False)}")
            
            cost_metrics = cost_report.get('cost_metrics', {})
            if cost_metrics.get('total_api_calls', 0) > 0:
                logger.info(f"   📞 Total API Calls: {cost_metrics['total_api_calls']}")
                logger.info(f"   💾 Batch Efficiency: {cost_metrics.get('batch_efficiency_ratio', 0):.1%}")
                
        except Exception as e:
            logger.debug(f"Could not get cost report: {e}")
        
        # Save results for analysis
        results_file = Path("scripts/results") / f"smart_money_whale_strategy_test_{scan_id}.json"
        results_file.parent.mkdir(exist_ok=True)
        
        try:
            with open(results_file, 'w') as f:
                json.dump({
                    'strategy_name': strategy.name,
                    'execution_time': execution_time,
                    'scan_id': scan_id,
                    'tokens_discovered': len(discovered_tokens),
                    'criteria': strategy.whale_smart_money_criteria,
                    'top_tokens': discovered_tokens[:5] if discovered_tokens else [],
                    'timestamp': start_time.isoformat()
                }, f, indent=2, default=str)
            
            logger.info(f"📁 Results saved to: {results_file}")
            
        except Exception as e:
            logger.warning(f"Could not save results: {e}")
        
        logger.info("\n🎉 Smart Money Whale Strategy test completed successfully!")
        
    except Exception as e:
        logger.error(f"❌ Error during strategy test: {e}")
        raise


async def test_strategy_components():
    """Test individual components of the strategy."""
    
    logger_setup = LoggerSetup("SmartMoneyWhaleComponentsTest", log_level="INFO")
    logger = logger_setup.logger
    
    logger.info("🧪 Testing Smart Money Whale Strategy Components")
    
    try:
        # Initialize strategy
        strategy = SmartMoneyWhaleStrategy(logger=logger)
        
        # Test criteria validation
        logger.info("\n🔍 Testing criteria validation...")
        
        # Mock whale analysis
        mock_whale_analysis = {
            "whales": [{"address": "whale1"}, {"address": "whale2"}, {"address": "whale3"}],
            "whale_analysis": {"total_volume": 1_000_000},
            "confidence": 0.75
        }
        
        # Mock smart money analysis
        mock_smart_money_analysis = {
            "skill_metrics": {
                "skilled_count": 5,
                "average_skill_score": 0.72
            },
            "smart_money_insights": {
                "skill_quality": "high"
            }
        }
        
        # Test whale criteria
        whale_meets_criteria = strategy._meets_whale_activity_criteria(mock_whale_analysis, {})
        logger.info(f"   🐋 Whale criteria test: {'✅ PASS' if whale_meets_criteria else '❌ FAIL'}")
        
        # Test smart money criteria
        smart_money_meets_criteria = strategy._meets_smart_money_criteria(mock_smart_money_analysis, {})
        logger.info(f"   🧠 Smart money criteria test: {'✅ PASS' if smart_money_meets_criteria else '❌ FAIL'}")
        
        # Test confluence calculation
        confluence_score = strategy._calculate_confluence_score(mock_whale_analysis, mock_smart_money_analysis)
        logger.info(f"   🤝 Confluence score: {confluence_score:.3f}")
        
        # Test combined scoring
        mock_token = {
            "score": 60.0,
            "whale_analysis": mock_whale_analysis,
            "smart_money_analysis": mock_smart_money_analysis,
            "confluence_score": confluence_score
        }
        
        combined_score = strategy._calculate_combined_whale_smart_money_score(mock_token)
        logger.info(f"   🎯 Combined score: {combined_score:.1f}")
        
        # Test signal strength classifications
        whale_strength = strategy._get_whale_signal_strength(mock_token)
        smart_money_strength = strategy._get_smart_money_signal_strength(mock_token)
        confluence_level = strategy._get_confluence_level(mock_token)
        
        logger.info(f"   📊 Signal strengths:")
        logger.info(f"      🐋 Whale: {whale_strength}")
        logger.info(f"      🧠 Smart Money: {smart_money_strength}")
        logger.info(f"      🤝 Confluence: {confluence_level}")
        
        logger.info("✅ Component tests completed successfully!")
        
    except Exception as e:
        logger.error(f"❌ Error during component tests: {e}")
        raise


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Test Smart Money Whale Strategy")
    parser.add_argument("--components-only", action="store_true", 
                       help="Test only strategy components without API calls")
    
    args = parser.parse_args()
    
    if args.components_only:
        asyncio.run(test_strategy_components())
    else:
        asyncio.run(test_smart_money_whale_strategy()) 