import pytest
from retirement_planner.tax.state import StateTax, CaliforniaTax

class DummyTax(StateTax):
    def __init__(self):
        super().__init__(state_code="XX", state_name="DummyState")
    def calculate_income_tax(self, income: float, filing_status: str, **kwargs) -> float:
        return 0.0
    def calculate_capital_gains_tax(self, gains: float, long_term: bool = True, **kwargs) -> float:
        return 0.0
    def calculate_property_tax(self, property_value: float, **kwargs) -> float:
        return 0.0
    def calculate_sales_tax(self, amount: float, **kwargs) -> float:
        return 0.0
    def get_tax_brackets(self, year: int, filing_status: str):
        return []
    def get_deductions(self, year: int, filing_status: str):
        return {}

def test_state_tax_abstract_instantiation():
    with pytest.raises(TypeError):
        StateTax("XX", "DummyState")

def test_dummy_tax_methods():
    dummy = DummyTax()
    assert dummy.calculate_income_tax(100000, 'single') == 0.0
    assert dummy.calculate_capital_gains_tax(10000) == 0.0
    assert dummy.calculate_property_tax(500000) == 0.0
    assert dummy.calculate_sales_tax(1000) == 0.0
    assert dummy.get_tax_brackets(2024, 'single') == []
    assert dummy.get_deductions(2024, 'single') == {}

def test_california_income_tax_basic():
    ca = CaliforniaTax()
    # Test zero income
    assert ca.calculate_income_tax(0, 'single') == 0.0
    # Test below standard deduction
    assert ca.calculate_income_tax(5000, 'single') == 0.0  # Below $5,202 standard deduction
    # Test above standard deduction
    income = 10000  # Above standard deduction
    tax = ca.calculate_income_tax(income, 'single')
    # Taxable income = 10000 - 5202 = 4798
    # Tax = 4798 * 0.01 = 47.98
    expected_tax = (income - 5202) * 0.01
    assert tax == pytest.approx(expected_tax)
    # Test across multiple brackets
    income = 60000
    tax = ca.calculate_income_tax(income, 'single')
    # Manual calculation for 2024 brackets with standard deduction
    taxable_income = income - 5202  # Standard deduction
    brackets = ca.get_tax_brackets(2024, 'single')
    expected = 0.0
    remaining = taxable_income
    for b in brackets:
        lower, upper, rate = b['min'], b['max'], b['rate']
        if taxable_income > lower:
            taxable = min(remaining, upper - lower)
            expected += taxable * rate
            remaining -= taxable
            if remaining <= 0:
                break
    assert tax == pytest.approx(expected)

def test_california_capital_gains_tax():
    ca = CaliforniaTax()
    # Should be same as income tax
    gains = 20000
    assert ca.calculate_capital_gains_tax(gains, long_term=True, filing_status='single') == ca.calculate_income_tax(gains, 'single')

def test_california_property_tax():
    ca = CaliforniaTax()
    value = 1_000_000
    expected = value * (0.01 + 0.0025)
    assert ca.calculate_property_tax(value) == pytest.approx(expected)

def test_california_sales_tax():
    ca = CaliforniaTax()
    amount = 1000
    expected = amount * (0.0725 + 0.01)
    assert ca.calculate_sales_tax(amount) == pytest.approx(expected)

def test_california_get_tax_brackets_and_deductions():
    ca = CaliforniaTax()
    brackets = ca.get_tax_brackets(2024, 'single')
    assert isinstance(brackets, list)
    assert all('min' in b and 'max' in b and 'rate' in b for b in brackets)
    ded = ca.get_deductions(2024, 'single')
    assert 'standard_deduction' in ded
    # NotImplemented for other statuses
    with pytest.raises(NotImplementedError):
        ca.get_tax_brackets(2024, 'married')
    with pytest.raises(NotImplementedError):
        ca.get_deductions(2024, 'married')

def test_california_capital_gains_are_taxed_as_income():
    from retirement_planner.tax.state import CaliforniaTax
    tax = CaliforniaTax()
    filing_status = 'single'
    year = 2024

    # Case 1: Only regular income
    income = 40000
    cg = 0
    total = income + cg
    tax_income_only = tax.calculate_income_tax(income, filing_status, year=year)
    tax_total = tax.calculate_income_tax(total, filing_status, year=year)
    assert tax_income_only == tax_total

    # Case 2: Only capital gains
    income = 0
    cg = 40000
    total = income + cg
    tax_cg_only = tax.calculate_income_tax(cg, filing_status, year=year)
    tax_total = tax.calculate_income_tax(total, filing_status, year=year)
    assert tax_cg_only == tax_total

    # Case 3: Both income and capital gains
    income = 40000
    cg = 40000
    total = income + cg
    tax_both = tax.calculate_income_tax(total, filing_status, year=year)
    # The tax on the combined amount should be higher than on either alone
    assert tax_both > tax_income_only
    assert tax_both > tax_cg_only

    # Case 4: Proportional split for reporting (simulate what calculator does)
    cg = 20000
    income = 30000
    total = income + cg
    total_tax = tax.calculate_income_tax(total, filing_status, year=year)
    cg_prop = cg / total
    cg_tax = total_tax * cg_prop
    income_tax = total_tax - cg_tax
    # The sum should match the total
    assert abs((cg_tax + income_tax) - total_tax) < 1e-6