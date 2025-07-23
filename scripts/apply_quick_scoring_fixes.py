#!/usr/bin/env python3
"""
QUICK FIX: Apply immediate fixes to running detector
"""

import sys
import os
sys.path.append(os.getcwd())

def apply_quick_fixes():
    """Apply quick fixes to high conviction detector"""
    try:
        from scripts.high_conviction_token_detector import HighConvictionTokenDetector
        
        print("🔧 Applying quick fixes to HighConvictionTokenDetector...")
        
        # Fix 1: Update high conviction threshold
        original_init = HighConvictionTokenDetector.__init__
        
        def fixed_init(self, config_path="config/config.yaml", debug_mode=False):
            # Call original init
            original_init(self, config_path, debug_mode)
            
            # Apply threshold fix based on actual score distribution
            if hasattr(self, 'session_token_registry'):
                unique_tokens = self.session_token_registry.get('unique_tokens_discovered', {})
                if len(unique_tokens) > 5:
                    scores = [token['score'] for token in unique_tokens.values()]
                    avg_score = sum(scores) / len(scores)
                    max_score = max(scores)
                    optimal_threshold = avg_score + (max_score - avg_score) * 0.3
                    
                    if optimal_threshold < self.high_conviction_threshold:
                        old_threshold = self.high_conviction_threshold
                        self.high_conviction_threshold = optimal_threshold
                        self.logger.info(f"🎯 Quick fix: Threshold adjusted {old_threshold} → {optimal_threshold:.1f}")
                else:
                    # Default quick fix for new sessions
                    if self.high_conviction_threshold > 50:
                        old_threshold = self.high_conviction_threshold
                        self.high_conviction_threshold = 35.0  # Conservative quick fix
                        self.logger.info(f"🎯 Quick fix: Threshold lowered {old_threshold} → 35.0")
        
        HighConvictionTokenDetector.__init__ = fixed_init
        
        print("✅ Quick fixes applied successfully")
        print("   • High conviction threshold adjusted")
        print("   • Will take effect on next detector initialization")
        
        return True
        
    except Exception as e:
        print(f"❌ Error applying quick fixes: {e}")
        return False

if __name__ == '__main__':
    apply_quick_fixes()
