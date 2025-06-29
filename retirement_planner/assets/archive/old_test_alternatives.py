"""
Tests for alternative asset classes.
"""

import pytest
from retirement_planner.assets.alternatives import RealEstate, Commodity, CustomAsset
from retirement_planner.assets.base import AssetType
from retirement_planner.core.exceptions import ValidationError


class TestRealEstate:
    """Test RealEstate class functionality."""

    def test_real_estate_creation_basic(self):
        """Test creating a basic real estate asset."""
        real_estate = RealEstate(
            name="Residential Property",
            current_value=500000.0,
            expected_return=0.06,
            volatility=0.12
        )
        assert real_estate.name == "Residential Property"
        assert real_estate.asset_type == AssetType.REAL_ESTATE
        assert real_estate.current_value == 500000.0
        assert real_estate.expected_return == 0.06
        assert real_estate.volatility == 0.12
        assert real_estate.get_metadata_field('property_type') == "Residential"
        assert real_estate.get_metadata_field('rental_yield') == 0.0
        assert real_estate.get_metadata_field('appreciation_rate') == 0.03

    def test_real_estate_creation_commercial(self):
        """Test creating a commercial real estate asset."""
        real_estate = RealEstate(
            name="Office Building",
            current_value=2000000.0,
            expected_return=0.08,
            volatility=0.15,
            property_type="Commercial",
            location="Downtown",
            rental_yield=0.05,
            appreciation_rate=0.04,
            leverage_ratio=0.6
        )
        assert real_estate.get_metadata_field('property_type') == "Commercial"
        assert real_estate.get_metadata_field('location') == "Downtown"
        assert real_estate.get_metadata_field('rental_yield') == 0.05
        assert real_estate.get_metadata_field('appreciation_rate') == 0.04
        assert real_estate.get_metadata_field('leverage_ratio') == 0.6

    def test_real_estate_creation_reit(self):
        """Test creating a REIT asset."""
        real_estate = RealEstate(
            name="REIT Fund",
            current_value=100000.0,
            expected_return=0.07,
            volatility=0.18,
            property_type="REIT",
            rental_yield=0.04,
            leverage_ratio=0.0  # REITs typically don't have leverage
        )
        assert real_estate.get_metadata_field('property_type') == "REIT"
        assert real_estate.get_metadata_field('leverage_ratio') == 0.0

    def test_real_estate_validation_invalid_rental_yield(self):
        """Test real estate validation with invalid rental yield."""
        with pytest.raises(ValueError, match="Rental yield must be between 0% and 20%"):
            RealEstate(
                name="Test Property",
                current_value=500000.0,
                expected_return=0.06,
                volatility=0.12,
                rental_yield=0.25  # 25% rental yield
            )

    def test_real_estate_validation_invalid_appreciation_rate(self):
        """Test real estate validation with invalid appreciation rate."""
        with pytest.raises(ValueError, match="Appreciation rate must be between 0% and 20%"):
            RealEstate(
                name="Test Property",
                current_value=500000.0,
                expected_return=0.06,
                volatility=0.12,
                appreciation_rate=0.25  # 25% appreciation rate
            )

    def test_real_estate_validation_invalid_property_tax_rate(self):
        """Test real estate validation with invalid property tax rate."""
        with pytest.raises(ValueError, match="Property tax rate must be between 0% and 5%"):
            RealEstate(
                name="Test Property",
                current_value=500000.0,
                expected_return=0.06,
                volatility=0.12,
                property_tax_rate=0.08  # 8% property tax rate
            )

    def test_real_estate_validation_invalid_leverage_ratio(self):
        """Test real estate validation with invalid leverage ratio."""
        with pytest.raises(ValueError, match="Leverage ratio must be between 0% and 90%"):
            RealEstate(
                name="Test Property",
                current_value=500000.0,
                expected_return=0.06,
                volatility=0.12,
                leverage_ratio=0.95  # 95% LTV
            )

    def test_get_rental_income(self):
        """Test calculating rental income."""
        real_estate = RealEstate(
            name="Rental Property",
            current_value=500000.0,
            expected_return=0.06,
            volatility=0.12,
            rental_yield=0.04
        )
        rental_income = real_estate.get_rental_income()
        assert rental_income == 20000.0  # 500000 * 0.04

    def test_get_net_rental_income(self):
        """Test calculating net rental income after expenses."""
        real_estate = RealEstate(
            name="Rental Property",
            current_value=500000.0,
            expected_return=0.06,
            volatility=0.12,
            rental_yield=0.04,
            property_tax_rate=0.012,
            maintenance_rate=0.02
        )
        net_rental_income = real_estate.get_net_rental_income()
        gross_rental = 500000.0 * 0.04  # 20000
        property_tax = 500000.0 * 0.012  # 6000
        maintenance = 500000.0 * 0.02  # 10000
        expected_net = gross_rental - property_tax - maintenance  # 20000 - 6000 - 10000 = 4000
        assert net_rental_income == expected_net

    def test_get_total_return(self):
        """Test calculating total return including rental income and appreciation."""
        real_estate = RealEstate(
            name="Rental Property",
            current_value=500000.0,
            expected_return=0.06,
            volatility=0.12,
            rental_yield=0.04,
            appreciation_rate=0.03
        )
        total_return = real_estate.get_total_return()
        assert total_return == 0.13  # 0.06 + 0.04 + 0.03

    def test_get_leverage_impact_no_leverage(self):
        """Test leverage impact with no debt."""
        real_estate = RealEstate(
            name="Property",
            current_value=500000.0,
            expected_return=0.06,
            volatility=0.12,
            leverage_ratio=0.0
        )
        leverage_impact = real_estate.get_leverage_impact()
        assert leverage_impact == 1.0

    def test_get_leverage_impact_with_leverage(self):
        """Test leverage impact with debt."""
        real_estate = RealEstate(
            name="Leveraged Property",
            current_value=500000.0,
            expected_return=0.06,
            volatility=0.12,
            leverage_ratio=0.6
        )
        leverage_impact = real_estate.get_leverage_impact()
        expected_impact = 1.0 + 0.6 * 0.5  # 1.0 + leverage_ratio * 0.5
        assert leverage_impact == expected_impact

    def test_get_tax_treatment(self):
        """Test getting tax treatment for real estate."""
        real_estate = RealEstate(
            name="Rental Property",
            current_value=500000.0,
            expected_return=0.06,
            volatility=0.12,
            property_type="Residential",
            location="Suburban"
        )
        tax_treatment = real_estate.get_tax_treatment()
        assert tax_treatment['depreciation'] is True
        assert tax_treatment['1031_exchange'] is True
        assert tax_treatment['property_type'] == "Residential"
        assert tax_treatment['location'] == "Suburban"
        assert tax_treatment['rental_income_taxable'] is True


