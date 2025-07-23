#!/usr/bin/env python3
"""
Meteora Cross-Platform Integration Test

Tests integration of Meteora API with existing cross-platform analysis structures
for enhanced trending token discovery in the discovery phase.
"""

import asyncio
import aiohttp
import json
import time
import sys
import os
from datetime import datetime
from typing import Dict, List, Set, Tuple, Optional, Any
from collections import defaultdict
import logging

# Add parent directories to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from scripts.cross_platform_token_analyzer import CrossPlatformAnalyzer
from services.enhanced_cache_manager import EnhancedPositionCacheManager
from core.cache_manager import CacheManager

class MeteoraConnector:
    """Enhanced Meteora API connector for pool-level trending discovery"""
    
    def __init__(self, enhanced_cache: Optional[EnhancedPositionCacheManager] = None):
        self.base_url = "https://universal-search-api.meteora.ag"
        self.enhanced_cache = enhanced_cache
        
        # API call tracking
        self.api_stats = {
            "total_calls": 0,
            "successful_calls": 0,
            "failed_calls": 0,
            "total_response_time_ms": 0,
            "endpoints_used": set(),
            "last_reset": time.time()
        }
        
        # Setup logging
        self.logger = logging.getLogger(__name__)
        
    def get_api_call_statistics(self) -> Dict[str, Any]:
        """Get API call statistics for reporting"""
        stats = self.api_stats.copy()
        stats["endpoints_used"] = list(stats["endpoints_used"])  # Convert set to list for JSON
        stats["average_response_time_ms"] = (
            stats["total_response_time_ms"] / max(1, stats["total_calls"])
        )
        return stats
    
    def reset_api_statistics(self):
        """Reset API call statistics"""
        self.api_stats = {
            "total_calls": 0,
            "successful_calls": 0,
            "failed_calls": 0,
            "total_response_time_ms": 0,
            "endpoints_used": set(),
            "last_reset": time.time()
        }
    
    async def _make_tracked_request(self, endpoint: str, params: Dict[str, Any] = None) -> Optional[Dict]:
        """Make a tracked API request to Meteora"""
        start_time = time.time()
        self.api_stats["total_calls"] += 1
        self.api_stats["endpoints_used"].add(endpoint)
        
        try:
            async with aiohttp.ClientSession() as session:
                url = f"{self.base_url}{endpoint}"
                async with session.get(url, params=params) as response:
                    response_time_ms = (time.time() - start_time) * 1000
                    self.api_stats["total_response_time_ms"] += response_time_ms
                    
                    if response.status == 200:
                        self.api_stats["successful_calls"] += 1
                        data = await response.json()
                        self.logger.info(f"🟢 Meteora API call successful: {endpoint} ({response.status}) - {response_time_ms:.1f}ms")
                        return data
                    else:
                        self.api_stats["failed_calls"] += 1
                        self.logger.warning(f"🔴 Meteora API call failed: {endpoint} ({response.status}) - {response_time_ms:.1f}ms")
                        return None
                        
        except Exception as e:
            response_time_ms = (time.time() - start_time) * 1000
            self.api_stats["total_response_time_ms"] += response_time_ms
            self.api_stats["failed_calls"] += 1
            self.logger.error(f"🔴 Meteora API error: {endpoint} - {e} - {response_time_ms:.1f}ms")
            return None
    
    async def get_trending_pools_by_volume(self, limit: int = 50) -> List[Dict]:
        """Get trending pools sorted by 24h volume"""
        # Check cache first
        cache_key = f"meteora_trending_volume_limit_{limit}"
        if self.enhanced_cache:
            cached_data = self.enhanced_cache.get_enhanced("meteora_trending", cache_key)
            if cached_data:
                return cached_data
        
        # Search for pools sorted by volume - FIXED PARAMETERS
        params = {
            "q": "*",  # Required parameter for all results
            "sort_by": "volume_24h:desc",  # Correct sorting format
            "limit": limit
        }
        
        data = await self._make_tracked_request("/pool/search", params)
        
        if not data or not isinstance(data, dict):
            return []
        
        # Extract pools from response - FIXED DATA STRUCTURE
        pools = data.get('hits', [])
        if pools:
            # Extract pool documents from hits
            pools = [hit.get('document', {}) for hit in pools]
        
        # Process and enhance pool data
        trending_pools = []
        for pool in pools:
            if isinstance(pool, dict):
                # Calculate VLR (Volume-to-Liquidity Ratio)
                volume_24h = pool.get('volume_24h', 0)
                tvl = pool.get('tvl', 1)  # Avoid division by zero
                vlr = volume_24h / tvl if tvl > 0 else 0
                
                # Extract token information
                token_mints = pool.get('token_mints', [])
                
                enhanced_pool = {
                    'pool_address': pool.get('id', pool.get('pool_mint', '')),  # Fixed field mapping
                    'pool_type': pool.get('pool_type', ''),
                    'tvl': tvl,
                    'volume_24h': volume_24h,
                    'fee_24h': pool.get('fee_24h', 0),
                    'token_mints': token_mints,
                    'vlr': round(vlr, 4),
                    'volume_tier': self._get_volume_tier(volume_24h),
                    'liquidity_tier': self._get_liquidity_tier(tvl),
                    'trending_score': self._calculate_pool_trending_score(pool, vlr),
                    'discovery_source': 'meteora_volume_trending'
                }
                trending_pools.append(enhanced_pool)
        
        # Cache the result
        if trending_pools and self.enhanced_cache:
            self.enhanced_cache.set_enhanced("meteora_trending", cache_key, trending_pools)
        
        self.logger.info(f"📊 Fetched {len(trending_pools)} trending pools by volume from Meteora")
        return trending_pools
    
    async def get_trending_pools_by_tvl(self, limit: int = 50) -> List[Dict]:
        """Get trending pools sorted by TVL"""
        # Check cache first
        cache_key = f"meteora_trending_tvl_limit_{limit}"
        if self.enhanced_cache:
            cached_data = self.enhanced_cache.get_enhanced("meteora_trending", cache_key)
            if cached_data:
                return cached_data
        
        # Search for pools sorted by TVL - FIXED PARAMETERS
        params = {
            "q": "*",  # Required parameter for all results
            "sort_by": "tvl:desc",  # Correct sorting format
            "limit": limit
        }
        
        data = await self._make_tracked_request("/pool/search", params)
        
        if not data or not isinstance(data, dict):
            return []
        
        # Extract pools from response - FIXED DATA STRUCTURE  
        pools = data.get('hits', [])
        if pools:
            # Extract pool documents from hits
            pools = [hit.get('document', {}) for hit in pools]
        
        # Process and enhance pool data
        trending_pools = []
        for pool in pools:
            if isinstance(pool, dict):
                # Calculate VLR (Volume-to-Liquidity Ratio)
                volume_24h = pool.get('volume_24h', 0)
                tvl = pool.get('tvl', 1)
                vlr = volume_24h / tvl if tvl > 0 else 0
                
                # Extract token information
                token_mints = pool.get('token_mints', [])
                
                enhanced_pool = {
                    'pool_address': pool.get('id', pool.get('pool_mint', '')),  # Fixed field mapping
                    'pool_type': pool.get('pool_type', ''),
                    'tvl': tvl,
                    'volume_24h': volume_24h,
                    'fee_24h': pool.get('fee_24h', 0),
                    'token_mints': token_mints,
                    'vlr': round(vlr, 4),
                    'volume_tier': self._get_volume_tier(volume_24h),
                    'liquidity_tier': self._get_liquidity_tier(tvl),
                    'trending_score': self._calculate_pool_trending_score(pool, vlr),
                    'discovery_source': 'meteora_tvl_trending'
                }
                trending_pools.append(enhanced_pool)
        
        # Cache the result
        if trending_pools and self.enhanced_cache:
            self.enhanced_cache.set_enhanced("meteora_trending", cache_key, trending_pools)
        
        self.logger.info(f"📊 Fetched {len(trending_pools)} trending pools by TVL from Meteora")
        return trending_pools
    
    def extract_trending_tokens(self, pools: List[Dict]) -> List[Dict]:
        """Extract trending tokens from pool data"""
        token_data = {}
        
        for pool in pools:
            token_mints = pool.get('token_mints', [])
            
            for token_address in token_mints:
                if not token_address or token_address in ['So11111111111111111111111111111111111111112']:  # Skip SOL
                    continue
                
                if token_address not in token_data:
                    token_data[token_address] = {
                        'address': token_address,
                        'pools': [],
                        'total_tvl': 0,
                        'total_volume_24h': 0,
                        'total_fees_24h': 0,
                        'pool_count': 0,
                        'max_vlr': 0,
                        'discovery_source': 'meteora_pool_extraction'
                    }
                
                # Aggregate data from all pools containing this token
                token_info = token_data[token_address]
                token_info['pools'].append({
                    'pool_address': pool.get('pool_address', ''),
                    'pool_type': pool.get('pool_type', ''),
                    'tvl': pool.get('tvl', 0),
                    'volume_24h': pool.get('volume_24h', 0),
                    'vlr': pool.get('vlr', 0)
                })
                
                token_info['total_tvl'] += pool.get('tvl', 0)
                token_info['total_volume_24h'] += pool.get('volume_24h', 0)
                token_info['total_fees_24h'] += pool.get('fee_24h', 0)
                token_info['pool_count'] += 1
                token_info['max_vlr'] = max(token_info['max_vlr'], pool.get('vlr', 0))
        
        # Convert to list and calculate additional metrics
        trending_tokens = []
        for token_address, data in token_data.items():
            # Calculate aggregate VLR
            aggregate_vlr = data['total_volume_24h'] / data['total_tvl'] if data['total_tvl'] > 0 else 0
            
            # Calculate liquidity distribution score
            liquidity_distribution = self._calculate_liquidity_distribution(data['pools'])
            
            # Calculate trending score
            trending_score = self._calculate_token_trending_score(data, aggregate_vlr, liquidity_distribution)
            
            token_info = {
                'address': token_address,
                'total_tvl': data['total_tvl'],
                'total_volume_24h': data['total_volume_24h'],
                'total_fees_24h': data['total_fees_24h'],
                'pool_count': data['pool_count'],
                'aggregate_vlr': round(aggregate_vlr, 4),
                'max_vlr': data['max_vlr'],
                'liquidity_distribution_score': liquidity_distribution,
                'trending_score': trending_score,
                'pools': data['pools'],
                'discovery_source': 'meteora_token_aggregation'
            }
            trending_tokens.append(token_info)
        
        # Sort by trending score
        trending_tokens.sort(key=lambda x: x['trending_score'], reverse=True)
        
        self.logger.info(f"🎯 Extracted {len(trending_tokens)} trending tokens from Meteora pools")
        return trending_tokens
    
    def _get_volume_tier(self, volume_24h: float) -> str:
        """Classify volume tier"""
        if volume_24h >= 10000000:  # $10M+
            return "MEGA_VOLUME"
        elif volume_24h >= 5000000:  # $5M+
            return "HIGH_VOLUME"
        elif volume_24h >= 1000000:  # $1M+
            return "MEDIUM_VOLUME"
        elif volume_24h >= 100000:   # $100K+
            return "LOW_VOLUME"
        else:
            return "MINIMAL_VOLUME"
    
    def _get_liquidity_tier(self, tvl: float) -> str:
        """Classify liquidity tier"""
        if tvl >= 50000000:  # $50M+
            return "MEGA_LIQUIDITY"
        elif tvl >= 10000000:  # $10M+
            return "HIGH_LIQUIDITY"
        elif tvl >= 1000000:   # $1M+
            return "MEDIUM_LIQUIDITY"
        elif tvl >= 100000:    # $100K+
            return "LOW_LIQUIDITY"
        else:
            return "MINIMAL_LIQUIDITY"
    
    def _calculate_pool_trending_score(self, pool: Dict, vlr: float) -> float:
        """Calculate pool trending score (0-100)"""
        score = 0.0
        
        # Volume scoring (0-40 points)
        volume_24h = pool.get('volume_24h', 0)
        if volume_24h >= 10000000:  # $10M+
            score += 40.0
        elif volume_24h >= 5000000:  # $5M+
            score += 30.0
        elif volume_24h >= 1000000:  # $1M+
            score += 20.0
        elif volume_24h >= 100000:   # $100K+
            score += 10.0
        
        # TVL scoring (0-30 points)
        tvl = pool.get('tvl', 0)
        if tvl >= 50000000:  # $50M+
            score += 30.0
        elif tvl >= 10000000:  # $10M+
            score += 25.0
        elif tvl >= 1000000:   # $1M+
            score += 15.0
        elif tvl >= 100000:    # $100K+
            score += 5.0
        
        # VLR scoring (0-20 points)
        if vlr >= 10.0:
            score += 20.0  # Extreme activity
        elif vlr >= 5.0:
            score += 15.0  # Very high activity
        elif vlr >= 2.0:
            score += 10.0  # High activity
        elif vlr >= 1.0:
            score += 5.0   # Moderate activity
        
        # Fee generation scoring (0-10 points)
        fee_24h = pool.get('fee_24h', 0)
        if fee_24h >= 100000:  # $100K+
            score += 10.0
        elif fee_24h >= 50000:  # $50K+
            score += 7.0
        elif fee_24h >= 10000:  # $10K+
            score += 4.0
        elif fee_24h >= 1000:   # $1K+
            score += 2.0
        
        return min(100.0, round(score, 1))
    
    def _calculate_liquidity_distribution(self, pools: List[Dict]) -> float:
        """Calculate liquidity distribution score (0-10)"""
        if not pools:
            return 0.0
        
        # Score based on number of pools and TVL distribution
        pool_count_score = min(len(pools) * 2, 6)  # Up to 6 points for multiple pools
        
        # Calculate TVL variance for distribution score
        tvls = [pool.get('tvl', 0) for pool in pools]
        if len(tvls) > 1:
            avg_tvl = sum(tvls) / len(tvls)
            variance = sum((tvl - avg_tvl) ** 2 for tvl in tvls) / len(tvls)
            # Lower variance = better distribution = higher score
            distribution_score = max(0, 4 - (variance / avg_tvl if avg_tvl > 0 else 0))
        else:
            distribution_score = 2  # Single pool gets moderate score
        
        return min(10.0, round(pool_count_score + distribution_score, 1))
    
    def _calculate_token_trending_score(self, data: Dict, aggregate_vlr: float, liquidity_distribution: float) -> float:
        """Calculate token trending score based on aggregated pool data (0-100)"""
        score = 0.0
        
        # Total volume scoring (0-35 points)
        total_volume = data['total_volume_24h']
        if total_volume >= 50000000:  # $50M+
            score += 35.0
        elif total_volume >= 20000000:  # $20M+
            score += 30.0
        elif total_volume >= 10000000:  # $10M+
            score += 25.0
        elif total_volume >= 5000000:   # $5M+
            score += 20.0
        elif total_volume >= 1000000:   # $1M+
            score += 15.0
        elif total_volume >= 500000:    # $500K+
            score += 10.0
        
        # Total TVL scoring (0-25 points)
        total_tvl = data['total_tvl']
        if total_tvl >= 100000000:  # $100M+
            score += 25.0
        elif total_tvl >= 50000000:  # $50M+
            score += 20.0
        elif total_tvl >= 10000000:  # $10M+
            score += 15.0
        elif total_tvl >= 1000000:   # $1M+
            score += 10.0
        elif total_tvl >= 100000:    # $100K+
            score += 5.0
        
        # Aggregate VLR scoring (0-20 points)
        if aggregate_vlr >= 5.0:
            score += 20.0
        elif aggregate_vlr >= 2.0:
            score += 15.0
        elif aggregate_vlr >= 1.0:
            score += 10.0
        elif aggregate_vlr >= 0.5:
            score += 5.0
        
        # Pool diversity scoring (0-10 points)
        pool_count = data['pool_count']
        if pool_count >= 5:
            score += 10.0
        elif pool_count >= 3:
            score += 7.0
        elif pool_count >= 2:
            score += 4.0
        elif pool_count >= 1:
            score += 2.0
        
        # Liquidity distribution scoring (0-10 points)
        score += liquidity_distribution
        
        return min(100.0, round(score, 1))

