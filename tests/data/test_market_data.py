"""
Unit tests for market_data module.
"""

import pytest
import numpy as np
import pandas as pd
from datetime import date, datetime
from pathlib import Path
import tempfile
import json
from unittest.mock import patch, MagicMock

from retirement_planner.data.market_data import (
    MarketDataLoader,
    HistoricalReturns,
    CorrelationMatrix,
    RiskFreeRate,
    MarketDataError
)
from retirement_planner.core.exceptions import ValidationError


class TestHistoricalReturns:
    """Test HistoricalReturns class."""

    def test_historical_returns_creation(self):
        """Test creating historical returns with valid data."""
        dates = pd.date_range('2020-01-01', '2023-12-31', freq='ME')
        asset_names = ['US_Stocks', 'Bonds']

        returns_data = pd.DataFrame({
            'US_Stocks': np.random.normal(0.01, 0.05, len(dates)),
            'Bonds': np.random.normal(0.005, 0.02, len(dates))
        }, index=dates)

        historical_returns = HistoricalReturns(
            asset_names=asset_names,
            returns_data=returns_data,
            start_date=dates[0].date(),
            end_date=dates[-1].date(),
            frequency="monthly"
        )

        assert historical_returns.asset_names == asset_names
        assert len(historical_returns.returns_data) == len(dates)
        assert historical_returns.start_date == dates[0].date()
        assert historical_returns.end_date == dates[-1].date()
        assert historical_returns.frequency == "monthly"

    def test_historical_returns_validation_mismatched_columns(self):
        """Test validation when asset names don't match columns."""
        dates = pd.date_range('2020-01-01', '2023-12-31', freq='ME')
        asset_names = ['US_Stocks']  # Only one asset name

        returns_data = pd.DataFrame({
            'US_Stocks': np.random.normal(0.01, 0.05, len(dates)),
            'Bonds': np.random.normal(0.005, 0.02, len(dates))  # Extra column
        }, index=dates)

        with pytest.raises(MarketDataError, match="Number of asset names must match"):
            HistoricalReturns(
                asset_names=asset_names,
                returns_data=returns_data,
                start_date=dates[0].date(),
                end_date=dates[-1].date()
            )

    def test_historical_returns_validation_invalid_dates(self):
        """Test validation with invalid date range."""
        dates = pd.date_range('2020-01-01', '2023-12-31', freq='ME')
        asset_names = ['US_Stocks']

        returns_data = pd.DataFrame({
            'US_Stocks': np.random.normal(0.01, 0.05, len(dates))
        }, index=dates)

        with pytest.raises(MarketDataError, match="Start date must be before end date"):
            HistoricalReturns(
                asset_names=asset_names,
                returns_data=returns_data,
                start_date=dates[-1].date(),  # End date
                end_date=dates[0].date()      # Start date
            )

    def test_get_asset_returns(self):
        """Test getting returns for specific asset."""
        dates = pd.date_range('2020-01-01', '2023-12-31', freq='ME')
        asset_names = ['US_Stocks', 'Bonds']

        returns_data = pd.DataFrame({
            'US_Stocks': [0.01, 0.02, 0.03],
            'Bonds': [0.005, 0.006, 0.007]
        }, index=dates[:3])

        historical_returns = HistoricalReturns(
            asset_names=asset_names,
            returns_data=returns_data,
            start_date=dates[0].date(),
            end_date=dates[2].date()
        )

        us_stocks_returns = historical_returns.get_asset_returns('US_Stocks')
        assert len(us_stocks_returns) == 3
        assert us_stocks_returns.iloc[0] == 0.01

        with pytest.raises(MarketDataError, match="Asset 'Invalid' not found"):
            historical_returns.get_asset_returns('Invalid')

    def test_get_mean_returns(self):
        """Test calculating mean returns."""
        dates = pd.date_range('2020-01-01', '2023-12-31', freq='ME')
        asset_names = ['US_Stocks', 'Bonds']

        returns_data = pd.DataFrame({
            'US_Stocks': [0.01, 0.02, 0.03],
            'Bonds': [0.005, 0.006, 0.007]
        }, index=dates[:3])

        historical_returns = HistoricalReturns(
            asset_names=asset_names,
            returns_data=returns_data,
            start_date=dates[0].date(),
            end_date=dates[2].date()
        )

        mean_returns = historical_returns.get_mean_returns()
        assert 'US_Stocks' in mean_returns
        assert 'Bonds' in mean_returns
        assert abs(mean_returns['US_Stocks'] - 0.02) < 1e-6
        assert abs(mean_returns['Bonds'] - 0.006) < 1e-6

    def test_get_volatilities(self):
        """Test calculating volatilities."""
        dates = pd.date_range('2020-01-01', '2023-12-31', freq='ME')
        asset_names = ['US_Stocks']

        returns_data = pd.DataFrame({
            'US_Stocks': [0.01, 0.02, 0.03, 0.04, 0.05]
        }, index=dates[:5])

        historical_returns = HistoricalReturns(
            asset_names=asset_names,
            returns_data=returns_data,
            start_date=dates[0].date(),
            end_date=dates[4].date()
        )

        volatilities = historical_returns.get_volatilities()
        assert 'US_Stocks' in volatilities
        assert volatilities['US_Stocks'] > 0

    def test_get_correlation_matrix(self):
        """Test calculating correlation matrix."""
        dates = pd.date_range('2020-01-01', '2023-12-31', freq='ME')
        asset_names = ['US_Stocks', 'Bonds']

        # Create correlated returns
        np.random.seed(42)
        returns_data = pd.DataFrame({
            'US_Stocks': np.random.normal(0.01, 0.05, len(dates)),
            'Bonds': np.random.normal(0.005, 0.02, len(dates))
        }, index=dates)

        historical_returns = HistoricalReturns(
            asset_names=asset_names,
            returns_data=returns_data,
            start_date=dates[0].date(),
            end_date=dates[-1].date()
        )

        corr_matrix = historical_returns.get_correlation_matrix()
        assert corr_matrix.shape == (2, 2)
        assert abs(corr_matrix.iloc[0, 0] - 1.0) < 1e-6  # Diagonal should be 1
        assert abs(corr_matrix.iloc[1, 1] - 1.0) < 1e-6

    def test_get_annualized_returns(self):
        """Test calculating annualized returns."""
        dates = pd.date_range('2020-01-01', '2023-12-31', freq='ME')
        asset_names = ['US_Stocks']

        returns_data = pd.DataFrame({
            'US_Stocks': [0.01] * 12  # 1% monthly return
        }, index=dates[:12])

        historical_returns = HistoricalReturns(
            asset_names=asset_names,
            returns_data=returns_data,
            start_date=dates[0].date(),
            end_date=dates[11].date(),
            frequency="monthly"
        )

        annualized_returns = historical_returns.get_annualized_returns()
        assert abs(annualized_returns['US_Stocks'] - 0.12) < 1e-6  # 12% annualized

    def test_get_annualized_volatilities(self):
        """Test calculating annualized volatilities."""
        dates = pd.date_range('2020-01-01', '2023-12-31', freq='ME')
        asset_names = ['US_Stocks']

        returns_data = pd.DataFrame({
            'US_Stocks': [0.01, -0.01, 0.01, -0.01] * 3  # Alternating returns
        }, index=dates[:12])

        historical_returns = HistoricalReturns(
            asset_names=asset_names,
            returns_data=returns_data,
            start_date=dates[0].date(),
            end_date=dates[11].date(),
            frequency="monthly"
        )

        annualized_volatilities = historical_returns.get_annualized_volatilities()
        assert annualized_volatilities['US_Stocks'] > 0

    def test_to_dict(self):
        """Test converting to dictionary."""
        dates = pd.date_range('2020-01-01', '2023-12-31', freq='ME')
        asset_names = ['US_Stocks']

        returns_data = pd.DataFrame({
            'US_Stocks': [0.01, 0.02, 0.03]
        }, index=dates[:3])

        historical_returns = HistoricalReturns(
            asset_names=asset_names,
            returns_data=returns_data,
            start_date=dates[0].date(),
            end_date=dates[2].date()
        )

        data_dict = historical_returns.to_dict()
        assert 'asset_names' in data_dict
        assert 'returns_data' in data_dict
        assert 'start_date' in data_dict
        assert 'end_date' in data_dict
        assert 'frequency' in data_dict


