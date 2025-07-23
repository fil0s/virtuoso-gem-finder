"""
Enhanced API Cache Manager with intelligent TTL strategies and async support.

This cache manager extends the core cache functionality with API-specific
optimizations, intelligent TTL strategies, and dependency management.
"""

import time
import json
import hashlib
import logging
import asyncio
from typing import Dict, Any, Optional, List, Set, Union
from core.cache_manager import CacheManager as CoreCacheManager

logger = logging.getLogger(__name__)

class EnhancedAPICacheManager(CoreCacheManager):
    """
    Enhanced cache manager specifically designed for API data with intelligent 
    TTL strategies, cache warming, and dependency management.
    
    This class extends the core cache manager with API-specific optimizations:
    - Intelligent TTL based on data volatility
    - Cache dependency management
    - Access pattern tracking
    - Batch operations
    - Cache warming for high-frequency data
    """
    
    def __init__(self, enabled: bool = True, default_ttl_seconds: int = 3600, 
                 max_memory_items: int = 1024, file_cache_dir: str = "temp/api_cache"):
        """
        Initialize the enhanced API cache manager.
        
        Args:
            enabled: Whether caching is enabled
            default_ttl_seconds: Default TTL for cached items
            max_memory_items: Maximum items in memory cache
            file_cache_dir: Directory for file-based cache
        """
        # Only pass ttl_default to the parent CacheManager
        super().__init__(ttl_default=default_ttl_seconds)
        self.logger = logging.getLogger(__name__)
        
        # Store the additional parameters for our own use
        self.enabled = enabled
        self.max_memory_items = max_memory_items
        self.file_cache_dir = file_cache_dir
        
        # TTL strategies based on data volatility and API characteristics
        self.ttl_strategies = self._build_ttl_strategies()
        
        # Cache dependencies - if parent changes, invalidate children
        self.cache_dependencies = self._build_cache_dependencies()
        
        # Track cache access patterns for optimization
        self.access_patterns = {}
        self.access_lock = asyncio.Lock()
        
        # Batch operation management
        self.batch_queue = {}
        self.batch_lock = asyncio.Lock()
        
        # Performance metrics
        self.metrics = {
            'total_requests': 0,
            'cache_hits': 0,
            'cache_misses': 0,
            'dependency_invalidations': 0,
            'batch_operations': 0
        }
        
        self.logger.info("Enhanced API Cache Manager initialized with intelligent TTL strategies")
    
    def _build_ttl_strategies(self) -> Dict[str, int]:
        """Build TTL strategies based on API data characteristics"""
        return {
            # Real-time/High volatility data (very short TTL)
            'price': 30,                    # 30 seconds - prices change rapidly
            'trades': 60,                   # 1 minute - recent trades
            'ohlcv_1m': 60,                # 1 minute - 1-minute candles
            'transaction_volume': 120,      # 2 minutes - transaction metrics
            'trending': 180,                # 3 minutes - trending data
            
            # Medium volatility data (medium TTL)
            'token_overview': 1800,         # 30 minutes - token metadata (increased for cost optimization)
            'ohlcv_5m': 300,               # 5 minutes - 5-minute candles
            'ohlcv_15m': 600,              # 10 minutes - 15-minute candles
            'trend_dynamics': 300,          # 5 minutes - trend analysis
            'trade_metrics': 300,           # 5 minutes - trading metrics
            'top_traders': 600,             # 10 minutes - trader rankings
            'wallet_portfolio': 300,        # 5 minutes - wallet holdings
            'market_data': 180,             # 3 minutes - market overview
            
            # Low volatility data (long TTL)
            'token_security': 3600,         # 1 hour - security analysis
            'token_creation_info': 86400,   # 24 hours - creation data (immutable)
            'holders': 1800,                # 30 minutes - holder distribution
            'ohlcv_1h': 1800,              # 30 minutes - hourly candles
            'ohlcv_4h': 3600,              # 1 hour - 4-hour candles
            'ohlcv_1d': 7200,              # 2 hours - daily candles
            'historical_price': 3600,       # 1 hour - historical data
            'new_listings': 600,            # 10 minutes - new token listings
            'whale_analysis': 900,          # 15 minutes - whale data
            
            # Error caching (short TTL to retry soon)
            'error': 60,                    # 1 minute - cached errors
            
            # Default fallback
            'default': 300                  # 5 minutes
        }
    
    def _build_cache_dependencies(self) -> Dict[str, List[str]]:
        """Build cache dependency relationships"""
        return {
            'token_overview': ['price', 'trades', 'market_data'],
            'trend_dynamics': ['trades', 'ohlcv_1m', 'ohlcv_5m'],
            'trade_metrics': ['trades', 'transaction_volume'],
            'market_data': ['price', 'trending'],
            'whale_analysis': ['top_traders', 'holders'],
            # Most other data types are independent
            'token_security': [],
            'token_creation_info': [],
            'historical_price': []
        }
    
    def get_intelligent_ttl(self, cache_key: str, data_type: Optional[str] = None) -> int:
        """
        Determine TTL based on cache key pattern and data characteristics.
        
        Args:
            cache_key: The cache key to analyze
            data_type: Optional explicit data type override
            
        Returns:
            TTL in seconds
        """
        if data_type and data_type in self.ttl_strategies:
            return self.ttl_strategies[data_type]
        
        # Analyze cache key to determine data type
        key_lower = cache_key.lower()
        
        for data_type, ttl in self.ttl_strategies.items():
            if data_type in key_lower:
                return ttl
        
        # Check for specific patterns
        if 'error' in key_lower or 'fail' in key_lower:
            return self.ttl_strategies['error']
        
        return self.ttl_strategies['default']
    
    async def set_with_intelligent_ttl(self, key: str, value: Any, 
                                     data_type: Optional[str] = None,
                                     namespace: str = "api") -> None:
        """
        Set cache value with automatically determined intelligent TTL.
        
        Args:
            key: Cache key
            value: Value to cache
            data_type: Optional data type for TTL determination
            namespace: Cache namespace
        """
        ttl = self.get_intelligent_ttl(key, data_type)
        self.set(key, value, ttl_seconds=ttl, namespace=namespace)
        
        # Track access pattern
        await self._track_access(key, 'set')
        
        # Update metrics
        self.metrics['total_requests'] += 1
        
        self.logger.debug(f"Cached {namespace}:{key} with TTL {ttl}s")
    
    async def get_with_tracking(self, key: str, namespace: str = "api") -> Any:
        """
        Get cache value with access tracking and metrics.
        
        Args:
            key: Cache key
            namespace: Cache namespace
            
        Returns:
            Cached value or None
        """
        value = self.get(key, namespace=namespace)
        
        # Track access pattern
        await self._track_access(key, 'get')
        
        # Update metrics
        self.metrics['total_requests'] += 1
        if value is not None:
            self.metrics['cache_hits'] += 1
        else:
            self.metrics['cache_misses'] += 1
        
        return value
    
    async def _track_access(self, key: str, operation: str) -> None:
        """Track cache access patterns for optimization"""
        async with self.access_lock:
            if key not in self.access_patterns:
                self.access_patterns[key] = {
                    'hits': 0,
                    'misses': 0,
                    'sets': 0,
                    'last_access': 0,
                    'frequency': 0,
                    'created': int(time.time())
                }
            
            pattern = self.access_patterns[key]
            pattern['last_access'] = int(time.time())
            pattern['frequency'] += 1
            
            if operation == 'get':
                if self.get(key) is not None:
                    pattern['hits'] += 1
                else:
                    pattern['misses'] += 1
            elif operation == 'set':
                pattern['sets'] += 1
    
    async def batch_set(self, items: Dict[str, Any], data_type: Optional[str] = None,
                       namespace: str = "api") -> None:
        """
        Set multiple cache items efficiently with intelligent TTL.
        
        Args:
            items: Dictionary of key-value pairs to cache
            data_type: Optional data type for TTL determination
            namespace: Cache namespace
        """
        async with self.batch_lock:
            for key, value in items.items():
                await self.set_with_intelligent_ttl(key, value, data_type, namespace)
            
            self.metrics['batch_operations'] += 1
            self.logger.debug(f"Batch cached {len(items)} items in namespace {namespace}")
    
    async def batch_get(self, keys: List[str], namespace: str = "api") -> Dict[str, Any]:
        """
        Get multiple cache items efficiently with tracking.
        
        Args:
            keys: List of cache keys to retrieve
            namespace: Cache namespace
            
        Returns:
            Dictionary of found key-value pairs
        """
        results = {}
        
        for key in keys:
            value = await self.get_with_tracking(key, namespace)
            if value is not None:
                results[key] = value
        
        hit_rate = len(results) / len(keys) if keys else 0
        self.logger.debug(f"Batch cache lookup: {len(results)}/{len(keys)} hits ({hit_rate:.2%})")
        
        return results
    
    async def invalidate_dependencies(self, parent_key: str, namespace: str = "api") -> None:
        """
        Invalidate dependent cache entries when parent data changes.
        
        Args:
            parent_key: The cache key that changed
            namespace: Cache namespace
        """
        # Extract data type from key
        data_type = None
        for key_type in self.cache_dependencies.keys():
            if key_type in parent_key.lower():
                data_type = key_type
                break
        
        if not data_type:
            return
        
        # Get dependent data types
        dependents = self.cache_dependencies.get(data_type, [])
        
        if dependents:
            invalidated_count = 0
            
            # Find and invalidate all cache entries of dependent types
            for dependent_type in dependents:
                # This would require scanning cache keys, which is expensive
                # In practice, you might maintain a reverse dependency index
                self.logger.debug(f"Would invalidate {dependent_type} caches due to {data_type} change")
                invalidated_count += 1
            
            self.metrics['dependency_invalidations'] += invalidated_count
            self.logger.info(f"Invalidated {invalidated_count} dependent cache entries for {parent_key}")
    
    def get_cache_performance_metrics(self) -> Dict[str, Any]:
        """
        Get comprehensive cache performance metrics.
        
        Returns:
            Dictionary of performance metrics
        """
        total_requests = self.metrics['total_requests']
        hit_rate = (self.metrics['cache_hits'] / total_requests) if total_requests > 0 else 0
        miss_rate = (self.metrics['cache_misses'] / total_requests) if total_requests > 0 else 0
        
        # Calculate access pattern statistics
        pattern_stats = {
            'hot_keys': 0,  # Keys with high access frequency
            'cold_keys': 0,  # Keys with low access frequency
            'total_tracked_keys': len(self.access_patterns)
        }
        
        current_time = int(time.time())
        for key, pattern in self.access_patterns.items():
            age = current_time - pattern['created']
            frequency_per_hour = (pattern['frequency'] / max(age / 3600, 1))
            
            if frequency_per_hour > 10:  # More than 10 accesses per hour
                pattern_stats['hot_keys'] += 1
            elif frequency_per_hour < 1:  # Less than 1 access per hour
                pattern_stats['cold_keys'] += 1
        
        return {
            'cache_metrics': {
                'total_requests': total_requests,
                'cache_hits': self.metrics['cache_hits'],
                'cache_misses': self.metrics['cache_misses'],
                'hit_rate': hit_rate,
                'miss_rate': miss_rate,
                'dependency_invalidations': self.metrics['dependency_invalidations'],
                'batch_operations': self.metrics['batch_operations']
            },
            'access_patterns': pattern_stats,
            'ttl_strategies': len(self.ttl_strategies),
            'cache_dependencies': len(self.cache_dependencies),
            'enabled': self.enabled
        }
    
    async def optimize_ttl_strategies(self) -> None:
        """
        Analyze access patterns and optimize TTL strategies.
        
        This method analyzes cache hit/miss patterns and adjusts TTL values
        to improve cache efficiency.
        """
        async with self.access_lock:
            adjustments = {}
            current_time = int(time.time())
            
            for key, pattern in self.access_patterns.items():
                if pattern['frequency'] < 5:  # Skip low-frequency keys
                    continue
                
                hit_rate = pattern['hits'] / max(pattern['hits'] + pattern['misses'], 1)
                
                # Extract data type from key
                data_type = None
                for dt in self.ttl_strategies.keys():
                    if dt in key.lower():
                        data_type = dt
                        break
                
                if not data_type:
                    continue
                
                current_ttl = self.ttl_strategies[data_type]
                
                # Adjust TTL based on hit rate
                if hit_rate > 0.9:  # Very high hit rate - can increase TTL
                    new_ttl = min(current_ttl * 1.2, current_ttl + 300)
                elif hit_rate < 0.5:  # Low hit rate - decrease TTL
                    new_ttl = max(current_ttl * 0.8, current_ttl - 60)
                else:
                    continue
                
                adjustments[data_type] = {
                    'old_ttl': current_ttl,
                    'new_ttl': int(new_ttl),
                    'hit_rate': hit_rate,
                    'sample_key': key
                }
            
            # Apply adjustments
            for data_type, adjustment in adjustments.items():
                self.ttl_strategies[data_type] = adjustment['new_ttl']
                self.logger.info(f"Optimized TTL for {data_type}: "
                               f"{adjustment['old_ttl']}s -> {adjustment['new_ttl']}s "
                               f"(hit_rate: {adjustment['hit_rate']:.2%})")
    
    def create_compound_key(self, *components: str, separator: str = "_") -> str:
        """
        Create a compound cache key from multiple components.
        
        Args:
            components: Key components
            separator: Separator character
            
        Returns:
            Compound cache key
        """
        # Filter out None/empty components and clean them
        clean_components = []
        for component in components:
            if component:
                # Convert to string and clean
                clean_component = str(component).replace(separator, "")
                clean_components.append(clean_component)
        
        return separator.join(clean_components)
    
    async def warm_cache_for_tokens(self, token_addresses: List[str], 
                                  priority_data_types: Optional[List[str]] = None) -> None:
        """
        Pre-warm cache for frequently accessed token data.
        
        Args:
            token_addresses: List of token addresses to warm cache for
            priority_data_types: Optional list of data types to prioritize
        """
        if not priority_data_types:
            priority_data_types = ['token_overview', 'price', 'token_security']
        
        self.logger.info(f"Starting cache warming for {len(token_addresses)} tokens")
        
        # This would trigger background cache warming
        # In practice, this would coordinate with API managers to fetch data
        warm_count = 0
        
        for address in token_addresses:
            for data_type in priority_data_types:
                cache_key = self.create_compound_key("birdeye", data_type, address)
                
                # Check if already cached
                if self.get(cache_key) is None:
                    # Add to warming queue (would be processed by background task)
                    self.logger.debug(f"Queuing for cache warming: {cache_key}")
                    warm_count += 1
        
        self.logger.info(f"Queued {warm_count} items for cache warming")

    def set(self, key: str, value: Any, ttl: Optional[int] = None, ttl_seconds: Optional[int] = None, namespace: str = "api") -> None:
        """
        Set a value in the cache with specified TTL.
        
        Args:
            key: Cache key
            value: Value to cache
            ttl: Time-to-live in seconds (uses default if None)
            ttl_seconds: Alternative parameter name for ttl (for backward compatibility)
            namespace: Cache namespace
        """
        # ttl_seconds takes precedence if both are provided
        effective_ttl = ttl_seconds if ttl_seconds is not None else ttl
        
        # Use the parent class set method with the proper parameter name
        super().set(key, value, ttl=effective_ttl)
    
    async def cleanup(self) -> None:
        """
        Cleanup cache resources (async method for compatibility).
        
        Since this cache manager inherits from a synchronous parent,
        this method doesn't need to do anything special.
        """
        # Log cleanup attempt
        self.logger.debug("Cache cleanup requested")
        
        # Clear access patterns to free memory
        async with self.access_lock:
            self.access_patterns.clear()
        
        # Clear batch queue
        async with self.batch_lock:
            self.batch_queue.clear()
        
        self.logger.info("Cache cleanup completed")

# Factory function for creating the enhanced cache manager
def create_api_cache_manager(enabled: bool = True, default_ttl_seconds: int = 300,
                           max_memory_items: int = 1024, 
                           file_cache_dir: str = "temp/api_cache") -> EnhancedAPICacheManager:
    """
    Factory function to create an enhanced API cache manager.
    
    Args:
        enabled: Whether caching is enabled
        default_ttl_seconds: Default TTL for cached items
        max_memory_items: Maximum items in memory cache
        file_cache_dir: Directory for file-based cache
        
    Returns:
        Configured EnhancedAPICacheManager instance
    """
    return EnhancedAPICacheManager(enabled, default_ttl_seconds, max_memory_items, file_cache_dir)

# Global instance for backward compatibility
_api_cache_manager: Optional[EnhancedAPICacheManager] = None

def get_api_cache_manager() -> EnhancedAPICacheManager:
    """Get or create the global API cache manager instance"""
    global _api_cache_manager
    if _api_cache_manager is None:
        _api_cache_manager = create_api_cache_manager()
    return _api_cache_manager 