# Dynamic Token Discovery and Filter Relaxation Strategy

This document outlines the dynamic token discovery process implemented in `api/batch_api_manager.py`. The system employs a multi-layered fallback strategy with adaptive filter relaxation to ensure a consistent flow of potentially promising tokens for analysis, even when market conditions vary. All list-based discovery now utilizes the V3 `/defi/v3/token/list` endpoint for consistency and access to richer filtering and sorting capabilities. The `/defi/token_trending` endpoint is used for its specific purpose of fetching curated trending tokens.

## Core Concepts

1.  **Tiered Discovery Attempts**: The system makes several attempts to discover tokens, starting with the most promising strategies and endpoints, and falling back to broader or alternative methods if initial attempts yield insufficient results.
2.  **Filter Relaxation Levels**: A `filter_relaxation_level` (0, 1, 2) is used to adjust the strictness of the quality filters applied to raw tokens.
    *   **Level 0 (Strict)**: Standard, most stringent filter thresholds.
    *   **Level 1 (Relaxed)**: Metric thresholds (liquidity, market cap, holders, volume) are reduced (e.g., to 80% of base), and the minimum momentum score is slightly lowered.
    *   **Level 2 (Very Relaxed)**: Metric thresholds are further reduced (e.g., to 65% of base), and the minimum momentum score is lowered more significantly.
3.  **Minimum Yield Threshold**: A `min_yield_threshold` (e.g., 25% of `max_tokens` requested) determines if a discovery attempt has found "enough" tokens to proceed without further relaxation.
4.  **Recently Analyzed Cache**: A `recently_analyzed_tokens` set prevents reprocessing the same tokens within a defined Time-To-Live (TTL), forcing discovery of new candidates.

## Discovery Orchestration (`efficient_discovery_with_strict_filters`)

The `efficient_discovery_with_strict_filters` method orchestrates the discovery process:

1.  **Initialization**:
    *   Resets `recently_analyzed_tokens` if TTL has expired.
    *   Starts with `filter_relaxation_level = 0`.

2.  **Attempt 1: Primary V3 Discovery (Strict)**
    *   **Endpoint**: `/defi/v3/token/list`
    *   **Sort By**: `volume_1h_change_percent` (targets recent volume surges).
    *   **Filters**: Level 0 (Strict).
    *   **Outcome**:
        *   If `len(found_tokens) >= min_yield_threshold`, returns these tokens.
        *   Otherwise, sets `filter_relaxation_level = 1` and proceeds.

3.  **Attempt 2: Alternate V3 Discovery (Relaxed)**
    *   **Endpoint**: `/defi/v3/token/list`
    *   **Sort By**: `last_trade_unix_time` (targets very recent trading activity).
    *   **Filters**: Level 1 (Relaxed), or current `filter_relaxation_level`.
    *   **Outcome**:
        *   If `len(found_tokens) >= min_yield_threshold`, returns these tokens.
        *   Otherwise, (if still below threshold) sets `filter_relaxation_level = 2` and proceeds.

4.  **Attempt 3: Trending Discovery (More Relaxed)**
    *   **Endpoint**: `/defi/token_trending`
    *   **Sort By**: Default API sort (curated trending list).
    *   **Filters**: Level 2 (Very Relaxed), or current `filter_relaxation_level`, applied to the tokens returned by the trending endpoint.
    *   **Outcome**:
        *   If `len(found_tokens) >= min_yield_threshold`, returns these tokens.
        *   Proceeds if still insufficient, potentially merging with previous results if applicable or using trending as a new base if prior attempts found nothing.

5.  **Attempt 4: V3 Fallback - FDV Sort (Most Relaxed)**
    *   **Endpoint**: `/defi/v3/token/list`
    *   **Sort By**: `fdv` (Fully Diluted Valuation).
    *   **Filters**: Level 2 (Very Relaxed), or current `filter_relaxation_level`.
    *   **Outcome**:
        *   If `len(found_tokens) >= min_yield_threshold`, returns these tokens.
        *   Proceeds if still insufficient, potentially using these tokens if prior attempts yielded nothing.

6.  **Attempt 5: V3 Fallback - Liquidity Sort (Most Relaxed - Last Resort for V3 Lists)**
    *   **Endpoint**: `/defi/v3/token/list`
    *   **Sort By**: `liquidity`.
    *   **Filters**: Level 2 (Very Relaxed), or current `filter_relaxation_level`.
    *   **Outcome**: Returns any tokens found. This is the final attempt to get candidates from V3 list endpoints.

7.  **No Tokens Found**:
    *   If all attempts (even with maximum relaxation) yield no tokens, the `recently_analyzed_tokens` cache is cleared to ensure the next full discovery cycle starts fresh.

## Filter Application (`_apply_quality_filters`)

The `_apply_quality_filters` method is responsible for:

*   Accepting the `filter_relaxation_level`.
*   Adjusting its internal base thresholds for liquidity, market cap, holder count, 24h volume, and minimum momentum score based on the received `relaxation_factor` and `momentum_score_reduction` derived from the `filter_relaxation_level`.
*   Applying these (potentially relaxed) filters to the raw list of tokens.
*   Considering `is_recent_listing_flag` to potentially further ease momentum score requirements for very new tokens, in conjunction with the overall relaxation level.
*   Logging the applied relaxation level and the effective thresholds being used for transparency.

## Helper Discovery Methods

Methods like `_alternate_discovery`, `_trending_discovery`, `_fallback_v3_discovery_fdv_sort`, and `_fallback_v3_discovery_liquidity_sort`:

*   Are now passed the `current_filter_relaxation_level` from the orchestrator.
*   Pass this level down to `_apply_quality_filters`.
*   Return an empty list `[]` if they fail or if all fetched tokens are already in the `recently_analyzed_tokens` cache (or if the API call itself fails), signaling the orchestrator to try the next step in the fallback chain.

## Benefits of this Dynamic Approach

*   **Resilience**: More likely to find tokens even when specific market segments are quiet or when primary strategies yield few results.
*   **Adaptability**: Filters adjust to the "discoverability" of tokens; stricter when good candidates are plentiful, looser when they are scarce.
*   **Efficiency**: Still prioritizes high-quality signals with strict filters initially, only relaxing when necessary, thus not over-processing low-quality data by default.
*   **Improved Consistency**: Helps maintain a more steady stream of tokens for the downstream analysis pipeline by leveraging multiple V3 sorting strategies.
*   **Transparency**: Logging clearly indicates when and how filters are being relaxed and which discovery attempt is active.
*   **API Consistency**: Primarily uses the V3 `/defi/v3/token/list` endpoint for list-based discovery, simplifying understanding of API parameter usage.

This dynamic system aims to strike a balance between rigorous filtering for high-probability opportunities and the practical need to keep the analysis pipeline fed with candidates. 