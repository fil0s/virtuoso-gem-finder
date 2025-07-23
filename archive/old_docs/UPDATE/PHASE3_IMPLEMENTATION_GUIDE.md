# Phase 3: Predictive Optimization Implementation (Week 3)

## Prerequisites
✅ Phase 1 completed and tested (all bugs fixed)
✅ Phase 2 completed and tested (trend + relative strength working)
✅ System discovering tokens with improved quality
✅ Birdeye API key working

---

## 🎯 Phase 3 Overview

Phase 3 transforms the token discovery system from reactive to predictive by:
- **Forward Return Backtesting**: Track actual performance of discovered tokens
- **Filter Optimization**: Data-driven optimization of filter thresholds
- **Predictive Validation**: Ensure filters actually predict positive returns
- **Systematic Learning**: Continuous improvement based on results

---

## 🔧 Task 3.1: Implement Forward Return Backtester

### Step 1: Create Database Schema
**Create File:** `database/forward_returns_schema.sql`

```sql
-- Forward returns tracking database schema
CREATE TABLE IF NOT EXISTS discovered_tokens (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    token_address TEXT NOT NULL,
    symbol TEXT,
    discovery_timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
    discovery_price REAL,
    liquidity REAL,
    volume_24h REAL,
    market_cap REAL,
    holders INTEGER,
    quick_score REAL,
    medium_score REAL,
    final_score REAL,
    trend_score REAL,
    rs_score REAL,
    whale_score REAL,
    social_score REAL,
    passed_quick_filter BOOLEAN,
    passed_trend_filter BOOLEAN,
    passed_rs_filter BOOLEAN,
    passed_final_filter BOOLEAN,
    alert_generated BOOLEAN DEFAULT FALSE
);

CREATE TABLE IF NOT EXISTS forward_returns (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    token_id INTEGER,
    timeframe TEXT, -- '1h', '4h', '24h', '7d'
    return_percentage REAL,
    price_at_measurement REAL,
    measurement_timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (token_id) REFERENCES discovered_tokens (id)
);

CREATE TABLE IF NOT EXISTS filter_performance (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    filter_name TEXT,
    threshold_value REAL,
    date_tested DATE,
    tokens_passed INTEGER,
    avg_return_1h REAL,
    avg_return_4h REAL,
    avg_return_24h REAL,
    win_rate_1h REAL,
    win_rate_4h REAL,
    win_rate_24h REAL,
    sharpe_ratio REAL,
    max_drawdown REAL
);

-- Indexes for performance
CREATE INDEX IF NOT EXISTS idx_token_address ON discovered_tokens(token_address);
CREATE INDEX IF NOT EXISTS idx_discovery_timestamp ON discovered_tokens(discovery_timestamp);
CREATE INDEX IF NOT EXISTS idx_filter_performance_date ON filter_performance(date_tested);
```

### Step 2: Create Forward Return Backtester
**Create File:** `services/forward_return_backtester.py`

