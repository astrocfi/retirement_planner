"""
Date utilities for retirement planning.

This module provides date/age conversions and time period calculations
for retirement planning scenarios.
"""

from datetime import datetime, date, timedelta
from typing import List, Optional, Tuple, Union, Dict
from dataclasses import dataclass
from retirement_planner.core.validation import Validator, RangeRule, RequiredRule
from retirement_planner.core.exceptions import ValidationError


@dataclass(frozen=True)
class AgePeriod:
    """Represents a period defined by ages."""
    start_age: int
    end_age: int
    description: Optional[str] = None

    def __post_init__(self):
        """Validate age period."""
        validator = Validator()
        validator.add_field_validator('start_age').add_rule(RangeRule('start_age', min_value=0, max_value=120))
        validator.add_field_validator('end_age').add_rule(RangeRule('end_age', min_value=0, max_value=120))

        result = validator.validate({
            'start_age': self.start_age,
            'end_age': self.end_age
        })

        if not result.is_valid:
            raise ValidationError(f"Age period validation failed: {result.errors}")

        if self.start_age > self.end_age:
            raise ValidationError("Start age must be less than or equal to end age")


@dataclass(frozen=True)
class DatePeriod:
    """Represents a period defined by dates."""
    start_date: date
    end_date: date
    description: Optional[str] = None

    def __post_init__(self):
        """Validate date period."""
        if self.start_date >= self.end_date:
            raise ValidationError("Start date must be before end date")


class DateUtils:
    """Date and time period calculation utilities."""

    @staticmethod
    def calculate_age(birth_date: date, target_date: Optional[date] = None) -> int:
        """
        Calculate age at a specific date.

        Args:
            birth_date: Date of birth
            target_date: Date to calculate age at (defaults to today)

        Returns:
            Age in years
        """
        if target_date is None:
            target_date = date.today()

        if birth_date > target_date:
            raise ValidationError("Birth date cannot be after target date")

        age = target_date.year - birth_date.year
        if (target_date.month, target_date.day) < (birth_date.month, birth_date.day):
            age -= 1

        return age

    @staticmethod
    def calculate_years_between(start_date: date, end_date: date) -> float:
        """
        Calculate years between two dates.

        Args:
            start_date: Start date
            end_date: End date

        Returns:
            Years between dates (can be fractional)
        """
        if start_date >= end_date:
            raise ValidationError("Start date must be before end date")

        delta = end_date - start_date
        return delta.days / 365.25  # Account for leap years

    @staticmethod
    def add_years_to_date(base_date: date, years: float) -> date:
        """
        Add years to a date.

        Args:
            base_date: Base date
            years: Years to add (can be fractional)

        Returns:
            New date
        """
        if years < 0:
            raise ValidationError("Years cannot be negative")

        # Handle fractional years
        whole_years = int(years)
        fractional_days = int((years - whole_years) * 365.25)

        # Add whole years
        new_date = base_date.replace(year=base_date.year + whole_years)

        # Add fractional days
        new_date += timedelta(days=fractional_days)

        return new_date

    @staticmethod
    def calculate_retirement_date(birth_date: date, retirement_age: int) -> date:
        """
        Calculate retirement date based on birth date and retirement age.

        Args:
            birth_date: Date of birth
            retirement_age: Age at retirement

        Returns:
            Retirement date
        """
        if retirement_age < 0:
            raise ValidationError("Retirement age cannot be negative")

        return DateUtils.add_years_to_date(birth_date, retirement_age)

    @staticmethod
    def calculate_life_expectancy_date(birth_date: date, life_expectancy: int) -> date:
        """
        Calculate expected end of life date.

        Args:
            birth_date: Date of birth
            life_expectancy: Expected age at death

        Returns:
            Expected end of life date
        """
        if life_expectancy < 0:
            raise ValidationError("Life expectancy cannot be negative")

        return DateUtils.add_years_to_date(birth_date, life_expectancy)

    @staticmethod
    def get_working_period(birth_date: date, retirement_age: int) -> DatePeriod:
        """
        Get working period from birth to retirement.

        Args:
            birth_date: Date of birth
            retirement_age: Age at retirement

        Returns:
            Working period
        """
        retirement_date = DateUtils.calculate_retirement_date(birth_date, retirement_age)
        return DatePeriod(
            start_date=birth_date,
            end_date=retirement_date,
            description="Working period"
        )

    @staticmethod
    def get_retirement_period(birth_date: date, retirement_age: int,
                            life_expectancy: int) -> DatePeriod:
        """
        Get retirement period from retirement to end of life.

        Args:
            birth_date: Date of birth
            retirement_age: Age at retirement
            life_expectancy: Expected age at death

        Returns:
            Retirement period
        """
        retirement_date = DateUtils.calculate_retirement_date(birth_date, retirement_age)
        end_date = DateUtils.calculate_life_expectancy_date(birth_date, life_expectancy)

        return DatePeriod(
            start_date=retirement_date,
            end_date=end_date,
            description="Retirement period"
        )

    @staticmethod
    def format_age(age: int) -> str:
        """
        Format age consistently.

        Args:
            age: Age in years

        Returns:
            Formatted age string
        """
        return f"age {age}"

    @staticmethod
    def format_date_range(start_date: date, end_date: date) -> str:
        """
        Format date range consistently.

        Args:
            start_date: Start date
            end_date: End date

        Returns:
            Formatted date range string
        """
        return f"{start_date.strftime('%Y-%m-%d')} to {end_date.strftime('%Y-%m-%d')}"

    @staticmethod
    def is_leap_year(year: int) -> bool:
        """
        Check if year is a leap year.

        Args:
            year: Year to check

        Returns:
            True if leap year
        """
        return year % 4 == 0 and (year % 100 != 0 or year % 400 == 0)

    @staticmethod
    def days_in_year(year: int) -> int:
        """
        Get number of days in a year.

        Args:
            year: Year to check

        Returns:
            Number of days in year
        """
        return 366 if DateUtils.is_leap_year(year) else 365


