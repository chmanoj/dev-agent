# Integration Testing Guide

This document provides comprehensive instructions for manually testing dev-agent end-to-end workflows.

## Prerequisites

### Environment Setup

1. **Install dev-agent**:
   ```bash
   uv sync --dev
   ```

2. **Configure Azure OpenAI** (required for full testing):
   ```bash
   export AZURE_OPENAI_ENDPOINT="https://your-resource.openai.azure.com/"
   export AZURE_OPENAI_API_KEY="your-api-key"
   export AZURE_OPENAI_API_VERSION="2024-02-15-preview"
   export AZURE_OPENAI_DEPLOYMENT_NAME="gpt-4"
   export AZURE_OPENAI_EMBEDDING_DEPLOYMENT="text-embedding-ada-002"
   ```

3. **Enable integration tests**:
   ```bash
   export INTEGRATION_TESTS=true
   ```

## Test Scenarios

### 1. New Project Workflow (End-to-End)

#### 1.1 Setup Wizard
```bash
# Run setup wizard
uv run dev-agent setup

# Expected:
# - Welcome message displayed
# - Azure OpenAI configuration prompts
# - Connection test performed
# - Preferences saved to ~/.dev_agent_config
```

**Verification**:
- [ ] Setup wizard completes successfully
- [ ] Configuration file created at `~/.dev_agent_config`
- [ ] Azure OpenAI connection test passes
- [ ] User preferences saved correctly

#### 1.2 Initialize New Project
```bash
# Create new project directory
mkdir ~/test_new_project
cd ~/test_new_project

# Initialize dev-agent
uv run dev-agent init

# Expected:
# - .dev_agent/ directory created
# - state.json initialized
# - Welcome message for new project
```

**Verification**:
- [ ] `.dev_agent/` directory exists
- [ ] `state.json` file created
- [ ] Initial state is correct (NOT_STARTED)

#### 1.3 Scaffold from Template (Optional)
```bash
# List available templates
uv run dev-agent scaffold list

# Create project from template
uv run dev-agent scaffold create --template python-cli

# Expected:
# - Template files created
# - Project structure initialized
# - README.md generated
```

**Verification**:
- [ ] Template files created correctly
- [ ] Project structure matches template
- [ ] All required files present

#### 1.4 Generate Specification
```bash
# Generate specification for new feature
uv run dev-agent run --phase specification

# Expected:
# - Prompt for feature description
# - Specification generated
# - Saved to .dev_agent/documents/specification.md
# - Cost summary displayed
```

**Verification**:
- [ ] Specification file created
- [ ] Content is well-structured
- [ ] Includes requirements and acceptance criteria
- [ ] Cost tracking updated

#### 1.5 Generate Design
```bash
# Generate design document
uv run dev-agent run --phase design

# Expected:
# - Design document generated
# - References specification
# - Saved to .dev_agent/documents/design.md
# - Cost summary displayed
```

**Verification**:
- [ ] Design file created
- [ ] Architecture section present
- [ ] References specification correctly
- [ ] Cost tracking updated

#### 1.6 Generate Implementation Tasks
```bash
# Generate task list
uv run dev-agent run --phase implementation

# Expected:
# - Task list generated
# - Saved to .dev_agent/documents/tasks.md
# - Tasks are actionable and specific
# - Cost summary displayed
```

**Verification**:
- [ ] Tasks file created
- [ ] Tasks are well-defined
- [ ] Requirements referenced
- [ ] Cost tracking updated

#### 1.7 Check Status
```bash
# Check project status
uv run dev-agent status

# Expected:
# - Current phase displayed
# - Progress percentage shown
# - Cost information displayed
# - Next steps suggested
```

**Verification**:
- [ ] Status displays correctly
- [ ] All phases shown with status
- [ ] Cost information accurate
- [ ] Helpful next steps provided

---

### 2. Existing Codebase Workflow (End-to-End)

#### 2.1 Initialize with Existing Code
```bash
# Navigate to existing Python project
cd ~/existing_python_project

# Initialize dev-agent
uv run dev-agent init

# Expected:
# - Existing code detected
# - Indexing starts automatically
# - Progress bar displayed
# - Summary of indexed files
```

