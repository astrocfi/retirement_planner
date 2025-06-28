"""
Retirement analysis engine for goal tracking and success calculation.

This module provides the core analysis capabilities for retirement planning,
including goal tracking, success probability calculation, and retirement
outcome analysis.
"""

from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, field
import numpy as np
from abc import ABC, abstractmethod

from retirement_planner.models.person import Person
from retirement_planner.models.portfolio import Portfolio
from retirement_planner.simulation.engine import SimulationResult, SimulationScenario
from retirement_planner.core.exceptions import AnalysisError
from retirement_planner.core.logging import RetirementPlannerLogger, LogLevel


@dataclass(frozen=True)
class GoalStatus:
    """Status of a retirement goal."""
    goal_name: str
    achieved: bool
    success_rate: float
    average_shortfall: float
    worst_case_shortfall: float
    years_to_achievement: Optional[float] = None
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class RetirementAnalysis:
    """Results of retirement analysis."""
    person: Person
    portfolio: Portfolio
    simulation_result: SimulationResult
    goal_statuses: List[GoalStatus]
    overall_success_rate: float
    average_retirement_duration: float
    risk_metrics: Dict[str, float]
    recommendations: List[str]
    metadata: Dict[str, Any] = field(default_factory=dict)


class GoalTracker:
    """Tracks retirement goals and their achievement status."""

    def __init__(self, person: Person):
        self.person = person
        self.logger = RetirementPlannerLogger()

    def track_goals(self, simulation_result: SimulationResult) -> List[GoalStatus]:
        """Track all person's goals against simulation results."""
        goal_statuses = []

        for goal in self.person.goals:
            self.logger.log(LogLevel.INFO, f"Analyzing goal: {goal.name}")

            if goal.goal_type == "income":
                status = self._track_retirement_income_goal(goal, simulation_result)
            elif goal.goal_type == "legacy":
                status = self._track_portfolio_value_goal(goal, simulation_result)
            elif goal.goal_type == "lifestyle":
                status = self._track_withdrawal_rate_goal(goal, simulation_result)
            elif goal.goal_type == "min_portfolio_value":
                status = self._track_min_portfolio_value_goal(goal, simulation_result)
            else:
                status = self._track_generic_goal(goal, simulation_result)

            goal_statuses.append(status)

        return goal_statuses

    def _track_retirement_income_goal(self, goal, simulation_result: SimulationResult) -> GoalStatus:
        """Track retirement income goal."""
        target_income = goal.target_amount
        achieved_scenarios = 0
        shortfalls = []
        years_to_achievement = []

        for scenario in simulation_result.scenarios:
            if not scenario.success:
                shortfalls.append(target_income)  # Complete failure
                continue

            # Calculate average annual income from portfolio
            total_withdrawals = sum(scenario.withdrawals)
            avg_annual_income = total_withdrawals / len(scenario.withdrawals)

            if avg_annual_income >= target_income:
                achieved_scenarios += 1
                shortfalls.append(0.0)
                # Calculate years to achieve target income
                years = self._calculate_years_to_target_income(scenario, target_income)
                if years is not None:
                    years_to_achievement.append(years)
            else:
                shortfalls.append(target_income - avg_annual_income)

        success_rate = achieved_scenarios / len(simulation_result.scenarios)
        avg_shortfall = np.mean(shortfalls) if shortfalls else 0.0
        worst_shortfall = np.max(shortfalls) if shortfalls else 0.0
        avg_years = np.mean(years_to_achievement) if years_to_achievement else None

        return GoalStatus(
            goal_name=goal.name,
            achieved=success_rate >= 0.8,  # 80% success threshold
            success_rate=success_rate,
            average_shortfall=avg_shortfall,
            worst_case_shortfall=worst_shortfall,
            years_to_achievement=avg_years
        )

    def _track_portfolio_value_goal(self, goal, simulation_result: SimulationResult) -> GoalStatus:
        """Track portfolio value goal."""
        target_value = goal.target_amount
        achieved_scenarios = 0
        shortfalls = []

        for scenario in simulation_result.scenarios:
            final_value = scenario.portfolio_values[-1]

            if final_value >= target_value:
                achieved_scenarios += 1
                shortfalls.append(0.0)
            else:
                shortfalls.append(target_value - final_value)

        success_rate = achieved_scenarios / len(simulation_result.scenarios)
        avg_shortfall = np.mean(shortfalls) if shortfalls else 0.0
        worst_shortfall = np.max(shortfalls) if shortfalls else 0.0

        return GoalStatus(
            goal_name=goal.name,
            achieved=success_rate >= 0.8,
            success_rate=success_rate,
            average_shortfall=avg_shortfall,
            worst_case_shortfall=worst_shortfall
        )

    def _track_withdrawal_rate_goal(self, goal, simulation_result: SimulationResult) -> GoalStatus:
        """Track withdrawal rate goal."""
        target_rate = goal.target_amount / 100.0  # Convert percentage to decimal
        achieved_scenarios = 0
        shortfalls = []

        for scenario in simulation_result.scenarios:
            if not scenario.success:
                shortfalls.append(target_rate)  # Complete failure
                continue

            # Calculate average withdrawal rate
            total_withdrawals = sum(scenario.withdrawals)
            avg_portfolio_value = np.mean(scenario.portfolio_values[:-1])  # Exclude final value
            avg_withdrawal_rate = total_withdrawals / (len(scenario.withdrawals) * avg_portfolio_value)

            if avg_withdrawal_rate <= target_rate:
                achieved_scenarios += 1
                shortfalls.append(0.0)
            else:
                shortfalls.append(avg_withdrawal_rate - target_rate)

        success_rate = achieved_scenarios / len(simulation_result.scenarios)
        avg_shortfall = np.mean(shortfalls) if shortfalls else 0.0
        worst_shortfall = np.max(shortfalls) if shortfalls else 0.0

        return GoalStatus(
            goal_name=goal.name,
            achieved=success_rate >= 0.8,
            success_rate=success_rate,
            average_shortfall=avg_shortfall,
            worst_case_shortfall=worst_shortfall
        )

    def _track_min_portfolio_value_goal(self, goal, simulation_result: SimulationResult) -> GoalStatus:
        """Track minimum portfolio value goal (portfolio never depletes below threshold)."""
        min_value = goal.target_amount
        achieved_scenarios = 0
        shortfalls = []

        for scenario in simulation_result.scenarios:
            min_portfolio = min(scenario.portfolio_values)
            if min_portfolio >= min_value:
                achieved_scenarios += 1
                shortfalls.append(0.0)
            else:
                shortfalls.append(min_value - min_portfolio)

        success_rate = achieved_scenarios / len(simulation_result.scenarios)
        avg_shortfall = np.mean(shortfalls) if shortfalls else 0.0
        worst_shortfall = np.max(shortfalls) if shortfalls else 0.0

        return GoalStatus(
            goal_name=goal.name,
            achieved=success_rate >= 0.8,
            success_rate=success_rate,
            average_shortfall=avg_shortfall,
            worst_case_shortfall=worst_shortfall
        )

    def _track_generic_goal(self, goal, simulation_result: SimulationResult) -> GoalStatus:
        """Track generic goal (fallback)."""
        # Default to portfolio value goal for unknown goal types
        return self._track_portfolio_value_goal(goal, simulation_result)

    def _calculate_years_to_target_income(self, scenario: SimulationScenario, target_income: float) -> Optional[float]:
        """Calculate years to achieve target income."""
        for i, withdrawal in enumerate(scenario.withdrawals):
            if withdrawal >= target_income:
                return float(i)
        return None


