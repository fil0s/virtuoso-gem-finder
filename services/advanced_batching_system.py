#!/usr/bin/env python3
"""
Advanced Batching System with Priority Queuing
Intelligent batching for OHLCV requests with priority-based processing
"""

import asyncio
import time
import logging
from typing import Dict, List, Any, Optional, Tuple, Callable
from dataclasses import dataclass, field
from enum import Enum
from collections import defaultdict, deque
import heapq

logger = logging.getLogger(__name__)

class Priority(Enum):
    """Request priority levels"""
    CRITICAL = 1    # Must process immediately
    HIGH = 2        # High-conviction tokens
    NORMAL = 3      # Standard processing
    LOW = 4         # Background processing
    BATCH_ONLY = 5  # Only process in batch

@dataclass
class BatchRequest:
    """Individual request in the batch queue"""
    token_address: str
    timeframe: str
    priority: Priority
    created_at: float
    callback: Optional[Callable] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    retry_count: int = 0
    max_retries: int = 3
    
    def __lt__(self, other):
        """Priority queue comparison (lower enum value = higher priority)"""
        if self.priority.value != other.priority.value:
            return self.priority.value < other.priority.value
        return self.created_at < other.created_at

@dataclass
class BatchResult:
    """Result from a batch request"""
    token_address: str
    timeframe: str
    data: Any
    success: bool
    error: Optional[str] = None
    processing_time: float = 0.0
    batch_id: Optional[str] = None

