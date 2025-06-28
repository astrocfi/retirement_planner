# Complicated Retirement Planning Examples

This directory contains complex retirement planning scenarios using the unified configuration format.

## Unified Configuration Format

The unified configuration format combines all retirement planning parameters into a single YAML file with the following sections:

### Person Section
- Basic personal information (name, age, retirement age, life expectancy)
- Risk tolerance and tax filing status
- Financial goals with priorities and target amounts

### Assets Section
- Simplified asset list with only type and current value
- Each asset references detailed performance data in the asset_performance section
- Supports all asset types: equity, bond, cash, real_estate, commodity, custom

### Asset Performance Section
- Detailed characteristics for each asset
- Expected returns, volatility, correlations
- Asset-specific metadata (dividend yields, credit ratings, etc.)
- Referenced by asset name from the assets section

### Events Section
- Income, expense, asset, liability, and benefit events
- Age-based event scheduling
- Probability and inflation adjustment settings

### Simulation Section
- Monte Carlo simulation parameters
- Market scenario generation settings
- Portfolio management and risk management rules
- Success criteria and output configuration

### Economy Section
- Inflation assumptions and modeling
- Risk-free rate data
- Market regime definitions
- Data source specifications

## Files

- `unified_config.yaml` - Complex 50-year-old retirement scenario with diverse asset allocation

## Usage

```bash
# Run analysis with unified config
python -m retirement_planner.analysis.run_analysis validate --config examples/complicated/unified_config.yaml

# Run analysis with multiple config files (later files override earlier ones)
python -m retirement_planner.analysis.run_analysis validate --config examples/simple_retirement/unified_config.yaml examples/complicated/unified_config.yaml
```

## Key Features

- **Section-based organization**: Clear separation of concerns
- **Asset/performance separation**: Simple asset list with detailed performance data
- **Multiple file support**: Later files override earlier ones
- **Comprehensive coverage**: All retirement planning aspects in one format
- **Extensible design**: Easy to add new sections or modify existing ones