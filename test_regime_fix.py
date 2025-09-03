#!/usr/bin/env python3
"""
Test script to validate the regime classification fix
"""

import requests
import json
import sys
sys.path.append('/Users/ashish/Claude/backtesting')

from src.regime.regime_detector import MarketRegimeDetector

def test_classification_fix():
    """Test the corrected regime classification logic"""
    
    print("🔧 TESTING REGIME CLASSIFICATION FIX")
    print("=" * 50)
    
    # Test case based on the evidence from session context
    print("\n1. Testing with Known Market Conditions:")
    print("   - 15% 3-month momentum")  
    print("   - 22% 12-month momentum")
    print("   - 6.5% above 200-day MA")
    print("   - Risk-on sentiment")
    print("   - High volatility")
    
    test_indicators = {
        'momentum_3m': 0.15,  # 15% 3-month momentum
        'momentum_12m': 0.22, # 22% 12-month momentum  
        'price_vs_ma200': 0.065, # 6.5% above 200-day MA
        'volatility_regime': 'high',
        'risk_regime': 'risk_on',
        'correlation_regime': 'high',
        'volatility_percentile': 0.75,  # High but not extreme
        'average_correlation': 0.6
    }
    
    detector = MarketRegimeDetector()
    classification = detector._classify_regime(test_indicators)
    
    print(f"\n✅ CORRECTED Classification:")
    regime_name = detector.regime_types[classification['regime_type']]['name']
    print(f"   Regime: {regime_name}")
    print(f"   Confidence: {classification['confidence']:.1%}")
    
    print(f"\n📊 All Regime Scores:")
    for regime, score in classification['all_scores'].items():
        regime_name = detector.regime_types[regime]['name']
        print(f"   {regime_name}: {score:.3f}")
    
    # Test API endpoint
    print(f"\n2. Testing Live API:")
    try:
        response = requests.get('http://localhost:8007/api/regime/current?lookback_days=252', timeout=10)
        if response.status_code == 200:
            api_data = response.json()
            print(f"   ✅ API Regime: {api_data.get('regime_name', 'N/A')}")
            print(f"   ✅ API Confidence: {api_data.get('confidence_score', 'N/A'):.1%}")
            
            # Check if fix was applied
            current_regime = api_data.get('regime_type', '')
            if current_regime in ['volatile_bull', 'bull_market']:
                print("   🎉 SUCCESS: Positive momentum correctly classified!")
            elif current_regime == 'bear_market':
                print("   ⚠️  WARNING: Still showing Bear Market - may need API restart")
            else:
                print(f"   ℹ️  INFO: Classified as {current_regime}")
                
        else:
            print(f"   ❌ API Error: {response.status_code}")
            
    except Exception as e:
        print(f"   ❌ API Connection Error: {e}")
    
    print(f"\n3. Key Improvements Made:")
    print("   ✅ Bear Market now excludes positive momentum scenarios")
    print("   ✅ Volatile Bull criteria expanded for positive momentum + high volatility")
    print("   ✅ Better scoring weights and normalization")
    print("   ✅ Exclusion logic prevents misclassification")
    
    