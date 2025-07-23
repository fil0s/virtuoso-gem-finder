"""
Token Discovery Scheduler

This module implements a flexible scheduling system for token discovery
with time-based filtering strategies integrated with the existing system.
"""

import asyncio
import logging
import time
import os
import sys
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Callable, Tuple
from pathlib import Path

# Fix import path issues
current_dir = Path(__file__).parent.parent.absolute()
if str(current_dir) not in sys.path:
    sys.path.insert(0, str(current_dir))
    print(f"Added {current_dir} to Python path for TokenDiscoveryScheduler")

from api.batch_api_manager import BatchAPIManager
from core.config_manager import ConfigManager

# Try to import logger_setup from different locations
try:
    from utils.logger_setup import LoggerSetup
except ImportError:
    try:
        from services.logger_setup import LoggerSetup
        print("Using logger_setup from services module as fallback in TokenDiscoveryScheduler")
    except ImportError:
        # If still can't import, define a minimal fallback
        class LoggerSetup:
            def __init__(self, name, log_file=None, log_level="INFO"):
                self.logger = logging.getLogger(name)
                self.logger.setLevel(getattr(logging, log_level))
                handler = logging.StreamHandler()
                formatter = logging.Formatter('%(asctime)s [%(levelname)s] %(name)s - %(message)s')
                handler.setFormatter(formatter)
                self.logger.addHandler(handler)
            
            def set_level(self, level):
                self.logger.setLevel(getattr(logging, level))
        
        print("Using minimal LoggerSetup fallback implementation in TokenDiscoveryScheduler")

class DiscoverySchedule:
    """
    Represents a scheduled token discovery configuration with
    specific filtering rules tied to a time window.
    """
    def __init__(
        self,
        name: str,
        active_days: List[int],  # 0=Monday, 6=Sunday
        active_hours: List[Tuple[int, int]],  # [(start_hour, end_hour), ...]
        filter_config: Dict[str, Any],
        priority: int = 1,
        description: str = ""
    ):
        self.name = name
        self.active_days = active_days
        self.active_hours = active_hours
        self.filter_config = filter_config
        self.priority = priority
        self.description = description
        
    def is_active(self) -> bool:
        """Check if this schedule is currently active based on day and time"""
        now = datetime.now()
        current_day = now.weekday()  # 0=Monday, 6=Sunday
        current_hour = now.hour
        
        # Check if current day is in active days
        if current_day not in self.active_days:
            return False
            
        # Check if current hour is in any active hour range
        for start_hour, end_hour in self.active_hours:
            if start_hour <= current_hour < end_hour:
                return True
                
        return False
    
    def get_filter_adjustments(self) -> Dict[str, Any]:
        """Return the filter adjustments for this schedule"""
        return self.filter_config
        
    def __str__(self) -> str:
        days = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
        active_days_str = ", ".join(days[day] for day in self.active_days)
        
        hours_str = []
        for start, end in self.active_hours:
            hours_str.append(f"{start:02d}:00-{end:02d}:00")
        
        return (f"Schedule '{self.name}' (Priority: {self.priority})\n"
                f"  Active: {active_days_str}, Hours: {', '.join(hours_str)}\n"
                f"  Description: {self.description}")


