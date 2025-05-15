import logging
import math
import statistics
import time
from dataclasses import dataclass, fields
from typing import Dict, List, Any, Optional

# Assuming TokenMetrics will be moved to a models file or importable from solgem
# For now, this will cause a lint error if TokenMetrics is not found.
# We will address TokenMetrics location later.
try:
    from solgem import TokenMetrics # Or from ..solgem if services is a package
except ImportError:
    # Define a placeholder if running this file standalone for testing, or if solgem is not in PYTHONPATH
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
        top_holders: List[Dict[str, Any]] # Simplified for placeholder
        is_mint_frozen: bool = False
        program_id: str = ""
        is_honeypot: bool = False
        contract_verified: bool = False
        buy_tax: float = 0.0
        sell_tax: float = 0.0
        risk_factors: List[str] = field(default_factory=list)
        volume_trend: str = "unknown"
        volume_acceleration: float = 0.0
        tx_count_trend: str = "unknown"


from services.logger_setup import LoggerSetup

@dataclass
class ScoreWeights:
    liquidity: float = 0.20
    market_cap: float = 0.15
    holders: float = 0.15
    volume: float = 0.15
    holder_distribution: float = 0.10
    supply_distribution: float = 0.10
    security: float = 0.08
    price_stability: float = 0.04
    age: float = 0.03
    # Added from existing GemScorer logic, ensure these are in config or defaults
    volume_trend: float = 0.0 # Placeholder, should be defined in config
    transaction_trend: float = 0.0 # Placeholder, should be defined in config


