#!/usr/bin/env python3
"""
Improved Batch API Manager
True batch processing with intelligent rate limiting and token validation
"""

import asyncio
import logging
import time
import json
from typing import Dict, List, Any, Optional, Set, Tuple
from dataclasses import dataclass
from enum import Enum
import hashlib

from api.birdeye_connector import BirdeyeAPI
from utils.token_validator import EnhancedTokenValidator
from utils.enhanced_structured_logger import create_enhanced_logger, APICallType


class BatchStrategy(Enum):
    """Batch processing strategies"""
    TRUE_BATCH = "true_batch"  # Use actual batch endpoints
    PARALLEL_INDIVIDUAL = "parallel_individual"  # Parallel individual calls
    SEQUENTIAL_SAFE = "sequential_safe"  # Sequential with delays (fallback)


@dataclass
class BatchConfig:
    """Batch processing configuration"""
    max_batch_size: int = 50
    max_concurrent_requests: int = 5
    request_delay_ms: int = 100
    enable_caching: bool = True
    enable_validation: bool = True
    retry_failed_individually: bool = True
    fallback_strategy: BatchStrategy = BatchStrategy.PARALLEL_INDIVIDUAL


@dataclass
class BatchStats:
    """Batch processing statistics"""
    total_requests: int = 0
    successful_batches: int = 0
    failed_batches: int = 0
    tokens_processed: int = 0
    tokens_validated: int = 0
    tokens_filtered: int = 0
    api_calls_made: int = 0
    api_calls_saved: int = 0
    total_time_ms: float = 0
    average_batch_time_ms: float = 0


