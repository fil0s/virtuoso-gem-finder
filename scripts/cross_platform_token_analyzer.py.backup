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

# WSOL-Only Analysis Configuration
WSOL_ADDRESS = 'So11111111111111111111111111111111111111112'  # Wrapped SOL address
WSOL_ONLY_MODE = True  # Enable WSOL-only pair filtering for focused analysis

from api.birdeye_connector import BirdeyeAPI
from api.rugcheck_connector import RugCheckConnector
from core.cache_manager import CacheManager
from services.rate_limiter_service import RateLimiterService
from services.logger_setup import LoggerSetup
from services.enhanced_cache_manager import EnhancedPositionCacheManager
from core.config_manager import ConfigManager, get_config_manager

from api.enhanced_jupiter_connector import EnhancedJupiterConnector
from api.orca_connector import OrcaConnector
from api.raydium_connector import RaydiumConnector

# Import VLR Intelligence
try:
    from services.vlr_intelligence import VLRIntelligence, VLRAnalysis, analyze_token_vlr_simple
    VLR_AVAILABLE = True
except ImportError:
    VLR_AVAILABLE = False
    logging.warning("⚠️ VLR Intelligence module not available")

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
        """Make a tracked API request to DexScreener with optimizations"""
        import time
        
        start_time = time.time()
        self.api_stats["total_calls"] += 1
        self.api_stats["endpoints_used"].add(endpoint)
        
        try:
            # Optimized session configuration
            timeout = aiohttp.ClientTimeout(total=10, connect=5)  # Reduced timeout for faster failures
            connector = aiohttp.TCPConnector(
                limit=10,  # Connection pool limit
                limit_per_host=5,  # Connections per host
                ttl_dns_cache=300,  # DNS cache TTL
                use_dns_cache=True,
                keepalive_timeout=30,
                enable_cleanup_closed=True
            )
            
            async with aiohttp.ClientSession(timeout=timeout, connector=connector) as session:
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
                        
        except asyncio.TimeoutError:
            response_time_ms = (time.time() - start_time) * 1000
            self.api_stats["total_response_time_ms"] += response_time_ms
            self.api_stats["failed_calls"] += 1
            logging.error(f"🔴 DexScreener API timeout: {endpoint} - {response_time_ms:.1f}ms")
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

    async def get_marketing_orders(self, token_address: str, chain_id: str = "solana") -> Dict[str, Any]:
        """
        Get marketing orders/promotional spending data for a specific token.
        Used in Stage 3 of cost-optimized pipeline for market analysis.
        
        Args:
            token_address: Token contract address
            chain_id: Blockchain identifier (default: solana)
            
        Returns:
            Marketing investment data and promotional analysis
        """
        try:
            # Check cache first
            cache_key = f"marketing_orders_{token_address}_{chain_id}"
            if self.enhanced_cache:
                cached_data = self.enhanced_cache.get_enhanced("marketing_data", cache_key)
                if cached_data:
                    return cached_data
            
            # Make tracked API request
            endpoint = f"/orders/v1/{chain_id}/{token_address}"
            data = await self._make_tracked_request(endpoint)
            
            if not data:
                return self._create_empty_marketing_data(token_address)
            
            # Process marketing data
            marketing_analysis = self._process_marketing_orders(token_address, data)
            
            # Cache the result
            if self.enhanced_cache:
                self.enhanced_cache.set_enhanced("marketing_data", cache_key, marketing_analysis)
            
            return marketing_analysis
            
        except Exception as e:
            logging.error(f"❌ Error getting marketing orders for {token_address}: {e}")
            return self._create_empty_marketing_data(token_address)
    
    def _process_marketing_orders(self, token_address: str, data: Dict[str, Any]) -> Dict[str, Any]:
        """Process marketing orders data for cost-optimized analysis"""
        try:
            orders = data if isinstance(data, list) else []
            
            # Calculate marketing metrics
            total_investment = 0.0
            active_campaigns = 0
            campaign_types = set()
            recent_activity = []
            
            for order in orders:
                amount = order.get('amount', 0)
                order_type = order.get('type', 'unknown')
                status = order.get('status', 'unknown')
                created_at = order.get('createdAt', '')
                
                if status == 'active':
                    active_campaigns += 1
                    total_investment += amount
                    campaign_types.add(order_type)
                    
                    # Track recent activity (last 7 days)
                    if created_at:
                        recent_activity.append({
                            'type': order_type,
                            'amount': amount,
                            'created_at': created_at
                        })
            
            # Calculate marketing investment score
            investment_score = self._calculate_investment_score(total_investment, active_campaigns)
            
            # Calculate promotional momentum
            momentum_score = self._calculate_promotional_momentum(recent_activity)
            
            return {
                'token_address': token_address,
                'total_investment_usd': total_investment,
                'active_campaigns': active_campaigns,
                'campaign_types': list(campaign_types),
                'recent_activity_count': len(recent_activity),
                'investment_score': investment_score,
                'momentum_score': momentum_score,
                'promotional_tier': self._get_promotional_tier(total_investment),
                'marketing_quality': self._assess_marketing_quality(orders),
                'raw_orders': orders,
                'analysis_timestamp': time.time()
            }
            
        except Exception as e:
            logging.error(f"❌ Error processing marketing orders: {e}")
            return self._create_empty_marketing_data(token_address)
    
    def _calculate_investment_score(self, total_investment: float, active_campaigns: int) -> float:
        """Calculate marketing investment score (0-100)"""
        # Base score from investment amount
        investment_component = min(total_investment / 1000, 50)  # $1000 = 50 points
        
        # Bonus for multiple active campaigns
        campaign_component = min(active_campaigns * 10, 30)  # Up to 30 points
        
        # Consistency bonus
        consistency_bonus = 20 if active_campaigns >= 3 and total_investment >= 500 else 0
        
        return min(investment_component + campaign_component + consistency_bonus, 100)
    
    def _calculate_promotional_momentum(self, recent_activity: List[Dict]) -> float:
        """Calculate promotional momentum based on recent activity"""
        if not recent_activity:
            return 0.0
        
        # Score based on activity frequency and amounts
        activity_score = min(len(recent_activity) * 15, 60)  # Up to 60 points
        
        # Bonus for high-value recent campaigns
        amount_bonus = 0
        for activity in recent_activity:
            if activity.get('amount', 0) >= 100:  # $100+ campaigns
                amount_bonus += 10
        
        return min(activity_score + amount_bonus, 100)
    
    def _get_promotional_tier(self, total_investment: float) -> str:
        """Categorize promotional investment level"""
        if total_investment >= 1000:
            return 'premium'
        elif total_investment >= 500:
            return 'standard'
        elif total_investment >= 100:
            return 'basic'
        elif total_investment > 0:
            return 'minimal'
        else:
            return 'none'
    
    def _assess_marketing_quality(self, orders: List[Dict]) -> str:
        """Assess overall marketing campaign quality"""
        if not orders:
            return 'none'
        
        # Check for diverse campaign types
        campaign_types = set(order.get('type', '') for order in orders)
        active_orders = [o for o in orders if o.get('status') == 'active']
        
        if len(campaign_types) >= 3 and len(active_orders) >= 2:
            return 'high'
        elif len(campaign_types) >= 2 and len(active_orders) >= 1:
            return 'medium'
        elif len(active_orders) >= 1:
            return 'basic'
        else:
            return 'low'
    
    def _create_empty_marketing_data(self, token_address: str) -> Dict[str, Any]:
        """Create empty marketing data structure for failed requests"""
        return {
            'token_address': token_address,
            'total_investment_usd': 0.0,
            'active_campaigns': 0,
            'campaign_types': [],
            'recent_activity_count': 0,
            'investment_score': 0.0,
            'momentum_score': 0.0,
            'promotional_tier': 'none',
            'marketing_quality': 'none',
            'raw_orders': [],
            'analysis_timestamp': time.time(),
            'error': 'Failed to retrieve marketing data'
        }
    
    async def get_batch_marketing_data(self, token_addresses: List[str], chain_id: str = "solana") -> Dict[str, Dict[str, Any]]:
        """
        Batch fetch marketing data for multiple tokens.
        Used in Stage 3 of cost-optimized pipeline.
        
        Args:
            token_addresses: List of token contract addresses
            chain_id: Blockchain identifier
            
        Returns:
            Dictionary mapping token addresses to marketing data
        """
        results = {}
        
        # Process in parallel for efficiency
        tasks = []
        for token_address in token_addresses:
            task = self.get_marketing_orders(token_address, chain_id)
            tasks.append((token_address, task))
        
        # Execute all requests
        for token_address, task in tasks:
            try:
                marketing_data = await task
                results[token_address] = marketing_data
            except Exception as e:
                logging.error(f"❌ Error getting marketing data for {token_address}: {e}")
                results[token_address] = self._create_empty_marketing_data(token_address)
        
        return results

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
        self.logger = logging.getLogger(__name__)
        
    async def get_trending_tokens(self, limit: int = 20) -> List[Dict]:
        """Get trending tokens from Birdeye with symbols directly from trending endpoint"""
        # Check cache first
        if self.enhanced_cache:
            cached_data = self.enhanced_cache.get_enhanced("cross_platform_trending", "birdeye_trending", f"limit_{limit}")
            if cached_data:
                return cached_data
        
        try:
            # Call the trending endpoint directly to get full token data including symbols
            response = await self.birdeye_api._make_request("/defi/token_trending")
            
            if not response or not isinstance(response, dict):
                logging.warning("Invalid response from Birdeye trending endpoint")
                return []
            
            # Extract tokens from response
            trending_tokens = []
            if response.get('success') and 'data' in response:
                data = response['data']
                if isinstance(data, dict) and 'tokens' in data:
                    trending_tokens = data['tokens']
                elif isinstance(data, list):
                    trending_tokens = data
                elif isinstance(data, dict) and 'items' in data:
                    trending_tokens = data['items']
            
            if not trending_tokens:
                logging.warning("No trending tokens found in Birdeye response")
                return []
            
            # Process the trending tokens with their symbols
            detailed_data = []
            for token in trending_tokens[:limit]:
                if not isinstance(token, dict) or 'address' not in token:
                    continue
                
                # Extract token data with symbols preserved from the trending endpoint
                token_data = {
                    'address': token.get('address', ''),
                    'symbol': token.get('symbol', token.get('name', 'Unknown')),
                    'name': token.get('name', ''),
                    'price': token.get('price', 0),
                    'volume_24h_usd': token.get('volume_24h_usd', token.get('volume24h', 0)),
                    'market_cap': token.get('market_cap', token.get('mc', 0)),
                    'liquidity': token.get('liquidity', 0),
                    'price_change_24h_percent': token.get('price_change_24h_percent', token.get('priceChange24h', 0)),
                    'holder_count': token.get('holder', token.get('holders', 0)),
                    'trade_24h_count': token.get('trade_24h_count', 0),
                    'last_trade_unix_time': token.get('last_trade_unix_time', 0),
                    'discovery_source': 'birdeye_trending'
                }
                
                # Only add tokens with valid addresses
                if token_data['address']:
                    detailed_data.append(token_data)
            
            # Cache the result
            if self.enhanced_cache:
                self.enhanced_cache.set_enhanced("cross_platform_trending", "birdeye_trending", detailed_data, f"limit_{limit}")
            
            logging.info(f"📈 Successfully fetched {len(detailed_data)} trending tokens with symbols from Birdeye")
            return detailed_data
            
        except Exception as e:
            logging.error(f"Error fetching Birdeye trending tokens: {e}")
            # Fallback to the old method if direct call fails
            try:
                trending_addresses = await self.birdeye_api.get_trending_tokens()
                if trending_addresses:
                    fallback_data = []
                    for address in trending_addresses[:limit]:
                        fallback_data.append({
                            'address': address,
                            'symbol': 'Unknown',
                            'name': '',
                            'price': 0,
                            'volume_24h_usd': 0,
                            'market_cap': 0,
                            'liquidity': 0,
                            'discovery_source': 'birdeye_trending_fallback'
                        })
                    return fallback_data
            except Exception as fallback_error:
                logging.error(f"Fallback method also failed: {fallback_error}")
            
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
                min_volume_24h_usd=500000,     # $500K+ daily volume (lowered threshold)
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

