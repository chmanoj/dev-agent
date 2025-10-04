# Workflow Commands Reference

This document provides detailed information about dev-agent's workflow-related commands. For a complete command reference, see [Commands](commands.md). For practical examples, see [CLI Examples](examples.md).

## Overview

dev-agent implements a structured four-phase development workflow:

1. **Indexing Phase**: Analyze codebase structure and patterns
2. **Specification Phase**: Generate detailed specifications
3. **Design Phase**: Create technical design documents
4. **Implementation Phase**: Generate actionable tasks

Each phase builds on the previous one, with user approval gates between phases to ensure quality and control.

## Workflow Lifecycle

```
┌─────────────┐
│   init      │  Initialize project
└──────┬──────┘
       │
       ▼
┌─────────────┐
│  Indexing   │  Analyze codebase (automatic for existing projects)
└──────┬──────┘
       │
       ▼
┌─────────────┐
│Specification│  Generate specs (requires user input)
└──────┬──────┘
       │
       ▼  (User approval required)
       │
┌─────────────┐
│   Design    │  Create design docs
└──────┬──────┘
       │
       ▼  (User approval required)
       │
┌─────────────┐
│Implementation│ Generate tasks
└──────┬──────┘
       │
       ▼  (User approval required)
       │
┌─────────────┐
│   resume    │  Continue or restart phases
└─────────────┘
```

## Project Initialization

### `dev-agent init`

Initialize a new dev-agent project.

```bash
dev-agent init [PROJECT_PATH] [OPTIONS]
```

**Purpose:**
Sets up dev-agent for a project, detecting whether it's a new or existing codebase and providing appropriate guidance.

**Workflow for New Projects:**

1. **Detection**: Identifies empty directory as new project
2. **Setup Check**: Verifies Azure OpenAI configuration
3. **Template Offer**: Optionally use project templates
4. **Structure Creation**: Creates `.dev_agent/` directory
5. **Guidance**: Explains next steps for specification creation

**Workflow for Existing Projects:**

1. **Detection**: Identifies existing code
2. **Setup Check**: Verifies Azure OpenAI configuration
3. **Codebase Analysis**: Displays detected languages and file count
4. **Indexing**: Automatically starts indexing phase with progress display
5. **Summary**: Shows indexing results and patterns found
6. **Guidance**: Explains next steps for specification generation

**Examples:**

```bash
# Initialize new project
cd my-new-project
dev-agent init

# Initialize existing codebase
cd my-existing-project
dev-agent init

# Initialize with verbose output
dev-agent init --verbose
```

**What Gets Created:**

```
project-root/
└── .dev_agent/
    ├── state.json              # Project state and progress
    ├── documents/              # Generated documents
    │   ├── specification.md    # (created in specification phase)
    │   ├── design.md          # (created in design phase)
    │   └── tasks.md           # (created in implementation phase)
    ├── embedding_cache/        # Cached embeddings
    ├── logs/                   # Operation logs
    └── backups/               # State backups
```

---

### `dev-agent resume`

Resume an existing dev-agent project.

```bash
dev-agent resume [PROJECT_PATH] [OPTIONS]
```

**Purpose:**
Loads a previously initialized project and continues from the last saved state.

**What It Does:**

1. **Load State**: Reads `.dev_agent/state.json`
2. **Display Status**: Shows current phase and progress
3. **Restore Context**: Loads all generated documents
4. **Continue Workflow**: Starts interactive mode at current phase

**State Information Restored:**

- Current workflow phase
- Phase completion status
- Generated documents (specification, design, tasks)
- Indexing results and embeddings
- Cost tracking data
- User approvals and feedback

**Examples:**

```bash
# Resume project in current directory
dev-agent resume

# Resume specific project
dev-agent resume /path/to/project

# Resume with verbose output
dev-agent resume --verbose
```

---

## Interactive Mode

### `dev-agent` (Interactive Mode)

Start interactive chat-based interface.

```bash
dev-agent [PROJECT_PATH] [OPTIONS]
```

**Purpose:**
Provides a conversational interface to execute workflow phases, ask questions, and get guidance.

**Interactive Commands:**

Within interactive mode, you can use these commands:

| Command | Description |
|---------|-------------|
| `help` | Show available commands |
| `status` | Show current phase and progress |
| `next` | Proceed to next phase |
| `retry` | Retry current phase |
| `cost` | Show cost information |
| `save` | Save current state |
| `exit` | Exit interactive mode |

**Examples:**

```bash
# Start interactive mode
dev-agent

# Start in specific project
dev-agent /path/to/project

# Start with verbose logging
dev-agent --verbose
```

---

## Phase Details

### Indexing Phase

