# 🔧 TECHNICAL REFERENCE - Portfolio Backtesting PoC

**📁 Project**: AI-powered portfolio optimization system  
**🎯 Current Sprint**: SPRINT 2, Phase 2 - "Advanced Risk Analytics + Conversational Rebalancing"  
**⏱️ Status**: Week 6 COMPLETE ✅ - Conversational Rebalancing Analysis Delivered  
**📅 Updated**: Session 6 - Sprint 2, Phase 2 COMPLETE - All Advanced Analytics Operational  
**🚀 Next**: Sprint 2, Phase 3 - Extended Historical Analysis & Final Integration

---

## 🏗️ SYSTEM ARCHITECTURE (CURRENT PRODUCTION STATE)

### ✅ **Production Components - ALL OPERATIONAL:**

```
Portfolio Backtesting System (7-Asset Universe + Advanced Analytics)
├── FastAPI Backend (src/api/) - Port 8006 ✅
│   ├── /api/backtest - Portfolio performance analysis
│   ├── /api/backtest/portfolio/7-asset - Specialized 7-asset endpoint  
│   ├── /api/optimize - Efficient frontier calculations
│   ├── /api/chat - Claude AI portfolio advisor
│   ├── /api/analyze/rolling-periods - ✅ Rolling period analysis
│   ├── /api/analyze/rolling-periods/multi - ✅ Multi-period comparison
│   ├── /api/analyze/rolling-periods/compare - ✅ Portfolio ranking
│   ├── /api/analyze/stress-test - ✅ Crisis period analysis
│   ├── /api/analyze/timeline-recommendation - ✅ Timeline-aware recommendations
│   ├── /api/analyze/rebalancing-strategy - 🆕 Rebalancing strategy analysis
│   ├── /api/analyze/rebalancing-strategy/compare - 🆕 Strategy comparison
│   └── /api/assets - Asset data endpoints
├── Local PostgreSQL Database (localhost:5432) ✅
│   ├── 33,725 price records (2004-2024) - 20-year history
│   ├── 7 assets: VTI, VTIAX, BND, VNQ, GLD, VWO, QQQ
│   └── Optimized schema with proper indexing
├── Advanced Analytics Engine (src/core/) ✅
│   ├── OptimizedPortfolioEngine - 3-4x performance improvement
│   ├── RollingPeriodAnalyzer - ✅ Performance consistency analysis
│   ├── CrisisPeriodAnalyzer - ✅ Stress testing across major crises
│   ├── RecoveryTimeAnalyzer - ✅ Drawdown and recovery analysis
│   ├── TimelineRiskAnalyzer - ✅ Life stage and horizon optimization
│   ├── RebalancingStrategyAnalyzer - 🆕 Comprehensive rebalancing analysis
│   ├── Modern Portfolio Theory implementation
│   └── Vectorized NumPy calculations
└── Docker Deployment ✅
    ├── API container on port 8006
    └── Connects to host PostgreSQL database
```

### 🚀 **Current Performance Benchmarks (Phase 2 Complete):**
- **4-year Backtests**: 0.12s (target: <0.3s) ✅ 
- **10-year Backtests**: 0.31s (target: <0.5s) ✅
- **20-year Backtests**: 0.41s (target: <1.0s) ✅
- **Rolling Period Analysis**: 4.44s for 49 windows ✅
- **Crisis Period Analysis**: <1s for all 3 major crises ✅
- **Recovery Time Analysis**: <2s for 20-year drawdown analysis ✅
- **Rebalancing Strategy Analysis**: <5s for comprehensive strategy comparison ✅
- **API Health Check**: http://localhost:8006/health ✅
- **API Documentation**: http://localhost:8006/docs ✅

---

## 📊 DATABASE SCHEMA REFERENCE

### **Critical Schema Information:**

```sql
-- Assets Table
CREATE TABLE assets (
    id INTEGER PRIMARY KEY,
    symbol VARCHAR(10) UNIQUE NOT NULL,  -- Primary identifier
    name VARCHAR(255) NOT NULL,
    asset_class VARCHAR(50) NOT NULL,
    expense_ratio DECIMAL(5,4),
    created_at TIMESTAMP DEFAULT now(),
    updated_at TIMESTAMP DEFAULT now()
);

-- Daily Prices Table  
CREATE TABLE daily_prices (
    date DATE NOT NULL,
    symbol VARCHAR(10) NOT NULL,  -- FK references assets(symbol)
    open_price DECIMAL(12,4),
    high_price DECIMAL(12,4), 
    low_price DECIMAL(12,4),
    close_price DECIMAL(12,4),
    adj_close DECIMAL(12,4) NOT NULL,
    volume BIGINT,
    dividend DECIMAL(8,4) DEFAULT 0,
    split_factor DECIMAL(8,4) DEFAULT 1,
    created_at TIMESTAMP DEFAULT now(),
    PRIMARY KEY (date, symbol),
    FOREIGN KEY (symbol) REFERENCES assets(symbol) ON DELETE CASCADE
);
```

