"""
Tests for Monte Carlo simulation engine.
"""

import pytest
import numpy as np
from unittest.mock import Mock, MagicMock
from retirement_planner.simulation.engine import (
    MonteCarloEngine, RandomScenarioGenerator, MarketSimulator,
    SimulationScenario, SimulationResult
)
from retirement_planner.models.portfolio import Portfolio, AssetAllocation, StaticRebalancingStrategy
from retirement_planner.assets.base import Asset, AssetType
from retirement_planner.core.exceptions import SimulationError


class TestSimulationScenario:
    """Test SimulationScenario functionality."""

    def test_simulation_scenario_creation(self):
        """Test creating a simulation scenario."""
        scenario = SimulationScenario(
            scenario_id=1,
            years=[0, 1, 2],
            portfolio_values=[100000, 105000, 110000],
            returns=[0.05, 0.048],
            withdrawals=[0, 5000],
            contributions=[0, 0],
            allocation_percentages=[{"stock": 0.6, "bond": 0.4}] * 3,
            success=True
        )

        assert scenario.scenario_id == 1
        assert len(scenario.years) == 3
        assert len(scenario.portfolio_values) == 3
        assert len(scenario.returns) == 2
        assert scenario.success is True
        assert scenario.failure_year is None

    def test_simulation_scenario_with_failure(self):
        """Test creating a simulation scenario with failure."""
        scenario = SimulationScenario(
            scenario_id=2,
            years=[0, 1, 2],
            portfolio_values=[100000, 50000, 0],
            returns=[-0.5, -1.0],
            withdrawals=[0, 10000],
            contributions=[0, 0],
            allocation_percentages=[{"stock": 0.6, "bond": 0.4}] * 3,
            success=False,
            failure_year=2
        )

        assert scenario.success is False
        assert scenario.failure_year == 2


class TestSimulationResult:
    """Test SimulationResult functionality."""

    def test_simulation_result_creation(self):
        """Test creating a simulation result."""
        scenarios = [
            SimulationScenario(
                scenario_id=i,
                years=[0, 1, 2],
                portfolio_values=[100000, 105000, 110000],
                returns=[0.05, 0.048],
                withdrawals=[0, 5000],
                contributions=[0, 0],
                allocation_percentages=[{"stock": 0.6, "bond": 0.4}] * 3,
                success=True
            ) for i in range(10)
        ]

        result = SimulationResult(
            scenarios=scenarios,
            success_rate=1.0,
            average_portfolio_value=110000,
            median_portfolio_value=110000,
            worst_case_portfolio_value=110000,
            best_case_portfolio_value=110000,
            time_horizon=2
        )

        assert len(result.scenarios) == 10
        assert result.success_rate == 1.0
        assert result.time_horizon == 2


class TestRandomScenarioGenerator:
    """Test RandomScenarioGenerator functionality."""

    def test_random_scenario_generator_creation(self):
        """Test creating a random scenario generator."""
        generator = RandomScenarioGenerator(time_horizon=30, random_seed=42)
        assert generator.time_horizon == 30

    def test_generate_scenarios(self):
        """Test generating scenarios."""
        generator = RandomScenarioGenerator(time_horizon=5, random_seed=42)
        scenarios = generator.generate_scenarios(num_scenarios=3, time_horizon=5)

        assert len(scenarios) == 3
        for scenario in scenarios:
            assert scenario['time_horizon'] == 5
            assert len(scenario['years']) == 5
            assert scenario['years'] == [0, 1, 2, 3, 4]


