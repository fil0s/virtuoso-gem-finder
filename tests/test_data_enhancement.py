#!/usr/bin/env python3
"""
🔍 DATA ENHANCEMENT TEST SCRIPT
Test both DexScreener and Birdeye APIs to determine optimal data enhancement strategy.

Test Token: FpYGrMsEbyKbpTxwknvVt6rbiftydvsnsuY2LsNhpump
Strategy: DexScreener first (free, comprehensive) → Birdeye second (enhanced data)
"""

import asyncio
import aiohttp
import json
import os
from typing import Dict, Any, Optional
import time
from datetime import datetime

class DataEnhancementTester:
    def __init__(self):
        self.test_token = "FpYGrMsEbyKbpTxwknvVt6rbiftydvsnsuY2LsNhpump"
        self.birdeye_api_key = os.getenv('BIRDEYE_API_KEY')
        
        # Data fields needed for early_gem_detector.py analysis
        self.required_fields = {
            'basic_info': [
                'address', 'symbol', 'name', 'price_usd', 'market_cap', 'liquidity_usd'
            ],
            'volume_data': [
                'volume_24h', 'volume_6h', 'volume_1h', 'volume_5m', 'volume_30m'
            ],
            'trading_activity': [
                'trades_24h', 'trades_6h', 'trades_1h', 'trades_5m', 
                'buys_24h', 'sells_24h', 'unique_traders_24h'
            ],
            'price_changes': [
                'price_change_24h', 'price_change_6h', 'price_change_1h', 
                'price_change_30m', 'price_change_5m'
            ],
            'holder_data': [
                'holder_count', 'top_holder_percentage', 'concentration_score'
            ],
            'creation_info': [
                'creation_time', 'age_hours', 'first_trade_time'
            ],
            'liquidity_info': [
                'liquidity_usd', 'dex_info', 'pool_address', 'fdv'
            ],
            'social_security': [
                'is_scam', 'is_risky', 'security_score', 'social_links'
            ]
        }
        
    async def test_dexscreener_data(self) -> Dict[str, Any]:
        """Test DexScreener API for comprehensive trading data"""
        print("🔍 TESTING DEXSCREENER API")
        print("=" * 50)
        
        url = f'https://api.dexscreener.com/latest/dex/tokens/{self.test_token}'
        
        try:
            async with aiohttp.ClientSession() as session:
                start_time = time.time()
                async with session.get(url) as response:
                    response_time = time.time() - start_time
                    
                    print(f"📡 Status: {response.status}")
                    print(f"⏱️  Response Time: {response_time:.2f}s")
                    
                    if response.status == 200:
                        data = await response.json()
                        return await self._analyze_dexscreener_response(data)
                    else:
                        text = await response.text()
                        print(f"❌ Error: {text[:200]}")
                        return {'error': f"HTTP {response.status}", 'data': {}}
                        
        except Exception as e:
            print(f"❌ Exception: {e}")
            return {'error': str(e), 'data': {}}
    
    async def _analyze_dexscreener_response(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze DexScreener response and extract relevant data"""
        result = {
            'available_data': {},
            'missing_data': [],
            'data_quality': 'unknown',
            'coverage_score': 0
        }
        
        if not data.get('pairs'):
            print("❌ No pairs found for token")
            result['data_quality'] = 'no_data'
            return result
            
        # Get the most liquid pair
        pair = max(data['pairs'], key=lambda x: x.get('liquidity', {}).get('usd', 0))
        
        print(f"✅ Found {len(data['pairs'])} pair(s)")
        print(f"📊 Using pair: {pair.get('dexId', 'Unknown')} - {pair.get('baseToken', {}).get('symbol', '?')}/{pair.get('quoteToken', {}).get('symbol', '?')}")
        
        # Extract available data
        extracted_data = {}
        available_fields = []
        
        # Basic info
        if pair.get('baseToken', {}).get('address') == self.test_token:
            token_info = pair.get('baseToken', {})
        else:
            token_info = pair.get('quoteToken', {})
            
        if token_info:
            extracted_data.update({
                'address': token_info.get('address'),
                'symbol': token_info.get('symbol'),
                'name': token_info.get('name'),
                'price_usd': float(pair.get('priceUsd', 0)),
                'market_cap': pair.get('marketCap', 0),
                'fdv': pair.get('fdv', 0)
            })
            available_fields.extend(['address', 'symbol', 'name', 'price_usd', 'market_cap', 'fdv'])
        
        # Liquidity data
        liquidity = pair.get('liquidity', {})
        if liquidity:
            extracted_data.update({
                'liquidity_usd': liquidity.get('usd', 0),
                'liquidity_base': liquidity.get('base', 0),
                'liquidity_quote': liquidity.get('quote', 0)
            })
            available_fields.extend(['liquidity_usd', 'liquidity_base', 'liquidity_quote'])
        
        # Volume data
        volume = pair.get('volume', {})
        if volume:
            extracted_data.update({
                'volume_24h': volume.get('h24', 0),
                'volume_6h': volume.get('h6', 0),
                'volume_1h': volume.get('h1', 0),
                'volume_5m': volume.get('m5', 0)
            })
            available_fields.extend(['volume_24h', 'volume_6h', 'volume_1h', 'volume_5m'])
        
        # Transaction data
        txns = pair.get('txns', {})
        if txns:
            # 24h transactions
            h24 = txns.get('h24', {})
            extracted_data.update({
                'trades_24h': h24.get('buys', 0) + h24.get('sells', 0),
                'buys_24h': h24.get('buys', 0),
                'sells_24h': h24.get('sells', 0)
            })
            
            # 1h transactions
            h1 = txns.get('h1', {})
            extracted_data.update({
                'trades_1h': h1.get('buys', 0) + h1.get('sells', 0),
                'buys_1h': h1.get('buys', 0),
                'sells_1h': h1.get('sells', 0)
            })
            
            # 5m transactions
            m5 = txns.get('m5', {})
            extracted_data.update({
                'trades_5m': m5.get('buys', 0) + m5.get('sells', 0),
                'buys_5m': m5.get('buys', 0),
                'sells_5m': m5.get('sells', 0)
            })
            
            available_fields.extend(['trades_24h', 'trades_1h', 'trades_5m', 'buys_24h', 'sells_24h'])
        
        # Price change data
        price_change = pair.get('priceChange', {})
        if price_change:
            extracted_data.update({
                'price_change_24h': price_change.get('h24', 0),
                'price_change_6h': price_change.get('h6', 0),
                'price_change_1h': price_change.get('h1', 0),
                'price_change_5m': price_change.get('m5', 0)
            })
            available_fields.extend(['price_change_24h', 'price_change_6h', 'price_change_1h', 'price_change_5m'])
        
        # DEX and pair info
        extracted_data.update({
            'dex_id': pair.get('dexId'),
            'pair_address': pair.get('pairAddress'),
            'pair_created_at': pair.get('pairCreatedAt'),
            'chain_id': pair.get('chainId')
        })
        available_fields.extend(['dex_id', 'pair_address', 'chain_id'])
        
        # Calculate estimated unique traders (approximation)
        if extracted_data.get('trades_24h', 0) > 0:
            extracted_data['unique_traders_estimate'] = max(1, extracted_data['trades_24h'] // 2.5)
            available_fields.append('unique_traders_estimate')
        
        result['available_data'] = extracted_data
        result['available_fields'] = available_fields
        
        # Display findings
        print(f"\n📋 DEXSCREENER DATA ANALYSIS:")
        print(f"   💰 Price: ${extracted_data.get('price_usd', 0):.8f}")
        print(f"   🏦 Market Cap: ${extracted_data.get('market_cap', 0):,.0f}")
        print(f"   💧 Liquidity: ${extracted_data.get('liquidity_usd', 0):,.0f}")
        print(f"   📈 Volume 24h: ${extracted_data.get('volume_24h', 0):,.0f}")
        print(f"   🔄 Trades 24h: {extracted_data.get('trades_24h', 0)}")
        print(f"   📊 Price Change 24h: {extracted_data.get('price_change_24h', 0):.2f}%")
        print(f"   🏪 DEX: {extracted_data.get('dex_id', 'Unknown')}")
        
        # Check what's missing for early_gem_detector.py
        all_required = []
        for category, fields in self.required_fields.items():
            all_required.extend(fields)
        
        missing_fields = [field for field in all_required if field not in available_fields]
        result['missing_data'] = missing_fields
        
        coverage = len(available_fields) / len(all_required) * 100
        result['coverage_score'] = coverage
        
        print(f"\n📊 COVERAGE ANALYSIS:")
        print(f"   ✅ Available: {len(available_fields)} fields")
        print(f"   ❌ Missing: {len(missing_fields)} fields")
        print(f"   📈 Coverage: {coverage:.1f}%")
        
        if missing_fields:
            print(f"\n⚠️  Missing Critical Fields:")
            for field in missing_fields[:10]:  # Show first 10
                print(f"      - {field}")
            if len(missing_fields) > 10:
                print(f"      ... and {len(missing_fields) - 10} more")
        
        return result
    
    async def test_birdeye_data(self) -> Dict[str, Any]:
        """Test Birdeye API for enhanced data"""
        print("\n\n🔍 TESTING BIRDEYE API")
        print("=" * 50)
        
        if not self.birdeye_api_key:
            print("❌ No Birdeye API key found")
            return {'error': 'No API key', 'data': {}}
        
        headers = {'X-API-KEY': self.birdeye_api_key}
        base_url = 'https://public-api.birdeye.so'
        
        birdeye_data = {}
        
        # Test multiple Birdeye endpoints
        endpoints = [
            ('token_overview', '/defi/token_overview', {'address': self.test_token}),
            ('token_holders', '/defi/v3/token/holder', {'address': self.test_token, 'limit': 10}),
            ('token_security', '/defi/token_security', {'address': self.test_token}),
            ('token_creation', '/defi/token_creation_info', {'address': self.test_token}),
            ('trade_data', '/defi/v3/token/trade-data/single', {'address': self.test_token})
        ]
        
        async with aiohttp.ClientSession() as session:
            for endpoint_name, endpoint_path, params in endpoints:
                try:
                    start_time = time.time()
                    url = f"{base_url}{endpoint_path}"
                    
                    async with session.get(url, params=params, headers=headers) as response:
                        response_time = time.time() - start_time
                        
                        print(f"\n📡 {endpoint_name.upper()}: {response.status} ({response_time:.2f}s)")
                        
                        if response.status == 200:
                            data = await response.json()
                            if data.get('success') and data.get('data'):
                                birdeye_data[endpoint_name] = data['data']
                                print(f"   ✅ Data received")
                            else:
                                print(f"   ⚠️  Success=False or no data")
                                birdeye_data[endpoint_name] = None
                        else:
                            text = await response.text()
                            print(f"   ❌ Error: {text[:100]}")
                            birdeye_data[endpoint_name] = None
                            
                except Exception as e:
                    print(f"   ❌ Exception: {e}")
                    birdeye_data[endpoint_name] = None
                
                # Rate limiting
                await asyncio.sleep(0.2)
        
        return await self._analyze_birdeye_response(birdeye_data)
    
    async def _analyze_birdeye_response(self, birdeye_data: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze Birdeye response and extract enhanced data"""
        result = {
            'available_data': {},
            'enhanced_fields': [],
            'unique_to_birdeye': [],
            'data_quality': 'partial'
        }
        
        extracted_data = {}
        enhanced_fields = []
        
        # Token Overview
        if birdeye_data.get('token_overview'):
            overview = birdeye_data['token_overview']
            extracted_data.update({
                'birdeye_price': overview.get('price', 0),
                'birdeye_market_cap': overview.get('marketCap', 0),
                'birdeye_liquidity': overview.get('liquidity', 0),
                'supply_total': overview.get('supply', 0),
                'birdeye_volume_24h': overview.get('volume', {}).get('h24', 0),
                'trade_count_24h': overview.get('trade24h', 0)
            })
            enhanced_fields.extend(['supply_total', 'trade_count_24h'])
            
            print(f"\n📋 BIRDEYE OVERVIEW:")
            print(f"   💰 Price: ${overview.get('price', 0):.8f}")
            print(f"   🏦 Market Cap: ${overview.get('marketCap', 0):,.0f}")
            print(f"   💧 Liquidity: ${overview.get('liquidity', 0):,.0f}")
            print(f"   📈 Volume 24h: ${overview.get('volume', {}).get('h24', 0):,.0f}")
        
        # Token Holders
        if birdeye_data.get('token_holders'):
            holders = birdeye_data['token_holders']
            extracted_data.update({
                'total_holders': holders.get('total', 0),
                'holder_items_count': len(holders.get('items', [])),
            })
            
            if holders.get('items'):
                top_holder = holders['items'][0]
                extracted_data['top_holder_percentage'] = top_holder.get('percentage', 0)
                enhanced_fields.append('top_holder_percentage')
            
            enhanced_fields.extend(['total_holders', 'holder_items_count'])
            
            print(f"\n👥 BIRDEYE HOLDERS:")
            print(f"   👥 Total Holders: {holders.get('total', 0)}")
            if holders.get('items'):
                print(f"   🏆 Top Holder: {holders['items'][0].get('percentage', 0):.2f}%")
        
        # Token Security
        if birdeye_data.get('token_security'):
            security = birdeye_data['token_security']
            extracted_data.update({
                'is_scam': security.get('isScam', False),
                'is_risky': security.get('isRisky', False),
                'security_score': security.get('score', 0)
            })
            enhanced_fields.extend(['is_scam', 'is_risky', 'security_score'])
            
            print(f"\n🛡️  BIRDEYE SECURITY:")
            print(f"   🚨 Is Scam: {security.get('isScam', 'Unknown')}")
            print(f"   ⚠️  Is Risky: {security.get('isRisky', 'Unknown')}")
        
        # Creation Info
        if birdeye_data.get('token_creation'):
            creation = birdeye_data['token_creation']
            extracted_data.update({
                'creation_time': creation.get('creationTime'),
                'creation_transaction': creation.get('creationTransaction')
            })
            enhanced_fields.extend(['creation_time', 'creation_transaction'])
            
            print(f"\n🕒 BIRDEYE CREATION:")
            print(f"   📅 Creation Time: {creation.get('creationTime', 'Unknown')}")
        
        # Trade Data (V3)
        if birdeye_data.get('trade_data'):
            trade_data = birdeye_data['trade_data']
            # This endpoint provides very detailed trading metrics
            extracted_data.update({
                'unique_wallets_24h': trade_data.get('unique_wallet_24h', 0),
                'unique_wallets_1h': trade_data.get('unique_wallet_1h', 0),
                'trade_volume_30m': trade_data.get('volume_30m_usd', 0),
                'buy_volume_24h': trade_data.get('volume_buy_24h_usd', 0),
                'sell_volume_24h': trade_data.get('volume_sell_24h_usd', 0)
            })
            enhanced_fields.extend(['unique_wallets_24h', 'unique_wallets_1h', 'buy_volume_24h', 'sell_volume_24h'])
            
            print(f"\n📊 BIRDEYE TRADE DATA:")
            print(f"   👥 Unique Wallets 24h: {trade_data.get('unique_wallet_24h', 0)}")
            print(f"   💰 Buy Volume 24h: ${trade_data.get('volume_buy_24h_usd', 0):,.0f}")
            print(f"   💸 Sell Volume 24h: ${trade_data.get('volume_sell_24h_usd', 0):,.0f}")
        
        result['available_data'] = extracted_data
        result['enhanced_fields'] = enhanced_fields
        
        # Identify fields unique to Birdeye
        unique_fields = [
            'total_holders', 'top_holder_percentage', 'is_scam', 'is_risky', 
            'security_score', 'creation_time', 'unique_wallets_24h', 'unique_wallets_1h',
            'buy_volume_24h', 'sell_volume_24h', 'supply_total'
        ]
        result['unique_to_birdeye'] = [f for f in unique_fields if f in enhanced_fields]
        
        print(f"\n📊 BIRDEYE ENHANCEMENT:")
        print(f"   ✅ Enhanced Fields: {len(enhanced_fields)}")
        print(f"   🎯 Unique to Birdeye: {len(result['unique_to_birdeye'])}")
        print(f"   🔑 Key Enhancements: {', '.join(result['unique_to_birdeye'][:5])}")
        
        return result
    
    async def create_optimal_enhancement_strategy(self, dex_result: Dict, birdeye_result: Dict):
        """Create the optimal data enhancement strategy"""
        print("\n\n🎯 OPTIMAL ENHANCEMENT STRATEGY")
        print("=" * 60)
        
        print("📋 RECOMMENDED APPROACH:")
        print("   1️⃣  PRIMARY: DexScreener API (Free, comprehensive trading data)")
        print("   2️⃣  SECONDARY: Birdeye API (Enhanced data for missing fields)")
        print()
        
        # Coverage analysis
        dex_coverage = dex_result.get('coverage_score', 0)
        print(f"\n📊 DATA COVERAGE ANALYSIS:")
        print(f"   📈 DexScreener Coverage: {dex_coverage:.1f}%")
        print(f"   🎯 Birdeye Enhancement: +{len(birdeye_result.get('unique_to_birdeye', []))} unique fields")
        
        return {
            'primary_source': 'dexscreener',
            'enhancement_source': 'birdeye', 
            'dex_coverage': dex_coverage,
            'birdeye_enhancements': len(birdeye_result.get('unique_to_birdeye', [])),
            'strategy': 'dexscreener_first_birdeye_enhance'
        }

async def main():
    """Run the comprehensive data enhancement test"""
    print("🚀 DATA ENHANCEMENT STRATEGY TEST")
    print("=" * 60)
    print(f"🎯 Test Token: FpYGrMsEbyKbpTxwknvVt6rbiftydvsnsuY2LsNhpump")
    print(f"📅 Test Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()
    
    tester = DataEnhancementTester()
    
    # Test DexScreener first
    dex_result = await tester.test_dexscreener_data()
    
    # Test Birdeye second
    birdeye_result = await tester.test_birdeye_data()
    
    # Create optimal strategy
    strategy = await tester.create_optimal_enhancement_strategy(dex_result, birdeye_result)
    
    print(f"\n🎊 TEST COMPLETE!")
    print(f"   📊 Strategy: {strategy['strategy']}")
    print(f"   📈 Combined Coverage: {strategy['dex_coverage']:.1f}% + {strategy['birdeye_enhancements']} enhancements")
    
    # Save results
    results = {
        'test_token': tester.test_token,
        'test_time': datetime.now().isoformat(),
        'dexscreener_result': dex_result,
        'birdeye_result': birdeye_result,
        'optimal_strategy': strategy
    }
    
    with open('data_enhancement_test_results.json', 'w') as f:
        json.dump(results, f, indent=2, default=str)
    
    print(f"   💾 Results saved to: data_enhancement_test_results.json")

if __name__ == "__main__":
    asyncio.run(main())
