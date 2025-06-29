"""
Unit tests for validators module.
"""

import pytest
import numpy as np
import pandas as pd
from datetime import date, datetime
from pathlib import Path
import tempfile
import json

from retirement_planner.data.validators import (
    DataValidator,
    OutlierDetector,
    DataQualityChecker,
    ValidationResult
)
from retirement_planner.core.exceptions import ValidationError


class TestValidationResult:
    """Test ValidationResult class."""

    def test_validation_result_creation(self):
        """Test creating validation result."""
        result = ValidationResult()

        assert result.is_valid is True
        assert len(result.errors) == 0
        assert len(result.warnings) == 0
        assert len(result.outliers) == 0
        assert len(result.quality_metrics) == 0

    def test_add_error(self):
        """Test adding error to validation result."""
        result = ValidationResult()

        result.add_error("Test error")

        assert result.is_valid is False
        assert len(result.errors) == 1
        assert result.errors[0] == "Test error"

    def test_add_warning(self):
        """Test adding warning to validation result."""
        result = ValidationResult()

        result.add_warning("Test warning")

        assert result.is_valid is True  # Warnings don't affect validity
        assert len(result.warnings) == 1
        assert result.warnings[0] == "Test warning"

    def test_add_outlier(self):
        """Test adding outlier information."""
        result = ValidationResult()

        outlier_info = {
            "index": 5,
            "value": 0.15,
            "column": "US_Stocks",
            "method": "zscore",
            "threshold": 3.0
        }

        result.add_outlier(outlier_info)

        assert len(result.outliers) == 1
        assert result.outliers[0] == outlier_info

    def test_add_quality_metric(self):
        """Test adding quality metric."""
        result = ValidationResult()

        result.add_quality_metric("completeness", 0.95)

        assert len(result.quality_metrics) == 1
        assert result.quality_metrics["completeness"] == 0.95

    def test_merge(self):
        """Test merging validation results."""
        result1 = ValidationResult()
        result1.add_error("Error 1")
        result1.add_warning("Warning 1")
        result1.add_quality_metric("metric1", 0.8)

        result2 = ValidationResult()
        result2.add_error("Error 2")
        result2.add_warning("Warning 2")
        result2.add_quality_metric("metric2", 0.9)

        merged = result1.merge(result2)

        assert merged.is_valid is False  # Has errors
        assert len(merged.errors) == 2
        assert len(merged.warnings) == 2
        assert len(merged.quality_metrics) == 2
        assert "Error 1" in merged.errors
        assert "Error 2" in merged.errors
        assert "Warning 1" in merged.warnings
        assert "Warning 2" in merged.warnings
        assert merged.quality_metrics["metric1"] == 0.8
        assert merged.quality_metrics["metric2"] == 0.9

    def test_to_dict(self):
        """Test converting to dictionary."""
        result = ValidationResult()
        result.add_error("Test error")
        result.add_warning("Test warning")
        result.add_outlier({"index": 1, "value": 0.1})
        result.add_quality_metric("completeness", 0.95)

        data_dict = result.to_dict()

        assert data_dict["is_valid"] is False
        assert data_dict["errors"] == ["Test error"]
        assert data_dict["warnings"] == ["Test warning"]
        assert len(data_dict["outliers"]) == 1
        assert data_dict["quality_metrics"]["completeness"] == 0.95


