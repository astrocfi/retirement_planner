# 50-Year-Old Retirement Scenario Example

## Scenario Overview

This example demonstrates a retirement planning scenario for a 50-year-old woman with the following profile:

### Personal Information
- **Age**: 50 years old
- **Current Income**: $100,000/year
- **Current Savings**: $1,000,000 (60% stocks, 40% bonds)
- **Annual 401(k) Contribution**: $20,000
- **Planned Retirement Age**: 67
- **Life Expectancy**: 95 years

### Financial Profile
- **Risk Tolerance**: Moderate
- **Tax Filing Status**: Single
- **State of Residence**: California

### Income Sources
- **Employment Income**: $100,000/year until age 67
- **Social Security**: Starting at age 67 (estimated $35,000/year)

### Expenses
- **Working Years (50-67)**: $80,000/year
- **Early Retirement (67-85)**: $80,000/year
- **Late Retirement (85-95)**: $60,000/year (reduced expenses)

### Goals
- **Primary Goal**: Ensure savings last until death at age 95
- **Secondary Goal**: Maintain $80,000/year lifestyle until age 85

## Analysis Question

**What is the probability that the savings will last until death at age 95?**

## Configuration Files

This example uses the following configuration files:

1. **person_profile.yaml** - Personal and financial profile
2. **events.yaml** - Income and expense events over time
3. **market_data.yaml** - Asset allocation and market assumptions
4. **simulation_config.yaml** - Monte Carlo simulation parameters

## Testing

The example includes tests to verify configuration validity:

```bash
# Run the events configuration test
cd tests
python test_events.py
```

The test validates:
- No overlapping event periods of the same type
- Complete expense coverage across all ages
- Proper event configuration structure

## Usage

### Using the Global Analysis Tool

The retirement planner provides a global analysis tool that can be used with any scenario:

```bash
# Using the Python module directly
python -m retirement_planner.analysis.run_analysis \
    --person-profile person_profile.yaml \
    --events events.yaml \
    --market-data market_data.yaml \
    --simulation-config simulation_config.yaml \
    --output-dir results/
```

### Running from the Example Directory

```bash
# Navigate to the example directory
cd examples/50_year_old_retirement_scenario

# Run analysis using relative paths
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
- **Investment Returns**: 7% average (stocks), 3% average (bonds)
- **Social Security**: COLA-adjusted benefits
- **Tax Rates**: Current federal and California rates
- **Market Volatility**: Historical levels for 60/40 portfolio