"""
Unit tests for base asset classes.

Tests Asset, AssetFactory, and AssetAllocation classes.
"""

import pytest
import numpy as np
from datetime import date
from retirement_planner.assets.base import Asset, AssetFactory, AssetAllocation, AssetType, AssetMetrics
from retirement_planner.core.exceptions import ValidationError, AssetError


class TestAssetType:
    """Test AssetType enum functionality."""

    def test_asset_type_values(self):
        """Test that asset type values are correct."""
        assert AssetType.EQUITY.value == "equity"
        assert AssetType.BOND.value == "bond"
        assert AssetType.REAL_ESTATE.value == "real_estate"
        assert AssetType.COMMODITY.value == "commodity"
        assert AssetType.CUSTOM.value == "custom"
        assert AssetType.CASH.value == "cash"

    def test_asset_type_enumeration(self):
        """Test that all expected asset types exist."""
        expected_types = [
            "equity", "bond", "real_estate", "commodity",
            "custom", "cash"
        ]
        actual_types = [asset_type.value for asset_type in AssetType]
        assert actual_types == expected_types


class TestAssetMetrics:
    """Test AssetMetrics class functionality."""

    def test_asset_metrics_creation(self):
        """Test creating asset metrics."""
        metrics = AssetMetrics(
            expected_return=0.08,
            volatility=0.15,
            correlation={'asset2': 0.3},
            sharpe_ratio=0.4
        )
        assert metrics.expected_return == 0.08
        assert metrics.volatility == 0.15
        assert metrics.correlation['asset2'] == 0.3
        assert metrics.sharpe_ratio == 0.4

    def test_asset_metrics_defaults(self):
        """Test asset metrics with default values."""
        metrics = AssetMetrics(expected_return=0.08, volatility=0.15)
        assert metrics.correlation == {}
        assert metrics.sharpe_ratio is None
        assert metrics.max_drawdown is None
        assert metrics.var_95 is None


class TestAsset:
    """Test Asset class functionality."""

    def test_asset_creation_valid(self):
        """Test creating a valid asset."""
        asset = Asset(
            name="Test Stock",
            asset_type=AssetType.EQUITY,
            current_value=10000.0,
            expected_return=0.08,
            volatility=0.15
        )
        assert asset.name == "Test Stock"
        assert asset.asset_type == AssetType.EQUITY
        assert asset.current_value == 10000.0
        assert asset.expected_return == 0.08
        assert asset.volatility == 0.15
        assert asset.correlation == {}

    def test_asset_creation_with_correlation(self):
        """Test creating asset with correlation data."""
        correlation = {'bond': 0.2, 'cash': -0.1}
        asset = Asset(
            name="Test Asset",
            asset_type=AssetType.EQUITY,
            current_value=10000.0,
            expected_return=0.08,
            volatility=0.15,
            correlation=correlation
        )
        assert asset.correlation == correlation

    def test_asset_validation_invalid_name(self):
        """Test asset validation with empty name."""
        with pytest.raises(ValidationError, match="Asset validation failed"):
            Asset(
                name="",
                asset_type=AssetType.EQUITY,
                current_value=10000.0,
                expected_return=0.08,
                volatility=0.15
            )

    def test_asset_validation_negative_value(self):
        """Test asset validation with negative current value."""
        with pytest.raises(ValidationError, match="Asset validation failed"):
            Asset(
                name="Test Asset",
                asset_type=AssetType.EQUITY,
                current_value=-1000.0,
                expected_return=0.08,
                volatility=0.15
            )

    def test_asset_validation_invalid_return(self):
        """Test asset validation with invalid expected return."""
        with pytest.raises(ValidationError, match="Asset validation failed"):
            Asset(
                name="Test Asset",
                asset_type=AssetType.EQUITY,
                current_value=10000.0,
                expected_return=3.0,  # 300% return is invalid
                volatility=0.15
            )

    def test_asset_validation_invalid_volatility(self):
        """Test asset validation with invalid volatility."""
        with pytest.raises(ValidationError, match="Asset validation failed"):
            Asset(
                name="Test Asset",
                asset_type=AssetType.EQUITY,
                current_value=10000.0,
                expected_return=0.08,
                volatility=-0.1  # Negative volatility is invalid
            )

    def test_get_metrics(self):
        """Test getting asset metrics."""
        asset = Asset(
            name="Test Asset",
            asset_type=AssetType.EQUITY,
            current_value=10000.0,
            expected_return=0.08,
            volatility=0.15
        )
        metrics = asset.get_metrics()
        assert metrics.expected_return == 0.08
        assert metrics.volatility == 0.15
        assert metrics.sharpe_ratio == pytest.approx(0.533, rel=1e-2)

    def test_get_correlation(self):
        """Test getting correlation with another asset."""
        asset = Asset(
            name="Test Asset",
            asset_type=AssetType.EQUITY,
            current_value=10000.0,
            expected_return=0.08,
            volatility=0.15,
            correlation={'bond': 0.2, 'cash': -0.1}
        )
        assert asset.get_correlation('bond') == 0.2
        assert asset.get_correlation('cash') == -0.1
        assert asset.get_correlation('nonexistent') == 0.0

    def test_get_tax_treatment(self):
        """Test getting tax treatment information."""
        asset = Asset(
            name="Test Asset",
            asset_type=AssetType.EQUITY,
            current_value=10000.0,
            expected_return=0.08,
            volatility=0.15
        )
        tax_treatment = asset.get_tax_treatment()
        assert tax_treatment['asset_type'] == 'equity'
        assert tax_treatment['tax_rate'] == 0.15
        assert tax_treatment['tax_deferred'] is False
        assert tax_treatment['tax_exempt'] is False

    def test_calculate_future_value(self):
        """Test calculating future value of asset."""
        asset = Asset(
            name="Test Asset",
            asset_type=AssetType.EQUITY,
            current_value=10000.0,
            expected_return=0.08,
            volatility=0.15
        )
        future_value = asset.calculate_future_value(5, inflation_rate=0.02)
        expected_value = 10000.0 * (1 + 0.08 - 0.02) ** 5
        assert future_value == pytest.approx(expected_value, rel=1e-2)

    def test_calculate_risk_metrics(self):
        """Test calculating risk metrics."""
        asset = Asset(
            name="Test Asset",
            asset_type=AssetType.EQUITY,
            current_value=10000.0,
            expected_return=0.08,
            volatility=0.15
        )
        risk_metrics = asset.calculate_risk_metrics()
        assert risk_metrics['volatility'] == 0.15
        assert risk_metrics['sharpe_ratio'] == pytest.approx(0.533, rel=1e-2)
        assert 'var' in risk_metrics