class ImprovedBatchAPIManager:
    """
    Improved Batch API Manager with True Batching
    
    Key Features:
    - True batch API calls when available
    - Intelligent fallback to parallel processing
    - Comprehensive token validation before API calls
    - Advanced caching with TTL management
    - Rate limiting protection
    - Detailed performance metrics
    - Error handling and retry logic
    """
    
    def __init__(self, 
                 birdeye_api: BirdeyeAPI, 
                 logger: logging.Logger,
                 config: Optional[BatchConfig] = None):
        
        self.birdeye_api = birdeye_api
        self.logger = logger
        self.enhanced_logger = create_enhanced_logger('ImprovedBatchAPIManager')
        
        # Configuration
        self.config = config or BatchConfig()
        
        # Token validator
        self.token_validator = EnhancedTokenValidator(logger)
        
        # Batch processing statistics
        self.stats = BatchStats()
        
        # Cache management
        self.cache = {}
        self.cache_ttl = {}
        self.default_cache_ttl = 300  # 5 minutes
        
        # Rate limiting
        self.last_request_time = 0
        self.requests_this_minute = 0
        self.minute_start_time = time.time()
        
        # API endpoint capabilities (detected at runtime)
        self.api_capabilities = {
            "supports_batch_price": None,  # Will be detected
            "supports_batch_metadata": None,  # Will be detected
            "max_batch_size": 50  # Conservative default
        }
        
        # Enhanced initialization logging with structured context
        self.enhanced_logger.info("Batch API Manager ready for operations",
                                batch_features={
                                    "true_batching": True,
                                    "parallel_processing": True,
                                    "intelligent_caching": self.config.enable_caching,
                                    "token_validation": self.config.enable_validation,
                                    "rate_limiting": True
                                },
                                session_id=self.session_id)
        
        self.logger.info("🚀 Improved Batch API Manager initialized")
        self.logger.info(f"   📊 Max batch size: {self.config.max_batch_size}")
        self.logger.info(f"   ⚡ Max concurrent: {self.config.max_concurrent_requests}")
        self.logger.info(f"   🔍 Validation enabled: {self.config.enable_validation}")
        self.logger.info(f"   💾 Caching enabled: {self.config.enable_caching}")
    
    async def batch_fetch_token_metadata(self, 
                                       token_addresses: List[str],
                                       scan_id: Optional[str] = None) -> Dict[str, Any]:
        """
        Fetch token metadata using optimal batching strategy
        
        Args:
            token_addresses: List of token addresses
            scan_id: Optional scan ID for tracking
            
        Returns:
            Dictionary mapping token address to metadata
        """
        start_time = time.time()
        
        if not token_addresses:
            return {}
        
        
        with self.enhanced_logger.api_call_context(
            APICallType.BATCH_METADATA, 
            endpoint="batch_fetch_token_metadata",
            token_count=len(token_addresses),
            session_id=self.session_id,
            scan_id=scan_id
        ):
            self.enhanced_logger.info("Starting batch metadata fetch",
                                    token_count=len(token_addresses),
                                    validation_enabled=self.config.enable_validation,
                                    caching_enabled=self.config.enable_caching,
                                    debug_mode=self.debug_mode)
            
            if self.debug_mode:
                self.enhanced_logger.debug("Batch fetch configuration",
                                         max_batch_size=self.config.max_batch_size,
                                         max_concurrent=self.config.max_concurrent_requests,
                                         fallback_strategy=self.config.fallback_strategy.value)
            
            self.logger.info(f"🔍 Starting batch metadata fetch for {len(token_addresses)} tokens")
        
        # Step 1: Validate tokens if enabled
        valid_tokens = token_addresses
        validation_report = {}
        
        if self.config.enable_validation:
            valid_tokens, validation_report = self.token_validator.validate_token_batch(
                token_addresses,
                enable_format_check=True,
                enable_exclusion_check=True,
                enable_duplicate_check=True
            )
            
            if validation_report["filtered_count"] > 0:
                self.enhanced_logger.info("Token validation completed",
                                        original_count=len(token_addresses),
                                        valid_count=len(valid_tokens),
                                        filtered_count=validation_report['filtered_count'],
                                        validation_details=validation_report if self.debug_mode else None)
                
                self.logger.info(f"🔍 Validation filtered {validation_report['filtered_count']} "
                               f"tokens, {len(valid_tokens)} remaining")
        
        if not valid_tokens:
            self.logger.warning("No valid tokens remaining after validation")
            return {}
        
        # Step 2: Check cache for existing data
        cached_data = {}
        tokens_to_fetch = []
        
        if self.config.enable_caching:
            for token in valid_tokens:
                cached_metadata = self._get_cached_data(f"metadata_{token}")
                if cached_metadata:
                    cached_data[token] = cached_metadata
                else:
                    tokens_to_fetch.append(token)
            
            if cached_data:
                self.logger.info(f"💾 Found cached data for {len(cached_data)} tokens")
        else:
            tokens_to_fetch = valid_tokens
        
        # Step 3: Fetch remaining tokens using optimal strategy
        fetched_data = {}
        if tokens_to_fetch:
            strategy = await self._determine_batch_strategy("metadata")
            fetched_data = await self._fetch_with_strategy(
                tokens_to_fetch, 
                "metadata", 
                strategy,
                scan_id
            )
            
            # Cache new data
            if self.config.enable_caching:
                for token, data in fetched_data.items():
                    if data:
                        self._set_cached_data(f"metadata_{token}", data, ttl=600)  # 10 minutes for metadata
        
        # Step 4: Combine results
        all_results = {**cached_data, **fetched_data}
        
        # Update statistics
        batch_time = (time.time() - start_time) * 1000
        self._update_batch_stats(
            tokens_processed=len(token_addresses),
            tokens_validated=len(valid_tokens),
            tokens_filtered=len(token_addresses) - len(valid_tokens),
            api_calls_made=len(tokens_to_fetch),
            api_calls_saved=len(cached_data) + validation_report.get("filtered_count", 0),
            batch_time_ms=batch_time
        )
        
        # Log results
        self.structured_logger.info({
            "event": "improved_batch_complete",
            "endpoint": "metadata",
            "total_input": len(token_addresses),
            "valid_tokens": len(valid_tokens),
            "cached_results": len(cached_data),
            "api_calls_made": len(tokens_to_fetch),
            "successful_results": len(all_results),
            "batch_time_ms": round(batch_time, 2),
            "scan_id": scan_id
        })
        
        self.logger.info(f"✅ Batch metadata fetch complete: {len(all_results)}/{len(token_addresses)} "
                        f"successful in {batch_time:.1f}ms")
        
        return all_results
    
    async def batch_fetch_token_prices(self, 
                                     token_addresses: List[str],
                                     scan_id: Optional[str] = None) -> Dict[str, Any]:
        """
        Fetch token prices using optimal batching strategy
        """
        start_time = time.time()
        
        if not token_addresses:
            return {}
        
        self.logger.info(f"💰 Starting batch price fetch for {len(token_addresses)} tokens")
        
        # Validation and caching (similar to metadata)
        valid_tokens = token_addresses
        if self.config.enable_validation:
            valid_tokens, validation_report = self.token_validator.validate_token_batch(token_addresses)
        
        cached_data = {}
        tokens_to_fetch = valid_tokens
        
        if self.config.enable_caching:
            for token in valid_tokens:
                cached_price = self._get_cached_data(f"price_{token}")
                if cached_price:
                    cached_data[token] = cached_price
                else:
                    tokens_to_fetch.append(token)
            tokens_to_fetch = [t for t in valid_tokens if t not in cached_data]
        
        # Fetch prices using optimal strategy
        fetched_data = {}
        if tokens_to_fetch:
            strategy = await self._determine_batch_strategy("price")
            fetched_data = await self._fetch_with_strategy(
                tokens_to_fetch, 
                "price", 
                strategy,
                scan_id
            )
            
            # Cache with shorter TTL for prices (more volatile)
            if self.config.enable_caching:
                for token, data in fetched_data.items():
                    if data:
                        self._set_cached_data(f"price_{token}", data, ttl=30)  # 30 seconds for prices
        
        all_results = {**cached_data, **fetched_data}
        
        # Statistics and logging
        batch_time = (time.time() - start_time) * 1000
        self._update_batch_stats(
            tokens_processed=len(token_addresses),
            api_calls_made=len(tokens_to_fetch),
            api_calls_saved=len(cached_data),
            batch_time_ms=batch_time
        )
        
        self.logger.info(f"✅ Batch price fetch complete: {len(all_results)}/{len(token_addresses)} "
                        f"successful in {batch_time:.1f}ms")
        
        return all_results
    
    async def _determine_batch_strategy(self, endpoint_type: str) -> BatchStrategy:
        """
        Determine the optimal batching strategy for the given endpoint
        """
        # Check if we've already detected API capabilities
        if endpoint_type == "metadata" and self.api_capabilities["supports_batch_metadata"] is not None:
            return BatchStrategy.TRUE_BATCH if self.api_capabilities["supports_batch_metadata"] else BatchStrategy.PARALLEL_INDIVIDUAL
        
        if endpoint_type == "price" and self.api_capabilities["supports_batch_price"] is not None:
            return BatchStrategy.TRUE_BATCH if self.api_capabilities["supports_batch_price"] else BatchStrategy.PARALLEL_INDIVIDUAL
        
        # Try to detect batch endpoint availability
        await self._detect_api_capabilities()
        
        # Return appropriate strategy based on detected capabilities
        if endpoint_type == "metadata":
            return BatchStrategy.TRUE_BATCH if self.api_capabilities["supports_batch_metadata"] else BatchStrategy.PARALLEL_INDIVIDUAL
        elif endpoint_type == "price":
            return BatchStrategy.TRUE_BATCH if self.api_capabilities["supports_batch_price"] else BatchStrategy.PARALLEL_INDIVIDUAL
        
        return self.config.fallback_strategy
    
    async def _detect_api_capabilities(self):
        """
        Detect which batch endpoints are available in the current API plan
        """
        self.logger.debug("🔍 Detecting API batch capabilities...")
        
        # Test a small batch to detect capabilities
        test_addresses = ['So11111111111111111111111111111111111111112']  # WSOL
        
        # Test batch price endpoint
        try:
            # Try actual batch endpoint if available
            if hasattr(self.birdeye_api, 'get_multi_token_price'):
                result = await self.birdeye_api.get_multi_token_price(test_addresses[:1])
                self.api_capabilities["supports_batch_price"] = result is not None
            else:
                self.api_capabilities["supports_batch_price"] = False
        except Exception as e:
            if "404" in str(e) or "not found" in str(e).lower():
                self.api_capabilities["supports_batch_price"] = False
            else:
                self.api_capabilities["supports_batch_price"] = None  # Unknown, will retry
        
        # Test batch metadata endpoint
        try:
            if hasattr(self.birdeye_api, 'get_batch_token_metadata'):
                result = await self.birdeye_api.get_batch_token_metadata(test_addresses[:1])
                self.api_capabilities["supports_batch_metadata"] = result is not None
            else:
                self.api_capabilities["supports_batch_metadata"] = False
        except Exception as e:
            if "404" in str(e) or "not found" in str(e).lower():
                self.api_capabilities["supports_batch_metadata"] = False
            else:
                self.api_capabilities["supports_batch_metadata"] = None
        
        self.logger.info(f"🔍 API Capabilities detected:")
        self.logger.info(f"   💰 Batch price: {'✅' if self.api_capabilities['supports_batch_price'] else '❌'}")
        self.logger.info(f"   📊 Batch metadata: {'✅' if self.api_capabilities['supports_batch_metadata'] else '❌'}")
    
    async def _fetch_with_strategy(self, 
                                 token_addresses: List[str], 
                                 endpoint_type: str,
                                 strategy: BatchStrategy,
                                 scan_id: Optional[str] = None) -> Dict[str, Any]:
        """
        Fetch data using the specified strategy
        """
        if strategy == BatchStrategy.TRUE_BATCH:
            return await self._fetch_true_batch(token_addresses, endpoint_type, scan_id)
        elif strategy == BatchStrategy.PARALLEL_INDIVIDUAL:
            return await self._fetch_parallel_individual(token_addresses, endpoint_type, scan_id)
        else:  # SEQUENTIAL_SAFE
            return await self._fetch_sequential_safe(token_addresses, endpoint_type, scan_id)
    
    async def _fetch_true_batch(self, 
                              token_addresses: List[str], 
                              endpoint_type: str,
                              scan_id: Optional[str] = None) -> Dict[str, Any]:
        """
        Fetch data using true batch API endpoints
        """
        self.logger.info(f"🚀 Using TRUE BATCH strategy for {len(token_addresses)} {endpoint_type} requests")
        
        results = {}
        batch_size = min(self.config.max_batch_size, self.api_capabilities["max_batch_size"])
        
        # Process in batches
        for i in range(0, len(token_addresses), batch_size):
            batch = token_addresses[i:i + batch_size]
            
            try:
                await self._apply_rate_limiting()
                
                if endpoint_type == "price":
                    batch_result = await self.birdeye_api.get_multi_token_price(batch)
                elif endpoint_type == "metadata":
                    batch_result = await self.birdeye_api.get_batch_token_metadata(batch)
                else:
                    continue
                
                if batch_result:
                    results.update(batch_result)
                
                self.logger.debug(f"✅ Batch {i//batch_size + 1} completed: {len(batch)} tokens")
                
            except Exception as e:
                self.logger.warning(f"❌ Batch {i//batch_size + 1} failed: {e}")
                
                # Fallback to individual requests for this batch
                if self.config.retry_failed_individually:
                    individual_results = await self._fetch_parallel_individual(batch, endpoint_type, scan_id)
                    results.update(individual_results)
        
        return results
    
    async def _fetch_parallel_individual(self, 
                                       token_addresses: List[str], 
                                       endpoint_type: str,
                                       scan_id: Optional[str] = None) -> Dict[str, Any]:
        """
        Fetch data using parallel individual API calls
        """
        self.logger.info(f"⚡ Using PARALLEL INDIVIDUAL strategy for {len(token_addresses)} {endpoint_type} requests")
        
        # Control concurrency to avoid rate limits
        semaphore = asyncio.Semaphore(self.config.max_concurrent_requests)
        
        async def fetch_single(token: str) -> Tuple[str, Optional[Dict]]:
            async with semaphore:
                try:
                    await self._apply_rate_limiting()
                    
                    if endpoint_type == "price":
                        result = await self.birdeye_api.get_token_price(token)
                    elif endpoint_type == "metadata":
                        result = await self.birdeye_api.get_token_metadata_single(token)
                    else:
                        return token, None
                    
                    return token, result
                    
                except Exception as e:
                    self.logger.debug(f"Failed to fetch {endpoint_type} for {token}: {e}")
                    return token, None
        
        # Execute parallel requests
        tasks = [fetch_single(token) for token in token_addresses]
        results_list = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Process results
        results = {}
        successful_count = 0
        for result in results_list:
            if isinstance(result, tuple) and result[1] is not None:
                results[result[0]] = result[1]
                successful_count += 1
            elif isinstance(result, Exception):
                self.logger.warning(f"Exception in parallel fetch: {result}")
        
        self.logger.info(f"✅ Parallel fetch complete: {successful_count}/{len(token_addresses)} successful")
        return results
    
    async def _fetch_sequential_safe(self, 
                                   token_addresses: List[str], 
                                   endpoint_type: str,
                                   scan_id: Optional[str] = None) -> Dict[str, Any]:
        """
        Fetch data using sequential requests with delays (safest but slowest)
        """
        self.logger.info(f"🐌 Using SEQUENTIAL SAFE strategy for {len(token_addresses)} {endpoint_type} requests")
        
        results = {}
        
        for i, token in enumerate(token_addresses):
            try:
                await self._apply_rate_limiting()
                await asyncio.sleep(self.config.request_delay_ms / 1000.0)
                
                if endpoint_type == "price":
                    result = await self.birdeye_api.get_token_price(token)
                elif endpoint_type == "metadata":
                    result = await self.birdeye_api.get_token_metadata_single(token)
                else:
                    continue
                
                if result:
                    results[token] = result
                
                if (i + 1) % 10 == 0:  # Log progress every 10 requests
                    self.logger.debug(f"Sequential progress: {i + 1}/{len(token_addresses)}")
                    
            except Exception as e:
                self.logger.debug(f"Failed to fetch {endpoint_type} for {token}: {e}")
        
        return results
    
    async def _apply_rate_limiting(self):
        """Apply intelligent rate limiting"""
        current_time = time.time()
        
        # Reset counter every minute
        if current_time - self.minute_start_time >= 60:
            self.requests_this_minute = 0
            self.minute_start_time = current_time
        
        # Check if we need to wait
        time_since_last = current_time - self.last_request_time
        min_interval = 60.0 / 800  # 800 requests per minute max
        
        if time_since_last < min_interval:
            sleep_time = min_interval - time_since_last
            await asyncio.sleep(sleep_time)
        
        self.last_request_time = time.time()
        self.requests_this_minute += 1
    
    def _get_cached_data(self, key: str) -> Optional[Any]:
        """Get data from cache if not expired"""
        if key not in self.cache:
            return None
            
        if key in self.cache_ttl and time.time() > self.cache_ttl[key]:
            # Cache expired
            del self.cache[key]
            del self.cache_ttl[key]
            return None
            
        return self.cache[key]
    
    def _set_cached_data(self, key: str, data: Any, ttl: Optional[int] = None):
        """Set data in cache with TTL"""
        self.cache[key] = data
        if ttl:
            self.cache_ttl[key] = time.time() + ttl
        else:
            self.cache_ttl[key] = time.time() + self.default_cache_ttl
    
    def _update_batch_stats(self, **kwargs):
        """Update batch processing statistics"""
        for key, value in kwargs.items():
            if hasattr(self.stats, key):
                current_value = getattr(self.stats, key)
                setattr(self.stats, key, current_value + value)
    
    def get_performance_stats(self) -> Dict[str, Any]:
        """Get comprehensive performance statistics"""
        return {
            "batch_stats": {
                "total_requests": self.stats.total_requests,
                "successful_batches": self.stats.successful_batches,
                "failed_batches": self.stats.failed_batches,
                "success_rate": round(self.stats.successful_batches / max(self.stats.total_requests, 1) * 100, 2)
            },
            "token_processing": {
                "tokens_processed": self.stats.tokens_processed,
                "tokens_validated": self.stats.tokens_validated,
                "tokens_filtered": self.stats.tokens_filtered,
                "validation_rate": round(self.stats.tokens_validated / max(self.stats.tokens_processed, 1) * 100, 2)
            },
            "api_efficiency": {
                "api_calls_made": self.stats.api_calls_made,
                "api_calls_saved": self.stats.api_calls_saved,
                "efficiency_ratio": round(self.stats.api_calls_saved / max(self.stats.api_calls_made + self.stats.api_calls_saved, 1) * 100, 2)
            },
            "performance_metrics": {
                "total_time_ms": round(self.stats.total_time_ms, 2),
                "average_batch_time_ms": round(self.stats.average_batch_time_ms, 2)
            },
            "validation_stats": self.token_validator.get_validation_stats(),
            "api_capabilities": self.api_capabilities
        }