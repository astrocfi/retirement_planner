"""
User-friendly logging system for retirement planner.

Provides clear, readable financial explanations and progress tracking
instead of technical audit trails.
"""

import logging
import sys
from typing import Any, Dict, List, Optional, Union
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from .exceptions import RetirementPlannerException


class LogLevel(Enum):
    """User-friendly log levels."""
    INFO = 1
    WARNING = 2
    ERROR = 3
    SUCCESS = 4
    RECOMMENDATION = 5


@dataclass
class LogMessage:
    """A user-friendly log message with financial context."""
    level: LogLevel
    message: str
    timestamp: datetime = field(default_factory=datetime.now)
    context: Dict[str, Any] = field(default_factory=dict)
    financial_data: Dict[str, Any] = field(default_factory=dict)


class FinancialFormatter:
    """Formats financial data in user-friendly ways."""

    @staticmethod
    def format_currency(amount: float) -> str:
        """Format currency with proper commas and decimal places."""
        if abs(amount) >= 1_000_000_000:
            return f"${amount/1_000_000_000:.1f}B"
        elif abs(amount) >= 1_000_000:
            return f"${amount/1_000_000:.1f}M"
        elif abs(amount) >= 1_000:
            return f"${amount:,.0f}"
        else:
            return f"${amount:.2f}"

    @staticmethod
    def format_percentage(value: float) -> str:
        """Format percentage with appropriate precision."""
        if abs(value) < 0.1:
            return f"{value:.3f}%"
        elif abs(value) < 1:
            return f"{value:.2f}%"
        else:
            return f"{value:.1f}%"

    @staticmethod
    def format_age(age: int) -> str:
        """Format age consistently."""
        return f"age {age}"

    @staticmethod
    def format_portfolio_allocation(allocation: Dict[str, float]) -> str:
        """Format portfolio allocation in readable format."""
        parts = []
        for asset, percentage in allocation.items():
            parts.append(f"{percentage:.0f}% {asset}")
        return ", ".join(parts)


class UserLogger:
    """Provides clear, readable messages for users."""

    def __init__(self, formatter: Optional[FinancialFormatter] = None):
        self.formatter = formatter or FinancialFormatter()

    def log_progress(self, operation: str, current: int, total: int,
                    additional_info: Optional[Dict[str, Any]] = None) -> str:
        """Log progress for long-running operations."""
        percentage = (current / total) * 100
        message = f"{operation}: {percentage:.0f}% complete ({current:,} of {total:,})"

        if additional_info:
            info_parts = []
            for key, value in additional_info.items():
                if key.endswith('_rate') or key.endswith('_percentage'):
                    info_parts.append(f"{key}: {self.formatter.format_percentage(value)}")
                elif 'scenario' in key and isinstance(value, (int, float)):
                    info_parts.append(f"{key}: {self.formatter.format_currency(value)}")
                elif isinstance(value, float):
                    info_parts.append(f"{key}: {self.formatter.format_currency(value)}")
                else:
                    info_parts.append(f"{key}: {value}")
            message += f" • {' • '.join(info_parts)}"

        return message

    def log_financial_calculation(self, calculation_type: str,
                                result: float, context: Dict[str, Any]) -> str:
        """Log financial calculations with clear explanations."""
        if calculation_type == "rmd":
            age = context.get('age', 'unknown')
            balance = context.get('balance', 0)
            return (f"Your required minimum distribution (RMD) at {self.formatter.format_age(age)} "
                   f"is {self.formatter.format_currency(result)}")

        elif calculation_type == "tax":
            tax_type = context.get('tax_type', 'tax')
            income = context.get('income', 0)
            return (f"{tax_type.title()} on {self.formatter.format_currency(income)}: "
                   f"{self.formatter.format_currency(result)} ({self.formatter.format_percentage(result/income*100)} rate)")

        elif calculation_type == "return":
            period = context.get('period', 'period')
            benchmark = context.get('benchmark', None)
            message = f"Portfolio returned {self.formatter.format_percentage(result)} in {period}"
            if benchmark:
                message += f", {'above' if result > benchmark else 'below'} the {self.formatter.format_percentage(benchmark)} benchmark"
            return message

        else:
            return f"{calculation_type.title()}: {self.formatter.format_currency(result)}"

    def log_portfolio_allocation(self, allocation: Dict[str, float],
                               portfolio_value: float) -> str:
        """Log portfolio allocation in readable format."""
        parts = []
        for asset, percentage in allocation.items():
            value = (percentage / 100) * portfolio_value
            parts.append(f"{percentage:.0f}% {asset} ({self.formatter.format_currency(value)})")
        return f"Your current allocation is {', '.join(parts)}"

    def log_cash_flow(self, income_sources: Dict[str, float],
                     expense_categories: Dict[str, float]) -> str:
        """Log cash flow information."""
        income_parts = []
        for source, amount in income_sources.items():
            income_parts.append(f"{self.formatter.format_currency(amount)} from {source}")

        expense_parts = []
        for category, amount in expense_categories.items():
            expense_parts.append(f"{self.formatter.format_currency(amount)} for {category}")

        return (f"Monthly income: {' + '.join(income_parts)} • "
               f"Monthly expenses: {' + '.join(expense_parts)}")


