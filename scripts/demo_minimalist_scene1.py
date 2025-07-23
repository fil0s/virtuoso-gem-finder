#!/usr/bin/env python3
"""
🏴‍☠️ Minimalist Treasure Quest - Scene 1 Demo
Showcasing clean, properly spaced visual design
"""

from colorama import init, Fore, Back, Style
import time

# Initialize colorama
init(autoreset=True)

def create_minimalist_scene_1():
    """Clean Scene 1: The Quest Begins - No embedded text, proper spacing"""
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

def main():
    print(f"""
{Fore.YELLOW + Style.BRIGHT}
╔══════════════════════════════════════════════════════════════════════════════╗
║              🏴‍☠️ MINIMALIST TREASURE QUEST - SCENE 1 DEMO 🏴‍☠️             ║
║                     Clean Visual Design with Proper Spacing                  ║
╚══════════════════════════════════════════════════════════════════════════════╝
{Style.RESET_ALL}
    """)
    
    # Display the minimalist scene
    scene = create_minimalist_scene_1()
    print(scene)
    
    print(f"\n{Fore.CYAN + Style.BRIGHT}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━{Style.RESET_ALL}")
    print(f"{Fore.MAGENTA + Style.BRIGHT}✨ MINIMALIST DESIGN IMPROVEMENTS ✨{Style.RESET_ALL}")
    
    print(f"\n{Fore.WHITE + Style.BRIGHT}🎨 DESIGN PRINCIPLES APPLIED:{Style.RESET_ALL}")
    print(f"{Fore.GREEN}✅ Removed embedded text from visual elements{Style.RESET_ALL}")
    print(f"{Fore.GREEN}✅ Clean geometric ship design with proper borders{Style.RESET_ALL}")
    print(f"{Fore.GREEN}✅ Consistent spacing between visual layers{Style.RESET_ALL}")
    print(f"{Fore.GREEN}✅ Separated descriptive text into clean information boxes{Style.RESET_ALL}")
    print(f"{Fore.GREEN}✅ Visual hierarchy: Sky → Island → Ocean → Ship → Info{Style.RESET_ALL}")
    print(f"{Fore.GREEN}✅ Symbolic representation over text labels{Style.RESET_ALL}")
    
    print(f"\n{Fore.WHITE + Style.BRIGHT}🎯 VISUAL STORYTELLING:{Style.RESET_ALL}")
    print(f"{Fore.YELLOW}☀️  Golden hour atmosphere{Style.RESET_ALL}")
    print(f"{Fore.GREEN}🏝️ 🌴  Treasure island clearly visible in distance{Style.RESET_ALL}")
    print(f"{Fore.BLUE}～～～  Ocean layers creating depth{Style.RESET_ALL}")
    print(f"{Fore.YELLOW}⚓  VIRTUOSO ship as focal point{Style.RESET_ALL}")
    print(f"{Fore.WHITE}📋  Clean mission briefing separated from art{Style.RESET_ALL}")
    
    print(f"\n{Fore.CYAN + Style.BRIGHT}🚀 AVAILABLE VERSIONS:{Style.RESET_ALL}")
    print(f"{Fore.YELLOW}📁 Original: python scripts/virtuoso_treasure_quest_generator.py{Style.RESET_ALL}")
    print(f"{Fore.GREEN}🎨 Minimalist: python scripts/minimalist_treasure_quest.py{Style.RESET_ALL}")
    print(f"{Fore.CYAN}⚡ Enhanced: python scripts/enhance_ascii_art.py{Style.RESET_ALL}")
    
    print(f"\n{Fore.GREEN + Style.BRIGHT}⚓ Ready for your crypto treasure hunting adventure! ⚓{Style.RESET_ALL}")

if __name__ == "__main__":
    main() 