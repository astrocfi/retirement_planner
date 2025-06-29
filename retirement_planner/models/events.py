"""
Event-driven modeling foundation for retirement planning.

Contains classes for temporal events, event management, and event processing.
"""

from dataclasses import dataclass, field
from typing import List, Optional, Dict, Any, Callable
from enum import Enum
from datetime import datetime
from retirement_planner.core.validation import Validator, RequiredRule, RangeRule, ChoiceRule
from retirement_planner.core.exceptions import ValidationError, EventError


class EventType(Enum):
    """Types of events in retirement planning."""
    INCOME = "income"
    EXPENSE = "expense"
    ASSET = "asset"
    LIABILITY = "liability"
    TAX = "tax"
    BENEFIT = "benefit"
    LIFESTYLE = "lifestyle"
    HEALTH = "health"
    FAMILY = "family"
    ECONOMIC = "economic"


@dataclass(frozen=True)
class Period:
    """Represents a time period with age-based boundaries."""
    start_age: int
    end_age: Optional[int] = None
    description: Optional[str] = None

    def __post_init__(self):
        """Validate period data."""
        validator = Validator()
        validator.add_field_validator('start_age').add_rule(RangeRule('start_age', min_value=0, max_value=120))
        validator.add_field_validator('end_age').add_rule(RangeRule('end_age', min_value=0, max_value=120))

        if self.end_age and self.start_age > self.end_age:
            raise ValidationError("End age must be greater than or equal to start age")

        result = validator.validate({
            'start_age': self.start_age,
            'end_age': self.end_age
        })

        if not result.is_valid:
            raise ValidationError(f"Period validation failed: {result.errors}")

    def contains_age(self, age: int) -> bool:
        """Check if period contains a specific age."""
        return self.start_age <= age <= (self.end_age or 120)

    def duration(self) -> int:
        """Calculate duration of period in years."""
        return (self.end_age or 120) - self.start_age + 1


@dataclass(frozen=True)
class Event:
    """Base event class for temporal modeling."""
    name: str
    event_type: EventType
    period: Period
    amount: float
    probability: float = 1.0
    inflation_adjustment: bool = True
    description: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    handlers: List[Callable] = field(default_factory=list)

    def __post_init__(self):
        """Validate event data."""
        validator = Validator()
        validator.add_field_validator('name').add_rule(RequiredRule('name'))
        validator.add_field_validator('amount').add_rule(RangeRule('amount', min_value=0))
        validator.add_field_validator('probability').add_rule(RangeRule('probability', min_value=0, max_value=1))

        result = validator.validate({
            'name': self.name,
            'amount': self.amount,
            'probability': self.probability
        })

        if not result.is_valid:
            raise ValidationError(f"Event validation failed: {result.errors}")

    def is_active_at_age(self, age: int) -> bool:
        """Check if event is active at a specific age."""
        return self.period.contains_age(age)

    def get_effective_amount(self, age: int, inflation_rate: float = 0.02) -> float:
        """Calculate effective amount at a specific age with inflation adjustment."""
        if not self.inflation_adjustment:
            return self.amount

        years_since_start = age - self.period.start_age
        return self.amount * (1 + inflation_rate) ** years_since_start

    def add_handler(self, handler: Callable) -> None:
        """Add an event handler (creates new instance due to immutability)."""
        # This would need to be implemented differently for immutable dataclass
        # For now, handlers are stored in metadata
        pass  # pragma: no cover


class EventManager:
    """Manages event processing and resolution."""

    def __init__(self):
        self.events: List[Event] = []
        self.event_handlers: Dict[EventType, List[Callable]] = {
            event_type: [] for event_type in EventType
        }

    def add_event(self, event: Event) -> None:
        """Add an event to the manager."""
        self.events.append(event)

    def add_handler(self, event_type: EventType, handler: Callable) -> None:
        """Add a handler for a specific event type."""
        self.event_handlers[event_type].append(handler)

    def get_events_at_age(self, age: int) -> List[Event]:
        """Get all events active at a specific age."""
        return [event for event in self.events if event.is_active_at_age(age)]

    def get_events_by_type(self, event_type: EventType) -> List[Event]:
        """Get all events of a specific type."""
        return [event for event in self.events if event.event_type == event_type]

    def process_events_at_age(self, age: int, context: Dict[str, Any]) -> Dict[str, Any]:
        """Process all events at a specific age and return results."""
        results = {
            'income': 0.0,
            'expenses': 0.0,
            'assets': 0.0,
            'liabilities': 0.0,
            'tax_impact': 0.0,
            'benefits': 0.0,
            'events_processed': []
        }

        active_events = self.get_events_at_age(age)

        for event in active_events:
            try:
                # Apply event handlers
                for handler in self.event_handlers[event.event_type]:
                    handler_result = handler(event, age, context)
                    if handler_result:
                        results.update(handler_result)

                # Calculate event impact
                effective_amount = event.get_effective_amount(age)

                if event.event_type == EventType.INCOME:
                    results['income'] += effective_amount * event.probability
                elif event.event_type == EventType.EXPENSE:
                    results['expenses'] += effective_amount * event.probability
                elif event.event_type == EventType.ASSET:
                    results['assets'] += effective_amount * event.probability
                elif event.event_type == EventType.LIABILITY:
                    results['liabilities'] += effective_amount * event.probability
                elif event.event_type == EventType.TAX:
                    results['tax_impact'] += effective_amount * event.probability
                elif event.event_type == EventType.BENEFIT:
                    results['benefits'] += effective_amount * event.probability

                results['events_processed'].append({
                    'name': event.name,
                    'type': event.event_type.value,
                    'amount': effective_amount,
                    'probability': event.probability
                })

            except Exception as e:  # pragma: no cover
                raise EventError(f"Error processing event {event.name}: {str(e)}")  # pragma: no cover

        return results

    def get_cash_flow_at_age(self, age: int, context: Dict[str, Any]) -> float:
        """Calculate net cash flow at a specific age."""
        results = self.process_events_at_age(age, context)
        return (results['income'] + results['benefits'] + results['assets'] -
                results['expenses'] - results['liabilities'] - results['tax_impact'])

    def validate_events(self) -> List[str]:
        """Validate all events and return any issues."""
        issues = []

        for event in self.events:
            # Check for overlapping events of same type
            overlapping = [e for e in self.events
                         if e != event and e.event_type == event.event_type
                         and e.period.start_age <= event.period.end_age
                         and e.period.end_age >= event.period.start_age]

            if overlapping:
                issues.append(f"Event '{event.name}' overlaps with: {[e.name for e in overlapping]}")

        return issues

    def get_event_summary(self) -> Dict[str, Any]:
        """Get summary of all events."""
        summary = {
            'total_events': len(self.events),
            'events_by_type': {},
            'age_range': {'min': 120, 'max': 0},
            'total_income_events': 0,
            'total_expense_events': 0
        }

        for event in self.events:
            # Count by type
            event_type_str = event.event_type.value
            summary['events_by_type'][event_type_str] = summary['events_by_type'].get(event_type_str, 0) + 1

            # Track age range
            summary['age_range']['min'] = min(summary['age_range']['min'], event.period.start_age)
            summary['age_range']['max'] = max(summary['age_range']['max'],
                                            event.period.end_age or event.period.start_age)

            # Count income/expense events
            if event.event_type == EventType.INCOME:
                summary['total_income_events'] += 1
            elif event.event_type == EventType.EXPENSE:
                summary['total_expense_events'] += 1

        return summary