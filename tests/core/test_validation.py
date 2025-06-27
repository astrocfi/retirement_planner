"""
Unit tests for retirement planner validation framework.

These tests verify the validation rules, field validators, business rule
validators, and the main validator class work correctly.
"""

import pytest
from decimal import Decimal
from retirement_planner.core.validation import (
    ValidationResult,
    ValidationRule,
    FieldValidator,
    BusinessRuleValidator,
    Validator,
    RequiredRule,
    TypeRule,
    RangeRule,
    AgeRule,
    PercentageRule,
    RegexRule,
    ChoiceRule,
)
from retirement_planner.core.exceptions import ValidationError


class TestValidationResult:
    """Test ValidationResult functionality."""

    def test_validation_result_creation(self):
        """Test creating ValidationResult with various states."""
        # Valid result
        result = ValidationResult(is_valid=True)
        assert result.is_valid is True
        assert result.errors == []
        assert result.warnings == []

        # Invalid result
        result = ValidationResult(is_valid=False)
        assert result.is_valid is False
        assert result.errors == []
        assert result.warnings == []

    def test_validation_result_boolean_conversion(self):
        """Test ValidationResult boolean conversion."""
        valid_result = ValidationResult(is_valid=True)
        invalid_result = ValidationResult(is_valid=False)

        assert bool(valid_result) is True
        assert bool(invalid_result) is False

    def test_validation_result_add_error(self):
        """Test adding errors to ValidationResult."""
        result = ValidationResult(is_valid=True)
        error = ValidationError("Test error")

        new_result = result.add_error(error)

        assert new_result.is_valid is False
        assert len(new_result.errors) == 1
        assert new_result.errors[0] == error
        assert new_result.warnings == []

    def test_validation_result_add_warning(self):
        """Test adding warnings to ValidationResult."""
        result = ValidationResult(is_valid=True)

        new_result = result.add_warning("Test warning")

        assert new_result.is_valid is True
        assert new_result.errors == []
        assert len(new_result.warnings) == 1
        assert new_result.warnings[0] == "Test warning"

    def test_validation_result_merge(self):
        """Test merging ValidationResults."""
        result1 = ValidationResult(is_valid=True)
        result1 = result1.add_warning("Warning 1")

        result2 = ValidationResult(is_valid=False)
        result2 = result2.add_error(ValidationError("Error 1"))
        result2 = result2.add_warning("Warning 2")

        merged = result1.merge(result2)

        assert merged.is_valid is False  # False AND True = False
        assert len(merged.errors) == 1
        assert len(merged.warnings) == 2
        assert "Warning 1" in merged.warnings
        assert "Warning 2" in merged.warnings


class TestValidationRule:
    """Test ValidationRule abstract base class."""

    def test_validation_rule_creation(self):
        """Test creating a concrete ValidationRule."""
        class TestRule(ValidationRule):
            def validate(self, value):
                if value == "valid":
                    return ValidationResult(is_valid=True)
                else:
                    return ValidationResult(
                        is_valid=False,
                        errors=[ValidationError("Invalid value")]
                    )

        rule = TestRule("test_field", "Test rule description")
        assert rule.field_name == "test_field"
        assert rule.description == "Test rule description"

    def test_validation_rule_callable(self):
        """Test that ValidationRule can be called directly."""
        class TestRule(ValidationRule):
            def validate(self, value):
                if value > 0:
                    return ValidationResult(is_valid=True)
                else:
                    return ValidationResult(
                        is_valid=False,
                        errors=[ValidationError("Value must be positive")]
                    )

        rule = TestRule("test_field")
        result = rule(5)  # Call directly
        assert result.is_valid is True

        result = rule(-1)  # Call directly
        assert result.is_valid is False


