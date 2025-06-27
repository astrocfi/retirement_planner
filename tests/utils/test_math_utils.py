"""
Unit tests for math_utils module.
"""

import pytest
import math
from datetime import date
from retirement_planner.utils.math_utils import (
    MathUtils, StatisticalUtils, RiskMetrics, PortfolioMath, FinancialMetrics
)
from retirement_planner.core.exceptions import ValidationError


class TestMathUtils:
    """Test mathematical utilities."""

    def test_calculate_compound_interest(self):
        """Test compound interest calculation."""
        # Basic compound interest
        result = MathUtils.calculate_compound_interest(1000, 0.05, 10)
        expected = 1000 * (1 + 0.05) ** 10
        assert abs(result - expected) < 1e-6

        # Monthly compounding
        result = MathUtils.calculate_compound_interest(1000, 0.05, 10, 12)
        expected = 1000 * (1 + 0.05/12) ** (12 * 10)
        assert abs(result - expected) < 1e-6

    def test_calculate_compound_interest_validation(self):
        """Test compound interest validation."""
        with pytest.raises(ValidationError):
            MathUtils.calculate_compound_interest(-1000, 0.05, 10)

        with pytest.raises(ValidationError):
            MathUtils.calculate_compound_interest(1000, -0.05, 10)

        with pytest.raises(ValidationError):
            MathUtils.calculate_compound_interest(1000, 0.05, -10)

        with pytest.raises(ValidationError):
            MathUtils.calculate_compound_interest(1000, 0.05, 10, 0)

    def test_calculate_present_value(self):
        """Test present value calculation."""
        result = MathUtils.calculate_present_value(1000, 0.05, 10)
        expected = 1000 / (1 + 0.05) ** 10
        assert abs(result - expected) < 1e-6

    def test_calculate_present_value_validation(self):
        """Test present value validation."""
        with pytest.raises(ValidationError):
            MathUtils.calculate_present_value(-1000, 0.05, 10)

        with pytest.raises(ValidationError):
            MathUtils.calculate_present_value(1000, -0.05, 10)

    def test_calculate_future_value(self):
        """Test future value calculation."""
        result = MathUtils.calculate_future_value(1000, 0.05, 10)
        expected = 1000 * (1 + 0.05) ** 10
        assert abs(result - expected) < 1e-6

    def test_calculate_annuity_payment(self):
        """Test annuity payment calculation."""
        result = MathUtils.calculate_annuity_payment(100000, 0.05, 20)
        # Verify it's a reasonable payment amount
        assert result > 0
        assert result < 100000

        # Zero rate case
        result = MathUtils.calculate_annuity_payment(100000, 0, 20)
        assert result == 5000  # 100000 / 20

    def test_calculate_annuity_payment_validation(self):
        """Test annuity payment validation."""
        with pytest.raises(ValidationError):
            MathUtils.calculate_annuity_payment(100000, 0.05, 0)

    def test_adjust_for_inflation(self):
        """Test inflation adjustment."""
        result = MathUtils.adjust_for_inflation(1000, 0.02, 10)
        expected = 1000 * (1 + 0.02) ** 10
        assert abs(result - expected) < 1e-6

    def test_calculate_real_return(self):
        """Test real return calculation."""
        result = MathUtils.calculate_real_return(0.08, 0.02)
        expected = (1 + 0.08) / (1 + 0.02) - 1
        assert abs(result - expected) < 1e-6

        # Negative nominal return
        result = MathUtils.calculate_real_return(-0.05, 0.02)
        expected = (1 - 0.05) / (1 + 0.02) - 1
        assert abs(result - expected) < 1e-6

    def test_calculate_real_return_validation(self):
        """Test real return validation."""
        with pytest.raises(ValidationError):
            MathUtils.calculate_real_return(-1.5, 0.02)  # Below -1

    def test_round_to_currency(self):
        """Test currency rounding."""
        assert MathUtils.round_to_currency(123.456) == 123.46
        assert MathUtils.round_to_currency(123.456, 3) == 123.456

    def test_round_to_percentage(self):
        """Test percentage rounding."""
        assert MathUtils.round_to_percentage(0.123456) == 0.1235
        assert MathUtils.round_to_percentage(0.123456, 6) == 0.123456

    def test_is_valid_probability(self):
        """Test probability validation."""
        assert MathUtils.is_valid_probability(0.5) is True
        assert MathUtils.is_valid_probability(0) is True
        assert MathUtils.is_valid_probability(1) is True
        assert MathUtils.is_valid_probability(-0.1) is False
        assert MathUtils.is_valid_probability(1.1) is False

    def test_is_valid_percentage(self):
        """Test percentage validation."""
        assert MathUtils.is_valid_percentage(50) is True
        assert MathUtils.is_valid_percentage(0) is True
        assert MathUtils.is_valid_percentage(100) is True
        assert MathUtils.is_valid_percentage(-10) is False
        assert MathUtils.is_valid_percentage(110) is False

    def test_is_within_tolerance(self):
        """Test tolerance comparison."""
        assert MathUtils.is_within_tolerance(1.0, 1.0) is True
        assert MathUtils.is_within_tolerance(1.0, 1.000001) is True
        assert MathUtils.is_within_tolerance(1.0, 1.1) is False
        assert MathUtils.is_within_tolerance(1.0, 1.1, 0.2) is True


