import time
import logging
from collections import defaultdict, deque
import asyncio
from typing import Dict, Optional, Deque
from asyncio import Lock as AsyncLock

# Assuming global config_manager is available
# from core.config_manager import config_manager 

logger = logging.getLogger(__name__)

class RateLimiterService:
    """
    Async-compatible rate limiter service.
    
    Manages rate limits for different API domains using async locks and proper async patterns.
    Thread-safe and designed to work with asyncio applications.
    """
    
    _instance = None
    _instance_lock = asyncio.Lock()

    def __init__(self, config: Optional[dict] = None):
        """Initialize the rate limiter with configuration."""
        if config is None:
            # Default configuration - UPDATED FOR BIRDEYE STARTER PACKAGE
            config = {
                "enabled": True,
                "default_retry_interval": 1,
                "domains": {
                    "default": {"calls": 5, "period": 1},  # Default: 5 calls per second
                    "helius": {"calls": 5, "period": 1},
                    "birdeye": {"calls": 15, "period": 1},  # FIXED: Starter package = 15 RPS (was 2)
                    "birdeye_wallet": {"calls": 30, "period": 60},  # NEW: Wallet API = 30 RPM
                    "dexscreener": {"calls": 30, "period": 60}
                }
            }
            
        self.enabled = config.get("enabled", True)
        self.domain_configs = config.get("domains", {})
        self.default_retry_interval = config.get("default_retry_interval", 1)
        
        # Async-safe data structures
        self.call_timestamps: Dict[str, Deque[float]] = defaultdict(deque)
        self.domain_locks: Dict[str, AsyncLock] = defaultdict(AsyncLock)
        
        # Track initialization
        self._initialized = True

        if not self.enabled:
            logger.info("Rate limiting is disabled by configuration.")
        else:
            logger.info(f"RateLimiterService initialized with domain configs: {self.domain_configs}")

    @classmethod
    async def get_instance(cls, config: Optional[dict] = None):
        """Get singleton instance in async-safe way."""
        async with cls._instance_lock:
            if cls._instance is None:
                cls._instance = cls(config)
            return cls._instance

    def _get_domain_config(self, domain: str) -> Optional[dict]:
        """Get configuration for a specific domain."""
        return self.domain_configs.get(domain, self.domain_configs.get("default"))

    async def acquire(self, domain: str = "default") -> None:
        """
        Acquire a rate limit slot for the specified domain.
        
        This method blocks until a slot is available, making it safe to use
        in synchronous-style code that doesn't want to handle the waiting logic.
        
        Args:
            domain: The API domain to acquire a slot for
        """
        if not self.enabled:
            return

        domain_config = self._get_domain_config(domain)
        if not domain_config:
            logger.warning(f"No rate limit configuration found for domain '{domain}' or default. Proceeding without limit.")
            return

        max_calls = domain_config['calls']
        period_seconds = domain_config['period']

        async with self.domain_locks[domain]:
            while True:
                now = time.monotonic()
                
                # Clean up old timestamps
                while (self.call_timestamps[domain] and 
                       self.call_timestamps[domain][0] <= now - period_seconds):
                    self.call_timestamps[domain].popleft()
                
                # Check if we can make a call
                if len(self.call_timestamps[domain]) < max_calls:
                    self.call_timestamps[domain].append(now)
                    logger.debug(f"Rate limit acquired for domain '{domain}'. "
                               f"Current calls in period: {len(self.call_timestamps[domain])}/{max_calls}")
                    return
                else:
                    # Calculate wait time
                    wait_time = (self.call_timestamps[domain][0] + period_seconds) - now
                    wait_time = max(0.001, min(wait_time, period_seconds))  # Reasonable bounds
                    
                    logger.debug(f"Rate limit exceeded for domain '{domain}'. "
                               f"Waiting for {wait_time:.3f} seconds. "
                               f"Calls: {len(self.call_timestamps[domain])}/{max_calls}")
                    
                    await asyncio.sleep(wait_time)

    async def wait_for_slot(self, domain: str = "default") -> None:
        """
        Wait for a rate limit slot to become available.
        
        This is the preferred method for async code as it clearly indicates
        that it's an async operation that may wait.
        
        Args:
            domain: The API domain to wait for a slot for
        """
        await self.acquire(domain)

    async def check_availability(self, domain: str = "default") -> bool:
        """
        Check if a rate limit slot is immediately available without acquiring it.
        
        Args:
            domain: The API domain to check
            
        Returns:
            True if a slot is available, False otherwise
        """
        if not self.enabled:
            return True

        domain_config = self._get_domain_config(domain)
        if not domain_config:
            return True

        max_calls = domain_config['calls']
        period_seconds = domain_config['period']
        now = time.monotonic()

        async with self.domain_locks[domain]:
            # Clean up old timestamps
            while (self.call_timestamps[domain] and 
                   self.call_timestamps[domain][0] <= now - period_seconds):
                self.call_timestamps[domain].popleft()
            
            return len(self.call_timestamps[domain]) < max_calls

    def get_domain_stats(self, domain: str = "default") -> dict:
        """
        Get current statistics for a domain.
        
        Args:
            domain: The domain to get stats for
            
        Returns:
            Dictionary with current call count, max calls, and period
        """
        domain_config = self._get_domain_config(domain)
        if not domain_config:
            return {"calls": 0, "max_calls": 0, "period": 0, "enabled": False}

        now = time.monotonic()
        period_seconds = domain_config['period']
        
        # Count recent calls (without modifying the deque)
        recent_calls = sum(1 for timestamp in self.call_timestamps[domain] 
                          if timestamp > now - period_seconds)
        
        return {
            "calls": recent_calls,
            "max_calls": domain_config['calls'],
            "period": period_seconds,
            "enabled": self.enabled
        }

    async def reset_domain(self, domain: str = "default") -> None:
        """
        Reset the call history for a specific domain.
        
        Args:
            domain: The domain to reset
        """
        async with self.domain_locks[domain]:
            self.call_timestamps[domain].clear()
            logger.info(f"Reset rate limit history for domain '{domain}'")

    async def close(self) -> None:
        """Clean up resources."""
        # Clear all timestamps
        for domain in list(self.call_timestamps.keys()):
            await self.reset_domain(domain)
        
        logger.info("RateLimiterService closed and cleaned up")

    def __del__(self):
        """Cleanup on destruction."""
        if hasattr(self, '_initialized'):
            logger.debug("RateLimiterService destroyed")

# Factory function for easy creation
def create_rate_limiter(config: Optional[dict] = None) -> RateLimiterService:
    """
    Create a new RateLimiterService instance.
    
    For most use cases, prefer this over the singleton pattern.
    """
    return RateLimiterService(config)

# Example usage (conceptual, would be in an API connector):
# class SomeAPI:
#     def __init__(self, rate_limiter: RateLimiterService, api_domain: str):
#         self.rate_limiter = rate_limiter
#         self.api_domain = api_domain
# 
#     def make_api_call(self, *args, **kwargs):
#         self.rate_limiter.acquire(self.api_domain)
#         # ... actual API call logic ...

# Global instance (optional)
# rate_limiter_service = RateLimiterService(config=config_manager.get_section("RATE_LIMITER")) 