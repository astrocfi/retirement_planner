"""
Unit tests for date_utils module.
"""

import pytest
from datetime import date, datetime, timedelta
from retirement_planner.utils.date_utils import (
    DateUtils, AgeCalculator, AgePeriod, DatePeriod
)
from retirement_planner.core.exceptions import ValidationError


class TestDateUtils:
    """Test date utilities."""

    def test_calculate_age(self):
        """Test age calculation."""
        birth_date = date(1990, 6, 15)
        target_date = date(2020, 6, 15)
        age = DateUtils.calculate_age(birth_date, target_date)
        assert age == 30

        # Before birthday
        target_date = date(2020, 5, 15)
        age = DateUtils.calculate_age(birth_date, target_date)
        assert age == 29

        # After birthday
        target_date = date(2020, 7, 15)
        age = DateUtils.calculate_age(birth_date, target_date)
        assert age == 30

    def test_calculate_age_default_target(self):
        """Test age calculation with default target date."""
        birth_date = date(1990, 6, 15)
        age = DateUtils.calculate_age(birth_date)
        # Should calculate age as of today
        assert age >= 30  # Assuming test is run after 2020

    def test_calculate_age_validation(self):
        """Test age calculation validation."""
        birth_date = date(1990, 6, 15)
        target_date = date(1980, 6, 15)  # Before birth

        with pytest.raises(ValidationError):
            DateUtils.calculate_age(birth_date, target_date)

    def test_calculate_years_between(self):
        """Test years between calculation."""
        start_date = date(2020, 1, 1)
        end_date = date(2025, 1, 1)
        years = DateUtils.calculate_years_between(start_date, end_date)
        assert abs(years - 5.0) < 0.01

        # Fractional years
        end_date = date(2022, 7, 1)  # 2.5 years later
        years = DateUtils.calculate_years_between(start_date, end_date)
        assert abs(years - 2.5) < 0.1

    def test_calculate_years_between_validation(self):
        """Test years between validation."""
        start_date = date(2020, 1, 1)
        end_date = date(2020, 1, 1)  # Same date

        with pytest.raises(ValidationError):
            DateUtils.calculate_years_between(start_date, end_date)

        end_date = date(2019, 1, 1)  # Before start

        with pytest.raises(ValidationError):
            DateUtils.calculate_years_between(start_date, end_date)

    def test_add_years_to_date(self):
        """Test adding years to date."""
        base_date = date(2020, 6, 15)

        # Whole years
        result = DateUtils.add_years_to_date(base_date, 5)
        expected = date(2025, 6, 15)
        assert result == expected

        # Fractional years
        result = DateUtils.add_years_to_date(base_date, 0.5)
        # Should be approximately 6 months later
        expected = date(2020, 12, 15)
        assert abs((result - base_date).days - 183) < 2  # Allow for leap year differences

    def test_add_years_to_date_validation(self):
        """Test add years validation."""
        base_date = date(2020, 6, 15)

        with pytest.raises(ValidationError):
            DateUtils.add_years_to_date(base_date, -1)

    def test_calculate_retirement_date(self):
        """Test retirement date calculation."""
        birth_date = date(1990, 6, 15)
        retirement_age = 65
        retirement_date = DateUtils.calculate_retirement_date(birth_date, retirement_age)
        expected = date(2055, 6, 15)
        assert retirement_date == expected

    def test_calculate_retirement_date_validation(self):
        """Test retirement date validation."""
        birth_date = date(1990, 6, 15)

        with pytest.raises(ValidationError):
            DateUtils.calculate_retirement_date(birth_date, -5)

    def test_calculate_life_expectancy_date(self):
        """Test life expectancy date calculation."""
        birth_date = date(1990, 6, 15)
        life_expectancy = 85
        end_date = DateUtils.calculate_life_expectancy_date(birth_date, life_expectancy)
        expected = date(2075, 6, 15)
        assert end_date == expected

    def test_get_working_period(self):
        """Test working period calculation."""
        birth_date = date(1990, 6, 15)
        retirement_age = 65
        working_period = DateUtils.get_working_period(birth_date, retirement_age)

        assert working_period.start_date == birth_date
        assert working_period.end_date == date(2055, 6, 15)
        assert working_period.description == "Working period"

    def test_get_retirement_period(self):
        """Test retirement period calculation."""
        birth_date = date(1990, 6, 15)
        retirement_age = 65
        life_expectancy = 85
        retirement_period = DateUtils.get_retirement_period(birth_date, retirement_age, life_expectancy)

        assert retirement_period.start_date == date(2055, 6, 15)
        assert retirement_period.end_date == date(2075, 6, 15)
        assert retirement_period.description == "Retirement period"

    def test_format_age(self):
        """Test age formatting."""
        assert DateUtils.format_age(30) == "age 30"
        assert DateUtils.format_age(0) == "age 0"
        assert DateUtils.format_age(100) == "age 100"

    def test_format_date_range(self):
        """Test date range formatting."""
        start_date = date(2020, 1, 1)
        end_date = date(2025, 12, 31)
        formatted = DateUtils.format_date_range(start_date, end_date)
        assert formatted == "2020-01-01 to 2025-12-31"

    def test_is_leap_year(self):
        """Test leap year detection."""
        assert DateUtils.is_leap_year(2020) is True
        assert DateUtils.is_leap_year(2021) is False
        assert DateUtils.is_leap_year(2000) is True  # Century leap year
        assert DateUtils.is_leap_year(1900) is False  # Century non-leap year

    def test_days_in_year(self):
        """Test days in year calculation."""
        assert DateUtils.days_in_year(2020) == 366
        assert DateUtils.days_in_year(2021) == 365
        assert DateUtils.days_in_year(2000) == 366
        assert DateUtils.days_in_year(1900) == 365


