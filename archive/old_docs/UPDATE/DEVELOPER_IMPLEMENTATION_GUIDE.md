# Developer Implementation Guide: Token Discovery System Overhaul

## 🚨 CRITICAL: Read This First

This guide provides **exact** step-by-step instructions for implementing the token discovery system overhaul. Each phase includes:
- **Exact file paths** and line numbers
- **Complete code snippets** with imports
- **Integration checkpoints** to verify functionality
- **Testing procedures** for each component
- **Rollback instructions** if something breaks

**⚠️ IMPORTANT:** Create backups before modifying any existing files!

---

## Phase 1: Critical Bug Fixes & Foundation (Week 1)

### 🔧 Task 1.1: Fix Cache System Failure

#### Step 1: Examine Current Cache Implementation
**File:** `api/batch_api_manager.py`

```bash
# First, find the current cache implementation
grep -n "cache" api/batch_api_manager.py
```

#### Step 2: Replace Cache Manager Class
**Location:** `api/batch_api_manager.py` (around line 20-50)

**FIND THIS CODE:**
```python
# Look for existing cache initialization
self.cache = {}  # or similar
```

**REPLACE WITH:**
```python
from cachetools import TTLCache
import hashlib
import json

class FixedCacheManager:
    def __init__(self):
        # Fixed cache system with proper TTL
        self.price_cache = TTLCache(maxsize=2000, ttl=60)      # 1 minute
        self.metadata_cache = TTLCache(maxsize=1000, ttl=300)  # 5 minutes
        self.trending_cache = TTLCache(maxsize=100, ttl=180)   # 3 minutes
        
        # Track cache performance
        self.cache_hits = 0
        self.cache_misses = 0
        
    def _generate_cache_key(self, endpoint: str, params: dict) -> str:
        """Generate consistent, hashable cache keys"""
        # Sort params to ensure consistent keys
        sorted_params = sorted(params.items()) if params else []
        key_data = f"{endpoint}:{json.dumps(sorted_params, sort_keys=True)}"
        return hashlib.md5(key_data.encode()).hexdigest()
    
    async def get_cached_data(self, endpoint: str, params: dict = None):
        """Get data from appropriate cache"""
        key = self._generate_cache_key(endpoint, params or {})
        
        # Check appropriate cache based on endpoint
        if 'price' in endpoint.lower():
            cached_data = self.price_cache.get(key)
        elif 'trending' in endpoint.lower():
            cached_data = self.trending_cache.get(key)
        else:
            cached_data = self.metadata_cache.get(key)
        
        if cached_data:
            self.cache_hits += 1
            return cached_data
        else:
            self.cache_misses += 1
            return None
    
    async def set_cached_data(self, endpoint: str, params: dict, data: any):
        """Store data in appropriate cache"""
        key = self._generate_cache_key(endpoint, params or {})
        
        if 'price' in endpoint.lower():
            self.price_cache[key] = data
        elif 'trending' in endpoint.lower():
            self.trending_cache[key] = data
        else:
            self.metadata_cache[key] = data
    
    def get_cache_hit_rate(self) -> float:
        """Calculate cache hit rate for monitoring"""
        total_requests = self.cache_hits + self.cache_misses
        return (self.cache_hits / total_requests * 100) if total_requests > 0 else 0.0
```

#### Step 3: Update BatchAPIManager Constructor
**Location:** `api/batch_api_manager.py` (in `__init__` method)

**FIND:**
```python
def __init__(self):
    # existing initialization
```

**ADD AFTER EXISTING INITIALIZATION:**
```python
    # Initialize fixed cache manager
    self.cache_manager = FixedCacheManager()
    logger.info("Initialized FixedCacheManager with multi-tier caching")
```

#### Step 4: Update API Call Methods
**Location:** `api/batch_api_manager.py` (in `_make_api_call` method)

**FIND:**
```python
async def _make_api_call(self, endpoint: str, params: dict = None):
    # existing implementation
```

**REPLACE WITH:**
```python
async def _make_api_call(self, endpoint: str, params: dict = None):
    """Make API call with fixed caching"""
    
    # Check cache first
    cached_data = await self.cache_manager.get_cached_data(endpoint, params)
    if cached_data:
        logger.debug(f"Cache HIT for {endpoint}")
        return cached_data
    
    # Make API call if not cached
    logger.debug(f"Cache MISS for {endpoint}")
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(endpoint, params=params) as response:
                if response.status == 200:
                    data = await response.json()
                    # Cache the result
                    await self.cache_manager.set_cached_data(endpoint, params, data)
                    return data
                else:
                    logger.error(f"API call failed: {response.status}")
                    return None
    except Exception as e:
        logger.error(f"API call error: {e}")
        return None
```

