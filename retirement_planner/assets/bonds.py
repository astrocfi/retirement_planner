"""
Bond asset classes for retirement planning.

Contains a single Bond class classified by tax treatment.
"""

from dataclasses import dataclass, field
from typing import Dict, Optional, Any
from datetime import date
from .base import Asset, AssetType


@dataclass(frozen=True)
class Bond(Asset):
    """Single bond class supporting all bond types with configuration for tax treatment."""
    coupon_rate: float = 0.0
    maturity_date: Optional[date] = None
    face_value: float = 1000.0
    credit_rating: Optional[str] = None
    issuer: Optional[str] = None
    tax_treatment: str = "taxable"  # taxable, tax-exempt, tax-deferred
    duration: Optional[float] = None  # Duration in years
    issuer_type: Optional[str] = None  # government, corporate, municipal
    industry: Optional[str] = None
    callable: bool = False
    convertible: bool = False

    def __init__(self, name: str, current_value: float, expected_return: float, volatility: float, coupon_rate: float = 0.0, maturity_date: Optional[date] = None, face_value: float = 1000.0, credit_rating: Optional[str] = None, issuer: Optional[str] = None, tax_treatment: str = "taxable", duration: Optional[float] = None, issuer_type: Optional[str] = None, industry: Optional[str] = None, callable: bool = False, convertible: bool = False, **kwargs):
        """Initialize Bond with asset_type automatically set."""
        # Store bond-specific fields in metadata
        metadata = {
            'coupon_rate': coupon_rate,
            'maturity_date': maturity_date,
            'face_value': face_value,
            'credit_rating': credit_rating,
            'issuer': issuer,
            'tax_treatment': tax_treatment,
            'duration': duration,
            'issuer_type': issuer_type,
            'industry': industry,
            'callable': callable,
            'convertible': convertible
        }
        metadata.update(kwargs)

        # Call parent constructor
        super().__init__(
            name=name,
            asset_type=AssetType.BOND,
            current_value=current_value,
            expected_return=expected_return,
            volatility=volatility,
            metadata=metadata
        )

    def __post_init__(self):
        """Validate bond-specific data."""
        # Get fields from metadata
        coupon_rate = self.get_metadata_field('coupon_rate', 0.0)
        face_value = self.get_metadata_field('face_value', 1000.0)
        tax_treatment = self.get_metadata_field('tax_treatment', 'taxable')
        duration = self.get_metadata_field('duration')
        credit_rating = self.get_metadata_field('credit_rating')

        # Additional validation for bond-specific fields
        if not (0 <= coupon_rate <= 0.5):  # Max 50% coupon rate
            raise ValueError("Coupon rate must be between 0% and 50%")

        if face_value <= 0:
            raise ValueError("Face value must be positive")

        if tax_treatment not in ['taxable', 'tax-exempt', 'tax-deferred']:
            raise ValueError("Tax treatment must be 'taxable', 'tax-exempt', or 'tax-deferred'")

        if duration is not None and duration < 0:
            raise ValueError("Duration must be non-negative")

        # Validate credit rating if provided
        valid_ratings = ['AAA', 'AA', 'A', 'BBB', 'BB', 'B', 'CCC', 'CC', 'C', 'D']
        if credit_rating and credit_rating not in valid_ratings:
            raise ValueError("Invalid credit rating")

    def _get_tax_rate(self) -> float:
        """Get tax rate for bond investments based on tax treatment."""
        tax_treatment = self.get_metadata_field('tax_treatment', 'taxable')
        if tax_treatment == "tax-exempt":
            return 0.0
        elif tax_treatment == "tax-deferred":
            return 0.0  # Tax deferred until withdrawal
        else:  # taxable
            return 0.25  # Ordinary income rate for taxable bonds

    def _is_tax_deferred(self) -> bool:
        """Check if bond is tax-deferred."""
        tax_treatment = self.get_metadata_field('tax_treatment', 'taxable')
        return tax_treatment == "tax-deferred"

    def _is_tax_exempt(self) -> bool:
        """Check if bond is tax-exempt."""
        tax_treatment = self.get_metadata_field('tax_treatment', 'taxable')
        return tax_treatment == "tax-exempt"

    def get_coupon_payment(self) -> float:
        """Calculate annual coupon payment."""
        coupon_rate = self.get_metadata_field('coupon_rate', 0.0)
        face_value = self.get_metadata_field('face_value', 1000.0)
        return face_value * coupon_rate

    def get_yield_to_maturity(self) -> float:
        """Calculate yield to maturity (simplified)."""
        coupon_rate = self.get_metadata_field('coupon_rate', 0.0)
        face_value = self.get_metadata_field('face_value', 1000.0)
        maturity_date = self.get_metadata_field('maturity_date')

        # Simplified YTM calculation
        if maturity_date and self.current_value != face_value and self.current_value > 0:
            # This is a simplified calculation - real YTM would be more complex
            return coupon_rate + (face_value - self.current_value) / self.current_value
        elif self.current_value != face_value and self.current_value > 0:
            # No maturity date but current value differs from face value
            return coupon_rate + (face_value - self.current_value) / self.current_value
        return coupon_rate

    def get_duration(self) -> float:
        """Calculate bond duration."""
        duration = self.get_metadata_field('duration')
        if duration is not None:
            return duration

        # Calculate duration if not provided
        maturity_date = self.get_metadata_field('maturity_date')
        coupon_rate = self.get_metadata_field('coupon_rate', 0.0)

        if maturity_date:
            # For zero-coupon bonds, duration = time to maturity
            if coupon_rate == 0:
                return self._years_to_maturity()
            # For coupon bonds, duration is typically 60-80% of time to maturity
            return self._years_to_maturity() * 0.7
        return 5.0  # Default duration

    def _years_to_maturity(self) -> float:
        """Calculate years to maturity."""
        maturity_date = self.get_metadata_field('maturity_date')
        if not maturity_date:
            return 10.0  # Default maturity

        today = date.today()
        days_to_maturity = (maturity_date - today).days
        return max(0, days_to_maturity / 365.25)

    def get_interest_rate_risk(self) -> float:
        """Calculate interest rate risk based on duration."""
        duration = self.get_duration()
        # Simplified: price change ≈ -duration × interest rate change
        return duration * 0.01  # For 1% interest rate change

    def get_credit_risk(self) -> float:
        """Get credit risk based on rating and issuer type."""
        issuer_type = self.get_metadata_field('issuer_type')
        credit_rating = self.get_metadata_field('credit_rating')

        if issuer_type == "government":
            return 0.001  # Government bonds have very low credit risk

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
        return risk_map.get(credit_rating, 0.05)

    def get_spread_over_treasury(self) -> float:
        """Get credit spread over Treasury bonds."""
        issuer_type = self.get_metadata_field('issuer_type')
        callable = self.get_metadata_field('callable', False)
        convertible = self.get_metadata_field('convertible', False)

        if issuer_type == "government":
            return 0.0  # No spread for government bonds

        # Simplified credit spread calculation
        base_spread = self.get_credit_risk() * 100  # Convert to basis points
        if callable:
            base_spread += 50  # Callable bonds have higher spreads
        if convertible:
            base_spread -= 25  # Convertible bonds have lower spreads
        return base_spread / 10000  # Convert back to decimal

    def get_total_yield(self) -> float:
        """Get total yield including credit spread."""
        treasury_yield = 0.03  # Assume 3% Treasury yield
        return treasury_yield + self.get_spread_over_treasury()

    def get_tax_treatment(self) -> Dict[str, Any]:
        """Get tax treatment for bonds."""
        base_treatment = super().get_tax_treatment()

        # Get fields from metadata
        tax_treatment = self.get_metadata_field('tax_treatment', 'taxable')
        issuer_type = self.get_metadata_field('issuer_type')
        credit_rating = self.get_metadata_field('credit_rating')
        callable = self.get_metadata_field('callable', False)
        convertible = self.get_metadata_field('convertible', False)
        industry = self.get_metadata_field('industry')

        base_treatment.update({
            'tax_treatment': tax_treatment,
            'tax_exempt': self._is_tax_exempt(),
            'tax_deferred': self._is_tax_deferred(),
            'issuer_type': issuer_type,
            'credit_rating': credit_rating,
            'credit_risk': self.get_credit_risk(),
            'duration': self.get_duration(),
            'callable': callable,
            'convertible': convertible,
            'industry': industry,
            'credit_spread': self.get_spread_over_treasury()
        })
        return base_treatment

    def get_after_tax_yield(self, marginal_tax_rate: float = 0.25) -> float:
        """Get after-tax yield based on tax treatment."""
        total_yield = self.get_total_yield()
        tax_treatment = self.get_metadata_field('tax_treatment', 'taxable')

        if tax_treatment == "tax-exempt":
            return total_yield  # No taxes
        elif tax_treatment == "tax-deferred":
            return total_yield  # No taxes until withdrawal
        else:  # taxable
            return total_yield * (1 - marginal_tax_rate)

    def get_equivalent_taxable_yield(self, marginal_tax_rate: float = 0.25) -> float:
        """Get equivalent taxable yield for tax-exempt bonds."""
        tax_treatment = self.get_metadata_field('tax_treatment', 'taxable')
        if tax_treatment != "tax-exempt":
            return self.get_total_yield()

        # For tax-exempt bonds, calculate equivalent taxable yield
        tax_exempt_yield = self.get_total_yield()
        return tax_exempt_yield / (1 - marginal_tax_rate)