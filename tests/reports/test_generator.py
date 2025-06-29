"""
Tests for report generation functionality.
"""

import pytest
import tempfile
from pathlib import Path
from unittest.mock import Mock, patch
import numpy as np
import pandas as pd

from retirement_planner.reports.generator import (
    ReportGenerator, ReportConfig, ChartCreator, DataExporter
)
from retirement_planner.core.exceptions import AnalysisError
from retirement_planner.core.logging import RetirementPlannerLogger


class TestReportConfig:
    """Test ReportConfig dataclass."""

    def test_default_config(self):
        """Test default configuration values."""
        config = ReportConfig()
        assert config.output_format == "text"
        assert config.include_charts is True
        assert config.chart_format == "png"
        assert config.include_raw_data is False
        assert config.custom_styles is None

    def test_custom_config(self):
        """Test custom configuration values."""
        custom_styles = {"font_size": 12, "color": "blue"}
        config = ReportConfig(
            output_format="html",
            include_charts=False,
            chart_format="pdf",
            include_raw_data=True,
            custom_styles=custom_styles
        )
        assert config.output_format == "html"
        assert config.include_charts is False
        assert config.chart_format == "pdf"
        assert config.include_raw_data is True
        assert config.custom_styles == custom_styles


class TestChartCreator:
    """Test ChartCreator functionality."""

    def setup_method(self):
        """Setup test fixtures."""
        self.logger = Mock(spec=RetirementPlannerLogger)
        self.chart_creator = ChartCreator(logger=self.logger)

    @patch('matplotlib.pyplot.savefig')
    @patch('matplotlib.pyplot.close')
    def test_create_portfolio_evolution_chart(self, mock_close, mock_savefig):
        """Test portfolio evolution chart creation."""
        # Create mock simulation result
        mock_scenario = Mock()
        mock_scenario.portfolio_values = [100000, 105000, 110000, 108000, 115000]
        mock_scenario.success = True

        mock_simulation_result = Mock()
        mock_simulation_result.time_horizon = 4
        mock_simulation_result.scenarios = [mock_scenario] * 10  # 10 scenarios
        mock_simulation_result.success_rate = 0.8
        mock_simulation_result.num_scenarios = 10

        with tempfile.TemporaryDirectory() as temp_dir:
            output_path = Path(temp_dir) / "portfolio_chart.png"

            result_path = self.chart_creator.create_portfolio_evolution_chart(
                simulation_result=mock_simulation_result,
                output_path=output_path
            )

            assert result_path == output_path
            mock_savefig.assert_called_once()
            mock_close.assert_called_once()
            self.logger.log.assert_called()

    @patch('matplotlib.pyplot.savefig')
    @patch('matplotlib.pyplot.close')
    def test_create_simulation_paths_chart(self, mock_close, mock_savefig):
        """Test simulation paths chart creation."""
        # Create mock simulation result with mixed success/failure scenarios
        mock_success_scenario = Mock()
        mock_success_scenario.portfolio_values = [100000, 105000, 110000, 108000, 115000]
        mock_success_scenario.success = True

        mock_failure_scenario = Mock()
        mock_failure_scenario.portfolio_values = [100000, 95000, 90000, 85000, 80000]
        mock_failure_scenario.success = False

        mock_simulation_result = Mock()
        mock_simulation_result.time_horizon = 4
        mock_simulation_result.success_rate = 0.6
        mock_simulation_result.scenarios = [mock_success_scenario] * 6 + [mock_failure_scenario] * 4  # 10 scenarios

        with tempfile.TemporaryDirectory() as temp_dir:
            output_path = Path(temp_dir) / "simulation_paths_chart.png"

            result_path = self.chart_creator.create_simulation_paths_chart(
                simulation_result=mock_simulation_result,
                output_path=output_path
            )

            assert result_path == output_path
            mock_savefig.assert_called_once()
            mock_close.assert_called_once()
            self.logger.log.assert_called()

    @patch('matplotlib.pyplot.savefig')
    @patch('matplotlib.pyplot.close')
    def test_create_simulation_paths_chart_with_many_scenarios(self, mock_close, mock_savefig):
        """Test simulation paths chart with many scenarios (should sample)."""
        # Create mock simulation result with many scenarios
        mock_scenario = Mock()
        mock_scenario.portfolio_values = [100000, 105000, 110000, 108000, 115000]
        mock_scenario.success = True

        mock_simulation_result = Mock()
        mock_simulation_result.time_horizon = 4
        mock_simulation_result.success_rate = 0.8
        mock_simulation_result.scenarios = [mock_scenario] * 200  # 200 scenarios

        with tempfile.TemporaryDirectory() as temp_dir:
            output_path = Path(temp_dir) / "simulation_paths_chart.png"

            result_path = self.chart_creator.create_simulation_paths_chart(
                simulation_result=mock_simulation_result,
                output_path=output_path,
                max_paths=50  # Limit to 50 paths
            )

            assert result_path == output_path
            mock_savefig.assert_called_once()
            mock_close.assert_called_once()
            self.logger.log.assert_called()

    @patch('matplotlib.pyplot.savefig')
    @patch('matplotlib.pyplot.close')
    def test_create_withdrawal_strategy_chart(self, mock_close, mock_savefig):
        """Test withdrawal strategy chart creation."""
        # Create mock withdrawal result
        mock_strategy = Mock()
        mock_strategy.name = "Fixed Withdrawal"
        mock_strategy.success_rate = 90.0
        mock_strategy.avg_annual_withdrawal = 50000

        mock_withdrawal_result = Mock()
        mock_withdrawal_result.strategies = [mock_strategy]
        mock_withdrawal_result.optimal_withdrawal_rate = 0.045
        mock_withdrawal_result.optimal_annual_withdrawal = 45000
        mock_withdrawal_result.success_rate = 0.85
        mock_withdrawal_result.average_portfolio_value = 1200000
        mock_withdrawal_result.worst_case_portfolio_value = 800000

        with tempfile.TemporaryDirectory() as temp_dir:
            output_path = Path(temp_dir) / "withdrawal_chart.png"

            result_path = self.chart_creator.create_withdrawal_strategy_chart(
                withdrawal_result=mock_withdrawal_result,
                output_path=output_path
            )

            assert result_path == output_path
            mock_savefig.assert_called_once()
            mock_close.assert_called_once()
            self.logger.log.assert_called()

    @patch('matplotlib.pyplot.savefig')
    @patch('matplotlib.pyplot.close')
    def test_create_asset_allocation_chart(self, mock_close, mock_savefig):
        """Test asset allocation chart creation."""
        # Create mock portfolio
        mock_portfolio = Mock()
        mock_portfolio.get_current_allocation.return_value = {
            "Stocks": 60.0,
            "Bonds": 30.0,
            "Cash": 10.0
        }

        with tempfile.TemporaryDirectory() as temp_dir:
            output_path = Path(temp_dir) / "allocation_chart.png"

            result_path = self.chart_creator.create_asset_allocation_chart(
                portfolio=mock_portfolio,
                output_path=output_path
            )

            assert result_path == output_path
            mock_savefig.assert_called_once()
            mock_close.assert_called_once()
            self.logger.log.assert_called()

    def test_chart_creation_error_handling(self):
        """Test error handling in chart creation."""
        with tempfile.TemporaryDirectory() as temp_dir:
            output_path = Path(temp_dir) / "error_chart.png"

            # Test with invalid simulation result
            with pytest.raises(AnalysisError, match="Failed to create portfolio evolution chart"):
                self.chart_creator.create_portfolio_evolution_chart(
                    simulation_result=None,
                    output_path=output_path
                )


