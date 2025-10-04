# CLI Commands Reference

This document provides a comprehensive reference for all dev-agent CLI commands. For workflow-specific commands, see [Workflow Commands](workflow-commands.md). For utility commands, see [Utility Commands](utility-commands.md). For practical examples, see [CLI Examples](examples.md).

## Overview

dev-agent provides a rich command-line interface organized into logical command groups:

- **Core Commands**: Project initialization, resumption, and interactive mode
- **Workflow Commands**: Phase execution and workflow management
- **Azure Commands**: Azure OpenAI configuration and testing
- **Utility Commands**: Status, validation, help, and examples
- **Maintenance Commands**: Audit, cleanup, and cost reporting
- **Configuration Commands**: Configuration management
- **Scaffolding Commands**: Project templates and scaffolding

## Command Structure

All dev-agent commands follow this pattern:

```bash
dev-agent [COMMAND] [SUBCOMMAND] [OPTIONS] [ARGUMENTS]
```

### Global Options

These options are available for all commands:

| Option | Short | Description |
|--------|-------|-------------|
| `--verbose` | `-v` | Enable verbose output with detailed logging |
| `--debug` | | Enable debug logging for troubleshooting |
| `--config-path` | | Path to custom configuration file |
| `--version` | | Show version information and exit |
| `--help` | | Show help message and exit |

## Core Commands

### `dev-agent`

Start interactive mode in the current directory.

```bash
dev-agent [PROJECT_PATH] [OPTIONS]
```

**Arguments:**
- `PROJECT_PATH` (optional): Project directory path (defaults to current directory)

**Options:**
- `--verbose, -v`: Enable verbose output
- `--debug`: Enable debug logging

**Description:**
When invoked without a command, dev-agent starts interactive mode where you can chat with the AI assistant and execute workflow phases interactively.

**Examples:**
```bash
# Start interactive mode in current directory
dev-agent

# Start interactive mode in specific directory
dev-agent /path/to/project

# Start with verbose output
dev-agent --verbose
```

---

### `dev-agent init`

Initialize a new dev-agent project.

```bash
dev-agent init [PROJECT_PATH] [OPTIONS]
```

**Arguments:**
- `PROJECT_PATH` (optional): Project directory path (defaults to current directory)

**Options:**
- `--verbose, -v`: Enable verbose output
- `--debug`: Enable debug logging

**Description:**
Initializes dev-agent for a project directory. Detects whether this is a new or existing project and provides appropriate guidance. For new projects, offers template selection. For existing codebases, automatically indexes the code.

**What it does:**
1. Detects if this is a new or existing project
2. Guides you through setup if not configured
3. Offers template selection for new projects
4. Indexes existing code for existing projects
5. Creates the `.dev_agent/` directory structure

**Examples:**
```bash
# Initialize in current directory
dev-agent init

# Initialize specific directory
dev-agent init /path/to/project

# Initialize with verbose output
dev-agent init --verbose

# Initialize with debug logging
dev-agent init --debug
```

**Next Steps:**
- For new projects: Use interactive mode to create specifications
- For existing projects: Use `dev-agent resume` to continue workflow

---

### `dev-agent resume`

Resume an existing dev-agent project.

```bash
dev-agent resume [PROJECT_PATH] [OPTIONS]
```

**Arguments:**
- `PROJECT_PATH` (optional): Project directory path (defaults to current directory)

**Options:**
- `--verbose, -v`: Enable verbose output
- `--debug`: Enable debug logging

**Description:**
Loads a previously initialized dev-agent project and continues from where you left off. The project state is automatically restored, including the current phase, generated documents, and workflow progress.

**What it does:**
1. Loads project state from `.dev_agent/`
2. Displays current phase and progress
3. Starts interactive mode to continue workflow
4. Restores all previous context and documents

**Examples:**
```bash
# Resume project in current directory
dev-agent resume

# Resume specific project
dev-agent resume /path/to/project

# Resume with verbose output
dev-agent resume --verbose
```

