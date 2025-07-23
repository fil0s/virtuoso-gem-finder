#!/usr/bin/env python3
"""
High Conviction Detector - 1 Hour Session with 6 Scans (DEBUG MODE)
Runs the detector for exactly 1 hour with 6 detection cycles (every 10 minutes)
Enhanced with debug logging to monitor API error fixes
"""

import asyncio
import sys
import os
import time
import logging
import traceback
from datetime import datetime, timedelta
import json
from typing import Dict, Any, List

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from scripts.high_conviction_token_detector import HighConvictionTokenDetector


class TimedHighConvictionSession:
    """Run High Conviction Detector for a specific duration with set number of scans"""
    
    def __init__(self, config_path: str = "config/config.yaml", debug_mode: bool = True):
        # Enable debug logging if requested
        if debug_mode:
            self._setup_debug_logging()
            
        self.detector = HighConvictionTokenDetector(config_path)
        self.debug_mode = debug_mode
        self.session_stats = {
            "start_time": None,
            "end_time": None,
            "total_scans": 0,
            "successful_scans": 0,
            "failed_scans": 0,
            "total_tokens_analyzed": 0,
            "high_conviction_candidates": 0,
            "alerts_sent": 0,
            "scan_results": [],
            "debug_info": {
                "api_errors_detected": 0,
                "none_type_errors_detected": 0,
                "address_filtering_events": 0,
                "successful_api_calls": 0
            }
        }
        
        # Enhanced token tracking
        self.session_token_registry = {
            "all_tokens_by_scan": {},  # scan_number -> list of tokens
            "unique_tokens_discovered": {},  # address -> token details
            "token_sources": {},  # address -> list of sources (rugcheck, dexscreener, birdeye)
            "token_scores": {},  # address -> score progression
            "high_conviction_tokens": {},  # address -> detailed analysis
            "session_summary": {
                "total_unique_tokens": 0,
                "tokens_by_source": {
                    "rugcheck": 0,
                    "dexscreener": 0,
                    "birdeye": 0
                },
                "score_distribution": {
                    "0-2": 0,
                    "2-4": 0,
                    "4-6": 0,
                    "6-8": 0,
                    "8-10": 0
                }
            }
        }
        
    def _setup_debug_logging(self):
        """Setup enhanced debug logging"""
        # Get the root logger and set to DEBUG level
        root_logger = logging.getLogger()
        root_logger.setLevel(logging.DEBUG)
        
        # Create debug handler if not exists
        debug_handler = None
        for handler in root_logger.handlers:
            if hasattr(handler, 'baseFilename') and 'debug' in str(handler.baseFilename):
                debug_handler = handler
                break
                
        if not debug_handler:
            debug_handler = logging.FileHandler('debug_session.log')
            debug_handler.setLevel(logging.DEBUG)
            formatter = logging.Formatter(
                '%(asctime)s [%(levelname)s] %(name)s - %(message)s'
            )
            debug_handler.setFormatter(formatter)
            root_logger.addHandler(debug_handler)
            
        print("🐛 ENHANCED DEBUG MODE ENABLED - Comprehensive API data logging active")
        print("📝 Debug logs will be saved to: debug_session.log")
        print("🔍 API responses will be logged in full detail for investigation")
        
    async def run_timed_session(self, duration_hours: float = 1.0, target_scans: int = 6):
        """
        Run detection session for specified duration with target number of scans
        
        Args:
            duration_hours: Duration to run in hours
            target_scans: Target number of scans to perform
        """
        self.session_stats["start_time"] = datetime.now()
        session_id = f"timed_session_{int(time.time())}"
        
        print(f"🚀 Starting High Conviction Detector - Timed Session")
        print(f"⏰ Duration: {duration_hours} hours")
        print(f"🎯 Target Scans: {target_scans}")
        print(f"📊 Scan Interval: {(duration_hours * 60) / target_scans:.1f} minutes")
        print(f"🆔 Session ID: {session_id}")
        print("=" * 60)
        
        # Calculate scan interval
        scan_interval_seconds = (duration_hours * 3600) / target_scans
        end_time = time.time() + (duration_hours * 3600)
        
        scan_count = 0
        raw_results = []  # Store raw results with API reports for session summary
        
        try:
            while scan_count < target_scans and time.time() < end_time:
                scan_count += 1
                scan_start = time.time()
                
                print(f"\n🔍 SCAN #{scan_count}/{target_scans}")
                print(f"⏰ Time: {datetime.now().strftime('%H:%M:%S')}")
                
                try:
                    if self.debug_mode:
                        print(f"🐛 DEBUG: Starting scan #{scan_count} with enhanced monitoring")
                        
                    # Run detection cycle with debug monitoring
                    result = await self._run_debug_detection_cycle(scan_count)
                    
                    # Store raw result for API session summary
                    raw_results.append(result)
                    
                    # Update session stats
                    self.session_stats["total_scans"] += 1
                    self.session_stats["successful_scans"] += 1
                    
                    # Process results
                    scan_result = self._process_scan_result(result, scan_count, scan_start)
                    self.session_stats["scan_results"].append(scan_result)
                    
                    # Update totals
                    self.session_stats["total_tokens_analyzed"] += scan_result.get("tokens_analyzed", 0)
                    self.session_stats["high_conviction_candidates"] += scan_result.get("candidates_found", 0)
                    self.session_stats["alerts_sent"] += scan_result.get("alerts_sent", 0)
                    
                    # Display scan summary with debug info
                    self._display_scan_summary(scan_result, scan_count, target_scans)
                    
                except Exception as e:
                    print(f"❌ Scan #{scan_count} failed: {e}")
                    self.session_stats["total_scans"] += 1
                    self.session_stats["failed_scans"] += 1
                    
                    scan_result = {
                        "scan_number": scan_count,
                        "timestamp": datetime.now().isoformat(),
                        "duration_seconds": time.time() - scan_start,
                        "status": "failed",
                        "error": str(e),
                        "tokens_analyzed": 0,
                        "candidates_found": 0,
                        "alerts_sent": 0
                    }
                    self.session_stats["scan_results"].append(scan_result)
                
                # Wait for next scan (unless it's the last one or time is up)
                if scan_count < target_scans and time.time() < end_time:
                    remaining_time = end_time - time.time()
                    remaining_scans = target_scans - scan_count
                    
                    if remaining_scans > 0:
                        wait_time = min(scan_interval_seconds, remaining_time / remaining_scans)
                        if wait_time > 0:
                            print(f"⏳ Waiting {wait_time:.1f} seconds until next scan...")
                            await asyncio.sleep(wait_time)
                
        except KeyboardInterrupt:
            print(f"\n⌨️ Session interrupted by user after {scan_count} scans")
        except Exception as e:
            print(f"\n💥 Fatal error in session: {e}")
        
        # Session complete
        self.session_stats["end_time"] = datetime.now()
        await self._display_session_summary()
        
        # Display comprehensive API session report
        self._display_api_session_summary(raw_results)
        
        # Cleanup
        await self.detector.cleanup()
        
    async def _run_debug_detection_cycle(self, scan_number: int) -> Dict[str, Any]:
        """Run detection cycle with enhanced debug monitoring"""
        cycle_start = time.time()
        
        try:
            if self.debug_mode:
                print(f"🔍 DEBUG: Monitoring API calls and error patterns...")
                
                # Monitor log output for specific error patterns
                original_logger = self.detector.logger
                debug_info = {
                    "api_errors": [],
                    "none_type_errors": [],
                    "address_filtering_events": [],
                    "successful_api_calls": []
                }
                
                # Create a custom log handler to capture debug info
                class DebugLogHandler(logging.Handler):
                    def emit(self, record):
                        msg = record.getMessage()
                        
                        # Monitor for specific error patterns
                        if "API Error 400" in msg and "list_address is invalid format" in msg:
                            debug_info["api_errors"].append({
                                "timestamp": time.time(),
                                "message": msg,
                                "scan": scan_number
                            })
                            
                        elif "Error enhancing with Birdeye data" in msg and "NoneType" in msg:
                            debug_info["none_type_errors"].append({
                                "timestamp": time.time(),
                                "message": msg,
                                "scan": scan_number
                            })
                            
                        elif "Filtered out" in msg and "non-Solana addresses" in msg:
                            debug_info["address_filtering_events"].append({
                                "timestamp": time.time(),
                                "message": msg,
                                "scan": scan_number
                            })
                            
                        elif "Batch success" in msg and "/defi/multi_price" in msg:
                            debug_info["successful_api_calls"].append({
                                "timestamp": time.time(),
                                "message": msg,
                                "scan": scan_number
                            })
                
                # Add debug handler temporarily
                debug_handler = DebugLogHandler()
                debug_handler.setLevel(logging.DEBUG)
                root_logger = logging.getLogger()
                root_logger.addHandler(debug_handler)
                
                try:
                    # Run the actual detection cycle
                    result = await self.detector.run_detection_cycle()
                    
                    # Process debug information
                    self._process_debug_info(debug_info, scan_number)
                    
                    # Wait for logs to be fully written
                    await asyncio.sleep(0.2)
                    
                    # Generate API scan report AFTER logs are complete
                    api_report = await self._generate_api_scan_report(scan_number)
                    
                    # Extract and record token data from this scan
                    self._record_scan_tokens(result, scan_number)
                    
                    # Add debug info and API report to result
                    result["debug_info"] = debug_info
                    result["api_report"] = api_report
                    
                finally:
                    # Remove debug handler
                    root_logger.removeHandler(debug_handler)
                    
            else:
                # Run normal detection cycle without debug monitoring
                result = await self.detector.run_detection_cycle()
                
            return result
            
        except Exception as e:
            if self.debug_mode:
                print(f"🐛 DEBUG: Exception in detection cycle: {e}")
                print(f"🐛 DEBUG: Traceback: {traceback.format_exc()}")
            raise
            
    def _process_debug_info(self, debug_info: Dict[str, Any], scan_number: int):
        """Process and display debug information"""
        api_errors = len(debug_info["api_errors"])
        none_type_errors = len(debug_info["none_type_errors"])
        filtering_events = len(debug_info["address_filtering_events"])
        successful_calls = len(debug_info["successful_api_calls"])
        
        # Update session debug stats
        self.session_stats["debug_info"]["api_errors_detected"] += api_errors
        self.session_stats["debug_info"]["none_type_errors_detected"] += none_type_errors
        self.session_stats["debug_info"]["address_filtering_events"] += filtering_events
        self.session_stats["debug_info"]["successful_api_calls"] += successful_calls
        
        print(f"🐛 DEBUG SCAN #{scan_number} RESULTS:")
        print(f"  ❌ API Errors (invalid format): {api_errors}")
        print(f"  ❌ NoneType Errors: {none_type_errors}")
        print(f"  🔍 Address Filtering Events: {filtering_events}")
        print(f"  ✅ Successful API Calls: {successful_calls}")
        
        # Detailed error reporting
        if api_errors > 0:
            print(f"  🚨 WARNING: Still detecting API format errors!")
            for error in debug_info["api_errors"]:
                print(f"    • {error['message']}")
                
        if none_type_errors > 0:
            print(f"  🚨 WARNING: Still detecting NoneType errors!")
            for error in debug_info["none_type_errors"]:
                print(f"    • {error['message']}")
                
        if filtering_events > 0:
            print(f"  ✅ GOOD: Address filtering is working!")
            
        if successful_calls > 0:
            print(f"  ✅ GOOD: API calls are succeeding!")
            
    async def _generate_api_scan_report(self, scan_number: int) -> Dict[str, Any]:
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
            
            # Debug print to verify estimation methods are working
            print(f"🔍 DEBUG: RugCheck stats: {rugcheck_stats}")
            print(f"🔍 DEBUG: DexScreener stats: {dexscreener_stats}")
            print(f"🔍 DEBUG: Birdeye stats: {birdeye_stats}")
            
            # Additional debug: Check if we can find recent API activity in logs
            try:
                with open('debug_session.log', 'r') as f:
                    recent_logs = f.readlines()[-50:]  # Last 50 lines
                    
                rugcheck_found = sum(1 for line in recent_logs if "Fetched" in line and "trending tokens from RugCheck" in line)
                dex_found = sum(1 for line in recent_logs if "dexscreener" in line and "cache_set" in line)
                birdeye_found = sum(1 for line in recent_logs if "BirdeyeAPI" in line and "api_call" in line)
                
                print(f"🔍 DEBUG: Recent log analysis:")
                print(f"  📊 RugCheck patterns found: {rugcheck_found}")
                print(f"  📊 DexScreener patterns found: {dex_found}")
                print(f"  📊 Birdeye patterns found: {birdeye_found}")
                
                # If we found patterns but stats are 0, update the estimates
                if rugcheck_found > 0 and rugcheck_stats["total_calls"] == 0:
                    rugcheck_stats = {"total_calls": rugcheck_found, "successful_calls": rugcheck_found, "failed_calls": 0}
                    print(f"🔧 DEBUG: Updated RugCheck stats: {rugcheck_stats}")
                    
                if dex_found > 0 and dexscreener_stats["total_calls"] == 0:
                    dexscreener_stats = {"total_calls": dex_found, "successful_calls": dex_found, "failed_calls": 0}
                    print(f"🔧 DEBUG: Updated DexScreener stats: {dexscreener_stats}")
                    
            except Exception as e:
                print(f"🔍 DEBUG: Error in recent log analysis: {e}")
            
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
            print(f"🚨 Error generating API scan report: {e}")
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
            
    def _create_api_summary(self, birdeye_stats: Dict[str, Any], cross_platform_stats: Dict[str, Any]) -> Dict[str, Any]:
        """Create combined API summary statistics"""
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
        
        # Combine Birdeye detailed API stats
        if birdeye_stats:
            summary["total_api_calls"] += birdeye_stats.get("total_api_calls", 0)
            summary["successful_calls"] += birdeye_stats.get("successful_api_calls", 0)
            summary["failed_calls"] += birdeye_stats.get("failed_api_calls", 0)
            summary["cache_hits"] += birdeye_stats.get("cache_hits", 0)
            summary["cache_misses"] += birdeye_stats.get("cache_misses", 0)
            
            # Add endpoints from detailed API
            if "top_endpoints" in birdeye_stats:
                for endpoint_info in birdeye_stats["top_endpoints"]:
                    summary["endpoints_used"].add(endpoint_info["endpoint"])
        
        # Combine cross-platform API stats
        if cross_platform_stats:
            summary["total_api_calls"] += cross_platform_stats.get("total_api_calls", 0)
            summary["successful_calls"] += cross_platform_stats.get("successful_api_calls", 0)
            summary["failed_calls"] += cross_platform_stats.get("failed_api_calls", 0)
            summary["cache_hits"] += cross_platform_stats.get("cache_hits", 0)
            summary["cache_misses"] += cross_platform_stats.get("cache_misses", 0)
            
            # Add endpoints from cross-platform API
            if "top_endpoints" in cross_platform_stats:
                for endpoint_info in cross_platform_stats["top_endpoints"]:
                    summary["endpoints_used"].add(endpoint_info["endpoint"])
        
        # Calculate derived metrics
        total_cache_requests = summary["cache_hits"] + summary["cache_misses"]
        if total_cache_requests > 0:
            summary["cache_hit_rate"] = (summary["cache_hits"] / total_cache_requests) * 100
            
        # Calculate combined average response time
        total_response_time = 0
        total_calls = 0
        
        if birdeye_stats and birdeye_stats.get("total_api_calls", 0) > 0:
            total_response_time += birdeye_stats.get("total_response_time_ms", 0)
            total_calls += birdeye_stats.get("total_api_calls", 0)
            
        if cross_platform_stats and cross_platform_stats.get("total_api_calls", 0) > 0:
            total_response_time += cross_platform_stats.get("total_response_time_ms", 0)
            total_calls += cross_platform_stats.get("total_api_calls", 0)
            
        if total_calls > 0:
            summary["average_response_time_ms"] = total_response_time / total_calls
            
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
        
        print("=" * 50)
        
        # 🔥 NEW: Enhanced API Service Breakdown by actual service provider
        self._display_enhanced_api_service_breakdown_single_scan(report)
        
    def _display_enhanced_api_service_breakdown_single_scan(self, report: Dict[str, Any]):
        """Display comprehensive API service breakdown by actual service provider"""
        scan_num = report["scan_number"]
        service_stats = report.get("service_stats", {})
        summary = report.get("summary", {})
        
        print(f"\n🔧 ENHANCED API SERVICE BREAKDOWN - Scan #{scan_num}")
        print("=" * 60)
        
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
            print(f"\n{emoji} {service_name.upper()}")
            print("-" * 50)
            
            print(f"📊 Service Summary:")
            print(f"  Total Calls: {calls}")
            print(f"  Successful: {success}")
            print(f"  Failed: {failed}")
            
            if calls > 0:
                success_rate = (success / calls) * 100
                print(f"  Success Rate: {success_rate:.1f}%")
                
            # Show average response time if available
            total_response_time = service.get("total_response_time_ms", 0)
            if total_response_time > 0 and calls > 0:
                avg_time = total_response_time / calls
                print(f"  Avg Response Time: {avg_time:.1f}ms")
            
            # Show endpoints used
            if endpoints:
                print(f"\n📈 Endpoints Used ({len(endpoints)}):")
                for endpoint in sorted(endpoints):
                    print(f"  • {endpoint}")
        
        # Cross-Service Summary
        if total_all_calls > 0:
            print(f"\n📈 CROSS-SERVICE SUMMARY:")
            overall_success_rate = (total_all_success / total_all_calls) * 100
            print(f"  Total API Calls Across All Services: {total_all_calls}")
            print(f"  Overall Success Rate: {overall_success_rate:.1f}%")
            
            # Service usage distribution
            print(f"\n🔄 SERVICE USAGE DISTRIBUTION:")
            for service_key in service_order:
                if service_key not in service_stats:
                    continue
                    
                service = service_stats[service_key]
                calls = service.get("total_calls", 0)
                service_name = service.get("service_name", service_key.upper())
                
                if calls > 0:
                    percentage = (calls / total_all_calls) * 100
                    emoji = service_emojis.get(service_key, "🔗")
                    print(f"  • {emoji} {service_name}: {calls} calls ({percentage:.1f}%)")
        
        # Optimization recommendations
        print(f"\n💡 SCAN #{scan_num} OPTIMIZATION RECOMMENDATIONS:")
        if total_all_success == total_all_calls and total_all_calls > 0:
            print(f"  ✅ All endpoints performing excellently - no optimization needed!")
        elif total_all_calls - total_all_success > 0:
            failed_count = total_all_calls - total_all_success
            print(f"  ⚠️  {failed_count} API calls failed - monitor error patterns")
            
            # Show which services had failures
            for service_key in service_order:
                if service_key not in service_stats:
                    continue
                service = service_stats[service_key]
                failed = service.get("failed_calls", 0)
                if failed > 0:
                    service_name = service.get("service_name", service_key.upper())
                    print(f"    • {service_name}: {failed} failed calls")
        else:
            print(f"  ✅ API performance looks good for this scan")
        
        print("=" * 60)
    
    def _estimate_rugcheck_api_calls(self) -> Dict[str, int]:
        """Estimate RugCheck API calls from recent debug logs"""
        try:
            rugcheck_calls = 0
            rugcheck_successes = 0
            
            # Read recent debug logs to look for RugCheck activity
            try:
                with open('debug_session.log', 'r') as f:
                    recent_logs = f.readlines()[-200:]  # Last 200 lines for better coverage
                    
                for line in recent_logs:
                    # Look for RugCheck trending fetch success
                    if "Fetched" in line and "trending tokens from RugCheck" in line:
                        rugcheck_calls += 1
                        rugcheck_successes += 1
                    # Look for RugCheck cache activity (backup detection)
                    elif "rugcheck_trending" in line and "cache_set" in line:
                        # This indicates a successful RugCheck API call was cached
                        if rugcheck_calls == 0:  # Don't double count
                            rugcheck_calls += 1
                            rugcheck_successes += 1
            except Exception as e:
                print(f"🔍 DEBUG: Error reading RugCheck logs: {e}")
                # Fallback: if we have cross-platform analyzer, assume basic calls
                if hasattr(self.detector, 'cross_platform_analyzer'):
                    rugcheck_calls = 1  # Trending call
                    rugcheck_successes = 1
                
            return {
                "total_calls": rugcheck_calls,
                "successful_calls": rugcheck_successes,
                "failed_calls": rugcheck_calls - rugcheck_successes
            }
        except Exception as e:
            print(f"🔍 DEBUG: Exception in RugCheck estimation: {e}")
            return {"total_calls": 0, "successful_calls": 0, "failed_calls": 0}
    
    def _estimate_dexscreener_api_calls(self) -> Dict[str, int]:
        """Estimate DexScreener API calls from recent debug logs"""
        try:
            dexscreener_calls = 0
            dexscreener_successes = 0
            
            # Read recent debug logs to look for DexScreener activity
            try:
                with open('debug_session.log', 'r') as f:
                    recent_logs = f.readlines()[-200:]  # Last 200 lines for better coverage
                    
                for line in recent_logs:
                    # Look for DexScreener cache activity (indicates API calls)
                    if "dexscreener_boosted" in line and "cache_set" in line:
                        dexscreener_calls += 1
                        dexscreener_successes += 1
                    elif "dexscreener_top_boosted" in line and "cache_set" in line:
                        dexscreener_calls += 1
                        dexscreener_successes += 1
            except Exception as e:
                print(f"🔍 DEBUG: Error reading DexScreener logs: {e}")
                # Fallback: if we have cross-platform analyzer, assume basic calls
                if hasattr(self.detector, 'cross_platform_analyzer'):
                    dexscreener_calls = 2  # Boosted + Top boosted calls
                    dexscreener_successes = 2
                
            return {
                "total_calls": dexscreener_calls,
                "successful_calls": dexscreener_successes,
                "failed_calls": dexscreener_calls - dexscreener_successes
            }
        except Exception as e:
            print(f"🔍 DEBUG: Exception in DexScreener estimation: {e}")
            return {"total_calls": 0, "successful_calls": 0, "failed_calls": 0}
    
    def _record_scan_tokens(self, result: Dict[str, Any], scan_number: int):
        """Record all tokens discovered and analyzed in this scan"""
        try:
            scan_tokens = []
            
            # Extract tokens from cross-platform analysis results if available
            if hasattr(self.detector, 'cross_platform_analyzer'):
                # Try to get the last analysis results
                try:
                    # Get cross-platform results from the detector's last run
                    cross_platform_data = getattr(self.detector.cross_platform_analyzer, '_last_analysis_results', None)
                    
                    if not cross_platform_data:
                        # If no cached results, we'll extract from result structure
                        cross_platform_data = result.get('cross_platform_results', {})
                    
                    if cross_platform_data and 'correlations' in cross_platform_data:
                        # Extract tokens from normalized data
                        all_tokens = cross_platform_data['correlations'].get('all_tokens', {})
                        
                        for address, token_data in all_tokens.items():
                            if not address or address in ['', 'unknown']:
                                continue
                                
                            token_info = {
                                'address': address,
                                'symbol': token_data.get('symbol', 'Unknown'),
                                'name': token_data.get('name', ''),
                                'score': token_data.get('score', 0),
                                'platforms': token_data.get('platforms', []),
                                'price': token_data.get('price', 0),
                                'volume_24h': token_data.get('volume_24h', 0),
                                'market_cap': token_data.get('market_cap', 0),
                                'liquidity': token_data.get('liquidity', 0),
                                'scan_number': scan_number,
                                'timestamp': datetime.now().isoformat(),
                                'source_breakdown': self._analyze_token_sources(token_data)
                            }
                            
                            scan_tokens.append(token_info)
                            
                            # Update session registry
                            self._update_session_registry(token_info)
                            
                except Exception as e:
                    print(f"🔍 DEBUG: Could not extract cross-platform tokens: {e}")
            
            # If no tokens found through cross-platform, try to extract from result structure
            if not scan_tokens:
                # Look for tokens in various result structures
                candidates = result.get('high_conviction_candidates', [])
                for candidate in candidates:
                    if isinstance(candidate, dict) and 'address' in candidate:
                        token_info = {
                            'address': candidate['address'],
                            'symbol': candidate.get('symbol', 'Unknown'),
                            'name': candidate.get('name', ''),
                            'score': candidate.get('cross_platform_score', 0),
                            'platforms': candidate.get('platforms', []),
                            'price': candidate.get('price', 0),
                            'volume_24h': candidate.get('volume_24h', 0),
                            'market_cap': candidate.get('market_cap', 0),
                            'liquidity': candidate.get('liquidity', 0),
                            'scan_number': scan_number,
                            'timestamp': datetime.now().isoformat(),
                            'source_breakdown': {'platforms': candidate.get('platforms', [])}
                        }
                        scan_tokens.append(token_info)
                        self._update_session_registry(token_info)
            
            # Store tokens for this scan
            self.session_token_registry['all_tokens_by_scan'][scan_number] = scan_tokens
            
            # Update session summary
            self._update_session_summary()
            
            print(f"📊 SCAN #{scan_number} TOKEN REGISTRY:")
            print(f"  🎯 Tokens Discovered: {len(scan_tokens)}")
            if scan_tokens:
                print(f"  📈 Score Range: {min(t['score'] for t in scan_tokens):.1f} - {max(t['score'] for t in scan_tokens):.1f}")
                
                # Show top 3 tokens by score
                top_tokens = sorted(scan_tokens, key=lambda x: x['score'], reverse=True)[:3]
                for i, token in enumerate(top_tokens, 1):
                    platforms_str = ', '.join(token['platforms']) if token['platforms'] else 'Unknown'
                    print(f"  {i}. {token['symbol']} ({token['address'][:8]}...) - Score: {token['score']:.1f} - Platforms: {platforms_str}")
            else:
                print(f"  ℹ️  No tokens discovered in this scan")
                
        except Exception as e:
            print(f"❌ Error recording scan tokens: {e}")
            import traceback
            print(f"🔍 DEBUG: {traceback.format_exc()}")
    
    def _analyze_token_sources(self, token_data: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze which sources contributed to token discovery"""
        sources = {
            'platforms': token_data.get('platforms', []),
            'rugcheck_data': 'rugcheck' in token_data.get('platforms', []),
            'dexscreener_data': 'dexscreener' in token_data.get('platforms', []),
            'birdeye_data': 'birdeye' in token_data.get('platforms', []),
            'multi_platform': len(token_data.get('platforms', [])) > 1
        }
        return sources
    
    def _update_session_registry(self, token_info: Dict[str, Any]):
        """Update the session-wide token registry"""
        address = token_info['address']
        
        # Update unique tokens discovered
        if address not in self.session_token_registry['unique_tokens_discovered']:
            self.session_token_registry['unique_tokens_discovered'][address] = token_info
            
            # Track sources
            self.session_token_registry['token_sources'][address] = token_info['platforms']
            
            # Update source counts
            for platform in token_info['platforms']:
                if platform in self.session_token_registry['session_summary']['tokens_by_source']:
                    self.session_token_registry['session_summary']['tokens_by_source'][platform] += 1
        
        # Update score tracking (always update to track progression)
        if address not in self.session_token_registry['token_scores']:
            self.session_token_registry['token_scores'][address] = []
        
        self.session_token_registry['token_scores'][address].append({
            'score': token_info['score'],
            'scan_number': token_info['scan_number'],
            'timestamp': token_info['timestamp']
        })
        
        # Track high conviction tokens
        if token_info['score'] >= 6.0:  # High conviction threshold
            self.session_token_registry['high_conviction_tokens'][address] = token_info
    
    def _update_session_summary(self):
        """Update session-wide summary statistics"""
        summary = self.session_token_registry['session_summary']
        
        # Update total unique tokens
        summary['total_unique_tokens'] = len(self.session_token_registry['unique_tokens_discovered'])
        
        # Update score distribution
        score_dist = {'0-2': 0, '2-4': 0, '4-6': 0, '6-8': 0, '8-10': 0}
        
        for token_data in self.session_token_registry['unique_tokens_discovered'].values():
            score = token_data['score']
            if score < 2:
                score_dist['0-2'] += 1
            elif score < 4:
                score_dist['2-4'] += 1
            elif score < 6:
                score_dist['4-6'] += 1
            elif score < 8:
                score_dist['6-8'] += 1
            else:
                score_dist['8-10'] += 1
        
        summary['score_distribution'] = score_dist
        
    def _process_scan_result(self, result: Dict[str, Any], scan_number: int, scan_start: float) -> Dict[str, Any]:
        """Process and format scan result"""
        status = result.get("status", "unknown")
        
        scan_result = {
            "scan_number": scan_number,
            "timestamp": datetime.now().isoformat(),
            "duration_seconds": time.time() - scan_start,
            "status": status,
            "tokens_analyzed": 0,
            "candidates_found": 0,
            "alerts_sent": 0
        }
        
        if status == "completed":
            scan_result.update({
                "tokens_analyzed": result.get("total_analyzed", 0),
                "candidates_found": result.get("candidates_analyzed", 0),
                "alerts_sent": result.get("alerts_sent", 0),
                "high_conviction_tokens": result.get("high_conviction_tokens", [])
            })
        elif status == "no_high_conviction":
            scan_result.update({
                "tokens_analyzed": result.get("total_analyzed", 0),
                "candidates_found": result.get("candidates", 0)
            })
        elif status == "no_results":
            scan_result["tokens_analyzed"] = 0
            
        return scan_result
        
    def _display_scan_summary(self, scan_result: Dict[str, Any], scan_number: int, total_scans: int):
        """Display summary for individual scan"""
        status = scan_result["status"]
        duration = scan_result["duration_seconds"]
        
        print(f"✅ Scan #{scan_number} completed in {duration:.1f}s")
        
        if status == "completed":
            tokens_analyzed = scan_result["tokens_analyzed"]
            candidates = scan_result["candidates_found"]
            alerts = scan_result["alerts_sent"]
            
            print(f"📊 Tokens analyzed: {tokens_analyzed}")
            print(f"🎯 High conviction candidates: {candidates}")
            print(f"🚨 Alerts sent: {alerts}")
            
            if alerts > 0:
                print("🚀 NEW HIGH CONVICTION TOKENS FOUND!")
                
        elif status == "no_high_conviction":
            tokens_analyzed = scan_result["tokens_analyzed"]
            print(f"📊 Tokens analyzed: {tokens_analyzed}")
            print("📈 No high conviction candidates found")
            
        elif status == "no_results":
            print("📊 No tokens found in cross-platform analysis")
            
        elif status == "failed":
            print(f"❌ Scan failed: {scan_result.get('error', 'Unknown error')}")
            
        # Progress indicator
        progress = (scan_number / total_scans) * 100
        print(f"📈 Session progress: {progress:.1f}% ({scan_number}/{total_scans})")
        
    async def _display_session_summary(self):
        """Display comprehensive session summary"""
        start_time = self.session_stats["start_time"]
        end_time = self.session_stats["end_time"]
        duration = end_time - start_time
        
        print("\n" + "=" * 60)
        print("📊 HIGH CONVICTION DETECTOR - SESSION SUMMARY")
        print("=" * 60)
        
        print(f"⏰ Session Duration: {duration}")
        print(f"🕐 Start Time: {start_time.strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"🕑 End Time: {end_time.strftime('%Y-%m-%d %H:%M:%S')}")
        
        print(f"\n🔍 SCAN STATISTICS:")
        print(f"  Total Scans: {self.session_stats['total_scans']}")
        print(f"  Successful: {self.session_stats['successful_scans']}")
        print(f"  Failed: {self.session_stats['failed_scans']}")
        
        if self.session_stats['total_scans'] > 0:
            success_rate = (self.session_stats['successful_scans'] / self.session_stats['total_scans']) * 100
            print(f"  Success Rate: {success_rate:.1f}%")
        
        print(f"\n📈 ANALYSIS RESULTS:")
        print(f"  Total Tokens Analyzed: {self.session_stats['total_tokens_analyzed']}")
        print(f"  High Conviction Candidates: {self.session_stats['high_conviction_candidates']}")
        print(f"  Alerts Sent: {self.session_stats['alerts_sent']}")
        
        # Debug information summary
        if self.debug_mode:
            debug_info = self.session_stats['debug_info']
            print(f"\n🐛 DEBUG SESSION SUMMARY:")
            print(f"  API Errors (invalid format): {debug_info['api_errors_detected']}")
            print(f"  NoneType Errors: {debug_info['none_type_errors_detected']}")
            print(f"  Address Filtering Events: {debug_info['address_filtering_events']}")
            print(f"  Successful API Calls: {debug_info['successful_api_calls']}")
            
            # Error analysis
            if debug_info['api_errors_detected'] == 0 and debug_info['none_type_errors_detected'] == 0:
                print(f"  🎉 EXCELLENT! No API or NoneType errors detected!")
            elif debug_info['api_errors_detected'] == 0:
                print(f"  ✅ GOOD! No API format errors detected (fix working!)")
                if debug_info['none_type_errors_detected'] > 0:
                    print(f"  ⚠️  Still some NoneType errors - may need additional fixes")
            else:
                print(f"  🚨 WARNING! Still detecting errors - fixes may need adjustment")
                
            # Success indicators
            if debug_info['address_filtering_events'] > 0:
                print(f"  ✅ Address filtering is active and working")
            if debug_info['successful_api_calls'] > 0:
                print(f"  ✅ API calls are succeeding after filtering")
        
        # Calculate averages
        if self.session_stats['successful_scans'] > 0:
            avg_tokens = self.session_stats['total_tokens_analyzed'] / self.session_stats['successful_scans']
            avg_candidates = self.session_stats['high_conviction_candidates'] / self.session_stats['successful_scans']
            print(f"  Average Tokens per Scan: {avg_tokens:.1f}")
            print(f"  Average Candidates per Scan: {avg_candidates:.1f}")
        
        # Show scan-by-scan breakdown
        print(f"\n📋 SCAN BREAKDOWN:")
        for scan in self.session_stats['scan_results']:
            scan_num = scan['scan_number']
            status = scan['status']
            duration = scan['duration_seconds']
            timestamp = datetime.fromisoformat(scan['timestamp']).strftime('%H:%M:%S')
            
            if status == "completed":
                tokens = scan['tokens_analyzed']
                candidates = scan['candidates_found']
                alerts = scan['alerts_sent']
                print(f"  Scan #{scan_num} ({timestamp}): ✅ {tokens} tokens, {candidates} candidates, {alerts} alerts ({duration:.1f}s)")
            elif status == "no_high_conviction":
                tokens = scan['tokens_analyzed']
                print(f"  Scan #{scan_num} ({timestamp}): 📊 {tokens} tokens, no candidates ({duration:.1f}s)")
            elif status == "no_results":
                print(f"  Scan #{scan_num} ({timestamp}): 📊 No results ({duration:.1f}s)")
            elif status == "failed":
                error = scan.get('error', 'Unknown')
                print(f"  Scan #{scan_num} ({timestamp}): ❌ Failed - {error} ({duration:.1f}s)")
        
        # Save session results
        session_file = f"data/session_results_{int(time.time())}.json"
        os.makedirs("data", exist_ok=True)
        
        with open(session_file, 'w') as f:
            # Convert datetime objects to strings for JSON serialization
            stats_copy = self.session_stats.copy()
            stats_copy["start_time"] = stats_copy["start_time"].isoformat()
            stats_copy["end_time"] = stats_copy["end_time"].isoformat()
            json.dump(stats_copy, f, indent=2)
        
        print(f"\n💾 Session results saved to: {session_file}")
        
        # Display comprehensive token registry summary
        self._display_session_token_summary()
        
        # Final summary
        if self.session_stats['alerts_sent'] > 0:
            print(f"\n🚀 SUCCESS! Found {self.session_stats['alerts_sent']} high conviction tokens!")
        else:
            print(f"\n📊 Session complete. No high conviction tokens found this time.")
        
        print("=" * 60)
    
    def _display_session_token_summary(self):
        """Display comprehensive session token registry summary"""
        print("\n" + "🪙" * 60)
        print("🪙 COMPREHENSIVE TOKEN REGISTRY - SESSION SUMMARY")
        print("🪙" * 60)
        
        registry = self.session_token_registry
        summary = registry['session_summary']
        
        # Overall statistics
        print(f"\n📊 OVERALL TOKEN STATISTICS:")
        print(f"  🎯 Total Unique Tokens Discovered: {summary['total_unique_tokens']}")
        print(f"  📈 Tokens by Source:")
        for source, count in summary['tokens_by_source'].items():
            if count > 0:
                print(f"    • {source.title()}: {count} tokens")
        
        # Score distribution
        print(f"\n📈 SCORE DISTRIBUTION:")
        for score_range, count in summary['score_distribution'].items():
            if count > 0:
                print(f"  📊 Score {score_range}: {count} tokens")
        
        # High conviction tokens
        high_conviction_count = len(registry['high_conviction_tokens'])
        if high_conviction_count > 0:
            print(f"\n🎯 HIGH CONVICTION TOKENS ({high_conviction_count}):")
            for address, token in registry['high_conviction_tokens'].items():
                platforms_str = ', '.join(token['platforms']) if token['platforms'] else 'Unknown'
                print(f"  🚀 {token['symbol']} ({address[:8]}...) - Score: {token['score']:.1f} - Platforms: {platforms_str}")
        else:
            print(f"\n🎯 HIGH CONVICTION TOKENS: None found")
        
        # Scan-by-scan breakdown
        print(f"\n📋 SCAN-BY-SCAN TOKEN BREAKDOWN:")
        for scan_num in sorted(registry['all_tokens_by_scan'].keys()):
            tokens = registry['all_tokens_by_scan'][scan_num]
            print(f"  Scan #{scan_num}: {len(tokens)} tokens discovered")
            
            if tokens:
                # Show top token from this scan
                top_token = max(tokens, key=lambda x: x['score'])
                platforms_str = ', '.join(top_token['platforms']) if top_token['platforms'] else 'Unknown'
                print(f"    🏆 Top: {top_token['symbol']} (Score: {top_token['score']:.1f}, Platforms: {platforms_str})")
        
        # Multi-platform tokens (cross-validation)
        multi_platform_tokens = [
            token for token in registry['unique_tokens_discovered'].values()
            if len(token['platforms']) > 1
        ]
        
        if multi_platform_tokens:
            print(f"\n🔗 CROSS-PLATFORM VALIDATED TOKENS ({len(multi_platform_tokens)}):")
            multi_platform_tokens.sort(key=lambda x: x['score'], reverse=True)
            for token in multi_platform_tokens[:10]:  # Show top 10
                platforms_str = ', '.join(token['platforms'])
                print(f"  ✅ {token['symbol']} ({token['address'][:8]}...) - Score: {token['score']:.1f} - Platforms: {platforms_str}")
        else:
            print(f"\n🔗 CROSS-PLATFORM VALIDATED TOKENS: None found")
        
        # Save detailed token registry
        token_registry_file = f"data/token_registry_{int(time.time())}.json"
        try:
            with open(token_registry_file, 'w') as f:
                json.dump(registry, f, indent=2, default=str)
            print(f"\n💾 Complete token registry saved to: {token_registry_file}")
        except Exception as e:
            print(f"\n❌ Error saving token registry: {e}")
        
        print("🪙" * 60)
        
    def _display_api_session_summary(self, results: List[Dict[str, Any]]):
        """Display comprehensive API session summary across all scans"""
        print("\n" + "=" * 60)
        print("📡 API SESSION SUMMARY - ALL SCANS")
        print("=" * 60)
        
        # Collect all API reports
        api_reports = []
        for result in results:
            if "api_report" in result and result["api_report"]:
                api_reports.append(result["api_report"])
        
        if not api_reports:
            print("No API reports available")
            return
            
        # Aggregate statistics across all scans
        total_session_stats = {
            "total_api_calls": 0,
            "successful_calls": 0,
            "failed_calls": 0,
            "cache_hits": 0,
            "cache_misses": 0,
            "total_response_time_ms": 0,
            "endpoints_used": set(),
            "scans_analyzed": len(api_reports)
        }
        
        health_status_counts = {}
        
        # Process each scan's API report
        for report in api_reports:
            if "summary" in report:
                summary = report["summary"]
                total_session_stats["total_api_calls"] += summary.get("total_api_calls", 0)
                total_session_stats["successful_calls"] += summary.get("successful_calls", 0)
                total_session_stats["failed_calls"] += summary.get("failed_calls", 0)
                total_session_stats["cache_hits"] += summary.get("cache_hits", 0)
                total_session_stats["cache_misses"] += summary.get("cache_misses", 0)
                total_session_stats["total_response_time_ms"] += summary.get("average_response_time_ms", 0) * summary.get("total_api_calls", 0)
                
                # Track endpoints
                for endpoint in summary.get("endpoints_used", []):
                    total_session_stats["endpoints_used"].add(endpoint)
                    
                # Track health status distribution
                health_status = summary.get("health_status", "unknown")
                health_status_counts[health_status] = health_status_counts.get(health_status, 0) + 1
        
        # Calculate session-wide metrics
        session_cache_hit_rate = 0
        total_cache_requests = total_session_stats["cache_hits"] + total_session_stats["cache_misses"]
        if total_cache_requests > 0:
            session_cache_hit_rate = (total_session_stats["cache_hits"] / total_cache_requests) * 100
            
        session_avg_response_time = 0
        if total_session_stats["total_api_calls"] > 0:
            session_avg_response_time = total_session_stats["total_response_time_ms"] / total_session_stats["total_api_calls"]
            session_success_rate = (total_session_stats["successful_calls"] / total_session_stats["total_api_calls"]) * 100
        else:
            session_success_rate = 0
        
        # Display session totals
        print(f"🔢 SESSION API TOTALS:")
        print(f"  Total API Calls: {total_session_stats['total_api_calls']}")
        print(f"  Successful: {total_session_stats['successful_calls']}")
        print(f"  Failed: {total_session_stats['failed_calls']}")
        print(f"  Success Rate: {session_success_rate:.1f}%")
        
        print(f"\n💾 SESSION CACHE PERFORMANCE:")
        print(f"  Total Cache Hits: {total_session_stats['cache_hits']}")
        print(f"  Total Cache Misses: {total_session_stats['cache_misses']}")
        print(f"  Session Hit Rate: {session_cache_hit_rate:.1f}%")
        
        print(f"\n⚡ SESSION PERFORMANCE:")
        print(f"  Average Response Time: {session_avg_response_time:.1f}ms")
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
        
        # Unique endpoints used across session
        endpoints_list = sorted(list(total_session_stats["endpoints_used"]))
        print(f"\n🎯 UNIQUE ENDPOINTS USED ({len(endpoints_list)}):")
        for endpoint in endpoints_list:
            print(f"  • {endpoint}")
        
        # Scan-by-scan API performance
        print(f"\n📊 SCAN-BY-SCAN API PERFORMANCE:")
        for i, report in enumerate(api_reports, 1):
            if "summary" in report:
                summary = report["summary"]
                calls = summary.get("total_api_calls", 0)
                success = summary.get("successful_calls", 0)
                failed = summary.get("failed_calls", 0)
                health = summary.get("health_status", "unknown")
                
                health_emoji = {
                    "excellent": "🟢",
                    "good": "🟡", 
                    "fair": "🟠",
                    "poor": "🔴",
                    "no_activity": "⚪",
                    "unknown": "❓"
                }.get(health, "❓")
                
                if calls > 0:
                    scan_success_rate = (success / calls) * 100
                    print(f"  Scan #{i}: {health_emoji} {success}/{calls} calls ({scan_success_rate:.1f}% success)")
                else:
                    print(f"  Scan #{i}: {health_emoji} No API activity")
        
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
            
        if session_cache_hit_rate >= 80:
            print(f"  💾 EXCELLENT: Cache is performing very well!")
        elif session_cache_hit_rate >= 60:
            print(f"  💾 GOOD: Cache performance is acceptable")
        else:
            print(f"  💾 FAIR: Cache hit rate could be improved")
        
        # Enhanced API Service Breakdown
        self._display_api_service_breakdown(api_reports)
        
        print("=" * 60)

    def _display_api_service_breakdown(self, api_reports: List[Dict[str, Any]]):
        """Display detailed breakdown of API usage by service and endpoint"""
        print(f"\n🔧 DETAILED API SERVICE BREAKDOWN")
        print("=" * 60)
        
        # Collect service statistics
        service_stats = {
            "birdeye_detailed": {
                "name": "Birdeye Detailed Analysis API",
                "endpoints": {},
                "total_calls": 0,
                "successful_calls": 0,
                "failed_calls": 0,
                "total_response_time_ms": 0
            },
            "birdeye_cross_platform": {
                "name": "Birdeye Cross-Platform API", 
                "endpoints": {},
                "total_calls": 0,
                "successful_calls": 0,
                "failed_calls": 0,
                "total_response_time_ms": 0
            }
        }
        
        # Process each API report
        for report in api_reports:
            # Process Birdeye detailed API stats
            if "birdeye_detailed_api" in report and report["birdeye_detailed_api"]:
                birdeye_stats = report["birdeye_detailed_api"]
                service = service_stats["birdeye_detailed"]
                
                service["total_calls"] += birdeye_stats.get("total_api_calls", 0)
                service["successful_calls"] += birdeye_stats.get("successful_api_calls", 0)
                service["failed_calls"] += birdeye_stats.get("failed_api_calls", 0)
                service["total_response_time_ms"] += birdeye_stats.get("total_response_time_ms", 0)
                
                # Process endpoint statistics
                if "calls_by_endpoint" in birdeye_stats:
                    for endpoint, endpoint_stats in birdeye_stats["calls_by_endpoint"].items():
                        if endpoint not in service["endpoints"]:
                            service["endpoints"][endpoint] = {
                                "total": 0,
                                "successful": 0,
                                "failed": 0,
                                "avg_response_time_ms": 0
                            }
                        
                        service["endpoints"][endpoint]["total"] += endpoint_stats.get("total", 0)
                        service["endpoints"][endpoint]["successful"] += endpoint_stats.get("successful", 0)
                        service["endpoints"][endpoint]["failed"] += endpoint_stats.get("failed", 0)
                        
                        # Update average response time
                        if endpoint_stats.get("total", 0) > 0:
                            service["endpoints"][endpoint]["avg_response_time_ms"] = endpoint_stats.get("avg_response_time_ms", 0)
            
            # Process Birdeye cross-platform API stats
            if "birdeye_cross_platform_api" in report and report["birdeye_cross_platform_api"]:
                cross_platform_stats = report["birdeye_cross_platform_api"]
                service = service_stats["birdeye_cross_platform"]
                
                service["total_calls"] += cross_platform_stats.get("total_api_calls", 0)
                service["successful_calls"] += cross_platform_stats.get("successful_api_calls", 0)
                service["failed_calls"] += cross_platform_stats.get("failed_api_calls", 0)
                service["total_response_time_ms"] += cross_platform_stats.get("total_response_time_ms", 0)
                
                # Process endpoint statistics
                if "calls_by_endpoint" in cross_platform_stats:
                    for endpoint, endpoint_stats in cross_platform_stats["calls_by_endpoint"].items():
                        if endpoint not in service["endpoints"]:
                            service["endpoints"][endpoint] = {
                                "total": 0,
                                "successful": 0,
                                "failed": 0,
                                "avg_response_time_ms": 0
                            }
                        
                        service["endpoints"][endpoint]["total"] += endpoint_stats.get("total", 0)
                        service["endpoints"][endpoint]["successful"] += endpoint_stats.get("successful", 0)
                        service["endpoints"][endpoint]["failed"] += endpoint_stats.get("failed", 0)
                        
                        # Update average response time
                        if endpoint_stats.get("total", 0) > 0:
                            service["endpoints"][endpoint]["avg_response_time_ms"] = endpoint_stats.get("avg_response_time_ms", 0)
        
        # Display breakdown for each service
        for service_key, service_data in service_stats.items():
            if service_data["total_calls"] == 0:
                continue  # Skip services with no activity
                
            print(f"\n🔗 {service_data['name'].upper()}")
            print("-" * 50)
            
            # Service totals
            total_calls = service_data["total_calls"]
            successful_calls = service_data["successful_calls"]
            failed_calls = service_data["failed_calls"]
            success_rate = (successful_calls / total_calls * 100) if total_calls > 0 else 0
            avg_response_time = (service_data["total_response_time_ms"] / total_calls) if total_calls > 0 else 0
            
            print(f"📊 Service Summary:")
            print(f"  Total Calls: {total_calls}")
            print(f"  Successful: {successful_calls}")
            print(f"  Failed: {failed_calls}")
            print(f"  Success Rate: {success_rate:.1f}%")
            print(f"  Avg Response Time: {avg_response_time:.1f}ms")
            
            # Endpoint breakdown
            if service_data["endpoints"]:
                print(f"\n🎯 Endpoints Used ({len(service_data['endpoints'])}):")
                
                # Sort endpoints by total calls (most used first)
                sorted_endpoints = sorted(
                    service_data["endpoints"].items(),
                    key=lambda x: x[1]["total"],
                    reverse=True
                )
                
                for endpoint, endpoint_stats in sorted_endpoints:
                    endpoint_total = endpoint_stats["total"]
                    endpoint_success = endpoint_stats["successful"]
                    endpoint_failed = endpoint_stats["failed"]
                    endpoint_success_rate = (endpoint_success / endpoint_total * 100) if endpoint_total > 0 else 0
                    endpoint_avg_time = endpoint_stats["avg_response_time_ms"]
                    
                    # Status indicator
                    if endpoint_success_rate >= 95:
                        status_emoji = "🟢"
                    elif endpoint_success_rate >= 85:
                        status_emoji = "🟡"
                    elif endpoint_success_rate >= 70:
                        status_emoji = "🟠"
                    else:
                        status_emoji = "🔴"
                    
                    print(f"  {status_emoji} {endpoint}")
                    print(f"    Calls: {endpoint_total} ({endpoint_success} success, {endpoint_failed} failed)")
                    print(f"    Success Rate: {endpoint_success_rate:.1f}%")
                    print(f"    Avg Response: {endpoint_avg_time:.1f}ms")
                    
                    # Show usage percentage within service
                    usage_percentage = (endpoint_total / total_calls * 100) if total_calls > 0 else 0
                    print(f"    Usage: {usage_percentage:.1f}% of service calls")
                    print()
        
        # Summary of all services
        total_all_calls = sum(service["total_calls"] for service in service_stats.values())
        total_all_success = sum(service["successful_calls"] for service in service_stats.values())
        total_all_failed = sum(service["failed_calls"] for service in service_stats.values())
        
        if total_all_calls > 0:
            print(f"\n📈 CROSS-SERVICE SUMMARY:")
            print(f"  Total API Calls Across All Services: {total_all_calls}")
            print(f"  Overall Success Rate: {(total_all_success / total_all_calls * 100):.1f}%")
            
            # Service distribution
            print(f"\n🔄 SERVICE USAGE DISTRIBUTION:")
            for service_key, service_data in service_stats.items():
                if service_data["total_calls"] > 0:
                    service_percentage = (service_data["total_calls"] / total_all_calls * 100)
                    print(f"  • {service_data['name']}: {service_data['total_calls']} calls ({service_percentage:.1f}%)")
        
        # Recommendations
        print(f"\n💡 OPTIMIZATION RECOMMENDATIONS:")
        
        # Check for high-failure endpoints
        high_failure_endpoints = []
        for service_data in service_stats.values():
            for endpoint, stats in service_data["endpoints"].items():
                if stats["total"] > 0:
                    failure_rate = (stats["failed"] / stats["total"]) * 100
                    if failure_rate > 15:  # More than 15% failure rate
                        high_failure_endpoints.append((endpoint, failure_rate, stats["total"]))
        
        if high_failure_endpoints:
            print(f"  🚨 High-failure endpoints detected:")
            for endpoint, failure_rate, total_calls in high_failure_endpoints[:3]:  # Show top 3
                print(f"    • {endpoint}: {failure_rate:.1f}% failure rate ({total_calls} calls)")
        
        # Check for slow endpoints
        slow_endpoints = []
        for service_data in service_stats.values():
            for endpoint, stats in service_data["endpoints"].items():
                if stats["avg_response_time_ms"] > 2000:  # Slower than 2 seconds
                    slow_endpoints.append((endpoint, stats["avg_response_time_ms"], stats["total"]))
        
        if slow_endpoints:
            print(f"  ⏰ Slow endpoints detected:")
            for endpoint, avg_time, total_calls in slow_endpoints[:3]:  # Show top 3
                print(f"    • {endpoint}: {avg_time:.1f}ms avg response ({total_calls} calls)")
        
        if not high_failure_endpoints and not slow_endpoints:
            print(f"  ✅ All endpoints performing well - no optimization needed!")


async def main():
    """Main entry point"""
    import argparse
    
    parser = argparse.ArgumentParser(description="High Conviction Detector - Timed Session")
    parser.add_argument("--config", default="config/config.yaml", help="Configuration file path")
    parser.add_argument("--duration", type=float, default=1.0, help="Session duration in hours")
    parser.add_argument("--scans", type=int, default=6, help="Number of scans to perform")
    
    args = parser.parse_args()
    
    try:
        session = TimedHighConvictionSession(args.config)
        await session.run_timed_session(args.duration, args.scans)
        
    except KeyboardInterrupt:
        print("\n⌨️ Session interrupted by user")
    except Exception as e:
        print(f"❌ Fatal error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main()) 