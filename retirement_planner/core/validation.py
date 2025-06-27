"""
Validation framework for the retirement planner package.

This module provides a comprehensive validation system for input data,
business rules, and configuration parameters.
"""

from typing import Any, Dict, List, Optional, Callable, Union, Type
from dataclasses import dataclass, field
from abc import ABC, abstractmethod
import re
from decimal import Decimal

from .exceptions import ValidationError, create_validation_error


@dataclass(frozen=True)
class ValidationResult:
    """Result of a validation operation."""

    is_valid: bool
    errors: List[ValidationError] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)

    def __bool__(self) -> bool:
        """Return True if validation passed."""
        return self.is_valid

    def add_error(self, error: ValidationError) -> 'ValidationResult':
        """Add an error and return new result."""
        return ValidationResult(
            is_valid=False,
            errors=self.errors + [error],
            warnings=self.warnings,
        )

    def add_warning(self, warning: str) -> 'ValidationResult':
        """Add a warning and return new result."""
        return ValidationResult(
            is_valid=self.is_valid,
            errors=self.errors,
            warnings=self.warnings + [warning],
        )

    def merge(self, other: 'ValidationResult') -> 'ValidationResult':
        """Merge with another validation result."""
        return ValidationResult(
            is_valid=self.is_valid and other.is_valid,
            errors=self.errors + other.errors,
            warnings=self.warnings + other.warnings,
        )


class ValidationRule(ABC):
    """Abstract base class for validation rules."""

    def __init__(self, field_name: str, description: str = ""):
        """
        Initialize validation rule.

        Args:
            field_name: Name of the field being validated
            description: Description of the validation rule
        """
        self.field_name = field_name
        self.description = description

    @abstractmethod
    def validate(self, value: Any) -> ValidationResult:
        """
        Validate a value.

        Args:
            value: Value to validate

        Returns:
            ValidationResult indicating success/failure
        """
        pass  # pragma: no cover

    def __call__(self, value: Any) -> ValidationResult:
        """Allow rules to be called directly."""
        return self.validate(value)


class FieldValidator:
    """Validator for individual fields with multiple rules."""

    def __init__(self, field_name: str):
        """
        Initialize field validator.

        Args:
            field_name: Name of the field being validated
        """
        self.field_name = field_name
        self.rules: List[ValidationRule] = []

    def add_rule(self, rule: ValidationRule) -> 'FieldValidator':
        """Add a validation rule."""
        self.rules.append(rule)
        return self

    def validate(self, value: Any) -> ValidationResult:
        """
        Validate a value against all rules.

        Args:
            value: Value to validate

        Returns:
            ValidationResult with all errors and warnings
        """
        result = ValidationResult(is_valid=True)

        for rule in self.rules:
            rule_result = rule.validate(value)
            result = result.merge(rule_result)

            # Stop on first error if rule fails
            if not rule_result.is_valid:
                break

        return result


class BusinessRuleValidator:
    """Validator for business rules that span multiple fields."""

    def __init__(self, rule_name: str):
        """
        Initialize business rule validator.

        Args:
            rule_name: Name of the business rule
        """
        self.rule_name = rule_name
        self.validation_functions: List[Callable[[Dict[str, Any]], ValidationResult]] = []

    def add_rule(self, validation_func: Callable[[Dict[str, Any]], ValidationResult]) -> 'BusinessRuleValidator':
        """Add a business rule validation function."""
        self.validation_functions.append(validation_func)
        return self

    def validate(self, data: Dict[str, Any]) -> ValidationResult:
        """
        Validate data against all business rules.

        Args:
            data: Dictionary of field values to validate

        Returns:
            ValidationResult with all errors and warnings
        """
        result = ValidationResult(is_valid=True)

        for validation_func in self.validation_functions:
            rule_result = validation_func(data)
            result = result.merge(rule_result)

        return result


