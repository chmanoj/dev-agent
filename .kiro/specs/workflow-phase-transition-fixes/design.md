# Design Document

## Overview

This design addresses three critical bugs affecting ALL phases of the dev-agent workflow: incomplete requirements generation from AI, datetime serialization errors in state persistence, and state loading failures. The solution involves enhancing the AI prompt templates to enforce complete requirements generation, fixing datetime handling in the state manager's serialization/deserialization logic for ALL document types (specification, design, tasks), and improving error handling throughout all workflow phases.

**Scope:** The fixes apply to:
- **Specification Phase:** Requirements generation and approval
- **Design Phase:** Design document generation and approval  
- **Task Phase:** Task list generation and approval
- **Implementation Phase:** Task tracking and progress updates
- **All Phase Transitions:** State persistence between phases

**Provider Compatibility:** All fixes are implemented at the abstraction layer and work with both Azure OpenAI and Gemini API through the ILLMClient interface. The datetime serialization, prompt templates, and validation logic are provider-agnostic.

## Architecture

### Component Structure

The fix involves modifications to three main components:

1. **Prompt Templates** (`dev_agent/llm/prompt_templates.py`)
   - Enhanced prompts with explicit requirements for complete output
   - Validation instructions for AI to self-check completeness

2. **State Manager** (`dev_agent/state/state_manager.py`)
   - Fixed datetime serialization in `_serialize_dataclass()`
   - Fixed datetime deserialization in reconstruction methods
   - Added validation and error recovery

3. **Specification Generator** (`dev_agent/generation/specification_generator.py`)
   - Enhanced parsing logic for AI-generated content
   - Validation of parsed requirements
   - User warnings for incomplete specifications

4. **Specification Workflow** (`dev_agent/workflow/specification_workflow.py`)
   - Better error handling and user feedback
   - Validation of generated specifications before approval

### Data Flow

```
User Request → Specification Workflow
                ↓
            Prompt Template (enhanced)
                ↓
            LLM Client (Azure OpenAI or Gemini)
                ↓
            AI-Generated Content
                ↓
            Specification Parser (enhanced)
                ↓
            Validation Check (new)
                ↓
            User Approval
                ↓
            State Manager (fixed datetime handling)
                ↓
            Persisted State (correct format)
```

**Note:** The fixes are provider-agnostic and work with both Azure OpenAI and Gemini API since they operate at the abstraction layer level (ILLMClient interface).

## Components and Interfaces

### 1. Enhanced Prompt Templates

**File:** `dev_agent/llm/prompt_templates.py`

**Changes:**
- Add explicit instructions in system prompts to generate complete requirements
- Reference the format guide (`dev_agent/REQUIREMENTS_FORMAT_GUIDE.md`) for expected structure
- Emphasize minimum requirement counts (3-5 requirements minimum)
- Add validation instructions for AI to self-check completeness
- Include examples from the format guide in prompts

**Format Reference:**
The prompts should enforce the format documented in `dev_agent/REQUIREMENTS_FORMAT_GUIDE.md`:
- User Story: "As a [role], I want [feature], so that [benefit]"
- Acceptance Criteria using EARS format (WHEN/THEN, IF/THEN, WHERE, SHALL)
- At least 2-3 acceptance criteria per requirement
- Specific, testable criteria

**Provider Compatibility:**
- Prompts work with both Azure OpenAI (GPT-4) and Gemini API
- Both providers support the same prompt structure (system + user prompts)
- No provider-specific prompt modifications needed

**Interface:**
```python
# No interface changes, only prompt content updates
SPECIFICATION_TEMPLATE.system_prompt  # Enhanced with completeness requirements
SPECIFICATION_NEW_PROJECT_TEMPLATE.system_prompt  # Enhanced with completeness requirements
```

### 2. Fixed State Manager Datetime Handling

**File:** `dev_agent/state/state_manager.py`

