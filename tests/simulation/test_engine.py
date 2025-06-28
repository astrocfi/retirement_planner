import pytest
import numpy as np
from unittest.mock import Mock, patch

from retirement_planner.simulation.engine import (
    MonteCarloEngine,
    SimulationScenario,
    SimulationResult,
    ScenarioGenerator,
    RandomScenarioGenerator,
    MarketSimulator
)
from retirement_planner.models.portfolio import Portfolio, AssetAllocation, StaticRebalancingStrategy
from retirement_planner.assets.equities import Equity
from retirement_planner.core.exceptions import SimulationError


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
        'CashC': Equity(
            name='CashC',
            current_value=10000,
            expected_return=0.02,
            volatility=0.01,
            dividend_yield=0.01,
            beta=0.1,
            market_cap='small',
            geography='domestic'
        ),
    }


@pytest.fixture
def portfolio(assets):
    allocation = AssetAllocation({'StockA': 0.6, 'BondB': 0.3, 'CashC': 0.1})
    asset_values = {'StockA': 60000, 'BondB': 30000, 'CashC': 10000}
    return Portfolio(
        assets=assets,
        allocation=allocation,
        asset_values=asset_values,
        rebalancing_strategy=StaticRebalancingStrategy()
    )


class TestSimulationScenario:
    def test_simulation_scenario_creation(self):
        scenario = SimulationScenario(
            scenario_id=1,
            years=[0, 1, 2],
            portfolio_values=[100000, 105000, 110000],
            returns=[0.05, 0.048],
            withdrawals=[5000, 5000],
            contributions=[10000, 10000],
            allocation_percentages=[{'StockA': 0.6}, {'StockA': 0.6}, {'StockA': 0.6}],
            success=True
        )
        assert scenario.scenario_id == 1
        assert len(scenario.years) == 3
        assert len(scenario.portfolio_values) == 3
        assert scenario.success is True
        assert scenario.failure_year is None

    def test_simulation_scenario_failure(self):
        scenario = SimulationScenario(
            scenario_id=2,
            years=[0, 1, 2],
            portfolio_values=[100000, 50000, 0],
            returns=[-0.5, -1.0],
            withdrawals=[5000, 5000],
            contributions=[0, 0],
            allocation_percentages=[{'StockA': 0.6}, {'StockA': 0.6}, {'StockA': 0.6}],
            success=False,
            failure_year=2
        )
        assert scenario.success is False
        assert scenario.failure_year == 2


class TestSimulationResult:
    def test_simulation_result_creation(self):
        scenarios = [
            SimulationScenario(
                scenario_id=1,
                years=[0, 1],
                portfolio_values=[100000, 105000],
                returns=[0.05],
                withdrawals=[5000],
                contributions=[10000],
                allocation_percentages=[{'StockA': 0.6}, {'StockA': 0.6}],
                success=True
            ),
            SimulationScenario(
                scenario_id=2,
                years=[0, 1],
                portfolio_values=[100000, 95000],
                returns=[-0.05],
                withdrawals=[5000],
                contributions=[10000],
                allocation_percentages=[{'StockA': 0.6}, {'StockA': 0.6}],
                success=True
            )
        ]

        result = SimulationResult(
            scenarios=scenarios,
            success_rate=1.0,
            average_portfolio_value=100000,
            median_portfolio_value=100000,
            worst_case_portfolio_value=95000,
            best_case_portfolio_value=105000
        )

        assert result.success_rate == 1.0
        assert result.average_portfolio_value == 100000
        assert len(result.scenarios) == 2


class TestScenarioGenerator:
    def test_scenario_generator_abstract(self):
        with pytest.raises(TypeError):
            ScenarioGenerator()

    def test_random_scenario_generator_creation(self):
        generator = RandomScenarioGenerator(seed=42)
        assert generator is not None

    def test_random_scenario_generator_generate(self):
        generator = RandomScenarioGenerator(seed=42)
        scenarios = generator.generate_scenarios(num_scenarios=5, time_horizon=10)

        assert len(scenarios) == 5
        for i, scenario in enumerate(scenarios):
            assert scenario['scenario_id'] == i
            assert scenario['time_horizon'] == 10
            assert len(scenario['years']) == 10


