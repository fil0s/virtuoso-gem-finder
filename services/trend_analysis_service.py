import logging
from typing import Dict, Any, Optional

# Assuming DexScreenerAPI is importable, e.g., from services.dexscreener_api
# For now, using a placeholder to allow linting and basic structure.
try:
    from services.dexscreener_api import DexScreenerAPI
except ImportError:
    class DexScreenerAPI: # Basic Placeholder
        def get_pair_details(self, pair_address: str) -> Optional[Dict]:
            # Mock response for testing structure
            if pair_address == "testpair123":
                return {
                    "volume": {"h1": 1000, "h6": 5000, "h24": 20000},
                    "txns": {
                        "h1": {"buys": 10, "sells": 5},
                        "h6": {"buys": 60, "sells": 30},
                        "h24": {"buys": 200, "sells": 100}
                    }
                }
            return None

from services.logger_setup import LoggerSetup

class TrendAnalysisService:
    def __init__(self, dexscreener_api: DexScreenerAPI, config: Optional[Dict] = None, logger_setup: Optional[LoggerSetup] = None):
        self.dex_screener = dexscreener_api
        self.config = config or {}
        if logger_setup:
            self.logger = logger_setup.get_logger('TrendAnalysisService')
        else:
            self.logger = LoggerSetup('TrendAnalysisService').logger
        self.logger.info("TrendAnalysisService initialized.")

    def analyze_volume_trend(self, pair_address: str) -> Dict[str, Any]:
        """
        Analyze volume trends over multiple timeframes to detect increasing interest.
        
        Args:
            pair_address: DEX pair address to analyze
            
        Returns:
            Dictionary with trend analysis results
        """
        try:
            pair_details = self.dex_screener.get_pair_details(pair_address)
            if not pair_details or "volume" not in pair_details:
                self.logger.warning(f"No pair details or volume data for {pair_address} in analyze_volume_trend.")
                return {"trend": "unknown", "trend_score": 0.0, "acceleration_percent": 0.0, "hourly_data": {}}
                
            volume_data = pair_details.get("volume", {})
            h1_volume = float(volume_data.get("h1", 0))
            h6_volume = float(volume_data.get("h6", 0))
            h24_volume = float(volume_data.get("h24", 0))
            
            avg_h1 = h1_volume
            # Ensure h6_volume >= h1_volume for sensible avg_h1_to_h6, otherwise 0 to prevent negative hourly averages
            avg_h1_to_h6 = (h6_volume - h1_volume) / 5.0 if h6_volume > h1_volume else 0.0
            # Ensure h24_volume >= h6_volume for sensible avg_h6_to_h24
            avg_h6_to_h24 = (h24_volume - h6_volume) / 18.0 if h24_volume > h6_volume else 0.0
            
            trend = "unknown"
            trend_score = 0.1 # Default low score for unknown/insufficient

            if h24_volume == 0 and h6_volume == 0 and h1_volume == 0:
                trend = "no_volume"
                trend_score = 0.0
            elif avg_h1 > 0 and avg_h1 >= avg_h1_to_h6 and avg_h1_to_h6 >= avg_h6_to_h24:
                if avg_h6_to_h24 > 0: # All periods have volume and it's accelerating
                    trend = "strongly_increasing"
                    trend_score = 1.0
                elif avg_h1_to_h6 > 0: # Accelerating more recently
                    trend = "increasing"
                    trend_score = 0.8
                else: # Only last hour has volume, or it's increasing from zero
                    trend = "recently_increasing"
                    trend_score = 0.6
            elif avg_h1 > avg_h1_to_h6 and avg_h1_to_h6 > 0: # Increasing recently
                 trend = "increasing"
                 trend_score = 0.7
            elif avg_h1 > 0 and avg_h1 > avg_h6_to_h24: # Recently increasing vs older average
                 trend = "recently_increasing"
                 trend_score = 0.5 
            elif h24_volume > 0 and abs(avg_h1 - (h24_volume/24.0)) < (h24_volume/24.0 * 0.2): # Relatively stable
                 trend = "stable"
                 trend_score = 0.4
            elif h1_volume < avg_h1_to_h6 or h1_volume < avg_h6_to_h24: # Decreasing
                if h1_volume < avg_h1_to_h6 and avg_h1_to_h6 < avg_h6_to_h24:
                    trend = "strongly_decreasing"
                    trend_score = 0.1
                else:
                    trend = "decreasing"
                    trend_score = 0.2
            elif h24_volume > 0: # Has some 24h volume, but trend unclear or flat/low activity recently
                trend = "stable_low_activity_or_unknown"
                trend_score = 0.3
            else:
                trend = "insufficient_data"
                trend_score = 0.05

            acceleration = 0.0
            if avg_h1_to_h6 > 0: # Compare last hour to previous 5 hours average
                acceleration = ((avg_h1 / avg_h1_to_h6) - 1.0) * 100.0
            elif avg_h1 > 0 and avg_h6_to_h24 > 0: # Compare last hour to older average if intermediate is zero
                 acceleration = ((avg_h1 / avg_h6_to_h24) - 1.0) * 100.0
            elif avg_h1 > 0: # If only H1 has volume
                acceleration = 100.0 # Signifies growth from zero
                
            return {
                "trend": trend,
                "trend_score": round(trend_score, 3),
                "acceleration_percent": round(acceleration, 2),
                "hourly_data": {
                    "h1_avg_vol": round(avg_h1, 2),
                    "h1_to_h6_avg_vol": round(avg_h1_to_h6, 2),
                    "h6_to_h24_avg_vol": round(avg_h6_to_h24, 2)
                }
            }
        except Exception as e:
            self.logger.error(f"Error analyzing volume trend for {pair_address}: {e}", exc_info=True)
            return {"trend": "error", "trend_score": 0.0, "acceleration_percent": 0.0, "hourly_data": {}}

    def analyze_transaction_trend(self, pair_data: Dict) -> Dict[str, Any]:
        """
        Analyze transaction count trends over time to detect increasing activity.
        
        Args:
            pair_data: DEX pair data from DexScreener (contains 'txns' field)
            
        Returns:
            Dictionary with transaction trend analysis results
        """
        try:
            txns = pair_data.get('txns', {})
            if not txns:
                self.logger.warning(f"No transaction data in pair_data for analyze_transaction_trend. Pair: {pair_data.get('pairAddress')}")
                return {"trend": "unknown", "trend_score": 0.0, "hourly_data": {}}

            h1_txns_data = txns.get('h1', {})
            h6_txns_data = txns.get('h6', {})
            h24_txns_data = txns.get('h24', {})

            h1_total_txns = h1_txns_data.get('buys', 0) + h1_txns_data.get('sells', 0)
            h6_total_txns = h6_txns_data.get('buys', 0) + h6_txns_data.get('sells', 0)
            h24_total_txns = h24_txns_data.get('buys', 0) + h24_txns_data.get('sells', 0)
            
            avg_h1_txns = float(h1_total_txns)
            avg_h1_to_h6_txns = (h6_total_txns - h1_total_txns) / 5.0 if h6_total_txns > h1_total_txns else 0.0
            avg_h6_to_h24_txns = (h24_total_txns - h6_total_txns) / 18.0 if h24_total_txns > h6_total_txns else 0.0
            
            trend = "unknown"
            trend_score = 0.1 # Default low score

            if h24_total_txns == 0 and h6_total_txns == 0 and h1_total_txns == 0:
                trend = "no_transactions"
                trend_score = 0.0
            elif avg_h1_txns > 0 and avg_h1_txns >= avg_h1_to_h6_txns and avg_h1_to_h6_txns >= avg_h6_to_h24_txns:
                if avg_h6_to_h24_txns > 0:
                    trend = "strongly_increasing"
                    trend_score = 1.0
                elif avg_h1_to_h6_txns > 0:
                    trend = "increasing"
                    trend_score = 0.8
                else:
                    trend = "recently_increasing"
                    trend_score = 0.6
            elif avg_h1_txns > avg_h1_to_h6_txns and avg_h1_to_h6_txns > 0:
                 trend = "increasing"
                 trend_score = 0.7
            elif avg_h1_txns > 0 and avg_h1_txns > avg_h6_to_h24_txns:
                 trend = "recently_increasing"
                 trend_score = 0.5
            elif h24_total_txns > 0 and abs(avg_h1_txns - (h24_total_txns/24.0)) < (h24_total_txns/24.0 * 0.2):
                 trend = "stable"
                 trend_score = 0.4
            elif h1_total_txns < avg_h1_to_h6_txns or h1_total_txns < avg_h6_to_h24_txns:
                if h1_total_txns < avg_h1_to_h6_txns and avg_h1_to_h6_txns < avg_h6_to_h24_txns:
                    trend = "strongly_decreasing"
                    trend_score = 0.1
                else:
                    trend = "decreasing"
                    trend_score = 0.2
            elif h24_total_txns > 0:
                trend = "stable_low_activity_or_unknown"
                trend_score = 0.3
            else:
                trend = "insufficient_data"
                trend_score = 0.05
                
            return {
                "trend": trend,
                "trend_score": round(trend_score, 3),
                "hourly_data": {
                    "h1_avg_txns": round(avg_h1_txns, 2),
                    "h1_to_h6_avg_txns": round(avg_h1_to_h6_txns, 2),
                    "h6_to_h24_avg_txns": round(avg_h6_to_h24_txns, 2)
                }
            }
        except Exception as e:
            self.logger.error(f"Error analyzing transaction trend for pair {pair_data.get('pairAddress')}: {e}", exc_info=True)
            return {"trend": "error", "trend_score": 0.0, "hourly_data": {}} 