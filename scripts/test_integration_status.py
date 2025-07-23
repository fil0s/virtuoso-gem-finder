#!/usr/bin/env python3
"""
Quick test to verify RugCheck integration status
"""

import asyncio
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from services.logger_setup import LoggerSetup
from core.token_discovery_strategies import VolumeMomentumStrategy
from utils.env_loader import load_environment

async def quick_test():
    load_environment()
    logger_setup = LoggerSetup('QuickTest')
    logger = logger_setup.logger
    
    print("🧪 Testing RugCheck Integration Status")
    print("=" * 50)
    
    strategy = VolumeMomentumStrategy(logger=logger)
    print(f'✅ Strategy created')
    print(f'🛡️ RugCheck enabled: {hasattr(strategy, "enable_rugcheck_filtering")}')
    print(f'📝 RugCheck connector available: {hasattr(strategy, "rugcheck_connector")}')
    
    if hasattr(strategy, 'rugcheck_connector') and strategy.rugcheck_connector:
        print('🎯 RugCheck integration is ready!')
        print('✅ Ready to filter risky tokens during monitoring')
    else:
        print('⚠️ RugCheck not initialized - check configuration')
        
    print()
    print("🔧 Configuration Status:")
    if hasattr(strategy, 'enable_rugcheck_filtering'):
        print(f"   • RugCheck filtering: {strategy.enable_rugcheck_filtering}")
    
    if hasattr(strategy, 'config'):
        config = strategy.config
        if 'RUGCHECK' in config:
            rugcheck_config = config['RUGCHECK']
            print(f"   • RugCheck enabled in config: {rugcheck_config.get('enabled', False)}")
            print(f"   • Filter high risk: {rugcheck_config.get('filter_high_risk', False)}")
            print(f"   • Allow safe tokens: {rugcheck_config.get('allow_safe', True)}")

if __name__ == "__main__":
    asyncio.run(quick_test()) 