class ProgressLogger:
    """Provides progress updates for long-running operations."""

    def __init__(self, user_logger: UserLogger):
        self.user_logger = user_logger
        self.start_time: Optional[datetime] = None

    def start_operation(self, operation_name: str, total_items: int) -> None:
        """Start a new operation with progress tracking."""
        self.start_time = datetime.now()
        print(f"Starting {operation_name}...")
        print(f"  • Processing {total_items:,} items")

    def update_progress(self, operation: str, current: int, total: int,
                       additional_info: Optional[Dict[str, Any]] = None) -> None:
        """Update progress for current operation."""
        message = self.user_logger.log_progress(operation, current, total, additional_info)
        print(f"Progress: {message}")

    def complete_operation(self, operation_name: str, results: Dict[str, Any]) -> None:
        """Complete an operation with summary results."""
        print(f"\n{operation_name} complete!")
        for key, value in results.items():
            if isinstance(value, float):
                if key.endswith('_rate') or key.endswith('_percentage'):
                    formatted_value = self.user_logger.formatter.format_percentage(value)
                else:
                    formatted_value = self.user_logger.formatter.format_currency(value)
            else:
                formatted_value = str(value)
            print(f"  • {key.replace('_', ' ').title()}: {formatted_value}")


class FinancialLogger:
    """Explains financial calculations in plain English."""

    def __init__(self, user_logger: UserLogger):
        self.user_logger = user_logger

    def log_tax_analysis(self, tax_brackets: Dict[str, float],
                        deductions: Dict[str, float]) -> str:
        """Log tax analysis in plain English."""
        parts = []
        for bracket, rate in tax_brackets.items():
            parts.append(f"{bracket}: {self.user_logger.formatter.format_percentage(rate)}")

        deduction_parts = []
        for deduction_type, amount in deductions.items():
            deduction_parts.append(f"{self.user_logger.formatter.format_currency(amount)} {deduction_type}")

        return (f"Tax brackets: {', '.join(parts)} • "
               f"Deductions: {', '.join(deduction_parts)}")

    def log_investment_recommendation(self, recommendation: str,
                                    expected_impact: Dict[str, float]) -> str:
        """Log investment recommendations with expected impact."""
        impact_parts = []
        for metric, value in expected_impact.items():
            if isinstance(value, float):
                if metric.endswith('_increase') or metric.endswith('_reduction'):
                    impact_parts.append(f"{metric.replace('_', ' ')}: {self.user_logger.formatter.format_percentage(value)}")
                else:
                    impact_parts.append(f"{metric.replace('_', ' ')}: {self.user_logger.formatter.format_currency(value)}")

        return f"Recommendation: {recommendation} • Expected impact: {' • '.join(impact_parts)}"

    def log_risk_assessment(self, risk_level: str, risk_score: float,
                          risk_factors: List[str]) -> str:
        """Log risk assessment in plain English."""
        factors = ', '.join(risk_factors)
        return (f"Risk level: {risk_level} ({risk_score}/10) • "
               f"Key factors: {factors}")


