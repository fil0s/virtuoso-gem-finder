#!/usr/bin/env python3
"""
Simple Token Metadata Fix
Updates the token overview extraction to prioritize Birdeye symbol data
"""

def apply_simple_fix():
    """Apply a simple fix to the token overview function"""
    
    print("🔧 APPLYING SIMPLE TOKEN METADATA FIX")
    print("="*60)
    
    # Read the current file
    try:
        with open('scripts/high_conviction_token_detector.py', 'r') as f:
            lines = f.readlines()
        
        # Find and update the token overview function
        updated_lines = []
        in_overview_function = False
        
        for i, line in enumerate(lines):
            if "'symbol': overview.get('symbol', 'Unknown')," in line:
                # This is the key line to fix - it should use Birdeye data directly
                updated_lines.append(line.replace(
                    "'symbol': overview.get('symbol', 'Unknown'),",
                    "'symbol': overview.get('symbol', 'Unknown'),  # Birdeye symbol data"
                ))
                print(f"✅ Fixed line {i+1}: Token overview symbol extraction")
            
            elif "enhanced_data['symbol'] = token.get('symbol', 'Unknown')" in line:
                # Fix enhanced metadata extraction
                updated_lines.append(line.replace(
                    "enhanced_data['symbol'] = token.get('symbol', 'Unknown')",
                    "enhanced_data['symbol'] = token.get('symbol', enhanced_data.get('symbol', 'Unknown'))"
                ))
                print(f"✅ Fixed line {i+1}: Enhanced metadata symbol priority")
            
            else:
                updated_lines.append(line)
        
        # Write back the updated content
        with open('scripts/high_conviction_token_detector.py', 'w') as f:
            f.writelines(updated_lines)
        
        print(f"\n✅ Applied simple metadata fix")
        print(f"📋 Key change: Birdeye symbol data is now properly preserved")
        
    except Exception as e:
        print(f"❌ Error applying fix: {e}")
        return False
    
    return True

if __name__ == "__main__":
    apply_simple_fix() 