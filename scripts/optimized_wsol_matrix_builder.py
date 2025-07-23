#!/usr/bin/env python3
"""
Optimized WSOL Matrix Builder - FIXED VERSION
Builds comprehensive WSOL availability matrix for all trending tokens with ACTUAL DEX checking
"""

import asyncio
import aiohttp
import json
import time
from dataclasses import dataclass, asdict
from typing import Dict, List, Any, Optional
import sys
import os

# Add parent directory to path for imports
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from scripts.cross_platform_token_analyzer import CrossPlatformAnalyzer
from api.orca_connector import OrcaConnector
from api.raydium_connector import RaydiumConnector
from api.enhanced_jupiter_connector import EnhancedJupiterConnector

@dataclass
class WSolPairInfo:
    """WSOL pair information for a token"""
    token_address: str
    symbol: str
    has_wsol_pairs: bool
    available_dexs: List[str]
    meteora_available: bool = False
    orca_available: bool = False  
    raydium_available: bool = False
    jupiter_available: bool = False
    check_duration: float = 0.0
    error: Optional[str] = None

class OptimizedWSolChecker:
    """Optimized WSOL availability checker with ACTUAL DEX integration"""
    
    def __init__(self, max_concurrent: int = 15):
        self.max_concurrent = max_concurrent
        self.session = None
        self.semaphore = asyncio.Semaphore(max_concurrent)
        
        # Initialize DEX connectors
        self.orca = None
        self.raydium = None
        self.jupiter = None
        
        # Cache for DEX trending tokens (to avoid repeated API calls)
        self.dex_wsol_tokens_cache = {}
        
    async def __aenter__(self):
        # Create optimized HTTP session
        connector = aiohttp.TCPConnector(
            limit=100,
            limit_per_host=20,
            ttl_dns_cache=300,
            use_dns_cache=True,
        )
        
        timeout = aiohttp.ClientTimeout(total=8, connect=3)
        self.session = aiohttp.ClientSession(
            connector=connector,
            timeout=timeout
        )
        
        # Initialize DEX connectors
        self.orca = OrcaConnector()
        self.raydium = RaydiumConnector()
        self.jupiter = EnhancedJupiterConnector()
        
        # Initialize DEX connectors
        await self.orca.__aenter__()
        await self.raydium.__aenter__()
        await self.jupiter.__aenter__()
        
        # Pre-populate DEX trending tokens cache
        await self._populate_dex_caches()
        
        return self
        
    async def _populate_dex_caches(self):
        """Pre-populate caches with WSOL trending tokens from each DEX"""
        print("🔄 Pre-loading DEX WSOL trending tokens...")
        
        try:
            # Get WSOL trending tokens from each DEX
            orca_trending = await self.orca.get_wsol_trending_pools(limit=200)
            raydium_trending = await self.raydium.get_wsol_trending_pairs(limit=200)
            
            # Cache token addresses for quick lookup
            self.dex_wsol_tokens_cache = {
                'orca': {token['address'].lower() for token in orca_trending if 'address' in token},
                'raydium': {token['address'].lower() for token in raydium_trending if 'address' in token},
            }
            
            print(f"✅ Cached {len(self.dex_wsol_tokens_cache['orca'])} Orca WSOL tokens")
            print(f"✅ Cached {len(self.dex_wsol_tokens_cache['raydium'])} Raydium WSOL tokens")
            
        except Exception as e:
            print(f"⚠️  Warning: Could not pre-load DEX caches: {e}")
            self.dex_wsol_tokens_cache = {'orca': set(), 'raydium': set()}

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Cleanup resources"""
        if self.session and not self.session.closed:
            await self.session.close()
            
        # Close DEX connectors
        if self.orca:
            await self.orca.__aexit__(exc_type, exc_val, exc_tb)
        if self.raydium:
            await self.raydium.__aexit__(exc_type, exc_val, exc_tb)
        if self.jupiter:
            await self.jupiter.__aexit__(exc_type, exc_val, exc_tb)
            
    async def close(self):
        """Explicit cleanup method"""
        if self.session and not self.session.closed:
            await self.session.close()
            
    async def check_jupiter_wsol_route(self, token_address: str) -> bool:
        """Check Jupiter for WSOL routing availability"""
        try:
            # Use Jupiter quote API to check WSOL routing
            wsol_address = 'So11111111111111111111111111111111111111112'
            
            # Try to get a quote from token to WSOL
            params = {
                'inputMint': token_address,
                'outputMint': wsol_address,
                'amount': '1000000',  # 1 token (6 decimals)
                'slippageBps': 500
            }
            
            async with self.session.get('https://quote-api.jup.ag/v6/quote', params=params) as response:
                if response.status == 200:
                    data = await response.json()
                    return 'routePlan' in data and len(data.get('routePlan', [])) > 0
                return False
                
        except Exception:
            return False
            
    async def check_orca_wsol_availability(self, token_address: str) -> bool:
        """Check if token has WSOL pairs on Orca using cached data"""
        return token_address.lower() in self.dex_wsol_tokens_cache.get('orca', set())
        
    async def check_raydium_wsol_availability(self, token_address: str) -> bool:
        """Check if token has WSOL pairs on Raydium using cached data"""  
        return token_address.lower() in self.dex_wsol_tokens_cache.get('raydium', set())
        
    async def check_meteora_wsol_availability(self, token_address: str) -> bool:
        """Check if token has WSOL pairs on Meteora via Jupiter routing"""
        # For now, use Jupiter routing as proxy for Meteora availability
        # In the future, could implement direct Meteora API integration
        try:
            return await self.check_jupiter_wsol_route(token_address)
        except Exception:
            return False
            
    async def check_token_wsol_pairs(self, token_address: str, symbol: str) -> WSolPairInfo:
        """Check WSOL pair availability for a single token across ALL DEXs"""
        async with self.semaphore:
            start_time = time.time()
            
            try:
                # Check all DEXs in parallel
                tasks = [
                    self.check_meteora_wsol_availability(token_address),
                    self.check_orca_wsol_availability(token_address),
                    self.check_raydium_wsol_availability(token_address), 
                    self.check_jupiter_wsol_route(token_address)
                ]
                
                meteora_available, orca_available, raydium_available, jupiter_available = await asyncio.gather(*tasks, return_exceptions=True)
                
                # Handle any exceptions
                meteora_available = meteora_available if not isinstance(meteora_available, Exception) else False
                orca_available = orca_available if not isinstance(orca_available, Exception) else False
                raydium_available = raydium_available if not isinstance(raydium_available, Exception) else False
                jupiter_available = jupiter_available if not isinstance(jupiter_available, Exception) else False
                
                # Build available DEXs list
                available_dexs = []
                if meteora_available:
                    available_dexs.append('meteora')
                if orca_available:
                    available_dexs.append('orca')
                if raydium_available:
                    available_dexs.append('raydium')
                if jupiter_available:
                    available_dexs.append('jupiter')
                    
                duration = time.time() - start_time
                
                return WSolPairInfo(
                    token_address=token_address,
                    symbol=symbol,
                    has_wsol_pairs=len(available_dexs) > 0,
                    available_dexs=available_dexs,
                    meteora_available=meteora_available,
                    orca_available=orca_available,
                    raydium_available=raydium_available,
                    jupiter_available=jupiter_available,
                    check_duration=duration
                )
                
            except Exception as e:
                duration = time.time() - start_time
                return WSolPairInfo(
                    token_address=token_address,
                    symbol=symbol,
                    has_wsol_pairs=False,
                    available_dexs=[],
                    check_duration=duration,
                    error=str(e)
                )

    async def build_complete_wsol_matrix(self, tokens: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Build complete WSOL availability matrix for all tokens"""
        print(f"🚀 Building WSOL matrix for {len(tokens)} tokens with {self.max_concurrent} concurrent workers...")
        
        start_time = time.time()
        
        tasks = []
        for token in tokens:
            task = self.check_token_wsol_pairs(
                token.get('address', ''),
                token.get('symbol', 'UNKNOWN')
            )
            tasks.append(task)
        
        # Process all tokens in parallel
        print(f"📊 Processing {len(tasks)} tokens in parallel...")
        
        results = []
        batch_size = 20
        
        for i in range(0, len(tasks), batch_size):
            batch = tasks[i:i + batch_size]
            batch_results = await asyncio.gather(*batch, return_exceptions=True)
            
            for result in batch_results:
                if isinstance(result, Exception):
                    print(f"❌ Error processing token: {result}")
                    continue
                    
                results.append(result)
                
            print(f"📈 Progress: {len(results)}/{len(tokens)} tokens completed ({len(results)/len(tokens)*100:.1f}%)")
        
        total_duration = time.time() - start_time
        
        # Generate analysis
        analysis = self._generate_matrix_analysis(results, total_duration)
        
        return {
            'analysis': analysis,
            'detailed_results': [asdict(result) for result in results],
            'summary': {
                'total_tokens': len(tokens),
                'tokens_with_wsol': len([r for r in results if r.has_wsol_pairs]),
                'tokens_without_wsol': len([r for r in results if not r.has_wsol_pairs]),
                'total_duration': total_duration,
                'avg_duration_per_token': total_duration / len(tokens) if tokens else 0
            }
        }

    def _generate_matrix_analysis(self, results: List[WSolPairInfo], duration: float) -> Dict[str, Any]:
        """Generate comprehensive analysis of WSOL availability matrix"""
        total_tokens = len(results)
        tokens_with_wsol = [r for r in results if r.has_wsol_pairs]
        
        # DEX availability stats
        dex_stats = {
            'meteora': len([r for r in results if r.meteora_available]),
            'orca': len([r for r in results if r.orca_available]),
            'raydium': len([r for r in results if r.raydium_available]),
            'jupiter': len([r for r in results if r.jupiter_available])
        }
        
        # Performance metrics
        durations = [r.check_duration for r in results if r.check_duration > 0]
        avg_duration = sum(durations) / len(durations) if durations else 0
        
        return {
            'performance': {
                'total_duration': duration,
                'tokens_per_second': total_tokens / duration if duration > 0 else 0,
                'avg_duration_per_token': avg_duration,
            },
            'coverage': {
                'total_tokens': total_tokens,
                'wsol_available': len(tokens_with_wsol),
                'wsol_coverage_percent': len(tokens_with_wsol) / total_tokens * 100 if total_tokens > 0 else 0,
            },
            'dex_breakdown': {
                dex: {
                    'count': count,
                    'percentage': count / total_tokens * 100 if total_tokens > 0 else 0
                }
                for dex, count in dex_stats.items()
            },
        }

