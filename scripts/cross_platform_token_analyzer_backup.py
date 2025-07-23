#!/usr/bin/env python3
"""
Cross-Platform Token Analyzer - Proof of Concept

Correlates token data across DexScreener, Birdeye, and RugCheck to identify
high-conviction trading opportunities through multi-platform validation.

ENHANCED WITH INTELLIGENT CACHING FOR COST OPTIMIZATION
"""

import asyncio
import aiohttp
import json
import time
from datetime import datetime
from typing import Dict, List, Set, Tuple, Optional, Any
from collections import defaultdict
import os
import sys
import logging

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from api.birdeye_connector import BirdeyeAPI
from api.rugcheck_connector import RugCheckConnector
from core.cache_manager import CacheManager
from services.rate_limiter_service import RateLimiterService
from services.logger_setup import LoggerSetup
from services.enhanced_cache_manager import EnhancedPositionCacheManager
from core.config_manager import ConfigManager

class DexScreenerConnector:
    """Enhanced DexScreener API connector using all available endpoints"""
    
    def __init__(self, enhanced_cache: Optional[EnhancedPositionCacheManager] = None):
        self.base_url = "https://api.dexscreener.com"
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
    
    async def _make_tracked_request(self, endpoint: str) -> Optional[Dict]:
        """Make a tracked API request to DexScreener"""
        import time
        
        start_time = time.time()
        self.api_stats["total_calls"] += 1
        self.api_stats["endpoints_used"].add(endpoint)
        
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(f"{self.base_url}{endpoint}") as response:
                    response_time_ms = (time.time() - start_time) * 1000
                    self.api_stats["total_response_time_ms"] += response_time_ms
                    
                    if response.status == 200:
                        self.api_stats["successful_calls"] += 1
                        data = await response.json()
                        logging.info(f"🟢 DexScreener API call successful: {endpoint} ({response.status}) - {response_time_ms:.1f}ms")
                        return data
                    else:
                        self.api_stats["failed_calls"] += 1
                        logging.warning(f"🔴 DexScreener API call failed: {endpoint} ({response.status}) - {response_time_ms:.1f}ms")
                        return None
                        
        except Exception as e:
            response_time_ms = (time.time() - start_time) * 1000
            self.api_stats["total_response_time_ms"] += response_time_ms
            self.api_stats["failed_calls"] += 1
            logging.error(f"🔴 DexScreener API error: {endpoint} - {e} - {response_time_ms:.1f}ms")
            return None
        
    async def get_boosted_tokens(self) -> List[Dict]:
        """Get latest boosted tokens from DexScreener"""
        # Check cache first
        if self.enhanced_cache:
            cached_data = self.enhanced_cache.get_enhanced("cross_platform_trending", "dexscreener_boosted")
            if cached_data:
                return cached_data
        
        # Make tracked API request
        data = await self._make_tracked_request("/token-boosts/latest/v1")
        
        # Extract the list from the response
        tokens = data if isinstance(data, list) else []
        
        # Cache the result
        if tokens and self.enhanced_cache:
            self.enhanced_cache.set_enhanced("cross_platform_trending", "dexscreener_boosted", tokens)
        
        return tokens
    
    async def get_top_boosted_tokens(self) -> List[Dict]:
        """Get top boosted tokens from DexScreener"""
        # Check cache first
        if self.enhanced_cache:
            cached_data = self.enhanced_cache.get_enhanced("cross_platform_trending", "dexscreener_top_boosted")
            if cached_data:
                return cached_data
        
        # Make tracked API request
        data = await self._make_tracked_request("/token-boosts/top/v1")
        
        # Extract the list from the response
        tokens = data if isinstance(data, list) else []
        
        # Cache the result
        if tokens and self.enhanced_cache:
            self.enhanced_cache.set_enhanced("cross_platform_trending", "dexscreener_top_boosted", tokens)
        
        return tokens

    async def get_token_profiles(self) -> List[Dict]:
        """Get latest token profiles with rich metadata for fundamental analysis"""
        # Check cache first
        if self.enhanced_cache:
            cached_data = self.enhanced_cache.get_enhanced("cross_platform_trending", "dexscreener_profiles")
            if cached_data:
                return cached_data
        
        # Make tracked API request
        data = await self._make_tracked_request("/token-profiles/latest/v1")
        
        # Extract the list from the response
        profiles = data if isinstance(data, list) else []
        
        # Process and enhance profile data
        enhanced_profiles = []
        if profiles:
            for item in profiles:
                # Extract social links
                website = None
                twitter = None
                telegram = None
                
                for link in item.get("links", []):
                    link_type = link.get("type", "").lower()
                    url = link.get("url", "")
                    
                    if link_type == "twitter" or "twitter.com" in url or "x.com" in url:
                        twitter = url
                    elif link_type == "telegram" or "t.me" in url:
                        telegram = url
                    elif link.get("label", "").lower() == "website":
                        website = url
                
                # Calculate social score
                social_score = 0.0
                if website: social_score += 0.3
                if twitter: social_score += 0.4
                if telegram: social_score += 0.3
                
                # Calculate narrative strength based on description
                description = item.get("description", "")
                narrative_strength = min(len(description) / 500, 1.0)  # Normalize to 0-1
                
                enhanced_profile = {
                    'address': item.get("tokenAddress", ""),
                    'chain_id': item.get("chainId", ""),
                    'description': description,
                    'website': website,
                    'twitter': twitter,
                    'telegram': telegram,
                    'social_score': social_score,
                    'narrative_strength': narrative_strength,
                    'raw_data': item
                }
                enhanced_profiles.append(enhanced_profile)
        
        # Cache the result
        if enhanced_profiles and self.enhanced_cache:
            self.enhanced_cache.set_enhanced("cross_platform_trending", "dexscreener_profiles", enhanced_profiles)
        
        return enhanced_profiles

    async def get_batch_token_data(self, token_addresses: List[str], chain_id: str = "solana") -> List[Dict]:
        """Efficiently batch fetch token data (up to 30 tokens per request)"""
        if not token_addresses:
            return []
        
        # Split into batches of 30 (API limit)
        batches = [token_addresses[i:i+30] for i in range(0, len(token_addresses), 30)]
        all_data = []
        
        for batch_idx, batch in enumerate(batches):
            # Check cache for this batch
            batch_key = f"batch_{hash(tuple(sorted(batch)))}"
            if self.enhanced_cache:
                cached_data = self.enhanced_cache.get_enhanced("dexscreener_batch", batch_key)
                if cached_data:
                    all_data.extend(cached_data)
                    continue
            
            # Make API request for uncached batch
            addresses_str = ",".join(batch)
            endpoint = f"/tokens/v1/{chain_id}/{addresses_str}"
            data = await self._make_tracked_request(endpoint)
            
            # Extract the list from the response
            batch_data = data if isinstance(data, list) else []
            
            if batch_data:
                all_data.extend(batch_data)
                # Cache this batch
                if self.enhanced_cache:
                    self.enhanced_cache.set_enhanced("dexscreener_batch", batch_key, batch_data)
        
        logging.info(f"📊 Batch processed {len(token_addresses)} tokens in {len(batches)} requests")
        return all_data

    async def search_tokens_by_criteria(self, query: str) -> List[Dict]:
        """Search for tokens matching specific criteria for narrative-based discovery"""
        # Check cache first
        cache_key = f"search_{query.replace(' ', '_').lower()}"
        if self.enhanced_cache:
            cached_data = self.enhanced_cache.get_enhanced("dexscreener_search", cache_key)
            if cached_data:
                return cached_data
        
        # Make tracked API request
        endpoint = f"/latest/dex/search?q={query}"
        data = await self._make_tracked_request(endpoint)
        
        pairs = []
        if data and isinstance(data, dict) and "pairs" in data:
            pairs = data["pairs"]
        
        # Cache the result
        if pairs and self.enhanced_cache:
            self.enhanced_cache.set_enhanced("dexscreener_search", cache_key, pairs)
        
        logging.info(f"🔍 Search '{query}' found {len(pairs)} results")
        return pairs

    async def get_token_liquidity_analysis(self, token_address: str, chain_id: str = "solana") -> Optional[Dict]:
        """Analyze token liquidity across all DEXes"""
        # Check cache first
        if self.enhanced_cache:
            cached_data = self.enhanced_cache.get_enhanced("liquidity_analysis", token_address)
            if cached_data:
                return cached_data
        
        endpoint = f"/token-pairs/v1/{chain_id}/{token_address}"
        data = await self._make_tracked_request(endpoint)
        
        # Extract the list from the response
        pairs = data if isinstance(data, list) else []
        
        if not pairs:
            return None
        
        total_liquidity = 0.0
        liquidity_by_dex = {}
        best_pair = None
        best_liquidity = 0.0
        
        for pair in pairs:
            liquidity = pair.get("liquidity", {})
            pair_liquidity = liquidity.get("usd", 0.0)
            dex_id = pair.get("dexId", "unknown")
            
            total_liquidity += pair_liquidity
            liquidity_by_dex[dex_id] = liquidity_by_dex.get(dex_id, 0.0) + pair_liquidity
            
            if pair_liquidity > best_liquidity:
                best_liquidity = pair_liquidity
                best_pair = pair.get("pairAddress")
        
        # Find primary DEX
        primary_dex = max(liquidity_by_dex, key=liquidity_by_dex.get) if liquidity_by_dex else "unknown"
        
        analysis = {
            'total_liquidity_usd': total_liquidity,
            'pair_count': len(pairs),
            'primary_dex': primary_dex,
            'liquidity_distribution': liquidity_by_dex,
            'best_entry_pair': best_pair,
            'liquidity_quality_score': self._calculate_liquidity_quality_score(total_liquidity, len(pairs), primary_dex)
        }
        
        # Cache the result
        if self.enhanced_cache:
            self.enhanced_cache.set_enhanced("liquidity_analysis", token_address, analysis)
        
        return analysis

    def _calculate_liquidity_quality_score(self, total_liquidity: float, pair_count: int, primary_dex: str) -> float:
        """Calculate liquidity quality score (0-10)"""
        score = 0.0
        
        # Liquidity amount scoring (0-4 points)
        if total_liquidity >= 1000000:  # $1M+
            score += 4.0
        elif total_liquidity >= 500000:  # $500K+
            score += 3.0
        elif total_liquidity >= 100000:  # $100K+
            score += 2.0
        elif total_liquidity >= 50000:   # $50K+
            score += 1.0
        
        # Pair diversity scoring (0-3 points)
        if pair_count >= 5:
            score += 3.0
        elif pair_count >= 3:
            score += 2.0
        elif pair_count >= 2:
            score += 1.0
        
        # Primary DEX quality scoring (0-3 points)
        quality_dexes = ['raydium', 'orca', 'jupiter', 'meteora']
        if primary_dex.lower() in quality_dexes:
            score += 3.0
        elif primary_dex != "unknown":
            score += 1.0
        
        return min(score, 10.0)

    async def discover_narrative_tokens(self, narratives: List[str]) -> Dict[str, List[Dict]]:
        """Discover tokens by searching for trending narratives"""
        results = {}
        
        for narrative in narratives:
            tokens = await self.search_tokens_by_criteria(narrative)
            if tokens:
                # Filter and enhance results - tokens is the 'pairs' array from DexScreener
                enhanced_tokens = []
                for pair in tokens[:10]:  # Limit to top 10 per narrative
                    base_token = pair.get('baseToken', {})
                    if base_token.get('address'):
                        # Only include Solana tokens for our analysis
                        if pair.get('chainId') == 'solana':
                            enhanced_token = {
                                'address': base_token['address'],
                                'symbol': base_token.get('symbol', ''),
                                'name': base_token.get('name', ''),
                                'price_usd': float(pair.get('priceUsd', 0)),
                                'volume_24h': pair.get('volume', {}).get('h24', 0),
                                'liquidity_usd': pair.get('liquidity', {}).get('usd', 0),
                                'price_change_24h': pair.get('priceChange', {}).get('h24', 0),
                                'discovery_narrative': narrative,
                                'dex_id': pair.get('dexId', ''),
                                'pair_address': pair.get('pairAddress', ''),
                                'market_cap': pair.get('marketCap', 0),
                                'chain_id': pair.get('chainId', 'solana')
                            }
                            enhanced_tokens.append(enhanced_token)
                
                if enhanced_tokens:
                    results[narrative] = enhanced_tokens
                    logging.info(f"🎯 Found {len(enhanced_tokens)} Solana tokens for narrative '{narrative}'")
                else:
                    logging.info(f"🔍 No Solana tokens found for narrative '{narrative}' (found {len(tokens)} total)")
            else:
                logging.info(f"🔍 No tokens found for narrative '{narrative}'")
        
        return results

