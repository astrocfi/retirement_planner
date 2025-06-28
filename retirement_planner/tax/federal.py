from abc import ABC, abstractmethod
from typing import Dict, List, Any, Optional
from dataclasses import dataclass
from datetime import date
from retirement_planner.utils.file_utils import YamlLoader
import os

@dataclass(frozen=True)
class SocialSecurityBenefit:
    """Social Security benefit information."""
    primary_insurance_amount: float
    benefit_at_full_retirement: float
    benefit_at_current_age: float
    reduction_factor: float
    delayed_credit_factor: float

class FederalTax(ABC):
    """
    Abstract base class for federal tax calculations.
    """

    def __init__(self):
        self.tax_year = 2024

    @abstractmethod
    def calculate_income_tax(self, income: float, filing_status: str, **kwargs) -> float:
        """Calculate federal income tax."""
        pass

    @abstractmethod
    def calculate_capital_gains_tax(self, gains: float, long_term: bool = True, **kwargs) -> float:
        """Calculate federal capital gains tax."""
        pass

    @abstractmethod
    def get_tax_brackets(self, year: int, filing_status: str) -> List[Dict[str, Any]]:
        """Get federal tax brackets."""
        pass

    @abstractmethod
    def get_deductions(self, year: int, filing_status: str) -> Dict[str, float]:
        """Get federal deductions."""
        pass

class USFederalTax(FederalTax):
    """
    US Federal tax calculations loaded from configuration file.
    """

    def __init__(self, config_path: str = None):
        super().__init__()
        if config_path is None:
            config_path = os.path.join(os.path.dirname(__file__), '../data/defaults/tax_data.yaml')
        self.config_path = os.path.abspath(config_path)
        self.tax_data = YamlLoader.load_yaml(self.config_path)

    def _get_federal_config(self, year: int, filing_status: str) -> dict:
        data = self.tax_data.get('federal_tax_brackets', {})
        if data.get('year') != year or data.get('filing_status') != filing_status:
            raise NotImplementedError(f"No config for year {year} and status {filing_status}")
        return data

    def calculate_income_tax(self, income: float, filing_status: str, **kwargs) -> float:
        config = self._get_federal_config(self.tax_year, filing_status)
        brackets = config['brackets']
        tax = 0.0
        remaining_income = income
        for bracket in brackets:
            lower = bracket['bracket_min']
            upper = bracket['bracket_max'] if bracket['bracket_max'] is not None else float('inf')
            rate = bracket['rate']
            if income > lower:
                taxable = min(remaining_income, upper - lower)
                tax += taxable * rate
                remaining_income -= taxable
                if remaining_income <= 0:
                    break
        return max(tax, 0.0)

    def calculate_capital_gains_tax(self, gains: float, long_term: bool = True, **kwargs) -> float:
        # For now, use config-driven long-term rate and threshold
        capital_gains = self.tax_data.get('capital_gains', {})
        filing_status = kwargs.get('filing_status', 'single')
        if not long_term:
            return self.calculate_income_tax(gains, filing_status)
        threshold = capital_gains.get('long_term_threshold', 47025.0)
        long_term_rate = capital_gains.get('long_term_rate', 0.15)
        if gains <= threshold:
            return 0.0
        return gains * long_term_rate

    def get_tax_brackets(self, year: int, filing_status: str) -> list:
        config = self._get_federal_config(year, filing_status)
        return config['brackets']

    def get_deductions(self, year: int, filing_status: str) -> dict:
        config = self._get_federal_config(year, filing_status)
        return {'standard_deduction': config.get('standard_deduction', 0.0)}

