#!/usr/bin/env python3
"""
Script to remove emoji borders and replace with clean ASCII borders
"""

def fix_emoji_borders():
    """Fix emoji borders in the high conviction detector"""
    
    file_path = "scripts/high_conviction_token_detector.py"
    
    # Read the file
    with open(file_path, 'r') as f:
        content = f.read()
    
    # Define replacements
    replacements = [
        # Coin emoji borders
        ('self.logger.info("🪙" * 60)', 'self.logger.info("-" * 60)'),
        
        # Coin emoji headers (keep the emoji but clean the border)
        ('self.logger.info(f"\\n🪙 TOKEN DISCOVERY SUMMARY:")', 'self.logger.info(f"\\n📊 TOKEN DISCOVERY SUMMARY:")'),
        
        # Fix any remaining magnifying glass borders if they exist
        ('self.logger.info("🔍" * 80)', 'self.logger.info("=" * 80)'),
        ('self.logger.info("🔍 COMPREHENSIVE SCAN SUMMARY', 'self.logger.info("COMPREHENSIVE SCAN SUMMARY'),
        ('self.logger.info("🔍 Scan ID:', 'self.logger.info("Scan ID:'),
        ('self.logger.info("🔍 Timestamp:', 'self.logger.info("Timestamp:'),
        ('self.logger.info("🔍 END SCAN', 'self.logger.info("END SCAN'),
        
        # Fix the header patterns
        ('self.logger.info("\\n" + "🪙" * 60)', 'self.logger.info("\\n" + "-" * 60)'),
        ('self.logger.info("🪙 COMPREHENSIVE TOKEN REGISTRY - SESSION SUMMARY")', 'self.logger.info("COMPREHENSIVE TOKEN REGISTRY - SESSION SUMMARY")'),
    ]
    
    # Apply replacements
    modified = False
    for old, new in replacements:
        if old in content:
            content = content.replace(old, new)
            modified = True
            print(f"✅ Replaced: {old[:50]}...")
    
    if modified:
        # Write back to file
        with open(file_path, 'w') as f:
            f.write(content)
        print(f"✅ Updated {file_path} with clean ASCII borders")
    else:
        print("ℹ️  No emoji borders found to replace")

if __name__ == "__main__":
    fix_emoji_borders() 