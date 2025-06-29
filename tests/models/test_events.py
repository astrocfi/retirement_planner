"""
Unit tests for Event model and related classes.

Tests the Event, EventManager, Period, and EventType classes with semantic behavior focus.
"""

import pytest
from retirement_planner.models.events import Event, EventManager, Period, EventType
from retirement_planner.core.exceptions import ValidationError, EventError


class TestEventType:
    """Test EventType enum functionality."""

    def test_event_type_values(self):
        """Test that event types have correct values."""
        assert EventType.INCOME.value == "income"
        assert EventType.EXPENSE.value == "expense"
        assert EventType.ASSET.value == "asset"
        assert EventType.LIABILITY.value == "liability"
        assert EventType.TAX.value == "tax"
        assert EventType.BENEFIT.value == "benefit"

    def test_event_type_enumeration(self):
        """Test that all expected event types exist."""
        expected_types = [
            "income", "expense", "asset", "liability",
            "tax", "benefit", "lifestyle", "health",
            "family", "economic"
        ]
        actual_types = [event_type.value for event_type in EventType]
        assert actual_types == expected_types


class TestPeriod:
    """Test Period class functionality."""

    def test_period_creation_valid(self):
        """Test creating a valid period."""
        period = Period(start_age=45, end_age=65)
        assert period.start_age == 45
        assert period.end_age == 65
        assert period.description is None

    def test_period_creation_with_description(self):
        """Test creating period with description."""
        period = Period(start_age=45, end_age=65, description="Working years")
        assert period.description == "Working years"

    def test_period_creation_no_end_age(self):
        """Test creating period without end age."""
        period = Period(start_age=65)
        assert period.start_age == 65
        assert period.end_age is None

    def test_period_creation_single_year(self):
        """Test creating period for a single year."""
        period = Period(start_age=65, end_age=65)
        assert period.start_age == 65
        assert period.end_age == 65
        assert period.duration() == 1

    def test_period_validation_invalid_age_range(self):
        """Test period validation with invalid age range."""
        with pytest.raises(ValidationError, match="End age must be greater than or equal to start age"):
            Period(start_age=65, end_age=60)

    def test_period_validation_invalid_start_age(self):
        """Test period validation with invalid start age."""
        with pytest.raises(ValidationError, match="Period validation failed"):
            Period(start_age=-5, end_age=65)

    def test_contains_age(self):
        """Test age containment logic."""
        period = Period(start_age=45, end_age=65)

        assert period.contains_age(45) is True
        assert period.contains_age(55) is True
        assert period.contains_age(65) is True
        assert period.contains_age(44) is False
        assert period.contains_age(66) is False

    def test_contains_age_single_year(self):
        """Test age containment for single year period."""
        period = Period(start_age=65, end_age=65)

        assert period.contains_age(65) is True
        assert period.contains_age(64) is False
        assert period.contains_age(66) is False

    def test_contains_age_no_end(self):
        """Test age containment with no end age."""
        period = Period(start_age=65)

        assert period.contains_age(65) is True
        assert period.contains_age(85) is True
        assert period.contains_age(120) is True
        assert period.contains_age(64) is False

    def test_duration(self):
        """Test duration calculation."""
        period = Period(start_age=45, end_age=65)
        assert period.duration() == 21  # 65 - 45 + 1

    def test_duration_single_year(self):
        """Test duration calculation for single year."""
        period = Period(start_age=65, end_age=65)
        assert period.duration() == 1

    def test_duration_no_end(self):
        """Test duration calculation with no end age."""
        period = Period(start_age=65)
        assert period.duration() == 56  # 120 - 65 + 1


