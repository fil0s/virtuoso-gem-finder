#!/usr/bin/env python3
"""
Comprehensive Fix for Unknown Symbols Issue

Root Cause Analysis:
1. DexScreener boosted tokens endpoint does NOT provide symbol field
2. RugCheck trending endpoint returns 404 (endpoint changed)
3. Symbol extraction logic lacks fallback mechanisms

Solution:
1. Implement symbol resolution service with multiple fallbacks
2. Add individual token API lookups for missing symbols
3. Update cross-platform analyzer to use symbol resolution
4. Add symbol caching to reduce API calls
"""

import asyncio
import aiohttp
import logging
import time
from typing import Dict, List, Any, Optional
import sys
import os

# Add project root to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

class SymbolResolver:
    """Resolve token symbols using multiple API sources"""
    
    def __init__(self, birdeye_api_key: Optional[str] = None):
        self.logger = logging.getLogger('SymbolResolver')
        self.birdeye_api_key = birdeye_api_key
        self.session = None
        self.symbol_cache = {}  # Address -> symbol mapping
        
    async def initialize(self):
        """Initialize async session"""
        self.session = aiohttp.ClientSession()
        
    async def close(self):
        """Close async session"""
        if self.session:
            await self.session.close()
    
    async def resolve_symbol(self, token_address: str) -> Dict[str, str]:
        """
        Resolve symbol and name for a token address using multiple sources
        
        Returns:
            Dict with 'symbol' and 'name' keys
        """
        # Check cache first
        if token_address in self.symbol_cache:
            return self.symbol_cache[token_address]
        
        result = {'symbol': 'Unknown', 'name': ''}
        
        # Try DexScreener pairs endpoint first (most reliable)
        dex_result = await self._resolve_from_dexscreener(token_address)
        if dex_result['symbol'] != 'Unknown':
            result = dex_result
        
        # Try Birdeye if DexScreener failed
        if result['symbol'] == 'Unknown' and self.birdeye_api_key:
            birdeye_result = await self._resolve_from_birdeye(token_address)
            if birdeye_result['symbol'] != 'Unknown':
                result = birdeye_result
        
        # Try RugCheck individual token
        if result['symbol'] == 'Unknown':
            rugcheck_result = await self._resolve_from_rugcheck(token_address)
            if rugcheck_result['symbol'] != 'Unknown':
                result = rugcheck_result
        
        # Cache the result
        self.symbol_cache[token_address] = result
        
        return result
    
    async def _resolve_from_dexscreener(self, token_address: str) -> Dict[str, str]:
        """Resolve symbol from DexScreener pairs endpoint"""
        try:
            url = f"https://api.dexscreener.com/latest/dex/tokens/{token_address}"
            async with self.session.get(url) as response:
                if response.status == 200:
                    data = await response.json()
                    pairs = data.get('pairs', [])
                    
                    if pairs:
                        # Use the first pair
                        pair = pairs[0]
                        base_token = pair.get('baseToken', {})
                        
                        symbol = base_token.get('symbol', '').strip()
                        name = base_token.get('name', '').strip()
                        
                        if symbol:
                            self.logger.debug(f"✅ DexScreener resolved {token_address[:8]}... -> {symbol}")
                            return {'symbol': symbol, 'name': name}
                        
        except Exception as e:
            self.logger.debug(f"❌ DexScreener resolution failed for {token_address[:8]}...: {e}")
        
        return {'symbol': 'Unknown', 'name': ''}
    
    async def _resolve_from_birdeye(self, token_address: str) -> Dict[str, str]:
        """Resolve symbol from Birdeye token overview"""
        try:
            url = f"https://public-api.birdeye.so/defi/token_overview"
            headers = {'X-API-KEY': self.birdeye_api_key}
            params = {'address': token_address}
            
            async with self.session.get(url, headers=headers, params=params) as response:
                if response.status == 200:
                    data = await response.json()
                    
                    symbol = data.get('symbol', '').strip()
                    name = data.get('name', '').strip()
                    
                    if symbol:
                        self.logger.debug(f"✅ Birdeye resolved {token_address[:8]}... -> {symbol}")
                        return {'symbol': symbol, 'name': name}
                        
        except Exception as e:
            self.logger.debug(f"❌ Birdeye resolution failed for {token_address[:8]}...: {e}")
        
        return {'symbol': 'Unknown', 'name': ''}
    
    async def _resolve_from_rugcheck(self, token_address: str) -> Dict[str, str]:
        """Resolve symbol from RugCheck individual token report"""
        try:
            url = f"https://api.rugcheck.xyz/v1/tokens/{token_address}/report"
            
            async with self.session.get(url) as response:
                if response.status == 200:
                    data = await response.json()
                    
                    token_meta = data.get('tokenMeta', {})
                    symbol = token_meta.get('symbol', '').strip()
                    name = token_meta.get('name', '').strip()
                    
                    if symbol:
                        self.logger.debug(f"✅ RugCheck resolved {token_address[:8]}... -> {symbol}")
                        return {'symbol': symbol, 'name': name}
                        
        except Exception as e:
            self.logger.debug(f"❌ RugCheck resolution failed for {token_address[:8]}...: {e}")
        
        return {'symbol': 'Unknown', 'name': ''}
    
    async def resolve_batch_symbols(self, token_addresses: List[str], max_concurrent: int = 5) -> Dict[str, Dict[str, str]]:
        """
        Resolve symbols for multiple tokens with concurrency control
        
        Args:
            token_addresses: List of token addresses
            max_concurrent: Maximum concurrent API calls
            
        Returns:
            Dict mapping token addresses to symbol/name data
        """
        results = {}
        
        # Process in batches to avoid overwhelming APIs
        semaphore = asyncio.Semaphore(max_concurrent)
        
        async def resolve_with_semaphore(address):
            async with semaphore:
                return address, await self.resolve_symbol(address)
        
        # Execute all resolutions
        tasks = [resolve_with_semaphore(addr) for addr in token_addresses]
        completed_tasks = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Process results
        for result in completed_tasks:
            if isinstance(result, tuple):
                address, symbol_data = result
                results[address] = symbol_data
            else:
                self.logger.error(f"Symbol resolution task failed: {result}")
        
        return results

