#!/usr/bin/env python3
"""
High Conviction Token Detector - Complete Scoring Pipeline Analysis
Breaks down the entire analysis pipeline and scoring methodology
"""

def analyze_scoring_pipeline():
    """Comprehensive breakdown of the scoring pipeline"""
    
    print("🔬" * 80)
    print("🔬 HIGH CONVICTION TOKEN DETECTOR - COMPLETE SCORING PIPELINE")
    print("🔬" * 80)
    
    print(f"\n🎯 OVERVIEW: Multi-Stage Analysis Pipeline")
    print(f"The detector uses a sophisticated 3-stage pipeline to identify high-conviction tokens:")
    print(f"1. Cross-Platform Discovery (Initial Filtering)")
    print(f"2. Detailed Birdeye Analysis (6 Components)")
    print(f"3. Final Score Calculation & Alert Decision")
    
    # STAGE 1: Cross-Platform Discovery
    print(f"\n" + "="*80)
    print(f"🔍 STAGE 1: CROSS-PLATFORM DISCOVERY & INITIAL FILTERING")
    print(f"="*80)
    
    print(f"\n📊 Data Sources:")
    print(f"  🔗 RugCheck API: Community sentiment & voting")
    print(f"  🔗 DexScreener API: Boosted tokens & social profiles")
    print(f"  🔗 Birdeye API: Trending tokens & market data")
    
    print(f"\n🎯 Initial Filtering:")
    print(f"  • Min Cross-Platform Score: 30.0 (configurable)")
    print(f"  • Multi-platform validation required")
    print(f"  • Duplicate prevention (already alerted tokens filtered)")
    
    print(f"\n📈 Cross-Platform Scoring Factors:")
    print(f"  • Platform presence (multiple platforms = higher score)")
    print(f"  • Community engagement (votes, boosts, social activity)")
    print(f"  • Market momentum (volume, price changes)")
    print(f"  • Narrative alignment (trending topics, themes)")
    
    # STAGE 2: Detailed Analysis
    print(f"\n" + "="*80)
    print(f"🔬 STAGE 2: DETAILED BIRDEYE ANALYSIS (6 COMPONENTS)")
    print(f"="*80)
    
    print(f"\n🏗️ Analysis Pipeline:")
    print(f"For each candidate token, 6 parallel analyses are performed:")
    
    # Component 1: Token Overview
    print(f"\n📊 1. TOKEN OVERVIEW ANALYSIS")
    print(f"   API: get_token_overview()")
    print(f"   Data: Price, market cap, liquidity, holders, volume, price changes")
    print(f"   Purpose: Core market fundamentals")
    
    # Component 2: Whale Analysis
    print(f"\n🐋 2. WHALE HOLDER ANALYSIS")
    print(f"   API: get_token_holders()")
    print(f"   Data: Holder distribution, whale concentration, smart money detection")
    print(f"   Purpose: Assess token distribution health")
    
    # Component 3: Volume/Price Analysis
    print(f"\n📈 3. VOLUME/PRICE ANALYSIS")
    print(f"   API: get_ohlcv_data()")
    print(f"   Data: Volume trends, price momentum, volatility patterns")
    print(f"   Purpose: Technical analysis indicators")
    
    # Component 4: Community Analysis
    print(f"\n👥 4. COMMUNITY BOOST ANALYSIS")
    print(f"   API: get_token_overview() (extensions)")
    print(f"   Data: Website, Twitter, Telegram, social scores")
    print(f"   Purpose: Community strength assessment")
    
    # Component 5: Security Analysis
    print(f"\n🔒 5. SECURITY ANALYSIS")
    print(f"   API: Security checks (placeholder)")
    print(f"   Data: Risk factors, mint authority, freeze authority")
    print(f"   Purpose: Safety and legitimacy verification")
    
    # Component 6: Trading Activity
    print(f"\n💹 6. TRADING ACTIVITY ANALYSIS")
    print(f"   API: get_token_transactions()")
    print(f"   Data: Recent transactions, buy/sell ratios, trading frequency")
    print(f"   Purpose: Market activity assessment")
    
    # STAGE 3: Final Scoring
    print(f"\n" + "="*80)
    print(f"🎯 STAGE 3: FINAL SCORE CALCULATION (0-100 SCALE)")
    print(f"="*80)
    
    print(f"\n🧮 Scoring Formula:")
    print(f"final_score = base_score + overview_score + whale_score + volume_score + community_score + security_score + trading_score")
    print(f"(Capped at 100)")
    
    print(f"\n📊 DETAILED SCORING BREAKDOWN:")
    
    # Base Score
    print(f"\n🎯 BASE SCORE (Cross-Platform Score)")
    print(f"   Range: 30-50+ points (from Stage 1)")
    print(f"   Source: Cross-platform analysis results")
    print(f"   Weight: Foundation score")
    
    # Overview Score (0-20 points)
    print(f"\n📊 OVERVIEW SCORE (0-20 points)")
    print(f"   Market Cap Scoring:")
    print(f"     • > $1M: +5 points")
    print(f"     • > $100K: +3 points") 
    print(f"     • > $10K: +1 point")
    print(f"   Liquidity Scoring:")
    print(f"     • > $500K: +5 points")
    print(f"     • > $100K: +3 points")
    print(f"     • > $10K: +1 point")
    print(f"   Price Momentum (1h):")
    print(f"     • > 10%: +3 points")
    print(f"     • > 5%: +2 points")
    print(f"     • > 0%: +1 point")
    print(f"   Price Momentum (24h):")
    print(f"     • > 20%: +3 points")
    print(f"     • > 10%: +2 points")
    print(f"     • > 0%: +1 point")
    print(f"   Holders:")
    print(f"     • > 1000: +4 points")
    print(f"     • > 100: +2 points")
    print(f"     • > 10: +1 point")
    
    # Whale Score (0-15 points)
    print(f"\n🐋 WHALE SCORE (0-15 points)")
    print(f"   Whale Concentration (Sweet Spot):")
    print(f"     • 20-60%: +8 points (healthy distribution)")
    print(f"     • 10-80%: +5 points (acceptable)")
    print(f"     • > 0%: +2 points (basic)")
    print(f"   Smart Money Detection:")
    print(f"     • Detected: +7 points")
    print(f"   Philosophy: Balanced whale presence (not too concentrated)")
    
    # Volume Score (0-15 points)  
    print(f"\n📈 VOLUME SCORE (0-15 points)")
    print(f"   Volume Trend:")
    print(f"     • Increasing: +8 points")
    print(f"     • Stable: +4 points")
    print(f"   Price Momentum:")
    print(f"     • Bullish: +7 points")
    print(f"     • Neutral: +3 points")
    print(f"   Philosophy: Rising volume + bullish momentum = opportunity")
    
    # Community Score (0-10 points)
    print(f"\n👥 COMMUNITY SCORE (0-10 points)")
    print(f"   Social Score Calculation:")
    print(f"     • Website: +2 to social_score")
    print(f"     • Twitter: +3 to social_score")
    print(f"     • Telegram: +2 to social_score")
    print(f"   Final: min(10, social_score * 1.5)")
    print(f"   Philosophy: Strong community presence indicates legitimacy")
    
    # Security Score (0-10 points)
    print(f"\n🔒 SECURITY SCORE (0-10 points)")
    print(f"   Base Security Score: (security_score/100) * 10")
    print(f"   Risk Factor Penalties: -2 points per risk factor")
    print(f"   Minimum: 0 (cannot go negative)")
    print(f"   Philosophy: Safety first - penalize risky tokens")
    
    # Trading Score (0-10 points)
    print(f"\n💹 TRADING SCORE (0-10 points)")
    print(f"   Activity Score: min(10, recent_activity_score / 10)")
    print(f"   Buy/Sell Ratio Bonus:")
    print(f"     • > 1.5 (more buys): +3 points")
    print(f"     • > 1.0: +1 point")
    print(f"   Cap: 10 points maximum")
    print(f"   Philosophy: Active trading with buy pressure = bullish")
    
    # Decision Logic
    print(f"\n" + "="*80)
    print(f"🚨 STAGE 4: ALERT DECISION LOGIC")
    print(f"="*80)
    
    print(f"\n🎯 Threshold System:")
    print(f"   High Conviction Threshold: 70.0 (configurable)")
    print(f"   Alert Threshold: 35.0 (secondary threshold)")
    print(f"   Min Candidate Score: 30.0 (initial filter)")
    
    print(f"\n🔄 Decision Flow:")
    print(f"   1. if final_score >= 70.0:")
    print(f"      → Send Telegram Alert 🚨")
    print(f"      → Mark as alerted (prevent duplicates)")
    print(f"      → Log as high conviction token")
    print(f"   2. else:")
    print(f"      → Log token for analysis")
    print(f"      → Track in session registry")
    print(f"      → No alert sent")
    
    # Example Calculation
    print(f"\n" + "="*80)
    print(f"💡 EXAMPLE SCORE CALCULATION")
    print(f"="*80)
    
    print(f"\nExample Token: 'GOMI' (from your session)")
    print(f"Cross-Platform Score: 31.0 (base)")
    print(f"+ Overview Score: ~5 (moderate market cap/liquidity)")
    print(f"+ Whale Score: ~3 (basic whale presence)")
    print(f"+ Volume Score: ~2 (stable volume)")
    print(f"+ Community Score: ~4 (some social presence)")
    print(f"+ Security Score: ~8 (no major risks)")
    print(f"+ Trading Score: ~3 (moderate activity)")
    print(f"= Final Score: ~56 points")
    print(f"Result: Below 70.0 threshold → No alert sent")
    
    # Optimization Insights
    print(f"\n" + "="*80)
    print(f"🎯 OPTIMIZATION INSIGHTS")
    print(f"="*80)
    
    print(f"\n🔧 Current Market Analysis:")
    print(f"   Your highest token: 42.0 points")
    print(f"   Threshold gap: 28 points (70.0 - 42.0)")
    print(f"   Issue: Threshold too high for current market conditions")
    
    print(f"\n💡 Recommended Adjustments:")
    print(f"   Option 1 (Conservative): Lower threshold to 45.0")
    print(f"   Option 2 (Moderate): Lower threshold to 35.0")
    print(f"   Option 3 (Aggressive): Lower threshold to 25.0")
    
    print(f"\n📊 Component Performance (Your Session):")
    print(f"   Base Scores: 31-42 points (good cross-platform validation)")
    print(f"   Likely Bottlenecks:")
    print(f"     • Low market caps (< $100K)")
    print(f"     • Limited liquidity (< $100K)")
    print(f"     • Minimal price momentum")
    print(f"     • Basic community presence")
    
    print(f"\n🎯 Market Context:")
    print(f"   Current: Low volatility/consolidation period")
    print(f"   Tokens: Early-stage pump.fun tokens")
    print(f"   Strategy: Lower thresholds or wait for bull market")
    
    print(f"\n🔬" * 80)
    print(f"🔬 END SCORING PIPELINE ANALYSIS")
    print(f"🔬" * 80)

if __name__ == "__main__":
    analyze_scoring_pipeline() 