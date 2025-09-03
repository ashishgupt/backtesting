"""
Asset Allocation Fix - Adding Minimum Allocation Constraints

This patch adds minimum allocation constraints to ensure meaningful diversification
across all asset classes, preventing the optimizer from going to zero allocation
for international, emerging markets, and real estate assets.
"""

# Add this function to portfolio_optimizer.py

def _get_minimum_allocations(self, strategy_type: StrategyType, request: PortfolioRequest) -> Dict[str, float]:
    """
    Get minimum allocation constraints for each asset to ensure diversification
    
    Returns dict of asset -> minimum weight
    """
    
    if strategy_type == StrategyType.CONSERVATIVE:
        # Conservative: Ensure diversification with meaningful minimums
        return {
            'VTI': 0.05,      # 5% minimum US total market
            'VTIAX': 0.08,    # 8% minimum international developed  
            'BND': 0.25,      # 25% minimum bonds (existing)
            'VNQ': 0.03,      # 3% minimum real estate
            'GLD': 0.02,      # 2% minimum gold
            'VWO': 0.02,      # 2% minimum emerging markets  
            'QQQ': 0.0        # No minimum for growth (conservative)
        }
    
    elif strategy_type == StrategyType.BALANCED:
        # Balanced: Meaningful allocation across all major asset classes
        return {
            'VTI': 0.08,      # 8% minimum US total market
            'VTIAX': 0.05,    # 5% minimum international developed
            'BND': 0.05,      # 5% minimum bonds (reduced for balanced)
            'VNQ': 0.05,      # 5% minimum real estate
            'GLD': 0.03,      # 3% minimum gold
            'VWO': 0.03,      # 3% minimum emerging markets
            'QQQ': 0.05       # 5% minimum growth
        }
    
    else:  # AGGRESSIVE
        # Aggressive: Smaller minimums but still ensure diversification
        return {
            'VTI': 0.05,      # 5% minimum US total market  
            'VTIAX': 0.03,    # 3% minimum international developed
            'BND': 0.02,      # 2% minimum bonds (very low for aggressive)
            'VNQ': 0.03,      # 3% minimum real estate
            'GLD': 0.02,      # 2% minimum gold
            'VWO': 0.02,      # 2% minimum emerging markets
            'QQQ': 0.08       # 8% minimum growth (aggressive)
        }

# Update bounds in each optimization function:

def _optimize_conservative_fixed(self, returns_stats: Dict, 
                               request: PortfolioRequest) -> OptimizedPortfolio:
    """
    FIXED Conservative strategy with minimum allocation constraints
    """
    
    expected_returns = returns_stats['expected_returns'].values
    cov_matrix = returns_stats['covariance_matrix'].values
    
    # Get minimum allocations for diversification
    min_allocations = self._get_minimum_allocations(StrategyType.CONSERVATIVE, request)
    
    # Objective: minimize portfolio variance
    def objective(weights):
        return np.dot(weights, np.dot(cov_matrix, weights))
        
    # Constraints 
    constraints = [
        {'type': 'eq', 'fun': lambda x: np.sum(x) - 1.0},  # Weights sum to 1
    ]
    
    # FIXED BOUNDS: Include minimum allocations
    bounds = []
    for i, asset in enumerate(self.assets):
        min_weight = min_allocations.get(asset, 0.0)
        
        if asset == 'BND':  # Bonds
            bounds.append((min_weight, 0.60))
        elif asset == 'GLD':  # Gold  
            bounds.append((min_weight, 0.10))
        else:  # Equities
            bounds.append((min_weight, 0.25))
    
    # Initial guess respecting minimums
    x0 = np.array([0.12, 0.12, 0.45, 0.08, 0.05, 0.10, 0.08])
    # Adjust for minimums
    for i, asset in enumerate(self.assets):
        min_weight = min_allocations.get(asset, 0.0)
        x0[i] = max(x0[i], min_weight)
    
    # Normalize to sum to 1
    x0 = x0 / np.sum(x0)
    
    # Same optimization logic...
    result = optimize.minimize(
        objective, x0, method='SLSQP', bounds=bounds, constraints=constraints
    )
    
    # ... rest of function unchanged
