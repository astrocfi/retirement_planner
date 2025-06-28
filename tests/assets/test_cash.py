"""
Tests for cash asset classes.
"""

import pytest
from datetime import date, timedelta
from retirement_planner.assets.cash import CashEquivalent
from retirement_planner.assets.base import AssetType
from retirement_planner.core.exceptions import ValidationError


class TestCashEquivalent:
    """Test CashEquivalent class functionality."""

    def test_cash_equivalent_creation_basic(self):
        """Test creating a basic cash equivalent asset."""
        cash = CashEquivalent(
            name="Savings Account",
            current_value=25000.0,
            expected_return=0.02,
            volatility=0.01
        )
        assert cash.name == "Savings Account"
        assert cash.asset_type == AssetType.CASH
        assert cash.current_value == 25000.0
        assert cash.expected_return == 0.02
        assert cash.volatility == 0.01
        assert cash.get_metadata_field('interest_rate') == 0.0
        assert cash.get_metadata_field('fdic_insured') is True
        assert cash.get_metadata_field('account_type') == "savings"

    def test_cash_equivalent_creation_savings(self):
        """Test creating a savings account."""
        cash = CashEquivalent(
            name="High Yield Savings",
            current_value=50000.0,
            expected_return=0.035,
            volatility=0.01,
            interest_rate=0.035,
            fdic_insured=True,
            minimum_balance=1000.0,
            monthly_fee=0.0,
            liquidity_score=1.0,
            account_type="savings"
        )
        assert cash.get_metadata_field('interest_rate') == 0.035
        assert cash.get_metadata_field('fdic_insured') is True
        assert cash.get_metadata_field('minimum_balance') == 1000.0
        assert cash.get_metadata_field('monthly_fee') == 0.0
        assert cash.get_metadata_field('liquidity_score') == 1.0
        assert cash.get_metadata_field('account_type') == "savings"

    def test_cash_equivalent_creation_cd(self):
        """Test creating a certificate of deposit."""
        maturity_date = date.today() + timedelta(days=365)
        cash = CashEquivalent(
            name="1-Year CD",
            current_value=100000.0,
            expected_return=0.045,
            volatility=0.005,
            interest_rate=0.045,
            fdic_insured=True,
            minimum_balance=10000.0,
            liquidity_score=0.3,
            account_type="cd",
            term_length=365,
            maturity_date=maturity_date,
            early_withdrawal_penalty=0.06
        )
        assert cash.get_metadata_field('account_type') == "cd"
        assert cash.get_metadata_field('term_length') == 365
        assert cash.get_metadata_field('maturity_date') == maturity_date
        assert cash.get_metadata_field('early_withdrawal_penalty') == 0.06
        assert cash.get_metadata_field('liquidity_score') == 0.3

    def test_cash_equivalent_creation_money_market(self):
        """Test creating a money market account."""
        cash = CashEquivalent(
            name="Money Market Account",
            current_value=75000.0,
            expected_return=0.04,
            volatility=0.008,
            interest_rate=0.04,
            fdic_insured=True,
            minimum_balance=2500.0,
            monthly_fee=12.0,
            liquidity_score=0.9,
            account_type="money_market",
            check_writing_limit=3
        )
        assert cash.get_metadata_field('account_type') == "money_market"
        assert cash.get_metadata_field('check_writing_limit') == 3
        assert cash.get_metadata_field('liquidity_score') == 0.9

    def test_cash_equivalent_creation_checking(self):
        """Test creating a checking account."""
        cash = CashEquivalent(
            name="Interest Checking",
            current_value=15000.0,
            expected_return=0.01,
            volatility=0.002,
            interest_rate=0.01,
            fdic_insured=True,
            minimum_balance=1500.0,
            monthly_fee=0.0,
            liquidity_score=1.0,
            account_type="checking",
            unlimited_transactions=True
        )
        assert cash.get_metadata_field('account_type') == "checking"
        assert cash.get_metadata_field('unlimited_transactions') is True
        assert cash.get_metadata_field('liquidity_score') == 1.0

    def test_cash_equivalent_validation_invalid_interest_rate(self):
        """Test cash equivalent validation with invalid interest rate."""
        with pytest.raises(ValueError, match="Interest rate must be between 0% and 20%"):
            CashEquivalent(
                name="Test Account",
                current_value=10000.0,
                expected_return=0.02,
                volatility=0.01,
                interest_rate=0.25  # 25% interest rate
            )

    def test_cash_equivalent_validation_invalid_minimum_balance(self):
        """Test cash equivalent validation with invalid minimum balance."""
        with pytest.raises(ValueError, match="Minimum balance must be non-negative"):
            CashEquivalent(
                name="Test Account",
                current_value=10000.0,
                expected_return=0.02,
                volatility=0.01,
                minimum_balance=-1000.0
            )

    def test_cash_equivalent_validation_invalid_monthly_fee(self):
        """Test cash equivalent validation with invalid monthly fee."""
        with pytest.raises(ValueError, match="Monthly fee must be non-negative"):
            CashEquivalent(
                name="Test Account",
                current_value=10000.0,
                expected_return=0.02,
                volatility=0.01,
                monthly_fee=-50.0
            )

    def test_cash_equivalent_validation_invalid_liquidity_score(self):
        """Test cash equivalent validation with invalid liquidity score."""
        with pytest.raises(ValueError, match="Liquidity score must be between 0 and 1"):
            CashEquivalent(
                name="Test Account",
                current_value=10000.0,
                expected_return=0.02,
                volatility=0.01,
                liquidity_score=1.5  # Invalid liquidity score
            )

    def test_cash_equivalent_validation_invalid_account_type(self):
        """Test cash equivalent validation with invalid account type."""
        with pytest.raises(ValueError, match="Account type must be 'savings', 'checking', 'cd', or 'money_market'"):
            CashEquivalent(
                name="Test Account",
                current_value=10000.0,
                expected_return=0.02,
                volatility=0.01,
                account_type="invalid"
            )

    def test_cash_equivalent_validation_invalid_term_length(self):
        """Test cash equivalent validation with invalid term length."""
        with pytest.raises(ValueError, match="Term length must be positive"):
            CashEquivalent(
                name="Test CD",
                current_value=10000.0,
                expected_return=0.02,
                volatility=0.01,
                account_type="cd",
                term_length=0
            )

    def test_cash_equivalent_validation_invalid_early_withdrawal_penalty(self):
        """Test cash equivalent validation with invalid early withdrawal penalty."""
        with pytest.raises(ValueError, match="Early withdrawal penalty must be between 0% and 100%"):
            CashEquivalent(
                name="Test CD",
                current_value=10000.0,
                expected_return=0.02,
                volatility=0.01,
                account_type="cd",
                early_withdrawal_penalty=1.5  # 150% penalty
            )

    def test_get_annual_interest_income(self):
        """Test calculating annual interest income."""
        cash = CashEquivalent(
            name="High Yield Savings",
            current_value=50000.0,
            expected_return=0.035,
            volatility=0.01,
            interest_rate=0.035
        )
        interest_income = cash.get_annual_interest_income()
        assert interest_income == pytest.approx(1750.0, rel=1e-10)  # 50000 * 0.035

    def test_get_net_interest_income(self):
        """Test calculating net interest income after fees."""
        cash = CashEquivalent(
            name="Money Market Account",
            current_value=75000.0,
            expected_return=0.04,
            volatility=0.008,
            interest_rate=0.04,
            monthly_fee=12.0
        )
        net_interest_income = cash.get_net_interest_income()
        gross_interest = 75000.0 * 0.04  # 3000
        annual_fees = 12.0 * 12  # 144
        expected_net = gross_interest - annual_fees  # 3000 - 144 = 2856
        assert net_interest_income == expected_net

    def test_get_effective_annual_yield(self):
        """Test calculating effective annual yield."""
        cash = CashEquivalent(
            name="High Yield Savings",
            current_value=50000.0,
            expected_return=0.035,
            volatility=0.01,
            interest_rate=0.035
        )
        effective_yield = cash.get_effective_annual_yield()
        # For simple interest, EAY = interest_rate
        assert effective_yield == 0.035

    def test_get_effective_annual_yield_compounded(self):
        """Test calculating effective annual yield with compounding."""
        cash = CashEquivalent(
            name="Compounded Savings",
            current_value=50000.0,
            expected_return=0.035,
            volatility=0.01,
            interest_rate=0.034,
            compounding_frequency=12  # Monthly compounding
        )
        effective_yield = cash.get_effective_annual_yield()
        # EAY = (1 + r/n)^n - 1 where r = 0.034, n = 12
        expected_eay = (1 + 0.034/12)**12 - 1
        assert effective_yield == pytest.approx(expected_eay, rel=1e-3)

    def test_get_liquidity_penalty_high_liquidity(self):
        """Test liquidity penalty for highly liquid accounts."""
        cash = CashEquivalent(
            name="Checking Account",
            current_value=15000.0,
            expected_return=0.01,
            volatility=0.002,
            liquidity_score=1.0
        )
        liquidity_penalty = cash.get_liquidity_penalty()
        assert liquidity_penalty == 0.0  # No penalty for highly liquid accounts

    def test_get_liquidity_penalty_low_liquidity(self):
        """Test liquidity penalty for low liquidity accounts."""
        cash = CashEquivalent(
            name="CD",
            current_value=100000.0,
            expected_return=0.045,
            volatility=0.005,
            liquidity_score=0.3
        )
        liquidity_penalty = cash.get_liquidity_penalty()
        expected_penalty = (1 - 0.3) * 0.01  # 0.007
        assert liquidity_penalty == pytest.approx(expected_penalty, rel=1e-10)

    def test_get_early_withdrawal_penalty_cd(self):
        """Test early withdrawal penalty for CDs."""
        cash = CashEquivalent(
            name="1-Year CD",
            current_value=100000.0,
            expected_return=0.045,
            volatility=0.005,
            account_type="cd",
            early_withdrawal_penalty=0.06
        )
        penalty = cash.get_early_withdrawal_penalty()
        assert penalty == 6000.0  # 100000 * 0.06

    def test_get_early_withdrawal_penalty_savings(self):
        """Test early withdrawal penalty for savings accounts."""
        cash = CashEquivalent(
            name="Savings Account",
            current_value=25000.0,
            expected_return=0.02,
            volatility=0.01,
            account_type="savings"
        )
        penalty = cash.get_early_withdrawal_penalty()
        assert penalty == 0.0  # No penalty for savings accounts

    def test_get_net_return_after_fees(self):
        """Test calculating net return after all fees and penalties."""
        cash = CashEquivalent(
            name="Money Market Account",
            current_value=75000.0,
            expected_return=0.04,
            volatility=0.008,
            interest_rate=0.04,
            monthly_fee=12.0,
            liquidity_score=0.9
        )
        net_return = cash.get_net_return_after_fees()
        gross_interest = 75000.0 * 0.04  # 3000
        annual_fees = 12.0 * 12  # 144
        # No liquidity penalty for liquidity_score >= 0.9
        net_income = gross_interest - annual_fees  # 3000 - 144 = 2856
        expected_return = net_income / 75000.0  # 0.03808
        assert net_return == pytest.approx(expected_return, rel=1e-10)

    def test_get_fdic_coverage(self):
        """Test FDIC coverage calculation."""
        cash = CashEquivalent(
            name="FDIC Insured Account",
            current_value=300000.0,
            expected_return=0.02,
            volatility=0.01,
            fdic_insured=True
        )
        fdic_coverage = cash.get_fdic_coverage()
        assert fdic_coverage == 250000.0  # Standard FDIC limit

    def test_get_fdic_coverage_uninsured(self):
        """Test FDIC coverage for uninsured accounts."""
        cash = CashEquivalent(
            name="Uninsured Account",
            current_value=300000.0,
            expected_return=0.02,
            volatility=0.01,
            fdic_insured=False
        )
        fdic_coverage = cash.get_fdic_coverage()
        assert fdic_coverage == 0.0

    def test_get_risk_adjusted_return(self):
        """Test calculating risk-adjusted return."""
        cash = CashEquivalent(
            name="High Yield Savings",
            current_value=50000.0,
            expected_return=0.035,
            volatility=0.01,
            interest_rate=0.035
        )
        risk_adjusted_return = cash.get_risk_adjusted_return(risk_free_rate=0.02)
        # Sharpe ratio = (return - risk_free_rate) / volatility
        expected_sharpe = (0.035 - 0.02) / 0.01  # 1.5
        assert risk_adjusted_return == expected_sharpe

    def test_get_tax_treatment_taxable(self):
        """Test tax treatment for taxable cash accounts."""
        cash = CashEquivalent(
            name="Taxable Savings",
            current_value=50000.0,
            expected_return=0.035,
            volatility=0.01,
            interest_rate=0.035,
            fdic_insured=True,
            account_type="savings"
        )
        tax_treatment = cash.get_tax_treatment()
        assert tax_treatment['interest_taxable'] is True
        assert tax_treatment['fdic_insured'] is True
        assert tax_treatment['account_type'] == "savings"
        assert tax_treatment['liquidity_score'] == 1.0

    def test_get_tax_treatment_tax_deferred(self):
        """Test tax treatment for tax-deferred cash accounts."""
        cash = CashEquivalent(
            name="IRA Savings",
            current_value=50000.0,
            expected_return=0.035,
            volatility=0.01,
            interest_rate=0.035,
            fdic_insured=True,
            account_type="savings",
            tax_deferred=True
        )
        tax_treatment = cash.get_tax_treatment()
        assert tax_treatment['interest_taxable'] is True  # Still taxable, just deferred
        assert tax_treatment['fdic_insured'] is True
        assert tax_treatment['account_type'] == "savings"
        assert tax_treatment['liquidity_score'] == 1.0

    def test_get_after_tax_yield_taxable(self):
        """Test after-tax yield for taxable accounts."""
        cash = CashEquivalent(
            name="Taxable Savings",
            current_value=50000.0,
            expected_return=0.035,
            volatility=0.01,
            interest_rate=0.035
        )
        after_tax_yield = cash.get_after_tax_yield(marginal_tax_rate=0.25)
        expected_yield = 0.035 * (1 - 0.25)  # 0.035 * 0.75 = 0.02625
        assert after_tax_yield == expected_yield

    def test_get_after_tax_yield_tax_deferred(self):
        """Test after-tax yield for tax-deferred accounts."""
        cash = CashEquivalent(
            name="IRA Savings",
            current_value=50000.0,
            expected_return=0.035,
            volatility=0.01,
            interest_rate=0.035,
            tax_deferred=True
        )
        after_tax_yield = cash.get_after_tax_yield(marginal_tax_rate=0.25)
        assert after_tax_yield == pytest.approx(cash.get_net_return_after_fees(), rel=1e-10)  # No taxes until withdrawal

    def test_get_equivalent_taxable_yield_tax_deferred(self):
        """Test equivalent taxable yield for tax-deferred accounts."""
        cash = CashEquivalent(
            name="IRA Savings",
            current_value=50000.0,
            expected_return=0.035,
            volatility=0.01,
            interest_rate=0.035,
            tax_deferred=True
        )
        equivalent_yield = cash.get_equivalent_taxable_yield(marginal_tax_rate=0.25)
        expected_yield = cash.get_net_return_after_fees() / (1 - 0.25)  # 0.035 / 0.75 = 0.0467
        assert equivalent_yield == pytest.approx(expected_yield, rel=1e-10)

    def test_get_equivalent_taxable_yield_taxable(self):
        """Test equivalent taxable yield for taxable accounts."""
        cash = CashEquivalent(
            name="Taxable Savings",
            current_value=50000.0,
            expected_return=0.035,
            volatility=0.01,
            interest_rate=0.035
        )
        equivalent_yield = cash.get_equivalent_taxable_yield(marginal_tax_rate=0.25)
        assert equivalent_yield == cash.get_net_return_after_fees()  # Same as net return