"""
Tax data loading and management for retirement planning.

This module provides functionality to load and manage tax brackets, rates,
limits, and Social Security parameters needed for tax calculations.
"""

import numpy as np
import pandas as pd
from datetime import date, datetime
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple, Union, Any
from pathlib import Path
import json
import yaml
import warnings
import re

# Optional imports for web scraping
try:
    import requests
except ImportError:
    requests = None
    warnings.warn("requests not available. Web download methods will not work.")

try:
    from bs4 import BeautifulSoup
except ImportError:
    BeautifulSoup = None
    warnings.warn("beautifulsoup4 not available. Web scraping methods will not work.")

from ..core.exceptions import DataError
from ..core.validation import Validator, RequiredRule, TypeRule, RangeRule
from ..utils.math_utils import MathUtils


class TaxDataError(DataError):
    """Exception raised for tax data related errors."""
    pass


@dataclass(frozen=True)
class TaxBracket:
    """Individual tax bracket with rate and income range."""

    min: float
    max: Optional[float]
    rate: float
    filing_status: str

    def __post_init__(self):
        """Validate the tax bracket."""
        validator = Validator()

        # Add field validators
        validator.add_field_validator("min").add_rule(RequiredRule("min")).add_rule(RangeRule("min", 0.0))
        validator.add_field_validator("rate").add_rule(RequiredRule("rate")).add_rule(RangeRule("rate", 0.0, 1.0))
        validator.add_field_validator("filing_status").add_rule(RequiredRule("filing_status")).add_rule(TypeRule("filing_status", str))

        # Validate the data
        data = {
            "min": self.min,
            "rate": self.rate,
            "filing_status": self.filing_status
        }

        result = validator.validate(data)
        if not result.is_valid:
            raise TaxDataError(f"Invalid tax bracket: {[e.message for e in result.errors]}")

        # Validate bracket range
        if self.max is not None and self.min >= self.max:
            raise TaxDataError("Bracket minimum must be less than bracket maximum")

    def contains_income(self, income: float) -> bool:
        """Check if income falls within this bracket."""
        if income < self.min:
            return False
        if self.max is None:
            return True
        return income <= self.max

    def calculate_tax(self, income: float) -> float:
        """Calculate tax for income in this bracket."""
        if not self.contains_income(income):
            return 0.0

        taxable_amount = income - self.min
        return taxable_amount * self.rate

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "min": self.min,
            "max": self.max,
            "rate": self.rate,
            "filing_status": self.filing_status
        }


@dataclass(frozen=True)
class TaxBrackets:
    """Complete set of tax brackets for a filing status and year."""

    year: int
    brackets: List[TaxBracket]
    filing_status: str
    standard_deduction: float
    personal_exemption: float = 0.0

    def __post_init__(self):
        """Validate the tax brackets."""
        validator = Validator()

        # Add field validators
        validator.add_field_validator("year").add_rule(RequiredRule("year")).add_rule(RangeRule("year", 1900, 2100))
        validator.add_field_validator("brackets").add_rule(RequiredRule("brackets")).add_rule(TypeRule("brackets", list))
        validator.add_field_validator("filing_status").add_rule(RequiredRule("filing_status")).add_rule(TypeRule("filing_status", str))
        validator.add_field_validator("standard_deduction").add_rule(RequiredRule("standard_deduction")).add_rule(RangeRule("standard_deduction", 0.0))
        validator.add_field_validator("personal_exemption").add_rule(RangeRule("personal_exemption", 0.0))

        # Validate the data
        data = {
            "year": self.year,
            "brackets": self.brackets,
            "filing_status": self.filing_status,
            "standard_deduction": self.standard_deduction,
            "personal_exemption": self.personal_exemption
        }

        result = validator.validate(data)
        if not result.is_valid:
            raise TaxDataError(f"Invalid tax brackets: {[e.message for e in result.errors]}")

        # Validate bracket consistency
        if len(self.brackets) == 0:
            raise TaxDataError("No tax brackets provided")

        # Check that brackets are consecutive
        for i in range(len(self.brackets) - 1):
            if self.brackets[i].max != self.brackets[i + 1].min:
                raise TaxDataError("Tax brackets must be consecutive")

        # Check that all brackets have same filing status
        for bracket in self.brackets:
            if bracket.filing_status != self.filing_status:
                raise TaxDataError("All brackets must have same filing status")

    def get_bracket_for_income(self, income: float) -> TaxBracket:
        """Get the tax bracket for a given income level."""
        for bracket in self.brackets:
            if bracket.contains_income(income):
                return bracket
        raise TaxDataError(f"No bracket found for income: {income}")

    def calculate_total_tax(self, income: float) -> float:
        """Calculate total tax for given income."""
        if income <= 0:
            return 0.0

        total_tax = 0.0
        remaining_income = income

        for bracket in self.brackets:
            if remaining_income <= 0:
                break

            if bracket.max is None:
                # Top bracket
                taxable_amount = remaining_income
                total_tax += taxable_amount * bracket.rate
                break
            else:
                # Regular bracket
                bracket_income = min(remaining_income, bracket.max - bracket.min)
                total_tax += bracket_income * bracket.rate
                remaining_income -= bracket_income

        return total_tax

    def get_marginal_rate(self, income: float) -> float:
        """Get marginal tax rate for given income."""
        bracket = self.get_bracket_for_income(income)
        return bracket.rate

    def get_effective_rate(self, income: float) -> float:
        """Get effective tax rate for given income."""
        if income <= 0:
            return 0.0

        total_tax = self.calculate_total_tax(income)
        return total_tax / income

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "year": self.year,
            "brackets": [bracket.to_dict() for bracket in self.brackets],
            "filing_status": self.filing_status,
            "standard_deduction": self.standard_deduction,
            "personal_exemption": self.personal_exemption
        }


