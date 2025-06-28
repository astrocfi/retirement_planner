"""
Alternative asset classes for retirement planning.

Contains real estate, commodity, private equity, and custom asset implementations.
"""

from dataclasses import dataclass, field
from typing import Dict, Optional, Any
from .base import Asset, AssetType


@dataclass(frozen=True)
class RealEstate(Asset):
    """Real estate investment implementation."""
    property_type: str = "Residential"  # Residential, Commercial, Industrial, REIT
    location: Optional[str] = None
    rental_yield: float = 0.0
    appreciation_rate: float = 0.03
    property_tax_rate: float = 0.012
    maintenance_rate: float = 0.02
    leverage_ratio: float = 0.0  # 0 = no debt, 0.8 = 80% LTV

    def __post_init__(self):
        """Validate real estate data."""
        # Set asset type before calling parent validation
        object.__setattr__(self, 'asset_type', AssetType.REAL_ESTATE)
        super().__post_init__()

        # Additional validation
        if not (0 <= self.rental_yield <= 0.2):  # Max 20% rental yield
            raise ValueError("Rental yield must be between 0% and 20%")

        if not (0 <= self.appreciation_rate <= 0.2):  # Max 20% appreciation
            raise ValueError("Appreciation rate must be between 0% and 20%")

        if not (0 <= self.property_tax_rate <= 0.05):  # Max 5% property tax
            raise ValueError("Property tax rate must be between 0% and 5%")

        if not (0 <= self.leverage_ratio <= 0.9):  # Max 90% LTV
            raise ValueError("Leverage ratio must be between 0% and 90%")

    def _get_tax_rate(self) -> float:
        """Get tax rate for real estate investments."""
        return 0.15  # Capital gains rate for real estate

    def get_rental_income(self) -> float:
        """Calculate annual rental income."""
        return self.current_value * self.rental_yield

    def get_net_rental_income(self) -> float:
        """Calculate net rental income after expenses."""
        gross_rental = self.get_rental_income()
        property_tax = self.current_value * self.property_tax_rate
        maintenance = self.current_value * self.maintenance_rate
        return gross_rental - property_tax - maintenance

    def get_total_return(self) -> float:
        """Get total return including rental income and appreciation."""
        return self.expected_return + self.rental_yield + self.appreciation_rate

    def get_leverage_impact(self) -> float:
        """Calculate impact of leverage on returns."""
        if self.leverage_ratio == 0:
            return 1.0

        # Simplified leverage calculation
        # Leverage amplifies both returns and risk
        return 1.0 + self.leverage_ratio * 0.5

    def get_tax_treatment(self) -> Dict[str, Any]:
        """Get tax treatment for real estate investments."""
        base_treatment = super().get_tax_treatment()
        base_treatment.update({
            'depreciation': True,
            '1031_exchange': True,
            'property_type': self.property_type,
            'location': self.location,
            'rental_income_taxable': True
        })
        return base_treatment


@dataclass(frozen=True)
class Commodity(Asset):
    """Commodity investment implementation."""
    commodity_type: str = "Gold"  # Gold, Silver, Oil, Natural Gas, etc.
    storage_cost_rate: float = 0.0
    insurance_cost_rate: float = 0.0
    delivery_mechanism: str = "ETF"  # Physical, ETF, Futures

    def __post_init__(self):
        """Validate commodity data."""
        # Set asset type before calling parent validation
        object.__setattr__(self, 'asset_type', AssetType.COMMODITY)
        super().__post_init__()

        # Additional validation
        if not (0 <= self.storage_cost_rate <= 0.1):  # Max 10% storage cost
            raise ValueError("Storage cost rate must be between 0% and 10%")

        if not (0 <= self.insurance_cost_rate <= 0.05):  # Max 5% insurance cost
            raise ValueError("Insurance cost rate must be between 0% and 5%")

    def _get_tax_rate(self) -> float:
        """Get tax rate for commodity investments."""
        if self.delivery_mechanism == "Physical":
            return 0.28  # Collectibles rate for physical commodities
        return 0.15  # Capital gains rate for ETFs/futures

    def get_carrying_cost(self) -> float:
        """Calculate annual carrying costs."""
        return self.current_value * (self.storage_cost_rate + self.insurance_cost_rate)

    def get_net_return(self) -> float:
        """Get net return after carrying costs."""
        return self.expected_return - self.get_carrying_cost()

    def get_inflation_hedge(self) -> float:
        """Estimate inflation hedging properties."""
        # Gold and other precious metals typically have high inflation correlation
        inflation_correlation = {
            'Gold': 0.8,
            'Silver': 0.7,
            'Oil': 0.6,
            'Natural Gas': 0.5
        }
        return inflation_correlation.get(self.commodity_type, 0.5)

    def get_tax_treatment(self) -> Dict[str, Any]:
        """Get tax treatment for commodity investments."""
        base_treatment = super().get_tax_treatment()
        base_treatment.update({
            'collectibles_tax': self.delivery_mechanism == "Physical",
            'commodity_type': self.commodity_type,
            'delivery_mechanism': self.delivery_mechanism,
            'inflation_hedge': self.get_inflation_hedge()
        })
        return base_treatment