class TestRequiredRule:
    """Test RequiredRule validation."""

    def test_required_rule_valid_values(self):
        """Test RequiredRule with valid values."""
        rule = RequiredRule("test_field")

        # Valid values
        assert rule.validate("hello").is_valid is True
        assert rule.validate(42).is_valid is True
        assert rule.validate(0).is_valid is True
        assert rule.validate(False).is_valid is True

    def test_required_rule_none_value(self):
        """Test RequiredRule with None value."""
        rule = RequiredRule("test_field")
        result = rule.validate(None)

        assert result.is_valid is False
        assert len(result.errors) == 1
        assert "Field is required" in str(result.errors[0])

    def test_required_rule_empty_string(self):
        """Test RequiredRule with empty string."""
        rule = RequiredRule("test_field")
        result = rule.validate("")

        assert result.is_valid is False
        assert len(result.errors) == 1
        assert "Field cannot be empty" in str(result.errors[0])

    def test_required_rule_whitespace_string(self):
        """Test RequiredRule with whitespace-only string."""
        rule = RequiredRule("test_field")
        result = rule.validate("   ")

        assert result.is_valid is False
        assert len(result.errors) == 1
        assert "Field cannot be empty" in str(result.errors[0])


class TestTypeRule:
    """Test TypeRule validation."""

    def test_type_rule_single_type_valid(self):
        """Test TypeRule with single type and valid value."""
        rule = TypeRule("test_field", int)
        result = rule.validate(42)

        assert result.is_valid is True

    def test_type_rule_single_type_invalid(self):
        """Test TypeRule with single type and invalid value."""
        rule = TypeRule("test_field", int)
        result = rule.validate("42")

        assert result.is_valid is False
        assert len(result.errors) == 1
        assert "Expected type(s): int" in str(result.errors[0])

    def test_type_rule_multiple_types_valid(self):
        """Test TypeRule with multiple types and valid value."""
        rule = TypeRule("test_field", [int, float])
        result = rule.validate(42)

        assert result.is_valid is True

        result = rule.validate(42.0)
        assert result.is_valid is True

    def test_type_rule_multiple_types_invalid(self):
        """Test TypeRule with multiple types and invalid value."""
        rule = TypeRule("test_field", [int, float])
        result = rule.validate("42")

        assert result.is_valid is False
        assert len(result.errors) == 1
        assert "Expected type(s): int, float" in str(result.errors[0])

    def test_type_rule_none_value(self):
        """Test TypeRule with None value (should pass)."""
        rule = TypeRule("test_field", int)
        result = rule.validate(None)

        assert result.is_valid is True  # None is handled by RequiredRule


class TestRangeRule:
    """Test RangeRule validation."""

    def test_range_rule_min_only_valid(self):
        """Test RangeRule with minimum value only."""
        rule = RangeRule("test_field", min_value=0)

        assert rule.validate(5).is_valid is True
        assert rule.validate(0).is_valid is True

    def test_range_rule_min_only_invalid(self):
        """Test RangeRule with minimum value only and invalid value."""
        rule = RangeRule("test_field", min_value=0)
        result = rule.validate(-1)

        assert result.is_valid is False
        assert len(result.errors) == 1
        assert "Value must be >= 0" in str(result.errors[0])

    def test_range_rule_max_only_valid(self):
        """Test RangeRule with maximum value only."""
        rule = RangeRule("test_field", max_value=100)

        assert rule.validate(50).is_valid is True
        assert rule.validate(100).is_valid is True

    def test_range_rule_max_only_invalid(self):
        """Test RangeRule with maximum value only and invalid value."""
        rule = RangeRule("test_field", max_value=100)
        result = rule.validate(150)

        assert result.is_valid is False
        assert len(result.errors) == 1
        assert "Value must be <= 100" in str(result.errors[0])

    def test_range_rule_min_max_valid(self):
        """Test RangeRule with both minimum and maximum values."""
        rule = RangeRule("test_field", min_value=0, max_value=100)

        assert rule.validate(50).is_valid is True
        assert rule.validate(0).is_valid is True
        assert rule.validate(100).is_valid is True

    def test_range_rule_min_max_invalid(self):
        """Test RangeRule with both minimum and maximum values and invalid values."""
        rule = RangeRule("test_field", min_value=0, max_value=100)

        result = rule.validate(-1)
        assert result.is_valid is False
        assert "Value must be >= 0" in str(result.errors[0])

        result = rule.validate(150)
        assert result.is_valid is False
        assert "Value must be <= 100" in str(result.errors[0])

    def test_range_rule_non_numeric(self):
        """Test RangeRule with non-numeric value."""
        rule = RangeRule("test_field", min_value=0, max_value=100)
        result = rule.validate("50")

        assert result.is_valid is False
        assert len(result.errors) == 1
        assert "Value must be numeric" in str(result.errors[0])

    def test_range_rule_decimal(self):
        """Test RangeRule with Decimal values."""
        rule = RangeRule("test_field", min_value=0.0, max_value=1.0)

        assert rule.validate(Decimal("0.5")).is_valid is True
        assert rule.validate(Decimal("0.0")).is_valid is True
        assert rule.validate(Decimal("1.0")).is_valid is True

    def test_range_rule_none_value(self):
        """Test RangeRule with None value (should pass)."""
        rule = RangeRule("test_field", min_value=0, max_value=100)
        result = rule.validate(None)

        assert result.is_valid is True  # None is handled by RequiredRule


