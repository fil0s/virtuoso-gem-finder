#!/usr/bin/env python3
"""
CU Budget Monitor Service

Monitors daily Compute Unit (CU) usage and sends alerts when budget thresholds are exceeded.
Part of the BirdEye API cost optimization implementation.
"""

import asyncio
import logging
import time
from datetime import datetime, timedelta
from typing import Dict, Any, Optional, List
import json
import os

from services.telegram_alerter import TelegramAlerter
from utils.structured_logger import get_structured_logger


class CUBudgetMonitor:
    """
    Monitor daily CU usage and send budget alerts.
    
    Features:
    - Daily CU budget tracking
    - 80% threshold alerts
    - 95% threshold critical alerts
    - Hourly usage rate monitoring
    - Projected daily usage warnings
    """
    
    def __init__(self, daily_budget_cus: int = 100000, alert_enabled: bool = True):
        """
        Initialize CU budget monitor.
        
        Args:
            daily_budget_cus: Daily CU budget limit
            alert_enabled: Whether to send alerts
        """
        self.daily_budget_cus = daily_budget_cus
        self.alert_enabled = alert_enabled
        
        self.logger = logging.getLogger(__name__)
        self.structured_logger = get_structured_logger('CUBudgetMonitor')
        
        # Alert thresholds
        self.thresholds = {
            'warning': 0.80,    # 80% threshold
            'critical': 0.95,   # 95% threshold
            'emergency': 1.0    # 100% threshold
        }
        
        # Usage tracking
        self.daily_usage = {
            'date': datetime.now().strftime('%Y-%m-%d'),
            'total_cus': 0,
            'hourly_usage': {},
            'alerts_sent': [],
            'last_reset': time.time()
        }
        
        # Alert cooldown (prevent spam)
        self.alert_cooldown = {
            'warning': 3600,    # 1 hour
            'critical': 1800,   # 30 minutes
            'emergency': 600    # 10 minutes
        }
        
        # Telegram alerter for notifications
        self.telegram_alerter = None
        if alert_enabled:
            try:
                self.telegram_alerter = TelegramAlerter()
            except Exception as e:
                self.logger.warning(f"Could not initialize Telegram alerter: {e}")
        
        self.logger.info(f"CU Budget Monitor initialized with daily budget: {daily_budget_cus:,} CUs")
    
    def add_cu_usage(self, cus_used: int, operation: str = "unknown", scan_id: Optional[str] = None):
        """
        Add CU usage to daily tracking.
        
        Args:
            cus_used: Number of CUs used
            operation: Description of the operation
            scan_id: Optional scan identifier
        """
        current_date = datetime.now().strftime('%Y-%m-%d')
        current_hour = datetime.now().strftime('%Y-%m-%d %H')
        
        # Reset daily usage if new day
        if current_date != self.daily_usage['date']:
            self._reset_daily_usage(current_date)
        
        # Add to daily total
        self.daily_usage['total_cus'] += cus_used
        
        # Add to hourly tracking
        if current_hour not in self.daily_usage['hourly_usage']:
            self.daily_usage['hourly_usage'][current_hour] = 0
        self.daily_usage['hourly_usage'][current_hour] += cus_used
        
        # Log usage
        self.structured_logger.info({
            "event": "cu_usage_added",
            "cus_used": cus_used,
            "total_daily_cus": self.daily_usage['total_cus'],
            "operation": operation,
            "scan_id": scan_id,
            "timestamp": int(time.time())
        })
        
        # Check if we need to send alerts
        asyncio.create_task(self._check_budget_alerts())
    
    def _reset_daily_usage(self, new_date: str):
        """Reset daily usage tracking for new day."""
        self.logger.info(f"Resetting daily CU usage tracking for {new_date}")
        
        # Save previous day's data if needed
        self._save_daily_usage_history()
        
        # Reset tracking
        self.daily_usage = {
            'date': new_date,
            'total_cus': 0,
            'hourly_usage': {},
            'alerts_sent': [],
            'last_reset': time.time()
        }
    
    def _save_daily_usage_history(self):
        """Save daily usage history to file."""
        try:
            history_dir = "data/cu_usage_history"
            os.makedirs(history_dir, exist_ok=True)
            
            filename = f"{history_dir}/cu_usage_{self.daily_usage['date']}.json"
            with open(filename, 'w') as f:
                json.dump(self.daily_usage, f, indent=2)
                
            self.logger.info(f"Saved daily CU usage history to {filename}")
        except Exception as e:
            self.logger.error(f"Failed to save daily usage history: {e}")
    
    async def _check_budget_alerts(self):
        """Check if budget alerts need to be sent."""
        if not self.alert_enabled:
            return
        
        usage_percentage = self.daily_usage['total_cus'] / self.daily_budget_cus
        current_time = time.time()
        
        # Determine alert level
        alert_level = None
        if usage_percentage >= self.thresholds['emergency']:
            alert_level = 'emergency'
        elif usage_percentage >= self.thresholds['critical']:
            alert_level = 'critical'
        elif usage_percentage >= self.thresholds['warning']:
            alert_level = 'warning'
        
        if alert_level:
            # Check if we've already sent this alert recently
            last_alert = self._get_last_alert_time(alert_level)
            if current_time - last_alert < self.alert_cooldown[alert_level]:
                return  # Still in cooldown
            
            # Send alert
            await self._send_budget_alert(alert_level, usage_percentage)
            
            # Record alert
            self.daily_usage['alerts_sent'].append({
                'level': alert_level,
                'timestamp': current_time,
                'usage_percentage': usage_percentage,
                'total_cus': self.daily_usage['total_cus']
            })
    
    def _get_last_alert_time(self, alert_level: str) -> float:
        """Get timestamp of last alert for given level."""
        for alert in reversed(self.daily_usage['alerts_sent']):
            if alert['level'] == alert_level:
                return alert['timestamp']
        return 0.0  # No previous alert
    
    async def _send_budget_alert(self, alert_level: str, usage_percentage: float):
        """Send budget alert via Telegram and logging."""
        cus_used = self.daily_usage['total_cus']
        cus_remaining = self.daily_budget_cus - cus_used
        
        # Create alert message
        emoji_map = {
            'warning': '⚠️',
            'critical': '🚨',
            'emergency': '🔴'
        }
        
        emoji = emoji_map.get(alert_level, '⚠️')
        
        message = f"{emoji} CU BUDGET ALERT - {alert_level.upper()}\n\n"
        message += f"📊 Daily Usage: {cus_used:,} / {self.daily_budget_cus:,} CUs ({usage_percentage:.1%})\n"
        message += f"💰 Remaining: {cus_remaining:,} CUs\n"
        
        # Add projected usage if we have enough hourly data
        projected_usage = self._calculate_projected_daily_usage()
        if projected_usage:
            message += f"📈 Projected Daily: {projected_usage:,} CUs ({projected_usage/self.daily_budget_cus:.1%})\n"
        
        # Add recommendations
        if alert_level == 'emergency':
            message += "\n🛑 EMERGENCY: Daily budget exceeded! Consider pausing non-critical operations."
        elif alert_level == 'critical':
            message += "\n🚨 CRITICAL: 95% budget used. Monitor usage closely."
        else:
            message += "\n⚠️ WARNING: 80% budget threshold reached."
        
        # Log alert
        self.logger.warning(f"CU Budget Alert ({alert_level}): {usage_percentage:.1%} of daily budget used")
        
        # Send Telegram alert if available
        if self.telegram_alerter:
            try:
                await self.telegram_alerter.send_alert(
                    title=f"CU Budget Alert - {alert_level.title()}",
                    message=message,
                    priority="high" if alert_level in ['critical', 'emergency'] else "medium"
                )
            except Exception as e:
                self.logger.error(f"Failed to send Telegram budget alert: {e}")
    
    def _calculate_projected_daily_usage(self) -> Optional[int]:
        """Calculate projected daily usage based on current hourly rate."""
        if not self.daily_usage['hourly_usage']:
            return None
        
        current_hour = datetime.now().hour
        if current_hour == 0:
            return None  # Too early to project
        
        # Calculate average hourly usage
        total_hourly_usage = sum(self.daily_usage['hourly_usage'].values())
        hours_elapsed = len(self.daily_usage['hourly_usage'])
        
        if hours_elapsed == 0:
            return None
        
        avg_hourly_usage = total_hourly_usage / hours_elapsed
        projected_daily = avg_hourly_usage * 24
        
        return int(projected_daily)
    
    def get_budget_status(self) -> Dict[str, Any]:
        """Get current budget status."""
        usage_percentage = self.daily_usage['total_cus'] / self.daily_budget_cus
        projected_usage = self._calculate_projected_daily_usage()
        
        return {
            'date': self.daily_usage['date'],
            'daily_budget_cus': self.daily_budget_cus,
            'total_cus_used': self.daily_usage['total_cus'],
            'cus_remaining': self.daily_budget_cus - self.daily_usage['total_cus'],
            'usage_percentage': usage_percentage,
            'projected_daily_usage': projected_usage,
            'projected_percentage': projected_usage / self.daily_budget_cus if projected_usage else None,
            'alert_level': self._get_current_alert_level(usage_percentage),
            'hourly_usage': self.daily_usage['hourly_usage'],
            'alerts_sent_today': len(self.daily_usage['alerts_sent'])
        }
    
    def _get_current_alert_level(self, usage_percentage: float) -> Optional[str]:
        """Get current alert level based on usage percentage."""
        if usage_percentage >= self.thresholds['emergency']:
            return 'emergency'
        elif usage_percentage >= self.thresholds['critical']:
            return 'critical'
        elif usage_percentage >= self.thresholds['warning']:
            return 'warning'
        return None
    
    async def get_daily_summary(self) -> Dict[str, Any]:
        """Get daily CU usage summary for session reporting."""
        status = self.get_budget_status()
        
        # Calculate efficiency metrics
        total_cus = status['total_cus_used']
        budget_cus = status['daily_budget_cus']
        usage_percentage = status['usage_percentage']
        
        # Determine efficiency grade
        if usage_percentage <= 0.5:  # Under 50%
            efficiency_grade = "A+ (Excellent)"
        elif usage_percentage <= 0.7:  # Under 70%
            efficiency_grade = "A (Very Good)"
        elif usage_percentage <= 0.8:  # Under 80%
            efficiency_grade = "B+ (Good)"
        elif usage_percentage <= 0.9:  # Under 90%
            efficiency_grade = "B (Fair)"
        elif usage_percentage <= 1.0:  # Under 100%
            efficiency_grade = "C (Caution)"
        else:  # Over 100%
            efficiency_grade = "D (Over Budget)"
        
        # Calculate estimated monthly cost
        monthly_projection = status['projected_daily_usage'] * 30 if status['projected_daily_usage'] else total_cus * 30
        monthly_cost = (monthly_projection / 3_000_000) * 99  # $99 per 3M CUs
        
        return {
            'date': status['date'],
            'total_cus_used': total_cus,
            'daily_budget_cus': budget_cus,
            'usage_percentage': usage_percentage,
            'efficiency_grade': efficiency_grade,
            'projected_daily_usage': status['projected_daily_usage'],
            'projected_monthly_usage': monthly_projection,
            'estimated_monthly_cost': monthly_cost,
            'alert_level': status['alert_level'],
            'alerts_sent_today': status['alerts_sent_today'],
            'hourly_usage_count': len(status['hourly_usage']),
            'budget_remaining': status['cus_remaining']
        }
    
    async def generate_daily_report(self) -> str:
        """Generate daily CU usage report."""
        status = self.get_budget_status()
        
        report = []
        report.append(f"📊 DAILY CU BUDGET REPORT - {status['date']}")
        report.append("=" * 50)
        report.append("")
        
        # Usage summary
        report.append("💰 USAGE SUMMARY:")
        report.append(f"   • Budget: {status['daily_budget_cus']:,} CUs")
        report.append(f"   • Used: {status['total_cus_used']:,} CUs ({status['usage_percentage']:.1%})")
        report.append(f"   • Remaining: {status['cus_remaining']:,} CUs")
        
        if status['projected_daily_usage']:
            report.append(f"   • Projected: {status['projected_daily_usage']:,} CUs ({status['projected_percentage']:.1%})")
        
        # Alert status
        if status['alert_level']:
            report.append(f"   • Alert Level: {status['alert_level'].upper()}")
        
        report.append("")
        
        # Hourly breakdown
        if status['hourly_usage']:
            report.append("⏰ HOURLY USAGE:")
            for hour, usage in sorted(status['hourly_usage'].items()):
                hour_display = hour.split(' ')[1] + ":00"
                report.append(f"   • {hour_display}: {usage:,} CUs")
        
        report.append("")
        
        # Alerts sent
        if status['alerts_sent_today'] > 0:
            report.append(f"🚨 ALERTS SENT TODAY: {status['alerts_sent_today']}")
            for alert in self.daily_usage['alerts_sent']:
                alert_time = datetime.fromtimestamp(alert['timestamp']).strftime('%H:%M')
                report.append(f"   • {alert_time}: {alert['level'].upper()} ({alert['usage_percentage']:.1%})")
        
        return "\n".join(report) 