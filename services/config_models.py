from typing import List, Dict, Optional, Tuple
from pydantic import BaseModel, Field, HttpUrl

# Pydantic models for config.yaml structure

class SolanaRpcConfig(BaseModel):
    rpc_url: HttpUrl = Field(default="https://api.mainnet-beta.solana.com")
    enhanced_rpc_url: HttpUrl = Field(default="https://api.mainnet-beta.solana.com")
    rpc_timeout: int = Field(default=10, ge=1)
    commitment_level: str = Field(default="confirmed")

class DatabaseConfig(BaseModel):
    name: str = Field(default="virtuoso_gems.db")
    log_level: str = Field(default="INFO")

class TelegramAlerterConfig(BaseModel):
    enabled: bool = Field(default=True)
    message_template_new_gem: str = Field(default=
        "💎 New Potential Gem Found! 💎\n"
        "Symbol: {symbol}\n"
        "Price: ${price:.6f}\nMCap: ${mcap:,.0f}\nLiq: ${liquidity:,.0f}\n"
        "<a href='https://dexscreener.com/solana/{pair_address}'>DexScreener</a>"
    )
    message_template_update: str = Field(default=
        "📊 Token Update: {symbol}\n"
        "Price: ${price:.6f}\nMCap: ${mcap:,.0f}\n"
        "Details: {update_details}"
    )

class ScoreWeightsConfig(BaseModel):
    liquidity: float = Field(default=20.0)
    market_cap: float = Field(default=15.0)
    holders: float = Field(default=10.0)
    volume: float = Field(default=10.0) # This corresponds to volume_to_mcap_ratio
    holder_distribution: float = Field(default=5.0)
    supply_distribution: float = Field(default=5.0)
    security: float = Field(default=15.0)
    price_stability: float = Field(default=5.0)
    age: float = Field(default=5.0)
    volume_trend: float = Field(default=5.0) # Corresponds to volume_trend_composite
    transaction_trend: float = Field(default=5.0)
    smart_contract: float = Field(default=0.0) # Weight for smart_contract score

class ApiClientConfig(BaseModel):
    enabled: bool = Field(default=True)
    api_key: Optional[str] = Field(default=None)
    base_url: Optional[HttpUrl] = Field(default=None)

class WalletAnalysisConfig(BaseModel):
    enabled: bool = Field(default=True)
    wallet_cache_dir: str = Field(default="./cache/wallets")
    max_wallets_to_analyze_per_token: int = Field(default=10, ge=1)
    min_balance_for_tracking_usd: int = Field(default=1000, ge=0)

class SmartMoneyClusteringConfig(BaseModel):
    enabled: bool = Field(default=False)
    min_wallets_for_clustering: int = Field(default=5, ge=2)
    recalculate_interval_hours: int = Field(default=12, ge=1)

class SmartMoneyConfig(BaseModel):
    enabled: bool = Field(default=False)
    wallet_cache_dir: str = Field(default="./cache/smart_money")
    min_confidence_score: float = Field(default=0.7, ge=0, le=1)
    clustering: SmartMoneyClusteringConfig = Field(default_factory=SmartMoneyClusteringConfig)

class BehavioralScoringConfig(BaseModel):
    enabled: bool = Field(default=False)
    cache_dir: str = Field(default="./cache/behavioral")
    early_signal_weights: Dict[str, float] = Field(default_factory=dict)
    trailing_signal_weights: Dict[str, float] = Field(default_factory=dict)

class MomentumAnalysisWeightsConfig(BaseModel):
    price_momentum: float = Field(default=0.30)
    volume_momentum: float = Field(default=0.25)
    holder_growth: float = Field(default=0.20)
    transaction_velocity: float = Field(default=0.15)
    net_flow: float = Field(default=0.10)

class MomentumAnalysisConfig(BaseModel):
    enabled: bool = Field(default=True)
    cache_dir: str = Field(default="./cache/momentum")
    timeframes: List[str] = Field(default_factory=lambda: ["5m", "15m", "1h", "6h", "24h"])
    weights: MomentumAnalysisWeightsConfig = Field(default_factory=MomentumAnalysisWeightsConfig)
    score_impact_percentage: Tuple[float, float] = Field(default=(-15.0, 20.0))
    # normalization_params and tx_velocity_config, net_flow_config could be nested models too
    normalization_params: Dict[str, float] = Field(default_factory=lambda: {
        "price_change_scale": 0.2, "volume_change_scale": 1.0,
        "holder_growth_scale": 0.1, "tx_velocity_scale": 100.0,
        "net_flow_scale": 0.5
    })
    transaction_velocity_config: Dict[str, Any] = Field(default_factory=lambda: {
        "lookback_seconds": 3600, "min_tx_count_for_max_score": 200
    })
    net_flow_config: Dict[str, Any] = Field(default_factory=lambda: {
        "lookback_seconds": 3600, "cex_wallets_list_url": None
    })

