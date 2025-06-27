"""
Unit tests for retirement planner user-friendly logging system.

These tests verify the logging system provides clear, readable financial
explanations and progress tracking.
"""

import pytest
from datetime import datetime
from retirement_planner.core.logging import (
    LogLevel,
    LogMessage,
    FinancialFormatter,
    UserLogger,
    ProgressLogger,
    FinancialLogger,
    RetirementPlannerLogger,
)


class TestLogLevel:
    """Test LogLevel enum functionality."""

    def test_log_level_values(self):
        """Test that log levels have correct values."""
        assert LogLevel.INFO.value == 1
        assert LogLevel.WARNING.value == 2
        assert LogLevel.ERROR.value == 3
        assert LogLevel.SUCCESS.value == 4
        assert LogLevel.RECOMMENDATION.value == 5

    def test_log_level_comparison(self):
        """Test log level comparison functionality."""
        assert LogLevel.INFO.value < LogLevel.WARNING.value
        assert LogLevel.WARNING.value < LogLevel.ERROR.value
        assert LogLevel.SUCCESS.value > LogLevel.INFO.value


class TestLogMessage:
    """Test LogMessage dataclass functionality."""

    def test_log_message_creation(self):
        """Test creating a LogMessage instance."""
        message = LogMessage(
            level=LogLevel.INFO,
            message="Test message",
            context={"user_id": 123},
            financial_data={"amount": 1000}
        )

        assert message.level == LogLevel.INFO
        assert message.message == "Test message"
        assert message.context == {"user_id": 123}
        assert message.financial_data == {"amount": 1000}
        assert isinstance(message.timestamp, datetime)

    def test_log_message_defaults(self):
        """Test LogMessage with default values."""
        message = LogMessage(level=LogLevel.INFO, message="Test")

        assert message.context == {}
        assert message.financial_data == {}
        assert isinstance(message.timestamp, datetime)


class TestFinancialFormatter:
    """Test FinancialFormatter functionality."""

    def test_format_currency_small_amount(self):
        """Test currency formatting for small amounts."""
        formatter = FinancialFormatter()
        assert formatter.format_currency(123.45) == "$123.45"
        assert formatter.format_currency(999.99) == "$999.99"

    def test_format_currency_medium_amount(self):
        """Test currency formatting for medium amounts."""
        formatter = FinancialFormatter()
        assert formatter.format_currency(1500) == "$1,500"
        assert formatter.format_currency(50000) == "$50,000"

    def test_format_currency_large_amount(self):
        """Test currency formatting for large amounts."""
        formatter = FinancialFormatter()
        assert formatter.format_currency(1500000) == "$1.5M"
        assert formatter.format_currency(2500000000) == "$2.5B"

    def test_format_percentage_small(self):
        """Test percentage formatting for small values."""
        formatter = FinancialFormatter()
        assert formatter.format_percentage(0.05) == "0.050%"
        assert formatter.format_percentage(0.5) == "0.50%"

    def test_format_percentage_medium(self):
        """Test percentage formatting for medium values."""
        formatter = FinancialFormatter()
        assert formatter.format_percentage(5.5) == "5.5%"
        assert formatter.format_percentage(25.0) == "25.0%"

    def test_format_percentage_large(self):
        """Test percentage formatting for large values."""
        formatter = FinancialFormatter()
        assert formatter.format_percentage(100) == "100.0%"
        assert formatter.format_percentage(250) == "250.0%"

    def test_format_age(self):
        """Test age formatting."""
        formatter = FinancialFormatter()
        assert formatter.format_age(45) == "age 45"
        assert formatter.format_age(65) == "age 65"

    def test_format_portfolio_allocation(self):
        """Test portfolio allocation formatting."""
        formatter = FinancialFormatter()
        allocation = {"stocks": 60, "bonds": 30, "cash": 10}
        result = formatter.format_portfolio_allocation(allocation)
        assert result == "60% stocks, 30% bonds, 10% cash"