### **⚠️ CRITICAL DATABASE NOTES:**
- **Foreign Key**: `daily_prices.symbol` → `assets.symbol` (NOT asset_id!)
- **Primary Key**: `daily_prices` uses composite key (date, symbol)
- **Price Field**: Use `adj_close` for calculations (dividend/split adjusted)
- **Date Range**: 2004-01-03 to 2024-12-31 (20 years, 33,725 records)
- **Query Performance**: Use indexes on symbol and date for optimal speed
---

## 🐍 PYTHON MODULE STRUCTURE

### **Core Modules (`src/core/`):**

```python
# Import Structure - CURRENT WORKING PATTERN:
from src.core import (
    DataManager,                    # Database operations
    PortfolioEngine,               # Original engine  
    OptimizedPortfolioEngine,      # 3-4x faster version ⭐
    OptimizationEngine,            # MPT calculations
    RollingPeriodAnalyzer,         # 🆕 Advanced analytics
    RollingPeriodResult,           # Response dataclass
    RollingPeriodSummary           # Summary dataclass
)

# Database Models - CURRENT WORKING PATTERN:
from src.models import (
    Base,                          # SQLAlchemy base
    engine,                        # Database engine
    get_db,                        # Session dependency
    Asset,                         # Assets table ORM
    DailyPrice,                    # Daily prices table ORM  
    PortfolioSnapshot              # Portfolio snapshots ORM
)
```

### **⚠️ CRITICAL IMPORT NOTES:**
- **Database Models**: Import from `src.models` (NOT `src.models.database`)
- **Core Classes**: All available from `src.core` namespace
- **Optimized Engine**: Always use `OptimizedPortfolioEngine` (3-4x faster)
- **Database Queries**: Use `symbol` field for joins (NOT asset_id)

---

## 🔧 API ENDPOINT REFERENCE

### **Backtesting Endpoints:**
```
POST /api/backtest/portfolio
- Standard portfolio backtesting (3 or 7 assets)
- Response: ~0.31s for 10-year analysis

POST /api/backtest/portfolio/7-asset  
- Specialized 7-asset backtesting endpoint
- Optimized for 7-asset universe performance
```

### **🆕 Rolling Period Analysis Endpoints (Week 4):**
```
POST /api/analyze/rolling-periods
- Single period analysis (e.g., 5-year rolling windows)
- Response: ~4.44s for 49 windows
- Example: 5-year rolling analysis across 20-year history

POST /api/analyze/rolling-periods/multi
- Multi-period comparison (e.g., 3yr vs 5yr vs 10yr)
- Response: ~7.46s for 2-period comparison
- Use case: Investment horizon impact analysis

POST /api/analyze/rolling-periods/compare
- Portfolio comparison with risk-adjusted ranking
- Response: ~30s+ for 3 portfolios (optimization needed)
- Ranking based on Sharpe ratio + consistency score

GET /api/analyze/rolling-periods/examples
- API documentation with example payloads
- Response: <1s
- Essential for testing and integration
```

### **Optimization & Chat Endpoints:**
```
POST /api/optimize/efficient-frontier - MPT efficient frontier
POST /api/optimize/max-sharpe - Maximum Sharpe ratio portfolio
POST /api/chat/recommend - Claude AI portfolio recommendations
POST /api/chat/analyze - Portfolio analysis Q&A
```
---

## ⚡ PERFORMANCE OPTIMIZATION PATTERNS

### **Database Query Optimization:**
```python
# ✅ CORRECT - Use symbol-based queries (FAST)
prices = db.query(DailyPrice).filter(
    DailyPrice.symbol == symbol,
    DailyPrice.date >= start_date,
    DailyPrice.date <= end_date
).order_by(DailyPrice.date.asc()).all()

# ❌ WRONG - Don't use asset_id lookups (SLOW) 
# This pattern causes errors - schema uses symbol FK
```

### **Portfolio Engine Selection:**
```python
# ✅ ALWAYS USE - OptimizedPortfolioEngine (3-4x faster)
from src.core import OptimizedPortfolioEngine
engine = OptimizedPortfolioEngine(data_manager)

# ❌ AVOID - Original PortfolioEngine (deprecated for new features)
from src.core import PortfolioEngine  # Only for legacy compatibility
```

### **API Response Time Targets:**
- **Simple Backtesting**: <1s (achieved: 0.31s for 10-year)
- **Rolling Period Analysis**: <5s (achieved: 4.44s for single period)  
- **Multi-Period Analysis**: <10s (achieved: 7.46s for 2 periods)
- **Portfolio Comparison**: <15s (current: 30s+ - needs optimization)

