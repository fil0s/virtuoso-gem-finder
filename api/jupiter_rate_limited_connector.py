#!/usr/bin/env python3
"""
Jupiter Rate-Limited Financial Connector
Production-ready connector with proper rate limiting based on Jupiter's official API documentation
"""

import asyncio
import aiohttp
import logging
import time
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Tuple
import json
from dataclasses import dataclass

logger = logging.getLogger(__name__)

@dataclass
class RateLimitConfig:
    """Rate limiting configuration based on Jupiter API documentation"""
    # Free tier limits (lite-api.jup.ag)
    requests_per_minute: int = 60
    tokens_per_period: int = 60
    period_seconds: int = 60
    min_request_interval: float = 1.5  # Conservative spacing (40 req/min max)
    max_retries: int = 3
    base_backoff_delay: float = 2.0
    max_backoff_delay: float = 30.0

class JupiterTokenBucket:
    """Token bucket implementation for Jupiter API rate limiting"""
    
    def __init__(self, config: RateLimitConfig):
        self.config = config
        self.tokens = config.tokens_per_period
        self.last_refill = time.time()
        self.last_request = 0.0
        
    def can_make_request(self) -> bool:
        """Check if we can make a request without hitting rate limits"""
        self._refill_tokens()
        
        # Check token availability
        if self.tokens <= 0:
            return False
            
        # Check minimum interval since last request
        time_since_last = time.time() - self.last_request
        if time_since_last < self.config.min_request_interval:
            return False
            
        return True
    
    def consume_token(self):
        """Consume a token for making a request"""
        if self.tokens > 0:
            self.tokens -= 1
            self.last_request = time.time()
    
    def _refill_tokens(self):
        """Refill tokens based on elapsed time"""
        now = time.time()
        time_passed = now - self.last_refill
        
        if time_passed >= self.config.period_seconds:
            # Full refill after period
            self.tokens = self.config.tokens_per_period
            self.last_refill = now
    
    def time_until_next_request(self) -> float:
        """Calculate time to wait before next request"""
        self._refill_tokens()
        
        if self.tokens > 0:
            time_since_last = time.time() - self.last_request
            if time_since_last < self.config.min_request_interval:
                return self.config.min_request_interval - time_since_last
            return 0.0
        
        # No tokens available - wait for refill
        time_since_refill = time.time() - self.last_refill
        return max(0.0, self.config.period_seconds - time_since_refill)

