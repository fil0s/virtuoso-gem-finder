#!/usr/bin/env python3
"""
RugCheck vs Birdeye Trending Tokens Comparison

This script compares trending tokens from both RugCheck and Birdeye APIs to analyze:
- Quality differences between the two sources
- Overlap in trending tokens
- Which source provides better filtering
- Effectiveness of each API's trending algorithm

The RugCheck /stats/trending endpoint returns exactly 10 tokens with inherent quality filtering,
while Birdeye provides larger sets that may need more filtering.

Based on RugCheck API documentation: https://api.rugcheck.xyz/swagger/index.html#/
"""

import asyncio
import json
import time
import sys
import os
from pathlib import Path
from typing import List, Dict, Any, Optional, Set, Tuple
from dataclasses import dataclass

# Add project root to Python path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from api.rugcheck_connector import RugCheckConnector, RugRiskLevel
from api.birdeye_connector import BirdeyeAPI
from core.config_manager import ConfigManager
from utils.logger_setup import LoggerSetup


@dataclass
class TrendingComparison:
    """Container for trending comparison results"""
    rugcheck_tokens: List[Dict[str, Any]]
    birdeye_tokens: List[Dict[str, Any]]
    overlap_tokens: List[Dict[str, Any]]
    rugcheck_only: List[Dict[str, Any]]
    birdeye_only: List[Dict[str, Any]]
    quality_analysis: Dict[str, Any]
    api_performance: Dict[str, Any]