class Validator:
    """Main validator class that coordinates field and business rule validation."""

    def __init__(self):
        """Initialize validator."""
        self.field_validators: Dict[str, FieldValidator] = {}
        self.business_rules: List[BusinessRuleValidator] = []

    def add_field_validator(self, field_name: str) -> FieldValidator:
        """Add a field validator."""
        if field_name not in self.field_validators:
            self.field_validators[field_name] = FieldValidator(field_name)
        return self.field_validators[field_name]

    def add_business_rule(self, rule_name: str) -> BusinessRuleValidator:
        """Add a business rule validator."""
        business_rule = BusinessRuleValidator(rule_name)
        self.business_rules.append(business_rule)
        return business_rule

    def validate(self, data: Dict[str, Any]) -> ValidationResult:
        """
        Validate data against all field validators and business rules.

        Args:
            data: Dictionary of field values to validate

        Returns:
            ValidationResult with all errors and warnings
        """
        result = ValidationResult(is_valid=True)

        # Validate individual fields
        for field_name, validator in self.field_validators.items():
            if field_name in data:
                field_result = validator.validate(data[field_name])
                result = result.merge(field_result)
            else:
                # Field is missing - this might be an error depending on requirements
                pass

        # Validate business rules
        for business_rule in self.business_rules:
            rule_result = business_rule.validate(data)
            result = result.merge(rule_result)

        return result


# Common validation rules
class RequiredRule(ValidationRule):
    """Rule to ensure a field is not None or empty."""

    def validate(self, value: Any) -> ValidationResult:
        if value is None:
            return ValidationResult(
                is_valid=False,
                errors=[create_validation_error(
                    "Field is required",
                    field_name=self.field_name,
                    value=value,
                    constraint="not None"
                )]
            )

        if isinstance(value, str) and not value.strip():
            return ValidationResult(
                is_valid=False,
                errors=[create_validation_error(
                    "Field cannot be empty",
                    field_name=self.field_name,
                    value=value,
                    constraint="non-empty string"
                )]
            )

        return ValidationResult(is_valid=True)


class TypeRule(ValidationRule):
    """Rule to ensure a field is of the correct type."""

    def __init__(self, field_name: str, expected_type: Union[Type, List[Type]], description: str = ""):
        super().__init__(field_name, description)
        self.expected_type = expected_type

    def validate(self, value: Any) -> ValidationResult:
        if value is None:
            return ValidationResult(is_valid=True)  # None is handled by RequiredRule

        expected_types = [self.expected_type] if not isinstance(self.expected_type, list) else self.expected_type

        if not any(isinstance(value, t) for t in expected_types):
            type_names = [t.__name__ for t in expected_types]
            return ValidationResult(
                is_valid=False,
                errors=[create_validation_error(
                    f"Expected type(s): {', '.join(type_names)}",
                    field_name=self.field_name,
                    value=value,
                    expected_type=', '.join(type_names)
                )]
            )

        return ValidationResult(is_valid=True)


class RangeRule(ValidationRule):
    """Rule to ensure a numeric field is within a range."""

    def __init__(self, field_name: str, min_value: Optional[float] = None, max_value: Optional[float] = None, description: str = ""):
        super().__init__(field_name, description)
        self.min_value = min_value
        self.max_value = max_value

    def validate(self, value: Any) -> ValidationResult:
        if value is None:
            return ValidationResult(is_valid=True)

        if not isinstance(value, (int, float, Decimal)):
            return ValidationResult(
                is_valid=False,
                errors=[create_validation_error(
                    "Value must be numeric",
                    field_name=self.field_name,
                    value=value,
                    expected_type="numeric"
                )]
            )

        numeric_value = float(value)

        if self.min_value is not None and numeric_value < self.min_value:
            return ValidationResult(
                is_valid=False,
                errors=[create_validation_error(
                    f"Value must be >= {self.min_value}",
                    field_name=self.field_name,
                    value=value,
                    constraint=f">= {self.min_value}"
                )]
            )

        if self.max_value is not None and numeric_value > self.max_value:
            return ValidationResult(
                is_valid=False,
                errors=[create_validation_error(
                    f"Value must be <= {self.max_value}",
                    field_name=self.field_name,
                    value=value,
                    constraint=f"<= {self.max_value}"
                )]
            )

        return ValidationResult(is_valid=True)