class SocialSecurity:
    """
    Social Security benefit calculations.
    """

    def __init__(self):
        self.full_retirement_age = 67  # For those born 1960 or later
        self.earliest_claiming_age = 62
        self.latest_claiming_age = 70

    def calculate_primary_insurance_amount(self, average_indexed_monthly_earnings: float) -> float:
        """Calculate Primary Insurance Amount (PIA)."""
        # 2024 bend points
        bend_point_1 = 1174
        bend_point_2 = 7078

        if average_indexed_monthly_earnings <= bend_point_1:
            pia = average_indexed_monthly_earnings * 0.90
        elif average_indexed_monthly_earnings <= bend_point_2:
            pia = (bend_point_1 * 0.90) + ((average_indexed_monthly_earnings - bend_point_1) * 0.32)
        else:
            pia = (bend_point_1 * 0.90) + ((bend_point_2 - bend_point_1) * 0.32) + ((average_indexed_monthly_earnings - bend_point_2) * 0.15)

        return round(pia, 2)

    def calculate_benefit_at_age(self, primary_insurance_amount: float, claiming_age: int) -> float:
        """Calculate benefit at specific claiming age."""
        if claiming_age < self.earliest_claiming_age:
            return 0.0
        elif claiming_age > self.latest_claiming_age:
            claiming_age = self.latest_claiming_age

        if claiming_age == self.full_retirement_age:
            return primary_insurance_amount
        elif claiming_age < self.full_retirement_age:
            # Early retirement reduction
            months_early = (self.full_retirement_age - claiming_age) * 12
            reduction_factor = 1 - (months_early * 0.00556)  # 5/9 of 1% for first 36 months
            if months_early > 36:
                additional_months = months_early - 36
                reduction_factor -= (additional_months * 0.00417)  # 5/12 of 1% for additional months
            return primary_insurance_amount * max(reduction_factor, 0.70)  # Minimum 70%
        else:
            # Delayed retirement credits
            months_delayed = (claiming_age - self.full_retirement_age) * 12
            credit_factor = 1 + (months_delayed * 0.00667)  # 8% per year = 2/3% per month
            return primary_insurance_amount * min(credit_factor, 1.32)  # Maximum 132%

    def calculate_medicare_premiums(self, income: float, filing_status: str) -> Dict[str, float]:
        """Calculate Medicare Part B and D premiums."""
        # 2024 Medicare Part B base premium
        base_premium = 174.70

        # Income-related monthly adjustment amounts (IRMAA)
        if filing_status == 'single':
            if income <= 103000:
                adjustment = 0
            elif income <= 129000:
                adjustment = 69.90
            elif income <= 161000:
                adjustment = 174.70
            elif income <= 193000:
                adjustment = 279.50
            elif income <= 500000:
                adjustment = 384.30
            else:
                adjustment = 419.30
        else:
            # Simplified for other filing statuses
            adjustment = 0

        part_b_premium = base_premium + adjustment
        part_d_premium = 34.70  # Base Part D premium (varies by plan)

        return {
            'part_b_premium': part_b_premium,
            'part_d_premium': part_d_premium,
            'total_medicare_premium': part_b_premium + part_d_premium
        }

class RetirementAccountTax:
    """
    Retirement account tax calculations and rules.
    """

    def __init__(self):
        self.current_year = 2024

    def calculate_rmd(self, account_balance: float, age: int, account_type: str = 'traditional_ira') -> float:
        """Calculate Required Minimum Distribution (RMD)."""
        if age < 73:  # RMD age is 73 for those born 1951-1959, 75 for 1960+
            return 0.0

        # Simplified RMD calculation using uniform lifetime table
        # For age 73, distribution period is 26.5 years
        distribution_periods = {
            73: 26.5, 74: 25.5, 75: 24.6, 76: 23.7, 77: 22.9,
            78: 22.0, 79: 21.1, 80: 20.2, 81: 19.3, 82: 18.4,
            83: 17.5, 84: 16.6, 85: 15.7, 86: 14.8, 87: 13.9,
            88: 13.0, 89: 12.1, 90: 11.2, 91: 10.3, 92: 9.4,
            93: 8.5, 94: 7.6, 95: 6.7, 96: 5.8, 97: 4.9,
            98: 4.0, 99: 3.1, 100: 2.2, 101: 1.3, 102: 0.4
        }

        if age > 102:
            return account_balance  # Must withdraw entire balance

        distribution_period = distribution_periods.get(age, 1.0)
        return account_balance / distribution_period

    def calculate_contribution_limit(self, age: int, account_type: str, income: float = 0) -> float:
        """Calculate contribution limits for retirement accounts."""
        if account_type == 'traditional_ira':
            if age < 50:
                return 7000  # 2024 limit
            else:
                return 8000  # 2024 catch-up contribution
        elif account_type == 'roth_ira':
            if age < 50:
                return 7000  # 2024 limit
            else:
                return 8000  # 2024 catch-up contribution
        elif account_type == '401k':
            if age < 50:
                return 23000  # 2024 limit
            else:
                return 30500  # 2024 catch-up contribution
        else:
            return 0.0

    def is_roth_eligible(self, income: float, filing_status: str) -> bool:
        """Check if Roth IRA contribution is eligible based on income."""
        if filing_status == 'single':
            if income <= 146000:
                return True
            elif income <= 161000:
                return False  # Partial phase-out
            else:
                return False  # Not eligible
        else:
            # Simplified for other filing statuses
            return income <= 146000

    def calculate_tax_deduction(self, contribution: float, income: float, filing_status: str,
                               account_type: str, has_employer_plan: bool = False) -> float:
        """Calculate tax deduction for traditional IRA contribution."""
        if account_type != 'traditional_ira':
            return 0.0

        if not has_employer_plan:
            return contribution  # Full deduction if no employer plan

        # Phase-out rules for traditional IRA when covered by employer plan
        if filing_status == 'single':
            if income <= 73000:
                return contribution  # Full deduction
            elif income <= 83000:
                # Partial phase-out
                phase_out_range = 10000
                phase_out_amount = (income - 73000) / phase_out_range
                return contribution * (1 - phase_out_amount)
            else:
                return 0.0  # No deduction
        else:
            # Simplified for other filing statuses
            return 0.0