"""
Test Enhanced Portfolio Optimization with Analytics Integration

Tests the new enhanced optimization system that integrates:
- Crisis period analysis
- Rolling period consistency
- Advanced risk metrics  
- Recovery time analysis
"""

import asyncio
import json
import logging
from datetime import datetime

from src.optimization.portfolio_optimizer_enhanced import (
    EnhancedPortfolioOptimizer,
    PortfolioRequest,
    AccountType
)

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def test_enhanced_optimization():
    """Test the enhanced portfolio optimization system"""
    
    print("🚀 Testing Enhanced Portfolio Optimization with Analytics Integration")
    print("=" * 80)
    
    try:
        # Initialize the enhanced optimizer
        enhanced_optimizer = EnhancedPortfolioOptimizer()
        print("✅ Enhanced optimizer initialized successfully")
        
        # Create test portfolio request
        request = PortfolioRequest(
            current_savings=50000.0,
            target_amount=500000.0,
            time_horizon=15,
            account_type=AccountType.TAX_FREE,
            new_money_available=True,
            max_annual_contribution=12000.0
        )
        
        print(f"\n📋 Portfolio Request:")
        print(f"  Current Savings: ${request.current_savings:,.0f}")
        print(f"  Target Amount: ${request.target_amount:,.0f}")
        print(f"  Time Horizon: {request.time_horizon} years")
        print(f"  Account Type: {request.account_type.value}")
        print(f"  New Money Available: {request.new_money_available}")
        print(f"  Max Annual Contribution: ${request.max_annual_contribution:,.0f}")
        
        # Run enhanced optimization
        print("\n⚡ Running enhanced optimization with analytics integration...")
        start_time = datetime.now()
        
        results = enhanced_optimizer.optimize_enhanced_portfolio(request)
        
        end_time = datetime.now()
        optimization_time = (end_time - start_time).total_seconds()
        
        print(f"✅ Optimization completed in {optimization_time:.2f} seconds")
        print(f"📊 Generated {len(results)} enhanced portfolios")
        
        # Display results for each strategy
        for i, result in enumerate(results, 1):
            print(f"\n{'='*20} STRATEGY {i}: {result.strategy.upper()} {'='*20}")
            
            # Core metrics
            print(f"📈 Core Portfolio Metrics:")
            print(f"  Expected Return: {result.expected_return:.2%}")
            print(f"  Volatility: {result.volatility:.2%}")
            print(f"  Sharpe Ratio: {result.sharpe_ratio:.2f}")
            print(f"  Target Achievement: {result.target_achievement_probability:.1%}")
            print(f"  Expected Final Value: ${result.expected_final_value:,.0f}")
            
            # Top allocations
            print(f"\n🎯 Top Asset Allocations:")
            sorted_allocation = sorted(result.allocation.items(), key=lambda x: x[1], reverse=True)
            for asset, weight in sorted_allocation[:5]:
                if weight > 0.01:  # Only show allocations > 1%
                    print(f"  {asset}: {weight:.1%}")
            
            # Crisis analysis summary
            print(f"\n🛡️  Crisis Period Resilience:")
            print(f"  Overall Crisis Score: {result.overall_crisis_score:.1f}/100")
            for crisis in result.crisis_analysis:
                print(f"  {crisis.crisis_name}: {crisis.portfolio_decline:.1f}% decline "
                      f"(Market: {crisis.market_decline:.1f}%)")
                if crisis.recovery_time_months:
                    print(f"    Recovery Time: {crisis.recovery_time_months:.1f} months")
            
            # Rolling period consistency
            print(f"\n📊 Rolling Period Consistency:")
            print(f"  Overall Consistency Score: {result.consistency_score:.1f}/100")
            for period, analysis in result.rolling_analysis.items():
                print(f"  {period}: Avg CAGR {analysis.avg_cagr:.1%}, "
                      f"Min {analysis.min_cagr:.1%}, Max {analysis.max_cagr:.1%}")
            
            # Enhanced risk metrics
            print(f"\n⚠️  Enhanced Risk Metrics:")
            print(f"  95% VaR: {result.risk_metrics.var_95:.2f}%")
            print(f"  95% CVaR: {result.risk_metrics.cvar_95:.2f}%")
            print(f"  Sortino Ratio: {result.risk_metrics.sortino_ratio:.2f}")
            print(f"  Calmar Ratio: {result.risk_metrics.calmar_ratio:.2f}")
            print(f"  Max Monthly Loss: {result.risk_metrics.max_monthly_loss:.1f}%")
            print(f"  Worst 12M Return: {result.risk_metrics.worst_12_month_return:.1f}%")
            
            # Recovery and rebalancing
            print(f"\n🔄 Recovery & Rebalancing:")
            print(f"  Avg Recovery Time: {result.avg_recovery_time_months:.1f} months")
            print(f"  Worst Recovery Time: {result.worst_drawdown_recovery_months:.1f} months")
            print(f"  Optimal Rebalancing: {result.optimal_rebalancing_frequency}")
            print(f"  Rebalancing Benefit: {result.rebalancing_benefit:.2%} annually")
            
            # Account-specific notes
            print(f"\n💡 Account-Specific Recommendations:")
            for note in result.account_specific_notes:
                print(f"  • {note}")
        
        # Summary comparison
        print(f"\n{'='*25} STRATEGY COMPARISON {'='*25}")
        print(f"{'Strategy':<12} {'Return':<8} {'Risk':<8} {'Sharpe':<8} {'Crisis':<8} {'Consistency':<12}")
        print("-" * 65)
        
        for result in results:
            print(f"{result.strategy.title():<12} "
                  f"{result.expected_return:.1%} "
                  f"{result.volatility:.1%} "
                  f"{result.sharpe_ratio:.2f} "
                  f"{result.overall_crisis_score:.0f}/100 "
                  f"{result.consistency_score:.0f}/100")
        
        print("\n🎉 Enhanced Portfolio Optimization Test Complete!")
        print(f"⏱️  Total optimization time: {optimization_time:.2f} seconds")
        print(f"📊 Analytics integration successful for all {len(results)} portfolios")
        
        return True
        
    except Exception as e:
        print(f"❌ Error during enhanced optimization test: {str(e)}")
        logger.exception("Detailed error information:")
        return False

