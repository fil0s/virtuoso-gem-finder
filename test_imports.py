#!/usr/bin/env python3
"""Test imports after reorganization"""

import sys
import os

# Add current directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

print("Testing imports...")

try:
    from utils.enhanced_structured_logger import create_enhanced_logger, DetectionStage
    print("✅ Enhanced logger import successful")
except ImportError as e:
    print(f"❌ Enhanced logger import failed: {e}")

try:
    from dashboard_utils import create_dashboard
    print("✅ Dashboard utils import successful (old path)")
except ImportError:
    try:
        from src.dashboard.dashboard_utils import create_dashboard
        print("✅ Dashboard utils import successful (new path)")
    except ImportError as e:
        print(f"❌ Dashboard utils import failed: {e}")

try:
    from dashboard_styled import create_futuristic_dashboard
    print("✅ Styled dashboard import successful (old path)")
except ImportError:
    try:
        from src.dashboard.dashboard_styled import create_futuristic_dashboard
        print("✅ Styled dashboard import successful (new path)")
    except ImportError as e:
        print(f"❌ Styled dashboard import failed: {e}")

try:
    from web_dashboard import VirtuosoWebDashboard
    print("✅ Web dashboard import successful (old path)")
except ImportError:
    try:
        from src.dashboard.web_dashboard import VirtuosoWebDashboard
        print("✅ Web dashboard import successful (new path)")
    except ImportError as e:
        print(f"❌ Web dashboard import failed: {e}")

try:
    from early_gem_detector import EarlyGemDetector
    print("✅ Early gem detector import successful (old path)")
except ImportError:
    try:
        from src.detectors.early_gem_detector import EarlyGemDetector
        print("✅ Early gem detector import successful (new path)")
    except ImportError as e:
        print(f"❌ Early gem detector import failed: {e}")

print("Import test complete!")