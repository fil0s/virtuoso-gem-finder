#!/usr/bin/env python3
"""
🔧 FIX CROSS-PLATFORM LINEAR ADDITIVITY FLAW

This script specifically fixes the mathematical flaw in cross_platform_token_analyzer.py
where the _calculate_token_score method uses simple linear addition.

MATHEMATICAL CORRECTION:
❌ OLD: score += platform_score + dexscreener_score + rugcheck_score + ...
✅ NEW: score = f(platform_interactions, boost_amplification, contradictions)
"""

import sys
import shutil
from pathlib import Path
from datetime import datetime

def fix_cross_platform_scoring():
    """Fix the linear additivity flaw in cross-platform analyzer"""
    
    print("🔧 FIXING CROSS-PLATFORM LINEAR ADDITIVITY FLAW")
    print("=" * 60)
    print()
    
    # Target file
    analyzer_file = Path("scripts/cross_platform_token_analyzer.py")
    
    if not analyzer_file.exists():
        print(f"❌ File not found: {analyzer_file}")
        return
    
    # Create backup
    backup_dir = Path("backups") / f"cross_platform_fix_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    backup_dir.mkdir(parents=True, exist_ok=True)
    backup_file = backup_dir / "cross_platform_token_analyzer.py"
    shutil.copy2(analyzer_file, backup_file)
    print(f"📦 Backup created: {backup_file}")
    
    # Read current content
    with open(analyzer_file, 'r') as f:
        content = f.read()
    
    # Find the flawed method
    method_start = content.find("def _calculate_token_score(")
    if method_start == -1:
        print("❌ Could not find _calculate_token_score method")
        return
    
    # Find method end
    method_end = content.find("\n    def ", method_start + 1)
    if method_end == -1:
        method_end = content.find("\n    async def ", method_start + 1)
    if method_end == -1:
        method_end = len(content)
    
    # Extract the current flawed method for analysis
    current_method = content[method_start:method_end]
    print("🔍 FOUND LINEAR ADDITIVITY FLAW:")
    print("   Current method just keeps adding: score += ...")
    print("   This assumes all factors are independent (WRONG)")
    print()
    
    # Create the interaction-based replacement
    new_method = '''def _calculate_token_score(self, token_data: Dict) -> float:
        """
        Calculate token score using INTERACTION-BASED SCORING.
        
        MATHEMATICAL FIX:
        OLD (WRONG): score = platform_score + boost_score + volume_score + ...
        NEW (CORRECT): score = f(interactions, amplifications, contradictions)
        """
        try:
            # Import interaction scoring system
            from scripts.interaction_based_scoring_system import InteractionBasedScorer, FactorValues
            
            # Initialize interaction scorer for cross-platform analysis
            if not hasattr(self, '_cross_platform_interaction_scorer'):
                self._cross_platform_interaction_scorer = InteractionBasedScorer(debug_mode=False)
            
            # Calculate traditional components (for comparison)
            traditional_components = self._calculate_cross_platform_traditional_components(token_data)
            
            # Extract normalized factor values
            factor_values = self._extract_cross_platform_factor_values(token_data)
            
            # Apply interaction-based scoring (THE FIX)
            final_score, interaction_analysis = self._cross_platform_interaction_scorer.calculate_interaction_based_score(
                factor_values, traditional_components
            )
            
            # Log improvement for debugging
            linear_score = sum(traditional_components.values()) if traditional_components else 0
            if hasattr(self, 'logger') and self.logger:
                self.logger.debug(f"🧠 Cross-Platform Interaction Fix:")
                self.logger.debug(f"   📊 Linear (Flawed): {linear_score:.1f}")
                self.logger.debug(f"   🚀 Interaction (Fixed): {final_score:.1f}")
                self.logger.debug(f"   📈 Improvement: {((final_score - linear_score) / max(linear_score, 1)) * 100:+.1f}%")
            
            return final_score
            
        except Exception as e:
            # Fallback to linear method with warning
            if hasattr(self, 'logger') and self.logger:
                self.logger.warning(f"⚠️ Cross-platform interaction scoring failed: {e}")
                self.logger.warning("🚨 USING LINEAR FALLBACK - MATHEMATICAL FLAW ACTIVE")
            
            return self._calculate_token_score_linear_fallback(token_data)
    
    def _calculate_cross_platform_traditional_components(self, token_data: Dict) -> Dict[str, float]:
        """Calculate traditional component scores for baseline comparison"""
        platforms = len(token_data.get('platforms', []))
        
        # Platform validation score (cross-platform bonus)
        platform_score = 0
        if platforms >= 2:
            platform_score = (platforms - 1) * 8.0  # 2 platforms=8, 3=16, etc.
        
        # DexScreener analysis
        dexscreener_score = 0
        if 'dexscreener' in token_data.get('data', {}):
            ds_data = token_data['data']['dexscreener']
            
            # Golden ticker bonus
            if ds_data.get('is_golden_ticker', False):
                dexscreener_score += 15.0
            
            # Boost intensity scoring
            boost_intensity = ds_data.get('boost_intensity', 'MINIMAL_BOOST')
            boost_scores = {
                'GOLDEN_TICKER': 12.0, 'MEGA_BOOST': 10.0, 'HIGH_BOOST': 8.0,
                'MEDIUM_BOOST': 6.0, 'LOW_BOOST': 4.0, 'MINIMAL_BOOST': 2.0
            }
            if not ds_data.get('is_golden_ticker', False):  # Avoid double counting
                dexscreener_score += boost_scores.get(boost_intensity, 0)
            
            # Trending multiplier impact
            trending_multiplier = ds_data.get('trending_score_multiplier', 1.0)
            if trending_multiplier > 2.0:
                dexscreener_score += 8.0
            elif trending_multiplier > 1.5:
                dexscreener_score += 5.0
            elif trending_multiplier > 1.1:
                dexscreener_score += 2.0
            
            # Investment commitment (boost total)
            boost_total = ds_data.get('boost_total', 0)
            if boost_total >= 1000:
                dexscreener_score += 8.0
            elif boost_total >= 500:
                dexscreener_score += 6.0
            elif boost_total >= 100:
                dexscreener_score += 4.0
            elif boost_total >= 50:
                dexscreener_score += 2.0
        
        # RugCheck community sentiment
        rugcheck_score = 0
        if 'rugcheck' in token_data.get('data', {}):
            sentiment = token_data['data']['rugcheck'].get('sentiment_score', 0)
            if sentiment >= 0.8:
                rugcheck_score += 10.0
            elif sentiment >= 0.6:
                rugcheck_score += 6.0
            elif sentiment >= 0.4:
                rugcheck_score += 3.0
        
        # Birdeye trading metrics
        birdeye_score = 0
        if 'birdeye' in token_data.get('data', {}):
            be_data = token_data['data']['birdeye']
            volume_24h = be_data.get('volume_24h_usd', 0)
            price_change = be_data.get('price_change_24h', 0)
            
            # Volume scoring
            if volume_24h >= 1000000:
                birdeye_score += 8.0
            elif volume_24h >= 500000:
                birdeye_score += 6.0
            elif volume_24h >= 100000:
                birdeye_score += 4.0
            elif volume_24h >= 50000:
                birdeye_score += 2.0
            
            # Price momentum
            if price_change >= 50:
                birdeye_score += 8.0
            elif price_change >= 20:
                birdeye_score += 5.0
            elif price_change >= 10:
                birdeye_score += 3.0
            elif price_change >= 5:
                birdeye_score += 1.0
        
        return {
            'platform_score': platform_score,
            'dexscreener_score': dexscreener_score,
            'rugcheck_score': rugcheck_score,
            'birdeye_score': birdeye_score
        }
    
    def _extract_cross_platform_factor_values(self, token_data: Dict) -> FactorValues:
        """Extract normalized factor values for interaction analysis"""
        platforms_count = len(token_data.get('platforms', []))
        
        # Extract raw values from different platforms
        raw_volume = 0
        raw_liquidity = 0
        price_change = 0
        boost_amount = 0
        sentiment = 0.5  # Default neutral
        
        # Birdeye data
        if 'birdeye' in token_data.get('data', {}):
            be_data = token_data['data']['birdeye']
            raw_volume = be_data.get('volume_24h_usd', 0)
            raw_liquidity = be_data.get('liquidity', 0)
            price_change = be_data.get('price_change_24h', 0)
        
        # DexScreener boost data
        if 'dexscreener' in token_data.get('data', {}):
            ds_data = token_data['data']['dexscreener']
            boost_amount = ds_data.get('boost_amount', 0)
        
        # RugCheck sentiment
        if 'rugcheck' in token_data.get('data', {}):
            sentiment = token_data['data']['rugcheck'].get('sentiment_score', 0.5)
        
        # Normalize values to 0-1 scale for interaction analysis
        volume_momentum = min(1.0, raw_volume / 5000000) if raw_volume > 0 else 0
        liquidity = min(1.0, raw_liquidity / 1000000) if raw_liquidity > 0 else 0
        price_momentum = min(1.0, abs(price_change) / 100) if price_change != 0 else 0
        cross_platform_validation = min(1.0, platforms_count / 5.0)
        
        # Use boost amount as proxy for smart money interest
        smart_money_score = min(1.0, boost_amount / 1000) if boost_amount > 0 else 0
        
        # Use sentiment as security proxy
        security_score = max(0, sentiment) if sentiment > 0 else 0.5
        
        return FactorValues(
            vlr_ratio=0.0,  # Not applicable for cross-platform
            liquidity=liquidity,
            smart_money_score=smart_money_score,
            volume_momentum=volume_momentum,
            security_score=security_score,
            whale_concentration=0.0,  # Not available in cross-platform data
            price_momentum=price_momentum,
            cross_platform_validation=cross_platform_validation,
            age_factor=0.5,  # Default neutral
            raw_vlr=0,
            raw_liquidity=raw_liquidity,
            raw_volume_24h=raw_volume,
            platforms_count=platforms_count
        )
    
    def _calculate_token_score_linear_fallback(self, token_data: Dict) -> float:
        """Fallback to original linear scoring (WITH MATHEMATICAL FLAW)"""
        if hasattr(self, 'logger') and self.logger:
            self.logger.warning("🚨 LINEAR ADDITIVITY FALLBACK ACTIVE - MATHEMATICAL FLAW PRESENT")
        
        # Original flawed linear logic
        score = 0.0
        platforms = len(token_data.get('platforms', []))
        
        # Linear addition (MATHEMATICALLY INCORRECT)
        if platforms >= 2:
            score += (platforms - 1) * 8.0
        
        if 'dexscreener' in token_data.get('data', {}):
            ds_data = token_data['data']['dexscreener']
            if ds_data.get('is_golden_ticker', False):
                score += 15.0
            
            boost_intensity = ds_data.get('boost_intensity', 'MINIMAL_BOOST')
            boost_scores = {
                'MEGA_BOOST': 10.0, 'HIGH_BOOST': 8.0, 'MEDIUM_BOOST': 6.0,
                'LOW_BOOST': 4.0, 'MINIMAL_BOOST': 2.0
            }
            score += boost_scores.get(boost_intensity, 0)
        
        if 'rugcheck' in token_data.get('data', {}):
            sentiment = token_data['data']['rugcheck'].get('sentiment_score', 0)
            if sentiment >= 0.8:
                score += 10.0
            elif sentiment >= 0.6:
                score += 6.0
            elif sentiment >= 0.4:
                score += 3.0
        
        if 'birdeye' in token_data.get('data', {}):
            be_data = token_data['data']['birdeye']
            volume_24h = be_data.get('volume_24h_usd', 0)
            if volume_24h >= 1000000:
                score += 8.0
            elif volume_24h >= 500000:
                score += 6.0
            elif volume_24h >= 100000:
                score += 4.0
            elif volume_24h >= 50000:
                score += 2.0
        
        return score

'''
    
    # Replace the method
    new_content = content[:method_start] + new_method + content[method_end:]
    
    # Write the updated content
    with open(analyzer_file, 'w') as f:
        f.write(new_content)
    
    print("✅ CROSS-PLATFORM LINEAR ADDITIVITY FLAW FIXED")
    print("   🧠 Replaced linear addition with interaction-based scoring")
    print("   📊 Factor interactions now properly modeled")
    print("   🔄 Fallback to linear method available if needed")
    print(f"   📦 Backup available at: {backup_file}")
    print()
    print("🎯 NEXT STEPS:")
    print("   1. Test the cross-platform analyzer")
    print("   2. Run the main detector integration script")
    print("   3. Verify both systems use interaction-based scoring")

if __name__ == "__main__":
    fix_cross_platform_scoring() 