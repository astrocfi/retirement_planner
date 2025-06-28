"""
Report generation for retirement analysis results.

This module provides comprehensive reporting capabilities including
text reports, charts, and data export functionality.
"""

import json
import csv
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Any, Optional, Union
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
import numpy as np
import pandas as pd
from dataclasses import dataclass

from retirement_planner.core.exceptions import AnalysisError
from retirement_planner.core.logging import RetirementPlannerLogger, LogLevel
from retirement_planner.analysis.retirement import RetirementAnalysis
from retirement_planner.analysis.withdrawal import WithdrawalOptimizationResult
from retirement_planner.simulation.engine import SimulationResult
from retirement_planner.models.portfolio import Portfolio


@dataclass
class ReportConfig:
    """Configuration for report generation."""
    output_format: str = "text"  # text, html, json
    include_charts: bool = True
    chart_format: str = "png"  # png, pdf, svg
    include_raw_data: bool = False
    custom_styles: Optional[Dict[str, Any]] = None


class ChartCreator:
    """Creates charts and visualizations for retirement analysis."""

    def __init__(self, logger: Optional[RetirementPlannerLogger] = None):
        self.logger = logger or RetirementPlannerLogger()
        self._setup_matplotlib()

    def _setup_matplotlib(self):
        """Setup matplotlib with consistent styling."""
        plt.style.use('default')
        plt.rcParams['figure.figsize'] = (12, 8)
        plt.rcParams['font.size'] = 10
        plt.rcParams['axes.grid'] = True
        plt.rcParams['grid.alpha'] = 0.3

    def create_portfolio_evolution_chart(
        self,
        simulation_result: SimulationResult,
        output_path: Path,
        title: str = "Portfolio Evolution Over Time"
    ) -> Path:
        """Create portfolio evolution chart showing median and percentiles."""
        try:
            # Extract portfolio values over time
            years = list(range(simulation_result.time_horizon + 1))

            # Calculate percentiles across scenarios
            percentiles = [5, 25, 50, 75, 95]
            portfolio_values = np.array([
                [scenario.portfolio_values[year] for year in years]
                for scenario in simulation_result.scenarios
            ])

            percentile_values = np.percentile(portfolio_values, percentiles, axis=0)

            # Create the chart
            fig, ax = plt.subplots(figsize=(12, 8))

            # Plot percentiles
            colors = ['#ff7f0e', '#ffbb78', '#1f77b4', '#ffbb78', '#ff7f0e']
            labels = ['5th percentile', '25th percentile', 'Median', '75th percentile', '95th percentile']

            for i, (pct, color, label) in enumerate(zip(percentiles, colors, labels)):
                ax.plot(years, percentile_values[i], color=color, linewidth=2, label=label)

            # Fill between 25th and 75th percentiles
            ax.fill_between(years, percentile_values[1], percentile_values[3],
                          alpha=0.3, color='#1f77b4', label='25th-75th percentile range')

            ax.set_xlabel('Years')
            ax.set_ylabel('Portfolio Value ($)')
            ax.set_title(title)
            ax.legend()
            ax.grid(True, alpha=0.3)

            # Format y-axis as currency
            ax.yaxis.set_major_formatter(plt.FuncFormatter(lambda x, p: f'${x/1000:.0f}K'))

            plt.tight_layout()
            plt.savefig(output_path, dpi=300, bbox_inches='tight')
            plt.close()

            self.logger.log(LogLevel.INFO, f"Portfolio evolution chart saved to {output_path}")
            return output_path

        except Exception as e:
            raise AnalysisError(f"Failed to create portfolio evolution chart: {e}")

    def create_simulation_paths_chart(
        self,
        simulation_result: SimulationResult,
        output_path: Path,
        title: str = "Individual Simulation Paths",
        max_paths: int = 100
    ) -> Path:
        """Create chart showing individual simulation paths overlaid."""
        try:
            # Extract portfolio values over time
            years = list(range(simulation_result.time_horizon + 1))

            # Limit number of paths to avoid overcrowding
            num_scenarios = len(simulation_result.scenarios)
            if num_scenarios > max_paths:
                # Sample paths evenly across the range
                step = num_scenarios // max_paths
                selected_scenarios = simulation_result.scenarios[::step][:max_paths]
                self.logger.log(LogLevel.INFO, f"Showing {len(selected_scenarios)} paths out of {num_scenarios} total scenarios")
            else:
                selected_scenarios = simulation_result.scenarios

            # Create the chart
            fig, ax = plt.subplots(figsize=(14, 8))

            # Plot individual paths
            colors = plt.cm.viridis(np.linspace(0, 1, len(selected_scenarios)))

            for i, scenario in enumerate(selected_scenarios):
                # Use different colors for successful vs failed scenarios
                if scenario.success:
                    color = '#1f77b4'  # Blue for successful
                    alpha = 0.3
                else:
                    color = '#d62728'  # Red for failed
                    alpha = 0.5

                ax.plot(years, scenario.portfolio_values, color=color, alpha=alpha, linewidth=0.8)

            # Add median line for reference
            portfolio_values = np.array([
                [scenario.portfolio_values[year] for year in years]
                for scenario in simulation_result.scenarios
            ])
            median_values = np.median(portfolio_values, axis=0)
            ax.plot(years, median_values, color='#2ca02c', linewidth=3, label='Median Path', zorder=10)

            # Add success/failure legend
            from matplotlib.lines import Line2D
            legend_elements = [
                Line2D([0], [0], color='#1f77b4', alpha=0.5, linewidth=2, label='Successful Scenarios'),
                Line2D([0], [0], color='#d62728', alpha=0.5, linewidth=2, label='Failed Scenarios'),
                Line2D([0], [0], color='#2ca02c', linewidth=3, label='Median Path')
            ]
            ax.legend(handles=legend_elements, loc='upper left')

            ax.set_xlabel('Years')
            ax.set_ylabel('Portfolio Value ($)')
            ax.set_title(f"{title}\n(Showing {len(selected_scenarios)} paths, Success Rate: {simulation_result.success_rate:.1%})")
            ax.grid(True, alpha=0.3)

            # Format y-axis as currency
            ax.yaxis.set_major_formatter(plt.FuncFormatter(lambda x, p: f'${x/1000:.0f}K'))

            plt.tight_layout()
            plt.savefig(output_path, dpi=300, bbox_inches='tight')
            plt.close()

            self.logger.log(LogLevel.INFO, f"Simulation paths chart saved to {output_path}")
            return output_path

        except Exception as e:
            raise AnalysisError(f"Failed to create simulation paths chart: {e}")

    def create_success_rate_chart(
        self,
        retirement_analysis: RetirementAnalysis,
        output_path: Path,
        title: str = "Goal Success Rates"
    ) -> Path:
        """Create chart showing success rates for different goals."""
        try:
            goals = [gs.goal_name for gs in retirement_analysis.goal_statuses]
            success_rates = [gs.success_rate for gs in retirement_analysis.goal_statuses]

            fig, ax = plt.subplots(figsize=(10, 6))

            bars = ax.bar(goals, success_rates, color='#1f77b4', alpha=0.7)

            # Add value labels on bars
            for bar, rate in zip(bars, success_rates):
                height = bar.get_height()
                ax.text(bar.get_x() + bar.get_width()/2., height + 0.01,
                       f'{rate:.1%}', ha='center', va='bottom')

            ax.set_xlabel('Goals')
            ax.set_ylabel('Success Rate (%)')
            ax.set_title(title)
            ax.set_ylim(0, 1)
            ax.grid(True, alpha=0.3, axis='y')

            plt.xticks(rotation=45, ha='right')
            plt.tight_layout()
            plt.savefig(output_path, dpi=300, bbox_inches='tight')
            plt.close()

            self.logger.log(LogLevel.INFO, f"Success rate chart saved to {output_path}")
            return output_path

        except Exception as e:
            raise AnalysisError(f"Failed to create success rate chart: {e}")

    def create_withdrawal_strategy_chart(
        self,
        withdrawal_result: WithdrawalOptimizationResult,
        output_path: Path,
        title: str = "Withdrawal Strategy Comparison"
    ) -> Path:
        """Create chart comparing different withdrawal strategies."""
        try:
            # If strategies attribute exists, use it (multi-strategy case)
            if hasattr(withdrawal_result, 'strategies') and withdrawal_result.strategies:
                strategies = [strategy.name for strategy in withdrawal_result.strategies]
                success_rates = [strategy.success_rate for strategy in withdrawal_result.strategies]
                avg_withdrawals = [strategy.avg_annual_withdrawal for strategy in withdrawal_result.strategies]

                fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(15, 6))

                # Success rates
                bars1 = ax1.bar(strategies, success_rates, color='#2ca02c', alpha=0.7)
                for bar, rate in zip(bars1, success_rates):
                    height = bar.get_height()
                    ax1.text(bar.get_x() + bar.get_width()/2., height + 0.01,
                            f'{rate:.1%}', ha='center', va='bottom')

                ax1.set_xlabel('Withdrawal Strategy')
                ax1.set_ylabel('Success Rate (%)')
                ax1.set_title('Success Rates by Strategy')
                ax1.set_ylim(0, 1)
                ax1.grid(True, alpha=0.3, axis='y')
                plt.setp(ax1.xaxis.get_majorticklabels(), rotation=45, ha='right')

                # Average withdrawals
                bars2 = ax2.bar(strategies, avg_withdrawals, color='#d62728', alpha=0.7)
                for bar, amount in zip(bars2, avg_withdrawals):
                    height = bar.get_height()
                    ax2.text(bar.get_x() + bar.get_width()/2., height + 1000,
                            f'${amount/1000:.0f}K', ha='center', va='bottom')

                ax2.set_xlabel('Withdrawal Strategy')
                ax2.set_ylabel('Average Annual Withdrawal ($)')
                ax2.set_title('Average Annual Withdrawals')
                ax2.grid(True, alpha=0.3, axis='y')
                plt.setp(ax2.xaxis.get_majorticklabels(), rotation=45, ha='right')

                plt.tight_layout()
                plt.savefig(output_path, dpi=300, bbox_inches='tight')
                plt.close()
            else:
                # Single optimal strategy case
                labels = ['Optimal Strategy']
                success_rates = [withdrawal_result.success_rate]
                avg_withdrawals = [withdrawal_result.optimal_annual_withdrawal]

                fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(12, 6))

                # Success rate bar
                bars1 = ax1.bar(labels, success_rates, color='#2ca02c', alpha=0.7)
                for bar, rate in zip(bars1, success_rates):
                    height = bar.get_height()
                    ax1.text(bar.get_x() + bar.get_width()/2., height + 0.01,
                            f'{rate:.1%}', ha='center', va='bottom')
                ax1.set_xlabel('Strategy')
                ax1.set_ylabel('Success Rate (%)')
                ax1.set_title('Optimal Withdrawal Success Rate')
                ax1.set_ylim(0, 1)
                ax1.grid(True, alpha=0.3, axis='y')

                # Average withdrawal bar
                bars2 = ax2.bar(labels, avg_withdrawals, color='#d62728', alpha=0.7)
                for bar, amount in zip(bars2, avg_withdrawals):
                    height = bar.get_height()
                    ax2.text(bar.get_x() + bar.get_width()/2., height + 1000,
                            f'${amount/1000:.0f}K', ha='center', va='bottom')
                ax2.set_xlabel('Strategy')
                ax2.set_ylabel('Average Annual Withdrawal ($)')
                ax2.set_title('Optimal Annual Withdrawal')
                ax2.grid(True, alpha=0.3, axis='y')

                plt.tight_layout()
                plt.savefig(output_path, dpi=300, bbox_inches='tight')
                plt.close()

            self.logger.log(LogLevel.INFO, f"Withdrawal strategy chart saved to {output_path}")
            return output_path

        except Exception as e:
            raise AnalysisError(f"Failed to create withdrawal strategy chart: {e}")

    def create_asset_allocation_chart(
        self,
        portfolio: Portfolio,
        output_path: Path,
        title: str = "Asset Allocation"
    ) -> Path:
        """Create pie chart showing current asset allocation."""
        try:
            allocation = portfolio.get_current_allocation()
            assets = list(allocation.keys())
            percentages = list(allocation.values())

            fig, ax = plt.subplots(figsize=(10, 8))

            colors = plt.cm.Set3(np.linspace(0, 1, len(assets)))
            wedges, texts, autotexts = ax.pie(percentages, labels=assets, autopct='%1.1f%%',
                                             colors=colors, startangle=90)

            ax.set_title(title)

            plt.tight_layout()
            plt.savefig(output_path, dpi=300, bbox_inches='tight')
            plt.close()

            self.logger.log(LogLevel.INFO, f"Asset allocation chart saved to {output_path}")
            return output_path

        except Exception as e:
            raise AnalysisError(f"Failed to create asset allocation chart: {e}")


