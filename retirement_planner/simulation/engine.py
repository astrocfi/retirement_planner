"""
Monte Carlo simulation engine for retirement planning.

This module provides the core simulation engine for running Monte Carlo
analysis of retirement scenarios.
"""

from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass, field
import numpy as np
from abc import ABC, abstractmethod

from retirement_planner.models.portfolio import Portfolio
from retirement_planner.assets.base import Asset
from retirement_planner.core.exceptions import SimulationError
from retirement_planner.core.logging import RetirementPlannerLogger, LogLevel


@dataclass(frozen=True)
class SimulationScenario:
    """Represents a single simulation scenario."""
    scenario_id: int
    years: List[int]
    portfolio_values: List[float]
    returns: List[float]
    withdrawals: List[float]
    contributions: List[float]
    allocation_percentages: List[Dict[str, float]]
    success: bool
    failure_year: Optional[int] = None
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class SimulationResult:
    """Results from a Monte Carlo simulation."""
    scenarios: List[SimulationScenario]
    success_rate: float
    average_portfolio_value: float
    median_portfolio_value: float
    worst_case_portfolio_value: float
    best_case_portfolio_value: float
    time_horizon: int
    average_years_to_failure: Optional[float] = None
    metadata: Dict[str, Any] = field(default_factory=dict)


class ScenarioGenerator(ABC):
    """Abstract base for scenario generation strategies."""

    @abstractmethod
    def generate_scenarios(self, num_scenarios: int, time_horizon: int) -> List[Dict[str, Any]]:
        """Generate simulation scenarios."""
        pass


class RandomScenarioGenerator(ScenarioGenerator):
    """Generates scenarios using random sampling."""

    def __init__(self, time_horizon: int = 45, random_seed: Optional[int] = None):
        self.time_horizon = time_horizon

    def generate_scenarios(self, num_scenarios: int, time_horizon: int) -> List[Dict[str, Any]]:
        """Generate random scenarios."""
        scenarios = []
        for i in range(num_scenarios):
            scenario = {
                'scenario_id': i,
                'time_horizon': time_horizon,
                'years': list(range(time_horizon))
            }
            scenarios.append(scenario)
        return scenarios