**Changes:**
- Fix `_serialize_dataclass()` to properly handle datetime objects in ALL document types
- Fix `_deserialize_datetime()` to handle None values
- Fix `_reconstruct_specification()` to handle None approval_timestamp
- Fix `_reconstruct_design()` to handle None approval_timestamp (if field exists)
- Fix `_reconstruct_tasks()` to handle None approval_timestamp (if field exists)
- Fix reconstruction of SessionData datetime fields
- Fix reconstruction of IndexMetadata datetime fields
- Add validation in `load_project_state()`

**Provider Compatibility:**
- State management is completely provider-agnostic
- Works identically with Azure OpenAI, Gemini, or any future LLM provider
- Datetime handling is independent of which LLM generated the content
- Applies to all workflow phases (specification, design, tasks, implementation)

**Interface:**
```python
class StateManager:
    def _serialize_dataclass(self, obj: Any) -> Any:
        """Recursively serialize dataclass objects, handling datetime properly."""
        # Enhanced to check isinstance(obj, datetime) FIRST before other checks
        # Handles datetime in all nested structures (specs, design, tasks, session, index)
        
    def _deserialize_datetime(self, date_str: str | None) -> datetime | None:
        """Deserialize ISO format datetime string, handling None."""
        # Enhanced to return None if date_str is None
        # Used by all reconstruction methods
        
    def _reconstruct_specification(self, spec_dict: dict[str, Any]) -> SpecificationDocument:
        """Reconstruct SpecificationDocument, handling None approval_timestamp."""
        # Enhanced to check if approval_timestamp is None before deserializing
        
    def _reconstruct_design(self, design_dict: dict[str, Any]) -> DesignDocument:
        """Reconstruct DesignDocument, handling None approval_timestamp."""
        # Enhanced to check if approval_timestamp exists and is None before deserializing
        
    def _reconstruct_tasks(self, tasks_dict: dict[str, Any]) -> TaskList:
        """Reconstruct TaskList, handling None approval_timestamp."""
        # Enhanced to check if approval_timestamp exists and is None before deserializing
        
    def _reconstruct_project_state(self, state_dict: dict[str, Any]) -> ProjectState:
        """Reconstruct ProjectState with ALL datetime fields handled correctly."""
        # Enhanced to deserialize created_at, updated_at
        # Enhanced to deserialize session_data datetime fields
        # Enhanced to deserialize index_metadata datetime fields
        
    def load_project_state(self) -> ProjectState | None:
        """Load project state with validation and error recovery."""
        # Enhanced with try/except and detailed error messages
        # Works across all workflow phases
```

### 3. Enhanced Specification Parser

**File:** `dev_agent/generation/specification_generator.py`

**Changes:**
- Improve `_parse_ai_specification()` to handle variations in AI output
- Add validation after parsing to check requirement completeness
- Add warning messages for incomplete specifications
- Enhance regex patterns for requirement extraction

**Provider Compatibility:**
- Parser handles output from both Azure OpenAI and Gemini API
- Regex patterns are flexible enough to handle variations in formatting from different providers
- Validation logic is provider-agnostic (checks structure, not generation method)
- Both providers generate markdown-formatted specifications that the parser can handle

**Interface:**
```python
class SpecificationGenerator:
    def _parse_ai_specification(
        self,
        spec_content: str,
        analysis: SpecificationAnalysis | None,
    ) -> SpecificationDocument:
        """Parse AI-generated specification with enhanced validation."""
        # Enhanced with better regex patterns and validation
        # Works with output from any LLM provider
        
    def _validate_specification(self, spec: SpecificationDocument) -> tuple[bool, list[str]]:
        """Validate specification completeness (NEW METHOD)."""
        # Returns (is_valid, list_of_issues)
        # Provider-agnostic validation
```

### 4. Enhanced Specification Workflow

**File:** `dev_agent/workflow/specification_workflow.py`

**Changes:**
- Add validation after specification generation
- Display warnings to users for incomplete specifications
- Better error handling with Rich panels
- Offer to regenerate if specification is incomplete

