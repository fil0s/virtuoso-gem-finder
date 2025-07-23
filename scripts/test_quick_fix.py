#!/usr/bin/env python3

import asyncio
import sys
import os
sys.path.append('..')

from cross_platform_token_analyzer import CrossPlatformAnalyzer

async def test_fix():
    analyzer = CrossPlatformAnalyzer()
    try:
        # Test a quick data collection
        print('🧪 Testing data collection...')
        platform_data = await analyzer.collect_all_data()
        print(f'📊 Platform data counts: {[(k, len(v)) for k, v in platform_data.items()]}')
        
        # Test normalization
        print('🔄 Testing normalization...')
        normalized = analyzer.normalize_token_data(platform_data)
        print(f'✅ Normalized {len(normalized)} tokens')
        
        print('🎉 Quick test passed!')
        return True
        
    except Exception as e:
        print(f'❌ Test failed: {e}')
        import traceback
        traceback.print_exc()
        return False
    finally:
        await analyzer.close()

if __name__ == "__main__":
    success = asyncio.run(test_fix())
    sys.exit(0 if success else 1) 