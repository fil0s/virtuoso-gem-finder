#!/usr/bin/env python3
"""
🏴‍☠️ VirtuosoHunt Treasure Island Quest - ASCII Art Scene Generator
Creates animated ASCII art scenes for crypto trading adventure
"""

import time
import random
from rich.console import Console
from rich.text import Text
from rich.panel import Panel
from rich.layout import Layout
from rich.live import Live
from colorama import init, Fore, Back, Style
import os

# Initialize colorama and rich
init(autoreset=True)

class TreasureQuestGenerator:
    def __init__(self):
        self.console = Console()
        self.scenes = {}
        self.initialize_scenes()
    
    def initialize_scenes(self):
        """Initialize all 8 scenes for the treasure quest"""
        self.scenes = {
            1: "The Quest Begins (Establishing Shot)",
            2: "Navigating Dangerous Waters",
            3: "Whale Territory Encounter", 
            4: "Shark-Infested Market Volatility",
            5: "Storm of Market Uncertainty",
            6: "Approaching Treasure Island",
            7: "Landing and Token Discovery",
            8: "Victory - Treasure Secured"
        }
    
    def create_scene_1_establishing_shot(self):
        """Scene 1: The Quest Begins - Wide establishing shot"""
        scene = f"""
{Fore.CYAN + Style.BRIGHT}
╔═══════════════════════════════════════════════════════════════════════════════╗
║                    🏴‍☠️ VIRTUOSO HUNT - TREASURE ISLAND QUEST 🏴‍☠️                    ║
║                            🏝️ TREASURE ISLAND AHEAD! 🏝️                            ║
╚═══════════════════════════════════════════════════════════════════════════════╝
{Style.RESET_ALL}

{Fore.YELLOW + Style.BRIGHT}                    ☀️  Golden Hour Sky  ☀️{Style.RESET_ALL}
{Fore.YELLOW}~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~{Style.RESET_ALL}
{Fore.MAGENTA + Style.DIM}                   ⛅ Dramatic Clouds ⛅{Style.RESET_ALL}
{Fore.WHITE + Style.BRIGHT}               🏝️{Fore.GREEN + Style.BRIGHT}🌴 TREASURE ISLAND 🌴{Fore.WHITE + Style.BRIGHT}🏝️{Style.RESET_ALL}
{Fore.BLUE + Style.DIM}═══════════════════════════════════════════════════════════════════{Style.RESET_ALL}
{Fore.BLUE + Style.BRIGHT}~~~~~~~~~~~~~~~~~~ VAST CRYPTO OCEAN ~~~~~~~~~~~~~~~~~~{Style.RESET_ALL}
{Fore.BLUE}~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~{Style.RESET_ALL}
{Fore.BLUE + Style.DIM}~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~{Style.RESET_ALL}

                            {Fore.BLACK + Style.BRIGHT}⚓ VIRTUOSO SHIP ⚓{Style.RESET_ALL}
                                {Fore.RED + Style.BRIGHT}🏴‍☠️{Style.RESET_ALL}
                             {Fore.WHITE + Style.BRIGHT}   ║{Style.RESET_ALL}
                         {Fore.YELLOW + Style.BRIGHT}    ╔═══╗{Style.RESET_ALL}
                         {Fore.YELLOW}    ║ V ║{Style.RESET_ALL}  {Fore.RED + Style.DIM}← Algorithm Engine{Style.RESET_ALL}
                                                   {Fore.YELLOW + Style.DIM}╔═══════════════╗{Style.RESET_ALL}
                          {Fore.BLACK + Style.BRIGHT}║   VIRTUOSO    ║{Style.RESET_ALL}
                          {Fore.BLACK + Style.BRIGHT}║  ⚓ HUNTER ⚓  ║{Style.RESET_ALL}
                          {Fore.YELLOW + Style.DIM}╚═══════════════╝{Style.RESET_ALL}
{Fore.BLUE + Style.BRIGHT}~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~{Style.RESET_ALL}
{Fore.BLUE}~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~{Style.RESET_ALL}

{Fore.GREEN + Style.BRIGHT}💰 MISSION: Navigate dangerous crypto waters to reach treasure island
🎯 TARGET: Discover profitable tokens before other hunters
⚔️  HAZARDS: Whales, sharks, and market volatility ahead!{Style.RESET_ALL}
"""
        return scene
    
    def create_scene_2_dangerous_waters(self):
        """Scene 2: Navigating Dangerous Waters"""
        scene = f"""
{Fore.RED + Style.BRIGHT}
╔══════════════════════════════════════════════════════════════════════════════╗
║                    ⚠️  ENTERING DANGEROUS TRADING WATERS ⚠️                    ║
║                        🌊 HIGH VOLATILITY ZONE AHEAD 🌊                        ║
╚══════════════════════════════════════════════════════════════════════════════╝
{Style.RESET_ALL}

{Fore.RED + Style.DIM}                    ⛈️  Storm Clouds Gathering  ⛈️{Style.RESET_ALL}
{Fore.BLACK + Style.BRIGHT}~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~{Style.RESET_ALL}
{Fore.BLUE + Style.BRIGHT}🌊~~~~~~~~~~~~~~~~ TURBULENT WATERS ~~~~~~~~~~~~~~~~🌊{Style.RESET_ALL}
{Fore.BLUE}~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~{Style.RESET_ALL}
{Fore.BLUE + Style.DIM}~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~{Style.RESET_ALL}

                    {Fore.RED + Style.BRIGHT}⚠️ MARKET VOLATILITY DETECTED ⚠️{Style.RESET_ALL}
                            {Fore.BLACK + Style.BRIGHT}🏴‍☠️ VIRTUOSO{Style.RESET_ALL}
                             {Fore.WHITE + Style.BRIGHT}   ║{Style.RESET_ALL}
                         {Fore.YELLOW + Style.BRIGHT}    ╔═══╗{Style.RESET_ALL}
                         {Fore.YELLOW}    ║ V ║{Style.RESET_ALL}  {Fore.CYAN + Style.DIM}← Scanning Markets{Style.RESET_ALL}
                         {Fore.YELLOW + Style.DIM}╔═══════════════╗{Style.RESET_ALL}
                         {Fore.YELLOW + Style.DIM}║   VIRTUOSO    ║{Style.RESET_ALL}  {Fore.GREEN + Style.DIM}📊 +15% Portfolio{Style.RESET_ALL}
                         {Fore.YELLOW + Style.DIM}║  ⚓ HUNTER ⚓  ║{Style.RESET_ALL}
                         {Fore.YELLOW + Style.DIM}╚═══════════════╝{Style.RESET_ALL}
{Fore.BLUE + Style.BRIGHT}🌊~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~🌊{Style.RESET_ALL}
{Fore.BLUE}~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~{Style.RESET_ALL}

{Fore.YELLOW + Style.BRIGHT}📈 MARKET SIGNALS:
   📊 Volume Spike Detected: +247%
   🎯 New Token Opportunities: 12 potential gems
   ⚡ Algorithm Status: ACTIVE HUNTING{Style.RESET_ALL}
"""
        return scene
    
    def create_scene_3_whale_encounter(self):
        """Scene 3: Whale Territory Encounter"""
        scene = f"""
{Fore.BLUE + Style.BRIGHT}
╔══════════════════════════════════════════════════════════════════════════════╗
║                      🐋 WHALE TERRITORY DETECTED 🐋                          ║
║                   ⚠️ MASSIVE MARKET MOVEMENTS AHEAD ⚠️                        ║
╚══════════════════════════════════════════════════════════════════════════════╝
{Style.RESET_ALL}

{Fore.BLUE + Style.BRIGHT}~~~~~~~~~~~~~~~~ DEEP WHALE WATERS ~~~~~~~~~~~~~~~~{Style.RESET_ALL}
{Fore.BLUE}~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~{Style.RESET_ALL}

    {Fore.BLUE + Style.BRIGHT}🐋{Style.RESET_ALL}                                      {Fore.BLUE + Style.BRIGHT}🐋{Style.RESET_ALL}
          {Fore.BLUE + Style.DIM}Whale #1: 50M SOL{Style.RESET_ALL}                     {Fore.BLUE + Style.DIM}Whale #2: 25M SOL{Style.RESET_ALL}
{Fore.BLUE}~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~{Style.RESET_ALL}
                            {Fore.BLACK + Style.BRIGHT}🏴‍☠️ VIRTUOSO{Style.RESET_ALL}
                             {Fore.WHITE + Style.BRIGHT}   ║{Style.RESET_ALL}
                         {Fore.YELLOW + Style.BRIGHT}    ╔═══╗{Style.RESET_ALL}
                         {Fore.YELLOW}    ║ V ║{Style.RESET_ALL}  {Fore.MAGENTA + Style.DIM}← Whale Detection ON{Style.RESET_ALL}
                         {Fore.YELLOW + Style.DIM}╔═══════════════╗{Style.RESET_ALL}
                         {Fore.YELLOW + Style.DIM}║   VIRTUOSO    ║{Style.RESET_ALL}  {Fore.RED + Style.DIM}🚨 Following Whales{Style.RESET_ALL}
                         {Fore.YELLOW + Style.DIM}║  ⚓ HUNTER ⚓  ║{Style.RESET_ALL}
                         {Fore.YELLOW + Style.DIM}╚═══════════════╝{Style.RESET_ALL}
{Fore.BLUE}~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~{Style.RESET_ALL}
                    {Fore.BLUE + Style.BRIGHT}🐋{Style.RESET_ALL}                     
                          {Fore.BLUE + Style.DIM}Whale #3: 100M SOL{Style.RESET_ALL}
{Fore.BLUE + Style.BRIGHT}~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~{Style.RESET_ALL}

{Fore.CYAN + Style.BRIGHT}🐋 WHALE ACTIVITY DETECTED:
   💰 Whale Wallet: 7CqX...k9mN (50M SOL)
   📊 Recent Activity: +500% token accumulation
   🎯 Target Tokens: Following whale movements
   ⚡ Strategy: Mirror successful whale trades{Style.RESET_ALL}
"""
        return scene
    
    def create_scene_4_shark_volatility(self):
        """Scene 4: Shark-Infested Market Volatility"""
        scene = f"""
{Fore.RED + Style.BRIGHT}
╔══════════════════════════════════════════════════════════════════════════════╗
║                    🦈 SHARK-INFESTED WATERS 🦈                               ║
║                  ⚡ EXTREME MARKET VOLATILITY ⚡                              ║
╚══════════════════════════════════════════════════════════════════════════════╝
{Style.RESET_ALL}

{Fore.RED + Style.BRIGHT}~~~~~~~~~~~~~~~~ DANGER ZONE ~~~~~~~~~~~~~~~~{Style.RESET_ALL}
    {Fore.RED + Style.BRIGHT}🦈{Style.RESET_ALL}         {Fore.RED + Style.BRIGHT}🦈{Style.RESET_ALL}         {Fore.RED + Style.BRIGHT}🦈{Style.RESET_ALL}
{Fore.RED + Style.DIM}     Rug Pull      Flash Crash    Pump & Dump{Style.RESET_ALL}
{Fore.BLUE + Style.BRIGHT}~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~{Style.RESET_ALL}
        {Fore.RED + Style.BRIGHT}🦈{Style.RESET_ALL}                            {Fore.RED + Style.BRIGHT}🦈{Style.RESET_ALL}
                            {Fore.BLACK + Style.BRIGHT}🏴‍☠️ VIRTUOSO{Style.RESET_ALL}
                             {Fore.WHITE + Style.BRIGHT}   ║{Style.RESET_ALL}
                         {Fore.YELLOW + Style.BRIGHT}    ╔═══╗{Style.RESET_ALL}
                         {Fore.YELLOW}    ║ V ║{Style.RESET_ALL}  {Fore.RED + Style.BRIGHT}← RISK MANAGEMENT ON{Style.RESET_ALL}
                         {Fore.YELLOW + Style.DIM}╔═══════════════╗{Style.RESET_ALL}
                         {Fore.YELLOW + Style.DIM}║   VIRTUOSO    ║{Style.RESET_ALL}  {Fore.GREEN + Style.DIM}🛡️ Protected Portfolio{Style.RESET_ALL}
                         {Fore.YELLOW + Style.DIM}║  ⚓ HUNTER ⚓  ║{Style.RESET_ALL}
                         {Fore.YELLOW + Style.DIM}╚═══════════════╝{Style.RESET_ALL}
{Fore.BLUE + Style.BRIGHT}~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~{Style.RESET_ALL}
   {Fore.RED + Style.BRIGHT}🦈{Style.RESET_ALL}                                   {Fore.RED + Style.BRIGHT}🦈{Style.RESET_ALL}
{Fore.RED + Style.DIM}  Scam Token                              Honey Pot{Style.RESET_ALL}

{Fore.YELLOW + Style.BRIGHT}🛡️ PROTECTION SYSTEMS ACTIVE:
   ✅ Rug Pull Detection: ENABLED
   ✅ Liquidity Analysis: SCANNING
   ✅ Smart Contract Audit: VERIFIED
   ✅ Stop Loss Orders: READY{Style.RESET_ALL}
"""
        return scene
    
    def create_scene_5_market_storm(self):
        """Scene 5: Storm of Market Uncertainty"""
        scene = f"""
{Fore.WHITE + Style.BRIGHT}
╔══════════════════════════════════════════════════════════════════════════════╗
║                    ⛈️  MARKET STORM APPROACHING ⛈️                           ║
║                      🌪️ EXTREME UNCERTAINTY 🌪️                              ║
╚══════════════════════════════════════════════════════════════════════════════╝
{Style.RESET_ALL}

{Fore.WHITE + Style.BRIGHT}        ⚡    ⛈️     ⚡     ⛈️     ⚡{Style.RESET_ALL}
{Fore.BLACK + Style.BRIGHT}████████████████████████████████████████████████████████████{Style.RESET_ALL}
{Fore.WHITE + Style.DIM}~~~~~~~~~~~~~~~~ MARKET CHAOS ~~~~~~~~~~~~~~~~{Style.RESET_ALL}
{Fore.BLUE + Style.BRIGHT}🌊~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~🌊{Style.RESET_ALL}
                            {Fore.BLACK + Style.BRIGHT}🏴‍☠️ VIRTUOSO{Style.RESET_ALL}
                             {Fore.WHITE + Style.BRIGHT}   ║{Style.RESET_ALL}
                         {Fore.YELLOW + Style.BRIGHT}    ╔═══╗{Style.RESET_ALL}
                         {Fore.YELLOW}    ║ V ║{Style.RESET_ALL}  {Fore.CYAN + Style.BRIGHT}← WEATHERING STORM{Style.RESET_ALL}
                         {Fore.YELLOW + Style.DIM}╔═══════════════╗{Style.RESET_ALL}
                         {Fore.YELLOW + Style.DIM}║   VIRTUOSO    ║{Style.RESET_ALL}  {Fore.YELLOW + Style.DIM}⚓ Staying Course{Style.RESET_ALL}
                         {Fore.YELLOW + Style.DIM}║  ⚓ HUNTER ⚓  ║{Style.RESET_ALL}
                         {Fore.YELLOW + Style.DIM}╚═══════════════╝{Style.RESET_ALL}
{Fore.BLUE + Style.BRIGHT}🌊~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~🌊{Style.RESET_ALL}
{Fore.WHITE + Style.BRIGHT}        ⚡    ⛈️     ⚡     ⛈️     ⚡{Style.RESET_ALL}

{Fore.RED + Style.BRIGHT}📊 MARKET CONDITIONS:
   📉 Volatility Index: EXTREME (95%)
   💔 Fear & Greed: 15 (Extreme Fear)
   🎯 Opportunity Score: HIGH (Contrarian Signal)
   ⚓ Strategy: HOLD STEADY - Storm will pass{Style.RESET_ALL}
"""
        return scene
    
    def create_scene_6_approaching_island(self):
        """Scene 6: Approaching Treasure Island"""
        scene = f"""
{Fore.GREEN + Style.BRIGHT}
╔══════════════════════════════════════════════════════════════════════════════╗
║                   🏝️ TREASURE ISLAND IN SIGHT! 🏝️                           ║
║                     💰 PROFITABLE TOKENS DETECTED 💰                         ║
╚══════════════════════════════════════════════════════════════════════════════╝
{Style.RESET_ALL}

{Fore.YELLOW + Style.BRIGHT}                    ☀️ Clear Skies Ahead ☀️{Style.RESET_ALL}
{Fore.GREEN + Style.BRIGHT}               🏝️🌴 TREASURE ISLAND 🌴🏝️{Style.RESET_ALL}
{Fore.GREEN}                    ╔═══════════════╗{Style.RESET_ALL}
{Fore.GREEN}                    ║  💰 GEMS 💰   ║{Style.RESET_ALL}
{Fore.GREEN}                    ║ 🪙 TOKENS 🪙  ║{Style.RESET_ALL}
{Fore.GREEN}                    ║  💎 RICHES 💎 ║{Style.RESET_ALL}
{Fore.GREEN}                    ╚═══════════════╝{Style.RESET_ALL}
{Fore.BLUE + Style.BRIGHT}~~~~~~~~~~~~~~~~~~ CALM WATERS ~~~~~~~~~~~~~~~~~~{Style.RESET_ALL}
{Fore.BLUE}~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~{Style.RESET_ALL}
                            {Fore.BLACK + Style.BRIGHT}🏴‍☠️ VIRTUOSO{Style.RESET_ALL}
                             {Fore.WHITE + Style.BRIGHT}   ║{Style.RESET_ALL}
                         {Fore.YELLOW + Style.BRIGHT}    ╔═══╗{Style.RESET_ALL}
                         {Fore.YELLOW}    ║ V ║{Style.RESET_ALL}  {Fore.GREEN + Style.BRIGHT}← TARGET ACQUIRED{Style.RESET_ALL}
                         {Fore.YELLOW + Style.DIM}╔═══════════════╗{Style.RESET_ALL}
                         {Fore.YELLOW + Style.DIM}║   VIRTUOSO    ║{Style.RESET_ALL}  {Fore.CYAN + Style.DIM}🎯 Preparing to Land{Style.RESET_ALL}
                         {Fore.YELLOW + Style.DIM}║  ⚓ HUNTER ⚓  ║{Style.RESET_ALL}
                         {Fore.YELLOW + Style.DIM}╚═══════════════╝{Style.RESET_ALL}
{Fore.BLUE + Style.BRIGHT}~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~{Style.RESET_ALL}

{Fore.GREEN + Style.BRIGHT}🎯 TREASURE ISLAND ANALYSIS:
   💰 High-Value Tokens Detected: 7 gems found
   📊 Market Cap Potential: 10-100x growth
   ⚡ Early Entry Opportunity: CONFIRMED
   🏝️ Landing Coordinates: Locked and Loaded{Style.RESET_ALL}
"""
        return scene
    
    def create_scene_7_token_discovery(self):
        """Scene 7: Landing and Token Discovery"""
        scene = f"""
{Fore.YELLOW + Style.BRIGHT}
╔══════════════════════════════════════════════════════════════════════════════╗
║                    ⚓ LANDING SUCCESSFUL! ⚓                                   ║
║                   💎 TOKEN DISCOVERY IN PROGRESS 💎                          ║
╚══════════════════════════════════════════════════════════════════════════════╝
{Style.RESET_ALL}

{Fore.GREEN + Style.BRIGHT}🏝️ TREASURE ISLAND - TOKEN MINING OPERATIONS 🏝️{Style.RESET_ALL}
{Fore.GREEN}                    🌴    🌴    🌴{Style.RESET_ALL}
{Fore.YELLOW + Style.BRIGHT}               💰 TREASURE CHEST OPENED 💰{Style.RESET_ALL}
{Fore.YELLOW}                  ╔═══════════════════╗{Style.RESET_ALL}
{Fore.YELLOW}                  ║ 💎 $SOLVAULT 💎   ║  {Fore.GREEN + Style.DIM}+2,347% 🚀{Style.RESET_ALL}
{Fore.YELLOW}                  ║ 🪙 $MOODENG 🪙     ║  {Fore.GREEN + Style.DIM}+1,892% 🚀{Style.RESET_ALL}
{Fore.YELLOW}                  ║ 💰 $PNUT 💰       ║  {Fore.GREEN + Style.DIM}+5,672% 🚀{Style.RESET_ALL}
{Fore.YELLOW}                  ║ ⭐ $GOAT ⭐       ║  {Fore.GREEN + Style.DIM}+3,421% 🚀{Style.RESET_ALL}
{Fore.YELLOW}                  ╚═══════════════════╝{Style.RESET_ALL}

{Fore.YELLOW + Style.BRIGHT}🏴‍☠️ VIRTUOSO CREW ON SHORE 🏴‍☠️{Style.RESET_ALL}
{Fore.YELLOW + Style.DIM}    ╔═══════════════╗{Style.RESET_ALL}
{Fore.YELLOW + Style.DIM}    ║   VIRTUOSO    ║{Style.RESET_ALL}  {Fore.CYAN + Style.BRIGHT}← ANCHORED SAFELY{Style.RESET_ALL}
{Fore.YELLOW + Style.DIM}    ║  ⚓ HUNTER ⚓  ║{Style.RESET_ALL}
{Fore.YELLOW + Style.DIM}    ╚═══════════════╝{Style.RESET_ALL}

{Fore.CYAN + Style.BRIGHT}⚡ DISCOVERY STATUS:
   ✅ 7 High-Value Tokens Found
   ✅ Smart Contracts Verified  
   ✅ Liquidity Pools Confirmed
   ✅ Early Entry Positions Secured{Style.RESET_ALL}
"""
        return scene
    
    def create_scene_8_victory(self):
        """Scene 8: Victory - Treasure Secured"""
        scene = f"""
{Fore.YELLOW + Style.BRIGHT}
╔══════════════════════════════════════════════════════════════════════════════╗
║                        🏆 QUEST COMPLETED! 🏆                                ║
║                     💰 TREASURE SUCCESSFULLY SECURED 💰                      ║
╚══════════════════════════════════════════════════════════════════════════════╝
{Style.RESET_ALL}

{Fore.YELLOW + Style.BRIGHT}                     🎆 VICTORY! 🎆{Style.RESET_ALL}
{Fore.GREEN + Style.BRIGHT}               🏝️ VIRTUOSO TREASURE ISLAND 🏝️{Style.RESET_ALL}
{Fore.GREEN}                      🌴  🏆  🌴{Style.RESET_ALL}

{Fore.YELLOW + Style.BRIGHT}            💰 FINAL TREASURE HAUL 💰{Style.RESET_ALL}
{Fore.YELLOW}          ╔═══════════════════════════════╗{Style.RESET_ALL}
{Fore.YELLOW}          ║  🚀 Portfolio Growth: +5,247% ║{Style.RESET_ALL}
{Fore.YELLOW}          ║  💎 Gems Discovered: 15 tokens║{Style.RESET_ALL}
{Fore.YELLOW}          ║  🪙 Total Value: $2.5M        ║{Style.RESET_ALL}
{Fore.YELLOW}          ║  ⭐ Success Rate: 94%         ║{Style.RESET_ALL}
{Fore.YELLOW}          ╚═══════════════════════════════╝{Style.RESET_ALL}

{Fore.YELLOW + Style.BRIGHT}🏴‍☠️ VIRTUOSO - LEGENDARY STATUS ACHIEVED 🏴‍☠️{Style.RESET_ALL}
{Fore.YELLOW + Style.DIM}    ╔═══════════════╗{Style.RESET_ALL}
{Fore.YELLOW + Style.DIM}    ║   VIRTUOSO    ║{Style.RESET_ALL}  {Fore.YELLOW + Style.BRIGHT}← TREASURE MASTER{Style.RESET_ALL}
{Fore.YELLOW + Style.DIM}    ║  ⚓ HUNTER ⚓  ║{Style.RESET_ALL}
{Fore.YELLOW + Style.DIM}    ╚═══════════════╝{Style.RESET_ALL}

{Fore.GREEN + Style.BRIGHT}🎯 MISSION ACCOMPLISHED:
   🏆 Legendary Trader Status: UNLOCKED
   💰 Treasure Island Conquered: COMPLETE
   🚀 Next Adventure: New horizons await...
   ⚓ The VirtuosoHunt continues!{Style.RESET_ALL}
"""
        return scene
    
    def animate_all_scenes(self, duration_per_scene=3):
        """Animate through all 8 scenes"""
        scenes = [
            self.create_scene_1_establishing_shot(),
            self.create_scene_2_dangerous_waters(),
            self.create_scene_3_whale_encounter(),
            self.create_scene_4_shark_volatility(),
            self.create_scene_5_market_storm(),
            self.create_scene_6_approaching_island(),
            self.create_scene_7_token_discovery(),
            self.create_scene_8_victory()
        ]
        
        for i, scene in enumerate(scenes, 1):
            self.console.clear()
            print(f"\n{Fore.CYAN + Style.BRIGHT}━━━ SCENE {i}/8: {self.scenes[i]} ━━━{Style.RESET_ALL}")
            print(scene)
            time.sleep(duration_per_scene)
    
    def display_scene_menu(self):
        """Display interactive scene selection menu"""
        print(f"\n{Fore.YELLOW + Style.BRIGHT}🏴‍☠️ VIRTUOSO TREASURE QUEST - SCENE SELECTOR 🏴‍☠️{Style.RESET_ALL}")
        print("=" * 60)
        
        for i, title in self.scenes.items():
            print(f"{Fore.CYAN}{i}.{Style.RESET_ALL} {title}")
        
        print(f"{Fore.GREEN}9.{Style.RESET_ALL} Play Full Animation (All Scenes)")
        print(f"{Fore.RED}0.{Style.RESET_ALL} Exit")
        
        return input(f"\n{Fore.YELLOW}Select scene (0-9): {Style.RESET_ALL}").strip()

