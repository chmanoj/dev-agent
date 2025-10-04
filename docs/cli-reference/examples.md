# CLI Usage Examples

This document provides practical examples for common dev-agent workflows. For command reference, see [Commands](commands.md). For workflow details, see [Workflow Commands](workflow-commands.md). For utility commands, see [Utility Commands](utility-commands.md).

## Table of Contents

- [First-Time Setup](#first-time-setup)
- [New Project Workflow](#new-project-workflow)
- [Existing Codebase Workflow](#existing-codebase-workflow)
- [Azure OpenAI Configuration](#azure-openai-configuration)
- [Cost Management](#cost-management)
- [Troubleshooting](#troubleshooting)
- [Advanced Usage](#advanced-usage)

---

## First-Time Setup

### Complete Initial Setup

```bash
# 1. Install dev-agent
pip install dev-agent
# or
uv pip install dev-agent

# 2. Run setup wizard
dev-agent setup

# Follow the interactive prompts:
# - Enter Azure OpenAI endpoint
# - Enter API key
# - Enter deployment names
# - Test connection

# 3. Verify setup
dev-agent setup --status

# 4. Validate environment
dev-agent validate
```

**Expected Output:**

```
dev-agent Setup Wizard
──────────────────────────────────────────────

Welcome to dev-agent!

Let's configure your Azure OpenAI settings...

Azure OpenAI Endpoint: https://my-resource.openai.azure.com/
API Key: ********
API Version: 2024-02-15-preview
GPT-4 Deployment Name: gpt-4
Embedding Deployment Name: text-embedding-ada-002

Testing connection...
✓ Chat completion test successful
✓ Embeddings test successful

✅ Setup complete!

Next steps:
  • Initialize a project: dev-agent init
  • Start interactive mode: dev-agent
  • Get help: dev-agent help
```

---

## New Project Workflow

### Creating a New Project from Scratch

```bash
# 1. Create project directory
mkdir my-new-api
cd my-new-api

# 2. Initialize dev-agent
dev-agent init

# Output:
# Initializing dev-agent Project
# This appears to be a new project (empty directory).
# dev-agent will help you set up and scaffold your project.

# 3. Optionally use a template
dev-agent scaffold list --language python --category api

# 4. Create from template (optional)
dev-agent scaffold create my-api fastapi-rest \
    --description "My REST API" \
    --author "John Doe" \
    --license MIT

# 5. Start interactive mode
dev-agent

# 6. Describe what you want to build
> I want to build a REST API for managing user accounts with authentication

# AI generates specification...

# 7. Review and approve
> show  # View the specification
> approve  # Approve and continue to design

# 8. Review design
> show  # View the design document
> approve  # Approve and continue to implementation

# 9. Review implementation tasks
> show  # View the task list
> approve  # Approve tasks

# 10. Exit and start implementing
> exit
```

**Project Structure After Init:**

```
my-new-api/
├── .dev_agent/
│   ├── state.json
│   ├── documents/
│   │   ├── specification.md
│   │   ├── design.md
│   │   └── tasks.md
│   ├── logs/
│   └── backups/
├── src/
│   └── (your code here)
├── tests/
├── requirements.txt
└── README.md
```

---

### Using Project Templates

```bash
# 1. List available templates
dev-agent scaffold list

# Output:
# Available Templates
# ──────────────────────────────────────────────
# 
# Python Templates:
#   fastapi-rest      - FastAPI REST API with authentication
#   flask-api         - Flask REST API
#   django-api        - Django REST Framework API
#   cli-tool          - Python CLI application
#   data-pipeline     - Data processing pipeline
#   ml-project        - Machine learning project
# 
# JavaScript Templates:
#   express-api       - Express.js REST API
#   nextjs-app        - Next.js web application
#   react-app         - React application

# 2. Filter by language
dev-agent scaffold list --language python

# 3. Filter by category
dev-agent scaffold list --category api

# 4. Create from template
dev-agent scaffold create my-api fastapi-rest \
    --output-path ~/projects \
    --description "User management API" \
    --author "Jane Smith" \
    --license MIT

# 5. Navigate to project
cd ~/projects/my-api

# 6. Initialize dev-agent
dev-agent init

# 7. Start development
dev-agent
```

---

## Existing Codebase Workflow

### Analyzing an Existing Project

```bash
# 1. Navigate to existing project
cd ~/projects/my-existing-api

# 2. Initialize dev-agent (automatically indexes)
dev-agent init

# Output:
# Initializing dev-agent Project
# 
# Detected existing python project with 247 files.
# Languages: Python, JavaScript
# 
# Codebase Detection Summary
# ──────────────────────────────────────────────
# Languages:    Python, JavaScript
# File Count:   247
# Project Size: Medium
# Complexity:   Moderate
# 
# Indexing codebase...
# [Progress bar shows file-by-file progress]
# 
# ✅ Indexing Complete!
# 
# Indexing Summary
# ──────────────────────────────────────────────
# Files Indexed:        247
# Lines of Code:        15,432
# Code Chunks:          1,234
# Embeddings Generated: 1,234
# Functions Found:      456
# Classes Found:        89
# 
# 🔍 Patterns Detected:
#   • 456 function definitions
#   • 89 class definitions
#   • 234 import statements
# 
# 💰 Indexing cost: $0.1234

# 3. Start interactive mode
dev-agent

# 4. Request a new feature
> Add JWT authentication to the existing API endpoints

# AI analyzes existing code patterns...
# AI generates specification matching your code style...

# 5. Review specification
> show

# 6. Approve and continue
> approve

# Design phase generates design matching your architecture...

# 7. Review design
> show
> approve

# Implementation phase generates tasks referencing existing patterns...

# 8. Review tasks
> show
> approve

# 9. Check status
> status

# 10. Exit
> exit
```

---

### Adding a Feature to Existing Code

```bash
# 1. Resume existing project
cd ~/projects/my-api
dev-agent resume

# Output:
# Resumed project: /Users/dev/my-api
# Current phase: IMPLEMENTATION

# 2. Check current status
dev-agent status

# Output:
# Project Status
# ──────────────────────────────────────────────
# Current Phase: IMPLEMENTATION
# Progress: 75%
# 
# Phase Status:
#   ✓ Indexing      (Completed)
#   ✓ Specification (Completed)
#   ✓ Design        (Completed)
#   ⟳ Implementation (In Progress)

# 3. View generated tasks
cat .dev_agent/documents/tasks.md

# 4. Start implementing tasks
# (Implement tasks manually or use AI assistance)

# 5. Track costs
dev-agent cost-report

# 6. When ready for next feature, start over
dev-agent
> I want to add rate limiting to the API
```

---

## Azure OpenAI Configuration

### Interactive Configuration

```bash
# 1. Run configuration wizard
dev-agent azure configure

# Follow prompts:
# Azure OpenAI Endpoint: https://my-resource.openai.azure.com/
# API Key: [paste your key]
# API Version: 2024-02-15-preview
# GPT-4 Deployment Name: gpt-4
# Embedding Deployment Name: text-embedding-ada-002
# 
# Do you want to test the connection now? [Y/n]: y
# 
# Testing Azure OpenAI Connection
# ──────────────────────────────────────────────
# 1. Testing Chat Completion
# ✓ Chat completion test successful
# 
# 2. Testing Embeddings
# ✓ Embeddings test successful
# 
# ✅ All tests passed successfully!
```

---

### Non-Interactive Configuration

```bash
# Configure via command-line options
dev-agent azure configure --no-interactive \
    --api-key "your-api-key-here" \
    --endpoint "https://your-resource.openai.azure.com/" \
    --deployment-name "gpt-4" \
    --embedding-deployment "text-embedding-ada-002"

# Test connection
dev-agent azure test
```

---

### Using Environment Variables

```bash
# 1. Set environment variables
export AZURE_OPENAI_API_KEY="your-api-key-here"
export AZURE_OPENAI_ENDPOINT="https://your-resource.openai.azure.com/"
export AZURE_OPENAI_DEPLOYMENT_NAME="gpt-4"
export AZURE_OPENAI_EMBEDDING_DEPLOYMENT="text-embedding-ada-002"

# 2. Verify configuration
dev-agent azure env

# Output:
# Azure OpenAI Environment Variables
# ──────────────────────────────────────────────
# AZURE_OPENAI_API_KEY:              ✓ Set
# AZURE_OPENAI_ENDPOINT:             ✓ Set
# AZURE_OPENAI_DEPLOYMENT_NAME:      ✓ Set
# AZURE_OPENAI_EMBEDDING_DEPLOYMENT: ✓ Set

# 3. Test connection
dev-agent azure test

# 4. Use dev-agent (will use environment variables)
dev-agent init
```

---

### Checking Azure Status

```bash
# Show current Azure OpenAI configuration
dev-agent azure status

# Output:
# Azure OpenAI Status
# ──────────────────────────────────────────────
# API Key:              *** (Configured)
# Endpoint:             https://my-resource.openai.azure.com/
# API Version:          2024-02-15-preview
# Deployment Name:      gpt-4
# Embedding Deployment: text-embedding-ada-002
# Max Tokens:           4000
# Temperature:          0.7
# 
# ✅ Azure OpenAI is fully configured and ready to use!
```

---

### Exporting and Importing Configuration

```bash
# Export configuration (without API key)
dev-agent azure export --output azure-config.json

# Export with API key (use with caution)
dev-agent azure export --output azure-config-full.json --include-secrets

# Import configuration
dev-agent azure import azure-config.json

# Import and merge with existing
dev-agent azure import azure-config.json --merge
```

---

## Cost Management

### Tracking Costs During Development

```bash
# 1. Check cost before starting
dev-agent cost-report

# Output:
# Azure OpenAI Cost Report
# ──────────────────────────────────────────────
# Total Cost: $0.00
# No API calls made yet.

# 2. Initialize and index project
dev-agent init

# 3. Check cost after indexing
dev-agent cost-report

# Output:
# Azure OpenAI Cost Report
# ──────────────────────────────────────────────
# Indexing:     $0.1234  (45,000 tokens)
# Total Cost:   $0.1234

# 4. Continue workflow
dev-agent

# 5. Check cost after each phase
dev-agent cost-report

# Output:
# Azure OpenAI Cost Report
# ──────────────────────────────────────────────
# Indexing:       $0.1234  (45,000 tokens)
# Specification:  $0.0567  (8,000 tokens)
# Design:         $0.0890  (10,023 tokens)
# Total Cost:     $0.2691
```

---

### Filtering Costs by Phase

```bash
# Show costs for specific phase
dev-agent cost-report --phase indexing
dev-agent cost-report --phase specification
dev-agent cost-report --phase design
dev-agent cost-report --phase implementation

# Example output:
# Azure OpenAI Cost Report - Indexing Phase
# ──────────────────────────────────────────────
# Embedding Tokens: 45,000
# Cost:             $0.1234
# API Calls:        125
# Cache Hit Rate:   0%
```

---

### Exporting Cost Reports

```bash
# Export as JSON for analysis
dev-agent cost-report --export cost-report.json

# Export specific phase
dev-agent cost-report --phase indexing --export indexing-costs.json

# View exported JSON
cat cost-report.json | jq .

# Example output:
# {
#   "project_path": "/Users/dev/my-api",
#   "report_date": "2024-01-15T10:30:45Z",
#   "total_cost": 0.2691,
#   "cost_by_phase": {
#     "indexing": 0.1234,
#     "specification": 0.0567,
#     "design": 0.0890
#   }
# }
```

---

### Optimizing Costs

```bash
# 1. Check cache hit rate
dev-agent cost-report --verbose

# Output shows:
# Efficiency Metrics
# ──────────────────────────────────────────────
# Cache Hit Rate:     78%
# Cached Embeddings:  975
# New Embeddings:     275

# 2. Don't delete embedding cache
# Keep .dev_agent/embedding_cache/ to avoid re-computing embeddings

# 3. Only re-index when code changes significantly
# Don't run 'dev-agent init' repeatedly on same code

# 4. Use smaller chunk sizes for smaller codebases
dev-agent config set indexing.chunk_size 500

# 5. Monitor costs regularly
dev-agent cost-report
```

---

## Troubleshooting

### Configuration Issues

```bash
# Problem: Azure OpenAI not configured
dev-agent validate

# Output:
# ❌ Validation failed
# Errors:
#   1. API Key not configured
#      Solution: Run 'dev-agent azure configure'

# Solution:
dev-agent azure configure

# Verify:
dev-agent azure test
```

---

### Connection Issues

```bash
# Problem: Cannot connect to Azure OpenAI
dev-agent azure test

# Output:
# ❌ Authentication Error
# Possible causes:
#   • Invalid API key
#   • Incorrect endpoint URL

# Solution 1: Reconfigure
dev-agent azure configure

# Solution 2: Check environment variables
dev-agent azure env

# Solution 3: Verify in Azure Portal
# Go to portal.azure.com → Your Azure OpenAI resource → Keys and Endpoint
```

---

### Project State Issues

```bash
# Problem: Cannot resume project
dev-agent resume

# Output:
# Error: No dev-agent project found
# Use 'dev-agent init' to initialize a new project.

# Solution: Initialize first
dev-agent init

# Problem: State corrupted
dev-agent resume

# Output:
# Warning: Could not resume project, starting new project...

# Solution: Restore from backup
cp .dev_agent/backups/state.json.backup .dev_agent/state.json
dev-agent resume
```

---

### Indexing Issues

```bash
# Problem: Indexing fails
dev-agent init --verbose

# Check logs
cat .dev_agent/logs/dev-agent.log

# Common issues:
# 1. File permissions
sudo chown -R $USER .dev_agent/

# 2. Disk space
df -h

# 3. Azure OpenAI quota
dev-agent azure test

# 4. Network connectivity
ping openai.azure.com
```

---

### Cost Issues

```bash
# Problem: Costs higher than expected
dev-agent cost-report --verbose

# Check:
# 1. Cache hit rate (should be >70% after first run)
# 2. Number of API calls
# 3. Token usage per call

# Solutions:
# 1. Don't delete embedding cache
ls -la .dev_agent/embedding_cache/

# 2. Reduce chunk size for smaller projects
dev-agent config set indexing.chunk_size 500

# 3. Use batch processing (already default)
dev-agent config show | grep batch_size
```

---

## Advanced Usage

### Re-running Specific Phases

```bash
# 1. Delete phase document
rm .dev_agent/documents/specification.md

# 2. Resume project
dev-agent resume

# 3. Phase will re-run automatically
# Specification phase will start again
```

---

### Trying Different Approaches

```bash
# 1. Backup current state
cp -r .dev_agent .dev_agent.backup

# 2. Try alternative approach
dev-agent
> Try a different architecture for the authentication system

# 3. Compare results
diff .dev_agent/documents/design.md .dev_agent.backup/documents/design.md

# 4. Restore if needed
rm -rf .dev_agent
mv .dev_agent.backup .dev_agent
```

---

### Batch Processing Multiple Projects

```bash
# Process multiple projects
for project in project1 project2 project3; do
    echo "Processing $project..."
    cd ~/projects/$project
    dev-agent init --verbose
    dev-agent cost-report --export "${project}-costs.json"
done

# Aggregate costs
jq -s 'map(.total_cost) | add' *-costs.json
```

---

### Custom Configuration Per Project

```bash
# 1. Initialize project
cd my-project
dev-agent init

# 2. Create project-specific config
cat > .dev_agent/config.yaml << EOF
indexing:
  chunk_size: 1500
  chunk_overlap: 300
  batch_size: 32

azure_openai:
  temperature: 0.5
  max_tokens: 8000

workflow:
  auto_save: true
  require_approval: true
EOF

# 3. Use project
dev-agent resume
# Uses project-specific configuration
```

---

### Cleanup and Maintenance

```bash
# 1. Scan for cleanup candidates
dev-agent cleanup scan

# Output:
# Cleanup Scan Results
# ──────────────────────────────────────────────
# Temporary Files:     45 files (12.3 MB)
# Generated Files:     23 files (5.6 MB)
# Development Artifacts: 12 files (2.1 MB)
# Total:              80 files (20.0 MB)

# 2. Dry run to see what would be removed
dev-agent cleanup dry-run

# 3. Execute cleanup with confirmation
dev-agent cleanup execute

# 4. Execute specific category only
dev-agent cleanup execute --category temporary

# 5. Execute without prompts (use with caution)
dev-agent cleanup execute --force
```

---

### Running System Audit

```bash
# 1. Run full audit
dev-agent audit

# Output:
# dev-agent System Audit
# ──────────────────────────────────────────────
# Indexing Phase:      ✓ Passed
# Specification Phase: ✓ Passed
# Design Phase:        ✓ Passed
# Implementation Phase: ✓ Passed
# State Management:    ✓ Passed
# Azure OpenAI:        ✓ Passed
# Error Handling:      ✓ Passed
# 
# ✅ All audit checks passed! (28/28)

# 2. Skip Azure tests (faster)
dev-agent audit --skip-azure

# 3. View detailed report
cat .dev_agent/audit_report.md
```

---

### Microservices Architecture

```bash
# Generate complete microservices architecture
dev-agent scaffold microservices my-system \
    --services "auth,users,products,orders,payments" \
    --gateway \
    --monitoring \
    --database postgres \
    --output-path ~/projects

# Output:
# Generated microservices architecture:
# my-system/
# ├── services/
# │   ├── auth-service/
# │   ├── users-service/
# │   ├── products-service/
# │   ├── orders-service/
# │   └── payments-service/
# ├── api-gateway/
# ├── monitoring/
# │   ├── prometheus/
# │   └── grafana/
# ├── docker-compose.yml
# └── README.md

# Initialize each service
cd ~/projects/my-system
for service in services/*; do
    cd $service
    dev-agent init
    cd ../..
done
```

---

## See Also

- [Commands Reference](commands.md) - Complete command reference
- [Workflow Commands](workflow-commands.md) - Workflow command details
- [Utility Commands](utility-commands.md) - Utility command details
- [Getting Started Guide](../getting-started/first-time-setup.md) - Initial setup
- [Troubleshooting Guide](../getting-started/troubleshooting.md) - Common issues
- [Azure OpenAI Configuration](../configuration/azure-openai.md) - Detailed Azure setup
