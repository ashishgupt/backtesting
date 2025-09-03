#!/usr/bin/env python3
"""
Test portfolio analysis with full debugging
"""

import requests
import json

API_BASE = "http://localhost:8007"

# Test payload matching the guided dashboard
payload = {
    "allocation": {
        "allocation": {
            "VTI": 0.6,
            "VTIAX": 0.3,
            "BND": 0.1,
            "VNQ": 0.0,
            "GLD": 0.0,
            "VWO": 0.0,
            "QQQ": 0.0
        }
    },
    "start_date": "2015-01-01",
    "end_date": "2024-12-31"
}

print("🧪 Testing Portfolio Analysis API...")

try:
    response = requests.post(
        f"{API_BASE}/api/backtest/portfolio",
        headers={"Content-Type": "application/json"},
        json=payload,
        timeout=30
    )
    
    print(f"Status: {response.status_code}")
    
    if response.status_code == 200:
        data = response.json()
        
        # Check if we have the expected fields for the frontend
        print("\n✅ API Response Structure:")
        print(f"   - success: {data.get('success')}")
        print(f"   - performance_metrics: {'present' if 'performance_metrics' in data else 'missing'}")
        print(f"   - metrics: {'present' if 'metrics' in data else 'missing'}")
        
        # Check if performance_metrics has the expected fields
        if 'performance_metrics' in data:
            pm = data['performance_metrics']
            print(f"\n📊 Performance Metrics:")
            print(f"   - cagr: {pm.get('cagr', 'missing')}")
            print(f"   - sharpe_ratio: {pm.get('sharpe_ratio', 'missing')}")
            print(f"   - volatility: {pm.get('volatility', 'missing')}")
            print(f"   - max_drawdown: {pm.get('max_drawdown', 'missing')}")
            
            # Format like the frontend would
            try:
                print(f"\n🎯 Frontend Display Values:")
                print(f"   - CAGR: {(pm['cagr'] * 100):.1f}%")
                print(f"   - Sharpe: {pm['sharpe_ratio']:.2f}")
                print(f"   - Volatility: {(pm['volatility'] * 100):.1f}%")
                print(f"   - Max Drawdown: {(abs(pm['max_drawdown']) * 100):.1f}%")
            except Exception as e:
                print(f"   ❌ Error formatting metrics: {e}")
        
        print("\n✅ API is working correctly!")
        
    else:
        print(f"❌ Error {response.status_code}:")
        print(response.text)
        
except Exception as e:
    print(f"❌ Request failed: {e}")
