# Onboarding Module API Reference

The onboarding module provides guided setup and user journey management for first-time and returning users.

## Overview

The onboarding system provides:

- **Setup Wizard**: Interactive first-time configuration
- **Journey Management**: Tailored experiences for different user scenarios
- **Azure OpenAI Configuration**: Guided credential setup
- **Project Type Detection**: Automatic detection of new vs. existing projects
- **Contextual Help**: Phase-specific guidance and tips
- **User Preferences**: Persistent user settings and preferences

## User Journeys

### New Project Journey
1. Welcome and setup wizard
2. Azure OpenAI configuration
3. Template selection (optional)
4. Project scaffolding
5. Initial specification creation

### Existing Codebase Journey
1. Welcome and setup wizard
2. Azure OpenAI configuration
3. Codebase detection and analysis
4. Indexing with progress display
5. Pattern recognition summary
6. Specification generation from code

## Setup Wizard

::: dev_agent.onboarding.setup_wizard
    options:
      show_root_heading: true
      show_source: true
      members_order: source

## Journey Manager

::: dev_agent.onboarding.journey_manager
    options:
      show_root_heading: true
      show_source: true
      members_order: source

## Onboarding Models

::: dev_agent.onboarding.models
    options:
      show_root_heading: true
      show_source: true
      members_order: source

## Setup Wizard Usage

```python
from dev_agent.onboarding.setup_wizard import SetupWizard

# Create setup wizard
wizard = SetupWizard()

# Run interactive setup
result = await wizard.run()

if result.azure_configured:
    print("Azure OpenAI configured successfully!")
    
if result.preferences_saved:
    print("User preferences saved")
    
if result.ready_to_use:
    print("Setup complete - ready to use dev-agent!")
else:
    print("Setup incomplete - please run 'dev-agent setup' again")
```

## Journey Manager Usage

```python
from dev_agent.onboarding.journey_manager import JourneyManager
from pathlib import Path

# Create journey manager
manager = JourneyManager()

# Detect project type
project_type = manager.detect_project_type(Path("/path/to/project"))
print(f"Detected project type: {project_type}")

# Check if first run
if manager.is_first_run():
    print("First time user - showing setup wizard")
    
# Get appropriate onboarding flow
flow = manager.get_onboarding_flow(project_type)
print(f"Onboarding flow has {len(flow.steps)} steps")

# Guide user through a phase
await manager.guide_user_through_phase("indexing")
```

## CLI Usage

```bash
# Run setup wizard (first time or reconfigure)
dev-agent setup

# Check setup status
dev-agent setup --status

# Reconfigure Azure OpenAI only
dev-agent setup --azure-only

# Skip setup wizard (use defaults)
dev-agent setup --skip-wizard

# Reset all preferences
dev-agent setup --reset
```

## Setup Wizard Flow

The setup wizard guides users through:

1. **Welcome Screen**
   - Introduction to dev-agent
   - Overview of four-phase workflow
   - What to expect

2. **Azure OpenAI Configuration**
   - Endpoint URL input
   - API key input (secure)
   - Deployment names
   - Connection testing

3. **Workflow Explanation**
   - Detailed phase descriptions
   - Time estimates
   - Cost implications

4. **Project Type Selection**
   - New project from template
   - Analyze existing codebase
   - Skip for now

5. **Preferences**
   - Cost warnings
   - Budget thresholds
   - Verbose output
   - Auto-approve phases

6. **Completion**
   - Configuration summary
   - Next steps
   - Quick start guide

## User Preferences

User preferences are stored in `~/.dev_agent_config` and include:

- **azure_configured**: Whether Azure OpenAI is configured
- **preferred_editor**: User's preferred code editor
- **cost_warnings_enabled**: Show cost warnings
- **budget_threshold**: Monthly budget limit
- **auto_approve_phases**: Skip approval prompts
- **verbose_output**: Show detailed output

## Project Context

The journey manager detects and tracks:

- **path**: Project directory path
- **project_type**: "new", "existing", or "template"
- **has_code**: Whether project contains code
- **languages_detected**: Programming languages found
- **estimated_size**: Project size estimate
- **complexity**: "simple", "moderate", or "complex"

## Onboarding Steps

Each onboarding step includes:

- **title**: Step name
- **description**: What the step does
- **action**: Callable to execute the step
- **help_text**: Detailed help information
- **estimated_time**: How long the step takes
- **skippable**: Whether step can be skipped
- **completed**: Whether step has been completed

## Best Practices

1. **Run setup wizard on first use** to configure Azure OpenAI
2. **Review cost estimates** before starting workflow
3. **Choose appropriate project type** for optimal experience
4. **Enable cost warnings** to avoid unexpected charges
5. **Set budget thresholds** for cost control
6. **Use verbose output** when learning the tool
7. **Reconfigure when needed** with `dev-agent setup`

## Error Handling

The onboarding system handles:

- **Invalid Azure credentials**: Clear error messages with setup guidance
- **Network connectivity issues**: Retry suggestions and offline mode
- **Configuration file errors**: Automatic backup and recovery
- **User cancellation**: Safe exit at any point
- **Incomplete setup**: Resume from last completed step
