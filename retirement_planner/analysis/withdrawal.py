"""
Withdrawal strategy optimization for retirement planning.

This module provides withdrawal strategy implementations and optimization
capabilities for retirement income planning.
"""

from typing import Dict, List, Optional, Any, Tuple, Callable
from dataclasses import dataclass, field
import numpy as np
from abc import ABC, abstractmethod
import copy

from retirement_planner.models.portfolio import Portfolio
from retirement_planner.simulation.engine import SimulationResult, SimulationScenario
from retirement_planner.core.exceptions import AnalysisError
from retirement_planner.core.logging import RetirementPlannerLogger, LogLevel


@dataclass(frozen=True)
class WithdrawalPlan:
    """A withdrawal plan with annual amounts."""
    annual_withdrawals: List[float]
    total_withdrawn: float
    average_withdrawal: float
    withdrawal_rate: float
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class WithdrawalOptimizationResult:
    """Results of withdrawal strategy optimization."""
    optimal_withdrawal_rate: float
    optimal_annual_withdrawal: float
    success_rate: float
    average_portfolio_value: float
    worst_case_portfolio_value: float
    risk_metrics: Dict[str, float]
    recommendations: List[str]
    metadata: Dict[str, Any] = field(default_factory=dict)


class WithdrawalStrategy(ABC):
    """Abstract base for withdrawal strategies."""

    @abstractmethod
    def calculate_withdrawals(self,
                            portfolio: Portfolio,
                            num_years: int,
                            **kwargs) -> WithdrawalPlan:
        """Calculate withdrawal amounts for the given period."""
        pass


class FixedWithdrawalStrategy(WithdrawalStrategy):
    """Fixed dollar amount withdrawal strategy."""

    def __init__(self, annual_amount: float):
        self.annual_amount = annual_amount

    def calculate_withdrawals(self,
                            portfolio: Portfolio,
                            num_years: int,
                            **kwargs) -> WithdrawalPlan:
        """Calculate fixed annual withdrawals."""
        withdrawals = [self.annual_amount] * num_years
        total_withdrawn = self.annual_amount * num_years
        withdrawal_rate = self.annual_amount / portfolio.total_value

        return WithdrawalPlan(
            annual_withdrawals=withdrawals,
            total_withdrawn=total_withdrawn,
            average_withdrawal=self.annual_amount,
            withdrawal_rate=withdrawal_rate
        )


class PercentageWithdrawalStrategy(WithdrawalStrategy):
    """Percentage-based withdrawal strategy."""

    def __init__(self, withdrawal_rate: float):
        self.withdrawal_rate = withdrawal_rate

    def calculate_withdrawals(self,
                            portfolio: Portfolio,
                            num_years: int,
                            **kwargs) -> WithdrawalPlan:
        """Calculate percentage-based withdrawals."""
        initial_withdrawal = portfolio.total_value * self.withdrawal_rate
        withdrawals = [initial_withdrawal] * num_years
        total_withdrawn = initial_withdrawal * num_years

        return WithdrawalPlan(
            annual_withdrawals=withdrawals,
            total_withdrawn=total_withdrawn,
            average_withdrawal=initial_withdrawal,
            withdrawal_rate=self.withdrawal_rate
        )


class InflationAdjustedWithdrawalStrategy(WithdrawalStrategy):
    """Inflation-adjusted withdrawal strategy (4% rule variant)."""

    def __init__(self, initial_withdrawal_rate: float, inflation_rate: float = 0.02):
        self.initial_withdrawal_rate = initial_withdrawal_rate
        self.inflation_rate = inflation_rate

    def calculate_withdrawals(self,
                            portfolio: Portfolio,
                            num_years: int,
                            **kwargs) -> WithdrawalPlan:
        """Calculate inflation-adjusted withdrawals."""
        initial_withdrawal = portfolio.total_value * self.initial_withdrawal_rate
        withdrawals = []

        for year in range(num_years):
            withdrawal = initial_withdrawal * (1 + self.inflation_rate) ** year
            withdrawals.append(withdrawal)

        total_withdrawn = sum(withdrawals)
        avg_withdrawal = total_withdrawn / num_years

        return WithdrawalPlan(
            annual_withdrawals=withdrawals,
            total_withdrawn=total_withdrawn,
            average_withdrawal=avg_withdrawal,
            withdrawal_rate=self.initial_withdrawal_rate
        )