class BirdeyeConnector:
    """Connector for Birdeye API with enhanced caching"""
    
    def __init__(self, birdeye_api: BirdeyeAPI, enhanced_cache: Optional[EnhancedPositionCacheManager] = None):
        self.birdeye_api = birdeye_api
        self.enhanced_cache = enhanced_cache
        
    async def get_trending_tokens(self, limit: int = 20) -> List[Dict]:
        """Get trending tokens from Birdeye with caching"""
        # Check cache first
        if self.enhanced_cache:
            cached_data = self.enhanced_cache.get_enhanced("cross_platform_trending", "birdeye_trending", f"limit_{limit}")
            if cached_data:
                return cached_data
        
        try:
            # Use the existing Birdeye API method
            trending_addresses = await self.birdeye_api.get_trending_tokens()
            if not trending_addresses:
                return []
            
            # Get detailed data for trending tokens using batch API
            detailed_data = []
            if len(trending_addresses) > 0:
                # Use batch API to get token market data efficiently
                batch_data = await self.birdeye_api.get_token_market_data_multiple(trending_addresses[:limit])
                
                if batch_data and isinstance(batch_data, dict):
                    for address in trending_addresses[:limit]:
                        if address in batch_data:
                            token_data = batch_data[address]
                            if token_data:  # Ensure data is not None
                                token_data['address'] = address
                                detailed_data.append(token_data)
                        else:
                            # If no batch data, create minimal entry
                            detailed_data.append({'address': address})
            
            # Cache the result
            if self.enhanced_cache:
                self.enhanced_cache.set_enhanced("cross_platform_trending", "birdeye_trending", detailed_data, f"limit_{limit}")
            
            return detailed_data
            
        except Exception as e:
            logging.error(f"Error fetching Birdeye trending tokens: {e}")
            return []

    async def get_emerging_stars(self, limit: int = 20) -> List[Dict]:
        """
        Get emerging star tokens using Birdeye's /defi/v3/token/list with filters
        for up-and-coming tokens with high potential but not yet massive
        """
        # Check cache first
        cache_key = f"birdeye_emerging_stars_limit_{limit}"
        if self.enhanced_cache:
            cached_data = self.enhanced_cache.get_enhanced("cross_platform_trending", cache_key)
            if cached_data:
                return cached_data
        
        try:
            # Use the token list endpoint with emerging stars filters
            token_list_data = await self.birdeye_api.get_token_list(
                sort_by="volume_24h_usd",
                sort_type="desc",
                min_volume_24h_usd=1000000,    # $1M+ daily volume (real traction)
                max_market_cap=100000000,      # Under $100M market cap (not yet massive)
                min_holder=100,                # Decent community (100+ holders)
                min_trade_24h_count=1000,      # Active trading (1000+ trades/day)
                limit=limit
            )
            
            emerging_stars = []
            if token_list_data and token_list_data.get('success'):
                tokens_data = token_list_data.get('data', {})
                if isinstance(tokens_data, dict) and 'tokens' in tokens_data:
                    tokens = tokens_data['tokens']
                elif 'items' in tokens_data:
                    tokens = tokens_data['items']
                else:
                    tokens = []
                
                for token in tokens:
                    if isinstance(token, dict):
                        # Calculate volume-to-market-cap ratio for momentum analysis
                        volume_24h = token.get('volume_24h_usd', 0)
                        market_cap = token.get('market_cap', 1)  # Avoid division by zero
                        volume_to_mcap_ratio = volume_24h / market_cap if market_cap > 0 else 0
                        
                        # Enhanced token data with emerging star metrics
                        emerging_star = {
                            'address': token.get('address', ''),
                            'symbol': token.get('symbol', ''),
                            'name': token.get('name', ''),
                            'volume_24h_usd': volume_24h,
                            'market_cap': market_cap,
                            'holder_count': token.get('holder', 0),
                            'trade_24h_count': token.get('trade_24h_count', 0),
                            'price': token.get('price', 0),
                            'price_change_24h_percent': token.get('price_change_24h_percent', 0),
                            'liquidity': token.get('liquidity', 0),
                            'fdv': token.get('fdv', 0),
                            'last_trade_unix_time': token.get('last_trade_unix_time', 0),
                            
                            # Emerging star specific metrics
                            'volume_to_mcap_ratio': round(volume_to_mcap_ratio, 2),
                            'emerging_star_score': self._calculate_emerging_star_score(token, volume_to_mcap_ratio),
                            'momentum_tier': self._get_momentum_tier(volume_to_mcap_ratio),
                            'discovery_source': 'birdeye_emerging_stars',
                            
                            # Multi-timeframe volume data if available
                            'volume_1h_usd': token.get('volume_1h_usd', 0),
                            'volume_2h_usd': token.get('volume_2h_usd', 0),
                            'volume_4h_usd': token.get('volume_4h_usd', 0),
                            'volume_8h_usd': token.get('volume_8h_usd', 0),
                            
                            # Multi-timeframe price changes if available
                            'price_change_1h_percent': token.get('price_change_1h_percent', 0),
                            'price_change_2h_percent': token.get('price_change_2h_percent', 0),
                            'price_change_4h_percent': token.get('price_change_4h_percent', 0),
                            'price_change_8h_percent': token.get('price_change_8h_percent', 0),
                            
                            # Trading activity metrics
                            'trade_1h_count': token.get('trade_1h_count', 0),
                            'trade_2h_count': token.get('trade_2h_count', 0),
                            'trade_4h_count': token.get('trade_4h_count', 0),
                            'trade_8h_count': token.get('trade_8h_count', 0)
                        }
                        
                        # Only include tokens with valid addresses
                        if emerging_star['address']:
                            emerging_stars.append(emerging_star)
            
            # Cache the result
            if self.enhanced_cache:
                self.enhanced_cache.set_enhanced("cross_platform_trending", cache_key, emerging_stars)
            
            logging.info(f"🌟 Discovered {len(emerging_stars)} emerging star tokens from Birdeye")
            return emerging_stars
            
        except Exception as e:
            logging.error(f"Error fetching Birdeye emerging stars: {e}")
            return []
    
    def _calculate_emerging_star_score(self, token: Dict, volume_to_mcap_ratio: float) -> float:
        """Calculate emerging star score (0-100) based on multiple factors"""
        score = 0.0
        
        # Volume momentum scoring (0-30 points)
        volume_24h = token.get('volume_24h_usd', 0)
        if volume_24h >= 50000000:  # $50M+
            score += 30.0
        elif volume_24h >= 20000000:  # $20M+
            score += 25.0
        elif volume_24h >= 10000000:  # $10M+
            score += 20.0
        elif volume_24h >= 5000000:   # $5M+
            score += 15.0
        elif volume_24h >= 1000000:   # $1M+
            score += 10.0
        
        # Volume-to-market-cap ratio scoring (0-25 points)
        if volume_to_mcap_ratio >= 10.0:
            score += 25.0  # Extreme momentum
        elif volume_to_mcap_ratio >= 5.0:
            score += 20.0  # Very high momentum
        elif volume_to_mcap_ratio >= 2.0:
            score += 15.0  # High momentum
        elif volume_to_mcap_ratio >= 1.0:
            score += 10.0  # Good momentum
        elif volume_to_mcap_ratio >= 0.5:
            score += 5.0   # Some momentum
        
        # Price momentum scoring (0-20 points)
        price_change_24h = token.get('price_change_24h_percent', 0)
        if price_change_24h >= 100:    # 100%+ gain
            score += 20.0
        elif price_change_24h >= 50:   # 50%+ gain
            score += 15.0
        elif price_change_24h >= 20:   # 20%+ gain
            score += 10.0
        elif price_change_24h >= 10:   # 10%+ gain
            score += 5.0
        
        # Community strength scoring (0-15 points)
        holder_count = token.get('holder', 0)
        if holder_count >= 10000:
            score += 15.0
        elif holder_count >= 5000:
            score += 12.0
        elif holder_count >= 1000:
            score += 8.0
        elif holder_count >= 500:
            score += 5.0
        elif holder_count >= 100:
            score += 2.0
        
        # Trading activity scoring (0-10 points)
        trade_count = token.get('trade_24h_count', 0)
        if trade_count >= 10000:
            score += 10.0
        elif trade_count >= 5000:
            score += 8.0
        elif trade_count >= 2000:
            score += 6.0
        elif trade_count >= 1000:
            score += 4.0
        
        return min(100.0, round(score, 1))
    
    def _get_momentum_tier(self, volume_to_mcap_ratio: float) -> str:
        """Classify momentum tier based on volume-to-market-cap ratio"""
        if volume_to_mcap_ratio >= 100.0:
            return "EXTREME_MOMENTUM"      # Potential moonshot candidates
        elif volume_to_mcap_ratio >= 10.0:
            return "VERY_HIGH_MOMENTUM"    # Strong breakout potential
        elif volume_to_mcap_ratio >= 5.0:
            return "HIGH_MOMENTUM"         # Good momentum plays
        elif volume_to_mcap_ratio >= 2.0:
            return "MEDIUM_MOMENTUM"       # Steady growth
        elif volume_to_mcap_ratio >= 1.0:
            return "LOW_MOMENTUM"          # Some interest
        else:
            return "MINIMAL_MOMENTUM"      # Established/stable
    
    async def get_token_price_volume(self, token_addresses: List[str]) -> Dict[str, Dict]:
        """Get price and volume data for multiple tokens with caching"""
        if not token_addresses:
            return {}
        
        # Check cache for each token
        cached_results = {}
        uncached_addresses = []
        
        if self.enhanced_cache:
            for address in token_addresses:
                cached_data = self.enhanced_cache.get_enhanced("multi_price", address)
                if cached_data:
                    cached_results[address] = cached_data
                else:
                    uncached_addresses.append(address)
        else:
            uncached_addresses = token_addresses
        
        # Fetch uncached data using batch API
        if uncached_addresses:
            try:
                batch_data = await self.birdeye_api.get_multi_price(uncached_addresses)
                
                # Cache individual results
                if self.enhanced_cache and batch_data:
                    for address, data in batch_data.items():
                        # Only cache and store non-None data
                        if data is not None:
                            self.enhanced_cache.set_enhanced("multi_price", address, data)
                            cached_results[address] = data
                        else:
                            # Log when we get None data but don't cache it
                            logging.debug(f"Received None data for token {address} from multi_price API")
                
            except Exception as e:
                logging.error(f"Error fetching price/volume data: {e}")
        
        return cached_results
    
    async def close(self):
        """Close the Birdeye API connection"""
        if self.birdeye_api:
            await self.birdeye_api.close()

