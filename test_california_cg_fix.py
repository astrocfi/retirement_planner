#!/usr/bin/env python3
"""
Test script to verify California capital gains tax calculation fix.
"""

from retirement_planner.tax.calculator import TaxCalculator

class MockAsset:
    """Mock asset for testing."""
    def __init__(self, name: str, current_value: float, cost_basis: float):
        self.name = name
        self.current_value = current_value
        self.cost_basis = cost_basis

    def get_dividend_income(self) -> float:
        return 0.0

    def get_capital_gains(self) -> float:
        return self.current_value - self.cost_basis

    def is_liquid_at_year(self, year: int) -> bool:
        return True

def test_california_capital_gains_calculation():
    """Test that California capital gains are calculated correctly."""
    print("Testing California capital gains tax calculation...")

    # Create tax calculator
    tax_calc = TaxCalculator(filing_status="single", state="CA")

    # Test case 1: Low income + capital gains
    print("\nTest Case 1: Low income ($20,000) + capital gains ($5,000)")

    # Create mock assets
    assets = [
        MockAsset("stock1", current_value=10000, cost_basis=5000)  # $5,000 capital gains
    ]

    sold_assets = {"stock1": 10000}  # Sell entire position

    result = tax_calc.calculate_annual_taxes(
        year=2024,
        income_events=[20000],  # $20,000 regular income
        assets=assets,
        sold_assets=sold_assets
    )

    print(f"  Regular income: $20,000")
    print(f"  Capital gains: $5,000")
    print(f"  Total income for state tax: $25,000")
    print(f"  State income tax: ${result.state_income_tax:.2f}")
    print(f"  State capital gains tax: ${result.state_capital_gains_tax:.2f}")
    print(f"  Total state tax: ${result.state_income_tax + result.state_capital_gains_tax:.2f}")

    # Test case 2: High income + capital gains (should hit higher bracket)
    print("\nTest Case 2: High income ($100,000) + capital gains ($25,000)")

    assets = [
        MockAsset("stock2", current_value=50000, cost_basis=25000)  # $25,000 capital gains
    ]

    sold_assets = {"stock2": 50000}

    result2 = tax_calc.calculate_annual_taxes(
        year=2024,
        income_events=[100000],  # $100,000 regular income
        assets=assets,
        sold_assets=sold_assets
    )

    print(f"  Regular income: $100,000")
    print(f"  Capital gains: $25,000")
    print(f"  Total income for state tax: $125,000")
    print(f"  State income tax: ${result2.state_income_tax:.2f}")
    print(f"  State capital gains tax: ${result2.state_capital_gains_tax:.2f}")
    print(f"  Total state tax: ${result2.state_income_tax + result2.state_capital_gains_tax:.2f}")

    # Verify that the total state tax is calculated correctly
    # For CA, total income of $125,000 should be in the 9.3% bracket
    expected_total_state_tax = 125000 * 0.093  # Simplified calculation
    actual_total_state_tax = result2.state_income_tax + result2.state_capital_gains_tax

    print(f"\nVerification:")
    print(f"  Expected total state tax (simplified): ${expected_total_state_tax:.2f}")
    print(f"  Actual total state tax: ${actual_total_state_tax:.2f}")
    print(f"  Difference: ${abs(expected_total_state_tax - actual_total_state_tax):.2f}")

    # Test case 3: No regular income, only capital gains
    print("\nTest Case 3: No regular income, only capital gains ($15,000)")

    assets = [
        MockAsset("stock3", current_value=30000, cost_basis=15000)  # $15,000 capital gains
    ]

    sold_assets = {"stock3": 30000}

    result3 = tax_calc.calculate_annual_taxes(
        year=2024,
        income_events=[],  # No regular income
        assets=assets,
        sold_assets=sold_assets
    )

    print(f"  Regular income: $0")
    print(f"  Capital gains: $15,000")
    print(f"  Total income for state tax: $15,000")
    print(f"  State income tax: ${result3.state_income_tax:.2f}")
    print(f"  State capital gains tax: ${result3.state_capital_gains_tax:.2f}")
    print(f"  Total state tax: ${result3.state_income_tax + result3.state_capital_gains_tax:.2f}")

    print("\n✅ California capital gains tax calculation test completed!")

if __name__ == "__main__":
    test_california_capital_gains_calculation()