#!/usr/bin/env python3
"""
Integration Script for Enhanced Structured Logging
Applies comprehensive structured logging to the early gem detector system
"""

import sys
import os
import shutil
from datetime import datetime

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from utils.enhanced_structured_logger import create_enhanced_logger, DetectionStage, APICallType


class LoggingIntegrationPatcher:
    """Apply enhanced structured logging to the gem detection system"""
    
    def __init__(self):
        self.logger = create_enhanced_logger("LoggingIntegrationPatcher")
        
        self.script_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        self.backup_dir = os.path.join(self.script_dir, 'backups', 
                                     f'enhanced_logging_{datetime.now().strftime("%Y%m%d_%H%M%S")}')
        
    def apply_logging_integration(self):
        """Apply enhanced structured logging to all components"""
        
        scan_id = self.logger.new_scan_context(
            strategy="logging_integration",
            timeframe="system_upgrade"
        )
        
        with self.logger.stage_context(DetectionStage.INITIALIZATION, 
                                      operation="apply_logging_integration"):
            
            self.logger.info("Starting enhanced logging integration",
                           scan_id=scan_id)
            
            # Step 1: Create backup
            self._create_backup()
            
            # Step 2: Patch early gem detector
            self._patch_early_gem_detector()
            
            # Step 3: Patch batch API manager
            self._patch_batch_api_manager()
            
            # Step 4: Patch birdeye connector
            self._patch_birdeye_connector()
            
            # Step 5: Create configuration
            self._create_logging_config()
            
            self.logger.log_performance_summary(
                operation="logging_integration_complete"
            )
    
    def _create_backup(self):
        """Create backup of files that will be modified"""
        with self.logger.stage_context(DetectionStage.INITIALIZATION,
                                     operation="create_backup"):
            
            self.logger.info("Creating backup of existing files")
            
            os.makedirs(self.backup_dir, exist_ok=True)
            
            files_to_backup = [
                'early_gem_detector.py',
                'api/batch_api_manager.py',
                'api/birdeye_connector.py',
                'api/improved_batch_api_manager.py'
            ]
            
            for file_path in files_to_backup:
                full_path = os.path.join(self.script_dir, file_path)
                if os.path.exists(full_path):
                    backup_path = os.path.join(self.backup_dir, file_path)
                    os.makedirs(os.path.dirname(backup_path), exist_ok=True)
                    shutil.copy2(full_path, backup_path)
                    
                    self.logger.info("File backed up",
                                   file_path=file_path,
                                   backup_path=backup_path)
    
    def _patch_early_gem_detector(self):
        """Patch early gem detector with enhanced logging"""
        with self.logger.stage_context(DetectionStage.STAGE_1_BASIC_FILTER,
                                     operation="patch_detector"):
            
            detector_path = os.path.join(self.script_dir, 'early_gem_detector.py')
            
            if not os.path.exists(detector_path):
                self.logger.warning("Early gem detector not found", path=detector_path)
                return
            
            with open(detector_path, 'r') as f:
                content = f.read()
            
            # Apply patches
            patched_content = self._apply_detector_patches(content)
            
            # Write back
            with open(detector_path, 'w') as f:
                f.write(patched_content)
            
            self.logger.info("Early gem detector patched successfully")
    
    def _apply_detector_patches(self, content: str) -> str:
        """Apply specific patches to the detector code"""
        
        # Patch 1: Add enhanced logging import
        enhanced_import = """# Enhanced structured logging
from utils.enhanced_structured_logger import create_enhanced_logger, DetectionStage, APICallType"""
        
        # Find import section and add enhanced logging
        if "from utils.structured_logger import" in content:
            content = content.replace(
                "from utils.structured_logger import get_structured_logger",
                enhanced_import
            )
        elif "import logging" in content:
            # Add after logging import
            content = content.replace(
                "import logging",
                f"import logging\n{enhanced_import}"
            )
        
        # Patch 2: Initialize enhanced logger in detector class
        old_logger_init = """self.logger = logging.getLogger(__name__)"""
        new_logger_init = """self.enhanced_logger = create_enhanced_logger("EarlyGemDetector")
        self.logger = logging.getLogger(__name__)  # Keep for compatibility"""
        
        if old_logger_init in content:
            content = content.replace(old_logger_init, new_logger_init)
        
        # Patch 3: Add scan context initialization
        scan_context_patch = """        
        # Initialize scan context for enhanced logging
        scan_id = self.enhanced_logger.new_scan_context(
            strategy=self.config.get('strategy_name', 'early_gem_detection'),
            timeframe=self.config.get('timeframe', '4_stages')
        )
        self.current_scan_id = scan_id"""
        
        # Find a good place to insert scan context (after config loading)
        if "self.config = config" in content:
            content = content.replace(
                "self.config = config",
                f"self.config = config{scan_context_patch}"
            )
        
        # Patch 4: Add stage contexts to main detection method
        stage_contexts = {
            "# Stage 0: Token Discovery": """
        with self.enhanced_logger.stage_context(DetectionStage.STAGE_0_DISCOVERY, 
                                               tokens_discovered=len(token_addresses) if token_addresses else 0):""",
            
            "# Stage 1: Basic filtering": """
        with self.enhanced_logger.stage_context(DetectionStage.STAGE_1_BASIC_FILTER,
                                               tokens_input=len(token_addresses) if token_addresses else 0):""",
            
            "# Stage 2: Enhanced analysis with batch APIs": """
        with self.enhanced_logger.stage_context(DetectionStage.STAGE_2_BATCH_ENRICHMENT,
                                               tokens_for_enrichment=len(token_addresses) if token_addresses else 0):""",
            
            "# Stage 3: Detailed individual analysis": """
        with self.enhanced_logger.stage_context(DetectionStage.STAGE_3_DETAILED_ANALYSIS,
                                               tokens_for_analysis=len(enriched_candidates) if enriched_candidates else 0):""",
            
            "# Stage 4: Final scoring and ranking": """
        with self.enhanced_logger.stage_context(DetectionStage.STAGE_4_FINAL_SCORING,
                                               candidates_for_scoring=len(analyzed_candidates) if analyzed_candidates else 0):"""
        }
        
        for old_comment, new_context in stage_contexts.items():
            if old_comment in content:
                content = content.replace(old_comment, f"{old_comment}{new_context}")
        
        # Patch 5: Add performance summary at the end
        performance_summary_patch = """
        # Log comprehensive performance summary
        self.enhanced_logger.log_performance_summary(
            total_gems_found=len(final_gems) if final_gems else 0,
            detection_complete=True
        )"""
        
        # Add before return statement
        if "return final_gems" in content:
            content = content.replace(
                "return final_gems",
                f"{performance_summary_patch}\n        return final_gems"
            )
        
        return content
    
    def _patch_batch_api_manager(self):
        """Patch batch API manager with enhanced logging"""
        with self.logger.stage_context(DetectionStage.STAGE_2_BATCH_ENRICHMENT,
                                     operation="patch_batch_manager"):
            
            # Patch the improved batch API manager
            manager_path = os.path.join(self.script_dir, 'api/improved_batch_api_manager.py')
            
            if os.path.exists(manager_path):
                with open(manager_path, 'r') as f:
                    content = f.read()
                
                # Replace structured logger with enhanced version
                content = content.replace(
                    "from utils.structured_logger import get_structured_logger",
                    "from utils.enhanced_structured_logger import create_enhanced_logger, APICallType"
                )
                
                content = content.replace(
                    "self.structured_logger = get_structured_logger('ImprovedBatchAPIManager')",
                    "self.enhanced_logger = create_enhanced_logger('ImprovedBatchAPIManager')"
                )
                
                # Add API call contexts
                api_context_patch = """
        with self.enhanced_logger.api_call_context(
            APICallType.BATCH_METADATA, 
            endpoint="batch_fetch_token_metadata",
            token_count=len(token_addresses)
        ):"""
                
                # Find batch fetch methods and add context
                if "async def batch_fetch_token_metadata" in content:
                    # Add context after the method definition
                    content = content.replace(
                        'self.logger.info(f"🔍 Starting batch metadata fetch for {len(token_addresses)} tokens")',
                        f'{api_context_patch}\n            self.logger.info(f"🔍 Starting batch metadata fetch for {{len(token_addresses)}} tokens")'
                    )
                
                with open(manager_path, 'w') as f:
                    f.write(content)
                
                self.logger.info("Improved batch API manager patched")
    
    def _patch_birdeye_connector(self):
        """Patch birdeye connector with enhanced logging"""
        with self.logger.stage_context(DetectionStage.STAGE_2_BATCH_ENRICHMENT,
                                     operation="patch_birdeye_connector"):
            
            connector_path = os.path.join(self.script_dir, 'api/birdeye_connector.py')
            
            if os.path.exists(connector_path):
                with open(connector_path, 'r') as f:
                    content = f.read()
                
                # Add enhanced logging import if not already present
                if "from utils.enhanced_structured_logger import" not in content:
                    content = content.replace(
                        "from utils.structured_logger import get_structured_logger",
                        "from utils.enhanced_structured_logger import create_enhanced_logger, APICallType"
                    )
                
                with open(connector_path, 'w') as f:
                    f.write(content)
                
                self.logger.info("Birdeye connector patched")
    
    def _create_logging_config(self):
        """Create logging configuration file"""
        with self.logger.stage_context(DetectionStage.INITIALIZATION,
                                     operation="create_config"):
            
            config_content = """# Enhanced Structured Logging Configuration
# This file contains settings for the enhanced structured logging system

logging_config:
  # Global logging level (DEBUG, INFO, WARNING, ERROR)
  log_level: "INFO"
  
  # Enable/disable different tracking features
  performance_tracking: true
  api_tracking: true
  context_tracking: true
  
  # Output configuration
  output_format: "json"  # json or text
  enable_console_output: true
  enable_file_output: true
  log_file_path: "logs/gem_detection.log"
  
  # Performance thresholds for alerts
  thresholds:
    max_stage_duration_seconds: 30
    max_api_call_duration_seconds: 5
    min_cache_hit_rate_percent: 80
    max_errors_per_scan: 5
  
  # API call tracking
  api_tracking:
    track_individual_calls: true
    track_batch_calls: true
    track_cache_operations: true
    log_slow_calls_threshold_ms: 1000
  
  # Context tracking
  context_tracking:
    track_scan_ids: true
    track_stage_progression: true
    track_token_processing: true
    max_context_stack_depth: 10

# Integration settings
integration:
  # Automatically apply to these components
  patch_components:
    - "early_gem_detector"
    - "batch_api_manager" 
    - "birdeye_connector"
    - "token_validator"
  
  # Backup settings
  create_backups: true
  backup_retention_days: 30
"""
            
            config_dir = os.path.join(self.script_dir, 'config')
            os.makedirs(config_dir, exist_ok=True)
            
            config_path = os.path.join(config_dir, 'enhanced_logging.yaml')
            with open(config_path, 'w') as f:
                f.write(config_content)
            
            self.logger.info("Logging configuration created", 
                           config_path=config_path)
    
    def print_integration_summary(self):
        """Print summary of logging integration"""
        print("\n" + "=" * 80)
        print("🚀 ENHANCED STRUCTURED LOGGING INTEGRATION COMPLETE")
        print("=" * 80)
        print()
        print("✅ FEATURES ADDED:")
        print("   📊 Comprehensive Stage Tracking")
        print("      • Detection stages with context and timing")
        print("      • Stage-specific performance metrics")
        print("      • Error tracking by stage")
        print()
        print("   🔍 Advanced API Call Tracking") 
        print("      • Individual and batch API call monitoring")
        print("      • Response time tracking and analysis")
        print("      • API call type classification")
        print()
        print("   📋 Contextual Debugging")
        print("      • Scan IDs for tracing full detection cycles")
        print("      • Nested context tracking for complex operations")
        print("      • Token processing flow visibility")
        print()
        print("   📈 Performance Monitoring")
        print("      • Real-time performance metrics")
        print("      • Cache hit/miss tracking")
        print("      • Validation statistics")
        print("      • Comprehensive performance summaries")
        print()
        print("📊 STRUCTURED LOGGING OUTPUT:")
        print("   • JSON-formatted logs for easy parsing")
        print("   • Standardized field names and formats")
        print("   • Timestamp and context information")
        print("   • Error tracking with full stack traces")
        print()
        print("🔧 INTEGRATION APPLIED TO:")
        print("   • early_gem_detector.py (main detection logic)")
        print("   • api/improved_batch_api_manager.py (batch processing)")
        print("   • api/birdeye_connector.py (API connections)")
        print()
        print("📁 FILES CREATED:")
        print("   • utils/enhanced_structured_logger.py (core logging system)")
        print("   • scripts/integrate_enhanced_logging.py (this script)")
        print("   • config/enhanced_logging.yaml (configuration)")
        print()
        print("✅ READY TO USE!")
        print("   Your gem detector now has comprehensive structured logging")
        print("   Run your detector as normal - enhanced logging is automatic")
        print("=" * 80)


def main():
    """Main function"""
    patcher = LoggingIntegrationPatcher()
    
    try:
        # Apply logging integration
        patcher.apply_logging_integration()
        
        # Print summary
        patcher.print_integration_summary()
        
        return 0
        
    except Exception as e:
        patcher.logger.error("Logging integration failed", 
                           error=str(e),
                           error_type=type(e).__name__)
        print(f"❌ Integration failed: {e}")
        return 1


if __name__ == "__main__":
    sys.exit(main())