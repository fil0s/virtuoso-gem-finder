import logging
import time
from typing import Dict, List, Any, Optional

from services.logger_setup import LoggerSetup
# Assuming TrendAnalysisService and JupiterAPI will be injected or accessible
# For now, define placeholders for imports if they come from files not yet created/moved.
try:
    from services.trend_analysis_service import TrendAnalysisService
except ImportError:
    class TrendAnalysisService: # Placeholder
        def analyze_volume_trend(self, pair_address: str) -> dict:
            return {"trend": "unknown", "trend_score": 0.0, "acceleration_percent": 0.0}
        def analyze_transaction_trend(self, pair: dict) -> dict:
            return {"trend": "unknown", "trend_score": 0.0}

try:
    from jupiter_connector import JupiterAPI # If jupiter_connector.py is top-level
except ImportError:
    try:
        from services.jupiter_api import JupiterAPI # If moved to services/
    except ImportError:
        class JupiterAPI: # Placeholder
            async def get_token_price_usd(self, token_address: str) -> Optional[float]:
                return None
            async def get_token_list(self) -> list:
                return []
            async def close(self):
                pass

# === Dexscreener Filters (moved from solgem.py) ===
FILTERS_DATA = [
    {
        "name": "High Risk",
        "market_cap_usd": {"max": 500000},
        "pair_age_hours": {"max": 48},
        "tx_24h": {"min": 1000},
        "volume_24h_usd": {"min": 1000000},
        "price_change_1h_percent": {"min": 10, "max": 20},
        "price_change_6h_percent": {"exact": 0},
        "price_change_24h_percent": {"exact": 0}
    },
    {
        "name": "Medium Risk",
        "market_cap_usd": {"min": 1000000, "max": 5000000},
        "pair_age_hours": {"min": 72},
        "tx_24h": {"min": 1500},
        "volume_24h_usd": {"min": 1500000},
        "price_change_1h_percent": {"min": 40},
        "price_change_6h_percent": {"exact": 0},
        "price_change_24h_percent": {"exact": 0}
    },
    {
        "name": "Low Risk",
        "market_cap_usd": {"min": 5000000, "max": 10000000},
        "pair_age_hours": {"min": 100},
        "tx_24h": {"min": 2000},
        "volume_24h_usd": {"min": 3000000},
        "price_change_1h_percent": {"min": 20},
        "price_change_6h_percent": {"min": 10, "max": 20},
        "price_change_24h_percent": {"min": 10, "max": 30}
    },
    {
        "name": "Minimum Risk",
        "market_cap_usd": {"min": 20000000},
        "pair_age_hours": {"min": 200},
        "tx_24h": {"min": 3000},
        "volume_24h_usd": {"min": 5000000},
        "price_change_1h_percent": {"min": 10},
        "price_change_6h_percent": {"exact": 0},
        "price_change_24h_percent": {"min": 10}
    }
]

def _check_condition(value: Optional[float], condition: Dict[str, float]) -> bool:
    """Helper to check a value against a condition dictionary (min, max, exact)."""
    if value is None:
        return False
    if "min" in condition and value < condition["min"]:
        return False
    if "max" in condition and value > condition["max"]:
        return False
    if "exact" in condition and value != condition["exact"]:
        return False
    return True

