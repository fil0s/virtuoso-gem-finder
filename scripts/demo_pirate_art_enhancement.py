#!/usr/bin/env python3
"""
Quick Demo of ASCII Art Enhancements
Shows before/after examples of the pirate ASCII art
"""

import os
import sys
from colorama import init, Fore, Back, Style

# Initialize colorama
init(autoreset=True)

def load_pirate_art():
    """Load the pirate ASCII art"""
    try:
        with open("ASIIC PIRATE PICTURE.sty", 'r', encoding='utf-8') as f:
            return f.read()
    except FileNotFoundError:
        print("⚠️  Could not find 'ASIIC PIRATE PICTURE.sty' - make sure you're in the right directory!")
        return None

def colorize_sample(text, max_lines=20):
    """Apply quick colorization to a sample of the art"""
    lines = text.split('\n')[:max_lines]  # Show first 20 lines
    
    color_map = {
        '%': Fore.YELLOW + Style.BRIGHT,      # Gold treasure
        '@': Fore.RED + Style.BRIGHT,         # Pirate red  
        '#': Fore.BLACK + Style.BRIGHT,       # Black
        'W': Fore.WHITE + Style.BRIGHT,       # White/silver
        '$': Fore.YELLOW + Style.DIM,         # Dull gold
        '9': Fore.BLUE + Style.BRIGHT,        # Ocean blue
        '8': Fore.CYAN + Style.BRIGHT,        # Sea cyan
        '7': Fore.GREEN + Style.BRIGHT,       # Island green
    }
    
    result = ""
    for line in lines:
        for char in line:
            if char in color_map:
                result += color_map[char] + char + Style.RESET_ALL
            else:
                result += char
        result += '\n'
    
    return result

def enhance_contrast_sample(text, max_lines=20):
    """Show enhanced contrast version"""
    lines = text.split('\n')[:max_lines]
    
    replacements = {
        '%': '█',  # Full block - treasure/gold areas
        '@': '▓',  # Dark shade - main pirate features
        '#': '▒',  # Medium shade - details
        'W': '░',  # Light shade - highlights
        '$': '◆',  # Diamond - special elements
    }
    
    result = ""
    for line in lines:
        enhanced_line = line
        for old, new in replacements.items():
            enhanced_line = enhanced_line.replace(old, new)
        result += enhanced_line + '\n'
    
    return result

def main():
    print("🏴‍☠️ " + "="*60 + " 🏴‍☠️")
    print("           PIRATE ASCII ART ENHANCEMENT DEMO")
    print("🏴‍☠️ " + "="*60 + " 🏴‍☠️")
    
    # Load the original art
    original_art = load_pirate_art()
    if not original_art:
        return
    
    print("\n" + "📜 ORIGINAL ASCII ART (first 20 lines):")
    print("-" * 50)
    original_lines = original_art.split('\n')[:20]
    for line in original_lines:
        print(line)
    
    print("\n" + "🎨 COLORIZED VERSION:")
    print("-" * 50)
    colorized = colorize_sample(original_art)
    print(colorized)
    
    print("\n" + "🔍 ENHANCED CONTRAST VERSION:")
    print("-" * 50)
    contrast_enhanced = enhance_contrast_sample(original_art)
    print(contrast_enhanced)
    
    print("\n" + "🌈 COLORIZED + ENHANCED VERSION:")
    print("-" * 50)
    combined = colorize_sample(enhance_contrast_sample(original_art, 100), 20)
    print(combined)
    
    print("\n" + "💡 ENHANCEMENT OPTIONS AVAILABLE:")
    print("=" * 50)
    print("✨ Rich library effects with gradients")
    print("🎬 Animated color-cycling versions") 
    print("🎭 3D shadow effects")
    print("🌈 Background color themes")
    print("⚡ Terminal-optimized layouts")
    print("🎯 Custom color schemes")
    print("🔧 Contrast and readability improvements")
    
    print(f"\n🚀 Run: {Fore.CYAN}python scripts/enhance_ascii_art.py{Style.RESET_ALL}")
    print("   For the full interactive enhancement tool!")
    
    print(f"\n📦 Required packages: {Fore.YELLOW}colorama rich{Style.RESET_ALL}")
    print(f"   Install with: {Fore.GREEN}pip install colorama rich{Style.RESET_ALL}")

if __name__ == "__main__":
    main() 