class DataExporter:
    """Exports analysis data in various formats."""

    def __init__(self, logger: Optional[RetirementPlannerLogger] = None):
        self.logger = logger or RetirementPlannerLogger()

    def export_simulation_data(
        self,
        simulation_result: SimulationResult,
        output_path: Path,
        format: str = "csv"
    ) -> Path:
        """Export simulation data to CSV or JSON."""
        try:
            if format.lower() == "csv":
                return self._export_simulation_csv(simulation_result, output_path)
            elif format.lower() == "json":
                return self._export_simulation_json(simulation_result, output_path)
            else:
                raise AnalysisError(f"Unsupported export format: {format}")

        except Exception as e:
            raise AnalysisError(f"Failed to export simulation data: {e}")

    def _export_simulation_csv(self, simulation_result: SimulationResult, output_path: Path) -> Path:
        """Export simulation data to CSV format."""
        data = []
        for i, scenario in enumerate(simulation_result.scenarios):
            for year, value in enumerate(scenario.portfolio_values):
                data.append({
                    'scenario': i,
                    'year': year,
                    'portfolio_value': value,
                    'success': scenario.success
                })

        df = pd.DataFrame(data)
        df.to_csv(output_path, index=False)

        self.logger.log(LogLevel.INFO, f"Simulation data exported to CSV: {output_path}")
        return output_path

    def _export_simulation_json(self, simulation_result: SimulationResult, output_path: Path) -> Path:
        """Export simulation data to JSON format."""
        data = {
            'metadata': {
                'num_scenarios': simulation_result.num_scenarios,
                'time_horizon': simulation_result.time_horizon,
                'success_rate': simulation_result.success_rate,
                'exported_at': datetime.now().isoformat()
            },
            'scenarios': [
                {
                    'scenario_id': i,
                    'portfolio_values': scenario.portfolio_values,
                    'success': scenario.success,
                    'final_value': scenario.portfolio_values[-1]
                }
                for i, scenario in enumerate(simulation_result.scenarios)
            ]
        }

        with open(output_path, 'w') as f:
            json.dump(data, f, indent=2)

        self.logger.log(LogLevel.INFO, f"Simulation data exported to JSON: {output_path}")
        return output_path

    def export_analysis_summary(
        self,
        retirement_analysis: RetirementAnalysis,
        output_path: Path,
        format: str = "json"
    ) -> Path:
        """Export analysis summary to JSON."""
        try:
            summary = {
                'metadata': {
                    'analysis_date': datetime.now().isoformat(),
                    'person_name': retirement_analysis.person.name,
                    'total_goals': len(retirement_analysis.goal_statuses)
                },
                'goals': [
                    {
                        'name': goal_status.goal_name,
                        'success_rate': goal_status.success_rate,
                        'achieved': goal_status.achieved,
                        'average_shortfall': goal_status.average_shortfall,
                        'worst_case_shortfall': goal_status.worst_case_shortfall
                    }
                    for goal_status in retirement_analysis.goal_statuses
                ],
                'overall_success_rate': retirement_analysis.overall_success_rate,
                'recommendations': retirement_analysis.recommendations
            }

            with open(output_path, 'w') as f:
                json.dump(summary, f, indent=2)

            self.logger.log(LogLevel.INFO, f"Analysis summary exported to JSON: {output_path}")
            return output_path

        except Exception as e:
            raise AnalysisError(f"Failed to export analysis summary: {e}")


