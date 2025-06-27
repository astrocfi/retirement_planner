"""
Unit tests for tax_data module.
"""

import pytest
import numpy as np
import pandas as pd
from datetime import date, datetime
from pathlib import Path
import tempfile
import json
from unittest.mock import patch, MagicMock

from retirement_planner.data.tax_data import (
    TaxDataLoader,
    TaxBracket,
    TaxBrackets,
    SocialSecurityData,
    TaxDataError
)
from retirement_planner.core.exceptions import ValidationError, DataError


class TestTaxBracket:
    """Test TaxBracket class."""

    def test_tax_bracket_creation(self):
        """Test creating tax bracket with valid data."""
        bracket = TaxBracket(
            bracket_min=0,
            bracket_max=11600,
            rate=0.10,
            filing_status="single"
        )

        assert bracket.bracket_min == 0
        assert bracket.bracket_max == 11600
        assert bracket.rate == 0.10
        assert bracket.filing_status == "single"

    def test_tax_bracket_creation_top_bracket(self):
        """Test creating top tax bracket (no upper limit)."""
        bracket = TaxBracket(
            bracket_min=609350,
            bracket_max=None,
            rate=0.37,
            filing_status="single"
        )

        assert bracket.bracket_min == 609350
        assert bracket.bracket_max is None
        assert bracket.rate == 0.37

    def test_tax_bracket_validation_invalid_rate(self):
        """Test validation with invalid tax rate."""
        with pytest.raises(TaxDataError, match="Invalid tax bracket"):
            TaxBracket(
                bracket_min=0,
                bracket_max=11600,
                rate=1.5,  # Rate > 100%
                filing_status="single"
            )

    def test_tax_bracket_validation_negative_rate(self):
        """Test validation with negative tax rate."""
        with pytest.raises(TaxDataError, match="Invalid tax bracket"):
            TaxBracket(
                bracket_min=0,
                bracket_max=11600,
                rate=-0.10,  # Negative rate
                filing_status="single"
            )

    def test_tax_bracket_validation_invalid_bracket_range(self):
        """Test tax bracket validation with invalid bracket range."""
        with pytest.raises(TaxDataError, match="Bracket minimum must be less than bracket maximum"):
            TaxBracket(
                bracket_min=10000,
                bracket_max=5000,  # Max < Min
                rate=0.25,
                filing_status="single"
            )

    def test_contains_income(self):
        """Test checking if income falls within bracket."""
        bracket = TaxBracket(
            bracket_min=11600,
            bracket_max=47150,
            rate=0.12,
            filing_status="single"
        )

        assert bracket.contains_income(11600) is True
        assert bracket.contains_income(25000) is True
        assert bracket.contains_income(47150) is True
        assert bracket.contains_income(11599) is False
        assert bracket.contains_income(47151) is False

    def test_contains_income_top_bracket(self):
        """Test checking income in top bracket (no upper limit)."""
        bracket = TaxBracket(
            bracket_min=609350,
            bracket_max=None,
            rate=0.37,
            filing_status="single"
        )

        assert bracket.contains_income(609350) is True
        assert bracket.contains_income(1000000) is True
        assert bracket.contains_income(609349) is False

    def test_calculate_tax(self):
        """Test calculating tax for income in bracket."""
        bracket = TaxBracket(
            bracket_min=11600,
            bracket_max=47150,
            rate=0.12,
            filing_status="single"
        )

        # Income within bracket
        tax = bracket.calculate_tax(25000)
        expected_tax = (25000 - 11600) * 0.12
        assert abs(tax - expected_tax) < 1e-6

        # Income at bracket minimum
        tax = bracket.calculate_tax(11600)
        assert tax == 0.0

        # Income at bracket maximum
        tax = bracket.calculate_tax(47150)
        expected_tax = (47150 - 11600) * 0.12
        assert abs(tax - expected_tax) < 1e-6

        # Income outside bracket
        tax = bracket.calculate_tax(10000)
        assert tax == 0.0

    def test_calculate_tax_top_bracket(self):
        """Test calculating tax for top bracket."""
        bracket = TaxBracket(
            bracket_min=609350,
            bracket_max=None,
            rate=0.37,
            filing_status="single"
        )

        tax = bracket.calculate_tax(700000)
        expected_tax = (700000 - 609350) * 0.37
        assert abs(tax - expected_tax) < 1e-6

    def test_to_dict(self):
        """Test converting to dictionary."""
        bracket = TaxBracket(
            bracket_min=11600,
            bracket_max=47150,
            rate=0.12,
            filing_status="single"
        )

        data_dict = bracket.to_dict()
        assert data_dict['bracket_min'] == 11600
        assert data_dict['bracket_max'] == 47150
        assert data_dict['rate'] == 0.12
        assert data_dict['filing_status'] == "single"