class EnhancedScoringConfig(BaseModel):
    enabled: bool = Field(default=True)
    cache_ttl_seconds: int = Field(default=3600, ge=60)
    min_base_score_for_trigger: int = Field(default=65, ge=0, le=100)
    wallet_analysis: WalletAnalysisConfig = Field(default_factory=WalletAnalysisConfig)
    smart_money: SmartMoneyConfig = Field(default_factory=SmartMoneyConfig)
    behavioral_scoring: BehavioralScoringConfig = Field(default_factory=BehavioralScoringConfig)
    momentum_analysis: MomentumAnalysisConfig = Field(default_factory=MomentumAnalysisConfig)

class FeaturesConfig(BaseModel):
    enable_trend_analysis: bool = Field(default=True)
    enable_volume_trend_filter: bool = Field(default=True)
    enable_txn_trend_filter: bool = Field(default=True)

class TokenFiltersConfig(BaseModel):
    min_age_minutes: int = Field(default=5, ge=0)
    min_reply_count: int = Field(default=0, ge=0)
    min_buy_count_5m: int = Field(default=3, ge=0)
    min_sell_count_5m: int = Field(default=0, ge=0)
    min_volume_usd_5m: int = Field(default=100, ge=0)
    check_freeze_authority: bool = Field(default=True)
    check_mint_authority: bool = Field(default=True)
    liquidity_concentration_threshold: float = Field(default=0.7, ge=0, le=1)
    max_pair_age_hours: int = Field(default=24*3, ge=1) # Default max age for a pair to be considered new
    volume_trends: Dict[str, float] = Field(default_factory=lambda: {"min_trend_score": 0.5, "min_acceleration": 50.0})
    tx_trends: Dict[str, float] = Field(default_factory=lambda: {"min_trend_score": 0.5})

class LoggingConfig(BaseModel):
    level: str = Field(default="INFO")
    log_file_path: str = Field(default="logs/virtuoso_gem_finder.log")
    max_file_size_mb: int = Field(default=10, ge=1)
    backup_count: int = Field(default=5, ge=1)
    metrics_log_interval_seconds: int = Field(default=300, ge=60)

class AppConfig(BaseModel):
    debug_mode: bool = Field(default=False)
    min_liquidity: int = Field(default=10000, ge=0)
    max_liquidity: int = Field(default=100000, ge=0)
    min_market_cap: int = Field(default=1000, ge=0)
    max_market_cap: int = Field(default=2000000, ge=0)
    min_holder_count: int = Field(default=50, ge=0)
    max_holder_count: int = Field(default=10000, ge=0)
    # min_age_minutes, min_txns_5m, min_volume_5m are now part of TokenFiltersConfig
    whale_threshold: float = Field(default=0.05, ge=0, le=1)
    min_gem_score: int = Field(default=70, ge=0, le=100)
    scan_interval: int = Field(default=30, ge=1)
    pair_recheck_interval_seconds: int = Field(default=300, ge=10)
    pair_check_cache_expiry_seconds: int = Field(default=3600, ge=60)
    scan_interval_error_fallback: int = Field(default=60, ge=5)
    price_discrepancy_alert_threshold_pct: float = Field(default=5.0, ge=0)
    background_task_interval_seconds: int = Field(default=3600, ge=60)

    solana_rpc: SolanaRpcConfig = Field(default_factory=SolanaRpcConfig)
    database: DatabaseConfig = Field(default_factory=DatabaseConfig)
    telegram_alerter: TelegramAlerterConfig = Field(default_factory=TelegramAlerterConfig)
    score_weights: ScoreWeightsConfig = Field(default_factory=ScoreWeightsConfig)
    
    dexscreener_api: ApiClientConfig = Field(default_factory=lambda: ApiClientConfig(base_url="https://api.dexscreener.com/latest/dex"))
    solscan_api: ApiClientConfig = Field(default_factory=ApiClientConfig)
    helius_api: ApiClientConfig = Field(default_factory=lambda: ApiClientConfig(enabled=False))
    jupiter_api: ApiClientConfig = Field(default_factory=lambda: ApiClientConfig(enabled=True)) # Jupiter often doesn't need a key
    rug_check_api: ApiClientConfig = Field(default_factory=lambda: ApiClientConfig(enabled=False))
    
    enhanced_scoring: EnhancedScoringConfig = Field(default_factory=EnhancedScoringConfig)
    features: FeaturesConfig = Field(default_factory=FeaturesConfig)
    token_filters: TokenFiltersConfig = Field(default_factory=TokenFiltersConfig)
    logging: LoggingConfig = Field(default_factory=LoggingConfig)

    class Config:
        validate_assignment = True # Ensure validation on assignment after creation 