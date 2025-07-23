"""
Raydium DEX API connector for enhanced liquidity and trading pair analysis
Integrates with existing virtuoso_gem_hunter API system
"""

import asyncio
import aiohttp
import json
import logging
from typing import Dict, List, Optional, Any
from datetime import datetime
import time
from tenacity import retry, stop_after_attempt, wait_exponential, RetryError, retry_if_exception_type

try:
    from utils.enhanced_structured_logger import create_enhanced_logger, APICallType
    HAS_ENHANCED_LOGGING = True
except ImportError:
    HAS_ENHANCED_LOGGING = False

logger = logging.getLogger(__name__)

class RaydiumConnector:
    """Production Raydium API connector following existing system patterns"""
    
    def __init__(self, enhanced_cache=None, api_tracking_enabled: bool = True, rate_limiter=None):
        self.base_url = "https://api-v3.raydium.io"  # Updated to v3 API
        self.v3_endpoints = {
            'pools': '/pools/info/list?poolType=all&poolSortField=volume24h&sortType=desc&page=1&pageSize=100',
            'pairs': '/pools/info/list?poolType=all&poolSortField=liquidity&sortType=desc&page=1&pageSize=100', 
            'tokens': '/mint/list',
            'main': '/pools/info/list'
        }
        # Legacy v2 fallback endpoints
        self.v2_base_url = "https://api.raydium.io/v2/main"
        self.session = None
        self.enhanced_cache = enhanced_cache
        self.api_tracking_enabled = api_tracking_enabled
        self.rate_limiter = rate_limiter
        
        # Initialize enhanced logging if available
        if HAS_ENHANCED_LOGGING:
            try:
                self.enhanced_logger = create_enhanced_logger(
                    domain="raydium",
                    logger_name="RaydiumConnector",
                    base_logger=logger
                )
            except Exception:
                self.enhanced_logger = None
        else:
            self.enhanced_logger = None
        
        # API tracking stats
        self.api_calls_made = 0
        self.last_call_time = 0
        self.rate_limit_delay = 2.0  # 2 seconds between calls (Raydium is more aggressive)
        self.successful_calls = 0
        self.failed_calls = 0
        self.total_response_time = 0
        
        # WSOL filtering
        self.wsol_address = 'So11111111111111111111111111111111111111112'
        
        # Load exclusion list (same pattern as existing connectors)
        self._load_exclusions()
    
    def _load_exclusions(self):
        """Load token exclusion list following existing patterns"""
        self.excluded_addresses = {
            # Major stablecoins
            'EPjFWdd5AufqSSqeM2qN1xzybapC8G4wEGGkZwyTDt1v',  # USDC
            'Es9vMFrzaCERmJfrF4H2FYD4KCoNkY11McCe8BenwNYB',  # USDT
            'EjmyN6qEC1Tf1JxiG1ae7UTJhUxSwk1TCWNWqxWV4J6o',  # DAI
            '9n4nbM75f5Ui33ZbPYXn59EwSgE8CGsHtAeTH5YFeJ9E',  # BTC
            '2FPyTwcZLUg1MDrwsyoP4D6s1tM7hAkHYRjkNb5w6Pxk',  # ETH
            # Wrapped tokens
            'So11111111111111111111111111111111111111112',   # SOL
            'DezXAZ8z7PnrnRJjz3wXBoRgixCa6xjnB7YaB1pPB263',  # BONK
            # Add more as needed
        }
    
    async def __aenter__(self):
        self.session = aiohttp.ClientSession()
        return self
        
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.session:
            await self.session.close()
    
    def get_api_call_statistics(self) -> Dict[str, Any]:
        """Get API call statistics following existing patterns"""
        avg_response_time = (self.total_response_time / max(1, self.successful_calls))
        
        return {
            'total_calls': self.api_calls_made,
            'successful_calls': self.successful_calls,
            'failed_calls': self.failed_calls,
            'success_rate': self.successful_calls / max(1, self.api_calls_made),
            'average_response_time': avg_response_time,
            'last_call_time': self.last_call_time
        }
    
    def reset_api_statistics(self):
        """Reset API statistics"""
        self.api_calls_made = 0
        self.successful_calls = 0
        self.failed_calls = 0
        self.total_response_time = 0
        self.last_call_time = 0
    
    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=4, max=10),
        retry=retry_if_exception_type((aiohttp.ClientError, asyncio.TimeoutError))
    )
    async def _make_tracked_request(self, endpoint: str, timeout: int = 60, use_v2_fallback: bool = True) -> Optional[Any]:
        """Make rate-limited API request with tracking and v2 fallback"""
        
        # Use RateLimiterService if available, otherwise fall back to simple rate limiting
        if self.rate_limiter:
            await self.rate_limiter.wait_for_slot("raydium")
        elif self.api_tracking_enabled:
            # Fallback rate limiting (more aggressive for Raydium)
            current_time = time.time()
            time_since_last = current_time - self.last_call_time
            if time_since_last < self.rate_limit_delay:
                await asyncio.sleep(self.rate_limit_delay - time_since_last)
            
        if self.api_tracking_enabled:
            self.api_calls_made += 1
            self.last_call_time = time.time()
        
        # Try v3 endpoint first
        v3_url = f"{self.base_url}{endpoint}"
        start_time = time.time()
        
        try:
            timeout_config = aiohttp.ClientTimeout(total=timeout)
            async with self.session.get(v3_url, timeout=timeout_config) as response:
                response_time = time.time() - start_time
                self.total_response_time += response_time
                
                if response.status == 200:
                    self.successful_calls += 1
                    logger.debug(f"✅ Raydium v3 API success: {endpoint}")
                    
                    # Enhanced logging
                    if self.enhanced_logger:
                        self.enhanced_logger.log_api_call(
                            api_type=APICallType.GET,
                            endpoint=endpoint,
                            status_code=response.status,
                            response_time_ms=int(response_time * 1000),
                            success=True
                        )
                    
                    try:
                        return await response.json()
                    except json.JSONDecodeError as json_err:
                        logger.error(f"❌ Raydium v3 JSON decode error for {endpoint}: {json_err}")
                        
                        # Enhanced logging for JSON errors
                        if self.enhanced_logger:
                            self.enhanced_logger.log_api_call(
                                api_type=APICallType.GET,
                                endpoint=endpoint,
                                status_code=response.status,
                                response_time_ms=int(response_time * 1000),
                                success=False,
                                error_message=f"JSON decode error: {json_err}"
                            )
                        
                        raise aiohttp.ClientError(f"Invalid JSON response: {json_err}")
                elif response.status == 429:
                    self.failed_calls += 1
                    logger.warning(f"⚠️ Raydium v3 API rate limited for {endpoint}")
                    await asyncio.sleep(5)
                    raise aiohttp.ClientError(f"Rate limited: {response.status}")
                elif response.status >= 500:
                    logger.warning(f"⚠️ Raydium v3 server error {response.status} for {endpoint}")
                    raise aiohttp.ClientError(f"Server error: {response.status}")
                else:
                    logger.warning(f"⚠️ Raydium v3 client error {response.status} for {endpoint}")
                    # Don't retry on client errors (4xx)
                    return None
                    
        except (aiohttp.ClientError, asyncio.TimeoutError) as e:
            logger.warning(f"⚠️ Raydium v3 API request failed for {endpoint}: {e}")
            raise  # Re-raise for retry logic
        except Exception as e:
            logger.error(f"❌ Unexpected error for Raydium v3 {endpoint}: {e}")
            return None
        
        # Fallback to v2 if enabled and v3 failed
        if use_v2_fallback and endpoint in ['/pools', '/pairs']:
            logger.info(f"🔄 Falling back to Raydium v2 for {endpoint}")
            v2_endpoint = endpoint
            if endpoint == '/pools':
                v2_endpoint = '/pools'
            elif endpoint == '/pairs':
                v2_endpoint = '/pairs'
                
            try:
                v2_url = f"{self.v2_base_url}{v2_endpoint}"
                timeout_config = aiohttp.ClientTimeout(total=timeout)
                async with self.session.get(v2_url, timeout=timeout_config) as response:
                    response_time = time.time() - start_time
                    self.total_response_time += response_time
                    
                    if response.status == 200:
                        self.successful_calls += 1
                        logger.info(f"✅ Raydium v2 fallback success: {endpoint}")
                        try:
                            return await response.json()
                        except json.JSONDecodeError as json_err:
                            logger.error(f"❌ Raydium v2 JSON decode error for {endpoint}: {json_err}")
                            return None
                    else:
                        self.failed_calls += 1
                        logger.warning(f"⚠️ Raydium v2 API error {response.status} for {endpoint}")
                        return None
            except (aiohttp.ClientError, asyncio.TimeoutError) as e:
                self.failed_calls += 1
                response_time = time.time() - start_time
                self.total_response_time += response_time
                logger.warning(f"⚠️ Raydium v2 fallback connection failed for {endpoint}: {e}")
                return None
            except Exception as e:
                self.failed_calls += 1
                response_time = time.time() - start_time
                self.total_response_time += response_time
                logger.error(f"❌ Raydium v2 fallback unexpected error for {endpoint}: {e}")
                return None
        
        self.failed_calls += 1
        return None
    
    async def get_pools(self, limit: Optional[int] = 50000) -> List[Dict]:
        """Get Raydium pools using v3 API with v2 fallback"""
        cache_key = f"raydium_v3_pools_{limit or 'all'}"
        
        # Check cache first
        if self.enhanced_cache:
            try:
                cached_data = await self.enhanced_cache.get_with_tracking(cache_key, "raydium_pools")
                if cached_data:
                    return cached_data
            except Exception as e:
                logger.debug(f"Cache get failed: {e}")
        
        # Try v3 endpoint first, fallback to v2
        data = await self._make_tracked_request(self.v3_endpoints['pools'], use_v2_fallback=True)
        pools = data if data else []
        
        # Handle different response structures between v2 and v3
        if isinstance(data, dict):
            # v3 API returns {success: true, data: {data: [...], hasNextPage: false}}
            if data.get('success') and 'data' in data:
                pools = data['data'].get('data', [])
            else:
                pools = data.get('data', data.get('pools', []))
        elif isinstance(data, list):
            # Direct list response (v2 style)
            pools = data
        else:
            pools = []
        
        if limit and pools and isinstance(pools, list):
            pools = pools[:limit]
        
        # Cache the results
        if self.enhanced_cache and pools:
            try:
                await self.enhanced_cache.set_with_intelligent_ttl(cache_key, pools, "raydium_pools")
            except Exception as e:
                logger.debug(f"Cache set failed: {e}")
        
        return pools if isinstance(pools, list) else []
    
    async def get_pairs(self, limit: Optional[int] = 50000) -> List[Dict]:
        """Get Raydium pairs using v3 API with v2 fallback"""
        cache_key = f"raydium_v3_pairs_{limit or 'all'}"
        
        # Check cache first
        if self.enhanced_cache:
            try:
                cached_data = await self.enhanced_cache.get_with_tracking(cache_key, "raydium_pairs")
                if cached_data:
                    return cached_data
            except Exception as e:
                logger.debug(f"Cache get failed: {e}")
        
        # Try v3 endpoint first, fallback to v2
        data = await self._make_tracked_request(self.v3_endpoints['pairs'], use_v2_fallback=True)
        
        # Handle different response structures between v2 and v3
        if isinstance(data, dict):
            # v3 API returns {success: true, data: {data: [...], hasNextPage: false}}
            if data.get('success') and 'data' in data:
                pairs = data['data'].get('data', [])
            else:
                pairs = data.get('data', data.get('pairs', []))
        elif isinstance(data, list):
            # Direct list response (v2 style)
            pairs = data
        else:
            pairs = []
        
        if limit and pairs and isinstance(pairs, list):
            pairs = pairs[:limit]
        
        # Cache the results
        if self.enhanced_cache and pairs:
            try:
                await self.enhanced_cache.set_with_intelligent_ttl(cache_key, pairs, "raydium_pairs")
            except Exception as e:
                logger.debug(f"Cache set failed: {e}")
        
        return pairs if isinstance(pairs, list) else []
    
    async def get_token_pairs(self, token_address: str, search_limit: int = 100000) -> List[Dict]:
        """Get pairs for a specific token"""
        if token_address in self.excluded_addresses:
            return []
        
        # Check cache first
        if self.enhanced_cache:
            try:
                cached_data = await self.enhanced_cache.get_with_tracking(f"token_pairs_{token_address}", "raydium_token_pairs")
                if cached_data:
                    return cached_data
            except Exception as e:
                logger.debug(f"Cache get failed: {e}")
        
        pairs = await self.get_pairs(limit=search_limit)
        matching_pairs = []
        
        for pair in pairs:
            pair_str = json.dumps(pair).lower()
            if token_address.lower() in pair_str:
                matching_pairs.append(pair)
        
        # Cache the results
        if self.enhanced_cache:
            try:
                await self.enhanced_cache.set_with_intelligent_ttl(f"token_pairs_{token_address}", matching_pairs, "raydium_token_pairs")
            except Exception as e:
                logger.debug(f"Cache set failed: {e}")
                
        return matching_pairs
    
    async def get_volume_trending_pairs(self, min_volume_24h: float = 10000, limit: int = 50) -> List[Dict]:
        """Get trending pairs by volume"""
        pairs = await self.get_pairs(limit=100000)  # Search first 100k
        trending = [
            pair for pair in pairs 
            if pair.get('volume_24h', 0) >= min_volume_24h
        ]
        return sorted(trending, key=lambda x: x.get('volume_24h', 0), reverse=True)[:limit]
    
    async def get_pool_stats(self, token_address: str) -> Dict[str, Any]:
        """Get comprehensive pool statistics for a token"""
        # Search both pools and pairs
        pools_task = self.get_pools(limit=50000)
        pairs_task = self.get_token_pairs(token_address, search_limit=100000)
        
        pools, pairs = await asyncio.gather(pools_task, pairs_task)
        
        # Find matching pools
        matching_pools = []
        for pool in pools:
            pool_str = json.dumps(pool).lower()
            if token_address.lower() in pool_str:
                matching_pools.append(pool)
        
        if not matching_pools and not pairs:
            return {
                'found': False,
                'pool_count': 0,
                'pair_count': 0,
                'total_liquidity': 0,
                'total_volume_24h': 0,
                'avg_apy': 0,
                'quality_score': 0
            }
        
        # Calculate stats from pools
        pool_liquidity = sum(p.get('liquidity_locked', 0) for p in matching_pools)
        
        # Calculate stats from pairs (more comprehensive)
        pair_liquidity = sum(p.get('liquidity', 0) for p in pairs)
        pair_volume = sum(p.get('volume_24h', 0) for p in pairs)
        
        # APY from pairs
        apys = [p.get('apy', 0) for p in pairs if p.get('apy') and p.get('apy') != 0]
        avg_apy = sum(apys) / len(apys) if apys else 0
        
        # Calculate quality score
        total_liquidity = pool_liquidity + pair_liquidity
        quality_score = self._calculate_raydium_quality_score(
            total_liquidity, pair_volume, len(matching_pools) + len(pairs), avg_apy
        )
        
        return {
            'found': True,
            'pool_count': len(matching_pools),
            'pair_count': len(pairs),
            'total_liquidity': total_liquidity,
            'total_volume_24h': pair_volume,
            'avg_apy': avg_apy,
            'quality_score': quality_score,
            'pools': matching_pools[:2],  # Top 2 pools
            'pairs': pairs[:3],  # Top 3 pairs
            'top_pair': max(pairs, key=lambda x: x.get('volume_24h', 0)) if pairs else None,
            'dex_name': 'Raydium'
        }
    
    def _calculate_raydium_quality_score(self, liquidity: float, volume: float, 
                                       total_pools: int, avg_apy: float) -> float:
        """Calculate Raydium-specific quality score"""
        # Base score from liquidity (0-35 points)
        liquidity_score = min(35, liquidity / 1000)  # 1 point per $1k liquidity, max 35
        
        # Volume score (0-30 points)
        volume_score = min(30, volume / 200)  # 1 point per $200 volume, max 30
        
        # Pool/pair diversity score (0-20 points)
        diversity_score = min(20, total_pools * 3)  # 3 points per pool/pair, max 20
        
        # APY bonus (0-15 points)
        if avg_apy > 0:
            apy_score = min(15, avg_apy / 100 * 15)  # Scale APY to 0-15 points
        else:
            apy_score = 0
        
        return liquidity_score + volume_score + diversity_score + apy_score
    
    async def get_batch_token_analytics(self, token_addresses: List[str]) -> Dict[str, Dict[str, Any]]:
        """Get analytics for multiple tokens efficiently"""
        results = {}
        
        # Get pools and pairs once
        pools_task = self.get_pools(limit=50000)
        pairs_task = self.get_pairs(limit=100000)
        
        pools, pairs = await asyncio.gather(pools_task, pairs_task)
        
        for token_address in token_addresses:
            if token_address in self.excluded_addresses:
                continue
                
            # Find matching pools
            matching_pools = []
            for pool in pools:
                pool_str = json.dumps(pool).lower()
                if token_address.lower() in pool_str:
                    matching_pools.append(pool)
            
            # Find matching pairs
            matching_pairs = []
            for pair in pairs:
                pair_str = json.dumps(pair).lower()
                if token_address.lower() in pair_str:
                    matching_pairs.append(pair)
            
            # Calculate analytics
            if matching_pools or matching_pairs:
                pool_liquidity = sum(p.get('liquidity_locked', 0) for p in matching_pools)
                pair_liquidity = sum(p.get('liquidity', 0) for p in matching_pairs)
                pair_volume = sum(p.get('volume_24h', 0) for p in matching_pairs)
                
                apys = [p.get('apy', 0) for p in matching_pairs if p.get('apy') and p.get('apy') != 0]
                avg_apy = sum(apys) / len(apys) if apys else 0
                
                total_liquidity = pool_liquidity + pair_liquidity
                quality_score = self._calculate_raydium_quality_score(
                    total_liquidity, pair_volume, len(matching_pools) + len(matching_pairs), avg_apy
                )
                
                results[token_address] = {
                    'found': True,
                    'pool_count': len(matching_pools),
                    'pair_count': len(matching_pairs),
                    'total_liquidity': total_liquidity,
                    'total_volume_24h': pair_volume,
                    'avg_apy': avg_apy,
                    'quality_score': quality_score,
                    'dex_name': 'Raydium'
                }
            else:
                results[token_address] = {
                    'found': False,
                    'pool_count': 0,
                    'pair_count': 0,
                    'total_liquidity': 0,
                    'total_volume_24h': 0,
                    'avg_apy': 0,
                    'quality_score': 0,
                    'dex_name': 'Raydium'
                }
        
        return results
    
    async def get_high_apy_opportunities(self, min_apy: float = 50.0, min_liquidity: float = 10000) -> List[Dict]:
        """Get high APY yield opportunities"""
        pairs = await self.get_pairs(limit=50000)
        
        opportunities = []
        for pair in pairs:
            apy = pair.get('apy', 0)
            liquidity = pair.get('liquidity', 0)
            
            if apy >= min_apy and liquidity >= min_liquidity:
                opportunities.append({
                    'name': pair.get('name', 'Unknown'),
                    'apy': apy,
                    'liquidity': liquidity,
                    'volume_24h': pair.get('volume_24h', 0),
                    'pair_data': pair
                })
        
        return sorted(opportunities, key=lambda x: x['apy'], reverse=True)
    
    async def get_wsol_trending_pairs(self, limit: int = 50) -> List[Dict]:
        """Get trending WSOL-paired pools optimized for early gem detection"""
        # Enhanced strategy: Scan pages 3-12 to find emerging gems (skip the giants)
        all_pairs = []
        
        # Phase 1: Get emerging gems from mid-tier volume pages
        for page in range(3, 13):  # Pages 3-12 (emerging gems sweet spot)
            page_endpoint = f'/pools/info/list?poolType=all&poolSortField=volume24h&sortType=desc&page={page}&pageSize=50'
            try:
                data = await self._make_tracked_request(page_endpoint, use_v2_fallback=False)
                if isinstance(data, dict) and data.get('success') and 'data' in data:
                    page_pairs = data['data'].get('data', [])
                    all_pairs.extend(page_pairs)
                    if len(page_pairs) < 50:  # No more data available
                        break
                else:
                    break
            except Exception:
                break
        
        # Phase 2: Add some high-volume pairs for comparison (top 100)
        top_volume_endpoint = '/pools/info/list?poolType=all&poolSortField=volume24h&sortType=desc&page=1&pageSize=100'
        try:
            top_data = await self._make_tracked_request(top_volume_endpoint, use_v2_fallback=False)
            if isinstance(top_data, dict) and top_data.get('success') and 'data' in top_data:
                top_pairs = top_data['data'].get('data', [])
                all_pairs.extend(top_pairs)
        except Exception:
            pass
                
        pairs = all_pairs
        
        if not pairs:
            return []
        
        wsol_pairs = []
        excluded_count = 0
        
        for pair in pairs:
            # Extract token addresses from pair - handle both v2 and v3 structures
            # v3 uses mintA/mintB as objects with address field, v2 uses baseMint/quoteMint as strings
            mint_a = pair.get('mintA', pair.get('baseMint', ''))
            mint_b = pair.get('mintB', pair.get('quoteMint', ''))
            
            # Handle v3 structure where mints are objects
            if isinstance(mint_a, dict):
                mint_a = mint_a.get('address', '')
            if isinstance(mint_b, dict):
                mint_b = mint_b.get('address', '')
            
            # Get volume - v3 uses day.volume, v2 uses volume24h
            volume_24h = 0
            if 'day' in pair and isinstance(pair['day'], dict):
                volume_24h = pair['day'].get('volume', 0)
            else:
                volume_24h = pair.get('volume24h', pair.get('volume_24h', 0))
            
            # Get symbol names from v3 or v2 structure
            mint_a_symbol = 'Unknown'
            mint_b_symbol = 'Unknown'
            
            if isinstance(pair.get('mintA'), dict):
                mint_a_symbol = pair['mintA'].get('symbol', f'{mint_a[:8]}...')
            if isinstance(pair.get('mintB'), dict):
                mint_b_symbol = pair['mintB'].get('symbol', f'{mint_b[:8]}...')
            
            # Calculate early gem score for prioritization
            tvl = pair.get('tvl', 0)
            volume_tvl_ratio = volume_24h / tvl if tvl > 0 else 0
            
            # Early gem criteria:
            # - TVL between $1k-$500k (not too small to be fake, not too big to be mature)
            # - Volume/TVL ratio > 0.1 (10% daily turnover shows activity)
            # - Must be WSOL paired for easier trading
            is_early_gem_candidate = (1000 <= tvl <= 500000 and volume_tvl_ratio > 0.1)
            
            # Only include pairs where one side is WSOL and the other is not excluded
            if mint_a == self.wsol_address and mint_b and mint_b not in self.excluded_addresses:
                # WSOL-mint_b pair
                wsol_pairs.append({
                    'address': mint_b,
                    'symbol': mint_b_symbol,
                    'pool_address': pair.get('id', pair.get('ammId', '')),
                    'pair_name': f'WSOL/{mint_b_symbol}',
                    'tvl': tvl,
                    'volume_24h': volume_24h,
                    'volume_tvl_ratio': volume_tvl_ratio,
                    'price': pair.get('price', 0),
                    'fee_24h': 0,  # Need to calculate from v3 data
                    'apr_24h': 0,  # Need to calculate from v3 data
                    'liquidity': tvl,
                    'discovery_source': 'raydium_v3_emerging_gems',
                    'is_wsol_pair': True,
                    'is_early_gem_candidate': is_early_gem_candidate,
                    'early_gem_score': volume_tvl_ratio if is_early_gem_candidate else 0,
                    'pair_type': f'WSOL-{mint_b_symbol}',
                    'raw_pair_data': pair
                })
                
            elif mint_b == self.wsol_address and mint_a and mint_a not in self.excluded_addresses:
                # mint_a-WSOL pair
                wsol_pairs.append({
                    'address': mint_a,
                    'symbol': mint_a_symbol,
                    'pool_address': pair.get('id', pair.get('ammId', '')),
                    'pair_name': f'{mint_a_symbol}/WSOL',
                    'tvl': tvl,
                    'volume_24h': volume_24h,
                    'volume_tvl_ratio': volume_tvl_ratio,
                    'price': pair.get('price', 0),
                    'fee_24h': 0,  # Need to calculate from v3 data
                    'apr_24h': 0,  # Need to calculate from v3 data
                    'liquidity': tvl,
                    'discovery_source': 'raydium_v3_emerging_gems',
                    'is_wsol_pair': True,
                    'is_early_gem_candidate': is_early_gem_candidate,
                    'early_gem_score': volume_tvl_ratio if is_early_gem_candidate else 0,
                    'pair_type': f'{mint_a_symbol}-WSOL',
                    'raw_pair_data': pair
                })
            else:
                excluded_count += 1
        
        # Enhanced sorting: Prioritize early gems, then by volume
        early_gems = [pair for pair in wsol_pairs if pair.get('is_early_gem_candidate', False)]
        regular_pairs = [pair for pair in wsol_pairs if not pair.get('is_early_gem_candidate', False)]
        
        # Sort early gems by early_gem_score (volume/TVL ratio), regular pairs by volume  
        early_gems.sort(key=lambda x: x.get('early_gem_score', 0), reverse=True)
        regular_pairs.sort(key=lambda x: x.get('volume_24h', 0), reverse=True)
        
        # Combine: early gems first, then top regular pairs
        final_pairs = early_gems + regular_pairs
        
        logger.info(f"⚡ Raydium v3 enhanced filtering: Found {len(wsol_pairs)} WSOL pairs ({len(early_gems)} early gems), excluded {excluded_count} non-WSOL pairs")
        
        return final_pairs[:limit]
    
    async def close(self):
        """Close the connector"""
        if self.session:
            await self.session.close() 