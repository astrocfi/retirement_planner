"""
Cash asset classes for retirement planning.

Contains cash equivalents, money market, and CD implementations.
"""

from dataclasses import dataclass, field
from typing import Dict, Optional, Any
from datetime import date
from .base import Asset, AssetType


@dataclass(frozen=True)
class Cash(Asset):
    """Base cash class with common cash functionality."""
    interest_rate: float = 0.0
    fdic_insured: bool = True
    minimum_balance: float = 0.0
    monthly_fee: float = 0.0

    def __post_init__(self):
        """Validate cash-specific data."""
        # Set asset type before calling parent validation
        object.__setattr__(self, 'asset_type', AssetType.CASH)
        super().__post_init__()

        # Additional validation
        if not (0 <= self.interest_rate <= 0.1):  # Max 10% interest rate
            raise ValueError("Interest rate must be between 0% and 10%")

        if self.minimum_balance < 0:
            raise ValueError("Minimum balance cannot be negative")

        if self.monthly_fee < 0:
            raise ValueError("Monthly fee cannot be negative")

    def _get_tax_rate(self) -> float:
        """Get tax rate for cash investments."""
        return 0.25  # Ordinary income rate for interest

    def get_annual_interest(self) -> float:
        """Calculate annual interest income."""
        return self.current_value * self.interest_rate

    def get_net_annual_return(self) -> float:
        """Calculate net annual return after fees."""
        annual_interest = self.get_annual_interest()
        annual_fees = self.monthly_fee * 12
        return annual_interest - annual_fees

    def get_effective_yield(self) -> float:
        """Calculate effective yield considering fees and minimum balance."""
        if self.current_value < self.minimum_balance:
            return 0.0  # No interest if below minimum balance

        net_return = self.get_net_annual_return()
        return net_return / self.current_value if self.current_value > 0 else 0.0

    def is_tax_exempt(self) -> bool:
        """Check if cash investment is tax-exempt."""
        return False

    def get_tax_treatment(self) -> Dict[str, Any]:
        """Get tax treatment for cash investments."""
        base_treatment = super().get_tax_treatment()
        base_treatment.update({
            'interest_taxable': True,
            'fdic_insured': self.fdic_insured,
            'minimum_balance': self.minimum_balance,
            'monthly_fee': self.monthly_fee
        })
        return base_treatment


@dataclass(frozen=True)
class MoneyMarket(Cash):
    """Money market account implementation."""
    account_type: str = "Savings"  # Savings, Checking, Investment
    check_writing: bool = False
    atm_access: bool = True
    online_banking: bool = True

    def __post_init__(self):
        """Validate money market data."""
        # Set asset type before calling parent validation
        object.__setattr__(self, 'asset_type', AssetType.CASH)
        super().__post_init__()

    def get_liquidity_score(self) -> float:
        """Get liquidity score for money market account."""
        score = 0.9  # Base liquidity score

        if self.check_writing:
            score += 0.05
        if self.atm_access:
            score += 0.03
        if self.online_banking:
            score += 0.02

        return min(score, 1.0)

    def get_transaction_limits(self) -> Dict[str, Any]:
        """Get transaction limits for money market account."""
        limits = {
            'monthly_withdrawals': 6 if self.account_type == "Savings" else float('inf'),
            'minimum_check_amount': 500 if self.check_writing else None,
            'atm_fee': 0 if self.atm_access else None
        }
        return limits

    def get_tax_treatment(self) -> Dict[str, Any]:
        """Get tax treatment for money market accounts."""
        base_treatment = super().get_tax_treatment()
        base_treatment.update({
            'account_type': self.account_type,
            'check_writing': self.check_writing,
            'atm_access': self.atm_access,
            'liquidity_score': self.get_liquidity_score()
        })
        return base_treatment


@dataclass(frozen=True)
class CD(Cash):
    """Certificate of Deposit implementation."""
    term_length: int = 12  # months
    maturity_date: Optional[date] = None
    early_withdrawal_penalty: float = 0.0
    auto_renewal: bool = True
    callable: bool = False

    def __post_init__(self):
        """Validate CD data."""
        # Set asset type before calling parent validation
        object.__setattr__(self, 'asset_type', AssetType.CASH)
        super().__post_init__()

        # Additional validation
        if not (1 <= self.term_length <= 120):  # 1 month to 10 years
            raise ValueError("Term length must be between 1 and 120 months")

        if not (0 <= self.early_withdrawal_penalty <= 0.12):  # Max 12 months penalty
            raise ValueError("Early withdrawal penalty must be between 0 and 12 months")

    def get_annualized_yield(self) -> float:
        """Calculate annualized yield for CD."""
        # Convert monthly rate to annual rate
        monthly_rate = self.interest_rate / 12
        annualized_rate = (1 + monthly_rate) ** 12 - 1
        return annualized_rate

    def get_early_withdrawal_cost(self, months_early: int) -> float:
        """Calculate cost of early withdrawal."""
        if months_early <= 0:
            return 0.0

        # Simplified penalty calculation
        penalty_months = min(months_early, self.early_withdrawal_penalty)
        penalty_rate = penalty_months / 12
        return self.current_value * penalty_rate

    def get_liquidity_score(self) -> float:
        """Get liquidity score for CD."""
        # CDs are less liquid due to early withdrawal penalties
        base_score = 0.3  # Base liquidity for CDs

        # Shorter terms are more liquid
        if self.term_length <= 6:
            base_score += 0.2
        elif self.term_length <= 12:
            base_score += 0.1

        # Lower penalties increase liquidity
        if self.early_withdrawal_penalty <= 3:
            base_score += 0.1

        return min(base_score, 0.8)  # Max 80% liquidity for CDs

    def get_maturity_value(self) -> float:
        """Calculate value at maturity."""
        annualized_rate = self.get_annualized_yield()
        years = self.term_length / 12
        return self.current_value * (1 + annualized_rate) ** years

    def get_tax_treatment(self) -> Dict[str, Any]:
        """Get tax treatment for CDs."""
        base_treatment = super().get_tax_treatment()
        base_treatment.update({
            'term_length': self.term_length,
            'maturity_date': self.maturity_date,
            'early_withdrawal_penalty': self.early_withdrawal_penalty,
            'auto_renewal': self.auto_renewal,
            'callable': self.callable,
            'liquidity_score': self.get_liquidity_score()
        })
        return base_treatment