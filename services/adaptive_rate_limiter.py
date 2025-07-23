#!/usr/bin/env python3
"""
Adaptive Rate Limiter - Enhanced rate limiting with exponential backoff
Improves API request pacing and reduces rate limit hits
"""

import time
import logging
import asyncio
from typing import Dict, Optional, List
from dataclasses import dataclass
from collections import defaultdict, deque

logger = logging.getLogger(__name__)

@dataclass
class RateLimitState:
    """Track rate limiting state for a specific domain"""
    request_interval: float
    consecutive_successes: int
    consecutive_failures: int
    last_request_time: float
    last_rate_limit_time: float
    total_requests: int
    rate_limit_hits: int
    
class AdaptiveRateLimiter:
    """
    Advanced adaptive rate limiter with intelligent request pacing.
    
    Features:
    - Exponential backoff after rate limit hits
    - Gradual optimization when requests succeed
    - Per-domain adaptive intervals
    - Smart reset time handling
    """
    
    def __init__(self, config: Optional[Dict] = None):
        """Initialize adaptive rate limiter"""
        
        if config is None:
            config = {
                "domains": {
                    "birdeye": {
                        "base_interval": 0.067,  # ~15 RPS for starter plan
                        "min_interval": 0.050,   # Aggressive minimum (20 RPS)
                        "max_interval": 2.0,     # Conservative maximum
                        "backoff_multiplier": 1.5,
                        "success_reduction": 0.95,
                        "optimization_threshold": 5  # Successes before optimization
                    },
                    "birdeye_wallet": {
                        "base_interval": 2.0,    # 30 RPM = 0.5 RPS
                        "min_interval": 1.8,
                        "max_interval": 10.0,
                        "backoff_multiplier": 2.0,
                        "success_reduction": 0.9,
                        "optimization_threshold": 3
                    },
                    "default": {
                        "base_interval": 0.2,    # 5 RPS default
                        "min_interval": 0.1,
                        "max_interval": 5.0,
                        "backoff_multiplier": 2.0,
                        "success_reduction": 0.9,
                        "optimization_threshold": 5
                    }
                }
            }
        
        self.config = config
        self.domain_states: Dict[str, RateLimitState] = {}
        self.domain_locks: Dict[str, asyncio.Lock] = defaultdict(asyncio.Lock)
        self.enabled = True
        
        # Initialize domain states
        for domain, domain_config in self.config["domains"].items():
            self.domain_states[domain] = RateLimitState(
                request_interval=domain_config["base_interval"],
                consecutive_successes=0,
                consecutive_failures=0,
                last_request_time=0.0,
                last_rate_limit_time=0.0,
                total_requests=0,
                rate_limit_hits=0
            )
        
        logger.info(f"🚀 AdaptiveRateLimiter initialized with {len(self.config['domains'])} domains")
    
    def _get_domain_config(self, domain: str) -> Dict:
        """Get configuration for domain with fallback to default"""
        return self.config["domains"].get(domain, self.config["domains"]["default"])
    
    def _get_domain_state(self, domain: str) -> RateLimitState:
        """Get or create domain state"""
        if domain not in self.domain_states:
            domain_config = self._get_domain_config(domain)
            self.domain_states[domain] = RateLimitState(
                request_interval=domain_config["base_interval"],
                consecutive_successes=0,
                consecutive_failures=0,
                last_request_time=0.0,
                last_rate_limit_time=0.0,
                total_requests=0,
                rate_limit_hits=0
            )
        return self.domain_states[domain]
    
    async def acquire(self, domain: str = "default") -> None:
        """
        Acquire rate limit slot with adaptive pacing.
        
        Args:
            domain: API domain to acquire slot for
        """
        if not self.enabled:
            return
        
        domain_config = self._get_domain_config(domain)
        state = self._get_domain_state(domain)
        
        async with self.domain_locks[domain]:
            now = time.time()
            
            # Calculate time since last request
            time_since_last = now - state.last_request_time
            
            # If we need to wait, do so
            if time_since_last < state.request_interval:
                wait_time = state.request_interval - time_since_last
                logger.debug(f"⏳ {domain}: Waiting {wait_time:.3f}s (interval: {state.request_interval:.3f}s)")
                await asyncio.sleep(wait_time)
                now = time.time()
            
            # Update state
            state.last_request_time = now
            state.total_requests += 1
    
    def on_request_success(self, domain: str = "default") -> None:
        """
        Record successful request and optimize interval.
        
        Args:
            domain: API domain that succeeded
        """
        domain_config = self._get_domain_config(domain)
        state = self._get_domain_state(domain)
        
        state.consecutive_successes += 1
        state.consecutive_failures = 0
        
        # Gradually optimize interval after consecutive successes
        if state.consecutive_successes >= domain_config["optimization_threshold"]:
            old_interval = state.request_interval
            state.request_interval = max(
                domain_config["min_interval"],
                state.request_interval * domain_config["success_reduction"]
            )
            
            if abs(old_interval - state.request_interval) > 0.001:
                logger.debug(f"📈 {domain}: Optimized interval {old_interval:.3f}s → {state.request_interval:.3f}s")
            
            state.consecutive_successes = 0
    
    def on_rate_limit_hit(self, domain: str = "default", reset_time: Optional[float] = None) -> None:
        """
        Record rate limit hit and apply backoff.
        
        Args:
            domain: API domain that hit rate limit
            reset_time: When rate limit resets (timestamp)
        """
        domain_config = self._get_domain_config(domain)
        state = self._get_domain_state(domain)
        
        state.consecutive_failures += 1
        state.consecutive_successes = 0
        state.rate_limit_hits += 1
        state.last_rate_limit_time = time.time()
        
        # Apply exponential backoff
        old_interval = state.request_interval
        state.request_interval = min(
            domain_config["max_interval"],
            state.request_interval * domain_config["backoff_multiplier"]
        )
        
        logger.warning(f"🚫 {domain}: Rate limit hit! Interval {old_interval:.3f}s → {state.request_interval:.3f}s")
        
        # If reset time provided, ensure we wait until then
        if reset_time:
            wait_until_reset = reset_time - time.time() + 1.0  # Add 1s buffer
            if wait_until_reset > 0:
                logger.info(f"⏰ {domain}: Waiting {wait_until_reset:.1f}s until rate limit reset")
                # Note: This should be handled by the caller as we can't await here
    
    async def wait_for_reset(self, domain: str, reset_time: float) -> None:
        """
        Wait until rate limit reset time.
        
        Args:
            domain: API domain
            reset_time: Reset timestamp
        """
        wait_time = reset_time - time.time() + 1.0  # 1s buffer
        if wait_time > 0:
            logger.info(f"⏰ {domain}: Waiting {wait_time:.1f}s for rate limit reset")
            await asyncio.sleep(wait_time)
    
    def get_stats(self, domain: str = None) -> Dict:
        """Get rate limiting statistics"""
        if domain:
            state = self._get_domain_state(domain)
            return {
                "domain": domain,
                "current_interval": state.request_interval,
                "total_requests": state.total_requests,
                "rate_limit_hits": state.rate_limit_hits,
                "hit_rate": state.rate_limit_hits / max(1, state.total_requests) * 100,
                "consecutive_successes": state.consecutive_successes,
                "consecutive_failures": state.consecutive_failures
            }
        else:
            # Return stats for all domains
            return {
                domain: self.get_stats(domain) 
                for domain in self.domain_states.keys()
            }
    
    def reset_domain(self, domain: str) -> None:
        """Reset domain state to defaults"""
        domain_config = self._get_domain_config(domain)
        if domain in self.domain_states:
            self.domain_states[domain].request_interval = domain_config["base_interval"]
            self.domain_states[domain].consecutive_successes = 0
            self.domain_states[domain].consecutive_failures = 0
            logger.info(f"🔄 {domain}: Rate limiter state reset")