**Provider Compatibility:**
- Workflow uses ILLMClient interface, supporting both Azure OpenAI and Gemini
- Validation and error handling work identically regardless of provider
- Cost tracking adapts to provider-specific token counting
- User experience is consistent across providers

**Interface:**
```python
class SpecificationWorkflow:
    async def _generate_from_existing_code(
        self, feature_description: str
    ) -> SpecificationDocument:
        """Generate specification with validation."""
        # Enhanced with post-generation validation
        # Works with any LLM provider through ILLMClient
        
    async def _generate_from_user_input(
        self, feature_description: str
    ) -> SpecificationDocument:
        """Generate specification with validation."""
        # Enhanced with post-generation validation
        # Works with any LLM provider through ILLMClient
```

### 5. Design Workflow Considerations

**File:** `dev_agent/workflow/design_workflow.py` (if exists)

**Changes:**
- Ensure design document approval saves state correctly with datetime serialization
- Validate design document completeness similar to specification
- Handle datetime fields in DesignDocument if approval_timestamp exists

**Provider Compatibility:**
- Same provider-agnostic approach as specification workflow
- Works with both Azure OpenAI and Gemini

### 6. Task Workflow Considerations

**File:** `dev_agent/workflow/task_workflow.py` (if exists)

**Changes:**
- Ensure task list approval saves state correctly with datetime serialization
- Validate task list completeness
- Handle datetime fields in TaskList if approval_timestamp exists

**Provider Compatibility:**
- Same provider-agnostic approach as specification workflow
- Works with both Azure OpenAI and Gemini

### 7. Phase Transition Handling

**All Workflow Files**

**Changes:**
- Ensure state is saved correctly after each phase approval
- Verify datetime serialization works during phase transitions
- Add logging for phase transitions to aid debugging
- Validate state can be loaded after each phase

**Critical Phase Transitions:**
1. **Indexing → Specification:** Save index_metadata with last_indexed datetime
2. **Specification → Design:** Save specification with approval_timestamp
3. **Design → Tasks:** Save design with approval_timestamp
4. **Tasks → Implementation:** Save tasks with approval_timestamp
5. **Any Phase → Resume:** Load state with all datetime fields correctly deserialized

## Data Models

### Datetime Handling in All Document Types

**Current Issue:**
```python
# Serialization creates datetime objects in dict (affects ALL phases)
state_dict = {
    "created_at": datetime(2024, 10, 9, 14, 30, 0),  # ❌ Not JSON serializable
    "updated_at": datetime(2024, 10, 9, 14, 35, 0),  # ❌ Not JSON serializable
    "specification": {
        "approval_timestamp": datetime(2024, 10, 9, 14, 35, 0)  # ❌ Not JSON serializable
    },
    "design": {
        "approval_timestamp": datetime(2024, 10, 9, 15, 00, 0)  # ❌ Not JSON serializable
    },
    "tasks": {
        "approval_timestamp": datetime(2024, 10, 9, 15, 30, 0)  # ❌ Not JSON serializable
    },
    "session_data": {
        "started_at": datetime(2024, 10, 9, 14, 00, 0),  # ❌ Not JSON serializable
        "last_activity": datetime(2024, 10, 9, 15, 30, 0)  # ❌ Not JSON serializable
    },
    "index_metadata": {
        "last_indexed": datetime(2024, 10, 9, 13, 00, 0)  # ❌ Not JSON serializable
    }
}
```

