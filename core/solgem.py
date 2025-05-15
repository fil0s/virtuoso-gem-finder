import requests
import time
import sqlite3
from datetime import datetime
import logging
from dataclasses import dataclass, field
from typing import List, Dict, Optional, Any
import json
from pathlib import Path
import threading
from logging.handlers import RotatingFileHandler
from pydantic import BaseModel, Field, validator
from tenacity import retry, stop_after_attempt, wait_exponential
from collections import deque
import signal
import sys
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
import traceback
import inspect
import psutil
import math
import statistics
import asyncio
# Import the API connectors
from api.jupiter_connector import JupiterAPI
from api.helius_connector import HeliusAPI
from api.solana_rpc_enhanced import EnhancedSolanaRPC
# Import the enhanced scoring system
from analysis.enhanced_scoring import EnhancedScoring
from services.logger_setup import LoggerSetup
from services.config_handler import ConfigHandler
from services.dexscreener_api import DexScreenerAPI
from services.solscan_api import SolscanAPI
from services.database_manager import DatabaseManager
from services.telegram_alerter import TelegramAlerter
from services.rug_check_api import RugCheckAPI
from services.gem_scorer import GemScorer
from services.whale_tracker import WhaleTracker, WhaleWallet
from services.trend_analysis_service import TrendAnalysisService
from services.filtering_service import FilteringService
from services.token_enrichment_service import TokenEnrichmentService
from services.config_models import AppConfig
from pydantic import ValidationError
import yaml

# Don't import from ourselves - we are the module
# from solgem import TokenMetrics, Metrics

# Service Protocols (Interfaces)
from services.service_interfaces import (
    DexScreenerAPIProtocol,
    SolscanAPIProtocol,
    JupiterAPIProtocol,
    HeliusAPIProtocol,
    SolanaRPCProtocol,
    DatabaseManagerProtocol,
    TelegramAlerterProtocol,
    GemScorerProtocol,
    WhaleTrackerProtocol,
    TrendAnalysisServiceProtocol,
    FilteringServiceProtocol,
    TokenEnrichmentServiceProtocol,
    EnhancedScoringProtocol
)

@dataclass
class TokenMetrics:
    address: str
    name: str
    symbol: str
    price: float
    mcap: float
    liquidity: float
    volume_24h: float
    holders: int
    creation_time: int
    whale_holdings: Dict[str, float]
    total_supply: int = 0
    decimals: int = 0
    is_mint_frozen: bool = False
    program_id: str = ""
    top_holders: List[Dict[str, Any]] = field(default_factory=list)
    security_score: float = 0.0
    risk_factors: List[str] = field(default_factory=list)
    contract_verified: bool = False
    is_honeypot: bool = False
    buy_tax: float = 0.0
    sell_tax: float = 0.0
    # Trend analysis fields
    volume_trend: str = "unknown"
    volume_trend_score: float = 0.0
    volume_acceleration: float = 0.0
    tx_count_trend: str = "unknown"
    tx_trend_score: float = 0.0
    creator_addresses: List[str] = field(default_factory=list)

@dataclass
class Metrics:
    api_calls: int = 0
    successful_calls: int = 0
    failed_calls: int = 0
    gems_found: int = 0
    response_times: deque = field(default_factory=lambda: deque(maxlen=100))

class SolscanAPI:
    def __init__(self, config: Dict):
        self.logger = LoggerSetup('SolscanAPI').logger
        self.base_url = "https://api.solscan.io"
        self.headers = {
            "Accept": "application/json",
            "User-Agent": "VirtuosoGemFinder/1.0"
        }
        self.rate_limit = 60  # Adjust based on Solscan's rate limits
        self.rate_window = 60
        self.tokens = self.rate_limit
        self.last_update = time.time()
        self.lock = threading.Lock()
        self.config = config

    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=4, max=10))
    def get_token_holders(self, token_address: str) -> int:
        """Get accurate holder count from Solscan"""
        self._rate_limit_check()
        try:
            response = requests.get(
                f"{self.base_url}/token/holders",
                params={"token": token_address},
                headers=self.headers,
                timeout=10
            )
            response.raise_for_status()
            data = response.json()
            return data.get('total', 0)
        except Exception as e:
            self.logger.error(f"Error fetching holder count: {e}")
            return 0

    def get_whale_holdings(self, token_address: str) -> Dict[str, float]:
        """Get top holder information from Solscan"""
        self._rate_limit_check()
        try:
            response = requests.get(
                f"{self.base_url}/token/holders",
                params={"token": token_address, "limit": 10},  # Top 10 holders
                headers=self.headers,
                timeout=10
            )
            response.raise_for_status()
            data = response.json()
            
            whale_holdings = {}
            total_supply = float(data.get('totalSupply', 0))
            if total_supply > 0:
                for holder in data.get('data', []):
                    amount = float(holder.get('amount', 0))
                    percentage = amount / total_supply
                    if percentage >= self.config.get('whale_threshold', 0.05):
                        whale_holdings[holder['owner']] = percentage
                        
            return whale_holdings
        except Exception as e:
            self.logger.error(f"Error fetching whale holdings: {e}")
            return {}

class TokenData(BaseModel):
    address: str
    name: str
    symbol: str
    price: float = Field(ge=0)
    mcap: float = Field(ge=0)
    liquidity: float = Field(ge=0)
    volume_24h: float = Field(ge=0)
    holders: int = Field(ge=0)
    
    @validator('price', 'mcap', 'liquidity', 'volume_24h')
    def validate_positive_float(cls, v):
        if v < 0:
            raise ValueError("Value must be positive")
        return v

class SolanaRPC:
    def __init__(self, rpc_url: str = "https://api.mainnet-beta.solana.com"):
        self.logger = LoggerSetup('SolanaRPC').logger
        self.rpc_url = rpc_url
        self.headers = {
            "Content-Type": "application/json",
            "User-Agent": "VirtuosoGemFinder/1.0"
        }

    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=4, max=10))
    def _make_request(self, method: str, params: List = None) -> Dict:
        """Make RPC request with retry logic"""
        payload = {
            "jsonrpc": "2.0",
            "id": 1,
            "method": method,
            "params": params or []
        }
        
        try:
            response = requests.post(self.rpc_url, json=payload, headers=self.headers)
            response.raise_for_status()
            return response.json()
        except Exception as e:
            self.logger.error(f"RPC request failed: {e}")
            raise

    def get_token_supply(self, token_address: str) -> Optional[int]:
        """Get token supply using getTokenSupply"""
        try:
            result = self._make_request("getTokenSupply", [token_address])
            return int(result['result']['value']['amount'])
        except Exception as e:
            self.logger.error(f"Failed to get token supply: {e}")
            return None

    def get_token_accounts(self, owner_address: str) -> List[Dict]:
        """Get token accounts by owner"""
        try:
            result = self._make_request(
                "getTokenAccountsByOwner",
                [
                    owner_address,
                    {"programId": "TokenkegQfeZyiNwAJbNbGKPFXCWuBvf9Ss623VQ5DA"},
                    {"encoding": "jsonParsed"}
                ]
            )
            return result['result']['value']
        except Exception as e:
            self.logger.error(f"Failed to get token accounts: {e}")
            return []

    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=4, max=10))
    def get_account_info(self, address: str) -> Dict:
        """Get detailed account information"""
        try:
            result = self._make_request(
                "getAccountInfo",
                [address, {"encoding": "jsonParsed", "commitment": "confirmed"}]
            )
            return result.get('result', {}).get('value', {})
        except Exception as e:
            self.logger.error(f"Failed to get account info: {e}")
            return {}

    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=4, max=10))
    def get_signature_history(self, address: str, limit: int = 10) -> List[Dict]:
        """Get transaction signature history for an address"""
        try:
            result = self._make_request(
                "getSignaturesForAddress",
                [address, {"limit": limit}]
            )
            return result.get('result', [])
        except Exception as e:
            self.logger.error(f"Failed to get signature history: {e}")
            return []

