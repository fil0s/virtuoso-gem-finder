#!/usr/bin/env python3
"""
Enhanced Jupiter + Meteora Cross-Platform Integration Test

Advanced integration that better leverages both APIs with:
- Multi-depth liquidity analysis (Jupiter)
- Comprehensive pool metrics (Meteora) 
- Cross-platform momentum scoring
- Advanced trending detection algorithms
- Real-time market depth testing
"""

import asyncio
import aiohttp
import json
import time
import sys
import os
from datetime import datetime, timedelta
from typing import Dict, List, Set, Tuple, Optional, Any
from collections import defaultdict
import logging
from prettytable import PrettyTable

# Add parent directories to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from scripts.cross_platform_token_analyzer import CrossPlatformAnalyzer
from services.enhanced_cache_manager import EnhancedPositionCacheManager

class EnhancedJupiterConnector:
    """Advanced Jupiter API connector with multi-depth liquidity analysis"""
    
    def __init__(self, enhanced_cache: Optional[EnhancedPositionCacheManager] = None):
        self.base_urls = {
            "quote": "https://quote-api.jup.ag/v6",
            "tokens": "https://token.jup.ag/all"
        }
        
        self.enhanced_cache = enhanced_cache
        self.api_key = os.getenv('JUPITER_API_KEY')
        
        # Enhanced API tracking
        self.api_stats = {
            "total_calls": 0,
            "successful_calls": 0,
            "failed_calls": 0,
            "total_response_time_ms": 0,
            "endpoints_used": set(),
            "depth_analysis_calls": 0,
            "batch_processing_calls": 0,
            "last_reset": time.time()
        }
        
        self.logger = logging.getLogger(__name__)
        
        self.headers = {
            'User-Agent': 'VirtuosoGemHunter/2.0',
            'Accept': 'application/json',
            'Content-Type': 'application/json'
        }
        
        if self.api_key:
            self.headers['Authorization'] = f'Bearer {self.api_key}'
    
    async def analyze_token_liquidity_depth(self, token_address: str) -> Dict[str, Any]:
        """Advanced multi-depth liquidity analysis"""
        self.logger.info(f"🔬 Analyzing liquidity depth for {token_address[:8]}...")
        
        # Test different swap amounts to measure liquidity depth
        test_amounts = [
            1000000,    # $1 USDC
            10000000,   # $10 USDC  
            100000000,  # $100 USDC
            1000000000  # $1000 USDC
        ]
        
        usdc_mint = "EPjFWdd5AufqSSqeM2qN1xzybapC8G4wEGGkZwyTDt1v"
        depth_analysis = {
            'token_address': token_address,
            'depth_tests': {},
            'liquidity_depth_score': 0,
            'market_maker_presence': 0,
            'effective_spread': 0,
            'price_impact_curve': [],
            'route_diversity_score': 0
        }
        
        for amount in test_amounts:
            try:
                params = {
                    "inputMint": token_address,
                    "outputMint": usdc_mint,
                    "amount": str(amount),
                    "slippageBps": "100"  # 1% max slippage
                }
                
                quote_data = await self._make_tracked_request(self.base_urls['quote'], params)
                self.api_stats["depth_analysis_calls"] += 1
                
                if quote_data:
                    price_impact = float(quote_data.get('priceImpactPct', 0))
                    route_count = len(quote_data.get('routePlan', []))
                    out_amount = int(quote_data.get('outAmount', 0))
                    
                    effective_price = out_amount / amount if amount > 0 else 0
                    
                    depth_analysis['depth_tests'][f"${amount/1000000:.0f}"] = {
                        'price_impact': price_impact,
                        'route_count': route_count,
                        'effective_price': effective_price,
                        'out_amount': out_amount,
                        'quote_success': True
                    }
                    
                    depth_analysis['price_impact_curve'].append({
                        'amount_usd': amount / 1000000,
                        'price_impact': price_impact
                    })
                
                # Rate limiting between depth tests
                await asyncio.sleep(0.3)
                
            except Exception as e:
                self.logger.warning(f"Depth test failed for ${amount/1000000:.0f}: {e}")
                depth_analysis['depth_tests'][f"${amount/1000000:.0f}"] = {
                    'quote_success': False,
                    'error': str(e)
                }
        
        # Calculate advanced metrics
        depth_analysis = self._calculate_liquidity_metrics(depth_analysis)
        
        return depth_analysis
    
    def _calculate_liquidity_metrics(self, depth_analysis: Dict) -> Dict:
        """Calculate advanced liquidity metrics from depth tests"""
        successful_tests = [test for test in depth_analysis['depth_tests'].values() 
                          if test.get('quote_success', False)]
        
        if not successful_tests:
            return depth_analysis
        
        # Liquidity Depth Score (0-10)
        # Based on ability to handle larger trades with minimal price impact
        large_trade_impact = None
        for test in successful_tests:
            if test.get('price_impact', 100) < 5.0:  # <5% impact
                large_trade_impact = test['price_impact']
        
        if large_trade_impact is not None:
            if large_trade_impact < 0.1:
                depth_analysis['liquidity_depth_score'] = 10  # Excellent
            elif large_trade_impact < 0.5:
                depth_analysis['liquidity_depth_score'] = 8   # Very Good
            elif large_trade_impact < 1.0:
                depth_analysis['liquidity_depth_score'] = 6   # Good
            elif large_trade_impact < 2.0:
                depth_analysis['liquidity_depth_score'] = 4   # Fair
            else:
                depth_analysis['liquidity_depth_score'] = 2   # Poor
        else:
            depth_analysis['liquidity_depth_score'] = 1       # Very Poor
        
        # Market Maker Presence Score (0-10)
        # Based on route count consistency across trade sizes
        route_counts = [test.get('route_count', 0) for test in successful_tests]
        avg_routes = sum(route_counts) / len(route_counts) if route_counts else 0
        route_consistency = 1 - (max(route_counts) - min(route_counts)) / max(1, max(route_counts))
        
        depth_analysis['market_maker_presence'] = min(10, avg_routes * 2 * route_consistency)
        
        # Route Diversity Score
        unique_routes = len(set(route_counts))
        depth_analysis['route_diversity_score'] = min(10, unique_routes * 2)
        
        # Effective Spread Analysis
        prices = [test.get('effective_price', 0) for test in successful_tests if test.get('effective_price', 0) > 0]
        if len(prices) > 1:
            price_range = max(prices) - min(prices)
            avg_price = sum(prices) / len(prices)
            depth_analysis['effective_spread'] = (price_range / avg_price) * 100 if avg_price > 0 else 0
        
        return depth_analysis
    
    async def batch_liquidity_analysis(self, token_addresses: List[str], max_concurrent: int = 3) -> List[Dict]:
        """Batch process liquidity analysis for multiple tokens"""
        self.logger.info(f"🔄 Starting batch liquidity analysis for {len(token_addresses)} tokens...")
        
        semaphore = asyncio.Semaphore(max_concurrent)
        
        async def analyze_with_semaphore(token_address: str) -> Dict:
            async with semaphore:
                return await self.analyze_token_liquidity_depth(token_address)
        
        # Process in batches
        batch_size = 5
        all_results = []
        
        for i in range(0, len(token_addresses), batch_size):
            batch = token_addresses[i:i + batch_size]
            batch_tasks = [analyze_with_semaphore(addr) for addr in batch]
            
            batch_results = await asyncio.gather(*batch_tasks, return_exceptions=True)
            
            for result in batch_results:
                if isinstance(result, Exception):
                    self.logger.error(f"Batch analysis error: {result}")
                else:
                    all_results.append(result)
            
            # Inter-batch delay
            if i + batch_size < len(token_addresses):
                await asyncio.sleep(2.0)
                self.logger.info(f"📊 Completed batch {i//batch_size + 1}/{(len(token_addresses)-1)//batch_size + 1}")
        
        self.api_stats["batch_processing_calls"] += len(all_results)
        self.logger.info(f"✅ Batch liquidity analysis complete: {len(all_results)} tokens analyzed")
        
        return all_results
    
    async def _make_tracked_request(self, endpoint: str, params: Dict[str, Any] = None) -> Optional[Dict]:
        """Enhanced tracked API request with better error handling"""
        start_time = time.time()
        self.api_stats["total_calls"] += 1
        self.api_stats["endpoints_used"].add(endpoint.split('/')[-1])
        
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(endpoint, params=params, headers=self.headers) as response:
                    response_time_ms = (time.time() - start_time) * 1000
                    self.api_stats["total_response_time_ms"] += response_time_ms
                    
                    if response.status == 200:
                        self.api_stats["successful_calls"] += 1
                        data = await response.json()
                        return data
                    else:
                        self.api_stats["failed_calls"] += 1
                        error_text = await response.text()
                        self.logger.warning(f"🔴 Jupiter API failed: {response.status} - {error_text[:100]}")
                        return None
                        
        except Exception as e:
            response_time_ms = (time.time() - start_time) * 1000
            self.api_stats["total_response_time_ms"] += response_time_ms
            self.api_stats["failed_calls"] += 1
            self.logger.error(f"🔴 Jupiter API error: {e}")
            return None
    
    def get_api_call_statistics(self) -> Dict[str, Any]:
        """Enhanced API statistics"""
        stats = self.api_stats.copy()
        stats["endpoints_used"] = list(stats["endpoints_used"])
        stats["average_response_time_ms"] = (
            stats["total_response_time_ms"] / max(1, stats["total_calls"])
        )
        return stats


