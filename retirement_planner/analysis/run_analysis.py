#!/usr/bin/env python3
"""
Generic retirement analysis runner with subcommands.

This script provides a command-line interface to run retirement analysis
using unified configuration files with section merging.

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
import numpy as np

def add_common_arguments(parser):
    parser.add_argument(
        "--config",
        required=True,
        nargs='+',
        help="Path to one or more configuration files (later files override earlier ones)"
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
    from retirement_planner.core.config import UnifiedConfigLoader
    from retirement_planner.core.logging import RetirementPlannerLogger, LogLevel

    logger = RetirementPlannerLogger(log_level=LogLevel.INFO if args.verbose else LogLevel.WARNING)
    success = True

    try:
        logger.log(LogLevel.INFO, f"Validating configuration files: {', '.join(args.config)}")
        loader = UnifiedConfigLoader()
        loader.load_from_files(args.config)

        required_sections = ['person', 'assets', 'asset_performance', 'events', 'simulation']
        for section in required_sections:
            if loader.has_section(section):
                logger.log(LogLevel.SUCCESS, f"Section '{section}' found and validated.")
            else:
                logger.log(LogLevel.ERROR, f"Required section '{section}' not found in configuration.")
                success = False

        if loader.has_section('person'):
            person_data = loader.get_section('person')
            required_person_fields = ['name', 'age', 'retirement_age', 'life_expectancy', 'risk_tolerance']
            for field in required_person_fields:
                if field not in person_data:
                    logger.log(LogLevel.ERROR, f"Required person field '{field}' not found.")
                    success = False

        if loader.has_section('assets'):
            assets_data = loader.get_section('assets')
            if not isinstance(assets_data, list):
                logger.log(LogLevel.ERROR, "Assets section must be a list.")
                success = False
            else:
                for i, asset in enumerate(assets_data):
                    if not isinstance(asset, dict) or 'type' not in asset or 'current_value' not in asset:
                        logger.log(LogLevel.ERROR, f"Asset {i} must have 'type' and 'current_value' fields.")
                        success = False

        if loader.has_section('asset_performance'):
            perf_data = loader.get_section('asset_performance')
            if not isinstance(perf_data, list):
                logger.log(LogLevel.ERROR, "Asset performance section must be a list.")
                success = False
            else:
                for i, perf in enumerate(perf_data):
                    if not isinstance(perf, dict) or 'type' not in perf:
                        logger.log(LogLevel.ERROR, f"Asset performance {i} must have 'type' field.")
                        success = False

        if success:
            logger.log(LogLevel.SUCCESS, "All configuration files validated successfully.")
        else:
            logger.log(LogLevel.ERROR, "Configuration validation failed.")

    except Exception as e:
        logger.log(LogLevel.ERROR, f"Configuration validation failed: {e}")
        success = False

    if not success:
        print("\nValidation failed. Please fix the above errors.")
        sys.exit(1)
    print("\nAll configuration files validated successfully.")

def analyze(args):
    """Run the complete retirement analysis with simulation and reporting."""
    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    print("=" * 60)
    print("RETIREMENT PLANNER ANALYSIS")
    print("=" * 60)
    print(f"Analysis started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()

    try:
        from retirement_planner.core.config import UnifiedConfigLoader
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

        logger.log(LogLevel.INFO, f"Loading configuration from: {', '.join(args.config)}")
        config_loader = UnifiedConfigLoader()
        config_loader.load_from_files(args.config)

        # Set the random seed ONCE at the very start
        simulation_data = config_loader.get_section('simulation')
        random_seed = simulation_data.get("random_seed", 42)
        np.random.seed(random_seed)

        logger.log(LogLevel.INFO, "Loading person profile...")
        person_data = config_loader.get_section('person')
        person = Person(
            name=person_data["name"],
            age=person_data["age"],
            retirement_age=person_data["retirement_age"],
            life_expectancy=person_data["life_expectancy"],
            risk_tolerance=person_data["risk_tolerance"],
            tax_filing_status=person_data.get("tax_filing_status", "single"),
            state_of_residence=person_data.get("state_of_residence", "CA"),
            goals=[Goal(**goal) for goal in person_data.get("goals", [])],
            additional_data=person_data.get("additional_data", {})
        )
        logger.log(LogLevel.INFO, f"Loaded person profile for {person.name}")
        logger.log(LogLevel.INFO, f"Current age: {person.age}, Retirement age: {person.retirement_age}")

        logger.log(LogLevel.INFO, "Loading events configuration...")
        events_data = config_loader.get_section('events')
        event_manager = EventManager()

        # Process income events
        for event_data in events_data.get("income", []):
            period = Period(**event_data["period"])
            event = Event(
                name=event_data["name"],
                event_type=EventType(event_data["event_type"]),
                period=period,
                amount=event_data["amount"],
                probability=event_data.get("probability", 1.0),
                inflation_adjustment=False,
                description=event_data.get("description", ""),
                metadata=event_data.get("metadata", {})
            )
            event_manager.add_event(event)

        # Process expense events
        for event_data in events_data.get("expenses", []):
            period = Period(**event_data["period"])
            event = Event(
                name=event_data["name"],
                event_type=EventType(event_data["event_type"]),
                period=period,
                amount=event_data["amount"],
                probability=event_data.get("probability", 1.0),
                inflation_adjustment=False,
                description=event_data.get("description", ""),
                metadata=event_data.get("metadata", {})
            )
            event_manager.add_event(event)

        # Process asset events
        for event_data in events_data.get("assets", []):
            period = Period(**event_data["period"])
            event = Event(
                name=event_data["name"],
                event_type=EventType(event_data["event_type"]),
                period=period,
                amount=event_data["amount"],
                probability=event_data.get("probability", 1.0),
                inflation_adjustment=False,
                description=event_data.get("description", ""),
                metadata=event_data.get("metadata", {})
            )
            event_manager.add_event(event)

        # Process liability events
        for event_data in events_data.get("liabilities", []):
            period = Period(**event_data["period"])
            event = Event(
                name=event_data["name"],
                event_type=EventType(event_data["event_type"]),
                period=period,
                amount=event_data["amount"],
                probability=event_data.get("probability", 1.0),
                inflation_adjustment=False,
                description=event_data.get("description", ""),
                metadata=event_data.get("metadata", {})
            )
            event_manager.add_event(event)

        # Process benefit events
        for event_data in events_data.get("benefits", []):
            period = Period(**event_data["period"])
            event = Event(
                name=event_data["name"],
                event_type=EventType(event_data["event_type"]),
                period=period,
                amount=event_data["amount"],
                probability=event_data.get("probability", 1.0),
                inflation_adjustment=False,
                description=event_data.get("description", ""),
                metadata=event_data.get("metadata", {})
            )
            event_manager.add_event(event)

        logger.log(LogLevel.INFO, f"Loaded {len(event_manager.events)} events (all in today's dollars)")

        initial_portfolio_event = None
        for event in event_manager.events:
            if event.name == "initial_portfolio":
                initial_portfolio_event = event
                break

        if initial_portfolio_event:
            logger.log(LogLevel.INFO, f"Initial portfolio value: ${initial_portfolio_event.amount:,.0f}")

        logger.log(LogLevel.INFO, "Loading asset performance data and creating assets...")
        assets_data = config_loader.get_section('assets')
        asset_performance_data = config_loader.get_section('asset_performance')

        performance_lookup = {perf['type']: perf for perf in asset_performance_data}

        asset_factory = AssetFactory()
        assets = []
        total_portfolio_value = 0

        for asset_data in assets_data:
            asset_type = asset_data['type']
            current_value = asset_data['current_value']
            total_portfolio_value += current_value

            if asset_type not in performance_lookup:
                raise ValueError(f"Asset type '{asset_type}' not found in asset_performance section")

            perf_data = performance_lookup[asset_type]

            asset_config = {
                "name": asset_type,
                "asset_type": perf_data["asset_type"],
                "current_value": current_value,
                "expected_return": perf_data["expected_return"],
                "volatility": perf_data["volatility"],
                "correlation": perf_data.get("correlation", {}),
                "description": perf_data.get("description", ""),
                "metadata": {**perf_data, "notes": asset_data.get("notes", "")}
            }

            asset = asset_factory.create_from_dict(asset_config)
            assets.append(asset)

        logger.log(LogLevel.INFO, f"Created {len(assets)} assets with total value: ${total_portfolio_value:,.0f}")

        economy_data = config_loader.get_section('economy')
        inflation_rate = economy_data.get("inflation", {}).get("expected_rate", 0.025)
        logger.log(LogLevel.INFO, f"Inflation rate: {inflation_rate:.1%}")

        allocation_data = {}
        for asset in assets:
            allocation_data[asset.name] = asset.current_value / total_portfolio_value

        allocation = AssetAllocation(allocation_data)
        portfolio = Portfolio(
            assets=assets,
            allocation_targets=allocation,
            rebalancing_strategy=StaticRebalancingStrategy()
        )
        logger.log(LogLevel.INFO, f"Created portfolio with allocation: {allocation_data}")

        logger.log(LogLevel.INFO, "Loading simulation configuration...")
        simulation_data = config_loader.get_section('simulation')

        scenario_generator = RandomScenarioGenerator(
            time_horizon=simulation_data.get("time_horizon", 45),
            random_seed=simulation_data.get("random_seed", 42)
        )

        correlation_matrix = {}
        for perf in asset_performance_data:
            if "correlation" in perf and perf["correlation"]:
                correlation_matrix[perf["type"]] = perf["correlation"]
        correlation_model = CorrelationModel(correlation_matrix)

        market_model = CorrelatedMarketModel(
            correlation_model=correlation_model,
            seed=simulation_data.get("random_seed", 42)
        )

        market_simulator = MarketSimulator(market_model)

        engine = MonteCarloEngine(
            scenario_generator=scenario_generator,
            market_simulator=market_simulator,
            num_scenarios=simulation_data.get("num_scenarios", 10000)
        )

        logger.log(LogLevel.INFO, f"Created Monte Carlo engine with {simulation_data.get('num_scenarios', 10000)} scenarios")

        logger.log(LogLevel.INFO, "Running Monte Carlo simulation...")
        simulation_result = engine.run_simulation(portfolio, person.get_working_years() + person.get_retirement_years(), event_manager, person)
        logger.log(LogLevel.SUCCESS, f"Simulation completed with {len(simulation_result.scenarios)} successful scenarios")

        logger.log(LogLevel.INFO, "Running retirement analysis...")
        analyzer = RetirementAnalyzer()
        analysis_result = analyzer.analyze_retirement(
            person=person,
            portfolio=portfolio,
            simulation_result=simulation_result
        )
        logger.log(LogLevel.SUCCESS, f"Analysis completed. Success rate: {analysis_result.overall_success_rate:.1%}")

        logger.log(LogLevel.INFO, "Running withdrawal optimization...")
        optimizer = WithdrawalOptimizer()
        withdrawal_result = optimizer.optimize_withdrawal_rate(
            portfolio=portfolio,
            simulation_result=simulation_result
        )
        logger.log(LogLevel.SUCCESS, f"Withdrawal optimization completed. Optimal rate: {withdrawal_result.optimal_withdrawal_rate:.1%}")

        logger.log(LogLevel.INFO, "Generating reports...")
        report_config = ReportConfig(
            output_format="html",
            include_charts=True,
            include_raw_data=True
        )

        report_generator = ReportGenerator(report_config)
        report_result = report_generator.generate_comprehensive_report(
            retirement_analysis=analysis_result,
            simulation_result=simulation_result,
            withdrawal_result=withdrawal_result,
            output_dir=output_dir,
            timestamp=timestamp
        )

        logger.log(LogLevel.SUCCESS, f"Reports generated successfully in {output_dir}")
        logger.log(LogLevel.INFO, f"Report files: {list(report_result.values())}")

        print("\n" + "=" * 60)
        print("ANALYSIS COMPLETE")
        print("=" * 60)
        print(f"Success Rate: {analysis_result.overall_success_rate:.1%}")
        print(f"Optimal Withdrawal Rate: {withdrawal_result.optimal_withdrawal_rate:.1%}")
        print(f"Optimal Annual Withdrawal: ${withdrawal_result.optimal_annual_withdrawal:,.0f}")
        print(f"Reports saved to: {output_dir}")
        print("=" * 60)

    except Exception as e:
        print(f"\nAnalysis failed: {e}")
        if args.verbose:
            import traceback
            traceback.print_exc()
        sys.exit(1)

def report(args):
    print("Report generation from existing results not yet implemented.")
    sys.exit(1)

def simulate(args):
    print("Simulation-only mode not yet implemented.")
    sys.exit(1)

def main():
    parser = argparse.ArgumentParser(
        description="Retirement Planner CLI with subcommands",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s validate --config config.yaml
  %(prog)s validate --config base.yaml override.yaml
  %(prog)s analyze --config config.yaml --output-dir results
  %(prog)s analyze --config base.yaml override.yaml --verbose
        """
    )

    subparsers = parser.add_subparsers(dest='command', help='Subcommand to run')

    validate_parser = subparsers.add_parser('validate', help='Validate configuration files')
    add_common_arguments(validate_parser)
    validate_parser.set_defaults(func=validate_configs)

    analyze_parser = subparsers.add_parser('analyze', help='Run complete retirement analysis with simulation and reporting')
    add_common_arguments(analyze_parser)
    analyze_parser.set_defaults(func=analyze)

    report_parser = subparsers.add_parser('report', help='Generate reports from existing analysis results')
    add_common_arguments(report_parser)
    report_parser.set_defaults(func=report)

    simulate_parser = subparsers.add_parser('simulate', help='Run Monte Carlo simulation only')
    add_common_arguments(simulate_parser)
    simulate_parser.set_defaults(func=simulate)

    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        sys.exit(1)

    args.func(args)

if __name__ == "__main__":
    main()