#!/usr/bin/env python3
"""
ASCII Art Enhancement Tool
Improves ASCII art with colors, effects, and visual enhancements
"""

import re
from rich.console import Console
from rich.text import Text
from rich import print as rprint
from colorama import init, Fore, Back, Style
import time
import random

# Initialize colorama for cross-platform color support
init(autoreset=True)

class ASCIIArtEnhancer:
    def __init__(self):
        self.console = Console()
        
    def load_ascii_art(self, filename):
        """Load ASCII art from file"""
        try:
            with open(filename, 'r', encoding='utf-8') as f:
                return f.read()
        except Exception as e:
            print(f"Error loading file: {e}")
            return None
    
    def colorize_pirate_theme(self, ascii_art):
        """Apply pirate-themed colors to ASCII art"""
        # Define color mapping for pirate theme
        color_map = {
            '%': Fore.YELLOW + Style.BRIGHT,      # Gold/treasure
            '@': Fore.RED + Style.BRIGHT,         # Pirate red
            '#': Fore.BLACK + Style.BRIGHT,       # Black pirate colors
            'W': Fore.WHITE + Style.BRIGHT,       # White/silver
            '$': Fore.YELLOW + Style.DIM,         # Dull gold
            '9': Fore.BLUE + Style.BRIGHT,        # Ocean blue
            '8': Fore.CYAN + Style.BRIGHT,        # Sea cyan
            '7': Fore.GREEN + Style.BRIGHT,       # Island green
            '6': Fore.MAGENTA + Style.BRIGHT,     # Mystical purple
            '5': Fore.RED + Style.DIM,            # Dark red
            '4': Fore.BLUE + Style.DIM,           # Dark blue
            '3': Fore.GREEN + Style.DIM,          # Dark green
            '2': Fore.YELLOW + Style.DIM,         # Dark yellow
            '1': Fore.WHITE + Style.DIM,          # Gray
            '0': Fore.BLACK + Style.DIM,          # Very dark
        }
        
        colored_art = ""
        for char in ascii_art:
            if char in color_map:
                colored_art += color_map[char] + char + Style.RESET_ALL
            else:
                colored_art += char
        
        return colored_art
    
    def add_rich_effects(self, ascii_art):
        """Use Rich library for advanced styling"""
        lines = ascii_art.split('\n')
        styled_lines = []
        
        for i, line in enumerate(lines):
            text = Text()
            
            # Apply gradient effects
            for j, char in enumerate(line):
                if char == '%':
                    # Gold gradient
                    text.append(char, style=f"bold yellow")
                elif char == '@':
                    # Red pirate color
                    text.append(char, style=f"bold red")
                elif char == '#':
                    # Black with white background for contrast
                    text.append(char, style=f"bold black on white")
                elif char == 'W':
                    # Bright white
                    text.append(char, style=f"bold bright_white")
                elif char == '$':
                    # Golden treasure
                    text.append(char, style=f"bold gold1")
                elif char.isdigit():
                    # Number-based color gradient
                    colors = ['blue', 'cyan', 'green', 'yellow', 'magenta', 'red']
                    color_idx = int(char) % len(colors)
                    text.append(char, style=f"bold {colors[color_idx]}")
                else:
                    text.append(char)
            
            styled_lines.append(text)
        
        return styled_lines
    
    def create_animated_version(self, ascii_art, frames=10):
        """Create animated ASCII art with color cycling"""
        lines = ascii_art.split('\n')
        
        for frame in range(frames):
            self.console.clear()
            
            # Cycle through different color schemes
            color_offset = frame % 6
            colors = [Fore.RED, Fore.YELLOW, Fore.GREEN, Fore.CYAN, Fore.BLUE, Fore.MAGENTA]
            
            animated_art = ""
            for line in lines:
                colored_line = ""
                for i, char in enumerate(line):
                    if char in ['%', '@', '#', 'W', '$']:
                        color_idx = (i + color_offset) % len(colors)
                        colored_line += colors[color_idx] + char + Style.RESET_ALL
                    else:
                        colored_line += char
                animated_art += colored_line + '\n'
            
            print(animated_art)
            time.sleep(0.5)
    
    def enhance_contrast(self, ascii_art):
        """Improve contrast and readability"""
        # Replace similar characters with more distinct ones
        replacements = {
            '%': '█',  # Full block
            '@': '▓',  # Dark shade
            '#': '▒',  # Medium shade  
            'W': '░',  # Light shade
            '$': '◆',  # Diamond
        }
        
        enhanced = ascii_art
        for old, new in replacements.items():
            enhanced = enhanced.replace(old, new)
        
        return enhanced
    
    def add_background_effects(self, ascii_art):
        """Add background colors for dramatic effect"""
        lines = ascii_art.split('\n')
        enhanced_lines = []
        
        for line in lines:
            enhanced_line = ""
            for char in line:
                if char == '%':
                    enhanced_line += Back.YELLOW + Fore.BLACK + char + Style.RESET_ALL
                elif char == '@':
                    enhanced_line += Back.RED + Fore.WHITE + char + Style.RESET_ALL
                elif char == '#':
                    enhanced_line += Back.BLACK + Fore.WHITE + char + Style.RESET_ALL
                elif char == 'W':
                    enhanced_line += Back.WHITE + Fore.BLACK + char + Style.RESET_ALL
                else:
                    enhanced_line += char
            enhanced_lines.append(enhanced_line)
        
        return '\n'.join(enhanced_lines)
    
    def create_3d_effect(self, ascii_art):
        """Create pseudo-3D effect with shadows"""
        lines = ascii_art.split('\n')
        enhanced_lines = []
        
        for i, line in enumerate(lines):
            enhanced_line = ""
            for j, char in enumerate(line):
                if char in ['%', '@', '#', 'W', '$']:
                    # Add shadow effect
                    enhanced_line += Fore.WHITE + Style.BRIGHT + char
                    if j < len(line) - 1:
                        enhanced_line += Fore.BLACK + Style.DIM + '▓'
                else:
                    enhanced_line += char
            enhanced_lines.append(enhanced_line + Style.RESET_ALL)
        
        return '\n'.join(enhanced_lines)
    
    def optimize_for_terminal(self, ascii_art):
        """Optimize ASCII art for better terminal display"""
        # Remove excessive whitespace and optimize character density
        lines = ascii_art.split('\n')
        optimized_lines = []
        
        for line in lines:
            # Replace multiple spaces with single spaces
            optimized_line = re.sub(r' +', ' ', line.rstrip())
            if optimized_line.strip():  # Only keep non-empty lines
                optimized_lines.append(optimized_line)
        
        return '\n'.join(optimized_lines)