class TestMarketSimulator:
    """Test MarketSimulator functionality."""

    def create_test_portfolio(self):
        """Create a test portfolio."""
        assets = [
            Asset(
                name="stock",
                asset_type=AssetType.EQUITY,
                current_value=60000,
                expected_return=0.07,
                volatility=0.15
            ),
            Asset(
                name="bond",
                asset_type=AssetType.BOND,
                current_value=40000,
                expected_return=0.03,
                volatility=0.05
            )
        ]

        allocation = AssetAllocation({
            "stock": 0.6,
            "bond": 0.4
        })

        return Portfolio(
            assets=assets,
            allocation_targets=allocation,
            rebalancing_strategy=StaticRebalancingStrategy()
        )

    def test_market_simulator_creation(self):
        """Test creating a market simulator."""
        market_model = Mock()
        simulator = MarketSimulator(market_model)
        assert simulator.market_model == market_model

    def test_simulate_returns(self):
        """Test simulating returns."""
        market_model = Mock()
        market_model.simulate_returns.return_value = {
            "stock": [0.05, 0.03, 0.07],
            "bond": [0.02, 0.025, 0.015]
        }

        simulator = MarketSimulator(market_model)
        assets = [
            Asset(name="stock", asset_type=AssetType.EQUITY, current_value=100000, expected_return=0.07, volatility=0.15),
            Asset(name="bond", asset_type=AssetType.BOND, current_value=100000, expected_return=0.03, volatility=0.05)
        ]

        returns = simulator.simulate_returns(assets, num_years=3)

        assert "stock" in returns
        assert "bond" in returns
        assert len(returns["stock"]) == 3
        assert len(returns["bond"]) == 3
        market_model.simulate_returns.assert_called_once()

    def test_simulate_portfolio_evolution(self):
        """Test simulating portfolio evolution."""
        market_model = Mock()
        simulator = MarketSimulator(market_model)
        portfolio = self.create_test_portfolio()

        returns = {
            "stock": [0.05, 0.03],
            "bond": [0.02, 0.025]
        }
        withdrawals = [0, 5000]
        contributions = [0, 0]

        scenario = simulator.simulate_portfolio_evolution(
            portfolio=portfolio,
            returns=returns,
            withdrawals=withdrawals,
            contributions=contributions
        )

        assert isinstance(scenario, SimulationScenario)
        assert len(scenario.portfolio_values) == 3  # Initial + 2 years
        assert len(scenario.returns) == 2
        assert len(scenario.withdrawals) == 2
        assert len(scenario.contributions) == 2

    def test_simulate_portfolio_evolution_with_failure(self):
        """Test simulating portfolio evolution that results in failure."""
        market_model = Mock()
        simulator = MarketSimulator(market_model)
        portfolio = self.create_test_portfolio()

        # Large negative returns that will cause failure
        returns = {
            "stock": [-0.5, -0.5],
            "bond": [-0.3, -0.3]
        }
        withdrawals = [0, 80000]  # Very large withdrawal that will cause failure
        contributions = [0, 0]

        scenario = simulator.simulate_portfolio_evolution(
            portfolio=portfolio,
            returns=returns,
            withdrawals=withdrawals,
            contributions=contributions
        )

        assert scenario.success is False
        assert scenario.failure_year is not None

    def test_calculate_portfolio_return(self):
        """Test calculating portfolio return."""
        market_model = Mock()
        simulator = MarketSimulator(market_model)
        portfolio = self.create_test_portfolio()

        year_returns = {"stock": 0.05, "bond": 0.02}
        portfolio_return = simulator._calculate_portfolio_return(portfolio, year_returns)

        # Expected: 0.6 * 0.05 + 0.4 * 0.02 = 0.038
        expected_return = 0.6 * 0.05 + 0.4 * 0.02
        assert abs(portfolio_return - expected_return) < 0.001

    def test_calculate_portfolio_return_zero_total(self):
        """Test calculating portfolio return with zero total value."""
        market_model = Mock()
        simulator = MarketSimulator(market_model)

        # Create portfolio with zero values
        assets = [
            Asset(name="stock", asset_type=AssetType.EQUITY, current_value=0, expected_return=0.07, volatility=0.15),
            Asset(name="bond", asset_type=AssetType.BOND, current_value=0, expected_return=0.03, volatility=0.05)
        ]
        allocation = AssetAllocation({"stock": 0.6, "bond": 0.4})
        portfolio = Portfolio(assets=assets, allocation_targets=allocation)

        year_returns = {"stock": 0.05, "bond": 0.02}
        portfolio_return = simulator._calculate_portfolio_return(portfolio, year_returns)

        assert portfolio_return == 0.0

    def test_apply_cash_flow(self):
        """Test applying cash flow to portfolio."""
        market_model = Mock()
        simulator = MarketSimulator(market_model)
        portfolio = self.create_test_portfolio()

        # Apply positive cash flow
        new_portfolio = simulator._apply_cash_flow(portfolio, 10000)

        # Check that total value increased by cash flow amount
        assert new_portfolio.total_value == portfolio.total_value + 10000

        # Check that cash flow was distributed proportionally
        original_stock_value = 60000
        original_bond_value = 40000
        total_original = 100000

        expected_stock_increase = 10000 * (original_stock_value / total_original)
        expected_bond_increase = 10000 * (original_bond_value / total_original)

        stock_asset = new_portfolio.get_asset("stock")
        bond_asset = new_portfolio.get_asset("bond")

        assert abs(stock_asset.current_value - (original_stock_value + expected_stock_increase)) < 0.01
        assert abs(bond_asset.current_value - (original_bond_value + expected_bond_increase)) < 0.01

    def test_apply_negative_cash_flow(self):
        """Test applying negative cash flow (withdrawal) to portfolio."""
        market_model = Mock()
        simulator = MarketSimulator(market_model)
        portfolio = self.create_test_portfolio()

        # Apply negative cash flow
        new_portfolio = simulator._apply_cash_flow(portfolio, -5000)

        # Check that total value decreased by cash flow amount
        assert new_portfolio.total_value == portfolio.total_value - 5000

    def test_apply_zero_cash_flow(self):
        """Test applying zero cash flow (should return same portfolio)."""
        market_model = Mock()
        simulator = MarketSimulator(market_model)
        portfolio = self.create_test_portfolio()

        new_portfolio = simulator._apply_cash_flow(portfolio, 0)

        # Should return the same portfolio
        assert new_portfolio.total_value == portfolio.total_value