```python
import asyncio
import aiohttp
import aiosqlite
import logging
import statistics
from typing import Dict, List, Optional, Tuple
from datetime import datetime, timedelta
import os
import json

logger = logging.getLogger(__name__)

class ForwardReturnBacktester:
    """Systematic backtesting and optimization of filter effectiveness"""
    
    def __init__(self, birdeye_api_key: str, db_path: str = "data/forward_returns.db"):
        self.api_key = birdeye_api_key
        self.db_path = db_path
        self.base_url = "https://public-api.birdeye.so"
        
        # Measurement timeframes
        self.measurement_timeframes = ['1h', '4h', '24h', '7d']
        
        # Ensure database directory exists
        os.makedirs(os.path.dirname(db_path), exist_ok=True)
        
    async def initialize_database(self):
        """Initialize database with schema"""
        async with aiosqlite.connect(self.db_path) as db:
            # Read and execute schema
            schema_path = "database/forward_returns_schema.sql"
            if os.path.exists(schema_path):
                with open(schema_path, 'r') as f:
                    schema_sql = f.read()
                await db.executescript(schema_sql)
            else:
                # Inline schema if file doesn't exist
                await self._create_tables(db)
            await db.commit()
        logger.info(f"Database initialized at {self.db_path}")
    
    async def _create_tables(self, db):
        """Create database tables inline"""
        await db.execute("""
            CREATE TABLE IF NOT EXISTS discovered_tokens (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                token_address TEXT NOT NULL,
                symbol TEXT,
                discovery_timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                discovery_price REAL,
                liquidity REAL,
                volume_24h REAL,
                market_cap REAL,
                holders INTEGER,
                quick_score REAL,
                medium_score REAL,
                final_score REAL,
                trend_score REAL,
                rs_score REAL,
                whale_score REAL,
                social_score REAL,
                passed_quick_filter BOOLEAN,
                passed_trend_filter BOOLEAN,
                passed_rs_filter BOOLEAN,
                passed_final_filter BOOLEAN,
                alert_generated BOOLEAN DEFAULT FALSE
            )
        """)
        
        await db.execute("""
            CREATE TABLE IF NOT EXISTS forward_returns (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                token_id INTEGER,
                timeframe TEXT,
                return_percentage REAL,
                price_at_measurement REAL,
                measurement_timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (token_id) REFERENCES discovered_tokens (id)
            )
        """)
        
        await db.execute("""
            CREATE TABLE IF NOT EXISTS filter_performance (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                filter_name TEXT,
                threshold_value REAL,
                date_tested DATE,
                tokens_passed INTEGER,
                avg_return_1h REAL,
                avg_return_4h REAL,
                avg_return_24h REAL,
                win_rate_1h REAL,
                win_rate_4h REAL,
                win_rate_24h REAL,
                sharpe_ratio REAL,
                max_drawdown REAL
            )
        """)
    
    async def track_discovered_token(self, token_data: Dict) -> int:
        """Store discovered token for future tracking"""
        
        async with aiosqlite.connect(self.db_path) as db:
            cursor = await db.execute("""
                INSERT INTO discovered_tokens (
                    token_address, symbol, discovery_price, liquidity, volume_24h,
                    market_cap, holders, quick_score, medium_score, final_score,
                    trend_score, rs_score, whale_score, social_score,
                    passed_quick_filter, passed_trend_filter, passed_rs_filter,
                    passed_final_filter, alert_generated
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                token_data.get('address'),
                token_data.get('symbol'),
                token_data.get('current_price', 0),
                token_data.get('liquidity', 0),
                token_data.get('volume_24h', 0),
                token_data.get('market_cap', 0),
                token_data.get('holders', 0),
                token_data.get('quick_score', 0),
                token_data.get('medium_score', 0),
                token_data.get('final_score', 0),
                token_data.get('trend_score', 0),
                token_data.get('rs_score', 0),
                token_data.get('whale_score', 0),
                token_data.get('social_score', 0),
                token_data.get('passed_quick_filter', False),
                token_data.get('passed_trend_filter', False),
                token_data.get('passed_rs_filter', False),
                token_data.get('passed_final_filter', False),
                token_data.get('alert_generated', False)
            ))
            
            token_id = cursor.lastrowid
            await db.commit()
            
        logger.debug(f"Tracked token {token_data.get('symbol')} with ID {token_id}")
        return token_id
    
    async def measure_forward_returns(self, lookback_hours: int = 24) -> Dict:
        """Measure forward returns for tokens discovered in the lookback period"""
        
        cutoff_time = datetime.now() - timedelta(hours=lookback_hours)
        
        async with aiosqlite.connect(self.db_path) as db:
            # Get tokens that need return measurement
            cursor = await db.execute("""
                SELECT id, token_address, symbol, discovery_timestamp, discovery_price
                FROM discovered_tokens 
                WHERE discovery_timestamp > ?
                AND id NOT IN (
                    SELECT DISTINCT token_id 
                    FROM forward_returns 
                    WHERE timeframe = '24h'
                )
            """, (cutoff_time,))
            
            tokens_to_measure = await cursor.fetchall()
        
        logger.info(f"Measuring forward returns for {len(tokens_to_measure)} tokens")
        
        results = {
            'tokens_measured': 0,
            'successful_measurements': 0,
            'average_returns': {},
            'measurement_errors': []
        }
        
        for token_id, address, symbol, discovery_time, discovery_price in tokens_to_measure:
            try:
                # Get current price
                current_price = await self._fetch_current_price(address)
                
                if current_price and discovery_price and discovery_price > 0:
                    # Calculate returns for each timeframe
                    discovery_dt = datetime.fromisoformat(discovery_time.replace('Z', '+00:00'))
                    time_elapsed = (datetime.now() - discovery_dt).total_seconds() / 3600
                    
                    for timeframe in self.measurement_timeframes:
                        timeframe_hours = self._timeframe_to_hours(timeframe)
                        
                        if time_elapsed >= timeframe_hours:
                            return_pct = ((current_price - discovery_price) / discovery_price) * 100
                            
                            # Store return measurement
                            await self._store_return_measurement(
                                token_id, timeframe, return_pct, current_price
                            )
                    
                    results['successful_measurements'] += 1
                    
                results['tokens_measured'] += 1
                
            except Exception as e:
                logger.error(f"Error measuring returns for {symbol}: {e}")
                results['measurement_errors'].append(f"{symbol}: {str(e)}")
        
        # Calculate aggregate statistics
        results['average_returns'] = await self._calculate_aggregate_returns()
        
        logger.info(f"Forward return measurement complete: "
                   f"{results['successful_measurements']}/{results['tokens_measured']} successful")
        
        return results
    
    async def _fetch_current_price(self, token_address: str) -> Optional[float]:
        """Fetch current price from Birdeye API"""
        
        endpoint = f"{self.base_url}/defi/price"
        params = {'address': token_address}
        headers = {'X-API-KEY': self.api_key}
        
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(endpoint, params=params, headers=headers) as response:
                    if response.status == 200:
                        data = await response.json()
                        return float(data.get('data', {}).get('value', 0))
                    else:
                        logger.warning(f"Price fetch failed for {token_address}: {response.status}")
                        return None
        except Exception as e:
            logger.error(f"Error fetching price for {token_address}: {e}")
            return None
    
    def _timeframe_to_hours(self, timeframe: str) -> float:
        """Convert timeframe string to hours"""
        mapping = {
            '1h': 1,
            '4h': 4,
            '24h': 24,
            '7d': 168
        }
        return mapping.get(timeframe, 1)
    
    async def _store_return_measurement(self, token_id: int, timeframe: str, 
                                      return_pct: float, current_price: float):
        """Store return measurement in database"""
        
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute("""
                INSERT INTO forward_returns (token_id, timeframe, return_percentage, price_at_measurement)
                VALUES (?, ?, ?, ?)
            """, (token_id, timeframe, return_pct, current_price))
            await db.commit()
    
    async def _calculate_aggregate_returns(self) -> Dict:
        """Calculate aggregate return statistics"""
        
        async with aiosqlite.connect(self.db_path) as db:
            results = {}
            
            for timeframe in self.measurement_timeframes:
                cursor = await db.execute("""
                    SELECT return_percentage 
                    FROM forward_returns 
                    WHERE timeframe = ?
                    AND measurement_timestamp > datetime('now', '-30 days')
                """, (timeframe,))
                
                returns = [row[0] for row in await cursor.fetchall()]
                
                if returns:
                    results[timeframe] = {
                        'mean': statistics.mean(returns),
                        'median': statistics.median(returns),
                        'std': statistics.stdev(returns) if len(returns) > 1 else 0,
                        'win_rate': len([r for r in returns if r > 0]) / len(returns) * 100,
                        'count': len(returns),
                        'max': max(returns),
                        'min': min(returns)
                    }
                else:
                    results[timeframe] = {'mean': 0, 'median': 0, 'std': 0, 'win_rate': 0, 'count': 0}
        
        return results
    
    async def optimize_filter_thresholds(self, target_metric: str = 'sharpe_ratio') -> Dict:
        """Optimize filter thresholds based on forward return performance"""
        
        logger.info(f"Optimizing filter thresholds targeting {target_metric}")
        
        # Define filter parameters to optimize
        filters_to_optimize = {
            'trend_score_threshold': {'current': 60, 'test_range': [40, 50, 60, 70, 80]},
            'rs_percentile_threshold': {'current': 60, 'test_range': [40, 50, 60, 70, 80]},
            'final_score_threshold': {'current': 70, 'test_range': [60, 65, 70, 75, 80]},
            'liquidity_threshold': {'current': 500000, 'test_range': [250000, 500000, 1000000, 2000000]}
        }
        
        optimization_results = {}
        
        for filter_name, config in filters_to_optimize.items():
            logger.info(f"Optimizing {filter_name}")
            
            filter_results = []
            
            for threshold in config['test_range']:
                # Test this threshold
                perf_metrics = await self._test_filter_threshold(filter_name, threshold)
                filter_results.append({
                    'threshold': threshold,
                    'metrics': perf_metrics
                })
            
            # Find optimal threshold
            optimal = self._find_optimal_threshold(filter_results, target_metric)
            optimization_results[filter_name] = optimal
            
            # Store optimization results
            await self._store_optimization_results(filter_name, filter_results)
        
        logger.info("Filter optimization complete")
        return optimization_results
    
    async def _test_filter_threshold(self, filter_name: str, threshold: float) -> Dict:
        """Test a specific filter threshold and calculate performance metrics"""
        
        async with aiosqlite.connect(self.db_path) as db:
            # Build query based on filter type
            if filter_name == 'trend_score_threshold':
                query = """
                    SELECT dt.id 
                    FROM discovered_tokens dt
                    WHERE dt.trend_score >= ?
                    AND dt.discovery_timestamp > datetime('now', '-30 days')
                """
            elif filter_name == 'rs_percentile_threshold':
                query = """
                    SELECT dt.id 
                    FROM discovered_tokens dt  
                    WHERE dt.rs_score >= ?
                    AND dt.discovery_timestamp > datetime('now', '-30 days')
                """
            elif filter_name == 'final_score_threshold':
                query = """
                    SELECT dt.id 
                    FROM discovered_tokens dt
                    WHERE dt.final_score >= ?
                    AND dt.discovery_timestamp > datetime('now', '-30 days')
                """
            elif filter_name == 'liquidity_threshold':
                query = """
                    SELECT dt.id 
                    FROM discovered_tokens dt
                    WHERE dt.liquidity >= ?
                    AND dt.discovery_timestamp > datetime('now', '-30 days')
                """
            else:
                return {}
            
            cursor = await db.execute(query, (threshold,))
            token_ids = [row[0] for row in await cursor.fetchall()]
            
            if not token_ids:
                return {'tokens_passed': 0, 'avg_return_24h': 0, 'win_rate_24h': 0, 'sharpe_ratio': 0}
            
            # Get returns for these tokens
            token_ids_str = ','.join(map(str, token_ids))
            cursor = await db.execute(f"""
                SELECT return_percentage 
                FROM forward_returns 
                WHERE token_id IN ({token_ids_str})
                AND timeframe = '24h'
            """)
            
            returns = [row[0] for row in await cursor.fetchall()]
            
            if not returns:
                return {'tokens_passed': len(token_ids), 'avg_return_24h': 0, 'win_rate_24h': 0, 'sharpe_ratio': 0}
            
            # Calculate performance metrics
            avg_return = statistics.mean(returns)
            win_rate = len([r for r in returns if r > 0]) / len(returns) * 100
            std_return = statistics.stdev(returns) if len(returns) > 1 else 0
            sharpe_ratio = avg_return / std_return if std_return > 0 else 0
            
            return {
                'tokens_passed': len(token_ids),
                'avg_return_24h': avg_return,
                'win_rate_24h': win_rate,
                'sharpe_ratio': sharpe_ratio,
                'return_count': len(returns)
            }
    
    def _find_optimal_threshold(self, filter_results: List[Dict], target_metric: str) -> Dict:
        """Find optimal threshold based on target metric"""
        
        if not filter_results:
            return {}
        
        # Sort by target metric (higher is better for sharpe_ratio, win_rate, avg_return)
        sorted_results = sorted(
            filter_results, 
            key=lambda x: x['metrics'].get(target_metric, 0), 
            reverse=True
        )
        
        optimal = sorted_results[0]
        
        return {
            'optimal_threshold': optimal['threshold'],
            'optimal_metrics': optimal['metrics'],
            'improvement_over_current': optimal['metrics'].get(target_metric, 0),
            'all_results': filter_results
        }
    
    async def _store_optimization_results(self, filter_name: str, results: List[Dict]):
        """Store optimization results in database"""
        
        async with aiosqlite.connect(self.db_path) as db:
            for result in results:
                await db.execute("""
                    INSERT INTO filter_performance (
                        filter_name, threshold_value, date_tested, tokens_passed,
                        avg_return_24h, win_rate_24h, sharpe_ratio
                    ) VALUES (?, ?, ?, ?, ?, ?, ?)
                """, (
                    filter_name,
                    result['threshold'],
                    datetime.now().date(),
                    result['metrics'].get('tokens_passed', 0),
                    result['metrics'].get('avg_return_24h', 0),
                    result['metrics'].get('win_rate_24h', 0),
                    result['metrics'].get('sharpe_ratio', 0)
                ))
            await db.commit()
    
    async def generate_performance_report(self, days_back: int = 30) -> Dict:
        """Generate comprehensive performance report"""
        
        logger.info(f"Generating {days_back}-day performance report")
        
        async with aiosqlite.connect(self.db_path) as db:
            # Overall discovery metrics
            cursor = await db.execute("""
                SELECT 
                    COUNT(*) as total_discovered,
                    COUNT(CASE WHEN passed_final_filter = 1 THEN 1 END) as passed_final,
                    COUNT(CASE WHEN alert_generated = 1 THEN 1 END) as alerts_generated,
                    AVG(final_score) as avg_final_score,
                    AVG(trend_score) as avg_trend_score,
                    AVG(rs_score) as avg_rs_score
                FROM discovered_tokens 
                WHERE discovery_timestamp > datetime('now', '-{} days')
            """.format(days_back))
            
            discovery_stats = await cursor.fetchone()
            
            # Return performance by filter stage
            filter_performance = {}
            
            for filter_stage in ['passed_quick_filter', 'passed_trend_filter', 'passed_rs_filter', 'passed_final_filter']:
                cursor = await db.execute(f"""
                    SELECT AVG(fr.return_percentage), COUNT(fr.return_percentage)
                    FROM discovered_tokens dt
                    JOIN forward_returns fr ON dt.id = fr.token_id
                    WHERE dt.{filter_stage} = 1 
                    AND fr.timeframe = '24h'
                    AND dt.discovery_timestamp > datetime('now', '-{days_back} days')
                """)
                
                result = await cursor.fetchone()
                filter_performance[filter_stage] = {
                    'avg_return_24h': result[0] if result[0] else 0,
                    'token_count': result[1] if result[1] else 0
                }
            
            # Top and bottom performers
            cursor = await db.execute("""
                SELECT dt.symbol, dt.final_score, fr.return_percentage
                FROM discovered_tokens dt
                JOIN forward_returns fr ON dt.id = fr.token_id
                WHERE fr.timeframe = '24h'
                AND dt.discovery_timestamp > datetime('now', '-{} days')
                ORDER BY fr.return_percentage DESC
                LIMIT 10
            """.format(days_back))
            
            top_performers = await cursor.fetchall()
            
            cursor = await db.execute("""
                SELECT dt.symbol, dt.final_score, fr.return_percentage
                FROM discovered_tokens dt
                JOIN forward_returns fr ON dt.id = fr.token_id
                WHERE fr.timeframe = '24h'
                AND dt.discovery_timestamp > datetime('now', '-{} days')
                ORDER BY fr.return_percentage ASC
                LIMIT 10
            """.format(days_back))
            
            bottom_performers = await cursor.fetchall()
        
        report = {
            'report_period_days': days_back,
            'discovery_summary': {
                'total_discovered': discovery_stats[0],
                'passed_final_filter': discovery_stats[1],
                'alerts_generated': discovery_stats[2],
                'avg_final_score': discovery_stats[3],
                'avg_trend_score': discovery_stats[4],
                'avg_rs_score': discovery_stats[5],
                'final_filter_pass_rate': (discovery_stats[1] / discovery_stats[0] * 100) if discovery_stats[0] > 0 else 0
            },
            'filter_performance': filter_performance,
            'top_performers': [
                {'symbol': row[0], 'score': row[1], 'return_24h': row[2]} 
                for row in top_performers
            ],
            'bottom_performers': [
                {'symbol': row[0], 'score': row[1], 'return_24h': row[2]} 
                for row in bottom_performers
            ],
            'aggregate_returns': await self._calculate_aggregate_returns(),
            'generated_at': datetime.now().isoformat()
        }
        
        logger.info("Performance report generated successfully")
        return report
```

