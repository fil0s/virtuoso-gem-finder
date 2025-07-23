#!/usr/bin/env python3

import asyncio
import os
import sys
import signal
import time
import json
from datetime import datetime, timedelta
from pathlib import Path

# Add the project root to the Python path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from scripts.high_conviction_token_detector import HighConvictionTokenDetector

class EarlyGemHunter:
    def __init__(self):
        self.detector = None
        self.running = False
        
    def setup_signal_handlers(self):
        """Setup signal handlers for graceful shutdown"""
        def signal_handler(signum, frame):
            print(f"\n🛑 Received signal {signum}, shutting down gracefully...")
            self.running = False
            if self.detector:
                asyncio.create_task(self.detector.cleanup())
            sys.exit(0)
        
        signal.signal(signal.SIGINT, signal_handler)
        signal.signal(signal.SIGTERM, signal_handler)
    
    def modify_config_for_early_gems(self):
        """Temporarily modify config to use early gem hunting weights"""
        import yaml
        
        # Load current config
        with open('config/config.yaml', 'r') as f:
            config = yaml.safe_load(f)
        
        # Switch to early gem scoring weights
        if 'early_gem_scoring_weights' in config['ANALYSIS']:
            config['ANALYSIS']['scoring_weights'] = config['ANALYSIS']['early_gem_scoring_weights']
            print("✅ Switched to early gem hunting scoring weights:")
            for key, value in config['ANALYSIS']['scoring_weights'].items():
                print(f"   {key}: {value*100:.0f}%")
        
        # Use early gem thresholds
        if 'early_gem_hunting' in config['ANALYSIS']['scoring']:
            config['ANALYSIS']['scoring']['cross_platform'] = config['ANALYSIS']['scoring']['early_gem_hunting']
            print("✅ Using early gem hunting thresholds:")
            print(f"   High conviction: {config['ANALYSIS']['scoring']['cross_platform']['high_conviction_threshold']}")
            print(f"   Min candidate: {config['ANALYSIS']['scoring']['cross_platform']['min_candidate_score']}")
        
        # Save modified config temporarily
        with open('config/config_early_gem.yaml', 'w') as f:
            yaml.dump(config, f, default_flow_style=False)
        
        return 'config/config_early_gem.yaml'
    
    async def run_early_gem_detection(self, duration_hours: int = 6):
        """Run early gem detection for specified duration"""
        print("🎯 EARLY GEM HUNTING MODE ACTIVATED")
        print("=" * 60)
        
        # Setup signal handlers
        self.setup_signal_handlers()
        
        # Modify config for early gem hunting
        config_path = self.modify_config_for_early_gems()
        
        try:
            # Initialize detector with early gem config
            self.detector = HighConvictionTokenDetector(config_path=config_path, debug_mode=True)
            
            print(f"🚀 Starting {duration_hours}-hour early gem hunting session...")
            print(f"⏰ Session will end at: {(datetime.now() + timedelta(hours=duration_hours)).strftime('%H:%M:%S')}")
            print("🎯 Optimized for: 0-6 hour tokens, early momentum, whale accumulation")
            print("=" * 60)
            
            self.running = True
            start_time = time.time()
            end_time = start_time + (duration_hours * 3600)
            
            cycle_count = 0
            total_gems_found = 0
            
            while self.running and time.time() < end_time:
                cycle_count += 1
                cycle_start = time.time()
                
                print(f"\n🔍 EARLY GEM HUNTING CYCLE #{cycle_count}")
                print(f"⏰ {datetime.now().strftime('%H:%M:%S')} - Scanning for ultra-early opportunities...")
                
                try:
                    # Run detection cycle
                    result = await self.detector.run_detection_cycle()
                    
                    # Track gems found
                    gems_this_cycle = result.get('high_conviction_count', 0)
                    total_gems_found += gems_this_cycle
                    
                    # Display results
                    cycle_duration = time.time() - cycle_start
                    remaining_time = (end_time - time.time()) / 3600
                    
                    print(f"✅ Cycle #{cycle_count} completed in {cycle_duration:.1f}s")
                    print(f"💎 Gems found this cycle: {gems_this_cycle}")
                    print(f"🏆 Total gems found: {total_gems_found}")
                    print(f"⏰ Time remaining: {remaining_time:.1f} hours")
                    
                    if gems_this_cycle > 0:
                        print(f"🔥 EARLY GEM DETECTED! Check alerts for details.")
                    
                except Exception as e:
                    print(f"❌ Error in detection cycle: {e}")
                    await asyncio.sleep(60)  # Wait before retrying
                
                # Wait 20 minutes between cycles (optimized for early detection)
                if self.running and time.time() < end_time:
                    print(f"⏳ Waiting 20 minutes until next early gem scan...")
                    await asyncio.sleep(1200)  # 20 minutes
            
            print(f"\n🏁 EARLY GEM HUNTING SESSION COMPLETED")
            print(f"📊 Total cycles: {cycle_count}")
            print(f"💎 Total gems found: {total_gems_found}")
            print(f"⏰ Session duration: {duration_hours} hours")
            
        except Exception as e:
            print(f"❌ Critical error in early gem hunting: {e}")
        finally:
            # Cleanup
            if self.detector:
                await self.detector.cleanup()
            
            # Remove temporary config
            if os.path.exists('config/config_early_gem.yaml'):
                os.remove('config/config_early_gem.yaml')
            
            print("🧹 Cleanup completed")

def main():
    import argparse
    
    parser = argparse.ArgumentParser(description='Early Gem Hunter - Optimized for ultra-early token detection')
    parser.add_argument('--hours', type=int, default=6, help='Duration to run in hours (default: 6)')
    args = parser.parse_args()
    
    hunter = EarlyGemHunter()
    asyncio.run(hunter.run_early_gem_detection(args.hours))

if __name__ == "__main__":
    main() 