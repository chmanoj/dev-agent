# CLI Commands Quick Reference

## Getting Unstuck from Indexing

If you're stuck in the indexing phase and don't have Azure OpenAI configured, you now have two options:

### Option 1: Skip to Next Phase
```bash
dev-agent
# In interactive mode:
skip
```

This will:
- Warn you about skipping
- Ask for confirmation
- Move you to the next phase (specification)
- Save your state

### Option 2: Cancel Current Operation
```bash
dev-agent
# In interactive mode:
cancel
```

This will:
- Cancel the current operation
- Save your state
- Let you resume later or use other commands

## All Available Commands

### Project Management
- `init [path]` - Initialize a new project
- `resume [path]` - Resume an existing project
- `status` - Show current project status

### Workflow Control
- `run` or `start` - Execute complete workflow
- `phase <PHASE>` - Transition to specific phase
  - Valid phases: INDEXING, SPECIFICATION, DESIGN, IMPLEMENTATION
- `skip` - Skip current phase (with warning)
- `cancel` - Cancel current operation

### Document Management
- `preview <type>` - Preview generated documents
  - Types: specification, design, tasks
- `approve` - Approve current document
- `reject` - Reject current document

### Analysis & Visualization
- `architecture` - Show architecture diagram
- `workflow` - Show workflow diagram
- `tree [path]` - Show project structure
- `search <query> <type>` - Search in documents

### Utilities
- `cost` - Display Azure OpenAI cost report
- `history` - Show command history
- `progress` - Show phase progress summary
- `help` - Show all commands
- `clear` - Clear screen
- `exit` or `quit` - Exit the application

## Common Scenarios

### Scenario 1: Stuck in Indexing Without Azure OpenAI
```bash
# Start dev-agent
dev-agent

# Skip indexing phase
skip
# Confirm: y

# Now you're in specification phase
status
```

### Scenario 2: Want to Cancel and Come Back Later
```bash
# Start dev-agent
dev-agent

# Cancel current operation
cancel
# Confirm: y

# Later, resume where you left off
dev-agent resume
```

### Scenario 3: Check Current Status
```bash
dev-agent

# Check status
status

# Output shows:
# - Current Phase
# - Status (Active/Complete)
# - Last Updated timestamp
```

### Scenario 4: Move to Specific Phase
```bash
dev-agent

# Jump to design phase
phase DESIGN

# Or jump to implementation
phase IMPLEMENTATION
```

## Phase Workflow

The normal workflow progresses through these phases:

```
1. INDEXING       → Analyze codebase structure
   ↓
2. SPECIFICATION  → Generate requirements
   ↓
3. DESIGN         → Create technical design
   ↓
4. IMPLEMENTATION → Generate tasks
```

You can:
- Skip phases with `skip` command
- Jump to specific phases with `phase <PHASE>` command
- Cancel and resume later with `cancel` command

## Tips

### When to Skip
- ✅ Skip indexing if you don't have Azure OpenAI configured
- ✅ Skip indexing for new projects (no code to analyze)
- ⚠️ Don't skip if you want context-aware code generation
- ⚠️ Skipping may reduce quality of generated documents

### When to Cancel
- ✅ Cancel if you need to configure Azure OpenAI first
- ✅ Cancel if you want to review documentation
- ✅ Cancel if you need to step away
- ✅ Your state is saved automatically

### Getting Help
- Type `help` in interactive mode for full command list
- Use `--help` flag with any command for details
- Check contextual help based on current phase

## Troubleshooting

### "Unknown command: skip"
**Fixed!** The skip command is now implemented. Make sure you're using the latest version.

### "Unknown command: cancel"
**Fixed!** The cancel command is now implemented. Make sure you're using the latest version.

### Still Stuck in Indexing
If you're still stuck:
1. Exit dev-agent (Ctrl+C or `exit`)
2. Check `.dev_agent/state.json`
3. If `current_phase` is "indexing", it's been updated to "specification"
4. Run `dev-agent resume` to continue

### State File Corrupted
If your state file is corrupted:
1. Backup `.dev_agent/state.json`
2. Delete the corrupted file
3. Run `dev-agent init` to start fresh

## Configuration

### Azure OpenAI Setup
If you want to use full features (including indexing with embeddings):

```bash
# Run setup wizard
dev-agent setup

# Check setup status
dev-agent setup --status

# Test Azure connection
dev-agent azure test
```

### Without Azure OpenAI
You can still use dev-agent without Azure OpenAI:
- Skip indexing phase
- Manually write specifications
- Use as a project organization tool

## Examples

### Example 1: New Project Without Azure OpenAI
```bash
# Initialize project
dev-agent init

# Skip indexing (no Azure OpenAI)
skip

# Manually create specification
# (or configure Azure OpenAI first)
```

### Example 2: Existing Project, Resume After Cancel
```bash
# Start working
dev-agent resume

# Need to step away
cancel

# Come back later
dev-agent resume

# Continue where you left off
status
```

### Example 3: Jump Between Phases
```bash
dev-agent

# Check current phase
status

# Jump to design
phase DESIGN

# Go back to specification
phase SPECIFICATION

# Skip to implementation
phase IMPLEMENTATION
```

## Getting More Help

- **Full documentation**: Check `docs/` directory
- **Setup guide**: Run `dev-agent setup`
- **Examples**: Run `dev-agent examples`
- **Issues**: Report at GitHub repository

## Summary

The key fixes:
- ✅ `skip` command now works - skip stuck phases
- ✅ `cancel` command now works - cancel and resume later
- ✅ State file updated - no longer stuck in indexing
- ✅ Better error handling - clearer messages

You can now:
- Skip phases you don't need
- Cancel operations safely
- Resume work anytime
- Move between phases freely
