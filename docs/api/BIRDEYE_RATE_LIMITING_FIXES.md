# BirdEye Rate Limiting Fixes - Critical Performance Enhancement

## 🚨 **CRITICAL ISSUE RESOLVED**

This document outlines the critical rate limiting issues that were identified and fixed to optimize our BirdEye API usage for the **Starter package**.

## **Problem Summary**

Our system was severely underutilizing the BirdEye API due to incorrect rate limiting configuration, causing:

- **7.5x slower performance** than necessary
- **Only 13% utilization** of available API capacity
- **Missed trading opportunities** due to artificial bottlenecks
- **Wasted compute units** from inefficient batching

## **Root Cause Analysis**

### **Issue 1: Severe Rate Limiting Bottleneck**

**Problem**: The `rate_limiter_service.py` had BirdEye limited to only **2 requests per second**, but the Starter package allows **15 requests per second**.

```python
# BEFORE (❌ Wrong)
"birdeye": {"calls": 2, "period": 1}  # Only 2 RPS!

# AFTER (✅ Fixed)  
"birdeye": {"calls": 15, "period": 1}  # Proper 15 RPS for Starter package
```

**Impact**:
- System was using only 13% of available capacity
- Scans taking 7.5x longer than necessary
- Quality-based selection improvements negated by bottlenecks

### **Issue 2: Missing Wallet API Rate Limits**

