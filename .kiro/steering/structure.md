# Project Structure

## Package Organization

The `dev_agent/` package follows a modular architecture with clear separation of concerns:

```
dev_agent/
├── __init__.py              # Package entry point with version
├── cli/                     # Command-line interface
│   ├── main.py             # Typer CLI application entry point
│   ├── interactive_cli.py  # Chat-based interactive interface
│   └── session_manager.py  # Session state management
├── interfaces/             # Abstract base classes and protocols
│   ├── workflow_interface.py
│   ├── analysis_interface.py
│   └── ...
├── models/                 # Pydantic data models
│   ├── enums.py           # Core enums (PhaseType, TaskStatus, etc.)
│   ├── project_state.py   # Project state data structures
│   ├── documents.py       # Document models
│   └── ...
├── workflow/              # Workflow orchestration
│   ├── workflow_manager.py
│   ├── phase_manager.py
│   └── ...
├── indexing/              # Code analysis and indexing
│   ├── indexing_engine.py
│   ├── tree_sitter_parser.py
│   ├── vector_database.py
│   └── code_chunker.py
├── generation/            # Content generation
│   ├── specification_generator.py
│   ├── design_generator.py
│   ├── task_generator.py
│   └── python_code_generator.py
├── analysis/              # Codebase analysis
│   └── codebase_analyzer.py
├── state/                 # State management
│   └── state_manager.py
├── config/                # Configuration management
│   ├── config_manager.py
│   └── logging_config.py
└── errors/                # Error handling
    ├── exceptions.py
    ├── error_handler.py
    └── recovery.py
```

## Project Root Structure

```
project-root/
├── dev_agent/              # Main package
├── tests/                  # Test suite
│   ├── sample_files/      # Test fixtures
│   └── test_*.py          # Test modules
├── examples/              # Usage examples and demos
├── scripts/               # Utility scripts
├── .dev_agent/           # Project state directory (created by tool)
│   ├── documents/        # Generated documents
│   └── state.json        # Project state
├── pyproject.toml        # Primary configuration
├── requirements.txt      # Legacy pip requirements
├── setup.py             # Legacy setup script
└── README.md            # Documentation
```

## Architecture Patterns

### Interface-Based Design
- All major components implement abstract interfaces from `interfaces/`
- Enables dependency injection and testing
- Clear contracts between components

### Enum-Driven State Management
- Core enums in `models/enums.py` define system states
- `PhaseType`: INDEXING, SPECIFICATION, DESIGN, IMPLEMENTATION
- `TaskStatus`: NOT_STARTED, IN_PROGRESS, COMPLETED, FAILED, BLOCKED
- `PhaseStatus`: NOT_STARTED, IN_PROGRESS, COMPLETED, FAILED, REQUIRES_APPROVAL

### Pydantic Models
- All data structures use Pydantic for validation
- Consistent serialization/deserialization
- Type safety and runtime validation

### Session-Based Workflow
- Persistent state across CLI sessions
- User approval required between phases
- State stored in `.dev_agent/` directory

## Naming Conventions

### Files and Modules
- Snake_case for all Python files
- Descriptive names indicating purpose
- Interface files end with `_interface.py`
- Test files prefixed with `test_`

### Classes
- PascalCase for class names
- Interface classes prefixed with `I` (e.g., `IWorkflowManager`)
- Exception classes suffixed with `Error` or `Exception`

### Functions and Variables
- Snake_case for functions and variables
- Private methods prefixed with `_`
- Constants in UPPER_CASE

### Project State Directory
- `.dev_agent/` created in project root
- Contains `state.json` and `documents/` subdirectory
- Managed automatically by the system