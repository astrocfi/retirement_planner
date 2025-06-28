import pytest
import numpy as np
from unittest.mock import Mock, patch

from retirement_planner.analysis.withdrawal import (
    WithdrawalStrategy,
    FixedWithdrawalStrategy,
    PercentageWithdrawalStrategy,
    InflationAdjustedWithdrawalStrategy,
    DynamicWithdrawalStrategy,
    WithdrawalOptimizer,
    WithdrawalPlan,
    WithdrawalOptimizationResult
)
from retirement_planner.models.portfolio import Portfolio, AssetAllocation, StaticRebalancingStrategy
from retirement_planner.assets.equities import Equity
from retirement_planner.simulation.engine import SimulationResult, SimulationScenario
from retirement_planner.core.exceptions import AnalysisError


@pytest.fixture
def assets():
    return {
        'StockA': Equity(
            name='StockA',
            current_value=60000,
            expected_return=0.08,
            volatility=0.15,
            dividend_yield=0.02,
            beta=1.0,
            market_cap='large',
            geography='domestic'
        ),
        'BondB': Equity(
            name='BondB',
            current_value=30000,
            expected_return=0.04,
            volatility=0.08,
            dividend_yield=0.03,
            beta=0.5,
            market_cap='medium',
            geography='domestic'
        ),
    }