**Error Handling:**
If the project hasn't been initialized, you'll see an error suggesting to use `dev-agent init` first.

---

### `dev-agent interactive`

Start interactive mode (same as running `dev-agent` without arguments).

```bash
dev-agent interactive [PROJECT_PATH] [OPTIONS]
```

**Arguments:**
- `PROJECT_PATH` (optional): Project directory path (defaults to current directory)

**Options:**
- `--verbose, -v`: Enable verbose output
- `--debug`: Enable debug logging

**Description:**
Explicitly starts interactive mode. This is the same as running `dev-agent` without any command.

---

## Setup and Configuration

### `dev-agent setup`

Run interactive setup wizard or display setup status.

```bash
dev-agent setup [OPTIONS]
```

**Options:**
- `--status`: Display current setup status instead of running wizard
- `--verbose, -v`: Enable verbose output

**Description:**
The setup wizard guides you through initial configuration including Azure OpenAI credentials, connection testing, workflow overview, and next steps guidance.

**What it configures:**
- Azure OpenAI endpoint and API key
- Deployment names for GPT-4 and embeddings
- Connection testing to verify configuration
- User preferences and first-run settings

**Examples:**
```bash
# Run setup wizard
dev-agent setup

# Check setup status
dev-agent setup --status

# Run setup with verbose output
dev-agent setup --verbose
```

**Setup Status:**
The `--status` flag shows:
- Azure OpenAI configuration status
- User preferences status
- First-run completion status
- Overall readiness

---

### `dev-agent validate`

Validate environment and configuration.

```bash
dev-agent validate [OPTIONS]
```

**Options:**
- `--verbose, -v`: Enable verbose output

**Description:**
Performs comprehensive validation of your dev-agent environment including Azure OpenAI configuration, API connectivity, required dependencies, and file system permissions.

**What it checks:**
1. Azure OpenAI configuration completeness
2. API connectivity and authentication
3. Required Python dependencies
4. File system permissions for `.dev_agent/` directory
5. Configuration file validity

**Examples:**
```bash
# Validate environment
dev-agent validate

# Validate with detailed output
dev-agent validate --verbose
```

**Validation Results:**
- ✅ All checks passed: Ready to use
- ⚠️ Warnings: May work but with limitations
- ❌ Errors: Must be fixed before use

---

## Azure OpenAI Commands

All Azure OpenAI configuration commands are under the `azure` command group.

### `dev-agent azure configure`

Configure Azure OpenAI settings.

```bash
dev-agent azure configure [OPTIONS]
```

**Options:**
- `--api-key TEXT`: Azure OpenAI API key
- `--endpoint TEXT`: Azure OpenAI endpoint URL
- `--api-version TEXT`: Azure OpenAI API version
- `--deployment-name TEXT`: GPT-4 deployment name
- `--embedding-deployment TEXT`: Embedding model deployment name
- `--interactive/--no-interactive`: Interactive configuration (default: interactive)

**Description:**
Provides an interactive wizard to configure Azure OpenAI credentials and settings. Validates all inputs and can optionally test the connection after configuration.

**Examples:**
```bash
# Interactive configuration (recommended)
dev-agent azure configure

# Non-interactive configuration
dev-agent azure configure --no-interactive \
    --api-key "your-key" \
    --endpoint "https://your-resource.openai.azure.com/" \
    --deployment-name "gpt-4" \
    --embedding-deployment "text-embedding-ada-002"
```

**Security Notice:**
- API keys are stored in configuration files
- Consider using environment variables for production
- Never commit API keys to version control
- Use Azure Key Vault for sensitive deployments

---

### `dev-agent azure test`

Test Azure OpenAI connection.

```bash
dev-agent azure test
```

**Description:**
Tests both completion and embedding endpoints to ensure your Azure OpenAI configuration is working correctly.

**What it tests:**
1. API authentication
2. Deployment accessibility
3. Model availability
4. Network connectivity
5. Embedding generation
6. Response quality

