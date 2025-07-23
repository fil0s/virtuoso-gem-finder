# Token Age-Aware Timeframe Selection

## Overview

The system now automatically selects appropriate timeframes for analyzing token price movements based on token age. This feature is particularly valuable for newly launched tokens where historical data is limited. By dynamically adapting the timeframe selection to the token's maturity, we ensure that analysis is performed with the most appropriate data granularity.

## Implementation

The token age detection and timeframe selection logic has been implemented in two main components:

1. The `get_token_age` method in the `BirdeyeAPI` class determines token age by:
   - Checking token creation info endpoint
   - Falling back to token security data
   - As a last resort, finding the earliest transaction
   
2. The `get_ohlcv_data` method selects appropriate timeframes when the `auto` timeframe is requested, based on token age.

## Age Categories and Timeframes

The system supports all timeframes offered by the Birdeye API, from 1-second to 1-week candles, and implements a highly granular age classification system:

| Age Category | Age Range | Primary Timeframe | Fallback Timeframes |
|--------------|-----------|-------------------|---------------------|
| Ultra New    | < 15 minutes | 1s | 15s, 30s, 1m |
| Very New     | 15 min - 1 hour | 15s | 30s, 1m, 5m |
| New          | 1-6 hours | 30s | 1m, 5m, 15m |
| Very Recent  | 6-24 hours | 1m | 5m, 15m, 30m |
| Recent       | 1-3 days | 5m | 15m, 30m, 1h |
| Developing   | 3-7 days | 15m | 30m, 1h, 2h |
| Emerging     | 7-14 days | 30m | 1h, 2h, 4h |
| Established  | 14-30 days | 1h | 2h, 4h, 6h |
| Mature (3mo) | 1-3 months | 2h | 4h, 6h, 12h |
| Mature (6mo) | 3-6 months | 4h | 6h, 12h, 1d |
| Veteran      | > 6 months | 6h | 12h, 1d, 3d |

## Dynamic Fallback System

For each age category, the system defines multiple fallback timeframes to try if the primary timeframe doesn't return data. This ensures maximum data availability while maintaining appropriate granularity.

## Code Example

```python
async def get_token_age(token_address: str) -> tuple[float, str]:
    """
    Determine token age in days and corresponding age category.
    
    Returns:
        Tuple of (age_in_days, age_category)
    """
    # Implementation details...
    # Categories: 'ultra_new', 'very_new', 'new', 'very_recent', 'recent', 
    # 'developing', 'emerging', 'established', 'mature', 'veteran'
```

## Example Use Case

1. A token launched 3 hours ago is classified as "New" (1-6 hours)
2. The system selects the 30s timeframe as primary
3. If no data is available at 30s, it tries 1m, then 5m, then 15m
4. If data is found, it performs analysis with the appropriate timeframe
5. For tokens older than 6 months, it uses 6h candles to improve performance

## Benefits

- **Better Analysis of New Tokens**: Ultra-fine granularity (down to 1s) for very new tokens
- **Full Data Spectrum**: 15 different timeframes across all token age ranges
- **Intelligent Fallbacks**: System tries multiple timeframes to maximize data availability
- **Performance Optimization**: Longer timeframes for mature tokens improve query efficiency
- **Enhanced Trend Detection**: Age-appropriate timeframes improve signal detection

## Next Steps

1. Monitor performance of this enhanced timeframe selection system
2. Collect metrics on which timeframes are most effective for each age category
3. Consider adding token-specific timeframe adjustments based on volatility and trading volume
4. Develop visualization tools that display multiple timeframes simultaneously for comprehensive analysis 