# Design Document

## Overview

This design document outlines the technical approach for auditing, cleaning up, and enhancing the dev-agent library. The design focuses on ensuring core functionality works correctly, improving user experience for both new and existing projects, enhancing the CLI interface, and updating documentation.

The design follows the existing architecture patterns in dev-agent while introducing improvements to make the tool more user-friendly, maintainable, and production-ready.

## Architecture

### High-Level Architecture

The dev-agent library follows a modular architecture with clear separation of concerns:

```
┌─────────────────────────────────────────────────────────────┐
│                         CLI Layer                            │
│  (Typer + Rich for interactive commands and display)        │
└────────────────┬────────────────────────────────────────────┘
                 │
┌────────────────▼────────────────────────────────────────────┐
│                    Workflow Manager                          │
│  (Orchestrates four-phase workflow with state management)   │
└────┬──────────┬──────────┬──────────┬──────────────────────┘
     │          │          │          │
┌────▼────┐ ┌──▼─────┐ ┌──▼──────┐ ┌▼──────────────┐
│Indexing │ │Spec    │ │Design   │ │Implementation │
│Phase    │ │Phase   │ │Phase    │ │Phase          │
└────┬────┘ └──┬─────┘ └──┬──────┘ └┬──────────────┘
     │          │          │          │
┌────▼──────────▼──────────▼──────────▼──────────────────────┐
│              Azure OpenAI Integration Layer                  │
│  (GPT-4 for generation, text-embedding-ada-002 for vectors) │
└─────────────────────────────────────────────────────────────┘
```

### Design Principles

1. **Backward Compatibility**: All changes must maintain compatibility with existing projects
2. **Progressive Enhancement**: New features should enhance but not replace existing functionality
3. **User-Centric Design**: Every change should improve the user experience
4. **Fail-Safe Operations**: All operations should be reversible or have clear rollback mechanisms
5. **Performance First**: Optimizations should not compromise functionality

## Components and Interfaces

### 1. Repository Audit System

**Purpose**: Verify that all core features are functional and identify issues.

**Component Structure**:
```python
# dev_agent/audit/audit_engine.py
class AuditEngine:
    """Comprehensive audit system for dev-agent functionality."""
    
    def audit_indexing_phase(self, test_project_path: str) -> AuditResult
    def audit_specification_phase(self, test_project_path: str) -> AuditResult
    def audit_design_phase(self, test_project_path: str) -> AuditResult
    def audit_implementation_phase(self, test_project_path: str) -> AuditResult
    def audit_state_management(self, test_project_path: str) -> AuditResult
    def audit_azure_openai_integration(self) -> AuditResult
    def audit_cost_tracking(self) -> AuditResult
    def generate_audit_report(self) -> AuditReport

@dataclass
class AuditResult:
    component: str
    status: Literal["pass", "fail", "warning"]
    message: str
    details: dict
    recommendations: list[str]

@dataclass
class AuditReport:
    timestamp: datetime
    results: list[AuditResult]
    overall_status: Literal["pass", "fail", "warning"]
    summary: str
```

**Integration Points**:
- CLI command: `dev-agent audit` to run comprehensive audit
- CI/CD integration for automated testing
- Generates markdown report in `.dev_agent/audit_report.md`

### 2. Repository Cleanup System

**Purpose**: Identify and remove unnecessary files while maintaining project integrity.

**Component Structure**:
```python
# dev_agent/cleanup/cleanup_manager.py
class CleanupManager:
    """Manages repository cleanup operations."""
    
    def scan_for_cleanup_candidates(self) -> CleanupPlan
    def identify_temporary_files(self) -> list[Path]
    def identify_generated_files(self) -> list[Path]
    def identify_obsolete_examples(self) -> list[Path]
    def identify_unused_dependencies(self) -> list[str]
    def execute_cleanup(self, plan: CleanupPlan, dry_run: bool = True) -> CleanupResult
    def generate_cleanup_report(self, result: CleanupResult) -> str

@dataclass
class CleanupPlan:
    files_to_remove: list[Path]
    directories_to_remove: list[Path]
    dependencies_to_remove: list[str]
    files_to_move: dict[Path, Path]
    total_size_reduction: int
    
@dataclass
class CleanupResult:
    removed_files: list[Path]
    removed_directories: list[Path]
    moved_files: dict[Path, Path]
    errors: list[str]
    size_reduction: int
```

