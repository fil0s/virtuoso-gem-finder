#!/usr/bin/env python3
"""
WSOL Integration Test Suite - PRODUCTION READY
"""

print("🧪 WSOL Integration Test Suite Starting...")

import asyncio
import json
import time
import os
import subprocess
from datetime import datetime
from pathlib import Path
import sys

# Add parent directory to path for imports
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

class WSolIntegrationTest:
    """Comprehensive WSOL integration test suite"""
    
    def __init__(self):
        self.test_results = {}
        self.start_time = datetime.now()
        
    async def run_all_tests(self):
        """Run the complete WSOL integration test suite"""
        print("🧪 WSOL Integration Test Suite")
        print("=" * 50)
        print(f"🕐 Started: {self.start_time}")
        print()
        
        # Test 1: WSOL Matrix File Availability
        await self._test_matrix_availability()
        
        # Test 2: High-Conviction Detector Integration
        await self._test_detector_integration()
        
        # Test 3: WSOL Matrix Scheduler
        await self._test_scheduler_functionality()
        
        # Test 4: Performance Monitoring
        await self._test_performance_monitoring()
        
        # Test 5: End-to-End Integration
        await self._test_end_to_end_flow()
        
        # Generate final report
        self._generate_final_report()
    
    async def _test_matrix_availability(self):
        """Test 1: Verify WSOL matrix files are available and valid"""
        print("🧪 Test 1: WSOL Matrix Availability")
        print("-" * 40)
        
        test_name = "matrix_availability"
        self.test_results[test_name] = {"status": "RUNNING", "details": []}
        
        try:
            import glob
            
            # Check for matrix files
            matrix_files = glob.glob("complete_wsol_matrix_*.json")
            
            if not matrix_files:
                self.test_results[test_name]["status"] = "FAILED"
                self.test_results[test_name]["details"].append("❌ No WSOL matrix files found")
                print("❌ FAILED: No WSOL matrix files found")
                return
            
            # Get latest file
            latest_file = max(matrix_files, key=os.path.getmtime)
            file_age = time.time() - os.path.getmtime(latest_file)
            
            print(f"✅ Found {len(matrix_files)} matrix files")
            print(f"📄 Latest file: {latest_file}")
            print(f"⏰ File age: {file_age/60:.1f} minutes")
            
            # Validate file content
            with open(latest_file, 'r') as f:
                matrix_data = json.load(f)
            
            matrix = matrix_data.get('matrix', {})
            if not matrix:
                self.test_results[test_name]["status"] = "FAILED"
                self.test_results[test_name]["details"].append("❌ Matrix file is empty")
                print("❌ FAILED: Matrix file is empty")
                return
            
            # Calculate statistics
            token_count = len(matrix)
            meteora_count = sum(1 for token in matrix.values() if token.get('meteora_available', False))
            orca_count = sum(1 for token in matrix.values() if token.get('orca_available', False))
            raydium_count = sum(1 for token in matrix.values() if token.get('raydium_available', False))
            jupiter_count = sum(1 for token in matrix.values() if token.get('jupiter_available', False))
            
            any_wsol = sum(1 for token in matrix.values() 
                          if any([token.get('meteora_available', False),
                                token.get('orca_available', False),
                                token.get('raydium_available', False),
                                token.get('jupiter_available', False)]))
            
            overall_coverage = (any_wsol / token_count) * 100 if token_count > 0 else 0
            
            print(f"📊 Matrix Statistics:")
            print(f"   🎯 Total Tokens: {token_count}")
            print(f"   🌊 Meteora: {meteora_count} ({meteora_count/token_count*100:.1f}%)")
            print(f"   🌀 Orca: {orca_count} ({orca_count/token_count*100:.1f}%)")
            print(f"   ⚡ Raydium: {raydium_count} ({raydium_count/token_count*100:.1f}%)")
            print(f"   🪐 Jupiter: {jupiter_count} ({jupiter_count/token_count*100:.1f}%)")
            print(f"   📈 Overall WSOL Coverage: {overall_coverage:.1f}%")
            
            # Validation checks
            if token_count < 50:
                self.test_results[test_name]["status"] = "WARNING"
                self.test_results[test_name]["details"].append(f"⚠️ Low token count: {token_count}")
                print(f"⚠️ WARNING: Low token count ({token_count})")
            
            if overall_coverage < 10:
                self.test_results[test_name]["status"] = "WARNING"
                self.test_results[test_name]["details"].append(f"⚠️ Low WSOL coverage: {overall_coverage:.1f}%")
                print(f"⚠️ WARNING: Low WSOL coverage ({overall_coverage:.1f}%)")
            
            if file_age > 7200:  # 2 hours
                self.test_results[test_name]["status"] = "WARNING"
                self.test_results[test_name]["details"].append(f"⚠️ Matrix file is old: {file_age/3600:.1f} hours")
                print(f"⚠️ WARNING: Matrix file is old ({file_age/3600:.1f} hours)")
            
            # Success if no failures
            if self.test_results[test_name]["status"] == "RUNNING":
                self.test_results[test_name]["status"] = "PASSED"
                self.test_results[test_name]["details"].append(f"✅ Matrix valid with {token_count} tokens and {overall_coverage:.1f}% coverage")
                print("✅ PASSED: Matrix file is valid and comprehensive")
            
        except Exception as e:
            self.test_results[test_name]["status"] = "FAILED"
            self.test_results[test_name]["details"].append(f"❌ Error: {str(e)}")
            print(f"❌ FAILED: {str(e)}")
        
        print()
    
    async def _test_detector_integration(self):
        """Test 2: Verify WSOL integration in high-conviction detector"""
        print("🧪 Test 2: High-Conviction Detector Integration")
        print("-" * 40)
        
        test_name = "detector_integration"
        self.test_results[test_name] = {"status": "RUNNING", "details": []}
        
        try:
            # Import the detector
            from scripts.high_conviction_token_detector import HighConvictionTokenDetector
            
            # Create detector instance
            detector = HighConvictionTokenDetector(debug_mode=False)
            
            # Check if WSOL methods are available
            required_methods = [
                '_load_latest_wsol_matrix',
                '_get_wsol_data', 
                '_calculate_wsol_routing_score',
                '_get_routing_recommendation'
            ]
            
            missing_methods = []
            for method_name in required_methods:
                if not hasattr(detector, method_name):
                    missing_methods.append(method_name)
            
            if missing_methods:
                self.test_results[test_name]["status"] = "FAILED"
                self.test_results[test_name]["details"].append(f"❌ Missing methods: {missing_methods}")
                print(f"❌ FAILED: Missing methods: {missing_methods}")
                return
            
            print("✅ All WSOL methods are present")
            
            # Test WSOL matrix loading
            matrix_data = detector._load_latest_wsol_matrix()
            if not matrix_data:
                self.test_results[test_name]["status"] = "WARNING"
                self.test_results[test_name]["details"].append("⚠️ Could not load WSOL matrix")
                print("⚠️ WARNING: Could not load WSOL matrix")
            else:
                print(f"✅ Successfully loaded WSOL matrix")
            
            # Test WSOL scoring with sample addresses
            test_addresses = [
                "GESaKc9LzD5PDHwFpXXjketjucGtBpsJPwYyQjHApump",  # Sample token
                "44pyqDkNbfJ9ySSXzCxGAF4E52EJ6CP7iis5b4tvpump",  # Sample token
                "invalid_address_test"  # Should return 0 score
            ]
            
            scoring_tests_passed = 0
            for address in test_addresses:
                try:
                    score, analysis = detector._calculate_wsol_routing_score(address)
                    
                    # Validate response structure
                    required_keys = ['wsol_available', 'routing_tier', 'score', 'dex_breakdown']
                    if all(key in analysis for key in required_keys):
                        scoring_tests_passed += 1
                        print(f"✅ Scoring test passed for {address[:8]}... (score: {score:.1f})")
                    else:
                        print(f"⚠️ Invalid response structure for {address[:8]}...")
                
                except Exception as e:
                    print(f"❌ Scoring failed for {address[:8]}...: {e}")
            
            if scoring_tests_passed >= 2:  # At least 2 out of 3 should work
                self.test_results[test_name]["status"] = "PASSED"
                self.test_results[test_name]["details"].append(f"✅ WSOL scoring integration working ({scoring_tests_passed}/3 tests passed)")
                print("✅ PASSED: WSOL scoring integration working")
            else:
                self.test_results[test_name]["status"] = "FAILED"
                self.test_results[test_name]["details"].append(f"❌ WSOL scoring tests failed ({scoring_tests_passed}/3 passed)")
                print(f"❌ FAILED: WSOL scoring tests failed ({scoring_tests_passed}/3 passed)")
            
        except Exception as e:
            self.test_results[test_name]["status"] = "FAILED"
            self.test_results[test_name]["details"].append(f"❌ Error: {str(e)}")
            print(f"❌ FAILED: {str(e)}")
        
        print()
    
    async def _test_scheduler_functionality(self):
        """Test 3: Verify WSOL matrix scheduler functionality"""
        print("🧪 Test 3: WSOL Matrix Scheduler")
        print("-" * 40)
        
        test_name = "scheduler_functionality"
        self.test_results[test_name] = {"status": "RUNNING", "details": []}
        
        try:
            # Check if scheduler files exist
            scheduler_script = Path("services/wsol_matrix_scheduler.py")
            daemon_script = Path("run_wsol_matrix_scheduler.sh")
            
            if not scheduler_script.exists():
                self.test_results[test_name]["status"] = "FAILED"
                self.test_results[test_name]["details"].append("❌ Scheduler script not found")
                print("❌ FAILED: Scheduler script not found")
                return
            
            if not daemon_script.exists():
                self.test_results[test_name]["status"] = "FAILED"
                self.test_results[test_name]["details"].append("❌ Daemon script not found")
                print("❌ FAILED: Daemon script not found")
                return
            
            print("✅ Scheduler files found")
            
            # Test scheduler import
            from services.wsol_matrix_scheduler import WSolMatrixScheduler
            
            # Create scheduler instance
            scheduler = WSolMatrixScheduler(refresh_interval_minutes=1)  # Short interval for testing
            
            # Test performance summary (should work even without running)
            performance = scheduler.get_performance_summary()
            
            required_keys = ['scheduler_status', 'refresh_statistics', 'performance_metrics', 'system_health']
            if all(key in performance for key in required_keys):
                print("✅ Performance summary structure is valid")
            else:
                print("⚠️ Performance summary structure is incomplete")
            
            # Test health status
            health = scheduler.get_health_status()
            if health in ['STARTING', 'HEALTHY', 'DEGRADED', 'UNHEALTHY']:
                print(f"✅ Health status is valid: {health}")
            else:
                print(f"⚠️ Invalid health status: {health}")
            
            # Test daemon script functionality (dry run)
            result = subprocess.run(
                ['./run_wsol_matrix_scheduler.sh', 'status'],
                capture_output=True,
                text=True,
                timeout=10
            )
            
            if result.returncode == 0 or "NOT RUNNING" in result.stdout:
                print("✅ Daemon script is functional")
                self.test_results[test_name]["status"] = "PASSED"
                self.test_results[test_name]["details"].append("✅ Scheduler functionality verified")
            else:
                print(f"⚠️ Daemon script issues: {result.stderr}")
                self.test_results[test_name]["status"] = "WARNING"
                self.test_results[test_name]["details"].append("⚠️ Daemon script has issues")
            
        except Exception as e:
            self.test_results[test_name]["status"] = "FAILED"
            self.test_results[test_name]["details"].append(f"❌ Error: {str(e)}")
            print(f"❌ FAILED: {str(e)}")
        
        print()
    
    async def _test_performance_monitoring(self):
        """Test 4: Verify performance monitoring capabilities"""
        print("🧪 Test 4: Performance Monitoring")
        print("-" * 40)
        
        test_name = "performance_monitoring"
        self.test_results[test_name] = {"status": "RUNNING", "details": []}
        
        try:
            # Test matrix builder performance
            print("🔄 Testing matrix builder performance...")
            
            start_time = time.time()
            result = subprocess.run(
                ['python3', 'optimized_wsol_matrix_builder.py'],
                capture_output=True,
                text=True,
                timeout=120  # 2 minute timeout for testing
            )
            duration = time.time() - start_time
            
            if result.returncode == 0:
                print(f"✅ Matrix builder completed in {duration:.1f}s")
                
                # Performance thresholds
                if duration < 30:
                    performance_grade = "EXCELLENT"
                elif duration < 60:
                    performance_grade = "GOOD"
                elif duration < 120:
                    performance_grade = "ACCEPTABLE"
                else:
                    performance_grade = "SLOW"
                
                print(f"📊 Performance Grade: {performance_grade}")
                
                # Check output quality
                output_lines = result.stdout.split('\n')
                has_performance_metrics = any('tokens/second' in line for line in output_lines)
                has_coverage_stats = any('coverage' in line.lower() for line in output_lines)
                
                if has_performance_metrics and has_coverage_stats:
                    print("✅ Performance metrics and coverage stats present")
                    quality_score = "HIGH"
                else:
                    print("⚠️ Missing some performance metrics")
                    quality_score = "MEDIUM"
                
                self.test_results[test_name]["status"] = "PASSED"
                self.test_results[test_name]["details"].append(
                    f"✅ Performance: {performance_grade} ({duration:.1f}s), Quality: {quality_score}"
                )
                
            else:
                print(f"❌ Matrix builder failed: {result.stderr}")
                self.test_results[test_name]["status"] = "FAILED"
                self.test_results[test_name]["details"].append(f"❌ Matrix builder failed")
            
        except subprocess.TimeoutExpired:
            print("❌ Matrix builder timed out (>2 minutes)")
            self.test_results[test_name]["status"] = "FAILED"
            self.test_results[test_name]["details"].append("❌ Performance too slow (timeout)")
            
        except Exception as e:
            self.test_results[test_name]["status"] = "FAILED"
            self.test_results[test_name]["details"].append(f"❌ Error: {str(e)}")
            print(f"❌ FAILED: {str(e)}")
        
        print()
    
    async def _test_end_to_end_flow(self):
        """Test 5: End-to-end integration flow"""
        print("🧪 Test 5: End-to-End Integration Flow")
        print("-" * 40)
        
        test_name = "end_to_end_flow"
        self.test_results[test_name] = {"status": "RUNNING", "details": []}
        
        try:
            # Step 1: Ensure fresh WSOL matrix exists
            import glob
            matrix_files = glob.glob("complete_wsol_matrix_*.json")
            
            if matrix_files:
                latest_file = max(matrix_files, key=os.path.getmtime)
                print(f"✅ Step 1: WSOL matrix available ({latest_file})")
            else:
                print("❌ Step 1: No WSOL matrix available")
                self.test_results[test_name]["status"] = "FAILED"
                return
            
            # Step 2: Test high-conviction detector can load matrix and calculate scores
            from scripts.high_conviction_token_detector import HighConvictionTokenDetector
            detector = HighConvictionTokenDetector(debug_mode=False)
            
            # Load matrix and test scoring
            matrix_data = detector._load_latest_wsol_matrix()
            if matrix_data:
                print("✅ Step 2: Detector successfully loaded WSOL matrix")
                
                # Test scoring integration in traditional components
                test_candidate = {
                    'address': 'GESaKc9LzD5PDHwFpXXjketjucGtBpsJPwYyQjHApump',
                    'platforms': ['birdeye', 'dexscreener']
                }
                
                # Test traditional components calculation (includes WSOL scoring)
                traditional_components = detector._calculate_traditional_components(
                    test_candidate, {}, {}, {}, {}, {}, {}, {}, {}
                )
                
                if 'wsol_score' in traditional_components:
                    wsol_score = traditional_components['wsol_score']
                    print(f"✅ Step 3: WSOL scoring integrated (score: {wsol_score:.1f})")
                else:
                    print("❌ Step 3: WSOL scoring not integrated")
                    self.test_results[test_name]["status"] = "FAILED"
                    return
                
            else:
                print("❌ Step 2: Detector failed to load WSOL matrix")
                self.test_results[test_name]["status"] = "FAILED"
                return
            
            # Step 3: Test scheduler integration
            from services.wsol_matrix_scheduler import WSolMatrixScheduler
            scheduler = WSolMatrixScheduler(refresh_interval_minutes=45)
            
            # Test matrix analysis
            analysis = scheduler._analyze_latest_matrix()
            if analysis and analysis.get('token_count', 0) > 0:
                print(f"✅ Step 4: Scheduler can analyze matrix ({analysis['token_count']} tokens)")
            else:
                print("⚠️ Step 4: Scheduler matrix analysis incomplete")
            
            # Step 4: Performance validation
            performance = scheduler.get_performance_summary()
            if performance:
                print("✅ Step 5: Performance monitoring operational")
            else:
                print("⚠️ Step 5: Performance monitoring issues")
            
            # Final integration check
            end_to_end_score = 0
            if matrix_files:
                end_to_end_score += 25  # Matrix available
            if 'wsol_score' in traditional_components:
                end_to_end_score += 25  # WSOL scoring integrated
            if matrix_data:
                end_to_end_score += 25  # Detector integration working
            if analysis:
                end_to_end_score += 25  # Scheduler working
            
            if end_to_end_score >= 75:
                self.test_results[test_name]["status"] = "PASSED"
                self.test_results[test_name]["details"].append(f"✅ End-to-end integration working ({end_to_end_score}% complete)")
                print(f"✅ PASSED: End-to-end integration working ({end_to_end_score}% complete)")
            else:
                self.test_results[test_name]["status"] = "FAILED"
                self.test_results[test_name]["details"].append(f"❌ End-to-end integration incomplete ({end_to_end_score}% complete)")
                print(f"❌ FAILED: End-to-end integration incomplete ({end_to_end_score}% complete)")
            
        except Exception as e:
            self.test_results[test_name]["status"] = "FAILED"
            self.test_results[test_name]["details"].append(f"❌ Error: {str(e)}")
            print(f"❌ FAILED: {str(e)}")
        
        print()
    
    def _generate_final_report(self):
        """Generate final test report"""
        print("📊 WSOL Integration Test Report")
        print("=" * 50)
        
        total_tests = len(self.test_results)
        passed_tests = sum(1 for result in self.test_results.values() if result['status'] == 'PASSED')
        failed_tests = sum(1 for result in self.test_results.values() if result['status'] == 'FAILED')
        warning_tests = sum(1 for result in self.test_results.values() if result['status'] == 'WARNING')
        
        print(f"📈 Test Summary:")
        print(f"   ✅ Passed: {passed_tests}/{total_tests}")
        print(f"   ❌ Failed: {failed_tests}/{total_tests}")
        print(f"   ⚠️  Warnings: {warning_tests}/{total_tests}")
        
        success_rate = (passed_tests / total_tests) * 100 if total_tests > 0 else 0
        print(f"   📊 Success Rate: {success_rate:.1f}%")
        
        print(f"\n🕐 Duration: {datetime.now() - self.start_time}")
        
        print(f"\n📋 Detailed Results:")
        for test_name, result in self.test_results.items():
            status_icon = {"PASSED": "✅", "FAILED": "❌", "WARNING": "⚠️"}.get(result['status'], "❓")
            print(f"   {status_icon} {test_name}: {result['status']}")
            for detail in result['details']:
                print(f"      {detail}")
        
        # Overall integration status
        if passed_tests == total_tests:
            overall_status = "🎉 EXCELLENT - All tests passed!"
        elif passed_tests >= total_tests * 0.8:
            overall_status = "✅ GOOD - Most tests passed, minor issues"
        elif passed_tests >= total_tests * 0.6:
            overall_status = "⚠️ FAIR - Some issues need attention"
        else:
            overall_status = "❌ POOR - Significant issues need fixing"
        
        print(f"\n🎯 Overall Status: {overall_status}")
        
        # Save results to file
        report_file = f"wsol_integration_test_report_{int(time.time())}.json"
        with open(report_file, 'w') as f:
            json.dump({
                'timestamp': datetime.now().isoformat(),
                'duration_seconds': (datetime.now() - self.start_time).total_seconds(),
                'summary': {
                    'total_tests': total_tests,
                    'passed': passed_tests,
                    'failed': failed_tests,
                    'warnings': warning_tests,
                    'success_rate': success_rate
                },
                'results': self.test_results,
                'overall_status': overall_status
            }, indent=2)
        
        print(f"\n💾 Report saved to: {report_file}")

async def main():
    """Run the WSOL integration test suite"""
    tester = WSolIntegrationTest()
    await tester.run_all_tests()

if __name__ == "__main__":
    asyncio.run(main()) 