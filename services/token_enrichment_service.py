import logging
import time
import asyncio # Required for async methods
from typing import Dict, List, Optional, Any

# Assuming all necessary API clients, services, and models are importable
# These will be constructor-injected.
# Placeholder imports for clarity of dependencies:
from services.logger_setup import LoggerSetup
from services.dexscreener_api import DexScreenerAPI
from services.solscan_api import SolscanAPI # Assuming SolscanAPI is in services
from services.gem_scorer import GemScorer
from services.whale_tracker import WhaleTracker
from services.trend_analysis_service import TrendAnalysisService
from jupiter_connector import JupiterAPI # Assuming top-level for Jupiter
from helius_connector import HeliusAPI # Assuming top-level for Helius
from solana_rpc_enhanced import EnhancedSolanaRPC # For _analyze_whale_wallet_enhanced if used here

# Assuming TokenMetrics is defined in a shared models file or solgem.py initially
try:
    from solgem import TokenMetrics
except ImportError:
    from dataclasses import dataclass, field
    @dataclass
    class TokenMetrics:
        address: str; name: str; symbol: str; price: float; mcap: float; liquidity: float
        volume_24h: float; holders: int; creation_time: int; whale_holdings: Dict[str, float]
        total_supply: int = 0; decimals: int = 0; is_mint_frozen: bool = False
        program_id: str = ""; top_holders: List[Dict[str, Any]] = field(default_factory=list)
        security_score: float = 0.0; risk_factors: List[str] = field(default_factory=list)
        contract_verified: bool = False; is_honeypot: bool = False
        buy_tax: float = 0.0; sell_tax: float = 0.0; volume_trend: str = "unknown"
        volume_trend_score: float = 0.0; volume_acceleration: float = 0.0
        tx_count_trend: str = "unknown"; tx_trend_score: float = 0.0
        creator_addresses: List[str] = field(default_factory=list)