class TestMarketSimulator:
    def test_market_simulator_creation(self):
        simulator = MarketSimulator()
        assert simulator is not None

    def test_simulate_returns(self, assets):
        simulator = MarketSimulator()
        returns = simulator.simulate_returns(assets, num_years=5)

        assert len(returns) == 3
        assert 'StockA' in returns
        assert 'BondB' in returns
        assert 'CashC' in returns

        for asset_name, asset_returns in returns.items():
            assert len(asset_returns) == 5
            # Check returns are reasonable (not below -100%)
            assert all(r >= -0.99 for r in asset_returns)

    def test_simulate_portfolio_evolution(self, portfolio):
        simulator = MarketSimulator()

        # Create simple returns
        returns = {
            'StockA': [0.05, 0.05],
            'BondB': [0.03, 0.03],
            'CashC': [0.02, 0.02]
        }

        withdrawals = [5000, 5000]
        contributions = [10000, 10000]

        scenario = simulator.simulate_portfolio_evolution(
            portfolio, returns, withdrawals, contributions
        )

        assert scenario.scenario_id == 0
        assert len(scenario.years) == 3  # 0, 1, 2
        assert len(scenario.portfolio_values) == 3
        assert len(scenario.returns) == 2
        assert len(scenario.withdrawals) == 2
        assert len(scenario.contributions) == 2
        assert len(scenario.allocation_percentages) == 3
        assert scenario.success is True

    def test_simulate_portfolio_evolution_empty_returns(self, portfolio):
        simulator = MarketSimulator()

        with pytest.raises(SimulationError):
            simulator.simulate_portfolio_evolution(
                portfolio, {}, [5000], [10000]
            )

    def test_simulate_portfolio_evolution_mismatched_lengths(self, portfolio):
        simulator = MarketSimulator()

        returns = {'StockA': [0.05, 0.05]}

        with pytest.raises(SimulationError):
            simulator.simulate_portfolio_evolution(
                portfolio, returns, [5000], [10000, 10000]  # Mismatched lengths
            )

    def test_calculate_portfolio_return(self, portfolio):
        simulator = MarketSimulator()

        year_returns = {'StockA': 0.05, 'BondB': 0.03, 'CashC': 0.02}
        portfolio_return = simulator._calculate_portfolio_return(portfolio, year_returns)

        # Should be weighted average of returns
        expected_return = (0.6 * 0.05 + 0.3 * 0.03 + 0.1 * 0.02)
        assert abs(portfolio_return - expected_return) < 0.001

    def test_apply_cash_flow(self, portfolio):
        simulator = MarketSimulator()

        # Apply positive cash flow
        new_portfolio = simulator._apply_cash_flow(portfolio, 10000)
        assert new_portfolio.total_value == portfolio.total_value + 10000

        # Apply negative cash flow
        new_portfolio = simulator._apply_cash_flow(portfolio, -5000)
        assert new_portfolio.total_value == portfolio.total_value - 5000

        # Apply zero cash flow
        new_portfolio = simulator._apply_cash_flow(portfolio, 0)
        assert new_portfolio.total_value == portfolio.total_value


class TestMonteCarloEngine:
    def test_monte_carlo_engine_creation(self):
        engine = MonteCarloEngine()
        assert engine is not None
        assert engine.scenario_generator is not None
        assert engine.market_simulator is not None
        assert engine.logger is not None

    def test_monte_carlo_engine_custom_components(self):
        generator = RandomScenarioGenerator()
        simulator = MarketSimulator()
        logger = Mock()

        engine = MonteCarloEngine(
            scenario_generator=generator,
            market_simulator=simulator,
            logger=logger
        )

        assert engine.scenario_generator == generator
        assert engine.market_simulator == simulator
        assert engine.logger == logger

    @patch('numpy.random.seed')
    def test_run_simulation(self, mock_seed, portfolio):
        engine = MonteCarloEngine()

        withdrawals = [5000] * 10
        contributions = [10000] * 10

        result = engine.run_simulation(
            portfolio=portfolio,
            num_scenarios=2,
            time_horizon=10,
            withdrawals=withdrawals,
            contributions=contributions,
            seed=42
        )

        assert isinstance(result, SimulationResult)
        assert len(result.scenarios) == 2
        assert 0.0 <= result.success_rate <= 1.0
        assert result.average_portfolio_value > 0
        assert result.median_portfolio_value > 0
        assert result.worst_case_portfolio_value > 0
        assert result.best_case_portfolio_value > 0

    def test_run_simulation_small_scale(self, portfolio):
        engine = MonteCarloEngine()

        withdrawals = [5000] * 5
        contributions = [10000] * 5

        result = engine.run_simulation(
            portfolio=portfolio,
            num_scenarios=1,
            time_horizon=5,
            withdrawals=withdrawals,
            contributions=contributions
        )

        assert len(result.scenarios) == 1
        assert result.scenarios[0].scenario_id == 0

    def test_calculate_results_empty_scenarios(self):
        engine = MonteCarloEngine()

        with pytest.raises(SimulationError):
            engine._calculate_results([])

    def test_calculate_results_with_failures(self):
        engine = MonteCarloEngine()

        scenarios = [
            SimulationScenario(
                scenario_id=1,
                years=[0, 1],
                portfolio_values=[100000, 105000],
                returns=[0.05],
                withdrawals=[5000],
                contributions=[10000],
                allocation_percentages=[{'StockA': 0.6}, {'StockA': 0.6}],
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

        result = engine._calculate_results(scenarios)

        assert result.success_rate == 0.5
        assert result.average_years_to_failure == 1.0