def create_symbol_resolver_patch():
    """Create the patch for cross_platform_token_analyzer.py"""
    
    patch_content = '''
# Add SymbolResolver import at the top of the file
import asyncio
import aiohttp
from typing import Dict, List, Any, Optional

class SymbolResolver:
    """Resolve token symbols using multiple API sources"""
    
    def __init__(self, birdeye_api_key: Optional[str] = None):
        self.logger = logging.getLogger('SymbolResolver')
        self.birdeye_api_key = birdeye_api_key
        self.session = None
        self.symbol_cache = {}
        
    async def initialize(self):
        """Initialize async session"""
        if not self.session:
            self.session = aiohttp.ClientSession()
        
    async def close(self):
        """Close async session"""
        if self.session:
            await self.session.close()
            self.session = None
    
    async def resolve_symbol(self, token_address: str) -> Dict[str, str]:
        """Resolve symbol and name for a token address"""
        if token_address in self.symbol_cache:
            return self.symbol_cache[token_address]
        
        result = {'symbol': 'Unknown', 'name': ''}
        
        # Try DexScreener pairs endpoint first
        try:
            url = f"https://api.dexscreener.com/latest/dex/tokens/{token_address}"
            async with self.session.get(url) as response:
                if response.status == 200:
                    data = await response.json()
                    pairs = data.get('pairs', [])
                    
                    if pairs:
                        base_token = pairs[0].get('baseToken', {})
                        symbol = base_token.get('symbol', '').strip()
                        name = base_token.get('name', '').strip()
                        
                        if symbol:
                            result = {'symbol': symbol, 'name': name}
                            self.logger.debug(f"✅ Resolved {token_address[:8]}... -> {symbol}")
        except Exception as e:
            self.logger.debug(f"❌ Symbol resolution failed for {token_address[:8]}...: {e}")
        
        # Try Birdeye if DexScreener failed
        if result['symbol'] == 'Unknown' and self.birdeye_api_key:
            try:
                url = f"https://public-api.birdeye.so/defi/token_overview"
                headers = {'X-API-KEY': self.birdeye_api_key}
                params = {'address': token_address}
                
                async with self.session.get(url, headers=headers, params=params) as response:
                    if response.status == 200:
                        data = await response.json()
                        symbol = data.get('symbol', '').strip()
                        name = data.get('name', '').strip()
                        
                        if symbol:
                            result = {'symbol': symbol, 'name': name}
                            self.logger.debug(f"✅ Birdeye resolved {token_address[:8]}... -> {symbol}")
            except Exception as e:
                self.logger.debug(f"❌ Birdeye resolution failed: {e}")
        
        self.symbol_cache[token_address] = result
        return result
    
    async def resolve_batch_symbols(self, token_addresses: List[str]) -> Dict[str, Dict[str, str]]:
        """Resolve symbols for multiple tokens"""
        results = {}
        
        # Process in small batches to avoid rate limits
        batch_size = 3
        for i in range(0, len(token_addresses), batch_size):
            batch = token_addresses[i:i + batch_size]
            
            tasks = [self.resolve_symbol(addr) for addr in batch]
            batch_results = await asyncio.gather(*tasks, return_exceptions=True)
            
            for addr, result in zip(batch, batch_results):
                if isinstance(result, dict):
                    results[addr] = result
                else:
                    results[addr] = {'symbol': 'Unknown', 'name': ''}
            
            # Small delay between batches
            if i + batch_size < len(token_addresses):
                await asyncio.sleep(0.5)
        
        return results

# Modify the CrossPlatformAnalyzer class
'''
    
    return patch_content

