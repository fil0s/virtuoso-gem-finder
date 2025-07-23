#!/usr/bin/env python3
"""
Telegram Chat ID Helper

This script helps you find the correct chat ID for your Telegram channel or group
so subscribers can receive alerts.
"""

import requests
import os
import json
from datetime import datetime

def get_bot_token():
    """Get bot token from environment"""
    token = os.getenv('TELEGRAM_BOT_TOKEN')
    if not token:
        print("❌ TELEGRAM_BOT_TOKEN not found in environment variables")
        print("💡 Make sure to set your bot token first")
        return None
    return token

def get_chat_updates(bot_token):
    """Get recent updates to find chat IDs"""
    try:
        response = requests.get(f'https://api.telegram.org/bot{bot_token}/getUpdates', timeout=10)
        if response.status_code == 200:
            return response.json()
        else:
            print(f"❌ Failed to get updates: {response.status_code} - {response.text}")
            return None
    except Exception as e:
        print(f"❌ Error getting updates: {e}")
        return None

def analyze_chats(updates_data):
    """Analyze chat data from updates"""
    chats = {}
    
    for update in updates_data.get('result', []):
        chat_data = None
        
        # Check different update types
        if 'message' in update:
            chat_data = update['message']['chat']
        elif 'channel_post' in update:
            chat_data = update['channel_post']['chat']
        elif 'edited_message' in update:
            chat_data = update['edited_message']['chat']
        elif 'edited_channel_post' in update:
            chat_data = update['edited_channel_post']['chat']
        
        if chat_data:
            chat_id = chat_data['id']
            chat_type = chat_data['type']
            chat_title = chat_data.get('title', chat_data.get('first_name', 'Unknown'))
            username = chat_data.get('username', None)
            
            chats[chat_id] = {
                'id': chat_id,
                'type': chat_type,
                'title': chat_title,
                'username': username
            }
    
    return chats

def test_chat_access(bot_token, chat_id):
    """Test if bot can send messages to a chat"""
    try:
        # Try to get chat info first
        response = requests.get(
            f'https://api.telegram.org/bot{bot_token}/getChat',
            params={'chat_id': chat_id},
            timeout=10
        )
        
        if response.status_code == 200:
            chat_info = response.json()['result']
            return True, chat_info
        else:
            error_data = response.json() if response.headers.get('content-type', '').startswith('application/json') else {}
            return False, error_data.get('description', 'Unknown error')
            
    except Exception as e:
        return False, str(e)

def main():
    print("🔍 TELEGRAM CHAT ID FINDER")
    print("=" * 60)
    print()
    
    # Get bot token
    bot_token = get_bot_token()
    if not bot_token:
        return
    
    print(f"🤖 Using bot: {bot_token[:10]}...")
    print()
    
    # Get updates
    print("📡 Getting recent bot interactions...")
    updates_data = get_chat_updates(bot_token)
    if not updates_data:
        return
    
    # Analyze chats
    chats = analyze_chats(updates_data)
    
    if not chats:
        print("❌ No chats found in recent updates")
        print()
        print("💡 TO FIND YOUR CHAT ID:")
        print("1️⃣ Add your bot to the channel/group you want to use")
        print("2️⃣ Send a message in that channel/group (mention the bot)")
        print("3️⃣ Run this script again")
        print()
        print("📋 CURRENT SETUP:")
        current_chat_id = os.getenv('TELEGRAM_CHAT_ID')
        if current_chat_id:
            print(f"   • Current TELEGRAM_CHAT_ID: {current_chat_id}")
            can_access, info = test_chat_access(bot_token, current_chat_id)
            if can_access:
                chat_type = info.get('type', 'unknown')
                chat_title = info.get('title', info.get('first_name', 'Unknown'))
                print(f"   • Chat type: {chat_type.upper()}")
                print(f"   • Chat name: {chat_title}")
                if chat_type == 'private':
                    print("   ⚠️  This is a PRIVATE chat - only you will receive alerts!")
            else:
                print(f"   ❌ Cannot access chat: {info}")
        return
    
    print(f"✅ Found {len(chats)} chat(s) where your bot has been used:")
    print()
    
    # Display chats
    for i, (chat_id, chat_info) in enumerate(chats.items(), 1):
        chat_type = chat_info['type']
        chat_title = chat_info['title']
        username = chat_info['username']
        
        print(f"🔹 OPTION {i}:")
        print(f"   📋 Chat ID: {chat_id}")
        print(f"   📱 Type: {chat_type.upper()}")
        print(f"   🏷️  Title: {chat_title}")
        if username:
            print(f"   🔗 Username: @{username}")
        
        # Test access
        can_access, info = test_chat_access(bot_token, chat_id)
        if can_access:
            print(f"   ✅ Bot can send messages here")
            
            # Provide recommendation
            if chat_type == 'channel':
                print(f"   💡 PERFECT for broadcasting alerts to subscribers!")
            elif chat_type in ['group', 'supergroup']:
                print(f"   💡 Good for group notifications")
            elif chat_type == 'private':
                print(f"   ⚠️  Private chat - only this person gets alerts")
        else:
            print(f"   ❌ Cannot send messages: {info}")
        
        print()
    
    # Current setup check
    current_chat_id = os.getenv('TELEGRAM_CHAT_ID')
    if current_chat_id:
        print("📋 CURRENT CONFIGURATION:")
        print(f"   • TELEGRAM_CHAT_ID: {current_chat_id}")
        
        if int(current_chat_id) in chats:
            current_chat = chats[int(current_chat_id)]
            print(f"   • Currently using: {current_chat['type'].upper()} - {current_chat['title']}")
            
            if current_chat['type'] == 'private':
                print("   ⚠️  WARNING: Using private chat - subscribers won't get alerts!")
        else:
            print("   ⚠️  Current chat ID not found in recent interactions")
        print()
    
    # Recommendations
    print("💡 RECOMMENDATIONS:")
    print("=" * 30)
    
    # Find best options
    channels = [c for c in chats.values() if c['type'] == 'channel']
    groups = [c for c in chats.values() if c['type'] in ['group', 'supergroup']]
    
    if channels:
        print("🎯 BEST OPTION - Use a CHANNEL for broadcasting:")
        for channel in channels:
            print(f"   export TELEGRAM_CHAT_ID={channel['id']}")
            print(f"   # Channel: {channel['title']}")
        print()
    
    if groups:
        print("📢 ALTERNATIVE - Use a GROUP for notifications:")
        for group in groups:
            print(f"   export TELEGRAM_CHAT_ID={group['id']}")
            print(f"   # Group: {group['title']}")
        print()
    
    if not channels and not groups:
        print("❌ No channels or groups found!")
        print()
        print("🛠️  SETUP INSTRUCTIONS:")
        print("1️⃣ Create a Telegram channel or group")
        print("2️⃣ Add your bot (@virtuosogembot) as admin")
        print("3️⃣ Send a test message mentioning the bot")
        print("4️⃣ Run this script again to get the chat ID")
        print("5️⃣ Update TELEGRAM_CHAT_ID environment variable")

if __name__ == "__main__":
    main() 