class TestTaxBrackets:
    """Test TaxBrackets class."""

    def test_tax_brackets_creation(self):
        """Test creating tax brackets with valid data."""
        brackets = [
            TaxBracket(0, 11600, 0.10, "single"),
            TaxBracket(11600, 47150, 0.12, "single"),
            TaxBracket(47150, 100525, 0.22, "single"),
            TaxBracket(100525, None, 0.24, "single")
        ]

        tax_brackets = TaxBrackets(
            year=2024,
            brackets=brackets,
            filing_status="single",
            standard_deduction=14600.0,
            personal_exemption=0.0
        )

        assert tax_brackets.year == 2024
        assert len(tax_brackets.brackets) == 4
        assert tax_brackets.filing_status == "single"
        assert tax_brackets.standard_deduction == 14600.0
        assert tax_brackets.personal_exemption == 0.0

    def test_tax_brackets_validation_non_consecutive(self):
        """Test validation with non-consecutive brackets."""
        brackets = [
            TaxBracket(0, 11600, 0.10, "single"),
            TaxBracket(12000, 47150, 0.12, "single")  # Gap between brackets
        ]

        with pytest.raises(TaxDataError, match="Tax brackets must be consecutive"):
            TaxBrackets(
                year=2024,
                brackets=brackets,
                filing_status="single",
                standard_deduction=14600.0
            )

    def test_tax_brackets_validation_mixed_filing_status(self):
        """Test validation with mixed filing statuses."""
        brackets = [
            TaxBracket(0, 11600, 0.10, "single"),
            TaxBracket(11600, 47150, 0.12, "married")  # Different filing status
        ]

        with pytest.raises(TaxDataError, match="All brackets must have same filing status"):
            TaxBrackets(
                year=2024,
                brackets=brackets,
                filing_status="single",
                standard_deduction=14600.0
            )

    def test_get_bracket_for_income(self):
        """Test getting bracket for specific income level."""
        brackets = [
            TaxBracket(0, 11600, 0.10, "single"),
            TaxBracket(11600, 47150, 0.12, "single"),
            TaxBracket(47150, 100525, 0.22, "single")
        ]

        tax_brackets = TaxBrackets(
            year=2024,
            brackets=brackets,
            filing_status="single",
            standard_deduction=14600.0
        )

        # Test income in first bracket
        bracket = tax_brackets.get_bracket_for_income(10000)
        assert bracket.rate == 0.10

        # Test income in second bracket
        bracket = tax_brackets.get_bracket_for_income(25000)
        assert bracket.rate == 0.12

        # Test income in third bracket
        bracket = tax_brackets.get_bracket_for_income(60000)
        assert bracket.rate == 0.22

    def test_calculate_total_tax(self):
        """Test calculating total tax for given income."""
        brackets = [
            TaxBracket(0, 11600, 0.10, "single"),
            TaxBracket(11600, 47150, 0.12, "single"),
            TaxBracket(47150, 100525, 0.22, "single")
        ]

        tax_brackets = TaxBrackets(
            year=2024,
            brackets=brackets,
            filing_status="single",
            standard_deduction=14600.0
        )

        # Test income in first bracket
        tax = tax_brackets.calculate_total_tax(10000)
        expected_tax = 10000 * 0.10
        assert abs(tax - expected_tax) < 1e-6

        # Test income in second bracket
        tax = tax_brackets.calculate_total_tax(25000)
        expected_tax = 11600 * 0.10 + (25000 - 11600) * 0.12
        assert abs(tax - expected_tax) < 1e-6

        # Test income in third bracket
        tax = tax_brackets.calculate_total_tax(60000)
        expected_tax = 11600 * 0.10 + (47150 - 11600) * 0.12 + (60000 - 47150) * 0.22
        assert abs(tax - expected_tax) < 1e-6

        # Test zero income
        tax = tax_brackets.calculate_total_tax(0)
        assert tax == 0.0

        # Test negative income
        tax = tax_brackets.calculate_total_tax(-1000)
        assert tax == 0.0

    def test_get_marginal_rate(self):
        """Test getting marginal tax rate for given income."""
        brackets = [
            TaxBracket(0, 11600, 0.10, "single"),
            TaxBracket(11600, 47150, 0.12, "single"),
            TaxBracket(47150, 100525, 0.22, "single")
        ]

        tax_brackets = TaxBrackets(
            year=2024,
            brackets=brackets,
            filing_status="single",
            standard_deduction=14600.0
        )

        assert tax_brackets.get_marginal_rate(10000) == 0.10
        assert tax_brackets.get_marginal_rate(25000) == 0.12
        assert tax_brackets.get_marginal_rate(60000) == 0.22

    def test_get_effective_rate(self):
        """Test getting effective tax rate for given income."""
        brackets = [
            TaxBracket(0, 11600, 0.10, "single"),
            TaxBracket(11600, 47150, 0.12, "single")
        ]

        tax_brackets = TaxBrackets(
            year=2024,
            brackets=brackets,
            filing_status="single",
            standard_deduction=14600.0
        )

        # Test income in first bracket
        effective_rate = tax_brackets.get_effective_rate(10000)
        expected_rate = (10000 * 0.10) / 10000
        assert abs(effective_rate - expected_rate) < 1e-6

        # Test income in second bracket
        effective_rate = tax_brackets.get_effective_rate(25000)
        total_tax = 11600 * 0.10 + (25000 - 11600) * 0.12
        expected_rate = total_tax / 25000
        assert abs(effective_rate - expected_rate) < 1e-6

        # Test zero income
        effective_rate = tax_brackets.get_effective_rate(0)
        assert effective_rate == 0.0

    def test_to_dict(self):
        """Test converting to dictionary."""
        brackets = [
            TaxBracket(0, 11600, 0.10, "single"),
            TaxBracket(11600, 47150, 0.12, "single")
        ]

        tax_brackets = TaxBrackets(
            year=2024,
            brackets=brackets,
            filing_status="single",
            standard_deduction=14600.0,
            personal_exemption=0.0
        )

        data_dict = tax_brackets.to_dict()
        assert data_dict['year'] == 2024
        assert len(data_dict['brackets']) == 2
        assert data_dict['filing_status'] == "single"
        assert data_dict['standard_deduction'] == 14600.0
        assert data_dict['personal_exemption'] == 0.0


