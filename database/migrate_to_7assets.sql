-- Database migration script: Add 4 new assets for 7-asset universe
-- Run after existing init.sql to expand asset universe

-- Add new assets to support expanded portfolio universe
INSERT INTO assets (symbol, name, asset_class, expense_ratio) VALUES
    ('VNQ', 'Vanguard Real Estate ETF', 'REIT', 0.0012),
    ('GLD', 'SPDR Gold Shares', 'COMMODITY', 0.0040),
    ('VWO', 'Vanguard Emerging Markets ETF', 'EMERGING_MARKETS', 0.0010),
    ('QQQ', 'Invesco QQQ Trust', 'LARGE_CAP_GROWTH', 0.0020)
ON CONFLICT (symbol) DO NOTHING;

-- Update portfolio snapshots table to support 7-asset allocations
-- First, rename existing table for backup
ALTER TABLE portfolio_snapshots RENAME TO portfolio_snapshots_3asset_backup;

-- Create new portfolio snapshots table for 7-asset support
CREATE TABLE IF NOT EXISTS portfolio_snapshots (
    id SERIAL PRIMARY KEY,
    allocation_hash VARCHAR(64) UNIQUE NOT NULL,
    
    -- Original 3 assets
    vti_weight DECIMAL(5,4) NOT NULL,
    vtiax_weight DECIMAL(5,4) NOT NULL, 
    bnd_weight DECIMAL(5,4) NOT NULL,
    
    -- New 4 assets
    vnq_weight DECIMAL(5,4) DEFAULT 0,
    gld_weight DECIMAL(5,4) DEFAULT 0,
    vwo_weight DECIMAL(5,4) DEFAULT 0,
    qqq_weight DECIMAL(5,4) DEFAULT 0,
    
    -- Performance metrics
    total_return DECIMAL(8,4),
    cagr DECIMAL(6,4),
    volatility DECIMAL(6,4),
    max_drawdown DECIMAL(6,4),
    sharpe_ratio DECIMAL(6,4),
    
    -- Metadata
    asset_count SMALLINT DEFAULT 7,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Copy existing 3-asset data to new table
INSERT INTO portfolio_snapshots (
    allocation_hash, vti_weight, vtiax_weight, bnd_weight,
    total_return, cagr, volatility, max_drawdown, sharpe_ratio, 
    asset_count, created_at
)
SELECT 
    allocation_hash, vti_weight, vtiax_weight, bnd_weight,
    total_return, cagr, volatility, max_drawdown, sharpe_ratio,
    3, created_at
FROM portfolio_snapshots_3asset_backup;

-- Update indexes
CREATE INDEX IF NOT EXISTS idx_portfolio_hash_7asset ON portfolio_snapshots(allocation_hash);
CREATE INDEX IF NOT EXISTS idx_portfolio_asset_count ON portfolio_snapshots(asset_count);

-- Add constraint to ensure weights sum to 1.0
ALTER TABLE portfolio_snapshots ADD CONSTRAINT check_allocation_sum 
CHECK (ABS((vti_weight + vtiax_weight + bnd_weight + vnq_weight + gld_weight + vwo_weight + qqq_weight) - 1.0) < 0.0001);

-- Verify new assets were added
SELECT symbol, name, asset_class, expense_ratio FROM assets ORDER BY symbol;