class MeteoraConnector:
    """Connector for Meteora DEX with pool-based token discovery"""
    
    def __init__(self, enhanced_cache: Optional[EnhancedPositionCacheManager] = None):
        self.enhanced_cache = enhanced_cache
        self.logger = logging.getLogger(__name__)
        self.base_url = "https://app.meteora.ag/clmm-api"
        self.session = None
        
        # API tracking
        self.api_calls = 0
        self.successful_calls = 0
        self.failed_calls = 0
        self.last_error = None
        self.start_time = time.time()
        
        # Exclusion system
        self.excluded_addresses = set()
        self._load_exclusions()
    
    def _load_exclusions(self):
        """Load exclusion list from central system"""
        try:
            import sys
            import os
            sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'services'))
            from early_token_detection import EarlyTokenDetector
            
            detector = EarlyTokenDetector()
            self.excluded_addresses = detector.get_excluded_addresses()
            self.logger.info(f"🚫 Loaded {len(self.excluded_addresses)} excluded addresses for Meteora")
            
        except Exception as e:
            self.logger.warning(f"Could not load central exclusions for Meteora: {e}")
            self.excluded_addresses = {
                'EPjFWdd5AufqSSqeM2qN1xzybapC8G4wEGGkZwyTDt1v',  # USDC
                'Es9vMFrzaCERmJfrF4H2FYD4KCoNkY11McCe8BenwNYB',  # USDT
                'So11111111111111111111111111111111111111112'    # SOL
            }
    
    def get_api_call_statistics(self) -> Dict[str, Any]:
        """Get comprehensive API call statistics"""
        runtime = time.time() - self.start_time
        success_rate = (self.successful_calls / self.api_calls * 100) if self.api_calls > 0 else 0
        
        return {
            'total_calls': self.api_calls,
            'successful_calls': self.successful_calls,
            'failed_calls': self.failed_calls,
            'success_rate': round(success_rate, 2),
            'runtime_seconds': round(runtime, 2),
            'calls_per_minute': round((self.api_calls / runtime * 60), 2) if runtime > 0 else 0,
            'last_error': self.last_error
        }
    
    async def _make_tracked_request(self, url: str) -> Optional[Dict]:
        """Make HTTP request with tracking"""
        if not self.session:
            import aiohttp
            self.session = aiohttp.ClientSession()
        
        self.api_calls += 1
        
        try:
            async with self.session.get(url, timeout=30) as response:
                if response.status == 200:
                    data = await response.json()
                    self.successful_calls += 1
                    return data
                else:
                    self.failed_calls += 1
                    self.last_error = f"HTTP {response.status}"
                    return None
                    
        except Exception as e:
            self.failed_calls += 1
            self.last_error = str(e)
            self.logger.error(f"Error making Meteora API request: {e}")
            return None
    
    async def get_volume_trending_pools(self, limit: int = 50) -> List[Dict]:
        """Get trending pools by volume with token discovery"""
        cache_key = f"meteora_volume_trending_{limit}"
        
        # Check cache first
        if self.enhanced_cache:
            cached_data = self.enhanced_cache.get_enhanced("meteora_pools", cache_key)
            if cached_data:
                return cached_data
        
        try:
            url = f"{self.base_url}/pair/all_by_groups"
            data = await self._make_tracked_request(url)
            
            if not data or not isinstance(data, dict) or 'groups' not in data:
                self.logger.warning("Invalid response from Meteora volume trending")
                return []
            
            trending_tokens = []
            excluded_count = 0
            
            # Extract all pairs from all groups
            all_pairs = []
            for group in data.get('groups', []):
                pairs = group.get('pairs', [])
                all_pairs.extend(pairs)
            
            # Process more pairs to find gems (not just the first N pairs)
            # Since most early pairs are SOL/USDC (excluded), we need to check many more pairs
            max_pairs_to_check = min(len(all_pairs), limit * 20)  # Check 20x more pairs to find non-excluded tokens
            tokens_found = 0
            
            for pool in all_pairs[:max_pairs_to_check]:
                if tokens_found >= limit:  # Stop when we have enough tokens
                    break
                if not isinstance(pool, dict):
                    continue
                
                # Extract token information from pool
                mint_x = pool.get('mint_x', '')
                mint_y = pool.get('mint_y', '')
                
                # WSOL-Only filtering: Only analyze pools with WSOL as one side
                target_mints = []
                if WSOL_ONLY_MODE:
                    # Only include pairs where one side is WSOL and the other is not excluded
                    if mint_x == WSOL_ADDRESS and mint_y and mint_y not in self.excluded_addresses:
                        target_mints.append(mint_y)  # Add the non-WSOL token
                        self.logger.debug(f"🌊 Found WSOL-{mint_y[:8]}... pair in Meteora pool")
                    elif mint_y == WSOL_ADDRESS and mint_x and mint_x not in self.excluded_addresses:
                        target_mints.append(mint_x)  # Add the non-WSOL token
                        self.logger.debug(f"🌊 Found {mint_x[:8]}...-WSOL pair in Meteora pool")
                    elif mint_x == WSOL_ADDRESS and mint_y in self.excluded_addresses:
                        excluded_count += 1  # WSOL pair but token is excluded
                        self.logger.debug(f"⏭️ Skipped WSOL-{mint_y[:8]}... pair (excluded token)")
                        continue
                    elif mint_y == WSOL_ADDRESS and mint_x in self.excluded_addresses:
                        excluded_count += 1  # WSOL pair but token is excluded  
                        self.logger.debug(f"⏭️ Skipped {mint_x[:8]}...-WSOL pair (excluded token)")
                        continue
                    else:
                        excluded_count += 1  # Not a WSOL pair
                        continue
                else:
                    # Original logic: find any non-excluded token
                    if mint_x and mint_x not in self.excluded_addresses:
                        target_mints.append(mint_x)
                    elif mint_x in self.excluded_addresses:
                        excluded_count += 1
                        
                    if mint_y and mint_y not in self.excluded_addresses:
                        target_mints.append(mint_y)
                    elif mint_y in self.excluded_addresses:
                        excluded_count += 1
                
                # If no valid tokens found, skip this pool
                if not target_mints:
                    continue
                
                for mint_address in target_mints:
                    
                    # Calculate Volume-to-Liquidity Ratio (VLR) - use reserves as proxy for TVL
                    # Ensure numeric types for calculations
                    try:
                        reserve_x = float(pool.get('reserve_x_amount', 0))
                        reserve_y = float(pool.get('reserve_y_amount', 0))
                        total_reserves = reserve_x + reserve_y
                        
                        # Use bin_step as activity indicator (smaller = more active)
                        bin_step = float(pool.get('bin_step', 100))
                        activity_score = max(0, 100 - bin_step) / 100  # Normalize to 0-1
                    except (ValueError, TypeError):
                        # Skip this token if we can't parse numeric values
                        continue
                    
                    vlr = activity_score
                    
                    token_data = {
                        'address': mint_address,
                        'symbol': pool.get('name', '').split('-')[0 if mint_address == mint_x else 1].strip(),
                        'pool_address': pool.get('address', ''),
                        'pool_name': pool.get('name', ''),
                        'bin_step': bin_step,
                        'activity_score': activity_score,
                        'vlr': round(vlr, 4),
                        'base_fee_percentage': pool.get('base_fee_percentage', 0),
                        'reserve_x': pool.get('reserve_x', 0),
                        'reserve_y': pool.get('reserve_y', 0),
                        'reserve_x_amount': reserve_x,
                        'reserve_y_amount': reserve_y,
                        'total_reserves': total_reserves,
                        'discovery_source': 'meteora_volume_trending',
                        'pool_type': 'CLMM',
                        'meteora_score': self._calculate_meteora_score(pool, vlr),
                        'timestamp': time.time()
                    }
                    
                    # Add WSOL pair flag when WSOL filtering is active
                    if WSOL_ONLY_MODE:
                        token_data['is_wsol_pair'] = True
                    
                    trending_tokens.append(token_data)
                    tokens_found += 1  # Count tokens found
            
            # Remove duplicates and sort by VLR
            unique_tokens = {}
            for token in trending_tokens:
                addr = token['address']
                if addr not in unique_tokens or token['vlr'] > unique_tokens[addr]['vlr']:
                    unique_tokens[addr] = token
            
            result = list(unique_tokens.values())
            result.sort(key=lambda x: x['vlr'], reverse=True)
            
            # Cache the result
            if self.enhanced_cache:
                self.enhanced_cache.set_enhanced("meteora_pools", cache_key, result)
            
            self.logger.info(f"🌊 Discovered {len(result)} tokens from Meteora pools (excluded {excluded_count})")
            return result
            
        except Exception as e:
            self.logger.error(f"Error fetching Meteora volume trending: {e}")
            return []
    
    def _calculate_meteora_score(self, pool: Dict, vlr: float) -> float:
        """Calculate Meteora-specific score for pool quality"""
        score = 0
        
        # Reserve component (0-40 points) - proxy for liquidity
        try:
            reserve_x = float(pool.get('reserve_x_amount', 0))
            reserve_y = float(pool.get('reserve_y_amount', 0))
            total_reserves = reserve_x + reserve_y
        except (ValueError, TypeError):
            total_reserves = 0
        
        if total_reserves > 1000000:  # $1M+ equivalent
            score += 40
        elif total_reserves > 500000:  # $500K+
            score += 30
        elif total_reserves > 100000:  # $100K+
            score += 20
        elif total_reserves > 10000:   # $10K+
            score += 10
        elif total_reserves > 1000:    # $1K+
            score += 5
        
        # Bin step component (0-30 points) - smaller bin step = more precise = better
        try:
            bin_step = float(pool.get('bin_step', 100))
        except (ValueError, TypeError):
            bin_step = 100
            
        if bin_step <= 10:
            score += 30
        elif bin_step <= 25:
            score += 25
        elif bin_step <= 50:
            score += 20
        elif bin_step <= 100:
            score += 15
        elif bin_step <= 200:
            score += 10
        
        # Activity score component (0-20 points)
        activity_score = vlr  # This is our activity score (0-1)
        score += activity_score * 20
        
        # Fee component (0-10 points) - reasonable fees are good
        try:
            base_fee = float(pool.get('base_fee_percentage', 0))
        except (ValueError, TypeError):
            base_fee = 0
            
        if 0.1 <= base_fee <= 1.0:  # Reasonable fee range
            score += 10
        elif 0.01 <= base_fee <= 2.0:  # Acceptable range
            score += 7
        elif base_fee > 0:  # At least has some fee
            score += 3
        
        return min(100, score)
    
    async def close(self):
        """Close HTTP session"""
        if self.session:
            await self.session.close()
            self.session = None

