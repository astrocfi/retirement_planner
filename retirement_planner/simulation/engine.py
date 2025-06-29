"""
Unified simulation engine for retirement planning (tax-aware by default).

This module provides comprehensive tax calculations including federal and state taxes,
capital gains, dividend income, and Social Security taxation.
"""

from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass, field
import numpy as np
from abc import ABC, abstractmethod
from dataclasses import replace
import concurrent.futures
import multiprocessing
from functools import partial

from retirement_planner.models.portfolio import Portfolio
from retirement_planner.assets.base import Asset
from retirement_planner.models.person import Person
from retirement_planner.models.events import EventManager
from retirement_planner.tax.calculator import TaxCalculator, TaxResult
from retirement_planner.core.exceptions import SimulationError
from retirement_planner.core.logging import RetirementPlannerLogger, LogLevel


@dataclass(frozen=True)
class SimulationScenario:
    """Represents a single simulation scenario with tax tracking."""
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
    # Tax tracking fields
    annual_taxes: List[TaxResult] = field(default_factory=list)
    dividend_income: List[float] = field(default_factory=list)
    capital_gains_tax: List[float] = field(default_factory=list)
    income_tax: List[float] = field(default_factory=list)
    total_tax: List[float] = field(default_factory=list)
    effective_tax_rate: List[float] = field(default_factory=list)


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
    """Unified market simulator with tax awareness."""

    def __init__(self, market_model, tax_calculator: Optional[TaxCalculator] = None):
        self.market_model = market_model
        self.tax_calculator = tax_calculator
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
        contributions: List[float],
        person: Optional[Person] = None,
        event_manager: Optional[EventManager] = None,
        inflation_path: Optional[np.ndarray] = None
    ) -> SimulationScenario:
        """Simulate portfolio evolution with comprehensive tax calculations."""
        if len(returns) == 0:
            raise SimulationError("No returns provided for simulation")

        num_years = len(next(iter(returns.values())))

        if len(withdrawals) != num_years:
            raise SimulationError(f"Withdrawals length ({len(withdrawals)}) must match simulation years ({num_years})")

        if len(contributions) != num_years:
            raise SimulationError(f"Contributions length ({len(contributions)}) must match simulation years ({num_years})")

        # Initialize tracking variables
        current_portfolio = portfolio
        initial_value = current_portfolio.total_value
        failure_threshold = initial_value * 0.01
        portfolio_values = [current_portfolio.total_value]
        allocation_percentages = [current_portfolio.get_allocation_percentages()]
        scenario_returns = []
        cumulative_inflation = 1.0
        inflation_factors = [1.0]

        # Tax tracking
        annual_taxes = []
        dividend_income_list = []
        capital_gains_tax_list = []
        income_tax_list = []
        total_tax_list = []
        effective_tax_rate_list = []

        success = True
        failure_year = None

        # Simulate each year
        for year in range(num_years):
            # Tax-aware simulation if tax calculator is available
            if self.tax_calculator and person and event_manager:
                current_age = person.age + year

                # Calculate income events for this year
                income_events = self._get_income_events_for_year(event_manager, current_age)
                social_security_income = self._get_social_security_income(event_manager, current_age)

                # Calculate dividend income from current assets
                dividend_income = sum(asset.get_dividend_income(year) for asset in current_portfolio.assets)
                dividend_income_list.append(dividend_income)

                # Calculate taxes on income and dividends (no capital gains yet)
                tax_result = self.tax_calculator.calculate_annual_taxes(
                    year=year,
                    income_events=income_events,
                    assets=current_portfolio.assets,
                    sold_assets={},  # No sales yet
                    social_security_income=social_security_income
                )

                # Calculate net income after taxes
                net_income = sum(income_events) + dividend_income - tax_result.total_tax

                # Calculate required withdrawal (expenses - net income)
                required_withdrawal = withdrawals[year] - net_income

                # Handle portfolio withdrawals if needed
                sold_assets = {}
                if required_withdrawal > 0:
                    # Need to sell assets to cover expenses
                    withdrawal_result = self.tax_calculator.calculate_withdrawal_tax_impact(
                        assets=current_portfolio.assets,
                        withdrawal_amount=required_withdrawal,
                        year=year
                    )

                    sold_assets = withdrawal_result['sold_assets']

                    # Update portfolio with sold assets
                    current_portfolio = self._apply_asset_sales(current_portfolio, sold_assets)

                    # Recalculate taxes including capital gains from sales
                    tax_result = self.tax_calculator.calculate_annual_taxes(
                        year=year,
                        income_events=income_events,
                        assets=current_portfolio.assets,
                        sold_assets=sold_assets,
                        social_security_income=social_security_income
                    )

                # Handle contributions (excess income)
                if contributions[year] > 0:
                    current_portfolio = self._apply_contributions_with_basis_update(
                        current_portfolio, contributions[year]
                    )

                # Store tax information
                annual_taxes.append(tax_result)
                capital_gains_tax_list.append(tax_result.federal_capital_gains_tax + tax_result.state_capital_gains_tax)
                income_tax_list.append(tax_result.federal_income_tax + tax_result.state_income_tax)
                total_tax_list.append(tax_result.total_tax)
                effective_tax_rate_list.append(tax_result.effective_tax_rate)

            else:
                # Simple simulation without taxes
                net_cash_flow = contributions[year] - withdrawals[year]
                if net_cash_flow != 0:
                    current_portfolio = self._apply_cash_flow(current_portfolio, net_cash_flow)

                # Add empty tax data for consistency
                annual_taxes.append(TaxResult())
                dividend_income_list.append(0.0)
                capital_gains_tax_list.append(0.0)
                income_tax_list.append(0.0)
                total_tax_list.append(0.0)
                effective_tax_rate_list.append(0.0)

            # Apply market returns
            year_returns = {asset: returns[asset][year] for asset in returns.keys()}
            portfolio_return = self._calculate_portfolio_return(current_portfolio, year_returns)
            scenario_returns.append(portfolio_return)

            # Update portfolio values based on returns
            if self.tax_calculator:
                # Preserve cost basis for tax-aware simulation
                current_portfolio = self._apply_returns_preserve_basis(current_portfolio, year_returns)
            else:
                # Simple value update for non-tax simulation
                current_portfolio = self._apply_returns_simple(current_portfolio, year_returns)

            # Rebalance portfolio
            current_portfolio = current_portfolio.rebalance()

            # Apply inflation discount
            if inflation_path is not None:
                cumulative_inflation *= (1 + inflation_path[year])
            inflation_factors.append(cumulative_inflation)

            # Track portfolio value and allocation
            discounted_value = current_portfolio.total_value / cumulative_inflation if cumulative_inflation > 0 else 0.0
            portfolio_values.append(discounted_value)
            allocation_percentages.append(current_portfolio.get_allocation_percentages())

            # Check for failure
            if current_portfolio.total_value <= failure_threshold:
                success = False
                failure_year = year
                break

        # Create scenario result
        expected_length = num_years + 1
        if len(portfolio_values) < expected_length:
            portfolio_values.extend([0.0] * (expected_length - len(portfolio_values)))

        return SimulationScenario(
            scenario_id=0,
            years=list(range(num_years + 1)),
            portfolio_values=portfolio_values,
            returns=scenario_returns,
            withdrawals=withdrawals,
            contributions=contributions,
            allocation_percentages=allocation_percentages,
            success=success,
            failure_year=failure_year,
            metadata={
                "inflation_path": inflation_path.tolist() if inflation_path is not None else None
            },
            annual_taxes=annual_taxes,
            dividend_income=dividend_income_list,
            capital_gains_tax=capital_gains_tax_list,
            income_tax=income_tax_list,
            total_tax=total_tax_list,
            effective_tax_rate=effective_tax_rate_list
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
                    new_asset = replace(asset, current_value=0.0)
                    new_assets.append(new_asset)
            else:
                # Distribute negative cash flow proportionally
                new_assets = []
                for asset in portfolio.assets:
                    asset_weight = asset.current_value / total_value
                    cash_adjustment = net_cash_flow * asset_weight
                    new_value = asset.current_value + cash_adjustment
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
                    new_asset = replace(asset, current_value=cash_per_asset)
                    new_assets.append(new_asset)
            else:
                # Distribute proportionally based on current allocation
                new_assets = []
                for asset in portfolio.assets:
                    asset_weight = asset.current_value / total_value
                    cash_adjustment = net_cash_flow * asset_weight
                    new_value = asset.current_value + cash_adjustment
                    new_asset = replace(asset, current_value=max(new_value, 0.0))
                    new_assets.append(new_asset)

        return portfolio.__class__(
            assets=new_assets,
            allocation_targets=portfolio.allocation_targets,
            rebalancing_strategy=portfolio.rebalancing_strategy
        )

    def _get_income_events_for_year(self, event_manager: EventManager, age: int) -> List[float]:
        """Get income events for a specific age."""
        income_events = []
        for event in event_manager.events:
            if (event.event_type.value == "income" and
                event.period.start_age <= age <= event.period.end_age):
                income_events.append(event.amount)
        return income_events

    def _get_social_security_income(self, event_manager: EventManager, age: int) -> float:
        """Get Social Security income for a specific age."""
        for event in event_manager.events:
            if (event.name.lower() == "social security" and
                event.period.start_age <= age <= event.period.end_age):
                return event.amount
        return 0.0

    def _apply_asset_sales(self, portfolio: Portfolio, sold_assets: Dict[str, float]) -> Portfolio:
        """Apply asset sales to portfolio."""
        new_assets = []
        for asset in portfolio.assets:
            if asset.name in sold_assets:
                amount_sold = sold_assets[asset.name]
                new_value = max(0.0, asset.current_value - amount_sold)

                # Update cost basis proportionally
                if asset.current_value > 0:
                    proportion_remaining = new_value / asset.current_value
                    new_cost_basis = asset.cost_basis * proportion_remaining
                else:
                    new_cost_basis = 0.0

                new_asset = replace(asset, current_value=new_value, cost_basis=new_cost_basis)
                new_assets.append(new_asset)
            else:
                new_assets.append(asset)

        return portfolio.__class__(
            assets=new_assets,
            allocation_targets=portfolio.allocation_targets,
            rebalancing_strategy=portfolio.rebalancing_strategy
        )

    def _apply_contributions_with_basis_update(self, portfolio: Portfolio, contribution: float) -> Portfolio:
        """Apply contributions and update cost basis proportionally."""
        if contribution <= 0:
            return portfolio

        total_value = portfolio.total_value
        new_assets = []

        # Handle case where portfolio has no assets
        if len(portfolio.assets) == 0:
            return portfolio

        # If total value is zero, distribute contribution equally among all assets
        if total_value <= 0:
            # Get target allocations to determine which assets should receive contributions
            target_allocations = portfolio.allocation_targets.allocation if hasattr(portfolio.allocation_targets, 'allocation') else {}

            # If no target allocations, distribute equally
            if not target_allocations:
                equal_share = contribution / len(portfolio.assets)
                for asset in portfolio.assets:
                    new_asset = replace(asset, current_value=equal_share, cost_basis=equal_share)
                    new_assets.append(new_asset)
            else:
                # Distribute based on target allocations
                total_target_weight = sum(target_allocations.values())
                if total_target_weight > 0:
                    for asset in portfolio.assets:
                        target_weight = target_allocations.get(asset.name, 0.0)
                        contribution_amount = contribution * (target_weight / total_target_weight)
                        new_asset = replace(asset, current_value=contribution_amount, cost_basis=contribution_amount)
                        new_assets.append(new_asset)
                else:
                    # Fallback to equal distribution
                    equal_share = contribution / len(portfolio.assets)
                    for asset in portfolio.assets:
                        new_asset = replace(asset, current_value=equal_share, cost_basis=equal_share)
                        new_assets.append(new_asset)
        else:
            # Normal case: distribute proportionally based on current values
            for asset in portfolio.assets:
                asset_weight = asset.current_value / total_value
                contribution_amount = contribution * asset_weight
                new_value = asset.current_value + contribution_amount

                # Update cost basis proportionally
                new_cost_basis = asset.cost_basis + contribution_amount

                new_asset = replace(asset, current_value=new_value, cost_basis=new_cost_basis)
                new_assets.append(new_asset)

        return portfolio.__class__(
            assets=new_assets,
            allocation_targets=portfolio.allocation_targets,
            rebalancing_strategy=portfolio.rebalancing_strategy
        )

    def _apply_returns_preserve_basis(self, portfolio: Portfolio, year_returns: Dict[str, float]) -> Portfolio:
        """Apply returns while preserving cost basis."""
        new_assets = []
        for asset in portfolio.assets:
            current_value = asset.current_value
            if asset.name in year_returns:
                return_rate = year_returns[asset.name]
                new_value = current_value * (1 + return_rate)
            else:
                new_value = current_value

            new_value = max(new_value, 0.0)

            # Preserve cost basis (don't change it for market returns)
            new_asset = replace(asset, current_value=new_value)
            new_assets.append(new_asset)

        return portfolio.__class__(
            assets=new_assets,
            allocation_targets=portfolio.allocation_targets,
            rebalancing_strategy=portfolio.rebalancing_strategy
        )

    def _apply_returns_simple(self, portfolio: Portfolio, year_returns: Dict[str, float]) -> Portfolio:
        """Apply returns with simple value updates (non-tax-aware)."""
        new_assets = []
        for asset in portfolio.assets:
            current_value = asset.current_value
            if asset.name in year_returns:
                return_rate = year_returns[asset.name]
                new_value = current_value * (1 + return_rate)
            else:
                new_value = current_value

            new_value = max(new_value, 0.0)
            new_asset = replace(asset, current_value=new_value)
            new_assets.append(new_asset)

        return portfolio.__class__(
            assets=new_assets,
            allocation_targets=portfolio.allocation_targets,
            rebalancing_strategy=portfolio.rebalancing_strategy
        )


class MonteCarloEngine:
    """Unified Monte Carlo simulation engine with tax awareness."""

    def __init__(self,
                 scenario_generator: Optional[ScenarioGenerator] = None,
                 market_simulator: Optional[MarketSimulator] = None,
                 num_scenarios: int = 10000,
                 tax_calculator: Optional[TaxCalculator] = None,
                 max_workers: Optional[int] = None):
        self.scenario_generator = scenario_generator or RandomScenarioGenerator()
        self.market_simulator = market_simulator
        self.num_scenarios = num_scenarios
        self.tax_calculator = tax_calculator
        self.max_workers = max_workers
        self.logger = RetirementPlannerLogger()

    def run_simulation(
        self,
        portfolio: Portfolio,
        time_horizon: int,
        event_manager: Optional[EventManager] = None,
        person: Optional[Person] = None,
        inflation_mean: float = 0.025,
        inflation_volatility: float = 0.01
    ) -> SimulationResult:
        """Run Monte Carlo simulation with optional tax awareness."""
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

        # Run simulations
        simulation_scenarios = []

        # Use parallel processing for scenario simulation
        max_workers = self.max_workers or min(multiprocessing.cpu_count(), self.num_scenarios)
        self.logger.log(LogLevel.INFO, f"Running {self.num_scenarios} scenarios using {max_workers} parallel workers")

        with concurrent.futures.ProcessPoolExecutor(max_workers=max_workers) as executor:
            # Create a list of scenario parameters
            scenario_params = []
            for i in range(self.num_scenarios):
                scenario_params.append({
                    'scenario_id': i,
                    'portfolio': portfolio,
                    'time_horizon': time_horizon,
                    'withdrawals': withdrawals,
                    'contributions': contributions,
                    'person': person,
                    'event_manager': event_manager,
                    'inflation_mean': inflation_mean,
                    'inflation_volatility': inflation_volatility,
                    'market_model': self.market_simulator.market_model,
                    'tax_calculator': self.tax_calculator
                })

            # Submit all scenarios for parallel execution
            futures = [executor.submit(_run_single_scenario_worker, params) for params in scenario_params]

            # Collect results as they complete
            for i, future in enumerate(concurrent.futures.as_completed(futures)):
                try:
                    result = future.result()
                    simulation_scenarios.append(result)

                    # Log progress every 1000 scenarios
                    if (i + 1) % 1000 == 0:
                        self.logger.log(LogLevel.INFO, f"Completed {i + 1}/{self.num_scenarios} scenarios")

                except Exception as e:
                    self.logger.log(LogLevel.WARNING, f"Scenario {i} failed: {e}")
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
                        failure_year=0,
                        metadata={
                            "inflation_path": [inflation_mean] * time_horizon
                        }
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

        # Calculate tax statistics if available
        tax_scenarios = [s for s in scenarios if hasattr(s, 'total_tax') and s.total_tax]
        if tax_scenarios:
            # Calculate average taxes over time
            max_years = max(len(s.total_tax) for s in tax_scenarios)
            avg_total_tax = []
            avg_effective_tax_rate = []

            for year in range(max_years):
                year_taxes = [s.total_tax[year] for s in tax_scenarios if year < len(s.total_tax)]
                year_rates = [s.effective_tax_rate[year] for s in tax_scenarios if year < len(s.effective_tax_rate)]

                avg_total_tax.append(np.mean(year_taxes) if year_taxes else 0.0)
                avg_effective_tax_rate.append(np.mean(year_rates) if year_rates else 0.0)

            tax_metadata = {
                'average_total_tax': avg_total_tax,
                'average_effective_tax_rate': avg_effective_tax_rate
            }
        else:
            tax_metadata = {}

        return SimulationResult(
            scenarios=scenarios,
            success_rate=success_rate,
            average_portfolio_value=average_portfolio_value,
            median_portfolio_value=median_portfolio_value,
            worst_case_portfolio_value=worst_case_portfolio_value,
            best_case_portfolio_value=best_case_portfolio_value,
            time_horizon=time_horizon,
            average_years_to_failure=average_years_to_failure,
            metadata={**tax_metadata}
        )


def _run_single_scenario_worker(params: Dict[str, Any]) -> SimulationScenario:
    """Worker function for parallel scenario execution.

    This function must be standalone and picklable for multiprocessing.
    """
    try:
        # Extract parameters
        scenario_id = params['scenario_id']
        portfolio = params['portfolio']
        time_horizon = params['time_horizon']
        withdrawals = params['withdrawals']
        contributions = params['contributions']
        person = params['person']
        event_manager = params['event_manager']
        inflation_mean = params['inflation_mean']
        inflation_volatility = params['inflation_volatility']
        market_model = params['market_model']
        tax_calculator = params['tax_calculator']

        # Set unique random seed for this scenario to ensure variation
        np.random.seed(scenario_id)

        # Create a market simulator for this worker
        market_simulator = MarketSimulator(market_model, tax_calculator)

        # Generate unique returns for this scenario
        returns = market_simulator.simulate_returns(portfolio.assets, time_horizon)

        # Generate stochastic inflation path for this scenario
        inflation_path = np.random.normal(inflation_mean, inflation_volatility, time_horizon)
        inflation_path = np.maximum(inflation_path, -0.99)

        # Run the simulation
        result = market_simulator.simulate_portfolio_evolution(
            portfolio=portfolio,
            returns=returns,
            withdrawals=withdrawals,
            contributions=contributions,
            person=person,
            event_manager=event_manager,
            inflation_path=inflation_path
        )

        # Set the scenario ID and store inflation path in metadata
        result = replace(
            result,
            scenario_id=scenario_id,
            metadata={**result.metadata, "inflation_path": inflation_path.tolist()}
        )

        return result

    except Exception as e:
        # Return a failed scenario if there's an error
        return SimulationScenario(
            scenario_id=scenario_id,
            years=list(range(time_horizon + 1)),
            portfolio_values=[portfolio.total_value] + [0.0] * time_horizon,
            returns=[0.0] * time_horizon,
            withdrawals=withdrawals,
            contributions=contributions,
            allocation_percentages=[portfolio.get_allocation_percentages()] + [{}] * time_horizon,
            success=False,
            failure_year=0,
            metadata={
                "inflation_path": [inflation_mean] * time_horizon,
                "error": str(e)
            }
        )