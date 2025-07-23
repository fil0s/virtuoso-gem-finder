#!/usr/bin/env python3
"""
Base Strategy Class for Trading Implementation
"""

from abc import ABC, abstractmethod
from typing import Dict, List, Any, Optional
from dataclasses import dataclass
from datetime import datetime
import logging

@dataclass
class TradingSignal:
    """Trading signal data structure"""
    strategy_name: str
    token_address: str
    signal_type: str  # 'BUY', 'SELL', 'HOLD'
    confidence: float  # 0.0 to 1.0
    position_size: float  # Percentage of portfolio
    entry_price: Optional[float] = None
    stop_loss: Optional[float] = None
    take_profit: Optional[float] = None
    time_limit: Optional[int] = None  # Minutes
    metadata: Dict[str, Any] = None
    timestamp: datetime = datetime.now()

@dataclass
class Position:
    """Trading position data structure"""
    token_address: str
    symbol: str
    entry_price: float
    quantity: float
    current_price: float
    entry_time: datetime
    strategy: str
    stop_loss: Optional[float] = None
    take_profit: Optional[float] = None
    
    @property
    def unrealized_pnl(self) -> float:
        """Calculate unrealized P&L"""
        return (self.current_price - self.entry_price) * self.quantity
    
    @property
    def unrealized_pnl_pct(self) -> float:
        """Calculate unrealized P&L percentage"""
        if self.entry_price == 0:
            return 0.0
        return (self.current_price - self.entry_price) / self.entry_price

class BaseStrategy(ABC):
    """Base class for all trading strategies"""
    
    def __init__(self, name: str, config: Dict[str, Any] = None):
        self.name = name
        self.config = config or {}
        self.logger = logging.getLogger(f"Strategy.{name}")
        self.active_positions: Dict[str, Position] = {}
        self.trade_history: List[Dict[str, Any]] = []
        
        # Strategy performance tracking
        self.total_trades = 0
        self.winning_trades = 0
        self.total_pnl = 0.0
        self.max_drawdown = 0.0
        
    @abstractmethod
    def should_enter(self, token_data: Dict[str, Any]) -> Optional[TradingSignal]:
        """
        Determine if strategy should enter a position
        
        Args:
            token_data: Token analysis data from detector
            
        Returns:
            TradingSignal if entry conditions met, None otherwise
        """
        pass
    
    @abstractmethod 
    def should_exit(self, position: Position, current_data: Dict[str, Any]) -> bool:
        """
        Determine if strategy should exit a position
        
        Args:
            position: Current position
            current_data: Latest token data
            
        Returns:
            True if should exit, False otherwise
        """
        pass
    
    def get_position_size(self, signal: TradingSignal, portfolio_value: float) -> float:
        """
        Calculate position size based on strategy rules
        
        Args:
            signal: Trading signal
            portfolio_value: Total portfolio value
            
        Returns:
            Position size in USD
        """
        base_size = signal.position_size * portfolio_value
        
        # Apply Kelly criterion if enabled
        if self.config.get('use_kelly_sizing', False):
            kelly_multiplier = self._calculate_kelly_multiplier()
            base_size *= kelly_multiplier
            
        # Apply maximum position size limit
        max_position = self.config.get('max_position_size', 0.02) * portfolio_value
        return min(base_size, max_position)
    
    def _calculate_kelly_multiplier(self) -> float:
        """Calculate Kelly criterion multiplier based on historical performance"""
        if self.total_trades < 10:
            return 1.0  # Not enough data for Kelly
            
        win_rate = self.winning_trades / self.total_trades
        
        # Calculate average win/loss
        wins = [trade['pnl'] for trade in self.trade_history if trade['pnl'] > 0]
        losses = [abs(trade['pnl']) for trade in self.trade_history if trade['pnl'] < 0]
        
        if not wins or not losses:
            return 1.0
            
        avg_win = sum(wins) / len(wins)
        avg_loss = sum(losses) / len(losses)
        
        # Kelly formula: f = (p*R - (1-p))/R where R = avg_win/avg_loss
        if avg_loss == 0:
            return 1.0
            
        R = avg_win / avg_loss
        kelly_f = (win_rate * R - (1 - win_rate)) / R
        
        # Cap Kelly at 25% and ensure positive
        return max(0.1, min(kelly_f, 0.25))
    
    def update_performance(self, trade_result: Dict[str, Any]):
        """Update strategy performance metrics"""
        self.total_trades += 1
        pnl = trade_result.get('pnl', 0)
        
        if pnl > 0:
            self.winning_trades += 1
            
        self.total_pnl += pnl
        self.trade_history.append(trade_result)
        
        # Update max drawdown
        running_pnl = sum(trade['pnl'] for trade in self.trade_history)
        peak = max([sum(trade['pnl'] for trade in self.trade_history[:i+1]) 
                   for i in range(len(self.trade_history))] + [0])
        current_drawdown = peak - running_pnl
        self.max_drawdown = max(self.max_drawdown, current_drawdown)
    
    def get_performance_metrics(self) -> Dict[str, float]:
        """Get strategy performance metrics"""
        if self.total_trades == 0:
            return {
                'total_trades': 0,
                'win_rate': 0.0,
                'total_pnl': 0.0,
                'avg_trade_pnl': 0.0,
                'max_drawdown': 0.0,
                'profit_factor': 0.0
            }
            
        win_rate = self.winning_trades / self.total_trades
        avg_trade_pnl = self.total_pnl / self.total_trades
        
        # Calculate profit factor
        gross_profit = sum(trade['pnl'] for trade in self.trade_history if trade['pnl'] > 0)
        gross_loss = abs(sum(trade['pnl'] for trade in self.trade_history if trade['pnl'] < 0))
        profit_factor = gross_profit / gross_loss if gross_loss > 0 else float('inf')
        
        return {
            'total_trades': self.total_trades,
            'win_rate': win_rate,
            'total_pnl': self.total_pnl,
            'avg_trade_pnl': avg_trade_pnl,
            'max_drawdown': self.max_drawdown,
            'profit_factor': profit_factor
        }
    
    def validate_entry_conditions(self, token_data: Dict[str, Any]) -> bool:
        """Validate basic entry conditions common to all strategies"""
        # Check if token has required data
        required_fields = ['address', 'symbol', 'price', 'market_cap']
        for field in required_fields:
            if not token_data.get(field):
                self.logger.debug(f"Missing required field: {field}")
                return False
                
        # Check if already have position in this token
        if token_data['address'] in self.active_positions:
            self.logger.debug(f"Already have position in {token_data['symbol']}")
            return False
            
        # Check basic liquidity requirements
        min_liquidity = self.config.get('min_liquidity', 1000)
        if token_data.get('liquidity', 0) < min_liquidity:
            self.logger.debug(f"Insufficient liquidity: {token_data.get('liquidity')}")
            return False
            
        return True
    
    def validate_exit_conditions(self, position: Position, current_data: Dict[str, Any]) -> Dict[str, Any]:
        """Check standard exit conditions (stop-loss, take-profit, time)"""
        exit_reason = None
        
        # Check stop-loss
        if position.stop_loss and current_data.get('price', 0) <= position.stop_loss:
            exit_reason = 'stop_loss'
            
        # Check take-profit
        elif position.take_profit and current_data.get('price', 0) >= position.take_profit:
            exit_reason = 'take_profit'
            
        # Check time limit
        elif hasattr(position, 'time_limit') and position.time_limit:
            time_elapsed = (datetime.now() - position.entry_time).total_seconds() / 60
            if time_elapsed >= position.time_limit:
                exit_reason = 'time_limit'
        
        return {
            'should_exit': exit_reason is not None,
            'reason': exit_reason
        }
    
    def log_signal(self, signal: TradingSignal, action: str):
        """Log trading signal for debugging"""
        self.logger.info(f"{action} signal for {signal.token_address}")
        self.logger.debug(f"Signal details: {signal}")

