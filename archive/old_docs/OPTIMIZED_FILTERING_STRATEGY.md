# Optimized Progressive Filtering Strategy - Using Available Data

## 🎯 **Goal: Get Best Candidates to Expensive Stage 3 Using Existing Data**

After analyzing the codebase, we actually **DO have valuable data** from discovery that we're not fully utilizing for filtering. Here's how to optimize progressive filtering without additional API costs.

---

## 📊 **Available Data Analysis**

### **Data We Already Have from Discovery:**

#### **1. Moralis Graduated Tokens (RICH DATA):**
```python
{
    'symbol': token.get('symbol', 'Unknown'),
    'name': token.get('name', 'Unknown Token'),
    'address': token.get('token_address'),
    'market_cap': float(token.get('fully_diluted_valuation', 0)),     # ✅ AVAILABLE
    'price': float(token.get('price_native', 0)),                    # ✅ AVAILABLE
    'liquidity': float(token.get('liquidity', 0)),                   # ✅ AVAILABLE
    'bonding_curve_progress': 100,                                   # ✅ GRADUATED
    'hours_since_graduation': hours_since_grad,                      # ✅ TIME SENSITIVE
    'graduated_at': graduated_at,                                    # ✅ TIMESTAMP
    'source': 'moralis_graduated'
}
```

#### **2. Moralis Bonding Tokens (MEDIUM DATA):**
```python
{
    'symbol': token.get('symbol', 'Unknown'),
    'address': token.get('token_address'),
    'market_cap': float(token.get('market_cap', 0)),                 # ✅ AVAILABLE
    'price': float(token.get('price_usd', 0)),                       # ✅ AVAILABLE  
    'liquidity': float(token.get('liquidity', 0)),                   # ✅ AVAILABLE
    'bonding_curve_progress': float(token.get('bonding_curve_progress')), # ✅ CRITICAL
    'estimated_age_minutes': 120,                                    # ✅ TIME INFO
    'pump_fun_stage': 'BONDING_CURVE',                              # ✅ STAGE INFO
    'source': 'moralis_bonding'
}
```

#### **3. Birdeye Trending (MINIMAL BUT VALIDATED):**
```python
{
    'symbol': 'Unknown',  # Needs enrichment
    'address': address,
    'market_cap': 0,      # Needs enrichment
    'price': 0,          # Needs enrichment
    'volume_24h': 0,     # Needs enrichment
    'source': 'birdeye_trending',  # ✅ ALREADY TRENDING (HIGH VALUE)
    'needs_enrichment': True
}
```

---

## 🚀 **Optimized Progressive Filtering Strategy**

### **Stage 1: Smart Discovery-Based Triage** 
**Cost:** 💚 **FREE** (uses existing discovery data)
**Target:** Reduce 40-80 tokens → 20-35 tokens (50-60% reduction)

#### **New Method: `_smart_discovery_triage()`**

