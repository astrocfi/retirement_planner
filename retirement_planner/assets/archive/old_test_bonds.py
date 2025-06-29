"""
Tests for bond asset classes.
"""

import pytest
from datetime import date, timedelta
from retirement_planner.assets.bonds import Bond
from retirement_planner.assets.base import AssetType
from retirement_planner.core.exceptions import ValidationError


class TestBond:
    """Test Bond class functionality."""

    def test_bond_creation_basic(self):
        """Test creating a basic bond asset."""
        bond = Bond(
            name="Treasury Bond",
            current_value=10000.0,
            expected_return=0.03,
            volatility=0.05
        )
        assert bond.name == "Treasury Bond"
        assert bond.asset_type == AssetType.BOND
        assert bond.current_value == 10000.0
        assert bond.expected_return == 0.03
        assert bond.volatility == 0.05
        assert bond.get_metadata_field('coupon_rate') == 0.0
        assert bond.get_metadata_field('face_value') == 1000.0
        assert bond.get_metadata_field('tax_treatment') == "taxable"

    def test_bond_creation_taxable(self):
        """Test creating a taxable bond."""
        bond = Bond(
            name="Corporate Bond",
            current_value=10000.0,
            expected_return=0.05,
            volatility=0.08,
            coupon_rate=0.04,
            tax_treatment="taxable",
            issuer_type="corporate",
            credit_rating="A",
            industry="Technology"
        )
        assert bond.get_metadata_field('tax_treatment') == "taxable"
        assert bond.get_metadata_field('issuer_type') == "corporate"
        assert bond.get_metadata_field('credit_rating') == "A"
        assert bond.get_metadata_field('industry') == "Technology"
        assert bond.get_metadata_field('coupon_rate') == 0.04

    def test_bond_creation_tax_exempt(self):
        """Test creating a tax-exempt bond."""
        bond = Bond(
            name="Municipal Bond",
            current_value=10000.0,
            expected_return=0.025,
            volatility=0.06,
            coupon_rate=0.025,
            tax_treatment="tax-exempt",
            issuer_type="municipal"
        )
        assert bond.get_metadata_field('tax_treatment') == "tax-exempt"
        assert bond.get_metadata_field('issuer_type') == "municipal"

    def test_bond_creation_tax_deferred(self):
        """Test creating a tax-deferred bond."""
        bond = Bond(
            name="IRA Bond",
            current_value=10000.0,
            expected_return=0.04,
            volatility=0.07,
            coupon_rate=0.04,
            tax_treatment="tax-deferred"
        )
        assert bond.get_metadata_field('tax_treatment') == "tax-deferred"

    def test_bond_creation_with_maturity(self):
        """Test creating a bond with maturity date."""
        maturity_date = date.today() + timedelta(days=365*5)  # 5 years
        bond = Bond(
            name="5-Year Treasury",
            current_value=10000.0,
            expected_return=0.03,
            volatility=0.05,
            maturity_date=maturity_date,
            duration=4.5
        )
        assert bond.get_metadata_field('maturity_date') == maturity_date
        assert bond.get_metadata_field('duration') == 4.5

    def test_bond_creation_callable(self):
        """Test creating a callable bond."""
        bond = Bond(
            name="Callable Corporate Bond",
            current_value=10000.0,
            expected_return=0.06,
            volatility=0.10,
            coupon_rate=0.05,
            callable=True,
            convertible=False
        )
        assert bond.get_metadata_field('callable') is True
        assert bond.get_metadata_field('convertible') is False

    def test_bond_validation_invalid_coupon_rate(self):
        """Test bond validation with invalid coupon rate."""
        with pytest.raises(ValueError, match="Coupon rate must be between 0% and 50%"):
            Bond(
                name="Test Bond",
                current_value=10000.0,
                expected_return=0.03,
                volatility=0.05,
                coupon_rate=0.6  # 60% coupon rate
            )

    def test_bond_validation_invalid_face_value(self):
        """Test bond validation with invalid face value."""
        with pytest.raises(ValueError, match="Face value must be positive"):
            Bond(
                name="Test Bond",
                current_value=10000.0,
                expected_return=0.03,
                volatility=0.05,
                face_value=-1000.0
            )

    def test_bond_validation_invalid_tax_treatment(self):
        """Test bond validation with invalid tax treatment."""
        with pytest.raises(ValueError, match="Tax treatment must be 'taxable', 'tax-exempt', or 'tax-deferred'"):
            Bond(
                name="Test Bond",
                current_value=10000.0,
                expected_return=0.03,
                volatility=0.05,
                tax_treatment="invalid"
            )

    def test_bond_validation_invalid_duration(self):
        """Test bond validation with invalid duration."""
        with pytest.raises(ValueError, match="Duration must be non-negative"):
            Bond(
                name="Test Bond",
                current_value=10000.0,
                expected_return=0.03,
                volatility=0.05,
                duration=-1.0
            )

    def test_bond_validation_invalid_credit_rating(self):
        """Test bond validation with invalid credit rating."""
        with pytest.raises(ValueError, match="Invalid credit rating"):
            Bond(
                name="Test Bond",
                current_value=10000.0,
                expected_return=0.03,
                volatility=0.05,
                credit_rating="X"  # Invalid rating
            )

    def test_get_coupon_payment(self):
        """Test calculating coupon payment."""
        bond = Bond(
            name="Coupon Bond",
            current_value=10000.0,
            expected_return=0.04,
            volatility=0.06,
            coupon_rate=0.03,
            face_value=1000.0
        )
        coupon_payment = bond.get_coupon_payment()
        assert coupon_payment == 30.0  # 1000 * 0.03

    def test_get_yield_to_maturity(self):
        """Test calculating yield to maturity."""
        bond = Bond(
            name="Discount Bond",
            current_value=950.0,
            expected_return=0.04,
            volatility=0.06,
            coupon_rate=0.03,
            face_value=1000.0
        )
        ytm = bond.get_yield_to_maturity()
        # Simplified calculation: coupon_rate + (face_value - current_value) / current_value
        expected_ytm = 0.03 + (1000.0 - 950.0) / 950.0
        assert ytm == pytest.approx(expected_ytm, rel=1e-10)

    def test_get_duration_provided(self):
        """Test getting duration when provided."""
        bond = Bond(
            name="Bond with Duration",
            current_value=10000.0,
            expected_return=0.04,
            volatility=0.06,
            duration=7.5
        )
        duration = bond.get_duration()
        assert duration == 7.5

    def test_get_duration_calculated_zero_coupon(self):
        """Test calculating duration for zero-coupon bond."""
        maturity_date = date.today() + timedelta(days=365*10)  # 10 years
        bond = Bond(
            name="Zero Coupon Bond",
            current_value=10000.0,
            expected_return=0.04,
            volatility=0.06,
            coupon_rate=0.0,
            maturity_date=maturity_date
        )
        duration = bond.get_duration()
        # For zero-coupon bonds, duration = time to maturity
        expected_duration = 10.0
        assert duration == pytest.approx(expected_duration, rel=1e-1)

    def test_get_duration_calculated_coupon(self):
        """Test calculating duration for coupon bond."""
        maturity_date = date.today() + timedelta(days=365*10)  # 10 years
        bond = Bond(
            name="Coupon Bond",
            current_value=10000.0,
            expected_return=0.04,
            volatility=0.06,
            coupon_rate=0.03,
            maturity_date=maturity_date
        )
        duration = bond.get_duration()
        # For coupon bonds, duration is typically 60-80% of time to maturity
        expected_duration = 10.0 * 0.7
        assert duration == pytest.approx(expected_duration, rel=1e-1)

    def test_get_duration_default(self):
        """Test getting default duration when no maturity date."""
        bond = Bond(
            name="Bond without Maturity",
            current_value=10000.0,
            expected_return=0.04,
            volatility=0.06
        )
        duration = bond.get_duration()
        assert duration == 5.0  # Default duration

    def test_get_interest_rate_risk(self):
        """Test calculating interest rate risk."""
        bond = Bond(
            name="Long Duration Bond",
            current_value=10000.0,
            expected_return=0.04,
            volatility=0.06,
            duration=10.0
        )
        interest_rate_risk = bond.get_interest_rate_risk()
        # Simplified: duration * 0.01 for 1% interest rate change
        expected_risk = 10.0 * 0.01
        assert interest_rate_risk == expected_risk

    def test_get_credit_risk_government(self):
        """Test credit risk for government bonds."""
        bond = Bond(
            name="Treasury Bond",
            current_value=10000.0,
            expected_return=0.03,
            volatility=0.05,
            issuer_type="government"
        )
        credit_risk = bond.get_credit_risk()
        assert credit_risk == 0.001  # Very low credit risk

    def test_get_credit_risk_corporate_aaa(self):
        """Test credit risk for AAA corporate bond."""
        bond = Bond(
            name="AAA Corporate Bond",
            current_value=10000.0,
            expected_return=0.04,
            volatility=0.06,
            issuer_type="corporate",
            credit_rating="AAA"
        )
        credit_risk = bond.get_credit_risk()
        assert credit_risk == 0.001

    def test_get_credit_risk_corporate_bb(self):
        """Test credit risk for BB corporate bond."""
        bond = Bond(
            name="BB Corporate Bond",
            current_value=10000.0,
            expected_return=0.08,
            volatility=0.12,
            issuer_type="corporate",
            credit_rating="BB"
        )
        credit_risk = bond.get_credit_risk()
        assert credit_risk == 0.05

    def test_get_spread_over_treasury_government(self):
        """Test credit spread for government bonds."""
        bond = Bond(
            name="Treasury Bond",
            current_value=10000.0,
            expected_return=0.03,
            volatility=0.05,
            issuer_type="government"
        )
        spread = bond.get_spread_over_treasury()
        assert spread == 0.0  # No spread for government bonds

    def test_get_spread_over_treasury_corporate(self):
        """Test credit spread for corporate bonds."""
        bond = Bond(
            name="Corporate Bond",
            current_value=10000.0,
            expected_return=0.06,
            volatility=0.08,
            issuer_type="corporate",
            credit_rating="A"
        )
        spread = bond.get_spread_over_treasury()
        # Base spread = credit_risk * 100 basis points
        expected_spread = 0.01 * 100 / 10000  # 1% = 100 basis points
        assert spread == pytest.approx(expected_spread, rel=1e-2)

    def test_get_spread_over_treasury_callable(self):
        """Test credit spread for callable bonds."""
        bond = Bond(
            name="Callable Corporate Bond",
            current_value=10000.0,
            expected_return=0.06,
            volatility=0.08,
            issuer_type="corporate",
            credit_rating="A",
            callable=True
        )
        spread = bond.get_spread_over_treasury()
        # Base spread + 50 basis points for callable
        expected_spread = (0.01 * 100 + 50) / 10000
        assert spread == pytest.approx(expected_spread, rel=1e-2)

    def test_get_total_yield(self):
        """Test calculating total yield."""
        bond = Bond(
            name="Corporate Bond",
            current_value=10000.0,
            expected_return=0.06,
            volatility=0.08,
            issuer_type="corporate",
            credit_rating="A"
        )
        total_yield = bond.get_total_yield()
        # Treasury yield (3%) + credit spread
        expected_yield = 0.03 + bond.get_spread_over_treasury()
        assert total_yield == pytest.approx(expected_yield, rel=1e-2)

    def test_get_tax_treatment_taxable(self):
        """Test tax treatment for taxable bonds."""
        bond = Bond(
            name="Corporate Bond",
            current_value=10000.0,
            expected_return=0.05,
            volatility=0.08,
            tax_treatment="taxable",
            issuer_type="corporate",
            credit_rating="A"
        )
        tax_treatment = bond.get_tax_treatment()
        assert tax_treatment['tax_treatment'] == "taxable"
        assert tax_treatment['tax_exempt'] is False
        assert tax_treatment['tax_deferred'] is False
        assert tax_treatment['issuer_type'] == "corporate"
        assert tax_treatment['credit_rating'] == "A"

    def test_get_tax_treatment_tax_exempt(self):
        """Test tax treatment for tax-exempt bonds."""
        bond = Bond(
            name="Municipal Bond",
            current_value=10000.0,
            expected_return=0.025,
            volatility=0.06,
            tax_treatment="tax-exempt",
            issuer_type="municipal"
        )
        tax_treatment = bond.get_tax_treatment()
        assert tax_treatment['tax_treatment'] == "tax-exempt"
        assert tax_treatment['tax_exempt'] is True
        assert tax_treatment['tax_deferred'] is False

    def test_get_tax_treatment_tax_deferred(self):
        """Test tax treatment for tax-deferred bonds."""
        bond = Bond(
            name="IRA Bond",
            current_value=10000.0,
            expected_return=0.04,
            volatility=0.07,
            tax_treatment="tax-deferred"
        )
        tax_treatment = bond.get_tax_treatment()
        assert tax_treatment['tax_treatment'] == "tax-deferred"
        assert tax_treatment['tax_exempt'] is False
        assert tax_treatment['tax_deferred'] is True

    def test_get_after_tax_yield_taxable(self):
        """Test after-tax yield for taxable bonds."""
        bond = Bond(
            name="Corporate Bond",
            current_value=10000.0,
            expected_return=0.05,
            volatility=0.08,
            tax_treatment="taxable"
        )
        after_tax_yield = bond.get_after_tax_yield(marginal_tax_rate=0.25)
        expected_yield = bond.get_total_yield() * (1 - 0.25)  # 5% * (1 - 25%)
        assert after_tax_yield == pytest.approx(expected_yield, rel=1e-10)

    def test_get_after_tax_yield_tax_exempt(self):
        """Test after-tax yield for tax-exempt bonds."""
        bond = Bond(
            name="Municipal Bond",
            current_value=10000.0,
            expected_return=0.025,
            volatility=0.06,
            tax_treatment="tax-exempt"
        )
        after_tax_yield = bond.get_after_tax_yield(marginal_tax_rate=0.25)
        assert after_tax_yield == pytest.approx(bond.get_total_yield(), rel=1e-10)  # No taxes

    def test_get_after_tax_yield_tax_deferred(self):
        """Test after-tax yield for tax-deferred bonds."""
        bond = Bond(
            name="IRA Bond",
            current_value=10000.0,
            expected_return=0.04,
            volatility=0.07,
            tax_treatment="tax-deferred"
        )
        after_tax_yield = bond.get_after_tax_yield(marginal_tax_rate=0.25)
        assert after_tax_yield == pytest.approx(bond.get_total_yield(), rel=1e-10)  # No taxes until withdrawal

    def test_get_equivalent_taxable_yield_tax_exempt(self):
        """Test equivalent taxable yield for tax-exempt bonds."""
        bond = Bond(
            name="Municipal Bond",
            current_value=10000.0,
            expected_return=0.025,
            volatility=0.06,
            tax_treatment="tax-exempt"
        )
        equivalent_yield = bond.get_equivalent_taxable_yield(marginal_tax_rate=0.25)
        expected_yield = bond.get_total_yield() / (1 - 0.25)  # 2.5% / (1 - 25%)
        assert equivalent_yield == pytest.approx(expected_yield, rel=1e-10)

    def test_get_equivalent_taxable_yield_taxable(self):
        """Test equivalent taxable yield for taxable bonds."""
        bond = Bond(
            name="Corporate Bond",
            current_value=10000.0,
            expected_return=0.05,
            volatility=0.08,
            tax_treatment="taxable"
        )
        equivalent_yield = bond.get_equivalent_taxable_yield(marginal_tax_rate=0.25)
        assert equivalent_yield == bond.get_total_yield()  # Same as total yield