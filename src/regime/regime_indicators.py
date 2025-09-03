"""
Market Regime Indicator Calculator

This module calculates various indicators used to identify market regimes:
- Value/Growth spread indicators
- Yield curve indicators  
- Volatility regime indicators (VIX percentiles)
- Market momentum indicators
- Inflation/deflation indicators
"""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import Dict, List, Tuple, Optional
import logging

logger = logging.getLogger(__name__)

class RegimeIndicatorCalculator:
    """
    Calculates various market regime indicators from historical data
    """
    
    def __init__(self):
        self.indicators = {}
        self.lookback_periods = {
            'short_term': 63,   # ~3 months
            'medium_term': 252, # ~1 year
            'long_term': 504    # ~2 years
        }
    
    def calculate_all_indicators(self, price_data: pd.DataFrame, 
                               start_date: datetime = None,
                               end_date: datetime = None) -> Dict:
        """
        Calculate all regime indicators for the given period
        
        Args:
            price_data: DataFrame with asset price data
            start_date: Start date for analysis
            end_date: End date for analysis
            
        Returns:
            Dict containing all calculated indicators
        """
        try:
            # Filter data by date range if provided
            if start_date and end_date:
                mask = (price_data.index >= start_date) & (price_data.index <= end_date)
                data = price_data[mask].copy()
            else:
                data = price_data.copy()
                
            indicators = {}
            
            # Calculate momentum indicators
            indicators.update(self._calculate_momentum_indicators(data))
            
            # Calculate volatility regime indicators  
            indicators.update(self._calculate_volatility_indicators(data))
            
            # Calculate value/growth spread indicators
            indicators.update(self._calculate_value_growth_spread(data))
            
            # Calculate market environment indicators
            indicators.update(self._calculate_market_environment(data))
            
            # Calculate correlation regime indicators
            indicators.update(self._calculate_correlation_regime(data))
            
            logger.info(f"Calculated {len(indicators)} regime indicators")
            return indicators
            
        except Exception as e:
            logger.error(f"Error calculating regime indicators: {str(e)}")
            return {}
    
    def _calculate_momentum_indicators(self, data: pd.DataFrame) -> Dict:
        """Calculate market momentum indicators"""
        indicators = {}
        
        try:
            # Assume VTI represents broad market
            if 'VTI' in data.columns:
                vti_returns = data['VTI'].pct_change().dropna()
                
                # Short-term momentum (3-month)
                short_momentum = vti_returns.rolling(63).mean() * 252
                indicators['momentum_3m'] = short_momentum.iloc[-1] if not short_momentum.empty else 0
                
                # Medium-term momentum (12-month)
                med_momentum = vti_returns.rolling(252).mean() * 252  
                indicators['momentum_12m'] = med_momentum.iloc[-1] if not med_momentum.empty else 0
                
                # Price relative to moving averages
                current_price = data['VTI'].iloc[-1]
                ma_200 = data['VTI'].rolling(200).mean().iloc[-1]
                ma_50 = data['VTI'].rolling(50).mean().iloc[-1]
                
                indicators['price_vs_ma200'] = (current_price / ma_200 - 1) if ma_200 > 0 else 0
                indicators['price_vs_ma50'] = (current_price / ma_50 - 1) if ma_50 > 0 else 0
                
        except Exception as e:
            logger.warning(f"Error calculating momentum indicators: {str(e)}")
            
        return indicators
    
    def _calculate_volatility_indicators(self, data: pd.DataFrame) -> Dict:
        """Calculate volatility regime indicators"""
        indicators = {}
        
        try:
            if 'VTI' in data.columns:
                returns = data['VTI'].pct_change().dropna()
                
                # Current volatility (annualized)
                current_vol = returns.rolling(21).std().iloc[-1] * np.sqrt(252)
                indicators['volatility_current'] = current_vol if not pd.isna(current_vol) else 0.15
                
                # Volatility percentile (relative to 2-year history)
                historical_vol = returns.rolling(21).std() * np.sqrt(252)
                vol_percentile = (historical_vol.rank(pct=True).iloc[-1]) if len(historical_vol) > 0 else 0.5
                indicators['volatility_percentile'] = vol_percentile
                
                # Volatility regime classification
                if vol_percentile < 0.25:
                    indicators['volatility_regime'] = 'low'
                elif vol_percentile > 0.75:
                    indicators['volatility_regime'] = 'high'
                else:
                    indicators['volatility_regime'] = 'normal'
                    
                # VIX-like calculation (simplified)
                # Use 30-day rolling volatility as proxy
                vix_proxy = returns.rolling(30).std() * np.sqrt(252) * 100
                indicators['vix_proxy'] = vix_proxy.iloc[-1] if not vix_proxy.empty else 15.0
                
        except Exception as e:
            logger.warning(f"Error calculating volatility indicators: {str(e)}")
            
        return indicators
    
    def _calculate_value_growth_spread(self, data: pd.DataFrame) -> Dict:
        """Calculate value/growth spread indicators"""
        indicators = {}
        
        try:
            # We don't have specific value/growth ETFs in our universe
            # Use VTI (broad market) relative performance as proxy
            if 'VTI' in data.columns and 'QQQ' in data.columns:
                # QQQ is growth-heavy, use relative performance
                vti_returns = data['VTI'].pct_change(21).dropna()  # 1-month
                qqq_returns = data['QQQ'].pct_change(21).dropna()  # 1-month
                
                if len(vti_returns) > 0 and len(qqq_returns) > 0:
                    # Value vs Growth spread (simplified)
                    value_growth_spread = vti_returns.iloc[-1] - qqq_returns.iloc[-1]
                    indicators['value_growth_spread'] = value_growth_spread
                    
                    # Historical percentile of spread
                    spread_series = vti_returns - qqq_returns
                    spread_percentile = spread_series.rank(pct=True).iloc[-1]
                    indicators['value_growth_percentile'] = spread_percentile
                    
                    # Regime classification
                    if spread_percentile > 0.7:
                        indicators['value_growth_regime'] = 'value_favored'
                    elif spread_percentile < 0.3:
                        indicators['value_growth_regime'] = 'growth_favored'  
                    else:
                        indicators['value_growth_regime'] = 'neutral'
        
        except Exception as e:
            logger.warning(f"Error calculating value/growth spread: {str(e)}")
            
        return indicators
    
    def _calculate_market_environment(self, data: pd.DataFrame) -> Dict:
        """Calculate overall market environment indicators"""
        indicators = {}
        
        try:
            # Risk-on vs Risk-off indicators
            if 'VTI' in data.columns and 'BND' in data.columns:
                # Stock/bond relative performance
                vti_3m = data['VTI'].pct_change(63).iloc[-1] if len(data) >= 63 else 0
                bnd_3m = data['BND'].pct_change(63).iloc[-1] if len(data) >= 63 else 0
                
                stock_bond_spread = vti_3m - bnd_3m
                indicators['stock_bond_spread'] = stock_bond_spread
                
                # Risk regime
                if stock_bond_spread > 0.02:  # Stocks outperforming by >2%
                    indicators['risk_regime'] = 'risk_on'
                elif stock_bond_spread < -0.02:  # Bonds outperforming by >2%
                    indicators['risk_regime'] = 'risk_off'
                else:
                    indicators['risk_regime'] = 'neutral'
            
            # International vs Domestic
            if 'VTI' in data.columns and 'VTIAX' in data.columns:
                vti_6m = data['VTI'].pct_change(126).iloc[-1] if len(data) >= 126 else 0
                vtiax_6m = data['VTIAX'].pct_change(126).iloc[-1] if len(data) >= 126 else 0
                
                domestic_intl_spread = vti_6m - vtiax_6m
                indicators['domestic_intl_spread'] = domestic_intl_spread
                
                if domestic_intl_spread > 0.05:
                    indicators['geographic_regime'] = 'domestic_favored'
                elif domestic_intl_spread < -0.05:
                    indicators['geographic_regime'] = 'international_favored'
                else:
                    indicators['geographic_regime'] = 'neutral'
                    
        except Exception as e:
            logger.warning(f"Error calculating market environment: {str(e)}")
            
        return indicators
        
    def _calculate_correlation_regime(self, data: pd.DataFrame) -> Dict:
        """Calculate asset correlation regime indicators"""
        indicators = {}
        
        try:
            # Calculate rolling correlations between major asset classes
            returns = data.pct_change().dropna()
            
            if len(returns.columns) >= 3:
                # 60-day rolling correlation matrix
                corr_60d = returns.rolling(60).corr()
                
                # Average correlation (excluding diagonal)
                if not corr_60d.empty:
                    latest_corr = corr_60d.iloc[-len(returns.columns):]
                    mask = np.ones_like(latest_corr, dtype=bool)
                    np.fill_diagonal(mask, False)
                    avg_correlation = latest_corr.values[mask].mean()
                    indicators['average_correlation'] = avg_correlation if not pd.isna(avg_correlation) else 0.3
                    
                    # Correlation regime
                    if avg_correlation > 0.6:
                        indicators['correlation_regime'] = 'high'
                    elif avg_correlation < 0.2:
                        indicators['correlation_regime'] = 'low'
                    else:
                        indicators['correlation_regime'] = 'normal'
                        
        except Exception as e:
            logger.warning(f"Error calculating correlation regime: {str(e)}")
            
        return indicators
    
    def get_regime_summary(self, indicators: Dict) -> Dict:
        """
        Generate a summary of the current market regime
        
        Args:
            indicators: Dictionary of calculated indicators
            
        Returns:
            Dictionary with regime summary and scores
        """
        try:
            summary = {
                'overall_regime': 'neutral',
                'confidence_score': 0.5,
                'key_factors': [],
                'regime_scores': {
                    'bullish': 0.0,
                    'bearish': 0.0, 
                    'volatile': 0.0,
                    'stable': 0.0
                }
            }
            
            # Score different regime components
            bullish_score = 0
            bearish_score = 0
            volatile_score = 0
            stable_score = 0
            
            # Momentum contribution
            if 'momentum_3m' in indicators:
                momentum = indicators['momentum_3m']
                if momentum > 0.1:
                    bullish_score += 1
                elif momentum < -0.1:
                    bearish_score += 1
            
            # Volatility contribution  
            if 'volatility_regime' in indicators:
                vol_regime = indicators['volatility_regime']
                if vol_regime == 'high':
                    volatile_score += 1
                elif vol_regime == 'low':
                    stable_score += 1
            
            # Risk regime contribution
            if 'risk_regime' in indicators:
                risk_regime = indicators['risk_regime']
                if risk_regime == 'risk_on':
                    bullish_score += 1
                elif risk_regime == 'risk_off':
                    bearish_score += 1
            
            # Normalize scores
            total_factors = max(1, bullish_score + bearish_score + volatile_score + stable_score)
            summary['regime_scores'] = {
                'bullish': bullish_score / total_factors,
                'bearish': bearish_score / total_factors,
                'volatile': volatile_score / total_factors,
                'stable': stable_score / total_factors
            }
            
            # Determine overall regime
            max_score = max(summary['regime_scores'].values())
            if max_score > 0.4:
                summary['overall_regime'] = max(summary['regime_scores'], 
                                              key=summary['regime_scores'].get)
                summary['confidence_score'] = max_score
            else:
                summary['overall_regime'] = 'neutral'
                summary['confidence_score'] = 0.5
                
            return summary
            
        except Exception as e:
            logger.error(f"Error generating regime summary: {str(e)}")
            return {'overall_regime': 'neutral', 'confidence_score': 0.5, 'key_factors': []}