class RugCheckVsBirdeyeTrendingComparison:
    
    def __init__(self):
        # Setup logging
        logger_setup = LoggerSetup("TrendingComparison")
        self.logger = logger_setup.logger
        
        # Setup configuration
        self.config_manager = ConfigManager()
        config_dict = self.config_manager.get_config()
        
        # Initialize RugCheck API
        self.rugcheck = RugCheckConnector(logger=self.logger)
        
        # Initialize Birdeye API (optional)
        self.birdeye_api = None
        try:
            birdeye_config = config_dict.get('api', {}).get('birdeye', {})
            if birdeye_config:
                from api.rate_limiter_service import RateLimiterService
                from api.cache_manager import CacheManager
                
                cache_manager = CacheManager(self.logger)
                rate_limiter = RateLimiterService(self.logger)
                
                self.birdeye_api = BirdeyeAPI(
                    config=birdeye_config,
                    logger=self.logger,
                    cache_manager=cache_manager,
                    rate_limiter=rate_limiter
                )
                self.logger.info("✅ Birdeye API initialized successfully")
            else:
                self.logger.warning("⚠️ Birdeye API configuration not found, will use sample data")
        except Exception as e:
            self.logger.warning(f"⚠️ Failed to initialize Birdeye API: {e}, will use sample data")
    
    def _get_sample_birdeye_trending(self) -> List[Dict[str, Any]]:
        """Get sample Birdeye trending tokens if API is not available"""
        return [
            {"address": "EPjFWdd5AufqSSqeM2qN1xzybapC8G4wEGGkZwyTDt1v", "symbol": "USDC", "name": "USD Coin", "volume_24h_usd": 50000000, "source": "birdeye_sample"},
            {"address": "So11111111111111111111111111111111111111112", "symbol": "SOL", "name": "Solana", "volume_24h_usd": 30000000, "source": "birdeye_sample"},
            {"address": "mSoLzYCxHdYgdzU16g5QSh3i5K3z3KZK7ytfqcJm7So", "symbol": "mSOL", "name": "Marinade SOL", "volume_24h_usd": 5000000, "source": "birdeye_sample"},
            {"address": "DezXAZ8z7PnrnRJjz3wXBoRgixCa6xjnB7YaB1pPB263", "symbol": "BONK", "name": "Bonk", "volume_24h_usd": 8000000, "source": "birdeye_sample"},
            {"address": "4k3Dyjzvzp8eMZWUXbBCjEvwSkkk59S5iCNLY3QrkX6R", "symbol": "RAY", "name": "Raydium", "volume_24h_usd": 2000000, "source": "birdeye_sample"},
            {"address": "7dHbWXmci3dT8UFYWYZweBLXgycu7Y3iL6trKn1Y7ARj", "symbol": "stSOL", "name": "Lido Staked SOL", "volume_24h_usd": 3000000, "source": "birdeye_sample"},
            {"address": "9n4nbM75f5Ui33ZbPYXn59EwSgE8CGsHtAeTH5YFeJ9E", "symbol": "BTC", "name": "Wrapped BTC", "volume_24h_usd": 1500000, "source": "birdeye_sample"},
            {"address": "2FPyTwcZLUg1MDrwsyoP4D6s1tM7hAkHYRjkNb5w6Pxk", "symbol": "ETH", "name": "Wrapped ETH", "volume_24h_usd": 1200000, "source": "birdeye_sample"},
            {"address": "A1KLoBrKBde8Ty9qtNQUtq3C2ortoC3u7twggz7sEto6", "symbol": "NEWCOIN", "name": "New Sample Coin", "volume_24h_usd": 800000, "source": "birdeye_sample"},
            {"address": "B2LoBrKBde8Ty9qtNQUtq3C2ortoC3u7twggz7sEto7", "symbol": "MEMECOIN", "name": "Meme Sample Coin", "volume_24h_usd": 600000, "source": "birdeye_sample"},
        ]
    
    async def fetch_rugcheck_trending(self) -> List[Dict[str, Any]]:
        """Fetch trending tokens from RugCheck API (exactly 10 tokens)"""
        self.logger.info("🔥 Fetching trending tokens from RugCheck API (/stats/trending)...")
        start_time = time.time()
        
        trending_tokens = await self.rugcheck.get_trending_tokens()
        
        fetch_time = time.time() - start_time
        self.logger.info(f"✅ RugCheck trending fetch completed in {fetch_time:.2f}s, got {len(trending_tokens)} tokens")
        
        return trending_tokens
    
    async def fetch_birdeye_trending(self, limit: int = 15) -> List[Dict[str, Any]]:
        """Fetch trending tokens from Birdeye API"""
        if not self.birdeye_api:
            self.logger.info("🔥 Using sample Birdeye trending tokens for comparison...")
            return self._get_sample_birdeye_trending()
        
        self.logger.info(f"🔥 Fetching trending tokens from Birdeye API (limit: {limit})...")
        start_time = time.time()
        
        try:
            # Try multiple methods to get trending tokens from Birdeye
            trending_tokens = []
            
            # Method 1: Direct trending endpoint
            try:
                trending_data = await self.birdeye_api.get_trending_tokens()
                if trending_data and isinstance(trending_data, list):
                    trending_tokens = trending_data[:limit]
                    self.logger.info(f"✅ Got {len(trending_tokens)} tokens from Birdeye trending endpoint")
            except Exception as e:
                self.logger.warning(f"Birdeye trending endpoint failed: {e}")
            
            # Method 2: High volume token list
            if not trending_tokens:
                try:
                    token_list_data = await self.birdeye_api.get_token_list(
                        sort_by="volume_24h_usd",
                        sort_type="desc",
                        min_volume_24h_usd=100000,
                        limit=limit
                    )
                    
                    if token_list_data and 'data' in token_list_data:
                        if isinstance(token_list_data['data'], dict) and 'items' in token_list_data['data']:
                            trending_tokens = token_list_data['data']['items'][:limit]
                        elif isinstance(token_list_data['data'], list):
                            trending_tokens = token_list_data['data'][:limit]
                    
                    if trending_tokens:
                        self.logger.info(f"✅ Got {len(trending_tokens)} tokens from Birdeye high-volume list")
                except Exception as e:
                    self.logger.warning(f"Birdeye token list failed: {e}")
            
            # Fallback to sample data
            if not trending_tokens:
                self.logger.warning("All Birdeye endpoints failed, using sample data")
                trending_tokens = self._get_sample_birdeye_trending()
            
            # Normalize format
            normalized_tokens = []
            for token in trending_tokens:
                normalized_token = {
                    'address': token.get('address', ''),
                    'symbol': token.get('symbol', 'UNKNOWN'),
                    'name': token.get('name', 'Unknown Token'),
                    'volume_24h_usd': token.get('volume_24h_usd', token.get('volume_24h', 0)),
                    'market_cap': token.get('market_cap', 0),
                    'source': token.get('source', 'birdeye_api')
                }
                if normalized_token['address']:  # Only include tokens with addresses
                    normalized_tokens.append(normalized_token)
            
            fetch_time = time.time() - start_time
            self.logger.info(f"✅ Birdeye trending fetch completed in {fetch_time:.2f}s, got {len(normalized_tokens)} tokens")
            
            return normalized_tokens
            
        except Exception as e:
            self.logger.error(f"Error fetching Birdeye trending: {e}")
            return self._get_sample_birdeye_trending()
    
    def analyze_overlap(self, rugcheck_tokens: List[Dict], birdeye_tokens: List[Dict]) -> Dict[str, Any]:
        """Analyze overlap between RugCheck and Birdeye trending tokens"""
        
        # Create address sets for comparison
        rugcheck_addresses = {token['address'] for token in rugcheck_tokens if token['address']}
        birdeye_addresses = {token['address'] for token in birdeye_tokens if token['address']}
        
        # Find overlapping addresses
        overlap_addresses = rugcheck_addresses.intersection(birdeye_addresses)
        
        # Categorize tokens
        overlap_tokens = []
        rugcheck_only = []
        birdeye_only = []
        
        # Get overlap tokens (from RugCheck perspective)
        for token in rugcheck_tokens:
            if token['address'] in overlap_addresses:
                overlap_tokens.append(token)
            else:
                rugcheck_only.append(token)
        
        # Get Birdeye-only tokens
        for token in birdeye_tokens:
            if token['address'] not in overlap_addresses:
                birdeye_only.append(token)
        
        return {
            'overlap': overlap_tokens,
            'rugcheck_only': rugcheck_only,
            'birdeye_only': birdeye_only,
            'overlap_count': len(overlap_tokens),
            'rugcheck_unique': len(rugcheck_only),
            'birdeye_unique': len(birdeye_only)
        }
    
    async def analyze_token_quality(self, all_tokens: List[Dict]) -> Dict[str, Any]:
        """Analyze the quality of tokens from both sources"""
        
        self.logger.info(f"🔍 Analyzing quality of tokens from both sources...")
        
        # Get unique addresses
        unique_addresses = list({token['address'] for token in all_tokens if token['address']})
        
        if not unique_addresses:
            return {'quality_by_source': {}, 'security_results': {}, 'total_analyzed': 0}
        
        # Run security analysis
        self.logger.info(f"Running security analysis on {len(unique_addresses)} unique tokens...")
        security_results = await self.rugcheck.batch_analyze_tokens(unique_addresses)
        
        # Analyze quality by source
        quality_by_source = {}
        
        for source in ['rugcheck_trending', 'birdeye_api', 'birdeye_sample']:
            source_tokens = [token for token in all_tokens if token.get('source') == source]
            if not source_tokens:
                continue
            
            source_addresses = [token['address'] for token in source_tokens if token['address']]
            
            # Calculate quality metrics
            safe_count = 0
            risky_count = 0
            unknown_count = 0
            total_score = 0
            scored_count = 0
            
            for address in source_addresses:
                if address in security_results:
                    result = security_results[address]
                    if result.is_healthy:
                        safe_count += 1
                    else:
                        risky_count += 1
                    
                    if result.score is not None:
                        total_score += result.score
                        scored_count += 1
                else:
                    unknown_count += 1
            
            total_tokens = len(source_addresses)
            quality_by_source[source] = {
                'token_count': total_tokens,
                'safe_tokens': safe_count,
                'risky_tokens': risky_count,
                'unknown_tokens': unknown_count,
                'safety_rate': (safe_count / total_tokens) * 100 if total_tokens else 0,
                'average_score': total_score / scored_count if scored_count > 0 else None
            }
        
        return {
            'quality_by_source': quality_by_source,
            'security_results': security_results,
            'total_analyzed': len(unique_addresses)
        }
    
    def print_comparison_results(self, comparison: TrendingComparison):
        """Print detailed comparison results"""
        
        print(f"\n🔥 RUGCHECK vs BIRDEYE TRENDING COMPARISON")
        print("=" * 80)
        print("Based on RugCheck API: https://api.rugcheck.xyz/swagger/index.html#/")
        
        # Basic statistics
        print(f"\n📊 BASIC STATISTICS:")
        print(f"  RugCheck trending tokens: {len(comparison.rugcheck_tokens)} (RugCheck /stats/trending returns exactly 10)")
        print(f"  Birdeye trending tokens: {len(comparison.birdeye_tokens)}")
        print(f"  Overlapping tokens: {len(comparison.overlap_tokens)}")
        print(f"  RugCheck unique: {len(comparison.rugcheck_only)}")
        print(f"  Birdeye unique: {len(comparison.birdeye_only)}")
        
        # Overlap analysis
        overlap_percentage = (len(comparison.overlap_tokens) / len(comparison.rugcheck_tokens)) * 100 if comparison.rugcheck_tokens else 0
        print(f"\n🔄 OVERLAP ANALYSIS:")
        print(f"  Overlap rate: {overlap_percentage:.1f}% ({len(comparison.overlap_tokens)}/{len(comparison.rugcheck_tokens)} RugCheck tokens)")
        
        if overlap_percentage > 50:
            print(f"  ✅ High overlap - Both APIs show similar trending patterns")
        elif overlap_percentage > 25:
            print(f"  ⚠️ Moderate overlap - Some alignment in trending detection") 
        else:
            print(f"  ❌ Low overlap - Different trending algorithms/criteria")
        
        # Quality analysis
        quality_analysis = comparison.quality_analysis
        print(f"\n🛡️ QUALITY COMPARISON:")
        
        for source, metrics in quality_analysis['quality_by_source'].items():
            if metrics['token_count'] == 0:
                continue
                
            source_name = {
                'rugcheck_trending': 'RugCheck Trending',
                'birdeye_api': 'Birdeye API',  
                'birdeye_sample': 'Birdeye Sample'
            }.get(source, source)
            
            print(f"\n  {source_name}:")
            print(f"    Total tokens: {metrics['token_count']}")
            print(f"    Safe tokens: {metrics['safe_tokens']} ({metrics['safety_rate']:.1f}%)")
            print(f"    Risky tokens: {metrics['risky_tokens']}")
            print(f"    Unknown tokens: {metrics['unknown_tokens']}")
            if metrics['average_score']:
                print(f"    Average score: {metrics['average_score']:.1f}")
        
        # Performance comparison
        print(f"\n⚡ API PERFORMANCE:")
        performance = comparison.api_performance
        print(f"  RugCheck API calls: {performance.get('rugcheck_calls', 0)} (1 trending + security analysis)")
        print(f"  Birdeye API calls: {performance.get('birdeye_calls', 0)}")
        print(f"  Total analysis time: {performance.get('total_time', 0):.2f}s")
        
        # Individual token details
        print(f"\n📋 OVERLAPPING TOKENS (High Confidence):")
        if comparison.overlap_tokens:
            for i, token in enumerate(comparison.overlap_tokens[:5], 1):
                symbol = token.get('symbol', 'UNKNOWN')
                name = token.get('name', 'Unknown')
                address = token['address'][:8] + "..." if token['address'] else "Unknown"
                
                # Get security info
                security_result = quality_analysis['security_results'].get(token['address'])
                if security_result:
                    risk_emoji = "✅" if security_result.is_healthy else "❌"
                    risk_level = security_result.risk_level.value
                else:
                    risk_emoji = "❓"
                    risk_level = "unknown"
                
                print(f"  {i}. {symbol:8} ({address}) - {risk_emoji} {risk_level}")
                print(f"     {name}")
                
                if security_result and not security_result.is_healthy and security_result.issues:
                    issues = security_result.issues[:2]
                    print(f"     Issues: {', '.join(issues)}")
                print()
        else:
            print("  No overlapping tokens found")
        
        # RugCheck unique tokens
        print(f"\n🎯 RUGCHECK UNIQUE TOKENS ({len(comparison.rugcheck_only)}):")
        for i, token in enumerate(comparison.rugcheck_only[:3], 1):
            symbol = token.get('symbol', 'UNKNOWN')
            address = token['address'][:8] + "..." if token['address'] else "Unknown"
            security_result = quality_analysis['security_results'].get(token['address'])
            risk_emoji = "✅" if security_result and security_result.is_healthy else "❌" if security_result else "❓"
            print(f"  {i}. {symbol:8} ({address}) - {risk_emoji}")
        
        # Recommendations
        print(f"\n🎯 RECOMMENDATIONS:")
        
        rugcheck_quality = quality_analysis['quality_by_source'].get('rugcheck_trending', {})
        birdeye_quality = quality_analysis['quality_by_source'].get('birdeye_api', quality_analysis['quality_by_source'].get('birdeye_sample', {}))
        
        rugcheck_safety = rugcheck_quality.get('safety_rate', 0)
        birdeye_safety = birdeye_quality.get('safety_rate', 0)
        
        if rugcheck_safety > birdeye_safety:
            print(f"  ✅ RugCheck trending shows better quality filtering ({rugcheck_safety:.1f}% vs {birdeye_safety:.1f}% safe)")
            print(f"  💡 Use RugCheck trending as primary source, Birdeye as supplementary")
        elif birdeye_safety > rugcheck_safety:
            print(f"  ✅ Birdeye trending shows better quality ({birdeye_safety:.1f}% vs {rugcheck_safety:.1f}% safe)")
            print(f"  💡 Use Birdeye trending as primary source, with RugCheck validation")
        else:
            print(f"  ⚖️ Both sources show similar quality levels")
            print(f"  💡 Combine both sources for comprehensive coverage")
        
        print(f"\n🔗 INTEGRATION BENEFITS:")
        print(f"  • RugCheck: Curated 10-token list with inherent quality filtering")
        print(f"  • Birdeye: Larger selection with volume-based trending")
        print(f"  • Combined: Best of both worlds - quality + coverage") 
        print(f"  • Overlap validation: Tokens appearing in both sources are high-confidence")
        
        # API efficiency insights
        print(f"\n💡 API EFFICIENCY INSIGHTS:")
        print(f"  • RugCheck trending: Fixed 10 tokens - predictable payload size")
        print(f"  • Rapid processing: Small dataset enables frequent polling")
        print(f"  • Quality over quantity: Pre-filtered for better success rates")
        print(f"  • Perfect for real-time integration with your existing batch API patterns")
    
    async def run_comparison(self):
        """Run the complete trending comparison analysis"""
        
        print("🔥 RUGCHECK vs BIRDEYE TRENDING COMPARISON")
        print("=" * 70)
        print("Comparing RugCheck /stats/trending (exactly 10 tokens)")
        print("vs Birdeye trending endpoints to analyze quality and overlap")
        print("Reference: https://api.rugcheck.xyz/swagger/index.html#/")
        print()
        
        start_time = time.time()
        
        try:
            # Step 1: Fetch trending tokens from both sources
            print("📡 Fetching trending tokens from both APIs...")
            
            rugcheck_task = self.fetch_rugcheck_trending()
            birdeye_task = self.fetch_birdeye_trending(limit=15)
            
            rugcheck_tokens, birdeye_tokens = await asyncio.gather(rugcheck_task, birdeye_task)
            
            # Step 2: Analyze overlap
            print("🔄 Analyzing overlap between sources...")
            overlap_analysis = self.analyze_overlap(rugcheck_tokens, birdeye_tokens)
            
            # Step 3: Quality analysis
            print("🛡️ Analyzing token quality from both sources...")
            all_tokens = rugcheck_tokens + birdeye_tokens
            quality_analysis = await self.analyze_token_quality(all_tokens)
            
            # Step 4: Compile results
            total_time = time.time() - start_time
            
            comparison = TrendingComparison(
                rugcheck_tokens=rugcheck_tokens,
                birdeye_tokens=birdeye_tokens,
                overlap_tokens=overlap_analysis['overlap'],
                rugcheck_only=overlap_analysis['rugcheck_only'],
                birdeye_only=overlap_analysis['birdeye_only'],
                quality_analysis=quality_analysis,
                api_performance={
                    'rugcheck_calls': 1,  # Single trending call
                    'birdeye_calls': 1,   # Single trending call
                    'total_time': total_time
                }
            )
            
            # Step 5: Display results
            self.print_comparison_results(comparison)
            
            # Step 6: Save results
            timestamp = int(time.time())
            results_file = f"scripts/results/rugcheck_vs_birdeye_trending_{timestamp}.json"
            
            # Prepare serializable results
            serializable_results = {
                'timestamp': timestamp,
                'comparison_type': 'rugcheck_vs_birdeye_trending',
                'api_reference': 'https://api.rugcheck.xyz/swagger/index.html#/',
                'rugcheck_tokens': rugcheck_tokens,
                'birdeye_tokens': birdeye_tokens,
                'overlap_analysis': overlap_analysis,
                'quality_summary': {
                    source: {
                        'token_count': metrics['token_count'],
                        'safety_rate': metrics['safety_rate'],
                        'safe_tokens': metrics['safe_tokens'],
                        'risky_tokens': metrics['risky_tokens']
                    }
                    for source, metrics in quality_analysis['quality_by_source'].items()
                },
                'performance_metrics': comparison.api_performance,
                'recommendations': {
                    'total_overlap': len(comparison.overlap_tokens),
                    'overlap_percentage': (len(comparison.overlap_tokens) / len(rugcheck_tokens)) * 100 if rugcheck_tokens else 0,
                    'analysis_time': total_time,
                    'rugcheck_token_count': len(rugcheck_tokens),
                    'birdeye_token_count': len(birdeye_tokens)
                }
            }
            
            # Save to file 
            os.makedirs(os.path.dirname(results_file), exist_ok=True)
            with open(results_file, 'w') as f:
                json.dump(serializable_results, f, indent=2, default=str)
            
            print(f"\n💾 Results saved to: {results_file}")
            
        except Exception as e:
            self.logger.error(f"Comparison failed: {e}")
            import traceback
            traceback.print_exc()
            print(f"\n❌ Comparison failed: {e}")
        
        finally:
            # Cleanup
            if hasattr(self, 'birdeye_api') and self.birdeye_api is not None:
                await self.birdeye_api.close()


async def main():
    """Main comparison function"""
    comparison = RugCheckVsBirdeyeTrendingComparison()
    await comparison.run_comparison()


if __name__ == "__main__":
    asyncio.run(main()) 