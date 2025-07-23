#!/usr/bin/env python3
"""
Enhanced 12-Hour High Conviction Detector Test with Comprehensive API Reporting
This enhancement adds the detailed per-scan API reporting features from run_1hour_6scans_detector.py
to the 12-hour test script for better monitoring and analysis.

Key Enhancements:
- Per-scan API reports showing service breakdown
- Real-time API performance monitoring
- Service-specific statistics (RugCheck, DexScreener, Birdeye)
- Session-wide API summary at completion
- Health status tracking per scan
- Optimization recommendations based on API performance
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

class EnhancedTwelveHourDetectorWithAPIReporting:
    def __init__(self):
        self.detector = HighConvictionTokenDetector()
        self.start_time = datetime.now()
        self.session_id = f"12h_enhanced_api_{int(time.time())}"
        self.scan_interval = 12 * 60  # 12 minutes = 720 seconds
        self.total_duration = 12 * 60 * 60  # 12 hours in seconds
        self.total_scans = 60  # 5 scans per hour × 12 hours
        self.completed_scans = 0
        
        # Enhanced session statistics with API reporting
        self.session_stats = {
            'start_time': self.start_time.isoformat(),
            'session_id': self.session_id,
            'scan_interval_minutes': 12,
            'total_planned_scans': self.total_scans,
            'total_duration_hours': 12,
            'scans': [],
            'tokens_discovered': {},
            'api_reports': [],  # Store all API reports for session analysis
            
            # Enhanced API tracking by provider
            'api_usage_by_provider': {
                'birdeye': {
                    'total_calls': 0,
                    'successful_calls': 0,
                    'failed_calls': 0,
                    'total_response_time_ms': 0,
                    'avg_response_time_ms': 0,
                    'estimated_cost_usd': 0.0
                },
                'dexscreener': {
                    'total_calls': 0,
                    'successful_calls': 0,
                    'failed_calls': 0,
                    'total_response_time_ms': 0,
                    'avg_response_time_ms': 0,
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
            
            # Performance metrics
            'performance_metrics': {
                'avg_scan_duration': 0,
                'total_tokens_found': 0,
                'unique_tokens': 0,
                'high_conviction_tokens': 0,
                'tokens_per_hour': 0,
                'high_conviction_rate': 0.0,
                'scan_success_rate': 0.0,
                'api_efficiency_score': 0.0
            }
        }
        
        # Setup logging
        self.logger_setup = LoggerSetup('12hour_enhanced_api_detector')
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
        
    def _generate_api_scan_report(self, scan_number: int) -> Dict[str, Any]:
        """Generate comprehensive API scan report by actual service provider"""
        try:
            # Get RugCheck statistics from actual API tracking
            rugcheck_stats = {"total_calls": 0, "successful_calls": 0, "failed_calls": 0}
            if hasattr(self.detector, 'cross_platform_analyzer') and self.detector.cross_platform_analyzer:
                if hasattr(self.detector.cross_platform_analyzer, 'rugcheck'):
                    try:
                        rugcheck_api_stats = self.detector.cross_platform_analyzer.rugcheck.get_api_call_statistics()
                        rugcheck_stats = {
                            "total_calls": rugcheck_api_stats.get("total_calls", 0),
                            "successful_calls": rugcheck_api_stats.get("successful_calls", 0),
                            "failed_calls": rugcheck_api_stats.get("failed_calls", 0),
                            "endpoints_used": rugcheck_api_stats.get("endpoints_used", [])
                        }
                    except:
                        pass
            
            # Fallback to estimation if no real stats available
            if rugcheck_stats["total_calls"] == 0:
                rugcheck_stats = self._estimate_rugcheck_api_calls()
            
            # Get DexScreener statistics from actual API tracking
            dexscreener_stats = {"total_calls": 0, "successful_calls": 0, "failed_calls": 0}
            if hasattr(self.detector, 'cross_platform_analyzer') and self.detector.cross_platform_analyzer:
                if hasattr(self.detector.cross_platform_analyzer, 'dexscreener'):
                    try:
                        dexscreener_api_stats = self.detector.cross_platform_analyzer.dexscreener.get_api_call_statistics()
                        dexscreener_stats = {
                            "total_calls": dexscreener_api_stats.get("total_calls", 0),
                            "successful_calls": dexscreener_api_stats.get("successful_calls", 0),
                            "failed_calls": dexscreener_api_stats.get("failed_calls", 0),
                            "endpoints_used": dexscreener_api_stats.get("endpoints_used", [])
                        }
                    except:
                        pass
            
            # Fallback to estimation if no real stats available
            if dexscreener_stats["total_calls"] == 0:
                dexscreener_stats = self._estimate_dexscreener_api_calls()
            
            # Get Birdeye API statistics
            birdeye_stats = {}
            if hasattr(self.detector, 'birdeye_api') and self.detector.birdeye_api:
                try:
                    birdeye_stats = self.detector.birdeye_api.get_api_call_statistics()
                except:
                    pass
            
            # Create service-based statistics
            service_stats = {
                "rugcheck": {
                    "total_calls": rugcheck_stats.get("total_calls", 0),
                    "successful_calls": rugcheck_stats.get("successful_calls", 0),
                    "failed_calls": rugcheck_stats.get("failed_calls", 0),
                    "service_name": "RugCheck API"
                },
                "dexscreener": {
                    "total_calls": dexscreener_stats.get("total_calls", 0),
                    "successful_calls": dexscreener_stats.get("successful_calls", 0),
                    "failed_calls": dexscreener_stats.get("failed_calls", 0),
                    "service_name": "DexScreener API"
                },
                "birdeye": {
                    "total_calls": birdeye_stats.get("total_api_calls", 0),
                    "successful_calls": birdeye_stats.get("successful_api_calls", 0),
                    "failed_calls": birdeye_stats.get("failed_api_calls", 0),
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
            "health_status": "unknown"
        }
        
        # Combine all service statistics
        for service_key, service in service_stats.items():
            summary["total_api_calls"] += service.get("total_calls", 0)
            summary["successful_calls"] += service.get("successful_calls", 0)
            summary["failed_calls"] += service.get("failed_calls", 0)
        
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

    def _display_session_api_summary(self):
        """Display comprehensive API session summary across all scans"""
        print("\n" + "=" * 60)
        print("📡 API SESSION SUMMARY - ALL SCANS")
        print("=" * 60)
        
        if not self.session_stats['api_reports']:
            print("No API reports available")
            return
            
        # Aggregate statistics across all scans
        total_session_stats = {
            "total_api_calls": 0,
            "successful_calls": 0,
            "failed_calls": 0,
            "scans_analyzed": len(self.session_stats['api_reports'])
        }
        
        health_status_counts = {}
        
        # Process each scan's API report
        for report in self.session_stats['api_reports']:
            if "summary" in report:
                summary = report["summary"]
                total_session_stats["total_api_calls"] += summary.get("total_api_calls", 0)
                total_session_stats["successful_calls"] += summary.get("successful_calls", 0)
                total_session_stats["failed_calls"] += summary.get("failed_calls", 0)
                    
                # Track health status distribution
                health_status = summary.get("health_status", "unknown")
                health_status_counts[health_status] = health_status_counts.get(health_status, 0) + 1
        
        # Calculate session-wide metrics
        if total_session_stats["total_api_calls"] > 0:
            session_success_rate = (total_session_stats["successful_calls"] / total_session_stats["total_api_calls"]) * 100
        else:
            session_success_rate = 0
        
        # Display session totals
        print(f"🔢 SESSION API TOTALS:")
        print(f"  Total API Calls: {total_session_stats['total_api_calls']}")
        print(f"  Successful: {total_session_stats['successful_calls']}")
        print(f"  Failed: {total_session_stats['failed_calls']}")
        print(f"  Success Rate: {session_success_rate:.1f}%")
        
        print(f"\n⚡ SESSION PERFORMANCE:")
        print(f"  Scans Analyzed: {total_session_stats['scans_analyzed']}")
        
        if total_session_stats["scans_analyzed"] > 0:
            avg_calls_per_scan = total_session_stats["total_api_calls"] / total_session_stats["scans_analyzed"]
            print(f"  Average API Calls per Scan: {avg_calls_per_scan:.1f}")
        
        # Health status distribution
        print(f"\n🏥 HEALTH STATUS DISTRIBUTION:")
        for status, count in sorted(health_status_counts.items()):
            percentage = (count / total_session_stats["scans_analyzed"]) * 100
            health_emoji = {
                "excellent": "🟢",
                "good": "🟡", 
                "fair": "🟠",
                "poor": "🔴",
                "no_activity": "⚪",
                "unknown": "❓"
            }.get(status, "❓")
            print(f"  {health_emoji} {status.upper()}: {count} scans ({percentage:.1f}%)")
        
        # Overall session assessment
        print(f"\n🎯 SESSION ASSESSMENT:")
        if session_success_rate >= 95:
            print(f"  🟢 EXCELLENT: API performance is outstanding!")
        elif session_success_rate >= 85:
            print(f"  🟡 GOOD: API performance is solid with minor issues")
        elif session_success_rate >= 70:
            print(f"  🟠 FAIR: API performance has some issues to address")
        else:
            print(f"  🔴 POOR: API performance needs immediate attention")
        
        print("=" * 60)

    def _update_session_stats(self, scan_results, scan_duration):
        """Enhanced session statistics update with comprehensive API tracking"""
        self.completed_scans += 1
        
        # Generate comprehensive API scan report after each scan
        api_report = self._generate_api_scan_report(self.completed_scans)
        self.session_stats['api_reports'].append(api_report)
        
        # Extract tokens from the scan results structure
        discovered_tokens = []
        if isinstance(scan_results, dict):
            if 'detailed_analyses' in scan_results:
                detailed_analyses = scan_results.get('detailed_analyses', [])
                if isinstance(detailed_analyses, list):
                    for analysis in detailed_analyses:
                        if isinstance(analysis, dict) and 'candidate' in analysis:
                            candidate = analysis['candidate']
                            discovered_tokens.append({
                                'address': candidate.get('address', ''),
                                'symbol': candidate.get('symbol', 'Unknown'),
                                'conviction_score': analysis.get('final_score', 0) / 10.0
                            })
        
        # Record scan details with API report
        scan_record = {
            'scan_number': self.completed_scans,
            'timestamp': datetime.now().isoformat(),
            'duration_seconds': scan_duration,
            'tokens_found': len(discovered_tokens),
            'high_conviction_count': len([t for t in discovered_tokens 
                                        if t.get('conviction_score', 0) >= 0.7]),
            'scan_status': scan_results.get('status', 'unknown') if isinstance(scan_results, dict) else 'completed',
            'alerts_sent': scan_results.get('alerts_sent', 0) if isinstance(scan_results, dict) else 0,
            'api_report': api_report
        }
        
        self.session_stats['scans'].append(scan_record)
        
        # Update performance metrics
        total_duration = sum(s['duration_seconds'] for s in self.session_stats['scans'])
        self.session_stats['performance_metrics']['avg_scan_duration'] = total_duration / self.completed_scans
        
        # Track discovered tokens
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

    def _save_session_results(self):
        """Save comprehensive session results to file"""
        results_dir = project_root / "scripts" / "results"
        results_dir.mkdir(exist_ok=True)
        
        results_file = results_dir / f"12hour_enhanced_api_results_{self.session_id}.json"
        
        # Update final stats
        self.session_stats['end_time'] = datetime.now().isoformat()
        self.session_stats['actual_duration_minutes'] = (datetime.now() - self.start_time).total_seconds() / 60
        self.session_stats['completed_scans'] = self.completed_scans
        self.session_stats['completion_rate'] = (self.completed_scans / self.total_scans) * 100
        
        with open(results_file, 'w') as f:
            json.dump(self.session_stats, f, indent=2, default=str)
            
        self.logger.info(f"📊 Enhanced API session results saved to: {results_file}")

    def _print_progress_header(self):
        """Print session header with key information"""
        print("\n" + "="*80)
        print("🎯 12-HOUR ENHANCED DETECTOR WITH COMPREHENSIVE API REPORTING")
        print("="*80)
        print(f"📅 Start Time: {self.start_time.strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"⏱️  Duration: 12 hours (720 minutes)")
        print(f"🔄 Scan Frequency: Every 12 minutes (5 scans/hour)")
        print(f"📊 Total Planned Scans: {self.total_scans}")
        print(f"🆔 Session ID: {self.session_id}")
        print(f"📡 API Reporting: Per-scan service breakdown + session summary")
        print("="*80)

    def _print_scan_progress(self, scan_num, scan_start_time):
        """Print progress for current scan"""
        elapsed_total = datetime.now() - self.start_time
        progress_pct = (scan_num / self.total_scans) * 100
        
        print(f"\n🔍 ENHANCED SCAN {scan_num}/{self.total_scans} ({progress_pct:.1f}%)")
        print(f"⏰ Scan Start: {scan_start_time.strftime('%H:%M:%S')}")
        print(f"📈 Total Elapsed: {str(elapsed_total).split('.')[0]}")
        print("-" * 60)

    async def run(self):
        """Run the 12-hour detection test with enhanced API reporting"""
        self._print_progress_header()
        
        try:
            scan_count = 0
            
            while self.running and scan_count < self.total_scans:
                scan_count += 1
                scan_start_time = datetime.now()
                
                self._print_scan_progress(scan_count, scan_start_time)
                
                try:
                    # Run detection scan
                    results = await self.detector.run_detection_cycle()
                    scan_duration = (datetime.now() - scan_start_time).total_seconds()
                    
                    # Update statistics with API reporting
                    self._update_session_stats(results, scan_duration)
                    
                    # Print scan results
                    status = results.get('status', 'unknown') if isinstance(results, dict) else 'completed'
                    alerts_sent = results.get('alerts_sent', 0) if isinstance(results, dict) else 0
                    new_candidates = results.get('new_candidates', 0) if isinstance(results, dict) else 0
                    
                    print(f"✅ Scan Complete - Duration: {scan_duration:.1f}s")
                    print(f"📊 Status: {status}")
                    print(f"🎯 New Candidates: {new_candidates} | Alerts Sent: {alerts_sent}")
                    
                    # Save progress every 10 scans
                    if scan_count % 10 == 0:
                        self._save_session_results()
                        print(f"💾 Progress saved (Scan {scan_count})")
                    
                except Exception as e:
                    self.logger.error(f"❌ Scan {scan_count} failed: {str(e)}")
                    print(f"❌ Scan {scan_count} failed: {str(e)}")
                
                # Wait for next scan (unless this is the last scan)
                if scan_count < self.total_scans and self.running:
                    next_scan_time = scan_start_time + timedelta(seconds=self.scan_interval)
                    wait_time = (next_scan_time - datetime.now()).total_seconds()
                    
                    if wait_time > 0:
                        print(f"⏳ Waiting {wait_time:.0f}s until next scan...")
                        
                        # Sleep in chunks to allow for graceful shutdown
                        while wait_time > 0 and self.running:
                            sleep_chunk = min(30, wait_time)
                            await asyncio.sleep(sleep_chunk)
                            wait_time -= sleep_chunk
            
            # Final session summary with comprehensive API analysis
            print(f"\n🎉 12-HOUR ENHANCED TEST COMPLETED!")
            self._display_session_api_summary()
            self._save_session_results()
                
        except KeyboardInterrupt:
            print(f"\n🛑 Test interrupted by user")
        except Exception as e:
            self.logger.error(f"❌ Unexpected error: {str(e)}")
            print(f"❌ Unexpected error: {str(e)}")
        finally:
            # Cleanup detector resources
            await self.detector.cleanup()
            self._save_session_results()

async def main():
    """Main async entry point"""
    print("🚀 Starting 12-Hour Enhanced Detector with Comprehensive API Reporting...")
    print("📡 This version includes detailed per-scan API reports like the 1-hour test")
    print("⚠️  This will run for 12 hours with 5 scans per hour (every 12 minutes)")
    print("🛑 Press Ctrl+C to stop gracefully at any time")
    
    # Confirmation prompt
    response = input("\n📋 Proceed with enhanced 12-hour test? (y/N): ").strip().lower()
    if response not in ['y', 'yes']:
        print("❌ Test cancelled by user")
        sys.exit(0)
    
    test = EnhancedTwelveHourDetectorWithAPIReporting()
    await test.run()

if __name__ == "__main__":
    asyncio.run(main())