class TestDataExporter:
    """Test DataExporter functionality."""

    def setup_method(self):
        """Setup test fixtures."""
        self.logger = Mock(spec=RetirementPlannerLogger)
        self.data_exporter = DataExporter(logger=self.logger)

    def test_export_simulation_data_csv(self):
        """Test CSV export of simulation data."""
        # Create mock simulation result with proper numeric attributes
        mock_scenario = Mock()
        mock_scenario.portfolio_values = [100000, 105000, 110000]
        mock_scenario.success = True
        mock_scenario.withdrawals = [5000, 5000]  # Add withdrawals
        mock_scenario.contributions = [0, 0]      # Add contributions

        # Create proper tax result objects with numeric attributes
        mock_tax_result1 = Mock()
        mock_tax_result1.federal_income_tax = 1000.0
        mock_tax_result1.federal_capital_gains_tax = 500.0
        mock_tax_result1.state_income_tax = 200.0
        mock_tax_result1.state_capital_gains_tax = 100.0
        mock_tax_result1.total_tax = 1800.0
        mock_tax_result1.effective_tax_rate = 0.15

        mock_tax_result2 = Mock()
        mock_tax_result2.federal_income_tax = 1100.0
        mock_tax_result2.federal_capital_gains_tax = 550.0
        mock_tax_result2.state_income_tax = 220.0
        mock_tax_result2.state_capital_gains_tax = 110.0
        mock_tax_result2.total_tax = 1980.0
        mock_tax_result2.effective_tax_rate = 0.16

        # Add tax-related attributes that the real code expects
        mock_scenario.dividend_income = [100, 100]
        mock_scenario.annual_taxes = [mock_tax_result1, mock_tax_result2]

        mock_simulation_result = Mock()
        mock_simulation_result.scenarios = [mock_scenario] * 3  # 3 scenarios

        with tempfile.TemporaryDirectory() as temp_dir:
            output_path = Path(temp_dir) / "simulation_data.csv"

            result_path = self.data_exporter.export_simulation_data(
                simulation_result=mock_simulation_result,
                output_path=output_path,
                format="csv"
            )

            assert result_path == output_path
            assert output_path.exists()

            # Verify CSV content
            df = pd.read_csv(output_path)
            assert len(df) == 6  # 3 scenarios * 2 years (portfolio_values has 3 values = 2 years)
            assert "scenario" in df.columns
            assert "year" in df.columns
            assert "starting_value" in df.columns
            assert "income" in df.columns
            assert "expenses" in df.columns
            assert "final_value" in df.columns
            assert "success" in df.columns

    def test_export_simulation_data_json(self):
        """Test JSON export of simulation data."""
        # Create mock simulation result
        mock_scenario = Mock()
        mock_scenario.portfolio_values = [100000, 105000, 110000]
        mock_scenario.success = True

        mock_simulation_result = Mock()
        mock_simulation_result.num_scenarios = 2
        mock_simulation_result.time_horizon = 2
        mock_simulation_result.success_rate = 85.0
        mock_simulation_result.scenarios = [mock_scenario] * 2

        with tempfile.TemporaryDirectory() as temp_dir:
            output_path = Path(temp_dir) / "simulation_data.json"

            result_path = self.data_exporter.export_simulation_data(
                simulation_result=mock_simulation_result,
                output_path=output_path,
                format="json"
            )

            assert result_path == output_path
            assert output_path.exists()

            # Verify JSON content
            import json
            with open(output_path, 'r') as f:
                data = json.load(f)

            assert "metadata" in data
            assert "scenarios" in data
            assert data["metadata"]["num_scenarios"] == 2
            assert data["metadata"]["time_horizon"] == 2
            assert data["metadata"]["success_rate"] == 85.0

    def test_export_analysis_summary(self):
        """Test analysis summary export."""
        # Create mock retirement analysis
        mock_goal_status = Mock()
        mock_goal_status.goal_name = "Retirement Goal"
        mock_goal_status.success_rate = 0.855
        mock_goal_status.achieved = True
        mock_goal_status.average_shortfall = 0
        mock_goal_status.worst_case_shortfall = 0

        mock_person = Mock()
        mock_person.name = "John Doe"

        mock_retirement_analysis = Mock()
        mock_retirement_analysis.person = mock_person
        mock_retirement_analysis.goal_statuses = [mock_goal_status]
        mock_retirement_analysis.overall_success_rate = 0.855
        mock_retirement_analysis.recommendations = ["Save more", "Invest wisely"]

        with tempfile.TemporaryDirectory() as temp_dir:
            output_path = Path(temp_dir) / "analysis_summary.json"

            result_path = self.data_exporter.export_analysis_summary(
                retirement_analysis=mock_retirement_analysis,
                output_path=output_path
            )

            assert result_path == output_path
            assert output_path.exists()

            # Verify JSON content
            import json
            with open(output_path, 'r') as f:
                data = json.load(f)

            assert "metadata" in data
            assert "person_name" in data["metadata"]
            assert "goals" in data
            assert "recommendations" in data
            assert data["metadata"]["person_name"] == "John Doe"
            assert len(data["goals"]) == 1
            assert len(data["recommendations"]) == 2

    def test_unsupported_export_format(self):
        """Test error handling for unsupported export format."""
        mock_simulation_result = Mock()

        with tempfile.TemporaryDirectory() as temp_dir:
            output_path = Path(temp_dir) / "data.txt"

            with pytest.raises(AnalysisError, match="Unsupported export format"):
                self.data_exporter.export_simulation_data(
                    simulation_result=mock_simulation_result,
                    output_path=output_path,
                    format="txt"
                )


