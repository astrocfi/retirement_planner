#!/usr/bin/env python3
"""
Test script to verify standard deduction calculations.
"""

import sys
from pathlib import Path

# Add the project root to the path
sys.path.insert(0, str(Path(__file__).parent))

from retirement_planner.tax.federal import USFederalTax
from retirement_planner.tax.state import CaliforniaTax
from retirement_planner.utils.file_utils import YamlLoader
import os

def calc_ca_tax_from_yaml(taxable_income, brackets):
    tax = 0.0
    remaining_income = taxable_income
    for bracket in brackets:
        lower = bracket['min']
        upper = bracket['max'] if bracket['max'] is not None else float('inf')
        rate = bracket['rate']
        if taxable_income > lower:
            taxable = min(remaining_income, upper - lower)
            tax += taxable * rate
            remaining_income -= taxable
            if remaining_income <= 0:
                break
    return tax

def test_standard_deductions():
    """Test that standard deductions are being applied correctly."""
    print("Testing Standard Deduction Calculations")
    print("=" * 50)

    # Test federal taxes
    federal_tax = USFederalTax()

    # Test case 1: Income below standard deduction
    income = 10000  # Below $14,600 standard deduction
    tax = federal_tax.calculate_income_tax(income, "single")
    print(f"Federal tax on ${income:,} income: ${tax:.2f}")
    assert tax == 0.0, f"Expected $0 tax for income below standard deduction, got ${tax:.2f}"

    # Test case 2: Income just above standard deduction
    income = 20000  # $20,000 - $14,600 = $5,400 taxable
    tax = federal_tax.calculate_income_tax(income, "single")
    expected_tax = 5400 * 0.10  # First bracket rate
    print(f"Federal tax on ${income:,} income: ${tax:.2f} (expected: ${expected_tax:.2f})")
    assert abs(tax - expected_tax) < 0.01, f"Expected ${expected_tax:.2f}, got ${tax:.2f}"

    # Test case 3: Income in second bracket
    income = 50000  # $50,000 - $14,600 = $35,400 taxable
    tax = federal_tax.calculate_income_tax(income, "single")
    expected_tax = 11600 * 0.10 + (35400 - 11600) * 0.12
    print(f"Federal tax on ${income:,} income: ${tax:.2f} (expected: ${expected_tax:.2f})")
    assert abs(tax - expected_tax) < 0.01, f"Expected ${expected_tax:.2f}, got ${tax:.2f}"

    # Test California state taxes
    ca_tax = CaliforniaTax()
    # Load CA brackets from YAML
    config_path = os.path.join(os.path.dirname(__file__), 'retirement_planner/data/defaults/tax_data.yaml')
    tax_data = YamlLoader.load_yaml(config_path)
    ca_config = tax_data['california_tax_brackets']
    ca_brackets = ca_config['brackets']
    ca_std_ded = ca_config['standard_deduction']

    # Test case 1: Income below CA standard deduction
    income = 3000  # Below $5,202 standard deduction
    tax = ca_tax.calculate_income_tax(income, "single")
    print(f"CA tax on ${income:,} income: ${tax:.2f}")
    assert tax == 0.0, f"Expected $0 tax for income below CA standard deduction, got ${tax:.2f}"

    # Test case 2: Income just above CA standard deduction
    income = 10000  # $10,000 - $5,202 = $4,798 taxable
    tax = ca_tax.calculate_income_tax(income, "single")
    expected_tax = calc_ca_tax_from_yaml(10000 - ca_std_ded, ca_brackets)
    print(f"CA tax on ${income:,} income: ${tax:.2f} (expected: ${expected_tax:.2f})")
    assert abs(tax - expected_tax) < 0.01, f"Expected ${expected_tax:.2f}, got ${tax:.2f}"

    # Test case 3: Income in second bracket
    income = 30000  # $30,000 - $5,202 = $24,798 taxable
    tax = ca_tax.calculate_income_tax(income, "single")
    expected_tax = calc_ca_tax_from_yaml(30000 - ca_std_ded, ca_brackets)
    print(f"CA tax on ${income:,} income: ${tax:.2f} (expected: ${expected_tax:.2f})")
    assert abs(tax - expected_tax) < 0.01, f"Expected ${expected_tax:.2f}, got ${tax:.2f}"

    print("\n✅ All standard deduction tests passed!")
    print("\nKey improvements:")
    print("- Federal standard deduction: $14,600 (2024)")
    print("- California standard deduction: $5,202 (2024)")
    print("- Tax calculations now properly apply deductions before computing tax")
    print("- Much more realistic tax burdens for retirees")

if __name__ == "__main__":
    test_standard_deductions()