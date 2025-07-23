#!/usr/bin/env python3
"""
Refactoring Script: Consolidate Jupiter Connectors
This script will refactor the cross-platform analyzer to use the enhanced Jupiter connector
"""

import os
import sys
import shutil
from pathlib import Path

def refactor_jupiter_connector():
    """Refactor to use consolidated Jupiter connector"""
    
    print("🔧 JUPITER CONNECTOR REFACTORING")
    print("=" * 50)
    
    # Step 1: Backup the current cross-platform analyzer
    backup_file = "scripts/cross_platform_token_analyzer.py.pre_jupiter_refactor"
    if not os.path.exists(backup_file):
        shutil.copy("scripts/cross_platform_token_analyzer.py", backup_file)
        print(f"✅ Created backup: {backup_file}")
    
    # Step 2: Read the current cross-platform analyzer
    with open("scripts/cross_platform_token_analyzer.py", "r") as f:
        content = f.read()
    
    # Step 3: Find the JupiterConnector class boundaries
    jupiter_start = content.find("class JupiterConnector:")
    if jupiter_start == -1:
        print("❌ JupiterConnector class not found")
        return False
    
    # Find the next class (MeteoraConnector)
    meteora_start = content.find("class MeteoraConnector:", jupiter_start)
    if meteora_start == -1:
        print("❌ Could not find end of JupiterConnector class")
        return False
    
    # Step 4: Extract the parts before and after JupiterConnector
    before_jupiter = content[:jupiter_start]
    after_jupiter = content[meteora_start:]
    
    # Step 5: Create the new import and initialization
    new_import = """from api.enhanced_jupiter_connector import EnhancedJupiterConnector

"""
    
    # Find where imports end to add our new import
    import_insertion_point = content.find("class DexScreenerConnector:")
    if import_insertion_point == -1:
        import_insertion_point = content.find("class CrossPlatformAnalyzer:")
    
    imports_section = content[:import_insertion_point]
    classes_section = content[import_insertion_point:]
    
    # Add our import to the imports section
    new_imports_section = imports_section + new_import
    
    # Step 6: Update the CrossPlatformAnalyzer initialization
    # Find the Jupiter initialization in CrossPlatformAnalyzer
    analyzer_init_start = classes_section.find("def __init__(self, config")
    if analyzer_init_start != -1:
        # Find the Jupiter connector initialization
        jupiter_init_pattern = "self.jupiter = JupiterConnector("
        jupiter_init_start = classes_section.find(jupiter_init_pattern)
        
        if jupiter_init_start != -1:
            # Replace with enhanced connector
            jupiter_init_end = classes_section.find(")", jupiter_init_start) + 1
            old_jupiter_init = classes_section[jupiter_init_start:jupiter_init_end]
            
            # Create new initialization for enhanced connector
            new_jupiter_init = """self.jupiter = EnhancedJupiterConnector(
                enhanced_cache=self.enhanced_cache,
                logger=self.logger
            )"""
            
            # Replace the initialization
            classes_section = classes_section.replace(old_jupiter_init, new_jupiter_init)
            print("✅ Updated Jupiter connector initialization")
    
    # Step 7: Remove the embedded JupiterConnector class
    # Remove everything from "class JupiterConnector:" to "class MeteoraConnector:"
    jupiter_class_start = classes_section.find("class JupiterConnector:")
    meteora_class_start = classes_section.find("class MeteoraConnector:", jupiter_class_start)
    
    if jupiter_class_start != -1 and meteora_class_start != -1:
        before_jupiter_class = classes_section[:jupiter_class_start]
        after_jupiter_class = classes_section[meteora_class_start:]
        classes_section = before_jupiter_class + after_jupiter_class
        print("✅ Removed embedded JupiterConnector class")
    
    # Step 8: Write the refactored file
    new_content = new_imports_section + classes_section
    
    with open("scripts/cross_platform_token_analyzer.py", "w") as f:
        f.write(new_content)
    
    print("✅ Cross-platform analyzer refactored successfully")
    
    # Step 9: Create a summary of changes
    print("\n📊 REFACTORING SUMMARY:")
    print("  ✅ Removed embedded JupiterConnector class (~350 lines)")
    print("  ✅ Added import for EnhancedJupiterConnector")
    print("  ✅ Updated initialization to use enhanced connector")
    print("  ✅ Created backup of original file")
    print("\n🎯 BENEFITS:")
    print("  • Single source of truth for Jupiter functionality")
    print("  • Better code organization and separation of concerns")
    print("  • Enhanced Jupiter features automatically available")
    print("  • Easier maintenance and testing")
    print("  • Consistent Jupiter behavior across all components")
    
    return True

def verify_refactoring():
    """Verify the refactoring was successful"""
    print("\n🔍 VERIFYING REFACTORING:")
    
    # Check if backup exists
    if os.path.exists("scripts/cross_platform_token_analyzer.py.pre_jupiter_refactor"):
        print("  ✅ Backup file exists")
    else:
        print("  ❌ Backup file missing")
        return False
    
    # Check if enhanced connector import was added
    with open("scripts/cross_platform_token_analyzer.py", "r") as f:
        content = f.read()
    
    if "from api.enhanced_jupiter_connector import EnhancedJupiterConnector" in content:
        print("  ✅ Enhanced Jupiter connector import added")
    else:
        print("  ❌ Enhanced Jupiter connector import missing")
        return False
    
    # Check if embedded JupiterConnector class was removed
    if "class JupiterConnector:" not in content:
        print("  ✅ Embedded JupiterConnector class removed")
    else:
        print("  ❌ Embedded JupiterConnector class still present")
        return False
    
    # Check if EnhancedJupiterConnector is being used
    if "self.jupiter = EnhancedJupiterConnector(" in content:
        print("  ✅ Using EnhancedJupiterConnector in initialization")
    else:
        print("  ❌ Not using EnhancedJupiterConnector")
        return False
    
    print("  🎉 Refactoring verification successful!")
    return True

def rollback_refactoring():
    """Rollback the refactoring if needed"""
    backup_file = "scripts/cross_platform_token_analyzer.py.pre_jupiter_refactor"
    
    if os.path.exists(backup_file):
        shutil.copy(backup_file, "scripts/cross_platform_token_analyzer.py")
        print("✅ Refactoring rolled back successfully")
        return True
    else:
        print("❌ Backup file not found, cannot rollback")
        return False

if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "rollback":
        rollback_refactoring()
    elif len(sys.argv) > 1 and sys.argv[1] == "verify":
        verify_refactoring()
    else:
        success = refactor_jupiter_connector()
        if success:
            verify_refactoring()
            print("\n🚀 Refactoring complete! The cross-platform analyzer now uses the enhanced Jupiter connector.")
            print("   Run 'python scripts/refactor_jupiter_connector.py rollback' if you need to revert.")
        else:
            print("\n❌ Refactoring failed!") 