class OHLCVBatcher:
    """
    Advanced OHLCV request batcher with intelligent grouping and priority handling.
    
    Features:
    - Priority-based queuing
    - Timeframe-aware batching
    - Adaptive batch sizing
    - Smart retry logic
    - Rate limit coordination
    """
    
    def __init__(self, api_client, config: Dict = None):
        """Initialize OHLCV batcher"""
        
        default_config = {
            'max_batch_size': 10,           # Maximum requests per batch
            'batch_timeout': 2.0,           # Seconds to wait before forcing batch
            'priority_batch_size': 5,       # Smaller batches for high priority
            'timeframe_grouping': True,     # Group by timeframe for efficiency
            'adaptive_sizing': True,        # Adapt batch size based on performance
            'max_concurrent_batches': 3,    # Maximum parallel batches
            'retry_delays': [1, 2, 4],      # Retry delays in seconds
        }
        
        self.config = {**default_config, **(config or {})}
        self.api_client = api_client
        self.logger = logging.getLogger(__name__)
        
        # Request queues (priority queues)
        self.priority_queue = []  # heapq for priority ordering
        self.timeframe_queues = defaultdict(deque)  # Group by timeframe
        
        # Batch management
        self.pending_batches = {}  # batch_id -> Future
        self.batch_results = {}    # batch_id -> List[BatchResult]
        self.batch_counter = 0
        
        # Performance tracking
        self.stats = {
            'total_requests': 0,
            'batched_requests': 0,
            'priority_requests': 0,
            'failed_requests': 0,
            'average_batch_size': 0,
            'processing_times': deque(maxlen=100)
        }
        
        # Control flags
        self.processing_active = False
        self.shutdown_requested = False
        
        # Start background processing
        self.processing_task = asyncio.create_task(self._process_batches())
    
    async def add_request(self, token_address: str, timeframe: str = 'auto', 
                         priority: Priority = Priority.NORMAL, 
                         metadata: Dict = None) -> str:
        """
        Add OHLCV request to batch queue.
        
        Args:
            token_address: Token contract address
            timeframe: OHLCV timeframe or 'auto'
            priority: Request priority level
            metadata: Additional request metadata
            
        Returns:
            Request ID for tracking
        """
        if self.shutdown_requested:
            raise RuntimeError("Batcher is shutting down")
        
        request = BatchRequest(
            token_address=token_address,
            timeframe=timeframe,
            priority=priority,
            created_at=time.time(),
            metadata=metadata or {}
        )
        
        # Generate request ID
        request_id = f"{token_address}_{timeframe}_{int(time.time() * 1000)}"
        request.metadata['request_id'] = request_id
        
        # Add to appropriate queue
        if priority in [Priority.CRITICAL, Priority.HIGH]:
            heapq.heappush(self.priority_queue, request)
            self.stats['priority_requests'] += 1
        else:
            self.timeframe_queues[timeframe].append(request)
        
        self.stats['total_requests'] += 1
        
        self.logger.debug(f"📥 Added {priority.name} request for {token_address} ({timeframe})")
        return request_id
    
    async def get_result(self, request_id: str, timeout: float = 30.0) -> Optional[BatchResult]:
        """
        Get result for a specific request.
        
        Args:
            request_id: Request ID from add_request
            timeout: Maximum wait time
            
        Returns:
            BatchResult or None if timeout/not found
        """
        start_time = time.time()
        
        while time.time() - start_time < timeout:
            # Check all batch results
            for batch_id, results in self.batch_results.items():
                for result in results:
                    if result.token_address in request_id:  # Simplified matching
                        return result
            
            await asyncio.sleep(0.1)  # Small delay to prevent busy waiting
        
        return None
    
    async def _process_batches(self):
        """Background task to process batch queues"""
        self.processing_active = True
        
        while not self.shutdown_requested:
            try:
                # Process priority queue first
                if self.priority_queue:
                    await self._process_priority_batch()
                
                # Process timeframe queues
                await self._process_timeframe_batches()
                
                # Small delay to prevent excessive CPU usage
                await asyncio.sleep(0.1)
                
            except Exception as e:
                self.logger.error(f"❌ Error in batch processing: {e}")
                await asyncio.sleep(1.0)  # Longer delay on error
        
        self.processing_active = False
        self.logger.info("🛑 Batch processing stopped")
    
    async def _process_priority_batch(self):
        """Process high-priority requests immediately"""
        if not self.priority_queue:
            return
        
        batch_size = min(
            self.config['priority_batch_size'],
            len(self.priority_queue)
        )
        
        # Extract priority requests
        priority_requests = []
        for _ in range(batch_size):
            if self.priority_queue:
                priority_requests.append(heapq.heappop(self.priority_queue))
        
        if priority_requests:
            await self._execute_batch(priority_requests, 'priority')
    
    async def _process_timeframe_batches(self):
        """Process timeframe-grouped requests"""
        # Process each timeframe queue
        for timeframe, queue in self.timeframe_queues.items():
            if not queue:
                continue
            
            # Determine batch size
            batch_size = self._calculate_batch_size(timeframe, len(queue))
            
            # Check if we should process based on batch size or timeout
            oldest_request_age = time.time() - queue[0].created_at if queue else 0
            should_process = (
                len(queue) >= batch_size or 
                oldest_request_age > self.config['batch_timeout']
            )
            
            if should_process:
                # Extract requests for batch
                batch_requests = []
                for _ in range(min(batch_size, len(queue))):
                    if queue:
                        batch_requests.append(queue.popleft())
                
                if batch_requests:
                    await self._execute_batch(batch_requests, f'timeframe_{timeframe}')
    
    def _calculate_batch_size(self, timeframe: str, queue_length: int) -> int:
        """Calculate optimal batch size based on timeframe and performance"""
        base_size = self.config['max_batch_size']
        
        # Adjust based on timeframe (shorter timeframes = smaller batches for faster processing)
        timeframe_adjustments = {
            '1s': 0.4, '15s': 0.5, '30s': 0.6, '1m': 0.7, '5m': 0.8,
            '15m': 0.9, '30m': 1.0, '1h': 1.1, '2h': 1.2, '4h': 1.3
        }
        
        adjustment = timeframe_adjustments.get(timeframe, 1.0)
        adjusted_size = int(base_size * adjustment)
        
        # Adaptive sizing based on recent performance
        if self.config['adaptive_sizing'] and self.stats['processing_times']:
            avg_time = sum(self.stats['processing_times']) / len(self.stats['processing_times'])
            
            # If processing is slow, reduce batch size
            if avg_time > 5.0:  # > 5 seconds average
                adjusted_size = int(adjusted_size * 0.7)
            elif avg_time < 2.0:  # < 2 seconds average
                adjusted_size = int(adjusted_size * 1.3)
        
        return max(1, min(adjusted_size, queue_length))
    
    async def _execute_batch(self, requests: List[BatchRequest], batch_type: str):
        """Execute a batch of OHLCV requests"""
        if not requests:
            return
        
        batch_id = f"{batch_type}_{self.batch_counter}"
        self.batch_counter += 1
        
        start_time = time.time()
        
        self.logger.info(f"🚀 Executing batch {batch_id} with {len(requests)} requests")
        
        try:
            # Group requests by timeframe for efficient API calls
            timeframe_groups = defaultdict(list)
            for request in requests:
                timeframe_groups[request.timeframe].append(request)
            
            batch_results = []
            
            # Process each timeframe group
            for timeframe, tf_requests in timeframe_groups.items():
                try:
                    # Create parallel tasks for this timeframe
                    tasks = []
                    for request in tf_requests:
                        task = self._process_single_request(request, batch_id)
                        tasks.append(task)
                    
                    # Execute requests in parallel (but rate-limited by adaptive rate limiter)
                    tf_results = await asyncio.gather(*tasks, return_exceptions=True)
                    
                    # Process results
                    for i, result in enumerate(tf_results):
                        if isinstance(result, Exception):
                            batch_results.append(BatchResult(
                                token_address=tf_requests[i].token_address,
                                timeframe=tf_requests[i].timeframe,
                                data=None,
                                success=False,
                                error=str(result),
                                batch_id=batch_id
                            ))
                        else:
                            batch_results.append(result)
                    
                except Exception as e:
                    self.logger.error(f"❌ Error processing timeframe group {timeframe}: {e}")
                    
                    # Create error results for all requests in this group
                    for request in tf_requests:
                        batch_results.append(BatchResult(
                            token_address=request.token_address,
                            timeframe=request.timeframe,
                            data=None,
                            success=False,
                            error=f"Batch processing error: {e}",
                            batch_id=batch_id
                        ))
            
            # Store results
            self.batch_results[batch_id] = batch_results
            
            # Update statistics
            processing_time = time.time() - start_time
            self.stats['processing_times'].append(processing_time)
            self.stats['batched_requests'] += len(requests)
            
            successful_count = sum(1 for r in batch_results if r.success)
            failed_count = len(batch_results) - successful_count
            self.stats['failed_requests'] += failed_count
            
            self.logger.info(f"✅ Batch {batch_id} completed: {successful_count} success, {failed_count} failed ({processing_time:.2f}s)")
            
        except Exception as e:
            self.logger.error(f"❌ Batch {batch_id} failed completely: {e}")
            
            # Create error results for all requests
            error_results = []
            for request in requests:
                error_results.append(BatchResult(
                    token_address=request.token_address,
                    timeframe=request.timeframe,
                    data=None,
                    success=False,
                    error=f"Batch execution error: {e}",
                    batch_id=batch_id
                ))
            
            self.batch_results[batch_id] = error_results
            self.stats['failed_requests'] += len(requests)
    
    async def _process_single_request(self, request: BatchRequest, batch_id: str) -> BatchResult:
        """Process a single OHLCV request"""
        start_time = time.time()
        
        try:
            # Use the enhanced API client method if available
            if hasattr(self.api_client, 'get_ohlcv_data_enhanced'):
                data = await self.api_client.get_ohlcv_data_enhanced(
                    request.token_address,
                    request.timeframe
                )
            else:
                # Fallback to standard method
                data = await self.api_client.get_ohlcv_data(
                    request.token_address,
                    request.timeframe
                )
            
            processing_time = time.time() - start_time
            
            return BatchResult(
                token_address=request.token_address,
                timeframe=request.timeframe,
                data=data,
                success=True,
                processing_time=processing_time,
                batch_id=batch_id
            )
            
        except Exception as e:
            processing_time = time.time() - start_time
            
            self.logger.debug(f"❌ Request failed for {request.token_address}: {e}")
            
            return BatchResult(
                token_address=request.token_address,
                timeframe=request.timeframe,
                data=None,
                success=False,
                error=str(e),
                processing_time=processing_time,
                batch_id=batch_id
            )
    
    def get_queue_stats(self) -> Dict[str, Any]:
        """Get current queue statistics"""
        timeframe_counts = {tf: len(queue) for tf, queue in self.timeframe_queues.items()}
        
        return {
            'priority_queue_size': len(self.priority_queue),
            'timeframe_queues': timeframe_counts,
            'total_queued': len(self.priority_queue) + sum(timeframe_counts.values()),
            'active_batches': len(self.pending_batches),
            'completed_batches': len(self.batch_results),
            'processing_active': self.processing_active
        }
    
    def get_performance_stats(self) -> Dict[str, Any]:
        """Get performance statistics"""
        avg_batch_size = (
            self.stats['batched_requests'] / max(1, len(self.batch_results))
            if self.batch_results else 0
        )
        
        avg_processing_time = (
            sum(self.stats['processing_times']) / len(self.stats['processing_times'])
            if self.stats['processing_times'] else 0
        )
        
        return {
            **self.stats,
            'average_batch_size': avg_batch_size,
            'average_processing_time': avg_processing_time,
            'success_rate': (
                (self.stats['total_requests'] - self.stats['failed_requests']) /
                max(1, self.stats['total_requests'])
            ) * 100
        }
    
    async def shutdown(self, timeout: float = 10.0):
        """Gracefully shutdown the batcher"""
        self.logger.info("🛑 Initiating batcher shutdown...")
        
        self.shutdown_requested = True
        
        # Wait for processing to complete
        try:
            await asyncio.wait_for(self.processing_task, timeout=timeout)
        except asyncio.TimeoutError:
            self.logger.warning("⏰ Batcher shutdown timeout, forcing termination")
            self.processing_task.cancel()
        
        self.logger.info("✅ Batcher shutdown complete")