### ✅ Checkpoint 3.1: Test Forward Return Backtester
**Create Test File:** `tests/test_forward_return_backtester.py`

```python
import asyncio
import sys
import os
import tempfile
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from services.forward_return_backtester import ForwardReturnBacktester

async def test_forward_return_backtester():
    """Test forward return backtesting system"""
    
    # Use temporary database for testing
    with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as tmp_db:
        db_path = tmp_db.name
    
    try:
        backtester = ForwardReturnBacktester("test_api_key", db_path)
        
        # Test 1: Database initialization
        await backtester.initialize_database()
        print("✅ Database initialized successfully")
        
        # Test 2: Track token
        test_token = {
            'address': 'test_address_123',
            'symbol': 'TEST',
            'current_price': 100.0,
            'liquidity': 1000000,
            'volume_24h': 500000,
            'final_score': 75,
            'trend_score': 65,
            'rs_score': 70,
            'passed_final_filter': True,
            'alert_generated': True
        }
        
        token_id = await backtester.track_discovered_token(test_token)
        assert token_id > 0, "Token tracking should return valid ID"
        print(f"✅ Token tracked with ID: {token_id}")
        
        # Test 3: Store return measurement
        await backtester._store_return_measurement(token_id, '24h', 15.5, 115.5)
        print("✅ Return measurement stored")
        
        # Test 4: Calculate aggregate returns
        agg_returns = await backtester._calculate_aggregate_returns()
        assert '24h' in agg_returns, "Should have 24h return data"
        print(f"✅ Aggregate returns: {agg_returns['24h']['mean']:.2f}%")
        
        # Test 5: Generate performance report
        report = await backtester.generate_performance_report(days_back=1)
        assert 'discovery_summary' in report, "Report should have discovery summary"
        print("✅ Performance report generated")
        
        print("🎉 All forward return backtester tests passed!")
        
    finally:
        # Cleanup
        if os.path.exists(db_path):
            os.unlink(db_path)

if __name__ == "__main__":
    asyncio.run(test_forward_return_backtester())
```

