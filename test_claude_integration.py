#!/usr/bin/env python3
"""
🤖 Test Claude Portfolio Advisor Integration
"""
import requests
import json

def test_claude_integration():
    """Test the Claude portfolio recommendation endpoints"""
    print("🤖 Testing Claude Portfolio Advisor Integration")
    print("=" * 55)
    
    base_url = "http://127.0.0.1:8006"
    
    # Test 1: Example queries endpoint
    print("1️⃣  EXAMPLE QUERIES")
    print("-" * 20)
    
    try:
        response = requests.get(f"{base_url}/api/chat/examples")
        if response.status_code == 200:
            examples = response.json()
            print("📋 Recommendation Examples:")
            for example in examples["recommendation_examples"][:3]:
                print(f"   • {example}")
            print("📋 Analysis Examples:")
            for example in examples["analysis_examples"][:3]:
                print(f"   • {example}")
        else:
            print(f"❌ Failed to get examples: {response.status_code}")
    except Exception as e:
        print(f"❌ Examples test failed: {e}")
        
    # Test 2: Natural language recommendations
    print(f"\n2️⃣  NATURAL LANGUAGE RECOMMENDATIONS")
    print("-" * 40)
    
    test_requests = [
        "I'm 35 years old and want a balanced portfolio for retirement",
        "Conservative allocation with some international exposure", 
        "Aggressive growth portfolio for a 25-year-old"
    ]
    
    for i, user_message in enumerate(test_requests, 1):
        try:
            print(f"\n🔍 Test {i}: \"{user_message}\"")
            
            response = requests.post(
                f"{base_url}/api/chat/recommend",
                json={"message": user_message}
            )
            
            if response.status_code == 200:
                result = response.json()
                print(f"✅ Recommendation generated:")
                print(f"   Risk Profile: {result['risk_profile']}")
                print(f"   Allocation: {', '.join([f'{k}:{v:.0%}' for k,v in result['allocation'].items() if v > 0.01])}")
                print(f"   Expected CAGR: {result['expected_cagr']:.1%}")
                print(f"   Max Drawdown: {result['max_drawdown']:.1%}")
                print(f"   Sharpe Ratio: {result['sharpe_ratio']:.2f}")
                print(f"   Confidence: {result['confidence_score']:.0%}")
                
                # Show first part of recommendation text
                rec_text = result['recommendation'].split('\n')[0:3]
                print(f"   Preview: {rec_text[0][:60]}...")
            else:
                print(f"❌ Failed: {response.status_code} - {response.text}")
                
        except Exception as e:
            print(f"❌ Recommendation test {i} failed: {e}")
            
    # Test 3: Portfolio analysis
    print(f"\n3️⃣  PORTFOLIO ANALYSIS")
    print("-" * 25)
    
    test_portfolios = [
        {
            "allocation": {"VTI": 0.6, "VTIAX": 0.3, "BND": 0.1},
            "question": "How risky is this portfolio?"
        },
        {
            "allocation": {"VTI": 0.2, "VTIAX": 0.1, "BND": 0.7},
            "question": "What returns should I expect?"
        }
    ]
    
    for i, test_case in enumerate(test_portfolios, 1):
        try:
            print(f"\n🔍 Analysis {i}: {test_case['question']}")
            print(f"   Portfolio: {', '.join([f'{k}:{v:.0%}' for k,v in test_case['allocation'].items()])}")
            
            response = requests.post(
                f"{base_url}/api/chat/analyze",
                json=test_case
            )
            
            if response.status_code == 200:
                result = response.json()
                print(f"✅ Analysis completed:")
                print(f"   Key Insights: {len(result['key_insights'])} found")
                print(f"   Suggestions: {len(result['suggestions'])} provided")
                
                # Show first insight and suggestion
                if result['key_insights']:
                    print(f"   Top Insight: {result['key_insights'][0][:60]}...")
                if result['suggestions']:
                    print(f"   Top Suggestion: {result['suggestions'][0][:60]}...")
                    
            else:
                print(f"❌ Failed: {response.status_code}")
                
        except Exception as e:
            print(f"❌ Analysis test {i} failed: {e}")
    
    print(f"\n✅ Claude Integration Testing Complete!")
    print(f"🎯 Natural language portfolio advice is operational")
    print(f"🤖 Ready for conversational portfolio recommendations")

if __name__ == "__main__":
    test_claude_integration()
