#!/usr/bin/env python3
"""
Generic retirement analysis runner with subcommands.

This script provides a command-line interface to run retirement analysis
using configuration files provided by the user.

Subcommands:
  validate   Validate configuration files
  analyze    Run complete retirement analysis with simulation and reporting
  report     Generate reports from existing analysis results
  simulate   Run Monte Carlo simulation only
"""

import sys
import argparse
from pathlib import Path
from datetime import datetime

def add_common_arguments(parser):
    parser.add_argument(
        "--person-profile",
        required=True,
        help="Path to person profile configuration file"
    )
    parser.add_argument(
        "--events",
        required=True,
        help="Path to events configuration file"
    )
    parser.add_argument(
        "--market-data",
        required=True,
        help="Path to market data configuration file"
    )
    parser.add_argument(
        "--simulation-config",
        required=True,
        help="Path to simulation configuration file"
    )
    parser.add_argument(
        "--output-dir",
        default="results",
        help="Directory to save analysis results"
    )
    parser.add_argument(
        "--verbose",
        action="store_true",
        help="Enable verbose output"
    )

def validate_configs(args):
    """Validate all configuration files and print errors/warnings."""
    from retirement_planner.core.config import ConfigLoader
    from retirement_planner.core.logging import RetirementPlannerLogger, LogLevel
    logger = RetirementPlannerLogger(log_level=LogLevel.INFO if args.verbose else LogLevel.WARNING)
    success = True
    for name, path in [
        ("Person profile", args.person_profile),
        ("Events", args.events),
        ("Market data", args.market_data),
        ("Simulation config", args.simulation_config),
    ]:
        logger.log(LogLevel.INFO, f"Validating {name} file: {path}")
        loader = ConfigLoader()
        try:
            loader.load_from_file(path)
            logger.log(LogLevel.SUCCESS, f"{name} file loaded and validated successfully.")
        except Exception as e:
            logger.log(LogLevel.ERROR, f"{name} file validation failed: {e}")
            success = False
    if not success:
        print("\nValidation failed. Please fix the above errors.")
        sys.exit(1)
    print("\nAll configuration files validated successfully.")

