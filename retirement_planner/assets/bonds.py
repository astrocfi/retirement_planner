"""
Bond asset classes for retirement planning.

Contains government and corporate bond implementations.
"""

from dataclasses import dataclass, field
from typing import Dict, Optional, Any
from datetime import date
from .base import Asset, AssetType


@dataclass(frozen=True)
class Bond(Asset):
    """Base bond class with common bond functionality."""
    coupon_rate: float = 0.0
    maturity_date: Optional[date] = None
    face_value: float = 1000.0
    credit_rating: Optional[str] = None
    issuer: Optional[str] = None

    def __post_init__(self):
        """Validate bond-specific data."""
        super().__post_init__()

        # Additional validation for bond-specific fields
        if not (0 <= self.coupon_rate <= 0.5):  # Max 50% coupon rate
            raise ValueError("Coupon rate must be between 0% and 50%")

        if self.face_value <= 0:
            raise ValueError("Face value must be positive")

    def _get_tax_rate(self) -> float:
        """Get tax rate for bond investments."""
        return 0.15  # Capital gains rate for bonds

    def get_coupon_payment(self) -> float:
        """Calculate annual coupon payment."""
        return self.face_value * self.coupon_rate

    def get_yield_to_maturity(self) -> float:
        """Calculate yield to maturity (simplified)."""
        # Simplified YTM calculation
        if self.maturity_date and self.current_value != self.face_value:
            # This is a simplified calculation - real YTM would be more complex
            return self.coupon_rate + (self.face_value - self.current_value) / self.current_value
        return self.coupon_rate

    def get_duration(self) -> float:
        """Calculate bond duration (simplified)."""
        # Simplified duration calculation
        if self.maturity_date:
            # For zero-coupon bonds, duration = time to maturity
            if self.coupon_rate == 0:
                return self._years_to_maturity()
            # For coupon bonds, duration is typically 60-80% of time to maturity
            return self._years_to_maturity() * 0.7
        return 5.0  # Default duration

    def _years_to_maturity(self) -> float:
        """Calculate years to maturity."""
        if not self.maturity_date:
            return 10.0  # Default maturity

        today = date.today()
        days_to_maturity = (self.maturity_date - today).days
        return max(0, days_to_maturity / 365.25)

    def get_interest_rate_risk(self) -> float:
        """Calculate interest rate risk based on duration."""
        duration = self.get_duration()
        # Simplified: price change ≈ -duration × interest rate change
        return duration * 0.01  # For 1% interest rate change

    def is_tax_exempt(self) -> bool:
        """Check if bond is tax-exempt."""
        return False


@dataclass(frozen=True)
class GovernmentBond(Bond):
    """Government bond implementation."""
    government_type: str = "Federal"  # Federal, State, Municipal
    backing: str = "Full Faith and Credit"

    def __post_init__(self):
        """Validate government bond data."""
        # Set asset type before calling parent validation
        object.__setattr__(self, 'asset_type', AssetType.BOND)
        super().__post_init__()

    def _get_tax_rate(self) -> float:
        """Get tax rate for government bonds."""
        if self.government_type == "Municipal":
            return 0.0  # Tax-exempt
        return 0.15  # Federal bonds taxed at capital gains rate

    def is_tax_exempt(self) -> bool:
        """Check if government bond is tax-exempt."""
        return self.government_type == "Municipal"

    def get_credit_risk(self) -> float:
        """Get credit risk for government bonds."""
        # Government bonds have very low credit risk
        return 0.001  # 0.1% default probability

    def get_tax_treatment(self) -> Dict[str, Any]:
        """Get tax treatment for government bonds."""
        base_treatment = super().get_tax_treatment()
        base_treatment.update({
            'tax_exempt': self.is_tax_exempt(),
            'government_type': self.government_type,
            'backing': self.backing,
            'credit_risk': self.get_credit_risk()
        })
        return base_treatment


@dataclass(frozen=True)
class CorporateBond(Bond):
    """Corporate bond implementation."""
    industry: Optional[str] = None
    callable: bool = False
    convertible: bool = False

    def __post_init__(self):
        """Validate corporate bond data."""
        # Set asset type before calling parent validation
        object.__setattr__(self, 'asset_type', AssetType.BOND)
        super().__post_init__()

    def _get_tax_rate(self) -> float:
        """Get tax rate for corporate bonds."""
        return 0.25  # Ordinary income rate for corporate bonds

    def get_credit_risk(self) -> float:
        """Get credit risk based on rating."""
        risk_map = {
            'AAA': 0.001,
            'AA': 0.005,
            'A': 0.01,
            'BBB': 0.025,
            'BB': 0.05,
            'B': 0.10,
            'CCC': 0.20,
            'CC': 0.30,
            'C': 0.40,
            'D': 0.50
        }
        return risk_map.get(self.credit_rating, 0.05)

    def get_spread_over_treasury(self) -> float:
        """Get credit spread over Treasury bonds."""
        # Simplified credit spread calculation
        base_spread = self.get_credit_risk() * 100  # Convert to basis points
        if self.callable:
            base_spread += 50  # Callable bonds have higher spreads
        if self.convertible:
            base_spread -= 25  # Convertible bonds have lower spreads
        return base_spread / 10000  # Convert back to decimal

    def get_total_yield(self) -> float:
        """Get total yield including credit spread."""
        treasury_yield = 0.03  # Assume 3% Treasury yield
        return treasury_yield + self.get_spread_over_treasury()

    def get_tax_treatment(self) -> Dict[str, Any]:
        """Get tax treatment for corporate bonds."""
        base_treatment = super().get_tax_treatment()
        base_treatment.update({
            'tax_exempt': False,
            'industry': self.industry,
            'callable': self.callable,
            'convertible': self.convertible,
            'credit_risk': self.get_credit_risk(),
            'credit_spread': self.get_spread_over_treasury()
        })
        return base_treatment