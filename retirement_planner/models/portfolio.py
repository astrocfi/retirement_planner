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
        return portfolio.allocation.rebalance(portfolio.asset_values, portfolio.total_value)

@dataclass(frozen=True)
class Portfolio:
    """
    Represents a portfolio of assets and their allocation.
    """
    assets: Dict[str, Asset]  # asset_name -> Asset
    allocation: AssetAllocation
    asset_values: Dict[str, float]  # asset_name -> current value
    rebalancing_strategy: RebalancingStrategy = field(default_factory=StaticRebalancingStrategy)

    @property
    def total_value(self) -> float:
        return sum(self.asset_values.values())

    def rebalance(self) -> 'Portfolio':
        """
        Returns a new Portfolio with asset_values rebalanced to the target allocation.
        """
        try:
            new_values = self.rebalancing_strategy.rebalance(self)
        except Exception as e:
            raise PortfolioError(f"Rebalancing failed: {e}")
        return replace(self, asset_values=new_values)

    def get_allocation_percentages(self) -> Dict[str, float]:
        total = self.total_value
        if total == 0:
            return {k: 0.0 for k in self.asset_values}
        return {k: v / total for k, v in self.asset_values.items()}

    def get_asset(self, asset_name: str) -> Asset:
        if asset_name not in self.assets:
            raise PortfolioError(f"Asset '{asset_name}' not found in portfolio.")
        return self.assets[asset_name]

    def validate(self) -> None:
        self.allocation.validate()
        if set(self.assets.keys()) != set(self.asset_values.keys()):
            raise PortfolioError("Assets and asset_values keys must match.")
        for asset in self.assets.values():
            if not isinstance(asset, Asset):
                raise PortfolioError(f"Invalid asset type: {type(asset)}")