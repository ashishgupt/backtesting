# 🔄 SESSION CONTEXT - Portfolio Backtesting PoC

**📁 Project**: AI-powered portfolio optimization system  
**🎯 Current Phase**: Phase 1 - Core Engine Setup  
**⏱️ Status**: Requirements complete, ready for implementation  

## 📋 WHAT TO READ FIRST
1. **requirements.md** - Core product requirements and user profile
2. **technical-reference.md** - Live implementation status & database schema  
3. **todo.md** - Current development tasks and priorities
4. **technical-architecture.md** - System design and API structure
5. **user-stories.md** - Acceptance criteria for testing

## 🎯 CORE OBJECTIVES
- **Primary**: Build backtesting engine for 3-asset portfolio (VTI/VTIAX/BND)
- **Data**: 10 years daily prices (2015-2025) with dividend reinvestment
- **Output**: Accurate performance metrics (CAGR, drawdown, Sharpe ratio)
- **Future**: Claude chat integration for portfolio recommendations

## ⚡ DEVELOPMENT APPROACH
- **Test-First**: Create acceptance criteria before coding each component
- **Incremental**: Build core engine → optimization → Claude integration
- **Validation**: Match industry-standard calculations (0.1% tolerance)
- **Documentation**: Update technical-reference.md with each implementation

## 🔧 TECH STACK DECISIONS
- **Backend**: FastAPI + PostgreSQL + SQLAlchemy
- **Financial**: pandas, numpy, scipy.optimize, yfinance
- **Data**: TimescaleDB for time-series optimization
- **Testing**: pytest with calculation validation

## 📊 KEY BUSINESS RULES
- **Target User**: Sophisticated investors comparing allocation strategies
- **Tax Aware**: Consider taxable account rebalancing costs
- **Risk Focused**: Drawdown analysis more important than returns
- **Conservative**: Start with 3 assets, expand later

## 🚨 CRITICAL REQUIREMENTS
- **Accuracy**: Backtesting must match industry tools
- **Performance**: API responses <5 seconds
- **Constraints**: Handle min/max allocation limits
- **Caching**: Store expensive calculations

## 💾 FILE ORGANIZATION
```
/Users/ashish/Claude/backtesting/
├── requirements/ ✅ (Complete - 5 files)
├── src/ ❌ (Next: Core implementation)
├── tests/ ❌ (Next: Acceptance criteria)  
└── database/ ❌ (Next: Schema setup)
```

## 🎯 NEXT ACTIONS (Start Here)
1. **Check todo.md** for current session tasks
2. **Review technical-reference.md** for implementation status
3. **Create acceptance criteria** before building any component
4. **Update technical-reference.md** as you implement
5. **Check off completed items** in todo.md

## 💡 DEVELOPMENT WORKFLOW

### 🔄 New Session Startup (2 minutes)
1. Read **session-context.md** (quick orientation)
2. Check **todo.md** for current tasks  
3. Review **technical-reference.md** for implementation status
4. Continue building from where left off

### 🛠️ Before Development Pattern (Every Component)
1. Pick a component from **todo.md**
2. Create acceptance criteria in **technical-reference.md** 
3. Implement the component
4. Update **technical-reference.md** with implementation details
5. Check off task in **todo.md**

### 📝 Session Efficiency Rules
- **One context file**: Only update session-context.md for major phase changes
- **Live updates**: Modify technical-reference.md with implementation details  
- **Task tracking**: Use todo.md checkboxes, don't create duplicate task lists
- **Test-driven**: Write acceptance criteria first, implement second

---
*🔄 Updated: Session 2 (workflow patterns added)*
