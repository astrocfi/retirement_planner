"""
Core module for retirement planner.

Provides foundational components including exceptions, validation,
configuration management, and user-friendly logging.
"""

from .exceptions import (
    RetirementPlannerException,
    ValidationError,
    ConfigurationError,
    DataError,
    SimulationError,
    OptimizationError,
    TaxCalculationError,
    AssetError,
    EventError,
    PortfolioError,
    ErrorContext,
    create_validation_error,
    create_configuration_error,
    create_data_error,
)

from .validation import (
    Validator,
    ValidationRule,
    ValidationResult,
    FieldValidator,
    BusinessRuleValidator,
    RequiredRule,
    TypeRule,
    RangeRule,
    AgeRule,
    PercentageRule,
    RegexRule,
    ChoiceRule,
)

from .config import (
    BaseConfig,
    ConfigLoader,
    AppConfig,
    get_default_schema,
)

from .logging import (
    LogLevel,
    LogMessage,
    FinancialFormatter,
    UserLogger,
    ProgressLogger,
    FinancialLogger,
    RetirementPlannerLogger,
)

__all__ = [
    # Exceptions
    'RetirementPlannerException',
    'ValidationError',
    'ConfigurationError',
    'DataError',
    'SimulationError',
    'OptimizationError',
    'TaxCalculationError',
    'AssetError',
    'EventError',
    'PortfolioError',
    'ErrorContext',
    'create_validation_error',
    'create_configuration_error',
    'create_data_error',

    # Validation
    'Validator',
    'ValidationRule',
    'ValidationResult',
    'FieldValidator',
    'BusinessRuleValidator',
    'RequiredRule',
    'TypeRule',
    'RangeRule',
    'AgeRule',
    'PercentageRule',
    'RegexRule',
    'ChoiceRule',

    # Configuration
    'BaseConfig',
    'ConfigLoader',
    'AppConfig',
    'get_default_schema',

    # Logging
    'LogLevel',
    'LogMessage',
    'FinancialFormatter',
    'UserLogger',
    'ProgressLogger',
    'FinancialLogger',
    'RetirementPlannerLogger',
]