**Automatic Execution:**
- Runs automatically during `init` for existing projects
- Can be re-run if codebase changes significantly

**What It Does:**

1. **File Discovery**: Scans project directory for code files
2. **AST Parsing**: Uses Tree-sitter to parse code structure
3. **Pattern Detection**: Identifies coding patterns and conventions
4. **Embedding Generation**: Creates semantic embeddings via Azure OpenAI
5. **Vector Storage**: Stores embeddings in FAISS for similarity search

**Performance:**

- **Speed**: 100+ files/second
- **Batch Size**: 16 embeddings per batch
- **Caching**: Embeddings cached to avoid re-computation
- **Memory**: Efficient streaming for large codebases

---

### Specification Phase

**Execution:**
- Triggered in interactive mode after indexing
- Requires user input describing desired feature

**What It Does:**

1. **Context Retrieval**: Finds relevant code examples via vector search
2. **Pattern Analysis**: Understands existing conventions
3. **GPT-4 Generation**: Creates detailed specification
4. **User Review**: Presents specification for approval
5. **Document Storage**: Saves to `.dev_agent/documents/specification.md`

**Specification Format:**

```markdown
# Feature Specification

## Overview
[High-level description]

## Requirements
1. Functional Requirements
2. Non-functional Requirements
3. Acceptance Criteria

## Dependencies
[Required libraries and services]

## API Design
[Endpoints, methods, parameters]

## Data Models
[Database schemas, data structures]

## Error Handling
[Error scenarios and responses]
```

---

### Design Phase

**Execution:**
- Triggered after specification approval
- Automatic based on approved specification

**What It Does:**

1. **Architecture Analysis**: Reviews existing patterns
2. **Design Generation**: Creates technical design using GPT-4
3. **Pattern Matching**: Ensures consistency with codebase
4. **User Review**: Presents design for approval
5. **Document Storage**: Saves to `.dev_agent/documents/design.md`

**Design Format:**

```markdown
# Technical Design

## Architecture Overview
[System architecture diagram]

## Components
[Detailed component descriptions]

## Data Flow
[How data moves through the system]

## API Specifications
[Detailed API contracts]

## Database Design
[Schema definitions]

## Security Considerations
[Authentication, authorization, encryption]

## Performance Considerations
[Caching, optimization strategies]

## Testing Strategy
[Unit, integration, e2e tests]
```

---

### Implementation Phase

**Execution:**
- Triggered after design approval
- Automatic based on approved design

**What It Does:**

1. **Task Breakdown**: Splits design into actionable tasks
2. **Dependency Analysis**: Orders tasks by dependencies
3. **Code Generation**: Generates implementation tasks
4. **User Review**: Presents task list for approval
5. **Document Storage**: Saves to `.dev_agent/documents/tasks.md`

**Task Format:**

```markdown
# Implementation Tasks

## Phase 1: Setup
- [ ] 1.1 Create project structure
- [ ] 1.2 Install dependencies
- [ ] 1.3 Configure environment

## Phase 2: Core Implementation
- [ ] 2.1 Implement data models
- [ ] 2.2 Create API endpoints
- [ ] 2.3 Add business logic

## Phase 3: Testing
- [ ] 3.1 Write unit tests
- [ ] 3.2 Write integration tests
- [ ] 3.3 Test error scenarios

## Phase 4: Documentation
- [ ] 4.1 Update API documentation
- [ ] 4.2 Add code comments
- [ ] 4.3 Create user guide
```

---

## Workflow State Management

### State Persistence

dev-agent automatically saves state after each significant operation:

- Phase transitions
- Document generation
- User approvals
- Cost updates

**State File Location:**
```
.dev_agent/state.json
```

**State Contents:**

```json
{
  "project_path": "/path/to/project",
  "current_phase": "SPECIFICATION",
  "phase_status": {
    "indexing": "COMPLETED",
    "specification": "IN_PROGRESS",
    "design": "NOT_STARTED",
    "implementation": "NOT_STARTED"
  },
  "documents": {
    "specification": ".dev_agent/documents/specification.md",
    "design": null,
    "tasks": null
  },
  "indexing_metadata": {
    "total_files": 247,
    "total_chunks": 1234,
    "embeddings_count": 1234
  },
  "cost_tracking": {
    "total_tokens": 15000,
    "total_cost": 0.45
  },
  "last_updated": "2024-01-15T10:30:00Z"
}
```

---

## Approval Gates

Each phase requires user approval before proceeding to the next phase.

### Approval Process

1. **Generation Complete**: Phase completes and presents results
2. **User Review**: User reviews generated document
3. **Approval Decision**: User approves, requests changes, or rejects
4. **Next Action**: 
   - Approved: Proceed to next phase
   - Changes: Regenerate with feedback
   - Rejected: Return to previous phase

