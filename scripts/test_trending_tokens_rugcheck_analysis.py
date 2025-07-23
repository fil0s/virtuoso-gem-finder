#!/usr/bin/env python3
"""
Trending Tokens vs RugCheck Analysis

This script fetches real trending tokens from Birdeye API and runs them through
comprehensive RugCheck analysis to demonstrate filtering effectiveness and potential
API call savings in a real-world scenario.
"""

import asyncio
import json
import time
import sys
import os
from pathlib import Path
from typing import List, Dict, Any, Optional
from dataclasses import dataclass

# Add project root to Python path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from api.rugcheck_connector import RugCheckConnector, RugRiskLevel
from api.birdeye_connector import BirdeyeAPI
from core.config_manager import ConfigManager
from utils.logger_setup import LoggerSetup


@dataclass
class AnalysisResult:
    """Container for analysis results"""
    total_tokens: int
    safe_tokens: int
    filtered_tokens: int
    api_calls_saved: int
    analysis_time: float
    token_breakdown: Dict[str, List[Dict]]
    savings_percentage: float


class TrendingTokensRugCheckAnalysis:
    
    def __init__(self):
        # Setup logging
        logger_setup = LoggerSetup("TrendingTokensAnalysis")
        self.logger = logger_setup.logger
        
        # Setup configuration
        self.config_manager = ConfigManager()
        config_dict = self.config_manager.get_config()
        
        # Initialize APIs
        self.rugcheck = RugCheckConnector(logger=self.logger)
        
        # Initialize Birdeye API (optional - will use sample data if not available)
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
                self.logger.warning("⚠️ Birdeye API configuration not found, will use sample tokens")
        except Exception as e:
            self.logger.warning(f"⚠️ Failed to initialize Birdeye API: {e}, will use sample tokens")
        
        # Analysis configuration
        self.max_tokens_to_analyze = 50  # Limit for demo purposes
        self.analysis_results = {}
    
    def _get_sample_trending_tokens(self, limit: int = 30) -> List[Dict[str, Any]]:
        """Get sample trending tokens for demo when Birdeye API is not available"""
        sample_tokens = [
            # Major tokens (likely safe)
            {"address": "EPjFWdd5AufqSSqeM2qN1xzybapC8G4wEGGkZwyTDt1v", "symbol": "USDC", "name": "USD Coin", "volume_24h_usd": 50000000, "market_cap": 28000000000},
            {"address": "So11111111111111111111111111111111111111112", "symbol": "SOL", "name": "Solana", "volume_24h_usd": 30000000, "market_cap": 45000000000},
            {"address": "mSoLzYCxHdYgdzU16g5QSh3i5K3z3KZK7ytfqcJm7So", "symbol": "mSOL", "name": "Marinade SOL", "volume_24h_usd": 5000000, "market_cap": 500000000},
            {"address": "7dHbWXmci3dT8UFYWYZweBLXgycu7Y3iL6trKn1Y7ARj", "symbol": "stSOL", "name": "Lido Staked SOL", "volume_24h_usd": 3000000, "market_cap": 400000000},
            {"address": "DezXAZ8z7PnrnRJjz3wXBoRgixCa6xjnB7YaB1pPB263", "symbol": "BONK", "name": "Bonk", "volume_24h_usd": 8000000, "market_cap": 800000000},
            
            # Mid-tier tokens (mixed quality)
            {"address": "4k3Dyjzvzp8eMZWUXbBCjEvwSkkk59S5iCNLY3QrkX6R", "symbol": "RAY", "name": "Raydium", "volume_24h_usd": 2000000, "market_cap": 200000000},
            {"address": "9n4nbM75f5Ui33ZbPYXn59EwSgE8CGsHtAeTH5YFeJ9E", "symbol": "BTC", "name": "Wrapped BTC (Solana)", "volume_24h_usd": 1500000, "market_cap": 150000000},
            {"address": "2FPyTwcZLUg1MDrwsyoP4D6s1tM7hAkHYRjkNb5w6Pxk", "symbol": "ETH", "name": "Wrapped ETH (Solana)", "volume_24h_usd": 1200000, "market_cap": 120000000},
            
            # Newer/riskier tokens (more likely to be filtered)
            {"address": "A1KLoBrKBde8Ty9qtNQUtq3C2ortoC3u7twggz7sEto6", "symbol": "NEWTOKEN1", "name": "Sample New Token 1", "volume_24h_usd": 500000, "market_cap": 5000000},
            {"address": "B2LoBrKBde8Ty9qtNQUtq3C2ortoC3u7twggz7sEto7", "symbol": "MEME1", "name": "Sample Meme Coin 1", "volume_24h_usd": 800000, "market_cap": 2000000},
            {"address": "C3LoBrKBde8Ty9qtNQUtq3C2ortoC3u7twggz7sEto8", "symbol": "SHITCOIN", "name": "Sample Risky Token", "volume_24h_usd": 300000, "market_cap": 1000000},
            {"address": "D4LoBrKBde8Ty9qtNQUtq3C2ortoC3u7twggz7sEto9", "symbol": "PUMP1", "name": "Pump Token Example", "volume_24h_usd": 1000000, "market_cap": 500000},
            {"address": "E5LoBrKBde8Ty9qtNQUtq3C2ortoC3u7twggz7sEt10", "symbol": "SCAM1", "name": "Potential Scam Token", "volume_24h_usd": 200000, "market_cap": 100000},
            
            # Additional sample tokens
            {"address": "F6LoBrKBde8Ty9qtNQUtq3C2ortoC3u7twggz7sEt11", "symbol": "DEFI1", "name": "DeFi Sample Token", "volume_24h_usd": 400000, "market_cap": 8000000},
            {"address": "G7LoBrKBde8Ty9qtNQUtq3C2ortoC3u7twggz7sEt12", "symbol": "NFT1", "name": "NFT Sample Token", "volume_24h_usd": 150000, "market_cap": 3000000},
            {"address": "H8LoBrKBde8Ty9qtNQUtq3C2ortoC3u7twggz7sEt13", "symbol": "GAME1", "name": "Gaming Sample Token", "volume_24h_usd": 600000, "market_cap": 12000000},
            {"address": "I9LoBrKBde8Ty9qtNQUtq3C2ortoC3u7twggz7sEt14", "symbol": "DAO1", "name": "DAO Sample Token", "volume_24h_usd": 350000, "market_cap": 6000000},
            {"address": "J1LoBrKBde8Ty9qtNQUtq3C2ortoC3u7twggz7sEt15", "symbol": "AI1", "name": "AI Sample Token", "volume_24h_usd": 750000, "market_cap": 15000000},
        ]
        
        # Add price change and liquidity estimates
        for token in sample_tokens:
            token['price_change_24h'] = (hash(token['address']) % 200) - 100  # Random -100% to +100%
            token['liquidity'] = token['market_cap'] * 0.05  # Estimate 5% of market cap as liquidity
        
        return sample_tokens[:limit]
    
    async def fetch_trending_tokens(self, limit: int = 50) -> List[Dict[str, Any]]:
        """Fetch trending tokens from Birdeye API or use sample data"""
        
        # If Birdeye API is not available, use sample trending tokens
        if not self.birdeye_api:
            self.logger.info("🔥 Using sample trending tokens for RugCheck analysis demo...")
            return self._get_sample_trending_tokens(limit)
        
        self.logger.info(f"🔥 Fetching top {limit} trending tokens from Birdeye...")
        
        try:
            # Try multiple endpoints to get trending tokens
            trending_data = None
            
            # Method 1: Try trending tokens endpoint
            try:
                trending_data = await self.birdeye_api.get_trending_tokens()
                if trending_data and isinstance(trending_data, list):
                    self.logger.info(f"✅ Got {len(trending_data)} tokens from trending endpoint")
                else:
                    trending_data = None
            except Exception as e:
                self.logger.warning(f"Trending endpoint failed: {e}")
            
            # Method 2: Fallback to token list with high volume
            if not trending_data:
                self.logger.info("Trying high-volume token list as fallback...")
                token_list_data = await self.birdeye_api.get_token_list(
                    sort_by="volume_24h_usd",
                    sort_type="desc",
                    min_volume_24h_usd=100000,  # High volume tokens
                    limit=limit
                )
                
                if token_list_data and 'data' in token_list_data:
                    if isinstance(token_list_data['data'], dict) and 'items' in token_list_data['data']:
                        trending_data = token_list_data['data']['items'][:limit]
                    elif isinstance(token_list_data['data'], list):
                        trending_data = token_list_data['data'][:limit]
                
                if trending_data:
                    self.logger.info(f"✅ Got {len(trending_data)} tokens from high-volume list")
            
            # Method 3: Last resort - use gainers/losers
            if not trending_data:
                self.logger.info("Trying gainers/losers as final fallback...")
                gainers_data = await self.birdeye_api.get_gainers_losers("24h")
                if gainers_data and isinstance(gainers_data, list):
                    # Convert trader data to token data format
                    trending_data = []
                    for trader in gainers_data[:limit]:
                        if 'address' in trader:
                            trending_data.append({
                                'address': trader['address'],
                                'symbol': trader.get('symbol', 'UNKNOWN'),
                                'name': trader.get('name', 'Unknown Token'),
                                'volume_24h_usd': trader.get('volume_24h', 0),
                                'price_change_24h': trader.get('pnl_24h', 0)
                            })
                    
                    if trending_data:
                        self.logger.info(f"✅ Got {len(trending_data)} tokens from gainers/losers")
            
            if not trending_data:
                # Create some test tokens if all methods fail
                self.logger.warning("All trending endpoints failed, using test tokens")
                trending_data = [
                    {"address": "EPjFWdd5AufqSSqeM2qN1xzybapC8G4wEGGkZwyTDt1v", "symbol": "USDC", "name": "USD Coin"},
                    {"address": "So11111111111111111111111111111111111111112", "symbol": "SOL", "name": "Solana"},
                    {"address": "mSoLzYCxHdYgdzU16g5QSh3i5K3z3KZK7ytfqcJm7So", "symbol": "mSOL", "name": "Marinade SOL"},
                ]
            
            # Ensure we have the required fields
            normalized_tokens = []
            for token in trending_data:
                if 'address' in token and token['address']:
                    normalized_token = {
                        'address': token['address'],
                        'symbol': token.get('symbol', 'UNKNOWN'),
                        'name': token.get('name', 'Unknown Token'),
                        'volume_24h_usd': token.get('volume_24h_usd', token.get('volume_24h', 0)),
                        'price_change_24h': token.get('price_change_24h', 0),
                        'market_cap': token.get('market_cap', 0),
                        'liquidity': token.get('liquidity', 0)
                    }
                    normalized_tokens.append(normalized_token)
            
            self.logger.info(f"🎯 Successfully fetched {len(normalized_tokens)} trending tokens for analysis")
            return normalized_tokens[:limit]
            
        except Exception as e:
            self.logger.error(f"Error fetching trending tokens: {e}")
            return []
    
    async def run_comprehensive_rugcheck_analysis(self, tokens: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Run comprehensive RugCheck analysis on tokens"""
        start_time = time.time()
        
        print(f"\n🛡️ RUGCHECK SECURITY ANALYSIS")
        print("=" * 60)
        print(f"Analyzing {len(tokens)} trending tokens for security risks...")
        
        # Extract token addresses
        token_addresses = [token['address'] for token in tokens]
        
        # Step 1: Basic security analysis
        print(f"\n📊 Step 1: Security Risk Assessment")
        security_results = await self.rugcheck.batch_analyze_tokens(token_addresses)
        
        # Step 2: Pre-validation for Birdeye analysis
        print(f"\n🔍 Step 2: Pre-Validation for Analysis Quality")
        validation_results = await self.rugcheck.pre_validate_for_birdeye_analysis(token_addresses)
        
        # Step 3: Quality-based routing
        print(f"\n🎯 Step 3: Quality-Based Routing")
        routing_results = self.rugcheck.route_tokens_by_quality(tokens, security_results, validation_results)
        
        analysis_time = time.time() - start_time
        
        # Compile results
        results = {
            'total_tokens': len(tokens),
            'analysis_time': analysis_time,
            'security_results': security_results,
            'validation_results': validation_results,
            'routing_results': routing_results,
            'token_details': tokens
        }
        
        return results
    
    def calculate_api_call_savings(self, routing_results: Dict[str, List[Dict]]) -> Dict[str, int]:
        """Calculate potential API call savings from routing"""
        
        # API call estimates per token analysis depth
        api_calls_per_token = {
            'premium_analysis': 8,    # Full analysis: OHLCV, transactions, holders, metadata, etc.
            'standard_analysis': 4,   # Basic analysis: price, volume, basic metrics
            'minimal_analysis': 2,    # Minimal: price and basic info only
            'skip_analysis': 0        # No API calls
        }
        
        actual_calls = 0
        naive_calls = 0
        
        for category, tokens in routing_results.items():
            actual_calls += len(tokens) * api_calls_per_token[category]
            naive_calls += len(tokens) * api_calls_per_token['premium_analysis']  # If we analyzed all fully
        
        saved_calls = naive_calls - actual_calls
        savings_percentage = (saved_calls / naive_calls * 100) if naive_calls > 0 else 0
        
        return {
            'naive_approach_calls': naive_calls,
            'optimized_approach_calls': actual_calls,
            'api_calls_saved': saved_calls,
            'savings_percentage': savings_percentage
        }
    
    def print_detailed_analysis(self, results: Dict[str, Any]):
        """Print detailed analysis results"""
        
        security_results = results['security_results']
        validation_results = results['validation_results']
        routing_results = results['routing_results']
        tokens = results['token_details']
        
        print(f"\n📋 DETAILED TOKEN ANALYSIS")
        print("=" * 80)
        
        # Security breakdown
        risk_counts = {}
        for result in security_results.values():
            risk_level = result.risk_level.value
            risk_counts[risk_level] = risk_counts.get(risk_level, 0) + 1
        
        print(f"\n🛡️ SECURITY RISK BREAKDOWN:")
        for risk_level, count in sorted(risk_counts.items()):
            percentage = (count / len(security_results) * 100) if security_results else 0
            print(f"  {risk_level.upper()}: {count} tokens ({percentage:.1f}%)")
        
        # Quality validation breakdown
        validation_counts = {
            'recommended': 0,
            'high_priority': 0,
            'medium_priority': 0,
            'low_priority': 0
        }
        
        for result in validation_results.values():
            if result.get('recommended_for_analysis'):
                validation_counts['recommended'] += 1
            
            priority = result.get('analysis_priority', 'low')
            validation_counts[f'{priority}_priority'] += 1
        
        print(f"\n🔍 QUALITY VALIDATION BREAKDOWN:")
        total_validated = len(validation_results)
        print(f"  Recommended for analysis: {validation_counts['recommended']}/{total_validated} ({validation_counts['recommended']/total_validated*100:.1f}%)")
        print(f"  High priority: {validation_counts['high_priority']} tokens")
        print(f"  Medium priority: {validation_counts['medium_priority']} tokens")
        print(f"  Low priority: {validation_counts['low_priority']} tokens")
        
        # Routing breakdown
        print(f"\n🎯 ROUTING RESULTS:")
        for category, token_list in routing_results.items():
            count = len(token_list)
            percentage = (count / len(tokens) * 100) if tokens else 0
            print(f"  {category.replace('_', ' ').title()}: {count} tokens ({percentage:.1f}%)")
        
        # API call savings
        savings = self.calculate_api_call_savings(routing_results)
        print(f"\n💰 API CALL SAVINGS ANALYSIS:")
        print(f"  Naive approach (full analysis for all): {savings['naive_approach_calls']} API calls")
        print(f"  Optimized approach (quality routing): {savings['optimized_approach_calls']} API calls")
        print(f"  API calls saved: {savings['api_calls_saved']} ({savings['savings_percentage']:.1f}% reduction)")
        
        # Individual token details
        print(f"\n📋 INDIVIDUAL TOKEN ANALYSIS:")
        print("-" * 80)
        
        for i, token in enumerate(tokens[:10]):  # Show first 10 tokens
            address = token['address']
            symbol = token.get('symbol', 'UNKNOWN')
            
            security_result = security_results.get(address)
            validation_result = validation_results.get(address, {})
            
            risk_level = security_result.risk_level.value if security_result else 'unknown'
            is_healthy = security_result.is_healthy if security_result else False
            recommended = validation_result.get('recommended_for_analysis', False)
            priority = validation_result.get('analysis_priority', 'unknown')
            
            # Determine which routing category this token fell into
            token_category = 'skip_analysis'  # default
            for category, category_tokens in routing_results.items():
                if any(t['address'] == address for t in category_tokens):
                    token_category = category
                    break
            
            status_emoji = "✅" if is_healthy else "❌"
            priority_emoji = {"high": "🏆", "medium": "📈", "low": "📊"}.get(priority, "❓")
            
            print(f"  {i+1:2d}. {symbol:8} ({address[:8]}...)")
            print(f"      Security: {status_emoji} {risk_level.upper()}")
            print(f"      Quality: {priority_emoji} {priority.upper()} priority")
            print(f"      Routing: → {token_category.replace('_', ' ').title()}")
            print(f"      Volume: ${token.get('volume_24h_usd', 0):,.0f}")
            
            if not is_healthy and security_result:
                issues = security_result.issues[:2]  # Show first 2 issues
                if issues:
                    print(f"      Issues: {', '.join(issues)}")
            
            print()
        
        if len(tokens) > 10:
            print(f"  ... and {len(tokens) - 10} more tokens")
    
    def print_summary_statistics(self, results: Dict[str, Any]):
        """Print summary statistics"""
        security_results = results['security_results']
        routing_results = results['routing_results']
        tokens = results['token_details']
        
        print(f"\n📊 SUMMARY STATISTICS")
        print("=" * 50)
        
        # Basic stats
        total_tokens = len(tokens)
        healthy_tokens = sum(1 for result in security_results.values() if result.is_healthy)
        filtered_tokens = total_tokens - healthy_tokens
        
        print(f"Total trending tokens analyzed: {total_tokens}")
        print(f"Tokens passing security checks: {healthy_tokens} ({healthy_tokens/total_tokens*100:.1f}%)")
        print(f"Tokens filtered out: {filtered_tokens} ({filtered_tokens/total_tokens*100:.1f}%)")
        
        # Routing stats
        premium_count = len(routing_results['premium_analysis'])
        standard_count = len(routing_results['standard_analysis'])
        minimal_count = len(routing_results['minimal_analysis'])
        skip_count = len(routing_results['skip_analysis'])
        
        print(f"\nResource allocation:")
        print(f"  🏆 Premium analysis: {premium_count} tokens (full Birdeye analysis)")
        print(f"  📈 Standard analysis: {standard_count} tokens (basic analysis)")
        print(f"  📊 Minimal analysis: {minimal_count} tokens (price only)")
        print(f"  🚫 Skip analysis: {skip_count} tokens (no API calls)")
        
        # Savings
        savings = self.calculate_api_call_savings(routing_results)
        print(f"\nCost optimization:")
        print(f"  API calls saved: {savings['api_calls_saved']} ({savings['savings_percentage']:.1f}%)")
        print(f"  Analysis time: {results['analysis_time']:.2f} seconds")
        
        # Quality insights
        high_risk_tokens = sum(1 for result in security_results.values() 
                              if result.risk_level in [RugRiskLevel.HIGH_RISK, RugRiskLevel.CRITICAL_RISK])
        
        print(f"\nRisk insights:")
        print(f"  High/Critical risk tokens: {high_risk_tokens}")
        print(f"  Potential rug pulls avoided: {high_risk_tokens}")
        print(f"  False positive reduction: {healthy_tokens/total_tokens*100:.1f}%")
    
    async def run_analysis(self, max_tokens: int = 30):
        """Run the complete trending tokens analysis"""
        
        print("🔥 TRENDING TOKENS vs RUGCHECK ANALYSIS")
        print("=" * 70)
        print("Testing real-world effectiveness of RugCheck filtering on trending tokens")
        print()
        
        try:
            # Step 1: Fetch trending tokens
            trending_tokens = await self.fetch_trending_tokens(limit=max_tokens)
            
            if not trending_tokens:
                print("❌ Failed to fetch trending tokens")
                return
            
            print(f"✅ Fetched {len(trending_tokens)} trending tokens")
            
            # Step 2: Run comprehensive analysis
            results = await self.run_comprehensive_rugcheck_analysis(trending_tokens)
            
            # Step 3: Display results
            self.print_detailed_analysis(results)
            self.print_summary_statistics(results)
            
            # Step 4: Save results
            timestamp = int(time.time())
            results_file = f"scripts/results/trending_rugcheck_analysis_{timestamp}.json"
            
            # Prepare serializable results
            serializable_results = {
                'timestamp': timestamp,
                'total_tokens': results['total_tokens'],
                'analysis_time': results['analysis_time'],
                'tokens': results['token_details'],
                'security_summary': {
                    address: {
                        'risk_level': result.risk_level.value,
                        'score': result.score,
                        'is_healthy': result.is_healthy,
                        'issues_count': len(result.issues),
                        'warnings_count': len(result.warnings)
                    }
                    for address, result in results['security_results'].items()
                },
                'routing_summary': {
                    category: len(tokens) 
                    for category, tokens in results['routing_results'].items()
                },
                'api_savings': self.calculate_api_call_savings(results['routing_results'])
            }
            
            # Save to file
            os.makedirs(os.path.dirname(results_file), exist_ok=True)
            with open(results_file, 'w') as f:
                json.dump(serializable_results, f, indent=2)
            
            print(f"\n💾 Results saved to: {results_file}")
            
            # Final recommendations
            print(f"\n🎯 RECOMMENDATIONS:")
            savings = self.calculate_api_call_savings(results['routing_results'])
            
            if savings['savings_percentage'] > 30:
                print(f"  ✅ Excellent optimization potential: {savings['savings_percentage']:.1f}% API call reduction")
            elif savings['savings_percentage'] > 15:
                print(f"  ✅ Good optimization potential: {savings['savings_percentage']:.1f}% API call reduction")
            else:
                print(f"  ⚠️ Limited optimization for this token set: {savings['savings_percentage']:.1f}% reduction")
            
            filtered_percentage = (len(results['routing_results']['skip_analysis']) / len(trending_tokens)) * 100
            if filtered_percentage > 20:
                print(f"  🛡️ Strong security filtering: {filtered_percentage:.1f}% of trending tokens filtered as risky")
            
            print(f"  💡 Implement quality routing to focus resources on {len(results['routing_results']['premium_analysis'])} high-quality tokens")
            
        except Exception as e:
            self.logger.error(f"Analysis failed: {e}")
            print(f"\n❌ Analysis failed: {e}")
        
        finally:
            # Cleanup
            if hasattr(self, 'birdeye_api') and self.birdeye_api is not None:
                await self.birdeye_api.close()


async def main():
    """Main analysis function"""
    analysis = TrendingTokensRugCheckAnalysis()
    await analysis.run_analysis(max_tokens=30)  # Analyze top 30 trending tokens


if __name__ == "__main__":
    asyncio.run(main()) 