class TestUserLogger:
    """Test UserLogger functionality."""

    def test_user_logger_creation(self):
        """Test creating UserLogger instance."""
        logger = UserLogger()
        assert isinstance(logger.formatter, FinancialFormatter)

    def test_log_progress_basic(self):
        """Test basic progress logging."""
        logger = UserLogger()
        message = logger.log_progress("Monte Carlo simulation", 500, 1000)
        assert "50% complete" in message
        assert "500 of 1,000" in message

    def test_log_progress_no_additional_info(self):
        logger = UserLogger()
        message = logger.log_progress("EdgeCaseRun", 1, 2)
        assert "50% complete" in message
        assert "1 of 2" in message

    def test_log_progress_with_additional_info(self):
        """Test progress logging with additional information."""
        logger = UserLogger()
        additional_info = {"success_rate": 75.5, "best_scenario": 2000000}
        message = logger.log_progress("Optimization", 3, 8, additional_info)
        assert "38% complete" in message
        assert "success_rate: 75.5%" in message
        assert "best_scenario: $2.0M" in message

    def test_log_progress_with_mixed_additional_info(self):
        """Test progress logging with mixed data types in additional info."""
        logger = UserLogger()
        additional_info = {"success_rate": 75.5, "status": "running", "iterations": 1000}
        message = logger.log_progress("Optimization", 3, 8, additional_info)
        assert "38% complete" in message
        assert "success_rate: 75.5%" in message
        assert "status: running" in message
        assert "iterations: 1000" in message

    def test_log_financial_calculation_rmd(self):
        """Test RMD calculation logging."""
        logger = UserLogger()
        context = {"age": 75, "balance": 500000}
        message = logger.log_financial_calculation("rmd", 18250, context)
        assert "Your required minimum distribution (RMD) at age 75 is $18,250" in message

    def test_log_financial_calculation_tax(self):
        """Test tax calculation logging."""
        logger = UserLogger()
        context = {"tax_type": "capital gains", "income": 50000}
        message = logger.log_financial_calculation("tax", 7500, context)
        assert "Capital Gains on $50,000: $7,500 (15.0% rate)" in message

    def test_log_financial_calculation_return(self):
        """Test return calculation logging."""
        logger = UserLogger()
        context = {"period": "2024", "benchmark": 7.2}
        message = logger.log_financial_calculation("return", 8.5, context)
        assert "Portfolio returned 8.5% in 2024" in message
        assert "above the 7.2% benchmark" in message

    def test_log_financial_calculation_unknown_type(self):
        """Test financial calculation logging with unknown calculation type."""
        logger = UserLogger()
        context = {"source": "custom"}
        message = logger.log_financial_calculation("custom_calc", 15000, context)
        assert "Custom_Calc: $15,000" in message

    def test_log_portfolio_allocation(self):
        """Test portfolio allocation logging."""
        logger = UserLogger()
        allocation = {"stocks": 60, "bonds": 30, "cash": 10}
        message = logger.log_portfolio_allocation(allocation, 500000)
        assert "60% stocks ($300,000)" in message
        assert "30% bonds ($150,000)" in message
        assert "10% cash ($50,000)" in message

    def test_log_cash_flow(self):
        """Test cash flow logging."""
        logger = UserLogger()
        income = {"salary": 8500, "social_security": 2200}
        expenses = {"housing": 3000, "healthcare": 800}
        message = logger.log_cash_flow(income, expenses)
        assert "$8,500 from salary" in message
        assert "$2,200 from social_security" in message
        assert "$3,000 for housing" in message
        assert "$800.00 for healthcare" in message


