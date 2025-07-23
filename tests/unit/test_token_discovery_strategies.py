import asyncio
import json
import logging
import time
from pathlib import Path
from unittest.mock import patch, MagicMock, mock_open, AsyncMock

import pytest

from core.token_discovery_strategies import (
    BaseTokenDiscoveryStrategy,
    VolumeMomentumStrategy,
    RecentListingsStrategy,
    PriceMomentumStrategy,
    LiquidityGrowthStrategy,
    HighTradingActivityStrategy
)
from api.birdeye_connector import BirdeyeAPI
from core.cache_manager import CacheManager
from services.rate_limiter_service import RateLimiterService
from core.config_manager import ConfigManager

# Mock data for BirdeyeAPI responses
MOCK_TOKEN_LIST_SUCCESS = {
    "data": {
        "tokens": [
            {
                "address": "tokenAddr1", "symbol": "TKN1", "name": "Token One",
                "volume24h": 100000.0, "priceChange24h": 5.0, "liquidity": 500000.0,
                "marketCap": 1000000.0, "createdTime": int(time.time()) - 86400 * 5, # 5 days ago
                "txns24h": 100, "holder": 500, "volume24h_change_percent": 10.0,
                "volume7d": 700000.0
            },
            {
                "address": "tokenAddr2", "symbol": "TKN2", "name": "Token Two",
                "volume24h": 200000.0, "priceChange24h": -2.0, "liquidity": 300000.0,
                "marketCap": 800000.0, "createdTime": int(time.time()) - 86400 * 10, # 10 days ago
                "txns24h": 150, "holder": 600, "volume24h_change_percent": -5.0,
                "volume7d": 1400000.0
            }
        ]
    },
    "success": True
}

MOCK_TOKEN_LIST_EMPTY = {
    "data": {"tokens": []},
    "success": True
}

MOCK_TOKEN_LIST_ERROR = {
    "data": {},
    "success": False,
    "message": "API error"
}

@pytest.fixture
def mock_logger():
    return MagicMock(spec=logging.Logger)

@pytest.fixture
def mock_birdeye_api():
    mock_api = MagicMock()
    mock_api.get_token_list = AsyncMock()
    return mock_api

@pytest.fixture
def tmp_storage_dir(tmp_path):
    storage_dir = tmp_path / "discovery_results"
    storage_dir.mkdir()
    return storage_dir

