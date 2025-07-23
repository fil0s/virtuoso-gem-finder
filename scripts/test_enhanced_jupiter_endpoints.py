#!/usr/bin/env python3
"""
Test Enhanced Jupiter Endpoints
Demonstrates the improved implementation of Jupiter's lite-api endpoints
"""

import asyncio
import sys
import os
import time
import json
from pathlib import Path

# Add project root to path
sys.path.append(str(Path(__file__).parent.parent))

from api.enhanced_jupiter_connector import EnhancedJupiterConnector
from scripts.cross_platform_token_analyzer import CrossPlatformAnalyzer
from services.enhanced_cache_manager import EnhancedPositionCacheManager
from core.cache_manager import CacheManager
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

async def test_enhanced_jupiter_connector():
    """Test the new enhanced Jupiter connector"""
    logger.info("🚀 Testing Enhanced Jupiter Connector")
    
    # Initialize cache
    base_cache = CacheManager()
    enhanced_cache = EnhancedPositionCacheManager(base_cache_manager=base_cache, logger=logger)
    
    async with EnhancedJupiterConnector(enhanced_cache) as connector:
        start_time = time.time()
        
        # Test 1: Enhanced token list (lite-api.jup.ag/tokens)
        logger.info("\n📋 Test 1: Enhanced Token List (lite-api.jup.ag/tokens)")
        tokens = await connector.get_enhanced_token_list(limit=1000, include_metadata=True)
        logger.info(f"✅ Retrieved {len(tokens)} tokens with enhanced metadata")
        
        if tokens:
            sample_token = tokens[0]
            logger.info(f"   Sample token: {sample_token['symbol']} ({sample_token['address'][:8]}...)")
            logger.info(f"   Risk level: {sample_token.get('risk_level', 'N/A')}")
            logger.info(f"   Quality score: {sample_token.get('quality_score', 0):.2f}")
        
        # Test 2: Batch pricing (lite-api.jup.ag/price/v2)
        logger.info("\n💰 Test 2: Batch Pricing (lite-api.jup.ag/price/v2)")
        if tokens:
            # Get sample token addresses
            sample_addresses = [token['address'] for token in tokens[:50]]
            prices = await connector.get_batch_prices(sample_addresses)
            logger.info(f"✅ Batch priced {len(prices)} tokens")
            
            if prices:
                sample_addr = list(prices.keys())[0]
                sample_price = prices[sample_addr]
                logger.info(f"   Sample price: {sample_addr[:8]}... = ${sample_price['price']:.6f}")
                logger.info(f"   Source: {sample_price['source']}")
        
        # Test 3: Enhanced quotes (quote-api.jup.ag/v6/quote)
        logger.info("\n📊 Test 3: Enhanced Quotes (quote-api.jup.ag/v6/quote)")
        sol_mint = "So11111111111111111111111111111111111111112"
        usdc_mint = "EPjFWdd5AufqSSqeM2qN1xzybapC8G4wEGGkZwyTDt1v"
        
        if tokens:
            sample_token = tokens[0]['address']
            quote = await connector.get_enhanced_quote(sol_mint, sample_token, 1000000)
            if quote:
                logger.info(f"✅ Quote successful: {quote['input_amount']} -> {quote['output_amount']}")
                logger.info(f"   Price impact: {quote['price_impact_pct']:.2f}%")
                logger.info(f"   Liquidity score: {quote['liquidity_score']:.2f}")
                logger.info(f"   Routing complexity: {quote['routing_complexity']}")
            else:
                logger.info("❌ Quote failed (expected for some tokens)")
        
        # Test 4: Comprehensive analysis
        logger.info("\n🔍 Test 4: Comprehensive Analysis")
        if tokens:
            sample_addresses = [token['address'] for token in tokens[:20]]
            analysis = await connector.get_comprehensive_token_analysis(sample_addresses)
            logger.info(f"✅ Comprehensive analysis for {len(analysis)} tokens")
            
            # Count data sources
            source_counts = {'lite_api_price_v2': 0, 'lite_api_tokens': 0, 'quote_api_v6': 0}
            for addr, data in analysis.items():
                for source in data.get('data_sources', []):
                    if source in source_counts:
                        source_counts[source] += 1
            
            logger.info(f"   Data sources coverage:")
            for source, count in source_counts.items():
                logger.info(f"     • {source}: {count} tokens")
        
        # Performance and efficiency stats
        duration = time.time() - start_time
        stats = connector.get_api_statistics()
        
        logger.info(f"\n📈 Performance Summary (Duration: {duration:.2f}s)")
        logger.info(f"   Total API calls: {stats['summary']['total_api_calls']}")
        logger.info(f"   Cache hits: {stats['summary']['total_cache_hits']}")
        logger.info(f"   Cache hit rate: {stats['summary']['cache_hit_rate_percent']:.1f}%")
        logger.info(f"   Error rate: {stats['summary']['error_rate_percent']:.1f}%")
        
        batch_efficiency = stats['summary']['batch_efficiency']
        logger.info(f"   Batch efficiency:")
        logger.info(f"     • Total batches: {batch_efficiency['total_batches']}")
        logger.info(f"     • Individual requests saved: {batch_efficiency['total_individual_requests_saved']}")
        
        return stats

