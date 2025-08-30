#!/usr/bin/env python3
"""
Test script to verify the datetime serialization fix
"""

from datetime import datetime
import json
from dataclasses import dataclass

@dataclass
class RollingPeriodResult:
    """Mock of the real RollingPeriodResult for testing"""
    start_date: datetime
    end_date: datetime
    period_years: int
    cagr: float
    volatility: float
    sharpe_ratio: float
    max_drawdown: float
    total_return: float

# Create test data similar to what the API generates
periods = [
    RollingPeriodResult(
        start_date=datetime(2018, 1, 1),
        end_date=datetime(2023, 1, 1),
        period_years=5,
        cagr=0.0888,
        volatility=0.157,
        sharpe_ratio=0.566,
        max_drawdown=0.125,
        total_return=0.524
    ),
    RollingPeriodResult(
        start_date=datetime(2018, 4, 1),
        end_date=datetime(2023, 4, 1),
        period_years=5,
        cagr=0.0912,
        volatility=0.162,
        sharpe_ratio=0.563,
        max_drawdown=0.131,
        total_return=0.547
    )
]

print("Testing datetime serialization fix...")
print(f"Generated {len(periods)} test periods")

# Test the BROKEN approach (what was causing the bug)
print("\n🚫 Testing BROKEN approach (direct datetime in JSON):")
try:
    broken_data = [
        {
            "start_date": period.start_date,
            "end_date": period.end_date,
            "period_years": period.period_years,
            "cagr": period.cagr
        }
        for period in periods
    ]
    json_str = json.dumps({"periods": broken_data})
    print("✅ BROKEN approach succeeded (unexpected!)")
except Exception as e:
    print(f"❌ BROKEN approach failed as expected: {e}")

# Test the FIXED approach (using isoformat())
print("\n✅ Testing FIXED approach (isoformat() conversion):")
try:
    fixed_data = [
        {
            "start_date": period.start_date.isoformat(),
            "end_date": period.end_date.isoformat(),
            "period_years": period.period_years,
            "cagr": period.cagr,
            "volatility": period.volatility,
            "sharpe_ratio": period.sharpe_ratio,
            "max_drawdown": period.max_drawdown,
            "total_return": period.total_return
        }
        for period in periods
    ]
    json_str = json.dumps({"periods": fixed_data}, indent=2)
    print("✅ FIXED approach succeeded!")
    print(f"Sample JSON output:\n{json_str}")
    
    # Verify we can parse it back
    parsed = json.loads(json_str)
    print(f"\n✅ JSON round-trip successful!")
    print(f"First period start date: {parsed['periods'][0]['start_date']}")
    
except Exception as e:
    print(f"❌ FIXED approach failed: {e}")

print("\n🎯 Summary: The fix converts datetime objects to ISO format strings using .isoformat()")
print("This allows FastAPI to serialize the response as JSON successfully.")
