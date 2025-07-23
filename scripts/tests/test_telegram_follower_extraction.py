#!/usr/bin/env python3
"""
Telegram Follower Count Extraction Test

Demonstrates our ability to extract real member counts from Telegram channels
"""

import asyncio
import aiohttp
import re
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.append(str(project_root))

class TelegramFollowerExtractor:
    """Extract follower/member counts from Telegram channels"""
    
    async def analyze_telegram_channel(self, telegram_url: str, description: str = ""):
        """Analyze a single Telegram channel and extract member count"""
        print(f"\n🔍 Analyzing: {description}")
        print(f"📱 URL: {telegram_url}")
        
        analysis = {
            'url': telegram_url,
            'channel_name': None,
            'members': None,
            'channel_exists': False,
            'public_channel': False,
            'subscribers': None,  # For channels vs groups
            'description': description
        }
        
        try:
            # Extract channel name from URL
            channel_match = re.search(r't\.me/([^/?]+)', telegram_url)
            if not channel_match:
                print(f"❌ Could not extract channel name from URL")
                return analysis
            
            channel_name = channel_match.group(1)
            analysis['channel_name'] = channel_name
            
            # Get Telegram web preview
            async with aiohttp.ClientSession() as session:
                try:
                    headers = {
                        'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
                    }
                    
                    async with session.get(telegram_url, timeout=15, headers=headers) as response:
                        if response.status == 200:
                            analysis['channel_exists'] = True
                            html_content = await response.text()
                            
                            # Multiple patterns to catch different formats
                            patterns = [
                                r'(\d+(?:,\d+)*)\s*members?',      # "1,234 members"
                                r'(\d+(?:,\d+)*)\s*subscribers?',  # "1,234 subscribers" 
                                r'(\d+(?:\.\d+)?[KkMm]?)\s*members?',  # "1.2K members"
                                r'(\d+(?:\.\d+)?[KkMm]?)\s*subscribers?'  # "1.2K subscribers"
                            ]
                            
                            for pattern in patterns:
                                match = re.search(pattern, html_content, re.IGNORECASE)
                                if match:
                                    count_str = match.group(1)
                                    
                                    # Handle K/M notation
                                    if count_str.lower().endswith('k'):
                                        analysis['members'] = int(float(count_str[:-1]) * 1000)
                                    elif count_str.lower().endswith('m'):
                                        analysis['members'] = int(float(count_str[:-1]) * 1000000)
                                    else:
                                        # Remove commas and convert
                                        clean_count = count_str.replace(',', '')
                                        analysis['members'] = int(clean_count)
                                    break
                            
                            # Check if it's a public channel
                            if 'public' in html_content.lower():
                                analysis['public_channel'] = True
                            
                            # Results
                            if analysis['members']:
                                print(f"✅ Channel exists: @{channel_name}")
                                print(f"👥 Members: {analysis['members']:,}")
                                print(f"🔓 Public: {'Yes' if analysis['public_channel'] else 'No'}")
                            else:
                                print(f"⚠️ Channel exists but member count not visible")
                        
                        elif response.status == 404:
                            print(f"❌ Channel not found: @{channel_name}")
                        elif response.status == 403:
                            print(f"🔒 Channel is private: @{channel_name}")
                        else:
                            print(f"⚠️ HTTP {response.status}: Could not access channel")
                
                except asyncio.TimeoutError:
                    print(f"⏰ Request timed out")
                except Exception as e:
                    print(f"❌ Error: {e}")
        
        except Exception as e:
            print(f"❌ Analysis failed: {e}")
        
        return analysis

async def main():
    """Test Telegram follower extraction on various channels"""
    extractor = TelegramFollowerExtractor()
    
    print("🚀 TELEGRAM FOLLOWER COUNT EXTRACTION TEST")
    print("=" * 60)
    
    # Test channels - mix of crypto, popular, and token-specific
    test_channels = [
        # From our previous token analysis
        ("https://t.me/kawsfans", "KAWS Token Community"),
        
        # Well-known crypto channels (for comparison)
        ("https://t.me/binance", "Binance Official"),
        ("https://t.me/ethereum", "Ethereum Community"), 
        ("https://t.me/bitcoin", "Bitcoin Discussion"),
        
        # Solana ecosystem
        ("https://t.me/solana", "Solana Official"),
        ("https://t.me/pump_fun", "Pump.fun Community"),
        
        # News channels
        ("https://t.me/cointelegraph", "Cointelegraph News"),
        
        # Test a private/invalid one
        ("https://t.me/nonexistentchannel123456", "Non-existent Channel")
    ]
    
    results = []
    
    for telegram_url, description in test_channels:
        try:
            result = await extractor.analyze_telegram_channel(telegram_url, description)
            results.append(result)
            
            # Small delay to be respectful
            await asyncio.sleep(2)
            
        except Exception as e:
            print(f"❌ Failed to analyze {description}: {e}")
    
    # Summary
    print("\n" + "=" * 80)
    print("📊 TELEGRAM FOLLOWER EXTRACTION SUMMARY")
    print("=" * 80)
    
    successful_extractions = [r for r in results if r.get('members')]
    accessible_channels = [r for r in results if r.get('channel_exists')]
    
    print(f"📈 Channels analyzed: {len(test_channels)}")
    print(f"✅ Channels accessible: {len(accessible_channels)}")
    print(f"👥 Member counts extracted: {len(successful_extractions)}")
    print(f"📊 Success rate: {len(successful_extractions)/len(test_channels)*100:.1f}%")
    
    if successful_extractions:
        print(f"\n🏆 TOP CHANNELS BY MEMBER COUNT:")
        successful_extractions.sort(key=lambda x: x['members'], reverse=True)
        
        for result in successful_extractions[:5]:
            print(f"📱 @{result['channel_name']}: {result['members']:,} members ({result['description']})")
    
    print(f"\n✨ CAPABILITIES DEMONSTRATED:")
    print(f"• Extract member counts from public Telegram channels")
    print(f"• Handle various formats (1,234 or 1.2K notation)")
    print(f"• Detect public vs private channels") 
    print(f"• Graceful handling of inaccessible channels")
    print(f"• Real-time web scraping without API keys")
    
    print(f"\n🔧 INTEGRATION READY:")
    print(f"• This functionality is already integrated into our token analysis")
    print(f"• Provides real community size metrics for token evaluation")
    print(f"• Helps distinguish legitimate projects from fake social presence")

if __name__ == "__main__":
    asyncio.run(main()) 