class JupiterRateLimitedConnector:
    """Production Jupiter connector with proper rate limiting"""
    
    def __init__(self, config: Optional[RateLimitConfig] = None):
        self.config = config or RateLimitConfig()
        self.token_bucket = JupiterTokenBucket(self.config)
        self.session = None
        
        # Use main endpoint (better token support than lite-api)
        self.base_url = "https://quote-api.jup.ag"
        self.quote_endpoint = f"{self.base_url}/v6/quote"
        
        # Statistics tracking
        self.stats = {
            "total_requests": 0,
            "successful_requests": 0,
            "rate_limited_requests": 0,
            "failed_requests": 0,
            "total_wait_time": 0.0
        }
    
    async def __aenter__(self):
        self.session = aiohttp.ClientSession()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.session:
            await self.session.close()
    
    async def _wait_for_rate_limit(self):
        """Wait for rate limiting if necessary"""
        wait_time = self.token_bucket.time_until_next_request()
        if wait_time > 0:
            logger.debug(f"Rate limiting: waiting {wait_time:.2f}s before next request")
            self.stats["total_wait_time"] += wait_time
            await asyncio.sleep(wait_time)
    
    async def _make_request_with_retry(self, url: str, params: Dict[str, Any]) -> Tuple[bool, Optional[Dict], Optional[str]]:
        """Make a request with exponential backoff retry logic"""
        
        for attempt in range(self.config.max_retries + 1):
            # Wait for rate limiting
            await self._wait_for_rate_limit()
            
            # Check if we can make the request
            if not self.token_bucket.can_make_request():
                wait_time = self.token_bucket.time_until_next_request()
                logger.warning(f"Rate limit exceeded, waiting {wait_time:.2f}s")
                await asyncio.sleep(wait_time)
                continue
            
            # Consume token and make request
            self.token_bucket.consume_token()
            self.stats["total_requests"] += 1
            
            try:
                async with self.session.get(url, params=params) as response:
                    if response.status == 200:
                        data = await response.json()
                        self.stats["successful_requests"] += 1
                        return True, data, None
                    
                    elif response.status == 429:
                        # Rate limited
                        self.stats["rate_limited_requests"] += 1
                        error_text = await response.text()
                        
                        if attempt < self.config.max_retries:
                            # Exponential backoff
                            backoff_delay = min(
                                self.config.base_backoff_delay * (2 ** attempt),
                                self.config.max_backoff_delay
                            )
                            logger.warning(f"Rate limited (429), retrying in {backoff_delay:.2f}s (attempt {attempt + 1})")
                            await asyncio.sleep(backoff_delay)
                            continue
                        else:
                            logger.error(f"Rate limited after {self.config.max_retries} retries")
                            return False, None, f"Rate limited: {error_text}"
                    
                    else:
                        # Other error
                        error_text = await response.text()
                        self.stats["failed_requests"] += 1
                        return False, None, f"HTTP {response.status}: {error_text}"
            
            except Exception as e:
                self.stats["failed_requests"] += 1
                if attempt < self.config.max_retries:
                    backoff_delay = min(
                        self.config.base_backoff_delay * (2 ** attempt),
                        self.config.max_backoff_delay
                    )
                    logger.warning(f"Request failed: {e}, retrying in {backoff_delay:.2f}s")
                    await asyncio.sleep(backoff_delay)
                    continue
                else:
                    return False, None, str(e)
        
        return False, None, "Max retries exceeded"
    
    async def get_token_price(self, token_address: str, amount: int = 1000000) -> Tuple[bool, Optional[float], Dict[str, Any]]:
        """Get token price via Jupiter quote API with rate limiting"""
        
        # Try both directions for price discovery
        scenarios = [
            {
                "inputMint": token_address,
                "outputMint": "EPjFWdd5AufqSSqeM2qN1xzybapC8G4wEGGkZwyTDt1v",  # USDC
                "amount": str(amount),
                "direction": "to_usdc"
            },
            {
                "inputMint": "EPjFWdd5AufqSSqeM2qN1xzybapC8G4wEGGkZwyTDt1v",  # USDC
                "outputMint": token_address,
                "amount": str(amount),
                "direction": "from_usdc"
            }
        ]
        
        price_data = {
            "scenarios_attempted": 0,
            "successful_scenarios": 0,
            "price_derivable": False,
            "price": 0.0,
            "price_confidence": "none",
            "method": "failed",
            "route_info": {},
            "errors": []
        }
        
        for scenario in scenarios:
            price_data["scenarios_attempted"] += 1
            
            params = {
                "inputMint": scenario["inputMint"],
                "outputMint": scenario["outputMint"],
                "amount": scenario["amount"],
                "slippageBps": "50"
            }
            
            success, data, error = await self._make_request_with_retry(self.quote_endpoint, params)
            
            if success and data:
                price_data["successful_scenarios"] += 1
                
                # Calculate price based on direction
                if scenario["direction"] == "to_usdc":
                    # Token -> USDC: price = outAmount / inAmount
                    in_amount = float(data["inAmount"])
                    out_amount = float(data["outAmount"])
                    if in_amount > 0:
                        # USDC has 6 decimals, adjust for that
                        price = (out_amount / 1_000_000) / (in_amount / amount)
                        price_data["price"] = price
                        price_data["price_derivable"] = True
                        price_data["method"] = "quote_to_usdc"
                        price_data["price_confidence"] = "high"
                        
                elif scenario["direction"] == "from_usdc":
                    # USDC -> Token: price = inAmount / outAmount
                    in_amount = float(data["inAmount"])
                    out_amount = float(data["outAmount"])
                    if out_amount > 0:
                        # USDC has 6 decimals
                        price = (in_amount / 1_000_000) / (out_amount / amount)
                        if not price_data["price_derivable"]:  # Only use if we don't have a better price
                            price_data["price"] = price
                            price_data["price_derivable"] = True
                            price_data["method"] = "quote_from_usdc"
                            price_data["price_confidence"] = "medium"
                
                # Store route information
                price_data["route_info"][scenario["direction"]] = {
                    "route_plan": data.get("routePlan", []),
                    "price_impact": data.get("priceImpactPct", "0"),
                    "swap_value": data.get("swapUsdValue", "0")
                }
                
                # If we got a good price, we can return early
                if price_data["price_derivable"] and price_data["price"] > 0:
                    break
            
            else:
                price_data["errors"].append({
                    "scenario": scenario["direction"],
                    "error": error
                })
        
        return price_data["price_derivable"], price_data["price"], price_data
    
    async def analyze_token_liquidity(self, token_address: str) -> Dict[str, Any]:
        """Analyze token liquidity using multiple quote amounts"""
        
        test_amounts = [1_000, 10_000, 100_000, 1_000_000]  # Different USD amounts (in USDC micro-units)
        liquidity_data = {
            "liquidity_score": 0.0,
            "depth_analysis": [],
            "average_price_impact": 0.0,
            "route_complexity": 0.0,
            "liquidity_tier": "unknown"
        }
        
        total_price_impact = 0.0
        successful_tests = 0
        total_routes = 0
        
        for amount in test_amounts:
            params = {
                "inputMint": "EPjFWdd5AufqSSqeM2qN1xzybapC8G4wEGGkZwyTDt1v",  # USDC
                "outputMint": token_address,
                "amount": str(amount),
                "slippageBps": "50"
            }
            
            success, data, error = await self._make_request_with_retry(self.quote_endpoint, params)
            
            depth_result = {
                "amount_usd": amount / 1_000_000,
                "quote_successful": success,
                "price_impact": 100.0,  # Default to high impact
                "route_count": 0
            }
            
            if success and data:
                successful_tests += 1
                price_impact = float(data.get("priceImpactPct", "0"))
                route_count = len(data.get("routePlan", []))
                
                depth_result["price_impact"] = price_impact
                depth_result["route_count"] = route_count
                
                total_price_impact += price_impact
                total_routes += route_count
            
            liquidity_data["depth_analysis"].append(depth_result)
        
        # Calculate aggregate metrics
        if successful_tests > 0:
            liquidity_data["average_price_impact"] = total_price_impact / successful_tests
            liquidity_data["route_complexity"] = total_routes / successful_tests
            
            # Calculate liquidity score (0-10 scale)
            avg_impact = liquidity_data["average_price_impact"]
            route_complexity = liquidity_data["route_complexity"]
            
            # Lower price impact = better liquidity
            impact_score = max(0, 10 - (avg_impact * 1000))  # Scale price impact
            complexity_score = min(10, route_complexity * 2)  # Route availability
            
            liquidity_data["liquidity_score"] = (impact_score + complexity_score) / 2
            
            # Determine liquidity tier
            if liquidity_data["liquidity_score"] >= 7:
                liquidity_data["liquidity_tier"] = "excellent"
            elif liquidity_data["liquidity_score"] >= 5:
                liquidity_data["liquidity_tier"] = "good"
            elif liquidity_data["liquidity_score"] >= 3:
                liquidity_data["liquidity_tier"] = "moderate"
            elif liquidity_data["liquidity_score"] >= 1:
                liquidity_data["liquidity_tier"] = "low"
            else:
                liquidity_data["liquidity_tier"] = "very_low"
        
        return liquidity_data
    
    async def get_comprehensive_financial_data(self, token_address: str) -> Dict[str, Any]:
        """Get comprehensive financial data for a token with proper rate limiting"""
        
        start_time = time.time()
        
        logger.info(f"📊 Getting comprehensive financial data for {token_address[:8]}... (rate-limited)")
        
        # Get price data
        price_success, price, price_data = await self.get_token_price(token_address)
        
        # Get liquidity data (only if price derivation was successful)
        liquidity_data = {}
        if price_success:
            liquidity_data = await self.analyze_token_liquidity(token_address)
        
        # Estimate volume based on liquidity (rough proxy)
        estimated_volume = 0
        if price_success and liquidity_data.get("liquidity_score", 0) > 0:
            liquidity_score = liquidity_data["liquidity_score"]
            # Very rough volume estimation based on liquidity
            estimated_volume = (liquidity_score / 10) * 100_000 * price
        
        analysis_duration = time.time() - start_time
        
        comprehensive_data = {
            "token_address": token_address,
            "analysis_timestamp": datetime.now().isoformat(),
            "analysis_duration_seconds": round(analysis_duration, 2),
            "price": price if price_success else 0,
            "volume_24h_estimated": estimated_volume,
            "price_derivable": price_success,
            "price_analysis": price_data,
            "liquidity_analysis": liquidity_data,
            "data_quality_score": 1.0 if price_success else 0.0,
            "has_sufficient_data": price_success,
            "data_source": "jupiter_rate_limited_connector",
            "rate_limit_stats": self.get_stats()
        }
        
        logger.info(f"✅ Financial analysis complete for {token_address[:8]} in {analysis_duration:.2f}s")
        
        return comprehensive_data
    
    def get_stats(self) -> Dict[str, Any]:
        """Get connector statistics"""
        total_requests = self.stats["total_requests"]
        success_rate = (self.stats["successful_requests"] / total_requests * 100) if total_requests > 0 else 0
        
        return {
            "total_requests": total_requests,
            "successful_requests": self.stats["successful_requests"],
            "rate_limited_requests": self.stats["rate_limited_requests"],
            "failed_requests": self.stats["failed_requests"],
            "success_rate_percent": round(success_rate, 1),
            "total_wait_time_seconds": round(self.stats["total_wait_time"], 2),
            "current_tokens": self.token_bucket.tokens,
            "time_since_last_request": round(time.time() - self.token_bucket.last_request, 2)
        }
    
    def reset_stats(self):
        """Reset statistics tracking"""
        self.stats = {
            "total_requests": 0,
            "successful_requests": 0,
            "rate_limited_requests": 0,
            "failed_requests": 0,
            "total_wait_time": 0.0
        }

