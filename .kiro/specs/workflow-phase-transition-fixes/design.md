# Design Document

## Overview

This design addresses critical workflow issues in the dev-agent system by implementing automatic phase transitions, proper LLM client initialization throughout the workflow, user-driven specification generation, and AI-powered feedback incorporation. The solution focuses on improving the user experience by removing manual intervention requirements and ensuring that AI capabilities are properly utilized throughout the specification phase.

## Architecture

### Component Interactions

```
WorkflowManager
    ├── PhaseManager
    │   ├── execute_indexing_phase() → auto-transition
    │   └── execute_specification_phase() → with LLM client
    ├── SpecificationWorkflow
    │   ├── LLM Client (injected)
    │   ├── Cost Tracker (injected)
    │   ├── Token Counter (injected)
    │   └── Vector Database (injected)
    └── SpecificationGenerator
        ├── LLM Client (injected)
        ├── Cost Tracker (injected)
        ├── Token Counter (injected)
        └── Vector Database (injected)
```

### Key Design Decisions

1. **Automatic Phase Transitions**: After successful phase completion, automatically advance to the next phase without requiring user input like "skip"
2. **Dependency Injection**: Pass LLM client and related components through the entire workflow chain
3. **User-Driven Generation**: Always prompt for feature description before generating specifications
4. **AI-Powered Refinement**: Use LLM client to refine specifications based on user feedback

## Components and Interfaces

### 1. PhaseManager Enhancements

**Purpose**: Manage phase execution and automatic transitions

**Changes**:
- After `execute_indexing_phase()` completes successfully, automatically update project state to next phase
- Remove requirement for user to enter "skip" to proceed
- Pass LLM client, cost tracker, token counter, and vector database to SpecificationWorkflow

**Methods Modified**:
```python
def execute_indexing_phase(self, project_path: str) -> IndexingResult:
    # ... existing indexing logic ...
    
    if result.status == PhaseStatus.COMPLETED:
        # Auto-transition to specification phase
        project_state = self.state_manager.load_project_state()
        if project_state:
            project_state.current_phase = PhaseType.SPECIFICATION
            self.state_manager.save_project_state(project_state)
            self.cli_interface.display_message(
                "✅ Indexing complete! Moving to specification phase..."
            )
    
    return result

def execute_specification_phase(self, context: ProjectContext) -> SpecificationResult:
    # Initialize SpecificationWorkflow with all required components
    if not self.specification_workflow:
        self.specification_workflow = SpecificationWorkflow(
            cli_interface=self.cli_interface,
            codebase_analyzer=self.codebase_analyzer,
            state_manager=self.state_manager,
            llm_client=self.llm_client,  # NEW
            cost_tracker=self.cost_tracker,  # NEW
            token_counter=self.token_counter,  # NEW
            vector_db=self.vector_db,  # NEW
        )
```

### 2. SpecificationWorkflow Enhancements

**Purpose**: Orchestrate specification generation with proper AI integration

**Changes**:
- Accept LLM client, cost tracker, token counter, and vector database in constructor
- Pass all components to SpecificationGenerator
- Prompt user for feature description before generation
- Use AI-powered refinement for feedback

**Constructor**:
```python
def __init__(
    self,
    cli_interface: ICLIInterface,
    codebase_analyzer: ICodebaseAnalyzer | None = None,
    state_manager: StateManager | None = None,
    llm_client: ILLMClient | None = None,  # NEW
    cost_tracker: CostTracker | None = None,  # NEW
    token_counter: TokenCounter | None = None,  # NEW
    vector_db: VectorDatabase | None = None,  # NEW
):
    self.cli_interface = cli_interface
    self.codebase_analyzer = codebase_analyzer
    self.state_manager = state_manager
    self.llm_client = llm_client
    self.cost_tracker = cost_tracker
    self.token_counter = token_counter
    self.vector_db = vector_db
    
    # Initialize generator with all components
    self.generator = SpecificationGenerator(
        cli_interface=cli_interface,
        llm_client=llm_client,
        cost_tracker=cost_tracker,
        token_counter=token_counter,
        vector_db=vector_db,
    )
```

