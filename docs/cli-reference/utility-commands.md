# Utility Commands Reference

This document provides detailed information about dev-agent's utility commands including status reporting, validation, help, and maintenance operations. For workflow commands, see [Workflow Commands](workflow-commands.md). For a complete command reference, see [Commands](commands.md).

## Overview

Utility commands help you:

- Monitor project status and progress
- Validate configuration and environment
- Track costs and usage
- Get help and examples
- Perform maintenance tasks
- Manage configuration

## Status and Monitoring

### `dev-agent status`

Display project status and progress.

```bash
dev-agent status [PROJECT_PATH] [OPTIONS]
```

**Arguments:**
- `PROJECT_PATH` (optional): Project directory path (defaults to current directory)

**Options:**
- `--detailed`: Show detailed status information
- `--verbose, -v`: Enable verbose output

**What It Shows:**

1. **Current Phase**: Which workflow phase you're in
2. **Phase Progress**: Percentage complete for current phase
3. **Completed Phases**: Checkmarks for finished phases
4. **Cost Information**: Total cost and cost by phase
5. **Last Activity**: Timestamp of last operation
6. **Next Steps**: Guidance on what to do next

**Output Example:**

```
Project Status
──────────────────────────────────────────────

Project Path: /Users/dev/my-project
Current Phase: SPECIFICATION
Progress: 50%

Phase Status:
  ✓ Indexing      (Completed)
  ⟳ Specification (In Progress)
  ○ Design        (Not Started)
  ○ Implementation (Not Started)

Cost Summary:
  Indexing:       $0.1234
  Specification:  $0.0567
  Total:          $0.1801

Last Activity: 2024-01-15 10:30:45
Next Step: Complete specification and approve to proceed to design

Documents:
  ✓ .dev_agent/documents/specification.md (draft)
  ○ .dev_agent/documents/design.md
  ○ .dev_agent/documents/tasks.md
```

**Detailed Mode:**

With `--detailed` flag, shows additional information:

- Indexing statistics (files, chunks, embeddings)
- Token usage breakdown
- API call counts
- Cache hit rates
- Error history
- Configuration summary

**Examples:**

```bash
# Show status for current project
dev-agent status

# Show status for specific project
dev-agent status /path/to/project

# Show detailed status
dev-agent status --detailed

# Show status with verbose logging
dev-agent status --verbose
```

**Use Cases:**

- Check progress before stepping away
- Verify phase completion
- Monitor costs during development
- Troubleshoot workflow issues
- Share progress with team

---

### `dev-agent cost-report`

Generate detailed cost report for Azure OpenAI usage.

```bash
dev-agent cost-report [PROJECT_PATH] [OPTIONS]
```

**Arguments:**
- `PROJECT_PATH` (optional): Project directory path (defaults to current directory)

**Options:**
- `--phase PHASE`: Filter by specific phase (indexing, specification, design, implementation)
- `--export PATH`: Export report as JSON to specified path
- `--verbose, -v`: Enable verbose output

**What It Shows:**

1. **Token Usage**: Prompt tokens, completion tokens, embedding tokens
2. **Cost Breakdown**: Cost by phase and operation type
3. **API Calls**: Number of API calls made
4. **Efficiency Metrics**: Cache hit rate, average tokens per call
5. **Budget Status**: Warnings if approaching limits

**Output Example:**

```
Azure OpenAI Cost Report
──────────────────────────────────────────────

Project: /Users/dev/my-project
Report Date: 2024-01-15 10:30:45

Token Usage Summary
──────────────────────────────────────────────
Prompt Tokens:      12,345
Completion Tokens:   5,678
Embedding Tokens:   45,000
Total Tokens:       63,023

Cost Breakdown by Phase
──────────────────────────────────────────────
Indexing:           $0.1234  (45,000 tokens)
Specification:      $0.0567  (8,000 tokens)
Design:             $0.0890  (10,023 tokens)
Implementation:     $0.0000  (0 tokens)
──────────────────────────────────────────────
Total Cost:         $0.2691

Cost Breakdown by Operation
──────────────────────────────────────────────
Embeddings:         $0.1234  (45,000 tokens)
Completions:        $0.1457  (18,023 tokens)
──────────────────────────────────────────────
Total Cost:         $0.2691

API Call Statistics
──────────────────────────────────────────────
Total API Calls:    156
Embedding Calls:    125
Completion Calls:   31
Average Tokens/Call: 404

Efficiency Metrics
──────────────────────────────────────────────
Cache Hit Rate:     78%
Cached Embeddings:  975
New Embeddings:     275

Budget Status
──────────────────────────────────────────────
Status: ✓ Within Budget
Estimated Total:    $0.35 (projected)
```

