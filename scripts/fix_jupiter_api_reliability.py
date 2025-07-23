#!/usr/bin/env python3
"""
Jupiter API Reliability Fix
Addresses the 11.5% success rate issue by improving error handling and implementing fallbacks
"""

import sys
import os
import re
import asyncio
import aiohttp
from pathlib import Path

sys.path.append(os.getcwd())

class JupiterAPIReliabilityFixer:
    """Fix Jupiter API reliability issues"""
    
    def __init__(self):
        self.cross_platform_analyzer_path = "scripts/cross_platform_token_analyzer.py"
        self.fixes_applied = []
    
    def apply_all_fixes(self):
        """Apply all Jupiter API reliability fixes"""
        print("🔴 JUPITER API RELIABILITY FIXER")
        print("=" * 50)
        print("Current Success Rate: 11.5% (CRITICAL)")
        print("Target Success Rate: 80%+")
        print("=" * 50)
        
        # Test current Jupiter endpoints
        print("\n🔍 Testing Jupiter endpoints...")
        working_endpoints = asyncio.run(self.test_jupiter_endpoints())
        
        # Apply fixes based on test results
        if self.cross_platform_analyzer_exists():
            self.fix_jupiter_connector_in_analyzer(working_endpoints)
        
        # Display summary
        self.display_fix_summary()
        
        return len(self.fixes_applied) > 0
    
    async def test_jupiter_endpoints(self) -> dict:
        """Test Jupiter API endpoints to identify working ones"""
        endpoints_to_test = {
            'token_list_primary': 'https://token.jup.ag/all',
            'token_list_lite': 'https://lite-api.jup.ag/tokens',
            'quote_api': 'https://quote-api.jup.ag/v6/quote',
            'price_api': 'https://lite-api.jup.ag/price/v2'
        }
        
        working_endpoints = {}
        
        async with aiohttp.ClientSession() as session:
            for name, url in endpoints_to_test.items():
                try:
                    # Set appropriate test parameters
                    params = {}
                    if name == 'quote_api':
                        params = {
                            'inputMint': 'So11111111111111111111111111111111111111112',  # SOL
                            'outputMint': 'EPjFWdd5AufqSSqeM2qN1xzybapC8G4wEGGkZwyTDt1v',  # USDC
                            'amount': '1000000'
                        }
                    elif name == 'price_api':
                        params = {
                            'ids': 'So11111111111111111111111111111111111111112',
                            'vsToken': 'EPjFWdd5AufqSSqeM2qN1xzybapC8G4wEGGkZwyTDt1v'
                        }
                    
                    async with session.get(url, params=params, timeout=10) as response:
                        if response.status == 200:
                            data = await response.json()
                            working_endpoints[name] = {
                                'url': url, 
                                'status': 'working',
                                'data_size': len(data) if isinstance(data, (list, dict)) else 1
                            }
                            print(f"✅ {name}: Working ({len(data) if isinstance(data, (list, dict)) else 1} items)")
                        else:
                            print(f"❌ {name}: Failed (HTTP {response.status})")
                            
                except Exception as e:
                    print(f"❌ {name}: Error - {str(e)[:50]}")
                
                await asyncio.sleep(0.5)  # Rate limiting
        
        return working_endpoints
    
    def cross_platform_analyzer_exists(self) -> bool:
        """Check if cross-platform analyzer exists"""
        return os.path.exists(self.cross_platform_analyzer_path)
    
    def fix_jupiter_connector_in_analyzer(self, working_endpoints: dict):
        """Fix Jupiter connector in cross-platform analyzer"""
        print("\n🔧 Fixing Jupiter connector in cross-platform analyzer...")
        
        if not os.path.exists(self.cross_platform_analyzer_path):
            print("❌ Cross-platform analyzer not found")
            return
        
        try:
            # Read the current file
            with open(self.cross_platform_analyzer_path, 'r') as f:
                content = f.read()
            
            # Create backup
            backup_path = f"{self.cross_platform_analyzer_path}.backup_jupiter_fix"
            with open(backup_path, 'w') as f:
                f.write(content)
            print(f"✅ Backup created: {backup_path}")
            
            # Apply fixes to Jupiter connector class
            updated_content = self.update_jupiter_connector_class(content, working_endpoints)
            
            if updated_content != content:
                # Write the updated file
                with open(self.cross_platform_analyzer_path, 'w') as f:
                    f.write(updated_content)
                
                print("✅ Jupiter connector updated with improved reliability")
                self.fixes_applied.append("Enhanced Jupiter connector with fallbacks and retry logic")
            else:
                print("⚠️ No updates needed for Jupiter connector")
                
        except Exception as e:
            print(f"❌ Error fixing Jupiter connector: {e}")
    
    def update_jupiter_connector_class(self, content: str, working_endpoints: dict) -> str:
        """Update the Jupiter connector class with better error handling"""
        
        # Find the Jupiter connector class
        jupiter_class_pattern = r'class JupiterConnector:.*?(?=class|\Z)'
        match = re.search(jupiter_class_pattern, content, re.DOTALL)
        
        if not match:
            print("⚠️ Jupiter connector class not found")
            return content
        
        # Create improved Jupiter connector
        improved_connector = self.create_improved_jupiter_connector(working_endpoints)
        
        # Replace the Jupiter connector class
        updated_content = re.sub(jupiter_class_pattern, improved_connector, content, flags=re.DOTALL)
        
        return updated_content
    
    def create_improved_jupiter_connector(self, working_endpoints: dict) -> str:
        """Create improved Jupiter connector with better reliability"""
        
        # Determine best endpoints to use
        token_list_url = working_endpoints.get('token_list_primary', {}).get('url', 'https://token.jup.ag/all')
        fallback_token_url = working_endpoints.get('token_list_lite', {}).get('url', 'https://lite-api.jup.ag/tokens')
        quote_url = working_endpoints.get('quote_api', {}).get('url', 'https://quote-api.jup.ag/v6/quote')
        price_url = working_endpoints.get('price_api', {}).get('url', 'https://lite-api.jup.ag/price/v2')
        
        return f'''class JupiterConnector:
    """Enhanced Jupiter API connector with improved reliability and fallbacks"""
    
    def __init__(self, enhanced_cache: Optional[EnhancedPositionCacheManager] = None):
        self.enhanced_cache = enhanced_cache
        self.logger = logging.getLogger(__name__)
        
        # Primary and fallback endpoints
        self.endpoints = {{
            'primary_tokens': '{token_list_url}',
            'fallback_tokens': '{fallback_token_url}',
            'quote_api': '{quote_url}',
            'price_api': '{price_url}'
        }}
        
        self.session = None
        self.max_retries = 3
        self.retry_delay = 1.0
        
        # Enhanced API tracking
        self.api_calls = 0
        self.successful_calls = 0
        self.failed_calls = 0
        self.fallback_used = 0
        self.last_error = None
        self.start_time = time.time()
        
        # Exclusion system - load from central system
        self.excluded_addresses = set()
        self._load_exclusions()
    
    def _load_exclusions(self):
        """Load exclusions from central system"""
        try:
            from services.early_token_detection import EarlyTokenDetector
            detector = EarlyTokenDetector()
            if hasattr(detector, 'excluded_addresses'):
                self.excluded_addresses = detector.excluded_addresses.copy()
                self.logger.info(f"🚫 Loaded {{len(self.excluded_addresses)}} exclusions from central system")
        except Exception as e:
            self.logger.warning(f"⚠️ Could not load central exclusions: {{e}}")
            # Fallback to basic exclusions
            self.excluded_addresses = {{
                'EPjFWdd5AufqSSqeM2qN1xzybapC8G4wEGGkZwyTDt1v',  # USDC
                'Es9vMFrzaCERmJfrF4H2FYD4KCoNkY11McCe8BenwNYB',  # USDT
                '4k3Dyjzvzp8eMZWUXbBCjEvwSkkk59S5iCNLY3QrkX6R',  # RAY
                'So11111111111111111111111111111111111111112'    # Wrapped SOL
            }}
    
    async def _make_reliable_request(self, primary_url: str, fallback_url: str = None, 
                                   params: dict = None) -> Optional[Dict]:
        """Make a reliable request with fallback and retry logic"""
        
        if not self.session:
            connector = aiohttp.TCPConnector(
                limit=100,
                limit_per_host=10,
                ttl_dns_cache=300,
                use_dns_cache=True,
                enable_cleanup_closed=True
            )
            self.session = aiohttp.ClientSession(
                connector=connector,
                timeout=aiohttp.ClientTimeout(total=15, connect=5),
                headers={{
                    'User-Agent': 'VirtuosoGemHunter/2.0',
                    'Accept': 'application/json'
                }}
            )
        
        urls_to_try = [primary_url]
        if fallback_url and fallback_url != primary_url:
            urls_to_try.append(fallback_url)
        
        for url in urls_to_try:
            for attempt in range(self.max_retries):
                self.api_calls += 1
                
                try:
                    async with self.session.get(url, params=params) as response:
                        if response.status == 200:
                            data = await response.json()
                            self.successful_calls += 1
                            
                            if url != primary_url:
                                self.fallback_used += 1
                                self.logger.info(f"✅ Jupiter fallback successful: {{url}}")
                            
                            return data
                        else:
                            error_text = await response.text()
                            self.last_error = f"HTTP {{response.status}}: {{error_text[:100]}}"
                            
                except Exception as e:
                    self.last_error = str(e)
                    if attempt < self.max_retries - 1:
                        delay = self.retry_delay * (2 ** attempt)
                        await asyncio.sleep(delay)
        
        self.failed_calls += 1
        self.logger.warning(f"❌ Jupiter request failed after retries: {{self.last_error}}")
        return None
    
    async def get_emerging_tokens(self, limit: int = 50) -> List[Dict]:
        """Get emerging tokens with improved reliability"""
        
        # Try primary endpoint first, then fallback
        data = await self._make_reliable_request(
            self.endpoints['primary_tokens'],
            self.endpoints['fallback_tokens']
        )
        
        if not data or not isinstance(data, list):
            self.logger.error("❌ Failed to get Jupiter token list")
            return []
        
        # Filter and process tokens
        filtered_tokens = []
        for token in data:
            if not isinstance(token, dict):
                continue
                
            address = token.get('address', '')
            if address in self.excluded_addresses:
                continue
            
            # Extract relevant token data
            token_data = {{
                'address': address,
                'symbol': token.get('symbol', ''),
                'name': token.get('name', ''),
                'decimals': token.get('decimals', 9),
                'tags': token.get('tags', []),
                'daily_volume': token.get('daily_volume', 0),
                'platform': 'jupiter',
                'discovery_source': 'jupiter_token_list'
            }}
            
            filtered_tokens.append(token_data)
            
            if len(filtered_tokens) >= limit:
                break
        
        self.logger.info(f"🪙 Jupiter emerging tokens: {{len(filtered_tokens)}} (from {{len(data)}} total)")
        return filtered_tokens
    
    async def get_token_price(self, token_address: str) -> Optional[float]:
        """Get token price with improved reliability"""
        
        # Try quote API first
        quote_params = {{
            'inputMint': token_address,
            'outputMint': 'EPjFWdd5AufqSSqeM2qN1xzybapC8G4wEGGkZwyTDt1v',  # USDC
            'amount': '1000000'
        }}
        
        quote_data = await self._make_reliable_request(
            self.endpoints['quote_api'],
            params=quote_params
        )
        
        if quote_data and 'outAmount' in quote_data:
            try:
                out_amount = float(quote_data['outAmount'])
                if out_amount > 0:
                    return out_amount / 1000000  # Convert to price per token
            except (ValueError, KeyError):
                pass
        
        # Fallback to price API
        price_params = {{
            'ids': token_address,
            'vsToken': 'EPjFWdd5AufqSSqeM2qN1xzybapC8G4wEGGkZwyTDt1v'
        }}
        
        price_data = await self._make_reliable_request(
            self.endpoints['price_api'],
            params=price_params
        )
        
        if price_data and 'data' in price_data:
            try:
                token_data = price_data['data'].get(token_address)
                if token_data and 'price' in token_data:
                    return float(token_data['price'])
            except (ValueError, KeyError):
                pass
        
        return None
    
    def get_api_call_statistics(self) -> Dict[str, Any]:
        """Get comprehensive API call statistics"""
        runtime = time.time() - self.start_time
        success_rate = (self.successful_calls / self.api_calls * 100) if self.api_calls > 0 else 0
        
        return {{
            'total_calls': self.api_calls,
            'successful_calls': self.successful_calls,
            'failed_calls': self.failed_calls,
            'success_rate': round(success_rate, 1),
            'fallback_usage': self.fallback_used,
            'runtime_seconds': round(runtime, 2),
            'calls_per_minute': round((self.api_calls / runtime * 60), 2) if runtime > 0 else 0,
            'last_error': self.last_error
        }}
    
    def reset_api_statistics(self):
        """Reset API call statistics"""
        self.api_calls = 0
        self.successful_calls = 0
        self.failed_calls = 0
        self.fallback_used = 0
        self.last_error = None
        self.start_time = time.time()
    
    async def close(self):
        """Close HTTP session"""
        if self.session and not self.session.closed:
            await self.session.close()
            self.session = None

    def display_fix_summary(self):
        """Display summary of fixes applied"""
        print("\n" + "=" * 50)
        print("🎉 JUPITER API RELIABILITY FIXES SUMMARY")
        print("=" * 50)
        
        if self.fixes_applied:
            for i, fix in enumerate(self.fixes_applied, 1):
                print(f"{i}. ✅ {fix}")
            
            print(f"\n📊 EXPECTED IMPROVEMENTS:")
            print(f"   • Success rate: 11.5% → 80%+ (with fallbacks)")
            print(f"   • Retry logic: 3 attempts with exponential backoff")
            print(f"   • Fallback endpoints: Primary + backup URLs")
            print(f"   • Connection pooling: Improved session management")
            print(f"   • Error handling: Better exception management")
            
            print(f"\n🚀 NEXT STEPS:")
            print(f"   1. Restart the detector to use updated Jupiter connector")
            print(f"   2. Monitor Jupiter API success rate in next run")
            print(f"   3. Check logs for fallback usage statistics")
            
        else:
            print("⚠️ No fixes were applied")
        
        print("=" * 50)

def main():
    """Main function to apply Jupiter API fixes"""
    fixer = JupiterAPIReliabilityFixer()
    success = fixer.apply_all_fixes()
    
    if success:
        print("\n🎯 Jupiter API reliability fixes applied!")
        print("   The success rate should improve significantly.")
        return 0
    else:
        print("\n❌ Jupiter API fixes could not be applied.")
        return 1

if __name__ == "__main__":
    exit(main()) 