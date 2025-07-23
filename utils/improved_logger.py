"""
Improved Logging System for Virtuoso Gem Hunter

Provides cleaner, more actionable logging with reduced verbosity and better structure.
"""

import logging
import json
from typing import Dict, Any, Optional, List
from datetime import datetime
from contextlib import contextmanager
import time
from collections import defaultdict

class APICallBatcher:
    """Batches API call logs to reduce verbosity"""
    
    def __init__(self, flush_interval: int = 30, max_batch_size: int = 50):
        self.flush_interval = flush_interval
        self.max_batch_size = max_batch_size
        self.batches = defaultdict(list)
        self.last_flush = time.time()
        
    def add_call(self, endpoint: str, status: str, response_time: float, address: Optional[str] = None):
        """Add API call to batch"""
        call_data = {
            'timestamp': datetime.now().isoformat(),
            'status': status,
            'response_time_ms': response_time,
        }
        if address:
            call_data['address'] = address
            
        self.batches[endpoint].append(call_data)
        
        # Flush if batch is full or time interval reached
        if (len(self.batches[endpoint]) >= self.max_batch_size or 
            time.time() - self.last_flush > self.flush_interval):
            return self.flush_batch(endpoint)
        return None
        
    def flush_batch(self, endpoint: str) -> Dict[str, Any]:
        """Flush batch and return summary"""
        if endpoint not in self.batches or not self.batches[endpoint]:
            return None
            
        calls = self.batches[endpoint]
        summary = {
            'endpoint': endpoint,
            'total_calls': len(calls),
            'successful': len([c for c in calls if c['status'] == 'success']),
            'failed': len([c for c in calls if c['status'] == 'error']),
            'avg_response_time': sum(c['response_time_ms'] for c in calls) / len(calls),
            'time_range': {
                'start': calls[0]['timestamp'],
                'end': calls[-1]['timestamp']
            }
        }
        
        # Clear the batch
        self.batches[endpoint] = []
        self.last_flush = time.time()
        
        return summary
        
    def flush_all(self) -> List[Dict[str, Any]]:
        """Flush all batches"""
        summaries = []
        for endpoint in list(self.batches.keys()):
            summary = self.flush_batch(endpoint)
            if summary:
                summaries.append(summary)
        return summaries

class ProgressTracker:
    """Tracks and displays progress for long-running operations"""
    
    def __init__(self, total_items: int, operation_name: str):
        self.total_items = total_items
        self.operation_name = operation_name
        self.processed = 0
        self.start_time = time.time()
        self.last_update = 0
        
    def update(self, increment: int = 1) -> Optional[str]:
        """Update progress and return status if significant progress made"""
        self.processed += increment
        current_time = time.time()
        
        # Only return status every 10% progress or 10 seconds
        progress_pct = (self.processed / self.total_items) * 100
        if (progress_pct >= self.last_update + 10 or 
            current_time - self.start_time > self.last_update + 10):
            
            elapsed = current_time - self.start_time
            rate = self.processed / elapsed if elapsed > 0 else 0
            eta = (self.total_items - self.processed) / rate if rate > 0 else 0
            
            self.last_update = progress_pct
            
            return {
                'operation': self.operation_name,
                'progress': f"{self.processed}/{self.total_items} ({progress_pct:.1f}%)",
                'rate': f"{rate:.1f} items/sec",
                'eta_seconds': int(eta)
            }
        return None

