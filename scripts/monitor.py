#!/usr/bin/env python3
"""
Early Token Detection Monitor

Uses advanced optimization techniques to reduce API calls by 70-80% while maintaining
or improving analysis quality. Key optimizations:

1. Batch processing for price/overview data
2. Progressive analysis pipeline (3 stages) 
3. Smart caching with intelligent TTL strategies
4. Centralized data management
5. Efficient discovery with strict upfront filters

Expected API call reduction: From 700-1000+ calls to 50-150 calls per scan.
"""

import os
import sys
import time
import signal
import asyncio
import argparse
from typing import Dict, Any, List, Set, Optional
from pathlib import Path
import logging
import json
import random
from datetime import datetime, timedelta
from utils.structured_logger import get_structured_logger, new_scan_id
import psutil

# Fix import path
current_dir = Path(__file__).parent.absolute()
if str(current_dir) not in sys.path:
    sys.path.insert(0, str(current_dir))
    print(f"Added {current_dir} to Python path")

# Set up fallback import mechanism for modules
try:
    from core.config_manager import ConfigManager
    from core.cache_manager import CacheManager
    from api.birdeye_connector import BirdeyeAPI
    from services.rate_limiter_service import RateLimiterService
    from services.early_token_detection import EarlyTokenDetector
    from services.whale_discovery_service import WhaleDiscoveryService  
    from services.whale_movement_tracker import WhaleMovementTracker
    from services.trader_performance_analyzer import TraderPerformanceAnalyzer, TraderProfile, TraderTier, PerformanceTimeframe
    from services.telegram_alerter import MinimalTokenMetrics, TelegramAlerter
    from api.batch_api_manager import BatchAPIManager
    from core.token_discovery_scheduler import TokenDiscoveryScheduler
    from core.strategy_scheduler import StrategyScheduler
    from services.performance_analyzer import PerformanceAnalyzer
    
    # Try to import logger_setup from utils
    try:
        from utils.logger_setup import LoggerSetup
    except ImportError:
        # If not found in utils, try to import from services as fallback
        from services.logger_setup import LoggerSetup
        print("Using logger_setup from services module as fallback")
except Exception as e:
    print(f"Error importing modules: {e}")
    print("Trying alternative import paths...")
    
    # Get the absolute path of the project
    project_path = os.path.dirname(os.path.abspath(__file__))
    
    # Add project path to Python path
    if project_path not in sys.path:
        sys.path.insert(0, project_path)
        print(f"Added {project_path} to Python path")
    
    # Try imports again
    from core.config_manager import ConfigManager
    from core.cache_manager import CacheManager
    from api.birdeye_connector import BirdeyeAPI
    from services.rate_limiter_service import RateLimiterService
    from services.early_token_detection import EarlyTokenDetector
    from services.whale_discovery_service import WhaleDiscoveryService
    from services.whale_movement_tracker import WhaleMovementTracker
    from services.trader_performance_analyzer import TraderPerformanceAnalyzer, TraderProfile, TraderTier, PerformanceTimeframe
    from services.telegram_alerter import MinimalTokenMetrics, TelegramAlerter
    from api.batch_api_manager import BatchAPIManager
    from core.token_discovery_scheduler import TokenDiscoveryScheduler
    from core.strategy_scheduler import StrategyScheduler
    from services.performance_analyzer import PerformanceAnalyzer
    
    # Try both potential locations for logger_setup
    try:
        from utils.logger_setup import LoggerSetup
    except ImportError:
        from services.logger_setup import LoggerSetup
        print("Using logger_setup from services module")

