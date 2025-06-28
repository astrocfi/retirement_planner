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

    def __init__(self, seed: Optional[int] = None):
        if seed is not None:
            np.random.seed(seed)

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

    def __init__(self, correlation_matrix: Optional[Dict[str, Dict[str, float]]] = None):
        self.correlation_matrix = correlation_matrix or {}
        self.logger = RetirementPlannerLogger()

    def simulate_returns(self, assets: Dict[str, Asset], num_years: int) -> Dict[str, List[float]]:
        """Simulate returns for all assets over the given time period."""
        returns = {}

        for asset_name, asset in assets.items():
            # Use asset's expected return and volatility for simulation
            expected_return = asset.expected_return
            volatility = asset.volatility

            # Generate random returns using normal distribution
            # Annual returns are assumed to be normally distributed
            annual_returns = np.random.normal(expected_return, volatility, num_years)

            # Ensure returns are reasonable (not below -100%)
            annual_returns = np.maximum(annual_returns, -0.99)

            returns[asset_name] = annual_returns.tolist()

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
        portfolio_values = [current_portfolio.total_value]
        allocation_percentages = [current_portfolio.get_allocation_percentages()]
        scenario_returns = []

        success = True
        failure_year = None

        # Simulate each year
        for year in range(num_years):
            # Calculate portfolio return for this year
            year_returns = {asset: returns[asset][year] for asset in returns.keys()}
            portfolio_return = self._calculate_portfolio_return(current_portfolio, year_returns)
            scenario_returns.append(portfolio_return)

            # Update portfolio values based on returns
            new_asset_values = {}
            for asset_name, asset in current_portfolio.assets.items():
                if asset_name in year_returns:
                    current_value = current_portfolio.asset_values[asset_name]
                    return_rate = year_returns[asset_name]
                    new_value = current_value * (1 + return_rate)
                    new_asset_values[asset_name] = new_value

            # Create new portfolio with updated values
            current_portfolio = current_portfolio.__class__(
                assets=current_portfolio.assets,
                allocation=current_portfolio.allocation,
                asset_values=new_asset_values,
                rebalancing_strategy=current_portfolio.rebalancing_strategy
            )

            # Apply contributions and withdrawals
            net_cash_flow = contributions[year] - withdrawals[year]
            if net_cash_flow != 0:
                # Distribute cash flow proportionally across assets
                current_portfolio = self._apply_cash_flow(current_portfolio, net_cash_flow)

            # Rebalance portfolio
            current_portfolio = current_portfolio.rebalance()

            # Track portfolio value and allocation
            portfolio_values.append(current_portfolio.total_value)
            allocation_percentages.append(current_portfolio.get_allocation_percentages())

            # Check for failure (portfolio depleted)
            if current_portfolio.total_value <= 0:
                success = False
                failure_year = year
                break

        # Create scenario result
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
        """Calculate portfolio return for a given year."""
        total_return = 0.0
        total_value = portfolio.total_value

        if total_value == 0:
            return 0.0

        for asset_name, return_rate in year_returns.items():
            if asset_name in portfolio.asset_values:
                asset_value = portfolio.asset_values[asset_name]
                asset_weight = asset_value / total_value
                total_return += asset_weight * return_rate

        return total_return

    def _apply_cash_flow(self, portfolio: Portfolio, net_cash_flow: float) -> Portfolio:
        """Apply cash flow to portfolio proportionally across assets."""
        if net_cash_flow == 0:
            return portfolio

        total_value = portfolio.total_value
        if total_value == 0:
            return portfolio

        new_asset_values = {}
        for asset_name, current_value in portfolio.asset_values.items():
            # Distribute cash flow proportionally
            weight = current_value / total_value
            cash_flow_share = net_cash_flow * weight
            new_asset_values[asset_name] = current_value + cash_flow_share

        return portfolio.__class__(
            assets=portfolio.assets,
            allocation=portfolio.allocation,
            asset_values=new_asset_values,
            rebalancing_strategy=portfolio.rebalancing_strategy
        )


class MonteCarloEngine:
    """Main Monte Carlo simulation engine."""

    def __init__(self,
                 scenario_generator: Optional[ScenarioGenerator] = None,
                 market_simulator: Optional[MarketSimulator] = None,
                 logger: Optional[RetirementPlannerLogger] = None):
        self.scenario_generator = scenario_generator or RandomScenarioGenerator()
        self.market_simulator = market_simulator or MarketSimulator()
        self.logger = logger or RetirementPlannerLogger()

    def run_simulation(
        self,
        portfolio: Portfolio,
        num_scenarios: int,
        time_horizon: int,
        withdrawals: List[float],
        contributions: List[float],
        seed: Optional[int] = None
    ) -> SimulationResult:
        """Run Monte Carlo simulation."""
        try:
            self.logger.log(LogLevel.INFO, f"Starting Monte Carlo simulation with {num_scenarios:,} scenarios")

            # Set random seed if provided
            if seed is not None:
                np.random.seed(seed)

            # Generate scenarios
            scenarios = self.scenario_generator.generate_scenarios(num_scenarios, time_horizon)

            # Run simulations
            simulation_scenarios = []
            for i, scenario in enumerate(scenarios):
                self.logger.log(LogLevel.INFO, f"Running scenario {i+1}/{num_scenarios}")

                # Simulate returns for this scenario
                returns = self.market_simulator.simulate_returns(portfolio.assets, time_horizon)

                # Run portfolio simulation
                simulation_scenario = self.market_simulator.simulate_portfolio_evolution(
                    portfolio, returns, withdrawals, contributions
                )

                # Update scenario ID
                simulation_scenario = simulation_scenario.__class__(
                    scenario_id=i,
                    years=simulation_scenario.years,
                    portfolio_values=simulation_scenario.portfolio_values,
                    returns=simulation_scenario.returns,
                    withdrawals=simulation_scenario.withdrawals,
                    contributions=simulation_scenario.contributions,
                    allocation_percentages=simulation_scenario.allocation_percentages,
                    success=simulation_scenario.success,
                    failure_year=simulation_scenario.failure_year,
                    metadata=simulation_scenario.metadata
                )

                simulation_scenarios.append(simulation_scenario)

            # Calculate results
            result = self._calculate_results(simulation_scenarios)

            self.logger.log(LogLevel.SUCCESS, f"Simulation complete. Success rate: {result.success_rate:.1%}")

            return result

        except Exception as e:
            raise SimulationError(f"Simulation failed: {e}") from e

    def _calculate_results(self, scenarios: List[SimulationScenario]) -> SimulationResult:
        """Calculate aggregate results from simulation scenarios."""
        if not scenarios:
            raise SimulationError("No scenarios provided for result calculation")

        # Extract final portfolio values
        final_values = [scenario.portfolio_values[-1] for scenario in scenarios]

        # Calculate success rate
        successful_scenarios = [s for s in scenarios if s.success]
        success_rate = len(successful_scenarios) / len(scenarios)

        # Calculate portfolio value statistics
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
            average_years_to_failure=average_years_to_failure
        )