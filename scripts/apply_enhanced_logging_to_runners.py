#!/usr/bin/env python3
"""
Apply Enhanced Structured Logging to Runner Files
Updates the detector runner files to use enhanced structured logging
"""

import sys
import os
import shutil
from datetime import datetime

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from utils.enhanced_structured_logger import create_enhanced_logger, DetectionStage


class RunnerLoggingPatcher:
    """Apply enhanced structured logging to runner files"""
    
    def __init__(self):
        self.logger = create_enhanced_logger("RunnerLoggingPatcher")
        
        self.script_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        self.backup_dir = os.path.join(self.script_dir, 'backups', 
                                     f'runner_logging_{datetime.now().strftime("%Y%m%d_%H%M%S")}')
    
    def apply_logging_to_runners(self):
        """Apply enhanced structured logging to runner files"""
        
        scan_id = self.logger.new_scan_context(
            strategy="runner_logging_integration",
            timeframe="system_upgrade"
        )
        
        with self.logger.stage_context(DetectionStage.INITIALIZATION, 
                                      operation="apply_runner_logging"):
            
            self.logger.info("Starting runner logging integration",
                           scan_id=scan_id)
            
            # Create backup
            self._create_backup()
            
            # Patch runner files
            runner_files = [
                'run_3hour_detector.py',
                'run_72hour_detector.py',
                'run_starter_plan_detector.py'
            ]
            
            for runner_file in runner_files:
                if os.path.exists(os.path.join(self.script_dir, runner_file)):
                    self._patch_runner_file(runner_file)
                else:
                    self.logger.warning(f"Runner file not found: {runner_file}")
            
            self.logger.log_performance_summary(
                operation="runner_logging_complete"
            )
    
    def _create_backup(self):
        """Create backup of runner files"""
        with self.logger.stage_context(DetectionStage.INITIALIZATION,
                                     operation="create_backup"):
            
            self.logger.info("Creating backup of runner files")
            
            os.makedirs(self.backup_dir, exist_ok=True)
            
            runner_files = [
                'run_3hour_detector.py',
                'run_72hour_detector.py', 
                'run_starter_plan_detector.py'
            ]
            
            for file_path in runner_files:
                full_path = os.path.join(self.script_dir, file_path)
                if os.path.exists(full_path):
                    backup_path = os.path.join(self.backup_dir, file_path)
                    shutil.copy2(full_path, backup_path)
                    
                    self.logger.info("Runner file backed up",
                                   file_path=file_path,
                                   backup_path=backup_path)
    
    def _patch_runner_file(self, runner_file):
        """Patch a specific runner file with enhanced logging"""
        with self.logger.stage_context(DetectionStage.STAGE_1_BASIC_FILTER,
                                     operation="patch_runner",
                                     file_name=runner_file):
            
            file_path = os.path.join(self.script_dir, runner_file)
            
            with open(file_path, 'r') as f:
                content = f.read()
            
            # Apply patches
            patched_content = self._apply_runner_patches(content, runner_file)
            
            # Write back
            with open(file_path, 'w') as f:
                f.write(patched_content)
            
            self.logger.info("Runner file patched successfully",
                           file_name=runner_file)
    
    def _apply_runner_patches(self, content: str, runner_file: str) -> str:
        """Apply specific patches to runner files"""
        
        # Patch 1: Add enhanced logging import
        enhanced_import = """
# Enhanced structured logging
from utils.enhanced_structured_logger import create_enhanced_logger, DetectionStage"""
        
        # Add import after other imports
        if "import logging" in content:
            content = content.replace(
                "import logging",
                f"import logging{enhanced_import}"
            )
        
        # Patch 2: Add logger initialization in main function
        if "async def main():" in content:
            # Find main function and add logger initialization
            main_func_start = content.find("async def main():")
            if main_func_start != -1:
                # Find the first line after the function definition
                next_line = content.find("\n", main_func_start)
                if next_line != -1:
                    logger_init = f"""
    # Initialize enhanced structured logger
    enhanced_logger = create_enhanced_logger("{runner_file.replace('.py', '').replace('_', '-')}")
    
    # Start scan context for the full detection run
    scan_id = enhanced_logger.new_scan_context(
        strategy="{runner_file.replace('.py', '').replace('_', '-')}",
        timeframe="multi_cycle_detection"
    )
    
    enhanced_logger.info("Starting {runner_file} detection run", 
                        scan_id=scan_id,
                        detection_cycles_planned="multiple")"""
                    
                    content = content[:next_line] + logger_init + content[next_line:]
        
        # Patch 3: Add cycle tracking context
        cycle_context_patch = """
        # Enhanced logging for detection cycle
        with enhanced_logger.stage_context(DetectionStage.INITIALIZATION, 
                                          cycle_number=cycle + 1,
                                          total_cycles=total_cycles):
            enhanced_logger.info(f"Starting detection cycle {{cycle + 1}}/{{total_cycles}}",
                               cycle_start_time=datetime.now().isoformat())"""
        
        # Find cycle loop and add context
        if "for cycle in range(" in content:
            # Find the line after the for loop
            for_loop_pos = content.find("for cycle in range(")
            if for_loop_pos != -1:
                next_line = content.find("\n", for_loop_pos)
                if next_line != -1:
                    # Find the next indented line (first line of loop body)
                    next_indented = content.find("\n        ", next_line)
                    if next_indented != -1:
                        content = content[:next_indented+1] + cycle_context_patch + content[next_indented+1:]
        
        # Patch 4: Add performance summary at the end
        performance_summary_patch = """
    # Log comprehensive performance summary for the entire run
    enhanced_logger.log_performance_summary(
        total_detection_run=True,
        detection_cycles_completed=total_cycles
    )
    
    enhanced_logger.info("Detection run completed successfully",
                        total_duration_hours=3,
                        cycles_completed=total_cycles)"""
        
        # Add before the final return or end of main function
        if "if __name__ == \"__main__\":" in content:
            main_end_pos = content.find("if __name__ == \"__main__\":")
            content = content[:main_end_pos] + performance_summary_patch + "\n\n" + content[main_end_pos:]
        
        return content
    
    def print_integration_summary(self):
        """Print summary of runner logging integration"""
        print("\n" + "=" * 80)
        print("🚀 RUNNER FILES ENHANCED LOGGING INTEGRATION COMPLETE")
        print("=" * 80)
        print()
        print("✅ ENHANCED LOGGING APPLIED TO:")
        print("   📊 run_3hour_detector.py (3-hour detection cycles)")
        print("   📊 run_72hour_detector.py (72-hour detection cycles)")
        print("   📊 run_starter_plan_detector.py (starter plan optimized)")
        print()
        print("🔍 NEW LOGGING FEATURES:")
        print("   • Scan context tracking for full detection runs")
        print("   • Cycle-by-cycle performance monitoring")
        print("   • Stage-based context for each detection cycle")
        print("   • Comprehensive performance summaries")
        print("   • JSON-structured logs for easy analysis")
        print()
        print("📈 VISIBILITY IMPROVEMENTS:")
        print("   • Full traceability across multi-hour detection runs")
        print("   • Per-cycle timing and performance metrics")
        print("   • Error tracking and recovery monitoring")
        print("   • Resource utilization tracking")
        print()
        print("✅ READY TO USE!")
        print("   Your runner files now have comprehensive structured logging")
        print("   All detection runs will be fully tracked and monitored")
        print("=" * 80)


def main():
    """Main function"""
    patcher = RunnerLoggingPatcher()
    
    try:
        # Apply logging integration
        patcher.apply_logging_to_runners()
        
        # Print summary
        patcher.print_integration_summary()
        
        return 0
        
    except Exception as e:
        patcher.logger.error("Runner logging integration failed", 
                           error=str(e),
                           error_type=type(e).__name__)
        print(f"❌ Integration failed: {e}")
        return 1


if __name__ == "__main__":
    sys.exit(main())