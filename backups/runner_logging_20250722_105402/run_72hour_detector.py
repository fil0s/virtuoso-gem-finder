#!/usr/bin/env python3
"""
72-Hour Early Gem Detector - Hourly Scans
Runs scans every hour for 72 hours (72 total cycles)
Provides detailed scan summary for each cycle and comprehensive final summary
"""

import asyncio
import sys
import os
import time
import logging
from datetime import datetime, timedelta

# Add current directory to path
sys.path.append(os.getcwd())

# Configure logging to reduce detector console output duplication
# This will be applied after detector initialization

def _display_detailed_scan_summary(detector, result, cycle_number, total_cycles):
    """Display detailed scan summary with tables if available"""
    try:
        # Try to import prettytable for enhanced display
        try:
            from prettytable import PrettyTable
            has_prettytable = True
        except ImportError:
            has_prettytable = False
        
        print(f"\n📊 SCAN #{cycle_number}/{total_cycles} SUMMARY:")
        print("-" * 50)
        
        # Display token breakdown with all metrics included
        _display_cycle_token_breakdown(detector, result, cycle_number, has_prettytable)
        
        # Display API usage for this cycle
        if has_prettytable:
            api_table = PrettyTable()
            api_table.field_names = ["Platform", "Calls", "Success Rate", "Avg Response"]
            api_table.align = "l"
            
            api_usage = detector.session_stats.get('api_usage_by_service', {})
            for platform, stats in api_usage.items():
                calls = stats.get('total_calls', 0)
                successes = stats.get('successful_calls', 0)
                success_rate = (successes / max(1, calls)) * 100
                avg_response = stats.get('avg_response_time_ms', 0)
                
                api_table.add_row([
                    platform.title(),
                    str(calls),
                    f"{success_rate:.1f}%",
                    f"{avg_response:.0f}ms"
                ])
            
            print(f"\n📡 API PERFORMANCE THIS CYCLE:")
            print(api_table)
        
        print("-" * 50)
        
    except Exception as e:
        print(f"⚠️ Error in detailed scan summary: {e}")

def _display_session_summary_tables(detector):
    """Display comprehensive session summary with tables"""
    try:
        # Try to import prettytable
        try:
            from prettytable import PrettyTable
            has_prettytable = True
        except ImportError:
            has_prettytable = False
            
        if not has_prettytable:
            print("📊 Enhanced tables require 'prettytable' package")
            return
            
        print(f"\n📊 COMPREHENSIVE SESSION SUMMARY:")
        print("=" * 80)
        
        # Overall statistics table
        overview_table = PrettyTable()
        overview_table.field_names = ["Metric", "Count", "Percentage"]
        overview_table.align = "l"
        
        session_stats = detector.session_stats
        total_tokens = session_stats.get('tokens_analyzed', 0)
        high_conviction = session_stats.get('high_conviction_found', 0)
        alerts_sent = session_stats.get('alerts_sent', 0)
        
        overview_table.add_row([
            "🎯 Total Tokens Analyzed", 
            str(total_tokens), 
            "100.0%"
        ])
        
        if high_conviction > 0:
            overview_table.add_row([
                "🔥 High Conviction Tokens", 
                str(high_conviction), 
                f"{(high_conviction/max(total_tokens, 1)*100):.1f}%"
            ])
            
        if alerts_sent > 0:
            overview_table.add_row([
                "📱 Alerts Sent", 
                str(alerts_sent), 
                f"{(alerts_sent/max(high_conviction, 1)*100):.1f}%"
            ])
        
        print(f"\n{overview_table}")
        
        # Enhanced API usage summary table
        api_usage = detector.session_stats.get('api_usage_by_service', {})
        if api_usage:
            api_summary_table = PrettyTable()
            api_summary_table.field_names = ["Platform", "Total Calls", "Success Rate", "Cost (USD)", "Type"]
            api_summary_table.align = "l"
            
            # Platform categorization for better display
            platform_types = {
                'birdeye': 'Traditional',
                'dexscreener': 'Traditional', 
                'rugcheck': 'Traditional',
                'moralis': 'Discovery',
                'pump_fun': 'Discovery',
                'launchlab': 'Discovery'
            }
            
            for platform, stats in api_usage.items():
                calls = stats.get('total_calls', 0)
                successes = stats.get('successful_calls', 0)
                success_rate = (successes / max(1, calls)) * 100
                cost = stats.get('estimated_cost_usd', 0.0)
                platform_type = platform_types.get(platform, 'Unknown')
                
                api_summary_table.add_row([
                    platform.title(),
                    str(calls),
                    f"{success_rate:.1f}%",
                    f"${cost:.4f}",
                    platform_type
                ])
            
            print(f"\n📡 ENHANCED API USAGE SUMMARY:")
            print(api_summary_table)
        
        print("=" * 80)
        
    except Exception as e:
        print(f"⚠️ Error in session summary tables: {e}")

