"""
Wallet Analysis module for Virtuoso Gem Finder.

This module provides detailed wallet profiling and classification, identifying whales,
smart money, and retail investors to provide better context for token analysis.
"""

import asyncio
from typing import Dict, List, Set, Tuple, Optional, Any
import logging
from dataclasses import dataclass, field, asdict
import time
import json
from pathlib import Path
from datetime import datetime, timedelta

@dataclass
class WalletProfile:
    """Data class for profiled wallet information"""
    address: str
    classification: str  # "whale", "smart_money", "retail", "bot", "developer"
    first_seen: int  # Timestamp when wallet was first seen
    last_active: int  # Timestamp of last activity
    total_balance_usd: float = 0.0  # Estimated total holdings in USD
    transaction_count: int = 0  # Total number of transactions
    tokens_held: int = 0  # Number of unique tokens in wallet
    historical_winners: int = 0  # Number of profitable token exits
    historical_losers: int = 0  # Number of unprofitable token exits
    average_hold_time: float = 0.0  # Average holding period in hours
    behavioral_score: float = 0.0  # 0-1 composite score
    token_entries: List[Dict] = field(default_factory=list)  # Recent token entries
    token_exits: List[Dict] = field(default_factory=list)  # Recent token exits
    reputation_tags: List[str] = field(default_factory=list)  # Classification tags
    risk_score: float = 0.0  # 0-1 risk score (higher = riskier)


