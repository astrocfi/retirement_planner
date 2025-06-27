"""
Integration tests for retirement planner core functionality.

These tests demonstrate how the exceptions and validation framework
work together in realistic retirement planning scenarios.
"""

import pytest
from retirement_planner.core.exceptions import (
    ValidationError,
    ConfigurationError,
    create_validation_error,
)
from retirement_planner.core.validation import (
    Validator,
    RequiredRule,
    TypeRule,
    RangeRule,
    AgeRule,
    PercentageRule,
    ValidationResult,
)


class TestRetirementProfileValidation:
    """Test validation of retirement profile data."""

    def test_valid_retirement_profile(self):
        """Test validation of a valid retirement profile."""
        validator = Validator()

        # Add field validators for retirement profile
        age_validator = validator.add_field_validator("current_age")
        age_validator.add_rule(RequiredRule("current_age"))
        age_validator.add_rule(AgeRule("current_age", min_age=18, max_age=80))

        retirement_age_validator = validator.add_field_validator("retirement_age")
        retirement_age_validator.add_rule(RequiredRule("retirement_age"))
        retirement_age_validator.add_rule(AgeRule("retirement_age", min_age=55, max_age=75))

        income_validator = validator.add_field_validator("annual_income")
        income_validator.add_rule(RequiredRule("annual_income"))
        income_validator.add_rule(TypeRule("annual_income", [int, float]))
        income_validator.add_rule(RangeRule("annual_income", min_value=0))

        savings_rate_validator = validator.add_field_validator("savings_rate")
        savings_rate_validator.add_rule(RequiredRule("savings_rate"))
        savings_rate_validator.add_rule(PercentageRule("savings_rate", min_percentage=0, max_percentage=50))

        # Add business rule for retirement age logic
        business_rule = validator.add_business_rule("retirement_age_logic")

        def retirement_age_logic(data):
            current_age = data.get("current_age")
            retirement_age = data.get("retirement_age")

            if current_age and retirement_age and current_age >= retirement_age:
                return ValidationResult(
                    is_valid=False,
                    errors=[ValidationError("Current age must be less than retirement age")]
                )
            return ValidationResult(is_valid=True)

        business_rule.add_rule(retirement_age_logic)

        # Valid profile data
        profile_data = {
            "current_age": 35,
            "retirement_age": 65,
            "annual_income": 100000,
            "savings_rate": 15.0,
        }

        result = validator.validate(profile_data)
        assert result.is_valid is True
        assert len(result.errors) == 0

    def test_invalid_retirement_profile(self):
        """Test validation of an invalid retirement profile."""
        validator = Validator()

        # Add field validators
        age_validator = validator.add_field_validator("current_age")
        age_validator.add_rule(RequiredRule("current_age"))
        age_validator.add_rule(AgeRule("current_age", min_age=18, max_age=80))

        retirement_age_validator = validator.add_field_validator("retirement_age")
        retirement_age_validator.add_rule(RequiredRule("retirement_age"))
        retirement_age_validator.add_rule(AgeRule("retirement_age", min_age=55, max_age=75))

        income_validator = validator.add_field_validator("annual_income")
        income_validator.add_rule(RequiredRule("annual_income"))
        income_validator.add_rule(TypeRule("annual_income", [int, float]))
        income_validator.add_rule(RangeRule("annual_income", min_value=0))

        # Add business rule
        business_rule = validator.add_business_rule("retirement_age_logic")

        def retirement_age_logic(data):
            current_age = data.get("current_age")
            retirement_age = data.get("retirement_age")

            if current_age and retirement_age and current_age >= retirement_age:
                return ValidationResult(
                    is_valid=False,
                    errors=[ValidationError("Current age must be less than retirement age")]
                )
            return ValidationResult(is_valid=True)

        business_rule.add_rule(retirement_age_logic)

        # Invalid profile data with multiple issues
        profile_data = {
            "current_age": 70,  # Too old for retirement age
            "retirement_age": 65,  # Current age > retirement age
            "annual_income": -50000,  # Negative income
        }

        result = validator.validate(profile_data)
        assert result.is_valid is False
        assert len(result.errors) >= 2  # Multiple validation errors expected

    def test_missing_required_fields(self):
        """Test validation with missing required fields."""
        validator = Validator()

        age_validator = validator.add_field_validator("current_age")
        age_validator.add_rule(RequiredRule("current_age"))
        age_validator.add_rule(AgeRule("current_age"))

        income_validator = validator.add_field_validator("annual_income")
        income_validator.add_rule(RequiredRule("annual_income"))
        income_validator.add_rule(RangeRule("annual_income", min_value=0))

        # Missing required fields
        profile_data = {
            "current_age": None,  # Missing required field
            # "annual_income" is completely missing
        }

        result = validator.validate(profile_data)
        assert result.is_valid is False
        assert len(result.errors) >= 1