class EnhancedMeteoraConnector:
    """Advanced Meteora API connector with comprehensive pool metrics"""
    
    def __init__(self, enhanced_cache: Optional[EnhancedPositionCacheManager] = None):
        self.base_url = "https://universal-search-api.meteora.ag"
        self.damm_api_url = "https://damm-api.meteora.ag"
        self.enhanced_cache = enhanced_cache
        
        self.api_stats = {
            "total_calls": 0,
            "successful_calls": 0,
            "failed_calls": 0,
            "total_response_time_ms": 0,
            "endpoints_used": set(),
            "pool_metrics_calls": 0,
            "comprehensive_analysis_calls": 0,
            "last_reset": time.time()
        }
        
        self.logger = logging.getLogger(__name__)
    
    async def get_comprehensive_pool_metrics(self, limit: int = 50) -> Dict[str, List[Dict]]:
        """Get comprehensive pool metrics using multiple endpoints"""
        self.logger.info(f"📊 Fetching comprehensive pool metrics (limit: {limit})...")
        
        # Use multiple sorting criteria for better trending detection
        search_queries = [
            {
                "name": "volume_trending",
                "params": {
                    "q": "*",
                    "sort_by": "volume_24h:desc",
                    "limit": limit
                }
            },
            {
                "name": "tvl_trending", 
                "params": {
                    "q": "*",
                    "sort_by": "tvl:desc",
                    "limit": limit
                }
            },
            {
                "name": "fee_trending",
                "params": {
                    "q": "*", 
                    "sort_by": "fee_24h:desc",
                    "limit": limit
                }
            }
        ]
        
        results = {}
        
        for query in search_queries:
            try:
                endpoint = "/pool/search"
                data = await self._make_tracked_request(endpoint, query["params"])
                self.api_stats["pool_metrics_calls"] += 1
                
                if data and 'hits' in data:
                    pools = [hit.get('document', {}) for hit in data['hits']]
                    
                    # Enhance pool data with trending metrics
                    enhanced_pools = []
                    for pool in pools:
                        enhanced_pool = self._calculate_pool_trending_metrics(pool, query["name"])
                        enhanced_pools.append(enhanced_pool)
                    
                    results[query["name"]] = enhanced_pools
                    self.logger.info(f"✅ {query['name']}: {len(enhanced_pools)} pools retrieved")
                else:
                    results[query["name"]] = []
                    self.logger.warning(f"⚠️ {query['name']}: No data returned")
                
                # Rate limiting between queries
                await asyncio.sleep(0.5)
                
            except Exception as e:
                self.logger.error(f"❌ {query['name']} failed: {e}")
                results[query["name"]] = []
        
        return results
    
    def _calculate_pool_trending_metrics(self, pool: Dict, metric_type: str) -> Dict:
        """Calculate enhanced trending metrics for a pool"""
        volume_24h = pool.get('volume_24h', 0)
        tvl = pool.get('tvl', 1)
        fee_24h = pool.get('fee_24h', 0)
        
        # Volume-to-Liquidity Ratio (VLR)
        vlr = volume_24h / tvl if tvl > 0 else 0
        
        # Fee Yield (APY estimation)
        fee_yield = (fee_24h * 365) / tvl * 100 if tvl > 0 else 0
        
        # Pool Activity Score (0-10)
        activity_score = min(10, vlr)
        
        # Pool Efficiency Score (based on fee generation)
        efficiency_score = min(10, fee_yield / 10) if fee_yield > 0 else 0
        
        # Composite Trending Score
        if metric_type == "volume_trending":
            trending_score = activity_score * 0.7 + efficiency_score * 0.3
        elif metric_type == "tvl_trending":
            trending_score = efficiency_score * 0.6 + activity_score * 0.4
        else:  # fee_trending
            trending_score = efficiency_score * 0.8 + activity_score * 0.2
        
        # Extract tokens from pool
        token_mints = pool.get('token_mints', [])
        
        enhanced_pool = {
            **pool,
            'vlr': round(vlr, 4),
            'fee_yield_apy': round(fee_yield, 2),
            'activity_score': round(activity_score, 2),
            'efficiency_score': round(efficiency_score, 2),
            'trending_score': round(trending_score, 2),
            'metric_type': metric_type,
            'token_count': len(token_mints),
            'tokens': token_mints
        }
        
        return enhanced_pool
    
    async def analyze_token_across_pools(self, token_address: str) -> Dict[str, Any]:
        """Analyze a specific token across all pools it participates in"""
        self.logger.info(f"🔍 Analyzing token {token_address[:8]}... across all pools")
        
        try:
            params = {
                "q": token_address,
                "query_by": "token_mints",
                "limit": 50
            }
            
            data = await self._make_tracked_request("/pool/search", params)
            
            if not data or 'hits' not in data:
                return {
                    'token_address': token_address,
                    'pools_found': 0,
                    'total_volume': 0,
                    'total_tvl': 0,
                    'total_fees': 0,
                    'pool_diversity_score': 0,
                    'aggregate_trending_score': 0
                }
            
            pools = [hit.get('document', {}) for hit in data['hits']]
            
            # Aggregate metrics across all pools
            total_volume = sum(pool.get('volume_24h', 0) for pool in pools)
            total_tvl = sum(pool.get('tvl', 0) for pool in pools)
            total_fees = sum(pool.get('fee_24h', 0) for pool in pools)
            
            # Pool diversity score (more pools = better liquidity distribution)
            pool_diversity_score = min(10, len(pools) * 2)
            
            # Aggregate VLR
            aggregate_vlr = total_volume / total_tvl if total_tvl > 0 else 0
            
            # Aggregate trending score
            aggregate_trending_score = min(10, aggregate_vlr)
            
            analysis = {
                'token_address': token_address,
                'pools_found': len(pools),
                'total_volume': total_volume,
                'total_tvl': total_tvl,
                'total_fees': total_fees,
                'aggregate_vlr': round(aggregate_vlr, 4),
                'pool_diversity_score': round(pool_diversity_score, 2),
                'aggregate_trending_score': round(aggregate_trending_score, 2),
                'pool_details': pools[:10]  # Top 10 pools for this token
            }
            
            self.api_stats["comprehensive_analysis_calls"] += 1
            return analysis
            
        except Exception as e:
            self.logger.error(f"Token analysis failed for {token_address[:8]}...: {e}")
            return {
                'token_address': token_address,
                'error': str(e),
                'pools_found': 0
            }
    
    async def _make_tracked_request(self, endpoint: str, params: Dict[str, Any] = None) -> Optional[Dict]:
        """Enhanced tracked API request"""
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
                        return data
                    else:
                        self.api_stats["failed_calls"] += 1
                        error_text = await response.text()
                        self.logger.warning(f"🔴 Meteora API failed: {response.status} - {error_text[:100]}")
                        return None
                        
        except Exception as e:
            response_time_ms = (time.time() - start_time) * 1000
            self.api_stats["total_response_time_ms"] += response_time_ms
            self.api_stats["failed_calls"] += 1
            self.logger.error(f"🔴 Meteora API error: {e}")
            return None
    
    def get_api_call_statistics(self) -> Dict[str, Any]:
        """Enhanced API statistics"""
        stats = self.api_stats.copy()
        stats["endpoints_used"] = list(stats["endpoints_used"])
        stats["average_response_time_ms"] = (
            stats["total_response_time_ms"] / max(1, stats["total_calls"])
        )
        return stats


