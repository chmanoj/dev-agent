# Specification: Fix Workflow State Persistence and Document Storage

## Overview

During end-to-end testing of the login page creation workflow, critical bugs were discovered in the workflow manager's state persistence and document storage mechanisms. Generated content (specifications, designs, tasks) is not being saved to the project state or written to disk, preventing phase transitions and losing user work.

## Problem Statement

### Current Issues

1. **Specification Not Saved to State**
   - Specification content is generated successfully via LLM
   - User approves the specification
   - However, `state.specification` remains `null` after generation
   - Phase transition to design fails with "No approved specification found"

2. **Documents Not Written to Filesystem**
   - Expected: Generated documents saved to `.dev_agent/documents/`
   - Actual: Directory remains empty after generation
   - Impact: No persistent record of generated content

3. **Approval State Not Persisted**
   - User approvals given during generation
   - Approvals not reflected in `state.json`
   - Phase validation fails due to missing approval flags

4. **Inconsistent State Updates**
   - Some state fields update correctly (e.g., `current_phase`, `indexing_complete`)
   - Other fields remain null despite content generation
   - State file writes succeed but content is incomplete

## Root Cause Analysis

### Observed Behavior

From test execution logs:
```
✅ Specification approved!
Unknown document type: specification
Specification saved to test-app/.dev_agent/documents/SPECIFICATION.md
Specification phase completed successfully!
```

But state shows:
```json
{
  "specification": null,
  "design": null,
  "tasks": null
}
```

### Likely Causes

1. **Document Type Mismatch**: "Unknown document type: specification" suggests document saving logic doesn't recognize the type
2. **State Update Timing**: Content generated but state not updated before save
3. **Approval Recording**: Approval given but not written to state before phase completion
4. **File Path Issues**: Document claims to be saved but file doesn't exist

## Requirements

### REQ-1: Persist Generated Specifications to State

**Priority**: Critical  
**User Story**: As a developer, when I generate and approve a specification, it should be saved to the project state so I can proceed to the design phase.

**Acceptance Criteria**:
1. WHEN specification is generated via LLM, THEN `state.specification` SHALL contain the full specification text
2. WHEN user approves specification, THEN `state.specification_approved` SHALL be set to `true`
3. WHEN state is saved, THEN specification content SHALL persist across sessions
4. WHEN specification is loaded, THEN it SHALL be available for subsequent phases

**Technical Requirements**:
- Update `ProjectState.specification` field after generation
- Call `state_manager.save_project_state()` after content assignment
- Validate specification is not null before phase transition
- Handle large specification content (>10KB) efficiently

### REQ-2: Write Generated Documents to Filesystem

**Priority**: Critical  
**User Story**: As a developer, I want generated documents saved to disk so I can review, edit, and version control them.

**Acceptance Criteria**:
1. WHEN specification is generated, THEN it SHALL be written to `.dev_agent/documents/specification.md`
2. WHEN design is generated, THEN it SHALL be written to `.dev_agent/documents/design.md`
3. WHEN tasks are generated, THEN they SHALL be written to `.dev_agent/documents/tasks.md`
4. WHEN document is saved, THEN file SHALL exist and be readable
5. WHEN document already exists, THEN it SHALL be versioned/backed up before overwrite

**Technical Requirements**:
- Create `.dev_agent/documents/` directory if not exists
- Use consistent filename conventions (lowercase with underscores)
- Write files with UTF-8 encoding
- Set appropriate file permissions (644)
- Log file write operations for debugging
- Handle write errors gracefully with user feedback

### REQ-3: Record and Persist User Approvals

**Priority**: High  
**User Story**: As a developer, when I approve a document, that approval should be recorded so phase transitions work correctly.