@dataclass(frozen=True)
class SocialSecurityData:
    """Social Security parameters and benefit calculations."""

    year: int
    full_retirement_age: int
    early_retirement_age: int
    maximum_earnings: float
    benefit_formula_bend_points: List[float]
    benefit_formula_rates: List[float]
    cola_rate: float
    medicare_part_b_premium: float
    medicare_part_d_premium: float

    def __post_init__(self):
        """Validate the Social Security data."""
        validator = Validator()

        # Add field validators
        validator.add_field_validator("year").add_rule(RequiredRule("year")).add_rule(RangeRule("year", 1900, 2100))
        validator.add_field_validator("full_retirement_age").add_rule(RequiredRule("full_retirement_age")).add_rule(RangeRule("full_retirement_age", 65, 70))
        validator.add_field_validator("early_retirement_age").add_rule(RequiredRule("early_retirement_age")).add_rule(RangeRule("early_retirement_age", 62, 67))
        validator.add_field_validator("maximum_earnings").add_rule(RequiredRule("maximum_earnings")).add_rule(RangeRule("maximum_earnings", 0.0))
        validator.add_field_validator("benefit_formula_bend_points").add_rule(RequiredRule("benefit_formula_bend_points")).add_rule(TypeRule("benefit_formula_bend_points", list))
        validator.add_field_validator("benefit_formula_rates").add_rule(RequiredRule("benefit_formula_rates")).add_rule(TypeRule("benefit_formula_rates", list))
        validator.add_field_validator("cola_rate").add_rule(RequiredRule("cola_rate")).add_rule(RangeRule("cola_rate", -0.5, 0.5))
        validator.add_field_validator("medicare_part_b_premium").add_rule(RequiredRule("medicare_part_b_premium")).add_rule(RangeRule("medicare_part_b_premium", 0.0))
        validator.add_field_validator("medicare_part_d_premium").add_rule(RequiredRule("medicare_part_d_premium")).add_rule(RangeRule("medicare_part_d_premium", 0.0))

        # Validate the data
        data = {
            "year": self.year,
            "full_retirement_age": self.full_retirement_age,
            "early_retirement_age": self.early_retirement_age,
            "maximum_earnings": self.maximum_earnings,
            "benefit_formula_bend_points": self.benefit_formula_bend_points,
            "benefit_formula_rates": self.benefit_formula_rates,
            "cola_rate": self.cola_rate,
            "medicare_part_b_premium": self.medicare_part_b_premium,
            "medicare_part_d_premium": self.medicare_part_d_premium
        }

        result = validator.validate(data)
        if not result.is_valid:
            raise TaxDataError(f"Invalid Social Security data: {[e.message for e in result.errors]}")

        # Validate age relationship
        if self.early_retirement_age >= self.full_retirement_age:
            raise TaxDataError("Early retirement age must be less than full retirement age")

        # Validate bend points and rates
        if len(self.benefit_formula_bend_points) + 1 != len(self.benefit_formula_rates):
            raise TaxDataError("Number of bend points must match number of rates")

    def calculate_primary_insurance_amount(self, aime: float) -> float:
        """Calculate Primary Insurance Amount (PIA) from Average Indexed Monthly Earnings."""
        if aime <= 0:
            return 0.0

        pia = 0.0
        remaining_aime = aime

        # Calculate PIA using the bend point formula
        # For 2024: 90% of first $1,174, 32% of next $5,904, 15% of remainder
        for i, bend_point in enumerate(self.benefit_formula_bend_points):
            if remaining_aime <= 0:
                break

            # Calculate the amount in this bracket
            if i == 0:
                # First bracket: from 0 to first bend point
                bracket_amount = min(remaining_aime, bend_point)
            else:
                # Subsequent brackets: from previous bend point to current bend point
                prev_bend_point = self.benefit_formula_bend_points[i - 1]
                bracket_amount = min(remaining_aime, bend_point - prev_bend_point)

            pia += bracket_amount * self.benefit_formula_rates[i]
            remaining_aime -= bracket_amount

        # Apply rate for income above highest bend point
        if remaining_aime > 0:
            pia += remaining_aime * self.benefit_formula_rates[-1]

        return pia

    def calculate_benefit_at_age(self, pia: float, claiming_age: int) -> float:
        """Calculate benefit amount at specific claiming age."""
        if claiming_age < self.early_retirement_age:
            raise TaxDataError(f"Claiming age {claiming_age} is before early retirement age {self.early_retirement_age}")

        if claiming_age == self.full_retirement_age:
            return pia
        elif claiming_age < self.full_retirement_age:
            # Early retirement reduction
            months_early = (self.full_retirement_age - claiming_age) * 12
            reduction_factor = 1 - (months_early * 0.005556)  # 5/9 of 1% per month
            return pia * reduction_factor
        else:
            # Delayed retirement credit
            months_delayed = (claiming_age - self.full_retirement_age) * 12
            increase_factor = 1 + (months_delayed * 0.006667)  # 8% per year
            return pia * increase_factor

    def calculate_medicare_premiums(self, income_level: str = "standard") -> Dict[str, float]:
        """Calculate Medicare premiums based on income level."""
        income_multipliers = {
            "standard": 1.0,
            "high": 1.4,
            "highest": 2.6
        }

        multiplier = income_multipliers.get(income_level, 1.0)

        return {
            "part_b": self.medicare_part_b_premium * multiplier,
            "part_d": self.medicare_part_d_premium * multiplier
        }

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "year": self.year,
            "full_retirement_age": self.full_retirement_age,
            "early_retirement_age": self.early_retirement_age,
            "maximum_earnings": self.maximum_earnings,
            "benefit_formula_bend_points": self.benefit_formula_bend_points,
            "benefit_formula_rates": self.benefit_formula_rates,
            "cola_rate": self.cola_rate,
            "medicare_part_b_premium": self.medicare_part_b_premium,
            "medicare_part_d_premium": self.medicare_part_d_premium
        }