**Verification**:
- [ ] Existing code detected correctly
- [ ] Indexing completes successfully
- [ ] Progress displayed during indexing
- [ ] Summary shows file count and languages

#### 2.2 Indexing Phase
```bash
# If not auto-started, run indexing manually
uv run dev-agent run --phase indexing

# Expected:
# - Tree-sitter parsing of Python files
# - Embeddings generated via Azure OpenAI
# - FAISS vector database created
# - Patterns detected and summarized
# - Cost summary displayed
```

**Verification**:
- [ ] All Python files parsed
- [ ] Embeddings generated and cached
- [ ] Vector database created
- [ ] Patterns detected (classes, functions, imports)
- [ ] Cost tracking accurate

#### 2.3 Generate Specification from Code
```bash
# Generate specification based on existing code
uv run dev-agent run --phase specification

# Expected:
# - Codebase analyzed
# - Relevant code chunks retrieved
# - Specification generated with context
# - References existing patterns
# - Cost summary displayed
```

**Verification**:
- [ ] Specification reflects existing code
- [ ] Includes detected patterns
- [ ] References actual code examples
- [ ] Well-structured and comprehensive

#### 2.4 Generate Design from Codebase
```bash
# Generate design document
uv run dev-agent run --phase design

# Expected:
# - Architecture analysis performed
# - Design matches existing patterns
# - References codebase structure
# - Cost summary displayed
```

**Verification**:
- [ ] Design reflects existing architecture
- [ ] Consistent with codebase patterns
- [ ] Includes component diagrams
- [ ] References specification

#### 2.5 Generate Enhancement Tasks
```bash
# Generate implementation tasks
uv run dev-agent run --phase implementation

# Expected:
# - Tasks generated for enhancements
# - Match existing code style
# - Reference design and specification
# - Cost summary displayed
```

**Verification**:
- [ ] Tasks are context-aware
- [ ] Match existing code conventions
- [ ] Actionable and specific
- [ ] Reference requirements

---

### 3. CLI Commands Testing

#### 3.1 Help Commands
```bash
# General help
uv run dev-agent --help

# Command-specific help
uv run dev-agent init --help
uv run dev-agent run --help
uv run dev-agent status --help
```

**Verification**:
- [ ] Help text displays correctly
- [ ] All commands listed
- [ ] Options documented
- [ ] Examples provided

#### 3.2 Status Command
```bash
# Basic status
uv run dev-agent status

# Detailed status
uv run dev-agent status --detailed

# Expected:
# - Current phase shown
# - Progress percentage
# - Completed phases marked
# - Cost information
# - Last activity timestamp
```

**Verification**:
- [ ] Status displays correctly
- [ ] Progress accurate
- [ ] Cost information present
- [ ] Timestamps correct

#### 3.3 Cost Report Command
```bash
# Full cost report
uv run dev-agent cost-report

# Phase-specific cost
uv run dev-agent cost-report --phase indexing

# Export to JSON
uv run dev-agent cost-report --export cost_report.json

# Expected:
# - Token usage breakdown
# - Cost by phase
# - Total cost calculated
# - Export successful
```

**Verification**:
- [ ] Cost breakdown accurate
- [ ] Phase filtering works
- [ ] JSON export successful
- [ ] Budget warnings if applicable

#### 3.4 Validate Command
```bash
# Validate environment
uv run dev-agent validate

# Expected:
# - Azure OpenAI config checked
# - API connectivity tested
# - Dependencies verified
# - File permissions checked
# - Results displayed with suggestions
```

**Verification**:
- [ ] All checks performed
- [ ] Results clearly displayed
- [ ] Suggestions provided for failures
- [ ] Exit code correct

#### 3.5 Audit Command
```bash
# Run comprehensive audit
uv run dev-agent audit

# Expected:
# - All phases audited
# - Results displayed
# - Report saved to .dev_agent/audit_report.md
# - Recommendations provided
```

**Verification**:
- [ ] Audit completes successfully
- [ ] All components checked
- [ ] Report generated
- [ ] Recommendations actionable