**Acceptance Criteria**:
1. WHEN user approves specification, THEN `state.specification_approved` SHALL be `true`
2. WHEN user approves design, THEN `state.design_approved` SHALL be `true`
3. WHEN user approves tasks, THEN `state.tasks_approved` SHALL be `true`
4. WHEN approval is recorded, THEN state SHALL be saved immediately
5. WHEN phase transition is attempted, THEN approval status SHALL be validated

**Technical Requirements**:
- Add approval flags to `ProjectState` model if missing
- Update approval flags in workflow manager after user confirmation
- Save state immediately after approval recording
- Validate approval flags in phase transition logic
- Provide clear error messages when approvals are missing

### REQ-4: Fix Document Type Recognition

**Priority**: High  
**User Story**: As a developer, the system should correctly identify and save all document types without errors.

**Acceptance Criteria**:
1. WHEN saving specification, THEN document type SHALL be recognized as "specification"
2. WHEN saving design, THEN document type SHALL be recognized as "design"
3. WHEN saving tasks, THEN document type SHALL be recognized as "tasks"
4. WHEN unknown document type encountered, THEN system SHALL log warning but still save
5. WHEN document is saved, THEN no "Unknown document type" warnings SHALL appear

**Technical Requirements**:
- Review and fix document type mapping in state manager
- Ensure consistent naming between workflow phases and document types
- Add validation for supported document types
- Improve error messages for unsupported types

### REQ-5: Ensure State Consistency

**Priority**: High  
**User Story**: As a developer, the project state should always be consistent and reflect the actual workflow progress.

**Acceptance Criteria**:
1. WHEN content is generated, THEN state SHALL be updated before phase completion
2. WHEN state is saved, THEN all fields SHALL be serialized correctly
3. WHEN state is loaded, THEN all fields SHALL be deserialized correctly
4. WHEN phase transitions, THEN state SHALL reflect new phase immediately
5. WHEN error occurs, THEN state SHALL remain in valid state (no partial updates)

**Technical Requirements**:
- Use atomic state updates (all or nothing)
- Validate state before saving
- Add state consistency checks
- Implement rollback on save failures
- Log all state changes for debugging

## Technical Design

### Component Changes

#### 1. Workflow Manager (`dev_agent/workflow/workflow_manager.py`)

**Changes Needed**:
```python
async def transition_to_phase(self, target_phase: PhaseType) -> bool:
    """Transition to target phase with proper state persistence."""
    
    # Generate content
    content = await self._generate_phase_content(target_phase)
    
    # Update state with generated content
    if target_phase == PhaseType.SPECIFICATION:
        self.current_project_state.specification = content
    elif target_phase == PhaseType.DESIGN:
        self.current_project_state.design = content
    elif target_phase == PhaseType.IMPLEMENTATION:
        self.current_project_state.tasks = content
    
    # Save state immediately after content generation
    self.state_manager.save_project_state(self.current_project_state)
    
    # Save document to filesystem
    self._save_document_to_file(target_phase, content)
    
    # Request user approval
    approved = await self._request_approval(target_phase, content)
    
    # Record approval in state
    if approved:
        self._record_approval(target_phase)
        self.state_manager.save_project_state(self.current_project_state)
    
    return approved

def _record_approval(self, phase: PhaseType) -> None:
    """Record user approval for phase."""
    if phase == PhaseType.SPECIFICATION:
        self.current_project_state.specification_approved = True
    elif phase == PhaseType.DESIGN:
        self.current_project_state.design_approved = True
    elif phase == PhaseType.IMPLEMENTATION:
        self.current_project_state.tasks_approved = True

def _save_document_to_file(self, phase: PhaseType, content: str) -> None:
    """Save generated document to filesystem."""
    docs_dir = Path(self.current_project_state.project_path) / ".dev_agent" / "documents"
    docs_dir.mkdir(parents=True, exist_ok=True)
    
    filename_map = {
        PhaseType.SPECIFICATION: "specification.md",
        PhaseType.DESIGN: "design.md",
        PhaseType.IMPLEMENTATION: "tasks.md"
    }
    
    filename = filename_map.get(phase)
    if not filename:
        logger.warning(f"Unknown phase for document save: {phase}")
        return
    
    filepath = docs_dir / filename
    
    try:
        filepath.write_text(content, encoding='utf-8')
        logger.info(f"Saved {phase.value} document to {filepath}")
    except Exception as e:
        logger.error(f"Failed to save document: {e}", exc_info=True)
        raise DocumentSaveError(f"Could not save {phase.value} document") from e
```

