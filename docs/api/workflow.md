# Workflow API Reference

The workflow module orchestrates the four-phase development process: Indexing, Specification, Design, and Implementation.

## Overview

The workflow system manages:

- **Phase Transitions**: Sequential progression through workflow phases
- **State Management**: Persistent state across sessions
- **User Approval**: Human-in-the-loop approval gates between phases
- **Error Handling**: Graceful error recovery and retry mechanisms
- **Progress Tracking**: Real-time progress reporting and cost tracking
- **LLM Integration**: Azure OpenAI integration for generation tasks

## Four-Phase Workflow

### 1. Indexing Phase
- Parse codebase with Tree-sitter
- Generate embeddings via Azure OpenAI
- Store vectors in FAISS database
- Detect patterns and conventions

### 2. Specification Phase
- Retrieve relevant code context
- Generate specifications with GPT-4
- Require user approval
- Save to `.dev_agent/documents/`

### 3. Design Phase
- Analyze architectural patterns
- Generate technical design with GPT-4
- Ensure consistency with codebase
- Require user approval

### 4. Implementation Phase
- Generate actionable tasks
- Match existing code style
- Create implementation plan
- Support iterative development

## Workflow Manager

The workflow manager orchestrates the complete four-phase workflow, managing phase transitions, state persistence, and user approvals.

::: dev_agent.workflow.workflow_manager
    options:
      show_root_heading: true
      show_source: true
      members_order: source

## Phase Manager

The phase manager handles individual phase execution, progress tracking, and error recovery.

::: dev_agent.workflow.phase_manager
    options:
      show_root_heading: true
      show_source: true
      members_order: source

## Design Workflow

The design workflow generates technical design documents based on specifications and codebase patterns.

::: dev_agent.workflow.design_workflow
    options:
      show_root_heading: true
      show_source: true
      members_order: source

## Specification Workflow

The specification workflow generates detailed specifications from codebase analysis and user requirements.

::: dev_agent.workflow.specification_workflow
    options:
      show_root_heading: true
      show_source: true
      members_order: source

## Usage Examples

### Running Complete Workflow

```python
from dev_agent.workflow.workflow_manager import WorkflowManager
from pathlib import Path

# Create workflow manager
manager = WorkflowManager(project_path=Path("/path/to/project"))

# Initialize project
await manager.initialize_project()

# Run complete workflow
result = await manager.run_complete_workflow()

if result.success:
    print("Workflow completed successfully!")
    print(f"Total cost: ${result.total_cost:.2f}")
else:
    print(f"Workflow failed: {result.error_message}")
```

### Running Individual Phases

```python
from dev_agent.workflow.phase_manager import PhaseManager
from dev_agent.models.enums import PhaseType

# Create phase manager
phase_manager = PhaseManager(project_path=Path("/path/to/project"))

# Run indexing phase
indexing_result = await phase_manager.execute_phase(PhaseType.INDEXING)
print(f"Indexed {indexing_result.files_processed} files")

# Run specification phase (requires indexing complete)
spec_result = await phase_manager.execute_phase(PhaseType.SPECIFICATION)
print(f"Generated specification: {spec_result.document_path}")

# Run design phase (requires specification approval)
design_result = await phase_manager.execute_phase(PhaseType.DESIGN)
print(f"Generated design: {design_result.document_path}")

# Run implementation phase (requires design approval)
impl_result = await phase_manager.execute_phase(PhaseType.IMPLEMENTATION)
print(f"Generated {len(impl_result.tasks)} tasks")
```

### State Management

```python
from dev_agent.workflow.workflow_manager import WorkflowManager
from pathlib import Path

# Create workflow manager
manager = WorkflowManager(project_path=Path("/path/to/project"))

# Load existing state
state = manager.load_state()
print(f"Current phase: {state.current_phase}")
print(f"Completed phases: {state.completed_phases}")

# Resume from last phase
result = await manager.resume_workflow()

# Save state
manager.save_state()
```

### Error Handling

```python
from dev_agent.workflow.workflow_manager import WorkflowManager
from dev_agent.errors.exceptions import WorkflowError
from pathlib import Path

manager = WorkflowManager(project_path=Path("/path/to/project"))

try:
    result = await manager.run_complete_workflow()
except WorkflowError as e:
    print(f"Workflow error: {e}")
    
    # Get recovery suggestions
    suggestions = e.get_recovery_suggestions()
    for suggestion in suggestions:
        print(f"- {suggestion}")
    
    # Retry failed phase
    if e.can_retry:
        result = await manager.retry_failed_phase()
```

## CLI Usage

```bash
# Run complete workflow
dev-agent run

# Run specific phase
dev-agent phase indexing
dev-agent phase specification
dev-agent phase design
dev-agent phase implementation

# Resume workflow
dev-agent resume

# Retry failed phase
dev-agent retry

# Check workflow status
dev-agent status
```

## Workflow State

The workflow state includes:

- **current_phase**: Current phase being executed
- **completed_phases**: List of completed phases
- **phase_results**: Results from each phase
- **approval_status**: User approval status for each phase
- **cost_tracking**: Token usage and costs per phase
- **error_history**: History of errors and recoveries
- **timestamp**: Last update timestamp

## Phase Results

Each phase returns a result containing:

- **success**: Whether phase completed successfully
- **phase_type**: Which phase was executed
- **duration**: Time taken to complete
- **cost**: Azure OpenAI costs incurred
- **output**: Phase-specific output (documents, tasks, etc.)
- **errors**: Any errors encountered
- **warnings**: Any warnings generated

## Best Practices

1. **Always initialize** before running workflow
2. **Review approvals** carefully between phases
3. **Monitor costs** during execution
4. **Save state frequently** to enable recovery
5. **Handle errors gracefully** with retry logic
6. **Use phase-specific commands** for targeted execution
7. **Review generated documents** before proceeding

## Error Recovery

The workflow system provides:

- **Automatic retry** with exponential backoff for transient errors
- **State preservation** before risky operations
- **Rollback capability** for failed phases
- **Manual intervention** points for complex errors
- **Detailed error logs** for debugging
- **Recovery suggestions** based on error type