#### 3.6 Cleanup Commands
```bash
# Scan for cleanup candidates
uv run dev-agent cleanup --scan

# Dry run
uv run dev-agent cleanup --dry-run

# Execute cleanup (with confirmation)
uv run dev-agent cleanup --execute

# Expected:
# - Cleanup plan generated
# - Dry run shows what would be removed
# - Confirmation prompt before execution
# - Backup created
# - Report generated
```

**Verification**:
- [ ] Scan identifies correct files
- [ ] Dry run doesn't remove anything
- [ ] Confirmation prompt works
- [ ] Backup created before cleanup
- [ ] Report accurate

---

### 4. Error Scenarios and Recovery

#### 4.1 Missing Configuration
```bash
# Unset Azure OpenAI config
unset AZURE_OPENAI_ENDPOINT
unset AZURE_OPENAI_API_KEY

# Try to run dev-agent
uv run dev-agent init

# Expected:
# - Clear error message
# - Configuration instructions
# - Link to setup wizard
# - Graceful exit
```

**Verification**:
- [ ] Error message clear and helpful
- [ ] Setup instructions provided
- [ ] No stack trace shown to user
- [ ] Exit code indicates error

#### 4.2 Invalid Project Path
```bash
# Try to initialize in non-existent directory
uv run dev-agent init /nonexistent/path

# Expected:
# - Path validation error
# - Helpful error message
# - Suggestion to create directory
# - Graceful exit
```

**Verification**:
- [ ] Path validation works
- [ ] Error message helpful
- [ ] Suggestions provided
- [ ] No crash

#### 4.3 Corrupted State File
```bash
# Corrupt state file
echo "{ invalid json }" > .dev_agent/state.json

# Try to resume
uv run dev-agent resume

# Expected:
# - Corruption detected
# - Recovery options offered
# - State reset or restored from backup
# - User informed of actions taken
```

**Verification**:
- [ ] Corruption detected
- [ ] Recovery mechanism works
- [ ] User informed clearly
- [ ] Project can continue

#### 4.4 API Timeout
```bash
# Simulate timeout (requires mock or actual timeout)
# Set very short timeout
export AZURE_OPENAI_TIMEOUT=1

# Try to generate specification
uv run dev-agent run --phase specification

# Expected:
# - Timeout detected
# - Retry attempted
# - User informed of retries
# - Graceful failure if all retries exhausted
```

**Verification**:
- [ ] Timeout handled gracefully
- [ ] Retries attempted
- [ ] User kept informed
- [ ] Helpful error message if fails

#### 4.5 Rate Limit Handling
```bash
# This requires actual rate limiting or mocking
# Try to make many rapid requests

# Expected:
# - Rate limit detected
# - Exponential backoff applied
# - User informed of wait time
# - Automatic retry after backoff
```

**Verification**:
- [ ] Rate limit detected
- [ ] Backoff strategy works
- [ ] User informed of delays
- [ ] Automatic recovery

---

### 5. Platform-Specific Testing

#### 5.1 macOS Testing
```bash
# Test on macOS
uname -a  # Verify macOS

# Run full workflow
cd ~/test_macos_project
uv run dev-agent init
uv run dev-agent run

# Test path handling
# Test file permissions
# Test environment variables
```

**Verification**:
- [ ] All commands work on macOS
- [ ] Path handling correct
- [ ] File permissions respected
- [ ] No platform-specific errors

#### 5.2 Linux Testing
```bash
# Test on Linux
uname -a  # Verify Linux

# Run full workflow
cd ~/test_linux_project
uv run dev-agent init
uv run dev-agent run

# Test path handling
# Test file permissions
# Test environment variables
```

**Verification**:
- [ ] All commands work on Linux
- [ ] Path handling correct
- [ ] File permissions respected
- [ ] No platform-specific errors

#### 5.3 Windows Testing
```powershell
# Test on Windows
systeminfo | findstr /B /C:"OS Name"

# Run full workflow
cd C:\test_windows_project
uv run dev-agent init
uv run dev-agent run

# Test path handling (backslashes vs forward slashes)
# Test file permissions
# Test environment variables
```

**Verification**:
- [ ] All commands work on Windows
- [ ] Path handling correct (pathlib handles this)
- [ ] File permissions respected
- [ ] No platform-specific errors