#### 2. State Manager (`dev_agent/state/state_manager.py`)

**Changes Needed**:
```python
def save_project_state(self, state: ProjectState) -> None:
    """Save project state with validation."""
    
    # Validate state before saving
    validation_errors = self._validate_state(state)
    if validation_errors:
        logger.warning(f"State validation warnings: {validation_errors}")
    
    # Serialize state
    try:
        state_dict = {
            "project_path": state.project_path,
            "current_phase": state.current_phase.value if isinstance(state.current_phase, PhaseType) else state.current_phase,
            "indexing_complete": state.indexing_complete,
            "specification": state.specification,  # Full content
            "specification_approved": getattr(state, 'specification_approved', False),
            "design": state.design,  # Full content
            "design_approved": getattr(state, 'design_approved', False),
            "tasks": state.tasks,  # Full content or serialized
            "tasks_approved": getattr(state, 'tasks_approved', False),
            # ... other fields
        }
        
        # Write atomically
        temp_file = self.state_file.with_suffix('.tmp')
        temp_file.write_text(json.dumps(state_dict, indent=2), encoding='utf-8')
        temp_file.replace(self.state_file)
        
        logger.info(f"Successfully saved project state to {self.state_file}")
        
    except Exception as e:
        logger.error(f"Failed to save state: {e}", exc_info=True)
        raise StateSavingError(f"Could not save project state") from e

def _validate_state(self, state: ProjectState) -> list[str]:
    """Validate state consistency."""
    errors = []
    
    # Check phase consistency
    if state.current_phase == PhaseType.DESIGN:
        if not state.specification:
            errors.append("Design phase but no specification")
        if not getattr(state, 'specification_approved', False):
            errors.append("Design phase but specification not approved")
    
    if state.current_phase == PhaseType.IMPLEMENTATION:
        if not state.design:
            errors.append("Implementation phase but no design")
        if not getattr(state, 'design_approved', False):
            errors.append("Implementation phase but design not approved")
    
    return errors
```

#### 3. Project State Model (`dev_agent/models/project_state.py`)

**Changes Needed**:
```python
@dataclass
class ProjectState:
    """Project state with approval tracking."""
    
    project_path: str
    current_phase: PhaseType
    indexing_complete: bool = False
    
    # Generated content
    specification: str | None = None
    design: str | None = None
    tasks: list[Task] | None = None
    
    # Approval tracking (ADD THESE)
    specification_approved: bool = False
    design_approved: bool = False
    tasks_approved: bool = False
    
    # Metadata
    index_metadata: dict | None = None
    implementation_progress: dict = field(default_factory=dict)
    session_data: dict = field(default_factory=dict)
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())
    updated_at: str = field(default_factory=lambda: datetime.now().isoformat())
```

### Error Handling

**New Exception Types**:
```python
class DocumentSaveError(DevAgentError):
    """Raised when document cannot be saved to filesystem."""
    pass

class StateInconsistencyError(DevAgentError):
    """Raised when state is inconsistent."""
    pass
```

### Logging Enhancements

Add detailed logging for:
- Content generation completion
- State updates before save
- Document file writes
- Approval recordings
- Phase transition validations

## Testing Requirements

### Unit Tests

1. **Test State Persistence**
   - Generate content and verify state update
   - Save state and verify file contents
   - Load state and verify content restored

2. **Test Document Saving**
   - Generate document and verify file created
   - Verify file contents match generated content
   - Test overwrite behavior