class TestPortfolioAllocationValidation:
    """Test validation of portfolio allocation data."""

    def test_valid_portfolio_allocation(self):
        """Test validation of a valid portfolio allocation."""
        validator = Validator()

        # Add business rules for portfolio validation
        business_rule = validator.add_business_rule("portfolio_allocation_rules")

        def allocation_sum_rule(data):
            allocations = data.get("allocations", {})
            total = sum(allocations.values())
            if abs(total - 1.0) < 0.001:
                return ValidationResult(is_valid=True)
            else:
                return ValidationResult(
                    is_valid=False,
                    errors=[ValidationError(f"Allocations must sum to 1.0, got {total}")]
                )

        def no_negative_allocation_rule(data):
            allocations = data.get("allocations", {})
            for asset, allocation in allocations.items():
                if allocation < 0:
                    return ValidationResult(
                        is_valid=False,
                        errors=[ValidationError(f"Negative allocation for {asset}: {allocation}")]
                    )
            return ValidationResult(is_valid=True)

        def max_allocation_rule(data):
            allocations = data.get("allocations", {})
            for asset, allocation in allocations.items():
                if allocation > 0.8:  # Max 80% in any single asset
                    return ValidationResult(
                        is_valid=False,
                        errors=[ValidationError(f"Allocation too high for {asset}: {allocation}")]
                    )
            return ValidationResult(is_valid=True)

        business_rule.add_rule(allocation_sum_rule)
        business_rule.add_rule(no_negative_allocation_rule)
        business_rule.add_rule(max_allocation_rule)

        # Valid allocation data
        allocation_data = {
            "allocations": {
                "stocks": 0.6,
                "bonds": 0.3,
                "cash": 0.1,
            }
        }

        result = validator.validate(allocation_data)
        assert result.is_valid is True
        assert len(result.errors) == 0

    def test_invalid_portfolio_allocation(self):
        """Test validation of an invalid portfolio allocation."""
        validator = Validator()

        # Add business rules
        business_rule = validator.add_business_rule("portfolio_allocation_rules")

        def allocation_sum_rule(data):
            allocations = data.get("allocations", {})
            total = sum(allocations.values())
            if abs(total - 1.0) < 0.001:
                return ValidationResult(is_valid=True)
            else:
                return ValidationResult(
                    is_valid=False,
                    errors=[ValidationError(f"Allocations must sum to 1.0, got {total}")]
                )

        def no_negative_allocation_rule(data):
            allocations = data.get("allocations", {})
            for asset, allocation in allocations.items():
                if allocation < 0:
                    return ValidationResult(
                        is_valid=False,
                        errors=[ValidationError(f"Negative allocation for {asset}: {allocation}")]
                    )
            return ValidationResult(is_valid=True)

        business_rule.add_rule(allocation_sum_rule)
        business_rule.add_rule(no_negative_allocation_rule)

        # Invalid allocation data
        allocation_data = {
            "allocations": {
                "stocks": 0.6,
                "bonds": -0.1,  # Negative allocation
                "cash": 0.3,    # Sum = 0.8, not 1.0
            }
        }

        result = validator.validate(allocation_data)
        assert result.is_valid is False
        assert len(result.errors) >= 1