class TestCorrelationMatrix:
    """Test CorrelationMatrix class."""

    def test_correlation_matrix_creation(self):
        """Test creating correlation matrix with valid data."""
        asset_names = ['US_Stocks', 'Bonds']
        correlation_data = pd.DataFrame({
            'US_Stocks': [1.0, 0.3],
            'Bonds': [0.3, 1.0]
        }, index=asset_names)

        correlation_matrix = CorrelationMatrix(
            asset_names=asset_names,
            correlation_data=correlation_data
        )

        assert correlation_matrix.asset_names == asset_names
        assert correlation_matrix.correlation_data.shape == (2, 2)

    def test_correlation_matrix_validation_non_square(self):
        """Test correlation matrix validation with non-square matrix."""
        # Create non-square matrix by having more columns than rows
        correlation_data = pd.DataFrame({
            'US_Stocks': [1.0, 0.3],
            'Bonds': [0.3, 1.0],
            'Real_Estate': [0.5, 0.2]  # Extra column
        }, index=['US_Stocks', 'Bonds'])  # Only 2 rows

        with pytest.raises(MarketDataError, match="Number of asset names must match correlation matrix dimensions"):
            CorrelationMatrix(
                asset_names=['US_Stocks', 'Bonds'],
                correlation_data=correlation_data
            )

    def test_correlation_matrix_validation_non_symmetric(self):
        """Test validation with non-symmetric matrix."""
        asset_names = ['US_Stocks', 'Bonds']
        correlation_data = pd.DataFrame({
            'US_Stocks': [1.0, 0.3],
            'Bonds': [0.5, 1.0]  # Different from 0.3
        }, index=asset_names)

        with pytest.raises(MarketDataError, match="Correlation matrix must be symmetric"):
            CorrelationMatrix(
                asset_names=asset_names,
                correlation_data=correlation_data
            )

    def test_correlation_matrix_validation_invalid_diagonal(self):
        """Test validation with invalid diagonal elements."""
        asset_names = ['US_Stocks', 'Bonds']
        correlation_data = pd.DataFrame({
            'US_Stocks': [0.9, 0.3],  # Not 1.0
            'Bonds': [0.3, 1.0]
        }, index=asset_names)

        with pytest.raises(MarketDataError, match="Diagonal element for US_Stocks must be 1.0"):
            CorrelationMatrix(
                asset_names=asset_names,
                correlation_data=correlation_data
            )

    def test_get_correlation(self):
        """Test getting correlation between two assets."""
        asset_names = ['US_Stocks', 'Bonds']
        correlation_data = pd.DataFrame({
            'US_Stocks': [1.0, 0.3],
            'Bonds': [0.3, 1.0]
        }, index=asset_names)

        correlation_matrix = CorrelationMatrix(
            asset_names=asset_names,
            correlation_data=correlation_data
        )

        correlation = correlation_matrix.get_correlation('US_Stocks', 'Bonds')
        assert abs(correlation - 0.3) < 1e-6

        with pytest.raises(MarketDataError, match="Asset not found"):
            correlation_matrix.get_correlation('Invalid', 'Bonds')

    def test_is_positive_definite(self):
        """Test checking if matrix is positive definite."""
        # Valid correlation matrix
        asset_names = ['US_Stocks', 'Bonds']
        correlation_data = pd.DataFrame({
            'US_Stocks': [1.0, 0.3],
            'Bonds': [0.3, 1.0]
        }, index=asset_names)

        correlation_matrix = CorrelationMatrix(
            asset_names=asset_names,
            correlation_data=correlation_data
        )

        assert correlation_matrix.is_positive_definite() is True

        # Invalid correlation matrix (perfect correlation)
        correlation_data_invalid = pd.DataFrame({
            'US_Stocks': [1.0, 1.0],
            'Bonds': [1.0, 1.0]
        }, index=asset_names)

        correlation_matrix_invalid = CorrelationMatrix(
            asset_names=asset_names,
            correlation_data=correlation_data_invalid
        )

        assert correlation_matrix_invalid.is_positive_definite() is False

    def test_get_cholesky_decomposition(self):
        """Test getting Cholesky decomposition."""
        asset_names = ['US_Stocks', 'Bonds']
        correlation_data = pd.DataFrame({
            'US_Stocks': [1.0, 0.3],
            'Bonds': [0.3, 1.0]
        }, index=asset_names)

        correlation_matrix = CorrelationMatrix(
            asset_names=asset_names,
            correlation_data=correlation_data
        )

        cholesky = correlation_matrix.get_cholesky_decomposition()
        assert cholesky.shape == (2, 2)
        assert np.allclose(cholesky @ cholesky.T, correlation_data.values)

    def test_get_cholesky_decomposition_invalid(self):
        """Test Cholesky decomposition with invalid matrix."""
        asset_names = ['US_Stocks', 'Bonds']
        correlation_data = pd.DataFrame({
            'US_Stocks': [1.0, 1.0],
            'Bonds': [1.0, 1.0]
        }, index=asset_names)

        correlation_matrix = CorrelationMatrix(
            asset_names=asset_names,
            correlation_data=correlation_data
        )

        with pytest.raises(MarketDataError, match="Correlation matrix is not positive definite"):
            correlation_matrix.get_cholesky_decomposition()

    def test_to_dict(self):
        """Test converting to dictionary."""
        asset_names = ['US_Stocks', 'Bonds']
        correlation_data = pd.DataFrame({
            'US_Stocks': [1.0, 0.3],
            'Bonds': [0.3, 1.0]
        }, index=asset_names)

        correlation_matrix = CorrelationMatrix(
            asset_names=asset_names,
            correlation_data=correlation_data
        )

        data_dict = correlation_matrix.to_dict()
        assert 'asset_names' in data_dict
        assert 'correlation_data' in data_dict