class TestBaseTokenDiscoveryStrategy:

    @pytest.fixture
    def base_strategy(self, mock_logger, tmp_storage_dir):
        strategy = BaseTokenDiscoveryStrategy(
            name="TestBaseStrategy",
            description="A base strategy for testing.",
            api_parameters={"limit": 10},
            min_consecutive_appearances=2,
            logger=mock_logger,
            storage_dir=str(tmp_storage_dir)
        )
        return strategy

    def test_initialization_new_history(self, base_strategy, mock_logger, tmp_storage_dir):
        assert base_strategy.name == "TestBaseStrategy"
        assert base_strategy.description == "A base strategy for testing."
        assert base_strategy.api_parameters == {"limit": 10}
        assert base_strategy.min_consecutive_appearances == 2
        assert base_strategy.logger == mock_logger
        assert base_strategy.storage_dir == tmp_storage_dir
        assert base_strategy.storage_file == tmp_storage_dir / "testbasestrategy_results.json"
        assert base_strategy.token_history == {"tokens": {}, "last_execution_time": 0}
        assert base_strategy.last_execution_time == 0

    def test_initialization_with_existing_valid_history(self, mock_logger, tmp_storage_dir):
        history_data = {
            "tokens": {"tokenAddr1": {"last_seen": 12345}},
            "last_execution_time": 123456
        }
        history_file = tmp_storage_dir / "existingstrategy_results.json"
        with open(history_file, 'w') as f:
            json.dump(history_data, f)

        strategy = BaseTokenDiscoveryStrategy(
            name="ExistingStrategy",
            description="Test existing history.",
            api_parameters={},
            logger=mock_logger,
            storage_dir=str(tmp_storage_dir)
        )
        assert strategy.token_history == history_data
        assert strategy.last_execution_time == 123456

    def test_initialization_with_corrupted_history(self, mock_logger, tmp_storage_dir):
        history_file = tmp_storage_dir / "corruptedstrategy_results.json"
        with open(history_file, 'w') as f:
            f.write("this is not json")

        strategy = BaseTokenDiscoveryStrategy(
            name="CorruptedStrategy",
            description="Test corrupted history.",
            api_parameters={},
            logger=mock_logger,
            storage_dir=str(tmp_storage_dir)
        )
        assert strategy.token_history == {"tokens": {}, "last_execution_time": 0}
        mock_logger.error.assert_called_once()
        assert "Error loading history" in mock_logger.error.call_args[0][0]

    @pytest.mark.asyncio
    async def test_execute_success(self, base_strategy, mock_birdeye_api, mock_logger):
        with patch('time.time', return_value=1000) as mock_time:
            results = await base_strategy.execute(mock_birdeye_api)

        mock_birdeye_api.get_token_list.assert_called_once_with(
            sort_by="volume_24h_usd", sort_type="desc", limit=10
        )
        assert len(results) == 2
        assert results[0]["address"] == "tokenAddr1"
        assert "strategy_data" in results[0]
        mock_logger.info.assert_any_call("Executing TestBaseStrategy strategy")
        mock_logger.info.assert_any_call("Strategy TestBaseStrategy found 2 tokens")
        
        # Check history update
        assert base_strategy.last_execution_time == 1000
        assert base_strategy.token_history["last_execution_time"] == 1000
        assert "tokenAddr1" in base_strategy.token_history["tokens"]
        assert base_strategy.token_history["tokens"]["tokenAddr1"]["last_seen"] == 1000

        # Check save_history was called (implicitly by checking file content or mocking save)
        with patch.object(base_strategy, 'save_history') as mock_save:
            await base_strategy.execute(mock_birdeye_api) # Execute again to trigger save
            mock_save.assert_called_once()


    @pytest.mark.asyncio
    async def test_execute_api_returns_empty(self, base_strategy, mock_birdeye_api, mock_logger):
        mock_birdeye_api.get_token_list.return_value = asyncio.Future()
        mock_birdeye_api.get_token_list.return_value.set_result(MOCK_TOKEN_LIST_EMPTY)
        
        results = await base_strategy.execute(mock_birdeye_api)
        assert len(results) == 0
        mock_logger.info.assert_any_call("Strategy TestBaseStrategy found 0 tokens")

    @pytest.mark.asyncio
    async def test_execute_api_returns_error(self, base_strategy, mock_birdeye_api, mock_logger):
        mock_birdeye_api.get_token_list.return_value = asyncio.Future()
        mock_birdeye_api.get_token_list.return_value.set_result(MOCK_TOKEN_LIST_ERROR)
        
        results = await base_strategy.execute(mock_birdeye_api)
        assert len(results) == 0
        expected_warning_msg = f"Strategy {base_strategy.name} API call failed: API error"
        mock_logger.warning.assert_called_with(expected_warning_msg)

    @pytest.mark.asyncio
    async def test_execute_api_exception(self, base_strategy, mock_birdeye_api, mock_logger):
        mock_birdeye_api.get_token_list.side_effect = Exception("API Call Failed")
        
        results = await base_strategy.execute(mock_birdeye_api)
        assert len(results) == 0
        mock_logger.error.assert_called_with("Error executing strategy TestBaseStrategy: API Call Failed")

    @pytest.mark.asyncio
    async def test_process_results(self, base_strategy):
        tokens_from_api = MOCK_TOKEN_LIST_SUCCESS["data"]["tokens"]
        mock_api = MagicMock() # Not used in this specific process_results but required by signature

        with patch('time.time', return_value=2000):
            processed_tokens = await base_strategy.process_results(tokens_from_api, mock_api)

        assert len(processed_tokens) == 2
        for token in processed_tokens:
            assert "strategy_data" in token
            assert token["strategy_data"]["strategy"] == base_strategy.name
            assert token["strategy_data"]["consecutive_appearances"] == 1
            assert token["strategy_data"]["first_seen"] == 2000
            assert token["strategy_data"]["appearances"] == [2000]
        
        # Verify token_history is updated
        assert "tokenAddr1" in base_strategy.token_history["tokens"]
        assert base_strategy.token_history["tokens"]["tokenAddr1"]["consecutive_appearances"] == 1

    def test_track_token_new_token(self, base_strategy):
        timestamp = 3000
        token_data = {"address": "newToken", "symbol": "NEW"}
        
        history_entry = base_strategy.track_token("newToken", token_data, timestamp)

        assert "newToken" in base_strategy.token_history["tokens"]
        entry = base_strategy.token_history["tokens"]["newToken"]
        assert entry["first_seen"] == timestamp
        assert entry["appearances"] == [timestamp]
        assert entry["consecutive_appearances"] == 1
        assert entry["last_seen"] == timestamp
        assert entry["last_data"] == token_data
        assert history_entry == entry
    
    def test_track_token_existing_token_consecutive(self, base_strategy):
        # Initial track
        base_strategy.track_token("existingToken", {"symbol": "EXT"}, 3000)
        
        # Consecutive track (within 8 hours)
        # 8 hours = 8 * 60 * 60 = 28800 seconds
        timestamp_consecutive = 3000 + 28799 
        token_data_updated = {"symbol": "EXTv2"}
        history_entry = base_strategy.track_token("existingToken", token_data_updated, timestamp_consecutive)
        
        entry = base_strategy.token_history["tokens"]["existingToken"]
        assert entry["first_seen"] == 3000
        assert entry["appearances"] == [3000, timestamp_consecutive]
        assert entry["consecutive_appearances"] == 2
        assert entry["last_seen"] == timestamp_consecutive
        assert entry["last_data"] == token_data_updated
        assert history_entry == entry

    def test_track_token_existing_token_non_consecutive(self, base_strategy):
        base_strategy.track_token("existingToken", {"symbol": "EXT"}, 3000)
        
        # Non-consecutive track (more than 8 hours)
        timestamp_non_consecutive = 3000 + 28801 
        token_data_updated = {"symbol": "EXTv3"}
        base_strategy.track_token("existingToken", token_data_updated, timestamp_non_consecutive)
        
        entry = base_strategy.token_history["tokens"]["existingToken"]
        assert entry["first_seen"] == 3000 # First seen remains original
        assert entry["appearances"] == [3000, timestamp_non_consecutive]
        assert entry["consecutive_appearances"] == 1 # Reset
        assert entry["last_seen"] == timestamp_non_consecutive
        assert entry["last_data"] == token_data_updated

    def test_track_token_appearance_list_capped(self, base_strategy):
        token_address = "cappedToken"
        for i in range(15):
            base_strategy.track_token(token_address, {"val": i}, 4000 + i * 100) # Ensure non-consecutive for simplicity here

        entry = base_strategy.token_history["tokens"][token_address]
        assert len(entry["appearances"]) == 10 # Should be capped at 10
        # Last 10 appearances, so 4000 + 5*100 to 4000 + 14*100
        expected_appearances = [4000 + i * 100 for i in range(5, 15)]
        assert entry["appearances"] == expected_appearances


    def test_get_promising_tokens(self, base_strategy):
        base_strategy.min_consecutive_appearances = 3
        base_strategy.token_history["tokens"] = {
            "promising1": {"consecutive_appearances": 3, "last_data": {}},
            "not_promising1": {"consecutive_appearances": 2, "last_data": {}},
            "promising2": {"consecutive_appearances": 5, "last_data": {}},
            "not_promising2": {"consecutive_appearances": 1, "last_data": {}},
        }
        promising = base_strategy.get_promising_tokens()
        assert sorted(promising) == sorted(["promising1", "promising2"])

    def test_get_promising_tokens_empty(self, base_strategy):
         base_strategy.min_consecutive_appearances = 3
         base_strategy.token_history["tokens"] = {
            "not_promising1": {"consecutive_appearances": 2, "last_data": {}},
         }
         assert base_strategy.get_promising_tokens() == []

    def test_save_and_load_history(self, base_strategy, tmp_storage_dir):
        base_strategy.token_history = {
            "tokens": {"tokenA": {"data": "valueA", "consecutive_appearances": 1}},
            "last_execution_time": 5000
        }
        base_strategy.save_history()
        
        assert base_strategy.storage_file.exists()
        
        # Create new strategy instance to load the saved history
        new_strategy = BaseTokenDiscoveryStrategy(
            name=base_strategy.name,
            description=base_strategy.description,
            api_parameters=base_strategy.api_parameters,
            logger=base_strategy.logger,
            storage_dir=str(tmp_storage_dir) # Use the same tmp_storage_dir
        )
        assert new_strategy.token_history == base_strategy.token_history

    def test_save_history_io_error(self, base_strategy, mock_logger):
        with patch('builtins.open', mock_open()) as mocked_file:
            mocked_file.side_effect = IOError("Disk full")
            base_strategy.save_history()
        mock_logger.error.assert_called_once()
        assert "Error saving history" in mock_logger.error.call_args[0][0]
        assert "Disk full" in mock_logger.error.call_args[0][0]

    def test_clean_expired_tokens(self, base_strategy, mock_logger):
        current_time = 1000000
        max_age_days = 7
        max_age_seconds = max_age_days * 24 * 60 * 60 # 604800

        base_strategy.token_history["tokens"] = {
            "expiredToken1": {"last_seen": current_time - max_age_seconds - 1, "last_data": {}},
            "activeToken1": {"last_seen": current_time - max_age_seconds + 1, "last_data": {}},
            "expiredToken2": {"last_seen": current_time - max_age_seconds * 2, "last_data": {}}, # much older
            "activeToken2": {"last_seen": current_time - 100, "last_data": {}}, # very recent
        }
        
        with patch('time.time', return_value=current_time):
            with patch.object(base_strategy, 'save_history') as mock_save:
                base_strategy.clean_expired_tokens(max_age_days=max_age_days)

        assert "expiredToken1" not in base_strategy.token_history["tokens"]
        assert "expiredToken2" not in base_strategy.token_history["tokens"]
        assert "activeToken1" in base_strategy.token_history["tokens"]
        assert "activeToken2" in base_strategy.token_history["tokens"]
        
        mock_logger.info.assert_called_with("Removed 2 expired tokens from TestBaseStrategy")
        mock_save.assert_called_once()

    def test_clean_expired_tokens_no_expired(self, base_strategy, mock_logger):
        current_time = 1000000
        max_age_days = 7
        
        base_strategy.token_history["tokens"] = {
            "activeToken1": {"last_seen": current_time - 100, "last_data": {}},
        }
        
        with patch('time.time', return_value=current_time):
            with patch.object(base_strategy, 'save_history') as mock_save:
                 base_strategy.clean_expired_tokens(max_age_days=max_age_days)

        assert "activeToken1" in base_strategy.token_history["tokens"]
        mock_logger.info.assert_not_called() # No "Removed x expired tokens"
        mock_save.assert_not_called()


