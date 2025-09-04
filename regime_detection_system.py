#!/usr/bin/env python3
"""
🌊 MARKET REGIME DETECTION SYSTEM - SPRINT 9 PHASE 1

Purpose: Identify different market regimes (Value vs Growth vs Defensive) historically
and in real-time to enable regime-aware portfolio allocation.

REGIME TYPES:
1. Value Regime: Value stocks outperform growth, low P/E ratios dominate
2. Growth Regime: Growth stocks outperform value, high P/E acceptable  
3. Defensive Regime: Bonds/utilities outperform equity, risk-off sentiment

DETECTION METHODS:
- Relative Performance: Value ETFs vs Growth ETFs vs Defensive assets
- Fundamental Indicators: P/E ratios, yield spreads, economic indicators
- Technical Indicators: Market momentum, volatility patterns
- Sector Rotation: Which sectors are leading/lagging

This system will form the foundation for regime-aware allocation optimization.
"""

import sys
import os
sys.path.append('/Users/ashish/Claude/backtesting')

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import matplotlib.pyplot as plt
import seaborn as sns
from dataclasses import dataclass
from typing import Dict, List, Tuple, Optional, Union
from enum import Enum
import warnings
warnings.filterwarnings('ignore')

# Import our existing system components
from src.optimization.portfolio_optimizer import PortfolioOptimizer

class MarketRegime(Enum):
    """Market regime types"""
    VALUE = "value"
    GROWTH = "growth"
    DEFENSIVE = "defensive"
    TRANSITION = "transition"  # Unclear regime
    
class RegimeStrength(Enum):
    """Regime conviction levels"""
    STRONG = "strong"      # >70% confidence
    MODERATE = "moderate"  # 50-70% confidence  
    WEAK = "weak"         # <50% confidence

@dataclass
class RegimeDetection:
    """Container for regime detection results"""
    date: str
    regime: MarketRegime
    strength: RegimeStrength
    confidence: float  # 0-1 probability
    indicators: Dict[str, float]  # Supporting indicators
    explanation: str  # Human readable explanation

@dataclass 
class RegimePeriod:
    """Container for regime period information"""
    start_date: str
    end_date: str
    regime: MarketRegime
    duration_months: int
    avg_confidence: float
    key_events: List[str]
    performance_data: Dict[str, float]