**Examples:**
```bash
# Test Azure OpenAI connection
dev-agent azure test
```

**Test Results:**
- ✅ All tests passed: Configuration is working
- ⚠️ Partial failure: Some tests failed
- ❌ All tests failed: Configuration needs fixing

---

### `dev-agent azure status`

Show Azure OpenAI configuration status.

```bash
dev-agent azure status
```

**Description:**
Displays current Azure OpenAI configuration including endpoint, deployment names, and settings. API keys are masked for security.

**Examples:**
```bash
# Show Azure OpenAI status
dev-agent azure status
```

**Status Display:**
- Configuration values (API key masked)
- Deployment names
- Model settings (max tokens, temperature, etc.)
- Overall configuration status

---

### `dev-agent azure models`

List available Azure OpenAI models.

```bash
dev-agent azure models
```

**Description:**
Lists common Azure OpenAI models including chat models (GPT-4, GPT-3.5) and embedding models (text-embedding-ada-002).

**Examples:**
```bash
# List available models
dev-agent azure models
```

**Note:** Model availability depends on your Azure OpenAI deployment and region.

---

### `dev-agent azure env`

Show required environment variables.

```bash
dev-agent azure env
```

**Description:**
Displays all Azure OpenAI environment variables, their descriptions, current values, and status.

**Environment Variables:**
- `AZURE_OPENAI_API_KEY`: Your Azure OpenAI API key (required)
- `AZURE_OPENAI_ENDPOINT`: Your Azure OpenAI endpoint URL (required)
- `AZURE_OPENAI_API_VERSION`: API version (optional)
- `AZURE_OPENAI_DEPLOYMENT_NAME`: GPT-4 deployment name (optional)
- `AZURE_OPENAI_EMBEDDING_DEPLOYMENT`: Embedding deployment name (optional)

**Examples:**
```bash
# Show environment variables
dev-agent azure env
```

---

### `dev-agent azure export`

Export Azure OpenAI configuration to a file.

```bash
dev-agent azure export [OPTIONS]
```

**Options:**
- `--output, -o PATH`: Output file path (default: `azure_openai_config.json`)
- `--include-secrets`: Include API key in export (NOT RECOMMENDED)

**Description:**
Exports your Azure OpenAI configuration to a JSON file. By default, API keys are NOT included for security reasons.

**Examples:**
```bash
# Export without API key (recommended)
dev-agent azure export

# Export to specific file
dev-agent azure export --output my-config.json

# Export with API key (use with caution)
dev-agent azure export --include-secrets
```

**Security Warning:**
When using `--include-secrets`:
- File contains API key in plain text
- Do NOT commit to version control
- Do NOT share publicly
- Store securely and delete after use

---

### `dev-agent azure import`

Import Azure OpenAI configuration from a file.

```bash
dev-agent azure import INPUT_FILE [OPTIONS]
```

**Arguments:**
- `INPUT_FILE`: Path to configuration JSON file

**Options:**
- `--merge`: Merge with existing configuration instead of replacing

**Description:**
Imports Azure OpenAI configuration from a JSON file. You can either replace the entire configuration or merge with existing settings.

**Examples:**
```bash
# Import and replace configuration
dev-agent azure import azure_openai_config.json

# Import and merge with existing
dev-agent azure import azure_openai_config.json --merge
```

---

## Help and Documentation

### `dev-agent help`

Show help information.

```bash
dev-agent help [COMMAND]
```

**Arguments:**
- `COMMAND` (optional): Specific command to get help for

**Description:**
Displays help information for dev-agent commands. Without arguments, shows general help. With a command name, shows detailed help for that specific command.

