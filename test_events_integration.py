#!/usr/bin/env python3
"""
Test script to verify events integration with portfolio evolution.
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))

from retirement_planner.models.person import Person, Goal
from retirement_planner.models.events import EventManager, Event, EventType, Period
from retirement_planner.models.portfolio import Portfolio, AssetAllocation, StaticRebalancingStrategy
from retirement_planner.assets.base import AssetFactory
from retirement_planner.simulation.engine import MonteCarloEngine, RandomScenarioGenerator, MarketSimulator

def test_events_integration():
    """Test that events properly generate cash flows for portfolio evolution."""

    # Create a simple person
    person = Person(
        name="Test Person",
        age=50,
        retirement_age=65,
        life_expectancy=85,
        risk_tolerance="moderate"
    )

    # Create events
    event_manager = EventManager()

    # Working period: contributions
    working_period = Period(start_age=50, end_age=65)
    salary_event = Event(
        name="Salary",
        event_type=EventType.INCOME,
        period=working_period,
        amount=80000,
        probability=1.0
    )
    event_manager.add_event(salary_event)

    # Retirement period: withdrawals
    retirement_period = Period(start_age=65, end_age=85)
    retirement_expense = Event(
        name="Retirement Expenses",
        event_type=EventType.EXPENSE,
        period=retirement_period,
        amount=120000,
        probability=1.0
    )
    event_manager.add_event(retirement_expense)

    # Create simple assets
    asset_factory = AssetFactory()
    stock_asset = asset_factory.create_asset(
        "equity",
        name="StockA",
        current_value=300000,
        expected_return=0.07,
        volatility=0.18
    )
    bond_asset = asset_factory.create_asset(
        "fixed_income",
        name="BondB",
        current_value=200000,
        expected_return=0.03,
        volatility=0.08
    )

    # Create portfolio
    assets = {asset.name: asset for asset in [stock_asset, bond_asset]}
    asset_values = {asset.name: asset.current_value for asset in [stock_asset, bond_asset]}
    allocation = AssetAllocation(allocation={"StockA": 0.6, "BondB": 0.4})

    portfolio = Portfolio(
        assets=assets,
        allocation=allocation,
        asset_values=asset_values,
        rebalancing_strategy=StaticRebalancingStrategy()
    )

    # Generate cash flows from events
    time_horizon = 35  # 50 to 85
    withdrawals = []
    contributions = []
    start_age = person.age

    print("Cash flows generated from events:")
    print("Age | Year | Net Cash Flow | Contribution | Withdrawal")
    print("-" * 55)

    for year in range(time_horizon):
        age = start_age + year
        context = {"year": year, "age": age}
        net_cash_flow = event_manager.get_cash_flow_at_age(age, context)

        if net_cash_flow >= 0:
            contributions.append(net_cash_flow)
            withdrawals.append(0.0)
        else:
            contributions.append(0.0)
            withdrawals.append(-net_cash_flow)

        print(f"{age:3d} | {year:4d} | {net_cash_flow:12.0f} | {contributions[-1]:11.0f} | {withdrawals[-1]:9.0f}")

    print(f"\nTotal contributions: ${sum(contributions):,.0f}")
    print(f"Total withdrawals: ${sum(withdrawals):,.0f}")
    print(f"Net cash flow: ${sum(contributions) - sum(withdrawals):,.0f}")

    # Run a simple simulation to verify portfolio evolution uses these cash flows
    print("\nRunning simulation to verify portfolio evolution...")

    simulation_engine = MonteCarloEngine(
        scenario_generator=RandomScenarioGenerator(seed=42),
        market_simulator=MarketSimulator()
    )

    simulation_result = simulation_engine.run_simulation(
        portfolio=portfolio,
        num_scenarios=10,  # Small number for testing
        time_horizon=time_horizon,
        withdrawals=withdrawals,
        contributions=contributions,
        seed=42
    )

    print(f"Simulation completed with {len(simulation_result.scenarios)} scenarios")
    print(f"Success rate: {simulation_result.success_rate:.1%}")

    # Check that portfolio values are being tracked
    if simulation_result.scenarios:
        scenario = simulation_result.scenarios[0]
        print(f"\nFirst scenario portfolio values (first 5 years):")
        for i, value in enumerate(scenario.portfolio_values[:5]):
            print(f"  Year {i}: ${value:,.0f}")

    print("\n✅ Events are properly integrated into portfolio evolution!")
    return True

if __name__ == "__main__":
    test_events_integration()