"""
Unit tests for retirement planner exceptions.

These tests verify the exception hierarchy, error context handling,
and convenience functions work correctly.
"""

import pytest
import dataclasses
from retirement_planner.core.exceptions import (
    RetirementPlannerException,
    ValidationError,
    ConfigurationError,
    DataError,
    SimulationError,
    OptimizationError,
    TaxCalculationError,
    AssetError,
    EventError,
    PortfolioError,
    ErrorContext,
    create_validation_error,
    create_configuration_error,
    create_data_error,
)


class TestErrorContext:
    """Test ErrorContext dataclass functionality."""

    def test_error_context_creation(self):
        """Test creating ErrorContext with various parameters."""
        context = ErrorContext(
            field_name="age",
            value=25,
            expected_type="integer",
            constraint="0 <= age <= 120",
            file_path="config.yaml",
            line_number=10,
            additional_info={"source": "user_input"}
        )

        assert context.field_name == "age"
        assert context.value == 25
        assert context.expected_type == "integer"
        assert context.constraint == "0 <= age <= 120"
        assert context.file_path == "config.yaml"
        assert context.line_number == 10
        assert context.additional_info == {"source": "user_input"}

    def test_error_context_defaults(self):
        """Test ErrorContext with default values."""
        context = ErrorContext()

        assert context.field_name is None
        assert context.value is None
        assert context.expected_type is None
        assert context.constraint is None
        assert context.file_path is None
        assert context.line_number is None
        assert context.additional_info == {}

    def test_error_context_immutability(self):
        """Test that ErrorContext is immutable."""
        context = ErrorContext(field_name="test")

        # Should not be able to modify fields
        with pytest.raises(dataclasses.FrozenInstanceError):
            context.field_name = "new_value"


class TestRetirementPlannerException:
    """Test base exception class functionality."""

    def test_exception_creation(self):
        """Test creating base exception with message."""
        exception = RetirementPlannerException("Test error message")

        assert str(exception) == "Test error message"
        assert exception.message == "Test error message"
        assert exception.context is not None
        assert exception.original_exception is None

    def test_exception_with_context(self):
        """Test creating exception with error context."""
        context = ErrorContext(field_name="age", value=150, constraint="0 <= age <= 120")
        exception = RetirementPlannerException("Invalid age", context)

        assert "Field: age" in str(exception)
        assert "Value: 150" in str(exception)
        assert "Constraint: 0 <= age <= 120" in str(exception)

    def test_exception_with_original_exception(self):
        """Test creating exception with original exception."""
        original = ValueError("Original error")
        exception = RetirementPlannerException("Wrapper error", original_exception=original)

        assert "Original: Original error" in str(exception)
        assert exception.original_exception == original

    def test_exception_to_dict(self):
        """Test converting exception to dictionary."""
        context = ErrorContext(field_name="test", value=42)
        exception = RetirementPlannerException("Test error", context)

        result = exception.to_dict()

        assert result["type"] == "RetirementPlannerException"
        assert result["message"] == "Test error"
        assert result["context"]["field_name"] == "test"
        assert result["context"]["value"] == 42
        assert result["original_exception"] is None

    def test_exception_to_dict_with_original(self):
        """Test converting exception with original exception to dictionary."""
        original = ValueError("Original")
        exception = RetirementPlannerException("Wrapper", original_exception=original)

        result = exception.to_dict()

        assert result["original_exception"] == "Original"


class TestExceptionHierarchy:
    """Test the exception hierarchy and inheritance."""

    def test_exception_inheritance(self):
        """Test that all exceptions inherit from base class."""
        exceptions = [
            ValidationError,
            ConfigurationError,
            DataError,
            SimulationError,
            OptimizationError,
            TaxCalculationError,
            AssetError,
            EventError,
            PortfolioError,
        ]

        for exception_class in exceptions:
            assert issubclass(exception_class, RetirementPlannerException)

    def test_validation_error(self):
        """Test ValidationError specific functionality."""
        error = ValidationError("Invalid input")
        assert isinstance(error, RetirementPlannerException)
        assert "Invalid input" in str(error)

    def test_configuration_error(self):
        """Test ConfigurationError specific functionality."""
        error = ConfigurationError("Config file not found")
        assert isinstance(error, RetirementPlannerException)
        assert "Config file not found" in str(error)

    def test_data_error(self):
        """Test DataError specific functionality."""
        error = DataError("Market data unavailable")
        assert isinstance(error, RetirementPlannerException)
        assert "Market data unavailable" in str(error)

    def test_simulation_error(self):
        """Test SimulationError specific functionality."""
        error = SimulationError("Simulation failed to converge")
        assert isinstance(error, RetirementPlannerException)
        assert "Simulation failed to converge" in str(error)

    def test_optimization_error(self):
        """Test OptimizationError specific functionality."""
        error = OptimizationError("Optimization constraints violated")
        assert isinstance(error, RetirementPlannerException)
        assert "Optimization constraints violated" in str(error)

    def test_tax_calculation_error(self):
        """Test TaxCalculationError specific functionality."""
        error = TaxCalculationError("Invalid tax bracket")
        assert isinstance(error, RetirementPlannerException)
        assert "Invalid tax bracket" in str(error)

    def test_asset_error(self):
        """Test AssetError specific functionality."""
        error = AssetError("Asset return calculation failed")
        assert isinstance(error, RetirementPlannerException)
        assert "Asset return calculation failed" in str(error)

    def test_event_error(self):
        """Test EventError specific functionality."""
        error = EventError("Event processing failed")
        assert isinstance(error, RetirementPlannerException)
        assert "Event processing failed" in str(error)

    def test_portfolio_error(self):
        """Test PortfolioError specific functionality."""
        error = PortfolioError("Portfolio allocation invalid")
        assert isinstance(error, RetirementPlannerException)
        assert "Portfolio allocation invalid" in str(error)


