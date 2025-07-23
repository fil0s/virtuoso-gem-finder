#!/usr/bin/env python3
"""
🎯 Focused Raydium API Test
Quick test to verify essential findings and identify the best working endpoint
"""

import asyncio
import aiohttp
import json
import time
import logging

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class FocusedRaydiumTester:
    def __init__(self):
        self.SOL_MINT = 'So11111111111111111111111111111111111111112'
        
    async def quick_test_endpoint(self, name: str, url: str, sample_size: int = 100) -> dict:
        """Quick test - only sample first records to identify structure"""
        logger.info(f"🔍 Testing {name}...")
        
        start_time = time.time()
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(url, timeout=aiohttp.ClientTimeout(total=15)) as response:
                    if response.status == 200:
                        # Stream and parse only beginning of response
                        text_data = ""
                        bytes_read = 0
                        max_bytes = 50 * 1024 * 1024  # 50MB max
                        
                        async for chunk in response.content.iter_chunked(8192):
                            text_data += chunk.decode('utf-8', errors='ignore')
                            bytes_read += len(chunk)
                            
                            # Try to parse partial JSON to get structure info
                            if bytes_read > 1024 * 1024:  # After 1MB, try parsing
                                try:
                                    # Try to parse what we have so far
                                    if text_data.strip().startswith('['):
                                        # It's an array, try to get first few items
                                        bracket_count = 0
                                        items_found = 0
                                        pos = 0
                                        
                                        for i, char in enumerate(text_data):
                                            if char == '{':
                                                bracket_count += 1
                                            elif char == '}':
                                                bracket_count -= 1
                                                if bracket_count == 0 and items_found < sample_size:
                                                    items_found += 1
                                                    pos = i
                                            
                                            if items_found >= sample_size:
                                                # Extract sample data
                                                sample_json = text_data[:pos+1] + ']'
                                                try:
                                                    sample_data = json.loads(sample_json)
                                                    total_time = time.time() - start_time
                                                    
                                                    # Analyze the sample
                                                    sol_pairs = self._find_sol_pairs_in_sample(sample_data)
                                                    
                                                    return {
                                                        'name': name,
                                                        'status': 'success',
                                                        'url': url,
                                                        'sample_size': len(sample_data),
                                                        'total_time': total_time,
                                                        'sol_pairs_found': len(sol_pairs),
                                                        'sol_pair_examples': sol_pairs[:3],
                                                        'sample_structure': self._analyze_structure(sample_data[:3]) if sample_data else {},
                                                        'estimated_total_records': '698K+' if 'pairs' in name.lower() else 'unknown'
                                                    }
                                                except:
                                                    continue
                                        break
                                except:
                                    if bytes_read > max_bytes:
                                        break
                                    continue
                            
                            if bytes_read > max_bytes:
                                logger.warning(f"   ⚠️ {name}: Stopped after {max_bytes//1024//1024}MB")
                                break
                        
                        # If we get here, try parsing the full data we have
                        try:
                            data = json.loads(text_data)
                            total_time = time.time() - start_time
                            
                            if isinstance(data, list):
                                sample_data = data[:sample_size]
                            else:
                                sample_data = data
                            
                            sol_pairs = self._find_sol_pairs_in_sample(sample_data if isinstance(sample_data, list) else [sample_data])
                            
                            return {
                                'name': name,
                                'status': 'success',
                                'url': url,
                                'sample_size': len(sample_data) if isinstance(sample_data, list) else 1,
                                'total_time': total_time,
                                'sol_pairs_found': len(sol_pairs),
                                'sol_pair_examples': sol_pairs[:3],
                                'sample_structure': self._analyze_structure(sample_data[:3] if isinstance(sample_data, list) else [sample_data]),
                                'data_size_mb': len(text_data) / 1024 / 1024
                            }
                        except json.JSONDecodeError:
                            return {
                                'name': name,
                                'status': 'json_error',
                                'url': url,
                                'error': 'Could not parse JSON',
                                'total_time': time.time() - start_time
                            }
                    else:
                        return {
                            'name': name,
                            'status': 'http_error',
                            'url': url,
                            'status_code': response.status,
                            'total_time': time.time() - start_time
                        }
                        
        except asyncio.TimeoutError:
            return {
                'name': name,
                'status': 'timeout',
                'url': url,
                'total_time': 15,
                'error': 'Timeout after 15s'
            }
        except Exception as e:
            return {
                'name': name,
                'status': 'error',
                'url': url,
                'error': str(e),
                'total_time': time.time() - start_time
            }

    def _find_sol_pairs_in_sample(self, sample_data: list) -> list:
        """Find SOL pairs in sample data"""
        sol_pairs = []
        
        for item in sample_data[:100]:  # Check first 100 items
            if not isinstance(item, dict):
                continue
                
            # Multiple field patterns to check
            fields_to_check = [
                ('baseMint', 'quoteMint'),
                ('base_mint', 'quote_mint'),
                ('baseToken.mint', 'quoteToken.mint'),
                ('baseToken.address', 'quoteToken.address'),
                ('token0.address', 'token1.address'),
            ]
            
            for base_field, quote_field in fields_to_check:
                base_value = self._get_nested_field(item, base_field)
                quote_value = self._get_nested_field(item, quote_field)
                
                if base_value == self.SOL_MINT or quote_value == self.SOL_MINT:
                    sol_pairs.append({
                        'base_mint': base_value,
                        'quote_mint': quote_value,
                        'matched_pattern': f"{base_field}/{quote_field}",
                        'pool_id': item.get('id', item.get('ammId', 'unknown'))
                    })
                    break
        
        return sol_pairs

    def _get_nested_field(self, data: dict, field_path: str):
        """Get nested field value like 'baseToken.mint'"""
        try:
            value = data
            for key in field_path.split('.'):
                if isinstance(value, dict) and key in value:
                    value = value[key]
                else:
                    return None
            return value
        except:
            return None

    def _analyze_structure(self, sample_items: list) -> dict:
        """Analyze structure of sample items"""
        if not sample_items:
            return {}
        
        first_item = sample_items[0]
        if not isinstance(first_item, dict):
            return {'type': type(first_item).__name__}
        
        return {
            'keys': list(first_item.keys())[:10],
            'nested_keys': {
                k: list(v.keys())[:5] if isinstance(v, dict) else type(v).__name__ 
                for k, v in first_item.items() 
                if k in ['baseToken', 'quoteToken', 'token0', 'token1']
            }
        }

