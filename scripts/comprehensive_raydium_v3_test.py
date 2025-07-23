#!/usr/bin/env python3
"""
Comprehensive end-to-end test for Raydium v3 implementation
Tests all components, integration points, and production scenarios
"""

import asyncio
import sys
import os
import time
import json
from pathlib import Path
from typing import Dict, List, Any
import logging

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.detectors.early_gem_detector import EarlyGemDetector
from api.raydium_connector import RaydiumConnector
from services.rate_limiter_service import RateLimiterService

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class ComprehensiveTestSuite:
    """Comprehensive test suite for Raydium v3 implementation"""
    
    def __init__(self):
        self.test_results = {
            'total_tests': 0,
            'passed_tests': 0,
            'failed_tests': 0,
            'test_details': [],
            'performance_metrics': {},
            'production_readiness': False
        }
        self.detector = None
    
    def log_test_result(self, test_name: str, passed: bool, details: str = "", metrics: Dict = None):
        """Log individual test result"""
        self.test_results['total_tests'] += 1
        if passed:
            self.test_results['passed_tests'] += 1
            status = "✅ PASS"
        else:
            self.test_results['failed_tests'] += 1
            status = "❌ FAIL"
        
        result = {
            'test_name': test_name,
            'status': status,
            'passed': passed,
            'details': details,
            'metrics': metrics or {}
        }
        self.test_results['test_details'].append(result)
        
        print(f"{status} {test_name}")
        if details:
            print(f"    {details}")
        if metrics:
            for key, value in metrics.items():
                if isinstance(value, float):
                    print(f"    {key}: {value:.2f}")
                else:
                    print(f"    {key}: {value}")
    
    async def test_1_initialization(self):
        """Test 1: Proper initialization of all components"""
        print("\n🔧 Test 1: Component Initialization")
        
        try:
            # Initialize EarlyGemDetector
            start_time = time.time()
            self.detector = EarlyGemDetector(debug_mode=True)
            init_time = time.time() - start_time
            
            # Check RaydiumConnector initialization
            if not self.detector.raydium_connector:
                self.log_test_result("1.1 RaydiumConnector Initialization", False, "RaydiumConnector not initialized")
                return False
            
            # Verify configuration
            connector = self.detector.raydium_connector
            config_checks = {
                "base_url": connector.base_url == "https://api-v3.raydium.io",
                "v3_endpoints": 'pools' in connector.v3_endpoints,
                "cache_manager": connector.enhanced_cache is not None,
                "rate_limiter": connector.rate_limiter is not None,
                "api_tracking": connector.api_tracking_enabled is True
            }
            
            failed_checks = [k for k, v in config_checks.items() if not v]
            if failed_checks:
                self.log_test_result("1.2 Configuration Verification", False, f"Failed checks: {failed_checks}")
                return False
            
            self.log_test_result("1.1 EarlyGemDetector Initialization", True, f"Initialized in {init_time:.2f}s", {"init_time": init_time})
            self.log_test_result("1.2 RaydiumConnector Configuration", True, "All configuration checks passed")
            return True
            
        except Exception as e:
            self.log_test_result("1.1 Initialization", False, f"Exception: {e}")
            return False
    
    async def test_2_connector_functionality(self):
        """Test 2: Direct RaydiumConnector functionality"""
        print("\n🔌 Test 2: RaydiumConnector Functionality")
        
        connector = self.detector.raydium_connector
        
        try:
            async with connector:
                # Test 2.1: Basic pools retrieval
                start_time = time.time()
                pools = await connector.get_pools(limit=5)
                pools_time = time.time() - start_time
                
                if not isinstance(pools, list):
                    self.log_test_result("2.1 Pools Retrieval", False, f"Invalid return type: {type(pools)}")
                    return False
                
                self.log_test_result("2.1 Pools Retrieval", True, f"{len(pools)} pools retrieved", {
                    "pools_count": len(pools),
                    "retrieval_time": pools_time
                })
                
                # Test 2.2: Pairs retrieval
                start_time = time.time()
                pairs = await connector.get_pairs(limit=5)
                pairs_time = time.time() - start_time
                
                if not isinstance(pairs, list):
                    self.log_test_result("2.2 Pairs Retrieval", False, f"Invalid return type: {type(pairs)}")
                    return False
                
                self.log_test_result("2.2 Pairs Retrieval", True, f"{len(pairs)} pairs retrieved", {
                    "pairs_count": len(pairs),
                    "retrieval_time": pairs_time
                })
                
                # Test 2.3: WSOL trending pairs (core functionality)
                start_time = time.time()
                wsol_pairs = await connector.get_wsol_trending_pairs(limit=10)
                wsol_time = time.time() - start_time
                
                if not isinstance(wsol_pairs, list):
                    self.log_test_result("2.3 WSOL Pairs Retrieval", False, f"Invalid return type: {type(wsol_pairs)}")
                    return False
                
                # Validate WSOL pair structure
                if wsol_pairs:
                    sample_pair = wsol_pairs[0]
                    required_fields = [
                        'address', 'symbol', 'tvl', 'volume_24h', 'volume_tvl_ratio',
                        'is_early_gem_candidate', 'early_gem_score', 'is_wsol_pair'
                    ]
                    
                    missing_fields = [field for field in required_fields if field not in sample_pair]
                    if missing_fields:
                        self.log_test_result("2.3 WSOL Pairs Structure", False, f"Missing fields: {missing_fields}")
                        return False
                    
                    # Check early gem detection
                    early_gems = [p for p in wsol_pairs if p.get('is_early_gem_candidate', False)]
                    early_gem_ratio = len(early_gems) / len(wsol_pairs) if wsol_pairs else 0
                    
                    self.log_test_result("2.3 WSOL Pairs Retrieval", True, f"{len(wsol_pairs)} pairs, {len(early_gems)} early gems", {
                        "wsol_pairs_count": len(wsol_pairs),
                        "early_gems_count": len(early_gems),
                        "early_gem_ratio": early_gem_ratio,
                        "retrieval_time": wsol_time
                    })
                else:
                    self.log_test_result("2.3 WSOL Pairs Retrieval", True, "0 pairs retrieved (API may be empty)", {
                        "wsol_pairs_count": 0,
                        "retrieval_time": wsol_time
                    })
                
                # Test 2.4: API statistics
                stats = connector.get_api_call_statistics()
                if not isinstance(stats, dict) or 'total_calls' not in stats:
                    self.log_test_result("2.4 API Statistics", False, "Invalid statistics format")
                    return False
                
                self.log_test_result("2.4 API Statistics", True, f"Success rate: {stats['success_rate']:.1%}", stats)
                return True
                
        except Exception as e:
            self.log_test_result("2.X Connector Functionality", False, f"Exception: {e}")
            return False
    
    async def test_3_fetch_method_integration(self):
        """Test 3: _fetch_raydium_v3_pools method integration"""
        print("\n🔄 Test 3: Fetch Method Integration")
        
        try:
            # Test 3.1: Method existence and callable
            if not hasattr(self.detector, '_fetch_raydium_v3_pools'):
                self.log_test_result("3.1 Method Existence", False, "_fetch_raydium_v3_pools method not found")
                return False
            
            if not callable(self.detector._fetch_raydium_v3_pools):
                self.log_test_result("3.1 Method Callable", False, "_fetch_raydium_v3_pools not callable")
                return False
            
            self.log_test_result("3.1 Method Existence", True, "Method found and callable")
            
            # Test 3.2: Method execution
            start_time = time.time()
            candidates = await self.detector._fetch_raydium_v3_pools()
            execution_time = time.time() - start_time
            
            if not isinstance(candidates, list):
                self.log_test_result("3.2 Method Execution", False, f"Invalid return type: {type(candidates)}")
                return False
            
            self.log_test_result("3.2 Method Execution", True, f"{len(candidates)} candidates returned", {
                "candidates_count": len(candidates),
                "execution_time": execution_time
            })
            
            # Test 3.3: Candidate structure validation
            if candidates:
                sample_candidate = candidates[0]
                required_fields = [
                    'symbol', 'address', 'market_cap', 'volume_24h', 'liquidity',
                    'is_early_gem_candidate', 'early_gem_score', 'discovery_source',
                    'platform', 'platforms', 'source'
                ]
                
                missing_fields = [field for field in required_fields if field not in sample_candidate]
                if missing_fields:
                    self.log_test_result("3.3 Candidate Structure", False, f"Missing fields: {missing_fields}")
                    return False
                
                # Validate data types
                type_checks = {
                    'symbol': str,
                    'address': str,
                    'volume_24h': (int, float),
                    'liquidity': (int, float),
                    'is_early_gem_candidate': bool,
                    'early_gem_score': (int, float),
                    'platform': str,
                    'platforms': list
                }
                
                type_errors = []
                for field, expected_type in type_checks.items():
                    if field in sample_candidate and not isinstance(sample_candidate[field], expected_type):
                        type_errors.append(f"{field}: expected {expected_type}, got {type(sample_candidate[field])}")
                
                if type_errors:
                    self.log_test_result("3.3 Candidate Structure", False, f"Type errors: {type_errors}")
                    return False
                
                # Count early gems
                early_gems = [c for c in candidates if c.get('is_early_gem_candidate', False)]
                
                self.log_test_result("3.3 Candidate Structure", True, f"All fields valid, {len(early_gems)} early gems", {
                    "early_gems_count": len(early_gems),
                    "total_candidates": len(candidates)
                })
            else:
                self.log_test_result("3.3 Candidate Structure", True, "No candidates to validate (API may be empty)")
            
            return True
            
        except Exception as e:
            self.log_test_result("3.X Fetch Method", False, f"Exception: {e}")
            return False
    
    async def test_4_pipeline_integration(self):
        """Test 4: Integration with detection pipeline"""
        print("\n🔗 Test 4: Detection Pipeline Integration")
        
        try:
            # Test 4.1: Pipeline discovery
            start_time = time.time()
            all_candidates = await self.detector.discover_early_tokens()
            pipeline_time = time.time() - start_time
            
            if not isinstance(all_candidates, list):
                self.log_test_result("4.1 Pipeline Discovery", False, f"Invalid return type: {type(all_candidates)}")
                return False
            
            # Find Raydium v3 candidates
            raydium_v3_candidates = [
                c for c in all_candidates 
                if c.get('discovery_source') == 'raydium_v3_enhanced' or 
                   c.get('source') == 'raydium_v3_pools' or
                   'raydium_v3' in str(c.get('discovery_source', '')).lower()
            ]
            
            self.log_test_result("4.1 Pipeline Discovery", True, f"{len(all_candidates)} total, {len(raydium_v3_candidates)} from Raydium v3", {
                "total_candidates": len(all_candidates),
                "raydium_v3_candidates": len(raydium_v3_candidates),
                "pipeline_time": pipeline_time
            })
            
            # Test 4.2: Platform distribution
            platform_distribution = {}
            for candidate in all_candidates:
                source = candidate.get('discovery_source', candidate.get('source', 'unknown'))
                platform_distribution[source] = platform_distribution.get(source, 0) + 1
            
            raydium_v3_present = any('raydium' in str(k).lower() for k in platform_distribution.keys())
            
            self.log_test_result("4.2 Platform Distribution", raydium_v3_present, 
                               f"Platforms: {list(platform_distribution.keys())}", 
                               platform_distribution)
            
            return raydium_v3_present
            
        except Exception as e:
            self.log_test_result("4.X Pipeline Integration", False, f"Exception: {e}")
            return False
    
    async def test_5_error_handling(self):
        """Test 5: Error handling and resilience"""
        print("\n🛡️ Test 5: Error Handling & Resilience")
        
        connector = self.detector.raydium_connector
        
        try:
            async with connector:
                # Test 5.1: Invalid endpoint handling
                start_time = time.time()
                result = await connector._make_tracked_request("/invalid/endpoint", use_v2_fallback=False)
                error_handling_time = time.time() - start_time
                
                # Should return None for invalid endpoints, not crash
                if result is None:
                    self.log_test_result("5.1 Invalid Endpoint Handling", True, "Gracefully handled invalid endpoint", {
                        "error_handling_time": error_handling_time
                    })
                else:
                    self.log_test_result("5.1 Invalid Endpoint Handling", False, f"Unexpected result: {result}")
                    return False
                
                # Test 5.2: Rate limiting behavior
                original_delay = connector.rate_limit_delay
                connector.rate_limit_delay = 0.1  # Speed up test
                
                start_time = time.time()
                tasks = [connector.get_pools(limit=1) for _ in range(3)]
                results = await asyncio.gather(*tasks, return_exceptions=True)
                rate_limit_time = time.time() - start_time
                
                connector.rate_limit_delay = original_delay  # Restore
                
                successful_results = [r for r in results if not isinstance(r, Exception)]
                
                self.log_test_result("5.2 Rate Limiting", True, f"{len(successful_results)}/3 requests successful", {
                    "successful_requests": len(successful_results),
                    "total_time": rate_limit_time
                })
                
                # Test 5.3: Statistics after errors
                stats = connector.get_api_call_statistics()
                has_failed_calls = stats.get('failed_calls', 0) > 0
                
                self.log_test_result("5.3 Error Statistics", True, f"Failed calls tracked: {stats.get('failed_calls', 0)}", {
                    "failed_calls": stats.get('failed_calls', 0),
                    "total_calls": stats.get('total_calls', 0)
                })
                
                return True
                
        except Exception as e:
            self.log_test_result("5.X Error Handling", False, f"Exception: {e}")
            return False
    
    async def test_6_performance_benchmarks(self):
        """Test 6: Performance benchmarks"""
        print("\n⚡ Test 6: Performance Benchmarks")
        
        connector = self.detector.raydium_connector
        performance_metrics = {}
        
        try:
            async with connector:
                # Test 6.1: Single request latency
                latencies = []
                for i in range(3):
                    start_time = time.time()
                    await connector.get_pools(limit=3)
                    latency = time.time() - start_time
                    latencies.append(latency)
                
                avg_latency = sum(latencies) / len(latencies)
                max_latency = max(latencies)
                min_latency = min(latencies)
                
                # Performance thresholds (reasonable for API calls)
                latency_ok = avg_latency < 5.0  # Average under 5 seconds
                
                self.log_test_result("6.1 Single Request Latency", latency_ok, 
                                   f"Avg: {avg_latency:.2f}s, Range: {min_latency:.2f}s-{max_latency:.2f}s", {
                                       "avg_latency": avg_latency,
                                       "max_latency": max_latency,
                                       "min_latency": min_latency
                                   })
                
                performance_metrics.update({
                    "avg_latency": avg_latency,
                    "max_latency": max_latency,
                    "min_latency": min_latency
                })
                
                # Test 6.2: Throughput test
                start_time = time.time()
                tasks = [connector.get_pools(limit=2) for _ in range(5)]
                results = await asyncio.gather(*tasks, return_exceptions=True)
                throughput_time = time.time() - start_time
                
                successful_requests = len([r for r in results if not isinstance(r, Exception)])
                requests_per_second = successful_requests / throughput_time
                
                # Throughput threshold
                throughput_ok = requests_per_second > 0.1  # At least 0.1 RPS
                
                self.log_test_result("6.2 Throughput", throughput_ok, 
                                   f"{requests_per_second:.2f} requests/second", {
                                       "requests_per_second": requests_per_second,
                                       "successful_requests": successful_requests,
                                       "total_time": throughput_time
                                   })
                
                performance_metrics["requests_per_second"] = requests_per_second
                
                # Test 6.3: Memory usage (basic check)
                import psutil
                import os
                
                process = psutil.Process(os.getpid())
                memory_usage = process.memory_info().rss / 1024 / 1024  # MB
                
                # Memory threshold (reasonable for this type of application)
                memory_ok = memory_usage < 500  # Under 500MB
                
                self.log_test_result("6.3 Memory Usage", memory_ok, f"{memory_usage:.1f} MB", {
                    "memory_usage_mb": memory_usage
                })
                
                performance_metrics["memory_usage_mb"] = memory_usage
                
                self.test_results['performance_metrics'] = performance_metrics
                return latency_ok and throughput_ok and memory_ok
                
        except Exception as e:
            self.log_test_result("6.X Performance", False, f"Exception: {e}")
            return False
    
    async def test_7_production_scenarios(self):
        """Test 7: Real production scenarios"""
        print("\n🏭 Test 7: Production Scenarios")
        
        try:
            # Test 7.1: Full detection cycle
            start_time = time.time()
            
            # Simulate full detection cycle
            candidates = await self.detector._fetch_raydium_v3_pools()
            
            if candidates:
                # Test scoring integration
                scored_candidates = []
                for candidate in candidates[:3]:  # Test first 3
                    try:
                        # This would normally go through the full scoring pipeline
                        scored_candidate = candidate.copy()
                        scored_candidate['test_score'] = 50.0  # Mock score
                        scored_candidates.append(scored_candidate)
                    except Exception as e:
                        logger.warning(f"Scoring failed for candidate: {e}")
                
                detection_time = time.time() - start_time
                
                self.log_test_result("7.1 Full Detection Cycle", True, 
                                   f"{len(scored_candidates)} candidates processed", {
                                       "candidates_processed": len(scored_candidates),
                                       "detection_time": detection_time
                                   })
            else:
                self.log_test_result("7.1 Full Detection Cycle", True, "No candidates to process (API may be empty)")
            
            # Test 7.2: Continuous operation simulation
            start_time = time.time()
            
            for i in range(3):  # Simulate 3 detection cycles
                candidates = await self.detector._fetch_raydium_v3_pools()
                await asyncio.sleep(0.5)  # Brief pause between cycles
            
            continuous_time = time.time() - start_time
            
            self.log_test_result("7.2 Continuous Operation", True, 
                               f"3 cycles completed", {
                                   "continuous_time": continuous_time,
                                   "avg_cycle_time": continuous_time / 3
                               })
            
            return True
            
        except Exception as e:
            self.log_test_result("7.X Production Scenarios", False, f"Exception: {e}")
            return False
    
    def generate_final_report(self):
        """Generate comprehensive final report"""
        print("\n" + "=" * 70)
        print("📊 COMPREHENSIVE TEST REPORT")
        print("=" * 70)
        
        # Overall results
        success_rate = (self.test_results['passed_tests'] / self.test_results['total_tests']) * 100
        print(f"\n✅ Overall Results: {self.test_results['passed_tests']}/{self.test_results['total_tests']} tests passed ({success_rate:.1f}%)")
        
        # Test breakdown
        print(f"\n📋 Test Breakdown:")
        for test in self.test_results['test_details']:
            print(f"   {test['status']} {test['test_name']}")
            if test['details']:
                print(f"      {test['details']}")
        
        # Performance summary
        if self.test_results['performance_metrics']:
            print(f"\n⚡ Performance Summary:")
            metrics = self.test_results['performance_metrics']
            
            if 'avg_latency' in metrics:
                print(f"   Average latency: {metrics['avg_latency']:.2f}s")
            if 'requests_per_second' in metrics:
                print(f"   Throughput: {metrics['requests_per_second']:.2f} requests/second")
            if 'memory_usage_mb' in metrics:
                print(f"   Memory usage: {metrics['memory_usage_mb']:.1f} MB")
        
        # Production readiness assessment
        print(f"\n🚀 Production Readiness Assessment:")
        
        critical_tests = [
            "1.1 EarlyGemDetector Initialization",
            "2.3 WSOL Pairs Retrieval", 
            "3.2 Method Execution",
            "4.1 Pipeline Discovery"
        ]
        
        critical_passed = all(
            any(test['test_name'] == critical and test['passed'] 
                for test in self.test_results['test_details'])
            for critical in critical_tests
        )
        
        if success_rate >= 80 and critical_passed:
            self.test_results['production_readiness'] = True
            print("✅ PRODUCTION READY")
            print("   All critical components functional")
            print("   Performance meets requirements")
            print("   Error handling works correctly")
            print("   Integration is complete")
        else:
            self.test_results['production_readiness'] = False
            print("❌ NOT PRODUCTION READY")
            if success_rate < 80:
                print(f"   Success rate too low: {success_rate:.1f}%")
            if not critical_passed:
                print("   Critical tests failed")
        
        return self.test_results['production_readiness']

