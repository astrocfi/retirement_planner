# Code Inventory

This file tracks all implemented files, classes, and methods to prevent code duplication and maintain consistency.

## File Structure Status

### Core Modules
- [x] `retirement_planner/core/__init__.py`
- [x] `retirement_planner/core/exceptions.py`
- [x] `retirement_planner/core/validation.py`
- [x] `retirement_planner/core/config.py`
- [x] `retirement_planner/core/logging.py`

### Models
- [x] `retirement_planner/models/__init__.py`
- [x] `retirement_planner/models/person.py`
- [x] `retirement_planner/models/portfolio.py`
- [x] `retirement_planner/models/events.py`
- [x] `retirement_planner/models/scenarios.py`

### Assets
- [ ] `retirement_planner/assets/__init__.py`
- [ ] `retirement_planner/assets/base.py`
- [ ] `retirement_planner/assets/equities.py`
- [ ] `retirement_planner/assets/bonds.py`
- [ ] `retirement_planner/assets/alternatives.py`
- [ ] `retirement_planner/assets/cash.py`

### Taxes
- [ ] `retirement_planner/taxes/__init__.py`
- [ ] `retirement_planner/taxes/federal.py`
- [ ] `retirement_planner/taxes/california.py`
- [ ] `retirement_planner/taxes/social_security.py`
- [ ] `retirement_planner/taxes/retirement_accounts.py`

### Simulation
- [ ] `retirement_planner/simulation/__init__.py`
- [ ] `retirement_planner/simulation/monte_carlo.py`
- [ ] `retirement_planner/simulation/random_generators.py`
- [ ] `retirement_planner/simulation/correlation.py`
- [ ] `retirement_planner/simulation/scenarios.py`

### Optimization
- [ ] `retirement_planner/optimization/__init__.py`
- [ ] `retirement_planner/optimization/strategies.py`
- [ ] `retirement_planner/optimization/objectives.py`
- [ ] `retirement_planner/optimization/algorithms.py`
- [ ] `retirement_planner/optimization/constraints.py`

### Analysis
- [ ] `retirement_planner/analysis/__init__.py`
- [ ] `retirement_planner/analysis/metrics.py`
- [ ] `retirement_planner/analysis/risk.py`
- [ ] `retirement_planner/analysis/sensitivity.py`
- [ ] `retirement_planner/analysis/comparison.py`

### Reporting
- [ ] `retirement_planner/reporting/__init__.py`
- [ ] `retirement_planner/reporting/reports.py`
- [ ] `retirement_planner/reporting/charts.py`
- [ ] `retirement_planner/reporting/export.py`
- [ ] `retirement_planner/reporting/templates/`

### Data
- [x] `retirement_planner/data/__init__.py`
- [x] `retirement_planner/data/market_data.py`
- [x] `retirement_planner/data/tax_data.py`
- [ ] `retirement_planner/data/loaders.py`
- [x] `retirement_planner/data/validators.py`

### Utils
- [ ] `retirement_planner/utils/__init__.py`
- [ ] `retirement_planner/utils/math_utils.py`
- [ ] `retirement_planner/utils/date_utils.py`
- [ ] `retirement_planner/utils/file_utils.py`
- [ ] `retirement_planner/utils/validation_utils.py`

## Class Inventory

### Core Classes
- [x] `RetirementPlannerException` - Base exception class
- [x] `ValidationError` - Input validation errors
- [x] `ConfigurationError` - Configuration errors
- [x] `DataError` - Data-related errors
- [x] `SimulationError` - Simulation errors
- [x] `OptimizationError` - Optimization errors
- [x] `TaxCalculationError` - Tax calculation errors
- [x] `AssetError` - Asset-related errors
- [x] `EventError` - Event processing errors
- [x] `PortfolioError` - Portfolio operation errors
- [x] `ErrorContext` - Context information for error reporting
- [x] `Validator` - Input validation and business logic validation
- [x] `ValidationRule` - Abstract base class for validation rules
- [x] `ValidationResult` - Result of validation operations
- [x] `FieldValidator` - Validator for individual fields
- [x] `BusinessRuleValidator` - Validator for business rules
- [x] `RequiredRule` - Rule to ensure field is not None or empty
- [x] `TypeRule` - Rule to ensure field is correct type
- [x] `RangeRule` - Rule to ensure numeric field is within range
- [x] `AgeRule` - Rule to validate age values
- [x] `PercentageRule` - Rule to validate percentage values
- [x] `RegexRule` - Rule to validate string against regex pattern
- [x] `ChoiceRule` - Rule to validate value is in allowed choices
- [x] `BaseConfig` - Base class for configuration objects
- [x] `ConfigLoader` - Loads and validates configuration from YAML/JSON files
- [x] `AppConfig` - Example application configuration dataclass
- [x] `RetirementPlannerLogger` - Main logging interface with user-friendly messages
- [x] `UserLogger` - Clear, readable messages for users
- [x] `ProgressLogger` - Progress updates for long-running operations
- [x] `FinancialLogger` - Financial calculations explained in plain English
- [ ] `ConfigurationManager` - Manages YAML/JSON configuration files

