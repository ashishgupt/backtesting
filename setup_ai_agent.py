#!/usr/bin/env python3
"""
Setup script for AI Agent implementation
Prepares environment and installs dependencies
"""

import os
import subprocess
import sys

def setup_ai_agent():
    """Setup AI Agent environment"""
    
    print("🚀 Setting up AI Agent for Portfolio Analytics...")
    
    # 1. Check environment variables
    print("\n1. Checking environment configuration...")
    
    if not os.getenv("ANTHROPIC_API_KEY"):
        print("❌ ANTHROPIC_API_KEY not found!")
        print("Please set your Anthropic API key:")
        print("export ANTHROPIC_API_KEY=your_key_here")
        print("\nOr add to .env file:")
        print("ANTHROPIC_API_KEY=your_key_here")
        
        # Check if .env exists
        env_file = "/Users/ashish/Claude/backtesting/.env"
        if os.path.exists(env_file):
            with open(env_file, 'a') as f:
                f.write("\n# AI Agent Configuration\n")
                f.write("# ANTHROPIC_API_KEY=your_key_here\n")
            print(f"✅ Template added to {env_file}")
        
        return False
    else:
        print("✅ ANTHROPIC_API_KEY configured")
    
    # 2. Install required packages
    print("\n2. Installing required packages...")
    required_packages = [
        "httpx",          # For async HTTP calls to Claude API
        "anthropic",      # Official Anthropic SDK (optional)
    ]
    
    for package in required_packages:
        try:
            subprocess.check_call([sys.executable, "-m", "pip", "install", package])
            print(f"✅ {package} installed")
        except subprocess.CalledProcessError:
            print(f"❌ Failed to install {package}")
            return False
    
    # 3. Create AI agent module structure
    print("\n3. Creating AI Agent module structure...")
    
    agent_dir = "/Users/ashish/Claude/backtesting/src/ai"
    
    # Ensure directory exists
    os.makedirs(agent_dir, exist_ok=True)
    
    # Create __init__.py if it doesn't exist
    init_file = os.path.join(agent_dir, "__init__.py")
    if not os.path.exists(init_file):
        with open(init_file, 'w') as f:
            f.write('"""AI Agent module for portfolio analytics"""\n')
        print(f"✅ Created {init_file}")
    
    # 4. Test Claude API connection
    print("\n4. Testing Claude API connection...")
    
    import httpx
    import json
    
    api_key = os.getenv("ANTHROPIC_API_KEY")
    
    try:
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
                    "content": "Hello, this is a test message. Please respond briefly."
                }
            ]
        }
        
        # Test connection (synchronous for setup)
        import requests
        response = requests.post(
            "https://api.anthropic.com/v1/messages",
            headers=headers,
            json=test_payload,
            timeout=10
        )
        
        if response.status_code == 200:
            print("✅ Claude API connection successful")
            print(f"Response: {response.json()['content'][0]['text'][:50]}...")
        else:
            print(f"❌ Claude API test failed: {response.status_code}")
            print(f"Error: {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ Claude API test error: {e}")
        return False
    
    print("\n🎉 AI Agent setup completed successfully!")
    print("\nNext steps:")
    print("1. Copy the AI Agent implementation files to src/ai/")
    print("2. Update claude_routes.py with the enhanced version")
    print("3. Test the agent with: python test_ai_agent.py")
    
    return True

if __name__ == "__main__":
    success = setup_ai_agent()
    sys.exit(0 if success else 1)
