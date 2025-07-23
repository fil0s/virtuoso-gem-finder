import sqlite3
import json
import time
import logging
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass, asdict
from pathlib import Path
import asyncio
from datetime import datetime, timedelta

@dataclass
class Position:
    """Represents a tracked trading position"""
    id: Optional[int] = None
    user_id: str = ""
    token_address: str = ""
    token_symbol: str = ""
    token_name: str = ""
    entry_timestamp: int = 0
    entry_price: float = 0.0
    current_price: float = 0.0
    position_size: Optional[float] = None
    profit_target: Optional[float] = None
    stop_loss: Optional[float] = None
    status: str = "active"  # active, closed, expired
    entry_score: float = 0.0
    entry_conditions: str = "{}"  # JSON string
    created_at: int = 0
    updated_at: int = 0
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert position to dictionary"""
        return asdict(self)
    
    def get_entry_conditions_dict(self) -> Dict[str, Any]:
        """Parse entry conditions JSON"""
        try:
            return json.loads(self.entry_conditions)
        except (json.JSONDecodeError, TypeError):
            return {}
    
    def get_hold_time_hours(self) -> float:
        """Calculate how long position has been held in hours"""
        current_time = int(time.time())
        return (current_time - self.entry_timestamp) / 3600.0
    
    def get_pnl_percent(self) -> float:
        """Calculate P&L percentage"""
        if self.entry_price <= 0:
            return 0.0
        return ((self.current_price - self.entry_price) / self.entry_price) * 100
    
    def get_pnl_usd(self) -> float:
        """Calculate P&L in USD (requires position_size)"""
        if not self.position_size or self.entry_price <= 0:
            return 0.0
        return self.position_size * (self.current_price - self.entry_price)

@dataclass 
class PositionAlert:
    """Represents an alert for a position"""
    id: Optional[int] = None
    position_id: int = 0
    alert_type: str = ""  # exit_signal, profit_target, stop_loss, time_limit
    alert_score: float = 0.0
    alert_message: str = ""
    sent_at: int = 0
    acknowledged: bool = False

@dataclass
class UserPreferences:
    """User preferences for position tracking"""
    user_id: str = ""
    exit_sensitivity: str = "medium"  # low, medium, high
    max_hold_time_hours: int = 48
    default_profit_target_percent: float = 50.0
    default_stop_loss_percent: float = 20.0
    alert_frequency_minutes: int = 15
    auto_close_on_exit_signal: bool = False

class PositionTracker:
    """Service for tracking and managing trading positions"""
    
    def __init__(self, db_path: str = "data/positions.db", logger: Optional[logging.Logger] = None):
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        
        self.logger = logger or logging.getLogger(__name__)
        
        # Initialize database
        self._init_database()
        
        self.logger.info(f"🎯 PositionTracker initialized with database: {self.db_path}")
    
    def _init_database(self):
        """Initialize SQLite database with required tables"""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS positions (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id TEXT NOT NULL,
                    token_address TEXT NOT NULL,
                    token_symbol TEXT NOT NULL,
                    token_name TEXT NOT NULL,
                    entry_timestamp INTEGER NOT NULL,
                    entry_price REAL NOT NULL,
                    current_price REAL NOT NULL,
                    position_size REAL,
                    profit_target REAL,
                    stop_loss REAL,
                    status TEXT NOT NULL DEFAULT 'active',
                    entry_score REAL NOT NULL DEFAULT 0.0,
                    entry_conditions TEXT NOT NULL DEFAULT '{}',
                    created_at INTEGER NOT NULL,
                    updated_at INTEGER NOT NULL,
                    UNIQUE(user_id, token_address, status)
                )
            """)
            
            conn.execute("""
                CREATE TABLE IF NOT EXISTS position_alerts (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    position_id INTEGER NOT NULL,
                    alert_type TEXT NOT NULL,
                    alert_score REAL NOT NULL DEFAULT 0.0,
                    alert_message TEXT NOT NULL,
                    sent_at INTEGER NOT NULL,
                    acknowledged BOOLEAN NOT NULL DEFAULT 0,
                    FOREIGN KEY (position_id) REFERENCES positions (id)
                )
            """)
            
            conn.execute("""
                CREATE TABLE IF NOT EXISTS user_preferences (
                    user_id TEXT PRIMARY KEY,
                    exit_sensitivity TEXT NOT NULL DEFAULT 'medium',
                    max_hold_time_hours INTEGER NOT NULL DEFAULT 48,
                    default_profit_target_percent REAL NOT NULL DEFAULT 50.0,
                    default_stop_loss_percent REAL NOT NULL DEFAULT 20.0,
                    alert_frequency_minutes INTEGER NOT NULL DEFAULT 15,
                    auto_close_on_exit_signal BOOLEAN NOT NULL DEFAULT 0
                )
            """)
            
            # Create indexes for performance
            conn.execute("CREATE INDEX IF NOT EXISTS idx_positions_user_status ON positions(user_id, status)")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_positions_status ON positions(status)")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_alerts_position_id ON position_alerts(position_id)")
            
            conn.commit()
    
    def add_position(self, user_id: str, token_address: str, token_symbol: str, 
                    token_name: str, entry_price: float, entry_score: float = 0.0,
                    position_size: Optional[float] = None, profit_target: Optional[float] = None,
                    stop_loss: Optional[float] = None, entry_conditions: Optional[Dict] = None) -> int:
        """Add a new position to track"""
        current_time = int(time.time())
        
        # Get user preferences for defaults
        prefs = self.get_user_preferences(user_id)
        
        if profit_target is None and prefs:
            profit_target = entry_price * (1 + prefs.default_profit_target_percent / 100)
        
        if stop_loss is None and prefs:
            stop_loss = entry_price * (1 - prefs.default_stop_loss_percent / 100)
        
        entry_conditions_json = json.dumps(entry_conditions or {})
        
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute("""
                INSERT OR REPLACE INTO positions 
                (user_id, token_address, token_symbol, token_name, entry_timestamp, 
                 entry_price, current_price, position_size, profit_target, stop_loss,
                 status, entry_score, entry_conditions, created_at, updated_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 'active', ?, ?, ?, ?)
            """, (user_id, token_address, token_symbol, token_name, current_time,
                  entry_price, entry_price, position_size, profit_target, stop_loss,
                  entry_score, entry_conditions_json, current_time, current_time))
            
            position_id = cursor.lastrowid
            conn.commit()
        
        self.logger.info(f"📊 Added position {position_id}: {token_symbol} for user {user_id} at ${entry_price:.6f}")
        return position_id
    
    def update_position_price(self, position_id: int, current_price: float) -> bool:
        """Update current price for a position"""
        current_time = int(time.time())
        
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute("""
                UPDATE positions 
                SET current_price = ?, updated_at = ?
                WHERE id = ? AND status = 'active'
            """, (current_price, current_time, position_id))
            
            updated = cursor.rowcount > 0
            conn.commit()
        
        if updated:
            self.logger.debug(f"💰 Updated position {position_id} price to ${current_price:.6f}")
        
        return updated
    
    def close_position(self, position_id: int, reason: str = "manual") -> bool:
        """Close a position"""
        current_time = int(time.time())
        
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute("""
                UPDATE positions 
                SET status = 'closed', updated_at = ?
                WHERE id = ? AND status = 'active'
            """, (current_time, position_id))
            
            closed = cursor.rowcount > 0
            conn.commit()
        
        if closed:
            # Add closing alert
            self.add_alert(position_id, "position_closed", 0.0, f"Position closed: {reason}")
            self.logger.info(f"🔒 Closed position {position_id} - {reason}")
        
        return closed
    
    def get_position(self, position_id: int) -> Optional[Position]:
        """Get a specific position by ID"""
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.execute("SELECT * FROM positions WHERE id = ?", (position_id,))
            row = cursor.fetchone()
            
            if row:
                return Position(**dict(row))
        
        return None
    
    def get_user_positions(self, user_id: str, status: str = "active") -> List[Position]:
        """Get all positions for a user"""
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.execute(
                "SELECT * FROM positions WHERE user_id = ? AND status = ? ORDER BY created_at DESC",
                (user_id, status)
            )
            
            return [Position(**dict(row)) for row in cursor.fetchall()]
    
    def get_all_active_positions(self) -> List[Position]:
        """Get all active positions across all users"""
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.execute(
                "SELECT * FROM positions WHERE status = 'active' ORDER BY created_at DESC"
            )
            
            return [Position(**dict(row)) for row in cursor.fetchall()]
    
    def add_alert(self, position_id: int, alert_type: str, alert_score: float, message: str) -> int:
        """Add an alert for a position"""
        current_time = int(time.time())
        
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute("""
                INSERT INTO position_alerts 
                (position_id, alert_type, alert_score, alert_message, sent_at)
                VALUES (?, ?, ?, ?, ?)
            """, (position_id, alert_type, alert_score, message, current_time))
            
            alert_id = cursor.lastrowid
            conn.commit()
        
        self.logger.info(f"🚨 Added alert {alert_id} for position {position_id}: {alert_type}")
        return alert_id
    
    def get_position_alerts(self, position_id: int, unacknowledged_only: bool = False) -> List[PositionAlert]:
        """Get alerts for a position"""
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            
            query = "SELECT * FROM position_alerts WHERE position_id = ?"
            params = [position_id]
            
            if unacknowledged_only:
                query += " AND acknowledged = 0"
            
            query += " ORDER BY sent_at DESC"
            
            cursor = conn.execute(query, params)
            return [PositionAlert(**dict(row)) for row in cursor.fetchall()]
    
    def acknowledge_alert(self, alert_id: int) -> bool:
        """Mark an alert as acknowledged"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute(
                "UPDATE position_alerts SET acknowledged = 1 WHERE id = ?",
                (alert_id,)
            )
            
            acknowledged = cursor.rowcount > 0
            conn.commit()
        
        return acknowledged
    
    def get_user_preferences(self, user_id: str) -> Optional[UserPreferences]:
        """Get user preferences"""
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.execute("SELECT * FROM user_preferences WHERE user_id = ?", (user_id,))
            row = cursor.fetchone()
            
            if row:
                return UserPreferences(**dict(row))
        
        return None
    
    def set_user_preferences(self, prefs: UserPreferences) -> bool:
        """Set user preferences"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute("""
                INSERT OR REPLACE INTO user_preferences 
                (user_id, exit_sensitivity, max_hold_time_hours, default_profit_target_percent,
                 default_stop_loss_percent, alert_frequency_minutes, auto_close_on_exit_signal)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (prefs.user_id, prefs.exit_sensitivity, prefs.max_hold_time_hours,
                  prefs.default_profit_target_percent, prefs.default_stop_loss_percent,
                  prefs.alert_frequency_minutes, prefs.auto_close_on_exit_signal))
            
            updated = cursor.rowcount > 0
            conn.commit()
        
        self.logger.info(f"⚙️ Updated preferences for user {prefs.user_id}")
        return updated
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get position tracking statistics"""
        with sqlite3.connect(self.db_path) as conn:
            # Active positions
            cursor = conn.execute("SELECT COUNT(*) FROM positions WHERE status = 'active'")
            active_count = cursor.fetchone()[0]
            
            # Total positions
            cursor = conn.execute("SELECT COUNT(*) FROM positions")
            total_count = cursor.fetchone()[0]
            
            # Recent alerts
            cursor = conn.execute("SELECT COUNT(*) FROM position_alerts WHERE sent_at > ?", 
                                (int(time.time()) - 86400,))  # Last 24 hours
            recent_alerts = cursor.fetchone()[0]
            
            # User count
            cursor = conn.execute("SELECT COUNT(DISTINCT user_id) FROM positions")
            user_count = cursor.fetchone()[0]
            
            return {
                "active_positions": active_count,
                "total_positions": total_count,
                "recent_alerts_24h": recent_alerts,
                "total_users": user_count,
                "database_path": str(self.db_path)
            }
    
    def cleanup_old_positions(self, days_old: int = 30) -> int:
        """Clean up old closed positions"""
        cutoff_time = int(time.time()) - (days_old * 86400)
        
        with sqlite3.connect(self.db_path) as conn:
            # First delete related alerts
            conn.execute("""
                DELETE FROM position_alerts 
                WHERE position_id IN (
                    SELECT id FROM positions 
                    WHERE status != 'active' AND updated_at < ?
                )
            """, (cutoff_time,))
            
            # Then delete old positions
            cursor = conn.execute("""
                DELETE FROM positions 
                WHERE status != 'active' AND updated_at < ?
            """, (cutoff_time,))
            
            deleted_count = cursor.rowcount
            conn.commit()
        
        self.logger.info(f"🧹 Cleaned up {deleted_count} old positions")
        return deleted_count 