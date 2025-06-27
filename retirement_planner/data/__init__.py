"""
Data layer for retirement planner.

This module provides data loading, validation, and management capabilities
for market data, tax data, and other financial information needed for
retirement planning analysis.
"""

from .market_data import (
    MarketDataLoader,
    HistoricalReturns,
    CorrelationMatrix,
    RiskFreeRate,
    MarketDataError
)

from .tax_data import (
    TaxDataLoader,
    TaxBrackets,
    SocialSecurityData,
    TaxDataError
)

from .validators import (
    DataValidator,
    OutlierDetector,
    DataQualityChecker,
    ValidationResult
)

__all__ = [
    # Market data
    'MarketDataLoader',
    'HistoricalReturns',
    'CorrelationMatrix',
    'RiskFreeRate',
    'MarketDataError',

    # Tax data
    'TaxDataLoader',
    'TaxBrackets',
    'SocialSecurityData',
    'TaxDataError',

    # Data validation
    'DataValidator',
    'OutlierDetector',
    'DataQualityChecker',
    'ValidationResult'
]