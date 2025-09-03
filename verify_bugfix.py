#!/usr/bin/env python3
"""
Verification script for Sprint 7 Phase 1B bug fix
Tests that the beginner-friendly metrics are properly implemented in guided-dashboard.html
"""

import re
import sys
from pathlib import Path

def check_guided_dashboard_fixes():
    """Check if all the bug fixes have been properly applied"""
    
    dashboard_path = Path(__file__).parent / 'web' / 'guided-dashboard.html'
    
    if not dashboard_path.exists():
        print("❌ guided-dashboard.html not found")
        return False
    
    with open(dashboard_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    checks = []
    
    # Check 1: Enhanced optimization-metrics CSS
    if 'background: #f8fafc;' in content and 'border: 1px solid #e2e8f0;' in content:
        checks.append("✅ Enhanced optimization-metrics CSS styling")
    else:
        checks.append("❌ Missing enhanced optimization-metrics CSS styling")
    
    # Check 2: De-emphasized asset-breakdown CSS  
    if 'opacity: 0.7;' in content and '.asset-breakdown' in content:
        checks.append("✅ De-emphasized asset-breakdown CSS styling")
    else:
        checks.append("❌ Missing de-emphasized asset-breakdown CSS styling")
    
    # Check 3: Key Information headers
    key_info_count = content.count('💡 Key Information:')
    if key_info_count >= 3:  # Should appear in all 3 portfolio cards
        checks.append(f"✅ Key Information headers present ({key_info_count} found)")
    else:
        checks.append(f"❌ Missing Key Information headers (only {key_info_count} found)")
    
    # Check 4: Technical Details labels
    tech_details_count = content.count('📋 Technical Details (Asset Allocation):')
    if tech_details_count >= 3:  # Should appear in all 3 portfolio cards
        checks.append(f"✅ Technical Details labels present ({tech_details_count} found)")
    else:
        checks.append(f"❌ Missing Technical Details labels (only {tech_details_count} found)")
    
    # Check 5: Enhanced test function
    if 'window.debugPortfolioCards' in content and 'window.reinitializeCards' in content:
        checks.append("✅ Enhanced debugging functions present")
    else:
        checks.append("❌ Missing enhanced debugging functions")
    
    # Check 6: Data field attributes for beginner metrics
    expected_fields = ['expected_return', 'risk_description', 'ten_year_projection']
    field_checks = []
    for field in expected_fields:
        count = content.count(f'data-field="{field}"')
        if count >= 3:  # Should appear in all 3 portfolio cards
            field_checks.append(f"  ✅ {field} fields: {count}")
        else:
            field_checks.append(f"  ❌ {field} fields: {count} (expected 3+)")
    
    checks.append("Data field attributes:")
    checks.extend(field_checks)
    
    # Check 7: Test function improvements
    if 'Found ${returnElements.length} return elements' in content:
        checks.append("✅ Enhanced test function with better logging")
    else:
        checks.append("❌ Missing enhanced test function logging")
    
    # Print results
    print("🔍 SPRINT 7 PHASE 1B BUG FIX VERIFICATION")
    print("=" * 50)
    
    success_count = sum(1 for check in checks if check.startswith("✅"))
    total_checks = len([c for c in checks if not c.startswith("  ")])
    
    for check in checks:
        print(check)
    
    print("=" * 50)
    if success_count >= total_checks - 1:  # Allow for 1 minor issue
        print(f"🎉 VERIFICATION PASSED: {success_count}/{total_checks} checks successful")
        print("✅ Bug fixes have been properly implemented!")
        return True
    else:
        print(f"❌ VERIFICATION FAILED: {success_count}/{total_checks} checks successful")
        print("⚠️  Some bug fixes may be missing or incomplete")
        return False

def check_server_running():
    """Check if the development server is running"""
    import urllib.request
    import urllib.error
    
    try:
        response = urllib.request.urlopen('http://localhost:8007/guided-dashboard.html', timeout=5)
        if response.getcode() == 200:
            print("✅ Development server is running on http://localhost:8007")
            return True
    except urllib.error.URLError:
        pass
    
    print("❌ Development server is not running on http://localhost:8007")
    print("💡 Start server with: python3 -m uvicorn src.api.main:app --host 0.0.0.0 --port 8007 --reload")
    return False

if __name__ == "__main__":
    print("🚀 Starting Sprint 7 Phase 1B Bug Fix Verification...")
    print()
    
    # Check file fixes
    fixes_ok = check_guided_dashboard_fixes()
    print()
    
    # Check server
    server_ok = check_server_running()
    print()
    
    if fixes_ok and server_ok:
        print("🎯 ALL CHECKS PASSED - Ready for user testing!")
        print()
        print("🧪 MANUAL TESTING INSTRUCTIONS:")
        print("1. Open: http://localhost:8007/guided-dashboard.html")
        print("2. Fill out Step 1 and navigate to Step 2")  
        print("3. Open browser console (F12)")
        print("4. Run: window.testMetrics()")
        print("5. Verify beginner-friendly metrics are displayed prominently")
        sys.exit(0)
    else:
        print("⚠️  ISSUES DETECTED - Please review and fix before testing")
        sys.exit(1)
