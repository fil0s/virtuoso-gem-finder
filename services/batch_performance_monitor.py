"""
Batch Performance Monitor

Real-time performance monitoring and optimization tracking for batch processing operations.
Provides detailed metrics, cost analysis, and performance recommendations.
"""

import asyncio
import time
import logging
import json
import os
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass, asdict
from datetime import datetime, timedelta
from pathlib import Path
import psutil
import statistics
from collections import deque, defaultdict

from utils.structured_logger import get_structured_logger

@dataclass
class BatchOperationMetrics:
    """Metrics for a single batch operation."""
    operation_type: str
    start_time: float
    end_time: float
    tokens_requested: int
    tokens_delivered: int
    api_calls_made: int
    compute_units_used: int
    cache_hits: int
    cache_misses: int
    success_rate: float
    error_count: int
    fallback_used: bool
    batch_size: int
    efficiency_score: float

@dataclass
class PerformanceSnapshot:
    """Performance snapshot at a specific time."""
    timestamp: float
    total_operations: int
    avg_response_time: float
    cache_hit_rate: float
    api_calls_per_minute: float
    compute_units_per_hour: float
    cost_efficiency_score: float
    batch_usage_rate: float
    error_rate: float
    cpu_usage: float
    memory_usage_mb: float

class BatchPerformanceMonitor:
    """
    Real-time performance monitoring for batch processing operations.
    
    Features:
    - Real-time metrics collection and analysis
    - Cost optimization tracking
    - Performance trend analysis
    - Automated alerts and recommendations
    - Historical performance data
    """
    
    def __init__(self, logger: Optional[logging.Logger] = None):
        self.logger = logger or logging.getLogger(__name__)
        self.structured_logger = get_structured_logger('BatchPerformanceMonitor')
        
        # Performance data storage
        self.operation_history: deque = deque(maxlen=1000)  # Last 1000 operations
        self.performance_snapshots: deque = deque(maxlen=288)  # 24 hours of 5-min snapshots
        self.hourly_summaries: deque = deque(maxlen=168)  # 7 days of hourly summaries
        
        # Real-time tracking
        self.current_operations: Dict[str, Dict] = {}
        self.session_metrics = {
            'session_start': time.time(),
            'total_operations': 0,
            'total_api_calls': 0,
            'total_compute_units': 0,
            'total_cost_savings': 0.0,
            'cache_hits': 0,
            'cache_misses': 0,
            'errors': 0,
            'fallback_operations': 0
        }
        
        # Performance thresholds
        self.thresholds = {
            'max_response_time': 30.0,  # seconds
            'min_cache_hit_rate': 0.60,  # 60%
            'max_error_rate': 0.05,  # 5%
            'min_efficiency_score': 0.70,  # 70%
            'max_api_calls_per_minute': 120,
            'max_cost_per_hour': 10.0  # USD
        }
        
        # Alert tracking
        self.alerts_sent = defaultdict(float)  # Alert type -> last sent time
        self.alert_cooldown = 300  # 5 minutes between same alert types
        
        # Storage configuration
        self.data_dir = Path("data/performance_monitoring")
        self.data_dir.mkdir(parents=True, exist_ok=True)
        
        # Start background monitoring
        self._monitoring_task = None
        self._start_background_monitoring()
        
        self.logger.info("🔍 Batch Performance Monitor initialized")

    def _start_background_monitoring(self):
        """Start background monitoring tasks."""
        if self._monitoring_task is None or self._monitoring_task.done():
            self._monitoring_task = asyncio.create_task(self._background_monitoring_loop())

    async def _background_monitoring_loop(self):
        """Background loop for periodic monitoring tasks."""
        try:
            while True:
                await asyncio.sleep(300)  # 5 minutes
                await self._create_performance_snapshot()
                self._check_performance_thresholds()
                self._cleanup_old_data()
        except asyncio.CancelledError:
            self.logger.info("Background monitoring stopped")
        except Exception as e:
            self.logger.error(f"Background monitoring error: {e}")

    async def start_operation(self, operation_id: str, operation_type: str, tokens_requested: int, batch_size: int) -> None:
        """Start tracking a batch operation."""
        self.current_operations[operation_id] = {
            'operation_type': operation_type,
            'start_time': time.time(),
            'tokens_requested': tokens_requested,
            'batch_size': batch_size,
            'api_calls_made': 0,
            'compute_units_used': 0,
            'cache_hits': 0,
            'cache_misses': 0,
            'errors': 0,
            'fallback_used': False
        }
        
        self.structured_logger.info({
            "event": "batch_operation_start",
            "operation_id": operation_id,
            "operation_type": operation_type,
            "tokens_requested": tokens_requested,
            "batch_size": batch_size,
            "timestamp": time.time()
        })

    async def update_operation(self, operation_id: str, **metrics) -> None:
        """Update metrics for an ongoing operation."""
        if operation_id in self.current_operations:
            self.current_operations[operation_id].update(metrics)

    async def complete_operation(self, operation_id: str, tokens_delivered: int, success_rate: float) -> BatchOperationMetrics:
        """Complete tracking a batch operation and return metrics."""
        if operation_id not in self.current_operations:
            self.logger.warning(f"Operation {operation_id} not found in current operations")
            return None
        
        operation_data = self.current_operations.pop(operation_id)
        end_time = time.time()
        
        # Calculate efficiency score
        efficiency_score = self._calculate_efficiency_score(
            operation_data['tokens_requested'],
            tokens_delivered,
            operation_data['api_calls_made'],
            operation_data['batch_size'],
            success_rate
        )
        
        # Create metrics object
        metrics = BatchOperationMetrics(
            operation_type=operation_data['operation_type'],
            start_time=operation_data['start_time'],
            end_time=end_time,
            tokens_requested=operation_data['tokens_requested'],
            tokens_delivered=tokens_delivered,
            api_calls_made=operation_data['api_calls_made'],
            compute_units_used=operation_data['compute_units_used'],
            cache_hits=operation_data['cache_hits'],
            cache_misses=operation_data['cache_misses'],
            success_rate=success_rate,
            error_count=operation_data['errors'],
            fallback_used=operation_data['fallback_used'],
            batch_size=operation_data['batch_size'],
            efficiency_score=efficiency_score
        )
        
        # Store metrics
        self.operation_history.append(metrics)
        
        # Update session metrics
        self.session_metrics['total_operations'] += 1
        self.session_metrics['total_api_calls'] += operation_data['api_calls_made']
        self.session_metrics['total_compute_units'] += operation_data['compute_units_used']
        self.session_metrics['cache_hits'] += operation_data['cache_hits']
        self.session_metrics['cache_misses'] += operation_data['cache_misses']
        self.session_metrics['errors'] += operation_data['errors']
        if operation_data['fallback_used']:
            self.session_metrics['fallback_operations'] += 1
        
        # Log completion
        self.structured_logger.info({
            "event": "batch_operation_complete",
            "operation_id": operation_id,
            "operation_type": operation_data['operation_type'],
            "duration": end_time - operation_data['start_time'],
            "tokens_requested": operation_data['tokens_requested'],
            "tokens_delivered": tokens_delivered,
            "success_rate": success_rate,
            "efficiency_score": efficiency_score,
            "api_calls": operation_data['api_calls_made'],
            "compute_units": operation_data['compute_units_used'],
            "cache_hit_rate": operation_data['cache_hits'] / max(1, operation_data['cache_hits'] + operation_data['cache_misses']),
            "timestamp": end_time
        })
        
        return metrics

    def _calculate_efficiency_score(self, requested: int, delivered: int, api_calls: int, batch_size: int, success_rate: float) -> float:
        """Calculate efficiency score for a batch operation."""
        # Base score from delivery rate
        delivery_rate = delivered / max(1, requested)
        
        # Batch efficiency (how well we used batching)
        ideal_api_calls = max(1, (requested + batch_size - 1) // batch_size)  # Ceiling division
        batch_efficiency = ideal_api_calls / max(1, api_calls)
        
        # Combine metrics
        efficiency_score = (
            delivery_rate * 0.4 +  # 40% weight on delivery
            batch_efficiency * 0.4 +  # 40% weight on batch efficiency
            success_rate * 0.2  # 20% weight on success rate
        )
        
        return min(1.0, efficiency_score)

    async def _create_performance_snapshot(self) -> None:
        """Create a performance snapshot for trend analysis."""
        current_time = time.time()
        
        # Calculate metrics from recent operations (last 5 minutes)
        recent_ops = [op for op in self.operation_history 
                     if current_time - op.end_time <= 300]
        
        if not recent_ops:
            return
        
        # Calculate snapshot metrics
        avg_response_time = statistics.mean([op.end_time - op.start_time for op in recent_ops])
        
        total_cache_ops = sum(op.cache_hits + op.cache_misses for op in recent_ops)
        cache_hit_rate = sum(op.cache_hits for op in recent_ops) / max(1, total_cache_ops)
        
        api_calls_per_minute = sum(op.api_calls_made for op in recent_ops) / 5.0  # 5-minute window
        compute_units_per_hour = sum(op.compute_units_used for op in recent_ops) * 12  # Extrapolate to hourly
        
        cost_efficiency_score = statistics.mean([op.efficiency_score for op in recent_ops])
        
        batch_ops = [op for op in recent_ops if op.batch_size > 1]
        batch_usage_rate = len(batch_ops) / len(recent_ops)
        
        error_rate = sum(op.error_count for op in recent_ops) / max(1, len(recent_ops))
        
        # System metrics
        cpu_usage = psutil.cpu_percent()
        memory_usage_mb = psutil.virtual_memory().used // 1024 // 1024
        
        snapshot = PerformanceSnapshot(
            timestamp=current_time,
            total_operations=len(recent_ops),
            avg_response_time=avg_response_time,
            cache_hit_rate=cache_hit_rate,
            api_calls_per_minute=api_calls_per_minute,
            compute_units_per_hour=compute_units_per_hour,
            cost_efficiency_score=cost_efficiency_score,
            batch_usage_rate=batch_usage_rate,
            error_rate=error_rate,
            cpu_usage=cpu_usage,
            memory_usage_mb=memory_usage_mb
        )
        
        self.performance_snapshots.append(snapshot)
        
        self.structured_logger.info({
            "event": "performance_snapshot",
            "snapshot": asdict(snapshot)
        })

    def _check_performance_thresholds(self) -> None:
        """Check performance against thresholds and send alerts if needed."""
        if not self.performance_snapshots:
            return
        
        latest = self.performance_snapshots[-1]
        current_time = time.time()
        
        # Check thresholds and send alerts
        alerts = []
        
        if latest.avg_response_time > self.thresholds['max_response_time']:
            if current_time - self.alerts_sent['slow_response'] > self.alert_cooldown:
                alerts.append({
                    'type': 'slow_response',
                    'message': f"High response time: {latest.avg_response_time:.2f}s (threshold: {self.thresholds['max_response_time']}s)",
                    'severity': 'warning'
                })
                self.alerts_sent['slow_response'] = current_time
        
        if latest.cache_hit_rate < self.thresholds['min_cache_hit_rate']:
            if current_time - self.alerts_sent['low_cache_hit'] > self.alert_cooldown:
                alerts.append({
                    'type': 'low_cache_hit',
                    'message': f"Low cache hit rate: {latest.cache_hit_rate:.2%} (threshold: {self.thresholds['min_cache_hit_rate']:.2%})",
                    'severity': 'warning'
                })
                self.alerts_sent['low_cache_hit'] = current_time
        
        if latest.error_rate > self.thresholds['max_error_rate']:
            if current_time - self.alerts_sent['high_error_rate'] > self.alert_cooldown:
                alerts.append({
                    'type': 'high_error_rate',
                    'message': f"High error rate: {latest.error_rate:.2%} (threshold: {self.thresholds['max_error_rate']:.2%})",
                    'severity': 'critical'
                })
                self.alerts_sent['high_error_rate'] = current_time
        
        if latest.cost_efficiency_score < self.thresholds['min_efficiency_score']:
            if current_time - self.alerts_sent['low_efficiency'] > self.alert_cooldown:
                alerts.append({
                    'type': 'low_efficiency',
                    'message': f"Low efficiency score: {latest.cost_efficiency_score:.2%} (threshold: {self.thresholds['min_efficiency_score']:.2%})",
                    'severity': 'warning'
                })
                self.alerts_sent['low_efficiency'] = current_time
        
        if latest.api_calls_per_minute > self.thresholds['max_api_calls_per_minute']:
            if current_time - self.alerts_sent['high_api_usage'] > self.alert_cooldown:
                alerts.append({
                    'type': 'high_api_usage',
                    'message': f"High API usage: {latest.api_calls_per_minute:.1f} calls/min (threshold: {self.thresholds['max_api_calls_per_minute']})",
                    'severity': 'warning'
                })
                self.alerts_sent['high_api_usage'] = current_time
        
        # Log alerts
        for alert in alerts:
            self.structured_logger.warning({
                "event": "performance_alert",
                "alert_type": alert['type'],
                "message": alert['message'],
                "severity": alert['severity'],
                "timestamp": current_time
            })
            
            if alert['severity'] == 'critical':
                self.logger.error(f"🚨 CRITICAL ALERT: {alert['message']}")
            else:
                self.logger.warning(f"⚠️ PERFORMANCE ALERT: {alert['message']}")

    def _cleanup_old_data(self) -> None:
        """Clean up old performance data to manage memory usage."""
        current_time = time.time()
        
        # Remove operation history older than 24 hours
        cutoff_time = current_time - 86400  # 24 hours
        while self.operation_history and self.operation_history[0].end_time < cutoff_time:
            self.operation_history.popleft()

    def get_performance_summary(self, hours: int = 1) -> Dict[str, Any]:
        """Get performance summary for the specified time period."""
        current_time = time.time()
        cutoff_time = current_time - (hours * 3600)
        
        # Filter recent operations
        recent_ops = [op for op in self.operation_history 
                     if op.end_time >= cutoff_time]
        
        if not recent_ops:
            return {'error': 'No operations in specified time period'}
        
        # Calculate summary metrics
        total_operations = len(recent_ops)
        avg_response_time = statistics.mean([op.end_time - op.start_time for op in recent_ops])
        
        total_cache_ops = sum(op.cache_hits + op.cache_misses for op in recent_ops)
        cache_hit_rate = sum(op.cache_hits for op in recent_ops) / max(1, total_cache_ops)
        
        total_api_calls = sum(op.api_calls_made for op in recent_ops)
        total_compute_units = sum(op.compute_units_used for op in recent_ops)
        
        avg_efficiency = statistics.mean([op.efficiency_score for op in recent_ops])
        
        batch_ops = [op for op in recent_ops if op.batch_size > 1]
        batch_usage_rate = len(batch_ops) / total_operations
        
        total_errors = sum(op.error_count for op in recent_ops)
        error_rate = total_errors / total_operations
        
        fallback_rate = len([op for op in recent_ops if op.fallback_used]) / total_operations
        
        # Calculate cost savings (estimated)
        individual_calls_needed = sum(op.tokens_requested for op in recent_ops)
        actual_calls_made = total_api_calls
        calls_saved = max(0, individual_calls_needed - actual_calls_made)
        cost_savings_percentage = (calls_saved / max(1, individual_calls_needed)) * 100
        
        return {
            'time_period_hours': hours,
            'total_operations': total_operations,
            'avg_response_time_seconds': round(avg_response_time, 2),
            'cache_hit_rate': round(cache_hit_rate, 3),
            'total_api_calls': total_api_calls,
            'total_compute_units': total_compute_units,
            'avg_efficiency_score': round(avg_efficiency, 3),
            'batch_usage_rate': round(batch_usage_rate, 3),
            'error_rate': round(error_rate, 3),
            'fallback_rate': round(fallback_rate, 3),
            'cost_savings_percentage': round(cost_savings_percentage, 1),
            'calls_saved': calls_saved,
            'api_calls_per_hour': round(total_api_calls / hours, 1),
            'compute_units_per_hour': round(total_compute_units / hours, 1)
        }

    def get_real_time_metrics(self) -> Dict[str, Any]:
        """Get real-time performance metrics."""
        current_time = time.time()
        session_duration = current_time - self.session_metrics['session_start']
        
        # Current operations
        active_operations = len(self.current_operations)
        
        # Session averages
        avg_api_calls_per_op = (self.session_metrics['total_api_calls'] / 
                               max(1, self.session_metrics['total_operations']))
        
        total_cache_ops = self.session_metrics['cache_hits'] + self.session_metrics['cache_misses']
        session_cache_hit_rate = self.session_metrics['cache_hits'] / max(1, total_cache_ops)
        
        # Recent performance (last 5 minutes)
        recent_snapshots = [s for s in self.performance_snapshots 
                           if current_time - s.timestamp <= 300]
        
        if recent_snapshots:
            latest_snapshot = recent_snapshots[-1]
            recent_avg_response = statistics.mean([s.avg_response_time for s in recent_snapshots])
            recent_cache_hit_rate = statistics.mean([s.cache_hit_rate for s in recent_snapshots])
        else:
            latest_snapshot = None
            recent_avg_response = 0
            recent_cache_hit_rate = 0
        
        return {
            'timestamp': current_time,
            'session_duration_hours': round(session_duration / 3600, 2),
            'active_operations': active_operations,
            'session_totals': {
                'operations': self.session_metrics['total_operations'],
                'api_calls': self.session_metrics['total_api_calls'],
                'compute_units': self.session_metrics['total_compute_units'],
                'errors': self.session_metrics['errors'],
                'fallback_operations': self.session_metrics['fallback_operations']
            },
            'session_averages': {
                'api_calls_per_operation': round(avg_api_calls_per_op, 2),
                'cache_hit_rate': round(session_cache_hit_rate, 3)
            },
            'recent_performance': {
                'avg_response_time': round(recent_avg_response, 2),
                'cache_hit_rate': round(recent_cache_hit_rate, 3),
                'snapshots_count': len(recent_snapshots)
            },
            'system_resources': {
                'cpu_percent': psutil.cpu_percent(),
                'memory_mb': psutil.virtual_memory().used // 1024 // 1024,
                'memory_percent': psutil.virtual_memory().percent
            }
        }

    def get_optimization_recommendations(self) -> List[Dict[str, Any]]:
        """Get optimization recommendations based on performance data."""
        recommendations = []
        
        if not self.performance_snapshots:
            return recommendations
        
        # Analyze recent performance
        recent_snapshots = list(self.performance_snapshots)[-12:]  # Last hour
        
        if len(recent_snapshots) >= 3:
            avg_cache_hit_rate = statistics.mean([s.cache_hit_rate for s in recent_snapshots])
            avg_batch_usage = statistics.mean([s.batch_usage_rate for s in recent_snapshots])
            avg_efficiency = statistics.mean([s.cost_efficiency_score for s in recent_snapshots])
            avg_response_time = statistics.mean([s.avg_response_time for s in recent_snapshots])
            
            # Cache optimization
            if avg_cache_hit_rate < 0.7:
                recommendations.append({
                    'type': 'cache_optimization',
                    'priority': 'high',
                    'title': 'Improve Cache Hit Rate',
                    'description': f'Current cache hit rate is {avg_cache_hit_rate:.1%}. Consider increasing cache TTL for stable data.',
                    'impact': 'Reduce API calls by 20-30%'
                })
            
            # Batch usage optimization
            if avg_batch_usage < 0.8:
                recommendations.append({
                    'type': 'batch_optimization',
                    'priority': 'medium',
                    'title': 'Increase Batch Usage',
                    'description': f'Only {avg_batch_usage:.1%} of operations use batching. Review token discovery patterns.',
                    'impact': 'Reduce API calls by 40-60%'
                })
            
            # Response time optimization
            if avg_response_time > 15.0:
                recommendations.append({
                    'type': 'performance_optimization',
                    'priority': 'medium',
                    'title': 'Optimize Response Times',
                    'description': f'Average response time is {avg_response_time:.1f}s. Consider reducing batch sizes or increasing concurrency.',
                    'impact': 'Improve user experience and system throughput'
                })
            
            # Efficiency optimization
            if avg_efficiency < 0.75:
                recommendations.append({
                    'type': 'efficiency_optimization',
                    'priority': 'high',
                    'title': 'Improve Operation Efficiency',
                    'description': f'Average efficiency score is {avg_efficiency:.1%}. Review error handling and retry logic.',
                    'impact': 'Reduce costs by 15-25%'
                })
        
        return recommendations

    async def export_performance_data(self, filepath: Optional[str] = None) -> str:
        """Export performance data to JSON file."""
        if filepath is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filepath = self.data_dir / f"performance_export_{timestamp}.json"
        
        export_data = {
            'export_timestamp': time.time(),
            'session_metrics': self.session_metrics,
            'operation_history': [asdict(op) for op in self.operation_history],
            'performance_snapshots': [asdict(s) for s in self.performance_snapshots],
            'thresholds': self.thresholds,
            'summary': self.get_performance_summary(24),  # Last 24 hours
            'recommendations': self.get_optimization_recommendations()
        }
        
        with open(filepath, 'w') as f:
            json.dump(export_data, f, indent=2)
        
        self.logger.info(f"Performance data exported to {filepath}")
        return str(filepath)

    async def cleanup(self):
        """Clean up monitoring resources."""
        if self._monitoring_task and not self._monitoring_task.done():
            self._monitoring_task.cancel()
            try:
                await self._monitoring_task
            except asyncio.CancelledError:
                pass
        
        self.logger.info("Batch Performance Monitor cleanup complete") 