@dataclass
class ScoreWeights:
    liquidity: float = 0.20        # 20% - Critical for trading
    market_cap: float = 0.15       # 15% - Project size
    holders: float = 0.15          # 15% - Community strength
    volume: float = 0.15           # 15% - Trading activity
    holder_distribution: float = 0.10  # 10% - Ownership concentration
    supply_distribution: float = 0.10  # 10% - Token distribution
    security: float = 0.08         # 8% - Contract security
    price_stability: float = 0.04  # 4% - Price volatility
    age: float = 0.03             # 3% - Project maturity

class GemScorer:
    def __init__(self, config: Dict):
        self.config = config
        self.weights = ScoreWeights(**config.get('score_weights', {}))
        self.logger = LoggerSetup('GemScorer').logger
        self.weights.security = config.get('score_weights', {}).get('security', 15.0)

    def _score_liquidity(self, liquidity: float) -> float:
        """Enhanced liquidity scoring with dynamic thresholds"""
        if liquidity <= 0:
            return 0
        
        # Logarithmic scaling for better distribution
        log_liq = math.log10(max(liquidity, 1))
        min_log = math.log10(self.config['min_liquidity'])
        max_log = math.log10(self.config['max_liquidity'])
        
        # Normalized score between 0 and 1
        score = (log_liq - min_log) / (max_log - min_log)
        return max(0.0, min(1.0, score))

    def _score_market_cap(self, mcap: float) -> float:
        """Score market cap with preference for smaller caps"""
        max_mcap = self.config['max_market_cap']
        if mcap > max_mcap:
            return 0
        return 1 - (mcap / max_mcap) ** 0.5

    def _score_holders(self, holder_count: int) -> float:
        """Score holder count with consideration for organic growth"""
        min_holders = self.config['min_holder_count']
        max_holders = self.config['max_holder_count']
        if holder_count < min_holders:
            return 0
        if holder_count > max_holders:
            return 0.7  # Penalty for potentially artificial growth
        return min(1.0, (holder_count - min_holders) / (max_holders - min_holders))

    def _score_holder_distribution(self, top_holders: List[Dict]) -> float:
        """Improved holder distribution scoring using Gini coefficient"""
        if not top_holders or len(top_holders) < 2:
            return 0

        # Extract holdings and sort
        holdings = sorted([
            float(h['account']['data']['parsed']['info']['tokenAmount']['amount'])
            for h in top_holders
        ])
        
        # Calculate Gini coefficient
        n = len(holdings)
        numerator = sum((n + 1 - i) * yi for i, yi in enumerate(holdings, 1))
        denominator = n * sum(holdings)
        
        if denominator == 0:
            return 0
            
        gini = (2 * numerator) / (n * denominator) - (n + 1) / n
        
        # Convert to score (lower Gini = better distribution)
        return 1 - gini

    def _score_age(self, creation_time: int) -> float:
        """Score based on token age with diminishing returns"""
        age_hours = (time.time() - creation_time) / 3600
        if age_hours < 24:  # Less than 24 hours
            return age_hours / 24
        return min(1.0, math.log(age_hours / 24 + 1) / math.log(8))  # Logarithmic scaling

    def _score_supply_distribution(self, whale_holdings: Dict[str, float]) -> float:
        """Score based on supply distribution and whale concentration"""
        if not whale_holdings:
            return 1.0  # No whales is good
            
        whale_concentration = sum(whale_holdings.values())
        if whale_concentration > 0.5:  # More than 50% held by whales
            return 0
        return 1 - (whale_concentration * 2)  # Linear penalty for whale concentration

    def _score_price_stability(self, historical_data: List[Dict]) -> float:
        """Score based on price stability and volatility"""
        if not historical_data:
            return 0.5  # Neutral score if no historical data
            
        prices = [d['price'] for d in historical_data]
        if len(prices) < 2:
            return 0.5
            
        # Calculate volatility
        returns = [math.log(prices[i]/prices[i-1]) for i in range(1, len(prices))]
        volatility = statistics.stdev(returns) if len(returns) > 1 else 0
        
        # Lower volatility is better
        return math.exp(-2 * volatility)

    def _score_smart_contract(self, metrics: TokenMetrics) -> float:
        """Score based on smart contract analysis"""
        score = 1.0
        
        # Check if mint is frozen (good security practice)
        if metrics.is_mint_frozen:
            score *= 1.2
        
        # Check if using standard token program
        if metrics.program_id == "TokenkegQfeZyiNwAJbNbGKPFXCWuBvf9Ss623VQ5DA":
            score *= 1.1
            
        return min(1.0, score)

    def _score_security(self, metrics: TokenMetrics) -> float:
        """Enhanced security scoring with multiple factors"""
        base_score = 1.0
        risk_multiplier = 1.0
        
        # Critical security checks
        if metrics.is_honeypot:
            return 0.0
        
        # Contract verification
        if not metrics.contract_verified:
            risk_multiplier *= 0.6
        
        # Tax analysis
        total_tax = metrics.buy_tax + metrics.sell_tax
        if total_tax > 0:
            tax_penalty = math.exp(-2 * total_tax)  # Exponential penalty
            risk_multiplier *= tax_penalty
        
        # Risk factors analysis
        risk_factor_penalties = {
            'high_mint_authority': 0.7,
            'upgradeable_contract': 0.8,
            'centralized_ownership': 0.6,
            'suspicious_transfers': 0.5
        }
        
        for risk in metrics.risk_factors:
            if risk in risk_factor_penalties:
                risk_multiplier *= risk_factor_penalties[risk]
        
        return max(0.0, min(1.0, base_score * risk_multiplier))

    def calculate_score(self, metrics: TokenMetrics, historical_data: List[Dict] = None) -> Dict[str, float]:
        """Calculate comprehensive gem score with detailed breakdowns and caching"""
        cache_key = f"{metrics.address}_{metrics.price}_{metrics.mcap}"
        
        # Check cache first
        if hasattr(self, '_score_cache') and cache_key in self._score_cache:
            return self._score_cache[cache_key]
        
        try:
            # Calculate individual scores
            scores = {
                'liquidity': self._score_liquidity(metrics.liquidity),
                'market_cap': self._score_market_cap(metrics.mcap),
                'holders': self._score_holders(metrics.holders),
                'volume': self._score_volume(metrics.volume_24h, metrics.mcap),
                'volume_trend': self._score_volume_trends(metrics),
                'holder_distribution': self._score_holder_distribution(metrics.top_holders),
                'supply_distribution': self._score_supply_distribution(metrics.whale_holdings),
                'security': self._score_security(metrics),
                'price_stability': self._score_price_stability(historical_data),
                'age': self._score_age(metrics.creation_time)
            }

            # Calculate weighted score
            total_score = 0
            for key, score in scores.items():
                weight = self.config.get('score_weights', {}).get(key, getattr(self.weights, key, 0))
                total_score += score * weight / 100  # Convert weight to 0-1 scale
            
            result = {
                'total': round(total_score * 100, 2),  # Convert back to 0-100 scale
                'breakdown': {k: round(v * 100, 2) for k, v in scores.items()},  # Display as percentages
                'risk_factors': metrics.risk_factors
            }
            
            # Cache the result
            if not hasattr(self, '_score_cache'):
                self._score_cache = {}
            self._score_cache[cache_key] = result
            
            return result
            
        except Exception as e:
            self.logger.error(f"Error calculating gem score: {str(e)}")
            return {'total': 0, 'breakdown': {}, 'risk_factors': []}

    def _score_volume_trends(self, metrics: TokenMetrics) -> float:
        """
        Score based on volume and transaction trends.
        
        Args:
            metrics: Token metrics including trend data
            
        Returns:
            Score between 0.0 and 1.0
        """
        # Base score from raw volume (re-use existing method if available)
        base_score = self._score_volume(metrics.volume_24h, metrics.mcap) if hasattr(self, '_score_volume') else 0.5
        
        # Modify based on trend
        trend_multipliers = {
            "strongly_increasing": 1.5,
            "increasing": 1.3,
            "recently_increasing": 1.2,
            "stable": 1.0,
            "decreasing": 0.7,
            "unknown": 0.9,
            "error": 0.9,
            "insufficient_data": 0.8
        }
        
        trend_multiplier = trend_multipliers.get(metrics.volume_trend, 0.9)
        
        # Apply acceleration bonus for rapidly growing volume
        if metrics.volume_acceleration > 200:  # More than tripling hourly
            acceleration_bonus = 0.2
        elif metrics.volume_acceleration > 100:  # More than doubling hourly
            acceleration_bonus = 0.1
        else:
            acceleration_bonus = 0
            
        return max(0.0, min(1.0, base_score * trend_multiplier + acceleration_bonus))
    
    def _score_transaction_trends(self, metrics: TokenMetrics) -> float:
        """
        Score based on transaction count trends.
        
        Args:
            metrics: Token metrics including transaction trend data
            
        Returns:
            Score between 0.0 and 1.0
        """
        trend_scores = {
            "strongly_increasing": 1.0,
            "increasing": 0.8,
            "recently_increasing": 0.6,
            "stable": 0.4,
            "decreasing": 0.2,
            "unknown": 0.3,
            "error": 0.3,
            "insufficient_data": 0.2
        }
        
        return trend_scores.get(metrics.tx_count_trend, 0.3)

    def _score_volume(self, volume_24h: float, mcap: float) -> float:
        """
        Score token volume relative to market cap.
        Higher volume relative to market cap is better.
        
        Args:
            volume_24h: 24-hour trading volume
            mcap: Market capitalization
            
        Returns:
            Score between 0.0 and 1.0
        """
        if mcap <= 0 or volume_24h <= 0:
            return 0.0
            
        # Calculate volume as percentage of market cap
        volume_to_mcap_ratio = volume_24h / mcap
        
        # Score based on ratio with diminishing returns
        if volume_to_mcap_ratio >= 1.0:  # 100% or more of mcap traded in 24h
            return 1.0
        elif volume_to_mcap_ratio >= 0.5:  # 50% or more of mcap traded in 24h
            return 0.8 + (volume_to_mcap_ratio - 0.5) * 0.4
        elif volume_to_mcap_ratio >= 0.1:  # 10% or more of mcap traded in 24h
            return 0.5 + (volume_to_mcap_ratio - 0.1) * 0.6
        else:
            return volume_to_mcap_ratio * 5  # Linear scaling up to 10% ratio
            
    def _score_volume_trends(self, metrics: TokenMetrics) -> float:
        """
        Score based on volume and transaction trends.
        
        Args:
            metrics: Token metrics including trend data
            
        Returns:
            Score between 0.0 and 1.0
        """
        # Base score from raw volume (re-use existing method if available)
        base_score = self._score_volume(metrics.volume_24h, metrics.mcap) if hasattr(self, '_score_volume') else 0.5
        
        # Modify based on trend
        trend_multipliers = {
            "strongly_increasing": 1.5,
            "increasing": 1.3,
            "recently_increasing": 1.2,
            "stable": 1.0,
            "decreasing": 0.7,
            "unknown": 0.9,
            "error": 0.9,
            "insufficient_data": 0.8
        }
        
        trend_multiplier = trend_multipliers.get(metrics.volume_trend, 0.9)
        
        # Apply acceleration bonus for rapidly growing volume
        if metrics.volume_acceleration > 200:  # More than tripling hourly
            acceleration_bonus = 0.2
        elif metrics.volume_acceleration > 100:  # More than doubling hourly
            acceleration_bonus = 0.1
        else:
            acceleration_bonus = 0
            
        return max(0.0, min(1.0, base_score * trend_multiplier + acceleration_bonus))