---

## 🔧 Task 3.2: Integrate Backtesting into Discovery Pipeline

### Step 1: Update Early Token Detection Service
**File:** `services/early_token_detection.py`

**ADD IMPORT:**
```python
from services.forward_return_backtester import ForwardReturnBacktester
```

**ADD to `__init__`:**
```python
# Initialize backtester
self.backtester = ForwardReturnBacktester(
    birdeye_api_key=os.getenv('BIRDEYE_API_KEY'),
    db_path=os.getenv('FORWARD_RETURNS_DB_PATH', 'data/forward_returns.db')
)
asyncio.create_task(self.backtester.initialize_database())
logger.info("Initialized ForwardReturnBacktester")
```

**ADD new method:**
```python
async def track_discovered_tokens(self, tokens: List[Dict], stage: str):
    """Track tokens at different pipeline stages for backtesting"""
    
    for token in tokens:
        try:
            # Mark which stage this token reached
            token[f'passed_{stage}_filter'] = True
            
            # Track in backtester
            await self.backtester.track_discovered_token(token)
            
        except Exception as e:
            logger.error(f"Error tracking token {token.get('symbol', 'UNKNOWN')}: {e}")
```

**UPDATE discovery pipeline:**
```python
async def discover_tokens(self) -> List[Dict]:
    """Main discovery pipeline with backtesting integration"""
    
    logger.info("🔍 Starting token discovery with backtesting")
    
    # Step 1: Initial discovery
    initial_tokens = await self._fetch_initial_candidates()
    logger.info(f"Initial candidates: {len(initial_tokens)}")
    
    # Step 2: Quick scoring
    quick_filtered = await self._apply_quick_scoring(initial_tokens)
    await self.track_discovered_tokens(quick_filtered, 'quick')
    logger.info(f"After quick scoring: {len(quick_filtered)}")
    
    # Step 3: Trend confirmation
    trend_confirmed = await self.apply_trend_confirmation_filter(quick_filtered)
    await self.track_discovered_tokens(trend_confirmed, 'trend')
    logger.info(f"After trend confirmation: {len(trend_confirmed)}")
    
    # Step 4: Relative strength
    rs_filtered = await self.rs_analyzer.filter_by_relative_strength(trend_confirmed)
    await self.track_discovered_tokens(rs_filtered, 'rs')
    logger.info(f"After relative strength: {len(rs_filtered)}")
    
    # Step 5: Final analysis
    final_tokens = await self._apply_full_analysis(rs_filtered)
    await self.track_discovered_tokens(final_tokens, 'final')
    logger.info(f"Final promising tokens: {len(final_tokens)}")
    
    return final_tokens
```

