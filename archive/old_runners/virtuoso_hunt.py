#!/usr/bin/env python3
"""
VirtuosoHunt - Advanced Token Discovery Orchestrator

Schedules and executes all token discovery strategies in a staggered manner
within a one-hour cycle. It includes performance monitoring, error handling,
and generates a comprehensive cross-strategy report at the end of each cycle.

🏴‍☠️ Ahoy! Welcome to the Meme Token Pirate Hunt! 🏴‍☠️
"""

import os
import sys
import time
import asyncio
import logging
import json
import uuid
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Any, Optional
import psutil

# Setup paths
current_dir = Path(__file__).parent.absolute()
if str(current_dir) not in sys.path:
    sys.path.insert(0, str(current_dir))

from core.config_manager import ConfigManager
from core.cache_manager import CacheManager
from api.birdeye_connector import BirdeyeAPI
from services.rate_limiter_service import RateLimiterService
from services.telegram_alerter import TelegramAlerter
from services.performance_analyzer import PerformanceAnalyzer
from utils.structured_logger import get_structured_logger
from core.strategies import (
    VolumeMomentumStrategy,
    RecentListingsStrategy,
    PriceMomentumStrategy,
    LiquidityGrowthStrategy,
    HighTradingActivityStrategy,
)

def print_ascii_art():
    """
    Optimized VirtuosoHunt ASCII art with treasure island adventure theme:
    - Navigate through whales and sharks to reach treasure island
    - Adventure-focused narrative without diamond flag references
    - Performance-optimized animation with adaptive sizing
    """
    import time
    import os
    import shutil
    import sys
    
    # Get terminal dimensions for adaptive sizing
    def get_terminal_size():
        try:
            columns, rows = shutil.get_terminal_size()
            return columns, rows
        except:
            return 80, 24  # Fallback to standard size
    
    # Optimized clear screen function
    def clear_screen():
        if os.name == 'nt':
            os.system('cls')
        else:
            # Use ANSI escape sequence for faster clearing on Unix systems
            sys.stdout.write('\033[2J\033[H')
            sys.stdout.flush()
    
    # Character density optimization for treasure hunt theme
    def get_optimized_chars():
        return {
            'dense': '█▉▊▋▌▍▎▏',
            'medium': '▓▒░',
            'light': '⋅·',
            'wave': '~≈∼',
            'sparkle': '✦✧✨⭐',
            'treasure': '💎💰🏆',
            'ship': '⛵🚢⚓',
            'flag': '🏴‍☠️🏴',
            'water': '〰️💧🌊',
            'danger': '🦈⚡💀',
            'island': '🏝️🌴🗻'
        }
    
    # Adaptive frame generation for treasure island adventure
    def generate_treasure_hunt_frames(width, height):
        chars = get_optimized_chars()
        
        # Scale art based on terminal width
        if width < 60:
            ship_size = "small"
            spacing = 1
        elif width < 100:
            ship_size = "medium" 
            spacing = 2
        else:
            ship_size = "large"
            spacing = 3
        
        frames = []
        
        # Frame 1: Ship approaching dangerous waters with whales and sharks
        frame1 = f"""
╔{'═' * min(width-2, 78)}╗
║{' ' * ((min(width-2, 78) - 42) // 2)}🏴‍☠️ VIRTUOSO HUNT - TREASURE ISLAND QUEST 🏴‍☠️{' ' * ((min(width-2, 78) - 42) // 2)}║
╠{'═' * min(width-2, 78)}╣
║{' ' * min(width-2, 78)}║
║{' ' * ((min(width-2, 78) - 30) // 2)}🏝️ TREASURE ISLAND AHEAD! 🏝️{' ' * ((min(width-2, 78) - 30) // 2)}║
║{' ' * ((min(width-2, 78) - 25) // 2)}🌴 Navigate Through Dangers 🌴{' ' * ((min(width-2, 78) - 25) // 2)}║
║{' ' * min(width-2, 78)}║
║{' ' * 15}🐋💨{chars['wave'][0] * 8}🦈{chars['wave'][1] * 8}🏝️💎{' ' * 10}║
║{' ' * 13}{chars['water'][0] * 12}🦈{chars['water'][1] * 12}🌴{' ' * 8}║
║{' ' * min(width-2, 78)}║
║{' ' * 25}⛵{' ' * 30}║
║{' ' * 24}/|\\{' ' * 29}║
║{' ' * 23}/ | \\{' ' * 28}║
║{' ' * 22}🏴‍☠️ | 🏴‍☠️{' ' * 25}║
║{' ' * 21}_____|_____{' ' * 25}║
║{' ' * 20}|  VIRTUOSO |{' ' * 24}║
║{' ' * 20}|___________|{' ' * 24}║
║{' ' * 19}{chars['wave'][1] * 16}{' ' * 23}║
║{' ' * min(width-2, 78)}║
║{' ' * ((min(width-2, 78) - 45) // 2)}🚢 AHOY! DANGEROUS WATERS AHEAD MATEYS! 🚢{' ' * ((min(width-2, 78) - 45) // 2)}║
║{' ' * min(width-2, 78)}║
║{' ' * 5}⚔️  NAVIGATION STRATEGY ARSENAL:{' ' * (min(width-2, 78) - 35)}║
║{' ' * 5}🔥 Volume Momentum - Ride the whale waves!{' ' * (min(width-2, 78) - 45)}║
║{' ' * 5}🆕 Recent Listings - Spot fresh treasures!{' ' * (min(width-2, 78) - 45)}║
║{' ' * 5}📈 Price Momentum - Navigate market currents!{' ' * (min(width-2, 78) - 47)}║
║{' ' * 5}💧 Liquidity Growth - Deep water passages!{' ' * (min(width-2, 78) - 44)}║
║{' ' * 5}⚡ High Trading Activity - Shark territory!{' ' * (min(width-2, 78) - 44)}║
║{' ' * min(width-2, 78)}║
║{' ' * ((min(width-2, 78) - 55) // 2)}💎 HUNTING EVERY 12 MINUTES - TREASURE AWAITS! 💎{' ' * ((min(width-2, 78) - 55) // 2)}║
╚{'═' * min(width-2, 78)}╝
        """
        frames.append(frame1)
        
        # Frame 2: Ship navigating through whale territory
        frame2 = f"""
╔{'═' * min(width-2, 78)}╗
║{' ' * ((min(width-2, 78) - 42) // 2)}🏴‍☠️ VIRTUOSO HUNT - TREASURE ISLAND QUEST 🏴‍☠️{' ' * ((min(width-2, 78) - 42) // 2)}║
╠{'═' * min(width-2, 78)}╣
║{' ' * min(width-2, 78)}║
║{' ' * ((min(width-2, 78) - 30) // 2)}🏝️ TREASURE ISLAND AHEAD! 🏝️{' ' * ((min(width-2, 78) - 30) // 2)}║
║{' ' * ((min(width-2, 78) - 25) // 2)}🌴 Navigate Through Dangers 🌴{' ' * ((min(width-2, 78) - 25) // 2)}║
║{' ' * min(width-2, 78)}║
║{' ' * 12}🐋💨💨{chars['wave'][0] * 6}🦈{chars['wave'][1] * 6}🏝️💎{' ' * 8}║
║{' ' * 10}{chars['water'][0] * 10}🦈{chars['water'][1] * 10}🌴{' ' * 8}║
║{' ' * min(width-2, 78)}║
║{' ' * 30}⛵{' ' * 25}║
║{' ' * 29}/|\\{' ' * 24}║
║{' ' * 28}/ | \\{' ' * 23}║
║{' ' * 27}🏴‍☠️ | 🏴‍☠️{' ' * 20}║
║{' ' * 26}_____|_____{' ' * 20}║
║{' ' * 25}|  VIRTUOSO |{' ' * 19}║
║{' ' * 25}|___________|{' ' * 19}║
║{' ' * 24}{chars['wave'][1] * 16}{' ' * 18}║
║{' ' * min(width-2, 78)}║
║{' ' * ((min(width-2, 78) - 45) // 2)}🚢 WHALE TERRITORY! NAVIGATING CAREFULLY! 🚢{' ' * ((min(width-2, 78) - 45) // 2)}║
║{' ' * min(width-2, 78)}║
║{' ' * 5}⚔️  NAVIGATION STRATEGY ARSENAL:{' ' * (min(width-2, 78) - 35)}║
║{' ' * 5}🔥 Volume Momentum - Ride the whale waves!{' ' * (min(width-2, 78) - 45)}║
║{' ' * 5}🆕 Recent Listings - Spot fresh treasures!{' ' * (min(width-2, 78) - 45)}║
║{' ' * 5}📈 Price Momentum - Navigate market currents!{' ' * (min(width-2, 78) - 47)}║
║{' ' * 5}💧 Liquidity Growth - Deep water passages!{' ' * (min(width-2, 78) - 44)}║
║{' ' * 5}⚡ High Trading Activity - Shark territory!{' ' * (min(width-2, 78) - 44)}║
║{' ' * min(width-2, 78)}║
║{' ' * ((min(width-2, 78) - 55) // 2)}💎 HUNTING EVERY 12 MINUTES - TREASURE AWAITS! 💎{' ' * ((min(width-2, 78) - 55) // 2)}║
╚{'═' * min(width-2, 78)}╝
        """
        frames.append(frame2)
        
        # Frame 3: Ship in shark-infested waters, getting closer to island
        frame3 = f"""
╔{'═' * min(width-2, 78)}╗
║{' ' * ((min(width-2, 78) - 42) // 2)}🏴‍☠️ VIRTUOSO HUNT - TREASURE ISLAND QUEST 🏴‍☠️{' ' * ((min(width-2, 78) - 42) // 2)}║
╠{'═' * min(width-2, 78)}╣
║{' ' * min(width-2, 78)}║
║{' ' * ((min(width-2, 78) - 30) // 2)}🏝️ TREASURE ISLAND AHEAD! 🏝️{' ' * ((min(width-2, 78) - 30) // 2)}║
║{' ' * ((min(width-2, 78) - 25) // 2)}🌴 Navigate Through Dangers 🌴{' ' * ((min(width-2, 78) - 25) // 2)}║
║{' ' * min(width-2, 78)}║
║{' ' * 8}🐋💨💨💨{chars['wave'][0] * 4}🦈🦈{chars['wave'][1] * 4}🏝️💎{' ' * 6}║
║{' ' * 6}{chars['water'][0] * 8}🦈💀🦈{chars['water'][1] * 8}🌴{' ' * 6}║
║{' ' * min(width-2, 78)}║
║{' ' * 35}⛵{' ' * 20}║
║{' ' * 34}/|\\{' ' * 19}║
║{' ' * 33}/ | \\{' ' * 18}║
║{' ' * 32}🏴‍☠️ | 🏴‍☠️{' ' * 15}║
║{' ' * 31}_____|_____{' ' * 15}║
║{' ' * 30}|  VIRTUOSO |{' ' * 14}║
║{' ' * 30}|___________|{' ' * 14}║
║{' ' * 29}{chars['wave'][1] * 16}{' ' * 13}║
║{' ' * min(width-2, 78)}║
║{' ' * ((min(width-2, 78) - 50) // 2)}🚢 SHARK WATERS! TREASURE ISLAND IN SIGHT! 🚢{' ' * ((min(width-2, 78) - 50) // 2)}║
║{' ' * min(width-2, 78)}║
║{' ' * 5}⚔️  NAVIGATION STRATEGY ARSENAL:{' ' * (min(width-2, 78) - 35)}║
║{' ' * 5}🔥 Volume Momentum - Ride the whale waves!{' ' * (min(width-2, 78) - 45)}║
║{' ' * 5}🆕 Recent Listings - Spot fresh treasures!{' ' * (min(width-2, 78) - 45)}║
║{' ' * 5}📈 Price Momentum - Navigate market currents!{' ' * (min(width-2, 78) - 47)}║
║{' ' * 5}💧 Liquidity Growth - Deep water passages!{' ' * (min(width-2, 78) - 44)}║
║{' ' * 5}⚡ High Trading Activity - Shark territory!{' ' * (min(width-2, 78) - 44)}║
║{' ' * min(width-2, 78)}║
║{' ' * ((min(width-2, 78) - 55) // 2)}💎 HUNTING EVERY 12 MINUTES - TREASURE AWAITS! 💎{' ' * ((min(width-2, 78) - 55) // 2)}║
╚{'═' * min(width-2, 78)}╝
        """
        frames.append(frame3)
        
        # Frame 4: Ship reaches treasure island successfully
        frame4 = f"""
╔{'═' * min(width-2, 78)}╗
║{' ' * ((min(width-2, 78) - 42) // 2)}🏴‍☠️ VIRTUOSO HUNT - TREASURE ISLAND QUEST 🏴‍☠️{' ' * ((min(width-2, 78) - 42) // 2)}║
╠{'═' * min(width-2, 78)}╣
║{' ' * min(width-2, 78)}║
║{' ' * ((min(width-2, 78) - 30) // 2)}🏝️ TREASURE ISLAND REACHED! 🏝️{' ' * ((min(width-2, 78) - 30) // 2)}║
║{' ' * ((min(width-2, 78) - 25) // 2)}🌴 Mission Accomplished! 🌴{' ' * ((min(width-2, 78) - 25) // 2)}║
║{' ' * min(width-2, 78)}║
║{' ' * 5}🐋💰💎💰{chars['wave'][0] * 4}🦈⚔️🦈{chars['wave'][1] * 4}🏝️💎🌴{' ' * 3}║
║{' ' * 3}{chars['water'][0] * 8}⚓💰⚓{chars['water'][1] * 8}🏆🌴{' ' * 3}║
║{' ' * min(width-2, 78)}║
║{' ' * 40}⛵{' ' * 15}║
║{' ' * 39}/|\\{' ' * 14}║
║{' ' * 38}/ | \\{' ' * 13}║
║{' ' * 37}🏴‍☠️ | 🏴‍☠️{' ' * 10}║
║{' ' * 36}_____|_____{' ' * 10}║
║{' ' * 35}|  VIRTUOSO |{' ' * 9}║
║{' ' * 35}|___________|{' ' * 9}║
║{' ' * 34}{chars['wave'][1] * 16}{' ' * 8}║
║{' ' * min(width-2, 78)}║
║{' ' * ((min(width-2, 78) - 55) // 2)}🚢 TREASURE ISLAND REACHED! ANALYZING BOUNTY! 🚢{' ' * ((min(width-2, 78) - 55) // 2)}║
║{' ' * min(width-2, 78)}║
║{' ' * 5}⚔️  VICTORIOUS STRATEGY ARSENAL:{' ' * (min(width-2, 78) - 35)}║
║{' ' * 5}🔥 Volume Momentum - Whale waves conquered!{' ' * (min(width-2, 78) - 45)}║
║{' ' * 5}🆕 Recent Listings - Fresh treasures found!{' ' * (min(width-2, 78) - 45)}║
║{' ' * 5}📈 Price Momentum - Market currents mastered!{' ' * (min(width-2, 78) - 47)}║
║{' ' * 5}💧 Liquidity Growth - Deep waters navigated!{' ' * (min(width-2, 78) - 45)}║
║{' ' * 5}⚡ High Trading Activity - Sharks defeated!{' ' * (min(width-2, 78) - 44)}║
║{' ' * min(width-2, 78)}║
║{' ' * ((min(width-2, 78) - 55) // 2)}💎 HUNTING EVERY 12 MINUTES - TREASURE AWAITS! 💎{' ' * ((min(width-2, 78) - 55) // 2)}║
╚{'═' * min(width-2, 78)}╝
        """
        frames.append(frame4)
        
        return frames
    
    # Performance-optimized animation with treasure hunt theme
    def run_treasure_hunt_animation():
        terminal_width, terminal_height = get_terminal_size()
        frames = generate_treasure_hunt_frames(terminal_width, terminal_height)
        
        # Adaptive timing based on terminal performance
        base_delay = 0.6 if terminal_width > 100 else 0.8
        
        try:
            # Pre-clear for smoother animation
            clear_screen()
            
            for i, frame in enumerate(frames):
                clear_screen()
                print(frame)
                
                # Variable timing for dramatic effect
                if i == len(frames) - 1:  # Last frame
                    time.sleep(base_delay * 2)
                else:
                    time.sleep(base_delay)
            
            # Final static display with treasure island theme
            clear_screen()
            show_final_treasure_display(terminal_width, terminal_height)
            
        except KeyboardInterrupt:
            # Graceful interruption handling
            clear_screen()
            show_treasure_fallback(terminal_width, terminal_height)
        except Exception as e:
            # Error fallback
            print("🏴‍☠️ VIRTUOSO HUNT - ASCII DISPLAY ERROR")
            print(f"Error: {e}")
            show_simple_treasure_fallback()
    
    def show_final_treasure_display(width, height):
        """Enhanced final display with treasure island theme"""
        chars = get_optimized_chars()
        
        final_display = f"""
╔{'═' * min(width-2, 78)}╗
║{' ' * ((min(width-2, 78) - 50) // 2)}🏴‍☠️ VIRTUOSO HUNT - READY FOR TREASURE QUEST! 🏴‍☠️{' ' * ((min(width-2, 78) - 50) // 2)}║
╠{'═' * min(width-2, 78)}╣
║{' ' * min(width-2, 78)}║
║{' ' * 10}🐋💰💎💰{chars['sparkle'][0] * 8}🏝️ TREASURE ISLAND 🏝️{' ' * 10}║
║{' ' * 8}{chars['wave'][0] * 15}🌴 Navigate Through Dangers 🌴{' ' * 8}║
║{' ' * min(width-2, 78)}║
║{' ' * 6}🦈{chars['wave'][1] * 12}⚔️{chars['wave'][2] * 12}🦈{' ' * 6}║
║{' ' * min(width-2, 78)}║
║{' ' * 40}⛵{' ' * 20}║
║{' ' * 39}/|\\{' ' * 19}║
║{' ' * 38}/ | \\{' ' * 18}║
║{' ' * 37}🏴‍☠️ | 🏴‍☠️{' ' * 15}║
║{' ' * 36}_____|_____{' ' * 15}║
║{' ' * 35}|  VIRTUOSO |{' ' * 14}║
║{' ' * 35}|___________|{' ' * 14}║
║{' ' * 34}{chars['wave'][1] * 16}{' ' * 13}║
║{' ' * min(width-2, 78)}║
║{' ' * ((min(width-2, 78) - 55) // 2)}🚢 SYSTEMS ONLINE! READY FOR TREASURE HUNT! 🚢{' ' * ((min(width-2, 78) - 55) // 2)}║
║{' ' * min(width-2, 78)}║
║{' ' * 5}⚔️  TREASURE HUNTING ARSENAL:{' ' * (min(width-2, 78) - 32)}║
║{' ' * 5}{chars['sparkle'][1]} Volume Momentum - Whale Wave Navigation{' ' * (min(width-2, 78) - 43)}║
║{' ' * 5}{chars['sparkle'][2]} Recent Listings - Fresh Treasure Discovery{' ' * (min(width-2, 78) - 45)}║
║{' ' * 5}{chars['sparkle'][3]} Price Momentum - Market Current Analysis{' ' * (min(width-2, 78) - 44)}║
║{' ' * 5}{chars['treasure'][0]} Liquidity Growth - Deep Water Exploration{' ' * (min(width-2, 78) - 45)}║
║{' ' * 5}{chars['treasure'][1]} High Activity - Shark Territory Survival{' ' * (min(width-2, 78) - 45)}║
║{' ' * min(width-2, 78)}║
║{' ' * ((min(width-2, 78) - 60) // 2)}{chars['treasure'][2]} OPTIMIZED: 12-MIN TREASURE HUNTS - MAXIMUM BOUNTY! {chars['treasure'][2]}{' ' * ((min(width-2, 78) - 60) // 2)}║
╚{'═' * min(width-2, 78)}╝
        """
        print(final_display)
    
    def show_treasure_fallback(width, height):
        """Static fallback for interrupted animation with treasure theme"""
        print(f"""
🏴‍☠️ VIRTUOSO HUNT - TREASURE ISLAND QUEST 🏴‍☠️

🐋💰💎💰                                    🏝️ TREASURE ISLAND 🏝️
~~~~~~~~~~~~~~~~~~                             🌴 Navigate Dangers 🌴

                  🦈~~~~~~~⚔️~~~~~~~🦈

                                    ⛵
                                   /|\\
                                  / | \\
                                 🏴‍☠️ | 🏴‍☠️
                                _____|_____
                               |  VIRTUOSO |
                               |___________|
                              ~~~~~~~~~~~~~~~~

🚢 TREASURE HUNT INITIALIZED - READY FOR ADVENTURE! 🚢

⚔️  TREASURE HUNTING ARSENAL:
✦ Volume Momentum - Ride whale waves to victory!
✧ Recent Listings - Discover fresh island treasures!
✨ Price Momentum - Navigate treacherous currents!
💎 Liquidity Growth - Explore deep water mysteries!
💰 High Trading Activity - Survive shark territories!

🏆 HUNTING EVERY 12 MINUTES - TREASURE AWAITS! 🏆
        """)
    
    def show_simple_treasure_fallback():
        """Simple fallback for error cases with treasure theme"""
        print("""
🏴‍☠️ VIRTUOSO HUNT 🏴‍☠️
🏝️ TREASURE ISLAND QUEST 🏝️
🚢 Ready to Hunt! 🚢
💎 12-Minute Adventures 💎
        """)
    
    # Execute optimized treasure hunt animation
    run_treasure_hunt_animation()

