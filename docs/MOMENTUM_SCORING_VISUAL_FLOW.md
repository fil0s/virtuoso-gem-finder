# 🎯 Momentum Scoring System - Visual Flow Diagram

## Complete System Flow

```
                           🎲 TOKEN DATA INPUT
                                    │
                        ┌───────────┴───────────┐
                        │   Available Data      │
                        │  • volume_5m: $15K    │
                        │  • volume_15m: $22K   │
                        │  • price_change_5m: +12.5%│
                        │  • trades_5m: 15      │
                        │  • estimated_age: 5min│
                        └───────────┬───────────┘
                                    │
                    ═══════════════════════════════════
                    ║  LAYER 1: CONFIDENCE ASSESSMENT ║
                    ═══════════════════════════════════
                                    │
                        ┌───────────┴───────────┐
                        │ Age-Aware Analysis    │
                        │ Token Age: 5 minutes  │
                        │ Category: ULTRA_EARLY │
                        └───────────┬───────────┘
                                    │
                        ┌───────────┴───────────┐
                        │ Data Pattern Check    │
                        │ ✅ Short-term: 5m,15m │
                        │ ✅ Multiple: 2 signals│
                        │ ✅ Real Momentum!     │
                        └───────────┬───────────┘
                                    │
                        ┌───────────┴───────────┐
                        │   CONFIDENCE LEVEL    │
                        │  🚀 EARLY_DETECTION   │
                        │   Bonus: +5%         │
                        └───────────┬───────────┘
                                    │
                    ═══════════════════════════════════
                    ║ LAYER 2: MOMENTUM QUANTIFICATION ║
                    ═══════════════════════════════════
                                    │
                ┌───────────────────┼───────────────────┐
                │                   │                   │
        ┌───────┴────────┐ ┌────────┴────────┐ ┌───────┴────────┐
        │ VOLUME ACCEL   │ │ MOMENTUM CASCADE│ │ ACTIVITY SURGE │
        │ Weight: 40%    │ │ Weight: 35%     │ │ Weight: 25%    │
        │ Max: 0.4 pts   │ │ Max: 0.35 pts   │ │ Max: 0.25 pts  │
        └───────┬────────┘ └────────┬────────┘ └───────┬────────┘
                │                   │                   │
        ┌───────┴────────┐ ┌────────┴────────┐ ┌───────┴────────┐
        │ 5m→1h Analysis │ │ Price Momentum  │ │ Trade Activity │
        │ proj: $180K    │ │ 5m: +12.5%     │ │ 5m: 15 trades  │
        │ actual: $35K   │ │ 15m: +18.2%    │ │ Level: Moderate│
        │ accel: 5.1x    │ │ Strong cascade  │ │ Score: 0.06    │
        │ Score: 0.15    │ │ Score: 0.10     │ │                │
        └───────┬────────┘ └────────┬────────┘ └───────┬────────┘
                │                   │                   │
                └───────────────────┼───────────────────┘
                                    │
                        ┌───────────┴───────────┐
                        │   VELOCITY SCORING    │
                        │ Volume: 0.15/0.4      │
                        │ Momentum: 0.10/0.35   │
                        │ Activity: 0.06/0.25   │
                        │ TOTAL: 0.31/1.0 (31%) │
                        └───────────┬───────────┘
                                    │
                    ═══════════════════════════════════
                    ║    FINAL SCORE ADJUSTMENT       ║
                    ═══════════════════════════════════
                                    │
                        ┌───────────┴───────────┐
                        │   Score Application   │
                        │ Base Score: 45.0      │
                        │ Velocity: +0.31       │
                        │ Confidence: +5%       │
                        │ Final: 47.6 points    │
                        └───────────┬───────────┘
                                    │
                        ┌───────────┴───────────┐
                        │      RESULT           │
                        │  🚀 HIGH CONVICTION   │
                        │  Score: 47.6/100     │
                        │  Confidence: EARLY    │
                        │  Alert: TRIGGERED     │
                        └───────────────────────┘
```

