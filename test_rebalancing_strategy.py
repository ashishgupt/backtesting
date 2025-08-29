"""
Test Suite for Rebalancing Strategy Analyzer

Tests comprehensive rebalancing strategy analysis including:
- Threshold-based rebalancing
- Time-based rebalancing  
- New money rebalancing
- Strategy comparison and ranking

Author: AI Assistant
Created: August 2025
"""

import unittest
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import Dict
import sys
import os

# Add the src directory to the path so we can import our modules
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..'))

from src.core.rebalancing_strategy_analyzer import (
    RebalancingStrategyAnalyzer,
    RebalancingFrequency,
    AccountType,
    RebalancingResult,
    RebalancingEvent
)


class TestRebalancingStrategyAnalyzer(unittest.TestCase):
    """Test cases for rebalancing strategy analysis"""
    
    def setUp(self):
        """Set up test data and analyzer"""
        # Create sample price data for testing (2 years of daily data)
        start_date = datetime(2022, 1, 1)
        end_date = datetime(2024, 1, 1)
        dates = pd.date_range(start=start_date, end=end_date, freq='D')
        
        # Create synthetic price data with realistic returns
        np.random.seed(42)  # For reproducible tests
        n_days = len(dates)
        
        # VTI (US Stock Market) - higher volatility, higher returns
        vti_returns = np.random.normal(0.0008, 0.015, n_days)  # ~20% annual, 15% vol
        vti_prices = 100 * np.exp(np.cumsum(vti_returns))
        
        # VTIAX (International Stocks) - moderate volatility
        vtiax_returns = np.random.normal(0.0005, 0.012, n_days)  # ~13% annual, 12% vol  
        vtiax_prices = 80 * np.exp(np.cumsum(vtiax_returns))
        
        # BND (Bonds) - lower volatility, lower returns
        bnd_returns = np.random.normal(0.0002, 0.004, n_days)  # ~5% annual, 4% vol
        bnd_prices = 60 * np.exp(np.cumsum(bnd_returns))
        
        self.price_data = pd.DataFrame({
            'VTI': vti_prices,
            'VTIAX': vtiax_prices,
            'BND': bnd_prices
        }, index=dates)
        
        # Standard test allocation
        self.test_allocation = {
            'VTI': 0.6,
            'VTIAX': 0.3,
            'BND': 0.1
        }
        
        # Initialize analyzer
        self.analyzer = RebalancingStrategyAnalyzer(self.price_data)
        
        print(f"✅ Test setup complete:")
        print(f"   📊 Price data: {len(self.price_data)} days ({self.price_data.index[0].date()} to {self.price_data.index[-1].date()})")
        print(f"   🎯 Test allocation: {self.test_allocation}")
        print(f"   💰 Final prices: VTI=${vti_prices[-1]:.2f}, VTIAX=${vtiax_prices[-1]:.2f}, BND=${bnd_prices[-1]:.2f}")
    
    def test_analyzer_initialization(self):
        """Test that analyzer initializes correctly"""
        self.assertIsInstance(self.analyzer, RebalancingStrategyAnalyzer)
        self.assertEqual(len(self.analyzer.price_data), len(self.price_data))
        self.assertEqual(len(self.analyzer.returns_data), len(self.price_data) - 1)
        
        # Check default parameters
        self.assertEqual(self.analyzer.transaction_cost_rate, 0.001)
        self.assertIn('short_term', self.analyzer.tax_rates)
        self.assertIn('long_term', self.analyzer.tax_rates)
        
        print("✅ Test 1 PASSED: Analyzer initialization")
    
    def test_threshold_rebalancing_analysis(self):
        """Test threshold-based rebalancing analysis"""
        thresholds = [5, 10, 15]
        
        results = self.analyzer.analyze_threshold_rebalancing(
            target_allocation=self.test_allocation,
            threshold_percentages=thresholds,
            account_type=AccountType.TAXABLE
        )
        
        # Verify results structure
        self.assertEqual(len(results), len(thresholds))
        
        for i, result in enumerate(results):
            self.assertIsInstance(result, RebalancingResult)
            self.assertEqual(result.frequency, RebalancingFrequency.THRESHOLD)
            self.assertIn(f"{thresholds[i]}%", result.strategy_name)
            
            # Check that all required metrics are present
            self.assertIsInstance(result.total_return, float)
            self.assertIsInstance(result.annualized_return, float)
            self.assertIsInstance(result.volatility, float)
            self.assertIsInstance(result.sharpe_ratio, float)
            self.assertIsInstance(result.max_drawdown, float)
            
            # Check rebalancing events
            self.assertIsInstance(result.rebalancing_events, list)
            self.assertGreaterEqual(result.total_transaction_costs, 0)
            self.assertGreaterEqual(result.total_tax_costs, 0)
            
            print(f"   📈 {result.strategy_name}: {result.total_return:.1%} return, "
                  f"{len(result.rebalancing_events)} rebalances, "
                  f"${result.total_transaction_costs + result.total_tax_costs:.0f} costs")
        
        # Higher thresholds should generally result in fewer rebalancing events
        rebalancing_counts = [len(r.rebalancing_events) for r in results]
        self.assertGreaterEqual(rebalancing_counts[0], rebalancing_counts[-1], 
                               "Lower thresholds should generally trigger more rebalancing")
        
        print("✅ Test 2 PASSED: Threshold rebalancing analysis")
    
    def test_time_based_rebalancing_analysis(self):
        """Test time-based rebalancing analysis"""
        frequencies = [
            RebalancingFrequency.MONTHLY,
            RebalancingFrequency.QUARTERLY,
            RebalancingFrequency.ANNUAL
        ]
        
        results = self.analyzer.analyze_time_based_rebalancing(
            target_allocation=self.test_allocation,
            frequencies=frequencies,
            account_type=AccountType.TAX_DEFERRED
        )
        
        # Verify results structure
        self.assertEqual(len(results), len(frequencies))
        
        for i, result in enumerate(results):
            self.assertIsInstance(result, RebalancingResult)
            self.assertEqual(result.frequency, frequencies[i])
            
            # Check metrics
            self.assertIsInstance(result.total_return, float)
            self.assertGreater(result.annualized_return, -1.0)  # Sanity check
            self.assertGreater(result.volatility, 0)
            
            # For tax-deferred accounts, tax costs should be zero
            self.assertEqual(result.total_tax_costs, 0)
            
            print(f"   📅 {result.strategy_name}: {result.total_return:.1%} return, "
                  f"{len(result.rebalancing_events)} rebalances")
        
        # Monthly should have more rebalancing events than annual
        monthly_events = len(results[0].rebalancing_events)
        annual_events = len(results[-1].rebalancing_events)
        self.assertGreater(monthly_events, annual_events,
                          "Monthly rebalancing should have more events than annual")
        
        print("✅ Test 3 PASSED: Time-based rebalancing analysis")
    
    def test_new_money_rebalancing_analysis(self):
        """Test new money rebalancing strategy"""
        monthly_contribution = 1000
        
        result = self.analyzer.analyze_new_money_rebalancing(
            target_allocation=self.test_allocation,
            monthly_contribution=monthly_contribution,
            account_type=AccountType.TAXABLE
        )
        
        # Verify result structure
        self.assertIsInstance(result, RebalancingResult)
        self.assertEqual(result.frequency, RebalancingFrequency.NEW_MONEY)
        self.assertIn("New Money", result.strategy_name)
        
        # Check that strategy had some performance
        self.assertIsInstance(result.total_return, float)
        self.assertGreater(result.total_return, -1.0)  # Sanity check
        
        # New money strategy should have lower costs than frequent rebalancing
        self.assertGreaterEqual(result.total_transaction_costs, 0)
        self.assertGreaterEqual(result.total_tax_costs, 0)
        
        print(f"   💵 {result.strategy_name}: {result.total_return:.1%} return, "
              f"{len(result.rebalancing_events)} rebalances, "
              f"${result.total_transaction_costs + result.total_tax_costs:.0f} costs")
        
        print("✅ Test 4 PASSED: New money rebalancing analysis")
    
    def test_strategy_comparison(self):
        """Test strategy comparison and ranking"""
        # Create different strategies to compare
        threshold_results = self.analyzer.analyze_threshold_rebalancing(
            target_allocation=self.test_allocation,
            threshold_percentages=[10],
            account_type=AccountType.TAXABLE
        )
        
        time_results = self.analyzer.analyze_time_based_rebalancing(
            target_allocation=self.test_allocation,
            frequencies=[RebalancingFrequency.QUARTERLY],
            account_type=AccountType.TAXABLE
        )
        
        new_money_result = self.analyzer.analyze_new_money_rebalancing(
            target_allocation=self.test_allocation,
            monthly_contribution=1000,
            account_type=AccountType.TAXABLE
        )
        
        all_results = threshold_results + time_results + [new_money_result]
        
        # Test comparison
        comparison = self.analyzer.compare_strategies(all_results)
        
        # Verify comparison structure
        self.assertIn('comparison_table', comparison)
        self.assertIn('best_strategy', comparison)
        self.assertIn('summary_stats', comparison)
        
        comparison_df = comparison['comparison_table']
        self.assertEqual(len(comparison_df), len(all_results))
        
        # Check that required columns exist
        required_columns = ['Strategy', 'Total Return', 'Sharpe Ratio', 'Total Costs', 'Overall Rank']
        for col in required_columns:
            self.assertIn(col, comparison_df.columns)
        
        # Verify ranking (rank 1 should be best)
        best_strategy = comparison_df.iloc[0]
        self.assertEqual(best_strategy['Overall Rank'], 1)
        
        print(f"   🏆 Best strategy: {comparison['best_strategy']}")
        print(f"   📊 Strategies compared: {len(all_results)}")
        print(f"   📈 Best return: {comparison['summary_stats']['best_return']:.1%}")
        print(f"   📉 Lowest costs: ${comparison['summary_stats']['lowest_costs']:.0f}")
        
        print("✅ Test 5 PASSED: Strategy comparison and ranking")
    
    def test_cost_parameters(self):
        """Test setting custom cost parameters"""
        # Test with higher transaction costs
        high_cost_rate = 0.005  # 0.5%
        custom_tax_rates = {
            'short_term': 0.40,
            'long_term': 0.25,
            'dividend': 0.25
        }
        
        self.analyzer.set_cost_parameters(
            transaction_cost=high_cost_rate,
            tax_rates=custom_tax_rates
        )
        
        self.assertEqual(self.analyzer.transaction_cost_rate, high_cost_rate)
        self.assertEqual(self.analyzer.tax_rates['short_term'], 0.40)
        self.assertEqual(self.analyzer.tax_rates['long_term'], 0.25)
        
        # Test with high-cost analysis
        results = self.analyzer.analyze_threshold_rebalancing(
            target_allocation=self.test_allocation,
            threshold_percentages=[10],
            account_type=AccountType.TAXABLE
        )
        
        self.assertEqual(len(results), 1)
        result = results[0]
        
        # High costs should result in higher total costs
        self.assertGreater(result.total_transaction_costs, 0)
        
        print(f"   💸 High-cost analysis: ${result.total_transaction_costs:.0f} transaction costs")
        
        print("✅ Test 6 PASSED: Custom cost parameters")
    
    def test_account_type_impact(self):
        """Test impact of different account types on tax costs"""
        # Test same strategy with different account types
        strategies = []
        
        for account_type in [AccountType.TAXABLE, AccountType.TAX_DEFERRED, AccountType.TAX_FREE]:
            results = self.analyzer.analyze_threshold_rebalancing(
                target_allocation=self.test_allocation,
                threshold_percentages=[15],
                account_type=account_type
            )
            strategies.append((account_type.value, results[0]))
        
        # Verify tax implications
        taxable_costs = strategies[0][1].total_tax_costs
        tax_deferred_costs = strategies[1][1].total_tax_costs  
        tax_free_costs = strategies[2][1].total_tax_costs
        
        # Tax-advantaged accounts should have zero tax costs
        self.assertEqual(tax_deferred_costs, 0)
        self.assertEqual(tax_free_costs, 0)
        
        # Taxable should have some tax costs (if there were any rebalancing events with gains)
        self.assertGreaterEqual(taxable_costs, 0)
        
        for account_type, result in strategies:
            print(f"   🏦 {account_type}: ${result.total_tax_costs:.0f} tax costs, "
                  f"${result.total_transaction_costs:.0f} transaction costs")
        
        print("✅ Test 7 PASSED: Account type impact on costs")