class FilteringService:
    def __init__(self, 
                 config: Dict,
                 trend_analyzer: TrendAnalysisService, 
                 jupiter_api: Optional[JupiterAPI] = None, # Jupiter API is optional for some filtering logic
                 logger_setup: Optional[LoggerSetup] = None):
        self.config = config
        self.trend_analyzer = trend_analyzer
        self.jupiter_api = jupiter_api # Store for _calculate_price_changes_with_jupiter
        self._jupiter_token_list_cache: Optional[Dict[str, Any]] = None # Cache for Jupiter token list

        if logger_setup:
            self.logger = logger_setup.get_logger('FilteringService')
        else:
            self.logger = LoggerSetup('FilteringService').logger
        self.logger.info("FilteringService initialized.")

    # _calculate_price_changes_with_jupiter needs to be part of this class or accessible to it.
    # It also needs an event loop if JupiterAPI calls are async.
    # For now, assuming it's a method here and VirtuosoGemFinder's loop might be passed or handled.
    async def _get_jupiter_price_async(self, token_address: str) -> Optional[float]:
        if not self.jupiter_api:
            return None
        try:
            price = await self.jupiter_api.get_token_price_usd(token_address)
            if price is not None:
                self.logger.debug(f"Got Jupiter price for {token_address}: ${price:.6f}")
            else:
                self.logger.debug(f"No Jupiter price available for {token_address}")
            return price
        except Exception as e:
            self.logger.error(f"Error getting Jupiter price for {token_address}: {e}", exc_info=True)
            return None

    async def _calculate_price_changes_with_jupiter_async(self, pair: Dict, token_address: str) -> Dict[str, Optional[float]]:
        dex_price_changes = {
            'h1': pair.get('priceChange', {}).get('h1'),
            'h6': pair.get('priceChange', {}).get('h6'),
            'h24': pair.get('priceChange', {}).get('h24')
        }
        try:
            current_price = await self._get_jupiter_price_async(token_address)
            if current_price is None:
                return dex_price_changes
            
            price_change_data = pair.get('priceChange', {})
            
            h1_change_pct = price_change_data.get('h1', 0.0)
            price_1h_ago = current_price / (1 + h1_change_pct / 100.0) if h1_change_pct != -100.0 else 0.0
            
            h6_change_pct = price_change_data.get('h6', 0.0)
            price_6h_ago = current_price / (1 + h6_change_pct / 100.0) if h6_change_pct != -100.0 else 0.0
            
            h24_change_pct = price_change_data.get('h24', 0.0)
            price_24h_ago = current_price / (1 + h24_change_pct / 100.0) if h24_change_pct != -100.0 else 0.0
            
            updated_h1 = ((current_price / price_1h_ago) - 1.0) * 100.0 if price_1h_ago > 0 else None
            updated_h6 = ((current_price / price_6h_ago) - 1.0) * 100.0 if price_6h_ago > 0 else None
            updated_h24 = ((current_price / price_24h_ago) - 1.0) * 100.0 if price_24h_ago > 0 else None
            
            return {'h1': updated_h1, 'h6': updated_h6, 'h24': updated_h24}
            
        except Exception as e:
            self.logger.error(f"Error calculating Jupiter price changes for {token_address}: {e}", exc_info=True)
            return dex_price_changes

    async def is_potential_gem(self, pair: Dict) -> bool:
        try:
            liquidity = float(pair.get('liquidity', {}).get('usd', 0))
            market_cap = float(pair.get('marketCap', 0))
            token_address = pair.get('baseToken', {}).get('address')
            pair_address = pair.get('pairAddress')
            
            base_criteria = (
                self.config.get('min_liquidity', 10000) <= liquidity <= self.config.get('max_liquidity', 100000) and # Adjusted default max_liquidity
                market_cap <= self.config.get('max_market_cap', 2000000) and # Adjusted default
                pair.get('pairCreatedAt', 0) > (time.time() - (self.config.get('token_filters',{}).get('max_pair_age_hours', 24) * 3600)) # Use configurable max age
            )
            
            if not base_criteria:
                return False
                
            trend_filters_enabled = self.config.get('features', {}).get('enable_trend_analysis', False)
            if trend_filters_enabled and pair_address and self.trend_analyzer:
                volume_trend_data = self.trend_analyzer.analyze_volume_trend(pair_address)
                tx_trend_data = self.trend_analyzer.analyze_transaction_trend(pair)
                
                token_filters_config = self.config.get('token_filters', {})
                volume_trends_config = token_filters_config.get('volume_trends', {})
                tx_trends_config = token_filters_config.get('tx_trends', {})

                min_vol_score = volume_trends_config.get('min_trend_score', 0.5)
                min_vol_accel = volume_trends_config.get('min_acceleration', 50)
                min_tx_score = tx_trends_config.get('min_trend_score', 0.5)

                if volume_trend_data['trend_score'] < min_vol_score:
                    self.logger.debug(f"{pair_address} rejected: vol trend {volume_trend_data['trend_score']:.2f} < {min_vol_score}")
                    return False
                if volume_trend_data.get('acceleration_percent', 0) < min_vol_accel:
                    self.logger.debug(f"{pair_address} rejected: vol accel {volume_trend_data.get('acceleration_percent', 0):.2f}% < {min_vol_accel}% ")
                    return False
                if tx_trend_data['trend_score'] < min_tx_score:
                    self.logger.debug(f"{pair_address} rejected: tx trend {tx_trend_data['trend_score']:.2f} < {min_tx_score}")
                    return False
                self.logger.debug(f"{pair_address} passed trend analysis.")

            if token_address and self.jupiter_api:
                updated_changes = await self._calculate_price_changes_with_jupiter_async(pair, token_address)
                for filter_set in FILTERS_DATA:
                    if 'price_change_1h_percent' in filter_set:
                        if _check_condition(updated_changes.get('h1'), filter_set['price_change_1h_percent']):
                            self.logger.debug(f"{token_address} meets Jupiter-enhanced price criteria for {filter_set['name']}")
                            return True # Passes if any advanced filter with Jupiter data matches
            
            # If Jupiter checks didn't make it pass, it relies on base_criteria (and trends if enabled)
            return True # If base_criteria passed and (either trends passed or were not enabled or no jupiter check triggered True)
            
        except (ValueError, TypeError) as e:
            self.logger.error(f"Error in is_potential_gem for pair {pair.get('pairAddress')}: {e}", exc_info=True)
            return False

    async def check_token_against_filter_set_async(self, dexscreener_pair_data: Dict[str, Any], 
                                             filter_criteria: Dict[str, Any],
                                             token_address: Optional[str] = None) -> bool:
        market_cap_usd = dexscreener_pair_data.get('fdv') 
        if 'market_cap_usd' in filter_criteria and not _check_condition(market_cap_usd, filter_criteria['market_cap_usd']):
            return False

        pair_created_at_ts_ms = dexscreener_pair_data.get('pairCreatedAt')
        pair_age_h = None
        if pair_created_at_ts_ms:
            pair_age_h = (time.time() - pair_created_at_ts_ms / 1000.0) / 3600.0
        if 'pair_age_hours' in filter_criteria and not _check_condition(pair_age_h, filter_criteria['pair_age_hours']):
            return False

        txns_h24_data = dexscreener_pair_data.get('txns', {}).get('h24', {})
        txns_24h_total = txns_h24_data.get('buys', 0) + txns_h24_data.get('sells', 0)
        if 'tx_24h' in filter_criteria and not _check_condition(float(txns_24h_total), filter_criteria['tx_24h']):
            return False

        volume_h24_usd = dexscreener_pair_data.get('volume', {}).get('h24')
        if 'volume_24h_usd' in filter_criteria and not _check_condition(volume_h24_usd, filter_criteria['volume_24h_usd']):
            return False

        jupiter_price_changes = None
        if token_address and self.jupiter_api:
             jupiter_price_changes = await self._calculate_price_changes_with_jupiter_async(dexscreener_pair_data, token_address)

        price_change_1h = jupiter_price_changes.get('h1') if jupiter_price_changes else dexscreener_pair_data.get('priceChange', {}).get('h1')
        price_change_6h = jupiter_price_changes.get('h6') if jupiter_price_changes else dexscreener_pair_data.get('priceChange', {}).get('h6')
        price_change_24h = jupiter_price_changes.get('h24') if jupiter_price_changes else dexscreener_pair_data.get('priceChange', {}).get('h24')

        if 'price_change_1h_percent' in filter_criteria and not _check_condition(price_change_1h, filter_criteria['price_change_1h_percent']):
            return False
        if 'price_change_6h_percent' in filter_criteria and not _check_condition(price_change_6h, filter_criteria['price_change_6h_percent']):
            return False
        if 'price_change_24h_percent' in filter_criteria and not _check_condition(price_change_24h, filter_criteria['price_change_24h_percent']):
            return False
            
        return True

    async def apply_dexscreener_filters_async(self, dexscreener_pair_data: Dict[str, Any], token_address: Optional[str] = None) -> List[str]:
        matching_risk_profiles = []
        if not dexscreener_pair_data:
            return matching_risk_profiles
            
        for filter_set in FILTERS_DATA:
            if await self.check_token_against_filter_set_async(dexscreener_pair_data, filter_set, token_address):
                matching_risk_profiles.append(filter_set["name"])
                
        return matching_risk_profiles 