class TokenEnrichmentService: # Renamed from TokenDataProvider for clarity on its role
    def __init__(self, 
                 config: Dict,
                 dex_screener_api: DexScreenerAPI,
                 solscan_api: Optional[SolscanAPI],
                 jupiter_api: Optional[JupiterAPI],
                 helius_api: Optional[HeliusAPI],
                 # solana_rpc: SolanaRPC, # Basic RPC, if needed directly
                 enhanced_rpc: Optional[EnhancedSolanaRPC],
                 trend_analyzer: TrendAnalysisService,
                 whale_tracker: WhaleTracker,
                 # GemScorer might not be needed if this service only provides data for scoring
                 # However, if _analyze_token itself calls scorer, it would be needed.
                 # For now, let's assume it might do some preliminary scoring or check score threshold.
                 gem_scorer: GemScorer, 
                 logger_setup: Optional[LoggerSetup] = None):
        
        self.config = config
        self.dex_screener = dex_screener_api
        self.solscan_api = solscan_api
        self.jupiter_api = jupiter_api
        self.helius_api = helius_api
        # self.solana_rpc = solana_rpc
        self.enhanced_rpc = enhanced_rpc # Used by _analyze_whale_wallet_enhanced logic
        self.trend_analyzer = trend_analyzer
        self.whale_tracker = whale_tracker
        self.gem_scorer = gem_scorer # If scoring logic is triggered from here
        
        if logger_setup:
            self.logger = logger_setup.get_logger('TokenEnrichmentService')
        else:
            self.logger = LoggerSetup('TokenEnrichmentService').logger
        
        self._jupiter_token_list_cache: Optional[Dict[str, Any]] = None
        self.loop = asyncio.get_event_loop() # For running async jupiter calls if this service is sync
        self.logger.info("TokenEnrichmentService initialized.")

    # --- Methods to be moved/adapted from VirtuosoGemFinder --- #

    def _get_liquidity_provider_share(self, token_address: str) -> Dict[str, float]:
        self.logger.debug(f"Getting LP share for {token_address}")
        lp_shares = {}
        try:
            token_pairs_info = self.dex_screener.get_token_info([token_address]) 
            if not token_pairs_info:
                return {}
            total_token_liquidity_usd = sum(
                float(pair.get('liquidity', {}).get('usd', 0))
                for pair in token_pairs_info
                if pair.get('liquidity', {}).get('usd')
            )
            if total_token_liquidity_usd == 0:
                return {}
            whale_threshold = self.config.get('whale_threshold', 0.05)
            for pair in token_pairs_info:
                pair_addr = pair.get('pairAddress')
                pair_liquidity = float(pair.get('liquidity', {}).get('usd', 0))
                if pair_addr and pair_liquidity > (total_token_liquidity_usd * whale_threshold):
                    lp_shares[pair_addr] = pair_liquidity / total_token_liquidity_usd
            return lp_shares
        except Exception as e:
            self.logger.error(f"Error in _get_liquidity_provider_share for {token_address}: {e}", exc_info=True)
            return {}

    async def get_actual_holder_count(self, token_address: str) -> int:
        if self.solscan_api:
            try:
                return await asyncio.to_thread(self.solscan_api.get_token_holders, token_address)
            except Exception as e:
                self.logger.error(f"Error getting Solscan holder count for {token_address}: {e}", exc_info=True)
        if self.helius_api:
            try:
                count = await self.helius_api.get_current_holder_count(token_address)
                if count is not None: return count
            except Exception as e:
                self.logger.error(f"Error getting Helius holder count for {token_address}: {e}", exc_info=True)
        self.logger.warning(f"Could not determine actual holder count for {token_address} from available APIs.")
        return 0
    
    async def get_jupiter_price(self, token_address: str) -> Optional[float]:
        if not self.jupiter_api:
            return None
        try:
            price = await self.jupiter_api.get_token_price_usd(token_address)
            self.logger.debug(f"Jupiter price for {token_address}: {price}")
            return price
        except Exception as e:
            self.logger.error(f"Error fetching Jupiter price for {token_address}: {e}", exc_info=True)
            return None

    async def verify_token_with_jupiter(self, token_address: str) -> bool:
        if not self.jupiter_api:
            return False 
        try:
            if self._jupiter_token_list_cache is None:
                token_list = await self.jupiter_api.get_token_list()
                self._jupiter_token_list_cache = {token.get('address'): token for token in token_list if token.get('address')}
                self.logger.info(f"Fetched and cached {len(self._jupiter_token_list_cache)} tokens from Jupiter.")
            is_listed = token_address in self._jupiter_token_list_cache
            self.logger.debug(f"Token {token_address} Jupiter listed: {is_listed}")
            return is_listed
        except Exception as e:
            self.logger.error(f"Error verifying token {token_address} with Jupiter: {e}", exc_info=True)
            return False

    async def get_enhanced_token_metadata(self, token_address: str) -> Dict:
        metadata = {}
        try:
            dex_info_list = await asyncio.to_thread(self.dex_screener.get_token_info, [token_address])
            if dex_info_list and len(dex_info_list) > 0:
                metadata["dexscreener"] = dex_info_list[0]

            if self.jupiter_api:
                metadata["jupiter_verified"] = await self.verify_token_with_jupiter(token_address)
            
            if self.helius_api:
                try:
                    helius_meta = await self.helius_api.get_token_metadata([token_address])
                    if token_address in helius_meta:
                        metadata["helius"] = helius_meta[token_address]
                        if "metadataUri" in helius_meta[token_address]:
                            metadata["metadata_uri"] = helius_meta[token_address]["metadataUri"]
                        if "creators" in helius_meta[token_address]:
                            metadata["creators"] = helius_meta[token_address]["creators"]
                except Exception as e_helius:
                    self.logger.error(f"Error fetching Helius component of metadata for {token_address}: {e_helius}", exc_info=True)

            if self.enhanced_rpc:
                try:
                    supply_info = await self.enhanced_rpc.get_token_supply_details(token_address) 
                    if supply_info:
                        metadata["total_supply"] = supply_info.get('uiAmountString')
                        metadata["decimals"] = supply_info.get('decimals')
                except Exception as e_rpc_supply:
                    self.logger.error(f"Error fetching RPC token supply for {token_address}: {e_rpc_supply}", exc_info=True)
        except Exception as e_outer:
            self.logger.error(f"Outer error in get_enhanced_token_metadata for {token_address}: {e_outer}", exc_info=True)
            # Ensure metadata is returned as a dict even in case of outer error
        return metadata

    async def analyze_token_comprehensively(self, pair_data: Dict) -> Optional[TokenMetrics]:
        self.logger.info(f"Starting comprehensive analysis for pair: {pair_data.get('pairAddress')}")
        start_time = time.time()
        
        base_token_info = pair_data.get('baseToken', {})
        token_address = base_token_info.get('address')
        pair_address = pair_data.get('pairAddress')

        if not token_address or not pair_address:
            self.logger.warning("Missing token_address or pair_address in pair_data.")
            return None

        try:
            pair_details = await asyncio.to_thread(self.dex_screener.get_pair_details, pair_address)
            if not pair_details:
                self.logger.warning(f"No pair details from DexScreener for {pair_address}")
                return None

            dex_price = float(pair_data.get('priceUsd', 0))
            jupiter_price_usd = await self.get_jupiter_price(token_address) if self.jupiter_api else None
            current_price = jupiter_price_usd if jupiter_price_usd is not None else dex_price

            if jupiter_price_usd is not None and dex_price > 0:
                price_diff_pct = abs(jupiter_price_usd - dex_price) / dex_price * 100
                if price_diff_pct > self.config.get('price_discrepancy_alert_threshold_pct', 5.0):
                    self.logger.warning(f"Price discrepancy for {token_address}: DexScreener ${dex_price:.6f} vs Jupiter ${jupiter_price_usd:.6f} ({price_diff_pct:.2f}%)")

            holder_count = await self.get_actual_holder_count(token_address)
            lp_shares = await asyncio.to_thread(self._get_liquidity_provider_share, token_address)
            is_jupiter_verified = await self.verify_token_with_jupiter(token_address)

            creation_timestamp_ms = pair_data.get('pairCreatedAt')
            creation_time_sec = int(creation_timestamp_ms / 1000) if creation_timestamp_ms else int(time.time())

            metrics = TokenMetrics(
                address=token_address,
                name=base_token_info.get('name', 'N/A'),
                symbol=base_token_info.get('symbol', 'N/A'),
                price=current_price,
                mcap=float(pair_data.get('marketCap', 0) or pair_data.get('fdv',0)),
                liquidity=float(pair_data.get('liquidity', {}).get('usd', 0)),
                volume_24h=float(pair_data.get('volume', {}).get('h24', 0)),
                holders=holder_count,
                creation_time=creation_time_sec, 
                whale_holdings=lp_shares, 
                risk_factors=[] 
            )

            if not is_jupiter_verified:
                metrics.risk_factors.append("TokenNotVerifiedOnJupiter")

            # 7. Enhanced Metadata (Helius, advanced RPC)
            self.logger.debug(f"Fetching enhanced metadata for {token_address}...")
            enhanced_meta = await self.get_enhanced_token_metadata(token_address)
            
            if enhanced_meta.get('helius'):
                helius_data = enhanced_meta['helius']
                self.logger.debug(f"Processing Helius data for {token_address}: {helius_data.keys() if isinstance(helius_data, dict) else 'N/A'}")
                # Example population (actual fields depend on HeliusAPI response structure)
                if isinstance(helius_data, dict):
                    on_chain_data = helius_data.get('onChainData', {})
                    if isinstance(on_chain_data, dict):
                        metadata_from_onchain = on_chain_data.get('metadata', {})
                        if isinstance(metadata_from_onchain, dict):
                             # Assuming Helius provides direct flags or data points we can map
                            metrics.contract_verified = metadata_from_onchain.get('isVerified', metrics.contract_verified) # Example field
                    # metrics.is_mint_frozen = helius_data.get('mintIsFrozen', metrics.is_mint_frozen) # Example direct field

            if enhanced_meta.get('total_supply') is not None:
                try: 
                    metrics.total_supply = int(float(enhanced_meta['total_supply']))
                except (ValueError, TypeError):
                    self.logger.warning(f"Could not parse total_supply '{enhanced_meta['total_supply']}' for {token_address}")
            
            if enhanced_meta.get('decimals') is not None:
                try:
                    metrics.decimals = int(enhanced_meta['decimals'])
                except (ValueError, TypeError):
                     self.logger.warning(f"Could not parse decimals '{enhanced_meta['decimals']}' for {token_address}")
            
            if enhanced_meta.get('creators'):
                creators_list = enhanced_meta['creators']
                if isinstance(creators_list, list):
                    metrics.creator_addresses = [c.get('address') for c in creators_list if isinstance(c, dict) and c.get('address')]
                else:
                    self.logger.warning(f"Unexpected type for creators data: {type(creators_list)}")

            # 8. Trend Analysis
            self.logger.debug(f"Performing trend analysis for {token_address}...")
            if self.trend_analyzer:
                # Ensure TrendAnalysisService methods are called appropriately (async or sync)
                # Current TrendAnalysisService methods are sync, using asyncio.to_thread for now.
                # If they become async, direct await can be used.
                volume_trend_data = await asyncio.to_thread(self.trend_analyzer.analyze_volume_trend, pair_address)
                tx_trend_data = await asyncio.to_thread(self.trend_analyzer.analyze_transaction_trend, pair_data)
                
                metrics.volume_trend = volume_trend_data.get("trend", "unknown")
                metrics.volume_trend_score = float(volume_trend_data.get("trend_score", 0.0))
                metrics.volume_acceleration = float(volume_trend_data.get("acceleration_percent", 0.0))
                metrics.tx_count_trend = tx_trend_data.get("trend", "unknown")
                metrics.tx_trend_score = float(tx_trend_data.get("trend_score", 0.0))

                if metrics.volume_trend in ["strongly_increasing", "increasing"] and \
                   metrics.tx_count_trend in ["strongly_increasing", "increasing"]:
                    metrics.risk_factors.append(f"PositiveTrendSignal (Vol: {metrics.volume_trend}, TX: {metrics.tx_count_trend}, Accel: {metrics.volume_acceleration:.0f}%)")
            else:
                self.logger.warning("TrendAnalyzer not available, skipping trend analysis.")
            
            self.logger.debug(f"Whale tracking for {token_address} based on LP shares (placeholder for token holders)...")
            
            self.logger.info(f"Token enrichment for {metrics.symbol} completed in {time.time() - start_time:.2f}s")
            return metrics

        except Exception as e:
            self.logger.error(f"Error in comprehensive analysis for {pair_address} ({token_address}): {e}", exc_info=True)
            return None

    # Note: _analyze_whale_wallet_enhanced and _get_enhanced_token_metadata from VirtuosoGemFinder
    # have been partially integrated or their logic components are callable via injected services.
    # The _calculate_price_changes_with_jupiter logic is now part of FilteringService as an async version.