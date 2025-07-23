# Starter Plan Implementation Guide
## Development Plan for Birdeye Starter Plan Optimization

### 🎯 Project Overview
This guide outlines the implementation plan for optimizing the 3-Hour Early Gem Detector to work efficiently within Birdeye Starter Plan constraints while maintaining detection accuracy and performance.

### 📊 Current State Analysis
- **Current Plan**: Birdeye Starter Plan (1,000,000 CU/month)
- **Current Usage**: ~2,500-3,500 CU per 20-minute cycle
- **Monthly Estimate**: ~180,000-252,000 CU (18 cycles × 3 hours)
- **Margin**: 75-82% of monthly allocation used
- **Risk Level**: HIGH (potential overage)

---

## 🚀 Phase 1: Core API Optimization (Week 1)

### 1.1 Batch API Manager Refactoring

**File**: `api/batch_api_manager.py`

**Changes Required**:
```python
# Replace batch endpoints with parallel individual calls
async def batch_multi_price_starter_optimized(self, addresses: List[str]) -> Dict[str, Any]:
    """
    Starter Plan Optimized: Replace batch calls with parallel individual calls
    Reduces CU usage by 60-70% compared to batch endpoints
    """
    semaphore = asyncio.Semaphore(5)  # Limit concurrent requests
    
    async def fetch_single_price(address: str) -> Tuple[str, Optional[Dict]]:
        async with semaphore:
            try:
                # Use individual price endpoint instead of batch
                response = await self.birdeye_api.get_token_price(address)
                return address, response
            except Exception as e:
                self.logger.warning(f"Failed to fetch price for {address}: {e}")
                return address, None
    
    # Execute parallel individual calls
    tasks = [fetch_single_price(addr) for addr in addresses]
    results = await asyncio.gather(*tasks, return_exceptions=True)
    
    # Process results
    successful_results = {}
    for result in results:
        if isinstance(result, tuple) and result[1] is not None:
            successful_results[result[0]] = result[1]
    
    return successful_results
```

**Testing Strategy**:
- Unit tests for parallel execution
- Rate limit simulation tests
- Performance comparison with batch endpoints

### 1.2 Rate Limiting Enhancement

**File**: `services/rate_limiter_service.py`

**Changes Required**:
```python
class StarterPlanRateLimiter:
    """
    Enhanced rate limiter optimized for Starter Plan constraints
    """
    
    def __init__(self):
        # Starter Plan limits
        self.starter_limits = {
            'requests_per_minute': 100,
            'burst_limit': 20,
            'monthly_cu_limit': 1000000
        }
        
        # Track usage
        self.current_minute_requests = 0
        self.current_month_cu = 0
        self.last_reset = time.time()
    
    async def wait_for_slot(self, endpoint: str):
        """Enhanced rate limiting with CU tracking"""
        current_time = time.time()
        
        # Reset minute counter if needed
        if current_time - self.last_reset >= 60:
            self.current_minute_requests = 0
            self.last_reset = current_time
        
        # Check minute limit
        if self.current_minute_requests >= self.starter_limits['requests_per_minute']:
            wait_time = 60 - (current_time - self.last_reset)
            self.logger.warning(f"Rate limit hit, waiting {wait_time:.1f}s")
            await asyncio.sleep(wait_time)
        
        # Check burst limit
        if self.current_minute_requests >= self.starter_limits['burst_limit']:
            await asyncio.sleep(1)  # 1-second delay for burst control
        
        self.current_minute_requests += 1
```

### 1.3 Endpoint Availability Checker

**File**: `api/birdeye_connector.py`

**Changes Required**:
```python
class StarterPlanEndpointManager:
    """
    Manages endpoint availability for Starter Plan
    """
    
    def __init__(self):
        # Starter Plan available endpoints
        self.available_endpoints = {
            'price': '/defi/price',
            'overview': '/defi/token_overview',
            'trending': '/defi/token_trending',
            'metadata': '/defi/token_metadata',
            'security': '/defi/token_security'
        }
        
        # Unavailable endpoints (require Business Plan)
        self.unavailable_endpoints = {
            'batch_price': '/defi/multi_price',
            'batch_overview': '/defi/multi_token_overview',
            'batch_metadata': '/defi/multi_token_metadata'
        }
    
    def is_endpoint_available(self, endpoint: str) -> bool:
        """Check if endpoint is available in Starter Plan"""
        return endpoint in self.available_endpoints.values()
    
    def get_alternative_endpoint(self, unavailable_endpoint: str) -> str:
        """Get individual endpoint alternative for batch endpoint"""
        alternatives = {
            '/defi/multi_price': '/defi/price',
            '/defi/multi_token_overview': '/defi/token_overview',
            '/defi/multi_token_metadata': '/defi/token_metadata'
        }
        return alternatives.get(unavailable_endpoint, unavailable_endpoint)
```

