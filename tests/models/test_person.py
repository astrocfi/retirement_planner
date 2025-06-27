"""
Unit tests for Person model and related classes.

Tests the Person and Goal classes with semantic behavior focus.
Note: Income and Expense classes have been removed in favor of the Event system.
"""

import pytest
from retirement_planner.models.person import Person, Goal
from retirement_planner.core.exceptions import ValidationError


class TestGoal:
    """Test Goal class functionality."""

    def test_goal_creation_valid(self):
        """Test creating a valid goal."""
        goal = Goal(
            name="Retirement Income",
            target_amount=80000,
            target_age=65,
            priority="essential",
            goal_type="income"
        )
        assert goal.name == "Retirement Income"
        assert goal.target_amount == 80000
        assert goal.priority == "essential"
        assert goal.goal_type == "income"

    def test_goal_creation_legacy(self):
        """Test creating legacy goal."""
        goal = Goal(
            name="Leave Inheritance",
            target_amount=500000,
            target_age=85,
            priority="important",
            goal_type="legacy"
        )
        assert goal.goal_type == "legacy"
        assert goal.priority == "important"

    def test_goal_validation_invalid_priority(self):
        """Test goal validation with invalid priority."""
        with pytest.raises(ValidationError, match="Goal validation failed"):
            Goal(
                name="Test Goal",
                target_amount=100000,
                target_age=65,
                priority="critical",
                goal_type="income"
            )

    def test_goal_validation_invalid_type(self):
        """Test goal validation with invalid goal type."""
        with pytest.raises(ValidationError, match="Goal validation failed"):
            Goal(
                name="Test Goal",
                target_amount=100000,
                target_age=65,
                priority="essential",
                goal_type="invalid"
            )


class TestPerson:
    """Test Person class functionality."""

    def test_person_creation_valid(self):
        """Test creating a valid person."""
        person = Person(
            name="John Doe",
            age=45,
            retirement_age=65,
            life_expectancy=85,
            current_savings=500000,
            annual_contribution=25000,
            risk_tolerance="moderate"
        )
        assert person.name == "John Doe"
        assert person.age == 45
        assert person.retirement_age == 65
        assert person.risk_tolerance == "moderate"
        assert len(person.goals) == 0

    def test_person_creation_with_goals(self):
        """Test creating person with goals."""
        goal1 = Goal(name="Retirement Income", target_amount=80000, target_age=65,
                    priority="essential", goal_type="income")
        goal2 = Goal(name="Legacy", target_amount=500000, target_age=85,
                    priority="important", goal_type="legacy")

        person = Person(
            name="Jane Smith",
            age=45,
            retirement_age=65,
            life_expectancy=85,
            current_savings=500000,
            annual_contribution=25000,
            risk_tolerance="moderate",
            goals=[goal1, goal2]
        )
        assert len(person.goals) == 2
        assert person.goals[0].name == "Retirement Income"
        assert person.goals[1].name == "Legacy"

    def test_person_validation_invalid_age_sequence(self):
        """Test person validation with invalid age sequence."""
        with pytest.raises(ValidationError, match="Retirement age must be after current age"):
            Person(
                name="Test Person",
                age=65,
                retirement_age=60,
                life_expectancy=85,
                current_savings=500000,
                annual_contribution=25000,
                risk_tolerance="moderate"
            )

    def test_person_validation_invalid_life_expectancy(self):
        """Test person validation with invalid life expectancy."""
        with pytest.raises(ValidationError, match="Life expectancy must be after retirement age"):
            Person(
                name="Test Person",
                age=45,
                retirement_age=65,
                life_expectancy=60,
                current_savings=500000,
                annual_contribution=25000,
                risk_tolerance="moderate"
            )

    def test_person_validation_invalid_risk_tolerance(self):
        """Test person validation with invalid risk tolerance."""
        with pytest.raises(ValidationError, match="Person validation failed"):
            Person(
                name="Test Person",
                age=45,
                retirement_age=65,
                life_expectancy=85,
                current_savings=500000,
                annual_contribution=25000,
                risk_tolerance="very_aggressive"
            )

    def test_get_essential_goals(self):
        """Test filtering essential goals."""
        goal1 = Goal(name="Retirement Income", target_amount=80000, target_age=65,
                    priority="essential", goal_type="income")
        goal2 = Goal(name="Legacy", target_amount=500000, target_age=85,
                    priority="important", goal_type="legacy")
        goal3 = Goal(name="Travel", target_amount=15000, target_age=65,
                    priority="essential", goal_type="lifestyle")

        person = Person(
            name="Test Person",
            age=45,
            retirement_age=65,
            life_expectancy=85,
            current_savings=500000,
            annual_contribution=25000,
            risk_tolerance="moderate",
            goals=[goal1, goal2, goal3]
        )

        essential_goals = person.get_essential_goals()
        assert len(essential_goals) == 2
        assert all(goal.priority == "essential" for goal in essential_goals)

    def test_get_working_years(self):
        """Test calculating working years."""
        person = Person(
            name="Test Person",
            age=45,
            retirement_age=65,
            life_expectancy=85,
            current_savings=500000,
            annual_contribution=25000,
            risk_tolerance="moderate"
        )
        assert person.get_working_years() == 20

    def test_get_retirement_years(self):
        """Test calculating retirement years."""
        person = Person(
            name="Test Person",
            age=45,
            retirement_age=65,
            life_expectancy=85,
            current_savings=500000,
            annual_contribution=25000,
            risk_tolerance="moderate"
        )
        assert person.get_retirement_years() == 20


class TestPersonIntegration:
    """Test Person integration scenarios."""

    def test_complete_retirement_profile(self):
        """Test a complete retirement profile with goals."""
        # Create goals
        retirement_income = Goal(name="Retirement Income", target_amount=80000, target_age=65,
                               priority="essential", goal_type="income")
        legacy = Goal(name="Legacy", target_amount=500000, target_age=85,
                     priority="important", goal_type="legacy")

        person = Person(
            name="Complete Profile",
            age=45,
            retirement_age=65,
            life_expectancy=85,
            current_savings=750000,
            annual_contribution=30000,
            risk_tolerance="moderate",
            tax_filing_status="married",
            state_of_residence="CA",
            goals=[retirement_income, legacy]
        )

        # Verify profile completeness
        assert person.name == "Complete Profile"
        assert len(person.goals) == 2
        assert person.tax_filing_status == "married"
        assert person.state_of_residence == "CA"

        # Test goal filtering
        essential_goals = person.get_essential_goals()
        assert len(essential_goals) == 1
        assert essential_goals[0].name == "Retirement Income"

        # Test year calculations
        assert person.get_working_years() == 20
        assert person.get_retirement_years() == 20