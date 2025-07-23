#!/usr/bin/env python3
"""
Find Telegram Channel Chat ID

Multiple methods to find your channel's chat ID for bot alerts.
"""

import requests
import os
import json

def method_1_bot_updates():
    """Method 1: Use bot updates (requires recent activity)"""
    print("🔍 METHOD 1: Bot Updates Analysis")
    print("-" * 40)
    
    bot_token = os.getenv('TELEGRAM_BOT_TOKEN')
    if not bot_token:
        print("❌ TELEGRAM_BOT_TOKEN not found")
        return
    
    try:
        response = requests.get(f'https://api.telegram.org/bot{bot_token}/getUpdates', timeout=10)
        if response.status_code == 200:
            updates = response.json()
            channels_found = {}
            
            for update in updates.get('result', []):
                # Check for channel posts
                if 'channel_post' in update:
                    chat = update['channel_post']['chat']
                    if chat['type'] == 'channel':
                        channels_found[chat['id']] = {
                            'title': chat.get('title', 'Unknown'),
                            'username': chat.get('username'),
                            'id': chat['id']
                        }
                
                # Check for messages in channels
                if 'message' in update and update['message']['chat']['type'] == 'channel':
                    chat = update['message']['chat']
                    channels_found[chat['id']] = {
                        'title': chat.get('title', 'Unknown'),
                        'username': chat.get('username'),
                        'id': chat['id']
                    }
            
            if channels_found:
                print("✅ Found channels:")
                for channel_id, info in channels_found.items():
                    username_str = f"@{info['username']}" if info['username'] else "No username"
                    print(f"   📢 {info['title']}")
                    print(f"      Chat ID: {channel_id}")
                    print(f"      Username: {username_str}")
                    print()
                return channels_found
            else:
                print("❌ No channels found in recent updates")
                print("💡 Try posting in your channel first, then run this again")
        else:
            print(f"❌ API error: {response.status_code}")
    
    except Exception as e:
        print(f"❌ Error: {e}")
    
    return {}

def method_2_manual_instructions():
    """Method 2: Manual instructions for finding chat ID"""
    print("\n🔍 METHOD 2: Manual Chat ID Discovery")
    print("-" * 40)
    print()
    print("📋 STEP-BY-STEP INSTRUCTIONS:")
    print()
    print("1️⃣ ADD BOT TO YOUR CHANNEL:")
    print("   • Go to your Telegram channel")
    print("   • Click on channel name → Administrators")
    print("   • Click 'Add Administrator'")
    print("   • Search for: @virtuosogembot")
    print("   • Add the bot with 'Post Messages' permission")
    print()
    print("2️⃣ GET THE CHAT ID:")
    print("   Option A - Using @userinfobot:")
    print("   • Forward any message from your channel to @userinfobot")
    print("   • It will show you the chat ID")
    print()
    print("   Option B - Using web browser:")
    print("   • Open https://web.telegram.org")
    print("   • Go to your channel")
    print("   • Look at the URL: https://web.telegram.org/k/#-1001234567890")
    print("   • The number after 'k/#' is your chat ID")
    print()
    print("   Option C - Using @RawDataBot:")
    print("   • Add @RawDataBot to your channel")
    print("   • Send any message in the channel")
    print("   • The bot will reply with JSON data containing chat ID")
    print()
    print("3️⃣ TEST THE CHAT ID:")
    print("   • Use the test command below with your chat ID")

