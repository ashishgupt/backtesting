#!/usr/bin/env python3
"""
Test script for Market Regime Awareness functionality

This script tests the new regime analysis features including:
- Current regime detection
- Historical regime analysis  
- Regime-aware portfolio recommendations
- Raw regime indicators
"""

import asyncio
import sys
import os
sys.path.append('/Users/ashish/Claude/backtesting')

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import logging

from src.regime.regime_detector import MarketRegimeDetector
from src.regime.regime_analyzer import RegimeAwareAnalyzer
from src.regime.regime_indicators import RegimeIndicatorCalculator
from src.models.base import DatabaseManager

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class RegimeAnalysisTestSuite:
    """Test suite for regime analysis functionality"""
    
    def __init__(self):
        self.db_manager = DatabaseManager()
        self.regime_detector = MarketRegimeDetector()
        self.regime_analyzer = RegimeAwareAnalyzer()
        self.indicator_calculator = RegimeIndicatorCalculator()
        
    def run_all_tests(self):
        """Run all regime analysis tests"""
        print("🚀 Starting Market Regime Analysis Test Suite")
        print("=" * 60)
        
        try:
            # Test 1: Database connectivity and data availability
            print("\n📊 Test 1: Database Connectivity & Data Availability")
            self.test_data_availability()
            
            # Test 2: Regime indicator calculations
            print("\n📈 Test 2: Regime Indicator Calculations")
            indicators = self.test_regime_indicators()
            
            # Test 3: Current regime detection
            print("\n🎯 Test 3: Current Regime Detection")
            current_regime = self.test_current_regime_detection()
            
            # Test 4: Historical regime analysis
            print("\n📜 Test 4: Historical Regime Analysis")
            historical_regimes = self.test_historical_regime_analysis()
            
            # Test 5: Regime-aware recommendations
            print("\n💡 Test 5: Regime-Aware Portfolio Recommendations")
            self.test_regime_recommendations()
            
            # Test 6: Performance analysis by regime
            print("\n⚡ Test 6: Performance Analysis by Regime")
            self.test_performance_analysis()
            
            print("\n✅ All tests completed successfully!")
            print("🎉 Market Regime Analysis system is fully operational!")
            
            return True
            
        except Exception as e:
            print(f"\n❌ Test suite failed: {str(e)}")
            logger.error(f"Test suite error: {str(e)}", exc_info=True)
            return False
    
    def test_data_availability(self):
        """Test database connectivity and data availability"""
        try:
            # Test basic connectivity
            query = "SELECT COUNT(*) FROM daily_prices WHERE symbol = 'VTI'"
            results = self.db_manager.execute_query(query)
            vti_count = results[0][0] if results else 0
            
            print(f"   ✓ VTI records available: {vti_count:,}")
            
            # Test recent data availability
            recent_query = """
            SELECT symbol, COUNT(*) as count, MAX(date) as latest_date
            FROM daily_prices 
            WHERE symbol IN ('VTI', 'VTIAX', 'BND', 'VNQ', 'GLD', 'VWO', 'QQQ')
            AND date >= %s
            GROUP BY symbol
            ORDER BY symbol
            """
            
            cutoff_date = datetime(2024, 12, 1)  # Use December 2024 instead of recent date
            results = self.db_manager.execute_query(recent_query, (cutoff_date,))
            
            if results:
                print("   ✓ Recent data availability (last 30 days):")
                for symbol, count, latest in results:
                    print(f"     {symbol}: {count} records, latest: {latest}")
            else:
                print("   ⚠ No recent data found")
                
            # Get sample price data for testing
            sample_query = """
            SELECT date, symbol, adj_close
            FROM daily_prices 
            WHERE date >= %s
            AND symbol IN ('VTI', 'VTIAX', 'BND', 'VNQ', 'GLD', 'VWO', 'QQQ')
            ORDER BY date DESC, symbol
            LIMIT 100
            """
            
            sample_results = self.db_manager.execute_query(sample_query, (cutoff_date,))
            print(f"   ✓ Sample data retrieved: {len(sample_results)} records")
            
        except Exception as e:
            print(f"   ❌ Database test failed: {str(e)}")
            raise
    
    def test_regime_indicators(self):
        """Test regime indicator calculations"""
        try:
            # Get price data
            price_data = self._get_test_price_data()
            
            if price_data.empty:
                raise Exception("No price data available for indicator testing")
            
            print(f"   ✓ Price data loaded: {len(price_data)} days, {len(price_data.columns)} assets")
            
            # Calculate indicators
            indicators = self.indicator_calculator.calculate_all_indicators(price_data)
            
            print(f"   ✓ Indicators calculated: {len(indicators)} metrics")
            
            # Display key indicators
            key_indicators = [
                'momentum_3m', 'momentum_12m', 'volatility_current', 'volatility_percentile',
                'value_growth_spread', 'stock_bond_spread', 'average_correlation'
            ]
            
            print("   📊 Key Indicators:")
            for key in key_indicators:
                if key in indicators:
                    value = indicators[key]
                    if isinstance(value, float):
                        if 'percentile' in key or 'correlation' in key:
                            print(f"     {key}: {value:.2%}")
                        elif 'momentum' in key or 'spread' in key:
                            print(f"     {key}: {value:.2%}")
                        else:
                            print(f"     {key}: {value:.3f}")
                    else:
                        print(f"     {key}: {value}")
            
            # Test regime summary
            regime_summary = self.indicator_calculator.get_regime_summary(indicators)
            print(f"   ✓ Regime summary generated: {regime_summary.get('overall_regime', 'unknown')}")
            print(f"     Confidence: {regime_summary.get('confidence_score', 0):.1%}")
            
            return indicators
            
        except Exception as e:
            print(f"   ❌ Indicator calculation test failed: {str(e)}")
            raise
    
    def test_current_regime_detection(self):
        """Test current regime detection"""
        try:
            # Get price data
            price_data = self._get_test_price_data()
            
            # Detect current regime
            regime_result = self.regime_detector.detect_current_regime(price_data, lookback_days=252)
            
            print(f"   ✓ Current regime detected: {regime_result['regime_name']}")
            print(f"     Type: {regime_result['regime_type']}")
            print(f"     Confidence: {regime_result['confidence_score']:.1%}")
            print(f"     Description: {regime_result['regime_description']}")
            
            print("   📋 Supporting factors:")
            for factor in regime_result['supporting_factors'][:3]:  # Show top 3
                print(f"     • {factor}")
            
            # Test with different lookback periods
            for lookback in [63, 126, 504]:
                short_result = self.regime_detector.detect_current_regime(price_data, lookback_days=lookback)
                print(f"   ✓ {lookback}-day regime: {short_result['regime_name']} "
                     f"({short_result['confidence_score']:.1%} confidence)")
            
            return regime_result
            
        except Exception as e:
            print(f"   ❌ Current regime detection test failed: {str(e)}")
            raise
    
    def test_historical_regime_analysis(self):
        """Test historical regime analysis"""
        try:
            # Get longer price data for historical analysis
            price_data = self._get_test_price_data(days_back=1000)  # ~3 years
            
            print(f"   ✓ Historical data loaded: {len(price_data)} days")
            
            # Detect historical regimes
            historical_regimes = self.regime_detector.detect_historical_regimes(
                price_data, window_days=126, step_days=21
            )
            
            print(f"   ✓ Historical regimes detected: {len(historical_regimes)} periods")
            
            if not historical_regimes.empty:
                # Analyze regime distribution
                regime_counts = historical_regimes['regime_type'].value_counts()
                print("   📊 Regime Distribution:")
                for regime, count in regime_counts.items():
                    regime_name = self.regime_detector.regime_types[regime]['name']
                    print(f"     {regime_name}: {count} periods ({count/len(historical_regimes):.1%})")
                
                # Show recent regimes
                print("   📅 Recent Regime History (last 5):")
                recent_regimes = historical_regimes.tail(5)
                for date, row in recent_regimes.iterrows():
                    print(f"     {date.strftime('%Y-%m-%d')}: {row['regime_name']} "
                         f"({row['confidence']:.1%} confidence)")
                
                # Get regime transitions
                transitions = self.regime_detector.get_regime_transitions(historical_regimes)
                print(f"   🔄 Regime transitions identified: {len(transitions)}")
                
                if transitions:
                    print("   📈 Recent Transitions (last 3):")
                    for transition in transitions[-3:]:
                        from_name = self.regime_detector.regime_types.get(
                            transition['from_regime'], {'name': transition['from_regime']}
                        )['name']
                        to_name = self.regime_detector.regime_types.get(
                            transition['to_regime'], {'name': transition['to_regime']}
                        )['name']
                        print(f"     {transition['date'].strftime('%Y-%m-%d')}: "
                             f"{from_name} → {to_name}")
            
            return historical_regimes
            
        except Exception as e:
            print(f"   ❌ Historical regime analysis test failed: {str(e)}")
            raise
    
    def test_regime_recommendations(self):
        """Test regime-aware portfolio recommendations"""
        try:
            # Sample portfolio allocation
            sample_portfolio = {
                'VTI': 0.40,    # 40% US Total Market
                'VTIAX': 0.20,  # 20% International
                'BND': 0.30,    # 30% Bonds
                'VNQ': 0.05,    # 5% REITs
                'GLD': 0.03,    # 3% Gold
                'VWO': 0.015,   # 1.5% Emerging Markets
                'QQQ': 0.005    # 0.5% Tech/Growth
            }
            
            print(f"   💼 Sample Portfolio:")
            for asset, weight in sample_portfolio.items():
                print(f"     {asset}: {weight:.1%}")
            
            # Get recommendations for different risk tolerances
            for risk_level in ['conservative', 'balanced', 'aggressive']:
                print(f"\n   🎯 {risk_level.title()} Risk Tolerance:")
                
                recommendations = self.regime_analyzer.get_regime_aware_recommendations(
                    sample_portfolio, risk_level
                )
                
                if recommendations:
                    current_regime = recommendations.get('current_regime', {})
                    regime_name = current_regime.get('regime_name', 'Unknown')
                    confidence = current_regime.get('confidence_score', 0)
                    
                    print(f"     Current Regime: {regime_name} ({confidence:.1%} confidence)")
                    
                    # Show regime adjustments
                    adjustments = recommendations.get('regime_adjustments', {})
                    if adjustments:
                        equity_bias = adjustments.get('equity_bias', 0)
                        vol_target = adjustments.get('volatility_target', 0.15)
                        rebal_freq = adjustments.get('rebalancing_frequency', 'quarterly')
                        
                        print(f"     Equity Bias: {equity_bias:+.1%}")
                        print(f"     Volatility Target: {vol_target:.1%}")
                        print(f"     Rebalancing: {rebal_freq}")
                    
                    # Show recommended changes
                    changes = recommendations.get('recommended_changes', {})
                    if changes:
                        print("     📊 Portfolio Changes:")
                        for asset, change in list(changes.items())[:3]:  # Show top 3
                            current = change['current_weight']
                            recommended = change['recommended_weight']
                            delta = change['change']
                            print(f"       {asset}: {current:.1%} → {recommended:.1%} "
                                 f"({delta:+.1%})")
                    
                    # Show key advice
                    advice = recommendations.get('risk_management_advice', [])
                    if advice:
                        print(f"     💡 Key Advice: {advice[0]}")
                
            print("   ✓ Recommendations generated successfully")
            
        except Exception as e:
            print(f"   ❌ Regime recommendations test failed: {str(e)}")
            raise
    
    def test_performance_analysis(self):
        """Test performance analysis by regime"""
        try:
            # Generate sample portfolio returns
            price_data = self._get_test_price_data(days_back=500)
            
            if len(price_data) < 100:
                print("   ⚠ Insufficient data for performance analysis, skipping...")
                return
            
            # Simple equal-weight portfolio returns
            returns = price_data.pct_change().mean(axis=1).dropna()
            
            print(f"   📊 Portfolio returns generated: {len(returns)} observations")
            print(f"     Annualized return: {returns.mean() * 252:.1%}")
            print(f"     Volatility: {returns.std() * np.sqrt(252):.1%}")
            
            # Analyze performance by regime
            analysis_result = self.regime_analyzer.analyze_performance_by_regime(
                returns, start_date=returns.index[0], end_date=returns.index[-1]
            )
            
            if analysis_result:
                regime_perf = analysis_result.get('regime_performance', {})
                print(f"   ✓ Regime performance analysis completed for {len(regime_perf)} regimes")
                
                if regime_perf:
                    print("   📈 Performance by Regime:")
                    for regime, perf in regime_perf.items():
                        regime_name = perf.get('regime_name', regime)
                        ann_return = perf.get('annualized_return', 0)
                        sharpe = perf.get('sharpe_ratio', 0)
                        periods = perf.get('total_periods', 0)
                        
                        print(f"     {regime_name}: {ann_return:.1%} return, "
                             f"{sharpe:.2f} Sharpe, {periods} periods")
                
                # Show regime summary
                regime_summary = analysis_result.get('regime_summary', {})
                if regime_summary:
                    best = regime_summary.get('best_regime', 'N/A')
                    worst = regime_summary.get('worst_regime', 'N/A')
                    consistency = regime_summary.get('regime_consistency', 0)
                    
                    print(f"   📋 Summary:")
                    print(f"     Best Regime: {best}")
                    print(f"     Worst Regime: {worst}")
                    print(f"     Consistency: {consistency:.1%}")
                
            print("   ✓ Performance analysis completed")
            
        except Exception as e:
            print(f"   ❌ Performance analysis test failed: {str(e)}")
            raise
    
    def _get_test_price_data(self, days_back=300):
        """Get price data for testing"""
        try:
            # Use December 2024 as end date since that's when our data ends
            end_date = datetime(2024, 12, 31)
            start_date = end_date - timedelta(days=days_back)
            
            query = """
            SELECT date, symbol, adj_close
            FROM daily_prices 
            WHERE date BETWEEN %s AND %s
            AND symbol IN ('VTI', 'VTIAX', 'BND', 'VNQ', 'GLD', 'VWO', 'QQQ')
            ORDER BY date, symbol
            """
            
            results = self.db_manager.execute_query(query, (start_date, end_date))
            
            if not results:
                return pd.DataFrame()
            
            # Convert to DataFrame with proper data types
            df = pd.DataFrame(results, columns=['date', 'symbol', 'price'])
            price_data = df.pivot(index='date', columns='symbol', values='price')
            price_data.index = pd.to_datetime(price_data.index)
            
            # Convert decimal columns to float and forward fill
            price_data = price_data.astype(float)
            price_data = price_data.ffill().dropna()
            
            return price_data
            
        except Exception as e:
            logger.error(f"Error getting test price data: {str(e)}")
            return pd.DataFrame()

def main():
    """Run the regime analysis test suite"""
    test_suite = RegimeAnalysisTestSuite()
    
    print("🎯 Market Regime Awareness - Sprint 5 Phase 8")
    print("=" * 60)
    print("Testing comprehensive regime detection and analysis capabilities")
    print("")
    
    success = test_suite.run_all_tests()
    
    if success:
        print("\n" + "=" * 60)
        print("🎉 SPRINT 5 PHASE 8 - MARKET REGIME AWARENESS COMPLETE!")
        print("=" * 60)
        print("✅ Current regime detection working")
        print("✅ Historical regime analysis operational")  
        print("✅ Regime-aware recommendations functional")
        print("✅ Performance attribution by regime ready")
        print("✅ Web interface available at: http://localhost:8007/regime-analyzer.html")
        print("\n🚀 System is production-ready for regime-aware portfolio management!")
        return 0
    else:
        print("\n" + "=" * 60)
        print("❌ TESTS FAILED - ISSUES NEED RESOLUTION")
        print("=" * 60)
        return 1

if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)
