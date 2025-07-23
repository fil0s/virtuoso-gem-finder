#!/usr/bin/env python3
"""
Comprehensive Strategy Comparison V4

This script runs all token discovery strategies independently and provides
comprehensive analysis of their individual and comparative performance.

Key Features:
- Independent execution of each strategy
- Comprehensive performance metrics
- Cross-strategy overlap analysis
- Quality scoring and ranking
- Detailed reporting with insights
- Token discovery effectiveness analysis
- Advanced API optimization analysis
"""

import os
import sys
import asyncio
import json
import time
import logging
import math
import traceback
import psutil
import gc
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Any, Set, Tuple, Optional
from collections import defaultdict, Counter
from functools import wraps

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from api.birdeye_connector import BirdeyeAPI
from services.logger_setup import LoggerSetup
from utils.structured_logger import get_structured_logger

# Import all strategies
from core.strategies import (
    VolumeMomentumStrategy,
    RecentListingsStrategy, 
    PriceMomentumStrategy,
    LiquidityGrowthStrategy,
    HighTradingActivityStrategy,
    SmartMoneyWhaleStrategy
)


class DebugProfiler:
    """Advanced debugging and profiling utilities for strategy comparison."""
    
    def __init__(self, logger=None, debug_mode=False):
        """Initialize the debug profiler."""
        self.logger = logger or logging.getLogger(__name__)
        self.debug_mode = debug_mode
        self.performance_stats = {}
        self.memory_snapshots = []
        self.api_call_traces = []
        self.debug_session_id = f"debug_{int(time.time())}"
        self.phase_timings = {}
        self.token_analysis_details = {}
        self.error_context_stack = []
        
        # Create debug output directory
        self.debug_dir = Path("debug") / f"session_{self.debug_session_id}"
        self.debug_dir.mkdir(parents=True, exist_ok=True)
        
        if self.debug_mode:
            self.logger.info(f"🐛 Debug Profiler initialized - Session ID: {self.debug_session_id}")
            self.logger.info(f"📁 Debug files will be saved to: {self.debug_dir}")
    
    def debug_decorator(self, func_name: str = None):
        """Decorator for comprehensive function debugging."""
        def decorator(func):
            @wraps(func)
            async def async_wrapper(*args, **kwargs):
                return await self._trace_function(func, func_name or func.__name__, args, kwargs, is_async=True)
            
            @wraps(func)
            def sync_wrapper(*args, **kwargs):
                return self._trace_function_sync(func, func_name or func.__name__, args, kwargs)
            
            return async_wrapper if asyncio.iscoroutinefunction(func) else sync_wrapper
        return decorator
    
    async def _trace_function(self, func, func_name: str, args, kwargs, is_async=True):
        """Trace async function execution with detailed debugging."""
        if not self.debug_mode:
            return await func(*args, **kwargs) if is_async else func(*args, **kwargs)
        
        start_time = time.time()
        start_memory = self._get_memory_usage()
        
        self.logger.debug(f"🚀 ENTER: {func_name} | Memory: {start_memory:.2f}MB")
        
        try:
            if is_async:
                result = await func(*args, **kwargs)
            else:
                result = func(*args, **kwargs)
            
            end_time = time.time()
            end_memory = self._get_memory_usage()
            execution_time = end_time - start_time
            memory_delta = end_memory - start_memory
            
            # Store performance stats
            self.performance_stats[func_name] = {
                'execution_time': execution_time,
                'memory_usage': end_memory,
                'memory_delta': memory_delta,
                'success': True,
                'timestamp': start_time
            }
            
            self.logger.debug(f"✅ EXIT: {func_name} | Time: {execution_time:.3f}s | Memory Δ: {memory_delta:+.2f}MB")
            
            # Log slow functions
            if execution_time > 5.0:
                self.logger.warning(f"🐌 SLOW FUNCTION: {func_name} took {execution_time:.2f}s")
            
            return result
            
        except Exception as e:
            end_time = time.time()
            execution_time = end_time - start_time
            
            # Store error stats
            self.performance_stats[func_name] = {
                'execution_time': execution_time,
                'memory_usage': self._get_memory_usage(),
                'success': False,
                'error': str(e),
                'timestamp': start_time
            }
            
            self.logger.error(f"❌ ERROR in {func_name}: {e}")
            self.logger.debug(f"🔍 Full traceback: {traceback.format_exc()}")
            
            # Store error context
            self._store_error_context(func_name, e, args, kwargs)
            raise
    
    def _trace_function_sync(self, func, func_name: str, args, kwargs):
        """Trace sync function execution."""
        if not self.debug_mode:
            return func(*args, **kwargs)
        
        start_time = time.time()
        start_memory = self._get_memory_usage()
        
        self.logger.debug(f"🚀 ENTER: {func_name} | Memory: {start_memory:.2f}MB")
        
        try:
            result = func(*args, **kwargs)
            
            end_time = time.time()
            end_memory = self._get_memory_usage()
            execution_time = end_time - start_time
            memory_delta = end_memory - start_memory
            
            self.performance_stats[func_name] = {
                'execution_time': execution_time,
                'memory_usage': end_memory,
                'memory_delta': memory_delta,
                'success': True,
                'timestamp': start_time
            }
            
            self.logger.debug(f"✅ EXIT: {func_name} | Time: {execution_time:.3f}s | Memory Δ: {memory_delta:+.2f}MB")
            return result
            
        except Exception as e:
            self.logger.error(f"❌ ERROR in {func_name}: {e}")
            self._store_error_context(func_name, e, args, kwargs)
            raise
    
    def start_phase(self, phase_name: str):
        """Start timing a phase."""
        if self.debug_mode:
            self.phase_timings[phase_name] = {
                'start_time': time.time(),
                'start_memory': self._get_memory_usage(),
                'start_gc_count': len(gc.get_objects())
            }
            self.logger.info(f"🎬 PHASE START: {phase_name}")
            self._take_memory_snapshot(f"phase_start_{phase_name}")
    
    def end_phase(self, phase_name: str):
        """End timing a phase."""
        if self.debug_mode and phase_name in self.phase_timings:
            start_data = self.phase_timings[phase_name]
            end_time = time.time()
            end_memory = self._get_memory_usage()
            end_gc_count = len(gc.get_objects())
            
            duration = end_time - start_data['start_time']
            memory_delta = end_memory - start_data['start_memory']
            gc_delta = end_gc_count - start_data['start_gc_count']
            
            self.phase_timings[phase_name].update({
                'duration': duration,
                'memory_delta': memory_delta,
                'gc_objects_delta': gc_delta,
                'end_time': end_time
            })
            
            self.logger.info(f"🏁 PHASE END: {phase_name} | Duration: {duration:.2f}s | Memory Δ: {memory_delta:+.2f}MB | Objects Δ: {gc_delta:+,}")
            self._take_memory_snapshot(f"phase_end_{phase_name}")
            
            # Force garbage collection after each phase
            collected = gc.collect()
            if collected > 0:
                self.logger.debug(f"🗑️ Garbage collected {collected} objects after {phase_name}")
    
    def log_api_call(self, endpoint: str, params: Dict, response_time: float, success: bool, response_size: int = 0):
        """Log detailed API call information."""
        if self.debug_mode:
            api_trace = {
                'timestamp': time.time(),
                'endpoint': endpoint,
                'params': params,
                'response_time_ms': response_time * 1000,
                'success': success,
                'response_size_bytes': response_size,
                'memory_at_call': self._get_memory_usage()
            }
            
            self.api_call_traces.append(api_trace)
            self.logger.debug(f"📡 API: {endpoint} | {response_time*1000:.1f}ms | {'✅' if success else '❌'} | {response_size:,} bytes")
    
    def log_token_analysis(self, strategy_name: str, token_address: str, analysis_data: Dict):
        """Log detailed token analysis information."""
        if self.debug_mode:
            if strategy_name not in self.token_analysis_details:
                self.token_analysis_details[strategy_name] = {}
            
            self.token_analysis_details[strategy_name][token_address] = {
                'timestamp': time.time(),
                'analysis_data': analysis_data,
                'memory_usage': self._get_memory_usage()
            }
            
            score = analysis_data.get('score', 0)
            self.logger.debug(f"🪙 TOKEN: {token_address[:8]}... | Strategy: {strategy_name} | Score: {score}")
    
    def log_strategy_progress(self, strategy_name: str, current: int, total: int, status: str = ""):
        """Log strategy execution progress."""
        if self.debug_mode:
            percentage = (current / total * 100) if total > 0 else 0
            progress_bar = self._create_progress_bar(percentage)
            
            self.logger.info(f"⏳ {strategy_name}: {progress_bar} {current}/{total} ({percentage:.1f}%) {status}")
    
    def debug_pause(self, message: str = "Debug pause"):
        """Interactive debug pause (only in debug mode)."""
        if self.debug_mode and os.getenv('INTERACTIVE_DEBUG', 'false').lower() == 'true':
            self.logger.info(f"⏸️ {message}")
            input("Press Enter to continue...")
    
    def save_debug_session(self):
        """Save comprehensive debug session data."""
        if not self.debug_mode:
            return
        
        debug_data = {
            'session_id': self.debug_session_id,
            'timestamp': time.time(),
            'performance_stats': self.performance_stats,
            'phase_timings': self.phase_timings,
            'memory_snapshots': self.memory_snapshots,
            'api_call_traces': self.api_call_traces,
            'token_analysis_details': self.token_analysis_details,
            'error_contexts': self.error_context_stack,
            'system_info': self._get_system_info()
        }
        
        # Save main debug file
        debug_file = self.debug_dir / "debug_session.json"
        with open(debug_file, 'w') as f:
            json.dump(debug_data, f, indent=2, default=str)
        
        # Save performance summary
        self._save_performance_summary()
        
        # Save API call analysis
        self._save_api_call_analysis()
        
        self.logger.info(f"💾 Debug session saved to: {debug_file}")
    
    def get_performance_summary(self) -> Dict[str, Any]:
        """Get comprehensive performance summary."""
        if not self.performance_stats:
            return {}
        
        functions = list(self.performance_stats.keys())
        total_time = sum(stat['execution_time'] for stat in self.performance_stats.values())
        
        # Find slowest functions
        slowest = sorted(self.performance_stats.items(), key=lambda x: x[1]['execution_time'], reverse=True)[:5]
        
        # Calculate memory usage
        max_memory = max(stat['memory_usage'] for stat in self.performance_stats.values())
        
        return {
            'total_functions_traced': len(functions),
            'total_execution_time': total_time,
            'max_memory_usage_mb': max_memory,
            'slowest_functions': [(name, data['execution_time']) for name, data in slowest],
            'error_count': len([s for s in self.performance_stats.values() if not s['success']]),
            'phase_summary': {name: data.get('duration', 0) for name, data in self.phase_timings.items()}
        }
    
    # Helper methods
    def _get_memory_usage(self) -> float:
        """Get current memory usage in MB."""
        try:
            process = psutil.Process()
            return process.memory_info().rss / 1024 / 1024
        except:
            return 0.0
    
    def _take_memory_snapshot(self, label: str):
        """Take a memory snapshot."""
        if self.debug_mode:
            snapshot = {
                'label': label,
                'timestamp': time.time(),
                'memory_mb': self._get_memory_usage(),
                'gc_objects': len(gc.get_objects())
            }
            self.memory_snapshots.append(snapshot)
    
    def _create_progress_bar(self, percentage: float, length: int = 20) -> str:
        """Create a text progress bar."""
        filled = int(length * percentage / 100)
        bar = '█' * filled + '░' * (length - filled)
        return f"[{bar}]"
    
    def _store_error_context(self, func_name: str, error: Exception, args: tuple, kwargs: dict):
        """Store detailed error context."""
        context = {
            'function': func_name,
            'error': str(error),
            'error_type': type(error).__name__,
            'traceback': traceback.format_exc(),
            'args_count': len(args),
            'kwargs_keys': list(kwargs.keys()),
            'timestamp': time.time(),
            'memory_usage': self._get_memory_usage()
        }
        self.error_context_stack.append(context)
    
    def _get_system_info(self) -> Dict[str, Any]:
        """Get comprehensive system information."""
        try:
            return {
                'python_version': sys.version,
                'platform': sys.platform,
                'cpu_count': psutil.cpu_count(),
                'memory_total_gb': psutil.virtual_memory().total / 1024**3,
                'memory_available_gb': psutil.virtual_memory().available / 1024**3,
                'disk_usage_gb': psutil.disk_usage('/').free / 1024**3,
                'pid': os.getpid()
            }
        except:
            return {'error': 'Could not gather system info'}
    
    def _save_performance_summary(self):
        """Save performance analysis to file."""
        summary = self.get_performance_summary()
        summary_file = self.debug_dir / "performance_summary.json"
        
        with open(summary_file, 'w') as f:
            json.dump(summary, f, indent=2, default=str)
    
    def _save_api_call_analysis(self):
        """Save API call analysis to file."""
        if not self.api_call_traces:
            return
        
        # Analyze API patterns
        endpoint_stats = defaultdict(list)
        for trace in self.api_call_traces:
            endpoint_stats[trace['endpoint']].append(trace['response_time_ms'])
        
        api_analysis = {
            'total_api_calls': len(self.api_call_traces),
            'endpoint_performance': {
                endpoint: {
                    'call_count': len(times),
                    'avg_response_time_ms': sum(times) / len(times),
                    'min_response_time_ms': min(times),
                    'max_response_time_ms': max(times)
                }
                for endpoint, times in endpoint_stats.items()
            },
            'raw_traces': self.api_call_traces
        }
        
        api_file = self.debug_dir / "api_call_analysis.json"
        with open(api_file, 'w') as f:
            json.dump(api_analysis, f, indent=2, default=str)