class TestProgressLogger:
    """Test ProgressLogger functionality."""

    def test_progress_logger_creation(self):
        """Test creating ProgressLogger instance."""
        user_logger = UserLogger()
        progress_logger = ProgressLogger(user_logger)
        assert progress_logger.user_logger == user_logger
        assert progress_logger.start_time is None

    def test_start_operation(self):
        """Test starting an operation."""
        user_logger = UserLogger()
        progress_logger = ProgressLogger(user_logger)
        progress_logger.start_operation("Test Operation", 1000)
        assert progress_logger.start_time is not None

    def test_update_progress(self):
        """Test updating progress."""
        user_logger = UserLogger()
        progress_logger = ProgressLogger(user_logger)
        progress_logger.update_progress("Test", 500, 1000)
        # This should print to console, so we just verify it doesn't raise an error

    def test_complete_operation(self):
        """Test completing an operation."""
        user_logger = UserLogger()
        progress_logger = ProgressLogger(user_logger)
        results = {"success_rate": 85.5, "total_scenarios": 2500}
        progress_logger.complete_operation("Test Operation", results)
        # This should print to console, so we just verify it doesn't raise an error

    def test_complete_operation_with_mixed_data(self):
        """Test completing an operation with mixed data types."""
        user_logger = UserLogger()
        progress_logger = ProgressLogger(user_logger)
        results = {"success_rate": 85.5, "status": "completed", "total_scenarios": 2500}
        progress_logger.complete_operation("Test Operation", results)
        # This should print to console, so we just verify it doesn't raise an error

    def test_complete_operation_with_string(self):
        user_logger = UserLogger()
        progress_logger = ProgressLogger(user_logger)
        results = {"note": ["done", "reviewed"]}
        progress_logger.complete_operation("Test Operation", results)


class TestFinancialLogger:
    """Test FinancialLogger functionality."""

    def test_financial_logger_creation(self):
        """Test creating FinancialLogger instance."""
        user_logger = UserLogger()
        financial_logger = FinancialLogger(user_logger)
        assert financial_logger.user_logger == user_logger

    def test_log_tax_analysis(self):
        """Test tax analysis logging."""
        user_logger = UserLogger()
        financial_logger = FinancialLogger(user_logger)
        tax_brackets = {"22%": 22.0, "24%": 24.0}
        deductions = {"standard": 12950, "itemized": 15000}
        message = financial_logger.log_tax_analysis(tax_brackets, deductions)
        assert "22%: 22.0%" in message
        assert "24%: 24.0%" in message
        assert "$12,950 standard" in message
        assert "$15,000 itemized" in message

    def test_log_investment_recommendation(self):
        """Test investment recommendation logging."""
        user_logger = UserLogger()
        financial_logger = FinancialLogger(user_logger)
        recommendation = "Increase international exposure"
        expected_impact = {"return_increase": 0.5, "risk_reduction": 0.8}
        message = financial_logger.log_investment_recommendation(recommendation, expected_impact)
        assert "Recommendation: Increase international exposure" in message
        assert "return increase: 0.50%" in message
        assert "risk reduction: 0.80%" in message

    def test_log_investment_recommendation_with_mixed_data(self):
        """Test investment recommendation logging with mixed data types."""
        user_logger = UserLogger()
        financial_logger = FinancialLogger(user_logger)
        recommendation = "Rebalance portfolio"
        expected_impact = {"return_increase": 0.5, "implementation_cost": 500.0, "timeframe_months": 3.0}
        message = financial_logger.log_investment_recommendation(recommendation, expected_impact)
        assert "Recommendation: Rebalance portfolio" in message
        assert "return increase: 0.50%" in message
        assert "implementation cost: $500" in message
        assert "timeframe months: $3.00" in message

    def test_log_risk_assessment(self):
        """Test risk assessment logging."""
        user_logger = UserLogger()
        financial_logger = FinancialLogger(user_logger)
        risk_level = "Moderate"
        risk_score = 7.0
        risk_factors = ["high equity allocation", "concentration in tech"]
        message = financial_logger.log_risk_assessment(risk_level, risk_score, risk_factors)
        assert "Risk level: Moderate (7.0/10)" in message
        assert "high equity allocation, concentration in tech" in message


