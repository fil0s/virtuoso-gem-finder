#!/usr/bin/env python3
"""
Test the optimized high conviction detector performance
"""
import asyncio
import sys
import time
sys.path.append('.')

from scripts.high_conviction_token_detector import HighConvictionTokenDetector

async def test_optimized_performance():
    print('🚀 TESTING OPTIMIZED HIGH CONVICTION DETECTOR')
    print('=' * 60)
    
    # Performance tracking
    start_time = time.time()
    
    detector = HighConvictionTokenDetector(debug_mode=True)
    
    print('⚡ Running optimized detection cycle...')
    print('📊 Optimizations applied:')
    print('  • Threshold: 50.0 → 40.0')
    print('  • Parallel processing: 3x concurrent')
    print('  • Pre-filtering: Quality + volume filters')
    print('  • API optimization: Better timeout handling')
    print()
    
    result = await detector.run_detection_cycle()
    
    end_time = time.time()
    total_duration = end_time - start_time
    
    print()
    print('📈 PERFORMANCE COMPARISON:')
    print('=' * 60)
    
    # Previous performance
    prev_duration = 158.1
    prev_tokens = 109
    prev_candidates = 6
    prev_high_conviction = 0
    
    # Current performance
    curr_duration = result.get('cycle_duration_seconds', total_duration)
    curr_tokens = result.get('total_analyzed', 0)
    curr_candidates = result.get('high_conviction_candidates', 0)
    curr_high_conviction = result.get('new_candidates', 0)
    
    print(f'⏱️  SPEED IMPROVEMENT:')
    print(f'  • Before: {prev_duration:.1f}s ({prev_duration/prev_tokens:.2f}s/token)')
    print(f'  • After:  {curr_duration:.1f}s ({curr_duration/curr_tokens:.2f}s/token)' if curr_tokens > 0 else f'  • After:  {curr_duration:.1f}s')
    print(f'  • Speedup: {prev_duration/curr_duration:.1f}x faster')
    print()
    
    print(f'🎯 QUALITY IMPROVEMENT:')
    print(f'  • Candidates Before: {prev_candidates}')
    print(f'  • Candidates After:  {curr_candidates}')
    print(f'  • High Conviction Before: {prev_high_conviction}')
    print(f'  • High Conviction After:  {curr_high_conviction}')
    print()
    
    print(f'💰 EFFICIENCY GAINS:')
    if curr_tokens > 0:
        print(f'  • Tokens Analyzed: {prev_tokens} → {curr_tokens}')
        print(f'  • API Call Reduction: {((prev_tokens - curr_tokens)/prev_tokens)*100:.1f}%')
    print(f'  • Time per Analysis: {prev_duration/prev_candidates:.1f}s → {curr_duration/max(curr_candidates,1):.1f}s')
    print()
    
    # Show detailed analysis results if available
    detailed_analyses = result.get('detailed_analyses_data', [])
    if detailed_analyses:
        print('🎯 HIGH CONVICTION RESULTS:')
        print('=' * 60)
        
        for i, analysis in enumerate(detailed_analyses, 1):
            if analysis and 'scoring_breakdown' in analysis:
                candidate = analysis['candidate']
                breakdown = analysis['scoring_breakdown']
                final_score = analysis['final_score']
                
                print(f'{i}. {candidate["symbol"]} - Score: {final_score:.1f}')
                print(f'   Address: {candidate["address"][:20]}...')
                
                # Show if it meets the new threshold
                threshold_status = "✅ HIGH CONVICTION" if final_score >= 40.0 else "⚠️  Below Threshold"
                print(f'   Status: {threshold_status}')
                
                # Quick breakdown
                summary = breakdown.get('final_score_summary', {})
                print(f'   Components: Base({summary.get("base_score", 0):.1f}) + Overview({summary.get("overview_score", 0):.1f}) + Volume({summary.get("volume_score", 0):.1f}) + Trading({summary.get("trading_score", 0):.1f})')
                print()
    
    await detector.cleanup()
    
    print('✅ OPTIMIZATION TEST COMPLETED!')
    print(f'🏆 Overall Performance: {prev_duration/curr_duration:.1f}x improvement')

if __name__ == "__main__":
    asyncio.run(test_optimized_performance())
