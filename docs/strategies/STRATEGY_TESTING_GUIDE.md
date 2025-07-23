# Strategy Testing Guide

This guide explains how to test different token discovery strategies in the Early Token Monitor system. The system provides multiple approaches for testing strategies individually, in combination, and under various market conditions.

## Overview of Available Strategies

The system includes 5 main token discovery strategies:

1. **Volume Momentum Strategy** - Finds tokens with significant trading activity growth
2. **Recent Listings Strategy** - Identifies newly listed tokens gaining market attention  
3. **Price Momentum Strategy** - Detects strong price performance with volume confirmation
4. **Liquidity Growth Strategy** - Spots tokens gaining liquidity rapidly
5. **High Trading Activity Strategy** - Filters high trading activity relative to market cap

## Testing Approaches

### 1. Individual Strategy Testing

#### A. Unit Testing Individual Strategies

Run the comprehensive unit tests for strategy logic:

```bash
# Test all strategy implementations
python -m pytest tests/unit/test_token_discovery_strategies.py -v

# Test specific strategy
python -m pytest tests/unit/test_token_discovery_strategies.py::TestVolumeMomentumStrategy -v

# Test strategy scheduler
python -m pytest tests/unit/test_strategy_scheduler.py -v
```

#### B. Live Strategy Testing

Test individual strategies with real market data:

```python
#!/usr/bin/env python3
"""
Individual Strategy Test Script
"""
import asyncio
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from core.token_discovery_strategies import VolumeMomentumStrategy
from api.birdeye_connector import BirdeyeAPI
from core.config_manager import get_config_manager
from core.cache_manager import CacheManager
from services.rate_limiter_service import RateLimiterService
from services.logger_setup import LoggerSetup

async def test_volume_momentum_strategy():
    """Test Volume Momentum Strategy individually"""
    
    # Setup
    logger_setup = LoggerSetup("StrategyTest")
    logger = logger_setup.logger
    
    config = get_config_manager().get_config()
    cache_manager = CacheManager()
    rate_limiter = RateLimiterService()
    
    birdeye_api = BirdeyeAPI(
        config=config.get('BIRDEYE_API', {}),
        logger=logger,
        cache_manager=cache_manager,
        rate_limiter=rate_limiter
    )
    
    # Initialize strategy
    strategy = VolumeMomentumStrategy(logger=logger)
    
    print(f"Testing {strategy.name}")
    print(f"Description: {strategy.description}")
    print(f"API Parameters: {strategy.api_parameters}")
    
    # Execute strategy
    tokens = await strategy.execute(birdeye_api, scan_id="individual_test")
    
    print(f"\nResults: {len(tokens)} tokens found")
    
    # Display results
    for i, token in enumerate(tokens[:5]):  # Show first 5
        print(f"\n{i+1}. {token.get('symbol', 'N/A')} ({token.get('address', 'N/A')[:8]}...)")
        print(f"   Volume 24h: ${token.get('volume24h', 0):,.0f}")
        print(f"   Price Change 24h: {token.get('priceChange24h', 0):.2f}%")
        print(f"   Market Cap: ${token.get('marketCap', 0):,.0f}")
        print(f"   Consecutive Appearances: {token.get('strategy_data', {}).get('consecutive_appearances', 0)}")

if __name__ == "__main__":
    asyncio.run(test_volume_momentum_strategy())
```

### 2. Strategy Configuration Testing

#### A. Test Different Strategy Configurations

Create custom configurations and test their impact:

```python
#!/usr/bin/env python3
"""
Strategy Configuration Testing
"""
import asyncio
from core.strategy_scheduler import StrategyScheduler

async def test_strategy_configurations():
    """Test different strategy configurations"""
    
    # Configuration 1: Conservative settings
    conservative_config = {
        "VolumeMomentumStrategy": {
            "enabled": True,
            "min_consecutive_appearances": 5,  # More conservative
            "api_parameters": {
                "limit": 10,  # Fewer tokens
                "min_liquidity": 500000  # Higher liquidity requirement
            }
        },
        "RecentListingsStrategy": {
            "enabled": True,
            "min_consecutive_appearances": 3,
            "api_parameters": {
                "limit": 15,
                "min_age_days": 1  # Only very recent listings
            }
        }
    }
    
    # Configuration 2: Aggressive settings
    aggressive_config = {
        "VolumeMomentumStrategy": {
            "enabled": True,
            "min_consecutive_appearances": 2,  # Less conservative
            "api_parameters": {
                "limit": 50,  # More tokens
                "min_liquidity": 100000  # Lower liquidity requirement
            }
        },
        "PriceMomentumStrategy": {
            "enabled": True,
            "min_consecutive_appearances": 1,  # Very aggressive
            "api_parameters": {
                "limit": 30
            }
        }
    }
    
    # Test both configurations
    for config_name, config in [("Conservative", conservative_config), ("Aggressive", aggressive_config)]:
        print(f"\n{'='*60}")
        print(f"TESTING {config_name.upper()} CONFIGURATION")
        print(f"{'='*60}")
        
        scheduler = StrategyScheduler(
            birdeye_api=birdeye_api,  # Assume birdeye_api is initialized
            logger=logger,
            strategy_configs=config
        )
        
        # Force execution for testing
        with patch.object(scheduler, 'should_run_strategies', return_value=True):
            tokens = await scheduler.run_due_strategies(scan_id=f"{config_name.lower()}_test")
            
        print(f"Found {len(tokens)} tokens with {config_name.lower()} settings")
        
        # Analyze results
        if tokens:
            avg_consecutive = sum(t.get('strategy_data', {}).get('consecutive_appearances', 0) for t in tokens) / len(tokens)
            print(f"Average consecutive appearances: {avg_consecutive:.2f}")
            
            unique_strategies = set()
            for token in tokens:
                unique_strategies.add(token.get('strategy_data', {}).get('strategy', 'Unknown'))
            print(f"Strategies that found tokens: {', '.join(unique_strategies)}")

if __name__ == "__main__":
    asyncio.run(test_strategy_configurations())
```