---

## Performance Testing

### Indexing Performance
```bash
# Test with large codebase (1000+ files)
cd ~/large_python_project

# Time the indexing
time uv run dev-agent run --phase indexing

# Expected:
# - Process at least 100 files/second
# - Progress updates smooth
# - Memory usage reasonable
# - No crashes or hangs
```

**Verification**:
- [ ] Indexing completes in reasonable time
- [ ] Performance meets targets (100+ files/sec)
- [ ] Memory usage acceptable
- [ ] No performance degradation

### Embedding Generation Performance
```bash
# Monitor embedding generation
uv run dev-agent run --phase indexing --verbose

# Expected:
# - Batch processing (16 items per batch)
# - Caching working (no re-computation)
# - Parallel processing where possible
```

**Verification**:
- [ ] Batching works correctly
- [ ] Cache hits reduce API calls
- [ ] Performance acceptable

---

## Regression Testing

### Test Previously Fixed Issues
```bash
# Test issues from previous tasks
# - Task 39: Test suite fixes
# - Task 38: Documentation validation
# - Task 37: Audit functionality
# - Task 36: Cleanup execution

# Run specific tests
uv run pytest tests/test_state_manager.py -v
uv run pytest tests/test_cleanup_manager.py -v
uv run pytest tests/test_audit_engine.py -v
```

**Verification**:
- [ ] All previously fixed issues still work
- [ ] No regressions introduced
- [ ] Tests pass consistently

---

## Documentation Verification

### Test Documentation Examples
```bash
# Test examples from documentation
# Follow examples in docs/getting-started/
# Follow examples in docs/usage/
# Follow examples in docs/examples/

# Verify all examples work as documented
```

**Verification**:
- [ ] All documentation examples work
- [ ] Output matches documentation
- [ ] No broken examples
- [ ] Documentation accurate

---

## Final Checklist

### Functionality
- [ ] New project workflow works end-to-end
- [ ] Existing codebase workflow works end-to-end
- [ ] All CLI commands function correctly
- [ ] Error handling works as expected
- [ ] Recovery mechanisms function properly

### Performance
- [ ] Indexing meets performance targets
- [ ] Embedding generation efficient
- [ ] CLI responsive (<100ms)
- [ ] State persistence fast (<100ms)

### Platform Compatibility
- [ ] Works on macOS
- [ ] Works on Linux
- [ ] Works on Windows
- [ ] No platform-specific issues

### Quality
- [ ] All tests pass
- [ ] Documentation accurate
- [ ] No regressions
- [ ] User experience smooth

### Security
- [ ] API keys never logged
- [ ] Credentials handled securely
- [ ] File permissions respected
- [ ] No security vulnerabilities

---

## Issue Reporting

If you encounter any issues during testing, document them with:

1. **Platform**: OS and version
2. **Steps to reproduce**: Exact commands run
3. **Expected behavior**: What should happen
4. **Actual behavior**: What actually happened
5. **Error messages**: Full error output
6. **Environment**: Python version, uv version, etc.

Create an issue in the project repository with this information.

---

## Automated Integration Test Execution

To run the automated integration tests:

```bash
# Enable integration tests
export INTEGRATION_TESTS=true

# Run integration tests
uv run pytest tests/integration/test_complete_workflows.py -v

# Run with coverage
uv run pytest tests/integration/test_complete_workflows.py --cov=dev_agent --cov-report=html

# Run specific test class
uv run pytest tests/integration/test_complete_workflows.py::TestNewProjectWorkflow -v
```

---

## Success Criteria

Integration testing is complete when:

1. ✅ All manual test scenarios pass
2. ✅ All automated integration tests pass
3. ✅ All platforms tested (macOS, Linux, Windows)
4. ✅ All error scenarios handled correctly
5. ✅ Performance targets met
6. ✅ Documentation verified
7. ✅ No critical issues found
8. ✅ User experience validated

---

## Next Steps

After successful integration testing:

1. Document any platform-specific issues found
2. Update documentation if needed
3. Create issues for any bugs found
4. Proceed to Task 41: Prepare release