**Phase Filtering:**

```bash
# Show costs for indexing phase only
dev-agent cost-report --phase indexing

# Show costs for specification phase
dev-agent cost-report --phase specification

# Show costs for design phase
dev-agent cost-report --phase design

# Show costs for implementation phase
dev-agent cost-report --phase implementation
```

**Export to JSON:**

```bash
# Export cost report as JSON
dev-agent cost-report --export cost-report.json

# Export with specific phase
dev-agent cost-report --phase indexing --export indexing-costs.json
```

**JSON Format:**

```json
{
  "project_path": "/Users/dev/my-project",
  "report_date": "2024-01-15T10:30:45Z",
  "token_usage": {
    "prompt_tokens": 12345,
    "completion_tokens": 5678,
    "embedding_tokens": 45000,
    "total_tokens": 63023
  },
  "cost_by_phase": {
    "indexing": 0.1234,
    "specification": 0.0567,
    "design": 0.0890,
    "implementation": 0.0000
  },
  "cost_by_operation": {
    "embeddings": 0.1234,
    "completions": 0.1457
  },
  "total_cost": 0.2691,
  "api_calls": {
    "total": 156,
    "embeddings": 125,
    "completions": 31
  },
  "efficiency": {
    "cache_hit_rate": 0.78,
    "cached_embeddings": 975,
    "new_embeddings": 275
  }
}
```

**Use Cases:**

- Track project costs
- Budget planning
- Optimize API usage
- Report to stakeholders
- Identify expensive operations

---

## Validation and Testing

### `dev-agent validate`

Validate environment and configuration.

```bash
dev-agent validate [OPTIONS]
```

**Options:**
- `--verbose, -v`: Enable verbose output

**What It Checks:**

1. **Azure OpenAI Configuration**
   - API key present
   - Endpoint URL valid
   - Deployment names configured
   - API version supported

2. **API Connectivity**
   - Network connectivity
   - Authentication success
   - Deployment accessibility
   - Model availability

3. **Dependencies**
   - Python version (>=3.10)
   - Required packages installed
   - Package versions compatible
   - Optional dependencies available

4. **File System**
   - `.dev_agent/` directory writable
   - Sufficient disk space
   - Proper permissions
   - No file system errors

5. **Configuration Files**
   - Config file valid YAML/JSON
   - No syntax errors
   - Required fields present
   - Values within valid ranges

**Output Example:**

```
Environment Validation
──────────────────────────────────────────────

Azure OpenAI Configuration
  ✓ API Key configured
  ✓ Endpoint URL valid
  ✓ Deployment name set
  ✓ Embedding deployment set
  ✓ API version supported

API Connectivity
  ✓ Network connectivity OK
  ✓ Authentication successful
  ✓ GPT-4 deployment accessible
  ✓ Embedding deployment accessible

Dependencies
  ✓ Python 3.11.5 (>= 3.10 required)
  ✓ openai 1.50.2 (>= 1.50.0 required)
  ✓ tiktoken 0.6.0 (>= 0.6.0 required)
  ✓ typer 0.15.0 (>= 0.15.0 required)
  ✓ rich 13.9.0 (>= 13.9.0 required)
  ✓ pydantic 2.10.0 (>= 2.10.0 required)
  ✓ faiss-cpu 1.9.0 (>= 1.9.0 required)

File System
  ✓ .dev_agent/ directory writable
  ✓ Sufficient disk space (45.2 GB free)
  ✓ Proper permissions
  ✓ No file system errors

Configuration Files
  ✓ Config file valid
  ✓ No syntax errors
  ✓ All required fields present
  ✓ Values within valid ranges

──────────────────────────────────────────────
✅ All validation checks passed!

Your environment is properly configured and ready to use.
```

**Error Example:**

```
Environment Validation
──────────────────────────────────────────────

Azure OpenAI Configuration
  ✗ API Key not configured
  ✓ Endpoint URL valid
  ✓ Deployment name set
  ⚠ Embedding deployment not set

API Connectivity
  ✗ Cannot connect - API key missing

Dependencies
  ✓ Python 3.11.5 (>= 3.10 required)
  ⚠ openai 1.45.0 (1.50.0 recommended)
  ✓ All other dependencies OK

──────────────────────────────────────────────
❌ Validation failed with 2 errors and 2 warnings

Errors:
  1. API Key not configured
     Solution: Run 'dev-agent azure configure' or set AZURE_OPENAI_API_KEY

  2. Cannot connect to Azure OpenAI
     Solution: Configure API key and test with 'dev-agent azure test'

Warnings:
  1. Embedding deployment not set
     Solution: Set via 'dev-agent azure configure'

  2. openai package version is outdated
     Solution: Run 'uv sync --upgrade' to update
```