class PriorityTokenProcessor:
    """
    Priority-based token processing system that integrates with the advanced batcher.
    
    Features:
    - Automatic priority assignment based on token characteristics
    - Dynamic priority adjustment based on market conditions
    - Integration with early exit strategies
    """
    
    def __init__(self, batcher: OHLCVBatcher):
        """Initialize priority processor"""
        self.batcher = batcher
        self.logger = logging.getLogger(__name__)
        
        # Priority scoring weights
        self.priority_weights = {
            'bonding_curve_progress': 0.3,
            'market_cap': 0.2,
            'volume_24h': 0.2,
            'price_change_24h': 0.15,
            'age_hours': 0.1,
            'graduation_imminent': 0.05
        }
    
    def calculate_priority(self, token_data: Dict[str, Any]) -> Priority:
        """
        Calculate processing priority based on token characteristics.
        
        Args:
            token_data: Token metadata and metrics
            
        Returns:
            Priority level for processing
        """
        score = 0
        
        # Bonding curve progress (higher = more urgent)
        bonding_progress = token_data.get('bonding_curve_progress', 0)
        if bonding_progress > 95:
            score += 100 * self.priority_weights['bonding_curve_progress']
        elif bonding_progress > 85:
            score += 80 * self.priority_weights['bonding_curve_progress']
        elif bonding_progress > 75:
            score += 60 * self.priority_weights['bonding_curve_progress']
        
        # Market cap (moderate values preferred)
        market_cap = token_data.get('market_cap', 0)
        if 10000 <= market_cap <= 1000000:  # Sweet spot
            score += 80 * self.priority_weights['market_cap']
        elif market_cap > 1000000:
            score += 40 * self.priority_weights['market_cap']
        
        # Volume (higher = more interest)
        volume_24h = token_data.get('volume_24h', 0)
        if volume_24h > 50000:
            score += 90 * self.priority_weights['volume_24h']
        elif volume_24h > 10000:
            score += 70 * self.priority_weights['volume_24h']
        elif volume_24h > 1000:
            score += 50 * self.priority_weights['volume_24h']
        
        # Price change (significant movements)
        price_change = abs(token_data.get('price_change_24h', 0))
        if price_change > 50:
            score += 90 * self.priority_weights['price_change_24h']
        elif price_change > 20:
            score += 70 * self.priority_weights['price_change_24h']
        
        # Age (newer = higher priority)
        age_hours = token_data.get('age_hours', 999)
        if age_hours < 1:
            score += 100 * self.priority_weights['age_hours']
        elif age_hours < 6:
            score += 80 * self.priority_weights['age_hours']
        elif age_hours < 24:
            score += 60 * self.priority_weights['age_hours']
        
        # Special flags
        if token_data.get('graduation_imminent', False):
            score += 100 * self.priority_weights['graduation_imminent']
        
        # Convert score to priority
        if score >= 80:
            return Priority.CRITICAL
        elif score >= 60:
            return Priority.HIGH
        elif score >= 40:
            return Priority.NORMAL
        else:
            return Priority.LOW
    
    async def process_tokens_with_priority(self, tokens: List[Dict[str, Any]]) -> Dict[str, List[BatchResult]]:
        """
        Process tokens with priority-based ordering.
        
        Args:
            tokens: List of token data dictionaries
            
        Returns:
            Dictionary mapping priority levels to results
        """
        # Calculate priorities and submit requests
        priority_groups = defaultdict(list)
        request_mappings = {}
        
        for token in tokens:
            priority = self.calculate_priority(token)
            priority_groups[priority].append(token)
            
            # Submit OHLCV request
            request_id = await self.batcher.add_request(
                token_address=token['address'],
                timeframe='auto',
                priority=priority,
                metadata={'token_data': token}
            )
            
            request_mappings[request_id] = (token, priority)
        
        self.logger.info(f"📊 Priority distribution: "
                        f"CRITICAL: {len(priority_groups[Priority.CRITICAL])}, "
                        f"HIGH: {len(priority_groups[Priority.HIGH])}, "
                        f"NORMAL: {len(priority_groups[Priority.NORMAL])}, "
                        f"LOW: {len(priority_groups[Priority.LOW])}")
        
        # Wait for results (with timeout)
        results_by_priority = defaultdict(list)
        timeout_per_request = 30.0
        
        for request_id, (token, priority) in request_mappings.items():
            try:
                result = await self.batcher.get_result(request_id, timeout=timeout_per_request)
                if result:
                    results_by_priority[priority].append(result)
                else:
                    # Create timeout result
                    timeout_result = BatchResult(
                        token_address=token['address'],
                        timeframe='auto',
                        data=None,
                        success=False,
                        error='Request timeout'
                    )
                    results_by_priority[priority].append(timeout_result)
                    
            except Exception as e:
                self.logger.error(f"❌ Error getting result for {token['address']}: {e}")
        
        return dict(results_by_priority)