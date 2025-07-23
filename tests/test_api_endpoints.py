#!/usr/bin/env python3
"""
Comprehensive API endpoint testing for Orca and Raydium
Tests current endpoints and researches alternatives
"""

import asyncio
import aiohttp
import json
import time
from typing import Dict, List, Optional, Any

class APIEndpointTester:
    def __init__(self):
        self.session = None
        self.results = {}
        
    async def __aenter__(self):
        self.session = aiohttp.ClientSession()
        return self
        
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.session:
            await self.session.close()
    
    async def test_endpoint(self, name: str, url: str, timeout: int = 30) -> Dict[str, Any]:
        """Test a single API endpoint and return detailed results"""
        print(f"\n🔍 Testing {name}: {url}")
        
        start_time = time.time()
        try:
            async with self.session.get(url, timeout=timeout) as response:
                response_time = time.time() - start_time
                
                # Get response headers
                headers = dict(response.headers)
                
                # Try to get response content
                try:
                    if response.content_type == 'application/json':
                        content = await response.json()
                        content_preview = str(content)[:500] + "..." if len(str(content)) > 500 else str(content)
                    else:
                        text_content = await response.text()
                        content_preview = text_content[:500] + "..." if len(text_content) > 500 else text_content
                        content = text_content
                except:
                    content = "Could not parse response content"
                    content_preview = "Could not parse response content"
                
                result = {
                    'status': 'success' if response.status == 200 else 'failed',
                    'status_code': response.status,
                    'response_time': response_time,
                    'content_type': response.content_type,
                    'content_length': len(str(content)) if content else 0,
                    'headers': headers,
                    'content_preview': content_preview,
                    'error': None
                }
                
                if response.status == 200:
                    print(f"✅ SUCCESS - Status: {response.status}, Time: {response_time:.2f}s")
                    print(f"   Content-Type: {response.content_type}")
                    print(f"   Content Length: {len(str(content))} chars")
                    if isinstance(content, (dict, list)):
                        print(f"   Data Type: {type(content).__name__}")
                        if isinstance(content, list):
                            print(f"   Array Length: {len(content)}")
                        elif isinstance(content, dict):
                            print(f"   Keys: {list(content.keys())[:5]}")
                else:
                    print(f"❌ FAILED - Status: {response.status}")
                    print(f"   Content Preview: {content_preview[:200]}")
                
                return result
                
        except asyncio.TimeoutError:
            response_time = time.time() - start_time
            print(f"⏰ TIMEOUT after {response_time:.2f}s")
            return {
                'status': 'timeout',
                'error': 'Request timed out',
                'response_time': response_time
            }
        except Exception as e:
            response_time = time.time() - start_time
            print(f"💥 ERROR: {str(e)}")
            return {
                'status': 'error',
                'error': str(e),
                'response_time': response_time
            }
    
    async def test_orca_endpoints(self) -> Dict[str, Any]:
        """Test various Orca API endpoints"""
        print("\n" + "="*50)
        print("🌊 TESTING ORCA API ENDPOINTS")
        print("="*50)
        
        endpoints_to_test = [
            # Current endpoint (legacy)
            ("Current Legacy Pool API", "https://archive.orca.so/legacy-pool/pools.json"),
            
            # Alternative Orca endpoints to try
            ("Orca API v1", "https://api.orca.so/v1/pools"),
            ("Orca API v2", "https://api.orca.so/v2/pools"),
            ("Orca Whirlpool API", "https://api.orca.so/whirlpools"),
            ("Orca Main API", "https://api.orca.so/pools"),
            ("Orca Analytics", "https://api.orca.so/analytics/pools"),
            
            # Try public endpoints
            ("Orca Public API", "https://orca-so.github.io/orca/pools.json"),
            ("Orca CDN", "https://cdn.orca.so/pools.json"),
            
            # Test if the base URLs respond
            ("Orca API Base", "https://api.orca.so/"),
            ("Orca Archive Base", "https://archive.orca.so/"),
        ]
        
        results = {}
        for name, url in endpoints_to_test:
            results[name] = await self.test_endpoint(name, url)
            await asyncio.sleep(1)  # Be respectful with rate limiting
        
        return results
    
    async def test_raydium_endpoints(self) -> Dict[str, Any]:
        """Test various Raydium API endpoints"""
        print("\n" + "="*50)
        print("☀️ TESTING RAYDIUM API ENDPOINTS")
        print("="*50)
        
        endpoints_to_test = [
            # Current endpoints
            ("Current Pools API", "https://api.raydium.io/pools"),
            ("Current Pairs API", "https://api.raydium.io/pairs"),
            
            # Alternative Raydium endpoints
            ("Raydium API v1", "https://api.raydium.io/v1/pools"),
            ("Raydium API v2", "https://api.raydium.io/v2/pools"),
            ("Raydium Analytics", "https://api.raydium.io/analytics"),
            ("Raydium Liquidity", "https://api.raydium.io/liquidity"),
            
            # Test new Raydium API structure
            ("Raydium V3 Pools", "https://api.raydium.io/v3/pools"),
            ("Raydium Main", "https://api-v3.raydium.io/pools"),
            ("Raydium Main V3", "https://api-v3.raydium.io/main/pools"),
            
            # Test base URL
            ("Raydium API Base", "https://api.raydium.io/"),
            ("Raydium V3 Base", "https://api-v3.raydium.io/"),
        ]
        
        results = {}
        for name, url in endpoints_to_test:
            results[name] = await self.test_endpoint(name, url)
            await asyncio.sleep(1)  # Be respectful with rate limiting
        
        return results
    
    async def test_alternative_sources(self) -> Dict[str, Any]:
        """Test alternative data sources that might have Orca/Raydium data"""
        print("\n" + "="*50)
        print("🔄 TESTING ALTERNATIVE DATA SOURCES")
        print("="*50)
        
        endpoints_to_test = [
            # Jupiter aggregator (has DEX data)
            ("Jupiter API Pools", "https://quote-api.jup.ag/v6/quote?inputMint=So11111111111111111111111111111111111111112&outputMint=EPjFWdd5AufqSSqeM2qN1xzybapC8G4wEGGkZwyTDt1v&amount=1000000"),
            
            # Solana ecosystem APIs
            ("Solana Beach API", "https://api.solanabeach.io/v1/latest-blocks"),
            ("SolScan API", "https://public-api.solscan.io/market/token/EPjFWdd5AufqSSqeM2qN1xzybapC8G4wEGGkZwyTDt1v"),
            
            # CoinGecko (might have DEX data)
            ("CoinGecko Solana DEXs", "https://api.coingecko.com/api/v3/exchanges?per_page=100"),
            
            # DexScreener (comprehensive DEX data)
            ("DexScreener Solana", "https://api.dexscreener.com/latest/dex/solana"),
            
            # Birdeye (has comprehensive DEX data)
            ("Birdeye Public API", "https://public-api.birdeye.so/public/tokenlist?sort_by=v24hUSD&sort_type=desc&offset=0&limit=50"),
        ]
        
        results = {}
        for name, url in endpoints_to_test:
            results[name] = await self.test_endpoint(name, url)
            await asyncio.sleep(1)
        
        return results
    
    async def run_comprehensive_test(self):
        """Run all API endpoint tests"""
        print("🚀 Starting Comprehensive API Endpoint Testing")
        print("="*60)
        
        # Test all endpoint categories
        orca_results = await self.test_orca_endpoints()
        raydium_results = await self.test_raydium_endpoints()
        alternative_results = await self.test_alternative_sources()
        
        # Compile summary
        all_results = {
            'orca': orca_results,
            'raydium': raydium_results,
            'alternatives': alternative_results
        }
        
        self.print_summary(all_results)
        return all_results
    
    def print_summary(self, results: Dict[str, Dict[str, Any]]):
        """Print a comprehensive summary of all test results"""
        print("\n" + "="*60)
        print("📊 COMPREHENSIVE TEST SUMMARY")
        print("="*60)
        
        for category, category_results in results.items():
            print(f"\n🏷️  {category.upper()} RESULTS:")
            print("-" * 40)
            
            working_endpoints = []
            failed_endpoints = []
            
            for endpoint_name, result in category_results.items():
                status = result.get('status', 'unknown')
                if status == 'success':
                    working_endpoints.append((endpoint_name, result))
                    print(f"✅ {endpoint_name}")
                    print(f"   └─ Status: {result.get('status_code')} | Time: {result.get('response_time', 0):.2f}s | Type: {result.get('content_type', 'unknown')}")
                else:
                    failed_endpoints.append((endpoint_name, result))
                    print(f"❌ {endpoint_name}")
                    error_info = result.get('error', f"Status {result.get('status_code', 'unknown')}")
                    print(f"   └─ Error: {error_info}")
            
            print(f"\n📈 {category.upper()} SUMMARY:")
            print(f"   Working: {len(working_endpoints)}/{len(category_results)}")
            print(f"   Failed: {len(failed_endpoints)}/{len(category_results)}")
            
            if working_endpoints:
                print(f"   🎯 RECOMMENDED ENDPOINTS:")
                for name, result in working_endpoints[:3]:  # Top 3 working
                    print(f"      • {name}")

async def main():
    """Main test execution"""
    async with APIEndpointTester() as tester:
        results = await tester.run_comprehensive_test()
        
        # Save results to file for further analysis
        with open('api_endpoint_test_results.json', 'w') as f:
            json.dump(results, f, indent=2, default=str)
        
        print(f"\n💾 Detailed results saved to: api_endpoint_test_results.json")
        
        return results

if __name__ == "__main__":
    asyncio.run(main()) 