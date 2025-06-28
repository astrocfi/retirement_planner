import pytest
from retirement_planner.models.portfolio import Portfolio, AssetAllocation, StaticRebalancingStrategy, PortfolioError
from retirement_planner.assets.equities import Equity

@pytest.fixture
def assets():
    return {
        'StockA': Equity(
            name='StockA',
            current_value=60000,
            expected_return=0.08,
            volatility=0.15,
            dividend_yield=0.02,
            beta=1.0,
            market_cap='large',
            geography='domestic'
        ),
        'BondB': Equity(
            name='BondB',
            current_value=30000,
            expected_return=0.04,
            volatility=0.08,
            dividend_yield=0.03,
            beta=0.5,
            market_cap='medium',
            geography='domestic'
        ),
        'CashC': Equity(
            name='CashC',
            current_value=10000,
            expected_return=0.02,
            volatility=0.01,
            dividend_yield=0.01,
            beta=0.1,
            market_cap='small',
            geography='domestic'
        ),
    }

@pytest.fixture
def allocation():
    return AssetAllocation({'StockA': 0.6, 'BondB': 0.3, 'CashC': 0.1})

@pytest.fixture
def asset_values():
    return {'StockA': 60000, 'BondB': 30000, 'CashC': 10000}

@pytest.fixture
def portfolio(assets, allocation, asset_values):
    return Portfolio(
        assets=assets,
        allocation=allocation,
        asset_values=asset_values,
        rebalancing_strategy=StaticRebalancingStrategy()
    )

def test_asset_allocation_valid(allocation):
    allocation.validate()  # Should not raise

def test_asset_allocation_invalid_sum():
    bad = AssetAllocation({'A': 0.5, 'B': 0.3})
    with pytest.raises(PortfolioError):
        bad.validate()

def test_asset_allocation_invalid_bounds():
    bad = AssetAllocation({'A': 1.2, 'B': -0.2})
    with pytest.raises(PortfolioError):
        bad.validate()

def test_asset_allocation_rebalance(allocation):
    current = {'StockA': 50000, 'BondB': 40000, 'CashC': 10000}
    total = sum(current.values())
    result = allocation.rebalance(current, total)
    assert pytest.approx(result['StockA'], 0.01) == 0.6 * total
    assert pytest.approx(result['BondB'], 0.01) == 0.3 * total
    assert pytest.approx(result['CashC'], 0.01) == 0.1 * total

def test_portfolio_creation_and_validation(portfolio):
    portfolio.validate()  # Should not raise

def test_portfolio_invalid_assets(allocation, asset_values):
    assets = {'StockA': Equity(
        name='StockA',
        current_value=60000,
        expected_return=0.08,
        volatility=0.15,
        dividend_yield=0.02,
        beta=1.0,
        market_cap='large',
        geography='domestic'
    )}
    with pytest.raises(PortfolioError):
        Portfolio(assets=assets, allocation=allocation, asset_values=asset_values).validate()

def test_portfolio_get_allocation_percentages(portfolio):
    result = portfolio.get_allocation_percentages()
    assert pytest.approx(result['StockA'], 0.01) == 0.6
    assert pytest.approx(result['BondB'], 0.01) == 0.3
    assert pytest.approx(result['CashC'], 0.01) == 0.1

def test_portfolio_rebalance(portfolio):
    new_port = portfolio.rebalance()
    # After rebalance, values should match allocation * total
    total = portfolio.total_value
    for k, v in new_port.asset_values.items():
        assert pytest.approx(v, 0.01) == portfolio.allocation.allocation[k] * total

def test_portfolio_get_asset(portfolio):
    asset = portfolio.get_asset('StockA')
    assert asset.name == 'StockA'
    with pytest.raises(PortfolioError):
        portfolio.get_asset('NotExist')

def test_static_rebalancing_strategy(portfolio):
    strat = StaticRebalancingStrategy()
    result = strat.rebalance(portfolio)
    total = portfolio.total_value
    for k, v in result.items():
        assert pytest.approx(v, 0.01) == portfolio.allocation.allocation[k] * total