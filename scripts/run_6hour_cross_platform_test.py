#!/usr/bin/env python3
"""
6-Hour Cross-Platform Token Analyzer Test
=========================================

Runs the cross-platform token analyzer continuously for 6 hours with:
- Regular analysis intervals (every 15 minutes)
- Performance monitoring
- Cost tracking
- Error handling and recovery
- Comprehensive reporting
"""

import asyncio
import json
import logging
import os
import time
from datetime import datetime, timedelta
from typing import Dict, List, Any
import traceback

# Import the analyzer
from cross_platform_token_analyzer import CrossPlatformAnalyzer

class SixHourTestRunner:
    """Manages a 6-hour continuous test of the cross-platform analyzer"""
    
    def __init__(self):
        self.start_time = time.time()
        self.end_time = self.start_time + (6 * 3600)  # 6 hours
        self.analysis_interval = 15 * 60  # 15 minutes
        self.results = []
        self.errors = []
        self.performance_stats = {
            'total_runs': 0,
            'successful_runs': 0,
            'failed_runs': 0,
            'total_execution_time': 0,
            'total_tokens_analyzed': 0,
            'total_high_conviction_tokens': 0,
            'total_api_calls': 0,
            'total_cost_savings': 0.0
        }
        
        # Set up logging
        self.setup_logging()
        self.logger = logging.getLogger('SixHourTest')
        
    def setup_logging(self):
        """Configure comprehensive logging for the test"""
        log_dir = "logs"
        os.makedirs(log_dir, exist_ok=True)
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        log_file = f"{log_dir}/cross_platform_6hour_test_{timestamp}.log"
        
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler(log_file),
                logging.StreamHandler()
            ]
        )
        
        self.logger = logging.getLogger('SixHourTest')
        self.logger.info(f"🚀 Starting 6-hour cross-platform analyzer test")
        self.logger.info(f"📝 Logging to: {log_file}")
        self.logger.info(f"⏰ Test duration: 6 hours (until {datetime.fromtimestamp(self.end_time)})")
        self.logger.info(f"🔄 Analysis interval: {self.analysis_interval // 60} minutes")
    
    async def run_single_analysis(self, run_number: int) -> Dict[str, Any]:
        """Run a single analysis cycle"""
        self.logger.info(f"🔍 Starting analysis run #{run_number}")
        
        analyzer = None
        try:
            # Initialize analyzer
            analyzer = CrossPlatformAnalyzer()
            
            # Run analysis
            start_time = time.time()
            results = await analyzer.run_analysis()
            execution_time = time.time() - start_time
            
            # Update performance stats
            self.performance_stats['total_runs'] += 1
            self.performance_stats['total_execution_time'] += execution_time
            
            if 'error' not in results:
                self.performance_stats['successful_runs'] += 1
                self.performance_stats['total_tokens_analyzed'] += results['correlations']['total_tokens']
                self.performance_stats['total_high_conviction_tokens'] += len(results['correlations']['high_conviction_tokens'])
                
                # Track cost savings
                cache_stats = results.get('cache_statistics', {})
                if 'estimated_cost_savings_usd' in cache_stats:
                    self.performance_stats['total_cost_savings'] += cache_stats['estimated_cost_savings_usd']
            else:
                self.performance_stats['failed_runs'] += 1
                self.errors.append({
                    'run_number': run_number,
                    'timestamp': datetime.now().isoformat(),
                    'error': results['error']
                })
            
            # Add run metadata
            results['run_number'] = run_number
            results['test_elapsed_hours'] = (time.time() - self.start_time) / 3600
            
            self.logger.info(f"✅ Run #{run_number} completed in {execution_time:.2f}s")
            return results
            
        except Exception as e:
            self.performance_stats['total_runs'] += 1
            self.performance_stats['failed_runs'] += 1
            
            error_details = {
                'run_number': run_number,
                'timestamp': datetime.now().isoformat(),
                'error': str(e),
                'traceback': traceback.format_exc()
            }
            self.errors.append(error_details)
            
            self.logger.error(f"❌ Run #{run_number} failed: {e}")
            self.logger.debug(f"Traceback: {traceback.format_exc()}")
            
            return {
                'run_number': run_number,
                'timestamp': datetime.now().isoformat(),
                'error': str(e),
                'test_elapsed_hours': (time.time() - self.start_time) / 3600
            }
        finally:
            if analyzer:
                try:
                    await analyzer.close()
                except Exception as e:
                    self.logger.warning(f"Error closing analyzer: {e}")
    
    def log_progress_summary(self, run_number: int):
        """Log a progress summary"""
        elapsed_hours = (time.time() - self.start_time) / 3600
        remaining_hours = max(0, 6 - elapsed_hours)
        
        self.logger.info("📊 Progress Summary")
        self.logger.info(f"   ⏰ Elapsed: {elapsed_hours:.2f}h / Remaining: {remaining_hours:.2f}h")
        self.logger.info(f"   🔄 Runs: {self.performance_stats['total_runs']} total")
        self.logger.info(f"   ✅ Success: {self.performance_stats['successful_runs']}")
        self.logger.info(f"   ❌ Failed: {self.performance_stats['failed_runs']}")
        
        if self.performance_stats['successful_runs'] > 0:
            avg_execution = self.performance_stats['total_execution_time'] / self.performance_stats['successful_runs']
            avg_tokens = self.performance_stats['total_tokens_analyzed'] / self.performance_stats['successful_runs']
            
            self.logger.info(f"   ⚡ Avg execution: {avg_execution:.2f}s")
            self.logger.info(f"   🎯 Avg tokens: {avg_tokens:.1f}")
            self.logger.info(f"   💎 Total high-conviction: {self.performance_stats['total_high_conviction_tokens']}")
            self.logger.info(f"   💰 Total savings: ${self.performance_stats['total_cost_savings']:.4f}")
    
    async def run_test(self):
        """Run the complete 6-hour test"""
        run_number = 1
        next_analysis_time = time.time()
        
        self.logger.info("🎯 Starting continuous analysis loop")
        
        try:
            while time.time() < self.end_time:
                current_time = time.time()
                
                # Check if it's time for the next analysis
                if current_time >= next_analysis_time:
                    # Run analysis
                    results = await self.run_single_analysis(run_number)
                    self.results.append(results)
                    
                    # Log progress every 5 runs
                    if run_number % 5 == 0:
                        self.log_progress_summary(run_number)
                    
                    # Schedule next analysis
                    next_analysis_time = current_time + self.analysis_interval
                    run_number += 1
                
                # Wait before checking again (1 minute intervals)
                await asyncio.sleep(60)
                
        except KeyboardInterrupt:
            self.logger.info("🛑 Test interrupted by user")
        except Exception as e:
            self.logger.error(f"💥 Test failed with unexpected error: {e}")
            self.logger.debug(f"Traceback: {traceback.format_exc()}")
        
        # Generate final report
        await self.generate_final_report()
    
    async def generate_final_report(self):
        """Generate comprehensive final report"""
        total_elapsed = time.time() - self.start_time
        
        self.logger.info("📋 Generating final test report...")
        
        # Calculate final statistics
        success_rate = (self.performance_stats['successful_runs'] / max(1, self.performance_stats['total_runs'])) * 100
        
        if self.performance_stats['successful_runs'] > 0:
            avg_execution_time = self.performance_stats['total_execution_time'] / self.performance_stats['successful_runs']
            avg_tokens_per_run = self.performance_stats['total_tokens_analyzed'] / self.performance_stats['successful_runs']
        else:
            avg_execution_time = 0
            avg_tokens_per_run = 0
        
        # Compile final report
        final_report = {
            'test_summary': {
                'start_time': datetime.fromtimestamp(self.start_time).isoformat(),
                'end_time': datetime.now().isoformat(),
                'total_duration_hours': total_elapsed / 3600,
                'planned_duration_hours': 6.0,
                'completed_early': total_elapsed < (6 * 3600 - 300)  # Allow 5 min tolerance
            },
            'performance_statistics': {
                **self.performance_stats,
                'success_rate_percent': success_rate,
                'average_execution_time_seconds': avg_execution_time,
                'average_tokens_per_run': avg_tokens_per_run,
                'total_duration_seconds': total_elapsed
            },
            'errors': self.errors,
            'detailed_results': self.results
        }
        
        # Save comprehensive report
        timestamp = int(self.start_time)
        report_file = f"scripts/results/cross_platform_6hour_test_report_{timestamp}.json"
        
        os.makedirs("scripts/results", exist_ok=True)
        with open(report_file, 'w') as f:
            json.dump(final_report, f, indent=2)
        
        # Print final summary
        print("\n" + "=" * 60)
        print("🎯 6-HOUR CROSS-PLATFORM ANALYZER TEST COMPLETE")
        print("=" * 60)
        print(f"⏰ Duration: {total_elapsed / 3600:.2f} hours")
        print(f"🔄 Total runs: {self.performance_stats['total_runs']}")
        print(f"✅ Successful: {self.performance_stats['successful_runs']} ({success_rate:.1f}%)")
        print(f"❌ Failed: {self.performance_stats['failed_runs']}")
        print(f"⚡ Avg execution time: {avg_execution_time:.2f}s")
        print(f"🎯 Total tokens analyzed: {self.performance_stats['total_tokens_analyzed']}")
        print(f"💎 Total high-conviction tokens: {self.performance_stats['total_high_conviction_tokens']}")
        print(f"💰 Total estimated savings: ${self.performance_stats['total_cost_savings']:.4f}")
        print(f"📁 Full report saved to: {report_file}")
        
        if self.errors:
            print(f"\n⚠️  Errors encountered: {len(self.errors)}")
            print("Recent errors:")
            for error in self.errors[-3:]:  # Show last 3 errors
                print(f"  • Run #{error['run_number']}: {error['error']}")
        
        print("\n🚀 Test completed successfully!")

async def main():
    """Main entry point"""
    test_runner = SixHourTestRunner()
    await test_runner.run_test()

if __name__ == "__main__":
    asyncio.run(main()) 