**Fixed Approach:**
```python
# Serialization converts ALL datetime fields to ISO strings
state_dict = {
    "created_at": "2024-10-09T14:30:00",  # ✅ JSON serializable
    "updated_at": "2024-10-09T14:35:00",  # ✅ JSON serializable
    "specification": {
        "approval_timestamp": "2024-10-09T14:35:00"  # ✅ JSON serializable
    },
    "design": {
        "approval_timestamp": "2024-10-09T15:00:00"  # ✅ JSON serializable
    },
    "tasks": {
        "approval_timestamp": "2024-10-09T15:30:00"  # ✅ JSON serializable
    },
    "session_data": {
        "started_at": "2024-10-09T14:00:00",  # ✅ JSON serializable
        "last_activity": "2024-10-09T15:30:00"  # ✅ JSON serializable
    },
    "index_metadata": {
        "last_indexed": "2024-10-09T13:00:00"  # ✅ JSON serializable
    }
}

# Deserialization converts back to datetime for ALL fields
state = ProjectState(
    created_at=datetime.fromisoformat("2024-10-09T14:30:00"),  # ✅ datetime object
    updated_at=datetime.fromisoformat("2024-10-09T14:35:00"),  # ✅ datetime object
    specification=SpecificationDocument(
        approval_timestamp=datetime.fromisoformat("2024-10-09T14:35:00")  # ✅ datetime object
    ),
    design=DesignDocument(
        approval_timestamp=datetime.fromisoformat("2024-10-09T15:00:00")  # ✅ datetime object
    ),
    tasks=TaskList(
        approval_timestamp=datetime.fromisoformat("2024-10-09T15:30:00")  # ✅ datetime object
    ),
    # ... and so on for all datetime fields
)
```

**Affected Document Types:**
1. **SpecificationDocument:** approval_timestamp
2. **DesignDocument:** approval_timestamp (if exists)
3. **TaskList:** approval_timestamp (if exists)
4. **ProjectState:** created_at, updated_at
5. **SessionData:** started_at, last_activity
6. **IndexMetadata:** last_indexed

### Specification Document Validation

**New Validation Model:**
```python
@dataclass
class SpecificationValidation:
    """Validation result for specification documents."""
    is_valid: bool
    issues: list[str]
    warnings: list[str]
    requirement_count: int
    has_introduction: bool
    has_key_features: bool
```

## Error Handling

### 1. Datetime Serialization Errors

**Strategy:**
- Check `isinstance(obj, datetime)` before attempting serialization
- Convert to ISO format string using `.isoformat()`
- Handle None values explicitly

**Error Messages:**
```python
try:
    state_dict = self._serialize_dataclass(state)
except Exception as e:
    logger.error(f"Error serializing project state: {e}")
    logger.error(f"Failed on field: {field_name}")  # Add field context
    raise
```

### 2. Datetime Deserialization Errors

**Strategy:**
- Check if value is None before calling `datetime.fromisoformat()`
- Provide clear error messages indicating which field failed
- Attempt recovery by using current datetime as fallback

**Error Messages:**
```python
def _deserialize_datetime(self, date_str: str | None) -> datetime | None:
    """Deserialize datetime with None handling."""
    if date_str is None:
        return None
    
    try:
        return datetime.fromisoformat(date_str)
    except (ValueError, TypeError) as e:
        logger.error(f"Failed to deserialize datetime: {date_str}")
        logger.error(f"Error: {e}")
        raise ValueError(f"Invalid datetime format: {date_str}") from e
```

### 3. Incomplete Specification Errors

**Strategy:**
- Validate specification after generation
- Display warnings to user with Rich panels
- Offer to regenerate or continue with incomplete spec

**Error Messages:**
```python
if req_count < 3:
    self.cli_interface.display_message(
        Panel(
            f"[yellow]Warning: Only {req_count} requirement(s) generated.[/yellow]\n\n"
            "A complete specification typically has 3-5 requirements.\n"
            "You may want to regenerate or provide more detailed feedback.",
            title="⚠️ Incomplete Specification",
            border_style="yellow",
        )
    )
```

### 4. State Loading Errors

**Strategy:**
- Catch specific exceptions (FileNotFoundError, JSONDecodeError, ValueError)
- Provide detailed error messages for each failure type
- Offer to create fresh state if loading fails

**Error Messages:**
```python
try:
    state = self.load_project_state()
except FileNotFoundError:
    logger.error("State file not found")
    raise ValueError("No existing project state found. Use start_new_project instead.")
except json.JSONDecodeError as e:
    logger.error(f"Corrupted state file: {e}")
    raise ValueError("Project state file is corrupted. Consider backing up and reinitializing.")
except ValueError as e:
    logger.error(f"Invalid state data: {e}")
    raise ValueError(f"Failed to load project state: {e}")
```