class TestEvent:
    """Test Event class functionality."""

    def test_event_creation_valid(self):
        """Test creating a valid event."""
        period = Period(start_age=45, end_age=65)
        event = Event(
            name="Salary Increase",
            event_type=EventType.INCOME,
            period=period,
            amount=10000
        )
        assert event.name == "Salary Increase"
        assert event.event_type == EventType.INCOME
        assert event.period == period
        assert event.amount == 10000
        assert event.probability == 1.0
        assert event.inflation_adjustment is True

    def test_event_creation_with_probability(self):
        """Test creating event with probability less than 1."""
        period = Period(start_age=60)
        event = Event(
            name="Inheritance",
            event_type=EventType.ASSET,
            period=period,
            amount=500000,
            probability=0.3
        )
        assert event.probability == 0.3

    def test_event_creation_no_inflation_adjustment(self):
        """Test creating event without inflation adjustment."""
        period = Period(start_age=65, end_age=85)
        event = Event(
            name="Fixed Pension",
            event_type=EventType.INCOME,
            period=period,
            amount=30000,
            inflation_adjustment=False
        )
        assert event.inflation_adjustment is False

    def test_event_validation_invalid_amount(self):
        """Test event validation with negative amount."""
        period = Period(start_age=45, end_age=65)
        with pytest.raises(ValidationError, match="Event validation failed"):
            Event(
                name="Test Event",
                event_type=EventType.EXPENSE,
                period=period,
                amount=-5000
            )

    def test_event_validation_invalid_probability(self):
        """Test event validation with invalid probability."""
        period = Period(start_age=45, end_age=65)
        with pytest.raises(ValidationError, match="Event validation failed"):
            Event(
                name="Test Event",
                event_type=EventType.INCOME,
                period=period,
                amount=10000,
                probability=1.5
            )

    def test_is_active_at_age(self):
        """Test event activity at specific ages."""
        period = Period(start_age=45, end_age=65)
        event = Event(
            name="Test Event",
            event_type=EventType.INCOME,
            period=period,
            amount=10000
        )

        assert event.is_active_at_age(45) is True
        assert event.is_active_at_age(55) is True
        assert event.is_active_at_age(65) is True
        assert event.is_active_at_age(44) is False
        assert event.is_active_at_age(66) is False

    def test_get_effective_amount_no_inflation(self):
        """Test effective amount calculation without inflation."""
        period = Period(start_age=45, end_age=65)
        event = Event(
            name="Test Event",
            event_type=EventType.INCOME,
            period=period,
            amount=10000,
            inflation_adjustment=False
        )

        # Should be same amount regardless of age
        assert event.get_effective_amount(45) == 10000
        assert event.get_effective_amount(55) == 10000
        assert event.get_effective_amount(65) == 10000

    def test_get_effective_amount_with_inflation(self):
        """Test effective amount calculation with inflation."""
        period = Period(start_age=45, end_age=65)
        event = Event(
            name="Test Event",
            event_type=EventType.INCOME,
            period=period,
            amount=10000,
            inflation_adjustment=True
        )

        # With 2% inflation
        assert event.get_effective_amount(45) == 10000
        assert event.get_effective_amount(55) == pytest.approx(10000 * (1.02 ** 10), rel=1e-2)
        assert event.get_effective_amount(65) == pytest.approx(10000 * (1.02 ** 20), rel=1e-2)


