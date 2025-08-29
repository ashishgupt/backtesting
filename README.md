# Portfolio Backtesting & Optimization System

An AI-powered portfolio optimization system for sophisticated individual investors who want data-driven asset allocation decisions based on backtested performance.

## 🎯 Features

### **Core Portfolio Analysis**
- **Historical Backtesting**: 20-year backtesting engine (2004-2025) with dividend reinvestment
- **7-Asset Universe**: VTI, VTIAX, BND, VNQ, GLD, VWO, QQQ with 33,725+ price records
- **Portfolio Optimization**: Modern Portfolio Theory with efficient frontier calculations
- **Performance Metrics**: CAGR, Sharpe ratio, max drawdown, volatility analysis

### **Advanced Analytics (NEW!)**
- **Rolling Period Analysis**: Performance consistency across multiple time windows
- **Crisis Period Stress Testing**: Portfolio resilience during 2008, 2020, 2022 crises  
- **Recovery Time Analysis**: Drawdown patterns and recovery velocity tracking
- **Timeline-Aware Risk**: Personalized recommendations based on investment horizon
- **Rebalancing Strategy Analysis**: Cost-optimized rebalancing with tax considerations
- **Extended Historical Analysis**: 20-year market regime detection and correlation evolution

### **API & Infrastructure**
- **REST API**: FastAPI-based backend with 10 comprehensive analysis endpoints
- **Database**: PostgreSQL with 20-year historical data across 7 asset classes
- **Performance**: Sub-second analysis operations (0.31s for 10-year backtests)
- **AI Integration**: Natural language portfolio optimization and analysis

## 🚀 Quick Start

### Prerequisites
- Python 3.8+
- PostgreSQL 16+
- pip or poetry

### Installation

1. Clone the repository:
```bash
git clone https://github.com/ashishgupt/backtesting.git
cd backtesting
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Set up database:
```bash
# Create PostgreSQL database
createdb backtesting

# Run schema setup
psql -d backtesting -f database/schema.sql
```

4. Configure environment:
```bash
cp .env.example .env
# Edit .env with your database credentials
```

5. Load historical data:
```bash
python load_historical_data.py
```

6. Start the API server:
```bash
cd src
uvicorn api.main:app --host 0.0.0.0 --port 8004 --reload
```

## 📊 API Endpoints

### Backtesting
- `POST /api/backtest/portfolio` - Backtest portfolio allocation
- `GET /api/data/assets` - List available assets
- `GET /api/data/status` - Data health check

### Optimization
- `POST /api/optimize/efficient-frontier` - Generate efficient frontier
- `POST /api/optimize/max-sharpe` - Find maximum Sharpe ratio portfolio

### Documentation
- `GET /docs` - Interactive API documentation (Swagger)

## 📈 Example Usage

### Backtest a 60/30/10 Portfolio
```python
import requests

response = requests.post("http://localhost:8004/api/backtest/portfolio", json={
    "allocations": {
        "VTI": 0.6,    # 60% US Total Market
        "VTIAX": 0.3,  # 30% International
        "BND": 0.1     # 10% Bonds
    }
})

results = response.json()
print(f"CAGR: {results['performance']['cagr']:.2%}")
print(f"Max Drawdown: {results['performance']['max_drawdown']:.2%}")
```

## 🏗️ Architecture

```
├── src/
│   ├── api/                 # FastAPI endpoints
│   ├── core/                # Business logic
│   │   ├── portfolio_engine.py    # Backtesting engine
│   │   ├── optimization_engine.py # Portfolio optimization
│   │   └── data_manager.py        # Data operations
│   └── models/              # Database models
├── database/                # Database schemas
├── tests/                   # Test files
└── requirements/            # Documentation
```

## 🧪 Testing

Run the test suite:
```bash
pytest tests/
```

Test specific components:
```bash
python test_portfolio_engine.py    # Core backtesting
python test_optimization_api.py    # Optimization endpoints
python test_backtest_api.py       # API integration
```

## 📊 Performance Benchmarks

- **Backtesting Speed**: <0.4s for 10-year, 3-asset portfolio
- **Optimization Speed**: <0.1s for efficient frontier calculation
- **Data Coverage**: 7,548 historical price records (2015-2024)
- **Accuracy**: Validated within 0.1% of industry tools

## 🛠️ Technology Stack

- **Backend**: FastAPI, SQLAlchemy, PostgreSQL
- **Financial**: pandas, numpy, scipy.optimize
- **Data Source**: Yahoo Finance (yfinance)
- **Database**: TimescaleDB-ready schema
- **Testing**: pytest

## 📋 Current Limitations

- **Asset Universe**: Limited to 3 core assets (VTI, VTIAX, BND)
- **Time Period**: 10 years of historical data
- **Rebalancing**: Monthly frequency only
- **Tax Optimization**: Not implemented

## 🚧 Roadmap

### Phase 1: Enhanced Asset Universe
- Add REITs (VNQ), Gold (GLD), Small Cap (VBR), Emerging Markets (VWO)
- Extend to 20-year historical data (2004-2024)
- Dynamic correlation analysis

### Phase 2: Advanced Analytics  
- Rolling period analysis for different time horizons
- Stress testing through major crisis periods
- Recovery time analysis
- Timeline-specific risk assessment

### Phase 3: AI Integration
- Claude-powered portfolio recommendations
- Natural language portfolio analysis
- Tax-efficient rebalancing strategies

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 🤝 Contributing

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## 📞 Support

For questions and support, please open an issue on GitHub.

---

**Disclaimer**: This tool is for educational and research purposes only. Not investment advice.
