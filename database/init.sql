-- Database initialization script
-- Creates tables and indexes for portfolio backtesting system

-- Enable TimescaleDB extension for time-series optimization
CREATE EXTENSION IF NOT EXISTS timescaledb CASCADE;

-- Create schema
CREATE SCHEMA IF NOT EXISTS portfolio;

-- Assets table
CREATE TABLE IF NOT EXISTS assets (
    id SERIAL PRIMARY KEY,
    symbol VARCHAR(10) UNIQUE NOT NULL,
    name VARCHAR(255) NOT NULL,
    asset_class VARCHAR(50) NOT NULL,
    expense_ratio DECIMAL(5,4),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Daily prices table (optimized for time-series)
CREATE TABLE IF NOT EXISTS daily_prices (
    date DATE NOT NULL,
    symbol VARCHAR(10) NOT NULL REFERENCES assets(symbol),
    open_price DECIMAL(12,4),
    high_price DECIMAL(12,4),
    low_price DECIMAL(12,4),
    close_price DECIMAL(12,4),
    adj_close DECIMAL(12,4) NOT NULL,
    volume BIGINT,
    dividend DECIMAL(8,4) DEFAULT 0,
    split_factor DECIMAL(8,4) DEFAULT 1,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (date, symbol)
);

-- Convert to TimescaleDB hypertable for better performance
SELECT create_hypertable('daily_prices', 'date', if_not_exists => TRUE);

-- Portfolio snapshots table for caching
CREATE TABLE IF NOT EXISTS portfolio_snapshots (
    id SERIAL PRIMARY KEY,
    allocation_hash VARCHAR(64) UNIQUE NOT NULL,
    vti_weight DECIMAL(5,4) NOT NULL,
    vtiax_weight DECIMAL(5,4) NOT NULL,
    bnd_weight DECIMAL(5,4) NOT NULL,
    total_return DECIMAL(8,4),
    cagr DECIMAL(6,4),
    volatility DECIMAL(6,4),
    max_drawdown DECIMAL(6,4),
    sharpe_ratio DECIMAL(6,4),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Indexes for performance
CREATE INDEX IF NOT EXISTS idx_assets_symbol ON assets(symbol);
CREATE INDEX IF NOT EXISTS idx_assets_class ON assets(asset_class);
CREATE INDEX IF NOT EXISTS idx_daily_prices_symbol_date ON daily_prices(symbol, date);
CREATE INDEX IF NOT EXISTS idx_portfolio_hash ON portfolio_snapshots(allocation_hash);

-- Insert initial asset data
INSERT INTO assets (symbol, name, asset_class, expense_ratio) VALUES
    ('VTI', 'Vanguard Total Stock Market ETF', 'US_EQUITY', 0.0003),
    ('VTIAX', 'Vanguard Total International Stock Index Fund Admiral Shares', 'INTL_EQUITY', 0.0011),
    ('BND', 'Vanguard Total Bond Market ETF', 'FIXED_INCOME', 0.0003)
ON CONFLICT (symbol) DO NOTHING;

-- Create user for application
CREATE USER portfolio_app WITH ENCRYPTED PASSWORD 'portfolio_app_pass';
GRANT SELECT, INSERT, UPDATE, DELETE ON ALL TABLES IN SCHEMA public TO portfolio_app;
GRANT USAGE, SELECT ON ALL SEQUENCES IN SCHEMA public TO portfolio_app;
