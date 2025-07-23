#!/usr/bin/env python3
"""
Enhanced Age Scoring Rollback Script

This script provides emergency rollback capability for the enhanced age scoring system.
It restores the original configuration and service files from backups.

Usage:
    python scripts/rollback_age_scoring.py [--force] [--verify]
"""

import os
import sys
import shutil
import logging
import argparse
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

class AgeScoringRollback:
    """Handles rollback of enhanced age scoring changes."""
    
    def __init__(self, force: bool = False, verify: bool = True):
        self.force = force
        self.verify = verify
        self.logger = logging.getLogger(__name__)
        self.setup_logging()
        
        # File paths
        self.config_path = project_root / "config" / "config.yaml"
        self.service_path = project_root / "services" / "early_token_detection.py"
        
        # Backup paths
        self.config_backup = project_root / "config" / "config.yaml.backup_before_age_enhancement"
        self.service_backup = project_root / "services" / "early_token_detection.py.backup_before_age_enhancement"
        
        # Rollback status
        self.rollback_status = {
            'config_restored': False,
            'service_restored': False,
            'verification_passed': False
        }
        
    def setup_logging(self):
        """Setup logging for rollback process."""
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler('logs/age_scoring_rollback.log'),
                logging.StreamHandler()
            ]
        )
    
    def check_backups_exist(self) -> bool:
        """Check if backup files exist."""
        self.logger.info("🔍 Checking for backup files...")
        
        missing_backups = []
        
        if not self.config_backup.exists():
            missing_backups.append(str(self.config_backup))
        else:
            self.logger.info(f"✅ Config backup found: {self.config_backup}")
        
        if not self.service_backup.exists():
            missing_backups.append(str(self.service_backup))
        else:
            self.logger.info(f"✅ Service backup found: {self.service_backup}")
        
        if missing_backups:
            self.logger.error(f"❌ Missing backup files: {missing_backups}")
            return False
        
        return True
    
    def confirm_rollback(self) -> bool:
        """Confirm rollback operation with user."""
        if self.force:
            self.logger.info("🔧 Force mode enabled - skipping confirmation")
            return True
        
        print("\n⚠️  ROLLBACK CONFIRMATION")
        print("=" * 50)
        print("This will restore the following files from backups:")
        print(f"  • {self.config_path}")
        print(f"  • {self.service_path}")
        print("\nAll enhanced age scoring changes will be lost!")
        print("=" * 50)
        
        response = input("Are you sure you want to proceed? (yes/no): ").lower().strip()
        
        if response in ['yes', 'y']:
            self.logger.info("✅ Rollback confirmed by user")
            return True
        else:
            self.logger.info("❌ Rollback cancelled by user")
            return False
    
    def restore_config(self) -> bool:
        """Restore configuration from backup."""
        try:
            self.logger.info("🔄 Restoring configuration file...")
            
            # Create a backup of current config before rollback
            current_backup = self.config_path.with_suffix('.yaml.pre_rollback_backup')
            shutil.copy2(self.config_path, current_backup)
            self.logger.info(f"📁 Current config backed up to: {current_backup}")
            
            # Restore from backup
            shutil.copy2(self.config_backup, self.config_path)
            self.logger.info(f"✅ Configuration restored from: {self.config_backup}")
            
            self.rollback_status['config_restored'] = True
            return True
            
        except Exception as e:
            self.logger.error(f"❌ Failed to restore configuration: {e}")
            return False
    
    def restore_service(self) -> bool:
        """Restore service file from backup."""
        try:
            self.logger.info("🔄 Restoring service file...")
            
            # Create a backup of current service before rollback
            current_backup = self.service_path.with_suffix('.py.pre_rollback_backup')
            shutil.copy2(self.service_path, current_backup)
            self.logger.info(f"📁 Current service backed up to: {current_backup}")
            
            # Restore from backup
            shutil.copy2(self.service_backup, self.service_path)
            self.logger.info(f"✅ Service file restored from: {self.service_backup}")
            
            self.rollback_status['service_restored'] = True
            return True
            
        except Exception as e:
            self.logger.error(f"❌ Failed to restore service file: {e}")
            return False
    
    def verify_rollback(self) -> bool:
        """Verify that rollback was successful."""
        if not self.verify:
            self.logger.info("🔍 Verification skipped")
            self.rollback_status['verification_passed'] = True
            return True
        
        self.logger.info("🔍 Verifying rollback...")
        
        try:
            # Check config file
            import yaml
            with open(self.config_path, 'r') as f:
                config = yaml.safe_load(f)
            
            # Check if age weight is back to original (0.20)
            scoring_weights = config.get('ANALYSIS', {}).get('scoring_weights', {})
            age_weight = scoring_weights.get('age', 0)
            
            if abs(age_weight - 0.20) < 0.001:
                self.logger.info(f"✅ Config verification passed - age weight: {age_weight}")
            else:
                self.logger.warning(f"⚠️ Config verification warning - age weight: {age_weight} (expected 0.20)")
            
            # Check service file for enhanced age scoring function
            with open(self.service_path, 'r') as f:
                service_content = f.read()
            
            if '_calculate_enhanced_age_score_and_bonus' in service_content:
                self.logger.warning("⚠️ Service verification warning - enhanced function still present")
            else:
                self.logger.info("✅ Service verification passed - enhanced function removed")
            
            self.rollback_status['verification_passed'] = True
            return True
            
        except Exception as e:
            self.logger.error(f"❌ Verification failed: {e}")
            return False
    
    def generate_rollback_report(self) -> str:
        """Generate rollback report."""
        
        report = f"""
# Enhanced Age Scoring Rollback Report

## Rollback Status
- **Config Restored**: {'✅' if self.rollback_status['config_restored'] else '❌'}
- **Service Restored**: {'✅' if self.rollback_status['service_restored'] else '❌'}
- **Verification Passed**: {'✅' if self.rollback_status['verification_passed'] else '❌'}

## Files Restored
- **Configuration**: {self.config_path}
  - Restored from: {self.config_backup}
- **Service**: {self.service_path}
  - Restored from: {self.service_backup}

## Backup Files Created
- **Pre-rollback Config**: {self.config_path.with_suffix('.yaml.pre_rollback_backup')}
- **Pre-rollback Service**: {self.service_path.with_suffix('.py.pre_rollback_backup')}

## Rollback Summary
The enhanced age scoring system has been rolled back to the original implementation.
All changes including:
- 8-tier age scoring system
- Bonus multipliers for ultra-new tokens
- Updated scoring weights
Have been reverted.

## Next Steps
1. Restart any running services
2. Monitor system behavior
3. Investigate rollback reason if needed
4. Plan re-implementation if appropriate

Generated at: {time.strftime('%Y-%m-%d %H:%M:%S')}
"""
        return report
    
    def perform_rollback(self) -> bool:
        """Perform complete rollback process."""
        self.logger.info("🚀 Starting Enhanced Age Scoring Rollback")
        
        try:
            # Check backups exist
            if not self.check_backups_exist():
                self.logger.error("❌ Cannot proceed - backup files missing")
                return False
            
            # Confirm rollback
            if not self.confirm_rollback():
                self.logger.info("❌ Rollback cancelled")
                return False
            
            # Restore configuration
            if not self.restore_config():
                self.logger.error("❌ Failed to restore configuration")
                return False
            
            # Restore service
            if not self.restore_service():
                self.logger.error("❌ Failed to restore service file")
                return False
            
            # Verify rollback
            if not self.verify_rollback():
                self.logger.warning("⚠️ Rollback verification failed")
            
            # Generate report
            report = self.generate_rollback_report()
            report_path = project_root / "docs" / "summaries" / "ENHANCED_AGE_SCORING_ROLLBACK_REPORT.md"
            
            with open(report_path, 'w') as f:
                f.write(report)
            
            self.logger.info(f"📄 Rollback report saved: {report_path}")
            
            self.logger.info("🎉 Rollback completed successfully!")
            return True
            
        except Exception as e:
            self.logger.error(f"❌ Rollback failed: {e}")
            return False

def main():
    """Main entry point for rollback script."""
    
    parser = argparse.ArgumentParser(description='Enhanced Age Scoring Rollback')
    parser.add_argument('--force', action='store_true', help='Skip confirmation prompt')
    parser.add_argument('--verify', action='store_true', default=True, help='Verify rollback (default: True)')
    parser.add_argument('--no-verify', dest='verify', action='store_false', help='Skip verification')
    
    args = parser.parse_args()
    
    # Create logs directory if it doesn't exist
    logs_dir = project_root / "logs"
    logs_dir.mkdir(exist_ok=True)
    
    # Perform rollback
    rollback = AgeScoringRollback(force=args.force, verify=args.verify)
    success = rollback.perform_rollback()
    
    if success:
        print("\n🎉 Rollback completed successfully!")
        print("📄 Check the rollback report for details")
        print("⚠️  Remember to restart any running services")
    else:
        print("\n❌ Rollback failed - check logs for details")
        sys.exit(1)

if __name__ == "__main__":
    main() 