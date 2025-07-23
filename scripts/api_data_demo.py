#!/usr/bin/env python3
"""
🧪 COMPREHENSIVE API DATA DEMONSTRATION
Shows all data points available from Pump.fun and LaunchLab APIs
"""

import json
import time
from datetime import datetime

def demo_pump_fun_api_data():
    """Demonstrate comprehensive Pump.fun API data points"""
    
    print("🔥 PUMP.FUN API COMPREHENSIVE DATA POINTS")
    print("=" * 70)
    print("Based on Bitquery API documentation and our integration")
    print()
    
    # Comprehensive Pump.fun data structure
    pump_fun_data = {
        "token_metadata": {
            "mint_address": "EQzpkp6w8ag3C5mGqr2cgSEXMEjdQ9q5r4o3KbHW8tB1",
            "symbol": "MOONCAT",
            "name": "Moon Cat Token",
            "creator_address": "7xKqR5mP8nQ2fV6wE3cH1dG4jL9sB2aF8iM3oN7pT4uX1zY6",
            "creation_timestamp": "2025-06-30T13:00:00Z",
            "total_supply": 1000000000,
            "decimals": 6,
            "metadata_uri": "https://pump.fun/EQzpkp6w8ag3C5mGqr2cgSEXMEjdQ9q5r4o3KbHW8tB1.json",
            "update_authority": "TSLvdd1pWpHVjahSpsvCXUbgwsL3JAcvokwaKt1eokM",
            "is_mutable": True,
            "is_fungible": True,
            "program_address": "6EF8rrecthR5Dkzon8Nwu78hRvfCKubJ14M5uBEwF6P"
        },
        "real_time_pricing": {
            "current_price_usd": 0.000002025,
            "current_price_sol": 0.000000015,
            "market_cap_usd": 2025,
            "market_cap_sol": 15.0,
            "ath_market_cap_usd": 8950.75,
            "ath_timestamp": "2025-06-30T12:30:00Z",
            "price_change_5m": 3.2,
            "price_change_1h": 12.5,
            "price_change_24h": 45.8,
            "velocity_usd_per_hour": 1250.0,
            "last_updated": time.time()
        },
        "bonding_curve_data": {
            "graduation_threshold_usd": 69000,
            "current_progress_pct": 2.93,
            "bonding_curve_stage": "STAGE_0_ULTRA_EARLY",
            "sol_in_bonding_curve": 5.67,
            "estimated_graduation_eta_hours": 55.2,
            "liquidity_burn_amount": 12000,
            "bonding_curve_velocity": 1250.0
        },
        "trade_analytics": {
            "volume_24h_usd": 89420.75,
            "volume_1h_usd": 15420.50,
            "volume_5m_usd": 1285.30,
            "trades_24h": 2847,
            "trades_1h": 187,
            "trades_5m": 23,
            "unique_traders_24h": 312,
            "unique_buyers_24h": 198,
            "unique_sellers_24h": 141,
            "buy_sell_ratio": 1.67,
            "avg_trade_size_usd": 31.42,
            "largest_trade_24h": 2840.50,
            "trade_frequency_per_minute": 1.98
        },
        "first_100_buyers": {
            "still_holding_count": 73,
            "still_holding_percentage": 73.0,
            "average_holding_time_hours": 4.2,
            "total_bought_usd": 12420.50,
            "average_entry_price": 0.000001850,
            "diamond_hands_score": 8.5
        },
        "holder_distribution": {
            "total_unique_holders": 847,
            "dev_current_holdings_pct": 9.5,
            "dev_tokens_sold": 5000000,
            "dev_usd_realized": 9250.00,
            "top_10_holders_pct": 34.2,
            "holders_under_1k_usd": 623,
            "holders_1k_to_10k_usd": 198,
            "holders_over_10k_usd": 26,
            "gini_coefficient": 0.72,
            "whale_concentration_score": 6.8
        },
        "enhanced_scoring_data": {
            "age_minutes": 127,
            "velocity_score": 9.2,
            "momentum_score": 8.7,
            "safety_score": 6.5,
            "graduation_risk": "VERY_LOW",
            "predicted_final_score": 82.3
        }
    }
    
    print("📋 TOKEN METADATA:")
    print(f"   �� Address: {pump_fun_data['token_metadata']['mint_address']}")
    print(f"   🏷️ Symbol: {pump_fun_data['token_metadata']['symbol']}")
    print(f"   👤 Creator: {pump_fun_data['token_metadata']['creator_address'][:10]}...")
    print(f"   📅 Created: {pump_fun_data['token_metadata']['creation_timestamp']}")
    print(f"   🔢 Supply: {pump_fun_data['token_metadata']['total_supply']:,}")
    
    print("\n📈 REAL-TIME PRICING:")
    print(f"   💰 Price: ${pump_fun_data['real_time_pricing']['current_price_usd']:.9f}")
    print(f"   📊 Market Cap: ${pump_fun_data['real_time_pricing']['market_cap_usd']:,}")
    print(f"   📈 24h Change: +{pump_fun_data['real_time_pricing']['price_change_24h']:.1f}%")
    print(f"   ⚡ Velocity: ${pump_fun_data['real_time_pricing']['velocity_usd_per_hour']:,}/hour")
    
    print("\n🌊 BONDING CURVE:")
    print(f"   🎯 Stage: {pump_fun_data['bonding_curve_data']['bonding_curve_stage']}")
    print(f"   📊 Progress: {pump_fun_data['bonding_curve_data']['current_progress_pct']:.2f}% to $69K")
    print(f"   ⏰ ETA: {pump_fun_data['bonding_curve_data']['estimated_graduation_eta_hours']:.1f} hours")
    print(f"   🔥 Burn Amount: ${pump_fun_data['bonding_curve_data']['liquidity_burn_amount']:,}")
    
    print("\n💹 TRADING ANALYTICS:")
    print(f"   📊 Volume (24h): ${pump_fun_data['trade_analytics']['volume_24h_usd']:,}")
    print(f"   🔄 Trades (24h): {pump_fun_data['trade_analytics']['trades_24h']:,}")
    print(f"   👥 Traders: {pump_fun_data['trade_analytics']['unique_traders_24h']}")
    print(f"   📈 Buy/Sell: {pump_fun_data['trade_analytics']['buy_sell_ratio']:.2f}")
    print(f"   ⚡ Frequency: {pump_fun_data['trade_analytics']['trade_frequency_per_minute']:.1f} trades/min")
    
    print("\n🏆 FIRST 100 BUYERS:")
    print(f"   �� Still Holding: {pump_fun_data['first_100_buyers']['still_holding_percentage']:.0f}%")
    print(f"   ⏰ Avg Hold Time: {pump_fun_data['first_100_buyers']['average_holding_time_hours']:.1f} hours")
    print(f"   💰 Total Bought: ${pump_fun_data['first_100_buyers']['total_bought_usd']:,}")
    print(f"   💎 Diamond Hands: {pump_fun_data['first_100_buyers']['diamond_hands_score']:.1f}/10")
    
    print("\n👥 HOLDER DISTRIBUTION:")
    print(f"   👤 Total Holders: {pump_fun_data['holder_distribution']['total_unique_holders']}")
    print(f"   �� Dev Holdings: {pump_fun_data['holder_distribution']['dev_current_holdings_pct']:.1f}%")
    print(f"   💰 Dev Realized: ${pump_fun_data['holder_distribution']['dev_usd_realized']:,}")
    print(f"   🐋 Whale Score: {pump_fun_data['holder_distribution']['whale_concentration_score']:.1f}/10")
    
    print("\n🎯 ENHANCED SCORING:")
    print(f"   ⏰ Age: {pump_fun_data['enhanced_scoring_data']['age_minutes']} minutes")
    print(f"   ⚡ Velocity: {pump_fun_data['enhanced_scoring_data']['velocity_score']:.1f}/10")
    print(f"   📈 Momentum: {pump_fun_data['enhanced_scoring_data']['momentum_score']:.1f}/10")
    print(f"   🛡️ Safety: {pump_fun_data['enhanced_scoring_data']['safety_score']:.1f}/10")
    print(f"   🎯 Final Score: {pump_fun_data['enhanced_scoring_data']['predicted_final_score']:.1f}/100")
    
    return pump_fun_data

if __name__ == "__main__":
    demo_pump_fun_api_data()