**Examples:**
```bash
# Show general help
dev-agent help

# Show help for specific command
dev-agent help init
dev-agent help azure configure
dev-agent help cleanup scan
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

**Description:**
Displays practical examples for common dev-agent workflows including new project setup, existing codebase analysis, Azure configuration, and cost management.

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

---

## Status and Reporting

### `dev-agent status`

Show project status and progress.

```bash
dev-agent status [PROJECT_PATH] [OPTIONS]
```

**Arguments:**
- `PROJECT_PATH` (optional): Project directory path (defaults to current directory)

**Options:**
- `--detailed`: Show detailed status information
- `--verbose, -v`: Enable verbose output

**Description:**
Displays current project status including current phase, progress percentage, completed phases, cost information, and last activity timestamp.

**Status Information:**
- Current workflow phase
- Phase progress percentage
- Completed phases with checkmarks
- Cost information (current and by phase)
- Last activity timestamp
- Next steps guidance

**Examples:**
```bash
# Show status for current directory
dev-agent status

# Show status for specific project
dev-agent status /path/to/project

# Show detailed status
dev-agent status --detailed
```

---

### `dev-agent cost-report`

Generate cost report for Azure OpenAI usage.

```bash
dev-agent cost-report [PROJECT_PATH] [OPTIONS]
```

**Arguments:**
- `PROJECT_PATH` (optional): Project directory path (defaults to current directory)

**Options:**
- `--phase PHASE`: Filter by specific phase (indexing, specification, design, implementation)
- `--export PATH`: Export report as JSON to specified path
- `--verbose, -v`: Enable verbose output

**Description:**
Displays detailed cost breakdown for Azure OpenAI API usage including token counts, cost by operation type, and budget warnings.

**Cost Information:**
- Total tokens used (prompt + completion)
- Cost breakdown by phase
- Cost breakdown by operation type
- Token usage statistics
- Budget warnings if thresholds exceeded

**Examples:**
```bash
# Show cost report for current project
dev-agent cost-report

# Show cost report for specific project
dev-agent cost-report /path/to/project

# Filter by phase
dev-agent cost-report --phase indexing
dev-agent cost-report --phase specification

# Export as JSON
dev-agent cost-report --export cost-report.json

# Detailed cost report
dev-agent cost-report --verbose
```

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

**Description:**
Performs comprehensive audit of all dev-agent functionality including indexing, specification generation, design generation, implementation tasks, state management, Azure OpenAI integration, and error handling.

**What it audits:**
1. Indexing phase functionality
2. Specification generation
3. Design document generation
4. Implementation task generation
5. State management and persistence
6. Azure OpenAI integration
7. Cost tracking accuracy
8. Error handling and recovery

**Examples:**
```bash
# Run full audit
dev-agent audit

# Skip Azure OpenAI tests
dev-agent audit --skip-azure

# Run audit with verbose output
dev-agent audit --verbose
```

**Audit Report:**
Generates a detailed markdown report in `.dev_agent/audit_report.md` with:
- Test results for each component
- Pass/fail status
- Recommendations for improvements
- Summary statistics

---

## Configuration Commands

Configuration commands are under the `config` command group.

### `dev-agent config show`

Show current configuration.

```bash
dev-agent config show
```

**Description:**
Displays the current dev-agent configuration including all settings, Azure OpenAI configuration, indexing settings, and logging configuration.

**Examples:**
```bash
# Show current configuration
dev-agent config show
```

---

### `dev-agent config set`

Set configuration value.

```bash
dev-agent config set KEY VALUE
```

**Arguments:**
- `KEY`: Configuration key (e.g., `logging.level`, `indexing.chunk_size`)
- `VALUE`: Configuration value

**Description:**
Sets a specific configuration value. Supports nested keys using dot notation.

**Examples:**
```bash
# Set logging level
dev-agent config set logging.level DEBUG

# Set chunk size
dev-agent config set indexing.chunk_size 1000

