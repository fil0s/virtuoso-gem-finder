import logging
import time
from typing import Dict, List, Any, Optional
from utils.structured_logger import get_structured_logger

class PerformanceAnalyzer:
    """
    Service for tracking and analyzing performance metrics of the monitoring system.
    Collects data on API calls, processing times, and resource usage.
    """
    
    def __init__(self, logger=None):
        self.logger = logger or logging.getLogger('PerformanceAnalyzer')
        self.structured_logger = get_structured_logger('PerformanceAnalyzer')
        self.start_time = time.time()
        self.api_calls = 0
        self.successful_api_calls = 0
        self.failed_api_calls = 0
        self.total_api_latency = 0
        self.max_api_latency = 0
        self.discovery_runs = 0
        self.tokens_discovered = 0
        self.tokens_analyzed = 0
        self.alerts_sent = 0
        self.processing_times = {}
        self.strategy_executions = {}
        
        # Token tracking
        self.discovered_tokens = []
        self.promising_tokens = []
        self.threshold_adjustments = []
        
    def add_tokens_from_scan(self, tokens: List[Dict[str, Any]], scan_number: int, scan_id: Optional[str] = None):
        """
        Track tokens discovered in a scan for performance analysis
        
        Args:
            tokens: List of token data dictionaries
            scan_number: The sequential scan number
            scan_id: The ID of the scan
        """
        if not tokens:
            return
            
        # Track basic token info for reporting
        self.promising_tokens.extend([{
            'symbol': token.get('symbol', 'Unknown'),
            'name': token.get('name', 'Unknown'),
            'address': token.get('address', ''),
            'score': token.get('token_score', 0),
            'discovery_scan': scan_number,
            'timestamp': time.time()
        } for token in tokens])
        
        # Update discovery metrics
        self.tokens_analyzed += len(tokens)
        
        # Log summary
        self.structured_logger.info({
            "event": "tokens_from_scan",
            "scan_id": scan_id,
            "scan_number": scan_number,
            "token_count": len(tokens) if tokens else 0,
            "timestamp": int(time.time())
        })
        
    def add_threshold_adjustment(self, stage: str, original: float, adjusted: float, tokens_before: int, tokens_after: int, scan_id: Optional[str] = None):
        """
        Track dynamic threshold adjustments for performance analysis
        
        Args:
            stage: The filtering stage (quick, medium, full)
            original: Original threshold value
            adjusted: Adjusted threshold value
            tokens_before: Token count before adjustment
            tokens_after: Token count after adjustment
            scan_id: The ID of the scan
        """
        self.threshold_adjustments.append({
            'stage': stage,
            'original_threshold': original,
            'adjusted_threshold': adjusted,
            'tokens_before': tokens_before,
            'tokens_after': tokens_after,
            'timestamp': time.time()
        })
        
        self.structured_logger.info({
            "event": "threshold_adjustment",
            "scan_id": scan_id,
            "stage": stage,
            "original": original,
            "adjusted": adjusted,
            "tokens_before": tokens_before,
            "tokens_after": tokens_after,
            "timestamp": int(time.time())
        })
        
    def log_api_call(self, endpoint: str, success: bool, latency: float, scan_id: Optional[str] = None):
        """
        Log API call metrics
        
        Args:
            endpoint: API endpoint called
            success: Whether call was successful
            latency: Time taken for call in seconds
            scan_id: The ID of the scan
        """
        self.api_calls += 1
        if success:
            self.successful_api_calls += 1
        else:
            self.failed_api_calls += 1
        
        self.total_api_latency += latency
        self.max_api_latency = max(self.max_api_latency, latency)
        
        self.structured_logger.info({
            "event": "api_call",
            "scan_id": scan_id,
            "endpoint": endpoint,
            "success": success,
            "latency": latency,
            "timestamp": int(time.time())
        })
        
    def get_performance_metrics(self) -> Dict[str, Any]:
        """
        Get summary of all performance metrics
        
        Returns:
            Dictionary with performance metrics
        """
        runtime = time.time() - self.start_time
        
        return {
            'runtime_seconds': runtime,
            'api_calls': {
                'total': self.api_calls,
                'successful': self.successful_api_calls,
                'failed': self.failed_api_calls,
                'success_rate': self.successful_api_calls / max(1, self.api_calls),
                'avg_latency': self.total_api_latency / max(1, self.api_calls),
                'max_latency': self.max_api_latency
            },
            'discovery': {
                'runs': self.discovery_runs,
                'tokens_discovered': self.tokens_discovered,
                'tokens_analyzed': self.tokens_analyzed,
                'promising_tokens': len(self.promising_tokens)
            },
            'alerts_sent': self.alerts_sent,
            'processing_times': self.processing_times,
            'strategy_executions': self.strategy_executions
        }
        
    def log_discovery_run(self, tokens_discovered: int, runtime: float, scan_id: Optional[str] = None):
        """
        Log metrics from a discovery run
        
        Args:
            tokens_discovered: Number of tokens discovered
            runtime: Time taken for discovery in seconds
            scan_id: The ID of the scan
        """
        self.discovery_runs += 1
        self.tokens_discovered += tokens_discovered
        self.processing_times[f'discovery_run_{self.discovery_runs}'] = runtime
        
        self.structured_logger.info({
            "event": "discovery_run",
            "scan_id": scan_id,
            "tokens_discovered": tokens_discovered,
            "runtime": runtime,
            "timestamp": int(time.time())
        })
        
    def log_strategy_execution(self, strategy_name: str, tokens_found: int, runtime: float, success: bool, scan_id: Optional[str] = None):
        """
        Log metrics from a strategy execution
        
        Args:
            strategy_name: Name of the executed strategy
            tokens_found: Number of tokens found by strategy
            runtime: Time taken for execution in seconds
            success: Whether execution was successful
            scan_id: The ID of the scan
        """
        if strategy_name not in self.strategy_executions:
            self.strategy_executions[strategy_name] = {
                'executions': 0,
                'success_count': 0,
                'failure_count': 0,
                'tokens_found': 0,
                'total_runtime': 0,
                'avg_runtime': 0
            }
            
        stats = self.strategy_executions[strategy_name]
        stats['executions'] += 1
        if success:
            stats['success_count'] += 1
        else:
            stats['failure_count'] += 1
            
        stats['tokens_found'] += tokens_found
        stats['total_runtime'] += runtime
        stats['avg_runtime'] = stats['total_runtime'] / stats['executions']
        
        self.structured_logger.info({
            "event": "strategy_execution",
            "scan_id": scan_id,
            "strategy": strategy_name,
            "tokens_found": tokens_found,
            "runtime": runtime,
            "success": success,
            "timestamp": int(time.time())
        })
        
    def record_api_call(self, endpoint: str, success: bool, latency: float):
        """Record API call metrics"""
        self.api_calls += 1
        if success:
            self.successful_api_calls += 1
        else:
            self.failed_api_calls += 1
        
        self.total_api_latency += latency
        self.max_api_latency = max(self.max_api_latency, latency)
        
        # Store metrics for this time period
        self._record_current_metrics()
        
    def start_operation(self, operation_name: str) -> float:
        """Start timing an operation"""
        return time.time()
        
    def end_operation(self, operation_name: str, start_time: float):
        """End timing an operation and record duration"""
        duration = time.time() - start_time
        
        if operation_name not in self.processing_times:
            self.processing_times[operation_name] = []
            
        self.processing_times[operation_name].append(duration)
        return duration
        
    def record_discovery_run(self, tokens_found: int):
        """Record metrics for a token discovery run"""
        self.discovery_runs += 1
        self.tokens_discovered += tokens_found
        
    def record_token_analysis(self, count: int):
        """Record number of tokens analyzed"""
        self.tokens_analyzed += count
        
    def record_alert_sent(self):
        """Record alert sent"""
        self.alerts_sent += 1
        
    def _record_current_metrics(self):
        """Store current metrics in history"""
        current_metrics = {
            'timestamp': time.time(),
            'uptime': time.time() - self.start_time,
            'api_calls': self.api_calls,
            'success_rate': self.successful_api_calls / max(1, self.api_calls),
            'avg_latency': self.total_api_latency / max(1, self.api_calls),
            'max_latency': self.max_api_latency,
            'discovery_runs': self.discovery_runs,
            'tokens_discovered': self.tokens_discovered,
            'tokens_analyzed': self.tokens_analyzed,
            'alerts_sent': self.alerts_sent
        }
        self.metrics_history.append(current_metrics)
        
        # Limit history size
        if len(self.metrics_history) > 1000:
            self.metrics_history = self.metrics_history[-1000:]
            
    def get_performance_summary(self) -> Dict[str, Any]:
        """Get performance summary statistics"""
        uptime_seconds = time.time() - self.start_time
        uptime_hours = uptime_seconds / 3600
        
        avg_api_latency = self.total_api_latency / max(1, self.api_calls)
        success_rate = self.successful_api_calls / max(1, self.api_calls) * 100
        
        # Calculate average operation times
        avg_operation_times = {}
        for op_name, times in self.processing_times.items():
            if times:
                avg_operation_times[op_name] = sum(times) / len(times)
                
        return {
            'uptime_seconds': uptime_seconds,
            'uptime_hours': uptime_hours,
            'api_calls': {
                'total': self.api_calls,
                'successful': self.successful_api_calls,
                'failed': self.failed_api_calls,
                'success_rate': success_rate,
                'avg_latency': avg_api_latency,
                'max_latency': self.max_api_latency
            },
            'discovery': {
                'runs': self.discovery_runs,
                'tokens_discovered': self.tokens_discovered,
                'tokens_analyzed': self.tokens_analyzed,
                'alerts_sent': self.alerts_sent
            },
            'processing_times': avg_operation_times
        }
    
    def log_performance_summary(self, scan_id: Optional[str] = None):
        """Log performance summary to logger"""
        summary = self.get_performance_summary()
        
        self.structured_logger.info({
            "event": "performance_summary",
            "scan_id": scan_id,
            "metrics": summary,
            "timestamp": int(time.time())
        })
        
        self.logger.info(f"===== PERFORMANCE SUMMARY =====")
        self.logger.info(f"Uptime: {summary['uptime_hours']:.2f} hours")
        self.logger.info(f"API Calls: {summary['api_calls']['total']} (Success rate: {summary['api_calls']['success_rate']:.1f}%)")
        self.logger.info(f"Avg API Latency: {summary['api_calls']['avg_latency']:.2f}s, Max: {summary['api_calls']['max_latency']:.2f}s")
        self.logger.info(f"Discovery runs: {summary['discovery']['runs']}")
        self.logger.info(f"Tokens discovered: {summary['discovery']['tokens_discovered']}")
        self.logger.info(f"Tokens analyzed: {summary['discovery']['tokens_analyzed']}")
        self.logger.info(f"Alerts sent: {summary['discovery']['alerts_sent']}")
        
        if summary['processing_times']:
            self.logger.info("Average processing times:")
            for op_name, avg_time in summary['processing_times'].items():
                self.logger.info(f"  - {op_name}: {avg_time:.2f}s") 