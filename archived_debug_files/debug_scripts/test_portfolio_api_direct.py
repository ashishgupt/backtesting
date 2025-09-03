#!/usr/bin/env python3
"""
Direct test of the portfolio analysis API with the exact same format as the frontend
"""

import requests
import json

API_BASE = "http://localhost:8007"

# Test the exact same payload as the frontend would send
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

print("🧪 Testing Portfolio Analysis API with frontend payload...")
print(f"📤 Sending payload:")
print(json.dumps(payload, indent=2))
print()

try:
    response = requests.post(
        f"{API_BASE}/api/backtest/portfolio",
        headers={"Content-Type": "application/json"},
        json=payload,
        timeout=30
    )
    
    print(f"📥 Response Status: {response.status_code}")
    print(f"📥 Response Headers: {dict(response.headers)}")
    print()
    
    if response.status_code == 200:
        data = response.json()
        print("✅ Success! Response data:")
        print(json.dumps(data, indent=2))
    else:
        print("❌ Error Response:")
        print(response.text)
        
        # Try to parse as JSON for better formatting
        try:
            error_data = response.json()
            print("\nFormatted error:")
            print(json.dumps(error_data, indent=2))
        except:
            pass
            
except Exception as e:
    print(f"❌ Request failed: {e}")