class SuccessCalculator:
    """Calculates success probabilities and retirement metrics."""

    def __init__(self):
        self.logger = RetirementPlannerLogger()

    def calculate_overall_success_rate(self, goal_statuses: List[GoalStatus]) -> float:
        """Calculate overall success rate across all goals."""
        if not goal_statuses:
            return 0.0

        # Weight all goals equally for now
        success_rates = [status.success_rate for status in goal_statuses]
        return np.mean(success_rates)

    def calculate_retirement_duration(self, simulation_result: SimulationResult) -> float:
        """Calculate average retirement duration."""
        durations = []

        for scenario in simulation_result.scenarios:
            if scenario.success:
                duration = len(scenario.years) - 1  # Subtract initial year
            else:
                duration = scenario.failure_year if scenario.failure_year is not None else 0

            durations.append(duration)

        return np.mean(durations) if durations else 0.0

    def calculate_risk_metrics(self, simulation_result: SimulationResult) -> Dict[str, float]:
        """Calculate various risk metrics."""
        final_values = [scenario.portfolio_values[-1] for scenario in simulation_result.scenarios]

        # Value at Risk (95th percentile)
        var_95 = np.percentile(final_values, 5)

        # Conditional Value at Risk (Expected Shortfall)
        cvar_95 = np.mean([v for v in final_values if v <= var_95])

        # Maximum Drawdown
        max_drawdowns = []
        for scenario in simulation_result.scenarios:
            if len(scenario.portfolio_values) > 1:
                peak = max(scenario.portfolio_values)
                drawdown = (peak - min(scenario.portfolio_values)) / peak
                max_drawdowns.append(drawdown)

        avg_max_drawdown = np.mean(max_drawdowns) if max_drawdowns else 0.0

        # Volatility of final values
        volatility = np.std(final_values) if len(final_values) > 1 else 0.0

        return {
            'var_95': var_95,
            'cvar_95': cvar_95,
            'avg_max_drawdown': avg_max_drawdown,
            'volatility': volatility,
            'worst_case_value': np.min(final_values),
            'best_case_value': np.max(final_values)
        }

    def generate_recommendations(self, analysis: RetirementAnalysis) -> List[str]:
        """Generate recommendations based on analysis results."""
        recommendations = []

        # Overall success rate recommendations
        if analysis.overall_success_rate < 0.5:
            recommendations.append("Consider increasing savings or delaying retirement")
        elif analysis.overall_success_rate < 0.8:
            recommendations.append("Consider moderate adjustments to retirement plan")
        else:
            recommendations.append("Retirement plan appears sustainable")

        # Goal-specific recommendations
        for status in analysis.goal_statuses:
            if status.success_rate < 0.8:
                recommendations.append(f"Goal '{status.goal_name}' needs attention - {status.success_rate:.1%} success rate")

        # Risk-based recommendations
        risk_metrics = analysis.risk_metrics
        if risk_metrics['avg_max_drawdown'] > 0.3:
            recommendations.append("Consider reducing portfolio risk to minimize drawdowns")

        if risk_metrics['volatility'] > 0.2:
            recommendations.append("Portfolio volatility is high - consider diversification")

        return recommendations


