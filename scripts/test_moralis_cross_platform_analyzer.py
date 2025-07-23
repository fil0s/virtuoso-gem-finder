#!/usr/bin/env python3
"""
Test Cross-Platform Token Analyzer with Moralis Integration

This is a test version that adds Moralis Solana trending tokens to the discovery
without modifying the original cross_platform_token_analyzer.py
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

# Import the original analyzer from the same directory
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from cross_platform_token_analyzer import CrossPlatformAnalyzer, DexScreenerConnector, BirdeyeConnector

from api.birdeye_connector import BirdeyeAPI
from api.rugcheck_connector import RugCheckConnector
from core.cache_manager import CacheManager
from services.rate_limiter_service import RateLimiterService
from services.logger_setup import LoggerSetup
from services.enhanced_cache_manager import EnhancedPositionCacheManager
from core.config_manager import ConfigManager

class MoralisConnector:
    """Connector for Moralis API to get Solana trending tokens"""
    
    def __init__(self, api_key: str, enhanced_cache: Optional[EnhancedPositionCacheManager] = None):
        self.api_key = api_key
        self.base_url = "https://deep-index.moralis.io/api/v2.2"
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
        stats["endpoints_used"] = list(stats["endpoints_used"])
        stats["average_response_time_ms"] = (
            stats["total_response_time_ms"] / max(1, stats["total_calls"])
        )
        return stats
    
    async def _make_tracked_request(self, endpoint: str) -> Optional[Dict]:
        """Make a tracked API request to Moralis"""
        start_time = time.time()
        self.api_stats["total_calls"] += 1
        self.api_stats["endpoints_used"].add(endpoint)
        
        try:
            headers = {
                "accept": "application/json",
                "X-API-Key": self.api_key
            }
            
            async with aiohttp.ClientSession() as session:
                async with session.get(f"{self.base_url}{endpoint}", headers=headers) as response:
                    response_time_ms = (time.time() - start_time) * 1000
                    self.api_stats["total_response_time_ms"] += response_time_ms
                    
                    if response.status == 200:
                        self.api_stats["successful_calls"] += 1
                        data = await response.json()
                        logging.info(f"🟢 Moralis API call successful: {endpoint} ({response.status}) - {response_time_ms:.1f}ms")
                        return data
                    else:
                        self.api_stats["failed_calls"] += 1
                        logging.warning(f"🔴 Moralis API call failed: {endpoint} ({response.status}) - {response_time_ms:.1f}ms")
                        return None
                        
        except Exception as e:
            response_time_ms = (time.time() - start_time) * 1000
            self.api_stats["total_response_time_ms"] += response_time_ms
            self.api_stats["failed_calls"] += 1
            logging.error(f"🔴 Moralis API error: {endpoint} - {e} - {response_time_ms:.1f}ms")
            return None
    
    async def get_trending_tokens(self) -> List[Dict]:
        """Get trending tokens from Moralis, filtered for Solana only"""
        # Check cache first
        if self.enhanced_cache:
            cached_data = self.enhanced_cache.get_enhanced("cross_platform_trending", "moralis_solana_trending")
            if cached_data:
                logging.info(f"📦 Retrieved {len(cached_data)} Moralis Solana trending tokens from cache")
                return cached_data
        
        # Make API request
        data = await self._make_tracked_request("/tokens/trending")
        
        if not data or not isinstance(data, list):
            logging.warning("No data received from Moralis trending API")
            return []
        
        # Filter for Solana tokens only
        solana_tokens = []
        for token in data:
            chain_id = token.get('chainId', '')
            if chain_id == 'solana':
                # Transform Moralis data to our standard format
                transformed_token = {
                    'address': token.get('tokenAddress', ''),
                    'name': token.get('name', ''),
                    'symbol': token.get('symbol', ''),
                    'decimals': token.get('decimals', 0),
                    'price_usd': float(token.get('usdPrice', 0)),
                    'market_cap': token.get('marketCap', 0),
                    'liquidity_usd': token.get('liquidityUsd', 0),
                    'holders': token.get('holders', 0),
                    'created_at': token.get('createdAt', ''),
                    'logo': token.get('logo', ''),
                    # Price changes
                    'price_change_1h': token.get('pricePercentChange', {}).get('1h', 0),
                    'price_change_4h': token.get('pricePercentChange', {}).get('4h', 0),
                    'price_change_12h': token.get('pricePercentChange', {}).get('12h', 0),
                    'price_change_24h': token.get('pricePercentChange', {}).get('24h', 0),
                    # Volume data
                    'volume_1h': token.get('totalVolume', {}).get('1h', 0),
                    'volume_4h': token.get('totalVolume', {}).get('4h', 0),
                    'volume_12h': token.get('totalVolume', {}).get('12h', 0),
                    'volume_24h': token.get('totalVolume', {}).get('24h', 0),
                    # Transaction data
                    'transactions_1h': token.get('transactions', {}).get('1h', 0),
                    'transactions_4h': token.get('transactions', {}).get('4h', 0),
                    'transactions_12h': token.get('transactions', {}).get('12h', 0),
                    'transactions_24h': token.get('transactions', {}).get('24h', 0),
                    # Buy/Sell data
                    'buy_transactions_24h': token.get('buyTransactions', {}).get('24h', 0),
                    'sell_transactions_24h': token.get('sellTransactions', {}).get('24h', 0),
                    'buyers_24h': token.get('buyers', {}).get('24h', 0),
                    'sellers_24h': token.get('sellers', {}).get('24h', 0),
                    # Raw data for reference
                    'raw_moralis_data': token
                }
                solana_tokens.append(transformed_token)
        
        # Cache the filtered results
        if solana_tokens and self.enhanced_cache:
            self.enhanced_cache.set_enhanced("cross_platform_trending", "moralis_solana_trending", solana_tokens)
        
        logging.info(f"🔥 Found {len(solana_tokens)} Solana trending tokens from Moralis (filtered from {len(data)} total)")
        return solana_tokens

class TestMoralisCrossPlatformAnalyzer(CrossPlatformAnalyzer):
    """Extended analyzer that includes Moralis Solana trending tokens"""
    
    def __init__(self, moralis_api_key: str, config: Optional[Dict] = None, logger: Optional[logging.Logger] = None):
        # Initialize parent class
        super().__init__(config, logger)
        
        # Add Moralis connector
        self.moralis = MoralisConnector(moralis_api_key, self.enhanced_cache)
        
        self.logger.info("🚀 Test Cross-Platform Analyzer initialized with Moralis integration")
    
    async def collect_all_data(self) -> Dict[str, List[Dict]]:
        """Enhanced data collection that includes Moralis Solana trending tokens"""
        self.logger.info("Starting enhanced parallel data collection with Moralis...")
        
        # Get original data collection tasks
        original_results = await super().collect_all_data()
        
        # Add Moralis task
        try:
            moralis_trending = await self.moralis.get_trending_tokens()
            original_results['moralis_trending'] = moralis_trending
            self.logger.info(f"  🔥 Moralis Solana trending: {len(moralis_trending)}")
        except Exception as e:
            self.logger.error(f"Error fetching Moralis trending tokens: {e}")
            original_results['moralis_trending'] = []
        
        return original_results
    
    def normalize_token_data(self, platform_data: Dict[str, List[Dict]]) -> Dict[str, Dict]:
        """Enhanced normalization that includes Moralis data with proper symbol extraction"""
        # Get original normalized data
        normalized = super().normalize_token_data(platform_data)
        
        # Process Moralis trending tokens
        for token in platform_data.get('moralis_trending', []):
            addr = token.get('address', '')
            if addr:
                if addr not in normalized:
                    normalized[addr] = {'platforms': set(), 'data': {}}
                
                normalized[addr]['platforms'].add('moralis')
                normalized[addr]['data']['moralis'] = {
                    'name': token.get('name', ''),
                    'symbol': token.get('symbol', ''),
                    'price_usd': token.get('price_usd', 0),
                    'market_cap': token.get('market_cap', 0),
                    'liquidity_usd': token.get('liquidity_usd', 0),
                    'holders': token.get('holders', 0),
                    'created_at': token.get('created_at', ''),
                    'logo': token.get('logo', ''),
                    # Price momentum
                    'price_change_1h': token.get('price_change_1h', 0),
                    'price_change_4h': token.get('price_change_4h', 0),
                    'price_change_12h': token.get('price_change_12h', 0),
                    'price_change_24h': token.get('price_change_24h', 0),
                    # Volume metrics
                    'volume_1h': token.get('volume_1h', 0),
                    'volume_4h': token.get('volume_4h', 0),
                    'volume_12h': token.get('volume_12h', 0),
                    'volume_24h': token.get('volume_24h', 0),
                    # Trading activity
                    'transactions_24h': token.get('transactions_24h', 0),
                    'buy_transactions_24h': token.get('buy_transactions_24h', 0),
                    'sell_transactions_24h': token.get('sell_transactions_24h', 0),
                    'buyers_24h': token.get('buyers_24h', 0),
                    'sellers_24h': token.get('sellers_24h', 0),
                    # Calculated metrics
                    'buy_sell_ratio': self._calculate_buy_sell_ratio(token),
                    'holder_quality_score': self._calculate_holder_quality_score(token),
                    'momentum_score': self._calculate_momentum_score(token),
                    'activity_score': self._calculate_activity_score(token)
                }
                
                # Register token for enhanced caching
                self.enhanced_cache.register_tracked_token(addr)
        
        return normalized
    
    def _calculate_buy_sell_ratio(self, token: Dict) -> float:
        """Calculate buy/sell ratio from Moralis data"""
        buy_txs = token.get('buy_transactions_24h', 0)
        sell_txs = token.get('sell_transactions_24h', 0)
        
        if sell_txs > 0:
            return buy_txs / sell_txs
        elif buy_txs > 0:
            return 10.0  # High ratio when there are buys but no sells
        else:
            return 1.0  # Neutral when no data
    
    def _calculate_holder_quality_score(self, token: Dict) -> float:
        """Calculate holder quality score (0-10)"""
        holders = token.get('holders', 0)
        market_cap = token.get('market_cap', 0)
        
        # Base score from holder count
        if holders >= 10000:
            holder_score = 5.0
        elif holders >= 5000:
            holder_score = 4.0
        elif holders >= 1000:
            holder_score = 3.0
        elif holders >= 500:
            holder_score = 2.0
        elif holders >= 100:
            holder_score = 1.0
        else:
            holder_score = 0.5
        
        # Adjust for market cap per holder (quality metric)
        if holders > 0 and market_cap > 0:
            mc_per_holder = market_cap / holders
            if mc_per_holder >= 1000:  # $1000+ per holder = quality
                holder_score += 2.0
            elif mc_per_holder >= 500:
                holder_score += 1.0
            elif mc_per_holder >= 100:
                holder_score += 0.5
        
        return min(holder_score, 10.0)
    
    def _calculate_momentum_score(self, token: Dict) -> float:
        """Calculate momentum score based on price changes (0-10)"""
        changes = [
            token.get('price_change_1h', 0),
            token.get('price_change_4h', 0),
            token.get('price_change_12h', 0),
            token.get('price_change_24h', 0)
        ]
        
        # Count positive momentum periods
        positive_periods = sum(1 for change in changes if change > 0)
        
        # Base momentum score
        momentum_score = positive_periods * 1.5  # 0-6 points
        
        # Bonus for strong momentum
        max_change = max(changes)
        if max_change >= 100:  # 100%+ gain
            momentum_score += 4.0
        elif max_change >= 50:   # 50%+ gain
            momentum_score += 2.0
        elif max_change >= 20:   # 20%+ gain
            momentum_score += 1.0
        
        return min(momentum_score, 10.0)
    
    def _calculate_activity_score(self, token: Dict) -> float:
        """Calculate activity score based on transactions and volume (0-10)"""
        volume_24h = token.get('volume_24h', 0)
        transactions_24h = token.get('transactions_24h', 0)
        buyers_24h = token.get('buyers_24h', 0)
        
        activity_score = 0.0
        
        # Volume scoring (0-4 points)
        if volume_24h >= 1000000:  # $1M+
            activity_score += 4.0
        elif volume_24h >= 500000:  # $500K+
            activity_score += 3.0
        elif volume_24h >= 100000:  # $100K+
            activity_score += 2.0
        elif volume_24h >= 50000:   # $50K+
            activity_score += 1.0
        
        # Transaction scoring (0-3 points)
        if transactions_24h >= 1000:
            activity_score += 3.0
        elif transactions_24h >= 500:
            activity_score += 2.0
        elif transactions_24h >= 100:
            activity_score += 1.0
        
        # Unique buyers scoring (0-3 points)
        if buyers_24h >= 500:
            activity_score += 3.0
        elif buyers_24h >= 200:
            activity_score += 2.0
        elif buyers_24h >= 50:
            activity_score += 1.0
        
        return min(activity_score, 10.0)
    
    def _calculate_token_score(self, token_data: Dict) -> float:
        """Enhanced token scoring that includes Moralis signals"""
        # Get base score from parent class
        base_score = super()._calculate_token_score(token_data)
        
        # Add Moralis-specific scoring (Max: 25 additional points)
        moralis_bonus = 0.0
        
        if 'moralis' in token_data['data']:
            moralis_data = token_data['data']['moralis']
            
            # Holder quality bonus (0-8 points)
            holder_quality = moralis_data.get('holder_quality_score', 0)
            moralis_bonus += (holder_quality / 10) * 8.0
            
            # Momentum bonus (0-6 points)
            momentum_score = moralis_data.get('momentum_score', 0)
            moralis_bonus += (momentum_score / 10) * 6.0
            
            # Activity bonus (0-6 points)
            activity_score = moralis_data.get('activity_score', 0)
            moralis_bonus += (activity_score / 10) * 6.0
            
            # Buy/sell ratio bonus (0-3 points)
            buy_sell_ratio = moralis_data.get('buy_sell_ratio', 1.0)
            if buy_sell_ratio >= 3.0:
                moralis_bonus += 3.0
            elif buy_sell_ratio >= 2.0:
                moralis_bonus += 2.0
            elif buy_sell_ratio >= 1.5:
                moralis_bonus += 1.0
            
            # Recent creation bonus (0-2 points) - newer tokens can be more explosive
            created_at = moralis_data.get('created_at', '')
            if created_at:
                try:
                    from datetime import datetime, timezone
                    created_time = datetime.fromisoformat(created_at.replace('Z', '+00:00'))
                    age_hours = (datetime.now(timezone.utc) - created_time).total_seconds() / 3600
                    
                    if age_hours <= 24:  # Less than 1 day old
                        moralis_bonus += 2.0
                    elif age_hours <= 168:  # Less than 1 week old
                        moralis_bonus += 1.0
                except:
                    pass  # Skip if date parsing fails
        
        # Ensure final score is within 0-100 range
        final_score = max(0.0, min(100.0, base_score + moralis_bonus))
        return round(final_score, 1)
    
    def generate_insights(self, correlations: Dict[str, Any]) -> List[str]:
        """Enhanced insights that include Moralis analysis and cross-platform validation"""
        # Get base insights
        insights = super().generate_insights(correlations)
        
        # Add Moralis-specific insights
        moralis_tokens = 0
        moralis_overlap = 0
        
        # Track tokens by platform count and identify universal tokens
        platform_counts = defaultdict(int)
        universal_tokens = []  # Tokens appearing on ALL platforms
        high_overlap_tokens = []  # Tokens appearing on 3+ platforms
        
        all_platforms = {'dexscreener', 'birdeye', 'rugcheck', 'moralis', 'dexscreener_narrative'}
        
        for token_addr, token_info in correlations.get('all_tokens', {}).items():
            token_platforms = set(token_info.get('platforms', []))
            platform_count = len(token_platforms)
            platform_counts[platform_count] += 1
            
            # Count Moralis tokens
            if 'moralis' in token_platforms:
                moralis_tokens += 1
                if platform_count > 1:
                    moralis_overlap += 1
            
            # Check for universal presence (appears on all major platforms)
            major_platforms = {'dexscreener', 'birdeye', 'rugcheck', 'moralis'}
            if len(token_platforms.intersection(major_platforms)) >= 4:
                # Token appears on all 4 major platforms
                universal_tokens.append({
                    'address': token_addr,
                    'symbol': token_info.get('symbol', 'Unknown'),
                    'score': token_info.get('score', 0),
                    'platforms': list(token_platforms),
                    'platform_count': platform_count
                })
            elif platform_count >= 3:
                # Token appears on 3+ platforms
                high_overlap_tokens.append({
                    'address': token_addr,
                    'symbol': token_info.get('symbol', 'Unknown'),
                    'score': token_info.get('score', 0),
                    'platforms': list(token_platforms),
                    'platform_count': platform_count
                })
        
        # Sort by score (highest first)
        universal_tokens.sort(key=lambda x: x['score'], reverse=True)
        high_overlap_tokens.sort(key=lambda x: x['score'], reverse=True)
        
        # Add universal token insights
        if universal_tokens:
            insights.append(f"🌟 UNIVERSAL TOKENS (All 4 Major APIs): {len(universal_tokens)} tokens")
            for i, token in enumerate(universal_tokens[:3], 1):  # Show top 3
                platforms_str = ', '.join(token['platforms'])
                insights.append(f"  {i}. {token['symbol']} ({token['address'][:8]}...) - Score: {token['score']:.1f} - Platforms: {platforms_str}")
            
            if len(universal_tokens) > 3:
                insights.append(f"  ... and {len(universal_tokens) - 3} more universal tokens")
        else:
            insights.append("🌟 UNIVERSAL TOKENS: None found across all 4 major APIs")
        
        # Add high overlap insights
        if high_overlap_tokens:
            insights.append(f"🎯 HIGH OVERLAP TOKENS (3+ platforms): {len(high_overlap_tokens)} tokens")
            for i, token in enumerate(high_overlap_tokens[:5], 1):  # Show top 5
                platforms_str = ', '.join(token['platforms'])
                insights.append(f"  {i}. {token['symbol']} ({token['address'][:8]}...) - Score: {token['score']:.1f} - Platforms: {platforms_str}")
        
        # Platform distribution insights
        insights.append(f"📊 Platform Distribution:")
        for count in sorted(platform_counts.keys(), reverse=True):
            if count > 1:
                insights.append(f"  • {count} platforms: {platform_counts[count]} tokens")
        
        # Moralis-specific insights
        if moralis_tokens > 0:
            insights.append(f"🔥 Moralis Solana trending tokens: {moralis_tokens}")
            
            if moralis_overlap > 0:
                overlap_rate = (moralis_overlap / moralis_tokens) * 100
                insights.append(f"🎯 Moralis cross-platform validation: {overlap_rate:.1f}% ({moralis_overlap}/{moralis_tokens})")
        
        # Cross-platform validation strength
        total_tokens = correlations['total_tokens']
        multi_platform_tokens = sum(count for platform_count, count in platform_counts.items() if platform_count > 1)
        if total_tokens > 0:
            validation_strength = (multi_platform_tokens / total_tokens) * 100
            insights.append(f"💪 Cross-platform validation strength: {validation_strength:.1f}% ({multi_platform_tokens}/{total_tokens})")
        
        # API overlap matrix insights
        insights.append(f"🔗 Key API Overlaps:")
        correlation_matrix = correlations.get('correlation_matrix', {})
        
        # Check specific overlaps
        overlap_pairs = [
            ('moralis', 'birdeye', 'Moralis-Birdeye'),
            ('moralis', 'dexscreener', 'Moralis-DexScreener'),
            ('moralis', 'rugcheck', 'Moralis-RugCheck'),
            ('dexscreener', 'birdeye', 'DexScreener-Birdeye'),
            ('rugcheck', 'birdeye', 'RugCheck-Birdeye'),
            ('dexscreener', 'rugcheck', 'DexScreener-RugCheck')
        ]
        
        for api1, api2, label in overlap_pairs:
            if api1 in correlation_matrix and api2 in correlation_matrix[api1]:
                overlap_count = correlation_matrix[api1][api2]
                if overlap_count > 0:
                    insights.append(f"  • {label}: {overlap_count} tokens")
        
        return insights
    
    def get_api_stats(self) -> Dict[str, Dict[str, Any]]:
        """Enhanced API stats that include Moralis"""
        stats = super().get_api_stats()
        
        # Add Moralis stats
        if hasattr(self, 'moralis') and self.moralis:
            moralis_stats = self.moralis.get_api_call_statistics()
            stats['moralis'] = {
                'calls': moralis_stats.get('total_calls', 0),
                'successes': moralis_stats.get('successful_calls', 0),
                'failures': moralis_stats.get('failed_calls', 0),
                'total_time_ms': moralis_stats.get('total_response_time_ms', 0),
                'estimated_cost': moralis_stats.get('total_calls', 0) * 0.001  # Estimated cost per call
            }
        
        return stats

    def analyze_correlations(self, normalized_data: Dict[str, Dict]) -> Dict[str, Any]:
        """Enhanced correlation analysis with proper symbol extraction"""
        # Get base correlations
        correlations = super().analyze_correlations(normalized_data)
        
        # Fix symbol extraction for all_tokens
        for token_addr, token_info in correlations.get('all_tokens', {}).items():
            if token_info.get('symbol') == 'Unknown' or not token_info.get('symbol'):
                # Try to extract symbol from platform data
                token_data = normalized_data.get(token_addr, {}).get('data', {})
                
                # Priority order for symbol extraction
                symbol = None
                name = None
                
                # 1. Try Moralis first (most reliable for Solana)
                if 'moralis' in token_data:
                    moralis_data = token_data['moralis']
                    symbol = moralis_data.get('symbol', '').strip()
                    name = moralis_data.get('name', '').strip()
                
                # 2. Try Birdeye if no Moralis symbol
                if not symbol and 'birdeye' in token_data:
                    birdeye_data = token_data['birdeye']
                    symbol = birdeye_data.get('symbol', '').strip()
                    if not name:
                        name = birdeye_data.get('name', '').strip()
                
                # 3. Try narrative data if available
                if not symbol and 'narratives' in token_data and token_data['narratives']:
                    narrative = token_data['narratives'][0]
                    symbol = narrative.get('symbol', '').strip()
                    if not name:
                        name = narrative.get('name', '').strip()
                
                # 4. Try DexScreener data
                if not symbol and 'dexscreener' in token_data:
                    ds_data = token_data['dexscreener']
                    # DexScreener might have symbol in profile or links
                    profile = ds_data.get('profile', {})
                    if profile and 'description_enhanced' in profile:
                        desc = profile['description_enhanced']
                        # Try to extract symbol from description (basic attempt)
                        import re
                        symbol_match = re.search(r'\$([A-Z]{2,10})', desc)
                        if symbol_match:
                            symbol = symbol_match.group(1)
                
                # Update token info with extracted symbol/name
                if symbol:
                    token_info['symbol'] = symbol
                else:
                    # Use shortened address as fallback
                    token_info['symbol'] = f"{token_addr[:4]}...{token_addr[-4:]}"
                
                if name and not token_info.get('name'):
                    token_info['name'] = name
                
                # Log symbol extraction for debugging
                self.logger.debug(f"Symbol extraction for {token_addr[:8]}...: '{symbol}' from platforms: {list(token_data.keys())}")
        
        return correlations

async def test_moralis_integration():
    """Test function to run the enhanced analyzer with Moralis"""
    # Set up logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    # Moralis API key (from your previous request)
    moralis_api_key = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJub25jZSI6IjM4NTlhNzQyLTEwNjctNDkyMy05YTU2LWQ5YjQxMGZmYmI5NiIsIm9yZ0lkIjoiNDU0OTY2IiwidXNlcklkIjoiNDY4MTAwIiwidHlwZUlkIjoiNjI1YTg1ZDEtM2Q0OC00YTUxLWEyOWEtMDM5YTU0Zjk2NzkwIiwidHlwZSI6IlBST0pFQ1QiLCJpYXQiOjE3NTA0MjgwMzcsImV4cCI6NDkwNjE4ODAzN30.kXspLCawOP0iaF3NxCnKMvN7prb6X_Na5xXjPRU7Lb4"
    
    analyzer = None
    try:
        # Initialize enhanced analyzer with Moralis
        analyzer = TestMoralisCrossPlatformAnalyzer(moralis_api_key)
        
        # Run analysis
        results = await analyzer.run_analysis()
        
        # Save results
        timestamp = int(time.time())
        output_file = f"results/test_moralis_cross_platform_analysis_{timestamp}.json"
        
        os.makedirs("results", exist_ok=True)
        with open(output_file, 'w') as f:
            json.dump(results, f, indent=2)
        
        # Print enhanced summary
        print("\n🔥 TEST: Cross-Platform Token Analysis with Moralis")
        print("=" * 60)
        
        if 'error' in results:
            print(f"❌ Analysis failed: {results['error']}")
        else:
            print(f"⏱️  Execution time: {results['execution_time_seconds']}s")
            print(f"📊 Platform data: {results['platform_data_counts']}")
            print(f"🔍 Total unique tokens: {results['correlations']['total_tokens']}")
            print(f"💎 High-conviction tokens: {len(results['correlations']['high_conviction_tokens'])}")
            
            # Show Moralis-specific stats
            moralis_count = results['platform_data_counts'].get('moralis_trending', 0)
            if moralis_count > 0:
                print(f"🔥 Moralis Solana tokens: {moralis_count}")
            
            # API call statistics
            api_stats = analyzer.get_api_stats()
            print(f"\n📡 API Call Statistics:")
            for platform, stats in api_stats.items():
                print(f"  {platform}: {stats['calls']} calls, {stats['successes']} successes, ${stats['estimated_cost']:.4f} cost")
            
            # Cache performance
            cache_stats = results['cache_statistics']
            print(f"🚀 Cache hit rate: {cache_stats['hit_rate_percent']:.1f}%")
            print(f"💰 Estimated savings: ${cache_stats['estimated_cost_savings_usd']:.4f}")
            
            print("\n📋 Key Insights:")
            for insight in results['insights']:
                print(f"  • {insight}")
            
            # Show top tokens with Moralis data
            high_conviction = results['correlations']['high_conviction_tokens']
            moralis_tokens = [t for t in high_conviction if 'moralis' in results['correlations']['all_tokens'][t['address']]['platforms']]
            
            if moralis_tokens:
                print(f"\n🎯 Top Moralis Cross-Platform Tokens:")
                for i, token in enumerate(moralis_tokens[:5], 1):
                    addr = token['address']
                    platforms = ', '.join(token['platforms'])
                    token_info = results['correlations']['all_tokens'][addr]
                    symbol = token_info.get('symbol', 'Unknown')
                    print(f"  {i}. {symbol} ({addr[:8]}...) - Score: {token['score']:.1f} - Platforms: {platforms}")
        
        print(f"\n📁 Full results saved to: {output_file}")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
    finally:
        if analyzer:
            await analyzer.close()

if __name__ == "__main__":
    asyncio.run(test_moralis_integration()) 