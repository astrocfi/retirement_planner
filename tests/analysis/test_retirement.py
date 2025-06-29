import pytest
import numpy as np
from unittest.mock import Mock, patch

from retirement_planner.analysis.retirement import (
    RetirementAnalyzer,
    GoalTracker,
    SuccessCalculator,
    GoalStatus,
    RetirementAnalysis
)
from retirement_planner.models.person import Person, Goal
from retirement_planner.models.portfolio import Portfolio, AssetAllocation, StaticRebalancingStrategy
from retirement_planner.assets.base import Asset, AssetType
from retirement_planner.simulation.engine import SimulationResult, SimulationScenario
from retirement_planner.core.exceptions import AnalysisError


@pytest.fixture
def person():
    goals = [
        Goal(name="Retirement Income", goal_type="income", priority="essential", target_amount=50000, target_age=65),
        Goal(name="Portfolio Value", goal_type="legacy", priority="important", target_amount=1000000, target_age=90),
        Goal(name="Withdrawal Rate", goal_type="lifestyle", priority="nice_to_have", target_amount=4.0, target_age=65)
    ]
    return Person(
        name="John Doe",
        age=50,
        retirement_age=65,
        life_expectancy=85,
        risk_tolerance="moderate",
        goals=goals
    )


@pytest.fixture
def assets():
    return {
        'StockA': Asset(
            name='StockA',
            asset_type=AssetType.EQUITY,
            current_value=60000,
            expected_return=0.08,
            volatility=0.15,
            dividend_rate=0.02,
            metadata={
                'beta': 1.0,
                'market_cap': 'large',
                'geography': 'domestic'
            }
        ),
        'BondB': Asset(
            name='BondB',
            asset_type=AssetType.BOND,
            current_value=30000,
            expected_return=0.04,
            volatility=0.08,
            dividend_rate=0.03,
            metadata={
                'beta': 0.5,
                'market_cap': 'medium',
                'geography': 'domestic'
            }
        ),
    }


@pytest.fixture
def portfolio(assets):
    allocation = AssetAllocation({'StockA': 0.6, 'BondB': 0.4})
    return Portfolio(
        assets=assets,
        allocation_targets=allocation,
        rebalancing_strategy=StaticRebalancingStrategy()
    )


@pytest.fixture
def simulation_result():
    scenarios = [
        SimulationScenario(
            scenario_id=0,
            years=[0, 1, 2],
            portfolio_values=[100000, 105000, 110000],
            returns=[0.05, 0.048],
            withdrawals=[5000, 5000],
            contributions=[10000, 10000],
            allocation_percentages=[{'StockA': 0.6}, {'StockA': 0.6}, {'StockA': 0.6}],
            success=True
        ),
        SimulationScenario(
            scenario_id=1,
            years=[0, 1, 2],
            portfolio_values=[100000, 105000, 110000],
            returns=[0.05, 0.048],
            withdrawals=[5000, 5000],
            contributions=[10000, 10000],
            allocation_percentages=[{'StockA': 0.6}, {'StockA': 0.6}, {'StockA': 0.6}],
            success=True
        ),
        SimulationScenario(
            scenario_id=2,
            years=[0, 1],
            portfolio_values=[100000, 0],
            returns=[-1.0],
            withdrawals=[5000],
            contributions=[10000],
            allocation_percentages=[{'StockA': 0.6}, {'StockA': 0.6}],
            success=False,
            failure_year=1
        )
    ]

    return SimulationResult(
        scenarios=scenarios,
        success_rate=2/3,
        average_portfolio_value=100000,
        median_portfolio_value=100000,
        worst_case_portfolio_value=0,
        best_case_portfolio_value=110000,
        time_horizon=2,
        average_years_to_failure=1.0
    )


class TestGoalStatus:
    def test_goal_status_creation(self):
        status = GoalStatus(
            goal_name="Test Goal",
            achieved=True,
            success_rate=0.85,
            average_shortfall=1000,
            worst_case_shortfall=5000,
            years_to_achievement=5.0
        )

        assert status.goal_name == "Test Goal"
        assert status.achieved is True
        assert status.success_rate == 0.85
        assert status.average_shortfall == 1000
        assert status.worst_case_shortfall == 5000
        assert status.years_to_achievement == 5.0

    def test_goal_status_optional_fields(self):
        status = GoalStatus(
            goal_name="Test Goal",
            achieved=False,
            success_rate=0.3,
            average_shortfall=5000,
            worst_case_shortfall=10000
        )

        assert status.years_to_achievement is None
        assert status.metadata == {}


