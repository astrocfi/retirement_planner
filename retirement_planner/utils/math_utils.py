"""
Mathematical utilities for retirement planning.

This module provides mathematical utilities, statistical functions, risk metrics,
and portfolio mathematics for financial calculations.
"""

import math
import numpy as np
from typing import List, Dict, Optional, Tuple, Union
from dataclasses import dataclass
from datetime import datetime, date
from retirement_planner.core.validation import Validator, RangeRule, RequiredRule
from retirement_planner.core.exceptions import ValidationError


@dataclass(frozen=True)
class FinancialMetrics:
    """Container for financial calculation results."""
    present_value: float
    future_value: float
    rate: float
    periods: int
    payment: Optional[float] = None
    metadata: Dict[str, any] = None


class MathUtils:
    """Core mathematical utilities for financial calculations."""

    @staticmethod
    def calculate_compound_interest(principal: float, rate: float, years: int,
                                  compounding_frequency: int = 1) -> float:
        """
        Calculate compound interest.

        Args:
            principal: Initial amount
            rate: Annual interest rate (as decimal)
            years: Number of years
            compounding_frequency: Number of times interest is compounded per year

        Returns:
            Final amount after compound interest
        """
        validator = Validator()
        validator.add_field_validator('principal').add_rule(RangeRule('principal', min_value=0))
        validator.add_field_validator('rate').add_rule(RangeRule('rate', min_value=0))
        validator.add_field_validator('years').add_rule(RangeRule('years', min_value=0))
        validator.add_field_validator('compounding_frequency').add_rule(RangeRule('compounding_frequency', min_value=1))

        result = validator.validate({
            'principal': principal,
            'rate': rate,
            'years': years,
            'compounding_frequency': compounding_frequency
        })

        if not result.is_valid:
            raise ValidationError(f"Compound interest validation failed: {result.errors}")

        return principal * (1 + rate / compounding_frequency) ** (compounding_frequency * years)

    @staticmethod
    def calculate_present_value(future_value: float, rate: float, years: int) -> float:
        """
        Calculate present value of a future amount.

        Args:
            future_value: Future amount
            rate: Annual discount rate (as decimal)
            years: Number of years

        Returns:
            Present value
        """
        validator = Validator()
        validator.add_field_validator('future_value').add_rule(RangeRule('future_value', min_value=0))
        validator.add_field_validator('rate').add_rule(RangeRule('rate', min_value=0))
        validator.add_field_validator('years').add_rule(RangeRule('years', min_value=0))

        result = validator.validate({
            'future_value': future_value,
            'rate': rate,
            'years': years
        })

        if not result.is_valid:
            raise ValidationError(f"Present value validation failed: {result.errors}")

        return future_value / (1 + rate) ** years

    @staticmethod
    def calculate_future_value(present_value: float, rate: float, years: int) -> float:
        """
        Calculate future value of a present amount.

        Args:
            present_value: Present amount
            rate: Annual interest rate (as decimal)
            years: Number of years

        Returns:
            Future value
        """
        validator = Validator()
        validator.add_field_validator('present_value').add_rule(RangeRule('present_value', min_value=0))
        validator.add_field_validator('rate').add_rule(RangeRule('rate', min_value=0))
        validator.add_field_validator('years').add_rule(RangeRule('years', min_value=0))

        result = validator.validate({
            'present_value': present_value,
            'rate': rate,
            'years': years
        })

        if not result.is_valid:
            raise ValidationError(f"Future value validation failed: {result.errors}")

        return present_value * (1 + rate) ** years

    @staticmethod
    def calculate_annuity_payment(present_value: float, rate: float, years: int) -> float:
        """
        Calculate annuity payment for a given present value.

        Args:
            present_value: Present value of annuity
            rate: Annual interest rate (as decimal)
            years: Number of years

        Returns:
            Annual payment amount
        """
        validator = Validator()
        validator.add_field_validator('present_value').add_rule(RangeRule('present_value', min_value=0))
        validator.add_field_validator('rate').add_rule(RangeRule('rate', min_value=0))
        validator.add_field_validator('years').add_rule(RangeRule('years', min_value=1))

        result = validator.validate({
            'present_value': present_value,
            'rate': rate,
            'years': years
        })

        if not result.is_valid:
            raise ValidationError(f"Annuity payment validation failed: {result.errors}")

        if rate == 0:
            return present_value / years

        return present_value * rate * (1 + rate) ** years / ((1 + rate) ** years - 1)

    @staticmethod
    def adjust_for_inflation(amount: float, inflation_rate: float, years: int) -> float:
        """
        Adjust amount for inflation over time.

        Args:
            amount: Original amount
            inflation_rate: Annual inflation rate (as decimal)
            years: Number of years

        Returns:
            Inflation-adjusted amount
        """
        validator = Validator()
        validator.add_field_validator('amount').add_rule(RangeRule('amount', min_value=0))
        validator.add_field_validator('inflation_rate').add_rule(RangeRule('inflation_rate', min_value=0))
        validator.add_field_validator('years').add_rule(RangeRule('years', min_value=0))

        result = validator.validate({
            'amount': amount,
            'inflation_rate': inflation_rate,
            'years': years
        })

        if not result.is_valid:
            raise ValidationError(f"Inflation adjustment validation failed: {result.errors}")

        return amount * (1 + inflation_rate) ** years

    @staticmethod
    def calculate_real_return(nominal_return: float, inflation_rate: float) -> float:
        """
        Calculate real return (nominal return minus inflation).

        Args:
            nominal_return: Nominal return rate (as decimal)
            inflation_rate: Inflation rate (as decimal)

        Returns:
            Real return rate (as decimal)
        """
        validator = Validator()
        validator.add_field_validator('nominal_return').add_rule(RangeRule('nominal_return', min_value=-1))
        validator.add_field_validator('inflation_rate').add_rule(RangeRule('inflation_rate', min_value=0))

        result = validator.validate({
            'nominal_return': nominal_return,
            'inflation_rate': inflation_rate
        })

        if not result.is_valid:
            raise ValidationError(f"Real return validation failed: {result.errors}")

        return (1 + nominal_return) / (1 + inflation_rate) - 1

    @staticmethod
    def round_to_currency(amount: float, decimal_places: int = 2) -> float:
        """
        Round amount to currency precision.

        Args:
            amount: Amount to round
            decimal_places: Number of decimal places

        Returns:
            Rounded amount
        """
        return round(amount, decimal_places)

    @staticmethod
    def round_to_percentage(value: float, decimal_places: int = 4) -> float:
        """
        Round percentage value to specified precision.

        Args:
            value: Percentage value (as decimal)
            decimal_places: Number of decimal places

        Returns:
            Rounded percentage
        """
        return round(value, decimal_places)

    @staticmethod
    def is_valid_probability(value: float) -> bool:
        """
        Check if value is a valid probability (0 to 1).

        Args:
            value: Value to check

        Returns:
            True if valid probability
        """
        return 0 <= value <= 1

    @staticmethod
    def is_valid_percentage(value: float) -> bool:
        """
        Check if value is a valid percentage (0 to 100).

        Args:
            value: Value to check

        Returns:
            True if valid percentage
        """
        return 0 <= value <= 100

    @staticmethod
    def is_within_tolerance(value1: float, value2: float, tolerance: float = 1e-6) -> bool:
        """
        Check if two values are within specified tolerance.

        Args:
            value1: First value
            value2: Second value
            tolerance: Tolerance for comparison

        Returns:
            True if values are within tolerance
        """
        return abs(value1 - value2) <= tolerance