@dataclass(frozen=True)
class PrivateEquity(Asset):
    """Private equity investment implementation."""
    fund_type: str = "Buyout"  # Buyout, Venture Capital, Growth, Distressed
    vintage_year: Optional[int] = None
    management_fee: float = 0.02  # 2% management fee
    carried_interest: float = 0.20  # 20% carried interest
    illiquidity_premium: float = 0.03  # 3% illiquidity premium

    def __post_init__(self):
        """Validate private equity data."""
        # Set asset type before calling parent validation
        object.__setattr__(self, 'asset_type', AssetType.PRIVATE_EQUITY)
        super().__post_init__()

        # Additional validation
        if not (0 <= self.management_fee <= 0.03):  # Max 3% management fee
            raise ValueError("Management fee must be between 0% and 3%")

        if not (0 <= self.carried_interest <= 0.30):  # Max 30% carried interest
            raise ValueError("Carried interest must be between 0% and 30%")

    def _get_tax_rate(self) -> float:
        """Get tax rate for private equity investments."""
        return 0.15  # Capital gains rate for private equity

    def get_net_return(self) -> float:
        """Get net return after fees."""
        gross_return = self.expected_return
        net_return = gross_return - self.management_fee

        # Apply carried interest if return exceeds hurdle rate (typically 8%)
        hurdle_rate = 0.08
        if net_return > hurdle_rate:
            excess_return = net_return - hurdle_rate
            carried_interest_cost = excess_return * self.carried_interest
            net_return -= carried_interest_cost

        return net_return

    def get_illiquidity_adjusted_return(self) -> float:
        """Get return adjusted for illiquidity."""
        return self.get_net_return() + self.illiquidity_premium

    def get_volatility_adjustment(self) -> float:
        """Adjust volatility for illiquidity and smoothing."""
        # Private equity returns are typically smoothed, so volatility appears lower
        smoothing_factor = 0.7
        return self.volatility * smoothing_factor

    def get_tax_treatment(self) -> Dict[str, Any]:
        """Get tax treatment for private equity investments."""
        base_treatment = super().get_tax_treatment()
        base_treatment.update({
            'carried_interest_tax': True,
            'fund_type': self.fund_type,
            'vintage_year': self.vintage_year,
            'illiquid': True
        })
        return base_treatment


@dataclass(frozen=True)
class CustomAsset(Asset):
    """Custom asset implementation for user-defined assets."""
    custom_type: str = "Other"
    income_stream: float = 0.0
    growth_rate: float = 0.0
    liquidity_score: float = 0.5  # 0 = illiquid, 1 = highly liquid
    complexity_score: float = 0.5  # 0 = simple, 1 = complex

    def __post_init__(self):
        """Validate custom asset data."""
        # Set asset type before calling parent validation
        object.__setattr__(self, 'asset_type', AssetType.CUSTOM)
        super().__post_init__()

        # Additional validation
        if not (0 <= self.income_stream <= 0.5):  # Max 50% income stream
            raise ValueError("Income stream must be between 0% and 50%")

        if not (0 <= self.liquidity_score <= 1):
            raise ValueError("Liquidity score must be between 0 and 1")

        if not (0 <= self.complexity_score <= 1):
            raise ValueError("Complexity score must be between 0 and 1")

    def _get_tax_rate(self) -> float:
        """Get tax rate for custom assets."""
        # Default to ordinary income rate for custom assets
        return 0.25

    def get_total_return(self) -> float:
        """Get total return including income and growth."""
        return self.expected_return + self.income_stream + self.growth_rate

    def get_liquidity_adjusted_return(self) -> float:
        """Get return adjusted for liquidity."""
        # Less liquid assets should have higher expected returns
        liquidity_premium = (1 - self.liquidity_score) * 0.02  # Up to 2% premium
        return self.get_total_return() + liquidity_premium

    def get_complexity_risk(self) -> float:
        """Estimate risk based on complexity."""
        # More complex assets may have higher risk
        complexity_risk = self.complexity_score * 0.1  # Up to 10% additional risk
        return self.volatility + complexity_risk

    def get_tax_treatment(self) -> Dict[str, Any]:
        """Get tax treatment for custom assets."""
        base_treatment = super().get_tax_treatment()
        base_treatment.update({
            'custom_type': self.custom_type,
            'liquidity_score': self.liquidity_score,
            'complexity_score': self.complexity_score,
            'income_taxable': True
        })
        return base_treatment