class TestAgeRule:
    """Test AgeRule validation."""

    def test_age_rule_valid_ages(self):
        """Test AgeRule with valid ages."""
        rule = AgeRule("age")

        assert rule.validate(25).is_valid is True
        assert rule.validate(0).is_valid is True
        assert rule.validate(120).is_valid is True

    def test_age_rule_invalid_ages(self):
        """Test AgeRule with invalid ages."""
        rule = AgeRule("age")

        result = rule.validate(-1)
        assert result.is_valid is False
        assert "Age must be between 0 and 120" in str(result.errors[0])

        result = rule.validate(150)
        assert result.is_valid is False
        assert "Age must be between 0 and 120" in str(result.errors[0])

    def test_age_rule_custom_range(self):
        """Test AgeRule with custom age range."""
        rule = AgeRule("age", min_age=18, max_age=65)

        assert rule.validate(25).is_valid is True
        assert rule.validate(18).is_valid is True
        assert rule.validate(65).is_valid is True

        result = rule.validate(16)
        assert result.is_valid is False
        assert "Age must be between 18 and 65" in str(result.errors[0])

    def test_age_rule_non_integer(self):
        """Test AgeRule with non-integer value."""
        rule = AgeRule("age")
        result = rule.validate(25.5)

        assert result.is_valid is False
        assert len(result.errors) == 1
        assert "Age must be an integer" in str(result.errors[0])

    def test_age_rule_none_value(self):
        """Test AgeRule with None value (should pass)."""
        rule = AgeRule("age")
        result = rule.validate(None)

        assert result.is_valid is True  # None is handled by RequiredRule


class TestPercentageRule:
    """Test PercentageRule validation."""

    def test_percentage_rule_valid_percentages(self):
        """Test PercentageRule with valid percentages."""
        rule = PercentageRule("percentage")

        assert rule.validate(50.0).is_valid is True
        assert rule.validate(0.0).is_valid is True
        assert rule.validate(100.0).is_valid is True
        assert rule.validate(25).is_valid is True

    def test_percentage_rule_invalid_percentages(self):
        """Test PercentageRule with invalid percentages."""
        rule = PercentageRule("percentage")

        result = rule.validate(-1.0)
        assert result.is_valid is False
        assert "Percentage must be between 0.0% and 100.0%" in str(result.errors[0])

        result = rule.validate(150.0)
        assert result.is_valid is False
        assert "Percentage must be between 0.0% and 100.0%" in str(result.errors[0])

    def test_percentage_rule_custom_range(self):
        """Test PercentageRule with custom percentage range."""
        rule = PercentageRule("percentage", min_percentage=10.0, max_percentage=90.0)

        assert rule.validate(50.0).is_valid is True
        assert rule.validate(10.0).is_valid is True
        assert rule.validate(90.0).is_valid is True

        result = rule.validate(5.0)
        assert result.is_valid is False
        assert "Percentage must be between 10.0% and 90.0%" in str(result.errors[0])

    def test_percentage_rule_non_numeric(self):
        """Test PercentageRule with non-numeric value."""
        rule = PercentageRule("percentage")
        result = rule.validate("50")

        assert result.is_valid is False
        assert len(result.errors) == 1
        assert "Percentage must be numeric" in str(result.errors[0])

    def test_percentage_rule_decimal(self):
        """Test PercentageRule with Decimal values."""
        rule = PercentageRule("percentage")

        assert rule.validate(Decimal("50.5")).is_valid is True
        assert rule.validate(Decimal("0.0")).is_valid is True
        assert rule.validate(Decimal("100.0")).is_valid is True

    def test_percentage_rule_none_value(self):
        """Test PercentageRule with None value (should pass)."""
        rule = PercentageRule("percentage")
        result = rule.validate(None)

        assert result.is_valid is True  # None is handled by RequiredRule