class AgeRule(ValidationRule):
    """Rule to validate age values."""

    def __init__(self, field_name: str, min_age: int = 0, max_age: int = 120, description: str = ""):
        super().__init__(field_name, description)
        self.min_age = min_age
        self.max_age = max_age

    def validate(self, value: Any) -> ValidationResult:
        if value is None:
            return ValidationResult(is_valid=True)

        if not isinstance(value, int):
            return ValidationResult(
                is_valid=False,
                errors=[create_validation_error(
                    "Age must be an integer",
                    field_name=self.field_name,
                    value=value,
                    expected_type="integer"
                )]
            )

        if value < self.min_age or value > self.max_age:
            return ValidationResult(
                is_valid=False,
                errors=[create_validation_error(
                    f"Age must be between {self.min_age} and {self.max_age}",
                    field_name=self.field_name,
                    value=value,
                    constraint=f"{self.min_age} <= age <= {self.max_age}"
                )]
            )

        return ValidationResult(is_valid=True)


class PercentageRule(ValidationRule):
    """Rule to validate percentage values (0-100)."""

    def __init__(self, field_name: str, min_percentage: float = 0.0, max_percentage: float = 100.0, description: str = ""):
        super().__init__(field_name, description)
        self.min_percentage = min_percentage
        self.max_percentage = max_percentage

    def validate(self, value: Any) -> ValidationResult:
        if value is None:
            return ValidationResult(is_valid=True)

        if not isinstance(value, (int, float, Decimal)):
            return ValidationResult(
                is_valid=False,
                errors=[create_validation_error(
                    "Percentage must be numeric",
                    field_name=self.field_name,
                    value=value,
                    expected_type="numeric"
                )]
            )

        numeric_value = float(value)

        if numeric_value < self.min_percentage or numeric_value > self.max_percentage:
            return ValidationResult(
                is_valid=False,
                errors=[create_validation_error(
                    f"Percentage must be between {self.min_percentage}% and {self.max_percentage}%",
                    field_name=self.field_name,
                    value=value,
                    constraint=f"{self.min_percentage}% <= percentage <= {self.max_percentage}%"
                )]
            )

        return ValidationResult(is_valid=True)


class RegexRule(ValidationRule):
    """Rule to validate string values against a regex pattern."""

    def __init__(self, field_name: str, pattern: str, description: str = ""):
        super().__init__(field_name, description)
        self.pattern = pattern
        self.regex = re.compile(pattern)

    def validate(self, value: Any) -> ValidationResult:
        if value is None:
            return ValidationResult(is_valid=True)

        if not isinstance(value, str):
            return ValidationResult(
                is_valid=False,
                errors=[create_validation_error(
                    "Value must be a string",
                    field_name=self.field_name,
                    value=value,
                    expected_type="string"
                )]
            )

        if not self.regex.match(value):
            return ValidationResult(
                is_valid=False,
                errors=[create_validation_error(
                    f"Value does not match pattern: {self.pattern}",
                    field_name=self.field_name,
                    value=value,
                    constraint=f"matches {self.pattern}"
                )]
            )

        return ValidationResult(is_valid=True)


class ChoiceRule(ValidationRule):
    """Rule to validate that a value is one of the allowed choices."""

    def __init__(self, field_name: str, choices: List[Any], description: str = ""):
        super().__init__(field_name, description)
        self.choices = choices

    def validate(self, value: Any) -> ValidationResult:
        if value is None:
            return ValidationResult(is_valid=True)

        if value not in self.choices:
            return ValidationResult(
                is_valid=False,
                errors=[create_validation_error(
                    f"Value must be one of: {self.choices}",
                    field_name=self.field_name,
                    value=value,
                    constraint=f"in {self.choices}"
                )]
            )

        return ValidationResult(is_valid=True)