# --- Tests for Specific Strategy Implementations ---

class TestVolumeMomentumStrategy:
    @pytest.fixture
    def strategy(self, mock_logger, tmp_storage_dir):
        return VolumeMomentumStrategy(logger=mock_logger) # storage_dir is default

    def test_volume_momentum_initialization(self, strategy):
        assert strategy.name == "Volume Momentum Strategy"
        assert strategy.api_parameters["sort_by"] == "volume_24h_change_percent"
        assert strategy.risk_management["suspicious_volume_multiplier"] == 3.0

    @pytest.mark.asyncio
    async def test_volume_momentum_process_results_normal(self, strategy, mock_birdeye_api, mock_logger):
        token_normal_volume = {
            "address": "normalVol", "symbol": "NVL", "name": "Normal Volume",
            "volume24h": 10000, "volume7d": 70000, # 24h volume is 1/7 of 7d, normal
            "strategy_data": {"strategy": strategy.name, "consecutive_appearances": 1, "first_seen": 1000, "appearances": [1000]}
        } # Added strategy_data as it's expected by super().process_results

        # Mocking super().process_results to return the token directly for isolated testing
        with patch.object(BaseTokenDiscoveryStrategy, 'process_results', return_value=asyncio.Future()) as mock_super_process:
            mock_super_process.return_value.set_result([token_normal_volume])
            filtered_tokens = await strategy.process_results([token_normal_volume], mock_birdeye_api)
        
        assert len(filtered_tokens) == 1
        assert filtered_tokens[0]["address"] == "normalVol"

    @pytest.mark.asyncio
    async def test_volume_momentum_process_results_suspicious_spike(self, strategy, mock_birdeye_api, mock_logger):
        # 24h volume (60k) is more than 3x (suspicious_volume_multiplier) 
        # the average daily volume from 7d (70k/7 = 10k, 10k * 4/7 ~ 5.7k per day, threshold for spike check using volume_7d/4)
        # Let's simplify: volume_24h (60000) > (volume_7d (70000) / 4 (quarter for avg day) * multiplier (3.0))
        # 60000 > (17500 * 3.0) => 60000 > 52500, so it's suspicious
        token_suspicious_volume = {
            "address": "suspVol", "symbol": "SVL", "name": "Suspicious Volume",
            "volume24h": 60000, "volume7d": 70000, 
            "strategy_data": {"strategy": strategy.name, "consecutive_appearances": 1, "first_seen": 1000, "appearances": [1000]}
        }
        with patch.object(BaseTokenDiscoveryStrategy, 'process_results', return_value=asyncio.Future()) as mock_super_process:
            mock_super_process.return_value.set_result([token_suspicious_volume])
            filtered_tokens = await strategy.process_results([token_suspicious_volume], mock_birdeye_api)
        
        assert len(filtered_tokens) == 0
        mock_logger.warning.assert_called_with("Skipping token SVL due to suspicious volume spike")

    @pytest.mark.asyncio
    async def test_volume_momentum_process_results_volume7d_zero(self, strategy, mock_birdeye_api, mock_logger):
        # volume7d is 0, so it's estimated as volume_24h * 7.
        # If volume_24h is 10000, volume7d_estimated is 70000.
        # Condition: 10000 > (70000 / 4 * 3.0) => 10000 > 52500 is False. So, not suspicious.
        token_volume7d_zero = {
            "address": "vol7dZero", "symbol": "V7Z", "name": "Volume 7d Zero",
            "volume24h": 10000, "volume7d": 0, # or None
             "strategy_data": {"strategy": strategy.name, "consecutive_appearances": 1, "first_seen": 1000, "appearances": [1000]}
        }
        with patch.object(BaseTokenDiscoveryStrategy, 'process_results', return_value=asyncio.Future()) as mock_super_process:
            mock_super_process.return_value.set_result([token_volume7d_zero])
            filtered_tokens = await strategy.process_results([token_volume7d_zero], mock_birdeye_api)
        assert len(filtered_tokens) == 1
        assert filtered_tokens[0]["address"] == "vol7dZero"
        mock_logger.warning.assert_not_called()

