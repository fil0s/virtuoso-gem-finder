#!/usr/bin/env python3
"""
Deep Investigation: Unknown Symbols Issue

This script investigates why tokens are showing "Unknown" symbols by:
1. Testing each API endpoint individually
2. Examining actual API response structures
3. Tracing symbol extraction logic
4. Identifying where symbols are lost in the pipeline
"""

import asyncio
import json
import logging
import time
from typing import Dict, List, Any, Optional
import aiohttp
import sys
import os

# Add the project root to the path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from scripts.cross_platform_token_analyzer import CrossPlatformAnalyzer
from api.birdeye_connector import BirdeyeAPI
from utils.env_loader import load_environment_variables

class SymbolInvestigator:
    """Investigate Unknown symbols issue across all platforms"""
    
    def __init__(self):
        self.logger = logging.getLogger('SymbolInvestigator')
        self.logger.setLevel(logging.DEBUG)
        
        # Create console handler
        handler = logging.StreamHandler()
        handler.setLevel(logging.DEBUG)
        formatter = logging.Formatter('%(asctime)s [%(levelname)s] %(name)s - %(message)s')
        handler.setFormatter(formatter)
        self.logger.addHandler(handler)
        
        # Load environment
        load_environment_variables()
        
        # Initialize APIs
        self.birdeye_api = None
        self.session = None
        
    async def initialize(self):
        """Initialize async components"""
        self.session = aiohttp.ClientSession()
        
        # Initialize Birdeye API
        try:
            self.birdeye_api = BirdeyeAPI()
            self.logger.info("✅ Birdeye API initialized")
        except Exception as e:
            self.logger.error(f"❌ Failed to initialize Birdeye API: {e}")
    
    async def test_dexscreener_endpoints(self) -> Dict[str, Any]:
        """Test DexScreener endpoints for symbol data"""
        self.logger.info("🔍 Testing DexScreener endpoints...")
        
        results = {
            'boosted_tokens': [],
            'top_boosted': [],
            'profiles': [],
            'symbol_analysis': {}
        }
        
        # Test boosted tokens endpoint
        try:
            url = "https://api.dexscreener.com/token-boosts/top/v1"
            async with self.session.get(url) as response:
                if response.status == 200:
                    data = await response.json()
                    results['boosted_tokens'] = data
                    self.logger.info(f"✅ DexScreener boosted tokens: {len(data)} tokens")
                    
                    # Analyze symbol availability
                    symbol_count = 0
                    for token in data[:5]:  # Check first 5
                        self.logger.info(f"📊 Boosted Token Sample:")
                        self.logger.info(f"   Address: {token.get('tokenAddress', 'N/A')}")
                        self.logger.info(f"   Symbol: {token.get('symbol', 'NOT_FOUND')}")
                        self.logger.info(f"   Description: {token.get('description', 'N/A')[:50]}...")
                        self.logger.info(f"   Available fields: {list(token.keys())}")
                        
                        if 'symbol' in token and token['symbol']:
                            symbol_count += 1
                    
                    results['symbol_analysis']['boosted_symbols_available'] = symbol_count
                    results['symbol_analysis']['boosted_total_checked'] = min(5, len(data))
                    
        except Exception as e:
            self.logger.error(f"❌ DexScreener boosted tokens error: {e}")
        
        # Test top boosted endpoint
        try:
            url = "https://api.dexscreener.com/token-boosts/top/v1"
            async with self.session.get(url, params={'sort': 'amount', 'order': 'desc'}) as response:
                if response.status == 200:
                    data = await response.json()
                    results['top_boosted'] = data
                    self.logger.info(f"✅ DexScreener top boosted: {len(data)} tokens")
        except Exception as e:
            self.logger.error(f"❌ DexScreener top boosted error: {e}")
            
        # Test profiles endpoint
        try:
            url = "https://api.dexscreener.com/token-profiles/latest/v1"
            async with self.session.get(url) as response:
                if response.status == 200:
                    data = await response.json()
                    results['profiles'] = data
                    self.logger.info(f"✅ DexScreener profiles: {len(data)} tokens")
                    
                    # Check profile symbol data
                    for profile in data[:3]:
                        self.logger.info(f"📊 Profile Sample:")
                        self.logger.info(f"   Address: {profile.get('address', 'N/A')}")
                        self.logger.info(f"   Symbol: {profile.get('symbol', 'NOT_FOUND')}")
                        self.logger.info(f"   Available fields: {list(profile.keys())}")
                        
        except Exception as e:
            self.logger.error(f"❌ DexScreener profiles error: {e}")
        
        return results
    
    async def test_rugcheck_endpoints(self) -> Dict[str, Any]:
        """Test RugCheck endpoints for symbol data"""
        self.logger.info("🔍 Testing RugCheck endpoints...")
        
        results = {
            'trending_tokens': [],
            'symbol_analysis': {}
        }
        
        try:
            url = "https://api.rugcheck.xyz/v1/tokens/trending"
            async with self.session.get(url) as response:
                if response.status == 200:
                    data = await response.json()
                    results['trending_tokens'] = data
                    self.logger.info(f"✅ RugCheck trending: {len(data)} tokens")
                    
                    # Analyze symbol availability
                    symbol_count = 0
                    for token in data[:5]:
                        self.logger.info(f"📊 RugCheck Token Sample:")
                        self.logger.info(f"   Mint: {token.get('mint', 'N/A')}")
                        self.logger.info(f"   Symbol: {token.get('symbol', 'NOT_FOUND')}")
                        self.logger.info(f"   Name: {token.get('name', 'NOT_FOUND')}")
                        self.logger.info(f"   Available fields: {list(token.keys())}")
                        
                        if 'symbol' in token and token['symbol']:
                            symbol_count += 1
                    
                    results['symbol_analysis']['rugcheck_symbols_available'] = symbol_count
                    results['symbol_analysis']['rugcheck_total_checked'] = min(5, len(data))
                    
        except Exception as e:
            self.logger.error(f"❌ RugCheck trending error: {e}")
        
        return results
    
    async def test_birdeye_endpoints(self) -> Dict[str, Any]:
        """Test Birdeye endpoints for symbol data"""
        self.logger.info("🔍 Testing Birdeye endpoints...")
        
        results = {
            'trending_tokens': [],
            'emerging_stars': [],
            'symbol_analysis': {}
        }
        
        if not self.birdeye_api:
            self.logger.error("❌ Birdeye API not initialized")
            return results
        
        # Test trending tokens
        try:
            trending_data = await self.birdeye_api.get_trending_tokens(limit=10)
            if trending_data and 'tokens' in trending_data:
                tokens = trending_data['tokens']
                results['trending_tokens'] = tokens
                self.logger.info(f"✅ Birdeye trending: {len(tokens)} tokens")
                
                # Analyze symbol availability
                symbol_count = 0
                for token in tokens[:5]:
                    self.logger.info(f"📊 Birdeye Trending Token Sample:")
                    self.logger.info(f"   Address: {token.get('address', 'N/A')}")
                    self.logger.info(f"   Symbol: {token.get('symbol', 'NOT_FOUND')}")
                    self.logger.info(f"   Name: {token.get('name', 'NOT_FOUND')}")
                    self.logger.info(f"   Available fields: {list(token.keys())}")
                    
                    if 'symbol' in token and token['symbol']:
                        symbol_count += 1
                
                results['symbol_analysis']['birdeye_trending_symbols_available'] = symbol_count
                results['symbol_analysis']['birdeye_trending_total_checked'] = min(5, len(tokens))
                
        except Exception as e:
            self.logger.error(f"❌ Birdeye trending error: {e}")
        
        # Test emerging stars
        try:
            emerging_data = await self.birdeye_api.get_emerging_stars(limit=10)
            if emerging_data and 'tokens' in emerging_data:
                tokens = emerging_data['tokens']
                results['emerging_stars'] = tokens
                self.logger.info(f"✅ Birdeye emerging stars: {len(tokens)} tokens")
                
                # Analyze symbol availability
                symbol_count = 0
                for token in tokens[:5]:
                    self.logger.info(f"📊 Birdeye Emerging Star Sample:")
                    self.logger.info(f"   Address: {token.get('address', 'N/A')}")
                    self.logger.info(f"   Symbol: {token.get('symbol', 'NOT_FOUND')}")
                    self.logger.info(f"   Name: {token.get('name', 'NOT_FOUND')}")
                    self.logger.info(f"   Available fields: {list(token.keys())}")
                    
                    if 'symbol' in token and token['symbol']:
                        symbol_count += 1
                
                results['symbol_analysis']['birdeye_emerging_symbols_available'] = symbol_count
                results['symbol_analysis']['birdeye_emerging_total_checked'] = min(5, len(tokens))
                
        except Exception as e:
            self.logger.error(f"❌ Birdeye emerging stars error: {e}")
        
        return results
    
    async def test_cross_platform_analyzer(self) -> Dict[str, Any]:
        """Test the cross-platform analyzer symbol extraction"""
        self.logger.info("🔍 Testing Cross-Platform Analyzer...")
        
        analyzer = CrossPlatformAnalyzer()
        
        try:
            # Run full analysis
            analysis_result = await analyzer.run_analysis()
            
            # Extract symbol analysis
            correlations = analysis_result.get('correlations', {})
            multi_platform_tokens = correlations.get('multi_platform_tokens', [])
            
            self.logger.info(f"✅ Cross-platform analysis completed")
            self.logger.info(f"📊 Multi-platform tokens found: {len(multi_platform_tokens)}")
            
            # Analyze symbols in multi-platform tokens
            symbol_stats = {
                'total_tokens': len(multi_platform_tokens),
                'tokens_with_symbols': 0,
                'tokens_with_unknown': 0,
                'tokens_with_truncated_addresses': 0,
                'symbol_examples': []
            }
            
            for token in multi_platform_tokens[:10]:  # Check first 10
                symbol = token.get('symbol', '')
                address = token.get('address', '')
                
                self.logger.info(f"📊 Multi-Platform Token:")
                self.logger.info(f"   Address: {address}")
                self.logger.info(f"   Symbol: {symbol}")
                self.logger.info(f"   Name: {token.get('name', 'N/A')}")
                self.logger.info(f"   Platforms: {token.get('platforms', [])}")
                self.logger.info(f"   Score: {token.get('score', 0)}")
                
                if symbol == 'Unknown':
                    symbol_stats['tokens_with_unknown'] += 1
                elif len(symbol) > 10 and ('...' in symbol or len(symbol) == len(address[:8]) + 4):
                    symbol_stats['tokens_with_truncated_addresses'] += 1
                elif symbol and symbol != 'Unknown':
                    symbol_stats['tokens_with_symbols'] += 1
                
                symbol_stats['symbol_examples'].append({
                    'address': address[:12] + '...',
                    'symbol': symbol,
                    'platforms': token.get('platforms', [])
                })
            
            await analyzer.close()
            
            return {
                'analysis_result': analysis_result,
                'symbol_stats': symbol_stats
            }
            
        except Exception as e:
            self.logger.error(f"❌ Cross-platform analyzer error: {e}")
            await analyzer.close()
            return {}
    
    async def investigate_specific_tokens(self, token_addresses: List[str]) -> Dict[str, Any]:
        """Investigate specific tokens across all platforms"""
        self.logger.info(f"🔍 Investigating specific tokens: {len(token_addresses)} addresses")
        
        results = {}
        
        for address in token_addresses[:3]:  # Test first 3
            self.logger.info(f"🔍 Investigating token: {address}")
            token_results = {
                'address': address,
                'dexscreener_data': None,
                'rugcheck_data': None,
                'birdeye_data': None,
                'symbol_sources': []
            }
            
            # Test DexScreener search
            try:
                url = f"https://api.dexscreener.com/latest/dex/tokens/{address}"
                async with self.session.get(url) as response:
                    if response.status == 200:
                        data = await response.json()
                        token_results['dexscreener_data'] = data
                        
                        # Extract symbol info
                        pairs = data.get('pairs', [])
                        if pairs:
                            pair = pairs[0]
                            base_token = pair.get('baseToken', {})
                            symbol = base_token.get('symbol', '')
                            if symbol:
                                token_results['symbol_sources'].append(f"DexScreener: {symbol}")
                                self.logger.info(f"   DexScreener symbol: {symbol}")
                        
            except Exception as e:
                self.logger.error(f"   DexScreener error for {address}: {e}")
            
            # Test RugCheck individual token
            try:
                url = f"https://api.rugcheck.xyz/v1/tokens/{address}/report"
                async with self.session.get(url) as response:
                    if response.status == 200:
                        data = await response.json()
                        token_results['rugcheck_data'] = data
                        
                        # Extract symbol info
                        token_meta = data.get('tokenMeta', {})
                        symbol = token_meta.get('symbol', '')
                        if symbol:
                            token_results['symbol_sources'].append(f"RugCheck: {symbol}")
                            self.logger.info(f"   RugCheck symbol: {symbol}")
                        
            except Exception as e:
                self.logger.error(f"   RugCheck error for {address}: {e}")
            
            # Test Birdeye token overview
            if self.birdeye_api:
                try:
                    overview_data = await self.birdeye_api.get_token_overview(address)
                    if overview_data:
                        token_results['birdeye_data'] = overview_data
                        
                        # Extract symbol info
                        symbol = overview_data.get('symbol', '')
                        if symbol:
                            token_results['symbol_sources'].append(f"Birdeye: {symbol}")
                            self.logger.info(f"   Birdeye symbol: {symbol}")
                            
                except Exception as e:
                    self.logger.error(f"   Birdeye error for {address}: {e}")
            
            results[address] = token_results
            
            # Summary for this token
            self.logger.info(f"   Symbol sources found: {len(token_results['symbol_sources'])}")
            for source in token_results['symbol_sources']:
                self.logger.info(f"     - {source}")
        
        return results
    
    async def run_investigation(self):
        """Run the complete investigation"""
        self.logger.info("🚀 Starting Unknown Symbols Investigation")
        
        investigation_results = {
            'timestamp': time.time(),
            'dexscreener_results': {},
            'rugcheck_results': {},
            'birdeye_results': {},
            'cross_platform_results': {},
            'specific_token_results': {},
            'summary': {}
        }
        
        await self.initialize()
        
        try:
            # Test individual API endpoints
            investigation_results['dexscreener_results'] = await self.test_dexscreener_endpoints()
            investigation_results['rugcheck_results'] = await self.test_rugcheck_endpoints()
            investigation_results['birdeye_results'] = await self.test_birdeye_endpoints()
            
            # Test cross-platform analyzer
            investigation_results['cross_platform_results'] = await self.test_cross_platform_analyzer()
            
            # Get some token addresses from cross-platform results for specific testing
            cross_platform_data = investigation_results['cross_platform_results']
            if 'analysis_result' in cross_platform_data:
                correlations = cross_platform_data['analysis_result'].get('correlations', {})
                multi_platform_tokens = correlations.get('multi_platform_tokens', [])
                
                # Get addresses of tokens with "Unknown" symbols
                unknown_addresses = []
                for token in multi_platform_tokens:
                    if token.get('symbol') == 'Unknown' or '...' in token.get('symbol', ''):
                        unknown_addresses.append(token.get('address'))
                
                if unknown_addresses:
                    investigation_results['specific_token_results'] = await self.investigate_specific_tokens(unknown_addresses)
            
            # Generate summary
            summary = self.generate_summary(investigation_results)
            investigation_results['summary'] = summary
            
            # Save results
            timestamp = int(time.time())
            filename = f"scripts/results/unknown_symbols_investigation_{timestamp}.json"
            os.makedirs(os.path.dirname(filename), exist_ok=True)
            
            with open(filename, 'w') as f:
                json.dump(investigation_results, f, indent=2, default=str)
            
            self.logger.info(f"📄 Investigation results saved to: {filename}")
            
            # Print summary
            self.print_summary(summary)
            
        except Exception as e:
            self.logger.error(f"❌ Investigation failed: {e}")
            raise
        finally:
            await self.cleanup()
    
    def generate_summary(self, results: Dict[str, Any]) -> Dict[str, Any]:
        """Generate investigation summary"""
        summary = {
            'api_symbol_availability': {},
            'cross_platform_symbol_stats': {},
            'root_causes': [],
            'recommendations': []
        }
        
        # Analyze API symbol availability
        dx_results = results.get('dexscreener_results', {})
        dx_analysis = dx_results.get('symbol_analysis', {})
        
        rc_results = results.get('rugcheck_results', {})
        rc_analysis = rc_results.get('symbol_analysis', {})
        
        be_results = results.get('birdeye_results', {})
        be_analysis = be_results.get('symbol_analysis', {})
        
        summary['api_symbol_availability'] = {
            'dexscreener_boosted': f"{dx_analysis.get('boosted_symbols_available', 0)}/{dx_analysis.get('boosted_total_checked', 0)}",
            'rugcheck_trending': f"{rc_analysis.get('rugcheck_symbols_available', 0)}/{rc_analysis.get('rugcheck_total_checked', 0)}",
            'birdeye_trending': f"{be_analysis.get('birdeye_trending_symbols_available', 0)}/{be_analysis.get('birdeye_trending_total_checked', 0)}",
            'birdeye_emerging': f"{be_analysis.get('birdeye_emerging_symbols_available', 0)}/{be_analysis.get('birdeye_emerging_total_checked', 0)}"
        }
        
        # Analyze cross-platform stats
        cp_results = results.get('cross_platform_results', {})
        if 'symbol_stats' in cp_results:
            stats = cp_results['symbol_stats']
            summary['cross_platform_symbol_stats'] = {
                'total_tokens': stats.get('total_tokens', 0),
                'with_symbols': stats.get('tokens_with_symbols', 0),
                'with_unknown': stats.get('tokens_with_unknown', 0),
                'with_truncated': stats.get('tokens_with_truncated_addresses', 0)
            }
        
        # Identify root causes
        if dx_analysis.get('boosted_symbols_available', 0) == 0:
            summary['root_causes'].append("DexScreener boosted tokens endpoint does not provide symbol field")
        
        if rc_analysis.get('rugcheck_symbols_available', 0) == 0:
            summary['root_causes'].append("RugCheck trending endpoint does not provide symbol field")
        
        if be_analysis.get('birdeye_trending_symbols_available', 0) < be_analysis.get('birdeye_trending_total_checked', 1):
            summary['root_causes'].append("Birdeye trending has incomplete symbol data")
        
        # Generate recommendations
        summary['recommendations'] = [
            "Implement fallback symbol lookup using individual token APIs",
            "Add symbol caching to reduce repeated API calls",
            "Use DexScreener pairs endpoint for symbol resolution",
            "Implement symbol extraction from token metadata",
            "Add Moralis or other metadata providers as backup"
        ]
        
        return summary
    
    def print_summary(self, summary: Dict[str, Any]):
        """Print investigation summary"""
        self.logger.info("=" * 80)
        self.logger.info("🔍 UNKNOWN SYMBOLS INVESTIGATION SUMMARY")
        self.logger.info("=" * 80)
        
        self.logger.info("📊 API Symbol Availability:")
        for api, availability in summary['api_symbol_availability'].items():
            self.logger.info(f"   {api}: {availability} tokens have symbols")
        
        self.logger.info("📊 Cross-Platform Symbol Statistics:")
        stats = summary['cross_platform_symbol_stats']
        if stats:
            self.logger.info(f"   Total tokens: {stats['total_tokens']}")
            self.logger.info(f"   With symbols: {stats['with_symbols']}")
            self.logger.info(f"   With 'Unknown': {stats['with_unknown']}")
            self.logger.info(f"   With truncated addresses: {stats['with_truncated']}")
        
        self.logger.info("🔍 Root Causes Identified:")
        for cause in summary['root_causes']:
            self.logger.info(f"   - {cause}")
        
        self.logger.info("💡 Recommendations:")
        for rec in summary['recommendations']:
            self.logger.info(f"   - {rec}")
        
        self.logger.info("=" * 80)
    
    async def cleanup(self):
        """Cleanup resources"""
        if self.session:
            await self.session.close()
        if self.birdeye_api:
            await self.birdeye_api.close()

async def main():
    """Main function"""
    investigator = SymbolInvestigator()
    await investigator.run_investigation()

if __name__ == "__main__":
    asyncio.run(main()) 