class WalletAnalyzer:
    """
    Implements detailed wallet profiling and scoring to classify wallets and
    provide behavioral context for token holder analysis.
    """
    
    def __init__(self, helius_api, jupiter_api, rpc, cache_dir: str = "./cache"):
        """
        Initialize the wallet analyzer.
        
        Args:
            helius_api: Instance of HeliusAPI for wallet data
            jupiter_api: Instance of JupiterAPI for price data
            rpc: Instance of EnhancedSolanaRPC
            cache_dir: Directory to store wallet profile cache
        """
        self.helius_api = helius_api
        self.jupiter_api = jupiter_api
        self.rpc = rpc
        self.logger = logging.getLogger('WalletAnalyzer')
        
        # Cache directory setup
        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(exist_ok=True)
        self.wallet_profiles_file = self.cache_dir / "wallet_profiles.json"
        
        # Wallet profiles database
        self.wallet_profiles: Dict[str, WalletProfile] = {}
        self.whale_threshold_usd = 100000  # $100k+ in holdings
        
        # Load cached profiles
        self._load_cache()
        
    def _load_cache(self):
        """Load cached wallet profiles data if available"""
        if self.wallet_profiles_file.exists():
            try:
                with open(self.wallet_profiles_file, 'r') as f:
                    profile_data = json.load(f)
                    
                self.wallet_profiles = {
                    addr: WalletProfile(**data) 
                    for addr, data in profile_data.items()
                }
                self.logger.info(f"Loaded {len(self.wallet_profiles)} wallet profiles from cache")
            except Exception as e:
                self.logger.error(f"Error loading wallet profiles cache: {e}")
                
    def _save_cache(self):
        """Save wallet profiles data to cache"""
        try:
            profile_data = {
                addr: asdict(profile)
                for addr, profile in self.wallet_profiles.items()
            }
            
            with open(self.wallet_profiles_file, 'w') as f:
                json.dump(profile_data, f)
                
            self.logger.info(f"Saved {len(self.wallet_profiles)} wallet profiles to cache")
        except Exception as e:
            self.logger.error(f"Error saving wallet profiles cache: {e}")
    
    async def analyze_wallet(self, address: str) -> Optional[WalletProfile]:
        """
        Perform comprehensive wallet analysis to create or update a profile
        
        Args:
            address: Wallet address to analyze
            
        Returns:
            WalletProfile object or None if insufficient data
        """
        # Check if we have a recent profile
        current_time = int(time.time())
        if address in self.wallet_profiles:
            profile = self.wallet_profiles[address]
            # Use cached profile if less than 24h old
            if current_time - profile.last_active < 86400:
                return profile
        
        # Get wallet data from Helius
        wallet_data = await self.helius_api.analyze_wallet(address)
        if not wallet_data or wallet_data.get("error"):
            self.logger.warning(f"Insufficient data for wallet {address}")
            return None
        
        # Get enhanced transactions
        enhanced_txs = await self.helius_api.get_enhanced_transactions(address, 100)
        
        # Get account holdings
        token_accounts = self.rpc.get_token_accounts(address)
        
        # Calculate estimated USD value
        total_balance_usd = await self._calculate_wallet_value(token_accounts)
        
        # Extract token entry/exit events
        token_entries, token_exits = self._extract_token_events(enhanced_txs)
        
        # Calculate performance metrics
        performance_metrics = self._calculate_performance_metrics(token_entries, token_exits)
        
        # Determine wallet classification
        classification, reputation_tags = self._classify_wallet(
            wallet_data, 
            total_balance_usd,
            performance_metrics
        )
        
        # Create or update profile
        profile = WalletProfile(
            address=address,
            classification=classification,
            first_seen=self.wallet_profiles.get(address, WalletProfile(address=address, classification="unknown", first_seen=current_time, last_active=current_time)).first_seen,
            last_active=current_time,
            total_balance_usd=total_balance_usd,
            transaction_count=wallet_data.get("transactions_analyzed", 0),
            tokens_held=len(token_accounts),
            historical_winners=performance_metrics.get("winners", 0),
            historical_losers=performance_metrics.get("losers", 0),
            average_hold_time=performance_metrics.get("avg_hold_time", 0),
            behavioral_score=self._calculate_behavioral_score(performance_metrics, wallet_data),
            token_entries=token_entries[:10],  # Keep most recent 10
            token_exits=token_exits[:10],      # Keep most recent 10
            reputation_tags=reputation_tags,
            risk_score=self._calculate_risk_score(wallet_data, performance_metrics)
        )
        
        # Update cache
        self.wallet_profiles[address] = profile
        self._save_cache()
        
        return profile
        
    async def _calculate_wallet_value(self, token_accounts: List[Dict]) -> float:
        """
        Calculate estimated total wallet value in USD
        
        Args:
            token_accounts: List of token accounts from RPC
            
        Returns:
            Estimated total value in USD
        """
        total_value = 0.0
        
        for account in token_accounts:
            token_address = account.get("mint", "")
            token_amount = float(account.get("amount", 0))
            token_decimals = account.get("decimals", 0)
            
            # Skip tokens with no info
            if not token_address or token_amount == 0:
                continue
                
            # Normalized token amount
            normalized_amount = token_amount / (10 ** token_decimals)
            
            # Get token price
            token_price = await self.jupiter_api.get_token_price_usd(token_address)
            if token_price:
                value = normalized_amount * token_price
                total_value += value
                
        return total_value
        
    def _extract_token_events(self, transactions: List[Dict]) -> Tuple[List[Dict], List[Dict]]:
        """
        Extract token entry (buy) and exit (sell) events from transactions
        
        Args:
            transactions: List of enhanced transactions from Helius
            
        Returns:
            Tuple of (entries, exits) lists
        """
        entries = []
        exits = []
        
        for tx in transactions:
            # Extract timestamp
            timestamp = tx.get("timestamp", 0) / 1000  # Convert to seconds
            
            # Find token transfers
            for transfer in tx.get("tokenTransfers", []):
                # Buy
                if transfer.get("toUserAccount") == tx.get("feePayer"):
                    entries.append({
                        "token": transfer.get("mint"),
                        "amount": transfer.get("tokenAmount", 0),
                        "timestamp": int(timestamp),
                        "tx_signature": tx.get("signature", "")
                    })
                
                # Sell
                elif transfer.get("fromUserAccount") == tx.get("feePayer"):
                    exits.append({
                        "token": transfer.get("mint"),
                        "amount": transfer.get("tokenAmount", 0),
                        "timestamp": int(timestamp),
                        "tx_signature": tx.get("signature", "")
                    })
                    
        # Sort by most recent first
        entries.sort(key=lambda x: x.get("timestamp", 0), reverse=True)
        exits.sort(key=lambda x: x.get("timestamp", 0), reverse=True)
        
        return entries, exits
        
    def _calculate_performance_metrics(self, entries: List[Dict], exits: List[Dict]) -> Dict[str, Any]:
        """
        Calculate performance metrics from entry and exit events
        
        Args:
            entries: List of token entry events
            exits: List of token exit events
            
        Returns:
            Dictionary of performance metrics
        """
        # This is a simplified implementation
        # In a real implementation, you would match buys and sells for the same token
        # and calculate profit/loss for each trade
        
        return {
            "winners": len([e for e in exits if e.get("profitable", True)]),
            "losers": len([e for e in exits if not e.get("profitable", True)]),
            "avg_hold_time": 72.0,  # Placeholder - 3 days average hold time
            "win_rate": 0.65 if exits else 0.0,  # Placeholder win rate
            "avg_profit": 2.5  # Placeholder - 2.5x average profit on winners
        }
        
    def _classify_wallet(self, 
                    wallet_data: Dict, 
                    balance_usd: float,
                    performance: Dict) -> Tuple[str, List[str]]:
        """
        Classify wallet based on its behavior and holdings
        
        Args:
            wallet_data: Wallet data from Helius
            balance_usd: Estimated balance in USD
            performance: Performance metrics dictionary
            
        Returns:
            Tuple of (classification, reputation_tags)
        """
        tags = []
        
        # Check for bot behavior
        tx_per_day = wallet_data.get("avg_tx_per_active_day", 0)
        is_likely_bot = wallet_data.get("is_likely_bot", False)
        
        if is_likely_bot or tx_per_day > 50:
            tags.append("bot")
            return "bot", tags
            
        # Check for whale status
        if balance_usd >= self.whale_threshold_usd:
            tags.append("whale")
            
        # Check for smart money indicators
        win_rate = performance.get("win_rate", 0)
        avg_profit = performance.get("avg_profit", 0)
        if win_rate > 0.6 and avg_profit > 2.0:
            tags.append("smart_money")
        
        # Check for token diversity
        token_diversity = wallet_data.get("unique_tokens_interacted", 0)
        if token_diversity > 20:
            tags.append("diverse_portfolio")
        elif token_diversity < 5:
            tags.append("concentrated_portfolio")
            
        # Determine primary classification
        if "whale" in tags and "smart_money" in tags:
            return "smart_whale", tags
        elif "whale" in tags:
            return "whale", tags
        elif "smart_money" in tags:
            return "smart_money", tags
        else:
            return "retail", tags
            
    def _calculate_behavioral_score(self, 
                              performance: Dict, 
                              wallet_data: Dict) -> float:
        """
        Calculate behavioral score based on wallet metrics
        
        Args:
            performance: Performance metrics dictionary
            wallet_data: Wallet data from Helius
            
        Returns:
            Behavioral score (0-1)
        """
        # Component scores
        win_rate = performance.get("win_rate", 0)
        avg_profit = min(performance.get("avg_profit", 0) / 5.0, 1.0)  # Cap at 5x
        
        # Diversity score - more diversity is better
        token_diversity = wallet_data.get("unique_tokens_interacted", 0)
        diversity_score = min(token_diversity / 20.0, 1.0)  # Cap at 20 tokens
        
        # Activity score - more consistent activity is better
        days_active = wallet_data.get("days_active", 0)
        tx_count = wallet_data.get("transactions_analyzed", 0)
        activity_score = min(days_active / 30.0, 1.0) * 0.5 + min(tx_count / 100.0, 1.0) * 0.5
        
        # Calculate overall score with weights
        score = (
            win_rate * 0.35 +
            avg_profit * 0.25 +
            diversity_score * 0.2 +
            activity_score * 0.2
        )
        
        return min(score, 1.0)  # Cap at 1.0
        
    def _calculate_risk_score(self, 
                        wallet_data: Dict, 
                        performance: Dict) -> float:
        """
        Calculate risk score for a wallet (higher = riskier)
        
        Args:
            wallet_data: Wallet data from Helius
            performance: Performance metrics dictionary
            
        Returns:
            Risk score (0-1)
        """
        # New wallets are riskier
        days_active = wallet_data.get("days_active", 0)
        age_risk = max(1.0 - (days_active / 90.0), 0.0)  # Newer = riskier
        
        # High transaction frequency can be risky
        tx_per_day = wallet_data.get("avg_tx_per_active_day", 0)
        frequency_risk = min(tx_per_day / 100.0, 1.0)
        
        # Low diversity is risky
        diversity = wallet_data.get("unique_tokens_interacted", 0)
        diversity_risk = max(1.0 - (diversity / 20.0), 0.0)
        
        # Low win rate is risky
        win_rate = performance.get("win_rate", 0.5)
        performance_risk = 1.0 - win_rate
        
        # Calculate overall risk score
        risk_score = (
            age_risk * 0.3 +
            frequency_risk * 0.2 +
            diversity_risk * 0.2 +
            performance_risk * 0.3
        )
        
        return min(risk_score, 1.0)  # Cap at 1.0
        
    async def analyze_token_holders(self, 
                             token_address: str, 
                             min_holders: int = 10) -> Dict[str, Any]:
        """
        Analyze token holders to provide holder-type distribution
        
        Args:
            token_address: Token address to analyze
            min_holders: Minimum number of holders to analyze
            
        Returns:
            Dictionary with holder analysis metrics
        """
        # Get token largest accounts
        largest_accounts = self.rpc.get_token_largest_accounts(token_address)
        
        # Limit to reasonable number to analyze
        accounts_to_analyze = largest_accounts[:min(len(largest_accounts), 20)]
        
        # Holder categories
        holder_types = {
            "whale": 0,
            "smart_money": 0,
            "retail": 0,
            "bot": 0,
            "smart_whale": 0,
            "unknown": 0
        }
        
        smart_money_holdings = 0.0
        whale_holdings = 0.0
        retail_holdings = 0.0
        bot_holdings = 0.0
        
        # Total supply from first account's info
        if accounts_to_analyze:
            first_account = accounts_to_analyze[0]
            total_supply = first_account.get("totalSupply", 0)
            if total_supply == 0:
                total_supply = 1  # Avoid division by zero
        else:
            total_supply = 1
            
        # Get owner addresses for each account
        owners = []
        for account in accounts_to_analyze:
            account_info = self.rpc.get_account_info(account.get("address", ""))
            owner_address = account_info.get("owner", "")
            amount = account.get("amount", 0)
            percentage = amount / total_supply
            
            owners.append({
                "address": owner_address,
                "percentage": percentage
            })
        
        # Analyze each owner
        for owner_data in owners:
            owner_address = owner_data["address"]
            holding_percentage = owner_data["percentage"]
            
            # Get wallet profile
            profile = await self.analyze_wallet(owner_address)
            
            if not profile:
                holder_types["unknown"] += 1
                continue
                
            # Update holder type counts
            holder_types[profile.classification] += 1
            
            # Track holdings by type
            if profile.classification == "whale":
                whale_holdings += holding_percentage
            elif profile.classification == "smart_money":
                smart_money_holdings += holding_percentage
            elif profile.classification == "smart_whale":
                smart_money_holdings += holding_percentage
                whale_holdings += holding_percentage
            elif profile.classification == "bot":
                bot_holdings += holding_percentage
            else:
                retail_holdings += holding_percentage
        
        return {
            "holder_distribution": {
                "whale_count": holder_types["whale"] + holder_types["smart_whale"],
                "smart_money_count": holder_types["smart_money"] + holder_types["smart_whale"],
                "retail_count": holder_types["retail"],
                "bot_count": holder_types["bot"],
                "unknown_count": holder_types["unknown"]
            },
            "holdings_distribution": {
                "whale_percentage": whale_holdings,
                "smart_money_percentage": smart_money_holdings,
                "retail_percentage": retail_holdings,
                "bot_percentage": bot_holdings
            },
            "smart_money_confidence": min(smart_money_holdings * 100, 1.0),  # 0-1 score
            "whale_risk": whale_holdings if whale_holdings > 0.5 else 0  # Risk if >50% whale holdings
        }
        
    def get_wallet_type(self, address: str) -> str:
        """
        Get wallet classification type
        
        Args:
            address: Wallet address
            
        Returns:
            Classification string
        """
        if address in self.wallet_profiles:
            return self.wallet_profiles[address].classification
        return "unknown"
        
    def get_behavioral_score(self, address: str) -> float:
        """
        Get wallet behavioral score
        
        Args:
            address: Wallet address
            
        Returns:
            Behavioral score (0-1)
        """
        if address in self.wallet_profiles:
            return self.wallet_profiles[address].behavioral_score
        return 0.0 