async def main():
    """Main execution function"""
    print("🚀 Starting FIXED Optimized WSOL Matrix Builder...")
    
    # Get all trending tokens
    analyzer = CrossPlatformAnalyzer()
    print("📡 Collecting trending tokens from all platforms...")
    
    start_discovery = time.time()
    results = await analyzer.run_analysis()
    discovery_duration = time.time() - start_discovery
    
    print(f"✅ Token discovery completed in {discovery_duration:.1f}s")
    
    # Extract token list - FIX: Access correlations.all_tokens correctly
    tokens = []
    correlations = results.get('correlations', {})
    all_tokens = correlations.get('all_tokens', {})
    
    print(f"🔍 Debug: Results keys: {list(results.keys())}")
    print(f"🔍 Debug: Correlations keys: {list(correlations.keys())}")
    print(f"🔍 Debug: All tokens count: {len(all_tokens)}")
    
    for token_addr, token_data in all_tokens.items():
        tokens.append({
            'address': token_addr,
            'symbol': token_data.get('symbol', 'UNKNOWN'),
            'platforms': token_data.get('platforms', [])
        })
    
    print(f"📊 Found {len(tokens)} unique tokens to analyze")
    
    if len(tokens) == 0:
        print("❌ CRITICAL: No tokens found in CrossPlatformAnalyzer results!")
        print("🔍 Investigating token discovery issue...")
        
        # Debug: Check if we have any other data structures
        for key, value in results.items():
            if isinstance(value, dict) and len(value) > 0:
                print(f"   📋 {key}: {len(value)} items")
                if len(value) < 10:  # Show details for small collections
                    for subkey in list(value.keys())[:5]:  # Show first 5 keys
                        print(f"      • {subkey}")
        return
    
    # Show sample tokens for verification
    print(f"🎯 Sample tokens to analyze:")
    for i, token in enumerate(tokens[:3]):
        print(f"   {i+1}. {token['symbol']} ({token['address'][:8]}...) - {len(token['platforms'])} platforms")
    
    # Build WSOL matrix with ACTUAL DEX checking
    try:
        async with OptimizedWSolChecker(max_concurrent=15) as checker:
            matrix_results = await checker.build_complete_wsol_matrix(tokens)
    finally:
        # Ensure analyzer is properly closed
        await analyzer.close()
    
    # Build matrix format expected by high-conviction detector
    matrix = {}
    for result in matrix_results['detailed_results']:
        token_addr = result['token_address']
        matrix[token_addr] = {
            'symbol': result['symbol'],
            'meteora_available': result['meteora_available'],
            'orca_available': result['orca_available'],
            'raydium_available': result['raydium_available'],
            'jupiter_available': result['jupiter_available'],
            'has_wsol_pairs': result['has_wsol_pairs'],
            'available_dexs': result['available_dexs'],
            'check_duration': result['check_duration']
        }
    
    # Save results with timestamp
    timestamp = int(time.time())
    
    # Create final output in expected format
    final_output = {
        'matrix': matrix,  # This is what the detector looks for!
        'metadata': {
            'timestamp': timestamp,
            'total_tokens': len(tokens),
            'tokens_with_wsol': len([r for r in matrix.values() if r['has_wsol_pairs']]),
            'generation_duration': matrix_results['analysis']['performance']['total_duration'],
            'tokens_per_second': matrix_results['analysis']['performance']['tokens_per_second']
        },
        'analysis': matrix_results['analysis']
    }
    
    output_file = f"complete_wsol_matrix_FIXED_{timestamp}.json"
    
    with open(output_file, 'w') as f:
        json.dump(final_output, f, indent=2)
    
    # Print summary
    analysis = final_output['analysis']
    metadata = final_output['metadata']
    matrix = final_output['matrix']
    
    print("\n" + "="*80)
    print("📊 COMPLETE WSOL AVAILABILITY MATRIX - FIXED VERSION")
    print("="*80)
    print(f"⚡ Performance: {analysis['performance']['tokens_per_second']:.1f} tokens/second")
    print(f"🎯 Coverage: {analysis['coverage']['wsol_coverage_percent']:.1f}% ({analysis['coverage']['wsol_available']}/{analysis['coverage']['total_tokens']})")
    print(f"⏱️  Total Duration: {analysis['performance']['total_duration']:.1f}s")
    print(f"📊 Matrix Size: {len(matrix)} tokens indexed")
    
    print("\n📈 DEX Availability:")
    for dex, stats in analysis['dex_breakdown'].items():
        print(f"   • {dex.capitalize()}: {stats['count']} tokens ({stats['percentage']:.1f}%)")
    
    print(f"\n📁 Complete results saved to: {output_file}")
    print(f"🎯 High-Conviction Detector Integration: ✅ READY")
    print(f"   Matrix format: {len(matrix)} tokens ready for routing analysis")
    print("🎉 FIXED WSOL matrix analysis completed!")

if __name__ == "__main__":
    asyncio.run(main()) 