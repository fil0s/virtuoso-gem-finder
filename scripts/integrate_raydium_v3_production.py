#!/usr/bin/env python3
"""
Integration script to make Raydium v3 connector production-ready
Integrates enhanced RaydiumConnector into early_gem_detector.py
"""

import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

def integrate_raydium_v3_production():
    """Integrate Raydium v3 connector into production early_gem_detector"""
    
    print("🚀 Integrating Raydium v3 Connector for Production")
    print("=" * 60)
    
    # Step 1: Check current imports in early_gem_detector.py
    early_gem_detector_path = project_root / "src" / "detectors" / "early_gem_detector.py"
    
    with open(early_gem_detector_path, 'r') as f:
        detector_content = f.read()
    
    # Check if RaydiumConnector is already imported
    if "from api.raydium_connector import RaydiumConnector" in detector_content:
        print("✅ RaydiumConnector already imported")
    else:
        print("❌ RaydiumConnector not imported - needs integration")
        
        # Find the import section and add RaydiumConnector
        import_section_end = detector_content.find("from services.telegram_alerter import")
        if import_section_end != -1:
            # Find the end of that line
            line_end = detector_content.find('\n', import_section_end)
            
            # Insert the new import
            new_import = "\nfrom api.raydium_connector import RaydiumConnector"
            updated_content = (detector_content[:line_end] + 
                             new_import + 
                             detector_content[line_end:])
            
            # Write back the updated content
            with open(early_gem_detector_path, 'w') as f:
                f.write(updated_content)
            
            print("✅ Added RaydiumConnector import")
        else:
            print("❌ Could not find import section")
    
    # Step 2: Check if RaydiumConnector is initialized in __init__
    with open(early_gem_detector_path, 'r') as f:
        detector_content = f.read()
    
    if "self.raydium_connector = None" in detector_content:
        print("✅ RaydiumConnector initialization already exists")
    else:
        print("❌ RaydiumConnector initialization missing - needs integration")
        
        # Find the __init__ method and add raydium_connector
        init_section = detector_content.find("def __init__(self")
        if init_section != -1:
            # Find a good place to add the initialization
            # Look for other connector initializations
            birdeye_init = detector_content.find("self.birdeye_api = None")
            if birdeye_init != -1:
                line_end = detector_content.find('\n', birdeye_init)
                
                # Insert the new initialization
                new_init = "\n        self.raydium_connector = None"
                updated_content = (detector_content[:line_end] + 
                                 new_init + 
                                 detector_content[line_end:])
                
                # Write back the updated content
                with open(early_gem_detector_path, 'w') as f:
                    f.write(updated_content)
                
                print("✅ Added RaydiumConnector initialization")
            else:
                print("❌ Could not find suitable initialization location")
    
    # Step 3: Check for Raydium data fetching method
    with open(early_gem_detector_path, 'r') as f:
        detector_content = f.read()
    
    if "_fetch_raydium_v3_pools" in detector_content:
        print("✅ Raydium v3 fetching method already exists")
    else:
        print("❌ Raydium v3 fetching method missing - needs implementation")
        print("   This requires manual integration due to complexity")
    
    # Step 4: Production readiness checklist
    print("\n📋 Production Readiness Checklist:")
    
    checklist_items = [
        ("✅ API Configuration", "config/api_endpoints.yaml updated"),
        ("✅ Enhanced Connector", "api/raydium_connector.py implemented"),
        ("❌ Main Integration", "Not integrated into early_gem_detector.py"),
        ("❌ Error Handling", "No production error handling"),
        ("❌ Rate Limiting", "Not using RateLimiterService"),
        ("❌ Caching Integration", "Not using EnhancedAPICacheManager"),
        ("❌ Logging Integration", "Not using enhanced structured logging"),
        ("❌ Testing", "No production testing suite"),
        ("❌ Monitoring", "No monitoring/alerting integration"),
        ("❌ Deployment", "No deployment scripts")
    ]
    
    for status, description in checklist_items:
        print(f"   {status} {description}")
    
    # Calculate readiness score
    ready_count = sum(1 for status, _ in checklist_items if status == "✅")
    total_count = len(checklist_items)
    readiness_percentage = (ready_count / total_count) * 100
    
    print(f"\n📊 Production Readiness: {readiness_percentage:.0f}% ({ready_count}/{total_count})")
    
    if readiness_percentage < 70:
        print("🚨 NOT PRODUCTION READY - Major integration work needed")
    elif readiness_percentage < 90:
        print("⚠️ PARTIALLY READY - Some integration work needed")
    else:
        print("✅ PRODUCTION READY")
    
    return readiness_percentage

if __name__ == "__main__":
    readiness = integrate_raydium_v3_production()
    sys.exit(0 if readiness >= 70 else 1)