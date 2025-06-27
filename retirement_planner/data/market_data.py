"""
Market data loading and management for retirement planning.

This module provides functionality to load and manage historical market data,
correlation matrices, and risk-free rates needed for Monte Carlo simulations
and portfolio analysis.
"""

import numpy as np
import pandas as pd
from datetime import date, datetime
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple, Union, Any
from pathlib import Path
import json
import yaml
import warnings

# Optional imports for web data download
try:
    import yfinance as yf
except ImportError:
    yf = None
    warnings.warn("yfinance not available. Yahoo Finance download methods will not work.")

try:
    import requests
except ImportError:
    requests = None
    warnings.warn("requests not available. Web download methods will not work.")

from ..core.exceptions import DataError
from ..core.validation import Validator, RequiredRule, TypeRule, RangeRule
from ..utils.math_utils import StatisticalUtils


class MarketDataError(DataError):
    """Exception raised for market data related errors."""
    pass


@dataclass(frozen=True)
class HistoricalReturns:
    """Historical returns data for assets."""

    asset_names: List[str]
    returns_data: pd.DataFrame
    start_date: date
    end_date: date
    frequency: str = "monthly"  # daily, weekly, monthly, quarterly, yearly

    def __post_init__(self):
        """Validate the historical returns data."""
        validator = Validator()

        # Add field validators
        validator.add_field_validator("asset_names").add_rule(RequiredRule("asset_names"))
        validator.add_field_validator("returns_data").add_rule(RequiredRule("returns_data"))
        validator.add_field_validator("start_date").add_rule(RequiredRule("start_date"))
        validator.add_field_validator("end_date").add_rule(RequiredRule("end_date"))
        validator.add_field_validator("frequency").add_rule(TypeRule("frequency", str))

        # Validate the data
        data = {
            "asset_names": self.asset_names,
            "returns_data": self.returns_data,
            "start_date": self.start_date,
            "end_date": self.end_date,
            "frequency": self.frequency
        }

        result = validator.validate(data)
        if not result.is_valid:
            raise MarketDataError(f"Invalid historical returns data: {[e.message for e in result.errors]}")

        # Validate data consistency
        if len(self.asset_names) != len(self.returns_data.columns):
            raise MarketDataError("Number of asset names must match number of columns in returns data")

        if self.start_date >= self.end_date:
            raise MarketDataError("Start date must be before end date")

    def get_asset_returns(self, asset_name: str) -> pd.Series:
        """Get returns for a specific asset."""
        if asset_name not in self.asset_names:
            raise MarketDataError(f"Asset '{asset_name}' not found in data")
        return self.returns_data[asset_name]

    def get_mean_returns(self) -> Dict[str, float]:
        """Calculate mean returns for all assets."""
        return {asset: StatisticalUtils.calculate_mean(self.returns_data[asset].dropna().tolist())
                for asset in self.asset_names}

    def get_volatilities(self) -> Dict[str, float]:
        """Calculate volatilities for all assets."""
        return {asset: StatisticalUtils.calculate_std_deviation(self.returns_data[asset].dropna().tolist())
                for asset in self.asset_names}

    def get_correlation_matrix(self) -> pd.DataFrame:
        """Calculate correlation matrix for all assets."""
        return self.returns_data.corr()

    def get_annualized_returns(self) -> Dict[str, float]:
        """Calculate annualized returns for all assets."""
        frequency_multipliers = {
            "daily": 252,
            "weekly": 52,
            "monthly": 12,
            "quarterly": 4,
            "yearly": 1
        }

        multiplier = frequency_multipliers.get(self.frequency, 12)
        mean_returns = self.get_mean_returns()

        return {asset: mean_return * multiplier for asset, mean_return in mean_returns.items()}

    def get_annualized_volatilities(self) -> Dict[str, float]:
        """Calculate annualized volatilities for all assets."""
        frequency_multipliers = {
            "daily": 252,
            "weekly": 52,
            "monthly": 12,
            "quarterly": 4,
            "yearly": 1
        }

        multiplier = frequency_multipliers.get(self.frequency, 12)
        volatilities = self.get_volatilities()

        return {asset: volatility * np.sqrt(multiplier) for asset, volatility in volatilities.items()}

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "asset_names": self.asset_names,
            "returns_data": self.returns_data.to_dict(),
            "start_date": self.start_date.isoformat(),
            "end_date": self.end_date.isoformat(),
            "frequency": self.frequency
        }


