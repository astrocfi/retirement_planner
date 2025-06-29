import pytest
from retirement_planner.tax.federal import USFederalTax, SocialSecurity, RetirementAccountTax, SocialSecurityBenefit

class TestUSFederalTax:
    """Test US Federal tax calculations."""

    def test_federal_tax_creation(self):
        """Test creating US Federal tax instance."""
        federal_tax = USFederalTax()
        assert federal_tax.tax_year == 2024

    def test_income_tax_zero_income(self):
        """Test federal income tax calculation for zero income."""
        federal_tax = USFederalTax()
        tax = federal_tax.calculate_income_tax(0, 'single')
        assert tax == 0.0

    def test_income_tax_low_bracket(self):
        """Test federal income tax calculation in lowest bracket."""
        federal_tax = USFederalTax()
        income = 20000  # Above standard deduction
        tax = federal_tax.calculate_income_tax(income, 'single')
        # Taxable income = 20000 - 14600 = 5400
        # Tax = 5400 * 0.10 = 540
        expected_tax = (income - 14600) * 0.10
        assert tax == pytest.approx(expected_tax)

    def test_income_tax_multiple_brackets(self):
        """Test federal income tax calculation across multiple brackets."""
        federal_tax = USFederalTax()
        income = 60000  # Above standard deduction
        tax = federal_tax.calculate_income_tax(income, 'single')

        # Manual calculation for 2024 brackets with standard deduction
        taxable_income = income - 14600  # Standard deduction
        brackets = federal_tax.get_tax_brackets(2024, 'single')
        expected = 0.0
        remaining = taxable_income
        for b in brackets:
            lower, upper, rate = b['min'], b['max'] if b['max'] is not None else float('inf'), b['rate']
            if taxable_income > lower:
                taxable = min(remaining, upper - lower)
                expected += taxable * rate
                remaining -= taxable
                if remaining <= 0:
                    break
        assert tax == pytest.approx(expected)

    def test_income_tax_below_standard_deduction(self):
        """Test federal income tax calculation below standard deduction."""
        federal_tax = USFederalTax()
        income = 10000  # Below standard deduction of 14600
        tax = federal_tax.calculate_income_tax(income, 'single')
        assert tax == 0.0

    def test_capital_gains_tax_short_term(self):
        """Test short-term capital gains tax (taxed as ordinary income)."""
        federal_tax = USFederalTax()
        gains = 20000
        short_term_tax = federal_tax.calculate_capital_gains_tax(gains, long_term=False, filing_status='single')
        income_tax = federal_tax.calculate_income_tax(gains, 'single')
        assert short_term_tax == pytest.approx(income_tax)

    def test_capital_gains_tax_long_term_zero_bracket(self):
        """Test long-term capital gains tax in 0% bracket."""
        federal_tax = USFederalTax()
        gains = 40000  # Below 44725 threshold
        tax = federal_tax.calculate_capital_gains_tax(gains, long_term=True, filing_status='single')
        assert tax == 0.0

    def test_capital_gains_tax_long_term_15_percent_bracket(self):
        """Test long-term capital gains tax in 15% bracket."""
        federal_tax = USFederalTax()
        gains = 100000  # Above 44725 threshold
        tax = federal_tax.calculate_capital_gains_tax(gains, long_term=True, filing_status='single')
        expected_tax = gains * 0.15
        assert tax == pytest.approx(expected_tax)

    def test_get_tax_brackets_single(self):
        """Test getting federal tax brackets for single filer."""
        federal_tax = USFederalTax()
        brackets = federal_tax.get_tax_brackets(2024, 'single')
        assert isinstance(brackets, list)
        assert all('min' in b and 'max' in b and 'rate' in b for b in brackets)
        assert len(brackets) == 7  # 7 brackets for 2024

    def test_get_deductions_single(self):
        """Test getting federal deductions for single filer."""
        federal_tax = USFederalTax()
        deductions = federal_tax.get_deductions(2024, 'single')
        assert 'standard_deduction' in deductions
        assert deductions['standard_deduction'] == 14600.0

    def test_get_tax_brackets_unsupported_status(self):
        """Test getting tax brackets for unsupported filing status."""
        federal_tax = USFederalTax()
        with pytest.raises(NotImplementedError):
            federal_tax.get_tax_brackets(2024, 'married')