## Testing Strategy

### Unit Tests

**File:** `tests/test_state_manager_datetime.py` (NEW)

```python
def test_serialize_datetime():
    """Test datetime serialization to ISO format."""
    
def test_deserialize_datetime():
    """Test datetime deserialization from ISO format."""
    
def test_serialize_none_datetime():
    """Test None datetime values are preserved."""
    
def test_deserialize_none_datetime():
    """Test None datetime values are handled correctly."""
    
def test_specification_with_approval_timestamp():
    """Test specification with approval timestamp serialization."""
    
def test_specification_without_approval_timestamp():
    """Test specification without approval timestamp (None)."""
```

**File:** `tests/test_specification_generator_validation.py` (NEW)

```python
def test_validate_complete_specification():
    """Test validation passes for complete specification."""
    
def test_validate_incomplete_specification():
    """Test validation fails for incomplete specification."""
    
def test_parse_ai_specification_with_requirements():
    """Test parsing AI output with complete requirements."""
    
def test_parse_ai_specification_without_requirements():
    """Test parsing AI output with missing requirements."""
```

### Integration Tests

**File:** `tests/test_specification_workflow_integration.py` (ENHANCED)

```python
async def test_specification_approval_saves_state():
    """Test that approving specification saves state correctly."""
    
async def test_resume_project_after_approval():
    """Test resuming project after specification approval."""
    
async def test_incomplete_specification_warning():
    """Test that incomplete specifications trigger warnings."""
```

### Provider-Specific Tests

**File:** `tests/test_multi_provider_workflow.py` (NEW)

```python
@pytest.mark.parametrize("provider", [LLMProvider.AZURE_OPENAI, LLMProvider.GEMINI])
async def test_specification_generation_with_provider(provider):
    """Test specification generation works with both providers."""
    
@pytest.mark.parametrize("provider", [LLMProvider.AZURE_OPENAI, LLMProvider.GEMINI])
async def test_state_persistence_with_provider(provider):
    """Test state persistence works regardless of provider used."""
    
@pytest.mark.parametrize("provider", [LLMProvider.AZURE_OPENAI, LLMProvider.GEMINI])
async def test_validation_with_provider(provider):
    """Test validation works with output from both providers."""
```

### Manual Testing Checklist

#### Specification Phase Testing

1. **Create new project and generate specification (Azure OpenAI)**
   - Verify requirements section is complete
   - Verify at least 3-5 requirements are generated
   - Approve specification
   - Verify no datetime errors
   - Verify state saves correctly

2. **Create new project and generate specification (Gemini)**
   - Verify requirements section is complete
   - Verify at least 3-5 requirements are generated
   - Approve specification
   - Verify no datetime errors
   - Verify state saves correctly

3. **Resume project after specification approval (both providers)**
   - Verify project loads without errors
   - Verify approval timestamp is preserved
   - Verify all datetime fields are correct
   - Test with projects created by Azure OpenAI
   - Test with projects created by Gemini

#### Design Phase Testing

4. **Generate and approve design document**
   - Complete specification phase
   - Generate design document
   - Approve design
   - Verify no datetime errors during save
   - Verify state includes both specification and design approval timestamps

5. **Resume project after design approval**
   - Verify project loads with both specification and design
   - Verify both approval timestamps are preserved
   - Verify can continue to task phase

#### Task Phase Testing

6. **Generate and approve task list**
   - Complete specification and design phases
   - Generate task list
   - Approve tasks
   - Verify no datetime errors during save
   - Verify state includes all approval timestamps

7. **Resume project after task approval**
   - Verify project loads with specification, design, and tasks
   - Verify all approval timestamps are preserved
   - Verify can continue to implementation phase

#### Full Workflow Testing

