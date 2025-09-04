#!/usr/bin/env python3
"""
🎯 REGIME-AWARE ALLOCATION SYSTEM - SPRINT 9 PHASE 2

Purpose: Create adaptive portfolio allocation based on detected market regimes.
This system uses regime detection to optimize allocations for different market conditions.

REGIME-SPECIFIC STRATEGIES:
1. Growth Regime: High allocation to QQQ/tech, moderate VTI, low bonds
2. Value Regime: Higher VTI allocation, moderate defensive, avoid growth concentration  
3. Defensive Regime: High bonds, defensive assets, lower equity exposure
4. Transition Regime: Balanced approach, avoid concentration

This addresses the fundamental flaw discovered in Sprint 8 - our static approach
was just momentum betting that accidentally captured the Growth regime continuation.
"""

import sys
import os
sys.path.append('/Users/ashish/Claude/backtesting')

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from dataclasses import dataclass
from typing import Dict, List, Tuple, Optional
import warnings
warnings.filterwarnings('ignore')

# Import our systems
from src.optimization.portfolio_optimizer import PortfolioOptimizer, PortfolioRequest, AccountType
from regime_detection_system import RegimeDetectionSystem, MarketRegime, RegimeDetection

@dataclass
class RegimeAllocation:
    """Container for regime-specific allocation"""
    regime: MarketRegime
    allocation: Dict[str, float]
    expected_return: float
    expected_volatility: float
    sharpe_ratio: float
    rationale: str

@dataclass
class RegimeAwarePortfolio:
    """Container for regime-aware portfolio results"""
    date: str
    detected_regime: RegimeDetection
    regime_allocation: RegimeAllocation
    static_allocation: Dict[str, float]  # For comparison
    allocation_difference: Dict[str, float]
    expected_performance: Dict[str, float]