class TestAssetFactory:
    """Test AssetFactory class functionality."""

    def test_create_asset_valid(self):
        """Test creating asset with valid type."""
        asset = AssetFactory.create_asset(
            asset_type="equity",
            name="Test Stock",
            current_value=10000.0,
            expected_return=0.08,
            volatility=0.15
        )
        assert asset.asset_type == AssetType.EQUITY
        assert asset.name == "Test Stock"

    def test_create_asset_invalid_type(self):
        """Test creating asset with invalid type."""
        with pytest.raises(AssetError, match="Invalid asset type"):
            AssetFactory.create_asset(
                asset_type="invalid_type",
                name="Test Asset",
                current_value=10000.0,
                expected_return=0.08,
                volatility=0.15
            )

    def test_create_from_dict_valid(self):
        """Test creating asset from valid dictionary."""
        data = {
            'name': 'Test Asset',
            'asset_type': 'equity',
            'current_value': 10000.0,
            'expected_return': 0.08,
            'volatility': 0.15,
            'correlation': {'bond': 0.2},
            'description': 'Test description'
        }
        asset = AssetFactory.create_from_dict(data)
        assert asset.name == 'Test Asset'
        assert asset.asset_type == AssetType.EQUITY
        assert asset.correlation['bond'] == 0.2
        assert asset.description == 'Test description'

    def test_create_from_dict_missing_field(self):
        """Test creating asset from dictionary with missing field."""
        data = {
            'name': 'Test Asset',
            'asset_type': 'equity',
            'current_value': 10000.0,
            'expected_return': 0.08
            # Missing volatility
        }
        with pytest.raises(AssetError, match="Missing required field"):
            AssetFactory.create_from_dict(data)


