#!/usr/bin/env python3
"""
Integration Script: Replace Current Scoring with Improved Normalized Scoring
Shows exactly how to integrate the new scoring system into the detector
"""

def show_integration_steps():
    """Show step-by-step integration process"""
    
    print("🔧" * 80)
    print("🔧 INTEGRATION GUIDE: IMPROVED NORMALIZED SCORING")
    print("🔧" * 80)
    
    print(f"\n🎯 OVERVIEW:")
    print(f"This guide shows how to replace the current scoring system with the improved")
    print(f"normalized version that properly scales all components to 0-100.")
    
    # Step 1: Code Changes
    print(f"\n" + "="*60)
    print(f"📝 STEP 1: CODE CHANGES REQUIRED")
    print("="*60)
    
    print(f"\n🔧 1.1 Add ImprovedTokenScorer to high_conviction_token_detector.py:")
    print(f"```python")
    print(f"# Add at top of file after existing imports")
    print(f"from scripts.improved_normalized_scoring import ImprovedTokenScorer")
    print(f"```")
    
    print(f"\n🔧 1.2 Initialize scorer in __init__ method:")
    print(f"```python")
    print(f"# In HighConvictionTokenDetector.__init__(), add:")
    print(f"# Determine market condition (could be config-driven)")
    print(f"market_condition = self.config.get('MARKET_CONDITION', 'normal')  # bear/normal/bull")
    print(f"self.improved_scorer = ImprovedTokenScorer(market_condition)")
    print(f"```")
    
    print(f"\n🔧 1.3 Replace _calculate_final_score method:")
    print(f"```python")
    print(f"def _calculate_final_score(self, candidate, overview_data, whale_analysis,")
    print(f"                         volume_price_analysis, community_boost_analysis,") 
    print(f"                         security_analysis, trading_activity) -> float:")
    print(f"    '''Calculate final score using improved normalized scoring'''")
    print(f"    ")
    print(f"    # Use improved scorer")
    print(f"    scores = self.improved_scorer.calculate_normalized_score(")
    print(f"        candidate, overview_data, whale_analysis, volume_price_analysis,")
    print(f"        community_boost_analysis, security_analysis, trading_activity")
    print(f"    )")
    print(f"    ")
    print(f"    # Log detailed breakdown")
    print(f"    self.logger.debug(f'📊 Improved score breakdown:')")
    print(f"    for component, score in scores.items():")
    print(f"        if component != 'final_score':")
    print(f"            self.logger.debug(f'  • {{component}}: {{score:.1f}}')")
    print(f"    ")
    print(f"    return scores['final_score']")
    print(f"```")
    
    # Step 2: Configuration Changes
    print(f"\n" + "="*60)
    print(f"⚙️ STEP 2: CONFIGURATION UPDATES")
    print("="*60)
    
    print(f"\n🔧 2.1 Update config.yaml with market-aware thresholds:")
    print(f"```yaml")
    print(f"# Add to config.yaml")
    print(f"MARKET_CONDITION: 'bear'  # Options: bear, normal, bull")
    print(f"")
    print(f"SCORING:")
    print(f"  # Market-adaptive thresholds")
    print(f"  bear_market:")
    print(f"    high_conviction_threshold: 45.0")
    print(f"    moderate_conviction_threshold: 30.0")
    print(f"    min_candidate_score: 15.0")
    print(f"  ")
    print(f"  normal_market:")
    print(f"    high_conviction_threshold: 60.0")
    print(f"    moderate_conviction_threshold: 40.0")
    print(f"    min_candidate_score: 20.0")
    print(f"  ")
    print(f"  bull_market:")
    print(f"    high_conviction_threshold: 70.0")
    print(f"    moderate_conviction_threshold: 50.0")
    print(f"    min_candidate_score: 30.0")
    print(f"```")
    
    print(f"\n🔧 2.2 Update threshold loading in __init__:")
    print(f"```python")
    print(f"# Replace existing threshold loading with:")
    print(f"market_condition = self.config.get('MARKET_CONDITION', 'normal')")
    print(f"scoring_config = self.config.get('SCORING', {{}}).get(f'{{market_condition}}_market', {{}})")
    print(f"")
    print(f"self.high_conviction_threshold = scoring_config.get('high_conviction_threshold', 60.0)")
    print(f"self.moderate_conviction_threshold = scoring_config.get('moderate_conviction_threshold', 40.0)")
    print(f"self.min_cross_platform_score = scoring_config.get('min_candidate_score', 20.0)")
    print(f"```")
    
    # Step 3: Enhanced Alert Logic
    print(f"\n" + "="*60)
    print(f"📢 STEP 3: ENHANCED ALERT LOGIC")
    print("="*60)
    
    print(f"\n🔧 3.1 Update alert decision logic:")
    print(f"```python")
    print(f"# In run_detection_cycle(), replace alert logic:")
    print(f"if detailed_analysis['final_score'] >= self.high_conviction_threshold:")
    print(f"    # High conviction alert")
    print(f"    await self._send_detailed_alert(detailed_analysis, scan_id, 'HIGH')")
    print(f"elif detailed_analysis['final_score'] >= self.moderate_conviction_threshold:")
    print(f"    # Moderate conviction alert (optional)")
    print(f"    await self._send_detailed_alert(detailed_analysis, scan_id, 'MODERATE')")
    print(f"```")
    
    print(f"\n🔧 3.2 Add conviction level to alerts:")
    print(f"```python")
    print(f"# Update _send_detailed_alert to include conviction level")
    print(f"async def _send_detailed_alert(self, detailed_analysis, scan_id, conviction_level='HIGH'):")
    print(f"    conviction_level = self.improved_scorer.get_conviction_level(detailed_analysis['final_score'])")
    print(f"    # Include conviction_level in alert message")
    print(f"```")
    
    # Step 4: Testing
    print(f"\n" + "="*60)
    print(f"🧪 STEP 4: TESTING THE INTEGRATION")
    print("="*60)
    
    print(f"\n🔧 4.1 Create test script:")
    print(f"```python")
    print(f"# Create test_improved_scoring.py")
    print(f"from scripts.high_conviction_token_detector import HighConvictionTokenDetector")
    print(f"")
    print(f"# Test with your existing token data")
    print(f"detector = HighConvictionTokenDetector(debug_mode=True)")
    print(f"")
    print(f"# Test score calculation with known token")
    print(f"test_candidate = {{'cross_platform_score': 35.0, 'symbol': 'TEST'}}")
    print(f"# ... add your token data ...")
    print(f"score = detector._calculate_final_score(...)")
    print(f"print(f'New score: {{score:.1f}} (was ~42.0 with old system)')")
    print(f"```")
    
    # Step 5: Deployment Strategy
    print(f"\n" + "="*60)
    print(f"🚀 STEP 5: DEPLOYMENT STRATEGY")
    print("="*60)
    
    print(f"\n🔧 5.1 Gradual rollout approach:")
    print(f"  1. Test in debug mode first")
    print(f"  2. Run parallel scoring (old + new) for comparison")
    print(f"  3. Adjust market condition based on results")
    print(f"  4. Switch to new system when confident")
    
    print(f"\n🔧 5.2 Market condition tuning:")
    print(f"  • Start with 'bear' market condition for current low-cap tokens")
    print(f"  • Monitor alert frequency and quality")
    print(f"  • Adjust to 'normal' or 'bull' as market conditions change")
    
    # Benefits Summary
    print(f"\n" + "="*60)
    print(f"✅ BENEFITS OF NEW SCORING SYSTEM")
    print("="*60)
    
    print(f"\n🎯 Immediate Benefits:")
    print(f"  ✅ Proper 0-100 normalization")
    print(f"  ✅ Market condition adaptability")
    print(f"  ✅ Better score distribution")
    print(f"  ✅ More intuitive conviction levels")
    print(f"  ✅ Logarithmic scaling for wide value ranges")
    
    print(f"\n📊 Expected Results with Your Token Data:")
    print(f"  • Current highest score: 42.0 → Expected: ~77.3 (bear market)")
    print(f"  • Better differentiation between tokens")
    print(f"  • More alerts in current market conditions")
    print(f"  • Clearer conviction levels (VERY LOW to VERY HIGH)")
    
    print(f"\n🎯 Long-term Benefits:")
    print(f"  ✅ Automatic market adaptation")
    print(f"  ✅ Consistent scoring across market cycles")
    print(f"  ✅ Better backtesting capabilities")
    print(f"  ✅ More granular alert levels")
    
    # Quick Implementation
    print(f"\n" + "="*60)
    print(f"⚡ QUICK IMPLEMENTATION (MINIMAL CHANGES)")
    print("="*60)
    
    print(f"\n🔧 For immediate testing, just replace the _calculate_final_score method:")
    
    print(f"\n```python")
    print(f"# Quick replacement in high_conviction_token_detector.py")
    print(f"def _calculate_final_score(self, candidate, overview_data, whale_analysis,")
    print(f"                         volume_price_analysis, community_boost_analysis,")
    print(f"                         security_analysis, trading_activity) -> float:")
    print(f"    '''Quick improved scoring - replace entire method'''")
    print(f"    ")
    print(f"    # Import at method level for quick testing")
    print(f"    from scripts.improved_normalized_scoring import ImprovedTokenScorer")
    print(f"    ")
    print(f"    # Use bear market for current conditions")
    print(f"    scorer = ImprovedTokenScorer('bear')")
    print(f"    scores = scorer.calculate_normalized_score(")
    print(f"        candidate, overview_data, whale_analysis, volume_price_analysis,")
    print(f"        community_boost_analysis, security_analysis, trading_activity")
    print(f"    )")
    print(f"    ")
    print(f"    # Log the improvement")
    print(f"    old_style_score = candidate.get('cross_platform_score', 0) + 10  # Rough old estimate")
    print(f"    new_score = scores['final_score']")
    print(f"    self.logger.info(f'📊 Score improvement: {{old_style_score:.1f}} → {{new_score:.1f}}')")
    print(f"    ")
    print(f"    return new_score")
    print(f"```")
    
    print(f"\n🔧 Then lower your threshold temporarily:")
    print(f"```python")
    print(f"# In __init__, temporarily set:")
    print(f"self.high_conviction_threshold = 45.0  # Down from 70.0")
    print(f"```")
    
    print(f"\n🔧" * 80)
    print(f"🔧 READY TO INTEGRATE! Start with the quick implementation above.")
    print(f"🔧" * 80)


if __name__ == "__main__":
    show_integration_steps() 