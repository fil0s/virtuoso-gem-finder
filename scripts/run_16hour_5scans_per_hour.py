#!/usr/bin/env python3
"""
12-Hour High Conviction Detector Test - Enhanced with Comprehensive Reporting
Runs 5 scans per hour (every 12 minutes) for 12 hours
Total: 60 scans over 12 hours

Enhanced Features:
- API usage tracking by provider
- Cost analysis and optimization data
- Detailed token analysis preservation
- Performance bottleneck identification
- Error pattern analysis
"""

import sys
import os
import time
import json
import signal
import asyncio
import traceback
import psutil
from datetime import datetime, timedelta
from pathlib import Path
from collections import defaultdict
from typing import Dict, List, Any, Optional

# Add project root to Python path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from scripts.high_conviction_token_detector import HighConvictionTokenDetector
from utils.logger_setup import LoggerSetup

class EnhancedTwelveHourDetectorTest:
    def __init__(self):
        self.detector = HighConvictionTokenDetector()
        self.start_time = datetime.now()
        self.session_id = f"12h_enhanced_{int(time.time())}"
        self.scan_interval = 12 * 60  # 12 minutes = 720 seconds
        self.total_duration = 12 * 60 * 60  # 12 hours in seconds
        self.total_scans = 60  # 5 scans per hour × 12 hours
        self.completed_scans = 0
        
        # Enhanced session statistics with comprehensive tracking
        self.session_stats = {
            'start_time': self.start_time.isoformat(),
            'session_id': self.session_id,
            'scan_interval_minutes': 12,
            'total_planned_scans': self.total_scans,
            'total_duration_hours': 12,
            'scans': [],
            'tokens_discovered': {},
            
            # Enhanced API tracking by provider
            'api_usage_by_provider': {
                'birdeye': {
                    'total_calls': 0,
                    'successful_calls': 0,
                    'failed_calls': 0,
                    'total_response_time_ms': 0,
                    'avg_response_time_ms': 0,
                    'endpoints': defaultdict(lambda: {
                        'calls': 0, 'successes': 0, 'failures': 0, 
                        'total_time_ms': 0, 'avg_time_ms': 0
                    }),
                    'rate_limit_hits': 0,
                    'estimated_cost_usd': 0.0
                },
                'dexscreener': {
                    'total_calls': 0,
                    'successful_calls': 0,
                    'failed_calls': 0,
                    'total_response_time_ms': 0,
                    'avg_response_time_ms': 0,
                    'endpoints': defaultdict(lambda: {
                        'calls': 0, 'successes': 0, 'failures': 0,
                        'total_time_ms': 0, 'avg_time_ms': 0
                    }),
                    'estimated_cost_usd': 0.0
                },
                'rugcheck': {
                'total_calls': 0,
                'successful_calls': 0,
                'failed_calls': 0,
                    'total_response_time_ms': 0,
                    'avg_response_time_ms': 0,
                    'estimated_cost_usd': 0.0
                }
            },
            
            # Cost analysis and optimization
            'cost_analysis': {
                'total_estimated_cost_usd': 0.0,
                'cost_per_scan_avg': 0.0,
                'cost_per_token_discovered': 0.0,
                'cost_per_high_conviction_token': 0.0,
                'cost_breakdown_by_stage': {
                    'cross_platform_analysis': 0.0,
                    'detailed_birdeye_analysis': 0.0,
                    'whale_analysis': 0.0,
                    'volume_analysis': 0.0,
                    'security_analysis': 0.0,
                    'community_analysis': 0.0
                },
                'optimization_recommendations': []
            },
            
            # Performance bottleneck identification
            'performance_analysis': {
                'avg_scan_duration': 0,
                'pipeline_stage_durations': {
                    'cross_platform_analysis_ms': [],
                    'detailed_analysis_ms': [],
                    'whale_analysis_ms': [],
                    'volume_analysis_ms': [],
                    'security_analysis_ms': [],
                    'community_analysis_ms': [],
                    'scoring_calculation_ms': [],
                    'alert_generation_ms': []
                },
                'bottlenecks_identified': [],
                'system_resource_usage': {
                    'peak_memory_mb': 0,
                    'avg_cpu_percent': 0,
                    'disk_io_mb': 0
                },
                'slowest_scans': [],
                'fastest_scans': []
            },
            
            # Error pattern analysis
            'error_analysis': {
                'total_errors': 0,
                'errors_by_provider': defaultdict(int),
                'errors_by_endpoint': defaultdict(int),
                'errors_by_type': defaultdict(int),
                'error_patterns': [],
                'recovery_success_rate': 0.0,
                'consecutive_failures': 0,
                'max_consecutive_failures': 0,
                'error_timeline': []
            },
            
            # Enhanced performance metrics
            'performance_metrics': {
                'avg_scan_duration': 0,
                'total_tokens_found': 0,
                'unique_tokens': 0,
                'high_conviction_tokens': 0,
                'tokens_per_hour': 0,
                'high_conviction_rate': 0.0,
                'scan_success_rate': 0.0,
                'api_efficiency_score': 0.0
            },
            
            # Detailed token analysis preservation
            'detailed_token_analyses': {}
        }
        
        # Setup logging
        self.logger_setup = LoggerSetup('12hour_enhanced_detector_test')
        self.logger = self.logger_setup.logger
        
        # Setup graceful shutdown
        signal.signal(signal.SIGINT, self._signal_handler)
        signal.signal(signal.SIGTERM, self._signal_handler)
        
        self.running = True
        self.process = psutil.Process()
        
    def _signal_handler(self, signum, frame):
        """Handle graceful shutdown"""
        self.logger.info(f"\n🛑 Received signal {signum}. Initiating graceful shutdown...")
        self.running = False
        self._save_session_results()
        
    def _save_session_results(self):
        """Save comprehensive session results to file"""
        results_dir = project_root / "scripts" / "results"
        results_dir.mkdir(exist_ok=True)
        
        results_file = results_dir / f"12hour_enhanced_results_{self.session_id}.json"
        
        # Update final stats
        self.session_stats['end_time'] = datetime.now().isoformat()
        self.session_stats['actual_duration_minutes'] = (datetime.now() - self.start_time).total_seconds() / 60
        self.session_stats['completed_scans'] = self.completed_scans
        self.session_stats['completion_rate'] = (self.completed_scans / self.total_scans) * 100
        
        # Calculate final performance metrics
        self._calculate_final_metrics()
        
        # Generate optimization recommendations
        self._generate_optimization_recommendations()
        
        # Convert defaultdict to regular dict for JSON serialization
        self._convert_defaultdicts_for_json()
        
        with open(results_file, 'w') as f:
            json.dump(self.session_stats, f, indent=2, default=str)
            
        self.logger.info(f"📊 Enhanced session results saved to: {results_file}")
        
        # Also save a summary report
        self._save_summary_report(results_dir)
        
    def _convert_defaultdicts_for_json(self):
        """Convert defaultdict objects to regular dicts for JSON serialization"""
        def convert_defaultdict(obj):
            if isinstance(obj, defaultdict):
                return dict(obj)
            elif isinstance(obj, dict):
                return {k: convert_defaultdict(v) for k, v in obj.items()}
            elif isinstance(obj, list):
                return [convert_defaultdict(item) for item in obj]
            else:
                return obj
        
        self.session_stats = convert_defaultdict(self.session_stats)
        
    def _save_summary_report(self, results_dir: Path):
        """Save a human-readable summary report"""
        summary_file = results_dir / f"12hour_summary_{self.session_id}.txt"
        
        with open(summary_file, 'w') as f:
            f.write("="*80 + "\n")
            f.write("12-HOUR ENHANCED HIGH CONVICTION DETECTOR TEST SUMMARY\n")
            f.write("="*80 + "\n\n")
            
            # Basic stats
            f.write(f"Session ID: {self.session_id}\n")
            f.write(f"Duration: {self.session_stats.get('actual_duration_minutes', 0):.1f} minutes\n")
            f.write(f"Completed Scans: {self.completed_scans}/{self.total_scans}\n")
            f.write(f"Success Rate: {self.session_stats['performance_metrics']['scan_success_rate']:.1f}%\n\n")
            
            # Token discovery
            f.write("TOKEN DISCOVERY:\n")
            f.write(f"- Total Tokens Found: {self.session_stats['performance_metrics']['total_tokens_found']}\n")
            f.write(f"- Unique Tokens: {self.session_stats['performance_metrics']['unique_tokens']}\n")
            f.write(f"- High Conviction Tokens: {self.session_stats['performance_metrics']['high_conviction_tokens']}\n")
            f.write(f"- High Conviction Rate: {self.session_stats['performance_metrics']['high_conviction_rate']:.1f}%\n\n")
            
            # API usage
            f.write("API USAGE SUMMARY:\n")
            for provider, stats in self.session_stats['api_usage_by_provider'].items():
                f.write(f"- {provider.upper()}:\n")
                f.write(f"  Total Calls: {stats['total_calls']}\n")
                f.write(f"  Success Rate: {(stats['successful_calls']/max(stats['total_calls'], 1)*100):.1f}%\n")
                f.write(f"  Avg Response Time: {stats['avg_response_time_ms']:.0f}ms\n")
                f.write(f"  Estimated Cost: ${stats['estimated_cost_usd']:.4f}\n\n")
            
            # Cost analysis
            f.write("COST ANALYSIS:\n")
            f.write(f"- Total Estimated Cost: ${self.session_stats['cost_analysis']['total_estimated_cost_usd']:.4f}\n")
            f.write(f"- Cost per Scan: ${self.session_stats['cost_analysis']['cost_per_scan_avg']:.4f}\n")
            f.write(f"- Cost per Token: ${self.session_stats['cost_analysis']['cost_per_token_discovered']:.4f}\n\n")
            
            # Performance
            f.write("PERFORMANCE ANALYSIS:\n")
            f.write(f"- Average Scan Duration: {self.session_stats['performance_metrics']['avg_scan_duration']:.1f}s\n")
            f.write(f"- Peak Memory Usage: {self.session_stats['performance_analysis']['system_resource_usage']['peak_memory_mb']:.1f}MB\n")
            f.write(f"- API Efficiency Score: {self.session_stats['performance_metrics']['api_efficiency_score']:.1f}/100\n\n")
            
            # Errors
            f.write("ERROR ANALYSIS:\n")
            f.write(f"- Total Errors: {self.session_stats['error_analysis']['total_errors']}\n")
            f.write(f"- Recovery Success Rate: {self.session_stats['error_analysis']['recovery_success_rate']:.1f}%\n")
            f.write(f"- Max Consecutive Failures: {self.session_stats['error_analysis']['max_consecutive_failures']}\n\n")
            
            # Optimization recommendations
            f.write("OPTIMIZATION RECOMMENDATIONS:\n")
            for i, rec in enumerate(self.session_stats['cost_analysis']['optimization_recommendations'], 1):
                f.write(f"{i}. {rec}\n")
                
        self.logger.info(f"📋 Summary report saved to: {summary_file}")
        
    def _calculate_final_metrics(self):
        """Calculate final performance and efficiency metrics"""
        if self.completed_scans == 0:
            return
            
        # Calculate averages
        total_duration = sum(s['duration_seconds'] for s in self.session_stats['scans'])
        self.session_stats['performance_metrics']['avg_scan_duration'] = total_duration / self.completed_scans
        
        # Calculate rates
        total_tokens = self.session_stats['performance_metrics']['total_tokens_found']
        high_conviction = self.session_stats['performance_metrics']['high_conviction_tokens']
        
        if total_tokens > 0:
            self.session_stats['performance_metrics']['high_conviction_rate'] = (high_conviction / total_tokens) * 100
            
        # Calculate tokens per hour
        duration_hours = (datetime.now() - self.start_time).total_seconds() / 3600
        if duration_hours > 0:
            self.session_stats['performance_metrics']['tokens_per_hour'] = total_tokens / duration_hours
            
        # Calculate success rate
        successful_scans = len([s for s in self.session_stats['scans'] if s['scan_status'] == 'completed'])
        self.session_stats['performance_metrics']['scan_success_rate'] = (successful_scans / self.completed_scans) * 100
        
        # Calculate API efficiency score
        self._calculate_api_efficiency_score()
        
        # Update cost per metrics
        total_cost = self.session_stats['cost_analysis']['total_estimated_cost_usd']
        if self.completed_scans > 0:
            self.session_stats['cost_analysis']['cost_per_scan_avg'] = total_cost / self.completed_scans
        if total_tokens > 0:
            self.session_stats['cost_analysis']['cost_per_token_discovered'] = total_cost / total_tokens
        if high_conviction > 0:
            self.session_stats['cost_analysis']['cost_per_high_conviction_token'] = total_cost / high_conviction
            
    def _calculate_api_efficiency_score(self):
        """Calculate API efficiency score based on success rates and response times"""
        total_score = 0
        provider_count = 0
        
        for provider, stats in self.session_stats['api_usage_by_provider'].items():
            if stats['total_calls'] > 0:
                success_rate = stats['successful_calls'] / stats['total_calls']
                response_time_score = max(0, (2000 - stats['avg_response_time_ms']) / 2000)  # Normalize to 0-1
                provider_score = (success_rate * 0.7 + response_time_score * 0.3) * 100
                total_score += provider_score
                provider_count += 1
                
        if provider_count > 0:
            self.session_stats['performance_metrics']['api_efficiency_score'] = total_score / provider_count
        else:
            self.session_stats['performance_metrics']['api_efficiency_score'] = 0
            
    def _generate_optimization_recommendations(self):
        """Generate optimization recommendations based on collected data"""
        recommendations = []
        
        # API efficiency recommendations
        for provider, stats in self.session_stats['api_usage_by_provider'].items():
            if stats['total_calls'] > 0:
                success_rate = stats['successful_calls'] / stats['total_calls']
                if success_rate < 0.95:
                    recommendations.append(f"Improve {provider} API reliability (current: {success_rate*100:.1f}%)")
                    
                if stats['avg_response_time_ms'] > 1000:
                    recommendations.append(f"Optimize {provider} API response times (current: {stats['avg_response_time_ms']:.0f}ms)")
        
        # Cost optimization
        total_cost = self.session_stats['cost_analysis']['total_estimated_cost_usd']
        if total_cost > 50:  # Arbitrary threshold
            recommendations.append("Consider implementing more aggressive caching to reduce API costs")
            
        # Performance optimization
        avg_duration = self.session_stats['performance_metrics']['avg_scan_duration']
        if avg_duration > 180:  # 3 minutes
            recommendations.append("Investigate scan duration bottlenecks - scans taking too long")
            
        # Error pattern recommendations
        if self.session_stats['error_analysis']['total_errors'] > self.completed_scans * 0.1:
            recommendations.append("High error rate detected - implement better error handling")
            
        self.session_stats['cost_analysis']['optimization_recommendations'] = recommendations
        
    def _print_progress_header(self):
        """Print session header with key information"""
        print("\n" + "="*80)
        print("🎯 12-HOUR ENHANCED HIGH CONVICTION DETECTOR TEST")
        print("="*80)
        print(f"📅 Start Time: {self.start_time.strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"⏱️  Duration: 12 hours (720 minutes)")
        print(f"🔄 Scan Frequency: Every 12 minutes (5 scans/hour)")
        print(f"📊 Total Planned Scans: {self.total_scans}")
        print(f"🆔 Session ID: {self.session_id}")
        print(f"📁 Results will be saved to: scripts/results/12hour_enhanced_results_{self.session_id}.json")
        print("📈 Enhanced Features: API tracking, Cost analysis, Performance profiling, Error analysis")
        print("="*80)
        
    def _print_scan_progress(self, scan_num, scan_start_time):
        """Print progress for current scan"""
        elapsed_total = datetime.now() - self.start_time
        progress_pct = (scan_num / self.total_scans) * 100
        
        # Calculate ETA
        if scan_num > 0:
            avg_scan_time = elapsed_total.total_seconds() / scan_num
            remaining_scans = self.total_scans - scan_num
            eta_seconds = remaining_scans * avg_scan_time
            eta = datetime.now() + timedelta(seconds=eta_seconds)
        else:
            eta = self.start_time + timedelta(hours=12)
            
        print(f"\n🔍 ENHANCED SCAN {scan_num}/{self.total_scans} ({progress_pct:.1f}%)")
        print(f"⏰ Scan Start: {scan_start_time.strftime('%H:%M:%S')}")
        print(f"📈 Total Elapsed: {str(elapsed_total).split('.')[0]}")
        print(f"🎯 ETA Completion: {eta.strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"💾 Memory Usage: {self.process.memory_info().rss / 1024 / 1024:.1f}MB")
        print("-" * 60)
        
    def _capture_api_usage_stats(self):
        """Capture API usage statistics from detector components"""
        try:
            # Capture Birdeye API stats
            if hasattr(self.detector, 'birdeye_api') and self.detector.birdeye_api:
                birdeye_stats = self._get_birdeye_api_stats()
                self._update_api_stats('birdeye', birdeye_stats)
                
            # Capture cross-platform analyzer stats
            if hasattr(self.detector, 'cross_platform_analyzer'):
                cross_platform_stats = self._get_cross_platform_api_stats()
                self._update_api_stats('dexscreener', cross_platform_stats.get('dexscreener', {}))
                self._update_api_stats('rugcheck', cross_platform_stats.get('rugcheck', {}))
                
        except Exception as e:
            self.logger.error(f"❌ Error capturing API usage stats: {e}")
            self._record_error('api_stats_capture', str(e), 'system')
            
    def _get_birdeye_api_stats(self) -> Dict[str, Any]:
        """Extract Birdeye API usage statistics"""
        stats = {
            'calls': 0,
            'successes': 0,
            'failures': 0,
            'total_time_ms': 0,
            'endpoints': {},
            'estimated_cost': 0.0
        }
        
        try:
            birdeye_api = self.detector.birdeye_api
            
            # Try to get stats from rate limiter or cache manager
            if hasattr(birdeye_api, 'rate_limiter') and birdeye_api.rate_limiter:
                rate_limiter_stats = getattr(birdeye_api.rate_limiter, 'get_stats', lambda: {})()
                if rate_limiter_stats:
                    stats['calls'] = rate_limiter_stats.get('total_requests', 0)
                    stats['successes'] = rate_limiter_stats.get('successful_requests', 0)
                    stats['failures'] = rate_limiter_stats.get('failed_requests', 0)
                    
            # Try to get cache stats
            if hasattr(birdeye_api, 'cache_manager') and birdeye_api.cache_manager:
                cache_stats = getattr(birdeye_api.cache_manager, 'get_stats', lambda: {})()
                if cache_stats:
                    # Extract API call counts from cache hits/misses
                    cache_misses = cache_stats.get('misses', 0)
                    stats['calls'] += cache_misses  # Cache misses = API calls made
                    
            # Estimate cost based on Birdeye pricing (approximate)
            # Birdeye charges per API call, roughly $0.001 per call
            stats['estimated_cost'] = stats['calls'] * 0.001
            
        except Exception as e:
            self.logger.error(f"❌ Error getting Birdeye API stats: {e}")
            
        return stats
        
    def _get_cross_platform_api_stats(self) -> Dict[str, Dict[str, Any]]:
        """Extract cross-platform API usage statistics"""
        stats = {
            'dexscreener': {
                'calls': 0,
                'successes': 0,
                'failures': 0,
                'total_time_ms': 0,
                'estimated_cost': 0.0
            },
            'rugcheck': {
                'calls': 0,
                'successes': 0,
                'failures': 0,
                'total_time_ms': 0,
                'estimated_cost': 0.0
            }
        }
        
        try:
            analyzer = self.detector.cross_platform_analyzer
            
            # Try to extract stats from the analyzer
            if hasattr(analyzer, 'get_api_stats'):
                analyzer_stats = analyzer.get_api_stats()
                if analyzer_stats:
                    stats.update(analyzer_stats)
            
            # Estimate costs (DexScreener is free, RugCheck has rate limits)
            stats['dexscreener']['estimated_cost'] = 0.0  # Free API
            stats['rugcheck']['estimated_cost'] = stats['rugcheck']['calls'] * 0.0001  # Minimal cost
            
        except Exception as e:
            self.logger.error(f"❌ Error getting cross-platform API stats: {e}")
            
        return stats
        
    def _update_api_stats(self, provider: str, new_stats: Dict[str, Any]):
        """Update API statistics for a provider"""
        if provider not in self.session_stats['api_usage_by_provider']:
            return
            
        provider_stats = self.session_stats['api_usage_by_provider'][provider]
        
        # Update totals (incremental)
        calls_delta = new_stats.get('calls', 0) - provider_stats.get('last_calls', 0)
        successes_delta = new_stats.get('successes', 0) - provider_stats.get('last_successes', 0)
        failures_delta = new_stats.get('failures', 0) - provider_stats.get('last_failures', 0)
        time_delta = new_stats.get('total_time_ms', 0) - provider_stats.get('last_total_time_ms', 0)
        
        provider_stats['total_calls'] += calls_delta
        provider_stats['successful_calls'] += successes_delta
        provider_stats['failed_calls'] += failures_delta
        provider_stats['total_response_time_ms'] += time_delta
        
        # Calculate averages
        if provider_stats['total_calls'] > 0:
            provider_stats['avg_response_time_ms'] = provider_stats['total_response_time_ms'] / provider_stats['total_calls']
            
        # Update cost estimates
        provider_stats['estimated_cost_usd'] += new_stats.get('estimated_cost', 0.0)
        
        # Store last values for next delta calculation
        provider_stats['last_calls'] = new_stats.get('calls', 0)
        provider_stats['last_successes'] = new_stats.get('successes', 0)
        provider_stats['last_failures'] = new_stats.get('failures', 0)
        provider_stats['last_total_time_ms'] = new_stats.get('total_time_ms', 0)
        
    def _capture_system_performance(self):
        """Capture system resource usage"""
        try:
            # Memory usage
            memory_info = self.process.memory_info()
            memory_mb = memory_info.rss / 1024 / 1024
            
            if memory_mb > self.session_stats['performance_analysis']['system_resource_usage']['peak_memory_mb']:
                self.session_stats['performance_analysis']['system_resource_usage']['peak_memory_mb'] = memory_mb
                
            # CPU usage
            cpu_percent = self.process.cpu_percent()
            current_avg = self.session_stats['performance_analysis']['system_resource_usage']['avg_cpu_percent']
            scan_count = self.completed_scans + 1
            new_avg = (current_avg * (scan_count - 1) + cpu_percent) / scan_count
            self.session_stats['performance_analysis']['system_resource_usage']['avg_cpu_percent'] = new_avg
            
        except Exception as e:
            self.logger.error(f"❌ Error capturing system performance: {e}")
            
    def _record_error(self, error_type: str, error_message: str, provider: str = 'unknown', endpoint: str = 'unknown'):
        """Record error for pattern analysis"""
        try:
            error_analysis = self.session_stats['error_analysis']
            
            # Update counters
            error_analysis['total_errors'] += 1
            error_analysis['errors_by_provider'][provider] += 1
            error_analysis['errors_by_endpoint'][endpoint] += 1
            error_analysis['errors_by_type'][error_type] += 1
            
            # Track consecutive failures
            error_analysis['consecutive_failures'] += 1
            if error_analysis['consecutive_failures'] > error_analysis['max_consecutive_failures']:
                error_analysis['max_consecutive_failures'] = error_analysis['consecutive_failures']
                
            # Record error with timestamp
            error_record = {
                'timestamp': datetime.now().isoformat(),
                'type': error_type,
                'message': error_message,
                'provider': provider,
                'endpoint': endpoint,
                'scan_number': self.completed_scans + 1
            }
            error_analysis['error_timeline'].append(error_record)
            
            # Keep only last 100 errors to prevent memory bloat
            if len(error_analysis['error_timeline']) > 100:
                error_analysis['error_timeline'] = error_analysis['error_timeline'][-100:]
                
        except Exception as e:
            self.logger.error(f"❌ Error recording error: {e}")
            
    def _record_successful_scan(self):
        """Record successful scan to reset consecutive failure counter"""
        self.session_stats['error_analysis']['consecutive_failures'] = 0
        
    def _preserve_detailed_token_analysis(self, scan_results: Dict[str, Any]):
        """Preserve detailed token analysis results"""
        try:
            if not isinstance(scan_results, dict):
                return
                
            # Extract detailed analyses if available
            detailed_analyses = scan_results.get('detailed_analyses', [])
            
            # Handle case where detailed_analyses might be an integer (count) instead of list
            if isinstance(detailed_analyses, int):
                # If it's just a count, we can't preserve the analysis details
                return
            
            if not detailed_analyses or not isinstance(detailed_analyses, list):
                return
                
            # Store detailed analysis for each token
            for analysis in detailed_analyses:
                if not isinstance(analysis, dict) or 'candidate' not in analysis:
                    continue
                    
                candidate = analysis['candidate']
                token_address = candidate.get('address')
                if not token_address:
                    continue
                    
                # Create comprehensive token analysis record
                token_analysis = {
                    'last_analyzed': datetime.now().isoformat(),
                    'scan_number': self.completed_scans,
                    'basic_info': {
                        'symbol': candidate.get('symbol', 'Unknown'),
                        'name': candidate.get('name', ''),
                        'address': token_address
                    },
                    'scores': {
                        'final_score': analysis.get('final_score', 0),
                        'cross_platform_score': candidate.get('cross_platform_score', 0)
                    },
                    'analysis_results': {
                        'overview_data': analysis.get('overview_data', {}),
                        'whale_analysis': analysis.get('whale_analysis', {}),
                        'volume_price_analysis': analysis.get('volume_price_analysis', {}),
                        'community_boost_analysis': analysis.get('community_boost_analysis', {}),
                        'security_analysis': analysis.get('security_analysis', {}),
                        'trading_activity': analysis.get('trading_activity', {})
                    },
                    'platforms': candidate.get('platforms', []),
                    'discovery_method': candidate.get('discovery_method', 'unknown')
                }
                
                # Store or update the analysis
                if token_address in self.session_stats['detailed_token_analyses']:
                    # Update existing analysis
                    existing = self.session_stats['detailed_token_analyses'][token_address]
                    existing['analysis_count'] = existing.get('analysis_count', 1) + 1
                    existing['last_analyzed'] = token_analysis['last_analyzed']
                    existing['scan_number'] = token_analysis['scan_number']
                    
                    # Update scores if better
                    if token_analysis['scores']['final_score'] > existing['scores']['final_score']:
                        existing['scores'] = token_analysis['scores']
                        existing['analysis_results'] = token_analysis['analysis_results']
                else:
                    # New token analysis
                    token_analysis['analysis_count'] = 1
                    token_analysis['first_discovered'] = token_analysis['last_analyzed']
                    self.session_stats['detailed_token_analyses'][token_address] = token_analysis
                    
        except Exception as e:
            self.logger.error(f"❌ Error preserving detailed token analysis: {e}")
            self._record_error('token_analysis_preservation', str(e), 'system')
            
    def _measure_pipeline_performance(self, scan_results: Dict[str, Any], scan_duration: float):
        """Measure and record pipeline performance metrics"""
        try:
            performance_analysis = self.session_stats['performance_analysis']
            
            # Record overall scan duration
            scan_duration_ms = scan_duration * 1000
            
            # Track slowest and fastest scans
            scan_record = {
                'scan_number': self.completed_scans,
                'duration_ms': scan_duration_ms,
                'timestamp': datetime.now().isoformat(),
                'tokens_found': scan_results.get('new_candidates', 0) if isinstance(scan_results, dict) else 0,
                'alerts_sent': scan_results.get('alerts_sent', 0) if isinstance(scan_results, dict) else 0
            }
            
            # Update slowest scans (keep top 5)
            performance_analysis['slowest_scans'].append(scan_record)
            performance_analysis['slowest_scans'].sort(key=lambda x: x['duration_ms'], reverse=True)
            performance_analysis['slowest_scans'] = performance_analysis['slowest_scans'][:5]
            
            # Update fastest scans (keep top 5)
            performance_analysis['fastest_scans'].append(scan_record)
            performance_analysis['fastest_scans'].sort(key=lambda x: x['duration_ms'])
            performance_analysis['fastest_scans'] = performance_analysis['fastest_scans'][:5]
            
            # Identify bottlenecks (scans taking >3 minutes)
            if scan_duration > 180:
                bottleneck = {
                    'scan_number': self.completed_scans,
                    'duration_seconds': scan_duration,
                    'timestamp': datetime.now().isoformat(),
                    'potential_cause': 'Unknown - investigate API response times'
                }
                performance_analysis['bottlenecks_identified'].append(bottleneck)
                
        except Exception as e:
            self.logger.error(f"❌ Error measuring pipeline performance: {e}")
            self._record_error('performance_measurement', str(e), 'system')
            
    def _update_cost_analysis(self):
        """Update cost analysis based on current API usage"""
        try:
            cost_analysis = self.session_stats['cost_analysis']
            
            # Calculate total cost from all providers
            total_cost = 0.0
            for provider, stats in self.session_stats['api_usage_by_provider'].items():
                total_cost += stats.get('estimated_cost_usd', 0.0)
                
            cost_analysis['total_estimated_cost_usd'] = total_cost
            
            # Estimate cost breakdown by stage (rough approximation)
            # Cross-platform analysis uses DexScreener (free) and RugCheck (minimal)
            cost_analysis['cost_breakdown_by_stage']['cross_platform_analysis'] = (
                self.session_stats['api_usage_by_provider']['rugcheck'].get('estimated_cost_usd', 0.0)
            )
            
            # Detailed Birdeye analysis
            birdeye_cost = self.session_stats['api_usage_by_provider']['birdeye'].get('estimated_cost_usd', 0.0)
            cost_analysis['cost_breakdown_by_stage']['detailed_birdeye_analysis'] = birdeye_cost * 0.6
            cost_analysis['cost_breakdown_by_stage']['whale_analysis'] = birdeye_cost * 0.15
            cost_analysis['cost_breakdown_by_stage']['volume_analysis'] = birdeye_cost * 0.15
            cost_analysis['cost_breakdown_by_stage']['security_analysis'] = birdeye_cost * 0.05
            cost_analysis['cost_breakdown_by_stage']['community_analysis'] = birdeye_cost * 0.05
            
        except Exception as e:
            self.logger.error(f"❌ Error updating cost analysis: {e}")
            self._record_error('cost_analysis_update', str(e), 'system')
        
    def _update_session_stats(self, scan_results, scan_duration):
        """Enhanced session statistics update with comprehensive tracking"""
        self.completed_scans += 1
        
        # Capture API usage statistics
        self._capture_api_usage_stats()
        
        # Capture system performance
        self._capture_system_performance()
        
        # Measure pipeline performance
        self._measure_pipeline_performance(scan_results, scan_duration)
        
        # Update cost analysis
        self._update_cost_analysis()
        
        # Preserve detailed token analysis
        self._preserve_detailed_token_analysis(scan_results)
        
        # Record successful scan (resets consecutive failure counter)
        self._record_successful_scan()
        
        # 🔥 NEW: Generate comprehensive API scan report after each scan
        api_report = self._generate_api_scan_report(self.completed_scans)
        
        # Extract tokens from the scan results structure (original logic)
        discovered_tokens = []
        if isinstance(scan_results, dict):
            # Handle the actual structure returned by run_detection_cycle
            if 'detailed_analyses' in scan_results:
                # Extract tokens from detailed analyses
                detailed_analyses = scan_results.get('detailed_analyses', [])
                # Handle case where detailed_analyses might be an integer (count) instead of list
                if isinstance(detailed_analyses, list):
                    for analysis in detailed_analyses:
                        if isinstance(analysis, dict) and 'candidate' in analysis:
                            candidate = analysis['candidate']
                            discovered_tokens.append({
                                'address': candidate.get('address', ''),
                                'symbol': candidate.get('symbol', 'Unknown'),
                                'conviction_score': analysis.get('final_score', 0) / 10.0  # Normalize to 0-1
                            })
            elif 'new_candidates' in scan_results:
                # Handle candidate structure
                new_candidates = scan_results.get('new_candidates', [])
                if isinstance(new_candidates, list):
                    for candidate in new_candidates:
                        if isinstance(candidate, dict):
                            discovered_tokens.append({
                                'address': candidate.get('address', ''),
                                'symbol': candidate.get('symbol', 'Unknown'),
                                'conviction_score': candidate.get('cross_platform_score', 0) / 10.0  # Normalize to 0-1
                            })
        
        # Record scan details with enhanced metrics
        scan_record = {
            'scan_number': self.completed_scans,
            'timestamp': datetime.now().isoformat(),
            'duration_seconds': scan_duration,
            'tokens_found': len(discovered_tokens),
            'high_conviction_count': len([t for t in discovered_tokens 
                                        if t.get('conviction_score', 0) >= 0.7]),
            'scan_status': scan_results.get('status', 'unknown') if isinstance(scan_results, dict) else 'completed',
            'alerts_sent': scan_results.get('alerts_sent', 0) if isinstance(scan_results, dict) else 0,
            'total_analyzed': scan_results.get('total_analyzed', 0) if isinstance(scan_results, dict) else 0,
            'high_conviction_candidates': scan_results.get('high_conviction_candidates', 0) if isinstance(scan_results, dict) else 0,
            'detailed_analyses': scan_results.get('detailed_analyses', 0) if isinstance(scan_results, dict) else 0,
            'api_report': api_report  # 🔥 NEW: Include API report in scan record
        }
        
        self.session_stats['scans'].append(scan_record)
        
        # Update performance metrics
        total_duration = sum(s['duration_seconds'] for s in self.session_stats['scans'])
        self.session_stats['performance_metrics']['avg_scan_duration'] = total_duration / self.completed_scans
        
        # Track discovered tokens (original logic)
        for token in discovered_tokens:
            token_address = token.get('address')
            if token_address:
                if token_address not in self.session_stats['tokens_discovered']:
                    self.session_stats['tokens_discovered'][token_address] = {
                        'first_seen': datetime.now().isoformat(),
                        'times_detected': 1,
                        'best_conviction_score': token.get('conviction_score', 0),
                        'symbol': token.get('symbol', 'Unknown')
                    }
                else:
                    self.session_stats['tokens_discovered'][token_address]['times_detected'] += 1
                    current_score = token.get('conviction_score', 0)
                    if current_score > self.session_stats['tokens_discovered'][token_address]['best_conviction_score']:
                        self.session_stats['tokens_discovered'][token_address]['best_conviction_score'] = current_score
        
        # Update totals
        self.session_stats['performance_metrics']['total_tokens_found'] = sum(s['tokens_found'] for s in self.session_stats['scans'])
        self.session_stats['performance_metrics']['unique_tokens'] = len(self.session_stats['tokens_discovered'])
        self.session_stats['performance_metrics']['high_conviction_tokens'] = len([
            t for t in self.session_stats['tokens_discovered'].values() 
            if t['best_conviction_score'] >= 0.7
        ])

    def _generate_api_scan_report(self, scan_number: int) -> Dict[str, Any]:
        """Generate comprehensive API scan report by actual service provider"""
        try:
            # Get RugCheck statistics from actual API tracking
            rugcheck_stats = {"total_calls": 0, "successful_calls": 0, "failed_calls": 0}
            if hasattr(self.detector, 'cross_platform_analyzer') and self.detector.cross_platform_analyzer:
                if hasattr(self.detector.cross_platform_analyzer, 'rugcheck'):
                    rugcheck_api_stats = self.detector.cross_platform_analyzer.rugcheck.get_api_call_statistics()
                    rugcheck_stats = {
                        "total_calls": rugcheck_api_stats.get("total_calls", 0),
                        "successful_calls": rugcheck_api_stats.get("successful_calls", 0),
                        "failed_calls": rugcheck_api_stats.get("failed_calls", 0),
                        "endpoints_used": rugcheck_api_stats.get("endpoints_used", [])
                    }
            
            # Fallback to estimation if no real stats available
            if rugcheck_stats["total_calls"] == 0:
                rugcheck_stats = self._estimate_rugcheck_api_calls()
            
            # Get DexScreener statistics from actual API tracking
            dexscreener_stats = {"total_calls": 0, "successful_calls": 0, "failed_calls": 0}
            if hasattr(self.detector, 'cross_platform_analyzer') and self.detector.cross_platform_analyzer:
                if hasattr(self.detector.cross_platform_analyzer, 'dexscreener'):
                    dexscreener_api_stats = self.detector.cross_platform_analyzer.dexscreener.get_api_call_statistics()
                    dexscreener_stats = {
                        "total_calls": dexscreener_api_stats.get("total_calls", 0),
                        "successful_calls": dexscreener_api_stats.get("successful_calls", 0),
                        "failed_calls": dexscreener_api_stats.get("failed_calls", 0),
                        "endpoints_used": dexscreener_api_stats.get("endpoints_used", [])
                    }
            
            # Fallback to estimation if no real stats available
            if dexscreener_stats["total_calls"] == 0:
                dexscreener_stats = self._estimate_dexscreener_api_calls()
            
            # Get Birdeye API statistics
            birdeye_stats = {}
            if hasattr(self.detector, 'birdeye_api') and self.detector.birdeye_api:
                birdeye_stats = self.detector.birdeye_api.get_api_call_statistics()
            
            # Create service-based statistics
            service_stats = {
                "rugcheck": {
                    "total_calls": rugcheck_stats.get("total_calls", 0),
                    "successful_calls": rugcheck_stats.get("successful_calls", 0),
                    "failed_calls": rugcheck_stats.get("failed_calls", 0),
                    "cache_hits": 0,
                    "cache_misses": 0,
                    "total_response_time_ms": 0,
                    "endpoints": ["RugCheck Trending API"],
                    "service_name": "RugCheck API"
                },
                "dexscreener": {
                    "total_calls": dexscreener_stats.get("total_calls", 0),
                    "successful_calls": dexscreener_stats.get("successful_calls", 0),
                    "failed_calls": dexscreener_stats.get("failed_calls", 0),
                    "cache_hits": 0,
                    "cache_misses": 0,
                    "total_response_time_ms": 0,
                    "endpoints": ["DexScreener Boosted API", "DexScreener Top Boosted API"],
                    "service_name": "DexScreener API"
                },
                "birdeye": {
                    "total_calls": birdeye_stats.get("total_api_calls", 0),
                    "successful_calls": birdeye_stats.get("successful_api_calls", 0),
                    "failed_calls": birdeye_stats.get("failed_api_calls", 0),
                    "cache_hits": birdeye_stats.get("cache_hits", 0),
                    "cache_misses": birdeye_stats.get("cache_misses", 0),
                    "total_response_time_ms": birdeye_stats.get("total_response_time_ms", 0),
                    "endpoints": [ep["endpoint"] for ep in birdeye_stats.get("top_endpoints", [])],
                    "service_name": "Birdeye API"
                }
            }
            
            # Create combined summary
            summary = self._create_service_based_summary(service_stats)
            
            # Combine statistics
            report = {
                "scan_number": scan_number,
                "timestamp": time.time(),
                "service_stats": service_stats,
                "summary": summary
            }
            
            # Display the report
            self._display_api_scan_report(report)
            
            return report
            
        except Exception as e:
            self.logger.error(f"❌ Error generating API scan report: {e}")
            return {"error": str(e), "scan_number": scan_number}

    def _create_service_based_summary(self, service_stats: Dict[str, Any]) -> Dict[str, Any]:
        """Create combined API summary from service-based statistics"""
        summary = {
            "total_api_calls": 0,
            "successful_calls": 0,
            "failed_calls": 0,
            "cache_hits": 0,
            "cache_misses": 0,
            "cache_hit_rate": 0.0,
            "average_response_time_ms": 0.0,
            "endpoints_used": set(),
            "health_status": "unknown"
        }
        
        total_response_time = 0
        total_calls_with_time = 0
        
        # Combine all service statistics
        for service_key, service in service_stats.items():
            summary["total_api_calls"] += service.get("total_calls", 0)
            summary["successful_calls"] += service.get("successful_calls", 0)
            summary["failed_calls"] += service.get("failed_calls", 0)
            summary["cache_hits"] += service.get("cache_hits", 0)
            summary["cache_misses"] += service.get("cache_misses", 0)
            
            # Add endpoints
            for endpoint in service.get("endpoints", []):
                summary["endpoints_used"].add(endpoint)
            
            # Calculate weighted average response time
            service_calls = service.get("total_calls", 0)
            service_response_time = service.get("total_response_time_ms", 0)
            if service_calls > 0 and service_response_time > 0:
                total_response_time += service_response_time
                total_calls_with_time += service_calls
        
        # Calculate derived metrics
        total_cache_requests = summary["cache_hits"] + summary["cache_misses"]
        if total_cache_requests > 0:
            summary["cache_hit_rate"] = (summary["cache_hits"] / total_cache_requests) * 100
            
        if total_calls_with_time > 0:
            summary["average_response_time_ms"] = total_response_time / total_calls_with_time
            
        # Determine health status
        if summary["total_api_calls"] == 0:
            summary["health_status"] = "no_activity"
        elif summary["failed_calls"] == 0:
            summary["health_status"] = "excellent"
        elif summary["successful_calls"] / summary["total_api_calls"] >= 0.95:
            summary["health_status"] = "good"
        elif summary["successful_calls"] / summary["total_api_calls"] >= 0.80:
            summary["health_status"] = "fair"
        else:
            summary["health_status"] = "poor"
            
        # Convert set to list for JSON serialization
        summary["endpoints_used"] = list(summary["endpoints_used"])
        
        return summary

    def _display_api_scan_report(self, report: Dict[str, Any]):
        """Display comprehensive API scan report by actual service provider"""
        scan_num = report["scan_number"]
        summary = report.get("summary", {})
        service_stats = report.get("service_stats", {})
        
        print(f"\n📡 API SCAN REPORT - Scan #{scan_num}")
        print("=" * 50)
        
        # Overall statistics
        total_calls = summary.get("total_api_calls", 0)
        successful = summary.get("successful_calls", 0)
        failed = summary.get("failed_calls", 0)
        
        print(f"🔢 API Call Statistics:")
        print(f"  Total Calls: {total_calls}")
        print(f"  Successful: {successful}")
        print(f"  Failed: {failed}")
        
        if total_calls > 0:
            success_rate = (successful / total_calls) * 100
            print(f"  Success Rate: {success_rate:.1f}%")
            
        # Cache performance
        cache_hits = summary.get("cache_hits", 0)
        cache_misses = summary.get("cache_misses", 0)
        cache_hit_rate = summary.get("cache_hit_rate", 0)
        
        print(f"\n💾 Cache Performance:")
        print(f"  Cache Hits: {cache_hits}")
        print(f"  Cache Misses: {cache_misses}")
        print(f"  Hit Rate: {cache_hit_rate:.1f}%")
        
        # Health status
        health_status = summary.get("health_status", "unknown")
        health_emoji = {
            "excellent": "🟢",
            "good": "🟡", 
            "fair": "🟠",
            "poor": "🔴",
            "no_activity": "⚪",
            "unknown": "❓"
        }.get(health_status, "❓")
        
        print(f"\n{health_emoji} Health Status: {health_status.upper()}")
        
        # Enhanced API Service Breakdown by actual service provider
        self._display_enhanced_api_service_breakdown_single_scan(report)
        
        print("=" * 50)

    def _display_enhanced_api_service_breakdown_single_scan(self, report: Dict[str, Any]):
        """Display comprehensive API service breakdown by actual service provider"""
        scan_num = report["scan_number"]
        service_stats = report.get("service_stats", {})
        
        print(f"\n🔧 API SERVICE BREAKDOWN - Scan #{scan_num}")
        print("-" * 50)
        
        # Service provider breakdown
        service_order = ["rugcheck", "dexscreener", "birdeye"]
        service_emojis = {
            "rugcheck": "🛡️",
            "dexscreener": "📊", 
            "birdeye": "🦅"
        }
        
        total_all_calls = 0
        total_all_success = 0
        
        for service_key in service_order:
            if service_key not in service_stats:
                continue
                
            service = service_stats[service_key]
            calls = service.get("total_calls", 0)
            success = service.get("successful_calls", 0)
            failed = service.get("failed_calls", 0)
            service_name = service.get("service_name", service_key.upper())
            endpoints = service.get("endpoints", [])
            
            if calls == 0:
                continue
                
            total_all_calls += calls
            total_all_success += success
            
            emoji = service_emojis.get(service_key, "🔗")
            print(f"\n{emoji} {service_name}")
            print(f"  Calls: {calls} | Success: {success} | Failed: {failed}")
            
            if calls > 0:
                success_rate = (success / calls) * 100
                print(f"  Success Rate: {success_rate:.1f}%")
        
        # Cross-Service Summary
        if total_all_calls > 0:
            overall_success_rate = (total_all_success / total_all_calls) * 100
            print(f"\n📈 SCAN TOTAL: {total_all_calls} calls ({overall_success_rate:.1f}% success)")

    def _estimate_rugcheck_api_calls(self) -> Dict[str, int]:
        """Estimate RugCheck API calls from recent activity"""
        try:
            # Basic estimation - assume 1 trending call per scan if cross-platform analyzer exists
            if hasattr(self.detector, 'cross_platform_analyzer'):
                return {"total_calls": 1, "successful_calls": 1, "failed_calls": 0}
            return {"total_calls": 0, "successful_calls": 0, "failed_calls": 0}
        except Exception:
            return {"total_calls": 0, "successful_calls": 0, "failed_calls": 0}

    def _estimate_dexscreener_api_calls(self) -> Dict[str, int]:
        """Estimate DexScreener API calls from recent activity"""
        try:
            # Basic estimation - assume 2 calls per scan (boosted + top boosted) if cross-platform analyzer exists
            if hasattr(self.detector, 'cross_platform_analyzer'):
                return {"total_calls": 2, "successful_calls": 2, "failed_calls": 0}
            return {"total_calls": 0, "successful_calls": 0, "failed_calls": 0}
        except Exception:
            return {"total_calls": 0, "successful_calls": 0, "failed_calls": 0}
        
        # Record scan details with enhanced metrics
        scan_record = {
            'scan_number': self.completed_scans,
            'timestamp': datetime.now().isoformat(),
            'duration_seconds': scan_duration,
            'tokens_found': len(discovered_tokens),
            'high_conviction_count': len([t for t in discovered_tokens 
                                        if t.get('conviction_score', 0) >= 0.7]),
            'scan_status': scan_results.get('status', 'unknown') if isinstance(scan_results, dict) else 'completed',
            'alerts_sent': scan_results.get('alerts_sent', 0) if isinstance(scan_results, dict) else 0,
            'total_analyzed': scan_results.get('total_analyzed', 0) if isinstance(scan_results, dict) else 0,
            'high_conviction_candidates': scan_results.get('high_conviction_candidates', 0) if isinstance(scan_results, dict) else 0,
            'detailed_analyses': scan_results.get('detailed_analyses', 0) if isinstance(scan_results, dict) else 0,
            'api_report': api_report  # 🔥 NEW: Include API report in scan record
        }
        
        self.session_stats['scans'].append(scan_record)
        
        # Update performance metrics
        total_duration = sum(s['duration_seconds'] for s in self.session_stats['scans'])
        self.session_stats['performance_metrics']['avg_scan_duration'] = total_duration / self.completed_scans
        
        # Track discovered tokens (original logic)
        for token in discovered_tokens:
            token_address = token.get('address')
            if token_address:
                if token_address not in self.session_stats['tokens_discovered']:
                    self.session_stats['tokens_discovered'][token_address] = {
                        'first_seen': datetime.now().isoformat(),
                        'times_detected': 1,
                        'best_conviction_score': token.get('conviction_score', 0),
                        'symbol': token.get('symbol', 'Unknown')
                    }
                else:
                    self.session_stats['tokens_discovered'][token_address]['times_detected'] += 1
                    current_score = token.get('conviction_score', 0)
                    if current_score > self.session_stats['tokens_discovered'][token_address]['best_conviction_score']:
                        self.session_stats['tokens_discovered'][token_address]['best_conviction_score'] = current_score
        
        # Update totals
        self.session_stats['performance_metrics']['total_tokens_found'] = sum(s['tokens_found'] for s in self.session_stats['scans'])
        self.session_stats['performance_metrics']['unique_tokens'] = len(self.session_stats['tokens_discovered'])
        self.session_stats['performance_metrics']['high_conviction_tokens'] = len([
            t for t in self.session_stats['tokens_discovered'].values() 
            if t['best_conviction_score'] >= 0.7
        ])

    def _generate_api_scan_report(self, scan_number: int) -> Dict[str, Any]:
        """Generate comprehensive API scan report by actual service provider"""
        try:
            # Get RugCheck statistics from actual API tracking
            rugcheck_stats = {"total_calls": 0, "successful_calls": 0, "failed_calls": 0}
            if hasattr(self.detector, 'cross_platform_analyzer') and self.detector.cross_platform_analyzer:
                if hasattr(self.detector.cross_platform_analyzer, 'rugcheck'):
                    rugcheck_api_stats = self.detector.cross_platform_analyzer.rugcheck.get_api_call_statistics()
                    rugcheck_stats = {
                        "total_calls": rugcheck_api_stats.get("total_calls", 0),
                        "successful_calls": rugcheck_api_stats.get("successful_calls", 0),
                        "failed_calls": rugcheck_api_stats.get("failed_calls", 0),
                        "endpoints_used": rugcheck_api_stats.get("endpoints_used", [])
                    }
            
            # Fallback to estimation if no real stats available
            if rugcheck_stats["total_calls"] == 0:
                rugcheck_stats = self._estimate_rugcheck_api_calls()
            
            # Get DexScreener statistics from actual API tracking
            dexscreener_stats = {"total_calls": 0, "successful_calls": 0, "failed_calls": 0}
            if hasattr(self.detector, 'cross_platform_analyzer') and self.detector.cross_platform_analyzer:
                if hasattr(self.detector.cross_platform_analyzer, 'dexscreener'):
                    dexscreener_api_stats = self.detector.cross_platform_analyzer.dexscreener.get_api_call_statistics()
                    dexscreener_stats = {
                        "total_calls": dexscreener_api_stats.get("total_calls", 0),
                        "successful_calls": dexscreener_api_stats.get("successful_calls", 0),
                        "failed_calls": dexscreener_api_stats.get("failed_calls", 0),
                        "endpoints_used": dexscreener_api_stats.get("endpoints_used", [])
                    }
            
            # Fallback to estimation if no real stats available
            if dexscreener_stats["total_calls"] == 0:
                dexscreener_stats = self._estimate_dexscreener_api_calls()
            
            # Get Birdeye API statistics
            birdeye_stats = {}
            if hasattr(self.detector, 'birdeye_api') and self.detector.birdeye_api:
                birdeye_stats = self.detector.birdeye_api.get_api_call_statistics()
            
            # Create service-based statistics
            service_stats = {
                "rugcheck": {
                    "total_calls": rugcheck_stats.get("total_calls", 0),
                    "successful_calls": rugcheck_stats.get("successful_calls", 0),
                    "failed_calls": rugcheck_stats.get("failed_calls", 0),
                    "cache_hits": 0,
                    "cache_misses": 0,
                    "total_response_time_ms": 0,
                    "endpoints": ["RugCheck Trending API"],
                    "service_name": "RugCheck API"
                },
                "dexscreener": {
                    "total_calls": dexscreener_stats.get("total_calls", 0),
                    "successful_calls": dexscreener_stats.get("successful_calls", 0),
                    "failed_calls": dexscreener_stats.get("failed_calls", 0),
                    "cache_hits": 0,
                    "cache_misses": 0,
                    "total_response_time_ms": 0,
                    "endpoints": ["DexScreener Boosted API", "DexScreener Top Boosted API"],
                    "service_name": "DexScreener API"
                },
                "birdeye": {
                    "total_calls": birdeye_stats.get("total_api_calls", 0),
                    "successful_calls": birdeye_stats.get("successful_api_calls", 0),
                    "failed_calls": birdeye_stats.get("failed_api_calls", 0),
                    "cache_hits": birdeye_stats.get("cache_hits", 0),
                    "cache_misses": birdeye_stats.get("cache_misses", 0),
                    "total_response_time_ms": birdeye_stats.get("total_response_time_ms", 0),
                    "endpoints": [ep["endpoint"] for ep in birdeye_stats.get("top_endpoints", [])],
                    "service_name": "Birdeye API"
                }
            }
            
            # Create combined summary
            summary = self._create_service_based_summary(service_stats)
            
            # Combine statistics
            report = {
                "scan_number": scan_number,
                "timestamp": time.time(),
                "service_stats": service_stats,
                "summary": summary
            }
            
            # Display the report
            self._display_api_scan_report(report)
            
            return report
            
        except Exception as e:
            self.logger.error(f"❌ Error generating API scan report: {e}")
            return {"error": str(e), "scan_number": scan_number}

    def _create_service_based_summary(self, service_stats: Dict[str, Any]) -> Dict[str, Any]:
        """Create combined API summary from service-based statistics"""
        summary = {
            "total_api_calls": 0,
            "successful_calls": 0,
            "failed_calls": 0,
            "cache_hits": 0,
            "cache_misses": 0,
            "cache_hit_rate": 0.0,
            "average_response_time_ms": 0.0,
            "endpoints_used": set(),
            "health_status": "unknown"
        }
        
        total_response_time = 0
        total_calls_with_time = 0
        
        # Combine all service statistics
        for service_key, service in service_stats.items():
            summary["total_api_calls"] += service.get("total_calls", 0)
            summary["successful_calls"] += service.get("successful_calls", 0)
            summary["failed_calls"] += service.get("failed_calls", 0)
            summary["cache_hits"] += service.get("cache_hits", 0)
            summary["cache_misses"] += service.get("cache_misses", 0)
            
            # Add endpoints
            for endpoint in service.get("endpoints", []):
                summary["endpoints_used"].add(endpoint)
            
            # Calculate weighted average response time
            service_calls = service.get("total_calls", 0)
            service_response_time = service.get("total_response_time_ms", 0)
            if service_calls > 0 and service_response_time > 0:
                total_response_time += service_response_time
                total_calls_with_time += service_calls
        
        # Calculate derived metrics
        total_cache_requests = summary["cache_hits"] + summary["cache_misses"]
        if total_cache_requests > 0:
            summary["cache_hit_rate"] = (summary["cache_hits"] / total_cache_requests) * 100
            
        if total_calls_with_time > 0:
            summary["average_response_time_ms"] = total_response_time / total_calls_with_time
            
        # Determine health status
        if summary["total_api_calls"] == 0:
            summary["health_status"] = "no_activity"
        elif summary["failed_calls"] == 0:
            summary["health_status"] = "excellent"
        elif summary["successful_calls"] / summary["total_api_calls"] >= 0.95:
            summary["health_status"] = "good"
        elif summary["successful_calls"] / summary["total_api_calls"] >= 0.80:
            summary["health_status"] = "fair"
        else:
            summary["health_status"] = "poor"
            
        # Convert set to list for JSON serialization
        summary["endpoints_used"] = list(summary["endpoints_used"])
        
        return summary

    def _display_api_scan_report(self, report: Dict[str, Any]):
        """Display comprehensive API scan report by actual service provider"""
        scan_num = report["scan_number"]
        summary = report.get("summary", {})
        service_stats = report.get("service_stats", {})
        
        print(f"\n📡 API SCAN REPORT - Scan #{scan_num}")
        print("=" * 50)
        
        # Overall statistics
        total_calls = summary.get("total_api_calls", 0)
        successful = summary.get("successful_calls", 0)
        failed = summary.get("failed_calls", 0)
        
        print(f"🔢 API Call Statistics:")
        print(f"  Total Calls: {total_calls}")
        print(f"  Successful: {successful}")
        print(f"  Failed: {failed}")
        
        if total_calls > 0:
            success_rate = (successful / total_calls) * 100
            print(f"  Success Rate: {success_rate:.1f}%")
            
        # Cache performance
        cache_hits = summary.get("cache_hits", 0)
        cache_misses = summary.get("cache_misses", 0)
        cache_hit_rate = summary.get("cache_hit_rate", 0)
        
        print(f"\n💾 Cache Performance:")
        print(f"  Cache Hits: {cache_hits}")
        print(f"  Cache Misses: {cache_misses}")
        print(f"  Hit Rate: {cache_hit_rate:.1f}%")
        
        # Health status
        health_status = summary.get("health_status", "unknown")
        health_emoji = {
            "excellent": "🟢",
            "good": "🟡", 
            "fair": "🟠",
            "poor": "🔴",
            "no_activity": "⚪",
            "unknown": "❓"
        }.get(health_status, "❓")
        
        print(f"\n{health_emoji} Health Status: {health_status.upper()}")
        
        # Enhanced API Service Breakdown by actual service provider
        self._display_enhanced_api_service_breakdown_single_scan(report)
        
        print("=" * 50)

    def _display_enhanced_api_service_breakdown_single_scan(self, report: Dict[str, Any]):
        """Display comprehensive API service breakdown by actual service provider"""
        scan_num = report["scan_number"]
        service_stats = report.get("service_stats", {})
        
        print(f"\n🔧 API SERVICE BREAKDOWN - Scan #{scan_num}")
        print("-" * 50)
        
        # Service provider breakdown
        service_order = ["rugcheck", "dexscreener", "birdeye"]
        service_emojis = {
            "rugcheck": "🛡️",
            "dexscreener": "📊", 
            "birdeye": "🦅"
        }
        
        total_all_calls = 0
        total_all_success = 0
        
        for service_key in service_order:
            if service_key not in service_stats:
                continue
                
            service = service_stats[service_key]
            calls = service.get("total_calls", 0)
            success = service.get("successful_calls", 0)
            failed = service.get("failed_calls", 0)
            service_name = service.get("service_name", service_key.upper())
            endpoints = service.get("endpoints", [])
            
            if calls == 0:
                continue
                
            total_all_calls += calls
            total_all_success += success
            
            emoji = service_emojis.get(service_key, "🔗")
            print(f"\n{emoji} {service_name}")
            print(f"  Calls: {calls} | Success: {success} | Failed: {failed}")
            
            if calls > 0:
                success_rate = (success / calls) * 100
                print(f"  Success Rate: {success_rate:.1f}%")
        
        # Cross-Service Summary
        if total_all_calls > 0:
            overall_success_rate = (total_all_success / total_all_calls) * 100
            print(f"\n📈 SCAN TOTAL: {total_all_calls} calls ({overall_success_rate:.1f}% success)")

    def _estimate_rugcheck_api_calls(self) -> Dict[str, int]:
        """Estimate RugCheck API calls from recent activity"""
        try:
            # Basic estimation - assume 1 trending call per scan if cross-platform analyzer exists
            if hasattr(self.detector, 'cross_platform_analyzer'):
                return {"total_calls": 1, "successful_calls": 1, "failed_calls": 0}
            return {"total_calls": 0, "successful_calls": 0, "failed_calls": 0}
        except Exception:
            return {"total_calls": 0, "successful_calls": 0, "failed_calls": 0}

    def _estimate_dexscreener_api_calls(self) -> Dict[str, int]:
        """Estimate DexScreener API calls from recent activity"""
        try:
            # Basic estimation - assume 2 calls per scan (boosted + top boosted) if cross-platform analyzer exists
            if hasattr(self.detector, 'cross_platform_analyzer'):
                return {"total_calls": 2, "successful_calls": 2, "failed_calls": 0}
            return {"total_calls": 0, "successful_calls": 0, "failed_calls": 0}
        except Exception:
            return {"total_calls": 0, "successful_calls": 0, "failed_calls": 0}

async def main():
    """Main async entry point"""
    print("🚀 Starting 12-Hour High Conviction Detector Test...")
    print("⚠️  This will run for 12 hours with 5 scans per hour (every 12 minutes)")
    print("🛑 Press Ctrl+C to stop gracefully at any time")
    
    # Confirmation prompt
    response = input("\n📋 Proceed with 12-hour test? (y/N): ").strip().lower()
    if response not in ['y', 'yes']:
        print("❌ Test cancelled by user")
        sys.exit(0)
    
    test = EnhancedTwelveHourDetectorTest()
    await test.run()

if __name__ == "__main__":
    # Run the async main function
    asyncio.run(main()) 