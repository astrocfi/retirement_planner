from typing import Dict, List, Type, Optional
from dataclasses import dataclass, field, replace
from retirement_planner.assets.base import Asset
from retirement_planner.core.exceptions import PortfolioError
from abc import ABC, abstractmethod

@dataclass(frozen=True)
class AssetAllocation:
    """
    Represents an immutable asset allocation.
    """
    allocation: Dict[str, float]  # asset_name -> percentage (0-1)

    def __post_init__(self):
        """Validate allocation on creation."""
        self.validate()

    def validate(self) -> None:
        total = sum(self.allocation.values())
        if not (0.99 <= total <= 1.01):
            raise PortfolioError(f"Allocation must sum to 1.0, got {total}")
        for asset, pct in self.allocation.items():
            if not (0.0 <= pct <= 1.0):
                raise PortfolioError(f"Allocation for {asset} out of bounds: {pct}")

    def rebalance(self, current_values: Dict[str, float], total_value: float) -> Dict[str, float]:
        """
        Returns the target dollar amount for each asset after rebalancing.
        """
        self.validate()
        return {asset: pct * total_value for asset, pct in self.allocation.items()}

class RebalancingStrategy(ABC):
    """
    Abstract base for rebalancing strategies.
    """
    @abstractmethod
    def rebalance(self, portfolio: 'Portfolio') -> Dict[str, float]:
        pass

class StaticRebalancingStrategy(RebalancingStrategy):
    """
    Rebalance to target allocation at each call.
    """
    def rebalance(self, portfolio: 'Portfolio') -> Dict[str, float]:
        return portfolio.allocation_targets.rebalance(portfolio.asset_values, portfolio.total_value)

@dataclass(frozen=True)
class Portfolio:
    """
    Represents a portfolio of assets and their allocation.
    """
    assets: List[Asset]  # List of Asset objects
    allocation_targets: AssetAllocation
    rebalancing_strategy: RebalancingStrategy = field(default_factory=StaticRebalancingStrategy)

    @property
    def asset_values(self) -> Dict[str, float]:
        """Get current asset values as a dictionary."""
        return {asset.name: asset.current_value for asset in self.assets}

    @property
    def total_value(self) -> float:
        return sum(asset.current_value for asset in self.assets)

    def rebalance(self) -> 'Portfolio':
        """
        Returns a new Portfolio with asset_values rebalanced to the target allocation.
        """
        try:
            new_values = self.rebalancing_strategy.rebalance(self)
            # Create new assets with updated values
            new_assets = []
            for asset in self.assets:
                if asset.name in new_values:
                    new_asset = replace(asset, current_value=new_values[asset.name])
                    new_assets.append(new_asset)
                else:
                    new_assets.append(asset)
            return replace(self, assets=new_assets)
        except Exception as e:
            raise PortfolioError(f"Rebalancing failed: {e}")

    def get_allocation_percentages(self) -> Dict[str, float]:
        total = self.total_value
        if total == 0:
            return {asset.name: 0.0 for asset in self.assets}
        return {asset.name: asset.current_value / total for asset in self.assets}

    def get_asset(self, asset_name: str) -> Asset:
        for asset in self.assets:
            if asset.name == asset_name:
                return asset
        raise PortfolioError(f"Asset '{asset_name}' not found in portfolio.")

    def validate(self) -> None:
        self.allocation_targets.validate()
        asset_names = {asset.name for asset in self.assets}
        allocation_names = set(self.allocation_targets.allocation.keys())

        if asset_names != allocation_names:
            raise PortfolioError(f"Asset names ({asset_names}) must match allocation names ({allocation_names})")

        for asset in self.assets:
            if not isinstance(asset, Asset):
                raise PortfolioError(f"Invalid asset type: {type(asset)}")