### Approval Commands (in Interactive Mode)

```
# Approve and continue
approve

# Request changes
revise [feedback]

# Reject and go back
reject

# View document again
show
```

---

## Cost Tracking

dev-agent tracks costs throughout the workflow.

### Cost by Phase

| Phase | Typical Cost | Tokens |
|-------|-------------|--------|
| Indexing | $0.10 - $0.50 | 5K - 25K |
| Specification | $0.05 - $0.20 | 2K - 10K |
| Design | $0.10 - $0.30 | 5K - 15K |
| Implementation | $0.05 - $0.15 | 2K - 8K |

**Total Workflow**: $0.30 - $1.15 for typical project

### Viewing Costs

```bash
# Show cost summary
dev-agent cost-report

# Show cost by phase
dev-agent cost-report --phase indexing

# Show detailed cost breakdown
dev-agent cost-report --verbose
```

---

## Error Handling and Recovery

### Common Errors

**Configuration Errors:**
```
Error: Azure OpenAI is not configured
Solution: Run 'dev-agent setup' or 'dev-agent azure configure'
```

**API Errors:**
```
Error: Rate limit exceeded
Solution: Wait a moment and retry, or check your Azure quota
```

**State Errors:**
```
Error: Project state is corrupted
Solution: Backup .dev_agent/ and run 'dev-agent init' again
```

### Recovery Options

1. **Retry Current Phase**: Use `retry` in interactive mode
2. **Restart Phase**: Delete phase document and restart
3. **Rollback**: Restore from `.dev_agent/backups/`
4. **Fresh Start**: Delete `.dev_agent/` and run `init` again

---

## Best Practices

### Workflow Execution

1. **Always Review**: Carefully review each generated document
2. **Provide Feedback**: Give specific feedback for revisions
3. **Save Frequently**: State is auto-saved, but manual saves don't hurt
4. **Monitor Costs**: Check costs regularly with `cost-report`
5. **Use Verbose Mode**: Enable verbose output for troubleshooting

### Project Organization

1. **One Project Per Directory**: Don't nest dev-agent projects
2. **Version Control**: Commit `.dev_agent/documents/` to git
3. **Ignore State**: Add `.dev_agent/state.json` to `.gitignore`
4. **Backup Important**: Backup `.dev_agent/` before major changes

### Performance Optimization

1. **Cache Embeddings**: Don't delete `.dev_agent/embedding_cache/`
2. **Incremental Indexing**: Only re-index when code changes significantly
3. **Batch Operations**: Let dev-agent batch API calls automatically
4. **Monitor Progress**: Use progress displays to track long operations

---

## Advanced Workflows

### Re-running Phases

To re-run a phase:

1. Delete the phase document from `.dev_agent/documents/`
2. Run `dev-agent resume`
3. Navigate to that phase in interactive mode

Example:
```bash
# Re-run specification phase
rm .dev_agent/documents/specification.md
dev-agent resume
```

### Branching Workflows

To try different approaches:

1. Backup current `.dev_agent/` directory
2. Try alternative approach
3. Compare results
4. Restore preferred version

Example:
```bash
# Backup current state
cp -r .dev_agent .dev_agent.backup

# Try alternative
dev-agent resume
# ... make changes ...

# Restore if needed
rm -rf .dev_agent
mv .dev_agent.backup .dev_agent
```

### Multi-Feature Development

For multiple features:

1. Complete workflow for Feature A
2. Commit documents to version control
3. Start new workflow for Feature B
4. Keep separate branches if needed

---

## Troubleshooting

### Phase Won't Complete

**Symptoms**: Phase hangs or fails repeatedly

**Solutions**:
1. Check Azure OpenAI connectivity: `dev-agent azure test`
2. Verify sufficient Azure quota
3. Check network connectivity
4. Review logs in `.dev_agent/logs/`
5. Try with `--verbose` flag

### Documents Not Generated

**Symptoms**: Phase completes but no document created

**Solutions**:
1. Check file permissions on `.dev_agent/documents/`
2. Verify disk space
3. Check for file system errors
4. Review error logs

### State Corruption

**Symptoms**: Cannot resume project, state errors

**Solutions**:
1. Restore from `.dev_agent/backups/`
2. Manually edit `state.json` if possible
3. Delete state and re-initialize
4. Contact support with logs

---

## See Also

- [Commands Reference](commands.md) - Complete command reference
- [Utility Commands](utility-commands.md) - Utility command details
- [CLI Examples](examples.md) - Practical workflow examples
- [Getting Started Guide](../getting-started/first-time-setup.md) - Initial setup
- [Troubleshooting Guide](../getting-started/troubleshooting.md) - Common issues
