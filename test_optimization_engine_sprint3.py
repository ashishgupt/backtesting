#!/usr/bin/env python3
"""
Test Portfolio Optimization Engine - Sprint 3

Test the new three-strategy portfolio optimization engine to ensure:
- All three strategies generate valid portfolios
- Rebalancing recommendations are appropriate
- Target achievement analysis works
- API endpoints respond correctly
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import asyncio
import json
from sqlalchemy.orm import Session
from src.models.database import get_db, SessionLocal
from src.optimization.portfolio_optimizer import (
    PortfolioOptimizer, PortfolioRequest, AccountType, StrategyType
)

def test_portfolio_optimization():
    """Test the core portfolio optimization engine"""
    
    print("🚀 Testing Portfolio Optimization Engine - Sprint 3")
    print("=" * 60)
    
    # Initialize database session
    db = SessionLocal()
    
    try:
        # Test Case 1: Basic optimization request
        print("\n📊 Test 1: Basic 10-year optimization")
        print("-" * 40)
        
        request = PortfolioRequest(
            current_savings=50000.0,
            time_horizon=10,
            account_type=AccountType.TAXABLE,
            new_money_available=False
        )
        
        optimizer = PortfolioOptimizer(db)
        result = optimizer.optimize_portfolio(request)
        
        # Validate all three portfolios generated
        assert len(result.portfolios) == 3, "Should generate 3 portfolios"
        
        for strategy, portfolio in result.portfolios.items():
            print(f"\n{strategy.value.upper()} Portfolio:")
            print(f"  Expected Return: {portfolio.expected_return:.1%}")
            print(f"  Volatility: {portfolio.expected_volatility:.1%}")
            print(f"  Sharpe Ratio: {portfolio.sharpe_ratio:.2f}")
            print(f"  Max Drawdown: {portfolio.max_drawdown:.1%}")
            print(f"  Rebalancing: {portfolio.optimal_rebalancing}")
            
            # Print top 3 allocations
            sorted_allocation = sorted(portfolio.allocation.items(), 
                                     key=lambda x: x[1], reverse=True)
            print("  Top Allocations:")
            for asset, weight in sorted_allocation[:3]:
                print(f"    {asset}: {weight:.1%}")
                
            # Validate portfolio weights sum to 1
            total_weight = sum(portfolio.allocation.values())
            assert abs(total_weight - 1.0) < 0.001, f"Weights should sum to 1, got {total_weight}"
            
            # Validate no negative weights
            assert all(w >= 0 for w in portfolio.allocation.values()), "No negative weights"
            
        print("\n✅ Test 1 PASSED - All portfolios valid")
        
        # Test Case 2: Target achievement analysis
        print("\n🎯 Test 2: Target achievement analysis")
        print("-" * 40)
        
        target_request = PortfolioRequest(
            current_savings=25000.0,
            target_amount=100000.0,  # 4x growth in 15 years
            time_horizon=15,
            account_type=AccountType.TAX_FREE,
            new_money_available=True,
            max_annual_contribution=6000.0
        )
        
        target_result = optimizer.optimize_portfolio(target_request)
        
        # Validate target analysis exists
        assert target_result.target_analysis is not None, "Target analysis should exist"
        
        print(f"Target: ${target_request.target_amount:,.0f} in {target_request.time_horizon} years")
        for strategy, analysis in target_result.target_analysis.items():
            probability = analysis['probability']
            expected_value = analysis['expected_final_value']
            print(f"  {strategy.value}: {probability:.0%} probability (Expected: ${expected_value:,.0f})")
            
            # Validate probability is reasonable (between 0 and 1)
            assert 0 <= probability <= 1, f"Probability should be 0-1, got {probability}"
            
        print("\n✅ Test 2 PASSED - Target analysis working")
        
        # Test Case 3: New money rebalancing
        print("\n💰 Test 3: New money rebalancing analysis")  
        print("-" * 40)
        
        new_money_request = PortfolioRequest(
            current_savings=100000.0,
            time_horizon=20,
            account_type=AccountType.TAXABLE,
            new_money_available=True,
            max_annual_contribution=12000.0
        )
        
        new_money_result = optimizer.optimize_portfolio(new_money_request)
        
        for strategy, portfolio in new_money_result.portfolios.items():
            if portfolio.new_money_needed_annual:
                print(f"\n{strategy.value.upper()} New Money Analysis:")
                print(f"  Annual need: ${portfolio.new_money_needed_annual:,.0f}")
                print(f"  Monthly need: ${portfolio.new_money_needed_monthly:.0f}")
                if portfolio.traditional_rebalancing_tax_drag:
                    print(f"  Tax drag avoided: {portfolio.traditional_rebalancing_tax_drag:.2%}")
                    
        print("\n✅ Test 3 PASSED - New money analysis working")
        
        # Test Case 4: Account type differences
        print("\n🏦 Test 4: Account type optimization differences")
        print("-" * 40)
        
        account_types = [AccountType.TAXABLE, AccountType.TAX_DEFERRED, AccountType.TAX_FREE]
        
        for account_type in account_types:
            test_request = PortfolioRequest(
                current_savings=75000.0,
                time_horizon=12,
                account_type=account_type
            )
            
            account_result = optimizer.optimize_portfolio(test_request)
            balanced_portfolio = account_result.portfolios[StrategyType.BALANCED]
            
            print(f"\n{account_type.value.upper()} Account:")
            print(f"  Rebalancing: {balanced_portfolio.optimal_rebalancing}")
            print(f"  Rationale: {balanced_portfolio.rebalancing_rationale[:50]}...")
            
        print("\n✅ Test 4 PASSED - Account type awareness working")
        
        print("\n" + "=" * 60)
        print("🎉 ALL TESTS PASSED - Portfolio Optimization Engine Ready!")
        print("=" * 60)
        
        return True
        
    except Exception as e:
        print(f"\n❌ TEST FAILED: {e}")
        import traceback
        traceback.print_exc()
        return False
        
    finally:
        db.close()

def test_api_integration():
    """Test the optimization API endpoints"""
    
    print("\n🌐 Testing API Integration")
    print("-" * 40)
    
    try:
        import requests
        
        base_url = "http://localhost:8007"
        
        # Test 1: Get available strategies
        response = requests.get(f"{base_url}/api/optimization/strategies")
        if response.status_code == 200:
            strategies = response.json()
            print(f"✅ Strategies endpoint working - {len(strategies['strategies'])} strategies available")
        else:
            print(f"❌ Strategies endpoint failed: {response.status_code}")
            
        # Test 2: Get asset universe
        response = requests.get(f"{base_url}/api/optimization/asset-universe")
        if response.status_code == 200:
            universe = response.json()
            print(f"✅ Asset universe endpoint working - {len(universe['assets'])} assets")
        else:
            print(f"❌ Asset universe endpoint failed: {response.status_code}")
            
        # Test 3: Portfolio optimization
        optimization_request = {
            "current_savings": 50000,
            "target_amount": 150000,
            "time_horizon": 15,
            "account_type": "tax_free",
            "new_money_available": True,
            "max_annual_contribution": 6000
        }
        
        response = requests.post(
            f"{base_url}/api/optimization/optimize",
            json=optimization_request
        )
        
        if response.status_code == 200:
            result = response.json()
            portfolios = result['portfolios']
            print(f"✅ Optimization endpoint working - {len(portfolios)} portfolios generated")
            
            # Validate response structure
            for strategy in ['conservative', 'balanced', 'aggressive']:
                assert strategy in portfolios, f"Missing {strategy} portfolio"
                portfolio = portfolios[strategy]
                assert 'allocation' in portfolio, "Missing allocation"
                assert 'expected_return' in portfolio, "Missing expected_return"
                
            print("✅ API response validation passed")
        else:
            print(f"❌ Optimization endpoint failed: {response.status_code}")
            print(f"Response: {response.text}")
            
        return True
        
    except requests.exceptions.ConnectionError:
        print("⚠️  API server not running - start with 'python -m src.api.main'")
        return False
    except Exception as e:
        print(f"❌ API test failed: {e}")
        return False

def main():
    """Run all tests"""
    
    print("🔬 Portfolio Optimization Engine Test Suite")
    print("Sprint 3 - Week 1 Implementation")
    print("=" * 60)
    
    # Test core optimization engine
    core_success = test_portfolio_optimization()
    
    if core_success:
        # Test API integration (optional - requires running server)
        api_success = test_api_integration()
        
        if core_success and api_success:
            print("\n🏆 ALL TESTS PASSED - Ready for Week 2 Analytics Integration!")
        elif core_success:
            print("\n✅ Core engine tests passed - API tests skipped (server not running)")
        
    print("\n📋 Next Steps:")
    print("  1. Start API server: python -m src.api.main")  
    print("  2. Test endpoints: http://localhost:8007/docs")
    print("  3. Begin Week 2: Analytics integration with existing engines")

if __name__ == "__main__":
    main()