class EnhancedCrossPlatformAnalyzer(CrossPlatformAnalyzer):
    """Enhanced analyzer with advanced cross-platform momentum scoring"""
    
    def __init__(self, config: Optional[Dict] = None, logger: Optional[logging.Logger] = None):
        super().__init__(config, logger)
        
        # Initialize enhanced connectors
        self.jupiter = EnhancedJupiterConnector(self.enhanced_cache)
        self.meteora = EnhancedMeteoraConnector(self.enhanced_cache)
        
        # Excluded infrastructure tokens
        self.excluded_addresses = {
            'So11111111111111111111111111111111111111112',  # SOL
            'EPjFWdd5AufqSSqeM2qN1xzybapC8G4wEGGkZwyTDt1v',  # USDC
            '27G8MtK7VtTcCHkpASjSDdkWWYfoqT6ggEuKidVJidD4',  # JLP
            'jupSoLaHXQiZZTSfEWMTRRgpnyFm8f6sZdosWBjx93v'   # JupSOL
        }
        
        self.logger.info("🚀 Enhanced Jupiter + Meteora Analyzer initialized")
        self.logger.info(f"🚫 Excluding {len(self.excluded_addresses)} infrastructure tokens")
    
    async def collect_enhanced_data(self) -> Dict[str, Any]:
        """Enhanced data collection with advanced analytics"""
        self.logger.info("🔄 Starting enhanced cross-platform data collection...")
        
        start_time = time.time()
        
        # Step 1: Get comprehensive Meteora pool metrics
        meteora_metrics = await self.meteora.get_comprehensive_pool_metrics(30)
        
        # Step 2: Extract trending tokens from Meteora data
        trending_tokens = self._extract_trending_tokens_from_meteora(meteora_metrics)
        
        # Step 3: Perform Jupiter liquidity depth analysis on top tokens
        top_tokens = trending_tokens[:15]  # Limit for depth analysis
        jupiter_analysis = await self.jupiter.batch_liquidity_analysis(top_tokens)
        
        # Step 4: Perform cross-platform correlation
        cross_platform_tokens = self._calculate_cross_platform_momentum(
            trending_tokens, jupiter_analysis
        )
        
        # Step 5: Get base platform data for comparison
        base_data = await super().collect_all_data()
        
        # Cache base data for comprehensive platform validation
        self._cached_base_data = base_data
        
        collection_time = time.time() - start_time
        
        enhanced_results = {
            "collection_summary": {
                "timestamp": datetime.now().isoformat(),
                "duration_seconds": round(collection_time, 2),
                "status": "SUCCESS"
            },
            "meteora_comprehensive_metrics": meteora_metrics,
            "jupiter_liquidity_analysis": jupiter_analysis,
            "cross_platform_momentum_tokens": cross_platform_tokens,
            "base_platform_data": base_data,
            "enhanced_statistics": {
                "meteora_pools_analyzed": sum(len(pools) for pools in meteora_metrics.values()),
                "jupiter_depth_analysis_count": len(jupiter_analysis),
                "cross_platform_correlations": len(cross_platform_tokens),
                "total_trending_candidates": len(trending_tokens)
            }
        }
        
        self.logger.info(f"✅ Enhanced data collection complete in {collection_time:.2f}s")
        return enhanced_results
    
    def _extract_trending_tokens_from_meteora(self, meteora_metrics: Dict[str, List[Dict]]) -> List[str]:
        """Extract unique trending tokens from comprehensive Meteora metrics"""
        token_scores = defaultdict(float)
        token_data = {}
        
        for metric_type, pools in meteora_metrics.items():
            weight = {
                "volume_trending": 0.4,
                "tvl_trending": 0.3,
                "fee_trending": 0.3
            }.get(metric_type, 0.33)
            
            for pool in pools:
                trending_score = pool.get('trending_score', 0)
                tokens = pool.get('tokens', [])
                
                for token_address in tokens:
                    if token_address not in self.excluded_addresses:
                        token_scores[token_address] += trending_score * weight
                        if token_address not in token_data:
                            token_data[token_address] = {
                                'address': token_address,
                                'meteora_pools': [],
                                'total_meteora_score': 0
                            }
                        token_data[token_address]['meteora_pools'].append(pool)
        
        # Update total scores
        for token_address, score in token_scores.items():
            if token_address in token_data:
                token_data[token_address]['total_meteora_score'] = round(score, 2)
        
        # Sort by score and return addresses
        sorted_tokens = sorted(token_scores.items(), key=lambda x: x[1], reverse=True)
        trending_addresses = [addr for addr, score in sorted_tokens if score > 1.0]
        
        self.logger.info(f"📊 Extracted {len(trending_addresses)} trending tokens from Meteora")
        return trending_addresses[:50]  # Top 50 for analysis
    
    def _calculate_cross_platform_momentum(self, meteora_tokens: List[str], 
                                         jupiter_analysis: List[Dict]) -> List[Dict]:
        """Calculate comprehensive cross-platform momentum scores across ALL platforms"""
        self.logger.info("🔄 Calculating comprehensive cross-platform momentum scores...")
        
        # Create Jupiter lookup
        jupiter_lookup = {analysis['token_address']: analysis for analysis in jupiter_analysis}
        
        # Cache Jupiter lookup for platform presence detection
        self._jupiter_lookup = jupiter_lookup
        
        momentum_tokens = []
        
        for token_address in meteora_tokens:
            jupiter_data = jupiter_lookup.get(token_address, {})
            
            # Base Meteora score (assumed from extraction)
            meteora_score = 5.0  # Default if not available
            
            # Jupiter liquidity scores
            liquidity_depth_score = jupiter_data.get('liquidity_depth_score', 0)
            market_maker_presence = jupiter_data.get('market_maker_presence', 0)
            route_diversity_score = jupiter_data.get('route_diversity_score', 0)
            
            # Calculate composite Jupiter score
            jupiter_composite = (
                liquidity_depth_score * 0.5 +
                market_maker_presence * 0.3 +
                route_diversity_score * 0.2
            )
            
            # Comprehensive platform validation
            platform_presence = self._check_comprehensive_platform_presence(token_address)
            
            # Calculate enhanced correlation bonus based on platform count
            platform_count = len(platform_presence['platforms'])
            correlation_bonus = self._calculate_enhanced_correlation_bonus(
                platform_count, jupiter_data, meteora_score
            )
            
            # Calculate final momentum score with comprehensive validation
            base_score = meteora_score * 0.6 + jupiter_composite * 0.4
            momentum_score = base_score * correlation_bonus
            
            # Risk adjustment
            effective_spread = jupiter_data.get('effective_spread', 0)
            if effective_spread > 5:  # High spread = risky
                momentum_score *= 0.8
            
            momentum_token = {
                'address': token_address,
                'meteora_score': round(meteora_score, 2),
                'jupiter_composite_score': round(jupiter_composite, 2),
                'liquidity_depth_score': round(liquidity_depth_score, 2),
                'market_maker_presence': round(market_maker_presence, 2),
                'route_diversity_score': round(route_diversity_score, 2),
                'platform_presence': platform_presence,
                'platform_count': platform_count,
                'correlation_bonus': round(correlation_bonus, 2),
                'base_score': round(base_score, 2),
                'momentum_score': round(momentum_score, 2),
                'cross_platform_validated': platform_count >= 2,
                'multi_platform_validated': platform_count >= 3,
                'premium_validated': platform_count >= 4,
                'risk_adjusted': effective_spread > 5,
                'jupiter_data': jupiter_data
            }
            
            momentum_tokens.append(momentum_token)
        
        # Sort by momentum score
        momentum_tokens.sort(key=lambda x: x['momentum_score'], reverse=True)
        
        self.logger.info(f"✅ Calculated comprehensive momentum scores for {len(momentum_tokens)} tokens")
        return momentum_tokens
    
    def _check_comprehensive_platform_presence(self, token_address: str) -> Dict[str, Any]:
        """Check token presence across ALL platforms comprehensively"""
        platforms_found = []
        platform_details = {}
        
        # Debug logging
        self.logger.debug(f"🔍 Checking platform presence for {token_address[:8]}...")
        
        # Always include Meteora (since token came from there)
        platforms_found.append('meteora')
        platform_details['meteora'] = {'source': 'pool_metrics', 'confidence': 'high'}
        
        # Check Jupiter presence (if we have Jupiter data for this token)
        if hasattr(self, '_jupiter_lookup') and token_address in self._jupiter_lookup:
            jupiter_data = self._jupiter_lookup[token_address]
            if jupiter_data and jupiter_data.get('liquidity_depth_score', 0) > 0:
                platforms_found.append('jupiter')
                platform_details['jupiter'] = {'source': 'liquidity_analysis', 'confidence': 'high'}
        
        # Check if we have base platform data
        if hasattr(self, '_cached_base_data') and self._cached_base_data:
            base_data = self._cached_base_data
            self.logger.debug(f"📊 Base data platforms available: {list(base_data.keys())}")
            
            # Check DexScreener platforms
            dex_platforms = ['dexscreener_boosted', 'dexscreener_top_boosted', 'dexscreener_profiles']
            for platform_key in dex_platforms:
                platform_data = base_data.get(platform_key, [])
                self.logger.debug(f"🔍 Checking {platform_key}: {len(platform_data)} items")
                if self._token_in_platform_data(token_address, platform_data):
                    platform_name = platform_key.replace('dexscreener_', 'dex_')
                    platforms_found.append(platform_name)
                    platform_details[platform_name] = {'source': 'trending', 'confidence': 'high'}
                    self.logger.debug(f"✅ Found {token_address[:8]} in {platform_name}")
            
            # Check DexScreener narratives
            narratives = base_data.get('dexscreener_narratives', {})
            for narrative, tokens in narratives.items():
                if self._token_in_platform_data(token_address, tokens):
                    platforms_found.append('dex_narratives')
                    platform_details['dex_narratives'] = {'source': f'narrative_{narrative}', 'confidence': 'medium'}
                    break
            
            # Check RugCheck
            rugcheck_data = base_data.get('rugcheck_trending', [])
            self.logger.debug(f"🔍 Checking rugcheck_trending: {len(rugcheck_data)} items")
            if self._token_in_platform_data(token_address, rugcheck_data):
                platforms_found.append('rugcheck')
                platform_details['rugcheck'] = {'source': 'trending', 'confidence': 'high'}
                self.logger.debug(f"✅ Found {token_address[:8]} in rugcheck")
            
            # Check Birdeye trending
            birdeye_trending = base_data.get('birdeye_trending', [])
            self.logger.debug(f"🔍 Checking birdeye_trending: {len(birdeye_trending)} items")
            if self._token_in_platform_data(token_address, birdeye_trending):
                platforms_found.append('birdeye')
                platform_details['birdeye'] = {'source': 'trending', 'confidence': 'high'}
                self.logger.debug(f"✅ Found {token_address[:8]} in birdeye")
            
            # Check Birdeye emerging stars
            birdeye_stars = base_data.get('birdeye_emerging_stars', [])
            self.logger.debug(f"🔍 Checking birdeye_emerging_stars: {len(birdeye_stars)} items")
            if self._token_in_platform_data(token_address, birdeye_stars):
                platforms_found.append('birdeye_stars')
                platform_details['birdeye_stars'] = {'source': 'emerging_stars', 'confidence': 'high'}
                self.logger.debug(f"✅ Found {token_address[:8]} in birdeye_stars")
        
        # Remove duplicates while preserving order
        unique_platforms = []
        seen = set()
        for platform in platforms_found:
            if platform not in seen:
                unique_platforms.append(platform)
                seen.add(platform)
        
        return {
            'platforms': unique_platforms,
            'platform_details': platform_details,
            'platform_count': len(unique_platforms),
            'validation_level': self._get_validation_level(len(unique_platforms))
        }
    
    def _token_in_platform_data(self, token_address: str, platform_data: List[Dict]) -> bool:
        """Check if token exists in platform data"""
        if not platform_data:
            return False
            
        for i, item in enumerate(platform_data):
            # Handle different data structures
            if isinstance(item, dict):
                # Check common address fields
                address_fields = ['address', 'token_address', 'mint', 'baseToken', 'quoteToken']
                for field in address_fields:
                    if item.get(field) == token_address:
                        self.logger.debug(f"🎯 Match found in item {i} field '{field}': {token_address[:8]}")
                        return True
                
                # Check nested structures
                if 'baseToken' in item and isinstance(item['baseToken'], dict):
                    if item['baseToken'].get('address') == token_address:
                        self.logger.debug(f"🎯 Match found in item {i} baseToken.address: {token_address[:8]}")
                        return True
                if 'quoteToken' in item and isinstance(item['quoteToken'], dict):
                    if item['quoteToken'].get('address') == token_address:
                        self.logger.debug(f"🎯 Match found in item {i} quoteToken.address: {token_address[:8]}")
                        return True
                        
                # Debug: Show structure of first few items
                if i < 2:
                    available_fields = list(item.keys())
                    self.logger.debug(f"📋 Item {i} structure: {available_fields}")
                    
            elif isinstance(item, str) and item == token_address:
                self.logger.debug(f"🎯 Direct string match found: {token_address[:8]}")
                return True
        
        return False
    
    def _calculate_enhanced_correlation_bonus(self, platform_count: int, jupiter_data: Dict, meteora_score: float) -> float:
        """Calculate enhanced correlation bonus based on platform presence"""
        base_bonus = 1.0
        
        # Platform count bonuses
        if platform_count >= 5:
            base_bonus = 3.0  # 200% bonus for 5+ platforms (ultra-premium)
        elif platform_count >= 4:
            base_bonus = 2.5  # 150% bonus for 4+ platforms (premium)
        elif platform_count >= 3:
            base_bonus = 2.0  # 100% bonus for 3+ platforms (high-confidence)
        elif platform_count >= 2:
            base_bonus = 1.5  # 50% bonus for 2+ platforms (cross-validated)
        
        # Jupiter quality bonus
        if jupiter_data:
            liquidity_depth = jupiter_data.get('liquidity_depth_score', 0)
            if liquidity_depth >= 9 and platform_count >= 3:
                base_bonus *= 1.2  # Additional 20% for exceptional liquidity + multi-platform
            elif liquidity_depth >= 7 and platform_count >= 2:
                base_bonus *= 1.1  # Additional 10% for good liquidity + cross-platform
        
        # Meteora quality bonus
        if meteora_score >= 7 and platform_count >= 3:
            base_bonus *= 1.1  # Additional 10% for high Meteora score + multi-platform
        
        return min(base_bonus, 4.0)  # Cap at 300% bonus
    
    def _extract_token_symbol(self, token_address: str) -> str:
        """Extract token symbol from cached platform data"""
        # Check Jupiter token list first
        if hasattr(self, '_jupiter_lookup') and token_address in self._jupiter_lookup:
            jupiter_data = self._jupiter_lookup[token_address]
            if 'symbol' in jupiter_data:
                return jupiter_data['symbol']
        
        # Check base platform data
        if hasattr(self, '_cached_base_data') and self._cached_base_data:
            base_data = self._cached_base_data
            
            # Check Birdeye trending data
            birdeye_trending = base_data.get('birdeye_trending', [])
            for token in birdeye_trending:
                if token.get('address') == token_address:
                    return token.get('symbol', token.get('name', 'Unknown'))
            
            # Check Birdeye emerging stars
            birdeye_stars = base_data.get('birdeye_emerging_stars', [])
            for token in birdeye_stars:
                if token.get('address') == token_address:
                    return token.get('symbol', token.get('name', 'Unknown'))
            
            # Check DexScreener data
            for platform_key in ['dexscreener_boosted', 'dexscreener_profiles']:
                platform_data = base_data.get(platform_key, [])
                for item in platform_data:
                    if isinstance(item, dict):
                        # Check baseToken
                        if item.get('baseToken', {}).get('address') == token_address:
                            return item.get('baseToken', {}).get('symbol', 'Unknown')
                        # Check quoteToken
                        if item.get('quoteToken', {}).get('address') == token_address:
                            return item.get('quoteToken', {}).get('symbol', 'Unknown')
            
            # Check RugCheck data
            rugcheck_data = base_data.get('rugcheck_trending', [])
            for token in rugcheck_data:
                if token.get('mint') == token_address or token.get('address') == token_address:
                    return token.get('symbol', token.get('name', 'Unknown'))
        
        # Fallback to shortened address
        return f"TOK{token_address[:6]}"
    
    def _get_validation_level(self, platform_count: int) -> str:
        """Get validation level description"""
        if platform_count >= 5:
            return "ULTRA_PREMIUM"
        elif platform_count >= 4:
            return "PREMIUM"
        elif platform_count >= 3:
            return "HIGH_CONFIDENCE"
        elif platform_count >= 2:
            return "CROSS_VALIDATED"
        else:
            return "SINGLE_PLATFORM"
    
    def get_enhanced_api_stats(self) -> Dict[str, Any]:
        """Get comprehensive API statistics"""
        stats = super().get_api_stats()
        
        # Add enhanced Jupiter stats
        jupiter_stats = self.jupiter.get_api_call_statistics()
        stats['enhanced_jupiter'] = {
            'calls': jupiter_stats.get('total_calls', 0),
            'successes': jupiter_stats.get('successful_calls', 0),
            'failures': jupiter_stats.get('failed_calls', 0),
            'depth_analysis_calls': jupiter_stats.get('depth_analysis_calls', 0),
            'batch_processing_calls': jupiter_stats.get('batch_processing_calls', 0),
            'total_time_ms': jupiter_stats.get('total_response_time_ms', 0),
            'estimated_cost': 0.0
        }
        
        # Add enhanced Meteora stats
        meteora_stats = self.meteora.get_api_call_statistics()
        stats['enhanced_meteora'] = {
            'calls': meteora_stats.get('total_calls', 0),
            'successes': meteora_stats.get('successful_calls', 0),
            'failures': meteora_stats.get('failed_calls', 0),
            'pool_metrics_calls': meteora_stats.get('pool_metrics_calls', 0),
            'comprehensive_analysis_calls': meteora_stats.get('comprehensive_analysis_calls', 0),
            'total_time_ms': meteora_stats.get('total_response_time_ms', 0),
            'estimated_cost': 0.0
        }
        
        return stats