### Step 2: Create Monthly Optimization Job
**Create File:** `scripts/monthly_optimization.py`

```python
#!/usr/bin/env python3
"""Monthly filter optimization based on forward return backtesting"""

import asyncio
import logging
import os
import sys
import json
from datetime import datetime

# Add project root to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from services.forward_return_backtester import ForwardReturnBacktester

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def run_monthly_optimization():
    """Run comprehensive monthly optimization"""
    
    logger.info("🔧 Starting monthly filter optimization")
    
    # Initialize backtester
    api_key = os.getenv('BIRDEYE_API_KEY')
    if not api_key:
        logger.error("BIRDEYE_API_KEY not found in environment")
        return
    
    backtester = ForwardReturnBacktester(api_key)
    
    try:
        # Step 1: Measure recent forward returns
        logger.info("📊 Measuring forward returns for recent tokens")
        return_results = await backtester.measure_forward_returns(lookback_hours=168)  # 7 days
        logger.info(f"Measured returns for {return_results['successful_measurements']} tokens")
        
        # Step 2: Generate performance report
        logger.info("📋 Generating performance report")
        report = await backtester.generate_performance_report(days_back=30)
        
        # Save report
        report_path = f"data/performance_reports/monthly_report_{datetime.now().strftime('%Y_%m_%d')}.json"
        os.makedirs(os.path.dirname(report_path), exist_ok=True)
        
        with open(report_path, 'w') as f:
            json.dump(report, f, indent=2)
        
        logger.info(f"Performance report saved to {report_path}")
        
        # Step 3: Optimize filter thresholds
        logger.info("🎯 Optimizing filter thresholds")
        optimization_results = await backtester.optimize_filter_thresholds(target_metric='sharpe_ratio')
        
        # Save optimization results
        opt_path = f"data/optimization_results/optimization_{datetime.now().strftime('%Y_%m_%d')}.json"
        os.makedirs(os.path.dirname(opt_path), exist_ok=True)
        
        with open(opt_path, 'w') as f:
            json.dump(optimization_results, f, indent=2)
        
        logger.info(f"Optimization results saved to {opt_path}")
        
        # Step 4: Generate recommendations
        recommendations = generate_optimization_recommendations(optimization_results)
        
        logger.info("🎉 Monthly optimization complete!")
        logger.info("Recommendations:")
        for rec in recommendations:
            logger.info(f"  • {rec}")
        
        return {
            'return_measurement': return_results,
            'performance_report': report,
            'optimization_results': optimization_results,
            'recommendations': recommendations
        }
        
    except Exception as e:
        logger.error(f"Error in monthly optimization: {e}")
        raise

def generate_optimization_recommendations(optimization_results: Dict) -> List[str]:
    """Generate actionable recommendations from optimization results"""
    
    recommendations = []
    
    for filter_name, results in optimization_results.items():
        optimal_threshold = results.get('optimal_threshold')
        current_metrics = results.get('optimal_metrics', {})
        
        if optimal_threshold and current_metrics:
            sharpe_ratio = current_metrics.get('sharpe_ratio', 0)
            win_rate = current_metrics.get('win_rate_24h', 0)
            
            if sharpe_ratio > 1.0:
                recommendations.append(
                    f"✅ {filter_name}: Use threshold {optimal_threshold} "
                    f"(Sharpe: {sharpe_ratio:.2f}, Win Rate: {win_rate:.1f}%)"
                )
            elif sharpe_ratio > 0.5:
                recommendations.append(
                    f"⚠️ {filter_name}: Consider threshold {optimal_threshold} "
                    f"(Moderate performance: Sharpe {sharpe_ratio:.2f})"
                )
            else:
                recommendations.append(
                    f"❌ {filter_name}: Poor performance across all thresholds "
                    f"(Best Sharpe: {sharpe_ratio:.2f}) - Review filter logic"
                )
    
    return recommendations

if __name__ == "__main__":
    asyncio.run(run_monthly_optimization())
```

