# Cursor Rules for Retirement Planner Development

## Communication Style
- Be concise. Avoid verbose explanations unless specifically requested.
- Question user decisions if they seem suboptimal or unclear.
- Provide direct, actionable responses.

## Testing Philosophy
- Write tests based on semantic behavior, not implementation details.
- Avoid mocks unless absolutely necessary for external dependencies.
- Focus on testing what the code should do, not how it does it.
- Ensure high test coverage through natural test scenarios.

## Code Quality
- All code must be class-based with no duplication.
- Use comprehensive type hints throughout.
- Follow immutable data patterns for financial structures.
- Implement proper error handling with custom exceptions.

## Documentation
- Update all design files (CODE_INVENTORY.md, DEVELOPMENT_PLAN.md, PACKAGE_STRUCTURE.md, REQUIREMENTS.md) when implementing features.
- Mark completed items with ✅ status indicators.
- Keep documentation consistent across all files.

## Development Process
- Follow the phased development plan strictly.
- Implement core foundation before building dependent modules.
- Always run tests after changes to verify functionality.
- Update code inventory to track all classes, methods, and design patterns.

## Architecture Principles
- Modular design with clear separation of concerns.
- Dependency injection for testability.
- Configuration-driven parameters via YAML/JSON.
- Event-driven modeling for temporal scenarios.
- User-friendly logging with clear financial explanations.

## Error Handling
- Use custom exception hierarchy for different error types.
- Provide meaningful error messages with context.
- Implement graceful degradation where possible.

## Performance Requirements
- Support 10,000+ Monte Carlo scenarios with sub-second execution.
- Use efficient data structures and algorithms.
- Implement caching for expensive calculations.