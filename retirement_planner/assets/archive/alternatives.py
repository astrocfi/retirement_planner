"""
Alternative asset classes for retirement planning.

Contains real estate, commodity, and custom asset implementations.
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

    def __init__(self, name: str, current_value: float, expected_return: float, volatility: float, property_type: str = "Residential", location: Optional[str] = None, rental_yield: float = 0.0, appreciation_rate: float = 0.03, property_tax_rate: float = 0.012, maintenance_rate: float = 0.02, leverage_ratio: float = 0.0, **kwargs):
        """Initialize RealEstate with asset_type automatically set."""
        # Store real estate specific fields in metadata
        metadata = {
            'property_type': property_type,
            'location': location,
            'rental_yield': rental_yield,
            'appreciation_rate': appreciation_rate,
            'property_tax_rate': property_tax_rate,
            'maintenance_rate': maintenance_rate,
            'leverage_ratio': leverage_ratio
        }
        metadata.update(kwargs)

        # Call parent constructor
        super().__init__(
            name=name,
            asset_type=AssetType.REAL_ESTATE,
            current_value=current_value,
            expected_return=expected_return,
            volatility=volatility,
            metadata=metadata
        )

    def __post_init__(self):
        """Validate real estate specific data."""
        # Get fields from metadata
        rental_yield = self.get_metadata_field('rental_yield', 0.0)
        appreciation_rate = self.get_metadata_field('appreciation_rate', 0.03)
        property_tax_rate = self.get_metadata_field('property_tax_rate', 0.012)
        leverage_ratio = self.get_metadata_field('leverage_ratio', 0.0)

        # Additional validation for real estate specific fields
        if not (0 <= rental_yield <= 0.2):  # Max 20% rental yield
            raise ValueError("Rental yield must be between 0% and 20%")

        if not (0 <= appreciation_rate <= 0.2):  # Max 20% appreciation rate
            raise ValueError("Appreciation rate must be between 0% and 20%")

        if not (0 <= property_tax_rate <= 0.05):  # Max 5% property tax rate
            raise ValueError("Property tax rate must be between 0% and 5%")

        if not (0 <= leverage_ratio <= 0.9):  # Max 90% LTV
            raise ValueError("Leverage ratio must be between 0% and 90%")

    def _get_tax_rate(self) -> float:
        """Get tax rate for real estate investments."""
        return 0.15  # Capital gains rate for real estate

    def get_rental_income(self) -> float:
        """Calculate annual rental income."""
        rental_yield = self.get_metadata_field('rental_yield', 0.0)
        return self.current_value * rental_yield

    def get_net_rental_income(self) -> float:
        """Calculate net rental income after expenses."""
        gross_rental = self.get_rental_income()
        property_tax_rate = self.get_metadata_field('property_tax_rate', 0.012)
        maintenance_rate = self.get_metadata_field('maintenance_rate', 0.02)
        property_tax = self.current_value * property_tax_rate
        maintenance = self.current_value * maintenance_rate
        return gross_rental - property_tax - maintenance

    def get_total_return(self) -> float:
        """Get total return including rental income and appreciation."""
        rental_yield = self.get_metadata_field('rental_yield', 0.0)
        appreciation_rate = self.get_metadata_field('appreciation_rate', 0.03)
        return self.expected_return + rental_yield + appreciation_rate

    def get_leverage_impact(self) -> float:
        """Calculate impact of leverage on returns."""
        leverage_ratio = self.get_metadata_field('leverage_ratio', 0.0)
        if leverage_ratio == 0:
            return 1.0

        # Simplified leverage calculation
        # Leverage amplifies both returns and risk
        return 1.0 + leverage_ratio * 0.5

    def get_tax_treatment(self) -> Dict[str, Any]:
        """Get tax treatment for real estate investments."""
        base_treatment = super().get_tax_treatment()

        # Get fields from metadata
        property_type = self.get_metadata_field('property_type', 'Residential')
        location = self.get_metadata_field('location')

        base_treatment.update({
            'depreciation': True,
            '1031_exchange': True,
            'property_type': property_type,
            'location': location,
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

    def __init__(self, name: str, current_value: float, expected_return: float, volatility: float, commodity_type: str = "Gold", storage_cost_rate: float = 0.0, insurance_cost_rate: float = 0.0, delivery_mechanism: str = "ETF", **kwargs):
        """Initialize Commodity with asset_type automatically set."""
        # Store commodity specific fields in metadata
        metadata = {
            'commodity_type': commodity_type,
            'storage_cost_rate': storage_cost_rate,
            'insurance_cost_rate': insurance_cost_rate,
            'delivery_mechanism': delivery_mechanism
        }
        metadata.update(kwargs)

        # Call parent constructor
        super().__init__(
            name=name,
            asset_type=AssetType.COMMODITY,
            current_value=current_value,
            expected_return=expected_return,
            volatility=volatility,
            metadata=metadata
        )

    def __post_init__(self):
        """Validate commodity specific data."""
        # Get fields from metadata
        storage_cost_rate = self.get_metadata_field('storage_cost_rate', 0.0)
        insurance_cost_rate = self.get_metadata_field('insurance_cost_rate', 0.0)

        # Additional validation for commodity specific fields
        if not (0 <= storage_cost_rate <= 0.1):  # Max 10% storage cost
            raise ValueError("Storage cost rate must be between 0% and 10%")

        if not (0 <= insurance_cost_rate <= 0.05):  # Max 5% insurance cost
            raise ValueError("Insurance cost rate must be between 0% and 5%")

    def _get_tax_rate(self) -> float:
        """Get tax rate for commodity investments."""
        delivery_mechanism = self.get_metadata_field('delivery_mechanism', 'ETF')
        if delivery_mechanism == "Physical":
            return 0.28  # Collectibles rate for physical commodities
        return 0.15  # Capital gains rate for ETFs/futures

    def get_carrying_cost(self) -> float:
        """Calculate annual carrying costs."""
        storage_cost_rate = self.get_metadata_field('storage_cost_rate', 0.0)
        insurance_cost_rate = self.get_metadata_field('insurance_cost_rate', 0.0)
        return self.current_value * (storage_cost_rate + insurance_cost_rate)

    def get_net_return(self) -> float:
        """Get net return after carrying costs."""
        carrying_cost_rate = self.get_carrying_cost() / self.current_value if self.current_value > 0 else 0.0
        return self.expected_return - carrying_cost_rate

    def get_inflation_hedge(self) -> float:
        """Estimate inflation hedging properties."""
        # Gold and other precious metals typically have high inflation correlation
        commodity_type = self.get_metadata_field('commodity_type', 'Gold')
        inflation_correlation = {
            'Gold': 0.8,
            'Silver': 0.7,
            'Oil': 0.6,
            'Natural Gas': 0.5
        }
        return inflation_correlation.get(commodity_type, 0.5)

    def get_tax_treatment(self) -> Dict[str, Any]:
        """Get tax treatment for commodity investments."""
        base_treatment = super().get_tax_treatment()

        # Get fields from metadata
        commodity_type = self.get_metadata_field('commodity_type', 'Gold')
        delivery_mechanism = self.get_metadata_field('delivery_mechanism', 'ETF')

        base_treatment.update({
            'collectibles_tax': delivery_mechanism == "Physical",
            'commodity_type': commodity_type,
            'delivery_mechanism': delivery_mechanism,
            'inflation_hedge': self.get_inflation_hedge()
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

    def __init__(self, name: str, current_value: float, expected_return: float, volatility: float, custom_type: str = "Other", income_stream: float = 0.0, growth_rate: float = 0.0, liquidity_score: float = 0.5, complexity_score: float = 0.5, **kwargs):
        """Initialize CustomAsset with asset_type automatically set."""
        # Store custom asset specific fields in metadata
        metadata = {
            'custom_type': custom_type,
            'income_stream': income_stream,
            'growth_rate': growth_rate,
            'liquidity_score': liquidity_score,
            'complexity_score': complexity_score
        }
        metadata.update(kwargs)

        # Call parent constructor
        super().__init__(
            name=name,
            asset_type=AssetType.CUSTOM,
            current_value=current_value,
            expected_return=expected_return,
            volatility=volatility,
            metadata=metadata
        )

    def __post_init__(self):
        """Validate custom asset specific data."""
        # Get fields from metadata
        income_stream = self.get_metadata_field('income_stream', 0.0)
        liquidity_score = self.get_metadata_field('liquidity_score', 0.5)
        complexity_score = self.get_metadata_field('complexity_score', 0.5)

        # Additional validation for custom asset specific fields
        if not (0 <= income_stream <= 1):  # Max 100% income stream
            raise ValueError("Income stream must be between 0% and 100%")

        if not (0 <= liquidity_score <= 1):
            raise ValueError("Liquidity score must be between 0 and 1")

        if not (0 <= complexity_score <= 1):
            raise ValueError("Complexity score must be between 0 and 1")

    def _get_tax_rate(self) -> float:
        """Get tax rate for custom assets."""
        return 0.25  # Ordinary income rate for custom assets

    def get_total_return(self) -> float:
        """Get total return including income stream and growth."""
        income_stream = self.get_metadata_field('income_stream', 0.0)
        growth_rate = self.get_metadata_field('growth_rate', 0.0)
        return self.expected_return + income_stream + growth_rate

    def get_liquidity_adjusted_return(self) -> float:
        """Get return adjusted for liquidity."""
        # Illiquid assets may have higher returns to compensate for lack of liquidity
        liquidity_score = self.get_metadata_field('liquidity_score', 0.5)
        if liquidity_score >= 0.9:
            return self.get_total_return()  # No premium for highly liquid assets
        liquidity_premium = (1 - liquidity_score) * 0.02  # Up to 2% premium
        return self.get_total_return() + liquidity_premium

    def get_complexity_risk(self) -> float:
        """Get additional risk due to complexity."""
        # Complex assets may have additional risk
        complexity_score = self.get_metadata_field('complexity_score', 0.5)
        return complexity_score * 0.05  # Up to 5% additional risk

    def get_tax_treatment(self) -> Dict[str, Any]:
        """Get tax treatment for custom assets."""
        base_treatment = super().get_tax_treatment()

        # Get fields from metadata
        custom_type = self.get_metadata_field('custom_type', 'Other')
        liquidity_score = self.get_metadata_field('liquidity_score', 0.5)
        complexity_score = self.get_metadata_field('complexity_score', 0.5)

        base_treatment.update({
            'custom_type': custom_type,
            'income_stream_taxable': True,
            'liquidity_score': liquidity_score,
            'complexity_score': complexity_score
        })
        return base_treatment