class DataAvailabilityChecker:
    """
    Quick data availability check to avoid expensive OHLCV calls on tokens without data.
    """
    
    def __init__(self, birdeye_api, cache_manager):
        self.birdeye_api = birdeye_api
        self.cache_manager = cache_manager
        self.logger = logging.getLogger(__name__)
    
    async def check_data_availability(self, token_address: str) -> Dict[str, any]:
        """
        Quick check for token data availability before expensive OHLCV calls.
        
        Returns:
            Dict with availability info and metadata
        """
        cache_key = f"data_availability_{token_address}"
        cached_result = self.cache_manager.get(cache_key)
        if cached_result:
            return cached_result
        
        result = {
            "has_recent_trades": False,
            "has_sufficient_volume": False,
            "estimated_age_hours": None,
            "skip_ohlcv": True,
            "reason": "no_data_conditions_met"
        }
        
        try:
            # Method 1: Check recent trades (cheaper than OHLCV)
            recent_trades = await self._check_recent_trades(token_address)
            if recent_trades:
                result["has_recent_trades"] = True
                result["last_trade_time"] = recent_trades.get("last_trade_time")
                
                # Check if trades are recent enough (last hour)
                if recent_trades.get("last_trade_time", 0) > time.time() - 3600:
                    result["skip_ohlcv"] = False
                    result["reason"] = "recent_trades_found"
            
            # Method 2: Check token metadata for age estimation
            metadata = await self._get_quick_metadata(token_address)
            if metadata:
                result["estimated_age_hours"] = metadata.get("age_hours")
                
                # Very new tokens (< 24h) should have OHLCV checked
                if metadata.get("age_hours", 999) < 24:
                    result["skip_ohlcv"] = False
                    result["reason"] = "new_token"
            
            # Method 3: Check basic price/volume data
            basic_data = await self._get_basic_price_data(token_address)
            if basic_data:
                volume_24h = basic_data.get("volume_24h", 0)
                if volume_24h > 1000:  # $1000+ volume suggests active trading
                    result["has_sufficient_volume"] = True
                    result["skip_ohlcv"] = False
                    result["reason"] = "sufficient_volume"
        
        except Exception as e:
            self.logger.debug(f"Data availability check failed for {token_address}: {e}")
            result["reason"] = "check_failed"
        
        # Cache result for 5 minutes
        self.cache_manager.set(cache_key, result, ttl=300)
        return result
    
    async def _check_recent_trades(self, token_address: str) -> Optional[Dict]:
        """Check for recent trades using lightweight endpoint"""
        try:
            # Use the correct trades endpoint for token trades
            trades_data = await self.birdeye_api._make_request(
                "/defi/txs/token", 
                params={"address": token_address, "limit": 1, "tx_type": "swap"},
                custom_headers={"x-chain": "solana"}
            )
            
            if trades_data and trades_data.get("data"):
                data_items = trades_data["data"]
                if isinstance(data_items, dict) and "items" in data_items:
                    data_items = data_items["items"]
                elif isinstance(data_items, list):
                    data_items = data_items
                else:
                    data_items = []
                    
                if data_items and len(data_items) > 0:
                    latest_trade = data_items[0]
                    return {
                        "last_trade_time": latest_trade.get("blockUnixTime", latest_trade.get("block_time", 0)),
                        "last_trade_volume": latest_trade.get("basePrice", latest_trade.get("volume_usd", 0))
                    }
        except Exception as e:
            self.logger.debug(f"Recent trades check failed: {e}")
        
        return None
    
    async def _get_quick_metadata(self, token_address: str) -> Optional[Dict]:
        """Get basic token metadata for age estimation"""
        try:
            metadata = await self.birdeye_api.get_token_metadata(token_address)
            if metadata:
                creation_time = metadata.get("creation_time")
                if creation_time:
                    age_hours = (time.time() - creation_time) / 3600
                    return {"age_hours": age_hours}
        except Exception as e:
            self.logger.debug(f"Quick metadata check failed: {e}")
        
        return None
    
    async def _get_basic_price_data(self, token_address: str) -> Optional[Dict]:
        """Get basic price/volume data without OHLCV"""
        try:
            # Use token_overview endpoint which has volume data
            overview_data = await self.birdeye_api._make_request(
                "/defi/token_overview",
                params={"address": token_address}
            )
            
            if overview_data and overview_data.get("data"):
                data = overview_data["data"]
                return {
                    "volume_24h": data.get("v24hUSD", 0),
                    "price": data.get("price", 0),
                    "last_trade_time": data.get("lastTradeUnixTime", 0)
                }
        except Exception as e:
            self.logger.debug(f"Basic price data check failed: {e}")
        
        return None