def main():
    enhancer = ASCIIArtEnhancer()
    
    # Load the pirate ASCII art
    ascii_art = enhancer.load_ascii_art("ASIIC PIRATE PICTURE.sty")
    
    if not ascii_art:
        print("Could not load ASCII art file!")
        return
    
    print("🏴‍☠️ ASCII Art Enhancement Options 🏴‍☠️")
    print("=" * 50)
    print("1. Colorized Pirate Theme")
    print("2. Rich Library Effects")
    print("3. Enhanced Contrast")
    print("4. Background Effects")
    print("5. 3D Shadow Effect")
    print("6. Animated Version")
    print("7. Terminal Optimized")
    print("8. All Effects Combined")
    
    try:
        choice = input("\nSelect enhancement (1-8): ").strip()
        
        if choice == '1':
            print("\n🎨 Applying Pirate Theme Colors...")
            enhanced = enhancer.colorize_pirate_theme(ascii_art)
            print(enhanced)
            
        elif choice == '2':
            print("\n✨ Applying Rich Library Effects...")
            styled_lines = enhancer.add_rich_effects(ascii_art)
            for line in styled_lines:
                enhancer.console.print(line)
                
        elif choice == '3':
            print("\n🔍 Enhancing Contrast...")
            enhanced = enhancer.enhance_contrast(ascii_art)
            print(enhanced)
            
        elif choice == '4':
            print("\n🌈 Adding Background Effects...")
            enhanced = enhancer.add_background_effects(ascii_art)
            print(enhanced)
            
        elif choice == '5':
            print("\n🎭 Creating 3D Effect...")
            enhanced = enhancer.create_3d_effect(ascii_art)
            print(enhanced)
            
        elif choice == '6':
            print("\n🎬 Starting Animation...")
            enhancer.create_animated_version(ascii_art)
            
        elif choice == '7':
            print("\n⚡ Terminal Optimized Version...")
            enhanced = enhancer.optimize_for_terminal(ascii_art)
            print(enhanced)
            
        elif choice == '8':
            print("\n🚀 Applying All Effects...")
            # Combine multiple effects
            optimized = enhancer.optimize_for_terminal(ascii_art)
            contrast_enhanced = enhancer.enhance_contrast(optimized)
            final_colored = enhancer.colorize_pirate_theme(contrast_enhanced)
            print(final_colored)
            
        else:
            print("Invalid choice!")
            
    except KeyboardInterrupt:
        print("\n\n👋 Goodbye, matey!")

if __name__ == "__main__":
    main()