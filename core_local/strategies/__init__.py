"""
Token Discovery Strategies Package

This package contains all token discovery strategies that implement the 
Enhanced Endpoint Integration Plan.

Available Strategies:
- BaseTokenDiscoveryStrategy: Base class for all strategies
- VolumeMomentumStrategy: Identify tokens with significant trading activity growth
- RecentListingsStrategy: Discover newly listed tokens gaining market attention
- PriceMomentumStrategy: Find tokens with strong price performance backed by volume
- LiquidityGrowthStrategy: Find tokens rapidly gaining liquidity
- HighTradingActivityStrategy: Discover tokens with unusually high trading activity
- SmartMoneyWhaleStrategy: Discover tokens based on whale and smart money activity patterns
"""

# Import base strategy
from .base_token_discovery_strategy import BaseTokenDiscoveryStrategy

# Import all strategy implementations
from .volume_momentum_strategy import VolumeMomentumStrategy
from .recent_listings_strategy import RecentListingsStrategy
from .price_momentum_strategy import PriceMomentumStrategy
from .liquidity_growth_strategy import LiquidityGrowthStrategy
from .high_trading_activity_strategy import HighTradingActivityStrategy
from .smart_money_whale_strategy import SmartMoneyWhaleStrategy

# Export all classes
__all__ = [
    'BaseTokenDiscoveryStrategy',
    'VolumeMomentumStrategy',
    'RecentListingsStrategy',
    'PriceMomentumStrategy',
    'LiquidityGrowthStrategy',
    'HighTradingActivityStrategy',
    'SmartMoneyWhaleStrategy'
] 