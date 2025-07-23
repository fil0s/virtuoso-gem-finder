#!/usr/bin/env python3
"""
Safe Logging Optimization Utilities
Replaces runtime patching with proper utility functions
"""

import logging
import time
from typing import Optional, Dict, Any
from functools import wraps

class OptimizedLogging:
    """
    Safe logging optimization utilities that don't use runtime patching
    """
    
    def __init__(self, sample_rate: float = 0.1):
        self.sample_rate = sample_rate
        self.last_log_times: Dict[str, float] = {}
        self.log_counters: Dict[str, int] = {}
    
    def should_log(self, key: str, min_interval: float = 5.0) -> bool:
        """
        Determine if a log message should be written based on sampling and timing
        
        Args:
            key: Unique identifier for the log type
            min_interval: Minimum seconds between logs of this type
        """
        current_time = time.time()
        last_time = self.last_log_times.get(key, 0)
        
        # Check time interval
        if current_time - last_time < min_interval:
            return False
        
        # Check sample rate
        counter = self.log_counters.get(key, 0) + 1
        self.log_counters[key] = counter
        
        if counter % int(1 / self.sample_rate) == 0:
            self.last_log_times[key] = current_time
            return True
        
        return False
    
    def log_cache_operation(self, operation: str, cache_key: str, force_log: bool = False):
        """
        Log cache operations with optimization
        
        Args:
            operation: 'hit' or 'miss'
            cache_key: The cache key
            force_log: Force logging regardless of sampling
        """
        if force_log or self.should_log(f"cache_{operation}"):
            logger = logging.getLogger('CacheOptimized')
            logger.debug(f"Cache {operation}: {cache_key[:50]}...")
    
    def log_api_call(self, service: str, endpoint: str, force_log: bool = False):
        """
        Log API calls with optimization
        
        Args:
            service: Service name (e.g., 'BirdEye', 'Moralis')
            endpoint: API endpoint
            force_log: Force logging regardless of sampling
        """
        if force_log or self.should_log(f"api_{service}"):
            logger = logging.getLogger('APIOptimized')
            logger.info(f"API call to {service}: {endpoint}")

def optimized_cache_logging(func):
    """
    Decorator for optimized cache logging without runtime patching
    """
    optimizer = OptimizedLogging()
    
    @wraps(func)
    def wrapper(self, *args, **kwargs):
        cache_key = str(args[0]) if args else "unknown"
        
        result = func(self, *args, **kwargs)
        
        # Determine if it was a hit or miss based on result
        if result is not None:
            optimizer.log_cache_operation('hit', cache_key)
        else:
            optimizer.log_cache_operation('miss', cache_key)
        
        return result
    
    return wrapper

def optimized_api_logging(service_name: str):
    """
    Decorator factory for optimized API logging
    """
    def decorator(func):
        optimizer = OptimizedLogging()
        
        @wraps(func)
        def wrapper(self, *args, **kwargs):
            endpoint = getattr(self, '_current_endpoint', 'unknown')
            optimizer.log_api_call(service_name, endpoint)
            return func(self, *args, **kwargs)
        
        return wrapper
    
    return decorator

class SafeLoggerPatch:
    """
    Safe alternative to runtime patching - uses composition instead
    """
    
    def __init__(self, original_logger: logging.Logger):
        self.original_logger = original_logger
        self.optimizer = OptimizedLogging()
    
    def debug(self, message: str, force: bool = False):
        """Optimized debug logging"""
        if force or self.optimizer.should_log(message[:20]):
            self.original_logger.debug(message)
    
    def info(self, message: str, force: bool = False):
        """Optimized info logging"""
        if force or self.optimizer.should_log(message[:20], min_interval=1.0):
            self.original_logger.info(message)
    
    def warning(self, message: str):
        """Always log warnings"""
        self.original_logger.warning(message)
    
    def error(self, message: str):
        """Always log errors"""
        self.original_logger.error(message)

def create_optimized_logger(name: str) -> SafeLoggerPatch:
    """
    Create an optimized logger without runtime patching
    
    Args:
        name: Logger name
        
    Returns:
        SafeLoggerPatch instance
    """
    original = logging.getLogger(name)
    return SafeLoggerPatch(original)

# Usage example for migration from monkey-patching:
"""
# Instead of monkey-patching:
# SomeClass.logger = patched_logger

# Use composition:
class SomeClass:
    def __init__(self):
        self.logger = create_optimized_logger('SomeClass')
        # or
        self.log_optimizer = OptimizedLogging()
    
    def some_method(self):
        # Optimized logging
        if self.log_optimizer.should_log('some_operation'):
            logging.getLogger().debug("Some operation completed")
"""