class RegimeDetectionSystem:
    """
    Comprehensive market regime detection system
    """
    
    def __init__(self):
        self.optimizer = PortfolioOptimizer()
        
        # Regime detection parameters
        self.lookback_months = 12  # Rolling window for regime assessment
        self.confidence_threshold = 0.6  # Minimum confidence for regime call
        
        # Asset proxies for regime detection
        self.regime_assets = {
            'value_proxy': 'VTI',      # We'll use broad market as proxy
            'growth_proxy': 'QQQ',     # Tech-heavy for growth
            'defensive_proxy': 'BND'   # Bonds for defensive
        }
        
        print("🌊 MARKET REGIME DETECTION SYSTEM INITIALIZED")
        print("=" * 60)
        print("Regime Types: Value, Growth, Defensive, Transition")
        print("Detection Methods: Relative performance, fundamentals, technicals")
        print("Assets: VTI (Value Proxy), QQQ (Growth Proxy), BND (Defensive)")
        print()
        
        # Initialize historical data
        self.historical_data = None
        self.regime_history = []
        self.regime_periods = []

    def load_historical_data(self) -> pd.DataFrame:
        """
        Load and prepare historical data for regime detection
        """
        print("📊 LOADING HISTORICAL DATA FOR REGIME DETECTION")
        print("-" * 50)
        
        try:
            # Get historical data from our optimizer
            raw_data = self.optimizer._get_historical_data(20)  # 20 years of data
            
            print(f"✅ Loaded {len(raw_data)} data points")
            print(f"Date range: {raw_data['Date'].min()} to {raw_data['Date'].max()}")
            
            # Convert to wide format for easier analysis
            wide_data = raw_data.pivot_table(
                index='Date',
                columns='Symbol',
                values='AdjClose',
                aggfunc='first'
            )
            
            # Forward fill missing data
            wide_data = wide_data.fillna(method='ffill')
            
            # Calculate returns for each asset
            returns_data = {}
            for asset in self.regime_assets.values():
                if asset in wide_data.columns:
                    prices = wide_data[asset]
                    returns = prices.pct_change().fillna(0)
                    returns_data[asset] = returns
                    print(f"   ✅ {asset}: {len(returns)} return observations")
            
            # Create comprehensive dataset
            analysis_data = pd.DataFrame(index=wide_data.index)
            
            # Add price data
            for asset in self.regime_assets.values():
                if asset in wide_data.columns:
                    analysis_data[f'{asset}_price'] = wide_data[asset]
                    analysis_data[f'{asset}_return'] = returns_data[asset]
            
            # Add rolling performance metrics
            window = 252  # 1 year rolling window
            
            for asset in self.regime_assets.values():
                if f'{asset}_return' in analysis_data.columns:
                    # Rolling annual returns
                    analysis_data[f'{asset}_annual_return'] = (
                        analysis_data[f'{asset}_return'].rolling(window).apply(
                            lambda x: (1 + x).prod() ** (252/len(x)) - 1
                        )
                    )
                    
                    # Rolling volatility
                    analysis_data[f'{asset}_volatility'] = (
                        analysis_data[f'{asset}_return'].rolling(window).std() * np.sqrt(252)
                    )
            
            # Add relative performance indicators
            if 'QQQ_annual_return' in analysis_data.columns and 'VTI_annual_return' in analysis_data.columns:
                # Growth vs Value performance spread
                analysis_data['growth_value_spread'] = (
                    analysis_data['QQQ_annual_return'] - analysis_data['VTI_annual_return']
                )
            
            if 'BND_annual_return' in analysis_data.columns and 'VTI_annual_return' in analysis_data.columns:
                # Defensive vs Equity performance spread  
                analysis_data['defensive_equity_spread'] = (
                    analysis_data['BND_annual_return'] - analysis_data['VTI_annual_return']
                )
            
            # Add market stress indicators
            if 'VTI_volatility' in analysis_data.columns:
                # High volatility periods (>20% annualized)
                analysis_data['high_volatility'] = analysis_data['VTI_volatility'] > 0.20
                
                # Volatility trend (increasing stress)
                analysis_data['volatility_trend'] = (
                    analysis_data['VTI_volatility'].rolling(60).apply(
                        lambda x: np.polyfit(range(len(x)), x, 1)[0] if len(x) > 1 else 0
                    )
                )
            
            self.historical_data = analysis_data
            
            print(f"✅ Prepared regime detection dataset with {len(analysis_data.columns)} indicators")
            print(f"   Date range: {analysis_data.index.min()} to {analysis_data.index.max()}")
            
            return analysis_data
            
        except Exception as e:
            print(f"❌ Error loading historical data: {e}")
            import traceback
            traceback.print_exc()
            return None

    def detect_regime_at_date(self, date: str) -> RegimeDetection:
        """
        Detect market regime at a specific date using available data up to that point
        """
        try:
            target_date = pd.to_datetime(date)
            
            if self.historical_data is None:
                raise ValueError("Historical data not loaded. Call load_historical_data() first.")
            
            # Get data available up to target date - ensure both sides are Timestamps
            available_data = self.historical_data[
                pd.to_datetime(self.historical_data.index) <= target_date
            ].copy()
            
            if len(available_data) < 252:  # Need at least 1 year of data
                return RegimeDetection(
                    date=date,
                    regime=MarketRegime.TRANSITION,
                    strength=RegimeStrength.WEAK,
                    confidence=0.0,
                    indicators={},
                    explanation="Insufficient historical data for regime detection"
                )
            
            # Get most recent data point for analysis
            latest_data = available_data.iloc[-1]
            
            # Initialize indicators dictionary
            indicators = {}
            regime_scores = {
                MarketRegime.VALUE: 0.0,
                MarketRegime.GROWTH: 0.0, 
                MarketRegime.DEFENSIVE: 0.0
            }
            
            # Indicator 1: Growth vs Value Performance Spread
            if 'growth_value_spread' in latest_data and not pd.isna(latest_data['growth_value_spread']):
                spread = latest_data['growth_value_spread']
                indicators['growth_value_spread'] = spread
                
                if spread > 0.05:  # Growth outperforming by >5%
                    regime_scores[MarketRegime.GROWTH] += 2.0
                elif spread < -0.05:  # Value outperforming by >5%
                    regime_scores[MarketRegime.VALUE] += 2.0
                else:
                    # Neutral performance - slight edge to current trend
                    if spread > 0:
                        regime_scores[MarketRegime.GROWTH] += 0.5
                    else:
                        regime_scores[MarketRegime.VALUE] += 0.5
            
            # Indicator 2: Defensive vs Equity Performance Spread
            if 'defensive_equity_spread' in latest_data and not pd.isna(latest_data['defensive_equity_spread']):
                def_spread = latest_data['defensive_equity_spread'] 
                indicators['defensive_equity_spread'] = def_spread
                
                if def_spread > 0.03:  # Defensive outperforming by >3%
                    regime_scores[MarketRegime.DEFENSIVE] += 2.0
                elif def_spread < -0.10:  # Equity significantly outperforming
                    # Strong equity performance - favor growth over value in modern markets
                    regime_scores[MarketRegime.GROWTH] += 1.0
                    regime_scores[MarketRegime.VALUE] += 0.5
            
            # Indicator 3: Market Volatility Level
            if 'VTI_volatility' in latest_data and not pd.isna(latest_data['VTI_volatility']):
                volatility = latest_data['VTI_volatility']
                indicators['market_volatility'] = volatility
                
                if volatility > 0.25:  # High volatility (>25%)
                    regime_scores[MarketRegime.DEFENSIVE] += 1.5
                elif volatility < 0.15:  # Low volatility (<15%)  
                    regime_scores[MarketRegime.GROWTH] += 1.0
                    regime_scores[MarketRegime.VALUE] += 0.5
            
            # Indicator 4: Volatility Trend
            if 'volatility_trend' in latest_data and not pd.isna(latest_data['volatility_trend']):
                vol_trend = latest_data['volatility_trend']
                indicators['volatility_trend'] = vol_trend
                
                if vol_trend > 0.001:  # Rising volatility
                    regime_scores[MarketRegime.DEFENSIVE] += 1.0
                elif vol_trend < -0.001:  # Falling volatility
                    regime_scores[MarketRegime.GROWTH] += 0.5
            
            # Indicator 5: Recent Performance Momentum (last 6 months)
            lookback_period = 126  # ~6 months
            if len(available_data) >= lookback_period:
                recent_data = available_data.iloc[-lookback_period:]
                
                # Calculate recent performance for each regime proxy
                if 'QQQ_return' in recent_data.columns:
                    qqq_recent = (1 + recent_data['QQQ_return']).prod() - 1
                    indicators['qqq_6m_return'] = qqq_recent
                    
                if 'VTI_return' in recent_data.columns:
                    vti_recent = (1 + recent_data['VTI_return']).prod() - 1  
                    indicators['vti_6m_return'] = vti_recent
                    
                if 'BND_return' in recent_data.columns:
                    bnd_recent = (1 + recent_data['BND_return']).prod() - 1
                    indicators['bnd_6m_return'] = bnd_recent
                
                # Award points based on recent momentum
                if 'qqq_6m_return' in indicators and 'vti_6m_return' in indicators:
                    if indicators['qqq_6m_return'] > indicators['vti_6m_return'] + 0.02:
                        regime_scores[MarketRegime.GROWTH] += 1.0
                    elif indicators['vti_6m_return'] > indicators['qqq_6m_return'] + 0.02:
                        regime_scores[MarketRegime.VALUE] += 1.0
            
            # Determine winning regime
            max_score = max(regime_scores.values())
            if max_score == 0:
                # No clear signals
                detected_regime = MarketRegime.TRANSITION
                confidence = 0.0
            else:
                detected_regime = max(regime_scores, key=regime_scores.get)
                # Normalize confidence (0-1)
                total_score = sum(regime_scores.values())
                confidence = regime_scores[detected_regime] / total_score if total_score > 0 else 0.0
            
            # Determine strength
            if confidence >= 0.7:
                strength = RegimeStrength.STRONG
            elif confidence >= 0.5:
                strength = RegimeStrength.MODERATE
            else:
                strength = RegimeStrength.WEAK
            
            # Generate explanation
            explanation = self._generate_regime_explanation(
                detected_regime, confidence, indicators, regime_scores
            )
            
            return RegimeDetection(
                date=date,
                regime=detected_regime,
                strength=strength, 
                confidence=confidence,
                indicators=indicators,
                explanation=explanation
            )
            
        except Exception as e:
            print(f"❌ Error detecting regime for {date}: {e}")
            return RegimeDetection(
                date=date,
                regime=MarketRegime.TRANSITION,
                strength=RegimeStrength.WEAK,
                confidence=0.0,
                indicators={},
                explanation=f"Error in regime detection: {str(e)}"
            )

    def _generate_regime_explanation(self, regime: MarketRegime, confidence: float,
                                   indicators: Dict, scores: Dict) -> str:
        """
        Generate human-readable explanation for regime detection
        """
        explanation_parts = []
        
        # Main regime determination
        explanation_parts.append(f"{regime.value.title()} regime detected with {confidence:.1%} confidence")
        
        # Key supporting factors
        if 'growth_value_spread' in indicators:
            spread = indicators['growth_value_spread']
            if abs(spread) > 0.02:
                if spread > 0:
                    explanation_parts.append(f"Growth outperforming Value by {spread:.1%}")
                else:
                    explanation_parts.append(f"Value outperforming Growth by {abs(spread):.1%}")
        
        if 'market_volatility' in indicators:
            vol = indicators['market_volatility']
            if vol > 0.25:
                explanation_parts.append("High market volatility suggests defensive positioning")
            elif vol < 0.15:
                explanation_parts.append("Low volatility environment favors risk assets")
        
        if 'defensive_equity_spread' in indicators:
            def_spread = indicators['defensive_equity_spread']
            if def_spread > 0.03:
                explanation_parts.append("Bonds outperforming equities - defensive regime")
            elif def_spread < -0.05:
                explanation_parts.append("Equities significantly outperforming bonds")
        
        # Recent momentum
        if 'qqq_6m_return' in indicators and 'vti_6m_return' in indicators:
            qqq_6m = indicators['qqq_6m_return']
            vti_6m = indicators['vti_6m_return']
            if qqq_6m > vti_6m + 0.02:
                explanation_parts.append(f"Growth momentum: QQQ +{qqq_6m:.1%} vs VTI +{vti_6m:.1%} (6M)")
            elif vti_6m > qqq_6m + 0.02:
                explanation_parts.append(f"Value momentum: VTI +{vti_6m:.1%} vs QQQ +{qqq_6m:.1%} (6M)")
        
        return ". ".join(explanation_parts)

    def analyze_historical_regimes(self, start_date: str = "2004-01-01", 
                                 end_date: str = "2024-12-31") -> List[RegimeDetection]:
        """
        Analyze historical regimes across a date range
        """
        print(f"\n🔍 ANALYZING HISTORICAL REGIMES: {start_date} to {end_date}")
        print("-" * 60)
        
        if self.historical_data is None:
            print("Loading historical data...")
            self.load_historical_data()
            
        if self.historical_data is None:
            print("❌ Could not load historical data")
            return []
        
        # Generate monthly regime detections
        start_dt = pd.to_datetime(start_date)
        end_dt = pd.to_datetime(end_date)
        
        # Create monthly date range
        date_range = pd.date_range(start=start_dt, end=end_dt, freq='M')
        
        regime_detections = []
        
        print(f"Analyzing {len(date_range)} monthly periods...")
        
        for i, date in enumerate(date_range):
            date_str = date.strftime('%Y-%m-%d')
            
            if i % 24 == 0:  # Print progress every 2 years
                print(f"   Analyzing {date.year}...")
            
            detection = self.detect_regime_at_date(date_str)
            regime_detections.append(detection)
        
        self.regime_history = regime_detections
        
        # Summarize results
        regime_counts = {}
        total_confidence = 0
        
        for detection in regime_detections:
            regime = detection.regime
            regime_counts[regime] = regime_counts.get(regime, 0) + 1
            total_confidence += detection.confidence
        
        print(f"\n✅ HISTORICAL REGIME ANALYSIS COMPLETE")
        print("-" * 40)
        
        for regime, count in regime_counts.items():
            percentage = count / len(regime_detections) * 100
            print(f"{regime.value.title():12}: {count:3d} periods ({percentage:4.1f}%)")
        
        avg_confidence = total_confidence / len(regime_detections)
        print(f"Average Confidence: {avg_confidence:.2f}")
        
        return regime_detections

    def identify_regime_periods(self) -> List[RegimePeriod]:
        """
        Identify distinct regime periods from historical detections
        """
        if not self.regime_history:
            print("❌ No regime history available. Run analyze_historical_regimes() first.")
            return []
        
        print(f"\n📊 IDENTIFYING REGIME PERIODS")
        print("-" * 30)
        
        periods = []
        current_regime = None
        current_start = None
        current_detections = []
        
        for detection in self.regime_history:
            detection_date = pd.to_datetime(detection.date)
            
            # Start of new regime or first detection
            if current_regime != detection.regime:
                # Save previous period if exists
                if current_regime is not None and current_detections:
                    period = self._create_regime_period(
                        current_regime, current_start, current_detections
                    )
                    if period:
                        periods.append(period)
                
                # Start new period
                current_regime = detection.regime
                current_start = detection_date
                current_detections = [detection]
            else:
                # Continue current regime
                current_detections.append(detection)
        
        # Handle final period
        if current_regime is not None and current_detections:
            period = self._create_regime_period(
                current_regime, current_start, current_detections
            )
            if period:
                periods.append(period)
        
        self.regime_periods = periods
        
        # Summary
        print(f"✅ Identified {len(periods)} distinct regime periods:")
        for period in periods:
            print(f"   {period.start_date[:7]} to {period.end_date[:7]}: "
                  f"{period.regime.value.title()} ({period.duration_months}M, "
                  f"{period.avg_confidence:.2f} confidence)")
        
        return periods

    def _create_regime_period(self, regime: MarketRegime, start_date: pd.Timestamp,
                            detections: List[RegimeDetection]) -> Optional[RegimePeriod]:
        """
        Create RegimePeriod from a list of detections
        """
        if not detections:
            return None
        
        end_date = pd.to_datetime(detections[-1].date)
        duration_months = len(detections)
        avg_confidence = np.mean([d.confidence for d in detections])
        
        # Extract performance data (simplified for now)
        performance_data = {}
        if detections[-1].indicators:
            indicators = detections[-1].indicators
            if 'qqq_6m_return' in indicators:
                performance_data['growth_return'] = indicators['qqq_6m_return']
            if 'vti_6m_return' in indicators:
                performance_data['value_return'] = indicators['vti_6m_return']  
            if 'bnd_6m_return' in indicators:
                performance_data['defensive_return'] = indicators['bnd_6m_return']
        
        # Key events (placeholder - could be enhanced with news/economic data)
        key_events = []
        if regime == MarketRegime.DEFENSIVE and duration_months > 12:
            key_events.append("Extended defensive period - potential crisis/recession")
        elif regime == MarketRegime.GROWTH and avg_confidence > 0.8:
            key_events.append("Strong growth regime - tech/innovation leadership")
        elif regime == MarketRegime.VALUE and duration_months > 24:
            key_events.append("Sustained value outperformance - mean reversion period")
        
        return RegimePeriod(
            start_date=start_date.strftime('%Y-%m-%d'),
            end_date=end_date.strftime('%Y-%m-%d'), 
            regime=regime,
            duration_months=duration_months,
            avg_confidence=avg_confidence,
            key_events=key_events,
            performance_data=performance_data
        )

    def get_current_regime(self) -> RegimeDetection:
        """
        Get the current market regime
        """
        current_date = datetime.now().strftime('%Y-%m-%d')
        return self.detect_regime_at_date(current_date)

    def display_regime_summary(self):
        """
        Display comprehensive summary of regime analysis
        """
        print(f"\n📊 REGIME DETECTION SYSTEM SUMMARY")
        print("=" * 60)
        
        if not self.regime_periods:
            print("❌ No regime periods identified. Run full analysis first.")
            return
        
        # Overall statistics
        total_periods = len(self.regime_periods)
        regime_stats = {}
        
        for period in self.regime_periods:
            regime = period.regime
            if regime not in regime_stats:
                regime_stats[regime] = {
                    'count': 0,
                    'total_months': 0,
                    'avg_confidence': 0,
                    'max_duration': 0
                }
            
            regime_stats[regime]['count'] += 1
            regime_stats[regime]['total_months'] += period.duration_months
            regime_stats[regime]['avg_confidence'] += period.avg_confidence
            regime_stats[regime]['max_duration'] = max(
                regime_stats[regime]['max_duration'], 
                period.duration_months
            )
        
        # Calculate averages
        for regime in regime_stats:
            count = regime_stats[regime]['count']
            regime_stats[regime]['avg_confidence'] /= count
            regime_stats[regime]['avg_duration'] = regime_stats[regime]['total_months'] / count
        
        print("REGIME STATISTICS:")
        print("-" * 30)
        for regime, stats in regime_stats.items():
            print(f"{regime.value.title():12}:")
            print(f"  Periods: {stats['count']}")
            print(f"  Avg Duration: {stats['avg_duration']:.1f} months") 
            print(f"  Max Duration: {stats['max_duration']} months")
            print(f"  Avg Confidence: {stats['avg_confidence']:.2f}")
            print()
        
        # Recent regime progression
        print("RECENT REGIME PROGRESSION (Last 5 periods):")
        print("-" * 45)
        recent_periods = self.regime_periods[-5:] if len(self.regime_periods) >= 5 else self.regime_periods
        
        for period in recent_periods:
            print(f"{period.start_date[:7]} - {period.end_date[:7]}: "
                  f"{period.regime.value.title():10} "
                  f"({period.duration_months:2d}M, {period.avg_confidence:.2f})")
        
        # Current regime
        if self.historical_data is not None:
            current = self.get_current_regime()
            print(f"\nCURRENT REGIME (as of today):")
            print(f"Regime: {current.regime.value.title()}")
            print(f"Confidence: {current.confidence:.2f}")
            print(f"Strength: {current.strength.value.title()}")
            print(f"Explanation: {current.explanation}")


def main():
    """
    Main function to demonstrate regime detection system
    """
    print("🚀 STARTING MARKET REGIME DETECTION SYSTEM")
    print("=" * 80)
    
    # Initialize system
    regime_detector = RegimeDetectionSystem()
    
    # Load historical data
    historical_data = regime_detector.load_historical_data()
    if historical_data is None:
        print("❌ Failed to load historical data. Cannot proceed.")
        return
    
    # Analyze historical regimes
    regime_history = regime_detector.analyze_historical_regimes()
    if not regime_history:
        print("❌ Failed to analyze historical regimes.")
        return
    
    # Identify distinct regime periods
    regime_periods = regime_detector.identify_regime_periods()
    
    # Display comprehensive summary
    regime_detector.display_regime_summary()
    
    print(f"\n🎉 REGIME DETECTION SYSTEM ANALYSIS COMPLETE")
    print(f"✅ Analyzed {len(regime_history)} monthly periods")
    print(f"✅ Identified {len(regime_periods)} distinct regime periods")
    print(f"✅ System ready for regime-aware allocation optimization")

if __name__ == "__main__":
    main()