**Problem**: [BirdEye documentation](https://docs.birdeye.so/docs/rate-limiting) specifies that Wallet API endpoints have special rate limits of **30 requests per minute**, but our system didn't account for this.

**Solution**: Added dedicated rate limiting domain for wallet endpoints:

```python
# NEW: Special rate limiting for wallet endpoints
"birdeye_wallet": {"calls": 30, "period": 60}  # 30 RPM for wallet APIs
```

**Affected Endpoints**:
- `/v1/wallet/tx-list`
- `/v1/wallet/token-list`
- `/v1/wallet/multichain-token-list`
- `/v1/wallet/token-balance`
- `/v1/wallet/multichain-tx-list`
- `/v1/wallet/simulate`

### **Issue 3: Inconsistent Rate Limiting Configuration**

**Problem**: Different parts of the system had conflicting rate limit configurations:

| Component | Before | After | Status |
|-----------|--------|-------|--------|
| `rate_limiter_service.py` | 2 RPS | 15 RPS | ✅ Fixed |
| `config.optimized.yaml` | 15 RPS | 15 RPS | ✅ Already correct |
| `run_optimized_10_scan_test.py` | 15 RPS | 15 RPS | ✅ Already correct |
| Various test files | 100 RPM | 15 RPS | ✅ Will use service default |

## **Implementation Details**

### **1. Updated Rate Limiter Service**

**File**: `services/rate_limiter_service.py`

```python
# Default configuration - UPDATED FOR BIRDEYE STARTER PACKAGE
config = {
    "enabled": True,
    "default_retry_interval": 1,
    "domains": {
        "default": {"calls": 5, "period": 1},  # Default: 5 calls per second
        "helius": {"calls": 5, "period": 1},
        "birdeye": {"calls": 15, "period": 1},  # FIXED: Starter package = 15 RPS (was 2)
        "birdeye_wallet": {"calls": 30, "period": 60},  # NEW: Wallet API = 30 RPM
        "dexscreener": {"calls": 30, "period": 60}
    }
}
```

### **2. Enhanced BirdEye API Connector**

**File**: `api/birdeye_connector.py`

Added intelligent rate limit domain selection:

```python
def _get_rate_limit_domain(self, endpoint: str) -> str:
    """
    Get the appropriate rate limiting domain based on the endpoint.
    
    Wallet API endpoints have special rate limits (30 RPM) according to BirdEye docs:
    https://docs.birdeye.so/docs/rate-limiting
    """
    wallet_endpoints = [
        '/v1/wallet/tx-list',
        '/v1/wallet/token-list', 
        '/v1/wallet/token_list',
        '/v1/wallet/multichain-token-list',
        '/v1/wallet/token-balance',
        '/v1/wallet/multichain-tx-list',
        '/v1/wallet/simulate'
    ]
    
    if any(endpoint.startswith(wallet_ep) for wallet_ep in wallet_endpoints):
        return "birdeye_wallet"
    else:
        return self.API_DOMAIN
```

Updated both `_make_request` and `_make_request_batch_aware` methods:

```python
# Apply rate limiting - use special domain for wallet endpoints
rate_limit_domain = self._get_rate_limit_domain(endpoint)
await self.rate_limiter.wait_for_slot(rate_limit_domain)
```

## **BirdEye Starter Package Specifications**

According to the [BirdEye pricing documentation](https://docs.birdeye.so/docs/pricing):

| Package | Base Price | Included CUs | Rate Limit | Cost per 1M additional CUs |
|---------|------------|--------------|------------|----------------------------|
| **Starter** | $99 | 3 Million | **15 rps** | $33 |

**Special Rate Limits**:
- **Most APIs**: 15 requests per second
- **Wallet APIs**: 30 requests per minute (0.5 RPS)

## **Expected Performance Improvements**

### **Immediate Benefits**

1. **7.5x Faster API Calls**: From 2 RPS → 15 RPS
2. **Better Resource Utilization**: From 13% → 100% of available capacity
3. **Reduced Scan Times**: Quality-based selection can now operate at full speed
4. **Improved Token Discovery**: High-potential tokens won't be missed due to artificial delays

### **Quantitative Impact**

**Before Fixes**:
- Rate limit: 2 RPS
- Time for 50 API calls: 25 seconds
- Utilization: 13% of Starter package capacity

**After Fixes**:
- Rate limit: 15 RPS  
- Time for 50 API calls: 3.3 seconds
- Utilization: 100% of Starter package capacity
- **Performance improvement: 650%**

### **Cost Optimization Benefits**

1. **Better CU Utilization**: More efficient use of included 3M compute units
2. **Reduced Overage Risk**: Faster processing means less chance of timeout-induced retries
3. **Improved ROI**: Getting full value from $99/month Starter package investment

## **Validation Steps**

To verify the fixes are working correctly:

1. **Check Rate Limiter Initialization**:
   ```bash
   grep -r "birdeye.*15.*period.*1" logs/
   ```

2. **Monitor API Call Rates**:
   - Look for log entries showing 15 RPS capability
   - Verify wallet endpoints use separate rate limiting

3. **Performance Benchmarking**:
   - Compare scan completion times before/after
   - Monitor API call efficiency ratios

## **Monitoring & Alerts**

### **Key Metrics to Track**

1. **API Call Rate**: Should approach 15 RPS during active scans
2. **Rate Limit Hits**: Should be minimal with proper 15 RPS limit
3. **Scan Completion Times**: Should be significantly faster
4. **CU Usage Efficiency**: Better utilization of included compute units

### **Warning Signs**

- Rate limit errors (429) with new 15 RPS limit → Investigate API usage patterns
- Wallet API failures → Check 30 RPM limit compliance
- No performance improvement → Verify configuration loading

## **Future Considerations**

### **Package Upgrade Triggers**

Consider upgrading to **Premium** ($199, 50 RPS, 10M CUs) if:
- Consistently hitting 15 RPS limit
- Using >3M compute units monthly
- Need >30 RPM for wallet operations

### **Optimization Opportunities**

1. **Batch Processing**: Leverage higher rate limits for more aggressive batching
2. **Concurrent Discovery**: Run multiple discovery strategies in parallel
3. **Predictive Caching**: Pre-fetch popular tokens during low-usage periods

## **References**

- [BirdEye Rate Limiting Documentation](https://docs.birdeye.so/docs/rate-limiting)
- [BirdEye Pricing Documentation](https://docs.birdeye.so/docs/pricing)
- Quality-Based Selection Implementation (docs/QUALITY_BASED_SELECTION_IMPLEMENTATION.md)

---

**Status**: ✅ **IMPLEMENTED AND ACTIVE**

**Impact**: 🚀 **CRITICAL PERFORMANCE ENHANCEMENT - 650% IMPROVEMENT**

**Next Steps**: Monitor performance metrics and consider Premium upgrade if hitting new limits consistently. 