**Cleanup Categories**:
1. **Temporary Files**: `.coverage`, `*.pyc`, `__pycache__/`, cache directories
2. **Generated Files**: `site/`, `TASK_*_COMPLETION_SUMMARY.md`, build artifacts
3. **Development Artifacts**: `.development/` contents (move to docs or remove)
4. **Obsolete Examples**: Non-functional or outdated example files
5. **Unused Dependencies**: Dependencies not imported in codebase

**Safety Mechanisms**:
- Dry-run mode by default
- Backup creation before deletion
- Whitelist of protected files/directories
- User confirmation for each category

### 3. Enhanced CLI System

**Purpose**: Improve user experience with better commands, help, and feedback.

**Component Structure**:
```python
# dev_agent/cli/enhanced_commands.py
class EnhancedCLICommands:
    """Enhanced CLI commands with improved UX."""
    
    def setup_wizard(self) -> bool
    def status_command(self, detailed: bool = False) -> None
    def cost_report_command(self, phase: PhaseType | None = None) -> None
    def help_command(self, topic: str | None = None) -> None
    def validate_environment(self) -> ValidationResult

# dev_agent/cli/progress_display.py
class ProgressDisplay:
    """Rich progress display for long-running operations."""
    
    def show_indexing_progress(self, current: int, total: int) -> None
    def show_streaming_response(self, stream: AsyncIterator[str]) -> str
    def show_phase_summary(self, phase: PhaseType, result: PhaseResult) -> None
    def show_cost_summary(self, report: CostReport) -> None
```

**New CLI Commands**:
```bash
# Setup and configuration
dev-agent setup                    # Interactive setup wizard
dev-agent validate                 # Validate environment and configuration

# Project operations
dev-agent init [path]              # Initialize project (enhanced)
dev-agent resume [path]            # Resume project (enhanced)
dev-agent status                   # Show detailed status
dev-agent audit                    # Run comprehensive audit

# Workflow operations
dev-agent run                      # Execute complete workflow
dev-agent phase <PHASE>            # Execute specific phase
dev-agent retry                    # Retry failed phase

# Cost management
dev-agent cost                     # Show cost summary
dev-agent cost --phase <PHASE>     # Show phase-specific costs
dev-agent cost --export report.json # Export cost report

# Cleanup and maintenance
dev-agent cleanup --scan           # Scan for cleanup candidates
dev-agent cleanup --execute        # Execute cleanup (with confirmation)
dev-agent cleanup --dry-run        # Show what would be cleaned

# Help and documentation
dev-agent help                     # Show general help
dev-agent help <command>           # Show command-specific help
dev-agent examples                 # Show usage examples
```

### 4. User Journey Optimization

**Purpose**: Provide tailored experiences for different user scenarios.

**Component Structure**:
```python
# dev_agent/onboarding/journey_manager.py
class JourneyManager:
    """Manages user journey based on project context."""
    
    def detect_project_type(self, path: Path) -> ProjectType
    def is_first_run(self) -> bool
    def get_onboarding_flow(self, project_type: ProjectType) -> OnboardingFlow
    def guide_user_through_phase(self, phase: PhaseType) -> None

@dataclass
class OnboardingFlow:
    steps: list[OnboardingStep]
    tips: list[str]
    warnings: list[str]
    
@dataclass
class OnboardingStep:
    title: str
    description: str
    action: Callable
    help_text: str
    estimated_time: str
```

**Journey Types**:

1. **New Project Journey**:
   ```
   1. Welcome & Setup Wizard
   2. Azure OpenAI Configuration
   3. Template Selection (optional)
   4. Project Scaffolding
   5. Initial Specification Creation
   6. Design Generation
   7. Task Breakdown
   ```

2. **Existing Codebase Journey**:
   ```
   1. Welcome & Setup Wizard
   2. Azure OpenAI Configuration
   3. Codebase Detection & Analysis
   4. Indexing with Progress Display
   5. Pattern Recognition Summary
   6. Specification Generation from Code
   7. Design Documentation
   8. Enhancement Task Generation
   ```

### 5. Setup Wizard

**Purpose**: Guide first-time users through configuration.