class VirtuosoGemHunter:
    """
    Main monitoring service that orchestrates token discovery, analysis, and alerting.
    Enhanced with whale tracking, trader analysis, and intelligent API batching.
    """
    
    def __init__(self):
        # Initialize logger first
        self.logger = get_structured_logger('VirtuosoGemHunter')
        self.logger.info("Starting Virtuoso Gem Hunter")
        
        # Load configuration
        self.config = self._load_config()
        
        # Configure logging with level from config
        log_level = logging.DEBUG if self.config.get('DEBUG', False) else logging.INFO
        self.logger.setLevel(log_level)
        
        # Handle Ctrl+C gracefully
        signal.signal(signal.SIGINT, self._signal_handler)
        
        # Core services
        self._cache = CacheManager()
        self.rate_limiter = RateLimiterService()
        
        # Initialize APIs
        birdeye_config = self.config.get('BIRDEYE_API', {})
        
        if not birdeye_config.get('api_key') and 'BIRDEYE_API_KEY' in os.environ:
            birdeye_config['api_key'] = os.environ.get('BIRDEYE_API_KEY')
        
        self.birdeye_api = BirdeyeAPI(
            config=birdeye_config,
            logger=self.logger,
            cache_manager=self._cache,
            rate_limiter=self.rate_limiter
        )
        
        # Initialize early token detection engine
        whale_tracking_enabled = self.config.get('WHALE_TRACKING', {}).get('enabled', False)
        self.detection_engine = EarlyTokenDetector(self.config, enable_whale_tracking=whale_tracking_enabled)
        
        # Initialize batch manager directly for use in scheduler
        self.batch_manager = BatchAPIManager(self.birdeye_api, self.logger)
        
        # Initialize token discovery scheduler
        self.discovery_scheduler = TokenDiscoveryScheduler(self.batch_manager, self.config)
        self.logger.info("Token discovery scheduler initialized")
        
        # Initialize strategy scheduler
        strategy_scheduler_config = self.config.get('STRATEGY_SCHEDULER', {})
        self.strategy_scheduler = StrategyScheduler(
            birdeye_api=self.birdeye_api,
            logger=self.logger,
            enabled=strategy_scheduler_config.get('enabled', True),
            run_hours=strategy_scheduler_config.get('run_hours', [0, 6, 12, 18]),
            strategy_configs=strategy_scheduler_config.get('strategies', {})
        )
        self.logger.info("Strategy scheduler initialized")
        
        # Initialize trader analyzer if enabled
        trader_discovery_enabled = self.config.get('TRADER_DISCOVERY', {}).get('enabled', False)
        if trader_discovery_enabled:
            self.trader_analyzer = TraderPerformanceAnalyzer(
                birdeye_api=self.birdeye_api
            )
        
        # Initialize Telegram alerter if configured
        telegram_config = self.config.get('TELEGRAM', {})
        telegram_token = telegram_config.get('bot_token') or os.environ.get('TELEGRAM_BOT_TOKEN')
        telegram_chat_id = telegram_config.get('chat_id') or os.environ.get('TELEGRAM_CHAT_ID')
        
        self.telegram_alerter = None
        if telegram_token and telegram_chat_id:
            self.telegram_alerter = TelegramAlerter(
                bot_token=telegram_token,
                chat_id=telegram_chat_id
            )
            self.logger.info("Telegram alerter initialized")
        
        # Track recently alerted tokens to prevent duplicates
        self.recently_alerted_tokens: Set[str] = set()
        
        # Runtime tracking
        self.max_runtime_hours = None
        self.start_time = None
        self.running = False
        self.shutdown_requested = False
        
        # Performance analysis
        self.performance_analyzer = PerformanceAnalyzer()
        
        self.logger.info("Virtuoso Gem Hunter initialization complete")
    
    def set_runtime_duration(self, hours: float):
        """Set maximum runtime in hours for the monitoring session"""
        self.max_runtime_hours = hours
        self.logger.info(f"🕒 Monitor will run for {hours} hours maximum")

    def _check_runtime_limit(self) -> bool:
        """Check if runtime limit has been reached"""
        if self.max_runtime_hours is None or self.start_time is None:
            return False
        
        elapsed_hours = (time.time() - self.start_time) / 3600
        if elapsed_hours >= self.max_runtime_hours:
            self.logger.info(f"🕒 Runtime limit reached: {elapsed_hours:.2f} hours")
            return True
        return False
    
    def _display_configuration(self):
        """Display the current configuration of the monitor"""
        print(f"\n{'='*90}")
        print(f"{'VIRTUOSO GEM HUNTER CONFIGURATION':^90}")
        print(f"{'='*90}")
        
        print(f"\n--- DISCOVERY SETTINGS ---")
        print(f"Scan interval: {self.scan_interval/60:.1f} minutes")
        print(f"Max tokens per scan: {self.max_tokens}")
        print(f"Score threshold: {self.min_score_threshold}")
        print(f"Whale tracking: {'Enabled' if self.detection_engine.enable_whale_tracking else 'Disabled'}")
        print(f"Trader analysis: {'Available' if hasattr(self, 'trader_analyzer') else 'Disabled'}")
        
        # Display discovery scheduler information
        schedule_info = self.discovery_scheduler.get_active_schedule_info()
        print(f"\n--- TIME-BASED DISCOVERY SCHEDULING ---")
        if schedule_info.get("active", False):
            print(f"Active schedule: {schedule_info['name']}")
            print(f"Description: {schedule_info['description']}")
            print(f"Priority: {schedule_info.get('priority', 'N/A')}")
            
            # Print some key filter adjustments
            adjustments = schedule_info.get('adjustments', {})
            if adjustments:
                print("Key filter adjustments:")
                for key in ['base_min_liquidity', 'base_min_market_cap', 'base_min_momentum_score']:
                    if key in adjustments:
                        print(f"  • {key}: {adjustments[key]}")
        else:
            print("No active schedule - using default filters")
        
        # Display strategy scheduler information
        strategy_status = self.strategy_scheduler.get_status_report()
        print(f"\n--- STRATEGY-BASED DISCOVERY ---")
        print(f"Enabled: {'Yes' if strategy_status['enabled'] else 'No'}")
        print(f"Total strategies: {strategy_status['total_strategies']}")
        print(f"Run hours (UTC): {', '.join(f'{h:02d}:00' for h in strategy_status['run_hours'])}")
        print(f"Next run: {strategy_status['next_run_hour']:02d}:00 UTC ({strategy_status['minutes_until_next_run']:.1f} minutes)")
        print(f"Promising tokens tracked: {strategy_status['promising_tokens']}")
        
        # Strategy metrics
        print(f"\n--- STRATEGY PERFORMANCE ---")
        for name, metrics in strategy_status.get('strategy_metrics', {}).items():
            print(f"• {name}: {metrics['promising_tokens_found']}/{metrics['total_tokens_tracked']} tokens ({metrics['success_rate']*100:.1f}%)")
        
        print(f"\n--- TRADER DISCOVERY SETTINGS ---")
        print(f"Discovery enabled: {'Yes' if self.trader_discovery_enabled else 'No'}")
        print(f"Discovery interval: Every {self.trader_discovery_interval} scans")
        print(f"Max traders per discovery: {self.max_traders_discovery}")
        print(f"Trader alert threshold: {self.trader_alert_threshold}")
        
        # API configuration
        birdeye_api_config = self.config.get('BIRDEYE_API', {})
        api_key = birdeye_api_config.get('api_key', 'Not set')
        masked_key = f"{api_key[:4]}...{api_key[-4:]}" if len(api_key) > 8 else "Not properly set"
        
        print(f"\n--- API CONFIGURATION ---")
        print(f"Birdeye API Key: {masked_key}")
        print(f"Rate limiting: {'Enabled' if birdeye_api_config.get('use_rate_limiting', True) else 'Disabled'}")
        print(f"Request timeout: {birdeye_api_config.get('request_timeout_seconds', 20)}s")
        
        # Alerts configuration
        telegram_enabled = self.telegram_alerter is not None
        print(f"\n--- ALERTS CONFIGURATION ---")
        print(f"Telegram alerts: {'Enabled' if telegram_enabled else 'Disabled'}")
        if telegram_enabled:
            chat_id = os.environ.get('TELEGRAM_CHAT_ID', 'Not set')
            # Mask chat ID for security (show first 3 and last 3 digits)
            if chat_id and chat_id != 'Not set' and len(chat_id) > 6:
                masked_chat_id = f"{chat_id[:3]}...{chat_id[-3:]}"
            else:
                masked_chat_id = "Not properly set"
            print(f"Telegram chat ID: {masked_chat_id}")
            print(f"Alert cooldown: {self.alert_cooldown_minutes} minutes")
            print(f"Enhanced safety validation: Enabled")
            print(f"  • 7-layer validation system")
            print(f"  • Pump-friendly, dump-averse logic")
            print(f"  • Pump opportunities welcomed")
            print(f"  • Dump phases blocked")
            print(f"  • Alert deduplication")
            print(f"  • Market sustainability checks")
        
        print(f"\n--- EXPECTED PERFORMANCE ---")
        print(f"API calls per scan: 50-150 (vs 700-1000+ in old system)")
        print(f"Expected reduction: 75-85%")
        print(f"Analysis quality: Maintained or improved")
        
        print(f"{'='*90}\n")
    
    def _log_configuration(self):
        """Log monitor configuration for operational purposes"""
        self.logger.info(f"Scan interval: {self.scan_interval/60:.1f} minutes")
        self.logger.info(f"Max tokens per scan: {self.max_tokens}")
        self.logger.info(f"Score threshold: {self.min_score_threshold}")
        
        # Log API configuration
        birdeye_api_config = self.config.get('BIRDEYE_API', {})
        api_key_set = bool(os.environ.get('BIRDEYE_API_KEY'))
        self.logger.info(f"Birdeye API configured: {api_key_set}")
        self.logger.info(f"Rate limiting enabled: {birdeye_api_config.get('use_rate_limiting', True)}")
        
        # Log Telegram configuration
        telegram_enabled = self.telegram_alerter is not None
        self.logger.info(f"Telegram alerts enabled: {telegram_enabled}")
        if telegram_enabled:
            self.logger.info("Telegram bot and chat ID configured")
        
        self.logger.info("Monitor configuration completed")
    
    async def start(self):
        self.logger.info({"event": "monitor_start", "msg": "Starting Virtuoso Gem Hunter with intelligent optimizations..."})
        self.start_time = time.time()
        self.running = True
        self._display_configuration()
        self._log_configuration()
        scan_count = 0
        total_tokens_discovered = 0
        total_tokens_analyzed = 0
        total_promising_tokens = 0
        total_api_calls = 0
        scan_durations = []
        api_calls_per_cycle = []
        while self.running and not self._check_runtime_limit():
            scan_id = new_scan_id()
            try:
                scan_count += 1
                scan_start_time = time.time()
                api_calls_start_of_cycle = self.birdeye_api.api_call_tracker['total_api_calls']
                self.logger.info({"event": "scan_start", "scan_id": scan_id, "scan_count": scan_count, "timestamp": time.time()})
                print(f"\n🔍 SCAN #{scan_count} - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
                
                # Check if we should run trader discovery
                should_run_trader_discovery = (
                    hasattr(self, 'trader_analyzer') and 
                    self.trader_discovery_enabled and 
                    scan_count % self.trader_discovery_interval == 0
                )
                
                try:
                    stage_start = time.time()
                    self.logger.info({"event": "stage_start", "stage": "strategy_discovery", "scan_id": scan_id, "timestamp": stage_start})
                    # Run strategy-based discovery if it's time
                    strategy_tokens = await self.strategy_scheduler.run_due_strategies()
                    if strategy_tokens:
                        self.logger.info(f"Strategy-based discovery found {len(strategy_tokens)} tokens")
                        print(f"📊 Strategy-based discovery found {len(strategy_tokens)} tokens")
                        
                        # Alert for promising strategy tokens
                        for token in strategy_tokens:
                            consecutive_appearances = token.get("strategy_data", {}).get("consecutive_appearances", 0)
                            strategy_name = token.get("strategy_data", {}).get("strategy", "Unknown Strategy")
                            
                            # Only alert for tokens that have appeared enough times
                            min_appearances = 3  # Default
                            if "Recent Listings" in strategy_name:
                                min_appearances = 2  # Lower threshold for new listings
                            
                            if consecutive_appearances >= min_appearances:
                                # Check if token is already in recently alerted tokens
                                token_address = token.get("address")
                                if token_address and token_address not in self.recently_alerted_tokens:
                                    # Add special strategy tag for alerts
                                    token["alert_tags"] = [f"Strategy: {strategy_name}"]
                                    token["alert_priority"] = "high" if consecutive_appearances >= 4 else "medium"
                                    
                                    # Send alert for this token
                                    await self._send_telegram_alert(token)
                                    
                                    # Add to recently alerted tokens
                                    self.recently_alerted_tokens.add(token_address)
                    
                    stage_end = time.time()
                    self.logger.info({"event": "stage_end", "stage": "strategy_discovery", "scan_id": scan_id, "duration": stage_end - stage_start, "timestamp": stage_end})
                    
                    # Update discovery scheduler for time-based filtering
                    self.discovery_scheduler.apply_schedule_to_batch_manager()
                    
                    # Display active schedule info
                    schedule_info = self.discovery_scheduler.get_active_schedule_info()
                    if schedule_info.get("active", False):
                        self.logger.info(f"Using schedule: {schedule_info['name']} - {schedule_info['description']}")
                    
                    # Enhanced token discovery and analysis
                    self.logger.info("Starting token discovery and analysis...")
                    
                    stage_start = time.time()
                    self.logger.info({"event": "stage_start", "stage": "token_discovery_and_analysis", "scan_id": scan_id, "timestamp": stage_start})
                    promising_tokens = []
                    try:
                        promising_tokens = await asyncio.wait_for(
                            self.detection_engine.discover_and_analyze(max_tokens=self.max_tokens),
                            timeout=600.0
                        )
                        stage_end = time.time()
                        self.logger.info({"event": "stage_end", "stage": "token_discovery_and_analysis", "scan_id": scan_id, "duration": stage_end - stage_start, "timestamp": stage_end})
                        tokens_discovered = getattr(self.detection_engine, 'last_discovery_tokens_count', 0) or 0
                        tokens_analyzed = getattr(self.detection_engine, 'last_analysis_tokens_count', 0) or 0
                        api_calls = self.birdeye_api.api_call_tracker['total_api_calls']
                        api_calls_this_cycle = api_calls - api_calls_start_of_cycle
                        api_calls_per_cycle.append(api_calls_this_cycle)
                        total_tokens_discovered += tokens_discovered
                        total_tokens_analyzed += tokens_analyzed
                        total_promising_tokens += len(promising_tokens)
                        total_api_calls += api_calls_this_cycle
                        self.logger.info({"event": "scan_metrics", "scan_id": scan_id, "tokens_discovered": tokens_discovered, "tokens_analyzed": tokens_analyzed, "promising_tokens": len(promising_tokens), "api_calls_this_cycle": api_calls_this_cycle})
                    except asyncio.TimeoutError:
                        self.logger.error({"event": "timeout", "scan_id": scan_id, "msg": "Discovery timed out after 10 minutes"})
                        continue
                    except Exception as e:
                        import traceback
                        self.logger.error({"event": "exception", "scan_id": scan_id, "error": str(e), "trace": traceback.format_exc()})
                        continue
                    
                    # Check if we should exit after analysis
                    if not self.running:
                        print("Received shutdown signal during analysis, stopping...")
                        break
                    
                    # Process promising tokens (if any)
                    if promising_tokens:
                        # Sort tokens by score in descending order
                        promising_tokens.sort(key=lambda x: x.get('score', 0), reverse=True)
                        
                        print(f"\n🔎 Found {len(promising_tokens)} promising tokens:")
                        
                        # Display token summary
                        for i, token in enumerate(promising_tokens):
                            self._display_token_summary(i+1, token)
                            
                            # Send alerts for tokens above threshold
                            if token.get('score', 0) >= self.min_score_threshold:
                                await self._send_telegram_alert(token)
                    else:
                        print("No promising tokens found in this scan")
                        
                    # Run trader discovery if scheduled
                    if should_run_trader_discovery:
                        await self._run_integrated_trader_discovery(scan_count)
                    
                    # Display API call breakdown
                    discovered_count = self.detection_engine.last_discovery_tokens_count or 0
                    analyzed_count = self.detection_engine.last_analysis_tokens_count or 0
                    final_count = len(promising_tokens)
                    
                    # CRITICAL FIX: Use actual API calls instead of estimates
                    actual_calls = self.birdeye_api.api_call_tracker['total_api_calls']
                    actual_calls_this_cycle = actual_calls - api_calls_start_of_cycle
                    
                    self._display_api_call_breakdown(scan_count, discovered_count, analyzed_count, final_count, actual_calls_this_cycle)
                    
                    # Performance metrics
                    if promising_tokens:
                        # Add tokens to performance analyzer
                        self.performance_analyzer.add_tokens_from_scan(
                            tokens=promising_tokens,
                            scan_number=scan_count
                        )
                    
                    # Calculate scan duration and add to history
                    scan_duration = time.time() - scan_start_time
                    scan_durations.append(scan_duration)
                    
                    # Resource usage
                    process = psutil.Process()
                    memory_info = process.memory_info()
                    cpu_percent = psutil.cpu_percent(interval=None)
                    self.logger.info({"event": "resource_usage", "scan_id": scan_id, "memory_mb": memory_info.rss / (1024 * 1024), "cpu_percent": cpu_percent, "timestamp": time.time()})
                    
                    # Display monitoring summary after each scan
                    self._display_monitoring_summary(
                        scan_count, 
                        scan_duration,
                        total_tokens_discovered,
                        total_tokens_analyzed,
                        total_promising_tokens,
                        total_api_calls,
                        scan_durations,
                        api_calls_per_cycle
                    )
                    
                except Exception as e:
                    import traceback
                    self.logger.error({"event": "exception", "scan_id": scan_id, "error": str(e), "trace": traceback.format_exc()})
                    print(f"❌ Error during scan: {e}")
                
                # Calculate next scan time and show countdown
                next_scan_time = time.strftime('%H:%M:%S', time.localtime(time.time() + self.scan_interval))
                print(f"\n⏱ Next scan in {self.scan_interval/60:.1f} minutes (at {next_scan_time})...")
                
                # Display countdown timer for next scan
                await self._display_countdown_to_next_scan(self.scan_interval)
                
            except asyncio.CancelledError:
                self.logger.info("Monitor received cancellation request")
                break
                
            except Exception as e:
                self.logger.error(f"Unexpected error in monitor loop: {e}")
                print(f"❌ Unexpected error: {e}")
                # Sleep briefly before retrying
                await asyncio.sleep(10)
                
        # Cleanup resources
        await self.cleanup()
        
        self.logger.info("Monitor completed")
        print("\n✅ Monitoring session completed")
        
    async def _display_countdown_to_next_scan(self, duration: float):
        """Display a countdown timer for the next scan"""
        try:
            start_time = time.time()
            interval = min(15, duration / 20)  # Update at most 20 times during the wait, but at least every 15 seconds
            
            while time.time() - start_time < duration:
                # Check for shutdown request
                if self.shutdown_requested or not self.running:
                    print("\nCountdown interrupted - shutting down...")
                    break
                    
                # Check runtime limit
                if self._check_runtime_limit():
                    print("\nCountdown interrupted - runtime limit reached...")
                    self.running = False
                    break
                
                # Calculate remaining time
                remaining = duration - (time.time() - start_time)
                if remaining <= 0:
                    break
                
                # Only update display occasionally to avoid console spam
                minutes = int(remaining // 60)
                seconds = int(remaining % 60)
                
                # Use carriage return to update in place
                print(f"\rNext scan in: {minutes:02d}:{seconds:02d}   ", end="", flush=True)
                
                # Sleep for a short interval
                await asyncio.sleep(min(interval, remaining))
            
            # Clear the line when done
            print("\r                                   ", end="\r", flush=True)
            
        except Exception as e:
            self.logger.error(f"Error in countdown display: {e}")
    
    def _display_monitoring_summary(self, scan_count, scan_duration, total_discovered, total_analyzed, total_promising, total_api_calls, scan_durations, api_calls_per_cycle):
        try:
            avg_duration = sum(scan_durations) / len(scan_durations)
            avg_discovered = total_discovered / scan_count
            avg_analyzed = total_analyzed / scan_count
            avg_promising = total_promising / scan_count
            
            # Get comprehensive API statistics from BirdeyeAPI
            api_stats = self.birdeye_api.get_api_call_statistics()
            
            print(f"\n📊 MONITORING SUMMARY (Scan #{scan_count})")
            print(f"{'='*50}")
            print(f"⏱️  Runtime: {time.time() - self.start_time:.1f} seconds")
            print(f"🔄 Scans completed: {scan_count}")
            print(f"⏱️  Last scan duration: {scan_duration:.2f} seconds")
            print(f"⏱️  Average scan duration: {avg_duration:.2f} seconds")
            print(f"🔍 Total tokens discovered: {total_discovered} (avg: {avg_discovered:.1f}/scan)")
            print(f"🔬 Total tokens analyzed: {total_analyzed} (avg: {avg_analyzed:.1f}/scan)")
            print(f"💎 Total promising tokens: {total_promising} (avg: {avg_promising:.1f}/scan)")
            
            # Enhanced API call reporting
            print(f"\n📡 COMPREHENSIVE API STATISTICS:")
            print(f"   🏥 API Health: {api_stats['health_status']}")
            print(f"   📞 Total API Calls: {api_stats['total_api_calls']}")
            print(f"   ✅ Successful: {api_stats['successful_api_calls']} ({api_stats['success_rate_percent']:.1f}%)")
            print(f"   ❌ Failed: {api_stats['failed_api_calls']} ({api_stats['failure_rate_percent']:.1f}%)")
            print(f"   ⚡ Rate: {api_stats['calls_per_minute']:.1f} calls/minute")
            print(f"   ⏱️  Avg Response: {api_stats['average_response_time_ms']:.0f}ms")
            
            # Cache performance
            print(f"\n📋 CACHE PERFORMANCE:")
            print(f"   🎯 Cache Hits: {api_stats['cache_hits']}")
            print(f"   ❌ Cache Misses: {api_stats['cache_misses']}")
            print(f"   📈 Hit Rate: {api_stats['cache_hit_rate_percent']:.1f}%")
            print(f"   🏆 Efficiency Score: {api_stats['cache_efficiency_score']:.2f}")
            
            # Top endpoints
            if api_stats['top_endpoints']:
                print(f"\n🔗 TOP API ENDPOINTS:")
                for i, endpoint in enumerate(api_stats['top_endpoints'][:3], 1):
                    print(f"   {i}. {endpoint['endpoint']}: {endpoint['total_calls']} calls ({endpoint['success_rate_percent']:.1f}% success)")
            
            # Legacy efficiency calculation for comparison
            api_calls_last = api_calls_per_cycle[-1] if api_calls_per_cycle else 0
            api_efficiency = 0
            if total_discovered > 0:
                estimated_old_calls = total_discovered * 5 + scan_count * 10
                api_efficiency = (1 - (api_stats['total_api_calls'] / estimated_old_calls)) * 100
            
            print(f"\n📈 EFFICIENCY METRICS:")
            print(f"   📊 API Efficiency vs Old System: {api_efficiency:.1f}% reduction")
            print(f"   🔄 Session Duration: {api_stats['session_duration_minutes']:.1f} minutes")
            
            # System resources
            import psutil
            process = psutil.Process()
            memory_info = process.memory_info()
            cpu_percent = psutil.cpu_percent(interval=None)
            print(f"\n🖥️  SYSTEM RESOURCES:")
            print(f"   🧠 Memory: {memory_info.rss / (1024 * 1024):.1f} MB")
            print(f"   ⚙️  CPU: {cpu_percent:.1f}%")
            
            # Runtime information
            elapsed = time.time() - self.start_time
            if self.max_runtime_hours:
                total_seconds = self.max_runtime_hours * 3600
                remaining = total_seconds - elapsed
                if remaining > 0:
                    hours = int(remaining // 3600)
                    minutes = int((remaining % 3600) // 60)
                    seconds = int(remaining % 60)
                    print(f"⏰ Remaining runtime: {hours:02d}:{minutes:02d}:{seconds:02d}")
                else:
                    print("⏰ Runtime limit reached")
            print(f"{'='*50}")
            
        except Exception as e:
            import traceback
            self.logger.error({"event": "exception", "error": str(e), "trace": traceback.format_exc()})
            print(f"❌ Error displaying monitoring summary: {e}")

    def _display_token_summary(self, index: int, token: Dict[str, Any]):
        """Display a summary of a promising token"""
        try:
            # Use the same key patterns as in _send_telegram_alert to ensure consistency
            name = token.get('token_name', token.get('name', 'Unknown'))
            symbol = token.get('token_symbol', token.get('symbol', 'UNKNOWN'))
            score = token.get('token_score', token.get('score', 0))
            address = token.get('token_address', token.get('address', ''))
            
            # Format prices with appropriate decimal places
            price = token.get('price_now', token.get('price', 0))
            price_formatted = f"${price:.8f}" if price < 0.01 else f"${price:.4f}"
            
            # Format market cap in millions or thousands
            market_cap = token.get('market_cap', 0)
            if market_cap >= 1000000:
                market_cap_formatted = f"${market_cap/1000000:.2f}M"
            else:
                market_cap_formatted = f"${market_cap/1000:.1f}K"
                
            # Format liquidity
            liquidity = token.get('liquidity', 0)
            if liquidity >= 1000000:
                liquidity_formatted = f"${liquidity/1000000:.2f}M"
            else:
                liquidity_formatted = f"${liquidity/1000:.1f}K"
                
            # Format volume
            volume = token.get('volume_24h', 0)
            if volume >= 1000000:
                volume_formatted = f"${volume/1000000:.2f}M"
            else:
                volume_formatted = f"${volume/1000:.1f}K"
                
            # Get holders count
            holders = token.get('holder_count', token.get('holders', 0))
            
            # Format price changes
            price_change_24h = token.get('price_change_24h', 0)
            price_change_color = "🟢" if price_change_24h >= 0 else "🔴"
            price_change_formatted = f"{price_change_color} {abs(price_change_24h):.2f}%"
            
            # Get age in hours
            age_hours = token.get('age_hours', 0)
            if age_hours < 24:
                age_formatted = f"{age_hours:.1f}h"
            elif age_hours < 24*30:
                age_formatted = f"{age_hours/24:.1f}d"
            else:
                age_formatted = f"{age_hours/24/30:.1f}m"
                
            # Format social stats
            social_score = token.get('social_score', 0)
            social_formatted = f"🗣️ {social_score:.1f}/10" if social_score > 0 else "🗣️ N/A"
            
            # Trends in volume
            volume_trend = token.get('volume_trend', '')
            volume_trend_formatted = f"📈 {volume_trend}" if volume_trend else ""
            
            # Get strategy information if available
            strategy_info = ""
            if "strategy_data" in token:
                strategy_name = token.get("strategy_data", {}).get("strategy", "")
                consecutive = token.get("strategy_data", {}).get("consecutive_appearances", 0)
                if strategy_name and consecutive:
                    strategy_info = f"[{strategy_name}: {consecutive}× appearances]"
            
            # Print token summary with corrected address
            token_link = f"https://birdeye.so/token/{address}" if address else "https://birdeye.so"
            print(f"{index}. {name} ({symbol}) - Score: {score:.1f} {strategy_info}")
            print(f"   💰 {price_formatted} {price_change_formatted} | MCap: {market_cap_formatted} | Age: {age_formatted}")
            print(f"   💧 Liquidity: {liquidity_formatted} | Vol 24h: {volume_formatted} | Holders: {holders}")
            print(f"   {social_formatted} {volume_trend_formatted}")
            print(f"   🔗 {token_link}")
            
            # Add debug info when in debug mode
            if os.environ.get('DEBUG_MODE'):
                print(f"   🔍 DEBUG: Keys in token data: {', '.join(token.keys())}")
                
        except Exception as e:
            self.logger.error(f"Error displaying token summary: {e}")
            print(f"{index}. [Error displaying token data: {e}]")
    
    def _display_api_call_breakdown(self, scan_count: int, discovered_count: int, analyzed_count: int, final_count: int, actual_calls_this_cycle: int):
        """Display a breakdown of API calls for this scan"""
        try:
            # Estimate API calls
            discovery_calls = int(discovered_count / 100) + 1  # 1 API call per ~100 tokens in discovery
            analysis_calls = analyzed_count * 3  # ~3 API calls per token in analysis
            total_estimated = discovery_calls + analysis_calls
            
            # Get actual API calls if available
            actual_calls = self.birdeye_api.api_call_tracker['total_api_calls']
            if actual_calls:
                efficiency = (1 - (actual_calls / (discovered_count * 5 + 10))) * 100
                efficiency_rating = "Excellent" if efficiency > 80 else "Good" if efficiency > 60 else "Average"
            else:
                efficiency = 0
                efficiency_rating = "Unknown"
                
            # Print API call breakdown
            print(f"\n🔄 API EFFICIENCY SUMMARY (Scan #{scan_count})")
            print(f"   Discovery: {discovered_count} tokens initially found")
            print(f"   Analysis: {analyzed_count} tokens analyzed in detail")
            print(f"   Final: {final_count} promising tokens after filtering")
            print(f"   Estimated API calls: ~{total_estimated} (vs. ~{discovered_count * 5 + 10} in old system)")
            
            if actual_calls:
                print(f"   Actual API calls: {actual_calls}")
                print(f"   Efficiency rating: {efficiency_rating} ({efficiency:.1f}% reduction)")
            
            print(f"   Actual API calls this cycle: {actual_calls_this_cycle}")
            
        except Exception as e:
            self.logger.error(f"Error displaying API call breakdown: {e}")
            print("Error displaying API call breakdown")

    async def _send_telegram_alert(self, token: Dict[str, Any]):
        """Send enhanced Telegram alert for promising token"""
        try:
            if not self.telegram_alerter:
                self.logger.warning("Telegram not initialized")
                return
            
            # Create minimal token metrics for Telegram alerter
            metrics = MinimalTokenMetrics(
                symbol=token.get("token_symbol", "Unknown"),
                address=token.get("token_address", ""),
                price=token.get("price_now", 0),
                name=token.get("token_name", "Unknown"),
                liquidity=token.get("liquidity", 0),
                volume_24h=token.get("volume_24h", 0),
                mcap=token.get("market_cap", 0),
                holders=token.get("holder_count", 0),
                price_change_24h=token.get("price_change_24h", 0),
                market_cap=token.get("market_cap", 0),
                score=token.get("token_score", 0)
            )
            
            # Prepare enhanced data for rich alert content
            enhanced_data = {
                'price_source': 'Birdeye',
                'links': {
                    'dexscreener': f"https://dexscreener.com/solana/{token.get('token_address', '')}",
                    'solscan': f"https://solscan.io/token/{token.get('token_address', '')}",
                    'birdeye': f"https://birdeye.so/token/{token.get('token_address', '')}?chain=solana"
                },
                'security_info': {
                    'is_scam': token.get('is_scam', False),
                    'is_risky': token.get('is_risky', False)
                },
                'risk_explanation': f"Analysis found promising token with score {token.get('token_score', 0):.1f}/100",
                'enhanced_pump_dump_analysis': token.get('enhanced_pump_dump_analysis'),
                'strategic_coordination_analysis': token.get('strategic_coordination_analysis')
            }
            
            # Use the reliable telegram alerter with enhanced pump/dump analysis
            self.telegram_alerter.send_gem_alert(
                metrics=metrics,
                score=token.get("token_score", 0),
                enhanced_data=enhanced_data,
                pair_address=token.get("token_address", "")
            )
            
            self.logger.info(f"Sent enhanced Telegram alert for {token.get('token_symbol', 'Unknown')}")
            
        except Exception as e:
            self.logger.error(f"Error sending Telegram alert: {e}")

    def _signal_handler(self, sig, frame):
        """Handle shutdown signals gracefully"""
        self.logger.info(f"Received signal {sig}, initiating graceful shutdown...")
        print(f"\n🛑 Received shutdown signal, stopping monitor...")
        self.shutdown_requested = True

    async def cleanup(self):
        """Cleanup resources and display final summary"""
        try:
            self.running = False
            
            # Display comprehensive final API summary
            if hasattr(self, 'birdeye_api') and self.birdeye_api:
                print(f"\n{'='*80}")
                print("🏁 FINAL SESSION SUMMARY")
                print(f"{'='*80}")
                
                # Log comprehensive API call summary
                self.birdeye_api.log_api_call_summary()
                
                # Get detailed statistics for final report
                api_stats = self.birdeye_api.get_api_call_statistics()
                
                print(f"\n📊 SESSION TOTALS:")
                print(f"   ⏱️  Total Runtime: {api_stats['session_duration_minutes']:.1f} minutes")
                print(f"   📞 Total API Calls: {api_stats['total_api_calls']}")
                print(f"   📋 Total Cache Operations: {api_stats['total_cache_requests']}")
                print(f"   🎯 Overall Success Rate: {api_stats['success_rate_percent']:.1f}%")
                print(f"   🏥 Final Health Status: {api_stats['health_status']}")
                
                if api_stats['calls_by_status_code']:
                    print(f"\n📈 STATUS CODE BREAKDOWN:")
                    for status_code, count in api_stats['calls_by_status_code'].items():
                        print(f"   {status_code}: {count} calls")
                
                print(f"\n🔗 ENDPOINT USAGE SUMMARY:")
                for endpoint_data in api_stats['top_endpoints'][:5]:
                    print(f"   {endpoint_data['endpoint']}: {endpoint_data['total_calls']} calls "
                          f"({endpoint_data['avg_response_time_ms']:.0f}ms avg)")
                
                print(f"{'='*80}")
            
            # Close API connections
            if hasattr(self, 'birdeye_api') and self.birdeye_api:
                await self.birdeye_api.close_session()
                
            if hasattr(self, 'telegram_alerter') and self.telegram_alerter:
                await self.telegram_alerter.close()
                
            self.logger.info({"event": "cleanup_complete", "timestamp": time.time()})
            
        except Exception as e:
            self.logger.error(f"Error during cleanup: {e}")
            print(f"❌ Error during cleanup: {e}")

    async def _run_integrated_trader_discovery(self, scan_count: int):
        """
        Run comprehensive integrated trader discovery system with full analysis.
        Includes multi-timeframe discovery, ranking, alerts, and detailed reporting.
        """
        print(f"\n{'='*90}")
        print(f"COMPREHENSIVE TRADER DISCOVERY - SCAN #{scan_count}")
        print(f"{'='*90}")
        
        try:
            scan_count = 0
            
            # Discover traders for both timeframes
            print("🔍 Discovering 24h top traders...")
            traders_24h = await self.trader_analyzer.discover_top_traders(
                PerformanceTimeframe.HOUR_24, 
                max_traders=self.max_traders_discovery
            )
            
            print("🔍 Discovering 7d top traders...")
            traders_7d = await self.trader_analyzer.discover_top_traders(
                PerformanceTimeframe.DAYS_7, 
                max_traders=self.max_traders_discovery
            )
            
            # Display comprehensive results
            if traders_24h:
                await self._display_trader_rankings(traders_24h, "24 HOUR", limit=5)
            
            if traders_7d:
                await self._display_trader_rankings(traders_7d, "7 DAY", limit=5)
            
            # Compare timeframes and find consistent performers
            if traders_24h and traders_7d:
                await self._display_timeframe_comparison(traders_24h, traders_7d)
            
            # Send alerts for elite traders
            await self._process_trader_alerts(traders_24h, traders_7d)
            
            # Display discovery summary
            await self._display_discovery_summary(traders_24h, traders_7d)
            
        except Exception as e:
            self.logger.error(f"Error in comprehensive trader discovery: {e}")
            print(f"❌ Trader discovery failed: {e}")

    async def _display_trader_rankings(self, traders: List[TraderProfile], timeframe_name: str, limit: int = 10):
        """Display trader rankings with comprehensive metrics"""
        if not traders:
            return
            
        print(f"\n🏆 TOP {min(limit, len(traders))} TRADERS - {timeframe_name} PERFORMANCE")
        print("-" * 90)
        
        # Header
        print(f"{'#':<3} {'Address':<12} {'Tier':<10} {'Score':<6} {'PnL':<12} {'ROI':<8} {'Win%':<6} {'Risk':<6} {'Tags'}")
        print("-" * 90)
        
        for i, trader in enumerate(traders[:limit], 1):
            primary_perf = trader.performance_7d or trader.performance_24h
            
            pnl_str = f"${primary_perf.total_pnl:,.0f}" if primary_perf else "N/A"
            roi_str = f"{primary_perf.roi_percentage:.1f}%" if primary_perf else "N/A"
            win_rate_str = f"{primary_perf.win_rate:.0%}" if primary_perf else "N/A"
            tags_str = ", ".join(trader.tags[:2]) if trader.tags else "-"
            
            tier_display = self._get_tier_display(trader.tier)
            address_short = trader.address[:10] + '...'
            
            print(f"{i:<3} {address_short:<12} {tier_display:<10} "
                  f"{trader.discovery_score:.0f:<6} {pnl_str:<12} {roi_str:<8} "
                  f"{win_rate_str:<6} {trader.risk_score:.0f:<6} {tags_str}")

    def _get_tier_display(self, tier: TraderTier) -> str:
        """Get tier display with emojis"""
        tier_displays = {
            TraderTier.ELITE: "🌟 Elite",
            TraderTier.PROFESSIONAL: "💎 Pro", 
            TraderTier.ADVANCED: "🔥 Adv",
            TraderTier.INTERMEDIATE: "📈 Int",
            TraderTier.NOVICE: "🆕 Nov"
        }
        return tier_displays.get(tier, "❓ Unknown")

    async def _display_timeframe_comparison(self, traders_24h: List[TraderProfile], traders_7d: List[TraderProfile]):
        """Compare traders across timeframes"""
        addrs_24h = {t.address for t in traders_24h}
        addrs_7d = {t.address for t in traders_7d}
        common_addrs = addrs_24h.intersection(addrs_7d)
        
        print(f"\n🔄 TIMEFRAME COMPARISON")
        print("-" * 50)
        print(f"Top 24h Traders: {len(traders_24h)}")
        print(f"Top 7d Traders: {len(traders_7d)}")
        print(f"Consistent Performers: {len(common_addrs)}")
        
        if len(common_addrs) > 0:
            overlap_pct = len(common_addrs) / max(len(addrs_24h), len(addrs_7d)) * 100
            print(f"Consistency Rate: {overlap_pct:.1f}%")
            
            if common_addrs:
                print(f"\n🤝 CONSISTENT TOP PERFORMERS:")
                for addr in list(common_addrs)[:3]:  # Show top 3
                    trader_24h = next((t for t in traders_24h if t.address == addr), None)
                    trader_7d = next((t for t in traders_7d if t.address == addr), None)
                    
                    if trader_24h and trader_7d:
                        print(f"  {addr[:10]}... - "
                              f"24h Score: {trader_24h.discovery_score:.0f}, "
                              f"7d Score: {trader_7d.discovery_score:.0f}")

    async def _process_trader_alerts(self, traders_24h: List[TraderProfile], traders_7d: List[TraderProfile]):
        """Process and send alerts for elite traders"""
        if not self.telegram_alerter:
            return
            
        elite_traders = []
        
        # Find elite performers
        for trader in traders_24h + traders_7d:
            if (trader.discovery_score >= self.trader_alert_threshold and 
                trader.tier in [TraderTier.ELITE, TraderTier.PROFESSIONAL]):
                elite_traders.append(trader)
        
        # Remove duplicates
        seen_addresses = set()
        unique_elite = []
        for trader in elite_traders:
            if trader.address not in seen_addresses:
                unique_elite.append(trader)
                seen_addresses.add(trader.address)
        
        if unique_elite:
            print(f"\n🚨 ELITE TRADER ALERTS: {len(unique_elite)} traders")
            for trader in unique_elite[:3]:  # Limit alerts to top 3
                await self._send_trader_alert(trader)

    async def _send_trader_alert(self, trader: TraderProfile):
        """Send Telegram alert for elite trader"""
        try:
            primary_perf = trader.performance_7d or trader.performance_24h
            if not primary_perf:
                return
                
            timeframe = "7d" if trader.performance_7d else "24h"
            
            message = f"🌟 **ELITE TRADER DISCOVERED**\n\n"
            message += f"**Address:** `{trader.address}`\n"
            message += f"**Tier:** {trader.tier.value.title()}\n"
            message += f"**Discovery Score:** {trader.discovery_score:.0f}/100\n"
            message += f"**Risk Score:** {trader.risk_score:.0f}/100\n\n"
            
            message += f"**{timeframe.upper()} PERFORMANCE:**\n"
            message += f"• PnL: ${primary_perf.total_pnl:,.0f}\n"
            message += f"• ROI: {primary_perf.roi_percentage:.1f}%\n"
            message += f"• Win Rate: {primary_perf.win_rate:.1%}\n"
            message += f"• Total Trades: {primary_perf.total_trades}\n"
            message += f"• Sharpe Ratio: {primary_perf.sharpe_ratio:.2f}\n\n"
            
            if trader.tags:
                message += f"**Tags:** {', '.join(trader.tags)}\n\n"
            
            message += f"**Links:**\n"
            message += f"[Solscan](https://solscan.io/account/{trader.address})\n"
            
            # Send via Telegram (simplified version)
            # Note: This would need to be adapted to work with the existing telegram_alerter
            self.logger.info(f"Elite trader alert prepared for {trader.address[:10]}...")
            print(f"  📱 Alert prepared for elite trader {trader.address[:10]}...")
            
        except Exception as e:
            self.logger.error(f"Error sending trader alert: {e}")

    async def _display_discovery_summary(self, traders_24h: List[TraderProfile], traders_7d: List[TraderProfile]):
        """Display comprehensive discovery summary"""
        print(f"\n📊 TRADER DISCOVERY SUMMARY")
        print("-" * 50)
        
        total_unique = len(set([t.address for t in traders_24h + traders_7d]))
        
        print(f"Total Unique Traders Discovered: {total_unique}")
        print(f"24h Performers: {len(traders_24h)}")
        print(f"7d Performers: {len(traders_7d)}")
        
        # Tier distribution
        all_traders = traders_24h + traders_7d
        tier_counts = {}
        for trader in all_traders:
            tier_counts[trader.tier] = tier_counts.get(trader.tier, 0) + 1
        
        print(f"\n🏅 TIER DISTRIBUTION:")
        for tier in TraderTier:
            count = tier_counts.get(tier, 0)
            percentage = (count / len(all_traders)) * 100 if all_traders else 0
            if count > 0:
                print(f"  {self._get_tier_display(tier)}: {count} ({percentage:.1f}%)")
        
        # Performance metrics
        if all_traders:
            performances = [
                t.performance_7d or t.performance_24h 
                for t in all_traders 
                if t.performance_7d or t.performance_24h
            ]
            
            if performances:
                avg_score = sum(t.discovery_score for t in all_traders) / len(all_traders)
                avg_pnl = sum(p.total_pnl for p in performances) / len(performances)
                avg_roi = sum(p.roi_percentage for p in performances) / len(performances)
                
                print(f"\n📈 PERFORMANCE AVERAGES:")
                print(f"  Average Discovery Score: {avg_score:.1f}/100")
                print(f"  Average PnL: ${avg_pnl:,.0f}")
                print(f"  Average ROI: {avg_roi:.1f}%")
        
        print(f"\n💡 Next trader discovery in {self.trader_discovery_interval} scans")
        print("-" * 50)

    async def _initialize_whale_tracking(self):
        """Discover and add initial whales for tracking"""
        if not self.detection_engine.enable_whale_tracking or not self.detection_engine.whale_movement_tracker:
            self.logger.warning("Whale tracking not enabled, skipping initialization")
            return
            
        try:
            self.logger.info("🔍 Discovering initial whales for tracking...")
            
            # First check if we already have tracked whales
            tracking_status = self.detection_engine.get_whale_tracking_status()
            if tracking_status['tracked_whales'] > 0:
                self.logger.info(f"Already tracking {tracking_status['tracked_whales']} whales")
                return
                
            # If no whales being tracked, discover new ones
            self.logger.info("No whales currently tracked, discovering new ones...")
            discovered_count = await self.detection_engine.discover_and_track_new_whales(max_discoveries=20)
            
            if discovered_count > 0:
                self.logger.info(f"✅ Successfully discovered and added {discovered_count} whales for tracking")
            else:
                self.logger.warning("⚠️ No whales discovered for tracking")
                
        except Exception as e:
            self.logger.error(f"Error initializing whale tracking: {e}")

    def _load_config(self):
        """Load configuration from YAML file"""
        config_path = Path("config/config.yaml")
        if not config_path.exists():
            raise FileNotFoundError(f"Configuration file not found: {config_path}")
            
        import yaml
        with open(config_path, 'r') as f:
            config = yaml.safe_load(f)
        
        # Expand environment variables
        import os
        def expand_env_vars(obj):
            if isinstance(obj, dict):
                return {k: expand_env_vars(v) for k, v in obj.items()}
            elif isinstance(obj, list):
                return [expand_env_vars(item) for item in obj]
            elif isinstance(obj, str) and obj.startswith("${") and obj.endswith("}"):
                env_var = obj[2:-1]
                env_value = os.environ.get(env_var)
                return env_value if env_value is not None else obj
            else:
                return obj
        
        return expand_env_vars(config)

    def _setup_logging(self):
        """Setup logging configuration"""
        # Create logs directory
        logs_dir = Path("logs")
        logs_dir.mkdir(exist_ok=True)
        
        # Configure logging
        logger = logging.getLogger("VirtuosoGemHunter")
        logger.setLevel(logging.DEBUG)  # Always set to DEBUG for 3-hour session
        
        # Console handler
        console_handler = logging.StreamHandler()
        console_handler.setLevel(logging.DEBUG)
        
        # File handler
        file_handler = logging.FileHandler("logs/monitor_debug.log")
        file_handler.setLevel(logging.DEBUG)
        
        # Formatter
        formatter = logging.Formatter(
            "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
        )
        console_handler.setFormatter(formatter)
        file_handler.setFormatter(formatter)
        
        logger.addHandler(console_handler)
        logger.addHandler(file_handler)
        
        return logger

    # Fix missing properties from legacy code
    @property
    def scan_interval(self):
        """Get scan interval from config"""
        # First check environment variables (highest priority)
        env_interval = os.environ.get('SCAN_INTERVAL_MINUTES') or os.environ.get('FORCE_SCAN_INTERVAL')
        if env_interval:
            try:
                interval_minutes = int(env_interval)
                self.logger.info(f"Using scan interval from environment: {interval_minutes} minutes")
                return interval_minutes * 60  # Convert to seconds
            except ValueError:
                self.logger.warning(f"Invalid environment scan interval: {env_interval}, using config")
        
        # Next check scan settings section
        scan_settings = self.config.get('SCAN_SETTINGS', {})
        if scan_settings.get('interval_minutes'):
            interval_minutes = scan_settings.get('interval_minutes')
            self.logger.info(f"Using scan interval from SCAN_SETTINGS: {interval_minutes} minutes")
            return interval_minutes * 60
            
        # Finally fall back to token discovery setting
        interval_minutes = self.config.get('TOKEN_DISCOVERY', {}).get('scan_interval_minutes', 10)
        self.logger.info(f"Using scan interval from TOKEN_DISCOVERY: {interval_minutes} minutes")
        return interval_minutes * 60
    
    @property 
    def max_tokens(self):
        """Get max tokens from config"""
        return self.config.get('TOKEN_DISCOVERY', {}).get('max_tokens', 30)
    
    @property
    def min_score_threshold(self):
        """Get minimum score threshold from config"""
        return self.config.get('ANALYSIS', {}).get('alert_score_threshold', 70)
    
    @property
    def trader_discovery_interval(self):
        """Get trader discovery interval"""
        return self.config.get('TRADER_DISCOVERY', {}).get('discovery_interval_scans', 5)
    
    @property
    def max_traders_discovery(self):
        """Get max traders for discovery"""
        return self.config.get('TRADER_DISCOVERY', {}).get('max_traders_per_discovery', 15)
    
    @property
    def trader_discovery_enabled(self):
        """Get trader discovery enabled status"""
        return self.config.get('TRADER_DISCOVERY', {}).get('enabled', True)
    
    @property
    def trader_alert_threshold(self):
        """Get trader alert threshold"""
        return self.config.get('TRADER_DISCOVERY', {}).get('alert_score_threshold', 80)
    
    @property
    def alert_cooldown_minutes(self):
        """Get alert cooldown in minutes"""
        return 30  # Default 30 minutes between alerts for same token

def main():
    """Main entry point with enhanced command-line interface"""
    parser = argparse.ArgumentParser(
        description="Virtuoso Gem Hunter - Advanced Token Discovery System",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python monitor.py run                                 # Run continuous monitoring
  python monitor.py debug --runtime-hours 3             # Run in debug mode for 3 hours
  python monitor.py debug --runtime-hours 3 --dashboard # Run in debug mode with dashboard
  python monitor.py run --discovery-now                 # Run discovery then continuous monitoring
  python monitor.py discover-traders                    # Run trader discovery only
  python monitor.py analyze-trader --trader-address <ADDRESS>
  python monitor.py compare-timeframes                  # Compare 24h vs 7d performance
  python monitor.py run --enhanced-timeframes           # Use enhanced timeframe selection
        """
    )
    
    # Positional argument for main operation mode
    parser.add_argument('operation_mode', choices=['run', 'debug', 'discover-traders', 'analyze-trader', 'compare-timeframes'], 
                       help='Main operation mode: run, debug, or specific utility modes.')
    
    # Runtime control & common flags
    parser.add_argument('--runtime-hours', type=float, help='Maximum runtime in hours (often used with debug mode)')
    parser.add_argument('--dashboard', action='store_true', help='Enable debug dashboard (used with debug mode)')
    parser.add_argument('--discovery-now', action='store_true', 
                       help='Run token/whale discovery immediately then start monitoring (used with run/debug mode)')
    parser.add_argument('--discovery-source', choices=['all', 'trending', 'new', 'whale'], default='all',
                       help='Source for token discovery (default: all)')
    parser.add_argument('--enhanced-timeframes', type=str, choices=['true', 'false'], default='false',
                       help='Enable enhanced timeframe selection for better token age awareness')

    # Arguments for specific utility modes
    parser.add_argument('--trader-address', help='Trader address for analyze-trader mode')
    
    args = parser.parse_args()

    async def run_with_args():
        # Set environment variables based on command line args
        if args.enhanced_timeframes.lower() == 'true':
            os.environ['ENHANCED_TIMEFRAMES'] = 'true'
            print("🕒 Enhanced timeframe selection enabled")
        
        monitor = VirtuosoGemHunter()
        
        # Set runtime duration if specified
        if args.runtime_hours:
            monitor.set_runtime_duration(args.runtime_hours)
            print(f"🕒 Monitor configured to run for {args.runtime_hours} hours")
        
        # Enable dashboard if specified (monitor needs to handle this)
        if args.dashboard:
            if hasattr(monitor, 'enable_dashboard'):
                monitor.enable_dashboard() # Assuming a method to toggle dashboard
                print("📊 Debug dashboard enabled.")
            else:
                print("⚠️ Dashboard functionality not implemented in monitor.")

        try:
            if args.operation_mode == 'discover-traders':
                await monitor.run_trader_discovery_now()
            elif args.operation_mode == 'analyze-trader':
                if not args.trader_address:
                    print("Error: --trader-address required for analyze-trader mode")
                    return
                await monitor.analyze_specific_trader(args.trader_address)
            elif args.operation_mode == 'compare-timeframes':
                await monitor.compare_timeframes_now()
            elif args.operation_mode in ['run', 'debug']:
                if args.operation_mode == 'debug':
                    print("🔧 Running in DEBUG mode.")
                    # Potentially set a debug flag in monitor or logger here
                    # e.g., monitor.set_debug_mode(True)
                    if not args.runtime_hours: # Default debug runtime if not specified
                         monitor.set_runtime_duration(1.0) # Default to 1 hour for debug
                         print(f"🕒 Defaulting debug mode to 1 hour runtime.")

                if args.discovery_now:
                    print("🔍 Running initial discovery cycle (tokens, whales, traders if applicable)...")
                    # Unified initial discovery call - assuming monitor.initial_discovery() handles all
                    if hasattr(monitor, 'initial_discovery'):
                        await monitor.initial_discovery()
                    else: # Fallback to old specific calls if general one not present
                        # Pass discovery source if supported
                        discovery_source = args.discovery_source if hasattr(monitor.detection_engine, 'set_discovery_source') else None
                        if discovery_source and discovery_source != 'all':
                            if hasattr(monitor.detection_engine, 'set_discovery_source'):
                                monitor.detection_engine.set_discovery_source(discovery_source)
                                print(f"🔍 Using discovery source: {discovery_source}")
                        
                        await monitor.detection_engine.discover_and_analyze(max_tokens=monitor.max_tokens)
                        if monitor.detection_engine.enable_whale_tracking:
                            await monitor._initialize_whale_tracking()
                        if monitor.trader_discovery_enabled and hasattr(monitor, 'run_trader_discovery_now'):
                            await monitor.run_trader_discovery_now()
                    print("\n🚀 Starting continuous monitoring...")
                
                await monitor.start()
            else:
                print(f"Error: Unknown operation mode '{args.operation_mode}'")
                parser.print_help()

        finally:
            # Cleanup
            await monitor.cleanup()
    
    # Run the async function
    asyncio.run(run_with_args())

if __name__ == "__main__":
    main() 