class TokenDiscoveryScheduler:
    """
    Manages time-based token discovery schedules and applies appropriate
    filtering strategies based on active schedules.
    """
    
    def __init__(self, batch_manager: BatchAPIManager, config: Optional[Dict] = None):
        self.logger_setup = LoggerSetup('TokenDiscoveryScheduler')
        self.logger = self.logger_setup.logger
        
        self.batch_manager = batch_manager
        self.config_manager = ConfigManager()
        self.config = config or self.config_manager.get_config()
        
        # Load schedules from config or use defaults
        self.schedules = self._load_schedules()
        self.currently_active_schedule = None
        
        # Last evaluated timestamp to avoid frequent rechecks
        self.last_schedule_evaluation = 0
        self.schedule_check_interval = 300  # 5 minutes
    
    def _load_schedules(self) -> List[DiscoverySchedule]:
        """Load token discovery schedules from config or use defaults"""
        schedules_config = self.config.get('TOKEN_DISCOVERY', {}).get('schedules', [])
        
        if not schedules_config:
            self.logger.info("No custom schedules found in config, using defaults")
            return self._create_default_schedules()
            
        schedules = []
        for schedule_config in schedules_config:
            try:
                schedule = DiscoverySchedule(
                    name=schedule_config.get('name', 'Unnamed Schedule'),
                    active_days=schedule_config.get('active_days', [0, 1, 2, 3, 4, 5, 6]),
                    active_hours=schedule_config.get('active_hours', [(0, 24)]),
                    filter_config=schedule_config.get('filter_config', {}),
                    priority=schedule_config.get('priority', 1),
                    description=schedule_config.get('description', '')
                )
                schedules.append(schedule)
            except Exception as e:
                self.logger.error(f"Error loading schedule: {e}")
                
        if not schedules:
            self.logger.warning("Failed to load any valid schedules, using defaults")
            return self._create_default_schedules()
            
        return sorted(schedules, key=lambda s: s.priority, reverse=True)
        
    def _create_default_schedules(self) -> List[DiscoverySchedule]:
        """Create default discovery schedules based on best practices"""
        
        # Default schedules
        schedules = []
        
        # 1. US/European active trading hours (more strict filters)
        active_hours_schedule = DiscoverySchedule(
            name="Active Market Hours",
            active_days=[0, 1, 2, 3, 4],  # Weekdays
            active_hours=[(14, 22)],  # 14:00-22:00 UTC (covering US/EU trading hours)
            filter_config={
                "base_min_liquidity": 30000,  # Higher liquidity requirement
                "base_min_market_cap": 50000,  # Higher market cap
                "base_min_holder_count": 75,  # More holders
                "base_min_volume_24h": 15000,  # Higher volume
                "base_min_momentum_score": 40,  # Higher momentum score
                "social_bonus_multiplier": 1.2,  # Emphasize social signals during active hours
                "volume_spike_threshold": 200,  # Require stronger volume spikes
                "relaxation_level_multiplier": 0.9  # Less relaxation during active hours
            },
            priority=3,
            description="Strict filtering during active US/European trading hours"
        )
        schedules.append(active_hours_schedule)
        
        # 2. Asian market hours (balanced filters)
        asian_hours_schedule = DiscoverySchedule(
            name="Asian Market Hours",
            active_days=[0, 1, 2, 3, 4],  # Weekdays
            active_hours=[(0, 10)],  # 00:00-10:00 UTC (covering Asian trading hours)
            filter_config={
                "base_min_liquidity": 25000,
                "base_min_market_cap": 40000,
                "base_min_holder_count": 60,
                "base_min_volume_24h": 12000,
                "base_min_momentum_score": 35,
                "social_bonus_multiplier": 1.1,
                "volume_spike_threshold": 180,
                "relaxation_level_multiplier": 0.95
            },
            priority=2,
            description="Balanced filtering during Asian market hours"
        )
        schedules.append(asian_hours_schedule)
        
        # 3. Weekend schedule (relaxed filters to catch opportunities during lower liquidity)
        weekend_schedule = DiscoverySchedule(
            name="Weekend Hours",
            active_days=[5, 6],  # Saturday and Sunday
            active_hours=[(0, 24)],  # All day
            filter_config={
                "base_min_liquidity": 20000,  # Standard liquidity
                "base_min_market_cap": 30000,  # Standard market cap
                "base_min_holder_count": 50,  # Standard holders
                "base_min_volume_24h": 10000,  # Standard volume
                "base_min_momentum_score": 30,  # Standard momentum
                "social_bonus_multiplier": 1.3,  # Higher social emphasis during weekends
                "volume_spike_threshold": 150,  # More sensitive to volume spikes
                "relaxation_level_multiplier": 1.05  # Slightly more relaxation on weekends
            },
            priority=1,
            description="Relaxed filtering during weekend hours"
        )
        schedules.append(weekend_schedule)
        
        # 4. Off-hours schedule (more relaxed, catch opportunities others might miss)
        off_hours_schedule = DiscoverySchedule(
            name="Off Hours",
            active_days=[0, 1, 2, 3, 4],  # Weekdays
            active_hours=[(10, 14), (22, 24)],  # 10:00-14:00 and 22:00-24:00 UTC
            filter_config={
                "base_min_liquidity": 15000,  # Lower liquidity requirement
                "base_min_market_cap": 25000,  # Lower market cap
                "base_min_holder_count": 40,  # Fewer holders
                "base_min_volume_24h": 8000,  # Lower volume
                "base_min_momentum_score": 25,  # Lower momentum score
                "social_bonus_multiplier": 1.4,  # Higher emphasis on social signals
                "volume_spike_threshold": 120,  # More sensitive to smaller volume spikes
                "relaxation_level_multiplier": 1.1  # More relaxation in off hours
            },
            priority=0,
            description="Relaxed filtering during off-peak hours"
        )
        schedules.append(off_hours_schedule)
        
        return schedules
    
    def update_active_schedule(self) -> bool:
        """
        Check if it's time to update the active schedule and do so if needed.
        Returns True if the active schedule changed.
        """
        current_time = time.time()
        
        # Check if we need to evaluate (avoid checking too frequently)
        if current_time - self.last_schedule_evaluation < self.schedule_check_interval:
            return False
            
        self.last_schedule_evaluation = current_time
        
        # Find highest priority active schedule
        prev_active = self.currently_active_schedule
        self.currently_active_schedule = None
        
        for schedule in self.schedules:
            if schedule.is_active():
                self.currently_active_schedule = schedule
                break
                
        # Check if changed
        if prev_active != self.currently_active_schedule:
            if self.currently_active_schedule:
                self.logger.info(f"Activating schedule: {self.currently_active_schedule.name}")
            else:
                self.logger.info("No active schedule found, using default filters")
            return True
            
        return False
    
    def get_current_filter_adjustments(self) -> Dict[str, Any]:
        """
        Get the filter adjustments for the currently active schedule.
        If no schedule is active, returns empty dict (no adjustments).
        """
        # Update active schedule if needed
        self.update_active_schedule()
        
        if self.currently_active_schedule:
            return self.currently_active_schedule.get_filter_adjustments()
        
        return {}
    
    def apply_schedule_to_batch_manager(self) -> None:
        """
        Apply the current schedule's filtering adjustments to the batch manager.
        This modifies the batch manager's filtering parameters based on time.
        """
        adjustments = self.get_current_filter_adjustments()
        
        if not adjustments:
            # No adjustments needed, reset to defaults
            if hasattr(self.batch_manager, 'discovery_filter_overrides'):
                self.batch_manager.discovery_filter_overrides = {}
            return
            
        # Store adjustments in batch manager
        if not hasattr(self.batch_manager, 'discovery_filter_overrides'):
            self.batch_manager.discovery_filter_overrides = {}
        
        self.batch_manager.discovery_filter_overrides = adjustments
        
        self.logger.info(f"Applied filter adjustments from schedule: {self.currently_active_schedule.name}")
    
    def get_active_schedule_info(self) -> Dict[str, Any]:
        """Get information about the currently active schedule for display/logging"""
        self.update_active_schedule()
        
        if not self.currently_active_schedule:
            return {
                "active": False,
                "name": "No active schedule",
                "description": "Using default filters"
            }
            
        return {
            "active": True,
            "name": self.currently_active_schedule.name,
            "description": self.currently_active_schedule.description,
            "priority": self.currently_active_schedule.priority,
            "adjustments": self.currently_active_schedule.get_filter_adjustments()
        }
    
    def log_all_schedules(self) -> None:
        """Log all configured schedules for debugging"""
        self.logger.info(f"Configured discovery schedules ({len(self.schedules)}):")
        
        for i, schedule in enumerate(self.schedules):
            self.logger.info(f"{i+1}. {schedule}") 