#### Step 5: Add Cache Monitoring
**Location:** `api/batch_api_manager.py` (add new method)

```python
def log_cache_performance(self):
    """Log cache performance metrics"""
    hit_rate = self.cache_manager.get_cache_hit_rate()
    total_keys = (len(self.cache_manager.price_cache) + 
                  len(self.cache_manager.metadata_cache) + 
                  len(self.cache_manager.trending_cache))
    
    logger.info(f"CACHE PERFORMANCE:")
    logger.info(f"  Cache Hit Rate: {hit_rate:.2f}%")
    logger.info(f"  Total Cache Keys: {total_keys}")
    logger.info(f"  Cache Hits: {self.cache_manager.cache_hits}")
    logger.info(f"  Cache Misses: {self.cache_manager.cache_misses}")
    
    # Alert if cache hit rate is too low
    if hit_rate < 30 and (self.cache_manager.cache_hits + self.cache_manager.cache_misses) > 100:
        logger.warning(f"⚠️ LOW CACHE HIT RATE: {hit_rate:.2f}% - Consider debugging cache issues")
```

#### ✅ Checkpoint 1.1: Test Cache System
**Create Test File:** `tests/test_cache_fix.py`

```python
import asyncio
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from api.batch_api_manager import BatchAPIManager

async def test_cache_functionality():
    """Test that cache system is working"""
    api_manager = BatchAPIManager()
    
    # Test cache key generation
    endpoint = "https://api.example.com/test"
    params = {"symbol": "SOL", "timeframe": "1h"}
    
    key1 = api_manager.cache_manager._generate_cache_key(endpoint, params)
    key2 = api_manager.cache_manager._generate_cache_key(endpoint, params)
    
    assert key1 == key2, "Cache keys should be consistent"
    print("✅ Cache key generation working")
    
    # Test cache storage and retrieval
    test_data = {"price": 100, "volume": 1000}
    await api_manager.cache_manager.set_cached_data(endpoint, params, test_data)
    
    cached_result = await api_manager.cache_manager.get_cached_data(endpoint, params)
    assert cached_result == test_data, "Cache storage/retrieval failed"
    print("✅ Cache storage/retrieval working")
    
    # Test cache hit rate calculation
    hit_rate = api_manager.cache_manager.get_cache_hit_rate()
    assert hit_rate > 0, "Cache hit rate should be calculable"
    print(f"✅ Cache hit rate: {hit_rate:.2f}%")
    
    print("🎉 All cache tests passed!")

if __name__ == "__main__":
    asyncio.run(test_cache_functionality())
```

**Run Test:**
```bash
cd /path/to/your/project
python tests/test_cache_fix.py
```

---

### 🔧 Task 1.2: Fix Whale Analysis Technical Bugs

#### Step 1: Locate Whale Analysis Errors
**File:** `services/whale_discovery_service.py`

```bash
# Find the problematic code
grep -n "unhashable type" logs/monitoring_runs/*/monitoring_*.log
```

#### Step 2: Fix Data Type Handling
**Location:** `services/whale_discovery_service.py` (find `analyze_whale_activity` method)

**FIND:**
```python
async def analyze_whale_activity(self, token_address: str) -> Dict:
    # existing problematic implementation
```