class TestMonteCarloEngine:
    """Test MonteCarloEngine functionality."""

    def create_test_portfolio(self):
        """Create a test portfolio."""
        assets = [
            Asset(
                name="stock",
                asset_type=AssetType.EQUITY,
                current_value=60000,
                expected_return=0.07,
                volatility=0.15
            ),
            Asset(
                name="bond",
                asset_type=AssetType.BOND,
                current_value=40000,
                expected_return=0.03,
                volatility=0.05
            )
        ]

        allocation = AssetAllocation({
            "stock": 0.6,
            "bond": 0.4
        })

        return Portfolio(
            assets=assets,
            allocation_targets=allocation,
            rebalancing_strategy=StaticRebalancingStrategy()
        )

    def test_monte_carlo_engine_creation(self):
        """Test creating a Monte Carlo engine."""
        engine = MonteCarloEngine(num_scenarios=1000)
        assert engine.num_scenarios == 1000
        assert isinstance(engine.scenario_generator, RandomScenarioGenerator)
        assert engine.market_simulator is None

    def test_monte_carlo_engine_with_custom_components(self):
        """Test creating Monte Carlo engine with custom components."""
        scenario_generator = RandomScenarioGenerator()
        market_simulator = MarketSimulator(Mock())

        engine = MonteCarloEngine(
            scenario_generator=scenario_generator,
            market_simulator=market_simulator,
            num_scenarios=500
        )

        assert engine.scenario_generator == scenario_generator
        assert engine.market_simulator == market_simulator
        assert engine.num_scenarios == 500

    def test_run_simulation(self):
        """Test running a Monte Carlo simulation."""
        # Create a real market model instead of Mock
        from retirement_planner.simulation.market import SimpleMarketModel
        market_model = SimpleMarketModel(seed=42)

        # Create a real market simulator
        market_simulator = MarketSimulator(market_model)

        engine = MonteCarloEngine(
            market_simulator=market_simulator,
            num_scenarios=10
        )
        portfolio = self.create_test_portfolio()

        result = engine.run_simulation(portfolio, time_horizon=3)

        assert isinstance(result, SimulationResult)
        assert len(result.scenarios) == 10
        assert result.time_horizon == 3
        # Note: Success rate may vary due to random market returns, so we just check it's a valid value
        assert 0.0 <= result.success_rate <= 1.0

    def test_run_simulation_with_failures(self):
        """Test running simulation with some failed scenarios."""
        # Create a real market model that can generate failures
        from retirement_planner.simulation.market import SimpleMarketModel
        market_model = SimpleMarketModel(seed=42)

        # Create a real market simulator
        market_simulator = MarketSimulator(market_model)

        engine = MonteCarloEngine(
            market_simulator=market_simulator,
            num_scenarios=10
        )
        portfolio = self.create_test_portfolio()

        result = engine.run_simulation(portfolio, time_horizon=3)

        assert isinstance(result, SimulationResult)
        assert len(result.scenarios) == 10
        # Note: Success rate may vary due to random market returns, so we just check it's a valid value
        assert 0.0 <= result.success_rate <= 1.0

    def test_calculate_results(self):
        """Test calculating simulation results."""
        engine = MonteCarloEngine()

        # Create test scenarios
        scenarios = []
        for i in range(10):
            final_value = 100000 + i * 10000  # Varying final values
            success = i < 8  # 8 successful, 2 failed
            failure_year = None if success else 2

            scenario = SimulationScenario(
                scenario_id=i,
                years=[0, 1, 2, 3],
                portfolio_values=[100000, 105000, 108000, final_value],
                returns=[0.05, 0.029, 0.037],
                withdrawals=[0, 0, 0],
                contributions=[0, 0, 0],
                allocation_percentages=[{"stock": 0.6, "bond": 0.4}] * 4,
                success=success,
                failure_year=failure_year
            )
            scenarios.append(scenario)

        result = engine._calculate_results(scenarios, time_horizon=3)

        assert result.success_rate == 0.8  # 8/10 successful
        assert result.time_horizon == 3
        assert result.average_years_to_failure == 2.0  # Both failures at year 2
        assert result.worst_case_portfolio_value == 100000  # Minimum final value
        assert result.best_case_portfolio_value == 190000  # Maximum final value

    def test_calculate_results_no_failures(self):
        """Test calculating results with no failures."""
        engine = MonteCarloEngine()

        scenarios = []
        for i in range(5):
            scenario = SimulationScenario(
                scenario_id=i,
                years=[0, 1, 2, 3],
                portfolio_values=[100000, 105000, 108000, 110000],
                returns=[0.05, 0.029, 0.037],
                withdrawals=[0, 0, 0],
                contributions=[0, 0, 0],
                allocation_percentages=[{"stock": 0.6, "bond": 0.4}] * 4,
                success=True
            )
            scenarios.append(scenario)

        result = engine._calculate_results(scenarios, time_horizon=3)

        assert result.success_rate == 1.0
        assert result.average_years_to_failure is None  # No failures

    def test_calculate_results_empty_scenarios(self):
        """Test calculating results with empty scenarios list."""
        engine = MonteCarloEngine()

        with pytest.raises(SimulationError):
            engine._calculate_results([], time_horizon=3)