class TestEventManager:
    """Test EventManager class functionality."""

    def test_event_manager_creation(self):
        """Test creating event manager."""
        manager = EventManager()
        assert len(manager.events) == 0
        assert len(manager.event_handlers) == len(EventType)

    def test_add_event(self):
        """Test adding events to manager."""
        manager = EventManager()
        period = Period(start_age=45, end_age=65)
        event = Event(
            name="Test Event",
            event_type=EventType.INCOME,
            period=period,
            amount=10000
        )

        manager.add_event(event)
        assert len(manager.events) == 1
        assert manager.events[0] == event

    def test_add_handler(self):
        """Test adding event handlers."""
        manager = EventManager()

        def test_handler(event, age, context):
            return {"processed": True}

        manager.add_handler(EventType.INCOME, test_handler)
        assert len(manager.event_handlers[EventType.INCOME]) == 1

    def test_get_events_at_age(self):
        """Test getting events active at specific age."""
        manager = EventManager()

        # Add events with different periods
        event1 = Event(
            name="Working Income",
            event_type=EventType.INCOME,
            period=Period(start_age=45, end_age=65),
            amount=100000
        )
        event2 = Event(
            name="Social Security",
            event_type=EventType.INCOME,
            period=Period(start_age=67, end_age=85),
            amount=40000
        )

        manager.add_event(event1)
        manager.add_event(event2)

        # Age 50 - only working income
        events_at_50 = manager.get_events_at_age(50)
        assert len(events_at_50) == 1
        assert events_at_50[0].name == "Working Income"

        # Age 70 - only social security
        events_at_70 = manager.get_events_at_age(70)
        assert len(events_at_70) == 1
        assert events_at_70[0].name == "Social Security"

        # Age 66 - no events
        events_at_66 = manager.get_events_at_age(66)
        assert len(events_at_66) == 0

    def test_get_events_by_type(self):
        """Test getting events by type."""
        manager = EventManager()

        income_event = Event(
            name="Salary",
            event_type=EventType.INCOME,
            period=Period(start_age=45, end_age=65),
            amount=100000
        )
        expense_event = Event(
            name="Housing",
            event_type=EventType.EXPENSE,
            period=Period(start_age=45, end_age=85),
            amount=30000
        )

        manager.add_event(income_event)
        manager.add_event(expense_event)

        income_events = manager.get_events_by_type(EventType.INCOME)
        assert len(income_events) == 1
        assert income_events[0].name == "Salary"

        expense_events = manager.get_events_by_type(EventType.EXPENSE)
        assert len(expense_events) == 1
        assert expense_events[0].name == "Housing"

    def test_process_events_at_age(self):
        """Test processing events at specific age."""
        manager = EventManager()

        # Add income and expense events
        income_event = Event(
            name="Salary",
            event_type=EventType.INCOME,
            period=Period(start_age=45, end_age=65),
            amount=100000
        )
        expense_event = Event(
            name="Housing",
            event_type=EventType.EXPENSE,
            period=Period(start_age=45, end_age=85),
            amount=30000
        )

        manager.add_event(income_event)
        manager.add_event(expense_event)

        # Process events at age 50
        results = manager.process_events_at_age(50, {})

        # Age 50 is 5 years after start age 45, so inflation adjustment: 100000 * (1.02)^5
        expected_income = 100000 * (1.02 ** 5)
        expected_expense = 30000 * (1.02 ** 5)

        assert results['income'] == pytest.approx(expected_income, rel=1e-2)
        assert results['expenses'] == pytest.approx(expected_expense, rel=1e-2)
        assert results['assets'] == 0
        assert results['liabilities'] == 0
        assert results['tax_impact'] == 0
        assert results['benefits'] == 0
        assert len(results['events_processed']) == 2

    def test_process_events_with_probability(self):
        """Test processing events with probability less than 1."""
        manager = EventManager()

        event = Event(
            name="Inheritance",
            event_type=EventType.ASSET,
            period=Period(start_age=60),
            amount=500000,
            probability=0.3
        )

        manager.add_event(event)
        results = manager.process_events_at_age(60, {})

        assert results['assets'] == 500000 * 0.3

    def test_get_cash_flow_at_age(self):
        """Test calculating cash flow at specific age."""
        manager = EventManager()

        # Add income and expense events
        income_event = Event(
            name="Salary",
            event_type=EventType.INCOME,
            period=Period(start_age=45, end_age=65),
            amount=100000
        )
        expense_event = Event(
            name="Housing",
            event_type=EventType.EXPENSE,
            period=Period(start_age=45, end_age=85),
            amount=30000
        )

        manager.add_event(income_event)
        manager.add_event(expense_event)

        cash_flow = manager.get_cash_flow_at_age(50, {})
        # Age 50 is 5 years after start age 45, so inflation adjustment: (100000 - 30000) * (1.02)^5
        expected_cash_flow = (100000 - 30000) * (1.02 ** 5)
        assert cash_flow == pytest.approx(expected_cash_flow, rel=1e-2)

    def test_validate_events(self):
        """Test event validation."""
        manager = EventManager()

        # Add overlapping events of same type
        event1 = Event(
            name="Salary",
            event_type=EventType.INCOME,
            period=Period(start_age=45, end_age=65),
            amount=100000
        )
        event2 = Event(
            name="Bonus",
            event_type=EventType.INCOME,
            period=Period(start_age=60, end_age=70),
            amount=20000
        )

        manager.add_event(event1)
        manager.add_event(event2)

        issues = manager.validate_events()
        assert len(issues) > 0
        assert "overlaps" in issues[0]

    def test_get_event_summary(self):
        """Test getting event summary."""
        manager = EventManager()

        # Add various events
        income_event = Event(
            name="Salary",
            event_type=EventType.INCOME,
            period=Period(start_age=45, end_age=65),
            amount=100000
        )
        expense_event = Event(
            name="Housing",
            event_type=EventType.EXPENSE,
            period=Period(start_age=45, end_age=85),
            amount=30000
        )
        asset_event = Event(
            name="Inheritance",
            event_type=EventType.ASSET,
            period=Period(start_age=60),
            amount=500000
        )

        manager.add_event(income_event)
        manager.add_event(expense_event)
        manager.add_event(asset_event)

        summary = manager.get_event_summary()

        assert summary['total_events'] == 3
        assert summary['events_by_type']['income'] == 1
        assert summary['events_by_type']['expense'] == 1
        assert summary['events_by_type']['asset'] == 1
        assert summary['total_income_events'] == 1
        assert summary['total_expense_events'] == 1
        assert summary['age_range']['min'] == 45
        assert summary['age_range']['max'] == 85

    def test_process_events_with_handlers(self):
        """Test processing events with custom handlers."""
        manager = EventManager()

        def income_handler(event, age, context):
            return {"bonus": 5000}

        def expense_handler(event, age, context):
            return {"discount": 1000}

        manager.add_handler(EventType.INCOME, income_handler)
        manager.add_handler(EventType.EXPENSE, expense_handler)

        income_event = Event(
            name="Salary",
            event_type=EventType.INCOME,
            period=Period(start_age=45, end_age=65),
            amount=100000
        )
        expense_event = Event(
            name="Housing",
            event_type=EventType.EXPENSE,
            period=Period(start_age=45, end_age=85),
            amount=30000
        )

        manager.add_event(income_event)
        manager.add_event(expense_event)

        results = manager.process_events_at_age(50, {})

        assert results['bonus'] == 5000
        assert results['discount'] == 1000
        assert results['income'] == pytest.approx(100000 * (1.02 ** 5), rel=1e-2)
        assert results['expenses'] == pytest.approx(30000 * (1.02 ** 5), rel=1e-2)

    def test_process_events_with_unused_types(self):
        """Test processing events with unused event types."""
        manager = EventManager()

        lifestyle_event = Event(
            name="Travel",
            event_type=EventType.LIFESTYLE,
            period=Period(start_age=65, end_age=75),
            amount=15000
        )
        health_event = Event(
            name="Medical",
            event_type=EventType.HEALTH,
            period=Period(start_age=70, end_age=85),
            amount=8000
        )
        family_event = Event(
            name="Support",
            event_type=EventType.FAMILY,
            period=Period(start_age=60, end_age=80),
            amount=12000
        )
        economic_event = Event(
            name="Inflation",
            event_type=EventType.ECONOMIC,
            period=Period(start_age=45, end_age=85),
            amount=2000
        )

        manager.add_event(lifestyle_event)
        manager.add_event(health_event)
        manager.add_event(family_event)
        manager.add_event(economic_event)

        results = manager.process_events_at_age(70, {})

        # These event types don't affect cash flow calculation
        assert results['income'] == 0
        assert results['expenses'] == 0
        assert results['assets'] == 0
        assert results['liabilities'] == 0
        assert results['tax_impact'] == 0
        assert results['benefits'] == 0
        assert len(results['events_processed']) == 4

    def test_process_events_with_liability_tax_benefit_types(self):
        """Test processing events with liability, tax, and benefit types."""
        manager = EventManager()

        liability_event = Event(
            name="Mortgage",
            event_type=EventType.LIABILITY,
            period=Period(start_age=45, end_age=65),
            amount=25000
        )
        tax_event = Event(
            name="Property Tax",
            event_type=EventType.TAX,
            period=Period(start_age=45, end_age=85),
            amount=8000
        )
        benefit_event = Event(
            name="Pension Benefit",
            event_type=EventType.BENEFIT,
            period=Period(start_age=65, end_age=85),
            amount=30000
        )

        manager.add_event(liability_event)
        manager.add_event(tax_event)
        manager.add_event(benefit_event)

        # Test at age 50 (liability and tax active)
        results_50 = manager.process_events_at_age(50, {})
        expected_liability_50 = 25000 * (1.02 ** 5)
        expected_tax_50 = 8000 * (1.02 ** 5)

        assert results_50['liabilities'] == pytest.approx(expected_liability_50, rel=1e-2)
        assert results_50['tax_impact'] == pytest.approx(expected_tax_50, rel=1e-2)
        assert results_50['benefits'] == 0

        # Test at age 70 (tax and benefit active)
        results_70 = manager.process_events_at_age(70, {})
        expected_tax_70 = 8000 * (1.02 ** 25)
        expected_benefit_70 = 30000 * (1.02 ** 5)

        assert results_70['liabilities'] == 0
        assert results_70['tax_impact'] == pytest.approx(expected_tax_70, rel=1e-2)
        assert results_70['benefits'] == pytest.approx(expected_benefit_70, rel=1e-2)


