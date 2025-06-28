# Code Inventory

## Phase 1: Core Foundation ✅
### Core Exceptions and Validation
- **File**: `retirement_planner/core/exceptions.py`
  - `ErrorContext`: Context information for error reporting.
  - `RetirementPlannerException`: Base exception for all planner errors.
  - `ValidationError`: Raised for input validation failures.
  - `ConfigurationError`: Raised for configuration errors.
  - `DataError`: Raised for data loading/processing errors.
  - `SimulationError`: Raised for simulation failures.
  - `OptimizationError`: Raised for optimization failures.
  - `TaxCalculationError`: Raised for tax calculation errors.
  - `AssetError`: Raised for asset-related errors.
  - `EventError`: Raised for event processing errors.
  - `PortfolioError`: Raised for portfolio operation errors.
  - Convenience functions: `create_validation_error`, `create_configuration_error`, `create_data_error` (helpers for error creation with context).

### Core Validation
- **File**: `retirement_planner/core/validation.py`
  - `ValidationResult`: Result of a validation operation (validity, errors, warnings).
  - `ValidationRule`: Abstract base for all validation rules.
  - `FieldValidator`: Validator for a single field with multiple rules.
  - `BusinessRuleValidator`: Validator for business rules spanning multiple fields.
  - `Validator`: Main orchestrator for field and business rule validation.
  - `RequiredRule`, `TypeRule`, `RangeRule`, `AgeRule`, `PercentageRule`, `RegexRule`, `ChoiceRule`: Concrete validation rules for common constraints.

### Logging System
- **File**: `retirement_planner/core/logging.py`
  - `LogLevel`: Enum for user-friendly log levels.
  - `LogMessage`: User-friendly log message with context.
  - `FinancialFormatter`: Formats financial data (currency, percent, age, allocation).
  - `UserLogger`: Logs clear, readable messages for users.
  - `ProgressLogger`: Logs progress for long-running operations.
  - `FinancialLogger`: Explains financial calculations in plain English.
  - `RetirementPlannerLogger`: Main logging interface, aggregates all logging features.

### Configuration Management
- **File**: `retirement_planner/core/config.py`
  - `BaseConfig`: Base class for configuration objects.
  - `ConfigLoader`: Loads and validates configuration from YAML/JSON and environment.
  - `AppConfig`: Example application config dataclass.
  - `get_default_schema`: Returns default config schema.

### Utilities
- **File**: `retirement_planner/utils/file_utils.py`
  - `FileInfo`: Information about a file.
  - `FileUtils`: General file I/O utilities (read, write, backup, info).
  - `YamlLoader`: YAML file loading, saving, validation, merging.
  - `JsonLoader`: JSON file loading, saving, validation, merging, pretty-printing.
  - `ConfigFileManager`: Configuration file management and caching.

- **File**: `retirement_planner/utils/math_utils.py`
  - `FinancialMetrics`: Container for financial calculation results.
  - `MathUtils`: Core mathematical utilities (compound interest, PV, FV, annuity, inflation, real return, rounding, validation).
  - `StatisticalUtils`: Statistical calculations (mean, median, std, variance, percentiles, correlation, skewness, kurtosis).
  - `RiskMetrics`: Risk measurement (VaR, CVaR, max drawdown, Sharpe, Sortino, Calmar ratios).
  - `PortfolioMath`: Portfolio-specific math (returns, volatility, rebalancing, geometric mean).

- **File**: `retirement_planner/utils/date_utils.py`
  - `AgePeriod`: Represents a period defined by ages.
  - `DatePeriod`: Represents a period defined by dates.
  - `DateUtils`: Date and time period calculation utilities (age, years between, add years, retirement/life expectancy dates, working/retirement periods, formatting, leap year, days in year).
  - `AgeCalculator`: Age-based calculations (years to retirement, retirement years, total planning years, working/retirement age checks, age periods, social security eligibility, RMD age, age formatting, age at date, dates for age range).

## Phase 2: Data Models & Data Layer ✅
### Person Model
- **File**: `retirement_planner/models/person.py`
  - `Person`: Core person profile (age, retirement age, life expectancy, goals).
  - `Goal`: Retirement planning goal (priority, type, target amount).

### Event System
- **File**: `retirement_planner/models/events.py`
  - `Event`: Base event class for temporal modeling (age-based timing, inflation adjustment).
  - `EventType`: Enumeration of event types (income, expense, asset, custom, liability, tax, benefit, lifestyle, health, family, economic).
  - `EventManager`: Manages event processing, resolution, and cash flow calculations.
  - `Period`: Time period with age-based boundaries for event scheduling.

### Data Structures
- **File**: `retirement_planner/data/tax_data.py`
  - `TaxDataLoader`: Loads tax data from config files.
  - `TaxBrackets`: Complete set of tax brackets for a filing status and year.
  - `SocialSecurityData`: Social Security parameters and benefit calculations.

- **File**: `retirement_planner/data/market_data.py`
  - `MarketDataLoader`: Loads market data from various sources.
  - `HistoricalReturns`: Historical returns data for assets.
  - `CorrelationMatrix`: Correlation matrix for asset returns.
  - `RiskFreeRate`: Risk-free rate data with term structure support.