class TestRetirementAnalysis:
    def test_retirement_analysis_creation(self, person, portfolio, simulation_result):
        goal_statuses = [
            GoalStatus(
                goal_name="Test Goal",
                achieved=True,
                success_rate=0.8,
                average_shortfall=0,
                worst_case_shortfall=0
            )
        ]

        analysis = RetirementAnalysis(
            person=person,
            portfolio=portfolio,
            simulation_result=simulation_result,
            goal_statuses=goal_statuses,
            overall_success_rate=0.8,
            average_retirement_duration=20.0,
            risk_metrics={'var_95': 50000},
            recommendations=["Test recommendation"]
        )

        assert analysis.person == person
        assert analysis.portfolio == portfolio
        assert analysis.simulation_result == simulation_result
        assert len(analysis.goal_statuses) == 1
        assert analysis.overall_success_rate == 0.8
        assert analysis.average_retirement_duration == 20.0
        assert analysis.risk_metrics['var_95'] == 50000
        assert len(analysis.recommendations) == 1


class TestGoalTracker:
    def test_goal_tracker_creation(self, person):
        tracker = GoalTracker(person)
        assert tracker.person == person

    def test_track_retirement_income_goal(self, person, simulation_result):
        tracker = GoalTracker(person)
        goal = Goal(name="Income Goal", goal_type="income", priority="essential", target_amount=5000, target_age=65)

        status = tracker._track_retirement_income_goal(goal, simulation_result)

        assert status.goal_name == "Income Goal"
        assert 0.0 <= status.success_rate <= 1.0
        assert status.average_shortfall >= 0
        assert status.worst_case_shortfall >= 0

    def test_track_portfolio_value_goal(self, person, simulation_result):
        tracker = GoalTracker(person)
        goal = Goal(name="Value Goal", goal_type="legacy", priority="important", target_amount=50000, target_age=90)

        status = tracker._track_portfolio_value_goal(goal, simulation_result)

        assert status.goal_name == "Value Goal"
        assert 0.0 <= status.success_rate <= 1.0
        assert status.average_shortfall >= 0
        assert status.worst_case_shortfall >= 0

    def test_track_withdrawal_rate_goal(self, person, simulation_result):
        tracker = GoalTracker(person)
        goal = Goal(name="Rate Goal", goal_type="lifestyle", priority="nice_to_have", target_amount=5.0, target_age=65)

        status = tracker._track_withdrawal_rate_goal(goal, simulation_result)

        assert status.goal_name == "Rate Goal"
        assert 0.0 <= status.success_rate <= 1.0
        assert status.average_shortfall >= 0
        assert status.worst_case_shortfall >= 0

    def test_track_generic_goal(self, person, simulation_result):
        tracker = GoalTracker(person)
        goal = Goal(name="Generic Goal", goal_type="purchase", priority="important", target_amount=100000, target_age=70)

        status = tracker._track_generic_goal(goal, simulation_result)

        assert status.goal_name == "Generic Goal"
        assert 0.0 <= status.success_rate <= 1.0

    def test_calculate_years_to_target_income(self, person):
        tracker = GoalTracker(person)

        # Scenario where target is achieved in year 1
        scenario = SimulationScenario(
            scenario_id=0,
            years=[0, 1, 2],
            portfolio_values=[100000, 105000, 110000],
            returns=[0.05, 0.048],
            withdrawals=[6000, 5000],  # Year 1 achieves 6000 target
            contributions=[10000, 10000],
            allocation_percentages=[{'StockA': 0.6}, {'StockA': 0.6}, {'StockA': 0.6}],
            success=True
        )

        years = tracker._calculate_years_to_target_income(scenario, 6000)
        assert years == 0.0  # Achieved in year 0 (first year)

        # Scenario where target is never achieved
        scenario2 = SimulationScenario(
            scenario_id=1,
            years=[0, 1, 2],
            portfolio_values=[100000, 105000, 110000],
            returns=[0.05, 0.048],
            withdrawals=[3000, 3000],  # Never achieves 6000 target
            contributions=[10000, 10000],
            allocation_percentages=[{'StockA': 0.6}, {'StockA': 0.6}, {'StockA': 0.6}],
            success=True
        )

        years = tracker._calculate_years_to_target_income(scenario2, 6000)
        assert years is None


