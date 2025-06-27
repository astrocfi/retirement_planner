"""
Exception classes for the retirement planner package.

This module defines a hierarchy of custom exceptions that provide
meaningful error messages and context for different types of errors
that can occur in retirement planning calculations.
"""

from typing import Optional, Any, Dict, List
from dataclasses import dataclass, field


@dataclass(frozen=True)
class ErrorContext:
    """Context information for error reporting."""

    field_name: Optional[str] = None
    value: Optional[Any] = None
    expected_type: Optional[str] = None
    constraint: Optional[str] = None
    file_path: Optional[str] = None
    line_number: Optional[int] = None
    additional_info: Dict[str, Any] = field(default_factory=dict)


class RetirementPlannerException(Exception):
    """
    Base exception class for all retirement planner errors.

    This class provides a common interface for all exceptions in the
    retirement planner package, including error context and formatting.
    """

    def __init__(
        self,
        message: str,
        context: Optional[ErrorContext] = None,
        original_exception: Optional[Exception] = None
    ) -> None:
        """
        Initialize the exception.

        Args:
            message: Human-readable error message
            context: Additional context about the error
            original_exception: Original exception that caused this error
        """
        super().__init__(message)
        self.message = message
        self.context = context or ErrorContext()
        self.original_exception = original_exception

    def __str__(self) -> str:
        """Return formatted error message with context."""
        error_msg = self.message

        if self.context.field_name:
            error_msg += f" (Field: {self.context.field_name})"

        if self.context.value is not None:
            error_msg += f" (Value: {self.context.value})"

        if self.context.expected_type:
            error_msg += f" (Expected: {self.context.expected_type})"

        if self.context.constraint:
            error_msg += f" (Constraint: {self.context.constraint})"

        if self.context.file_path:
            error_msg += f" (File: {self.context.file_path}"
            if self.context.line_number:
                error_msg += f":{self.context.line_number}"
            error_msg += ")"

        if self.original_exception:
            error_msg += f" (Original: {self.original_exception})"

        return error_msg

    def to_dict(self) -> Dict[str, Any]:
        """Convert exception to dictionary for serialization."""
        return {
            "type": self.__class__.__name__,
            "message": self.message,
            "context": {
                "field_name": self.context.field_name,
                "value": self.context.value,
                "expected_type": self.context.expected_type,
                "constraint": self.context.constraint,
                "file_path": self.context.file_path,
                "line_number": self.context.line_number,
                "additional_info": self.context.additional_info,
            },
            "original_exception": str(self.original_exception) if self.original_exception else None,
        }


class ValidationError(RetirementPlannerException):
    """
    Exception raised when input validation fails.

    This exception is used when user input or configuration data
    fails validation rules.
    """
    pass


class ConfigurationError(RetirementPlannerException):
    """
    Exception raised when configuration is invalid or missing.

    This exception is used when configuration files are malformed,
    missing required parameters, or contain invalid values.
    """
    pass


class DataError(RetirementPlannerException):
    """
    Exception raised when data is invalid, missing, or corrupted.

    This exception is used for market data, tax data, or other
    external data sources that are required for calculations.
    """
    pass


class SimulationError(RetirementPlannerException):
    """
    Exception raised when Monte Carlo simulation fails.

    This exception is used when simulation parameters are invalid,
    scenarios cannot be generated, or simulation execution fails.
    """
    pass


class OptimizationError(RetirementPlannerException):
    """
    Exception raised when optimization algorithms fail.

    This exception is used when optimization parameters are invalid,
    constraints cannot be satisfied, or optimization execution fails.
    """
    pass


class TaxCalculationError(RetirementPlannerException):
    """
    Exception raised when tax calculations fail.

    This exception is used when tax parameters are invalid,
    tax rules cannot be applied, or tax calculations fail.
    """
    pass


class AssetError(RetirementPlannerException):
    """
    Exception raised when asset-related operations fail.

    This exception is used when asset parameters are invalid,
    asset returns cannot be calculated, or asset operations fail.
    """
    pass


class EventError(RetirementPlannerException):
    """
    Exception raised when event processing fails.

    This exception is used when event definitions are invalid,
    events cannot be processed, or event dependencies fail.
    """
    pass


class PortfolioError(RetirementPlannerException):
    """
    Exception raised when portfolio operations fail.

    This exception is used when portfolio parameters are invalid,
    portfolio calculations fail, or portfolio constraints are violated.
    """
    pass


# Convenience functions for creating exceptions with context
def create_validation_error(
    message: str,
    field_name: Optional[str] = None,
    value: Optional[Any] = None,
    expected_type: Optional[str] = None,
    constraint: Optional[str] = None,
) -> ValidationError:
    """Create a ValidationError with context."""
    context = ErrorContext(
        field_name=field_name,
        value=value,
        expected_type=expected_type,
        constraint=constraint,
    )
    return ValidationError(message, context)


def create_configuration_error(
    message: str,
    file_path: Optional[str] = None,
    line_number: Optional[int] = None,
    field_name: Optional[str] = None,
    value: Optional[Any] = None,
) -> ConfigurationError:
    """Create a ConfigurationError with context."""
    context = ErrorContext(
        field_name=field_name,
        value=value,
        file_path=file_path,
        line_number=line_number,
    )
    return ConfigurationError(message, context)


def create_data_error(
    message: str,
    data_source: Optional[str] = None,
    field_name: Optional[str] = None,
    value: Optional[Any] = None,
) -> DataError:
    """Create a DataError with context."""
    context = ErrorContext(
        field_name=field_name,
        value=value,
        additional_info={"data_source": data_source} if data_source else {},
    )
    return DataError(message, context)