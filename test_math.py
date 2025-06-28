#!/usr/bin/env python3
"""
Simple test to verify portfolio growth math.
"""

def test_portfolio_growth():
    """Test portfolio growth with 7% returns and contributions."""

    # Initial portfolio
    portfolio_value = 1000000  # $1M
    annual_contribution = 20000  # $20K per year
    annual_return = 0.07  # 7%

    print("Portfolio Growth Test (7% annual return)")
    print("Year | Portfolio | Return | Contribution | New Total")
    print("-" * 55)

    for year in range(21):  # 20 years
        if year == 0:
            print(f"{year:4d} | {portfolio_value:8,.0f} | {'N/A':>6} | {'N/A':>11} | {portfolio_value:9,.0f}")
            continue

        # Calculate return on current portfolio
        return_amount = portfolio_value * annual_return
        new_portfolio = portfolio_value + return_amount + annual_contribution

        print(f"{year:4d} | {portfolio_value:8,.0f} | {return_amount:6,.0f} | {annual_contribution:11,.0f} | {new_portfolio:9,.0f}")

        portfolio_value = new_portfolio

    print(f"\nFinal portfolio value: ${portfolio_value:,.0f}")
    print(f"Total contributions: ${annual_contribution * 20:,.0f}")
    print(f"Growth from returns only: ${portfolio_value - 1000000 - (annual_contribution * 20):,.0f}")
    print(f"Multiple of original: {portfolio_value / 1000000:.1f}x")

if __name__ == "__main__":
    test_portfolio_growth()