import pytest
import numpy as np
from unittest.mock import Mock

from retirement_planner.simulation.market import (
    MarketModel,
    CorrelationModel,
    ReturnSimulator,
    SimpleMarketModel,
    CorrelatedMarketModel
)
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


class TestMarketModel:
    def test_market_model_abstract(self):
        with pytest.raises(TypeError):
            MarketModel()


class TestCorrelationModel:
    def test_correlation_model_creation(self):
        correlation_matrix = {
            'StockA': {'StockA': 1.0, 'BondB': 0.3, 'CashC': 0.1},
            'BondB': {'StockA': 0.3, 'BondB': 1.0, 'CashC': 0.2},
            'CashC': {'StockA': 0.1, 'BondB': 0.2, 'CashC': 1.0}
        }
        model = CorrelationModel(correlation_matrix)
        assert model.correlation_matrix == correlation_matrix

    def test_correlation_model_empty(self):
        model = CorrelationModel({})
        model.validate()  # Should not raise

    def test_correlation_model_validation_valid(self):
        correlation_matrix = {
            'StockA': {'StockA': 1.0, 'BondB': 0.3},
            'BondB': {'StockA': 0.3, 'BondB': 1.0}
        }
        model = CorrelationModel(correlation_matrix)
        model.validate()  # Should not raise

    def test_correlation_model_validation_missing_assets(self):
        correlation_matrix = {
            'StockA': {'StockA': 1.0, 'BondB': 0.3},
            'BondB': {'StockA': 0.3}  # Missing BondB
        }
        model = CorrelationModel(correlation_matrix)
        with pytest.raises(SimulationError):
            model.validate()

    def test_correlation_model_validation_invalid_diagonal(self):
        correlation_matrix = {
            'StockA': {'StockA': 0.5, 'BondB': 0.3},  # Should be 1.0
            'BondB': {'StockA': 0.3, 'BondB': 1.0}
        }
        model = CorrelationModel(correlation_matrix)
        with pytest.raises(SimulationError):
            model.validate()

    def test_correlation_model_validation_invalid_correlation(self):
        correlation_matrix = {
            'StockA': {'StockA': 1.0, 'BondB': 1.5},  # > 1.0
            'BondB': {'StockA': 1.5, 'BondB': 1.0}
        }
        model = CorrelationModel(correlation_matrix)
        with pytest.raises(SimulationError):
            model.validate()

    def test_get_correlation_same_asset(self):
        model = CorrelationModel({})
        assert model.get_correlation('StockA', 'StockA') == 1.0

    def test_get_correlation_existing(self):
        correlation_matrix = {
            'StockA': {'StockA': 1.0, 'BondB': 0.3},
            'BondB': {'StockA': 0.3, 'BondB': 1.0}
        }
        model = CorrelationModel(correlation_matrix)
        assert model.get_correlation('StockA', 'BondB') == 0.3
        assert model.get_correlation('BondB', 'StockA') == 0.3

    def test_get_correlation_missing(self):
        model = CorrelationModel({})
        assert model.get_correlation('StockA', 'BondB') == 0.0

    def test_get_cholesky_decomposition_empty(self):
        model = CorrelationModel({})
        cholesky = model.get_cholesky_decomposition([])
        assert cholesky.size == 0

    def test_get_cholesky_decomposition_single_asset(self):
        model = CorrelationModel({})
        cholesky = model.get_cholesky_decomposition(['StockA'])
        assert cholesky.shape == (1, 1)
        assert cholesky[0, 0] == 1.0

    def test_get_cholesky_decomposition_two_assets(self):
        correlation_matrix = {
            'StockA': {'StockA': 1.0, 'BondB': 0.3},
            'BondB': {'StockA': 0.3, 'BondB': 1.0}
        }
        model = CorrelationModel(correlation_matrix)
        cholesky = model.get_cholesky_decomposition(['StockA', 'BondB'])
        assert cholesky.shape == (2, 2)
        # Verify it's lower triangular
        assert cholesky[0, 1] == 0.0

    def test_get_cholesky_decomposition_not_positive_definite(self):
        # Create a correlation matrix that's not positive definite
        # This violates the triangle inequality: |corr(A,B) + corr(B,C)| <= 1 + corr(A,C)
        correlation_matrix = {
            'StockA': {'StockA': 1.0, 'BondB': 0.8, 'CashC': 0.8},
            'BondB': {'StockA': 0.8, 'BondB': 1.0, 'CashC': -0.8},
            'CashC': {'StockA': 0.8, 'BondB': -0.8, 'CashC': 1.0}
        }
        model = CorrelationModel(correlation_matrix)
        with pytest.raises(SimulationError):
            model.get_cholesky_decomposition(['StockA', 'BondB', 'CashC'])


