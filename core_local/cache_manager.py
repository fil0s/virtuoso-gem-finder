#!/usr/bin/env python3
"""
Cache manager for the Gem Finder application.
Provides a simple in-memory cache with optional Redis support.
"""

import time
import logging
import json
import hashlib
from pathlib import Path
from typing import Any, Optional, Union, Dict, Tuple
from functools import wraps

from cachetools import TTLCache
# Removed REDIS related imports for now to simplify, can be added back if Redis is a firm requirement.

from core_local.config_manager import ConfigManager
from utils.structured_logger import get_structured_logger

logger = logging.getLogger(__name__)

class CacheManager:
    """
    Cache manager with TTL support for optimizing API calls.
    Provides in-memory caching with configurable expiration times.
    """
    
    def __init__(self, ttl_default: int = 300):
        """
        Initialize the cache manager.
        
        Args:
            ttl_default: Default TTL in seconds (5 minutes)
        """
        self.cache: Dict[str, Dict[str, Any]] = {}
        self.ttl_default = ttl_default
        self.stats = {'hits': 0, 'misses': 0}
        self.logger = get_structured_logger('CacheManager')

    def get(self, key: str, default: Any = None, scan_id: Optional[str] = None) -> Any:
        """
        Get a value from the cache if it exists and hasn't expired.
        
        Args:
            key: Cache key
            default: Default value if key not found or expired
            scan_id: Optional scan ID for logging
            
        Returns:
            Cached value or default
        """
        entry = self.cache.get(key)
        now = time.time()
        if entry and now - entry['timestamp'] < entry['ttl']:
            self.stats['hits'] += 1
            self.logger.info({"event": "cache_get", "result": "hit", "key": key, "scan_id": scan_id, "ttl": entry['ttl'], "timestamp": entry['timestamp']})
            return entry['data']
        if entry:
            self.logger.info({"event": "cache_expiry", "key": key, "scan_id": scan_id, "ttl": entry['ttl'], "timestamp": entry['timestamp']})
            del self.cache[key]
        self.stats['misses'] += 1
        self.logger.info({"event": "cache_get", "result": "miss", "key": key, "scan_id": scan_id})
        return default
    
    def set(self, key: str, value: Any, ttl: Optional[int] = None, scan_id: Optional[str] = None) -> None:
        """
        Set a value in the cache with specified TTL.
        
        Args:
            key: Cache key
            value: Value to cache
            ttl: Time-to-live in seconds (uses default if None)
            scan_id: Optional scan ID for logging
        """
        self.cache[key] = {
            'data': value,
            'timestamp': time.time(),
            'ttl': ttl if ttl is not None else self.ttl_default
        }
        self.logger.info({"event": "cache_set", "key": key, "scan_id": scan_id, "ttl": ttl if ttl is not None else self.ttl_default})
        
    def invalidate(self, key: str, scan_id: Optional[str] = None) -> bool:
        """
        Invalidate a specific cache entry.
        
        Args:
            key: Cache key to invalidate
            scan_id: Optional scan ID for logging
            
        Returns:
            True if key was found and invalidated, False otherwise
        """
        if key in self.cache:
            self.logger.info({"event": "cache_invalidate", "key": key, "scan_id": scan_id})
            del self.cache[key]
            return True
        return False
    
    def invalidate_pattern(self, pattern: str) -> int:
        """
        Invalidate all cache entries that start with the given pattern.
        
        Args:
            pattern: Pattern to match against keys
            
        Returns:
            Number of invalidated entries
        """
        invalidated = 0
        for key in list(self.cache.keys()):
            if key.startswith(pattern):
                del self.cache[key]
                invalidated += 1
        return invalidated
    
    def clear(self) -> int:
        """
        Clear the entire cache.
        
        Returns:
            Number of cleared entries
        """
        size = len(self.cache)
        self.cache = {}
        return size
    
    def get_stats(self) -> Dict[str, Any]:
        """
        Get cache statistics.
        
        Returns:
            Dictionary with cache statistics
        """
        total = self.stats['hits'] + self.stats['misses']
        hit_rate = (self.stats['hits'] / total) * 100 if total > 0 else 0
        stats = {
            'hits': self.stats['hits'],
            'misses': self.stats['misses'],
            'hit_rate': hit_rate,
            'total_keys': len(self.cache)
        }
        self.logger.info({"event": "cache_stats", **stats})
        return stats
    
    def log_cache_size(self, scan_id: Optional[str] = None) -> int:
        """
        Log cache size and return size in bytes.
        
        Args:
            scan_id: Optional scan ID for logging
            
        Returns:
            Size of the cache in bytes
        """
        import sys
        size = sys.getsizeof(self.cache)
        self.logger.info({"event": "cache_size", "size_bytes": size, "total_keys": len(self.cache), "scan_id": scan_id})
        return size

    def get_cache_stats(self) -> Dict[str, Any]:
        """
        Alias for get_stats() for backward compatibility.
        
        Returns:
            Dictionary with cache statistics
        """
        return self.get_stats()

# Global instance (optional, depends on project structure)
# cache_manager = CacheManager(config=config_manager.get_section("CACHING")) 
# This instantiation depends on how config_manager is made available globally.
# It's often better to instantiate and pass CacheManager explicitly where needed (Dependency Injection).

def cached(cache_name: str, key_func=None, ttl: Optional[int] = None, ttl_seconds: Optional[int] = None):
    """
    Decorator to cache function results.
    
    Args:
        cache_name: Name of the cache to use
        key_func: Function to generate cache key from args/kwargs
        ttl: Optional cache TTL override
        ttl_seconds: Alternative parameter name for ttl (for backward compatibility)
        
    Returns:
        decorator: Function decorator
    """
    # ttl_seconds takes precedence if both are provided
    effective_ttl = ttl_seconds if ttl_seconds is not None else ttl
    
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            cache = CacheManager().get_cache(cache_name)
            
            # Generate cache key
            if key_func:
                key = key_func(*args, **kwargs)
            else:
                # Default key generation
                key = f"{func.__name__}:{str(args)}:{str(kwargs)}"
            
            # Check cache
            cached_result = cache.get(key)
            if cached_result is not None:
                return cached_result
            
            # Call function
            result = func(*args, **kwargs)
            
            # Cache result
            cache.set(key, result, ttl=effective_ttl)
            
            return result
        return wrapper
    return decorator 