def _display_scoring_analysis(detector, result, cycle_number):
    """Display scoring analysis"""
    try:
        print(f"\n🎯 SCORING ANALYSIS:")
        print("-" * 50)
        
        # Get scoring data from detector
        session_stats = getattr(detector, 'session_stats', {})
        
        # Score distribution analysis
        all_candidates = result.get('all_candidates', [])
        if all_candidates:
            scores = [candidate.get('final_score', candidate.get('score', 0)) for candidate in all_candidates]
            if scores:
                avg_score = sum(scores) / len(scores)
                max_score = max(scores)
                min_score = min(scores)
                
                print(f"📊 Score Statistics:")
                print(f"  • Average Score: {avg_score:.1f}")
                print(f"  • Highest Score: {max_score:.1f}")
                print(f"  • Lowest Score: {min_score:.1f}")
                print(f"  • Total Tokens: {len(scores)}")
                
                # Score distribution ranges
                high_score = sum(1 for s in scores if s >= 70)
                medium_score = sum(1 for s in scores if 50 <= s < 70)
                low_score = sum(1 for s in scores if s < 50)
                
                print(f"\n📈 Score Distribution:")
                print(f"  • High (70+): {high_score} tokens ({(high_score/len(scores)*100):.1f}%)")
                print(f"  • Medium (50-69): {medium_score} tokens ({(medium_score/len(scores)*100):.1f}%)")
                print(f"  • Low (<50): {low_score} tokens ({(low_score/len(scores)*100):.1f}%)")
        else:
            print("  📊 No scoring data available for this cycle")
        
        print("-" * 50)
        
    except Exception as e:
        print(f"⚠️ Error in scoring analysis: {e}")

def _display_cycle_token_breakdown(detector, result, cycle_number, has_prettytable):
    """Display breakdown of tokens found in this cycle"""
    try:
        # Display basic scan metrics first
        total_analyzed = result.get('total_analyzed', 0)
        high_conviction_found = len(result.get('high_conviction_tokens', []))
        alerts_sent = result.get('alerts_sent', 0)
        cycle_time = result.get('cycle_time', 0)
        
        print(f"🔍 Analyzed: {total_analyzed} tokens | 🎯 High Conviction: {high_conviction_found} | 📱 Alerts: {alerts_sent} | ⏱️ Duration: {cycle_time:.1f}s")
        
        # Get tokens from this cycle
        high_conviction_tokens = result.get('high_conviction_tokens', [])
        all_candidates = result.get('all_candidates', [])
        
        if not high_conviction_tokens and not all_candidates:
            print(f"\n📊 No tokens discovered in Cycle #{cycle_number}")
            return
        
        # Sort high conviction tokens by score (highest first)
        high_conviction_tokens.sort(key=lambda x: x.get('score', 0), reverse=True)
        
        if has_prettytable:
            from prettytable import PrettyTable
            
            if high_conviction_tokens:
                # Create high conviction tokens table
                tokens_table = PrettyTable()
                tokens_table.field_names = ["Rank", "Symbol", "Score", "Market Cap", "Source", "Full Address"]
                tokens_table.align = "l"
                
                for i, token in enumerate(high_conviction_tokens, 1):
                    symbol = token.get('symbol', 'Unknown')[:12]  # Truncate long symbols
                    score = token.get('score', 0)
                    market_cap = token.get('market_cap', token.get('marketCap', 0))
                    source = token.get('source', 'unknown')
                    address = token.get('address', token.get('token_address', 'Unknown'))
                    
                    # Format market cap
                    mc_str = f"${market_cap:,.0f}" if market_cap > 0 else "N/A"
                    
                    tokens_table.add_row([
                        f"{i}.",
                        symbol,
                        f"{score:.1f}",
                        mc_str,
                        source,
                        address
                    ])
                
                print(f"\n🚀 HIGH CONVICTION TOKENS ({len(high_conviction_tokens)}):")
                print(tokens_table)
            
            # Show score distribution
            _display_score_distribution(all_candidates)
            
        else:
            # Fallback without prettytable
            if high_conviction_tokens:
                print(f"\n🚀 HIGH CONVICTION TOKENS ({len(high_conviction_tokens)}):")
                
                for i, token in enumerate(high_conviction_tokens, 1):
                    symbol = token.get('symbol', 'Unknown')
                    score = token.get('score', 0)
                    market_cap = token.get('market_cap', token.get('marketCap', 0))
                    source = token.get('source', 'unknown')
                    address = token.get('address', token.get('token_address', 'Unknown'))
                    
                    # Format market cap
                    mc_str = f"${market_cap:,.0f}" if market_cap > 0 else "N/A"
                    
                    print(f"  {i}. {symbol} - Score: {score:.1f} - MC: {mc_str} - Source: {source} - Address: {address}")
            
            # Show basic score distribution
            _display_score_distribution(all_candidates)
        
    except Exception as e:
        print(f"⚠️ Error displaying cycle token breakdown: {e}")

