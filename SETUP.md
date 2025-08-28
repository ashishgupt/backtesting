# 🚀 Portfolio Backtesting System - Quick Setup Guide

## ⚡ Quick Start (2 minutes)

The system is configured to use your **local PostgreSQL database** and runs on **port 8006** to avoid conflicts.

### 1. Start the System
```bash
cd /Users/ashish/Claude/backtesting
docker-compose up -d api
```

### 2. Verify Health
```bash
curl http://localhost:8006/health
# Expected: {"status":"healthy","database":"connected","timestamp":"..."}
```

### 3. Test 7-Asset Portfolio
```bash
curl -X POST http://localhost:8006/api/backtest/portfolio \
  -H "Content-Type: application/json" \
  -d '{
    "allocation": {
      "allocation": {
        "VTI": 0.30, "VTIAX": 0.20, "BND": 0.25,
        "VNQ": 0.10, "GLD": 0.05, "VWO": 0.05, "QQQ": 0.05
      }
    },
    "start_date": "2015-01-02",
    "end_date": "2024-12-31",
    "initial_value": 10000,
    "rebalance_frequency": "quarterly"
  }'
```

## 🎯 System Architecture

### Database Configuration
- **Local PostgreSQL**: `postgresql://ashish:@localhost:5432/backtesting`
- **Docker API Connection**: Uses `host.docker.internal` to connect to host database
- **Data**: 33,725 price records across 7 assets (2004-2024)

### Port Configuration
- **API**: http://localhost:8006
- **Documentation**: http://localhost:8006/docs
- **Health**: http://localhost:8006/health

### Asset Universe
- **VTI**: US Total Stock Market
- **VTIAX**: International Stocks  
- **BND**: US Bonds
- **VNQ**: REITs
- **GLD**: Gold/Commodities
- **VWO**: Emerging Markets
- **QQQ**: Technology/Growth

## 🔧 Troubleshooting

### Common Issues
1. **"Connection refused"** → Database not running: Check PostgreSQL service
2. **"Port already in use"** → Another service on 8006: Change port in docker-compose.yml
3. **"No data found"** → Date range issue: Ensure dates are within 2004-2024

### Reset System
```bash
docker-compose down
docker-compose up -d api
```

### View Logs
```bash
docker-compose logs portfolio_api
```

## 📊 Current Status
✅ **Phase 1 Complete**: 7-asset universe with 20-year historical data  
✅ **API Operational**: All endpoints working on port 8006  
✅ **Database Connected**: Local PostgreSQL with 33,725 records  
🚀 **Ready For**: Phase 2 Advanced Analytics + Conversational Rebalancing