---

## 🔧 Phase 2: Detection Engine Optimization (Week 2)

### 2.1 EarlyGemDetector Parallel Processing

**File**: `early_gem_detector.py`

**Changes Required**:
```python
class StarterPlanOptimizedDetector(EarlyGemDetector):
    """
    Optimized detector for Starter Plan constraints
    """
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.starter_plan_optimizer = StarterPlanOptimizer()
        self.rate_limiter = StarterPlanRateLimiter()
    
    async def discover_early_tokens_starter_optimized(self) -> List[Dict[str, Any]]:
        """
        Optimized discovery for Starter Plan
        """
        # Use semaphore to limit concurrent API calls
        semaphore = asyncio.Semaphore(3)  # Conservative limit
        
        async def discover_with_limit(source_func, *args):
            async with semaphore:
                return await source_func(*args)
        
        # Parallel discovery with rate limiting
        discovery_tasks = [
            discover_with_limit(self._discover_pump_fun_stage0),
            discover_with_limit(self._discover_launchlab_early),
            discover_with_limit(self._fetch_birdeye_trending_tokens)
        ]
        
        results = await asyncio.gather(*discovery_tasks, return_exceptions=True)
        
        # Process results and handle exceptions
        all_candidates = []
        for result in results:
            if isinstance(result, list):
                all_candidates.extend(result)
            elif isinstance(result, Exception):
                self.logger.warning(f"Discovery source failed: {result}")
        
        return all_candidates
```

### 2.2 Token Enrichment Optimization

**File**: `services/token_enrichment_service.py`

**Changes Required**:
```python
class StarterPlanEnrichmentService:
    """
    Optimized token enrichment for Starter Plan
    """
    
    def __init__(self):
        self.cache_manager = EnhancedAPICacheManager()
        self.rate_limiter = StarterPlanRateLimiter()
        self.semaphore = asyncio.Semaphore(2)  # Conservative enrichment limit
    
    async def enrich_tokens_starter_optimized(self, tokens: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Optimized enrichment with individual API calls
        """
        enriched_tokens = []
        
        async def enrich_single_token(token: Dict[str, Any]) -> Dict[str, Any]:
            async with self.semaphore:
                try:
                    # Use individual endpoints instead of batch
                    address = token.get('address')
                    if not address:
                        return token
                    
                    # Parallel individual calls
                    price_task = self._get_token_price(address)
                    overview_task = self._get_token_overview(address)
                    metadata_task = self._get_token_metadata(address)
                    
                    results = await asyncio.gather(
                        price_task, overview_task, metadata_task,
                        return_exceptions=True
                    )
                    
                    # Merge results
                    enriched = token.copy()
                    for result in results:
                        if isinstance(result, dict):
                            enriched.update(result)
                    
                    return enriched
                    
                except Exception as e:
                    self.logger.warning(f"Failed to enrich token {token.get('address')}: {e}")
                    return token
        
        # Process tokens with rate limiting
        tasks = [enrich_single_token(token) for token in tokens]
        enriched_tokens = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Filter out exceptions
        return [token for token in enriched_tokens if isinstance(token, dict)]
```

---

## 📊 Phase 3: Performance Monitoring (Week 3)

### 3.1 CU Usage Tracker

**File**: `services/cu_tracker.py`