## Decision Tree Flow

```
TOKEN DATA
    │
    ├─ Age < 30min? ──┐ YES ─── Has 5m/15m data? ──┐ YES ─── Multiple signals? ──┐ YES ─── 🚀 EARLY_DETECTION (+5%)
    │                 │                             │                            │
    │                 │                             │                            └─ NO ──── 🟡 MEDIUM (neutral)
    │                 │                             │
    │                 │                             └─ NO ──── Only 24h data? ──┐ YES ─── 🟠 LOW (-5%)
    │                 │                                                          │
    │                 │                                                          └─ NO ──── 🟡 MEDIUM (neutral)
    │                 │
    │                 └─ NO ──── Age 30m-2h? ──┐ YES ─── Coverage ≥50%? ──┐ YES ─── 🟢 HIGH (+2%)
    │                                          │                          │
    │                                          │                          ├─ 33%+ ── 🟡 MEDIUM (-2%)
    │                                          │                          │
    │                                          │                          └─ <33% ── 🟠 LOW (-5%)
    │                                          │
    │                                          └─ NO ──── Age 2-12h? ──┐ YES ─── [Similar logic]
    │                                                                   │
    │                                                                   └─ NO ──── Mature (12h+)
    │
    └─ MOMENTUM SCORING (Parallel Process)
        │
        ├─ Volume Acceleration (40%)
        │   ├─ 5m→1h: Check acceleration ratio
        │   ├─ 1h→6h: Check acceleration ratio  
        │   └─ 6h→24h: Check acceleration ratio
        │
        ├─ Momentum Cascade (35%)
        │   ├─ 5m price change (highest weight)
        │   ├─ 15m-30m price changes
        │   └─ 1h price change
        │
        └─ Activity Surge (25%)
            ├─ 5m trade count
            ├─ 1h trade count
            └─ Unique trader diversity
```

## Component Scoring Breakdown

```
VOLUME ACCELERATION (0-0.4 points)
┌─────────────────────────────────────┐
│ 5m→1h Acceleration                  │
│ ├─ >3.0x: +0.15 (EXPLOSIVE) 🚀      │
│ ├─ >2.0x: +0.10 (Strong) 📈         │
│ └─ >1.5x: +0.05 (Moderate) 📊       │
│                                     │
│ 1h→6h Acceleration                  │
│ ├─ >2.0x: +0.10 (Strong) 📈         │
│ └─ >1.5x: +0.05 (Moderate) 📊       │
│                                     │
│ 6h→24h Acceleration                 │
│ └─ >1.5x: +0.05 (Building) 📊       │
│                                     │
│ Consistency Bonus                   │
│ └─ 2+ accelerating: +0.05 🎯        │
└─────────────────────────────────────┘

MOMENTUM CASCADE (0-0.35 points)
┌─────────────────────────────────────┐
│ Ultra-short (5m)                    │
│ ├─ >15%: +0.15 (EXPLOSIVE) 🚀       │
│ ├─ >10%: +0.10 (Strong) 📈          │
│ └─ >5%: +0.05 (Moderate) 📊         │
│                                     │
│ Short-term (15m-30m)                │
│ ├─ >10%: +0.08 (Building) 📈        │
│ └─ >5%: +0.04 (Early) 📊            │
│                                     │
│ Medium-term (1h)                    │
│ ├─ >20%: +0.07 (Strong) 📈          │
│ └─ >10%: +0.04 (Moderate) 📊        │
│                                     │
│ Cascade Bonus                       │
│ └─ 3+ positive: +0.05 🎯            │
└─────────────────────────────────────┘

ACTIVITY SURGE (0-0.25 points)
┌─────────────────────────────────────┐
│ Short-term (5m)                     │
│ ├─ >20 trades: +0.10 (INTENSE) 🔥   │
│ ├─ >10 trades: +0.06 (High) 📈      │
│ └─ >5 trades: +0.03 (Moderate) 📊   │
│                                     │
│ Medium-term (1h)                    │
│ ├─ >200 trades: +0.08 (Very High)📈 │
│ ├─ >100 trades: +0.05 (High) 📊     │
│ └─ >50 trades: +0.02 (Moderate) 📊  │
│                                     │
│ Trader Diversity                    │
│ ├─ >100 unique: +0.05 👥            │
│ └─ >50 unique: +0.02 👥             │
└─────────────────────────────────────┘
```

