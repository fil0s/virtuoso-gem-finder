#!/usr/bin/env python3
"""
Configuration Consolidation Tool

This tool helps consolidate multiple config files and documents which configuration
is actually being used by the system.
"""

import yaml
import json
import sys
from pathlib import Path
from typing import Dict, List, Any
from datetime import datetime

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

class ConfigConsolidationTool:
    """Tool to analyze and consolidate configuration files"""
    
    def __init__(self):
        self.config_dir = Path("config")
        self.config_files = list(self.config_dir.glob("*.yaml"))
        
    def analyze_configurations(self) -> Dict:
        """Analyze all configuration files and their differences"""
        
        analysis = {
            "timestamp": datetime.now().isoformat(),
            "config_files": [],
            "active_config": None,
            "threshold_comparison": {},
            "recommendations": []
        }
        
        # Load all config files
        configs = {}
        for config_file in self.config_files:
            try:
                with open(config_file, 'r') as f:
                    configs[config_file.name] = yaml.safe_load(f)
                
                analysis["config_files"].append({
                    "filename": config_file.name,
                    "size_bytes": config_file.stat().st_size,
                    "modified": datetime.fromtimestamp(config_file.stat().st_mtime).isoformat(),
                    "status": "loaded"
                })
                
            except Exception as e:
                analysis["config_files"].append({
                    "filename": config_file.name,
                    "status": f"error: {e}"
                })
        
        # Determine active config
        analysis["active_config"] = self._determine_active_config()
        
        # Compare alert thresholds
        analysis["threshold_comparison"] = self._compare_thresholds(configs)
        
        # Generate recommendations
        analysis["recommendations"] = self._generate_recommendations(configs, analysis)
        
        return analysis
    
    def _determine_active_config(self) -> Dict:
        """Determine which config file is actually being used"""
        
        # Check the main config.yaml file (this is what's loaded by default)
        main_config = Path("config/config.yaml")
        
        if main_config.exists():
            stat = main_config.stat()
            return {
                "filename": "config.yaml",
                "path": str(main_config),
                "size_bytes": stat.st_size,
                "modified": datetime.fromtimestamp(stat.st_mtime).isoformat(),
                "reason": "Default configuration file loaded by ConfigManager"
            }
        else:
            return {
                "filename": None,
                "reason": "No config.yaml found - system may use fallback configuration"
            }
    
    def _compare_thresholds(self, configs: Dict) -> Dict:
        """Compare alert thresholds across all config files"""
        
        threshold_keys = [
            "ANALYSIS.alert_score_threshold",
            "ANALYSIS.scoring.cross_platform.high_conviction_threshold", 
            "ANALYSIS.scoring.final_scoring.alert_threshold",
            "TRADER_DISCOVERY.alert_score_threshold"
        ]
        
        comparison = {}
        
        for key in threshold_keys:
            comparison[key] = {}
            for config_name, config_data in configs.items():
                value = self._get_nested_value(config_data, key)
                if value is not None:
                    comparison[key][config_name] = value
        
        return comparison
    
    def _get_nested_value(self, data: Dict, key_path: str) -> Any:
        """Get nested value from dictionary using dot notation"""
        keys = key_path.split('.')
        current = data
        
        try:
            for key in keys:
                current = current[key]
            return current
        except (KeyError, TypeError):
            return None
    
    def _generate_recommendations(self, configs: Dict, analysis: Dict) -> List[str]:
        """Generate recommendations for configuration consolidation"""
        recommendations = []
        
        # Check for multiple config files
        config_count = len([cf for cf in analysis["config_files"] if cf["status"] == "loaded"])
        if config_count > 3:
            recommendations.append(f"⚠️ Found {config_count} config files - consider consolidating to reduce confusion")
        
        # Check for threshold conflicts
        threshold_comparison = analysis["threshold_comparison"]
        for threshold_key, values in threshold_comparison.items():
            if len(values) > 1:
                unique_values = set(values.values())
                if len(unique_values) > 1:
                    recommendations.append(f"🔧 Conflicting values for {threshold_key}: {dict(values)}")
        
        # Check for unused config files
        active_config = analysis["active_config"]["filename"]
        for config_file in analysis["config_files"]:
            if config_file["filename"] != active_config and config_file["status"] == "loaded":
                if "example" not in config_file["filename"] and "template" not in config_file["filename"]:
                    recommendations.append(f"📄 {config_file['filename']} is not being used by the main system")
        
        # Specific recommendations
        if "config.enhanced.yaml" in configs and "config.yaml" in configs:
            recommendations.append("🔄 Consider merging enhanced config features into main config.yaml")
        
        if not recommendations:
            recommendations.append("✅ Configuration appears well organized")
        
        return recommendations
    
    def create_consolidated_config(self) -> str:
        """Create a consolidated configuration file"""
        
        # Load the main config as base
        main_config_path = Path("config/config.yaml")
        if not main_config_path.exists():
            return "❌ No main config.yaml found to use as base"
        
        with open(main_config_path, 'r') as f:
            consolidated = yaml.safe_load(f)
        
        # Add any unique sections from other configs
        enhanced_config_path = Path("config/config.enhanced.yaml")
        if enhanced_config_path.exists():
            with open(enhanced_config_path, 'r') as f:
                enhanced = yaml.safe_load(f)
            
            # Add unique enhanced features
            for key, value in enhanced.items():
                if key not in consolidated:
                    consolidated[key] = value
        
        # Save consolidated config
        output_path = Path("config/config.consolidated.yaml")
        with open(output_path, 'w') as f:
            yaml.dump(consolidated, f, default_flow_style=False, indent=2)
        
        return f"✅ Created consolidated config: {output_path}"
    
    def document_configuration_usage(self) -> str:
        """Create documentation about which config is used"""
        
        doc_content = f"""# Configuration Usage Documentation

Generated: {datetime.now().isoformat()}

## Active Configuration

The Virtuoso Gem Hunter system uses **config/config.yaml** as its primary configuration file.

This is loaded by:
- `core/config_manager.py` (ConfigManager class)
- `scripts/high_conviction_token_detector.py` (default path)
- All daemon scripts and main entry points

## Configuration File Priority

1. **config/config.yaml** - Main configuration (ACTIVE)
2. config/config.enhanced.yaml - Enhanced features (testing only)
3. config/config.optimized.yaml - Performance optimized settings
4. config/config.example.yaml - Template file

## Important Alert Thresholds (from active config)

```yaml
ANALYSIS:
  alert_score_threshold: 35.0
  scoring:
    cross_platform:
      high_conviction_threshold: 44.5
    final_scoring:
      alert_threshold: 30.0
```

## Telegram Configuration

```yaml
TELEGRAM:
  enabled: true
  bot_token: ${{TELEGRAM_BOT_TOKEN}}
  chat_id: ${{TELEGRAM_CHAT_ID}}
  max_alerts_per_hour: 10
  cooldown_minutes: 30
```

## To Change Configuration

1. Edit `config/config.yaml` directly
2. Restart the detector daemon
3. Test with `python3 test_telegram_mic_check.py`

## Files NOT Used by Main System

- config.enhanced.yaml (used only by specific test scripts)
- config.optimized.yaml (historical)
- config.override.yaml (historical)

## Recommendations

1. Keep config.yaml as the single source of truth
2. Test changes before deploying to production
3. Backup config.yaml before making changes
4. Use environment variables for sensitive data
"""
        
        doc_path = Path("docs/CONFIGURATION_USAGE.md")
        doc_path.parent.mkdir(exist_ok=True)
        
        with open(doc_path, 'w') as f:
            f.write(doc_content)
        
        return f"✅ Created configuration documentation: {doc_path}"
    
    def print_analysis(self):
        """Print formatted analysis to console"""
        analysis = self.analyze_configurations()
        
        print("🔧 CONFIGURATION ANALYSIS")
        print("=" * 50)
        
        print(f"📅 Analysis Time: {analysis['timestamp']}")
        
        print(f"\n📁 CONFIGURATION FILES ({len(analysis['config_files'])})")
        print("-" * 30)
        for cf in analysis["config_files"]:
            status_icon = "✅" if cf["status"] == "loaded" else "❌"
            print(f"{status_icon} {cf['filename']}")
            if cf["status"] == "loaded":
                print(f"    Size: {cf['size_bytes']} bytes")
                print(f"    Modified: {cf['modified']}")
            else:
                print(f"    Status: {cf['status']}")
        
        print(f"\n🎯 ACTIVE CONFIGURATION")
        print("-" * 25)
        active = analysis["active_config"]
        if active["filename"]:
            print(f"✅ {active['filename']}")
            print(f"   Path: {active['path']}")
            print(f"   Size: {active['size_bytes']} bytes")
            print(f"   Modified: {active['modified']}")
            print(f"   Reason: {active['reason']}")
        else:
            print(f"❌ {active['reason']}")
        
        print(f"\n⚖️ THRESHOLD COMPARISON")
        print("-" * 25)
        for threshold, values in analysis["threshold_comparison"].items():
            if values:
                print(f"\n{threshold}:")
                for config_name, value in values.items():
                    print(f"  {config_name}: {value}")
                
                # Check for conflicts
                unique_values = set(values.values())
                if len(unique_values) > 1:
                    print(f"  ⚠️ CONFLICT: Multiple values found!")
        
        print(f"\n💡 RECOMMENDATIONS")
        print("-" * 20)
        for rec in analysis["recommendations"]:
            print(f"  {rec}")
        
        print("\n" + "=" * 50)

def main():
    """Main function"""
    tool = ConfigConsolidationTool()
    
    print("🔧 Configuration Consolidation Tool")
    print("Choose an action:")
    print("1. Analyze configurations")
    print("2. Create consolidated config")
    print("3. Document configuration usage")
    print("4. All of the above")
    
    choice = input("\nEnter choice (1-4): ").strip()
    
    if choice in ["1", "4"]:
        tool.print_analysis()
    
    if choice in ["2", "4"]:
        print(f"\n{tool.create_consolidated_config()}")
    
    if choice in ["3", "4"]:
        print(f"\n{tool.document_configuration_usage()}")

if __name__ == "__main__":
    main()