**Component Structure**:
```python
# dev_agent/onboarding/setup_wizard.py
class SetupWizard:
    """Interactive setup wizard for first-time users."""
    
    def run(self) -> SetupResult
    def configure_azure_openai(self) -> AzureConfig
    def test_azure_connection(self, config: AzureConfig) -> bool
    def explain_workflow(self) -> None
    def offer_sample_project(self) -> bool
    def save_user_preferences(self, prefs: UserPreferences) -> None

@dataclass
class SetupResult:
    azure_configured: bool
    preferences_saved: bool
    sample_project_created: bool
    ready_to_use: bool
```

**Wizard Flow**:
```
┌─────────────────────────────────────────┐
│  Welcome to dev-agent!                  │
│  Let's get you set up...                │
└────────────┬────────────────────────────┘
             │
┌────────────▼────────────────────────────┐
│  Azure OpenAI Configuration             │
│  - Endpoint URL                         │
│  - API Key                              │
│  - Deployment Names                     │
│  - Test Connection                      │
└────────────┬────────────────────────────┘
             │
┌────────────▼────────────────────────────┐
│  Workflow Explanation                   │
│  - Four-phase overview                  │
│  - What to expect                       │
│  - Cost estimates                       │
└────────────┬────────────────────────────┘
             │
┌────────────▼────────────────────────────┐
│  Project Type Selection                 │
│  - New project from template            │
│  - Analyze existing codebase            │
│  - Skip for now                         │
└────────────┬────────────────────────────┘
             │
┌────────────▼────────────────────────────┐
│  Setup Complete!                        │
│  - Configuration saved                  │
│  - Next steps                           │
│  - Quick start guide                    │
└─────────────────────────────────────────┘
```

### 6. Progress and Feedback System

**Purpose**: Provide real-time feedback during long-running operations.

**Component Structure**:
```python
# dev_agent/cli/feedback_system.py
class FeedbackSystem:
    """Provides user feedback during operations."""
    
    def show_phase_start(self, phase: PhaseType) -> None
    def show_operation_progress(self, operation: str, progress: float) -> None
    def show_streaming_content(self, stream: AsyncIterator[str]) -> str
    def show_phase_complete(self, phase: PhaseType, result: PhaseResult) -> None
    def show_error(self, error: Exception, suggestions: list[str]) -> None
    def show_warning(self, message: str, action: str | None = None) -> None
    def show_success(self, message: str, next_steps: list[str] | None = None) -> None
```

**Feedback Types**:
1. **Progress Indicators**: Spinners for indeterminate operations, progress bars for determinate
2. **Streaming Display**: Real-time display of LLM responses
3. **Phase Summaries**: Detailed summaries after each phase completion
4. **Cost Tracking**: Real-time cost updates during operations
5. **Error Messages**: User-friendly errors with actionable suggestions
6. **Success Messages**: Clear confirmation with next steps

### 7. Documentation System

**Purpose**: Maintain comprehensive, up-to-date documentation.

**Documentation Structure**:
```
docs/
├── index.md                          # Overview and quick start
├── installation.md                   # Installation guide
├── getting-started/
│   ├── first-time-setup.md          # Setup wizard walkthrough
│   ├── new-project.md               # New project journey
│   ├── existing-codebase.md         # Existing codebase journey
│   └── troubleshooting.md           # Common issues and solutions
├── configuration/
│   ├── azure-openai.md              # Azure OpenAI setup (enhanced)
│   ├── environment-variables.md     # All env vars documented
│   └── advanced-config.md           # Advanced configuration options
├── cli-reference/
│   ├── commands.md                  # All commands documented
│   ├── workflow-commands.md         # Workflow-specific commands
│   ├── utility-commands.md          # Utility commands
│   └── examples.md                  # CLI usage examples
├── user-guides/
│   ├── four-phase-workflow.md       # Detailed workflow guide
│   ├── cost-management.md           # Managing Azure OpenAI costs
│   ├── best-practices.md            # Best practices and tips
│   └── advanced-usage.md            # Advanced features
├── api/
│   ├── cli.md                       # CLI module API
│   ├── workflow.md                  # Workflow module API
│   ├── llm.md                       # LLM integration API
│   └── ...                          # Other module APIs
└── development/
    ├── contributing.md              # Contribution guide
    ├── architecture.md              # System architecture
    ├── testing.md                   # Testing guide
    └── cleanup-summary.md           # Cleanup changes documented
```

