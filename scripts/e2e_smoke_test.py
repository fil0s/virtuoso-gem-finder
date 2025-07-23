print("[E2E] TEST PRINT - Script is being executed (top of file)")
import os
import sys
import asyncio
import logging
from pathlib import Path

# Improve path handling to avoid import errors
current_dir = Path(__file__).parent.absolute()
project_root = current_dir.parent
sys.path.insert(0, str(project_root))

try:
    from services.early_token_detection import EarlyTokenDetector
    from api.birdeye_connector import BirdeyeAPI
    from api.batch_api_manager import BatchAPIManager
    from core.config_manager import get_config_manager
    from core.cache_manager import CacheManager
    from services.rate_limiter_service import RateLimiterService
except ImportError as e:
    print(f"Import error: {e}")
    print("Try running from project root with: python -m scripts.e2e_smoke_test")
    sys.exit(1)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)
logger.info("[E2E] TEST LOG - Logger is working at module level")

async def run_e2e_smoke_test():
    print("\n🚦 Starting E2E Smoke Test...\n")
    logger.info("[E2E] Starting E2E Smoke Test...")
    print("[E2E] TEST PRINT - Entered run_e2e_smoke_test()")
    try:
        detector = EarlyTokenDetector()
        print("[E2E] Before discover_tokens()")
        logger.info("[E2E] Before discover_tokens()")
        tokens = await detector.discover_tokens()
        print("[E2E] After discover_tokens()")
        logger.info("[E2E] After discover_tokens()")
        print(f"Discovered {len(tokens)} tokens (discover_tokens).")
        if tokens:
            print("\nSample discovered tokens (discover_tokens):")
            for t in tokens[:5]:
                print(f"- {t.get('symbol', 'N/A')}: score={t.get('score')}, trend={t.get('trend_score')}, whale={t.get('whale_score')}, social={t.get('social_score')}")
        else:
            print("No tokens discovered by discover_tokens. Check quality gates and data sources.")
        print("[E2E] Before discover_and_analyze()")
        logger.info("[E2E] Before discover_and_analyze()")
        analyzed_tokens = await detector.discover_and_analyze()
        print("[E2E] After discover_and_analyze()")
        logger.info("[E2E] After discover_and_analyze()")
        print(f"Discovered {len(analyzed_tokens)} tokens (discover_and_analyze).")
        if analyzed_tokens:
            print("\nSample analyzed tokens (discover_and_analyze):")
            for t in analyzed_tokens[:5]:
                print(f"- {t.get('token_symbol', 'N/A')}: score={t.get('token_score')}, reason={t.get('reason', 'N/A')}")
        else:
            print("No tokens discovered by discover_and_analyze. Check quality gates and data sources.")
    except Exception as e:
        print(f"[E2E] Exception occurred: {e}")
        logger.error(f"[E2E] Exception occurred: {e}")
    print("[E2E] TEST PRINT - Exiting run_e2e_smoke_test()")

if __name__ == "__main__":
    print("[E2E] TEST PRINT - Before asyncio.run()")
    logger.info("[E2E] TEST LOG - Before asyncio.run()")
    asyncio.run(run_e2e_smoke_test())
    print("[E2E] TEST PRINT - After asyncio.run()")
    logger.info("[E2E] TEST LOG - After asyncio.run()")

    # Print cache stats if available
    try:
        config = get_config_manager().get_config()
        
        cache_manager = CacheManager()
        rate_limiter = RateLimiterService()
        birdeye_api = BirdeyeAPI(
            config=config.get('BIRDEYE_API', {}),
            logger=logger,
            cache_manager=cache_manager,
            rate_limiter=rate_limiter
        )
        api_manager = BatchAPIManager(birdeye_api, logger)
        hit_rate = api_manager.cache_manager.get_cache_hit_rate()
        print(f"\nCache hit rate: {hit_rate:.2f}%")
    except Exception as e:
        print(f"Cache stats unavailable: {e}") 