class MarketSimulator:
    """Simulates market returns and portfolio evolution."""

    def __init__(self, market_model):
        self.market_model = market_model
        self.logger = RetirementPlannerLogger()

    def simulate_returns(self, assets: List[Asset], num_years: int) -> Dict[str, List[float]]:
        """Simulate returns for all assets over the given time period."""
        # Convert list of assets to dictionary for market model
        assets_dict = {asset.name: asset for asset in assets}
        returns = self.market_model.simulate_returns(assets_dict, num_years)
        return returns

    def simulate_portfolio_evolution(
        self,
        portfolio: Portfolio,
        returns: Dict[str, List[float]],
        withdrawals: List[float],
        contributions: List[float]
    ) -> SimulationScenario:
        """Simulate portfolio evolution over time."""
        if len(returns) == 0:
            raise SimulationError("No returns provided for simulation")

        # Get the number of years from the first asset's returns
        num_years = len(next(iter(returns.values())))

        if len(withdrawals) != num_years:
            raise SimulationError(f"Withdrawals length ({len(withdrawals)}) must match simulation years ({num_years})")

        if len(contributions) != num_years:
            raise SimulationError(f"Contributions length ({len(contributions)}) must match simulation years ({num_years})")

        # Initialize tracking variables
        current_portfolio = portfolio
        initial_value = current_portfolio.total_value
        failure_threshold = initial_value * 0.01  # 1% of initial value
        portfolio_values = [current_portfolio.total_value]
        allocation_percentages = [current_portfolio.get_allocation_percentages()]
        scenario_returns = []

        success = True
        failure_year = None

        # Simulate each year
        for year in range(num_years):
            # Apply contributions and withdrawals FIRST
            net_cash_flow = contributions[year] - withdrawals[year]
            if net_cash_flow != 0:
                # Distribute cash flow proportionally across assets
                current_portfolio = self._apply_cash_flow(current_portfolio, net_cash_flow)

            # Calculate portfolio return for this year (on the post-cash-flow portfolio)
            year_returns = {asset: returns[asset][year] for asset in returns.keys()}
            portfolio_return = self._calculate_portfolio_return(current_portfolio, year_returns)
            scenario_returns.append(portfolio_return)

            # Update portfolio values based on returns
            new_assets = []
            for asset in current_portfolio.assets:
                current_value = asset.current_value
                if asset.name in year_returns:
                    return_rate = year_returns[asset.name]
                    new_value = current_value * (1 + return_rate)
                else:
                    # If no return data for this asset, keep the same value
                    new_value = current_value
                # Clamp asset value to zero (never negative)
                new_value = max(new_value, 0.0)

                # Create new asset with updated value
                from dataclasses import replace
                new_asset = replace(asset, current_value=new_value)
                new_assets.append(new_asset)

            # Create new portfolio with updated assets
            current_portfolio = current_portfolio.__class__(
                assets=new_assets,
                allocation_targets=current_portfolio.allocation_targets,
                rebalancing_strategy=current_portfolio.rebalancing_strategy
            )

            # Rebalance portfolio
            current_portfolio = current_portfolio.rebalance()

            # Track portfolio value and allocation
            portfolio_values.append(current_portfolio.total_value)
            allocation_percentages.append(current_portfolio.get_allocation_percentages())

            # Check for failure (portfolio depleted or below threshold)
            if current_portfolio.total_value <= failure_threshold:
                success = False
                failure_year = year
                break

        # Create scenario result
        # Ensure portfolio_values has the correct length for all scenarios
        expected_length = num_years + 1
        if len(portfolio_values) < expected_length:
            # Pad with zeros for failed scenarios
            portfolio_values.extend([0.0] * (expected_length - len(portfolio_values)))

        return SimulationScenario(
            scenario_id=0,  # Will be set by the engine
            years=list(range(num_years + 1)),
            portfolio_values=portfolio_values,
            returns=scenario_returns,
            withdrawals=withdrawals,
            contributions=contributions,
            allocation_percentages=allocation_percentages,
            success=success,
            failure_year=failure_year
        )

    def _calculate_portfolio_return(self, portfolio: Portfolio, year_returns: Dict[str, float]) -> float:
        """Calculate the weighted portfolio return for a given year."""
        total_return = 0.0
        total_value = portfolio.total_value

        if total_value == 0:
            return 0.0

        for asset in portfolio.assets:
            if asset.name in year_returns:
                asset_weight = asset.current_value / total_value
                total_return += asset_weight * year_returns[asset.name]

        return total_return

    def _apply_cash_flow(self, portfolio: Portfolio, net_cash_flow: float) -> Portfolio:
        """Apply cash flow to portfolio by distributing proportionally across assets."""
        if net_cash_flow == 0:
            return portfolio

        total_value = portfolio.total_value

        # Handle negative cash flow (expenses)
        if net_cash_flow < 0:
            # If expenses exceed portfolio value, set all assets to zero
            if abs(net_cash_flow) >= total_value:
                new_assets = []
                for asset in portfolio.assets:
                    from dataclasses import replace
                    new_asset = replace(asset, current_value=0.0)
                    new_assets.append(new_asset)
            else:
                # Distribute negative cash flow proportionally
                new_assets = []
                for asset in portfolio.assets:
                    asset_weight = asset.current_value / total_value
                    cash_adjustment = net_cash_flow * asset_weight
                    new_value = asset.current_value + cash_adjustment
                    from dataclasses import replace
                    new_asset = replace(asset, current_value=max(new_value, 0.0))
                    new_assets.append(new_asset)
        else:
            # Handle positive cash flow (contributions)
            if total_value == 0:
                # If portfolio is empty, distribute equally
                num_assets = len(portfolio.assets)
                if num_assets == 0:
                    return portfolio
                cash_per_asset = net_cash_flow / num_assets
                new_assets = []
                for asset in portfolio.assets:
                    from dataclasses import replace
                    new_asset = replace(asset, current_value=cash_per_asset)
                    new_assets.append(new_asset)
            else:
                # Distribute proportionally based on current allocation
                new_assets = []
                for asset in portfolio.assets:
                    asset_weight = asset.current_value / total_value
                    cash_adjustment = net_cash_flow * asset_weight
                    new_value = asset.current_value + cash_adjustment
                    from dataclasses import replace
                    new_asset = replace(asset, current_value=max(new_value, 0.0))
                    new_assets.append(new_asset)

        return portfolio.__class__(
            assets=new_assets,
            allocation_targets=portfolio.allocation_targets,
            rebalancing_strategy=portfolio.rebalancing_strategy
        )


