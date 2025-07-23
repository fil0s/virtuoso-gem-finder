#!/usr/bin/env python3
"""
Trending Token Monitor Service

This service monitors trending tokens using the Birdeye /defi/token_trending endpoint
and provides momentum analysis for token discovery enhancement.
"""

import asyncio
import logging
import time
from typing import Dict, List, Any, Optional, Set
from datetime import datetime, timedelta

from api.birdeye_connector import BirdeyeAPI
from core.cache_manager import CacheManager
from utils.structured_logger import get_structured_logger


class TrendingTokenMonitor:
    """
    Monitors trending tokens and provides momentum analysis.
    
    Uses the Birdeye /defi/token_trending endpoint to identify tokens with
    strong momentum and provides scoring boosts for trending tokens.
    """
    
    def __init__(self, birdeye_api: BirdeyeAPI, logger: Optional[logging.Logger] = None):
        """
        Initialize the trending token monitor.
        
        Args:
            birdeye_api: Birdeye API instance
            logger: Logger instance
        """
        self.birdeye_api = birdeye_api
        self.logger = logger or logging.getLogger(__name__)
        self.cache_manager = CacheManager()
        
        # Cache settings
        self.trending_cache_ttl = 300  # 5 minutes cache for trending data
        self.momentum_cache_ttl = 600  # 10 minutes cache for momentum analysis
        
        # Trending analysis settings
        self.trending_thresholds = {
            "min_volume_24h": 50000,      # Minimum $50k daily volume
            "min_liquidity": 100000,      # Minimum $100k liquidity
            "min_trades_24h": 100,        # Minimum 100 trades per day
            "momentum_threshold": 1.5,    # 50% momentum threshold
        }
        
        # Internal tracking
        self._last_trending_fetch = 0
        self._trending_tokens_cache = {}
        self._momentum_history = {}
        
        self.logger.info("🔥 TrendingTokenMonitor initialized - monitoring trending tokens")
    
    async def get_trending_tokens(self, limit: int = 50) -> List[Dict[str, Any]]:
        """
        Get current trending tokens from Birdeye API.
        
        Args:
            limit: Maximum number of trending tokens to fetch
            
        Returns:
            List of trending token data
        """
        cache_key = f"trending_tokens_{limit}"
        
        # Check cache first
        cached_data = self.cache_manager.get(cache_key)
        if cached_data:
            self.logger.debug(f"📊 Using cached trending tokens data ({len(cached_data)} tokens)")
            return cached_data
        
        try:
            self.logger.info(f"📈 Fetching trending tokens (limit: {limit})")
            
            # Call Birdeye trending endpoint
            result = await self.birdeye_api.get_trending_tokens(limit=limit)
            
            if result and result.get("success") and "data" in result:
                trending_tokens = result["data"]
                
                # Process and filter trending tokens
                processed_tokens = await self._process_trending_tokens(trending_tokens)
                
                # Cache the results
                self.cache_manager.set(cache_key, processed_tokens, ttl=self.trending_cache_ttl)
                
                self.logger.info(f"✅ Found {len(processed_tokens)} qualifying trending tokens")
                return processed_tokens
            else:
                self.logger.warning(f"⚠️ Trending tokens API call failed: {result}")
                return []
                
        except Exception as e:
            self.logger.error(f"❌ Error fetching trending tokens: {e}")
            return []
    
    async def _process_trending_tokens(self, trending_tokens: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Process and filter trending tokens based on quality criteria.
        
        Args:
            trending_tokens: Raw trending token data from API
            
        Returns:
            Processed and filtered trending tokens
        """
        processed_tokens = []
        current_time = int(time.time())
        
        for token in trending_tokens:
            try:
                # Basic validation
                if not token.get("address"):
                    continue
                
                # Apply quality filters
                if not self._passes_trending_quality_check(token):
                    continue
                
                # Calculate momentum metrics
                momentum_data = await self._calculate_momentum_metrics(token)
                
                # Enhance token data
                enhanced_token = {
                    **token,
                    "trending_analysis": {
                        "discovered_at": current_time,
                        "trending_score": self._calculate_trending_score(token),
                        "momentum_metrics": momentum_data,
                        "quality_passed": True,
                        "trending_rank": len(processed_tokens) + 1
                    }
                }
                
                processed_tokens.append(enhanced_token)
                
            except Exception as e:
                self.logger.error(f"Error processing trending token {token.get('address', 'unknown')}: {e}")
                continue
        
        return processed_tokens
    
    def _passes_trending_quality_check(self, token: Dict[str, Any]) -> bool:
        """
        Check if trending token meets quality criteria.
        
        Args:
            token: Token data to check
            
        Returns:
            True if token passes quality checks
        """
        try:
            # Check minimum volume
            volume_24h = token.get("volume24h", 0) or 0
            if volume_24h < self.trending_thresholds["min_volume_24h"]:
                return False
            
            # Check minimum liquidity
            liquidity = token.get("liquidity", 0) or 0
            if liquidity < self.trending_thresholds["min_liquidity"]:
                return False
            
            # Check minimum trades
            trades_24h = token.get("trade24h", 0) or 0
            if trades_24h < self.trending_thresholds["min_trades_24h"]:
                return False
            
            return True
            
        except Exception as e:
            self.logger.error(f"Error in trending quality check: {e}")
            return False
    
    async def _calculate_momentum_metrics(self, token: Dict[str, Any]) -> Dict[str, Any]:
        """
        Calculate momentum metrics for trending token.
        
        Args:
            token: Token data
            
        Returns:
            Momentum metrics dictionary
        """
        try:
            token_address = token.get("address")
            if not token_address:
                return {}
            
            # Get historical data for momentum calculation
            cache_key = f"momentum_{token_address}"
            cached_momentum = self.cache_manager.get(cache_key)
            
            if cached_momentum:
                return cached_momentum
            
            # Calculate momentum metrics
            momentum_metrics = {
                "price_momentum_24h": self._calculate_price_momentum(token),
                "volume_momentum_24h": self._calculate_volume_momentum(token),
                "liquidity_momentum_24h": self._calculate_liquidity_momentum(token),
                "trade_momentum_24h": self._calculate_trade_momentum(token),
                "overall_momentum_score": 0.0
            }
            
            # Calculate overall momentum score
            momentum_metrics["overall_momentum_score"] = self._calculate_overall_momentum_score(momentum_metrics)
            
            # Cache momentum data
            self.cache_manager.set(cache_key, momentum_metrics, ttl=self.momentum_cache_ttl)
            
            return momentum_metrics
            
        except Exception as e:
            self.logger.error(f"Error calculating momentum metrics: {e}")
            return {}
    
    def _calculate_price_momentum(self, token: Dict[str, Any]) -> float:
        """Calculate price momentum score."""
        try:
            price_change_24h = token.get("priceChange24h", 0) or 0
            # Normalize to 0-1 scale, cap at 100% change
            return min(max(price_change_24h / 100.0, -1.0), 1.0)
        except:
            return 0.0
    
    def _calculate_volume_momentum(self, token: Dict[str, Any]) -> float:
        """Calculate volume momentum score."""
        try:
            volume_24h = token.get("volume24h", 0) or 0
            volume_change = token.get("volumeChange24h", 0) or 0
            
            # Base score from volume change
            volume_score = min(max(volume_change / 100.0, -1.0), 2.0)
            
            # Boost for high absolute volume
            if volume_24h > 1000000:  # $1M+ volume
                volume_score *= 1.2
            elif volume_24h > 500000:  # $500k+ volume
                volume_score *= 1.1
            
            return volume_score
        except:
            return 0.0
    
    def _calculate_liquidity_momentum(self, token: Dict[str, Any]) -> float:
        """Calculate liquidity momentum score."""
        try:
            liquidity = token.get("liquidity", 0) or 0
            liquidity_change = token.get("liquidityChange24h", 0) or 0
            
            # Base score from liquidity change
            liquidity_score = min(max(liquidity_change / 100.0, -1.0), 1.0)
            
            # Boost for high liquidity
            if liquidity > 2000000:  # $2M+ liquidity
                liquidity_score *= 1.2
            elif liquidity > 1000000:  # $1M+ liquidity
                liquidity_score *= 1.1
            
            return liquidity_score
        except:
            return 0.0
    
    def _calculate_trade_momentum(self, token: Dict[str, Any]) -> float:
        """Calculate trading activity momentum score."""
        try:
            trades_24h = token.get("trade24h", 0) or 0
            trades_change = token.get("tradeChange24h", 0) or 0
            
            # Base score from trade count change
            trade_score = min(max(trades_change / 100.0, -1.0), 1.5)
            
            # Boost for high trade count
            if trades_24h > 1000:  # 1000+ trades
                trade_score *= 1.2
            elif trades_24h > 500:  # 500+ trades
                trade_score *= 1.1
            
            return trade_score
        except:
            return 0.0
    
    def _calculate_overall_momentum_score(self, momentum_metrics: Dict[str, Any]) -> float:
        """
        Calculate overall momentum score from individual metrics.
        
        Args:
            momentum_metrics: Individual momentum metrics
            
        Returns:
            Overall momentum score (0-1 scale)
        """
        try:
            # Weighted combination of momentum metrics
            weights = {
                "price_momentum_24h": 0.3,
                "volume_momentum_24h": 0.4,
                "liquidity_momentum_24h": 0.2,
                "trade_momentum_24h": 0.1
            }
            
            overall_score = 0.0
            for metric, weight in weights.items():
                score = momentum_metrics.get(metric, 0.0)
                overall_score += score * weight
            
            # Normalize to 0-1 scale
            return max(0.0, min(1.0, (overall_score + 1.0) / 2.0))
            
        except Exception as e:
            self.logger.error(f"Error calculating overall momentum score: {e}")
            return 0.0
    
    def _calculate_trending_score(self, token: Dict[str, Any]) -> float:
        """
        Calculate trending score for token.
        
        Args:
            token: Token data
            
        Returns:
            Trending score (0-1 scale)
        """
        try:
            score = 0.0
            
            # Volume component (40% weight)
            volume_24h = token.get("volume24h", 0) or 0
            if volume_24h > 1000000:
                score += 0.4
            elif volume_24h > 500000:
                score += 0.3
            elif volume_24h > 100000:
                score += 0.2
            
            # Price change component (30% weight)
            price_change = token.get("priceChange24h", 0) or 0
            if price_change > 50:
                score += 0.3
            elif price_change > 20:
                score += 0.2
            elif price_change > 10:
                score += 0.1
            
            # Liquidity component (20% weight)
            liquidity = token.get("liquidity", 0) or 0
            if liquidity > 2000000:
                score += 0.2
            elif liquidity > 1000000:
                score += 0.15
            elif liquidity > 500000:
                score += 0.1
            
            # Trading activity component (10% weight)
            trades_24h = token.get("trade24h", 0) or 0
            if trades_24h > 1000:
                score += 0.1
            elif trades_24h > 500:
                score += 0.05
            
            return min(1.0, score)
            
        except Exception as e:
            self.logger.error(f"Error calculating trending score: {e}")
            return 0.0
    
    async def check_token_trending_status(self, token_address: str) -> Dict[str, Any]:
        """
        Check if a specific token is currently trending.
        
        Args:
            token_address: Token address to check
            
        Returns:
            Trending status and metrics
        """
        try:
            # Get current trending tokens
            trending_tokens = await self.get_trending_tokens()
            
            # Find token in trending list
            for trending_token in trending_tokens:
                if trending_token.get("address") == token_address:
                    return {
                        "is_trending": True,
                        "trending_rank": trending_token.get("trending_analysis", {}).get("trending_rank", 0),
                        "trending_score": trending_token.get("trending_analysis", {}).get("trending_score", 0.0),
                        "momentum_metrics": trending_token.get("trending_analysis", {}).get("momentum_metrics", {}),
                        "score_boost": 1.5  # 50% boost for trending tokens
                    }
            
            return {
                "is_trending": False,
                "trending_rank": 0,
                "trending_score": 0.0,
                "momentum_metrics": {},
                "score_boost": 1.0  # No boost
            }
            
        except Exception as e:
            self.logger.error(f"Error checking trending status for {token_address}: {e}")
            return {
                "is_trending": False,
                "trending_rank": 0,
                "trending_score": 0.0,
                "momentum_metrics": {},
                "score_boost": 1.0
            }
    
    def get_trending_addresses(self) -> Set[str]:
        """
        Get set of currently trending token addresses.
        
        Returns:
            Set of trending token addresses
        """
        try:
            trending_tokens = self._trending_tokens_cache.get("data", [])
            return {token.get("address") for token in trending_tokens if token.get("address")}
        except:
            return set()
    
    def get_metrics(self) -> Dict[str, Any]:
        """
        Get performance metrics.
        
        Returns:
            Dictionary of performance metrics
        """
        cache_hit_rate = (
            self.cache_manager.cache_hits / max(1, self.cache_manager.cache_hits + self.cache_manager.cache_misses)
        ) * 100
        
        return {
            'total_requests': self.cache_manager.total_requests,
            'cache_hits': self.cache_manager.cache_hits,
            'cache_misses': self.cache_manager.cache_misses,
            'trending_tokens_found': len(self._trending_tokens_cache.get('data', [])),
            'momentum_calculations': 0,  # Assuming momentum calculations are not tracked in the cache manager
            'last_update': datetime.now().isoformat(),
            'cache_hit_rate_percent': round(cache_hit_rate, 2),
            'momentum_history_size': len(self._momentum_history),
            'cache_valid': self.cache_manager.is_cache_valid(time.time())
        }
    
    def clear_cache(self):
        """Clear the trending cache to force fresh data fetch."""
        self._trending_tokens_cache = {}
        self._last_trending_fetch = 0
        self.cache_manager.clear_cache()
        self.logger.info("🗑️ Trending token cache cleared") 