class TestRecentListingsStrategy:
    @pytest.fixture
    def strategy(self, mock_logger, mock_birdeye_api, tmp_path):
        # mock_birdeye_api is kept as an arg because tests using this fixture might pass it to strategy methods.
        # It's not used in the RecentListingsStrategy constructor itself.
        with patch.object(BaseTokenDiscoveryStrategy, 'load_history', return_value={"tokens": {}, "last_execution_time": 0}) as mock_load_history:
            # RecentListingsStrategy constructor only takes `logger`.
            # `storage_dir` (and thus `storage_file`) is determined by BaseTokenDiscoveryStrategy's defaults or its own logic.
            # By patching `load_history`, we ensure a fresh start for `self.token_history`.
            strat = RecentListingsStrategy(logger=mock_logger)
            
            # To ensure any save_history calls in tests use tmp_path, we can override storage_file and storage_dir.
            # This makes tests more hermetic regarding file system state.
            test_specific_storage_dir = tmp_path / "test_strat_data" / strat.name.lower().replace(' ', '_')
            test_specific_storage_dir.mkdir(parents=True, exist_ok=True)
            strat.storage_dir = test_specific_storage_dir
            strat.storage_file = test_specific_storage_dir / "token_history.json"
            
            # strat.token_history is already fresh due to the patched load_history.
        return strat

    # Test methods like test_recent_listings_initialization will use this fixture.
    # They will receive mock_birdeye_api as a separate argument if they need to pass it to strategy methods.

    @pytest.mark.asyncio
    async def test_recent_listings_initialization(self, strategy, mock_logger): 
        assert strategy.name == "Recent Listings Strategy"
        assert strategy.api_parameters["sort_by"] == "recent_listing_time"
        assert strategy.min_consecutive_appearances == 2
        assert strategy.risk_management["max_allocation_percentage"] == 2.5
        assert strategy.risk_management["min_days_since_listing"] == 2

    @pytest.mark.asyncio
    async def test_recent_listings_process_results_valid(self, strategy, mock_birdeye_api, mock_logger):
        current_time = int(time.time())
        valid_token_address = "validNewToken"
        
        current_api_liquidity = 1000
        previously_recorded_first_liquidity = 900

        current_token_api_data = {
            "address": valid_token_address, 
            "symbol": "VNT", 
            "createdTime": current_time - (86400 * 3), # 3 days old
            "liquidity": current_api_liquidity
        }

        time_of_previous_processing = current_time - 86400
        strategy.token_history["tokens"][valid_token_address] = {
            "first_seen": time_of_previous_processing - 3600, 
            "appearances": [time_of_previous_processing - 3600, time_of_previous_processing],
            "consecutive_appearances": 2,
            "last_seen": time_of_previous_processing,
            "last_data": { 
                "address": valid_token_address, "symbol": "VNT", 
                "createdTime": current_token_api_data["createdTime"],
                "liquidity": previously_recorded_first_liquidity 
            },
            "first_liquidity": previously_recorded_first_liquidity
        }
        strategy.last_execution_time = time_of_previous_processing

        async def mock_base_process_results_behavior(tokens_from_api_list, birdeye_api_arg):
            base_output_list = []
            for token_api_data_item in tokens_from_api_list:
                addr = token_api_data_item["address"]
                strategy.track_token(addr, token_api_data_item, current_time)
                history_after_track_token = strategy.token_history["tokens"][addr]
                token_for_downstream_strategy = token_api_data_item.copy()
                token_for_downstream_strategy["strategy_data"] = {
                    "strategy": strategy.name, 
                    "consecutive_appearances": history_after_track_token["consecutive_appearances"],
                    "first_seen": history_after_track_token["first_seen"],
                    "appearances": history_after_track_token["appearances"]
                }
                base_output_list.append(token_for_downstream_strategy)
            return base_output_list

        with patch.object(BaseTokenDiscoveryStrategy, 'process_results', side_effect=mock_base_process_results_behavior):
            with patch('time.time', return_value=current_time): 
                 filtered_tokens = await strategy.process_results([current_token_api_data], mock_birdeye_api)
    
        assert len(filtered_tokens) == 1, f"Token {valid_token_address} should have passed RecentListingsStrategy filters"
        output_token = filtered_tokens[0]
        assert output_token["address"] == valid_token_address

        output_token_strategy_data = output_token.get("strategy_data", {})
        assert "first_liquidity_recorded_by_recent_strat" not in output_token_strategy_data, \
            "'first_liquidity_recorded_by_recent_strat' should not be in output strategy_data if first_liquidity was read from history."

        history_entry = strategy.token_history["tokens"][valid_token_address]
        assert history_entry["first_liquidity"] == previously_recorded_first_liquidity, \
            "The first_liquidity in history should remain unchanged."
        assert history_entry["last_data"]["liquidity"] == current_api_liquidity, \
            "last_data.liquidity in history should be updated to current API liquidity by track_token."

    @pytest.mark.asyncio
    async def test_recent_listings_process_results_too_recent(self, strategy, mock_birdeye_api, mock_logger):
        current_time = int(time.time())
        too_recent_token = {
            "address": "tooNew", "symbol": "TNW", "createdTime": current_time - (86400 * 1), # 1 day old
            "liquidity": 1000,
            "strategy_data": {}
        } # min_days_since_listing is 2
        with patch.object(BaseTokenDiscoveryStrategy, 'process_results', return_value=asyncio.Future()) as mock_super_process:
            mock_super_process.return_value.set_result([too_recent_token])
            with patch('time.time', return_value=current_time):
                filtered_tokens = await strategy.process_results([too_recent_token], mock_birdeye_api)
        
        assert len(filtered_tokens) == 0
        # No specific log for this, it's just skipped

    @pytest.mark.asyncio
    async def test_recent_listings_process_results_liquidity_decreased(self, strategy, mock_birdeye_api, mock_logger):
        current_time = int(time.time())
        token_liq_decrease = {
            "address": "liqDec", "symbol": "LDC", "createdTime": current_time - (86400 * 3),
            "liquidity": 500, # Current liquidity
            # Mock that it was seen before with higher liquidity
            "strategy_data": {"first_liquidity": 1000, "first_seen": current_time - 86400, "appearances": [current_time - 86400]}
        }
        with patch.object(BaseTokenDiscoveryStrategy, 'process_results', return_value=asyncio.Future()) as mock_super_process:
            mock_super_process.return_value.set_result([token_liq_decrease])
            with patch('time.time', return_value=current_time):
                 filtered_tokens = await strategy.process_results([token_liq_decrease], mock_birdeye_api)
        
        assert len(filtered_tokens) == 0
        
    @pytest.mark.asyncio
    async def test_recent_listings_process_results_first_time_seen_stores_liquidity(self, strategy, mock_birdeye_api):
        # 'strategy' fixture now ensures a fresh token_history due to patched load_history
        test_current_time = int(time.time())
        first_seen_token_data_from_api = {
            "address": "firstLiq", "symbol": "FLQ", "createdTime": test_current_time - (86400 * 3),
            "liquidity": 1500
        }
    
        async def mock_super_process_results_behavior(tokens_list_from_api, api_arg):
            processed_by_base = []
            for token_api_data in tokens_list_from_api:
                addr = token_api_data["address"]
                strategy.track_token(addr, token_api_data, test_current_time) 
                history_entry_after_track = strategy.token_history["tokens"][addr]
                output_token = token_api_data.copy()
                output_token["strategy_data"] = { 
                    "strategy": strategy.name, 
                    "consecutive_appearances": history_entry_after_track["consecutive_appearances"],
                    "first_seen": history_entry_after_track["first_seen"],
                    "appearances": history_entry_after_track["appearances"]
                }
                processed_by_base.append(output_token)
            return processed_by_base
    
        with patch.object(BaseTokenDiscoveryStrategy, 'process_results', side_effect=mock_super_process_results_behavior):
            with patch('time.time', return_value=test_current_time): 
                filtered_tokens = await strategy.process_results([first_seen_token_data_from_api], mock_birdeye_api)
    
        assert len(filtered_tokens) == 1
        assert filtered_tokens[0]["address"] == "firstLiq"
        
        output_strategy_data = filtered_tokens[0]["strategy_data"]
        
        assert "first_liquidity_recorded_by_recent_strat" in output_strategy_data
        assert output_strategy_data["first_liquidity_recorded_by_recent_strat"] == 1500
        
        assert strategy.token_history["tokens"]["firstLiq"]["first_liquidity"] == 1500


