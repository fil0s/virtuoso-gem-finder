#!/usr/bin/env python3
"""
Strategy Configuration Testing Script

This script demonstrates how to test different token discovery strategies
with various configurations to optimize performance.
"""

import asyncio
import sys
import json
import time
from pathlib import Path
from datetime import datetime
from unittest.mock import patch

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from core.token_discovery_strategies import (
    VolumeMomentumStrategy,
    RecentListingsStrategy, 
    PriceMomentumStrategy,
    LiquidityGrowthStrategy,
    HighTradingActivityStrategy
)
from core.strategy_scheduler import StrategyScheduler
from api.birdeye_connector import BirdeyeAPI
from core.config_manager import get_config_manager
from core.cache_manager import CacheManager
from services.rate_limiter_service import RateLimiterService
from services.logger_setup import LoggerSetup


class StrategyTester:
    """Test different strategy configurations"""
    
    def __init__(self):
        """Initialize the strategy tester"""
        self.logger_setup = LoggerSetup("StrategyTester")
        self.logger = self.logger_setup.logger
        
        # Initialize API components
        config = get_config_manager().get_config()
        self.cache_manager = CacheManager()
        self.rate_limiter = RateLimiterService()
        
        self.birdeye_api = BirdeyeAPI(
            config=config.get('BIRDEYE_API', {}),
            logger=self.logger,
            cache_manager=self.cache_manager,
            rate_limiter=self.rate_limiter
        )
        
        self.results = {}
    
    async def test_individual_strategy(self, strategy_class, custom_config=None):
        """Test an individual strategy"""
        
        strategy_name = strategy_class.__name__
        self.logger.info(f"Testing individual strategy: {strategy_name}")
        
        # Initialize strategy
        strategy = strategy_class(logger=self.logger)
        
        # Apply custom configuration if provided
        if custom_config:
            if 'api_parameters' in custom_config:
                strategy.api_parameters.update(custom_config['api_parameters'])
            if 'min_consecutive_appearances' in custom_config:
                strategy.min_consecutive_appearances = custom_config['min_consecutive_appearances']
        
        print(f"\n{'='*60}")
        print(f"TESTING: {strategy.name}")
        print(f"{'='*60}")
        print(f"Description: {strategy.description}")
        print(f"API Parameters: {strategy.api_parameters}")
        print(f"Min Consecutive Appearances: {strategy.min_consecutive_appearances}")
        
        # Execute strategy
        start_time = time.time()
        tokens = await strategy.execute(self.birdeye_api, scan_id=f"individual_test_{strategy_name}")
        execution_time = time.time() - start_time
        
        print(f"\nResults:")
        print(f"  Execution Time: {execution_time:.2f} seconds")
        print(f"  Tokens Found: {len(tokens)}")
        
        if tokens:
            # Analyze token characteristics
            avg_volume = sum(t.get('volume24h', 0) for t in tokens) / len(tokens)
            avg_price_change = sum(t.get('priceChange24h', 0) for t in tokens) / len(tokens)
            avg_market_cap = sum(t.get('marketCap', 0) for t in tokens) / len(tokens)
            avg_consecutive = sum(t.get('strategy_data', {}).get('consecutive_appearances', 0) for t in tokens) / len(tokens)
            
            print(f"  Average 24h Volume: ${avg_volume:,.0f}")
            print(f"  Average 24h Price Change: {avg_price_change:.2f}%")
            print(f"  Average Market Cap: ${avg_market_cap:,.0f}")
            print(f"  Average Consecutive Appearances: {avg_consecutive:.1f}")
            
            # Show top 3 tokens
            print(f"\nTop 3 tokens:")
            for i, token in enumerate(tokens[:3]):
                print(f"  {i+1}. {token.get('symbol', 'N/A')} - ${token.get('volume24h', 0):,.0f} volume, {token.get('priceChange24h', 0):.1f}% change")
        
        # Store results
        self.results[strategy_name] = {
            'execution_time': execution_time,
            'tokens_found': len(tokens),
            'config': custom_config or {},
            'tokens': tokens[:10] if tokens else []  # Store first 10 for analysis
        }
        
        return tokens
    
    async def test_strategy_combinations(self):
        """Test different strategy combinations"""
        
        print(f"\n{'='*80}")
        print("TESTING STRATEGY COMBINATIONS")
        print(f"{'='*80}")
        
        # Define test configurations
        configurations = {
            "Conservative": {
                "VolumeMomentumStrategy": {
                    "enabled": True,
                    "min_consecutive_appearances": 4,
                    "api_parameters": {"limit": 15, "min_liquidity": 500000}
                },
                "LiquidityGrowthStrategy": {
                    "enabled": True,
                    "min_consecutive_appearances": 4,
                    "api_parameters": {"limit": 15}
                }
            },
            "Aggressive": {
                "VolumeMomentumStrategy": {
                    "enabled": True,
                    "min_consecutive_appearances": 2,
                    "api_parameters": {"limit": 30, "min_liquidity": 100000}
                },
                "PriceMomentumStrategy": {
                    "enabled": True,
                    "min_consecutive_appearances": 2,
                    "api_parameters": {"limit": 25}
                },
                "RecentListingsStrategy": {
                    "enabled": True,
                    "min_consecutive_appearances": 1,
                    "api_parameters": {"limit": 20}
                }
            },
            "Balanced": {
                "VolumeMomentumStrategy": {
                    "enabled": True,
                    "min_consecutive_appearances": 3,
                    "api_parameters": {"limit": 20}
                },
                "RecentListingsStrategy": {
                    "enabled": True,
                    "min_consecutive_appearances": 3,
                    "api_parameters": {"limit": 20}
                },
                "LiquidityGrowthStrategy": {
                    "enabled": True,
                    "min_consecutive_appearances": 3,
                    "api_parameters": {"limit": 15}
                }
            }
        }
        
        combination_results = {}
        
        for config_name, config in configurations.items():
            print(f"\n{'-'*50}")
            print(f"Testing {config_name} Configuration")
            print(f"{'-'*50}")
            
            # Initialize scheduler with configuration
            scheduler = StrategyScheduler(
                birdeye_api=self.birdeye_api,
                logger=self.logger,
                strategy_configs=config
            )
            
            # Force execution for testing
            with patch.object(scheduler, 'should_run_strategies', return_value=True):
                start_time = time.time()
                tokens = await scheduler.run_due_strategies(scan_id=f"{config_name.lower()}_test")
                execution_time = time.time() - start_time
            
            print(f"Results for {config_name}:")
            print(f"  Execution Time: {execution_time:.2f} seconds")
            print(f"  Total Tokens Found: {len(tokens)}")
            print(f"  Active Strategies: {len(scheduler.strategies)}")
            
            if tokens:
                # Analyze strategy distribution
                strategy_distribution = {}
                for token in tokens:
                    strategy = token.get('strategy_data', {}).get('strategy', 'Unknown')
                    strategy_distribution[strategy] = strategy_distribution.get(strategy, 0) + 1
                
                print(f"  Strategy Distribution:")
                for strategy, count in strategy_distribution.items():
                    print(f"    {strategy}: {count} tokens")
                
                # Quality metrics
                high_quality_tokens = len([t for t in tokens if t.get('strategy_data', {}).get('consecutive_appearances', 0) >= 3])
                avg_consecutive = sum(t.get('strategy_data', {}).get('consecutive_appearances', 0) for t in tokens) / len(tokens)
                
                print(f"  High Quality Tokens (≥3 appearances): {high_quality_tokens}")
                print(f"  Average Consecutive Appearances: {avg_consecutive:.1f}")
            
            combination_results[config_name] = {
                'execution_time': execution_time,
                'tokens_found': len(tokens),
                'strategies_used': len(scheduler.strategies),
                'tokens': tokens[:5] if tokens else []  # Store first 5 for comparison
            }
        
        self.results['combinations'] = combination_results
        return combination_results
    
    async def test_parameter_sensitivity(self):
        """Test sensitivity to different parameters"""
        
        print(f"\n{'='*80}")
        print("TESTING PARAMETER SENSITIVITY")
        print(f"{'='*80}")
        
        # Test different min_consecutive_appearances values
        consecutive_values = [1, 2, 3, 4, 5]
        
        print(f"\nTesting min_consecutive_appearances sensitivity...")
        
        consecutive_results = {}
        
        for consecutive in consecutive_values:
            print(f"\nTesting with min_consecutive_appearances = {consecutive}")
            
            config = {
                "VolumeMomentumStrategy": {
                    "enabled": True,
                    "min_consecutive_appearances": consecutive,
                    "api_parameters": {"limit": 20}
                }
            }
            
            scheduler = StrategyScheduler(
                birdeye_api=self.birdeye_api,
                logger=self.logger,
                strategy_configs=config
            )
            
            with patch.object(scheduler, 'should_run_strategies', return_value=True):
                tokens = await scheduler.run_due_strategies(scan_id=f"consecutive_{consecutive}_test")
            
            print(f"  Tokens found: {len(tokens)}")
            
            consecutive_results[consecutive] = len(tokens)
        
        print(f"\nConsecutive Appearances Sensitivity Results:")
        for consecutive, count in consecutive_results.items():
            print(f"  {consecutive} appearances: {count} tokens")
        
        # Test different limit values
        limit_values = [10, 20, 30, 50]
        
        print(f"\nTesting API limit sensitivity...")
        
        limit_results = {}
        
        for limit in limit_values:
            print(f"\nTesting with limit = {limit}")
            
            config = {
                "VolumeMomentumStrategy": {
                    "enabled": True,
                    "min_consecutive_appearances": 3,
                    "api_parameters": {"limit": limit}
                }
            }
            
            scheduler = StrategyScheduler(
                birdeye_api=self.birdeye_api,
                logger=self.logger,
                strategy_configs=config
            )
            
            with patch.object(scheduler, 'should_run_strategies', return_value=True):
                start_time = time.time()
                tokens = await scheduler.run_due_strategies(scan_id=f"limit_{limit}_test")
                execution_time = time.time() - start_time
            
            print(f"  Tokens found: {len(tokens)}")
            print(f"  Execution time: {execution_time:.2f}s")
            
            limit_results[limit] = {
                'tokens_found': len(tokens),
                'execution_time': execution_time
            }
        
        print(f"\nAPI Limit Sensitivity Results:")
        for limit, results in limit_results.items():
            print(f"  Limit {limit}: {results['tokens_found']} tokens in {results['execution_time']:.2f}s")
        
        self.results['sensitivity'] = {
            'consecutive_appearances': consecutive_results,
            'api_limits': limit_results
        }
    
    async def performance_benchmark(self):
        """Benchmark strategy performance"""
        
        print(f"\n{'='*80}")
        print("PERFORMANCE BENCHMARK")
        print(f"{'='*80}")
        
        strategies_to_test = [
            (VolumeMomentumStrategy, {}),
            (RecentListingsStrategy, {}),
            (PriceMomentumStrategy, {}),
            (LiquidityGrowthStrategy, {}),
            (HighTradingActivityStrategy, {})
        ]
        
        benchmark_results = {}
        
        for strategy_class, config in strategies_to_test:
            strategy_name = strategy_class.__name__
            print(f"\nBenchmarking {strategy_name}...")
            
            execution_times = []
            token_counts = []
            
            # Run multiple times for statistical significance
            for run in range(3):
                print(f"  Run {run + 1}/3...")
                
                strategy = strategy_class(logger=self.logger)
                
                start_time = time.time()
                tokens = await strategy.execute(self.birdeye_api, scan_id=f"benchmark_{strategy_name}_{run}")
                end_time = time.time()
                
                execution_time = end_time - start_time
                execution_times.append(execution_time)
                token_counts.append(len(tokens))
                
                print(f"    {execution_time:.2f}s, {len(tokens)} tokens")
            
            avg_time = sum(execution_times) / len(execution_times)
            avg_tokens = sum(token_counts) / len(token_counts)
            
            benchmark_results[strategy_name] = {
                'avg_execution_time': avg_time,
                'avg_tokens_found': avg_tokens,
                'tokens_per_second': avg_tokens / avg_time if avg_time > 0 else 0
            }
            
            print(f"  Average: {avg_time:.2f}s, {avg_tokens:.1f} tokens, {avg_tokens/avg_time:.1f} tokens/sec")
        
        print(f"\n{'-'*50}")
        print("BENCHMARK SUMMARY")
        print(f"{'-'*50}")
        
        for strategy_name, metrics in benchmark_results.items():
            print(f"{strategy_name}:")
            print(f"  Avg Time: {metrics['avg_execution_time']:.2f}s")
            print(f"  Avg Tokens: {metrics['avg_tokens_found']:.1f}")
            print(f"  Efficiency: {metrics['tokens_per_second']:.1f} tokens/sec")
            print()
        
        self.results['benchmark'] = benchmark_results
    
    def save_results(self):
        """Save test results to file"""
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        results_file = Path(f"data/strategy_test_results_{timestamp}.json")
        results_file.parent.mkdir(parents=True, exist_ok=True)
        
        with open(results_file, 'w') as f:
            json.dump(self.results, f, indent=2, default=str)
        
        print(f"\nResults saved to: {results_file}")
        return results_file
    
    def print_summary(self):
        """Print a summary of all test results"""
        
        print(f"\n{'='*80}")
        print("STRATEGY TESTING SUMMARY")
        print(f"{'='*80}")
        
        if 'combinations' in self.results:
            print(f"\nStrategy Combination Results:")
            for config_name, results in self.results['combinations'].items():
                print(f"  {config_name}: {results['tokens_found']} tokens in {results['execution_time']:.2f}s")
        
        if 'benchmark' in self.results:
            print(f"\nPerformance Benchmark:")
            sorted_strategies = sorted(
                self.results['benchmark'].items(),
                key=lambda x: x[1]['tokens_per_second'],
                reverse=True
            )
            for strategy_name, metrics in sorted_strategies:
                print(f"  {strategy_name}: {metrics['tokens_per_second']:.1f} tokens/sec")
        
        if 'sensitivity' in self.results:
            print(f"\nParameter Sensitivity:")
            if 'consecutive_appearances' in self.results['sensitivity']:
                consecutive_data = self.results['sensitivity']['consecutive_appearances']
                best_consecutive = max(consecutive_data.items(), key=lambda x: x[1])
                print(f"  Best min_consecutive_appearances: {best_consecutive[0]} ({best_consecutive[1]} tokens)")


async def main():
    """Main testing function"""
    
    print("🧪 Starting Strategy Configuration Testing...")
    
    tester = StrategyTester()
    
    try:
        # Test individual strategies with default configurations
        print("\n1. Testing individual strategies...")
        await tester.test_individual_strategy(VolumeMomentumStrategy)
        await tester.test_individual_strategy(RecentListingsStrategy)
        
        # Test strategy combinations
        print("\n2. Testing strategy combinations...")
        await tester.test_strategy_combinations()
        
        # Test parameter sensitivity
        print("\n3. Testing parameter sensitivity...")
        await tester.test_parameter_sensitivity()
        
        # Performance benchmark
        print("\n4. Running performance benchmark...")
        await tester.performance_benchmark()
        
        # Print summary and save results
        tester.print_summary()
        results_file = tester.save_results()
        
        print(f"\n✅ Strategy testing completed successfully!")
        print(f"📊 Detailed results saved to: {results_file}")
        
    except Exception as e:
        print(f"❌ Error during strategy testing: {e}")
        tester.logger.error(f"Strategy testing error: {e}")
        raise


if __name__ == "__main__":
    asyncio.run(main())