# Example usage and testing
async def test_rate_limited_connector():
    """Test the rate-limited connector"""
    
    test_tokens = [
        ("USELESS", "Dz9mQ9NzkBcCsuGPFJ3r1bS4wgqKMHBPiVuniW8Mbonk"),
        ("$michi", "5mbK36SZ7J19An8jFochhQS4of8g6BwUjbeCSxBSoWdp"),
        ("BILLY", "3B5wuUrMEi5yATD7on46hKfej3pfmd7t1RKgrsN3pump")
    ]
    
    async with JupiterRateLimitedConnector() as connector:
        logger.info("🚀 Testing Jupiter Rate-Limited Connector")
        logger.info("=" * 60)
        
        for token_name, token_address in test_tokens:
            logger.info(f"\n🔍 Testing {token_name} ({token_address[:8]}...)")
            
            try:
                data = await connector.get_comprehensive_financial_data(token_address)
                
                logger.info(f"📈 Results for {token_name}:")
                logger.info(f"   Price: ${data['price']:.6f}")
                logger.info(f"   Volume Est: ${data['volume_24h_estimated']:,.0f}")
                logger.info(f"   Price Derivable: {data['price_derivable']}")
                logger.info(f"   Data Quality: {data['data_quality_score']:.1f}")
                
            except Exception as e:
                logger.error(f"❌ Error testing {token_name}: {e}")
        
        # Print final stats
        stats = connector.get_stats()
        logger.info(f"\n📊 Final Statistics:")
        logger.info(f"   Total Requests: {stats['total_requests']}")
        logger.info(f"   Success Rate: {stats['success_rate_percent']}%")
        logger.info(f"   Rate Limited: {stats['rate_limited_requests']}")
        logger.info(f"   Total Wait Time: {stats['total_wait_time_seconds']}s")

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
    asyncio.run(test_rate_limited_connector()) 