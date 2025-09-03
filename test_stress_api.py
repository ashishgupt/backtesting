#!/usr/bin/env python3
"""
Simple test script to verify the stress test API is working correctly.
Run this to test the API without browser/CORS issues.
"""

import requests
import json

def test_stress_test_api():
    print("🧪 Testing Stress Test API...")
    
    # Test data
    api_base = "http://localhost:8007"
    endpoint = f"{api_base}/api/analyze/stress-test"
    
    payload = {
        "allocation": {"VTI": 0.6, "BND": 0.2, "VTIAX": 0.15, "VNQ": 0.05},
        "crisis_periods": ["2008-financial-crisis", "2020-covid-crash", "2022-bear-market"]
    }
    
    try:
        print(f"📡 Calling: {endpoint}")
        print(f"📦 Payload: {json.dumps(payload, indent=2)}")
        
        response = requests.post(
            endpoint,
            json=payload,
            headers={"Content-Type": "application/json"}
        )
        
        print(f"📊 Response Status: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print("✅ API Response received successfully!")
            
            # Check response structure
            print(f"\n📋 Response Structure Analysis:")
            print(f"- Has 'crisis_results': {bool(data.get('crisis_results'))}")
            print(f"- Has 'summary': {bool(data.get('summary'))}")
            
            if data.get('crisis_results'):
                crisis_results = data['crisis_results']
                print(f"- Crisis results count: {len(crisis_results)}")
                for i, crisis in enumerate(crisis_results):
                    name = crisis.get('crisis_name', 'Unknown')
                    decline = crisis.get('crisis_decline', 0) * 100
                    recovery = crisis.get('recovery_time_days', 0)
                    resilience = crisis.get('resilience_score', 0)
                    print(f"  {i+1}. {name}: {decline:.1f}% decline, {recovery} days recovery, {resilience:.1f} resilience")
            
            if data.get('summary'):
                summary = data['summary']
                print(f"\n📈 Summary:")
                print(f"- Overall resilience score: {summary.get('overall_resilience_score', 0):.1f}")
                print(f"- Average recovery time: {summary.get('avg_recovery_time_days', 0)} days")
                print(f"- Average crisis decline: {summary.get('avg_crisis_decline', 0) * 100:.1f}%")
                print(f"- Worst crisis decline: {summary.get('worst_crisis_decline', 0) * 100:.1f}%")
            
            print("\n🎯 Test Result: SUCCESS - API is working correctly!")
            return True
            
        else:
            print(f"❌ API Error: {response.status_code}")
            print(f"Response: {response.text}")
            return False
            
    except requests.exceptions.ConnectionError:
        print("❌ Connection Error: Server is not running on localhost:8007")
        return False
    except Exception as e:
        print(f"❌ Test Error: {e}")
        return False

if __name__ == "__main__":
    test_stress_test_api()
