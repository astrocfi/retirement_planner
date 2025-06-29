"""
Equity asset classes for retirement planning.

Contains a single Equity class supporting all stock types with configuration.
"""

from dataclasses import dataclass, field
from typing import Dict, Optional, Any
from .base import Asset, AssetType


@dataclass(frozen=True)
class Equity(Asset):
    """Single equity class supporting all stock types with configuration."""
    dividend_yield: float = 0.0
    beta: float = 1.0
    market_cap: Optional[str] = None  # small, medium, large
    geography: str = "domestic"  # domestic, international, emerging
    is_public: bool = True  # public vs private equity
    sector: Optional[str] = None
    country: Optional[str] = None
    region: Optional[str] = None  # Europe, Asia, Emerging Markets, etc.
    foreign_tax_rate: float = 0.0

    def __init__(self, name: str, current_value: float, expected_return: float, volatility: float, dividend_yield: float = 0.0, beta: float = 1.0, market_cap: Optional[str] = None, geography: str = "domestic", is_public: bool = True, sector: Optional[str] = None, country: Optional[str] = None, region: Optional[str] = None, foreign_tax_rate: float = 0.0, **kwargs):
        """Initialize Equity with asset_type automatically set."""
        # Store equity-specific fields in metadata
        metadata = {
            'dividend_yield': dividend_yield,
            'beta': beta,
            'market_cap': market_cap,
            'geography': geography,
            'is_public': is_public,
            'sector': sector,
            'country': country,
            'region': region,
            'foreign_tax_rate': foreign_tax_rate
        }
        metadata.update(kwargs)

        # Call parent constructor
        super().__init__(
            name=name,
            asset_type=AssetType.EQUITY,
            current_value=current_value,
            expected_return=expected_return,
            volatility=volatility,
            metadata=metadata
        )

    def __post_init__(self):
        """Validate equity-specific data."""
        # Get fields from metadata
        dividend_yield = self.get_metadata_field('dividend_yield', 0.0)
        beta = self.get_metadata_field('beta', 1.0)
        market_cap = self.get_metadata_field('market_cap')
        geography = self.get_metadata_field('geography', 'domestic')
        foreign_tax_rate = self.get_metadata_field('foreign_tax_rate', 0.0)

        # Additional validation for equity-specific fields
        if not (0 <= dividend_yield <= 0.5):  # Max 50% dividend yield
            raise ValueError("Dividend yield must be between 0% and 50%")

        if not (0 <= beta <= 3):  # Beta between 0 and 3
            raise ValueError("Beta must be between 0 and 3")

        if market_cap and market_cap not in ['small', 'medium', 'large']:
            raise ValueError("Market cap must be 'small', 'medium', or 'large'")

        if geography not in ['domestic', 'international', 'emerging']:
            raise ValueError("Geography must be 'domestic', 'international', or 'emerging'")

        if not (0 <= foreign_tax_rate <= 0.5):
            raise ValueError("Foreign tax rate must be between 0% and 50%")

    def _get_tax_rate(self) -> float:
        """Get tax rate for equity investments."""
        # Qualified dividends and long-term capital gains
        return 0.15

    def get_dividend_income(self) -> float:
        """Calculate annual dividend income."""
        dividend_yield = self.get_metadata_field('dividend_yield', 0.0)
        return self.current_value * dividend_yield

    def get_total_return(self) -> float:
        """Get total return including dividends."""
        dividend_yield = self.get_metadata_field('dividend_yield', 0.0)
        return self.expected_return + dividend_yield

    def get_risk_adjusted_return(self, risk_free_rate: float = 0.02) -> float:
        """Calculate risk-adjusted return using CAPM."""
        beta = self.get_metadata_field('beta', 1.0)
        return risk_free_rate + beta * (self.expected_return - risk_free_rate)

    def get_tax_treatment(self) -> Dict[str, Any]:
        """Get tax treatment for equity investments."""
        base_treatment = super().get_tax_treatment()

        # Get fields from metadata
        geography = self.get_metadata_field('geography', 'domestic')
        country = self.get_metadata_field('country')
        region = self.get_metadata_field('region')
        market_cap = self.get_metadata_field('market_cap')
        is_public = self.get_metadata_field('is_public', True)
        foreign_tax_rate = self.get_metadata_field('foreign_tax_rate', 0.0)

        # Determine if qualified dividends apply
        qualified_dividends = geography == "domestic" or (geography == "international" and country in ["Canada", "UK", "Germany", "France", "Japan", "Australia"])

        base_treatment.update({
            'qualified_dividends': qualified_dividends,
            'foreign_tax_credit': geography != "domestic",
            'foreign_tax_rate': foreign_tax_rate if geography != "domestic" else 0.0,
            'country': country,
            'region': region,
            'geography': geography,
            'market_cap': market_cap,
            'is_public': is_public
        })
        return base_treatment

    def get_effective_dividend_yield(self) -> float:
        """Get effective dividend yield after foreign taxes."""
        dividend_yield = self.get_metadata_field('dividend_yield', 0.0)
        geography = self.get_metadata_field('geography', 'domestic')
        foreign_tax_rate = self.get_metadata_field('foreign_tax_rate', 0.0)

        if geography == "domestic":
            return dividend_yield
        return dividend_yield * (1 - foreign_tax_rate)

    def get_currency_risk(self) -> float:
        """Estimate currency risk based on geography and region."""
        geography = self.get_metadata_field('geography', 'domestic')
        region = self.get_metadata_field('region')

        if geography == "domestic":
            return 0.0

        currency_risk_map = {
            'Europe': 0.15,
            'Asia': 0.20,
            'Emerging Markets': 0.25,
            'Developed': 0.10
        }

        if geography == "emerging":
            return 0.25
        elif region:
            return currency_risk_map.get(region, 0.20)
        else:
            return 0.20

    def get_total_volatility(self) -> float:
        """Get total volatility including currency risk."""
        currency_risk = self.get_currency_risk()
        # Simplified calculation: sqrt(equity_vol^2 + currency_vol^2)
        return (self.volatility ** 2 + currency_risk ** 2) ** 0.5

    def get_liquidity_premium(self) -> float:
        """Get liquidity premium for private equity."""
        is_public = self.get_metadata_field('is_public', True)
        if not is_public:
            return 0.02  # 2% liquidity premium for private equity
        return 0.0

    def get_adjusted_return(self) -> float:
        """Get return adjusted for liquidity premium."""
        return self.expected_return + self.get_liquidity_premium()

    def get_size_premium(self) -> float:
        """Get size premium based on market cap."""
        market_cap = self.get_metadata_field('market_cap')
        size_premiums = {
            'small': 0.03,  # 3% small cap premium
            'medium': 0.01,  # 1% mid cap premium
            'large': 0.00   # No premium for large cap
        }
        return size_premiums.get(market_cap, 0.0)

    def get_geography_premium(self) -> float:
        """Get geography premium for international/emerging markets."""
        geography = self.get_metadata_field('geography', 'domestic')
        geography_premiums = {
            'domestic': 0.00,      # No premium for domestic
            'international': 0.01,  # 1% premium for international
            'emerging': 0.03       # 3% premium for emerging markets
        }
        return geography_premiums.get(geography, 0.0)

    def get_total_premium(self) -> float:
        """Get total premium including size, geography, and liquidity."""
        return (self.get_size_premium() +
                self.get_geography_premium() +
                self.get_liquidity_premium())

    def get_risk_adjusted_expected_return(self) -> float:
        """Get expected return adjusted for all premiums."""
        return self.expected_return + self.get_total_premium()