class TestExceptionIntegration:
    """Test integration between exceptions and validation."""

    def test_validation_error_with_context(self):
        """Test that validation errors include proper context."""
        validator = Validator()

        age_validator = validator.add_field_validator("age")
        age_validator.add_rule(AgeRule("age", min_age=18, max_age=65))

        # Test with invalid age
        result = validator.validate({"age": 16})

        assert result.is_valid is False
        assert len(result.errors) == 1

        error = result.errors[0]
        assert isinstance(error, ValidationError)
        assert "Age must be between 18 and 65" in str(error)
        assert error.context.field_name == "age"
        assert error.context.value == 16

    def test_business_rule_error_with_context(self):
        """Test that business rule errors include proper context."""
        validator = Validator()

        business_rule = validator.add_business_rule("income_expense_rule")

        def income_expense_rule(data):
            income = data.get("income", 0)
            expenses = data.get("expenses", 0)

            if income <= expenses:
                return ValidationResult(
                    is_valid=False,
                    errors=[create_validation_error(
                        "Income must exceed expenses",
                        field_name="income",
                        value=income,
                        constraint=f"income > {expenses}"
                    )]
                )
            return ValidationResult(is_valid=True)

        business_rule.add_rule(income_expense_rule)

        # Test with invalid data
        result = validator.validate({"income": 50000, "expenses": 60000})

        assert result.is_valid is False
        assert len(result.errors) == 1

        error = result.errors[0]
        assert isinstance(error, ValidationError)
        assert "Income must exceed expenses" in str(error)
        assert error.context.field_name == "income"
        assert error.context.value == 50000
        assert "income > 60000" in error.context.constraint


