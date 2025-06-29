"""
Tests for equity asset classes.
"""

import pytest
from retirement_planner.assets.equities import Equity
from retirement_planner.assets.base import AssetType
from retirement_planner.core.exceptions import ValidationError


class TestEquity:
    """Test Equity class functionality."""

    def test_equity_creation_basic(self):
        """Test creating a basic equity asset."""
        equity = Equity(
            name="S&P 500 ETF",
            current_value=10000.0,
            expected_return=0.08,
            volatility=0.15
        )
        assert equity.name == "S&P 500 ETF"
        assert equity.asset_type == AssetType.EQUITY
        assert equity.current_value == 10000.0
        assert equity.expected_return == 0.08
        assert equity.volatility == 0.15
        assert equity.dividend_yield == 0.0
        assert equity.beta == 1.0
        assert equity.geography == "domestic"
        assert equity.is_public is True

    def test_equity_creation_domestic_large_cap(self):
        """Test creating a domestic large cap equity."""
        equity = Equity(
            name="Large Cap Stock",
            current_value=50000.0,
            expected_return=0.07,
            volatility=0.12,
            dividend_yield=0.02,
            beta=0.9,
            market_cap="large",
            sector="Technology"
        )
        assert equity.get_metadata_field('market_cap') == "large"
        assert equity.get_metadata_field('sector') == "Technology"
        assert equity.get_metadata_field('dividend_yield') == 0.02
        assert equity.get_metadata_field('beta') == 0.9

    def test_equity_creation_international(self):
        """Test creating an international equity."""
        equity = Equity(
            name="International Stock",
            current_value=20000.0,
            expected_return=0.09,
            volatility=0.18,
            geography="international",
            country="Germany",
            region="Europe",
            foreign_tax_rate=0.15
        )
        assert equity.get_metadata_field('geography') == "international"
        assert equity.get_metadata_field('country') == "Germany"
        assert equity.get_metadata_field('region') == "Europe"
        assert equity.get_metadata_field('foreign_tax_rate') == 0.15

    def test_equity_creation_emerging_markets(self):
        """Test creating an emerging markets equity."""
        equity = Equity(
            name="Emerging Markets ETF",
            current_value=15000.0,
            expected_return=0.12,
            volatility=0.25,
            geography="emerging",
            region="Emerging Markets"
        )
        assert equity.get_metadata_field('geography') == "emerging"
        assert equity.get_metadata_field('region') == "Emerging Markets"

    def test_equity_creation_private_equity(self):
        """Test creating a private equity investment."""
        equity = Equity(
            name="Private Equity Fund",
            current_value=100000.0,
            expected_return=0.15,
            volatility=0.30,
            is_public=False
        )
        assert equity.get_metadata_field('is_public') is False

    def test_equity_validation_invalid_dividend_yield(self):
        """Test equity validation with invalid dividend yield."""
        with pytest.raises(ValueError, match="Dividend yield must be between 0% and 50%"):
            Equity(
                name="Test Stock",
                current_value=10000.0,
                expected_return=0.08,
                volatility=0.15,
                dividend_yield=0.6  # 60% dividend yield
            )

    def test_equity_validation_invalid_beta(self):
        """Test equity validation with invalid beta."""
        with pytest.raises(ValueError, match="Beta must be between 0 and 3"):
            Equity(
                name="Test Stock",
                current_value=10000.0,
                expected_return=0.08,
                volatility=0.15,
                beta=4.0  # Beta > 3
            )

    def test_equity_validation_invalid_market_cap(self):
        """Test equity validation with invalid market cap."""
        with pytest.raises(ValueError, match="Market cap must be 'small', 'medium', or 'large'"):
            Equity(
                name="Test Stock",
                current_value=10000.0,
                expected_return=0.08,
                volatility=0.15,
                market_cap="mega"  # Invalid market cap
            )

    def test_equity_validation_invalid_geography(self):
        """Test equity validation with invalid geography."""
        with pytest.raises(ValueError, match="Geography must be 'domestic', 'international', or 'emerging'"):
            Equity(
                name="Test Stock",
                current_value=10000.0,
                expected_return=0.08,
                volatility=0.15,
                geography="global"  # Invalid geography
            )

    def test_equity_validation_invalid_foreign_tax_rate(self):
        """Test equity validation with invalid foreign tax rate."""
        with pytest.raises(ValueError, match="Foreign tax rate must be between 0% and 50%"):
            Equity(
                name="Test Stock",
                current_value=10000.0,
                expected_return=0.08,
                volatility=0.15,
                geography="international",
                foreign_tax_rate=0.6  # 60% foreign tax rate
            )

    def test_get_dividend_income(self):
        """Test calculating dividend income."""
        equity = Equity(
            name="Dividend Stock",
            current_value=10000.0,
            expected_return=0.08,
            volatility=0.15,
            dividend_yield=0.03
        )
        dividend_income = equity.get_dividend_income()
        assert dividend_income == 300.0  # 10000 * 0.03

    def test_get_total_return(self):
        """Test calculating total return including dividends."""
        equity = Equity(
            name="Dividend Stock",
            current_value=10000.0,
            expected_return=0.08,
            volatility=0.15,
            dividend_yield=0.03
        )
        total_return = equity.get_total_return()
        assert total_return == 0.11  # 0.08 + 0.03

    def test_get_risk_adjusted_return(self):
        """Test calculating risk-adjusted return using CAPM."""
        equity = Equity(
            name="Test Stock",
            current_value=10000.0,
            expected_return=0.08,
            volatility=0.15,
            beta=1.2
        )
        risk_adjusted_return = equity.get_risk_adjusted_return(risk_free_rate=0.02)
        expected_return = 0.02 + 1.2 * (0.08 - 0.02)
        assert risk_adjusted_return == pytest.approx(expected_return, rel=1e-2)

    def test_get_tax_treatment_domestic(self):
        """Test tax treatment for domestic equities."""
        equity = Equity(
            name="Domestic Stock",
            current_value=10000.0,
            expected_return=0.08,
            volatility=0.15,
            geography="domestic"
        )
        tax_treatment = equity.get_tax_treatment()
        assert tax_treatment['qualified_dividends'] is True
        assert tax_treatment['foreign_tax_credit'] is False
        assert tax_treatment['foreign_tax_rate'] == 0.0
        assert tax_treatment['geography'] == "domestic"

    def test_get_tax_treatment_international(self):
        """Test tax treatment for international equities."""
        equity = Equity(
            name="International Stock",
            current_value=10000.0,
            expected_return=0.08,
            volatility=0.15,
            geography="international",
            country="Germany",
            foreign_tax_rate=0.15
        )
        tax_treatment = equity.get_tax_treatment()
        assert tax_treatment['qualified_dividends'] is True  # Germany is in qualified list
        assert tax_treatment['foreign_tax_credit'] is True
        assert tax_treatment['foreign_tax_rate'] == 0.15
        assert tax_treatment['geography'] == "international"

    def test_get_effective_dividend_yield_domestic(self):
        """Test effective dividend yield for domestic equities."""
        equity = Equity(
            name="Domestic Stock",
            current_value=10000.0,
            expected_return=0.08,
            volatility=0.15,
            dividend_yield=0.03,
            geography="domestic"
        )
        effective_yield = equity.get_effective_dividend_yield()
        assert effective_yield == 0.03  # No foreign taxes

    def test_get_effective_dividend_yield_international(self):
        """Test effective dividend yield for international equities."""
        equity = Equity(
            name="International Stock",
            current_value=10000.0,
            expected_return=0.08,
            volatility=0.15,
            dividend_yield=0.04,
            geography="international",
            foreign_tax_rate=0.15
        )
        effective_yield = equity.get_effective_dividend_yield()
        assert effective_yield == 0.034  # 0.04 * (1 - 0.15)

    def test_get_currency_risk_domestic(self):
        """Test currency risk for domestic equities."""
        equity = Equity(
            name="Domestic Stock",
            current_value=10000.0,
            expected_return=0.08,
            volatility=0.15,
            geography="domestic"
        )
        currency_risk = equity.get_currency_risk()
        assert currency_risk == 0.0

    def test_get_currency_risk_international(self):
        """Test currency risk for international equities."""
        equity = Equity(
            name="International Stock",
            current_value=10000.0,
            expected_return=0.08,
            volatility=0.15,
            geography="international",
            region="Europe"
        )
        currency_risk = equity.get_currency_risk()
        assert currency_risk == 0.15

    def test_get_currency_risk_emerging(self):
        """Test currency risk for emerging markets."""
        equity = Equity(
            name="Emerging Markets Stock",
            current_value=10000.0,
            expected_return=0.08,
            volatility=0.15,
            geography="emerging"
        )
        currency_risk = equity.get_currency_risk()
        assert currency_risk == 0.25

    def test_get_total_volatility(self):
        """Test calculating total volatility including currency risk."""
        equity = Equity(
            name="International Stock",
            current_value=10000.0,
            expected_return=0.08,
            volatility=0.15,
            geography="international",
            region="Europe"
        )
        total_volatility = equity.get_total_volatility()
        # sqrt(0.15^2 + 0.15^2) = sqrt(0.045) ≈ 0.212
        assert total_volatility == pytest.approx(0.212, rel=1e-2)

    def test_get_liquidity_premium_public(self):
        """Test liquidity premium for public equities."""
        equity = Equity(
            name="Public Stock",
            current_value=10000.0,
            expected_return=0.08,
            volatility=0.15,
            is_public=True
        )
        liquidity_premium = equity.get_liquidity_premium()
        assert liquidity_premium == 0.0

    def test_get_liquidity_premium_private(self):
        """Test liquidity premium for private equities."""
        equity = Equity(
            name="Private Equity",
            current_value=10000.0,
            expected_return=0.08,
            volatility=0.15,
            is_public=False
        )
        liquidity_premium = equity.get_liquidity_premium()
        assert liquidity_premium == 0.02  # 2% liquidity premium

    def test_get_adjusted_return(self):
        """Test return adjusted for liquidity premium."""
        equity = Equity(
            name="Private Equity",
            current_value=10000.0,
            expected_return=0.08,
            volatility=0.15,
            is_public=False
        )
        adjusted_return = equity.get_adjusted_return()
        assert adjusted_return == 0.10  # 0.08 + 0.02

    def test_get_size_premium_large(self):
        """Test size premium for large cap."""
        equity = Equity(
            name="Large Cap Stock",
            current_value=10000.0,
            expected_return=0.08,
            volatility=0.15,
            market_cap="large"
        )
        size_premium = equity.get_size_premium()
        assert size_premium == 0.0

    def test_get_size_premium_medium(self):
        """Test size premium for medium cap."""
        equity = Equity(
            name="Medium Cap Stock",
            current_value=10000.0,
            expected_return=0.08,
            volatility=0.15,
            market_cap="medium"
        )
        size_premium = equity.get_size_premium()
        assert size_premium == 0.01  # 1% premium

    def test_get_size_premium_small(self):
        """Test size premium for small cap."""
        equity = Equity(
            name="Small Cap Stock",
            current_value=10000.0,
            expected_return=0.08,
            volatility=0.15,
            market_cap="small"
        )
        size_premium = equity.get_size_premium()
        assert size_premium == 0.03  # 3% premium

    def test_get_geography_premium_domestic(self):
        """Test geography premium for domestic equities."""
        equity = Equity(
            name="Domestic Stock",
            current_value=10000.0,
            expected_return=0.08,
            volatility=0.15,
            geography="domestic"
        )
        geography_premium = equity.get_geography_premium()
        assert geography_premium == 0.0

    def test_get_geography_premium_international(self):
        """Test geography premium for international equities."""
        equity = Equity(
            name="International Stock",
            current_value=10000.0,
            expected_return=0.08,
            volatility=0.15,
            geography="international"
        )
        geography_premium = equity.get_geography_premium()
        assert geography_premium == 0.01  # 1% premium

    def test_get_geography_premium_emerging(self):
        """Test geography premium for emerging markets."""
        equity = Equity(
            name="Emerging Markets Stock",
            current_value=10000.0,
            expected_return=0.08,
            volatility=0.15,
            geography="emerging"
        )
        geography_premium = equity.get_geography_premium()
        assert geography_premium == 0.03  # 3% premium

    def test_get_total_premium(self):
        """Test total premium calculation."""
        equity = Equity(
            name="Small Cap International Private Equity",
            current_value=10000.0,
            expected_return=0.08,
            volatility=0.15,
            market_cap="small",
            geography="international",
            is_public=False
        )
        total_premium = equity.get_total_premium()
        expected_premium = 0.03 + 0.01 + 0.02  # size + geography + liquidity
        assert total_premium == expected_premium

    def test_get_risk_adjusted_expected_return(self):
        """Test risk-adjusted expected return with all premiums."""
        equity = Equity(
            name="Small Cap International Private Equity",
            current_value=10000.0,
            expected_return=0.08,
            volatility=0.15,
            market_cap="small",
            geography="international",
            is_public=False
        )
        adjusted_return = equity.get_risk_adjusted_expected_return()
        expected_return = 0.08 + 0.03 + 0.01 + 0.02  # base + size + geography + liquidity
        assert adjusted_return == pytest.approx(expected_return, rel=1e-10)