async def main():
    """Quick focused test"""
    tester = FocusedRaydiumTester()
    
    # Test key endpoints with focus on finding working SOL pair detection
    endpoints = {
        'raydium_pairs_v2': 'https://api.raydium.io/v2/main/pairs',  # This showed 10 SOL pairs
        'raydium_pools': 'https://api.raydium.io/pools',  # This showed 0 SOL pairs
        'raydium_pairs_alt': 'https://api.raydium.io/pairs',  # This showed 0 SOL pairs
        'jupiter_pairs': 'https://stats.jup.ag/pools/pairs',  # Alternative source
        'orca_pools': 'https://api.orca.so/v1/pools',  # Alternative source
    }
    
    logger.info("🎯 Focused Raydium API Test - Finding Best SOL Pair Source")
    logger.info("=" * 60)
    
    results = []
    for name, url in endpoints.items():
        result = await tester.quick_test_endpoint(name, url, sample_size=50)
        results.append(result)
        
        # Log result immediately
        if result['status'] == 'success':
            sol_count = result.get('sol_pairs_found', 0)
            time_taken = result.get('total_time', 0)
            sample_size = result.get('sample_size', 0)
            
            logger.info(f"✅ {name}: {sol_count} SOL pairs found in {sample_size} samples ({time_taken:.1f}s)")
            
            # Show structure info
            structure = result.get('sample_structure', {})
            if 'keys' in structure:
                logger.info(f"   🔑 Keys: {structure['keys'][:5]}")
            if 'nested_keys' in structure and structure['nested_keys']:
                logger.info(f"   🏗️ Nested: {structure['nested_keys']}")
            
            # Show SOL pair examples
            examples = result.get('sol_pair_examples', [])
            if examples:
                logger.info(f"   🌊 Pattern: {examples[0]['matched_pattern']}")
        else:
            error = result.get('error', result['status'])
            logger.error(f"❌ {name}: {error}")
        
        await asyncio.sleep(1)  # Be respectful
    
    # Summary and recommendations
    logger.info("\n" + "=" * 60)
    logger.info("📊 SUMMARY & RECOMMENDATIONS")
    logger.info("=" * 60)
    
    working_results = [r for r in results if r['status'] == 'success']
    sol_pair_results = [r for r in working_results if r.get('sol_pairs_found', 0) > 0]
    
    if sol_pair_results:
        # Sort by SOL pairs found
        sol_pair_results.sort(key=lambda x: x['sol_pairs_found'], reverse=True)
        best_result = sol_pair_results[0]
        
        logger.info(f"🏆 BEST ENDPOINT FOR SOL PAIRS:")
        logger.info(f"   Name: {best_result['name']}")
        logger.info(f"   URL: {best_result['url']}")
        logger.info(f"   SOL pairs: {best_result['sol_pairs_found']} found")
        logger.info(f"   Performance: {best_result['total_time']:.1f}s")
        
        # Show the correct field pattern
        if best_result.get('sol_pair_examples'):
            pattern = best_result['sol_pair_examples'][0]['matched_pattern']
            logger.info(f"   🔧 Field pattern to use: {pattern}")
        
        logger.info(f"\n💡 RECOMMENDATION:")
        logger.info(f"   Switch to: {best_result['url']}")
        logger.info(f"   Expected performance: {best_result['total_time']:.1f}s for sample data")
        
        return best_result
    else:
        logger.error("❌ CRITICAL: No endpoints found SOL pairs!")
        logger.info("🔧 Need to investigate field patterns further")
        return None

if __name__ == "__main__":
    result = asyncio.run(main())
    if result:
        print(f"\n✅ Found working endpoint: {result['name']}")
        print(f"🌊 SOL pairs detected: {result['sol_pairs_found']}")
    else:
        print("\n❌ No working endpoints found")