class TestStatisticalUtils:
    """Test statistical utilities."""

    def test_calculate_mean(self):
        """Test mean calculation."""
        values = [1, 2, 3, 4, 5]
        assert StatisticalUtils.calculate_mean(values) == 3.0

        values = [1.5, 2.5, 3.5]
        assert StatisticalUtils.calculate_mean(values) == 2.5

    def test_calculate_mean_empty(self):
        """Test mean calculation with empty list."""
        with pytest.raises(ValidationError):
            StatisticalUtils.calculate_mean([])

    def test_calculate_median(self):
        """Test median calculation."""
        # Odd number of elements
        values = [1, 3, 5, 7, 9]
        assert StatisticalUtils.calculate_median(values) == 5

        # Even number of elements
        values = [1, 3, 5, 7]
        assert StatisticalUtils.calculate_median(values) == 4.0

        # Single element
        values = [5]
        assert StatisticalUtils.calculate_median(values) == 5

    def test_calculate_median_empty(self):
        """Test median calculation with empty list."""
        with pytest.raises(ValidationError):
            StatisticalUtils.calculate_median([])

    def test_calculate_std_deviation(self):
        """Test standard deviation calculation."""
        values = [1, 2, 3, 4, 5]
        mean = 3.0
        variance = sum((x - mean) ** 2 for x in values) / 4  # n-1
        expected = math.sqrt(variance)
        result = StatisticalUtils.calculate_std_deviation(values)
        assert abs(result - expected) < 1e-6

    def test_calculate_std_deviation_insufficient_data(self):
        """Test standard deviation with insufficient data."""
        with pytest.raises(ValidationError):
            StatisticalUtils.calculate_std_deviation([1])

    def test_calculate_variance(self):
        """Test variance calculation."""
        values = [1, 2, 3, 4, 5]
        mean = 3.0
        expected = sum((x - mean) ** 2 for x in values) / 4  # n-1
        result = StatisticalUtils.calculate_variance(values)
        assert abs(result - expected) < 1e-6

    def test_calculate_percentile(self):
        """Test percentile calculation."""
        values = [1, 2, 3, 4, 5, 6, 7, 8, 9, 10]

        # 50th percentile (median)
        assert StatisticalUtils.calculate_percentile(values, 50) == 5.5

        # 25th percentile
        assert StatisticalUtils.calculate_percentile(values, 25) == 3.25

        # 75th percentile
        assert StatisticalUtils.calculate_percentile(values, 75) == 7.75

    def test_calculate_percentile_validation(self):
        """Test percentile validation."""
        with pytest.raises(ValidationError):
            StatisticalUtils.calculate_percentile([], 50)

        with pytest.raises(ValidationError):
            StatisticalUtils.calculate_percentile([1, 2, 3], -10)

        with pytest.raises(ValidationError):
            StatisticalUtils.calculate_percentile([1, 2, 3], 110)

    def test_calculate_correlation(self):
        """Test correlation calculation."""
        x_values = [1, 2, 3, 4, 5]
        y_values = [2, 4, 6, 8, 10]  # Perfect positive correlation

        result = StatisticalUtils.calculate_correlation(x_values, y_values)
        assert abs(result - 1.0) < 1e-6

        # Perfect negative correlation
        y_values = [10, 8, 6, 4, 2]
        result = StatisticalUtils.calculate_correlation(x_values, y_values)
        assert abs(result - (-1.0)) < 1e-6

    def test_calculate_correlation_validation(self):
        """Test correlation validation."""
        with pytest.raises(ValidationError):
            StatisticalUtils.calculate_correlation([1, 2], [1, 2, 3])

        with pytest.raises(ValidationError):
            StatisticalUtils.calculate_correlation([1], [1])

    def test_calculate_skewness(self):
        """Test skewness calculation."""
        values = [1, 2, 3, 4, 5]
        result = StatisticalUtils.calculate_skewness(values)
        # Symmetric data should have skewness close to 0
        assert abs(result) < 0.1

    def test_calculate_skewness_insufficient_data(self):
        """Test skewness with insufficient data."""
        with pytest.raises(ValidationError):
            StatisticalUtils.calculate_skewness([1, 2])

    def test_calculate_kurtosis(self):
        """Test kurtosis calculation."""
        values = [1, 2, 3, 4, 5]
        result = StatisticalUtils.calculate_kurtosis(values)
        # Uniform distribution of 5 values has excess kurtosis about -1.2
        assert -2 < result < 0

    def test_calculate_kurtosis_insufficient_data(self):
        """Test kurtosis with insufficient data."""
        with pytest.raises(ValidationError):
            StatisticalUtils.calculate_kurtosis([1, 2, 3])