class CrossPlatformAnalyzer:
    """Main analyzer for cross-platform token correlation with enhanced caching"""
    
    def __init__(self, config: Optional[Dict] = None, logger: Optional[logging.Logger] = None):
        # Initialize configuration
        self.config_manager = ConfigManager()
        self.config = config or self.config_manager.get_config()
        
        # Initialize logging
        if logger:
            self.logger = logger
        else:
            self.logger_setup = LoggerSetup('CrossPlatformAnalyzer')
            self.logger = self.logger_setup.logger
        
        # Initialize core services with shared caching
        self.base_cache = CacheManager()
        self.enhanced_cache = EnhancedPositionCacheManager(self.base_cache, self.logger)
        self.rate_limiter = RateLimiterService()
        
        # Initialize APIs with shared services
        birdeye_config = self.config.get('BIRDEYE_API', {})
        self.birdeye_api = BirdeyeAPI(
            config=birdeye_config,
            logger=self.logger,
            cache_manager=self.base_cache,
            rate_limiter=self.rate_limiter
        )
        
        # Initialize connectors with enhanced caching
        self.dexscreener = DexScreenerConnector(self.enhanced_cache)
        self.birdeye = BirdeyeConnector(self.birdeye_api, self.enhanced_cache)
        self.rugcheck = RugCheckConnector()
        
        self.logger.info("🚀 Cross-Platform Analyzer initialized with enhanced caching")
    
    async def collect_all_data(self) -> Dict[str, List[Dict]]:
        """Collect data from all platforms in parallel with enhanced DexScreener capabilities"""
        self.logger.info("Starting enhanced parallel data collection from all platforms...")
        
        # Create tasks for parallel execution
        tasks = []
        
        # Enhanced DexScreener tasks
        tasks.append(('dexscreener_boosted', self.dexscreener.get_boosted_tokens()))
        tasks.append(('dexscreener_top', self.dexscreener.get_top_boosted_tokens()))
        tasks.append(('dexscreener_profiles', self.dexscreener.get_token_profiles()))
        
        # Narrative-based discovery
        trending_narratives = ["AI", "agent", "pump", "meme", "dog", "cat", "pepe", "gaming", "DeFi"]
        tasks.append(('dexscreener_narratives', self.dexscreener.discover_narrative_tokens(trending_narratives)))
        
        # RugCheck task
        tasks.append(('rugcheck_trending', self._get_rugcheck_trending()))
        
        # Birdeye task
        tasks.append(('birdeye_trending', self.birdeye.get_trending_tokens()))
        tasks.append(('birdeye_emerging_stars', self.birdeye.get_emerging_stars()))
        
        # Execute all tasks in parallel
        results = {}
        task_names = [name for name, _ in tasks]
        task_coroutines = [coro for _, coro in tasks]
        
        completed = await asyncio.gather(*task_coroutines, return_exceptions=True)
        
        for name, result in zip(task_names, completed):
            if isinstance(result, Exception):
                self.logger.error(f"Error in {name}: {result}")
                results[name] = []
            else:
                results[name] = result if result else []
                
        # Log enhanced collection results
        self.logger.info(f"📊 Enhanced data collection completed:")
        self.logger.info(f"  🚀 DexScreener boosted: {len(results.get('dexscreener_boosted', []))}")
        self.logger.info(f"  🏆 DexScreener top: {len(results.get('dexscreener_top', []))}")
        self.logger.info(f"  📋 DexScreener profiles: {len(results.get('dexscreener_profiles', []))}")
        
        # Log narrative discovery results
        narrative_results = results.get('dexscreener_narratives', {})
        if narrative_results:
            total_narrative_tokens = sum(len(tokens) for tokens in narrative_results.values())
            self.logger.info(f"  🎯 Narrative discovery: {total_narrative_tokens} tokens across {len(narrative_results)} narratives")
            for narrative, tokens in narrative_results.items():
                self.logger.info(f"    • {narrative}: {len(tokens)} tokens")
        
        self.logger.info(f"  ✅ RugCheck trending: {len(results.get('rugcheck_trending', []))}")
        self.logger.info(f"  📈 Birdeye trending: {len(results.get('birdeye_trending', []))}")
        self.logger.info(f"  🌟 Birdeye emerging stars: {len(results.get('birdeye_emerging_stars', []))}")
                
        return results
    
    async def _get_rugcheck_trending(self) -> List[Dict]:
        """Get trending tokens from RugCheck with caching using the RugCheck connector"""
        # Check cache first
        if self.enhanced_cache:
            cached_data = self.enhanced_cache.get_enhanced("cross_platform_trending", "rugcheck_trending")
            if cached_data:
                return cached_data
        
        try:
            # Use the RugCheck connector which has API tracking
            data = await self.rugcheck.get_trending_tokens()
            
            # Cache the result
            if data and self.enhanced_cache:
                self.enhanced_cache.set_enhanced("cross_platform_trending", "rugcheck_trending", data)
            
            self.logger.info(f"Fetched {len(data)} trending tokens from RugCheck")
            return data
            
        except Exception as e:
            self.logger.error(f"Error fetching RugCheck data: {e}")
            return []
    
    def normalize_token_data(self, platform_data: Dict[str, List[Dict]]) -> Dict[str, Dict]:
        """Normalize token data across platforms with enhanced DexScreener data"""
        normalized = defaultdict(lambda: {'platforms': set(), 'data': {}})
        
        # Create profile lookup for efficient access
        profile_lookup = {}
        for profile in platform_data.get('dexscreener_profiles', []):
            addr = profile.get('address', '')
            if addr:
                profile_lookup[addr] = profile
        
        # Process DexScreener boosted tokens
        for token in platform_data.get('dexscreener_boosted', []):
            addr = token.get('tokenAddress', '')  # Keep original case for Solana addresses
            if addr:
                normalized[addr]['platforms'].add('dexscreener')
                
                # Enhanced boost analysis according to DexScreener documentation
                boost_amount = token.get('amount', 0)
                boost_total = token.get('totalAmount', 0)
                
                # Calculate boost metrics
                boost_consumption = self._calculate_boost_consumption(token)
                is_golden_ticker = boost_amount >= 500  # Golden Ticker threshold
                boost_intensity = self._calculate_boost_intensity(boost_amount, boost_total)
                
                normalized[addr]['data']['dexscreener'] = {
                    'boost_amount': boost_amount,
                    'boost_total': boost_total,
                    'boost_consumption': boost_consumption,
                    'is_golden_ticker': is_golden_ticker,
                    'boost_intensity': boost_intensity,
                    'boost_tier': self._get_boost_tier(boost_amount),
                    'trending_score_multiplier': self._calculate_trending_multiplier(boost_amount),
                    'chain': token.get('chainId', 'unknown'),
                    'description': token.get('description', ''),
                    'links': token.get('links', [])
                }
                
                # Add profile data if available
                if addr in profile_lookup:
                    profile = profile_lookup[addr]
                    normalized[addr]['data']['dexscreener']['profile'] = {
                        'social_score': profile.get('social_score', 0),
                        'narrative_strength': profile.get('narrative_strength', 0),
                        'website': profile.get('website'),
                        'twitter': profile.get('twitter'),
                        'telegram': profile.get('telegram'),
                        'description_enhanced': profile.get('description', '')
                    }
                
                # Register token for enhanced caching
                self.enhanced_cache.register_tracked_token(addr)
        
        # Process DexScreener top boosted tokens
        for token in platform_data.get('dexscreener_top', []):
            addr = token.get('tokenAddress', '')
            if addr:
                if addr not in normalized:
                    normalized[addr]['platforms'].add('dexscreener')
                    normalized[addr]['data']['dexscreener'] = {}
                
                # Update with top boost data
                normalized[addr]['data']['dexscreener'].update({
                    'top_boost_amount': token.get('amount', 0),
                    'top_boost_total': token.get('totalAmount', 0),
                    'top_boost_consumption': self._calculate_boost_consumption(token),
                    'is_top_boosted': True
                })
                
                # Add profile data if available and not already added
                if addr in profile_lookup and 'profile' not in normalized[addr]['data']['dexscreener']:
                    profile = profile_lookup[addr]
                    normalized[addr]['data']['dexscreener']['profile'] = {
                        'social_score': profile.get('social_score', 0),
                        'narrative_strength': profile.get('narrative_strength', 0),
                        'website': profile.get('website'),
                        'twitter': profile.get('twitter'),
                        'telegram': profile.get('telegram'),
                        'description_enhanced': profile.get('description', '')
                    }
                
                self.enhanced_cache.register_tracked_token(addr)
        
        # Process narrative discovery tokens
        narrative_data = platform_data.get('dexscreener_narratives', {})
        if isinstance(narrative_data, dict):
            for narrative, tokens in narrative_data.items():
                for token in tokens:
                    addr = token.get('address', '')
                    if addr:
                        if addr not in normalized:
                            normalized[addr]['platforms'].add('dexscreener_narrative')
                            normalized[addr]['data']['dexscreener_narrative'] = {}
                        
                        # Add narrative discovery data
                        if 'narratives' not in normalized[addr]['data']:
                            normalized[addr]['data']['narratives'] = []
                        
                        normalized[addr]['data']['narratives'].append({
                            'narrative': narrative,
                            'symbol': token.get('symbol', ''),
                            'name': token.get('name', ''),
                            'price_usd': token.get('price_usd', 0),
                            'volume_24h': token.get('volume_24h', 0),
                            'liquidity_usd': token.get('liquidity_usd', 0),
                            'price_change_24h': token.get('price_change_24h', 0),
                            'dex_id': token.get('dex_id', ''),
                            'market_cap': token.get('market_cap', 0)
                        })
                        
                        # Add narrative score
                        if 'narrative_score' not in normalized[addr]['data']:
                            normalized[addr]['data']['narrative_score'] = 0
                        normalized[addr]['data']['narrative_score'] += 1  # +1 for each narrative match
                        
                        self.enhanced_cache.register_tracked_token(addr)
        
        # Process RugCheck trending tokens
        for token in platform_data.get('rugcheck_trending', []):
            addr = token.get('mint', '')  # Keep original case for Solana addresses
            if addr:
                normalized[addr]['platforms'].add('rugcheck')
                normalized[addr]['data']['rugcheck'] = {
                    'vote_count': token.get('vote_count', 0),
                    'up_count': token.get('up_count', 0),
                    'sentiment_score': self._calculate_sentiment(token)
                }
                
                # Register token for enhanced caching
                self.enhanced_cache.register_tracked_token(addr)
        
        # Process Birdeye trending tokens
        for token in platform_data.get('birdeye_trending', []):
            addr = token.get('address', '')  # Keep original case for Solana addresses
            if addr:
                normalized[addr]['platforms'].add('birdeye')
                normalized[addr]['data']['birdeye'] = {
                    'volume_24h_usd': token.get('v24hUSD', 0),
                    'price_change_24h': token.get('v24hChangePercent', 0),
                    'liquidity': token.get('liquidity', 0),
                    'market_cap': token.get('mc', 0),
                    'symbol': token.get('symbol', ''),
                    'name': token.get('name', ''),
                    'last_trade_time': token.get('lastTradeUnixTime', 0)
                }
                
                # Register token for enhanced caching
                self.enhanced_cache.register_tracked_token(addr)
        
        return dict(normalized)
    
    def _calculate_boost_consumption(self, token: Dict) -> float:
        """Calculate boost consumption rate"""
        total = token.get('totalAmount', 0)
        current = token.get('amount', 0)
        if total > 0:
            return (total - current) / total
        return 0.0
    
    def _calculate_boost_intensity(self, boost_amount: int, boost_total: int) -> str:
        """Calculate boost intensity based on DexScreener documentation"""
        if boost_amount >= 500:
            return "GOLDEN_TICKER"  # Ultimate flex - golden color
        elif boost_amount >= 100:
            return "MEGA_BOOST"     # Very high visibility
        elif boost_amount >= 50:
            return "HIGH_BOOST"     # High visibility
        elif boost_amount >= 20:
            return "MEDIUM_BOOST"   # Moderate visibility
        elif boost_amount >= 5:
            return "LOW_BOOST"      # Some visibility
        else:
            return "MINIMAL_BOOST"  # Minimal visibility
    
    def _get_boost_tier(self, boost_amount: int) -> str:
        """Get boost tier classification"""
        if boost_amount >= 500:
            return "GOLDEN"
        elif boost_amount >= 100:
            return "PLATINUM"
        elif boost_amount >= 50:
            return "GOLD"
        elif boost_amount >= 20:
            return "SILVER"
        elif boost_amount >= 5:
            return "BRONZE"
        else:
            return "BASIC"
    
    def _calculate_trending_multiplier(self, boost_amount: int) -> float:
        """Calculate trending score multiplier based on boost amount"""
        # According to docs: Boosts apply a multiplier to existing trending score
        if boost_amount >= 500:
            return 5.0   # Golden Ticker gets maximum multiplier
        elif boost_amount >= 100:
            return 3.5   # Very high multiplier
        elif boost_amount >= 50:
            return 2.5   # High multiplier
        elif boost_amount >= 20:
            return 1.8   # Medium multiplier
        elif boost_amount >= 5:
            return 1.3   # Low multiplier
        else:
            return 1.1   # Minimal multiplier
    
    def _calculate_sentiment(self, token: Dict) -> float:
        """Calculate sentiment score from votes"""
        total_votes = token.get('vote_count', 0)
        up_votes = token.get('up_count', 0)
        if total_votes > 0:
            return up_votes / total_votes
        return 0.0
    
    def analyze_correlations(self, normalized_data: Dict[str, Dict]) -> Dict[str, Any]:
        """Analyze cross-platform correlations"""
        correlations = {
            'total_tokens': len(normalized_data),
            'platform_distribution': defaultdict(int),
            'all_tokens': {},  # ADD: All tokens with scores and metadata
            'multi_platform_tokens': [],
            'correlation_matrix': defaultdict(lambda: defaultdict(int)),
            'high_conviction_tokens': [],
            'boost_analysis': {
                'golden_ticker_count': 0,
                'boost_distribution': {'GOLDEN': 0, 'PLATINUM': 0, 'GOLD': 0, 'SILVER': 0, 'BRONZE': 0, 'BASIC': 0},
                'average_boost_amount': 0,
                'total_boost_investment': 0
            }
        }
        
        # Track boost statistics
        total_boost_amount = 0
        boost_count = 0
        
        # Analyze platform distribution and build all_tokens
        for token_addr, token_data in normalized_data.items():
            platforms = token_data['platforms']
            correlations['platform_distribution'][len(platforms)] += 1
            
            # Calculate score for this token
            token_score = self._calculate_token_score(token_data)
            
            # ADD: Build all_tokens structure with complete token data
            token_info = {
                'address': token_addr,
                'platforms': list(platforms),
                'score': token_score,
                'symbol': 'Unknown',  # Default, will be updated from platform data
                'name': '',
                'price': 0,
                'volume_24h': 0,
                'market_cap': 0,
                'liquidity': 0,
                'price_change_24h': 0
            }
            
            # Enhanced symbol/name extraction with priority order: Birdeye > Narratives > DexScreener
            symbol_found = False
            
            # Priority 1: Extract symbol/name from Birdeye data (most reliable)
            if 'birdeye' in token_data['data']:
                be_data = token_data['data']['birdeye']
                be_symbol = be_data.get('symbol', '').strip()
                be_name = be_data.get('name', '').strip()
                
                if be_symbol and be_symbol != 'Unknown':
                    token_info['symbol'] = be_symbol
                    symbol_found = True
                if be_name:
                    token_info['name'] = be_name
                    
                token_info['price'] = be_data.get('price', 0)
                token_info['volume_24h'] = be_data.get('volume_24h_usd', 0)
                token_info['market_cap'] = be_data.get('market_cap', 0)
                token_info['liquidity'] = be_data.get('liquidity', 0)
                token_info['price_change_24h'] = be_data.get('price_change_24h', 0)
            
            # Priority 2: Extract from narrative data if symbol not found or is Unknown
            if 'narratives' in token_data['data'] and token_data['data']['narratives']:
                narrative = token_data['data']['narratives'][0]  # Use first narrative
                narrative_symbol = narrative.get('symbol', '').strip()
                narrative_name = narrative.get('name', '').strip()
                
                if not symbol_found and narrative_symbol and narrative_symbol != 'Unknown':
                    token_info['symbol'] = narrative_symbol
                    symbol_found = True
                if not token_info['name'] and narrative_name:
                    token_info['name'] = narrative_name
                if token_info['price'] == 0:
                    token_info['price'] = narrative.get('price_usd', 0)
                if token_info['volume_24h'] == 0:
                    token_info['volume_24h'] = narrative.get('volume_24h', 0)
                if token_info['market_cap'] == 0:
                    token_info['market_cap'] = narrative.get('market_cap', 0)
                if token_info['liquidity'] == 0:
                    token_info['liquidity'] = narrative.get('liquidity_usd', 0)
                if token_info['price_change_24h'] == 0:
                    token_info['price_change_24h'] = narrative.get('price_change_24h', 0)
            
            # Priority 3: Try to extract from DexScreener data if still no symbol
            if not symbol_found and 'dexscreener' in token_data['data']:
                ds_data = token_data['data']['dexscreener']
                # DexScreener doesn't directly provide symbol, but might have it in description or links
                description = ds_data.get('description', '')
                if description and len(description) > 0:
                    # Try to extract symbol from description (basic heuristic)
                    words = description.split()
                    for word in words:
                        # Look for potential symbols (uppercase, 2-10 chars, alphanumeric)
                        if word.isupper() and 2 <= len(word) <= 10 and word.isalnum():
                            token_info['symbol'] = word
                            symbol_found = True
                            break
            
            # Log symbol extraction for debugging
            if self.logger:
                if symbol_found and token_info['symbol'] != 'Unknown':
                    self.logger.debug(f"🏷️ Extracted symbol '{token_info['symbol']}' for {token_addr[:8]}...")
                else:
                    self.logger.debug(f"⚠️ No symbol found for {token_addr[:8]}..., keeping as 'Unknown'")
            
            # Store in all_tokens
            correlations['all_tokens'][token_addr] = token_info
            
            # Analyze DexScreener boost data
            if 'dexscreener' in token_data['data']:
                ds_data = token_data['data']['dexscreener']
                
                # Golden Ticker tracking
                if ds_data.get('is_golden_ticker', False):
                    correlations['boost_analysis']['golden_ticker_count'] += 1
                
                # Boost tier distribution
                boost_tier = ds_data.get('boost_tier', 'BASIC')
                if boost_tier in correlations['boost_analysis']['boost_distribution']:
                    correlations['boost_analysis']['boost_distribution'][boost_tier] += 1
                
                # Boost amount tracking
                boost_amount = ds_data.get('boost_amount', 0)
                boost_total = ds_data.get('boost_total', 0)
                if boost_amount > 0:
                    total_boost_amount += boost_amount
                    boost_count += 1
                    correlations['boost_analysis']['total_boost_investment'] += boost_total
            
            # Track multi-platform tokens
            if len(platforms) > 1:
                correlations['multi_platform_tokens'].append({
                    'address': token_addr,
                    'platforms': list(platforms),
                    'score': token_score,
                    'symbol': token_info['symbol'],  # Include extracted symbol
                    'name': token_info['name'],      # Include extracted name
                    'price': token_info['price'],
                    'volume_24h': token_info['volume_24h'],
                    'market_cap': token_info['market_cap'],
                    'liquidity': token_info['liquidity']
                })
            
            # Build correlation matrix
            for p1 in platforms:
                for p2 in platforms:
                    if p1 != p2:
                        correlations['correlation_matrix'][p1][p2] += 1
        
        # Calculate average boost amount
        if boost_count > 0:
            correlations['boost_analysis']['average_boost_amount'] = total_boost_amount / boost_count
        
        # Sort multi-platform tokens by score
        correlations['multi_platform_tokens'].sort(key=lambda x: x['score'], reverse=True)
        
        # Identify high conviction tokens (present on 2+ platforms with good metrics)
        for token in correlations['multi_platform_tokens']:
            if token['score'] >= 70.0:  # Updated for 0-100 scale
                correlations['high_conviction_tokens'].append({
                    'address': token['address'],
                    'platforms': token['platforms'],
                    'score': token['score'],
                    'symbol': token['symbol'],  # Include symbol
                    'name': token['name'],      # Include name
                    'price': token['price'],
                    'volume_24h': token['volume_24h'],
                    'market_cap': token['market_cap'],
                    'liquidity': token['liquidity']
                })
        
        return correlations
    
    def _calculate_token_score(self, token_data: Dict) -> float:
        """Calculate enhanced token score based on multi-platform signals using 0-100 scale"""
        score = 0.0
        platforms = len(token_data['platforms'])
        
        # Platform presence score (1-4 platforms) - Base: 0-20 points
        score += platforms * 5.0  # 1 platform=5, 2=10, 3=15, 4=20
        
        # Enhanced DexScreener analysis - Max: 40 points
        if 'dexscreener' in token_data['data']:
            ds_data = token_data['data']['dexscreener']
            boost_amount = ds_data.get('boost_amount', 0)
            boost_total = ds_data.get('boost_total', 0)
            consumption = ds_data.get('boost_consumption', 0)
            is_golden_ticker = ds_data.get('is_golden_ticker', False)
            boost_intensity = ds_data.get('boost_intensity', 'MINIMAL_BOOST')
            trending_multiplier = ds_data.get('trending_score_multiplier', 1.0)
            
            # Golden Ticker bonus (ultimate signal) - 15 points
            if is_golden_ticker:
                score += 15.0  # Premium signal
            
            # Boost intensity scoring based on visibility impact - 0-12 points
            boost_intensity_scores = {
                'GOLDEN_TICKER': 12.0,   # Already counted above, but ensure consistency
                'MEGA_BOOST': 10.0,      # Very high visibility
                'HIGH_BOOST': 8.0,       # High visibility  
                'MEDIUM_BOOST': 6.0,     # Moderate visibility
                'LOW_BOOST': 4.0,        # Some visibility
                'MINIMAL_BOOST': 2.0     # Minimal visibility
            }
            
            if not is_golden_ticker:  # Avoid double counting
                score += boost_intensity_scores.get(boost_intensity, 0)
            
            # Trending score multiplier impact - 0-8 points
            if trending_multiplier > 2.0:
                score += 8.0  # High multiplier impact
            elif trending_multiplier > 1.5:
                score += 5.0  # Medium multiplier impact
            elif trending_multiplier > 1.1:
                score += 2.0  # Low multiplier impact
            
            # Boost consumption analysis (active vs spent boosts) - 0-6 points
            if consumption > 0.7:  # High consumption = sustained interest
                score += 6.0
            elif consumption > 0.4:
                score += 4.0
            elif consumption > 0.1:
                score += 2.0
            
            # Investment commitment scoring (total boost amount) - 0-8 points
            if boost_total >= 1000:  # Very high investment
                score += 8.0
            elif boost_total >= 500:  # High investment
                score += 6.0
            elif boost_total >= 100:  # Medium investment
                score += 4.0
            elif boost_total >= 50:   # Low investment
                score += 2.0
            
            # Top boosted bonus - 3 points
            if ds_data.get('is_top_boosted'):
                score += 3.0
            
            # Social and fundamental signals from profiles - 0-8 points
            profile = ds_data.get('profile', {})
            if profile:
                # Social presence scoring (0-5 points)
                social_score = profile.get('social_score', 0)
                score += social_score * 5.0  # Scale to 0-5 points
                
                # Narrative strength scoring (0-3 points)
                narrative_strength = profile.get('narrative_strength', 0)
                score += narrative_strength * 3.0
                
                # Complete social presence bonus - 2 points
                if (profile.get('website') and profile.get('twitter') and 
                    profile.get('telegram')):
                    score += 2.0  # Complete social suite bonus
            
            # Liquidity quality scoring - 0-5 points
            liquidity_analysis = ds_data.get('liquidity_analysis', {})
            if liquidity_analysis:
                liquidity_quality_score = liquidity_analysis.get('liquidity_quality_score', 0)
                score += (liquidity_quality_score / 10) * 5.0  # Scale to 0-5 points
        
        # RugCheck community sentiment - Max: 10 points
        if 'rugcheck' in token_data['data']:
            rc_data = token_data['data']['rugcheck']
            sentiment = rc_data.get('sentiment_score', 0)
            
            if sentiment >= 0.8:
                score += 10.0
            elif sentiment >= 0.6:
                score += 6.0
            elif sentiment >= 0.4:
                score += 3.0
        
        # Birdeye trading metrics - Max: 20 points
        if 'birdeye' in token_data['data']:
            be_data = token_data['data']['birdeye']
            volume_24h = be_data.get('volume_24h_usd', 0)
            price_change = be_data.get('price_change_24h', 0)
            liquidity = be_data.get('liquidity', 0)
            
            # Volume scoring - 0-8 points
            if volume_24h >= 1000000:  # $1M+
                score += 8.0
            elif volume_24h >= 500000:  # $500k+
                score += 6.0
            elif volume_24h >= 100000:  # $100k+
                score += 4.0
            elif volume_24h >= 50000:   # $50k+
                score += 2.0
            
            # Price momentum scoring - 0-8 points
            if price_change >= 50:  # 50%+ gain
                score += 8.0
            elif price_change >= 20:  # 20%+ gain
                score += 5.0
            elif price_change >= 10:  # 10%+ gain
                score += 3.0
            elif price_change >= 5:   # 5%+ gain
                score += 1.0
            
            # Liquidity scoring - 0-4 points
            if liquidity >= 500000:  # $500k+
                score += 4.0
            elif liquidity >= 100000:  # $100k+
                score += 2.0
        
        # Narrative discovery scoring - Max: 10 points
        narrative_score = token_data['data'].get('narrative_score', 0)
        narratives = token_data['data'].get('narratives', [])
        
        if narrative_score > 0:
            # Multiple narrative bonus (trending across multiple themes)
            if narrative_score >= 3:
                score += 8.0  # Very strong narrative presence
            elif narrative_score >= 2:
                score += 5.0  # Strong narrative presence
            else:
                score += 3.0  # Single narrative presence
            
            # High-value narrative bonus - 2 points
            high_value_narratives = ['AI', 'gaming', 'DeFi', 'RWA']
            for narrative_data in narratives:
                if narrative_data.get('narrative') in high_value_narratives:
                    score += 2.0
                    break  # Only count once
        
        # Ensure score is within 0-100 range and round to 1 decimal
        final_score = max(0.0, min(100.0, score))
        return round(final_score, 1)
    
    async def _enhance_with_birdeye_data(self, normalized_data: Dict[str, Dict]) -> None:
        """Enhance tokens with additional Birdeye data using batch APIs"""
        if not normalized_data or not isinstance(normalized_data, dict):
            self.logger.warning("No normalized data provided for Birdeye enhancement")
            return
            
        token_addresses = list(normalized_data.keys())
        
        if not token_addresses:
            self.logger.debug("No token addresses to enhance with Birdeye data")
            return
        
        try:
            # Get price/volume data for all tokens in batches
            batch_size = 20  # Birdeye API limit
            for i in range(0, len(token_addresses), batch_size):
                batch_addresses = token_addresses[i:i + batch_size]
                
                if not batch_addresses:
                    continue
                
                self.logger.debug(f"Processing batch {i//batch_size + 1}: {len(batch_addresses)} addresses")
                
                # Get price and volume data
                try:
                    price_volume_data = await self.birdeye.get_token_price_volume(batch_addresses)
                except Exception as batch_error:
                    self.logger.error(f"Error getting price/volume data for batch: {batch_error}")
                    continue
                
                # Validate price_volume_data before processing
                if not price_volume_data or not isinstance(price_volume_data, dict):
                    self.logger.warning(f"Invalid price_volume_data received: {type(price_volume_data)}")
                    continue
                
                # Update normalized data with enhanced information
                for address in batch_addresses:
                    if not address or address not in normalized_data:
                        continue
                        
                    if address in price_volume_data:
                        enhanced_data = price_volume_data[address]
                        
                        # Skip if enhanced_data is None (API returned no data for this token)
                        if enhanced_data is None:
                            self.logger.debug(f"No enhanced data available for token {address}")
                            continue
                        
                        # Add to birdeye data if not already present
                        if 'birdeye' not in normalized_data[address]['data']:
                            normalized_data[address]['platforms'].add('birdeye')
                            normalized_data[address]['data']['birdeye'] = {}
                        
                        # Update with fresh data (ensure enhanced_data is a dict)
                        if isinstance(enhanced_data, dict):
                            normalized_data[address]['data']['birdeye'].update({
                                'current_price': enhanced_data.get('value', 0),
                                'price_update_time': enhanced_data.get('updateUnixTime', 0),
                                'liquidity_enhanced': enhanced_data.get('liquidity', 0)
                            })
                        else:
                            self.logger.warning(f"Enhanced data for {address} is not a dict: {type(enhanced_data)}")
                
                # Add DexScreener liquidity analysis for high-scoring tokens
                if address in normalized_data:
                    current_score = self._calculate_token_score(normalized_data[address])
                    if current_score >= 6.0:  # Only analyze liquidity for promising tokens
                        try:
                            liquidity_analysis = await self.dexscreener.get_token_liquidity_analysis(address)
                            if liquidity_analysis:
                                if 'dexscreener' not in normalized_data[address]['data']:
                                    normalized_data[address]['data']['dexscreener'] = {}
                                
                                normalized_data[address]['data']['dexscreener']['liquidity_analysis'] = liquidity_analysis
                                self.logger.debug(f"Added liquidity analysis for {address}: ${liquidity_analysis['total_liquidity_usd']:,.0f}")
                        except Exception as liquidity_error:
                            self.logger.debug(f"Could not get liquidity analysis for {address}: {liquidity_error}")
                
                # Rate limiting between batches
                await asyncio.sleep(0.5)
                
        except Exception as e:
            self.logger.error(f"Error enhancing with Birdeye data: {e}")
            # Log additional debugging information
            self.logger.debug(f"Error details - Token addresses: {len(token_addresses)}")
            self.logger.debug(f"Error details - Exception type: {type(e).__name__}")
            if hasattr(e, '__traceback__'):
                import traceback
                self.logger.debug(f"Error traceback: {traceback.format_exc()}")
    
    def generate_insights(self, correlations: Dict[str, Any]) -> List[str]:
        """Generate actionable insights from correlation analysis"""
        insights = []
        
        # Platform distribution insights
        total_tokens = correlations['total_tokens']
        multi_platform = len(correlations['multi_platform_tokens'])
        
        if total_tokens > 0:
            validation_rate = (multi_platform / total_tokens) * 100
            insights.append(f"Cross-platform validation rate: {validation_rate:.1f}% ({multi_platform}/{total_tokens} tokens)")
        
        # High conviction tokens
        high_conviction = correlations['high_conviction_tokens']
        if high_conviction:
            insights.append(f"Identified {len(high_conviction)} high-conviction tokens (score ≥70.0)")
            
            # Top token details
            top_token = high_conviction[0]
            platforms = ', '.join(top_token['platforms'])
            insights.append(f"Top token: {top_token['address'][:8]}... (Score: {top_token['score']}, Platforms: {platforms})")
        
        # DexScreener boost analysis insights
        boost_analysis = correlations.get('boost_analysis', {})
        if boost_analysis:
            golden_ticker_count = boost_analysis.get('golden_ticker_count', 0)
            if golden_ticker_count > 0:
                insights.append(f"🥇 Golden Ticker tokens detected: {golden_ticker_count} (500+ boosts each)")
            
            # Boost tier distribution
            boost_dist = boost_analysis.get('boost_distribution', {})
            high_tier_count = boost_dist.get('GOLDEN', 0) + boost_dist.get('PLATINUM', 0) + boost_dist.get('GOLD', 0)
            if high_tier_count > 0:
                insights.append(f"High-tier boosted tokens: {high_tier_count} (Gold+ tier)")
            
            # Investment analysis
            avg_boost = boost_analysis.get('average_boost_amount', 0)
            total_investment = boost_analysis.get('total_boost_investment', 0)
            if avg_boost > 0:
                insights.append(f"Average boost amount: {avg_boost:.1f} (Total investment: {total_investment:,.0f})")
        
        # Platform correlation insights
        correlation_matrix = correlations['correlation_matrix']
        if 'dexscreener' in correlation_matrix and 'birdeye' in correlation_matrix['dexscreener']:
            ds_be_overlap = correlation_matrix['dexscreener']['birdeye']
            insights.append(f"DexScreener-Birdeye overlap: {ds_be_overlap} tokens")
        
        if 'rugcheck' in correlation_matrix and 'birdeye' in correlation_matrix['rugcheck']:
            rc_be_overlap = correlation_matrix['rugcheck']['birdeye']
            insights.append(f"RugCheck-Birdeye overlap: {rc_be_overlap} tokens")
        
        # Cache performance insights
        cache_stats = self.enhanced_cache.get_cache_statistics()
        if cache_stats['cache_hits'] + cache_stats['cache_misses'] > 0:
            insights.append(f"Cache efficiency: {cache_stats['hit_rate_percent']:.1f}% hit rate")
            insights.append(f"Estimated cost savings: ${cache_stats['estimated_cost_savings_usd']:.4f}")
        
        return insights
    
    async def run_analysis(self) -> Dict[str, Any]:
        """Run complete cross-platform analysis with caching optimization"""
        start_time = time.time()
        
        try:
            # Collect data from all platforms
            platform_data = await self.collect_all_data()
            
            # Normalize and correlate data
            normalized_data = self.normalize_token_data(platform_data)
            
            # Enhance with additional Birdeye data
            await self._enhance_with_birdeye_data(normalized_data)
            
            # Analyze correlations
            correlations = self.analyze_correlations(normalized_data)
            
            # Generate insights
            insights = self.generate_insights(correlations)
            
            # Compile results
            results = {
                'timestamp': datetime.now().isoformat(),
                'execution_time_seconds': round(time.time() - start_time, 2),
                'platform_data_counts': {k: len(v) for k, v in platform_data.items()},
                'correlations': correlations,
                'insights': insights,
                'cache_statistics': self.enhanced_cache.get_cache_statistics()
            }
            
            self.logger.info(f"✅ Analysis completed in {results['execution_time_seconds']}s")
            return results
            
        except Exception as e:
            self.logger.error(f"❌ Analysis failed: {e}")
            return {
                'timestamp': datetime.now().isoformat(),
                'execution_time_seconds': round(time.time() - start_time, 2),
                'error': str(e),
                'cache_statistics': self.enhanced_cache.get_cache_statistics()
            }
    
    async def close(self):
        """Clean up resources"""
        await self.birdeye.close()
    
    def get_api_stats(self) -> Dict[str, Dict[str, Any]]:
        """Get API statistics from all connectors for health monitoring"""
        stats = {}
        
        try:
            # Get DexScreener stats
            if hasattr(self, 'dexscreener') and self.dexscreener:
                dexscreener_stats = self.dexscreener.get_api_call_statistics()
                stats['dexscreener'] = {
                    'calls': dexscreener_stats.get('total_calls', 0),
                    'successes': dexscreener_stats.get('successful_calls', 0),
                    'failures': dexscreener_stats.get('failed_calls', 0),
                    'total_time_ms': dexscreener_stats.get('total_response_time_ms', 0),
                    'estimated_cost': 0.0  # DexScreener is free
                }
            
            # Get RugCheck stats - NOW PROPERLY CALLING THE ACTUAL API STATS
            if hasattr(self, 'rugcheck') and self.rugcheck:
                rugcheck_stats = self.rugcheck.get_api_call_statistics()
                stats['rugcheck'] = {
                    'calls': rugcheck_stats.get('total_calls', 0),
                    'successes': rugcheck_stats.get('successful_calls', 0),
                    'failures': rugcheck_stats.get('failed_calls', 0),
                    'total_time_ms': rugcheck_stats.get('total_response_time_ms', 0),
                    'estimated_cost': rugcheck_stats.get('total_calls', 0) * 0.0001  # Minimal cost estimate
                }
                self.logger.debug(f"📊 RugCheck API stats: {rugcheck_stats.get('total_calls', 0)} calls, {rugcheck_stats.get('successful_calls', 0)} successes")
            
            # Get Birdeye stats from the connector (this would be for cross-platform Birdeye calls)
            if hasattr(self, 'birdeye') and self.birdeye:
                # Get stats from the underlying BirdeyeAPI if available
                if hasattr(self.birdeye, 'birdeye_api') and self.birdeye.birdeye_api:
                    birdeye_stats = self.birdeye.birdeye_api.get_api_call_statistics()
                    stats['birdeye'] = {
                        'calls': birdeye_stats.get('total_api_calls', 0),
                        'successes': birdeye_stats.get('successful_api_calls', 0),
                        'failures': birdeye_stats.get('failed_api_calls', 0),
                        'total_time_ms': birdeye_stats.get('total_response_time_ms', 0),
                        'estimated_cost': birdeye_stats.get('cost_tracking', {}).get('total_cost_usd', 0.0)
                    }
                    self.logger.debug(f"📊 Birdeye API stats: {birdeye_stats.get('total_api_calls', 0)} calls, {birdeye_stats.get('successful_api_calls', 0)} successes")
                else:
                    # Fallback if direct access isn't available
                    stats['birdeye'] = {
                        'calls': 0,
                        'successes': 0,
                        'failures': 0,
                        'total_time_ms': 0,
                        'estimated_cost': 0.0
                    }
            
        except Exception as e:
            self.logger.error(f"Error getting API stats: {e}")
            
        return stats

