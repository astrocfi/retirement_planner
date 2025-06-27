#!/usr/bin/env python3
"""
Test script to verify configuration files work with current implementation.
"""

import sys
from pathlib import Path

# Add the parent directory to the path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

# Get the directory where this script is located
SCRIPT_DIR = Path(__file__).parent.parent

def test_person_profile():
    """Test loading and creating Person object from profile."""
    from retirement_planner.core.config import ConfigLoader
    from retirement_planner.models.person import Person, Goal

    print("Testing person profile configuration...")

    # Load person profile using absolute path
    loader = ConfigLoader()
    loader.load_from_file(SCRIPT_DIR / 'person_profile.yaml')
    person_data = loader.config_data

    print(f"✓ Person profile loaded successfully!")
    print(f"  Name: {person_data['name']}")
    print(f"  Age: {person_data['age']}")
    print(f"  Retirement age: {person_data['retirement_age']}")
    print(f"  Current savings: ${person_data['current_savings']:,.0f}")

    # Create Person object
    person = Person(
        name=person_data['name'],
        age=person_data['age'],
        retirement_age=person_data['retirement_age'],
        life_expectancy=person_data['life_expectancy'],
        current_savings=person_data['current_savings'],
        annual_contribution=person_data['annual_contribution'],
        risk_tolerance=person_data['risk_tolerance'],
        tax_filing_status=person_data['tax_filing_status'],
        state_of_residence=person_data['state_of_residence'],
        goals=[Goal(**goal) for goal in person_data['goals']],
        additional_data=person_data.get('additional_data', {})
    )

    print(f"✓ Person object created successfully!")
    print(f"  Working years: {person.get_working_years()}")
    print(f"  Retirement years: {person.get_retirement_years()}")
    print(f"  Essential goals: {len(person.get_essential_goals())}")

    # Assertions to verify the test passed
    assert person.name == person_data['name']
    assert person.age == person_data['age']
    assert person.get_working_years() == person_data['retirement_age'] - person_data['age']

def test_events_config():
    """Test loading events configuration."""
    from retirement_planner.core.config import ConfigLoader
    from retirement_planner.models.events import EventManager, Event, EventType, Period

    print("\nTesting events configuration...")

    # Load events using absolute path
    loader = ConfigLoader()
    loader.load_from_file(SCRIPT_DIR / 'events.yaml')
    events_data = loader.config_data

    print(f"✓ Events configuration loaded successfully!")

    # Create EventManager and add events
    event_manager = EventManager()

    # Process events by category
    for category, events_list in events_data["events"].items():
        for event_data in events_list:
            # Create Period object
            period = Period(**event_data["period"])

            # Create Event object
            event = Event(
                name=event_data["name"],
                event_type=EventType(event_data["event_type"]),
                period=period,
                amount=event_data["amount"],
                probability=event_data["probability"],
                inflation_adjustment=event_data["inflation_adjustment"],
                description=event_data["description"],
                metadata=event_data.get("metadata", {})
            )

            event_manager.add_event(event)

    print(f"✓ Created {len(event_manager.events)} events")

    # Test event processing
    context = {}
    results = event_manager.process_events_at_age(55, context)
    print(f"✓ Events processed at age 55: {len(results['events_processed'])} events")

    # Assertions to verify the test passed
    assert len(event_manager.events) > 0
    assert len(results['events_processed']) > 0

def test_market_data():
    """Test loading market data configuration."""
    from retirement_planner.core.config import ConfigLoader

    print("\nTesting market data configuration...")

    loader = ConfigLoader()
    loader.load_from_file(SCRIPT_DIR / 'market_data.yaml')
    market_data = loader.config_data

    print(f"✓ Market data configuration loaded successfully!")
    print(f"  Portfolio allocation: {market_data['portfolio_allocation']}")
    print(f"  Expected returns: {market_data['expected_returns']}")
    print(f"  Volatility: {market_data['volatility']}")

    # Assertions to verify the test passed
    assert 'portfolio_allocation' in market_data
    assert 'expected_returns' in market_data
    assert 'volatility' in market_data

def test_simulation_config():
    """Test loading simulation configuration."""
    from retirement_planner.core.config import ConfigLoader

    print("\nTesting simulation configuration...")

    loader = ConfigLoader()
    loader.load_from_file(SCRIPT_DIR / 'simulation_config.yaml')
    sim_data = loader.config_data

    print(f"✓ Simulation configuration loaded successfully!")
    print(f"  Scenarios: {sim_data['simulation']['num_scenarios']:,}")
    print(f"  Time horizon: {sim_data['simulation']['time_horizon']} years")
    print(f"  Random method: {sim_data['random_generation']['method']}")

    # Assertions to verify the test passed
    assert sim_data['simulation']['num_scenarios'] > 0
    assert sim_data['simulation']['time_horizon'] > 0
    assert sim_data['random_generation']['method'] in ['sobol', 'random', 'latin_hypercube']

def main():
    """Run all configuration tests."""
    print("=" * 60)
    print("CONFIGURATION FILE COMPATIBILITY TEST")
    print("=" * 60)

    tests = [
        test_person_profile,
        test_events_config,
        test_market_data,
        test_simulation_config
    ]

    passed = 0
    total = len(tests)

    for test in tests:
        try:
            test()
            passed += 1
        except Exception as e:
            print(f"✗ Test {test.__name__} failed: {e}")

    print("\n" + "=" * 60)
    print(f"TEST RESULTS: {passed}/{total} tests passed")

    if passed == total:
        print("✓ All configuration files are compatible with current implementation!")
    else:
        print("✗ Some configuration files have compatibility issues.")

    print("=" * 60)

if __name__ == "__main__":
    main()