"""
Tests for report formatters.
"""

import pytest
import tempfile
import json
from pathlib import Path
from unittest.mock import Mock

from retirement_planner.reports.formatters import (
    TextFormatter, HtmlFormatter, JsonFormatter
)
from retirement_planner.core.exceptions import AnalysisError
from retirement_planner.core.logging import RetirementPlannerLogger


class TestTextFormatter:
    """Test TextFormatter functionality."""

    def setup_method(self):
        """Setup test fixtures."""
        self.logger = Mock(spec=RetirementPlannerLogger)
        self.formatter = TextFormatter(logger=self.logger)

    def test_format_report(self):
        """Test text report formatting."""
        # Create mock objects
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

        # Format report
        content = self.formatter.format_report(
            retirement_analysis=mock_retirement_analysis,
            simulation_result=mock_simulation_result
        )

        # Verify content
        assert "RETIREMENT ANALYSIS REPORT" in content
        assert "John Doe" in content
        assert "45" in content
        assert "65" in content
        assert "85" in content
        assert "$500,000" in content
        assert "$20,000" in content
        assert "1,000" in content
        assert "20" in content
        assert "85.5%" in content
        assert "$1,200,000" in content
        assert "$1,150,000" in content
        assert "Retirement Goal" in content
        assert "$1,000,000" in content
        assert "high" in content
        assert "Save more" in content
        assert "Invest wisely" in content

    def test_format_report_with_withdrawal_result(self):
        """Test text report formatting with withdrawal strategy results."""
        # Create mock objects
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

        mock_strategy = Mock()
        mock_strategy.name = "Fixed Withdrawal"
        mock_strategy.success_rate = 90.0
        mock_strategy.avg_annual_withdrawal = 50000

        mock_withdrawal_result = Mock()
        mock_withdrawal_result.best_strategy = mock_strategy

        # Format report
        content = self.formatter.format_report(
            retirement_analysis=mock_retirement_analysis,
            simulation_result=mock_simulation_result,
            withdrawal_result=mock_withdrawal_result
        )

        # Verify withdrawal strategy content
        assert "WITHDRAWAL STRATEGY ANALYSIS" in content
        assert "Fixed Withdrawal" in content
        assert "90.0%" in content
        assert "$50,000" in content

    def test_save_report(self):
        """Test saving text report to file."""
        content = "Test report content"

        with tempfile.TemporaryDirectory() as temp_dir:
            output_path = Path(temp_dir) / "report.txt"

            result_path = self.formatter.save_report(content, output_path)

            assert result_path == output_path
            assert output_path.exists()
            assert output_path.read_text() == content
            self.logger.log.assert_called()

    def test_format_report_error_handling(self):
        """Test error handling in report formatting."""
        with pytest.raises(AnalysisError, match="Failed to format text report"):
            self.formatter.format_report(
                retirement_analysis=None,
                simulation_result=None
            )


class TestHtmlFormatter:
    """Test HtmlFormatter functionality."""

    def setup_method(self):
        """Setup test fixtures."""
        self.logger = Mock(spec=RetirementPlannerLogger)
        self.formatter = HtmlFormatter(logger=self.logger)

    def test_format_report(self):
        """Test HTML report formatting."""
        # Create mock objects
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

        # Format report
        content = self.formatter.format_report(
            retirement_analysis=mock_retirement_analysis,
            simulation_result=mock_simulation_result
        )

        # Verify HTML structure
        assert "<!DOCTYPE html>" in content
        assert "<html lang='en'>" in content
        assert "<head>" in content
        assert "<title>Retirement Analysis Report</title>" in content
        assert "<style>" in content
        assert "<body>" in content
        assert "<h1>Retirement Analysis Report</h1>" in content

        # Verify content
        assert "John Doe" in content
        assert "45" in content
        assert "65" in content
        assert "85" in content
        assert "$500,000" in content
        assert "$20,000" in content
        assert "1,000" in content
        assert "20" in content
        assert "85.5%" in content
        assert "$1,200,000" in content
        assert "$1,150,000" in content
        assert "Retirement Goal" in content
        assert "$1,000,000" in content
        assert "high" in content
        assert "Save more" in content
        assert "Invest wisely" in content

        # Verify CSS classes
        assert "class='header'" in content
        assert "class='section'" in content
        assert "class='metric'" in content
        assert "class='goal'" in content
        assert "class='recommendation'" in content
        assert "class='success'" in content

    def test_format_report_with_withdrawal_result(self):
        """Test HTML report formatting with withdrawal strategy results."""
        # Create mock objects
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

        mock_strategy = Mock()
        mock_strategy.name = "Fixed Withdrawal"
        mock_strategy.success_rate = 90.0
        mock_strategy.avg_annual_withdrawal = 50000

        mock_withdrawal_result = Mock()
        mock_withdrawal_result.best_strategy = mock_strategy

        # Format report
        content = self.formatter.format_report(
            retirement_analysis=mock_retirement_analysis,
            simulation_result=mock_simulation_result,
            withdrawal_result=mock_withdrawal_result
        )

        # Verify withdrawal strategy content
        assert "Withdrawal Strategy Analysis" in content
        assert "Fixed Withdrawal" in content
        assert "90.0%" in content
        assert "$50,000" in content

    def test_save_report(self):
        """Test saving HTML report to file."""
        content = "<html><body>Test report</body></html>"

        with tempfile.TemporaryDirectory() as temp_dir:
            output_path = Path(temp_dir) / "report.html"

            result_path = self.formatter.save_report(content, output_path)

            assert result_path == output_path
            assert output_path.exists()
            assert output_path.read_text() == content
            self.logger.log.assert_called()

    def test_format_report_error_handling(self):
        """Test error handling in HTML report formatting."""
        with pytest.raises(AnalysisError, match="Failed to format HTML report"):
            self.formatter.format_report(
                retirement_analysis=None,
                simulation_result=None
            )