@pytest.fixture
def portfolio(assets):
    allocation = AssetAllocation({'StockA': 0.6, 'BondB': 0.4})
    return Portfolio(
        assets=list(assets.values()),
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
            portfolio_values=[100000, 95000, 90000],
            returns=[-0.05, -0.053],
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
            contributions=[0],
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


class TestWithdrawalPlan:
    def test_withdrawal_plan_creation(self):
        plan = WithdrawalPlan(
            annual_withdrawals=[5000, 5000, 5000],
            total_withdrawn=15000,
            average_withdrawal=5000,
            withdrawal_rate=0.05
        )

        assert len(plan.annual_withdrawals) == 3
        assert plan.total_withdrawn == 15000
        assert plan.average_withdrawal == 5000
        assert plan.withdrawal_rate == 0.05
        assert plan.metadata == {}


class TestWithdrawalOptimizationResult:
    def test_withdrawal_optimization_result_creation(self):
        result = WithdrawalOptimizationResult(
            optimal_withdrawal_rate=0.04,
            optimal_annual_withdrawal=4000,
            success_rate=0.85,
            average_portfolio_value=100000,
            worst_case_portfolio_value=50000,
            risk_metrics={'volatility': 0.15},
            recommendations=["Test recommendation"]
        )

        assert result.optimal_withdrawal_rate == 0.04
        assert result.optimal_annual_withdrawal == 4000
        assert result.success_rate == 0.85
        assert result.average_portfolio_value == 100000
        assert result.worst_case_portfolio_value == 50000
        assert result.risk_metrics['volatility'] == 0.15
        assert len(result.recommendations) == 1


class TestWithdrawalStrategy:
    def test_withdrawal_strategy_abstract(self):
        with pytest.raises(TypeError):
            WithdrawalStrategy()


class TestFixedWithdrawalStrategy:
    def test_fixed_withdrawal_strategy_creation(self):
        strategy = FixedWithdrawalStrategy(annual_amount=5000)
        assert strategy.annual_amount == 5000

    def test_calculate_withdrawals(self, portfolio):
        strategy = FixedWithdrawalStrategy(annual_amount=5000)
        plan = strategy.calculate_withdrawals(portfolio, num_years=3)

        assert len(plan.annual_withdrawals) == 3
        assert all(w == 5000 for w in plan.annual_withdrawals)
        assert plan.total_withdrawn == 15000
        assert plan.average_withdrawal == 5000
        assert plan.withdrawal_rate == 5000 / portfolio.total_value


class TestPercentageWithdrawalStrategy:
    def test_percentage_withdrawal_strategy_creation(self):
        strategy = PercentageWithdrawalStrategy(withdrawal_rate=0.04)
        assert strategy.withdrawal_rate == 0.04

    def test_calculate_withdrawals(self, portfolio):
        strategy = PercentageWithdrawalStrategy(withdrawal_rate=0.04)
        plan = strategy.calculate_withdrawals(portfolio, num_years=3)

        expected_withdrawal = portfolio.total_value * 0.04
        assert len(plan.annual_withdrawals) == 3
        assert all(w == expected_withdrawal for w in plan.annual_withdrawals)
        assert plan.total_withdrawn == expected_withdrawal * 3
        assert plan.average_withdrawal == expected_withdrawal
        assert plan.withdrawal_rate == 0.04


class TestInflationAdjustedWithdrawalStrategy:
    def test_inflation_adjusted_withdrawal_strategy_creation(self):
        strategy = InflationAdjustedWithdrawalStrategy(initial_withdrawal_rate=0.04, inflation_rate=0.02)
        assert strategy.initial_withdrawal_rate == 0.04
        assert strategy.inflation_rate == 0.02

    def test_calculate_withdrawals(self, portfolio):
        strategy = InflationAdjustedWithdrawalStrategy(initial_withdrawal_rate=0.04, inflation_rate=0.02)
        plan = strategy.calculate_withdrawals(portfolio, num_years=3)

        initial_withdrawal = portfolio.total_value * 0.04
        expected_withdrawals = [
            initial_withdrawal,
            initial_withdrawal * 1.02,
            initial_withdrawal * (1.02 ** 2)
        ]

        assert len(plan.annual_withdrawals) == 3
        for i, withdrawal in enumerate(plan.annual_withdrawals):
            assert abs(withdrawal - expected_withdrawals[i]) < 0.01

        assert plan.withdrawal_rate == 0.04

    def test_calculate_withdrawals_zero_inflation(self, portfolio):
        strategy = InflationAdjustedWithdrawalStrategy(initial_withdrawal_rate=0.04, inflation_rate=0.0)
        plan = strategy.calculate_withdrawals(portfolio, num_years=3)

        expected_withdrawal = portfolio.total_value * 0.04
        assert all(abs(w - expected_withdrawal) < 0.01 for w in plan.annual_withdrawals)


class TestDynamicWithdrawalStrategy:
    def test_dynamic_withdrawal_strategy_creation(self):
        strategy = DynamicWithdrawalStrategy(
            base_withdrawal_rate=0.04,
            floor_rate=0.02,
            ceiling_rate=0.06,
            adjustment_factor=0.1
        )
        assert strategy.base_withdrawal_rate == 0.04
        assert strategy.floor_rate == 0.02
        assert strategy.ceiling_rate == 0.06
        assert strategy.adjustment_factor == 0.1

    def test_calculate_withdrawals(self, portfolio):
        strategy = DynamicWithdrawalStrategy(base_withdrawal_rate=0.04)
        plan = strategy.calculate_withdrawals(portfolio, num_years=3)

        expected_withdrawal = portfolio.total_value * 0.04
        assert len(plan.annual_withdrawals) == 3
        assert all(w == expected_withdrawal for w in plan.annual_withdrawals)
        assert plan.withdrawal_rate == 0.04


class TestWithdrawalOptimizer:
    def test_withdrawal_optimizer_creation(self):
        optimizer = WithdrawalOptimizer()
        assert optimizer is not None
        assert optimizer.strategy_factory is not None
        assert optimizer.logger is not None

    def test_withdrawal_optimizer_custom_factory(self):
        factory = Mock()
        logger = Mock()
        optimizer = WithdrawalOptimizer(strategy_factory=factory, logger=logger)
        assert optimizer.strategy_factory == factory
        assert optimizer.logger == logger

    def test_default_strategy_factory_percentage(self):
        optimizer = WithdrawalOptimizer()
        strategy = optimizer._default_strategy_factory("percentage", 0.04)
        assert isinstance(strategy, PercentageWithdrawalStrategy)
        assert strategy.withdrawal_rate == 0.04

    def test_default_strategy_factory_fixed(self):
        optimizer = WithdrawalOptimizer()
        strategy = optimizer._default_strategy_factory("fixed", 5000)
        assert isinstance(strategy, FixedWithdrawalStrategy)
        assert strategy.annual_amount == 5000

    def test_default_strategy_factory_inflation_adjusted(self):
        optimizer = WithdrawalOptimizer()
        strategy = optimizer._default_strategy_factory("inflation_adjusted", 0.04)
        assert isinstance(strategy, InflationAdjustedWithdrawalStrategy)
        assert strategy.initial_withdrawal_rate == 0.04

    def test_default_strategy_factory_dynamic(self):
        optimizer = WithdrawalOptimizer()
        strategy = optimizer._default_strategy_factory("dynamic", 0.04)
        assert isinstance(strategy, DynamicWithdrawalStrategy)
        assert strategy.base_withdrawal_rate == 0.04

    def test_default_strategy_factory_unknown(self):
        optimizer = WithdrawalOptimizer()
        with pytest.raises(AnalysisError):
            optimizer._default_strategy_factory("unknown", 0.04)

    def test_calculate_optimization_metrics(self, simulation_result):
        optimizer = WithdrawalOptimizer()

        plan = WithdrawalPlan(
            annual_withdrawals=[5000, 5000],
            total_withdrawn=10000,
            average_withdrawal=5000,
            withdrawal_rate=0.05
        )

        metrics = optimizer._calculate_optimization_metrics(plan, simulation_result)

        assert 'average_portfolio_value' in metrics
        assert 'worst_case_portfolio_value' in metrics
        assert 'best_case_portfolio_value' in metrics
        assert 'volatility' in metrics
        assert 'total_withdrawn' in metrics
        assert 'average_withdrawal' in metrics

        assert metrics['total_withdrawn'] == 10000
        assert metrics['average_withdrawal'] == 5000

    def test_generate_optimization_recommendations_low_success(self):
        optimizer = WithdrawalOptimizer()

        recommendations = optimizer._generate_optimization_recommendations(
            optimal_rate=0.06,
            success_rate=0.5,
            metrics={'volatility': 0.35}
        )

        assert len(recommendations) > 0
        assert any("reducing withdrawal rate" in rec.lower() for rec in recommendations)

    def test_generate_optimization_recommendations_high_rate(self):
        optimizer = WithdrawalOptimizer()

        recommendations = optimizer._generate_optimization_recommendations(
            optimal_rate=0.07,
            success_rate=0.9,
            metrics={'volatility': 0.15}
        )

        assert len(recommendations) > 0
        assert any("high withdrawal rate" in rec.lower() for rec in recommendations)

    def test_generate_optimization_recommendations_low_rate(self):
        optimizer = WithdrawalOptimizer()

        recommendations = optimizer._generate_optimization_recommendations(
            optimal_rate=0.02,
            success_rate=0.95,
            metrics={'volatility': 0.1}
        )

        assert len(recommendations) > 0
        assert any("conservative" in rec.lower() for rec in recommendations)

    def test_optimize_withdrawal_rate(self, portfolio, simulation_result):
        optimizer = WithdrawalOptimizer()

        result = optimizer.optimize_withdrawal_rate(
            portfolio=portfolio,
            simulation_result=simulation_result,
            strategy_type="percentage",
            min_rate=0.02,
            max_rate=0.06
        )

        assert isinstance(result, WithdrawalOptimizationResult)
        assert 0.02 <= result.optimal_withdrawal_rate <= 0.06
        assert result.optimal_annual_withdrawal > 0
        assert 0.0 <= result.success_rate <= 1.0
        assert result.average_portfolio_value > 0
        assert result.worst_case_portfolio_value >= 0
        assert len(result.risk_metrics) > 0
        assert len(result.recommendations) > 0

    def test_optimize_withdrawal_rate_error_handling(self, portfolio):
        optimizer = WithdrawalOptimizer()

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
            optimizer.optimize_withdrawal_rate(
                portfolio=portfolio,
                simulation_result=invalid_result,
                strategy_type="percentage"
            )