async def apply_comprehensive_fix():
    """Apply comprehensive fix to the cross-platform analyzer"""
    
    print("🔧 Applying Comprehensive Unknown Symbols Fix...")
    
    # Read the current cross_platform_token_analyzer.py
    analyzer_file = "scripts/cross_platform_token_analyzer.py"
    
    with open(analyzer_file, 'r') as f:
        content = f.read()
    
    # Check if SymbolResolver is already added
    if "class SymbolResolver:" in content:
        print("✅ SymbolResolver already exists in the file")
        return
    
    # Find the CrossPlatformAnalyzer class initialization
    init_pattern = "def __init__(self, config: Optional[Dict] = None, logger: Optional[logging.Logger] = None):"
    
    if init_pattern in content:
        # Add SymbolResolver to imports
        import_section = """import asyncio
import aiohttp
from typing import Dict, List, Any, Optional
import logging
import time
from collections import defaultdict
from datetime import datetime, timedelta
"""
        
        # Insert SymbolResolver class before CrossPlatformAnalyzer
        symbol_resolver_class = '''
class SymbolResolver:
    """Resolve token symbols using multiple API sources"""
    
    def __init__(self, birdeye_api_key: Optional[str] = None):
        self.logger = logging.getLogger('SymbolResolver')
        self.birdeye_api_key = birdeye_api_key
        self.session = None
        self.symbol_cache = {}
        
    async def initialize(self):
        """Initialize async session"""
        if not self.session:
            self.session = aiohttp.ClientSession()
        
    async def close(self):
        """Close async session"""
        if self.session:
            await self.session.close()
            self.session = None
    
    async def resolve_symbol(self, token_address: str) -> Dict[str, str]:
        """Resolve symbol and name for a token address"""
        if token_address in self.symbol_cache:
            return self.symbol_cache[token_address]
        
        result = {'symbol': 'Unknown', 'name': ''}
        
        # Try DexScreener pairs endpoint first
        try:
            url = f"https://api.dexscreener.com/latest/dex/tokens/{token_address}"
            async with self.session.get(url) as response:
                if response.status == 200:
                    data = await response.json()
                    pairs = data.get('pairs', [])
                    
                    if pairs:
                        base_token = pairs[0].get('baseToken', {})
                        symbol = base_token.get('symbol', '').strip()
                        name = base_token.get('name', '').strip()
                        
                        if symbol:
                            result = {'symbol': symbol, 'name': name}
                            self.logger.debug(f"✅ Resolved {token_address[:8]}... -> {symbol}")
        except Exception as e:
            self.logger.debug(f"❌ Symbol resolution failed for {token_address[:8]}...: {e}")
        
        # Try Birdeye if DexScreener failed
        if result['symbol'] == 'Unknown' and self.birdeye_api_key:
            try:
                url = f"https://public-api.birdeye.so/defi/token_overview"
                headers = {'X-API-KEY': self.birdeye_api_key}
                params = {'address': token_address}
                
                async with self.session.get(url, headers=headers, params=params) as response:
                    if response.status == 200:
                        data = await response.json()
                        symbol = data.get('symbol', '').strip()
                        name = data.get('name', '').strip()
                        
                        if symbol:
                            result = {'symbol': symbol, 'name': name}
                            self.logger.debug(f"✅ Birdeye resolved {token_address[:8]}... -> {symbol}")
            except Exception as e:
                self.logger.debug(f"❌ Birdeye resolution failed: {e}")
        
        self.symbol_cache[token_address] = result
        return result
    
    async def resolve_batch_symbols(self, token_addresses: List[str]) -> Dict[str, Dict[str, str]]:
        """Resolve symbols for multiple tokens"""
        results = {}
        
        # Process in small batches to avoid rate limits
        batch_size = 3
        for i in range(0, len(token_addresses), batch_size):
            batch = token_addresses[i:i + batch_size]
            
            tasks = [self.resolve_symbol(addr) for addr in batch]
            batch_results = await asyncio.gather(*tasks, return_exceptions=True)
            
            for addr, result in zip(batch, batch_results):
                if isinstance(result, dict):
                    results[addr] = result
                else:
                    results[addr] = {'symbol': 'Unknown', 'name': ''}
            
            # Small delay between batches
            if i + batch_size < len(token_addresses):
                await asyncio.sleep(0.5)
        
        return results

'''
        
        # Find where to insert the SymbolResolver class
        class_insert_point = content.find("class CrossPlatformAnalyzer:")
        
        if class_insert_point != -1:
            # Insert SymbolResolver before CrossPlatformAnalyzer
            new_content = (
                content[:class_insert_point] + 
                symbol_resolver_class + 
                content[class_insert_point:]
            )
            
            # Now modify the CrossPlatformAnalyzer __init__ method to include symbol resolver
            init_pattern = "def __init__(self, config: Optional[Dict] = None, logger: Optional[logging.Logger] = None):"
            init_replacement = """def __init__(self, config: Optional[Dict] = None, logger: Optional[logging.Logger] = None):
        # Initialize configuration
        self.config = config or {}
        self.logger = logger or logging.getLogger(__name__)
        
        # Initialize symbol resolver
        birdeye_key = os.getenv('BIRDEYE_API_KEY')
        self.symbol_resolver = SymbolResolver(birdeye_key)
        
        # Initialize other components"""
            
            new_content = new_content.replace(
                init_pattern,
                init_replacement
            )
            
            # Add symbol resolution to analyze_correlations method
            # Find the symbol extraction section and enhance it
            symbol_extraction_pattern = "# Enhanced symbol/name extraction with priority order: Birdeye > Narratives > DexScreener"
            
            if symbol_extraction_pattern in new_content:
                enhanced_extraction = """
            # Enhanced symbol/name extraction with priority order: Birdeye > Narratives > DexScreener > API Fallback
            symbol_found = False
            
            # Priority 1: Extract symbol/name from Birdeye data (most reliable)
            if 'birdeye' in token_data['data']:
                be_data = token_data['data']['birdeye']
                be_symbol = be_data.get('symbol', '').strip()
                be_name = be_data.get('name', '').strip()
                
                if be_symbol and be_symbol != 'Unknown':
                    token_info['symbol'] = be_symbol
                    symbol_found = True
                if be_name:
                    token_info['name'] = be_name
                    
                token_info['price'] = be_data.get('price', 0)
                token_info['volume_24h'] = be_data.get('volume_24h_usd', 0)
                token_info['market_cap'] = be_data.get('market_cap', 0)
                token_info['liquidity'] = be_data.get('liquidity', 0)
                token_info['price_change_24h'] = be_data.get('price_change_24h', 0)
            
            # Priority 2: Extract from narrative data if symbol not found or is Unknown
            if 'narratives' in token_data['data'] and token_data['data']['narratives']:
                narrative = token_data['data']['narratives'][0]  # Use first narrative
                narrative_symbol = narrative.get('symbol', '').strip()
                narrative_name = narrative.get('name', '').strip()
                
                if not symbol_found and narrative_symbol and narrative_symbol != 'Unknown':
                    token_info['symbol'] = narrative_symbol
                    symbol_found = True
                if not token_info['name'] and narrative_name:
                    token_info['name'] = narrative_name
                if token_info['price'] == 0:
                    token_info['price'] = narrative.get('price_usd', 0)
                if token_info['volume_24h'] == 0:
                    token_info['volume_24h'] = narrative.get('volume_24h', 0)
                if token_info['market_cap'] == 0:
                    token_info['market_cap'] = narrative.get('market_cap', 0)
                if token_info['liquidity'] == 0:
                    token_info['liquidity'] = narrative.get('liquidity_usd', 0)
                if token_info['price_change_24h'] == 0:
                    token_info['price_change_24h'] = narrative.get('price_change_24h', 0)
            
            # Priority 3: Try to extract from DexScreener data if still no symbol
            if not symbol_found and 'dexscreener' in token_data['data']:
                ds_data = token_data['data']['dexscreener']
                # DexScreener doesn't directly provide symbol, but might have it in description or links
                description = ds_data.get('description', '')
                if description and len(description) > 0:
                    # Try to extract symbol from description (basic heuristic)
                    words = description.split()
                    for word in words:
                        # Look for potential symbols (uppercase, 2-10 chars, alphanumeric)
                        if word.isupper() and 2 <= len(word) <= 10 and word.isalnum():
                            token_info['symbol'] = word
                            symbol_found = True
                            break
            
            # Priority 4: API Fallback - Use SymbolResolver for missing symbols
            if not symbol_found or token_info['symbol'] == 'Unknown':
                # Mark for symbol resolution (will be processed in batch later)
                token_info['needs_symbol_resolution'] = True
"""
                
                # Replace the symbol extraction section
                old_extraction_start = new_content.find("# Enhanced symbol/name extraction with priority order: Birdeye > Narratives > DexScreener")
                old_extraction_end = new_content.find("# Log symbol extraction for debugging", old_extraction_start)
                
                if old_extraction_start != -1 and old_extraction_end != -1:
                    new_content = (
                        new_content[:old_extraction_start] +
                        enhanced_extraction +
                        new_content[old_extraction_end:]
                    )
            
            # Add symbol resolution batch processing at the end of analyze_correlations
            batch_resolution_code = """
        
        # Batch resolve missing symbols
        tokens_needing_resolution = []
        for token_addr, token_info in correlations['all_tokens'].items():
            if token_info.get('needs_symbol_resolution', False):
                tokens_needing_resolution.append(token_addr)
        
        if tokens_needing_resolution:
            self.logger.info(f"🔍 Resolving symbols for {len(tokens_needing_resolution)} tokens...")
            
            # Initialize symbol resolver if needed
            await self.symbol_resolver.initialize()
            
            try:
                resolved_symbols = await self.symbol_resolver.resolve_batch_symbols(tokens_needing_resolution)
                
                # Update token info with resolved symbols
                for token_addr, symbol_data in resolved_symbols.items():
                    if token_addr in correlations['all_tokens']:
                        token_info = correlations['all_tokens'][token_addr]
                        
                        if symbol_data['symbol'] != 'Unknown':
                            token_info['symbol'] = symbol_data['symbol']
                            if symbol_data['name']:
                                token_info['name'] = symbol_data['name']
                            
                            self.logger.debug(f"✅ Resolved symbol for {token_addr[:8]}... -> {symbol_data['symbol']}")
                        
                        # Remove the resolution flag
                        token_info.pop('needs_symbol_resolution', None)
                
                self.logger.info(f"✅ Symbol resolution completed")
                
            except Exception as e:
                self.logger.error(f"❌ Symbol resolution failed: {e}")
                
                # Remove resolution flags even if failed
                for token_addr in tokens_needing_resolution:
                    if token_addr in correlations['all_tokens']:
                        correlations['all_tokens'][token_addr].pop('needs_symbol_resolution', None)
"""
            
            # Find the end of analyze_correlations method and add batch resolution
            method_end_pattern = "return correlations"
            new_content = new_content.replace(
                method_end_pattern,
                batch_resolution_code + "\n        " + method_end_pattern
            )
            
            # Add cleanup to close method
            close_pattern = "async def close(self):"
            if close_pattern in new_content:
                close_replacement = """async def close(self):
        \"\"\"Close all connections\"\"\"
        if hasattr(self, 'symbol_resolver') and self.symbol_resolver:
            await self.symbol_resolver.close()
        
        if hasattr(self, 'dexscreener') and self.dexscreener:
            # DexScreener cleanup if needed
            pass
        
        if hasattr(self, 'birdeye') and self.birdeye:
            await self.birdeye.close()"""
                
                new_content = new_content.replace(
                    close_pattern + "\n        \"\"\"Close all connections\"\"\"",
                    close_replacement
                )
            
            # Write the updated file
            with open(analyzer_file, 'w') as f:
                f.write(new_content)
            
            print("✅ Successfully applied comprehensive Unknown symbols fix!")
            print("📊 Changes made:")
            print("   - Added SymbolResolver class with multiple API fallbacks")
            print("   - Enhanced symbol extraction with API fallback priority")
            print("   - Added batch symbol resolution for missing symbols")
            print("   - Updated CrossPlatformAnalyzer initialization and cleanup")
            
        else:
            print("❌ Could not find CrossPlatformAnalyzer class")
    else:
        print("❌ Could not find __init__ method in CrossPlatformAnalyzer")

