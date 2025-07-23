import logging
import re
import time
from typing import Dict, List, Optional, Any, Tuple
import asyncio
import json

from services.position_tracker import Position, PositionTracker, UserPreferences
from services.telegram_alerter import TelegramAlerter
from api.birdeye_connector import BirdeyeAPI
from scripts.cross_platform_token_analyzer import CrossPlatformAnalyzer

class TelegramBotHandler:
    """Handles Telegram bot commands for position tracking"""
    
    def __init__(self, position_tracker: PositionTracker, telegram_alerter: TelegramAlerter,
                 birdeye_api: BirdeyeAPI, config: Dict[str, Any], 
                 logger: Optional[logging.Logger] = None):
        self.position_tracker = position_tracker
        self.telegram_alerter = telegram_alerter
        self.birdeye_api = birdeye_api
        self.config = config
        self.logger = logger or logging.getLogger(__name__)
        
        # Initialize cross-platform analyzer for token validation
        self.cross_platform_analyzer = CrossPlatformAnalyzer(config, logger)
        
        # Command handlers mapping
        self.command_handlers = {
            '/track': self._handle_track_command,
            '/positions': self._handle_positions_command,
            '/untrack': self._handle_untrack_command,
            '/set_targets': self._handle_set_targets_command,
            '/preferences': self._handle_preferences_command,
            '/help_positions': self._handle_help_command,
            '/stats': self._handle_stats_command
        }
        
        self.logger.info("🤖 TelegramBotHandler initialized")
    
    async def handle_message(self, user_id: str, message: str) -> str:
        """Handle incoming Telegram message and return response"""
        try:
            message = message.strip()
            
            # Extract command and arguments
            parts = message.split()
            if not parts:
                return "❓ Please send a command. Use /help_positions for available commands."
            
            command = parts[0].lower()
            args = parts[1:] if len(parts) > 1 else []
            
            # Handle command
            if command in self.command_handlers:
                return await self.command_handlers[command](user_id, args)
            else:
                return f"❓ Unknown command: {command}\nUse /help_positions for available commands."
                
        except Exception as e:
            self.logger.error(f"❌ Error handling message from {user_id}: {e}")
            return f"❌ Sorry, there was an error processing your command: {str(e)}"
    
    async def _handle_track_command(self, user_id: str, args: List[str]) -> str:
        """Handle /track command to start tracking a position"""
        if len(args) < 2:
            return (
                "📊 **Track Position Command**\n\n"
                "Usage: `/track <token_address> <entry_price> [position_size] [profit_target%] [stop_loss%]`\n\n"
                "Examples:\n"
                "• `/track ABC123...XYZ 0.0001234` - Basic tracking\n"
                "• `/track ABC123...XYZ 0.0001234 1000` - With position size\n"
                "• `/track ABC123...XYZ 0.0001234 1000 50 20` - With targets (50% profit, 20% stop)\n\n"
                "💡 You can also use token symbols if they're unique."
            )
        
        try:
            # Parse arguments
            token_input = args[0]
            entry_price = float(args[1])
            position_size = float(args[2]) if len(args) > 2 and args[2] != '-' else None
            profit_target_pct = float(args[3]) if len(args) > 3 and args[3] != '-' else None
            stop_loss_pct = float(args[4]) if len(args) > 4 and args[4] != '-' else None
            
            # Validate entry price
            if entry_price <= 0:
                return "❌ Entry price must be greater than 0"
            
            # Resolve token address (handle both addresses and symbols)
            token_address, token_symbol, token_name = await self._resolve_token(token_input)
            if not token_address:
                return f"❌ Could not find token: {token_input}\nPlease check the address or symbol."
            
            # Check if position already exists
            existing_positions = self.position_tracker.get_user_positions(user_id, "active")
            for pos in existing_positions:
                if pos.token_address.lower() == token_address.lower():
                    return f"⚠️ You already have an active position for {token_symbol}\nUse /untrack first to close it."
            
            # Get current token data for validation
            current_data = await self.birdeye_api.get_token_overview(token_address)
            current_price = current_data.get('price', 0) if current_data else 0
            
            # Calculate targets if provided
            profit_target = None
            stop_loss = None
            
            if profit_target_pct is not None:
                profit_target = entry_price * (1 + profit_target_pct / 100)
            
            if stop_loss_pct is not None:
                stop_loss = entry_price * (1 - stop_loss_pct / 100)
            
            # Get entry conditions snapshot
            entry_conditions = {}
            if current_data:
                entry_conditions = {
                    'price': current_price,
                    'volume_24h': current_data.get('volume', {}).get('h24', 0),
                    'market_cap': current_data.get('marketCap', 0),
                    'liquidity': current_data.get('liquidity', 0),
                    'holders': current_data.get('holders', 0),
                    'timestamp': int(time.time())
                }
            
            # Add position to tracker
            position_id = self.position_tracker.add_position(
                user_id=user_id,
                token_address=token_address,
                token_symbol=token_symbol,
                token_name=token_name,
                entry_price=entry_price,
                entry_score=0.0,  # Will be updated by monitoring
                position_size=position_size,
                profit_target=profit_target,
                stop_loss=stop_loss,
                entry_conditions=entry_conditions
            )
            
            # Build response message
            response_parts = [
                f"✅ **Position Tracked Successfully**",
                f"",
                f"🎯 **{token_name} ({token_symbol})**",
                f"📍 Address: `{token_address[:8]}...{token_address[-6:]}`",
                f"💰 Entry Price: ${entry_price:.8f}",
            ]
            
            if current_price > 0:
                pnl = ((current_price - entry_price) / entry_price) * 100
                response_parts.append(f"📊 Current Price: ${current_price:.8f} ({pnl:+.2f}%)")
            
            if position_size:
                response_parts.append(f"💼 Position Size: {position_size:,.2f}")
            
            if profit_target:
                response_parts.append(f"🎯 Profit Target: ${profit_target:.8f} (+{profit_target_pct:.1f}%)")
            
            if stop_loss:
                response_parts.append(f"🛑 Stop Loss: ${stop_loss:.8f} (-{stop_loss_pct:.1f}%)")
            
            response_parts.extend([
                f"",
                f"🔔 You'll receive alerts when exit conditions are detected.",
                f"📱 Use /positions to view all your positions."
            ])
            
            return "\n".join(response_parts)
            
        except ValueError as e:
            return f"❌ Invalid number format: {e}\nPlease check your entry price and other numeric values."
        except Exception as e:
            self.logger.error(f"❌ Error tracking position for {user_id}: {e}")
            return f"❌ Error tracking position: {str(e)}"
    
    async def _handle_positions_command(self, user_id: str, args: List[str]) -> str:
        """Handle /positions command to view all positions"""
        try:
            # Get active positions
            active_positions = self.position_tracker.get_user_positions(user_id, "active")
            
            if not active_positions:
                return (
                    "📭 **No Active Positions**\n\n"
                    "You don't have any positions being tracked.\n"
                    "Use `/track <token_address> <entry_price>` to start tracking a position.\n\n"
                    "💡 Use /help_positions for more information."
                )
            
            # Build positions summary
            response_parts = [
                f"📊 **Your Active Positions ({len(active_positions)})**",
                ""
            ]
            
            total_pnl = 0.0
            total_positions_with_size = 0
            
            for i, position in enumerate(active_positions, 1):
                # Get current price
                current_data = await self.birdeye_api.get_token_overview(position.token_address)
                current_price = current_data.get('price', 0) if current_data else position.current_price
                
                # Update position price
                if current_price > 0:
                    self.position_tracker.update_position_price(position.id, current_price)
                    position.current_price = current_price
                
                # Calculate metrics
                pnl_percent = position.get_pnl_percent()
                hold_time = position.get_hold_time_hours()
                
                # Format position info
                position_parts = [
                    f"**{i}. {position.token_symbol}**",
                    f"💰 Entry: ${position.entry_price:.8f}",
                    f"📊 Current: ${current_price:.8f} ({pnl_percent:+.2f}%)",
                    f"⏰ Hold Time: {hold_time:.1f}h"
                ]
                
                if position.position_size:
                    pnl_usd = position.get_pnl_usd()
                    position_parts.append(f"💼 P&L: ${pnl_usd:+.2f}")
                    total_pnl += pnl_usd
                    total_positions_with_size += 1
                
                if position.profit_target:
                    target_pct = ((position.profit_target - position.entry_price) / position.entry_price) * 100
                    position_parts.append(f"🎯 Target: ${position.profit_target:.8f} (+{target_pct:.1f}%)")
                
                if position.stop_loss:
                    stop_pct = ((position.entry_price - position.stop_loss) / position.entry_price) * 100
                    position_parts.append(f"🛑 Stop: ${position.stop_loss:.8f} (-{stop_pct:.1f}%)")
                
                response_parts.append("\n".join(position_parts))
                response_parts.append("")
            
            # Add portfolio summary if we have position sizes
            if total_positions_with_size > 0:
                response_parts.extend([
                    "📈 **Portfolio Summary**",
                    f"💰 Total P&L: ${total_pnl:+.2f}",
                    f"📊 Positions with P&L: {total_positions_with_size}/{len(active_positions)}",
                    ""
                ])
            
            response_parts.extend([
                "💡 **Commands:**",
                "• `/untrack <symbol>` - Stop tracking a position",
                "• `/set_targets <symbol> <profit%> <stop%>` - Update targets",
                "• `/preferences` - View/update settings"
            ])
            
            return "\n".join(response_parts)
            
        except Exception as e:
            self.logger.error(f"❌ Error getting positions for {user_id}: {e}")
            return f"❌ Error retrieving positions: {str(e)}"
    
    async def _handle_untrack_command(self, user_id: str, args: List[str]) -> str:
        """Handle /untrack command to stop tracking a position"""
        if not args:
            return (
                "🛑 **Untrack Position Command**\n\n"
                "Usage: `/untrack <token_symbol_or_address>`\n\n"
                "Examples:\n"
                "• `/untrack BONK` - Stop tracking by symbol\n"
                "• `/untrack ABC123...XYZ` - Stop tracking by address\n\n"
                "💡 Use /positions to see your active positions."
            )
        
        try:
            token_input = args[0]
            
            # Find matching position
            active_positions = self.position_tracker.get_user_positions(user_id, "active")
            matching_position = None
            
            for position in active_positions:
                if (token_input.lower() == position.token_symbol.lower() or 
                    token_input.lower() == position.token_address.lower() or
                    position.token_address.lower().startswith(token_input.lower())):
                    matching_position = position
                    break
            
            if not matching_position:
                symbols = [pos.token_symbol for pos in active_positions]
                if symbols:
                    return (
                        f"❌ No active position found for: {token_input}\n\n"
                        f"Your active positions: {', '.join(symbols)}\n"
                        f"Use /positions for detailed view."
                    )
                else:
                    return "❌ You don't have any active positions to untrack."
            
            # Get final metrics before closing
            current_data = await self.birdeye_api.get_token_overview(matching_position.token_address)
            current_price = current_data.get('price', 0) if current_data else matching_position.current_price
            
            if current_price > 0:
                self.position_tracker.update_position_price(matching_position.id, current_price)
                matching_position.current_price = current_price
            
            # Calculate final P&L
            pnl_percent = matching_position.get_pnl_percent()
            pnl_usd = matching_position.get_pnl_usd() if matching_position.position_size else None
            hold_time = matching_position.get_hold_time_hours()
            
            # Close the position
            success = self.position_tracker.close_position(matching_position.id, "manual_close")
            
            if success:
                response_parts = [
                    f"✅ **Position Closed Successfully**",
                    f"",
                    f"🎯 **{matching_position.token_name} ({matching_position.token_symbol})**",
                    f"💰 Entry Price: ${matching_position.entry_price:.8f}",
                    f"📊 Exit Price: ${current_price:.8f}",
                    f"📈 P&L: {pnl_percent:+.2f}%",
                    f"⏰ Hold Time: {hold_time:.1f} hours"
                ]
                
                if pnl_usd is not None:
                    response_parts.append(f"💼 P&L (USD): ${pnl_usd:+.2f}")
                
                response_parts.extend([
                    f"",
                    f"🎉 Thanks for using position tracking!",
                    f"📊 Use /positions to view remaining positions."
                ])
                
                return "\n".join(response_parts)
            else:
                return f"❌ Failed to close position for {matching_position.token_symbol}"
                
        except Exception as e:
            self.logger.error(f"❌ Error untracking position for {user_id}: {e}")
            return f"❌ Error closing position: {str(e)}"
    
    async def _handle_set_targets_command(self, user_id: str, args: List[str]) -> str:
        """Handle /set_targets command to update profit targets and stop losses"""
        if len(args) < 3:
            return (
                "🎯 **Set Targets Command**\n\n"
                "Usage: `/set_targets <token_symbol> <profit_target%> <stop_loss%>`\n\n"
                "Examples:\n"
                "• `/set_targets BONK 50 20` - 50% profit target, 20% stop loss\n"
                "• `/set_targets BONK 100 -` - 100% profit target, no stop loss\n"
                "• `/set_targets BONK - 15` - No profit target, 15% stop loss\n\n"
                "💡 Use `-` to remove a target."
            )
        
        try:
            token_input = args[0]
            profit_target_input = args[1]
            stop_loss_input = args[2]
            
            # Parse targets
            profit_target_pct = None if profit_target_input == '-' else float(profit_target_input)
            stop_loss_pct = None if stop_loss_input == '-' else float(stop_loss_input)
            
            # Validate targets
            if profit_target_pct is not None and profit_target_pct <= 0:
                return "❌ Profit target must be greater than 0%"
            
            if stop_loss_pct is not None and (stop_loss_pct <= 0 or stop_loss_pct >= 100):
                return "❌ Stop loss must be between 0% and 100%"
            
            # Find matching position
            active_positions = self.position_tracker.get_user_positions(user_id, "active")
            matching_position = None
            
            for position in active_positions:
                if (token_input.lower() == position.token_symbol.lower() or 
                    token_input.lower() == position.token_address.lower()):
                    matching_position = position
                    break
            
            if not matching_position:
                return f"❌ No active position found for: {token_input}"
            
            # Calculate new target prices
            entry_price = matching_position.entry_price
            new_profit_target = entry_price * (1 + profit_target_pct / 100) if profit_target_pct else None
            new_stop_loss = entry_price * (1 - stop_loss_pct / 100) if stop_loss_pct else None
            
            # Update position in database
            with self.position_tracker._get_connection() as conn:
                conn.execute("""
                    UPDATE positions 
                    SET profit_target = ?, stop_loss = ?, updated_at = ?
                    WHERE id = ?
                """, (new_profit_target, new_stop_loss, int(time.time()), matching_position.id))
                conn.commit()
            
            # Build response
            response_parts = [
                f"✅ **Targets Updated Successfully**",
                f"",
                f"🎯 **{matching_position.token_symbol}**",
                f"💰 Entry Price: ${entry_price:.8f}"
            ]
            
            if new_profit_target:
                response_parts.append(f"🎯 New Profit Target: ${new_profit_target:.8f} (+{profit_target_pct:.1f}%)")
            else:
                response_parts.append(f"🎯 Profit Target: Removed")
            
            if new_stop_loss:
                response_parts.append(f"🛑 New Stop Loss: ${new_stop_loss:.8f} (-{stop_loss_pct:.1f}%)")
            else:
                response_parts.append(f"🛑 Stop Loss: Removed")
            
            response_parts.extend([
                f"",
                f"🔔 You'll receive alerts when these targets are reached.",
                f"📊 Use /positions to view all your positions."
            ])
            
            return "\n".join(response_parts)
            
        except ValueError as e:
            return f"❌ Invalid number format: {e}"
        except Exception as e:
            self.logger.error(f"❌ Error setting targets for {user_id}: {e}")
            return f"❌ Error updating targets: {str(e)}"
    
    async def _handle_preferences_command(self, user_id: str, args: List[str]) -> str:
        """Handle /preferences command to view/update user preferences"""
        try:
            if not args:
                # Show current preferences
                prefs = self.position_tracker.get_user_preferences(user_id)
                if not prefs:
                    prefs = UserPreferences(user_id=user_id)  # Default preferences
                
                return (
                    f"⚙️ **Your Position Tracking Preferences**\n\n"
                    f"🎯 Exit Sensitivity: {prefs.exit_sensitivity.title()}\n"
                    f"⏰ Max Hold Time: {prefs.max_hold_time_hours} hours\n"
                    f"📈 Default Profit Target: {prefs.default_profit_target_percent:.1f}%\n"
                    f"🛑 Default Stop Loss: {prefs.default_stop_loss_percent:.1f}%\n"
                    f"🔔 Alert Frequency: {prefs.alert_frequency_minutes} minutes\n"
                    f"🤖 Auto-close on Exit Signal: {'Yes' if prefs.auto_close_on_exit_signal else 'No'}\n\n"
                    f"**Update Commands:**\n"
                    f"• `/preferences sensitivity <low|medium|high>`\n"
                    f"• `/preferences max_hold <hours>`\n"
                    f"• `/preferences profit_target <percentage>`\n"
                    f"• `/preferences stop_loss <percentage>`\n"
                    f"• `/preferences alert_freq <minutes>`\n"
                    f"• `/preferences auto_close <yes|no>`"
                )
            
            # Update preferences
            if len(args) < 2:
                return "❌ Please specify both setting and value. Use `/preferences` to see options."
            
            setting = args[0].lower()
            value = args[1].lower()
            
            # Get current preferences
            prefs = self.position_tracker.get_user_preferences(user_id)
            if not prefs:
                prefs = UserPreferences(user_id=user_id)
            
            # Update specific setting
            if setting in ['sensitivity', 'exit_sensitivity']:
                if value not in ['low', 'medium', 'high']:
                    return "❌ Exit sensitivity must be: low, medium, or high"
                prefs.exit_sensitivity = value
                
            elif setting in ['max_hold', 'max_hold_time']:
                try:
                    hours = int(value)
                    if hours < 1 or hours > 168:  # 1 hour to 1 week
                        return "❌ Max hold time must be between 1 and 168 hours"
                    prefs.max_hold_time_hours = hours
                except ValueError:
                    return "❌ Max hold time must be a number (hours)"
                    
            elif setting in ['profit_target', 'profit']:
                try:
                    percent = float(value)
                    if percent < 1 or percent > 1000:
                        return "❌ Profit target must be between 1% and 1000%"
                    prefs.default_profit_target_percent = percent
                except ValueError:
                    return "❌ Profit target must be a number (percentage)"
                    
            elif setting in ['stop_loss', 'stop']:
                try:
                    percent = float(value)
                    if percent < 1 or percent > 90:
                        return "❌ Stop loss must be between 1% and 90%"
                    prefs.default_stop_loss_percent = percent
                except ValueError:
                    return "❌ Stop loss must be a number (percentage)"
                    
            elif setting in ['alert_freq', 'alert_frequency']:
                try:
                    minutes = int(value)
                    if minutes < 5 or minutes > 120:
                        return "❌ Alert frequency must be between 5 and 120 minutes"
                    prefs.alert_frequency_minutes = minutes
                except ValueError:
                    return "❌ Alert frequency must be a number (minutes)"
                    
            elif setting in ['auto_close', 'auto']:
                if value in ['yes', 'true', '1', 'on']:
                    prefs.auto_close_on_exit_signal = True
                elif value in ['no', 'false', '0', 'off']:
                    prefs.auto_close_on_exit_signal = False
                else:
                    return "❌ Auto-close must be: yes or no"
                    
            else:
                return f"❌ Unknown setting: {setting}\nUse `/preferences` to see available options."
            
            # Save preferences
            success = self.position_tracker.set_user_preferences(prefs)
            
            if success:
                return f"✅ **Preference Updated Successfully**\n\n{setting.replace('_', ' ').title()}: {value}"
            else:
                return "❌ Failed to update preferences"
                
        except Exception as e:
            self.logger.error(f"❌ Error handling preferences for {user_id}: {e}")
            return f"❌ Error updating preferences: {str(e)}"
    
    async def _handle_help_command(self, user_id: str, args: List[str]) -> str:
        """Handle /help_positions command"""
        return (
            "🤖 **Position Tracking Bot Help**\n\n"
            "**Main Commands:**\n"
            "• `/track <address> <price> [size] [profit%] [stop%]` - Start tracking a position\n"
            "• `/positions` - View all your active positions\n"
            "• `/untrack <symbol>` - Stop tracking a position\n"
            "• `/set_targets <symbol> <profit%> <stop%>` - Update targets\n"
            "• `/preferences` - View/update your settings\n"
            "• `/stats` - View tracking statistics\n\n"
            "**How It Works:**\n"
            "1. 🎯 Track positions with entry price and optional targets\n"
            "2. 🔍 System monitors token conditions every 15 minutes\n"
            "3. 🚨 Get alerts when exit conditions are detected\n"
            "4. 📊 Monitor P&L and performance in real-time\n\n"
            "**Exit Signals Based On:**\n"
            "• 📉 Volume degradation (>30% decline)\n"
            "• 📊 Price momentum reversal\n"
            "• 🐋 Whale selling activity\n"
            "• 👥 Community sentiment decline\n"
            "• 📈 Technical indicator warnings\n"
            "• ⏰ Time-based recommendations\n\n"
            "**Example Usage:**\n"
            "`/track EPjFWdd5AufqSSqeM2qN1xzybapC8G4wEGGkZwyTDt1v 1.0001 1000 25 15`\n"
            "↳ Track USDC at $1.0001, $1000 position, 25% profit target, 15% stop loss\n\n"
            "💡 **Pro Tips:**\n"
            "• Set realistic profit targets (20-50%)\n"
            "• Use stop losses to limit downside (10-20%)\n"
            "• Monitor alerts regularly for best results\n"
            "• Adjust preferences based on your risk tolerance"
        )
    
    async def _handle_stats_command(self, user_id: str, args: List[str]) -> str:
        """Handle /stats command to show tracking statistics"""
        try:
            # Get user's position statistics
            active_positions = self.position_tracker.get_user_positions(user_id, "active")
            closed_positions = self.position_tracker.get_user_positions(user_id, "closed")
            
            # Calculate metrics
            total_positions = len(active_positions) + len(closed_positions)
            
            if total_positions == 0:
                return (
                    "📊 **Your Trading Statistics**\n\n"
                    "📭 No positions tracked yet.\n"
                    "Use `/track` to start tracking your first position!"
                )
            
            # Calculate performance metrics for closed positions
            profitable_positions = 0
            total_pnl = 0.0
            total_hold_time = 0.0
            
            for position in closed_positions:
                pnl_percent = position.get_pnl_percent()
                if pnl_percent > 0:
                    profitable_positions += 1
                
                if position.position_size:
                    total_pnl += position.get_pnl_usd()
                
                total_hold_time += position.get_hold_time_hours()
            
            # Calculate current active P&L
            current_pnl = 0.0
            active_with_size = 0
            
            for position in active_positions:
                if position.position_size:
                    current_pnl += position.get_pnl_usd()
                    active_with_size += 1
            
            # Build statistics message
            response_parts = [
                f"📊 **Your Trading Statistics**",
                f"",
                f"**📈 Overall Performance**",
                f"• Total Positions: {total_positions}",
                f"• Active Positions: {len(active_positions)}",
                f"• Closed Positions: {len(closed_positions)}"
            ]
            
            if closed_positions:
                win_rate = (profitable_positions / len(closed_positions)) * 100
                avg_hold_time = total_hold_time / len(closed_positions)
                
                response_parts.extend([
                    f"• Win Rate: {win_rate:.1f}%",
                    f"• Avg Hold Time: {avg_hold_time:.1f}h"
                ])
                
                if total_pnl != 0:
                    response_parts.append(f"• Realized P&L: ${total_pnl:+.2f}")
            
            if active_positions:
                response_parts.extend([
                    f"",
                    f"**🎯 Active Positions**"
                ])
                
                if active_with_size > 0:
                    response_parts.append(f"• Unrealized P&L: ${current_pnl:+.2f}")
                
                # Show active position summary
                for position in active_positions[:3]:  # Show top 3
                    pnl_percent = position.get_pnl_percent()
                    hold_time = position.get_hold_time_hours()
                    response_parts.append(
                        f"• {position.token_symbol}: {pnl_percent:+.1f}% ({hold_time:.1f}h)"
                    )
                
                if len(active_positions) > 3:
                    response_parts.append(f"• ... and {len(active_positions) - 3} more")
            
            # Get system statistics
            system_stats = self.position_tracker.get_statistics()
            
            response_parts.extend([
                f"",
                f"**🌐 System Statistics**",
                f"• Total Users: {system_stats['total_users']}",
                f"• Active Positions: {system_stats['active_positions']}",
                f"• Recent Alerts: {system_stats['recent_alerts_24h']} (24h)"
            ])
            
            return "\n".join(response_parts)
            
        except Exception as e:
            self.logger.error(f"❌ Error getting stats for {user_id}: {e}")
            return f"❌ Error retrieving statistics: {str(e)}"
    
    async def _resolve_token(self, token_input: str) -> Tuple[Optional[str], Optional[str], Optional[str]]:
        """Resolve token input to address, symbol, and name"""
        try:
            # If input looks like an address (long alphanumeric string)
            if len(token_input) > 32 and token_input.replace('_', '').replace('-', '').isalnum():
                # Try to get token info from address
                token_data = await self.birdeye_api.get_token_overview(token_input)
                if token_data:
                    symbol = token_data.get('symbol', 'UNKNOWN')
                    name = token_data.get('name', symbol)
                    return token_input, symbol, name
                else:
                    return None, None, None
            
            # Otherwise, try to search by symbol using cross-platform analyzer
            search_results = await self.cross_platform_analyzer.search_token_by_symbol(token_input)
            
            if search_results:
                # Return the first matching result
                token = search_results[0]
                return token.get('address'), token.get('symbol'), token.get('name')
            
            return None, None, None
            
        except Exception as e:
            self.logger.warning(f"⚠️ Error resolving token {token_input}: {e}")
            return None, None, None
    
    def create_track_position_button(self, token_address: str, token_symbol: str, 
                                   current_price: float) -> str:
        """Create a track position button for high conviction alerts"""
        return (
            f"\n\n🎯 **Quick Track Position**\n"
            f"To track this position, send:\n"
            f"`/track {token_address} {current_price:.8f}`\n\n"
            f"Or with position size:\n"
            f"`/track {token_address} {current_price:.8f} 1000`"
        )
    
    async def send_exit_alert(self, position: Position, exit_signal: Any) -> bool:
        """Send exit alert to user"""
        try:
            # Build exit alert message
            message_parts = [
                f"🚨 **EXIT SIGNAL DETECTED**",
                f"",
                exit_signal.message,
                f"",
                f"**Current Status:**",
                f"💰 Current Price: ${position.current_price:.8f}",
                f"📊 P&L: {position.get_pnl_percent():+.2f}%"
            ]
            
            if position.position_size:
                pnl_usd = position.get_pnl_usd()
                message_parts.append(f"💼 P&L (USD): ${pnl_usd:+.2f}")
            
            message_parts.extend([
                f"",
                f"**Quick Actions:**",
                f"• `/untrack {position.token_symbol}` - Close position tracking",
                f"• `/positions` - View all positions",
                f"",
                f"⚠️ This is automated analysis. Always do your own research before trading."
            ])
            
            message = "\n".join(message_parts)
            
            # Send alert
            await self.telegram_alerter.send_message(message)
            
            # Log the alert
            self.position_tracker.add_alert(
                position.id, 
                exit_signal.signal_type, 
                exit_signal.signal_strength,
                f"Exit signal: {exit_signal.recommendation}"
            )
            
            return True
            
        except Exception as e:
            self.logger.error(f"❌ Error sending exit alert for position {position.id}: {e}")
            return False 