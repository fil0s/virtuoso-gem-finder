#!/usr/bin/env python3

"""
Implement Optimized Batch Size for Birdeye API

Based on test results showing 100% success rate for all batch sizes 15-100,
this script implements a conservative optimization to 30 tokens as a first step.
"""

import os
from pathlib import Path

def implement_optimized_batch_size():
    """Implement optimized batch size of 30 tokens"""
    
    print("🚀 IMPLEMENTING OPTIMIZED BATCH SIZE")
    print("=" * 60)
    print("📊 Test Results Summary:")
    print("  • All batch sizes 15-100: 100% success rate")
    print("  • Current: 15 tokens per batch")
    print("  • Recommended: 30 tokens (conservative increase)")
    print("  • Expected improvement: 100% more efficient")
    print()
    
    files_to_update = [
        {
            'file': 'core/config_manager.py',
            'search': '"multi_price": 15',
            'replace': '"multi_price": 30  # Optimized from 15 based on testing',
            'description': 'Configuration batch size'
        },
        {
            'file': 'services/exit_signal_detector.py', 
            'search': 'batch_size = 15  # Reduced to prevent timeouts',
            'replace': 'batch_size = 30  # Optimized based on testing',
            'description': 'Exit signal detector batch size'
        },
        {
            'file': 'scripts/cross_platform_token_analyzer.py',
            'search': 'batch_size = 15  # Reduced to prevent timeouts', 
            'replace': 'batch_size = 30  # Optimized based on testing',
            'description': 'Cross-platform analyzer batch size'
        }
    ]
    
    changes_made = 0
    
    for update in files_to_update:
        file_path = Path(update['file'])
        
        if not file_path.exists():
            print(f"⚠️  File not found: {file_path}")
            continue
            
        try:
            # Read file content
            content = file_path.read_text()
            
            if update['search'] in content:
                # Make replacement
                new_content = content.replace(update['search'], update['replace'])
                
                # Write back
                file_path.write_text(new_content)
                
                print(f"✅ Updated {update['description']}: {file_path}")
                changes_made += 1
            else:
                print(f"⚠️  Pattern not found in {file_path}: {update['search']}")
                
        except Exception as e:
            print(f"❌ Error updating {file_path}: {e}")
    
    print()
    print("📈 OPTIMIZATION RESULTS:")
    print(f"  • Files updated: {changes_made}")
    print(f"  • Batch size: 15 → 30 tokens")
    print(f"  • Efficiency gain: 100% (2x fewer API calls)")
    print(f"  • Expected impact: Faster processing, same reliability")
    print()
    
    if changes_made > 0:
        print("🎯 NEXT STEPS:")
        print("  1. Test the new 30-token batch size")
        print("  2. Monitor success rates and performance")
        print("  3. Consider further increases to 50-100 tokens")
        print("  4. Implement adaptive batch sizing")
    
    return changes_made

if __name__ == "__main__":
    implement_optimized_batch_size() 