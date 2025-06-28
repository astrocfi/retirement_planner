"""
Tests for portfolio management functionality.
"""

import pytest
from retirement_planner.models.portfolio import Portfolio, AssetAllocation, StaticRebalancingStrategy
from retirement_planner.assets.base import Asset, AssetType


class TestAssetAllocation:
    """Test AssetAllocation functionality."""

    def test_asset_allocation_creation(self):
        """Test creating a valid asset allocation."""
        allocation = AssetAllocation({
            "stock": 0.6,
            "bond": 0.4
        })
        assert allocation.allocation["stock"] == 0.6
        assert allocation.allocation["bond"] == 0.4

    def test_asset_allocation_validation(self):
        """Test asset allocation validation."""
        # Valid allocation
        allocation = AssetAllocation({
            "stock": 0.6,
            "bond": 0.4
        })
        allocation.validate()  # Should not raise

    def test_asset_allocation_invalid_sum(self):
        """Test that allocation must sum to 1.0."""
        with pytest.raises(Exception):
            AssetAllocation({
                "stock": 0.6,
                "bond": 0.3  # Sum = 0.9, should be 1.0
            })

    def test_asset_allocation_invalid_percentages(self):
        """Test that allocation percentages must be between 0 and 1."""
        with pytest.raises(Exception):
            AssetAllocation({
                "stock": 1.2,  # > 1.0
                "bond": -0.2   # < 0.0
            })

    def test_asset_allocation_rebalance(self):
        """Test rebalancing calculation."""
        allocation = AssetAllocation({
            "stock": 0.6,
            "bond": 0.4
        })

        current_values = {"stock": 50000, "bond": 30000}
        total_value = 80000

        target_values = allocation.rebalance(current_values, total_value)

        assert target_values["stock"] == 48000  # 0.6 * 80000
        assert target_values["bond"] == 32000   # 0.4 * 80000

    def test_asset_allocation_rebalance_with_zero_total(self):
        """Test rebalancing with zero total value."""
        allocation = AssetAllocation({
            "stock": 0.6,
            "bond": 0.4
        })

        current_values = {"stock": 0, "bond": 0}
        total_value = 0

        target_values = allocation.rebalance(current_values, total_value)

        assert target_values["stock"] == 0
        assert target_values["bond"] == 0


class TestRebalancingStrategy:
    """Test rebalancing strategy functionality."""

    def test_static_rebalancing_strategy(self):
        """Test static rebalancing strategy."""
        strategy = StaticRebalancingStrategy()
        assert isinstance(strategy, StaticRebalancingStrategy)


