# Integration Testing Quick Reference

Quick reference for running integration tests on dev-agent.

## Quick Start

### Run All Tests (Unix/Linux/macOS)
```bash
./scripts/run_integration_tests.sh
```

### Run All Tests (Windows)
```powershell
.\scripts\run_integration_tests.ps1
```

## Common Commands

### Skip Unit Tests
```bash
# Unix/Linux/macOS
./scripts/run_integration_tests.sh --skip-unit

# Windows
.\scripts\run_integration_tests.ps1 -SkipUnit
```

### Generate Coverage Report
```bash
# Unix/Linux/macOS
./scripts/run_integration_tests.sh --report

# Windows
.\scripts\run_integration_tests.ps1 -Report
```

### Run Only Integration Tests
```bash
# Unix/Linux/macOS
export INTEGRATION_TESTS=true
uv run pytest tests/integration/test_complete_workflows.py -v

# Windows
$env:INTEGRATION_TESTS = "true"
uv run pytest tests/integration/test_complete_workflows.py -v
```

## Manual Testing

### New Project Workflow
```bash
mkdir ~/test_project
cd ~/test_project
uv run dev-agent init
uv run dev-agent run --phase specification
uv run dev-agent run --phase design
uv run dev-agent run --phase implementation
uv run dev-agent status
```

### Existing Codebase Workflow
```bash
cd ~/existing_project
uv run dev-agent init
# Indexing starts automatically
uv run dev-agent run --phase specification
uv run dev-agent run --phase design
uv run dev-agent run --phase implementation
uv run dev-agent status
```

### Test CLI Commands
```bash
uv run dev-agent --help
uv run dev-agent status
uv run dev-agent cost-report
uv run dev-agent validate
uv run dev-agent audit
```

## Prerequisites

### Required Environment Variables
```bash
# Unix/Linux/macOS
export AZURE_OPENAI_ENDPOINT="https://your-resource.openai.azure.com/"
export AZURE_OPENAI_API_KEY="your-api-key"
export AZURE_OPENAI_API_VERSION="2024-02-15-preview"
export AZURE_OPENAI_DEPLOYMENT_NAME="gpt-4"
export AZURE_OPENAI_EMBEDDING_DEPLOYMENT="text-embedding-ada-002"

# Windows PowerShell
$env:AZURE_OPENAI_ENDPOINT = "https://your-resource.openai.azure.com/"
$env:AZURE_OPENAI_API_KEY = "your-api-key"
$env:AZURE_OPENAI_API_VERSION = "2024-02-15-preview"
$env:AZURE_OPENAI_DEPLOYMENT_NAME = "gpt-4"
$env:AZURE_OPENAI_EMBEDDING_DEPLOYMENT = "text-embedding-ada-002"
```

## Test Categories

| Category | Tests | Description |
|----------|-------|-------------|
| New Project | 3 | New project initialization and workflow |
| Existing Codebase | 3 | Existing code detection and analysis |
| CLI Commands | 4 | All CLI command functionality |
| Error Scenarios | 6 | Error handling and recovery |
| Platform | 4 | Cross-platform compatibility |
| State Management | 3 | Workflow state persistence |
| Document Generation | 3 | Specification, design, task generation |
| **Total** | **25** | **Complete integration coverage** |

## Platform-Specific Notes

### macOS
- ✅ Fully supported
- ✅ All terminal emulators work
- ✅ No known issues

### Linux
- ✅ Fully supported
- ✅ All major distributions tested
- ✅ No known issues

### Windows
- ⚠️ Use Windows Terminal (recommended)
- ⚠️ Use PowerShell 7+ for best experience
- ⚠️ Enable long path support if needed
- ✅ All core features work

## Troubleshooting

### Tests Skipped
**Problem**: All tests show as "SKIPPED"
**Solution**: Set `INTEGRATION_TESTS=true` environment variable

### Azure OpenAI Errors
**Problem**: Authentication or connection errors
**Solution**: Verify environment variables are set correctly

### Permission Errors
**Problem**: Cannot create files or directories
**Solution**: Check file permissions and ownership

### Import Errors
**Problem**: Module not found errors
**Solution**: Run `uv sync --dev` to install dependencies

## Documentation

- **Comprehensive Guide**: `INTEGRATION_TESTING_GUIDE.md`
- **Platform Issues**: `PLATFORM_SPECIFIC_ISSUES.md`
- **Task Summary**: `TASK_40_INTEGRATION_TESTING_SUMMARY.md`

## Success Criteria

Integration testing is successful when:
- ✅ All automated tests pass
- ✅ Manual workflows complete successfully
- ✅ No platform-specific errors
- ✅ Error handling works correctly
- ✅ Performance meets targets

## Getting Help

1. Check `INTEGRATION_TESTING_GUIDE.md` for detailed instructions
2. Check `PLATFORM_SPECIFIC_ISSUES.md` for platform-specific problems
3. Run `./scripts/run_integration_tests.sh --help` for script options
4. Report issues with platform, Python version, and error messages

---

**Last Updated**: 2025-01-04
