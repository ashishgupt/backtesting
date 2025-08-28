# 🔧 TECHNICAL REFERENCE - Portfolio Backtesting PoC

**📁 Project**: AI-powered portfolio optimization system  
**🎯 Current Phase**: Phase 1 - Expanded Asset Universe (Weeks 1-3)  
**⏱️ Status**: Core system operational, expanding to 7-asset universe  
**📅 Updated**: Session 4 - Sprint "Market-Beating Diversification"

## 🏗️ SYSTEM ARCHITECTURE (CURRENT)

### ✅ **Production Components:**
```
Portfolio Backtesting System
├── FastAPI Backend (src/api/)
│   ├── /backtest - Portfolio performance analysis
│   ├── /optimize - Efficient frontier calculations
│   └── /assets - Asset data endpoints
├── PostgreSQL Database (database/)
│   ├── 7,548 price records (2015-2024)
│   ├── 3 assets: VTI, VTIAX, BND
│   └── Normalized schema with proper indexing
├── Portfolio Engine (src/core/)
│   ├── Modern Portfolio Theory implementation
│   ├── Risk/return calculations
│   └── Optimization algorithms
└── Docker Deployment
    ├── Multi-container setup
    └── Production-ready configuration
```

### 🚀 **Performance Benchmarks:**
- **Backtesting Speed**: 0.36s for 10-year, 3-asset portfolio
- **Optimization Speed**: 0.09s for max Sharpe, 0.10s for efficient frontier  
- **API Response Time**: All endpoints <1s
- **Data Quality**: 99.9% accuracy vs PortfolioVisualizer

---

## 📋 PHASE 1: EXPANDED ASSET UNIVERSE (WEEKS 1-3)

### 🎯 **Week 1 Objectives: Database & Data Pipeline**

#### **Database Schema Extension:**
```sql
-- New assets to add
INSERT INTO assets (symbol, name, asset_class, expense_ratio) VALUES
('VNQ', 'Vanguard Real Estate ETF', 'REIT', 0.0012),
('GLD', 'SPDR Gold Shares', 'Commodity', 0.0040),
('VWO', 'Vanguard Emerging Markets ETF', 'Emerging Market Equity', 0.0010),
('QQQ', 'Invesco QQQ Trust', 'Large Cap Growth', 0.0020);

-- Expected final state: 7 assets total
-- Target: 51,100+ price records (20 years × 7 assets × ~365 days)
```

#### **Data Pipeline Updates:**
- **File**: `load_historical_data.py`
- **Extension**: Add 4 new asset tickers
- **Historical Period**: Extend to 20 years (2004-2024)
- **Data Validation**: Ensure data completeness across all assets
- **Performance Target**: Load 51,100+ records in <30s

### 🎯 **Week 2 Objectives: API & Model Extensions**

#### **Pydantic Model Updates:**
```python
# Current: 3-asset allocation model
class PortfolioAllocation(BaseModel):
    VTI: float = Field(ge=0, le=1)
    VTIAX: float = Field(ge=0, le=1) 
    BND: float = Field(ge=0, le=1)

# Target: 7-asset allocation model
class ExpandedPortfolioAllocation(BaseModel):
    VTI: float = Field(ge=0, le=1)     # US Total Market
    VTIAX: float = Field(ge=0, le=1)   # International
    BND: float = Field(ge=0, le=1)     # Bonds
    VNQ: float = Field(ge=0, le=1)     # REITs
    GLD: float = Field(ge=0, le=1)     # Gold
    VWO: float = Field(ge=0, le=1)     # Emerging Markets
    QQQ: float = Field(ge=0, le=1)     # Technology/Growth
```

#### **API Endpoint Updates:**
- **Backward Compatibility**: Maintain 3-asset endpoint support
- **New Endpoints**: 7-asset backtesting and optimization
- **Performance Target**: <2s for 7-asset optimization

### 🎯 **Week 3 Objectives: Portfolio Engine Optimization**

#### **Multi-Asset Portfolio Engine:**
- **File**: `src/core/portfolio.py`
- **Enhancement**: Support variable asset count (3-7 assets)
- **Optimization**: Efficient frontier for 7-asset universe
- **Validation**: Results accuracy vs benchmark tools

---

## 📊 PHASE 2: ADVANCED RISK ANALYTICS + CONVERSATIONAL REBALANCING (WEEKS 4-5)

### 🤖 **Conversational Rebalancing Architecture:**

#### **Core Components:**
```python
# Rebalancing Strategy Engine
class RebalancingStrategies:
    MONTHLY = {'frequency': 30, 'threshold': 0}
    QUARTERLY = {'frequency': 90, 'threshold': 0}
    THRESHOLD_5PCT = {'frequency': None, 'threshold': 5}
    THRESHOLD_10PCT = {'frequency': None, 'threshold': 10}
    HYBRID_ANNUAL = {'frequency': 365, 'threshold': 7.5}

# Tax-Efficient Analysis
class TaxEfficiencyEngine:
    - new_money_rebalancing: bool
    - tax_loss_harvesting: bool
    - long_term_preference: bool
    - wash_sale_awareness: bool
```

