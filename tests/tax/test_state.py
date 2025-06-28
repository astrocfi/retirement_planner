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
    # Test below first bracket
    assert ca.calculate_income_tax(5000, 'single') == pytest.approx(5000 * 0.01)
    # Test across multiple brackets
    income = 60000
    tax = ca.calculate_income_tax(income, 'single')
    # Manual calculation for 2024 brackets
    brackets = ca.get_tax_brackets(2024, 'single')
    expected = 0.0
    remaining = income
    for b in brackets:
        lower, upper, rate = b['min'], b['max'], b['rate']
        if income > lower:
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