class TestOutlierDetector:
    """Test OutlierDetector class."""

    def test_outlier_detector_creation(self):
        """Test creating outlier detector."""
        detector = OutlierDetector(method="zscore", threshold=3.0)

        assert detector.method == "zscore"
        assert detector.threshold == 3.0

    def test_outlier_detector_creation_invalid_method(self):
        """Test creating outlier detector with invalid method."""
        with pytest.raises(ValueError, match="Unknown outlier detection method"):
            OutlierDetector(method="invalid", threshold=3.0)

    def test_outlier_detector_creation_invalid_threshold(self):
        """Test creating outlier detector with invalid threshold."""
        with pytest.raises(ValueError, match="Threshold must be positive"):
            OutlierDetector(method="zscore", threshold=0)

    def test_detect_outliers_zscore(self):
        """Test detecting outliers using Z-score method."""
        detector = OutlierDetector(method="zscore", threshold=2.0)

        # Create data with obvious outliers
        data = [1, 2, 3, 4, 5, 100, 6, 7, 8, 9, 10]

        outliers = detector.detect_outliers(data)

        assert len(outliers) == 1
        assert outliers[0] == 5  # Index of value 100

    def test_detect_outliers_iqr(self):
        """Test detecting outliers using IQR method."""
        detector = OutlierDetector(method="iqr", threshold=1.5)

        # Create data with outliers
        data = [1, 2, 3, 4, 5, 20, 6, 7, 8, 9, 10]

        outliers = detector.detect_outliers(data)

        assert len(outliers) >= 1
        assert 5 in outliers  # Index of value 20

    def test_detect_outliers_modified_zscore(self):
        """Test detecting outliers using modified Z-score method."""
        detector = OutlierDetector(method="modified_zscore", threshold=3.5)

        # Create data with outliers
        data = [1, 2, 3, 4, 5, 50, 6, 7, 8, 9, 10]

        outliers = detector.detect_outliers(data)

        assert len(outliers) >= 1
        assert 5 in outliers  # Index of value 50

    def test_detect_outliers_pandas_series(self):
        """Test detecting outliers with pandas series."""
        detector = OutlierDetector(method="zscore", threshold=2.0)

        data = pd.Series([1, 2, 3, 4, 5, 100, 6, 7, 8, 9, 10])

        outliers = detector.detect_outliers(data)

        assert len(outliers) == 1
        assert outliers[0] == 5

    def test_detect_outliers_numpy_array(self):
        """Test detecting outliers with numpy array."""
        detector = OutlierDetector(method="zscore", threshold=2.0)

        data = np.array([1, 2, 3, 4, 5, 100, 6, 7, 8, 9, 10])

        outliers = detector.detect_outliers(data)

        assert len(outliers) == 1
        assert outliers[0] == 5

    def test_get_outlier_info(self):
        """Test getting detailed outlier information."""
        detector = OutlierDetector(method="zscore", threshold=2.0)

        data = [1, 2, 3, 4, 5, 100, 6, 7, 8, 9, 10]

        outlier_info = detector.get_outlier_info(data, "test_column")

        assert len(outlier_info) == 1
        assert outlier_info[0]["index"] == 5
        assert outlier_info[0]["value"] == 100
        assert outlier_info[0]["column"] == "test_column"
        assert outlier_info[0]["method"] == "zscore"
        assert outlier_info[0]["threshold"] == 2.0
        assert "z_score" in outlier_info[0]

    def test_get_outlier_info_iqr(self):
        """Test getting outlier information with IQR method."""
        detector = OutlierDetector(method="iqr", threshold=1.5)

        data = [1, 2, 3, 4, 5, 20, 6, 7, 8, 9, 10]

        outlier_info = detector.get_outlier_info(data, "test_column")

        if len(outlier_info) > 0:
            assert "iqr" in outlier_info[0]
            assert "q1" in outlier_info[0]
            assert "q3" in outlier_info[0]


