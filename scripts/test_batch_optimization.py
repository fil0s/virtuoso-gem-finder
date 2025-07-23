#!/usr/bin/env python3
"""
Test Batch API Optimization

This script tests the improved batch API usage in strategies and demonstrates
the cost savings achieved by using Birdeye's batch endpoints properly.
"""

import asyncio
import logging
import time
from pathlib import Path
import sys

# Add project root to path
sys.path.append(str(Path(__file__).parent.parent))

from api.birdeye_connector import BirdeyeAPI
from core.strategies.volume_momentum_strategy import VolumeMomentumStrategy
from core.strategies.high_trading_activity_strategy import HighTradingActivityStrategy
from core.strategies.recent_listings_strategy import RecentListingsStrategy
from services.logger_setup import LoggerSetup


class BatchOptimizationTester:
    """Test batch API optimization improvements."""
    
    def __init__(self):
        self.logger_setup = LoggerSetup("BatchOptimizationTest")
        self.logger = self.logger_setup.logger
        
        # Initialize Birdeye API
        self.birdeye_api = BirdeyeAPI(logger=self.logger)
        
        # Initialize strategies
        self.strategies = [
            VolumeMomentumStrategy(logger=self.logger),
            HighTradingActivityStrategy(logger=self.logger),
            RecentListingsStrategy(logger=self.logger)
        ]
    
    async def test_batch_optimization(self):
        """Test batch optimization across all strategies."""
        self.logger.info("🚀 Testing Batch API Optimization")
        
        total_results = {}
        overall_start_time = time.time()
        
        for strategy in self.strategies:
            self.logger.info(f"\n{'='*60}")
            self.logger.info(f"Testing Strategy: {strategy.name}")
            self.logger.info(f"{'='*60}")
            
            strategy_start_time = time.time()
            
            try:
                # Execute strategy with batch optimization
                tokens = await strategy.execute(self.birdeye_api, scan_id=f"batch_test_{int(time.time())}")
                
                strategy_execution_time = time.time() - strategy_start_time
                
                # Get cost optimization report
                cost_report = strategy.get_cost_optimization_report()
                
                # Log results
                self.logger.info(f"✅ Strategy completed in {strategy_execution_time:.2f}s")
                self.logger.info(f"📊 Tokens discovered: {len(tokens)}")
                self.logger.info(f"💰 Cost Efficiency: {cost_report['efficiency_grade']}")
                self.logger.info(f"📈 Batch Efficiency Ratio: {cost_report['cost_metrics']['batch_efficiency_ratio']:.2%}")
                self.logger.info(f"🔄 API Calls Used: {cost_report['cost_metrics']['total_api_calls']}")
                self.logger.info(f"💾 Estimated CU Saved: {cost_report['cost_metrics']['estimated_cu_saved']}")
                
                # Store results
                total_results[strategy.name] = {
                    'tokens_found': len(tokens),
                    'execution_time': strategy_execution_time,
                    'cost_report': cost_report,
                    'sample_tokens': tokens[:3] if tokens else []  # First 3 tokens as sample
                }
                
                # Show sample token with batch enrichment
                if tokens:
                    sample_token = tokens[0]
                    self.logger.info(f"\n📋 Sample Token Analysis:")
                    self.logger.info(f"   Symbol: {sample_token.get('symbol', 'N/A')}")
                    self.logger.info(f"   Address: {sample_token.get('address', 'N/A')[:12]}...")
                    self.logger.info(f"   Batch Enriched: {sample_token.get('batch_enriched', False)}")
                    
                    if sample_token.get('enrichment_sources'):
                        sources = sample_token['enrichment_sources']
                        self.logger.info(f"   Data Sources: Price={sources.get('price_data', False)}, "
                                       f"Meta={sources.get('metadata', False)}, "
                                       f"Trade={sources.get('trade_data', False)}")
                    
                    if sample_token.get('smart_money_detected'):
                        self.logger.info(f"   Smart Money: {sample_token.get('smart_money_level', 'N/A')} "
                                       f"(Score: {sample_token.get('smart_money_score', 0):.2f})")
                    
                    if sample_token.get('is_trending'):
                        self.logger.info(f"   Trending: Yes (Boost: {sample_token.get('trending_boost_applied', 1.0):.2f}x)")
                
            except Exception as e:
                self.logger.error(f"❌ Strategy {strategy.name} failed: {e}")
                total_results[strategy.name] = {
                    'error': str(e),
                    'execution_time': time.time() - strategy_start_time
                }
            
            # Brief pause between strategies
            await asyncio.sleep(1)
        
        # Overall summary
        total_execution_time = time.time() - overall_start_time
        self.logger.info(f"\n{'='*80}")
        self.logger.info(f"🎯 BATCH OPTIMIZATION TEST SUMMARY")
        self.logger.info(f"{'='*80}")
        
        total_tokens = sum(r.get('tokens_found', 0) for r in total_results.values())
        total_api_calls = sum(r.get('cost_report', {}).get('cost_metrics', {}).get('total_api_calls', 0) 
                             for r in total_results.values())
        total_cu_saved = sum(r.get('cost_report', {}).get('cost_metrics', {}).get('estimated_cu_saved', 0) 
                            for r in total_results.values())
        
        self.logger.info(f"⏱️  Total Execution Time: {total_execution_time:.2f}s")
        self.logger.info(f"🎯 Total Tokens Discovered: {total_tokens}")
        self.logger.info(f"📞 Total API Calls Used: {total_api_calls}")
        self.logger.info(f"💰 Total CU Saved: {total_cu_saved}")
        self.logger.info(f"🚀 Strategies with Batch APIs: {len([s for s in self.strategies if s.rate_limit_config['prefer_batch_apis']])}/{len(self.strategies)}")
        
        # Efficiency analysis
        efficient_strategies = [name for name, result in total_results.items() 
                              if result.get('cost_report', {}).get('efficiency_grade') in ['Excellent', 'Good']]
        
        self.logger.info(f"✅ Efficient Strategies: {len(efficient_strategies)}/{len(self.strategies)}")
        
        if efficient_strategies:
            self.logger.info(f"   📈 Efficient: {', '.join(efficient_strategies)}")
        
        # Rate limiting compliance
        avg_api_calls_per_strategy = total_api_calls / len(self.strategies) if self.strategies else 0
        self.logger.info(f"📊 Avg API Calls per Strategy: {avg_api_calls_per_strategy:.1f}")
        
        # Estimate rate limit compliance (assuming Starter tier: 15 rps)
        if avg_api_calls_per_strategy < 10:
            self.logger.info("✅ Rate Limit Compliance: EXCELLENT (well under limits)")
        elif avg_api_calls_per_strategy < 15:
            self.logger.info("✅ Rate Limit Compliance: GOOD (within limits)")
        else:
            self.logger.info("⚠️  Rate Limit Compliance: NEEDS ATTENTION (may exceed limits)")
        
        return total_results
    
    async def test_cost_comparison(self):
        """Compare costs between batch and individual API approaches."""
        self.logger.info(f"\n{'='*60}")
        self.logger.info("💰 COST COMPARISON: Batch vs Individual APIs")
        self.logger.info(f"{'='*60}")
        
        # Example calculation for 20 tokens
        token_count = 20
        
        # Individual API costs (old approach)
        individual_price_calls = token_count * 5  # 5 CU per price call
        individual_metadata_calls = token_count * 30  # 30 CU per metadata call
        individual_trade_calls = token_count * 15  # 15 CU per trade call
        total_individual_cost = individual_price_calls + individual_metadata_calls + individual_trade_calls
        
        # Batch API costs (new approach)
        batch_price_cost = int(pow(token_count, 0.8) * 5)  # N^0.8 × 5 for multi_price
        batch_metadata_cost = int(pow(min(token_count, 50), 0.8) * 5)  # N^0.8 × 5 for metadata (max 50)
        batch_trade_cost = int(pow(min(token_count, 20), 0.8) * 15)  # N^0.8 × 15 for trade data (max 20)
        total_batch_cost = batch_price_cost + batch_metadata_cost + batch_trade_cost
        
        cost_savings = total_individual_cost - total_batch_cost
        savings_percentage = (cost_savings / total_individual_cost) * 100
        
        self.logger.info(f"📊 Cost Analysis for {token_count} tokens:")
        self.logger.info(f"   Individual API Approach:")
        self.logger.info(f"     • Price calls: {token_count} × 5 CU = {individual_price_calls} CU")
        self.logger.info(f"     • Metadata calls: {token_count} × 30 CU = {individual_metadata_calls} CU")
        self.logger.info(f"     • Trade calls: {token_count} × 15 CU = {individual_trade_calls} CU")
        self.logger.info(f"     • Total: {total_individual_cost} CU")
        
        self.logger.info(f"   Batch API Approach:")
        self.logger.info(f"     • Batch price: {token_count}^0.8 × 5 = {batch_price_cost} CU")
        self.logger.info(f"     • Batch metadata: {min(token_count, 50)}^0.8 × 5 = {batch_metadata_cost} CU")
        self.logger.info(f"     • Batch trades: {min(token_count, 20)}^0.8 × 15 = {batch_trade_cost} CU")
        self.logger.info(f"     • Total: {total_batch_cost} CU")
        
        self.logger.info(f"💰 Cost Savings: {cost_savings} CU ({savings_percentage:.1f}% reduction)")
        
        # Rate limit comparison
        self.logger.info(f"\n📊 Rate Limit Impact:")
        self.logger.info(f"   Individual APIs: {token_count * 3} requests")
        self.logger.info(f"   Batch APIs: 3 requests (regardless of token count)")
        self.logger.info(f"   Rate Limit Efficiency: {((token_count * 3 - 3) / (token_count * 3)) * 100:.1f}% fewer requests")


async def main():
    """Main test function."""
    tester = BatchOptimizationTester()
    
    print("🚀 Starting Batch API Optimization Test")
    print("=" * 80)
    
    try:
        # Test batch optimization
        results = await tester.test_batch_optimization()
        
        # Test cost comparison
        await tester.test_cost_comparison()
        
        print("\n✅ Batch API Optimization Test Completed Successfully!")
        
    except Exception as e:
        print(f"❌ Test failed: {e}")
        raise


if __name__ == "__main__":
    asyncio.run(main()) 