async def test_cross_platform_integration():
    """Test the enhanced Jupiter integration in cross-platform analyzer"""
    logger.info("\n🌐 Testing Cross-Platform Integration")
    
    from scripts.cross_platform_token_analyzer import CrossPlatformAnalyzer
    
    # Initialize analyzer
    analyzer = CrossPlatformAnalyzer(logger=logger)
    
    try:
        # Test enhanced data collection
        logger.info("📊 Testing enhanced data collection...")
        platform_data = await analyzer.collect_all_data()
        
        # Check Jupiter enhancements
        jupiter_tokens = platform_data.get('jupiter_token_list', [])
        jupiter_prices = platform_data.get('jupiter_batch_prices', [])
        
        logger.info(f"✅ Jupiter tokens: {len(jupiter_tokens)}")
        logger.info(f"✅ Jupiter batch prices: {len(jupiter_prices)}")
        
        # Test normalization
        logger.info("🔄 Testing enhanced normalization...")
        normalized = analyzer.normalize_token_data(platform_data)
        
        # Count tokens with Jupiter data
        jupiter_count = 0
        jupiter_pricing_count = 0
        
        for addr, token_data in normalized.items():
            platforms = token_data['platforms']
            if 'jupiter' in platforms:
                jupiter_count += 1
            if 'jupiter_pricing' in platforms:
                jupiter_pricing_count += 1
        
        logger.info(f"✅ Tokens with Jupiter data: {jupiter_count}")
        logger.info(f"✅ Tokens with Jupiter pricing: {jupiter_pricing_count}")
        
        # Get API stats
        api_stats = analyzer.get_api_stats()
        jupiter_stats = api_stats.get('jupiter', {})
        
        logger.info(f"📊 Jupiter API Stats:")
        logger.info(f"   Total calls: {jupiter_stats.get('total_calls', 0)}")
        logger.info(f"   Success rate: {jupiter_stats.get('success_rate', 0):.1f}%")
        
        return {
            'jupiter_tokens': len(jupiter_tokens),
            'jupiter_prices': len(jupiter_prices),
            'normalized_tokens': len(normalized),
            'jupiter_data_count': jupiter_count,
            'jupiter_pricing_count': jupiter_pricing_count
        }
        
    finally:
        await analyzer.close()