### Model Classes
- [x] `Person` - Person profile with age, income, expenses, goals
- [x] `Income` - Income source with amount, timing, and probability
- [x] `Expense` - Expense category with amount, frequency, and timing
- [x] `Goal` - Retirement planning goal with priority and type
- [x] `Portfolio` - Asset allocation and holdings management
- [x] `Event` - Base event class for temporal modeling
- [x] `EventManager` - Manages event processing and resolution
- [x] `EventType` - Enumeration of event types (income, expense, asset, etc.)
- [x] `Period` - Time period with age-based boundaries
- [ ] `Scenario` - Scenario definition and management

### Asset Classes
- [ ] `Asset` - Base asset class with common functionality
- [ ] `Equity` - Domestic/international stocks
- [ ] `Bond` - Government/corporate bonds
- [ ] `RealEstate` - Real estate investments
- [ ] `Commodity` - Commodities and precious metals
- [ ] `PrivateEquity` - Private equity investments
- [ ] `Cash` - Cash equivalents

### Tax Classes
- [ ] `TaxCalculator` - Base tax calculation class
- [ ] `FederalTax` - Federal income tax calculations
- [ ] `CaliforniaTax` - California state tax calculations
- [ ] `SocialSecurity` - Social Security benefit calculations
- [ ] `RetirementAccount` - IRA/401(k) rules and calculations

### Simulation Classes
- [ ] `MonteCarloSimulator` - Main Monte Carlo simulation engine
- [ ] `RandomGenerator` - Random number generation
- [ ] `CorrelationMatrix` - Correlation matrices and Cholesky decomposition
- [ ] `EconomicScenario` - Economic scenario generation

### Optimization Classes
- [ ] `Strategy` - Strategy definition and parameter spaces
- [ ] `ObjectiveFunction` - Optimization objectives and scoring
- [ ] `Optimizer` - Grid search, genetic algorithms, Bayesian optimization
- [ ] `Constraint` - Financial, behavioral, regulatory constraints

### Analysis Classes
- [ ] `PerformanceMetrics` - Performance metrics calculation
- [ ] `RiskAnalyzer` - Risk analysis and VaR calculations
- [ ] `SensitivityAnalyzer` - Sensitivity analysis and tornado charts
- [ ] `StrategyComparator` - Strategy comparison and baseline analysis

### Reporting Classes
- [ ] `ReportGenerator` - Report generation and formatting
- [ ] `ChartGenerator` - Visualization and chart creation
- [ ] `DataExporter` - PDF, Excel, API export capabilities

### Data Classes
- [x] `MarketDataLoader` - Historical returns and correlation data
- [x] `HistoricalReturns` - Historical returns data for assets
- [x] `CorrelationMatrix` - Correlation matrix for asset returns
- [x] `RiskFreeRate` - Risk-free rate data
- [x] `TaxDataLoader` - Tax brackets, rates, limits
- [x] `TaxBracket` - Individual tax bracket with rate and income range
- [x] `TaxBrackets` - Complete set of tax brackets for a filing status and year
- [x] `SocialSecurityData` - Social Security parameters and benefit calculations
- [x] `DataValidator` - Data validation and quality checks
- [x] `OutlierDetector` - Detect outliers in data using various statistical methods
- [x] `DataQualityChecker` - Check data quality and consistency
- [x] `ValidationResult` - Result of data validation operations

### Utility Classes
- [ ] `MathUtils` - Mathematical utilities and statistical functions
- [ ] `DateUtils` - Date/age conversions and time period calculations
- [ ] `FileUtils` - File I/O and configuration file handling
- [ ] `ValidationUtils` - Validation helper functions

## Method Inventory

### Common Methods (Implemented in Base Classes)
- [x] `validate()` - Input validation
- [x] `to_dict()` - Convert to dictionary for serialization
- [x] `__repr__()` - String representation
- [x] `__eq__()` - Equality comparison
- [x] `__str__()` - String representation with context
- [x] `add_error()` - Add error to validation result
- [x] `add_warning()` - Add warning to validation result
- [x] `merge()` - Merge validation results
- [x] `__call__()` - Allow validation rules to be called directly
- [x] `from_dict()` - Create config object from dictionary
- [x] `load_from_file()` - Load configuration from YAML/JSON file
- [x] `override_with_env()` - Override config with environment variables
- [x] `validate_schema()` - Validate config against JSON schema
- [x] `get_config()` - Return type-safe config object
- [ ] `calculate()` - Core calculation logic
- [ ] `copy()` - Create immutable copy