class RetirementPlannerLogger:
    """Main logging interface with user-friendly messages."""

    def __init__(self, log_level: LogLevel = LogLevel.INFO):
        self.log_level = log_level
        self.formatter = FinancialFormatter()
        self.user_logger = UserLogger(self.formatter)
        self.progress_logger = ProgressLogger(self.user_logger)
        self.financial_logger = FinancialLogger(self.user_logger)
        self.messages: List[LogMessage] = []

    def log(self, level: LogLevel, message: str,
            context: Optional[Dict[str, Any]] = None,
            financial_data: Optional[Dict[str, Any]] = None) -> None:
        """Log a message with the specified level."""
        if level.value >= self.log_level.value:
            log_msg = LogMessage(
                level=level,
                message=message,
                context=context or {},
                financial_data=financial_data or {}
            )
            self.messages.append(log_msg)

            # Print to console with appropriate formatting
            timestamp = log_msg.timestamp.strftime("%H:%M:%S")
            print(f"[{timestamp}] {level.name}: {message}")

    def info(self, message: str, **kwargs) -> None:
        """Log an informational message."""
        self.log(LogLevel.INFO, message, **kwargs)

    def warning(self, message: str, **kwargs) -> None:
        """Log a warning message."""
        self.log(LogLevel.WARNING, f"Warning: {message}", **kwargs)

    def error(self, message: str, **kwargs) -> None:
        """Log an error message."""
        self.log(LogLevel.ERROR, f"Error: {message}", **kwargs)

    def success(self, message: str, **kwargs) -> None:
        """Log a success message."""
        self.log(LogLevel.SUCCESS, f"Success: {message}", **kwargs)

    def recommendation(self, message: str, **kwargs) -> None:
        """Log a recommendation message."""
        self.log(LogLevel.RECOMMENDATION, f"Recommendation: {message}", **kwargs)

    def log_progress(self, operation: str, current: int, total: int,
                    additional_info: Optional[Dict[str, Any]] = None) -> None:
        """Log progress for long-running operations."""
        message = self.user_logger.log_progress(operation, current, total, additional_info)
        self.info(message)

    def log_financial_calculation(self, calculation_type: str, result: float,
                                context: Dict[str, Any]) -> None:
        """Log financial calculations with clear explanations."""
        message = self.user_logger.log_financial_calculation(calculation_type, result, context)
        self.info(message, financial_data={'calculation_type': calculation_type, 'result': result})

    def log_portfolio_allocation(self, allocation: Dict[str, float],
                               portfolio_value: float) -> None:
        """Log portfolio allocation in readable format."""
        message = self.user_logger.log_portfolio_allocation(allocation, portfolio_value)
        self.info(message, financial_data={'allocation': allocation, 'portfolio_value': portfolio_value})

    def start_progress_tracking(self, operation_name: str, total_items: int) -> None:
        """Start progress tracking for an operation."""
        self.progress_logger.start_operation(operation_name, total_items)

    def update_progress(self, operation: str, current: int, total: int,
                       additional_info: Optional[Dict[str, Any]] = None) -> None:
        """Update progress for current operation."""
        self.progress_logger.update_progress(operation, current, total, additional_info)

    def complete_progress(self, operation_name: str, results: Dict[str, Any]) -> None:
        """Complete progress tracking with results."""
        self.progress_logger.complete_operation(operation_name, results)

    def get_messages(self, level: Optional[LogLevel] = None) -> List[LogMessage]:
        """Get logged messages, optionally filtered by level."""
        if level is None:
            return self.messages
        return [msg for msg in self.messages if msg.level == level]

    def clear_messages(self) -> None:
        """Clear all logged messages."""
        self.messages.clear()