class TestPriceMomentumStrategy:
    @pytest.fixture
    def strategy(self, mock_logger, tmp_storage_dir):
        return PriceMomentumStrategy(logger=mock_logger)

    def test_price_momentum_initialization(self, strategy):
        assert strategy.name == "Price Momentum Strategy"
        assert strategy.api_parameters["sort_by"] == "price_change_24h_percent"
        assert strategy.min_consecutive_appearances == 2

    @pytest.mark.asyncio
    async def test_price_momentum_process_results_valid(self, strategy, mock_birdeye_api, mock_logger):
        valid_token = {
            "address": "validPrice", "symbol": "VPC", "priceChange24h": 30, "volumeChange24h": 20,
            "strategy_data": {}
        } # priceChange 30% < 50%; volumeChange 20% >= priceChange 30% * 0.5 (15)
        with patch.object(BaseTokenDiscoveryStrategy, 'process_results', return_value=asyncio.Future()) as mock_super_process:
            mock_super_process.return_value.set_result([valid_token])
            filtered_tokens = await strategy.process_results([valid_token], mock_birdeye_api)
        
        assert len(filtered_tokens) == 1
        assert filtered_tokens[0]["address"] == "validPrice"

    @pytest.mark.asyncio
    async def test_price_momentum_process_results_excessive_price_increase(self, strategy, mock_birdeye_api, mock_logger):
        excessive_price_token = {
            "address": "exPrice", "symbol": "EPC", "priceChange24h": 60, "volumeChange24h": 40,
             "strategy_data": {}
        } # priceChange 60% > 50%
        with patch.object(BaseTokenDiscoveryStrategy, 'process_results', return_value=asyncio.Future()) as mock_super_process:
            mock_super_process.return_value.set_result([excessive_price_token])
            filtered_tokens = await strategy.process_results([excessive_price_token], mock_birdeye_api)
        
        assert len(filtered_tokens) == 0
        mock_logger.warning.assert_called_with("Skipping token EPC due to excessive 24h price increase: 60%")

    @pytest.mark.asyncio
    async def test_price_momentum_process_results_volume_not_matching(self, strategy, mock_birdeye_api, mock_logger):
        low_volume_token = {
            "address": "lowVol", "symbol": "LVC", "priceChange24h": 30, "volumeChange24h": 10,
            "strategy_data": {}
        } # priceChange 30% < 50%; volumeChange 10% < priceChange 30% * 0.5 (15)
        with patch.object(BaseTokenDiscoveryStrategy, 'process_results', return_value=asyncio.Future()) as mock_super_process:
            mock_super_process.return_value.set_result([low_volume_token])
            filtered_tokens = await strategy.process_results([low_volume_token], mock_birdeye_api)
        
        assert len(filtered_tokens) == 0
        mock_logger.warning.assert_called_with("Skipping token LVC due to volume not matching price growth")

