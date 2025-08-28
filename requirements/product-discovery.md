# Portfolio Backtesting PoC - Product Discovery

## Project Vision
Create an AI-powered portfolio optimization system that helps users find optimal asset allocations based on their risk tolerance, time horizon, and account types through backtesting and efficient frontier analysis.

## Key Stakeholder Questions

### User Profile
- [ ] Primary user persona (individual investors vs advisors)
- [ ] Financial sophistication level
- [ ] Current tools/process they use for portfolio decisions
- [ ] Decision-making timeline (immediate vs research over time)

### Business Context  
- [ ] Success criteria for PoC
- [ ] Timeline for PoC completion
- [ ] Future integration plans with main wealth management app
- [ ] Resource constraints (development time, infrastructure)

### Technical Scope
- [ ] Initial asset universe (which indexes/ETFs)
- [ ] Historical data requirements (timeframe, granularity)
- [ ] Performance requirements (response times, concurrent users)
- [ ] Integration complexity with Claude API

## Initial Feature Set (From Requirements)
1. **Database Layer**: Store major index historical data
2. **Backtesting Engine**: Calculate portfolio performance metrics
3. **Optimization Algorithms**: Find optimal allocations using efficient frontier
4. **Chat Interface**: Claude-powered portfolio recommendations
5. **Mathematical APIs**: Modular calculation endpoints

## Open Questions
1. What specific indexes should we prioritize?
2. How do we handle different account types (taxable, 401k, Roth)?
3. What's the minimum viable optimization algorithm?
4. How sophisticated should the chat interface be?
5. What visualization/reporting is needed?