class APIOptimizationAnalyzer:
    """Analyze API usage patterns and optimization opportunities."""
    
    def __init__(self, logger=None):
        """Initialize the API optimization analyzer."""
        self.logger = logger or logging.getLogger(__name__)
    
    def analyze_api_optimization(self, all_strategy_metrics: Dict[str, Dict]) -> Dict[str, Any]:
        """Comprehensive API optimization analysis across all strategies."""
        
        # Aggregate metrics across all strategies
        aggregated_metrics = self._aggregate_strategy_metrics(all_strategy_metrics)
        
        return {
            "endpoint_efficiency": self._analyze_endpoint_efficiency(aggregated_metrics),
            "cost_benefit_analysis": self._calculate_cost_benefit_ratios(all_strategy_metrics),
            "cache_optimization": self._analyze_cache_optimization(aggregated_metrics),
            "rate_limiting_optimization": self._optimize_rate_limiting(aggregated_metrics),
            "api_budget_allocation": self._optimize_api_budget_allocation(all_strategy_metrics),
            "strategy_api_comparison": self._compare_api_usage_across_strategies(all_strategy_metrics),
            "optimization_recommendations": self._generate_optimization_recommendations(all_strategy_metrics, aggregated_metrics)
        }
    
    def _aggregate_strategy_metrics(self, all_strategy_metrics: Dict[str, Dict]) -> Dict[str, Any]:
        """Aggregate API metrics across all strategies."""
        
        total_api_calls = 0
        total_cache_hits = 0
        total_cache_misses = 0
        total_response_time = 0
        total_successful_calls = 0
        total_failed_calls = 0
        
        endpoint_usage = defaultdict(int)
        endpoint_response_times = defaultdict(list)
        endpoint_errors = defaultdict(int)
        endpoint_tokens = defaultdict(int)
        
        strategy_efficiency_scores = {}
        
        for strategy_name, metrics in all_strategy_metrics.items():
            api_metrics = metrics.get('api_metrics', {})
            
            # Aggregate totals
            total_api_calls += api_metrics.get('api_calls_made', 0)
            total_cache_hits += api_metrics.get('cache_hits', 0)
            total_cache_misses += api_metrics.get('cache_misses', 0)
            total_response_time += api_metrics.get('total_response_time_ms', 0)
            total_successful_calls += api_metrics.get('successful_api_calls', 0)
            total_failed_calls += api_metrics.get('failed_api_calls', 0)
            
            # Aggregate endpoint data
            endpoint_usage_data = api_metrics.get('endpoint_usage', {})
            for endpoint, calls in endpoint_usage_data.items():
                endpoint_usage[endpoint] += calls
                endpoint_tokens[endpoint] += metrics.get('token_count', 0)
            
            # Store strategy efficiency
            strategy_efficiency_scores[strategy_name] = api_metrics.get('api_efficiency_score', 0)
        
        # Calculate aggregated metrics
        total_cache_requests = total_cache_hits + total_cache_misses
        avg_response_time = total_response_time / total_api_calls if total_api_calls > 0 else 0
        cache_hit_rate = (total_cache_hits / total_cache_requests * 100) if total_cache_requests > 0 else 0
        success_rate = (total_successful_calls / total_api_calls * 100) if total_api_calls > 0 else 0
        
        return {
            'total_api_calls': total_api_calls,
            'total_cache_hits': total_cache_hits,
            'total_cache_misses': total_cache_misses,
            'total_cache_requests': total_cache_requests,
            'cache_hit_rate_percent': cache_hit_rate,
            'avg_response_time_ms': avg_response_time,
            'success_rate_percent': success_rate,
            'endpoint_usage': dict(endpoint_usage),
            'endpoint_tokens': dict(endpoint_tokens),
            'strategy_efficiency_scores': strategy_efficiency_scores
        }
    
    def _analyze_endpoint_efficiency(self, aggregated_metrics: Dict) -> Dict[str, Any]:
        """Analyze efficiency of different API endpoints."""
        
        endpoint_usage = aggregated_metrics.get('endpoint_usage', {})
        endpoint_tokens = aggregated_metrics.get('endpoint_tokens', {})
        
        endpoint_analysis = {}
        
        for endpoint, calls in endpoint_usage.items():
            tokens_found = endpoint_tokens.get(endpoint, 0)
            tokens_per_call = tokens_found / calls if calls > 0 else 0
            
            # Calculate efficiency score (tokens per call weighted by usage)
            usage_weight = calls / aggregated_metrics.get('total_api_calls', 1)
            efficiency_score = tokens_per_call * usage_weight * 100
            
            endpoint_analysis[endpoint] = {
                'api_calls': calls,
                'tokens_found': tokens_found,
                'tokens_per_call': round(tokens_per_call, 2),
                'usage_percentage': round(usage_weight * 100, 1),
                'efficiency_score': round(efficiency_score, 2),
                'efficiency_grade': self._grade_endpoint_efficiency(tokens_per_call),
                'recommendation': self._generate_endpoint_recommendation(tokens_per_call, usage_weight)
            }
        
        # Sort by efficiency score
        sorted_endpoints = sorted(endpoint_analysis.items(), key=lambda x: x[1]['efficiency_score'], reverse=True)
        
        return {
            'endpoint_analysis': dict(sorted_endpoints),
            'most_efficient_endpoint': sorted_endpoints[0][0] if sorted_endpoints else None,
            'least_efficient_endpoint': sorted_endpoints[-1][0] if sorted_endpoints else None,
            'total_endpoints_used': len(endpoint_analysis),
            'endpoint_diversity_score': self._calculate_endpoint_diversity_score(endpoint_usage)
        }
    
    def _calculate_cost_benefit_ratios(self, all_strategy_metrics: Dict[str, Dict]) -> Dict[str, Any]:
        """Calculate cost-benefit ratios for each strategy."""
        
        cost_benefit_analysis = {}
        
        for strategy_name, metrics in all_strategy_metrics.items():
            api_metrics = metrics.get('api_metrics', {})
            tokens_found = metrics.get('token_count', 0)
            
            api_calls = api_metrics.get('api_calls_made', 0)
            cache_hits = api_metrics.get('cache_hits', 0)
            execution_time = metrics.get('execution_time', 0)
            
            # Calculate various cost metrics
            api_cost_score = api_calls  # Simple proxy for API cost
            time_cost_score = execution_time * 10  # Weight execution time
            cache_efficiency_bonus = cache_hits * 0.1  # Cache hits reduce effective cost
            
            total_cost_score = api_cost_score + time_cost_score - cache_efficiency_bonus
            
            # Calculate benefit metrics
            token_benefit = tokens_found
            quality_benefit = 0
            
            # Add quality benefit if available
            individual_analysis = metrics.get('individual_analysis', {})
            quality_analysis = individual_analysis.get('quality_analysis', {})
            avg_quality = quality_analysis.get('avg_quality_score', 0)
            quality_benefit = tokens_found * (avg_quality / 100)  # Quality-weighted token benefit
            
            total_benefit_score = token_benefit + quality_benefit
            
            # Calculate ratios
            cost_benefit_ratio = total_benefit_score / total_cost_score if total_cost_score > 0 else 0
            tokens_per_api_call = tokens_found / api_calls if api_calls > 0 else 0
            quality_per_cost = quality_benefit / total_cost_score if total_cost_score > 0 else 0
            
            cost_benefit_analysis[strategy_name] = {
                'total_cost_score': round(total_cost_score, 2),
                'total_benefit_score': round(total_benefit_score, 2),
                'cost_benefit_ratio': round(cost_benefit_ratio, 3),
                'tokens_per_api_call': round(tokens_per_api_call, 2),
                'quality_per_cost': round(quality_per_cost, 3),
                'cost_efficiency_grade': self._grade_cost_efficiency(cost_benefit_ratio),
                'breakdown': {
                    'api_cost': api_cost_score,
                    'time_cost': round(time_cost_score, 2),
                    'cache_bonus': round(cache_efficiency_bonus, 2),
                    'token_benefit': token_benefit,
                    'quality_benefit': round(quality_benefit, 2)
                }
            }
        
        # Find best and worst performers
        sorted_strategies = sorted(cost_benefit_analysis.items(), key=lambda x: x[1]['cost_benefit_ratio'], reverse=True)
        
        return {
            'strategy_analysis': cost_benefit_analysis,
            'best_cost_benefit': sorted_strategies[0] if sorted_strategies else None,
            'worst_cost_benefit': sorted_strategies[-1] if sorted_strategies else None,
            'avg_cost_benefit_ratio': sum(s[1]['cost_benefit_ratio'] for s in sorted_strategies) / len(sorted_strategies) if sorted_strategies else 0
        }
    
    def _analyze_cache_optimization(self, aggregated_metrics: Dict) -> Dict[str, Any]:
        """Analyze cache optimization opportunities."""
        
        cache_hits = aggregated_metrics.get('total_cache_hits', 0)
        cache_misses = aggregated_metrics.get('total_cache_misses', 0)
        total_requests = cache_hits + cache_misses
        
        if total_requests == 0:
            return {
                'current_performance': 'No cache data available',
                'optimization_potential': 'Unknown',
                'recommendations': ['Enable cache monitoring']
            }
        
        cache_hit_rate = (cache_hits / total_requests) * 100
        cache_efficiency_score = cache_hit_rate
        
        # Calculate potential savings
        potential_api_calls_saved = cache_hits
        api_calls_if_no_cache = aggregated_metrics.get('total_api_calls', 0) + cache_hits
        savings_percentage = (cache_hits / api_calls_if_no_cache) * 100 if api_calls_if_no_cache > 0 else 0
        
        # Optimization recommendations
        recommendations = []
        if cache_hit_rate < 30:
            recommendations.append("🔴 Critical: Cache hit rate is very low - review cache strategy")
        elif cache_hit_rate < 50:
            recommendations.append("🟡 Warning: Cache hit rate could be improved")
        elif cache_hit_rate < 70:
            recommendations.append("🟢 Good: Cache performance is acceptable")
        else:
            recommendations.append("✅ Excellent: Cache performance is optimal")
        
        if cache_misses > cache_hits:
            recommendations.append("Consider increasing cache TTL for frequently accessed data")
        
        if total_requests > 1000:
            recommendations.append("Consider implementing tiered caching for high-volume operations")
        
        return {
            'current_performance': {
                'cache_hit_rate_percent': round(cache_hit_rate, 1),
                'cache_hits': cache_hits,
                'cache_misses': cache_misses,
                'total_cache_requests': total_requests,
                'efficiency_grade': self._grade_cache_efficiency(cache_hit_rate)
            },
            'optimization_impact': {
                'api_calls_saved': potential_api_calls_saved,
                'savings_percentage': round(savings_percentage, 1),
                'cost_savings_score': round(savings_percentage * 2, 1)  # Approximate cost impact
            },
            'recommendations': recommendations,
            'optimization_potential': self._assess_cache_optimization_potential(cache_hit_rate, total_requests)
        }
    
    def _optimize_rate_limiting(self, aggregated_metrics: Dict) -> Dict[str, Any]:
        """Analyze and optimize rate limiting strategies."""
        
        total_api_calls = aggregated_metrics.get('total_api_calls', 0)
        success_rate = aggregated_metrics.get('success_rate_percent', 0)
        avg_response_time = aggregated_metrics.get('avg_response_time_ms', 0)
        
        # Calculate current rate limiting effectiveness
        rate_limiting_score = success_rate
        if avg_response_time > 5000:  # Slow responses might indicate rate limiting issues
            rate_limiting_score *= 0.8
        
        # Optimization recommendations
        recommendations = []
        
        if success_rate < 90:
            recommendations.append("🔴 Critical: Low success rate may indicate rate limiting issues")
            recommendations.append("Consider implementing exponential backoff")
        
        if avg_response_time > 3000:
            recommendations.append("🟡 Warning: High response times detected")
            recommendations.append("Consider reducing request rate or implementing request batching")
        
        if total_api_calls > 500:
            recommendations.append("Consider implementing intelligent request scheduling")
        
        # Calculate optimal rate limiting parameters
        optimal_rate = self._calculate_optimal_api_rate(total_api_calls, success_rate, avg_response_time)
        
        return {
            'current_performance': {
                'success_rate_percent': success_rate,
                'avg_response_time_ms': avg_response_time,
                'rate_limiting_score': round(rate_limiting_score, 1),
                'performance_grade': self._grade_rate_limiting_performance(success_rate, avg_response_time)
            },
            'optimization_recommendations': recommendations,
            'optimal_parameters': {
                'recommended_api_rate': optimal_rate,
                'batch_size_recommendation': self._recommend_batch_size(total_api_calls),
                'backoff_strategy': self._recommend_backoff_strategy(success_rate)
            }
        }
    
    def _optimize_api_budget_allocation(self, all_strategy_metrics: Dict[str, Dict]) -> Dict[str, Any]:
        """Optimize API budget allocation across strategies."""
        
        strategy_efficiency = {}
        total_api_calls = 0
        total_tokens = 0
        
        for strategy_name, metrics in all_strategy_metrics.items():
            api_calls = metrics.get('api_metrics', {}).get('api_calls_made', 0)
            tokens_found = metrics.get('token_count', 0)
            
            efficiency = tokens_found / api_calls if api_calls > 0 else 0
            
            strategy_efficiency[strategy_name] = {
                'api_calls': api_calls,
                'tokens_found': tokens_found,
                'efficiency': efficiency,
                'current_budget_share': api_calls / sum(m.get('api_metrics', {}).get('api_calls_made', 0) for m in all_strategy_metrics.values()) if sum(m.get('api_metrics', {}).get('api_calls_made', 0) for m in all_strategy_metrics.values()) > 0 else 0
            }
            
            total_api_calls += api_calls
            total_tokens += tokens_found
        
        # Calculate optimal budget allocation based on efficiency
        total_efficiency = sum(s['efficiency'] for s in strategy_efficiency.values())
        
        optimal_allocation = {}
        for strategy_name, data in strategy_efficiency.items():
            optimal_share = data['efficiency'] / total_efficiency if total_efficiency > 0 else 1 / len(strategy_efficiency)
            current_share = data['current_budget_share']
            
            optimal_allocation[strategy_name] = {
                'current_share_percent': round(current_share * 100, 1),
                'optimal_share_percent': round(optimal_share * 100, 1),
                'reallocation_needed': round((optimal_share - current_share) * 100, 1),
                'efficiency_score': round(data['efficiency'], 2),
                'recommendation': self._generate_budget_recommendation(current_share, optimal_share, data['efficiency'])
            }
        
        return {
            'current_allocation': {strategy: data['current_share_percent'] for strategy, data in optimal_allocation.items()},
            'optimal_allocation': {strategy: data['optimal_share_percent'] for strategy, data in optimal_allocation.items()},
            'reallocation_recommendations': optimal_allocation,
            'total_efficiency_score': round(total_tokens / total_api_calls if total_api_calls > 0 else 0, 2),
            'budget_optimization_potential': self._calculate_budget_optimization_potential(optimal_allocation)
        }
    
    def _compare_api_usage_across_strategies(self, all_strategy_metrics: Dict[str, Dict]) -> Dict[str, Any]:
        """Compare API usage patterns across strategies."""
        
        comparison_data = {}
        
        for strategy_name, metrics in all_strategy_metrics.items():
            api_metrics = metrics.get('api_metrics', {})
            
            comparison_data[strategy_name] = {
                'api_calls': api_metrics.get('api_calls_made', 0),
                'tokens_per_call': api_metrics.get('tokens_per_api_call', 0),
                'cache_hit_rate': api_metrics.get('cache_hit_rate_percent', 0),
                'success_rate': api_metrics.get('success_rate_percent', 0),
                'avg_response_time': api_metrics.get('avg_response_time_ms', 0),
                'endpoints_used': len(api_metrics.get('endpoints_used', [])),
                'efficiency_grade': api_metrics.get('resource_efficiency_grade', 'Unknown')
            }
        
        # Find best and worst performers in each category
        best_performers = {
            'tokens_per_call': max(comparison_data.items(), key=lambda x: x[1]['tokens_per_call']) if comparison_data else None,
            'cache_hit_rate': max(comparison_data.items(), key=lambda x: x[1]['cache_hit_rate']) if comparison_data else None,
            'success_rate': max(comparison_data.items(), key=lambda x: x[1]['success_rate']) if comparison_data else None,
            'response_time': min(comparison_data.items(), key=lambda x: x[1]['avg_response_time']) if comparison_data else None
        }
        
        return {
            'strategy_comparison': comparison_data,
            'best_performers': best_performers,
            'performance_rankings': self._rank_strategies_by_api_performance(comparison_data),
            'usage_patterns': self._identify_usage_patterns(comparison_data)
        }
    
    def _generate_optimization_recommendations(self, all_strategy_metrics: Dict[str, Dict], aggregated_metrics: Dict) -> List[str]:
        """Generate comprehensive optimization recommendations."""
        
        recommendations = []
        
        # Cache optimization recommendations
        cache_hit_rate = aggregated_metrics.get('cache_hit_rate_percent', 0)
        if cache_hit_rate < 50:
            recommendations.append("🚨 Priority: Implement or improve caching strategy - current hit rate is too low")
        
        # API efficiency recommendations
        total_calls = aggregated_metrics.get('total_api_calls', 0)
        success_rate = aggregated_metrics.get('success_rate_percent', 0)
        
        if success_rate < 90:
            recommendations.append("🔧 Implement better error handling and retry mechanisms")
        
        if total_calls > 1000:
            recommendations.append("💡 Consider implementing request batching for high-volume operations")
        
        # Strategy-specific recommendations
        strategy_efficiencies = []
        for strategy_name, metrics in all_strategy_metrics.items():
            tokens_per_call = metrics.get('api_metrics', {}).get('tokens_per_api_call', 0)
            strategy_efficiencies.append((strategy_name, tokens_per_call))
        
        # Sort by efficiency
        strategy_efficiencies.sort(key=lambda x: x[1], reverse=True)
        
        if len(strategy_efficiencies) >= 2:
            best_strategy, best_efficiency = strategy_efficiencies[0]
            worst_strategy, worst_efficiency = strategy_efficiencies[-1]
            
            if best_efficiency > worst_efficiency * 2:  # Significant efficiency gap
                recommendations.append(f"⚡ Focus resources on {best_strategy} - it's significantly more API-efficient than {worst_strategy}")
        
        # Endpoint optimization
        endpoint_usage = aggregated_metrics.get('endpoint_usage', {})
        if len(endpoint_usage) > 5:
            recommendations.append("🎯 Consider consolidating endpoint usage - you're using many different endpoints")
        
        # Response time optimization
        avg_response_time = aggregated_metrics.get('avg_response_time_ms', 0)
        if avg_response_time > 2000:
            recommendations.append("⏱️ High response times detected - consider geographic proximity to API servers")
        
        return recommendations
    
    # Helper methods for grading and calculations
    
    def _grade_endpoint_efficiency(self, tokens_per_call: float) -> str:
        """Grade endpoint efficiency based on tokens per call."""
        if tokens_per_call >= 5.0: return "Excellent"
        elif tokens_per_call >= 3.0: return "Very Good"
        elif tokens_per_call >= 2.0: return "Good"
        elif tokens_per_call >= 1.0: return "Fair"
        else: return "Poor"
    
    def _grade_cost_efficiency(self, cost_benefit_ratio: float) -> str:
        """Grade cost efficiency based on cost-benefit ratio."""
        if cost_benefit_ratio >= 2.0: return "Excellent"
        elif cost_benefit_ratio >= 1.5: return "Very Good"
        elif cost_benefit_ratio >= 1.0: return "Good"
        elif cost_benefit_ratio >= 0.5: return "Fair"
        else: return "Poor"
    
    def _grade_cache_efficiency(self, cache_hit_rate: float) -> str:
        """Grade cache efficiency based on hit rate."""
        if cache_hit_rate >= 80: return "Excellent"
        elif cache_hit_rate >= 60: return "Very Good"
        elif cache_hit_rate >= 40: return "Good"
        elif cache_hit_rate >= 20: return "Fair"
        else: return "Poor"
    
    def _grade_rate_limiting_performance(self, success_rate: float, avg_response_time: float) -> str:
        """Grade rate limiting performance."""
        if success_rate >= 95 and avg_response_time < 1500:
            return "Excellent"
        elif success_rate >= 90 and avg_response_time < 3000:
            return "Very Good"
        elif success_rate >= 80 and avg_response_time < 5000:
            return "Good"
        elif success_rate >= 70:
            return "Fair"
        else:
            return "Poor"
    
    def _calculate_endpoint_diversity_score(self, endpoint_usage: Dict) -> float:
        """Calculate how diverse the endpoint usage is."""
        if not endpoint_usage:
            return 0.0
        
        total_calls = sum(endpoint_usage.values())
        if total_calls == 0:
            return 0.0
        
        # Calculate entropy-based diversity score
        entropy = 0
        for calls in endpoint_usage.values():
            proportion = calls / total_calls
            if proportion > 0:
                entropy -= proportion * math.log2(proportion)
        
        # Normalize to 0-100 scale
        max_entropy = math.log2(len(endpoint_usage))
        return (entropy / max_entropy * 100) if max_entropy > 0 else 0
    
    def _generate_endpoint_recommendation(self, tokens_per_call: float, usage_weight: float) -> str:
        """Generate recommendation for endpoint usage."""
        if tokens_per_call >= 3.0 and usage_weight < 0.3:
            return "Increase usage - high efficiency, low utilization"
        elif tokens_per_call < 1.0 and usage_weight > 0.2:
            return "Reduce usage - low efficiency, high utilization"
        elif tokens_per_call >= 2.0:
            return "Maintain usage - good efficiency"
        else:
            return "Optimize or replace - poor efficiency"
    
    def _calculate_optimal_api_rate(self, total_calls: int, success_rate: float, avg_response_time: float) -> int:
        """Calculate optimal API call rate."""
        base_rate = 60  # calls per minute
        
        # Adjust based on success rate
        if success_rate < 80:
            base_rate *= 0.5
        elif success_rate < 90:
            base_rate *= 0.7
        elif success_rate > 95:
            base_rate *= 1.2
        
        # Adjust based on response time
        if avg_response_time > 3000:
            base_rate *= 0.6
        elif avg_response_time > 1500:
            base_rate *= 0.8
        elif avg_response_time < 1000:
            base_rate *= 1.1
        
        return max(10, int(base_rate))  # Minimum 10 calls per minute
    
    def _recommend_batch_size(self, total_calls: int) -> int:
        """Recommend batch size based on total API calls."""
        if total_calls > 1000:
            return 50
        elif total_calls > 500:
            return 25
        elif total_calls > 100:
            return 10
        else:
            return 5
    
    def _recommend_backoff_strategy(self, success_rate: float) -> str:
        """Recommend backoff strategy based on success rate."""
        if success_rate < 70:
            return "Exponential backoff with jitter (aggressive)"
        elif success_rate < 85:
            return "Exponential backoff (moderate)"
        elif success_rate < 95:
            return "Linear backoff (gentle)"
        else:
            return "Minimal backoff (current performance is good)"
    
    def _generate_budget_recommendation(self, current_share: float, optimal_share: float, efficiency: float) -> str:
        """Generate budget allocation recommendation."""
        diff = optimal_share - current_share
        
        if abs(diff) < 0.05:  # Less than 5% difference
            return "Maintain current allocation"
        elif diff > 0.1:  # Should increase by more than 10%
            return f"Increase allocation significantly (+{diff*100:.1f}%)"
        elif diff > 0.05:  # Should increase by 5-10%
            return f"Increase allocation moderately (+{diff*100:.1f}%)"
        elif diff < -0.1:  # Should decrease by more than 10%
            return f"Decrease allocation significantly ({diff*100:.1f}%)"
        else:  # Should decrease by 5-10%
            return f"Decrease allocation moderately ({diff*100:.1f}%)"
    
    def _calculate_budget_optimization_potential(self, optimal_allocation: Dict) -> str:
        """Calculate the potential for budget optimization."""
        total_reallocation_needed = sum(abs(data['reallocation_needed']) for data in optimal_allocation.values())
        avg_reallocation = total_reallocation_needed / len(optimal_allocation) if optimal_allocation else 0
        
        if avg_reallocation > 20:
            return "High - Significant reallocation could improve efficiency"
        elif avg_reallocation > 10:
            return "Medium - Moderate reallocation recommended"
        elif avg_reallocation > 5:
            return "Low - Minor adjustments could help"
        else:
            return "Minimal - Current allocation is near optimal"
    
    def _assess_cache_optimization_potential(self, cache_hit_rate: float, total_requests: int) -> str:
        """Assess potential for cache optimization."""
        if cache_hit_rate < 30:
            return "High - Major cache improvements possible"
        elif cache_hit_rate < 50:
            return "Medium - Moderate cache improvements possible"
        elif cache_hit_rate < 70:
            return "Low - Minor cache improvements possible"
        else:
            return "Minimal - Cache is already well optimized"
    
    def _rank_strategies_by_api_performance(self, comparison_data: Dict) -> List[Tuple[str, float]]:
        """Rank strategies by overall API performance."""
        performance_scores = []
        
        for strategy_name, data in comparison_data.items():
            # Weighted performance score
            score = (
                data['tokens_per_call'] * 0.3 +
                data['cache_hit_rate'] * 0.25 +
                data['success_rate'] * 0.25 +
                (100 - min(100, data['avg_response_time'] / 50)) * 0.2  # Response time (inverted)
            )
            performance_scores.append((strategy_name, score))
        
        return sorted(performance_scores, key=lambda x: x[1], reverse=True)
    
    def _identify_usage_patterns(self, comparison_data: Dict) -> Dict[str, List[str]]:
        """Identify common usage patterns across strategies."""
        patterns = {
            'high_volume': [],
            'high_efficiency': [],
            'cache_optimized': [],
            'response_time_optimized': []
        }
        
        for strategy_name, data in comparison_data.items():
            if data['api_calls'] > 100:
                patterns['high_volume'].append(strategy_name)
            if data['tokens_per_call'] > 3.0:
                patterns['high_efficiency'].append(strategy_name)
            if data['cache_hit_rate'] > 60:
                patterns['cache_optimized'].append(strategy_name)
            if data['avg_response_time'] < 1500:
                patterns['response_time_optimized'].append(strategy_name)
        
        return patterns


