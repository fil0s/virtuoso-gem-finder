"""
Solana On-chain Momentum Analyzer for Virtuoso Gem Finder.

This module provides functionality to analyze various on-chain momentum
indicators for Solana tokens.
"""

import logging
import asyncio
from typing import Dict, List, Any, Optional
import yaml
import time
from pathlib import Path
import math

# Import actual API class types for type hinting
from helius_connector import HeliusAPI
from jupiter_connector import JupiterAPI
from solana_rpc_enhanced import EnhancedSolanaRPC

# Assuming helius_api, jupiter_api, and rpc types are defined elsewhere
# from helius_connector import HeliusAPI # Example
# from jupiter_connector import JupiterAPI # Example
# from solana_rpc_enhanced import EnhancedSolanaRPC # Example

class MomentumAnalyzer:
    """
    Analyzes on-chain momentum for Solana tokens.
    """
    def __init__(self, 
                 helius_api: HeliusAPI,
                 jupiter_api: JupiterAPI,
                 rpc: EnhancedSolanaRPC,
                 config_path: str,
                 cache_dir: str = "./cache/momentum"):
        """
        Initialize the MomentumAnalyzer.

        Args:
            helius_api: Instance of HeliusAPI.
            jupiter_api: Instance of JupiterAPI.
            rpc: Instance of EnhancedSolanaRPC.
            config_path: Path to the main configuration file.
            cache_dir: Directory to store cache for momentum analysis.
        """
        self.helius_api = helius_api
        self.jupiter_api = jupiter_api
        self.rpc = rpc
        self.config_path = config_path
        self.logger = logging.getLogger('MomentumAnalyzer')
        
        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        
        self.config = self._load_momentum_config()
        self.normalization_params = self.config.get("normalization_params", {
            "price_change_scale": 0.2,
            "volume_change_scale": 1.0,
            "holder_growth_scale": 0.1,
            "tx_velocity_scale": 100,
            "net_flow_scale": 0.5 # e.g., scale for a net flow metric (-1 to 1, normalized)
        })
        self.tx_velocity_config = self.config.get("transaction_velocity_config", {
            "lookback_seconds": 3600, 
            "min_tx_count_for_max_score": 200 
        })
        self.net_flow_config = self.config.get("net_flow_config", {
            "lookback_seconds": 3600, # Lookback for net flow analysis
            "cex_wallets_list_url": None # Optional: URL to a list of known CEX wallets
        })

    def _load_momentum_config(self) -> Dict:
        """Load momentum-specific configuration from the main config file."""
        try:
            with open(self.config_path, 'r') as f:
                full_config = yaml.safe_load(f)
            momentum_config = full_config.get("momentum_analysis", {})
            if not momentum_config.get("enabled", False):
                self.logger.info("Momentum analysis is disabled in the configuration.")
                return {}
            self.logger.info("MomentumAnalyzer configuration loaded.")
            return momentum_config
        except FileNotFoundError:
            self.logger.error(f"Configuration file not found at {self.config_path}")
            return {}
        except Exception as e:
            self.logger.error(f"Error loading momentum configuration: {e}")
            return {}

    def _normalize_score(self, value: float, center: float = 0.0, scale: float = 1.0, steepness: float = 1.0) -> float:
        """
        Normalizes a raw value (e.g., percentage change) to a 0-1 score using a scaled arctan function.
        This provides an S-shaped curve, good for metrics where extreme values have diminishing impact.

        Args:
            value: The raw value to normalize (e.g., fractional change like 0.1 for +10%).
            center: The value that should map to a score of 0.5.
            scale: Controls the range of values that map to the 0-1 score.
                   A smaller scale means the score changes more rapidly around the center.
                   Roughly, values from center - scale to center + scale will cover a significant portion of the 0-1 range.
            steepness: Controls the steepness of the S-curve. Higher values make it steeper.

        Returns:
            A normalized score between 0 and 1.
        """
        if scale <= 0:
            self.logger.warning("Normalization scale must be positive. Defaulting to 1.0.")
            scale = 1.0
        
        # Scaled and shifted arctan: (atan(steepness * (value - center) / scale) / pi) + 0.5
        # This maps (-inf, +inf) to (0, 1)
        normalized = (math.atan(steepness * (value - center) / scale) / math.pi) + 0.5
        
        # Clamp to ensure it's strictly within [0, 1] due to potential floating point inaccuracies
        return max(0.0, min(1.0, normalized))

    async def analyze_token_momentum(self, token_address: str) -> Dict[str, Any]:
        """
        Analyze various momentum indicators for a given token.

        Args:
            token_address: The Solana address of the token to analyze.

        Returns:
            A dictionary containing momentum scores and related data.
            Example:
            {
                "price_momentum": {"1h": 0.5, "24h": 0.7, ...},
                "volume_momentum": {"1h": 0.6, "24h": 0.8, ...},
                "holder_growth_momentum": {"24h": 0.3, "7d": 0.5, ...},
                "transaction_velocity": 0.4,
                "net_flow_score": 0.6, // Positive for inflow, negative for outflow
                "overall_momentum_score": 0.65 // Weighted average or composite score
            }
        """
        if not self.config.get("enabled", False):
            return {"error": "Momentum analysis is disabled."}

        self.logger.info(f"Starting momentum analysis for token: {token_address}")
        
        # Placeholder for actual analysis logic
        # This will involve calling helper methods for each metric
        # e.g., self._calculate_price_momentum(token_address)
        # e.g., self._calculate_volume_momentum(token_address)
        # e.g., self._calculate_holder_growth(token_address)
        
        # Example structure of results
        momentum_results = {
            "price_momentum": {},
            "volume_momentum": {},
            "holder_growth_momentum": {},
            "transaction_velocity": None,
            "net_flow_score": None,
            "overall_momentum_score": None,
            "error_messages": []
        }
        
        timeframes = self.config.get("timeframes", ["1h", "24h", "7d"])
        weights = self.config.get("weights", {
            "price_momentum": 0.35,
            "volume_momentum": 0.25,
            "holder_growth": 0.20,
            "transaction_velocity": 0.10,
            "net_flow": 0.10
        })

        # --- Sub-Analysis Tasks ---
        # These would be more detailed async methods
        
        # Price Momentum
        try:
            price_mom = await self._get_price_momentum(token_address, timeframes)
            momentum_results["price_momentum"] = price_mom
        except Exception as e:
            msg = f"Error calculating price momentum for {token_address}: {e}"
            self.logger.error(msg)
            momentum_results["error_messages"].append(msg)

        # Volume Momentum
        try:
            vol_mom = await self._get_volume_momentum(token_address, timeframes)
            momentum_results["volume_momentum"] = vol_mom
        except Exception as e:
            msg = f"Error calculating volume momentum for {token_address}: {e}"
            self.logger.error(msg)
            momentum_results["error_messages"].append(msg)

        # Holder Growth
        try:
            holder_growth = await self._get_holder_growth_momentum(token_address, timeframes)
            momentum_results["holder_growth_momentum"] = holder_growth
        except Exception as e:
            msg = f"Error calculating holder growth for {token_address}: {e}"
            self.logger.error(msg)
            momentum_results["error_messages"].append(msg)

        # Transaction Velocity (More complex, might need Helius)
        try:
            tx_velocity = await self._calculate_transaction_velocity(token_address)
            momentum_results["transaction_velocity"] = tx_velocity
        except Exception as e:
            msg = f"Error calculating transaction velocity for {token_address}: {e}"
            self.logger.error(msg)
            momentum_results["error_messages"].append(msg)

        # Net Flow (More complex, might need Helius and wallet tagging)
        try:
            net_flow = await self._calculate_net_flow(token_address)
            momentum_results["net_flow_score"] = net_flow
        except Exception as e:
            msg = f"Error calculating net flow for {token_address}: {e}"
            self.logger.error(msg)
            momentum_results["error_messages"].append(msg)

        # Calculate overall momentum score (simple weighted average for now)
        overall_score = 0
        total_weight = 0
        
        # Simplified scoring - assumes sub-metrics return a single score or an average
        # This needs refinement based on actual data structure from sub-methods
        
        # Example: If price_momentum returns dict of scores, we might average them
        if momentum_results["price_momentum"] and isinstance(momentum_results["price_momentum"], dict):
            avg_price_score = sum(momentum_results["price_momentum"].values()) / len(momentum_results["price_momentum"]) if momentum_results["price_momentum"] else 0
            overall_score += avg_price_score * weights.get("price_momentum", 0)
            total_weight += weights.get("price_momentum", 0)

        if momentum_results["volume_momentum"] and isinstance(momentum_results["volume_momentum"], dict):
            avg_vol_score = sum(momentum_results["volume_momentum"].values()) / len(momentum_results["volume_momentum"]) if momentum_results["volume_momentum"] else 0
            overall_score += avg_vol_score * weights.get("volume_momentum", 0)
            total_weight += weights.get("volume_momentum", 0)
            
        if momentum_results["holder_growth_momentum"] and isinstance(momentum_results["holder_growth_momentum"], dict):
            # Holder growth might be structured differently, e.g. {"7d_growth_rate": 0.1, "7d_score": 0.7}
            # For simplicity, let's assume it gives a score per timeframe and we average it
            avg_holder_score = sum(momentum_results["holder_growth_momentum"].values()) / len(momentum_results["holder_growth_momentum"]) if momentum_results["holder_growth_momentum"] else 0
            overall_score += avg_holder_score * weights.get("holder_growth", 0)
            total_weight += weights.get("holder_growth", 0)

        # Add other factors if implemented
        if momentum_results["transaction_velocity"] is not None:
            overall_score += momentum_results["transaction_velocity"] * weights.get("transaction_velocity", 0)
            total_weight += weights.get("transaction_velocity", 0)
        
        if momentum_results["net_flow_score"] is not None:
            overall_score += momentum_results["net_flow_score"] * weights.get("net_flow", 0)
            total_weight += weights.get("net_flow", 0)
        
        if total_weight > 0:
            momentum_results["overall_momentum_score"] = round(overall_score / total_weight, 3)
        else:
            momentum_results["overall_momentum_score"] = 0
            
        self.logger.info(f"Momentum analysis for {token_address} completed. Score: {momentum_results['overall_momentum_score']}")
        return momentum_results

    async def _get_price_momentum(self, token_address: str, timeframes: List[str]) -> Dict[str, Optional[float]]:
        """
        Calculate price momentum for different timeframes.
        Uses JupiterAPI to provide historical price data.
        """
        if not self.jupiter_api:
            self.logger.warning(f"JupiterAPI not available, cannot calculate price momentum for {token_address}.")
            return {tf: None for tf in timeframes}

        self.logger.debug(f"Calculating price momentum for {token_address} over {timeframes}")
        price_momentum_scores = {}
        
        price_scale = self.normalization_params.get("price_change_scale", 0.2) # Default to 20% scale

        for tf in timeframes:
            try:
                # We need two data points: current (or most recent) and previous (at start of timeframe)
                # The limit might depend on how get_historical_prices interprets 'timeframe'
                # Assuming limit=2 gives [latest, previous_for_timeframe_start]
                # Or, more robustly, fetch a small series and pick the right points.
                # For simplicity with current placeholder: fetch 2 points.
                # A real API might take `startTime` and `endTime` or `periodCount`.
                # The placeholder `get_historical_prices` returns data sorted by timestamp (ascending).
                historical_data = await self.jupiter_api.get_historical_prices(
                    token_mint=token_address, 
                    timeframe=tf, # The placeholder uses this to determine time_delta
                    limit=2 # Request two points: current and one at timeframe start
                )

                if historical_data and len(historical_data) == 2:
                    # Data is sorted [oldest, newest] by placeholder
                    price_then = historical_data[0].get('price') 
                    price_now = historical_data[1].get('price')

                    if price_then is not None and price_now is not None and price_then > 0:
                        change_pct = (price_now - price_then) / price_then
                        score = self._normalize_score(change_pct, center=0.0, scale=price_scale, steepness=2.0) # Steepness 2 for good sensitivity
                        price_momentum_scores[tf] = round(score, 3)
                        self.logger.debug(f"Price momentum for {token_address} ({tf}): change={change_pct:.2%}, score={score:.3f}")
                    else:
                        price_momentum_scores[tf] = None
                        self.logger.debug(f"Insufficient price data for {token_address} ({tf}) to calculate momentum (now: {price_now}, then: {price_then}).")
                elif historical_data and len(historical_data) == 1:
                    # Only one data point, cannot calculate change
                    price_momentum_scores[tf] = 0.5 # Neutral score
                    self.logger.debug(f"Only one price data point for {token_address} ({tf}), cannot calculate momentum. Setting neutral score.")
                else:
                    price_momentum_scores[tf] = None
                    self.logger.warning(f"Could not fetch sufficient historical price data for {token_address} ({tf}). Response: {historical_data}")
            except Exception as e:
                self.logger.error(f"Error calculating price momentum for {token_address} ({tf}): {e}", exc_info=True)
                price_momentum_scores[tf] = None
        
        return price_momentum_scores

    async def _get_volume_momentum(self, token_address: str, timeframes: List[str]) -> Dict[str, Optional[float]]:
        """
        Calculate trading volume momentum.
        Uses JupiterAPI for historical volume data.
        """
        if not self.jupiter_api:
            self.logger.warning(f"JupiterAPI not available, cannot calculate volume momentum for {token_address}.")
            return {tf: None for tf in timeframes}

        self.logger.debug(f"Calculating volume momentum for {token_address} over {timeframes}")
        volume_momentum_scores = {}
        
        volume_scale = self.normalization_params.get("volume_change_scale", 1.0) # Default to 100% (or 1.0x) scale

        for tf in timeframes:
            try:
                # Similar to price, fetch 2 data points for volume
                # Placeholder returns data sorted by timestamp (ascending).
                historical_data = await self.jupiter_api.get_historical_volume(
                    token_mint=token_address,
                    timeframe=tf,
                    limit=2 
                )

                if historical_data and len(historical_data) == 2:
                    # Data is sorted [oldest, newest]
                    volume_then = historical_data[0].get('volume')
                    volume_now = historical_data[1].get('volume')

                    if volume_then is not None and volume_now is not None and volume_then > 0: # volume_then > 0 to avoid division by zero
                        # For volume, a common metric is ratio or % change.
                        # Ratio: volume_now / volume_then. A ratio of 1 is no change.
                        # Score could be based on (ratio - 1). So, if ratio is 2 (100% increase), value is 1.
                        # If ratio is 0.5 (50% decrease), value is -0.5.
                        change_factor = (volume_now - volume_then) / volume_then
                        score = self._normalize_score(change_factor, center=0.0, scale=volume_scale, steepness=1.5) # Steepness 1.5
                        volume_momentum_scores[tf] = round(score, 3)
                        self.logger.debug(f"Volume momentum for {token_address} ({tf}): change_factor={change_factor:.2f}, score={score:.3f}")
                    else:
                        volume_momentum_scores[tf] = None
                        self.logger.debug(f"Insufficient volume data for {token_address} ({tf}) to calculate momentum (now: {volume_now}, then: {volume_then}).")
                elif historical_data and len(historical_data) == 1:
                    volume_momentum_scores[tf] = 0.5 # Neutral score
                    self.logger.debug(f"Only one volume data point for {token_address} ({tf}), cannot calculate momentum. Setting neutral score.")
                else:
                    volume_momentum_scores[tf] = None
                    self.logger.warning(f"Could not fetch sufficient historical volume data for {token_address} ({tf}). Response: {historical_data}")
            except Exception as e:
                self.logger.error(f"Error calculating volume momentum for {token_address} ({tf}): {e}", exc_info=True)
                volume_momentum_scores[tf] = None
        
        return volume_momentum_scores

    async def _get_holder_growth_momentum(self, token_address: str, timeframes: List[str]) -> Dict[str, Optional[float]]:
        """
        Calculate holder growth momentum for different timeframes.
        Uses HeliusAPI to provide historical and current holder counts.
        Note: Relies on placeholder methods in HeliusAPI.
        """
        if not self.helius_api:
            self.logger.warning(f"HeliusAPI not available, cannot calculate holder growth momentum for {token_address}.")
            return {tf: None for tf in timeframes}

        self.logger.debug(f"Calculating holder growth momentum for {token_address} over {timeframes}")
        holder_growth_scores: Dict[str, Optional[float]] = {}
        
        growth_scale = self.normalization_params.get("holder_growth_scale", 0.1) # Default to 10% scale

        try:
            current_holders = await self.helius_api.get_current_holder_count(token_address)
            if current_holders is None:
                self.logger.warning(f"Could not fetch current holder count for {token_address}. Cannot calculate holder growth.")
                return {tf: None for tf in timeframes}
            
            # Get historical counts for the start of each timeframe
            # The placeholder get_historical_holder_counts is designed to give counts *at the start* of the timeframe.
            historical_counts = await self.helius_api.get_historical_holder_counts(token_address, timeframes)

            for tf in timeframes:
                holders_then = historical_counts.get(tf)

                if holders_then is not None and current_holders is not None and holders_then > 0:
                    # Growth rate = (current - past) / past
                    growth_rate = (current_holders - holders_then) / holders_then
                    score = self._normalize_score(growth_rate, center=0.0, scale=growth_scale, steepness=2.0)
                    holder_growth_scores[tf] = round(score, 3)
                    self.logger.debug(f"Holder growth for {token_address} ({tf}): then={holders_then}, now={current_holders}, growth={growth_rate:.2%}, score={score:.3f}")
                elif holders_then == 0 and current_holders > 0: # Grew from zero holders
                    holder_growth_scores[tf] = 1.0 # Max score if grew from 0 to some positive number
                    self.logger.debug(f"Holder growth for {token_address} ({tf}): then=0, now={current_holders}, score=1.0 (grew from zero)")
                elif holders_then is not None and current_holders is not None and holders_then == current_holders: # No change
                    holder_growth_scores[tf] = 0.5 # Neutral score for no change
                else:
                    holder_growth_scores[tf] = None
                    self.logger.debug(f"Insufficient holder data for {token_address} ({tf}) to calculate growth (now: {current_holders}, then: {holders_then}).")
        
        except Exception as e:
            self.logger.error(f"Error calculating holder growth momentum for {token_address}: {e}", exc_info=True)
            for tf_err in timeframes: # Ensure all timeframes are in dict if an early error occurs
                if tf_err not in holder_growth_scores:
                    holder_growth_scores[tf_err] = None
            
        return holder_growth_scores

    async def _calculate_transaction_velocity(self, token_address: str) -> Optional[float]:
        """
        Calculate a score for transaction velocity based on recent transaction count.
        Uses HeliusAPI to get transaction counts.
        Note: Relies on placeholder method in HeliusAPI.
        """
        if not self.helius_api:
            self.logger.warning(f"HeliusAPI not available, cannot calculate transaction velocity for {token_address}.")
            return None

        self.logger.debug(f"Calculating transaction velocity for {token_address}")
        
        lookback_seconds = self.tx_velocity_config.get("lookback_seconds", 3600)
        # The scale for _normalize_score here should represent the typical range of transaction counts
        # for the lookback_seconds period. If lookback is 1hr, and we expect 0-200 tx/hr to map to 0-1 score,
        # then scale parameter in _normalize_score might be max_expected_tx_count / 2.
        # Or, we can define a max expected count and normalize based on that.
        # Let's use the configured `tx_velocity_scale` which represents the value at which score is ~0.84 (if steepness=1, center=0)
        # or where a significant part of the 0-1 range is covered.
        # For raw counts, center should be 0 for normalization, and scale is the configured `tx_velocity_scale`.
        # A better approach might be to normalize against a max expected value. 
        # Let scale be `min_tx_count_for_max_score / 2` if center is `min_tx_count_for_max_score / 2`.
        # Let's use the configured scale directly, with center = 0 for raw positive counts like this.

        tx_count_scale = self.normalization_params.get("tx_velocity_scale", 100)
        # For a raw count, we want 0 count to be 0 score, and higher counts to be higher scores.
        # So, center for normalization should be 0. `tx_count_scale` would be the value giving a highish score.
        # A simpler normalization for raw positive counts: value / max_expected_value, then clamp.
        # Or use _normalize_score with center=0 and an appropriate scale.
        # If `tx_count_scale` is e.g. 100, then 100 txns will give a score of atan(1)/pi + 0.5 = 0.25 + 0.5 = 0.75 (if steepness=1)

        try:
            tx_count = await self.helius_api.get_transaction_count_for_token(token_address, lookback_seconds)

            if tx_count is not None:
                # Normalize the transaction count. Center is 0 for raw count.
                # `tx_count_scale` is the point where score is significantly high (e.g. 0.75-0.84 for steepness 1-2)
                score = self._normalize_score(float(tx_count), center=0.0, scale=tx_count_scale, steepness=1.0)
                self.logger.debug(f"Transaction velocity for {token_address} ({lookback_seconds}s): count={tx_count}, scale={tx_count_scale}, score={score:.3f}")
                return round(score, 3)
            else:
                self.logger.warning(f"Could not fetch transaction count for {token_address}. Cannot calculate velocity.")
                return None
        except Exception as e:
            self.logger.error(f"Error calculating transaction velocity for {token_address}: {e}", exc_info=True)
            return None

    async def _calculate_net_flow(self, token_address: str) -> Optional[float]:
        """
        Calculate a score for net token flow (e.g., CEX inflow/outflow or DEX net buys).
        PLACEHOLDER: This is a complex metric requiring significant data processing.
        Currently returns a neutral score or None.
        """
        if not self.helius_api or not self.jupiter_api: # Might need both or other specialized data
            self.logger.warning(f"APIs not available, cannot calculate net flow for {token_address}.")
            return None

        self.logger.debug(f"Calculating net flow for {token_address} (Placeholder)")
        
        # lookback_seconds = self.net_flow_config.get("lookback_seconds", 3600)
        # net_flow_scale = self.normalization_params.get("net_flow_scale", 0.5)

        # Actual implementation would involve:
        # 1. Fetching transactions for the token (e.g., via Helius).
        # 2. Identifying transaction types (buys, sells, transfers to/from known CEX wallets).
        # 3. Aggregating net volume (e.g., (buy_volume - sell_volume) / total_volume, or net CEX inflow).
        # 4. Normalizing this value to a -1 to +1 range, then to a 0-1 score.
        #    A positive net flow (more buying/inflow) would be > 0.5 score.
        #    A negative net flow (more selling/outflow) would be < 0.5 score.

        # For now, returning a neutral score as it's not implemented.
        self.logger.info(f"Net flow calculation for {token_address} is a placeholder and not implemented. Returning neutral score.")
        return 0.5 # Neutral score


