#!/usr/bin/env python3
"""
Quick script to fix color issues in the treasure quest files
"""

import os
import re

def fix_color_issues():
    """Fix BROWN and GOLD color references that don't exist in colorama"""
    
    files_to_fix = [
        "scripts/virtuoso_treasure_quest_generator.py"
    ]
    
    replacements = {
        r'{Fore\.BROWN}': '{Fore.YELLOW + Style.DIM}',
        r'{Fore\.BROWN \+ Style\.BRIGHT}': '{Fore.YELLOW + Style.BRIGHT}',
        r'{Fore\.GOLD}': '{Fore.YELLOW}',
        r'{Fore\.GOLD \+ Style\.BRIGHT}': '{Fore.YELLOW + Style.BRIGHT}'
    }
    
    for file_path in files_to_fix:
        if os.path.exists(file_path):
            print(f"Fixing colors in {file_path}...")
            
            with open(file_path, 'r') as f:
                content = f.read()
            
            for old_pattern, new_replacement in replacements.items():
                content = re.sub(old_pattern, new_replacement, content)
            
            with open(file_path, 'w') as f:
                f.write(content)
            
            print(f"✅ Fixed {file_path}")
        else:
            print(f"⚠️ File not found: {file_path}")

if __name__ == "__main__":
    fix_color_issues()
    print("🎨 Color fixes complete!") 