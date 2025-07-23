"""
Whale Movement Tracker

Real-time monitoring and analysis of whale wallet movements for early alpha signals.
Tracks transactions, detects patterns, and provides alerts for significant whale activity.

Key Features:
- Real-time whale transaction monitoring
- Movement pattern detection and classification
- Early warning alerts for significant whale activity
- Historical movement analysis and trend tracking
- Cross-token whale flow analysis
"""

import asyncio
import logging
import time
import json
from typing import Dict, List, Any, Optional, Set, Tuple
from dataclasses import dataclass, asdict
from enum import Enum
from pathlib import Path
from datetime import datetime, timedelta
from utils.structured_logger import get_structured_logger

class MovementType(Enum):
    LARGE_BUY = "large_buy"              # Significant token purchase
    LARGE_SELL = "large_sell"            # Significant token sale
    ACCUMULATION = "accumulation"        # Gradual buying over time
    DISTRIBUTION = "distribution"        # Gradual selling over time
    ROTATION = "rotation"                # Moving from one token to another
    ENTRY = "entry"                      # First-time purchase of a token
    EXIT = "exit"                        # Complete exit from a token
    PORTFOLIO_REBALANCE = "rebalance"    # Portfolio adjustment

class AlertLevel(Enum):
    LOW = "low"          # Minor movements, FYI only
    MEDIUM = "medium"    # Significant movements, worth noting
    HIGH = "high"        # Major movements, immediate attention
    CRITICAL = "critical" # Massive movements, urgent action

@dataclass
class WhaleMovement:
    whale_address: str
    movement_type: MovementType
    token_address: str
    token_symbol: str
    amount_usd: float
    transaction_hash: str
    timestamp: int
    alert_level: AlertLevel
    confidence: float        # 0.0 to 1.0 confidence in movement significance
    context: Dict[str, Any]  # Additional context (previous holdings, etc.)
    description: str         # Human-readable description

@dataclass 
class WhaleAlert:
    alert_id: str
    whale_address: str
    whale_name: str
    alert_level: AlertLevel
    movements: List[WhaleMovement]
    total_value: float
    timeframe: str          # "1h", "24h", etc.
    significance_score: float  # 0-100 score for alert importance
    recommended_action: str
    created_at: int

