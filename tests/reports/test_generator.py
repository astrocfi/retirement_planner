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
    def test_create_success_rate_chart(self, mock_close, mock_savefig):
        """Test success rate chart creation."""
        # Create mock retirement analysis
        mock_goal = Mock()
        mock_goal.name = "Retirement Goal"
        mock_goal.success_rate = 85.5

        mock_retirement_analysis = Mock()
        mock_retirement_analysis.goals = [mock_goal]

        with tempfile.TemporaryDirectory() as temp_dir:
            output_path = Path(temp_dir) / "success_chart.png"

            result_path = self.chart_creator.create_success_rate_chart(
                retirement_analysis=mock_retirement_analysis,
                output_path=output_path
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
        # Create mock simulation result
        mock_scenario = Mock()
        mock_scenario.portfolio_values = [100000, 105000, 110000]
        mock_scenario.success = True

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
            assert len(df) == 9  # 3 scenarios * 3 years
            assert "scenario" in df.columns
            assert "year" in df.columns
            assert "portfolio_value" in df.columns
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
        mock_goal = Mock()
        mock_goal.name = "Retirement Goal"
        mock_goal.success_rate = 85.5
        mock_goal.target_amount = 1000000
        mock_goal.priority = "high"

        mock_person = Mock()
        mock_person.name = "John Doe"

        mock_retirement_analysis = Mock()
        mock_retirement_analysis.person = mock_person
        mock_retirement_analysis.goals = [mock_goal]
        mock_retirement_analysis.overall_success_rate = 85.5
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
    @patch('retirement_planner.reports.generator.ChartCreator.create_success_rate_chart')
    @patch('retirement_planner.reports.generator.DataExporter.export_simulation_data')
    @patch('retirement_planner.reports.generator.DataExporter.export_analysis_summary')
    def test_generate_comprehensive_report(
        self, mock_export_summary, mock_export_data,
        mock_success_chart, mock_portfolio_chart
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

        mock_goal = Mock()
        mock_goal.name = "Retirement Goal"
        mock_goal.target_amount = 1000000
        mock_goal.success_rate = 85.5
        mock_goal.priority = "high"

        mock_retirement_analysis = Mock()
        mock_retirement_analysis.person = mock_person
        mock_retirement_analysis.goals = [mock_goal]
        mock_retirement_analysis.recommendations = ["Save more", "Invest wisely"]

        # Create mock scenarios for simulation result
        mock_scenario = Mock()
        mock_scenario.portfolio_values = [100000, 105000, 110000, 108000, 115000]
        mock_scenario.success = True

        mock_simulation_result = Mock()
        mock_simulation_result.num_scenarios = 1000
        mock_simulation_result.time_horizon = 20
        mock_simulation_result.success_rate = 85.5
        mock_simulation_result.avg_final_value = 1200000
        mock_simulation_result.median_final_value = 1150000
        mock_simulation_result.scenarios = [mock_scenario] * 10  # 10 scenarios

        # Create mock withdrawal strategy
        mock_strategy = Mock()
        mock_strategy.name = "Fixed Withdrawal"
        mock_strategy.success_rate = 90.0
        mock_strategy.avg_annual_withdrawal = 50000

        mock_withdrawal_result = Mock()
        mock_withdrawal_result.best_strategy = mock_strategy
        mock_withdrawal_result.strategies = [mock_strategy]

        # Setup mock return values
        mock_portfolio_chart.return_value = Path("portfolio_chart.png")
        mock_success_chart.return_value = Path("success_chart.png")
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
            assert "success_chart" in report_files
            assert "simulation_data" in report_files
            assert "analysis_summary" in report_files

            # Verify directories were created
            assert output_dir.exists()
            assert (output_dir / "charts").exists()
            assert (output_dir / "data").exists()

            # Verify mock calls
            mock_portfolio_chart.assert_called_once()
            mock_success_chart.assert_called_once()
            mock_export_data.assert_called_once()
            mock_export_summary.assert_called_once()

    def test_generate_comprehensive_report_no_charts(self):
        """Test report generation without charts."""
        config = ReportConfig(include_charts=False)
        report_generator = ReportGenerator(config=config, logger=self.logger)

        # Create mock objects with proper attributes
        mock_person = Mock()
        mock_person.name = "John Doe"
        mock_person.age = 45
        mock_person.retirement_age = 65
        mock_person.life_expectancy = 85
        mock_person.current_savings = 500000
        mock_person.annual_contribution = 20000

        mock_retirement_analysis = Mock()
        mock_retirement_analysis.person = mock_person
        mock_retirement_analysis.goals = []
        mock_retirement_analysis.recommendations = []

        mock_simulation_result = Mock()
        mock_simulation_result.num_scenarios = 1000
        mock_simulation_result.time_horizon = 20
        mock_simulation_result.success_rate = 85.5
        mock_simulation_result.avg_final_value = 1200000
        mock_simulation_result.median_final_value = 1150000

        with tempfile.TemporaryDirectory() as temp_dir:
            output_dir = Path(temp_dir) / "reports"

            report_files = report_generator.generate_comprehensive_report(
                retirement_analysis=mock_retirement_analysis,
                simulation_result=mock_simulation_result,
                output_dir=output_dir
            )

            # Should only have text report
            assert "text_report" in report_files
            assert "portfolio_chart" not in report_files
            assert "success_chart" not in report_files

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

        mock_retirement_analysis = Mock()
        mock_retirement_analysis.person = mock_person
        mock_retirement_analysis.goals = []
        mock_retirement_analysis.recommendations = []

        # Create mock scenarios for simulation result
        mock_scenario = Mock()
        mock_scenario.portfolio_values = [100000 + 1000 * i for i in range(21)]  # 21 years for time_horizon=20
        mock_scenario.success = True

        mock_simulation_result = Mock()
        mock_simulation_result.num_scenarios = 1000
        mock_simulation_result.time_horizon = 20
        mock_simulation_result.success_rate = 85.5
        mock_simulation_result.avg_final_value = 1200000
        mock_simulation_result.median_final_value = 1150000
        mock_simulation_result.scenarios = [mock_scenario] * 10  # 10 scenarios

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

        mock_goal = Mock()
        mock_goal.name = "Retirement Goal"
        mock_goal.target_amount = 1000000
        mock_goal.success_rate = 85.5
        mock_goal.priority = "high"

        mock_retirement_analysis = Mock()
        mock_retirement_analysis.person = mock_person
        mock_retirement_analysis.goals = [mock_goal]
        mock_retirement_analysis.recommendations = ["Save more", "Invest wisely"]

        mock_simulation_result = Mock()
        mock_simulation_result.num_scenarios = 1000
        mock_simulation_result.time_horizon = 20
        mock_simulation_result.success_rate = 85.5
        mock_simulation_result.avg_final_value = 1200000
        mock_simulation_result.median_final_value = 1150000

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