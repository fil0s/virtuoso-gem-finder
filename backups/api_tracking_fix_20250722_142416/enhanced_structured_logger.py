#!/usr/bin/env python3
"""
Enhanced Structured Logging System with structlog
Comprehensive debugging and performance tracking for the gem detection system
"""

import structlog
import logging
import time
import uuid
import asyncio
from typing import Dict, Any, Optional, List
from contextlib import contextmanager
from dataclasses import dataclass, field
from enum import Enum
import json
from datetime import datetime


class DetectionStage(Enum):
    """Detection stages for tracking progress"""
    INITIALIZATION = "initialization"
    STAGE_0_DISCOVERY = "stage_0_discovery"
    STAGE_1_BASIC_FILTER = "stage_1_basic_filter"
    STAGE_2_BATCH_ENRICHMENT = "stage_2_batch_enrichment"
    STAGE_3_DETAILED_ANALYSIS = "stage_3_detailed_analysis"
    STAGE_4_FINAL_SCORING = "stage_4_final_scoring"
    ANALYSIS = "analysis"
    ALERT_PROCESSING = "alert_processing"
    ERROR_HANDLING = "error_handling"


class APICallType(Enum):
    """Types of API calls for tracking"""
    TOKEN_DISCOVERY = "token_discovery"
    BATCH_METADATA = "batch_metadata"
    BATCH_PRICE = "batch_price"
    INDIVIDUAL_METADATA = "individual_metadata"
    INDIVIDUAL_PRICE = "individual_price"
    VALIDATION = "validation"
    CACHE_OPERATION = "cache_operation"


@dataclass
class PerformanceMetrics:
    """Track performance metrics across stages"""
    stage_start_times: Dict[str, float] = field(default_factory=dict)
    stage_durations: Dict[str, float] = field(default_factory=dict)
    api_call_counts: Dict[str, int] = field(default_factory=dict)
    api_call_durations: Dict[str, List[float]] = field(default_factory=dict)
    tokens_processed: Dict[str, int] = field(default_factory=dict)
    errors_by_stage: Dict[str, int] = field(default_factory=dict)
    cache_hits: int = 0
    cache_misses: int = 0
    validation_stats: Dict[str, int] = field(default_factory=dict)


