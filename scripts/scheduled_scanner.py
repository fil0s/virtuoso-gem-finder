#!/usr/bin/env python3
"""
Advanced Scheduled Token Scanner

This script provides advanced scheduling capabilities for token discovery and analysis
with integrated RugCheck security filtering. Supports cron-like scheduling, multiple
scan profiles, and intelligent resource management.
"""

import asyncio
import logging
import sys
import time
import signal
import json
import argparse
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Any, Optional
from dataclasses import dataclass, asdict
from enum import Enum

# Add project root to path
sys.path.append(str(Path(__file__).parent.parent))

from api.birdeye_connector import BirdeyeAPI
from api.rugcheck_connector import RugCheckConnector
from core.token_discovery_strategies import (
    VolumeMomentumStrategy, 
    RecentListingsStrategy, 
    PriceMomentumStrategy,
    LiquidityGrowthStrategy,
    HighTradingActivityStrategy
)
from utils.env_loader import load_environment_variables
from services.logger_setup import LoggerSetup
from utils.structured_logger import get_structured_logger


class ScanProfile(Enum):
    """Predefined scan profiles with different intervals and strategies"""
    AGGRESSIVE = "aggressive"      # Every 5 minutes, all strategies
    STANDARD = "standard"          # Every 10 minutes, balanced strategies  
    CONSERVATIVE = "conservative"  # Every 15 minutes, strict filtering
    DISCOVERY = "discovery"        # Every 30 minutes, focus on new tokens
    MONITORING = "monitoring"      # Every 60 minutes, track existing tokens


@dataclass
class ScanConfiguration:
    """Configuration for a scheduled scan"""
    profile: ScanProfile
    interval_minutes: int
    max_tokens_per_strategy: int
    strategies: List[str]
    rugcheck_enabled: bool
    risk_tolerance: str  # "low", "medium", "high"
    alert_threshold: float
    description: str