class TestCommodity:
    """Test Commodity class functionality."""

    def test_commodity_creation_basic(self):
        """Test creating a basic commodity asset."""
        commodity = Commodity(
            name="Gold ETF",
            current_value=50000.0,
            expected_return=0.04,
            volatility=0.20
        )
        assert commodity.name == "Gold ETF"
        assert commodity.asset_type == AssetType.COMMODITY
        assert commodity.current_value == 50000.0
        assert commodity.expected_return == 0.04
        assert commodity.volatility == 0.20
        assert commodity.get_metadata_field('commodity_type') == "Gold"
        assert commodity.get_metadata_field('delivery_mechanism') == "ETF"

    def test_commodity_creation_physical(self):
        """Test creating a physical commodity asset."""
        commodity = Commodity(
            name="Physical Gold",
            current_value=100000.0,
            expected_return=0.04,
            volatility=0.20,
            commodity_type="Gold",
            delivery_mechanism="Physical",
            storage_cost_rate=0.01,
            insurance_cost_rate=0.005
        )
        assert commodity.get_metadata_field('commodity_type') == "Gold"
        assert commodity.get_metadata_field('delivery_mechanism') == "Physical"
        assert commodity.get_metadata_field('storage_cost_rate') == 0.01
        assert commodity.get_metadata_field('insurance_cost_rate') == 0.005

    def test_commodity_creation_oil(self):
        """Test creating an oil commodity asset."""
        commodity = Commodity(
            name="Oil Futures",
            current_value=75000.0,
            expected_return=0.06,
            volatility=0.35,
            commodity_type="Oil",
            delivery_mechanism="Futures"
        )
        assert commodity.get_metadata_field('commodity_type') == "Oil"
        assert commodity.get_metadata_field('delivery_mechanism') == "Futures"

    def test_commodity_validation_invalid_storage_cost_rate(self):
        """Test commodity validation with invalid storage cost rate."""
        with pytest.raises(ValueError, match="Storage cost rate must be between 0% and 10%"):
            Commodity(
                name="Test Commodity",
                current_value=50000.0,
                expected_return=0.04,
                volatility=0.20,
                storage_cost_rate=0.15  # 15% storage cost
            )

    def test_commodity_validation_invalid_insurance_cost_rate(self):
        """Test commodity validation with invalid insurance cost rate."""
        with pytest.raises(ValueError, match="Insurance cost rate must be between 0% and 5%"):
            Commodity(
                name="Test Commodity",
                current_value=50000.0,
                expected_return=0.04,
                volatility=0.20,
                insurance_cost_rate=0.08  # 8% insurance cost
            )

    def test_get_carrying_cost(self):
        """Test calculating carrying costs."""
        commodity = Commodity(
            name="Physical Gold",
            current_value=100000.0,
            expected_return=0.04,
            volatility=0.20,
            storage_cost_rate=0.01,
            insurance_cost_rate=0.005
        )
        carrying_cost = commodity.get_carrying_cost()
        expected_cost = 100000.0 * (0.01 + 0.005)  # 1500
        assert carrying_cost == expected_cost

    def test_get_net_return(self):
        """Test calculating net return after carrying costs."""
        commodity = Commodity(
            name="Physical Gold",
            current_value=100000.0,
            expected_return=0.04,
            volatility=0.20,
            storage_cost_rate=0.01,
            insurance_cost_rate=0.005
        )
        net_return = commodity.get_net_return()
        carrying_cost = 100000.0 * (0.01 + 0.005)  # 1500
        expected_net_return = 0.04 - (carrying_cost / 100000.0)  # 0.04 - 0.015 = 0.025
        assert net_return == pytest.approx(expected_net_return, rel=1e-10)

    def test_get_inflation_hedge_gold(self):
        """Test inflation hedging properties for gold."""
        commodity = Commodity(
            name="Gold",
            current_value=50000.0,
            expected_return=0.04,
            volatility=0.20,
            commodity_type="Gold"
        )
        inflation_hedge = commodity.get_inflation_hedge()
        assert inflation_hedge == 0.8  # Gold has high inflation correlation

    def test_get_inflation_hedge_oil(self):
        """Test inflation hedging properties for oil."""
        commodity = Commodity(
            name="Oil",
            current_value=75000.0,
            expected_return=0.06,
            volatility=0.35,
            commodity_type="Oil"
        )
        inflation_hedge = commodity.get_inflation_hedge()
        assert inflation_hedge == 0.6  # Oil has moderate inflation correlation

    def test_get_inflation_hedge_unknown(self):
        """Test inflation hedging properties for unknown commodity."""
        commodity = Commodity(
            name="Unknown Commodity",
            current_value=50000.0,
            expected_return=0.04,
            volatility=0.20,
            commodity_type="Unknown"
        )
        inflation_hedge = commodity.get_inflation_hedge()
        assert inflation_hedge == 0.5  # Default correlation

    def test_get_tax_treatment_physical(self):
        """Test tax treatment for physical commodities."""
        commodity = Commodity(
            name="Physical Gold",
            current_value=100000.0,
            expected_return=0.04,
            volatility=0.20,
            commodity_type="Gold",
            delivery_mechanism="Physical"
        )
        tax_treatment = commodity.get_tax_treatment()
        assert tax_treatment['collectibles_tax'] is True
        assert tax_treatment['commodity_type'] == "Gold"
        assert tax_treatment['delivery_mechanism'] == "Physical"
        assert tax_treatment['inflation_hedge'] == 0.8

    def test_get_tax_treatment_etf(self):
        """Test tax treatment for ETF commodities."""
        commodity = Commodity(
            name="Gold ETF",
            current_value=50000.0,
            expected_return=0.04,
            volatility=0.20,
            commodity_type="Gold",
            delivery_mechanism="ETF"
        )
        tax_treatment = commodity.get_tax_treatment()
        assert tax_treatment['collectibles_tax'] is False
        assert tax_treatment['delivery_mechanism'] == "ETF"


