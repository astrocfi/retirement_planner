# Retirement Planner Examples

This directory contains example retirement planning scenarios demonstrating different levels of complexity and the unified configuration format.

## Directory Structure

### Simple Examples
- **simple_retirement/** - Basic retirement scenario for a 65-year-old retiree
  - Single asset type (100% stocks)
  - Minimal configuration
  - Good starting point for learning

### Moderate Complexity
- **50_year_old_retirement_scenario/** - Comprehensive scenario for a 50-year-old planning retirement
  - Diverse asset allocation (stocks, bonds, cash, alternatives)
  - Multiple financial goals
  - Detailed simulation parameters

### High Complexity
- **complicated/** - Advanced scenarios with sophisticated features
  - Complex asset allocations
  - Advanced simulation settings
  - Comprehensive event modeling

## Configuration Format Evolution

### New Unified Format (Recommended)
All examples now support the unified configuration format that combines all retirement planning parameters into a single YAML file with the following sections:

- **person** - Personal information, goals, and preferences
- **assets** - Simplified asset list (type and current value only)
- **asset_performance** - Detailed asset characteristics and performance data
- **events** - Income, expense, asset, liability, and benefit events
- **simulation** - Monte Carlo simulation parameters
- **economy** - Inflation, risk-free rates, and market regime assumptions

### Legacy Format (Deprecated)
The old format used separate files:
- `person_profile.yaml`
- `assets.yaml`
- `market_data.yaml`
- `simulation_config.yaml`
- `events.yaml`

## Usage Examples

### Basic Validation
```bash
# Validate a single configuration file
python -m retirement_planner.analysis.run_analysis validate --config examples/simple_retirement/unified_config.yaml

# Validate multiple configuration files (later files override earlier ones)
python -m retirement_planner.analysis.run_analysis validate \
    --config examples/simple_retirement/unified_config.yaml \
    examples/complicated/unified_config.yaml
```

### Full Analysis
```bash
# Run complete analysis with unified config
python -m retirement_planner.analysis.run_analysis run_analysis \
    --config examples/50_year_old_retirement_scenario/unified_config.yaml \
    --output-dir results/
```

## Key Features

### Unified Configuration Benefits
- **Single file**: All configuration in one place
- **Section-based**: Clear organization and separation of concerns
- **Asset separation**: Simple asset list with detailed performance data
- **Multiple file support**: Later files override earlier ones
- **Better validation**: Comprehensive validation across all sections
- **Backward compatibility**: Still supports legacy separate file format

### Asset Structure
The new format separates asset definition from performance characteristics:

```yaml
# Assets section (simple)
assets:
  - name: "S&P 500 ETF"
    asset_type: "equity"
    current_value: 600000.0
    notes: "Large cap domestic equity exposure"

# Asset performance section (detailed)
asset_performance:
  "S&P 500 ETF":
    expected_return: 0.07
    volatility: 0.18
    dividend_yield: 0.015
    beta: 1.0
    # ... other characteristics
```

### Multiple File Support
You can combine multiple configuration files for different scenarios:

```bash
# Base configuration
python -m retirement_planner.analysis.run_analysis validate \
    --config examples/simple_retirement/unified_config.yaml

# Base + Override configuration
python -m retirement_planner.analysis.run_analysis validate \
    --config examples/simple_retirement/unified_config.yaml \
    examples/complicated/unified_config.yaml
```

## Migration Guide

### From Legacy to Unified Format

1. **Combine files**: Merge all separate YAML files into a single `unified_config.yaml`
2. **Organize sections**: Use the section headers (person, assets, asset_performance, events, simulation, economy)
3. **Update asset format**: Change from `type` field to `name` and `asset_type` fields
4. **Update asset_performance**: Change from list to dictionary with asset names as keys
5. **Test validation**: Use the validate command to ensure proper format

### Example Migration
```yaml
# Old format (assets.yaml)
assets:
  - type: sp500_etf
    current_value: 600000

# New format (unified_config.yaml)
assets:
  - name: "S&P 500 ETF"
    asset_type: "equity"
    current_value: 600000.0
    notes: "Large cap domestic equity exposure"

asset_performance:
  "S&P 500 ETF":
    expected_return: 0.07
    volatility: 0.18
    # ... other characteristics
```

## Testing

Each example directory includes tests to verify configuration validity:

```bash
# Run example-specific tests
cd examples/50_year_old_retirement_scenario/tests
python test_events.py
```

## Next Steps

1. **Start simple**: Begin with the simple_retirement example
2. **Explore complexity**: Move to 50_year_old_retirement_scenario for more features
3. **Advanced scenarios**: Use the complicated examples for sophisticated modeling
4. **Custom scenarios**: Create your own unified configuration files
5. **Multiple files**: Combine base and override configurations for different scenarios