def main():
    quest = TreasureQuestGenerator()
    
    print(f"""
{Fore.YELLOW + Style.BRIGHT}
╔═══════════════════════════════════════════════════════════════════════════════╗
║              🏴‍☠️ VIRTUOSO TREASURE ISLAND QUEST GENERATOR 🏴‍☠️               ║
║                     Visual Story for Crypto Token Discovery                   ║
╚═══════════════════════════════════════════════════════════════════════════════╝
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
                print(quest.create_scene_1_establishing_shot())
            elif choice == '2':
                quest.console.clear()
                print(quest.create_scene_2_dangerous_waters())
            elif choice == '3':
                quest.console.clear()
                print(quest.create_scene_3_whale_encounter())
            elif choice == '4':
                quest.console.clear()
                print(quest.create_scene_4_shark_volatility())
            elif choice == '5':
                quest.console.clear()
                print(quest.create_scene_5_market_storm())
            elif choice == '6':
                quest.console.clear()
                print(quest.create_scene_6_approaching_island())
            elif choice == '7':
                quest.console.clear()
                print(quest.create_scene_7_token_discovery())
            elif choice == '8':
                quest.console.clear()
                print(quest.create_scene_8_victory())
            elif choice == '9':
                print(f"\n{Fore.GREEN + Style.BRIGHT}🎬 Starting Full Animation...{Style.RESET_ALL}")
                quest.animate_all_scenes()
            else:
                print(f"{Fore.RED}Invalid choice! Please select 0-9.{Style.RESET_ALL}")
            
            if choice != '0' and choice != '9':
                input(f"\n{Fore.YELLOW}Press Enter to return to menu...{Style.RESET_ALL}")
                
        except KeyboardInterrupt:
            print(f"\n\n{Fore.CYAN}⚓ Adventure interrupted! ⚓{Style.RESET_ALL}")
            break

if __name__ == "__main__":
    main()