# Set temperature
dev-agent config set azure_openai.temperature 0.8
```

---

### `dev-agent config reset`

Reset configuration to defaults.

```bash
dev-agent config reset
```

**Description:**
Resets all configuration to default values. This does not affect Azure OpenAI credentials.

**Examples:**
```bash
# Reset configuration
dev-agent config reset
```

**Warning:** This will reset all custom settings to defaults.

---

## Scaffolding Commands

Scaffolding commands are under the `scaffold` command group.

### `dev-agent scaffold list`

List available project templates.

```bash
dev-agent scaffold list [OPTIONS]
```

**Options:**
- `--language, -l LANGUAGE`: Filter by programming language (python, javascript, typescript, go, rust)
- `--category, -c CATEGORY`: Filter by category (web, api, cli, data, ml)

**Description:**
Lists all available project templates with descriptions, languages, and features.

**Examples:**
```bash
# List all templates
dev-agent scaffold list

# Filter by language
dev-agent scaffold list --language python

# Filter by category
dev-agent scaffold list --category web
```

---

### `dev-agent scaffold create`

Create project from template.

```bash
dev-agent scaffold create NAME TEMPLATE_ID [OPTIONS]
```

**Arguments:**
- `NAME`: Project name
- `TEMPLATE_ID`: Template identifier from `scaffold list`

**Options:**
- `--output-path, -o PATH`: Output directory path
- `--description TEXT`: Project description
- `--author TEXT`: Author name
- `--license TEXT`: License type (MIT, Apache-2.0, GPL-3.0, BSD-3-Clause)

**Description:**
Creates a new project from a template with proper structure, dependencies, and configuration.

**Examples:**
```bash
# Create from template
dev-agent scaffold create my-api fastapi-rest

# Create with custom output path
dev-agent scaffold create my-api fastapi-rest --output-path /path/to/projects

# Create with metadata
dev-agent scaffold create my-api fastapi-rest \
    --description "My REST API" \
    --author "John Doe" \
    --license MIT
```

---

### `dev-agent scaffold microservices`

Generate microservices architecture.

```bash
dev-agent scaffold microservices NAME [OPTIONS]
```

**Arguments:**
- `NAME`: Architecture name

**Options:**
- `--output-path, -o PATH`: Output directory path
- `--services TEXT`: Comma-separated list of service names
- `--gateway`: Include API gateway
- `--monitoring`: Include monitoring stack
- `--database TEXT`: Database type (postgres, mongodb, mysql)

**Description:**
Generates a complete microservices architecture with multiple services, API gateway, service mesh, and monitoring.

**Examples:**
```bash
# Generate basic microservices
dev-agent scaffold microservices my-system

# Generate with specific services
dev-agent scaffold microservices my-system \
    --services "auth,users,products,orders"

# Generate with gateway and monitoring
dev-agent scaffold microservices my-system \
    --gateway \
    --monitoring \
    --database postgres
```

---

## Cleanup Commands

Cleanup commands are under the `cleanup` command group.

### `dev-agent cleanup scan`

Scan for cleanup candidates.

```bash
dev-agent cleanup scan [PROJECT_PATH] [OPTIONS]
```

**Arguments:**
- `PROJECT_PATH` (optional): Project directory path (defaults to current directory)

**Options:**
- `--category CATEGORY`: Scan specific category only (temporary, generated, artifacts, examples, dependencies)
- `--verbose, -v`: Enable verbose output

**Description:**
Scans the repository for files and directories that can be cleaned up including temporary files, generated files, development artifacts, obsolete examples, and unused dependencies.

**Cleanup Categories:**
1. **Temporary Files**: `.coverage`, `*.pyc`, `__pycache__/`, cache directories
2. **Generated Files**: `site/`, `TASK_*.md`, build artifacts
3. **Development Artifacts**: `.development/` contents
4. **Obsolete Examples**: Non-functional or outdated examples
5. **Unused Dependencies**: Dependencies not imported in codebase

**Examples:**
```bash
# Scan all categories
dev-agent cleanup scan

# Scan specific project
dev-agent cleanup scan /path/to/project

# Scan specific category
dev-agent cleanup scan --category temporary
dev-agent cleanup scan --category dependencies

