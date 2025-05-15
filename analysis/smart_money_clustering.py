"""
Smart Money Clustering module for Virtuoso Gem Finder.

This module implements wallet analysis and clustering to identify "smart money" wallets
based on their historical performance with early token investments.
"""

import asyncio
from typing import Dict, List, Set, Tuple, Optional, Any
import logging
import numpy as np
from sklearn.cluster import DBSCAN
from datetime import datetime, timedelta
import json
import os
from pathlib import Path
from dataclasses import dataclass, field, asdict
import time

@dataclass
class SmartWallet:
    """Data class for storing smart wallet information and metrics"""
    address: str
    win_rate: float = 0.0  # Percentage of profitable trades (0.0-1.0)
    avg_profit_multiple: float = 0.0  # Average ROI multiplier on profitable trades
    early_entry_rate: float = 0.0  # Rate of entering tokens early (before significant price movement)
    trade_count: int = 0  # Total number of trades analyzed
    profitable_exits: int = 0  # Number of trades with profitable exits
    avg_hold_time: float = 0.0  # Average holding period in hours
    entry_timing_score: float = 0.0  # 0-1 score for how early wallet typically enters
    performance_7d: float = 0.0  # 7-day performance (ROI)
    performance_30d: float = 0.0  # 30-day performance (ROI)
    token_diversity: int = 0  # Number of unique tokens traded
    first_seen: int = 0  # Timestamp of first observed transaction
    cluster_id: int = -1  # Cluster this wallet belongs to (-1 = unclustered)
    top_tokens: List[str] = field(default_factory=list)  # Top tokens this wallet has profited from
    tags: List[str] = field(default_factory=list)  # Classification tags

@dataclass
class WalletCluster:
    """Data class for storing cluster information"""
    cluster_id: int
    wallet_count: int = 0
    avg_win_rate: float = 0.0
    avg_profit_multiple: float = 0.0
    avg_entry_timing: float = 0.0
    member_wallets: List[str] = field(default_factory=list)
    common_tokens: List[str] = field(default_factory=list)
    classification: str = "Unknown"  # Smart Money, Retail, Whale, etc.
    confidence_score: float = 0.0


