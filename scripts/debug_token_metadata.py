#!/usr/bin/env python3
"""
Debug Token Metadata Extraction
Investigates why tokens are showing as "Unknown" and traces the metadata pipeline
"""

import asyncio
import json
import os
import sys
from datetime import datetime
from pathlib import Path

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

try:
    from scripts.cross_platform_token_analyzer import CrossPlatformAnalyzer
    from api.birdeye_connector import BirdeyeAPI
    from core.cache_manager import CacheManager
    from services.rate_limiter_service import RateLimiterService
    from utils.logger_setup import LoggerSetup
    from core.config_manager import ConfigManager
except ImportError as e:
    print(f"❌ Import error: {e}")
    sys.exit(1)


class TokenMetadataDebugger:
    """Debug token metadata extraction issues"""
    
    def __init__(self):
        self.config_manager = ConfigManager("config/config.yaml")
        self.config = self.config_manager.get_config()
        
        # Initialize logging
        self.logger_setup = LoggerSetup("TokenMetadataDebugger")
        self.logger = self.logger_setup.logger
        
        # Initialize services
        self.cache_manager = CacheManager()
        self.rate_limiter = RateLimiterService()
        
        # Initialize APIs
        self._init_apis()
        
    def _init_apis(self):
        """Initialize API connections"""
        try:
            # Initialize cross-platform analyzer
            self.cross_platform_analyzer = CrossPlatformAnalyzer(
                config=self.config,
                logger=self.logger
            )
            
            # Initialize Birdeye API
            birdeye_api_key = os.getenv('BIRDEYE_API_KEY')
            if birdeye_api_key:
                birdeye_config = self.config.get('BIRDEYE_API', {})
                birdeye_config['api_key'] = birdeye_api_key
                
                self.birdeye_api = BirdeyeAPI(
                    config=birdeye_config,
                    logger=self.logger,
                    cache_manager=self.cache_manager,
                    rate_limiter=self.rate_limiter
                )
                self.logger.info("✅ Birdeye API initialized")
            else:
                self.birdeye_api = None
                self.logger.error("❌ BIRDEYE_API_KEY not found")
                
        except Exception as e:
            self.logger.error(f"❌ Error initializing APIs: {e}")
            raise
    
    async def debug_token_metadata_pipeline(self):
        """Debug the complete token metadata extraction pipeline"""
        
        print("🔍" * 80)
        print("🔍 TOKEN METADATA DEBUGGING PIPELINE")
        print("🔍" * 80)
        
        # Step 1: Debug Cross-Platform Analysis
        print(f"\n📊 STEP 1: CROSS-PLATFORM ANALYSIS DEBUG")
        print("="*60)
        
        cross_platform_results = await self.cross_platform_analyzer.run_analysis()
        
        if not cross_platform_results:
            print("❌ No cross-platform results returned")
            return
        
        # Analyze the structure
        self._debug_cross_platform_structure(cross_platform_results)
        
        # Step 2: Extract sample tokens for detailed analysis
        sample_tokens = self._extract_sample_tokens(cross_platform_results)
        
        if not sample_tokens:
            print("❌ No sample tokens found for analysis")
            return
        
        # Step 3: Debug individual token metadata extraction
        print(f"\n🔬 STEP 3: INDIVIDUAL TOKEN METADATA DEBUG")
        print("="*60)
        
        for i, token in enumerate(sample_tokens[:3], 1):  # Debug first 3 tokens
            print(f"\n🪙 TOKEN #{i} ANALYSIS:")
            print(f"  📍 Address: {token.get('address', 'MISSING')}")
            print(f"  🏷️  Symbol: {token.get('symbol', 'MISSING')}")
            print(f"  📛 Name: {token.get('name', 'MISSING')}")
            print(f"  🌐 Platforms: {token.get('platforms', [])}")
            
            await self._debug_individual_token_metadata(token)
            
            print("-" * 40)
    
    def _debug_cross_platform_structure(self, results: dict):
        """Debug the cross-platform results structure"""
        print(f"\n📋 CROSS-PLATFORM RESULTS STRUCTURE:")
        print(f"  🔑 Top-level keys: {list(results.keys())}")
        
        # Check correlations structure
        correlations = results.get('correlations', {})
        print(f"  📊 Correlations keys: {list(correlations.keys())}")
        
        # Check multi-platform tokens
        multi_platform_tokens = correlations.get('multi_platform_tokens', [])
        print(f"  🔗 Multi-platform tokens count: {len(multi_platform_tokens)}")
        
        if multi_platform_tokens:
            sample_token = multi_platform_tokens[0]
            print(f"  📋 Sample multi-platform token structure:")
            for key, value in sample_token.items():
                if isinstance(value, (str, int, float, bool)):
                    print(f"    • {key}: {value}")
                else:
                    print(f"    • {key}: {type(value)} (length: {len(value) if hasattr(value, '__len__') else 'N/A'})")
        
        # Check all tokens structure
        all_tokens = correlations.get('all_tokens', {})
        print(f"  📊 All tokens count: {len(all_tokens)}")
        
        if all_tokens:
            sample_address = list(all_tokens.keys())[0]
            sample_data = all_tokens[sample_address]
            print(f"  📋 Sample all_tokens entry structure:")
            print(f"    📍 Address: {sample_address}")
            for key, value in sample_data.items():
                if isinstance(value, (str, int, float, bool)):
                    print(f"    • {key}: {value}")
                else:
                    print(f"    • {key}: {type(value)}")
        
        # Check platform data
        platform_data = results.get('platform_data', {})
        print(f"  🌐 Platform data keys: {list(platform_data.keys())}")
        
        for platform, data in platform_data.items():
            if isinstance(data, list):
                print(f"    📡 {platform}: {len(data)} items")
                if data and isinstance(data[0], dict):
                    sample_item = data[0]
                    print(f"      📋 Sample item keys: {list(sample_item.keys())}")
                    # Check for symbol/name fields
                    symbol_fields = [k for k in sample_item.keys() if 'symbol' in k.lower()]
                    name_fields = [k for k in sample_item.keys() if 'name' in k.lower()]
                    print(f"      🏷️  Symbol fields: {symbol_fields}")
                    print(f"      📛 Name fields: {name_fields}")
            else:
                print(f"    📡 {platform}: {type(data)}")
    
    def _extract_sample_tokens(self, results: dict) -> list:
        """Extract sample tokens for detailed analysis"""
        sample_tokens = []
        
        # Try to get from multi_platform_tokens first
        correlations = results.get('correlations', {})
        multi_platform_tokens = correlations.get('multi_platform_tokens', [])
        
        if multi_platform_tokens:
            sample_tokens.extend(multi_platform_tokens[:5])
            print(f"✅ Extracted {len(sample_tokens)} tokens from multi_platform_tokens")
        
        # If not enough, get from all_tokens
        if len(sample_tokens) < 3:
            all_tokens = correlations.get('all_tokens', {})
            for address, token_data in list(all_tokens.items())[:5]:
                if address and address not in [t.get('address') for t in sample_tokens]:
                    token_data['address'] = address
                    sample_tokens.append(token_data)
        
        print(f"📊 Total sample tokens for analysis: {len(sample_tokens)}")
        return sample_tokens
    
    async def _debug_individual_token_metadata(self, token: dict):
        """Debug metadata extraction for an individual token"""
        address = token.get('address')
        if not address:
            print("    ❌ No address found for token")
            return
        
        print(f"    🔍 DEBUGGING TOKEN: {address}")
        
        # Check if Birdeye API is available
        if not self.birdeye_api:
            print("    ❌ Birdeye API not available")
            return
        
        try:
            # Get token overview from Birdeye
            print(f"    📡 Fetching Birdeye token overview...")
            overview = await self.birdeye_api.get_token_overview(address)
            
            if overview is None:
                print(f"    ❌ Birdeye overview returned None")
                return
            
            if not isinstance(overview, dict):
                print(f"    ❌ Birdeye overview returned {type(overview)}, expected dict")
                return
            
            print(f"    ✅ Birdeye overview fetched successfully")
            print(f"    📊 Overview fields count: {len(overview)}")
            
            # Check symbol and name extraction
            birdeye_symbol = overview.get('symbol', 'NOT_FOUND')
            birdeye_name = overview.get('name', 'NOT_FOUND')
            
            print(f"    🏷️  Birdeye Symbol: '{birdeye_symbol}'")
            print(f"    📛 Birdeye Name: '{birdeye_name}'")
            
            # Compare with cross-platform data
            cross_platform_symbol = token.get('symbol', 'NOT_FOUND')
            cross_platform_name = token.get('name', 'NOT_FOUND')
            
            print(f"    🔗 Cross-Platform Symbol: '{cross_platform_symbol}'")
            print(f"    🔗 Cross-Platform Name: '{cross_platform_name}'")
            
            # Check for symbol/name mismatches
            if birdeye_symbol != cross_platform_symbol:
                print(f"    ⚠️  SYMBOL MISMATCH detected!")
                print(f"      Cross-Platform: '{cross_platform_symbol}'")
                print(f"      Birdeye: '{birdeye_symbol}'")
            
            if birdeye_name != cross_platform_name:
                print(f"    ⚠️  NAME MISMATCH detected!")
                print(f"      Cross-Platform: '{cross_platform_name}'")
                print(f"      Birdeye: '{birdeye_name}'")
            
            # Check for "Unknown" issues
            if cross_platform_symbol in ['Unknown', '', None]:
                print(f"    🚨 CROSS-PLATFORM SYMBOL ISSUE: '{cross_platform_symbol}'")
                print(f"    💡 Birdeye has: '{birdeye_symbol}'")
            
            if cross_platform_name in ['', None]:
                print(f"    🚨 CROSS-PLATFORM NAME ISSUE: '{cross_platform_name}'")
                print(f"    💡 Birdeye has: '{birdeye_name}'")
            
            # Check other important fields
            price = overview.get('price', 'NOT_FOUND')
            market_cap = overview.get('marketCap', 'NOT_FOUND')
            liquidity = overview.get('liquidity', 'NOT_FOUND')
            
            print(f"    💰 Price: {price}")
            print(f"    📊 Market Cap: {market_cap}")
            print(f"    💧 Liquidity: {liquidity}")
            
            # Save detailed debug info
            debug_info = {
                'address': address,
                'timestamp': datetime.now().isoformat(),
                'cross_platform_data': token,
                'birdeye_overview': overview,
                'analysis': {
                    'symbol_mismatch': birdeye_symbol != cross_platform_symbol,
                    'name_mismatch': birdeye_name != cross_platform_name,
                    'cross_platform_symbol_issue': cross_platform_symbol in ['Unknown', '', None],
                    'cross_platform_name_issue': cross_platform_name in ['', None],
                    'birdeye_symbol': birdeye_symbol,
                    'birdeye_name': birdeye_name,
                    'cross_platform_symbol': cross_platform_symbol,
                    'cross_platform_name': cross_platform_name
                }
            }
            
            # Save to file for further analysis
            debug_file = f"debug/token_metadata_debug_{address[:8]}.json"
            os.makedirs("debug", exist_ok=True)
            with open(debug_file, 'w') as f:
                json.dump(debug_info, f, indent=2, default=str)
            
            print(f"    💾 Debug info saved to: {debug_file}")
            
        except Exception as e:
            print(f"    ❌ Error debugging token {address}: {e}")
            import traceback
            print(f"    🔍 Traceback: {traceback.format_exc()}")
    
    async def analyze_token_registry(self):
        """Analyze the latest token registry to understand the Unknown token issue"""
        
        print(f"\n📁 STEP 4: TOKEN REGISTRY ANALYSIS")
        print("="*60)
        
        # Find the latest token registry file
        data_dir = Path("data")
        registry_files = list(data_dir.glob("token_registry_*.json"))
        
        if not registry_files:
            print("❌ No token registry files found")
            return
        
        latest_registry = max(registry_files, key=lambda x: x.stat().st_mtime)
        print(f"📄 Latest registry: {latest_registry}")
        
        try:
            with open(latest_registry, 'r') as f:
                registry_data = json.load(f)
            
            # Analyze unique tokens
            unique_tokens = registry_data.get('unique_tokens_discovered', {})
            print(f"📊 Total unique tokens in registry: {len(unique_tokens)}")
            
            unknown_count = 0
            empty_name_count = 0
            
            for address, token_data in unique_tokens.items():
                symbol = token_data.get('symbol', '')
                name = token_data.get('name', '')
                
                if symbol == 'Unknown':
                    unknown_count += 1
                    print(f"  🚨 Unknown symbol: {address[:8]}... - Name: '{name}'")
                
                if not name or name == '':
                    empty_name_count += 1
                    print(f"  🚨 Empty name: {address[:8]}... - Symbol: '{symbol}'")
            
            print(f"\n📈 REGISTRY ANALYSIS SUMMARY:")
            print(f"  🚨 Unknown symbols: {unknown_count}/{len(unique_tokens)} ({(unknown_count/len(unique_tokens)*100):.1f}%)")
            print(f"  🚨 Empty names: {empty_name_count}/{len(unique_tokens)} ({(empty_name_count/len(unique_tokens)*100):.1f}%)")
            
        except Exception as e:
            print(f"❌ Error analyzing token registry: {e}")
    
    async def run_complete_debug(self):
        """Run complete debugging pipeline"""
        try:
            await self.debug_token_metadata_pipeline()
            await self.analyze_token_registry()
            
            print(f"\n✅ DEBUGGING COMPLETE")
            print("="*60)
            print("📋 Check the debug/ directory for detailed token analysis files")
            print("💡 Look for patterns in symbol/name mismatches")
            print("🔧 Use findings to improve metadata extraction pipeline")
            
        except Exception as e:
            self.logger.error(f"❌ Error in complete debug: {e}")
            import traceback
            traceback.print_exc()
        finally:
            if self.birdeye_api:
                await self.birdeye_api.close()


async def main():
    debugger = TokenMetadataDebugger()
    await debugger.run_complete_debug()


if __name__ == "__main__":
    asyncio.run(main()) 