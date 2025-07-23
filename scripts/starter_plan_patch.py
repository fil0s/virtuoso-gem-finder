
# Birdeye Starter Plan Compatibility Patch
# This patch modifies the system to work within starter plan limitations

import time
import asyncio
from typing import Dict, List, Optional, Any

class StarterPlanBirdeyeAPI:
    """Wrapper for BirdeyeAPI that enforces starter plan limitations"""
    
    def __init__(self, original_api):
        self.original_api = original_api
        self.last_request_time = 0
        self.requests_this_minute = 0
        self.minute_start_time = time.time()
        
        # Starter plan rate limiting
        self.max_rpm = 30
        self.min_delay = 2.0
        
    async def _enforce_rate_limit(self):
        """Enforce starter plan rate limits"""
        current_time = time.time()
        
        # Reset counter if minute has passed
        if current_time - self.minute_start_time >= 60:
            self.requests_this_minute = 0
            self.minute_start_time = current_time
        
        # Check if we've hit the rate limit
        if self.requests_this_minute >= self.max_rpm:
            wait_time = 60 - (current_time - self.minute_start_time)
            if wait_time > 0:
                print(f"⚠️ Rate limit reached. Waiting {wait_time:.1f} seconds...")
                await asyncio.sleep(wait_time)
                self.requests_this_minute = 0
                self.minute_start_time = time.time()
        
        # Enforce minimum delay between requests
        time_since_last = current_time - self.last_request_time
        if time_since_last < self.min_delay:
            await asyncio.sleep(self.min_delay - time_since_last)
        
        self.last_request_time = time.time()
        self.requests_this_minute += 1
    
    async def get_token_metadata_multiple(self, addresses: List[str], scan_id: Optional[str] = None) -> Dict[str, Any]:
        """Fallback to individual calls for starter plan"""
        print("⚠️ Starter plan: Using individual calls instead of batch metadata")
        
        results = {}
        for address in addresses:
            await self._enforce_rate_limit()
            try:
                overview = await self.original_api.get_token_overview(address)
                if overview:
                    results[address] = overview
            except Exception as e:
                print(f"❌ Failed to get overview for {address}: {e}")
        
        return results
    
    async def get_price_volume_multi(self, addresses: List[str], time_range: str = "24h", scan_id: Optional[str] = None) -> Dict[str, Any]:
        """Fallback to individual calls for starter plan"""
        print("⚠️ Starter plan: Using individual calls instead of batch price/volume")
        
        results = {}
        for address in addresses:
            await self._enforce_rate_limit()
            try:
                price_data = await self.original_api.get_price(address)
                if price_data:
                    results[address] = price_data
            except Exception as e:
                print(f"❌ Failed to get price for {address}: {e}")
        
        return results
    
    async def get_token_trade_data_multiple(self, addresses: List[str], time_frame: str = "24h", scan_id: Optional[str] = None) -> Dict[str, Any]:
        """Fallback to individual calls for starter plan"""
        print("⚠️ Starter plan: Using individual calls instead of batch trade data")
        
        results = {}
        for address in addresses:
            await self._enforce_rate_limit()
            try:
                # Use individual transaction endpoint
                tx_data = await self.original_api.get_token_transactions(address)
                if tx_data:
                    results[address] = tx_data
            except Exception as e:
                print(f"❌ Failed to get trade data for {address}: {e}")
        
        return results

# Patch the original BirdeyeAPI class
def apply_starter_plan_patch(birdeye_api):
    """Apply starter plan compatibility patch"""
    return StarterPlanBirdeyeAPI(birdeye_api)