**Examples:**

```bash
# Validate environment
dev-agent validate

# Validate with detailed output
dev-agent validate --verbose
```

**Use Cases:**

- Troubleshoot setup issues
- Verify installation
- Pre-flight check before starting work
- Diagnose configuration problems
- Ensure environment consistency

---

## Help and Documentation

### `dev-agent help`

Show help information.

```bash
dev-agent help [COMMAND]
```

**Arguments:**
- `COMMAND` (optional): Specific command to get help for

**Without Arguments:**

Shows general help with:
- Overview of dev-agent
- List of all commands
- Quick start guide
- Common workflows
- Links to documentation

**With Command:**

Shows detailed help for specific command:
- Command description
- Usage syntax
- Arguments and options
- Examples
- Related commands

**Examples:**

```bash
# Show general help
dev-agent help

# Show help for init command
dev-agent help init

# Show help for azure configure
dev-agent help azure configure

# Show help for cleanup scan
dev-agent help cleanup scan
```

**Alternative:**

You can also use `--help` flag:

```bash
dev-agent --help
dev-agent init --help
dev-agent azure configure --help
```

---

### `dev-agent examples`

Show common workflow examples.

```bash
dev-agent examples [WORKFLOW]
```

**Arguments:**
- `WORKFLOW` (optional): Specific workflow to show examples for
  - `new-project`: New project workflow
  - `existing`: Existing codebase workflow
  - `azure`: Azure OpenAI setup
  - `cost`: Cost management

**Without Arguments:**

Shows examples for all workflows:
- New project from scratch
- Analyzing existing codebase
- Azure OpenAI configuration
- Cost tracking and optimization
- Common troubleshooting scenarios

**With Workflow:**

Shows detailed examples for specific workflow with:
- Step-by-step instructions
- Expected output
- Common variations
- Troubleshooting tips

**Output Example:**

```
dev-agent Examples
──────────────────────────────────────────────

New Project Workflow
──────────────────────────────────────────────

1. Initial Setup
   $ dev-agent setup
   # Configure Azure OpenAI credentials

2. Initialize Project
   $ cd my-new-project
   $ dev-agent init
   # Creates .dev_agent/ structure

3. Start Interactive Mode
   $ dev-agent
   > I want to build a REST API for user management
   # AI generates specification

4. Review and Approve
   > approve
   # Proceeds to design phase

5. Continue Through Phases
   # Design → Implementation → Tasks

──────────────────────────────────────────────

Existing Codebase Workflow
──────────────────────────────────────────────

1. Navigate to Project
   $ cd my-existing-project

2. Initialize and Index
   $ dev-agent init
   # Automatically indexes codebase
   # Shows detected patterns

3. Generate Feature Spec
   $ dev-agent
   > Add JWT authentication to the API
   # AI analyzes existing code
   # Generates spec matching patterns

4. Review Generated Docs
   # Specification matches your code style
   # Design follows your architecture
   # Tasks reference existing patterns

──────────────────────────────────────────────

For more examples, visit:
https://github.com/yourusername/dev-agent/tree/main/examples
```

**Examples:**

```bash
# Show all examples
dev-agent examples

# Show new project examples
dev-agent examples new-project

# Show existing codebase examples
dev-agent examples existing

# Show Azure setup examples
dev-agent examples azure

# Show cost management examples
dev-agent examples cost
```

**Use Cases:**

- Learn dev-agent workflows
- Quick reference for commands
- Onboarding new team members
- Troubleshooting common issues
- Discover features

---

## Maintenance Commands

### `dev-agent audit`

Run comprehensive system audit.

```bash
dev-agent audit [OPTIONS]
```

**Options:**
- `--skip-azure`: Skip Azure OpenAI integration tests
- `--verbose, -v`: Enable verbose output

**What It Audits:**

1. **Indexing Phase**
   - Tree-sitter parsing
   - Embedding generation
   - FAISS vector storage
   - Pattern detection

2. **Specification Phase**
   - GPT-4 specification generation
   - Context retrieval
   - Document structure

3. **Design Phase**
   - Design document generation
   - Pattern matching
   - Architecture consistency

4. **Implementation Phase**
   - Task generation
   - Dependency ordering
   - Task actionability

5. **State Management**
   - State persistence
   - State loading
   - State integrity

6. **Azure OpenAI Integration**
   - API connectivity
   - Token counting
   - Cost tracking

7. **Error Handling**
   - Error scenarios
   - Graceful degradation
   - Error messages

**Output Example:**

