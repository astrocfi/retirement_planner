"""
Data validation and quality checking for retirement planning.

This module provides functionality to validate data quality, detect outliers,
and ensure data integrity for market data, tax data, and other financial information.
"""

import numpy as np
import pandas as pd
from datetime import date, datetime
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple, Union, Any, Set
from pathlib import Path
import json

from ..core.exceptions import DataError
from ..core.validation import Validator, RequiredRule, TypeRule, RangeRule
from ..utils.math_utils import StatisticalUtils


class ValidationResult:
    """Result of data validation operations."""

    def __init__(self):
        """Initialize validation result."""
        self.is_valid = True
        self.errors = []
        self.warnings = []
        self.outliers = []
        self.quality_metrics = {}

    def add_error(self, error: str) -> None:
        """Add an error message."""
        self.errors.append(error)
        self.is_valid = False

    def add_warning(self, warning: str) -> None:
        """Add a warning message."""
        self.warnings.append(warning)

    def add_outlier(self, outlier_info: Dict[str, Any]) -> None:
        """Add outlier information."""
        self.outliers.append(outlier_info)

    def add_quality_metric(self, metric_name: str, value: float) -> None:
        """Add a quality metric."""
        self.quality_metrics[metric_name] = value

    def merge(self, other: 'ValidationResult') -> 'ValidationResult':
        """Merge with another validation result."""
        merged = ValidationResult()
        merged.is_valid = self.is_valid and other.is_valid
        merged.errors = self.errors + other.errors
        merged.warnings = self.warnings + other.warnings
        merged.outliers = self.outliers + other.outliers
        merged.quality_metrics = {**self.quality_metrics, **other.quality_metrics}
        return merged

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "is_valid": self.is_valid,
            "errors": self.errors,
            "warnings": self.warnings,
            "outliers": self.outliers,
            "quality_metrics": self.quality_metrics
        }


class OutlierDetector:
    """Detect outliers in data using various statistical methods."""

    def __init__(self, method: str = "zscore", threshold: float = 3.0):
        """
        Initialize outlier detector.

        Args:
            method: Detection method ('zscore', 'iqr', 'modified_zscore')
            threshold: Threshold for outlier detection
        """
        if method not in ["zscore", "iqr", "modified_zscore"]:
            raise ValueError(f"Unknown outlier detection method: {method}")

        if threshold <= 0:
            raise ValueError("Threshold must be positive")

        self.method = method
        self.threshold = threshold

    def detect_outliers(self, data: Union[List, np.ndarray, pd.Series]) -> List[int]:
        """
        Detect outliers in the data.

        Args:
            data: Input data (list, numpy array, or pandas series)

        Returns:
            List of indices where outliers are found
        """
        if isinstance(data, pd.Series):
            data = data.values
        elif isinstance(data, list):
            data = np.array(data)

        if self.method == "zscore":
            return self._detect_zscore_outliers(data)
        elif self.method == "iqr":
            return self._detect_iqr_outliers(data)
        elif self.method == "modified_zscore":
            return self._detect_modified_zscore_outliers(data)

    def _detect_zscore_outliers(self, data: np.ndarray) -> List[int]:
        """Detect outliers using Z-score method."""
        mean = np.mean(data)
        std = np.std(data)

        if std == 0:
            return []

        z_scores = np.abs((data - mean) / std)
        return np.where(z_scores > self.threshold)[0].tolist()

    def _detect_iqr_outliers(self, data: np.ndarray) -> List[int]:
        """Detect outliers using IQR method."""
        q1 = np.percentile(data, 25)
        q3 = np.percentile(data, 75)
        iqr = q3 - q1

        if iqr == 0:
            return []

        lower_bound = q1 - self.threshold * iqr
        upper_bound = q3 + self.threshold * iqr

        return np.where((data < lower_bound) | (data > upper_bound))[0].tolist()

    def _detect_modified_zscore_outliers(self, data: np.ndarray) -> List[int]:
        """Detect outliers using modified Z-score method."""
        median = np.median(data)
        mad = np.median(np.abs(data - median))

        if mad == 0:
            return []

        modified_z_scores = 0.6745 * (data - median) / mad
        return np.where(np.abs(modified_z_scores) > self.threshold)[0].tolist()

    def get_outlier_info(self, data: Union[List, np.ndarray, pd.Series], column_name: str) -> List[Dict[str, Any]]:
        """
        Get detailed information about outliers.

        Args:
            data: Input data
            column_name: Name of the column being analyzed

        Returns:
            List of dictionaries with outlier information
        """
        outlier_indices = self.detect_outliers(data)
        outlier_info = []

        if isinstance(data, pd.Series):
            data_values = data.values
        elif isinstance(data, list):
            data_values = np.array(data)
        else:
            data_values = data

        for idx in outlier_indices:
            info = {
                "index": int(idx),
                "value": float(data_values[idx]),
                "column": column_name,
                "method": self.method,
                "threshold": self.threshold
            }

            # Add method-specific information
            if self.method == "zscore":
                mean = np.mean(data_values)
                std = np.std(data_values)
                info["z_score"] = float((data_values[idx] - mean) / std)
            elif self.method == "iqr":
                q1 = np.percentile(data_values, 25)
                q3 = np.percentile(data_values, 75)
                info["iqr"] = float(q3 - q1)
                info["q1"] = float(q1)
                info["q3"] = float(q3)

            outlier_info.append(info)

        return outlier_info


