# Implementation Plan: Workflow State Persistence Fixes

## Overview
This implementation plan addresses critical bugs in workflow state persistence and document storage. The tasks are organized to fix state management, document saving, and approval tracking to ensure generated content persists correctly across sessions.

## Tasks

- [x] 1. Add approval tracking fields to ProjectState model
  - Modify `dev_agent/models/project_state.py` to add three boolean fields: `specification_approved`, `design_approved`, and `tasks_approved`
  - Set default values to `False` for all approval fields
  - Ensure backward compatibility with existing state files
  - _Requirements: REQ-3.1, REQ-3.2, REQ-3.3_

- [x] 2. Update StateManager serialization to include approval flags
  - Modify `_serialize_dataclass()` in `dev_agent/state/state_manager.py` to serialize approval flags
  - Use `getattr()` with default `False` for backward compatibility
  - Ensure approval flags are included in the state dictionary
  - _Requirements: REQ-3.4, REQ-5.2_

- [x] 3. Update StateManager deserialization to load approval flags
  - Modify `load_project_state()` in `dev_agent/state/state_manager.py` to deserialize approval flags
  - Use `.get()` with default `False` for backward compatibility with old state files
  - Ensure approval flags are properly restored when loading state
  - _Requirements: REQ-3.4, REQ-5.3_

- [x] 4. Implement state validation for approval consistency
  - Add validation checks in `_validate_state()` method to verify approval consistency
  - Check that design phase has approved specification
  - Check that implementation phase has approved design
  - Check that approved content exists (no approval without content)
  - Log warnings for inconsistencies but allow save to proceed
  - _Requirements: REQ-5.1, REQ-5.4_

- [x] 5. Implement document saving to filesystem
  - Create `_save_document_to_file()` method in `dev_agent/workflow/workflow_manager.py`
  - Ensure `.dev_agent/documents/` directory exists
  - Map phase types to filenames: specification.md, design.md, tasks.md
  - Write documents with UTF-8 encoding
  - Create timestamped backups before overwriting existing files
  - Handle write errors gracefully with proper logging
  - _Requirements: REQ-2.1, REQ-2.2, REQ-2.3, REQ-2.4, REQ-2.5, REQ-2.6_

- [ ] 6. Implement approval recording in workflow manager
  - Create `_record_approval()` method in `dev_agent/workflow/workflow_manager.py`
  - Set appropriate approval flag based on phase type
  - Save state immediately after recording approval
  - Log approval recording for debugging
  - _Requirements: REQ-3.1, REQ-3.2, REQ-3.3, REQ-3.4_

- [ ] 7. Update phase transition to save content to state
  - Modify `transition_to_phase()` in `dev_agent/workflow/workflow_manager.py`
  - Create `_update_state_with_content()` helper method
  - Save specification content to `state.specification` after generation
  - Save design content to `state.design` after generation
  - Save tasks to `state.tasks` after generation
  - Call `state_manager.save_project_state()` immediately after content update
  - _Requirements: REQ-1.1, REQ-1.2, REQ-1.3_

- [ ] 8. Integrate document saving into phase transition workflow
  - Call `_save_document_to_file()` after content is saved to state
  - Ensure document saving happens before requesting user approval
  - Log document save operations
  - Continue workflow even if document save fails (state has content)
  - _Requirements: REQ-2.1, REQ-2.2, REQ-2.3, REQ-2.4_

- [ ] 9. Integrate approval recording into phase transition workflow
  - Call `_record_approval()` after user approves content
  - Save state immediately after approval is recorded
  - Ensure approval is persisted before phase transition completes
  - _Requirements: REQ-3.4, REQ-3.5_

- [ ] 10. Update phase transition validation to check approvals
  - Modify `_validate_phase_transition()` or create `validate_phase_transition()` method
  - Check that specification exists and is approved before allowing design phase
  - Check that design exists and is approved before allowing implementation phase
  - Return clear error messages when validation fails
  - _Requirements: REQ-3.5, REQ-5.1_

- [ ] 11. Fix document type recognition in state manager
  - Review document type mapping in state manager
  - Ensure phase types map correctly to document types
  - Remove or fix "Unknown document type" warnings
  - Use consistent naming between workflow phases and document types
  - _Requirements: REQ-4.1, REQ-4.2, REQ-4.3, REQ-4.4, REQ-4.5_

- [ ] 12. Add comprehensive error handling for document operations
  - Use existing `DocumentSaveError` exception for document write failures
  - Add proper error context with file paths and phase information
  - Log errors with appropriate severity levels
  - Provide actionable error messages to users
  - _Requirements: REQ-2.6, REQ-5.5_

- [ ] 13. Verify atomic state saves prevent corruption
  - Confirm temp file + rename pattern is working correctly
  - Ensure state validation happens before write
  - Verify cleanup of temp files on error
  - Test state consistency across save/load cycles
  - _Requirements: REQ-5.1, REQ-5.2, REQ-5.3, REQ-5.5_

- [ ]* 14. Add unit tests for approval tracking
  - Test approval flag serialization and deserialization
  - Test approval recording for each phase type
  - Test state validation with various approval states
  - Test backward compatibility with old state files without approval flags
  - _Requirements: REQ-3.1, REQ-3.2, REQ-3.3, REQ-3.4_

- [ ]* 15. Add unit tests for document saving
  - Test document directory creation
  - Test document file writing with various content sizes
  - Test backup creation before overwrite
  - Test error handling for write failures
  - Test filename mapping for each phase
  - _Requirements: REQ-2.1, REQ-2.2, REQ-2.3, REQ-2.4, REQ-2.5, REQ-2.6_

- [ ]* 16. Add integration tests for complete workflow
  - Test specification generation → state save → document save → approval
  - Test design generation → state save → document save → approval
  - Test tasks generation → state save → document save → approval
  - Test phase transitions with approval validation
  - Test state consistency across full workflow
  - _Requirements: REQ-1, REQ-2, REQ-3, REQ-5_

- [ ] 17. Run end-to-end test with create_login_page.py
  - Execute `create_login_page.py` test script
  - Verify all documents are created in `.dev_agent/documents/`
  - Verify `state.json` contains all generated content
  - Verify approval flags are set correctly
  - Verify no "Unknown document type" warnings appear
  - Verify phase transitions work without errors
  - _Requirements: All requirements_

- [ ] 18. Update documentation for state structure
  - Document new approval fields in ProjectState
  - Document document saving behavior
  - Document phase transition validation rules
  - Add troubleshooting guide for state issues
  - _Requirements: REQ-5_

## Notes

- Tasks 1-13 are core implementation tasks that must be completed
- Tasks 14-16 are optional testing tasks (marked with *)
- Task 17 is the acceptance test that validates all fixes
- Task 18 is documentation (can be done in parallel with implementation)
- Each task builds on previous tasks - follow the order for best results
- State manager already has atomic write support - verify it works correctly
- Error exception classes already exist - reuse them for consistency
- Backward compatibility is critical - use getattr() and .get() with defaults

## Success Criteria

✅ All generated documents exist in `.dev_agent/documents/`
✅ `state.json` contains specification, design, and tasks content
✅ `state.json` contains approval flags for all phases
✅ Phase transitions validate approvals correctly
✅ No "Unknown document type" warnings in logs
✅ State remains consistent across save/load cycles
✅ `create_login_page.py` test completes successfully