class TestDataQualityChecker:
    """Test DataQualityChecker class."""

    def test_data_quality_checker_creation(self):
        """Test creating data quality checker."""
        checker = DataQualityChecker()
        assert checker is not None

    def test_check_completeness(self):
        """Test checking data completeness."""
        checker = DataQualityChecker()

        # Create DataFrame with missing values
        data = pd.DataFrame({
            'A': [1, 2, np.nan, 4, 5],
            'B': [1, 2, 3, 4, np.nan],
            'C': [1, 2, 3, 4, 5]
        })

        completeness = checker.check_completeness(data)

        # 13 non-missing out of 15 total = 13/15 = 0.866...
        expected_completeness = 13/15
        assert abs(completeness["overall_completeness"] - expected_completeness) < 1e-10
        assert completeness["total_cells"] == 15
        assert completeness["missing_cells"] == 2
        assert completeness["column_completeness"]["A"]["missing_count"] == 1
        assert completeness["column_completeness"]["B"]["missing_count"] == 1
        assert completeness["column_completeness"]["C"]["missing_count"] == 0

    def test_check_consistency(self):
        """Test checking data consistency."""
        checker = DataQualityChecker()

        # Create DataFrame with various consistency issues
        data = pd.DataFrame({
            'A': [1, 2, 3, 4, 5],
            'B': [1, 1, 1, 1, 1],  # Constant column
            'C': [1, 2, 3, 4, 5],
            'D': [1, 2, 3, 4, 5]
        })

        # Add duplicate row
        data = pd.concat([data, data.iloc[0:1]], ignore_index=True)

        consistency = checker.check_consistency(data)

        assert consistency["duplicate_rows"]["count"] == 1
        assert consistency["constant_columns"] == ["B"]
        assert len(consistency["negative_values"]) == 0

    def test_check_consistency_with_negative_values(self):
        """Test checking consistency with negative values."""
        checker = DataQualityChecker()

        data = pd.DataFrame({
            'A': [1, -2, 3, -4, 5],
            'B': [1, 2, 3, 4, 5]
        })

        consistency = checker.check_consistency(data)

        assert len(consistency["negative_values"]) == 1
        assert consistency["negative_values"][0]["column"] == "A"
        assert consistency["negative_values"][0]["negative_count"] == 2

    def test_check_distribution(self):
        """Test checking data distribution."""
        checker = DataQualityChecker()

        # Create DataFrame with same length columns
        data = pd.DataFrame({
            'A': [1, 2, 3, 4, 5],
            'B': [1, 2, 3, 4, 5],
            'C': ['a', 'b', 'c', 'd', 'e']  # Non-numeric column
        })

        distribution = checker.check_distribution(data)

        assert 'A' in distribution
        assert 'B' in distribution
        assert 'C' not in distribution  # Non-numeric column

        assert distribution['A']['count'] == 5
        assert distribution['A']['mean'] == 3.0
        assert distribution['A']['median'] == 3.0
        assert distribution['A']['std'] > 0
        assert distribution['A']['min'] == 1
        assert distribution['A']['max'] == 5

    def test_check_date_consistency(self):
        """Test checking date consistency."""
        checker = DataQualityChecker()

        data = pd.DataFrame({
            'date': ['2020-01-01', '2020-01-02', '2020-01-04', '2020-01-05', 'invalid_date'],
            'value': [1, 2, 3, 4, 5]
        })

        date_info = checker.check_date_consistency(data, 'date')

        assert date_info["total_rows"] == 5
        assert date_info["valid_dates"] == 4
        assert date_info["invalid_dates"] == 1
        assert date_info["date_range"]["start"] == "2020-01-01"
        assert date_info["date_range"]["end"] == "2020-01-05"
        assert len(date_info["gaps"]) == 1  # Gap between 2020-01-02 and 2020-01-04

    def test_check_date_consistency_missing_column(self):
        """Test checking date consistency with missing column."""
        checker = DataQualityChecker()

        data = pd.DataFrame({
            'value': [1, 2, 3, 4, 5]
        })

        date_info = checker.check_date_consistency(data, 'date')

        assert "error" in date_info
        assert "not found" in date_info["error"]

    def test_check_date_consistency_no_valid_dates(self):
        """Test checking date consistency with no valid dates."""
        checker = DataQualityChecker()

        data = pd.DataFrame({
            'date': ['invalid1', 'invalid2', 'invalid3'],
            'value': [1, 2, 3]
        })

        date_info = checker.check_date_consistency(data, 'date')

        assert "error" in date_info
        assert "No valid dates found" in date_info["error"]


