#!/usr/bin/env python3
"""
🚀 LAUNCHLAB API DATA DEMONSTRATION  
Shows all data points available from LaunchLab API
"""

import json
import time
from datetime import datetime

def demo_launchlab_api_data():
    """Demonstrate comprehensive LaunchLab API data points"""
    
    print("🚀 LAUNCHLAB API COMPREHENSIVE DATA POINTS")
    print("=" * 70)
    print("Based on Raydium LaunchLab integration and SOL-native metrics")
    print()
    
    # Comprehensive LaunchLab data structure
    launchlab_data = {
        "token_metadata": {
            "mint_address": "BcR3nQ8fV2wE5cH8dG1jL4sA7fG9iN6oP3qT5uY2xZ8",
            "symbol": "SOLROCKET",
            "name": "Sol Rocket Token",
            "creator_address": "4xKqR8mP2nQ5fV9wE3cH7dG4jL5sB2aF8iM5oN2pT4uX7zY6",
            "creation_timestamp": "2025-06-30T12:45:00Z",
            "total_supply": 1000000000,
            "decimals": 9,
            "raydium_program": "27G8MtK7VtTcCHkpASjSDdkWWYfoqT6ggEuKidVJidD4",
            "is_launchlab_token": True
        },
        "sol_bonding_curve": {
            "sol_raised_current": 23.5,
            "sol_graduation_target": 85.0,
            "graduation_progress_pct": 27.6,
            "sol_remaining": 61.5,
            "current_sol_price": 135.0,
            "estimated_graduation_eta_hours": 22.0,
            "sol_velocity_per_hour": 2.8,
            "stage": "LAUNCHLAB_EARLY_MOMENTUM"
        },
        "market_data_sol": {
            "current_price_sol": 0.0000235,
            "current_price_usd": 0.00317,
            "market_cap_sol": 23.5,
            "market_cap_usd": 3172.50,
            "ath_market_cap_sol": 35.9,
            "ath_market_cap_usd": 4846.50,
            "price_change_15m": 5.2,
            "price_change_1h": 18.7,
            "price_change_24h": 156.8,
            "velocity_sol_per_hour": 2.8,
            "velocity_usd_per_hour": 378.0
        },
        "trade_analytics_sol": {
            "volume_24h_sol": 45.8,
            "volume_24h_usd": 6183.0,
            "volume_1h_sol": 3.8,
            "trades_24h": 284,
            "trades_1h": 23,
            "unique_traders_24h": 89,
            "unique_buyers_24h": 58,
            "unique_sellers_24h": 41,
            "buy_sell_ratio_sol": 1.89,
            "avg_trade_size_sol": 0.161,
            "largest_trade_sol": 5.2,
            "sol_trade_frequency": 12.1
        },
        "holder_analytics": {
            "total_holders": 234,
            "dev_holdings_pct": 12.8,
            "dev_sol_withdrawn": 2.1,
            "dev_profit_sol": 2.1,
            "dev_profit_usd": 283.50,
            "whale_holders_1sol_plus": 28,
            "whale_holders_5sol_plus": 8,
            "whale_holders_10sol_plus": 3,
            "concentration_score": 5.8,
            "sol_distribution_gini": 0.68
        },
        "strategic_recommendations": {
            "current_stage": "LAUNCHLAB_EARLY_MOMENTUM",
            "profit_potential": "5-15x",
            "risk_level": "VERY_HIGH",
            "recommended_wallet": "discovery_scout",
            "position_size_pct": 2.0,
            "entry_strategy": "MOMENTUM_ENTRY",
            "exit_recommendation": "PARTIAL_AT_50_SOL",
            "optimal_entry_window": "CURRENT",
            "graduation_timing": "22_HOURS",
            "risk_reward_ratio": 7.5
        },
        "graduation_analysis": {
            "graduation_probability": 0.87,
            "graduation_eta_hours": 22.0,
            "graduation_confidence": 0.82,
            "sol_needed_daily": 2.8,
            "current_daily_rate": 3.1,
            "graduation_surplus": 0.3,
            "risk_factors": ["whale_sell_pressure", "sol_price_volatility"],
            "graduation_catalysts": ["momentum_acceleration", "whale_accumulation"]
        },
        "enhanced_scoring_data": {
            "age_minutes": 90,
            "sol_velocity_score": 8.9,
            "momentum_score": 8.7,
            "graduation_score": 9.1,
            "safety_score": 7.3,
            "strategic_score": 8.8,
            "predicted_final_score": 78.4
        }
    }
    
    print("📋 TOKEN METADATA:")
    print(f"   🆔 Address: {launchlab_data['token_metadata']['mint_address']}")
    print(f"   🏷️ Symbol: {launchlab_data['token_metadata']['symbol']}")
    print(f"   👤 Creator: {launchlab_data['token_metadata']['creator_address'][:10]}...")
    print(f"   📅 Created: {launchlab_data['token_metadata']['creation_timestamp']}")
    print(f"   🚀 Platform: Raydium LaunchLab")
    
    print("\n🌊 SOL BONDING CURVE:")
    print(f"   💰 SOL Raised: {launchlab_data['sol_bonding_curve']['sol_raised_current']:.1f} SOL")
    print(f"   🎯 Target: {launchlab_data['sol_bonding_curve']['sol_graduation_target']:.0f} SOL")
    print(f"   📊 Progress: {launchlab_data['sol_bonding_curve']['graduation_progress_pct']:.1f}%")
    print(f"   ⏳ Remaining: {launchlab_data['sol_bonding_curve']['sol_remaining']:.1f} SOL")
    print(f"   ⚡ Velocity: {launchlab_data['sol_bonding_curve']['sol_velocity_per_hour']:.1f} SOL/hour")
    print(f"   ⏰ ETA: {launchlab_data['sol_bonding_curve']['estimated_graduation_eta_hours']:.0f} hours")
    
    print("\n�� SOL-NATIVE PRICING:")
    print(f"   💰 Price: {launchlab_data['market_data_sol']['current_price_sol']:.7f} SOL")
    print(f"   💵 Price USD: ${launchlab_data['market_data_sol']['current_price_usd']:.5f}")
    print(f"   📊 Market Cap: {launchlab_data['market_data_sol']['market_cap_sol']:.1f} SOL")
    print(f"   📈 24h Change: +{launchlab_data['market_data_sol']['price_change_24h']:.1f}%")
    print(f"   ⚡ SOL Velocity: {launchlab_data['market_data_sol']['velocity_sol_per_hour']:.1f} SOL/hour")
    
    print("\n💹 SOL TRADING ANALYTICS:")
    print(f"   📊 Volume (24h): {launchlab_data['trade_analytics_sol']['volume_24h_sol']:.1f} SOL")
    print(f"   🔄 Trades (24h): {launchlab_data['trade_analytics_sol']['trades_24h']:,}")
    print(f"   👥 Traders: {launchlab_data['trade_analytics_sol']['unique_traders_24h']}")
    print(f"   📈 Buy/Sell: {launchlab_data['trade_analytics_sol']['buy_sell_ratio_sol']:.2f}")
    print(f"   💰 Avg Trade: {launchlab_data['trade_analytics_sol']['avg_trade_size_sol']:.3f} SOL")
    print(f"   🏆 Largest: {launchlab_data['trade_analytics_sol']['largest_trade_sol']:.1f} SOL")
    
    print("\n👥 HOLDER ANALYTICS:")
    print(f"   👤 Total Holders: {launchlab_data['holder_analytics']['total_holders']}")
    print(f"   👑 Dev Holdings: {launchlab_data['holder_analytics']['dev_holdings_pct']:.1f}%")
    print(f"   💰 Dev Withdrawn: {launchlab_data['holder_analytics']['dev_sol_withdrawn']:.1f} SOL")
    print(f"   🐋 1+ SOL Holders: {launchlab_data['holder_analytics']['whale_holders_1sol_plus']}")
    print(f"   🐋 5+ SOL Holders: {launchlab_data['holder_analytics']['whale_holders_5sol_plus']}")
    print(f"   📊 Concentration: {launchlab_data['holder_analytics']['concentration_score']:.1f}/10")
    
    print("\n🎯 STRATEGIC RECOMMENDATIONS:")
    print(f"   🏷️ Stage: {launchlab_data['strategic_recommendations']['current_stage']}")
    print(f"   💰 Profit Potential: {launchlab_data['strategic_recommendations']['profit_potential']}")
    print(f"   ⚠️ Risk Level: {launchlab_data['strategic_recommendations']['risk_level']}")
    print(f"   🎲 Position Size: {launchlab_data['strategic_recommendations']['position_size_pct']:.1f}%")
    print(f"   🚀 Strategy: {launchlab_data['strategic_recommendations']['entry_strategy']}")
    print(f"   🚪 Exit: {launchlab_data['strategic_recommendations']['exit_recommendation']}")
    print(f"   ⚖️ Risk/Reward: {launchlab_data['strategic_recommendations']['risk_reward_ratio']:.1f}:1")
    
    print("\n🎓 GRADUATION ANALYSIS:")
    print(f"   📊 Probability: {launchlab_data['graduation_analysis']['graduation_probability']:.0%}")
    print(f"   ⏰ ETA: {launchlab_data['graduation_analysis']['graduation_eta_hours']:.0f} hours")
    print(f"   💪 Confidence: {launchlab_data['graduation_analysis']['graduation_confidence']:.0%}")
    print(f"   📈 Daily Rate: {launchlab_data['graduation_analysis']['current_daily_rate']:.1f} SOL/day")
    print(f"   ✅ Surplus: +{launchlab_data['graduation_analysis']['graduation_surplus']:.1f} SOL/day")
    
    print("\n🎯 ENHANCED SCORING:")
    print(f"   ⏰ Age: {launchlab_data['enhanced_scoring_data']['age_minutes']} minutes")
    print(f"   ⚡ SOL Velocity: {launchlab_data['enhanced_scoring_data']['sol_velocity_score']:.1f}/10")
    print(f"   📈 Momentum: {launchlab_data['enhanced_scoring_data']['momentum_score']:.1f}/10")
    print(f"   🎓 Graduation: {launchlab_data['enhanced_scoring_data']['graduation_score']:.1f}/10")
    print(f"   🎯 Final Score: {launchlab_data['enhanced_scoring_data']['predicted_final_score']:.1f}/100")
    
    return launchlab_data

if __name__ == "__main__":
    demo_launchlab_api_data()
