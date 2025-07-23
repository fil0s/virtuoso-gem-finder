#!/usr/bin/env python3
"""
Enhanced Age Scoring Implementation Script

This script implements the enhanced age scoring system with:
- 8-tier age scoring with exponential decay
- Bonus multipliers for ultra-new tokens (≤30min: +20%, ≤2h: +10%)
- Updated scoring weights (age: 20% → 25%)
- Comprehensive testing and validation

Usage:
    python scripts/implement_enhanced_age_scoring.py [--dry-run] [--skip-tests]
"""

import os
import sys
import time
import shutil
import logging
import argparse
from pathlib import Path
from typing import Dict, List, Tuple, Any
import yaml

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from core.config_manager import ConfigManager

class EnhancedAgeScoringImplementor:
    """Implements enhanced age scoring with comprehensive validation."""
    
    def __init__(self, dry_run: bool = False):
        self.dry_run = dry_run
        self.logger = logging.getLogger(__name__)
        self.setup_logging()
        
        # File paths
        self.config_path = project_root / "config" / "config.yaml"
        self.service_path = project_root / "services" / "early_token_detection.py"
        
        # Backup paths
        self.config_backup = project_root / "config" / "config.yaml.backup_before_age_enhancement"
        self.service_backup = project_root / "services" / "early_token_detection.py.backup_before_age_enhancement"
        
        # Implementation status
        self.implementation_status = {
            'backups_created': False,
            'config_updated': False,
            'service_updated': False,
            'tests_passed': False,
            'validation_passed': False
        }
        
    def setup_logging(self):
        """Setup detailed logging for implementation tracking."""
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler('logs/enhanced_age_scoring_implementation.log'),
                logging.StreamHandler()
            ]
        )
        
    def create_backups(self) -> bool:
        """Create backups of original files."""
        try:
            self.logger.info("🔄 Creating backups of original files...")
            
            if not self.dry_run:
                # Backup config.yaml
                if self.config_path.exists():
                    shutil.copy2(self.config_path, self.config_backup)
                    self.logger.info(f"✅ Config backup created: {self.config_backup}")
                else:
                    self.logger.error(f"❌ Config file not found: {self.config_path}")
                    return False
                
                # Backup early_token_detection.py
                if self.service_path.exists():
                    shutil.copy2(self.service_path, self.service_backup)
                    self.logger.info(f"✅ Service backup created: {self.service_backup}")
                else:
                    self.logger.error(f"❌ Service file not found: {self.service_path}")
                    return False
            else:
                self.logger.info("🔍 DRY RUN: Would create backups")
            
            self.implementation_status['backups_created'] = True
            return True
            
        except Exception as e:
            self.logger.error(f"❌ Failed to create backups: {e}")
            return False
    
    def validate_current_config(self) -> Dict[str, Any]:
        """Validate current configuration and return baseline metrics."""
        try:
            self.logger.info("🔄 Validating current configuration...")
            
            with open(self.config_path, 'r') as f:
                config = yaml.safe_load(f)
            
            # Check current scoring weights
            current_weights = config.get('ANALYSIS', {}).get('scoring_weights', {})
            
            baseline = {
                'current_weights': current_weights,
                'weights_sum': sum(current_weights.values()),
                'age_weight': current_weights.get('age', 0),
                'config_valid': True
            }
            
            self.logger.info(f"📊 Current scoring weights: {current_weights}")
            self.logger.info(f"📊 Weights sum: {baseline['weights_sum']:.3f}")
            self.logger.info(f"📊 Current age weight: {baseline['age_weight']:.3f}")
            
            if abs(baseline['weights_sum'] - 1.0) > 0.001:
                self.logger.warning(f"⚠️ Weights don't sum to 1.0: {baseline['weights_sum']}")
                baseline['config_valid'] = False
            
            return baseline
            
        except Exception as e:
            self.logger.error(f"❌ Failed to validate config: {e}")
            return {'config_valid': False, 'error': str(e)}
    
    def update_config_weights(self) -> bool:
        """Update scoring weights in configuration."""
        try:
            self.logger.info("🔄 Updating scoring weights in configuration...")
            
            # New weight distribution
            new_weights = {
                'liquidity': 0.28,     # Reduced from 0.30
                'age': 0.25,           # Increased from 0.20
                'price_change': 0.18,  # Reduced from 0.20
                'volume': 0.14,        # Reduced from 0.15
                'concentration': 0.10, # Unchanged
                'trend_dynamics': 0.05 # Unchanged
            }
            
            # Validate new weights sum to 1.0
            weights_sum = sum(new_weights.values())
            if abs(weights_sum - 1.0) > 0.001:
                self.logger.error(f"❌ New weights don't sum to 1.0: {weights_sum}")
                return False
            
            if not self.dry_run:
                # Load current config
                with open(self.config_path, 'r') as f:
                    config = yaml.safe_load(f)
                
                # Update weights
                if 'ANALYSIS' not in config:
                    config['ANALYSIS'] = {}
                config['ANALYSIS']['scoring_weights'] = new_weights
                
                # Write updated config
                with open(self.config_path, 'w') as f:
                    yaml.dump(config, f, default_flow_style=False, indent=2)
                
                self.logger.info("✅ Configuration weights updated successfully")
                self.logger.info(f"📊 New weights: {new_weights}")
                self.logger.info(f"📊 Weights sum: {weights_sum:.6f}")
            else:
                self.logger.info("🔍 DRY RUN: Would update config weights")
                self.logger.info(f"🔍 New weights would be: {new_weights}")
            
            self.implementation_status['config_updated'] = True
            return True
            
        except Exception as e:
            self.logger.error(f"❌ Failed to update config weights: {e}")
            return False
    
    def generate_enhanced_age_scoring_code(self) -> str:
        """Generate the enhanced age scoring function code."""
        return '''
    def _calculate_enhanced_age_score_and_bonus(self, creation_time: float, current_time: float) -> Tuple[float, float]:
        """
        Calculate enhanced age score and bonus multiplier for gem hunting optimization.
        
        This function implements an 8-tier age scoring system with exponential decay
        favoring newer tokens, plus bonus multipliers for ultra-fresh discoveries.
        
        Args:
            creation_time: Token creation timestamp
            current_time: Current timestamp
            
        Returns:
            Tuple of (age_score, bonus_multiplier)
            
        Age Tiers:
        - Ultra-new (≤30 min): 120 points + 20% total score bonus
        - Extremely new (30min-2h): 110 points + 10% total score bonus  
        - Very new (2-6h): 100 points
        - New (6-24h): 85 points
        - Recent (1-3 days): 65 points
        - Moderate (3-7 days): 45 points
        - Established (7-30 days): 25 points
        - Mature (>30 days): 10 points
        """
        if not creation_time:
            # Default for unknown age - conservative scoring
            return 12.5, 1.0
        
        age_seconds = current_time - creation_time
        age_minutes = age_seconds / 60
        age_hours = age_seconds / 3600
        age_days = age_seconds / 86400
        
        # Enhanced 8-tier age scoring with bonus multipliers
        if age_minutes <= 30:      # Ultra-new (≤30 min)
            age_score = 120
            bonus_multiplier = 1.20  # 20% total score bonus
            tier = "ULTRA_NEW"
        elif age_hours <= 2:       # Extremely new (30min-2h)
            age_score = 110
            bonus_multiplier = 1.10  # 10% total score bonus
            tier = "EXTREMELY_NEW"
        elif age_hours <= 6:       # Very new (2-6h)
            age_score = 100
            bonus_multiplier = 1.0
            tier = "VERY_NEW"
        elif age_hours <= 24:      # New (6-24h)
            age_score = 85
            bonus_multiplier = 1.0
            tier = "NEW"
        elif age_days <= 3:        # Recent (1-3 days)
            age_score = 65
            bonus_multiplier = 1.0
            tier = "RECENT"
        elif age_days <= 7:        # Moderate (3-7 days)
            age_score = 45
            bonus_multiplier = 1.0
            tier = "MODERATE"
        elif age_days <= 30:       # Established (7-30 days)
            age_score = 25
            bonus_multiplier = 1.0
            tier = "ESTABLISHED"
        else:                      # Mature (>30 days)
            age_score = 10
            bonus_multiplier = 1.0
            tier = "MATURE"
        
        # Log age analysis for debugging
        if age_minutes <= 30:
            self.logger.info(f"🔥 ULTRA-NEW TOKEN: {age_minutes:.1f} min old, tier={tier}, score={age_score}, bonus={bonus_multiplier:.2f}x")
        elif age_hours <= 2:
            self.logger.info(f"⚡ EXTREMELY NEW TOKEN: {age_hours:.1f}h old, tier={tier}, score={age_score}, bonus={bonus_multiplier:.2f}x")
        else:
            self.logger.debug(f"📅 Token age: {age_hours:.1f}h old, tier={tier}, score={age_score}, bonus={bonus_multiplier:.2f}x")
        
        return age_score, bonus_multiplier
'''
    
    def update_quick_scoring_method(self, service_content: str) -> str:
        """Update the quick scoring method with enhanced age scoring."""
        
        # Find the quick scoring age section
        start_marker = "# Age score (20%) - newer is better for early detection"
        end_marker = "score += self.scoring_weights['age'] * age_score"
        
        # New enhanced quick scoring code
        new_quick_age_code = '''            # Enhanced Age Score (25%) - exponential decay favoring ultra-new tokens
            creation_time = token.get('creation_time', current_time)
            age_score_raw, age_bonus_multiplier = self._calculate_enhanced_age_score_and_bonus(creation_time, current_time)
            
            # Scale age score for quick scoring (max 100 points)
            age_score = min(100, age_score_raw)
            
            score += self.scoring_weights['age'] * age_score'''
        
        # Replace the old age scoring logic
        lines = service_content.split('\n')
        new_lines = []
        in_age_section = False
        
        for line in lines:
            if start_marker in line:
                in_age_section = True
                new_lines.append(new_quick_age_code)
                continue
            elif in_age_section and end_marker in line:
                in_age_section = False
                # Apply age bonus multiplier to final score after all components calculated
                new_lines.append('\n        # Apply age bonus multiplier for ultra-new tokens')
                new_lines.append('        score *= age_bonus_multiplier')
                new_lines.append('        ')
                continue
            elif not in_age_section:
                new_lines.append(line)
        
        return '\n'.join(new_lines)
    
    def update_comprehensive_scoring_method(self, service_content: str) -> str:
        """Update the comprehensive scoring method with enhanced age scoring."""
        
        # Find the comprehensive scoring age section
        start_marker = "# 2. Age Score (20% weight)"
        end_marker = 'self.logger.debug(f"[SCORING] {token_symbol} - Age: Unknown -> Default Score: {scores[\'age\']}/20")'
        
        # New enhanced comprehensive scoring code
        new_comprehensive_age_code = '''            # 2. Enhanced Age Score (25% weight) - exponential decay with bonus multipliers
            creation_time = basic_metrics.get(token_address, {}).get('creation_time')
            current_time = time.time()
            
            age_score_raw, age_bonus_multiplier = self._calculate_enhanced_age_score_and_bonus(creation_time, current_time)
            
            # Scale age score for comprehensive scoring (max 25 points)
            scores['age'] = min(25, age_score_raw * 0.208)  # Scale 120 max to 25 max
            
            if creation_time:
                age_hours = (current_time - creation_time) / 3600
                age_tier = "UNKNOWN"
                if age_hours <= 0.5:
                    age_tier = "ULTRA_NEW"
                elif age_hours <= 2:
                    age_tier = "EXTREMELY_NEW"
                elif age_hours <= 6:
                    age_tier = "VERY_NEW"
                elif age_hours <= 24:
                    age_tier = "NEW"
                elif age_hours <= 72:
                    age_tier = "RECENT"
                elif age_hours <= 168:
                    age_tier = "MODERATE"
                elif age_hours <= 720:
                    age_tier = "ESTABLISHED"
                else:
                    age_tier = "MATURE"
                    
                self.logger.debug(f"[SCORING] {token_symbol} - Enhanced Age: {age_hours:.1f}h ({age_tier}) -> Score: {scores['age']:.1f}/25, Bonus: {age_bonus_multiplier:.2f}x")
            else:
                self.logger.debug(f"[SCORING] {token_symbol} - Enhanced Age: Unknown -> Default Score: {scores['age']:.1f}/25")'''
        
        # Replace the old age scoring logic
        lines = service_content.split('\n')
        new_lines = []
        in_age_section = False
        skip_until_end = False
        
        for line in lines:
            if start_marker in line:
                in_age_section = True
                new_lines.append(new_comprehensive_age_code)
                skip_until_end = True
                continue
            elif skip_until_end and end_marker in line:
                skip_until_end = False
                in_age_section = False
                continue
            elif not skip_until_end:
                new_lines.append(line)
        
        return '\n'.join(new_lines)
    
    def add_bonus_multiplier_application(self, service_content: str) -> str:
        """Add bonus multiplier application to final score calculation."""
        
        # Find the end of comprehensive scoring where final score is calculated
        final_score_marker = "final_score = sum(scores.values())"
        
        lines = service_content.split('\n')
        new_lines = []
        
        for i, line in enumerate(lines):
            new_lines.append(line)
            if final_score_marker in line:
                # Add bonus multiplier application
                new_lines.append('')
                new_lines.append('            # Apply enhanced age bonus multiplier for ultra-new tokens')
                new_lines.append('            creation_time = basic_metrics.get(token_address, {}).get(\'creation_time\')')
                new_lines.append('            if creation_time:')
                new_lines.append('                _, age_bonus_multiplier = self._calculate_enhanced_age_score_and_bonus(creation_time, current_time)')
                new_lines.append('                final_score *= age_bonus_multiplier')
                new_lines.append('                if age_bonus_multiplier > 1.0:')
                new_lines.append('                    self.logger.info(f"[SCORING] {token_symbol} - 🔥 AGE BONUS APPLIED: {age_bonus_multiplier:.2f}x -> Final Score: {final_score:.1f}")')
                new_lines.append('')
        
        return '\n'.join(new_lines)
    
    def update_service_file(self) -> bool:
        """Update the service file with enhanced age scoring."""
        try:
            self.logger.info("🔄 Updating service file with enhanced age scoring...")
            
            if not self.dry_run:
                # Read current service file
                with open(self.service_path, 'r') as f:
                    service_content = f.read()
                
                # Add the enhanced age scoring function
                enhanced_function = self.generate_enhanced_age_scoring_code()
                
                # Find a good place to insert the function (after imports, before class methods)
                insert_marker = "class EarlyTokenDetector:"
                lines = service_content.split('\n')
                new_lines = []
                
                for line in lines:
                    new_lines.append(line)
                    if insert_marker in line:
                        # Add the enhanced function after the class definition
                        new_lines.extend(enhanced_function.split('\n'))
                
                service_content = '\n'.join(new_lines)
                
                # Update quick scoring method
                service_content = self.update_quick_scoring_method(service_content)
                
                # Update comprehensive scoring method  
                service_content = self.update_comprehensive_scoring_method(service_content)
                
                # Add bonus multiplier application
                service_content = self.add_bonus_multiplier_application(service_content)
                
                # Write updated service file
                with open(self.service_path, 'w') as f:
                    f.write(service_content)
                
                self.logger.info("✅ Service file updated successfully")
            else:
                self.logger.info("🔍 DRY RUN: Would update service file with enhanced age scoring")
            
            self.implementation_status['service_updated'] = True
            return True
            
        except Exception as e:
            self.logger.error(f"❌ Failed to update service file: {e}")
            return False
    
    def run_validation_tests(self) -> bool:
        """Run validation tests to ensure implementation works correctly."""
        try:
            self.logger.info("🔄 Running validation tests...")
            
            # Test the enhanced age scoring function
            test_cases = [
                (time.time() - 900, "15 minutes ago", 120, 1.20),     # Ultra-new
                (time.time() - 3600, "1 hour ago", 110, 1.10),       # Extremely new
                (time.time() - 14400, "4 hours ago", 100, 1.0),      # Very new
                (time.time() - 43200, "12 hours ago", 85, 1.0),      # New
                (time.time() - 172800, "2 days ago", 65, 1.0),       # Recent
                (time.time() - 432000, "5 days ago", 45, 1.0),       # Moderate
                (time.time() - 1296000, "15 days ago", 25, 1.0),     # Established
                (time.time() - 2592000, "30 days ago", 10, 1.0),     # Mature
            ]
            
            if not self.dry_run:
                # Import the updated service to test
                sys.path.insert(0, str(project_root))
                from services.early_token_detection import EarlyTokenDetector
                
                detector = EarlyTokenDetector()
                current_time = time.time()
                
                all_tests_passed = True
                for creation_time, description, expected_score, expected_bonus in test_cases:
                    score, bonus = detector._calculate_enhanced_age_score_and_bonus(creation_time, current_time)
                    
                    if abs(score - expected_score) > 1 or abs(bonus - expected_bonus) > 0.01:
                        self.logger.error(f"❌ Test failed for {description}: expected ({expected_score}, {expected_bonus}), got ({score}, {bonus})")
                        all_tests_passed = False
                    else:
                        self.logger.info(f"✅ Test passed for {description}: score={score}, bonus={bonus:.2f}x")
                
                if all_tests_passed:
                    self.logger.info("✅ All validation tests passed")
                    self.implementation_status['tests_passed'] = True
                    return True
                else:
                    self.logger.error("❌ Some validation tests failed")
                    return False
            else:
                self.logger.info("🔍 DRY RUN: Would run validation tests")
                self.implementation_status['tests_passed'] = True
                return True
                
        except Exception as e:
            self.logger.error(f"❌ Validation tests failed: {e}")
            return False
    
    def generate_implementation_report(self) -> str:
        """Generate a comprehensive implementation report."""
        
        report = f"""
# Enhanced Age Scoring Implementation Report

## Implementation Status
- Backups Created: {'✅' if self.implementation_status['backups_created'] else '❌'}
- Config Updated: {'✅' if self.implementation_status['config_updated'] else '❌'}
- Service Updated: {'✅' if self.implementation_status['service_updated'] else '❌'}
- Tests Passed: {'✅' if self.implementation_status['tests_passed'] else '❌'}
- Validation Passed: {'✅' if self.implementation_status['validation_passed'] else '❌'}

## Implementation Summary
- **Enhanced Age Scoring**: 8-tier system with exponential decay
- **Bonus Multipliers**: Ultra-new (≤30min): +20%, Extremely new (≤2h): +10%
- **Weight Changes**: Age increased from 20% to 25%
- **Dry Run Mode**: {'Enabled' if self.dry_run else 'Disabled'}

## Files Modified
- Configuration: {self.config_path}
- Service: {self.service_path}

## Backup Files Created
- Config Backup: {self.config_backup}
- Service Backup: {self.service_backup}

## Next Steps
1. Run comprehensive testing with real token data
2. Monitor alert generation patterns
3. Validate score distributions
4. Fine-tune thresholds if needed

## Rollback Instructions
If issues arise, restore from backups:
```bash
cp {self.config_backup} {self.config_path}
cp {self.service_backup} {self.service_path}
```

Generated at: {time.strftime('%Y-%m-%d %H:%M:%S')}
"""
        return report
    
    def implement(self, skip_tests: bool = False) -> bool:
        """Run the complete implementation process."""
        
        self.logger.info("🚀 Starting Enhanced Age Scoring Implementation")
        self.logger.info(f"🔍 Dry Run Mode: {'Enabled' if self.dry_run else 'Disabled'}")
        
        try:
            # Phase 1: Create backups
            if not self.create_backups():
                self.logger.error("❌ Failed to create backups, aborting implementation")
                return False
            
            # Phase 2: Validate current system
            baseline = self.validate_current_config()
            if not baseline.get('config_valid', False):
                self.logger.error("❌ Current configuration is invalid, aborting implementation")
                return False
            
            # Phase 3: Update configuration
            if not self.update_config_weights():
                self.logger.error("❌ Failed to update configuration, aborting implementation")
                return False
            
            # Phase 4: Update service file
            if not self.update_service_file():
                self.logger.error("❌ Failed to update service file, aborting implementation")
                return False
            
            # Phase 5: Run validation tests
            if not skip_tests and not self.run_validation_tests():
                self.logger.error("❌ Validation tests failed, aborting implementation")
                return False
            
            # Generate implementation report
            report = self.generate_implementation_report()
            report_path = project_root / "docs" / "summaries" / "ENHANCED_AGE_SCORING_RESULTS.md"
            
            if not self.dry_run:
                with open(report_path, 'w') as f:
                    f.write(report)
                self.logger.info(f"📄 Implementation report saved: {report_path}")
            else:
                self.logger.info("🔍 DRY RUN: Would save implementation report")
            
            self.logger.info("🎉 Enhanced Age Scoring Implementation Completed Successfully!")
            return True
            
        except Exception as e:
            self.logger.error(f"❌ Implementation failed: {e}")
            return False

def main():
    """Main entry point for the implementation script."""
    
    parser = argparse.ArgumentParser(description='Implement Enhanced Age Scoring System')
    parser.add_argument('--dry-run', action='store_true', help='Run in dry-run mode (no actual changes)')
    parser.add_argument('--skip-tests', action='store_true', help='Skip validation tests')
    
    args = parser.parse_args()
    
    # Create logs directory if it doesn't exist
    logs_dir = project_root / "logs"
    logs_dir.mkdir(exist_ok=True)
    
    # Run implementation
    implementor = EnhancedAgeScoringImplementor(dry_run=args.dry_run)
    success = implementor.implement(skip_tests=args.skip_tests)
    
    if success:
        print("\n🎉 Enhanced Age Scoring Implementation Completed Successfully!")
        if args.dry_run:
            print("🔍 This was a dry run - no actual changes were made")
            print("💡 Run without --dry-run to apply changes")
        else:
            print("✅ All changes have been applied")
            print("📊 Monitor the system for the next 24 hours")
            print("📄 Check the implementation report for details")
    else:
        print("\n❌ Implementation failed - check logs for details")
        sys.exit(1)

if __name__ == "__main__":
    main() 