### 3. A/B Testing Strategies

#### A. Compare Strategy Performance

```python
#!/usr/bin/env python3
"""
Strategy A/B Testing
"""
import asyncio
import json
from datetime import datetime, timedelta

async def ab_test_strategies():
    """Compare performance of different strategy combinations"""
    
    # Test Group A: Traditional momentum focus
    group_a_config = {
        "VolumeMomentumStrategy": {"enabled": True, "min_consecutive_appearances": 3},
        "PriceMomentumStrategy": {"enabled": True, "min_consecutive_appearances": 3},
        "RecentListingsStrategy": {"enabled": False}
    }
    
    # Test Group B: New listings focus  
    group_b_config = {
        "RecentListingsStrategy": {"enabled": True, "min_consecutive_appearances": 2},
        "LiquidityGrowthStrategy": {"enabled": True, "min_consecutive_appearances": 2},
        "VolumeMomentumStrategy": {"enabled": False}
    }
    
    results = {}
    
    for group_name, config in [("Group_A_Momentum", group_a_config), ("Group_B_Listings", group_b_config)]:
        print(f"\nTesting {group_name}...")
        
        scheduler = StrategyScheduler(
            birdeye_api=birdeye_api,
            logger=logger,
            strategy_configs=config
        )
        
        # Execute multiple times to get statistical significance
        group_results = []
        for run in range(3):  # 3 test runs
            print(f"  Run {run + 1}/3...")
            
            with patch.object(scheduler, 'should_run_strategies', return_value=True):
                tokens = await scheduler.run_due_strategies(scan_id=f"{group_name}_run_{run}")
                
            group_results.append({
                'run': run + 1,
                'tokens_found': len(tokens),
                'avg_score': sum(t.get('score', 0) for t in tokens) / len(tokens) if tokens else 0,
                'high_quality_tokens': len([t for t in tokens if t.get('score', 0) > 70])
            })
        
        results[group_name] = group_results
    
    # Compare results
    print(f"\n{'='*60}")
    print("A/B TEST RESULTS COMPARISON")
    print(f"{'='*60}")
    
    for group_name, group_results in results.items():
        avg_tokens = sum(r['tokens_found'] for r in group_results) / len(group_results)
        avg_score = sum(r['avg_score'] for r in group_results) / len(group_results)
        avg_high_quality = sum(r['high_quality_tokens'] for r in group_results) / len(group_results)
        
        print(f"\n{group_name}:")
        print(f"  Average tokens found: {avg_tokens:.1f}")
        print(f"  Average token score: {avg_score:.1f}")
        print(f"  Average high-quality tokens (>70 score): {avg_high_quality:.1f}")
    
    # Save results for further analysis
    with open(f"data/ab_test_results_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json", 'w') as f:
        json.dump(results, f, indent=2)

if __name__ == "__main__":
    asyncio.run(ab_test_strategies())
```

### 4. Market Condition Testing

#### A. Test Strategies Under Different Market Conditions