**Implementation**:
```python
class StarterPlanCUTracker:
    """
    Tracks Compute Unit usage for Starter Plan optimization
    """
    
    def __init__(self):
        self.monthly_cu_limit = 1000000
        self.current_month_cu = 0
        self.daily_cu_usage = {}
        self.endpoint_cu_tracking = {}
        
    def track_api_call(self, endpoint: str, cu_used: int):
        """Track CU usage for API call"""
        self.current_month_cu += cu_used
        
        # Track by endpoint
        if endpoint not in self.endpoint_cu_tracking:
            self.endpoint_cu_tracking[endpoint] = 0
        self.endpoint_cu_tracking[endpoint] += cu_used
        
        # Track by day
        today = datetime.now().strftime('%Y-%m-%d')
        if today not in self.daily_cu_usage:
            self.daily_cu_usage[today] = 0
        self.daily_cu_usage[today] += cu_used
        
        # Alert if approaching limit
        if self.current_month_cu > self.monthly_cu_limit * 0.8:
            self._alert_high_usage()
    
    def get_usage_summary(self) -> Dict[str, Any]:
        """Get comprehensive usage summary"""
        return {
            'current_month_cu': self.current_month_cu,
            'monthly_limit': self.monthly_cu_limit,
            'usage_percentage': (self.current_month_cu / self.monthly_cu_limit) * 100,
            'daily_usage': self.daily_cu_usage,
            'endpoint_usage': self.endpoint_cu_tracking
        }
    
    def _alert_high_usage(self):
        """Alert when approaching monthly limit"""
        usage_pct = (self.current_month_cu / self.monthly_cu_limit) * 100
        self.logger.warning(f"⚠️ High CU usage: {usage_pct:.1f}% of monthly limit")
```

### 3.2 Performance Dashboard

**File**: `dashboard/starter_plan_dashboard.py`

**Implementation**:
```python
class StarterPlanDashboard:
    """
    Real-time dashboard for Starter Plan monitoring
    """
    
    def __init__(self):
        self.cu_tracker = StarterPlanCUTracker()
        self.rate_limiter = StarterPlanRateLimiter()
    
    async def display_starter_plan_status(self):
        """Display real-time Starter Plan status"""
        usage_summary = self.cu_tracker.get_usage_summary()
        
        print("🚀 STARTER PLAN STATUS")
        print("=" * 50)
        print(f"📊 Monthly CU Usage: {usage_summary['current_month_cu']:,} / {usage_summary['monthly_limit']:,}")
        print(f"📈 Usage Percentage: {usage_summary['usage_percentage']:.1f}%")
        print(f"⚡ Current Minute Requests: {self.rate_limiter.current_minute_requests}")
        print(f"🕒 Time Until Reset: {60 - (time.time() - self.rate_limiter.last_reset):.0f}s")
        
        # Display endpoint usage
        print("\n📋 Endpoint Usage:")
        for endpoint, cu_used in usage_summary['endpoint_usage'].items():
            print(f"  • {endpoint}: {cu_used:,} CU")
```

---

## 🧪 Phase 4: Testing and Validation (Week 4)

### 4.1 Starter Plan Simulation Tests

**File**: `tests/test_starter_plan_optimization.py`

**Implementation**:
```python
import pytest
import asyncio
from unittest.mock import Mock, patch

class TestStarterPlanOptimization:
    """Test suite for Starter Plan optimizations"""
    
    @pytest.mark.asyncio
    async def test_parallel_individual_calls(self):
        """Test that individual calls work correctly in parallel"""
        detector = StarterPlanOptimizedDetector()
        
        # Mock API responses
        with patch.object(detector.birdeye_api, 'get_token_price') as mock_price:
            mock_price.return_value = {'price': 1.0}
            
            # Test parallel execution
            addresses = ['token1', 'token2', 'token3']
            results = await detector._batch_multi_price_starter_optimized(addresses)
            
            assert len(results) == 3
            assert all(addr in results for addr in addresses)
    
    @pytest.mark.asyncio
    async def test_rate_limiting(self):
        """Test rate limiting functionality"""
        rate_limiter = StarterPlanRateLimiter()
        
        # Simulate rapid requests
        start_time = time.time()
        for _ in range(5):
            await rate_limiter.wait_for_slot('/test/endpoint')
        
        # Should not exceed rate limits
        assert rate_limiter.current_minute_requests <= rate_limiter.starter_limits['requests_per_minute']
    
    @pytest.mark.asyncio
    async def test_cu_tracking(self):
        """Test CU usage tracking"""
        cu_tracker = StarterPlanCUTracker()
        
        # Simulate API calls
        cu_tracker.track_api_call('/defi/price', 10)
        cu_tracker.track_api_call('/defi/token_overview', 15)
        
        summary = cu_tracker.get_usage_summary()
        assert summary['current_month_cu'] == 25
        assert summary['usage_percentage'] == 0.0025  # 25/1,000,000
```