#### **Chatbot Integration:**
```python
# Conversational Interface
class ClaudePortfolioAdvisor:
    def analyze_rebalancing_strategy(self, user_profile, portfolio):
        """Compare multiple rebalancing approaches with tax implications"""
        
    def recommend_allocation_adjustment(self, current_drift, user_context):
        """Provide personalized rebalancing recommendations"""
        
    def crisis_period_analysis(self, strategy, historical_periods):
        """Analyze rebalancing effectiveness during market crashes"""
```

### 🔍 **Advanced Analytics Features:**

#### **Rolling Period Analysis:**
- **3-year windows**: Risk/return across all possible periods
- **5-year windows**: Medium-term performance validation
- **Crisis period focus**: 2008, 2020, 2022 deep analysis

#### **Recovery Time Calculations:**
- **Drawdown periods**: Time underwater analysis
- **Recovery methodology**: Path back to previous highs
- **Strategy comparison**: Rebalanced vs buy-and-hold recovery

#### **Stress Testing Engine:**
```python
class StressTesting:
    def crisis_period_backtest(self, allocation, crisis_periods):
        """Test portfolio performance during specific crisis periods"""
        
    def rebalancing_impact_analysis(self, strategies, crisis_periods):
        """Compare rebalancing strategies during market stress"""
        
    def tax_drag_calculation(self, rebalancing_frequency, tax_bracket):
        """Calculate annual tax impact of different rebalancing frequencies"""
```

---

## 🎯 PHASE 3: EXTENDED HISTORICAL ANALYSIS (WEEKS 6-8)

### **20-Year Analysis Features:**
- **Market Cycle Analysis**: Performance across different economic regimes
- **Correlation Monitoring**: Track diversification effectiveness over time
- **Regime Change Detection**: Identify when correlations break down
- **Long-term Validation**: 20-year vs 10-year performance differences

---

## 📁 UPDATED FILE STRUCTURE

```
/Users/ashish/Claude/backtesting/
├── session-context.md ✅ (Updated with conversational rebalancing)
├── technical-reference.md ✅ (This file - comprehensive architecture)
├── requirements/ ✅ (Complete analysis)
├── src/ ✅ (Production-ready backend)
│   ├── api/ ✅ (3-asset endpoints operational)
│   │   └── [EXPANDING] 7-asset endpoint support
│   ├── core/ ✅ (Portfolio engine operational)  
│   │   └── [EXPANDING] Multi-asset optimization
│   ├── models/ ✅ (3-asset schema)
│   │   └── [EXPANDING] 7-asset Pydantic models
│   └── [NEW] ai/ - Conversational rebalancing engine
│       ├── claude_advisor.py - Natural language interface
│       ├── rebalancing_strategies.py - Strategy comparison
│       └── tax_efficiency.py - Tax-aware optimization
├── database/ ✅ (PostgreSQL with 3 assets)
│   └── [EXPANDING] 7-asset schema + 20-year data
├── tests/ ✅ (Comprehensive test suite)
│   └── [EXPANDING] 7-asset and rebalancing tests
└── web/ ✅ (User documentation)
    └── [EXPANDING] Conversational interface demo
```

---

## 🎯 IMPLEMENTATION PRIORITY (CURRENT SPRINT)

### ✅ **Completed (Phase 0):**
- Core 3-asset backtesting system
- FastAPI backend with optimization
- PostgreSQL database with 10-year data
- Docker deployment configuration
- Comprehensive testing and validation

### 🚧 **In Progress (Phase 1, Week 1):**
1. **Database expansion** to 7 assets
2. **Historical data extension** to 20 years  
3. **Data pipeline updates** for new assets

### 📋 **Next Up:**
1. **Week 2**: API model extensions for 7-asset support
2. **Week 3**: Portfolio engine optimization for multi-asset universe
3. **Weeks 4-5**: Conversational rebalancing analysis implementation
4. **Weeks 6-8**: Extended historical analysis and market regime detection

---

## 🎯 SUCCESS METRICS

### **Phase 1 Targets:**
- **Data Volume**: 51,100+ price records successfully loaded
- **API Performance**: <2s response time for 7-asset optimization
- **Accuracy**: <0.1% variance vs benchmark tools for all 7 assets

### **Phase 2 Targets:**
- **Rebalancing Analysis**: Compare 5+ strategies with tax implications
- **Conversational Interface**: Natural language recommendations
- **Crisis Analysis**: Quantify rebalancing benefit during 2008/2020/2022

### **Phase 3 Targets:**  
- **Historical Depth**: 20-year analysis across multiple market regimes
- **Regime Detection**: Identify correlation breakdowns automatically
- **Long-term Validation**: 20-year performance vs 10-year analysis

---

*🔄 Updated: Session 4 - Phase 1 Week 1 ready to begin*
*📅 Next: Database expansion + 20-year historical data loading*
