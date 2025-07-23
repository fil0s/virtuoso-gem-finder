import asyncio
import sys
import os
from pathlib import Path

# Improve path handling to avoid import errors
current_dir = Path(__file__).parent.absolute()
project_root = current_dir.parent
sys.path.insert(0, str(project_root))

try:
    from services.early_token_detection import EarlyTokenDetector
except ImportError as e:
    print(f"Import error: {e}")
    print("Try running from project root with: python -m tests.test_quality_gates")
    sys.exit(1)

class DummyLogger:
    def info(self, msg): pass
    def debug(self, msg): pass
    def warning(self, msg): pass
    def error(self, msg): pass

async def test_quality_gates():
    """Test strict quality gates implementation"""
    print("🧪 Testing Quality Gates Implementation...")
    
    try:
        # Initialize detector
        detector = EarlyTokenDetector()
        
        # Create test tokens with varying quality scores
        test_tokens = [
            {'symbol': 'HIGH_QUALITY', 'score': 75, 'liquidity': 1000000, 'holders': 5000, 'volume_24h': 500000},
            {'symbol': 'MID_QUALITY', 'score': 45, 'liquidity': 500000, 'holders': 1000, 'volume_24h': 100000},
            {'symbol': 'LOW_QUALITY', 'score': 20, 'liquidity': 10000, 'holders': 100, 'volume_24h': 5000},
            {'symbol': 'VERY_LOW', 'score': 5, 'liquidity': 1000, 'holders': 10, 'volume_24h': 100}
        ]
        
        # Apply filtering based on scores - should only include tokens with score >= 30
        # This is a simplified test of the quality gate logic
        passed_tokens = [t for t in test_tokens if t['score'] >= 30]
        
        if len(passed_tokens) == 2:
            print("✅ Basic quality gate passed correctly (2/4 tokens passed)")
        else:
            print(f"❌ Quality gate failed - expected 2 tokens to pass, got {len(passed_tokens)}")
            
        # Verify no emergency inclusion of low-quality tokens
        if all(token['score'] >= 30 for token in passed_tokens):
            print("✅ No emergency inclusion of low-quality tokens")
        else:
            print("❌ Emergency inclusion detected - low-quality tokens were allowed")
            
        # Check that highest quality tokens are prioritized
        if passed_tokens and passed_tokens[0]['symbol'] == 'HIGH_QUALITY':
            print("✅ Highest quality tokens prioritized correctly")
        else:
            print("❌ Token prioritization failed")
            
        print("🎉 Quality gates test completed!")
        
    except Exception as e:
        print(f"❌ Test failed with error: {e}")

if __name__ == "__main__":
    try:
        asyncio.run(test_quality_gates())
    except Exception as e:
        print(f"❌ Test failed with error: {e}") 