### 4.2 Performance Benchmarking

**File**: `tests/benchmark_starter_plan.py`

**Implementation**:
```python
class StarterPlanBenchmark:
    """Benchmark tests for Starter Plan optimizations"""
    
    async def benchmark_cycle_performance(self):
        """Benchmark full detection cycle performance"""
        detector = StarterPlanOptimizedDetector()
        cu_tracker = StarterPlanCUTracker()
        
        # Run detection cycle
        start_time = time.time()
        start_cu = cu_tracker.current_month_cu
        
        results = await detector.run_detection_cycle()
        
        end_time = time.time()
        end_cu = cu_tracker.current_month_cu
        
        # Calculate metrics
        cycle_time = end_time - start_time
        cu_used = end_cu - start_cu
        tokens_found = len(results.get('all_candidates', []))
        
        print(f"📊 Cycle Performance:")
        print(f"  ⏱️ Cycle Time: {cycle_time:.1f}s")
        print(f"  💰 CU Used: {cu_used}")
        print(f"  🪙 Tokens Found: {tokens_found}")
        print(f"  📈 CU per Token: {cu_used/max(1, tokens_found):.1f}")
        
        return {
            'cycle_time': cycle_time,
            'cu_used': cu_used,
            'tokens_found': tokens_found,
            'cu_per_token': cu_used/max(1, tokens_found)
        }
```

---

## 🚀 Phase 5: Deployment and Monitoring (Week 5)

### 5.1 Configuration Updates

**File**: `config/config.starter_plan.yaml`

**Implementation**:
```yaml
STARTER_PLAN_OPTIMIZATION:
  enabled: true
  rate_limiting:
    requests_per_minute: 100
    burst_limit: 20
    semaphore_limit: 3
  caching:
    price_cache_ttl: 30
    overview_cache_ttl: 300
    metadata_cache_ttl: 600
  monitoring:
    cu_alert_threshold: 80  # Alert at 80% of monthly limit
    performance_logging: true
    real_time_dashboard: true

API_OPTIMIZATION:
  use_individual_endpoints: true
  parallel_processing: true
  fallback_strategies: true
  cache_aggressive: true

PERFORMANCE_MONITORING:
  track_cu_usage: true
  track_rate_limits: true
  track_cache_hits: true
  alert_on_high_usage: true
```

### 5.2 Deployment Script

**File**: `scripts/deploy_starter_plan_optimization.sh`

**Implementation**:
```bash
#!/bin/bash

echo "🚀 Deploying Starter Plan Optimization..."

# Backup current configuration
cp config/config.yaml config/config.yaml.backup

# Update configuration for Starter Plan
cp config/config.starter_plan.yaml config/config.yaml

# Run tests
echo "🧪 Running Starter Plan tests..."
python -m pytest tests/test_starter_plan_optimization.py -v

# Run benchmark
echo "📊 Running performance benchmark..."
python tests/benchmark_starter_plan.py

# Deploy with monitoring
echo "🚀 Starting optimized detector..."
python run_3hour_detector.py --starter-plan-mode

echo "✅ Starter Plan optimization deployed successfully!"
```

---

## 📈 Success Metrics and KPIs

### Performance Targets
- **CU Usage**: < 80% of monthly limit (800,000 CU)
- **Cycle Time**: < 15 minutes per cycle
- **Token Discovery**: > 50 tokens per cycle
- **Cache Hit Rate**: > 70% for price data
- **Rate Limit Hits**: < 5% of total requests

### Monitoring Dashboard
- Real-time CU usage tracking
- Rate limit monitoring
- Performance metrics
- Alert system for thresholds

### Rollback Plan
- Configuration backup system
- Quick rollback script
- Performance comparison tools

---

## 🔄 Continuous Improvement

### Weekly Reviews
- Performance analysis
- CU usage optimization
- Rate limit analysis
- User feedback integration

### Monthly Optimization
- Cache strategy refinement
- Endpoint usage analysis
- Cost-benefit analysis
- Plan upgrade evaluation

This implementation plan provides a comprehensive approach to optimizing the 3-Hour Early Gem Detector for Birdeye Starter Plan constraints while maintaining detection accuracy and performance. 