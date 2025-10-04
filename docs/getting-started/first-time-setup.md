# First-Time Setup

Welcome to dev-agent! This guide will walk you through setting up dev-agent for the first time.

## Prerequisites

Before you begin, ensure you have:

- **Python 3.10 or higher** installed
- **Azure OpenAI access** with an active subscription
- **uv package manager** installed (recommended) or pip

## Installation

### Using uv (Recommended)

```bash
# Install uv if you haven't already
curl -LsSf https://astral.sh/uv/install.sh | sh

# Install dev-agent
uv pip install dev-agent

# Or install from source
git clone https://github.com/your-org/dev-agent.git
cd dev-agent
uv sync --dev
```

### Using pip

```bash
pip install dev-agent
```

## Running the Setup Wizard

The first time you run dev-agent, you'll be guided through an interactive setup wizard:

```bash
dev-agent setup
```

The wizard will help you configure:

1. **Azure OpenAI Connection**
2. **Model Deployments**
3. **User Preferences**
4. **Project Type Selection**

## Step 1: Azure OpenAI Configuration

The wizard will prompt you for your Azure OpenAI credentials:

### Required Information

```
Azure OpenAI Endpoint: https://your-resource.openai.azure.com/
API Key: your-api-key-here
API Version: 2024-02-15-preview (default)
GPT-4 Deployment Name: gpt-4
Embedding Deployment Name: text-embedding-ada-002
```

### Where to Find These Values

1. **Azure Portal**: Navigate to your Azure OpenAI resource
2. **Endpoint**: Found in "Keys and Endpoint" section
3. **API Key**: Click "Show Keys" in the same section
4. **Deployment Names**: Go to "Model deployments" to see your deployment names

!!! tip "Security Best Practice"
    The setup wizard will save your API key securely in `~/.dev_agent_config`. Never commit this file to version control.

### Testing Your Connection

The wizard will automatically test your Azure OpenAI connection:

```
✓ Testing Azure OpenAI connection...
✓ GPT-4 deployment accessible
✓ Embedding deployment accessible
✓ Connection successful!
```

If the test fails, you'll see specific error messages to help troubleshoot.

## Step 2: Understanding the Workflow

The wizard explains dev-agent's four-phase workflow:

### Phase 1: Indexing
- Analyzes your codebase structure
- Generates semantic embeddings
- Stores code patterns in vector database
- **Estimated time**: 2-5 minutes for medium projects

### Phase 2: Specification
- Generates detailed specifications
- Uses GPT-4 with codebase context
- Requires user approval before proceeding
- **Estimated time**: 3-10 minutes

### Phase 3: Design
- Creates technical design documents
- References existing architectural patterns
- Requires user approval before proceeding
- **Estimated time**: 5-15 minutes

### Phase 4: Implementation
- Generates actionable implementation tasks
- Produces context-aware code
- Maintains consistency with existing code
- **Estimated time**: Varies by task complexity

!!! info "Cost Estimates"
    The wizard provides estimated costs for each phase based on your project size. Typical costs range from $0.50 to $5.00 for a complete workflow on a medium-sized project.

## Step 3: Project Type Selection

The wizard offers three options:

### Option 1: New Project from Template

```
Would you like to:
1. Create a new project from a template
2. Analyze an existing codebase
3. Skip for now

Choice: 1
```

Select from available templates:
- **FastAPI Web Service**
- **CLI Application**
- **Data Processing Pipeline**
- **Machine Learning Project**

### Option 2: Analyze Existing Codebase

```
Choice: 2

Enter the path to your existing project: /path/to/project
```

The wizard will:
- Detect programming languages
- Estimate project size
- Calculate indexing time
- Provide cost estimates

### Option 3: Skip for Now

```
Choice: 3

Setup complete! You can initialize a project later with:
  dev-agent init [path]
```

## Step 4: Preferences Configuration

The wizard saves your preferences:

```yaml
# ~/.dev_agent_config
azure_openai:
  endpoint: https://your-resource.openai.azure.com/
  api_key: ***REDACTED***
  deployment_name: gpt-4
  embedding_deployment: text-embedding-ada-002

preferences:
  cost_warnings_enabled: true
  budget_threshold: 10.0
  auto_approve_phases: false
  verbose_output: false
```

### Preference Options

- **cost_warnings_enabled**: Show warnings when operations exceed cost thresholds
- **budget_threshold**: Maximum budget per workflow (in USD)
- **auto_approve_phases**: Automatically proceed between phases (not recommended)
- **verbose_output**: Show detailed logging information

## Verifying Your Setup

After setup completes, verify everything is working:

```bash
# Check configuration status
dev-agent setup --status

# Validate environment
dev-agent validate

# View help
dev-agent --help
```

### Expected Output

```
✓ Azure OpenAI configured
✓ API connection successful
✓ All dependencies installed
✓ Ready to use dev-agent!

Next steps:
  - Initialize a new project: dev-agent init
  - Analyze existing code: dev-agent init /path/to/project
  - View examples: dev-agent examples
```

## Environment Variables (Alternative Setup)

If you prefer not to use the setup wizard, you can configure via environment variables:

```bash
# Create .env file
cat > .env << EOF
AZURE_OPENAI_ENDPOINT=https://your-resource.openai.azure.com/
AZURE_OPENAI_API_KEY=your-api-key-here
AZURE_OPENAI_API_VERSION=2024-02-15-preview
AZURE_OPENAI_DEPLOYMENT_NAME=gpt-4
AZURE_OPENAI_EMBEDDING_DEPLOYMENT=text-embedding-ada-002
EOF

# Load environment variables
source .env

# Or export them directly
export AZURE_OPENAI_ENDPOINT="https://your-resource.openai.azure.com/"
export AZURE_OPENAI_API_KEY="your-api-key-here"
```

!!! warning "Security"
    Add `.env` to your `.gitignore` to prevent committing credentials.

## Reconfiguring

To change your configuration later:

```bash
# Re-run setup wizard
dev-agent setup

# Update specific settings
dev-agent config set azure.endpoint "https://new-endpoint.openai.azure.com/"
dev-agent config set preferences.budget_threshold 20.0

# View current configuration
dev-agent config show
```

## Next Steps

Now that you're set up, choose your path:

- **New Project**: Follow the [New Project Guide](new-project.md)
- **Existing Codebase**: Follow the [Existing Codebase Guide](existing-codebase.md)
- **Troubleshooting**: See [Troubleshooting Guide](troubleshooting.md)

## Quick Start Commands

```bash
# Initialize a new project
dev-agent init my-project

# Analyze existing codebase
dev-agent init /path/to/existing/project

# Interactive mode
dev-agent

# Get help
dev-agent --help
dev-agent help <command>
```

## Support

If you encounter issues during setup:

1. Check the [Troubleshooting Guide](troubleshooting.md)
2. Verify your Azure OpenAI credentials
3. Run `dev-agent validate` for diagnostics
4. Check the logs in `.dev_agent/logs/`

For additional help, visit our [documentation](../index.md) or open an issue on GitHub.
