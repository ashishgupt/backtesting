#!/usr/bin/env python3
"""
Test script for AI Agent implementation
Validates Claude API integration and tool calling functionality
"""

import asyncio
import sys
import os
import json
from datetime import datetime

# Add project root to path
sys.path.append('/Users/ashish/Claude/backtesting')

# Test imports
def test_imports():
    """Test that all required modules can be imported"""
    print("🧪 Testing imports...")
    
    try:
        from src.ai.claude_ai_agent import ClaudeAIAgent, AgentResponse
        print("✅ ClaudeAIAgent imported successfully")
        
        from src.ai.ai_agent_tools import ToolRegistry, ToolCallHandler
        print("✅ AI Agent tools imported successfully")
        
        import httpx
        print("✅ httpx available for API calls")
        
        return True
    except ImportError as e:
        print(f"❌ Import failed: {e}")
        return False

# Test environment setup
def test_environment():
    """Test environment configuration"""
    print("\n🔧 Testing environment...")
    
    api_key = os.getenv("ANTHROPIC_API_KEY")
    if api_key:
        print(f"✅ ANTHROPIC_API_KEY configured (length: {len(api_key)})")
        return True
    else:
        print("❌ ANTHROPIC_API_KEY not found")
        print("Please set: export ANTHROPIC_API_KEY=your_key_here")
        return False

# Test tool registry
def test_tool_registry():
    """Test tool definitions"""
    print("\n🛠️ Testing tool registry...")
    
    try:
        from src.ai.ai_agent_tools import ToolRegistry
        registry = ToolRegistry()
        tools = registry.get_all_tools()
        
        print(f"✅ {len(tools)} tools registered:")
        for tool in tools:
            print(f"   - {tool['name']}: {tool['description'][:60]}...")
        
        return True
    except Exception as e:
        print(f"❌ Tool registry test failed: {e}")
        return False

# Test Claude API connection
async def test_claude_api():
    """Test direct Claude API connection"""
    print("\n🌐 Testing Claude API connection...")
    
    try:
        import httpx
        
        api_key = os.getenv("ANTHROPIC_API_KEY")
        if not api_key:
            print("❌ No API key for testing")
            return False
        
        headers = {
            "Content-Type": "application/json",
            "x-api-key": api_key
        }
        
        test_payload = {
            "model": "claude-sonnet-4-20250514",
            "max_tokens": 100,
            "messages": [
                {
                    "role": "user",
                    "content": "Hello! This is a test message. Please respond briefly that the connection is working."
                }
            ]
        }
        
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(
                "https://api.anthropic.com/v1/messages",
                headers=headers,
                json=test_payload
            )
        
        if response.status_code == 200:
            data = response.json()
            response_text = data["content"][0]["text"]
            print(f"✅ Claude API connection successful")
            print(f"Response: {response_text[:100]}...")
            return True
        else:
            print(f"❌ Claude API error: {response.status_code}")
            print(f"Details: {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ Claude API test failed: {e}")
        return False

# Test AI Agent initialization
async def test_agent_init():
    """Test AI Agent initialization"""
    print("\n🤖 Testing AI Agent initialization...")
    
    try:
        from src.ai.claude_ai_agent import ClaudeAIAgent
        
        agent = ClaudeAIAgent()
        print("✅ AI Agent initialized successfully")
        print(f"Model: {agent.model}")
        print(f"Max tokens: {agent.max_tokens}")
        print(f"Default portfolio keys: {list(agent.default_portfolio.keys())}")
        
        return True, agent
    except Exception as e:
        print(f"❌ AI Agent initialization failed: {e}")
        return False, None

# Test sample request processing  
async def test_sample_request(agent):
    """Test sample request processing"""
    print("\n📝 Testing sample request processing...")
    
    if not agent:
        print("❌ No agent available for testing")
        return False
    
    try:
        # Simple test message
        test_message = "What would be the recovery time for a balanced portfolio?"
        
        print(f"Test query: {test_message}")
        print("Processing...")
        
        start_time = datetime.now()
        response = await agent.process_request(test_message)
        end_time = datetime.now()
        
        processing_time = (end_time - start_time).total_seconds()
        
        print(f"✅ Request processed in {processing_time:.2f} seconds")
        print(f"Tools called: {response.tool_calls_made}")
        print(f"Synthesis quality: {response.synthesis_quality}")
        print(f"Confidence: {response.confidence_score:.2f}")
        print(f"Response preview: {response.recommendation[:150]}...")
        
        return True
    except Exception as e:
        print(f"❌ Sample request test failed: {e}")
        return False

# Main test runner
async def run_all_tests():
    """Run all tests"""
    print("🚀 AI Agent Test Suite")
    print("=" * 50)
    
    results = []
    
    # Sync tests
    results.append(("Imports", test_imports()))
    results.append(("Environment", test_environment()))
    results.append(("Tool Registry", test_tool_registry()))
    
    # Async tests
    results.append(("Claude API", await test_claude_api()))
    
    agent_success, agent = await test_agent_init()
    results.append(("Agent Init", agent_success))
    
    if agent_success:
        results.append(("Sample Request", await test_sample_request(agent)))
    else:
        results.append(("Sample Request", False))
    
    # Summary
    print("\n" + "=" * 50)
    print("📊 Test Results Summary:")
    
    passed = 0
    total = len(results)
    
    for test_name, success in results:
        status = "✅ PASS" if success else "❌ FAIL"
        print(f"{test_name:15} {status}")
        if success:
            passed += 1
    
    print(f"\nOverall: {passed}/{total} tests passed")
    
    if passed == total:
        print("\n🎉 All tests passed! AI Agent is ready for deployment.")
        print("\nNext steps:")
        print("1. Update claude_routes.py with enhanced version")
        print("2. Test integration with existing FastAPI server")
        print("3. Monitor performance and adjust as needed")
    else:
        print(f"\n⚠️  {total - passed} tests failed. Please fix issues before deployment.")
    
    return passed == total

if __name__ == "__main__":
    success = asyncio.run(run_all_tests())
    sys.exit(0 if success else 1)
