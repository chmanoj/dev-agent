# Implementation Plan

- [x] 1. Update PhaseManager to support LLM components
  - Add llm_client, token_counter, and vector_db parameters to __init__
  - Store these components as instance variables
  - Update type hints and docstrings
  - _Requirements: 2.1, 2.2_

- [x] 2. Implement automatic phase transition after indexing
  - [x] 2.1 Modify execute_indexing_phase to update project state after completion
    - After successful indexing, load project state
    - Update current_phase to PhaseType.SPECIFICATION
    - Save updated project state
    - Display transition message to user
    - _Requirements: 1.1, 1.3_

  - [x] 2.2 Handle transition for skipped indexing (already up-to-date)
    - Apply same transition logic when index is current
    - Ensure consistent behavior for both paths
    - _Requirements: 1.4_

  - [x] 2.3 Display clear completion and transition messages
    - Show "✅ Indexing complete! Moving to specification phase..."
    - Ensure message is visible before transition
    - _Requirements: 1.2_

- [x] 3. Update SpecificationWorkflow to accept and use LLM components
  - [x] 3.1 Modify __init__ to accept LLM components
    - Add llm_client, cost_tracker, token_counter, vector_db parameters
    - Store as instance variables
    - Pass all components to SpecificationGenerator
    - Update docstrings
    - _Requirements: 2.1, 2.2_

  - [x] 3.2 Add LLM client validation in execute_specification_phase
    - Check if llm_client is None at start of phase
    - Display clear error message if missing
    - Raise ValueError with helpful message
    - _Requirements: 2.3, 2.4_

  - [x] 3.3 Add feature description prompt
    - Prompt user for feature description before generation
    - Validate that description is not empty
    - Display error if empty and re-prompt
    - _Requirements: 3.1, 3.2, 3.3_

  - [x] 3.4 Implement AI-powered specification generation path
    - Call generate_from_existing_code_ai for existing codebases
    - Call generate_from_user_input_ai for new projects
    - Pass feature_description to generation methods
    - Handle async/await properly
    - _Requirements: 3.4_

  - [x] 3.5 Implement AI-powered approval workflow
    - Create _approval_workflow_ai method (async)
    - Use AI refinement instead of rule-based refinement
    - Pass feature_description to refinement
    - Display progress messages during AI operations
    - _Requirements: 4.1, 4.2, 4.3, 4.4, 4.5_

- [ ] 4. Implement AI-powered specification generation methods
  - [ ] 4.1 Implement generate_from_user_input_ai in SpecificationGenerator
    - Accept feature_description parameter
    - Build context for new project template
    - Use "specification_new_project" template
    - Generate specification using LLM client
    - Parse AI response into SpecificationDocument
    - Handle errors gracefully
    - _Requirements: 3.1, 3.2, 3.3, 3.4_

  - [ ] 4.2 Implement refine_specification_ai in SpecificationGenerator
    - Accept spec, feedback, and feature_description parameters
    - Format current specification as text
    - Build refinement context
    - Use "specification_refinement" template
    - Generate refined specification using LLM
    - Parse refined response
    - Update version and reset approval status
    - _Requirements: 4.1, 4.2, 4.3, 4.4_

  - [ ] 4.3 Create prompt templates for new methods
    - Create specification_new_project template in prompt_templates.py
    - Create specification_refinement template in prompt_templates.py
    - Include clear instructions for AI
    - Set appropriate temperature and max_tokens
    - _Requirements: 3.4, 4.1, 4.2_

- [ ] 5. Update WorkflowManager to initialize and pass LLM components
  - [ ] 5.1 Initialize LLM client in WorkflowManager.__init__
    - Check if Azure OpenAI is configured
    - Create AzureOpenAIClient instance
    - Create CostTracker instance
    - Create TokenCounter instance
    - Handle missing configuration gracefully
    - _Requirements: 2.1, 2.2_

  - [ ] 5.2 Initialize VectorDatabase in WorkflowManager.__init__
    - Check if embedding_client is available
    - Create VectorDatabase instance with correct path
    - Handle missing embedding client gracefully
    - _Requirements: 2.1, 2.2_

  - [ ] 5.3 Pass LLM components to PhaseManager
    - Update PhaseManager initialization call
    - Pass llm_client, cost_tracker, token_counter, vector_db
    - Ensure all components are available
    - _Requirements: 2.1, 2.2_

- [ ] 6. Update PhaseManager.execute_specification_phase to pass components
  - Initialize SpecificationWorkflow with all LLM components
  - Pass llm_client, cost_tracker, token_counter, vector_db
  - Ensure components are available before initialization
  - _Requirements: 2.1, 2.2, 2.3_

- [ ] 7. Add error handling and user feedback
  - [ ] 7.1 Add clear error messages for missing LLM client
    - Use Rich Panel for formatted error display
    - Include instructions for configuration
    - Suggest running 'dev-agent azure configure'
    - _Requirements: 2.4, 5.4_

  - [ ] 7.2 Add progress indicators for AI operations
    - Display "🤖 Generating specification..." messages
    - Show "🤖 Refining specification..." during refinement
    - Display cost information after generation
    - _Requirements: 5.2, 5.3_

  - [ ] 7.3 Add validation for user inputs
    - Validate feature description is not empty
    - Validate feedback is not empty when provided
    - Display helpful prompts and instructions
    - _Requirements: 5.1, 5.5_

- [ ] 8. Update execute_specification_phase to be async
  - Change method signature to async def
  - Update all callers to use await
  - Ensure proper async/await throughout call chain
  - Handle async context properly
  - _Requirements: 3.4, 4.1, 4.2, 4.4_

- [ ] 9. Update CLI integration for async specification phase
  - Update workflow_manager calls to handle async
  - Use asyncio.run() or similar for async execution
  - Ensure proper event loop handling
  - Test in interactive mode
  - _Requirements: 3.4, 4.4_

- [ ]* 10. Add comprehensive tests
  - [ ]* 10.1 Unit test automatic phase transition
    - Mock indexing completion
    - Verify state update to SPECIFICATION
    - Verify no user input required
    - _Requirements: 1.1, 1.3, 1.4_

  - [ ]* 10.2 Unit test LLM component initialization
    - Verify components passed through workflow
    - Verify no warnings about missing client
    - Test with and without Azure OpenAI config
    - _Requirements: 2.1, 2.2, 2.3_

  - [ ]* 10.3 Unit test feature description prompt
    - Mock user input
    - Verify prompt displayed
    - Test empty input rejection
    - _Requirements: 3.1, 3.2_

  - [ ]* 10.4 Unit test AI-powered refinement
    - Mock LLM responses
    - Verify feedback incorporated
    - Verify specification changes
    - _Requirements: 4.1, 4.2, 4.3_

  - [ ]* 10.5 Integration test end-to-end workflow
    - Test complete workflow from init to specification
    - Verify automatic transitions
    - Test with real Azure OpenAI (optional, gated by env var)
    - _Requirements: 1.1, 2.1, 3.1, 4.1_

