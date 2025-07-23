"""
Base Token Discovery Strategy

This module contains the base class for all token discovery strategies.
It provides common functionality for token tracking, security filtering,
and API interaction patterns.
"""

import os
import json
import time
import logging
import asyncio
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Any, Optional, Set, Tuple

from api.birdeye_connector import BirdeyeAPI
from api.rugcheck_connector import RugCheckConnector
from services.logger_setup import LoggerSetup
from utils.structured_logger import get_structured_logger


class BaseTokenDiscoveryStrategy:
    """
    Base class for token discovery strategies.
    
    Each strategy implements a specific approach to discovering promising tokens
    using the Birdeye API's token list endpoint with different parameters.
    """
    
    def __init__(
        self,
        name: str,
        description: str,
        api_parameters: Dict[str, Any],
        min_consecutive_appearances: int = 3,
        logger: Optional[logging.Logger] = None,
        storage_dir: str = "data/discovery_results",
        enable_rugcheck_filtering: bool = True
    ):
        """
        Initialize the base token discovery strategy.
        
        Args:
            name: Name of the strategy
            description: Description of the strategy's purpose
            api_parameters: Parameters for the Birdeye API token list call
            min_consecutive_appearances: Min number of consecutive appearances to consider promising
            logger: Logger instance
            storage_dir: Directory to store strategy results
            enable_rugcheck_filtering: Enable RugCheck security filtering
        """
        self.name = name
        self.description = description
        self.api_parameters = api_parameters
        self.min_consecutive_appearances = min_consecutive_appearances
        self.enable_rugcheck_filtering = enable_rugcheck_filtering
        
        # Setup logger
        if logger:
            self.logger = logger
        else:
            logger_setup = LoggerSetup(f"Strategy_{name}")
            self.logger = logger_setup.logger
        
        # Setup RugCheck connector for security filtering
        if self.enable_rugcheck_filtering:
            self.rugcheck_connector = RugCheckConnector(logger=self.logger)
            self.logger.info(f"🛡️ RugCheck security filtering enabled for {name} strategy")
        else:
            self.rugcheck_connector = None
            self.logger.info(f"⚠️ RugCheck security filtering disabled for {name} strategy")
        
        # Setup storage
        self.storage_dir = Path(storage_dir)
        self.storage_dir.mkdir(parents=True, exist_ok=True)
        self.storage_file = self.storage_dir / f"{name.lower().replace(' ', '_')}_results.json"
        
        # Load history or initialize empty
        self.token_history = self.load_history()
        
        # Last execution time
        self.last_execution_time = self.token_history.get("last_execution_time", 0)
        
        # Risk management parameters - can be overridden by subclasses
        self.risk_management = {
            "max_allocation_percentage": 5.0,  # Max 5% allocation per token
            "suspicious_volume_multiplier": 3.0,  # Flag if volume jumps more than 3x
            "min_holder_distribution": 0.5,  # Top 10 holders should have < 50% 
            "max_concentration_pct": 70.0,  # Max 70% concentration in top wallets
            "min_dexs_with_liquidity": 2,  # Minimum DEXs with liquidity
            "min_days_since_listing": 2,       # Require at least 2 days history
        }
        
        self.structured_logger = get_structured_logger('StrategyExecutor')
        
        # Enhanced enrichment services (initialized lazily)
        self._trending_monitor = None
        self._smart_money_detector = None
        self._holder_analyzer = None
        
        # ENHANCED: Rate limiting and cost optimization tracking
        self.rate_limit_config = {
            "max_concurrent_batches": 3,  # Limit concurrent batch operations
            "batch_delay_seconds": 0.1,   # Delay between batch operations
            "enable_cost_tracking": True,  # Track API costs
            "prefer_batch_apis": True,     # Prefer batch APIs when available
        }
        
        # Cost optimization metrics
        self.cost_metrics = {
            "total_api_calls": 0,
            "batch_api_calls": 0,
            "individual_api_calls": 0,
            "estimated_cu_cost": 0,
            "estimated_cu_saved": 0,
            "batch_efficiency_ratio": 0.0
        }
        
    async def execute(self, birdeye_api: BirdeyeAPI, scan_id: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        Execute the strategy by calling the Birdeye API with the strategy's parameters.
        ENHANCED: Now includes batch operation optimization and cost tracking.
        
        Args:
            birdeye_api: Initialized Birdeye API instance
            scan_id: Optional scan ID for structured logging
            
        Returns:
            List of token data dictionaries
        """
        execution_start_time = time.time()
        self.structured_logger.info({"event": "strategy_run_start", "strategy": self.name, "scan_id": scan_id, "params": self.api_parameters, "timestamp": int(time.time())})
        self.logger.info(f"Executing {self.name} strategy with batch optimization")
        
        try:
            # Track initial API call metrics
            initial_api_calls = getattr(birdeye_api, 'api_call_count', 0)
            
            # Extract API parameters
            params = self.api_parameters.copy()
            sort_by = params.pop("sort_by", "volume_24h_usd")
            sort_type = params.pop("sort_type", "desc")
            limit = params.pop("limit", 20)
            
            # Call the Birdeye API for token discovery
            result = await birdeye_api.get_token_list(
                sort_by=sort_by,
                sort_type=sort_type,
                limit=limit,
                **params
            )
            
            # Process the results
            if result and isinstance(result, dict) and result.get("success") is True and "data" in result:
                tokens = result.get("data", {}).get("tokens", [])
                self.structured_logger.info({"event": "strategy_run_end", "strategy": self.name, "scan_id": scan_id, "tokens_found": len(tokens), "timestamp": int(time.time())})
                self.logger.info(f"Strategy {self.name} found {len(tokens)} tokens")
                
                # Filter out major tokens to save processing time
                from services.early_token_detection import filter_major_tokens
                tokens = filter_major_tokens(tokens)
                self.logger.info(f"Strategy {self.name} after major token filtering: {len(tokens)} tokens")
                
                # ENHANCED: Use batch operations for enrichment with cost tracking
                if self.rate_limit_config["enable_cost_tracking"]:
                    enrichment_start_time = time.time()
                    
                # ENHANCED: Batch enrich with all data sources simultaneously
                tokens = await self._batch_enrich_all_data(tokens, birdeye_api)
                
                processed_tokens = await self.process_results(tokens, birdeye_api, scan_id=scan_id)
                
                # ENHANCED: Apply enhanced scoring
                processed_tokens = await self._apply_enhanced_scoring(processed_tokens)
                
                # Track execution metrics
                execution_time = time.time() - execution_start_time
                final_api_calls = getattr(birdeye_api, 'api_call_count', 0)
                api_calls_used = final_api_calls - initial_api_calls
                
                # Update cost metrics
                self._update_cost_metrics(api_calls_used, len(tokens), execution_time)
                
                self.last_execution_time = int(time.time())
                self.token_history["last_execution_time"] = self.last_execution_time
                
                self.save_history()
                
                # Log performance metrics
                self.logger.info(f"✅ Strategy {self.name} completed in {execution_time:.2f}s, "
                               f"API calls: {api_calls_used}, Efficiency: {self.cost_metrics['batch_efficiency_ratio']:.2%}")
                
                return processed_tokens
            elif result and isinstance(result, dict) and result.get("success") is False:
                self.structured_logger.warning({"event": "strategy_error", "strategy": self.name, "scan_id": scan_id, "error": result.get('message', 'No error message')})
                self.logger.warning(f"Strategy {self.name} API call failed: {result.get('message', 'No error message')}")
                return []
            else:
                self.structured_logger.warning({"event": "strategy_error", "strategy": self.name, "scan_id": scan_id, "error": f"Strategy returned invalid or unsuccessful results structure: {result}"})
                self.logger.warning(f"Strategy {self.name} returned invalid or unsuccessful results structure: {result}")
                return []
                
        except Exception as e:
            self.structured_logger.error({"event": "strategy_error", "strategy": self.name, "scan_id": scan_id, "error": str(e)})
            self.logger.error(f"Error executing strategy {self.name}: {e}")
            return []
    
    async def process_results(self, tokens: List[Dict[str, Any]], birdeye_api: BirdeyeAPI, scan_id: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        Process the results from the API call, apply RugCheck filtering, and track token appearances.
        
        Args:
            tokens: List of token data from API
            birdeye_api: API instance for additional data fetching
            scan_id: Optional scan ID for structured logging
            
        Returns:
            List of processed and security-filtered token data
        """
        processed_tokens = []
        current_time = int(time.time())
        
        # Step 1: Apply RugCheck security filtering if enabled
        if self.enable_rugcheck_filtering and self.rugcheck_connector and tokens:
            self.logger.info(f"🛡️ Applying RugCheck security filtering to {len(tokens)} tokens from {self.name} strategy")
            
            # Extract token addresses for batch analysis
            token_addresses = [token.get("address") for token in tokens if token.get("address")]
            
            if token_addresses:
                # Perform batch security analysis
                rugcheck_results = await self.rugcheck_connector.batch_analyze_tokens(token_addresses)
                
                # Filter tokens based on security analysis
                tokens = self.rugcheck_connector.filter_healthy_tokens(tokens, rugcheck_results)
                
                self.logger.info(f"🛡️ Security filtering complete: {len(tokens)} healthy tokens remaining")
            else:
                self.logger.warning(f"⚠️ No valid token addresses found for security analysis")
        
        # Step 2: Process the filtered tokens
        for token in tokens:
            # Extract token address and basic info
            token_address = token.get("address")
            
            if not token_address:
                continue
                
            # Track this token's appearance
            token_history = self.track_token(token_address, token, current_time)
            
            # Add tracking data to token
            token["strategy_data"] = {
                "strategy": self.name,
                "consecutive_appearances": token_history.get("consecutive_appearances", 1),
                "first_seen": token_history.get("first_seen", current_time),
                "appearances": token_history.get("appearances", [current_time]),
                "rugcheck_filtered": self.enable_rugcheck_filtering
            }
            
            self.structured_logger.info({
                "event": "strategy_token_eval",
                "strategy": self.name,
                "scan_id": scan_id,
                "token": token_address,
                "features": token,
                "consecutive_appearances": token_history.get("consecutive_appearances", 1),
                "decision": "promising" if token_history.get("consecutive_appearances", 1) >= self.min_consecutive_appearances else "not_promising",
                "rugcheck_filtered": self.enable_rugcheck_filtering,
                "security_analysis": token.get("security_analysis", {})
            })
            
            # Add the processed token to the list
            processed_tokens.append(token)
            
        return processed_tokens
    
    def track_token(self, token_address: str, token_data: Dict[str, Any], timestamp: int) -> Dict[str, Any]:
        """
        Track a token's appearance in the strategy results.
        
        Args:
            token_address: The token's address
            token_data: Token data from API
            timestamp: Current timestamp
            
        Returns:
            Token history dictionary
        """
        # Initialize if this is a new token
        if token_address not in self.token_history.get("tokens", {}):
            self.token_history["tokens"][token_address] = {
                "first_seen": timestamp,
                "appearances": [timestamp],
                "consecutive_appearances": 1,
                "last_seen": timestamp,
                "last_data": token_data
            }
            return self.token_history["tokens"][token_address]
            
        # Update existing token
        token_history = self.token_history["tokens"][token_address]
        
        # Check if this is a consecutive appearance (within 8 hours of last appearance)
        last_seen = token_history.get("last_seen", 0)
        is_consecutive = (timestamp - last_seen) < (8 * 60 * 60)  # 8 hours
        
        if is_consecutive:
            token_history["consecutive_appearances"] += 1
        else:
            token_history["consecutive_appearances"] = 1
            
        # Update appearance data
        token_history["appearances"].append(timestamp)
        token_history["last_seen"] = timestamp
        token_history["last_data"] = token_data
        
        # Keep only the last 10 appearances to save space
        if len(token_history["appearances"]) > 10:
            token_history["appearances"] = token_history["appearances"][-10:]
            
        return token_history
    
    def get_promising_tokens(self) -> List[str]:
        """
        Get tokens that have appeared in enough consecutive runs to be considered promising.
        
        Returns:
            List of promising token addresses
        """
        promising = []
        
        for address, history in self.token_history.get("tokens", {}).items():
            if history.get("consecutive_appearances", 0) >= self.min_consecutive_appearances:
                promising.append(address)
                
        return promising
    
    def load_history(self) -> Dict[str, Any]:
        """
        Load token tracking history from storage.
        
        Returns:
            Dictionary with token tracking data
        """
        if not self.storage_file.exists():
            return {"tokens": {}, "last_execution_time": 0}
            
        try:
            with open(self.storage_file, 'r') as f:
                history = json.load(f)
                
            # Ensure the structure is correct
            if not isinstance(history, dict):
                history = {"tokens": {}, "last_execution_time": 0}
            if "tokens" not in history:
                history["tokens"] = {}
            if "last_execution_time" not in history:
                history["last_execution_time"] = 0
                
            return history
            
        except Exception as e:
            self.logger.error(f"Error loading history for {self.name}: {e}")
            return {"tokens": {}, "last_execution_time": 0}
    
    def save_history(self) -> None:
        """Save token tracking history to storage."""
        try:
            with open(self.storage_file, 'w') as f:
                json.dump(self.token_history, f, indent=2)
                
        except Exception as e:
            self.logger.error(f"Error saving history for {self.name}: {e}")
    
    def clean_expired_tokens(self, max_age_days: int = 7) -> None:
        """
        Remove tokens that haven't been seen recently.
        
        Args:
            max_age_days: Maximum age in days before removing a token
        """
        current_time = int(time.time())
        max_age_seconds = max_age_days * 24 * 60 * 60
        
        tokens_to_remove = []
        
        for address, history in self.token_history.get("tokens", {}).items():
            last_seen = history.get("last_seen", 0)
            if (current_time - last_seen) > max_age_seconds:
                tokens_to_remove.append(address)
                
        for address in tokens_to_remove:
            del self.token_history["tokens"][address]
            
        if tokens_to_remove:
            self.logger.info(f"Removed {len(tokens_to_remove)} expired tokens from {self.name}")
            self.save_history()
    
    def _get_trending_monitor(self, birdeye_api: BirdeyeAPI):
        """Get or create trending monitor instance."""
        if self._trending_monitor is None:
            from services.trending_token_monitor import TrendingTokenMonitor
            self._trending_monitor = TrendingTokenMonitor(birdeye_api, self.logger)
        return self._trending_monitor
    
    def _get_smart_money_detector(self, birdeye_api: BirdeyeAPI):
        """Get or create smart money detector instance."""
        if self._smart_money_detector is None:
            from services.smart_money_detector import SmartMoneyDetector
            self._smart_money_detector = SmartMoneyDetector(birdeye_api, self.logger)
        return self._smart_money_detector
    
    def _get_holder_analyzer(self, birdeye_api: BirdeyeAPI):
        """Get or create holder analyzer instance."""
        if self._holder_analyzer is None:
            from services.holder_distribution_analyzer import HolderDistributionAnalyzer
            self._holder_analyzer = HolderDistributionAnalyzer(birdeye_api, self.logger)
        return self._holder_analyzer
    
    async def _batch_enrich_all_data(self, tokens: List[Dict[str, Any]], birdeye_api: BirdeyeAPI) -> List[Dict[str, Any]]:
        """
        Batch enrich tokens with all data sources simultaneously for maximum efficiency.
        
        Args:
            tokens: List of tokens to enrich
            birdeye_api: Birdeye API instance
            
        Returns:
            Enriched tokens
        """
        if not tokens:
            return tokens
            
        self.logger.info(f"🚀 Batch enriching {len(tokens)} tokens with all data sources")
        
        try:
            # Use batch manager if available for maximum efficiency
            if hasattr(birdeye_api, 'batch_manager') and self.rate_limit_config["prefer_batch_apis"]:
                token_addresses = [token.get('address') for token in tokens if token.get('address')]
                
                # Batch fetch all required data simultaneously
                import asyncio
                
                # Create semaphore for rate limiting
                semaphore = asyncio.Semaphore(self.rate_limit_config["max_concurrent_batches"])
                
                async def fetch_with_semaphore(coro):
                    async with semaphore:
                        result = await coro
                        # Small delay between batch operations
                        await asyncio.sleep(self.rate_limit_config["batch_delay_seconds"])
                        return result
                
                # Fetch all data in parallel with rate limiting
                batch_tasks = [
                    fetch_with_semaphore(birdeye_api.batch_manager.batch_multi_price(token_addresses)),
                    fetch_with_semaphore(birdeye_api.batch_manager.batch_metadata_enhanced(token_addresses)),
                    fetch_with_semaphore(birdeye_api.batch_manager.batch_trade_data_enhanced(token_addresses)),
                ]
                
                batch_results = await asyncio.gather(*batch_tasks, return_exceptions=True)
                
                # Process batch results
                batch_price_data = batch_results[0] if not isinstance(batch_results[0], Exception) else {}
                batch_metadata = batch_results[1] if not isinstance(batch_results[1], Exception) else {}
                batch_trade_data = batch_results[2] if not isinstance(batch_results[2], Exception) else {}
                
                # Enrich tokens with batch data
                tokens = self._apply_batch_enrichment(tokens, batch_price_data, batch_metadata, batch_trade_data)
                
                self.cost_metrics["batch_api_calls"] += len(batch_tasks)
                self.logger.info(f"✅ Batch enrichment completed using {len(batch_tasks)} batch API calls")
                
            else:
                # Fallback to individual enrichment methods
                self.logger.info("⚠️ Batch manager not available, using individual enrichment methods")
                tokens = await self._enrich_with_trending_data(tokens, birdeye_api)
                tokens = await self._enrich_with_trader_data(tokens, birdeye_api)
                tokens = await self._enrich_with_holder_data(tokens, birdeye_api)
                
        except Exception as e:
            self.logger.error(f"Error in batch enrichment: {e}")
            # Fallback to individual enrichment
            try:
                tokens = await self._enrich_with_trending_data(tokens, birdeye_api)
                tokens = await self._enrich_with_trader_data(tokens, birdeye_api)
                tokens = await self._enrich_with_holder_data(tokens, birdeye_api)
            except Exception as fallback_error:
                self.logger.error(f"Fallback enrichment also failed: {fallback_error}")
        
        return tokens
    
    def _apply_batch_enrichment(self, tokens: List[Dict[str, Any]], price_data: Dict[str, Any], 
                               metadata: Dict[str, Any], trade_data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Apply batch enrichment data to tokens.
        
        Args:
            tokens: Original tokens
            price_data: Batch price data
            metadata: Batch metadata
            trade_data: Batch trade data
            
        Returns:
            Enriched tokens
        """
        enriched_tokens = []
        
        for token in tokens:
            address = token.get('address')
            if not address:
                enriched_tokens.append(token)
                continue
                
            # Enrich with price data
            if address in price_data:
                token.update(price_data[address])
                
            # Enrich with metadata
            if address in metadata:
                meta = metadata[address]
                token['holder'] = meta.get('holder', token.get('holder', 0))
                token['marketCap'] = meta.get('marketCap', token.get('marketCap', 0))
                # Add holder analysis
                token['holder_analysis'] = self._analyze_holders_from_metadata(meta)
                
            # Enrich with trade data
            if address in trade_data:
                trade = trade_data[address]
                token['trader_analysis'] = self._analyze_traders_from_trade_data(trade)
                
            # Add batch enrichment flags
            token['batch_enriched'] = True
            token['enrichment_sources'] = {
                'price_data': address in price_data,
                'metadata': address in metadata,
                'trade_data': address in trade_data
            }
                
            enriched_tokens.append(token)
            
        return enriched_tokens
    
    def _analyze_holders_from_metadata(self, metadata: Dict[str, Any]) -> Dict[str, Any]:
        """Quick holder analysis from metadata."""
        holder_count = metadata.get('holder', 0)
        market_cap = metadata.get('marketCap', 0)
        
        risk_score = 50
        if holder_count < 100:
            risk_score += 30
        elif holder_count > 1000:
            risk_score -= 20
            
        return {
            'risk_assessment': {
                'risk_level': 'high' if risk_score > 70 else 'medium' if risk_score > 40 else 'low',
                'overall_risk_score': risk_score
            },
            'holder_count': holder_count
        }
    
    def _analyze_traders_from_trade_data(self, trade_data: Dict[str, Any]) -> Dict[str, Any]:
        """Quick trader analysis from trade data."""
        transactions = trade_data.get('transactions', [])
        if not transactions:
            return {'smart_money_level': 'minimal', 'smart_money_score': 0.0}
            
        unique_traders = set()
        total_volume = 0
        
        for tx in transactions:
            trader = tx.get('from_address') or tx.get('trader')
            if trader:
                unique_traders.add(trader)
            total_volume += tx.get('volume_usd', 0)
            
        avg_trade_size = total_volume / len(transactions) if transactions else 0
        quality_score = min(1.0, (len(unique_traders) / 10) * 0.5 + (avg_trade_size / 5000) * 0.5)
        
        return {
            'smart_money_level': 'high' if quality_score > 0.7 else 'medium' if quality_score > 0.4 else 'minimal',
            'smart_money_score': quality_score,
            'trader_count': len(unique_traders)
        }
    
    def _update_cost_metrics(self, api_calls_used: int, tokens_processed: int, execution_time: float):
        """Update cost optimization metrics."""
        self.cost_metrics["total_api_calls"] += api_calls_used
        
        # Estimate cost savings from batch operations
        if tokens_processed > 0:
            # Estimate individual API calls that would have been needed
            estimated_individual_calls = tokens_processed * 3  # Price + metadata + trades
            actual_calls = api_calls_used
            
            self.cost_metrics["estimated_cu_saved"] += max(0, estimated_individual_calls - actual_calls) * 15  # Avg 15 CU per call
            self.cost_metrics["batch_efficiency_ratio"] = 1.0 - (actual_calls / max(1, estimated_individual_calls))
    
    def get_cost_optimization_report(self) -> Dict[str, Any]:
        """Get cost optimization performance report."""
        return {
            "strategy_name": self.name,
            "cost_metrics": self.cost_metrics.copy(),
            "rate_limit_config": self.rate_limit_config.copy(),
            "batch_apis_enabled": self.rate_limit_config["prefer_batch_apis"],
            "efficiency_grade": "Excellent" if self.cost_metrics["batch_efficiency_ratio"] > 0.7 else 
                              "Good" if self.cost_metrics["batch_efficiency_ratio"] > 0.4 else "Needs Improvement"
        }

    async def _enrich_with_trending_data(self, tokens: List[Dict[str, Any]], birdeye_api: BirdeyeAPI) -> List[Dict[str, Any]]:
        """Enrich tokens with trending information using batch operations."""
        try:
            trending_monitor = self._get_trending_monitor(birdeye_api)
            
            # Get trending tokens once for all tokens
            trending_tokens = await trending_monitor.get_trending_tokens(limit=100)
            trending_addresses = {token.get('address') for token in trending_tokens if token.get('address')}
            
            # ENHANCED: Use batch operations instead of individual calls
            token_addresses = [token.get('address') for token in tokens if token.get('address')]
            
            # Batch check trending status for all tokens at once
            batch_trending_status = {}
            if hasattr(trending_monitor, 'batch_check_trending_status'):
                batch_trending_status = await trending_monitor.batch_check_trending_status(token_addresses)
            else:
                # Fallback: Use batch API manager if available
                if hasattr(birdeye_api, 'batch_manager'):
                    # Get price/volume data in batch for trending analysis
                    batch_price_data = await birdeye_api.batch_manager.batch_multi_price(token_addresses)
                    batch_trending_status = self._analyze_trending_from_batch_data(batch_price_data, trending_addresses)
            
            # Enrich tokens with trending data
            enriched_tokens = []
            for token in tokens:
                address = token.get('address')
                if address in batch_trending_status:
                    trending_status = batch_trending_status[address]
                    token['is_trending'] = trending_status.get('is_trending', address in trending_addresses)
                    token['trending_analysis'] = trending_status.get('analysis', {})
                    token['trending_boost_applied'] = trending_status.get('score_boost', 1.2 if address in trending_addresses else 1.0)
                elif address in trending_addresses:
                    token['is_trending'] = True
                    token['trending_boost_applied'] = 1.2
                else:
                    token['is_trending'] = False
                    token['trending_boost_applied'] = 1.0
                    
                enriched_tokens.append(token)
            
            self.logger.info(f"✨ Enhanced {len(tokens)} tokens with trending data using batch operations")
            return enriched_tokens
        except Exception as e:
            self.logger.warning(f"⚠️ Failed to enrich with trending data: {e}")
            return tokens
    
    def _analyze_trending_from_batch_data(self, batch_price_data: Dict[str, Any], trending_addresses: set) -> Dict[str, Any]:
        """Analyze trending status from batch price data."""
        trending_status = {}
        
        for address, price_data in batch_price_data.items():
            is_trending = address in trending_addresses
            volume_24h = price_data.get('volume24h', 0)
            price_change = price_data.get('priceChange24h', 0)
            
            # Simple trending analysis based on available data
            trending_score = 0.5
            if volume_24h > 100000:  # High volume
                trending_score += 0.2
            if price_change > 10:  # Price momentum
                trending_score += 0.2
            if is_trending:  # In trending list
                trending_score += 0.3
                
            trending_status[address] = {
                'is_trending': is_trending or trending_score > 0.7,
                'score_boost': 1.0 + (trending_score - 0.5) * 0.6,  # 1.0 to 1.3x boost
                'analysis': {
                    'trending_score': trending_score,
                    'volume_24h': volume_24h,
                    'price_change_24h': price_change
                }
            }
            
        return trending_status

    async def _enrich_with_trader_data(self, tokens: List[Dict[str, Any]], birdeye_api: BirdeyeAPI) -> List[Dict[str, Any]]:
        """Enrich tokens with smart money and trader analysis using batch operations."""
        try:
            smart_money_detector = self._get_smart_money_detector(birdeye_api)
            
            # ENHANCED: Use batch operations instead of individual calls
            token_addresses = [token.get('address') for token in tokens if token.get('address')]
            
            # Batch analyze traders for all tokens
            batch_trader_analysis = {}
            if hasattr(smart_money_detector, 'batch_analyze_token_traders'):
                batch_trader_analysis = await smart_money_detector.batch_analyze_token_traders(token_addresses, limit=20)
            else:
                # Fallback: Use batch API manager for transaction data
                if hasattr(birdeye_api, 'batch_manager'):
                    # Get trade data in batch
                    batch_trade_data = await birdeye_api.batch_manager.batch_trade_data_enhanced(token_addresses)
                    batch_trader_analysis = self._analyze_traders_from_batch_data(batch_trade_data)
            
            # Enrich tokens with trader analysis
            enriched_tokens = []
            for token in tokens:
                address = token.get('address')
                if address and address in batch_trader_analysis:
                    trader_analysis = batch_trader_analysis[address]
                    token['smart_money_detected'] = trader_analysis.get('smart_traders_count', 0) > 0
                    token['smart_money_score'] = trader_analysis.get('aggregate_metrics', {}).get('avg_quality_score', 0.0)
                    token['smart_money_level'] = trader_analysis.get('smart_money_level', 'minimal')
                    token['smart_money_boost_applied'] = trader_analysis.get('score_boost', 1.0)
                    token['smart_traders_count'] = trader_analysis.get('smart_traders_count', 0)
                else:
                    token['smart_money_detected'] = False
                    token['smart_money_score'] = 0.0
                    token['smart_money_level'] = 'minimal'
                    token['smart_money_boost_applied'] = 1.0
                    token['smart_traders_count'] = 0
                    
                enriched_tokens.append(token)
            
            self.logger.info(f"🧠 Enhanced {len(tokens)} tokens with smart money data using batch operations")
            return enriched_tokens
        except Exception as e:
            self.logger.warning(f"⚠️ Failed to enrich with trader data: {e}")
            return tokens
    
    def _analyze_traders_from_batch_data(self, batch_trade_data: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze trader quality from batch trade data."""
        trader_analysis = {}
        
        for address, trade_data in batch_trade_data.items():
            transactions = trade_data.get('transactions', [])
            unique_traders = set()
            total_volume = 0
            large_trades = 0
            
            for tx in transactions:
                trader = tx.get('from_address') or tx.get('trader_address')
                if trader:
                    unique_traders.add(trader)
                    
                value = tx.get('volume_usd', 0) or tx.get('value_usd', 0)
                total_volume += value
                if value > 10000:  # Large trade > $10k
                    large_trades += 1
            
            # Simple trader quality analysis
            trader_count = len(unique_traders)
            avg_trade_size = total_volume / len(transactions) if transactions else 0
            large_trade_ratio = large_trades / len(transactions) if transactions else 0
            
            quality_score = 0.0
            if trader_count > 10:  # Good trader diversity
                quality_score += 0.3
            if avg_trade_size > 1000:  # Decent trade sizes
                quality_score += 0.3
            if large_trade_ratio > 0.1:  # Some large traders
                quality_score += 0.4
            
            smart_money_level = 'minimal'
            if quality_score > 0.7:
                smart_money_level = 'high'
            elif quality_score > 0.4:
                smart_money_level = 'medium'
            
            trader_analysis[address] = {
                'smart_traders_count': max(1, int(trader_count * large_trade_ratio)),
                'aggregate_metrics': {'avg_quality_score': quality_score},
                'smart_money_level': smart_money_level,
                'score_boost': 1.0 + quality_score * 0.5,  # 1.0 to 1.5x boost
                'total_traders': trader_count
            }
            
        return trader_analysis

    async def _enrich_with_holder_data(self, tokens: List[Dict[str, Any]], birdeye_api: BirdeyeAPI) -> List[Dict[str, Any]]:
        """Enrich tokens with holder distribution analysis using batch operations."""
        try:
            holder_analyzer = self._get_holder_analyzer(birdeye_api)
            
            # ENHANCED: Use batch operations instead of individual calls
            token_addresses = [token.get('address') for token in tokens if token.get('address')]
            
            # Batch analyze holder distribution for all tokens
            batch_holder_analysis = {}
            if hasattr(holder_analyzer, 'batch_analyze_holder_distribution'):
                batch_holder_analysis = await holder_analyzer.batch_analyze_holder_distribution(token_addresses, limit=100)
            else:
                # Fallback: Use batch API manager for metadata
                if hasattr(birdeye_api, 'batch_manager'):
                    # Get metadata in batch (includes holder info)
                    batch_metadata = await birdeye_api.batch_manager.batch_metadata_enhanced(token_addresses)
                    batch_holder_analysis = self._analyze_holders_from_batch_data(batch_metadata)
            
            # Enrich tokens with holder analysis
            enriched_tokens = []
            for token in tokens:
                address = token.get('address')
                if address and address in batch_holder_analysis:
                    holder_analysis = batch_holder_analysis[address]
                    token['holder_analysis'] = holder_analysis
                    token['holder_risk_level'] = holder_analysis.get('risk_assessment', {}).get('risk_level', 'unknown')
                    token['holder_quality_score'] = 1.0 - (holder_analysis.get('risk_assessment', {}).get('overall_risk_score', 50) / 100.0)
                    token['holder_adjustment_factor'] = holder_analysis.get('score_adjustment', {}).get('score_multiplier', 1.0)
                    token['concentration_warning'] = holder_analysis.get('risk_assessment', {}).get('is_high_risk', False)
                    token['gini_coefficient'] = holder_analysis.get('gini_coefficient', 0.0)
                else:
                    token['holder_analysis'] = {}
                    token['holder_risk_level'] = 'unknown'
                    token['holder_quality_score'] = 0.5
                    token['holder_adjustment_factor'] = 1.0
                    token['concentration_warning'] = False
                    token['gini_coefficient'] = 0.0
                    
                enriched_tokens.append(token)
            
            self.logger.info(f"👥 Enhanced {len(tokens)} tokens with holder distribution data using batch operations")
            return enriched_tokens
        except Exception as e:
            self.logger.warning(f"⚠️ Failed to enrich with holder data: {e}")
            return tokens
    
    def _analyze_holders_from_batch_data(self, batch_metadata: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze holder distribution from batch metadata."""
        holder_analysis = {}
        
        for address, metadata in batch_metadata.items():
            holder_count = metadata.get('holder', 0) or metadata.get('holders', 0)
            market_cap = metadata.get('marketCap', 0)
            liquidity = metadata.get('liquidity', 0)
            
            # Simple holder analysis based on available data
            risk_score = 50  # Default medium risk
            
            if holder_count < 100:
                risk_score += 30  # High risk for low holder count
            elif holder_count > 1000:
                risk_score -= 20  # Lower risk for high holder count
            
            if market_cap > 0 and liquidity > 0:
                liquidity_ratio = liquidity / market_cap
                if liquidity_ratio > 0.5:  # Very high liquidity ratio might indicate concentration
                    risk_score += 10
                elif liquidity_ratio < 0.05:  # Very low liquidity
                    risk_score += 20
            
            risk_level = 'high' if risk_score > 70 else 'medium' if risk_score > 40 else 'low'
            
            # Calculate adjustment factors
            quality_score = max(0.0, min(1.0, (100 - risk_score) / 100))
            score_multiplier = 0.8 + (quality_score * 0.4)  # 0.8 to 1.2x multiplier
            
            holder_analysis[address] = {
                'risk_assessment': {
                    'risk_level': risk_level,
                    'overall_risk_score': risk_score,
                    'is_high_risk': risk_score > 70
                },
                'score_adjustment': {
                    'score_multiplier': score_multiplier
                },
                'gini_coefficient': min(0.8, risk_score / 100),  # Approximate Gini
                'distribution_score': quality_score,
                'whale_concentration': min(0.9, risk_score / 100)
            }
            
        return holder_analysis
    
    async def _apply_enhanced_scoring(self, tokens: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Apply enhanced scoring using multiple signals."""
        try:
            enhanced_tokens = []
            
            for token in tokens:
                # Get existing score or default
                base_score = token.get('score', 50.0)
                enhancement_factors = []
                
                # Apply trending boost (20% signal weight, up to 1.5x boost)
                trending_boost = token.get('trending_boost_applied', 1.0)
                if trending_boost > 1.0:
                    base_score *= trending_boost
                    enhancement_factors.append(f"Trending: {trending_boost:.2f}x")
                
                # Apply smart money boost (20% signal weight, up to 1.5x boost)
                smart_money_boost = token.get('smart_money_boost_applied', 1.0)
                if smart_money_boost > 1.0:
                    base_score *= smart_money_boost
                    enhancement_factors.append(f"Smart Money: {smart_money_boost:.2f}x")
                
                # Apply holder quality adjustment (10% signal weight, ±20% adjustment)
                holder_adjustment = token.get('holder_adjustment_factor', 1.0)
                base_score *= holder_adjustment
                if holder_adjustment != 1.0:
                    enhancement_factors.append(f"Holder Quality: {holder_adjustment:.2f}x")
                
                # Freshness factor for new tokens (5% signal weight)
                creation_time = token.get('creation_time', 0)
                if creation_time > 0:
                    age_hours = (time.time() - creation_time) / 3600
                    if age_hours < 24:  # Less than 24 hours old
                        freshness_boost = 1.1  # 10% bonus for very fresh tokens
                        base_score *= freshness_boost
                        enhancement_factors.append(f"Freshness: {freshness_boost:.2f}x")
                
                # Risk penalties
                if token.get('concentration_warning', False):
                    risk_penalty = 0.9  # 10% penalty for concentration risk
                    base_score *= risk_penalty
                    enhancement_factors.append(f"Risk Penalty: {risk_penalty:.2f}x")
                
                # Store enhanced score and factors
                token['enhanced_score'] = round(base_score, 2)
                token['score'] = round(base_score, 2)
                token['enhancement_factors'] = enhancement_factors
                token['base_score_before_enhancement'] = token.get('score', 50.0)
                
                # Add summary of enhancements
                token['enhancement_summary'] = {
                    'is_trending': token.get('is_trending', False),
                    'smart_money_detected': token.get('smart_money_detected', False),
                    'holder_risk_level': token.get('holder_risk_level', 'unknown'),
                    'total_boost_factor': round(base_score / token.get('score', 50.0), 3),
                    'enhancement_count': len(enhancement_factors)
                }
                
                enhanced_tokens.append(token)
            
            # Sort by enhanced score
            enhanced_tokens.sort(key=lambda x: x.get('enhanced_score', 0), reverse=True)
            
            self.logger.info(f"🎯 Applied enhanced scoring to {len(tokens)} tokens")
            return enhanced_tokens
            
        except Exception as e:
            self.logger.warning(f"⚠️ Failed to apply enhanced scoring: {e}")
            return tokens 