class DataQualityChecker:
    """Check data quality and consistency."""

    def __init__(self):
        """Initialize data quality checker."""
        pass

    def check_completeness(self, data: pd.DataFrame) -> Dict[str, Any]:
        """
        Check data completeness.

        Args:
            data: DataFrame to check

        Returns:
            Dictionary with completeness metrics
        """
        total_cells = data.size
        missing_cells = data.isnull().sum().sum()
        overall_completeness = (total_cells - missing_cells) / total_cells if total_cells > 0 else 0.0

        column_completeness = {}
        for column in data.columns:
            missing_count = data[column].isnull().sum()
            total_count = len(data[column])
            completeness = (total_count - missing_count) / total_count if total_count > 0 else 0.0

            column_completeness[column] = {
                "missing_count": int(missing_count),
                "total_count": int(total_count),
                "completeness": float(completeness)
            }

        return {
            "overall_completeness": float(overall_completeness),
            "total_cells": int(total_cells),
            "missing_cells": int(missing_cells),
            "column_completeness": column_completeness
        }

    def check_consistency(self, data: pd.DataFrame) -> Dict[str, Any]:
        """
        Check data consistency.

        Args:
            data: DataFrame to check

        Returns:
            Dictionary with consistency metrics
        """
        # Check for duplicate rows
        duplicate_rows = data.duplicated()
        duplicate_count = duplicate_rows.sum()

        # Check for constant columns
        constant_columns = []
        for column in data.columns:
            if data[column].nunique() == 1:
                constant_columns.append(column)

        # Check for negative values in numeric columns
        negative_values = []
        for column in data.select_dtypes(include=[np.number]).columns:
            negative_count = (data[column] < 0).sum()
            if negative_count > 0:
                negative_values.append({
                    "column": column,
                    "negative_count": int(negative_count)
                })

        return {
            "duplicate_rows": {
                "count": int(duplicate_count),
                "indices": duplicate_rows[duplicate_rows].index.tolist()
            },
            "constant_columns": constant_columns,
            "negative_values": negative_values
        }

    def check_distribution(self, data: pd.DataFrame) -> Dict[str, Dict[str, float]]:
        """
        Check data distribution for numeric columns.

        Args:
            data: DataFrame to check

        Returns:
            Dictionary with distribution statistics for each numeric column
        """
        distribution = {}

        for column in data.select_dtypes(include=[np.number]).columns:
            series = data[column].dropna()
            if len(series) == 0:
                continue

            # Convert to list for StatisticalUtils
            values = series.tolist()

            distribution[column] = {
                "count": int(len(values)),
                "mean": float(StatisticalUtils.calculate_mean(values)),
                "median": float(StatisticalUtils.calculate_median(values)),
                "std": float(StatisticalUtils.calculate_std_deviation(values)),
                "min": float(min(values)),
                "max": float(max(values))
            }

        return distribution

    def check_date_consistency(self, data: pd.DataFrame, date_column: str) -> Dict[str, Any]:
        """
        Check date consistency.

        Args:
            data: DataFrame to check
            date_column: Name of the date column

        Returns:
            Dictionary with date consistency metrics
        """
        if date_column not in data.columns:
            return {"error": f"Date column '{date_column}' not found"}

        try:
            # Try common date formats first, then fall back to inference
            date_formats = ['%Y-%m-%d', '%m/%d/%Y', '%d/%m/%Y', '%Y-%m-%d %H:%M:%S']
            date_series = None

            for fmt in date_formats:
                try:
                    date_series = pd.to_datetime(data[date_column], format=fmt, errors='coerce')
                    # If we get here without error, the format worked
                    break
                except (ValueError, TypeError):
                    continue

            # If no format worked, use the original method but suppress the warning
            if date_series is None:
                import warnings
                with warnings.catch_warnings():
                    warnings.simplefilter("ignore", UserWarning)
                    date_series = pd.to_datetime(data[date_column], errors='coerce')

            valid_dates = date_series.dropna()

            if len(valid_dates) == 0:
                return {"error": "No valid dates found"}

            total_rows = len(data)
            valid_count = len(valid_dates)
            invalid_count = total_rows - valid_count

            # Find gaps in dates
            valid_dates_sorted = valid_dates.sort_values()
            gaps = []
            for i in range(len(valid_dates_sorted) - 1):
                current_date = valid_dates_sorted.iloc[i]
                next_date = valid_dates_sorted.iloc[i + 1]
                if (next_date - current_date).days > 1:
                    gaps.append({
                        "start": current_date.strftime('%Y-%m-%d'),
                        "end": next_date.strftime('%Y-%m-%d'),
                        "gap_days": (next_date - current_date).days
                    })

            return {
                "total_rows": int(total_rows),
                "valid_dates": int(valid_count),
                "invalid_dates": int(invalid_count),
                "date_range": {
                    "start": valid_dates_sorted.min().strftime('%Y-%m-%d'),
                    "end": valid_dates_sorted.max().strftime('%Y-%m-%d')
                },
                "gaps": gaps
            }

        except Exception as e:
            return {"error": f"Error processing dates: {str(e)}"}