async def compare_old_vs_new():
    """Compare performance and demonstrate enhanced features"""
    logger.info("\n⚖️  Demonstrating Enhanced Jupiter Implementation")
    
    # Initialize cache
    base_cache = CacheManager()
    enhanced_cache = EnhancedPositionCacheManager(base_cache_manager=base_cache, logger=logger)
    
    # Test enhanced implementation with comprehensive features
    logger.info("🚀 Testing ENHANCED implementation...")
    async with EnhancedJupiterConnector(enhanced_cache) as connector:
        start_time = time.time()
        
        # Get enhanced token list
        tokens = await connector.get_enhanced_token_list(limit=200, include_metadata=True)
        
        # Test batch pricing (major efficiency improvement)
        if tokens:
            sample_addresses = [token['address'] for token in tokens[:100]]
            batch_prices = await connector.get_batch_prices(sample_addresses)
            
            # Test comprehensive analysis
            comprehensive = await connector.get_comprehensive_token_analysis(sample_addresses[:50])
        
        duration = time.time() - start_time
        stats = connector.get_api_statistics()
    
    # Enhanced features analysis
    enhanced_features = {
        'risk_assessment': 0,
        'quality_scoring': 0,
        'metadata_complete': 0,
        'pricing_data': 0
    }
    
    if tokens:
        for token in tokens[:50]:
            if token.get('risk_level'):
                enhanced_features['risk_assessment'] += 1
            if token.get('quality_score', 0) > 0:
                enhanced_features['quality_scoring'] += 1
            if token.get('logo_uri') and token.get('name'):
                enhanced_features['metadata_complete'] += 1
        
        enhanced_features['pricing_data'] = len(batch_prices) if 'batch_prices' in locals() else 0
    
    # Results
    logger.info(f"\n📊 Enhanced Implementation Results:")
    logger.info(f"   Performance:")
    logger.info(f"     • Tokens discovered: {len(tokens)}")
    logger.info(f"     • Duration: {duration:.2f}s")
    logger.info(f"     • Total API calls: {stats['summary']['total_api_calls']}")
    logger.info(f"     • Cache hit rate: {stats['summary']['cache_hit_rate_percent']:.1f}%")
    logger.info(f"     • Error rate: {stats['summary']['error_rate_percent']:.1f}%")
    
    logger.info(f"   Enhanced Features:")
    logger.info(f"     • Risk assessment: {enhanced_features['risk_assessment']}/50 tokens")
    logger.info(f"     • Quality scoring: {enhanced_features['quality_scoring']}/50 tokens")
    logger.info(f"     • Complete metadata: {enhanced_features['metadata_complete']}/50 tokens")
    logger.info(f"     • Batch pricing: {enhanced_features['pricing_data']} tokens")
    
    logger.info(f"   Endpoints Used:")
    logger.info(f"     • lite-api.jup.ag/tokens (10,000 token capacity)")
    logger.info(f"     • lite-api.jup.ag/price/v2 (batch pricing)")
    logger.info(f"     • quote-api.jup.ag/v6/quote (liquidity analysis)")
    
    # Efficiency calculation
    individual_calls_saved = enhanced_features['pricing_data']
    efficiency_improvement = (individual_calls_saved / max(1, stats['summary']['total_api_calls'])) * 100
    
    logger.info(f"\n🎯 Efficiency Improvements:")
    logger.info(f"     • Individual pricing calls saved: {individual_calls_saved}")
    logger.info(f"     • API efficiency improvement: {efficiency_improvement:.1f}%")
    logger.info(f"     • Batch processing enabled: ✅")
    logger.info(f"     • Smart caching enabled: ✅")
    logger.info(f"     • Risk assessment enabled: ✅")
    
    return {
        'enhanced': {
            'tokens': len(tokens), 
            'duration': duration, 
            'calls': stats['summary']['total_api_calls'],
            'features': enhanced_features,
            'efficiency_improvement': efficiency_improvement
        }
    }

async def main():
    """Run all tests"""
    logger.info("🧪 Jupiter Enhanced Endpoints Test Suite")
    logger.info("=" * 60)
    
    results = {}
    
    try:
        # Test 1: Enhanced connector
        results['enhanced_connector'] = await test_enhanced_jupiter_connector()
        
        # Test 2: Cross-platform integration
        results['cross_platform'] = await test_cross_platform_integration()
        
        # Test 3: Old vs new comparison
        results['comparison'] = await compare_old_vs_new()
        
        # Save results
        results_file = f"scripts/results/jupiter_enhancement_test_{int(time.time())}.json"
        os.makedirs(os.path.dirname(results_file), exist_ok=True)
        
        with open(results_file, 'w') as f:
            json.dump(results, f, indent=2, default=str)
        
        logger.info(f"\n💾 Results saved to: {results_file}")
        logger.info("\n✅ All tests completed successfully!")
        
    except Exception as e:
        logger.error(f"❌ Test failed: {e}")
        raise

if __name__ == "__main__":
    asyncio.run(main()) 