class RetirementAnalyzer:
    """Main retirement analysis orchestrator."""

    def __init__(self,
                 goal_tracker: Optional[GoalTracker] = None,
                 success_calculator: Optional[SuccessCalculator] = None,
                 logger: Optional[RetirementPlannerLogger] = None):
        self.goal_tracker = goal_tracker
        self.success_calculator = success_calculator or SuccessCalculator()
        self.logger = logger or RetirementPlannerLogger()

    def analyze_retirement(self,
                          person: Person,
                          portfolio: Portfolio,
                          simulation_result: SimulationResult) -> RetirementAnalysis:
        """Perform comprehensive retirement analysis."""
        try:
            self.logger.log(LogLevel.INFO, f"Starting retirement analysis for {person.name}")

            # Track goals
            goal_tracker = self.goal_tracker or GoalTracker(person)
            goal_statuses = goal_tracker.track_goals(simulation_result)

            # Calculate overall success rate
            overall_success_rate = self.success_calculator.calculate_overall_success_rate(goal_statuses)

            # Calculate retirement duration
            avg_retirement_duration = self.success_calculator.calculate_retirement_duration(simulation_result)

            # Calculate risk metrics
            risk_metrics = self.success_calculator.calculate_risk_metrics(simulation_result)

            # Create analysis result
            analysis = RetirementAnalysis(
                person=person,
                portfolio=portfolio,
                simulation_result=simulation_result,
                goal_statuses=goal_statuses,
                overall_success_rate=overall_success_rate,
                average_retirement_duration=avg_retirement_duration,
                risk_metrics=risk_metrics,
                recommendations=[]
            )

            # Generate recommendations
            recommendations = self.success_calculator.generate_recommendations(analysis)
            analysis = analysis.__class__(
                person=analysis.person,
                portfolio=analysis.portfolio,
                simulation_result=analysis.simulation_result,
                goal_statuses=analysis.goal_statuses,
                overall_success_rate=analysis.overall_success_rate,
                average_retirement_duration=analysis.average_retirement_duration,
                risk_metrics=analysis.risk_metrics,
                recommendations=recommendations,
                metadata=analysis.metadata
            )

            self.logger.log(LogLevel.SUCCESS, f"Retirement analysis complete. Overall success rate: {overall_success_rate:.1%}")

            return analysis

        except Exception as e:
            raise AnalysisError(f"Retirement analysis failed: {e}") from e