class TestAgeCalculator:
    """Test age calculator utilities."""

    def test_calculate_years_to_retirement(self):
        """Test years to retirement calculation."""
        current_age = 35
        retirement_age = 65
        years = AgeCalculator.calculate_years_to_retirement(current_age, retirement_age)
        assert years == 30

        # Already at retirement age
        current_age = 65
        years = AgeCalculator.calculate_years_to_retirement(current_age, retirement_age)
        assert years == 0

        # Past retirement age
        current_age = 70
        years = AgeCalculator.calculate_years_to_retirement(current_age, retirement_age)
        assert years == 0

    def test_calculate_years_to_retirement_validation(self):
        """Test years to retirement validation."""
        with pytest.raises(ValidationError):
            AgeCalculator.calculate_years_to_retirement(-5, 65)

        with pytest.raises(ValidationError):
            AgeCalculator.calculate_years_to_retirement(35, 150)

    def test_calculate_retirement_years(self):
        """Test retirement years calculation."""
        retirement_age = 65
        life_expectancy = 85
        years = AgeCalculator.calculate_retirement_years(retirement_age, life_expectancy)
        assert years == 20

        # No retirement period
        retirement_age = 85
        years = AgeCalculator.calculate_retirement_years(retirement_age, life_expectancy)
        assert years == 0

    def test_calculate_total_planning_years(self):
        """Test total planning years calculation."""
        current_age = 35
        life_expectancy = 85
        years = AgeCalculator.calculate_total_planning_years(current_age, life_expectancy)
        assert years == 50

        # No planning period
        current_age = 85
        years = AgeCalculator.calculate_total_planning_years(current_age, life_expectancy)
        assert years == 0

    def test_is_working_age(self):
        """Test working age detection."""
        retirement_age = 65

        assert AgeCalculator.is_working_age(30, retirement_age) is True
        assert AgeCalculator.is_working_age(64, retirement_age) is True
        assert AgeCalculator.is_working_age(65, retirement_age) is False
        assert AgeCalculator.is_working_age(70, retirement_age) is False

    def test_is_retirement_age(self):
        """Test retirement age detection."""
        retirement_age = 65

        assert AgeCalculator.is_retirement_age(30, retirement_age) is False
        assert AgeCalculator.is_retirement_age(64, retirement_age) is False
        assert AgeCalculator.is_retirement_age(65, retirement_age) is True
        assert AgeCalculator.is_retirement_age(70, retirement_age) is True

    def test_get_age_periods(self):
        """Test age periods calculation."""
        current_age = 35
        retirement_age = 65
        life_expectancy = 85

        periods = AgeCalculator.get_age_periods(current_age, retirement_age, life_expectancy)

        assert len(periods) == 2

        # Working period
        working_period = periods[0]
        assert working_period.start_age == 35
        assert working_period.end_age == 65
        assert working_period.description == "Working period"

        # Retirement period
        retirement_period = periods[1]
        assert retirement_period.start_age == 65
        assert retirement_period.end_age == 85
        assert retirement_period.description == "Retirement period"

    def test_get_age_periods_already_retired(self):
        """Test age periods when already retired."""
        current_age = 70
        retirement_age = 65
        life_expectancy = 85

        periods = AgeCalculator.get_age_periods(current_age, retirement_age, life_expectancy)

        assert len(periods) == 1

        # Only retirement period
        retirement_period = periods[0]
        assert retirement_period.start_age == 65
        assert retirement_period.end_age == 85
        assert retirement_period.description == "Retirement period"

    def test_calculate_social_security_eligibility(self):
        """Test Social Security eligibility calculation."""
        eligibility = AgeCalculator.calculate_social_security_eligibility(60)
        assert eligibility['early_eligibility'] is False
        assert eligibility['full_eligibility'] is False
        assert eligibility['delayed_eligibility'] is False
        assert eligibility['medicare_eligibility'] is False

        eligibility = AgeCalculator.calculate_social_security_eligibility(62)
        assert eligibility['early_eligibility'] is True
        assert eligibility['full_eligibility'] is False
        assert eligibility['delayed_eligibility'] is False
        assert eligibility['medicare_eligibility'] is False

        eligibility = AgeCalculator.calculate_social_security_eligibility(67)
        assert eligibility['early_eligibility'] is True
        assert eligibility['full_eligibility'] is True
        assert eligibility['delayed_eligibility'] is False
        assert eligibility['medicare_eligibility'] is True

        eligibility = AgeCalculator.calculate_social_security_eligibility(70)
        assert eligibility['early_eligibility'] is True
        assert eligibility['full_eligibility'] is True
        assert eligibility['delayed_eligibility'] is True
        assert eligibility['medicare_eligibility'] is True

    def test_calculate_rmd_age(self):
        """Test RMD age calculation."""
        assert AgeCalculator.calculate_rmd_age(70) is False
        assert AgeCalculator.calculate_rmd_age(73) is True
        assert AgeCalculator.calculate_rmd_age(75) is True
        assert AgeCalculator.calculate_rmd_age(80) is True

    def test_format_age_range(self):
        """Test age range formatting."""
        assert AgeCalculator.format_age_range(30, 65) == "ages 30-65"
        assert AgeCalculator.format_age_range(0, 100) == "ages 0-100"

    def test_calculate_age_at_date(self):
        """Test age at specific date calculation."""
        birth_date = date(1990, 6, 15)
        target_date = date(2020, 6, 15)
        age = AgeCalculator.calculate_age_at_date(birth_date, target_date)
        assert age == 30

    def test_calculate_dates_for_age_range(self):
        """Test date calculation for age range."""
        birth_date = date(1990, 6, 15)
        start_age = 30
        end_age = 65

        start_date, end_date = AgeCalculator.calculate_dates_for_age_range(
            birth_date, start_age, end_age
        )

        assert start_date == date(2020, 6, 15)
        assert end_date == date(2055, 6, 15)