### Asset Methods
- [ ] `get_return()` - Calculate asset return
- [ ] `get_volatility()` - Calculate asset volatility
- [ ] `get_correlation()` - Get correlation with other assets
- [ ] `get_tax_treatment()` - Get tax treatment information

### Tax Methods
- [ ] `calculate_tax()` - Calculate tax liability
- [ ] `get_marginal_rate()` - Get marginal tax rate
- [ ] `get_effective_rate()` - Get effective tax rate
- [ ] `get_deductions()` - Calculate available deductions

### Simulation Methods
- [ ] `generate_scenarios()` - Generate Monte Carlo scenarios
- [ ] `run_simulation()` - Run complete simulation
- [ ] `get_results()` - Get simulation results
- [ ] `validate_scenarios()` - Validate generated scenarios

### Optimization Methods
- [ ] `evaluate_strategy()` - Evaluate strategy performance
- [ ] `optimize()` - Run optimization algorithm
- [ ] `get_optimal_strategy()` - Get optimal strategy
- [ ] `compare_strategies()` - Compare multiple strategies

### Analysis Methods
- [ ] `calculate_metrics()` - Calculate performance metrics
- [ ] `analyze_risk()` - Analyze risk characteristics
- [ ] `sensitivity_analysis()` - Perform sensitivity analysis
- [ ] `generate_report()` - Generate analysis report

### Model Methods
- [x] `Person.get_total_income_at_age()` - Calculate total income at specific age
- [x] `Person.get_total_expenses_at_age()` - Calculate total expenses at specific age
- [x] `Person.get_essential_goals()` - Get all essential goals
- [x] `Person.get_working_years()` - Calculate years until retirement
- [x] `Person.get_retirement_years()` - Calculate years in retirement
- [x] `Period.contains_age()` - Check if period contains specific age
- [x] `Period.duration()` - Calculate duration of period
- [x] `Event.is_active_at_age()` - Check if event is active at specific age
- [x] `Event.get_effective_amount()` - Calculate inflation-adjusted amount
- [x] `EventManager.add_event()` - Add event to manager
- [x] `EventManager.add_handler()` - Add event handler
- [x] `EventManager.get_events_at_age()` - Get events active at specific age
- [x] `EventManager.get_events_by_type()` - Get events by type
- [x] `EventManager.process_events_at_age()` - Process all events at specific age
- [x] `EventManager.get_cash_flow_at_age()` - Calculate net cash flow at age
- [x] `EventManager.validate_events()` - Validate all events
- [x] `EventManager.get_event_summary()` - Get summary of all events

### Data Methods
- [x] `load_historical_returns()` - Load historical returns from CSV file
- [x] `load_correlation_matrix()` - Load correlation matrix from CSV file
- [x] `load_risk_free_rate()` - Load risk-free rate from JSON file
- [x] `save_historical_returns()` - Save historical returns to CSV file
- [x] `save_correlation_matrix()` - Save correlation matrix to CSV file
- [x] `save_risk_free_rate()` - Save risk-free rate to JSON file
- [x] `generate_sample_data()` - Generate sample market data for testing
- [x] `get_asset_returns()` - Get returns for a specific asset
- [x] `get_mean_returns()` - Calculate mean returns for all assets
- [x] `get_volatilities()` - Calculate volatilities for all assets
- [x] `get_correlation_matrix()` - Calculate correlation matrix for all assets
- [x] `get_annualized_returns()` - Calculate annualized returns for all assets
- [x] `get_annualized_volatilities()` - Calculate annualized volatilities for all assets
- [x] `get_correlation()` - Get correlation between two assets
- [x] `is_positive_definite()` - Check if correlation matrix is positive definite
- [x] `get_cholesky_decomposition()` - Get Cholesky decomposition of correlation matrix
- [x] `get_annualized_rate()` - Get annualized risk-free rate
- [x] `contains_income()` - Check if income falls within bracket
- [x] `calculate_tax()` - Calculate tax for income in bracket
- [x] `get_bracket_for_income()` - Get the tax bracket for a given income level
- [x] `calculate_total_tax()` - Calculate total tax for given income
- [x] `get_marginal_rate()` - Get marginal tax rate for given income
- [x] `get_effective_rate()` - Get effective tax rate for given income
- [x] `calculate_primary_insurance_amount()` - Calculate Primary Insurance Amount (PIA)
- [x] `calculate_benefit_at_age()` - Calculate benefit amount at specific claiming age
- [x] `calculate_medicare_premiums()` - Calculate Medicare premiums based on income level
- [x] `detect_outliers()` - Detect outliers in the data
- [x] `get_outlier_info()` - Get detailed information about outliers
- [x] `check_completeness()` - Check data completeness
- [x] `check_consistency()` - Check data consistency
- [x] `check_distribution()` - Check data distribution for numeric columns
- [x] `check_date_consistency()` - Check date consistency
- [x] `validate_historical_returns()` - Validate historical returns data
- [x] `validate_correlation_matrix()` - Validate correlation matrix
- [x] `validate_tax_brackets()` - Validate tax brackets data
- [x] `validate_social_security_data()` - Validate Social Security data
- [x] `generate_validation_report()` - Generate a human-readable validation report
- [x] `download_historical_returns_from_yahoo()` - Download historical returns from Yahoo Finance
- [x] `download_risk_free_rate_from_fred()` - Download risk-free rate from FRED
- [x] `download_tax_brackets_from_irs()` - Download tax brackets from IRS
- [x] `download_social_security_data_from_ssa()` - Download Social Security data from SSA