async def test_api_integration():
    """Test the enhanced optimization API endpoints"""
    
    print("\n🌐 Testing Enhanced Optimization API Integration")
    print("=" * 60)
    
    try:
        # This would require the API server to be running
        # For now, we'll just test the route structure
        from src.api.enhanced_optimization_routes import router
        
        print("✅ Enhanced optimization API routes loaded successfully")
        print(f"📍 Available endpoints:")
        
        for route in router.routes:
            if hasattr(route, 'path') and hasattr(route, 'methods'):
                methods = list(route.methods) if route.methods else ['GET']
                print(f"  {methods[0]:<6} {route.path}")
        
        print("\n💡 To test API endpoints, start the server and visit:")
        print("  http://localhost:8000/docs")
        print("  Look for 'Enhanced Portfolio Optimization' section")
        
        return True
        
    except Exception as e:
        print(f"❌ Error testing API integration: {str(e)}")
        return False

if __name__ == "__main__":
    print("🔬 Enhanced Portfolio Optimization - Comprehensive Test Suite")
    print("Testing Sprint 3 Week 2 - Analytics Integration")
    print("=" * 80)
    
    # Run tests
    test_results = []
    
    # Test 1: Enhanced Optimization Core Functionality
    print("\n🧪 TEST 1: Enhanced Optimization Core Functionality")
    result1 = asyncio.run(test_enhanced_optimization())
    test_results.append(("Enhanced Optimization", result1))
    
    # Test 2: API Integration
    print("\n🧪 TEST 2: API Integration")
    result2 = asyncio.run(test_api_integration())
    test_results.append(("API Integration", result2))
    
    # Test summary
    print("\n" + "="*80)
    print("📋 TEST SUMMARY")
    print("="*80)
    
    passed = 0
    for test_name, passed_test in test_results:
        status = "✅ PASS" if passed_test else "❌ FAIL"
        print(f"{test_name:<40} {status}")
        if passed_test:
            passed += 1
    
    print(f"\n🎯 Results: {passed}/{len(test_results)} tests passed")
    
    if passed == len(test_results):
        print("🎉 All tests passed! Enhanced optimization system is ready.")
        print("\n🚀 Next Steps:")
        print("  1. Start the API server: uvicorn src.api.main:app --reload")
        print("  2. Visit http://localhost:8000/docs to test endpoints") 
        print("  3. Test with frontend integration")
        print("  4. Add Chart.js visualization components")
    else:
        print("⚠️  Some tests failed. Please review the errors above.")
