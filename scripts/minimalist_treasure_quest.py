#!/usr/bin/env python3
"""
🏴‍☠️ VirtuosoHunt Treasure Island Quest - Minimalist Edition
Clean, visual-focused ASCII art with proper spacing and minimal text overlay
"""

import time
from rich.console import Console
from colorama import init, Fore, Back, Style

# Initialize colorama
init(autoreset=True)

class MinimalistTreasureQuest:
    def __init__(self):
        self.console = Console()
    
    def create_scene_1_establishing(self):
        """Scene 1: The Quest Begins - Clean establishing shot"""
        return f"""
{Fore.CYAN + Style.BRIGHT}
╔══════════════════════════════════════════════════════════════════════════════╗
║                    🏴‍☠️ VIRTUOSO HUNT - TREASURE ISLAND QUEST 🏴‍☠️                   ║
╚══════════════════════════════════════════════════════════════════════════════╝
{Style.RESET_ALL}

{Fore.YELLOW + Style.BRIGHT}                              ☀️{Style.RESET_ALL}
{Fore.YELLOW + Style.DIM}                    ～～～～～～～～～～～～～{Style.RESET_ALL}
{Fore.MAGENTA + Style.DIM}                        ⛅    ⛅{Style.RESET_ALL}

{Fore.GREEN + Style.BRIGHT}                     🏝️ 🌴  🌴 🏝️{Style.RESET_ALL}
{Fore.GREEN + Style.DIM}                         ▲ ▲ ▲{Style.RESET_ALL}

{Fore.BLUE + Style.DIM}     ═══════════════════════════════════════════════════════{Style.RESET_ALL}
{Fore.BLUE + Style.BRIGHT}     ～～～～～～～～～～～～～～～～～～～～～～～～～～～～～～～{Style.RESET_ALL}
{Fore.BLUE}     ～～～～～～～～～～～～～～～～～～～～～～～～～～～～～～～～～{Style.RESET_ALL}
{Fore.BLUE + Style.DIM}     ～～～～～～～～～～～～～～～～～～～～～～～～～～～～～～～{Style.RESET_ALL}


                                {Fore.RED + Style.BRIGHT}🏴‍☠️{Style.RESET_ALL}
                                {Fore.WHITE + Style.BRIGHT}║{Style.RESET_ALL}
                            {Fore.YELLOW + Style.BRIGHT}┌─────┐{Style.RESET_ALL}
                            {Fore.YELLOW}│  V  │{Style.RESET_ALL}
                        {Fore.YELLOW + Style.DIM}┌─────────────────┐{Style.RESET_ALL}
                        {Fore.YELLOW + Style.DIM}│                 │{Style.RESET_ALL}
                        {Fore.YELLOW + Style.DIM}│    VIRTUOSO     │{Style.RESET_ALL}
                        {Fore.YELLOW + Style.DIM}│      ⚓ ⚓       │{Style.RESET_ALL}
                        {Fore.YELLOW + Style.DIM}└─────────────────┘{Style.RESET_ALL}

{Fore.BLUE + Style.BRIGHT}     ～～～～～～～～～～～～～～～～～～～～～～～～～～～～～～～～～{Style.RESET_ALL}
{Fore.BLUE}     ～～～～～～～～～～～～～～～～～～～～～～～～～～～～～～～～～～～{Style.RESET_ALL}


{Fore.WHITE + Style.BRIGHT}┌─ MISSION BRIEFING ─────────────────────────────────────────────┐{Style.RESET_ALL}
{Fore.GREEN + Style.BRIGHT}│ 🎯 Navigate crypto waters to reach treasure island             │{Style.RESET_ALL}
{Fore.CYAN + Style.BRIGHT}│ ⚓ Discover profitable tokens before competing hunters         │{Style.RESET_ALL}
{Fore.RED + Style.BRIGHT}│ ⚠️  Beware: Whales, sharks, and market volatility ahead        │{Style.RESET_ALL}
{Fore.WHITE + Style.BRIGHT}└────────────────────────────────────────────────────────────────┘{Style.RESET_ALL}
"""

    def create_scene_2_dangerous_waters(self):
        """Scene 2: Navigating Dangerous Waters - Clean volatility zone"""
        return f"""
{Fore.RED + Style.BRIGHT}
╔══════════════════════════════════════════════════════════════════════════════╗
║                           ⚠️  VOLATILITY ZONE ⚠️                              ║
╚══════════════════════════════════════════════════════════════════════════════╝
{Style.RESET_ALL}

{Fore.BLACK + Style.BRIGHT}               ⛈️     ⛈️     ⛈️{Style.RESET_ALL}
{Fore.RED + Style.DIM}            ⚡      ⚡      ⚡{Style.RESET_ALL}

{Fore.BLUE + Style.BRIGHT}     🌊～～～～～～～～～～～～～～～～～～～～～～～～～～～～🌊{Style.RESET_ALL}
{Fore.BLUE}        ～～～～～～～～～～～～～～～～～～～～～～～～～～～～～{Style.RESET_ALL}
{Fore.BLUE + Style.DIM}         ～～～～～～～～～～～～～～～～～～～～～～～～～～～{Style.RESET_ALL}


                                {Fore.RED + Style.BRIGHT}🏴‍☠️{Style.RESET_ALL}
                                {Fore.WHITE + Style.BRIGHT}║{Style.RESET_ALL}
                            {Fore.YELLOW + Style.BRIGHT}┌─────┐{Style.RESET_ALL}
                            {Fore.YELLOW}│  V  │{Style.RESET_ALL}
                        {Fore.YELLOW + Style.DIM}┌─────────────────┐{Style.RESET_ALL}
                        {Fore.YELLOW + Style.DIM}│    VIRTUOSO     │{Style.RESET_ALL}
                        {Fore.YELLOW + Style.DIM}│      ⚓ ⚓       │{Style.RESET_ALL}
                        {Fore.YELLOW + Style.DIM}└─────────────────┘{Style.RESET_ALL}

{Fore.BLUE + Style.BRIGHT}     🌊～～～～～～～～～～～～～～～～～～～～～～～～～～～～🌊{Style.RESET_ALL}
{Fore.BLUE}        ～～～～～～～～～～～～～～～～～～～～～～～～～～～～～{Style.RESET_ALL}


{Fore.WHITE + Style.BRIGHT}┌─ MARKET ANALYSIS ──────────────────────────────────────────────┐{Style.RESET_ALL}
{Fore.YELLOW + Style.BRIGHT}│ 📊 Volume Spike: +247%                                         │{Style.RESET_ALL}
{Fore.GREEN + Style.BRIGHT}│ 🎯 Opportunities: 12 potential gems detected                   │{Style.RESET_ALL}
{Fore.CYAN + Style.BRIGHT}│ ⚡ Status: Algorithm actively hunting                           │{Style.RESET_ALL}
{Fore.WHITE + Style.BRIGHT}└────────────────────────────────────────────────────────────────┘{Style.RESET_ALL}
"""

    def create_scene_3_whale_encounter(self):
        """Scene 3: Whale Territory - Clean whale visualization"""
        return f"""
{Fore.BLUE + Style.BRIGHT}
╔══════════════════════════════════════════════════════════════════════════════╗
║                            🐋 WHALE TERRITORY 🐋                             ║
╚══════════════════════════════════════════════════════════════════════════════╝
{Style.RESET_ALL}

{Fore.BLUE + Style.BRIGHT}        🐋                                    🐋{Style.RESET_ALL}
{Fore.BLUE}     ～～～～～～～～～～～～～～～～～～～～～～～～～～～～～～～{Style.RESET_ALL}
{Fore.BLUE + Style.DIM}      ～～～～～～～～～～～～～～～～～～～～～～～～～～～～～{Style.RESET_ALL}


                                {Fore.RED + Style.BRIGHT}🏴‍☠️{Style.RESET_ALL}
                                {Fore.WHITE + Style.BRIGHT}║{Style.RESET_ALL}
                            {Fore.YELLOW + Style.BRIGHT}┌─────┐{Style.RESET_ALL}
                            {Fore.YELLOW}│  V  │{Style.RESET_ALL}
                        {Fore.YELLOW + Style.DIM}┌─────────────────┐{Style.RESET_ALL}
                        {Fore.YELLOW + Style.DIM}│    VIRTUOSO     │{Style.RESET_ALL}
                        {Fore.YELLOW + Style.DIM}│      ⚓ ⚓       │{Style.RESET_ALL}
                        {Fore.YELLOW + Style.DIM}└─────────────────┘{Style.RESET_ALL}

{Fore.BLUE}     ～～～～～～～～～～～～～～～～～～～～～～～～～～～～～～～{Style.RESET_ALL}
{Fore.BLUE + Style.DIM}      ～～～～～～～～～～～～～～～～～～～～～～～～～～～～～{Style.RESET_ALL}
                         {Fore.BLUE + Style.BRIGHT}🐋{Style.RESET_ALL}
{Fore.BLUE + Style.BRIGHT}     ～～～～～～～～～～～～～～～～～～～～～～～～～～～～～～～{Style.RESET_ALL}


{Fore.WHITE + Style.BRIGHT}┌─ WHALE ACTIVITY ───────────────────────────────────────────────┐{Style.RESET_ALL}
{Fore.BLUE + Style.BRIGHT}│ 🐋 Whale #1: 50M SOL  │  🐋 Whale #2: 25M SOL                  │{Style.RESET_ALL}
{Fore.MAGENTA + Style.BRIGHT}│ 📈 Activity: +500% token accumulation                          │{Style.RESET_ALL}
{Fore.CYAN + Style.BRIGHT}│ 🎯 Strategy: Following whale movements                          │{Style.RESET_ALL}
{Fore.WHITE + Style.BRIGHT}└────────────────────────────────────────────────────────────────┘{Style.RESET_ALL}
"""

    def create_scene_4_shark_territory(self):
        """Scene 4: Shark Territory - Minimalist danger zone"""
        return f"""
{Fore.RED + Style.BRIGHT}
╔══════════════════════════════════════════════════════════════════════════════╗
║                           🦈 DANGER ZONE 🦈                                  ║
╚══════════════════════════════════════════════════════════════════════════════╝
{Style.RESET_ALL}

        {Fore.RED + Style.BRIGHT}🦈{Style.RESET_ALL}          {Fore.RED + Style.BRIGHT}🦈{Style.RESET_ALL}          {Fore.RED + Style.BRIGHT}🦈{Style.RESET_ALL}
{Fore.BLUE + Style.BRIGHT}     🌊～～～～～～～～～～～～～～～～～～～～～～～～～～～～🌊{Style.RESET_ALL}
{Fore.BLUE}        ～～～～～     ～～～～～～～～～～～～～～～     ～～～{Style.RESET_ALL}
           {Fore.RED + Style.BRIGHT}🦈{Style.RESET_ALL}                                {Fore.RED + Style.BRIGHT}🦈{Style.RESET_ALL}


                                {Fore.RED + Style.BRIGHT}🏴‍☠️{Style.RESET_ALL}
                                {Fore.WHITE + Style.BRIGHT}║{Style.RESET_ALL}
                            {Fore.YELLOW + Style.BRIGHT}┌─────┐{Style.RESET_ALL}
                            {Fore.YELLOW}│  V  │{Style.RESET_ALL}  {Fore.GREEN + Style.BRIGHT}🛡️{Style.RESET_ALL}
                        {Fore.YELLOW + Style.DIM}┌─────────────────┐{Style.RESET_ALL}
                        {Fore.YELLOW + Style.DIM}│    VIRTUOSO     │{Style.RESET_ALL}
                        {Fore.YELLOW + Style.DIM}│      ⚓ ⚓       │{Style.RESET_ALL}
                        {Fore.YELLOW + Style.DIM}└─────────────────┘{Style.RESET_ALL}

{Fore.BLUE + Style.BRIGHT}     🌊～～～～～～～～～～～～～～～～～～～～～～～～～～～～🌊{Style.RESET_ALL}
      {Fore.RED + Style.BRIGHT}🦈{Style.RESET_ALL}                                    {Fore.RED + Style.BRIGHT}🦈{Style.RESET_ALL}


{Fore.WHITE + Style.BRIGHT}┌─ PROTECTION SYSTEMS ───────────────────────────────────────────┐{Style.RESET_ALL}
{Fore.GREEN + Style.BRIGHT}│ 🛡️ Rug Pull Detection: ACTIVE  │  🔍 Liquidity Scan: ACTIVE    │{Style.RESET_ALL}
{Fore.CYAN + Style.BRIGHT}│ ✅ Smart Contract Audit: VERIFIED                               │{Style.RESET_ALL}
{Fore.YELLOW + Style.BRIGHT}│ ⚡ Stop Loss Orders: READY                                      │{Style.RESET_ALL}
{Fore.WHITE + Style.BRIGHT}└────────────────────────────────────────────────────────────────┘{Style.RESET_ALL}
"""

    def create_scene_5_storm(self):
        """Scene 5: Market Storm - Clean atmospheric design"""
        return f"""
{Fore.WHITE + Style.BRIGHT}
╔══════════════════════════════════════════════════════════════════════════════╗
║                            ⛈️  MARKET STORM ⛈️                               ║
╚══════════════════════════════════════════════════════════════════════════════╝
{Style.RESET_ALL}

{Fore.WHITE + Style.BRIGHT}          ⚡    ⛈️    ⚡    ⛈️    ⚡{Style.RESET_ALL}
{Fore.BLACK + Style.BRIGHT}     ████████████████████████████████████████████{Style.RESET_ALL}
{Fore.WHITE + Style.DIM}          ▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓{Style.RESET_ALL}
{Fore.BLUE + Style.BRIGHT}     🌊～～～～～～～～～～～～～～～～～～～～～～～～～～～～🌊{Style.RESET_ALL}


                                {Fore.RED + Style.BRIGHT}🏴‍☠️{Style.RESET_ALL}
                                {Fore.WHITE + Style.BRIGHT}║{Style.RESET_ALL}
                            {Fore.YELLOW + Style.BRIGHT}┌─────┐{Style.RESET_ALL}
                            {Fore.YELLOW}│  V  │{Style.RESET_ALL}  {Fore.CYAN + Style.BRIGHT}⚓{Style.RESET_ALL}
                        {Fore.YELLOW + Style.DIM}┌─────────────────┐{Style.RESET_ALL}
                        {Fore.YELLOW + Style.DIM}│    VIRTUOSO     │{Style.RESET_ALL}
                        {Fore.YELLOW + Style.DIM}│      ⚓ ⚓       │{Style.RESET_ALL}
                        {Fore.YELLOW + Style.DIM}└─────────────────┘{Style.RESET_ALL}

{Fore.BLUE + Style.BRIGHT}     🌊～～～～～～～～～～～～～～～～～～～～～～～～～～～～🌊{Style.RESET_ALL}
{Fore.WHITE + Style.BRIGHT}          ⚡    ⛈️    ⚡    ⛈️    ⚡{Style.RESET_ALL}


{Fore.WHITE + Style.BRIGHT}┌─ MARKET CONDITIONS ────────────────────────────────────────────┐{Style.RESET_ALL}
{Fore.RED + Style.BRIGHT}│ 📉 Volatility: EXTREME (95%)  │  💔 Fear & Greed: 15          │{Style.RESET_ALL}
{Fore.GREEN + Style.BRIGHT}│ 🎯 Opportunity Score: HIGH (Contrarian Signal)                 │{Style.RESET_ALL}
{Fore.CYAN + Style.BRIGHT}│ ⚓ Strategy: HOLD STEADY - Storm will pass                      │{Style.RESET_ALL}
{Fore.WHITE + Style.BRIGHT}└────────────────────────────────────────────────────────────────┘{Style.RESET_ALL}
"""

    def create_scene_6_approaching_island(self):
        """Scene 6: Approaching Island - Clean destination view"""
        return f"""
{Fore.GREEN + Style.BRIGHT}
╔══════════════════════════════════════════════════════════════════════════════╗
║                        🏝️ TREASURE ISLAND AHEAD 🏝️                          ║
╚══════════════════════════════════════════════════════════════════════════════╝
{Style.RESET_ALL}

{Fore.YELLOW + Style.BRIGHT}                            ☀️{Style.RESET_ALL}
{Fore.GREEN + Style.BRIGHT}                   🏝️ 🌴 🌴 🌴 🏝️{Style.RESET_ALL}
{Fore.GREEN}                     ┌─────────────────┐{Style.RESET_ALL}
{Fore.GREEN}                     │  💰  💎  🪙  💰  │{Style.RESET_ALL}
{Fore.GREEN}                     │     TREASURE     │{Style.RESET_ALL}
{Fore.GREEN}                     │   💎  🪙  💰    │{Style.RESET_ALL}
{Fore.GREEN}                     └─────────────────┘{Style.RESET_ALL}

{Fore.BLUE + Style.BRIGHT}     ～～～～～～～～～～～～～～～～～～～～～～～～～～～～～～～{Style.RESET_ALL}
{Fore.BLUE}     ～～～～～～～～～～～～～～～～～～～～～～～～～～～～～～～～～{Style.RESET_ALL}


                                {Fore.RED + Style.BRIGHT}🏴‍☠️{Style.RESET_ALL}
                                {Fore.WHITE + Style.BRIGHT}║{Style.RESET_ALL}
                            {Fore.YELLOW + Style.BRIGHT}┌─────┐{Style.RESET_ALL}
                            {Fore.YELLOW}│  V  │{Style.RESET_ALL}  {Fore.GREEN + Style.BRIGHT}🎯{Style.RESET_ALL}
                        {Fore.YELLOW + Style.DIM}┌─────────────────┐{Style.RESET_ALL}
                        {Fore.YELLOW + Style.DIM}│    VIRTUOSO     │{Style.RESET_ALL}
                        {Fore.YELLOW + Style.DIM}│      ⚓ ⚓       │{Style.RESET_ALL}
                        {Fore.YELLOW + Style.DIM}└─────────────────┘{Style.RESET_ALL}

{Fore.BLUE + Style.BRIGHT}     ～～～～～～～～～～～～～～～～～～～～～～～～～～～～～～～～～{Style.RESET_ALL}


{Fore.WHITE + Style.BRIGHT}┌─ TREASURE ANALYSIS ────────────────────────────────────────────┐{Style.RESET_ALL}
{Fore.GREEN + Style.BRIGHT}│ 💰 High-Value Tokens: 7 gems discovered                        │{Style.RESET_ALL}
{Fore.YELLOW + Style.BRIGHT}│ 📊 Growth Potential: 10-100x estimated                         │{Style.RESET_ALL}
{Fore.CYAN + Style.BRIGHT}│ ⚡ Entry Status: Early opportunity confirmed                     │{Style.RESET_ALL}
{Fore.WHITE + Style.BRIGHT}└────────────────────────────────────────────────────────────────┘{Style.RESET_ALL}
"""

    def create_scene_7_discovery(self):
        """Scene 7: Token Discovery - Clean treasure layout"""
        return f"""
{Fore.YELLOW + Style.BRIGHT}
╔══════════════════════════════════════════════════════════════════════════════╗
║                           ⚓ LANDING SUCCESSFUL ⚓                            ║
╚══════════════════════════════════════════════════════════════════════════════╝
{Style.RESET_ALL}

{Fore.GREEN + Style.BRIGHT}                   🏝️ 🌴    🌴    🌴 🏝️{Style.RESET_ALL}

{Fore.YELLOW + Style.BRIGHT}                    ┌─────────────────────┐{Style.RESET_ALL}
{Fore.YELLOW}                    │     TREASURE CHEST      │{Style.RESET_ALL}
{Fore.YELLOW}                    ├─────────────────────────┤{Style.RESET_ALL}
{Fore.YELLOW}                    │  💎 $SOLVAULT    +2,347%│{Style.RESET_ALL}
{Fore.YELLOW}                    │  🪙 $MOODENG     +1,892%│{Style.RESET_ALL}
{Fore.YELLOW}                    │  💰 $PNUT        +5,672%│{Style.RESET_ALL}
{Fore.YELLOW}                    │  ⭐ $GOAT        +3,421%│{Style.RESET_ALL}
{Fore.YELLOW}                    └─────────────────────────┘{Style.RESET_ALL}


            {Fore.YELLOW + Style.DIM}┌─────────────────┐{Style.RESET_ALL}
            {Fore.YELLOW + Style.DIM}│    VIRTUOSO     │{Style.RESET_ALL}  {Fore.CYAN + Style.BRIGHT}⚓ ANCHORED{Style.RESET_ALL}
            {Fore.YELLOW + Style.DIM}│      ⚓ ⚓       │{Style.RESET_ALL}
            {Fore.YELLOW + Style.DIM}└─────────────────┘{Style.RESET_ALL}


{Fore.WHITE + Style.BRIGHT}┌─ DISCOVERY STATUS ─────────────────────────────────────────────┐{Style.RESET_ALL}
{Fore.GREEN + Style.BRIGHT}│ ✅ 7 High-Value Tokens Found                                   │{Style.RESET_ALL}
{Fore.CYAN + Style.BRIGHT}│ ✅ Smart Contracts Verified                                     │{Style.RESET_ALL}
{Fore.YELLOW + Style.BRIGHT}│ ✅ Early Entry Positions Secured                               │{Style.RESET_ALL}
{Fore.WHITE + Style.BRIGHT}└────────────────────────────────────────────────────────────────┘{Style.RESET_ALL}
"""

    def create_scene_8_victory(self):
        """Scene 8: Victory - Clean celebration layout"""
        return f"""
{Fore.YELLOW + Style.BRIGHT}
╔══════════════════════════════════════════════════════════════════════════════╗
║                           🏆 QUEST COMPLETED 🏆                              ║
╚══════════════════════════════════════════════════════════════════════════════╝
{Style.RESET_ALL}

{Fore.YELLOW + Style.BRIGHT}                          🎆 VICTORY 🎆{Style.RESET_ALL}
{Fore.GREEN + Style.BRIGHT}                   🏝️ 🌴  🏆  🌴 🏝️{Style.RESET_ALL}

{Fore.YELLOW + Style.BRIGHT}            ┌─────────────────────────────────┐{Style.RESET_ALL}
{Fore.YELLOW}            │        TREASURE SECURED         │{Style.RESET_ALL}
{Fore.YELLOW}            ├─────────────────────────────────┤{Style.RESET_ALL}
{Fore.YELLOW}            │  🚀 Portfolio Growth:  +5,247%  │{Style.RESET_ALL}
{Fore.YELLOW}            │  💎 Gems Discovered:   15 tokens│{Style.RESET_ALL}
{Fore.YELLOW}            │  🪙 Total Value:       $2.5M    │{Style.RESET_ALL}
{Fore.YELLOW}            │  ⭐ Success Rate:      94%      │{Style.RESET_ALL}
{Fore.YELLOW}            └─────────────────────────────────┘{Style.RESET_ALL}

        {Fore.YELLOW + Style.DIM}┌─────────────────┐{Style.RESET_ALL}
        {Fore.YELLOW + Style.DIM}│    VIRTUOSO     │{Style.RESET_ALL}      {Fore.YELLOW + Style.BRIGHT}🏆 LEGENDARY{Style.RESET_ALL}
        {Fore.YELLOW + Style.DIM}│      ⚓ ⚓       │{Style.RESET_ALL}
        {Fore.YELLOW + Style.DIM}└─────────────────┘{Style.RESET_ALL}


{Fore.WHITE + Style.BRIGHT}┌─ MISSION ACCOMPLISHED ─────────────────────────────────────────┐{Style.RESET_ALL}
{Fore.GREEN + Style.BRIGHT}│ 🏆 Legendary Trader Status: UNLOCKED                           │{Style.RESET_ALL}
{Fore.YELLOW + Style.BRIGHT}│ 💰 Treasure Island: CONQUERED                                  │{Style.RESET_ALL}
{Fore.CYAN + Style.BRIGHT}│ ⚓ The VirtuosoHunt continues to new horizons...                │{Style.RESET_ALL}
{Fore.WHITE + Style.BRIGHT}└────────────────────────────────────────────────────────────────┘{Style.RESET_ALL}
"""

    def animate_all_scenes(self, duration_per_scene=4):
        """Animate through all 8 scenes with proper spacing"""
        scenes = [
            ("The Quest Begins", self.create_scene_1_establishing()),
            ("Dangerous Waters", self.create_scene_2_dangerous_waters()),
            ("Whale Territory", self.create_scene_3_whale_encounter()),
            ("Shark Territory", self.create_scene_4_shark_territory()),
            ("Market Storm", self.create_scene_5_storm()),
            ("Approaching Island", self.create_scene_6_approaching_island()),
            ("Token Discovery", self.create_scene_7_discovery()),
            ("Victory", self.create_scene_8_victory())
        ]
        
        for i, (title, scene) in enumerate(scenes, 1):
            self.console.clear()
            print(f"\n{Fore.CYAN + Style.BRIGHT}━━━ SCENE {i}/8: {title} ━━━{Style.RESET_ALL}")
            print(scene)
            time.sleep(duration_per_scene)
            print(f"\n{Fore.WHITE + Style.DIM}Press Ctrl+C to stop animation...{Style.RESET_ALL}")

    def display_scene_menu(self):
        """Display interactive scene selection menu"""
        scenes = {
            1: "The Quest Begins",
            2: "Dangerous Waters", 
            3: "Whale Territory",
            4: "Shark Territory",
            5: "Market Storm",
            6: "Approaching Island",
            7: "Token Discovery",
            8: "Victory"
        }
        
        print(f"\n{Fore.YELLOW + Style.BRIGHT}🏴‍☠️ MINIMALIST TREASURE QUEST - SCENE SELECTOR 🏴‍☠️{Style.RESET_ALL}")
        print("=" * 60)
        
        for i, title in scenes.items():
            print(f"{Fore.CYAN}{i}.{Style.RESET_ALL} {title}")
        
        print(f"{Fore.GREEN}9.{Style.RESET_ALL} Play Full Animation (All Scenes)")
        print(f"{Fore.RED}0.{Style.RESET_ALL} Exit")
        
        return input(f"\n{Fore.YELLOW}Select scene (0-9): {Style.RESET_ALL}").strip()