class ReportGenerator:
    """Main report generator for retirement analysis."""

    def __init__(self, config: Optional[ReportConfig] = None, logger: Optional[RetirementPlannerLogger] = None):
        self.config = config or ReportConfig()
        self.logger = logger or RetirementPlannerLogger()
        self.chart_creator = ChartCreator(logger)
        self.data_exporter = DataExporter(logger)

    def generate_comprehensive_report(
        self,
        retirement_analysis: RetirementAnalysis,
        simulation_result: SimulationResult,
        withdrawal_result: Optional[WithdrawalOptimizationResult] = None,
        output_dir: Path = Path("reports")
    ) -> Dict[str, Path]:
        """Generate a comprehensive retirement analysis report."""
        try:
            output_dir.mkdir(exist_ok=True)
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

            report_files = {}

            # Generate text report
            text_report_path = output_dir / f"retirement_analysis_{timestamp}.txt"
            report_files['text_report'] = self._generate_text_report(
                retirement_analysis, simulation_result, withdrawal_result, text_report_path
            )

            # Generate charts
            if self.config.include_charts:
                charts_dir = output_dir / "charts"
                charts_dir.mkdir(exist_ok=True)

                # Portfolio evolution chart
                portfolio_chart_path = charts_dir / f"portfolio_evolution_{timestamp}.{self.config.chart_format}"
                report_files['portfolio_chart'] = self.chart_creator.create_portfolio_evolution_chart(
                    simulation_result, portfolio_chart_path
                )

                # Simulation paths chart
                simulation_paths_chart_path = charts_dir / f"simulation_paths_{timestamp}.{self.config.chart_format}"
                report_files['simulation_paths_chart'] = self.chart_creator.create_simulation_paths_chart(
                    simulation_result, simulation_paths_chart_path
                )

                # Success rate chart
                success_chart_path = charts_dir / f"success_rates_{timestamp}.{self.config.chart_format}"
                report_files['success_chart'] = self.chart_creator.create_success_rate_chart(
                    retirement_analysis, success_chart_path
                )

                # Withdrawal strategy chart (if available)
                if withdrawal_result:
                    withdrawal_chart_path = charts_dir / f"withdrawal_strategies_{timestamp}.{self.config.chart_format}"
                    report_files['withdrawal_chart'] = self.chart_creator.create_withdrawal_strategy_chart(
                        withdrawal_result, withdrawal_chart_path
                    )

            # Export data
            if self.config.include_raw_data:
                data_dir = output_dir / "data"
                data_dir.mkdir(exist_ok=True)

                # Simulation data
                sim_data_path = data_dir / f"simulation_data_{timestamp}.csv"
                report_files['simulation_data'] = self.data_exporter.export_simulation_data(
                    simulation_result, sim_data_path, "csv"
                )

                # Analysis summary
                summary_path = data_dir / f"analysis_summary_{timestamp}.json"
                report_files['analysis_summary'] = self.data_exporter.export_analysis_summary(
                    retirement_analysis, summary_path
                )

            self.logger.log(LogLevel.SUCCESS, f"Comprehensive report generated in {output_dir}")
            return report_files

        except Exception as e:
            raise AnalysisError(f"Failed to generate comprehensive report: {e}")

    def _generate_text_report(
        self,
        retirement_analysis: RetirementAnalysis,
        simulation_result: SimulationResult,
        withdrawal_result: Optional[WithdrawalOptimizationResult],
        output_path: Path
    ) -> Path:
        """Generate a comprehensive text report."""
        try:
            with open(output_path, 'w') as f:
                f.write("=" * 80 + "\n")
                f.write("RETIREMENT ANALYSIS REPORT\n")
                f.write("=" * 80 + "\n")
                f.write(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")

                # Person information
                f.write("PERSONAL INFORMATION\n")
                f.write("-" * 40 + "\n")
                f.write(f"Name: {retirement_analysis.person.name}\n")
                f.write(f"Current Age: {retirement_analysis.person.age}\n")
                f.write(f"Retirement Age: {retirement_analysis.person.retirement_age}\n")
                f.write(f"Life Expectancy: {retirement_analysis.person.life_expectancy}\n")
                f.write(f"Current Portfolio Value: ${retirement_analysis.portfolio.total_value:,.0f}\n")
                f.write(f"Risk Tolerance: {retirement_analysis.person.risk_tolerance}\n\n")

                # Simulation results
                f.write("SIMULATION RESULTS\n")
                f.write("-" * 40 + "\n")
                f.write(f"Number of Scenarios: {len(simulation_result.scenarios):,}\n")
                f.write(f"Time Horizon: {simulation_result.time_horizon} years\n")
                f.write(f"Overall Success Rate: {simulation_result.success_rate:.1%}\n")
                f.write(f"Average Final Portfolio Value: ${simulation_result.average_portfolio_value:,.0f}\n")
                f.write(f"Median Final Portfolio Value: ${simulation_result.median_portfolio_value:,.0f}\n")
                f.write(f"Best Case Final Value: ${simulation_result.best_case_portfolio_value:,.0f}\n")
                f.write(f"Worst Case Final Value: ${simulation_result.worst_case_portfolio_value:,.0f}\n")
                if simulation_result.average_years_to_failure:
                    f.write(f"Average Years to Failure: {simulation_result.average_years_to_failure:.1f}\n")
                f.write("\n")

                # Goal analysis
                f.write("GOAL ANALYSIS\n")
                f.write("-" * 40 + "\n")
                for goal_status in retirement_analysis.goal_statuses:
                    f.write(f"Goal: {goal_status.goal_name}\n")
                    f.write(f"  Success Rate: {goal_status.success_rate:.1%}\n")
                    f.write(f"  Achieved: {'Yes' if goal_status.achieved else 'No'}\n")
                    f.write(f"  Average Shortfall: ${goal_status.average_shortfall:,.0f}\n")
                    f.write(f"  Worst Case Shortfall: ${goal_status.worst_case_shortfall:,.0f}\n")
                    if goal_status.years_to_achievement:
                        f.write(f"  Years to Achievement: {goal_status.years_to_achievement:.1f}\n")
                    f.write("\n")

                # Withdrawal strategy results
                if withdrawal_result:
                    f.write("WITHDRAWAL STRATEGY ANALYSIS\n")
                    f.write("-" * 40 + "\n")
                    f.write(f"Optimal Withdrawal Rate: {withdrawal_result.optimal_withdrawal_rate:.1%}\n")
                    f.write(f"Optimal Annual Withdrawal: ${withdrawal_result.optimal_annual_withdrawal:,.0f}\n")
                    f.write(f"Success Rate: {withdrawal_result.success_rate:.1%}\n")
                    f.write(f"Average Portfolio Value: ${withdrawal_result.average_portfolio_value:,.0f}\n")
                    f.write(f"Worst Case Portfolio Value: ${withdrawal_result.worst_case_portfolio_value:,.0f}\n\n")

                # Recommendations
                f.write("RECOMMENDATIONS\n")
                f.write("-" * 40 + "\n")
                for i, recommendation in enumerate(retirement_analysis.recommendations, 1):
                    f.write(f"{i}. {recommendation}\n")
                f.write("\n")

                f.write("=" * 80 + "\n")
                f.write("End of Report\n")
                f.write("=" * 80 + "\n")

            self.logger.log(LogLevel.INFO, f"Text report generated: {output_path}")
            return output_path

        except Exception as e:
            raise AnalysisError(f"Failed to generate text report: {e}")