class TestRiskFreeRate:
    """Test RiskFreeRate class."""

    def test_risk_free_rate_creation(self):
        """Test creating risk-free rate with valid data."""
        risk_free_rate = RiskFreeRate(
            rate=0.004,  # 0.4% monthly
            start_date=date(2020, 1, 1),
            end_date=date(2023, 12, 31),
            frequency="monthly",
            source="Treasury"
        )

        assert risk_free_rate.rate == 0.004
        assert risk_free_rate.start_date == date(2020, 1, 1)
        assert risk_free_rate.end_date == date(2023, 12, 31)
        assert risk_free_rate.frequency == "monthly"
        assert risk_free_rate.source == "Treasury"

    def test_risk_free_rate_validation_invalid_rate(self):
        """Test validation with invalid rate."""
        with pytest.raises(MarketDataError, match="Invalid risk-free rate data"):
            RiskFreeRate(
                rate=-0.01,  # Negative rate
                start_date=date(2020, 1, 1),
                end_date=date(2023, 12, 31)
            )

    def test_risk_free_rate_validation_invalid_dates(self):
        """Test validation with invalid date range."""
        with pytest.raises(MarketDataError, match="Start date must be before end date"):
            RiskFreeRate(
                rate=0.004,
                start_date=date(2023, 12, 31),
                end_date=date(2020, 1, 1)
            )

    def test_get_annualized_rate(self):
        """Test calculating annualized rate."""
        risk_free_rate = RiskFreeRate(
            rate=0.004,  # 0.4% monthly
            start_date=date(2020, 1, 1),
            end_date=date(2023, 12, 31),
            frequency="monthly"
        )

        annualized_rate = risk_free_rate.get_annualized_rate()
        assert abs(annualized_rate - 0.048) < 1e-6  # 4.8% annualized

    def test_get_annualized_rate_daily(self):
        """Test calculating annualized rate for daily frequency."""
        risk_free_rate = RiskFreeRate(
            rate=0.0002,  # 0.02% daily
            start_date=date(2020, 1, 1),
            end_date=date(2023, 12, 31),
            frequency="daily"
        )

        annualized_rate = risk_free_rate.get_annualized_rate()
        assert abs(annualized_rate - 0.0504) < 1e-6  # 5.04% annualized

    def test_to_dict(self):
        """Test converting to dictionary."""
        risk_free_rate = RiskFreeRate(
            rate=0.004,
            start_date=date(2020, 1, 1),
            end_date=date(2023, 12, 31),
            frequency="monthly",
            source="Treasury"
        )

        data_dict = risk_free_rate.to_dict()
        assert data_dict['rate'] == 0.004
        assert data_dict['start_date'] == '2020-01-01'
        assert data_dict['end_date'] == '2023-12-31'
        assert data_dict['frequency'] == 'monthly'
        assert data_dict['source'] == 'Treasury'