**REPLACE WITH:**
```python
async def analyze_whale_activity(self, token_address: str) -> Dict:
    """Analyze whale activity with proper error handling"""
    try:
        logger.debug(f"Starting whale analysis for {token_address}")
        
        # Fetch whale data with proper type checking
        whale_data = await self._fetch_whale_data(token_address)
        
        # Fix: Ensure proper data structure handling
        if whale_data is None:
            logger.warning(f"No whale data received for {token_address}")
            return self._default_whale_score()
        
        # Handle different data types properly
        if isinstance(whale_data, dict):
            return self._process_whale_dict(whale_data)
        elif isinstance(whale_data, list):
            return self._process_whale_list(whale_data)
        else:
            logger.warning(f"Unexpected whale data type: {type(whale_data)}")
            return self._default_whale_score()
            
    except Exception as e:
        logger.error(f"Whale analysis error for {token_address}: {str(e)}")
        logger.error(f"Error type: {type(e).__name__}")
        return self._default_whale_score()

def _process_whale_dict(self, whale_data: dict) -> Dict:
    """Process whale data when it's a dictionary"""
    try:
        return {
            'whale_score': whale_data.get('score', 0),
            'large_holders_count': whale_data.get('large_holders', 0),
            'whale_activity': whale_data.get('activity', 'unknown'),
            'confidence': 'medium'
        }
    except Exception as e:
        logger.error(f"Error processing whale dict: {e}")
        return self._default_whale_score()

def _process_whale_list(self, whale_data: list) -> Dict:
    """Process whale data when it's a list"""
    try:
        if not whale_data:
            return self._default_whale_score()
        
        # Calculate aggregate metrics from list
        total_score = sum(item.get('score', 0) for item in whale_data if isinstance(item, dict))
        avg_score = total_score / len(whale_data) if whale_data else 0
        
        return {
            'whale_score': min(avg_score, 100),  # Cap at 100
            'large_holders_count': len(whale_data),
            'whale_activity': 'multiple_whales',
            'confidence': 'high' if len(whale_data) > 3 else 'medium'
        }
    except Exception as e:
        logger.error(f"Error processing whale list: {e}")
        return self._default_whale_score()

def _default_whale_score(self) -> Dict:
    """Return safe default whale analysis"""
    return {
        'whale_score': 0,
        'large_holders_count': 0,
        'whale_activity': 'unknown',
        'confidence': 'low',
        'error': True
    }
```

#### ✅ Checkpoint 1.2: Test Whale Analysis Fix
**Create Test File:** `tests/test_whale_fix.py`

```python
import asyncio
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from services.whale_discovery_service import WhaleDiscoveryService

async def test_whale_analysis_fix():
    """Test whale analysis with different data types"""
    service = WhaleDiscoveryService()
    
    # Test with dict data
    dict_data = {'score': 75, 'large_holders': 5, 'activity': 'buying'}
    result = service._process_whale_dict(dict_data)
    assert result['whale_score'] == 75
    print("✅ Whale dict processing working")
    
    # Test with list data
    list_data = [{'score': 60}, {'score': 80}, {'score': 70}]
    result = service._process_whale_list(list_data)
    assert result['whale_score'] == 70  # Average
    print("✅ Whale list processing working")
    
    # Test default score
    result = service._default_whale_score()
    assert result['whale_score'] == 0
    assert result['error'] == True
    print("✅ Default whale score working")
    
    print("🎉 All whale analysis tests passed!")

if __name__ == "__main__":
    asyncio.run(test_whale_analysis_fix())
```

---

### 🔧 Task 1.3: Eliminate Emergency Inclusion Logic

#### Step 1: Find Emergency Inclusion Code
**File:** `services/early_token_detection.py`

```bash
# Find all emergency inclusion references
grep -n -i "emergency" services/early_token_detection.py
```

#### Step 2: Remove Emergency Inclusion Logic
**Location:** `services/early_token_detection.py` (find and DELETE these sections)

**REMOVE ALL CODE LIKE THIS:**
```python
# DELETE these lines and similar logic
if len(promising_tokens) < min_tokens:
    logger.warning("🚨 Emergency inclusion activated")
    # Any code that forces inclusion of low-scoring tokens
```

#### Step 3: Add Strict Quality Gates
**Location:** `services/early_token_detection.py` (replace emergency logic with this)

```python
def apply_quality_gates(self, tokens: List[Dict]) -> List[Dict]:
    """Apply strict quality filtering - NO emergency inclusion"""
    
    # Absolute minimum requirements (NEVER relaxed)
    MIN_SCORE = 60          # No tokens below 60 points
    MIN_LIQUIDITY = 500000  # $500K minimum liquidity
    MIN_HOLDERS = 1000      # 1K minimum holders
    MIN_VOLUME_24H = 100000 # $100K minimum 24h volume
    
    logger.info(f"Applying strict quality gates to {len(tokens)} tokens")
    
    filtered_tokens = []
    for token in tokens:
        # Check all minimum requirements
        if (token.get('score', 0) >= MIN_SCORE and 
            token.get('liquidity', 0) >= MIN_LIQUIDITY and
            token.get('holders', 0) >= MIN_HOLDERS and
            token.get('volume_24h', 0) >= MIN_VOLUME_24H):
            
            filtered_tokens.append(token)
        else:
            logger.debug(f"Token {token.get('symbol', 'UNKNOWN')} failed quality gates: "
                        f"score={token.get('score', 0)}, "
                        f"liquidity=${token.get('liquidity', 0):,.0f}, "
                        f"holders={token.get('holders', 0)}")
    
    logger.info(f"Quality gates passed: {len(filtered_tokens)}/{len(tokens)} tokens")
    
    # Return what we have - NO forced inclusion
    return filtered_tokens
```