class TestDataValidator:
    """Test DataValidator class."""

    def test_data_validator_creation(self):
        """Test creating data validator."""
        validator = DataValidator()

        assert validator.outlier_detector is not None
        assert validator.quality_checker is not None

    def test_validate_historical_returns_valid_data(self):
        """Test validating valid historical returns data."""
        validator = DataValidator()

        # Create valid returns data
        dates = pd.date_range('2020-01-01', '2023-12-31', freq='ME')
        returns_data = pd.DataFrame({
            'US_Stocks': np.random.normal(0.01, 0.05, len(dates)),
            'Bonds': np.random.normal(0.005, 0.02, len(dates))
        }, index=dates)

        result = validator.validate_historical_returns(returns_data)

        assert result.is_valid is True
        assert len(result.errors) == 0
        assert len(result.quality_metrics) > 0

    def test_validate_historical_returns_empty_data(self):
        """Test validating empty historical returns data."""
        validator = DataValidator()

        returns_data = pd.DataFrame()

        result = validator.validate_historical_returns(returns_data)

        assert result.is_valid is False
        assert len(result.errors) == 1
        assert "empty" in result.errors[0]

    def test_validate_historical_returns_no_columns(self):
        """Test validating historical returns with no columns."""
        validator = DataValidator()

        # Create DataFrame with index but no columns
        returns_data = pd.DataFrame(index=pd.date_range('2020-01-01', '2023-12-31', freq='ME'))

        result = validator.validate_historical_returns(returns_data)

        assert result.is_valid is False
        assert len(result.errors) == 1
        assert "Returns data is empty" in result.errors[0]

    def test_validate_historical_returns_non_numeric_columns(self):
        """Test validating historical returns with non-numeric columns."""
        validator = DataValidator()

        dates = pd.date_range('2020-01-01', '2023-12-31', freq='ME')
        # Create DataFrame with proper length for non-numeric column
        non_numeric_data = ['a', 'b', 'c'] * (len(dates) // 3)
        if len(non_numeric_data) < len(dates):
            non_numeric_data.extend(['a'] * (len(dates) - len(non_numeric_data)))

        returns_data = pd.DataFrame({
            'US_Stocks': np.random.normal(0.01, 0.05, len(dates)),
            'Bonds': non_numeric_data[:len(dates)]  # Non-numeric
        }, index=dates)

        result = validator.validate_historical_returns(returns_data)

        assert result.is_valid is False
        assert len(result.errors) == 1
        assert "not numeric" in result.errors[0]

    def test_validate_historical_returns_extreme_values(self):
        """Test validating historical returns with extreme values."""
        validator = DataValidator()

        dates = pd.date_range('2020-01-01', '2023-12-31', freq='ME')
        returns_data = pd.DataFrame({
            'US_Stocks': [0.01, 0.02, 1.5, 0.03, 0.04],  # 150% return
            'Bonds': [0.005, 0.006, -0.6, 0.007, 0.008]  # -60% return
        }, index=dates[:5])

        result = validator.validate_historical_returns(returns_data)

        assert result.is_valid is True  # Should be valid but with warnings
        assert len(result.warnings) >= 2
        assert any("greater than 100%" in warning for warning in result.warnings)
        assert any("less than -50%" in warning for warning in result.warnings)

    def test_validate_correlation_matrix_valid(self):
        """Test validating valid correlation matrix."""
        validator = DataValidator()

        correlation_data = pd.DataFrame({
            'US_Stocks': [1.0, 0.3],
            'Bonds': [0.3, 1.0]
        }, index=['US_Stocks', 'Bonds'])

        result = validator.validate_correlation_matrix(correlation_data)

        assert result.is_valid is True
        assert len(result.errors) == 0

    def test_validate_correlation_matrix_non_square(self):
        """Test validating non-square correlation matrix."""
        validator = DataValidator()

        # Create non-square matrix by having more rows than columns
        correlation_data = pd.DataFrame({
            'US_Stocks': [1.0, 0.3, 0.5],
            'Bonds': [0.3, 1.0, 0.2]
        }, index=['US_Stocks', 'Bonds', 'Real_Estate'])  # More rows than columns

        result = validator.validate_correlation_matrix(correlation_data)

        assert result.is_valid is False
        assert len(result.errors) == 1
        assert "must be square" in result.errors[0]

    def test_validate_correlation_matrix_non_symmetric(self):
        """Test validating non-symmetric correlation matrix."""
        validator = DataValidator()

        correlation_data = pd.DataFrame({
            'US_Stocks': [1.0, 0.3],
            'Bonds': [0.5, 1.0]  # Different from 0.3
        }, index=['US_Stocks', 'Bonds'])

        result = validator.validate_correlation_matrix(correlation_data)

        assert result.is_valid is False
        assert len(result.errors) == 1
        assert "must be symmetric" in result.errors[0]

    def test_validate_correlation_matrix_invalid_diagonal(self):
        """Test validating correlation matrix with invalid diagonal."""
        validator = DataValidator()

        correlation_data = pd.DataFrame({
            'US_Stocks': [0.9, 0.3],  # Not 1.0
            'Bonds': [0.3, 1.0]
        }, index=['US_Stocks', 'Bonds'])

        result = validator.validate_correlation_matrix(correlation_data)

        assert result.is_valid is False
        assert len(result.errors) == 1
        assert "must be 1.0" in result.errors[0]

    def test_validate_correlation_matrix_invalid_range(self):
        """Test validating correlation matrix with values outside [-1, 1]."""
        validator = DataValidator()

        correlation_data = pd.DataFrame({
            'US_Stocks': [1.0, 1.5],  # > 1.0
            'Bonds': [1.5, 1.0]
        }, index=['US_Stocks', 'Bonds'])

        result = validator.validate_correlation_matrix(correlation_data)

        assert result.is_valid is False
        assert len(result.errors) >= 1
        assert "outside [-1, 1] range" in result.errors[0]

    def test_validate_correlation_matrix_not_positive_definite(self):
        """Test validating correlation matrix that's not positive definite."""
        validator = DataValidator()

        correlation_data = pd.DataFrame({
            'US_Stocks': [1.0, 1.0],  # Perfect correlation
            'Bonds': [1.0, 1.0]
        }, index=['US_Stocks', 'Bonds'])

        result = validator.validate_correlation_matrix(correlation_data)

        assert result.is_valid is False
        assert len(result.errors) == 1
        assert "not positive definite" in result.errors[0]

    def test_validate_tax_brackets_valid(self):
        """Test validating valid tax brackets."""
        validator = DataValidator()

        # Test valid tax bracket data
        valid_brackets = [
            {
                'min': 0,
                'max': 11600,
                'rate': 0.10,
                'filing_status': 'single'
            },
            {
                'min': 11600,
                'max': 47150,
                'rate': 0.12,
                'filing_status': 'single'
            }
        ]

        result = validator.validate_tax_brackets(valid_brackets)
        assert result.is_valid

        # Test invalid tax bracket data (missing required fields)
        invalid_brackets = [
            {
                'rate': 0.10  # Missing min and filing_status
            }
        ]

        result = validator.validate_tax_brackets(invalid_brackets)
        assert not result.is_valid
        assert len(result.errors) > 0

        # Test invalid tax bracket data (invalid rate)
        invalid_brackets = [
            {
                'min': 0,
                'max': 11600,
                'rate': 1.5,  # Rate > 100%
                'filing_status': 'single'
            }
        ]

        result = validator.validate_tax_brackets(invalid_brackets)
        assert not result.is_valid
        assert len(result.errors) > 0

    def test_validate_social_security_data_valid(self):
        """Test validating valid Social Security data."""
        validator = DataValidator()

        ss_data = {
            'year': 2024,
            'full_retirement_age': 67,
            'early_retirement_age': 62,
            'maximum_earnings': 168600.0,
            'benefit_formula_bend_points': [1174.0, 7078.0],
            'benefit_formula_rates': [0.90, 0.32, 0.15],
            'cola_rate': 0.032
        }

        result = validator.validate_social_security_data(ss_data)

        assert result.is_valid is True
        assert len(result.errors) == 0

    def test_validate_social_security_data_missing_fields(self):
        """Test validating Social Security data with missing fields."""
        validator = DataValidator()

        ss_data = {
            'year': 2024,
            'full_retirement_age': 67
            # Missing other required fields
        }

        result = validator.validate_social_security_data(ss_data)

        assert result.is_valid is False
        assert len(result.errors) >= 1
        assert "Missing required field" in result.errors[0]

    def test_validate_social_security_data_invalid_ages(self):
        """Test validating Social Security data with invalid ages."""
        validator = DataValidator()

        ss_data = {
            'year': 2024,
            'full_retirement_age': 65,
            'early_retirement_age': 67,  # Early > Full
            'maximum_earnings': 168600.0,
            'benefit_formula_bend_points': [1174.0, 7078.0],
            'benefit_formula_rates': [0.90, 0.32, 0.15],
            'cola_rate': 0.032
        }

        result = validator.validate_social_security_data(ss_data)

        assert result.is_valid is False
        assert len(result.errors) == 1
        assert "Early retirement age must be less than full retirement age" in result.errors[0]

    def test_validate_social_security_data_mismatched_bend_points_rates(self):
        """Test validating Social Security data with mismatched bend points and rates."""
        validator = DataValidator()

        ss_data = {
            'year': 2024,
            'full_retirement_age': 67,
            'early_retirement_age': 62,
            'maximum_earnings': 168600.0,
            'benefit_formula_bend_points': [1174.0, 7078.0],  # 2 bend points
            'benefit_formula_rates': [0.90, 0.32],  # Only 2 rates
            'cola_rate': 0.032
        }

        result = validator.validate_social_security_data(ss_data)

        assert result.is_valid is False
        assert len(result.errors) == 1
        assert "Number of bend points must match number of rates" in result.errors[0]

    def test_generate_validation_report(self):
        """Test generating validation report."""
        validator = DataValidator()

        result = ValidationResult()
        result.add_error("Test error 1")
        result.add_error("Test error 2")
        result.add_warning("Test warning")
        result.add_outlier({"index": 5, "value": 0.15, "column": "US_Stocks"})
        result.add_quality_metric("completeness", 0.95)

        report = validator.generate_validation_report(result)

        assert "FAIL" in report  # Has errors
        assert "Test error 1" in report
        assert "Test error 2" in report
        assert "Test warning" in report
        assert "US_Stocks[5]" in report
        assert "completeness" in report