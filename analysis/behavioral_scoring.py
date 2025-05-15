"""
Behavioral Scoring module for Virtuoso Gem Finder.

This module implements a scoring mechanism based on developer responsiveness,
transparency, and community engagement metrics along with early signal detection
and weighted scoring.
"""

import asyncio
from typing import Dict, List, Set, Tuple, Optional, Any
import logging
import time
import json
from pathlib import Path
from dataclasses import dataclass, field, asdict
import numpy as np
from datetime import datetime, timedelta

@dataclass
class DeveloperProfile:
    """Data class for developer/team behavioral metrics"""
    address: str  # Creator/developer wallet address
    project_name: str = ""  # Associated project name
    response_score: float = 0.0  # Developer responsiveness score (0-1)
    transparency_score: float = 0.0  # Project transparency score (0-1)
    community_score: float = 0.0  # Community engagement score (0-1)
    behavioral_score: float = 0.0  # Composite behavioral score (0-1)
    last_updated: int = 0  # Timestamp of last update
    response_history: List[Dict] = field(default_factory=list)  # History of response metrics
    transparency_events: List[Dict] = field(default_factory=list)  # Transparency events
    community_events: List[Dict] = field(default_factory=list)  # Community engagement events
    risk_factors: List[str] = field(default_factory=list)  # Identified risk factors
    previous_projects: List[Dict] = field(default_factory=list)  # Previous projects by same dev

@dataclass
class TokenBehavioralMetrics:
    """Data class for token behavioral metrics"""
    address: str  # Token address
    symbol: str = ""
    name: str = ""
    developer_score: float = 0.0  # Developer behavioral score
    community_growth_score: float = 0.0  # Community growth patterns score
    transaction_pattern_score: float = 0.0  # Transaction pattern health score
    early_signal_score: float = 0.0  # Early growth signals score
    composite_score: float = 0.0  # Weighted composite score
    creation_time: int = 0  # Token creation timestamp
    last_updated: int = 0  # Metrics last updated timestamp
    early_signals: Dict[str, float] = field(default_factory=dict)  # Early signals with weights
    trailing_signals: Dict[str, float] = field(default_factory=dict)  # Trailing signals with weights
    warning_flags: List[str] = field(default_factory=list)  # Warning flags for suspicious behavior


