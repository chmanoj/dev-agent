# Code Quality Standards

## MANDATORY Tools & Configuration

### Ruff Configuration (REQUIRED)
All code MUST pass comprehensive Ruff checks with these rule categories:

```toml
[tool.ruff.lint]
select = [
    "E",    # pycodestyle errors
    "W",    # pycodestyle warnings  
    "F",    # pyflakes
    "I",    # isort (import sorting)
    "B",    # flake8-bugbear
    "C4",   # flake8-comprehensions
    "UP",   # pyupgrade (modern Python syntax)
    "RUF",  # ruff-specific rules
    "N",    # pep8-naming
    "S",    # flake8-bandit (security)
    "T20",  # flake8-print (no print statements)
    "PT",   # flake8-pytest-style
    "Q",    # flake8-quotes
    "SIM",  # flake8-simplify
    "TID",  # flake8-tidy-imports
    "TCH",  # flake8-type-checking
    "ARG",  # flake8-unused-arguments
    "PTH",  # flake8-use-pathlib
    "ERA",  # eradicate (commented code)
    "PL",   # pylint
    "PERF", # perflint (performance)
    "FURB", # refurb (modernization)
    "LOG",  # flake8-logging
]
```

### mypy Configuration (STRICT MODE REQUIRED)
```toml
[tool.mypy]
strict = true
python_version = "3.10"
warn_return_any = true
warn_unused_configs = true
disallow_any_generics = true
disallow_subclassing_any = true
disallow_untyped_calls = true
disallow_untyped_defs = true
disallow_incomplete_defs = true
check_untyped_defs = true
disallow_untyped_decorators = true
no_implicit_optional = true
warn_redundant_casts = true
warn_unused_ignores = true
warn_no_return = true
warn_unreachable = true
strict_equality = true
show_error_codes = true
pretty = true
enable_error_code = ["ignore-without-code", "redundant-expr", "truthy-bool"]
```

## Code Standards

### Type Annotations (MANDATORY)
- ALL functions MUST have type annotations for parameters and return values
- Use modern typing syntax: `list[str]` not `List[str]`
- Use `from __future__ import annotations` for forward references
- Generic types MUST be properly parameterized

### Error Handling
- Use specific exception types, not bare `except:`
- Custom exceptions MUST inherit from appropriate base classes
- Log errors with appropriate levels and context
- Use `raise ... from ...` for exception chaining

### Security Standards
- NO hardcoded secrets or credentials (especially Azure OpenAI API keys)
- Use environment variables for ALL configuration (Azure endpoint, API keys, deployments)
- Use Pydantic SecretStr for API keys (never logged or serialized)
- Validate all external inputs (user prompts, file paths, API responses)
- Use secure defaults for all configurations
- Follow OWASP guidelines for web components
- Implement audit logging for all Azure OpenAI API calls
- Never include API keys in error messages or logs
- Rotate Azure OpenAI keys regularly

### Performance Standards
- Use pathlib instead of os.path
- Prefer list/dict comprehensions over loops where appropriate
- Use f-strings for string formatting
- Avoid unnecessary object creation in loops
- Use appropriate data structures (sets for membership tests, etc.)

### Import Organization
- Standard library imports first
- Third-party imports second  
- Local imports last
- Use absolute imports
- Group imports logically
- Remove unused imports

## Testing Requirements

### Coverage Standards
- MINIMUM 90% test coverage required
- Critical paths MUST have 100% coverage
- All public APIs MUST be tested
- Integration tests for workflow phases

### Test Structure
- Use pytest fixtures for setup/teardown
- Parametrize tests for multiple scenarios
- Use descriptive test names
- Group related tests in classes
- Mock external dependencies (ESPECIALLY Azure OpenAI API calls)
- Use pytest-asyncio for async test functions
- Mock Azure OpenAI responses with realistic data
- Test retry logic and error handling
- Test token counting accuracy

### Test Quality
- Tests MUST be deterministic (mock all Azure OpenAI API calls)
- No test dependencies on external services (never call real Azure OpenAI in tests)
- Fast unit tests (<1s each)
- Separate slow integration tests (optional Azure OpenAI integration tests with real API)
- Use environment variable flags for integration tests (AZURE_OPENAI_INTEGRATION_TESTS=true)
- Mock Azure OpenAI streaming responses
- Test cost tracking and token counting

## Documentation Standards

### Docstrings (REQUIRED)
- ALL public functions/classes MUST have docstrings
- Use Google-style docstrings
- Include parameter types and descriptions
- Include return value descriptions
- Include example usage for complex functions

### Code Comments
- Explain WHY, not WHAT
- Update comments when code changes
- Remove commented-out code
- Use TODO comments sparingly with issue references

## Pre-commit Hooks (ENFORCED)
These hooks MUST pass before any commit:
- Ruff formatting and linting
- mypy type checking
- pytest test execution
- YAML/JSON/TOML validation
- Trailing whitespace removal
- Large file detection

## CI/CD Requirements
- ALL checks MUST pass on Python 3.10, 3.11, 3.12, 3.13
- Security scanning via Ruff
- Dependency vulnerability scanning
- Code coverage reporting
- Automated quality gates

## Modern Python Practices (ENFORCED)
- Use dataclasses or Pydantic models for data structures
- Use Enum for constants and state values
- Use pathlib for file operations
- Use context managers for resource management
- Use async/await for I/O operations where appropriate
- Follow PEP 8 naming conventions strictly