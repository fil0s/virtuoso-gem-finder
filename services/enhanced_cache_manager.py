#!/usr/bin/env python3
"""
Enhanced Cache Manager for Position Tracking and Signal Detection

Optimizes Birdeye API usage by implementing intelligent caching strategies
specifically designed for position monitoring and cross-platform analysis.

Key Features:
- Shared cache between all tracking systems
- Context-aware TTL (longer for stable data, shorter for volatile)
- Batch invalidation for related data
- Cost-aware caching with priority levels
- Smart cache warming for tracked tokens
"""

import time
import json
import logging
from typing import Dict, List, Optional, Any, Set, Tuple
from dataclasses import dataclass
from enum import Enum
import asyncio
from core.cache_manager import CacheManager

class CachePriority(Enum):
    """Cache priority levels for different data types"""
    CRITICAL = "critical"      # Position tracking data - never expire during trading hours
    HIGH = "high"             # Price/volume data for tracked tokens  
    MEDIUM = "medium"         # General market data
    LOW = "low"               # Background analysis data

@dataclass
class CacheConfig:
    """Configuration for cache behavior"""
    ttl_seconds: int
    priority: CachePriority
    auto_refresh: bool = False
    batch_invalidate: bool = False

class EnhancedPositionCacheManager:
    """Enhanced cache manager optimized for position tracking and signal detection"""
    
    def __init__(self, base_cache_manager: CacheManager, logger: Optional[logging.Logger] = None):
        self.base_cache = base_cache_manager
        self.logger = logger or logging.getLogger(__name__)
        
        # Track tokens being monitored for position tracking
        self.tracked_tokens: Set[str] = set()
        self.position_tokens: Set[str] = set()
        
        # Cache configurations for different data types
        self.cache_configs = {
            # Position tracking data (CRITICAL - long TTL during market hours)
            "position_token_overview": CacheConfig(900, CachePriority.CRITICAL, auto_refresh=True),  # 15 min
            "position_price": CacheConfig(180, CachePriority.CRITICAL, auto_refresh=True),           # 3 min
            "position_volume": CacheConfig(300, CachePriority.CRITICAL),                             # 5 min
            "position_whale_activity": CacheConfig(600, CachePriority.HIGH),                         # 10 min
            
            # Cross-platform analysis data (HIGH priority for tracked tokens)
            "cross_platform_trending": CacheConfig(600, CachePriority.HIGH),                        # 10 min
            "cross_platform_correlation": CacheConfig(900, CachePriority.MEDIUM),                   # 15 min
            
            # General market data (MEDIUM priority)
            "token_overview": CacheConfig(300, CachePriority.MEDIUM),                               # 5 min
            "token_security": CacheConfig(3600, CachePriority.LOW),                                 # 1 hour
            "top_traders": CacheConfig(600, CachePriority.MEDIUM),                                  # 10 min
            
            # Batch API data (optimized for cost efficiency)
            "multi_price": CacheConfig(120, CachePriority.HIGH, batch_invalidate=True),             # 2 min
            "multi_trade_data": CacheConfig(300, CachePriority.HIGH, batch_invalidate=True),        # 5 min
            
            # Background analysis (LOW priority)
            "historical_price": CacheConfig(3600, CachePriority.LOW),                               # 1 hour
            "token_creation_info": CacheConfig(86400, CachePriority.LOW),                           # 24 hours
        }
        
        # Performance tracking
        self.stats = {
            'cache_hits': 0,
            'cache_misses': 0,
            'api_calls_saved': 0,
            'cost_savings_estimate': 0.0,
            'last_reset': time.time()
        }
        
        # Auto-refresh tracking
        self.auto_refresh_queue: List[Tuple[str, str, int]] = []  # (key, data_type, last_refresh)
        
        self.logger.info("🚀 Enhanced Position Cache Manager initialized")
    
    def register_tracked_token(self, token_address: str, is_position: bool = False):
        """Register a token for enhanced caching"""
        self.tracked_tokens.add(token_address.lower())
        if is_position:
            self.position_tokens.add(token_address.lower())
            self.logger.debug(f"📍 Registered position token for enhanced caching: {token_address}")
        else:
            self.logger.debug(f"👁️ Registered tracked token for enhanced caching: {token_address}")
    
    def unregister_tracked_token(self, token_address: str):
        """Unregister a token from enhanced caching"""
        token_address = token_address.lower()
        self.tracked_tokens.discard(token_address)
        self.position_tokens.discard(token_address)
        
        # Invalidate related cache entries
        self._invalidate_token_cache(token_address)
        self.logger.debug(f"🗑️ Unregistered token from enhanced caching: {token_address}")
    
    def get_enhanced(self, data_type: str, token_address: str, additional_key: str = "") -> Optional[Any]:
        """Get data with enhanced caching logic"""
        cache_key = self._build_cache_key(data_type, token_address, additional_key)
        
        # Check if data exists in cache
        cached_data = self.base_cache.get(cache_key)
        
        if cached_data is not None:
            self.stats['cache_hits'] += 1
            
            # Check if auto-refresh is needed for critical data
            if self._should_auto_refresh(data_type, token_address, cache_key):
                self._schedule_auto_refresh(cache_key, data_type, token_address)
            
            self.logger.debug(f"✅ Cache hit: {data_type} for {token_address}")
            return cached_data
        
        self.stats['cache_misses'] += 1
        self.logger.debug(f"❌ Cache miss: {data_type} for {token_address}")
        return None
    
    def set_enhanced(self, data_type: str, token_address: str, data: Any, additional_key: str = ""):
        """Set data with enhanced caching logic"""
        cache_key = self._build_cache_key(data_type, token_address, additional_key)
        config = self.cache_configs.get(data_type, CacheConfig(300, CachePriority.MEDIUM))
        
        # Adjust TTL based on token priority
        ttl = self._get_adjusted_ttl(data_type, token_address, config.ttl_seconds)
        
        # Store in cache
        self.base_cache.set(cache_key, data, ttl=ttl)
        
        # Track auto-refresh if enabled
        if config.auto_refresh and token_address.lower() in self.position_tokens:
            self._add_to_auto_refresh(cache_key, data_type, token_address)
        
        # Estimate cost savings
        self._estimate_cost_savings(data_type)
        
        self.logger.debug(f"💾 Cached: {data_type} for {token_address} (TTL: {ttl}s)")
    
    def batch_get_enhanced(self, data_type: str, token_addresses: List[str], additional_key: str = "") -> Dict[str, Any]:
        """Get multiple tokens' data from cache"""
        results = {}
        
        for token_address in token_addresses:
            cached_data = self.get_enhanced(data_type, token_address, additional_key)
            if cached_data is not None:
                results[token_address] = cached_data
        
        return results
    
    def batch_set_enhanced(self, data_type: str, token_data: Dict[str, Any], additional_key: str = ""):
        """Set multiple tokens' data in cache"""
        for token_address, data in token_data.items():
            self.set_enhanced(data_type, token_address, data, additional_key)
    
    def invalidate_token_cache(self, token_address: str, data_types: Optional[List[str]] = None):
        """Invalidate all cached data for a specific token"""
        if data_types is None:
            data_types = list(self.cache_configs.keys())
        
        for data_type in data_types:
            cache_key = self._build_cache_key(data_type, token_address)
            self.base_cache.delete(cache_key)
        
        self.logger.debug(f"🗑️ Invalidated cache for token: {token_address}")
    
    def warm_cache_for_positions(self, position_tokens: List[str]) -> List[str]:
        """Identify which position tokens need cache warming"""
        tokens_needing_data = []
        
        critical_data_types = [
            "position_token_overview",
            "position_price", 
            "position_volume"
        ]
        
        for token_address in position_tokens:
            self.register_tracked_token(token_address, is_position=True)
            
            needs_warming = False
            for data_type in critical_data_types:
                if self.get_enhanced(data_type, token_address) is None:
                    needs_warming = True
                    break
            
            if needs_warming:
                tokens_needing_data.append(token_address)
        
        if tokens_needing_data:
            self.logger.info(f"🔥 Cache warming needed for {len(tokens_needing_data)} position tokens")
        
        return tokens_needing_data
    
    def get_cache_statistics(self) -> Dict[str, Any]:
        """Get comprehensive cache statistics"""
        total_requests = self.stats['cache_hits'] + self.stats['cache_misses']
        hit_rate = (self.stats['cache_hits'] / total_requests * 100) if total_requests > 0 else 0
        
        return {
            'cache_hits': self.stats['cache_hits'],
            'cache_misses': self.stats['cache_misses'],
            'hit_rate_percent': round(hit_rate, 2),
            'api_calls_saved': self.stats['api_calls_saved'],
            'estimated_cost_savings_usd': round(self.stats['cost_savings_estimate'], 4),
            'tracked_tokens': len(self.tracked_tokens),
            'position_tokens': len(self.position_tokens),
            'auto_refresh_queue_size': len(self.auto_refresh_queue)
        }
    
    def _build_cache_key(self, data_type: str, token_address: str, additional_key: str = "") -> str:
        """Build standardized cache key"""
        key_parts = ["enhanced", data_type, token_address.lower()]
        if additional_key:
            key_parts.append(additional_key)
        return "_".join(key_parts)
    
    def _get_adjusted_ttl(self, data_type: str, token_address: str, base_ttl: int) -> int:
        """Adjust TTL based on token priority and market conditions"""
        token_address = token_address.lower()
        
        # Position tokens get longer TTL for stability
        if token_address in self.position_tokens:
            if data_type.startswith("position_"):
                return base_ttl * 2  # Double TTL for position data
            else:
                return int(base_ttl * 1.5)  # 1.5x TTL for other data
        
        # Tracked tokens get slightly longer TTL
        if token_address in self.tracked_tokens:
            return int(base_ttl * 1.2)
        
        return base_ttl
    
    def _should_auto_refresh(self, data_type: str, token_address: str, cache_key: str) -> bool:
        """Check if auto-refresh is needed"""
        config = self.cache_configs.get(data_type)
        if not config or not config.auto_refresh:
            return False
        
        # Only auto-refresh for position tokens
        if token_address.lower() not in self.position_tokens:
            return False
        
        # Check if data is getting stale (>75% of TTL elapsed)
        cache_info = self.base_cache.get_with_ttl(cache_key)
        if cache_info and len(cache_info) == 2:
            data, remaining_ttl = cache_info
            if remaining_ttl < (config.ttl_seconds * 0.25):  # Less than 25% TTL remaining
                return True
        
        return False
    
    def _schedule_auto_refresh(self, cache_key: str, data_type: str, token_address: str):
        """Schedule auto-refresh for critical data"""
        current_time = int(time.time())
        
        # Add to refresh queue if not already present
        refresh_entry = (cache_key, data_type, current_time)
        if refresh_entry not in self.auto_refresh_queue:
            self.auto_refresh_queue.append(refresh_entry)
            self.logger.debug(f"⏰ Scheduled auto-refresh: {data_type} for {token_address}")
    
    def _add_to_auto_refresh(self, cache_key: str, data_type: str, token_address: str):
        """Add entry to auto-refresh tracking"""
        current_time = int(time.time())
        refresh_entry = (cache_key, data_type, current_time)
        
        # Remove old entry if exists
        self.auto_refresh_queue = [entry for entry in self.auto_refresh_queue if entry[0] != cache_key]
        
        # Add new entry
        self.auto_refresh_queue.append(refresh_entry)
    
    def _invalidate_token_cache(self, token_address: str):
        """Invalidate all cache entries for a token"""
        for data_type in self.cache_configs.keys():
            cache_key = self._build_cache_key(data_type, token_address)
            self.base_cache.delete(cache_key)
    
    def _estimate_cost_savings(self, data_type: str):
        """Estimate cost savings from cache usage"""
        # Rough estimate: each cache hit saves ~1-5 compute units
        if data_type.startswith("position_"):
            savings = 3  # Position data is frequently accessed
        elif "multi_" in data_type:
            savings = 5  # Batch calls save more
        else:
            savings = 2  # Regular API calls
        
        self.stats['api_calls_saved'] += 1
        self.stats['cost_savings_estimate'] += savings * 0.00001  # ~$0.00001 per CU
    
    def reset_statistics(self):
        """Reset cache statistics"""
        self.stats = {
            'cache_hits': 0,
            'cache_misses': 0,
            'api_calls_saved': 0,
            'cost_savings_estimate': 0.0,
            'last_reset': time.time()
        }
        self.logger.info("📊 Cache statistics reset") 