@dataclass(frozen=True)
class CorrelationMatrix:
    """Correlation matrix for asset returns."""

    asset_names: List[str]
    correlation_data: pd.DataFrame

    def __post_init__(self):
        """Validate the correlation matrix."""
        validator = Validator()

        # Add field validators
        validator.add_field_validator("asset_names").add_rule(RequiredRule("asset_names"))
        validator.add_field_validator("correlation_data").add_rule(RequiredRule("correlation_data"))

        # Validate the data
        data = {
            "asset_names": self.asset_names,
            "correlation_data": self.correlation_data
        }

        result = validator.validate(data)
        if not result.is_valid:
            raise MarketDataError(f"Invalid correlation matrix: {[e.message for e in result.errors]}")

        # Validate matrix properties
        if len(self.asset_names) != len(self.correlation_data.columns):
            raise MarketDataError("Number of asset names must match correlation matrix dimensions")

        if len(self.asset_names) != len(self.correlation_data.index):
            raise MarketDataError("Correlation matrix must be square")

        # Check if matrix is symmetric
        if not self.correlation_data.equals(self.correlation_data.T):
            raise MarketDataError("Correlation matrix must be symmetric")

        # Check diagonal elements are 1.0
        for i, asset in enumerate(self.asset_names):
            if abs(self.correlation_data.iloc[i, i] - 1.0) > 1e-6:
                raise MarketDataError(f"Diagonal element for {asset} must be 1.0")

    def get_correlation(self, asset1: str, asset2: str) -> float:
        """Get correlation between two assets."""
        if asset1 not in self.asset_names or asset2 not in self.asset_names:
            raise MarketDataError(f"Asset not found in correlation matrix")
        return self.correlation_data.loc[asset1, asset2]

    def is_positive_definite(self) -> bool:
        """Check if correlation matrix is positive definite."""
        try:
            np.linalg.cholesky(self.correlation_data.values)
            return True
        except np.linalg.LinAlgError:
            return False

    def get_cholesky_decomposition(self) -> np.ndarray:
        """Get Cholesky decomposition of correlation matrix."""
        if not self.is_positive_definite():
            raise MarketDataError("Correlation matrix is not positive definite")
        return np.linalg.cholesky(self.correlation_data.values)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "asset_names": self.asset_names,
            "correlation_data": self.correlation_data.to_dict()
        }


@dataclass(frozen=True)
class RiskFreeRate:
    """Risk-free rate data."""

    rate: float
    start_date: date
    end_date: date
    frequency: str = "monthly"
    source: str = "Treasury"

    def __post_init__(self):
        """Validate the risk-free rate data."""
        validator = Validator()

        # Add field validators
        validator.add_field_validator("rate").add_rule(RequiredRule("rate")).add_rule(RangeRule("rate", 0.0, 1.0))
        validator.add_field_validator("start_date").add_rule(RequiredRule("start_date"))
        validator.add_field_validator("end_date").add_rule(RequiredRule("end_date"))
        validator.add_field_validator("frequency").add_rule(TypeRule("frequency", str))
        validator.add_field_validator("source").add_rule(TypeRule("source", str))

        # Validate the data
        data = {
            "rate": self.rate,
            "start_date": self.start_date,
            "end_date": self.end_date,
            "frequency": self.frequency,
            "source": self.source
        }

        result = validator.validate(data)
        if not result.is_valid:
            raise MarketDataError(f"Invalid risk-free rate data: {[e.message for e in result.errors]}")

        if self.start_date >= self.end_date:
            raise MarketDataError("Start date must be before end date")

    def get_annualized_rate(self) -> float:
        """Get annualized risk-free rate."""
        frequency_multipliers = {
            "daily": 252,
            "weekly": 52,
            "monthly": 12,
            "quarterly": 4,
            "yearly": 1
        }

        multiplier = frequency_multipliers.get(self.frequency, 12)
        return self.rate * multiplier

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "rate": self.rate,
            "start_date": self.start_date.isoformat(),
            "end_date": self.end_date.isoformat(),
            "frequency": self.frequency,
            "source": self.source
        }