**Methods Modified**:
```python
def execute_specification_phase(self, project_path: str) -> SpecificationDocument:
    # Check LLM client availability
    if not self.llm_client:
        self.cli_interface.display_message(
            "❌ Azure OpenAI is not configured. Please run 'dev-agent azure configure'"
        )
        raise ValueError("LLM client required for specification generation")
    
    # Prompt user for feature description
    feature_description = self.cli_interface.get_user_input(
        "What feature would you like to build? Describe it in detail: "
    )
    
    if not feature_description.strip():
        self.cli_interface.display_message(
            "❌ Feature description is required"
        )
        raise ValueError("Feature description cannot be empty")
    
    # Generate specification using AI
    if self.codebase_analyzer and self._has_existing_code(project_path):
        analysis = self.codebase_analyzer.analyze_for_specification()
        spec = await self.generator.generate_from_existing_code_ai(
            analysis=analysis,
            feature_description=feature_description,
        )
    else:
        spec = await self.generator.generate_from_user_input_ai(
            feature_description=feature_description,
        )
    
    # Approval workflow with AI-powered refinement
    spec = await self._approval_workflow_ai(spec, feature_description)
    
    return spec

async def _approval_workflow_ai(
    self,
    spec: SpecificationDocument,
    feature_description: str,
) -> SpecificationDocument:
    current_spec = spec
    max_iterations = 3
    iteration = 0
    
    while iteration < max_iterations:
        iteration += 1
        
        # Request user approval
        approved = self.generator.request_user_approval(current_spec)
        
        if approved:
            return current_spec
        
        # Get feedback for refinement
        if iteration < max_iterations:
            feedback = self.cli_interface.get_user_input(
                "Please provide feedback for improving the specification: "
            )
            
            if feedback.strip():
                self.cli_interface.display_message(
                    "🤖 Refining specification using AI based on your feedback..."
                )
                
                # Use AI to refine specification
                current_spec = await self.generator.refine_specification_ai(
                    spec=current_spec,
                    feedback=feedback,
                    feature_description=feature_description,
                )
            else:
                current_spec.approved = True
                return current_spec
    
    current_spec.approved = True
    return current_spec
```

### 3. SpecificationGenerator Enhancements

**Purpose**: Generate and refine specifications using AI

**New Methods**:
```python
async def generate_from_user_input_ai(
    self,
    feature_description: str,
) -> SpecificationDocument:
    """Generate specification from user input using AI.
    
    For new projects without existing code, this generates a specification
    based solely on the user's feature description.
    """
    if not self.llm_client:
        raise ValueError("LLM client required for AI-powered generation")
    
    # Build context for new project
    context = {
        "feature_description": feature_description,
        "project_type": "new",
    }
    
    # Get template and generate
    template = get_template("specification_new_project")
    system_prompt, user_prompt = template.render(context, self.token_counter)
    
    spec_content = await self.llm_client.generate_completion(
        prompt=user_prompt,
        system_prompt=system_prompt,
        temperature=template.temperature,
        max_tokens=template.max_tokens,
    )
    
    # Parse and return
    return self._parse_ai_specification(spec_content, None)

async def refine_specification_ai(
    self,
    spec: SpecificationDocument,
    feedback: str,
    feature_description: str,
) -> SpecificationDocument:
    """Refine specification using AI based on user feedback.
    
    This method uses the LLM to understand the feedback and generate
    an improved version of the specification.
    """
    if not self.llm_client:
        raise ValueError("LLM client required for AI-powered refinement")
    
    # Build context for refinement
    current_spec_text = self.format_specification_document(spec)
    
    context = {
        "current_specification": current_spec_text,
        "user_feedback": feedback,
        "feature_description": feature_description,
    }
    
    # Get refinement template
    template = get_template("specification_refinement")
    system_prompt, user_prompt = template.render(context, self.token_counter)
    
    # Generate refined specification
    refined_content = await self.llm_client.generate_completion(
        prompt=user_prompt,
        system_prompt=system_prompt,
        temperature=template.temperature,
        max_tokens=template.max_tokens,
    )
    
    # Parse refined specification
    refined_spec = self._parse_ai_specification(refined_content, None)
    
    # Update version and reset approval
    refined_spec.version = self._increment_version(spec.version)
    refined_spec.approved = False
    refined_spec.approval_timestamp = None
    
    return refined_spec
```

### 4. WorkflowManager Enhancements

**Purpose**: Ensure LLM client and related components are available throughout workflow

**Changes**:
- Store LLM client, cost tracker, token counter, and vector database as instance variables
- Pass these components to PhaseManager during initialization