class ImprovedLogger:
    """Improved logger with batching and progress tracking"""
    
    def __init__(self, name: str = "VirtuosoGemHunter", enable_batching: bool = True):
        self.logger = logging.getLogger(name)
        self.enable_batching = enable_batching
        self.api_batcher = APICallBatcher() if enable_batching else None
        self.progress_trackers = {}
        
        # Setup if not already done
        if not self.logger.handlers:
            self._setup_logger()
    
    def _setup_logger(self):
        """Setup logger with improved formatting"""
        # Console handler with clean format
        console_handler = logging.StreamHandler()
        console_handler.setLevel(logging.INFO)
        
        # Clean format for console - includes filename for debugging
        console_format = (
            "%(asctime)s | %(levelname)-7s | %(filename)-25s | %(message)s"
        )
        console_handler.setFormatter(logging.Formatter(console_format, datefmt='%H:%M:%S'))
        self.logger.addHandler(console_handler)
        
        # File handler with detailed format (optional)
        try:
            file_handler = logging.FileHandler("logs/detailed.log")
            file_handler.setLevel(logging.DEBUG)
            file_format = (
                "%(asctime)s | %(levelname)-7s | %(filename)-25s | %(funcName)-20s | L%(lineno)-5d | %(message)s"
            )
            file_handler.setFormatter(logging.Formatter(file_format))
            self.logger.addHandler(file_handler)
        except:
            pass  # Skip file logging if directory doesn't exist
            
        self.logger.setLevel(logging.DEBUG)
    
    def log_api_call(self, endpoint: str, status: str, response_time: float, 
                     address: Optional[str] = None, details: Optional[Dict] = None):
        """Log API call with batching"""
        if self.enable_batching and self.api_batcher:
            summary = self.api_batcher.add_call(endpoint, status, response_time, address)
            if summary:
                self._log_api_batch_summary(summary)
        else:
            # Individual logging (fallback)
            self.debug(f"API {endpoint}: {status} ({response_time:.0f}ms) {address or ''}")
    
    def _log_api_batch_summary(self, summary: Dict[str, Any]):
        """Log API batch summary"""
        endpoint = summary['endpoint']
        total = summary['total_calls']
        success = summary['successful'] 
        failed = summary['failed']
        avg_time = summary['avg_response_time']
        
        if failed > 0:
            self.warning(f"📡 {endpoint}: {success}/{total} successful, {failed} failed (avg: {avg_time:.0f}ms)")
        else:
            self.info(f"📡 {endpoint}: {total} calls completed (avg: {avg_time:.0f}ms)")
    
    def start_progress(self, operation_id: str, total_items: int, operation_name: str):
        """Start tracking progress for an operation"""
        self.progress_trackers[operation_id] = ProgressTracker(total_items, operation_name)
        self.info(f"🚀 Starting {operation_name}: {total_items} items to process")
    
    def update_progress(self, operation_id: str, increment: int = 1):
        """Update progress for an operation"""
        if operation_id in self.progress_trackers:
            status = self.progress_trackers[operation_id].update(increment)
            if status:
                self.info(f"⚡ {status['operation']}: {status['progress']} | {status['rate']} | ETA: {status['eta_seconds']}s")
    
    def finish_progress(self, operation_id: str):
        """Finish progress tracking"""
        if operation_id in self.progress_trackers:
            tracker = self.progress_trackers.pop(operation_id)
            elapsed = time.time() - tracker.start_time
            rate = tracker.processed / elapsed if elapsed > 0 else 0
            self.info(f"✅ {tracker.operation_name} completed: {tracker.processed} items in {elapsed:.1f}s ({rate:.1f} items/sec)")
    
    def log_rate_limit(self, service: str, reset_time: Optional[int] = None):
        """Log rate limit in a structured way"""
        if reset_time:
            self.warning(f"⏳ Rate limit reached for {service} (reset: {reset_time})")
        else:
            self.warning(f"⏳ Rate limit reached for {service}")
    
    def log_cycle_summary(self, cycle_num: int, total_cycles: int, results: Dict[str, Any]):
        """Log cycle completion summary"""
        duration = results.get('cycle_time', 0)
        analyzed = results.get('total_analyzed', 0)
        high_conviction = results.get('high_conviction_count', 0)
        
        self.info(f"📊 Cycle {cycle_num}/{total_cycles}: {analyzed} analyzed, {high_conviction} high conviction ({duration:.1f}s)")
    
    def log_session_stats(self, stats: Dict[str, Any]):
        """Log session statistics"""
        cycles = stats.get('cycles_completed', 0)
        tokens = stats.get('tokens_analyzed', 0)
        alerts = stats.get('alerts_sent', 0)
        
        api_stats = []
        for service, data in stats.get('api_usage_by_service', {}).items():
            calls = data.get('total_calls', 0)
            success_rate = data.get('successful_calls', 0) / calls * 100 if calls > 0 else 0
            api_stats.append(f"{service}: {calls} calls ({success_rate:.1f}% success)")
        
        self.info(f"📈 Session: {cycles} cycles, {tokens} tokens, {alerts} alerts | " + " | ".join(api_stats))
    
    def debug(self, msg: str, **kwargs):
        """Debug level logging"""
        self.logger.debug(msg, extra=kwargs)
    
    def info(self, msg: str, **kwargs):
        """Info level logging"""
        self.logger.info(msg, extra=kwargs)
    
    def warning(self, msg: str, **kwargs):
        """Warning level logging"""
        self.logger.warning(msg, extra=kwargs)
    
    def error(self, msg: str, exc_info=None, **kwargs):
        """Error level logging"""
        self.logger.error(msg, exc_info=exc_info, extra=kwargs)
    
    def flush_batches(self):
        """Manually flush all API call batches"""
        if self.api_batcher:
            summaries = self.api_batcher.flush_all()
            for summary in summaries:
                self._log_api_batch_summary(summary)

    @contextmanager
    def operation_context(self, operation_name: str, **context):
        """Context manager for operation logging"""
        operation_id = f"{operation_name}_{int(time.time())}"
        start_time = time.time()
        
        self.info(f"🔄 Starting {operation_name}")
        try:
            yield operation_id
            duration = time.time() - start_time
            self.info(f"✅ {operation_name} completed in {duration:.2f}s")
        except Exception as e:
            duration = time.time() - start_time
            self.error(f"❌ {operation_name} failed after {duration:.2f}s: {str(e)}", exc_info=True)
            raise

# Global instance
improved_logger = ImprovedLogger()