*Web-based data download is supported for market, tax, and Social Security data. Local files are used as cache or for user-provided data.*

## Design Patterns Used

### Immutable Data Classes
- All financial data structures are immutable using `@dataclass(frozen=True)`
- Changes create new instances rather than modifying existing ones

### Strategy Pattern
- Different asset classes implement common interface
- Different optimization algorithms implement common interface
- Different tax calculation methods implement common interface

### Factory Pattern
- Asset factory for creating different asset types
- Event factory for creating different event types
- Strategy factory for creating different strategy types

### Observer Pattern
- Event system notifies observers of changes
- Simulation progress updates
- Optimization progress updates

### Template Method Pattern
- Base classes define algorithm structure
- Subclasses implement specific details

## Code Standards

### Type Hints
- All methods must have complete type hints
- Use `typing` module for complex types
- Generic types for reusable components

### Documentation
- All classes and methods must have docstrings
- Use Google or NumPy docstring format
- Include examples in docstrings

### Testing
- All classes must have unit tests
- Test edge cases and error conditions
- Maintain high test coverage

### Error Handling
- Use custom exception classes
- Provide meaningful error messages
- Log errors for debugging

## Last Updated
- Date: 2024-12-19
- Files Modified:
  - `retirement_planner/core/__init__.py` - Core module initialization
  - `retirement_planner/core/exceptions.py` - Exception hierarchy
  - `retirement_planner/core/validation.py` - Validation framework
  - `retirement_planner/core/config.py` - Configuration management
  - `retirement_planner/core/logging.py` - User-friendly logging system
  - `retirement_planner/models/__init__.py` - Models module initialization
  - `retirement_planner/models/person.py` - Person, Income, Expense, Goal models
  - `retirement_planner/models/events.py` - Event-driven modeling foundation
- Classes Added:
  - `RetirementPlannerException`, `ValidationError`, `ConfigurationError`, `DataError`, `SimulationError`, `OptimizationError`, `TaxCalculationError`, `AssetError`, `EventError`, `PortfolioError`
  - `ErrorContext` - Error context information
  - `Validator`, `ValidationRule`, `ValidationResult`, `FieldValidator`, `BusinessRuleValidator`
  - `RequiredRule`, `TypeRule`, `RangeRule`, `AgeRule`, `PercentageRule`, `RegexRule`, `ChoiceRule`
  - `LogLevel`, `LogMessage`, `FinancialFormatter`
  - `RetirementPlannerLogger`, `UserLogger`, `ProgressLogger`, `FinancialLogger`
  - `Person`, `Income`, `Expense`, `Goal` - Person profile and financial components
  - `Event`, `EventManager`, `EventType`, `Period` - Event-driven modeling foundation
- Methods Added:
  - Validation framework methods: `validate()`, `add_rule()`, `add_field_validator()`
  - Logging methods: `log()`, `log_progress()`, `log_financial_calculation()`, `complete_operation()`
  - Person methods: `get_total_income_at_age()`, `get_total_expenses_at_age()`, `get_essential_goals()`
  - Event methods: `is_active_at_age()`, `get_effective_amount()`, `process_events_at_age()`, `get_cash_flow_at_age()`
- Status: Phase 1 Complete - Core foundation, validation, configuration, logging, and base data models implemented with 100% test coverage

### Phase 1 Complete:
- Core validation framework working
- Configuration system operational
- Logging system functional with user-friendly messages and progress tracking
- Person and Event models functional

### Phase 1.4 Complete:
- Portfolio model functional