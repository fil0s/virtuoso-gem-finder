#!/usr/bin/env python3
"""
🏥 PRODUCTION HEALTH MONITOR
Real-time health monitoring for Early Gem Detector production system
"""

import asyncio
import logging
import time
import json
import psutil
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
from dataclasses import dataclass
from pathlib import Path

@dataclass
class HealthMetric:
    name: str
    status: str  # HEALTHY, WARNING, CRITICAL
    value: Any
    threshold: Any
    message: str
    timestamp: float

@dataclass
class SystemHealth:
    overall_status: str
    metrics: List[HealthMetric]
    uptime_seconds: float
    last_check: float

class ProductionHealthMonitor:
    """Production-grade health monitoring for Early Gem Detector"""
    
    def __init__(self, early_gem_detector=None):
        self.logger = logging.getLogger('ProductionHealthMonitor')
        self.detector = early_gem_detector
        
        # Health tracking
        self.start_time = time.time()
        self.health_history: List[SystemHealth] = []
        self.max_history = 100  # Keep last 100 health checks
        
        # Alert thresholds
        self.thresholds = {
            'cpu_usage': 85.0,          # CPU > 85% = WARNING
            'memory_usage': 80.0,       # Memory > 80% = WARNING
            'disk_usage': 90.0,         # Disk > 90% = WARNING
            'api_error_rate': 10.0,     # Error rate > 10% = WARNING
            'detection_cycle_time': 10.0, # Cycle time > 10s = WARNING
            'telegram_failures': 3,     # 3+ failures = WARNING
            'websocket_disconnects': 5  # 5+ disconnects = CRITICAL
        }
        
        # Counters
        self.counters = {
            'total_health_checks': 0,
            'warnings_issued': 0,
            'critical_alerts': 0,
            'api_calls_successful': 0,
            'api_calls_failed': 0,
            'detection_cycles_completed': 0,
            'telegram_alerts_sent': 0,
            'telegram_failures': 0,
            'websocket_reconnects': 0
        }
        
        self.logger.info("🏥 Production Health Monitor initialized")
    
    async def start_monitoring(self, check_interval: int = 60):
        """Start continuous health monitoring"""
        self.logger.info(f"🔄 Starting health monitoring (check every {check_interval}s)")
        
        while True:
            try:
                health_status = await self.perform_health_check()
                await self.process_health_status(health_status)
                
                # Log health summary
                self._log_health_summary(health_status)
                
                # Clean up old history
                self._cleanup_history()
                
                await asyncio.sleep(check_interval)
                
            except Exception as e:
                self.logger.error(f"❌ Health monitoring error: {e}")
                await asyncio.sleep(check_interval * 2)  # Wait longer on error
    
    async def perform_health_check(self) -> SystemHealth:
        """Perform comprehensive health check"""
        self.counters['total_health_checks'] += 1
        check_time = time.time()
        metrics = []
        
        # 1. System Resource Metrics
        cpu_metric = self._check_cpu_usage()
        memory_metric = self._check_memory_usage()
        disk_metric = self._check_disk_usage()
        
        metrics.extend([cpu_metric, memory_metric, disk_metric])
        
        # 2. Application Metrics
        if self.detector:
            app_metrics = await self._check_application_health()
            metrics.extend(app_metrics)
        
        # 3. API Health Metrics
        api_metrics = self._check_api_health()
        metrics.extend(api_metrics)
        
        # 4. Determine overall status
        overall_status = self._determine_overall_status(metrics)
        
        health_status = SystemHealth(
            overall_status=overall_status,
            metrics=metrics,
            uptime_seconds=check_time - self.start_time,
            last_check=check_time
        )
        
        # Store in history
        self.health_history.append(health_status)
        
        return health_status
    
    def _check_cpu_usage(self) -> HealthMetric:
        """Check CPU usage"""
        cpu_percent = psutil.cpu_percent(interval=1)
        threshold = self.thresholds['cpu_usage']
        
        if cpu_percent > threshold * 1.2:  # 20% over threshold = CRITICAL
            status = "CRITICAL"
            message = f"CPU usage critically high: {cpu_percent:.1f}%"
        elif cpu_percent > threshold:
            status = "WARNING"
            message = f"CPU usage high: {cpu_percent:.1f}%"
        else:
            status = "HEALTHY"
            message = f"CPU usage normal: {cpu_percent:.1f}%"
        
        return HealthMetric(
            name="cpu_usage",
            status=status,
            value=cpu_percent,
            threshold=threshold,
            message=message,
            timestamp=time.time()
        )
    
    def _check_memory_usage(self) -> HealthMetric:
        """Check memory usage"""
        memory = psutil.virtual_memory()
        memory_percent = memory.percent
        threshold = self.thresholds['memory_usage']
        
        if memory_percent > threshold * 1.2:
            status = "CRITICAL"
            message = f"Memory usage critically high: {memory_percent:.1f}%"
        elif memory_percent > threshold:
            status = "WARNING"
            message = f"Memory usage high: {memory_percent:.1f}%"
        else:
            status = "HEALTHY"
            message = f"Memory usage normal: {memory_percent:.1f}%"
        
        return HealthMetric(
            name="memory_usage",
            status=status,
            value=memory_percent,
            threshold=threshold,
            message=message,
            timestamp=time.time()
        )
    
    def _check_disk_usage(self) -> HealthMetric:
        """Check disk usage"""
        disk = psutil.disk_usage('/')
        disk_percent = (disk.used / disk.total) * 100
        threshold = self.thresholds['disk_usage']
        
        if disk_percent > threshold:
            status = "WARNING"
            message = f"Disk usage high: {disk_percent:.1f}%"
        else:
            status = "HEALTHY"
            message = f"Disk usage normal: {disk_percent:.1f}%"
        
        return HealthMetric(
            name="disk_usage",
            status=status,
            value=disk_percent,
            threshold=threshold,
            message=message,
            timestamp=time.time()
        )
    
    async def _check_application_health(self) -> List[HealthMetric]:
        """Check Early Gem Detector application health"""
        metrics = []
        
        # Check detection cycle performance
        if hasattr(self.detector, 'session_stats'):
            stats = self.detector.session_stats
            
            # Check cycle completion rate
            cycles = stats.get('cycles_completed', 0)
            if cycles > 0:
                avg_time = stats.get('total_detection_time', 0) / cycles
                threshold = self.thresholds['detection_cycle_time']
                
                if avg_time > threshold:
                    status = "WARNING"
                    message = f"Detection cycles slow: {avg_time:.2f}s avg"
                else:
                    status = "HEALTHY"
                    message = f"Detection cycles normal: {avg_time:.2f}s avg"
                
                metrics.append(HealthMetric(
                    name="cycle_performance",
                    status=status,
                    value=avg_time,
                    threshold=threshold,
                    message=message,
                    timestamp=time.time()
                ))
            
            # Check API success rate
            api_calls = stats.get('api_calls_made', 0)
            api_errors = stats.get('api_errors', 0)
            
            if api_calls > 0:
                error_rate = (api_errors / api_calls) * 100
                threshold = self.thresholds['api_error_rate']
                
                if error_rate > threshold:
                    status = "WARNING"
                    message = f"API error rate high: {error_rate:.1f}%"
                else:
                    status = "HEALTHY"
                    message = f"API error rate normal: {error_rate:.1f}%"
                
                metrics.append(HealthMetric(
                    name="api_error_rate",
                    status=status,
                    value=error_rate,
                    threshold=threshold,
                    message=message,
                    timestamp=time.time()
                ))
        
        # Check Telegram integration health
        if hasattr(self.detector, 'telegram_alerter') and self.detector.telegram_alerter:
            telegram_metric = self._check_telegram_health()
            metrics.append(telegram_metric)
        
        # Check WebSocket health (if pump.fun monitor exists)
        if hasattr(self.detector, 'pump_fun_monitor') and self.detector.pump_fun_monitor:
            websocket_metric = self._check_websocket_health()
            metrics.append(websocket_metric)
        
        return metrics
    
    def _check_api_health(self) -> List[HealthMetric]:
        """Check API connectivity health"""
        metrics = []
        
        # Calculate overall API health from counters
        total_api_calls = self.counters['api_calls_successful'] + self.counters['api_calls_failed']
        
        if total_api_calls > 0:
            success_rate = (self.counters['api_calls_successful'] / total_api_calls) * 100
            
            if success_rate < 90:
                status = "WARNING"
                message = f"API success rate low: {success_rate:.1f}%"
            else:
                status = "HEALTHY"
                message = f"API success rate good: {success_rate:.1f}%"
            
            metrics.append(HealthMetric(
                name="api_success_rate",
                status=status,
                value=success_rate,
                threshold=90.0,
                message=message,
                timestamp=time.time()
            ))
        
        return metrics
    
    def _check_telegram_health(self) -> HealthMetric:
        """Check Telegram integration health"""
        failures = self.counters['telegram_failures']
        threshold = self.thresholds['telegram_failures']
        
        if failures > threshold:
            status = "WARNING"
            message = f"Telegram failures high: {failures}"
        else:
            status = "HEALTHY"
            message = f"Telegram working: {failures} failures"
        
        return HealthMetric(
            name="telegram_health",
            status=status,
            value=failures,
            threshold=threshold,
            message=message,
            timestamp=time.time()
        )
    
    def _check_websocket_health(self) -> HealthMetric:
        """Check WebSocket connection health"""
        reconnects = self.counters['websocket_reconnects']
        threshold = self.thresholds['websocket_disconnects']
        
        if reconnects > threshold:
            status = "CRITICAL"
            message = f"WebSocket unstable: {reconnects} reconnects"
        elif reconnects > threshold // 2:
            status = "WARNING"
            message = f"WebSocket reconnecting: {reconnects} times"
        else:
            status = "HEALTHY"
            message = f"WebSocket stable: {reconnects} reconnects"
        
        return HealthMetric(
            name="websocket_health",
            status=status,
            value=reconnects,
            threshold=threshold,
            message=message,
            timestamp=time.time()
        )
    
    def _determine_overall_status(self, metrics: List[HealthMetric]) -> str:
        """Determine overall system health status"""
        has_critical = any(m.status == "CRITICAL" for m in metrics)
        has_warning = any(m.status == "WARNING" for m in metrics)
        
        if has_critical:
            return "CRITICAL"
        elif has_warning:
            return "WARNING"
        else:
            return "HEALTHY"
    
    async def process_health_status(self, health_status: SystemHealth):
        """Process health status and take actions"""
        
        # Count status types
        if health_status.overall_status == "WARNING":
            self.counters['warnings_issued'] += 1
        elif health_status.overall_status == "CRITICAL":
            self.counters['critical_alerts'] += 1
        
        # Take actions based on status
        if health_status.overall_status == "CRITICAL":
            await self._handle_critical_status(health_status)
        elif health_status.overall_status == "WARNING":
            await self._handle_warning_status(health_status)
    
    async def _handle_critical_status(self, health_status: SystemHealth):
        """Handle critical system status"""
        self.logger.error("🚨 CRITICAL SYSTEM STATUS DETECTED!")
        
        critical_metrics = [m for m in health_status.metrics if m.status == "CRITICAL"]
        for metric in critical_metrics:
            self.logger.error(f"   💥 {metric.name}: {metric.message}")
        
        # Could implement automatic recovery actions here
        # For now, just alert
    
    async def _handle_warning_status(self, health_status: SystemHealth):
        """Handle warning system status"""
        self.logger.warning("⚠️ System warnings detected")
        
        warning_metrics = [m for m in health_status.metrics if m.status == "WARNING"]
        for metric in warning_metrics:
            self.logger.warning(f"   ⚠️ {metric.name}: {metric.message}")
    
    def _log_health_summary(self, health_status: SystemHealth):
        """Log health summary"""
        uptime_hours = health_status.uptime_seconds / 3600
        
        status_emoji = {
            "HEALTHY": "✅",
            "WARNING": "⚠️",
            "CRITICAL": "🚨"
        }
        
        emoji = status_emoji.get(health_status.overall_status, "❓")
        
        self.logger.info(f"{emoji} System Health: {health_status.overall_status} (Uptime: {uptime_hours:.1f}h)")
        
        if health_status.overall_status != "HEALTHY":
            for metric in health_status.metrics:
                if metric.status != "HEALTHY":
                    self.logger.info(f"   {metric.name}: {metric.message}")
    
    def _cleanup_history(self):
        """Clean up old health history"""
        if len(self.health_history) > self.max_history:
            self.health_history = self.health_history[-self.max_history:]
    
    def get_health_dashboard(self) -> Dict[str, Any]:
        """Get comprehensive health dashboard data"""
        if not self.health_history:
            return {"status": "NO_DATA", "message": "No health data available"}
        
        latest = self.health_history[-1]
        
        return {
            "overall_status": latest.overall_status,
            "uptime_hours": latest.uptime_seconds / 3600,
            "last_check": datetime.fromtimestamp(latest.last_check).isoformat(),
            "metrics": [
                {
                    "name": m.name,
                    "status": m.status,
                    "value": m.value,
                    "threshold": m.threshold,
                    "message": m.message
                }
                for m in latest.metrics
            ],
            "counters": self.counters.copy(),
            "health_trend": [h.overall_status for h in self.health_history[-10:]]
        }
    
    def record_api_call(self, success: bool):
        """Record API call result for health tracking"""
        if success:
            self.counters['api_calls_successful'] += 1
        else:
            self.counters['api_calls_failed'] += 1
    
    def record_telegram_alert(self, success: bool):
        """Record Telegram alert result"""
        if success:
            self.counters['telegram_alerts_sent'] += 1
        else:
            self.counters['telegram_failures'] += 1
    
    def record_websocket_reconnect(self):
        """Record WebSocket reconnection"""
        self.counters['websocket_reconnects'] += 1
    
    def record_detection_cycle(self):
        """Record detection cycle completion"""
        self.counters['detection_cycles_completed'] += 1 