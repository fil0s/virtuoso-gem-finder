#!/usr/bin/env python3
"""
Simple Orca and Raydium API Test
Tests basic API connectivity without cache dependencies
"""

import asyncio
import aiohttp
import json
from datetime import datetime

class SimpleOrcaTest:
    def __init__(self):
        self.base_url = "https://api.orca.so"
        self.session = None
    
    async def __aenter__(self):
        self.session = aiohttp.ClientSession()
        return self
        
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.session:
            await self.session.close()
    
    async def test_pools(self):
        """Test Orca pools endpoint"""
        try:
            print("🌊 Testing Orca API...")
            async with self.session.get(f"{self.base_url}/pools", timeout=30) as response:
                if response.status == 200:
                    data = await response.json()
                    print(f"  ✅ Orca pools: {len(data) if data else 0} pools found")
                    return data
                else:
                    print(f"  ❌ Orca API error: {response.status}")
                    return None
        except Exception as e:
            print(f"  ❌ Orca API failed: {e}")
            return None

class SimpleRaydiumTest:
    def __init__(self):
        self.base_url = "https://api.raydium.io"
        self.session = None
    
    async def __aenter__(self):
        self.session = aiohttp.ClientSession()
        return self
        
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.session:
            await self.session.close()
    
    async def test_pools(self):
        """Test Raydium pools endpoint"""
        try:
            print("⚡ Testing Raydium API...")
            async with self.session.get(f"{self.base_url}/pools", timeout=30) as response:
                if response.status == 200:
                    data = await response.json()
                    print(f"  ✅ Raydium pools: {len(data) if data else 0} pools found")
                    return data
                else:
                    print(f"  ❌ Raydium API error: {response.status}")
                    return None
        except Exception as e:
            print(f"  ❌ Raydium API failed: {e}")
            return None
    
    async def test_pairs(self):
        """Test Raydium pairs endpoint"""
        try:
            async with self.session.get(f"{self.base_url}/pairs", timeout=30) as response:
                if response.status == 200:
                    data = await response.json()
                    print(f"  ✅ Raydium pairs: {len(data) if data else 0} pairs found")
                    return data
                else:
                    print(f"  ❌ Raydium pairs API error: {response.status}")
                    return None
        except Exception as e:
            print(f"  ❌ Raydium pairs API failed: {e}")
            return None

async def main():
    """Run simple API tests"""
    print("🚀 Simple Orca & Raydium API Test")
    print(f"📅 {datetime.now().isoformat()}")
    
    # Test Orca
    async with SimpleOrcaTest() as orca:
        orca_pools = await orca.test_pools()
        
        if orca_pools:
            print(f"  📊 Sample Orca pool: {json.dumps(orca_pools[0], indent=2)[:200]}...")
    
    # Test Raydium
    async with SimpleRaydiumTest() as raydium:
        raydium_pools = await raydium.test_pools()
        raydium_pairs = await raydium.test_pairs()
        
        if raydium_pools:
            print(f"  📊 Sample Raydium pool: {json.dumps(raydium_pools[0], indent=2)[:200]}...")
        
        if raydium_pairs:
            print(f"  💱 Sample Raydium pair: {json.dumps(raydium_pairs[0], indent=2)[:200]}...")
    
    print("\n✅ Simple API test completed!")

if __name__ == "__main__":
    asyncio.run(main()) 