class TestRetirementPlannerLogger:
    """Test RetirementPlannerLogger functionality."""

    def test_logger_creation(self):
        """Test creating RetirementPlannerLogger instance."""
        logger = RetirementPlannerLogger()
        assert logger.log_level == LogLevel.INFO
        assert isinstance(logger.formatter, FinancialFormatter)
        assert isinstance(logger.user_logger, UserLogger)
        assert isinstance(logger.progress_logger, ProgressLogger)
        assert isinstance(logger.financial_logger, FinancialLogger)
        assert logger.messages == []

    def test_logger_creation_with_custom_level(self):
        """Test creating logger with custom log level."""
        logger = RetirementPlannerLogger(LogLevel.WARNING)
        assert logger.log_level == LogLevel.WARNING

    def test_log_info_message(self):
        """Test logging info message."""
        logger = RetirementPlannerLogger()
        logger.info("Test info message")
        assert len(logger.messages) == 1
        assert logger.messages[0].level == LogLevel.INFO
        assert logger.messages[0].message == "Test info message"

    def test_log_warning_message(self):
        """Test logging warning message."""
        logger = RetirementPlannerLogger()
        logger.warning("Test warning message")
        assert len(logger.messages) == 1
        assert logger.messages[0].level == LogLevel.WARNING
        assert "Warning: Test warning message" in logger.messages[0].message

    def test_log_error_message(self):
        """Test logging error message."""
        logger = RetirementPlannerLogger()
        logger.error("Test error message")
        assert len(logger.messages) == 1
        assert logger.messages[0].level == LogLevel.ERROR
        assert "Error: Test error message" in logger.messages[0].message

    def test_log_success_message(self):
        """Test logging success message."""
        logger = RetirementPlannerLogger()
        logger.success("Test success message")
        assert len(logger.messages) == 1
        assert logger.messages[0].level == LogLevel.SUCCESS
        assert "Success: Test success message" in logger.messages[0].message

    def test_log_recommendation_message(self):
        """Test logging recommendation message."""
        logger = RetirementPlannerLogger()
        logger.recommendation("Test recommendation message")
        assert len(logger.messages) == 1
        assert logger.messages[0].level == LogLevel.RECOMMENDATION
        assert "Recommendation: Test recommendation message" in logger.messages[0].message

    def test_log_with_context(self):
        """Test logging with context information."""
        logger = RetirementPlannerLogger()
        context = {"user_id": 123, "scenario": "base_case"}
        logger.info("Test message", context=context)
        assert logger.messages[0].context == context

    def test_log_with_financial_data(self):
        """Test logging with financial data."""
        logger = RetirementPlannerLogger()
        financial_data = {"portfolio_value": 500000, "allocation": {"stocks": 60}}
        logger.info("Test message", financial_data=financial_data)
        assert logger.messages[0].financial_data == financial_data

    def test_log_level_filtering(self):
        """Test log level filtering."""
        logger = RetirementPlannerLogger(LogLevel.WARNING)
        logger.info("Info message")  # Should not be logged
        logger.warning("Warning message")  # Should be logged
        logger.error("Error message")  # Should be logged

        assert len(logger.messages) == 2
        assert all(msg.level in [LogLevel.WARNING, LogLevel.ERROR] for msg in logger.messages)

    def test_log_progress(self):
        """Test logging progress."""
        logger = RetirementPlannerLogger()
        logger.log_progress("Test operation", 500, 1000)
        assert len(logger.messages) == 1
        assert "50% complete" in logger.messages[0].message

    def test_log_financial_calculation(self):
        """Test logging financial calculation."""
        logger = RetirementPlannerLogger()
        context = {"age": 75, "balance": 500000}
        logger.log_financial_calculation("rmd", 18250, context)
        assert len(logger.messages) == 1
        assert "RMD" in logger.messages[0].message
        assert logger.messages[0].financial_data["calculation_type"] == "rmd"
        assert logger.messages[0].financial_data["result"] == 18250

    def test_log_portfolio_allocation(self):
        """Test logging portfolio allocation."""
        logger = RetirementPlannerLogger()
        allocation = {"stocks": 60, "bonds": 30, "cash": 10}
        logger.log_portfolio_allocation(allocation, 500000)
        assert len(logger.messages) == 1
        assert "60% stocks" in logger.messages[0].message
        assert logger.messages[0].financial_data["allocation"] == allocation
        assert logger.messages[0].financial_data["portfolio_value"] == 500000

    def test_get_messages_all(self):
        """Test getting all messages."""
        logger = RetirementPlannerLogger()
        logger.info("Message 1")
        logger.warning("Message 2")
        logger.error("Message 3")

        messages = logger.get_messages()
        assert len(messages) == 3

    def test_get_messages_filtered(self):
        """Test getting messages filtered by level."""
        logger = RetirementPlannerLogger()
        logger.info("Info message")
        logger.warning("Warning message")
        logger.error("Error message")

        warning_messages = logger.get_messages(LogLevel.WARNING)
        assert len(warning_messages) == 1
        assert warning_messages[0].level == LogLevel.WARNING

    def test_clear_messages(self):
        """Test clearing messages."""
        logger = RetirementPlannerLogger()
        logger.info("Test message")
        assert len(logger.messages) == 1

        logger.clear_messages()
        assert len(logger.messages) == 0


