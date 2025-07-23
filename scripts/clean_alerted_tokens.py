#!/usr/bin/env python3
"""
Clean Alerted Tokens Script

Removes tokens from alerted_tokens.json that are older than 7 days to allow re-alerting.
Creates a backup before making changes.
"""

import json
import time
import shutil
from datetime import datetime
from pathlib import Path

def clean_alerted_tokens():
    """Clean tokens older than 7 days from alerted_tokens.json"""
    
    data_dir = Path("data")
    alerted_tokens_file = data_dir / "alerted_tokens.json"
    backup_file = data_dir / f"alerted_tokens_backup_{int(time.time())}.json"
    
    if not alerted_tokens_file.exists():
        print("❌ alerted_tokens.json not found")
        return
    
    # Create backup
    shutil.copy2(alerted_tokens_file, backup_file)
    print(f"✅ Backup created: {backup_file}")
    
    # Load current data
    with open(alerted_tokens_file, 'r') as f:
        alerted_tokens = json.load(f)
    
    print(f"📊 Current tokens: {len(alerted_tokens)}")
    
    # Calculate cutoff time (7 days ago)
    current_time = time.time()
    seven_days_ago = current_time - (7 * 24 * 60 * 60)
    
    # Separate old and recent tokens
    old_tokens = {}
    recent_tokens = {}
    
    for address, timestamp in alerted_tokens.items():
        if timestamp < seven_days_ago:
            old_tokens[address] = timestamp
        else:
            recent_tokens[address] = timestamp
    
    print(f"🗑️  Tokens to remove: {len(old_tokens)}")
    print(f"✅ Tokens to keep: {len(recent_tokens)}")
    
    if old_tokens:
        print("\n🗑️  Removing old tokens:")
        for address, timestamp in old_tokens.items():
            alert_time = datetime.fromtimestamp(timestamp)
            days_ago = (current_time - timestamp) / (24 * 60 * 60)
            print(f"  {address[:20]}...{address[-8:]} | {alert_time.strftime('%Y-%m-%d %H:%M')} | {days_ago:.1f} days ago")
        
        # Save cleaned data
        with open(alerted_tokens_file, 'w') as f:
            json.dump(recent_tokens, f, indent=2)
        
        print(f"\n✅ Cleaned alerted_tokens.json")
        print(f"📊 Tokens remaining: {len(recent_tokens)}")
        print(f"🔄 These tokens can now be re-alerted if they qualify again")
    else:
        print("\n✅ No old tokens to remove - all entries are recent")

if __name__ == "__main__":
    print("🧹 Virtuoso Gem Hunter - Alerted Tokens Cleaner")
    print("=" * 50)
    clean_alerted_tokens()