#!/usr/bin/env python3
"""
Test script to verify asset configuration works with current implementation.
"""

import sys
from pathlib import Path

# Add the parent directory to the path
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))

# Get the directory where this script is located
SCRIPT_DIR = Path(__file__).parent.parent

def test_asset_configuration():
    """Test loading and creating asset objects from configuration."""
    from retirement_planner.core.config import ConfigLoader
    from retirement_planner.assets.equities import Equity
    from retirement_planner.assets.bonds import Bond
    from retirement_planner.assets.cash import CashEquivalent
    from retirement_planner.assets.alternatives import RealEstate, Commodity, CustomAsset
    from retirement_planner.assets.base import AssetType

    print("Testing asset configuration...")

    # Load asset configuration using absolute path
    loader = ConfigLoader()
    loader.load_from_file(SCRIPT_DIR / 'assets.yaml')
    assets_data = loader.config_data

    print(f"✓ Asset configuration loaded successfully!")

    # Test creating different asset types
    assets_created = 0

    for category, assets_list in assets_data["assets"].items():
        print(f"  Processing {category} assets...")

        for asset_data in assets_list:
            asset_type = AssetType(asset_data["asset_type"])

            # Create appropriate asset object based on type
            if asset_type == AssetType.EQUITY:
                asset = Equity(
                    name=asset_data["name"],
                    current_value=asset_data["current_value"],
                    expected_return=asset_data["expected_return"],
                    volatility=asset_data["volatility"],
                    **asset_data.get("metadata", {})
                )
            elif asset_type == AssetType.BOND:
                asset = Bond(
                    name=asset_data["name"],
                    current_value=asset_data["current_value"],
                    expected_return=asset_data["expected_return"],
                    volatility=asset_data["volatility"],
                    **asset_data.get("metadata", {})
                )
            elif asset_type == AssetType.CASH:
                asset = CashEquivalent(
                    name=asset_data["name"],
                    current_value=asset_data["current_value"],
                    expected_return=asset_data["expected_return"],
                    volatility=asset_data["volatility"],
                    **asset_data.get("metadata", {})
                )
            elif asset_type == AssetType.REAL_ESTATE:
                asset = RealEstate(
                    name=asset_data["name"],
                    current_value=asset_data["current_value"],
                    expected_return=asset_data["expected_return"],
                    volatility=asset_data["volatility"],
                    **asset_data.get("metadata", {})
                )
            elif asset_type == AssetType.COMMODITY:
                asset = Commodity(
                    name=asset_data["name"],
                    current_value=asset_data["current_value"],
                    expected_return=asset_data["expected_return"],
                    volatility=asset_data["volatility"],
                    **asset_data.get("metadata", {})
                )
            elif asset_type == AssetType.CUSTOM:
                asset = CustomAsset(
                    name=asset_data["name"],
                    current_value=asset_data["current_value"],
                    expected_return=asset_data["expected_return"],
                    volatility=asset_data["volatility"],
                    **asset_data.get("metadata", {})
                )
            else:
                raise ValueError(f"Unsupported asset type: {asset_type}")

            assets_created += 1
            print(f"    ✓ Created {asset.name} ({asset.asset_type.value})")

    print(f"✓ Successfully created {assets_created} assets")

    # Test portfolio summary
    portfolio_summary = assets_data.get("portfolio_summary", {})
    if portfolio_summary:
        print(f"✓ Portfolio summary loaded:")
        print(f"  Total value: ${portfolio_summary['total_value']:,.0f}")
        print(f"  Allocation: {portfolio_summary['allocation']}")
        print(f"  Expected return: {portfolio_summary['risk_metrics']['expected_return']:.1%}")
        print(f"  Volatility: {portfolio_summary['risk_metrics']['volatility']:.1%}")

    # Assertions to verify the test passed
    assert assets_created > 0
    assert "portfolio_summary" in assets_data

def test_asset_metadata_access():
    """Test accessing asset metadata fields."""
    from retirement_planner.assets.equities import Equity
    from retirement_planner.assets.bonds import Bond

    print("\nTesting asset metadata access...")

    # Test equity metadata
    equity = Equity(
        name="Test Stock",
        current_value=10000.0,
        expected_return=0.08,
        volatility=0.15,
        dividend_yield=0.02,
        beta=1.1,
        market_cap="large",
        geography="domestic"
    )

    assert equity.get_metadata_field('dividend_yield') == 0.02
    assert equity.get_metadata_field('beta') == 1.1
    assert equity.get_metadata_field('market_cap') == "large"
    print("  ✓ Equity metadata access working")

    # Test bond metadata
    bond = Bond(
        name="Test Bond",
        current_value=10000.0,
        expected_return=0.04,
        volatility=0.06,
        coupon_rate=0.03,
        tax_treatment="tax-exempt",
        issuer_type="municipal"
    )

    assert bond.get_metadata_field('coupon_rate') == 0.03
    assert bond.get_metadata_field('tax_treatment') == "tax-exempt"
    assert bond.get_metadata_field('issuer_type') == "municipal"
    print("  ✓ Bond metadata access working")

def main():
    """Run all asset configuration tests."""
    print("=" * 60)
    print("ASSET CONFIGURATION COMPATIBILITY TEST")
    print("=" * 60)

    tests = [
        test_asset_configuration,
        test_asset_metadata_access
    ]

    passed = 0
    total = len(tests)

    for test in tests:
        try:
            test()
            passed += 1
        except Exception as e:
            print(f"✗ Test {test.__name__} failed: {e}")

    print("\n" + "=" * 60)
    print(f"TEST RESULTS: {passed}/{total} tests passed")

    if passed == total:
        print("✓ All asset configurations are compatible with current implementation!")
    else:
        print("✗ Some asset configurations have compatibility issues.")

    print("=" * 60)

if __name__ == "__main__":
    main()