"""
Token Discovery Strategies

This module serves as an import aggregator for all token discovery strategies.
It maintains backward compatibility by importing all strategies from their
individual files.

Main strategies implemented:
1. Volume Momentum Strategy - Tokens with significant trading activity growth
2. Recent Listings with Traction - Newly listed tokens gaining market attention
3. Price Momentum with Volume Confirmation - Strong price performance with volume
4. Liquidity Growth Detector - Tokens gaining liquidity rapidly
5. High Trading Activity Filter - High trading activity relative to market cap
"""

# Import all strategies from the strategies package
from core.strategies import (
    BaseTokenDiscoveryStrategy,
    VolumeMomentumStrategy,
    RecentListingsStrategy,
    PriceMomentumStrategy,
    LiquidityGrowthStrategy,
    HighTradingActivityStrategy
)

# Export all strategies for backward compatibility
__all__ = [
    'BaseTokenDiscoveryStrategy',
    'VolumeMomentumStrategy',
    'RecentListingsStrategy',
    'PriceMomentumStrategy',
    'LiquidityGrowthStrategy',
    'HighTradingActivityStrategy'
] 