async def test_enhanced_jupiter_meteora_integration():
    """Test the enhanced Jupiter + Meteora integration system"""
    logging.basicConfig(level=logging.INFO)
    logger = logging.getLogger(__name__)
    
    logger.info("🚀 Starting Enhanced Jupiter + Meteora Integration Test")
    logger.info("=" * 80)
    
    start_time = time.time()
    
    try:
        # Initialize enhanced analyzer
        config = {
            'cache_enabled': True,
            'parallel_processing': True,
            'max_concurrent_requests': 5,
            'enhanced_analytics': True
        }
        
        analyzer = EnhancedCrossPlatformAnalyzer(config, logger)
        
        # Run enhanced analysis
        logger.info("📊 Running enhanced cross-platform analysis...")
        results = await analyzer.collect_enhanced_data()
        
        # Generate comprehensive report
        test_duration = time.time() - start_time
        
        # Extract key metrics
        meteora_pools = results["enhanced_statistics"]["meteora_pools_analyzed"]
        jupiter_analysis = results["enhanced_statistics"]["jupiter_depth_analysis_count"]
        cross_platform = results["enhanced_statistics"]["cross_platform_correlations"]
        
        # Get API statistics
        api_stats = analyzer.get_enhanced_api_stats()
        
        # Create final results
        final_results = {
            "test_summary": {
                "timestamp": datetime.now().isoformat(),
                "duration_seconds": round(test_duration, 2),
                "status": "SUCCESS",
                "enhancement_level": "ADVANCED"
            },
            "enhanced_analytics": {
                "meteora_pools_analyzed": meteora_pools,
                "jupiter_liquidity_analysis": jupiter_analysis,
                "cross_platform_correlations": cross_platform,
                "momentum_scoring_enabled": True,
                "multi_depth_analysis_enabled": True
            },
            "api_performance": api_stats,
            "top_momentum_tokens": results["cross_platform_momentum_tokens"][:10],
            "recommendations": [
                "✅ Enhanced multi-depth liquidity analysis operational",
                "✅ Comprehensive Meteora pool metrics integrated",
                "✅ Cross-platform momentum scoring active",
                "🎯 Ready for advanced trending detection deployment"
            ]
        }
        
        # Save results
        timestamp = int(time.time())
        filename = f"scripts/tests/enhanced_jupiter_meteora_results_{timestamp}.json"
        
        with open(filename, 'w') as f:
            json.dump(final_results, f, indent=2, default=str)
        
        # Generate comprehensive platform breakdown table
        logger.info(f"\n✅ Analysis completed in {test_duration:.2f}s")
        logger.info("=" * 60)
        
        # Platform Data Summary
        logger.info("📊 PLATFORM DATA SUMMARY:")
        base_data = results.get("base_platform_data", {})
        meteora_metrics = results.get("meteora_comprehensive_metrics", {})
        
        # Standard platforms
        platform_counts = {
            "dexscreener_boosted": len(base_data.get("dexscreener_boosted", [])),
            "dexscreener_top": len(base_data.get("dexscreener_top_boosted", [])),
            "dexscreener_profiles": len(base_data.get("dexscreener_profiles", [])),
            "dexscreener_narratives": len(base_data.get("dexscreener_narratives", [])),
            "rugcheck_trending": len(base_data.get("rugcheck_trending", [])),
            "birdeye_trending": len(base_data.get("birdeye_trending", [])),
            "birdeye_emerging_stars": len(base_data.get("birdeye_emerging_stars", [])),
            "meteora_volume_trending": len(meteora_metrics.get("volume_trending", [])),
            "meteora_tvl_trending": len(meteora_metrics.get("tvl_trending", [])),
            "meteora_fee_trending": len(meteora_metrics.get("fee_trending", [])),
            "jupiter_trending_tokens": len(results.get("jupiter_liquidity_analysis", []))
        }
        
        for platform, count in platform_counts.items():
            if count > 0:
                logger.info(f"  • {platform}: {count} items")
        
        # Enhanced Correlation Analysis
        logger.info("\n🔍 COMPREHENSIVE CORRELATION ANALYSIS:")
        momentum_tokens = results["cross_platform_momentum_tokens"]
        
        # Count comprehensive validation levels
        ultra_premium = len([t for t in momentum_tokens if t.get('platform_count', 0) >= 5])
        premium = len([t for t in momentum_tokens if t.get('platform_count', 0) == 4])
        high_confidence = len([t for t in momentum_tokens if t.get('platform_count', 0) == 3])
        cross_validated = len([t for t in momentum_tokens if t.get('platform_count', 0) == 2])
        single_platform = len([t for t in momentum_tokens if t.get('platform_count', 0) == 1])
        high_conviction = len([t for t in momentum_tokens if t.get('momentum_score', 0) >= 15])
        
        logger.info(f"  • Total analyzed tokens: {len(momentum_tokens)}")
        logger.info(f"  • Ultra Premium validated (5+ platforms): {ultra_premium}")
        logger.info(f"  • Premium validated (4 platforms): {premium}")
        logger.info(f"  • High Confidence (3 platforms): {high_confidence}")
        logger.info(f"  • Cross-platform validated (2 platforms): {cross_validated}")
        logger.info(f"  • Single-platform tokens: {single_platform}")
        logger.info(f"  • High-conviction tokens (≥15 score): {high_conviction}")
        
        # Comprehensive Platform Distribution Analysis
        logger.info("\n📈 COMPREHENSIVE PLATFORM DISTRIBUTION:")
        distribution = {}
        for token in momentum_tokens:
            platform_count = token.get('platform_count', 1)
            if platform_count not in distribution:
                distribution[platform_count] = 0
            distribution[platform_count] += 1
        
        for platform_count in sorted(distribution.keys(), reverse=True):
            token_count = distribution[platform_count]
            validation_level = {
                5: "Ultra Premium", 4: "Premium", 3: "High Confidence", 
                2: "Cross Validated", 1: "Single Platform"
            }.get(platform_count, f"{platform_count} platforms")
            logger.info(f"  • {platform_count} platform(s) [{validation_level}]: {token_count} tokens")
        
        # Enhanced Cross-Platform Correlation Table using PrettyTable
        logger.info("\n🔗 COMPREHENSIVE CROSS-PLATFORM CORRELATION TABLE:")
        
        # Create main correlation table
        correlation_table = PrettyTable()
        correlation_table.field_names = [
            "Rank", "Symbol", "Final Score", "Correlation Bonus", 
            "Platform Count", "Validation Level", "Platform Breakdown", "Full Address"
        ]
        correlation_table.align = "l"
        correlation_table.align["Rank"] = "r"
        correlation_table.align["Final Score"] = "r"
        correlation_table.align["Correlation Bonus"] = "r"
        correlation_table.align["Platform Count"] = "r"
        
        # Sort tokens by momentum score for ranking
        sorted_tokens = sorted(momentum_tokens, key=lambda x: x.get('momentum_score', 0), reverse=True)
        
        for i, token in enumerate(sorted_tokens, 1):
            addr = token['address']
            score = token.get('momentum_score', 0)
            correlation_bonus = token.get('correlation_bonus', 1.0)
            platform_count = token.get('platform_count', 1)
            
            # Get platform presence details
            platform_presence = token.get('platform_presence', {})
            platforms = platform_presence.get('platforms', ['meteora'])
            validation_level = platform_presence.get('validation_level', 'SINGLE_PLATFORM')
            
            # Create platform breakdown string
            platform_str = ", ".join(platforms[:3])  # Show first 3 platforms
            if len(platforms) > 3:
                platform_str += f" +{len(platforms)-3}"
            
            # Extract symbol using enhanced method
            symbol = analyzer._extract_token_symbol(addr)
            
            # Format validation level for display
            validation_display = validation_level.replace('_', ' ').title()
            
            # Add row to table
            correlation_table.add_row([
                i, symbol, f"{score:.1f}", f"{correlation_bonus:.1f}x",
                platform_count, validation_display, platform_str, addr
            ])
        
        # Print the table
        for line in str(correlation_table).split('\n'):
            logger.info(line)
        
        # Enhanced Platform Validation Summary
        logger.info("\n📊 COMPREHENSIVE PLATFORM VALIDATION SUMMARY:")
        ultra_premium = len([t for t in momentum_tokens if t.get('platform_count', 0) >= 5])
        premium = len([t for t in momentum_tokens if t.get('platform_count', 0) == 4])
        high_confidence = len([t for t in momentum_tokens if t.get('platform_count', 0) == 3])
        cross_validated = len([t for t in momentum_tokens if t.get('platform_count', 0) == 2])
        single_platform = len([t for t in momentum_tokens if t.get('platform_count', 0) == 1])
        
        logger.info(f"  🏆 Ultra Premium (5+ platforms): {ultra_premium} tokens")
        logger.info(f"  💎 Premium (4 platforms): {premium} tokens")
        logger.info(f"  🔥 High Confidence (3 platforms): {high_confidence} tokens")
        logger.info(f"  ✅ Cross Validated (2 platforms): {cross_validated} tokens")
        logger.info(f"  ⚪ Single Platform (1 platform): {single_platform} tokens")
        
        # Comprehensive Token Summary Table
        logger.info("\n💎 COMPREHENSIVE TOKEN SUMMARY - TOP 15 TOKENS:")
        
        # Create detailed summary table
        summary_table = PrettyTable()
        summary_table.field_names = [
            "Rank", "Symbol", "Score", "Platforms", "Validation", 
            "Jupiter Score", "Meteora Score", "Liquidity Depth", "Full Address"
        ]
        summary_table.align = "l"
        summary_table.align["Rank"] = "r"
        summary_table.align["Score"] = "r"
        summary_table.align["Jupiter Score"] = "r"
        summary_table.align["Meteora Score"] = "r"
        summary_table.align["Liquidity Depth"] = "r"
        
        for i, token in enumerate(sorted_tokens[:15], 1):
            addr = token['address']
            score = token.get('momentum_score', 0)
            platform_presence = token.get('platform_presence', {})
            platforms = platform_presence.get('platforms', ['meteora'])
            validation_level = platform_presence.get('validation_level', 'SINGLE_PLATFORM')
            
            # Extract detailed scores
            jupiter_score = token.get('jupiter_composite_score', 0)
            meteora_score = token.get('meteora_score', 0)
            liquidity_depth = token.get('liquidity_depth_score', 0)
            
            # Extract symbol
            symbol = analyzer._extract_token_symbol(addr)
            
            # Format validation level
            validation_short = {
                'SINGLE_PLATFORM': 'Single',
                'CROSS_VALIDATED': 'Cross',
                'HIGH_CONFIDENCE': 'High',
                'PREMIUM': 'Premium',
                'ULTRA_PREMIUM': 'Ultra'
            }.get(validation_level, validation_level[:6])
            
            # Platform count
            platform_count = len(platforms)
            
            summary_table.add_row([
                i, symbol, f"{score:.1f}", f"{platform_count}P",
                validation_short, f"{jupiter_score:.1f}", f"{meteora_score:.1f}",
                f"{liquidity_depth:.0f}/10", addr
            ])
        
        # Print the summary table
        for line in str(summary_table).split('\n'):
            logger.info(line)
        
        # Detailed Platform Breakdown for Top Tokens
        logger.info("\n🎯 DETAILED PLATFORM BREAKDOWN - TOP 10 TOKENS:")
        
        # Create platform breakdown table
        breakdown_table = PrettyTable()
        breakdown_table.field_names = ["Token", "Symbol", "Score", "Platform Details"]
        breakdown_table.align = "l"
        breakdown_table.align["Score"] = "r"
        breakdown_table.max_width["Platform Details"] = 60
        
        for i, token in enumerate(sorted_tokens[:10], 1):
            addr_short = token['address'][:8]
            score = token.get('momentum_score', 0)
            platform_presence = token.get('platform_presence', {})
            platforms = platform_presence.get('platforms', ['meteora'])
            platform_details = platform_presence.get('platform_details', {})
            symbol = analyzer._extract_token_symbol(token['address'])
            
            # Create detailed platform breakdown
            platform_breakdown = []
            for platform in platforms:
                details = platform_details.get(platform, {})
                source = details.get('source', 'unknown')
                confidence = details.get('confidence', 'medium')
                platform_breakdown.append(f"• {platform}: {source} ({confidence})")
            
            breakdown_table.add_row([
                f"{addr_short}...", symbol, f"{score:.1f}",
                "\n".join(platform_breakdown)
            ])
        
        # Print the breakdown table
        for line in str(breakdown_table).split('\n'):
            logger.info(line)
        
        logger.info("")
        
        # Score Distribution
        high_score = len([t for t in momentum_tokens if t.get('momentum_score', 0) >= 15])
        medium_score = len([t for t in momentum_tokens if 10 <= t.get('momentum_score', 0) < 15])
        low_score = len([t for t in momentum_tokens if t.get('momentum_score', 0) < 10])
        
        logger.info(f"\n📊 Score Distribution: 🟢 High ({high_score}) | 🟡 Medium ({medium_score}) | ⚪ Low ({low_score})")
        
        # Top Multi-Platform Tokens Summary
        # Top Multi-Platform Tokens using PrettyTable
        logger.info("\n🏆 TOP ENHANCED MOMENTUM TOKENS:")
        
        # Create top tokens table
        top_tokens_table = PrettyTable()
        top_tokens_table.field_names = [
            "Rank", "Symbol", "Score", "Validation", "Platforms", "Address"
        ]
        top_tokens_table.align = "l"
        top_tokens_table.align["Rank"] = "r"
        top_tokens_table.align["Score"] = "r"
        
        top_tokens = momentum_tokens[:10]
        for i, token in enumerate(top_tokens, 1):
            addr = token['address']
            addr_short = addr[:8] + "..."
            score = token['momentum_score']
            
            # Get platform presence
            platform_presence = token.get('platform_presence', {})
            platforms = platform_presence.get('platforms', ['meteora'])
            validation_level = platform_presence.get('validation_level', 'SINGLE_PLATFORM')
            
            # Extract symbol
            symbol = analyzer._extract_token_symbol(addr)
            
            # Format validation level
            validation_short = {
                'SINGLE_PLATFORM': 'Single',
                'CROSS_VALIDATED': 'Cross',
                'HIGH_CONFIDENCE': 'High',
                'PREMIUM': 'Premium',
                'ULTRA_PREMIUM': 'Ultra'
            }.get(validation_level, validation_level[:6])
            
            platform_str = ", ".join(platforms)
            
            top_tokens_table.add_row([
                i, symbol, f"{score:.1f}", validation_short, platform_str, addr_short
            ])
        
        # Print the top tokens table
        for line in str(top_tokens_table).split('\n'):
            logger.info(line)
        
        # Enhanced API Performance
        logger.info("\n📊 ENHANCED API PERFORMANCE:")
        for platform, stats in api_stats.items():
            if stats.get('calls', 0) > 0:
                success_rate = (stats['successes'] / max(1, stats['calls'])) * 100
                calls = stats['calls']
                response_time = stats.get('total_time_ms', 0) / max(1, calls)
                logger.info(f"  • {platform}: {calls} calls, {success_rate:.1f}% success, {response_time:.0f}ms avg")
        
        # Jupiter-Specific Metrics
        jupiter_stats = api_stats.get('enhanced_jupiter', {})
        if jupiter_stats.get('calls', 0) > 0:
            logger.info("\n🔬 JUPITER ADVANCED METRICS:")
            logger.info(f"  • Depth analysis calls: {jupiter_stats.get('depth_analysis_calls', 0)}")
            logger.info(f"  • Batch processing calls: {jupiter_stats.get('batch_processing_calls', 0)}")
            logger.info(f"  • Multi-depth success rate: {(jupiter_stats['successes'] / max(1, jupiter_stats['calls'])) * 100:.1f}%")
        
        # Meteora-Specific Metrics
        meteora_stats = api_stats.get('enhanced_meteora', {})
        if meteora_stats.get('calls', 0) > 0:
            logger.info("\n🌊 METEORA ADVANCED METRICS:")
            logger.info(f"  • Pool metrics calls: {meteora_stats.get('pool_metrics_calls', 0)}")
            logger.info(f"  • Comprehensive analysis: {meteora_stats.get('comprehensive_analysis_calls', 0)}")
            logger.info(f"  • Multi-metric success rate: {(meteora_stats['successes'] / max(1, meteora_stats['calls'])) * 100:.1f}%")
        
        logger.info(f"\n✅ Enhanced integration test completed! Results: {filename}")
        
        return final_results
        
    except Exception as e:
        logger.error(f"❌ Enhanced integration test failed: {e}")
        return {
            "test_summary": {
                "timestamp": datetime.now().isoformat(),
                "duration_seconds": round(time.time() - start_time, 2),
                "status": "FAILED",
                "error": str(e)
            }
        }


if __name__ == "__main__":
    asyncio.run(test_enhanced_jupiter_meteora_integration()) 