class MonteCarloEngine:
    """Main Monte Carlo simulation engine."""

    def __init__(self,
                 scenario_generator: Optional[ScenarioGenerator] = None,
                 market_simulator: Optional[MarketSimulator] = None,
                 num_scenarios: int = 10000):
        self.scenario_generator = scenario_generator or RandomScenarioGenerator()
        self.market_simulator = market_simulator
        self.num_scenarios = num_scenarios
        self.logger = RetirementPlannerLogger()

    def run_simulation(
        self,
        portfolio: Portfolio,
        time_horizon: int,
        event_manager=None,
        person=None
    ) -> SimulationResult:
        """Run Monte Carlo simulation."""
        self.logger.log(LogLevel.INFO, f"Starting Monte Carlo simulation with {self.num_scenarios} scenarios")

        # Generate scenarios
        scenarios = self.scenario_generator.generate_scenarios(self.num_scenarios, time_horizon)

        # Calculate cash flows from events if event_manager is provided
        if event_manager:
            withdrawals = []
            contributions = []
            retirement_age = person.retirement_age if person else 65
            for year in range(time_horizon):
                year_income = 0.0
                year_expenses = 0.0

                # Calculate income and expenses for this year based on events
                for event in event_manager.events:
                    if event.period.start_age <= (year + retirement_age) <= event.period.end_age:
                        if event.event_type.value == "income":
                            year_income += event.amount
                        elif event.event_type.value == "expense":
                            year_expenses += event.amount

                contributions.append(year_income)
                withdrawals.append(year_expenses)
        else:
            # Fallback to zero cash flows if no event manager
            withdrawals = [0.0] * time_horizon
            contributions = [0.0] * time_horizon

        # Run simulations - each scenario gets its own random returns
        simulation_scenarios = []
        for i, scenario in enumerate(scenarios):
            try:
                # Generate unique returns for this scenario
                returns = self.market_simulator.simulate_returns(portfolio.assets, time_horizon)

                result = self.market_simulator.simulate_portfolio_evolution(
                    portfolio=portfolio,
                    returns=returns,
                    withdrawals=withdrawals,
                    contributions=contributions
                )
                # Set the scenario ID
                result = result.__class__(
                    scenario_id=i,
                    years=result.years,
                    portfolio_values=result.portfolio_values,
                    returns=result.returns,
                    withdrawals=result.withdrawals,
                    contributions=result.contributions,
                    allocation_percentages=result.allocation_percentages,
                    success=result.success,
                    failure_year=result.failure_year,
                    metadata=result.metadata
                )
                simulation_scenarios.append(result)
            except Exception as e:
                self.logger.log(LogLevel.ERROR, f"Scenario {i} failed: {e}")
                # Create a failed scenario
                failed_scenario = SimulationScenario(
                    scenario_id=i,
                    years=list(range(time_horizon + 1)),
                    portfolio_values=[portfolio.total_value] + [0.0] * time_horizon,
                    returns=[0.0] * time_horizon,
                    withdrawals=withdrawals,
                    contributions=contributions,
                    allocation_percentages=[portfolio.get_allocation_percentages()] + [{}] * time_horizon,
                    success=False,
                    failure_year=0
                )
                simulation_scenarios.append(failed_scenario)

        # Calculate results
        result = self._calculate_results(simulation_scenarios, time_horizon)

        self.logger.log(LogLevel.SUCCESS, f"Simulation completed. Success rate: {result.success_rate:.1%}")
        return result

    def _calculate_results(self, scenarios: List[SimulationScenario], time_horizon: int) -> SimulationResult:
        """Calculate aggregate results from simulation scenarios."""
        if not scenarios:
            raise SimulationError("No scenarios provided for result calculation")

        # Calculate success rate
        successful_scenarios = [s for s in scenarios if s.success]
        success_rate = len(successful_scenarios) / len(scenarios)

        # Calculate portfolio value statistics at the end of the simulation
        final_values = [s.portfolio_values[-1] for s in scenarios]
        average_portfolio_value = np.mean(final_values)
        median_portfolio_value = np.median(final_values)
        worst_case_portfolio_value = np.min(final_values)
        best_case_portfolio_value = np.max(final_values)

        # Calculate average years to failure for failed scenarios
        failed_scenarios = [s for s in scenarios if not s.success]
        if failed_scenarios:
            failure_years = [s.failure_year for s in failed_scenarios if s.failure_year is not None]
            average_years_to_failure = np.mean(failure_years) if failure_years else None
        else:
            average_years_to_failure = None

        return SimulationResult(
            scenarios=scenarios,
            success_rate=success_rate,
            average_portfolio_value=average_portfolio_value,
            median_portfolio_value=median_portfolio_value,
            worst_case_portfolio_value=worst_case_portfolio_value,
            best_case_portfolio_value=best_case_portfolio_value,
            time_horizon=time_horizon,
            average_years_to_failure=average_years_to_failure
        )