class BehavioralScorer:
    """
    Implements behavioral scoring based on developer, community, and transaction
    patterns with weighted signals for early detection.
    """
    
    def __init__(self, helius_api, rpc, wallet_analyzer, cache_dir: str = "./cache"):
        """
        Initialize the behavioral scorer.
        
        Args:
            helius_api: Instance of HeliusAPI for transaction and wallet analysis
            rpc: Instance of EnhancedSolanaRPC for blockchain data
            wallet_analyzer: Instance of WalletAnalyzer for detailed wallet insights
            cache_dir: Directory to store behavioral scoring cache
        """
        self.helius_api = helius_api
        self.rpc = rpc
        self.wallet_analyzer = wallet_analyzer
        self.logger = logging.getLogger('BehavioralScorer')
        
        # Cache directory setup
        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(exist_ok=True)
        self.dev_profiles_file = self.cache_dir / "developer_profiles.json"
        self.token_metrics_file = self.cache_dir / "token_behavioral_metrics.json"
        
        # Storage for behavioral data
        self.developer_profiles: Dict[str, DeveloperProfile] = {}
        self.token_metrics: Dict[str, TokenBehavioralMetrics] = {}
        
        # Signal weights (early signals get higher weights)
        self.early_signal_weights = {
            "new_wallet_engagement": 1.5,  # New wallets engaging with token
            "transaction_growth_rate": 1.8,  # Growth rate in transactions
            "organic_volume_growth": 1.6,  # Organic growth in volume
            "smart_money_interest": 2.0,  # Smart money wallets showing interest
            "developer_activity": 1.7,  # Recent developer activity
            "community_engagement": 1.4  # Community engagement metrics
        }
        
        self.trailing_signal_weights = {
            "total_volume": 0.7,  # Total trading volume
            "market_cap": 0.8,  # Current market cap
            "holder_count": 0.9,  # Total holder count
            "price_action": 0.6,  # Recent price movement
            "social_mentions": 0.5  # Social media mentions
        }
        
        # Load cached data
        self._load_cache()
        
    def _load_cache(self):
        """Load cached behavioral data if available"""
        # Load developer profiles
        if self.dev_profiles_file.exists():
            try:
                with open(self.dev_profiles_file, 'r') as f:
                    dev_data = json.load(f)
                    
                self.developer_profiles = {
                    addr: DeveloperProfile(**data) 
                    for addr, data in dev_data.items()
                }
                self.logger.info(f"Loaded {len(self.developer_profiles)} developer profiles from cache")
            except Exception as e:
                self.logger.error(f"Error loading developer profiles cache: {e}")
                
        # Load token metrics
        if self.token_metrics_file.exists():
            try:
                with open(self.token_metrics_file, 'r') as f:
                    token_data = json.load(f)
                    
                self.token_metrics = {
                    addr: TokenBehavioralMetrics(**data) 
                    for addr, data in token_data.items()
                }
                self.logger.info(f"Loaded {len(self.token_metrics)} token behavioral metrics from cache")
            except Exception as e:
                self.logger.error(f"Error loading token metrics cache: {e}")
                
    def _save_cache(self):
        """Save behavioral data to cache"""
        # Save developer profiles
        try:
            dev_data = {
                addr: asdict(profile)
                for addr, profile in self.developer_profiles.items()
            }
            
            with open(self.dev_profiles_file, 'w') as f:
                json.dump(dev_data, f)
                
            self.logger.info(f"Saved {len(self.developer_profiles)} developer profiles to cache")
        except Exception as e:
            self.logger.error(f"Error saving developer profiles cache: {e}")
            
        # Save token metrics
        try:
            token_data = {
                addr: asdict(metrics)
                for addr, metrics in self.token_metrics.items()
            }
            
            with open(self.token_metrics_file, 'w') as f:
                json.dump(token_data, f)
                
            self.logger.info(f"Saved {len(self.token_metrics)} token behavioral metrics to cache")
        except Exception as e:
            self.logger.error(f"Error saving token metrics cache: {e}")
            
    async def analyze_developer_behavior(self, 
                                 dev_address: str, 
                                 token_address: str = None,
                                 project_name: str = None) -> DeveloperProfile:
        """
        Analyze developer/creator wallet for behavioral patterns
        
        Args:
            dev_address: Developer wallet address
            token_address: Associated token address (optional)
            project_name: Project name (optional)
            
        Returns:
            DeveloperProfile object with analysis results
        """
        current_time = int(time.time())
        
        # Check for existing profile less than 24h old
        if dev_address in self.developer_profiles:
            profile = self.developer_profiles[dev_address]
            if current_time - profile.last_updated < 86400:  # 24 hours
                return profile
                
        # Get transaction history from Helius
        tx_history = await self.helius_api.get_enhanced_transactions(dev_address, 100)
        
        # Analyze token creator history if token address provided
        if token_address:
            # Find creation transaction and other associated projects
            creator_info = await self._analyze_creator_history(dev_address, token_address)
        else:
            creator_info = {
                "previous_projects": [],
                "has_rugs": False,
                "avg_project_lifespan": 0
            }
            
        # Calculate response metrics
        response_data = self._calculate_response_metrics(tx_history)
        
        # Calculate transparency metrics
        transparency_data = self._calculate_transparency_metrics(tx_history, dev_address)
        
        # Calculate community engagement metrics
        community_data = self._calculate_community_metrics(tx_history, dev_address)
        
        # Create or update developer profile
        profile = DeveloperProfile(
            address=dev_address,
            project_name=project_name or "",
            response_score=response_data.get("score", 0.0),
            transparency_score=transparency_data.get("score", 0.0),
            community_score=community_data.get("score", 0.0),
            behavioral_score=self._calculate_composite_score(
                response_data.get("score", 0.0),
                transparency_data.get("score", 0.0),
                community_data.get("score", 0.0),
                creator_info.get("has_rugs", False)
            ),
            last_updated=current_time,
            response_history=response_data.get("history", []),
            transparency_events=transparency_data.get("events", []),
            community_events=community_data.get("events", []),
            risk_factors=self._identify_risk_factors(
                response_data, 
                transparency_data, 
                community_data,
                creator_info
            ),
            previous_projects=creator_info.get("previous_projects", [])
        )
        
        # Update cache
        self.developer_profiles[dev_address] = profile
        self._save_cache()
        
        return profile
        
    async def _analyze_creator_history(self, 
                                creator_address: str, 
                                token_address: str) -> Dict[str, Any]:
        """
        Analyze token creator's history to find past projects
        
        Args:
            creator_address: Creator wallet address
            token_address: Current token address
            
        Returns:
            Dictionary with creator history metrics
        """
        # This would be a complex implementation involving:
        # 1. Finding other tokens created by this wallet
        # 2. Analyzing their performance and outcomes
        # 3. Identifying patterns of behavior across projects
        
        # Simplified placeholder implementation
        return {
            "previous_projects": [],
            "has_rugs": False,
            "avg_project_lifespan": 90  # 90 days placeholder
        }
        
    def _calculate_response_metrics(self, tx_history: List[Dict]) -> Dict[str, Any]:
        """
        Calculate developer responsiveness metrics
        
        Args:
            tx_history: Transaction history from Helius
            
        Returns:
            Dictionary with response metrics and score
        """
        # This would analyze:
        # - How quickly developer responds to issues
        # - Frequency of contract interactions
        # - Patterns of activity during critical periods
        
        # Simplified placeholder implementation
        response_events = []
        
        # Simple scoring based on regular activity
        activity_days = set()
        for tx in tx_history:
            timestamp = tx.get("timestamp", 0) / 1000  # Convert to seconds
            date = datetime.fromtimestamp(timestamp).strftime('%Y-%m-%d')
            activity_days.add(date)
            
        # More active = higher score
        score = min(len(activity_days) / 30.0, 1.0)
        
        return {
            "score": score,
            "history": response_events,
            "active_days": len(activity_days)
        }
        
    def _calculate_transparency_metrics(self, 
                                  tx_history: List[Dict], 
                                  dev_address: str) -> Dict[str, Any]:
        """
        Calculate transparency metrics based on developer behavior
        
        Args:
            tx_history: Transaction history from Helius
            dev_address: Developer wallet address
            
        Returns:
            Dictionary with transparency metrics and score
        """
        # This would analyze:
        # - Consistent vs erratic behavioral patterns
        # - Openness of operations (public transactions)
        # - Code verification and documentation
        
        # Simplified placeholder implementation
        transparency_events = []
        
        # Simple placeholder score
        score = 0.7  # Default moderate score
        
        return {
            "score": score,
            "events": transparency_events
        }
        
    def _calculate_community_metrics(self, 
                               tx_history: List[Dict], 
                               dev_address: str) -> Dict[str, Any]:
        """
        Calculate community engagement metrics
        
        Args:
            tx_history: Transaction history from Helius
            dev_address: Developer wallet address
            
        Returns:
            Dictionary with community metrics and score
        """
        # This would analyze:
        # - Interactions with community wallets
        # - Distribution of tokens to community
        # - Engagement patterns outside whale-only circles
        
        # Simplified placeholder implementation
        community_events = []
        
        # Placeholder score
        score = 0.6
        
        return {
            "score": score,
            "events": community_events
        }
        
    def _calculate_composite_score(self, 
                            response_score: float, 
                            transparency_score: float,
                            community_score: float,
                            has_rugs: bool) -> float:
        """
        Calculate composite behavioral score
        
        Args:
            response_score: Responsiveness score
            transparency_score: Transparency score
            community_score: Community engagement score
            has_rugs: Whether developer has rug pulls in history
            
        Returns:
            Composite behavioral score (0-1)
        """
        # Instant fail for rug pulls
        if has_rugs:
            return 0.0
            
        # Weighted composite score
        score = (
            response_score * 0.4 +
            transparency_score * 0.3 +
            community_score * 0.3
        )
        
        return min(score, 1.0)  # Cap at 1.0
        
    def _identify_risk_factors(self, 
                        response_data: Dict, 
                        transparency_data: Dict,
                        community_data: Dict,
                        creator_info: Dict) -> List[str]:
        """
        Identify risk factors based on behavioral metrics
        
        Args:
            response_data: Response metrics
            transparency_data: Transparency metrics
            community_data: Community metrics
            creator_info: Creator history information
            
        Returns:
            List of risk factor strings
        """
        risk_factors = []
        
        # Check for low scores
        if response_data.get("score", 0) < 0.4:
            risk_factors.append("low_developer_responsiveness")
            
        if transparency_data.get("score", 0) < 0.4:
            risk_factors.append("low_transparency")
            
        if community_data.get("score", 0) < 0.4:
            risk_factors.append("poor_community_engagement")
            
        # Check creator history
        if creator_info.get("has_rugs", False):
            risk_factors.append("previous_rug_pulls")
            
        if creator_info.get("avg_project_lifespan", 0) < 30:
            risk_factors.append("short_lived_previous_projects")
            
        return risk_factors
        
    async def calculate_token_behavioral_score(self, 
                                      token_address: str,
                                      token_data: Dict,
                                      whale_analysis: Dict = None) -> TokenBehavioralMetrics:
        """
        Calculate comprehensive behavioral score for a token
        
        Args:
            token_address: Token mint address
            token_data: Token market data
            whale_analysis: Optional whale analysis data
            
        Returns:
            TokenBehavioralMetrics object with scores
        """
        current_time = int(time.time())
        
        # Check for cached recent analysis
        if token_address in self.token_metrics:
            metrics = self.token_metrics[token_address]
            if current_time - metrics.last_updated < 3600:  # 1 hour
                return metrics
                
        # Get creator address
        creator_address = token_data.get("creator_address", "")
        if not creator_address:
            # Try to find creator from enhanced RPC
            token_info = self.rpc.get_account_info(token_address)
            creator_address = token_info.get("owner", "")
            
        # If we have a creator, analyze their behavior
        developer_score = 0.5  # Default moderate score
        if creator_address:
            dev_profile = await self.analyze_developer_behavior(
                creator_address, 
                token_address,
                token_data.get("name", "")
            )
            developer_score = dev_profile.behavioral_score
            
        # Calculate early signal metrics
        early_signals = await self._calculate_early_signals(token_address, token_data)
        
        # Calculate trailing metrics
        trailing_signals = self._calculate_trailing_signals(token_data, whale_analysis)
        
        # Calculate community growth score
        community_score = self._calculate_community_growth_score(token_data, early_signals)
        
        # Calculate transaction pattern score
        tx_pattern_score = self._calculate_transaction_pattern_score(early_signals)
        
        # Calculate early signal weighted score
        early_signal_score = self._calculate_weighted_signal_score(early_signals, self.early_signal_weights)
        
        # Calculate composite score
        composite_score = (
            developer_score * 0.3 +
            community_score * 0.2 +
            tx_pattern_score * 0.2 +
            early_signal_score * 0.3
        )
        
        # Create metrics object
        metrics = TokenBehavioralMetrics(
            address=token_address,
            symbol=token_data.get("symbol", ""),
            name=token_data.get("name", ""),
            developer_score=developer_score,
            community_growth_score=community_score,
            transaction_pattern_score=tx_pattern_score,
            early_signal_score=early_signal_score,
            composite_score=composite_score,
            creation_time=token_data.get("creation_time", current_time),
            last_updated=current_time,
            early_signals=early_signals,
            trailing_signals=trailing_signals,
            warning_flags=self._identify_warning_flags(early_signals, trailing_signals, developer_score)
        )
        
        # Update cache
        self.token_metrics[token_address] = metrics
        self._save_cache()
        
        return metrics
        
    async def _calculate_early_signals(self, 
                               token_address: str, 
                               token_data: Dict) -> Dict[str, float]:
        """
        Calculate early growth signals for a token
        
        Args:
            token_address: Token mint address
            token_data: Token market data
            
        Returns:
            Dictionary of early signal metrics with scores
        """
        # Get recent transactions for the token
        recent_txs = self.rpc.get_recent_token_transactions(token_address, 50)
        
        # Analyze wallet engagement (new wallets vs. existing wallets)
        new_wallet_count = 0
        total_wallet_count = 0
        wallets_seen = set()
        
        for tx in recent_txs:
            # Extract accounts involved
            for account in tx.get("accounts", []):
                if account not in wallets_seen:
                    wallets_seen.add(account)
                    total_wallet_count += 1
                    
                    # Check if this is a new wallet
                    wallet_age = self._get_wallet_age(account)
                    if wallet_age < 7:  # New wallet if < 7 days old
                        new_wallet_count += 1
                        
        # Calculate new wallet engagement score
        new_wallet_engagement = new_wallet_count / max(total_wallet_count, 1)
        
        # Calculate transaction growth rate
        tx_data = token_data.get("tx_counts", {})
        tx_24h = tx_data.get("count_24h", 0)
        tx_prev_24h = tx_data.get("count_prev_24h", 0)
        
        if tx_prev_24h > 0:
            tx_growth_rate = (tx_24h - tx_prev_24h) / tx_prev_24h
        else:
            tx_growth_rate = 0
            
        # Normalize tx growth rate to 0-1 score
        tx_growth_score = min(max(tx_growth_rate, 0), 5) / 5.0
        
        # Volume growth analysis (similar to tx growth)
        volume_data = token_data.get("volume", {})
        vol_24h = volume_data.get("volume_24h", 0)
        vol_prev_24h = volume_data.get("volume_prev_24h", 0)
        
        if vol_prev_24h > 0:
            vol_growth_rate = (vol_24h - vol_prev_24h) / vol_prev_24h
        else:
            vol_growth_rate = 0
            
        # Normalize volume growth to 0-1 score
        vol_growth_score = min(max(vol_growth_rate, 0), 5) / 5.0
        
        # Placeholder for smart money interest (would come from wallet analyzer)
        smart_money_score = 0.5
        
        # Developer activity (placeholder)
        dev_activity_score = 0.6
        
        # Community engagement (placeholder)
        community_engagement_score = 0.5
        
        return {
            "new_wallet_engagement": new_wallet_engagement,
            "transaction_growth_rate": tx_growth_score,
            "organic_volume_growth": vol_growth_score,
            "smart_money_interest": smart_money_score,
            "developer_activity": dev_activity_score,
            "community_engagement": community_engagement_score
        }
        
    def _calculate_trailing_signals(self, 
                             token_data: Dict, 
                             whale_analysis: Dict = None) -> Dict[str, float]:
        """
        Calculate trailing signals for a token
        
        Args:
            token_data: Token market data
            whale_analysis: Optional whale analysis data
            
        Returns:
            Dictionary of trailing signal metrics with scores
        """
        # Total volume normalized score (0-1)
        volume = token_data.get("volume_24h", 0)
        volume_score = min(volume / 1000000, 1.0)  # Normalize to 0-1, cap at $1M
        
        # Market cap normalized score (0-1)
        mcap = token_data.get("mcap", 0)
        mcap_score = min(mcap / 10000000, 1.0)  # Normalize to 0-1, cap at $10M
        
        # Holder count normalized score
        holders = token_data.get("holders", 0)
        holder_score = min(holders / 1000, 1.0)  # Normalize to 0-1, cap at 1000 holders
        
        # Price action score
        price_change = token_data.get("price_change_24h", 0)
        price_score = (price_change + 100) / 200  # Normalize -100% to +100% to 0-1 scale
        
        # Social mentions (placeholder)
        social_score = 0.5
        
        return {
            "total_volume": volume_score,
            "market_cap": mcap_score,
            "holder_count": holder_score,
            "price_action": price_score,
            "social_mentions": social_score
        }
        
    def _calculate_community_growth_score(self, 
                                   token_data: Dict, 
                                   early_signals: Dict) -> float:
        """
        Calculate community growth score based on holder metrics
        
        Args:
            token_data: Token market data
            early_signals: Early signal metrics
            
        Returns:
            Community growth score (0-1)
        """
        # Combine multiple factors:
        # - Holder count growth
        # - New wallet engagement
        # - Community engagement
        
        # Holder growth
        holder_data = token_data.get("holder_counts", {})
        holders_24h = holder_data.get("count_24h", 0)
        holders_prev_24h = holder_data.get("count_prev_24h", 0)
        
        if holders_prev_24h > 0:
            holder_growth = (holders_24h - holders_prev_24h) / holders_prev_24h
        else:
            holder_growth = 0
            
        # Normalize holder growth to 0-1
        holder_growth_score = min(max(holder_growth, 0), 1.0)
        
        # Get other factors from early signals
        new_wallet_score = early_signals.get("new_wallet_engagement", 0)
        community_score = early_signals.get("community_engagement", 0)
        
        # Weighted combination
        return (
            holder_growth_score * 0.4 +
            new_wallet_score * 0.4 +
            community_score * 0.2
        )
        
    def _calculate_transaction_pattern_score(self, early_signals: Dict) -> float:
        """
        Calculate transaction pattern health score
        
        Args:
            early_signals: Early signal metrics
            
        Returns:
            Transaction pattern score (0-1)
        """
        # Combine multiple factors:
        # - Transaction growth rate
        # - Organic volume growth
        # - Smart money interest
        
        tx_growth = early_signals.get("transaction_growth_rate", 0)
        vol_growth = early_signals.get("organic_volume_growth", 0)
        smart_money = early_signals.get("smart_money_interest", 0)
        
        # Weighted combination
        return (
            tx_growth * 0.4 +
            vol_growth * 0.3 +
            smart_money * 0.3
        )
        
    def _calculate_weighted_signal_score(self, 
                                  signals: Dict[str, float], 
                                  weights: Dict[str, float]) -> float:
        """
        Calculate weighted score for signals
        
        Args:
            signals: Signal metrics dictionary
            weights: Weight factors for each signal
            
        Returns:
            Weighted score (0-1)
        """
        total_weight = sum(weights.values())
        weighted_sum = 0.0
        
        for signal, score in signals.items():
            if signal in weights:
                weighted_sum += score * weights[signal]
                
        return weighted_sum / total_weight
        
    def _identify_warning_flags(self, 
                         early_signals: Dict[str, float],
                         trailing_signals: Dict[str, float],
                         developer_score: float) -> List[str]:
        """
        Identify warning flags based on behavioral metrics
        
        Args:
            early_signals: Early signal metrics
            trailing_signals: Trailing signal metrics
            developer_score: Developer behavioral score
            
        Returns:
            List of warning flag strings
        """
        flags = []
        
        # Check for concerning patterns
        if early_signals.get("new_wallet_engagement", 0) > 0.8:
            flags.append("excessive_new_wallets")
            
        if early_signals.get("transaction_growth_rate", 0) > 0.9:
            flags.append("suspicious_tx_growth")
            
        if developer_score < 0.3:
            flags.append("concerning_developer_behavior")
            
        # Add more checks as needed
        
        return flags
        
    def _get_wallet_age(self, address: str) -> int:
        """
        Get wallet age in days
        
        Args:
            address: Wallet address
            
        Returns:
            Age in days (approximation)
        """
        # This would use signature history to determine first transaction
        # Simplified placeholder
        return 30  # Default to 30 days
        
    def get_token_behavioral_score(self, token_address: str) -> float:
        """
        Get cached token behavioral score if available
        
        Args:
            token_address: Token address
            
        Returns:
            Behavioral score (0-1) or 0 if not available
        """
        if token_address in self.token_metrics:
            return self.token_metrics[token_address].composite_score
        return 0.0
        
    def get_developer_score(self, dev_address: str) -> float:
        """
        Get cached developer behavioral score if available
        
        Args:
            dev_address: Developer address
            
        Returns:
            Behavioral score (0-1) or 0 if not available
        """
        if dev_address in self.developer_profiles:
            return self.developer_profiles[dev_address].behavioral_score
        return 0.0 