class TaxDataLoader:
    """Loader for tax data from various sources."""

    def __init__(self, data_directory: Optional[Path] = None):
        """Initialize the tax data loader."""
        self.data_directory = data_directory or Path("data/tax")
        self.data_directory.mkdir(parents=True, exist_ok=True)

    def load_tax_brackets(self, file_path: Union[str, Path]) -> TaxBrackets:
        """Load tax brackets from JSON file."""
        file_path = Path(file_path)

        if not file_path.exists():
            raise TaxDataError(f"File not found: {file_path}")

        try:
            with open(file_path, 'r') as f:
                data = json.load(f)

            brackets = []
            for bracket_data in data['brackets']:
                bracket = TaxBracket(
                    min=bracket_data['min'],
                    max=bracket_data.get('max'),
                    rate=bracket_data['rate'],
                    filing_status=bracket_data['filing_status']
                )
                brackets.append(bracket)

            return TaxBrackets(
                year=data['year'],
                brackets=brackets,
                filing_status=data['filing_status'],
                standard_deduction=data['standard_deduction'],
                personal_exemption=data.get('personal_exemption', 0.0)
            )

        except Exception as e:
            raise TaxDataError(f"Error loading tax brackets: {e}")

    def load_social_security_data(self, file_path: Union[str, Path]) -> SocialSecurityData:
        """Load Social Security data from JSON file."""
        file_path = Path(file_path)

        if not file_path.exists():
            raise TaxDataError(f"File not found: {file_path}")

        try:
            with open(file_path, 'r') as f:
                data = json.load(f)

            return SocialSecurityData(
                year=data['year'],
                full_retirement_age=data['full_retirement_age'],
                early_retirement_age=data['early_retirement_age'],
                maximum_earnings=data['maximum_earnings'],
                benefit_formula_bend_points=data['benefit_formula_bend_points'],
                benefit_formula_rates=data['benefit_formula_rates'],
                cola_rate=data['cola_rate'],
                medicare_part_b_premium=data['medicare_part_b_premium'],
                medicare_part_d_premium=data['medicare_part_d_premium']
            )

        except Exception as e:
            raise TaxDataError(f"Error loading Social Security data: {e}")

    def save_tax_brackets(self, brackets: TaxBrackets, file_path: Union[str, Path]) -> None:
        """Save tax brackets to JSON file."""
        file_path = Path(file_path)
        file_path.parent.mkdir(parents=True, exist_ok=True)

        try:
            with open(file_path, 'w') as f:
                json.dump(brackets.to_dict(), f, indent=2)
        except Exception as e:
            raise TaxDataError(f"Error saving tax brackets: {e}")

    def save_social_security_data(self, ss_data: SocialSecurityData, file_path: Union[str, Path]) -> None:
        """Save Social Security data to JSON file."""
        file_path = Path(file_path)
        file_path.parent.mkdir(parents=True, exist_ok=True)

        try:
            with open(file_path, 'w') as f:
                json.dump(ss_data.to_dict(), f, indent=2)
        except Exception as e:
            raise TaxDataError(f"Error saving Social Security data: {e}")

    def generate_sample_data(self) -> Tuple[TaxBrackets, SocialSecurityData]:
        """Generate sample tax data for testing."""
        # 2024 Single Filing Tax Brackets
        brackets = [
            TaxBracket(0, 11600, 0.10, "single"),
            TaxBracket(11600, 47150, 0.12, "single"),
            TaxBracket(47150, 100525, 0.22, "single"),
            TaxBracket(100525, 191950, 0.24, "single"),
            TaxBracket(191950, 243725, 0.32, "single"),
            TaxBracket(243725, 609350, 0.35, "single"),
            TaxBracket(609350, None, 0.37, "single")
        ]

        tax_brackets = TaxBrackets(
            year=2024,
            brackets=brackets,
            filing_status="single",
            standard_deduction=14600.0,
            personal_exemption=0.0
        )

        # 2024 Social Security Data
        social_security_data = SocialSecurityData(
            year=2024,
            full_retirement_age=67,
            early_retirement_age=62,
            maximum_earnings=168600.0,
            benefit_formula_bend_points=[1174.0, 7078.0],
            benefit_formula_rates=[0.90, 0.32, 0.15],
            cola_rate=0.032,
            medicare_part_b_premium=174.70,
            medicare_part_d_premium=34.70
        )

        return tax_brackets, social_security_data

    def download_tax_brackets_from_irs(self, year, filing_status="single", file_path=None):
        """Download tax brackets from IRS website for the given year."""
        if requests is None or BeautifulSoup is None:
            raise ImportError("requests and beautifulsoup4 are required for IRS downloads")

        try:
            # IRS tax bracket URLs (these may need updating for new years)
            irs_urls = {
                2024: "https://www.irs.gov/newsroom/irs-provides-tax-inflation-adjustments-for-tax-year-2024",
                2023: "https://www.irs.gov/newsroom/irs-provides-tax-inflation-adjustments-for-tax-year-2023",
                2022: "https://www.irs.gov/newsroom/irs-provides-tax-inflation-adjustments-for-tax-year-2022"
            }

            if year not in irs_urls:
                raise ValueError(f"IRS data not available for year {year}")

            url = irs_urls[year]
            response = requests.get(url)
            response.raise_for_status()

            soup = BeautifulSoup(response.content, 'html.parser')

            # Extract tax bracket information from the page
            # This is a simplified parser - in practice, you'd need more robust parsing
            brackets = []

            # Look for table data or structured content
            tables = soup.find_all('table')
            for table in tables:
                rows = table.find_all('tr')
                for row in rows:
                    cells = row.find_all(['td', 'th'])
                    if len(cells) >= 2:
                        try:
                            # Try to extract bracket information
                            income_text = cells[0].get_text().strip()
                            rate_text = cells[1].get_text().strip()

                            # Parse income range and rate
                            if '$' in income_text and '%' in rate_text:
                                # Extract numeric values from range (e.g., "$0 - $11,600")
                                range_match = re.search(r'\$?([\d,]+)\s*-\s*\$?([\d,]+)', income_text)
                                rate_match = re.search(r'(\d+(?:\.\d+)?)', rate_text)

                                if range_match and rate_match:
                                    bracket_min = float(range_match.group(1).replace(',', ''))
                                    bracket_max = float(range_match.group(2).replace(',', ''))
                                    rate = float(rate_match.group(1)) / 100.0

                                    brackets.append({
                                        'min': bracket_min,
                                        'max': bracket_max,
                                        'rate': rate
                                    })
                        except (ValueError, AttributeError):
                            continue

            if not brackets:
                raise DataError(f"Could not extract tax brackets from IRS page for {year}")

            # Sort brackets by minimum value
            brackets.sort(key=lambda x: x['min'])

            # Create TaxBrackets object
            tax_brackets = TaxBrackets(
                year=year,
                brackets=[TaxBracket(b['min'], b['max'], b['rate'], filing_status) for b in brackets],
                filing_status=filing_status,
                standard_deduction=14600.0,  # 2024 default
                personal_exemption=0.0
            )

            if file_path:
                self.save_tax_brackets(tax_brackets, file_path)

            return tax_brackets

        except Exception as e:
            raise DataError(f"Failed to download tax brackets from IRS: {str(e)}")

    def download_social_security_data_from_ssa(self, year, file_path=None):
        """Download Social Security data from SSA website for the given year."""
        if requests is None or BeautifulSoup is None:
            raise ImportError("requests and beautifulsoup4 are required for SSA downloads")

        try:
            # SSA data URLs
            ssa_urls = {
                2024: "https://www.ssa.gov/oact/cola/COLA2024.html",
                2023: "https://www.ssa.gov/oact/cola/COLA2023.html",
                2022: "https://www.ssa.gov/oact/cola/COLA2022.html"
            }

            if year not in ssa_urls:
                raise ValueError(f"SSA data not available for year {year}")

            url = ssa_urls[year]
            response = requests.get(url)
            response.raise_for_status()

            soup = BeautifulSoup(response.content, 'html.parser')

            # Extract Social Security parameters
            # This is a simplified parser - in practice, you'd need more robust parsing
            cola_rate = 0.0
            bend_points = [1174, 7078]  # Default 2024 values
            benefit_rates = [0.90, 0.32, 0.15]  # Default 2024 rates

            # Look for COLA rate
            text_content = soup.get_text()
            cola_match = re.search(r'(\d+(?:\.\d+)?)\s*percent', text_content, re.IGNORECASE)
            if cola_match:
                cola_rate = float(cola_match.group(1)) / 100.0

            # Create SocialSecurityData object
            ss_data = SocialSecurityData(
                year=year,
                full_retirement_age=67,
                early_retirement_age=62,
                maximum_earnings=168600.0,
                benefit_formula_bend_points=bend_points,
                benefit_formula_rates=benefit_rates,
                cola_rate=cola_rate,
                medicare_part_b_premium=174.70,
                medicare_part_d_premium=34.70
            )

            if file_path:
                self.save_social_security_data(ss_data, file_path)

            return ss_data

        except Exception as e:
            raise DataError(f"Failed to download Social Security data from SSA: {str(e)}")