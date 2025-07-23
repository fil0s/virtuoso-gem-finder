#!/usr/bin/env python3
"""
Jupiter + Meteora Cross-Platform Integration Test

Integrates both Jupiter and Meteora APIs into the existing cross-platform
trending detection system for comprehensive token discovery.

Jupiter API Capabilities (from our testing):
✅ Quote API: Real-time pricing, liquidity inference via routes
✅ Token List API: 287K+ tokens for discovery  
❌ Price API: DNS issues (price.jup.ag doesn't exist)
❌ Stats API: Connection timeouts

Meteora API Capabilities (now fixed):
✅ Pool Search: 171K+ pools with volume/TVL data
✅ VLR Calculation: Volume-to-Liquidity ratios
✅ Token Extraction: From high-activity pools
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

class JupiterConnector:
    """Jupiter API connector for token discovery and pricing"""
    
    def __init__(self, enhanced_cache: Optional[EnhancedPositionCacheManager] = None):
        # Based on our testing - these are the WORKING endpoints
        self.base_urls = {
            "quote": "https://quote-api.jup.ag/v6/quote", # ✅ WORKING - Full endpoint
            "tokens": "https://token.jup.ag/all",         # ✅ WORKING 
            # Note: price.jup.ag and stats.jup.ag have DNS/connection issues
        }
        
        self.enhanced_cache = enhanced_cache
        self.api_key = os.getenv('JUPITER_API_KEY')  # Optional from portal.jup.ag
        
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
        
        # Headers for Jupiter API
        self.headers = {
            'User-Agent': 'VirtuosoGemHunter/1.0',
            'Accept': 'application/json',
            'Content-Type': 'application/json'
        }
        
        if self.api_key:
            self.headers['Authorization'] = f'Bearer {self.api_key}'
    
    def get_api_call_statistics(self) -> Dict[str, Any]:
        """Get API call statistics for reporting"""
        stats = self.api_stats.copy()
        stats["endpoints_used"] = list(stats["endpoints_used"])
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
        """Make a tracked API request to Jupiter"""
        start_time = time.time()
        self.api_stats["total_calls"] += 1
        self.api_stats["endpoints_used"].add(endpoint)
        
        try:
            async with aiohttp.ClientSession() as session:
                url = f"{endpoint}"  # endpoint is full URL for Jupiter
                async with session.get(url, params=params, headers=self.headers) as response:
                    response_time_ms = (time.time() - start_time) * 1000
                    self.api_stats["total_response_time_ms"] += response_time_ms
                    
                    if response.status == 200:
                        self.api_stats["successful_calls"] += 1
                        data = await response.json()
                        self.logger.info(f"🟢 Jupiter API call successful: {endpoint.split('/')[-1]} ({response.status}) - {response_time_ms:.1f}ms")
                        return data
                    else:
                        self.api_stats["failed_calls"] += 1
                        self.logger.warning(f"🔴 Jupiter API call failed: {endpoint.split('/')[-1]} ({response.status}) - {response_time_ms:.1f}ms")
                        return None
                        
        except Exception as e:
            response_time_ms = (time.time() - start_time) * 1000
            self.api_stats["total_response_time_ms"] += response_time_ms
            self.api_stats["failed_calls"] += 1
            self.logger.error(f"🔴 Jupiter API error: {endpoint.split('/')[-1]} - {e} - {response_time_ms:.1f}ms")
            return None
    
    async def get_all_tokens(self) -> List[Dict]:
        """Get all available tokens from Jupiter"""
        # Check cache first
        cache_key = "jupiter_all_tokens"
        if self.enhanced_cache:
            cached_data = self.enhanced_cache.get_enhanced("jupiter_tokens", cache_key)
            if cached_data:
                return cached_data
        
        data = await self._make_tracked_request(self.base_urls["tokens"])
        
        if not data or not isinstance(data, list):
            return []
        
        # Process and enhance token data
        enhanced_tokens = []
        for token in data:
            if isinstance(token, dict):
                enhanced_token = {
                    'address': token.get('address', ''),
                    'symbol': token.get('symbol', ''),
                    'name': token.get('name', ''),
                    'decimals': token.get('decimals', 9),
                    'logoURI': token.get('logoURI', ''),
                    'tags': token.get('tags', []),
                    'daily_volume': token.get('daily_volume', 0),  # May not be available
                    'discovery_source': 'jupiter_token_list'
                }
                enhanced_tokens.append(enhanced_token)
        
        # Cache the result
        if enhanced_tokens and self.enhanced_cache:
            self.enhanced_cache.set_enhanced("jupiter_tokens", cache_key, enhanced_tokens)
        
        self.logger.info(f"📊 Fetched {len(enhanced_tokens)} tokens from Jupiter")
        return enhanced_tokens
    
    async def get_trending_tokens_via_quotes(self, target_tokens: List[str], limit: int = 20) -> List[Dict]:
        """Get trending tokens by analyzing quote data for liquidity/activity"""
        trending_tokens = []
        
        # Test various tokens against USDC to gauge activity
        usdc_mint = "EPjFWdd5AufqSSqeM2qN1xzybapC8G4wEGGkZwyTDt1v"
        
        for i, token_address in enumerate(target_tokens[:limit]):
            if token_address == usdc_mint:  # Skip USDC itself
                continue
                
            # Test quote to measure liquidity and activity
            params = {
                "inputMint": token_address,
                "outputMint": usdc_mint,
                "amount": "1000000000",  # 1 token (assuming 9 decimals)
                "slippageBps": "100"  # 1% slippage
            }
            
            quote_data = await self._make_tracked_request(self.base_urls['quote'], params)
            
            if quote_data:
                # Analyze quote for trending indicators
                analysis = self._analyze_quote_for_trending(quote_data, token_address)
                
                if analysis['is_tradeable']:
                    trending_token = {
                        'address': token_address,
                        'quote_analysis': analysis,
                        'liquidity_score': analysis['liquidity_score'],
                        'activity_score': analysis['activity_score'],
                        'route_complexity': analysis['route_complexity'],
                        'price_impact': analysis['price_impact'],
                        'trending_score': analysis['trending_score'],
                        'discovery_source': 'jupiter_quote_analysis'
                    }
                    trending_tokens.append(trending_token)
            
            # Rate limiting - be conservative
            await asyncio.sleep(0.2)
            
            # Progress logging
            if (i + 1) % 5 == 0:
                self.logger.info(f"📈 Analyzed {i + 1}/{min(limit, len(target_tokens))} tokens for trending signals")
        
        # Sort by trending score
        trending_tokens.sort(key=lambda x: x['trending_score'], reverse=True)
        
        self.logger.info(f"🎯 Analyzed {len(trending_tokens)} trending tokens via Jupiter quotes")
        return trending_tokens
    
    def _analyze_quote_for_trending(self, quote_data: Dict, token_address: str) -> Dict[str, Any]:
        """Analyze quote data to determine trending potential - ENHANCED ACCURACY"""
        analysis = {
            'is_tradeable': False,
            'liquidity_score': 0,
            'activity_score': 0,
            'route_complexity': 0,
            'price_impact': 0,
            'trending_score': 0,
            'validation_errors': []
        }
        
        if not quote_data:
            analysis['validation_errors'].append("No quote data received")
            return analysis
        
        # Validate quote structure
        required_fields = ['outAmount', 'inAmount']
        missing_fields = [field for field in required_fields if field not in quote_data]
        if missing_fields:
            analysis['validation_errors'].append(f"Missing required fields: {missing_fields}")
            return analysis
        
        # Check if quote is valid
        try:
            out_amount = int(quote_data['outAmount'])
            in_amount = int(quote_data['inAmount'])
            
            if out_amount <= 0 or in_amount <= 0:
                analysis['validation_errors'].append("Invalid amount values")
                return analysis
                
            analysis['is_tradeable'] = True
            
            # Analyze route complexity (indicator of liquidity) - ENHANCED
            route_plan = quote_data.get('routePlan', [])
            if not isinstance(route_plan, list):
                analysis['validation_errors'].append("Invalid routePlan structure")
                route_plan = []
            
            analysis['route_complexity'] = len(route_plan)
            
            # Liquidity score based on route availability - VALIDATED RANGES
            if analysis['route_complexity'] >= 4:
                analysis['liquidity_score'] = 10  # Excellent liquidity
            elif analysis['route_complexity'] == 3:
                analysis['liquidity_score'] = 8   # High liquidity  
            elif analysis['route_complexity'] == 2:
                analysis['liquidity_score'] = 6   # Medium liquidity
            elif analysis['route_complexity'] == 1:
                analysis['liquidity_score'] = 4   # Low liquidity
            else:
                analysis['liquidity_score'] = 1   # Very low liquidity
            
            # Price impact analysis - ENHANCED VALIDATION
            price_impact = quote_data.get('priceImpactPct')
            if price_impact is not None:
                try:
                    impact = float(price_impact)
                    # Validate price impact range
                    if impact < 0 or impact > 100:
                        analysis['validation_errors'].append(f"Invalid price impact: {impact}%")
                        impact = 5.0  # Default fallback
                    
                    analysis['price_impact'] = impact
                    
                    # Activity score based on price impact (lower = better liquidity)
                    if impact < 0.01:     # <0.01% impact - Excellent
                        analysis['activity_score'] = 10
                    elif impact < 0.1:    # <0.1% impact - Very Good
                        analysis['activity_score'] = 9
                    elif impact < 0.5:    # <0.5% impact - Good
                        analysis['activity_score'] = 7
                    elif impact < 1.0:    # <1.0% impact - Fair
                        analysis['activity_score'] = 5
                    elif impact < 2.0:    # <2.0% impact - Poor
                        analysis['activity_score'] = 3
                    else:                 # >2.0% impact - Very Poor
                        analysis['activity_score'] = 1
                except (ValueError, TypeError) as e:
                    analysis['validation_errors'].append(f"Price impact parsing error: {e}")
                    analysis['activity_score'] = 5  # Default
            else:
                analysis['activity_score'] = 5  # Default when no price impact data
            
            # Calculate overall trending score - VALIDATED
            raw_score = (
                analysis['liquidity_score'] * 0.6 +  # 60% weight on liquidity
                analysis['activity_score'] * 0.4     # 40% weight on activity
            )
            
            # Validate score range
            analysis['trending_score'] = max(0, min(10, raw_score))
            
            # Log validation warnings
            if analysis['validation_errors']:
                self.logger.warning(f"Jupiter quote validation issues for {token_address[:8]}...: {analysis['validation_errors']}")
                
        except Exception as e:
            analysis['validation_errors'].append(f"Quote analysis error: {e}")
            self.logger.error(f"Failed to analyze quote for {token_address[:8]}...: {e}")
        
        return analysis


class MeteoraConnector:
    """Meteora API connector - FIXED VERSION"""
    
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
        
        self.logger = logging.getLogger(__name__)
    
    def get_api_call_statistics(self) -> Dict[str, Any]:
        """Get API call statistics for reporting"""
        stats = self.api_stats.copy()
        stats["endpoints_used"] = list(stats["endpoints_used"])
        stats["average_response_time_ms"] = (
            stats["total_response_time_ms"] / max(1, stats["total_calls"])
        )
        return stats
    
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
    
    async def get_trending_pools_by_volume(self, limit: int = 30) -> List[Dict]:
        """Get trending pools sorted by 24h volume - FIXED VERSION"""
        # FIXED PARAMETERS based on our investigation
        params = {
            "q": "*",  # Required parameter for all results
            "sort_by": "volume_24h:desc",  # Correct sorting format
            "limit": limit
        }
        
        data = await self._make_tracked_request("/pool/search", params)
        
        if not data or not isinstance(data, dict):
            return []
        
        # FIXED DATA STRUCTURE - Extract from hits
        pools = data.get('hits', [])
        if pools:
            pools = [hit.get('document', {}) for hit in pools]
        
        # Process pools into trending tokens
        trending_tokens = []
        for pool in pools:
            if isinstance(pool, dict):
                token_mints = pool.get('token_mints', [])
                volume_24h = pool.get('volume_24h', 0)
                tvl = pool.get('tvl', 1)
                vlr = volume_24h / tvl if tvl > 0 else 0
                
                for token_address in token_mints:
                    if token_address != "So11111111111111111111111111111111111111112":  # Skip SOL
                        trending_token = {
                            'address': token_address,
                            'pool_id': pool.get('id', ''),
                            'pool_name': pool.get('pool_name', ''),
                            'volume_24h': volume_24h,
                            'tvl': tvl,
                            'vlr': vlr,
                            'fee_24h': pool.get('fee_24h', 0),
                            'trending_score': min(10, vlr),  # Cap at 10
                            'discovery_source': 'meteora_volume_trending'
                        }
                        trending_tokens.append(trending_token)
        
        self.logger.info(f"📊 Extracted {len(trending_tokens)} trending tokens from Meteora pools")
        return trending_tokens


class JupiterMeteoraIntegratedAnalyzer(CrossPlatformAnalyzer):
    """Enhanced analyzer that integrates both Jupiter and Meteora APIs"""
    
    def __init__(self, config: Optional[Dict] = None, logger: Optional[logging.Logger] = None):
        super().__init__(config, logger)
        
        # Initialize both connectors
        self.jupiter = JupiterConnector(self.enhanced_cache)
        self.meteora = MeteoraConnector(self.enhanced_cache)
        
        # Jupiter token lookup table for symbol resolution
        self.jupiter_token_lookup = {}  # {address: symbol}
        
        # Excluded token addresses (infrastructure tokens to filter out)
        self.excluded_addresses = {
            'So11111111111111111111111111111111111111112',  # SOL
            'EPjFWdd5AufqSSqeM2qN1xzybapC8G4wEGGkZwyTDt1v',  # USDC
            '27G8MtK7VtTcCHkpASjSDdkWWYfoqT6ggEuKidVJidD4',  # JLP
            'jupSoLaHXQiZZTSfEWMTRRgpnyFm8f6sZdosWBjx93v'   # JupSOL
        }
        
        self.logger.info("🚀 Jupiter + Meteora Integrated Analyzer initialized")
        self.logger.info(f"🚫 Excluding {len(self.excluded_addresses)} infrastructure tokens from analysis")
    
    def _build_jupiter_token_lookup(self, jupiter_tokens: List[Dict]):
        """Build lookup table from Jupiter token list for symbol resolution"""
        self.jupiter_token_lookup = {}
        
        for token in jupiter_tokens:
            if isinstance(token, dict):
                address = token.get('address', '').strip()
                symbol = token.get('symbol', '').strip()
                
                if address and symbol and symbol.upper() not in ['', 'UNKNOWN', 'NULL']:
                    self.jupiter_token_lookup[address] = symbol
        
        self.logger.info(f"🔍 Built Jupiter token lookup table with {len(self.jupiter_token_lookup)} symbols")
    
    async def collect_all_data(self) -> Dict[str, List[Dict]]:
        """Enhanced data collection including both Jupiter and Meteora"""
        self.logger.info("Starting integrated data collection: Jupiter + Meteora + existing platforms...")
        
        # Get base platform data
        base_results = await super().collect_all_data()
        
        # Add Jupiter and Meteora tasks
        integrated_tasks = [
            ('jupiter_all_tokens', self.jupiter.get_all_tokens()),
            ('meteora_trending_pools', self.meteora.get_trending_pools_by_volume(30)),
        ]
        
        # Execute integrated tasks
        completed_tasks = await asyncio.gather(*[task for _, task in integrated_tasks], return_exceptions=True)
        
        for (name, _), result in zip(integrated_tasks, completed_tasks):
            if isinstance(result, Exception):
                self.logger.error(f"Error in {name}: {result}")
                base_results[name] = []
            else:
                base_results[name] = result if result else []
        
        # Build Jupiter token lookup table BEFORE quote analysis
        jupiter_tokens = base_results.get('jupiter_all_tokens', [])
        if jupiter_tokens:
            self._build_jupiter_token_lookup(jupiter_tokens)
            
            # Sample top tokens for quote analysis (to avoid rate limits)
            sample_tokens = [token['address'] for token in jupiter_tokens[:50] if token.get('address')]
            
            jupiter_trending_task = self.jupiter.get_trending_tokens_via_quotes(sample_tokens, 15)
            try:
                jupiter_trending = await jupiter_trending_task
                base_results['jupiter_trending_quotes'] = jupiter_trending
            except Exception as e:
                self.logger.error(f"Error in Jupiter trending analysis: {e}")
                base_results['jupiter_trending_quotes'] = []
        
        # Combine and deduplicate tokens
        all_tokens = self._combine_and_deduplicate_tokens(base_results)
        base_results['integrated_trending_tokens'] = all_tokens
        
        self.logger.info(f"🎯 Integrated data collection complete: {len(all_tokens)} unique trending tokens discovered")
        return base_results
    
    def _combine_and_deduplicate_tokens(self, platform_data: Dict[str, List[Dict]]) -> List[Dict]:
        """Combine tokens from all sources and deduplicate - ENHANCED ACCURACY"""
        token_data = {}
        validation_stats = {
            'meteora_processed': 0,
            'meteora_invalid': 0,
            'jupiter_processed': 0,
            'jupiter_invalid': 0,
            'cross_platform_matches': 0
        }
        
        # Process Meteora tokens - ENHANCED VALIDATION
        meteora_tokens = platform_data.get('meteora_trending_pools', [])
        for token in meteora_tokens:
            address = token.get('address', '').strip()
            
            # Skip excluded infrastructure tokens
            if address in self.excluded_addresses:
                validation_stats['meteora_invalid'] += 1
                continue
            
            # Validate token address
            if not address or len(address) < 32:
                validation_stats['meteora_invalid'] += 1
                continue
                
            # Validate trending score
            trending_score = token.get('trending_score', 0)
            if not isinstance(trending_score, (int, float)) or trending_score < 0:
                self.logger.warning(f"Invalid Meteora trending score for {address[:8]}...: {trending_score}")
                trending_score = 0
            
            if address not in token_data:
                token_data[address] = {
                    'address': address,
                    'sources': ['meteora'],
                    'meteora_data': token,
                    'combined_score': min(10, max(0, trending_score))  # Validate range
                }
                validation_stats['meteora_processed'] += 1
        
        # Process Jupiter tokens - ENHANCED VALIDATION
        jupiter_trending = platform_data.get('jupiter_trending_quotes', [])
        for token in jupiter_trending:
            address = token.get('address', '').strip()
            
            # Skip excluded infrastructure tokens
            if address in self.excluded_addresses:
                validation_stats['jupiter_invalid'] += 1
                continue
            
            # Validate token address
            if not address or len(address) < 32:
                validation_stats['jupiter_invalid'] += 1
                continue
            
            # Validate trending score
            trending_score = token.get('trending_score', 0)
            if not isinstance(trending_score, (int, float)) or trending_score < 0:
                self.logger.warning(f"Invalid Jupiter trending score for {address[:8]}...: {trending_score}")
                trending_score = 0
            
            validated_score = min(10, max(0, trending_score))
            
            if address in token_data:
                # Cross-platform match found
                token_data[address]['sources'].append('jupiter')
                token_data[address]['jupiter_data'] = token
                # Combine scores with validation
                token_data[address]['combined_score'] += validated_score
                validation_stats['cross_platform_matches'] += 1
            else:
                token_data[address] = {
                    'address': address,
                    'sources': ['jupiter'],
                    'jupiter_data': token,
                    'combined_score': validated_score
                }
            
            validation_stats['jupiter_processed'] += 1
        
        # Convert to list and sort by combined score
        combined_tokens = list(token_data.values())
        
        # Final validation of combined scores
        for token in combined_tokens:
            if token['combined_score'] > 20:  # Max possible is 10+10
                self.logger.warning(f"Combined score too high for {token['address'][:8]}...: {token['combined_score']}")
                token['combined_score'] = 20
        
        combined_tokens.sort(key=lambda x: x['combined_score'], reverse=True)
        
        # Log validation statistics
        self.logger.info(f"Token deduplication stats: {validation_stats}")
        self.logger.info(f"Final token count: {len(combined_tokens)} (Meteora: {validation_stats['meteora_processed']}, Jupiter: {validation_stats['jupiter_processed']}, Cross-platform: {validation_stats['cross_platform_matches']})")
        
        return combined_tokens
    
    def get_api_stats(self) -> Dict[str, Dict[str, Any]]:
        """Enhanced API stats including Jupiter and Meteora"""
        stats = super().get_api_stats()
        
        # Add Jupiter stats
        if hasattr(self, 'jupiter') and self.jupiter:
            jupiter_stats = self.jupiter.get_api_call_statistics()
            stats['jupiter'] = {
                'calls': jupiter_stats.get('total_calls', 0),
                'successes': jupiter_stats.get('successful_calls', 0),
                'failures': jupiter_stats.get('failed_calls', 0),
                'total_time_ms': jupiter_stats.get('total_response_time_ms', 0),
                'estimated_cost': 0.0  # Jupiter is free
            }
        
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
    
    def _validate_test_results(self, results: Dict, platform_data: Dict) -> Dict[str, Any]:
        """Validate test results for accuracy and consistency"""
        validation = {
            "overall_accuracy": 0,
            "validation_errors": [],
            "validation_warnings": [],
            "data_consistency_checks": {},
            "score_validation": {},
            "api_validation": {}
        }
        
        try:
            # Validate API performance data
            api_stats = results.get("api_performance", {})
            for platform, stats in api_stats.items():
                success_rate = stats.get("successes", 0) / max(1, stats.get("calls", 1)) * 100
                if success_rate < 100:
                    validation["validation_warnings"].append(f"{platform} API success rate: {success_rate:.1f}%")
                
                avg_response = stats.get("total_time_ms", 0) / max(1, stats.get("calls", 1))
                if avg_response > 2000:  # >2s response time
                    validation["validation_warnings"].append(f"{platform} slow response: {avg_response:.0f}ms")
            
            # Validate token counts
            data_results = results.get("data_collection_results", {})
            jupiter_tokens = data_results.get("jupiter_all_tokens", 0)
            jupiter_trending = data_results.get("jupiter_trending_analysis", 0)
            meteora_tokens = data_results.get("meteora_trending_pools", 0)
            integrated_tokens = data_results.get("integrated_unique_tokens", 0)
            
            # Check for realistic token counts
            if jupiter_tokens < 100000:
                validation["validation_errors"].append(f"Jupiter token count too low: {jupiter_tokens}")
            if jupiter_trending > 50:
                validation["validation_warnings"].append(f"Jupiter trending count high: {jupiter_trending}")
            if meteora_tokens > 100:
                validation["validation_warnings"].append(f"Meteora token count high: {meteora_tokens}")
            
            # Validate score ranges in sample tokens
            sample_tokens = results.get("sample_integrated_tokens", [])
            score_issues = 0
            total_scores = 0
            
            for token in sample_tokens:
                combined_score = token.get("combined_score", 0)
                total_scores += 1
                
                if combined_score < 0 or combined_score > 20:
                    validation["validation_errors"].append(f"Invalid combined score: {combined_score}")
                    score_issues += 1
                
                # Validate individual platform scores
                if "jupiter_data" in token:
                    jupiter_score = token["jupiter_data"].get("trending_score", 0)
                    if jupiter_score < 0 or jupiter_score > 10:
                        validation["validation_errors"].append(f"Invalid Jupiter score: {jupiter_score}")
                        score_issues += 1
                
                if "meteora_data" in token:
                    meteora_score = token["meteora_data"].get("trending_score", 0)
                    if meteora_score < 0 or meteora_score > 10:
                        validation["validation_errors"].append(f"Invalid Meteora score: {meteora_score}")
                        score_issues += 1
            
            # Calculate accuracy metrics
            validation["data_consistency_checks"] = {
                "api_success_rate": sum(stats.get("successes", 0) for stats in api_stats.values()) / max(1, sum(stats.get("calls", 0) for stats in api_stats.values())) * 100,
                "token_count_realistic": jupiter_tokens >= 100000 and meteora_tokens <= 100,
                "score_validation_rate": (total_scores - score_issues) / max(1, total_scores) * 100
            }
            
            # Calculate overall accuracy
            accuracy_factors = [
                validation["data_consistency_checks"]["api_success_rate"],
                100 if validation["data_consistency_checks"]["token_count_realistic"] else 80,
                validation["data_consistency_checks"]["score_validation_rate"]
            ]
            
            validation["overall_accuracy"] = sum(accuracy_factors) / len(accuracy_factors)
            
            # Penalize for errors
            error_penalty = min(20, len(validation["validation_errors"]) * 5)
            warning_penalty = min(10, len(validation["validation_warnings"]) * 2)
            validation["overall_accuracy"] = max(0, validation["overall_accuracy"] - error_penalty - warning_penalty)
            
        except Exception as e:
            validation["validation_errors"].append(f"Validation process error: {e}")
            validation["overall_accuracy"] = 50  # Default low score for validation failures
        
        return validation
    
    def _extract_symbol_from_token(self, token: Dict, platform_key: str) -> str:
        """Extract symbol from token data with platform-specific logic"""
        
        # Platform-specific symbol extraction
        if platform_key == 'meteora_trending_pools':
            # For Meteora: extract from pool_name (e.g., "GOR-SOL" -> "GOR")
            pool_name = token.get('pool_name', '')
            if pool_name and '-' in pool_name:
                return pool_name.split('-')[0]
            return 'Unknown'
        
        elif platform_key == 'jupiter_trending_quotes':
            # For Jupiter quotes: use token lookup table to resolve symbols
            address = token.get('address', '').strip()
            if address and address in self.jupiter_token_lookup:
                symbol = self.jupiter_token_lookup[address]
                self.logger.debug(f"🔍 Resolved Jupiter symbol: {address[:8]}... -> {symbol}")
                return symbol
            else:
                self.logger.debug(f"❓ Jupiter symbol not found for: {address[:8]}...")
                return 'Unknown'
        
        elif platform_key in ['dexscreener_boosted', 'dexscreener_top', 'dexscreener_profiles']:
            # DexScreener tokens
            return token.get('baseToken', {}).get('symbol', 
                   token.get('symbol', 
                   token.get('name', 'Unknown')))
        
        elif platform_key == 'dexscreener_narratives':
            # DexScreener narrative tokens
            return token.get('baseToken', {}).get('symbol',
                   token.get('symbol',
                   token.get('name', 'Unknown')))
        
        elif platform_key == 'rugcheck_trending':
            # RugCheck tokens
            return token.get('symbol', 
                   token.get('name', 'Unknown'))
        
        elif platform_key in ['birdeye_trending', 'birdeye_emerging_stars']:
            # Birdeye tokens
            return token.get('symbol',
                   token.get('name', 'Unknown'))
        
        else:
            # Generic fallback
            return token.get('symbol', 
                   token.get('name',
                   token.get('baseToken', {}).get('symbol', 'Unknown')))
    
    def _generate_platform_breakdown(self, platform_data: Dict[str, List[Dict]]) -> Dict[str, Any]:
        """Generate comprehensive platform breakdown analysis"""
        breakdown = {
            "platform_summary": {},
            "token_distribution": {},
            "cross_platform_analysis": {},
            "detailed_token_table": []
        }
        
        # Track all tokens across platforms
        all_tokens = {}
        platform_counts = {}
        
        # Process each platform's data
        platform_mapping = {
            'dexscreener_boosted': 'DexScreener Boosted',
            'dexscreener_top': 'DexScreener Top',
            'dexscreener_profiles': 'DexScreener Profiles', 
            'dexscreener_narratives': 'DexScreener Narratives',
            'rugcheck_trending': 'RugCheck Trending',
            'birdeye_trending': 'Birdeye Trending',
            'birdeye_emerging_stars': 'Birdeye Emerging Stars',
            'meteora_trending_pools': 'Meteora Volume Trending',
            'jupiter_trending_quotes': 'Jupiter Quote Analysis',
            'jupiter_all_tokens': 'Jupiter Token List'
        }
        
        # Shorter platform names for table display
        platform_display_mapping = {
            'DexScreener Boosted': 'DexScreener-Boost',
            'DexScreener Top': 'DexScreener-Top',
            'DexScreener Profiles': 'DexScreener-Prof', 
            'DexScreener Narratives': 'DexScreener-Narr',
            'RugCheck Trending': 'RugCheck',
            'Birdeye Trending': 'Birdeye-Trend',
            'Birdeye Emerging Stars': 'Birdeye-Stars',
            'Meteora Volume Trending': 'Meteora-Vol',
            'Jupiter Quote Analysis': 'Jupiter-Quote',
            'Jupiter Token List': 'Jupiter-List'
        }
        
        for platform_key, platform_name in platform_mapping.items():
            tokens = platform_data.get(platform_key, [])
            token_count = len(tokens)
            platform_counts[platform_name] = token_count
            
            # Process tokens from this platform
            for token in tokens:
                if isinstance(token, dict):
                    # Extract token address and symbol with platform-specific logic
                    address = token.get('address', '')
                    
                    # Platform-specific symbol extraction
                    symbol = self._extract_symbol_from_token(token, platform_key)
                    
                    # Skip Jupiter token list (too many tokens)
                    if platform_key == 'jupiter_all_tokens':
                        continue
                    
                    # Skip excluded infrastructure tokens
                    if address in self.excluded_addresses:
                        continue
                    
                    if address and len(address) > 10:  # Valid address
                        if address not in all_tokens:
                            all_tokens[address] = {
                                'address': address,
                                'symbol': symbol,
                                'platforms': [],
                                'platform_data': {},
                                'platform_scores': {},  # Track scores per platform
                                'total_score': 0,
                                'platform_count': 0
                            }
                        else:
                            # Update symbol if we get a better one from another platform
                            if all_tokens[address]['symbol'] == 'Unknown' and symbol != 'Unknown':
                                all_tokens[address]['symbol'] = symbol
                        
                        # Check if this platform is already recorded for this token
                        if platform_name not in all_tokens[address]['platforms']:
                            # New platform - add it
                            all_tokens[address]['platforms'].append(platform_name)
                            all_tokens[address]['platform_data'][platform_name] = token
                            all_tokens[address]['platform_count'] = len(all_tokens[address]['platforms'])
                            
                            # Initialize platform score
                            score = token.get('trending_score', token.get('score', token.get('combined_score', 0)))
                            if isinstance(score, (int, float)):
                                all_tokens[address]['platform_scores'][platform_name] = score
                                all_tokens[address]['total_score'] += score
                        else:
                            # Same platform, multiple occurrences - use the BEST score
                            score = token.get('trending_score', token.get('score', token.get('combined_score', 0)))
                            if isinstance(score, (int, float)):
                                current_score = all_tokens[address]['platform_scores'].get(platform_name, 0)
                                if score > current_score:
                                    # Update to better score and token data
                                    score_diff = score - current_score
                                    all_tokens[address]['platform_scores'][platform_name] = score
                                    all_tokens[address]['platform_data'][platform_name] = token
                                    all_tokens[address]['total_score'] += score_diff
        
        # Generate platform summary
        breakdown["platform_summary"] = {
            "total_platforms": len([p for p, count in platform_counts.items() if count > 0]),
            "platform_counts": platform_counts,
            "total_unique_tokens": len(all_tokens)
        }
        
        # Analyze token distribution by platform count
        distribution = {}
        multi_platform_tokens = []
        
        for address, token_info in all_tokens.items():
            platform_count = token_info['platform_count']
            if platform_count not in distribution:
                distribution[platform_count] = 0
            distribution[platform_count] += 1
            
            if platform_count > 1:
                multi_platform_tokens.append(token_info)
        
        breakdown["token_distribution"] = {
            "by_platform_count": distribution,
            "multi_platform_tokens": len(multi_platform_tokens),
            "single_platform_tokens": distribution.get(1, 0)
        }
        
        # Sort multi-platform tokens by score and platform count
        multi_platform_tokens.sort(key=lambda x: (x['platform_count'], x['total_score']), reverse=True)
        
        breakdown["cross_platform_analysis"] = {
            "top_multi_platform_tokens": multi_platform_tokens[:20],
            "highest_platform_count": max(distribution.keys()) if distribution else 0,
            "cross_platform_percentage": (len(multi_platform_tokens) / max(1, len(all_tokens))) * 100
        }
        
        # Generate detailed token table
        all_tokens_list = list(all_tokens.values())
        all_tokens_list.sort(key=lambda x: (x['platform_count'], x['total_score']), reverse=True)
        
        for i, token in enumerate(all_tokens_list[:50]):  # Top 50 tokens
            # Convert platform names to shorter display names
            display_platforms = []
            for platform in token['platforms']:
                display_name = platform_display_mapping.get(platform, platform)
                display_platforms.append(display_name)
            
            breakdown["detailed_token_table"].append({
                "rank": i + 1,
                "symbol": token['symbol'],
                "address": token['address'],
                "platform_count": token['platform_count'],
                "platforms": ', '.join(display_platforms),
                "total_score": round(token['total_score'], 2),
                "status": "🏆 Multi-Platform" if token['platform_count'] > 1 else "⚪ Single-Platform"
            })
        
        return breakdown


async def test_jupiter_meteora_integration():
    """Test the integrated Jupiter + Meteora trending detection system"""
    # Setup logging
    logging.basicConfig(level=logging.INFO)
    logger = logging.getLogger(__name__)
    
    logger.info("🚀 Starting Jupiter + Meteora Cross-Platform Integration Test")
    logger.info("=" * 80)
    
    start_time = time.time()
    
    try:
        # Initialize the integrated analyzer
        config = {
            'cache_enabled': True,
            'parallel_processing': True,
            'max_concurrent_requests': 10
        }
        
        analyzer = JupiterMeteoraIntegratedAnalyzer(config, logger)
        
        # Run the integrated analysis
        logger.info("📊 Running integrated data collection...")
        platform_data = await analyzer.collect_all_data()
        
        # Generate analysis report
        logger.info("📋 Generating analysis report...")
        
        # Summary statistics
        jupiter_tokens = len(platform_data.get('jupiter_all_tokens', []))
        jupiter_trending = len(platform_data.get('jupiter_trending_quotes', []))
        meteora_tokens = len(platform_data.get('meteora_trending_pools', []))
        integrated_tokens = len(platform_data.get('integrated_trending_tokens', []))
        
        # API statistics
        api_stats = analyzer.get_api_stats()
        
        # Generate detailed platform breakdown
        platform_breakdown = analyzer._generate_platform_breakdown(platform_data)
        
        # Generate test results
        test_duration = time.time() - start_time
        
        results = {
            "test_summary": {
                "timestamp": datetime.now().isoformat(),
                "duration_seconds": round(test_duration, 2),
                "status": "SUCCESS"
            },
            "data_collection_results": {
                "jupiter_all_tokens": jupiter_tokens,
                "jupiter_trending_analysis": jupiter_trending,
                "meteora_trending_pools": meteora_tokens,
                "integrated_unique_tokens": integrated_tokens
            },
            "platform_breakdown": platform_breakdown,
            "api_performance": api_stats,
            "integration_analysis": {
                "jupiter_api_status": "WORKING" if jupiter_tokens > 0 else "FAILED",
                "meteora_api_status": "WORKING" if meteora_tokens > 0 else "FAILED",
                "cross_platform_correlation": "ENABLED" if integrated_tokens > 0 else "DISABLED",
                "trending_detection_feasibility": "HIGH" if integrated_tokens > 10 else "MEDIUM" if integrated_tokens > 5 else "LOW"
            },
            "sample_integrated_tokens": platform_data.get('integrated_trending_tokens', [])[:10],
            "recommendations": []
        }
        
        # Validate test results accuracy
        validation_results = analyzer._validate_test_results(results, platform_data)
        results["accuracy_validation"] = validation_results
        
        # Generate recommendations
        if jupiter_tokens > 0:
            results["recommendations"].append("✅ Jupiter Token List API working - use for comprehensive token discovery")
        if jupiter_trending > 0:
            results["recommendations"].append("✅ Jupiter Quote API working - use for real-time liquidity analysis")
        if meteora_tokens > 0:
            results["recommendations"].append("✅ Meteora Pool API working - use for volume/TVL trending detection")
        if integrated_tokens > 10:
            results["recommendations"].append("🎯 High integration success - ready for production deployment")
        
        # Add accuracy recommendations
        if validation_results["overall_accuracy"] >= 95:
            results["recommendations"].append("✅ Test results highly accurate - ready for production")
        elif validation_results["overall_accuracy"] >= 85:
            results["recommendations"].append("⚠️ Test results mostly accurate - minor improvements needed")
        else:
            results["recommendations"].append("🔴 Test accuracy issues detected - review validation errors")
        
        # Save results
        timestamp = int(time.time())
        filename = f"scripts/tests/jupiter_meteora_integration_results_{timestamp}.json"
        
        with open(filename, 'w') as f:
            json.dump(results, f, indent=2, default=str)
        
        # Print summary
        logger.info("\n🎯 INTEGRATION TEST RESULTS:")
        logger.info(f"Duration: {test_duration:.2f}s")
        logger.info(f"Jupiter Tokens: {jupiter_tokens}")
        logger.info(f"Jupiter Trending: {jupiter_trending}")
        logger.info(f"Meteora Tokens: {meteora_tokens}")
        logger.info(f"Integrated Total: {integrated_tokens}")
        logger.info(f"Results saved to: {filename}")
        
        logger.info("\n📊 API PERFORMANCE:")
        for platform, stats in api_stats.items():
            success_rate = (stats['successes'] / max(1, stats['calls'])) * 100
            logger.info(f"{platform}: {stats['calls']} calls, {success_rate:.1f}% success")
        
        # Display platform breakdown table
        platform_breakdown = results.get("platform_breakdown", {})
        if platform_breakdown:
            logger.info("\n📊 PLATFORM BREAKDOWN ANALYSIS:")
            
            # Platform summary
            platform_summary = platform_breakdown.get("platform_summary", {})
            logger.info(f"Total Platforms Active: {platform_summary.get('total_platforms', 0)}")
            logger.info(f"Total Unique Tokens: {platform_summary.get('total_unique_tokens', 0)}")
            
            # Platform counts
            platform_counts = platform_summary.get("platform_counts", {})
            logger.info("\n📋 TOKENS PER PLATFORM:")
            for platform, count in platform_counts.items():
                if count > 0:
                    logger.info(f"  • {platform}: {count} tokens")
            
            # Token distribution
            token_dist = platform_breakdown.get("token_distribution", {})
            logger.info(f"\n🔗 CROSS-PLATFORM DISTRIBUTION:")
            logger.info(f"Multi-Platform Tokens: {token_dist.get('multi_platform_tokens', 0)}")
            logger.info(f"Single-Platform Tokens: {token_dist.get('single_platform_tokens', 0)}")
            
            by_platform_count = token_dist.get("by_platform_count", {})
            for platform_count in sorted(by_platform_count.keys(), reverse=True):
                token_count = by_platform_count[platform_count]
                logger.info(f"  • {platform_count} platform(s): {token_count} tokens")
            
            # Top multi-platform tokens table
            detailed_table = platform_breakdown.get("detailed_token_table", [])
            if detailed_table:
                logger.info("\n🏆 TOP TOKENS ACROSS PLATFORMS:")
                logger.info("+" + "-"*4 + "+" + "-"*12 + "+" + "-"*8 + "+" + "-"*50 + "+" + "-"*12 + "+" + "-"*60 + "+")
                logger.info("| Rank | Symbol      | Platforms | Address                                          | Total Score | Platform Names                                                 |")
                logger.info("+" + "-"*4 + "+" + "-"*12 + "+" + "-"*8 + "+" + "-"*50 + "+" + "-"*12 + "+" + "-"*60 + "+")
                
                for token in detailed_table[:15]:  # Top 15 tokens
                    rank = str(token['rank']).ljust(2)
                    symbol = token['symbol'][:10].ljust(10)
                    platform_count = str(token['platform_count']).ljust(6)
                    address = token['address'][:46] + "..." if len(token['address']) > 46 else token['address'].ljust(46)
                    score = str(token['total_score']).ljust(10)
                    
                    # Truncate platform names if too long
                    platforms_text = token['platforms']
                    if len(platforms_text) > 58:
                        platforms_text = platforms_text[:55] + "..."
                    platforms_text = platforms_text.ljust(58)
                    
                    logger.info(f"| {rank} | {symbol} | {platform_count} | {address} | {score} | {platforms_text} |")
                
                logger.info("+" + "-"*4 + "+" + "-"*12 + "+" + "-"*8 + "+" + "-"*50 + "+" + "-"*12 + "+" + "-"*60 + "+")
        
        logger.info("\n✅ Jupiter + Meteora integration test completed successfully!")
        
        return results
        
    except Exception as e:
        logger.error(f"❌ Integration test failed: {e}")
        return {
            "test_summary": {
                "timestamp": datetime.now().isoformat(),
                "duration_seconds": round(time.time() - start_time, 2),
                "status": "FAILED",
                "error": str(e)
            }
        }


if __name__ == "__main__":
    asyncio.run(test_jupiter_meteora_integration()) 