#!/usr/bin/env python3
"""
Comprehensive Orca and Raydium Integration Test
Tests both connectors and demonstrates integration benefits
"""

import asyncio
import json
import time
from datetime import datetime
import sys
import os

# Add project root to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from api.orca_connector import OrcaConnector
from api.raydium_connector import RaydiumConnector
from api.cache_manager import EnhancedAPICacheManager
from utils.logger_setup import LoggerSetup

class OrcaRaydiumIntegrationTest:
    def __init__(self):
        logger_setup = LoggerSetup("orca_raydium_test")
        self.logger = logger_setup.logger
        self.cache_manager = EnhancedAPICacheManager()
        
        # Initialize connectors
        self.orca = OrcaConnector(
            enhanced_cache=self.cache_manager
        )
        self.raydium = RaydiumConnector(
            enhanced_cache=self.cache_manager
        )
        
        # Test tokens from your high-scoring list
        self.test_tokens = [
            "Dz9mQ9NzkBcCsuGPFJ3r1bS4wgqKMHBPiVuniW8Mbonk",  # USELESS
            "6p6xgHyF7AeE6TZkSmFsko444wqoP15icUSqi2jfGiPN",  # TRUMP
            "DtR4D9FtVoTX2569gaL837ZgrB6wNjj6tkmnX9Rdk9B2",  # aura
            "71Jvq4Epe2FCJ7JFSF7jLXdNk1Wy4Bhqd9iL6bEFELvg",  # GOR
            "J3NKxxXZcnNiMjKw9hYb2K4LUxgwB6t1FtPtQVsv3KFr",  # SPX
        ]
        
        self.results = {
            'timestamp': datetime.now().isoformat(),
            'orca_tests': {},
            'raydium_tests': {},
            'integration_analysis': {},
            'performance_metrics': {},
            'errors': []
        }

    async def test_orca_connector(self):
        """Test Orca API connector functionality"""
        print("\n🌊 Testing Orca Connector...")
        
        try:
            # Test 1: Get all pools
            print("  📊 Testing pool data retrieval...")
            pools = await self.orca.get_pools()
            self.results['orca_tests']['total_pools'] = len(pools) if pools else 0
            
            if pools:
                print(f"    ✅ Found {len(pools)} pools")
                # Analyze pool data
                pool_sample = pools[:5] if len(pools) >= 5 else pools
                self.results['orca_tests']['sample_pools'] = pool_sample
            else:
                print("    ❌ No pools found")
            
            # Test 2: Search for specific tokens
            print("  🔍 Testing token-specific searches...")
            token_results = {}
            
            for token in self.test_tokens:
                token_pools = await self.orca.get_token_pools(token)
                token_results[token] = {
                    'pools_found': len(token_pools) if token_pools else 0,
                    'pools': token_pools[:3] if token_pools else []  # First 3 pools
                }
                
                if token_pools:
                    print(f"    ✅ {token}: Found {len(token_pools)} pool(s)")
                else:
                    print(f"    ❌ {token}: No pools found")
            
            self.results['orca_tests']['token_searches'] = token_results
            
            # Test 3: Get trending pools
            print("  📈 Testing trending pools...")
            trending = await self.orca.get_trending_pools(min_volume_24h=1000)
            self.results['orca_tests']['trending_pools'] = {
                'count': len(trending) if trending else 0,
                'pools': trending[:5] if trending else []
            }
            
            if trending:
                print(f"    ✅ Found {len(trending)} trending pools")
            else:
                print("    ❌ No trending pools found")
                
        except Exception as e:
            error_msg = f"Orca connector test failed: {str(e)}"
            print(f"    ❌ {error_msg}")
            self.results['errors'].append(error_msg)

    async def test_raydium_connector(self):
        """Test Raydium API connector functionality"""
        print("\n⚡ Testing Raydium Connector...")
        
        try:
            # Test 1: Get pools (limited for testing)
            print("  📊 Testing pool data retrieval...")
            pools = await self.raydium.get_pools(limit=100)  # Limited for testing
            self.results['raydium_tests']['pools_retrieved'] = len(pools) if pools else 0
            
            if pools:
                print(f"    ✅ Retrieved {len(pools)} pools")
                # Analyze pool data
                pool_sample = pools[:5] if len(pools) >= 5 else pools
                self.results['raydium_tests']['sample_pools'] = pool_sample
            else:
                print("    ❌ No pools found")
            
            # Test 2: Get trading pairs
            print("  💱 Testing trading pairs...")
            pairs = await self.raydium.get_pairs(limit=50)  # Limited for testing
            self.results['raydium_tests']['pairs_retrieved'] = len(pairs) if pairs else 0
            
            if pairs:
                print(f"    ✅ Retrieved {len(pairs)} trading pairs")
                # Analyze high APY opportunities
                high_apy_pairs = [p for p in pairs if p.get('apy', 0) > 100]
                self.results['raydium_tests']['high_apy_opportunities'] = len(high_apy_pairs)
                print(f"    💰 Found {len(high_apy_pairs)} high APY opportunities (>100%)")
            else:
                print("    ❌ No trading pairs found")
            
            # Test 3: Search for specific tokens
            print("  🔍 Testing token-specific searches...")
            token_results = {}
            
            for token in self.test_tokens:
                token_pairs = await self.raydium.get_token_pairs(token)
                token_results[token] = {
                    'pairs_found': len(token_pairs) if token_pairs else 0,
                    'pairs': token_pairs[:3] if token_pairs else []  # First 3 pairs
                }
                
                if token_pairs:
                    print(f"    ✅ {token}: Found {len(token_pairs)} pair(s)")
                    # Check for high APY
                    high_apy = [p for p in token_pairs if p.get('apy', 0) > 50]
                    if high_apy:
                        print(f"      💎 High APY opportunities: {len(high_apy)}")
                else:
                    print(f"    ❌ {token}: No pairs found")
            
            self.results['raydium_tests']['token_searches'] = token_results
                
        except Exception as e:
            error_msg = f"Raydium connector test failed: {str(e)}"
            print(f"    ❌ {error_msg}")
            self.results['errors'].append(error_msg)

    async def test_integration_benefits(self):
        """Test how the integration enhances existing analysis"""
        print("\n🔗 Testing Integration Benefits...")
        
        try:
            # Test cross-platform data correlation
            print("  📊 Analyzing cross-platform data correlation...")
            
            correlation_data = {}
            for token in self.test_tokens[:3]:  # Test first 3 tokens
                print(f"    🔍 Analyzing {token}...")
                
                # Get data from both platforms
                orca_pools = await self.orca.get_token_pools(token)
                raydium_pairs = await self.raydium.get_token_pairs(token)
                
                token_analysis = {
                    'orca_presence': len(orca_pools) > 0 if orca_pools else False,
                    'raydium_presence': len(raydium_pairs) > 0 if raydium_pairs else False,
                    'orca_pools': len(orca_pools) if orca_pools else 0,
                    'raydium_pairs': len(raydium_pairs) if raydium_pairs else 0,
                    'total_dex_presence': (len(orca_pools) if orca_pools else 0) + (len(raydium_pairs) if raydium_pairs else 0)
                }
                
                # Calculate risk score based on DEX distribution
                if token_analysis['total_dex_presence'] == 0:
                    risk_level = "HIGH - No DEX presence"
                elif token_analysis['total_dex_presence'] == 1:
                    risk_level = "MEDIUM - Single DEX"
                else:
                    risk_level = "LOW - Multi-DEX presence"
                
                token_analysis['risk_assessment'] = risk_level
                correlation_data[token] = token_analysis
                
                print(f"      📈 DEX Presence: {token_analysis['total_dex_presence']} pools/pairs")
                print(f"      ⚠️  Risk Level: {risk_level}")
            
            self.results['integration_analysis']['cross_platform_correlation'] = correlation_data
            
            # Test liquidity quality assessment
            print("  💧 Testing liquidity quality assessment...")
            liquidity_analysis = await self.analyze_liquidity_quality()
            self.results['integration_analysis']['liquidity_quality'] = liquidity_analysis
            
        except Exception as e:
            error_msg = f"Integration benefits test failed: {str(e)}"
            print(f"    ❌ {error_msg}")
            self.results['errors'].append(error_msg)

    async def analyze_liquidity_quality(self):
        """Analyze liquidity quality across DEXes"""
        try:
            # Get trending pools from both platforms
            orca_trending = await self.orca.get_trending_pools(min_volume_24h=1000)
            raydium_pairs = await self.raydium.get_pairs(limit=50)
            
            liquidity_analysis = {
                'orca_avg_liquidity': 0,
                'raydium_avg_liquidity': 0,
                'high_liquidity_pools': 0,
                'yield_opportunities': 0
            }
            
            # Analyze Orca liquidity
            if orca_trending:
                orca_liquidities = [pool.get('liquidity', 0) for pool in orca_trending if pool.get('liquidity')]
                if orca_liquidities:
                    liquidity_analysis['orca_avg_liquidity'] = sum(orca_liquidities) / len(orca_liquidities)
                    liquidity_analysis['high_liquidity_pools'] += len([l for l in orca_liquidities if l > 100000])
            
            # Analyze Raydium liquidity and APY
            if raydium_pairs:
                raydium_liquidities = [pair.get('liquidity', 0) for pair in raydium_pairs if pair.get('liquidity')]
                if raydium_liquidities:
                    liquidity_analysis['raydium_avg_liquidity'] = sum(raydium_liquidities) / len(raydium_liquidities)
                    liquidity_analysis['high_liquidity_pools'] += len([l for l in raydium_liquidities if l > 100000])
                
                # Count yield opportunities
                high_apy_pairs = [pair for pair in raydium_pairs if pair.get('apy', 0) > 50]
                liquidity_analysis['yield_opportunities'] = len(high_apy_pairs)
            
            return liquidity_analysis
            
        except Exception as e:
            print(f"    ❌ Liquidity analysis failed: {str(e)}")
            return {}

    async def measure_performance(self):
        """Measure API performance and reliability"""
        print("\n⏱️  Measuring Performance...")
        
        performance_metrics = {
            'orca_response_times': [],
            'raydium_response_times': [],
            'success_rates': {},
            'api_call_stats': {}
        }
        
        # Test Orca performance
        print("  🌊 Testing Orca performance...")
        orca_times = []
        orca_successes = 0
        
        for i in range(3):  # 3 test calls
            try:
                start_time = time.time()
                pools = await self.orca.get_pools()
                end_time = time.time()
                
                response_time = end_time - start_time
                orca_times.append(response_time)
                
                if pools:
                    orca_successes += 1
                    
                print(f"    📊 Call {i+1}: {response_time:.2f}s")
                
            except Exception as e:
                print(f"    ❌ Call {i+1} failed: {str(e)}")
        
        performance_metrics['orca_response_times'] = orca_times
        performance_metrics['success_rates']['orca'] = orca_successes / 3
        
        # Test Raydium performance
        print("  ⚡ Testing Raydium performance...")
        raydium_times = []
        raydium_successes = 0
        
        for i in range(3):  # 3 test calls
            try:
                start_time = time.time()
                pairs = await self.raydium.get_pairs(limit=10)  # Small limit for performance test
                end_time = time.time()
                
                response_time = end_time - start_time
                raydium_times.append(response_time)
                
                if pairs:
                    raydium_successes += 1
                    
                print(f"    📊 Call {i+1}: {response_time:.2f}s")
                
            except Exception as e:
                print(f"    ❌ Call {i+1} failed: {str(e)}")
        
        performance_metrics['raydium_response_times'] = raydium_times
        performance_metrics['success_rates']['raydium'] = raydium_successes / 3
        
        # Get API call statistics
        performance_metrics['api_call_stats'] = {
            'orca': self.orca.get_api_call_statistics(),
            'raydium': self.raydium.get_api_call_statistics()
        }
        
        self.results['performance_metrics'] = performance_metrics

    def generate_summary_report(self):
        """Generate a comprehensive summary report"""
        print("\n" + "="*60)
        print("🎯 ORCA & RAYDIUM INTEGRATION TEST SUMMARY")
        print("="*60)
        
        # Orca Results
        print("\n🌊 ORCA CONNECTOR RESULTS:")
        orca_tests = self.results.get('orca_tests', {})
        print(f"  • Total Pools Found: {orca_tests.get('total_pools', 0)}")
        print(f"  • Trending Pools: {orca_tests.get('trending_pools', {}).get('count', 0)}")
        
        token_searches = orca_tests.get('token_searches', {})
        tokens_found = sum(1 for result in token_searches.values() if result.get('pools_found', 0) > 0)
        print(f"  • Test Tokens Found: {tokens_found}/{len(self.test_tokens)}")
        
        # Raydium Results
        print("\n⚡ RAYDIUM CONNECTOR RESULTS:")
        raydium_tests = self.results.get('raydium_tests', {})
        print(f"  • Pools Retrieved: {raydium_tests.get('pools_retrieved', 0)}")
        print(f"  • Trading Pairs: {raydium_tests.get('pairs_retrieved', 0)}")
        print(f"  • High APY Opportunities: {raydium_tests.get('high_apy_opportunities', 0)}")
        
        raydium_token_searches = raydium_tests.get('token_searches', {})
        raydium_tokens_found = sum(1 for result in raydium_token_searches.values() if result.get('pairs_found', 0) > 0)
        print(f"  • Test Tokens Found: {raydium_tokens_found}/{len(self.test_tokens)}")
        
        # Integration Analysis
        print("\n🔗 INTEGRATION BENEFITS:")
        integration = self.results.get('integration_analysis', {})
        correlation = integration.get('cross_platform_correlation', {})
        
        multi_dex_tokens = sum(1 for analysis in correlation.values() 
                              if analysis.get('total_dex_presence', 0) > 1)
        print(f"  • Multi-DEX Tokens: {multi_dex_tokens}/{len(correlation)}")
        
        liquidity = integration.get('liquidity_quality', {})
        print(f"  • High Liquidity Pools: {liquidity.get('high_liquidity_pools', 0)}")
        print(f"  • Yield Opportunities: {liquidity.get('yield_opportunities', 0)}")
        
        # Performance Metrics
        print("\n⏱️  PERFORMANCE METRICS:")
        performance = self.results.get('performance_metrics', {})
        
        orca_times = performance.get('orca_response_times', [])
        if orca_times:
            avg_orca_time = sum(orca_times) / len(orca_times)
            print(f"  • Orca Avg Response: {avg_orca_time:.2f}s")
        
        raydium_times = performance.get('raydium_response_times', [])
        if raydium_times:
            avg_raydium_time = sum(raydium_times) / len(raydium_times)
            print(f"  • Raydium Avg Response: {avg_raydium_time:.2f}s")
        
        success_rates = performance.get('success_rates', {})
        print(f"  • Orca Success Rate: {success_rates.get('orca', 0)*100:.1f}%")
        print(f"  • Raydium Success Rate: {success_rates.get('raydium', 0)*100:.1f}%")
        
        # Errors
        errors = self.results.get('errors', [])
        if errors:
            print(f"\n❌ ERRORS ENCOUNTERED: {len(errors)}")
            for error in errors:
                print(f"  • {error}")
        else:
            print(f"\n✅ NO ERRORS ENCOUNTERED")
        
        # Recommendations
        print("\n💡 RECOMMENDATIONS:")
        
        # Check if integration is beneficial
        total_tokens_found = tokens_found + raydium_tokens_found
        if total_tokens_found > 0:
            print("  ✅ Integration will enhance token discovery")
            print("  ✅ Direct DEX data provides valuable insights")
        else:
            print("  ⚠️  Limited token coverage - may need broader token testing")
        
        if liquidity.get('yield_opportunities', 0) > 0:
            print("  ✅ Yield opportunities detected - valuable for strategy")
        
        if multi_dex_tokens > 0:
            print("  ✅ Multi-DEX analysis will improve risk assessment")
        
        avg_response_time = (sum(orca_times + raydium_times) / len(orca_times + raydium_times)) if (orca_times + raydium_times) else 0
        if avg_response_time < 5.0:
            print("  ✅ Performance is acceptable for production")
        else:
            print("  ⚠️  Consider optimizing for better performance")
        
        print("\n" + "="*60)

    async def run_comprehensive_test(self):
        """Run all tests in sequence"""
        print("🚀 Starting Comprehensive Orca & Raydium Integration Test")
        print(f"📅 Timestamp: {self.results['timestamp']}")
        
        # Initialize sessions for connectors
        async with self.orca, self.raydium:
            # Run all test phases
            await self.test_orca_connector()
            await self.test_raydium_connector()
            await self.test_integration_benefits()
            await self.measure_performance()
        
        # Generate summary
        self.generate_summary_report()
        
        # Save detailed results
        results_file = f"scripts/results/orca_raydium_integration_test_{int(time.time())}.json"
        os.makedirs(os.path.dirname(results_file), exist_ok=True)
        
        with open(results_file, 'w') as f:
            json.dump(self.results, f, indent=2, default=str)
        
        print(f"\n📄 Detailed results saved to: {results_file}")
        
        return self.results

async def main():
    """Main test execution"""
    test = OrcaRaydiumIntegrationTest()
    results = await test.run_comprehensive_test()
    
    # Return success/failure based on results
    errors = results.get('errors', [])
    if len(errors) == 0:
        print("\n🎉 All tests completed successfully!")
        return 0
    else:
        print(f"\n⚠️  Tests completed with {len(errors)} error(s)")
        return 1

if __name__ == "__main__":
    import asyncio
    exit_code = asyncio.run(main())
    exit(exit_code) 