class StrategyConfig:
    """Configuration class for strategy parameters"""
    
    # Default configuration for all strategies
    DEFAULT_CONFIG = {
        'max_position_size': 0.02,  # 2% max position size
        'min_liquidity': 1000,      # Minimum $1000 liquidity
        'use_kelly_sizing': True,   # Use Kelly criterion for sizing
        'max_positions': 10,        # Maximum concurrent positions
        'risk_free_rate': 0.02,     # 2% risk-free rate for Sharpe calculation
    }
    
    @classmethod
    def get_strategy_config(cls, strategy_name: str) -> Dict[str, Any]:
        """Get configuration for specific strategy"""
        configs = {
            'launch_sniping': {
                **cls.DEFAULT_CONFIG,
                'position_size': 0.01,      # 1% position size
                'max_token_age': 5,         # 5 minutes max age
                'min_initial_volume': 10,   # 10 SOL minimum volume
                'stop_loss_pct': -30,       # -30% stop loss
                'take_profit_pct': 50,      # +50% take profit
                'time_limit_minutes': 120   # 2 hour time limit
            },
            'momentum_scaling': {
                **cls.DEFAULT_CONFIG,
                'initial_position_size': 0.003,  # 0.3% initial
                'scale_increment': 0.002,        # 0.2% increments
                'max_position_size': 0.02,       # 2% maximum
                'min_curve_progress': 30,        # 30% minimum progress
                'max_curve_progress': 70,        # 70% maximum progress
                'min_vlr': 1.5,                  # Minimum VLR ratio
                'stop_loss_pct': -25,            # -25% stop loss
                'trailing_stop_pct': 15          # 15% trailing stop
            },
            'breakout_momentum': {
                **cls.DEFAULT_CONFIG,
                'position_size': 0.02,           # 2% position size
                'max_graduation_hours': 1,       # 1 hour post-graduation
                'min_price_change': 30,          # 30% minimum price change
                'min_volume_multiple': 5,        # 5x volume increase
                'min_holders': 500,              # 500 minimum holders
                'stop_loss_pct': -20,            # -20% stop loss
                'trailing_stop_pct': 20,         # 20% trailing stop
                'take_profit_pct': 100           # 100% take profit
            }
        }
        
        return configs.get(strategy_name, cls.DEFAULT_CONFIG)