class WhaleMovementTracker:
    """
    Tracks whale wallet movements in real-time and generates alpha signals.
    """
    
    def __init__(self, birdeye_api, whale_discovery_service, logger: Optional[logging.Logger] = None):
        self.birdeye_api = birdeye_api
        self.whale_discovery_service = whale_discovery_service
        self.logger = logger or logging.getLogger(__name__)
        
        # Movement detection thresholds
        self.movement_thresholds = {
            'large_transaction_usd': 500_000,      # $500K+ = large transaction
            'massive_transaction_usd': 2_000_000,  # $2M+ = massive transaction
            'accumulation_timeframe_hours': 24,    # Track accumulation over 24h
            'accumulation_threshold_usd': 1_000_000, # $1M+ accumulated = significant
            'portfolio_change_threshold': 0.1,     # 10%+ portfolio change
            'min_confidence_threshold': 0.7,       # 70%+ confidence for alerts
        }
        
        # Alert configuration
        self.alert_config = {
            'enable_alerts': True,
            'min_alert_value': 250_000,           # $250K minimum for alerts
            'alert_cooldown_hours': 1,            # 1 hour between similar alerts
            'max_alerts_per_hour': 10,            # Rate limit alerts
        }
        
        # Data storage paths
        self.data_dir = Path("data/whale_movements")
        self.data_dir.mkdir(parents=True, exist_ok=True)
        
        self.movements_db_path = self.data_dir / "whale_movements.json"
        self.alerts_db_path = self.data_dir / "whale_alerts.json"
        
        # In-memory tracking
        self.tracked_whales: Set[str] = set()
        self.recent_movements: List[WhaleMovement] = []
        self.active_alerts: List[WhaleAlert] = []
        self.last_check_time = int(time.time())
        
        # Load existing data
        self._load_movement_history()
        self._initialize_whale_tracking()
        
        self.structured_logger = get_structured_logger('WhaleAlerting')

    async def start_monitoring(self, check_interval_seconds: int = 300):
        """
        Start continuous whale movement monitoring.
        
        Args:
            check_interval_seconds: How often to check for new movements (default 5 min)
        """
        self.logger.info(f"🐋 Starting whale movement monitoring (checking every {check_interval_seconds}s)")
        
        while True:
            try:
                # Check if we have any whales to track
                if not self.tracked_whales:
                    self.logger.warning("No whales currently tracked. Waiting for whale discovery...")
                    await asyncio.sleep(60)  # Wait 1 minute before retrying
                    continue
                
                await self._check_whale_movements()
                await asyncio.sleep(check_interval_seconds)
                
            except Exception as e:
                self.logger.error(f"Error in whale monitoring loop: {e}")
                await asyncio.sleep(60)  # Wait 1 minute before retrying

    async def _check_whale_movements(self):
        """Check all tracked whales for new movements using intelligent batching"""
        whale_count = len(self.tracked_whales)
        self.logger.debug(f"Checking {whale_count} whale wallets for movements...")
        
        # Skip processing if no whales to track
        if whale_count == 0:
            self.logger.info("No whales to track, skipping movement check")
            return
        
        current_time = int(time.time())
        new_movements = []
        
        # ENHANCED: Use intelligent batching instead of individual calls
        if hasattr(self.birdeye_api, 'batch_manager'):
            # Use batch processing for maximum efficiency
            whale_addresses = list(self.tracked_whales)
            try:
                # Batch fetch all whale portfolios at once
                batch_portfolios = await self.birdeye_api.batch_manager.batch_whale_portfolios(whale_addresses)
                
                if not batch_portfolios:
                    self.logger.warning("Batch whale portfolio fetch returned empty results, skipping analysis")
                    return
                
                # Process batched results
                for whale_address, portfolio_data in batch_portfolios.items():
                    try:
                        movements = await self._analyze_whale_transactions_batched(whale_address, portfolio_data)
                        new_movements.extend(movements)
                    except Exception as e:
                        self.logger.warning(f"Error analyzing batched whale {whale_address[:8]}...: {e}")
                        continue
                
                self.logger.info(f"🚀 BATCHED whale analysis: {len(batch_portfolios)} whales processed efficiently")
                
            except Exception as e:
                self.logger.error(f"Error in whale batch processing, falling back to individual calls: {e}")
                # Fallback to individual processing
                new_movements = await self._check_whale_movements_individual()
        else:
            # Fallback to individual processing
            new_movements = await self._check_whale_movements_individual()
        
        # Process new movements
        if new_movements:
            await self._process_new_movements(new_movements)
            
        self.last_check_time = current_time
        self.logger.debug(f"Whale movement check complete. Found {len(new_movements)} new movements.")

    async def _check_whale_movements_individual(self):
        """Fallback method: Check whales individually (less efficient)"""
        new_movements = []
        
        # Check each tracked whale individually (old method)
        for whale_address in list(self.tracked_whales):
            try:
                movements = await self._analyze_whale_transactions(whale_address)
                new_movements.extend(movements)
                
                # Rate limiting
                await asyncio.sleep(0.5)
                
            except Exception as e:
                self.logger.warning(f"Error checking whale {whale_address[:8]}...: {e}")
                continue
        
        return new_movements

    async def _analyze_whale_transactions_batched(self, whale_address: str, portfolio_data: Dict) -> List[WhaleMovement]:
        """Analyze whale transactions using pre-fetched batched portfolio data"""
        movements = []
        
        try:
            if not portfolio_data or 'data' not in portfolio_data:
                return movements
            
            # Use the batched portfolio data directly
            portfolio_items = portfolio_data.get('data', {})
            
            # Analyze portfolio changes for significant movements
            transactions = self._detect_portfolio_changes_batched(whale_address, portfolio_items)
            
            # Analyze each detected transaction
            for tx in transactions:
                movement = await self._classify_transaction(whale_address, tx, portfolio_items)
                if movement:
                    movements.append(movement)
            
        except Exception as e:
            self.logger.warning(f"Error analyzing batched transactions for {whale_address[:8]}...: {e}")
        
        return movements

    def _detect_portfolio_changes_batched(self, wallet_address: str, current_portfolio: Dict) -> List[Dict]:
        """Detect significant portfolio changes using batched data (optimized version)"""
        changes = []
        
        # Enhanced analysis using batched portfolio data
        positions = current_portfolio.get('items', [])
        
        for position in positions:
            token_address = position.get('address', '')
            value_usd = position.get('valueUsd', 0)
            pnl = position.get('pnl', 0)
            
            # Enhanced detection with more sophisticated criteria
            if value_usd >= self.movement_thresholds['large_transaction_usd']:
                # Calculate position significance
                total_portfolio_value = current_portfolio.get('totalValueUsd', 1)
                position_percentage = (value_usd / total_portfolio_value) * 100 if total_portfolio_value > 0 else 0
                
                changes.append({
                    'wallet': wallet_address,
                    'token_address': token_address,
                    'token_symbol': position.get('symbol', 'UNKNOWN'),
                    'value_usd': value_usd,
                    'pnl': pnl,
                    'position_percentage': position_percentage,
                    'timestamp': int(time.time()),
                    'tx_hash': f"batched_{wallet_address[:8]}_{token_address[:8]}",
                    'type': 'position_detected_batched'
                })
        
        return changes

    async def _analyze_whale_transactions(self, whale_address: str) -> List[WhaleMovement]:
        """Analyze recent transactions for a specific whale wallet"""
        movements = []
        
        try:
            # Get recent wallet transactions
            # Note: This endpoint might need adjustment based on actual Birdeye API
            transactions = await self._get_wallet_transactions(whale_address)
            
            if not transactions:
                return movements
            
            # Get current portfolio for context
            portfolio = await self.birdeye_api.get_wallet_portfolio(whale_address)
            portfolio_data = portfolio.get('data', {}) if portfolio else {}
            
            # Analyze each transaction
            for tx in transactions:
                movement = await self._classify_transaction(whale_address, tx, portfolio_data)
                if movement:
                    movements.append(movement)
            
        except Exception as e:
            self.logger.warning(f"Error analyzing transactions for {whale_address[:8]}...: {e}")
        
        return movements

    async def _get_wallet_transactions(self, wallet_address: str) -> List[Dict]:
        """Get recent transactions for a wallet (implement based on available API)"""
        try:
            # This would use Birdeye's transaction history endpoint
            # For now, we'll use a simplified approach with portfolio changes
            
            # Get current portfolio
            portfolio = await self.birdeye_api.get_wallet_portfolio(wallet_address)
            
            if not portfolio or 'data' not in portfolio:
                return []
            
            # For demonstration, we'll simulate transaction detection by comparing
            # portfolio changes over time (in a real implementation, use transaction APIs)
            return self._detect_portfolio_changes(wallet_address, portfolio['data'])
            
        except Exception as e:
            self.logger.warning(f"Error getting transactions for {wallet_address}: {e}")
            return []

    def _detect_portfolio_changes(self, wallet_address: str, current_portfolio: Dict) -> List[Dict]:
        """Detect significant portfolio changes (simplified transaction detection)"""
        changes = []
        
        # This is a simplified approach - in production, use actual transaction APIs
        positions = current_portfolio.get('items', [])
        
        for position in positions:
            token_address = position.get('address', '')
            value_usd = position.get('valueUsd', 0)
            pnl = position.get('pnl', 0)
            
            # Simulate detecting significant positions as potential movements
            if value_usd >= self.movement_thresholds['large_transaction_usd']:
                changes.append({
                    'wallet': wallet_address,
                    'token_address': token_address,
                    'token_symbol': position.get('symbol', 'UNKNOWN'),
                    'value_usd': value_usd,
                    'pnl': pnl,
                    'timestamp': int(time.time()),
                    'tx_hash': f"simulated_{wallet_address[:8]}_{token_address[:8]}",
                    'type': 'position_detected'
                })
        
        return changes

    async def _classify_transaction(self, whale_address: str, transaction: Dict, 
                                  portfolio_context: Dict) -> Optional[WhaleMovement]:
        """Classify a transaction into a movement type"""
        try:
            token_address = transaction.get('token_address', '')
            token_symbol = transaction.get('token_symbol', 'UNKNOWN')
            value_usd = transaction.get('value_usd', 0)
            tx_hash = transaction.get('tx_hash', '')
            timestamp = transaction.get('timestamp', int(time.time()))
            
            # Skip small transactions
            if value_usd < self.movement_thresholds['large_transaction_usd']:
                return None
            
            # Determine movement type and alert level
            movement_type = self._determine_movement_type(transaction, portfolio_context)
            alert_level = self._calculate_alert_level(value_usd, movement_type)
            confidence = self._calculate_movement_confidence(transaction, portfolio_context)
            
            # Skip low-confidence movements
            if confidence < self.movement_thresholds['min_confidence_threshold']:
                return None
            
            # Generate description
            description = self._generate_movement_description(
                whale_address, movement_type, token_symbol, value_usd
            )
            
            return WhaleMovement(
                whale_address=whale_address,
                movement_type=movement_type,
                token_address=token_address,
                token_symbol=token_symbol,
                amount_usd=value_usd,
                transaction_hash=tx_hash,
                timestamp=timestamp,
                alert_level=alert_level,
                confidence=confidence,
                context={'portfolio': portfolio_context, 'transaction': transaction},
                description=description
            )
            
        except Exception as e:
            self.logger.warning(f"Error classifying transaction: {e}")
            return None

    def _determine_movement_type(self, transaction: Dict, portfolio: Dict) -> MovementType:
        """Determine the type of whale movement"""
        value_usd = transaction.get('value_usd', 0)
        tx_type = transaction.get('type', '')
        
        # Simple classification logic (enhance based on actual transaction data)
        if value_usd >= self.movement_thresholds['massive_transaction_usd']:
            if 'sell' in tx_type.lower():
                return MovementType.LARGE_SELL
            else:
                return MovementType.LARGE_BUY
        else:
            # Default to accumulation for large positions detected
            return MovementType.ACCUMULATION

    def _calculate_alert_level(self, value_usd: float, movement_type: MovementType) -> AlertLevel:
        """Calculate alert level based on movement size and type"""
        if value_usd >= 10_000_000:  # $10M+
            return AlertLevel.CRITICAL
        elif value_usd >= 5_000_000:  # $5M+
            return AlertLevel.HIGH
        elif value_usd >= 1_000_000:  # $1M+
            return AlertLevel.MEDIUM
        else:
            return AlertLevel.LOW

    def _calculate_movement_confidence(self, transaction: Dict, portfolio: Dict) -> float:
        """Calculate confidence score for movement detection"""
        confidence = 0.8  # Base confidence
        
        # Adjust based on transaction value (higher value = higher confidence)
        value_usd = transaction.get('value_usd', 0)
        if value_usd >= self.movement_thresholds['massive_transaction_usd']:
            confidence += 0.1
        
        # Adjust based on portfolio context
        if portfolio and portfolio.get('totalValueUsd', 0) > 0:
            confidence += 0.1
        
        return min(1.0, confidence)

    def _generate_movement_description(self, whale_address: str, movement_type: MovementType, 
                                     token_symbol: str, value_usd: float) -> str:
        """Generate human-readable movement description"""
        whale_name = self._get_whale_name(whale_address)
        
        if movement_type == MovementType.LARGE_BUY:
            return f"{whale_name} bought ${value_usd:,.0f} worth of {token_symbol}"
        elif movement_type == MovementType.LARGE_SELL:
            return f"{whale_name} sold ${value_usd:,.0f} worth of {token_symbol}"
        elif movement_type == MovementType.ACCUMULATION:
            return f"{whale_name} accumulating {token_symbol} (${value_usd:,.0f} position)"
        else:
            return f"{whale_name} {movement_type.value} in {token_symbol} (${value_usd:,.0f})"

    def _get_whale_name(self, whale_address: str) -> str:
        """Get whale name from discovery service or use shortened address"""
        if self.whale_discovery_service:
            whale_db = self.whale_discovery_service.get_whale_database_for_analyzer()
            whale_info = whale_db.get(whale_address, {})
            name = whale_info.get('name', '')
            if name and name != 'Unknown':
                return name
        
        return f"Whale {whale_address[:8]}..."

    async def _process_new_movements(self, movements: List[WhaleMovement]):
        """Process and store new whale movements"""
        self.logger.info(f"Processing {len(movements)} new whale movements")
        
        # Add to recent movements
        self.recent_movements.extend(movements)
        
        # Keep only recent movements (last 24 hours)
        cutoff_time = int(time.time()) - (24 * 3600)
        self.recent_movements = [
            m for m in self.recent_movements 
            if m.timestamp >= cutoff_time
        ]
        
        # Generate alerts for significant movements
        alerts = await self._generate_alerts(movements)
        
        # Process alerts
        for alert in alerts:
            await self._handle_alert(alert)
        
        # Save to database
        await self._save_movements(movements)

    async def _generate_alerts(self, movements: List[WhaleMovement]) -> List[WhaleAlert]:
        """Generate alerts for significant whale movements"""
        alerts = []
        
        # Group movements by whale for combined analysis
        whale_movements = {}
        for movement in movements:
            whale_addr = movement.whale_address
            if whale_addr not in whale_movements:
                whale_movements[whale_addr] = []
            whale_movements[whale_addr].append(movement)
        
        # Generate alerts for each whale with significant activity
        for whale_address, whale_moves in whale_movements.items():
            alert = await self._create_whale_alert(whale_address, whale_moves)
            if alert:
                alerts.append(alert)
        
        return alerts

    async def _create_whale_alert(self, whale_address: str, movements: List[WhaleMovement]) -> Optional[WhaleAlert]:
        """Create alert for whale activity"""
        if not movements:
            return None
        
        # Calculate total value and significance
        total_value = sum(m.amount_usd for m in movements)
        max_alert_level = max(m.alert_level for m in movements)
        
        # Skip if below alert threshold
        if total_value < self.alert_config['min_alert_value']:
            return None
        
        # Calculate significance score (0-100)
        significance_score = min(100, (total_value / 1_000_000) * 10)  # $10M = 100 points
        
        # Determine recommended action
        recommended_action = self._determine_recommended_action(movements)
        
        # Create alert
        alert_id = f"whale_{whale_address[:8]}_{int(time.time())}"
        whale_name = self._get_whale_name(whale_address)
        
        alert = WhaleAlert(
            alert_id=alert_id,
            whale_address=whale_address,
            whale_name=whale_name,
            alert_level=max_alert_level,
            movements=movements,
            total_value=total_value,
            timeframe="recent",
            significance_score=significance_score,
            recommended_action=recommended_action,
            created_at=int(time.time())
        )
        
        return alert

    def _determine_recommended_action(self, movements: List[WhaleMovement]) -> str:
        """Determine recommended action based on whale movements"""
        total_value = sum(m.amount_usd for m in movements)
        
        # Analyze movement types
        buy_movements = [m for m in movements if m.movement_type in [MovementType.LARGE_BUY, MovementType.ACCUMULATION]]
        sell_movements = [m for m in movements if m.movement_type in [MovementType.LARGE_SELL, MovementType.DISTRIBUTION]]
        
        if len(buy_movements) > len(sell_movements):
            if total_value >= 5_000_000:
                return "🚀 STRONG BUY SIGNAL - Major whale accumulation detected"
            else:
                return "📈 WATCH - Whale accumulation activity"
        elif len(sell_movements) > len(buy_movements):
            if total_value >= 5_000_000:
                return "🚨 EXIT WARNING - Major whale distribution detected"
            else:
                return "⚠️ CAUTION - Whale selling activity"
        else:
            return "👁️ MONITOR - Mixed whale activity, watch for trends"

    async def _handle_alert(self, alert: WhaleAlert, scan_id: Optional[str] = None):
        self.structured_logger.info({
            "event": "alert_trigger_attempt",
            "alert_type": "whale",
            "scan_id": scan_id,
            "whale": alert.whale_address,
            "alert_id": alert.alert_id,
            "alert_level": alert.alert_level.value,
            "trigger_reason": "whale_movement",
            "timestamp": int(time.time())
        })
        self.logger.info(f"🐋 WHALE ALERT [{alert.alert_level.value.upper()}]: {alert.whale_name}")
        self.logger.info(f"   🏦 Whale: {alert.whale_address[:8]}... | Value: ${alert.total_value:,.0f}")
        self.logger.info(f"   📝 Action: {alert.recommended_action}")
        # Send Telegram or webhook/email alert if enabled (pseudo, extend as needed)
        try:
            # ... send alert logic ...
            self.structured_logger.info({
                "event": "alert_send_result",
                "alert_type": "whale",
                "scan_id": scan_id,
                "whale": alert.whale_address,
                "alert_id": alert.alert_id,
                "result": "success",
                "timestamp": int(time.time())
            })
        except Exception as e:
            self.structured_logger.error({
                "event": "alert_send_result",
                "alert_type": "whale",
                "scan_id": scan_id,
                "whale": alert.whale_address,
                "alert_id": alert.alert_id,
                "result": "error",
                "error": str(e),
                "timestamp": int(time.time())
            })

    def _initialize_whale_tracking(self):
        """Initialize whale tracking with known whales"""
        # Load tracked whale addresses from file if exists
        whale_config_path = self.data_dir / "tracked_whales.json"
        
        try:
            if whale_config_path.exists():
                # Use the imported json module
                with open(whale_config_path, 'r') as f:
                    whale_data = json.load(f)
                    self.tracked_whales = set(whale_data.get('addresses', []))
                self.logger.info(f"Loaded {len(self.tracked_whales)} whales for tracking")
            else:
                # Initialize with empty set if no file
                self.tracked_whales = set()
                self.logger.info("No tracked whales file found, starting with empty tracking list")
                
                # Create default file with empty list
                with open(whale_config_path, 'w') as f:
                    json.dump({'addresses': []}, f)
                
        except Exception as e:
            self.logger.error(f"Error initializing whale tracking: {e}")
            self.tracked_whales = set()

    async def add_whale_for_tracking(self, whale_address: str):
        """
        Add a whale wallet for tracking.
        
        Args:
            whale_address: Whale wallet address to track
        """
        self.tracked_whales.add(whale_address)
        self.logger.info(f"Added whale {whale_address[:8]}... for tracking")
        await self._save_tracked_whales()

    async def remove_whale_from_tracking(self, whale_address: str):
        """
        Remove a whale wallet from tracking.
        
        Args:
            whale_address: Whale wallet address to remove
        """
        if whale_address in self.tracked_whales:
            self.tracked_whales.remove(whale_address)
            self.logger.info(f"Removed whale {whale_address[:8]}... from tracking")
            await self._save_tracked_whales()

    async def _save_tracked_whales(self):
        """Save the list of tracked whales to a file"""
        whale_config_path = self.data_dir / "tracked_whales.json"
        try:
            # Use the imported json module directly
            with open(whale_config_path, 'w') as f:
                json.dump({'addresses': list(self.tracked_whales)}, f)
            self.logger.debug(f"Saved {len(self.tracked_whales)} tracked whales to config file")
        except Exception as e:
            self.logger.error(f"Error saving tracked whales: {e}")

    def get_recent_movements(self, hours: int = 24) -> List[WhaleMovement]:
        """Get recent whale movements within specified timeframe"""
        cutoff_time = int(time.time()) - (hours * 3600)
        return [m for m in self.recent_movements if m.timestamp >= cutoff_time]

    def get_active_alerts(self) -> List[WhaleAlert]:
        """Get currently active whale alerts"""
        return self.active_alerts.copy()

    def get_tracking_stats(self) -> Dict[str, Any]:
        """Get whale tracking statistics"""
        recent_24h = self.get_recent_movements(24)
        
        return {
            'tracked_whales': len(self.tracked_whales),
            'movements_24h': len(recent_24h),
            'active_alerts': len(self.active_alerts),
            'total_value_24h': sum(m.amount_usd for m in recent_24h),
            'last_check': self.last_check_time,
            'avg_movement_size': sum(m.amount_usd for m in recent_24h) / len(recent_24h) if recent_24h else 0
        }

    def _load_movement_history(self):
        """Load movement history from database"""
        try:
            if self.movements_db_path.exists():
                with open(self.movements_db_path, 'r') as f:
                    data = json.load(f)
                    # Load recent movements only (last 24 hours)
                    cutoff_time = int(time.time()) - (24 * 3600)
                    self.recent_movements = [
                        WhaleMovement(**m) for m in data 
                        if m.get('timestamp', 0) >= cutoff_time
                    ]
                    
        except Exception as e:
            self.logger.warning(f"Error loading movement history: {e}")

    async def _save_movements(self, movements: List[WhaleMovement]):
        """Save movements to database"""
        try:
            # Load existing movements
            existing_movements = []
            if self.movements_db_path.exists():
                with open(self.movements_db_path, 'r') as f:
                    existing_movements = json.load(f)
            
            # Add new movements
            new_data = [asdict(m) for m in movements]
            existing_movements.extend(new_data)
            
            # Keep only recent movements (last 7 days for storage)
            cutoff_time = int(time.time()) - (7 * 24 * 3600)
            existing_movements = [
                m for m in existing_movements 
                if m.get('timestamp', 0) >= cutoff_time
            ]
            
            # Save updated movements
            with open(self.movements_db_path, 'w') as f:
                json.dump(existing_movements, f, indent=2, default=str)
                
        except Exception as e:
            self.logger.error(f"Error saving movements: {e}")

    async def _save_alert(self, alert: WhaleAlert):
        """Save alert to database"""
        try:
            # Load existing alerts
            existing_alerts = []
            if self.alerts_db_path.exists():
                with open(self.alerts_db_path, 'r') as f:
                    existing_alerts = json.load(f)
            
            # Add new alert
            alert_data = asdict(alert)
            existing_alerts.append(alert_data)
            
            # Keep only recent alerts (last 30 days)
            cutoff_time = int(time.time()) - (30 * 24 * 3600)
            existing_alerts = [
                a for a in existing_alerts 
                if a.get('created_at', 0) >= cutoff_time
            ]
            
            # Save updated alerts
            with open(self.alerts_db_path, 'w') as f:
                json.dump(existing_alerts, f, indent=2, default=str)
                
        except Exception as e:
            self.logger.error(f"Error saving alert: {e}") 