@dataclass
class WalletMetrics:
    win_rate: float = 0.0
    avg_profit: float = 0.0
    trade_count: int = 0
    sell_timing_score: float = 0.0  # Higher score = suspicious timing
    price_impact_score: float = 0.0  # Higher score = more negative impact
    performance_7d: float = 0.0
    performance_30d: float = 0.0
    is_developer: bool = False
    suspicious_patterns: List[str] = field(default_factory=list)

class SmartMoneyAnalyzer:
    DEFAULT_THRESHOLDS = {
            'win_rate': 0.85,  # 85%+ win rate is suspicious
            'sell_timing': 0.8,  # 80%+ sells near local tops
            'price_impact': 0.7,  # 70%+ trades causing dumps
            'min_trades': 10,    # Minimum trades for analysis
        }

    def __init__(self, rpc: SolanaRPC, config: Optional[Dict] = None):
        self.rpc = rpc
        self.config = config or {}
        self.logger = LoggerSetup('SmartMoneyAnalyzer').logger
        self.suspicious_thresholds = self.config.get('suspicious_thresholds', self.DEFAULT_THRESHOLDS)
        self.logger.info(f"SmartMoneyAnalyzer initialized with thresholds: {self.suspicious_thresholds}")

    def analyze_wallet_trades(self, address: str, token_address: str, 
                            price_history: List[Dict]) -> WalletMetrics:
        """Analyze trading patterns for smart money detection"""
        metrics = WalletMetrics()
        
        # Get historical transactions
        signatures = self.rpc.get_signature_history(address, limit=100)
        trades = self._parse_trades(signatures, token_address)
        
        if len(trades) < self.suspicious_thresholds['min_trades']:
            return metrics
            
        # Calculate win rate and average profit
        profitable_trades = [t for t in trades if t['profit'] > 0]
        metrics.win_rate = len(profitable_trades) / len(trades)
        metrics.avg_profit = sum(t['profit'] for t in trades) / len(trades)
        metrics.trade_count = len(trades)
        
        # Analyze sell timing
        metrics.sell_timing_score = self._analyze_sell_timing(
            trades, price_history
        )
        
        # Analyze price impact
        metrics.price_impact_score = self._analyze_price_impact(
            trades, price_history
        )
        
        # Calculate performance metrics
        metrics.performance_7d = self._calculate_performance(trades, 7)
        metrics.performance_30d = self._calculate_performance(trades, 30)
        
        # Check for developer patterns
        metrics.is_developer = self._check_developer_patterns(
            address, token_address
        )
        
        # Flag suspicious patterns
        metrics.suspicious_patterns = self._identify_suspicious_patterns(metrics)
        
        return metrics

    def _parse_trades(self, signatures: List[Dict], 
                     token_address: str) -> List[Dict]:
        """Parse transaction signatures into trade data"""
        trades = []
        for sig in signatures:
            try:
                tx_data = self.rpc.get_transaction(sig['signature'])
                if self._is_token_transaction(tx_data, token_address):
                    trade = {
                        'timestamp': sig['blockTime'],
                        'type': self._determine_trade_type(tx_data),
                        'amount': self._calculate_trade_amount(tx_data),
                        'price': self._get_price_at_time(tx_data),
                        'profit': self._calculate_trade_profit(tx_data)
                    }
                    trades.append(trade)
            except Exception as e:
                self.logger.error(f"Error parsing trade: {str(e)}")
                continue
        return trades

    def _analyze_sell_timing(self, trades: List[Dict], 
                           price_history: List[Dict]) -> float:
        """Analyze how often sells occur near local price tops"""
        if not trades or not price_history:
            return 0.0
            
        sells_near_top = 0
        total_sells = 0
        
        for trade in trades:
            if trade['type'] != 'sell':
                continue
                
            total_sells += 1
            if self._is_near_local_top(trade['timestamp'], price_history):
                sells_near_top += 1
                
        return sells_near_top / total_sells if total_sells > 0 else 0.0

    def _analyze_price_impact(self, trades: List[Dict], 
                            price_history: List[Dict]) -> float:
        """Analyze price impact after trades"""
        if not trades or not price_history:
            return 0.0
            
        negative_impacts = 0
        total_trades = 0
        
        for trade in trades:
            total_trades += 1
            if self._causes_price_dump(trade, price_history):
                negative_impacts += 1
                
        return negative_impacts / total_trades if total_trades > 0 else 0.0

    def _check_developer_patterns(self, address: str, 
                                token_address: str) -> bool:
        """Check if wallet shows developer patterns"""
        try:
            # Check contract creation involvement
            creation_tx = self._find_contract_creation(token_address)
            if creation_tx and address in creation_tx['signers']:
                return True
                
            # Check for contract upgrades/admin functions
            admin_txs = self._find_admin_transactions(token_address)
            if any(address in tx['signers'] for tx in admin_txs):
                return True
                
            # Check for early token minting/distribution
            early_txs = self._get_early_token_transactions(token_address)
            if any(address in tx['signers'] for tx in early_txs):
                return True
                
            return False
            
        except Exception as e:
            self.logger.error(f"Error checking developer patterns: {str(e)}")
            return False

    def _identify_suspicious_patterns(self, 
                                   metrics: WalletMetrics) -> List[str]:
        """Identify suspicious trading patterns"""
        patterns = []
        
        if metrics.win_rate > self.suspicious_thresholds['win_rate']:
            patterns.append(
                f"Unusually high win rate: {metrics.win_rate:.1%}"
            )
            
        if metrics.sell_timing_score > self.suspicious_thresholds['sell_timing']:
            patterns.append(
                f"Suspicious sell timing: {metrics.sell_timing_score:.1%} "
                "near local tops"
            )
            
        if metrics.price_impact_score > self.suspicious_thresholds['price_impact']:
            patterns.append(
                f"High negative price impact: {metrics.price_impact_score:.1%} "
                "of trades"
            )
            
        if metrics.is_developer and metrics.trade_count > 0:
            patterns.append(
                "Developer wallet with active trading"
            )
            
        return patterns

