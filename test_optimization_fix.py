#!/usr/bin/env python3
"""
Test the corrected optimization engine
"""

import sys
sys.path.append('.')

from src.optimization.portfolio_optimizer import PortfolioOptimizer, PortfolioRequest, AccountType

def test_corrected_optimization():
    """Test the corrected optimization with the same parameters"""
    
    request = PortfolioRequest(
        current_savings=10000.0,
        target_amount=None,
        time_horizon=15,
        account_type=AccountType.TAX_FREE,
        new_money_available=True,
        max_annual_contribution=6000
    )
    
    print("Testing corrected optimization engine...")
    print("=" * 60)
    
    try:
        optimizer = PortfolioOptimizer()
        result = optimizer.optimize_portfolio(request)
        
        print(f"\nOptimization completed successfully!")
        print(f"Data period: {result.optimization_metadata['data_period_years']} years")
        print(f"Assets used: {result.optimization_metadata['assets_used']}")
        
        # Display results for each strategy
        for strategy_name, portfolio in result.portfolios.items():
            print(f"\n{strategy_name.value.upper()} STRATEGY:")
            print("-" * 30)
            print(f"Expected Return: {portfolio.expected_return:.4f} ({portfolio.expected_return*100:.2f}%)")
            print(f"Expected Volatility: {portfolio.expected_volatility:.4f} ({portfolio.expected_volatility*100:.2f}%)")
            print(f"Sharpe Ratio: {portfolio.sharpe_ratio:.3f}")
            print(f"Max Drawdown: {portfolio.max_drawdown:.4f} ({portfolio.max_drawdown*100:.2f}%)")
            print(f"New Money Needed (Annual): ${portfolio.new_money_needed_annual:.2f}")
            print(f"New Money Needed (Monthly): ${portfolio.new_money_needed_monthly:.2f}")
            
            print("\nTop Allocations:")
            sorted_allocation = sorted(portfolio.allocation.items(), key=lambda x: x[1], reverse=True)
            for asset, weight in sorted_allocation:
                if weight > 0.005:  # Only show assets with >0.5% allocation
                    print(f"  {asset}: {weight*100:.2f}%")
                    
        # Verify the fixes
        print("\n" + "=" * 60)
        print("VERIFICATION OF FIXES:")
        print("=" * 60)
        
        conservative = result.portfolios[list(result.portfolios.keys())[0]]
        balanced = result.portfolios[list(result.portfolios.keys())[1]] 
        aggressive = result.portfolios[list(result.portfolios.keys())[2]]
        
        print(f"Conservative Return: {conservative.expected_return*100:.2f}%")
        print(f"Balanced Return: {balanced.expected_return*100:.2f}%") 
        print(f"Aggressive Return: {aggressive.expected_return*100:.2f}%")
        
        print(f"\nReturn ordering correct: {conservative.expected_return < balanced.expected_return < aggressive.expected_return}")
        print(f"Volatility ordering correct: {conservative.expected_volatility < balanced.expected_volatility < aggressive.expected_volatility}")
        
        # Check new money requirements are different
        new_money_values = [p.new_money_needed_annual for p in result.portfolios.values()]
        print(f"New money requirements differ: {len(set(new_money_values)) > 1}")
        print(f"New money requirements: {[f'${x:.2f}' for x in new_money_values]}")
        
        return True
        
    except Exception as e:
        print(f"ERROR: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    test_corrected_optimization()