class SmartMoneyClusterer:
    """
    Implements smart money wallet identification and clustering based on transaction
    history and profitability metrics.
    """
    
    def __init__(self, helius_api, jupiter_api, enhanced_rpc, cache_dir: str = "./cache"):
        """
        Initialize the smart money clusterer.
        
        Args:
            helius_api: Instance of HeliusAPI for transaction analysis
            jupiter_api: Instance of JupiterAPI for price data
            enhanced_rpc: Instance of EnhancedSolanaRPC for blockchain data
            cache_dir: Directory to store wallet analysis cache
        """
        self.helius_api = helius_api
        self.jupiter_api = jupiter_api
        self.rpc = enhanced_rpc
        self.logger = logging.getLogger('SmartMoneyClusterer')
        
        # Cache directory for wallet analysis
        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(exist_ok=True)
        self.wallet_cache_file = self.cache_dir / "smart_wallets.json"
        
        # Smart wallet database (address -> SmartWallet)
        self.smart_wallets: Dict[str, SmartWallet] = {}
        self.wallet_clusters: List[WalletCluster] = []
        
        # Load cached data if available
        self._load_cache()
        
    def _load_cache(self):
        """Load cached wallet analysis data if available"""
        if self.wallet_cache_file.exists():
            try:
                with open(self.wallet_cache_file, 'r') as f:
                    wallet_data = json.load(f)
                    
                self.smart_wallets = {
                    addr: SmartWallet(**data) 
                    for addr, data in wallet_data.items()
                }
                self.logger.info(f"Loaded {len(self.smart_wallets)} wallets from cache")
            except Exception as e:
                self.logger.error(f"Error loading wallet cache: {e}")
                
    def _save_cache(self):
        """Save wallet analysis data to cache"""
        try:
            wallet_data = {
                addr: asdict(wallet)
                for addr, wallet in self.smart_wallets.items()
            }
            
            with open(self.wallet_cache_file, 'w') as f:
                json.dump(wallet_data, f)
                
            self.logger.info(f"Saved {len(self.smart_wallets)} wallets to cache")
        except Exception as e:
            self.logger.error(f"Error saving wallet cache: {e}")
            
    async def analyze_wallet(self, address: str) -> Optional[SmartWallet]:
        """
        Perform comprehensive analysis of a wallet to determine if it's "smart money"
        
        Args:
            address: Wallet address to analyze
            
        Returns:
            SmartWallet object with analysis results or None if insufficient data
        """
        # Check if we have cached analysis
        if address in self.smart_wallets:
            # If analysis is recent (last 24h), use cached data
            wallet = self.smart_wallets[address]
            cache_age = time.time() - wallet.first_seen
            if cache_age < 86400:  # 24 hours
                return wallet
        
        # Get wallet transaction history and metrics
        wallet_data = await self.helius_api.analyze_wallet(address)
        
        if not wallet_data or wallet_data.get("analysis") == "insufficient_data":
            return None
            
        # Get token transactions for profitability analysis
        enhanced_txs = await self.helius_api.get_enhanced_transactions(address, 100)
        
        # Extract token transfers and analyze profitability
        tokens_traded, profit_data = await self._analyze_token_profitability(enhanced_txs)
        
        # Create smart wallet object with metrics
        smart_wallet = SmartWallet(
            address=address,
            win_rate=profit_data.get("win_rate", 0.0),
            avg_profit_multiple=profit_data.get("avg_profit_multiple", 0.0),
            early_entry_rate=profit_data.get("early_entry_rate", 0.0),
            trade_count=profit_data.get("trade_count", 0),
            profitable_exits=profit_data.get("profitable_exits", 0),
            avg_hold_time=profit_data.get("avg_hold_time", 0.0),
            entry_timing_score=profit_data.get("entry_timing_score", 0.0),
            performance_7d=profit_data.get("performance_7d", 0.0),
            performance_30d=profit_data.get("performance_30d", 0.0),
            token_diversity=len(tokens_traded),
            first_seen=int(time.time()),
            top_tokens=profit_data.get("top_tokens", []),
            tags=self._classify_wallet(profit_data)
        )
        
        # Cache the analysis
        self.smart_wallets[address] = smart_wallet
        self._save_cache()
        
        return smart_wallet
        
    async def _analyze_token_profitability(self, 
                                     transactions: List[Dict]) -> Tuple[Set[str], Dict[str, Any]]:
        """
        Analyze token transactions to determine profitability metrics
        
        Args:
            transactions: List of enhanced transactions from Helius API
            
        Returns:
            Tuple of (set of token addresses traded, profitability metrics dictionary)
        """
        tokens_traded = set()
        token_entries = {}  # token -> {timestamp, price, amount}
        token_exits = {}  # token -> {timestamp, price, amount}
        profit_data = {
            "win_rate": 0.0,
            "avg_profit_multiple": 0.0,
            "early_entry_rate": 0.0,
            "trade_count": 0,
            "profitable_exits": 0,
            "avg_hold_time": 0.0,
            "entry_timing_score": 0.0,
            "performance_7d": 0.0,
            "performance_30d": 0.0,
            "top_tokens": []
        }
        
        # Process is simplified here - actual implementation would need to:
        # 1. Track token buys and sells with proper matching
        # 2. Calculate entry and exit prices
        # 3. Track holding periods
        # 4. Calculate P&L for each token
        
        # This is a simplified placeholder
        for tx in transactions:
            # Extract token transfers
            for transfer in tx.get("tokenTransfers", []):
                token_mint = transfer.get("mint")
                if not token_mint:
                    continue
                    
                tokens_traded.add(token_mint)
                
                # More detailed analysis would be done here
        
        # Placeholder profit calculation (would be more complex in full implementation)
        if len(tokens_traded) > 0:
            profit_data["win_rate"] = 0.65  # Placeholder
            profit_data["trade_count"] = len(tokens_traded)
            profit_data["token_diversity"] = len(tokens_traded)
            
        return tokens_traded, profit_data
        
    def _classify_wallet(self, profit_data: Dict[str, Any]) -> List[str]:
        """
        Classify a wallet based on its profitability metrics
        
        Args:
            profit_data: Dictionary of profitability metrics
            
        Returns:
            List of classification tags
        """
        tags = []
        
        # Simplified classification logic
        win_rate = profit_data.get("win_rate", 0.0)
        avg_profit = profit_data.get("avg_profit_multiple", 0.0)
        trade_count = profit_data.get("trade_count", 0)
        early_entry = profit_data.get("early_entry_rate", 0.0)
        
        # Smart money classification
        if win_rate > 0.6 and avg_profit > 3.0 and early_entry > 0.5:
            tags.append("smart_money")
            
        # High volume trader
        if trade_count > 50:
            tags.append("high_volume")
            
        # Early investor
        if early_entry > 0.7:
            tags.append("early_investor")
            
        # Diamond hands (long hold times)
        if profit_data.get("avg_hold_time", 0) > 720:  # > 30 days
            tags.append("diamond_hands")
            
        return tags
        
    async def cluster_smart_wallets(self) -> List[WalletCluster]:
        """
        Cluster wallets based on behavior similarity using DBSCAN
        
        Returns:
            List of wallet clusters
        """
        if len(self.smart_wallets) < 10:
            self.logger.warning("Not enough wallets to perform clustering")
            return []
            
        # Extract features for clustering
        addresses = []
        features = []
        
        for addr, wallet in self.smart_wallets.items():
            addresses.append(addr)
            features.append([
                wallet.win_rate,
                wallet.avg_profit_multiple,
                wallet.early_entry_rate,
                wallet.entry_timing_score,
                wallet.avg_hold_time / 24.0  # Normalize to days
            ])
            
        # Normalize features
        features_array = np.array(features)
        features_normalized = (features_array - features_array.mean(axis=0)) / features_array.std(axis=0)
        
        # Run DBSCAN clustering
        clustering = DBSCAN(eps=0.5, min_samples=5).fit(features_normalized)
        
        # Update wallet cluster IDs
        clusters = {}
        for i, addr in enumerate(addresses):
            cluster_id = clustering.labels_[i]
            self.smart_wallets[addr].cluster_id = cluster_id
            
            if cluster_id not in clusters:
                clusters[cluster_id] = []
            clusters[cluster_id].append(addr)
            
        # Create cluster objects
        self.wallet_clusters = []
        for cluster_id, member_addrs in clusters.items():
            if cluster_id == -1:  # Skip unclustered wallets
                continue
                
            # Calculate cluster metrics
            members = [self.smart_wallets[addr] for addr in member_addrs]
            avg_win_rate = sum(w.win_rate for w in members) / len(members)
            avg_profit = sum(w.avg_profit_multiple for w in members) / len(members)
            avg_entry = sum(w.entry_timing_score for w in members) / len(members)
            
            # Find common tokens
            token_counts = {}
            for wallet in members:
                for token in wallet.top_tokens:
                    if token not in token_counts:
                        token_counts[token] = 0
                    token_counts[token] += 1
            
            common_tokens = [
                token for token, count in token_counts.items()
                if count >= len(members) * 0.3  # At least 30% of members traded this token
            ]
            
            # Classify the cluster
            classification = "Unknown"
            if avg_win_rate > 0.7 and avg_profit > 5.0:
                classification = "Smart Money"
            elif avg_win_rate > 0.5 and avg_profit > 2.0:
                classification = "Skilled Trader"
            elif avg_entry > 0.8:
                classification = "Early Adopter"
            
            cluster = WalletCluster(
                cluster_id=cluster_id,
                wallet_count=len(members),
                avg_win_rate=avg_win_rate,
                avg_profit_multiple=avg_profit,
                avg_entry_timing=avg_entry,
                member_wallets=member_addrs,
                common_tokens=common_tokens,
                classification=classification,
                confidence_score=min(avg_win_rate * avg_profit, 1.0)
            )
            
            self.wallet_clusters.append(cluster)
            
        # Save updated wallet data
        self._save_cache()
        
        return self.wallet_clusters
        
    async def identify_smart_money_holders(self, 
                                     token_address: str, 
                                     min_confidence: float = 0.6) -> List[Tuple[str, float]]:
        """
        Identify smart money wallets holding a specific token
        
        Args:
            token_address: Token mint address to check
            min_confidence: Minimum confidence score (0-1)
            
        Returns:
            List of (wallet_address, confidence_score) tuples
        """
        # Get token holders
        holder_accounts = self.rpc.get_token_largest_accounts(token_address)
        
        smart_holders = []
        for account in holder_accounts:
            account_info = self.rpc.get_account_info(account.get("address", ""))
            owner = account_info.get("owner", "")
            
            # Check if owner is in our smart money database
            if owner in self.smart_wallets:
                wallet = self.smart_wallets[owner]
                
                # Calculate confidence score
                confidence = wallet.win_rate * wallet.avg_profit_multiple
                if confidence >= min_confidence:
                    smart_holders.append((owner, confidence))
                    
        return smart_holders
        
    def get_wallet_behavioral_score(self, address: str) -> float:
        """
        Get behavioral score for a wallet based on its metrics
        
        Args:
            address: Wallet address
            
        Returns:
            Behavioral score (0-1)
        """
        if address not in self.smart_wallets:
            return 0.0
            
        wallet = self.smart_wallets[address]
        
        # Calculate behavioral score based on key metrics
        score = (
            wallet.win_rate * 0.3 +
            min(wallet.avg_profit_multiple / 10.0, 1.0) * 0.3 +
            wallet.early_entry_rate * 0.2 +
            wallet.entry_timing_score * 0.2
        )
        
        return min(score, 1.0)  # Cap at 1.0
        
    def classify_wallet_type(self, address: str) -> str:
        """
        Classify a wallet as smart money, whale, or retail
        
        Args:
            address: Wallet address
            
        Returns:
            Classification string
        """
        if address not in self.smart_wallets:
            return "unknown"
            
        wallet = self.smart_wallets[address]
        
        # Check for smart money
        behavioral_score = self.get_wallet_behavioral_score(address)
        if behavioral_score > 0.7:
            return "smart_money"
        
        # Check tags for classification hints
        if "whale" in wallet.tags:
            return "whale"
            
        # Default to retail
        return "retail" 