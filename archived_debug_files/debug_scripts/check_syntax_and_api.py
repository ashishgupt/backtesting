#!/usr/bin/env python3
"""
Test the JavaScript syntax and API connectivity from the server side
"""

import subprocess
import sys
import os

def check_html_syntax(file_path):
    """Check if HTML file has valid syntax"""
    print(f"🔍 Checking {file_path}...")
    
    if not os.path.exists(file_path):
        print(f"❌ File not found: {file_path}")
        return False
    
    # Read the file and look for common JavaScript issues
    with open(file_path, 'r') as f:
        content = f.read()
    
    # Check for common JavaScript syntax issues
    issues = []
    
    # Check for unclosed functions
    open_braces = content.count('{')
    close_braces = content.count('}')
    if open_braces != close_braces:
        issues.append(f"Mismatched braces: {open_braces} open, {close_braces} close")
    
    # Check for unclosed parentheses
    open_parens = content.count('(')
    close_parens = content.count(')')
    if open_parens != close_parens:
        issues.append(f"Mismatched parentheses: {open_parens} open, {close_parens} close")
    
    # Check for async/await usage
    if 'async function' in content and 'await' in content:
        print("✅ Async/await syntax found - likely correct")
    
    # Check for fetch calls
    fetch_count = content.count('fetch(')
    print(f"📡 Found {fetch_count} fetch() calls")
    
    # Check for console.log statements
    log_count = content.count('console.log')
    print(f"🐛 Found {log_count} console.log statements")
    
    if issues:
        print("❌ Issues found:")
        for issue in issues:
            print(f"   - {issue}")
        return False
    else:
        print("✅ Basic syntax check passed")
        return True

def test_api_directly():
    """Test the API directly with curl"""
    print("\n🧪 Testing API directly with curl...")
    
    # Test health endpoint
    try:
        result = subprocess.run([
            'curl', '-s', '-w', '%{http_code}', 
            'http://localhost:8007/api/health'
        ], capture_output=True, text=True, timeout=10)
        
        print(f"Health endpoint - Status: {result.stdout[-3:] if len(result.stdout) >= 3 else 'unknown'}")
        if result.stdout:
            print(f"Health endpoint - Response: {result.stdout[:-3]}")
    except Exception as e:
        print(f"❌ Health check failed: {e}")
    
    # Test portfolio analysis endpoint
    payload = '''
    {
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
    '''
    
    try:
        result = subprocess.run([
            'curl', '-s', '-w', '%{http_code}', '-X', 'POST',
            '-H', 'Content-Type: application/json',
            '-d', payload,
            'http://localhost:8007/api/backtest/portfolio'
        ], capture_output=True, text=True, timeout=30)
        
        status_code = result.stdout[-3:] if len(result.stdout) >= 3 else 'unknown'
        response_body = result.stdout[:-3] if len(result.stdout) >= 3 else result.stdout
        
        print(f"Portfolio endpoint - Status: {status_code}")
        if status_code == '200':
            print("✅ Portfolio API is working")
        else:
            print("❌ Portfolio API failed")
            print(f"Response: {response_body}")
            
    except Exception as e:
        print(f"❌ Portfolio API test failed: {e}")

def main():
    print("🔍 JavaScript and API Connectivity Check")
    print("=" * 50)
    
    # Check the key files
    files_to_check = [
        "/Users/ashish/Claude/backtesting/web/guided-dashboard.html",
        "/Users/ashish/Claude/backtesting/web/portfolio-debug.html",
        "/Users/ashish/Claude/backtesting/web/portfolio-test.html"
    ]
    
    for file_path in files_to_check:
        check_html_syntax(file_path)
        print()
    
    # Test API directly
    test_api_directly()
    
    print("\n" + "=" * 50)
    print("🎯 If syntax is OK but browser fails, check:")
    print("   1. Browser console for JavaScript errors")
    print("   2. Network tab for failed requests")
    print("   3. CORS issues (should be disabled in API)")

if __name__ == "__main__":
    main()
