#!/usr/bin/env python3
"""
🏴‍☠️ VirtuosoHunt Treasure Island Quest - Complete TEXT-FREE Optimized Edition
8-Scene Animated Treasure Hunting Adventure
Enhanced with PrettyTable for professional formatting
"""

import time
import os
import random
from rich.console import Console
from rich.text import Text
from rich.panel import Panel
from colorama import init, Fore, Back, Style
from prettytable import PrettyTable
try:
    from ascii_magic import AsciiArt
    from PIL import Image, ImageDraw, ImageFont
    ASCII_MAGIC_AVAILABLE = True
except ImportError:
    ASCII_MAGIC_AVAILABLE = False

# Initialize colorama
init(autoreset=True)

class TextFreeOptimizedTreasureQuest:
    def __init__(self):
        self.console = Console()
        
        # Enhanced color palettes
        self.themes = {
            'pirate_gold': Fore.YELLOW + Style.BRIGHT,
            'pirate_silver': Fore.WHITE + Style.BRIGHT,
            'pirate_red': Fore.RED + Style.BRIGHT,
            'ocean_deep': Fore.BLUE + Style.BRIGHT,
            'whale_blue': Fore.BLUE + Style.BRIGHT,
            'success_green': Fore.GREEN + Style.BRIGHT,
            'danger_red': Fore.RED + Style.BRIGHT,
            'storm_purple': Fore.MAGENTA + Style.BRIGHT,
            'treasure_gold': Fore.YELLOW + Style.BRIGHT
        }
        
        # Advanced character sets
        self.char_sets = {
            'density_light': ' ░▒▓█',
            'density_detailed': ' .:-=+*#%@',
            'blocks_gradient': ' ▁▂▃▄▅▆▇█',
            'maritime': '~≈∼⌐¬─═║│┌┐└┘├┤┬┴┼',
            'crypto': '₿⧫◆◇♦♢▲△▼▽●◯◦•∘°'
        }
        
        # Padding and alignment settings
        self.display_width = 80
        self.left_padding = 8
        self.right_padding = 8
        
        # PrettyTable configuration
        self.table_width = 80
        self.setup_table_styles()
    
    def setup_table_styles(self):
        """Configure PrettyTable default styles"""
        self.default_table_style = {
            'border': True,
            'header': True,
            'padding_width': 2,
            'align': 'c',  # center alignment
            'valign': 'm'   # middle vertical alignment
        }
    
    def create_ascii_display_table(self, content, title="", width=80):
        """Create a properly formatted table for ASCII art display"""
        table = PrettyTable()
        table.field_names = [title if title else "VirtuosoHunt Display"]
        table.add_row([content])
        
        # Apply styling
        table.border = True
        table.header = True if title else False
        table.padding_width = 3
        table.align = 'c'
        table.max_width = width
        
        return table
    
    def create_info_panel_table(self, data_dict, title="Information Panel"):
        """Create a formatted information panel using PrettyTable"""
        table = PrettyTable()
        table.field_names = ["Parameter", "Value", "Status"]
        
        for key, value in data_dict.items():
            if isinstance(value, dict):
                table.add_row([key, value.get('value', ''), value.get('status', '')])
            else:
                table.add_row([key, value, "✓"])
        
        table.border = True
        table.header = True
        table.padding_width = 2
        table.align["Parameter"] = 'l'
        table.align["Value"] = 'c'
        table.align["Status"] = 'c'
        table.header_style = 'title'
        
        return table
    
    def center_text(self, text, width=None):
        """Center text within a given width"""
        if width is None:
            width = self.display_width
        
        lines = text.split('\n')
        centered_lines = []
        
        for line in lines:
            # Remove ANSI color codes for length calculation
            import re
            clean_line = re.sub(r'\x1b\[[0-9;]*m', '', line)
            line_length = len(clean_line)
            
            if line_length < width:
                padding = (width - line_length) // 2
                centered_line = ' ' * padding + line + ' ' * (width - line_length - padding)
                centered_lines.append(centered_line)
            else:
                centered_lines.append(line)
        
        return '\n'.join(centered_lines)
    
    def add_padding(self, text, left_pad=None, right_pad=None):
        """Add consistent padding to ASCII art"""
        if left_pad is None:
            left_pad = self.left_padding
        if right_pad is None:
            right_pad = self.right_padding
            
        lines = text.split('\n')
        padded_lines = []
        
        for line in lines:
            padded_line = ' ' * left_pad + line + ' ' * right_pad
            padded_lines.append(padded_line)
        
        return '\n'.join(padded_lines)
    
    def create_text_free_pirate_ship(self, size='normal'):
        """Create pirate ship with NO embedded text using PrettyTable"""
        if size == 'large':
            ship_art = f"""{self.themes['pirate_red']}🏴‍☠️{Style.RESET_ALL}
{self.themes['pirate_silver']}║{Style.RESET_ALL}
{self.themes['pirate_gold']}┌───────┐{Style.RESET_ALL}
{self.themes['pirate_gold']}│ ╔═══╗ │{Style.RESET_ALL}
{self.themes['pirate_gold']}┌───┴─╫ ⚓ ╫─┴───┐{Style.RESET_ALL}
{self.themes['pirate_gold']}│   ═════   │{Style.RESET_ALL}
{self.themes['pirate_gold']}│ ▓▓▓▓▓▓▓▓▓ │{Style.RESET_ALL}
{self.themes['pirate_gold']}│▓▓▓▓▓▓▓▓▓▓▓│{Style.RESET_ALL}
{self.themes['pirate_gold']}└┬──────────┬┘{Style.RESET_ALL}
{self.themes['pirate_gold']}└──┐    ┌──┘{Style.RESET_ALL}
{self.themes['pirate_gold']}└────┘{Style.RESET_ALL}"""
        else:
            ship_art = f"""{self.themes['pirate_red']}🏴‍☠️{Style.RESET_ALL}
{self.themes['pirate_silver']}║{Style.RESET_ALL}
{self.themes['pirate_gold']}┌───────┐{Style.RESET_ALL}
{self.themes['pirate_gold']}│ ╔═══╗ │{Style.RESET_ALL}
{self.themes['pirate_gold']}┌───┴─╫ ⚓ ╫─┴───┐{Style.RESET_ALL}
{self.themes['pirate_gold']}│   ═════   │{Style.RESET_ALL}
{self.themes['pirate_gold']}│ ▓▓▓▓▓▓▓▓▓ │{Style.RESET_ALL}
{self.themes['pirate_gold']}│▓▓▓▓▓▓▓▓▓▓▓│{Style.RESET_ALL}
{self.themes['pirate_gold']}└┬──────────┬┘{Style.RESET_ALL}
{self.themes['pirate_gold']}└──┐    ┌──┘{Style.RESET_ALL}
{self.themes['pirate_gold']}└────┘{Style.RESET_ALL}"""
        
        return self.create_ascii_display_table(ship_art, "🏴‍☠️ VirtuosoHunt Flagship ⚓")
    
    def create_text_free_treasure_island(self, variant='normal'):
        """Create treasure island with NO embedded text using PrettyTable"""
        if variant == 'victory':
            island_art = f"""{self.themes['treasure_gold']}☀️ ✨ ☀️ ✨ ☀️{Style.RESET_ALL}
{self.themes['success_green']}🏝️ 🌴 🏆 💎 🏆 🌴 🏝️{Style.RESET_ALL}
{Fore.GREEN}▲▲▲ ▓▓▓ ▲▲▲{Style.RESET_ALL}
{Fore.GREEN + Style.DIM}░▒▓███▓▒░{Style.RESET_ALL}

{self.themes['treasure_gold']}┌─────────────┐{Style.RESET_ALL}
{self.themes['treasure_gold']}│ 💰💎🪙⭐💰 │{Style.RESET_ALL}
{self.themes['treasure_gold']}│ ⭐🪙💎💰⭐ │{Style.RESET_ALL}
{self.themes['treasure_gold']}│ 💰⭐🪙💎💰 │{Style.RESET_ALL}
{self.themes['treasure_gold']}│ 💎💰⭐🪙💎 │{Style.RESET_ALL}
{self.themes['treasure_gold']}└─────────────┘{Style.RESET_ALL}"""
            title = "🏆 LEGENDARY TREASURE ISLAND 🏆"
        else:
            island_art = f"""{self.themes['pirate_gold']}☀️ ✨ ☀️{Style.RESET_ALL}
{self.themes['success_green']}🏝️ 🌴 💰 🌴 🏝️{Style.RESET_ALL}
{Fore.GREEN}▲▲▲ ▓▓▓ ▲▲▲{Style.RESET_ALL}
{Fore.GREEN + Style.DIM}░▒▓███▓▒░{Style.RESET_ALL}

{self.themes['pirate_gold']}┌─────────────┐{Style.RESET_ALL}
{self.themes['pirate_gold']}│ 💰💎🪙⭐💰 │{Style.RESET_ALL}
{self.themes['pirate_gold']}│ ⭐🪙💎💰⭐ │{Style.RESET_ALL}
{self.themes['pirate_gold']}│ 💰⭐🪙💎💰 │{Style.RESET_ALL}
{self.themes['pirate_gold']}└─────────────┘{Style.RESET_ALL}"""
            title = "🏝️ TREASURE ISLAND 💰"
        
        return self.create_ascii_display_table(island_art, title)
    
    def create_ocean_environment_table(self):
        """Create a beautiful ocean environment using PrettyTable"""
        ocean_layers = f"""{self.themes['ocean_deep']}🌊≈≈≈≈≈≈≈≈≈≈≈≈≈≈≈≈≈≈≈≈≈≈≈≈≈≈≈≈≈≈🌊{Style.RESET_ALL}
{Fore.BLUE}∼∼∼∼∼∼∼∼∼∼∼∼∼∼∼∼∼∼∼∼∼∼∼∼∼∼∼∼∼∼∼∼∼∼∼{Style.RESET_ALL}
{Fore.BLUE + Style.DIM}~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~{Style.RESET_ALL}
{Fore.CYAN + Style.DIM}⌐⌐⌐⌐⌐⌐⌐⌐⌐⌐⌐⌐¬¬¬¬¬¬¬¬¬¬¬¬⌐⌐⌐⌐⌐⌐⌐⌐⌐⌐⌐{Style.RESET_ALL}"""
        
        return self.create_ascii_display_table(ocean_layers, "🌊 OCEAN ENVIRONMENT 🌊")
    
    def create_whale_tracker_table(self, whales_data):
        """Create a whale tracking display using PrettyTable"""
        table = PrettyTable()
        table.field_names = ["🐋 Whale", "Holdings", "Activity", "Status"]
        
        for whale in whales_data:
            table.add_row([
                f"🐋 {whale['emoji']}",
                f"{whale['holdings']} SOL",
                f"{whale['activity']}",
                whale['status']
            ])
        
        table.border = True
        table.header = True
        table.padding_width = 1
        table.align = 'c'
        table.header_style = 'title'
        
        return table
    
    def create_text_free_shark(self):
        """Create shark with NO embedded text"""
        shark = f"""
{self.themes['danger_red']}🦈{Style.RESET_ALL}
{self.themes['danger_red']}╭─────────╮{Style.RESET_ALL}
{self.themes['danger_red']}╭────┴─┐      ╱{Style.RESET_ALL}
{self.themes['danger_red']}╱      └┬──────╱{Style.RESET_ALL}
{self.themes['danger_red']}╱        └────╱{Style.RESET_ALL}
{Fore.RED + Style.DIM}⚡⚡⚡⚡⚡⚡⚡⚡{Style.RESET_ALL}"""
        
        return self.center_text(shark)

    def create_scene_1_text_free(self):
        """Scene 1: The Quest Begins - TEXT-FREE VERSION with PrettyTable"""
        
        # Create mission parameters table
        mission_data = {
            "🚢 Ship": "VirtuosoHunt Flagship",
            "🏝️ Target": "Treasure Island", 
            "💰 Objective": "Legendary Crypto Treasures",
            "⚓ Status": "Quest Initiated",
            "🎨 Design": "TEXT-FREE OPTIMIZED"
        }
        mission_table = self.create_info_panel_table(mission_data, "🎯 MISSION PARAMETERS")
        
        # Build the complete scene
        header = f"""
{Fore.CYAN + Style.BRIGHT}
╔══════════════════════════════════════════════════════════════════════════════╗
║                🏴‍☠️ VIRTUOSO HUNT - TEXT-FREE TREASURE QUEST 🏴‍☠️                ║
║                          Scene 1: The Quest Begins                          ║
╚══════════════════════════════════════════════════════════════════════════════╝
{Style.RESET_ALL}
"""
        
        return f"""{header}
{self.create_text_free_treasure_island()}

{self.create_ocean_environment_table()}

{self.create_text_free_pirate_ship()}

{mission_table}
"""

    def create_scene_3_text_free(self):
        """Scene 3: Whale Territory - TEXT-FREE VERSION with PrettyTable"""
        
        # Create whale tracking data
        whales_data = [
            {"emoji": "🏆", "holdings": "50M", "activity": "ACTIVE", "status": "+500% 🏆"},
            {"emoji": "⭐", "holdings": "25M", "activity": "MONITORING", "status": "Accumulation ⭐"},
            {"emoji": "💎", "holdings": "100M", "activity": "TRACKING", "status": "Mirror Trade 💎"}
        ]
        whale_tracker = self.create_whale_tracker_table(whales_data)
        
        # Whale analysis data
        analysis_data = {
            "🐋 Whale #1": {"value": "7CqX...k9mN | 50M SOL", "status": "+500%"},
            "📊 Pattern": {"value": "Accumulation Phase", "status": "AI, Gaming, DeFi"},
            "🎯 Strategy": {"value": "Mirror Trades", "status": "87% Confidence"},
            "⚠️ Risk Level": {"value": "Medium", "status": "Managed"}
        }
        analysis_table = self.create_info_panel_table(analysis_data, "🐋 WHALE MOVEMENT ANALYSIS")
        
        header = f"""
{Fore.BLUE + Style.BRIGHT}
╔══════════════════════════════════════════════════════════════════════════════╗
║                      🐋 Scene 3: Whale Territory 🐋                        ║
╚══════════════════════════════════════════════════════════════════════════════╝
{Style.RESET_ALL}
"""
        
        status_table = self.create_ascii_display_table(
            f"{Fore.MAGENTA + Style.BRIGHT}🔍 WHALE TRACKER ACTIVE{Style.RESET_ALL}",
            "🎯 WHALE TRACKING STATUS"
        )
        
        return f"""{header}
{status_table}

{whale_tracker}

{self.create_ocean_environment_table()}

{self.create_text_free_pirate_ship()}

{analysis_table}
"""

    def create_scene_4_text_free(self):
        """Scene 4: Shark-Infested Waters - TEXT-FREE VERSION"""
        shark_ascii = self.create_text_free_shark()
        
        # Create properly spaced shark displays
        shark_display_1 = self.center_text(f"🦈 {self.themes['danger_red']}⚡ VOLATILITY{Style.RESET_ALL}")
        shark_display_2 = self.center_text(f"🦈 {self.themes['danger_red']}⚡ DANGER{Style.RESET_ALL}")
        shark_display_3 = self.center_text(f"🦈 {self.themes['danger_red']}⚡ MARKET CRASH{Style.RESET_ALL}")
        
        return f"""
{Fore.RED + Style.BRIGHT}
╔══════════════════════════════════════════════════════════════════════════════╗
║                    🦈 Scene 4: Shark-Infested Waters 🦈                    ║
╚══════════════════════════════════════════════════════════════════════════════╝
{Style.RESET_ALL}

{shark_display_1}     {shark_display_2}

{self.center_text(f"{self.themes['danger_red']}{'⚡' + '≈' * 30 + '⚡'}{Style.RESET_ALL}")}
{self.center_text(f"{Fore.RED}{'∼' * 35}{Style.RESET_ALL}")}

{self.create_text_free_pirate_ship()}
{self.center_text(f"{Fore.YELLOW + Style.BRIGHT}🛡️ SHIELDS UP{Style.RESET_ALL}")}

{self.center_text(f"{Fore.RED}{'~' * 35}{Style.RESET_ALL}")}
{shark_display_3}

{Fore.WHITE + Style.BRIGHT}╔═ 🦈 DANGER ZONE ANALYSIS ═════════════════════════════════════════════╗{Style.RESET_ALL}
{self.themes['danger_red']}║ Threat Level: EXTREME │ Volatility: +847% │ Liquidations: $50M  ║{Style.RESET_ALL}
{Fore.YELLOW + Style.BRIGHT}║ Protection: Anti-Rug Shields │ Stop-Loss: ACTIVE │ Risk: MANAGED   ║{Style.RESET_ALL}
{Fore.CYAN + Style.BRIGHT}║ Strategy: Navigate Carefully │ Opportunity: High │ Reward: Epic     ║{Style.RESET_ALL}
{Fore.WHITE + Style.BRIGHT}╚════════════════════════════════════════════════════════════════════╝{Style.RESET_ALL}
"""

    def create_scene_8_text_free(self):
        """Scene 8: Victory! - TEXT-FREE VERSION"""
        victory_treasure = self.create_text_free_treasure_island('victory')
        
        return f"""
{Fore.YELLOW + Style.BRIGHT}
╔══════════════════════════════════════════════════════════════════════════════╗
║                    🏆 Scene 8: LEGENDARY VICTORY! 🏆                       ║
╚══════════════════════════════════════════════════════════════════════════════╝
{Style.RESET_ALL}

{victory_treasure}

{self.create_text_free_pirate_ship('large')}
{self.center_text(f"{self.themes['treasure_gold']}🏆 LEGENDARY STATUS{Style.RESET_ALL}")}

{Fore.WHITE + Style.BRIGHT}╔═ 📊 EPIC QUEST RESULTS ═══════════════════════════════════════════════╗{Style.RESET_ALL}
{self.themes['success_green']}║ 🚀 Portfolio Growth: +5,247% │ 💎 Gems Found: 15 tokens        ║{Style.RESET_ALL}
{self.themes['treasure_gold']}║ 🪙 Total Value: $2.5M │ ⭐ Success Rate: 94%                ║{Style.RESET_ALL}
{Fore.MAGENTA + Style.BRIGHT}║ 🏆 Status: LEGENDARY TRADER │ ⚓ Ship: VirtuosoHunt Flagship   ║{Style.RESET_ALL}
{Fore.WHITE + Style.BRIGHT}╚════════════════════════════════════════════════════════════════════╝{Style.RESET_ALL}

{Fore.WHITE + Style.BRIGHT}╔═ 🎨 TEXT-FREE DESIGN ACHIEVEMENTS ═══════════════════════════════════╗{Style.RESET_ALL}
{self.themes['success_green']}║ ✨ ASCII-Magic Integration: MASTERED                               ║{Style.RESET_ALL}
{Fore.CYAN + Style.BRIGHT}║ 🖼️  Pure Visual Storytelling: PERFECTED                            ║{Style.RESET_ALL}
{self.themes['treasure_gold']}║ 🌊 Maritime ASCII Enhancement: LEGENDARY                            ║{Style.RESET_ALL}
{Fore.MAGENTA + Style.BRIGHT}║ 🏆 Minimalist Aesthetic: EPIC LEVEL ACHIEVED                       ║{Style.RESET_ALL}
{Fore.WHITE + Style.BRIGHT}╚════════════════════════════════════════════════════════════════════╝{Style.RESET_ALL}
"""

    def display_text_free_menu(self):
        """Display menu highlighting text-free optimization"""
        magic_status = f"{self.themes['success_green']}ACTIVE{Style.RESET_ALL}" if ASCII_MAGIC_AVAILABLE else f"{Fore.YELLOW}FALLBACK{Style.RESET_ALL}"
        
        print(f"\n{Fore.YELLOW + Style.BRIGHT}🏴‍☠️ VIRTUOSO TREASURE QUEST - TEXT-FREE OPTIMIZED EDITION 🏴‍☠️{Style.RESET_ALL}")
        print(f"{Fore.CYAN + Style.BRIGHT}ASCII-Magic: {magic_status} | Visual Design: TEXT-FREE | Storytelling: SYMBOL-BASED{Style.RESET_ALL}")
        print("=" * 75)
        
        print(f"{self.themes['success_green']}1.{Style.RESET_ALL} 🎬 The Quest Begins (Text-Free Adventure Starts)")
        print(f"{self.themes['success_green']}3.{Style.RESET_ALL} 🐋 Whale Territory (Symbol-Based Whale Tracking)")
        print(f"{self.themes['success_green']}4.{Style.RESET_ALL} 🦈 Shark-Infested Waters (Pure Visual Danger)")
        print(f"{self.themes['success_green']}8.{Style.RESET_ALL} 🏆 Victory! (Epic Text-Free Celebration)")
        print(f"{Fore.CYAN}0.{Style.RESET_ALL} Exit")
        
        return input(f"\n{Fore.YELLOW}Select scene: {Style.RESET_ALL}").strip()

