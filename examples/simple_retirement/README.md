# Simple Retirement Example

## Scenario Overview

This example demonstrates a basic retirement planning scenario for a 65-year-old retiree with a simple portfolio.

### Personal Information
- **Age**: 65 years old (already retired)
- **Current Savings**: $1,000,000 (100% stocks)
- **Life Expectancy**: 95 years

### Financial Profile
- **Risk Tolerance**: Moderate
- **Tax Filing Status**: Single
- **State of Residence**: California

### Portfolio
- **Asset Allocation**: 100% stocks
- **Expected Return**: 7% annually
- **Volatility**: 12% annually

### Goals
- **Primary Goal**: Ensure savings last until death at age 95

## Analysis Question

**What is the probability that the savings will last until death at age 95?**

## Configuration Files

This example uses the unified configuration format:

### New Unified Format (Recommended)
- **unified_config.yaml** - Complete configuration in single file

### Legacy Separate Files (Deprecated)
- **person_profile.yaml** - Personal and financial profile
- **events.yaml** - Income and expense events over time
- **market_data.yaml** - Asset allocation and market assumptions
- **simulation_config.yaml** - Monte Carlo simulation parameters

## Usage

### Using the Unified Configuration (Recommended)

```bash
# Using the unified configuration file
python -m retirement_planner.analysis.run_analysis validate --config examples/simple_retirement/unified_config.yaml

# Run full analysis with unified config
python -m retirement_planner.analysis.run_analysis run_analysis --config examples/simple_retirement/unified_config.yaml --output-dir results/
```

### Using Multiple Configuration Files

```bash
# Combine multiple config files (later files override earlier ones)
python -m retirement_planner.analysis.run_analysis validate \
    --config examples/simple_retirement/unified_config.yaml \
    examples/complicated/unified_config.yaml
```

### Legacy Usage (Deprecated)

```bash
# Using the Python module directly with separate files
python -m retirement_planner.analysis.run_analysis \
    --person-profile person_profile.yaml \
    --events events.yaml \
    --market-data market_data.yaml \
    --simulation-config simulation_config.yaml \
    --output-dir results/
```

## Expected Output

The analysis will generate:
- Probability of success (savings lasting until age 95)
- Monte Carlo simulation results
- Cash flow projections
- Risk analysis
- Recommendations for adjustments

## Key Assumptions

- **Inflation Rate**: 2.5% annually
- **Investment Returns**: 7% average (stocks)
- **Market Volatility**: 12% annually
- **Time Horizon**: 30 years (65 to 95)

## Simple vs Complex Examples

This simple example demonstrates:
- **Basic portfolio**: Single asset type
- **Minimal configuration**: Essential parameters only
- **Easy to understand**: Good starting point for learning

For more complex scenarios, see:
- **50_year_old_retirement_scenario**: Moderate complexity with diverse assets
- **complicated**: High complexity with advanced features

## Migration to Unified Format

The unified configuration format provides several advantages:
- **Single file**: All configuration in one place
- **Section-based**: Clear organization with person, assets, asset_performance, events, simulation, economy sections
- **Asset separation**: Simple asset list with detailed performance data
- **Multiple file support**: Later files override earlier ones
- **Better validation**: Comprehensive validation across all sections