async def test_fix():
    """Test the fix by running a small analysis"""
    print("\n🧪 Testing the fix...")
    
    try:
        from scripts.cross_platform_token_analyzer import CrossPlatformAnalyzer
        
        analyzer = CrossPlatformAnalyzer()
        
        # Run a quick analysis
        result = await analyzer.run_analysis()
        
        # Check symbols in results
        correlations = result.get('correlations', {})
        multi_platform_tokens = correlations.get('multi_platform_tokens', [])
        
        print(f"📊 Analysis completed - found {len(multi_platform_tokens)} multi-platform tokens")
        
        # Check symbol quality
        symbols_resolved = 0
        for token in multi_platform_tokens[:10]:
            symbol = token.get('symbol', 'Unknown')
            if symbol != 'Unknown' and not ('...' in symbol and len(symbol) < 15):
                symbols_resolved += 1
            
            print(f"   {token.get('address', '')[:12]}... -> {symbol}")
        
        print(f"✅ Symbol resolution rate: {symbols_resolved}/{min(10, len(multi_platform_tokens))}")
        
        await analyzer.close()
        
    except Exception as e:
        print(f"❌ Test failed: {e}")

if __name__ == "__main__":
    asyncio.run(apply_comprehensive_fix())
    # Uncomment to test after applying fix
    # asyncio.run(test_fix()) 