class TestSocialSecurity:
    """Test Social Security benefit calculations."""

    def test_social_security_creation(self):
        """Test creating Social Security instance."""
        ss = SocialSecurity()
        assert ss.full_retirement_age == 67
        assert ss.earliest_claiming_age == 62
        assert ss.latest_claiming_age == 70

    def test_primary_insurance_amount_low_earnings(self):
        """Test PIA calculation for low earnings."""
        ss = SocialSecurity()
        aime = 1000  # Below first bend point
        pia = ss.calculate_primary_insurance_amount(aime)
        expected_pia = aime * 0.90
        assert pia == pytest.approx(expected_pia, rel=1e-2)

    def test_primary_insurance_amount_medium_earnings(self):
        """Test PIA calculation for medium earnings."""
        ss = SocialSecurity()
        aime = 3000  # Between bend points
        pia = ss.calculate_primary_insurance_amount(aime)
        expected_pia = (1174 * 0.90) + ((3000 - 1174) * 0.32)
        assert pia == pytest.approx(expected_pia, rel=1e-2)

    def test_primary_insurance_amount_high_earnings(self):
        """Test PIA calculation for high earnings."""
        ss = SocialSecurity()
        aime = 8000  # Above second bend point
        pia = ss.calculate_primary_insurance_amount(aime)
        expected_pia = (1174 * 0.90) + ((7078 - 1174) * 0.32) + ((8000 - 7078) * 0.15)
        assert pia == pytest.approx(expected_pia, rel=1e-2)

    def test_benefit_at_full_retirement_age(self):
        """Test benefit calculation at full retirement age."""
        ss = SocialSecurity()
        pia = 2000
        benefit = ss.calculate_benefit_at_age(pia, 67)
        assert benefit == pia

    def test_benefit_early_retirement(self):
        """Test benefit calculation for early retirement."""
        ss = SocialSecurity()
        pia = 2000
        benefit = ss.calculate_benefit_at_age(pia, 62)
        # Should be reduced by approximately 30%
        assert benefit < pia
        assert benefit >= pia * 0.70  # Minimum 70%

    def test_benefit_delayed_retirement(self):
        """Test benefit calculation for delayed retirement."""
        ss = SocialSecurity()
        pia = 2000
        benefit = ss.calculate_benefit_at_age(pia, 70)
        # Should be increased by approximately 24%
        assert benefit > pia
        assert benefit <= pia * 1.32  # Maximum 132%

    def test_benefit_before_earliest_age(self):
        """Test benefit calculation before earliest claiming age."""
        ss = SocialSecurity()
        pia = 2000
        benefit = ss.calculate_benefit_at_age(pia, 60)
        assert benefit == 0.0

    def test_medicare_premiums_low_income(self):
        """Test Medicare premium calculation for low income."""
        ss = SocialSecurity()
        income = 50000
        premiums = ss.calculate_medicare_premiums(income, 'single')
        assert 'part_b_premium' in premiums
        assert 'part_d_premium' in premiums
        assert 'total_medicare_premium' in premiums
        assert premiums['part_b_premium'] == 174.70  # Base premium
        assert premiums['total_medicare_premium'] == 174.70 + 34.70

    def test_medicare_premiums_high_income(self):
        """Test Medicare premium calculation for high income."""
        ss = SocialSecurity()
        income = 200000
        premiums = ss.calculate_medicare_premiums(income, 'single')
        assert premiums['part_b_premium'] > 174.70  # Should have IRMAA adjustment

