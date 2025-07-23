import math
from typing import Dict, List, Optional
import logging

class BirdEyeCostCalculator:
    """
    Calculate BirdEye API costs using their official batch cost formula:
    Batch CU Cost = N^0.8 × Base CU Cost
    
    Based on: https://docs.birdeye.so/docs/batch-token-cu-cost
    """
    
    # Official BirdEye endpoint costs from documentation
    ENDPOINT_COSTS = {
        # Single token endpoints
        '/defi/price': 10,
        '/defi/token_overview': 30,
        '/defi/token_security': 50,
        '/defi/ohlcv': 35,
        '/defi/v3/ohlcv': 30,
        '/defi/txs/token': 10,
        '/defi/token_trending': 50,
        '/defi/v2/tokens/new_listing': 80,
        '/defi/v3/token/list': 100,
        '/defi/v2/tokens/top_traders': 30,
        
        # Batch endpoints with base costs
        '/defi/multi_price': {'base_cu': 5, 'n_max': 100},
        '/defi/price_volume/multi': {'base_cu': 15, 'n_max': 50},
        '/defi/v3/token/meta-data/multiple': {'base_cu': 5, 'n_max': 50},
        '/defi/v3/token/trade-data/multiple': {'base_cu': 15, 'n_max': 20},
        '/defi/v3/token/market-data/multiple': {'base_cu': 15, 'n_max': 20},
        '/defi/v3/pair/overview/multiple': {'base_cu': 20, 'n_max': 20},
    }
    
    def __init__(self, logger: Optional[logging.Logger] = None):
        self.logger = logger or logging.getLogger(__name__)
        self.session_costs = {
            'total_compute_units': 0,
            'total_http_requests': 0,
            'cost_by_endpoint': {},
            'batch_savings': 0,  # CUs saved by using batch APIs
            'calls_by_endpoint': {}
        }
    
    def calculate_batch_cost(self, endpoint: str, num_tokens: int) -> int:
        """
        Calculate cost for batch API call using BirdEye's formula:
        Batch CU Cost = N^0.8 × Base CU Cost (rounded up)
        
        Args:
            endpoint: API endpoint path
            num_tokens: Number of tokens in the batch
            
        Returns:
            Compute units cost
        """
        if endpoint not in self.ENDPOINT_COSTS:
            self.logger.warning(f"Unknown endpoint cost for {endpoint}, using default 10 CUs")
            return num_tokens * 10
        
        endpoint_config = self.ENDPOINT_COSTS[endpoint]
        
        # Handle batch endpoints
        if isinstance(endpoint_config, dict):
            base_cu = endpoint_config['base_cu']
            n_max = endpoint_config['n_max']
            
            # Ensure we don't exceed batch limit
            if num_tokens > n_max:
                self.logger.warning(f"Batch size {num_tokens} exceeds n_max {n_max} for {endpoint}")
                num_tokens = min(num_tokens, n_max)
            
            # Apply BirdEye's batch cost formula
            batch_cost = math.ceil(pow(num_tokens, 0.8) * base_cu)
            
            # Calculate savings vs individual calls
            individual_cost = num_tokens * (base_cu * 2)  # Estimate individual call cost
            savings = individual_cost - batch_cost
            
            self.logger.debug(f"Batch cost for {endpoint}: {num_tokens} tokens = {batch_cost} CUs (saved {savings} CUs)")
            return batch_cost
        
        # Handle single token endpoints
        else:
            cost = endpoint_config * num_tokens
            self.logger.debug(f"Individual cost for {endpoint}: {num_tokens} calls = {cost} CUs")
            return cost
    
    def track_api_call(self, endpoint: str, num_tokens: int = 1, is_batch: bool = False) -> int:
        """
        Track an API call and calculate its cost.
        
        Args:
            endpoint: API endpoint path
            num_tokens: Number of tokens processed
            is_batch: Whether this was a batch call
            
        Returns:
            Compute units consumed
        """
        # Calculate cost
        if is_batch and num_tokens > 1:
            cost = self.calculate_batch_cost(endpoint, num_tokens)
            
            # Calculate savings from batching
            individual_cost = self.get_individual_cost(endpoint) * num_tokens
            savings = individual_cost - cost
            self.session_costs['batch_savings'] += max(0, savings)
        else:
            cost = self.get_individual_cost(endpoint) * num_tokens
        
        # Track session costs
        self.session_costs['total_compute_units'] += cost
        self.session_costs['total_http_requests'] += 1
        
        # Track by endpoint
        if endpoint not in self.session_costs['cost_by_endpoint']:
            self.session_costs['cost_by_endpoint'][endpoint] = 0
            self.session_costs['calls_by_endpoint'][endpoint] = 0
        
        self.session_costs['cost_by_endpoint'][endpoint] += cost
        self.session_costs['calls_by_endpoint'][endpoint] += 1
        
        return cost
    
    def get_individual_cost(self, endpoint: str) -> int:
        """Get the cost for a single token call to this endpoint."""
        if endpoint not in self.ENDPOINT_COSTS:
            return 10  # Default cost
        
        endpoint_config = self.ENDPOINT_COSTS[endpoint]
        
        if isinstance(endpoint_config, dict):
            # For batch endpoints, estimate individual cost as base_cu * 2
            return endpoint_config['base_cu'] * 2
        else:
            return endpoint_config
    
    def get_optimal_batch_size(self, endpoint: str, total_tokens: int) -> List[int]:
        """
        Calculate optimal batch sizes for cost efficiency.
        
        Args:
            endpoint: API endpoint path
            total_tokens: Total number of tokens to process
            
        Returns:
            List of optimal batch sizes
        """
        if endpoint not in self.ENDPOINT_COSTS:
            return [total_tokens]
        
        endpoint_config = self.ENDPOINT_COSTS[endpoint]
        
        if not isinstance(endpoint_config, dict):
            # Not a batch endpoint
            return [1] * total_tokens
        
        n_max = endpoint_config['n_max']
        
        if total_tokens <= n_max:
            return [total_tokens]
        
        # Split into optimal batches
        batches = []
        remaining = total_tokens
        
        while remaining > 0:
            batch_size = min(remaining, n_max)
            batches.append(batch_size)
            remaining -= batch_size
        
        return batches
    
    def get_session_summary(self) -> Dict:
        """Get comprehensive session cost summary."""
        total_requests = self.session_costs['total_http_requests']
        total_cus = self.session_costs['total_compute_units']
        
        # Calculate efficiency metrics
        avg_cus_per_request = total_cus / total_requests if total_requests > 0 else 0
        batch_efficiency = (self.session_costs['batch_savings'] / total_cus * 100) if total_cus > 0 else 0
        
        return {
            'total_compute_units': total_cus,
            'total_http_requests': total_requests,
            'avg_cus_per_request': round(avg_cus_per_request, 2),
            'batch_savings_cus': self.session_costs['batch_savings'],
            'batch_efficiency_percent': round(batch_efficiency, 2),
            'cost_by_endpoint': self.session_costs['cost_by_endpoint'],
            'calls_by_endpoint': self.session_costs['calls_by_endpoint'],
            'top_cost_endpoints': self._get_top_cost_endpoints()
        }
    
    def _get_top_cost_endpoints(self, top_n: int = 5) -> List[Dict]:
        """Get the top cost-consuming endpoints."""
        endpoint_costs = self.session_costs['cost_by_endpoint']
        sorted_endpoints = sorted(endpoint_costs.items(), key=lambda x: x[1], reverse=True)
        
        return [
            {
                'endpoint': endpoint,
                'total_cus': cost,
                'calls': self.session_costs['calls_by_endpoint'].get(endpoint, 0),
                'avg_cus_per_call': round(cost / self.session_costs['calls_by_endpoint'].get(endpoint, 1), 2)
            }
            for endpoint, cost in sorted_endpoints[:top_n]
        ]
    
    def reset_session(self):
        """Reset session tracking."""
        self.session_costs = {
            'total_compute_units': 0,
            'total_http_requests': 0,
            'cost_by_endpoint': {},
            'batch_savings': 0,
            'calls_by_endpoint': {}
        }
        self.logger.info("Cost tracking session reset")
    
    def estimate_monthly_cost(self, daily_cus: int, price_per_million_cus: float = 10.0) -> Dict:
        """
        Estimate monthly costs based on daily usage.
        
        Args:
            daily_cus: Average daily compute units
            price_per_million_cus: Price per million CUs (default $10)
            
        Returns:
            Cost estimates
        """
        monthly_cus = daily_cus * 30
        monthly_cost = (monthly_cus / 1_000_000) * price_per_million_cus
        
        return {
            'daily_cus': daily_cus,
            'monthly_cus': monthly_cus,
            'monthly_cost_usd': round(monthly_cost, 2),
            'cost_per_day_usd': round(monthly_cost / 30, 2)
        } 