class MarketDataLoader:
    """Loader for market data from various sources."""

    def __init__(self, data_directory: Optional[Path] = None):
        """Initialize the market data loader."""
        self.data_directory = data_directory or Path("data/market")
        self.data_directory.mkdir(parents=True, exist_ok=True)

    def load_historical_returns(self, file_path: Union[str, Path]) -> HistoricalReturns:
        """Load historical returns from CSV file."""
        file_path = Path(file_path)

        if not file_path.exists():
            raise MarketDataError(f"File not found: {file_path}")

        try:
            # Load CSV with date index
            df = pd.read_csv(file_path, index_col=0, parse_dates=True)

            # Convert to returns if needed (check if data looks like prices)
            if df.iloc[0, 0] > 1.0:  # Likely prices, convert to returns
                df = df.pct_change().dropna()

            # Extract asset names and date range
            asset_names = list(df.columns)
            start_date = df.index[0].date()
            end_date = df.index[-1].date()

            return HistoricalReturns(
                asset_names=asset_names,
                returns_data=df,
                start_date=start_date,
                end_date=end_date,
                frequency="monthly"  # Default, could be detected from data
            )

        except Exception as e:
            raise MarketDataError(f"Error loading historical returns: {e}")

    def load_correlation_matrix(self, file_path: Union[str, Path]) -> CorrelationMatrix:
        """Load correlation matrix from CSV file."""
        file_path = Path(file_path)

        if not file_path.exists():
            raise MarketDataError(f"File not found: {file_path}")

        try:
            df = pd.read_csv(file_path, index_col=0)

            # Validate correlation matrix
            if not df.equals(df.T):
                raise MarketDataError("Correlation matrix must be symmetric")

            asset_names = list(df.columns)

            return CorrelationMatrix(
                asset_names=asset_names,
                correlation_data=df
            )

        except Exception as e:
            raise MarketDataError(f"Error loading correlation matrix: {e}")

    def load_risk_free_rate(self, file_path: Union[str, Path]) -> RiskFreeRate:
        """Load risk-free rate from JSON file."""
        file_path = Path(file_path)

        if not file_path.exists():
            raise MarketDataError(f"File not found: {file_path}")

        try:
            with open(file_path, 'r') as f:
                data = json.load(f)

            return RiskFreeRate(
                rate=data['rate'],
                start_date=date.fromisoformat(data['start_date']),
                end_date=date.fromisoformat(data['end_date']),
                frequency=data.get('frequency', 'monthly'),
                source=data.get('source', 'Treasury')
            )

        except Exception as e:
            raise MarketDataError(f"Error loading risk-free rate: {e}")

    def save_historical_returns(self, returns: HistoricalReturns, file_path: Union[str, Path]) -> None:
        """Save historical returns to CSV file."""
        file_path = Path(file_path)
        file_path.parent.mkdir(parents=True, exist_ok=True)

        try:
            returns.returns_data.to_csv(file_path)
        except Exception as e:
            raise MarketDataError(f"Error saving historical returns: {e}")

    def save_correlation_matrix(self, correlation: CorrelationMatrix, file_path: Union[str, Path]) -> None:
        """Save correlation matrix to CSV file."""
        file_path = Path(file_path)
        file_path.parent.mkdir(parents=True, exist_ok=True)

        try:
            correlation.correlation_data.to_csv(file_path)
        except Exception as e:
            raise MarketDataError(f"Error saving correlation matrix: {e}")

    def save_risk_free_rate(self, rate: RiskFreeRate, file_path: Union[str, Path]) -> None:
        """Save risk-free rate to JSON file."""
        file_path = Path(file_path)
        file_path.parent.mkdir(parents=True, exist_ok=True)

        try:
            with open(file_path, 'w') as f:
                json.dump(rate.to_dict(), f, indent=2)
        except Exception as e:
            raise MarketDataError(f"Error saving risk-free rate: {e}")

    def generate_sample_data(self) -> Tuple[HistoricalReturns, CorrelationMatrix, RiskFreeRate]:
        """Generate sample market data for testing."""
        # Generate sample historical returns
        np.random.seed(42)
        dates = pd.date_range('2020-01-01', '2023-12-31', freq='ME')
        asset_names = ['US_Stocks', 'International_Stocks', 'Bonds', 'Real_Estate']

        # Generate correlated returns
        returns_data = pd.DataFrame(
            np.random.multivariate_normal(
                mean=[0.01, 0.008, 0.005, 0.007],  # Monthly returns
                cov=[[0.04, 0.03, 0.01, 0.02],
                     [0.03, 0.06, 0.01, 0.025],
                     [0.01, 0.01, 0.02, 0.01],
                     [0.02, 0.025, 0.01, 0.05]],
                size=len(dates)
            ),
            index=dates,
            columns=asset_names
        )

        historical_returns = HistoricalReturns(
            asset_names=asset_names,
            returns_data=returns_data,
            start_date=dates[0].date(),
            end_date=dates[-1].date(),
            frequency="monthly"
        )

        # Generate correlation matrix
        correlation_data = returns_data.corr()
        correlation_matrix = CorrelationMatrix(
            asset_names=asset_names,
            correlation_data=correlation_data
        )

        # Generate risk-free rate
        risk_free_rate = RiskFreeRate(
            rate=0.004,  # 0.4% monthly
            start_date=dates[0].date(),
            end_date=dates[-1].date(),
            frequency="monthly",
            source="Treasury"
        )

        return historical_returns, correlation_matrix, risk_free_rate

    def download_historical_returns_from_yahoo(self, tickers, start, end, file_path=None):
        """Download historical price/returns data from Yahoo Finance and save as CSV."""
        if yf is None:
            raise ImportError("yfinance is required for Yahoo Finance downloads")

        data = yf.download(tickers, start=start, end=end, auto_adjust=True)['Adj Close']
        returns = data.pct_change().dropna()
        if file_path:
            returns.to_csv(file_path)
        return returns

    def download_risk_free_rate_from_fred(self, symbol='DGS10', start='2000-01-01', end=None, file_path=None):
        """Download risk-free rate from FRED using direct API calls."""
        if requests is None:
            raise ImportError("requests is required for FRED downloads")

        # Use FRED API directly instead of pandas_datareader
        if end is None:
            end = datetime.now().strftime('%Y-%m-%d')

        url = f"https://api.stlouisfed.org/fred/series/observations"
        params = {
            'series_id': symbol,
            'api_key': 'demo',  # Use demo key for testing
            'file_type': 'json',
            'observation_start': start,
            'observation_end': end
        }

        response = requests.get(url, params=params)
        response.raise_for_status()

        data = response.json()
        observations = data['observations']

        # Convert to DataFrame
        dates = [obs['date'] for obs in observations]
        values = [float(obs['value']) if obs['value'] != '.' else np.nan for obs in observations]

        df = pd.DataFrame({'value': values}, index=pd.to_datetime(dates))

        if file_path:
            df.to_csv(file_path)

        return df