#### Step 4: Update Score Thresholds
**Location:** `services/early_token_detection.py` (find threshold definitions)

**REPLACE:**
```python
# Old dynamic thresholds
QUICK_SCORE_THRESHOLD = 30  # or similar low values
```

**WITH:**
```python
# Fixed strict thresholds - never lowered
QUICK_SCORE_THRESHOLD = 50
MEDIUM_SCORE_THRESHOLD = 60  
FULL_SCORE_THRESHOLD = 70

# Remove any dynamic threshold adjustment code
```

#### ✅ Checkpoint 1.3: Test Quality Gates
**Create Test File:** `tests/test_quality_gates.py`

```python
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from services.early_token_detection import EarlyTokenDetector

def test_quality_gates():
    """Test that quality gates work without emergency inclusion"""
    detector = EarlyTokenDetector()
    
    # Test tokens - some pass, some fail
    test_tokens = [
        {  # Should pass
            'symbol': 'GOOD',
            'score': 75,
            'liquidity': 1000000,
            'holders': 5000,
            'volume_24h': 500000
        },
        {  # Should fail - low score
            'symbol': 'BAD1',
            'score': 45,
            'liquidity': 1000000,
            'holders': 5000,
            'volume_24h': 500000
        },
        {  # Should fail - low liquidity
            'symbol': 'BAD2',
            'score': 75,
            'liquidity': 100000,
            'holders': 5000,
            'volume_24h': 500000
        }
    ]
    
    filtered = detector.apply_quality_gates(test_tokens)
    
    assert len(filtered) == 1, f"Expected 1 token to pass, got {len(filtered)}"
    assert filtered[0]['symbol'] == 'GOOD', "Wrong token passed quality gates"
    
    print("✅ Quality gates working correctly")
    print("✅ Emergency inclusion eliminated")
    print("🎉 Quality gate tests passed!")

if __name__ == "__main__":
    test_quality_gates()
```

---

### 🔧 Task 1.4: Cap Social Media Bonuses

#### Step 1: Find Social Media Bonus Code
**Location:** `services/early_token_detection.py`

```bash
# Find social media bonus calculation
grep -n -i "social.*bonus\|bonus.*social" services/early_token_detection.py
```

#### Step 2: Replace Social Media Bonus Logic
**FIND:**
```python
def calculate_social_media_bonus(self, token_data: Dict) -> float:
    # existing unlimited bonus logic
```

**REPLACE WITH:**
```python
def calculate_social_media_bonus(self, token_data: Dict) -> float:
    """Calculate capped social media bonus with fundamental requirements"""
    
    # First, check fundamental score requirements
    price_score = token_data.get('price_score', 0)
    trend_score = token_data.get('trend_score', 0) 
    volume_score = token_data.get('volume_score', 0)
    
    fundamental_score = price_score + trend_score + volume_score
    
    logger.debug(f"Token {token_data.get('symbol', 'UNKNOWN')} fundamental scores: "
                f"price={price_score}, trend={trend_score}, volume={volume_score}, "
                f"total={fundamental_score}")
    
    # Require minimum 30 points from fundamentals before any social bonus
    if fundamental_score < 30:
        logger.debug(f"No social bonus - fundamental score {fundamental_score} < 30")
        return 0
    
    # Calculate social media metrics
    social_metrics = {
        'website': 1 if token_data.get('website') else 0,
        'twitter': 2 if token_data.get('twitter') else 0,
        'telegram': 2 if token_data.get('telegram') else 0,
        'discord': 1 if token_data.get('discord') else 0,
        'community_size': min(token_data.get('community_size', 0) / 10000, 3),  # Max 3 points
        'social_activity': min(token_data.get('social_activity_score', 0) / 20, 2)  # Max 2 points
    }
    
    raw_social_score = sum(social_metrics.values())
    
    # Apply caps based on fundamental strength
    if fundamental_score >= 50:
        max_bonus = 10  # Strong fundamentals allow up to +10
    elif fundamental_score >= 40:
        max_bonus = 7   # Medium fundamentals allow up to +7
    else:
        max_bonus = 5   # Weak fundamentals allow up to +5
    
    final_bonus = min(raw_social_score, max_bonus)
    
    logger.debug(f"Social bonus calculation: raw={raw_social_score:.1f}, "
                f"max_allowed={max_bonus}, final={final_bonus:.1f}")
    
    return final_bonus
```