def main():
    quest = MinimalistTreasureQuest()
    
    print(f"""
{Fore.YELLOW + Style.BRIGHT}
╔══════════════════════════════════════════════════════════════════════════════╗
║           🏴‍☠️ VIRTUOSO TREASURE QUEST - MINIMALIST EDITION 🏴‍☠️            ║
║                Clean Visual Storytelling with Proper Spacing                 ║
╚══════════════════════════════════════════════════════════════════════════════╝
{Style.RESET_ALL}
    """)
    
    while True:
        try:
            choice = quest.display_scene_menu()
            
            if choice == '0':
                print(f"\n{Fore.CYAN}⚓ Fair winds and following seas! ⚓{Style.RESET_ALL}")
                break
            elif choice == '1':
                quest.console.clear()
                print(quest.create_scene_1_establishing())
            elif choice == '2':
                quest.console.clear()
                print(quest.create_scene_2_dangerous_waters())
            elif choice == '3':
                quest.console.clear()
                print(quest.create_scene_3_whale_encounter())
            elif choice == '4':
                quest.console.clear()
                print(quest.create_scene_4_shark_territory())
            elif choice == '5':
                quest.console.clear()
                print(quest.create_scene_5_storm())
            elif choice == '6':
                quest.console.clear()
                print(quest.create_scene_6_approaching_island())
            elif choice == '7':
                quest.console.clear()
                print(quest.create_scene_7_discovery())
            elif choice == '8':
                quest.console.clear()
                print(quest.create_scene_8_victory())
            elif choice == '9':
                print(f"\n{Fore.GREEN + Style.BRIGHT}🎬 Starting Minimalist Animation...{Style.RESET_ALL}")
                quest.animate_all_scenes()
            else:
                print(f"{Fore.RED}Invalid choice! Please select 0-9.{Style.RESET_ALL}")
            
            if choice != '0' and choice != '9':
                input(f"\n{Fore.YELLOW}Press Enter to return to menu...{Style.RESET_ALL}")
                
        except KeyboardInterrupt:
            print(f"\n\n{Fore.CYAN}⚓ Adventure concluded gracefully! ⚓{Style.RESET_ALL}")
            break

if __name__ == "__main__":
    main() 