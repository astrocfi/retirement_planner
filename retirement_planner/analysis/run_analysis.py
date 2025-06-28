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
    from retirement_planner.core.logging import RetirementPlannerLogger
    logger = RetirementPlannerLogger(level="INFO" if args.verbose else "WARNING")
    success = True
    for name, path in [
        ("Person profile", args.person_profile),
        ("Events", args.events),
        ("Market data", args.market_data),
        ("Simulation config", args.simulation_config),
    ]:
        logger.log(f"Validating {name} file: {path}", level="info")
        loader = ConfigLoader()
        try:
            loader.load_from_file(path)
            logger.log(f"{name} file loaded and validated successfully.", level="success")
        except Exception as e:
            logger.log(f"{name} file validation failed: {e}", level="error")
            success = False
    if not success:
        print("\nValidation failed. Please fix the above errors.")
        sys.exit(1)
    print("\nAll configuration files validated successfully.")

def analyze(args):
    """Run the complete retirement analysis with simulation and reporting."""
    output_dir = Path(args.output_dir)
    output_dir.mkdir(exist_ok=True)
    print("=" * 60)
    print("RETIREMENT PLANNER ANALYSIS")
    print("=" * 60)
    print(f"Analysis started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()

    try:
        from retirement_planner.core.config import ConfigLoader
        from retirement_planner.core.logging import RetirementPlannerLogger
        from retirement_planner.models.person import Person, Goal
        from retirement_planner.models.events import EventManager, Event, EventType, Period
        from retirement_planner.models.portfolio import Portfolio, AssetAllocation
        from retirement_planner.assets.factory import AssetFactory
        from retirement_planner.simulation.engine import MonteCarloEngine, RandomScenarioGenerator, MarketSimulator
        from retirement_planner.simulation.market import CorrelatedMarketModel
        from retirement_planner.analysis.retirement import RetirementAnalyzer
        from retirement_planner.analysis.withdrawal import WithdrawalOptimizer
        from retirement_planner.reports.generator import ReportGenerator, ReportConfig

        logger = RetirementPlannerLogger(level="INFO" if args.verbose else "WARNING")
        logger.log("Starting comprehensive retirement analysis", level="info")

        # Load person profile
        logger.log("Loading person profile...", level="info")
        person_loader = ConfigLoader()
        person_loader.load_from_file(args.person_profile)
        person_data = person_loader.config_data
        person = Person(
            name=person_data["name"],
            age=person_data["age"],
            retirement_age=person_data["retirement_age"],
            life_expectancy=person_data["life_expectancy"],
            current_savings=person_data["current_savings"],
            annual_contribution=person_data["annual_contribution"],
            risk_tolerance=person_data["risk_tolerance"],
            tax_filing_status=person_data["tax_filing_status"],
            state_of_residence=person_data["state_of_residence"],
            goals=[Goal(**goal) for goal in person_data["goals"]],
            additional_data=person_data.get("additional_data", {})
        )
        logger.log(f"Loaded person profile for {person.name}", level="info")
        logger.log(f"Current age: {person.age}, Retirement age: {person.retirement_age}", level="info")
        logger.log(f"Current savings: ${person.current_savings:,.0f}", level="info")

        # Load events
        logger.log("Loading events configuration...", level="info")
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
                    inflation_adjustment=event_data["inflation_adjustment"],
                    description=event_data["description"],
                    metadata=event_data.get("metadata", {})
                )
                event_manager.add_event(event)
        logger.log(f"Loaded {len(event_manager.events)} events", level="info")

        # Load market data and create portfolio
        logger.log("Loading market data and creating portfolio...", level="info")
        market_loader = ConfigLoader()
        market_loader.load_from_file(args.market_data)
        market_data = market_loader.config_data

        # Create assets using factory
        asset_factory = AssetFactory()
        assets = []
        for asset_config in market_data["assets"]:
            asset = asset_factory.create_asset(asset_config)
            assets.append(asset)

        # Create portfolio with asset allocation
        allocation_data = market_data["portfolio_allocation"]
        allocation = AssetAllocation(
            assets=assets,
            target_weights=allocation_data["target_weights"],
            current_values=allocation_data["current_values"]
        )

        portfolio = Portfolio(
            assets=assets,
            allocation=allocation,
            rebalancing_strategy="static"
        )

        logger.log(f"Created portfolio with {len(assets)} assets", level="info")
        logger.log(f"Portfolio value: ${portfolio.get_total_value():,.0f}", level="info")

        # Load simulation configuration
        logger.log("Loading simulation configuration...", level="info")
        sim_loader = ConfigLoader()
        sim_loader.load_from_file(args.simulation_config)
        sim_data = sim_loader.config_data

        # Create market model
        market_model = CorrelatedMarketModel(
            assets=assets,
            expected_returns=market_data["expected_returns"],
            volatilities=market_data["volatilities"],
            correlation_matrix=market_data["correlation_matrix"],
            seed=sim_data["simulation"].get("seed", None)
        )

        # Run Monte Carlo simulation
        logger.log("Running Monte Carlo simulation...", level="info")
        logger.log(f"Scenarios: {sim_data['simulation']['num_scenarios']:,}", level="info")
        logger.log(f"Time horizon: {sim_data['simulation']['time_horizon']} years", level="info")

        scenario_generator = RandomScenarioGenerator(
            time_horizon=sim_data["simulation"]["time_horizon"]
        )

        market_simulator = MarketSimulator(
            market_model=market_model,
            event_manager=event_manager
        )

        simulation_engine = MonteCarloEngine(
            scenario_generator=scenario_generator,
            market_simulator=market_simulator,
            logger=logger
        )

        simulation_result = simulation_engine.run_simulation(
            portfolio=portfolio,
            num_scenarios=sim_data["simulation"]["num_scenarios"],
            person=person
        )

        logger.log(f"Simulation completed. Success rate: {simulation_result.success_rate:.1f}%", level="success")

        # Run retirement analysis
        logger.log("Running retirement analysis...", level="info")
        retirement_analyzer = RetirementAnalyzer(logger=logger)
        retirement_analysis = retirement_analyzer.analyze_retirement(
            person=person,
            simulation_result=simulation_result,
            goals=person.goals
        )

        logger.log(f"Analysis completed. Overall success rate: {retirement_analysis.overall_success_rate:.1f}%", level="success")

        # Run withdrawal strategy optimization
        logger.log("Optimizing withdrawal strategies...", level="info")
        withdrawal_optimizer = WithdrawalOptimizer(logger=logger)
        withdrawal_result = withdrawal_optimizer.optimize_withdrawal_strategies(
            person=person,
            simulation_result=simulation_result,
            target_income=person.goals[0].target_amount if person.goals else 50000
        )

        logger.log(f"Withdrawal optimization completed. Best strategy: {withdrawal_result.best_strategy.name}", level="success")

        # Generate comprehensive report
        logger.log("Generating comprehensive report...", level="info")
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
            output_dir=output_dir
        )

        # Print summary
        print("\n" + "=" * 60)
        print("ANALYSIS SUMMARY")
        print("=" * 60)
        print(f"Person: {person.name}")
        print(f"Working years remaining: {person.get_working_years()}")
        print(f"Retirement years: {person.get_retirement_years()}")
        print(f"Portfolio value: ${portfolio.get_total_value():,.0f}")
        print(f"Simulation scenarios: {simulation_result.num_scenarios:,}")
        print(f"Overall success rate: {retirement_analysis.overall_success_rate:.1f}%")
        print(f"Best withdrawal strategy: {withdrawal_result.best_strategy.name}")
        print(f"Recommended annual withdrawal: ${withdrawal_result.best_strategy.avg_annual_withdrawal:,.0f}")
        print(f"Output directory: {output_dir.absolute()}")
        print("=" * 60)

        logger.log("Comprehensive analysis completed successfully", level="success")

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
        from retirement_planner.assets.factory import AssetFactory
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