**Constructor Enhancement**:
```python
def __init__(
    self,
    cli_interface: ICLIInterface,
    embedding_client: IEmbeddingClient | None = None,
):
    # ... existing initialization ...
    
    # Initialize LLM components
    config = ConfigManager().get_config()
    
    if config.azure_openai:
        from ..llm.azure_client import AzureOpenAIClient
        from ..llm.cost_tracker import CostTracker
        from ..llm.token_counter import TokenCounter
        
        self.llm_client = AzureOpenAIClient(config.azure_openai)
        self.cost_tracker = CostTracker()
        self.token_counter = TokenCounter(model=config.azure_openai.deployment_name)
        
        # Initialize vector database if embedding client available
        if embedding_client:
            from ..indexing.vector_database import VectorDatabase
            index_path = Path(self.state_manager.project_path) / ".dev_agent" / "index"
            self.vector_db = VectorDatabase(
                index_path=index_path,
                embedding_client=embedding_client,
            )
    else:
        self.llm_client = None
        self.cost_tracker = None
        self.token_counter = None
        self.vector_db = None
    
    # Initialize phase manager with all components
    self.phase_manager = PhaseManager(
        cli_interface=cli_interface,
        state_manager=self.state_manager,
        embedding_client=embedding_client,
        cost_tracker=self.cost_tracker,
        llm_client=self.llm_client,  # NEW
        token_counter=self.token_counter,  # NEW
        vector_db=self.vector_db,  # NEW
    )
```

### 5. PhaseManager Constructor Enhancement

**Purpose**: Accept and store LLM components

**Changes**:
```python
def __init__(
    self,
    cli_interface: ICLIInterface,
    state_manager: StateManager,
    embedding_client: Any | None = None,
    cost_tracker: Any | None = None,
    llm_client: Any | None = None,  # NEW
    token_counter: Any | None = None,  # NEW
    vector_db: Any | None = None,  # NEW
):
    self.cli_interface = cli_interface
    self.state_manager = state_manager
    self.embedding_client = embedding_client
    self.cost_tracker = cost_tracker
    self.llm_client = llm_client
    self.token_counter = token_counter
    self.vector_db = vector_db
    
    # ... rest of initialization ...
```

## Data Models

### No Changes Required

The existing data models (SpecificationDocument, Requirement, etc.) are sufficient for this implementation.

## Error Handling

### LLM Client Not Available

```python
if not self.llm_client:
    self.cli_interface.display_message(
        Panel(
            "[red]Azure OpenAI is not configured.[/red]\n\n"
            "Please configure Azure OpenAI first:\n"
            "  [cyan]dev-agent azure configure[/cyan]",
            title="❌ Configuration Required",
            border_style="red"
        )
    )
    raise ValueError("LLM client required for specification generation")
```

### Empty Feature Description

```python
if not feature_description.strip():
    self.cli_interface.display_message(
        "❌ Feature description is required. Please describe what you want to build."
    )
    raise ValueError("Feature description cannot be empty")
```

### AI Generation Failures

```python
try:
    spec = await self.generator.generate_from_existing_code_ai(...)
except LLMError as e:
    self.cli_interface.display_message(
        f"❌ AI generation failed: {e}\n"
        "Please check your Azure OpenAI configuration and try again."
    )
    raise
```

## Testing Strategy

### Unit Tests

1. **Test Automatic Phase Transition**
   - Mock indexing completion
   - Verify project state updated to SPECIFICATION phase
   - Verify no user input required

2. **Test LLM Client Initialization**
   - Verify SpecificationWorkflow receives LLM client
   - Verify SpecificationGenerator receives all components
   - Verify no warnings about missing LLM client

3. **Test Feature Description Prompt**
   - Mock user input for feature description
   - Verify prompt is displayed
   - Verify empty input is rejected

4. **Test AI-Powered Refinement**
   - Mock LLM client responses
   - Verify feedback is incorporated
   - Verify refined specification differs from original

### Integration Tests

1. **End-to-End Workflow Test**
   - Initialize project
   - Complete indexing
   - Verify automatic transition
   - Provide feature description
   - Generate specification
   - Provide feedback
   - Verify refinement

2. **Error Handling Test**
   - Test with missing LLM client
   - Test with empty feature description
   - Test with AI generation failures

## Implementation Notes

1. **Async/Await**: All AI-powered methods must be async
2. **Backward Compatibility**: Keep existing rule-based methods for fallback
3. **Error Messages**: Provide clear, actionable error messages
4. **Progress Indicators**: Show progress during AI generation
5. **Cost Tracking**: Track and display API costs for transparency

