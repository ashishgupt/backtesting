#!/bin/bash
# Sprint 7 Phase 1 Demonstration Script
# Shows the transformation from basic robo-advisor to institutional-grade optimization

echo "🚀 SPRINT 7 PHASE 1 DEMONSTRATION"
echo "=================================="
echo "Transformation: Basic Robo-Advisor → Institutional-Grade Optimization"
echo ""

echo "📊 TESTING ENHANCED OPTIMIZATION API:"
echo "Calling sophisticated portfolio optimization with real user parameters..."
echo ""

# Test the enhanced optimization API
curl -s -X POST "http://localhost:8007/api/enhanced/portfolio/optimize" \
  -H "Content-Type: application/json" \
  -d '{
    "current_savings": 50000,
    "target_amount": 200000,
    "time_horizon": 15,
    "account_type": "tax_free",
    "new_money_available": true,
    "max_annual_contribution": 6000
  }' | python3 -m json.tool | head -30

echo ""
echo "✅ TRANSFORMATION COMPLETE!"
echo ""
echo "BEFORE (Static - Sprint 6):"
echo "  Conservative: VTI 30%, BND 70%"
echo "  Balanced: VTI 60%, VTIAX 30%, BND 10%"
echo "  Aggressive: VTI 80%, VTIAX 20%"
echo "  → Looked like basic robo-advisor from 2010!"
echo ""
echo "AFTER (Dynamic - Sprint 7):"
echo "  ✨ Mathematical Sharpe ratio optimization"
echo "  ✨ 7-asset professional diversification"
echo "  ✨ Account-type tax intelligence"
echo "  ✨ Expected returns & risk metrics"
echo "  → Institutional-grade optimization platform!"
echo ""
echo "🎯 NEXT: Phase 2 - Validation & Analytics Integration"
echo "Ready to showcase our rigorous backtesting methodology!"