class TestCustomAsset:
    """Test CustomAsset class functionality."""

    def test_custom_asset_creation_basic(self):
        """Test creating a basic custom asset."""
        custom_asset = CustomAsset(
            name="Private Business",
            current_value=250000.0,
            expected_return=0.12,
            volatility=0.25
        )
        assert custom_asset.name == "Private Business"
        assert custom_asset.asset_type == AssetType.CUSTOM
        assert custom_asset.current_value == 250000.0
        assert custom_asset.expected_return == 0.12
        assert custom_asset.volatility == 0.25
        assert custom_asset.get_metadata_field('custom_type') == "Other"
        assert custom_asset.get_metadata_field('income_stream') == 0.0
        assert custom_asset.get_metadata_field('growth_rate') == 0.0

    def test_custom_asset_creation_with_income(self):
        """Test creating a custom asset with income stream."""
        custom_asset = CustomAsset(
            name="Rental Business",
            current_value=500000.0,
            expected_return=0.08,
            volatility=0.15,
            custom_type="Business",
            income_stream=0.06,
            growth_rate=0.02,
            liquidity_score=0.3,
            complexity_score=0.7
        )
        assert custom_asset.get_metadata_field('custom_type') == "Business"
        assert custom_asset.get_metadata_field('income_stream') == 0.06
        assert custom_asset.get_metadata_field('growth_rate') == 0.02
        assert custom_asset.get_metadata_field('liquidity_score') == 0.3
        assert custom_asset.get_metadata_field('complexity_score') == 0.7

    def test_custom_asset_validation_invalid_income_stream(self):
        """Test custom asset validation with invalid income stream."""
        with pytest.raises(ValueError, match="Income stream must be between 0% and 100%"):
            CustomAsset(
                name="Test Asset",
                current_value=100000.0,
                expected_return=0.08,
                volatility=0.15,
                income_stream=1.2  # 120% income stream
            )

    def test_custom_asset_validation_invalid_liquidity_score(self):
        """Test custom asset validation with invalid liquidity score."""
        with pytest.raises(ValueError, match="Liquidity score must be between 0 and 1"):
            CustomAsset(
                name="Test Asset",
                current_value=100000.0,
                expected_return=0.08,
                volatility=0.15,
                liquidity_score=1.5  # Invalid liquidity score
            )

    def test_custom_asset_validation_invalid_complexity_score(self):
        """Test custom asset validation with invalid complexity score."""
        with pytest.raises(ValueError, match="Complexity score must be between 0 and 1"):
            CustomAsset(
                name="Test Asset",
                current_value=100000.0,
                expected_return=0.08,
                volatility=0.15,
                complexity_score=-0.1  # Invalid complexity score
            )

    def test_get_total_return(self):
        """Test calculating total return including income stream and growth."""
        custom_asset = CustomAsset(
            name="Business with Income",
            current_value=500000.0,
            expected_return=0.08,
            volatility=0.15,
            income_stream=0.06,
            growth_rate=0.02
        )
        total_return = custom_asset.get_total_return()
        assert total_return == 0.16  # 0.08 + 0.06 + 0.02

    def test_get_liquidity_adjusted_return_high_liquidity(self):
        """Test liquidity adjusted return for highly liquid asset."""
        custom_asset = CustomAsset(
            name="Liquid Asset",
            current_value=100000.0,
            expected_return=0.08,
            volatility=0.15,
            liquidity_score=0.9
        )
        adjusted_return = custom_asset.get_liquidity_adjusted_return()
        # No liquidity premium for highly liquid assets
        assert adjusted_return == pytest.approx(0.08, rel=1e-10)

    def test_get_liquidity_adjusted_return_low_liquidity(self):
        """Test liquidity adjusted return for illiquid asset."""
        custom_asset = CustomAsset(
            name="Illiquid Asset",
            current_value=100000.0,
            expected_return=0.08,
            volatility=0.15,
            liquidity_score=0.2
        )
        adjusted_return = custom_asset.get_liquidity_adjusted_return()
        # Illiquid assets get premium: 0.08 + (1 - 0.2) * 0.02 = 0.08 + 0.016 = 0.096
        expected_return = 0.08 + (1 - 0.2) * 0.02
        assert adjusted_return == pytest.approx(expected_return, rel=1e-10)

    def test_get_complexity_risk(self):
        """Test calculating complexity risk."""
        custom_asset = CustomAsset(
            name="Complex Asset",
            current_value=100000.0,
            expected_return=0.08,
            volatility=0.15,
            complexity_score=0.8
        )
        complexity_risk = custom_asset.get_complexity_risk()
        expected_risk = 0.8 * 0.05  # 0.04
        assert complexity_risk == pytest.approx(expected_risk, rel=1e-10)

    def test_get_tax_treatment(self):
        """Test getting tax treatment for custom assets."""
        custom_asset = CustomAsset(
            name="Private Business",
            current_value=250000.0,
            expected_return=0.12,
            volatility=0.25,
            custom_type="Business",
            liquidity_score=0.3,
            complexity_score=0.7
        )
        tax_treatment = custom_asset.get_tax_treatment()
        assert tax_treatment['custom_type'] == "Business"
        assert tax_treatment['income_stream_taxable'] is True
        assert tax_treatment['liquidity_score'] == 0.3
        assert tax_treatment['complexity_score'] == 0.7