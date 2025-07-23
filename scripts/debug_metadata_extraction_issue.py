#!/usr/bin/env python3
"""
Debug Token Metadata Extraction Issue
Comprehensive analysis of why tokens are showing as "Unknown"
"""

def analyze_metadata_issue():
    """Analyze the metadata extraction issue and provide solutions"""
    
    print("🔍" * 80)
    print("🔍 TOKEN METADATA EXTRACTION ISSUE ANALYSIS")
    print("🔍" * 80)
    
    print(f"\n🚨 PROBLEM IDENTIFIED:")
    print(f"Tokens are showing as 'Unknown' because of a metadata pipeline issue.")
    
    print(f"\n📊 ROOT CAUSE ANALYSIS:")
    print(f"1. ✅ Birdeye API provides correct token metadata:")
    print(f"   • Token 1: symbol='shadow', name='Shadow'")
    print(f"   • Token 2: symbol='TG', name='Trade Gaurd'") 
    print(f"   • Token 3: symbol='coded', name='soft shill'")
    
    print(f"\n2. ❌ Cross-Platform Analysis returns 'NOT_FOUND':")
    print(f"   • Cross-Platform Symbol: 'NOT_FOUND'")
    print(f"   • Cross-Platform Name: 'NOT_FOUND'")
    
    print(f"\n3. ⚠️  Token Display Logic Issue:")
    print(f"   • System prioritizes cross-platform data over Birdeye data")
    print(f"   • When cross-platform returns 'NOT_FOUND', it displays as 'Unknown'")
    print(f"   • Birdeye data is fetched but not used for display")
    
    print(f"\n" + "="*80)
    print(f"🔧 SOLUTION IMPLEMENTATION PLAN")
    print("="*80)
    
    print(f"\n🎯 IMMEDIATE FIX (High Priority):")
    print(f"1. Update token display logic in high_conviction_token_detector.py")
    print(f"2. Fallback hierarchy: Birdeye → Cross-Platform → 'Unknown'")
    print(f"3. Ensure Birdeye metadata is used when available")
    
    print(f"\n📋 SPECIFIC CODE CHANGES NEEDED:")
    print(f"")
    print(f"Location: scripts/high_conviction_token_detector.py")
    print(f"Function: _format_token_for_display() or similar")
    print(f"")
    print(f"Current Logic (BROKEN):")
    print(f"  symbol = token.get('symbol', 'Unknown')")
    print(f"  name = token.get('name', '')")
    print(f"")
    print(f"Fixed Logic (CORRECT):")
    print(f"  # Priority: Birdeye > Cross-Platform > Default")
    print(f"  symbol = (token.get('birdeye_symbol') or ")
    print(f"           token.get('symbol') or 'Unknown')")
    print(f"  name = (token.get('birdeye_name') or ")
    print(f"         token.get('name') or '')")
    
    print(f"\n🔄 PIPELINE IMPROVEMENT (Medium Priority):")
    print(f"1. Enhance cross-platform analysis to better extract metadata")
    print(f"2. Improve symbol/name extraction from DexScreener API")
    print(f"3. Add metadata validation and consistency checks")
    
    print(f"\n📈 DATA QUALITY IMPROVEMENTS (Lower Priority):")
    print(f"1. Implement metadata caching strategy")
    print(f"2. Add symbol/name confidence scoring")
    print(f"3. Cross-reference multiple sources for validation")
    
    print(f"\n" + "="*80)
    print(f"💡 IMPLEMENTATION STEPS")
    print("="*80)
    
    print(f"\n🔧 Step 1: Locate Display Functions")
    print(f"• Find where token symbols/names are formatted for display")
    print(f"• Look for 'Unknown' string assignments")
    print(f"• Check Telegram alert formatting")
    
    print(f"\n🔧 Step 2: Update Metadata Priority Logic")
    print(f"• Implement fallback hierarchy")
    print(f"• Ensure Birdeye data is preserved and used")
    print(f"• Test with current token samples")
    
    print(f"\n🔧 Step 3: Validate Fix")
    print(f"• Run single scan test")
    print(f"• Verify tokens show correct names/symbols")
    print(f"• Check Telegram alerts display properly")
    
    print(f"\n✅ EXPECTED RESULTS AFTER FIX:")
    print(f"• Token 1: 'shadow' (Shadow) instead of 'Unknown'")
    print(f"• Token 2: 'TG' (Trade Gaurd) instead of 'Unknown'")
    print(f"• Token 3: 'coded' (soft shill) instead of 'Unknown'")
    print(f"• Much better user experience and token identification")
    
    print(f"\n🎯 IMPACT:")
    print(f"• 🟢 High: Significantly improves token identification")
    print(f"• 🟢 High: Better Telegram alerts with proper names")
    print(f"• 🟢 Medium: Improved user confidence in system")
    print(f"• 🟢 Low: Better debugging and analysis capabilities")

if __name__ == "__main__":
    analyze_metadata_issue() 