class TestRealWorldScenario:
    """Test a realistic retirement planning scenario."""

    def test_complete_retirement_planning_validation(self):
        """Test validation of a complete retirement planning scenario."""
        validator = Validator()

        # Personal information validation
        age_validator = validator.add_field_validator("current_age")
        age_validator.add_rule(RequiredRule("current_age"))
        age_validator.add_rule(AgeRule("current_age", min_age=18, max_age=80))

        retirement_age_validator = validator.add_field_validator("retirement_age")
        retirement_age_validator.add_rule(RequiredRule("retirement_age"))
        retirement_age_validator.add_rule(AgeRule("retirement_age", min_age=55, max_age=75))

        # Financial information validation
        income_validator = validator.add_field_validator("annual_income")
        income_validator.add_rule(RequiredRule("annual_income"))
        income_validator.add_rule(TypeRule("annual_income", [int, float]))
        income_validator.add_rule(RangeRule("annual_income", min_value=0))

        expenses_validator = validator.add_field_validator("annual_expenses")
        expenses_validator.add_rule(RequiredRule("annual_expenses"))
        expenses_validator.add_rule(TypeRule("annual_expenses", [int, float]))
        expenses_validator.add_rule(RangeRule("annual_expenses", min_value=0))

        savings_validator = validator.add_field_validator("current_savings")
        savings_validator.add_rule(RequiredRule("current_savings"))
        savings_validator.add_rule(TypeRule("current_savings", [int, float]))
        savings_validator.add_rule(RangeRule("current_savings", min_value=0))

        # Business rules
        business_rule = validator.add_business_rule("retirement_logic")

        def retirement_age_logic(data):
            current_age = data.get("current_age")
            retirement_age = data.get("retirement_age")

            if current_age and retirement_age and current_age >= retirement_age:
                return ValidationResult(
                    is_valid=False,
                    errors=[ValidationError("Current age must be less than retirement age")]
                )
            return ValidationResult(is_valid=True)

        def income_expense_logic(data):
            income = data.get("annual_income", 0)
            expenses = data.get("annual_expenses", 0)

            if income <= expenses:
                return ValidationResult(
                    is_valid=False,
                    errors=[ValidationError("Income must exceed expenses for retirement planning")]
                )
            return ValidationResult(is_valid=True)

        def savings_adequacy_logic(data):
            income = data.get("annual_income", 0)
            expenses = data.get("annual_expenses", 0)
            current_age = data.get("current_age", 0)
            retirement_age = data.get("retirement_age", 0)

            if income > 0 and expenses > 0 and current_age > 0 and retirement_age > 0:
                years_to_retirement = retirement_age - current_age
                annual_savings_needed = (expenses * 25) / years_to_retirement  # 4% rule

                if annual_savings_needed > income * 0.8:  # More than 80% of income (more realistic)
                    return ValidationResult(
                        is_valid=False,
                        errors=[ValidationError("Required savings rate is too high")]
                    )
            return ValidationResult(is_valid=True)

        business_rule.add_rule(retirement_age_logic)
        business_rule.add_rule(income_expense_logic)
        business_rule.add_rule(savings_adequacy_logic)

        # Valid retirement planning data
        planning_data = {
            "current_age": 35,
            "retirement_age": 65,
            "annual_income": 100000,
            "annual_expenses": 70000,
            "current_savings": 200000,
        }

        result = validator.validate(planning_data)
        assert result.is_valid is True
        assert len(result.errors) == 0
        assert len(result.warnings) == 0

    def test_invalid_retirement_planning_scenario(self):
        """Test validation of an invalid retirement planning scenario."""
        validator = Validator()

        # Add the same validators as above
        age_validator = validator.add_field_validator("current_age")
        age_validator.add_rule(RequiredRule("current_age"))
        age_validator.add_rule(AgeRule("current_age", min_age=18, max_age=80))

        retirement_age_validator = validator.add_field_validator("retirement_age")
        retirement_age_validator.add_rule(RequiredRule("retirement_age"))
        retirement_age_validator.add_rule(AgeRule("retirement_age", min_age=55, max_age=75))

        income_validator = validator.add_field_validator("annual_income")
        income_validator.add_rule(RequiredRule("annual_income"))
        income_validator.add_rule(TypeRule("annual_income", [int, float]))
        income_validator.add_rule(RangeRule("annual_income", min_value=0))

        expenses_validator = validator.add_field_validator("annual_expenses")
        expenses_validator.add_rule(RequiredRule("annual_expenses"))
        expenses_validator.add_rule(TypeRule("annual_expenses", [int, float]))
        expenses_validator.add_rule(RangeRule("annual_expenses", min_value=0))

        # Add business rules
        business_rule = validator.add_business_rule("retirement_logic")

        def retirement_age_logic(data):
            current_age = data.get("current_age")
            retirement_age = data.get("retirement_age")

            if current_age and retirement_age and current_age >= retirement_age:
                return ValidationResult(
                    is_valid=False,
                    errors=[ValidationError("Current age must be less than retirement age")]
                )
            return ValidationResult(is_valid=True)

        def income_expense_logic(data):
            income = data.get("annual_income", 0)
            expenses = data.get("annual_expenses", 0)

            if income <= expenses:
                return ValidationResult(
                    is_valid=False,
                    errors=[ValidationError("Income must exceed expenses for retirement planning")]
                )
            return ValidationResult(is_valid=True)

        business_rule.add_rule(retirement_age_logic)
        business_rule.add_rule(income_expense_logic)

        # Invalid planning data with multiple issues
        planning_data = {
            "current_age": 70,  # Too old for retirement age
            "retirement_age": 65,  # Current age > retirement age
            "annual_income": 50000,
            "annual_expenses": 60000,  # Expenses > income
        }

        result = validator.validate(planning_data)
        assert result.is_valid is False
        assert len(result.errors) >= 2  # Multiple validation errors expected