8. **Complete end-to-end workflow**
   - Index codebase (verify last_indexed datetime)
   - Generate and approve specification (verify approval_timestamp)
   - Generate and approve design (verify approval_timestamp)
   - Generate and approve tasks (verify approval_timestamp)
   - Start implementation
   - Resume at each phase
   - Verify all datetime fields persist correctly

9. **Test with incomplete AI output (both providers)**
   - Mock AI to return incomplete specification
   - Verify warning is displayed
   - Verify user can regenerate or continue
   - Test with both Azure OpenAI and Gemini mocks

10. **Test state file corruption (provider-agnostic)**
    - Manually corrupt state file
    - Verify error message is clear
    - Verify recovery option is offered
    - Verify works regardless of which provider created the state

11. **Test provider switching across phases**
    - Create project with Azure OpenAI (specification phase)
    - Switch to Gemini for design phase
    - Switch back to Azure OpenAI for task phase
    - Verify state loads correctly at each transition
    - Verify all datetime fields are preserved

12. **Test session data datetime handling**
    - Start new session
    - Verify started_at is set correctly
    - Perform actions
    - Verify last_activity updates correctly
    - Resume session
    - Verify session datetime fields load correctly

## Implementation Notes

### Priority Order

1. **Fix datetime serialization** (CRITICAL - blocks ALL workflow phases)
   - Update `_serialize_dataclass()` in StateManager to check datetime FIRST
   - Ensure datetime objects are converted to ISO strings in ALL nested structures
   - Test with specification, design, tasks, session_data, and index_metadata
   - Verify works across all phase transitions

2. **Fix datetime deserialization** (CRITICAL - blocks project resumption at ANY phase)
   - Update `_deserialize_datetime()` to handle None values
   - Add None checks in `_reconstruct_specification()` for approval_timestamp
   - Add None checks in `_reconstruct_design()` for approval_timestamp (if exists)
   - Add None checks in `_reconstruct_tasks()` for approval_timestamp (if exists)
   - Fix SessionData datetime deserialization (started_at, last_activity)
   - Fix IndexMetadata datetime deserialization (last_indexed)
   - Update `_reconstruct_project_state()` for created_at and updated_at

3. **Test all phase transitions** (CRITICAL - ensures fixes work end-to-end)
   - Test indexing → specification transition
   - Test specification → design transition
   - Test design → tasks transition
   - Test tasks → implementation transition
   - Test resume at each phase

4. **Enhance prompt templates** (HIGH - improves specification quality)
   - Update SPECIFICATION_TEMPLATE system prompt
   - Update SPECIFICATION_NEW_PROJECT_TEMPLATE system prompt
   - Add validation instructions
   - Consider similar enhancements for design and task templates

5. **Add specification validation** (MEDIUM - improves user experience)
   - Implement `_validate_specification()` method
   - Add validation calls in workflow
   - Display warnings for incomplete specs
   - Consider similar validation for design and tasks

6. **Enhance error messages** (LOW - improves debugging)
   - Update error messages throughout all workflows
   - Add Rich panels for user-facing errors
   - Add detailed logging for debugging
   - Include phase context in error messages

### Backward Compatibility

- Existing state files with datetime objects will fail to load
- Provide clear error message explaining the issue
- Offer to reinitialize project state (user can manually backup if needed)
- No automatic migration - keep it simple

### Performance Considerations

- Datetime serialization/deserialization is fast (< 1ms per field)
- Validation adds minimal overhead (< 10ms)
- No impact on AI generation performance
- State file size unchanged

## Security Considerations

- No security implications for datetime handling
- State files remain local and not transmitted
- No sensitive data in datetime fields
- Validation does not expose internal state

## Deployment Strategy

Simple deployment - all fixes go together:
1. Fix datetime handling in state manager
2. Enhance prompt templates
3. Add validation logic
4. Improve error messages
5. Test thoroughly before merging

## Rollback Plan

- If issues arise, revert the entire change
- Users with corrupted state files can reinitialize
- Keep it simple - no complex migration

---

## Document Metadata

- **Version:** 1.0
- **Status:** Draft
- **Last Updated:** 2024-10-09