class TestAgePeriod:
    """Test AgePeriod dataclass."""

    def test_age_period_creation(self):
        """Test AgePeriod creation."""
        period = AgePeriod(start_age=30, end_age=65, description="Working period")

        assert period.start_age == 30
        assert period.end_age == 65
        assert period.description == "Working period"

    def test_age_period_validation(self):
        """Test AgePeriod validation."""
        with pytest.raises(ValidationError):
            AgePeriod(start_age=-5, end_age=65)

        with pytest.raises(ValidationError):
            AgePeriod(start_age=30, end_age=150)

        with pytest.raises(ValidationError):
            AgePeriod(start_age=65, end_age=30)  # Start after end

    def test_age_period_immutability(self):
        """Test AgePeriod immutability."""
        period = AgePeriod(start_age=30, end_age=65)

        with pytest.raises(Exception):
            period.start_age = 35


class TestDatePeriod:
    """Test DatePeriod dataclass."""

    def test_date_period_creation(self):
        """Test DatePeriod creation."""
        start_date = date(2020, 1, 1)
        end_date = date(2025, 12, 31)
        period = DatePeriod(start_date=start_date, end_date=end_date, description="Test period")

        assert period.start_date == start_date
        assert period.end_date == end_date
        assert period.description == "Test period"

    def test_date_period_validation(self):
        """Test DatePeriod validation."""
        start_date = date(2020, 1, 1)
        end_date = date(2020, 1, 1)  # Same date

        with pytest.raises(ValidationError):
            DatePeriod(start_date=start_date, end_date=end_date)

        end_date = date(2019, 12, 31)  # Before start

        with pytest.raises(ValidationError):
            DatePeriod(start_date=start_date, end_date=end_date)

    def test_date_period_immutability(self):
        """Test DatePeriod immutability."""
        start_date = date(2020, 1, 1)
        end_date = date(2025, 12, 31)
        period = DatePeriod(start_date=start_date, end_date=end_date)

        with pytest.raises(Exception):
            period.start_date = date(2021, 1, 1)