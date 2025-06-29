"""
Base asset classes for retirement planning.

Contains the base Asset class and related functionality.
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any, Tuple
from enum import Enum
import numpy as np
from retirement_planner.core.validation import Validator, RequiredRule, RangeRule, PercentageRule
from retirement_planner.core.exceptions import ValidationError, AssetError


class AssetType(Enum):
    """Types of assets in retirement planning."""
    EQUITY = "equity"
    BOND = "bond"
    REAL_ESTATE = "real_estate"
    COMMODITY = "commodity"
    CUSTOM = "custom"
    CASH = "cash"

    @classmethod
    def from_string(cls, asset_type_str: str) -> 'AssetType':
        """Create AssetType from string, handling common aliases."""
        # Define aliases for common asset type names
        aliases = {
            'stocks': 'equity',
            'stock': 'equity',
            'equities': 'equity',
            'bonds': 'bond',
            'fixed_income': 'bond',
            'cash_equivalent': 'cash',
            'cash_equivalents': 'cash',
            'real_estate': 'real_estate',
            'property': 'real_estate',
            'commodities': 'commodity',
            'precious_metals': 'commodity',
            'custom_asset': 'custom',
            'alternative': 'custom'
        }

        # Normalize the input string
        normalized = asset_type_str.lower().strip()

        # Check if it's a direct match first
        try:
            return cls(normalized)
        except ValueError:
            pass

        # Check if it's an alias
        if normalized in aliases:
            return cls(aliases[normalized])

        # If still not found, raise the original error
        raise ValueError(f"'{asset_type_str}' is not a valid AssetType")


@dataclass(frozen=True)
class AssetMetrics:
    """Metrics for an asset."""
    expected_return: float
    volatility: float
    correlation: Dict[str, float] = field(default_factory=dict)
    sharpe_ratio: Optional[float] = None
    max_drawdown: Optional[float] = None
    var_95: Optional[float] = None  # 95% Value at Risk


@dataclass(frozen=True)
class Asset:
    """Base asset class with common functionality."""
    name: str
    asset_type: AssetType
    current_value: float
    expected_return: float
    volatility: float
    correlation: Dict[str, float] = field(default_factory=dict)
    description: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    # Tax-related fields
    cost_basis: float = 0.0
    dividend_rate: float = 0.0
    dividend_volatility: float = 0.0
    tax_free: bool = False
    liquid: bool = True
    liquid_from_year: Optional[int] = None
    dividend_reinvestment: bool = True

    def __init__(self, name: str, asset_type: AssetType, current_value: float, expected_return: float, volatility: float, correlation: Dict[str, float] = None, description: Optional[str] = None, metadata: Dict[str, Any] = None, cost_basis: float = None, dividend_rate: float = 0.0, dividend_volatility: float = 0.0, tax_free: bool = False, liquid: bool = True, liquid_from_year: Optional[int] = None, dividend_reinvestment: bool = True, **kwargs):
        """Initialize Asset with support for additional fields in metadata."""
        # Store additional fields in metadata
        if metadata is None:
            metadata = {}
        if correlation is None:
            correlation = {}

        # Add any additional kwargs to metadata
        metadata.update(kwargs)

        # Set cost basis to current value if not specified
        if cost_basis is None:
            cost_basis = current_value

        # Use object.__setattr__ to set fields since this is a frozen dataclass
        object.__setattr__(self, 'name', name)
        object.__setattr__(self, 'asset_type', asset_type)
        object.__setattr__(self, 'current_value', current_value)
        object.__setattr__(self, 'expected_return', expected_return)
        object.__setattr__(self, 'volatility', volatility)
        object.__setattr__(self, 'correlation', correlation)
        object.__setattr__(self, 'description', description)
        object.__setattr__(self, 'metadata', metadata)
        object.__setattr__(self, 'cost_basis', cost_basis)
        object.__setattr__(self, 'dividend_rate', dividend_rate)
        object.__setattr__(self, 'dividend_volatility', dividend_volatility)
        object.__setattr__(self, 'tax_free', tax_free)
        object.__setattr__(self, 'liquid', liquid)
        object.__setattr__(self, 'liquid_from_year', liquid_from_year)
        object.__setattr__(self, 'dividend_reinvestment', dividend_reinvestment)

        # Run validation
        self.__post_init__()

    def __post_init__(self):
        """Validate asset data."""
        validator = Validator()
        validator.add_field_validator('name').add_rule(RequiredRule('name'))
        validator.add_field_validator('current_value').add_rule(RangeRule('current_value', min_value=0))
        validator.add_field_validator('expected_return').add_rule(RangeRule('expected_return', min_value=-1, max_value=2))
        validator.add_field_validator('volatility').add_rule(RangeRule('volatility', min_value=0, max_value=2))
        validator.add_field_validator('cost_basis').add_rule(RangeRule('cost_basis', min_value=0))
        validator.add_field_validator('dividend_rate').add_rule(RangeRule('dividend_rate', min_value=0, max_value=1))
        validator.add_field_validator('dividend_volatility').add_rule(RangeRule('dividend_volatility', min_value=0, max_value=1))

        result = validator.validate({
            'name': self.name,
            'current_value': self.current_value,
            'expected_return': self.expected_return,
            'volatility': self.volatility,
            'cost_basis': self.cost_basis,
            'dividend_rate': self.dividend_rate,
            'dividend_volatility': self.dividend_volatility
        })

        if not result.is_valid:
            raise ValidationError(f"Asset validation failed: {result.errors}")

    def get_metadata_field(self, field_name: str, default: Any = None) -> Any:
        """Get a field from metadata."""
        return self.metadata.get(field_name, default)

    def set_metadata_field(self, field_name: str, value: Any) -> None:
        """Set a field in metadata."""
        # Since this is a frozen dataclass, we need to create a new instance
        # This is a limitation of frozen dataclasses
        raise NotImplementedError("Cannot modify metadata in frozen dataclass")

    def get_metrics(self) -> AssetMetrics:
        """Get asset metrics."""
        sharpe_ratio = self.expected_return / self.volatility if self.volatility > 0 else None
        return AssetMetrics(
            expected_return=self.expected_return,
            volatility=self.volatility,
            correlation=self.correlation,
            sharpe_ratio=sharpe_ratio
        )

    def get_correlation(self, other_asset: str) -> float:
        """Get correlation with another asset."""
        return self.correlation.get(other_asset, 0.0)

    def get_tax_treatment(self) -> Dict[str, Any]:
        """Get tax treatment information for this asset."""
        return {
            'asset_type': self.asset_type.value,
            'tax_rate': self._get_tax_rate(),
            'tax_deferred': self._is_tax_deferred(),
            'tax_exempt': self._is_tax_exempt(),
            'tax_free': self.tax_free,
            'liquid': self.liquid,
            'liquid_from_year': self.liquid_from_year,
            'dividend_rate': self.dividend_rate,
            'dividend_reinvestment': self.dividend_reinvestment
        }

    def _get_tax_rate(self) -> float:
        """Get applicable tax rate for this asset."""
        if self.tax_free:
            return 0.0

        # Default implementation - subclasses should override
        if self.asset_type == AssetType.BOND:
            return 0.15  # Capital gains rate for bonds
        elif self.asset_type == AssetType.EQUITY:
            return 0.15  # Capital gains rate for equities
        else:
            return 0.25  # Ordinary income rate for other assets

    def _is_tax_deferred(self) -> bool:
        """Check if asset is tax-deferred."""
        return False

    def _is_tax_exempt(self) -> bool:
        """Check if asset is tax-exempt."""
        return False

    def is_liquid_at_year(self, year: int) -> bool:
        """Check if asset is liquid at the given year."""
        if not self.liquid:
            return False
        if self.liquid_from_year is not None:
            return year >= self.liquid_from_year
        return True

    def get_dividend_income(self, year: Optional[int] = None) -> float:
        """Get annual dividend/interest income with optional stochastic dividend rates."""
        if self.tax_free:
            return 0.0  # Tax-free assets don't generate taxable income

        # If dividend volatility is specified, generate stochastic dividend rate
        if self.dividend_volatility > 0 and year is not None:
            # Use year as seed for consistent random generation across scenarios
            np.random.seed(year)
            stochastic_dividend_rate = np.random.normal(self.dividend_rate, self.dividend_volatility)
            # Ensure dividend rate is non-negative and reasonable
            stochastic_dividend_rate = max(0.0, min(stochastic_dividend_rate, 0.5))
            return self.current_value * stochastic_dividend_rate

        # Default to fixed dividend rate
        return self.current_value * self.dividend_rate

    def get_capital_gains(self) -> float:
        """Get unrealized capital gains."""
        if self.tax_free:
            return 0.0  # Tax-free assets don't have capital gains
        return max(0.0, self.current_value - self.cost_basis)

    def get_capital_gains_rate(self) -> float:
        """Get capital gains tax rate."""
        if self.tax_free:
            return 0.0
        return 0.15  # Long-term capital gains rate

    def calculate_future_value(self, years: int, inflation_rate: float = 0.02) -> float:
        """Calculate future value of the asset."""
        real_return = self.expected_return - inflation_rate
        return self.current_value * (1 + real_return) ** years

    def calculate_risk_metrics(self, confidence_level: float = 0.95) -> Dict[str, float]:
        """Calculate risk metrics for the asset."""
        # Simplified VaR calculation assuming normal distribution
        z_score = 1.645 if confidence_level == 0.95 else 2.326  # 95% or 99%
        var = z_score * self.volatility * self.current_value

        return {
            'var': var,
            'volatility': self.volatility,
            'sharpe_ratio': self.expected_return / self.volatility if self.volatility > 0 else 0
        }


class AssetFactory:
    """Factory for creating asset instances."""

    @staticmethod
    def create_asset(asset_type: str, **kwargs) -> Asset:
        """Create an asset instance based on type."""
        try:
            asset_enum = AssetType.from_string(asset_type)
        except ValueError as e:
            raise AssetError(f"Invalid asset type: {asset_type}")

        # This would be expanded when specific asset classes are implemented
        return Asset(
            asset_type=asset_enum,
            **kwargs
        )

    @staticmethod
    def create_from_dict(data: Dict[str, Any]) -> Asset:
        """Create an asset from dictionary data."""
        required_fields = ['name', 'asset_type', 'current_value', 'expected_return', 'volatility']

        for field in required_fields:
            if field not in data:
                raise AssetError(f"Missing required field: {field}")

        return Asset(
            name=data['name'],
            asset_type=AssetType.from_string(data['asset_type']),
            current_value=data['current_value'],
            expected_return=data['expected_return'],
            volatility=data['volatility'],
            correlation=data.get('correlation', {}),
            description=data.get('description'),
            metadata=data.get('metadata', {}),
            cost_basis=data.get('cost_basis'),
            dividend_rate=data.get('dividend_rate', 0.0),
            dividend_volatility=data.get('dividend_volatility', 0.0),
            tax_free=data.get('tax_free', False),
            liquid=data.get('liquid', True),
            liquid_from_year=data.get('liquid_from_year'),
            dividend_reinvestment=data.get('dividend_reinvestment', True)
        )


@dataclass(frozen=True)
class AssetAllocation:
    """Represents an asset allocation strategy."""
    name: str
    allocations: Dict[str, float]  # asset_name -> percentage
    description: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)

    def __post_init__(self):
        """Validate allocation data."""
        validator = Validator()
        validator.add_field_validator('name').add_rule(RequiredRule('name'))

        # Validate individual allocations are between 0% and 100%
        for asset, allocation in self.allocations.items():
            if not (0 <= allocation <= 1):
                raise ValidationError(f"Allocation for {asset} must be between 0% and 100%, got {allocation * 100:.2f}%")
        # Validate allocations sum to 100%
        total_allocation = sum(self.allocations.values())
        if not (0.99 <= total_allocation <= 1.01):  # Allow small rounding errors
            raise ValidationError(f"Allocations must sum to 100%, got {total_allocation * 100:.2f}%")

        result = validator.validate({'name': self.name})
        if not result.is_valid:
            raise ValidationError(f"AssetAllocation validation failed: {result.errors}")

    def get_allocation(self, asset_name: str) -> float:
        """Get allocation percentage for a specific asset."""
        return self.allocations.get(asset_name, 0.0)

    def get_expected_return(self, assets: Dict[str, Asset]) -> float:
        """Calculate expected return for this allocation."""
        total_return = 0.0
        for asset_name, allocation in self.allocations.items():
            if asset_name in assets:
                total_return += allocation * assets[asset_name].expected_return
        return total_return

    def get_volatility(self, assets: Dict[str, Asset]) -> float:
        """Calculate portfolio volatility for this allocation."""
        # Simplified calculation - assumes correlation matrix is available
        variance = 0.0

        # Individual asset variances
        for asset_name, allocation in self.allocations.items():
            if asset_name in assets:
                asset = assets[asset_name]
                variance += (allocation ** 2) * (asset.volatility ** 2)

        # Cross-asset covariances (simplified)
        asset_names = list(self.allocations.keys())
        for i, asset_name1 in enumerate(asset_names):
            if asset_name1 not in assets:
                continue
            asset1 = assets[asset_name1]

            for j, asset_name2 in enumerate(asset_names[i+1:], i+1):
                if asset_name2 not in assets:
                    continue
                asset2 = assets[asset_name2]

                correlation = asset1.get_correlation(asset_name2)
                covariance = 2 * self.allocations[asset_name1] * self.allocations[asset_name2] * \
                           asset1.volatility * asset2.volatility * correlation
                variance += covariance

        return np.sqrt(variance)

    def rebalance(self, current_values: Dict[str, float], target_values: Dict[str, float]) -> Dict[str, float]:
        """Calculate rebalancing trades needed."""
        trades = {}
        total_current = sum(current_values.values())

        for asset_name, target_allocation in self.allocations.items():
            current_value = current_values.get(asset_name, 0.0)
            target_value = total_current * target_allocation
            trade_amount = target_value - current_value

            if abs(trade_amount) > 0.01:  # Only trade if difference is significant
                trades[asset_name] = trade_amount

        return trades