## Confidence Level Matrix

```
                    ULTRA_EARLY    EARLY       ESTABLISHED    MATURE
                    (0-30min)      (30m-2h)    (2-12h)        (12h+)
                    ┌────────────┬─────────────┬──────────────┬─────────────┐
Coverage ≥83%       │     -      │      -      │      -       │ 🟢 HIGH     │
Coverage ≥67%       │     -      │      -      │ 🟢 HIGH      │ 🟡 MEDIUM   │
Coverage ≥50%       │     -      │ 🟢 HIGH     │ 🟡 MEDIUM    │ 🟠 LOW      │
Coverage ≥33%       │     -      │ 🟡 MEDIUM   │ 🟠 LOW       │ 🔴 VERY_LOW │
Multiple + Short    │ 🚀 EARLY   │      -      │      -       │      -      │
Single Signal       │ 🟡 MEDIUM  │      -      │      -       │      -      │
Only Long-term      │ 🟠 LOW     │      -      │      -       │      -      │
No Data             │ 🟠 LOW     │ 🟠 LOW      │ 🟠 LOW       │ 🔴 VERY_LOW │
                    └────────────┴─────────────┴──────────────┴─────────────┘

Legend:
🚀 EARLY_DETECTION: +5% bonus (genuine early momentum)
🟢 HIGH: +2% bonus (excellent data)
🟡 MEDIUM: -2% penalty (moderate data)
🟠 LOW: -5% penalty (limited data)
🔴 VERY_LOW: -10% penalty (poor data quality)
```

## Real-Time Processing Flow

```
API Data Ingestion
        │
        ▼
┌───────────────────┐    ┌───────────────────┐    ┌───────────────────┐
│   DexScreener     │    │   Birdeye OHLCV   │    │   Birdeye Core    │
│                   │    │                   │    │                   │
│ • 5m, 1h, 6h,24h  │    │ • 15m, 30m       │    │ • Unique traders  │
│ • Volume data     │    │ • OHLC candles    │    │ • Holder counts   │
│ • Price changes   │    │ • Price movements │    │ • Social metrics  │
│ • Trade counts    │    │ • Volume spikes   │    │ • Metadata        │
└─────────┬─────────┘    └─────────┬─────────┘    └─────────┬─────────┘
          │                        │                        │
          └────────────────────────┼────────────────────────┘
                                   │
                                   ▼
                        ┌─────────────────────┐
                        │  Data Aggregation   │
                        │                     │
                        │ • Merge timeframes  │
                        │ • Calculate ratios  │
                        │ • Estimate token age│
                        │ • Quality assessment│
                        └─────────┬───────────┘
                                  │
                                  ▼
                        ┌─────────────────────┐
                        │ Momentum Analysis   │
                        │                     │
                        │ • Confidence check  │
                        │ • Component scoring │
                        │ • Final adjustment  │
                        │ • Alert generation  │
                        └─────────┬───────────┘
                                  │
                                  ▼
                        ┌─────────────────────┐
                        │   Output Results    │
                        │                     │
                        │ • Final score       │
                        │ • Confidence level  │
                        │ • Alert status      │
                        │ • Detailed breakdown│
                        └─────────────────────┘
```

---

*This visual documentation provides a clear understanding of how the momentum scoring system processes token data through multiple layers to arrive at accurate, confidence-adjusted scores.* 