class EnhancedCrossPlatformAnalyzer(CrossPlatformAnalyzer):
    """Enhanced analyzer that includes Meteora integration"""
    
    def __init__(self, config: Optional[Dict] = None, logger: Optional[logging.Logger] = None):
        super().__init__(config, logger)
        
        # Initialize Meteora connector
        self.meteora = MeteoraConnector(self.enhanced_cache)
        
        self.logger.info("🚀 Enhanced Cross-Platform Analyzer initialized with Meteora integration")
    
    async def collect_all_data(self) -> Dict[str, List[Dict]]:
        """Enhanced data collection including Meteora trending pools"""
        self.logger.info("Starting enhanced parallel data collection including Meteora...")
        
        # Get base platform data
        base_results = await super().collect_all_data()
        
        # Add Meteora tasks
        meteora_tasks = [
            ('meteora_volume_trending', self.meteora.get_trending_pools_by_volume(30)),
            ('meteora_tvl_trending', self.meteora.get_trending_pools_by_tvl(30))
        ]
        
        # Execute Meteora tasks
        meteora_completed = await asyncio.gather(*[task for _, task in meteora_tasks], return_exceptions=True)
        
        for (name, _), result in zip(meteora_tasks, meteora_completed):
            if isinstance(result, Exception):
                self.logger.error(f"Error in {name}: {result}")
                base_results[name] = []
            else:
                base_results[name] = result if result else []
        
        # Extract trending tokens from Meteora pools
        all_meteora_pools = []
        all_meteora_pools.extend(base_results.get('meteora_volume_trending', []))
        all_meteora_pools.extend(base_results.get('meteora_tvl_trending', []))
        
        # Remove duplicates based on pool address
        seen_pools = set()
        unique_pools = []
        for pool in all_meteora_pools:
            pool_addr = pool.get('pool_address', '')
            if pool_addr and pool_addr not in seen_pools:
                seen_pools.add(pool_addr)
                unique_pools.append(pool)
        
        # Extract trending tokens
        meteora_tokens = self.meteora.extract_trending_tokens(unique_pools)
        base_results['meteora_trending_tokens'] = meteora_tokens
        
        # Log enhanced collection results
        self.logger.info(f"📊 Enhanced data collection with Meteora completed:")
        self.logger.info(f"  🌊 Meteora volume pools: {len(base_results.get('meteora_volume_trending', []))}")
        self.logger.info(f"  💰 Meteora TVL pools: {len(base_results.get('meteora_tvl_trending', []))}")
        self.logger.info(f"  🎯 Meteora trending tokens: {len(meteora_tokens)}")
        
        return base_results
    
    def normalize_token_data(self, platform_data: Dict[str, List[Dict]]) -> Dict[str, Dict]:
        """Enhanced normalization including Meteora data"""
        # Get base normalized data
        normalized = super().normalize_token_data(platform_data)
        
        # Add Meteora trending tokens
        for token in platform_data.get('meteora_trending_tokens', []):
            addr = token.get('address', '')
            if addr:
                if addr not in normalized:
                    normalized[addr] = {'platforms': set(), 'data': {}}
                
                normalized[addr]['platforms'].add('meteora')
                normalized[addr]['data']['meteora'] = {
                    'total_tvl': token.get('total_tvl', 0),
                    'total_volume_24h': token.get('total_volume_24h', 0),
                    'total_fees_24h': token.get('total_fees_24h', 0),
                    'pool_count': token.get('pool_count', 0),
                    'aggregate_vlr': token.get('aggregate_vlr', 0),
                    'max_vlr': token.get('max_vlr', 0),
                    'liquidity_distribution_score': token.get('liquidity_distribution_score', 0),
                    'trending_score': token.get('trending_score', 0),
                    'pools': token.get('pools', []),
                    'discovery_source': 'meteora_trending'
                }
                
                # Register token for enhanced caching
                self.enhanced_cache.register_tracked_token(addr)
        
        return dict(normalized)
    
    def _calculate_token_score(self, token_data: Dict) -> float:
        """Enhanced scoring including Meteora signals"""
        # Get base score
        score = super()._calculate_token_score(token_data)
        
        # Add Meteora scoring - Max: 25 points
        if 'meteora' in token_data['data']:
            meteora_data = token_data['data']['meteora']
            
            # Pool liquidity scoring (0-10 points)
            total_tvl = meteora_data.get('total_tvl', 0)
            if total_tvl >= 100000000:  # $100M+
                score += 10.0
            elif total_tvl >= 50000000:  # $50M+
                score += 8.0
            elif total_tvl >= 10000000:  # $10M+
                score += 6.0
            elif total_tvl >= 1000000:   # $1M+
                score += 4.0
            elif total_tvl >= 100000:    # $100K+
                score += 2.0
            
            # Volume activity scoring (0-8 points)
            total_volume = meteora_data.get('total_volume_24h', 0)
            if total_volume >= 50000000:  # $50M+
                score += 8.0
            elif total_volume >= 20000000:  # $20M+
                score += 6.0
            elif total_volume >= 5000000:   # $5M+
                score += 4.0
            elif total_volume >= 1000000:   # $1M+
                score += 2.0
            
            # VLR momentum scoring (0-5 points)
            aggregate_vlr = meteora_data.get('aggregate_vlr', 0)
            if aggregate_vlr >= 5.0:
                score += 5.0
            elif aggregate_vlr >= 2.0:
                score += 3.0
            elif aggregate_vlr >= 1.0:
                score += 2.0
            
            # Pool diversity bonus (0-2 points)
            pool_count = meteora_data.get('pool_count', 0)
            if pool_count >= 3:
                score += 2.0
            elif pool_count >= 2:
                score += 1.0
        
        # Ensure score is within 0-100 range
        final_score = max(0.0, min(100.0, score))
        return round(final_score, 1)
    
    def get_api_stats(self) -> Dict[str, Dict[str, Any]]:
        """Enhanced API stats including Meteora"""
        stats = super().get_api_stats()
        
        # Add Meteora stats
        if hasattr(self, 'meteora') and self.meteora:
            meteora_stats = self.meteora.get_api_call_statistics()
            stats['meteora'] = {
                'calls': meteora_stats.get('total_calls', 0),
                'successes': meteora_stats.get('successful_calls', 0),
                'failures': meteora_stats.get('failed_calls', 0),
                'total_time_ms': meteora_stats.get('total_response_time_ms', 0),
                'estimated_cost': 0.0  # Meteora is free
            }
        
        return stats