```
dev-agent System Audit
──────────────────────────────────────────────

Running comprehensive audit...

Indexing Phase
  ✓ Tree-sitter parsing works
  ✓ Embedding generation successful
  ✓ FAISS vector storage functional
  ✓ Pattern detection accurate

Specification Phase
  ✓ GPT-4 generation works
  ✓ Context retrieval accurate
  ✓ Document structure valid

Design Phase
  ✓ Design generation works
  ✓ Pattern matching accurate
  ✓ Architecture consistency maintained

Implementation Phase
  ✓ Task generation works
  ✓ Dependencies ordered correctly
  ✓ Tasks are actionable

State Management
  ✓ State saves correctly
  ✓ State loads correctly
  ✓ State integrity maintained

Azure OpenAI Integration
  ✓ API connectivity OK
  ✓ Token counting accurate
  ✓ Cost tracking functional

Error Handling
  ✓ Errors handled gracefully
  ✓ Error messages helpful
  ✓ Recovery options provided

──────────────────────────────────────────────
✅ All audit checks passed! (28/28)

Audit report saved to: .dev_agent/audit_report.md
```

**Audit Report:**

Generates detailed markdown report with:
- Test results for each component
- Pass/fail status with details
- Recommendations for improvements
- Performance metrics
- Error logs if any

**Examples:**

```bash
# Run full audit
dev-agent audit

# Skip Azure OpenAI tests (faster)
dev-agent audit --skip-azure

# Run audit with verbose output
dev-agent audit --verbose
```

**Use Cases:**

- Verify installation
- Troubleshoot issues
- Pre-release testing
- Performance validation
- Quality assurance

---

## Configuration Management

### `dev-agent config show`

Show current configuration.

```bash
dev-agent config show
```

**What It Shows:**

- Azure OpenAI settings
- Indexing configuration
- Logging settings
- Workflow preferences
- Cost tracking settings

**Output Example:**

```
dev-agent Configuration
──────────────────────────────────────────────

Azure OpenAI
  Endpoint: https://my-resource.openai.azure.com/
  API Version: 2024-02-15-preview
  Deployment: gpt-4
  Embedding Deployment: text-embedding-ada-002
  Max Tokens: 4000
  Temperature: 0.7
  Max Retries: 3
  Timeout: 60s

Indexing
  Chunk Size: 1000
  Chunk Overlap: 200
  Use Azure Embeddings: true
  Batch Size: 16

Logging
  Level: INFO
  File: .dev_agent/logs/dev-agent.log
  Console: true

Workflow
  Auto Save: true
  Require Approval: true
  Cost Warnings: true
```

**Examples:**

```bash
# Show configuration
dev-agent config show
```

---

### `dev-agent config set`

Set configuration value.

```bash
dev-agent config set KEY VALUE
```

**Arguments:**
- `KEY`: Configuration key (dot notation for nested keys)
- `VALUE`: Configuration value

**Examples:**

```bash
# Set logging level
dev-agent config set logging.level DEBUG

# Set chunk size
dev-agent config set indexing.chunk_size 1500

# Set temperature
dev-agent config set azure_openai.temperature 0.8

# Enable cost warnings
dev-agent config set workflow.cost_warnings true
```

**Common Configuration Keys:**

| Key | Type | Description |
|-----|------|-------------|
| `logging.level` | string | Logging level (DEBUG, INFO, WARNING, ERROR) |
| `indexing.chunk_size` | int | Code chunk size for embeddings |
| `indexing.chunk_overlap` | int | Overlap between chunks |
| `indexing.batch_size` | int | Embedding batch size |
| `azure_openai.temperature` | float | GPT-4 temperature (0.0-2.0) |
| `azure_openai.max_tokens` | int | Max tokens per completion |
| `azure_openai.timeout` | int | API timeout in seconds |
| `workflow.auto_save` | bool | Auto-save state |
| `workflow.require_approval` | bool | Require phase approvals |
| `workflow.cost_warnings` | bool | Show cost warnings |

---

### `dev-agent config reset`

Reset configuration to defaults.

```bash
dev-agent config reset
```

**What It Resets:**

- Indexing settings
- Logging settings
- Workflow preferences
- Cost tracking settings

**What It Preserves:**

- Azure OpenAI credentials
- User preferences
- Project state

**Examples:**

```bash
# Reset configuration
dev-agent config reset
```

**Warning:** This will reset all custom settings to defaults. Azure OpenAI credentials are preserved.

---

## See Also

- [Commands Reference](commands.md) - Complete command reference
- [Workflow Commands](workflow-commands.md) - Workflow command details
- [CLI Examples](examples.md) - Practical examples
- [Configuration Guide](../configuration/azure-openai.md) - Configuration details
- [Troubleshooting Guide](../getting-started/troubleshooting.md) - Common issues