class TestRiskMetrics:
    """Test risk metrics."""

    def test_calculate_var(self):
        """Test Value at Risk calculation."""
        returns = [-0.05, -0.03, -0.01, 0.02, 0.04, 0.06, 0.08]
        var_95 = RiskMetrics.calculate_var(returns, 0.05)
        assert var_95 <= -0.01  # Should be negative (loss)

    def test_calculate_var_validation(self):
        """Test VaR validation."""
        with pytest.raises(ValidationError):
            RiskMetrics.calculate_var([], 0.05)

        with pytest.raises(ValidationError):
            RiskMetrics.calculate_var([0.01, 0.02], 1.5)

    def test_calculate_cvar(self):
        """Test Conditional Value at Risk calculation."""
        returns = [-0.05, -0.03, -0.01, 0.02, 0.04, 0.06, 0.08]
        cvar = RiskMetrics.calculate_cvar(returns, 0.05)
        var = RiskMetrics.calculate_var(returns, 0.05)
        assert cvar <= var  # CVaR should be <= VaR

    def test_calculate_max_drawdown(self):
        """Test maximum drawdown calculation."""
        portfolio_values = [100, 110, 105, 120, 115, 130, 125]
        max_dd = RiskMetrics.calculate_max_drawdown(portfolio_values)
        assert max_dd < 0  # Should be negative
        assert max_dd >= -0.15  # Should be reasonable

    def test_calculate_sharpe_ratio(self):
        """Test Sharpe ratio calculation."""
        returns = [0.01, 0.02, 0.03, 0.04, 0.05]
        sharpe = RiskMetrics.calculate_sharpe_ratio(returns, 0.01)
        assert sharpe > 0  # Should be positive for positive excess returns

    def test_calculate_sortino_ratio(self):
        """Test Sortino ratio calculation."""
        returns = [0.01, 0.02, -0.01, 0.03, 0.04]
        sortino = RiskMetrics.calculate_sortino_ratio(returns, 0.01)
        assert sortino > 0  # Should be positive for positive excess returns

    def test_calculate_calmar_ratio(self):
        """Test Calmar ratio calculation."""
        returns = [0.01, 0.02, 0.03, 0.04, 0.05]
        portfolio_values = [100, 101, 103, 106, 110, 115]
        calmar = RiskMetrics.calculate_calmar_ratio(returns, portfolio_values)
        # Calmar ratio can be zero if max_drawdown is zero
        assert calmar >= 0