class TestReturnSimulator:
    def test_return_simulator_creation(self):
        simulator = ReturnSimulator()
        assert simulator is not None

    def test_return_simulator_with_correlation_model(self):
        correlation_matrix = {
            'StockA': {'StockA': 1.0, 'BondB': 0.3},
            'BondB': {'StockA': 0.3, 'BondB': 1.0}
        }
        correlation_model = CorrelationModel(correlation_matrix)
        simulator = ReturnSimulator(correlation_model)
        assert simulator.correlation_model == correlation_model

    def test_simulate_uncorrelated_returns(self, assets):
        simulator = ReturnSimulator()
        returns = simulator.simulate_uncorrelated_returns(assets, num_years=5)

        assert len(returns) == 3
        assert 'StockA' in returns
        assert 'BondB' in returns
        assert 'CashC' in returns

        for asset_name, asset_returns in returns.items():
            assert len(asset_returns) == 5
            # Check returns are reasonable (not below -100%)
            assert all(r >= -0.99 for r in asset_returns)

    def test_simulate_correlated_returns_no_correlation_model(self, assets):
        simulator = ReturnSimulator()  # No correlation model
        returns = simulator.simulate_correlated_returns(assets, num_years=5)

        # Should fall back to uncorrelated returns
        assert len(returns) == 3
        for asset_name, asset_returns in returns.items():
            assert len(asset_returns) == 5

    def test_simulate_correlated_returns_with_correlation_model(self, assets):
        correlation_matrix = {
            'StockA': {'StockA': 1.0, 'BondB': 0.3, 'CashC': 0.1},
            'BondB': {'StockA': 0.3, 'BondB': 1.0, 'CashC': 0.2},
            'CashC': {'StockA': 0.1, 'BondB': 0.2, 'CashC': 1.0}
        }
        correlation_model = CorrelationModel(correlation_matrix)
        simulator = ReturnSimulator(correlation_model)

        returns = simulator.simulate_correlated_returns(assets, num_years=5)

        assert len(returns) == 3
        for asset_name, asset_returns in returns.items():
            assert len(asset_returns) == 5
            assert all(r >= -0.99 for r in asset_returns)

    def test_simulate_correlated_returns_empty_assets(self):
        correlation_matrix = {
            'StockA': {'StockA': 1.0, 'BondB': 0.3},
            'BondB': {'StockA': 0.3, 'BondB': 1.0}
        }
        correlation_model = CorrelationModel(correlation_matrix)
        simulator = ReturnSimulator(correlation_model)

        returns = simulator.simulate_correlated_returns({}, num_years=5)
        assert returns == {}

    def test_simulate_returns_uncorrelated(self, assets):
        simulator = ReturnSimulator()
        returns = simulator.simulate_returns(assets, num_years=5, use_correlation=False)

        assert len(returns) == 3
        for asset_name, asset_returns in returns.items():
            assert len(asset_returns) == 5

    def test_simulate_returns_correlated(self, assets):
        correlation_matrix = {
            'StockA': {'StockA': 1.0, 'BondB': 0.3, 'CashC': 0.1},
            'BondB': {'StockA': 0.3, 'BondB': 1.0, 'CashC': 0.2},
            'CashC': {'StockA': 0.1, 'BondB': 0.2, 'CashC': 1.0}
        }
        correlation_model = CorrelationModel(correlation_matrix)
        simulator = ReturnSimulator(correlation_model)

        returns = simulator.simulate_returns(assets, num_years=5, use_correlation=True)

        assert len(returns) == 3
        for asset_name, asset_returns in returns.items():
            assert len(asset_returns) == 5


class TestSimpleMarketModel:
    def test_simple_market_model_creation(self):
        model = SimpleMarketModel()
        assert model is not None

    def test_simple_market_model_with_seed(self):
        model = SimpleMarketModel(seed=42)
        assert model is not None

    def test_simple_market_model_simulate_returns(self, assets):
        model = SimpleMarketModel(seed=42)
        returns = model.simulate_returns(assets, num_years=5)

        assert len(returns) == 3
        for asset_name, asset_returns in returns.items():
            assert len(asset_returns) == 5


class TestCorrelatedMarketModel:
    def test_correlated_market_model_creation(self):
        correlation_matrix = {
            'StockA': {'StockA': 1.0, 'BondB': 0.3},
            'BondB': {'StockA': 0.3, 'BondB': 1.0}
        }
        correlation_model = CorrelationModel(correlation_matrix)
        model = CorrelatedMarketModel(correlation_model)
        assert model is not None

    def test_correlated_market_model_with_seed(self):
        correlation_matrix = {
            'StockA': {'StockA': 1.0, 'BondB': 0.3},
            'BondB': {'StockA': 0.3, 'BondB': 1.0}
        }
        correlation_model = CorrelationModel(correlation_matrix)
        model = CorrelatedMarketModel(correlation_model, seed=42)
        assert model is not None

    def test_correlated_market_model_simulate_returns(self, assets):
        correlation_matrix = {
            'StockA': {'StockA': 1.0, 'BondB': 0.3, 'CashC': 0.1},
            'BondB': {'StockA': 0.3, 'BondB': 1.0, 'CashC': 0.2},
            'CashC': {'StockA': 0.1, 'BondB': 0.2, 'CashC': 1.0}
        }
        correlation_model = CorrelationModel(correlation_matrix)
        model = CorrelatedMarketModel(correlation_model)

        returns = model.simulate_returns(assets, num_years=5)

        assert len(returns) == 3
        for asset_name, asset_returns in returns.items():
            assert len(asset_returns) == 5