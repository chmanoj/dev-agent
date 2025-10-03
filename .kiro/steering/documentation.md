# Documentation Standards

## MANDATORY Documentation Requirements

### Documentation Stack (REQUIRED)
- **MkDocs**: Static site generator for documentation
- **mkdocstrings**: Automatic API documentation from docstrings
- **Material Theme**: Modern, responsive documentation theme
- **Python Markdown Extensions**: Enhanced markdown features

### Documentation Structure (ENFORCED)
```
docs/
├── index.md              # Project overview and quick start
├── installation.md       # Installation and setup guide
├── configuration/       # Configuration guides (NEW)
│   ├── azure-openai.md  # Azure OpenAI setup (REQUIRED)
│   ├── environment.md   # Environment variables
│   └── security.md      # Security best practices
├── usage/               # User guides
│   ├── cli.md           # CLI usage and commands
│   ├── workflow.md      # Four-phase workflow guide
│   └── cost-management.md # Token usage and cost tracking (NEW)
├── api/                 # API documentation (auto-generated)
│   ├── cli.md           # CLI module docs
│   ├── llm.md           # LLM integration docs (NEW)
│   ├── models.md        # Data models
│   ├── workflow.md      # Workflow components
│   └── analysis.md      # Analysis components
├── development/         # Developer documentation
│   ├── contributing.md  # Contribution guidelines
│   ├── architecture.md  # System architecture
│   ├── llm-integration.md # LLM integration guide (NEW)
│   ├── testing.md       # Testing guidelines
│   └── deployment.md    # Deployment instructions
└── examples/            # Usage examples and tutorials
    ├── basic-usage.md   # Basic workflow examples
    ├── advanced.md      # Advanced usage patterns
    └── azure-setup.md   # Azure OpenAI setup examples (NEW)
```

### Docstring Standards (MANDATORY)
All public functions, classes, and modules MUST have Google-style docstrings:

```python
def process_codebase(project_path: str, config: Config) -> AnalysisResult:
    """Analyze a codebase and generate comprehensive analysis.
    
    This function performs deep analysis of a Python codebase including
    AST parsing, dependency analysis, and pattern detection.
    
    Args:
        project_path: Absolute path to the project directory
        config: Configuration object with analysis settings
        
    Returns:
        AnalysisResult containing all analysis data and metrics
        
    Raises:
        ProjectNotFoundError: If project_path doesn't exist
        AnalysisError: If analysis fails due to code issues
        
    Example:
        ```python
        config = Config(include_tests=True)
        result = process_codebase("/path/to/project", config)
        print(f"Found {len(result.functions)} functions")
        ```
    """
```

### MkDocs Configuration (REQUIRED)
- **Theme**: Material with custom colors matching project branding
- **Plugins**: mkdocstrings, search, git-revision-date-localized
- **Extensions**: Admonitions, code highlighting, tables, footnotes
- **Navigation**: Logical structure with clear hierarchy

### Documentation Deployment
- **Local Development**: `mkdocs serve` for live preview
- **Production**: GitHub Pages or similar static hosting
- **Auto-deployment**: CI/CD pipeline builds and deploys docs

## Content Standards (ENFORCED)

### Writing Style
- **Clear and Concise**: Use simple, direct language
- **User-Focused**: Write from the user's perspective
- **Action-Oriented**: Use active voice and imperative mood
- **Consistent Terminology**: Use the same terms throughout

### Code Examples (MANDATORY)
- **All examples MUST be tested** and functional
- **Include complete examples** with imports and setup
- **Show expected output** where relevant
- **Use realistic data** not foo/bar placeholders
- **NEVER include real API keys** - use placeholder values like `your-api-key-here`
- **Show environment variable setup** for Azure OpenAI configuration
- **Include cost estimates** for example operations (token usage)
- **Mock Azure OpenAI calls** in example tests

### API Documentation (AUTO-GENERATED)
- **All public APIs** automatically documented via mkdocstrings
- **Type hints** displayed in documentation
- **Source code links** for easy navigation
- **Inheritance diagrams** for complex class hierarchies

### Screenshots and Diagrams
- **CLI screenshots** showing actual usage
- **Architecture diagrams** using Mermaid or similar
- **Workflow diagrams** for the four-phase process
- **Keep images up-to-date** with code changes

## Development Workflow (MANDATORY)

### Documentation Updates
- **Update docs WITH code changes** - never separate
- **Preview locally** before committing: `mkdocs serve`
- **Test all examples** in documentation
- **Check for broken links** and references

### Review Process
- **Documentation changes** require review like code
- **API changes** MUST update corresponding docs
- **New features** MUST include documentation
- **Breaking changes** MUST update migration guides

### Quality Checks
- **Spell check** all documentation
- **Link validation** in CI pipeline
- **Example testing** as part of test suite
- **Documentation coverage** tracking

## Commands and Automation

### Development Commands
```bash
# Install documentation dependencies
uv sync --group docs

# Serve documentation locally (live reload)
uv run mkdocs serve

# Build documentation for production
uv run mkdocs build

# Deploy to GitHub Pages
uv run mkdocs gh-deploy

# Test documentation examples
python scripts/test_docs_examples.py

# Validate documentation links
uv run mkdocs build --strict
```

### CI/CD Integration
- **Build docs** on every PR
- **Deploy docs** on main branch changes
- **Test examples** in documentation
- **Check for broken links**

## Documentation Dependencies (REQUIRED)
Add to pyproject.toml:
```toml
[project.optional-dependencies]
docs = [
    "mkdocs>=1.5.0",
    "mkdocs-material>=9.4.0",
    "mkdocstrings[python]>=0.24.0",
    "mkdocs-git-revision-date-localized-plugin>=1.2.0",
    "pymdown-extensions>=10.0.0",
]
```

## Enforcement Rules

### Pre-commit Hooks
- **Spell check** documentation files
- **Link validation** for internal links
- **Example syntax** validation

### CI/CD Checks
- **Documentation builds** without errors
- **All examples execute** successfully
- **API documentation** is complete
- **No broken links** in generated docs

### Review Requirements
- **Documentation PRs** require approval
- **API changes** need doc updates
- **New features** need usage examples
- **Breaking changes** need migration docs

Remember: Documentation is NOT optional - it's a core requirement for maintainable software.