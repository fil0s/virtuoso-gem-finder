#!/usr/bin/env python3
"""
Test API Call Tracking

This script tests the enhanced API call tracking functionality in the 
comprehensive strategy comparison script.
"""

import asyncio
import sys
import json
from pathlib import Path
from datetime import datetime

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from api.birdeye_connector import BirdeyeAPI
from core.strategies.volume_momentum_strategy import VolumeMomentumStrategy
from core.config_manager import get_config_manager
from services.logger_setup import LoggerSetup


class APICallTrackingTester:
    """Test the API call tracking functionality"""
    
    def __init__(self):
        """Initialize the testing system"""
        self.logger_setup = LoggerSetup("APICallTrackingTester")
        self.logger = self.logger_setup.logger
        
        # Initialize Birdeye API
        self.birdeye_api = BirdeyeAPI(logger=self.logger)
        
        self.logger.info("🧪 API Call Tracking Tester initialized")
    
    async def test_api_call_tracking(self):
        """Test the API call tracking functionality"""
        
        print(f"\n{'='*80}")
        print(f"🧪 TESTING API CALL TRACKING FUNCTIONALITY")
        print(f"{'='*80}")
        
        try:
            # Capture initial API statistics
            initial_stats = self.birdeye_api.get_api_call_statistics()
            initial_performance = self.birdeye_api.get_performance_stats()
            
            print(f"\n📊 INITIAL API STATISTICS:")
            print(f"   Total API Calls: {initial_stats.get('total_api_calls', 0)}")
            print(f"   Successful Calls: {initial_stats.get('successful_api_calls', 0)}")
            print(f"   Failed Calls: {initial_stats.get('failed_api_calls', 0)}")
            print(f"   Cache Hits: {initial_stats.get('cache_hits', 0)}")
            print(f"   Cache Misses: {initial_stats.get('cache_misses', 0)}")
            print(f"   Endpoints Called: {len(initial_stats.get('calls_by_endpoint', {}))}")
            
            # Initialize a strategy for testing
            strategy = VolumeMomentumStrategy(logger=self.logger)
            
            print(f"\n🚀 EXECUTING STRATEGY: {strategy.name}")
            print(f"   Description: {strategy.description}")
            
            # Execute the strategy to generate API calls
            tokens = await strategy.execute(
                self.birdeye_api, 
                scan_id="api_tracking_test"
            )
            
            # Capture final API statistics
            final_stats = self.birdeye_api.get_api_call_statistics()
            final_performance = self.birdeye_api.get_performance_stats()
            
            print(f"\n📊 FINAL API STATISTICS:")
            print(f"   Total API Calls: {final_stats.get('total_api_calls', 0)}")
            print(f"   Successful Calls: {final_stats.get('successful_api_calls', 0)}")
            print(f"   Failed Calls: {final_stats.get('failed_api_calls', 0)}")
            print(f"   Cache Hits: {final_stats.get('cache_hits', 0)}")
            print(f"   Cache Misses: {final_stats.get('cache_misses', 0)}")
            print(f"   Endpoints Called: {len(final_stats.get('calls_by_endpoint', {}))}")
            
            # Calculate the differences
            calls_made = final_stats.get('total_api_calls', 0) - initial_stats.get('total_api_calls', 0)
            successful_calls = final_stats.get('successful_api_calls', 0) - initial_stats.get('successful_api_calls', 0)
            failed_calls = final_stats.get('failed_api_calls', 0) - initial_stats.get('failed_api_calls', 0)
            cache_hits = final_stats.get('cache_hits', 0) - initial_stats.get('cache_hits', 0)
            cache_misses = final_stats.get('cache_misses', 0) - initial_stats.get('cache_misses', 0)
            
            print(f"\n📈 API CALLS MADE DURING STRATEGY EXECUTION:")
            print(f"   Total Calls: {calls_made}")
            print(f"   Successful Calls: {successful_calls}")
            print(f"   Failed Calls: {failed_calls}")
            print(f"   Cache Hits: {cache_hits}")
            print(f"   Cache Misses: {cache_misses}")
            
            # Analyze endpoint usage
            endpoint_usage = {}
            for endpoint, final_data in final_stats.get('calls_by_endpoint', {}).items():
                initial_data = initial_stats.get('calls_by_endpoint', {}).get(endpoint, {'total': 0})
                
                # Handle both dict and int formats
                if isinstance(final_data, dict):
                    final_count = final_data.get('total', 0)
                else:
                    final_count = final_data
                    
                if isinstance(initial_data, dict):
                    initial_count = initial_data.get('total', 0)
                else:
                    initial_count = initial_data
                
                calls_made_endpoint = final_count - initial_count
                if calls_made_endpoint > 0:
                    endpoint_usage[endpoint] = calls_made_endpoint
            
            # Categorize endpoints
            batch_endpoints = {}
            individual_endpoints = {}
            
            for endpoint, count in endpoint_usage.items():
                if any(batch_pattern in endpoint.lower() for batch_pattern in ['multi', 'multiple', 'batch']):
                    batch_endpoints[endpoint] = count
                else:
                    individual_endpoints[endpoint] = count
            
            print(f"\n🚀 BATCH ENDPOINTS USED:")
            if batch_endpoints:
                for endpoint, count in batch_endpoints.items():
                    print(f"   • {endpoint}: {count} calls")
            else:
                print(f"   No batch endpoints used")
            
            print(f"\n🔄 INDIVIDUAL ENDPOINTS USED:")
            if individual_endpoints:
                for endpoint, count in individual_endpoints.items():
                    print(f"   • {endpoint}: {count} calls")
            else:
                print(f"   No individual endpoints used")
            
            # Calculate efficiency metrics
            batch_calls = sum(batch_endpoints.values())
            individual_calls = sum(individual_endpoints.values())
            total_endpoint_calls = batch_calls + individual_calls
            
            batch_efficiency = (batch_calls / max(1, total_endpoint_calls)) * 100
            success_rate = (successful_calls / max(1, calls_made)) * 100 if calls_made > 0 else 0
            cache_hit_rate = (cache_hits / max(1, cache_hits + cache_misses)) * 100 if (cache_hits + cache_misses) > 0 else 0
            
            print(f"\n📊 EFFICIENCY METRICS:")
            print(f"   Batch Efficiency: {batch_efficiency:.1f}%")
            print(f"   Success Rate: {success_rate:.1f}%")
            print(f"   Cache Hit Rate: {cache_hit_rate:.1f}%")
            
            print(f"\n📋 STRATEGY RESULTS:")
            print(f"   Tokens Found: {len(tokens) if tokens else 0}")
            if tokens:
                print(f"   Sample Tokens:")
                for i, token in enumerate(tokens[:3], 1):
                    symbol = token.get('symbol', 'Unknown')
                    address = token.get('address', 'N/A')
                    print(f"      {i}. {symbol} ({address[:12]}...)")
            
            # Test the cost optimization report if available
            try:
                cost_report = strategy.get_cost_optimization_report()
                print(f"\n💰 COST OPTIMIZATION REPORT:")
                print(f"   Efficiency Grade: {cost_report.get('efficiency_grade', 'N/A')}")
                print(f"   Batch Efficiency Ratio: {cost_report.get('cost_metrics', {}).get('batch_efficiency_ratio', 0):.1%}")
                print(f"   Estimated CU Saved: {cost_report.get('cost_metrics', {}).get('estimated_cu_saved', 0):.0f}")
            except Exception as e:
                print(f"\n⚠️  Cost optimization report not available: {e}")
            
            print(f"\n✅ API Call Tracking Test Completed Successfully!")
            
            return {
                'calls_made': calls_made,
                'successful_calls': successful_calls,
                'failed_calls': failed_calls,
                'batch_calls': batch_calls,
                'individual_calls': individual_calls,
                'batch_efficiency': batch_efficiency,
                'success_rate': success_rate,
                'cache_hit_rate': cache_hit_rate,
                'tokens_found': len(tokens) if tokens else 0,
                'endpoints_used': len(endpoint_usage)
            }
            
        except Exception as e:
            print(f"❌ Error during API call tracking test: {e}")
            self.logger.error(f"API call tracking test error: {e}")
            raise
    
    async def cleanup(self):
        """Clean up resources"""
        try:
            await self.birdeye_api.close()
            print("🧹 Cleanup completed")
        except Exception as e:
            self.logger.warning(f"Error during cleanup: {e}")


async def main():
    """Main function to run API call tracking test"""
    
    print("🧪 API CALL TRACKING TEST")
    print("="*80)
    print("Testing enhanced API call tracking functionality")
    
    tester = APICallTrackingTester()
    
    try:
        # Run the test
        results = await tester.test_api_call_tracking()
        
        print(f"\n🎉 Test Results Summary:")
        print(f"   API Calls Made: {results['calls_made']}")
        print(f"   Batch Efficiency: {results['batch_efficiency']:.1f}%")
        print(f"   Success Rate: {results['success_rate']:.1f}%")
        print(f"   Tokens Found: {results['tokens_found']}")
        print(f"   Endpoints Used: {results['endpoints_used']}")
        
        # Determine test success
        if results['calls_made'] > 0:
            print(f"\n✅ API Call Tracking is Working Correctly!")
            print(f"   The system successfully tracked {results['calls_made']} API calls")
            print(f"   Batch optimization is {'working' if results['batch_calls'] > 0 else 'not detected'}")
        else:
            print(f"\n⚠️  No API calls detected - check configuration")
            
    except Exception as e:
        print(f"❌ Test failed: {e}")
    finally:
        await tester.cleanup()


if __name__ == "__main__":
    asyncio.run(main()) 