class TestJsonFormatter:
    """Test JsonFormatter functionality."""

    def setup_method(self):
        """Setup test fixtures."""
        self.logger = Mock(spec=RetirementPlannerLogger)
        self.formatter = JsonFormatter(logger=self.logger)

    def test_format_report(self):
        """Test JSON report formatting."""
        # Create mock objects
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

        # Format report
        content = self.formatter.format_report(
            retirement_analysis=mock_retirement_analysis,
            simulation_result=mock_simulation_result
        )

        # Parse JSON content
        data = json.loads(content)

        # Verify structure
        assert "metadata" in data
        assert "person" in data
        assert "simulation_results" in data
        assert "goals" in data
        assert "recommendations" in data

        # Verify metadata
        assert data["metadata"]["report_type"] == "retirement_analysis"

        # Verify person data
        assert data["person"]["name"] == "John Doe"
        assert data["person"]["age"] == 45
        assert data["person"]["retirement_age"] == 65
        assert data["person"]["life_expectancy"] == 85
        assert data["person"]["current_savings"] == 500000
        assert data["person"]["annual_contribution"] == 20000

        # Verify simulation results
        assert data["simulation_results"]["num_scenarios"] == 1000
        assert data["simulation_results"]["time_horizon"] == 20
        assert data["simulation_results"]["success_rate"] == 85.5
        assert data["simulation_results"]["avg_final_value"] == 1200000
        assert data["simulation_results"]["median_final_value"] == 1150000

        # Verify goals
        assert len(data["goals"]) == 1
        goal = data["goals"][0]
        assert goal["name"] == "Retirement Goal"
        assert goal["target_amount"] == 1000000
        assert goal["success_rate"] == 85.5
        assert goal["priority"] == "high"

        # Verify recommendations
        assert data["recommendations"] == ["Save more", "Invest wisely"]

    def test_format_report_with_withdrawal_result(self):
        """Test JSON report formatting with withdrawal strategy results."""
        # Create mock objects
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

        mock_strategy = Mock()
        mock_strategy.name = "Fixed Withdrawal"
        mock_strategy.success_rate = 90.0
        mock_strategy.avg_annual_withdrawal = 50000

        mock_withdrawal_result = Mock()
        mock_withdrawal_result.best_strategy = mock_strategy

        # Format report
        content = self.formatter.format_report(
            retirement_analysis=mock_retirement_analysis,
            simulation_result=mock_simulation_result,
            withdrawal_result=mock_withdrawal_result
        )

        # Parse JSON content
        data = json.loads(content)

        # Verify withdrawal analysis
        assert "withdrawal_analysis" in data
        assert "best_strategy" in data["withdrawal_analysis"]
        strategy = data["withdrawal_analysis"]["best_strategy"]
        assert strategy["name"] == "Fixed Withdrawal"
        assert strategy["success_rate"] == 90.0
        assert strategy["avg_annual_withdrawal"] == 50000

    def test_save_report(self):
        """Test saving JSON report to file."""
        content = '{"test": "data"}'

        with tempfile.TemporaryDirectory() as temp_dir:
            output_path = Path(temp_dir) / "report.json"

            result_path = self.formatter.save_report(content, output_path)

            assert result_path == output_path
            assert output_path.exists()
            assert output_path.read_text() == content
            self.logger.log.assert_called()

    def test_format_report_error_handling(self):
        """Test error handling in JSON report formatting."""
        with pytest.raises(AnalysisError, match="Failed to format JSON report"):
            self.formatter.format_report(
                retirement_analysis=None,
                simulation_result=None
            )