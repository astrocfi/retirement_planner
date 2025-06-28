"""
Person model for retirement planning.

Contains classes for person profiles and goals.
"""

from dataclasses import dataclass, field
from typing import List, Optional, Dict, Any
from datetime import date
from retirement_planner.core.validation import Validator, RequiredRule, RangeRule, ChoiceRule
from retirement_planner.core.exceptions import ValidationError


@dataclass(frozen=True)
class Goal:
    """Represents a retirement planning goal."""
    name: str
    target_amount: float
    target_age: int
    priority: str  # essential, important, nice_to_have
    goal_type: str  # income, legacy, purchase, lifestyle, min_portfolio_value
    inflation_adjusted: bool = True
    description: Optional[str] = None

    def __post_init__(self):
        """Validate goal data."""
        validator = Validator()
        validator.add_field_validator('name').add_rule(RequiredRule('name'))
        validator.add_field_validator('target_amount').add_rule(RangeRule('target_amount', min_value=0))
        validator.add_field_validator('target_age').add_rule(RangeRule('target_age', min_value=0, max_value=120))
        validator.add_field_validator('priority').add_rule(ChoiceRule('priority', ['essential', 'important', 'nice_to_have']))
        validator.add_field_validator('goal_type').add_rule(ChoiceRule('goal_type', ['income', 'legacy', 'purchase', 'lifestyle', 'min_portfolio_value']))

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
    """Person profile for retirement planning with age, goals, and basic information."""
    name: str
    age: int
    retirement_age: int
    life_expectancy: int
    risk_tolerance: str  # conservative, moderate, aggressive
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
        validator.add_field_validator('risk_tolerance').add_rule(ChoiceRule('risk_tolerance', ['conservative', 'moderate', 'aggressive']))
        validator.add_field_validator('tax_filing_status').add_rule(ChoiceRule('tax_filing_status', ['single', 'married', 'head_of_household']))

        if self.retirement_age < self.age:
            raise ValidationError("Retirement age must be at least current age")

        if self.life_expectancy <= self.retirement_age:
            raise ValidationError("Life expectancy must be after retirement age")

        result = validator.validate({
            'name': self.name,
            'age': self.age,
            'retirement_age': self.retirement_age,
            'life_expectancy': self.life_expectancy,
            'risk_tolerance': self.risk_tolerance,
            'tax_filing_status': self.tax_filing_status
        })

        if not result.is_valid:
            raise ValidationError(f"Person validation failed: {result.errors}")

    def get_working_years(self) -> int:
        """Calculate years until retirement."""
        return self.retirement_age - self.age

    def get_retirement_years(self) -> int:
        """Calculate years in retirement."""
        return self.life_expectancy - self.retirement_age

    def get_essential_goals(self) -> List[Goal]:
        """Get all essential goals."""
        return [goal for goal in self.goals if goal.priority == "essential"]