class TestSuccessCalculator:
    def test_success_calculator_creation(self):
        calculator = SuccessCalculator()
        assert calculator is not None

    def test_calculate_overall_success_rate(self):
        calculator = SuccessCalculator()

        goal_statuses = [
            GoalStatus("Goal1", True, 0.8, 0, 0),
            GoalStatus("Goal2", False, 0.6, 1000, 2000),
            GoalStatus("Goal3", True, 0.9, 0, 0)
        ]

        overall_rate = calculator.calculate_overall_success_rate(goal_statuses)
        expected_rate = (0.8 + 0.6 + 0.9) / 3
        assert abs(overall_rate - expected_rate) < 0.001

    def test_calculate_overall_success_rate_empty(self):
        calculator = SuccessCalculator()
        rate = calculator.calculate_overall_success_rate([])
        assert rate == 0.0

    def test_calculate_retirement_duration(self, simulation_result):
        calculator = SuccessCalculator()
        duration = calculator.calculate_retirement_duration(simulation_result)

        # Expected: (2 + 2 + 1) / 3 = 1.67 years
        expected_duration = (2 + 2 + 1) / 3
        assert abs(duration - expected_duration) < 0.01

    def test_calculate_risk_metrics(self, simulation_result):
        calculator = SuccessCalculator()
        metrics = calculator.calculate_risk_metrics(simulation_result)

        assert 'var_95' in metrics
        assert 'cvar_95' in metrics
        assert 'avg_max_drawdown' in metrics
        assert 'volatility' in metrics
        assert 'worst_case_value' in metrics
        assert 'best_case_value' in metrics

        assert metrics['worst_case_value'] == 0
        assert metrics['best_case_value'] == 110000

    def test_generate_recommendations_low_success(self):
        calculator = SuccessCalculator()

        # Create analysis with low success rate
        analysis = RetirementAnalysis(
            person=Mock(),
            portfolio=Mock(),
            simulation_result=Mock(),
            goal_statuses=[],
            overall_success_rate=0.3,
            average_retirement_duration=20.0,
            risk_metrics={'avg_max_drawdown': 0.4, 'volatility': 0.25},
            recommendations=[]
        )

        recommendations = calculator.generate_recommendations(analysis)

        assert len(recommendations) > 0
        assert any("increasing savings" in rec.lower() for rec in recommendations)

    def test_generate_recommendations_high_success(self):
        calculator = SuccessCalculator()

        # Create analysis with high success rate
        analysis = RetirementAnalysis(
            person=Mock(),
            portfolio=Mock(),
            simulation_result=Mock(),
            goal_statuses=[],
            overall_success_rate=0.9,
            average_retirement_duration=20.0,
            risk_metrics={'avg_max_drawdown': 0.1, 'volatility': 0.1},
            recommendations=[]
        )

        recommendations = calculator.generate_recommendations(analysis)

        assert len(recommendations) > 0
        assert any("sustainable" in rec.lower() for rec in recommendations)


class TestRetirementAnalyzer:
    def test_retirement_analyzer_creation(self):
        analyzer = RetirementAnalyzer()
        assert analyzer is not None
        assert analyzer.success_calculator is not None
        assert analyzer.logger is not None

    def test_retirement_analyzer_custom_components(self, person):
        goal_tracker = GoalTracker(person)
        success_calculator = SuccessCalculator()
        logger = Mock()

        analyzer = RetirementAnalyzer(
            goal_tracker=goal_tracker,
            success_calculator=success_calculator,
            logger=logger
        )

        assert analyzer.goal_tracker == goal_tracker
        assert analyzer.success_calculator == success_calculator
        assert analyzer.logger == logger

    def test_analyze_retirement(self, person, portfolio, simulation_result):
        analyzer = RetirementAnalyzer()

        analysis = analyzer.analyze_retirement(person, portfolio, simulation_result)

        assert isinstance(analysis, RetirementAnalysis)
        assert analysis.person == person
        assert analysis.portfolio == portfolio
        assert analysis.simulation_result == simulation_result
        assert len(analysis.goal_statuses) == 3  # Three goals in person fixture
        assert 0.0 <= analysis.overall_success_rate <= 1.0
        assert analysis.average_retirement_duration > 0
        assert len(analysis.risk_metrics) > 0
        assert len(analysis.recommendations) > 0

    def test_analyze_retirement_error_handling(self, person, portfolio):
        analyzer = RetirementAnalyzer()

        # Create invalid simulation result
        invalid_result = SimulationResult(
            scenarios=[],
            success_rate=0.0,
            average_portfolio_value=0.0,
            median_portfolio_value=0.0,
            worst_case_portfolio_value=0.0,
            best_case_portfolio_value=0.0,
            time_horizon=10
        )

        with pytest.raises(AnalysisError):
            analyzer.analyze_retirement(person, portfolio, invalid_result)