- **File**: `retirement_planner/data/validators.py`
  - `DataValidator`: Main data validation orchestrator.
  - `OutlierDetector`: Detects outliers in data using statistical methods.
  - `DataQualityChecker`: Checks data quality and consistency.
  - `ValidationResult`: Result of data validation operations.

## Phase 3: Asset Classes ✅
### Base Asset System
- **File**: `retirement_planner/assets/base.py`
  - `Asset`: Base asset class (returns, volatility, correlation, config-driven).
  - `AssetFactory`: Factory for creating asset instances with configuration.
  - `AssetAllocation`: Asset allocation strategy and rebalancing functionality.

### Equity Assets
- **File**: `retirement_planner/assets/equities.py`
  - `Equity`: Single class supporting all stock types (market cap, geography, public/private, config-driven).

### Bond Assets
- **File**: `retirement_planner/assets/bonds.py`
  - `Bond`: Single class supporting all bond types (tax treatment, duration, credit quality, config-driven).

### Cash Assets
- **File**: `retirement_planner/assets/cash.py`
  - `CashEquivalent`: Single class supporting all cash equivalents (interest rate, liquidity, FDIC insurance, config-driven).

### Alternative Assets
- **File**: `retirement_planner/assets/alternatives.py`
  - `RealEstate`: Real estate investments (property type, location, leverage, config-driven).
  - `Commodity`: Commodities and precious metals (commodity type, storage costs, config-driven).
  - `CustomAsset`: User-defined custom assets (flexible configuration for any investment type).

## Phase 4: Tax Classes ✅
### Federal and State Tax System
- **File**: `retirement_planner/tax/federal.py`
  - `FederalTax`: Abstract base for federal tax logic.
  - `USFederalTax`: Loads brackets, deductions, and rates from YAML config.
  - `SocialSecurity`: Social Security benefit and Medicare calculations (config-driven).
  - `RetirementAccountTax`: RMD and contribution rules (config-driven).

- **File**: `retirement_planner/tax/state.py`
  - `StateTax`: Abstract base for state tax logic.
  - `CaliforniaTax`: California-specific logic, config-driven.

## Phase 5: Portfolio Management
### Portfolio Management
- **File**: `retirement_planner/portfolio/portfolio.py`
- **Classes**: `Portfolio`, `AssetAllocation`, `RebalancingStrategy`
- **Status**: PLANNED

### Risk Management
- **File**: `retirement_planner/portfolio/risk.py`
- **Classes**: `RiskMetrics`, `RiskManager`, `RiskCalculator`
- **Status**: PLANNED

## Phase 6: Monte Carlo Simulation
### Simulation Engine
- **File**: `retirement_planner/simulation/engine.py`
- **Classes**: `MonteCarloEngine`, `ScenarioGenerator`, `MarketSimulator`
- **Status**: PLANNED

### Market Modeling
- **File**: `retirement_planner/simulation/market.py`
- **Classes**: `MarketModel`, `ReturnSimulator`, `CorrelationModel`
- **Status**: PLANNED

## Phase 7: Analysis Engine
### Retirement Analysis
- **File**: `retirement_planner/analysis/retirement.py`
- **Classes**: `RetirementAnalyzer`, `GoalTracker`, `SuccessCalculator`
- **Status**: PLANNED

### Withdrawal Strategies
- **File**: `retirement_planner/analysis/withdrawal.py`
- **Classes**: `WithdrawalStrategy`, `WithdrawalOptimizer`
- **Status**: PLANNED

## Phase 8: User Interface
### Command Line Interface
- **File**: `retirement_planner/cli/main.py`
- **Classes**: `CLI`, `CommandHandler`, `OutputFormatter`
- **Status**: PLANNED

### Report Generation
- **File**: `retirement_planner/reports/generator.py`
- **Classes**: `ReportGenerator`, `ChartCreator`, `DataExporter`
- **Status**: PLANNED

## Testing Coverage
### Unit Tests
- **Core Tests**: `tests/core/` - Complete coverage
- **Model Tests**: `tests/models/` - Complete coverage
- **Asset Tests**: `tests/assets/` - Complete coverage (158 tests)
- **Tax Tests**: `tests/tax/` - Complete coverage (7 tests)
- **Utility Tests**: `tests/utils/` - Complete coverage

### Integration Tests
- **Configuration Tests**: `examples/50_year_old_retirement_scenario/tests/` - Complete coverage
- **Asset Configuration Tests**: `examples/50_year_old_retirement_scenario/tests/assets_test.py` - Complete coverage

## Documentation
### Design Documents
- **Development Plan**: `DEVELOPMENT_PLAN.md` - Updated with Phase 4 completion
- **Code Inventory**: `CODE_INVENTORY.md` - Updated with all completed phases
- **Package Structure**: `PACKAGE_STRUCTURE.md` - Current structure documented
- **Requirements**: `REQUIREMENTS.md` - Comprehensive requirements specification

### Example Configurations
- **Person Profile**: `examples/50_year_old_retirement_scenario/person_profile.yaml` - Updated for new design
- **Asset Configuration**: `examples/50_year_old_retirement_scenario/assets.yaml` - New metadata-based structure
- **Events Configuration**: `examples/50_year_old_retirement_scenario/events.yaml` - Compatible with current design
- **Market Data**: `examples/50_year_old_retirement_scenario/market_data.yaml` - Compatible with current design
- **Simulation Config**: `examples/50_year_old_retirement_scenario/simulation_config.yaml` - Compatible with current design