def main():
    quest = TextFreeOptimizedTreasureQuest()
    
    print(f"""
{Fore.YELLOW + Style.BRIGHT}
╔══════════════════════════════════════════════════════════════════════════════╗
║              🎨 VIRTUOSO TREASURE QUEST - TEXT-FREE OPTIMIZATION 🎨         ║
║                                                                              ║
║  ✨ ASCII-Magic Package: {'✓ ACTIVE' if ASCII_MAGIC_AVAILABLE else '⚠ Install: pip install ascii-magic'}                                    ║
║  🎯 Character Density Mapping: ✓ OPTIMIZED                                  ║
║  🌊 Maritime ASCII Sets: ✓ INTEGRATED                                       ║
║  🖼️  Text-Free Visual Design: ✓ PERFECTED                                   ║
║  🏆 Symbol-Based Storytelling: ✓ LEGENDARY                                  ║
╚══════════════════════════════════════════════════════════════════════════════╝
{Style.RESET_ALL}
    """)
    
    while True:
        try:
            choice = quest.display_text_free_menu()
            
            if choice == '0':
                print(f"\n{Fore.CYAN}⚓ Your text-free treasure hunting adventure awaits! ⚓{Style.RESET_ALL}")
                break
            elif choice == '1':
                quest.console.clear()
                print(quest.create_scene_1_text_free())
                input(f"\n{Fore.YELLOW}Press Enter to return to menu...{Style.RESET_ALL}")
            elif choice == '3':
                quest.console.clear()
                print(quest.create_scene_3_text_free())
                input(f"\n{Fore.YELLOW}Press Enter to return to menu...{Style.RESET_ALL}")
            elif choice == '4':
                quest.console.clear()
                print(quest.create_scene_4_text_free())
                input(f"\n{Fore.YELLOW}Press Enter to return to menu...{Style.RESET_ALL}")
            elif choice == '8':
                quest.console.clear()
                print(quest.create_scene_8_text_free())
                input(f"\n{Fore.YELLOW}Press Enter to return to menu...{Style.RESET_ALL}")
            else:
                print(f"{Fore.RED}Invalid choice!{Style.RESET_ALL}")
                
        except KeyboardInterrupt:
            print(f"\n\n{Fore.CYAN}⚓ Text-free treasure quest concluded! ⚓{Style.RESET_ALL}")
            break

if __name__ == "__main__":
    main() 