class TestLoggingIntegration:
    """Test integration scenarios for the logging system."""

    def test_monte_carlo_simulation_logging(self):
        """Test logging for Monte Carlo simulation scenario."""
        logger = RetirementPlannerLogger()

        # Start simulation
        logger.start_progress_tracking("Monte Carlo simulation", 2500)

        # Update progress with financial context
        logger.update_progress("Monte Carlo simulation", 625, 2500,
                              {"success_rate": 78.0, "best_scenario": 2100000})

        # Log financial calculations
        logger.log_financial_calculation("return", 8.5, {"period": "2024", "benchmark": 7.2})

        # Complete with results
        results = {"success_rate": 77.0, "optimal_withdrawal_rate": 3.8, "expected_legacy": 850000}
        logger.complete_progress("Monte Carlo simulation", results)

        # Verify messages were logged (only financial calculation adds to messages)
        assert len(logger.messages) >= 1  # At least the financial calculation

    def test_tax_optimization_logging(self):
        """Test logging for tax optimization scenario."""
        logger = RetirementPlannerLogger()

        # Log current tax situation
        logger.info("Analyzing tax optimization opportunities...")

        # Log tax brackets
        tax_brackets = {"Federal 22%": 22.0, "California 9.3%": 9.3}
        deductions = {"standard": 12950}
        tax_analysis = logger.financial_logger.log_tax_analysis(tax_brackets, deductions)
        logger.info(tax_analysis)

        # Log recommendation
        recommendation = "Convert $25,000 annually to Roth IRA"
        expected_impact = {"tax_savings": 115000, "implementation_years": 10}
        rec_message = logger.financial_logger.log_investment_recommendation(recommendation, expected_impact)
        logger.recommendation(rec_message)

        # Verify messages
        assert len(logger.messages) >= 3
        assert any("tax optimization" in msg.message.lower() for msg in logger.messages)
        assert any("recommendation" in msg.message.lower() for msg in logger.messages)

    def test_portfolio_analysis_logging(self):
        """Test logging for portfolio analysis scenario."""
        logger = RetirementPlannerLogger()

        # Log current allocation
        allocation = {"stocks": 60, "bonds": 30, "cash": 10}
        logger.log_portfolio_allocation(allocation, 500000)

        # Log risk assessment
        risk_message = logger.financial_logger.log_risk_assessment(
            "Moderate", 7.0, ["high equity allocation", "concentration in tech"]
        )
        logger.info(risk_message)

        # Log recommendations
        logger.recommendation("Increase international exposure to 20%")
        logger.recommendation("Rebalance quarterly to maintain target allocation")

        # Verify messages
        assert len(logger.messages) >= 4
        assert any("60% stocks" in msg.message for msg in logger.messages)
        assert any("risk level" in msg.message.lower() for msg in logger.messages)
        assert any("recommendation" in msg.message.lower() for msg in logger.messages)