```python
async def _smart_discovery_triage(self, candidates: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Smart triage using rich data already available from discovery APIs
    Leverages source-specific data quality and time-sensitive opportunities
    """
    high_priority_candidates = []
    
    for candidate in candidates:
        priority_score = 0
        source = candidate.get('source', 'unknown')
        
        # === SOURCE-SPECIFIC SMART SCORING ===
        
        if source == 'moralis_graduated':
            # Rich data available - use it effectively
            hours_since_grad = candidate.get('hours_since_graduation', 999)
            market_cap = candidate.get('market_cap', 0)
            liquidity = candidate.get('liquidity', 0)
            
            # Time-sensitive fresh graduate bonus (CRITICAL)
            if hours_since_grad <= 1:
                priority_score += 40  # Ultra-fresh graduates
            elif hours_since_grad <= 6:
                priority_score += 25  # Fresh graduates
            elif hours_since_grad <= 12:
                priority_score += 15  # Recent graduates
            
            # Market validation (using available data)
            if 50000 <= market_cap <= 2000000:
                priority_score += 20  # Sweet spot
            elif 10000 <= market_cap <= 50000:
                priority_score += 15  # Early stage
            elif market_cap > 2000000:
                priority_score += 5   # Larger but still valid
            
            # Liquidity validation
            if liquidity > 50000:
                priority_score += 15  # Good liquidity
            elif liquidity > 10000:
                priority_score += 10  # Decent liquidity
            elif liquidity > 1000:
                priority_score += 5   # Minimal liquidity
        
        elif source == 'moralis_bonding':
            # Use bonding curve proximity (TIME-CRITICAL)
            bonding_progress = candidate.get('bonding_curve_progress', 0)
            market_cap = candidate.get('market_cap', 0)
            
            # Graduation proximity scoring (HIGHEST PRIORITY)
            if bonding_progress >= 95:
                priority_score += 50  # Imminent graduation
            elif bonding_progress >= 90:
                priority_score += 35  # Very close
            elif bonding_progress >= 85:
                priority_score += 25  # Close
            elif bonding_progress >= 75:
                priority_score += 15  # Promising
            elif bonding_progress >= 50:
                priority_score += 10  # Mid-stage
            
            # Market cap validation for bonding tokens
            if 5000 <= market_cap <= 500000:
                priority_score += 15  # Good range for bonding
            elif market_cap < 5000 and market_cap > 0:
                priority_score += 10  # Very early
        
        elif source == 'birdeye_trending':
            # Already trending = validated by market
            priority_score += 30  # Base trending bonus
            
            # Trending tokens get benefit of doubt
            # Will be enriched in Stage 2 if they pass
        
        elif source == 'sol_bonding_detector':
            # SOL ecosystem strength
            priority_score += 20  # Base SOL bonus
        
        # === UNIVERSAL QUALITY INDICATORS ===
        
        # Address validation
        if candidate.get('address') and len(candidate.get('address', '')) == 44:
            priority_score += 5  # Valid Solana address
        
        # Symbol quality
        symbol = candidate.get('symbol', '')
        if symbol and symbol != 'Unknown' and len(symbol) <= 10:
            priority_score += 3  # Reasonable symbol
        
        # Age bonus (prefer newer tokens for early gems)
        age_minutes = candidate.get('estimated_age_minutes', 999)
        if age_minutes <= 60:
            priority_score += 8   # Ultra-fresh
        elif age_minutes <= 360:
            priority_score += 5   # Very fresh
        elif age_minutes <= 1440:
            priority_score += 2   # Fresh (24h)
        
        # === FILTERING LOGIC ===
        candidate['discovery_priority_score'] = priority_score
        
        # Dynamic thresholds based on source expectations
        if source == 'moralis_graduated':
            threshold = 25  # Rich data available
        elif source == 'moralis_bonding':
            threshold = 30  # Time-critical opportunities
        elif source == 'birdeye_trending':
            threshold = 30  # Already validated
        else:
            threshold = 20  # Conservative for others
        
        if priority_score >= threshold:
            high_priority_candidates.append(candidate)
    
    # Sort by priority score
    sorted_candidates = sorted(high_priority_candidates, 
                              key=lambda x: x.get('discovery_priority_score', 0), 
                              reverse=True)
    
    return sorted_candidates[:35]  # Top 35 candidates
```

### **Stage 2: Enhanced Analysis with Existing Batch Enrichment**
**Cost:** 🟡 **MEDIUM** (existing batch APIs, no OHLCV)
**Target:** 20-35 tokens → 15-25 tokens (25-30% further reduction)

#### **Fix Existing Method: Use Rich Data from Stage 1**