class TestPortfolioMath:
    """Test portfolio mathematics."""

    def test_calculate_portfolio_return(self):
        """Test portfolio return calculation."""
        weights = [0.6, 0.4]
        returns = [0.08, 0.12]
        portfolio_return = PortfolioMath.calculate_portfolio_return(weights, returns)
        expected = 0.6 * 0.08 + 0.4 * 0.12
        assert abs(portfolio_return - expected) < 1e-6

    def test_calculate_portfolio_return_validation(self):
        """Test portfolio return validation."""
        with pytest.raises(ValidationError):
            PortfolioMath.calculate_portfolio_return([0.6], [0.08, 0.12])

        with pytest.raises(ValidationError):
            PortfolioMath.calculate_portfolio_return([0.6, 0.3], [0.08, 0.12])

    def test_calculate_portfolio_volatility(self):
        """Test portfolio volatility calculation."""
        weights = [0.6, 0.4]
        covariance_matrix = [[0.04, 0.01], [0.01, 0.09]]
        volatility = PortfolioMath.calculate_portfolio_volatility(weights, covariance_matrix)
        assert volatility > 0

    def test_calculate_rebalancing_trades(self):
        """Test rebalancing trades calculation."""
        current_weights = [0.5, 0.5]
        target_weights = [0.6, 0.4]
        portfolio_value = 100000
        trades = PortfolioMath.calculate_rebalancing_trades(current_weights, target_weights, portfolio_value)

        assert len(trades) == 2
        assert abs(trades[0] - 10000) < 1e-6  # Buy 10% of portfolio
        assert abs(trades[1] + 10000) < 1e-6  # Sell 10% of portfolio
        assert abs(sum(trades)) < 1e-6  # Net zero

    def test_calculate_geometric_mean(self):
        """Test geometric mean calculation."""
        returns = [0.1, 0.2, -0.1, 0.15]
        geometric_mean = PortfolioMath.calculate_geometric_mean(returns)

        # Manual calculation
        growth_factors = [1.1, 1.2, 0.9, 1.15]
        product = 1
        for factor in growth_factors:
            product *= factor
        expected = product ** (1/4) - 1

        assert abs(geometric_mean - expected) < 1e-6

    def test_calculate_geometric_mean_empty(self):
        """Test geometric mean with empty list."""
        with pytest.raises(ValidationError):
            PortfolioMath.calculate_geometric_mean([])


class TestFinancialMetrics:
    """Test FinancialMetrics dataclass."""

    def test_financial_metrics_creation(self):
        """Test FinancialMetrics creation."""
        metrics = FinancialMetrics(
            present_value=1000,
            future_value=1500,
            rate=0.05,
            periods=10
        )

        assert metrics.present_value == 1000
        assert metrics.future_value == 1500
        assert metrics.rate == 0.05
        assert metrics.periods == 10
        assert metrics.payment is None
        assert metrics.metadata is None

    def test_financial_metrics_with_optional_fields(self):
        """Test FinancialMetrics with optional fields."""
        metadata = {"source": "test"}
        metrics = FinancialMetrics(
            present_value=1000,
            future_value=1500,
            rate=0.05,
            periods=10,
            payment=100,
            metadata=metadata
        )

        assert metrics.payment == 100
        assert metrics.metadata == metadata