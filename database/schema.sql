-- Portfolio Backtesting Database Schema
-- Created: Session 2
-- Description: Core tables for backtesting engine

-- ============================================================================
-- Assets Table: Store metadata for ETFs/Indexes we can backtest
-- ============================================================================
CREATE TABLE assets (
    id SERIAL PRIMARY KEY,
    symbol VARCHAR(10) UNIQUE NOT NULL,
    name VARCHAR(255) NOT NULL,
    asset_class VARCHAR(50) NOT NULL,
    expense_ratio DECIMAL(5,4),
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

-- Index for fast symbol lookups
CREATE INDEX idx_assets_symbol ON assets(symbol);
CREATE INDEX idx_assets_asset_class ON assets(asset_class);

-- ============================================================================
-- Daily Prices Table: Historical price data for backtesting calculations
-- ============================================================================
CREATE TABLE daily_prices (
    date DATE NOT NULL,
    symbol VARCHAR(10) NOT NULL,
    open_price DECIMAL(12,4),
    high_price DECIMAL(12,4),
    low_price DECIMAL(12,4),
    close_price DECIMAL(12,4),
    adj_close DECIMAL(12,4) NOT NULL,  -- Adjusted for dividends/splits
    volume BIGINT,
    dividend DECIMAL(8,4) DEFAULT 0,   -- Daily dividend amount
    split_factor DECIMAL(8,4) DEFAULT 1, -- Stock split factor
    created_at TIMESTAMP DEFAULT NOW(),
    PRIMARY KEY (date, symbol)
);

-- Foreign key relationship to assets table
ALTER TABLE daily_prices ADD CONSTRAINT fk_daily_prices_symbol 
    FOREIGN KEY (symbol) REFERENCES assets(symbol) ON DELETE CASCADE;

-- Performance indexes for time-series queries
CREATE INDEX idx_daily_prices_symbol_date ON daily_prices(symbol, date DESC);
CREATE INDEX idx_daily_prices_date ON daily_prices(date DESC);

-- ============================================================================
-- Portfolio Snapshots Table: Cache expensive backtest calculations
-- ============================================================================
CREATE TABLE portfolio_snapshots (
    id SERIAL PRIMARY KEY,
    allocation_hash VARCHAR(64) UNIQUE NOT NULL, -- MD5 hash of allocation
    -- Asset allocation weights (must sum to 1.0)
    vti_weight DECIMAL(5,4) NOT NULL CHECK (vti_weight >= 0 AND vti_weight <= 1),
    vtiax_weight DECIMAL(5,4) NOT NULL CHECK (vtiax_weight >= 0 AND vtiax_weight <= 1),
    bnd_weight DECIMAL(5,4) NOT NULL CHECK (bnd_weight >= 0 AND bnd_weight <= 1),
    
    -- Backtest parameters
    start_date DATE NOT NULL,
    end_date DATE NOT NULL,
    rebalance_frequency VARCHAR(20) DEFAULT 'monthly',
    initial_value DECIMAL(12,2) DEFAULT 10000,
    
    -- Performance metrics
    total_return DECIMAL(8,4),           -- Total return over period
    cagr DECIMAL(6,4),                   -- Compound Annual Growth Rate
    volatility DECIMAL(6,4),             -- Annualized standard deviation
    max_drawdown DECIMAL(6,4),           -- Maximum peak-to-trough decline
    sharpe_ratio DECIMAL(6,4),           -- Risk-adjusted return metric
    sortino_ratio DECIMAL(6,4),          -- Downside risk-adjusted return
    
    -- Year-by-year analysis
    best_year DECIMAL(6,4),              -- Best annual return
    worst_year DECIMAL(6,4),             -- Worst annual return
    positive_years INTEGER,              -- Number of positive return years
    total_years INTEGER,                 -- Total years in backtest
    
    -- Detailed metrics (stored as JSON for flexibility)
    yearly_returns JSONB,               -- Array of annual returns
    underwater_periods JSONB,           -- Drawdown recovery analysis
    monthly_returns JSONB,              -- Monthly return series
    
    -- Metadata
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

-- Constraint: allocation weights must sum to 1.0
ALTER TABLE portfolio_snapshots ADD CONSTRAINT chk_allocation_sum 
    CHECK (ABS((vti_weight + vtiax_weight + bnd_weight) - 1.0) < 0.0001);

-- Performance indexes
CREATE INDEX idx_portfolio_snapshots_hash ON portfolio_snapshots(allocation_hash);
CREATE INDEX idx_portfolio_snapshots_dates ON portfolio_snapshots(start_date, end_date);
CREATE INDEX idx_portfolio_snapshots_performance ON portfolio_snapshots(cagr DESC, sharpe_ratio DESC);

-- ============================================================================
-- Insert Initial Asset Data
-- ============================================================================
INSERT INTO assets (symbol, name, asset_class, expense_ratio) VALUES
('VTI', 'Vanguard Total Stock Market ETF', 'US_EQUITY', 0.0003),
('VTIAX', 'Vanguard Total International Stock Index Fund', 'INTERNATIONAL_EQUITY', 0.0011),
('BND', 'Vanguard Total Bond Market ETF', 'BONDS', 0.0003);

-- ============================================================================
-- Utility Views for Common Queries
-- ============================================================================

-- View: Latest prices for all assets
CREATE VIEW latest_prices AS
SELECT DISTINCT ON (symbol) 
    symbol, 
    date, 
    adj_close as price,
    volume
FROM daily_prices 
ORDER BY symbol, date DESC;

-- View: Portfolio performance summary
CREATE VIEW portfolio_performance_summary AS
SELECT 
    id,
    allocation_hash,
    ROUND(vti_weight::numeric, 3) as vti_pct,
    ROUND(vtiax_weight::numeric, 3) as vtiax_pct, 
    ROUND(bnd_weight::numeric, 3) as bnd_pct,
    ROUND((cagr * 100)::numeric, 2) as cagr_percent,
    ROUND((volatility * 100)::numeric, 2) as volatility_percent,
    ROUND((max_drawdown * 100)::numeric, 2) as max_drawdown_percent,
    ROUND(sharpe_ratio::numeric, 3) as sharpe_ratio,
    total_years,
    positive_years,
    created_at
FROM portfolio_snapshots
ORDER BY cagr DESC;

-- ============================================================================
-- Comments for Documentation
-- ============================================================================
COMMENT ON TABLE assets IS 'Metadata for ETFs and indexes available for backtesting';
COMMENT ON TABLE daily_prices IS 'Historical price data with dividend adjustments';
COMMENT ON TABLE portfolio_snapshots IS 'Cached portfolio backtest results';

COMMENT ON COLUMN daily_prices.adj_close IS 'Price adjusted for dividends and stock splits';
COMMENT ON COLUMN portfolio_snapshots.allocation_hash IS 'MD5 hash for caching identical allocations';
COMMENT ON COLUMN portfolio_snapshots.underwater_periods IS 'JSON array of drawdown periods and recovery times';