class TestLiquidityGrowthStrategy:
    @pytest.fixture
    def strategy(self, mock_logger, tmp_storage_dir):
        return LiquidityGrowthStrategy(logger=mock_logger)

    def test_liquidity_growth_initialization(self, strategy):
        assert strategy.name == "Liquidity Growth Strategy"
        assert strategy.api_parameters["sort_by"] == "liquidity"

    @pytest.mark.asyncio
    async def test_liquidity_growth_process_results_valid(self, strategy, mock_birdeye_api, mock_logger):
        valid_token = {
            "address": "validLiq", "symbol": "VLQ", "liquidity": 100000, "marketCap": 1000000, # ratio 0.1 >= 0.05
            "holder": 500,
            # Mock previous data showing holder growth
            "strategy_data": {"last_data": {"holder": 490}, "consecutive_appearances":1} 
        }
        
        async def mock_super_call(tokens, api):
            processed = []
            for t in tokens:
                 # Simulate super().process_results's effect on token_history for 'last_data' access
                strategy.token_history["tokens"][t['address']] = {
                    "last_data": t.get("strategy_data", {}).get("last_data", {}), # Use provided last_data
                    "consecutive_appearances": t.get("strategy_data", {}).get("consecutive_appearances", 1)
                }
                t_copy = t.copy()
                t_copy['strategy_data'] = strategy.token_history['tokens'][t['address']].copy()
                t_copy['strategy_data']['strategy'] = strategy.name
                processed.append(t_copy)
            return processed

        with patch.object(BaseTokenDiscoveryStrategy, 'process_results', side_effect=mock_super_call):
            filtered_tokens = await strategy.process_results([valid_token], mock_birdeye_api)
        
        assert len(filtered_tokens) == 1
        assert filtered_tokens[0]["address"] == "validLiq"
        assert filtered_tokens[0]["liq_to_mcap_ratio"] == 0.1

    @pytest.mark.asyncio
    async def test_liquidity_growth_process_results_low_liq_to_mcap(self, strategy, mock_birdeye_api, mock_logger):
        low_ratio_token = {
            "address": "lowRatio", "symbol": "LRT", "liquidity": 40000, "marketCap": 1000000, # ratio 0.04 < 0.05
            "holder": 500,
            "strategy_data": {"last_data": {"holder": 490}}
        }
        with patch.object(BaseTokenDiscoveryStrategy, 'process_results', return_value=asyncio.Future()) as mock_super_process:
            mock_super_process.return_value.set_result([low_ratio_token])
            filtered_tokens = await strategy.process_results([low_ratio_token], mock_birdeye_api)
        assert len(filtered_tokens) == 0

    @pytest.mark.asyncio
    async def test_liquidity_growth_process_results_holder_not_growing(self, strategy, mock_birdeye_api, mock_logger):
        stagnant_holder_token = {
            "address": "stagHold", "symbol": "SHT", "liquidity": 100000, "marketCap": 1000000,
            "holder": 500,
            # Mock previous data showing same or lower holder count
            "strategy_data": {"last_data": {"holder": 500}, "consecutive_appearances": 1} 
        }
        async def mock_super_call(tokens, api): # Same mock as in valid test
            processed = []
            for t in tokens:
                strategy.token_history["tokens"][t['address']] = {
                    "last_data": t.get("strategy_data", {}).get("last_data", {}),
                    "consecutive_appearances": t.get("strategy_data", {}).get("consecutive_appearances", 1)
                }
                t_copy = t.copy()
                t_copy['strategy_data'] = strategy.token_history['tokens'][t['address']].copy()
                t_copy['strategy_data']['strategy'] = strategy.name
                processed.append(t_copy)
            return processed

        with patch.object(BaseTokenDiscoveryStrategy, 'process_results', side_effect=mock_super_call):
            filtered_tokens = await strategy.process_results([stagnant_holder_token], mock_birdeye_api)
        assert len(filtered_tokens) == 0


