"""
Unit tests for Person model and related classes.

Tests the Person, Income, Expense, and Goal classes with semantic behavior focus.
"""

import pytest
from retirement_planner.models.person import Person, Income, Expense, Goal
from retirement_planner.core.exceptions import ValidationError


class TestIncome:
    """Test Income class functionality."""

    def test_income_creation_valid(self):
        """Test creating a valid income source."""
        income = Income(
            source="Salary",
            amount=100000,
            start_age=30,
            end_age=65
        )
        assert income.source == "Salary"
        assert income.amount == 100000
        assert income.start_age == 30
        assert income.end_age == 65
        assert income.inflation_adjustment is True
        assert income.probability == 1.0

    def test_income_creation_with_probability(self):
        """Test creating income with probability less than 1."""
        income = Income(
            source="Consulting",
            amount=25000,
            start_age=60,
            probability=0.7
        )
        assert income.probability == 0.7
        assert income.end_age is None

    def test_income_validation_invalid_amount(self):
        """Test income validation with negative amount."""
        with pytest.raises(ValidationError, match="Income validation failed"):
            Income(
                source="Salary",
                amount=-50000,
                start_age=30
            )

    def test_income_validation_invalid_age_range(self):
        """Test income validation with invalid age range."""
        with pytest.raises(ValidationError, match="End age must be after start age"):
            Income(
                source="Salary",
                amount=100000,
                start_age=65,
                end_age=60
            )

    def test_income_validation_invalid_probability(self):
        """Test income validation with invalid probability."""
        with pytest.raises(ValidationError, match="Income validation failed"):
            Income(
                source="Salary",
                amount=100000,
                start_age=30,
                probability=1.5
            )


class TestExpense:
    """Test Expense class functionality."""

    def test_expense_creation_valid(self):
        """Test creating a valid expense."""
        expense = Expense(
            category="Housing",
            amount=30000,
            start_age=30,
            frequency="annual"
        )
        assert expense.category == "Housing"
        assert expense.amount == 30000
        assert expense.frequency == "annual"
        assert expense.inflation_adjustment is True

    def test_expense_creation_monthly(self):
        """Test creating monthly expense."""
        expense = Expense(
            category="Utilities",
            amount=200,
            start_age=30,
            frequency="monthly"
        )
        assert expense.frequency == "monthly"

    def test_expense_creation_one_time(self):
        """Test creating one-time expense."""
        expense = Expense(
            category="Home Purchase",
            amount=500000,
            start_age=35,
            frequency="one_time"
        )
        assert expense.frequency == "one_time"

    def test_expense_validation_invalid_frequency(self):
        """Test expense validation with invalid frequency."""
        with pytest.raises(ValidationError, match="Expense validation failed"):
            Expense(
                category="Housing",
                amount=30000,
                start_age=30,
                frequency="weekly"
            )

    def test_expense_validation_invalid_age_range(self):
        """Test expense validation with invalid age range."""
        with pytest.raises(ValidationError, match="End age must be after start age"):
            Expense(
                category="Healthcare",
                amount=15000,
                start_age=80,
                end_age=75
            )


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
        assert len(person.income_sources) == 0
        assert len(person.expenses) == 0
        assert len(person.goals) == 0

    def test_person_creation_with_income_and_expenses(self):
        """Test creating person with income and expenses."""
        income = Income(source="Salary", amount=100000, start_age=45, end_age=65)
        expense = Expense(category="Housing", amount=30000, start_age=45, end_age=85)

        person = Person(
            name="Jane Smith",
            age=45,
            retirement_age=65,
            life_expectancy=85,
            current_savings=500000,
            annual_contribution=25000,
            risk_tolerance="moderate",
            income_sources=[income],
            expenses=[expense]
        )
        assert len(person.income_sources) == 1
        assert len(person.expenses) == 1
        assert person.income_sources[0].source == "Salary"
        assert person.expenses[0].category == "Housing"

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

    def test_get_total_income_at_age(self):
        """Test calculating total income at specific age."""
        income1 = Income(source="Salary", amount=100000, start_age=45, end_age=65)
        income2 = Income(source="Social Security", amount=35000, start_age=67, end_age=85)

        person = Person(
            name="Test Person",
            age=45,
            retirement_age=65,
            life_expectancy=85,
            current_savings=500000,
            annual_contribution=25000,
            risk_tolerance="moderate",
            income_sources=[income1, income2]
        )

        # Age 50 - only salary
        assert person.get_total_income_at_age(50) == 100000

        # Age 70 - only social security
        assert person.get_total_income_at_age(70) == 35000

        # Age 66 - no income
        assert person.get_total_income_at_age(66) == 0

    def test_get_total_expenses_at_age(self):
        """Test calculating total expenses at specific age."""
        expense1 = Expense(category="Housing", amount=30000, start_age=45, end_age=85, frequency="annual")
        expense2 = Expense(category="Healthcare", amount=800, start_age=45, end_age=85, frequency="monthly")
        expense3 = Expense(category="Home Purchase", amount=500000, start_age=50, frequency="one_time")

        person = Person(
            name="Test Person",
            age=45,
            retirement_age=65,
            life_expectancy=85,
            current_savings=500000,
            annual_contribution=25000,
            risk_tolerance="moderate",
            expenses=[expense1, expense2, expense3]
        )

        # Age 49 - housing + healthcare (monthly converted to annual)
        assert person.get_total_expenses_at_age(49) == 30000 + (800 * 12)

        # Age 50 - housing + healthcare + one-time home purchase
        assert person.get_total_expenses_at_age(50) == 30000 + (800 * 12) + 500000

        # Age 51 - housing + healthcare (no one-time expense)
        assert person.get_total_expenses_at_age(51) == 30000 + (800 * 12)

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
        """Test a complete retirement profile with all components."""
        # Create income sources
        salary = Income(source="Salary", amount=120000, start_age=45, end_age=65)
        social_security = Income(source="Social Security", amount=40000, start_age=67, end_age=85)

        # Create expenses
        housing = Expense(category="Housing", amount=35000, start_age=45, end_age=85, frequency="annual")
        healthcare = Expense(category="Healthcare", amount=1000, start_age=45, end_age=85, frequency="monthly")

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
            income_sources=[salary, social_security],
            expenses=[housing, healthcare],
            goals=[retirement_income, legacy]
        )

        # Verify profile completeness
        assert person.name == "Complete Profile"
        assert len(person.income_sources) == 2
        assert len(person.expenses) == 2
        assert len(person.goals) == 2
        assert person.tax_filing_status == "married"
        assert person.state_of_residence == "CA"

        # Test cash flow calculations
        working_income = person.get_total_income_at_age(50)
        working_expenses = person.get_total_expenses_at_age(50)
        assert working_income == 120000
        assert working_expenses == 35000 + (1000 * 12)

        # Test retirement cash flow
        retirement_income = person.get_total_income_at_age(70)
        retirement_expenses = person.get_total_expenses_at_age(70)
        assert retirement_income == 40000
        assert retirement_expenses == 35000 + (1000 * 12)