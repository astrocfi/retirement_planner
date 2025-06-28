# Simple Retirement Two Assets Example

This example demonstrates a retirement scenario with two asset types (stocks and bonds) and multiple asset performance scenarios to test the system's ability to handle different return assumptions.

## Portfolio Structure

- **Total Portfolio Value**: $1,000,000
- **Stocks**: $600,000 (60% allocation)
- **Bonds**: $400,000 (40% allocation)

## Asset Performance Scenarios

### 1. Baseline Scenario (`asset_performance_baseline.yaml`)
- **Stocks**: 7% expected return, 15% volatility
- **Bonds**: 4% expected return, 5% volatility
- **Correlation**: 0.0 (uncorrelated)

### 2. High Returns Scenario (`asset_performance_high_returns.yaml`)
- **Stocks**: 10% expected return, 18% volatility
- **Bonds**: 6% expected return, 6% volatility
- **Correlation**: 0.0 (uncorrelated)

### 3. Low Returns Scenario (`asset_performance_low_returns.yaml`)
- **Stocks**: 4% expected return, 12% volatility
- **Bonds**: 2% expected return, 4% volatility
- **Correlation**: 0.0 (uncorrelated)

### 4. Zero Returns Scenario (`asset_performance_zero_returns.yaml`)
- **Stocks**: 0% expected return, 0% volatility
- **Bonds**: 0% expected return, 0% volatility
- **Correlation**: 0.0 (uncorrelated)

### 5. Stocks Zero Returns (`asset_performance_stocks_zero.yaml`) - Debugging
- **Stocks**: 0% expected return, 0% volatility
- **Bonds**: 4% expected return, 5% volatility
- **Correlation**: 0.0 (uncorrelated)

### 6. Bonds Zero Returns (`asset_performance_bonds_zero.yaml`) - Debugging
- **Stocks**: 7% expected return, 15% volatility
- **Bonds**: 0% expected return, 0% volatility
- **Correlation**: 0.0 (uncorrelated)

## Running the Analysis

To run with a specific asset performance scenario:

```bash
# Baseline scenario
python -m retirement_planner.analysis.run_analysis analyze \
  --config examples/simple_retirement_two_assets/config.yaml \
  examples/simple_retirement_two_assets/asset_performance_baseline.yaml \
  --output-dir results_baseline

# High returns scenario
python -m retirement_planner.analysis.run_analysis analyze \
  --config examples/simple_retirement_two_assets/config.yaml \
  examples/simple_retirement_two_assets/asset_performance_high_returns.yaml \
  --output-dir results_high_returns

# Low returns scenario
python -m retirement_planner.analysis.run_analysis analyze \
  --config examples/simple_retirement_two_assets/config.yaml \
  examples/simple_retirement_two_assets/asset_performance_low_returns.yaml \
  --output-dir results_low_returns

# Zero returns scenario
python -m retirement_planner.analysis.run_analysis analyze \
  --config examples/simple_retirement_two_assets/config.yaml \
  examples/simple_retirement_two_assets/asset_performance_zero_returns.yaml \
  --output-dir results_zero_returns

# Stocks zero returns (debugging)
python -m retirement_planner.analysis.run_analysis analyze \
  --config examples/simple_retirement_two_assets/config.yaml \
  examples/simple_retirement_two_assets/asset_performance_stocks_zero.yaml \
  --output-dir results_stocks_zero

# Bonds zero returns (debugging)
python -m retirement_planner.analysis.run_analysis analyze \
  --config examples/simple_retirement_two_assets/config.yaml \
  examples/simple_retirement_two_assets/asset_performance_bonds_zero.yaml \
  --output-dir results_bonds_zero
```

## Expected Results

The analysis should show:

1. **Baseline**: Moderate success rate with typical market returns
2. **High Returns**: Higher success rate due to optimistic returns
3. **Low Returns**: Lower success rate due to conservative returns
4. **Zero Returns**: Very low success rate as portfolio only declines due to withdrawals
5. **Stocks Zero**: Success rate based only on bond returns (40% of portfolio)
6. **Bonds Zero**: Success rate based only on stock returns (60% of portfolio)

## Debugging Insights

The single-asset-zero scenarios help validate:
- Portfolio allocation is working correctly (60% stocks, 40% bonds)
- Each asset type contributes appropriately to overall returns
- The system properly handles mixed scenarios where one asset has returns and another doesn't
- Correlation matrices work correctly with partial zero returns

This validates that the system properly handles multiple asset types with different return characteristics and correlation structures.