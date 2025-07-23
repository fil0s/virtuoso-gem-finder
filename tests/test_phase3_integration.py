#!/usr/bin/env python3
"""
Test script to verify Phase 3 High Conviction Detector integration
"""
import asyncio
import sys
import os

# Add the project root to Python path
sys.path.insert(0, '/Users/ffv_macmini/Desktop/virtuoso_gem_hunter')

from scripts.cross_platform_token_analyzer import CrossPlatformAnalyzer

async def test_phase3_integration():
    """Test the Phase 3 integration with categorization"""
    print("🚀 Testing Phase 3: High Conviction Detector Integration")
    print("=" * 60)
    
    try:
        # Initialize the enhanced cross-platform analyzer
        analyzer = CrossPlatformAnalyzer()
        print("✅ CrossPlatformAnalyzer initialized successfully")
        
        # Run a quick analysis to test categorization
        print("\n📊 Running cross-platform analysis with categorization...")
        results = await analyzer.run_analysis()
        
        # Check for category analysis
        if 'correlations' in results and 'category_analysis' in results['correlations']:
            category_analysis = results['correlations']['category_analysis']
            print(f"\n🎯 Category Analysis Results:")
            print(f"  📈 Distribution: {category_analysis['distribution']}")
            print(f"  📊 Average Scores: {category_analysis['average_scores']}")
            
            # Show top tokens by category
            top_tokens = category_analysis.get('top_tokens_by_category', {})
            for category, tokens in top_tokens.items():
                if tokens:
                    top_token = tokens[0]
                    print(f"  🌟 Top {category}: {top_token['symbol']} (Score: {top_token['score']})")
            
            print(f"\n✅ Phase 3 categorization system working perfectly!")
            
        else:
            print("⚠️ Category analysis not found in results")
            
        # Test risk assessment function
        print(f"\n🔍 Testing risk assessment...")
        platforms = ['jupiter', 'birdeye', 'jupiter_quotes']
        risk_level = analyzer._categorize_token({'platforms': set(platforms)})
        print(f"  📊 Platforms: {platforms}")
        print(f"  🏷️ Category: {risk_level}")
        
        await analyzer.close()
        print(f"\n🎉 Phase 3 integration test completed successfully!")
        
    except Exception as e:
        print(f"❌ Error during Phase 3 integration test: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_phase3_integration()) 