class TestConvenienceFunctions:
    """Test convenience functions for creating exceptions."""

    def test_create_validation_error(self):
        """Test create_validation_error function."""
        error = create_validation_error(
            "Age must be positive",
            field_name="age",
            value=-5,
            expected_type="positive integer",
            constraint="age > 0"
        )

        assert isinstance(error, ValidationError)
        assert error.message == "Age must be positive"
        assert error.context.field_name == "age"
        assert error.context.value == -5
        assert error.context.expected_type == "positive integer"
        assert error.context.constraint == "age > 0"

    def test_create_configuration_error(self):
        """Test create_configuration_error function."""
        error = create_configuration_error(
            "Missing required field",
            file_path="config.yaml",
            line_number=15,
            field_name="retirement_age",
            value=None
        )

        assert isinstance(error, ConfigurationError)
        assert error.message == "Missing required field"
        assert error.context.file_path == "config.yaml"
        assert error.context.line_number == 15
        assert error.context.field_name == "retirement_age"
        assert error.context.value is None

    def test_create_data_error(self):
        """Test create_data_error function."""
        error = create_data_error(
            "Market data unavailable",
            data_source="Yahoo Finance",
            field_name="stock_price",
            value=None
        )

        assert isinstance(error, DataError)
        assert error.message == "Market data unavailable"
        assert error.context.additional_info["data_source"] == "Yahoo Finance"
        assert error.context.field_name == "stock_price"
        assert error.context.value is None

    def test_create_validation_error_minimal(self):
        """Test create_validation_error with minimal parameters."""
        error = create_validation_error("Simple error")

        assert isinstance(error, ValidationError)
        assert error.message == "Simple error"
        assert error.context.field_name is None
        assert error.context.value is None

    def test_create_configuration_error_minimal(self):
        """Test create_configuration_error with minimal parameters."""
        error = create_configuration_error("Config error")

        assert isinstance(error, ConfigurationError)
        assert error.message == "Config error"
        assert error.context.file_path is None
        assert error.context.line_number is None

    def test_create_data_error_minimal(self):
        """Test create_data_error with minimal parameters."""
        error = create_data_error("Data error")

        assert isinstance(error, DataError)
        assert error.message == "Data error"
        assert error.context.additional_info == {}


class TestExceptionStringRepresentation:
    """Test exception string representation with various contexts."""

    def test_exception_with_all_context_fields(self):
        """Test exception string representation with all context fields populated."""
        context = ErrorContext(
            field_name="retirement_age",
            value=65,
            expected_type="integer",
            constraint="55 <= age <= 75",
            file_path="user_config.yaml",
            line_number=25,
            additional_info={"section": "personal_info"}
        )

        exception = ValidationError("Invalid retirement age", context)
        error_str = str(exception)

        assert "Invalid retirement age" in error_str
        assert "(Field: retirement_age)" in error_str
        assert "(Value: 65)" in error_str
        assert "(Expected: integer)" in error_str
        assert "(Constraint: 55 <= age <= 75)" in error_str
        assert "(File: user_config.yaml:25)" in error_str

    def test_exception_with_partial_context(self):
        """Test exception string representation with partial context."""
        context = ErrorContext(field_name="income", value=100000)
        exception = ValidationError("Income too high", context)
        error_str = str(exception)

        assert "Income too high" in error_str
        assert "(Field: income)" in error_str
        assert "(Value: 100000)" in error_str
        assert "(Expected:" not in error_str  # Should not appear if None
        assert "(Constraint:" not in error_str  # Should not appear if None

    def test_exception_with_original_exception(self):
        """Test exception string representation with original exception."""
        original = ValueError("Cannot convert string to int")
        exception = ValidationError("Validation failed", original_exception=original)
        error_str = str(exception)

        assert "Validation failed" in error_str
        assert "(Original: Cannot convert string to int)" in error_str


class TestExceptionSerialization:
    """Test exception serialization to dictionary format."""

    def test_exception_serialization_complete(self):
        """Test complete exception serialization."""
        context = ErrorContext(
            field_name="portfolio_allocation",
            value={"stocks": 0.8, "bonds": 0.2},
            expected_type="dict",
            constraint="sum of allocations = 1.0",
            file_path="portfolio.json",
            line_number=10,
            additional_info={"risk_level": "moderate"}
        )

        exception = PortfolioError("Invalid allocation", context)
        result = exception.to_dict()

        assert result["type"] == "PortfolioError"
        assert result["message"] == "Invalid allocation"
        assert result["context"]["field_name"] == "portfolio_allocation"
        assert result["context"]["value"] == {"stocks": 0.8, "bonds": 0.2}
        assert result["context"]["expected_type"] == "dict"
        assert result["context"]["constraint"] == "sum of allocations = 1.0"
        assert result["context"]["file_path"] == "portfolio.json"
        assert result["context"]["line_number"] == 10
        assert result["context"]["additional_info"] == {"risk_level": "moderate"}

    def test_exception_serialization_minimal(self):
        """Test minimal exception serialization."""
        exception = ValidationError("Simple error")
        result = exception.to_dict()

        assert result["type"] == "ValidationError"
        assert result["message"] == "Simple error"
        assert result["context"]["field_name"] is None
        assert result["context"]["value"] is None
        assert result["original_exception"] is None