class DynamicWithdrawalStrategy(WithdrawalStrategy):
    """Dynamic withdrawal strategy based on portfolio performance."""

    def __init__(self,
                 base_withdrawal_rate: float,
                 floor_rate: float = 0.02,
                 ceiling_rate: float = 0.06,
                 adjustment_factor: float = 0.1):
        self.base_withdrawal_rate = base_withdrawal_rate
        self.floor_rate = floor_rate
        self.ceiling_rate = ceiling_rate
        self.adjustment_factor = adjustment_factor

    def calculate_withdrawals(self,
                            portfolio: Portfolio,
                            num_years: int,
                            **kwargs) -> WithdrawalPlan:
        """Calculate dynamic withdrawals based on portfolio performance."""
        # This is a simplified version - in practice, would need portfolio performance data
        initial_withdrawal = portfolio.total_value * self.base_withdrawal_rate
        withdrawals = [initial_withdrawal] * num_years  # Simplified for now

        total_withdrawn = sum(withdrawals)
        avg_withdrawal = total_withdrawn / num_years

        return WithdrawalPlan(
            annual_withdrawals=withdrawals,
            total_withdrawn=total_withdrawn,
            average_withdrawal=avg_withdrawal,
            withdrawal_rate=self.base_withdrawal_rate
        )