class TestAssetAllocation:
    """Test AssetAllocation class functionality."""

    def test_allocation_creation_valid(self):
        """Test creating valid asset allocation."""
        allocations = {'stocks': 0.6, 'bonds': 0.3, 'cash': 0.1}
        allocation = AssetAllocation(
            name="Conservative",
            allocations=allocations
        )
        assert allocation.name == "Conservative"
        assert allocation.allocations == allocations

    def test_allocation_validation_sum_not_100(self):
        """Test allocation validation when sum is not 100%."""
        allocations = {'stocks': 0.6, 'bonds': 0.3}  # Sum = 90%
        with pytest.raises(ValidationError, match="Allocations must sum to 100%"):
            AssetAllocation(name="Invalid", allocations=allocations)

    def test_allocation_validation_negative_allocation(self):
        """Test allocation validation with negative allocation."""
        allocations = {'stocks': 0.6, 'bonds': 0.3, 'cash': -0.1}
        with pytest.raises(ValidationError, match="Allocation for cash must be between 0% and 100%"):
            AssetAllocation(name="Invalid", allocations=allocations)

    def test_allocation_validation_over_100_percent(self):
        """Test allocation validation with allocation over 100%."""
        allocations = {'stocks': 0.6, 'bonds': 0.5}  # Sum = 110%
        with pytest.raises(ValidationError, match="Allocations must sum to 100%"):
            AssetAllocation(name="Invalid", allocations=allocations)

    def test_get_allocation(self):
        """Test getting allocation for specific asset."""
        allocations = {'stocks': 0.6, 'bonds': 0.3, 'cash': 0.1}
        allocation = AssetAllocation(name="Test", allocations=allocations)
        assert allocation.get_allocation('stocks') == 0.6
        assert allocation.get_allocation('bonds') == 0.3
        assert allocation.get_allocation('nonexistent') == 0.0

    def test_get_expected_return(self):
        """Test calculating expected return for allocation."""
        allocations = {'stocks': 0.6, 'bonds': 0.4}
        allocation = AssetAllocation(name="Test", allocations=allocations)

        assets = {
            'stocks': Asset(
                name="Stocks",
                asset_type=AssetType.EQUITY,
                current_value=10000.0,
                expected_return=0.08,
                volatility=0.15
            ),
            'bonds': Asset(
                name="Bonds",
                asset_type=AssetType.BOND,
                current_value=10000.0,
                expected_return=0.04,
                volatility=0.05
            )
        }

        expected_return = allocation.get_expected_return(assets)
        expected = 0.6 * 0.08 + 0.4 * 0.04
        assert expected_return == pytest.approx(expected, rel=1e-2)

    def test_get_volatility(self):
        """Test calculating portfolio volatility."""
        allocations = {'stocks': 0.6, 'bonds': 0.4}
        allocation = AssetAllocation(name="Test", allocations=allocations)

        assets = {
            'stocks': Asset(
                name="Stocks",
                asset_type=AssetType.EQUITY,
                current_value=10000.0,
                expected_return=0.08,
                volatility=0.15,
                correlation={'bonds': 0.2}
            ),
            'bonds': Asset(
                name="Bonds",
                asset_type=AssetType.BOND,
                current_value=10000.0,
                expected_return=0.04,
                volatility=0.05,
                correlation={'stocks': 0.2}
            )
        }

        volatility = allocation.get_volatility(assets)
        # Simplified calculation should be positive
        assert volatility > 0
        assert volatility < 0.15  # Should be less than max individual volatility

    def test_rebalance(self):
        """Test calculating rebalancing trades."""
        allocations = {'stocks': 0.6, 'bonds': 0.4}
        allocation = AssetAllocation(name="Test", allocations=allocations)

        current_values = {'stocks': 6500.0, 'bonds': 3500.0}  # 65%/35%
        target_values = {'stocks': 6000.0, 'bonds': 4000.0}  # 60%/40%

        trades = allocation.rebalance(current_values, target_values)

        # Should sell stocks and buy bonds
        assert trades['stocks'] < 0  # Sell stocks
        assert trades['bonds'] > 0   # Buy bonds

    def test_rebalance_no_trades_needed(self):
        """Test rebalancing when no trades are needed."""
        allocations = {'stocks': 0.6, 'bonds': 0.4}
        allocation = AssetAllocation(name="Test", allocations=allocations)

        current_values = {'stocks': 6000.0, 'bonds': 4000.0}  # Already balanced
        target_values = {'stocks': 6000.0, 'bonds': 4000.0}

        trades = allocation.rebalance(current_values, target_values)
        assert len(trades) == 0  # No trades needed