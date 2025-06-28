from abc import ABC, abstractmethod
from typing import Dict, List, Any

class StateTax(ABC):
    """
    Abstract base class for state tax calculations.
    """
    state_code: str
    state_name: str

    def __init__(self, state_code: str, state_name: str):
        self.state_code = state_code
        self.state_name = state_name

    @abstractmethod
    def calculate_income_tax(self, income: float, filing_status: str, **kwargs) -> float:
        pass

    @abstractmethod
    def calculate_capital_gains_tax(self, gains: float, long_term: bool = True, **kwargs) -> float:
        pass

    @abstractmethod
    def calculate_property_tax(self, property_value: float, **kwargs) -> float:
        pass

    @abstractmethod
    def calculate_sales_tax(self, amount: float, **kwargs) -> float:
        pass

    @abstractmethod
    def get_tax_brackets(self, year: int, filing_status: str) -> List[Dict[str, Any]]:
        pass

    @abstractmethod
    def get_deductions(self, year: int, filing_status: str) -> Dict[str, float]:
        pass

class CaliforniaTax(StateTax):
    """
    California-specific tax calculations.
    """
    def __init__(self):
        super().__init__(state_code="CA", state_name="California")

    def calculate_income_tax(self, income: float, filing_status: str, **kwargs) -> float:
        brackets = self.get_tax_brackets(year=kwargs.get('year', 2024), filing_status=filing_status)
        tax = 0.0
        remaining_income = income
        for bracket in brackets:
            lower = bracket['min']
            upper = bracket['max']
            rate = bracket['rate']
            if income > lower:
                taxable = min(remaining_income, upper - lower)
                tax += taxable * rate
                remaining_income -= taxable
                if remaining_income <= 0:
                    break
        return max(tax, 0.0)

    def calculate_capital_gains_tax(self, gains: float, long_term: bool = True, **kwargs) -> float:
        # CA taxes capital gains as regular income
        return self.calculate_income_tax(gains, kwargs.get('filing_status', 'single'), year=kwargs.get('year', 2024))

    def calculate_property_tax(self, property_value: float, **kwargs) -> float:
        # Prop 13: 1% base rate, plus local assessments (assume 0.25% extra)
        base_rate = 0.01
        local_rate = 0.0025
        return property_value * (base_rate + local_rate)

    def calculate_sales_tax(self, amount: float, **kwargs) -> float:
        # State base rate 7.25%, local rates vary (assume 1.0% extra)
        base_rate = 0.0725
        local_rate = 0.01
        return amount * (base_rate + local_rate)

    def get_tax_brackets(self, year: int, filing_status: str) -> List[Dict[str, Any]]:
        # 2024 CA brackets (simplified, single filer)
        # Real implementation would load from data
        if filing_status == 'single':
            return [
                {'min': 0, 'max': 10412, 'rate': 0.01},
                {'min': 10412, 'max': 24684, 'rate': 0.02},
                {'min': 24684, 'max': 38959, 'rate': 0.04},
                {'min': 38959, 'max': 54081, 'rate': 0.06},
                {'min': 54081, 'max': 68250, 'rate': 0.08},
                {'min': 68250, 'max': 349137, 'rate': 0.093},
                {'min': 349137, 'max': 418961, 'rate': 0.103},
                {'min': 418961, 'max': 698271, 'rate': 0.113},
                {'min': 698271, 'max': float('inf'), 'rate': 0.123},
            ]
        # Add other filing statuses as needed
        raise NotImplementedError(f"Brackets for filing status {filing_status} not implemented.")

    def get_deductions(self, year: int, filing_status: str) -> Dict[str, float]:
        # 2024 CA standard deduction (single)
        if filing_status == 'single':
            return {'standard_deduction': 5202.0}
        # Add other filing statuses as needed
        raise NotImplementedError(f"Deductions for filing status {filing_status} not implemented.")