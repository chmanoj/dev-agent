# Implementation Plan

- [x] 1. Fix datetime serialization in StateManager
  - Update `_serialize_dataclass()` to check `isinstance(obj, datetime)` FIRST before other type checks
  - Convert datetime objects to ISO format strings using `.isoformat()`
  - Ensure recursive handling works for nested structures (specification, design, tasks, session_data, index_metadata)
  - Test serialization with all document types
  - _Requirements: 2.1, 2.2, 2.3, 2.4, 2.5_

- [-] 2. Fix datetime deserialization in StateManager
  - Update `_deserialize_datetime()` to handle None values by returning None immediately
  - Add None checks in `_reconstruct_specification()` before deserializing approval_timestamp
  - Add None checks in `_reconstruct_design()` before deserializing approval_timestamp (if field exists)
  - Add None checks in `_reconstruct_tasks()` before deserializing approval_timestamp (if field exists)
  - Fix SessionData datetime deserialization (started_at, last_activity) in `_reconstruct_project_state()`
  - Fix IndexMetadata datetime deserialization (last_indexed) in `_reconstruct_project_state()`
  - Fix ProjectState datetime deserialization (created_at, updated_at) in `_reconstruct_project_state()`
  - _Requirements: 3.1, 3.2, 3.3, 3.4, 3.5_

- [ ] 3. Enhance prompt templates for complete requirements generation
  - Update SPECIFICATION_TEMPLATE system prompt with explicit completeness requirements
  - Update SPECIFICATION_NEW_PROJECT_TEMPLATE system prompt with explicit completeness requirements
  - Add reference to `dev_agent/REQUIREMENTS_FORMAT_GUIDE.md` format in prompts
  - Emphasize minimum 3-5 requirements with complete user stories and acceptance criteria
  - Add validation instructions for AI to self-check output completeness
  - _Requirements: 1.1, 1.2, 1.3_

- [ ] 4. Improve specification parsing and validation
  - Enhance `_parse_ai_specification()` regex patterns to handle format variations
  - Add `_validate_specification()` method to check requirement completeness
  - Validate that each requirement has a user story and at least 2 acceptance criteria
  - Add logging for parsing failures with detailed error information
  - _Requirements: 1.4, 1.5, 4.1, 4.2, 4.3, 4.4, 4.5_

- [ ] 5. Add validation to specification workflow
  - Call `_validate_specification()` after generation in `_generate_from_existing_code()`
  - Call `_validate_specification()` after generation in `_generate_from_user_input()`
  - Display warning with Rich panel if specification has fewer than 3 requirements
  - Display requirement count to user after generation
  - _Requirements: 1.4, 5.1, 5.2, 5.3, 5.4, 5.5_

- [ ] 6. Enhance error handling and user feedback
  - Add detailed error messages for datetime serialization failures with field context
  - Add detailed error messages for datetime deserialization failures with field context
  - Add clear error messages for state loading failures (missing file, corrupted data, deserialization error)
  - Use Rich panels for user-facing error messages with appropriate colors
  - Add logging for all error scenarios with detailed context
  - _Requirements: 5.1, 5.2, 5.3, 5.4, 5.5_

- [ ] 7. Add state validation and recovery
  - Add validation in `load_project_state()` to check all required fields are present
  - Add try/except blocks with specific exception handling (FileNotFoundError, JSONDecodeError, ValueError)
  - Provide clear error messages explaining the type of failure
  - Offer to create fresh state if loading fails
  - Log validation errors with details for debugging
  - _Requirements: 6.1, 6.2, 6.3, 6.4, 6.5_

- [ ]* 8. Write unit tests for datetime handling
  - Create `tests/test_state_manager_datetime.py` with tests for datetime serialization
  - Test datetime serialization to ISO format
  - Test datetime deserialization from ISO format
  - Test None datetime values are preserved during serialization
  - Test None datetime values are handled correctly during deserialization
  - Test specification with approval_timestamp serialization
  - Test specification without approval_timestamp (None) serialization
  - Test design document datetime handling
  - Test task list datetime handling
  - Test session_data datetime handling
  - Test index_metadata datetime handling
  - _Requirements: 7.1, 7.2, 7.3, 7.4, 7.5_

- [ ]* 9. Write unit tests for specification validation
  - Create `tests/test_specification_generator_validation.py`
  - Test validation passes for complete specification (3+ requirements)
  - Test validation fails for incomplete specification (< 3 requirements)
  - Test parsing AI output with complete requirements
  - Test parsing AI output with missing requirements
  - Test parsing handles format variations gracefully
  - _Requirements: 7.1, 7.2, 7.3, 7.4, 7.5_

- [ ]* 10. Write integration tests for workflow phases
  - Enhance `tests/test_specification_workflow_integration.py`
  - Test specification approval saves state correctly with datetime
  - Test resume project after specification approval loads datetime correctly
  - Test incomplete specification triggers warning
  - Test design phase approval saves state correctly
  - Test task phase approval saves state correctly
  - Test full workflow end-to-end with all phase transitions
  - Test provider switching (Azure OpenAI ↔ Gemini) across phases
  - _Requirements: 7.1, 7.2, 7.3, 7.4, 7.5_

- [ ]* 11. Add provider-specific tests
  - Create `tests/test_multi_provider_workflow.py`
  - Test specification generation with Azure OpenAI provider
  - Test specification generation with Gemini provider
  - Test state persistence works with both providers
  - Test validation works with output from both providers
  - Test datetime handling is provider-agnostic
  - _Requirements: 7.1, 7.2, 7.3, 7.4, 7.5_

- [ ] 12. Manual testing and verification
  - Test complete workflow with Azure OpenAI (indexing → specification → design → tasks)
  - Test complete workflow with Gemini (indexing → specification → design → tasks)
  - Test resume at each phase with both providers
  - Test with incomplete AI output to verify warnings
  - Test state file corruption recovery
  - Test provider switching across phases
  - Verify all datetime fields persist and load correctly
  - Verify error messages are clear and helpful
  - _Requirements: 1.1, 1.2, 1.3, 1.4, 1.5, 2.1, 2.2, 2.3, 2.4, 2.5, 3.1, 3.2, 3.3, 3.4, 3.5_

---

## Notes

- Tasks 1-7 are core implementation tasks (REQUIRED)
- Tasks 8-11 are testing tasks (OPTIONAL but recommended)
- Task 12 is manual verification (REQUIRED before merging)
- All datetime fixes must work across ALL workflow phases (specification, design, tasks, implementation)
- All fixes must be provider-agnostic (work with both Azure OpenAI and Gemini)
- Focus on simplicity - no complex migration, just clear error messages and recovery options

## Task Dependencies

```
1 (datetime serialization) → 2 (datetime deserialization) → 7 (validation/recovery)
                                                          ↓
3 (prompt templates) → 4 (parsing/validation) → 5 (workflow validation) → 6 (error handling)
                                                                         ↓
                                                                    8, 9, 10, 11 (tests)
                                                                         ↓
                                                                    12 (manual testing)
```

## Estimated Effort

- Tasks 1-2: 2-3 hours (datetime handling is critical and needs careful testing)
- Tasks 3-5: 2-3 hours (prompt and validation enhancements)
- Tasks 6-7: 1-2 hours (error handling and recovery)
- Tasks 8-11: 3-4 hours (comprehensive testing)
- Task 12: 1-2 hours (manual verification)

**Total: 9-14 hours**