class GemScorer:
    def __init__(self, config: Dict, logger_setup: LoggerSetup = None): # Allow passing LoggerSetup for consistency
        self.config = config
        # Ensure score_weights from config are properly loaded into ScoreWeights object
        # The original GemScorer directly modified self.weights.security, which might be better handled
        # by ensuring the ScoreWeights dataclass is initialized correctly from the config's score_weights dict.
        
        raw_weights = config.get('score_weights', {})
        # Filter raw_weights to only include fields defined in ScoreWeights
        valid_weight_fields = {f.name for f in fields(ScoreWeights)}
        filtered_weights = {k: v for k, v in raw_weights.items() if k in valid_weight_fields}
        self.weights = ScoreWeights(**filtered_weights)

        if logger_setup:
            self.logger = logger_setup.get_logger('GemScorer')
        else:
            self.logger = LoggerSetup('GemScorer').logger # Fallback if not provided

        # This line was in original, if 'security' is a top-level config item for GemScorer, handle it.
        # Or ensure it's part of the score_weights structure. For now, assuming it's within score_weights.
        # self.weights.security = config.get('score_weights', {}).get('security', 15.0) 
        # The above is problematic because ScoreWeights defines security with a default.
        # If it's intended to be overridden from a different part of config, that needs clarity.
        # For now, we assume ScoreWeights is fully populated by config['score_weights'].

        # Initialize score cache
        self._score_cache: Dict[str, Dict[str, float]] = {}


    def _score_liquidity(self, liquidity: float) -> float:
        if liquidity <= 0:
            return 0.0
        
        min_liq_config = self.config.get('min_liquidity', 1) # Default to 1 to avoid log(0)
        max_liq_config = self.config.get('max_liquidity', 1000000)

        # Ensure min_liq_config is not zero for log
        min_liq_safe = max(min_liq_config, 1)
        
        log_liq = math.log10(max(liquidity, 1))
        min_log = math.log10(min_liq_safe)
        max_log = math.log10(max(max_liq_config, min_liq_safe + 1)) # Ensure max_log > min_log
        
        if max_log <= min_log: # Avoid division by zero or negative
            return 1.0 if log_liq >= min_log else 0.0

        score = (log_liq - min_log) / (max_log - min_log)
        return max(0.0, min(1.0, score))

    def _score_market_cap(self, mcap: float) -> float:
        max_mcap_config = self.config.get('max_market_cap', 1000000)
        if mcap <=0: # Handle non-positive mcap
            return 0.0
        if mcap > max_mcap_config:
            return 0.0
        # Preference for smaller caps, score decreases as mcap approaches max_mcap_config
        return 1.0 - (mcap / max_mcap_config) ** 0.5


    def _score_holders(self, holder_count: int) -> float:
        min_holders = self.config.get('min_holder_count', 10)
        max_holders = self.config.get('max_holder_count', 10000)
        
        if holder_count < min_holders:
            return 0.0
        # Original had a penalty for exceeding max_holders. Re-evaluating if that's desired.
        # For now, capping score at 1.0 if above min_holders.
        # A more nuanced approach might involve a gentle curve.
        if holder_count >= max_holders: # If it meets or exceeds a high threshold, give good score
             return 1.0
        
        # Linear scaling between min_holders and max_holders
        if max_holders <= min_holders: # Avoid division by zero
            return 1.0 if holder_count >= min_holders else 0.0

        score = (holder_count - min_holders) / (max_holders - min_holders)
        return max(0.0, min(1.0, score))


    def _score_holder_distribution(self, top_holders: List[Dict]) -> float:
        if not top_holders or len(top_holders) < 2:
            # If no data or only one holder, distribution is maximally concentrated (bad) or undefined.
            # Consider returning 0 or a low score.
            return 0.0 

        holdings = []
        for h_entry in top_holders:
            try:
                # Assuming structure like Solscan API where amount is directly accessible
                # or needs to be parsed if it's from a generic RPC source
                # Example assumes parsed info: h_entry['account']['data']['parsed']['info']['tokenAmount']['uiAmountString']
                # Or it might be h_entry['amount'] if already processed.
                # For placeholder from solgem.py, it was:
                # float(h['account']['data']['parsed']['info']['tokenAmount']['amount'])
                # This needs to be robust to the actual data structure of top_holders.
                # Let's assume top_holders provides a list of amounts directly or simple dicts like {'amount': float_value}
                if isinstance(h_entry, dict) and 'amount' in h_entry:
                    holdings.append(float(h_entry['amount']))
                elif isinstance(h_entry, (int, float)): # If it's just a list of numbers
                    holdings.append(float(h_entry))
                # Add more sophisticated parsing if needed based on actual top_holders structure
            except (TypeError, ValueError, KeyError) as e:
                self.logger.warning(f"Could not parse holding amount from entry: {h_entry}. Error: {e}")
                continue
        
        if not holdings or len(holdings) < 2 : # Need at least two holders to calculate Gini
             return 0.0 # Or a score indicating high concentration if only one effective holder found

        holdings.sort()
        
        n = len(holdings)
        sum_yi = sum(holdings)
        if sum_yi == 0: # Avoid division by zero if all holdings are zero
            return 1.0 # Perfect equality if all have zero (though practically means no holdings)

        # Corrected Gini calculation:
        # index_sum = sum((i + 1) * holdings[i] for i in range(n))
        # gini = (2 * index_sum) / (n * sum_yi) - (n + 1) / n
        # Alternate Gini: Mean absolute difference / (2 * mean)
        # Simpler way: sum of all absolute differences / (2 * n^2 * mean)
        
        # Using a common formula for Gini from sorted list:
        # ( Sum_i Sum_j |x_i - x_j| ) / ( 2 * n * Sum_i x_i )
        # Or from sorted list: 1 - (2 / (n-1)) * Sum_{i=1 to n-1} (S_i / S_T - i/n) where S_i is cumulated sum
        # Let's use a well-known formula for discrete samples:
        # G = (Sum_i Sum_j |y_i - y_j|) / (2 * n * Sum_k y_k)
        
        # A more direct Gini from sorted data:
        # B = sum( (n + 1 - 2*i) * y_i for i=1 to n ) / (n * sum(y_i) )
        # Gini = 1 - B  -- this is Brown's formula, but Gini is usually 1-B (if B is Gini coefficient of equality)
        # Or G = sum (2i - n - 1)x_i / (n^2 * mean)
        
        # Using the formula based on rank and value (from Wikipedia/common sources):
        # G = [ (n+1) - 2 * ( sum( (n+1-i)*y_i ) / sum(y_i) ) ] / n
        # where y_i is sorted.
        
        numerator_sum = sum((i + 1) * val for i, val in enumerate(holdings)) # sum(rank_i * value_i)
        gini_intermediate = (2 * numerator_sum) / (n * sum_yi) - ((n + 1) / n)
        
        # Gini coefficient typically ranges from 0 (perfect equality) to 1 (perfect inequality).
        # We want to score higher for more equality (lower Gini).
        score = 1.0 - gini_intermediate 
        return max(0.0, min(1.0, score))


    def _score_age(self, creation_time: int) -> float:
        if creation_time <= 0: return 0.0 # Invalid creation time
        age_seconds = time.time() - creation_time
        age_hours = age_seconds / 3600
        
        if age_hours < 1: # Less than 1 hour old
            return age_hours # Score from 0 to 1 linearly for the first hour
        elif age_hours < 24:  # Between 1 and 24 hours
            return 0.3 + (age_hours / 24) * 0.3 # maps 1-24 hours to 0.3-0.6
        elif age_hours < 24 * 7: # Between 1 day and 1 week
            return 0.6 + ((age_hours - 24) / (24*6)) * 0.2 # maps 1-7 days to 0.6-0.8
        else: # Older than 1 week
            # Logarithmic scaling for older tokens, reaching close to 1 for very old tokens
            # Max score for e.g. 30 days old
            return min(1.0, 0.8 + math.log10(max(1, (age_hours / (24*7)))) * 0.2)


    def _score_supply_distribution(self, whale_holdings: Dict[str, float]) -> float:
        if not whale_holdings:
            return 1.0
            
        whale_concentration = sum(whale_holdings.values()) # Sum of percentages held by whales
        
        if whale_concentration >= 0.5: # 50% or more held by identified whales
            return 0.0
        elif whale_concentration >= 0.3: # 30-50%
            return 0.5 * (1.0 - (whale_concentration - 0.3) / 0.2) # Score from 0.5 down to 0
        elif whale_concentration >= 0.1: # 10-30%
            return 1.0 - (whale_concentration / 0.3) * 0.5 # Score from 1.0 down to 0.5
        else: # Less than 10%
            return 1.0 # Low whale concentration is good


    def _score_price_stability(self, historical_data: Optional[List[Dict]]) -> float:
        if not historical_data or len(historical_data) < 2:
            return 0.5  # Neutral if not enough data
            
        prices = [item['price'] for item in historical_data if isinstance(item, dict) and 'price' in item]
        if len(prices) < 2:
            return 0.5
            
        # Calculate log returns
        log_returns = []
        for i in range(1, len(prices)):
            if prices[i-1] > 0 and prices[i] > 0: # Avoid log(0) or division by zero
                log_returns.append(math.log(prices[i] / prices[i-1]))
        
        if not log_returns:
            return 0.3 # Low score if no valid returns (e.g. all zero prices or one price)

        volatility = statistics.stdev(log_returns) if len(log_returns) > 1 else 0.0
        
        # Normalize volatility: Higher volatility means lower score.
        # Using exponential decay. `volatility_scale` determines how quickly score drops.
        # A volatility of 0.1 (10% stdev of log returns) might be a typical benchmark.
        volatility_scale = self.config.get('price_stability_volatility_scale', 0.1) 
        score = math.exp(-volatility / volatility_scale) 
        return max(0.0, min(1.0, score))

    def _score_smart_contract(self, metrics: TokenMetrics) -> float:
        # This method was not in the provided GemScorer snippet,
        # but was referenced by calculate_score. Adding a placeholder.
        # Actual implementation would check metrics.is_mint_frozen, metrics.program_id etc.
        score = 0.5 # Neutral placeholder
        if metrics.is_mint_frozen:
            score += 0.25
        if metrics.program_id == "TokenkegQfeZyiNwAJbNbGKPFXCWuBvf9Ss623VQ5DA": # Standard SPL Token program
             score += 0.25
        return max(0.0, min(1.0, score))


    def _score_security(self, metrics: TokenMetrics) -> float:
        base_score = 1.0 # Start with perfect score
        
        if metrics.is_honeypot:
            return 0.0 # Honeypot is critical
        
        # Penalty for not being contract verified
        if not metrics.contract_verified:
            base_score *= 0.7 # Significant penalty
        
        # Penalties for taxes
        total_tax = (metrics.buy_tax or 0.0) + (metrics.sell_tax or 0.0)
        if total_tax > 0.20: # More than 20% total tax
            base_score *= 0.5
        elif total_tax > 0.10: # More than 10% total tax
            base_score *= 0.75
        elif total_tax > 0.05: # More than 5% total tax
            base_score *= 0.9
            
        # Penalties for specific risk factors listed
        # These factors might come from an external rug check API or manual analysis
        risk_factor_penalties = self.config.get('security_risk_factor_penalties', {
            'MINT_AUTHORITY_ENABLED': 0.5, # Example: if mint authority still enabled
            'FREEZE_AUTHORITY_ENABLED': 0.8, # Example: if freeze authority enabled
            'HIGHLY_CONCENTRATED_LP': 0.7, # Example
            'SUSPICIOUS_CODE_DETECTED': 0.3
        })

        for risk in metrics.risk_factors:
            if risk in risk_factor_penalties:
                base_score *= risk_factor_penalties[risk]
        
        return max(0.0, min(1.0, base_score))

    def _score_volume(self, volume_24h: float, mcap: float) -> float:
        if mcap <= 0:
            return 0.0
        if volume_24h <=0:
             return 0.0
            
        volume_to_mcap_ratio = volume_24h / mcap
        
        # Sigmoid-like function or steps
        if volume_to_mcap_ratio >= 1.0:  # Ratio >= 100%
            return 1.0
        elif volume_to_mcap_ratio >= 0.5: # Ratio >= 50%
            return 0.8 + (volume_to_mcap_ratio - 0.5) * 0.4 # 0.8 to 1.0
        elif volume_to_mcap_ratio >= 0.2: # Ratio >= 20%
            return 0.5 + (volume_to_mcap_ratio - 0.2) * (0.3 / 0.3) # Should be (0.3 / 0.3) = 1, maps 0.2 to 0.5, 0.5 to 0.8
            # Corrected: return 0.5 + ((volume_to_mcap_ratio - 0.2) / 0.3) * 0.3
            return 0.5 + (volume_to_mcap_ratio - 0.2) # this is 0.5 for ratio 0.2, up to 0.8 for ratio 0.5
        elif volume_to_mcap_ratio >= 0.05: # Ratio >= 5%
            #return 0.2 + (volume_to_mcap_ratio - 0.05) * (0.3 / 0.15) # maps 0.05 to 0.2, 0.2 to 0.5
            return 0.2 + ((volume_to_mcap_ratio - 0.05) / 0.15) * 0.3
        else: # Ratio < 5%
            return (volume_to_mcap_ratio / 0.05) * 0.2 # maps 0 to 0, 0.05 to 0.2
        
        # Simpler version from original for reference:
        # if volume_to_mcap_ratio >= 1.0: return 1.0
        # elif volume_to_mcap_ratio >= 0.5: return 0.8 + (volume_to_mcap_ratio - 0.5) * 0.4
        # elif volume_to_mcap_ratio >= 0.1: return 0.5 + (volume_to_mcap_ratio - 0.1) * 0.6 # (0.3 / 0.4 * 0.4)
        # else: return volume_to_mcap_ratio * 5


    def _score_volume_trends(self, metrics: TokenMetrics) -> float:
        base_volume_score = self._score_volume(metrics.volume_24h, metrics.mcap)
        
        trend_multipliers = self.config.get('volume_trend_multipliers', {
            "strongly_increasing": 1.3,
            "increasing": 1.2,
            "recently_increasing": 1.1,
            "stable": 1.0,
            "decreasing": 0.8,
            "strongly_decreasing": 0.6,
            "unknown": 0.95, # Slight penalty for unknown
            "error": 0.9,
            "insufficient_data": 0.9
        })
        
        trend_multiplier = trend_multipliers.get(metrics.volume_trend, 0.95)
        
        # Acceleration bonus/penalty
        # Assuming volume_acceleration is a percentage change (e.g., 50 for +50%)
        acceleration_factor = 0.0
        if metrics.volume_acceleration > 100: # More than doubled
            acceleration_factor = 0.15
        elif metrics.volume_acceleration > 50: # More than 50% increase
            acceleration_factor = 0.07
        elif metrics.volume_acceleration < -50: # More than 50% decrease
            acceleration_factor = -0.1
        
        final_score = base_volume_score * trend_multiplier + acceleration_factor
        return max(0.0, min(1.0, final_score))

    def _score_transaction_trends(self, metrics: TokenMetrics) -> float:
        trend_scores = self.config.get('tx_trend_scores', {
            "strongly_increasing": 1.0,
            "increasing": 0.85,
            "recently_increasing": 0.7,
            "stable": 0.5, # Stable is neutral
            "decreasing": 0.3,
            "strongly_decreasing": 0.15,
            "unknown": 0.4, # Penalty for unknown
            "error": 0.3,
            "insufficient_data": 0.3
        })
        return trend_scores.get(metrics.tx_count_trend, 0.4)

    def calculate_score(self, metrics: TokenMetrics, historical_data: Optional[List[Dict]] = None) -> Dict[str, Any]:
        cache_key = f"{metrics.address}_{metrics.price}_{metrics.mcap}"
        if cache_key in self._score_cache:
            return self._score_cache[cache_key]
        
        try:
            scores = {
                'liquidity': self._score_liquidity(metrics.liquidity),
                'market_cap': self._score_market_cap(metrics.mcap),
                'holders': self._score_holders(metrics.holders),
                'holder_distribution': self._score_holder_distribution(metrics.top_holders or []),
                'supply_distribution': self._score_supply_distribution(metrics.whale_holdings or {}),
                'security': self._score_security(metrics),
                'price_stability': self._score_price_stability(historical_data),
                'age': self._score_age(metrics.creation_time),
                'smart_contract': self._score_smart_contract(metrics), # Added this from earlier note
                # Volume related scores are now more granular
                'volume_to_mcap_ratio': self._score_volume(metrics.volume_24h, metrics.mcap), # Raw volume/mcap score
                'volume_trend_composite': self._score_volume_trends(metrics), # Volume score adjusted by trend and accel
                'transaction_trend': self._score_transaction_trends(metrics)
            }

            total_score_weighted = 0
            active_weight_sum = 0 # To normalize if some weights are zero or not applicable

            for key, score_value in scores.items():
                # Get weight from ScoreWeights dataclass attribute, which should be pre-filled from config
                weight = getattr(self.weights, key, 0.0) # Default to 0 if key somehow not in ScoreWeights
                if weight > 0: # Only consider scores with actual weight
                    total_score_weighted += score_value * weight 
                    active_weight_sum += weight
            
            # Normalize total score by sum of active weights (0-1 range)
            normalized_total_score = (total_score_weighted / active_weight_sum) if active_weight_sum > 0 else 0.0
            
            result = {
                'total': round(normalized_total_score * 100, 2), # Final score 0-100
                'breakdown': {k: round(v * 100, 2) for k, v in scores.items()}, # Individual scores 0-100
                'risk_factors': metrics.risk_factors or []
            }
            
            self._score_cache[cache_key] = result
            return result
            
        except Exception as e:
            self.logger.error(f"Error calculating gem score for {metrics.address}: {e}", exc_info=True)
            return {'total': 0.0, 'breakdown': {}, 'risk_factors': ['Scoring error occurred']}

# Need to add 'fields' from dataclasses if not already available globally in this context
from dataclasses import fields 