class WithdrawalOptimizer:
    """Optimizes withdrawal strategies for retirement planning."""

    def __init__(self,
                 strategy_factory: Optional[Callable] = None,
                 logger: Optional[RetirementPlannerLogger] = None):
        self.strategy_factory = strategy_factory or self._default_strategy_factory
        self.logger = logger or RetirementPlannerLogger()

    def optimize_withdrawal_rate(self,
                                portfolio: Portfolio,
                                simulation_result: SimulationResult,
                                strategy_type: str = "percentage",
                                min_rate: float = 0.001,  # 0.1%
                                max_rate: float = 0.10,   # 10%
                                target_success_rate: float = 0.8) -> WithdrawalOptimizationResult:
        """Find optimal withdrawal rate using binary search for efficiency."""
        try:
            self.logger.log(LogLevel.INFO, f"Optimizing withdrawal rate for {strategy_type} strategy")

            # Import here to avoid circular imports
            from retirement_planner.simulation.engine import MonteCarloEngine, RandomScenarioGenerator, MarketSimulator
            from retirement_planner.simulation.market import SimpleMarketModel

            # Create simulation engine (reuse the same setup as main simulation)
            time_horizon = simulation_result.time_horizon
            num_scenarios = len(simulation_result.scenarios)

            # Use SimpleMarketModel since we don't need correlation for single asset
            market_model = SimpleMarketModel()
            market_simulator = MarketSimulator(market_model)

            engine = MonteCarloEngine(
                scenario_generator=RandomScenarioGenerator(time_horizon=time_horizon),
                market_simulator=market_simulator,
                num_scenarios=num_scenarios
            )

            # Binary search for the highest rate that achieves target success rate
            best_rate = min_rate
            best_success_rate = 0.0
            best_metrics = {}
            best_simulation_result = None

            # Binary search parameters
            tolerance = 0.001  # 0.1% precision
            left = min_rate
            right = max_rate

            self.logger.log(LogLevel.INFO, f"Binary search: target success rate {target_success_rate:.1%}")

            while right - left > tolerance:
                mid = (left + right) / 2

                # Test the middle rate
                strategy = self.strategy_factory(strategy_type, mid)
                withdrawal_plan = strategy.calculate_withdrawals(portfolio, time_horizon)

                new_simulation_result = self._run_withdrawal_simulation(
                    engine, portfolio, withdrawal_plan, time_horizon
                )

                success_rate = new_simulation_result.success_rate
                self.logger.log(LogLevel.INFO, f"Testing rate {mid:.1%}: {success_rate:.1%} success")

                if success_rate >= target_success_rate:
                    # This rate works, try a higher rate
                    best_rate = mid
                    best_success_rate = success_rate
                    best_simulation_result = new_simulation_result
                    best_metrics = self._calculate_optimization_metrics(
                        withdrawal_plan, new_simulation_result
                    )
                    left = mid
                else:
                    # This rate fails, try a lower rate
                    right = mid

            # If we didn't find any rate that meets the target, just return the best we found
            if best_success_rate < target_success_rate:
                self.logger.log(LogLevel.INFO, f"No rate achieved {target_success_rate:.1%} success. Best available: {best_rate:.1%} with {best_success_rate:.1%} success")

            # Generate recommendations
            recommendations = self._generate_optimization_recommendations(
                best_rate, best_success_rate, best_metrics
            )

            result = WithdrawalOptimizationResult(
                optimal_withdrawal_rate=best_rate,
                optimal_annual_withdrawal=portfolio.total_value * best_rate,
                success_rate=best_success_rate,
                average_portfolio_value=best_metrics.get('average_portfolio_value', 0.0),
                worst_case_portfolio_value=best_metrics.get('worst_case_portfolio_value', 0.0),
                risk_metrics=best_metrics,
                recommendations=recommendations
            )

            self.logger.log(LogLevel.SUCCESS,
                           f"Optimization complete. Optimal rate: {best_rate:.1%}, Success: {best_success_rate:.1%}")

            return result

        except Exception as e:
            raise AnalysisError(f"Withdrawal optimization failed: {e}") from e

    def _run_withdrawal_simulation(self, engine, portfolio, withdrawal_plan, time_horizon):
        """Run a simulation with the given withdrawal plan."""
        # Create custom withdrawals and zero contributions for this test
        withdrawals = withdrawal_plan.annual_withdrawals
        contributions = [0.0] * time_horizon

        # Run simulation with these specific withdrawals
        simulation_scenarios = []

        for i in range(engine.num_scenarios):
            try:
                # Generate unique returns for this scenario
                returns = engine.market_simulator.simulate_returns(portfolio.assets, time_horizon)

                # Deep copy the portfolio so each scenario starts fresh
                scenario_portfolio = copy.deepcopy(portfolio)

                result = engine.market_simulator.simulate_portfolio_evolution(
                    portfolio=scenario_portfolio,
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
                from retirement_planner.simulation.engine import SimulationScenario
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
        result = engine._calculate_results(simulation_scenarios, time_horizon)

        return result

    def _default_strategy_factory(self, strategy_type: str, rate: float) -> WithdrawalStrategy:
        """Default factory for creating withdrawal strategies."""
        if strategy_type == "percentage":
            return PercentageWithdrawalStrategy(rate)
        elif strategy_type == "fixed":
            return FixedWithdrawalStrategy(rate)
        elif strategy_type == "inflation_adjusted":
            return InflationAdjustedWithdrawalStrategy(rate)
        elif strategy_type == "dynamic":
            return DynamicWithdrawalStrategy(rate)
        else:
            raise AnalysisError(f"Unknown strategy type: {strategy_type}")

    def _calculate_optimization_metrics(self,
                                      withdrawal_plan: WithdrawalPlan,
                                      simulation_result: SimulationResult) -> Dict[str, float]:
        """Calculate metrics for optimization result."""
        final_values = [scenario.portfolio_values[-1] for scenario in simulation_result.scenarios]

        return {
            'average_portfolio_value': np.mean(final_values),
            'worst_case_portfolio_value': np.min(final_values),
            'best_case_portfolio_value': np.max(final_values),
            'volatility': np.std(final_values),
            'total_withdrawn': withdrawal_plan.total_withdrawn,
            'average_withdrawal': withdrawal_plan.average_withdrawal
        }

    def _generate_optimization_recommendations(self,
                                             optimal_rate: float,
                                             success_rate: float,
                                             metrics: Dict[str, float]) -> List[str]:
        """Generate recommendations based on optimization results."""
        recommendations = []

        if success_rate < 0.8:
            recommendations.append("Consider reducing withdrawal rate to improve success probability")

        if optimal_rate < 0.03:
            recommendations.append("Very conservative withdrawal rate - consider increasing if comfortable with risk")
        elif optimal_rate > 0.06:
            recommendations.append("High withdrawal rate - ensure you have backup income sources")

        if metrics.get('volatility', 0) > 0.3:
            recommendations.append("High portfolio volatility - consider more conservative withdrawal strategy")

        return recommendations