class TestHighTradingActivityStrategy:
    @pytest.fixture
    def strategy(self, mock_logger, tmp_storage_dir):
        return HighTradingActivityStrategy(logger=mock_logger)

    def test_high_trading_activity_initialization(self, strategy):
        assert strategy.name == "High Trading Activity Strategy"
        assert strategy.api_parameters["sort_by"] == "trade_24h_count"

    @pytest.mark.asyncio
    async def test_high_trading_activity_process_results_valid(self, strategy, mock_birdeye_api, mock_logger):
        valid_token = {
            "address": "validTrade", "symbol": "VTR", "txns24h": 400, "marketCap": 1000000, # trades_per_mcap 400 <= 500
             "strategy_data": {}
        }
        with patch.object(BaseTokenDiscoveryStrategy, 'process_results', return_value=asyncio.Future()) as mock_super_process:
            mock_super_process.return_value.set_result([valid_token])
            filtered_tokens = await strategy.process_results([valid_token], mock_birdeye_api)
        
        assert len(filtered_tokens) == 1
        assert filtered_tokens[0]["address"] == "validTrade"
        assert filtered_tokens[0]["trades_per_mcap"] == 400.0

    @pytest.mark.asyncio
    async def test_high_trading_activity_process_results_wash_trading(self, strategy, mock_birdeye_api, mock_logger):
        wash_trade_token = {
            "address": "washTrade", "symbol": "WTR", "txns24h": 600, "marketCap": 1000000, # trades_per_mcap 600 > 500
            "strategy_data": {}
        }
        with patch.object(BaseTokenDiscoveryStrategy, 'process_results', return_value=asyncio.Future()) as mock_super_process:
            mock_super_process.return_value.set_result([wash_trade_token])
            filtered_tokens = await strategy.process_results([wash_trade_token], mock_birdeye_api)
        
        assert len(filtered_tokens) == 0
        mock_logger.warning.assert_called_with("Skipping token WTR due to potential wash trading")

    @pytest.mark.asyncio
    async def test_high_trading_activity_zero_market_cap(self, strategy, mock_birdeye_api, mock_logger):
        # Should not error, and should pass through if marketCap is 0 (ratio check is skipped)
        zero_mcap_token = {
            "address": "zeroCap", "symbol": "ZMC", "txns24h": 100, "marketCap": 0,
            "strategy_data": {}
        }
        with patch.object(BaseTokenDiscoveryStrategy, 'process_results', return_value=asyncio.Future()) as mock_super_process:
            mock_super_process.return_value.set_result([zero_mcap_token])
            filtered_tokens = await strategy.process_results([zero_mcap_token], mock_birdeye_api)

        assert len(filtered_tokens) == 1
        assert filtered_tokens[0]["address"] == "zeroCap"
        assert "trades_per_mcap" not in filtered_tokens[0] # Ratio calculation skipped
        mock_logger.warning.assert_not_called()