# Scan with verbose output
dev-agent cleanup scan --verbose
```

---

### `dev-agent cleanup dry-run`

Simulate cleanup without making changes.

```bash
dev-agent cleanup dry-run [PROJECT_PATH] [OPTIONS]
```

**Arguments:**
- `PROJECT_PATH` (optional): Project directory path (defaults to current directory)

**Options:**
- `--category CATEGORY`: Clean specific category only
- `--verbose, -v`: Enable verbose output

**Description:**
Simulates cleanup operations without actually removing or moving files. Shows what would be cleaned up and estimated size reduction.

**Examples:**
```bash
# Dry run for all categories
dev-agent cleanup dry-run

# Dry run for specific category
dev-agent cleanup dry-run --category temporary

# Dry run with verbose output
dev-agent cleanup dry-run --verbose
```

---

### `dev-agent cleanup execute`

Execute cleanup operations.

```bash
dev-agent cleanup execute [PROJECT_PATH] [OPTIONS]
```

**Arguments:**
- `PROJECT_PATH` (optional): Project directory path (defaults to current directory)

**Options:**
- `--category CATEGORY`: Clean specific category only
- `--no-backup`: Skip backup creation (NOT RECOMMENDED)
- `--force`: Skip confirmation prompts
- `--verbose, -v`: Enable verbose output

**Description:**
Executes cleanup operations with confirmation prompts. Creates backups before removing files unless `--no-backup` is specified.

**Safety Features:**
- Confirmation prompts for each category
- Automatic backup creation
- Detailed logging of all operations
- Rollback capability via backups

**Examples:**
```bash
# Execute cleanup with prompts
dev-agent cleanup execute

# Execute specific category
dev-agent cleanup execute --category temporary

# Execute without backup (not recommended)
dev-agent cleanup execute --no-backup

# Execute without prompts (use with caution)
dev-agent cleanup execute --force

# Execute with verbose output
dev-agent cleanup execute --verbose
```

**Cleanup Report:**
Generates a detailed report in `CLEANUP_REPORT.md` with:
- List of all removed files with reasons
- Size reduction statistics
- Backup location
- Timestamp and execution details

---

## Command Aliases

Some commands have shorter aliases for convenience:

| Full Command | Alias | Description |
|-------------|-------|-------------|
| `dev-agent` | `dev-agent interactive` | Start interactive mode |
| `dev-agent --help` | `dev-agent help` | Show help |
| `dev-agent --version` | | Show version |

---

## Exit Codes

dev-agent uses standard exit codes:

| Code | Meaning |
|------|---------|
| 0 | Success |
| 1 | General error |
| 2 | Configuration error |
| 3 | API error |
| 130 | Interrupted by user (Ctrl+C) |

---

## Environment Variables

In addition to Azure OpenAI variables, dev-agent respects these environment variables:

| Variable | Description | Default |
|----------|-------------|---------|
| `DEV_AGENT_CONFIG_PATH` | Path to configuration file | `~/.dev_agent/config.yaml` |
| `DEV_AGENT_LOG_LEVEL` | Logging level | `INFO` |
| `DEV_AGENT_NO_COLOR` | Disable colored output | `false` |
| `DEV_AGENT_INTEGRATION_TESTS` | Enable integration tests | `false` |

---

## Configuration Files

dev-agent uses these configuration files:

| File | Location | Purpose |
|------|----------|---------|
| `config.yaml` | `~/.dev_agent/` | Global configuration |
| `config.yaml` | `.dev_agent/` | Project-specific configuration |
| `.dev_agent_config` | `~/` | User preferences from setup wizard |
| `state.json` | `.dev_agent/` | Project state and progress |

Project-specific configuration overrides global configuration.

---

## Getting Help

For more detailed information:

- **Workflow Commands**: See [Workflow Commands](workflow-commands.md)
- **Utility Commands**: See [Utility Commands](utility-commands.md)
- **CLI Examples**: See [CLI Examples](examples.md)
- **General Documentation**: See [Documentation Index](../index.md)
- **GitHub Issues**: Report bugs or request features

For command-specific help, use:
```bash
dev-agent COMMAND --help
```
