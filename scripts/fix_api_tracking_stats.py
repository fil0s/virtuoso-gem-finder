#!/usr/bin/env python3
"""
Fix API tracking statistics issue in Virtuoso Gem Hunter

This script fixes:
1. APICallType.BATCH missing from enum
2. API usage stats not being captured properly
3. birdeye_connector vs birdeye_api naming mismatch
"""

import os
import sys
import shutil
from datetime import datetime

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

def backup_file(filepath):
    """Create backup of file before modification"""
    backup_dir = "backups/api_tracking_fix_" + datetime.now().strftime("%Y%m%d_%H%M%S")
    os.makedirs(backup_dir, exist_ok=True)
    
    backup_path = os.path.join(backup_dir, os.path.basename(filepath))
    shutil.copy2(filepath, backup_path)
    print(f"✅ Backed up {filepath} to {backup_path}")
    return backup_path

def fix_api_call_type_enum():
    """Add BATCH to APICallType enum"""
    file_path = "utils/enhanced_structured_logger.py"
    
    print(f"\n🔧 Fixing APICallType enum in {file_path}")
    backup_file(file_path)
    
    with open(file_path, 'r') as f:
        content = f.read()
    
    # Find the APICallType enum and add BATCH
    lines = content.split('\n')
    updated_lines = []
    in_enum = False
    
    for i, line in enumerate(lines):
        if 'class APICallType(Enum):' in line:
            in_enum = True
        elif in_enum and line.strip() == '':
            # End of enum, insert BATCH before the empty line
            if 'BATCH = "batch"' not in content:
                updated_lines.append('    BATCH = "batch"')
            in_enum = False
        
        updated_lines.append(line)
    
    # Write updated content
    with open(file_path, 'w') as f:
        f.write('\n'.join(updated_lines))
    
    print("✅ Added BATCH to APICallType enum")

def fix_api_usage_capture():
    """Fix the API usage statistics capture in early_gem_detector.py"""
    file_path = "early_gem_detector.py"
    
    print(f"\n🔧 Fixing API usage capture in {file_path}")
    backup_file(file_path)
    
    with open(file_path, 'r') as f:
        content = f.read()
    
    # Replace birdeye_connector with birdeye_api in _capture_api_usage_stats
    content = content.replace(
        "if hasattr(self, 'birdeye_connector') and self.birdeye_connector:",
        "if hasattr(self, 'birdeye_api') and self.birdeye_api:"
    )
    
    content = content.replace(
        "birdeye_stats = getattr(self.birdeye_connector, 'call_stats', {})",
        "birdeye_stats = getattr(self.birdeye_api, 'api_call_tracker', {})"
    )
    
    # Fix the stats extraction to use api_call_tracker format
    old_stats_code = """                if birdeye_stats:
                    api_stats = self.session_stats['api_usage_by_service']['BirdEye']
                    api_stats['total_calls'] += birdeye_stats.get('total_calls', 0)
                    api_stats['successful_calls'] += birdeye_stats.get('successful_calls', 0)
                    api_stats['failed_calls'] += birdeye_stats.get('failed_calls', 0)"""
    
    new_stats_code = """                if birdeye_stats:
                    api_stats = self.session_stats['api_usage_by_service']['BirdEye']
                    api_stats['total_calls'] += birdeye_stats.get('total_api_calls', 0)
                    api_stats['successful_calls'] += birdeye_stats.get('successful_api_calls', 0)
                    api_stats['failed_calls'] += birdeye_stats.get('failed_api_calls', 0)"""
    
    content = content.replace(old_stats_code, new_stats_code)
    
    # Write updated content
    with open(file_path, 'w') as f:
        f.write(content)
    
    print("✅ Fixed API usage capture method")

def add_stats_capture_calls():
    """Add calls to _capture_api_usage_stats in the main loop"""
    file_path = "early_gem_detector.py"
    
    print(f"\n🔧 Adding stats capture calls in {file_path}")
    
    with open(file_path, 'r') as f:
        content = f.read()
    
    # Check if _capture_api_usage_stats is being called after cycles
    if "_capture_api_usage_stats()" not in content:
        # Find where to add the call - after cycle completion
        lines = content.split('\n')
        updated_lines = []
        
        for i, line in enumerate(lines):
            updated_lines.append(line)
            
            # Add capture call after updating session stats
            if "self.session_stats['cycles_completed'] += 1" in line:
                # Add the capture call with proper indentation
                indent = len(line) - len(line.lstrip())
                updated_lines.append(' ' * indent + "# Capture API usage statistics")
                updated_lines.append(' ' * indent + "self._capture_api_usage_stats()")
        
        content = '\n'.join(updated_lines)
        
        with open(file_path, 'w') as f:
            f.write(content)
        
        print("✅ Added API stats capture calls")
    else:
        print("✅ API stats capture calls already present")

def fix_batch_api_call_type():
    """Replace APICallType.BATCH with APICallType.BATCH_METADATA"""
    file_path = "early_gem_detector.py"
    
    print(f"\n🔧 Fixing APICallType.BATCH usage in {file_path}")
    
    with open(file_path, 'r') as f:
        content = f.read()
    
    # Replace APICallType.BATCH with APICallType.BATCH_METADATA
    content = content.replace("APICallType.BATCH", "APICallType.BATCH_METADATA")
    
    with open(file_path, 'w') as f:
        f.write(content)
    
    print("✅ Fixed APICallType.BATCH usage")

def main():
    """Run all fixes"""
    print("🚀 Starting API tracking statistics fix")
    
    try:
        # Fix 1: Add BATCH to APICallType enum
        fix_api_call_type_enum()
        
        # Fix 2: Fix API usage capture method
        fix_api_usage_capture()
        
        # Fix 3: Add stats capture calls
        add_stats_capture_calls()
        
        # Fix 4: Fix BATCH usage
        fix_batch_api_call_type()
        
        print("\n✅ All fixes applied successfully!")
        print("\n📊 API statistics should now be tracked properly")
        print("🔄 Please restart the detector to see the changes")
        
    except Exception as e:
        print(f"\n❌ Error applying fixes: {str(e)}")
        import traceback
        traceback.print_exc()
        return 1
    
    return 0

if __name__ == "__main__":
    sys.exit(main())