class ScheduledTokenScanner:
    """
    Advanced token scanner with flexible scheduling and RugCheck integration
    """
    
    def __init__(self, config_file: Optional[str] = None):
        """Initialize the scheduled scanner"""
        
        # Setup logging
        self.logger_setup = LoggerSetup("ScheduledScanner")
        self.logger = self.logger_setup.logger
        self.structured_logger = get_structured_logger('ScheduledScanner')
        
        # Load environment variables
        self.env_vars = load_environment_variables()
        
        # Initialize APIs
        self.birdeye_api = None
        self.rugcheck_connector = None
        
        # Scan configurations
        self.scan_profiles = self._create_scan_profiles()
        self.current_profile = ScanProfile.STANDARD
        self.current_config = self.scan_profiles[self.current_profile]
        
        # Runtime state
        self.running = False
        self.scan_count = 0
        self.last_scan_time = None
        self.next_scan_time = None
        self.total_tokens_discovered = 0
        self.total_tokens_filtered = 0
        self.scan_statistics = []
        
        # Setup signal handlers
        signal.signal(signal.SIGINT, self._signal_handler)
        signal.signal(signal.SIGTERM, self._signal_handler)
        
        self.logger.info("🛡️ Scheduled Token Scanner initialized with RugCheck integration")
    
    def _create_scan_profiles(self) -> Dict[ScanProfile, ScanConfiguration]:
        """Create predefined scan profiles"""
        profiles = {
            ScanProfile.AGGRESSIVE: ScanConfiguration(
                profile=ScanProfile.AGGRESSIVE,
                interval_minutes=5,
                max_tokens_per_strategy=15,
                strategies=["volume_momentum", "price_momentum", "recent_listings", "liquidity_growth", "high_activity"],
                rugcheck_enabled=True,
                risk_tolerance="medium",
                alert_threshold=60.0,
                description="Aggressive scanning every 5 minutes with all strategies"
            ),
            
            ScanProfile.STANDARD: ScanConfiguration(
                profile=ScanProfile.STANDARD,
                interval_minutes=10,
                max_tokens_per_strategy=12,
                strategies=["volume_momentum", "price_momentum", "recent_listings"],
                rugcheck_enabled=True,
                risk_tolerance="low",
                alert_threshold=70.0,
                description="Standard scanning every 10 minutes with balanced strategies"
            ),
            
            ScanProfile.CONSERVATIVE: ScanConfiguration(
                profile=ScanProfile.CONSERVATIVE,
                interval_minutes=15,
                max_tokens_per_strategy=8,
                strategies=["volume_momentum", "liquidity_growth"],
                rugcheck_enabled=True,
                risk_tolerance="low",
                alert_threshold=80.0,
                description="Conservative scanning every 15 minutes with strict filtering"
            ),
            
            ScanProfile.DISCOVERY: ScanConfiguration(
                profile=ScanProfile.DISCOVERY,
                interval_minutes=30,
                max_tokens_per_strategy=20,
                strategies=["recent_listings", "liquidity_growth"],
                rugcheck_enabled=True,
                risk_tolerance="medium",
                alert_threshold=65.0,
                description="Discovery-focused scanning every 30 minutes for new tokens"
            ),
            
            ScanProfile.MONITORING: ScanConfiguration(
                profile=ScanProfile.MONITORING,
                interval_minutes=60,
                max_tokens_per_strategy=10,
                strategies=["volume_momentum", "high_activity"],
                rugcheck_enabled=True,
                risk_tolerance="low",
                alert_threshold=75.0,
                description="Monitoring scanning every 60 minutes for established tokens"
            )
        }
        
        return profiles
    
    async def initialize_apis(self):
        """Initialize API connections"""
        if not self.env_vars.get("BIRDEYE_API_KEY"):
            raise ValueError("BIRDEYE_API_KEY not found in environment variables")
        
        # Initialize Birdeye API
        self.birdeye_api = BirdeyeAPI(
            api_key=self.env_vars["BIRDEYE_API_KEY"],
            logger=self.logger
        )
        
        # Initialize RugCheck connector
        self.rugcheck_connector = RugCheckConnector(logger=self.logger)
        
        self.logger.info("✅ API connections initialized")
    
    def set_scan_profile(self, profile: ScanProfile):
        """Set the active scan profile"""
        if profile not in self.scan_profiles:
            raise ValueError(f"Unknown scan profile: {profile}")
        
        self.current_profile = profile
        self.current_config = self.scan_profiles[profile]
        
        self.logger.info(f"📊 Scan profile set to: {profile.value}")
        self.logger.info(f"   Interval: {self.current_config.interval_minutes} minutes")
        self.logger.info(f"   Strategies: {', '.join(self.current_config.strategies)}")
        self.logger.info(f"   RugCheck: {'Enabled' if self.current_config.rugcheck_enabled else 'Disabled'}")
    
    async def run_single_scan(self) -> Dict[str, Any]:
        """Run a single scan cycle"""
        scan_start_time = time.time()
        scan_id = f"scan_{int(scan_start_time)}"
        
        self.structured_logger.info({
            "event": "scan_start",
            "scan_id": scan_id,
            "scan_count": self.scan_count + 1,
            "profile": self.current_profile.value,
            "timestamp": int(scan_start_time)
        })
        
        self.logger.info(f"🔍 Starting scan #{self.scan_count + 1} with {self.current_profile.value} profile")
        
        # Initialize strategy instances
        strategies = self._create_strategy_instances()
        
        # Run discovery strategies
        all_discovered_tokens = []
        strategy_results = {}
        
        for strategy_name, strategy in strategies.items():
            if strategy_name not in self.current_config.strategies:
                continue
            
            try:
                self.logger.info(f"   Running {strategy_name} strategy...")
                tokens = await strategy.execute(self.birdeye_api, scan_id=scan_id)
                
                strategy_results[strategy_name] = {
                    "tokens_found": len(tokens),
                    "tokens": tokens
                }
                
                all_discovered_tokens.extend(tokens)
                self.logger.info(f"   ✅ {strategy_name}: {len(tokens)} tokens discovered")
                
            except Exception as e:
                self.logger.error(f"   ❌ {strategy_name} strategy failed: {e}")
                strategy_results[strategy_name] = {
                    "tokens_found": 0,
                    "tokens": [],
                    "error": str(e)
                }
        
        # Remove duplicates
        unique_tokens = self._deduplicate_tokens(all_discovered_tokens)
        
        # Apply additional filtering if needed
        filtered_tokens = await self._apply_additional_filtering(unique_tokens, scan_id)
        
        # Calculate scan statistics
        scan_duration = time.time() - scan_start_time
        
        scan_stats = {
            "scan_id": scan_id,
            "scan_count": self.scan_count + 1,
            "profile": self.current_profile.value,
            "duration_seconds": scan_duration,
            "strategies_run": len([s for s in self.current_config.strategies if s in strategy_results]),
            "total_discovered": len(unique_tokens),
            "total_filtered": len(filtered_tokens),
            "tokens_removed": len(unique_tokens) - len(filtered_tokens),
            "strategy_results": strategy_results,
            "timestamp": int(scan_start_time)
        }
        
        # Update counters
        self.scan_count += 1
        self.last_scan_time = scan_start_time
        self.total_tokens_discovered += len(unique_tokens)
        self.total_tokens_filtered += len(filtered_tokens)
        self.scan_statistics.append(scan_stats)
        
        # Log results
        self.structured_logger.info({
            "event": "scan_complete",
            "scan_id": scan_id,
            "scan_stats": scan_stats,
            "timestamp": int(time.time())
        })
        
        self.logger.info(f"✅ Scan #{self.scan_count} complete:")
        self.logger.info(f"   Duration: {scan_duration:.1f}s")
        self.logger.info(f"   Discovered: {len(unique_tokens)} tokens")
        self.logger.info(f"   After filtering: {len(filtered_tokens)} tokens")
        self.logger.info(f"   Filtered out: {len(unique_tokens) - len(filtered_tokens)} tokens")
        
        return scan_stats
    
    def _create_strategy_instances(self) -> Dict[str, Any]:
        """Create instances of discovery strategies"""
        strategies = {
            "volume_momentum": VolumeMomentumStrategy(logger=self.logger),
            "recent_listings": RecentListingsStrategy(logger=self.logger),
            "price_momentum": PriceMomentumStrategy(logger=self.logger),
            "liquidity_growth": LiquidityGrowthStrategy(logger=self.logger),
            "high_activity": HighTradingActivityStrategy(logger=self.logger)
        }
        
        return strategies
    
    def _deduplicate_tokens(self, tokens: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Remove duplicate tokens based on address"""
        seen_addresses = set()
        unique_tokens = []
        
        for token in tokens:
            address = token.get("address")
            if address and address not in seen_addresses:
                seen_addresses.add(address)
                unique_tokens.append(token)
        
        return unique_tokens
    
    async def _apply_additional_filtering(self, tokens: List[Dict[str, Any]], scan_id: str) -> List[Dict[str, Any]]:
        """Apply additional filtering based on scan configuration"""
        if not tokens:
            return tokens
        
        # Apply risk tolerance filtering
        filtered_tokens = []
        
        for token in tokens:
            # Check if token has security analysis (from RugCheck)
            security_analysis = token.get("security_analysis", {})
            
            if security_analysis:
                risk_level = security_analysis.get("risk_level", "unknown")
                score = security_analysis.get("rugcheck_score", 0)
                
                # Apply risk tolerance
                if self.current_config.risk_tolerance == "low":
                    if risk_level in ["safe", "low_risk"] and score >= 70:
                        filtered_tokens.append(token)
                elif self.current_config.risk_tolerance == "medium":
                    if risk_level in ["safe", "low_risk", "medium_risk"] and score >= 50:
                        filtered_tokens.append(token)
                elif self.current_config.risk_tolerance == "high":
                    if risk_level != "critical_risk" and score >= 30:
                        filtered_tokens.append(token)
            else:
                # No security analysis - apply based on risk tolerance
                if self.current_config.risk_tolerance == "high":
                    filtered_tokens.append(token)
                # For low/medium risk tolerance, skip tokens without security analysis
        
        return filtered_tokens
    
    async def run_scheduled_scanning(self):
        """Run continuous scheduled scanning"""
        if not self.birdeye_api:
            await self.initialize_apis()
        
        self.running = True
        self.logger.info(f"🚀 Starting scheduled scanning with {self.current_profile.value} profile")
        self.logger.info(f"   Scan interval: {self.current_config.interval_minutes} minutes")
        self.logger.info(f"   RugCheck filtering: {'Enabled' if self.current_config.rugcheck_enabled else 'Disabled'}")
        
        while self.running:
            try:
                # Run scan
                await self.run_single_scan()
                
                # Calculate next scan time
                self.next_scan_time = time.time() + (self.current_config.interval_minutes * 60)
                next_scan_str = datetime.fromtimestamp(self.next_scan_time).strftime("%H:%M:%S")
                
                self.logger.info(f"⏰ Next scan in {self.current_config.interval_minutes} minutes (at {next_scan_str})")
                
                # Wait for next scan
                await self._wait_for_next_scan()
                
            except Exception as e:
                self.logger.error(f"❌ Scan failed: {e}")
                self.logger.info(f"⏰ Retrying in {self.current_config.interval_minutes} minutes...")
                await asyncio.sleep(self.current_config.interval_minutes * 60)
    
    async def _wait_for_next_scan(self):
        """Wait for the next scheduled scan with countdown"""
        if not self.running:
            return
        
        wait_time = self.current_config.interval_minutes * 60
        
        # Show countdown every minute for the first 5 minutes, then every 5 minutes
        countdown_interval = 60 if wait_time <= 300 else 300
        
        while wait_time > 0 and self.running:
            if wait_time % countdown_interval == 0 or wait_time <= 60:
                minutes_left = wait_time // 60
                seconds_left = wait_time % 60
                
                if minutes_left > 0:
                    self.logger.info(f"⏳ Next scan in {minutes_left}m {seconds_left}s...")
                else:
                    self.logger.info(f"⏳ Next scan in {seconds_left}s...")
            
            await asyncio.sleep(min(10, wait_time))
            wait_time -= min(10, wait_time)
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get scanning statistics"""
        if not self.scan_statistics:
            return {"message": "No scans completed yet"}
        
        # Calculate averages
        total_scans = len(self.scan_statistics)
        avg_duration = sum(s["duration_seconds"] for s in self.scan_statistics) / total_scans
        avg_discovered = sum(s["total_discovered"] for s in self.scan_statistics) / total_scans
        avg_filtered = sum(s["total_filtered"] for s in self.scan_statistics) / total_scans
        
        return {
            "profile": self.current_profile.value,
            "total_scans": total_scans,
            "total_tokens_discovered": self.total_tokens_discovered,
            "total_tokens_after_filtering": self.total_tokens_filtered,
            "average_scan_duration": avg_duration,
            "average_tokens_per_scan": avg_discovered,
            "average_filtered_per_scan": avg_filtered,
            "filtering_rate": (self.total_tokens_discovered - self.total_tokens_filtered) / max(self.total_tokens_discovered, 1) * 100,
            "last_scan_time": datetime.fromtimestamp(self.last_scan_time).isoformat() if self.last_scan_time else None,
            "next_scan_time": datetime.fromtimestamp(self.next_scan_time).isoformat() if self.next_scan_time else None
        }
    
    def _signal_handler(self, signum, frame):
        """Handle shutdown signals"""
        self.logger.info(f"🛑 Received signal {signum}, shutting down...")
        self.running = False
    
    async def shutdown(self):
        """Graceful shutdown"""
        self.running = False
        
        # Display final statistics
        stats = self.get_statistics()
        self.logger.info("📊 Final Statistics:")
        self.logger.info(f"   Total scans: {stats.get('total_scans', 0)}")
        self.logger.info(f"   Total tokens discovered: {stats.get('total_tokens_discovered', 0)}")
        self.logger.info(f"   Total tokens after filtering: {stats.get('total_tokens_after_filtering', 0)}")
        self.logger.info(f"   Average filtering rate: {stats.get('filtering_rate', 0):.1f}%")
        
        self.logger.info("✅ Scheduled scanner shutdown complete")


async def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(description="Advanced Scheduled Token Scanner with RugCheck")
    parser.add_argument("--profile", choices=[p.value for p in ScanProfile], 
                       default=ScanProfile.STANDARD.value,
                       help="Scan profile to use")
    parser.add_argument("--single-scan", action="store_true",
                       help="Run a single scan and exit")
    parser.add_argument("--stats", action="store_true",
                       help="Show statistics and exit")
    
    args = parser.parse_args()
    
    # Create scanner
    scanner = ScheduledTokenScanner()
    
    # Set profile
    profile = ScanProfile(args.profile)
    scanner.set_scan_profile(profile)
    
    try:
        if args.single_scan:
            # Run single scan
            await scanner.initialize_apis()
            await scanner.run_single_scan()
            stats = scanner.get_statistics()
            print(json.dumps(stats, indent=2))
        else:
            # Run continuous scanning
            await scanner.run_scheduled_scanning()
    
    except KeyboardInterrupt:
        print("\n🛑 Interrupted by user")
    except Exception as e:
        print(f"❌ Error: {e}")
        return 1
    finally:
        await scanner.shutdown()
    
    return 0


if __name__ == "__main__":
    exit_code = asyncio.run(main())