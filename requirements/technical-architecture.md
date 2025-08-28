# Technical Architecture

## System Overview
```
┌─────────────────────────────────────────────────────────────┐
│                    Client Layer                              │
├─────────────────────────────────────────────────────────────┤
│  Web UI (Future)     │  Claude Chat Interface (Future)      │
│  - Portfolio Compare │  - Natural Language Queries          │
│  - Chart Visualize   │  - Function Call Integration         │
└─────────────────────────────────────────────────────────────┘
                                │
┌─────────────────────────────────────────────────────────────┐
│                    API Layer                                │
├─────────────────────────────────────────────────────────────┤
│  FastAPI REST Endpoints                                     │
│  ├── /api/data/*        (Data management)                   │
│  ├── /api/backtest/*    (Portfolio backtesting)             │
│  ├── /api/optimize/*    (Portfolio optimization)            │
│  ├── /api/metrics/*     (Financial calculations)            │
│  └── /api/rebalance/*   (Rebalancing analysis)              │
└─────────────────────────────────────────────────────────────┘
                                │
┌─────────────────────────────────────────────────────────────┐
│                  Business Logic Layer                       │
├─────────────────────────────────────────────────────────────┤
│  Portfolio Engine    │  Optimization Engine                 │
│  - Backtesting       │  - Efficient Frontier                │
│  - Performance Calc  │  - Constrained Optimization          │
│  - Risk Metrics      │  - Monte Carlo (Future)              │
│                      │                                      │
│  Rebalancing Engine  │  Tax Engine                          │
│  - Current vs Optimal│  - Capital Gains Calculation         │
│  - Cost Analysis     │  - Tax-Loss Harvesting               │
└─────────────────────────────────────────────────────────────┘
                                │
┌─────────────────────────────────────────────────────────────┐
│                    Data Layer                               │
├─────────────────────────────────────────────────────────────┤
│  PostgreSQL Database                                        │
│  ├── assets (VTI, VTIAX, BND metadata)                     │
│  ├── daily_prices (date, symbol, adj_close, volume)        │
│  ├── portfolio_snapshots (cached backtest results)          │
│  └── optimization_cache (efficient frontier cache)          │
│                                                             │
│  External Data Sources                                      │
│  ├── Yahoo Finance API (primary)                           │
│  └── Alpha Vantage API (backup)                            │
└─────────────────────────────────────────────────────────────┘
```

## Technology Stack

### Backend Core
- **Framework**: FastAPI (Python 3.11+)
- **Database**: PostgreSQL with TimescaleDB extension
- **ORM**: SQLAlchemy with Alembic migrations
- **Async**: asyncio + asyncpg for database operations

### Financial Libraries
- **NumPy/Pandas**: Data manipulation and analysis
- **scipy.optimize**: Portfolio optimization algorithms
- **pyfolio**: Portfolio analysis and risk metrics
- **quantlib**: Advanced financial calculations (if needed)

### API & Integration
- **Pydantic**: Data validation and serialization
- **httpx**: Async HTTP client for external APIs
- **uvicorn**: ASGI server

### Data Sources
- **Primary**: Yahoo Finance (yfinance library)
- **Backup**: Alpha Vantage API
- **Future**: Consider paid data providers for production

## Database Schema

### Assets Table
```sql
CREATE TABLE assets (
    id SERIAL PRIMARY KEY,
    symbol VARCHAR(10) UNIQUE NOT NULL,
    name VARCHAR(255) NOT NULL,
    asset_class VARCHAR(50) NOT NULL,
    expense_ratio DECIMAL(5,4),
    created_at TIMESTAMP DEFAULT NOW()
);
```

### Daily Prices Table (TimescaleDB)
```sql
CREATE TABLE daily_prices (
    date DATE NOT NULL,
    symbol VARCHAR(10) NOT NULL,
    open_price DECIMAL(12,4),
    high_price DECIMAL(12,4),
    low_price DECIMAL(12,4),
    close_price DECIMAL(12,4),
    adj_close DECIMAL(12,4) NOT NULL,
    volume BIGINT,
    dividend DECIMAL(8,4) DEFAULT 0,
    PRIMARY KEY (date, symbol)
);

-- TimescaleDB hypertable for time-series optimization
SELECT create_hypertable('daily_prices', 'date');
```

### Portfolio Snapshots (Cache)
```sql
CREATE TABLE portfolio_snapshots (
    id SERIAL PRIMARY KEY,
    allocation_hash VARCHAR(64) UNIQUE NOT NULL,
    vti_weight DECIMAL(5,4) NOT NULL,
    vtiax_weight DECIMAL(5,4) NOT NULL,
    bnd_weight DECIMAL(5,4) NOT NULL,
    start_date DATE NOT NULL,
    end_date DATE NOT NULL,
    total_return DECIMAL(8,4),
    cagr DECIMAL(6,4),
    volatility DECIMAL(6,4),
    max_drawdown DECIMAL(6,4),
    sharpe_ratio DECIMAL(6,4),
    best_year DECIMAL(6,4),
    worst_year DECIMAL(6,4),
    underwater_periods JSONB,
    created_at TIMESTAMP DEFAULT NOW()
);
```

## API Design

### Core Endpoints

#### Backtesting API
```python
POST /api/backtest/portfolio
{
    "allocation": {"VTI": 0.6, "VTIAX": 0.3, "BND": 0.1},
    "start_date": "2015-01-01",
    "end_date": "2025-01-01",
    "rebalance_frequency": "monthly",
    "initial_value": 10000
}

Response:
{
    "performance": {
        "total_return": 0.847,
        "cagr": 0.0923,
        "volatility": 0.152,
        "sharpe_ratio": 0.61
    },
    "risk_metrics": {
        "max_drawdown": -0.234,
        "worst_year": -0.089,
        "underwater_periods": [...]
    },
    "yearly_returns": [0.124, -0.089, 0.156, ...]
}
```

#### Optimization API
```python
POST /api/optimize/efficient-frontier
{
    "assets": ["VTI", "VTIAX", "BND"],
    "lookback_period": "10Y",
    "num_portfolios": 100
}

Response:
{
    "portfolios": [
        {
            "allocation": {"VTI": 0.2, "VTIAX": 0.1, "BND": 0.7},
            "expected_return": 0.067,
            "volatility": 0.045,
            "sharpe_ratio": 1.49
        },
        ...
    ],
    "min_variance_portfolio": {...},
    "max_sharpe_portfolio": {...}
}
```

## Development Phases

### Phase 1: Core Engine (Weeks 1-2)
1. Database setup and data ingestion
2. Basic backtesting engine
3. Performance metrics calculation
4. API endpoints for backtesting

### Phase 2: Optimization (Weeks 3-4)
1. Efficient frontier calculation
2. Constrained optimization
3. Portfolio comparison APIs
4. Caching and performance optimization

### Phase 3: Integration Prep (Weeks 5-6)
1. Claude function integration
2. Rebalancing analysis
3. Tax consideration framework
4. API documentation and testing

## Performance Considerations
- **Caching**: Store computed results to avoid recalculation
- **Async Processing**: Handle multiple portfolio calculations concurrently
- **Database Indexing**: Optimize time-series queries
- **Rate Limiting**: Respect external API limits
