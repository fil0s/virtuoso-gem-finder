#!/usr/bin/env python3
"""
Enhanced Jupiter Connector
Optimized implementation leveraging successful endpoint tests:
- lite-api.jup.ag/tokens (10,000 tokens with rich metadata)
- lite-api.jup.ag/price/v2 (batch pricing winner)
- quote-api.jup.ag/v6/quote (optimized usage)
"""

import asyncio
import aiohttp
import logging
import time
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Tuple, Set
import json
from dataclasses import dataclass
from collections import defaultdict
import hashlib

logger = logging.getLogger(__name__)

@dataclass
class EndpointConfig:
    """Configuration for different Jupiter endpoints"""
    url: str
    rate_limit_per_minute: int
    batch_size: int
    cache_ttl_seconds: int
    min_request_interval: float

class EnhancedJupiterConnector:
    """Enhanced Jupiter connector leveraging successful endpoint tests"""
    
    def __init__(self, enhanced_cache=None):
        self.enhanced_cache = enhanced_cache
        self.session = None
        self._session_initialized = False
        
        # Endpoint configurations based on test results
        self.endpoints = {
            'tokens': EndpointConfig(
                url="https://token.jup.ag/all",
                rate_limit_per_minute=60,  # Conservative for free tier
                batch_size=10000,  # Can handle large batches
                cache_ttl_seconds=3600,  # 1 hour cache for token list
                min_request_interval=1.0
            ),
            'price_v2': EndpointConfig(
                url="https://lite-api.jup.ag/price/v2",
                rate_limit_per_minute=120,  # Higher limit for batch pricing
                batch_size=100,  # Optimal batch size for pricing
                cache_ttl_seconds=300,  # 5 minute cache for prices
                min_request_interval=0.5
            ),
            'quote': EndpointConfig(
                url="https://quote-api.jup.ag/v6/quote",
                rate_limit_per_minute=30,  # Stricter rate limits
                batch_size=1,  # Individual quotes only
                cache_ttl_seconds=180,  # 3 minute cache for quotes
                min_request_interval=2.0
            )
        }
        
        # Rate limiting state
        self.rate_limiters = {}
        for endpoint_name, config in self.endpoints.items():
            self.rate_limiters[endpoint_name] = {
                'requests': [],
                'last_request': 0,
                'config': config
            }
        
        # Statistics tracking
        self.stats = {
            'tokens_endpoint': {'calls': 0, 'cache_hits': 0, 'errors': 0},
            'price_v2_endpoint': {'calls': 0, 'cache_hits': 0, 'errors': 0, 'tokens_priced': 0},
            'quote_endpoint': {'calls': 0, 'cache_hits': 0, 'errors': 0},
            'batch_efficiency': {'total_batches': 0, 'total_individual_requests_saved': 0}
        }
        
        # Exclusion system
        self.excluded_addresses = self._load_exclusions()
        
    def _load_exclusions(self) -> Set[str]:
        """Load exclusion list from central system"""
        try:
            import sys
            import os
            sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'services'))
            from early_token_detection import EarlyTokenDetector
            
            detector = EarlyTokenDetector()
            exclusions = detector.get_excluded_addresses()
            logger.info(f"🚫 Loaded {len(exclusions)} excluded addresses from central system")
            return exclusions
            
        except Exception as e:
            logger.warning(f"Could not load central exclusions: {e}")
            return {
                'EPjFWdd5AufqSSqeM2qN1xzybapC8G4wEGGkZwyTDt1v',  # USDC
                'Es9vMFrzaCERmJfrF4H2FYD4KCoNkY11McCe8BenwNYB',  # USDT
                'So11111111111111111111111111111111111111112',   # SOL
            }
    
    async def __aenter__(self):
        self.session = aiohttp.ClientSession()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.session:
            await self.session.close()
    
    def _can_make_request(self, endpoint_name: str) -> bool:
        """Check if we can make a request to the endpoint"""
        limiter = self.rate_limiters[endpoint_name]
        config = limiter['config']
        now = time.time()
        
        # Clean old requests (older than 1 minute)
        limiter['requests'] = [req_time for req_time in limiter['requests'] 
                              if now - req_time < 60]
        
        # Check rate limit
        if len(limiter['requests']) >= config.rate_limit_per_minute:
            return False
        
        # Check minimum interval
        if now - limiter['last_request'] < config.min_request_interval:
            return False
        
        return True
    
    async def _wait_for_rate_limit(self, endpoint_name: str):
        """Wait for rate limiting if necessary"""
        while not self._can_make_request(endpoint_name):
            await asyncio.sleep(0.1)
    
    def _record_request(self, endpoint_name: str):
        """Record a request for rate limiting"""
        now = time.time()
        limiter = self.rate_limiters[endpoint_name]
        limiter['requests'].append(now)
        limiter['last_request'] = now
    
    async def _ensure_session(self):
        """Ensure HTTP session is initialized"""
        if not self.session or self.session.closed:
            self.session = aiohttp.ClientSession()
            self._session_initialized = True

    async def _make_cached_request(self, endpoint_name: str, cache_key: str, 
                                 url: str, params: Optional[Dict] = None) -> Tuple[bool, Optional[Dict], Optional[str]]:
        """Make a cached request with rate limiting"""
        
        # Check cache first
        if self.enhanced_cache:
            cached_data = self.enhanced_cache.get_enhanced("jupiter_enhanced", cache_key)
            if cached_data:
                self.stats[f'{endpoint_name}_endpoint']['cache_hits'] += 1
                return True, cached_data, None
        
        # Ensure session is initialized
        await self._ensure_session()
        
        # Wait for rate limiting
        await self._wait_for_rate_limit(endpoint_name)
        self._record_request(endpoint_name)
        
        try:
            async with self.session.get(url, params=params) as response:
                if response.status == 200:
                    data = await response.json()
                    
                    # Cache the result
                    if self.enhanced_cache:
                        ttl = self.endpoints[endpoint_name].cache_ttl_seconds
                        self.enhanced_cache.set_enhanced("jupiter_enhanced", cache_key, data)
                    
                    self.stats[f'{endpoint_name}_endpoint']['calls'] += 1
                    return True, data, None
                else:
                    error_msg = f"HTTP {response.status}: {await response.text()}"
                    self.stats[f'{endpoint_name}_endpoint']['errors'] += 1
                    return False, None, error_msg
                    
        except Exception as e:
            self.stats[f'{endpoint_name}_endpoint']['errors'] += 1
            return False, None, str(e)
    
    async def get_enhanced_token_list(self, limit: int = 10000, include_metadata: bool = True, 
                                     filter_criteria: Optional[Dict] = None) -> List[Dict]:
        """Get comprehensive token list from lite-api.jup.ag/tokens with intelligent filtering"""
        cache_key = f"enhanced_tokens_list_{limit}_{include_metadata}_{hash(str(filter_criteria))}"
        
        success, data, error = await self._make_cached_request(
            'tokens', cache_key, self.endpoints['tokens'].url
        )
        
        if not success or not data:
            logger.error(f"Failed to fetch token list: {error}")
            return []
        
        # Process and filter tokens
        filtered_tokens = []
        excluded_count = 0
        filter_stats = {
            'excluded_addresses': 0,
            'min_daily_volume': 0,
            'new_tokens': 0,
            'old_tokens': 0,
            'missing_tags': 0,
            'high_risk': 0,
            'tag_limit_reached': {}
        }
        
        # Apply filtering criteria
        filter_criteria = filter_criteria or {}
        min_daily_volume = filter_criteria.get('min_daily_volume', 0)
        exclude_new_days = filter_criteria.get('exclude_new_tokens_days', 0)
        exclude_old_days = filter_criteria.get('exclude_old_tokens_days', 0)
        required_tags = filter_criteria.get('required_tags', [])
        exclude_risk_levels = filter_criteria.get('exclude_risk_levels', [])
        max_tokens_per_tag = filter_criteria.get('max_tokens_per_tag', float('inf'))
        
        # Track tokens per tag
        tag_counts = {}
        current_time = time.time()
        
        for token in data:
            if not isinstance(token, dict) or 'address' not in token:
                continue
            
            address = token.get('address', '')
            
            # Skip excluded addresses
            if address in self.excluded_addresses:
                filter_stats['excluded_addresses'] += 1
                continue
            
            # Enhanced token data with rich metadata
            token_data = {
                'address': address,
                'symbol': token.get('symbol', ''),
                'name': token.get('name', ''),
                'decimals': token.get('decimals', 9),
                'logo_uri': token.get('logoURI', ''),
                'tags': token.get('tags', []),
                'daily_volume': token.get('daily_volume', 0),
                'freeze_authority': token.get('freeze_authority'),
                'mint_authority': token.get('mint_authority'),
                'permanent_delegate': token.get('permanent_delegate'),
                'minted_at': token.get('minted_at'),
                'extensions': token.get('extensions', {}),
                'discovery_source': 'jupiter_lite_api_tokens',
                'timestamp': time.time()
            }
            
            # Add risk assessment if metadata requested
            if include_metadata:
                token_data['risk_level'] = self._assess_token_risk(token)
                token_data['quality_score'] = self._calculate_token_quality(token)
            
            # Apply filters
            should_include = True
            
            # Filter by daily volume
            if min_daily_volume > 0 and token_data['daily_volume'] < min_daily_volume:
                filter_stats['min_daily_volume'] += 1
                should_include = False
            
            # Filter by token age (if minted_at is available)
            if should_include and token_data.get('minted_at'):
                try:
                    minted_timestamp = int(token_data['minted_at'])
                    token_age_days = (current_time - minted_timestamp) / (24 * 3600)
                    
                    if exclude_new_days > 0 and token_age_days < exclude_new_days:
                        filter_stats['new_tokens'] += 1
                        should_include = False
                    elif exclude_old_days > 0 and token_age_days > exclude_old_days:
                        filter_stats['old_tokens'] += 1
                        should_include = False
                except (ValueError, TypeError):
                    pass  # Skip age filtering if timestamp is invalid
            
            # Filter by required tags
            if should_include and required_tags:
                token_tags = token_data.get('tags', [])
                if not any(tag in token_tags for tag in required_tags):
                    filter_stats['missing_tags'] += 1
                    should_include = False
            
            # Filter by risk level
            if should_include and exclude_risk_levels and include_metadata:
                if token_data.get('risk_level') in exclude_risk_levels:
                    filter_stats['high_risk'] += 1
                    should_include = False
            
            # Apply per-tag limits
            if should_include and max_tokens_per_tag < float('inf'):
                token_tags = token_data.get('tags', [])
                for tag in token_tags:
                    if tag_counts.get(tag, 0) >= max_tokens_per_tag:
                        if tag not in filter_stats['tag_limit_reached']:
                            filter_stats['tag_limit_reached'][tag] = 0
                        filter_stats['tag_limit_reached'][tag] += 1
                        should_include = False
                        break
                
                # Update tag counts if token is included
                if should_include:
                    for tag in token_tags:
                        tag_counts[tag] = tag_counts.get(tag, 0) + 1
            
            if should_include:
                filtered_tokens.append(token_data)
                
                # Stop if we've reached the limit
                if len(filtered_tokens) >= limit:
                    break
        
        # Log filtering results
        total_filtered = (filter_stats['excluded_addresses'] + filter_stats['min_daily_volume'] + 
                         filter_stats['new_tokens'] + filter_stats['old_tokens'] + 
                         filter_stats['missing_tags'] + filter_stats['high_risk'] + 
                         sum(filter_stats['tag_limit_reached'].values()))
        logger.info(f"🪙 Enhanced Jupiter: {len(filtered_tokens)} tokens (filtered out {total_filtered})")
        
        if filter_criteria:
            logger.info(f"📊 Filter breakdown:")
            logger.info(f"  • Excluded addresses: {filter_stats['excluded_addresses']}")
            if min_daily_volume > 0:
                logger.info(f"  • Low volume (<${min_daily_volume:,}): {filter_stats['min_daily_volume']}")
            if exclude_new_days > 0:
                logger.info(f"  • Too new (<{exclude_new_days} days): {filter_stats['new_tokens']}")
            if exclude_old_days > 0:
                logger.info(f"  • Too old (>{exclude_old_days} days): {filter_stats['old_tokens']}")
            if required_tags:
                logger.info(f"  • Missing required tags: {filter_stats['missing_tags']}")
            if exclude_risk_levels:
                logger.info(f"  • High risk tokens: {filter_stats['high_risk']}")
            if filter_stats['tag_limit_reached']:
                logger.info(f"  • Tag limits reached: {len(filter_stats['tag_limit_reached'])} tags")
        
        return filtered_tokens
    
    async def get_batch_prices(self, token_addresses: List[str], vs_token: str = "EPjFWdd5AufqSSqeM2qN1xzybapC8G4wEGGkZwyTDt1v") -> Dict[str, Dict]:
        """Get batch prices using lite-api.jup.ag/price/v2 (the winner!)"""
        if not token_addresses:
            return {}
        
        # Filter out excluded addresses
        filtered_addresses = [addr for addr in token_addresses if addr not in self.excluded_addresses]
        
        if not filtered_addresses:
            return {}
        
        # Process in optimal batches
        batch_size = self.endpoints['price_v2'].batch_size
        all_prices = {}
        
        for i in range(0, len(filtered_addresses), batch_size):
            batch = filtered_addresses[i:i + batch_size]
            batch_key = hashlib.md5(f"batch_prices_{'_'.join(batch)}_{vs_token}".encode()).hexdigest()
            
            # Prepare request parameters
            params = {
                'ids': ','.join(batch),
                'vsToken': vs_token
            }
            
            success, data, error = await self._make_cached_request(
                'price_v2', batch_key, self.endpoints['price_v2'].url, params
            )
            
            if success and data and 'data' in data:
                # Process batch results
                for token_addr, price_data in data['data'].items():
                    if price_data and 'price' in price_data:
                        all_prices[token_addr] = {
                            'price': float(price_data['price']),
                            'vs_token': vs_token,
                            'timestamp': time.time(),
                            'source': 'jupiter_lite_api_price_v2'
                        }
                
                # Update batch efficiency stats
                self.stats['batch_efficiency']['total_batches'] += 1
                self.stats['batch_efficiency']['total_individual_requests_saved'] += len(batch) - 1
                self.stats['price_v2_endpoint']['tokens_priced'] += len(batch)
            
            elif error:
                logger.warning(f"Batch pricing failed for batch {i//batch_size + 1}: {error}")
        
        logger.info(f"💰 Batch priced {len(all_prices)} tokens in {len(range(0, len(filtered_addresses), batch_size))} batches")
        return all_prices
    
    async def get_enhanced_quote(self, input_mint: str, output_mint: str, amount: int, 
                               slippage_bps: int = 50) -> Optional[Dict]:
        """Get enhanced quote using quote-api.jup.ag/v6/quote (optimized usage)"""
        
        # Note: We don't exclude tokens for quote analysis since this is for liquidity research
        # SOL/USDC are legitimate base pairs for analyzing routing and liquidity
        
        cache_key = f"enhanced_quote_{input_mint}_{output_mint}_{amount}_{slippage_bps}"
        
        params = {
            'inputMint': input_mint,
            'outputMint': output_mint,
            'amount': str(amount),
            'slippageBps': str(slippage_bps),
            'onlyDirectRoutes': 'false',  # Allow complex routing
            'asLegacyTransaction': 'false'  # Use modern transaction format
        }
        
        success, data, error = await self._make_cached_request(
            'quote', cache_key, self.endpoints['quote'].url, params
        )
        
        if not success or not data:
            logger.debug(f"Quote failed for {input_mint} -> {output_mint}: {error}")
            return None
        
        # Enhanced quote analysis
        enhanced_quote = {
            'input_mint': input_mint,
            'output_mint': output_mint,
            'input_amount': amount,
            'output_amount': int(data.get('outAmount', 0)),
            'price_impact_pct': float(data.get('priceImpactPct', 0)),
            'route_plan': data.get('routePlan', []),
            'swap_mode': data.get('swapMode', ''),
            'slippage_bps': int(data.get('slippageBps', slippage_bps)),
            'other_amount_threshold': int(data.get('otherAmountThreshold', 0)),
            'swap_mode_label': data.get('swapModeLabel', ''),
            'context_slot': data.get('contextSlot', 0),
            'time_taken': data.get('timeTaken', 0),
            
            # Enhanced analysis
            'liquidity_score': self._calculate_liquidity_score(
                float(data.get('priceImpactPct', 0)), 
                len(data.get('routePlan', []))
            ),
            'routing_complexity': len(data.get('routePlan', [])),
            'efficiency_ratio': self._calculate_efficiency_ratio(data),
            'discovery_source': 'jupiter_quote_api_v6',
            'timestamp': time.time()
        }
        
        return enhanced_quote
    
    async def get_comprehensive_token_analysis(self, token_addresses: List[str]) -> Dict[str, Dict]:
        """Comprehensive analysis combining all three endpoints"""
        results = {}
        
        # 1. Get batch prices (most efficient)
        logger.info(f"🔍 Starting comprehensive analysis for {len(token_addresses)} tokens")
        prices = await self.get_batch_prices(token_addresses)
        
        # 2. Get enhanced token metadata
        token_list = await self.get_enhanced_token_list(limit=10000)
        token_metadata = {token['address']: token for token in token_list}
        
        # 3. Get selective quotes for high-value tokens
        sol_mint = "So11111111111111111111111111111111111111112"
        usdc_mint = "EPjFWdd5AufqSSqeM2qN1xzybapC8G4wEGGkZwyTDt1v"
        
        for address in token_addresses:
            if address in self.excluded_addresses:
                continue
            
            analysis = {
                'address': address,
                'price_data': prices.get(address, {}),
                'metadata': token_metadata.get(address, {}),
                'quote_data': {},
                'analysis_timestamp': time.time(),
                'data_sources': []
            }
            
            # Add data source tracking
            if address in prices:
                analysis['data_sources'].append('lite_api_price_v2')
            if address in token_metadata:
                analysis['data_sources'].append('lite_api_tokens')
            
            # Get quote data for tokens with good price data
            if address in prices and prices[address].get('price', 0) > 0:
                quote = await self.get_enhanced_quote(sol_mint, address, 1000000)  # 1 SOL worth
                if quote:
                    analysis['quote_data'] = quote
                    analysis['data_sources'].append('quote_api_v6')
            
            results[address] = analysis
        
        logger.info(f"✅ Comprehensive analysis complete: {len(results)} tokens analyzed")
        return results
    
    def _assess_token_risk(self, token: Dict) -> str:
        """Assess token risk level based on metadata"""
        risk_factors = 0
        
        # Check for risk indicators
        if token.get('freeze_authority'):
            risk_factors += 2
        if token.get('mint_authority'):
            risk_factors += 1
        if not token.get('symbol'):
            risk_factors += 1
        if not token.get('name'):
            risk_factors += 1
        if not token.get('logoURI'):
            risk_factors += 0.5
        
        # Risk classification
        if risk_factors >= 4:
            return 'high'
        elif risk_factors >= 2:
            return 'medium'
        else:
            return 'low'
    
    def _calculate_token_quality(self, token: Dict) -> float:
        """Calculate token quality score (0-1)"""
        score = 0.0
        
        # Metadata completeness (40%)
        if token.get('symbol'):
            score += 0.1
        if token.get('name'):
            score += 0.1
        if token.get('logoURI'):
            score += 0.1
        if token.get('tags'):
            score += 0.1
        
        # Authority status (30%)
        if not token.get('freeze_authority'):
            score += 0.15
        if not token.get('mint_authority'):
            score += 0.15
        
        # Activity indicators (30%)
        daily_volume = token.get('daily_volume', 0)
        if daily_volume > 100000:  # $100k+
            score += 0.15
        elif daily_volume > 10000:  # $10k+
            score += 0.1
        elif daily_volume > 1000:  # $1k+
            score += 0.05
        
        if token.get('extensions'):
            score += 0.15
        
        return min(1.0, score)
    
    def _calculate_liquidity_score(self, price_impact: float, route_complexity: int) -> float:
        """Calculate liquidity score based on price impact and routing"""
        # Lower price impact = better liquidity
        impact_score = max(0, 1 - (price_impact / 10))  # 10% impact = 0 score
        
        # Simpler routing = better liquidity
        complexity_score = max(0, 1 - (route_complexity - 1) * 0.2)  # Penalty for complex routes
        
        return (impact_score + complexity_score) / 2
    
    def _calculate_efficiency_ratio(self, quote_data: Dict) -> float:
        """Calculate routing efficiency ratio"""
        try:
            input_amount = int(quote_data.get('inAmount', 0))
            output_amount = int(quote_data.get('outAmount', 0))
            
            if input_amount > 0:
                return output_amount / input_amount
            return 0.0
        except:
            return 0.0
    
    def get_api_statistics(self) -> Dict[str, Any]:
        """Get comprehensive API statistics"""
        total_calls = sum(endpoint['calls'] for endpoint in self.stats.values() if 'calls' in endpoint)
        total_cache_hits = sum(endpoint['cache_hits'] for endpoint in self.stats.values() if 'cache_hits' in endpoint)
        total_errors = sum(endpoint['errors'] for endpoint in self.stats.values() if 'errors' in endpoint)
        
        cache_hit_rate = (total_cache_hits / (total_calls + total_cache_hits) * 100) if (total_calls + total_cache_hits) > 0 else 0
        error_rate = (total_errors / total_calls * 100) if total_calls > 0 else 0
        
        return {
            'endpoint_stats': self.stats,
            'summary': {
                'total_api_calls': total_calls,
                'total_cache_hits': total_cache_hits,
                'total_errors': total_errors,
                'cache_hit_rate_percent': round(cache_hit_rate, 2),
                'error_rate_percent': round(error_rate, 2),
                'batch_efficiency': self.stats['batch_efficiency']
            }
        }
    
    def reset_statistics(self):
        """Reset all statistics"""
        for endpoint_stats in self.stats.values():
            if isinstance(endpoint_stats, dict):
                for key in endpoint_stats:
                    endpoint_stats[key] = 0
    
    async def close(self):
        """Close HTTP session"""
        if self.session and not self.session.closed:
            await self.session.close()
        self.session = None
        self._session_initialized = False
    
    def get_api_call_statistics(self) -> Dict[str, Any]:
        """Get API call statistics for compatibility with cross-platform analyzer"""
        stats = self.get_api_statistics()
        
        # Convert to format expected by cross-platform analyzer
        return {
            'total_calls': stats['summary']['total_api_calls'],
            'successful_calls': stats['summary']['total_api_calls'] - stats['summary']['total_errors'],
            'failed_calls': stats['summary']['total_errors'],
            'success_rate': 100.0 - stats['summary']['error_rate_percent'],
            'runtime_seconds': 0,  # Not tracked in enhanced connector
            'calls_per_minute': 0,  # Not tracked in enhanced connector
            'last_error': None  # Not tracked in enhanced connector
        }