#### ✅ Checkpoint 1.4: Test Social Media Bonus Cap
**Create Test File:** `tests/test_social_bonus_cap.py`

```python
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from services.early_token_detection import EarlyTokenDetector

def test_social_bonus_cap():
    """Test social media bonus capping"""
    detector = EarlyTokenDetector()
    
    # Test case 1: Weak fundamentals should get no bonus
    weak_token = {
        'symbol': 'WEAK',
        'price_score': 10,
        'trend_score': 0,
        'volume_score': 15,
        'website': True,
        'twitter': True,
        'telegram': True,
        'community_size': 50000
    }
    
    bonus = detector.calculate_social_media_bonus(weak_token)
    assert bonus == 0, f"Weak fundamentals should get 0 bonus, got {bonus}"
    print("✅ Weak fundamentals correctly get 0 bonus")
    
    # Test case 2: Strong fundamentals should get capped bonus
    strong_token = {
        'symbol': 'STRONG',
        'price_score': 20,
        'trend_score': 15,
        'volume_score': 20,  # Total 55 fundamental
        'website': True,
        'twitter': True,
        'telegram': True,
        'discord': True,
        'community_size': 100000,
        'social_activity_score': 100
    }
    
    bonus = detector.calculate_social_media_bonus(strong_token)
    assert bonus <= 10, f"Bonus should be capped at 10, got {bonus}"
    print(f"✅ Strong fundamentals get capped bonus: {bonus}")
    
    print("🎉 Social bonus cap tests passed!")

if __name__ == "__main__":
    test_social_bonus_cap()
```

---

## Phase 1 Integration Test

**Create Integration Test:** `tests/test_phase1_integration.py`

```python
import asyncio
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from api.batch_api_manager import BatchAPIManager
from services.whale_discovery_service import WhaleDiscoveryService
from services.early_token_detection import EarlyTokenDetector

async def test_phase1_integration():
    """Test all Phase 1 fixes working together"""
    
    print("🧪 Testing Phase 1 Integration...")
    
    # Test 1: Cache system
    api_manager = BatchAPIManager()
    hit_rate = api_manager.cache_manager.get_cache_hit_rate()
    print(f"✅ Cache system initialized: {hit_rate:.2f}% hit rate")
    
    # Test 2: Whale analysis
    whale_service = WhaleDiscoveryService()
    default_score = whale_service._default_whale_score()
    assert 'error' in default_score
    print("✅ Whale analysis error handling working")
    
    # Test 3: Quality gates
    detector = EarlyTokenDetector()
    test_tokens = [{'score': 45}, {'score': 75, 'liquidity': 1000000, 'holders': 2000, 'volume_24h': 200000}]
    filtered = detector.apply_quality_gates(test_tokens)
    assert len(filtered) <= 1  # Should filter out low quality
    print("✅ Quality gates working (no emergency inclusion)")
    
    # Test 4: Social bonus cap
    test_token = {'price_score': 0, 'trend_score': 0, 'volume_score': 0, 'website': True}
    bonus = detector.calculate_social_media_bonus(test_token)
    assert bonus == 0  # Should be 0 for weak fundamentals
    print("✅ Social bonus properly capped")
    
    print("🎉 Phase 1 Integration Test PASSED!")
    print("📋 Ready for Phase 2 implementation")

if __name__ == "__main__":
    asyncio.run(test_phase1_integration())
```

**Run Integration Test:**
```bash
python tests/test_phase1_integration.py
```

**Expected Output:**
```
🧪 Testing Phase 1 Integration...
✅ Cache system initialized: 0.00% hit rate
✅ Whale analysis error handling working  
✅ Quality gates working (no emergency inclusion)
✅ Social bonus properly capped
🎉 Phase 1 Integration Test PASSED!
📋 Ready for Phase 2 implementation
```

---

## Phase 1 Success Criteria Checklist

**Before proceeding to Phase 2, verify:**

- [ ] Cache hit rate >0% (visible in logs)
- [ ] Zero "unhashable type: 'dict'" errors in whale analysis
- [ ] Zero emergency inclusion activations in logs
- [ ] Social bonuses capped at ≤10 points
- [ ] All Phase 1 tests pass
- [ ] System still discovers tokens (even if fewer)

**If any criteria fail, debug and fix before Phase 2!**

---

*This guide continues with Phase 2 implementation details...* 