class TestEventIntegration:
    """Test Event integration scenarios."""

    def test_complete_retirement_timeline(self):
        """Test a complete retirement timeline with multiple events."""
        manager = EventManager()

        # Working years (45-65)
        salary = Event(
            name="Salary",
            event_type=EventType.INCOME,
            period=Period(start_age=45, end_age=65),
            amount=120000
        )
        housing = Event(
            name="Housing",
            event_type=EventType.EXPENSE,
            period=Period(start_age=45, end_age=85),
            amount=35000
        )

        # Retirement transition (65-67)
        pension = Event(
            name="Pension",
            event_type=EventType.INCOME,
            period=Period(start_age=65, end_age=85),
            amount=40000
        )

        # Social Security (67+)
        social_security = Event(
            name="Social Security",
            event_type=EventType.INCOME,
            period=Period(start_age=67, end_age=85),
            amount=35000
        )

        # Healthcare costs (65+)
        healthcare = Event(
            name="Healthcare",
            event_type=EventType.EXPENSE,
            period=Period(start_age=65, end_age=85),
            amount=15000
        )

        # Add all events
        manager.add_event(salary)
        manager.add_event(housing)
        manager.add_event(pension)
        manager.add_event(social_security)
        manager.add_event(healthcare)

        # Test cash flows at different ages
        working_cash_flow = manager.get_cash_flow_at_age(50, {})
        # Age 50 is 5 years after start age 45, so inflation adjustment: (120000 - 35000) * (1.02)^5
        expected_working_cash_flow = (120000 - 35000) * (1.02 ** 5)
        assert working_cash_flow == pytest.approx(expected_working_cash_flow, rel=1e-2)

        early_retirement_cash_flow = manager.get_cash_flow_at_age(66, {})
        # Age 66: pension starts at 65, housing continues, healthcare starts at 65, no salary, no SS yet
        # Pension: 40000 * (1.02)^1, Housing: 35000 * (1.02)^21, Healthcare: 15000 * (1.02)^1
        expected_early_retirement = 40000 * (1.02 ** 1) - 35000 * (1.02 ** 21) - 15000 * (1.02 ** 1)
        assert early_retirement_cash_flow == pytest.approx(expected_early_retirement, rel=1e-2)

        full_retirement_cash_flow = manager.get_cash_flow_at_age(70, {})
        # Age 70: pension + SS - housing - healthcare
        # Pension: 40000 * (1.02)^5, SS: 35000 * (1.02)^3, Housing: 35000 * (1.02)^25, Healthcare: 15000 * (1.02)^5
        expected_full_retirement = (40000 * (1.02 ** 5) + 35000 * (1.02 ** 3) -
                                   35000 * (1.02 ** 25) - 15000 * (1.02 ** 5))
        assert full_retirement_cash_flow == pytest.approx(expected_full_retirement, rel=1e-2)

        # Test event summary
        summary = manager.get_event_summary()
        assert summary['total_events'] == 5
        assert summary['total_income_events'] == 3
        assert summary['total_expense_events'] == 2
        assert summary['age_range']['min'] == 45
        assert summary['age_range']['max'] == 85