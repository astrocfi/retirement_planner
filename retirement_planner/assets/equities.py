"""
Equity asset classes for retirement planning.

Contains domestic and international stock implementations.
"""

from dataclasses import dataclass, field
from typing import Dict, Optional, Any
from .base import Asset, AssetType


@dataclass(frozen=True)
class Equity(Asset):
    """Base equity class with common stock functionality."""
    dividend_yield: float = 0.0
    beta: float = 1.0
    market_cap: Optional[str] = None  # large, mid, small
    sector: Optional[str] = None

    def __post_init__(self):
        """Validate equity-specific data."""
        super().__post_init__()

        # Additional validation for equity-specific fields
        if not (0 <= self.dividend_yield <= 0.5):  # Max 50% dividend yield
            raise ValueError("Dividend yield must be between 0% and 50%")

        if not (0 <= self.beta <= 3):  # Beta between 0 and 3
            raise ValueError("Beta must be between 0 and 3")

    def _get_tax_rate(self) -> float:
        """Get tax rate for equity investments."""
        # Qualified dividends and long-term capital gains
        return 0.15

    def get_dividend_income(self) -> float:
        """Calculate annual dividend income."""
        return self.current_value * self.dividend_yield

    def get_total_return(self) -> float:
        """Get total return including dividends."""
        return self.expected_return + self.dividend_yield

    def get_risk_adjusted_return(self, risk_free_rate: float = 0.02) -> float:
        """Calculate risk-adjusted return using CAPM."""
        return risk_free_rate + self.beta * (self.expected_return - risk_free_rate)


@dataclass(frozen=True)
class DomesticStock(Equity):
    """Domestic stock implementation."""
    country: str = "US"
    exchange: Optional[str] = None  # NYSE, NASDAQ, etc.

    def __post_init__(self):
        """Validate domestic stock data."""
        # Set asset type before calling parent validation
        object.__setattr__(self, 'asset_type', AssetType.EQUITY)
        super().__post_init__()

    def get_tax_treatment(self) -> Dict[str, Any]:
        """Get tax treatment for domestic stocks."""
        base_treatment = super().get_tax_treatment()
        base_treatment.update({
            'qualified_dividends': True,
            'foreign_tax_credit': False,
            'country': self.country
        })
        return base_treatment


@dataclass(frozen=True)
class InternationalStock(Equity):
    """International stock implementation."""
    country: str = "International"
    region: Optional[str] = None  # Europe, Asia, Emerging Markets, etc.
    foreign_tax_rate: float = 0.0

    def __post_init__(self):
        """Validate international stock data."""
        # Set asset type before calling parent validation
        object.__setattr__(self, 'asset_type', AssetType.EQUITY)
        super().__post_init__()

        if not (0 <= self.foreign_tax_rate <= 0.5):
            raise ValueError("Foreign tax rate must be between 0% and 50%")

    def get_tax_treatment(self) -> Dict[str, Any]:
        """Get tax treatment for international stocks."""
        base_treatment = super().get_tax_treatment()
        base_treatment.update({
            'qualified_dividends': True,
            'foreign_tax_credit': True,
            'foreign_tax_rate': self.foreign_tax_rate,
            'country': self.country,
            'region': self.region
        })
        return base_treatment

    def get_effective_dividend_yield(self) -> float:
        """Get effective dividend yield after foreign taxes."""
        return self.dividend_yield * (1 - self.foreign_tax_rate)

    def get_currency_risk(self) -> float:
        """Estimate currency risk based on region."""
        currency_risk_map = {
            'Europe': 0.15,
            'Asia': 0.20,
            'Emerging Markets': 0.25,
            'Developed': 0.10
        }
        return currency_risk_map.get(self.region, 0.20)

    def get_total_volatility(self) -> float:
        """Get total volatility including currency risk."""
        currency_risk = self.get_currency_risk()
        # Simplified calculation: sqrt(equity_vol^2 + currency_vol^2)
        return (self.volatility ** 2 + currency_risk ** 2) ** 0.5