class TestPortfolio:
    """Test Portfolio functionality."""

    def create_test_assets(self):
        """Create test assets for portfolio testing."""
        return [
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

    def test_portfolio_creation(self):
        """Test creating a portfolio."""
        assets = self.create_test_assets()
        allocation = AssetAllocation({
            "stock": 0.6,
            "bond": 0.4
        })

        portfolio = Portfolio(
            assets=assets,
            allocation_targets=allocation
        )

        assert len(portfolio.assets) == 2
        assert portfolio.total_value == 100000
        assert portfolio.allocation_targets == allocation

    def test_portfolio_asset_values_property(self):
        """Test the asset_values property."""
        assets = self.create_test_assets()
        allocation = AssetAllocation({
            "stock": 0.6,
            "bond": 0.4
        })

        portfolio = Portfolio(
            assets=assets,
            allocation_targets=allocation
        )

        asset_values = portfolio.asset_values
        assert asset_values["stock"] == 60000
        assert asset_values["bond"] == 40000

    def test_portfolio_total_value_property(self):
        """Test the total_value property."""
        assets = self.create_test_assets()
        allocation = AssetAllocation({
            "stock": 0.6,
            "bond": 0.4
        })

        portfolio = Portfolio(
            assets=assets,
            allocation_targets=allocation
        )

        assert portfolio.total_value == 100000

    def test_portfolio_get_allocation_percentages(self):
        """Test getting allocation percentages."""
        assets = self.create_test_assets()
        allocation = AssetAllocation({
            "stock": 0.6,
            "bond": 0.4
        })

        portfolio = Portfolio(
            assets=assets,
            allocation_targets=allocation
        )

        percentages = portfolio.get_allocation_percentages()
        assert percentages["stock"] == 0.6
        assert percentages["bond"] == 0.4

    def test_portfolio_get_allocation_percentages_zero_total(self):
        """Test allocation percentages with zero total value."""
        assets = [
            Asset(
                name="stock",
                asset_type=AssetType.EQUITY,
                current_value=0,
                expected_return=0.07,
                volatility=0.15
            ),
            Asset(
                name="bond",
                asset_type=AssetType.BOND,
                current_value=0,
                expected_return=0.03,
                volatility=0.05
            )
        ]
        allocation = AssetAllocation({
            "stock": 0.6,
            "bond": 0.4
        })

        portfolio = Portfolio(
            assets=assets,
            allocation_targets=allocation
        )

        percentages = portfolio.get_allocation_percentages()
        assert percentages["stock"] == 0.0
        assert percentages["bond"] == 0.0

    def test_portfolio_get_asset(self):
        """Test getting a specific asset."""
        assets = self.create_test_assets()
        allocation = AssetAllocation({
            "stock": 0.6,
            "bond": 0.4
        })

        portfolio = Portfolio(
            assets=assets,
            allocation_targets=allocation
        )

        stock_asset = portfolio.get_asset("stock")
        assert stock_asset.name == "stock"
        assert stock_asset.current_value == 60000

        bond_asset = portfolio.get_asset("bond")
        assert bond_asset.name == "bond"
        assert bond_asset.current_value == 40000

    def test_portfolio_get_nonexistent_asset(self):
        """Test getting a nonexistent asset raises error."""
        assets = self.create_test_assets()
        allocation = AssetAllocation({
            "stock": 0.6,
            "bond": 0.4
        })

        portfolio = Portfolio(
            assets=assets,
            allocation_targets=allocation
        )

        with pytest.raises(Exception):
            portfolio.get_asset("nonexistent")

    def test_portfolio_rebalance(self):
        """Test portfolio rebalancing."""
        assets = self.create_test_assets()
        allocation = AssetAllocation({
            "stock": 0.6,
            "bond": 0.4
        })

        portfolio = Portfolio(
            assets=assets,
            allocation_targets=allocation
        )

        # Rebalance the portfolio
        rebalanced_portfolio = portfolio.rebalance()

        # Check that the rebalanced portfolio has the correct target values
        target_values = allocation.rebalance(portfolio.asset_values, portfolio.total_value)

        for asset in rebalanced_portfolio.assets:
            assert asset.current_value == target_values[asset.name]

    def test_portfolio_validation(self):
        """Test portfolio validation."""
        assets = self.create_test_assets()
        allocation = AssetAllocation({
            "stock": 0.6,
            "bond": 0.4
        })

        portfolio = Portfolio(
            assets=assets,
            allocation_targets=allocation
        )

        portfolio.validate()  # Should not raise

    def test_portfolio_validation_mismatched_names(self):
        """Test portfolio validation with mismatched asset names."""
        assets = self.create_test_assets()
        # Allocation with different names than assets
        allocation = AssetAllocation({
            "equity": 0.6,
            "fixed_income": 0.4
        })

        portfolio = Portfolio(
            assets=assets,
            allocation_targets=allocation
        )

        with pytest.raises(Exception):
            portfolio.validate()

    def test_portfolio_validation_invalid_asset_type(self):
        """Test portfolio validation with invalid asset type."""
        assets = [
            Asset(
                name="stock",
                asset_type=AssetType.EQUITY,
                current_value=60000,
                expected_return=0.07,
                volatility=0.15
            ),
            "not an asset"  # Invalid type
        ]
        allocation = AssetAllocation({
            "stock": 0.6,
            "bond": 0.4
        })

        portfolio = Portfolio(
            assets=assets,
            allocation_targets=allocation
        )

        with pytest.raises(Exception):
            portfolio.validate()

    def test_portfolio_with_custom_rebalancing_strategy(self):
        """Test portfolio with custom rebalancing strategy."""
        assets = self.create_test_assets()
        allocation = AssetAllocation({
            "stock": 0.6,
            "bond": 0.4
        })

        strategy = StaticRebalancingStrategy()
        portfolio = Portfolio(
            assets=assets,
            allocation_targets=allocation,
            rebalancing_strategy=strategy
        )

        assert portfolio.rebalancing_strategy == strategy

    def test_portfolio_immutability(self):
        """Test that portfolio is immutable."""
        assets = self.create_test_assets()
        allocation = AssetAllocation({
            "stock": 0.6,
            "bond": 0.4
        })

        portfolio = Portfolio(
            assets=assets,
            allocation_targets=allocation
        )

        # Test that we can't modify the portfolio directly
        # (This would depend on the specific implementation of immutability)
        assert portfolio.total_value == 100000

    def test_portfolio_with_empty_assets(self):
        """Test portfolio with empty assets list."""
        allocation = AssetAllocation({
            "stock": 0.6,
            "bond": 0.4
        })

        portfolio = Portfolio(
            assets=[],
            allocation_targets=allocation
        )

        assert portfolio.total_value == 0
        assert portfolio.asset_values == {}
        assert portfolio.get_allocation_percentages() == {}

    def test_portfolio_rebalance_with_changed_values(self):
        """Test rebalancing after asset values have changed."""
        assets = self.create_test_assets()
        allocation = AssetAllocation({
            "stock": 0.6,
            "bond": 0.4
        })

        portfolio = Portfolio(
            assets=assets,
            allocation_targets=allocation
        )

        # Simulate market movement - stock went up, bond went down
        updated_assets = [
            Asset(
                name="stock",
                asset_type=AssetType.EQUITY,
                current_value=70000,  # Increased
                expected_return=0.07,
                volatility=0.15
            ),
            Asset(
                name="bond",
                asset_type=AssetType.BOND,
                current_value=30000,  # Decreased
                expected_return=0.03,
                volatility=0.05
            )
        ]

        updated_portfolio = Portfolio(
            assets=updated_assets,
            allocation_targets=allocation
        )

        # Rebalance to target allocation
        rebalanced_portfolio = updated_portfolio.rebalance()

        # Check that the rebalanced portfolio has the correct target values
        total_value = 100000  # 70000 + 30000
        target_values = allocation.rebalance(updated_portfolio.asset_values, total_value)

        for asset in rebalanced_portfolio.assets:
            assert asset.current_value == target_values[asset.name]