class VirtuosoHuntOrchestrator:
    """
    🏴‍☠️ The Captain's Bridge - Orchestrates the hourly, staggered execution 
    of token discovery strategies with performance monitoring and error handling.
    """

    def __init__(self):
        self.logger = get_structured_logger('VirtuosoHunt')
        self.hunt_id = str(uuid.uuid4())[:8]
        
        print_ascii_art()
        self.logger.info(f"🏴‍☠️ Initializing Virtuoso Hunt Orchestrator (Hunt ID: {self.hunt_id})...")

        # Load configuration
        try:
            self.config_manager = ConfigManager()
            self.config = self.config_manager.get_config()
        except Exception as e:
            self.logger.error(f"Failed to load configuration: {e}")
            sys.exit(1)

        # Initialize core services
        self._cache = CacheManager()
        self.rate_limiter = RateLimiterService()

        # Initialize Birdeye API
        birdeye_config = self.config.get('BIRDEYE_API', {})
        api_key = os.environ.get('BIRDEYE_API_KEY') or birdeye_config.get('api_key')
        if not api_key:
            self.logger.error("🚨 Birdeye API key not found! Set BIRDEYE_API_KEY in your .env file.")
            sys.exit(1)
        
        birdeye_config['api_key'] = api_key
        self.birdeye_api = BirdeyeAPI(
            config=birdeye_config,
            logger=self.logger,
            cache_manager=self._cache,
            rate_limiter=self.rate_limiter
        )

        # Initialize Telegram Alerter
        telegram_config = self.config.get('TELEGRAM', {})
        telegram_token = os.environ.get('TELEGRAM_BOT_TOKEN') or telegram_config.get('bot_token')
        telegram_chat_id = os.environ.get('TELEGRAM_CHAT_ID') or telegram_config.get('chat_id')
        
        self.telegram_alerter = None
        if telegram_token and telegram_chat_id:
            self.telegram_alerter = TelegramAlerter(telegram_token, telegram_chat_id)
            self.logger.info("📱 Telegram alerter initialized - Captain's communications ready!")
        else:
            self.logger.warning("⚠️ Telegram not configured - sailing without communications!")

        # Initialize performance monitoring
        self.performance_analyzer = PerformanceAnalyzer()
        
        # Initialize strategies
        self.strategies = self._initialize_strategies()
        
        # Setup reporting
        self.reports_dir = Path("reports")
        self.reports_dir.mkdir(exist_ok=True)
        
        # Hunt statistics
        self.hunt_stats = {
            'cycles_completed': 0,
            'total_tokens_discovered': 0,
            'total_api_calls': 0,
            'strategy_failures': 0,
            'start_time': datetime.now(),
            'last_cycle_time': None
        }
        
        self.logger.info(f"⚔️ Initialized {len(self.strategies)} battle-ready strategies!")
        self.logger.info(f"🗺️ Reports will be stored in: {self.reports_dir.absolute()}")

    def _initialize_strategies(self) -> List:
        """Initialize all available token discovery strategies - Our battle fleet!"""
        strategy_classes = [
            VolumeMomentumStrategy,
            RecentListingsStrategy, 
            PriceMomentumStrategy,
            LiquidityGrowthStrategy,
            HighTradingActivityStrategy
        ]
        
        strategies = []
        for strategy_class in strategy_classes:
            try:
                strategy = strategy_class(logger=self.logger)
                strategies.append(strategy)
                self.logger.info(f"⚔️ Strategy enlisted: {strategy.name}")
            except Exception as e:
                self.logger.error(f"❌ Failed to initialize {strategy_class.__name__}: {e}")
        
        return strategies

    async def run_hunt(self):
        """🏴‍☠️ Main hunting loop - The eternal quest for treasure tokens!"""
        self.logger.info("🚢 Setting sail! Beginning the eternal treasure hunt...")
        
        if self.telegram_alerter:
            await self.telegram_alerter.send_message(
                f"🏴‍☠️ **VirtuosoHunt Started!** 🏴‍☠️\n\n"
                f"Hunt ID: `{self.hunt_id}`\n"
                f"Strategies: {len(self.strategies)}\n"
                f"Stagger Interval: {60/len(self.strategies):.1f} minutes\n\n"
                f"⚔️ The hunt begins! ⚔️"
            )

        try:
            while True:
                cycle_start_time = datetime.now()
                cycle_id = str(uuid.uuid4())[:8]
                
                self.logger.info(f"🏴‍☠️ Starting Hunt Cycle #{self.hunt_stats['cycles_completed'] + 1} (ID: {cycle_id})")
                self.logger.info(f"⏰ Cycle started at: {cycle_start_time.strftime('%Y-%m-%d %H:%M:%S')}")
                
                # Display system status
                self._display_system_status()
                
                cycle_results = {}
                cycle_api_calls = 0
                cycle_errors = 0
                
                # Calculate stagger interval (12 minutes for 5 strategies)
                stagger_interval_minutes = 60 / len(self.strategies) if self.strategies else 60
                
                # Execute each strategy with staggered timing
                for i, strategy in enumerate(self.strategies):
                    strategy_start_time = datetime.now()
                    self.logger.info(f"⚔️ Executing Strategy {i+1}/{len(self.strategies)}: {strategy.name}")
                    
                    try:
                        # Track initial API calls
                        initial_api_calls = getattr(self.birdeye_api, 'api_call_count', 0)
                        
                        # Execute strategy
                        tokens = await strategy.execute(self.birdeye_api, scan_id=cycle_id)
                        
                        # Calculate API calls used
                        final_api_calls = getattr(self.birdeye_api, 'api_call_count', 0)
                        strategy_api_calls = final_api_calls - initial_api_calls
                        cycle_api_calls += strategy_api_calls
                        
                        # Store results
                        cycle_results[strategy.name] = {
                            'tokens': tokens,
                            'token_count': len(tokens),
                            'api_calls': strategy_api_calls,
                            'execution_time': (datetime.now() - strategy_start_time).total_seconds(),
                            'status': 'success'
                        }
                        
                        self.logger.info(f"✅ {strategy.name}: {len(tokens)} tokens, {strategy_api_calls} API calls")
                        
                        # Track performance
                        if hasattr(self.performance_analyzer, 'track_strategy_run'):
                            cost_report = strategy.get_cost_optimization_report() if hasattr(strategy, 'get_cost_optimization_report') else {}
                            self.performance_analyzer.track_strategy_run(
                                strategy.name,
                                len(tokens),
                                cost_report
                            )

                    except Exception as e:
                        cycle_errors += 1
                        self.hunt_stats['strategy_failures'] += 1
                        
                        error_msg = f"Strategy {strategy.name} failed: {str(e)}"
                        self.logger.error(error_msg, exc_info=True)
                        
                        cycle_results[strategy.name] = {
                            'tokens': [],
                            'token_count': 0,
                            'api_calls': 0,
                            'execution_time': (datetime.now() - strategy_start_time).total_seconds(),
                            'status': 'failed',
                            'error': str(e)
                        }
                        
                        if self.telegram_alerter:
                            await self.telegram_alerter.send_message(
                                f"🚨 **Strategy Failure Alert** 🚨\n\n"
                                f"Hunt ID: `{self.hunt_id}`\n"
                                f"Cycle: #{self.hunt_stats['cycles_completed'] + 1}\n"
                                f"Strategy: `{strategy.name}`\n"
                                f"Error: `{str(e)[:200]}...`"
                            )

                    # Wait before next strategy (except for the last one)
                    if i < len(self.strategies) - 1:
                        self.logger.info(f"⏳ Waiting {stagger_interval_minutes:.1f} minutes until next strategy...")
                        await asyncio.sleep(stagger_interval_minutes * 60)

                # Update hunt statistics
                self.hunt_stats['cycles_completed'] += 1
                self.hunt_stats['total_api_calls'] += cycle_api_calls
                self.hunt_stats['last_cycle_time'] = cycle_start_time
                
                total_tokens = sum(result['token_count'] for result in cycle_results.values())
                self.hunt_stats['total_tokens_discovered'] += total_tokens

                self.logger.info(f"🏴‍☠️ Cycle #{self.hunt_stats['cycles_completed']} Complete!")
                self.logger.info(f"📊 Tokens discovered: {total_tokens}, API calls: {cycle_api_calls}, Errors: {cycle_errors}")

                # Generate comprehensive report
                await self.generate_cross_strategy_report(cycle_results, cycle_start_time, cycle_id)
                
                # Calculate time to wait for next cycle
                cycle_duration = (datetime.now() - cycle_start_time).total_seconds()
                time_to_wait = max(0, 3600 - cycle_duration)  # Wait until next hour
                
                if time_to_wait > 0:
                    self.logger.info(f"⏰ Next hunt cycle in {time_to_wait/60:.1f} minutes...")
                    await asyncio.sleep(time_to_wait)
                else:
                    self.logger.warning("⚠️ Cycle took longer than 1 hour! Starting next cycle immediately.")

        except KeyboardInterrupt:
            self.logger.info("🏴‍☠️ Hunt stopped by Captain's orders!")
        except Exception as e:
            self.logger.critical(f"💀 Critical error in hunt loop: {e}", exc_info=True)
            if self.telegram_alerter:
                await self.telegram_alerter.send_message(
                    f"💀 **CRITICAL HUNT FAILURE** 💀\n\n"
                    f"Hunt ID: `{self.hunt_id}`\n"
                    f"Error: `{str(e)[:300]}...`\n\n"
                    f"🚨 Manual intervention required! 🚨"
                )
        finally:
            await self.cleanup()

    def _display_system_status(self):
        """Display current system status and performance metrics."""
        cpu_percent = psutil.cpu_percent()
        memory = psutil.virtual_memory()
        
        self.logger.info("🖥️ System Status:")
        self.logger.info(f"   CPU Usage: {cpu_percent}%")
        self.logger.info(f"   Memory Usage: {memory.percent}% ({memory.used // 1024 // 1024} MB)")
        self.logger.info(f"   Hunt Statistics:")
        self.logger.info(f"     Cycles Completed: {self.hunt_stats['cycles_completed']}")
        self.logger.info(f"     Total Tokens: {self.hunt_stats['total_tokens_discovered']}")
        self.logger.info(f"     Total API Calls: {self.hunt_stats['total_api_calls']}")
        self.logger.info(f"     Strategy Failures: {self.hunt_stats['strategy_failures']}")

    async def generate_cross_strategy_report(self, cycle_results: Dict, cycle_start_time: datetime, cycle_id: str):
        """Generate and save a comprehensive cross-strategy analysis report."""
        try:
            report_timestamp = cycle_start_time.strftime('%Y%m%d_%H%M%S')
            report_filename = self.reports_dir / f"virtuoso_hunt_report_{report_timestamp}.json"
            text_report_filename = self.reports_dir / f"virtuoso_hunt_report_{report_timestamp}.txt"

            # Aggregate all tokens across strategies
            all_tokens = {}
            strategy_summary = {}
            
            for strategy_name, result in cycle_results.items():
                tokens = result.get('tokens', [])
                strategy_summary[strategy_name] = {
                    'token_count': result.get('token_count', 0),
                    'api_calls': result.get('api_calls', 0),
                    'execution_time': result.get('execution_time', 0),
                    'status': result.get('status', 'unknown'),
                    'error': result.get('error')
                }
                
                for token in tokens:
                    address = token.get('address')
                    if not address:
                        continue
                        
                    if address not in all_tokens:
                        all_tokens[address] = {
                            'address': address,
                            'symbol': token.get('symbol', 'UNKNOWN'),
                            'name': token.get('name', 'Unknown Token'),
                            'score': token.get('score', 0),
                            'strategies': [],
                            'max_score': token.get('score', 0),
                            'token_data': token
                        }
                    
                    all_tokens[address]['strategies'].append(strategy_name)
                    # Keep the highest score across strategies
                    if token.get('score', 0) > all_tokens[address]['max_score']:
                        all_tokens[address]['max_score'] = token.get('score', 0)
                        all_tokens[address]['token_data'] = token

            # Sort tokens by strategy count and score
            sorted_tokens = sorted(
                all_tokens.values(), 
                key=lambda x: (len(x['strategies']), x['max_score']), 
                reverse=True
            )

            # Create comprehensive report data
            report_data = {
                'hunt_metadata': {
                    'hunt_id': self.hunt_id,
                    'cycle_id': cycle_id,
                    'cycle_number': self.hunt_stats['cycles_completed'],
                    'cycle_start_time': cycle_start_time.isoformat(),
                    'report_generated_at': datetime.now().isoformat(),
                    'total_unique_tokens': len(all_tokens),
                    'total_strategies': len(self.strategies)
                },
                'hunt_statistics': self.hunt_stats.copy(),
                'strategy_summary': strategy_summary,
                'top_tokens': sorted_tokens[:50],  # Top 50 tokens
                'performance_metrics': self.performance_analyzer.get_summary() if hasattr(self.performance_analyzer, 'get_summary') else {},
                'raw_cycle_results': cycle_results
            }

            # Save JSON report
            with open(report_filename, 'w') as f:
                json.dump(report_data, f, indent=2, default=str)

            # Generate human-readable text report
            with open(text_report_filename, 'w') as f:
                f.write("🏴‍☠️ VIRTUOSO HUNT - TREASURE MAP REPORT 🏴‍☠️\n")
                f.write("="*80 + "\n\n")
                
                f.write(f"Hunt ID: {self.hunt_id}\n")
                f.write(f"Cycle #{self.hunt_stats['cycles_completed']} (ID: {cycle_id})\n")
                f.write(f"Cycle Time: {cycle_start_time.strftime('%Y-%m-%d %H:%M:%S')}\n")
                f.write(f"Report Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")

                f.write("⚔️ STRATEGY PERFORMANCE ⚔️\n")
                f.write("-" * 40 + "\n")
                for strategy_name, summary in strategy_summary.items():
                    status_emoji = "✅" if summary['status'] == 'success' else "❌"
                    f.write(f"{status_emoji} {strategy_name}:\n")
                    f.write(f"   Tokens: {summary['token_count']}\n")
                    f.write(f"   API Calls: {summary['api_calls']}\n")
                    f.write(f"   Time: {summary['execution_time']:.2f}s\n")
                    if summary.get('error'):
                        f.write(f"   Error: {summary['error']}\n")
                    f.write("\n")

                f.write("💎 TOP TREASURE TOKENS 💎\n")
                f.write("-" * 40 + "\n")
                for i, token in enumerate(sorted_tokens[:20], 1):
                    strategy_count = len(token['strategies'])
                    f.write(f"{i:2d}. {token['symbol']} ({token['name']})\n")
                    f.write(f"    Score: {token['max_score']:.2f}\n")
                    f.write(f"    Strategies ({strategy_count}): {', '.join(token['strategies'])}\n")
                    f.write(f"    Address: {token['address']}\n\n")

                f.write("📊 HUNT STATISTICS 📊\n")
                f.write("-" * 40 + "\n")
                hunt_duration = datetime.now() - self.hunt_stats['start_time']
                f.write(f"Total Cycles: {self.hunt_stats['cycles_completed']}\n")
                f.write(f"Hunt Duration: {hunt_duration}\n")
                f.write(f"Total Tokens Discovered: {self.hunt_stats['total_tokens_discovered']}\n")
                f.write(f"Total API Calls: {self.hunt_stats['total_api_calls']}\n")
                f.write(f"Strategy Failures: {self.hunt_stats['strategy_failures']}\n")
                f.write(f"Success Rate: {((len(self.strategies) * self.hunt_stats['cycles_completed'] - self.hunt_stats['strategy_failures']) / max(1, len(self.strategies) * self.hunt_stats['cycles_completed']) * 100):.1f}%\n")

            self.logger.info(f"📊 Cross-strategy report saved:")
            self.logger.info(f"   JSON: {report_filename}")
            self.logger.info(f"   Text: {text_report_filename}")

            # Send Telegram summary
            if self.telegram_alerter:
                multi_strategy_tokens = [t for t in sorted_tokens if len(t['strategies']) > 1]
                
                summary_message = (
                    f"🏴‍☠️ **Hunt Cycle #{self.hunt_stats['cycles_completed']} Complete!** 🏴‍☠️\n\n"
                    f"🎯 **Treasure Found:**\n"
                    f"• Total Tokens: {len(all_tokens)}\n"
                    f"• Multi-Strategy Hits: {len(multi_strategy_tokens)}\n"
                    f"• API Calls Used: {sum(s.get('api_calls', 0) for s in strategy_summary.values())}\n\n"
                    f"⚔️ **Strategy Performance:**\n"
                )
                
                for strategy_name, summary in strategy_summary.items():
                    status_emoji = "✅" if summary['status'] == 'success' else "❌"
                    summary_message += f"{status_emoji} {strategy_name}: {summary['token_count']} tokens\n"
                
                if multi_strategy_tokens:
                    summary_message += f"\n💎 **Top Multi-Strategy Finds:**\n"
                    for token in multi_strategy_tokens[:5]:
                        summary_message += f"• {token['symbol']} ({len(token['strategies'])} strategies)\n"

                await self.telegram_alerter.send_message(summary_message)
                
                # Send the text report as document
                try:
                    await self.telegram_alerter.send_document(
                        document_path=str(text_report_filename),
                        caption=f"📊 Detailed Hunt Report - Cycle #{self.hunt_stats['cycles_completed']}"
                    )
                except Exception as e:
                    self.logger.warning(f"Failed to send report document via Telegram: {e}")

        except Exception as e:
            self.logger.error(f"❌ Error generating cross-strategy report: {e}", exc_info=True)

    async def cleanup(self):
        """Cleanup resources and save final statistics."""
        self.logger.info("🏴‍☠️ Performing cleanup operations...")
        
        try:
            # Save final hunt statistics
            final_stats_file = self.reports_dir / f"hunt_final_stats_{self.hunt_id}.json"
            final_stats = {
                'hunt_id': self.hunt_id,
                'hunt_stats': self.hunt_stats.copy(),
                'final_cleanup_time': datetime.now().isoformat(),
                'total_hunt_duration': str(datetime.now() - self.hunt_stats['start_time'])
            }
            
            with open(final_stats_file, 'w') as f:
                json.dump(final_stats, f, indent=2, default=str)
            
            self.logger.info(f"💾 Final statistics saved to: {final_stats_file}")
            
            if self.telegram_alerter:
                await self.telegram_alerter.send_message(
                    f"🏴‍☠️ **VirtuosoHunt Ended** 🏴‍☠️\n\n"
                    f"Hunt ID: `{self.hunt_id}`\n"
                    f"Cycles Completed: {self.hunt_stats['cycles_completed']}\n"
                    f"Total Tokens: {self.hunt_stats['total_tokens_discovered']}\n"
                    f"Duration: {datetime.now() - self.hunt_stats['start_time']}\n\n"
                    f"⚔️ The hunt ends, but the legend lives on! ⚔️"
                )
                
        except Exception as e:
            self.logger.error(f"Error during cleanup: {e}")

def main():
    """🏴‍☠️ Launch the VirtuosoHunt - All aboard the treasure ship!"""
    orchestrator = VirtuosoHuntOrchestrator()
    
    try:
        asyncio.run(orchestrator.run_hunt())
    except KeyboardInterrupt:
        print("\n🏴‍☠️ Hunt stopped by Captain's orders! Farewell, brave pirates! 🏴‍☠️")
    except Exception as e:
        print(f"\n💀 Critical error during hunt: {e}")
        logging.critical(f"Critical error in main: {e}", exc_info=True)

if __name__ == "__main__":
    main() 