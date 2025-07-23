#!/usr/bin/env python3
"""
High Trading Activity Strategy Optimization Test

This script runs 3 scans using only the High Trading Activity Strategy
to analyze API call patterns and identify optimization opportunities.

Features:
- Detailed API call tracking per scan
- Token discovery analysis
- Performance metrics
- Optimization recommendations
- Data export for further analysis
"""

import asyncio
import json
import time
import psutil
import os
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Any, Optional
import yaml

# Add project root to path
import sys
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from api.birdeye_connector import BirdeyeAPI
from core.strategies.high_trading_activity_strategy import HighTradingActivityStrategy
from services.early_token_detection import EarlyTokenDetector
from utils.env_loader import load_environment


class HighTradingActivityOptimizationTest:
    """Comprehensive test for High Trading Activity Strategy optimization analysis."""
    
    def __init__(self):
        """Initialize the optimization test."""
        self.start_time = time.time()
        self.scan_results = []
        self.api_metrics = []
        self.optimization_insights = {}
        
        # Load environment and config
        load_environment()
        with open('config/config.yaml', 'r') as f:
            self.config = yaml.safe_load(f)
        
        # Initialize APIs
        from core.cache_manager import CacheManager
        from services.rate_limiter_service import RateLimiterService
        from services.logger_setup import LoggerSetup
        
        # Setup logger
        logger_setup = LoggerSetup("OptimizationTest")
        self.logger = logger_setup.logger
        
        # Initialize cache and rate limiter
        cache_manager = CacheManager()
        rate_limiter = RateLimiterService()
        
        # Initialize BirdeyeAPI properly
        birdeye_config = self.config.get('BIRDEYE_API', {})
        # Force load API key from environment
        birdeye_config['api_key'] = os.environ.get('BIRDEYE_API_KEY')
        
        self.birdeye_api = BirdeyeAPI(
            config=birdeye_config,
            logger=self.logger,
            cache_manager=cache_manager,
            rate_limiter=rate_limiter
        )
        
        # Initialize strategy
        self.strategy = HighTradingActivityStrategy(logger=self.logger)
        
        # Initialize batch-optimized detector for comparison
        self.batch_detector = EarlyTokenDetector(self.config)
        
        # Results directory
        self.results_dir = Path("scripts/results")
        self.results_dir.mkdir(exist_ok=True)
        
        print("🔬 High Trading Activity Strategy Optimization Test")
        print("=" * 60)
        print(f"📅 Test started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"🎯 Strategy: {self.strategy.name}")
        print(f"⏱️  Scan interval: 2 minutes (demo mode)")
        print(f"🔢 Total scans: 3")
        print()
    
    async def run_optimization_test(self):
        """Run the complete optimization test."""
        print("🚀 Starting High Trading Activity Strategy Optimization Test")
        print("=" * 60)
        
        # Run 3 scans with detailed tracking
        for scan_num in range(1, 4):
            print(f"\n🔍 SCAN #{scan_num} - {datetime.now().strftime('%H:%M:%S')}")
            print("-" * 40)
            
            # Run scan with detailed metrics
            scan_result = await self._run_detailed_scan(scan_num)
            self.scan_results.append(scan_result)
            
            # Display immediate results
            self._display_scan_summary(scan_result)
            
            # Wait 2 minutes before next scan (except for last scan) - shortened for demo
            if scan_num < 3:
                print(f"\n⏳ Waiting 2 minutes before next scan...")
                await self._countdown_timer(120)  # 2 minutes
        
        # Generate comprehensive analysis
        await self._generate_optimization_analysis()
        
        # Save results
        await self._save_results()
        
        print(f"\n🎉 Optimization test completed!")
        print(f"📊 Results saved to: {self.results_dir}")
    
    async def _run_detailed_scan(self, scan_num: int) -> Dict[str, Any]:
        """Run a single scan with detailed API and performance tracking."""
        scan_start_time = time.time()
        
        # Reset API call tracking
        initial_api_calls = self.birdeye_api.api_call_tracker['total_api_calls']
        
        # Memory tracking
        process = psutil.Process()
        initial_memory = process.memory_info().rss / 1024 / 1024  # MB
        
        print(f"📊 Initial API calls: {initial_api_calls}")
        print(f"💾 Initial memory: {initial_memory:.1f} MB")
        
        # Test 1: Raw strategy execution
        print(f"\n🧪 Test 1: Raw Strategy Execution")
        raw_start_time = time.time()
        raw_api_calls_start = self.birdeye_api.api_call_tracker['total_api_calls']
        
        try:
            raw_tokens = await self.strategy.execute(self.birdeye_api)
            raw_execution_time = time.time() - raw_start_time
            raw_api_calls_used = self.birdeye_api.api_call_tracker['total_api_calls'] - raw_api_calls_start
            
            print(f"   ✅ Raw execution completed")
            print(f"   🔢 Tokens discovered: {len(raw_tokens)}")
            print(f"   ⏱️  Execution time: {raw_execution_time:.2f}s")
            print(f"   📞 API calls used: {raw_api_calls_used}")
            
        except Exception as e:
            print(f"   ❌ Raw execution failed: {e}")
            raw_tokens = []
            raw_execution_time = 0
            raw_api_calls_used = 0
        
        # Small delay to avoid rate limiting
        await asyncio.sleep(2)
        
        # Test 2: Batch-optimized execution
        print(f"\n🧪 Test 2: Batch-Optimized Execution")
        batch_start_time = time.time()
        batch_api_calls_start = self.birdeye_api.api_call_tracker['total_api_calls']
        
        try:
            # Use EarlyTokenDetector batch-optimized discovery
            batch_tokens = await self.batch_detector.discover_and_analyze(
                max_tokens=30
            )
            batch_execution_time = time.time() - batch_start_time
            batch_api_calls_used = self.birdeye_api.api_call_tracker['total_api_calls'] - batch_api_calls_start
            
            print(f"   ✅ Batch execution completed")
            print(f"   🔢 Tokens discovered: {len(batch_tokens)}")
            print(f"   ⏱️  Execution time: {batch_execution_time:.2f}s")
            print(f"   📞 API calls used: {batch_api_calls_used}")
            
        except Exception as e:
            print(f"   ❌ Batch execution failed: {e}")
            batch_tokens = []
            batch_execution_time = 0
            batch_api_calls_used = 0
        
        # Final metrics
        total_scan_time = time.time() - scan_start_time
        total_api_calls = self.birdeye_api.api_call_tracker['total_api_calls'] - initial_api_calls
        final_memory = process.memory_info().rss / 1024 / 1024  # MB
        memory_used = final_memory - initial_memory
        
        # API call breakdown
        api_breakdown = self._get_api_call_breakdown()
        
        # Create comprehensive scan result
        scan_result = {
            "scan_number": scan_num,
            "timestamp": datetime.now().isoformat(),
            "scan_duration": total_scan_time,
            "memory_used_mb": memory_used,
            "total_api_calls": total_api_calls,
            "api_breakdown": api_breakdown,
            "raw_strategy": {
                "tokens_found": len(raw_tokens),
                "execution_time": raw_execution_time,
                "api_calls_used": raw_api_calls_used,
                "tokens": raw_tokens[:5] if raw_tokens else []  # Sample tokens
            },
            "batch_optimized": {
                "tokens_found": len(batch_tokens),
                "execution_time": batch_execution_time,
                "api_calls_used": batch_api_calls_used,
                "tokens": batch_tokens[:5] if batch_tokens else []  # Sample tokens
            },
            "efficiency_comparison": {
                "api_calls_saved": max(0, raw_api_calls_used - batch_api_calls_used),
                "time_difference": raw_execution_time - batch_execution_time,
                "tokens_difference": len(batch_tokens) - len(raw_tokens)
            }
        }
        
        return scan_result
    
    def _get_api_call_breakdown(self) -> Dict[str, int]:
        """Get detailed API call breakdown by endpoint."""
        tracker = self.birdeye_api.api_call_tracker
        
        breakdown = {}
        for endpoint, count in tracker.items():
            if isinstance(count, int) and endpoint != 'total_api_calls':
                breakdown[endpoint] = count
        
        return breakdown
    
    def _display_scan_summary(self, scan_result: Dict[str, Any]):
        """Display immediate scan summary."""
        print(f"\n📊 SCAN #{scan_result['scan_number']} SUMMARY")
        print("-" * 30)
        print(f"⏱️  Total scan time: {scan_result['scan_duration']:.2f}s")
        print(f"💾 Memory used: {scan_result['memory_used_mb']:.1f} MB")
        print(f"📞 Total API calls: {scan_result['total_api_calls']}")
        
        print(f"\n🔄 EXECUTION COMPARISON:")
        raw = scan_result['raw_strategy']
        batch = scan_result['batch_optimized']
        
        print(f"   Raw Strategy:    {raw['tokens_found']:2d} tokens, {raw['api_calls_used']:2d} calls, {raw['execution_time']:.1f}s")
        print(f"   Batch Optimized: {batch['tokens_found']:2d} tokens, {batch['api_calls_used']:2d} calls, {batch['execution_time']:.1f}s")
        
        efficiency = scan_result['efficiency_comparison']
        if efficiency['api_calls_saved'] > 0:
            savings_pct = (efficiency['api_calls_saved'] / raw['api_calls_used']) * 100 if raw['api_calls_used'] > 0 else 0
            print(f"   💰 Savings:      {efficiency['api_calls_saved']} calls ({savings_pct:.1f}% reduction)")
        
        # API breakdown
        if scan_result['api_breakdown']:
            print(f"\n📞 API CALL BREAKDOWN:")
            for endpoint, count in scan_result['api_breakdown'].items():
                if count > 0:
                    print(f"   {endpoint}: {count}")
    
    async def _countdown_timer(self, seconds: int):
        """Display countdown timer."""
        while seconds > 0:
            mins, secs = divmod(seconds, 60)
            print(f"\r⏳ Next scan in: {mins:02d}:{secs:02d}", end="", flush=True)
            await asyncio.sleep(1)
            seconds -= 1
        print(f"\r⏳ Starting next scan...        ")
    
    async def _generate_optimization_analysis(self):
        """Generate comprehensive optimization analysis."""
        print(f"\n🔬 GENERATING OPTIMIZATION ANALYSIS")
        print("=" * 50)
        
        if not self.scan_results:
            print("❌ No scan results to analyze")
            return
        
        # Calculate averages and trends
        total_scans = len(self.scan_results)
        
        # API call analysis
        avg_total_calls = sum(r['total_api_calls'] for r in self.scan_results) / total_scans
        avg_raw_calls = sum(r['raw_strategy']['api_calls_used'] for r in self.scan_results) / total_scans
        avg_batch_calls = sum(r['batch_optimized']['api_calls_used'] for r in self.scan_results) / total_scans
        
        # Performance analysis
        avg_scan_time = sum(r['scan_duration'] for r in self.scan_results) / total_scans
        avg_raw_time = sum(r['raw_strategy']['execution_time'] for r in self.scan_results) / total_scans
        avg_batch_time = sum(r['batch_optimized']['execution_time'] for r in self.scan_results) / total_scans
        
        # Token discovery analysis
        avg_raw_tokens = sum(r['raw_strategy']['tokens_found'] for r in self.scan_results) / total_scans
        avg_batch_tokens = sum(r['batch_optimized']['tokens_found'] for r in self.scan_results) / total_scans
        
        # Memory analysis
        avg_memory = sum(r['memory_used_mb'] for r in self.scan_results) / total_scans
        
        # API endpoint analysis
        endpoint_totals = {}
        for scan in self.scan_results:
            for endpoint, count in scan['api_breakdown'].items():
                endpoint_totals[endpoint] = endpoint_totals.get(endpoint, 0) + count
        
        # Calculate efficiency gains
        api_efficiency = ((avg_raw_calls - avg_batch_calls) / avg_raw_calls * 100) if avg_raw_calls > 0 else 0
        time_efficiency = ((avg_raw_time - avg_batch_time) / avg_raw_time * 100) if avg_raw_time > 0 else 0
        
        self.optimization_insights = {
            "test_summary": {
                "total_scans": total_scans,
                "test_duration_minutes": (time.time() - self.start_time) / 60,
                "strategy_tested": self.strategy.name
            },
            "api_call_analysis": {
                "average_total_calls_per_scan": round(avg_total_calls, 1),
                "average_raw_strategy_calls": round(avg_raw_calls, 1),
                "average_batch_optimized_calls": round(avg_batch_calls, 1),
                "api_efficiency_gain_percent": round(api_efficiency, 1),
                "calls_saved_per_scan": round(avg_raw_calls - avg_batch_calls, 1)
            },
            "performance_analysis": {
                "average_scan_duration_seconds": round(avg_scan_time, 2),
                "average_raw_execution_seconds": round(avg_raw_time, 2),
                "average_batch_execution_seconds": round(avg_batch_time, 2),
                "time_efficiency_gain_percent": round(time_efficiency, 1),
                "average_memory_usage_mb": round(avg_memory, 1)
            },
            "token_discovery_analysis": {
                "average_raw_tokens_found": round(avg_raw_tokens, 1),
                "average_batch_tokens_found": round(avg_batch_tokens, 1),
                "token_discovery_difference": round(avg_batch_tokens - avg_raw_tokens, 1)
            },
            "endpoint_usage_analysis": {
                "total_calls_by_endpoint": endpoint_totals,
                "most_used_endpoints": sorted(endpoint_totals.items(), key=lambda x: x[1], reverse=True)[:5]
            },
            "optimization_recommendations": self._generate_optimization_recommendations(
                avg_raw_calls, avg_batch_calls, endpoint_totals, api_efficiency
            )
        }
        
        # Display analysis
        self._display_optimization_analysis()
    
    def _generate_optimization_recommendations(self, avg_raw_calls: float, avg_batch_calls: float, 
                                             endpoint_totals: Dict[str, int], api_efficiency: float) -> List[str]:
        """Generate specific optimization recommendations."""
        recommendations = []
        
        # API efficiency recommendations
        if api_efficiency > 20:
            recommendations.append(f"🚀 EXCELLENT: Batch optimization provides {api_efficiency:.1f}% API call reduction")
            recommendations.append("✅ Continue using batch-optimized EarlyTokenDetector for production")
        elif api_efficiency > 10:
            recommendations.append(f"✅ GOOD: Batch optimization provides {api_efficiency:.1f}% API call reduction")
            recommendations.append("💡 Consider further batch optimization for even better efficiency")
        else:
            recommendations.append("⚠️ LIMITED: Batch optimization shows minimal API call reduction")
            recommendations.append("🔍 Investigate why batch optimization isn't more effective")
        
        # Endpoint-specific recommendations
        if endpoint_totals:
            top_endpoint = max(endpoint_totals.items(), key=lambda x: x[1])
            recommendations.append(f"🎯 FOCUS: '{top_endpoint[0]}' is the most used endpoint ({top_endpoint[1]} calls)")
            
            if top_endpoint[1] > avg_raw_calls * 0.5:
                recommendations.append("💡 Consider caching or batching this endpoint for maximum impact")
        
        # Performance recommendations
        if avg_raw_calls > 50:
            recommendations.append("⚡ HIGH USAGE: Consider implementing more aggressive caching")
            recommendations.append("🔄 Evaluate if all API calls are necessary for strategy effectiveness")
        
        # Strategy-specific recommendations
        recommendations.append("📊 STRATEGY SPECIFIC: High Trading Activity Strategy focuses on trade counts")
        recommendations.append("💡 Consider pre-filtering by trade count before detailed analysis")
        recommendations.append("🎯 Optimize for tokens with trade_count > threshold to reduce API overhead")
        
        return recommendations
    
    def _display_optimization_analysis(self):
        """Display the comprehensive optimization analysis."""
        insights = self.optimization_insights
        
        print(f"\n📊 COMPREHENSIVE OPTIMIZATION ANALYSIS")
        print("=" * 50)
        
        # Test Summary
        summary = insights['test_summary']
        print(f"🧪 Test completed: {summary['total_scans']} scans over {summary['test_duration_minutes']:.1f} minutes")
        print(f"🎯 Strategy tested: {summary['strategy_tested']}")
        
        # API Call Analysis
        api = insights['api_call_analysis']
        print(f"\n📞 API CALL EFFICIENCY:")
        print(f"   Raw Strategy:     {api['average_raw_strategy_calls']:.1f} calls/scan")
        print(f"   Batch Optimized:  {api['average_batch_optimized_calls']:.1f} calls/scan")
        print(f"   💰 Efficiency Gain: {api['api_efficiency_gain_percent']:.1f}% ({api['calls_saved_per_scan']:.1f} calls saved/scan)")
        
        # Performance Analysis
        perf = insights['performance_analysis']
        print(f"\n⚡ PERFORMANCE METRICS:")
        print(f"   Average scan time: {perf['average_scan_duration_seconds']:.2f}s")
        print(f"   Raw execution:     {perf['average_raw_execution_seconds']:.2f}s")
        print(f"   Batch execution:   {perf['average_batch_execution_seconds']:.2f}s")
        print(f"   ⏱️  Time Efficiency: {perf['time_efficiency_gain_percent']:.1f}% improvement")
        print(f"   💾 Memory usage:   {perf['average_memory_usage_mb']:.1f} MB/scan")
        
        # Token Discovery
        tokens = insights['token_discovery_analysis']
        print(f"\n🔍 TOKEN DISCOVERY:")
        print(f"   Raw tokens found:    {tokens['average_raw_tokens_found']:.1f}/scan")
        print(f"   Batch tokens found:  {tokens['average_batch_tokens_found']:.1f}/scan")
        print(f"   📈 Discovery diff:   {tokens['token_discovery_difference']:+.1f} tokens")
        
        # Top Endpoints
        endpoints = insights['endpoint_usage_analysis']['most_used_endpoints']
        print(f"\n🎯 TOP API ENDPOINTS:")
        for endpoint, count in endpoints:
            print(f"   {endpoint}: {count} calls")
        
        # Recommendations
        print(f"\n💡 OPTIMIZATION RECOMMENDATIONS:")
        for i, rec in enumerate(insights['optimization_recommendations'], 1):
            print(f"   {i}. {rec}")
    
    async def _save_results(self):
        """Save all results to files for further analysis."""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        # Save comprehensive results
        results_file = self.results_dir / f"high_trading_activity_optimization_{timestamp}.json"
        with open(results_file, 'w') as f:
            json.dump({
                "scan_results": self.scan_results,
                "optimization_insights": self.optimization_insights,
                "test_metadata": {
                    "timestamp": timestamp,
                    "strategy_name": self.strategy.name,
                    "total_scans": len(self.scan_results),
                    "test_duration_minutes": (time.time() - self.start_time) / 60
                }
            }, f, indent=2)
        
        # Save summary report
        summary_file = self.results_dir / f"optimization_summary_{timestamp}.txt"
        with open(summary_file, 'w') as f:
            f.write("HIGH TRADING ACTIVITY STRATEGY OPTIMIZATION REPORT\n")
            f.write("=" * 60 + "\n\n")
            
            insights = self.optimization_insights
            api = insights['api_call_analysis']
            perf = insights['performance_analysis']
            
            f.write(f"API Efficiency: {api['api_efficiency_gain_percent']:.1f}% improvement\n")
            f.write(f"Calls Saved: {api['calls_saved_per_scan']:.1f} per scan\n")
            f.write(f"Time Efficiency: {perf['time_efficiency_gain_percent']:.1f}% improvement\n")
            f.write(f"Memory Usage: {perf['average_memory_usage_mb']:.1f} MB per scan\n\n")
            
            f.write("RECOMMENDATIONS:\n")
            for i, rec in enumerate(insights['optimization_recommendations'], 1):
                f.write(f"{i}. {rec}\n")
        
        print(f"\n💾 Results saved:")
        print(f"   📊 Detailed results: {results_file}")
        print(f"   📄 Summary report: {summary_file}")


async def main():
    """Run the High Trading Activity Strategy optimization test."""
    test = HighTradingActivityOptimizationTest()
    await test.run_optimization_test()


if __name__ == "__main__":
    asyncio.run(main()) 