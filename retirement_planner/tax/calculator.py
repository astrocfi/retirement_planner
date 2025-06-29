"""
Tax calculation system for retirement planning simulation.

This module provides comprehensive tax calculations including federal and state taxes,
capital gains, dividend income, and Social Security taxation.
"""

from typing import Dict, List, Any, Optional
from dataclasses import dataclass
from abc import ABC, abstractmethod

from retirement_planner.assets.base import Asset
from retirement_planner.tax.federal import USFederalTax
from retirement_planner.tax.state import CaliforniaTax
from retirement_planner.core.exceptions import SimulationError


@dataclass
class TaxResult:
    """Result of tax calculations for a year."""
    federal_income_tax: float = 0.0
    federal_capital_gains_tax: float = 0.0
    state_income_tax: float = 0.0
    state_capital_gains_tax: float = 0.0
    total_tax: float = 0.0
    effective_tax_rate: float = 0.0
    taxable_income: float = 0.0
    capital_gains: float = 0.0
    social_security_taxable: float = 0.0


class TaxCalculator:
    """Comprehensive tax calculator for retirement simulation."""

    def __init__(self, filing_status: str = "single", state: str = "CA"):
        """Initialize tax calculator."""
        if filing_status != "single":
            raise SimulationError("Only single filing status is currently supported")

        if state != "CA":
            raise SimulationError("Only California state taxes are currently supported")

        self.filing_status = filing_status
        self.state = state
        self.federal_tax = USFederalTax()
        self.state_tax = CaliforniaTax()

        # Social Security taxation thresholds (2024)
        self.ss_tax_threshold_1 = 25000  # First threshold for single filers
        self.ss_tax_threshold_2 = 34000  # Second threshold for single filers

    def calculate_annual_taxes(
        self,
        year: int,
        income_events: List[float],
        assets: List[Asset],
        sold_assets: Dict[str, float],  # asset_name -> amount_sold
        social_security_income: float = 0.0
    ) -> TaxResult:
        """Calculate all taxes for a given year."""

        # Calculate dividend/interest income from assets
        dividend_income = sum(asset.get_dividend_income() for asset in assets)

        # Calculate capital gains from sold assets
        capital_gains = self._calculate_capital_gains_from_sales(assets, sold_assets)

        # Calculate Social Security taxation
        social_security_taxable = self._calculate_social_security_taxable(
            income_events, dividend_income, capital_gains, social_security_income
        )

        # Total taxable income
        total_income = sum(income_events) + dividend_income + social_security_taxable

        # Calculate federal taxes
        federal_income_tax = self.federal_tax.calculate_income_tax(
            total_income, self.filing_status
        )
        federal_capital_gains_tax = self.federal_tax.calculate_capital_gains_tax(
            capital_gains, long_term=True
        )

        # Calculate state taxes - California treats capital gains as regular income
        # So we combine all income including capital gains for tax bracket determination
        total_income_for_state_tax = total_income + capital_gains
        state_total_tax = self.state_tax.calculate_income_tax(
            total_income_for_state_tax, self.filing_status
        )

        # For reporting purposes, we need to separate the tax on regular income vs capital gains
        # We'll calculate the proportion of tax that applies to capital gains
        if total_income_for_state_tax > 0:
            capital_gains_proportion = capital_gains / total_income_for_state_tax
            state_capital_gains_tax = state_total_tax * capital_gains_proportion
            state_income_tax = state_total_tax - state_capital_gains_tax
        else:
            state_capital_gains_tax = 0.0
            state_income_tax = 0.0

        # Calculate totals
        total_tax = (federal_income_tax + federal_capital_gains_tax +
                    state_income_tax + state_capital_gains_tax)

        effective_tax_rate = total_tax / total_income if total_income > 0 else 0.0

        return TaxResult(
            federal_income_tax=federal_income_tax,
            federal_capital_gains_tax=federal_capital_gains_tax,
            state_income_tax=state_income_tax,
            state_capital_gains_tax=state_capital_gains_tax,
            total_tax=total_tax,
            effective_tax_rate=effective_tax_rate,
            taxable_income=total_income,
            capital_gains=capital_gains,
            social_security_taxable=social_security_taxable
        )

    def _calculate_capital_gains_from_sales(
        self,
        assets: List[Asset],
        sold_assets: Dict[str, float]
    ) -> float:
        """Calculate capital gains from asset sales."""
        total_gains = 0.0

        for asset in assets:
            if asset.name in sold_assets:
                amount_sold = sold_assets[asset.name]
                if amount_sold > 0 and asset.current_value > 0:
                    # Calculate proportion of asset sold
                    proportion_sold = amount_sold / asset.current_value

                    # Calculate capital gains on the sold portion
                    gains = asset.get_capital_gains() * proportion_sold
                    total_gains += gains

        return total_gains

    def _calculate_social_security_taxable(
        self,
        income_events: List[float],
        dividend_income: float,
        capital_gains: float,
        social_security_income: float
    ) -> float:
        """Calculate taxable portion of Social Security benefits."""
        if social_security_income <= 0:
            return 0.0

        # Calculate combined income (AGI + tax-exempt interest + 50% of SS)
        combined_income = sum(income_events) + dividend_income + capital_gains + (0.5 * social_security_income)

        # Determine taxable portion based on thresholds
        if combined_income <= self.ss_tax_threshold_1:
            return 0.0
        elif combined_income <= self.ss_tax_threshold_2:
            # 50% of SS benefits are taxable
            return 0.5 * social_security_income
        else:
            # 85% of SS benefits are taxable
            return 0.85 * social_security_income

    def calculate_withdrawal_tax_impact(
        self,
        assets: List[Asset],
        withdrawal_amount: float,
        year: int
    ) -> Dict[str, Any]:
        """Calculate tax impact of withdrawing from portfolio."""
        # Get liquid assets
        liquid_assets = [asset for asset in assets if asset.is_liquid_at_year(year)]

        if not liquid_assets:
            raise SimulationError("No liquid assets available for withdrawal")

        # Calculate proportional withdrawal
        total_liquid_value = sum(asset.current_value for asset in liquid_assets)
        if total_liquid_value == 0:
            raise SimulationError("No liquid assets have value")

        # Calculate how much needs to be sold to get the withdrawal amount after taxes
        # This is an iterative process since taxes depend on the amount sold
        target_after_tax = withdrawal_amount
        estimated_sale_amount = target_after_tax * 1.2  # Initial estimate

        # Add bounds to prevent infinite loops
        max_sale_amount = total_liquid_value * 2.0  # Never sell more than 2x total value
        min_sale_amount = target_after_tax * 0.5    # Never sell less than 50% of target

        for iteration in range(10):  # Increased max iterations with better bounds
            # Calculate capital gains on estimated sale
            sold_assets = {}
            for asset in liquid_assets:
                proportion = asset.current_value / total_liquid_value
                sold_amount = estimated_sale_amount * proportion
                sold_assets[asset.name] = sold_amount

            # Calculate taxes
            tax_result = self.calculate_annual_taxes(
                year=year,
                income_events=[],
                assets=assets,
                sold_assets=sold_assets
            )

            # Calculate after-tax amount
            after_tax_amount = estimated_sale_amount - tax_result.federal_capital_gains_tax - tax_result.state_capital_gains_tax

            # Check for convergence
            if abs(after_tax_amount - target_after_tax) < 0.01:
                break

            # Prevent division by zero or very small numbers
            if after_tax_amount <= 0.01:
                # If after-tax amount is too small, increase the estimate significantly
                estimated_sale_amount = min(estimated_sale_amount * 2.0, max_sale_amount)
            else:
                # Adjust estimate with bounds
                adjustment_factor = target_after_tax / after_tax_amount
                # Limit the adjustment factor to prevent wild swings
                adjustment_factor = max(0.5, min(2.0, adjustment_factor))
                estimated_sale_amount = estimated_sale_amount * adjustment_factor

            # Apply bounds
            estimated_sale_amount = max(min_sale_amount, min(max_sale_amount, estimated_sale_amount))

        return {
            'gross_withdrawal': estimated_sale_amount,
            'net_withdrawal': after_tax_amount,
            'federal_capital_gains_tax': tax_result.federal_capital_gains_tax,
            'state_capital_gains_tax': tax_result.state_capital_gains_tax,
            'total_capital_gains_tax': tax_result.federal_capital_gains_tax + tax_result.state_capital_gains_tax,
            'sold_assets': sold_assets
        }