### ✅ Checkpoint 3.2: Test Integration
**Create Test File:** `tests/test_phase3_integration.py`

```python
import asyncio
import sys
import os
import tempfile
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from services.early_token_detection import EarlyTokenDetector
from services.forward_return_backtester import ForwardReturnBacktester

async def test_phase3_integration():
    """Test Phase 3 backtesting integration"""
    
    print("🧪 Testing Phase 3 Integration...")
    
    # Use temporary database
    with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as tmp_db:
        db_path = tmp_db.name
    
    try:
        # Test 1: Backtester initialization
        backtester = ForwardReturnBacktester("test_key", db_path)
        await backtester.initialize_database()
        print("✅ Backtester initialized")
        
        # Test 2: Token tracking
        test_token = {
            'address': 'test_123',
            'symbol': 'TEST',
            'current_price': 100,
            'final_score': 75,
            'passed_final_filter': True
        }
        
        token_id = await backtester.track_discovered_token(test_token)
        assert token_id > 0
        print("✅ Token tracking working")
        
        # Test 3: Filter optimization (mock)
        perf_metrics = await backtester._test_filter_threshold('final_score_threshold', 70)
        assert 'tokens_passed' in perf_metrics
        print("✅ Filter optimization logic working")
        
        # Test 4: Performance report generation
        report = await backtester.generate_performance_report(days_back=1)
        assert 'discovery_summary' in report
        print("✅ Performance reporting working")
        
        print("🎉 Phase 3 Integration Test PASSED!")
        print("📋 Ready for Phase 4 implementation")
        
    finally:
        if os.path.exists(db_path):
            os.unlink(db_path)

if __name__ == "__main__":
    asyncio.run(test_phase3_integration())
```

---

## Phase 3 Success Criteria Checklist

**Before proceeding to Phase 4, verify:**

- [ ] Database schema created and functional
- [ ] Token tracking working throughout pipeline
- [ ] Forward return measurement operational
- [ ] Filter optimization logic functional
- [ ] Monthly optimization script working
- [ ] Performance reports generating
- [ ] All Phase 3 tests pass

**Expected Improvements:**
- [ ] Forward return tracking for 100% of discovered tokens
- [ ] Monthly optimization cycles reducing false positives
- [ ] Data-driven filter threshold adjustments
- [ ] Improved Sharpe ratio of discovered tokens

---

*This completes Phase 3. Proceed to Phase 4 for monitoring and validation implementation.* 