class TestRetirementAccountTax:
    """Test retirement account tax calculations."""

    def test_retirement_account_tax_creation(self):
        """Test creating RetirementAccountTax instance."""
        rat = RetirementAccountTax()
        assert rat.current_year == 2024

    def test_rmd_before_required_age(self):
        """Test RMD calculation before required age."""
        rat = RetirementAccountTax()
        rmd = rat.calculate_rmd(100000, 70)
        assert rmd == 0.0

    def test_rmd_at_required_age(self):
        """Test RMD calculation at required age."""
        rat = RetirementAccountTax()
        account_balance = 100000
        rmd = rat.calculate_rmd(account_balance, 73)
        expected_rmd = account_balance / 26.5  # Distribution period for age 73
        assert rmd == pytest.approx(expected_rmd)

    def test_rmd_old_age(self):
        """Test RMD calculation for very old age."""
        rat = RetirementAccountTax()
        account_balance = 100000
        rmd = rat.calculate_rmd(account_balance, 100)
        expected_rmd = account_balance / 2.2  # Distribution period for age 100
        assert rmd == pytest.approx(expected_rmd)

    def test_contribution_limit_traditional_ira_under_50(self):
        """Test contribution limit for traditional IRA under 50."""
        rat = RetirementAccountTax()
        limit = rat.calculate_contribution_limit(45, 'traditional_ira')
        assert limit == 7000

    def test_contribution_limit_traditional_ira_over_50(self):
        """Test contribution limit for traditional IRA over 50."""
        rat = RetirementAccountTax()
        limit = rat.calculate_contribution_limit(55, 'traditional_ira')
        assert limit == 8000

    def test_contribution_limit_401k_under_50(self):
        """Test contribution limit for 401k under 50."""
        rat = RetirementAccountTax()
        limit = rat.calculate_contribution_limit(45, '401k')
        assert limit == 23000

    def test_contribution_limit_401k_over_50(self):
        """Test contribution limit for 401k over 50."""
        rat = RetirementAccountTax()
        limit = rat.calculate_contribution_limit(55, '401k')
        assert limit == 30500

    def test_roth_eligibility_low_income(self):
        """Test Roth IRA eligibility for low income."""
        rat = RetirementAccountTax()
        eligible = rat.is_roth_eligible(100000, 'single')
        assert eligible is True

    def test_roth_eligibility_high_income(self):
        """Test Roth IRA eligibility for high income."""
        rat = RetirementAccountTax()
        eligible = rat.is_roth_eligible(200000, 'single')
        assert eligible is False

    def test_tax_deduction_no_employer_plan(self):
        """Test tax deduction when no employer plan."""
        rat = RetirementAccountTax()
        contribution = 7000
        deduction = rat.calculate_tax_deduction(contribution, 100000, 'single', 'traditional_ira', has_employer_plan=False)
        assert deduction == contribution

    def test_tax_deduction_with_employer_plan_low_income(self):
        """Test tax deduction with employer plan and low income."""
        rat = RetirementAccountTax()
        contribution = 7000
        deduction = rat.calculate_tax_deduction(contribution, 50000, 'single', 'traditional_ira', has_employer_plan=True)
        assert deduction == contribution  # Full deduction below phase-out

    def test_tax_deduction_with_employer_plan_high_income(self):
        """Test tax deduction with employer plan and high income."""
        rat = RetirementAccountTax()
        contribution = 7000
        deduction = rat.calculate_tax_deduction(contribution, 100000, 'single', 'traditional_ira', has_employer_plan=True)
        assert deduction == 0.0  # No deduction above phase-out

    def test_tax_deduction_roth_ira(self):
        """Test tax deduction for Roth IRA (should be zero)."""
        rat = RetirementAccountTax()
        contribution = 7000
        deduction = rat.calculate_tax_deduction(contribution, 100000, 'single', 'roth_ira')
        assert deduction == 0.0

class TestSocialSecurityBenefit:
    """Test SocialSecurityBenefit dataclass."""

    def test_social_security_benefit_creation(self):
        """Test creating SocialSecurityBenefit instance."""
        benefit = SocialSecurityBenefit(
            primary_insurance_amount=2000.0,
            benefit_at_full_retirement=2000.0,
            benefit_at_current_age=1800.0,
            reduction_factor=0.9,
            delayed_credit_factor=1.0
        )
        assert benefit.primary_insurance_amount == 2000.0
        assert benefit.benefit_at_full_retirement == 2000.0
        assert benefit.benefit_at_current_age == 1800.0
        assert benefit.reduction_factor == 0.9
        assert benefit.delayed_credit_factor == 1.0