def analyze(args):
    """Run the complete retirement analysis with simulation and reporting."""
    output_dir = Path(args.output_dir)
    output_dir.mkdir(exist_ok=True)
    # Generate timestamp ONCE for all outputs
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    print("=" * 60)
    print("RETIREMENT PLANNER ANALYSIS")
    print("=" * 60)
    print(f"Analysis started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()

    try:
        from retirement_planner.core.config import ConfigLoader
        from retirement_planner.core.logging import RetirementPlannerLogger, LogLevel
        from retirement_planner.models.person import Person, Goal
        from retirement_planner.models.events import EventManager, Event, EventType, Period
        from retirement_planner.models.portfolio import Portfolio, AssetAllocation, StaticRebalancingStrategy
        from retirement_planner.assets.base import AssetFactory
        from retirement_planner.simulation.engine import MonteCarloEngine, RandomScenarioGenerator, MarketSimulator
        from retirement_planner.simulation.market import CorrelatedMarketModel, CorrelationModel
        from retirement_planner.analysis.retirement import RetirementAnalyzer
        from retirement_planner.analysis.withdrawal import WithdrawalOptimizer
        from retirement_planner.reports.generator import ReportGenerator, ReportConfig

        logger = RetirementPlannerLogger(log_level=LogLevel.INFO if args.verbose else LogLevel.WARNING)
        logger.log(LogLevel.INFO, "Starting comprehensive retirement analysis")

        # Load person profile
        logger.log(LogLevel.INFO, "Loading person profile...")
        person_loader = ConfigLoader()
        person_loader.load_from_file(args.person_profile)
        person_data = person_loader.config_data
        person = Person(
            name=person_data["name"],
            age=person_data["age"],
            retirement_age=person_data["retirement_age"],
            life_expectancy=person_data["life_expectancy"],
            risk_tolerance=person_data["risk_tolerance"],
            tax_filing_status=person_data["tax_filing_status"],
            state_of_residence=person_data["state_of_residence"],
            goals=[Goal(**goal) for goal in person_data["goals"]],
            additional_data=person_data.get("additional_data", {})
        )
        logger.log(LogLevel.INFO, f"Loaded person profile for {person.name}")
        logger.log(LogLevel.INFO, f"Current age: {person.age}, Retirement age: {person.retirement_age}")

        # Load events
        logger.log(LogLevel.INFO, "Loading events configuration...")
        events_loader = ConfigLoader()
        events_loader.load_from_file(args.events)
        events_data = events_loader.config_data
        event_manager = EventManager()
        for category, events_list in events_data["events"].items():
            for event_data in events_list:
                period = Period(**event_data["period"])
                event = Event(
                    name=event_data["name"],
                    event_type=EventType(event_data["event_type"]),
                    period=period,
                    amount=event_data["amount"],
                    probability=event_data["probability"],
                    inflation_adjustment=False,  # No inflation adjustment since we use real returns
                    description=event_data["description"],
                    metadata=event_data.get("metadata", {})
                )
                event_manager.add_event(event)
        logger.log(LogLevel.INFO, f"Loaded {len(event_manager.events)} events (all in today's dollars)")

        # Extract initial portfolio value from events
        initial_portfolio_event = None
        for event in event_manager.events:
            if event.name == "initial_portfolio":
                initial_portfolio_event = event
                break

        if initial_portfolio_event:
            logger.log(LogLevel.INFO, f"Initial portfolio value: ${initial_portfolio_event.amount:,.0f}")

        # Load market data and create portfolio
        logger.log(LogLevel.INFO, "Loading market data and creating portfolio...")
        market_loader = ConfigLoader()
        market_loader.load_from_file(args.market_data)
        market_data = market_loader.config_data

        # Get inflation rate from market data
        inflation_rate = market_data.get("inflation", {}).get("expected_rate", 0.025)
        logger.log(LogLevel.INFO, f"Inflation rate: {inflation_rate:.1%}")

        # Create assets using factory - handle both formats
        asset_factory = AssetFactory()
        assets = []

        # Check if we have individual asset configurations or need to create from allocation
        if "assets" in market_data:
            # Individual asset configurations provided
            for asset_config in market_data["assets"]:
                asset = asset_factory.create_from_dict(asset_config)
                assets.append(asset)
        else:
            # Create assets from allocation percentages
            allocation = market_data["portfolio_allocation"]
            expected_returns = market_data["expected_returns"]
            volatilities = market_data["volatility"]

            # Create basic assets from allocation
            for asset_type, weight in allocation.items():
                if weight > 0:
                    asset_config = {
                        "name": f"{asset_type.title()} Asset",
                        "asset_type": asset_type,
                        "current_value": initial_portfolio_event.amount * weight if initial_portfolio_event else 0,
                        "expected_return": expected_returns[asset_type],
                        "volatility": volatilities[asset_type],
                        "correlation": {},
                        "description": f"{asset_type.title()} allocation"
                    }
                    asset = asset_factory.create_from_dict(asset_config)
                    assets.append(asset)

        # Create portfolio with asset allocation
        if "portfolio_allocation" in market_data:
            allocation_data = market_data["portfolio_allocation"]
            # Convert allocation percentages to target weights
            target_weights = list(allocation_data.values())
            current_values = [asset.current_value for asset in assets]

            # Create asset dictionaries for portfolio
            assets_dict = {asset.name: asset for asset in assets}
            asset_values_dict = {asset.name: asset.current_value for asset in assets}

            # Create allocation using the asset names, not the YAML keys
            asset_allocation = {asset.name: allocation_data[asset_type] for asset_type, asset in zip(allocation_data.keys(), assets)}
            allocation = AssetAllocation(allocation=asset_allocation)
        else:
            # Use equal weights if no allocation specified
            target_weights = [1.0 / len(assets)] * len(assets)
            current_values = [asset.current_value for asset in assets]

            # Create asset dictionaries for portfolio
            assets_dict = {asset.name: asset for asset in assets}
            asset_values_dict = {asset.name: asset.current_value for asset in assets}

            # Create equal allocation
            equal_allocation = {asset.name: 1.0 / len(assets) for asset in assets}
            allocation = AssetAllocation(allocation=equal_allocation)

        portfolio = Portfolio(
            assets=assets_dict,
            allocation=allocation,
            asset_values=asset_values_dict,
            rebalancing_strategy=StaticRebalancingStrategy()
        )

        logger.log(LogLevel.INFO, f"Created portfolio with {len(assets)} assets")
        logger.log(LogLevel.INFO, f"Portfolio value: ${portfolio.total_value:,.0f}")
        logger.log(LogLevel.INFO, f"Portfolio asset names: {list(portfolio.assets.keys())}")
        logger.log(LogLevel.INFO, f"Portfolio asset values keys: {list(portfolio.asset_values.keys())}")

        # Load simulation configuration
        logger.log(LogLevel.INFO, "Loading simulation configuration...")
        sim_loader = ConfigLoader()
        sim_loader.load_from_file(args.simulation_config)
        sim_data = sim_loader.config_data

        # Create market model - handle both formats
        if "expected_returns" in market_data and "volatility" in market_data:
            # Use the allocation-based format
            expected_returns = list(market_data["expected_returns"].values())
            volatilities = list(market_data["volatility"].values())
            correlation_matrix = market_data["correlation_matrix"]
        else:
            # Use asset-specific format
            expected_returns = [asset.expected_return for asset in assets]
            volatilities = [asset.volatility for asset in assets]
            # Create identity correlation matrix
            correlation_matrix = [[1.0 if i == j else 0.0 for j in range(len(assets))] for i in range(len(assets))]

        # Create correlation model
        correlation_model = CorrelationModel(correlation_matrix=correlation_matrix)

        market_model = CorrelatedMarketModel(
            correlation_model=correlation_model,
            seed=sim_data["simulation"].get("seed", None)
        )

        # Run Monte Carlo simulation
        logger.log(LogLevel.INFO, "Running Monte Carlo simulation...")
        logger.log(LogLevel.INFO, f"Scenarios: {sim_data['simulation']['num_scenarios']:,}")
        logger.log(LogLevel.INFO, f"Time horizon: {sim_data['simulation']['time_horizon']} years")

        scenario_generator = RandomScenarioGenerator(
            seed=sim_data["simulation"].get("seed", None)
        )

        market_simulator = MarketSimulator(
            correlation_matrix=correlation_matrix
        )

        simulation_engine = MonteCarloEngine(
            scenario_generator=scenario_generator,
            market_simulator=market_simulator,
            logger=logger
        )

        # Prepare cash flows from events
        time_horizon = sim_data["simulation"]["time_horizon"]
        withdrawals = []
        contributions = []
        start_age = person.age
        cash_flow_details = []  # For reporting
        for year in range(time_horizon):
            age = start_age + year
            context = {"year": year, "age": age}
            event_results = event_manager.process_events_at_age(age, context)
            net_cash_flow = (
                event_results['income'] + event_results['benefits'] + event_results['assets']
                - event_results['expenses'] - event_results['liabilities'] - event_results['tax_impact']
            )
            if net_cash_flow >= 0:
                contributions.append(net_cash_flow)
                withdrawals.append(0.0)
            else:
                contributions.append(0.0)
                withdrawals.append(-net_cash_flow)
            cash_flow_details.append({
                'year': year,
                'age': age,
                'income': event_results['income'] + event_results['benefits'],
                'expense': event_results['expenses']
            })
        logger.log(LogLevel.INFO, f"Contributions by year: {contributions}")
        logger.log(LogLevel.INFO, f"Withdrawals by year: {withdrawals}")

        # Print cash flow report
        report_lines = []
        report_lines.append("CASH FLOW REPORT (from events)")
        report_lines.append("Year | Age |   Income   |  Expense  ")
        report_lines.append("-----------------------------------")
        for row in cash_flow_details:
            report_lines.append(f"{row['year']:4d} | {row['age']:3d} | {row['income']:10,.0f} | {row['expense']:9,.0f}")
        report_lines.append("-----------------------------------\n")
        report_text = "\n".join(report_lines)
        print("\n" + report_text)
        # Use the same timestamp for all outputs
        cash_flow_report_path = output_dir / f"cash_flow_report_{timestamp}.txt"
        with open(cash_flow_report_path, "w") as f:
            f.write(report_text)
        logger.log(LogLevel.INFO, f"Cash flow report written to {cash_flow_report_path}")

        simulation_result = simulation_engine.run_simulation(
            portfolio=portfolio,
            num_scenarios=sim_data["simulation"]["num_scenarios"],
            time_horizon=time_horizon,
            withdrawals=withdrawals,
            contributions=contributions,
            inflation_rate=inflation_rate
        )

        logger.log(LogLevel.SUCCESS, f"Simulation completed. Success rate: {simulation_result.success_rate:.1f}%")

        # Run retirement analysis
        logger.log(LogLevel.INFO, "Running retirement analysis...")
        retirement_analyzer = RetirementAnalyzer(logger=logger)
        retirement_analysis = retirement_analyzer.analyze_retirement(
            person=person,
            portfolio=portfolio,
            simulation_result=simulation_result
        )

        logger.log(LogLevel.SUCCESS, f"Analysis completed. Overall success rate: {retirement_analysis.overall_success_rate:.1f}%")

        # Run withdrawal strategy optimization
        logger.log(LogLevel.INFO, "Optimizing withdrawal strategies...")
        withdrawal_optimizer = WithdrawalOptimizer(logger=logger)
        withdrawal_result = withdrawal_optimizer.optimize_withdrawal_rate(
            portfolio=portfolio,
            simulation_result=simulation_result,
            strategy_type="percentage",
            min_rate=0.02,
            max_rate=0.08,
            step_size=0.001
        )

        logger.log(LogLevel.SUCCESS, f"Withdrawal optimization completed. Optimal rate: {withdrawal_result.optimal_withdrawal_rate:.1%}")

        # Generate comprehensive report
        logger.log(LogLevel.INFO, "Generating comprehensive report...")
        report_config = ReportConfig(
            output_format="text",
            include_charts=True,
            chart_format="png",
            include_raw_data=True
        )

        report_generator = ReportGenerator(config=report_config, logger=logger)
        report_files = report_generator.generate_comprehensive_report(
            retirement_analysis=retirement_analysis,
            simulation_result=simulation_result,
            withdrawal_result=withdrawal_result,
            output_dir=output_dir,
            timestamp=timestamp
        )

        # Print summary
        print("\n" + "=" * 60)
        print("ANALYSIS SUMMARY")
        print("=" * 60)
        print(f"Person: {person.name}")
        print(f"Working years remaining: {person.get_working_years()}")
        print(f"Retirement years: {person.get_retirement_years()}")
        print(f"Portfolio value: ${portfolio.total_value:,.0f}")
        print(f"Simulation scenarios: {len(simulation_result.scenarios):,}")
        print(f"Overall success rate: {retirement_analysis.overall_success_rate:.1f}%")
        print(f"Optimal withdrawal rate: {withdrawal_result.optimal_withdrawal_rate:.1%}")
        print(f"Optimal annual withdrawal: ${withdrawal_result.optimal_annual_withdrawal:,.0f}")
        print(f"Output directory: {output_dir.absolute()}")
        print("=" * 60)

        logger.log(LogLevel.SUCCESS, "Comprehensive analysis completed successfully")

    except Exception as e:
        print(f"Error during analysis: {e}")
        if args.verbose:
            import traceback
            traceback.print_exc()
        sys.exit(1)

def report(args):
    """Generate reports from existing analysis results."""
    print("Report generation from existing results is not yet implemented.")
    print("Use the 'analyze' command to run a complete analysis with reporting.")
    sys.exit(0)

def simulate(args):
    """Run Monte Carlo simulation only."""
    output_dir = Path(args.output_dir)
    output_dir.mkdir(exist_ok=True)
    print("=" * 60)
    print("MONTE CARLO SIMULATION")
    print("=" * 60)
    print(f"Simulation started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()

    try:
        from retirement_planner.core.config import ConfigLoader
        from retirement_planner.core.logging import RetirementPlannerLogger
        from retirement_planner.models.person import Person, Goal
        from retirement_planner.models.events import EventManager, Event, EventType, Period
        from retirement_planner.models.portfolio import Portfolio, AssetAllocation
        from retirement_planner.assets.base import AssetFactory
        from retirement_planner.simulation.engine import MonteCarloEngine, RandomScenarioGenerator, MarketSimulator
        from retirement_planner.simulation.market import CorrelatedMarketModel
        from retirement_planner.reports.generator import DataExporter

        logger = RetirementPlannerLogger(level="INFO" if args.verbose else "WARNING")
        logger.log("Starting Monte Carlo simulation", level="info")

        # Load configurations (same as analyze function)
        # ... (load person, events, market data, simulation config)

        # Create portfolio and run simulation
        # ... (create assets, portfolio, market model, run simulation)

        # Export simulation data
        data_exporter = DataExporter(logger=logger)
        sim_data_path = output_dir / "simulation_data.csv"
        data_exporter.export_simulation_data(
            simulation_result=simulation_result,  # This would be from the simulation
            output_path=sim_data_path,
            format="csv"
        )

        print("\n" + "=" * 60)
        print("SIMULATION SUMMARY")
        print("=" * 60)
        print(f"Simulation data exported to: {sim_data_path}")
        print("=" * 60)

        logger.log("Simulation completed successfully", level="success")

    except Exception as e:
        print(f"Error during simulation: {e}")
        if args.verbose:
            import traceback
            traceback.print_exc()
        sys.exit(1)

def main():
    parser = argparse.ArgumentParser(
        description="Retirement Planner CLI with subcommands"
    )
    subparsers = parser.add_subparsers(dest="command", required=True, help="Subcommand to run")

    # Validate subcommand
    parser_validate = subparsers.add_parser("validate", help="Validate configuration files")
    add_common_arguments(parser_validate)
    parser_validate.set_defaults(func=validate_configs)

    # Analyze subcommand
    parser_analyze = subparsers.add_parser("analyze", help="Run complete retirement analysis with simulation and reporting")
    add_common_arguments(parser_analyze)
    parser_analyze.set_defaults(func=analyze)

    # Report subcommand
    parser_report = subparsers.add_parser("report", help="Generate reports from existing analysis results")
    add_common_arguments(parser_report)
    parser_report.set_defaults(func=report)

    # Simulate subcommand
    parser_simulate = subparsers.add_parser("simulate", help="Run Monte Carlo simulation only")
    add_common_arguments(parser_simulate)
    parser_simulate.set_defaults(func=simulate)

    args = parser.parse_args()
    args.func(args)

if __name__ == "__main__":
    main()