def method_3_web_api_approach():
    """Method 3: Web API approach for public channels"""
    print("\n🔍 METHOD 3: Public Channel Username Lookup")
    print("-" * 40)
    print()
    
    channel_username = input("Enter your channel username (without @): ").strip()
    if not channel_username:
        print("❌ No username provided")
        return
    
    bot_token = os.getenv('TELEGRAM_BOT_TOKEN')
    if not bot_token:
        print("❌ TELEGRAM_BOT_TOKEN not found")
        return
    
    try:
        # Try to get chat info using username
        response = requests.get(
            f'https://api.telegram.org/bot{bot_token}/getChat',
            params={'chat_id': f'@{channel_username}'},
            timeout=10
        )
        
        if response.status_code == 200:
            chat_info = response.json()['result']
            chat_id = chat_info['id']
            title = chat_info.get('title', 'Unknown')
            
            print(f"✅ Found channel: {title}")
            print(f"📋 Chat ID: {chat_id}")
            print(f"🔗 Username: @{channel_username}")
            
            return {chat_id: {'title': title, 'username': channel_username, 'id': chat_id}}
        else:
            error_data = response.json() if response.headers.get('content-type', '').startswith('application/json') else {}
            error_desc = error_data.get('description', 'Unknown error')
            print(f"❌ Cannot access channel: {error_desc}")
            
            if 'not found' in error_desc.lower():
                print("💡 Make sure:")
                print("   • Channel username is correct")
                print("   • Channel is public OR bot is added as admin")
    
    except Exception as e:
        print(f"❌ Error: {e}")
    
    return {}

def generate_test_command(chat_id):
    """Generate test command for a specific chat ID"""
    print(f"\n🧪 TEST COMMAND FOR CHAT ID: {chat_id}")
    print("-" * 50)
    print()
    print("Copy and paste this command to test:")
    print()
    print(f'python -c "')
    print(f'import requests, os')
    print(f'bot_token = os.getenv(\\"TELEGRAM_BOT_TOKEN\\")')
    print(f'response = requests.post(f\\"https://api.telegram.org/bot{{bot_token}}/sendMessage\\",')
    print(f'                       json={{\\"chat_id\\": {chat_id}, \\"text\\": \\"🎤 Test alert for subscribers!\\"}})')
    print(f'print(\\"✅ Success!\\" if response.status_code == 200 else f\\"❌ Failed: {{response.text}}\\")')
    print(f'"')
    print()
    print("If successful, update your environment:")
    print(f"export TELEGRAM_CHAT_ID={chat_id}")

def main():
    print("🔍 TELEGRAM CHANNEL CHAT ID FINDER")
    print("=" * 60)
    print()
    print("This tool will help you find your channel's chat ID using multiple methods.")
    print()
    
    # Method 1: Check bot updates
    channels_from_updates = method_1_bot_updates()
    
    # Method 2: Manual instructions
    method_2_manual_instructions()
    
    # Method 3: Username lookup
    print("\n" + "=" * 60)
    print("🔍 OPTIONAL: Try username lookup for public channels")
    try_username = input("Do you want to try looking up by username? (y/n): ").strip().lower()
    
    channels_from_username = {}
    if try_username == 'y':
        channels_from_username = method_3_web_api_approach()
    
    # Combine results
    all_channels = {**channels_from_updates, **channels_from_username}
    
    if all_channels:
        print("\n" + "=" * 60)
        print("📋 SUMMARY - FOUND CHANNELS:")
        print("=" * 60)
        
        for i, (chat_id, info) in enumerate(all_channels.items(), 1):
            print(f"\n🔹 OPTION {i}: {info['title']}")
            print(f"   Chat ID: {chat_id}")
            username_str = f"@{info['username']}" if info['username'] else "No public username"
            print(f"   Username: {username_str}")
            
            # Generate test command
            generate_test_command(chat_id)
    
    else:
        print("\n" + "=" * 60)
        print("❌ NO CHANNELS FOUND AUTOMATICALLY")
        print("=" * 60)
        print()
        print("💡 NEXT STEPS:")
        print("1. Follow the manual instructions above")
        print("2. Make sure your bot is added to the channel as admin")
        print("3. Post a message in the channel mentioning the bot")
        print("4. Run this script again")
        print()
        print("🆘 NEED HELP?")
        print("• Use @userinfobot (forward a message from your channel)")
        print("• Use @RawDataBot (add to channel, send message)")
        print("• Check web.telegram.org URL when viewing your channel")

if __name__ == "__main__":
    main() 