class DataValidator:
    """Main data validator that coordinates all validation operations."""

    def __init__(self):
        """Initialize data validator."""
        self.outlier_detector = OutlierDetector()
        self.quality_checker = DataQualityChecker()

    def validate_historical_returns(self, returns_data: pd.DataFrame) -> ValidationResult:
        """
        Validate historical returns data.

        Args:
            returns_data: DataFrame with historical returns

        Returns:
            ValidationResult with validation results
        """
        result = ValidationResult()

        # Check if data is empty
        if returns_data.empty:
            result.add_error("Returns data is empty")
            return result

        # Check if there are any columns
        if len(returns_data.columns) == 0:
            result.add_error("No asset columns found")
            return result

        # Check if all columns are numeric
        non_numeric_columns = returns_data.select_dtypes(exclude=[np.number]).columns
        if len(non_numeric_columns) > 0:
            result.add_error(f"Columns {list(non_numeric_columns)} are not numeric")
            return result

        # Check for extreme values
        for column in returns_data.columns:
            series = returns_data[column].dropna()
            if len(series) == 0:
                continue

            values = series.tolist()
            max_return = max(values)
            min_return = min(values)

            if max_return > 1.0:  # 100% return
                result.add_warning(f"Column {column} has returns greater than 100% (max: {max_return:.2%})")

            if min_return < -0.5:  # -50% return
                result.add_warning(f"Column {column} has returns less than -50% (min: {min_return:.2%})")

        # Check data quality
        completeness_info = self.quality_checker.check_completeness(returns_data)
        consistency_info = self.quality_checker.check_consistency(returns_data)
        distribution_info = self.quality_checker.check_distribution(returns_data)

        # Add quality metrics
        result.add_quality_metric("completeness", completeness_info["overall_completeness"])

        # Check for outliers
        for column in returns_data.columns:
            outliers = self.outlier_detector.get_outlier_info(returns_data[column], column)
            for outlier in outliers:
                result.add_outlier(outlier)

        return result

    def validate_correlation_matrix(self, correlation_data: pd.DataFrame) -> ValidationResult:
        """
        Validate correlation matrix.

        Args:
            correlation_data: DataFrame with correlation matrix

        Returns:
            ValidationResult with validation results
        """
        result = ValidationResult()

        # Check if matrix is square
        if len(correlation_data.columns) != len(correlation_data.index):
            result.add_error("Correlation matrix must be square")
            return result

        # Check if matrix is symmetric
        if not correlation_data.equals(correlation_data.T):
            result.add_error("Correlation matrix must be symmetric")

        # Check diagonal elements are 1.0
        for i, asset in enumerate(correlation_data.columns):
            if abs(correlation_data.iloc[i, i] - 1.0) > 1e-6:
                result.add_error(f"Diagonal element for {asset} must be 1.0")

        # Check values are in [-1, 1] range
        invalid_values = []
        for i in range(len(correlation_data.columns)):
            for j in range(len(correlation_data.index)):
                value = correlation_data.iloc[i, j]
                if value < -1.0 or value > 1.0:
                    invalid_values.append((i, j, value))

        if invalid_values:
            result.add_error(f"Found {len(invalid_values)} correlation values outside [-1, 1] range")

        # Check if matrix is positive definite
        try:
            np.linalg.cholesky(correlation_data.values)
        except np.linalg.LinAlgError:
            result.add_error("Correlation matrix is not positive definite")

        return result

    def validate_tax_brackets(self, brackets: List[Dict[str, Any]]) -> ValidationResult:
        """
        Validate tax brackets data.

        Args:
            brackets: List of tax bracket dictionaries

        Returns:
            ValidationResult with validation results
        """
        result = ValidationResult()

        if not brackets:
            result.add_error("No tax brackets provided")
            return result

        required_fields = ["bracket_min", "rate", "filing_status"]

        for i, bracket in enumerate(brackets):
            # Check required fields
            for field in required_fields:
                if field not in bracket:
                    result.add_error(f"Bracket {i} missing required field: {field}")

            # Check rate is valid
            if "rate" in bracket:
                rate = bracket["rate"]
                if not isinstance(rate, (int, float)) or rate < 0 or rate > 1:
                    result.add_error(f"Bracket {i} has invalid rate: {rate}")

        return result

    def validate_social_security_data(self, ss_data: Dict[str, Any]) -> ValidationResult:
        """
        Validate Social Security data.

        Args:
            ss_data: Dictionary with Social Security data

        Returns:
            ValidationResult with validation results
        """
        result = ValidationResult()

        required_fields = [
            "year", "full_retirement_age", "early_retirement_age",
            "maximum_earnings", "benefit_formula_bend_points",
            "benefit_formula_rates", "cola_rate"
        ]

        # Check required fields
        for field in required_fields:
            if field not in ss_data:
                result.add_error(f"Missing required field: {field}")

        # Check age relationship
        if "early_retirement_age" in ss_data and "full_retirement_age" in ss_data:
            if ss_data["early_retirement_age"] >= ss_data["full_retirement_age"]:
                result.add_error("Early retirement age must be less than full retirement age")

        # Check bend points and rates
        if "benefit_formula_bend_points" in ss_data and "benefit_formula_rates" in ss_data:
            bend_points = ss_data["benefit_formula_bend_points"]
            rates = ss_data["benefit_formula_rates"]
            if len(bend_points) + 1 != len(rates):
                result.add_error("Number of bend points must match number of rates")

        return result

    def generate_validation_report(self, result: ValidationResult) -> str:
        """
        Generate a human-readable validation report.

        Args:
            result: ValidationResult to report on

        Returns:
            Formatted validation report
        """
        report = []

        # Header
        status = "PASS" if result.is_valid else "FAIL"
        report.append(f"=== DATA VALIDATION REPORT [{status}] ===")
        report.append("")

        # Errors
        if result.errors:
            report.append("ERRORS:")
            for error in result.errors:
                report.append(f"  ❌ {error}")
            report.append("")

        # Warnings
        if result.warnings:
            report.append("WARNINGS:")
            for warning in result.warnings:
                report.append(f"  ⚠️  {warning}")
            report.append("")

        # Outliers
        if result.outliers:
            report.append("OUTLIERS:")
            for outlier in result.outliers:
                report.append(f"  🔍 {outlier['column']}[{outlier['index']}] = {outlier['value']}")
            report.append("")

        # Quality metrics
        if result.quality_metrics:
            report.append("QUALITY METRICS:")
            for metric, value in result.quality_metrics.items():
                report.append(f"  📊 {metric}: {value:.3f}")
            report.append("")

        return "\n".join(report)