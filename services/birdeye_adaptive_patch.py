#!/usr/bin/env python3
"""
BirdEye API Adaptive Rate Limiting Patch
Enhances the existing BirdEye connector with adaptive rate limiting and data availability checks
"""

import time
import logging
from typing import Dict, Any, Optional
import re

from services.adaptive_rate_limiter import AdaptiveRateLimiter, DataAvailabilityChecker

class BirdeyeAPIEnhanced:
    """
    Enhanced BirdEye API wrapper with adaptive rate limiting and smart data availability checks.
    
    This class acts as a mixin/patch for the existing BirdeyeAPI class.
    """
    
    def __init__(self, original_birdeye_api):
        """Initialize enhanced wrapper around existing BirdEye API"""
        self.original_api = original_birdeye_api
        self.logger = original_birdeye_api.logger
        
        # Initialize adaptive rate limiter
        self.adaptive_rate_limiter = AdaptiveRateLimiter({
            "domains": {
                "birdeye": {
                    "base_interval": 0.067,  # ~15 RPS for starter plan
                    "min_interval": 0.050,   # Aggressive minimum (20 RPS)
                    "max_interval": 2.0,     # Conservative maximum
                    "backoff_multiplier": 1.5,
                    "success_reduction": 0.95,
                    "optimization_threshold": 5
                },
                "birdeye_wallet": {
                    "base_interval": 2.0,    # 30 RPM = 0.5 RPS
                    "min_interval": 1.8,
                    "max_interval": 10.0,
                    "backoff_multiplier": 2.0,
                    "success_reduction": 0.9,
                    "optimization_threshold": 3
                }
            }
        })
        
        # Initialize data availability checker
        self.data_availability_checker = DataAvailabilityChecker(
            self.original_api, 
            self.original_api.cache_manager
        )
        
        self.logger.info("🚀 BirdEye API Enhanced with adaptive rate limiting and data availability checks")
    
    def _get_rate_limit_domain(self, endpoint: str) -> str:
        """Determine rate limit domain based on endpoint"""
        if '/wallet/' in endpoint or 'wallet' in endpoint.lower():
            return 'birdeye_wallet'
        return 'birdeye'
    
    async def _make_request_enhanced(self, endpoint: str, params: Optional[Dict[str, Any]] = None, **kwargs) -> Any:
        """
        Enhanced request method with adaptive rate limiting.
        Wraps the original _make_request with intelligent pacing.
        """
        domain = self._get_rate_limit_domain(endpoint)
        
        # Apply adaptive rate limiting
        await self.adaptive_rate_limiter.acquire(domain)
        
        try:
            # Make the actual request using original method
            result = await self.original_api._make_request(endpoint, params, **kwargs)
            
            # Record success for rate limiter optimization
            self.adaptive_rate_limiter.on_request_success(domain)
            
            return result
            
        except Exception as e:
            # Check if it's a rate limit error
            if "429" in str(e) or "rate limit" in str(e).lower():
                # Extract reset time if available
                reset_time = self._extract_reset_time(str(e))
                self.adaptive_rate_limiter.on_rate_limit_hit(domain, reset_time)
                
                # Wait for reset if provided
                if reset_time:
                    await self.adaptive_rate_limiter.wait_for_reset(domain, reset_time)
                
            raise e
    
    def _extract_reset_time(self, error_message: str) -> Optional[float]:
        """Extract rate limit reset time from error message"""
        try:
            # Look for patterns like "reset=1234567890" or "reset_time=1234567890"
            match = re.search(r'reset[_=](\d+)', error_message)
            if match:
                return float(match.group(1))
        except Exception:
            pass
        return None
    
    async def get_ohlcv_data_enhanced(self, token_address: str, time_frame: str = 'auto', limit: int = 60) -> Optional[Dict[str, Any]]:
        """
        Enhanced OHLCV data collection with multi-timeframe hierarchy and data availability checks.
        """
        # First, check if we should skip this token entirely
        availability = await self.data_availability_checker.check_data_availability(token_address)
        
        if availability.get("skip_ohlcv", True):
            reason = availability.get("reason", "unknown")
            self.logger.debug(f"⏭️ Skipping OHLCV for {token_address}: {reason}")
            return {
                "data": [],
                "timeframe": time_frame,
                "skipped": True,
                "skip_reason": reason,
                "availability_info": availability
            }
        
        # If we should get OHLCV data, use multi-timeframe hierarchy
        if time_frame == 'auto':
            timeframes = self._get_timeframe_hierarchy(availability)
        else:
            timeframes = [time_frame]
        
        for tf in timeframes:
            try:
                self.logger.debug(f"🔍 Trying OHLCV timeframe {tf} for {token_address}")
                
                # Use enhanced request method
                result = await self._make_request_enhanced(
                    "/defi/v3/ohlcv",
                    params={
                        "address": token_address,
                        "type": tf,
                        "time_from": int(time.time()) - 86400,  # 24h ago
                        "time_to": int(time.time())
                    }
                )
                
                if result and result.get("data") and len(result["data"]) > 5:
                    self.logger.info(f"✅ OHLCV data found for {token_address} with timeframe {tf}")
                    return {
                        "data": result["data"],
                        "timeframe": tf,
                        "availability_info": availability,
                        "data_quality": self._assess_data_quality(result["data"])
                    }
                    
            except Exception as e:
                if "429" in str(e):
                    # Don't try more timeframes if rate limited
                    self.logger.warning(f"🚫 Rate limited while fetching OHLCV for {token_address}")
                    break
                
                self.logger.debug(f"❌ OHLCV failed for {token_address} with timeframe {tf}: {e}")
                continue
        
        # No data found with any timeframe
        self.logger.debug(f"❌ No OHLCV data available for {token_address} with any timeframe")
        return {
            "data": [],
            "timeframe": timeframes[0] if timeframes else time_frame,
            "availability_info": availability,
            "no_data_reason": "insufficient_trading_data"
        }
    
    def _get_timeframe_hierarchy(self, availability_info: Dict) -> list:
        """
        Get appropriate timeframe hierarchy based on token characteristics.
        Returns timeframes in order of preference (most granular first).
        """
        age_hours = availability_info.get("estimated_age_hours", 999)
        has_recent_trades = availability_info.get("has_recent_trades", False)
        
        if age_hours < 1:  # < 1 hour old
            return ['1m', '5m', '15m', '30m']
        elif age_hours < 6:  # < 6 hours old
            return ['5m', '15m', '30m', '1h']
        elif age_hours < 24:  # < 1 day old
            return ['15m', '30m', '1h', '2h']
        elif has_recent_trades:  # Older but active
            return ['30m', '1h', '2h', '4h']
        else:  # Older and less active
            return ['1h', '2h', '4h', '6h']
    
    def _assess_data_quality(self, ohlcv_data: list) -> Dict[str, Any]:
        """Assess the quality of OHLCV data"""
        if not ohlcv_data:
            return {"quality_score": 0, "reason": "no_data"}
        
        # Basic quality metrics
        data_points = len(ohlcv_data)
        
        # Check for non-zero volumes
        volume_points = sum(1 for candle in ohlcv_data if candle.get('v', 0) > 0)
        volume_ratio = volume_points / data_points if data_points > 0 else 0
        
        # Calculate quality score
        quality_score = min(100, (data_points * 2) + (volume_ratio * 50))
        
        return {
            "quality_score": quality_score,
            "data_points": data_points,
            "volume_ratio": volume_ratio,
            "has_sufficient_data": quality_score > 30
        }
    
    def get_rate_limiter_stats(self) -> Dict[str, Any]:
        """Get adaptive rate limiter statistics"""
        return self.adaptive_rate_limiter.get_stats()
    
    def reset_rate_limiter(self, domain: str = None) -> None:
        """Reset rate limiter for domain or all domains"""
        if domain:
            self.adaptive_rate_limiter.reset_domain(domain)
        else:
            for d in ['birdeye', 'birdeye_wallet']:
                self.adaptive_rate_limiter.reset_domain(d)
    
    # Proxy other methods to original API
    def __getattr__(self, name):
        """Proxy all other method calls to original API"""
        return getattr(self.original_api, name)


# Utility function to patch existing BirdEye API instances
def enhance_birdeye_api(birdeye_api):
    """
    Enhance an existing BirdEye API instance with adaptive rate limiting.
    
    Usage:
        enhanced_api = enhance_birdeye_api(original_birdeye_api)
        
    Returns:
        Enhanced API with adaptive rate limiting and data availability checks
    """
    return BirdeyeAPIEnhanced(birdeye_api)