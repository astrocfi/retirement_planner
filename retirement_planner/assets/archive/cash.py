"""
Cash asset classes for retirement planning.

Contains a single CashEquivalent class with configuration for different cash types.
"""

from dataclasses import dataclass, field
from typing import Dict, Optional, Any
from datetime import date
from .base import Asset, AssetType


@dataclass(frozen=True)
class CashEquivalent(Asset):
    """Single cash class supporting all cash equivalents with configuration."""
    interest_rate: float = 0.0
    fdic_insured: bool = True
    minimum_balance: float = 0.0
    monthly_fee: float = 0.0
    liquidity_score: float = 1.0  # 0 = illiquid, 1 = highly liquid
    account_type: str = "savings"  # savings, checking, cd, money_market
    term_length: Optional[int] = None  # For CDs
    early_withdrawal_penalty: float = 0.0  # For CDs
    compounding_frequency: int = 1  # 1 = annual, 12 = monthly
    check_writing_limit: Optional[int] = None  # For money market accounts
    unlimited_transactions: bool = False  # For checking accounts

    def __init__(self, name: str, current_value: float, expected_return: float, volatility: float, interest_rate: float = 0.0, fdic_insured: bool = True, minimum_balance: float = 0.0, monthly_fee: float = 0.0, liquidity_score: float = 1.0, account_type: str = "savings", term_length: Optional[int] = None, early_withdrawal_penalty: float = 0.0, compounding_frequency: int = 1, check_writing_limit: Optional[int] = None, unlimited_transactions: bool = False, **kwargs):
        """Initialize CashEquivalent with asset_type automatically set."""
        # Store cash-specific fields in metadata
        metadata = {
            'interest_rate': interest_rate,
            'fdic_insured': fdic_insured,
            'minimum_balance': minimum_balance,
            'monthly_fee': monthly_fee,
            'liquidity_score': liquidity_score,
            'account_type': account_type,
            'term_length': term_length,
            'early_withdrawal_penalty': early_withdrawal_penalty,
            'compounding_frequency': compounding_frequency,
            'check_writing_limit': check_writing_limit,
            'unlimited_transactions': unlimited_transactions
        }
        metadata.update(kwargs)

        # Call parent constructor
        super().__init__(
            name=name,
            asset_type=AssetType.CASH,
            current_value=current_value,
            expected_return=expected_return,
            volatility=volatility,
            metadata=metadata
        )

    def __post_init__(self):
        """Validate cash equivalent specific data."""
        # Get fields from metadata
        interest_rate = self.get_metadata_field('interest_rate', 0.0)
        minimum_balance = self.get_metadata_field('minimum_balance', 0.0)
        monthly_fee = self.get_metadata_field('monthly_fee', 0.0)
        liquidity_score = self.get_metadata_field('liquidity_score', 1.0)
        account_type = self.get_metadata_field('account_type', 'savings')
        term_length = self.get_metadata_field('term_length')
        early_withdrawal_penalty = self.get_metadata_field('early_withdrawal_penalty', 0.0)

        # Additional validation for cash equivalent specific fields
        if not (0 <= interest_rate <= 0.2):  # Max 20% interest rate
            raise ValueError("Interest rate must be between 0% and 20%")

        if minimum_balance < 0:
            raise ValueError("Minimum balance must be non-negative")

        if monthly_fee < 0:
            raise ValueError("Monthly fee must be non-negative")

        if not (0 <= liquidity_score <= 1):
            raise ValueError("Liquidity score must be between 0 and 1")

        if account_type not in ['savings', 'checking', 'cd', 'money_market']:
            raise ValueError("Account type must be 'savings', 'checking', 'cd', or 'money_market'")

        if term_length is not None and term_length <= 0:
            raise ValueError("Term length must be positive")

        if not (0 <= early_withdrawal_penalty <= 1):  # Max 100% penalty
            raise ValueError("Early withdrawal penalty must be between 0% and 100%")

    def _get_tax_rate(self) -> float:
        """Get tax rate for cash investments."""
        return 0.25  # Ordinary income rate for interest

    def get_annual_interest_income(self) -> float:
        """Calculate annual interest income."""
        interest_rate = self.get_metadata_field('interest_rate', 0.0)
        return self.current_value * interest_rate

    def get_net_interest_income(self) -> float:
        """Calculate net interest income after fees."""
        annual_interest = self.get_annual_interest_income()
        monthly_fee = self.get_metadata_field('monthly_fee', 0.0)
        annual_fees = monthly_fee * 12
        return annual_interest - annual_fees

    def get_effective_annual_yield(self) -> float:
        """Calculate effective annual yield considering compounding."""
        interest_rate = self.get_metadata_field('interest_rate', 0.0)
        compounding_frequency = self.get_metadata_field('compounding_frequency', 1)

        if compounding_frequency == 1:
            return interest_rate

        # Calculate effective annual yield with compounding
        # EAY = (1 + r/n)^n - 1 where r = interest_rate, n = compounding_frequency
        return (1 + interest_rate / compounding_frequency) ** compounding_frequency - 1

    def get_liquidity_penalty(self) -> float:
        """Calculate liquidity penalty based on liquidity score."""
        liquidity_score = self.get_metadata_field('liquidity_score', 1.0)
        if liquidity_score >= 0.9:
            return 0.0  # No penalty for highly liquid accounts

        # Illiquid accounts get a penalty (as a percentage)
        return (1 - liquidity_score) * 0.01

    def get_early_withdrawal_penalty(self) -> float:
        """Calculate early withdrawal penalty for CDs."""
        account_type = self.get_metadata_field('account_type', 'savings')
        early_withdrawal_penalty = self.get_metadata_field('early_withdrawal_penalty', 0.0)

        if account_type == 'cd':
            return self.current_value * early_withdrawal_penalty
        return 0.0

    def get_net_return_after_fees(self) -> float:
        """Calculate net return after all fees and penalties."""
        gross_interest = self.get_annual_interest_income()
        monthly_fee = self.get_metadata_field('monthly_fee', 0.0)
        annual_fees = monthly_fee * 12
        liquidity_penalty_rate = self.get_liquidity_penalty()
        liquidity_penalty = self.current_value * liquidity_penalty_rate
        net_income = gross_interest - annual_fees - liquidity_penalty
        return net_income / self.current_value if self.current_value > 0 else 0.0

    def get_fdic_coverage(self) -> float:
        """Get FDIC coverage amount."""
        fdic_insured = self.get_metadata_field('fdic_insured', True)
        if fdic_insured:
            return 250000.0  # Standard FDIC limit
        return 0.0

    def get_risk_adjusted_return(self, risk_free_rate: float = 0.02) -> float:
        """Calculate risk-adjusted return using Sharpe ratio."""
        return (self.get_net_return_after_fees() - risk_free_rate) / self.volatility if self.volatility > 0 else 0.0

    def get_tax_treatment(self) -> Dict[str, Any]:
        """Get tax treatment for cash investments."""
        base_treatment = super().get_tax_treatment()

        # Get fields from metadata
        fdic_insured = self.get_metadata_field('fdic_insured', True)
        account_type = self.get_metadata_field('account_type', 'savings')
        liquidity_score = self.get_metadata_field('liquidity_score', 1.0)

        base_treatment.update({
            'interest_taxable': True,
            'fdic_insured': fdic_insured,
            'account_type': account_type,
            'liquidity_score': liquidity_score
        })
        return base_treatment

    def get_after_tax_yield(self, marginal_tax_rate: float) -> float:
        """Calculate after-tax yield."""
        # Check if this is a tax-deferred account
        if self.get_metadata_field('tax_deferred', False):
            return self.get_net_return_after_fees()  # No taxes until withdrawal
        return self.get_net_return_after_fees() * (1 - marginal_tax_rate)

    def get_equivalent_taxable_yield(self, marginal_tax_rate: float) -> float:
        """Calculate equivalent taxable yield for tax-deferred accounts."""
        # Check if this is a tax-deferred account
        if self.get_metadata_field('tax_deferred', False):
            tax_deferred_yield = self.get_net_return_after_fees()
            return tax_deferred_yield / (1 - marginal_tax_rate)
        # For cash accounts, this is the same as net return since they're typically taxable
        return self.get_net_return_after_fees()