class TestSocialSecurityData:
    """Test SocialSecurityData class."""

    def test_social_security_data_creation(self):
        """Test creating Social Security data with valid data."""
        ss_data = SocialSecurityData(
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

        assert ss_data.year == 2024
        assert ss_data.full_retirement_age == 67
        assert ss_data.early_retirement_age == 62
        assert ss_data.maximum_earnings == 168600.0
        assert ss_data.benefit_formula_bend_points == [1174.0, 7078.0]
        assert ss_data.benefit_formula_rates == [0.90, 0.32, 0.15]
        assert ss_data.cola_rate == 0.032
        assert ss_data.medicare_part_b_premium == 174.70
        assert ss_data.medicare_part_d_premium == 34.70

    def test_social_security_data_validation_invalid_ages(self):
        """Test validation with invalid age ranges."""
        with pytest.raises(TaxDataError, match="Early retirement age must be less than full retirement age"):
            SocialSecurityData(
                year=2024,
                full_retirement_age=65,
                early_retirement_age=67,  # Early > Full
                maximum_earnings=168600.0,
                benefit_formula_bend_points=[1174.0, 7078.0],
                benefit_formula_rates=[0.90, 0.32, 0.15],
                cola_rate=0.032,
                medicare_part_b_premium=174.70,
                medicare_part_d_premium=34.70
            )

    def test_social_security_data_validation_mismatched_bend_points_rates(self):
        """Test validation with mismatched bend points and rates."""
        with pytest.raises(TaxDataError, match="Number of bend points must match number of rates"):
            SocialSecurityData(
                year=2024,
                full_retirement_age=67,
                early_retirement_age=62,
                maximum_earnings=168600.0,
                benefit_formula_bend_points=[1174.0, 7078.0],  # 2 bend points
                benefit_formula_rates=[0.90, 0.32],  # Only 2 rates
                cola_rate=0.032,
                medicare_part_b_premium=174.70,
                medicare_part_d_premium=34.70
            )

    def test_calculate_primary_insurance_amount(self):
        """Test calculating primary insurance amount."""
        ss_data = SocialSecurityData(
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

        # Test with AIME of $1000 (below first bend point)
        pia = ss_data.calculate_primary_insurance_amount(1000.0)
        expected_pia = 1000.0 * 0.90  # 90% of first $1174
        assert abs(pia - expected_pia) < 1e-6

        # Test with AIME of $2000 (between bend points)
        pia = ss_data.calculate_primary_insurance_amount(2000.0)
        expected_pia = 1174.0 * 0.90 + (2000.0 - 1174.0) * 0.32
        assert abs(pia - expected_pia) < 1e-6

        # Test with AIME of $8000 (above second bend point)
        pia = ss_data.calculate_primary_insurance_amount(8000.0)
        expected_pia = 1174.0 * 0.90 + (7078.0 - 1174.0) * 0.32 + (8000.0 - 7078.0) * 0.15
        assert abs(pia - expected_pia) < 1e-6

        # Test zero AIME
        pia = ss_data.calculate_primary_insurance_amount(0.0)
        assert pia == 0.0

        # Test negative AIME
        pia = ss_data.calculate_primary_insurance_amount(-1000.0)
        assert pia == 0.0

    def test_calculate_benefit_at_age(self):
        """Test calculating benefit at specific claiming age."""
        ss_data = SocialSecurityData(
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

        pia = 2000.0  # $2000 PIA

        # Test claiming at full retirement age
        benefit = ss_data.calculate_benefit_at_age(pia, 67)
        assert abs(benefit - pia) < 1e-6

        # Test claiming early (age 62)
        benefit = ss_data.calculate_benefit_at_age(pia, 62)
        months_early = (67 - 62) * 12
        reduction_factor = 1 - (months_early * 0.005556)
        expected_benefit = pia * reduction_factor
        assert abs(benefit - expected_benefit) < 1e-6

        # Test claiming late (age 70)
        benefit = ss_data.calculate_benefit_at_age(pia, 70)
        months_delayed = (70 - 67) * 12
        increase_factor = 1 + (months_delayed * 0.006667)
        expected_benefit = pia * increase_factor
        assert abs(benefit - expected_benefit) < 1e-6

        # Test claiming before early retirement age
        with pytest.raises(TaxDataError, match="Claiming age 60 is before early retirement age 62"):
            ss_data.calculate_benefit_at_age(pia, 60)

    def test_calculate_medicare_premiums(self):
        """Test calculating Medicare premiums."""
        ss_data = SocialSecurityData(
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

        # Test standard income level
        premiums = ss_data.calculate_medicare_premiums("standard")
        assert abs(premiums["part_b"] - 174.70) < 1e-6
        assert abs(premiums["part_d"] - 34.70) < 1e-6

        # Test high income level
        premiums = ss_data.calculate_medicare_premiums("high")
        assert abs(premiums["part_b"] - 174.70 * 1.4) < 1e-6
        assert abs(premiums["part_d"] - 34.70 * 1.4) < 1e-6

        # Test highest income level
        premiums = ss_data.calculate_medicare_premiums("highest")
        assert abs(premiums["part_b"] - 174.70 * 2.6) < 1e-6
        assert abs(premiums["part_d"] - 34.70 * 2.6) < 1e-6

        # Test unknown income level (defaults to standard)
        premiums = ss_data.calculate_medicare_premiums("unknown")
        assert abs(premiums["part_b"] - 174.70) < 1e-6

    def test_to_dict(self):
        """Test converting to dictionary."""
        ss_data = SocialSecurityData(
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

        data_dict = ss_data.to_dict()
        assert data_dict['year'] == 2024
        assert data_dict['full_retirement_age'] == 67
        assert data_dict['early_retirement_age'] == 62
        assert data_dict['maximum_earnings'] == 168600.0
        assert data_dict['benefit_formula_bend_points'] == [1174.0, 7078.0]
        assert data_dict['benefit_formula_rates'] == [0.90, 0.32, 0.15]
        assert data_dict['cola_rate'] == 0.032
        assert data_dict['medicare_part_b_premium'] == 174.70
        assert data_dict['medicare_part_d_premium'] == 34.70


class TestTaxDataLoader:
    """Test TaxDataLoader class."""

    def test_tax_data_loader_creation(self):
        """Test creating tax data loader."""
        loader = TaxDataLoader()
        assert loader.data_directory == Path("data/tax")

        custom_loader = TaxDataLoader(Path("custom/tax"))
        assert custom_loader.data_directory == Path("custom/tax")

    def test_load_tax_brackets_json(self):
        """Test loading tax brackets from JSON."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            json.dump({
                "year": 2024,
                "filing_status": "single",
                "standard_deduction": 14600.0,
                "personal_exemption": 0.0,
                "brackets": [
                    {
                        "bracket_min": 0,
                        "bracket_max": 11600,
                        "rate": 0.10,
                        "filing_status": "single"
                    },
                    {
                        "bracket_min": 11600,
                        "bracket_max": 47150,
                        "rate": 0.12,
                        "filing_status": "single"
                    }
                ]
            }, f)
            temp_file = f.name

        try:
            loader = TaxDataLoader()
            tax_brackets = loader.load_tax_brackets(temp_file)

            assert tax_brackets.year == 2024
            assert tax_brackets.filing_status == "single"
            assert len(tax_brackets.brackets) == 2
            assert tax_brackets.brackets[0].rate == 0.10
            assert tax_brackets.brackets[1].rate == 0.12
        finally:
            Path(temp_file).unlink()

    def test_load_tax_brackets_nonexistent_file(self):
        """Test loading from nonexistent file."""
        loader = TaxDataLoader()

        with pytest.raises(TaxDataError, match="File not found"):
            loader.load_tax_brackets("nonexistent.json")

    def test_load_social_security_data_json(self):
        """Test loading Social Security data from JSON."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            json.dump({
                "year": 2024,
                "full_retirement_age": 67,
                "early_retirement_age": 62,
                "maximum_earnings": 168600.0,
                "benefit_formula_bend_points": [1174.0, 7078.0],
                "benefit_formula_rates": [0.90, 0.32, 0.15],
                "cola_rate": 0.032,
                "medicare_part_b_premium": 174.70,
                "medicare_part_d_premium": 34.70
            }, f)
            temp_file = f.name

        try:
            loader = TaxDataLoader()
            ss_data = loader.load_social_security_data(temp_file)

            assert ss_data.year == 2024
            assert ss_data.full_retirement_age == 67
            assert ss_data.early_retirement_age == 62
            assert ss_data.maximum_earnings == 168600.0
        finally:
            Path(temp_file).unlink()

    def test_save_tax_brackets(self):
        """Test saving tax brackets to JSON."""
        brackets = [
            TaxBracket(0, 11600, 0.10, "single"),
            TaxBracket(11600, 47150, 0.12, "single")
        ]

        tax_brackets = TaxBrackets(
            year=2024,
            brackets=brackets,
            filing_status="single",
            standard_deduction=14600.0,
            personal_exemption=0.0
        )

        with tempfile.NamedTemporaryFile(suffix='.json', delete=False) as f:
            temp_file = f.name

        try:
            loader = TaxDataLoader()
            loader.save_tax_brackets(tax_brackets, temp_file)

            # Verify file was created and contains data
            assert Path(temp_file).exists()
            with open(temp_file, 'r') as f:
                data = json.load(f)
            assert data['year'] == 2024
            assert data['filing_status'] == "single"
            assert len(data['brackets']) == 2
        finally:
            Path(temp_file).unlink()

    def test_save_social_security_data(self):
        """Test saving Social Security data to JSON."""
        ss_data = SocialSecurityData(
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

        with tempfile.NamedTemporaryFile(suffix='.json', delete=False) as f:
            temp_file = f.name

        try:
            loader = TaxDataLoader()
            loader.save_social_security_data(ss_data, temp_file)

            # Verify file was created and contains data
            assert Path(temp_file).exists()
            with open(temp_file, 'r') as f:
                data = json.load(f)
            assert data['year'] == 2024
            assert data['full_retirement_age'] == 67
            assert data['early_retirement_age'] == 62
        finally:
            Path(temp_file).unlink()

    def test_generate_sample_data(self):
        """Test generating sample tax data."""
        loader = TaxDataLoader()
        tax_brackets, social_security_data = loader.generate_sample_data()

        # Check tax brackets
        assert tax_brackets.year == 2024
        assert tax_brackets.filing_status == "single"
        assert len(tax_brackets.brackets) == 7  # 2024 single filing brackets

        # Check Social Security data
        assert social_security_data.year == 2024
        assert social_security_data.full_retirement_age == 67
        assert social_security_data.early_retirement_age == 62
        assert social_security_data.maximum_earnings == 168600.0

    @patch('retirement_planner.data.tax_data.requests.get')
    def test_download_tax_brackets_from_irs(self, mock_get):
        """Test downloading tax brackets from IRS."""
        # Mock the HTTP response with HTML containing tax bracket data
        mock_response = MagicMock()
        mock_response.raise_for_status.return_value = None
        mock_response.content = b"""
        <html><body>
        <table>
            <tr><td>$0 - $11,600</td><td>10%</td></tr>
            <tr><td>$11,600 - $47,150</td><td>12%</td></tr>
            <tr><td>$47,150 - $100,525</td><td>22%</td></tr>
        </table>
        </body></html>
        """
        mock_get.return_value = mock_response

        loader = TaxDataLoader()
        result = loader.download_tax_brackets_from_irs(year=2024)

        assert isinstance(result, TaxBrackets)
        assert result.year == 2024
        assert result.filing_status == "single"
        assert len(result.brackets) == 3

    @patch('retirement_planner.data.tax_data.requests.get')
    def test_download_tax_brackets_from_irs_with_save(self, mock_get):
        """Test downloading tax brackets and saving to file."""
        # Mock the HTTP response with HTML containing tax bracket data
        mock_response = MagicMock()
        mock_response.raise_for_status.return_value = None
        mock_response.content = b"""
        <html><body>
        <table>
            <tr><td>$0 - $11,600</td><td>10%</td></tr>
            <tr><td>$11,600 - $47,150</td><td>12%</td></tr>
        </table>
        </body></html>
        """
        mock_get.return_value = mock_response

        loader = TaxDataLoader()

        with tempfile.NamedTemporaryFile(suffix='.json', delete=False) as f:
            temp_file = f.name

        try:
            result = loader.download_tax_brackets_from_irs(
                year=2024,
                file_path=temp_file
            )
            assert isinstance(result, TaxBrackets)
            assert Path(temp_file).exists()
        finally:
            Path(temp_file).unlink(missing_ok=True)

    @patch('retirement_planner.data.tax_data.requests.get')
    def test_download_tax_brackets_from_irs_unsupported_year(self, mock_get):
        """Test downloading tax brackets for unsupported year."""
        loader = TaxDataLoader()

        with pytest.raises(DataError, match="Failed to download.*not available for year"):
            loader.download_tax_brackets_from_irs(year=2020)

    @patch('retirement_planner.data.tax_data.requests.get')
    def test_download_tax_brackets_from_irs_network_error(self, mock_get):
        """Test downloading tax brackets with network error."""
        # Mock network error
        mock_get.side_effect = Exception("Network error")

        loader = TaxDataLoader()

        with pytest.raises(DataError, match="Failed to download"):
            loader.download_tax_brackets_from_irs(year=2024)

    @patch('retirement_planner.data.tax_data.requests.get')
    def test_download_social_security_data_from_ssa(self, mock_get):
        """Test downloading Social Security data from SSA."""
        # Mock the HTTP response with HTML containing SSA data
        mock_response = MagicMock()
        mock_response.raise_for_status.return_value = None
        mock_response.content = b"""
        <html><body>
        <p>The COLA rate for 2024 is 3.2 percent.</p>
        <p>Maximum taxable earnings: $168,600</p>
        </body></html>
        """
        mock_get.return_value = mock_response

        loader = TaxDataLoader()

        # Test download without saving
        result = loader.download_social_security_data_from_ssa(year=2024)

        assert isinstance(result, SocialSecurityData)
        assert result.year == 2024
        assert result.cola_rate == 0.032  # 3.2% converted to decimal

    @patch('retirement_planner.data.tax_data.requests.get')
    def test_download_social_security_data_from_ssa_with_save(self, mock_get):
        """Test downloading Social Security data and saving to file."""
        # Mock the HTTP response with HTML containing SSA data
        mock_response = MagicMock()
        mock_response.raise_for_status.return_value = None
        mock_response.content = b"""
        <html><body>
        <p>The COLA rate for 2024 is 3.2 percent.</p>
        </body></html>
        """
        mock_get.return_value = mock_response

        loader = TaxDataLoader()

        with tempfile.NamedTemporaryFile(suffix='.json', delete=False) as f:
            temp_file = f.name

        try:
            result = loader.download_social_security_data_from_ssa(
                year=2024,
                file_path=temp_file
            )
            assert isinstance(result, SocialSecurityData)
            assert Path(temp_file).exists()
        finally:
            Path(temp_file).unlink(missing_ok=True)

    @patch('retirement_planner.data.tax_data.requests.get')
    def test_download_social_security_data_from_ssa_unsupported_year(self, mock_get):
        """Test downloading Social Security data for unsupported year."""
        loader = TaxDataLoader()

        with pytest.raises(DataError, match="Failed to download.*not available for year"):
            loader.download_social_security_data_from_ssa(year=2020)

    @patch('retirement_planner.data.tax_data.requests.get')
    def test_download_social_security_data_from_ssa_network_error(self, mock_get):
        """Test downloading Social Security data with network error."""
        # Mock network error
        mock_get.side_effect = Exception("Network error")

        loader = TaxDataLoader()

        with pytest.raises(DataError, match="Failed to download"):
            loader.download_social_security_data_from_ssa(year=2024)