class TestMarketDataLoader:
    """Test MarketDataLoader class."""

    def test_market_data_loader_creation(self):
        """Test creating market data loader."""
        loader = MarketDataLoader()
        assert loader.data_directory == Path("data/market")

        custom_loader = MarketDataLoader(Path("custom/data"))
        assert custom_loader.data_directory == Path("custom/data")

    def test_load_historical_returns_csv(self):
        """Test loading historical returns from CSV."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as f:
            f.write("Date,US_Stocks,Bonds\n")
            f.write("2020-01-01,0.01,0.005\n")
            f.write("2020-02-01,0.02,0.006\n")
            f.write("2020-03-01,0.03,0.007\n")
            temp_file = f.name

        try:
            loader = MarketDataLoader()
            historical_returns = loader.load_historical_returns(temp_file)

            assert len(historical_returns.asset_names) == 2
            assert 'US_Stocks' in historical_returns.asset_names
            assert 'Bonds' in historical_returns.asset_names
            assert len(historical_returns.returns_data) == 3
        finally:
            Path(temp_file).unlink()

    def test_load_historical_returns_nonexistent_file(self):
        """Test loading from nonexistent file."""
        loader = MarketDataLoader()

        with pytest.raises(MarketDataError, match="File not found"):
            loader.load_historical_returns("nonexistent.csv")

    def test_load_correlation_matrix_csv(self):
        """Test loading correlation matrix from CSV."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as f:
            f.write(",US_Stocks,Bonds\n")
            f.write("US_Stocks,1.0,0.3\n")
            f.write("Bonds,0.3,1.0\n")
            temp_file = f.name

        try:
            loader = MarketDataLoader()
            correlation_matrix = loader.load_correlation_matrix(temp_file)

            assert len(correlation_matrix.asset_names) == 2
            assert correlation_matrix.correlation_data.shape == (2, 2)
        finally:
            Path(temp_file).unlink()

    def test_load_risk_free_rate_json(self):
        """Test loading risk-free rate from JSON."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            json.dump({
                "rate": 0.004,
                "start_date": "2020-01-01",
                "end_date": "2023-12-31",
                "frequency": "monthly",
                "source": "Treasury"
            }, f)
            temp_file = f.name

        try:
            loader = MarketDataLoader()
            risk_free_rate = loader.load_risk_free_rate(temp_file)

            assert risk_free_rate.rate == 0.004
            assert risk_free_rate.start_date == date(2020, 1, 1)
            assert risk_free_rate.end_date == date(2023, 12, 31)
        finally:
            Path(temp_file).unlink()

    def test_save_historical_returns(self):
        """Test saving historical returns to CSV."""
        dates = pd.date_range('2020-01-01', '2023-12-31', freq='ME')
        asset_names = ['US_Stocks', 'Bonds']

        returns_data = pd.DataFrame({
            'US_Stocks': [0.01, 0.02, 0.03],
            'Bonds': [0.005, 0.006, 0.007]
        }, index=dates[:3])

        historical_returns = HistoricalReturns(
            asset_names=asset_names,
            returns_data=returns_data,
            start_date=dates[0].date(),
            end_date=dates[2].date()
        )

        with tempfile.NamedTemporaryFile(suffix='.csv', delete=False) as f:
            temp_file = f.name

        try:
            loader = MarketDataLoader()
            loader.save_historical_returns(historical_returns, temp_file)

            # Verify file was created and contains data
            assert Path(temp_file).exists()
            loaded_data = pd.read_csv(temp_file, index_col=0)
            assert len(loaded_data) == 3
            assert len(loaded_data.columns) == 2
        finally:
            Path(temp_file).unlink()

    def test_save_correlation_matrix(self):
        """Test saving correlation matrix to CSV."""
        asset_names = ['US_Stocks', 'Bonds']
        correlation_data = pd.DataFrame({
            'US_Stocks': [1.0, 0.3],
            'Bonds': [0.3, 1.0]
        }, index=asset_names)

        correlation_matrix = CorrelationMatrix(
            asset_names=asset_names,
            correlation_data=correlation_data
        )

        with tempfile.NamedTemporaryFile(suffix='.csv', delete=False) as f:
            temp_file = f.name

        try:
            loader = MarketDataLoader()
            loader.save_correlation_matrix(correlation_matrix, temp_file)

            # Verify file was created and contains data
            assert Path(temp_file).exists()
            loaded_data = pd.read_csv(temp_file, index_col=0)
            assert loaded_data.shape == (2, 2)
        finally:
            Path(temp_file).unlink()

    def test_save_risk_free_rate(self):
        """Test saving risk-free rate to JSON."""
        risk_free_rate = RiskFreeRate(
            rate=0.004,
            start_date=date(2020, 1, 1),
            end_date=date(2023, 12, 31),
            frequency="monthly",
            source="Treasury"
        )

        with tempfile.NamedTemporaryFile(suffix='.json', delete=False) as f:
            temp_file = f.name

        try:
            loader = MarketDataLoader()
            loader.save_risk_free_rate(risk_free_rate, temp_file)

            # Verify file was created and contains data
            assert Path(temp_file).exists()
            with open(temp_file, 'r') as f:
                data = json.load(f)
            assert data['rate'] == 0.004
            assert data['start_date'] == '2020-01-01'
        finally:
            Path(temp_file).unlink()

    def test_generate_sample_data(self):
        """Test generating sample market data."""
        loader = MarketDataLoader()
        historical_returns, correlation_matrix, risk_free_rate = loader.generate_sample_data()

        # Check historical returns
        assert len(historical_returns.asset_names) == 4
        assert len(historical_returns.returns_data) > 0

        # Check correlation matrix
        assert len(correlation_matrix.asset_names) == 4
        assert correlation_matrix.correlation_data.shape == (4, 4)

        # Check risk-free rate
        assert risk_free_rate.rate == 0.004
        assert risk_free_rate.frequency == "monthly"
        assert risk_free_rate.source == "Treasury"

    @patch('retirement_planner.data.market_data.yf.download')
    def test_download_historical_returns_from_yahoo(self, mock_download):
        """Test downloading historical returns from Yahoo Finance."""
        # Mock the yfinance download response
        mock_data = pd.DataFrame({
            'AAPL': [100, 105, 110, 108, 112],
            'MSFT': [200, 210, 215, 212, 220]
        }, index=pd.date_range('2023-01-01', periods=5, freq='D'))

        mock_download.return_value = MagicMock()
        mock_download.return_value.__getitem__.return_value = mock_data

        loader = MarketDataLoader()

        # Test download without saving
        result = loader.download_historical_returns_from_yahoo(
            tickers=['AAPL', 'MSFT'],
            start='2023-01-01',
            end='2023-01-05'
        )

        # Verify yfinance was called correctly
        mock_download.assert_called_once_with(
            ['AAPL', 'MSFT'],
            start='2023-01-01',
            end='2023-01-05',
            auto_adjust=True
        )

        # Verify result is a DataFrame
        assert isinstance(result, pd.DataFrame)
        assert list(result.columns) == ['AAPL', 'MSFT']

    @patch('retirement_planner.data.market_data.yf.download')
    def test_download_historical_returns_from_yahoo_with_save(self, mock_download):
        """Test downloading historical returns and saving to file."""
        # Mock the yfinance download response
        mock_data = pd.DataFrame({
            'AAPL': [100, 105, 110, 108, 112],
            'MSFT': [200, 210, 215, 212, 220]
        }, index=pd.date_range('2023-01-01', periods=5, freq='D'))

        mock_download.return_value = MagicMock()
        mock_download.return_value.__getitem__.return_value = mock_data

        loader = MarketDataLoader()

        with tempfile.NamedTemporaryFile(suffix='.csv', delete=False) as f:
            temp_file = f.name

        try:
            result = loader.download_historical_returns_from_yahoo(
                tickers=['AAPL', 'MSFT'],
                start='2023-01-01',
                end='2023-01-05',
                file_path=temp_file
            )

            # Verify file was created
            assert Path(temp_file).exists()

            # Verify file contains data
            saved_data = pd.read_csv(temp_file, index_col=0, parse_dates=True)
            assert len(saved_data) > 0

        finally:
            Path(temp_file).unlink()

    @patch('retirement_planner.data.market_data.requests.get')
    def test_download_risk_free_rate_from_fred(self, mock_get):
        """Test downloading risk-free rate from FRED."""
        # Mock the HTTP response
        mock_response = MagicMock()
        mock_response.raise_for_status.return_value = None
        mock_response.json.return_value = {
            'observations': [
                {'date': '2024-01-01', 'value': '4.5'},
                {'date': '2024-01-02', 'value': '4.6'},
                {'date': '2024-01-03', 'value': '.'}  # Missing value
            ]
        }
        mock_get.return_value = mock_response

        loader = MarketDataLoader()
        result = loader.download_risk_free_rate_from_fred('DGS10')

        assert isinstance(result, pd.DataFrame)
        assert len(result) == 3
        assert result.index[0] == pd.Timestamp('2024-01-01')
        assert result.iloc[0, 0] == 4.5
        assert pd.isna(result.iloc[2, 0])  # Missing value should be NaN

    @patch('retirement_planner.data.market_data.requests.get')
    def test_download_risk_free_rate_from_fred_with_save(self, mock_get):
        """Test downloading risk-free rate and saving to file."""
        # Mock the HTTP response
        mock_response = MagicMock()
        mock_response.raise_for_status.return_value = None
        mock_response.json.return_value = {
            'observations': [
                {'date': '2024-01-01', 'value': '4.5'},
                {'date': '2024-01-02', 'value': '4.6'}
            ]
        }
        mock_get.return_value = mock_response

        loader = MarketDataLoader()

        with tempfile.NamedTemporaryFile(suffix='.csv', delete=False) as f:
            temp_file = f.name

        try:
            result = loader.download_risk_free_rate_from_fred('DGS10', file_path=temp_file)
            assert isinstance(result, pd.DataFrame)
            assert Path(temp_file).exists()
        finally:
            Path(temp_file).unlink(missing_ok=True)

    @patch('retirement_planner.data.market_data.requests.get')
    def test_download_risk_free_rate_from_fred_default_end_date(self, mock_get):
        """Test downloading risk-free rate with default end date."""
        # Mock the HTTP response
        mock_response = MagicMock()
        mock_response.raise_for_status.return_value = None
        mock_response.json.return_value = {
            'observations': [
                {'date': '2024-01-01', 'value': '4.5'}
            ]
        }
        mock_get.return_value = mock_response

        loader = MarketDataLoader()
        result = loader.download_risk_free_rate_from_fred('DGS10', start='2024-01-01')

        assert isinstance(result, pd.DataFrame)
        assert len(result) == 1