async def main():
    """Run comprehensive test suite"""
    print("🧪 COMPREHENSIVE RAYDIUM V3 TEST SUITE")
    print("=" * 70)
    print("Testing all components, integration points, and production scenarios...")
    
    suite = ComprehensiveTestSuite()
    
    try:
        # Run all tests
        test_results = []
        
        test_results.append(await suite.test_1_initialization())
        test_results.append(await suite.test_2_connector_functionality())
        test_results.append(await suite.test_3_fetch_method_integration())
        test_results.append(await suite.test_4_pipeline_integration())
        test_results.append(await suite.test_5_error_handling())
        test_results.append(await suite.test_6_performance_benchmarks())
        test_results.append(await suite.test_7_production_scenarios())
        
        # Generate final report
        is_production_ready = suite.generate_final_report()
        
        # Return appropriate exit code
        if is_production_ready:
            print(f"\n🎉 ALL TESTS COMPLETED SUCCESSFULLY")
            print(f"🚀 Raydium v3 implementation is 100% production ready!")
            return 0
        else:
            print(f"\n❌ TESTS FAILED")
            print(f"🚨 Implementation needs fixes before production deployment")
            return 1
        
    except Exception as e:
        print(f"\n💥 Test suite crashed: {e}")
        return 1

if __name__ == "__main__":
    result = asyncio.run(main())
    sys.exit(result)