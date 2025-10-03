# Modern Python Enforcement

## CRITICAL: Always Follow These Standards

### Package Management (MANDATORY)
- **ALWAYS use `uv`** for dependency management - never use pip directly for development
- **ALWAYS run `uv sync --dev`** to install dependencies
- **NEVER edit uv.lock manually** - it's auto-generated
- **Keep requirements.txt in sync** with pyproject.toml for legacy compatibility only

### Code Quality (NON-NEGOTIABLE)
- **ALL code MUST pass Ruff with comprehensive rules** (security, performance, complexity)
- **ALL code MUST pass mypy in strict mode** with type annotations
- **ALL commits MUST pass pre-commit hooks**
- **90%+ test coverage REQUIRED**

### Modern Python Syntax (ENFORCED)
```python
# ✅ CORRECT - Modern Python 3.10+
from __future__ import annotations

def process_items(items: list[str]) -> dict[str, int]:
    """Process items and return counts."""
    return {item: len(item) for item in items}

# ❌ WRONG - Old syntax
from typing import List, Dict

def process_items(items: List[str]) -> Dict[str, int]:
    return dict((item, len(item)) for item in items)
```

### Dependency Versions (CURRENT MINIMUMS)
- Python: >=3.10 (NO older versions)
- **Azure OpenAI**: openai >=1.50.0 (REQUIRED)
- **Token Management**: tiktoken >=0.6.0 (REQUIRED)
- **Retry Logic**: tenacity >=8.2.0 (REQUIRED)
- Typer: >=0.15.0
- Rich: >=13.9.0  
- Pydantic: >=2.10.0 (v2 REQUIRED)
- FAISS-CPU: >=1.9.0
- FastAPI: >=0.115.0
- NumPy: >=2.0.0 (latest major)
- Ruff: >=0.8.0
- mypy: >=1.13.0
- pytest: >=8.3.0

### Development Workflow (MANDATORY)
```bash
# Setup (ALWAYS)
uv sync --dev
uv run pre-commit install

# Before every commit (REQUIRED)
uv run ruff format dev_agent tests
uv run ruff check dev_agent tests
uv run mypy dev_agent
uv run pytest --cov=dev_agent

# Or use shortcuts
make quality  # run all quality checks
make test     # run tests with coverage
make ci       # run all CI checks locally
```

### Architecture Patterns (REQUIRED)
- **Use Pydantic models** for all data structures (including LLM configs)
- **Use Enums** for constants and state values (PhaseType, LLMProvider, etc.)
- **Use pathlib** instead of os.path
- **Use f-strings** for string formatting
- **Use type annotations** on ALL functions
- **Use async/await** for ALL I/O operations (especially Azure OpenAI API calls)
- **Use context managers** for resource management
- **Use SecretStr** for API keys and sensitive data (Pydantic)
- **Use tenacity** for retry logic with exponential backoff
- **Use tiktoken** for accurate token counting before API calls

### Error Handling (STRICT)
```python
# ✅ CORRECT
try:
    result = risky_operation()
except SpecificError as e:
    logger.error(f"Operation failed: {e}")
    raise ProcessingError("Failed to process") from e

# ❌ WRONG
try:
    result = risky_operation()
except:
    print("Something went wrong")
    raise
```

### Security (NON-NEGOTIABLE)
- **NO hardcoded secrets** - use environment variables for Azure OpenAI credentials
- **NEVER log API keys** - use Pydantic SecretStr for sensitive data
- **Validate ALL external inputs** - especially user prompts and file paths
- **Use secure defaults** - minimum required permissions
- **Follow OWASP guidelines** - especially for API key management
- **Pass Ruff security checks (S rules)** - mandatory for all code
- **Azure OpenAI only** - no data sent to third-party services
- **Audit logging** - log API calls without sensitive data

### Testing (MANDATORY)
- **90%+ coverage required**
- **All public APIs must be tested**
- **Use pytest fixtures and parametrize**
- **Mock external dependencies**
- **Deterministic tests only**

## Enforcement Mechanisms
1. **Pre-commit hooks** prevent bad commits
2. **CI/CD pipeline** blocks merges that fail quality checks
3. **Ruff with comprehensive rules** catches issues early
4. **mypy strict mode** enforces type safety
5. **Coverage reporting** ensures adequate testing

## Quick Reference Commands
```bash
# Development setup
make dev

# Quality checks (must pass)
make quality

# Testing (must pass)
make test

# Full CI simulation
make ci

# Clean temporary files
make clean

# Update dependencies
uv lock --upgrade
```

## Project Cleanliness (MANDATORY)
- **NO legacy files**: setup.py, MANIFEST.in, etc.
- **NO build artifacts**: dist/, build/, *.egg-info/
- **NO temporary files**: coverage.xml, htmlcov/, demo_project/
- **Use `make clean`** to remove temporary files
- **Keep examples/** - they demonstrate system capabilities

Remember: These are not suggestions - they are REQUIREMENTS for all code in this project.