class AgeCalculator:
    """Age-based calculation utilities."""

    @staticmethod
    def calculate_years_to_retirement(current_age: int, retirement_age: int) -> int:
        """
        Calculate years until retirement.

        Args:
            current_age: Current age
            retirement_age: Target retirement age

        Returns:
            Years until retirement
        """
        validator = Validator()
        validator.add_field_validator('current_age').add_rule(RangeRule('current_age', min_value=0, max_value=120))
        validator.add_field_validator('retirement_age').add_rule(RangeRule('retirement_age', min_value=0, max_value=120))

        result = validator.validate({
            'current_age': current_age,
            'retirement_age': retirement_age
        })

        if not result.is_valid:
            raise ValidationError(f"Years to retirement validation failed: {result.errors}")

        if current_age >= retirement_age:
            return 0

        return retirement_age - current_age

    @staticmethod
    def calculate_retirement_years(retirement_age: int, life_expectancy: int) -> int:
        """
        Calculate years in retirement.

        Args:
            retirement_age: Age at retirement
            life_expectancy: Expected age at death

        Returns:
            Years in retirement
        """
        validator = Validator()
        validator.add_field_validator('retirement_age').add_rule(RangeRule('retirement_age', min_value=0, max_value=120))
        validator.add_field_validator('life_expectancy').add_rule(RangeRule('life_expectancy', min_value=0, max_value=120))

        result = validator.validate({
            'retirement_age': retirement_age,
            'life_expectancy': life_expectancy
        })

        if not result.is_valid:
            raise ValidationError(f"Retirement years validation failed: {result.errors}")

        if retirement_age >= life_expectancy:
            return 0

        return life_expectancy - retirement_age

    @staticmethod
    def calculate_total_planning_years(current_age: int, life_expectancy: int) -> int:
        """
        Calculate total years for planning horizon.

        Args:
            current_age: Current age
            life_expectancy: Expected age at death

        Returns:
            Total planning years
        """
        validator = Validator()
        validator.add_field_validator('current_age').add_rule(RangeRule('current_age', min_value=0, max_value=120))
        validator.add_field_validator('life_expectancy').add_rule(RangeRule('life_expectancy', min_value=0, max_value=120))

        result = validator.validate({
            'current_age': current_age,
            'life_expectancy': life_expectancy
        })

        if not result.is_valid:
            raise ValidationError(f"Total planning years validation failed: {result.errors}")

        if current_age >= life_expectancy:
            return 0

        return life_expectancy - current_age

    @staticmethod
    def is_working_age(age: int, retirement_age: int) -> bool:
        """
        Check if age is in working period.

        Args:
            age: Age to check
            retirement_age: Retirement age

        Returns:
            True if in working period
        """
        return age < retirement_age

    @staticmethod
    def is_retirement_age(age: int, retirement_age: int) -> bool:
        """
        Check if age is in retirement period.

        Args:
            age: Age to check
            retirement_age: Retirement age

        Returns:
            True if in retirement period
        """
        return age >= retirement_age

    @staticmethod
    def get_age_periods(current_age: int, retirement_age: int,
                       life_expectancy: int) -> List[AgePeriod]:
        """
        Get age-based periods for planning.

        Args:
            current_age: Current age
            retirement_age: Retirement age
            life_expectancy: Expected age at death

        Returns:
            List of age periods
        """
        periods = []

        # Working period
        if current_age < retirement_age:
            periods.append(AgePeriod(
                start_age=current_age,
                end_age=retirement_age,
                description="Working period"
            ))

        # Retirement period
        if retirement_age < life_expectancy:
            periods.append(AgePeriod(
                start_age=retirement_age,
                end_age=life_expectancy,
                description="Retirement period"
            ))

        return periods

    @staticmethod
    def calculate_social_security_eligibility(age: int, full_retirement_age: int = 67) -> Dict[str, bool]:
        """
        Calculate Social Security eligibility at different ages.

        Args:
            age: Current age
            full_retirement_age: Full retirement age

        Returns:
            Dictionary of eligibility flags
        """
        return {
            'early_eligibility': age >= 62,
            'full_eligibility': age >= full_retirement_age,
            'delayed_eligibility': age >= 70,
            'medicare_eligibility': age >= 65
        }

    @staticmethod
    def calculate_rmd_age(age: int) -> bool:
        """
        Check if RMDs are required at given age.

        Args:
            age: Age to check

        Returns:
            True if RMDs required
        """
        # RMDs start at age 73 for those born 1951-1959, 75 for those born 1960+
        # For simplicity, using 73 as the threshold
        return age >= 73

    @staticmethod
    def format_age_range(start_age: int, end_age: int) -> str:
        """
        Format age range consistently.

        Args:
            start_age: Start age
            end_age: End age

        Returns:
            Formatted age range string
        """
        return f"ages {start_age}-{end_age}"

    @staticmethod
    def calculate_age_at_date(birth_date: date, target_date: date) -> int:
        """
        Calculate exact age at a specific date.

        Args:
            birth_date: Date of birth
            target_date: Target date

        Returns:
            Age at target date
        """
        return DateUtils.calculate_age(birth_date, target_date)

    @staticmethod
    def calculate_dates_for_age_range(birth_date: date, start_age: int,
                                    end_age: int) -> Tuple[date, date]:
        """
        Calculate start and end dates for an age range.

        Args:
            birth_date: Date of birth
            start_age: Start age
            end_age: End age

        Returns:
            Tuple of (start_date, end_date)
        """
        start_date = DateUtils.add_years_to_date(birth_date, start_age)
        end_date = DateUtils.add_years_to_date(birth_date, end_age)

        return start_date, end_date