def run_comprehensive_test():
    """Run comprehensive test suite with detailed output"""
    print("🚀 STARTING COMPREHENSIVE REBALANCING STRATEGY ANALYZER TESTS")
    print("=" * 80)
    
    # Create test suite
    suite = unittest.TestLoader().loadTestsFromTestCase(TestRebalancingStrategyAnalyzer)
    
    # Run tests with verbose output
    runner = unittest.TextTestRunner(verbosity=2, stream=sys.stdout)
    result = runner.run(suite)
    
    print("\n" + "=" * 80)
    if result.wasSuccessful():
        print("🎉 ALL TESTS PASSED! Rebalancing Strategy Analyzer is working correctly.")
        print(f"✅ {result.testsRun} tests completed successfully")
    else:
        print("❌ SOME TESTS FAILED!")
        print(f"❌ Failures: {len(result.failures)}")
        print(f"❌ Errors: {len(result.errors)}")
        
        if result.failures:
            print("\nFAILURES:")
            for test, failure in result.failures:
                print(f"  - {test}: {failure}")
                
        if result.errors:
            print("\nERRORS:")
            for test, error in result.errors:
                print(f"  - {test}: {error}")
    
    return result.wasSuccessful()


if __name__ == "__main__":
    success = run_comprehensive_test()
    sys.exit(0 if success else 1)