class CrossPlatformAnalyzer:
    """Enhanced cross-platform token analyzer with comprehensive data collection and correlation analysis"""
    
    def __init__(self, config: Optional[Dict] = None, logger: Optional[logging.Logger] = None, shared_birdeye_api: Optional[Any] = None):
        # Initialize configuration
        if config is None:
            config_manager = get_config_manager()
            config = config_manager.get_config()
        self.config = config
        
        # Initialize logger
        if logger is None:
            logger_setup = LoggerSetup("CrossPlatformAnalyzer")
            logger = logger_setup.logger
        self.logger = logger
        
        # Load exclusions (stablecoins, wrapped tokens, etc.)
        self.excluded_addresses = set()
        self._load_exclusions()
        
        # Initialize cache managers
        self.base_cache = CacheManager()
        self.enhanced_cache = EnhancedPositionCacheManager(base_cache_manager=self.base_cache, logger=logger)
        
        # Initialize rate limiter for API calls
        rate_limiter_config = {
            "enabled": True,
            "domains": {
                "default": {"calls": 30, "period": 60}  # 30 calls per minute
            }
        }
        self.rate_limiter = RateLimiterService(config=rate_limiter_config)
        
        # Initialize APIs with shared services
        birdeye_config = self.config.get('BIRDEYE_API', {})
        
        # Use shared BirdeyeAPI instance if provided, otherwise create new one
        if shared_birdeye_api is not None:
            self.logger.info("🔗 Using shared BirdeyeAPI instance for cross-platform analysis")
            self.birdeye_api = shared_birdeye_api
        else:
            # Manually set API key from environment (like other working scripts)
            birdeye_api_key = os.environ.get('BIRDEYE_API_KEY')
            if birdeye_api_key:
                birdeye_config['api_key'] = birdeye_api_key
            
            self.birdeye_api = BirdeyeAPI(
                config=birdeye_config,
                logger=self.logger,
                cache_manager=self.base_cache,
                rate_limiter=self.rate_limiter
            )
            self.logger.info("🆕 Created new BirdeyeAPI instance for cross-platform analysis")
        
        # Initialize connectors with enhanced caching
        self.dexscreener = DexScreenerConnector(self.enhanced_cache)
        self.birdeye = BirdeyeConnector(self.birdeye_api, self.enhanced_cache)
        self.rugcheck = RugCheckConnector()
        
        # Initialize emerging token discovery connectors
        self.jupiter = EnhancedJupiterConnector(
            enhanced_cache=self.enhanced_cache
        )
        self.meteora = MeteoraConnector(self.enhanced_cache)
        
        # Initialize DEX connectors for direct liquidity analysis
        self.orca = OrcaConnector(enhanced_cache=self.enhanced_cache)
        self.raydium = RaydiumConnector(enhanced_cache=self.enhanced_cache)
        
        # Initialize VLR Intelligence
        if VLR_AVAILABLE:
            self.vlr_intelligence = VLRIntelligence(logger=self.logger)
            self.logger.info("🧠 VLR Intelligence initialized for cross-platform analysis")
        else:
            self.vlr_intelligence = None
            self.logger.warning("⚠️ VLR Intelligence not available - VLR analysis disabled")
        
        shared_status = "shared" if shared_birdeye_api is not None else "independent"
        self.logger.info(f"🚀 Cross-Platform Analyzer initialized with {shared_status} BirdeyeAPI and enhanced caching (excluding {len(self.excluded_addresses)} stablecoins and wrapped tokens)")
        self.logger.info("🪙 Emerging token discovery enabled via Jupiter & Meteora")
    
    def _load_exclusions(self):
        """Load exclusion list from central exclusion system"""
        try:
            # Import the central exclusion system
            import sys
            import os
            sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'services'))
            from early_token_detection import EarlyTokenDetector
            
            # Get exclusions from central system
            detector = EarlyTokenDetector()
            self.excluded_addresses = detector.get_excluded_addresses()
            self.logger.info(f"🚫 Loaded {len(self.excluded_addresses)} excluded addresses from central system")
            
        except Exception as e:
            self.logger.warning(f"Could not load central exclusions, using minimal set: {e}")
            # Fallback minimal exclusions
            self.excluded_addresses = {
                'EPjFWdd5AufqSSqeM2qN1xzybapC8G4wEGGkZwyTDt1v',  # USDC
                'Es9vMFrzaCERmJfrF4H2FYD4KCoNkY11McCe8BenwNYB',  # USDT
                'So11111111111111111111111111111111111111112',   # SOL
                '4k3Dyjzvzp8eMZWUXbBCjEvwSkkk59S5iCNLY3QrkX6R',   # RAY
                'mSoLzYCxHdYgdzU16g5QSh3i5K3z3KZK7ytfqcJm7So'    # mSOL
            }
    
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
        
        # Enhanced emerging token discovery tasks
        tasks.append(('jupiter_token_list', self.jupiter.get_enhanced_token_list(
            limit=200,  # Reasonable limit for gem discovery
            filter_criteria={
                'min_daily_volume': 1000,       # Lower threshold for early gems
                'exclude_old_tokens_days': 730,  # Exclude tokens older than 2 years
                'exclude_risk_levels': ['VERY_HIGH'],  # Only exclude very high risk
                'max_tokens_per_tag': 50        # Limit per category
            }
        )))  # Smart filtering for gem discovery
        tasks.append(('jupiter_quote_analysis', self.jupiter.get_enhanced_quote("So11111111111111111111111111111111111111112", "EPjFWdd5AufqSSqeM2qN1xzybapC8G4wEGGkZwyTDt1v", 1000000)))  # Updated method call
        tasks.append(('meteora_volume_trending', self.meteora.get_volume_trending_pools(limit=50)))
        
        # DEX connector tasks for direct liquidity analysis
        tasks.append(('orca_trending_pools', self.orca.get_wsol_trending_pools(limit=50)))
        tasks.append(('raydium_trending_pairs', self.raydium.get_wsol_trending_pairs(limit=50)))
        
        # Execute all tasks in parallel
        results = {}
        task_names = [name for name, _ in tasks]
        task_coroutines = [coro for _, coro in tasks]
        
        completed = await asyncio.gather(*task_coroutines, return_exceptions=True)
        
        for name, result in zip(task_names, completed):
            if isinstance(result, Exception):
                self.logger.error(f"❌ Error in {name}: {result}")
                # Add more detailed error logging
                import traceback
                self.logger.error(f"   Traceback: {traceback.format_exc()}")
                results[name] = []
            else:
                # Special handling for Jupiter quote analysis (returns single dict, not list)
                if name == 'jupiter_quote_analysis':
                    if result:
                        # Convert single quote result to list format with address extraction
                        quote_result = []
                        # Extract both input and output token addresses from the quote
                        input_mint = result.get('input_mint', '')
                        output_mint = result.get('output_mint', '')
                        
                        # Add the input token (SOL) with quote data
                        if input_mint:
                            quote_result.append({
                                'address': input_mint,
                                **result,
                                'role': 'input_token'
                            })
                        
                        # Add the output token (USDC) with quote data
                        if output_mint and output_mint != input_mint:
                            quote_result.append({
                                'address': output_mint,
                                **result,
                                'role': 'output_token'
                            })
                        
                        results[name] = quote_result
                        self.logger.info(f"✅ {name}: Successfully processed quote analysis for {len(quote_result)} tokens")
                    else:
                        results[name] = []
                        self.logger.warning(f"⚠️ {name}: Returned empty result (no error, but no data)")
                else:
                    # Standard handling for list results
                    results[name] = result if result else []
                    # Log success with more detail
                    if result:
                        self.logger.info(f"✅ {name}: Successfully fetched {len(result)} items")
                    else:
                        self.logger.warning(f"⚠️ {name}: Returned empty result (no error, but no data)")
        
        # Log enhanced collection results with WSOL filtering status
        wsol_status = "🪙 WSOL-ONLY MODE" if WSOL_ONLY_MODE else "🌐 ALL-PAIRS MODE"
        self.logger.info(f"📊 Enhanced data collection completed ({wsol_status}):")
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
        
        # Log emerging token discovery results
        self.logger.info(f"  🪙 Jupiter token list: {len(results.get('jupiter_token_list', []))}")
        self.logger.info(f"  📊 Jupiter quote analysis: {len(results.get('jupiter_quote_analysis', []))}")
        self.logger.info(f"  🌊 Meteora volume trending: {len(results.get('meteora_volume_trending', []))}")
        self.logger.info(f"  🌀 Orca trending pools: {len(results.get('orca_trending_pools', []))}")
        self.logger.info(f"  ⚡ Raydium trending pairs: {len(results.get('raydium_trending_pairs', []))}")
        
        # Enhanced: Get batch pricing for discovered Jupiter tokens
        jupiter_tokens = results.get('jupiter_token_list', [])
        if jupiter_tokens:
            try:
                # Extract token addresses for batch pricing (reduced from 500 to match filtering)
                token_addresses = [token['address'] for token in jupiter_tokens[:100]]  # Reduced for efficiency
                self.logger.info(f"💰 Getting batch prices for {len(token_addresses)} Jupiter tokens...")
                
                jupiter_prices = await self.jupiter.get_batch_prices(token_addresses)
                if jupiter_prices:
                    results['jupiter_batch_prices'] = [
                        {
                            'address': addr,
                            'price_data': price_info,
                            'discovery_source': 'jupiter_batch_pricing'
                        }
                        for addr, price_info in jupiter_prices.items()
                    ]
                    self.logger.info(f"  💰 Jupiter batch pricing: {len(jupiter_prices)} tokens priced")
            except Exception as e:
                self.logger.warning(f"Jupiter batch pricing failed: {e}")
                results['jupiter_batch_prices'] = []
                
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
            if addr and addr not in self.excluded_addresses:  # Filter excluded addresses
                profile_lookup[addr] = profile
        
        # Process DexScreener boosted tokens
        for token in platform_data.get('dexscreener_boosted', []):
            addr = token.get('tokenAddress', '')  # Keep original case for Solana addresses
            if addr and addr not in self.excluded_addresses:  # Filter excluded addresses
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
            if addr and addr not in self.excluded_addresses:  # Filter excluded addresses
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
                    if addr and addr not in self.excluded_addresses:  # Filter excluded addresses
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
            if addr and addr not in self.excluded_addresses:  # Filter excluded addresses
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
            if addr and addr not in self.excluded_addresses:  # Filter excluded addresses
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
                

        # Process Birdeye emerging stars tokens
        for token in platform_data.get('birdeye_emerging_stars', []):
            addr = token.get('address', '')  # Keep original case for Solana addresses
            if addr and addr not in self.excluded_addresses:  # Filter excluded addresses
                # Add emerging stars as a distinct platform signal
                normalized[addr]['platforms'].add('birdeye_emerging_stars')
                
                # Create or update birdeye data with emerging star specific metrics
                if 'birdeye' not in normalized[addr]['data']:
                    normalized[addr]['data']['birdeye'] = {}
                
                # Add emerging star specific data
                normalized[addr]['data']['birdeye'].update({
                    'volume_24h_usd': token.get('volume_24h_usd', 0),
                    'market_cap': token.get('market_cap', 0),
                    'holder_count': token.get('holder_count', 0),
                    'trade_24h_count': token.get('trade_24h_count', 0),
                    'price': token.get('price', 0),
                    'price_change_24h': token.get('price_change_24h_percent', 0),
                    'liquidity': token.get('liquidity', 0),
                    'fdv': token.get('fdv', 0),
                    'symbol': token.get('symbol', ''),
                    'name': token.get('name', ''),
                    'last_trade_time': token.get('last_trade_unix_time', 0),
                    
                    # Emerging star specific metrics
                    'volume_to_mcap_ratio': token.get('volume_to_mcap_ratio', 0),
                    'emerging_star_score': token.get('emerging_star_score', 0),
                    'momentum_tier': token.get('momentum_tier', 'MINIMAL_MOMENTUM'),
                    'discovery_source': 'birdeye_emerging_stars',
                    'is_emerging_star': True
                })
                
                # Register token for enhanced caching
                self.enhanced_cache.register_tracked_token(addr)
        
        # Process Jupiter token list (EMERGING tokens)
        for token in platform_data.get('jupiter_token_list', []):
            addr = token.get('address', '')
            if addr and addr not in self.excluded_addresses:
                normalized[addr]['platforms'].add('jupiter')
                normalized[addr]['data']['jupiter'] = {
                    'symbol': token.get('symbol', ''),
                    'name': token.get('name', ''),
                    'decimals': token.get('decimals', 9),
                    'logo_uri': token.get('logo_uri', ''),
                    'tags': token.get('tags', []),
                    'daily_volume': token.get('daily_volume', 0),
                    'freeze_authority': token.get('freeze_authority'),
                    'mint_authority': token.get('mint_authority'),
                    'permanent_delegate': token.get('permanent_delegate'),
                    'minted_at': token.get('minted_at'),
                    'extensions': token.get('extensions', {}),
                    'discovery_source': 'jupiter_token_list',
                    'risk_level': token.get('risk_level', 'MEDIUM')
                }
                self.enhanced_cache.register_tracked_token(addr)
        
        # Process Jupiter quote analysis (liquidity-focused EMERGING tokens)
        for token in platform_data.get('jupiter_quote_analysis', []):
            addr = token.get('address', '')
            if addr and addr not in self.excluded_addresses:
                # Add Jupiter quote analysis as additional platform signal
                normalized[addr]['platforms'].add('jupiter_quotes')
                
                # Create or update Jupiter data with quote analysis
                if 'jupiter' not in normalized[addr]['data']:
                    normalized[addr]['data']['jupiter'] = {}
                
                normalized[addr]['data']['jupiter'].update({
                    'input_amount': token.get('input_amount', 0),
                    'output_amount': token.get('output_amount', 0),
                    'price_impact_pct': token.get('price_impact_pct', 0),
                    'route_plan': token.get('route_plan', []),
                    'swap_mode': token.get('swap_mode', ''),
                    'slippage_bps': token.get('slippage_bps', 50),
                    'liquidity_score': token.get('liquidity_score', 0),
                    'routing_complexity': token.get('routing_complexity', 0),
                    'discovery_source': 'jupiter_quote_analysis',
                    'quote_timestamp': token.get('timestamp', 0),
                    'has_liquidity_analysis': True
                })
                self.enhanced_cache.register_tracked_token(addr)
        
        # Process Meteora volume trending (pool-based EMERGING tokens)
        for token in platform_data.get('meteora_volume_trending', []):
            addr = token.get('address', '')
            if addr and addr not in self.excluded_addresses:
                normalized[addr]['platforms'].add('meteora')
                meteora_data = {
                    'symbol': token.get('symbol', ''),
                    'pool_address': token.get('pool_address', ''),
                    'volume_24h': token.get('volume_24h', 0),
                    'tvl': token.get('tvl', 0),
                    'vlr': token.get('vlr', 0),  # Volume-to-Liquidity Ratio
                    'fees_24h': token.get('fees_24h', 0),
                    'apr': token.get('apr', 0),
                    'liquidity_x': token.get('liquidity_x', 0),
                    'liquidity_y': token.get('liquidity_y', 0),
                    'price': token.get('price', 0),
                    'price_change_24h': token.get('price_change_24h', 0),
                    'discovery_source': 'meteora_volume_trending',
                    'pool_type': token.get('pool_type', 'CLMM'),
                    'meteora_score': token.get('meteora_score', 0),
                    'timestamp': token.get('timestamp', 0)
                }
                
                # Add WSOL pair flag if present in source data
                if token.get('is_wsol_pair'):
                    meteora_data['is_wsol_pair'] = True
                
                normalized[addr]['data']['meteora'] = meteora_data
                self.enhanced_cache.register_tracked_token(addr)
        
        # Process Jupiter batch pricing (ENHANCED pricing data)
        for token in platform_data.get('jupiter_batch_prices', []):
            addr = token.get('address', '')
            if addr and addr not in self.excluded_addresses:
                normalized[addr]['platforms'].add('jupiter_pricing')
                price_data = token.get('price_data', {})
                
                # Defensive programming: ensure price_data is a dictionary
                if not isinstance(price_data, dict):
                    if self.logger:
                        self.logger.warning(f"⚠️ Jupiter price_data for {addr[:8]}... is not a dict: {type(price_data)} = {price_data}")
                    price_data = {}
                
                # Create or update Jupiter data with pricing
                if 'jupiter' not in normalized[addr]['data']:
                    normalized[addr]['data']['jupiter'] = {}
                
                try:
                    normalized[addr]['data']['jupiter'].update({
                        'price': price_data.get('price', 0),
                        'vs_token': price_data.get('vs_token', 'USDC'),
                        'price_source': price_data.get('source', 'jupiter_lite_api_price_v2'),
                        'price_timestamp': price_data.get('timestamp', time.time()),
                        'has_pricing_data': True,
                        'discovery_source': token.get('discovery_source', 'jupiter_batch_pricing')
                    })
                except Exception as e:
                    if self.logger:
                        self.logger.error(f"❌ Error processing Jupiter pricing for {addr[:8]}...: {e}")
                        self.logger.error(f"🔍 token data: {token}")
                        self.logger.error(f"🔍 price_data type: {type(price_data)}, value: {price_data}")
                    continue
                    
                self.enhanced_cache.register_tracked_token(addr)
        
        # Process Orca trending pools (DEX liquidity data) - WSOL-Only filtering
        for pool in platform_data.get('orca_trending_pools', []):
            # Extract token addresses from pool data
            token_a_addr = pool.get('token_a', {}).get('address', '')
            token_b_addr = pool.get('token_b', {}).get('address', '')
            
            if WSOL_ONLY_MODE:
                # Only process WSOL pairs
                target_token = None
                if token_a_addr == WSOL_ADDRESS and token_b_addr and token_b_addr not in self.excluded_addresses:
                    target_token = token_b_addr
                elif token_b_addr == WSOL_ADDRESS and token_a_addr and token_a_addr not in self.excluded_addresses:
                    target_token = token_a_addr
                
                if target_token:
                    normalized[target_token]['platforms'].add('orca')
                    normalized[target_token]['data']['orca'] = {
                        'pool_address': pool.get('address', ''),
                        'liquidity_usd': pool.get('liquidity_usd', 0),
                        'volume_24h': pool.get('volume_24h', 0),
                        'fee_tier': pool.get('fee_tier', 0),
                        'apr': pool.get('apr', 0),
                        'pool_type': 'whirlpool',
                        'discovery_source': 'orca_trending_pools',
                        'timestamp': pool.get('timestamp', 0),
                        'is_wsol_pair': True
                    }
                    self.enhanced_cache.register_tracked_token(target_token)
                    logging.debug(f"🌀 Found WSOL-{target_token[:8]}... pair in Orca")
            else:
                # Original logic: process all non-excluded tokens
                for addr in [token_a_addr, token_b_addr]:
                    if addr and addr not in self.excluded_addresses:
                        normalized[addr]['platforms'].add('orca')
                        normalized[addr]['data']['orca'] = {
                            'pool_address': pool.get('address', ''),
                            'liquidity_usd': pool.get('liquidity_usd', 0),
                            'volume_24h': pool.get('volume_24h', 0),
                            'fee_tier': pool.get('fee_tier', 0),
                            'apr': pool.get('apr', 0),
                            'pool_type': 'whirlpool',
                            'discovery_source': 'orca_trending_pools',
                            'timestamp': pool.get('timestamp', 0)
                        }
                        self.enhanced_cache.register_tracked_token(addr)
        
        # Process Raydium trending pairs (DEX liquidity data) - WSOL-Only filtering
        for pair in platform_data.get('raydium_trending_pairs', []):
            # Extract token addresses from pair data
            base_mint = pair.get('base_mint', '')
            quote_mint = pair.get('quote_mint', '')
            
            if WSOL_ONLY_MODE:
                # Only process WSOL pairs
                target_token = None
                if base_mint == WSOL_ADDRESS and quote_mint and quote_mint not in self.excluded_addresses:
                    target_token = quote_mint
                elif quote_mint == WSOL_ADDRESS and base_mint and base_mint not in self.excluded_addresses:
                    target_token = base_mint
                
                if target_token:
                    normalized[target_token]['platforms'].add('raydium')
                    normalized[target_token]['data']['raydium'] = {
                        'pair_address': pair.get('address', ''),
                        'liquidity_usd': pair.get('liquidity_usd', 0),
                        'volume_24h': pair.get('volume_24h', 0),
                        'apr': pair.get('apr', 0),
                        'pool_type': pair.get('pool_type', 'AMM'),
                        'discovery_source': 'raydium_trending_pairs',
                        'timestamp': pair.get('timestamp', 0),
                        'is_wsol_pair': True
                    }
                    self.enhanced_cache.register_tracked_token(target_token)
                    logging.debug(f"⚡ Found WSOL-{target_token[:8]}... pair in Raydium")
            else:
                # Original logic: process all non-excluded tokens
                for addr in [base_mint, quote_mint]:
                    if addr and addr not in self.excluded_addresses:
                        normalized[addr]['platforms'].add('raydium')
                        normalized[addr]['data']['raydium'] = {
                            'pair_address': pair.get('address', ''),
                            'liquidity_usd': pair.get('liquidity_usd', 0),
                            'volume_24h': pair.get('volume_24h', 0),
                            'apr': pair.get('apr', 0),
                            'pool_type': pair.get('pool_type', 'AMM'),
                            'discovery_source': 'raydium_trending_pairs',
                            'timestamp': pair.get('timestamp', 0)
                        }
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
    
    async def analyze_correlations(self, normalized_data: Dict[str, Dict]) -> Dict[str, Any]:
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
            },
            'platform_analysis': {
                'distribution': {},
                'platform_effectiveness': {},
                'top_tokens_by_platform': {},
                'platform_insights': []
            }
        }
        
        # Track boost statistics
        total_boost_amount = 0
        boost_count = 0
        
        # Analyze platform distribution and build all_tokens
        try:
            for token_addr, token_data in normalized_data.items():
                try:
                    # Defensive programming: ensure token_data is a dictionary
                    if not isinstance(token_data, dict):
                        if self.logger:
                            self.logger.warning(f"⚠️ Token data for {token_addr[:8]}... is not a dict: {type(token_data)} = {token_data}")
                        continue
                    
                    # Ensure required keys exist
                    if 'platforms' not in token_data or 'data' not in token_data:
                        if self.logger:
                            self.logger.warning(f"⚠️ Token data for {token_addr[:8]}... missing required keys: {list(token_data.keys())}")
                        continue
                    
                    platforms = token_data['platforms']
                    if not isinstance(platforms, (set, list)):
                        if self.logger:
                            self.logger.warning(f"⚠️ Platforms for {token_addr[:8]}... is not a set/list: {type(platforms)} = {platforms}")
                        continue
                        
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
                        'price_change_24h': 0,
                        'data': token_data['data']  # CRITICAL: Preserve platform-specific data including is_wsol_pair flags
                    }
                    
                    # Enhanced symbol/name extraction with priority order: Birdeye > Narratives > DexScreener > API Fallback
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
                    
                    # Priority 4: Mark for API fallback resolution if still no symbol
                    if not symbol_found or token_info['symbol'] == 'Unknown':
                        token_info['needs_symbol_resolution'] = True
                    
                    # Log symbol extraction for debugging
                    if self.logger:
                        if symbol_found and token_info['symbol'] != 'Unknown':
                            self.logger.debug(f"🏷️ Extracted symbol '{token_info['symbol']}' for {token_addr[:8]}...")
                        else:
                            self.logger.debug(f"⚠️ No symbol found for {token_addr[:8]}..., keeping as 'Unknown'")
                    
                    # Add VLR analysis if available
                    if self.vlr_intelligence:
                        try:
                            vlr_token_data = {
                                'address': token_addr,
                                'symbol': token_info['symbol'],
                                'volume_24h': token_info['volume_24h'],
                                'liquidity': token_info['liquidity'],
                                'market_cap': token_info['market_cap']
                            }
                            
                            vlr_analysis = self.vlr_intelligence.analyze_token_vlr(vlr_token_data)
                            
                            # Add VLR data to token info
                            token_info['vlr_analysis'] = {
                                'vlr': vlr_analysis.vlr,
                                'category': vlr_analysis.category.value,
                                'gem_stage': vlr_analysis.gem_stage.value,
                                'risk_level': vlr_analysis.risk_level.value,
                                'gem_potential': vlr_analysis.gem_potential,
                                'lp_attractiveness': vlr_analysis.lp_attractiveness,
                                'expected_apy': vlr_analysis.expected_apy,
                                'position_recommendation': vlr_analysis.position_recommendation,
                                'investment_strategy': vlr_analysis.investment_strategy,
                                'risk_warnings': vlr_analysis.risk_warnings
                            }
                            
                            # Add VLR score to overall token score (weighted)
                            vlr_score_weight = 0.2  # 20% weight for VLR analysis
                            vlr_normalized_score = min(vlr_analysis.vlr * 10, 100)  # Normalize VLR to 0-100 scale
                            token_score_with_vlr = (token_score * 0.8) + (vlr_normalized_score * vlr_score_weight)
                            token_info['score'] = token_score_with_vlr
                            
                            self.logger.debug(f"🧠 VLR analysis for {token_info['symbol']}: VLR={vlr_analysis.vlr:.2f}, Category={vlr_analysis.category.value}")
                            
                        except Exception as e:
                            self.logger.warning(f"⚠️ VLR analysis failed for {token_addr[:8]}...: {e}")
                            token_info['vlr_analysis'] = {}
                    else:
                        token_info['vlr_analysis'] = {}
                    
                    # Store in all_tokens
                    correlations['all_tokens'][token_addr] = token_info
                    
                    # Platform analysis - track platform effectiveness
                    primary_platform = list(platforms)[0] if platforms else 'unknown'
                    
                    # Update platform distribution
                    for platform in platforms:
                        if platform not in correlations['platform_analysis']['distribution']:
                            correlations['platform_analysis']['distribution'][platform] = 0
                        correlations['platform_analysis']['distribution'][platform] += 1
                        
                        # Track platform effectiveness
                        if platform not in correlations['platform_analysis']['platform_effectiveness']:
                            correlations['platform_analysis']['platform_effectiveness'][platform] = {
                                'token_count': 0,
                                'total_score': 0,
                                'high_conviction_count': 0
                            }
                        
                        correlations['platform_analysis']['platform_effectiveness'][platform]['token_count'] += 1
                        correlations['platform_analysis']['platform_effectiveness'][platform]['total_score'] += token_score
                        
                        if token_score >= 70.0:
                            correlations['platform_analysis']['platform_effectiveness'][platform]['high_conviction_count'] += 1
                    
                    # Add to platform-specific token lists (top 5 per platform)
                    for platform in platforms:
                        if platform not in correlations['platform_analysis']['top_tokens_by_platform']:
                            correlations['platform_analysis']['top_tokens_by_platform'][platform] = []
                        
                        platform_token_info = {
                            'address': token_addr,
                            'symbol': token_info['symbol'],
                            'score': token_score,
                            'platforms': list(platforms),
                            'platform_count': len(platforms)
                        }
                        
                        platform_list = correlations['platform_analysis']['top_tokens_by_platform'][platform]
                        platform_list.append(platform_token_info)
                        platform_list.sort(key=lambda x: x['score'], reverse=True)
                        correlations['platform_analysis']['top_tokens_by_platform'][platform] = platform_list[:5]  # Keep top 5
                    
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
                
                except Exception as e:
                    if self.logger:
                        self.logger.error(f"❌ Error processing token {token_addr}: {e}")
                        self.logger.error(f"🔍 Token data: {token_data}")
                    continue
        
        except Exception as e:
            if self.logger:
                self.logger.error(f"❌ Error in analyze_correlations: {e}")
            raise
        
        # Calculate average boost amount
        if boost_count > 0:
            correlations['boost_analysis']['average_boost_amount'] = total_boost_amount / boost_count
        
        # Sort multi-platform tokens by score
        correlations['multi_platform_tokens'].sort(key=lambda x: x['score'], reverse=True)
        
        # Identify high conviction tokens (present on 2+ platforms with good metrics)
        for token in correlations['multi_platform_tokens']:
            if token['score'] >= 50.0:  # Lowered since single platform tokens get 0 validation points
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
        
        # Calculate platform effectiveness metrics
        for platform, effectiveness in correlations['platform_analysis']['platform_effectiveness'].items():
            token_count = effectiveness['token_count']
            if token_count > 0:
                effectiveness['avg_score'] = round(effectiveness['total_score'] / token_count, 1)
                effectiveness['high_conviction_rate'] = round((effectiveness['high_conviction_count'] / token_count) * 100, 1)
        
        # Generate platform insights
        platform_insights = []
        total_tokens = len(normalized_data)
        
        for platform, count in correlations['platform_analysis']['distribution'].items():
            if count > 0:
                percentage = (count / total_tokens) * 100
                effectiveness = correlations['platform_analysis']['platform_effectiveness'][platform]
                avg_score = effectiveness['avg_score']
                hc_rate = effectiveness['high_conviction_rate']
                platform_insights.append(f"{platform}: {count} tokens ({percentage:.1f}%), avg score: {avg_score}, {hc_rate}% high conviction")
        
        correlations['platform_analysis']['platform_insights'] = platform_insights
        
        # Add VLR intelligence summary if available
        if self.vlr_intelligence:
            vlr_summary = self._generate_vlr_summary(correlations['all_tokens'])
            correlations['vlr_analysis'] = vlr_summary
            self.logger.info(f"🧠 VLR Analysis Summary: {vlr_summary.get('total_analyzed', 0)} tokens analyzed")
        else:
            correlations['vlr_analysis'] = {'status': 'VLR Intelligence not available'}
        
        # Batch resolve missing symbols using DexScreener individual token API
        await self._resolve_missing_symbols(correlations)
        
        return correlations
    
    def _generate_vlr_summary(self, all_tokens: Dict[str, Dict]) -> Dict[str, Any]:
        """Generate comprehensive VLR analysis summary"""
        vlr_summary = {
            'total_analyzed': 0,
            'category_breakdown': {
                '🔍 Gem Discovery': [],
                '🚀 Momentum Building': [],
                '💰 Peak Performance': [],
                '⚠️ Danger Zone': [],
                '🚨 Manipulation': []
            },
            'gem_candidates': [],
            'lp_opportunities': [],
            'risk_alerts': [],
            'top_vlr_tokens': [],
            'statistics': {
                'avg_vlr': 0,
                'vlr_range': [0, 0],
                'high_potential_count': 0,
                'high_risk_count': 0
            }
        }
        
        vlr_values = []
        
        for token_addr, token_info in all_tokens.items():
            vlr_analysis = token_info.get('vlr_analysis', {})
            if not vlr_analysis:
                continue
            
            vlr_summary['total_analyzed'] += 1
            vlr = vlr_analysis.get('vlr', 0)
            category = vlr_analysis.get('category', 'Unknown')
            gem_potential = vlr_analysis.get('gem_potential', 'LOW')
            risk_level = vlr_analysis.get('risk_level', 'HIGH')
            lp_attractiveness = vlr_analysis.get('lp_attractiveness', 0)
            
            vlr_values.append(vlr)
            
            # Categorize tokens
            if category in vlr_summary['category_breakdown']:
                vlr_summary['category_breakdown'][category].append({
                    'address': token_addr,
                    'symbol': token_info.get('symbol', 'Unknown'),
                    'vlr': vlr,
                    'score': token_info.get('score', 0),
                    'platforms': token_info.get('platforms', [])
                })
            
            # Identify gem candidates
            if gem_potential == 'HIGH':
                vlr_summary['gem_candidates'].append({
                    'address': token_addr,
                    'symbol': token_info.get('symbol', 'Unknown'),
                    'vlr': vlr,
                    'gem_stage': vlr_analysis.get('gem_stage', 'Unknown'),
                    'investment_strategy': vlr_analysis.get('investment_strategy', ''),
                    'platforms': token_info.get('platforms', [])
                })
                vlr_summary['statistics']['high_potential_count'] += 1
            
            # Identify LP opportunities
            if lp_attractiveness >= 70:
                vlr_summary['lp_opportunities'].append({
                    'address': token_addr,
                    'symbol': token_info.get('symbol', 'Unknown'),
                    'vlr': vlr,
                    'lp_attractiveness': lp_attractiveness,
                    'expected_apy': vlr_analysis.get('expected_apy', 0),
                    'position_recommendation': vlr_analysis.get('position_recommendation', ''),
                    'platforms': token_info.get('platforms', [])
                })
            
            # Identify risk alerts
            if risk_level in ['HIGH', 'CRITICAL'] or '🚨 Manipulation' in category or '⚠️ Danger Zone' in category:
                vlr_summary['risk_alerts'].append({
                    'address': token_addr,
                    'symbol': token_info.get('symbol', 'Unknown'),
                    'vlr': vlr,
                    'risk_level': risk_level,
                    'category': category,
                    'risk_warnings': vlr_analysis.get('risk_warnings', []),
                    'platforms': token_info.get('platforms', [])
                })
                vlr_summary['statistics']['high_risk_count'] += 1
            
            # Add to top VLR tokens
            vlr_summary['top_vlr_tokens'].append({
                'address': token_addr,
                'symbol': token_info.get('symbol', 'Unknown'),
                'vlr': vlr,
                'category': category,
                'score': token_info.get('score', 0),
                'platforms': token_info.get('platforms', [])
            })
        
        # Calculate statistics
        if vlr_values:
            vlr_summary['statistics']['avg_vlr'] = sum(vlr_values) / len(vlr_values)
            vlr_summary['statistics']['vlr_range'] = [min(vlr_values), max(vlr_values)]
        
        # Sort lists by relevance
        vlr_summary['gem_candidates'].sort(key=lambda x: x['vlr'], reverse=True)
        vlr_summary['lp_opportunities'].sort(key=lambda x: x['lp_attractiveness'], reverse=True)
        vlr_summary['risk_alerts'].sort(key=lambda x: x['vlr'], reverse=True)
        vlr_summary['top_vlr_tokens'].sort(key=lambda x: x['vlr'], reverse=True)
        
        # Limit lists for performance
        vlr_summary['gem_candidates'] = vlr_summary['gem_candidates'][:10]
        vlr_summary['lp_opportunities'] = vlr_summary['lp_opportunities'][:10]
        vlr_summary['risk_alerts'] = vlr_summary['risk_alerts'][:10]
        vlr_summary['top_vlr_tokens'] = vlr_summary['top_vlr_tokens'][:20]
        
        return vlr_summary
    
    async def _resolve_missing_symbols(self, correlations: Dict[str, Any]) -> None:
        """Resolve missing symbols using DexScreener individual token API"""
        tokens_needing_resolution = []
        
        # Find tokens that need symbol resolution
        for token_addr, token_info in correlations['all_tokens'].items():
            if token_info.get('needs_symbol_resolution', False):
                tokens_needing_resolution.append(token_addr)
        
        if not tokens_needing_resolution:
            return
        
        self.logger.info(f"🔍 Resolving symbols for {len(tokens_needing_resolution)} tokens using DexScreener API...")
        
        # Use a single session for all requests with timeout
        import aiohttp
        timeout = aiohttp.ClientTimeout(total=10)  # 10 second timeout per request
        
        async with aiohttp.ClientSession(timeout=timeout) as session:
            # Process in small batches to avoid rate limits
            batch_size = 5
            resolved_count = 0
            
            for i in range(0, len(tokens_needing_resolution), batch_size):
                batch = tokens_needing_resolution[i:i + batch_size]
                
                # Process batch concurrently
                tasks = []
                for token_addr in batch:
                    url = f"https://api.dexscreener.com/latest/dex/tokens/{token_addr}"
                    tasks.append(self._resolve_single_symbol(session, token_addr, url, correlations))
                
                # Execute batch concurrently
                batch_results = await asyncio.gather(*tasks, return_exceptions=True)
                
                # Count successful resolutions
                for result in batch_results:
                    if result is True:  # Successful resolution
                        resolved_count += 1
                    elif isinstance(result, Exception):
                        self.logger.debug(f"❌ Symbol resolution task failed: {result}")
                
                # Progress update
                progress = min(i + batch_size, len(tokens_needing_resolution))
                self.logger.info(f"📊 Symbol resolution progress: {progress}/{len(tokens_needing_resolution)} tokens processed")
                
                # Delay between batches
                if i + batch_size < len(tokens_needing_resolution):
                    await asyncio.sleep(0.5)  # Reduced delay for better performance
        
        # Clean up resolution flags
        for token_addr in tokens_needing_resolution:
            if token_addr in correlations['all_tokens']:
                correlations['all_tokens'][token_addr].pop('needs_symbol_resolution', None)
        
        self.logger.info(f"✅ Symbol resolution completed: {resolved_count}/{len(tokens_needing_resolution)} symbols resolved")
    
    async def _resolve_single_symbol(self, session: aiohttp.ClientSession, token_addr: str, url: str, correlations: Dict[str, Any]) -> bool:
        """Resolve a single token symbol"""
        try:
            async with session.get(url) as response:
                if response.status == 200:
                    data = await response.json()
                    pairs = data.get('pairs', [])
                    
                    if pairs:
                        # Use first pair's base token info
                        base_token = pairs[0].get('baseToken', {})
                        symbol = base_token.get('symbol', '').strip()
                        name = base_token.get('name', '').strip()
                        
                        if symbol and symbol != 'Unknown':
                            # Update token info
                            token_info = correlations['all_tokens'][token_addr]
                            token_info['symbol'] = symbol
                            if name:
                                token_info['name'] = name
                            
                            # Update in multi_platform_tokens as well
                            for mp_token in correlations['multi_platform_tokens']:
                                if mp_token['address'] == token_addr:
                                    mp_token['symbol'] = symbol
                                    if name:
                                        mp_token['name'] = name
                                    break
                            
                            # Update in high_conviction_tokens as well
                            for hc_token in correlations['high_conviction_tokens']:
                                if hc_token['address'] == token_addr:
                                    hc_token['symbol'] = symbol
                                    if name:
                                        hc_token['name'] = name
                                    break
                            
                            self.logger.debug(f"✅ Resolved {token_addr[:8]}... -> {symbol}")
                            return True
                        
        except Exception as e:
            self.logger.debug(f"❌ Failed to resolve symbol for {token_addr[:8]}...: {e}")
        
        return False
    
    def _calculate_token_score(self, token_data: Dict) -> float:
        """
        Calculate token score using INTERACTION-BASED SCORING.
        
        MATHEMATICAL FIX:
        OLD (WRONG): score = platform_score + boost_score + volume_score + ...
        NEW (CORRECT): score = f(interactions, amplifications, contradictions)
        """
        try:
            # Import interaction scoring system
            from scripts.interaction_based_scoring_system import InteractionBasedScorer, FactorValues
            
            # Initialize interaction scorer for cross-platform analysis
            if not hasattr(self, '_cross_platform_interaction_scorer'):
                self._cross_platform_interaction_scorer = InteractionBasedScorer(debug_mode=False)
            
            # Calculate traditional components (for comparison)
            traditional_components = self._calculate_cross_platform_traditional_components(token_data)
            
            # Extract normalized factor values
            factor_values = self._extract_cross_platform_factor_values(token_data)
            
            # Apply interaction-based scoring (THE FIX)
            final_score, interaction_analysis = self._cross_platform_interaction_scorer.calculate_interaction_based_score(
                factor_values, traditional_components
            )
            
            # Log improvement for debugging
            linear_score = sum(traditional_components.values()) if traditional_components else 0
            if hasattr(self, 'logger') and self.logger:
                self.logger.debug(f"🧠 Cross-Platform Interaction Fix:")
                self.logger.debug(f"   📊 Linear (Flawed): {linear_score:.1f}")
                self.logger.debug(f"   🚀 Interaction (Fixed): {final_score:.1f}")
                self.logger.debug(f"   📈 Improvement: {((final_score - linear_score) / max(linear_score, 1)) * 100:+.1f}%")
            
            return final_score
            
        except Exception as e:
            # Fallback to linear method with warning
            if hasattr(self, 'logger') and self.logger:
                self.logger.warning(f"⚠️ Cross-platform interaction scoring failed: {e}")
                self.logger.warning("🚨 USING LINEAR FALLBACK - MATHEMATICAL FLAW ACTIVE")
            
            return self._calculate_token_score_linear_fallback(token_data)
    
    def _calculate_cross_platform_traditional_components(self, token_data: Dict) -> Dict[str, float]:
        """Calculate traditional component scores for baseline comparison"""
        platforms = len(token_data.get('platforms', []))
        
        # Platform validation score (cross-platform bonus)
        platform_score = 0
        if platforms >= 2:
            platform_score = (platforms - 1) * 8.0  # 2 platforms=8, 3=16, etc.
        
        # DexScreener analysis
        dexscreener_score = 0
        if 'dexscreener' in token_data.get('data', {}):
            ds_data = token_data['data']['dexscreener']
            
            # Golden ticker bonus
            if ds_data.get('is_golden_ticker', False):
                dexscreener_score += 15.0
            
            # Boost intensity scoring
            boost_intensity = ds_data.get('boost_intensity', 'MINIMAL_BOOST')
            boost_scores = {
                'GOLDEN_TICKER': 12.0, 'MEGA_BOOST': 10.0, 'HIGH_BOOST': 8.0,
                'MEDIUM_BOOST': 6.0, 'LOW_BOOST': 4.0, 'MINIMAL_BOOST': 2.0
            }
            if not ds_data.get('is_golden_ticker', False):  # Avoid double counting
                dexscreener_score += boost_scores.get(boost_intensity, 0)
            
            # Trending multiplier impact
            trending_multiplier = ds_data.get('trending_score_multiplier', 1.0)
            if trending_multiplier > 2.0:
                dexscreener_score += 8.0
            elif trending_multiplier > 1.5:
                dexscreener_score += 5.0
            elif trending_multiplier > 1.1:
                dexscreener_score += 2.0
            
            # Investment commitment (boost total)
            boost_total = ds_data.get('boost_total', 0)
            if boost_total >= 1000:
                dexscreener_score += 8.0
            elif boost_total >= 500:
                dexscreener_score += 6.0
            elif boost_total >= 100:
                dexscreener_score += 4.0
            elif boost_total >= 50:
                dexscreener_score += 2.0
        
        # RugCheck community sentiment
        rugcheck_score = 0
        if 'rugcheck' in token_data.get('data', {}):
            sentiment = token_data['data']['rugcheck'].get('sentiment_score', 0)
            if sentiment >= 0.8:
                rugcheck_score += 10.0
            elif sentiment >= 0.6:
                rugcheck_score += 6.0
            elif sentiment >= 0.4:
                rugcheck_score += 3.0
        
        # Birdeye trading metrics
        birdeye_score = 0
        if 'birdeye' in token_data.get('data', {}):
            be_data = token_data['data']['birdeye']
            volume_24h = be_data.get('volume_24h_usd', 0)
            price_change = be_data.get('price_change_24h', 0)
            
            # Volume scoring
            if volume_24h >= 1000000:
                birdeye_score += 8.0
            elif volume_24h >= 500000:
                birdeye_score += 6.0
            elif volume_24h >= 100000:
                birdeye_score += 4.0
            elif volume_24h >= 50000:
                birdeye_score += 2.0
            
            # Price momentum
            if price_change >= 50:
                birdeye_score += 8.0
            elif price_change >= 20:
                birdeye_score += 5.0
            elif price_change >= 10:
                birdeye_score += 3.0
            elif price_change >= 5:
                birdeye_score += 1.0
        
        return {
            'platform_score': platform_score,
            'dexscreener_score': dexscreener_score,
            'rugcheck_score': rugcheck_score,
            'birdeye_score': birdeye_score
        }
    
    def _extract_cross_platform_factor_values(self, token_data: Dict) -> 'FactorValues':
        """Extract normalized factor values for interaction analysis"""
        platforms_count = len(token_data.get('platforms', []))
        
        # Check if FactorValues is available
        try:
            from scripts.interaction_based_scoring_system import FactorValues
        except ImportError:
            # Return a basic dict if FactorValues is not available
            if hasattr(self, 'logger') and self.logger:
                self.logger.warning("⚠️ FactorValues not available - returning basic factor dict")
            return {
                'vlr_ratio': 0.0,
                'liquidity': 0.0,
                'smart_money_score': 0.0,
                'volume_momentum': 0.0,
                'security_score': 0.5,
                'whale_concentration': 0.0,
                'price_momentum': 0.0,
                'cross_platform_validation': 0.0,
                'age_factor': 0.5
            }
        
        # Extract raw values from different platforms
        raw_volume = 0
        raw_liquidity = 0
        price_change = 0
        boost_amount = 0
        sentiment = 0.5  # Default neutral
        
        # Birdeye data
        if 'birdeye' in token_data.get('data', {}):
            be_data = token_data['data']['birdeye']
            raw_volume = be_data.get('volume_24h_usd', 0)
            raw_liquidity = be_data.get('liquidity', 0)
            price_change = be_data.get('price_change_24h', 0)
        
        # DexScreener boost data
        if 'dexscreener' in token_data.get('data', {}):
            ds_data = token_data['data']['dexscreener']
            boost_amount = ds_data.get('boost_amount', 0)
        
        # RugCheck sentiment
        if 'rugcheck' in token_data.get('data', {}):
            sentiment = token_data['data']['rugcheck'].get('sentiment_score', 0.5)
        
        # Normalize values to 0-1 scale for interaction analysis
        volume_momentum = min(1.0, raw_volume / 5000000) if raw_volume > 0 else 0
        liquidity = min(1.0, raw_liquidity / 1000000) if raw_liquidity > 0 else 0
        price_momentum = min(1.0, abs(price_change) / 100) if price_change != 0 else 0
        cross_platform_validation = min(1.0, platforms_count / 5.0)
        
        # Use boost amount as proxy for smart money interest
        smart_money_score = min(1.0, boost_amount / 1000) if boost_amount > 0 else 0
        
        # Use sentiment as security proxy
        security_score = max(0, sentiment) if sentiment > 0 else 0.5
        
        return FactorValues(
            vlr_ratio=0.0,  # Not applicable for cross-platform
            liquidity=liquidity,
            smart_money_score=smart_money_score,
            volume_momentum=volume_momentum,
            security_score=security_score,
            whale_concentration=0.0,  # Not available in cross-platform data
            price_momentum=price_momentum,
            cross_platform_validation=cross_platform_validation,
            age_factor=0.5,  # Default neutral
            raw_vlr=0,
            raw_liquidity=raw_liquidity,
            raw_volume_24h=raw_volume,
            platforms_count=platforms_count
        )
    
    def _calculate_token_score_linear_fallback(self, token_data: Dict) -> float:
        """Fallback to original linear scoring (WITH MATHEMATICAL FLAW)"""
        if hasattr(self, 'logger') and self.logger:
            self.logger.warning("🚨 LINEAR ADDITIVITY FALLBACK ACTIVE - MATHEMATICAL FLAW PRESENT")
        
        # Original flawed linear logic
        score = 0.0
        platforms = len(token_data.get('platforms', []))
        
        # Linear addition (MATHEMATICALLY INCORRECT)
        if platforms >= 2:
            score += (platforms - 1) * 8.0
        
        if 'dexscreener' in token_data.get('data', {}):
            ds_data = token_data['data']['dexscreener']
            if ds_data.get('is_golden_ticker', False):
                score += 15.0
            
            boost_intensity = ds_data.get('boost_intensity', 'MINIMAL_BOOST')
            boost_scores = {
                'MEGA_BOOST': 10.0, 'HIGH_BOOST': 8.0, 'MEDIUM_BOOST': 6.0,
                'LOW_BOOST': 4.0, 'MINIMAL_BOOST': 2.0
            }
            score += boost_scores.get(boost_intensity, 0)
        
        if 'rugcheck' in token_data.get('data', {}):
            sentiment = token_data['data']['rugcheck'].get('sentiment_score', 0)
            if sentiment >= 0.8:
                score += 10.0
            elif sentiment >= 0.6:
                score += 6.0
            elif sentiment >= 0.4:
                score += 3.0
        
        if 'birdeye' in token_data.get('data', {}):
            be_data = token_data['data']['birdeye']
            volume_24h = be_data.get('volume_24h_usd', 0)
            if volume_24h >= 1000000:
                score += 8.0
            elif volume_24h >= 500000:
                score += 6.0
            elif volume_24h >= 100000:
                score += 4.0
            elif volume_24h >= 50000:
                score += 2.0
        
        return score

    
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
            batch_size = 30  # Optimized based on testing
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
        
        # WSOL filtering status insight
        if WSOL_ONLY_MODE:
            insights.append(f"🪙 WSOL-Only Analysis: Focusing exclusively on WSOL-paired tokens for maximum liquidity and reliability")
        
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
            platforms = self._format_platform_display(top_token['platforms'])
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
        
        # Platform effectiveness insights
        platform_analysis = correlations.get('platform_analysis', {})
        if platform_analysis:
            distribution = platform_analysis.get('distribution', {})
            effectiveness = platform_analysis.get('platform_effectiveness', {})
            
            # Find most effective platforms
            best_platforms = []
            for platform, metrics in effectiveness.items():
                if metrics.get('token_count', 0) >= 5:  # Only consider platforms with 5+ tokens
                    best_platforms.append((platform, metrics.get('avg_score', 0), metrics.get('high_conviction_rate', 0)))
            
            best_platforms.sort(key=lambda x: x[1], reverse=True)  # Sort by average score
            
            if best_platforms:
                top_platform = best_platforms[0]
                insights.append(f"🏆 Most effective platform: {top_platform[0]} (avg score: {top_platform[1]}, {top_platform[2]}% high conviction)")
            
            # Jupiter/Meteora specific insights
            jupiter_count = distribution.get('jupiter', 0) + distribution.get('jupiter_quotes', 0)
            meteora_count = distribution.get('meteora', 0)
            
            if jupiter_count > 0:
                insights.append(f"🪙 Jupiter discovery: {jupiter_count} tokens with emerging potential")
            
            if meteora_count > 0:
                insights.append(f"🌊 Meteora pools: {meteora_count} tokens with active trading")
            
            # Cross-platform validation insights
            multi_platform_count = len(correlations.get('multi_platform_tokens', []))
            if multi_platform_count > 0:
                validation_rate = (multi_platform_count / total_tokens) * 100
                insights.append(f"✅ Cross-platform validation: {multi_platform_count} tokens ({validation_rate:.1f}%) on multiple platforms")
        
        # Cache performance insights
        cache_stats = self.enhanced_cache.get_cache_statistics()
        if cache_stats['cache_hits'] + cache_stats['cache_misses'] > 0:
            insights.append(f"Cache efficiency: {cache_stats['hit_rate_percent']:.1f}% hit rate")
            insights.append(f"Estimated cost savings: ${cache_stats['estimated_cost_savings_usd']:.4f}")
        
        return insights

    def _format_platform_display(self, platforms):
        """
        Enhanced platform display formatting with icons, grouping, and smart abbreviations
        
        Args:
            platforms: List of platform names
            
        Returns:
            Formatted string for display in table
        """
        if not platforms:
            return "None"
        
        # Platform mapping with icons and smart abbreviations
        platform_mapping = {
            # Birdeye platforms
            'birdeye': '🐦BE',
            'birdeye_trending': '🐦BE',
            'birdeye_emerging_stars': '🐦BE★',
            'birdeye_cross_platform': '🐦BE✓',
            'birdeye_detailed_analysis': '🐦BE📊',
            'birdeye_whale_analysis': '🐦BE🐋',
            'birdeye_volume_analysis': '🐦BE📈',
            'birdeye_security_analysis': '🐦BE🛡️',
            'birdeye_community_analysis': '🐦BE👥',
            
            # DexScreener platforms
            'dexscreener': '📱DX',
            'dexscreener_boosted': '📱DX💰',
            'dexscreener_top': '📱DX🔝',
            'dexscreener_profiles': '📱DX👤',
            'dexscreener_narratives': '📱DX📝',
            
            # Jupiter platforms
            'jupiter': '🪐JUP',
            'jupiter_trending_quotes': '🪐JUP💱',
            'jupiter_quote': '🪐JUP💱',
            'jupiter_tokens': '🪐JUP📋',
            'jupiter_liquidity': '🪐JUP💧',
            
            # Meteora platforms
            'meteora': '🌊MET',
            'meteora_trending_pools': '🌊MET🏊',
            'meteora_volume': '🌊MET📊',
            
            # RugCheck platforms
            'rugcheck': '🛡️RUG',
            'rugcheck_trending': '🛡️RUG📈',
            'rugcheck_security': '🛡️RUG🔒',
        }
        
        # Group platforms by provider
        platform_groups = {
            'birdeye': [],
            'dexscreener': [],
            'jupiter': [],
            'meteora': [],
            'rugcheck': [],
            'other': []
        }
        
        # Categorize platforms
        for platform in platforms:
            if platform.startswith('birdeye'):
                platform_groups['birdeye'].append(platform)
            elif platform.startswith('dexscreener') or platform == 'dex':
                platform_groups['dexscreener'].append(platform)
            elif platform.startswith('jupiter'):
                platform_groups['jupiter'].append(platform)
            elif platform.startswith('meteora'):
                platform_groups['meteora'].append(platform)
            elif platform.startswith('rugcheck') or platform == 'rug':
                platform_groups['rugcheck'].append(platform)
            else:
                platform_groups['other'].append(platform)
        
        # Build display string
        display_parts = []
        
        # Birdeye group
        if platform_groups['birdeye']:
            birdeye_platforms = platform_groups['birdeye']
            if len(birdeye_platforms) == 1:
                display_parts.append(platform_mapping.get(birdeye_platforms[0], '🐦BE'))
            else:
                # Multiple birdeye endpoints - show count
                has_stars = any('stars' in p for p in birdeye_platforms)
                base_icon = '🐦BE★' if has_stars else '🐦BE'
                if len(birdeye_platforms) > 1:
                    display_parts.append(f"{base_icon}({len(birdeye_platforms)})")
                else:
                    display_parts.append(base_icon)
        
        # DexScreener group
        if platform_groups['dexscreener']:
            dex_platforms = platform_groups['dexscreener']
            if len(dex_platforms) == 1:
                platform_name = dex_platforms[0]
                if platform_name == 'dex':
                    platform_name = 'dexscreener'
                display_parts.append(platform_mapping.get(platform_name, '📱DX'))
            else:
                display_parts.append(f"📱DX({len(dex_platforms)})")
        
        # Jupiter group
        if platform_groups['jupiter']:
            jupiter_platforms = platform_groups['jupiter']
            if len(jupiter_platforms) == 1:
                display_parts.append(platform_mapping.get(jupiter_platforms[0], '🪐JUP'))
            else:
                display_parts.append(f"🪐JUP({len(jupiter_platforms)})")
        
        # Meteora group
        if platform_groups['meteora']:
            meteora_platforms = platform_groups['meteora']
            if len(meteora_platforms) == 1:
                display_parts.append(platform_mapping.get(meteora_platforms[0], '🌊MET'))
            else:
                display_parts.append(f"🌊MET({len(meteora_platforms)})")
        
        # RugCheck group
        if platform_groups['rugcheck']:
            rug_platforms = platform_groups['rugcheck']
            if len(rug_platforms) == 1:
                platform_name = rug_platforms[0]
                if platform_name == 'rug':
                    platform_name = 'rugcheck'
                display_parts.append(platform_mapping.get(platform_name, '🛡️RUG'))
            else:
                display_parts.append(f"🛡️RUG({len(rug_platforms)})")
        
        # Other platforms
        for platform in platform_groups['other']:
            if len(platform) > 8:
                display_parts.append(platform[:6] + '..')
            else:
                display_parts.append(platform)
        
        # Join with commas, but keep it concise
        result = ', '.join(display_parts)
        
        # If result is too long, use summary format
        if len(result) > 30:
            total_platforms = len(platforms)
            unique_providers = sum(1 for group in platform_groups.values() if group)
            result = f"{unique_providers} providers ({total_platforms} endpoints)"
        
        return result
    
    async def run_analysis(self) -> Dict[str, Any]:
        """Run complete cross-platform analysis with caching optimization"""
        start_time = time.time()
        
        try:
            # Collect data from all platforms
            if self.logger:
                self.logger.info("🔍 Step 1: Collecting data from all platforms...")
            platform_data = await self.collect_all_data()
            
            if self.logger:
                self.logger.info("🔍 Step 2: Normalizing token data...")
            # Normalize and correlate data
            normalized_data = self.normalize_token_data(platform_data)
            
            if self.logger:
                self.logger.info("🔍 Step 3: Enhancing with Birdeye data...")
            # Enhance with additional Birdeye data
            await self._enhance_with_birdeye_data(normalized_data)
            
            if self.logger:
                self.logger.info("🔍 Step 4: Analyzing correlations...")
            # Analyze correlations
            correlations = await self.analyze_correlations(normalized_data)
            
            if self.logger:
                self.logger.info("🔍 Step 5: Generating insights...")
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
            if self.logger:
                self.logger.error(f"❌ Analysis failed: {e}")
                import traceback
                self.logger.error(f"🔍 Full traceback: {traceback.format_exc()}")
            return {
                'timestamp': datetime.now().isoformat(),
                'execution_time_seconds': round(time.time() - start_time, 2),
                'error': str(e),
                'cache_statistics': self.enhanced_cache.get_cache_statistics()
            }
    
    async def close(self):
        """Clean up resources"""
        await self.birdeye.close()
        await self.jupiter.close()
        await self.meteora.close()
        await self.orca.close()
        await self.raydium.close()
    
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
            
            # Get Jupiter stats
            if hasattr(self, 'jupiter') and self.jupiter:
                jupiter_stats = self.jupiter.get_api_call_statistics()
                stats['jupiter'] = {
                    'calls': jupiter_stats.get('total_calls', 0),
                    'successes': jupiter_stats.get('successful_calls', 0),
                    'failures': jupiter_stats.get('failed_calls', 0),
                    'success_rate': jupiter_stats.get('success_rate', 0),
                    'runtime_seconds': jupiter_stats.get('runtime_seconds', 0),
                    'calls_per_minute': jupiter_stats.get('calls_per_minute', 0),
                    'estimated_cost': 0.0  # Jupiter is free
                }
                self.logger.debug(f"📊 Jupiter API stats: {jupiter_stats.get('total_calls', 0)} calls, {jupiter_stats.get('successful_calls', 0)} successes")
            
            # Get Meteora stats
            if hasattr(self, 'meteora') and self.meteora:
                meteora_stats = self.meteora.get_api_call_statistics()
                stats['meteora'] = {
                    'calls': meteora_stats.get('total_calls', 0),
                    'successes': meteora_stats.get('successful_calls', 0),
                    'failures': meteora_stats.get('failed_calls', 0),
                    'success_rate': meteora_stats.get('success_rate', 0),
                    'runtime_seconds': meteora_stats.get('runtime_seconds', 0),
                    'calls_per_minute': meteora_stats.get('calls_per_minute', 0),
                    'estimated_cost': 0.0  # Meteora is free
                }
                self.logger.debug(f"📊 Meteora API stats: {meteora_stats.get('total_calls', 0)} calls, {meteora_stats.get('successful_calls', 0)} successes")
            
            # Get Orca stats
            if hasattr(self, 'orca') and self.orca:
                orca_stats = self.orca.get_api_call_statistics()
                stats['orca'] = {
                    'calls': orca_stats.get('total_calls', 0),
                    'successes': orca_stats.get('successful_calls', 0),
                    'failures': orca_stats.get('failed_calls', 0),
                    'success_rate': orca_stats.get('success_rate', 0),
                    'runtime_seconds': orca_stats.get('runtime_seconds', 0),
                    'calls_per_minute': orca_stats.get('calls_per_minute', 0),
                    'estimated_cost': 0.0  # Orca is free
                }
                self.logger.debug(f"📊 Orca API stats: {orca_stats.get('total_calls', 0)} calls, {orca_stats.get('successful_calls', 0)} successes")
            
            # Get Raydium stats
            if hasattr(self, 'raydium') and self.raydium:
                raydium_stats = self.raydium.get_api_call_statistics()
                stats['raydium'] = {
                    'calls': raydium_stats.get('total_calls', 0),
                    'successes': raydium_stats.get('successful_calls', 0),
                    'failures': raydium_stats.get('failed_calls', 0),
                    'success_rate': raydium_stats.get('success_rate', 0),
                    'runtime_seconds': raydium_stats.get('runtime_seconds', 0),
                    'calls_per_minute': raydium_stats.get('calls_per_minute', 0),
                    'estimated_cost': 0.0  # Raydium is free
                }
                self.logger.debug(f"📊 Raydium API stats: {raydium_stats.get('total_calls', 0)} calls, {raydium_stats.get('successful_calls', 0)} successes")
            
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