class RegimeAwareAllocationSystem:
    """
    Regime-aware portfolio allocation system that adapts to market conditions
    """
    
    def __init__(self):
        self.optimizer = PortfolioOptimizer()
        self.regime_detector = RegimeDetectionSystem()
        self.assets = ['VTI', 'VTIAX', 'BND', 'VNQ', 'GLD', 'VWO', 'QQQ']
        
        # Initialize regime-specific allocation strategies
        self.regime_strategies = self._initialize_regime_strategies()
        
        print("🎯 REGIME-AWARE ALLOCATION SYSTEM INITIALIZED")
        print("=" * 60)
        print("Approach: Adaptive allocation based on detected market regimes")
        print("Regimes: Growth, Value, Defensive, Transition")
        print("Assets: 7-asset universe with regime-specific weightings")
        print()

    def _initialize_regime_strategies(self) -> Dict[MarketRegime, Dict[str, float]]:
        """
        Initialize regime-specific allocation strategies based on historical analysis
        """
        strategies = {
            MarketRegime.GROWTH: {
                'QQQ': 0.55,    # Higher tech allocation in growth regimes
                'VTI': 0.20,    # Moderate broad market
                'BND': 0.05,    # Minimal bonds (growth environment) 
                'VNQ': 0.08,    # Real estate benefits from growth
                'GLD': 0.07,    # Some inflation hedge
                'VWO': 0.05,    # Emerging markets in growth
                'VTIAX': 0.00   # Avoid redundancy with VTI
            },
            
            MarketRegime.VALUE: {
                'VTI': 0.40,    # Higher broad market (value tilt)
                'QQQ': 0.25,    # Reduced tech concentration
                'BND': 0.15,    # More bonds for stability
                'VNQ': 0.10,    # Real estate value play
                'GLD': 0.05,    # Reduced gold
                'VTIAX': 0.05,  # Some international value
                'VWO': 0.00     # Avoid EM in value periods
            },
            
            MarketRegime.DEFENSIVE: {
                'BND': 0.40,    # High bond allocation
                'VTI': 0.25,    # Reduced equity exposure  
                'QQQ': 0.10,    # Minimal tech (defensive)
                'GLD': 0.15,    # Higher gold for safety
                'VNQ': 0.05,    # Reduced real estate
                'VTIAX': 0.05,  # Some international diversification
                'VWO': 0.00     # No emerging markets
            },
            
            MarketRegime.TRANSITION: {
                'VTI': 0.30,    # Balanced broad market
                'QQQ': 0.30,    # Balanced tech
                'BND': 0.20,    # Moderate bonds
                'VNQ': 0.08,    # Moderate real estate
                'GLD': 0.07,    # Moderate gold
                'VTIAX': 0.03,  # Small international
                'VWO': 0.02     # Small emerging markets
            }
        }
        
        return strategies

    def get_regime_allocation(self, regime: MarketRegime, confidence: float) -> RegimeAllocation:
        """
        Get allocation for a specific regime with confidence adjustment
        """
        base_allocation = self.regime_strategies[regime].copy()
        
        # Adjust allocation based on confidence level
        if confidence < 0.6:  # Low confidence - move toward transition allocation
            transition_allocation = self.regime_strategies[MarketRegime.TRANSITION]
            
            # Blend with transition allocation based on confidence
            blend_factor = (0.6 - confidence) / 0.6  # 0 to 1
            
            for asset in base_allocation:
                base_allocation[asset] = (
                    base_allocation[asset] * (1 - blend_factor) + 
                    transition_allocation.get(asset, 0) * blend_factor
                )
        
        # Normalize to ensure sum = 1.0
        total_weight = sum(base_allocation.values())
        if total_weight > 0:
            base_allocation = {k: v/total_weight for k, v in base_allocation.items()}
        
        # Calculate expected performance (simplified)
        expected_return, expected_volatility = self._estimate_regime_performance(regime, base_allocation)
        sharpe_ratio = expected_return / expected_volatility if expected_volatility > 0 else 0
        
        rationale = self._generate_allocation_rationale(regime, confidence, base_allocation)
        
        return RegimeAllocation(
            regime=regime,
            allocation=base_allocation,
            expected_return=expected_return,
            expected_volatility=expected_volatility,
            sharpe_ratio=sharpe_ratio,
            rationale=rationale
        )

    def _estimate_regime_performance(self, regime: MarketRegime, allocation: Dict[str, float]) -> Tuple[float, float]:
        """
        Estimate expected return and volatility for regime-specific allocation
        """
        # Historical regime performance estimates (simplified)
        regime_returns = {
            MarketRegime.GROWTH: 0.15,    # 15% expected in growth regimes
            MarketRegime.VALUE: 0.10,     # 10% expected in value regimes  
            MarketRegime.DEFENSIVE: 0.06, # 6% expected in defensive regimes
            MarketRegime.TRANSITION: 0.08 # 8% expected in transition
        }
        
        regime_volatilities = {
            MarketRegime.GROWTH: 0.16,    # Higher vol in growth
            MarketRegime.VALUE: 0.14,     # Moderate vol in value
            MarketRegime.DEFENSIVE: 0.08, # Lower vol in defensive  
            MarketRegime.TRANSITION: 0.12 # Moderate vol in transition
        }
        
        expected_return = regime_returns.get(regime, 0.08)
        expected_volatility = regime_volatilities.get(regime, 0.12)
        
        # Adjust based on allocation (simplified)
        # Higher equity = higher return and volatility
        equity_weight = allocation.get('QQQ', 0) + allocation.get('VTI', 0) + allocation.get('VTIAX', 0)
        bond_weight = allocation.get('BND', 0)
        
        # Equity adjustment
        if equity_weight > 0.7:
            expected_return += 0.02
            expected_volatility += 0.02
        elif equity_weight < 0.4:
            expected_return -= 0.02
            expected_volatility -= 0.02
        
        # Bond adjustment (stabilizing effect)
        if bond_weight > 0.3:
            expected_volatility -= 0.03
        
        return expected_return, expected_volatility

    def _generate_allocation_rationale(self, regime: MarketRegime, confidence: float, 
                                     allocation: Dict[str, float]) -> str:
        """
        Generate explanation for regime-specific allocation
        """
        rationale_parts = []
        
        # Regime-specific reasoning
        if regime == MarketRegime.GROWTH:
            rationale_parts.append("Growth regime favors technology and innovation sectors")
            if allocation.get('QQQ', 0) > 0.5:
                rationale_parts.append(f"High QQQ allocation ({allocation['QQQ']:.1%}) captures growth momentum")
            if allocation.get('BND', 0) < 0.1:
                rationale_parts.append("Minimal bond allocation due to growth environment")
                
        elif regime == MarketRegime.VALUE:
            rationale_parts.append("Value regime favors broad market over concentrated tech")
            if allocation.get('VTI', 0) > allocation.get('QQQ', 0):
                rationale_parts.append("VTI over QQQ weighting captures value opportunities")
            if allocation.get('BND', 0) > 0.1:
                rationale_parts.append("Increased bond allocation provides stability")
                
        elif regime == MarketRegime.DEFENSIVE:
            rationale_parts.append("Defensive regime requires capital preservation focus")
            if allocation.get('BND', 0) > 0.3:
                rationale_parts.append("High bond allocation protects against equity volatility")
            if allocation.get('GLD', 0) > 0.1:
                rationale_parts.append("Gold allocation hedges against market stress")
                
        else:  # TRANSITION
            rationale_parts.append("Transition regime requires balanced, diversified approach")
            rationale_parts.append("Avoiding concentration while maintaining growth exposure")
        
        # Confidence adjustment
        if confidence < 0.6:
            rationale_parts.append(f"Low regime confidence ({confidence:.1%}) - allocation blended with balanced approach")
        elif confidence > 0.8:
            rationale_parts.append(f"High regime confidence ({confidence:.1%}) - full regime-specific allocation")
        
        return ". ".join(rationale_parts)

    def get_static_allocation_for_comparison(self) -> Dict[str, float]:
        """
        Get static allocation (our current approach) for comparison
        """
        # This represents our current "momentum betting" static approach
        return {
            'QQQ': 0.50,
            'VTI': 0.22, 
            'BND': 0.28,
            'VNQ': 0.00,
            'GLD': 0.00,
            'VWO': 0.00,
            'VTIAX': 0.00
        }

    def create_regime_aware_portfolio(self, date: str) -> RegimeAwarePortfolio:
        """
        Create regime-aware portfolio for a specific date
        """
        # Detect regime for the date
        regime_detection = self.regime_detector.detect_regime_at_date(date)
        
        # Get regime-specific allocation
        regime_allocation = self.get_regime_allocation(
            regime_detection.regime, 
            regime_detection.confidence
        )
        
        # Get static allocation for comparison
        static_allocation = self.get_static_allocation_for_comparison()
        
        # Calculate allocation differences
        allocation_difference = {}
        for asset in self.assets:
            regime_weight = regime_allocation.allocation.get(asset, 0)
            static_weight = static_allocation.get(asset, 0)
            allocation_difference[asset] = regime_weight - static_weight
        
        # Expected performance comparison
        expected_performance = {
            'regime_return': regime_allocation.expected_return,
            'regime_volatility': regime_allocation.expected_volatility,
            'regime_sharpe': regime_allocation.sharpe_ratio,
            'static_return': 0.12,  # Our historical static performance
            'static_volatility': 0.14,
            'static_sharpe': 0.86
        }
        
        return RegimeAwarePortfolio(
            date=date,
            detected_regime=regime_detection,
            regime_allocation=regime_allocation,
            static_allocation=static_allocation,
            allocation_difference=allocation_difference,
            expected_performance=expected_performance
        )

    def analyze_regime_allocation_history(self, start_date: str = "2014-01-01",
                                        end_date: str = "2024-12-31") -> List[RegimeAwarePortfolio]:
        """
        Analyze regime-aware allocations across historical period
        """
        print(f"\n📊 ANALYZING REGIME-AWARE ALLOCATION HISTORY")
        print(f"Period: {start_date} to {end_date}")
        print("-" * 60)
        
        # Load regime detection history if not already loaded
        if not self.regime_detector.regime_history:
            print("Loading regime detection data...")
            self.regime_detector.load_historical_data()
            self.regime_detector.analyze_historical_regimes(start_date, end_date)
        
        # Create quarterly analysis points
        start_dt = pd.to_datetime(start_date)
        end_dt = pd.to_datetime(end_date)
        date_range = pd.date_range(start=start_dt, end=end_dt, freq='Q')  # Quarterly
        
        regime_portfolios = []
        
        print(f"Analyzing {len(date_range)} quarterly periods...")
        
        for i, date in enumerate(date_range):
            date_str = date.strftime('%Y-%m-%d')
            
            if i % 8 == 0:  # Progress every 2 years
                print(f"   Analyzing {date.year}...")
            
            portfolio = self.create_regime_aware_portfolio(date_str)
            regime_portfolios.append(portfolio)
        
        # Summary statistics
        print(f"\n✅ REGIME-AWARE ALLOCATION ANALYSIS COMPLETE")
        print("-" * 50)
        
        regime_counts = {}
        allocation_changes = 0
        previous_allocation = None
        
        for portfolio in regime_portfolios:
            regime = portfolio.detected_regime.regime
            regime_counts[regime] = regime_counts.get(regime, 0) + 1
            
            # Count allocation changes
            current_allocation = portfolio.regime_allocation.allocation
            if previous_allocation and current_allocation != previous_allocation:
                allocation_changes += 1
            previous_allocation = current_allocation
        
        print("REGIME DISTRIBUTION IN ANALYSIS PERIOD:")
        for regime, count in regime_counts.items():
            percentage = count / len(regime_portfolios) * 100
            print(f"{regime.value.title():12}: {count:2d} periods ({percentage:4.1f}%)")
        
        print(f"\nAllocation Changes: {allocation_changes}")
        print(f"Change Frequency: {allocation_changes / len(regime_portfolios):.2f} per quarter")
        
        return regime_portfolios

    def display_current_regime_recommendation(self):
        """
        Display current regime-aware allocation recommendation
        """
        print(f"\n🎯 CURRENT REGIME-AWARE ALLOCATION RECOMMENDATION")
        print("=" * 60)
        
        current_date = datetime.now().strftime('%Y-%m-%d')
        current_portfolio = self.create_regime_aware_portfolio(current_date)
        
        detection = current_portfolio.detected_regime
        allocation = current_portfolio.regime_allocation
        
        print(f"Date: {current_date}")
        print(f"Detected Regime: {detection.regime.value.title()} ({detection.confidence:.1%} confidence)")
        print(f"Regime Strength: {detection.strength.value.title()}")
        print()
        
        print("REGIME EXPLANATION:")
        print(detection.explanation)
        print()
        
        print("REGIME-AWARE ALLOCATION:")
        print("-" * 30)
        for asset, weight in sorted(allocation.allocation.items(), key=lambda x: x[1], reverse=True):
            if weight > 0:
                print(f"{asset:6}: {weight:5.1%}")
        
        print(f"\nExpected Performance:")
        print(f"Return: {allocation.expected_return:.1%}")
        print(f"Volatility: {allocation.expected_volatility:.1%}")
        print(f"Sharpe Ratio: {allocation.sharpe_ratio:.2f}")
        
        print(f"\nALLOCATION RATIONALE:")
        print(allocation.rationale)
        
        print(f"\n📈 COMPARISON VS STATIC APPROACH:")
        print("-" * 40)
        
        static = current_portfolio.static_allocation
        differences = current_portfolio.allocation_difference
        
        print("Asset     Regime    Static    Difference")
        print("-" * 40)
        for asset in self.assets:
            regime_weight = allocation.allocation.get(asset, 0)
            static_weight = static.get(asset, 0)
            diff = differences.get(asset, 0)
            
            if regime_weight > 0.01 or static_weight > 0.01:
                diff_str = f"{diff:+5.1%}" if abs(diff) > 0.01 else "  --"
                print(f"{asset:8} {regime_weight:6.1%}   {static_weight:6.1%}   {diff_str}")
        
        # Performance comparison
        perf = current_portfolio.expected_performance
        print(f"\nExpected Performance Comparison:")
        print(f"                 Regime    Static")
        print(f"Return:         {perf['regime_return']:6.1%}    {perf['static_return']:6.1%}")
        print(f"Volatility:     {perf['regime_volatility']:6.1%}    {perf['static_volatility']:6.1%}")
        print(f"Sharpe Ratio:   {perf['regime_sharpe']:6.2f}    {perf['static_sharpe']:6.2f}")

    def display_regime_strategy_summary(self):
        """
        Display summary of regime-specific strategies
        """
        print(f"\n📋 REGIME-SPECIFIC ALLOCATION STRATEGIES")
        print("=" * 60)
        
        for regime, allocation in self.regime_strategies.items():
            print(f"\n{regime.value.upper()} REGIME STRATEGY:")
            print("-" * 30)
            
            # Sort by allocation weight
            sorted_allocation = sorted(allocation.items(), key=lambda x: x[1], reverse=True)
            
            for asset, weight in sorted_allocation:
                if weight > 0:
                    print(f"{asset:6}: {weight:5.1%}")
            
            # Get rationale for max confidence
            regime_allocation = self.get_regime_allocation(regime, 1.0)  # Max confidence
            print(f"\nRationale: {regime_allocation.rationale}")


def main():
    """
    Main function to demonstrate regime-aware allocation system
    """
    print("🚀 STARTING REGIME-AWARE ALLOCATION SYSTEM")
    print("=" * 80)
    
    # Initialize system
    regime_allocator = RegimeAwareAllocationSystem()
    
    # Load regime detection system
    print("Loading regime detection system...")
    regime_allocator.regime_detector.load_historical_data()
    
    # Display regime-specific strategies
    regime_allocator.display_regime_strategy_summary()
    
    # Show current recommendation
    regime_allocator.display_current_regime_recommendation()
    
    # Analyze historical regime allocations
    historical_portfolios = regime_allocator.analyze_regime_allocation_history()
    
    print(f"\n🎉 REGIME-AWARE ALLOCATION SYSTEM ANALYSIS COMPLETE")
    print(f"✅ System ready for regime-aware optimization testing")
    print(f"✅ Historical analysis shows {len(historical_portfolios)} quarterly allocations")
    print(f"✅ Ready to compare against static momentum betting approach")

if __name__ == "__main__":
    main()