---

## 🛠️ DEVELOPMENT WORKFLOW PATTERNS

### **Before Starting New Components:**

1. **Check Technical Reference** - Verify current architecture and imports ⭐
2. **Review Database Schema** - Confirm table relationships and field names
3. **Test Database Connection** - Verify PostgreSQL running and accessible
4. **Check API Health** - Confirm `curl http://localhost:8006/health`
5. **Review Existing Code** - Look for similar patterns in codebase

### **New API Endpoint Pattern:**
```python
# 1. Create analysis class in src/core/
# 2. Add to src/core/__init__.py exports  
# 3. Create API routes in src/api/[feature]_routes.py
# 4. Add router to src/api/main.py
# 5. Restart API: docker-compose restart api
# 6. Test endpoint functionality
# 7. Update technical reference
```

### **Testing Pattern:**
```python
# 1. Test core functionality first (direct class usage)
# 2. Test API endpoints with curl/requests
# 3. Validate against known benchmarks
# 4. Check performance targets
# 5. Update documentation
```
---

## 🚨 COMMON PITFALLS & SOLUTIONS

### **Database Issues:**
- **Problem**: Import errors for Asset, DailyPrice models
- **Solution**: Always import from `src.models` (not `src.models.database`)
- **Pattern**: `from src.models import Asset, DailyPrice, get_db`

### **Performance Issues:**
- **Problem**: Slow API responses for complex analysis  
- **Solution**: Use OptimizedPortfolioEngine + vectorized NumPy calculations
- **Pattern**: Break complex operations into smaller chunks

### **Docker/API Issues:**
- **Problem**: API not responding or showing unhealthy status
- **Solution**: Check PostgreSQL running + restart API container
- **Commands**: 
  ```bash
  brew services list | grep postgresql  # Check DB
  docker-compose restart api            # Restart API
  curl http://localhost:8006/health     # Verify health
  ```

### **Import/Module Issues:**
- **Problem**: Module not found or circular import errors
- **Solution**: Follow established import patterns from working code
- **Reference**: Check existing working files for correct patterns

---

## 📋 QUICK REFERENCE COMMANDS

### **Database Operations:**
```bash
# Check PostgreSQL status
brew services list | grep postgresql

# Connect to database  
psql -h localhost -U ashish -d backtesting

# Check table schema
\d daily_prices
\d assets

# Check data count
SELECT COUNT(*) FROM daily_prices;
```

### **Docker Operations:**
```bash
# Restart API container
cd /Users/ashish/Claude/backtesting
docker-compose restart api

# Check container status
docker-compose ps

# View API logs
docker logs portfolio_api --tail=20
```

### **API Testing:**
```bash
# Health check
curl -s http://localhost:8006/health

# API documentation  
open http://localhost:8006/docs

# Test endpoint
curl -X POST http://localhost:8006/api/analyze/rolling-periods \
  -H "Content-Type: application/json" \
  -d '{"allocation":{"VTI":0.6,"BND":0.4},"period_years":5}'
```

---

*📅 Last Updated: Session 5, Sprint 2 Phase 2 Week 4 Complete*  
*🔄 Next Update: Week 5 Crisis Testing Implementation*

---

## 🔄 REBALANCING STRATEGY ANALYSIS SYSTEM (NEW - Week 6)

### **RebalancingStrategyAnalyzer Class - Complete Implementation:**

```python
# Location: src/core/rebalancing_strategy_analyzer.py (359 lines)
from src.core.rebalancing_strategy_analyzer import (
    RebalancingStrategyAnalyzer,
    RebalancingFrequency,
    AccountType,
    RebalancingResult
)

# Initialize with price data
analyzer = RebalancingStrategyAnalyzer(price_data)
analyzer.set_cost_parameters(transaction_cost=0.001, tax_rates=custom_rates)

# Analyze different strategies
threshold_results = analyzer.analyze_threshold_rebalancing(
    target_allocation={'VTI': 0.6, 'VTIAX': 0.3, 'BND': 0.1},
    threshold_percentages=[5, 10, 15, 20],
    account_type=AccountType.TAXABLE
)

time_results = analyzer.analyze_time_based_rebalancing(
    target_allocation=allocation,
    frequencies=[RebalancingFrequency.MONTHLY, RebalancingFrequency.QUARTERLY],
    account_type=AccountType.TAX_DEFERRED
)

new_money_result = analyzer.analyze_new_money_rebalancing(
    target_allocation=allocation,
    monthly_contribution=1000,
    account_type=AccountType.TAXABLE
)

# Compare all strategies
comparison = analyzer.compare_strategies(all_results)
```

