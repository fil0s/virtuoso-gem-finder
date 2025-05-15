#!/usr/bin/env python3
"""
Virtuoso Gem Finder - Main Application
Main entry point to run the gem finder
"""

import asyncio
import sys
from core.solgem import VirtuosoGemFinder

def main():
    """Main entry point to run the Virtuoso Gem Finder"""
    try:
        # Create an instance of VirtuosoGemFinder from the reorganized structure
        finder = VirtuosoGemFinder(config_path="config/config.yaml")
        
        # Run the main scan loop
        loop = asyncio.get_event_loop()
        loop.run_until_complete(finder.scan_new_pairs_enhanced())
        
    except KeyboardInterrupt:
        print("\nShutting down gracefully...")
        sys.exit(0)
    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main() 