```python
async def _enhanced_candidate_analysis_fixed(self, candidates: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    FIXED: Actually enhanced analysis using discovery priority + batch enrichment
    """
    # Enrich candidates that need it (mainly Birdeye trending)
    candidates_needing_enrichment = [c for c in candidates if c.get('needs_enrichment')]
    enriched_candidates = await self._batch_enrich_tokens(candidates_needing_enrichment)
    
    # Merge enriched data back
    enriched_map = {c.get('address'): c for c in enriched_candidates if c.get('address')}
    for candidate in candidates:
        if candidate.get('address') in enriched_map:
            candidate.update(enriched_map[candidate.get('address')])
    
    enhanced_scored_candidates = []
    
    for candidate in candidates:
        # Start with discovery priority score
        discovery_score = candidate.get('discovery_priority_score', 0)
        
        # Add enrichment bonuses
        enrichment_bonus = 0
        
        # Volume validation (now available from batch enrichment)
        volume_24h = candidate.get('volume_24h', 0)
        if volume_24h > 100000:
            enrichment_bonus += 15  # High volume
        elif volume_24h > 50000:
            enrichment_bonus += 10  # Medium volume
        elif volume_24h > 10000:
            enrichment_bonus += 5   # Some volume
        
        # Trading activity
        trades_24h = candidate.get('trades_24h', 0)
        if trades_24h > 500:
            enrichment_bonus += 10  # Active trading
        elif trades_24h > 100:
            enrichment_bonus += 5   # Some trading
        
        # Holder validation
        holder_count = candidate.get('holder_count', 0)
        if holder_count > 200:
            enrichment_bonus += 10  # Good distribution
        elif holder_count > 50:
            enrichment_bonus += 5   # Decent distribution
        
        # Security bonus
        security_score = candidate.get('security_score', 0)
        if security_score > 80:
            enrichment_bonus += 8
        elif security_score > 60:
            enrichment_bonus += 4
        
        enhanced_score = discovery_score + enrichment_bonus
        candidate['enhanced_score'] = enhanced_score
        
        # Progressive threshold based on source and data quality
        source = candidate.get('source', 'unknown')
        data_quality = 'high' if candidate.get('market_cap', 0) > 0 else 'low'
        
        if source == 'moralis_bonding' and data_quality == 'high':
            threshold = 45  # High bar for pre-graduation with good data
        elif source == 'moralis_graduated' and data_quality == 'high':
            threshold = 40  # Good bar for graduates with data
        elif source == 'birdeye_trending':
            threshold = 35  # Already trending, lower bar
        else:
            threshold = 35  # Conservative default
        
        if enhanced_score >= threshold:
            enhanced_scored_candidates.append(candidate)
    
    # Sort and limit
    sorted_candidates = sorted(enhanced_scored_candidates, 
                              key=lambda x: x.get('enhanced_score', 0), 
                              reverse=True)
    
    return sorted_candidates[:25]  # Top 25 for deep analysis
```

### **Stage 3: Deep Analysis (UNCHANGED)**
**Cost:** 🔴 **EXPENSIVE** (OHLCV + comprehensive analysis)
**Target:** 15-25 tokens → Final high-conviction candidates

Keep existing deep analysis exactly as is - it's working well.

---

## 📊 **Expected Filtering Performance**

| Stage | Current | Optimized | Improvement |
|-------|---------|-----------|-------------|
| **Stage 1** | 40-80 → 38-76 (5% reduction) | 40-80 → 20-35 (**50-60% reduction**) | **10x better** |
| **Stage 2** | 38-76 → varies | 20-35 → 15-25 (**25-30% reduction**) | **Consistent** |
| **Stage 3** | varies → final | 15-25 → final | **Optimized input** |

## 🎯 **Key Optimizations**

### **1. Source-Specific Intelligence:**
- **Moralis Graduated:** Time-sensitive fresh graduate prioritization
- **Moralis Bonding:** Graduation proximity scoring (95%+ = highest priority)
- **Birdeye Trending:** Market-validated trending bonus
- **SOL Bonding:** Ecosystem strength weighting

### **2. Time-Critical Opportunity Detection:**
- **<1h since graduation:** 40-point priority boost
- **>95% bonding progress:** 50-point priority boost
- **Fresh launches (<1h):** 8-point age bonus

### **3. Data-Driven Validation:**
- **Market cap sweet spots:** $50K-$2M for graduated, $5K-$500K for bonding
- **Liquidity thresholds:** >$50K for graduates, >$10K for bonding
- **Volume activity:** Batch enriched volume validation

### **4. Dynamic Thresholds:**
- **Source-aware thresholds** based on data quality expectations
- **Progressive scoring** that builds from discovery → enhancement → deep analysis

---

## 🚀 **Implementation Priority**

### **High Priority (Immediate Impact):**
1. ✅ Replace `_quick_triage_candidates()` with `_smart_discovery_triage()`
2. ✅ Fix `_enhanced_candidate_analysis()` to actually enhance scores
3. ✅ Implement source-specific thresholds

### **Medium Priority (Performance):**
4. ✅ Add time-sensitive opportunity detection
5. ✅ Implement data quality validation
6. ✅ Add progressive threshold logic

## 📈 **Expected Results**

**With these optimizations:**
- **Stage 1:** Effectively filters 50-60% of candidates using rich discovery data
- **Stage 2:** Further 25-30% reduction with enhanced batch data
- **Stage 3:** Receives 15-25 high-quality candidates instead of 40-80

**Outcome:** Same expensive Stage 3 analysis cost, but **much higher quality input** leading to better detection accuracy and resource efficiency.

The key insight is that we already have **valuable time-sensitive data** (graduation proximity, fresh graduate timing) that can create effective filtering without additional API costs!