if __name__ == '__main__':
    # Example Usage (requires setting up mock APIs or actual instances)
    # This is for testing the MomentumAnalyzer independently.
    
    logging.basicConfig(level=logging.DEBUG)
    logger = logging.getLogger(__name__)

    # Create a dummy config.yaml for testing
    dummy_config_content = {
        "momentum_analysis": {
            "enabled": True,
            "timeframes": ["1h", "24h", "7d"],
            "weights": {
                "price_momentum": 0.4,
                "volume_momentum": 0.3,
                "holder_growth": 0.2,
                "transaction_velocity": 0.05, # Not implemented yet
                "net_flow": 0.05 # Not implemented yet
            },
            "cache_dir": "./cache/momentum_test"
        }
        # Add other necessary configs if Helius/Jupiter/RPC need them from main config
    }
    
    dummy_config_path = "dummy_config_momentum.yaml"
    with open(dummy_config_path, 'w') as f:
        yaml.dump(dummy_config_content, f)

    # Mock API classes (replace with actual or more sophisticated mocks)
    class MockAPI:
        async def get_historical_prices(self, token, timeframe, limit):
            logger.info(f"MockAPI: get_historical_prices called for {token} ({timeframe})")
            # Simulate some price data
            if timeframe == "1h": return [{"price": 1.05}, {"price": 1.0}] 
            if timeframe == "24h": return [{"price": 1.10}, {"price": 1.0}]
            if timeframe == "7d": return [{"price": 1.20}, {"price": 1.0}]
            return []
            
        async def get_historical_volume(self, token, timeframe): # Fictional method
            logger.info(f"MockAPI: get_historical_volume called for {token} ({timeframe})")
            return {"current_volume": 150000, "previous_volume": 100000} # Example data

    class MockRPC:
        def get_token_largest_accounts(self, token_address): # Example, may not be directly used by momentum
            logger.info(f"MockRPC: get_token_largest_accounts for {token_address}")
            return [{"totalSupply": 1000000}]


    async def main_test():
        logger.info("Starting MomentumAnalyzer test...")
        
        mock_helius = MockAPI() # Assuming Helius might be used for holder data later
        mock_jupiter = MockAPI() 
        mock_rpc = MockRPC()
        
        analyzer = MomentumAnalyzer(
            helius_api=mock_helius,
            jupiter_api=mock_jupiter,
            rpc=mock_rpc,
            config_path=dummy_config_path,
            cache_dir=dummy_config_content["momentum_analysis"]["cache_dir"]
        )
        
        # Test with a dummy token address
        token_address = "So11111111111111111111111111111111111111112" # SOL address for example
        
        if analyzer.config.get("enabled"):
            results = await analyzer.analyze_token_momentum(token_address)
            logger.info(f"Momentum Analysis Results for {token_address}:")
            import json
            logger.info(json.dumps(results, indent=2))
            
            # Specific checks
            if "price_momentum" in results and "1h" in results["price_momentum"]:
                 logger.info(f"1h Price Momentum Score: {results['price_momentum']['1h']}")
            if "overall_momentum_score" in results:
                logger.info(f"Overall Momentum Score: {results['overall_momentum_score']}")
        else:
            logger.info("Momentum analysis is disabled via config, skipping analysis.")

        # Clean up dummy config
        Path(dummy_config_path).unlink(missing_ok=True)
        # Clean up cache if needed (recursively remove self.cache_dir)

    if __name__ == '__main__':
        asyncio.run(main_test()) 