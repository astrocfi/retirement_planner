#!/usr/bin/env python3
"""
Test script to verify events configuration has no overlapping periods.
"""

import sys
import os
import yaml
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..'))

from retirement_planner.models.events import EventManager, Event, EventType, Period


def load_events_from_yaml(filename):
    """Load events from YAML file."""
    with open(filename, 'r') as f:
        data = yaml.safe_load(f)

    events = []
    for category, event_list in data['events'].items():
        for event_data in event_list:
            # Create period
            period = Period(
                start_age=event_data['period']['start_age'],
                end_age=event_data['period']['end_age'],
                description=event_data['period']['description']
            )

            # Create event
            event = Event(
                name=event_data['name'],
                event_type=EventType(event_data['event_type']),
                period=period,
                amount=event_data['amount'],
                probability=event_data.get('probability', 1.0),
                inflation_adjustment=event_data.get('inflation_adjustment', True),
                description=event_data.get('description'),
                metadata=event_data.get('metadata', {})
            )
            events.append(event)

    return events


def test_events_configuration():
    """Test that the events configuration has no overlapping periods."""

    # Load events from configuration
    events_file = os.path.join(os.path.dirname(__file__), "..", "events.yaml")
    events = load_events_from_yaml(events_file)

    # Create event manager and add events
    manager = EventManager()
    for event in events:
        manager.add_event(event)

    # Validate events
    issues = manager.validate_events()

    if issues:
        print("❌ Found overlapping events:")
        for issue in issues:
            print(f"  - {issue}")
        return False
    else:
        print("✅ No overlapping events found")
        return True


def test_age_coverage():
    """Test that all relevant ages have expense coverage."""

    # Load events from configuration
    events_file = os.path.join(os.path.dirname(__file__), "..", "events.yaml")
    events = load_events_from_yaml(events_file)

    # Create event manager and add events
    manager = EventManager()
    for event in events:
        manager.add_event(event)

    # Check expense coverage for ages 50-95
    expense_events = manager.get_events_by_type(EventType.EXPENSE)

    print("\nExpense coverage by age:")
    for age in range(50, 96):
        active_expenses = [e for e in expense_events if e.is_active_at_age(age)]
        if active_expenses:
            total_expense = sum(e.amount for e in active_expenses)
            print(f"  Age {age}: ${total_expense:,.0f} ({len(active_expenses)} events)")
        else:
            print(f"  Age {age}: NO EXPENSE COVERAGE ⚠️")


if __name__ == "__main__":
    print("Testing events configuration...")

    success = test_events_configuration()
    test_age_coverage()

    if success:
        print("\n✅ Events configuration is valid")
    else:
        print("\n❌ Events configuration has issues")
        sys.exit(1)