class EnhancedStructuredLogger:
    """Enhanced structured logger with comprehensive debugging capabilities"""
    
    def __init__(self, 
                 name: str = "VirtuosoGemHunter",
                 log_level: str = "INFO",
                 enable_performance_tracking: bool = True,
                 enable_api_tracking: bool = True,
                 enable_context_tracking: bool = True):
        
        self.name = name
        self.enable_performance_tracking = enable_performance_tracking
        self.enable_api_tracking = enable_api_tracking
        self.enable_context_tracking = enable_context_tracking
        
        # Configure structlog
        self._configure_structlog(log_level)
        
        # Initialize structured logger
        self.logger = structlog.get_logger(name)
        
        # Performance tracking
        self.performance_metrics = PerformanceMetrics()
        self.current_scan_context = {}
        
        # Context stack for nested operations
        self.context_stack = []
        
        self.logger.info("Enhanced structured logger initialized", 
                        logger_name=name,
                        performance_tracking=enable_performance_tracking,
                        api_tracking=enable_api_tracking,
                        context_tracking=enable_context_tracking)
    
    def _configure_structlog(self, log_level: str):
        """Configure structlog with comprehensive processors"""
        
        # Custom timestamp processor
        def add_timestamp(logger, method_name, event_dict):
            event_dict["timestamp"] = datetime.utcnow().isoformat()
            return event_dict
        
        # Performance metrics processor
        def add_performance_context(logger, method_name, event_dict):
            if hasattr(self, 'current_scan_context') and self.current_scan_context:
                # Add context but avoid 'event' key conflicts
                context = {k: v for k, v in self.current_scan_context.items() if k != 'event'}
                event_dict.update(context)
            
            # Add context stack but avoid key conflicts
            if hasattr(self, 'context_stack') and self.context_stack:
                stack_context = {k: v for k, v in self.context_stack[-1].items() if k not in ['event', 'log_event']}
                event_dict.update(stack_context)
            
            return event_dict
        
        # Configure processors
        processors = [
            structlog.contextvars.merge_contextvars,
            add_timestamp,
            structlog.stdlib.add_log_level,
            structlog.stdlib.PositionalArgumentsFormatter(),
            structlog.processors.StackInfoRenderer(),
            structlog.processors.format_exc_info,
            structlog.processors.UnicodeDecoder(),
            add_performance_context,
            structlog.processors.JSONRenderer()
        ]
        
        structlog.configure(
            processors=processors,
            wrapper_class=structlog.stdlib.BoundLogger,
            logger_factory=structlog.stdlib.LoggerFactory(),
            cache_logger_on_first_use=True,
        )
        
        # Set logging level
        logging.basicConfig(
            format="%(message)s",
            level=getattr(logging, log_level.upper())
        )
    
    def new_scan_context(self, 
                        scan_id: Optional[str] = None,
                        strategy: Optional[str] = None,
                        timeframe: Optional[str] = None) -> str:
        """Create a new scan context for tracking"""
        if not scan_id:
            scan_id = f"scan_{uuid.uuid4().hex[:8]}"
        
        self.current_scan_context = {
            "scan_id": scan_id,
            "strategy": strategy or "unknown",
            "timeframe": timeframe or "unknown",
            "scan_start_time": time.time(),
            "scan_timestamp": datetime.utcnow().isoformat()
        }
        
        # Reset performance metrics for new scan
        self.performance_metrics = PerformanceMetrics()
        
        self.logger.info("New scan context created",
                        scan_id=scan_id,
                        strategy=strategy,
                        timeframe=timeframe)
        
        return scan_id
    
    @contextmanager
    def stage_context(self, stage: DetectionStage, **extra_context):
        """Context manager for tracking detection stages"""
        stage_name = stage.value
        stage_id = f"{stage_name}_{uuid.uuid4().hex[:6]}"
        
        # Start stage tracking
        start_time = time.time()
        if self.enable_performance_tracking:
            self.performance_metrics.stage_start_times[stage_name] = start_time
        
        # Add stage context
        stage_context = {
            "stage": stage_name,
            "stage_id": stage_id,
            "stage_start": datetime.utcnow().isoformat(),
            **extra_context
        }
        
        # Push context to stack
        if self.enable_context_tracking:
            self.context_stack.append(stage_context)
        
        stage_context["log_event"] = "stage_start"
        self.logger.info("Stage started", **stage_context)
        
        try:
            yield stage_id
        except Exception as e:
            # Track errors by stage
            if self.enable_performance_tracking:
                self.performance_metrics.errors_by_stage[stage_name] = \
                    self.performance_metrics.errors_by_stage.get(stage_name, 0) + 1
            
            error_context = stage_context.copy()
            error_context.update({
                "error": str(e),
                "error_type": type(e).__name__,
                "log_event": "stage_error"
            })
            self.logger.error("Stage failed", **error_context)
            raise
        finally:
            # End stage tracking
            end_time = time.time()
            duration = end_time - start_time
            
            if self.enable_performance_tracking:
                self.performance_metrics.stage_durations[stage_name] = duration
            
            # Pop context from stack
            if self.enable_context_tracking and self.context_stack:
                self.context_stack.pop()
            
            complete_context = stage_context.copy()
            complete_context.update({
                "duration_ms": round(duration * 1000, 2),
                "log_event": "stage_complete"
            })
            self.logger.info("Stage completed", **complete_context)
    
    @contextmanager
    def api_call_context(self, 
                        call_type: APICallType, 
                        endpoint: str,
                        token_count: Optional[int] = None,
                        **extra_context):
        """Context manager for tracking API calls"""
        call_type_name = call_type.value
        call_id = f"api_{uuid.uuid4().hex[:6]}"
        
        start_time = time.time()
        
        api_context = {
            "api_call_type": call_type_name,
            "api_endpoint": endpoint,
            "api_call_id": call_id,
            "api_start": datetime.utcnow().isoformat(),
            **extra_context
        }
        
        if token_count is not None:
            api_context["token_count"] = token_count
        
        api_context["log_event"] = "api_start"
        self.logger.debug("API call started", **api_context)
        
        try:
            yield call_id
        except Exception as e:
            error_context = api_context.copy()
            error_context.update({
                "error": str(e),
                "error_type": type(e).__name__,
                "log_event": "api_error"
            })
            self.logger.error("API call failed", **error_context)
            raise
        finally:
            end_time = time.time()
            duration = end_time - start_time
            
            # Track API performance
            if self.enable_api_tracking:
                self.performance_metrics.api_call_counts[call_type_name] = \
                    self.performance_metrics.api_call_counts.get(call_type_name, 0) + 1
                
                if call_type_name not in self.performance_metrics.api_call_durations:
                    self.performance_metrics.api_call_durations[call_type_name] = []
                self.performance_metrics.api_call_durations[call_type_name].append(duration)
            
            complete_context = api_context.copy()
            complete_context.update({
                "duration_ms": round(duration * 1000, 2),
                "success": True,
                "log_event": "api_complete"
            })
            self.logger.info("API call completed", **complete_context)
    
    def log_token_processing(self, 
                           stage: DetectionStage,
                           tokens_input: int,
                           tokens_output: int,
                           tokens_filtered: Optional[int] = None,
                           filter_reasons: Optional[Dict[str, int]] = None,
                           **extra_context):
        """Log token processing statistics"""
        stage_name = stage.value
        
        # Update performance metrics
        if self.enable_performance_tracking:
            self.performance_metrics.tokens_processed[f"{stage_name}_input"] = tokens_input
            self.performance_metrics.tokens_processed[f"{stage_name}_output"] = tokens_output
        
        log_data = {
            "stage": stage_name,
            "tokens_input": tokens_input,
            "tokens_output": tokens_output,
            "processing_efficiency": round((tokens_output / max(tokens_input, 1)) * 100, 2),
            **extra_context
        }
        log_data["log_event"] = "token_processing"
        
        if tokens_filtered is not None:
            log_data["tokens_filtered"] = tokens_filtered
            log_data["filter_rate"] = round((tokens_filtered / max(tokens_input, 1)) * 100, 2)
        
        if filter_reasons:
            log_data["filter_reasons"] = filter_reasons
        
        self.logger.info("Token processing stats", **log_data)
    
    def log_validation_stats(self, 
                           validation_report: Dict[str, Any],
                           **extra_context):
        """Log token validation statistics"""
        # Update performance metrics
        if self.enable_performance_tracking:
            for key, value in validation_report.items():
                if isinstance(value, (int, float)):
                    self.performance_metrics.validation_stats[key] = value
        
        log_data = validation_report.copy()
        log_data.update(extra_context)
        log_data["log_event"] = "validation_stats"
        self.logger.info("Validation statistics", **log_data)
    
    def log_cache_operation(self, 
                          operation: str,
                          cache_key: str,
                          hit: bool,
                          ttl: Optional[int] = None,
                          **extra_context):
        """Log cache operations"""
        # Update performance metrics
        if self.enable_performance_tracking:
            if hit:
                self.performance_metrics.cache_hits += 1
            else:
                self.performance_metrics.cache_misses += 1
        
        log_data = {
            "cache_operation": operation,
            "cache_key": cache_key,
            "cache_hit": hit,
            **extra_context
        }
        log_data["log_event"] = "cache_operation"
        
        if ttl is not None:
            log_data["cache_ttl"] = ttl
        
        self.logger.debug("Cache operation", **log_data)
    
    def log_performance_summary(self, **extra_context):
        """Log comprehensive performance summary"""
        if not self.enable_performance_tracking:
            return
        
        metrics = self.performance_metrics
        
        # Calculate summary statistics
        total_scan_duration = 0
        if self.current_scan_context.get("scan_start_time"):
            total_scan_duration = time.time() - self.current_scan_context["scan_start_time"]
        
        # API call statistics
        total_api_calls = sum(metrics.api_call_counts.values())
        api_avg_durations = {}
        for call_type, durations in metrics.api_call_durations.items():
            if durations:
                api_avg_durations[f"{call_type}_avg_ms"] = round(sum(durations) / len(durations) * 1000, 2)
        
        # Cache efficiency
        total_cache_operations = metrics.cache_hits + metrics.cache_misses
        cache_hit_rate = 0
        if total_cache_operations > 0:
            cache_hit_rate = round((metrics.cache_hits / total_cache_operations) * 100, 2)
        
        summary_data = {
            "total_scan_duration_ms": round(total_scan_duration * 1000, 2),
            "stage_durations": {k: round(v * 1000, 2) for k, v in metrics.stage_durations.items()},
            "total_api_calls": total_api_calls,
            "api_call_counts": metrics.api_call_counts,
            "api_average_durations": api_avg_durations,
            "cache_hit_rate": cache_hit_rate,
            "cache_hits": metrics.cache_hits,
            "cache_misses": metrics.cache_misses,
            "tokens_processed": metrics.tokens_processed,
            "errors_by_stage": metrics.errors_by_stage,
            "validation_stats": metrics.validation_stats,
            **extra_context
        }
        summary_data["log_event"] = "performance_summary"
        
        self.logger.info("Performance summary", **summary_data)
    
    def log_alert(self, 
                  alert_type: str,
                  token_address: str,
                  confidence_score: float,
                  alert_data: Dict[str, Any],
                  **extra_context):
        """Log alert generation"""
        alert_data_log = {
            "alert_type": alert_type,
            "token_address": token_address,
            "confidence_score": confidence_score,
            "alert_timestamp": datetime.utcnow().isoformat(),
            **alert_data,
            **extra_context
        }
        alert_data_log["log_event"] = "alert_generated"
        
        self.logger.info("Alert generated", **alert_data_log)
    
    def get_current_context(self) -> Dict[str, Any]:
        """Get current logging context"""
        context = {}
        context.update(self.current_scan_context)
        
        if self.context_stack:
            context.update(self.context_stack[-1])
        
        return context
    
    def debug(self, message: str, **kwargs):
        """Debug level logging"""
        self.logger.debug(message, **kwargs)
    
    def info(self, message: str, **kwargs):
        """Info level logging"""
        self.logger.info(message, **kwargs)
    
    def warning(self, message: str, **kwargs):
        """Warning level logging"""
        self.logger.warning(message, **kwargs)
    
    def error(self, message: str, **kwargs):
        """Error level logging"""
        self.logger.error(message, **kwargs)


# Factory functions for easy initialization
def create_enhanced_logger(name: str = "VirtuosoGemHunter",
                          log_level: str = "INFO",
                          **kwargs) -> EnhancedStructuredLogger:
    """Create and return a configured enhanced structured logger"""
    return EnhancedStructuredLogger(name=name, log_level=log_level, **kwargs)


def get_enhanced_logger(name: str = "VirtuosoGemHunter") -> EnhancedStructuredLogger:
    """Get or create an enhanced structured logger (singleton-like behavior)"""
    # In a real implementation, you might want to implement proper singleton pattern
    return create_enhanced_logger(name=name)