class TestRegexRule:
    """Test RegexRule validation."""

    def test_regex_rule_valid_pattern(self):
        """Test RegexRule with valid pattern match."""
        rule = RegexRule("email", r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$")

        assert rule.validate("user@example.com").is_valid is True
        assert rule.validate("test.email+tag@domain.co.uk").is_valid is True

    def test_regex_rule_invalid_pattern(self):
        """Test RegexRule with invalid pattern match."""
        rule = RegexRule("email", r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$")
        result = rule.validate("invalid-email")

        assert result.is_valid is False
        assert len(result.errors) == 1
        assert "Value does not match pattern" in str(result.errors[0])

    def test_regex_rule_non_string(self):
        """Test RegexRule with non-string value."""
        rule = RegexRule("email", r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$")
        result = rule.validate(123)

        assert result.is_valid is False
        assert len(result.errors) == 1
        assert "Value must be a string" in str(result.errors[0])

    def test_regex_rule_none_value(self):
        """Test RegexRule with None value (should pass)."""
        rule = RegexRule("email", r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$")
        result = rule.validate(None)

        assert result.is_valid is True  # None is handled by RequiredRule

    def test_regex_rule_simple_pattern(self):
        """Test RegexRule with simple pattern."""
        rule = RegexRule("code", r"^[A-Z]{3}\d{3}$")

        assert rule.validate("ABC123").is_valid is True
        assert rule.validate("XYZ789").is_valid is True

        result = rule.validate("AB123")  # Missing one letter
        assert result.is_valid is False


class TestChoiceRule:
    """Test ChoiceRule validation."""

    def test_choice_rule_valid_choice(self):
        """Test ChoiceRule with valid choice."""
        rule = ChoiceRule("status", ["active", "inactive", "pending"])

        assert rule.validate("active").is_valid is True
        assert rule.validate("inactive").is_valid is True
        assert rule.validate("pending").is_valid is True

    def test_choice_rule_invalid_choice(self):
        """Test ChoiceRule with invalid choice."""
        rule = ChoiceRule("status", ["active", "inactive", "pending"])
        result = rule.validate("unknown")

        assert result.is_valid is False
        assert len(result.errors) == 1
        assert "Value must be one of: ['active', 'inactive', 'pending']" in str(result.errors[0])

    def test_choice_rule_numeric_choices(self):
        """Test ChoiceRule with numeric choices."""
        rule = ChoiceRule("level", [1, 2, 3, 4, 5])

        assert rule.validate(1).is_valid is True
        assert rule.validate(5).is_valid is True

        result = rule.validate(6)
        assert result.is_valid is False

    def test_choice_rule_none_value(self):
        """Test ChoiceRule with None value (should pass)."""
        rule = ChoiceRule("status", ["active", "inactive"])
        result = rule.validate(None)

        assert result.is_valid is True  # None is handled by RequiredRule


class TestFieldValidator:
    """Test FieldValidator functionality."""

    def test_field_validator_creation(self):
        """Test creating FieldValidator."""
        validator = FieldValidator("test_field")
        assert validator.field_name == "test_field"
        assert validator.rules == []

    def test_field_validator_add_rule(self):
        """Test adding rules to FieldValidator."""
        validator = FieldValidator("test_field")
        rule = RequiredRule("test_field")

        result = validator.add_rule(rule)
        assert result is validator  # Should return self for chaining
        assert len(validator.rules) == 1
        assert validator.rules[0] == rule

    def test_field_validator_validate_single_rule(self):
        """Test FieldValidator with single rule."""
        validator = FieldValidator("test_field")
        validator.add_rule(RequiredRule("test_field"))

        assert validator.validate("value").is_valid is True
        assert validator.validate(None).is_valid is False

    def test_field_validator_validate_multiple_rules(self):
        """Test FieldValidator with multiple rules."""
        validator = FieldValidator("age")
        validator.add_rule(RequiredRule("age"))
        validator.add_rule(TypeRule("age", int))
        validator.add_rule(RangeRule("age", min_value=0, max_value=120))

        assert validator.validate(25).is_valid is True
        assert validator.validate(None).is_valid is False  # Required rule fails
        assert validator.validate("25").is_valid is False  # Type rule fails
        assert validator.validate(150).is_valid is False  # Range rule fails

    def test_field_validator_stop_on_first_error(self):
        """Test that FieldValidator stops on first error."""
        validator = FieldValidator("age")
        validator.add_rule(RequiredRule("age"))
        validator.add_rule(TypeRule("age", int))
        validator.add_rule(RangeRule("age", min_value=0, max_value=120))

        result = validator.validate(None)
        assert result.is_valid is False
        assert len(result.errors) == 1  # Only RequiredRule error, not TypeRule or RangeRule


class TestBusinessRuleValidator:
    """Test BusinessRuleValidator functionality."""

    def test_business_rule_validator_creation(self):
        """Test creating BusinessRuleValidator."""
        validator = BusinessRuleValidator("test_rule")
        assert validator.rule_name == "test_rule"
        assert validator.validation_functions == []

    def test_business_rule_validator_add_rule(self):
        """Test adding validation functions to BusinessRuleValidator."""
        validator = BusinessRuleValidator("test_rule")

        def validation_func(data):
            if data.get("income", 0) > data.get("expenses", 0):
                return ValidationResult(is_valid=True)
            else:
                return ValidationResult(
                    is_valid=False,
                    errors=[ValidationError("Income must exceed expenses")]
                )

        result = validator.add_rule(validation_func)
        assert result is validator  # Should return self for chaining
        assert len(validator.validation_functions) == 1

    def test_business_rule_validator_validate_single_rule(self):
        """Test BusinessRuleValidator with single validation function."""
        validator = BusinessRuleValidator("income_expense_rule")

        def income_expense_rule(data):
            if data.get("income", 0) > data.get("expenses", 0):
                return ValidationResult(is_valid=True)
            else:
                return ValidationResult(
                    is_valid=False,
                    errors=[ValidationError("Income must exceed expenses")]
                )

        validator.add_rule(income_expense_rule)

        # Valid data
        result = validator.validate({"income": 100000, "expenses": 80000})
        assert result.is_valid is True

        # Invalid data
        result = validator.validate({"income": 50000, "expenses": 60000})
        assert result.is_valid is False
        assert len(result.errors) == 1
        assert "Income must exceed expenses" in str(result.errors[0])

    def test_business_rule_validator_validate_multiple_rules(self):
        """Test BusinessRuleValidator with multiple validation functions."""
        validator = BusinessRuleValidator("portfolio_rules")

        def allocation_sum_rule(data):
            total = sum(data.get("allocations", {}).values())
            if abs(total - 1.0) < 0.001:
                return ValidationResult(is_valid=True)
            else:
                return ValidationResult(
                    is_valid=False,
                    errors=[ValidationError("Allocations must sum to 1.0")]
                )

        def no_negative_allocation_rule(data):
            allocations = data.get("allocations", {})
            for asset, allocation in allocations.items():
                if allocation < 0:
                    return ValidationResult(
                        is_valid=False,
                        errors=[ValidationError(f"Negative allocation for {asset}")]
                    )
            return ValidationResult(is_valid=True)

        validator.add_rule(allocation_sum_rule)
        validator.add_rule(no_negative_allocation_rule)

        # Valid data
        result = validator.validate({"allocations": {"stocks": 0.6, "bonds": 0.4}})
        assert result.is_valid is True

        # Invalid data - allocations don't sum to 1.0
        result = validator.validate({"allocations": {"stocks": 0.6, "bonds": 0.3}})
        assert result.is_valid is False
        assert len(result.errors) == 1
        assert "Allocations must sum to 1.0" in str(result.errors[0])

        # Invalid data - negative allocation
        result = validator.validate({"allocations": {"stocks": 0.6, "bonds": -0.1, "cash": 0.5}})
        assert result.is_valid is False
        assert len(result.errors) == 1
        assert "Negative allocation for bonds" in str(result.errors[0])


class TestValidator:
    """Test main Validator class functionality."""

    def test_validator_creation(self):
        """Test creating Validator."""
        validator = Validator()
        assert validator.field_validators == {}
        assert validator.business_rules == []

    def test_validator_add_field_validator(self):
        """Test adding field validators."""
        validator = Validator()
        field_validator = validator.add_field_validator("age")

        assert isinstance(field_validator, FieldValidator)
        assert field_validator.field_name == "age"
        assert "age" in validator.field_validators

    def test_validator_add_business_rule(self):
        """Test adding business rules."""
        validator = Validator()
        business_rule = validator.add_business_rule("test_rule")

        assert isinstance(business_rule, BusinessRuleValidator)
        assert business_rule.rule_name == "test_rule"
        assert len(validator.business_rules) == 1

    def test_validator_validate_field_only(self):
        """Test Validator with field validation only."""
        validator = Validator()
        age_validator = validator.add_field_validator("age")
        age_validator.add_rule(RequiredRule("age"))
        age_validator.add_rule(AgeRule("age"))

        # Valid data
        result = validator.validate({"age": 25})
        assert result.is_valid is True

        # Invalid data
        result = validator.validate({"age": 150})
        assert result.is_valid is False
        assert len(result.errors) == 1

    def test_validator_validate_business_rules_only(self):
        """Test Validator with business rules only."""
        validator = Validator()
        business_rule = validator.add_business_rule("income_expense_rule")

        def income_expense_rule(data):
            if data.get("income", 0) > data.get("expenses", 0):
                return ValidationResult(is_valid=True)
            else:
                return ValidationResult(
                    is_valid=False,
                    errors=[ValidationError("Income must exceed expenses")]
                )

        business_rule.add_rule(income_expense_rule)

        # Valid data
        result = validator.validate({"income": 100000, "expenses": 80000})
        assert result.is_valid is True

        # Invalid data
        result = validator.validate({"income": 50000, "expenses": 60000})
        assert result.is_valid is False
        assert len(result.errors) == 1

    def test_validator_validate_combined(self):
        """Test Validator with both field and business rule validation."""
        validator = Validator()

        # Add field validators
        age_validator = validator.add_field_validator("age")
        age_validator.add_rule(RequiredRule("age"))
        age_validator.add_rule(AgeRule("age"))

        income_validator = validator.add_field_validator("income")
        income_validator.add_rule(RequiredRule("income"))
        income_validator.add_rule(RangeRule("income", min_value=0))

        # Add business rule
        business_rule = validator.add_business_rule("income_expense_rule")

        def income_expense_rule(data):
            if data.get("income", 0) > data.get("expenses", 0):
                return ValidationResult(is_valid=True)
            else:
                return ValidationResult(
                    is_valid=False,
                    errors=[ValidationError("Income must exceed expenses")]
                )

        business_rule.add_rule(income_expense_rule)

        # Valid data
        result = validator.validate({
            "age": 30,
            "income": 100000,
            "expenses": 80000
        })
        assert result.is_valid is True

        # Invalid data - field validation fails
        result = validator.validate({
            "age": 150,  # Invalid age
            "income": 100000,
            "expenses": 80000
        })
        assert result.is_valid is False
        assert len(result.errors) >= 1

        # Invalid data - business rule fails
        result = validator.validate({
            "age": 30,
            "income": 50000,
            "expenses": 60000  # Expenses > income
        })
        assert result.is_valid is False
        assert len(result.errors) >= 1

    def test_validator_missing_fields(self):
        """Test Validator behavior with missing fields."""
        validator = Validator()
        age_validator = validator.add_field_validator("age")
        age_validator.add_rule(RequiredRule("age"))

        # Missing field should not cause error (field validators only validate present fields)
        result = validator.validate({})
        assert result.is_valid is True  # No validation errors since field is not present