class StrategyComparisonAnalyzer:
    """Comprehensive strategy comparison and analysis engine."""
    
    def __init__(self):
        """Initialize the strategy comparison analyzer."""
        # Check for debug mode
        debug_mode = os.getenv('DEBUG_MODE', 'false').lower() == 'true'
        log_level = os.getenv('LOG_LEVEL', 'INFO').upper()
        
        self.logger_setup = LoggerSetup("StrategyComparison")
        self.logger = self.logger_setup.logger
        
        # Set debug logging level if debug mode is enabled
        if debug_mode:
            self.logger.setLevel(getattr(logging, log_level, logging.DEBUG))
            for handler in self.logger.handlers:
                handler.setLevel(getattr(logging, log_level, logging.DEBUG))
            self.logger.info("🐛 DEBUG MODE ENABLED - Enhanced logging activated")
        
        self.structured_logger = get_structured_logger('StrategyComparison')
        self.debug_mode = debug_mode
        
        # Results storage
        self.strategy_results = {}
        self.comparison_metrics = {}
        self.analysis_timestamp = int(time.time())
        
        # Analysis configuration
        self.analysis_config = {
            "min_quality_score": 60.0,           # Minimum quality threshold
            "high_quality_threshold": 80.0,      # High quality threshold
            "overlap_significance_threshold": 0.3, # 30%+ overlap is significant
            "performance_weights": {
                "token_count": 0.2,              # 20% - Number of tokens found
                "avg_quality": 0.3,              # 30% - Average token quality
                "high_quality_count": 0.2,       # 20% - Number of high-quality tokens
                "uniqueness": 0.15,              # 15% - Strategy uniqueness
                "execution_efficiency": 0.15,    # 15% - Execution speed/efficiency
            }
        }
        
        # Initialize strategies and API optimizer
        self.strategies = self._initialize_strategies()
        self.api_optimizer = APIOptimizationAnalyzer(logger=self.logger)
        
        # Initialize debug profiler
        self.debug_profiler = DebugProfiler(logger=self.logger, debug_mode=self.debug_mode)
    
    async def _initialize_birdeye_api(self) -> BirdeyeAPI:
        """Initialize BirdeyeAPI with required dependencies."""
        import os
        from core.cache_manager import CacheManager
        from services.rate_limiter_service import RateLimiterService
        
        # Check API key
        api_key = os.getenv('BIRDEYE_API_KEY')
        if not api_key:
            raise ValueError("BIRDEYE_API_KEY environment variable not set")
        
        # Initialize services
        cache_manager = CacheManager(ttl_default=300)
        rate_limiter = RateLimiterService()
        
        # Create config for BirdeyeAPI
        config = {
            'api_key': api_key,
            'base_url': 'https://public-api.birdeye.so',
            'rate_limit': 100,
            'request_timeout_seconds': 20,
            'cache_ttl_default_seconds': 300,
            'cache_ttl_error_seconds': 60,
            'max_retries': 3,
            'backoff_factor': 2
        }
        
        # Create logger for BirdeyeAPI
        from services.logger_setup import LoggerSetup
        birdeye_logger = LoggerSetup("BirdeyeAPI")
        
        birdeye_api = BirdeyeAPI(config, birdeye_logger, cache_manager, rate_limiter)
        
        self.logger.info("✅ BirdeyeAPI initialized successfully")
        return birdeye_api
        
    def _initialize_strategies(self) -> List[Any]:
        """Initialize all token discovery strategies."""
        strategies = []
        
        try:
            # Initialize each strategy with consistent logger
            strategy_classes = [
                VolumeMomentumStrategy,
                RecentListingsStrategy,
                PriceMomentumStrategy, 
                LiquidityGrowthStrategy,
                HighTradingActivityStrategy,
                SmartMoneyWhaleStrategy
            ]
            
            for strategy_class in strategy_classes:
                try:
                    strategy = strategy_class(logger=self.logger)
                    strategies.append(strategy)
                    self.logger.info(f"✅ Initialized {strategy.name}")
                except Exception as e:
                    self.logger.error(f"❌ Failed to initialize {strategy_class.__name__}: {e}")
            
            self.logger.info(f"🚀 Initialized {len(strategies)} strategies total")
            return strategies
            
        except Exception as e:
            self.logger.error(f"Error initializing strategies: {e}")
            return []
    
    async def run_comprehensive_comparison(self) -> Dict[str, Any]:
        """Run comprehensive strategy comparison analysis."""
        self.logger.info("🎯 Starting Comprehensive Strategy Comparison V4")
        self.logger.info("=" * 80)
        
        # Initialize Birdeye API with required dependencies
        birdeye_api = await self._initialize_birdeye_api()
        scan_id = f"strategy_comparison_{self.analysis_timestamp}"
        
        try:
            # Phase 1: Execute all strategies independently
            self.debug_profiler.start_phase("Phase_1_Strategy_Execution")
            self.logger.info("📊 Phase 1: Independent Strategy Execution")
            if self.debug_mode:
                self.logger.debug(f"🐛 DEBUG: Starting Phase 1 with scan_id: {scan_id}")
                self.logger.debug(f"🐛 DEBUG: Initialized {len(self.strategies)} strategies")
                self.debug_profiler.debug_pause("Ready to execute strategies")
            await self._execute_all_strategies(birdeye_api, scan_id)
            self.debug_profiler.end_phase("Phase_1_Strategy_Execution")
            
            # Phase 2: Analyze individual strategy performance  
            self.debug_profiler.start_phase("Phase_2_Individual_Analysis")
            self.logger.info("📈 Phase 2: Individual Strategy Analysis")
            await self._analyze_individual_strategies()
            self.debug_profiler.end_phase("Phase_2_Individual_Analysis")
            
            # Phase 3: Cross-strategy comparison analysis
            self.debug_profiler.start_phase("Phase_3_Cross_Strategy_Analysis")
            self.logger.info("🔄 Phase 3: Cross-Strategy Comparison")
            await self._analyze_cross_strategy_performance()
            self.debug_profiler.end_phase("Phase_3_Cross_Strategy_Analysis")
            
            # Phase 4: API optimization analysis
            self.debug_profiler.start_phase("Phase_4_API_Optimization")
            self.logger.info("🔧 Phase 4: API Optimization Analysis")
            await self._analyze_api_optimization()
            self.debug_profiler.end_phase("Phase_4_API_Optimization")
            
            # Phase 5: Generate comprehensive report
            self.debug_profiler.start_phase("Phase_5_Report_Generation")
            self.logger.info("📋 Phase 5: Comprehensive Report Generation")
            final_report = await self._generate_comprehensive_report()
            self.debug_profiler.end_phase("Phase_5_Report_Generation")
            
            # Phase 6: Save results
            self.debug_profiler.start_phase("Phase_6_Save_Results")
            await self._save_analysis_results(final_report)
            self.debug_profiler.end_phase("Phase_6_Save_Results")
            
            # Save debug session
            if self.debug_mode:
                self.debug_profiler.save_debug_session()
                performance_summary = self.debug_profiler.get_performance_summary()
                self.logger.info("🐛 DEBUG SESSION SUMMARY:")
                self.logger.info(f"   📊 Functions traced: {performance_summary.get('total_functions_traced', 0)}")
                self.logger.info(f"   ⏱️ Total execution time: {performance_summary.get('total_execution_time', 0):.2f}s")
                self.logger.info(f"   💾 Max memory usage: {performance_summary.get('max_memory_usage_mb', 0):.2f}MB")
                self.logger.info(f"   ❌ Errors encountered: {performance_summary.get('error_count', 0)}")
                self.logger.info(f"   📁 Debug files saved to: {self.debug_profiler.debug_dir}")
            
            self.logger.info("✅ Comprehensive Strategy Comparison Complete!")
            return final_report
            
        except Exception as e:
            self.logger.error(f"❌ Error in comprehensive comparison: {e}")
            raise
    
    async def _execute_all_strategies(self, birdeye_api: BirdeyeAPI, scan_id: str):
        """Execute all strategies independently and collect results."""
        
        total_strategies = len(self.strategies)
        for i, strategy in enumerate(self.strategies, 1):
            strategy_name = strategy.name
            self.logger.info(f"🔍 [{i}/{total_strategies}] Executing {strategy_name}")
            
            # Debug progress tracking
            self.debug_profiler.log_strategy_progress(strategy_name, i-1, total_strategies, "Starting execution")
            
            start_time = time.time()
            
            # Capture API statistics before strategy execution
            pre_execution_api_stats = birdeye_api.get_api_call_statistics()
            pre_execution_performance = birdeye_api.get_performance_stats()
            
            # Debug memory snapshot before strategy
            if self.debug_mode:
                self.debug_profiler._take_memory_snapshot(f"before_strategy_{strategy_name}")
                self.logger.debug(f"🐛 Starting {strategy_name} | Memory: {self.debug_profiler._get_memory_usage():.2f}MB")
            
            try:
                # Execute strategy
                tokens = await strategy.execute(birdeye_api, scan_id=f"{scan_id}_{strategy_name.lower().replace(' ', '_')}")
                execution_time = time.time() - start_time
                
                # Capture API statistics after strategy execution
                post_execution_api_stats = birdeye_api.get_api_call_statistics()
                post_execution_performance = birdeye_api.get_performance_stats()
                
                # Calculate strategy-specific API metrics
                strategy_api_metrics = self._calculate_strategy_api_metrics(
                    pre_execution_api_stats, post_execution_api_stats,
                    pre_execution_performance, post_execution_performance,
                    len(tokens), execution_time
                )
                
                # Store results with API metrics
                self.strategy_results[strategy_name] = {
                    "tokens": tokens,
                    "execution_time": execution_time,
                    "token_count": len(tokens),
                    "strategy_instance": strategy,
                    "execution_successful": True,
                    "error": None,
                    "api_metrics": strategy_api_metrics
                }
                
                self.logger.info(f"✅ {strategy_name}: {len(tokens)} tokens in {execution_time:.2f}s")
                self.logger.info(f"   📡 API Calls: {strategy_api_metrics['api_calls_made']}, "
                               f"Cache Hits: {strategy_api_metrics['cache_hits']}, "
                               f"Efficiency: {strategy_api_metrics['tokens_per_api_call']:.2f} tokens/call")
                
                # Debug progress update
                self.debug_profiler.log_strategy_progress(strategy_name, i, total_strategies, f"✅ Completed - {len(tokens)} tokens")
                
                # Debug mode: show detailed API metrics and token analysis
                if self.debug_mode:
                    self.debug_profiler._take_memory_snapshot(f"after_strategy_{strategy_name}")
                    self.logger.debug(f"🐛 DEBUG {strategy_name} API Details:")
                    self.logger.debug(f"   Success Rate: {strategy_api_metrics.get('success_rate_percent', 0):.1f}%")
                    self.logger.debug(f"   Avg Response Time: {strategy_api_metrics.get('avg_response_time_ms', 0):.1f}ms")
                    self.logger.debug(f"   Endpoints Used: {strategy_api_metrics.get('endpoints_used', [])}")
                    self.logger.debug(f"   Resource Efficiency: {strategy_api_metrics.get('resource_efficiency_grade', 'Unknown')}")
                    
                    # Log individual token analysis for top tokens
                    for idx, token in enumerate(tokens[:3]):  # Top 3 tokens for debug
                        if token.get('address'):
                            self.debug_profiler.log_token_analysis(
                                strategy_name, 
                                token['address'], 
                                {
                                    'score': token.get('score', 0),
                                    'market_cap': token.get('marketCap', 0),
                                    'volume_24h': token.get('volume24hUSD', 0),
                                    'price_change_24h': token.get('priceChange24hPercent', 0)
                                }
                            )
                
                # Log structured data with API metrics
                self.structured_logger.info({
                    "event": "strategy_execution_complete",
                    "strategy": strategy_name,
                    "scan_id": scan_id,
                    "tokens_found": len(tokens),
                    "execution_time": execution_time,
                    "api_metrics": strategy_api_metrics,
                    "timestamp": int(time.time())
                })
                
            except Exception as e:
                execution_time = time.time() - start_time
                
                # Capture API stats even on failure
                post_execution_api_stats = birdeye_api.get_api_call_statistics()
                post_execution_performance = birdeye_api.get_performance_stats()
                
                strategy_api_metrics = self._calculate_strategy_api_metrics(
                    pre_execution_api_stats, post_execution_api_stats,
                    pre_execution_performance, post_execution_performance,
                    0, execution_time
                )
                
                # Store error results with API metrics
                self.strategy_results[strategy_name] = {
                    "tokens": [],
                    "execution_time": execution_time,
                    "token_count": 0,
                    "strategy_instance": strategy,  
                    "execution_successful": False,
                    "error": str(e),
                    "api_metrics": strategy_api_metrics
                }
                
                self.logger.error(f"❌ {strategy_name} failed: {e}")
                self.logger.warning(f"   📡 API Calls during failure: {strategy_api_metrics['api_calls_made']}")
                
                # Debug progress update for failure
                self.debug_profiler.log_strategy_progress(strategy_name, i, total_strategies, f"❌ Failed - {str(e)[:50]}...")
                
                # Enhanced debug logging for errors
                if self.debug_mode:
                    self.debug_profiler._take_memory_snapshot(f"error_strategy_{strategy_name}")
                    self.logger.debug(f"🐛 ERROR DETAILS for {strategy_name}:")
                    self.logger.debug(f"   Exception Type: {type(e).__name__}")
                    self.logger.debug(f"   Exception Args: {e.args}")
                    self.logger.debug(f"   Memory at Error: {self.debug_profiler._get_memory_usage():.2f}MB")
                    self.logger.debug(f"   Full Traceback:\n{traceback.format_exc()}")
                    
                    # Store detailed error context
                    error_context = {
                        'strategy_name': strategy_name,
                        'error_type': type(e).__name__,
                        'error_message': str(e),
                        'execution_time': execution_time,
                        'api_metrics': strategy_api_metrics,
                        'memory_usage': self.debug_profiler._get_memory_usage(),
                        'traceback': traceback.format_exc(),
                        'timestamp': time.time()
                    }
                    
                    # Save error context to debug session
                    self.debug_profiler.error_context_stack.append(error_context)
                
                # Log structured error with API metrics
                self.structured_logger.error({
                    "event": "strategy_execution_error",
                    "strategy": strategy_name,
                    "scan_id": scan_id,
                    "error": str(e),
                    "execution_time": execution_time,
                    "api_metrics": strategy_api_metrics,
                    "timestamp": int(time.time())
                })
    
    def _calculate_strategy_api_metrics(self, pre_stats: Dict[str, Any], post_stats: Dict[str, Any], 
                                      pre_performance: Dict[str, Any], post_performance: Dict[str, Any],
                                      tokens_found: int, execution_time: float) -> Dict[str, Any]:
        """Calculate API metrics specific to a strategy execution."""
        
        # Calculate deltas
        api_calls_made = post_stats['total_api_calls'] - pre_stats['total_api_calls']
        successful_calls = post_stats['successful_api_calls'] - pre_stats['successful_api_calls']
        failed_calls = post_stats['failed_api_calls'] - pre_stats['failed_api_calls']
        cache_hits = post_stats['cache_hits'] - pre_stats['cache_hits'] 
        cache_misses = post_stats['cache_misses'] - pre_stats['cache_misses']
        
        # Calculate response time delta
        total_response_time_delta = post_stats['total_response_time_ms'] - pre_stats['total_response_time_ms']
        avg_response_time = total_response_time_delta / api_calls_made if api_calls_made > 0 else 0
        
        # Calculate efficiency metrics
        tokens_per_api_call = tokens_found / api_calls_made if api_calls_made > 0 else 0
        api_calls_per_second = api_calls_made / execution_time if execution_time > 0 else 0
        
        # Calculate cache efficiency
        total_cache_requests = cache_hits + cache_misses
        cache_hit_rate = (cache_hits / total_cache_requests * 100) if total_cache_requests > 0 else 0
        
        # Calculate success rate
        success_rate = (successful_calls / api_calls_made * 100) if api_calls_made > 0 else 0
        
        # Calculate cost efficiency (if cost tracking available)
        cost_metrics = {}
        if 'cost_tracking' in post_stats and post_stats['cost_tracking']:
            cost_data = post_stats['cost_tracking']
            if cost_data and 'total_compute_units' in cost_data:
                total_cu = cost_data.get('total_compute_units', 0)
                cost_metrics = {
                    'compute_units_used': total_cu,
                    'cost_per_token': total_cu / tokens_found if tokens_found > 0 else 0,
                    'cost_efficiency_score': tokens_found / total_cu if total_cu > 0 else 0
                }
        
        # Determine endpoint usage pattern
        pre_endpoints = pre_stats.get('calls_by_endpoint', {})
        post_endpoints = post_stats.get('calls_by_endpoint', {})
        endpoint_usage = {}
        
        for endpoint, post_count in post_endpoints.items():
            pre_count = pre_endpoints.get(endpoint, 0)
            calls_made = post_count - pre_count
            if calls_made > 0:
                endpoint_usage[endpoint] = calls_made
        
        return {
            # Core API metrics
            'api_calls_made': api_calls_made,
            'successful_api_calls': successful_calls,
            'failed_api_calls': failed_calls,
            'success_rate_percent': round(success_rate, 2),
            
            # Cache performance
            'cache_hits': cache_hits,
            'cache_misses': cache_misses,
            'cache_hit_rate_percent': round(cache_hit_rate, 2),
            'total_cache_requests': total_cache_requests,
            
            # Performance metrics
            'avg_response_time_ms': round(avg_response_time, 2),
            'total_response_time_ms': total_response_time_delta,
            
            # Efficiency metrics
            'tokens_per_api_call': round(tokens_per_api_call, 2),
            'api_calls_per_second': round(api_calls_per_second, 2),
            'api_efficiency_score': round(tokens_per_api_call * success_rate / 100, 2),
            
            # Endpoint analysis
            'endpoints_used': list(endpoint_usage.keys()),
            'endpoint_usage': endpoint_usage,
            'endpoint_diversity': len(endpoint_usage),
            
            # Cost metrics (if available)
            'cost_metrics': cost_metrics,
            
            # Resource utilization
            'resource_efficiency_grade': self._grade_api_efficiency(tokens_per_api_call, cache_hit_rate, success_rate),
            'api_health_status': self._grade_api_health(success_rate, avg_response_time)
        }
    
    async def _analyze_individual_strategies(self):
        """Analyze individual strategy performance."""
        
        for strategy_name, results in self.strategy_results.items():
            self.logger.info(f"📊 Analyzing {strategy_name}")
            
            if not results["execution_successful"]:
                continue
                
            tokens = results["tokens"]
            strategy_analysis = {
                "basic_metrics": self._calculate_basic_metrics(tokens),
                "quality_analysis": self._analyze_token_quality(tokens),
                "diversity_analysis": self._analyze_token_diversity(tokens),
                "enhancement_analysis": self._analyze_enhancement_effectiveness(tokens),
                "risk_analysis": self._analyze_risk_factors(tokens),
                "efficiency_metrics": self._calculate_efficiency_metrics(results)
            }
            
            # Store analysis
            results["individual_analysis"] = strategy_analysis
            
            # Log key insights
            basic = strategy_analysis["basic_metrics"]
            quality = strategy_analysis["quality_analysis"]
            
            self.logger.info(f"  📈 Tokens: {basic['token_count']}, Avg Score: {quality['avg_quality_score']:.1f}")
            self.logger.info(f"  🎯 High Quality: {quality['high_quality_count']}, Unique Tokens: {basic['unique_addresses']}")
    
    async def _analyze_cross_strategy_performance(self):
        """Analyze cross-strategy performance and overlaps."""
        
        # Calculate overlaps between strategies
        overlap_matrix = self._calculate_overlap_matrix()
        
        # Analyze token uniqueness and strategy distinctiveness
        uniqueness_analysis = self._analyze_strategy_uniqueness()
        
        # Performance ranking
        performance_ranking = self._calculate_performance_ranking()
        
        # Strategy complementarity analysis
        complementarity_analysis = self._analyze_strategy_complementarity()
        
        # Token quality comparison
        quality_comparison = self._compare_token_quality_across_strategies()
        
        self.comparison_metrics = {
            "overlap_matrix": overlap_matrix,
            "uniqueness_analysis": uniqueness_analysis,
            "performance_ranking": performance_ranking,
            "complementarity_analysis": complementarity_analysis,
            "quality_comparison": quality_comparison,
            "total_unique_tokens": len(self._get_all_unique_tokens()),
            "successful_strategies": len([r for r in self.strategy_results.values() if r["execution_successful"]])
        }
        
        self.logger.info(f"🔄 Cross-analysis complete: {self.comparison_metrics['total_unique_tokens']} total unique tokens")
    
    async def _analyze_api_optimization(self):
        """Analyze API optimization opportunities across all strategies."""
        
        # Collect all strategy metrics with API data
        all_strategy_metrics = {}
        
        for strategy_name, results in self.strategy_results.items():
            if results["execution_successful"] and results.get("api_metrics"):
                all_strategy_metrics[strategy_name] = results
        
        if not all_strategy_metrics:
            self.logger.warning("⚠️ No API metrics available for optimization analysis")
            self.comparison_metrics["api_optimization"] = {
                "status": "No data available",
                "message": "API metrics collection needs to be enabled"
            }
            return
        
        # Run comprehensive API optimization analysis
        self.logger.info(f"🔍 Analyzing API optimization for {len(all_strategy_metrics)} strategies")
        
        try:
            api_optimization_results = self.api_optimizer.analyze_api_optimization(all_strategy_metrics)
            
            # Store results
            self.comparison_metrics["api_optimization"] = api_optimization_results
            
            # Log key insights
            endpoint_efficiency = api_optimization_results.get("endpoint_efficiency", {})
            cost_benefit = api_optimization_results.get("cost_benefit_analysis", {})
            cache_optimization = api_optimization_results.get("cache_optimization", {})
            
            # Log endpoint insights
            if endpoint_efficiency:
                most_efficient = endpoint_efficiency.get("most_efficient_endpoint")
                total_endpoints = endpoint_efficiency.get("total_endpoints_used", 0)
                self.logger.info(f"  📡 Endpoints: {total_endpoints} used, most efficient: {most_efficient}")
            
            # Log cost-benefit insights
            if cost_benefit.get("best_cost_benefit"):
                best_strategy = cost_benefit["best_cost_benefit"][0]
                best_ratio = cost_benefit["best_cost_benefit"][1]["cost_benefit_ratio"]
                self.logger.info(f"  💰 Best cost-benefit: {best_strategy} (ratio: {best_ratio:.2f})")
            
            # Log cache insights
            cache_perf = cache_optimization.get("current_performance", {})
            if isinstance(cache_perf, dict):
                cache_hit_rate = cache_perf.get("cache_hit_rate_percent", 0)
                cache_grade = cache_perf.get("efficiency_grade", "Unknown")
                self.logger.info(f"  🗄️ Cache performance: {cache_hit_rate:.1f}% hit rate ({cache_grade})")
            
            # Log optimization recommendations count
            recommendations = api_optimization_results.get("optimization_recommendations", [])
            self.logger.info(f"  💡 Generated {len(recommendations)} optimization recommendations")
            
        except Exception as e:
            self.logger.error(f"❌ Error in API optimization analysis: {e}")
            self.comparison_metrics["api_optimization"] = {
                "status": "Analysis failed",
                "error": str(e)
            }
    
    def _calculate_basic_metrics(self, tokens: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Calculate basic metrics for a token list."""
        if not tokens:
            return {"token_count": 0, "unique_addresses": 0, "avg_score": 0.0}
        
        addresses = set()
        scores = []
        
        for token in tokens:
            if token.get("address"):
                addresses.add(token.get("address"))
            if token.get("score") is not None:
                scores.append(token.get("score", 0))
        
        return {
            "token_count": len(tokens),
            "unique_addresses": len(addresses),
            "avg_score": sum(scores) / len(scores) if scores else 0.0,
            "total_score": sum(scores),
            "score_distribution": {
                "min": min(scores) if scores else 0,
                "max": max(scores) if scores else 0,
                "median": sorted(scores)[len(scores)//2] if scores else 0
            }
        }
    
    def _analyze_token_quality(self, tokens: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Analyze token quality metrics."""
        if not tokens:
            return {
                "avg_quality_score": 0.0,
                "high_quality_count": 0,
                "quality_distribution": {},
                "enhancement_effectiveness": 0.0
            }
        
        scores = [token.get("score", 0) for token in tokens]
        enhanced_scores = [token.get("enhanced_score", token.get("score", 0)) for token in tokens]
        
        high_quality_count = len([s for s in scores if s >= self.analysis_config["high_quality_threshold"]])
        
        quality_ranges = {
            "excellent": len([s for s in scores if s >= 90]),
            "very_good": len([s for s in scores if 80 <= s < 90]),
            "good": len([s for s in scores if 70 <= s < 80]),
            "fair": len([s for s in scores if 60 <= s < 70]),
            "poor": len([s for s in scores if s < 60])
        }
        
        # Enhancement effectiveness
        enhancement_boost = sum(enhanced_scores) - sum(scores) if enhanced_scores and scores else 0
        enhancement_effectiveness = enhancement_boost / len(tokens) if tokens else 0
        
        return {
            "avg_quality_score": sum(scores) / len(scores) if scores else 0,
            "high_quality_count": high_quality_count,
            "quality_distribution": quality_ranges,
            "enhancement_effectiveness": enhancement_effectiveness,
            "quality_grade": self._grade_overall_quality(sum(scores) / len(scores) if scores else 0)
        }
    
    def _analyze_token_diversity(self, tokens: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Analyze token diversity across different dimensions."""
        if not tokens:
            return {"market_cap_diversity": 0, "sector_diversity": 0, "age_diversity": 0}
        
        # Market cap diversity
        market_caps = [token.get("marketCap", 0) for token in tokens if token.get("marketCap", 0) > 0]
        mcap_ranges = self._categorize_market_caps(market_caps)
        
        # Age diversity
        current_time = time.time()
        ages = []
        for token in tokens:
            creation_time = token.get("createdTime", 0) or token.get("creation_time", 0)
            if creation_time > 0:
                age_days = (current_time - creation_time) / (24 * 60 * 60)
                ages.append(age_days)
        
        age_ranges = self._categorize_ages(ages)
        
        return {
            "market_cap_diversity": len([v for v in mcap_ranges.values() if v > 0]),
            "market_cap_distribution": mcap_ranges,
            "age_diversity": len([v for v in age_ranges.values() if v > 0]),
            "age_distribution": age_ranges,
            "diversity_score": self._calculate_diversity_score(mcap_ranges, age_ranges)
        }
    
    def _analyze_enhancement_effectiveness(self, tokens: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Analyze effectiveness of token enhancements."""
        if not tokens:
            return {"enhancement_count": 0, "avg_boost": 0.0, "enhancement_types": {}}
        
        enhanced_tokens = [t for t in tokens if t.get("enhancement_factors")]
        enhancement_types = Counter()
        total_boost = 0
        
        for token in enhanced_tokens:
            factors = token.get("enhancement_factors", [])
            for factor in factors:
                enhancement_type = factor.split(":")[0] if ":" in factor else factor
                enhancement_types[enhancement_type] += 1
            
            base_score = token.get("base_score_before_enhancement", token.get("score", 0))
            enhanced_score = token.get("enhanced_score", token.get("score", 0))
            if base_score > 0:
                boost = (enhanced_score - base_score) / base_score
                total_boost += boost
        
        return {
            "enhancement_count": len(enhanced_tokens),
            "avg_boost": total_boost / len(enhanced_tokens) if enhanced_tokens else 0,
            "enhancement_types": dict(enhancement_types),
            "enhancement_rate": len(enhanced_tokens) / len(tokens) if tokens else 0
        }
    
    def _analyze_risk_factors(self, tokens: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Analyze risk factors across tokens."""
        if not tokens:
            return {"high_risk_count": 0, "risk_distribution": {}, "avg_risk_score": 0}
        
        high_risk_count = 0
        risk_factors = Counter()
        risk_scores = []
        
        for token in tokens:
            # Check holder concentration warnings
            if token.get("concentration_warning"):
                high_risk_count += 1
                risk_factors["concentration_risk"] += 1
            
            # Check risk levels
            holder_risk = token.get("holder_risk_level", "unknown")
            if holder_risk == "high":
                risk_factors["holder_risk"] += 1
            
            # Collect risk scores
            holder_risk_score = token.get("holder_analysis", {}).get("risk_assessment", {}).get("overall_risk_score", 50)
            risk_scores.append(holder_risk_score)
        
        return {
            "high_risk_count": high_risk_count,
            "risk_distribution": dict(risk_factors),
            "avg_risk_score": sum(risk_scores) / len(risk_scores) if risk_scores else 50,
            "risk_grade": self._grade_risk_level(sum(risk_scores) / len(risk_scores) if risk_scores else 50)
        }
    
    def _calculate_efficiency_metrics(self, results: Dict[str, Any]) -> Dict[str, Any]:
        """Calculate strategy execution efficiency metrics."""
        execution_time = results.get("execution_time", 0)
        token_count = results.get("token_count", 0)
        
        tokens_per_second = token_count / execution_time if execution_time > 0 else 0
        
        return {
            "execution_time": execution_time,
            "tokens_per_second": tokens_per_second,
            "efficiency_grade": self._grade_efficiency(execution_time, token_count)
        }
    
    def _calculate_overlap_matrix(self) -> Dict[str, Dict[str, float]]:
        """Calculate overlap matrix between all strategies."""
        strategy_names = list(self.strategy_results.keys())
        overlap_matrix = {}
        
        for strategy1 in strategy_names:
            overlap_matrix[strategy1] = {}
            tokens1 = set(t.get("address") for t in self.strategy_results[strategy1]["tokens"] if t.get("address"))
            
            for strategy2 in strategy_names:
                if strategy1 == strategy2:
                    overlap_matrix[strategy1][strategy2] = 1.0
                else:
                    tokens2 = set(t.get("address") for t in self.strategy_results[strategy2]["tokens"] if t.get("address"))
                    
                    if tokens1 or tokens2:
                        overlap = len(tokens1.intersection(tokens2)) / len(tokens1.union(tokens2))
                        overlap_matrix[strategy1][strategy2] = overlap
                    else:
                        overlap_matrix[strategy1][strategy2] = 0.0
        
        return overlap_matrix
    
    def _analyze_strategy_uniqueness(self) -> Dict[str, Any]:
        """Analyze how unique each strategy's discoveries are."""
        all_tokens = self._get_all_unique_tokens()
        token_strategy_map = defaultdict(list)
        
        # Map each token to strategies that found it
        for strategy_name, results in self.strategy_results.items():
            for token in results["tokens"]:
                address = token.get("address")
                if address:
                    token_strategy_map[address].append(strategy_name)
        
        # Calculate uniqueness for each strategy
        uniqueness_analysis = {}
        for strategy_name, results in self.strategy_results.items():
            strategy_tokens = set(t.get("address") for t in results["tokens"] if t.get("address"))
            
            unique_tokens = 0
            shared_tokens = 0
            
            for address in strategy_tokens:
                if len(token_strategy_map[address]) == 1:
                    unique_tokens += 1
                else:
                    shared_tokens += 1
            
            total_tokens = len(strategy_tokens)
            uniqueness_score = unique_tokens / total_tokens if total_tokens > 0 else 0
            
            uniqueness_analysis[strategy_name] = {
                "unique_tokens": unique_tokens,
                "shared_tokens": shared_tokens,
                "total_tokens": total_tokens,
                "uniqueness_score": uniqueness_score,
                "uniqueness_grade": self._grade_uniqueness(uniqueness_score)
            }
        
        return uniqueness_analysis
    
    def _calculate_performance_ranking(self) -> List[Dict[str, Any]]:
        """Calculate overall performance ranking of strategies."""
        rankings = []
        
        for strategy_name, results in self.strategy_results.items():
            if not results["execution_successful"]:
                continue
                
            analysis = results.get("individual_analysis", {})
            basic = analysis.get("basic_metrics", {})
            quality = analysis.get("quality_analysis", {})
            efficiency = analysis.get("efficiency_metrics", {})
            api_metrics = results.get("api_metrics", {})
            
            # Calculate weighted performance score
            weights = self.analysis_config["performance_weights"]
            
            token_count_score = min(100, basic.get("token_count", 0) * 2)  # Normalize to 100
            avg_quality_score = quality.get("avg_quality_score", 0)
            high_quality_score = min(100, quality.get("high_quality_count", 0) * 10)  # Normalize to 100
            uniqueness_score = self.comparison_metrics.get("uniqueness_analysis", {}).get(strategy_name, {}).get("uniqueness_score", 0) * 100
            
            # Enhanced efficiency score including API metrics
            execution_efficiency_score = min(100, efficiency.get("tokens_per_second", 0) * 20)  # Normalize to 100
            api_efficiency_score = min(100, api_metrics.get("tokens_per_api_call", 0) * 5)  # Normalize to 100
            cache_efficiency_score = api_metrics.get("cache_hit_rate_percent", 0)
            
            # Combined efficiency score (execution + API efficiency)
            combined_efficiency_score = (execution_efficiency_score * 0.4 + 
                                       api_efficiency_score * 0.4 + 
                                       cache_efficiency_score * 0.2)
            
            performance_score = (
                weights["token_count"] * token_count_score +
                weights["avg_quality"] * avg_quality_score +  
                weights["high_quality_count"] * high_quality_score +
                weights["uniqueness"] * uniqueness_score +
                weights["execution_efficiency"] * combined_efficiency_score
            )
            
            rankings.append({
                "strategy": strategy_name,
                "performance_score": performance_score,
                "component_scores": {
                    "token_count": token_count_score,
                    "avg_quality": avg_quality_score,
                    "high_quality_count": high_quality_score,
                    "uniqueness": uniqueness_score,
                    "execution_efficiency": execution_efficiency_score,
                    "api_efficiency": api_efficiency_score,
                    "cache_efficiency": cache_efficiency_score,
                    "combined_efficiency": combined_efficiency_score
                },
                "api_metrics_summary": {
                    "api_calls_made": api_metrics.get("api_calls_made", 0),
                    "tokens_per_api_call": api_metrics.get("tokens_per_api_call", 0),
                    "cache_hit_rate": api_metrics.get("cache_hit_rate_percent", 0),
                    "api_success_rate": api_metrics.get("success_rate_percent", 0),
                    "resource_efficiency_grade": api_metrics.get("resource_efficiency_grade", "Unknown")
                },
                "grade": self._grade_performance(performance_score)
            })
        
        # Sort by performance score
        rankings.sort(key=lambda x: x["performance_score"], reverse=True)
        
        # Add ranks
        for i, ranking in enumerate(rankings):
            ranking["rank"] = i + 1
        
        return rankings
    
    def _analyze_strategy_complementarity(self) -> Dict[str, Any]:
        """Analyze how well strategies complement each other."""
        overlap_matrix = self.comparison_metrics.get("overlap_matrix", {})
        
        # Find best strategy pairs (low overlap, high combined quality)
        strategy_pairs = []
        strategy_names = list(self.strategy_results.keys())
        
        for i, strategy1 in enumerate(strategy_names):
            for j, strategy2 in enumerate(strategy_names[i+1:], i+1):
                overlap = overlap_matrix.get(strategy1, {}).get(strategy2, 0)
                
                # Calculate combined value
                tokens1 = len(self.strategy_results[strategy1]["tokens"])
                tokens2 = len(self.strategy_results[strategy2]["tokens"])
                
                quality1 = self.strategy_results[strategy1].get("individual_analysis", {}).get("quality_analysis", {}).get("avg_quality_score", 0)
                quality2 = self.strategy_results[strategy2].get("individual_analysis", {}).get("quality_analysis", {}).get("avg_quality_score", 0)
                
                complementarity_score = (1 - overlap) * (tokens1 + tokens2) * ((quality1 + quality2) / 200)
                
                strategy_pairs.append({
                    "strategy1": strategy1,
                    "strategy2": strategy2,
                    "overlap": overlap,
                    "complementarity_score": complementarity_score,
                    "combined_tokens": tokens1 + tokens2,
                    "avg_combined_quality": (quality1 + quality2) / 2
                })
        
        # Sort by complementarity score
        strategy_pairs.sort(key=lambda x: x["complementarity_score"], reverse=True)
        
        return {
            "best_pairs": strategy_pairs[:5],  # Top 5 complementary pairs
            "avg_overlap": sum(overlap_matrix[s1][s2] for s1 in overlap_matrix for s2 in overlap_matrix[s1] if s1 != s2) / (len(strategy_names) * (len(strategy_names) - 1)) if len(strategy_names) > 1 else 0
        }
    
    def _compare_token_quality_across_strategies(self) -> Dict[str, Any]:
        """Compare token quality across strategies."""
        all_tokens_by_address = {}
        
        # Collect all tokens with their strategies
        for strategy_name, results in self.strategy_results.items():
            for token in results["tokens"]:
                address = token.get("address")
                if address:
                    if address not in all_tokens_by_address:
                        all_tokens_by_address[address] = {
                            "token": token,
                            "strategies": [],
                            "scores": []
                        }
                    all_tokens_by_address[address]["strategies"].append(strategy_name)
                    all_tokens_by_address[address]["scores"].append(token.get("score", 0))
        
        # Analyze tokens found by multiple strategies
        multi_strategy_tokens = {addr: data for addr, data in all_tokens_by_address.items() if len(data["strategies"]) > 1}
        
        quality_comparison = {
            "total_unique_tokens": len(all_tokens_by_address),
            "multi_strategy_tokens": len(multi_strategy_tokens),
            "single_strategy_tokens": len(all_tokens_by_address) - len(multi_strategy_tokens),
            "cross_validation_rate": len(multi_strategy_tokens) / len(all_tokens_by_address) if all_tokens_by_address else 0
        }
        
        # Analyze quality by discovery count
        quality_by_discovery_count = defaultdict(list)
        for data in all_tokens_by_address.values():
            discovery_count = len(data["strategies"])
            avg_score = sum(data["scores"]) / len(data["scores"]) if data["scores"] else 0
            quality_by_discovery_count[discovery_count].append(avg_score)
        
        quality_comparison["quality_by_discovery_count"] = {
            str(count): {
                "avg_quality": sum(scores) / len(scores) if scores else 0,
                "token_count": len(scores)
            }
            for count, scores in quality_by_discovery_count.items()
        }
        
        return quality_comparison
    
    def _get_all_unique_tokens(self) -> Set[str]:
        """Get all unique token addresses across all strategies."""
        all_addresses = set()
        
        for results in self.strategy_results.values():
            for token in results["tokens"]:
                address = token.get("address")
                if address:
                    all_addresses.add(address)
        
        return all_addresses
    
    async def _generate_comprehensive_report(self) -> Dict[str, Any]:
        """Generate comprehensive analysis report."""
        
        report = {
            "analysis_metadata": {
                "timestamp": self.analysis_timestamp,
                "analysis_date": datetime.fromtimestamp(self.analysis_timestamp).isoformat(),
                "total_strategies": len(self.strategies),
                "successful_strategies": self.comparison_metrics["successful_strategies"],
                "total_unique_tokens": self.comparison_metrics["total_unique_tokens"],
                "scan_id": f"strategy_comparison_{self.analysis_timestamp}"
            },
            
            "individual_strategy_performance": {},
            "cross_strategy_analysis": self.comparison_metrics,
            "performance_ranking": self.comparison_metrics["performance_ranking"],
            "api_optimization_analysis": self.comparison_metrics.get("api_optimization", {}),
            "key_insights": self._generate_key_insights(),
            "recommendations": self._generate_recommendations(),
            "execution_summary": self._generate_execution_summary()
        }
        
        # Add individual strategy details
        for strategy_name, results in self.strategy_results.items():
            report["individual_strategy_performance"][strategy_name] = {
                "execution_successful": results["execution_successful"],
                "error": results.get("error"),
                "basic_stats": {
                    "tokens_found": results["token_count"],
                    "execution_time": results["execution_time"],
                    "tokens_per_second": results.get("individual_analysis", {}).get("efficiency_metrics", {}).get("tokens_per_second", 0)
                },
                "api_metrics": results.get("api_metrics", {}),
                "analysis": results.get("individual_analysis", {})
            }
        
        return report
    
    def _generate_key_insights(self) -> List[str]:
        """Generate key insights from the analysis."""
        insights = []
        
        # Performance insights
        ranking = self.comparison_metrics.get("performance_ranking", [])
        if ranking:
            best_strategy = ranking[0]
            insights.append(f"🏆 Best performing strategy: {best_strategy['strategy']} (Score: {best_strategy['performance_score']:.1f})")
            
            # Add API efficiency insight for best strategy
            api_summary = best_strategy.get("api_metrics_summary", {})
            if api_summary:
                insights.append(f"   📡 API Efficiency: {api_summary.get('tokens_per_api_call', 0):.2f} tokens/call, "
                              f"{api_summary.get('cache_hit_rate', 0):.1f}% cache hit rate")
        
        # Token discovery insights
        total_tokens = self.comparison_metrics["total_unique_tokens"]
        successful_strategies = self.comparison_metrics["successful_strategies"]
        if successful_strategies > 0:
            avg_tokens_per_strategy = total_tokens / successful_strategies
            insights.append(f"📊 Average tokens per strategy: {avg_tokens_per_strategy:.1f}")
        
        # API efficiency insights
        api_insights = self._analyze_api_efficiency_across_strategies()
        if api_insights:
            insights.append(f"⚡ Most API-efficient strategy: {api_insights['most_efficient_strategy']} "
                          f"({api_insights['best_tokens_per_call']:.2f} tokens/call)")
            insights.append(f"📋 Best cache performance: {api_insights['best_cache_strategy']} "
                          f"({api_insights['best_cache_rate']:.1f}% hit rate)")
        
        # Overlap insights
        overlap_matrix = self.comparison_metrics.get("overlap_matrix", {})
        if overlap_matrix:
            avg_overlap = sum(overlap_matrix[s1][s2] for s1 in overlap_matrix for s2 in overlap_matrix[s1] if s1 != s2) / max(1, len(overlap_matrix) * (len(overlap_matrix) - 1))
            insights.append(f"🔄 Average strategy overlap: {avg_overlap:.1%}")
        
        # Quality insights
        quality_comparison = self.comparison_metrics.get("quality_comparison", {})
        cross_validation_rate = quality_comparison.get("cross_validation_rate", 0)
        insights.append(f"✅ Cross-validation rate: {cross_validation_rate:.1%} of tokens found by multiple strategies")
        
        # Complementarity insights
        complementarity = self.comparison_metrics.get("complementarity_analysis", {})
        best_pairs = complementarity.get("best_pairs", [])
        if best_pairs:
            best_pair = best_pairs[0]
            insights.append(f"🤝 Best complementary pair: {best_pair['strategy1']} + {best_pair['strategy2']} (Score: {best_pair['complementarity_score']:.1f})")
        
        # API optimization insights
        api_optimization = self.comparison_metrics.get("api_optimization", {})
        if api_optimization and api_optimization.get("status") != "No data available":
            
            # Cost-benefit insights
            cost_benefit = api_optimization.get("cost_benefit_analysis", {})
            if cost_benefit.get("best_cost_benefit"):
                best_cb = cost_benefit["best_cost_benefit"]
                insights.append(f"💰 Best cost-benefit strategy: {best_cb[0]} (ratio: {best_cb[1]['cost_benefit_ratio']:.2f})")
            
            # Cache optimization insights
            cache_opt = api_optimization.get("cache_optimization", {})
            if isinstance(cache_opt.get("current_performance"), dict):
                cache_perf = cache_opt["current_performance"]
                cache_potential = cache_opt.get("optimization_potential", "")
                insights.append(f"🗄️ Cache efficiency: {cache_perf.get('cache_hit_rate_percent', 0):.1f}% ({cache_potential})")
            
            # Budget allocation insights
            budget_alloc = api_optimization.get("api_budget_allocation", {})
            if budget_alloc.get("budget_optimization_potential"):
                potential = budget_alloc["budget_optimization_potential"]
                insights.append(f"📊 Budget optimization potential: {potential}")
            
            # Rate limiting insights
            rate_limiting = api_optimization.get("rate_limiting_optimization", {})
            if rate_limiting.get("current_performance"):
                rate_perf = rate_limiting["current_performance"]
                rate_grade = rate_perf.get("performance_grade", "Unknown")
                success_rate = rate_perf.get("success_rate_percent", 0)
                insights.append(f"🚦 Rate limiting performance: {success_rate:.1f}% success rate ({rate_grade})")
        
        return insights
    
    def _analyze_api_efficiency_across_strategies(self) -> Dict[str, Any]:
        """Analyze API efficiency across all strategies."""
        efficiency_data = []
        
        for strategy_name, results in self.strategy_results.items():
            if not results["execution_successful"]:
                continue
                
            api_metrics = results.get("api_metrics", {})
            if api_metrics:
                efficiency_data.append({
                    "strategy": strategy_name,
                    "tokens_per_call": api_metrics.get("tokens_per_api_call", 0),
                    "cache_hit_rate": api_metrics.get("cache_hit_rate_percent", 0),
                    "api_calls_made": api_metrics.get("api_calls_made", 0),
                    "success_rate": api_metrics.get("success_rate_percent", 0)
                })
        
        if not efficiency_data:
            return {}
        
        # Find most efficient strategies
        most_efficient = max(efficiency_data, key=lambda x: x["tokens_per_call"])
        best_cache = max(efficiency_data, key=lambda x: x["cache_hit_rate"])
        
        return {
            "most_efficient_strategy": most_efficient["strategy"],
            "best_tokens_per_call": most_efficient["tokens_per_call"],
            "best_cache_strategy": best_cache["strategy"],
            "best_cache_rate": best_cache["cache_hit_rate"],
            "total_api_calls": sum(d["api_calls_made"] for d in efficiency_data),
            "avg_cache_hit_rate": sum(d["cache_hit_rate"] for d in efficiency_data) / len(efficiency_data),
            "avg_tokens_per_call": sum(d["tokens_per_call"] for d in efficiency_data) / len(efficiency_data)
        }
    
    def _generate_recommendations(self) -> List[str]:
        """Generate actionable recommendations."""
        recommendations = []
        
        # Strategy selection recommendations
        ranking = self.comparison_metrics.get("performance_ranking", [])
        if len(ranking) >= 3:
            top_3 = [r["strategy"] for r in ranking[:3]]
            recommendations.append(f"🎯 Prioritize top 3 strategies: {', '.join(top_3)}")
        
        # Complementarity recommendations
        complementarity = self.comparison_metrics.get("complementarity_analysis", {})
        best_pairs = complementarity.get("best_pairs", [])
        if best_pairs:
            best_pair = best_pairs[0]
            recommendations.append(f"🤝 Best strategy combination: {best_pair['strategy1']} + {best_pair['strategy2']}")
        
        # Uniqueness recommendations
        uniqueness = self.comparison_metrics.get("uniqueness_analysis", {})
        most_unique = max(uniqueness.items(), key=lambda x: x[1].get("uniqueness_score", 0)) if uniqueness else None
        if most_unique:
            recommendations.append(f"🎲 Most unique discoveries: {most_unique[0]} ({most_unique[1]['uniqueness_score']:.1%} unique)")
        
        # Quality recommendations
        quality_comparison = self.comparison_metrics.get("quality_comparison", {})
        cross_validation_rate = quality_comparison.get("cross_validation_rate", 0)
        if cross_validation_rate < 0.2:
            recommendations.append("⚠️ Low cross-validation rate suggests strategies are too distinct - consider overlap analysis")
        elif cross_validation_rate > 0.6:
            recommendations.append("🔄 High cross-validation rate suggests strategies may be redundant - consider diversification")
        
        # API optimization recommendations
        api_optimization = self.comparison_metrics.get("api_optimization", {})
        if api_optimization and api_optimization.get("status") != "No data available":
            api_recommendations = api_optimization.get("optimization_recommendations", [])
            if api_recommendations:
                recommendations.append("🔧 API Optimization:")
                for rec in api_recommendations[:3]:  # Add top 3 API recommendations
                    recommendations.append(f"  • {rec}")
            
            # Budget allocation recommendations
            budget_alloc = api_optimization.get("api_budget_allocation", {})
            if budget_alloc.get("budget_optimization_potential") and "High" in budget_alloc["budget_optimization_potential"]:
                recommendations.append("💰 Consider reallocating API budget based on strategy efficiency analysis")
            
            # Cache optimization recommendations
            cache_opt = api_optimization.get("cache_optimization", {})
            if isinstance(cache_opt.get("current_performance"), dict):
                cache_grade = cache_opt["current_performance"].get("efficiency_grade", "")
                if cache_grade in ["Poor", "Fair"]:
                    recommendations.append("🗄️ High priority: Improve caching strategy for better API efficiency")
        
        return recommendations
    
    def _generate_execution_summary(self) -> Dict[str, Any]:
        """Generate execution summary statistics."""
        successful_strategies = [r for r in self.strategy_results.values() if r["execution_successful"]]
        failed_strategies = [r for r in self.strategy_results.values() if not r["execution_successful"]]
        
        execution_times = [r["execution_time"] for r in successful_strategies]
        token_counts = [r["token_count"] for r in successful_strategies]
        
        return {
            "total_strategies": len(self.strategy_results),
            "successful_executions": len(successful_strategies),
            "failed_executions": len(failed_strategies),
            "success_rate": len(successful_strategies) / len(self.strategy_results) if self.strategy_results else 0,
            "total_execution_time": sum(execution_times),
            "avg_execution_time": sum(execution_times) / len(execution_times) if execution_times else 0,
            "total_tokens_found": sum(token_counts),
            "avg_tokens_per_strategy": sum(token_counts) / len(token_counts) if token_counts else 0,
            "failed_strategies": [{"strategy": name, "error": results["error"]} for name, results in self.strategy_results.items() if not results["execution_successful"]]
        }
    
    # Helper grading functions
    def _grade_overall_quality(self, avg_score: float) -> str:
        if avg_score >= 85: return "A+"
        elif avg_score >= 80: return "A"
        elif avg_score >= 75: return "B+"
        elif avg_score >= 70: return "B"
        elif avg_score >= 65: return "C+"
        elif avg_score >= 60: return "C"
        else: return "D"
    
    def _grade_risk_level(self, avg_risk_score: float) -> str:
        if avg_risk_score >= 80: return "High Risk"
        elif avg_risk_score >= 60: return "Medium Risk"
        elif avg_risk_score >= 40: return "Low-Medium Risk"
        else: return "Low Risk"
    
    def _grade_efficiency(self, execution_time: float, token_count: int) -> str:
        tokens_per_second = token_count / execution_time if execution_time > 0 else 0
        if tokens_per_second >= 5: return "Excellent"
        elif tokens_per_second >= 2: return "Good"
        elif tokens_per_second >= 1: return "Fair"
        else: return "Slow"
    
    def _grade_uniqueness(self, uniqueness_score: float) -> str:
        if uniqueness_score >= 0.8: return "Highly Unique"
        elif uniqueness_score >= 0.6: return "Moderately Unique"
        elif uniqueness_score >= 0.4: return "Somewhat Unique"
        else: return "Low Uniqueness"
    
    def _grade_performance(self, performance_score: float) -> str:
        if performance_score >= 85: return "Excellent"
        elif performance_score >= 75: return "Very Good"
        elif performance_score >= 65: return "Good"
        elif performance_score >= 55: return "Fair"
        else: return "Needs Improvement"
    
    def _grade_api_efficiency(self, tokens_per_api_call: float, cache_hit_rate: float, success_rate: float) -> str:
        """Grade API efficiency based on tokens per call, cache performance, and success rate."""
        efficiency_score = (tokens_per_api_call * 20) + (cache_hit_rate * 0.5) + (success_rate * 0.3)
        
        if efficiency_score >= 90: return "Excellent"
        elif efficiency_score >= 75: return "Very Good"
        elif efficiency_score >= 60: return "Good"
        elif efficiency_score >= 45: return "Fair"
        else: return "Poor"
    
    def _grade_api_health(self, success_rate: float, avg_response_time: float) -> str:
        """Grade API health based on success rate and response time."""
        if success_rate >= 95 and avg_response_time < 1000:
            return "Excellent" 
        elif success_rate >= 90 and avg_response_time < 2000:
            return "Good"
        elif success_rate >= 80 and avg_response_time < 5000:
            return "Fair"
        elif success_rate >= 60:
            return "Poor"
        else:
            return "Critical"
    
    def _categorize_market_caps(self, market_caps: List[float]) -> Dict[str, int]:
        ranges = {
            "micro": 0,      # < $1M
            "small": 0,      # $1M - $10M
            "medium": 0,     # $10M - $100M
            "large": 0,      # $100M - $1B
            "mega": 0        # > $1B
        }
        
        for mcap in market_caps:
            if mcap < 1_000_000:
                ranges["micro"] += 1
            elif mcap < 10_000_000:
                ranges["small"] += 1
            elif mcap < 100_000_000:
                ranges["medium"] += 1
            elif mcap < 1_000_000_000:
                ranges["large"] += 1
            else:
                ranges["mega"] += 1
        
        return ranges
    
    def _categorize_ages(self, ages: List[float]) -> Dict[str, int]:
        ranges = {
            "very_new": 0,   # < 1 day
            "new": 0,        # 1-7 days
            "recent": 0,     # 7-30 days
            "established": 0, # 30-90 days
            "mature": 0      # > 90 days
        }
        
        for age in ages:
            if age < 1:
                ranges["very_new"] += 1
            elif age < 7:
                ranges["new"] += 1
            elif age < 30:
                ranges["recent"] += 1
            elif age < 90:
                ranges["established"] += 1
            else:
                ranges["mature"] += 1
        
        return ranges
    
    def _calculate_diversity_score(self, mcap_ranges: Dict[str, int], age_ranges: Dict[str, int]) -> float:
        mcap_diversity = len([v for v in mcap_ranges.values() if v > 0]) / len(mcap_ranges)
        age_diversity = len([v for v in age_ranges.values() if v > 0]) / len(age_ranges)
        return (mcap_diversity + age_diversity) / 2
    
    async def _save_analysis_results(self, report: Dict[str, Any]):
        """Save analysis results to file."""
        try:
            # Create results directory
            results_dir = Path("scripts/results")
            results_dir.mkdir(exist_ok=True)
            
            # Save comprehensive report
            timestamp_str = datetime.fromtimestamp(self.analysis_timestamp).strftime("%Y%m%d_%H%M%S")
            report_file = results_dir / f"comprehensive_strategy_comparison_v4_{timestamp_str}.json"
            
            with open(report_file, 'w') as f:
                json.dump(report, f, indent=2, default=str)
            
            self.logger.info(f"📊 Report saved to: {report_file}")
            
            # Save summary report (key metrics only)
            summary_report = {
                "timestamp": report["analysis_metadata"]["timestamp"],
                "analysis_date": report["analysis_metadata"]["analysis_date"],
                "performance_ranking": report["performance_ranking"],
                "key_insights": report["key_insights"],
                "recommendations": report["recommendations"],
                "execution_summary": report["execution_summary"]
            }
            
            summary_file = results_dir / f"strategy_comparison_summary_v4_{timestamp_str}.json"
            with open(summary_file, 'w') as f:
                json.dump(summary_report, f, indent=2, default=str)
            
            self.logger.info(f"📋 Summary saved to: {summary_file}")
            
        except Exception as e:
            self.logger.error(f"Error saving results: {e}")


async def main():
    """Main function to run comprehensive strategy comparison."""
    print("🚀 Starting Comprehensive Strategy Comparison V4")
    print("=" * 80)
    
    try:
        analyzer = StrategyComparisonAnalyzer()
        report = await analyzer.run_comprehensive_comparison()
        
        # Print summary to console
        print("\n" + "=" * 80)
        print("📊 COMPREHENSIVE STRATEGY COMPARISON RESULTS")
        print("=" * 80)
        
        # Performance ranking
        print("\n🏆 STRATEGY PERFORMANCE RANKING:")
        for ranking in report["performance_ranking"]:
            print(f"  {ranking['rank']}. {ranking['strategy']}")
            print(f"     Score: {ranking['performance_score']:.1f} | Grade: {ranking['grade']}")
            
            # Add API efficiency details
            api_summary = ranking.get("api_metrics_summary", {})
            if api_summary:
                print(f"     📡 API: {api_summary.get('api_calls_made', 0)} calls, "
                      f"{api_summary.get('tokens_per_api_call', 0):.2f} tokens/call, "
                      f"{api_summary.get('cache_hit_rate', 0):.1f}% cache hit rate")
        
        # Key insights
        print("\n💡 KEY INSIGHTS:")
        for insight in report["key_insights"]:
            print(f"  • {insight}")
        
        # Recommendations
        print("\n🎯 RECOMMENDATIONS:")
        for rec in report["recommendations"]:
            print(f"  • {rec}")
        
        # Execution summary
        exec_summary = report["execution_summary"]
        print(f"\n⏱️  EXECUTION SUMMARY:")
        print(f"  • Strategies executed: {exec_summary['successful_executions']}/{exec_summary['total_strategies']}")
        print(f"  • Total execution time: {exec_summary['total_execution_time']:.1f}s")
        print(f"  • Total unique tokens found: {exec_summary['total_tokens_found']}")
        print(f"  • Average tokens per strategy: {exec_summary['avg_tokens_per_strategy']:.1f}")
        
        # API optimization summary
        api_optimization = report.get("api_optimization_analysis", {})
        if api_optimization and api_optimization.get("status") != "No data available":
            print(f"\n🔧 API OPTIMIZATION SUMMARY:")
            
            # Cache performance
            cache_opt = api_optimization.get("cache_optimization", {})
            if isinstance(cache_opt.get("current_performance"), dict):
                cache_perf = cache_opt["current_performance"]
                print(f"  • Cache hit rate: {cache_perf.get('cache_hit_rate_percent', 0):.1f}% ({cache_perf.get('efficiency_grade', 'Unknown')})")
            
            # Best cost-benefit strategy
            cost_benefit = api_optimization.get("cost_benefit_analysis", {})
            if cost_benefit.get("best_cost_benefit"):
                best_cb = cost_benefit["best_cost_benefit"]
                print(f"  • Best cost-benefit: {best_cb[0]} (ratio: {best_cb[1]['cost_benefit_ratio']:.2f})")
            
            # Endpoint efficiency
            endpoint_eff = api_optimization.get("endpoint_efficiency", {})
            if endpoint_eff.get("most_efficient_endpoint"):
                print(f"  • Most efficient endpoint: {endpoint_eff['most_efficient_endpoint']}")
                print(f"  • Total endpoints used: {endpoint_eff.get('total_endpoints_used', 0)}")
            
            # Top optimization recommendations
            recommendations = api_optimization.get("optimization_recommendations", [])
            if recommendations:
                print(f"  • Top recommendations: {len(recommendations)} generated")
        
        print("\n✅ Analysis complete! Check scripts/results/ for detailed reports.")
        
    except Exception as e:
        print(f"❌ Error in main execution: {e}")
        raise


if __name__ == "__main__":
    asyncio.run(main()) 