async def main():
    """Main execution function"""
    # Set up logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    analyzer = None
    try:
        # Initialize analyzer
        analyzer = CrossPlatformAnalyzer()
        
        # Run analysis
        results = await analyzer.run_analysis()
        
        # Save results
        timestamp = int(time.time())
        output_file = f"scripts/results/cross_platform_analysis_{timestamp}.json"
        
        os.makedirs("scripts/results", exist_ok=True)
        with open(output_file, 'w') as f:
            json.dump(results, f, indent=2)
        
        # Print summary
        print("\n🎯 Cross-Platform Token Analysis Results")
        print("=" * 50)
        
        if 'error' in results:
            print(f"❌ Analysis failed: {results['error']}")
        else:
            print(f"⏱️  Execution time: {results['execution_time_seconds']}s")
            print(f"📊 Platform data: {results['platform_data_counts']}")
            print(f"🔍 Total unique tokens: {results['correlations']['total_tokens']}")
            print(f"💎 High-conviction tokens: {len(results['correlations']['high_conviction_tokens'])}")
            
            # Cache performance
            cache_stats = results['cache_statistics']
            print(f"🚀 Cache hit rate: {cache_stats['hit_rate_percent']:.1f}%")
            print(f"💰 Estimated savings: ${cache_stats['estimated_cost_savings_usd']:.4f}")
            
            print("\n📋 Key Insights:")
            for insight in results['insights']:
                print(f"  • {insight}")
        
        print(f"\n📁 Full results saved to: {output_file}")
        
    except Exception as e:
        print(f"❌ Error: {e}")
    finally:
        if analyzer:
            await analyzer.close()

if __name__ == "__main__":
    asyncio.run(main()) 