```python
#!/usr/bin/env python3
"""
Market Condition Strategy Testing
"""
import asyncio
from datetime import datetime, timedelta

async def test_market_conditions():
    """Test how strategies perform under different market conditions"""
    
    # Define market condition filters
    market_conditions = {
        "bull_market": {
            "min_market_cap_growth": 0.1,  # 10% growth
            "min_volume_growth": 0.2,       # 20% volume growth
            "description": "Bull market conditions - high growth"
        },
        "bear_market": {
            "max_market_cap_growth": -0.05, # 5% decline
            "max_volume_decline": -0.1,      # 10% volume decline  
            "description": "Bear market conditions - declining metrics"
        },
        "sideways_market": {
            "max_market_cap_change": 0.05,  # ±5% change
            "max_volume_change": 0.1,        # ±10% volume change
            "description": "Sideways market conditions - low volatility"
        }
    }
    
    for condition_name, condition_params in market_conditions.items():
        print(f"\n{'='*60}")
        print(f"TESTING: {condition_params['description'].upper()}")
        print(f"{'='*60}")
        
        # Adjust strategy parameters based on market conditions
        if condition_name == "bull_market":
            # More aggressive in bull markets
            strategy_config = {
                "VolumeMomentumStrategy": {
                    "enabled": True,
                    "min_consecutive_appearances": 2,
                    "api_parameters": {"limit": 30}
                },
                "PriceMomentumStrategy": {
                    "enabled": True,
                    "min_consecutive_appearances": 2
                }
            }
        elif condition_name == "bear_market":
            # More conservative in bear markets
            strategy_config = {
                "LiquidityGrowthStrategy": {
                    "enabled": True,
                    "min_consecutive_appearances": 4,
                    "api_parameters": {"limit": 15, "min_liquidity": 1000000}
                },
                "HighTradingActivityStrategy": {
                    "enabled": True,
                    "min_consecutive_appearances": 4
                }
            }
        else:  # sideways_market
            # Balanced approach
            strategy_config = {
                "RecentListingsStrategy": {
                    "enabled": True,
                    "min_consecutive_appearances": 3
                },
                "VolumeMomentumStrategy": {
                    "enabled": True,
                    "min_consecutive_appearances": 3
                }
            }
        
        scheduler = StrategyScheduler(
            birdeye_api=birdeye_api,
            logger=logger,
            strategy_configs=strategy_config
        )
        
        with patch.object(scheduler, 'should_run_strategies', return_value=True):
            tokens = await scheduler.run_due_strategies(scan_id=f"{condition_name}_test")
        
        print(f"Tokens found: {len(tokens)}")
        
        if tokens:
            # Analyze token characteristics for this market condition
            avg_volume = sum(t.get('volume24h', 0) for t in tokens) / len(tokens)
            avg_price_change = sum(t.get('priceChange24h', 0) for t in tokens) / len(tokens)
            avg_market_cap = sum(t.get('marketCap', 0) for t in tokens) / len(tokens)
            
            print(f"Average 24h volume: ${avg_volume:,.0f}")
            print(f"Average 24h price change: {avg_price_change:.2f}%")
            print(f"Average market cap: ${avg_market_cap:,.0f}")

if __name__ == "__main__":
    asyncio.run(test_market_conditions())
```

### 5. Integration Testing

#### A. Full System Integration Test

Use the existing comprehensive test:

```bash
# Run full end-to-end test
python scripts/e2e_full_test.py

# Run integration tests
python -m pytest tests/integration/ -v

# Run batch integration tests
python scripts/test_batch_integration_performance.py
```

#### B. Strategy + Analysis Pipeline Test

```python
#!/usr/bin/env python3
"""
Complete Pipeline Testing
"""
import asyncio

async def test_complete_pipeline():
    """Test the complete strategy -> analysis -> scoring pipeline"""
    
    from services.early_token_detection import EarlyTokenDetector
    
    detector = EarlyTokenDetector()
    
    print("Testing complete pipeline...")
    
    # Step 1: Strategy discovery
    print("\n1. Running strategy discovery...")
    strategy_tokens = await detector.strategy_scheduler.run_due_strategies(scan_id="pipeline_test")
    print(f"   Strategies found: {len(strategy_tokens)} tokens")
    
    # Step 2: Full analysis
    print("\n2. Running full token analysis...")
    analyzed_tokens = await detector.discover_and_analyze()
    print(f"   Analysis complete: {len(analyzed_tokens)} tokens")
    
    # Step 3: Compare results
    print("\n3. Pipeline comparison:")
    strategy_addresses = {t.get('address') for t in strategy_tokens}
    analyzed_addresses = {t.get('token_address') for t in analyzed_tokens}
    
    overlap = strategy_addresses.intersection(analyzed_addresses)
    print(f"   Strategy tokens: {len(strategy_addresses)}")
    print(f"   Analyzed tokens: {len(analyzed_addresses)}")
    print(f"   Overlap: {len(overlap)} tokens")
    print(f"   Conversion rate: {len(overlap)/len(strategy_addresses)*100:.1f}%")

if __name__ == "__main__":
    asyncio.run(test_complete_pipeline())
```

### 6. Performance Testing

#### A. Strategy Performance Benchmarking

