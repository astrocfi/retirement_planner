from abc import ABC, abstractmethod
from typing import Dict, List, Any
import os
from retirement_planner.utils.file_utils import YamlLoader

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
    California-specific tax calculations loaded from configuration file.
    """

    def __init__(self, config_path: str = None):
        super().__init__(state_code="CA", state_name="California")
        if config_path is None:
            config_path = os.path.join(os.path.dirname(__file__), '../data/defaults/tax_data.yaml')
        self.config_path = os.path.abspath(config_path)
        self.tax_data = YamlLoader.load_yaml(self.config_path)

    def _get_california_config(self, year: int, filing_status: str) -> dict:
        data = self.tax_data.get('california_tax_brackets', {})
        if data.get('year') != year or data.get('filing_status') != filing_status:
            raise NotImplementedError(f"No CA config for year {year} and status {filing_status}")
        return data

    def calculate_income_tax(self, income: float, filing_status: str, **kwargs) -> float:
        config = self._get_california_config(kwargs.get('year', 2024), filing_status)
        brackets = config['brackets']
        standard_deduction = config.get('standard_deduction', 0.0)

        # Apply standard deduction to get taxable income
        taxable_income = max(0.0, income - standard_deduction)

        # If no taxable income after deduction, no tax
        if taxable_income <= 0:
            return 0.0

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
        return max(tax, 0.0)

    def calculate_capital_gains_tax(self, gains: float, long_term: bool = True, **kwargs) -> float:
        # CA taxes capital gains as regular income, so this method is deprecated
        # Capital gains should be included in total income for tax calculation
        # This method is kept for compatibility but should not be used directly
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
        config = self._get_california_config(year, filing_status)
        return config['brackets']

    def get_deductions(self, year: int, filing_status: str) -> Dict[str, float]:
        config = self._get_california_config(year, filing_status)
        return {'standard_deduction': config.get('standard_deduction', 0.0)}