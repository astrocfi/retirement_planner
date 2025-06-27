"""
Person model for retirement planning.

Contains classes for person profiles, income, expenses, and goals.
"""

from dataclasses import dataclass, field
from typing import List, Optional, Dict, Any
from datetime import date
from retirement_planner.core.validation import Validator, RequiredRule, RangeRule, ChoiceRule
from retirement_planner.core.exceptions import ValidationError


@dataclass(frozen=True)
class Income:
    """Represents an income source."""
    source: str
    amount: float
    start_age: int
    end_age: Optional[int] = None
    inflation_adjustment: bool = True
    probability: float = 1.0
    description: Optional[str] = None

    def __post_init__(self):
        """Validate income data."""
        validator = Validator()
        validator.add_field_validator('source').add_rule(RequiredRule('source'))
        validator.add_field_validator('amount').add_rule(RangeRule('amount', min_value=0))
        validator.add_field_validator('start_age').add_rule(RangeRule('start_age', min_value=0, max_value=120))
        validator.add_field_validator('end_age').add_rule(RangeRule('end_age', min_value=0, max_value=120))
        validator.add_field_validator('probability').add_rule(RangeRule('probability', min_value=0, max_value=1))

        if self.end_age and self.start_age >= self.end_age:
            raise ValidationError("End age must be after start age")

        result = validator.validate({
            'source': self.source,
            'amount': self.amount,
            'start_age': self.start_age,
            'end_age': self.end_age,
            'probability': self.probability
        })

        if not result.is_valid:
            raise ValidationError(f"Income validation failed: {result.errors}")


@dataclass(frozen=True)
class Expense:
    """Represents an expense category."""
    category: str
    amount: float
    start_age: int
    end_age: Optional[int] = None
    inflation_adjustment: bool = True
    frequency: str = "annual"  # annual, monthly, one_time
    description: Optional[str] = None

    def __post_init__(self):
        """Validate expense data."""
        validator = Validator()
        validator.add_field_validator('category').add_rule(RequiredRule('category'))
        validator.add_field_validator('amount').add_rule(RangeRule('amount', min_value=0))
        validator.add_field_validator('start_age').add_rule(RangeRule('start_age', min_value=0, max_value=120))
        validator.add_field_validator('end_age').add_rule(RangeRule('end_age', min_value=0, max_value=120))
        validator.add_field_validator('frequency').add_rule(ChoiceRule('frequency', ['annual', 'monthly', 'one_time']))

        if self.end_age and self.start_age >= self.end_age:
            raise ValidationError("End age must be after start age")

        result = validator.validate({
            'category': self.category,
            'amount': self.amount,
            'start_age': self.start_age,
            'end_age': self.end_age,
            'frequency': self.frequency
        })

        if not result.is_valid:
            raise ValidationError(f"Expense validation failed: {result.errors}")


@dataclass(frozen=True)
class Goal:
    """Represents a retirement planning goal."""
    name: str
    target_amount: float
    target_age: int
    priority: str  # essential, important, nice_to_have
    goal_type: str  # income, legacy, purchase, lifestyle
    inflation_adjusted: bool = True
    description: Optional[str] = None

    def __post_init__(self):
        """Validate goal data."""
        validator = Validator()
        validator.add_field_validator('name').add_rule(RequiredRule('name'))
        validator.add_field_validator('target_amount').add_rule(RangeRule('target_amount', min_value=0))
        validator.add_field_validator('target_age').add_rule(RangeRule('target_age', min_value=0, max_value=120))
        validator.add_field_validator('priority').add_rule(ChoiceRule('priority', ['essential', 'important', 'nice_to_have']))
        validator.add_field_validator('goal_type').add_rule(ChoiceRule('goal_type', ['income', 'legacy', 'purchase', 'lifestyle']))

        result = validator.validate({
            'name': self.name,
            'target_amount': self.target_amount,
            'target_age': self.target_age,
            'priority': self.priority,
            'goal_type': self.goal_type
        })

        if not result.is_valid:
            raise ValidationError(f"Goal validation failed: {result.errors}")


@dataclass(frozen=True)
class Person:
    """Person profile for retirement planning."""
    name: str
    age: int
    retirement_age: int
    life_expectancy: int
    current_savings: float
    annual_contribution: float
    risk_tolerance: str  # conservative, moderate, aggressive
    income_sources: List[Income] = field(default_factory=list)
    expenses: List[Expense] = field(default_factory=list)
    goals: List[Goal] = field(default_factory=list)
    tax_filing_status: str = "single"  # single, married, head_of_household
    state_of_residence: str = "CA"
    additional_data: Dict[str, Any] = field(default_factory=dict)

    def __post_init__(self):
        """Validate person data."""
        validator = Validator()
        validator.add_field_validator('name').add_rule(RequiredRule('name'))
        validator.add_field_validator('age').add_rule(RangeRule('age', min_value=0, max_value=120))
        validator.add_field_validator('retirement_age').add_rule(RangeRule('retirement_age', min_value=0, max_value=120))
        validator.add_field_validator('life_expectancy').add_rule(RangeRule('life_expectancy', min_value=0, max_value=120))
        validator.add_field_validator('current_savings').add_rule(RangeRule('current_savings', min_value=0))
        validator.add_field_validator('annual_contribution').add_rule(RangeRule('annual_contribution', min_value=0))
        validator.add_field_validator('risk_tolerance').add_rule(ChoiceRule('risk_tolerance', ['conservative', 'moderate', 'aggressive']))
        validator.add_field_validator('tax_filing_status').add_rule(ChoiceRule('tax_filing_status', ['single', 'married', 'head_of_household']))

        if self.retirement_age <= self.age:
            raise ValidationError("Retirement age must be after current age")

        if self.life_expectancy <= self.retirement_age:
            raise ValidationError("Life expectancy must be after retirement age")

        result = validator.validate({
            'name': self.name,
            'age': self.age,
            'retirement_age': self.retirement_age,
            'life_expectancy': self.life_expectancy,
            'current_savings': self.current_savings,
            'annual_contribution': self.annual_contribution,
            'risk_tolerance': self.risk_tolerance,
            'tax_filing_status': self.tax_filing_status
        })

        if not result.is_valid:
            raise ValidationError(f"Person validation failed: {result.errors}")

    def get_total_income_at_age(self, age: int) -> float:
        """Calculate total income at a specific age."""
        total = 0.0
        for income in self.income_sources:
            if income.start_age <= age <= (income.end_age or 120):
                total += income.amount * income.probability
        return total

    def get_total_expenses_at_age(self, age: int) -> float:
        """Calculate total expenses at a specific age."""
        total = 0.0
        for expense in self.expenses:
            if expense.start_age <= age <= (expense.end_age or 120):
                if expense.frequency == "annual":
                    total += expense.amount
                elif expense.frequency == "monthly":
                    total += expense.amount * 12
                else:  # one_time
                    if age == expense.start_age:
                        total += expense.amount
        return total

    def get_essential_goals(self) -> List[Goal]:
        """Get all essential goals."""
        return [goal for goal in self.goals if goal.priority == "essential"]

    def get_working_years(self) -> int:
        """Calculate years until retirement."""
        return self.retirement_age - self.age

    def get_retirement_years(self) -> int:
        """Calculate years in retirement."""
        return self.life_expectancy - self.retirement_age