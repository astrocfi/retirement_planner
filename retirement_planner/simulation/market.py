"""
Market modeling for Monte Carlo simulation.

This module provides market modeling capabilities including return simulation
and correlation modeling for Monte Carlo analysis.
"""

from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass
import numpy as np
from abc import ABC, abstractmethod

from retirement_planner.assets.base import Asset
from retirement_planner.core.exceptions import SimulationError


class MarketModel(ABC):
    """Abstract base for market models."""

    @abstractmethod
    def simulate_returns(self, assets: Dict[str, Asset], num_years: int) -> Dict[str, List[float]]:
        """Simulate returns for assets over the given time period."""
        pass


@dataclass(frozen=True)
class CorrelationModel:
    """Handles correlation between assets."""

    correlation_matrix: Dict[str, Dict[str, float]]

    def validate(self) -> None:
        """Validate correlation matrix."""
        if not self.correlation_matrix:
            return

        # Check that all assets have correlation entries
        asset_names = set(self.correlation_matrix.keys())
        for asset_name, correlations in self.correlation_matrix.items():
            if set(correlations.keys()) != asset_names:
                raise SimulationError(f"Correlation matrix for {asset_name} missing some assets")

            # Check diagonal values are 1.0
            if correlations[asset_name] != 1.0:
                raise SimulationError(f"Correlation of {asset_name} with itself must be 1.0")

            # Check correlation values are in [-1, 1]
            for other_asset, corr in correlations.items():
                if not (-1.0 <= corr <= 1.0):
                    raise SimulationError(f"Correlation between {asset_name} and {other_asset} must be in [-1, 1]")

    def get_correlation(self, asset1: str, asset2: str) -> float:
        """Get correlation between two assets."""
        if asset1 == asset2:
            return 1.0

        if asset1 in self.correlation_matrix and asset2 in self.correlation_matrix[asset1]:
            return self.correlation_matrix[asset1][asset2]

        # Default to zero correlation if not specified
        return 0.0

    def get_cholesky_decomposition(self, asset_names: List[str]) -> np.ndarray:
        """Get Cholesky decomposition of correlation matrix for correlated sampling."""
        n = len(asset_names)
        if n == 0:
            return np.array([])

        # Build correlation matrix
        corr_matrix = np.zeros((n, n))
        for i, asset1 in enumerate(asset_names):
            for j, asset2 in enumerate(asset_names):
                corr_matrix[i, j] = self.get_correlation(asset1, asset2)

        # Check if matrix is positive definite
        try:
            cholesky = np.linalg.cholesky(corr_matrix)
            return cholesky
        except np.linalg.LinAlgError:
            raise SimulationError("Correlation matrix is not positive definite")


class ReturnSimulator:
    """Simulates asset returns with correlation."""

    def __init__(self, correlation_model: Optional[CorrelationModel] = None):
        self.correlation_model = correlation_model

    def simulate_uncorrelated_returns(self, assets: Dict[str, Asset], num_years: int) -> Dict[str, List[float]]:
        """Simulate uncorrelated returns for assets."""
        returns = {}

        for asset_name, asset in assets.items():
            expected_return = asset.expected_return
            volatility = asset.volatility

            # Generate random returns using normal distribution
            annual_returns = np.random.normal(expected_return, volatility, num_years)

            # Ensure returns are reasonable (not below -100%)
            annual_returns = np.maximum(annual_returns, -0.99)

            returns[asset_name] = annual_returns.tolist()

        return returns

    def simulate_correlated_returns(self, assets: Dict[str, Asset], num_years: int) -> Dict[str, List[float]]:
        """Simulate correlated returns for assets."""
        if not self.correlation_model:
            return self.simulate_uncorrelated_returns(assets, num_years)

        asset_names = list(assets.keys())
        if len(asset_names) == 0:
            return {}

        # Validate correlation model
        self.correlation_model.validate()

        # Get Cholesky decomposition
        cholesky = self.correlation_model.get_cholesky_decomposition(asset_names)

        # Generate uncorrelated random numbers
        uncorrelated = np.random.normal(0, 1, (len(asset_names), num_years))

        # Apply Cholesky transformation to get correlated random numbers
        correlated = cholesky @ uncorrelated

        # Transform to asset-specific returns
        returns = {}
        for i, asset_name in enumerate(asset_names):
            asset = assets[asset_name]
            expected_return = asset.expected_return
            volatility = asset.volatility

            # Transform standard normal to asset-specific distribution
            asset_returns = expected_return + volatility * correlated[i, :]

            # Ensure returns are reasonable (not below -100%)
            asset_returns = np.maximum(asset_returns, -0.99)

            returns[asset_name] = asset_returns.tolist()

        return returns

    def simulate_returns(self, assets: Dict[str, Asset], num_years: int, use_correlation: bool = True) -> Dict[str, List[float]]:
        """Simulate returns for assets."""
        if use_correlation and self.correlation_model:
            return self.simulate_correlated_returns(assets, num_years)
        else:
            return self.simulate_uncorrelated_returns(assets, num_years)


class SimpleMarketModel(MarketModel):
    """Simple market model using uncorrelated returns."""

    def __init__(self, seed: Optional[int] = None):
        if seed is not None:
            np.random.seed(seed)
        self.return_simulator = ReturnSimulator()

    def simulate_returns(self, assets: Dict[str, Asset], num_years: int) -> Dict[str, List[float]]:
        """Simulate uncorrelated returns for assets."""
        return self.return_simulator.simulate_returns(assets, num_years, use_correlation=False)


class CorrelatedMarketModel(MarketModel):
    """Market model using correlated returns."""

    def __init__(self, correlation_model: CorrelationModel, seed: Optional[int] = None):
        if seed is not None:
            np.random.seed(seed)
        self.return_simulator = ReturnSimulator(correlation_model)

    def simulate_returns(self, assets: Dict[str, Asset], num_years: int) -> Dict[str, List[float]]:
        """Simulate correlated returns for assets."""
        return self.return_simulator.simulate_returns(assets, num_years, use_correlation=True)