3. **Test Approval Recording**
   - Record approval and verify state flag
   - Verify approval persists across save/load
   - Test phase transition with/without approval

### Integration Tests

1. **Test Complete Workflow**
   - Generate specification → verify saved
   - Approve specification → verify recorded
   - Transition to design → verify allowed
   - Generate design → verify saved
   - Complete full workflow

2. **Test Error Recovery**
   - Simulate file write failure
   - Simulate state save failure
   - Verify state remains consistent

### E2E Tests

Use the existing `create_login_page.py` test to validate:
1. Specification generation and persistence
2. Design generation and persistence
3. Task generation and persistence
4. Full workflow completion

## Success Criteria

1. ✅ `create_login_page.py` test completes successfully
2. ✅ All generated documents exist in `.dev_agent/documents/`
3. ✅ `state.json` contains all generated content
4. ✅ Phase transitions work without "No approved specification" errors
5. ✅ No "Unknown document type" warnings in logs
6. ✅ State remains consistent across save/load cycles
7. ✅ User approvals are recorded and validated

## Implementation Plan

### Phase 1: Fix State Persistence (Priority: Critical)
- [ ] Add approval flags to `ProjectState` model
- [ ] Update workflow manager to save content to state
- [ ] Fix state serialization to include all fields
- [ ] Add state validation before save

### Phase 2: Fix Document Storage (Priority: Critical)
- [ ] Implement `_save_document_to_file()` method
- [ ] Fix document type recognition
- [ ] Ensure documents directory creation
- [ ] Add error handling for file writes

### Phase 3: Fix Approval Recording (Priority: High)
- [ ] Implement `_record_approval()` method
- [ ] Save state immediately after approval
- [ ] Update phase transition validation
- [ ] Add approval status to state display

### Phase 4: Testing and Validation (Priority: High)
- [ ] Run `create_login_page.py` test
- [ ] Verify all documents created
- [ ] Verify state consistency
- [ ] Run full test suite

### Phase 5: Documentation (Priority: Medium)
- [ ] Update workflow documentation
- [ ] Document state structure
- [ ] Add troubleshooting guide
- [ ] Update API documentation

## Dependencies

- No new external dependencies required
- Uses existing state management infrastructure
- Leverages existing file I/O utilities

## Risks and Mitigation

### Risk 1: Large Content in State File
**Impact**: State file becomes very large with full specification/design text  
**Mitigation**: Consider storing only references in state, full content in separate files  
**Alternative**: Implement content compression for state storage

### Risk 2: Concurrent State Updates
**Impact**: Multiple processes could corrupt state file  
**Mitigation**: Use file locking or atomic writes (already using atomic writes)

### Risk 3: Backward Compatibility
**Impact**: Existing state files may not have new approval fields  
**Mitigation**: Use `getattr()` with defaults when reading approval flags

## Acceptance Testing

Run the following command and verify success:
```bash
export GEMINI_API_KEY=AIzaSyB7b0svJ7VFJKiCVq5A1xylYjngGR0E-I0
export GEMINI_MODEL_NAME=gemini-2.5-flash
export GEMINI_EMBEDDING_MODEL=gemini-embedding-001
export PREFERRED_LLM_PROVIDER=gemini

uv run python create_login_page.py
```

Expected output:
```
✓ Specification generated
✓ Specification saved to state
✓ Specification saved to file
✓ Design generated
✓ Design saved to state
✓ Design saved to file
✓ Tasks generated
✓ Tasks saved to state
✓ Tasks saved to file
✅ Success! All checks passed!
```

## References

- Test Results: `TEST_RESULTS.md`
- Test Script: `create_login_page.py`
- Workflow Manager: `dev_agent/workflow/workflow_manager.py`
- State Manager: `dev_agent/state/state_manager.py`
- Project State Model: `dev_agent/models/project_state.py`
