#!/usr/bin/env python3
"""
Test PortfolioEngine with sample portfolio allocations
"""
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from src.models.database import SessionLocal
from src.core.portfolio_engine import PortfolioEngine

def test_simple_portfolio():
    """Test backtesting with a balanced 3-asset portfolio"""
    print("🧪 Testing PortfolioEngine - Balanced Portfolio")
    print("=" * 60)
    
    # Create PortfolioEngine instance
    db = SessionLocal()
    engine = PortfolioEngine(db)
    
    try:
        # Define a balanced portfolio
        allocation = {
            'VTI': 0.60,    # 60% US Total Market
            'VTIAX': 0.30,  # 30% International
            'BND': 0.10     # 10% Bonds
        }
        
        print(f"Testing allocation: {allocation}")
        print("Backtesting 10 years (2015-2024)...")
        
        # Run backtest
        results = engine.backtest_portfolio(
            allocation=allocation,
            initial_value=10000,
            start_date="2015-01-02",  # First trading day
            end_date="2024-12-31",
            rebalance_frequency="monthly"
        )
        
        # Display results
        metrics = results['performance_metrics']
        print(f"\n📊 Portfolio Performance Results:")
        print(f"  Initial Value: $10,000")
        print(f"  Final Value: ${results['final_value']:,.2f}")
        print(f"  Total Return: {metrics['total_return']:.2%}")
        print(f"  CAGR: {metrics['cagr']:.2%}")
        print(f"  Volatility: {metrics['volatility']:.2%}")
        print(f"  Max Drawdown: {metrics['max_drawdown']:.2%}")
        print(f"  Sharpe Ratio: {metrics['sharpe_ratio']:.3f}")
        print(f"  Sortino Ratio: {metrics['sortino_ratio']:.3f}")
        print(f"  Win Rate: {metrics['win_rate']:.1%}")
        print(f"  Trading Days: {metrics['total_trading_days']}")
        
        # Save to database cache
        engine.save_portfolio_snapshot(allocation, metrics)
        
        # Test a more aggressive portfolio
        print(f"\n🧪 Testing Aggressive Portfolio")
        print("-" * 40)
        
        aggressive_allocation = {
            'VTI': 0.80,    # 80% US Total Market  
            'VTIAX': 0.20,  # 20% International
            'BND': 0.00     # 0% Bonds
        }
        
        aggressive_results = engine.backtest_portfolio(
            allocation=aggressive_allocation,
            initial_value=10000,
            start_date="2015-01-02",
            end_date="2024-12-31", 
            rebalance_frequency="monthly"
        )
        
        aggressive_metrics = aggressive_results['performance_metrics']
        print(f"  Final Value: ${aggressive_results['final_value']:,.2f}")
        print(f"  CAGR: {aggressive_metrics['cagr']:.2%}")
        print(f"  Max Drawdown: {aggressive_metrics['max_drawdown']:.2%}")
        print(f"  Sharpe Ratio: {aggressive_metrics['sharpe_ratio']:.3f}")
        
        engine.save_portfolio_snapshot(aggressive_allocation, aggressive_metrics)
        
        print(f"\n✅ Portfolio backtesting tests completed successfully!")
        
        return True
        
    except Exception as e:
        print(f"❌ Portfolio testing failed: {e}")
        import traceback
        traceback.print_exc()
        return False
        
    finally:
        db.close()

if __name__ == "__main__":
    test_simple_portfolio()