def _display_score_distribution(candidates):
    """Display score distribution of candidates"""
    if not candidates:
        return
    
    scores = [candidate.get('final_score', candidate.get('score', 0)) for candidate in candidates]
    
    # Score distribution
    high_score = sum(1 for s in scores if s >= 70)
    medium_score = sum(1 for s in scores if 50 <= s < 70)
    low_score = sum(1 for s in scores if s < 50)
    
    print(f"\n📊 Score Distribution: 🟢 High ({high_score}) | 🟡 Medium ({medium_score}) | ⚪ Low ({low_score})")

def _display_condensed_cycle_summary(detector, result, cycle_number, total_cycles):
    """Display condensed cycle summary with key metrics only"""
    try:
        # Basic cycle metrics
        total_analyzed = result.get('total_analyzed', 0)
        high_conviction_found = len(result.get('high_conviction_tokens', []))
        alerts_sent = result.get('alerts_sent', 0)
        cycle_time = result.get('cycle_time', 0)
        
        print(f"\n📊 CYCLE #{cycle_number}/{total_cycles} SUMMARY:")
        print(f"🔍 Analyzed: {total_analyzed} | 🎯 High Conviction: {high_conviction_found} | 📱 Alerts: {alerts_sent} | ⏱️ {cycle_time:.1f}s")
        
        # Get high conviction tokens
        high_conviction_tokens = result.get('high_conviction_tokens', [])
        
        # Show top 3 tokens if any found
        if high_conviction_found > 0:
            # Sort by score
            high_conviction_tokens.sort(key=lambda x: x.get('score', 0), reverse=True)
            top_tokens = high_conviction_tokens[:3]
            
            if top_tokens:
                print(f"🏆 Top Tokens:")
                for i, token in enumerate(top_tokens, 1):
                    symbol = token.get('symbol', 'Unknown')
                    score = token.get('score', 0)
                    source = token.get('source', 'unknown')
                    print(f"  {i}. {symbol} - {score:.1f} ({source})")
        
        # API usage summary
        api_usage = detector.session_stats.get('api_usage_by_service', {})
        if api_usage:
            total_calls = sum(stats.get('total_calls', 0) for stats in api_usage.values())
            total_successes = sum(stats.get('successful_calls', 0) for stats in api_usage.values())
            success_rate = (total_successes / max(total_calls, 1)) * 100
            
            print(f"📡 API: {total_calls} calls | {success_rate:.1f}% success")
        
        print("-" * 60)
        
    except Exception as e:
        print(f"⚠️ Error in condensed cycle summary: {e}")

