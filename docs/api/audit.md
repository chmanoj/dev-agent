# Audit Module API Reference

The audit module provides comprehensive functionality verification for dev-agent, ensuring all core features work correctly.

## Overview

The audit system tests:

- **Indexing Phase**: Tree-sitter parsing, FAISS vector storage, Azure OpenAI embeddings
- **Specification Phase**: GPT-4 specification generation with codebase context
- **Design Phase**: Technical design document generation
- **Implementation Phase**: Task generation and breakdown
- **State Management**: State persistence and recovery
- **Azure OpenAI Integration**: API connectivity, token counting, cost tracking
- **Error Handling**: Graceful error handling and recovery

## Audit Engine

::: dev_agent.audit.audit_engine
    options:
      show_root_heading: true
      show_source: true
      members_order: source

## Audit Models

::: dev_agent.audit.models
    options:
      show_root_heading: true
      show_source: true
      members_order: source

## Usage Example

```python
from dev_agent.audit.audit_engine import AuditEngine
from pathlib import Path

# Create audit engine
engine = AuditEngine(project_path=Path("/path/to/project"))

# Run comprehensive audit
report = await engine.run_comprehensive_audit()

# Check results
if report.overall_status == "pass":
    print("All checks passed!")
else:
    print(f"Audit found issues: {report.summary}")
    for result in report.results:
        if result.status == "fail":
            print(f"Failed: {result.component} - {result.message}")

# Generate markdown report
report_path = engine.generate_audit_report()
print(f"Detailed report saved to: {report_path}")
```

## CLI Usage

```bash
# Run comprehensive audit
dev-agent audit

# Run audit with detailed output
dev-agent audit --detailed

# Save audit report to custom location
dev-agent audit --output /path/to/report.md
```

## Audit Results

Each audit check returns an `AuditResult` with:

- **component**: Name of the component being tested
- **status**: One of "pass", "fail", or "warning"
- **message**: Human-readable description of the result
- **details**: Additional diagnostic information
- **recommendations**: Suggested actions for failures
- **timestamp**: When the check was performed

## Audit Report

The comprehensive audit report includes:

- **Overall Status**: Pass/fail/warning for entire audit
- **Summary**: High-level overview of findings
- **Individual Results**: Detailed results for each check
- **Statistics**: Count of passed/failed/warning checks
- **Recommendations**: Prioritized list of actions to take