class StatisticalUtils:
    """Statistical analysis utilities."""

    @staticmethod
    def calculate_mean(values: List[float]) -> float:
        """
        Calculate arithmetic mean of values.

        Args:
            values: List of numeric values

        Returns:
            Arithmetic mean
        """
        if not values:
            raise ValidationError("Cannot calculate mean of empty list")

        return sum(values) / len(values)

    @staticmethod
    def calculate_median(values: List[float]) -> float:
        """
        Calculate median of values.

        Args:
            values: List of numeric values

        Returns:
            Median value
        """
        if not values:
            raise ValidationError("Cannot calculate median of empty list")

        sorted_values = sorted(values)
        n = len(sorted_values)

        if n % 2 == 0:
            return (sorted_values[n//2 - 1] + sorted_values[n//2]) / 2
        else:
            return sorted_values[n//2]

    @staticmethod
    def calculate_std_deviation(values: List[float]) -> float:
        """
        Calculate standard deviation of values.

        Args:
            values: List of numeric values

        Returns:
            Standard deviation
        """
        if len(values) < 2:
            raise ValidationError("Need at least 2 values for standard deviation")

        mean = StatisticalUtils.calculate_mean(values)
        variance = sum((x - mean) ** 2 for x in values) / (len(values) - 1)
        return math.sqrt(variance)

    @staticmethod
    def calculate_variance(values: List[float]) -> float:
        """
        Calculate variance of values.

        Args:
            values: List of numeric values

        Returns:
            Variance
        """
        if len(values) < 2:
            raise ValidationError("Need at least 2 values for variance")

        mean = StatisticalUtils.calculate_mean(values)
        return sum((x - mean) ** 2 for x in values) / (len(values) - 1)

    @staticmethod
    def calculate_percentile(values: List[float], percentile: float) -> float:
        """
        Calculate specified percentile of values.

        Args:
            values: List of numeric values
            percentile: Percentile to calculate (0-100)

        Returns:
            Percentile value
        """
        if not values:
            raise ValidationError("Cannot calculate percentile of empty list")

        if not 0 <= percentile <= 100:
            raise ValidationError("Percentile must be between 0 and 100")

        sorted_values = sorted(values)
        n = len(sorted_values)
        k = (n - 1) * percentile / 100
        f = math.floor(k)
        c = math.ceil(k)

        if f == c:
            return sorted_values[int(k)]

        d0 = sorted_values[int(f)] * (c - k)
        d1 = sorted_values[int(c)] * (k - f)
        return d0 + d1

    @staticmethod
    def calculate_correlation(x_values: List[float], y_values: List[float]) -> float:
        """
        Calculate correlation coefficient between two sets of values.

        Args:
            x_values: First set of values
            y_values: Second set of values

        Returns:
            Correlation coefficient (-1 to 1)
        """
        if len(x_values) != len(y_values):
            raise ValidationError("X and Y values must have same length")

        if len(x_values) < 2:
            raise ValidationError("Need at least 2 values for correlation")

        x_mean = StatisticalUtils.calculate_mean(x_values)
        y_mean = StatisticalUtils.calculate_mean(y_values)

        numerator = sum((x - x_mean) * (y - y_mean) for x, y in zip(x_values, y_values))
        x_variance = sum((x - x_mean) ** 2 for x in x_values)
        y_variance = sum((y - y_mean) ** 2 for y in y_values)

        if x_variance == 0 or y_variance == 0:
            return 0

        return numerator / math.sqrt(x_variance * y_variance)

    @staticmethod
    def calculate_skewness(values: List[float]) -> float:
        """
        Calculate skewness of values.

        Args:
            values: List of numeric values

        Returns:
            Skewness coefficient
        """
        if len(values) < 3:
            raise ValidationError("Need at least 3 values for skewness")

        mean = StatisticalUtils.calculate_mean(values)
        std_dev = StatisticalUtils.calculate_std_deviation(values)

        if std_dev == 0:
            return 0

        n = len(values)
        skewness = sum(((x - mean) / std_dev) ** 3 for x in values) / n
        return skewness * math.sqrt(n * (n - 1)) / (n - 2)

    @staticmethod
    def calculate_kurtosis(values: List[float]) -> float:
        """
        Calculate kurtosis of values.

        Args:
            values: List of numeric values

        Returns:
            Kurtosis coefficient
        """
        if len(values) < 4:
            raise ValidationError("Need at least 4 values for kurtosis")

        mean = StatisticalUtils.calculate_mean(values)
        std_dev = StatisticalUtils.calculate_std_deviation(values)

        if std_dev == 0:
            return 0

        n = len(values)
        kurtosis = sum(((x - mean) / std_dev) ** 4 for x in values) / n
        return kurtosis - 3  # Excess kurtosis


class RiskMetrics:
    """Risk measurement and analysis utilities."""

    @staticmethod
    def calculate_var(returns: List[float], confidence_level: float = 0.05) -> float:
        """
        Calculate Value at Risk (VaR).

        Args:
            returns: List of return values
            confidence_level: Confidence level (e.g., 0.05 for 95% VaR)

        Returns:
            Value at Risk
        """
        if not returns:
            raise ValidationError("Cannot calculate VaR with empty returns")

        if not 0 < confidence_level < 1:
            raise ValidationError("Confidence level must be between 0 and 1")

        return StatisticalUtils.calculate_percentile(returns, confidence_level * 100)

    @staticmethod
    def calculate_cvar(returns: List[float], confidence_level: float = 0.05) -> float:
        """
        Calculate Conditional Value at Risk (CVaR).

        Args:
            returns: List of return values
            confidence_level: Confidence level

        Returns:
            Conditional Value at Risk
        """
        if not returns:
            raise ValidationError("Cannot calculate CVaR with empty returns")

        var = RiskMetrics.calculate_var(returns, confidence_level)
        tail_returns = [r for r in returns if r <= var]

        if not tail_returns:
            return var

        return StatisticalUtils.calculate_mean(tail_returns)

    @staticmethod
    def calculate_max_drawdown(portfolio_values: List[float]) -> float:
        """
        Calculate maximum drawdown from peak.

        Args:
            portfolio_values: List of portfolio values over time

        Returns:
            Maximum drawdown as negative percentage
        """
        if not portfolio_values:
            raise ValidationError("Cannot calculate drawdown with empty values")

        peak = portfolio_values[0]
        max_drawdown = 0

        for value in portfolio_values:
            if value > peak:
                peak = value
            drawdown = (value - peak) / peak
            max_drawdown = min(max_drawdown, drawdown)

        return max_drawdown

    @staticmethod
    def calculate_sharpe_ratio(returns: List[float], risk_free_rate: float = 0.0) -> float:
        """
        Calculate Sharpe ratio.

        Args:
            returns: List of return values
            risk_free_rate: Risk-free rate (as decimal)

        Returns:
            Sharpe ratio
        """
        if not returns:
            raise ValidationError("Cannot calculate Sharpe ratio with empty returns")

        mean_return = StatisticalUtils.calculate_mean(returns)
        std_dev = StatisticalUtils.calculate_std_deviation(returns)

        if std_dev == 0:
            return 0

        return (mean_return - risk_free_rate) / std_dev

    @staticmethod
    def calculate_sortino_ratio(returns: List[float], risk_free_rate: float = 0.0) -> float:
        """
        Calculate Sortino ratio.

        Args:
            returns: List of return values
            risk_free_rate: Risk-free rate (as decimal)

        Returns:
            Sortino ratio
        """
        if not returns:
            raise ValidationError("Cannot calculate Sortino ratio with empty returns")

        mean_return = StatisticalUtils.calculate_mean(returns)
        negative_returns = [r for r in returns if r < 0]

        if not negative_returns:
            return float('inf') if mean_return > risk_free_rate else 0

        downside_deviation = math.sqrt(sum(r ** 2 for r in negative_returns) / len(returns))

        if downside_deviation == 0:
            return 0

        return (mean_return - risk_free_rate) / downside_deviation

    @staticmethod
    def calculate_calmar_ratio(returns: List[float], portfolio_values: List[float]) -> float:
        """
        Calculate Calmar ratio.

        Args:
            returns: List of return values
            portfolio_values: List of portfolio values over time

        Returns:
            Calmar ratio
        """
        if not returns or not portfolio_values:
            raise ValidationError("Cannot calculate Calmar ratio with empty data")

        mean_return = StatisticalUtils.calculate_mean(returns)
        max_drawdown = abs(RiskMetrics.calculate_max_drawdown(portfolio_values))

        if max_drawdown == 0:
            return 0

        return mean_return / max_drawdown


class PortfolioMath:
    """Portfolio-specific mathematical operations."""

    @staticmethod
    def calculate_portfolio_return(weights: List[float], returns: List[float]) -> float:
        """
        Calculate weighted portfolio return.

        Args:
            weights: Asset weights (must sum to 1)
            returns: Asset returns

        Returns:
            Portfolio return
        """
        if len(weights) != len(returns):
            raise ValidationError("Weights and returns must have same length")

        if not MathUtils.is_within_tolerance(sum(weights), 1.0, 1e-6):
            raise ValidationError("Weights must sum to 1")

        return sum(w * r for w, r in zip(weights, returns))

    @staticmethod
    def calculate_portfolio_volatility(weights: List[float],
                                     covariance_matrix: List[List[float]]) -> float:
        """
        Calculate portfolio volatility using covariance matrix.

        Args:
            weights: Asset weights
            covariance_matrix: Covariance matrix

        Returns:
            Portfolio volatility
        """
        if len(weights) != len(covariance_matrix):
            raise ValidationError("Weights and covariance matrix dimensions must match")

        if not MathUtils.is_within_tolerance(sum(weights), 1.0, 1e-6):
            raise ValidationError("Weights must sum to 1")

        # Convert to numpy for matrix operations
        w = np.array(weights)
        cov = np.array(covariance_matrix)

        portfolio_variance = w.T @ cov @ w
        return math.sqrt(portfolio_variance)

    @staticmethod
    def calculate_rebalancing_trades(current_weights: List[float],
                                   target_weights: List[float],
                                   portfolio_value: float) -> List[float]:
        """
        Calculate rebalancing trades needed.

        Args:
            current_weights: Current asset weights
            target_weights: Target asset weights
            portfolio_value: Total portfolio value

        Returns:
            List of trade amounts (positive = buy, negative = sell)
        """
        if len(current_weights) != len(target_weights):
            raise ValidationError("Current and target weights must have same length")

        if not MathUtils.is_within_tolerance(sum(current_weights), 1.0, 1e-6):
            raise ValidationError("Current weights must sum to 1")

        if not MathUtils.is_within_tolerance(sum(target_weights), 1.0, 1e-6):
            raise ValidationError("Target weights must sum to 1")

        trades = []
        for current, target in zip(current_weights, target_weights):
            trade_amount = (target - current) * portfolio_value
            trades.append(trade_amount)

        return trades

    @staticmethod
    def calculate_geometric_mean(returns: List[float]) -> float:
        """
        Calculate geometric mean of returns.

        Args:
            returns: List of return values

        Returns:
            Geometric mean
        """
        if not returns:
            raise ValidationError("Cannot calculate geometric mean of empty list")

        # Convert returns to growth factors (1 + return)
        growth_factors = [1 + r for r in returns]

        # Calculate geometric mean
        product = 1
        for factor in growth_factors:
            product *= factor

        geometric_mean = product ** (1 / len(returns))
        return geometric_mean - 1  # Convert back to return format