def _display_comprehensive_final_summary(detector, total_cycles, successful_cycles, failed_cycles, total_tokens_found, total_alerts_sent, session_start):
    """Display comprehensive final summary at the end of the 72-hour session"""
    try:
        # Try to import prettytable
        try:
            from prettytable import PrettyTable
            has_prettytable = True
        except ImportError:
            has_prettytable = False
        
        total_time = time.time() - session_start
        
        print("\n" + "="*80)
        print("🎯 FINAL COMPREHENSIVE SESSION ANALYSIS")
        print("="*80)
        
        # Display session summary tables
        _display_session_summary_tables(detector)
        
        # Final session summary with comprehensive API usage
        final_api_stats = {}
        total_final_api_calls = 0
        api_cost_estimate = 0.0
        
        try:
            if hasattr(detector, 'session_stats') and detector.session_stats:
                api_usage = detector.session_stats.get('api_usage_by_service', {})
                
                # Extract detailed stats for each platform
                for platform in api_usage:
                    platform_data = api_usage.get(platform, {})
                    final_api_stats[platform] = {
                        'calls': platform_data.get('total_calls', 0),
                        'successes': platform_data.get('successful_calls', 0),
                        'failures': platform_data.get('failed_calls', 0),
                        'cost': platform_data.get('estimated_cost_usd', 0.0)
                    }
                    total_final_api_calls += final_api_stats[platform]['calls']
                    api_cost_estimate += final_api_stats[platform]['cost']
        except Exception:
            pass
        
        print(f"\n🎉 72-HOUR SESSION COMPLETED")
        print("=" * 80)
        print(f"⏰ Total duration: {total_time/3600:.1f} hours")
        print(f"🔄 Cycles completed: {successful_cycles + failed_cycles}")
        print(f"✅ Successful cycles: {successful_cycles}")
        print(f"❌ Failed cycles: {failed_cycles}")
        print(f"📈 Success rate: {(successful_cycles/(successful_cycles+failed_cycles)*100):.1f}%" if (successful_cycles + failed_cycles) > 0 else "N/A")
        print(f"🎯 Total high conviction tokens: {total_tokens_found}")
        print(f"📱 Total alerts sent: {total_alerts_sent}")
        print("")
        print("📊 API USAGE SUMMARY:")
        print(f"  🔗 Total API calls: {total_final_api_calls}")
        print(f"  💰 Estimated cost: ${api_cost_estimate:.4f}")
        print(f"  📈 Calls per hour: {(total_final_api_calls / max(0.1, total_time/3600)):.1f}")
        print("")
        print("🔍 BY PLATFORM:")
        for platform, stats in final_api_stats.items():
            platform_name = platform.title()
            success_rate = (stats['successes'] / max(1, stats['calls'])) * 100 if stats['calls'] > 0 else 0
            print(f"  • {platform_name}: {stats['calls']} calls ({success_rate:.1f}% success) - ${stats['cost']:.4f}")
        print("")
        
        print(f"🏁 Ended at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print("=" * 80)
    
    except Exception as e:
        print(f"⚠️ Error in comprehensive final summary: {e}")

async def run_72hour_detector():
    """Run detector for 72 hours with hourly intervals"""
    
    # Configuration
    TOTAL_DURATION_HOURS = 72
    INTERVAL_MINUTES = 60
    TOTAL_CYCLES = TOTAL_DURATION_HOURS  # 1 scan per hour
    
    # Progress tracking function
    def print_progress_bar(progress, total, prefix='', suffix='', length=50, fill='█'):
        """Print progress bar to console"""
        percent = ("{0:.1f}").format(100 * (progress / float(total)))
        filled_length = int(length * progress // total)
        bar = fill * filled_length + '-' * (length - filled_length)
        print(f'\r{prefix} |{bar}| {percent}% {suffix}', end='\r')
        if progress == total: 
            print()
    
    print("🚀 EARLY GEM DETECTOR - 72 HOUR SESSION")
    print("=" * 60)
    print(f"⏰ Duration: {TOTAL_DURATION_HOURS} hours")
    print(f"🔄 Interval: {INTERVAL_MINUTES} minutes")
    print(f"📊 Total cycles: {TOTAL_CYCLES}")
    print(f"🚀 Starting at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"📁 Working directory: {os.getcwd()}")
    print(f"🐍 Python path: {sys.executable}")
    print("=" * 60)
    
    # Parse command line arguments
    import argparse
    parser = argparse.ArgumentParser(description='72-Hour Early Gem Detector')
    parser.add_argument('--debug', action='store_true', help='Enable debug mode')
    args = parser.parse_args()
    
    debug_mode = args.debug
    if debug_mode:
        print("🐛 Debug mode enabled")
    
    # Check environment variables
    print("\n🔍 ENVIRONMENT CHECK:")
    env_vars = ['BIRDEYE_API_KEY', 'MORALIS_API_KEY', 'TELEGRAM_BOT_TOKEN', 'TELEGRAM_CHAT_ID']
    for var in env_vars:
        value = os.getenv(var)
        if value:
            print(f"   ✅ {var}: {'*' * 8}...{value[-4:] if len(value) > 4 else '****'}")
        else:
            print(f"   ❌ {var}: Not set")
    print()
    
    # Import detector
    try:
        from scripts.early_gem_detector import EarlyGemDetector
        print("✅ Detector imported successfully")
    except Exception as e:
        print(f"❌ Import failed: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    # Initialize detector
    try:
        print("🔧 Initializing detector...")
        detector = EarlyGemDetector(debug_mode=debug_mode)
        print("✅ Detector initialized")
        
        # Test basic functionality
        print("🧪 Testing detector basic functionality...")
        if hasattr(detector, 'session_stats'):
            print(f"   ✅ Session stats initialized: {detector.session_stats}")
        else:
            print("   ⚠️ Session stats not found")
            
        if hasattr(detector, 'run_detection_cycle'):
            print("   ✅ run_detection_cycle method available")
        else:
            print("   ❌ run_detection_cycle method missing")
            
        if hasattr(detector, 'logger'):
            print("   ✅ Logger initialized")
        else:
            print("   ⚠️ Logger not found")
        
        # Monkey patch the run_detection_cycle method to show progress
        original_run_detection_cycle = detector.run_detection_cycle
        
        async def patched_run_detection_cycle():
            """Patched version of run_detection_cycle that shows progress"""
            print("\n🔄 Starting detection cycle...")
            print("📡 Step 1: Multi-platform token discovery")
            
            # Call the original method
            result = await original_run_detection_cycle()
            
            return result
            
        # Apply the patch
        detector.run_detection_cycle = patched_run_detection_cycle
        
        # Also patch the discover_early_tokens method to show progress
        original_discover_early_tokens = detector.discover_early_tokens
        
        async def patched_discover_early_tokens():
            """Patched version of discover_early_tokens that shows progress"""
            print("\n🔍 Discovering tokens from all sources...")
            
            # Call the original method
            candidates = await original_discover_early_tokens()
            
            print(f"✅ Found {len(candidates)} token candidates")
            return candidates
            
        # Apply the patch
        detector.discover_early_tokens = patched_discover_early_tokens
        
        # Patch the analyze_early_candidates method to show progress
        original_analyze_early_candidates = detector.analyze_early_candidates
        
        async def patched_analyze_early_candidates(candidates):
            """Patched version of analyze_early_candidates that shows progress"""
            print(f"\n🔬 Analyzing {len(candidates)} token candidates...")
            
            # Call the original method
            results = await original_analyze_early_candidates(candidates)
            
            print(f"✅ Analysis complete - {len(results)} tokens processed")
            return results
            
        # Apply the patch
        detector.analyze_early_candidates = patched_analyze_early_candidates
        
        # Fix logging duplication: Disable console handler for EarlyGemDetector
        detector_logger = logging.getLogger('EarlyGemDetector')
        console_handlers_to_remove = []
        for handler in detector_logger.handlers:
            if isinstance(handler, logging.StreamHandler) and not hasattr(handler, 'baseFilename'):
                console_handlers_to_remove.append(handler)
        
        for handler in console_handlers_to_remove:
            detector_logger.removeHandler(handler)
            print("🔧 Console handler removed from EarlyGemDetector to prevent duplication")
            print("📝 All detector logs will still be saved to file, but console output comes directly from detector")
                
    except Exception as e:
        print(f"❌ Detector initialization failed: {e}")
        print(f"🔍 Exception type: {type(e)}")
        import traceback
        print(f"📋 Full traceback:")
        traceback.print_exc()
        return False
    
    # Session tracking
    session_start = time.time()
    session_end = session_start + (TOTAL_DURATION_HOURS * 3600)
    successful_cycles = 0
    failed_cycles = 0
    total_tokens_found = 0
    total_alerts_sent = 0
    
    try:
        cycle_number = 1
        
        while time.time() < session_end and cycle_number <= TOTAL_CYCLES:
            cycle_start = time.time()
            
            print(f"\n🔍 SCAN CYCLE #{cycle_number}/{TOTAL_CYCLES}")
            print(f"⏰ Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
            print("-" * 40)
            
            try:
                print(f"\n{'='*40}")
                print(f"🔍 RUNNING DETECTION CYCLE #{cycle_number}/{TOTAL_CYCLES}")
                print(f"{'='*40}")
                
                # Run detection cycle with detailed error tracking
                result = None
                detection_start = time.time()
                
                try:
                    print(f"🔄 Calling detector.run_detection_cycle()...")
                    result = await detector.run_detection_cycle()
                    detection_time = time.time() - detection_start
                    print(f"🔍 Detection cycle returned after {detection_time:.2f}s: {type(result)}")
                    
                    if result:
                        print(f"📋 Result keys: {list(result.keys()) if isinstance(result, dict) else 'Not a dict'}")
                        if isinstance(result, dict):
                            error_field = result.get('error', 'No error field')
                            print(f"🔍 Error in result: {error_field}")
                            print(f"📊 Total analyzed: {result.get('total_analyzed', 'Missing')}")
                            print(f"🎯 High conviction tokens: {len(result.get('high_conviction_tokens', []))}")
                            print(f"⏱️ Cycle time: {result.get('cycle_time', 'Missing')}")
                            
                            # Check if there's an actual error
                            if error_field and error_field != 'No error field' and error_field is not None:
                                print(f"⚠️ Detected error in result: {error_field}")
                    else:
                        print("⚠️ Result is None or empty")
                        
                except Exception as detection_error:
                    detection_time = time.time() - detection_start
                    print(f"❌ Detection cycle threw exception after {detection_time:.2f}s: {detection_error}")
                    print(f"🔍 Exception type: {type(detection_error)}")
                    print(f"🔍 Exception args: {detection_error.args}")
                    import traceback
                    print(f"📋 Full traceback:")
                    traceback.print_exc()
                    result = {'error': str(detection_error), 'cycle_time': detection_time, 'total_analyzed': 0, 'high_conviction_tokens': [], 'alerts_sent': 0}
                
                # Track results with detailed validation  
                # Check if result is successful (no error or error is None)
                has_error = result and isinstance(result, dict) and result.get('error') is not None
                if result and isinstance(result, dict) and not has_error:
                    successful_cycles += 1
                    high_conviction_count = len(result.get('high_conviction_tokens', []))
                    total_tokens_found += high_conviction_count
                    alerts_sent = result.get('alerts_sent', 0)
                    total_alerts_sent += alerts_sent
                    
                    print(f"\n✅ Cycle {cycle_number} completed successfully")
                    print(f"{'='*40}")
                    print(f"📊 CYCLE #{cycle_number} RESULTS:")
                    print(f"🔍 Tokens analyzed: {result.get('total_analyzed', 0)}")
                    print(f"🎯 High conviction tokens: {high_conviction_count}")
                    print(f"📱 Alerts sent: {alerts_sent}")
                    print(f"⏱️ Cycle duration: {result.get('cycle_time', 0):.2f}s")
                    print(f"{'='*40}")
                    
                    # Display condensed summary for most cycles
                    if cycle_number == TOTAL_CYCLES:
                        # Detailed summary for final cycle
                        _display_detailed_scan_summary(detector, result, cycle_number, TOTAL_CYCLES)
                        _display_scoring_analysis(detector, result, cycle_number)
                    else:
                        # Condensed summary for regular cycles
                        _display_condensed_cycle_summary(detector, result, cycle_number, TOTAL_CYCLES)
                else:
                    failed_cycles += 1
                    print(f"\n⚠️ Cycle {cycle_number} completed with issues")
                    print(f"🔍 Debug info:")
                    print(f"  • Result type: {type(result)}")
                    print(f"  • Result is None: {result is None}")
                    print(f"  • Result is dict: {isinstance(result, dict)}")
                    if isinstance(result, dict):
                        error_value = result.get('error', 'No error field')
                        print(f"  • Has error field: {'error' in result}")
                        print(f"  • Error value: {error_value}")
                        print(f"  • Error is None: {error_value is None}")
                        print(f"  • Has actual error: {error_value is not None}")
                        print(f"  • All keys: {list(result.keys())}")
                    
                    # Try to get some useful info even from failed cycles
                    if result and isinstance(result, dict):
                        cycle_time = result.get('cycle_time', 0)
                        total_analyzed = result.get('total_analyzed', 0)
                        print(f"  • Partial results: {total_analyzed} tokens analyzed in {cycle_time:.2f}s")
                        
                        # If error is None, this might actually be a successful cycle
                        if result.get('error') is None:
                            print(f"  🤔 ERROR IS NULL - This might actually be a successful cycle!")
                            print(f"  📊 High conviction tokens found: {len(result.get('high_conviction_tokens', []))}")
                            print(f"  📱 Alerts sent: {result.get('alerts_sent', 0)}")
                
            except Exception as e:
                failed_cycles += 1
                print(f"\n❌ Cycle {cycle_number} failed with exception: {e}")
                print(f"🔍 Exception type: {type(e)}")
                import traceback
                print(f"📋 Full traceback:")
                traceback.print_exc()
            
            # Calculate next cycle time
            cycle_duration = time.time() - cycle_start
            next_cycle_time = cycle_start + (INTERVAL_MINUTES * 60)
            time_until_next = next_cycle_time - time.time()
            
            # Progress summary
            elapsed_hours = (time.time() - session_start) / 3600
            remaining_hours = (session_end - time.time()) / 3600
            
            # Get API usage stats from detector
            api_stats = {}
            try:
                if hasattr(detector, 'session_stats') and detector.session_stats:
                    api_usage = detector.session_stats.get('api_usage_by_service', {})
                    for platform, stats in api_usage.items():
                        api_stats[platform] = stats.get('total_calls', 0)
                    total_api_calls = sum(api_stats.values())
                else:
                    total_api_calls = 0
            except Exception:
                total_api_calls = 0
                api_stats = {}

            print(f"\n📈 SESSION PROGRESS:")
            print(f"  ✅ Successful cycles: {successful_cycles}")
            print(f"  ❌ Failed cycles: {failed_cycles}")
            print(f"  🎯 Total tokens found: {total_tokens_found}")
            print(f"  📱 Total alerts sent: {total_alerts_sent}")
            print(f"  ⏰ Elapsed: {elapsed_hours:.1f}h | Remaining: {remaining_hours:.1f}h")
            print(f"  📊 API Calls: {total_api_calls} total")
            
            # Wait for next cycle (if not the last one)
            if cycle_number < TOTAL_CYCLES and time.time() < session_end:
                if time_until_next > 0:
                    next_scan_time = datetime.fromtimestamp(next_cycle_time)
                    print(f"\n⏸️ Next scan at: {next_scan_time.strftime('%H:%M:%S')}")
                    print(f"💤 Waiting {time_until_next/60:.1f} minutes...")
                    
                    # Sleep in chunks to allow for interruption and show progress
                    total_wait_time = time_until_next
                    elapsed_wait = 0
                    
                    print(f"\n⏳ Waiting for next cycle...")
                    
                    while time_until_next > 0 and time.time() < session_end:
                        sleep_time = min(10, time_until_next)  # Sleep 10 seconds at a time for progress updates
                        await asyncio.sleep(sleep_time)
                        elapsed_wait += sleep_time
                        time_until_next = next_cycle_time - time.time()
                        
                        # Show progress bar
                        mins_left = time_until_next / 60
                        print_progress_bar(
                            elapsed_wait, 
                            total_wait_time,
                            prefix=f"⏳ Next cycle in {mins_left:.1f} mins",
                            suffix=f"Cycle #{cycle_number+1} at {next_scan_time.strftime('%H:%M:%S')}",
                            length=40
                        )
            
            cycle_number += 1
    
    except KeyboardInterrupt:
        print(f"\n⚠️ Session interrupted by user")
    except Exception as e:
        print(f"\n❌ Session error: {e}")
        import traceback
        traceback.print_exc()
    
    finally:
        # Final cleanup and summary
        try:
            await detector.cleanup()
            print("\n✅ Detector cleanup completed")
        except Exception as e:
            print(f"\n⚠️ Cleanup error: {e}")
        
        # Display comprehensive final summary
        _display_comprehensive_final_summary(detector, TOTAL_CYCLES, successful_cycles, failed_cycles, total_tokens_found, total_alerts_sent, session_start)
    
    return successful_cycles > 0

if __name__ == '__main__':
    try:
        success = asyncio.run(run_72hour_detector())
        if success:
            print("\n🎉 72-hour session completed successfully!")
        else:
            print("\n💥 72-hour session failed!")
            sys.exit(1)
    except KeyboardInterrupt:
        print("\n⚠️ Session interrupted by user")
        sys.exit(0)
    except Exception as e:
        print(f"\n❌ Unexpected error: {e}")
        sys.exit(1)
 