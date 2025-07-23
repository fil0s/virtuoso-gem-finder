#!/usr/bin/env python3
"""
🏴‍☠️ VirtuosoHunt Treasure Island Quest - Scene 1 Demo
Quick demo of the establishing shot scene
"""

from colorama import init, Fore, Back, Style
import time

# Initialize colorama
init(autoreset=True)

def create_scene_1_establishing_shot():
    """Scene 1: The Quest Begins - Wide establishing shot"""
    return f"""
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

def animated_intro():
    """Create an animated intro effect"""
    print(f"{Fore.CYAN + Style.BRIGHT}🏴‍☠️ PREPARING TREASURE QUEST... 🏴‍☠️{Style.RESET_ALL}")
    
    # Animated loading
    loading_chars = ["⚓", "🌊", "🏴‍☠️", "🏝️"]
    for i in range(12):
        char = loading_chars[i % len(loading_chars)]
        print(f"\r{Fore.YELLOW}Loading quest... {char} {Style.RESET_ALL}", end="")
        time.sleep(0.3)
    
    print(f"\n{Fore.GREEN + Style.BRIGHT}✅ QUEST READY! ⚓{Style.RESET_ALL}\n")
    time.sleep(1)

def main():
    print(f"""
{Fore.YELLOW + Style.BRIGHT}
╔═══════════════════════════════════════════════════════════════════════════════╗
║              🏴‍☠️ VIRTUOSO TREASURE ISLAND QUEST - SCENE 1 🏴‍☠️               ║
║                          The Quest Begins (Demo)                             ║
╚═══════════════════════════════════════════════════════════════════════════════╝
{Style.RESET_ALL}
    """)
    
    # Animated intro
    animated_intro()
    
    # Display Scene 1
    scene = create_scene_1_establishing_shot()
    print(scene)
    
    print(f"\n{Fore.CYAN + Style.BRIGHT}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━{Style.RESET_ALL}")
    print(f"{Fore.MAGENTA + Style.BRIGHT}🎬 SCENE 1 COMPLETE - The adventure begins!{Style.RESET_ALL}")
    print(f"{Fore.YELLOW}Duration: 2-3 seconds (establishing shot){Style.RESET_ALL}")
    print(f"{Fore.GREEN}Purpose: Set adventure tone and introduce the quest{Style.RESET_ALL}")
    
    print(f"\n{Fore.WHITE + Style.BRIGHT}📋 SCENE ELEMENTS ACHIEVED:{Style.RESET_ALL}")
    print(f"{Fore.GREEN}✅ Wide establishing shot of vast ocean{Style.RESET_ALL}")
    print(f"{Fore.GREEN}✅ Treasure island visible in distance{Style.RESET_ALL}")
    print(f"{Fore.GREEN}✅ Pirate ship 'VIRTUOSO' prominently displayed{Style.RESET_ALL}")
    print(f"{Fore.GREEN}✅ Black flag with pirate theme{Style.RESET_ALL}")
    print(f"{Fore.GREEN}✅ Dramatic golden hour lighting{Style.RESET_ALL}")
    print(f"{Fore.GREEN}✅ Title overlay with quest branding{Style.RESET_ALL}")
    print(f"{Fore.GREEN}✅ Subtitle: 'TREASURE ISLAND AHEAD!'{Style.RESET_ALL}")
    
    print(f"\n{Fore.CYAN + Style.BRIGHT}🚀 NEXT STEPS:{Style.RESET_ALL}")
    print(f"{Fore.YELLOW}Run: python scripts/virtuoso_treasure_quest_generator.py{Style.RESET_ALL}")
    print(f"{Fore.CYAN}  → Access all 8 scenes of the complete quest{Style.RESET_ALL}")
    print(f"{Fore.CYAN}  → Interactive scene selection menu{Style.RESET_ALL}")
    print(f"{Fore.CYAN}  → Full animation playback option{Style.RESET_ALL}")
    
    print(f"\n{Fore.GREEN + Style.BRIGHT}⚓ Ready to set sail for the complete treasure quest adventure! ⚓{Style.RESET_ALL}")

if __name__ == "__main__":
    main() 