class WhaleTracker:
    DEFAULT_SUSPICIOUS_PATTERNS = {
        'new_wallet_max_age_seconds': 24 * 3600,  # Wallet younger than 24 hours
        'high_frequency_min_txns_24h': 100,     # More than 100 transactions in 24h
        # 'contract_interaction': True  # This seems too vague, might need specific contract types/flags
    }

    def __init__(self, rpc: SolanaRPC, db: DatabaseManager, smart_money_analyzer: SmartMoneyAnalyzer, config: Optional[Dict] = None):
        self.rpc = rpc
        self.db = db
        self.smart_money_analyzer = smart_money_analyzer # Use the passed instance
        self.config = config or {}
        self.logger = LoggerSetup('WhaleTracker').logger
        
        # Load its own configurable patterns
        self.suspicious_patterns = self.config.get('suspicious_patterns', self.DEFAULT_SUSPICIOUS_PATTERNS)
        self.logger.info(f"WhaleTracker initialized with suspicious patterns: {self.suspicious_patterns}")

    def analyze_whale_wallet(self, address: str, 
                           holding_amount: float,
                           token_address: str,
                           price_history: List[Dict]) -> WhaleWallet:
        """Enhanced whale wallet analysis with smart money tracking"""
        wallet = super().analyze_whale_wallet(address, holding_amount)
        
        # Add smart money analysis
        smart_money_metrics = self.smart_money_analyzer.analyze_wallet_trades(
            address, token_address, price_history
        )
        
        # Update wallet risk assessment based on smart money analysis
        if smart_money_metrics.suspicious_patterns:
            wallet.risk_factors.extend(smart_money_metrics.suspicious_patterns)
            
        if smart_money_metrics.is_developer:
            wallet.is_developer = True
            
        # Store detailed metrics in database
        self._store_wallet_metrics(
            token_address, address, smart_money_metrics
        )
        
        return wallet

    def _verify_wallet_legitimacy(self, address: str, wallet_age: int, 
                                tx_count: int, is_contract: bool) -> bool:
        """Verify if a whale wallet appears legitimate"""
        suspicious_factors = []
        
        # Check wallet age
        if wallet_age < self.suspicious_patterns['new_wallet_max_age_seconds']:
            suspicious_factors.append('New wallet')
            
        # Check transaction frequency
        if tx_count > self.suspicious_patterns['high_frequency_min_txns_24h']:
            suspicious_factors.append('High transaction frequency')
            
        # Check if it's a contract
        if is_contract and self.suspicious_patterns['contract_interaction']:
            suspicious_factors.append('Contract address')
            
        if suspicious_factors:
            self.logger.warning(
                f"Suspicious whale wallet {address}: {', '.join(suspicious_factors)}"
            )
            return False
            
        return True

    def track_whale_movements(self, token_address: str, 
                            whale_holdings: Dict[str, float]) -> Dict[str, WhaleWallet]:
        """Track and analyze whale wallet movements"""
        verified_whales = {}
        
        for address, amount in whale_holdings.items():
            whale_data = self.analyze_whale_wallet(address, amount)
            if whale_data.verified:
                verified_whales[address] = whale_data
                self._update_whale_tracking(token_address, whale_data)
                
        return verified_whales

    def _update_whale_tracking(self, token_address: str, whale: WhaleWallet):
        """Update whale tracking information in database"""
        with self.db.pool as conn:
            conn.execute('''
                INSERT OR REPLACE INTO whale_holdings
                (token_address, whale_address, holding_percentage, last_updated,
                 transaction_count, wallet_age, is_contract, verified)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                token_address,
                whale.address,
                whale.holdings,
                int(time.time()),
                whale.transaction_count,
                whale.wallet_age,
                whale.is_contract,
                whale.verified
            ))

class VirtuosoGemFinder:
    # Type hint attributes with Protocols
    config: AppConfig
    dex_screener: DexScreenerAPIProtocol
    db: DatabaseManagerProtocol
    telegram: TelegramAlerterProtocol
    solana_rpc: SolanaRPCProtocol # Or a more specific base SolanaRPC protocol if needed
    enhanced_rpc: SolanaRPCProtocol # Using general one, or define specific EnhancedSolanaRPCProtocol
    solscan_api: Optional[SolscanAPIProtocol]
    helius_api: Optional[HeliusAPIProtocol]
    jupiter_api: Optional[JupiterAPIProtocol]
    rug_check_api: Optional[Any] # Replace Any with RugCheckAPIProtocol if created
    gem_scorer: GemScorerProtocol
    smart_money_analyzer: Any # Replace Any with SmartMoneyAnalyzerProtocol if created and used directly by VGF
    whale_tracker: WhaleTrackerProtocol
    trend_analyzer: TrendAnalysisServiceProtocol
    filtering_service: FilteringServiceProtocol
    token_enrichment_service: TokenEnrichmentServiceProtocol
    enhanced_scoring: Optional[EnhancedScoringProtocol]

    def __init__(self, telegram_bot_token: Optional[str], telegram_chat_id: Optional[str]):
        self.logger_setup = LoggerSetup('VirtuosoGemFinder') # Store LoggerSetup instance
        self.logger = self.logger_setup.get_logger('VirtuosoGemFinder')
        self.config_file_name = "config.yaml"
        
        loaded_config_dict = self._load_raw_config_dict()
        try:
            self.config = AppConfig(**loaded_config_dict)
            self.logger.info(f"Configuration loaded and validated from {self.config_file_name}.")
        except ValidationError as e:
            self.logger.error(f"Config validation error from {self.config_file_name}:\n{e}")
            self.logger.warning("Falling back to default Pydantic model config.")
            self.config = AppConfig()
        except Exception as e_parse:
            self.logger.error(f"Critical error parsing config: {e_parse}", exc_info=True)
            self.logger.warning("Critical error: Falling back to default Pydantic model config.")
            self.config = AppConfig()

        self.loop = asyncio.get_event_loop()
        self.debug_mode = self.config.debug_mode
        if self.debug_mode:
            self.logger.info("Debug mode enabled via configuration.")

        # Initialize services (assigning concrete implementations to protocol-typed attributes)
        self.dex_screener: DexScreenerAPIProtocol = DexScreenerAPI() 
        self.db: DatabaseManagerProtocol = DatabaseManager(db_name=self.config.database.name, logger_setup=self.logger_setup)
        
        if telegram_bot_token and telegram_chat_id: # Only init if token/chat_id provided
            self.telegram: TelegramAlerterProtocol = TelegramAlerter(
                telegram_bot_token, 
                telegram_chat_id, 
                config=self.config.telegram_alerter.model_dump(),
                logger_setup=self.logger_setup
            )
        else:
            self.logger.warning("Telegram token or chat ID missing, TelegramAlerter disabled.")
            # Create a NullAlerter or ensure optional handling if telegram is None
            class NullAlerter(TelegramAlerterProtocol):
                async def send_gem_alert(self, *args, **kwargs): self.logger.debug("NullAlerter: send_gem_alert called")
                async def send_message(self, *args, **kwargs): self.logger.debug("NullAlerter: send_message called")
            self.telegram: TelegramAlerterProtocol = NullAlerter()
            self.telegram.logger = self.logger_setup.get_logger('NullAlerter') # Give it a logger

        self.solana_rpc: SolanaRPCProtocol = SolanaRPC(rpc_url=str(self.config.solana_rpc.rpc_url), logger_setup=self.logger_setup)
        self.enhanced_rpc: SolanaRPCProtocol = EnhancedSolanaRPC(rpc_url=str(self.config.solana_rpc.enhanced_rpc_url), logger_setup=self.logger_setup)

        self.solscan_api = SolscanAPI(config=self.config.model_dump(), logger_setup=self.logger_setup) if self.config.solscan_api.enabled else None
        if self.solscan_api: self.logger.info("SolscanAPI initialized.") 
        else: self.logger.info("SolscanAPI disabled.")

        self.helius_api = HeliusAPI(api_key=self.config.helius_api.api_key, logger_setup=self.logger_setup) if self.config.helius_api.enabled and self.config.helius_api.api_key else None
        if self.helius_api: self.logger.info("HeliusAPI initialized.")
        else: self.logger.info("HeliusAPI disabled or API key missing.")

        self.jupiter_api = JupiterAPI(rpc_url=str(self.config.jupiter_api.base_url or self.config.solana_rpc.rpc_url), logger_setup=self.logger_setup) if self.config.jupiter_api.enabled else None
        if self.jupiter_api: self.logger.info(f"JupiterAPI initialized with {self.jupiter_api.rpc_url}.")
        else: self.logger.info("JupiterAPI disabled.")
        
        self.rug_check_api = RugCheckAPI(api_key=self.config.rug_check_api.api_key, logger_setup=self.logger_setup) if self.config.rug_check_api.enabled and self.config.rug_check_api.api_key else None
        if self.rug_check_api: self.logger.info("RugCheckAPI initialized.")
        else: self.logger.info("RugCheckAPI disabled or API key missing.")

        self.gem_scorer: GemScorerProtocol = GemScorer(config=self.config.model_dump(), logger_setup=self.logger_setup)
        self.logger.info("GemScorer initialized.")

        # SmartMoneyAnalyzer might not have a dedicated protocol yet, or its methods are internal to WhaleTracker uses
        self.smart_money_analyzer = SmartMoneyAnalyzer(rpc=self.enhanced_rpc, config=self.config.enhanced_scoring.smart_money.model_dump(), logger_setup=self.logger_setup)
        self.logger.info("SmartMoneyAnalyzer initialized.")
        
        self.whale_tracker: WhaleTrackerProtocol = WhaleTracker(
            rpc=self.enhanced_rpc, db=self.db, smart_money_analyzer=self.smart_money_analyzer, 
            config=self.config.model_dump(), logger_setup=self.logger_setup
        )
        self.logger.info("WhaleTracker initialized.")

        self.trend_analyzer: TrendAnalysisServiceProtocol = TrendAnalysisService(dexscreener_api=self.dex_screener, config=self.config.model_dump(), logger_setup=self.logger_setup)
        self.logger.info("TrendAnalysisService initialized.")

        self.filtering_service: FilteringServiceProtocol = FilteringService(
            config=self.config.model_dump(), trend_analyzer=self.trend_analyzer,
            jupiter_api=self.jupiter_api, logger_setup=self.logger_setup
        )
        self.logger.info("FilteringService initialized.")

        self.token_enrichment_service: TokenEnrichmentServiceProtocol = TokenEnrichmentService(
            config=self.config.model_dump(), dex_screener_api=self.dex_screener,
            solscan_api=self.solscan_api, jupiter_api=self.jupiter_api, helius_api=self.helius_api,
            enhanced_rpc=self.enhanced_rpc, trend_analyzer=self.trend_analyzer,
            whale_tracker=self.whale_tracker, gem_scorer=self.gem_scorer, logger_setup=self.logger_setup
        )
        self.logger.info("TokenEnrichmentService initialized.")

        if self.config.enhanced_scoring.enabled:
            if self.helius_api and self.jupiter_api: 
                try:
                    self.enhanced_scoring: Optional[EnhancedScoringProtocol] = EnhancedScoring(
                        config_path=self.config_file_name, 
                        helius_api=self.helius_api,
                        jupiter_api=self.jupiter_api,
                        rpc=self.enhanced_rpc, # Assuming EnhancedScoring takes base RPC type
                        rug_check_api=self.rug_check_api,
                        solscan_api=self.solscan_api,
                        logger_setup=self.logger_setup # Pass logger_setup
                    )
                    self.logger.info("EnhancedScoring system initialized.")
        except Exception as e:
                    self.logger.error(f"Failed to initialize EnhancedScoring: {e}", exc_info=True)
                    self.enhanced_scoring = None
            else:
                self.enhanced_scoring = None
                missing_deps = [dep for dep, present in [("HeliusAPI", self.helius_api), ("JupiterAPI", self.jupiter_api)] if not present]
                self.logger.warning(f"EnhancedScoring system is enabled but not initialized due to missing dependencies: {missing_deps}.")
        else:
            self.enhanced_scoring = None
            self.logger.info("EnhancedScoring system is disabled in config.")

        self.metrics = Metrics()
        self.running = True
        self._config_observer: Optional[Observer] = None # For config watcher cleanup
        self._setup_signal_handlers()
        if self.config.features.get('enable_config_hot_reload', False): # Example: make hot-reload configurable
             self._setup_config_watcher()
        self.logger.info("VirtuosoGemFinder initialized successfully with Pydantic config.")
    
    def _load_raw_config_dict(self) -> Dict:
        """Loads config from YAML and merges with Pydantic model defaults (as dict)."""
        config_path = Path(self.config_file_name)
        
        # Get defaults from the Pydantic model structure
        default_config_dict = AppConfig().model_dump(mode='python') # Get defaults as dict
        
        loaded_config_yaml = {}
        if config_path.exists():
            try:
                with open(config_path, 'r') as f:
                    loaded_config_yaml = yaml.safe_load(f) or {}
                self.logger.info(f"Successfully loaded raw configuration from {self.config_file_name}")
            except yaml.YAMLError as e_yaml:
                self.logger.error(f"Error parsing YAML config {self.config_file_name}: {e_yaml}")
            except Exception as e_load:
                self.logger.error(f"Error loading config file {self.config_file_name}: {e_load}")
        else:
            self.logger.warning(f"Config file {self.config_file_name} not found. Will use defaults.")

        # Deep merge: loaded_config_yaml overrides defaults from Pydantic model
        # A more robust deep merge might be needed for deeply nested dicts if {**a, **b} isn't sufficient.
        # Python's dict update or {**a, **b} for top-level keys, and then recursively for nested dicts.
        
        def deep_merge_dicts(base, update):
            merged = base.copy()
            for key, value in update.items():
                if isinstance(value, dict) and isinstance(merged.get(key), dict):
                    merged[key] = deep_merge_dicts(merged[key], value)
                else:
                    merged[key] = value
            return merged

        final_raw_config = deep_merge_dicts(default_config_dict, loaded_config_yaml)
        return final_raw_config

    def _handle_gem_discovery(self, metrics: TokenMetrics, score_data: Dict, pair_data: Optional[Dict] = None):
        """Enhanced gem discovery handler with detailed scoring and enhanced analysis."""
        enhanced_data_results = {} 
        base_score = score_data['total'] 
        final_score = base_score
        final_score_breakdown = {
            "base_metrics": score_data.get('breakdown', {}),
            "enhanced_adjustments": {},
            "risk_factors": metrics.risk_factors or [] 
        }
        
        if self.enhanced_scoring:
            if self.helius_api: 
                try:
                    base_token_data_for_enhance = {
                            "name": metrics.name,
                            "symbol": metrics.symbol,
                            "mcap": metrics.mcap,
                            "price": metrics.price,
                            "volume_24h": metrics.volume_24h,
                            "holders": metrics.holders,
                            "creation_time": metrics.creation_time,
                            "liquidity": metrics.liquidity
                        }
                    # Calls to loop.run_until_complete will be refactored to await in async phase
                    enhanced_data_results = self.loop.run_until_complete(
                        self.enhanced_scoring.enhance_token_analysis(
                            metrics.address, 
                            base_token_data_for_enhance,
                            base_score 
                        )
                    )
                    
                    final_score, score_components = self.enhanced_scoring.calculate_enhanced_gem_score(
                        base_score, 
                        enhanced_data_results
                    )
                    
                    final_score_breakdown["enhanced_adjustments"] = {
                        key: value for key, value in score_components.items() 
                        if key not in ["base_score", "final_score"]
                    }
                    if enhanced_data_results.get("behavioral_analysis", {}).get("warning_flags"):
                        final_score_breakdown["behavioral_warnings"] = enhanced_data_results["behavioral_analysis"]["warning_flags"]
                    if enhanced_data_results.get("onchain_momentum_analysis", {}).get("error_messages"):
                        final_score_breakdown["momentum_errors"] = enhanced_data_results["onchain_momentum_analysis"]["error_messages"]
                
                self.logger.info(
                    f"Enhanced scoring applied to {metrics.symbol}: "
                        f"Base: {base_score:.1f}, Enhanced: {final_score:.1f} "
                        f"(Adj Pct: {score_components.get('total_adjustment_pct', 0):.1f}%)"
                )
            except Exception as e:
                    self.logger.error(f"Error applying enhanced scoring for {metrics.symbol}: {e}", exc_info=True)
            else:
                self.logger.info(f"Helius API not available, skipping enhanced scoring for {metrics.symbol}.")
        
        self.db.save_token(metrics, final_score) 
        
        self.telegram.send_gem_alert(
            metrics=metrics, 
            score=final_score, 
            score_breakdown=final_score_breakdown, 
            enhanced_data=enhanced_data_results,
            pair_address=pair_data.get('pairAddress') if pair_data else metrics.address
        )
        
        self.logger.info(
            f"New gem found: {metrics.symbol} with score {final_score}\n"
            f"Score breakdown: {json.dumps(final_score_breakdown, indent=2)}"
        )

    def _track_api_call(self, start_time: float, success: bool):
        self.metrics.api_calls += 1
        if success:
            self.metrics.successful_calls += 1
        else:
            self.metrics.failed_calls += 1
        self.metrics.response_times.append(time.time() - start_time)
    
    def get_metrics_report(self) -> str:
        avg_response_time = sum(self.metrics.response_times) / len(self.metrics.response_times) if self.metrics.response_times else 0
        return (
            f"API Calls: {self.metrics.api_calls}\n"
            f"Success Rate: {(self.metrics.successful_calls / self.metrics.api_calls * 100):.2f}%\n"
            f"Avg Response Time: {avg_response_time:.2f}s\n"
            f"Gems Found: {self.metrics.gems_found}"
        )

    def _log_performance_metrics(self, operation: str, start_time: float):
        duration = time.time() - start_time
        self.logger.debug(
            f"Performance metrics - Operation: {operation}, "
            f"Duration: {duration:.3f}s, "
            f"API Calls: {self.metrics.api_calls}, "
            f"Memory Usage: {self._get_memory_usage():.1f}MB"
        )

    def _get_memory_usage(self) -> float:
        process = psutil.Process()
        return process.memory_info().rss / 1024 / 1024

    async def scan_new_pairs(self):
        self.logger.info("Starting Virtuoso Gem Finder scan (async)...")
        last_check = {}
        last_metrics_log = time.time()
        metrics_interval = self.config.logging.metrics_log_interval_seconds
        
        while self.running:
            try:
                scan_start_time = time.time()
                pairs = await asyncio.to_thread(self.dex_screener.get_solana_pairs)
                self.logger.debug(f"Fetched {len(pairs)} pairs from DexScreener.")
                
                current_time = time.time()
                processed_pairs_count = 0
                potential_gems_count = 0
                
                tasks = []
                for pair_raw_data in pairs:
                    pair_address = pair_raw_data.get('pairAddress')
                    if pair_address in last_check and (current_time - last_check[pair_address] < self.config.pair_recheck_interval_seconds):
                            continue
                    
                    processed_pairs_count += 1
                    tasks.append(self._process_single_pair(pair_raw_data))
                    last_check[pair_address] = current_time
                
                analysis_results = await asyncio.gather(*tasks, return_exceptions=True)
                for result in analysis_results:
                    if isinstance(result, TokenMetrics):
                        potential_gems_count += 1
                    elif isinstance(result, Exception):
                        self.logger.error(f"Error processing a pair: {result}", exc_info=result)

                if time.time() - last_metrics_log >= metrics_interval:
                    self.logger.info(f"Async Scan Iteration: Processed {processed_pairs_count}, Potential (analyzed) {potential_gems_count}, Duration {time.time() - scan_start_time:.2f}s")
                    last_metrics_log = time.time()
                
                cleanup_threshold = current_time - self.config.pair_check_cache_expiry_seconds
                last_check = {addr: ts for addr, ts in last_check.items() if ts > cleanup_threshold}
                
                await asyncio.sleep(self.config.scan_interval)
                
            except Exception as e:
                self.logger.error(f"Error in async scan_new_pairs loop: {e}", exc_info=True)
                await asyncio.sleep(self.config.scan_interval_error_fallback)

    async def _process_single_pair(self, pair_data: Dict) -> Optional[TokenMetrics]:
        """Helper async method to process a single pair."""
        pair_address = pair_data.get('pairAddress')
        token_symbol = pair_data.get('baseToken', {}).get('symbol', 'N/A')
        try:
            if await self.filtering_service.is_potential_gem(pair_data):
                self.logger.debug(f"Pair {pair_address} ({token_symbol}) is a potential gem by initial filter.")
                token_metrics = await self.token_enrichment_service.analyze_token_comprehensively(pair_data)
                
                if token_metrics:
                    historical_data = await asyncio.to_thread(self.dex_screener.get_token_history, token_metrics.address)
                    
                    score_data = self.gem_scorer.calculate_score(token_metrics, historical_data)
                    
                    if score_data.get('total', 0) >= self.config.min_gem_score:
                        self.logger.info(f"Gem candidate {token_metrics.symbol} ({token_address}) scored {score_data['total']:.1f}. Triggering discovery process.")
                        await self._handle_gem_discovery_async(token_metrics, score_data, pair_data=pair_data)
                        return token_metrics
                    else:
                        self.logger.debug(f"Token {token_metrics.symbol} ({token_address}) score {score_data.get('total',0):.1f} below threshold.")
                else:
                    self.logger.debug(f"No detailed metrics from enrichment for {pair_address} ({token_symbol}).")
            # else: self.logger.debug(f"Pair {pair_address} ({token_symbol}) did not pass initial filter.") # Optional: too verbose?
        except Exception as e:
            self.logger.error(f"Error processing single pair {pair_address} ({token_symbol}): {e}", exc_info=True)
            return None
        return None

    async def _handle_gem_discovery_async(self, metrics: TokenMetrics, score_data: Dict, pair_data: Optional[Dict] = None):
        """Async version of gem discovery handler."""
        enhanced_data_results = {}
        base_score = score_data['total']
        final_score = base_score
        final_score_breakdown = {
            "base_metrics": score_data.get('breakdown', {}),
            "enhanced_adjustments": {},
            "risk_factors": metrics.risk_factors or []
        }

        if self.enhanced_scoring:
        if self.helius_api:
            try:
                    base_token_data_for_enhance = {
                        "name": metrics.name, "symbol": metrics.symbol, "mcap": metrics.mcap,
                        "price": metrics.price, "volume_24h": metrics.volume_24h, "holders": metrics.holders,
                        "creation_time": metrics.creation_time, "liquidity": metrics.liquidity
                    }
                    enhanced_data_results = await self.enhanced_scoring.enhance_token_analysis(
                        metrics.address, base_token_data_for_enhance, base_score
                    )
                    final_score, score_components = self.enhanced_scoring.calculate_enhanced_gem_score(
                        base_score, enhanced_data_results
                    )
                    final_score_breakdown["enhanced_adjustments"] = {
                        key: value for key, value in score_components.items() 
                        if key not in ["base_score", "final_score"]
                    }
                    if enhanced_data_results.get("behavioral_analysis", {}).get("warning_flags"):
                        final_score_breakdown["behavioral_warnings"] = enhanced_data_results["behavioral_analysis"]["warning_flags"]
                    if enhanced_data_results.get("onchain_momentum_analysis", {}).get("error_messages"):
                        final_score_breakdown["momentum_errors"] = enhanced_data_results["onchain_momentum_analysis"]["error_messages"]

                    self.logger.info(f"Enhanced scoring for {metrics.symbol}: Base {base_score:.1f}, Final {final_score:.1f} (Adj Pct: {score_components.get('total_adjustment_pct', 0):.1f}%)")
            except Exception as e:
                    self.logger.error(f"Error in async enhanced scoring for {metrics.symbol}: {e}", exc_info=True)
            else:
                self.logger.info(f"Helius API not available, skipping enhanced scoring for {metrics.symbol}.")
        
        await asyncio.to_thread(self.db.save_token, metrics, final_score)
        
        await asyncio.to_thread(
            self.telegram.send_gem_alert,
            metrics=metrics, score=final_score, score_breakdown=final_score_breakdown,
            enhanced_data=enhanced_data_results, pair_address=pair_data.get('pairAddress') if pair_data else metrics.address
        )
        self.logger.info(f"New gem handled: {metrics.symbol}, Score {final_score:.1f}. Breakdown: {json.dumps(final_score_breakdown, indent=2)}")

    async def scan_new_pairs_enhanced(self):
        self.logger.info("Starting Virtuoso Gem Finder scan (enhanced, async)...")
        await self.scan_new_pairs()

    async def run_background_tasks_async(self):
        if not self.enhanced_scoring or not self.helius_api:
            self.logger.warning("Async background tasks skipped: Enhanced scoring or Helius API not available")
            return
        try:
            self.logger.info("Running async smart money wallet clustering...")
            cluster_count = await self.enhanced_scoring.run_wallet_clustering()
            self.logger.info(f"Async wallet clustering complete: {cluster_count} clusters identified")
            except Exception as e:
            self.logger.error(f"Error running async background tasks: {e}", exc_info=True)
            
    async def scan_new_pairs_with_background_tasks(self):
        self.logger.info("Starting Virtuoso Gem Finder with enhanced scoring & background tasks (async)...")
        last_check = {}
        last_metrics_log = time.time()
        last_background_run_time = time.time()
        metrics_interval = self.config.logging.metrics_log_interval_seconds
        background_task_interval = self.config.background_task_interval_seconds
        
        while self.running:
            try:
                current_time_loop_start = time.time()
                if current_time_loop_start - last_background_run_time >= background_task_interval:
                    await self.run_background_tasks_async()
                    last_background_run_time = current_time_loop_start

                scan_start_time = time.time()
                pairs = await asyncio.to_thread(self.dex_screener.get_solana_pairs)
                self.logger.debug(f"Fetched {len(pairs)} pairs from DexScreener.")
                
                current_time_processing = time.time()
                processed_pairs_count = 0
                
                tasks = []
                for pair_raw_data in pairs:
                    pair_address = pair_raw_data.get('pairAddress')
                    if pair_address in last_check and (current_time_processing - last_check[pair_address] < self.config.pair_recheck_interval_seconds):
                            continue
                    processed_pairs_count += 1
                    tasks.append(self._process_single_pair(pair_raw_data))
                    last_check[pair_address] = current_time_processing
                
                analysis_results = await asyncio.gather(*tasks, return_exceptions=True)
                successful_analyses = sum(1 for r in analysis_results if isinstance(r, TokenMetrics))

                if time.time() - last_metrics_log >= metrics_interval:
                    self.logger.info(f"Async Scan+BG Iteration: Processed {processed_pairs_count}, Successful Analyses {successful_analyses}, Duration {time.time() - scan_start_time:.2f}s")
                    last_metrics_log = time.time()
                
                cleanup_threshold = current_time_processing - self.config.pair_check_cache_expiry_seconds
                last_check = {addr: ts for addr, ts in last_check.items() if ts > cleanup_threshold}
                
                await asyncio.sleep(self.config.scan_interval)
                
            except Exception as e:
                self.logger.error(f"Error in async scan_new_pairs_with_background_tasks loop: {e}", exc_info=True)
                await asyncio.sleep(self.config.scan_interval_error_fallback)

    async def _cleanup_async(self):
        self.logger.info("Cleaning up VirtuosoGemFinder resources (async)...")
        if hasattr(self, '_config_observer') and self._config_observer.is_alive():
            self._config_observer.stop()
            await asyncio.to_thread(self._config_observer.join) 
            self.logger.info("Config watcher stopped.")

        if self.jupiter_api and hasattr(self.jupiter_api, 'close') and asyncio.iscoroutinefunction(self.jupiter_api.close):
            try:
                await self.jupiter_api.close()
                self.logger.info("JupiterAPI connection closed.")
        except Exception as e:
                self.logger.error(f"Error closing JupiterAPI: {e}", exc_info=True)
        
        if self.helius_api and hasattr(self.helius_api, 'close_session') and asyncio.iscoroutinefunction(self.helius_api.close_session):
             try:
                await self.helius_api.close_session() 
                self.logger.info("HeliusAPI session closed.")
        except Exception as e:
                self.logger.error(f"Error closing HeliusAPI session: {e}", exc_info=True)

        if hasattr(self, 'db') and hasattr(self.db, 'pool') and self.db.pool is not None:
            try:
                if hasattr(self.db.pool, 'close') and not asyncio.iscoroutinefunction(self.db.pool.close):
                    await asyncio.to_thread(self.db.pool.close)
                    self.logger.info("Database connection pool closed.")
                elif hasattr(self.db.pool, 'close') and asyncio.iscoroutinefunction(self.db.pool.close):
                    await self.db.pool.close()
                    self.logger.info("Database connection pool closed (async).")
        except Exception as e:
                self.logger.error(f"Error closing database pool: {e}", exc_info=True)
                
        self.logger.info("VirtuosoGemFinder async cleanup complete.")

    def _setup_signal_handlers(self):
        def signal_handler(signum, frame):
            self.logger.info("Received shutdown signal, initiating async cleanup...")
            self.running = False
            if self.loop and self.loop.is_running():
                asyncio.run_coroutine_threadsafe(self._cleanup_async(), self.loop)
            else:
                self._cleanup()
            self.logger.info("Exiting signal handler. Main loop should terminate.")
            
        signal.signal(signal.SIGINT, signal_handler)
        signal.signal(signal.SIGTERM, signal_handler)

    def _cleanup(self):
        self.logger.info("Performing synchronous parts of cleanup...")
        if hasattr(self, '_config_observer') and self._config_observer.is_alive():
            self._config_observer.stop()
            self._config_observer.join(timeout=5)
            self.logger.info("Config watcher stopped (sync fallback).")
        if hasattr(self, 'db') and hasattr(self.db, 'pool') and self.db.pool is not None:
            if hasattr(self.db.pool, 'close') and not asyncio.iscoroutinefunction(self.db.pool.close):
                try:
                    self.db.pool.close()
                    self.logger.info("Database connection pool closed (sync fallback).")
            except Exception as e:
                    self.logger.error(f"Error closing database pool (sync fallback): {e}", exc_info=True)
        self.logger.info("Synchronous cleanup actions complete.")

# Global utility functions and FILTERS_DATA were moved to filtering_service.py
# (e.g., _check_condition, check_token_against_filter_set, apply_dexscreener_filters)

def main():
    # Setup basic logging for issues before VirtuosoGemFinder logger is ready
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    logger_main = LoggerSetup('main').logger # General logger for main execution

    credentials_path = Path(__file__).parent / 'credentials.json' 
    bot_token = None
    chat_id = None
    if credentials_path.exists():
        try:
            with open(credentials_path) as f:
                credentials = json.load(f)
            bot_token = credentials.get('telegram_bot_token')
            chat_id = credentials.get('telegram_chat_id')
        except Exception as e:
            logger_main.error(f"Error loading credentials from {credentials_path}: {e}", exc_info=True)
        else:
        logger_main.warning(f"Credentials file {credentials_path} not found.")

    if not bot_token or not chat_id:
        logger_main.error("Telegram BOT_TOKEN or CHAT_ID not found. Cannot start TelegramAlerter or the bot effectively.")
        # Decide if application should exit or run without Telegram features
        # return # Optionally exit if Telegram is critical

    gem_finder = VirtuosoGemFinder(telegram_bot_token=bot_token, telegram_chat_id=chat_id)
    
    logger_main.info("Starting Virtuoso Gem Finder application (async)...")

    main_scan_task = None
    try:
        if gem_finder.token_enrichment_service and gem_finder.filtering_service:
            logger_main.info("Configuring to run scan_new_pairs_with_background_tasks (async).")
            # asyncio.run() should be the main entry point for the async application
            # The VirtuosoGemFinder instance and its loop are already created.
            # We need to run its main async task.
            main_scan_task = gem_finder.scan_new_pairs_with_background_tasks() # This is now an awaitable coroutine
            asyncio.run(main_scan_task) # Main entry point for the async app
    else:
             logger_main.error("Core services (TokenEnrichment or Filtering) not initialized. Cannot start scan.")

    except KeyboardInterrupt:
        logger_main.info("Keyboard interrupt received by main, shutting down...")
        # The signal handler in VirtuosoGemFinder should manage cleanup.
    except Exception as e_main:
        logger_main.error(f"Unhandled exception in main: {e_main}", exc_info=True)
    finally:
        logger_main.info("Main function is exiting. Ensuring cleanup is triggered if loop was running.")
        # If the loop was started by asyncio.run(), it handles its own shutdown.
        # The signal handler in VirtuosoGemFinder should have set self.running = False
        # and initiated cleanup.
        # If asyncio.run() completed or was interrupted, ensure gem_finder.running is False.
        if gem_finder:
            gem_finder.running = False # Ensure all loops stop
            # If loop is still running somehow (e.g. if asyncio.run was not reached or exited prematurely)
            # and _cleanup_async needs to be explicitly called:
            if gem_finder.loop and gem_finder.loop.is_running() and main_scan_task and not main_scan_task.done():
                logger_main.info("Main scan task was not done, attempting to cancel and run cleanup...")
                main_scan_task.cancel() # Cancel the main task if it's still around
                # Run cleanup if not already handled by signal
                try:
                    gem_finder.loop.run_until_complete(gem_finder._cleanup_async())
                except RuntimeError: # Loop might be closed already
                    pass 
            elif not (gem_finder.loop and gem_finder.loop.is_running()):
                 # If loop is not running, a more direct synchronous cleanup if parts of it are safe
                 gem_finder._cleanup() # Fallback to original sync parts of cleanup
        logger_main.info("Virtuoso Gem Finder main function has finished.")

if __name__ == "__main__":
    main()