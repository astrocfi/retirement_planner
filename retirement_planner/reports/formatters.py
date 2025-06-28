"""
Output formatters for retirement analysis reports.

This module provides different formatting options for reports including
text, HTML, and JSON formats.
"""

import json
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Any, Optional
from abc import ABC, abstractmethod

from retirement_planner.core.exceptions import AnalysisError
from retirement_planner.core.logging import RetirementPlannerLogger
from retirement_planner.analysis.retirement import RetirementAnalysis
from retirement_planner.analysis.withdrawal import WithdrawalOptimizationResult
from retirement_planner.simulation.engine import SimulationResult


class BaseFormatter(ABC):
    """Abstract base class for report formatters."""

    def __init__(self, logger: Optional[RetirementPlannerLogger] = None):
        self.logger = logger or RetirementPlannerLogger()

    @abstractmethod
    def format_report(
        self,
        retirement_analysis: RetirementAnalysis,
        simulation_result: SimulationResult,
        withdrawal_result: Optional[WithdrawalOptimizationResult] = None
    ) -> str:
        """Format the report content."""
        pass

    @abstractmethod
    def save_report(
        self,
        content: str,
        output_path: Path
    ) -> Path:
        """Save the formatted report to file."""
        pass


class TextFormatter(BaseFormatter):
    """Text-based report formatter."""

    def format_report(
        self,
        retirement_analysis: RetirementAnalysis,
        simulation_result: SimulationResult,
        withdrawal_result: Optional[WithdrawalOptimizationResult] = None
    ) -> str:
        """Format report as plain text."""
        try:
            lines = []

            # Header
            lines.append("=" * 80)
            lines.append("RETIREMENT ANALYSIS REPORT")
            lines.append("=" * 80)
            lines.append(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
            lines.append("")

            # Person information
            lines.append("PERSONAL INFORMATION")
            lines.append("-" * 40)
            lines.append(f"Name: {retirement_analysis.person.name}")
            lines.append(f"Current Age: {retirement_analysis.person.age}")
            lines.append(f"Retirement Age: {retirement_analysis.person.retirement_age}")
            lines.append(f"Life Expectancy: {retirement_analysis.person.life_expectancy}")
            lines.append(f"Current Savings: ${retirement_analysis.person.current_savings:,.0f}")
            lines.append(f"Annual Contribution: ${retirement_analysis.person.annual_contribution:,.0f}")
            lines.append("")

            # Simulation results
            lines.append("SIMULATION RESULTS")
            lines.append("-" * 40)
            lines.append(f"Number of Scenarios: {simulation_result.num_scenarios:,}")
            lines.append(f"Time Horizon: {simulation_result.time_horizon} years")
            lines.append(f"Overall Success Rate: {simulation_result.success_rate:.1f}%")
            lines.append(f"Average Final Portfolio Value: ${simulation_result.avg_final_value:,.0f}")
            lines.append(f"Median Final Portfolio Value: ${simulation_result.median_final_value:,.0f}")
            lines.append("")

            # Goal analysis
            lines.append("GOAL ANALYSIS")
            lines.append("-" * 40)
            for goal in retirement_analysis.goals:
                lines.append(f"Goal: {goal.name}")
                lines.append(f"  Target Amount: ${goal.target_amount:,.0f}")
                lines.append(f"  Success Rate: {goal.success_rate:.1f}%")
                lines.append(f"  Priority: {goal.priority}")
                lines.append("")

            # Withdrawal strategy results
            if withdrawal_result:
                lines.append("WITHDRAWAL STRATEGY ANALYSIS")
                lines.append("-" * 40)
                lines.append(f"Best Strategy: {withdrawal_result.best_strategy.name}")
                lines.append(f"Best Success Rate: {withdrawal_result.best_strategy.success_rate:.1f}%")
                lines.append(f"Recommended Annual Withdrawal: ${withdrawal_result.best_strategy.avg_annual_withdrawal:,.0f}")
                lines.append("")

            # Recommendations
            lines.append("RECOMMENDATIONS")
            lines.append("-" * 40)
            for i, recommendation in enumerate(retirement_analysis.recommendations, 1):
                lines.append(f"{i}. {recommendation}")
            lines.append("")

            lines.append("=" * 80)
            lines.append("End of Report")
            lines.append("=" * 80)

            return "\n".join(lines)

        except Exception as e:
            raise AnalysisError(f"Failed to format text report: {e}")

    def save_report(self, content: str, output_path: Path) -> Path:
        """Save text report to file."""
        try:
            with open(output_path, 'w') as f:
                f.write(content)

            self.logger.log(f"Text report saved to {output_path}", level="info")
            return output_path

        except Exception as e:
            raise AnalysisError(f"Failed to save text report: {e}")


class HtmlFormatter(BaseFormatter):
    """HTML-based report formatter."""

    def format_report(
        self,
        retirement_analysis: RetirementAnalysis,
        simulation_result: SimulationResult,
        withdrawal_result: Optional[WithdrawalOptimizationResult] = None
    ) -> str:
        """Format report as HTML."""
        try:
            html = []

            # HTML header
            html.append("<!DOCTYPE html>")
            html.append("<html lang='en'>")
            html.append("<head>")
            html.append("    <meta charset='UTF-8'>")
            html.append("    <meta name='viewport' content='width=device-width, initial-scale=1.0'>")
            html.append("    <title>Retirement Analysis Report</title>")
            html.append("    <style>")
            html.append("        body { font-family: Arial, sans-serif; margin: 40px; line-height: 1.6; }")
            html.append("        .header { text-align: center; border-bottom: 2px solid #333; padding-bottom: 20px; }")
            html.append("        .section { margin: 30px 0; }")
            html.append("        .section h2 { color: #2c3e50; border-bottom: 1px solid #bdc3c7; padding-bottom: 10px; }")
            html.append("        .metric { background: #f8f9fa; padding: 15px; margin: 10px 0; border-radius: 5px; }")
            html.append("        .goal { background: #e8f4f8; padding: 10px; margin: 5px 0; border-left: 4px solid #3498db; }")
            html.append("        .recommendation { background: #fff3cd; padding: 10px; margin: 5px 0; border-left: 4px solid #ffc107; }")
            html.append("        .success { color: #28a745; font-weight: bold; }")
            html.append("        .warning { color: #ffc107; font-weight: bold; }")
            html.append("        .danger { color: #dc3545; font-weight: bold; }")
            html.append("    </style>")
            html.append("</head>")
            html.append("<body>")

            # Header
            html.append("    <div class='header'>")
            html.append("        <h1>Retirement Analysis Report</h1>")
            html.append(f"        <p>Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>")
            html.append("    </div>")

            # Person information
            html.append("    <div class='section'>")
            html.append("        <h2>Personal Information</h2>")
            html.append(f"        <div class='metric'><strong>Name:</strong> {retirement_analysis.person.name}</div>")
            html.append(f"        <div class='metric'><strong>Current Age:</strong> {retirement_analysis.person.age}</div>")
            html.append(f"        <div class='metric'><strong>Retirement Age:</strong> {retirement_analysis.person.retirement_age}</div>")
            html.append(f"        <div class='metric'><strong>Life Expectancy:</strong> {retirement_analysis.person.life_expectancy}</div>")
            html.append(f"        <div class='metric'><strong>Current Savings:</strong> ${retirement_analysis.person.current_savings:,.0f}</div>")
            html.append(f"        <div class='metric'><strong>Annual Contribution:</strong> ${retirement_analysis.person.annual_contribution:,.0f}</div>")
            html.append("    </div>")

            # Simulation results
            html.append("    <div class='section'>")
            html.append("        <h2>Simulation Results</h2>")
            html.append(f"        <div class='metric'><strong>Number of Scenarios:</strong> {simulation_result.num_scenarios:,}</div>")
            html.append(f"        <div class='metric'><strong>Time Horizon:</strong> {simulation_result.time_horizon} years</div>")
            html.append(f"        <div class='metric'><strong>Overall Success Rate:</strong> <span class='success'>{simulation_result.success_rate:.1f}%</span></div>")
            html.append(f"        <div class='metric'><strong>Average Final Portfolio Value:</strong> ${simulation_result.avg_final_value:,.0f}</div>")
            html.append(f"        <div class='metric'><strong>Median Final Portfolio Value:</strong> ${simulation_result.median_final_value:,.0f}</div>")
            html.append("    </div>")

            # Goal analysis
            html.append("    <div class='section'>")
            html.append("        <h2>Goal Analysis</h2>")
            for goal in retirement_analysis.goals:
                success_class = "success" if goal.success_rate >= 80 else "warning" if goal.success_rate >= 60 else "danger"
                html.append("        <div class='goal'>")
                html.append(f"            <h3>{goal.name}</h3>")
                html.append(f"            <p><strong>Target Amount:</strong> ${goal.target_amount:,.0f}</p>")
                html.append(f"            <p><strong>Success Rate:</strong> <span class='{success_class}'>{goal.success_rate:.1f}%</span></p>")
                html.append(f"            <p><strong>Priority:</strong> {goal.priority}</p>")
                html.append("        </div>")
            html.append("    </div>")

            # Withdrawal strategy results
            if withdrawal_result:
                html.append("    <div class='section'>")
                html.append("        <h2>Withdrawal Strategy Analysis</h2>")
                html.append(f"        <div class='metric'><strong>Best Strategy:</strong> {withdrawal_result.best_strategy.name}</div>")
                html.append(f"        <div class='metric'><strong>Best Success Rate:</strong> <span class='success'>{withdrawal_result.best_strategy.success_rate:.1f}%</span></div>")
                html.append(f"        <div class='metric'><strong>Recommended Annual Withdrawal:</strong> ${withdrawal_result.best_strategy.avg_annual_withdrawal:,.0f}</div>")
                html.append("    </div>")

            # Recommendations
            html.append("    <div class='section'>")
            html.append("        <h2>Recommendations</h2>")
            for i, recommendation in enumerate(retirement_analysis.recommendations, 1):
                html.append(f"        <div class='recommendation'>{i}. {recommendation}</div>")
            html.append("    </div>")

            html.append("</body>")
            html.append("</html>")

            return "\n".join(html)

        except Exception as e:
            raise AnalysisError(f"Failed to format HTML report: {e}")

    def save_report(self, content: str, output_path: Path) -> Path:
        """Save HTML report to file."""
        try:
            with open(output_path, 'w') as f:
                f.write(content)

            self.logger.log(f"HTML report saved to {output_path}", level="info")
            return output_path

        except Exception as e:
            raise AnalysisError(f"Failed to save HTML report: {e}")


class JsonFormatter(BaseFormatter):
    """JSON-based report formatter."""

    def format_report(
        self,
        retirement_analysis: RetirementAnalysis,
        simulation_result: SimulationResult,
        withdrawal_result: Optional[WithdrawalOptimizationResult] = None
    ) -> str:
        """Format report as JSON."""
        try:
            data = {
                "metadata": {
                    "generated_at": datetime.now().isoformat(),
                    "report_type": "retirement_analysis"
                },
                "person": {
                    "name": retirement_analysis.person.name,
                    "age": retirement_analysis.person.age,
                    "retirement_age": retirement_analysis.person.retirement_age,
                    "life_expectancy": retirement_analysis.person.life_expectancy,
                    "current_savings": retirement_analysis.person.current_savings,
                    "annual_contribution": retirement_analysis.person.annual_contribution
                },
                "simulation_results": {
                    "num_scenarios": simulation_result.num_scenarios,
                    "time_horizon": simulation_result.time_horizon,
                    "success_rate": simulation_result.success_rate,
                    "avg_final_value": simulation_result.avg_final_value,
                    "median_final_value": simulation_result.median_final_value
                },
                "goals": [
                    {
                        "name": goal.name,
                        "target_amount": goal.target_amount,
                        "success_rate": goal.success_rate,
                        "priority": goal.priority
                    }
                    for goal in retirement_analysis.goals
                ],
                "recommendations": retirement_analysis.recommendations
            }

            if withdrawal_result:
                data["withdrawal_analysis"] = {
                    "best_strategy": {
                        "name": withdrawal_result.best_strategy.name,
                        "success_rate": withdrawal_result.best_strategy.success_rate,
                        "avg_annual_withdrawal": withdrawal_result.best_strategy.avg_annual_withdrawal
                    }
                }

            return json.dumps(data, indent=2)

        except Exception as e:
            raise AnalysisError(f"Failed to format JSON report: {e}")

    def save_report(self, content: str, output_path: Path) -> Path:
        """Save JSON report to file."""
        try:
            with open(output_path, 'w') as f:
                f.write(content)

            self.logger.log(f"JSON report saved to {output_path}", level="info")
            return output_path

        except Exception as e:
            raise AnalysisError(f"Failed to save JSON report: {e}")