```python
#!/usr/bin/env python3
"""
Strategy Performance Benchmarking
"""
import asyncio
import time
from statistics import mean, stdev

async def benchmark_strategies():
    """Benchmark strategy execution performance"""
    
    strategies_to_test = [
        VolumeMomentumStrategy,
        RecentListingsStrategy,
        PriceMomentumStrategy,
        LiquidityGrowthStrategy,
        HighTradingActivityStrategy
    ]
    
    results = {}
    
    for strategy_class in strategies_to_test:
        strategy = strategy_class(logger=logger)
        
        print(f"\nBenchmarking {strategy.name}...")
        
        execution_times = []
        token_counts = []
        
        # Run multiple times for statistical significance
        for run in range(5):
            start_time = time.time()
            
            tokens = await strategy.execute(birdeye_api, scan_id=f"benchmark_run_{run}")
            
            end_time = time.time()
            execution_time = end_time - start_time
            
            execution_times.append(execution_time)
            token_counts.append(len(tokens))
            
            print(f"  Run {run + 1}: {execution_time:.2f}s, {len(tokens)} tokens")
        
        results[strategy.name] = {
            'avg_execution_time': mean(execution_times),
            'std_execution_time': stdev(execution_times) if len(execution_times) > 1 else 0,
            'avg_tokens_found': mean(token_counts),
            'std_tokens_found': stdev(token_counts) if len(token_counts) > 1 else 0
        }
    
    # Display benchmark results
    print(f"\n{'='*80}")
    print("STRATEGY PERFORMANCE BENCHMARK RESULTS")
    print(f"{'='*80}")
    
    for strategy_name, metrics in results.items():
        print(f"\n{strategy_name}:")
        print(f"  Execution Time: {metrics['avg_execution_time']:.2f}s ± {metrics['std_execution_time']:.2f}s")
        print(f"  Tokens Found: {metrics['avg_tokens_found']:.1f} ± {metrics['std_tokens_found']:.1f}")
        print(f"  Tokens/Second: {metrics['avg_tokens_found']/metrics['avg_execution_time']:.2f}")

if __name__ == "__main__":
    asyncio.run(benchmark_strategies())
```

### 7. Historical Backtesting

#### A. Strategy Backtesting Framework

```python
#!/usr/bin/env python3
"""
Strategy Backtesting
"""
import asyncio
from datetime import datetime, timedelta

async def backtest_strategies():
    """Backtest strategies against historical data"""
    
    # This would require historical data - implement based on your data availability
    print("Backtesting strategies against historical performance...")
    
    # Example framework:
    # 1. Load historical token performance data
    # 2. Simulate strategy execution at different time points
    # 3. Track which tokens the strategies would have selected
    # 4. Measure actual performance of selected tokens
    # 5. Calculate strategy success rates and ROI
    
    # Placeholder implementation
    backtest_periods = [
        datetime.now() - timedelta(days=7),
        datetime.now() - timedelta(days=14),
        datetime.now() - timedelta(days=30)
    ]
    
    for period in backtest_periods:
        print(f"\nBacktesting period: {period.strftime('%Y-%m-%d')} to now")
        # Implementation would go here
        pass

if __name__ == "__main__":
    asyncio.run(backtest_strategies())
```

## Quick Testing Commands

### Run Existing Tests

```bash
# Unit tests for strategies
python -m pytest tests/unit/test_token_discovery_strategies.py -v

# Integration tests
python -m pytest tests/integration/ -v

# Smoke test
python scripts/e2e_smoke_test.py

# Enhanced scoring test
python scripts/test_enhanced_scoring.py

# Full end-to-end test
python scripts/e2e_full_test.py
```

### Configuration Testing

```bash
# Test with different configurations
cp config/config.example.yaml config/config.test.yaml
# Edit config.test.yaml with your test settings
CONFIG_FILE=config.test.yaml python scripts/e2e_smoke_test.py
```

### Strategy-Specific Testing

```bash
# Test individual strategies
python -c "
import asyncio
from core.token_discovery_strategies import VolumeMomentumStrategy
# ... (strategy testing code)
"
```

## Best Practices for Strategy Testing

1. **Test in Isolation**: Test each strategy individually before combining
2. **Use Mock Data**: Create mock data for consistent testing
3. **Test Edge Cases**: Test with extreme market conditions
4. **Performance Testing**: Monitor execution times and resource usage
5. **A/B Testing**: Compare different configurations systematically
6. **Document Results**: Keep detailed records of test results
7. **Continuous Testing**: Set up automated testing pipelines

## Monitoring Strategy Performance

The system includes built-in performance monitoring:

```python
# Get strategy performance metrics
scheduler = StrategyScheduler(...)
metrics = scheduler.get_strategy_performance_metrics()

# Get status report
status = scheduler.get_status_report()

# Get promising tokens across all strategies
promising = scheduler.get_all_promising_tokens()
```

This comprehensive testing approach allows you to validate strategy performance, optimize configurations, and ensure robust token discovery across different market conditions.