class TestReportGenerator:
    """Test ReportGenerator functionality."""

    def setup_method(self):
        """Setup test fixtures."""
        self.logger = Mock(spec=RetirementPlannerLogger)
        self.config = ReportConfig()
        self.report_generator = ReportGenerator(config=self.config, logger=self.logger)

    @patch('retirement_planner.reports.generator.ChartCreator.create_portfolio_evolution_chart')
    @patch('retirement_planner.reports.generator.DataExporter.export_simulation_data')
    @patch('retirement_planner.reports.generator.DataExporter.export_analysis_summary')
    def test_generate_comprehensive_report(
        self, mock_export_summary, mock_export_data, mock_portfolio_chart
    ):
        """Test comprehensive report generation."""
        # Create mock objects with proper attributes for formatting
        mock_person = Mock()
        mock_person.name = "John Doe"
        mock_person.age = 45
        mock_person.retirement_age = 65
        mock_person.life_expectancy = 85
        mock_person.current_savings = 500000
        mock_person.annual_contribution = 20000

        mock_goal_status = Mock()
        mock_goal_status.goal_name = "Retirement Goal"
        mock_goal_status.success_rate = 0.855
        mock_goal_status.achieved = True
        mock_goal_status.average_shortfall = 0
        mock_goal_status.worst_case_shortfall = 0
        mock_goal_status.years_to_achievement = 5.0

        mock_portfolio = Mock()
        mock_portfolio.total_value = 500000

        mock_retirement_analysis = Mock()
        mock_retirement_analysis.person = mock_person
        mock_retirement_analysis.portfolio = mock_portfolio
        mock_retirement_analysis.goal_statuses = [mock_goal_status]
        mock_retirement_analysis.recommendations = ["Save more", "Invest wisely"]

        # Create mock scenarios for simulation result
        mock_scenario = Mock()
        mock_scenario.portfolio_values = [100000 + 1000 * i for i in range(21)]  # 21 years for time_horizon=20
        mock_scenario.success = True
        mock_scenario.withdrawals = [0] * 20  # Add withdrawals
        mock_scenario.contributions = [0] * 20  # Add contributions

        # Add allocation percentages and returns for debug export
        mock_scenario.allocation_percentages = [{"stock": 0.6, "bond": 0.4}] * 20
        mock_scenario.returns = [0.05] * 20

        # Add tax-related attributes
        mock_scenario.dividend_income = [100] * 20
        mock_tax_results = []
        for i in range(20):
            mock_tax_result = Mock()
            mock_tax_result.federal_income_tax = 1000.0 + i * 10
            mock_tax_result.federal_capital_gains_tax = 500.0 + i * 5
            mock_tax_result.state_income_tax = 200.0 + i * 2
            mock_tax_result.state_capital_gains_tax = 100.0 + i * 1
            mock_tax_result.total_tax = 1800.0 + i * 18
            mock_tax_result.effective_tax_rate = 0.15 + i * 0.001
            mock_tax_results.append(mock_tax_result)
        mock_scenario.annual_taxes = mock_tax_results

        mock_simulation_result = Mock()
        mock_simulation_result.scenarios = [mock_scenario] * 10  # 10 scenarios
        mock_simulation_result.time_horizon = 20
        mock_simulation_result.success_rate = 0.855
        mock_simulation_result.average_portfolio_value = 1200000
        mock_simulation_result.median_portfolio_value = 1150000
        mock_simulation_result.best_case_portfolio_value = 1500000
        mock_simulation_result.worst_case_portfolio_value = 800000
        mock_simulation_result.average_years_to_failure = 5.5

        # Create mock withdrawal strategy
        mock_strategy = Mock()
        mock_strategy.name = "Fixed Withdrawal"
        mock_strategy.success_rate = 90.0
        mock_strategy.avg_annual_withdrawal = 50000

        mock_withdrawal_result = Mock()
        mock_withdrawal_result.best_strategy = mock_strategy
        mock_withdrawal_result.strategies = [mock_strategy]
        mock_withdrawal_result.optimal_withdrawal_rate = 0.045
        mock_withdrawal_result.optimal_annual_withdrawal = 45000
        mock_withdrawal_result.success_rate = 0.85
        mock_withdrawal_result.average_portfolio_value = 1200000
        mock_withdrawal_result.worst_case_portfolio_value = 800000

        # Setup mock return values
        mock_portfolio_chart.return_value = Path("portfolio_chart.png")
        mock_export_data.return_value = Path("simulation_data.csv")
        mock_export_summary.return_value = Path("analysis_summary.json")

        config = ReportConfig(include_raw_data=True)
        report_generator = ReportGenerator(config=config, logger=self.logger)

        with tempfile.TemporaryDirectory() as temp_dir:
            output_dir = Path(temp_dir) / "reports"

            report_files = report_generator.generate_comprehensive_report(
                retirement_analysis=mock_retirement_analysis,
                simulation_result=mock_simulation_result,
                withdrawal_result=mock_withdrawal_result,
                output_dir=output_dir
            )

            # Verify report files were created
            assert "text_report" in report_files
            assert "portfolio_chart" in report_files
            assert "simulation_data" in report_files
            assert "analysis_summary" in report_files

            # Verify directories were created
            assert output_dir.exists()
            assert (output_dir / "charts").exists()
            assert (output_dir / "data").exists()

            # Verify mock calls
            mock_portfolio_chart.assert_called_once()
            mock_export_data.assert_called_once()
            mock_export_summary.assert_called_once()

    @patch('retirement_planner.reports.generator.DataExporter.export_analysis_summary')
    def test_generate_comprehensive_report_no_charts(self, mock_export_summary):
        """Test comprehensive report generation without charts."""
        # Create mock objects
        mock_retirement_analysis = Mock()
        mock_retirement_analysis.person.name = "Test Person"
        mock_retirement_analysis.portfolio.total_value = 1000000
        mock_retirement_analysis.overall_success_rate = 0.85
        mock_retirement_analysis.goal_statuses = []
        mock_retirement_analysis.recommendations = []

        mock_scenario = Mock()
        mock_scenario.portfolio_values = [100000, 105000, 110000]
        mock_scenario.success = True
        mock_scenario.withdrawals = [5000, 5000]
        mock_scenario.contributions = [0, 0]
        mock_scenario.dividend_income = [100, 100]

        # Create proper tax result objects
        mock_tax_result1 = Mock()
        mock_tax_result1.federal_income_tax = 1000.0
        mock_tax_result1.federal_capital_gains_tax = 500.0
        mock_tax_result1.state_income_tax = 200.0
        mock_tax_result1.state_capital_gains_tax = 100.0
        mock_tax_result1.total_tax = 1800.0
        mock_tax_result1.effective_tax_rate = 0.15

        mock_tax_result2 = Mock()
        mock_tax_result2.federal_income_tax = 1100.0
        mock_tax_result2.federal_capital_gains_tax = 550.0
        mock_tax_result2.state_income_tax = 220.0
        mock_tax_result2.state_capital_gains_tax = 110.0
        mock_tax_result2.total_tax = 1980.0
        mock_tax_result2.effective_tax_rate = 0.16

        mock_scenario.annual_taxes = [mock_tax_result1, mock_tax_result2]

        # Add allocation percentages and returns for debug export
        mock_scenario.allocation_percentages = [{"stock": 0.6, "bond": 0.4}, {"stock": 0.6, "bond": 0.4}]
        mock_scenario.returns = [0.05, 0.05]

        mock_simulation_result = Mock()
        mock_simulation_result.scenarios = [mock_scenario] * 3
        mock_simulation_result.time_horizon = 2
        mock_simulation_result.success_rate = 0.8
        mock_simulation_result.average_portfolio_value = 110000
        mock_simulation_result.median_portfolio_value = 110000
        mock_simulation_result.worst_case_portfolio_value = 100000
        mock_simulation_result.best_case_portfolio_value = 120000
        mock_simulation_result.average_years_to_failure = 5.5
        mock_simulation_result.num_scenarios = 3

        mock_withdrawal_result = Mock()
        mock_withdrawal_result.optimal_withdrawal_rate = 0.04
        mock_withdrawal_result.optimal_annual_withdrawal = 40000
        mock_withdrawal_result.success_rate = 0.85
        mock_withdrawal_result.average_portfolio_value = 110000
        mock_withdrawal_result.worst_case_portfolio_value = 100000

        # Configure mock to return a path
        mock_export_summary.return_value = Path("/tmp/test_summary.json")

        report_config = ReportConfig(include_charts=False, include_raw_data=True)
        report_generator = ReportGenerator(config=report_config, logger=self.logger)

        with tempfile.TemporaryDirectory() as temp_dir:
            report_files = report_generator.generate_comprehensive_report(
                retirement_analysis=mock_retirement_analysis,
                simulation_result=mock_simulation_result,
                withdrawal_result=mock_withdrawal_result,
                output_dir=Path(temp_dir)
            )

            # Verify report files were generated
            assert 'text_report' in report_files
            assert 'analysis_summary' in report_files
            assert 'simulation_data' in report_files

            # Verify text report exists
            text_report_path = report_files['text_report']
            assert text_report_path.exists()
            assert text_report_path.suffix == '.txt'

            # Verify content was written
            with open(text_report_path, 'r') as f:
                content = f.read()
                assert "Test Person" in content
                assert "85.0%" in content  # Success rate

    def test_generate_comprehensive_report_no_raw_data(self):
        """Test report generation without raw data export."""
        config = ReportConfig(include_raw_data=False)
        report_generator = ReportGenerator(config=config, logger=self.logger)

        # Create mock objects with proper attributes
        mock_person = Mock()
        mock_person.name = "John Doe"
        mock_person.age = 45
        mock_person.retirement_age = 65
        mock_person.life_expectancy = 85
        mock_person.current_savings = 500000
        mock_person.annual_contribution = 20000

        mock_portfolio = Mock()
        mock_portfolio.total_value = 500000

        mock_retirement_analysis = Mock()
        mock_retirement_analysis.person = mock_person
        mock_retirement_analysis.portfolio = mock_portfolio
        mock_retirement_analysis.goal_statuses = []
        mock_retirement_analysis.recommendations = []

        # Create mock scenarios for simulation result
        mock_scenario = Mock()
        mock_scenario.portfolio_values = [100000 + 1000 * i for i in range(21)]  # 21 years for time_horizon=20
        mock_scenario.success = True
        mock_scenario.withdrawals = [0] * 20  # Add withdrawals
        mock_scenario.contributions = [0] * 20  # Add contributions

        # Add allocation percentages and returns for debug export
        mock_scenario.allocation_percentages = [{"stock": 0.6, "bond": 0.4}] * 20
        mock_scenario.returns = [0.05] * 20

        mock_simulation_result = Mock()
        mock_simulation_result.scenarios = [mock_scenario] * 10  # 10 scenarios
        mock_simulation_result.time_horizon = 20
        mock_simulation_result.success_rate = 0.855
        mock_simulation_result.average_portfolio_value = 1200000
        mock_simulation_result.median_portfolio_value = 1150000
        mock_simulation_result.best_case_portfolio_value = 1500000
        mock_simulation_result.worst_case_portfolio_value = 800000
        mock_simulation_result.average_years_to_failure = 5.5

        with tempfile.TemporaryDirectory() as temp_dir:
            output_dir = Path(temp_dir) / "reports"

            report_files = report_generator.generate_comprehensive_report(
                retirement_analysis=mock_retirement_analysis,
                simulation_result=mock_simulation_result,
                output_dir=output_dir
            )

            # Should only have text report and charts
            assert "text_report" in report_files
            assert "simulation_data" not in report_files
            assert "analysis_summary" not in report_files

    def test_generate_text_report(self):
        """Test text report generation."""
        # Create mock objects with realistic data
        mock_person = Mock()
        mock_person.name = "John Doe"
        mock_person.age = 45
        mock_person.retirement_age = 65
        mock_person.life_expectancy = 85
        mock_person.current_savings = 500000
        mock_person.annual_contribution = 20000

        mock_goal_status = Mock()
        mock_goal_status.goal_name = "Retirement Goal"
        mock_goal_status.success_rate = 0.855
        mock_goal_status.achieved = True
        mock_goal_status.average_shortfall = 0
        mock_goal_status.worst_case_shortfall = 0
        mock_goal_status.years_to_achievement = 5.0

        mock_portfolio = Mock()
        mock_portfolio.total_value = 500000

        mock_retirement_analysis = Mock()
        mock_retirement_analysis.person = mock_person
        mock_retirement_analysis.portfolio = mock_portfolio
        mock_retirement_analysis.goal_statuses = [mock_goal_status]
        mock_retirement_analysis.recommendations = ["Save more", "Invest wisely"]

        # Create mock scenarios for simulation result
        mock_scenario = Mock()
        mock_scenario.portfolio_values = [100000 + 1000 * i for i in range(21)]  # 21 years for time_horizon=20
        mock_scenario.success = True
        mock_scenario.withdrawals = [0] * 20  # Add withdrawals
        mock_scenario.contributions = [0] * 20  # Add contributions

        mock_simulation_result = Mock()
        mock_simulation_result.scenarios = [mock_scenario] * 10  # 10 scenarios
        mock_simulation_result.time_horizon = 20
        mock_simulation_result.success_rate = 0.855
        mock_simulation_result.average_portfolio_value = 1200000
        mock_simulation_result.median_portfolio_value = 1150000
        mock_simulation_result.best_case_portfolio_value = 1500000
        mock_simulation_result.worst_case_portfolio_value = 800000
        mock_simulation_result.average_years_to_failure = 5.5

        with tempfile.TemporaryDirectory() as temp_dir:
            output_path = Path(temp_dir) / "report.txt"

            result_path = self.report_generator._generate_text_report(
                retirement_analysis=mock_retirement_analysis,
                simulation_result=mock_simulation_result,
                withdrawal_result=None,
                output_path=output_path
            )

            assert result_path == output_path
            assert output_path.exists()

            # Verify report content
            content = output_path.read_text()
            assert "RETIREMENT ANALYSIS REPORT" in content
            assert "John Doe" in content
            assert "45" in content
            assert "65" in content
            assert "$500,000" in content
            assert "85.5%" in content
            assert "Save more" in content
            assert "Invest wisely" in content

    def test_report_generation_error_handling(self):
        """Test error handling in report generation."""
        with tempfile.TemporaryDirectory() as temp_dir:
            output_dir = Path(temp_dir) / "reports"

            # Test with invalid data
            with pytest.raises(AnalysisError, match="Failed to generate comprehensive report"):
                self.report_generator.generate_comprehensive_report(
                    retirement_analysis=None,
                    simulation_result=None,
                    output_dir=output_dir
                )