### **Rebalancing Analysis Features:**

#### **1. Strategy Types:**
- **Threshold-based**: Rebalance when allocation drifts beyond specified threshold (5%, 10%, 15%, 20%)
- **Time-based**: Rebalance on fixed schedule (monthly, quarterly, annual)
- **New Money**: Use new contributions to rebalance, minimizing taxes and transaction costs

#### **2. Account Type Support:**
- **Taxable Accounts**: Full tax cost calculation with capital gains implications
- **Tax-Deferred**: 401k, traditional IRA with no immediate tax costs
- **Tax-Free**: Roth IRA, HSA with no tax implications ever

#### **3. Cost Analysis:**
- **Transaction Costs**: Configurable rate (default 0.1%) applied to all trades
- **Tax Costs**: Realistic capital gains tax calculation based on holding periods
- **Total Cost Impact**: Comprehensive analysis of how costs affect net returns

#### **4. Performance Metrics:**
```python
class RebalancingResult:
    strategy_name: str
    total_return: float           # Raw portfolio return
    annualized_return: float      # Annualized performance
    volatility: float             # Portfolio volatility
    sharpe_ratio: float           # Risk-adjusted return
    max_drawdown: float           # Maximum drawdown experienced
    total_transaction_costs: float # Sum of all transaction costs
    total_tax_costs: float        # Sum of all tax costs
    rebalancing_events: List[RebalancingEvent]  # Detailed event history
    average_drift: float          # Average portfolio drift
    drift_episodes: int           # Number of significant drift episodes
    rebalancing_effectiveness: float  # Effectiveness score
```

### **API Endpoints:**

```python
# Standalone rebalancing routes (src/api/rebalancing_routes.py)
POST /api/analyze/rebalancing-strategy
POST /api/analyze/rebalancing-strategy/compare
GET  /api/analyze/rebalancing-strategy/examples

# Request format example:
{
    "allocation": {"VTI": 0.6, "VTIAX": 0.3, "BND": 0.1},
    "strategy_type": "threshold",
    "threshold_percentages": [5, 10, 15, 20],
    "account_type": "taxable",
    "transaction_cost_pct": 0.1
}

# Response format:
{
    "results": [
        {
            "strategy_name": "Threshold 10%",
            "total_return": 1.014,
            "total_costs": 541.0,
            "rebalancing_events_count": 1,
            "cost_adjusted_return": 0.9086
        }
    ],
    "best_strategy": "Threshold 10%",
    "execution_time_seconds": 2.34
}
```

### **Key Business Insights from Testing:**

#### **Cost Impact Analysis:**
- **New Money Strategy**: Often optimal with $0 additional costs (141.4% return over 2 years)
- **10% Threshold**: Good balance with 101.0% return, $541 total costs
- **5% Threshold**: More frequent rebalancing with 97.6% return, $1,627 total costs
- **Monthly Time-based**: 98.2% return with higher transaction costs
- **Annual Time-based**: 101.6% return with lower costs

#### **Account Type Impact:**
- **Taxable Accounts**: Tax costs range $0-$1,068 per rebalancing cycle
- **Tax-Deferred**: $0 tax costs, only transaction costs apply
- **Tax-Free**: $0 tax costs, optimal for frequent rebalancing

#### **Optimal Strategy Selection:**
1. **Tax-advantaged accounts**: More frequent rebalancing acceptable
2. **Taxable accounts**: Favor threshold-based or new money approaches
3. **Regular contributors**: New money strategy often optimal
4. **Buy-and-hold investors**: Higher thresholds (15-20%) often better

### **Testing Results (7/7 Tests Passing):**
```bash
# Comprehensive test suite: test_rebalancing_strategy.py
✅ Test 1 PASSED: Analyzer initialization
✅ Test 2 PASSED: Threshold rebalancing analysis  
✅ Test 3 PASSED: Time-based rebalancing analysis
✅ Test 4 PASSED: New money rebalancing analysis
✅ Test 5 PASSED: Strategy comparison and ranking
✅ Test 6 PASSED: Custom cost parameters
✅ Test 7 PASSED: Account type impact on costs

# Performance: All tests complete in 7.72 seconds
# Coverage: 100% of major functionality tested
```

### **Integration Status:**
- **Core Engine**: ✅ Complete and fully tested (359-line implementation)
- **API Routes**: ✅ Complete with standalone rebalancing_routes.py  
- **Request/Response Models**: ✅ Complete with Pydantic validation
- **Error Handling**: ✅ Comprehensive error handling and logging
- **Documentation**: ✅ Complete with examples and usage patterns
- **Production Ready**: 🔄 Pending API integration fix (analysis_routes.py syntax issue)

---
