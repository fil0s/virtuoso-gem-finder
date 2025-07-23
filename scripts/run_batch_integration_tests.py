#!/usr/bin/env python3
"""
Batch Integration Test Runner

This script runs the complete batch integration test suite including:
1. Performance monitoring setup
2. Integration tests with existing token discovery strategies
3. Performance validation and reporting
"""

import asyncio
import subprocess
import sys
import os
import time
from pathlib import Path

def run_command(command: str, description: str) -> bool:
    """Run a command and return success status."""
    print(f"\n🔄 {description}")
    print(f"Command: {command}")
    
    try:
        result = subprocess.run(
            command.split(),
            capture_output=True,
            text=True,
            cwd=Path(__file__).parent.parent
        )
        
        if result.returncode == 0:
            print(f"✅ {description} - SUCCESS")
            if result.stdout:
                print("Output:")
                print(result.stdout)
            return True
        else:
            print(f"❌ {description} - FAILED")
            if result.stderr:
                print("Error:")
                print(result.stderr)
            return False
            
    except Exception as e:
        print(f"❌ {description} - FAILED with exception: {e}")
        return False

async def main():
    """Main test runner execution."""
    print("🚀 Batch Integration Test Suite")
    print("=" * 50)
    print("This will test the integration of batch processing with existing token discovery strategies")
    print("and validate performance improvements.")
    
    start_time = time.time()
    
    # Test results tracking
    test_results = []
    
    # Step 1: Setup performance monitoring
    print("\n" + "=" * 50)
    print("STEP 1: Setting up Performance Monitoring")
    print("=" * 50)
    
    setup_success = run_command(
        "python scripts/setup_performance_monitoring.py",
        "Setting up performance monitoring system"
    )
    test_results.append(("Performance Monitoring Setup", setup_success))
    
    if not setup_success:
        print("⚠️ Performance monitoring setup failed, but continuing with tests...")
    
    # Step 2: Run integration tests
    print("\n" + "=" * 50)
    print("STEP 2: Running Batch Integration Tests")
    print("=" * 50)
    
    integration_success = run_command(
        "python scripts/test_batch_integration_performance.py",
        "Running batch integration performance tests"
    )
    test_results.append(("Batch Integration Tests", integration_success))
    
    # Step 3: Run existing cost optimization tests (if they exist)
    print("\n" + "=" * 50)
    print("STEP 3: Running Cost Optimization Tests")
    print("=" * 50)
    
    cost_test_files = [
        "scripts/test_birdeye_cost_calculator.py",
        "scripts/test_enhanced_cost_optimization.py"
    ]
    
    for test_file in cost_test_files:
        if Path(test_file).exists():
            test_name = Path(test_file).stem.replace('_', ' ').title()
            cost_success = run_command(
                f"python {test_file}",
                f"Running {test_name}"
            )
            test_results.append((test_name, cost_success))
        else:
            print(f"⚠️ Test file {test_file} not found, skipping...")
    
    # Step 4: Generate comprehensive report
    print("\n" + "=" * 50)
    print("STEP 4: Generating Test Report")
    print("=" * 50)
    
    total_time = time.time() - start_time
    
    # Calculate success rate
    passed_tests = sum(1 for _, success in test_results if success)
    total_tests = len(test_results)
    success_rate = (passed_tests / total_tests) * 100 if total_tests > 0 else 0
    
    print(f"\n🎯 TEST SUITE SUMMARY")
    print("=" * 30)
    print(f"Total Tests: {total_tests}")
    print(f"Passed: {passed_tests}")
    print(f"Failed: {total_tests - passed_tests}")
    print(f"Success Rate: {success_rate:.1f}%")
    print(f"Total Time: {total_time:.1f} seconds")
    
    print(f"\n📊 DETAILED RESULTS:")
    for test_name, success in test_results:
        status = "✅ PASS" if success else "❌ FAIL"
        print(f"  • {test_name}: {status}")
    
    # Recommendations based on results
    print(f"\n💡 RECOMMENDATIONS:")
    
    if success_rate >= 80:
        print("  🎉 Excellent! Batch integration is working well.")
        print("  🚀 Ready for production deployment.")
        print("  📈 Monitor performance metrics in production.")
    elif success_rate >= 60:
        print("  ⚠️ Good progress, but some issues need attention.")
        print("  🔧 Review failed tests and fix issues.")
        print("  🧪 Re-run tests after fixes.")
    else:
        print("  🚨 Significant issues detected.")
        print("  🔍 Review all failed tests carefully.")
        print("  🛠️ Fix critical issues before deployment.")
    
    # Next steps
    print(f"\n🚀 NEXT STEPS:")
    print("  1. Review any failed tests and fix issues")
    print("  2. Check performance monitoring configuration")
    print("  3. Run monitor with batch processing enabled")
    print("  4. Monitor cost savings and performance improvements")
    print("  5. Adjust batch sizes and thresholds as needed")
    
    # Create summary file
    summary_file = Path("data/test_results") / f"batch_integration_summary_{int(time.time())}.txt"
    summary_file.parent.mkdir(parents=True, exist_ok=True)
    
    with open(summary_file, 'w') as f:
        f.write("Batch Integration Test Suite Summary\n")
        f.write("=" * 40 + "\n\n")
        f.write(f"Execution Time: {time.ctime()}\n")
        f.write(f"Total Duration: {total_time:.1f} seconds\n")
        f.write(f"Success Rate: {success_rate:.1f}%\n\n")
        
        f.write("Test Results:\n")
        for test_name, success in test_results:
            status = "PASS" if success else "FAIL"
            f.write(f"  {test_name}: {status}\n")
    
    print(f"\n📄 Summary saved to: {summary_file}")
    
    # Exit with appropriate code
    if success_rate >= 80:
        print("\n🎉 Test suite completed successfully!")
        sys.exit(0)
    else:
        print("\n⚠️ Test suite completed with issues. Please review failed tests.")
        sys.exit(1)

if __name__ == '__main__':
    asyncio.run(main()) 