**Documentation Updates**:
1. **README.md**: Update with new CLI commands and user journeys
2. **Installation Guide**: Add troubleshooting section
3. **Azure OpenAI Guide**: Step-by-step setup with screenshots
4. **CLI Reference**: Document all commands with examples
5. **User Guides**: Create journey-specific guides
6. **API Documentation**: Update for any interface changes
7. **Changelog**: Document all cleanup and enhancement changes

## Data Models

### Audit Models

```python
@dataclass
class AuditResult:
    """Result of a single audit check."""
    component: str
    status: Literal["pass", "fail", "warning"]
    message: str
    details: dict[str, Any]
    recommendations: list[str]
    timestamp: datetime

@dataclass
class AuditReport:
    """Complete audit report."""
    timestamp: datetime
    results: list[AuditResult]
    overall_status: Literal["pass", "fail", "warning"]
    summary: str
    total_checks: int
    passed_checks: int
    failed_checks: int
    warnings: int
```

### Cleanup Models

```python
@dataclass
class CleanupPlan:
    """Plan for cleanup operations."""
    files_to_remove: list[Path]
    directories_to_remove: list[Path]
    dependencies_to_remove: list[str]
    files_to_move: dict[Path, Path]
    total_size_reduction: int
    estimated_time: str
    safety_level: Literal["safe", "moderate", "aggressive"]

@dataclass
class CleanupResult:
    """Result of cleanup execution."""
    removed_files: list[Path]
    removed_directories: list[Path]
    moved_files: dict[Path, Path]
    removed_dependencies: list[str]
    errors: list[str]
    size_reduction: int
    execution_time: float
```

### Onboarding Models

```python
@dataclass
class UserPreferences:
    """User preferences saved during setup."""
    azure_configured: bool
    preferred_editor: str | None
    cost_warnings_enabled: bool
    budget_threshold: float | None
    auto_approve_phases: bool
    verbose_output: bool

@dataclass
class OnboardingStep:
    """Single step in onboarding flow."""
    title: str
    description: str
    action: Callable[[], bool]
    help_text: str
    estimated_time: str
    skippable: bool
    completed: bool = False

@dataclass
class ProjectContext:
    """Context about the project being worked on."""
    path: Path
    project_type: Literal["new", "existing", "template"]
    has_code: bool
    languages_detected: list[str]
    estimated_size: str
    complexity: Literal["simple", "moderate", "complex"]
```

## Error Handling

### Error Categories

1. **Configuration Errors**: Azure OpenAI not configured, invalid credentials
2. **File System Errors**: Permission denied, disk full, path not found
3. **API Errors**: Rate limits, timeouts, authentication failures
4. **Workflow Errors**: Phase failures, state corruption, invalid transitions
5. **User Input Errors**: Invalid commands, malformed arguments

### Error Handling Strategy

```python
# dev_agent/errors/enhanced_error_handler.py
class EnhancedErrorHandler:
    """Enhanced error handling with user-friendly messages."""
    
    def handle_configuration_error(self, error: ConfigurationError) -> ErrorResponse
    def handle_api_error(self, error: APIError) -> ErrorResponse
    def handle_workflow_error(self, error: WorkflowError) -> ErrorResponse
    def suggest_solutions(self, error: Exception) -> list[str]
    def create_error_report(self, error: Exception) -> ErrorReport

@dataclass
class ErrorResponse:
    """Structured error response."""
    error_type: str
    message: str
    suggestions: list[str]
    documentation_link: str | None
    can_retry: bool
    recovery_action: Callable | None
```

### Error Messages

All error messages should follow this format:
```
❌ Error: <Brief description>

What happened:
<Detailed explanation>

Possible solutions:
1. <Solution 1>
2. <Solution 2>
3. <Solution 3>

For more help: <documentation link>
```

## Testing Strategy

### Test Categories

1. **Unit Tests**: Test individual components in isolation
2. **Integration Tests**: Test component interactions
3. **End-to-End Tests**: Test complete user journeys
4. **CLI Tests**: Test CLI commands and output
5. **Performance Tests**: Test indexing and search performance

### Test Structure