async def test_meteora_cross_platform_integration():
    """Test Meteora integration with cross-platform analysis"""
    print("\n🚀 Testing Meteora Cross-Platform Integration")
    print("=" * 60)
    
    # Setup logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    analyzer = None
    try:
        # Initialize enhanced analyzer
        print("🔧 Initializing Enhanced Cross-Platform Analyzer...")
        analyzer = EnhancedCrossPlatformAnalyzer()
        
        # Run enhanced analysis
        print("📊 Running enhanced cross-platform analysis with Meteora...")
        start_time = time.time()
        
        results = await analyzer.run_analysis()
        
        execution_time = time.time() - start_time
        
        # Print results
        print(f"\n✅ Analysis completed in {execution_time:.2f}s")
        print("=" * 60)
        
        if 'error' in results:
            print(f"❌ Analysis failed: {results['error']}")
            return
        
        # Platform data summary
        print("📊 PLATFORM DATA SUMMARY:")
        platform_counts = results['platform_data_counts']
        for platform, count in platform_counts.items():
            print(f"  • {platform}: {count} items")
        
        # Cross-platform correlation summary
        correlations = results['correlations']
        print(f"\n🔍 CORRELATION ANALYSIS:")
        print(f"  • Total unique tokens: {correlations['total_tokens']}")
        print(f"  • Multi-platform tokens: {len(correlations['multi_platform_tokens'])}")
        print(f"  • High-conviction tokens: {len(correlations['high_conviction_tokens'])}")
        
        # Platform distribution
        print(f"\n📈 PLATFORM DISTRIBUTION:")
        platform_dist = correlations['platform_distribution']
        for platform_count, token_count in platform_dist.items():
            print(f"  • {platform_count} platform(s): {token_count} tokens")
        
        # Top multi-platform tokens
        print(f"\n🏆 TOP MULTI-PLATFORM TOKENS:")
        top_tokens = correlations['multi_platform_tokens'][:10]
        for i, token in enumerate(top_tokens, 1):
            platforms = ', '.join(token['platforms'])
            symbol = token.get('symbol', 'Unknown')
            print(f"  {i:2d}. {symbol} - Score: {token['score']} - Platforms: {platforms}")
        
        # Meteora-specific insights
        print(f"\n🌊 METEORA-SPECIFIC INSIGHTS:")
        meteora_tokens = [t for t in correlations['all_tokens'].values() if 'meteora' in t.get('platforms', [])]
        print(f"  • Meteora tokens discovered: {len(meteora_tokens)}")
        
        if meteora_tokens:
            # Find top Meteora token
            top_meteora = max(meteora_tokens, key=lambda x: x.get('score', 0))
            print(f"  • Top Meteora token: {top_meteora.get('symbol', 'Unknown')} (Score: {top_meteora.get('score', 0)})")
            
            # Cross-platform Meteora tokens
            cross_platform_meteora = [t for t in meteora_tokens if len(t.get('platforms', [])) > 1]
            print(f"  • Cross-platform Meteora tokens: {len(cross_platform_meteora)}")
        
        # API performance summary
        print(f"\n⚡ API PERFORMANCE SUMMARY:")
        api_stats = analyzer.get_api_stats()
        for platform, stats in api_stats.items():
            success_rate = (stats['successes'] / max(1, stats['calls'])) * 100
            avg_time = stats['total_time_ms'] / max(1, stats['calls'])
            print(f"  • {platform.capitalize()}: {stats['calls']} calls, {success_rate:.1f}% success, {avg_time:.0f}ms avg")
        
        # Cache performance
        cache_stats = results['cache_statistics']
        print(f"\n🚀 CACHE PERFORMANCE:")
        print(f"  • Hit rate: {cache_stats['hit_rate_percent']:.1f}%")
        print(f"  • Cost savings: ${cache_stats['estimated_cost_savings_usd']:.4f}")
        
        # Key insights
        print(f"\n💡 KEY INSIGHTS:")
        for insight in results['insights']:
            print(f"  • {insight}")
        
        # Save detailed results
        timestamp = int(time.time())
        output_file = f"scripts/tests/meteora_cross_platform_test_{timestamp}.json"
        
        os.makedirs("scripts/tests", exist_ok=True)
        with open(output_file, 'w') as f:
            json.dump(results, f, indent=2)
        
        print(f"\n📁 Detailed results saved to: {output_file}")
        
    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
    finally:
        if analyzer:
            await analyzer.close()

if __name__ == "__main__":
    asyncio.run(test_meteora_cross_platform_integration())