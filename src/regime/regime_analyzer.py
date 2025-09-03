"""
Regime-Aware Portfolio Analyzer

This module provides regime-aware analysis capabilities, including:
- Performance attribution by market regime
- Regime-specific strategy recommendations
- Portfolio optimization based on regime forecasts
"""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import Dict, List, Tuple, Optional
import logging

from .regime_detector import MarketRegimeDetector
from ..models.base import DatabaseManager

logger = logging.getLogger(__name__)

class RegimeAwareAnalyzer:
    """
    Provides regime-aware analysis for portfolio optimization and strategy selection
    """
    
    def __init__(self, db_manager: DatabaseManager = None):
        self.db_manager = db_manager or DatabaseManager()
        self.regime_detector = MarketRegimeDetector()
        
        # Regime-specific strategy adjustments
        self.regime_adjustments = {
            'bull_market': {
                'equity_bias': 0.05,      # Increase equity allocation by 5%
                'volatility_target': 0.12, # Lower vol target in bull markets
                'rebalancing_frequency': 'quarterly',
                'description': 'Favor equities with lower volatility targeting'
            },
            'bear_market': {
                'equity_bias': -0.10,     # Decrease equity allocation by 10%
                'volatility_target': 0.20, # Higher vol tolerance in bear markets
                'rebalancing_frequency': 'monthly',
                'description': 'Defensive posture with frequent rebalancing'
            },
            'volatile_bull': {
                'equity_bias': 0.02,      # Slight equity increase
                'volatility_target': 0.18, # Higher vol tolerance
                'rebalancing_frequency': 'monthly',
                'description': 'Opportunistic with active risk management'
            },
            'sideways_market': {
                'equity_bias': 0.0,       # Neutral allocation
                'volatility_target': 0.15, # Standard vol target
                'rebalancing_frequency': 'quarterly',
                'description': 'Balanced approach with standard parameters'
            },
            'crisis_mode': {
                'equity_bias': -0.15,     # Significant equity reduction
                'volatility_target': 0.25, # High vol tolerance
                'rebalancing_frequency': 'weekly',
                'description': 'Capital preservation with frequent adjustments'
            }
        }
    
    def analyze_performance_by_regime(self, portfolio_returns: pd.Series,
                                    start_date: datetime = None,
                                    end_date: datetime = None) -> Dict:
        """
        Analyze portfolio performance across different market regimes
        
        Args:
            portfolio_returns: Time series of portfolio returns
            start_date: Start date for analysis
            end_date: End date for analysis
            
        Returns:
            Dict with performance attribution by regime
        """
        try:
            # Get price data for regime detection
            price_data = self._get_price_data(start_date, end_date)
            
            if price_data.empty:
                logger.warning("No price data available for regime analysis")
                return {}
            
            # Detect historical regimes
            historical_regimes = self.regime_detector.detect_historical_regimes(
                price_data, window_days=126, step_days=21  # ~6 month windows
            )
            
            if historical_regimes.empty:
                logger.warning("No historical regimes detected")
                return {}
            
            # Align returns with regime classifications
            regime_performance = {}
            
            for regime_type in self.regime_detector.regime_types.keys():
                regime_dates = historical_regimes[
                    historical_regimes['regime_type'] == regime_type
                ].index
                
                if len(regime_dates) > 0:
                    # Get returns during this regime
                    regime_returns = []
                    for date in regime_dates:
                        # Get returns in 21-day window around regime date
                        window_start = date - timedelta(days=10)
                        window_end = date + timedelta(days=10)
                        
                        window_returns = portfolio_returns[
                            (portfolio_returns.index >= window_start) & 
                            (portfolio_returns.index <= window_end)
                        ]
                        regime_returns.extend(window_returns.tolist())
                    
                    if regime_returns:
                        returns_series = pd.Series(regime_returns)
                        
                        regime_performance[regime_type] = {
                            'total_return': returns_series.sum(),
                            'annualized_return': returns_series.mean() * 252,
                            'volatility': returns_series.std() * np.sqrt(252),
                            'sharpe_ratio': self._calculate_sharpe_ratio(returns_series),
                            'max_drawdown': self._calculate_max_drawdown(returns_series),
                            'positive_periods': (returns_series > 0).sum(),
                            'total_periods': len(returns_series),
                            'regime_name': self.regime_detector.regime_types[regime_type]['name']
                        }
            
            # Calculate regime-adjusted metrics
            analysis_result = {
                'regime_performance': regime_performance,
                'regime_summary': self._generate_regime_summary(regime_performance),
                'current_regime_forecast': self._get_current_regime_forecast(price_data),
                'strategy_recommendations': self._generate_strategy_recommendations(
                    regime_performance, price_data
                )
            }
            
            logger.info(f"Completed regime-aware performance analysis for {len(regime_performance)} regimes")
            return analysis_result
            
        except Exception as e:
            logger.error(f"Error in regime-aware performance analysis: {str(e)}")
            return {}
    
    def get_regime_aware_recommendations(self, current_portfolio: Dict,
                                       risk_tolerance: str = 'balanced') -> Dict:
        """
        Generate regime-aware portfolio recommendations
        
        Args:
            current_portfolio: Current portfolio allocation
            risk_tolerance: Risk tolerance level
            
        Returns:
            Dict with regime-aware recommendations
        """
        try:
            # Get current regime
            price_data = self._get_price_data()
            current_regime = self.regime_detector.detect_current_regime(price_data)
            
            regime_type = current_regime.get('regime_type', 'sideways_market')
            adjustments = self.regime_adjustments.get(regime_type, {})
            
            # Generate recommendations based on current regime
            recommendations = {
                'current_regime': current_regime,
                'regime_adjustments': adjustments,
                'recommended_changes': self._calculate_recommended_changes(
                    current_portfolio, adjustments, risk_tolerance
                ),
                'rebalancing_guidance': self._get_rebalancing_guidance(regime_type),
                'risk_management_advice': self._get_risk_management_advice(regime_type),
                'monitoring_suggestions': self._get_monitoring_suggestions(regime_type)
            }
            
            logger.info(f"Generated regime-aware recommendations for {regime_type} regime")
            return recommendations
            
        except Exception as e:
            logger.error(f"Error generating regime-aware recommendations: {str(e)}")
            return {}
    
    def _get_price_data(self, start_date: datetime = None, 
                       end_date: datetime = None) -> pd.DataFrame:
        """Get price data from database"""
        try:
            if not start_date:
                start_date = datetime.now() - timedelta(days=1000)  # ~3 years default
            if not end_date:
                end_date = datetime.now()
                
            query = """
            SELECT date, symbol, adj_close
            FROM daily_prices 
            WHERE date BETWEEN %s AND %s
            AND symbol IN ('VTI', 'VTIAX', 'BND', 'VNQ', 'GLD', 'VWO', 'QQQ')
            ORDER BY date, symbol
            """
            
            results = self.db_manager.execute_query(query, (start_date, end_date))
            
            if results:
                df = pd.DataFrame(results, columns=['date', 'symbol', 'price'])
                pivot_df = df.pivot(index='date', columns='symbol', values='price')
                pivot_df.index = pd.to_datetime(pivot_df.index)
                # Convert decimal to float and forward fill
                pivot_df = pivot_df.astype(float)
                return pivot_df.ffill().dropna()
            else:
                return pd.DataFrame()
                
        except Exception as e:
            logger.error(f"Error getting price data: {str(e)}")
            return pd.DataFrame()
    
    def _calculate_sharpe_ratio(self, returns: pd.Series, risk_free_rate: float = 0.02) -> float:
        """Calculate Sharpe ratio for returns series"""
        try:
            excess_returns = returns.mean() * 252 - risk_free_rate
            volatility = returns.std() * np.sqrt(252)
            return excess_returns / volatility if volatility > 0 else 0
        except:
            return 0
    
    def _calculate_max_drawdown(self, returns: pd.Series) -> float:
        """Calculate maximum drawdown for returns series"""
        try:
            cumulative = (1 + returns).cumprod()
            rolling_max = cumulative.expanding().max()
            drawdown = (cumulative - rolling_max) / rolling_max
            return drawdown.min()
        except:
            return 0
    
    def _generate_regime_summary(self, regime_performance: Dict) -> Dict:
        """Generate summary statistics across regimes"""
        try:
            if not regime_performance:
                return {}
                
            summary = {
                'best_regime': '',
                'worst_regime': '',
                'most_volatile_regime': '',
                'best_sharpe_regime': '',
                'regime_consistency': 0
            }
            
            # Find best/worst performing regimes
            returns_by_regime = {k: v['annualized_return'] for k, v in regime_performance.items()}
            if returns_by_regime:
                summary['best_regime'] = max(returns_by_regime, key=returns_by_regime.get)
                summary['worst_regime'] = min(returns_by_regime, key=returns_by_regime.get)
            
            # Find most volatile regime
            vol_by_regime = {k: v['volatility'] for k, v in regime_performance.items()}
            if vol_by_regime:
                summary['most_volatile_regime'] = max(vol_by_regime, key=vol_by_regime.get)
            
            # Find best Sharpe regime
            sharpe_by_regime = {k: v['sharpe_ratio'] for k, v in regime_performance.items()}
            if sharpe_by_regime:
                summary['best_sharpe_regime'] = max(sharpe_by_regime, key=sharpe_by_regime.get)
            
            # Calculate regime consistency (% positive returns across regimes)
            positive_regimes = sum(1 for v in regime_performance.values() 
                                 if v['annualized_return'] > 0)
            summary['regime_consistency'] = positive_regimes / len(regime_performance) if regime_performance else 0
            
            return summary
            
        except Exception as e:
            logger.warning(f"Error generating regime summary: {str(e)}")
            return {}
    
    def _get_current_regime_forecast(self, price_data: pd.DataFrame) -> Dict:
        """Get current regime and confidence forecast"""
        try:
            current_regime = self.regime_detector.detect_current_regime(price_data)
            
            # Add forecast confidence and duration
            forecast = {
                'regime_type': current_regime.get('regime_type', 'sideways_market'),
                'regime_name': current_regime.get('regime_name', 'Sideways Market'),
                'confidence': current_regime.get('confidence_score', 0.5),
                'expected_duration': self._estimate_regime_duration(
                    current_regime.get('regime_type', 'sideways_market')
                ),
                'key_risks': self._identify_regime_risks(
                    current_regime.get('regime_type', 'sideways_market')
                ),
                'transition_probability': self._calculate_transition_probability(price_data)
            }
            
            return forecast
            
        except Exception as e:
            logger.warning(f"Error getting current regime forecast: {str(e)}")
            return {}
    
    def _generate_strategy_recommendations(self, regime_performance: Dict, 
                                         price_data: pd.DataFrame) -> List[Dict]:
        """Generate specific strategy recommendations based on regime analysis"""
        recommendations = []
        
        try:
            current_regime = self.regime_detector.detect_current_regime(price_data)
            regime_type = current_regime.get('regime_type', 'sideways_market')
            
            # Asset allocation recommendations
            if regime_type == 'bull_market':
                recommendations.append({
                    'category': 'Asset Allocation',
                    'recommendation': 'Increase equity allocation by 5-10%',
                    'rationale': 'Bull markets favor risk assets with lower volatility',
                    'priority': 'high'
                })
            elif regime_type == 'bear_market':
                recommendations.append({
                    'category': 'Asset Allocation', 
                    'recommendation': 'Reduce equity allocation by 10-15%',
                    'rationale': 'Bear markets require defensive positioning',
                    'priority': 'high'
                })
            elif regime_type == 'crisis_mode':
                recommendations.append({
                    'category': 'Risk Management',
                    'recommendation': 'Implement capital preservation mode',
                    'rationale': 'Crisis conditions require immediate risk reduction',
                    'priority': 'critical'
                })
            
            # Rebalancing recommendations
            adjustments = self.regime_adjustments.get(regime_type, {})
            rebal_freq = adjustments.get('rebalancing_frequency', 'quarterly')
            recommendations.append({
                'category': 'Rebalancing',
                'recommendation': f'Switch to {rebal_freq} rebalancing',
                'rationale': f'Optimal frequency for {regime_type} conditions',
                'priority': 'medium'
            })
            
            # Volatility targeting
            vol_target = adjustments.get('volatility_target', 0.15)
            recommendations.append({
                'category': 'Risk Control',
                'recommendation': f'Target {vol_target:.1%} portfolio volatility',
                'rationale': f'Appropriate risk level for current regime',
                'priority': 'medium'
            })
            
            return recommendations
            
        except Exception as e:
            logger.warning(f"Error generating strategy recommendations: {str(e)}")
            return []
    
    def _calculate_recommended_changes(self, current_portfolio: Dict, 
                                     adjustments: Dict, risk_tolerance: str) -> Dict:
        """Calculate specific portfolio changes based on regime adjustments"""
        try:
            changes = {}
            equity_bias = adjustments.get('equity_bias', 0)
            
            # Apply equity bias adjustment
            if equity_bias != 0:
                # Identify equity assets (VTI, VTIAX, VWO, QQQ)
                equity_assets = ['VTI', 'VTIAX', 'VWO', 'QQQ']
                bond_assets = ['BND']
                other_assets = ['VNQ', 'GLD']
                
                for asset in equity_assets:
                    if asset in current_portfolio:
                        current_weight = current_portfolio[asset]
                        adjustment = equity_bias * current_weight  # Proportional adjustment
                        changes[asset] = {
                            'current_weight': current_weight,
                            'recommended_weight': current_weight + adjustment,
                            'change': adjustment
                        }
                
                # Offset with bond allocation changes
                for asset in bond_assets:
                    if asset in current_portfolio:
                        current_weight = current_portfolio[asset]
                        adjustment = -equity_bias * 0.5  # Reduce bonds to offset equity increase
                        changes[asset] = {
                            'current_weight': current_weight,
                            'recommended_weight': max(0, current_weight + adjustment),
                            'change': adjustment
                        }
            
            return changes
            
        except Exception as e:
            logger.warning(f"Error calculating recommended changes: {str(e)}")
            return {}
    
    def _get_rebalancing_guidance(self, regime_type: str) -> Dict:
        """Get rebalancing guidance for the current regime"""
        adjustments = self.regime_adjustments.get(regime_type, {})
        
        return {
            'frequency': adjustments.get('rebalancing_frequency', 'quarterly'),
            'threshold': self._get_rebalancing_threshold(regime_type),
            'priority_assets': self._get_priority_assets(regime_type),
            'guidance': adjustments.get('description', 'Standard rebalancing approach')
        }
    
    def _get_risk_management_advice(self, regime_type: str) -> List[str]:
        """Get risk management advice for the current regime"""
        advice = []
        
        if regime_type == 'bear_market':
            advice.extend([
                'Consider reducing position sizes',
                'Implement stop-loss levels for major holdings',
                'Increase cash allocation for opportunities'
            ])
        elif regime_type == 'crisis_mode':
            advice.extend([
                'Focus on capital preservation',
                'Avoid leverage and concentrated positions',
                'Monitor portfolio daily during crisis periods'
            ])
        elif regime_type == 'volatile_bull':
            advice.extend([
                'Use volatility spikes as buying opportunities',
                'Maintain disciplined rebalancing',
                'Consider taking profits on overperforming assets'
            ])
        else:
            advice.append('Maintain standard risk management practices')
            
        return advice
    
    def _get_monitoring_suggestions(self, regime_type: str) -> List[str]:
        """Get monitoring suggestions for the current regime"""
        suggestions = [
            'Monitor regime indicators weekly',
            'Track portfolio performance vs regime expectations'
        ]
        
        if regime_type in ['crisis_mode', 'bear_market']:
            suggestions.extend([
                'Daily portfolio monitoring recommended',
                'Watch for regime transition signals'
            ])
        elif regime_type == 'bull_market':
            suggestions.extend([
                'Monthly regime assessment sufficient',
                'Watch for overheating indicators'
            ])
            
        return suggestions
    
    def _estimate_regime_duration(self, regime_type: str) -> str:
        """Estimate typical duration for regime type"""
        durations = {
            'bull_market': '12-36 months',
            'bear_market': '6-18 months', 
            'volatile_bull': '3-12 months',
            'sideways_market': '6-24 months',
            'crisis_mode': '1-6 months'
        }
        return durations.get(regime_type, '6-12 months')
    
    def _identify_regime_risks(self, regime_type: str) -> List[str]:
        """Identify key risks for the current regime"""
        risks = {
            'bull_market': ['Overvaluation', 'Complacency', 'Sudden reversals'],
            'bear_market': ['Continued decline', 'Liquidity issues', 'Forced selling'],
            'volatile_bull': ['Whipsaws', 'False signals', 'Increased correlation'],
            'sideways_market': ['Range breaks', 'Low returns', 'Opportunity cost'],
            'crisis_mode': ['System risk', 'Liquidity crisis', 'Extreme volatility']
        }
        return risks.get(regime_type, ['Regime transition risk'])
    
    def _calculate_transition_probability(self, price_data: pd.DataFrame) -> Dict:
        """Calculate probability of regime transitions"""
        try:
            # Simplified transition probability based on indicators
            current_regime = self.regime_detector.detect_current_regime(price_data)
            confidence = current_regime.get('confidence_score', 0.5)
            
            # Higher confidence = lower transition probability
            transition_prob = 1 - confidence
            
            return {
                'transition_probability': transition_prob,
                'stability': confidence,
                'next_likely_regime': self._get_next_likely_regime(
                    current_regime.get('regime_type', 'sideways_market')
                )
            }
            
        except Exception as e:
            logger.warning(f"Error calculating transition probability: {str(e)}")
            return {'transition_probability': 0.3, 'stability': 0.7}
    
    def _get_next_likely_regime(self, current_regime: str) -> str:
        """Get most likely next regime based on transitions"""
        transitions = {
            'bull_market': 'volatile_bull',
            'bear_market': 'sideways_market',
            'volatile_bull': 'sideways_market', 
            'sideways_market': 'bull_market',
            'crisis_mode': 'bear_market'
        }
        return transitions.get(current_regime, 'sideways_market')
    
    def _get_rebalancing_threshold(self, regime_type: str) -> float:
        """Get rebalancing threshold for regime"""
        thresholds = {
            'bull_market': 0.05,      # 5% threshold
            'bear_market': 0.03,      # 3% threshold - more sensitive
            'volatile_bull': 0.03,    # 3% threshold
            'sideways_market': 0.05,  # 5% threshold
            'crisis_mode': 0.02       # 2% threshold - very sensitive
        }
        return thresholds.get(regime_type, 0.05)
    
    def _get_priority_assets(self, regime_type: str) -> List[str]:
        """Get priority assets to monitor for rebalancing"""
        if regime_type == 'bear_market':
            return ['BND', 'GLD']  # Focus on defensive assets
        elif regime_type == 'bull_market':
            return ['VTI', 'QQQ']  # Focus on growth assets
        elif regime_type == 'crisis_mode':
            return ['BND', 'GLD', 'VTI']  # Monitor defensive and liquid assets
        else:
            return ['VTI', 'BND']  # Standard monitoring