```python
# tests/test_audit_engine.py
class TestAuditEngine:
    def test_audit_indexing_phase(self, mock_project)
    def test_audit_specification_phase(self, mock_project)
    def test_audit_design_phase(self, mock_project)
    def test_audit_implementation_phase(self, mock_project)
    def test_generate_audit_report(self, mock_results)

# tests/test_cleanup_manager.py
class TestCleanupManager:
    def test_scan_for_cleanup_candidates(self, test_repo)
    def test_identify_temporary_files(self, test_repo)
    def test_execute_cleanup_dry_run(self, test_repo)
    def test_execute_cleanup_with_confirmation(self, test_repo)

# tests/test_user_journeys.py
class TestUserJourneys:
    def test_new_project_journey(self, tmp_path)
    def test_existing_codebase_journey(self, sample_project)
    def test_setup_wizard_flow(self, mock_cli)
    def test_phase_transitions(self, initialized_project)

# tests/test_enhanced_cli.py
class TestEnhancedCLI:
    def test_setup_command(self, mock_cli)
    def test_status_command(self, mock_project)
    def test_cost_report_command(self, mock_project)
    def test_cleanup_command(self, test_repo)
    def test_help_command(self, mock_cli)
```

### Test Coverage Goals

- Overall coverage: ≥90%
- Critical paths: 100%
- CLI commands: 100%
- Error handling: 100%
- User journeys: 100%

## Implementation Phases

### Phase 1: Audit and Analysis
1. Create audit engine
2. Run comprehensive audit
3. Document findings
4. Identify cleanup candidates

### Phase 2: Cleanup Execution
1. Implement cleanup manager
2. Execute cleanup with dry-run
3. Review and confirm changes
4. Execute actual cleanup
5. Document removed files

### Phase 3: CLI Enhancements
1. Implement setup wizard
2. Enhance existing commands
3. Add new utility commands
4. Improve progress display
5. Enhance error messages

### Phase 4: User Journey Optimization
1. Implement journey manager
2. Create onboarding flows
3. Add contextual help
4. Implement feedback system

### Phase 5: Documentation
1. Update README
2. Create user guides
3. Update API documentation
4. Create CLI reference
5. Add troubleshooting guide

### Phase 6: Testing and Validation
1. Write comprehensive tests
2. Run test suite
3. Fix identified issues
4. Validate user journeys
5. Performance testing

## Performance Considerations

### Optimization Targets

1. **Indexing Performance**: 100+ files/second
2. **Embedding Generation**: Batch size of 16, parallel processing
3. **Vector Search**: O(log n) with FAISS
4. **CLI Responsiveness**: <100ms for command parsing
5. **State Persistence**: <100ms for save operations
6. **Startup Time**: <1 second to ready state

### Caching Strategy

1. **Embedding Cache**: Cache all generated embeddings
2. **AST Cache**: Cache parsed ASTs for unchanged files
3. **Pattern Cache**: Cache detected patterns
4. **Configuration Cache**: Cache loaded configuration

## Security Considerations

1. **API Key Protection**: Never log or display API keys
2. **File System Safety**: Validate all file operations
3. **Input Validation**: Sanitize all user inputs
4. **Backup Creation**: Create backups before destructive operations
5. **Audit Logging**: Log all significant operations

## Deployment Strategy

### Release Process

1. **Version Bump**: Update version in `pyproject.toml`
2. **Changelog Update**: Document all changes
3. **Documentation Build**: Build and deploy docs
4. **Package Build**: Build wheel and sdist
5. **PyPI Upload**: Upload to PyPI
6. **GitHub Release**: Create GitHub release with notes

### Migration Guide

For users upgrading from previous versions:
1. Backup existing `.dev_agent/` directory
2. Run `dev-agent setup` to reconfigure
3. Review new CLI commands
4. Update any scripts using old commands
5. Review cost tracking features

## Success Metrics

1. **Functionality**: All core features pass audit
2. **Cleanup**: 20%+ reduction in repository size
3. **User Experience**: Setup wizard completion rate >90%
4. **Documentation**: Zero broken links, comprehensive coverage
5. **Performance**: All performance targets met
6. **Test Coverage**: ≥90% overall coverage
7. **User Satisfaction**: Positive feedback on CLI improvements
