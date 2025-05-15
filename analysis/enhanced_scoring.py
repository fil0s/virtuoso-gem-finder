"""
Enhanced Scoring module for Virtuoso Gem Finder.

This module integrates the Smart Money Clustering, Wallet Analysis, Behavioral Scoring,
and Early Signal Weighting features into the main application.
"""

import logging
import asyncio
from typing import Dict, List, Tuple, Optional, Any
import yaml
import time
from pathlib import Path

# Import the new modules
from analysis.smart_money_clustering import SmartMoneyClusterer
from analysis.wallet_analyzer import WalletAnalyzer
from analysis.behavioral_scoring import BehavioralScorer
from analysis.momentum_analyzer import MomentumAnalyzer

class EnhancedScoring:
    """
    Main integration class for enhanced scoring features.
    """
    
    def __init__(self, config_path: str, helius_api, jupiter_api, rpc, rug_check_api=None, solscan_api=None):
        """
        Initialize the enhanced scoring system.
        
        Args:
            config_path: Path to the configuration file
            helius_api: Instance of HeliusAPI
            jupiter_api: Instance of JupiterAPI
            rpc: Instance of EnhancedSolanaRPC
            rug_check_api: Optional instance of RugCheckAPI
            solscan_api: Optional instance of SolscanAPI
        """
        self.config_path = config_path
        self.helius_api = helius_api
        self.jupiter_api = jupiter_api
        self.rpc = rpc
        self.rug_check_api = rug_check_api
        self.solscan_api = solscan_api
        self.logger = logging.getLogger('EnhancedScoring')
        
        # Load configuration
        self.config = self._load_config()
        
        # Create cache directory
        self.cache_dir = Path("./cache")
        self.cache_dir.mkdir(exist_ok=True)
        
        # Initialize components
        self._init_components()
        
    def _load_config(self) -> Dict:
        """Load configuration from YAML file"""
        try:
            with open(self.config_path, 'r') as f:
                config = yaml.safe_load(f)
            return config
        except Exception as e:
            self.logger.error(f"Error loading config: {e}")
            return {}
            
    def _init_components(self):
        """Initialize all enhanced scoring components"""
        # Initialize wallet analyzer
        wallet_config = self.config.get("wallet_analysis", {})
        if wallet_config.get("enabled", False):
            self.wallet_analyzer = WalletAnalyzer(
                self.helius_api,
                self.jupiter_api,
                self.rpc,
                cache_dir=wallet_config.get("wallet_cache_dir", "./cache")
            )
            self.logger.info("Wallet analyzer initialized")
        else:
            self.wallet_analyzer = None
            
        # Initialize smart money clusterer
        sm_config = self.config.get("smart_money", {})
        if sm_config.get("enabled", False):
            self.smart_money_clusterer = SmartMoneyClusterer(
                self.helius_api,
                self.jupiter_api,
                self.rpc,
                cache_dir=sm_config.get("wallet_cache_dir", "./cache")
            )
            self.logger.info("Smart money clusterer initialized")
        else:
            self.smart_money_clusterer = None
            
        # Initialize behavioral scorer
        bs_config = self.config.get("behavioral_scoring", {})
        if bs_config.get("enabled", False) and self.wallet_analyzer:
            self.behavioral_scorer = BehavioralScorer(
                self.helius_api,
                self.rpc,
                self.wallet_analyzer,
                cache_dir=bs_config.get("cache_dir", "./cache")
            )
            self.logger.info("Behavioral scorer initialized")
        else:
            self.behavioral_scorer = None
            
        # Initialize momentum analyzer
        ma_config = self.config.get("momentum_analysis", {})
        if ma_config.get("enabled", False):
            self.momentum_analyzer = MomentumAnalyzer(
                self.helius_api,
                self.jupiter_api,
                self.rpc,
                config_path=self.config_path,
                cache_dir=ma_config.get("cache_dir", "./cache/momentum")
            )
            self.logger.info("Momentum analyzer initialized")
        else:
            self.momentum_analyzer = None
            
    async def enhance_token_analysis(self, token_address: str, token_data: Dict, base_score: float) -> Dict[str, Any]:
        """
        Enhance token analysis with all available features.
        
        Args:
            token_address: Token address to analyze
            token_data: Base token data from DexScreener or other sources
            base_score: The pre-calculated base score for the token (0-100)
            
        Returns:
            Dictionary with enhanced analysis data
        """
        results = {
            "smart_money_analysis": None,
            "wallet_analysis": None,
            "behavioral_analysis": None,
            "onchain_momentum_analysis": None
        }
        
        # Parallelize the analysis tasks
        tasks = []
        
        # Create wallet analysis task
        if self.wallet_analyzer:
            tasks.append(self._analyze_token_wallets(token_address))
            
        # Create smart money analysis task
        if self.smart_money_clusterer:
            tasks.append(self._analyze_smart_money(token_address))
            
        # Create momentum analysis task if conditions are met
        should_run_momentum = False
        if self.momentum_analyzer:
            momentum_config = self.config.get("momentum_analysis", {})
            min_score_for_momentum = momentum_config.get("min_base_score_for_trigger", 0)
            if base_score >= min_score_for_momentum:
                should_run_momentum = True
                tasks.append(self._analyze_onchain_momentum(token_address))
            else:
                self.logger.info(f"Skipping momentum analysis for {token_address}, base_score {base_score} < {min_score_for_momentum}")
        
        # Execute tasks in parallel
        if tasks:
            analysis_results = await asyncio.gather(*tasks)
            
            # Process results
            task_idx = 0
            if self.wallet_analyzer:
                results["wallet_analysis"] = analysis_results[task_idx]
                task_idx += 1
            if self.smart_money_clusterer:
                results["smart_money_analysis"] = analysis_results[task_idx]
                task_idx += 1
            if self.momentum_analyzer and should_run_momentum:
                results["onchain_momentum_analysis"] = analysis_results[task_idx]
                task_idx += 1
        
        # Behavioral analysis depends on wallet analysis, so do it after
        if self.behavioral_scorer and results["wallet_analysis"]:
            results["behavioral_analysis"] = await self._perform_behavioral_analysis(
                token_address, 
                token_data, 
                results["wallet_analysis"]
            )
            
        return results
        
    async def _analyze_token_wallets(self, token_address: str) -> Dict[str, Any]:
        """
        Analyze token holders with wallet profiling.
        
        Args:
            token_address: Token address to analyze
            
        Returns:
            Wallet analysis results
        """
        try:
            wallet_config = self.config.get("wallet_analysis", {})
            max_wallets = wallet_config.get("max_wallets_to_analyze_per_token", 20)
            
            # Analyze token holders
            holder_analysis = await self.wallet_analyzer.analyze_token_holders(
                token_address,
                min_holders=max_wallets
            )
            
            return holder_analysis
        except Exception as e:
            self.logger.error(f"Error in wallet analysis: {e}")
            return {}
            
    async def _analyze_smart_money(self, token_address: str) -> Dict[str, Any]:
        """
        Perform smart money analysis on token.
        
        Args:
            token_address: Token address to analyze
            
        Returns:
            Smart money analysis results
        """
        try:
            sm_config = self.config.get("smart_money", {})
            min_confidence = sm_config.get("min_confidence_score", 0.6)
            
            # Identify smart money holders
            smart_holders = await self.smart_money_clusterer.identify_smart_money_holders(
                token_address,
                min_confidence=min_confidence
            )
            
            # Get token largest accounts for percentage calculation
            largest_accounts = self.rpc.get_token_largest_accounts(token_address)
            total_supply = largest_accounts[0].get("totalSupply", 1) if largest_accounts else 1
            
            # Calculate smart money share
            sm_share = 0.0
            for holder, confidence in smart_holders:
                # Get account holdings
                holdings = self._get_holder_percentage(holder, token_address, largest_accounts) 
                sm_share += holdings
                
            # Check if clustering should be run
            do_clustering = (
                sm_config.get("clustering", {}).get("enabled", False) and
                len(self.smart_money_clusterer.smart_wallets) >= 
                sm_config.get("clustering", {}).get("min_wallets_for_clustering", 10)
            )
            
            # Run clustering if needed
            clusters = []
            if do_clustering:
                # Check if we need to recalculate clusters
                recalc_interval = sm_config.get("clustering", {}).get("recalculate_interval_hours", 24) * 3600
                if time.time() - getattr(self.smart_money_clusterer, "last_cluster_time", 0) > recalc_interval:
                    clusters = await self.smart_money_clusterer.cluster_smart_wallets()
                    self.smart_money_clusterer.last_cluster_time = time.time()
                else:
                    clusters = self.smart_money_clusterer.wallet_clusters
                    
            return {
                "smart_money_holders": [
                    {"address": addr, "confidence": conf}
                    for addr, conf in smart_holders
                ],
                "smart_money_share": sm_share,
                "cluster_count": len(clusters),
                "clusters": [
                    {
                        "id": c.cluster_id,
                        "wallet_count": c.wallet_count,
                        "classification": c.classification,
                        "confidence": c.confidence_score,
                        "avg_win_rate": c.avg_win_rate,
                        "avg_profit_multiple": c.avg_profit_multiple
                    }
                    for c in clusters
                ],
                "confidence_score": min(sm_share * 2, 1.0)  # 0-1 score based on share
            }
        except Exception as e:
            self.logger.error(f"Error in smart money analysis: {e}")
            return {}
            
    def _get_holder_percentage(self, holder_address: str, token_address: str, largest_accounts: List[Dict]) -> float:
        """Get the percentage of token held by an address"""
        total_supply = largest_accounts[0].get("totalSupply", 1) if largest_accounts else 1
        
        # Find holder's accounts
        holder_amount = 0
        for account in largest_accounts:
            account_info = self.rpc.get_account_info(account.get("address", ""))
            if account_info.get("owner", "") == holder_address:
                holder_amount += account.get("amount", 0)
                
        return holder_amount / total_supply
            
    async def _perform_behavioral_analysis(self, 
                                    token_address: str, 
                                    token_data: Dict,
                                    wallet_analysis: Dict) -> Dict[str, Any]:
        """
        Perform behavioral scoring analysis.
        
        Args:
            token_address: Token address to analyze
            token_data: Base token data
            wallet_analysis: Wallet analysis results
            
        Returns:
            Behavioral analysis results
        """
        try:
            # Calculate token behavioral score
            metrics = await self.behavioral_scorer.calculate_token_behavioral_score(
                token_address,
                token_data,
                wallet_analysis
            )
            
            # Extract early and trailing signals with weights
            bs_config = self.config.get("behavioral_scoring", {})
            early_weights = bs_config.get("early_signal_weights", {})
            trailing_weights = bs_config.get("trailing_signal_weights", {})
            
            # Calculate weighted early signals
            early_signals = {}
            for signal, value in metrics.early_signals.items():
                weight = early_weights.get(signal, 1.0)
                early_signals[signal] = {
                    "score": value,
                    "weight": weight,
                    "weighted_score": value * weight
                }
                
            # Calculate weighted trailing signals
            trailing_signals = {}
            for signal, value in metrics.trailing_signals.items():
                weight = trailing_weights.get(signal, 1.0)
                trailing_signals[signal] = {
                    "score": value,
                    "weight": weight,
                    "weighted_score": value * weight
                }
                
            return {
                "developer_score": metrics.developer_score,
                "community_growth_score": metrics.community_growth_score,
                "transaction_pattern_score": metrics.transaction_pattern_score,
                "early_signal_score": metrics.early_signal_score,
                "composite_score": metrics.composite_score,
                "early_signals": early_signals,
                "trailing_signals": trailing_signals,
                "warning_flags": metrics.warning_flags
            }
        except Exception as e:
            self.logger.error(f"Error in behavioral analysis: {e}")
            return {}
    
    def calculate_enhanced_gem_score(self, base_score: float, enhanced_data: Dict) -> Tuple[float, Dict]:
        """
        Calculate enhanced gem score that incorporates all new features.
        
        Args:
            base_score: Base gem score from original scoring system
            enhanced_data: Enhanced analysis data
            
        Returns:
            Tuple of (enhanced_score, score_components)
        """
        # Default adjustments
        smart_money_adj = 0.0
        wallet_analysis_adj = 0.0
        behavioral_adj = 0.0
        momentum_adj = 0.0
        
        # Extract component scores
        wallet_data = enhanced_data.get("wallet_analysis", {})
        smart_money_data = enhanced_data.get("smart_money_analysis", {})
        behavioral_data = enhanced_data.get("behavioral_analysis", {})
        momentum_data = enhanced_data.get("onchain_momentum_analysis", {})
        
        # Smart money adjustment (0-10% boost)
        if smart_money_data:
            sm_share = smart_money_data.get("smart_money_share", 0)
            sm_confidence = smart_money_data.get("confidence_score", 0)
            
            # Higher adjustment for higher smart money interest
            smart_money_adj = min(sm_share * sm_confidence * 10, 10.0)
            
        # Wallet analysis adjustment (-5% to +5%)
        if wallet_data:
            # Positive adjustment for high smart money percentage
            sm_percentage = wallet_data.get("holdings_distribution", {}).get("smart_money_percentage", 0)
            
            # Negative adjustment for high whale concentration
            whale_risk = wallet_data.get("whale_risk", 0)
            
            wallet_analysis_adj = min(sm_percentage * 10, 5.0) - min(whale_risk * 10, 5.0)
            
        # Behavioral adjustment (-10% to +10%)
        if behavioral_data:
            composite_score = behavioral_data.get("composite_score", 0.5)
            warning_count = len(behavioral_data.get("warning_flags", []))
            
            # Higher score = positive adjustment, warnings = negative adjustment
            behavioral_adj = (composite_score - 0.5) * 20 - warning_count * 2
            behavioral_adj = max(min(behavioral_adj, 10.0), -10.0)  # Cap at -10% to +10%
            
        # Momentum adjustment (e.g., -10% to +15% boost based on overall_momentum_score)
        if momentum_data and self.momentum_analyzer:
            overall_momentum_score = momentum_data.get("overall_momentum_score")
            
            if overall_momentum_score is not None:
                # Example: score of 0.5 is neutral, 1.0 is max positive, 0.0 is max negative
                # score_impact defines the max % change, e.g. [-10, 15] for -10% to +15%
                impact_range = self.config.get("momentum_analysis", {}).get("score_impact_percentage", [-10, 15]) 
                min_impact, max_impact = impact_range[0], impact_range[1]
                
                # Linear scaling: (score - 0.5) * 2 maps 0-1 score to -1 to 1 range
                # Then scale by positive or negative impact range
                scaled_factor = (overall_momentum_score - 0.5) * 2
                if scaled_factor >= 0:
                    momentum_adj = scaled_factor * max_impact
                else:
                    momentum_adj = scaled_factor * abs(min_impact) # abs because scaled_factor is already negative
                
                momentum_adj = max(min(momentum_adj, max_impact), min_impact)

            # Consider error messages or incomplete data if needed
            if momentum_data.get("error_messages"):
                self.logger.warning(f"Momentum analysis for token had errors: {momentum_data.get('error_messages')}")
                # Potentially apply a neutral or slight negative adjustment if errors occurred
                # momentum_adj = min(momentum_adj, 0) # Example: cap positive effect if errors

        # Calculate total adjustment percentage
        total_adj_pct = smart_money_adj + wallet_analysis_adj + behavioral_adj + momentum_adj
        
        # Apply adjustment to base score
        adjusted_score = base_score * (1 + total_adj_pct / 100)
        
        # Cap at 100
        final_score = min(max(adjusted_score, 0), 100)
        
        # Return score and components
        return final_score, {
            "base_score": base_score,
            "smart_money_adjustment": smart_money_adj,
            "wallet_analysis_adjustment": wallet_analysis_adj,
            "behavioral_adjustment": behavioral_adj,
            "momentum_adjustment": momentum_adj,
            "total_adjustment_pct": total_adj_pct,
            "final_score": final_score
        }
        
    async def run_wallet_clustering(self) -> int:
        """
        Run smart money wallet clustering as a background task.
        
        Returns:
            Number of clusters found
        """
        if not self.smart_money_clusterer:
            return 0
            
        try:
            clusters = await self.smart_money_clusterer.cluster_smart_wallets()
            self.smart_money_clusterer.last_cluster_time = time.time()
            return len(clusters)
        except Exception as e:
            self.logger.error(f"Error running wallet clustering: {e}")
            return 0

    async def _analyze_onchain_momentum(self, token_address: str) -> Dict[str, Any]:
        """
        Perform on-chain momentum analysis on token.
        
        Args:
            token_address: Token address to analyze
            
        Returns:
            On-chain momentum analysis results
        """
        if not self.momentum_analyzer:
            self.logger.info("Momentum analyzer not enabled or initialized.")
            return {}
        try:
            momentum_results = await self.momentum_analyzer.analyze_token_momentum(token_address)
            return momentum_results
        except Exception as e:
            self.logger.error(f"Error in on-chain momentum analysis for {token_address}: {e}")
            return {"error": str(e)} 