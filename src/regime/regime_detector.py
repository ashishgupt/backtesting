"""
Market Regime Detection Engine

This module provides the core regime detection functionality, identifying
different market environments based on multiple indicators and historical patterns.
"""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import Dict, List, Tuple, Optional
import logging

# sklearn imports are optional for now
try:
    from sklearn.cluster import KMeans
    from sklearn.preprocessing import StandardScaler
    SKLEARN_AVAILABLE = True
except ImportError:
    SKLEARN_AVAILABLE = False

from .regime_indicators import RegimeIndicatorCalculator

logger = logging.getLogger(__name__)

class MarketRegimeDetector:
    """
    Detects market regimes using multiple indicators and classification methods
    """
    
    def __init__(self):
        self.indicator_calculator = RegimeIndicatorCalculator()
        self.regime_history = {}
        self.classification_model = None
        
        # Define regime types and characteristics
        self.regime_types = {
            'bull_market': {
                'name': 'Bull Market',
                'description': 'Rising markets with low volatility',
                'characteristics': ['positive_momentum', 'low_volatility', 'risk_on']
            },
            'bear_market': {
                'name': 'Bear Market', 
                'description': 'Declining markets with high volatility',
                'characteristics': ['negative_momentum', 'high_volatility', 'risk_off']
            },
            'volatile_bull': {
                'name': 'Volatile Bull',
                'description': 'Rising markets with high volatility',
                'characteristics': ['positive_momentum', 'high_volatility', 'mixed_risk']
            },
            'sideways_market': {
                'name': 'Sideways Market',
                'description': 'Range-bound markets with moderate volatility',
                'characteristics': ['low_momentum', 'normal_volatility', 'neutral_risk']
            },
            'crisis_mode': {
                'name': 'Crisis Mode',
                'description': 'Extreme stress conditions',
                'characteristics': ['negative_momentum', 'extreme_volatility', 'flight_to_quality']
            }
        }
    
    def detect_current_regime(self, price_data: pd.DataFrame,
                            lookback_days: int = 252) -> Dict:
        """
        Detect the current market regime based on recent data
        
        Args:
            price_data: DataFrame with asset price data
            lookback_days: Number of days to look back for analysis
            
        Returns:
            Dict with regime detection results
        """
        try:
            # Calculate indicators using all available data (no date filtering)
            # The API already provides appropriate data with sufficient buffer
            indicators = self.indicator_calculator.calculate_all_indicators(price_data)
            
            if not indicators:
                return self._get_default_regime()
            
            # Classify regime based on indicators
            regime_classification = self._classify_regime(indicators)
            
            # Add confidence and supporting evidence
            regime_result = {
                'regime_type': regime_classification['regime_type'],
                'regime_name': self.regime_types[regime_classification['regime_type']]['name'],
                'confidence_score': regime_classification['confidence'],
                'key_indicators': indicators,
                'supporting_factors': regime_classification['factors'],
                'regime_description': self.regime_types[regime_classification['regime_type']]['description'],
                'detection_date': price_data.index[-1],
                'lookback_period': lookback_days
            }
            
            logger.info(f"Detected regime: {regime_result['regime_name']} "
                       f"(confidence: {regime_result['confidence_score']:.2f})")
            
            return regime_result
            
        except Exception as e:
            logger.error(f"Error detecting current regime: {str(e)}")
            return self._get_default_regime()
    
    def detect_historical_regimes(self, price_data: pd.DataFrame,
                                window_days: int = 252,
                                step_days: int = 21) -> pd.DataFrame:
        """
        Detect market regimes over historical periods
        
        Args:
            price_data: DataFrame with asset price data
            window_days: Size of rolling window for regime detection
            step_days: Step size between regime detections
            
        Returns:
            DataFrame with historical regime classifications
        """
        try:
            regimes = []
            start_idx = window_days
            
            while start_idx < len(price_data):
                end_date = price_data.index[start_idx]
                start_date = end_date - timedelta(days=window_days)
                
                # Get data window
                window_data = price_data[
                    (price_data.index >= start_date) & (price_data.index <= end_date)
                ]
                
                if len(window_data) >= window_days * 0.7:  # At least 70% data coverage
                    regime_result = self.detect_current_regime(window_data, window_days)
                    
                    regimes.append({
                        'date': end_date,
                        'regime_type': regime_result['regime_type'],
                        'regime_name': regime_result['regime_name'],
                        'confidence': regime_result['confidence_score'],
                        'momentum_3m': regime_result['key_indicators'].get('momentum_3m', 0),
                        'volatility_percentile': regime_result['key_indicators'].get('volatility_percentile', 0.5),
                        'risk_regime': regime_result['key_indicators'].get('risk_regime', 'neutral')
                    })
                
                start_idx += step_days
            
            regime_df = pd.DataFrame(regimes)
            if not regime_df.empty:
                regime_df.set_index('date', inplace=True)
                
            logger.info(f"Detected {len(regimes)} historical regime periods")
            return regime_df
            
        except Exception as e:
            logger.error(f"Error detecting historical regimes: {str(e)}")
            return pd.DataFrame()
    
    def _classify_regime(self, indicators: Dict) -> Dict:
        """
        Classify market regime based on calculated indicators
        
        Args:
            indicators: Dict of regime indicators
            
        Returns:
            Dict with regime classification and confidence
        """
        try:
            # Score each regime type based on indicators
            regime_scores = {}
            
            for regime_type in self.regime_types.keys():
                score = self._calculate_regime_score(regime_type, indicators)
                regime_scores[regime_type] = score
            
            # Find best matching regime
            best_regime = max(regime_scores, key=regime_scores.get)
            confidence = regime_scores[best_regime]
            
            # Get supporting factors
            supporting_factors = self._get_supporting_factors(best_regime, indicators)
            
            return {
                'regime_type': best_regime,
                'confidence': min(max(confidence, 0.0), 1.0),  # Clamp to [0,1]
                'factors': supporting_factors,
                'all_scores': regime_scores
            }
            
        except Exception as e:
            logger.error(f"Error classifying regime: {str(e)}")
            return {
                'regime_type': 'sideways_market',
                'confidence': 0.5,
                'factors': ['default_classification']
            }
    
    def _calculate_regime_score(self, regime_type: str, indicators: Dict) -> float:
        """Calculate how well indicators match a specific regime type"""
        try:
            score = 0.0
            factor_count = 0
            momentum_3m = indicators.get('momentum_3m', 0)
            
            # Bull Market scoring
            if regime_type == 'bull_market':
                # Strong positive momentum (>10% annualized)
                if momentum_3m > 0.10:
                    score += 2.0
                    factor_count += 1
                elif momentum_3m > 0.05:  # Moderate positive momentum
                    score += 1.0
                    factor_count += 1
                    
                if indicators.get('volatility_regime') == 'low':
                    score += 1.5
                    factor_count += 1
                    
                if indicators.get('risk_regime') == 'risk_on':
                    score += 1.0  
                    factor_count += 1
                    
                if indicators.get('price_vs_ma200', 0) > 0:
                    score += 0.5
                    factor_count += 1
                
                # Exclude if negative momentum
                if momentum_3m < -0.02:
                    score = 0
            
            # Bear Market scoring
            elif regime_type == 'bear_market':
                # Must have negative momentum to be bear market
                if momentum_3m < -0.05:  # <-5% annualized
                    score += 2.0
                    factor_count += 1
                elif momentum_3m < -0.02:  # Slightly negative
                    score += 1.0
                    factor_count += 1
                    
                if indicators.get('volatility_regime') == 'high':
                    score += 1.0
                    factor_count += 1
                    
                if indicators.get('risk_regime') == 'risk_off':
                    score += 1.0
                    factor_count += 1
                    
                if indicators.get('price_vs_ma200', 0) < -0.1:
                    score += 0.5
                    factor_count += 1
                
                # Exclude if positive momentum (key fix!)
                if momentum_3m > 0.02:
                    score = 0
            
            # Volatile Bull scoring - EXPANDED CRITERIA
            elif regime_type == 'volatile_bull':
                # Positive momentum with high volatility
                if momentum_3m > 0.02:  # Any positive momentum
                    if momentum_3m > 0.15:  # Very strong momentum
                        score += 1.5
                    else:  # Moderate positive momentum
                        score += 2.0
                    factor_count += 1
                    
                if indicators.get('volatility_regime') == 'high':
                    score += 2.0  # High weight for volatility
                    factor_count += 1
                    
                # High correlation suggests market stress despite positive momentum
                if indicators.get('correlation_regime') == 'high':
                    score += 1.0
                    factor_count += 1
                
                # Risk-on sentiment supports volatile bull
                if indicators.get('risk_regime') == 'risk_on':
                    score += 0.5
                    factor_count += 1
                
                # Exclude if negative momentum
                if momentum_3m < -0.02:
                    score = 0
            
            # Sideways Market scoring  
            elif regime_type == 'sideways_market':
                momentum = abs(momentum_3m)
                if momentum < 0.03:  # Very low absolute momentum
                    score += 2.0
                    factor_count += 1
                elif momentum < 0.05:  # Low absolute momentum
                    score += 1.0
                    factor_count += 1
                    
                if indicators.get('volatility_regime') == 'normal':
                    score += 1.5
                    factor_count += 1
                    
                if indicators.get('risk_regime') == 'neutral':
                    score += 1.0
                    factor_count += 1
                
                # Exclude if strong momentum in either direction
                if abs(momentum_3m) > 0.08:
                    score = 0
            
            # Crisis Mode scoring
            elif regime_type == 'crisis_mode':
                if momentum_3m < -0.15:  # Very negative momentum
                    score += 2.0
                    factor_count += 1
                elif momentum_3m < -0.10:  # Strong negative momentum
                    score += 1.0
                    factor_count += 1
                    
                if indicators.get('volatility_percentile', 0.5) > 0.9:
                    score += 2.0
                    factor_count += 1
                elif indicators.get('volatility_percentile', 0.5) > 0.8:
                    score += 1.0
                    factor_count += 1
                    
                if indicators.get('average_correlation', 0.3) > 0.7:
                    score += 1.5
                    factor_count += 1
                
                # Exclude if positive momentum
                if momentum_3m > 0.02:
                    score = 0
            
            # Normalize score with improved weighting
            if factor_count > 0:
                normalized_score = score / (factor_count * 2.0)  # Normalize to max possible score
                return min(max(normalized_score, 0.0), 1.0)  # Clamp to [0,1]
            else:
                return 0.1  # Default low score
                
        except Exception as e:
            logger.warning(f"Error calculating regime score for {regime_type}: {str(e)}")
            return 0.1
    
    def _get_supporting_factors(self, regime_type: str, indicators: Dict) -> List[str]:
        """Get list of supporting factors for the classified regime"""
        factors = []
        
        try:
            if regime_type == 'bull_market':
                if indicators.get('momentum_3m', 0) > 0.05:
                    factors.append('Strong positive momentum')
                if indicators.get('volatility_regime') == 'low':
                    factors.append('Low volatility environment')
                if indicators.get('risk_regime') == 'risk_on':
                    factors.append('Risk-on sentiment')
                    
            elif regime_type == 'bear_market':
                if indicators.get('momentum_3m', 0) < -0.05:
                    factors.append('Negative momentum trend')
                if indicators.get('volatility_regime') == 'high':
                    factors.append('High volatility environment')
                if indicators.get('risk_regime') == 'risk_off':
                    factors.append('Risk-off sentiment')
                    
            elif regime_type == 'crisis_mode':
                if indicators.get('volatility_percentile', 0.5) > 0.9:
                    factors.append('Extreme volatility levels')
                if indicators.get('average_correlation', 0.3) > 0.7:
                    factors.append('High asset correlation')
                if indicators.get('momentum_3m', 0) < -0.15:
                    factors.append('Severe negative momentum')
            
            # Add general factors
            vol_regime = indicators.get('volatility_regime', 'normal')
            factors.append(f'Volatility regime: {vol_regime}')
            
            risk_regime = indicators.get('risk_regime', 'neutral')  
            factors.append(f'Risk sentiment: {risk_regime}')
            
        except Exception as e:
            logger.warning(f"Error getting supporting factors: {str(e)}")
            factors.append('Limited supporting evidence available')
            
        return factors if factors else ['Regime classification based on available indicators']
    
    def _get_default_regime(self) -> Dict:
        """Return default regime when detection fails"""
        return {
            'regime_type': 'sideways_market',
            'regime_name': 'Sideways Market',
            'confidence_score': 0.5,
            'key_indicators': {},
            'supporting_factors': ['Default classification - insufficient data'],
            'regime_description': 'Range-bound markets with moderate volatility',
            'detection_date': datetime.now(),
            'lookback_period': 252
        }
    
    def get_regime_transitions(self, historical_regimes: pd.DataFrame) -> List[Dict]:
        """
        Identify regime transition points in historical data
        
        Args:
            historical_regimes: DataFrame from detect_historical_regimes
            
        Returns:
            List of regime transition events
        """
        try:
            transitions = []
            
            if len(historical_regimes) < 2:
                return transitions
            
            prev_regime = historical_regimes['regime_type'].iloc[0]
            
            for i in range(1, len(historical_regimes)):
                current_regime = historical_regimes['regime_type'].iloc[i]
                
                if current_regime != prev_regime:
                    transition = {
                        'date': historical_regimes.index[i],
                        'from_regime': prev_regime,
                        'to_regime': current_regime,
                        'confidence': historical_regimes['confidence'].iloc[i],
                        'duration_days': (historical_regimes.index[i] - 
                                        historical_regimes.index[i-1]).days
                    }
                    transitions.append(transition)
                    prev_regime = current_regime
            
            logger.info(f"Identified {len(transitions)} regime transitions")
            return transitions
            
        except Exception as e:
            logger.error(f"Error identifying regime transitions: {str(e)}")
            return []
