#!/usr/bin/env python3
"""
Fix remaining import issues in bulk for files that import early_gem_detector
"""

import os
import re
from pathlib import Path

def fix_file_imports(file_path):
    """Fix imports in a single file"""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        original_content = content
        
        # Fix early_gem_detector imports
        content = re.sub(
            r'from early_gem_detector import EarlyGemDetector',
            '''try:
    from early_gem_detector import EarlyGemDetector
except ImportError:
    from src.detectors.early_gem_detector import EarlyGemDetector''',
            content
        )
        
        # Fix dashboard imports
        content = re.sub(
            r'from dashboard_styled import (.+)',
            r'''try:
    from dashboard_styled import \1
except ImportError:
    from src.dashboard.dashboard_styled import \1''',
            content
        )
        
        content = re.sub(
            r'from dashboard_utils import (.+)',
            r'''try:
    from dashboard_utils import \1
except ImportError:
    from src.dashboard.dashboard_utils import \1''',
            content
        )
        
        content = re.sub(
            r'from web_dashboard import (.+)',
            r'''try:
    from web_dashboard import \1
except ImportError:
    from src.dashboard.web_dashboard import \1''',
            content
        )
        
        # Only write if content changed
        if content != original_content:
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(content)
            print(f"✅ Fixed imports in {file_path}")
            return True
        else:
            print(f"⏭️ No changes needed in {file_path}")
            return False
            
    except Exception as e:
        print(f"❌ Error fixing {file_path}: {e}")
        return False

def main():
    """Fix imports in all affected files"""
    
    base_dir = Path(__file__).parent
    
    # Files that need fixing
    files_to_fix = [
        # Test files
        "tests/test_real_world_implementation.py",
        "tests/test_early_gem_routing.py", 
        "tests/test_comprehensive_dexscreener_optimization.py",
        "tests/integration/focused_dexscreener_test.py",
        "tests/test_dexscreener_optimization.py",
        "tests/test_complete_analysis.py",
        "tests/test_pump_api_fix.py",
        "tests/test_pump_api_fix_simple.py",
        "tests/test_sol_address_fix.py",
        
        # Archive files (optional)
        "archive/old_runners/run_72hour_detector.py",
        "archive/old_runners/run_3hour_detector_backup.py", 
        "archive/old_runners/run_starter_plan_detector.py",
    ]
    
    fixed_count = 0
    
    for file_path in files_to_fix:
        full_path = base_dir / file_path
        if full_path.exists():
            if fix_file_imports(full_path):
                fixed_count += 1
        else:
            print(f"⚠️ File not found: {full_path}")
    
    print(f"\n✅ Import fixing complete! Fixed {fixed_count} files.")

if __name__ == "__main__":
    main()