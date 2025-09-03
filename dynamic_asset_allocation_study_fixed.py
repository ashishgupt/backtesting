    def _get_rolling_historical_data(self, start_date: str, end_date: str) -> Optional[pd.DataFrame]:
        """
        Get historical data for a specific date range and pivot to wide format for analysis
        """
        try:
            # Get full historical data (in long format)
            full_data = self.optimizer._get_historical_data(20)
            
            # Filter to date range
            start_dt = pd.to_datetime(start_date)
            end_dt = pd.to_datetime(end_date)
            
            # Filter data by date range
            filtered_data = full_data[
                (pd.to_datetime(full_data['Date']) >= start_dt) & 
                (pd.to_datetime(full_data['Date']) <= end_dt)
            ].copy()
            
            if len(filtered_data) == 0:
                return None
            
            # Pivot to wide format for easier analysis
            # Create a pivot table with Date as index and Symbol as columns
            wide_data = filtered_data.pivot_table(
                index='Date',
                columns='Symbol', 
                values='AdjClose',
                aggfunc='first'
            ).reset_index()
            
            # Fill any missing data forward
            wide_data = wide_data.fillna(method='ffill')
            
            return wide_data if len(wide_data) > 0 else None
            
        except Exception as e:
            print(f"   ❌ Error filtering data for {start_date} to {end_date}: {e}")
            return None

    def simulate_performance(self, allocation_strategy: str = "static") -> PerformanceResult:
        """
        Simulate portfolio performance using either static or rolling allocations
        """
        print(f"\n📊 SIMULATING {allocation_strategy.upper()} STRATEGY PERFORMANCE")
        print("-" * 60)
        
        try:
            # Get historical data for simulation period in wide format
            simulation_data = self._get_rolling_historical_data(
                self.study_period_start, 
                self.study_period_end
            )
            
            if simulation_data is None or len(simulation_data) == 0:
                print("❌ No data available for simulation period")
                return None
            
            print(f"📊 Simulation data: {len(simulation_data)} days from {simulation_data['Date'].min()} to {simulation_data['Date'].max()}")
            
            # Ensure all required assets are present
            available_assets = [col for col in simulation_data.columns if col != 'Date']
            missing_assets = [asset for asset in self.assets if asset not in available_assets]
            if missing_assets:
                print(f"⚠️  Missing assets in data: {missing_assets}")
            
            # Calculate returns for each available asset
            returns_data = {}
            for asset in self.assets:
                if asset in simulation_data.columns:
                    prices = simulation_data[asset].dropna()
                    if len(prices) > 1:
                        returns = prices.pct_change().dropna()
                        returns_data[asset] = returns
                        print(f"   ✅ {asset}: {len(returns)} return observations")
                    else:
                        print(f"   ❌ {asset}: Insufficient price data")
                else:
                    print(f"   ❌ {asset}: Not found in data")
            
            if not returns_data:
                print("❌ No return data available for simulation")
                return None
            
            # Simulate portfolio performance
            portfolio_values = [self.initial_portfolio_value]
            portfolio_returns = []
            allocation_changes = 0
            current_allocation = None
            
            # Get dates for simulation
            simulation_dates = pd.to_datetime(simulation_data['Date'])
            
            print(f"🔄 Simulating performance over {len(simulation_dates)} days...")
            
            for i in range(1, len(simulation_dates)):  # Start from 1 for returns calculation
                date = simulation_dates.iloc[i]
                year = date.year
                
                # Determine allocation for this year
                if allocation_strategy == "static" and self.static_allocation:
                    allocation = self.static_allocation.allocation
                    
                elif allocation_strategy == "rolling":
                    # Find allocation for this year
                    year_allocation = None
                    for ra in self.rolling_allocations:
                        if ra.year == year:
                            year_allocation = ra.allocation
                            break
                    
                    if year_allocation is None:
                        # Use previous year's allocation or fallback to static
                        if current_allocation:
                            allocation = current_allocation
                        elif self.static_allocation:
                            allocation = self.static_allocation.allocation
                        else:
                            continue
                    else:
                        allocation = year_allocation
                        
                        # Count allocation changes (only at beginning of new year)
                        if (current_allocation and allocation != current_allocation and 
                            date.dayofyear <= 5):  # Only count changes in first few days of year
                            allocation_changes += 1
                        current_allocation = allocation
                else:
                    continue
                
                # Calculate portfolio return for this day
                day_return = 0.0
                total_weight = 0.0
                
                for asset, weight in allocation.items():
                    if asset in returns_data and i-1 < len(returns_data[asset]):
                        try:
                            asset_return = returns_data[asset].iloc[i-1]
                            if not pd.isna(asset_return):
                                day_return += weight * asset_return
                                total_weight += weight
                        except (IndexError, KeyError):
                            continue
                
                # Normalize if weights don't sum to 1 (handle any rounding issues)
                if total_weight > 0 and abs(total_weight - 1.0) > 0.01:
                    day_return = day_return / total_weight
                
                portfolio_returns.append(day_return)
                current_value = portfolio_values[-1] * (1 + day_return)
                portfolio_values.append(current_value)
            
            # Calculate performance metrics
            if len(portfolio_returns) == 0:
                print("❌ No portfolio returns calculated")
                return None
            
            portfolio_returns = np.array(portfolio_returns)
            final_value = portfolio_values[-1]
            
            print(f"✅ Calculated {len(portfolio_returns)} portfolio returns")
            print(f"   Portfolio grew from ${self.initial_portfolio_value:,.0f} to ${final_value:,.0f}")
            
            # Basic metrics
            total_return = (final_value - self.initial_portfolio_value) / self.initial_portfolio_value
            years = len(portfolio_returns) / 252  # Assuming daily data
            annual_return = (1 + total_return) ** (1/years) - 1 if years > 0 else 0
            
            volatility = np.std(portfolio_returns) * np.sqrt(252) if len(portfolio_returns) > 1 else 0
            sharpe_ratio = annual_return / volatility if volatility > 0 else 0
            
            # Downside deviation for Sortino ratio
            downside_returns = portfolio_returns[portfolio_returns < 0]
            downside_deviation = np.std(downside_returns) * np.sqrt(252) if len(downside_returns) > 0 else 0
            sortino_ratio = annual_return / downside_deviation if downside_deviation > 0 else sharpe_ratio
            
            # Maximum drawdown
            cumulative_values = np.array(portfolio_values)
            running_max = np.maximum.accumulate(cumulative_values)
            drawdown = (cumulative_values - running_max) / running_max
            max_drawdown = abs(np.min(drawdown)) if len(drawdown) > 0 else 0
            
            # Calmar ratio
            calmar_ratio = annual_return / max_drawdown if max_drawdown > 0 else 0
            
            # Turnover approximation
            turnover = allocation_changes / years if years > 0 else 0
            
            result = PerformanceResult(
                strategy_name=allocation_strategy,
                total_return=total_return,
                annual_return=annual_return,
                volatility=volatility,
                sharpe_ratio=sharpe_ratio,
                sortino_ratio=sortino_ratio,
                max_drawdown=max_drawdown,
                calmar_ratio=calmar_ratio,
                turnover=turnover,
                num_rebalances=allocation_changes
            )
            
            print(f"✅ {allocation_strategy.upper()} STRATEGY RESULTS:")
            print(f"   Total Return: {result.total_return:.2%}")
            print(f"   Annual Return: {result.annual_return:.2%}")
            print(f"   Volatility: {result.volatility:.2%}")
            print(f"   Sharpe Ratio: {result.sharpe_ratio:.3f}")
            print(f"   Sortino Ratio: {result.sortino_ratio:.3f}")
            print(f"   Max Drawdown: {result.max_drawdown:.2%}")
            print(f"   Calmar Ratio: {result.calmar_ratio:.3f}")
            print(f"   Allocation Changes: {result.num_rebalances}")
            print(f"   Turnover: {result.turnover:.1f}/year")
            
            return result
            
        except Exception as e:
            print(f"❌ Error simulating {allocation_strategy} performance: {e}")
            import traceback
            traceback.print_exc()
            return None
