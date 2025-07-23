#!/usr/bin/env python3
"""
🔍 Capture Real Scoring Breakdown
Analyze actual token data to find bonus stacking issue
"""

import sys
import os
import asyncio
import json
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from scripts.early_gem_detector import EarlyGemDetector

async def capture_real_scoring():
    """Capture real scoring breakdown from actual tokens"""
    
    print("🔍 CAPTURING REAL SCORING BREAKDOWN")
    print("=" * 60)
    
    # Initialize detector
    detector = EarlyGemDetector(debug_mode=True)
    
    print("🚀 Running detection cycle...")
    
    # Run a detection cycle
    results = await detector.run_detection_cycle()
    
    # Get high conviction tokens
    high_conviction = results.get('high_conviction_tokens', [])
    
    if not high_conviction:
        print("❌ No high conviction tokens found")
        return
    
    print(f"📊 Found {len(high_conviction)} high conviction tokens")
    print()
    
    # Analyze the top 3 highest scoring tokens
    sorted_tokens = sorted(high_conviction, key=lambda x: x.get('final_score', 0), reverse=True)
    top_tokens = sorted_tokens[:3]
    
    for i, token in enumerate(top_tokens):
        print(f"🎯 TOKEN {i+1}: {token.get('symbol', 'UNKNOWN')}")
        print(f"   Address: {token.get('address', 'N/A')}")
        print(f"   Source: {token.get('source', 'N/A')}")
        print(f"   Final Score: {token.get('final_score', 0):.1f}")
        
        # Check if scoring breakdown exists
        scoring_breakdown = token.get('scoring_breakdown', {})
        if scoring_breakdown:
            print(f"   📊 SCORING BREAKDOWN AVAILABLE")
            
            # Check final score summary
            final_summary = scoring_breakdown.get('final_score_summary', {})
            if final_summary:
                component_scores = final_summary.get('component_scores', {})
                scoring_totals = final_summary.get('scoring_totals', {})
                
                raw_total = scoring_totals.get('raw_total_score', 0)
                normalized_score = scoring_totals.get('normalized_score', 0)
                
                print(f"   🔍 RAW TOTAL: {raw_total:.1f}/125")
                print(f"   🎯 NORMALIZED: {normalized_score:.1f}/100")
                
                if raw_total > 125:
                    print(f"   🚨 PROBLEM: Raw score {raw_total:.1f} exceeds 125 limit by {raw_total - 125:.1f}!")
                
                # Show component breakdown
                print(f"   📋 COMPONENTS:")
                for comp_name, comp_data in component_scores.items():
                    raw_score = comp_data.get('raw', 0)
                    max_score = comp_data.get('max', 0)
                    status = "✅" if raw_score <= max_score else f"❌ OVER BY {raw_score - max_score:.1f}"
                    print(f"     • {comp_name}: {raw_score:.1f}/{max_score} {status}")
                
                # Check for specific stacking issues
                early_platform = scoring_breakdown.get('early_platform_analysis', {})
                if early_platform:
                    score_components = early_platform.get('score_components', {})
                    total_before_cap = score_components.get('total_before_cap', 0)
                    final_score = score_components.get('final_score', 0)
                    
                    if total_before_cap > 50:
                        print(f"   🚨 EARLY PLATFORM STACKING: {total_before_cap:.1f} before cap (should be ≤50)")
                        
                        # Show individual bonuses
                        print(f"     📋 BONUS BREAKDOWN:")
                        for comp, value in score_components.items():
                            if isinstance(value, (int, float)) and comp not in ['total_before_cap', 'final_score']:
                                print(f"       - {comp}: {value:.1f}")
        else:
            print(f"   ❌ No scoring breakdown available")
        
        print()
    
    # Save detailed data for analysis
    output_file = f"debug_high_scores_{int(time.time())}.json"
    with open(output_file, 'w') as f:
        json.dump({
            'high_conviction_tokens': high_conviction,
            'analysis_timestamp': time.time()
        }, f, indent=2)
    
    print(f"💾 Detailed data saved to: {output_file}")

if __name__ == "__main__":
    import time
    asyncio.run(capture_real_scoring()) 