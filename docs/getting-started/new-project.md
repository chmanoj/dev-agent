# New Project Journey

This guide walks you through creating a new project from scratch using dev-agent.

## Overview

When starting a new project, dev-agent helps you:

1. **Scaffold** project structure from templates
2. **Generate** initial specifications
3. **Design** system architecture
4. **Implement** features incrementally

**Estimated Time**: 30-60 minutes for initial setup and first feature

## Prerequisites

- Completed [First-Time Setup](first-time-setup.md)
- Azure OpenAI configured and tested
- Clear idea of what you want to build

## Step 1: Initialize New Project

Create a new project directory and initialize dev-agent:

```bash
# Create and navigate to project directory
mkdir my-awesome-project
cd my-awesome-project

# Initialize dev-agent
dev-agent init
```

### What Happens

```
🚀 Welcome to dev-agent!

Detected: Empty directory (new project)

Would you like to:
1. Create from template
2. Start with custom specification
3. Set up empty project structure

Choice: 1
```

## Step 2: Choose a Template

Select a template that matches your project type:

```
Available Templates:

1. FastAPI Web Service
   - REST API with async support
   - Database integration (SQLAlchemy)
   - Authentication & authorization
   - OpenAPI documentation

2. CLI Application
   - Typer-based CLI framework
   - Rich terminal output
   - Configuration management
   - Comprehensive help system

3. Data Processing Pipeline
   - Pandas/Polars data processing
   - ETL workflow orchestration
   - Data validation with Pydantic
   - Logging and monitoring

4. Machine Learning Project
   - Model training pipeline
   - Experiment tracking
   - Model serving API
   - Data preprocessing utilities

5. Custom (start from scratch)

Select template: 1
```

### Template Configuration

After selecting a template, you'll be prompted for project details:

```
Project Name: my-awesome-project
Description: A REST API for managing tasks
Author: Your Name
Python Version: 3.11
Database: PostgreSQL
Authentication: JWT

Generating project structure...
✓ Created project files
✓ Generated pyproject.toml
✓ Created directory structure
✓ Initialized git repository
```

## Step 3: Project Structure Created

Your project now has a complete structure:

```
my-awesome-project/
├── .dev_agent/              # dev-agent state and documents
│   ├── state.json
│   └── documents/
├── src/
│   └── my_awesome_project/
│       ├── __init__.py
│       ├── api/
│       ├── models/
│       ├── services/
│       └── config.py
├── tests/
│   ├── __init__.py
│   └── conftest.py
├── docs/
│   └── index.md
├── pyproject.toml
├── README.md
├── .gitignore
└── .env.example
```

## Step 4: Define Your First Feature

Now specify what you want to build:

```bash
# Start interactive mode
dev-agent

> I want to create a task management API with CRUD operations
```

Or use the specification command:

```bash
dev-agent spec create "Task management API with CRUD operations"
```

### Interactive Specification

dev-agent will ask clarifying questions:

```
📝 Let's define your feature...

What entities will your API manage?
> Tasks, Users, Projects

What operations do you need for Tasks?
> Create, Read, Update, Delete, List with filters

Should tasks have relationships to other entities?
> Yes, tasks belong to projects and are assigned to users

Any specific requirements?
> - Tasks should have priority levels
> - Support due dates and reminders
> - Track task status (todo, in_progress, done)
> - Audit trail for changes
```

## Step 5: Review Generated Specification

dev-agent generates a detailed specification:

```markdown
# Task Management API Specification

## Overview
REST API for managing tasks with support for projects and user assignments.

## Entities

### Task
- id: UUID (primary key)
- title: string (required, max 200 chars)
- description: text (optional)
- status: enum (todo, in_progress, done)
- priority: enum (low, medium, high)
- due_date: datetime (optional)
- project_id: UUID (foreign key)
- assigned_to: UUID (foreign key to User)
- created_at: datetime
- updated_at: datetime

### Endpoints

#### POST /api/v1/tasks
Create a new task
...
```

### Approve or Refine

```
📄 Specification generated!

View: .dev_agent/documents/specification.md

Options:
1. Approve and continue to design
2. Request changes
3. Add more details

Choice: 1
```

**Cost Summary**: ~$0.15 (500 prompt tokens, 2000 completion tokens)

## Step 6: Design Phase

dev-agent generates technical design:

```
🎨 Generating design document...

Analyzing:
✓ Template architecture patterns
✓ Database schema design
✓ API endpoint structure
✓ Authentication flow
✓ Error handling strategy

Design complete!
```

### Review Design Document

```markdown
# Task Management API Design

## Architecture

### Layer Structure
```
┌─────────────────────────────────────┐
│         API Layer (FastAPI)         │
├─────────────────────────────────────┤
│       Service Layer (Business)      │
├─────────────────────────────────────┤
│     Repository Layer (Data Access)  │
├─────────────────────────────────────┤
│         Database (PostgreSQL)       │
└─────────────────────────────────────┘
```

### Database Schema
```sql
CREATE TABLE tasks (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    title VARCHAR(200) NOT NULL,
    description TEXT,
    ...
);
```

### API Endpoints
- Authentication: JWT tokens
- Rate limiting: 100 requests/minute
- Pagination: Cursor-based
...
```

### Approve Design

```
Options:
1. Approve and continue to implementation
2. Request changes
3. Regenerate with different approach

Choice: 1
```

**Cost Summary**: ~$0.25 (800 prompt tokens, 3000 completion tokens)

## Step 7: Implementation Tasks

dev-agent breaks down implementation into tasks:

```
📋 Generating implementation tasks...

✓ Created 15 actionable tasks
✓ Organized by priority
✓ Estimated effort for each task

View: .dev_agent/documents/tasks.md
```

### Task Breakdown

```markdown
# Implementation Tasks

- [ ] 1. Set up database models and migrations
  - Create SQLAlchemy models for Task, User, Project
  - Generate Alembic migrations
  - Add database indexes
  - Requirements: Spec 2.1, 2.2

- [ ] 2. Implement repository layer
  - Create TaskRepository with CRUD operations
  - Add filtering and pagination
  - Implement transaction handling
  - Requirements: Spec 3.1

- [ ] 3. Create service layer
  - Implement TaskService business logic
  - Add validation rules
  - Handle relationships
  - Requirements: Spec 3.2

- [ ] 4. Build API endpoints
  - Create FastAPI routers
  - Add request/response models
  - Implement error handling
  - Requirements: Spec 4.1, 4.2
...
```

## Step 8: Implement Tasks

Start implementing tasks one by one:

```bash
# Generate code for first task
dev-agent implement task 1
```

### Code Generation

```python
# Generated: src/my_awesome_project/models/task.py

from sqlalchemy import Column, String, Enum, DateTime, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
import uuid
from datetime import datetime

from .base import Base

class Task(Base):
    """Task model for task management."""
    
    __tablename__ = "tasks"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    title = Column(String(200), nullable=False)
    description = Column(String, nullable=True)
    status = Column(Enum("todo", "in_progress", "done", name="task_status"))
    priority = Column(Enum("low", "medium", "high", name="task_priority"))
    due_date = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    project_id = Column(UUID(as_uuid=True), ForeignKey("projects.id"))
    assigned_to = Column(UUID(as_uuid=True), ForeignKey("users.id"))
    
    project = relationship("Project", back_populates="tasks")
    assignee = relationship("User", back_populates="assigned_tasks")
```

### Review and Refine

```
✓ Code generated for Task 1

Files created:
- src/my_awesome_project/models/task.py
- src/my_awesome_project/models/user.py
- src/my_awesome_project/models/project.py
- alembic/versions/001_initial_schema.py

Next steps:
1. Review generated code
2. Run tests: pytest
3. Apply migrations: alembic upgrade head
4. Continue to Task 2

Continue to next task? (y/n): y
```

**Cost Summary**: ~$0.30 per task (varies by complexity)

## Step 9: Iterative Development

Continue implementing tasks:

```bash
# Implement next task
dev-agent implement task 2

# Or implement multiple tasks
dev-agent implement tasks 2-5

# Or implement all remaining tasks
dev-agent implement all
```

### Progress Tracking

```bash
# Check project status
dev-agent status
```

```
📊 Project Status

Phase: Implementation
Progress: 5/15 tasks completed (33%)

Completed Tasks:
✓ 1. Set up database models and migrations
✓ 2. Implement repository layer
✓ 3. Create service layer
✓ 4. Build API endpoints
✓ 5. Add authentication

In Progress:
→ 6. Implement task filtering

Remaining: 9 tasks

Cost Summary:
- Indexing: $0.05
- Specification: $0.15
- Design: $0.25
- Implementation: $1.50
- Total: $1.95
```

## Step 10: Testing and Validation

After implementing tasks, test your application:

```bash
# Run tests
pytest

# Run linting
ruff check src tests

# Type checking
mypy src

# Start development server
uvicorn src.my_awesome_project.main:app --reload
```

### Generated Tests

dev-agent generates tests alongside code:

```python
# Generated: tests/test_task_service.py

import pytest
from src.my_awesome_project.services.task_service import TaskService
from src.my_awesome_project.models.task import Task

@pytest.mark.asyncio
async def test_create_task(task_service, sample_user, sample_project):
    """Test task creation."""
    task_data = {
        "title": "Test Task",
        "description": "Test Description",
        "status": "todo",
        "priority": "medium",
        "project_id": sample_project.id,
        "assigned_to": sample_user.id,
    }
    
    task = await task_service.create_task(task_data)
    
    assert task.id is not None
    assert task.title == "Test Task"
    assert task.status == "todo"
```

## Step 11: Documentation

Generate API documentation:

```bash
# Generate OpenAPI docs
dev-agent docs generate

# Build documentation site
mkdocs build

# Serve documentation locally
mkdocs serve
```

## Best Practices for New Projects

### 1. Start Small
Begin with core features, then expand:
```bash
# Phase 1: Core CRUD operations
dev-agent spec create "Basic task CRUD"

# Phase 2: Add relationships
dev-agent spec create "Task-project relationships"

# Phase 3: Advanced features
dev-agent spec create "Task filtering and search"
```

### 2. Review Generated Code
Always review and understand generated code:
- Check for security issues
- Verify business logic
- Ensure code quality
- Add custom logic as needed

### 3. Maintain Context
Keep dev-agent's context updated:
```bash
# Re-index after manual changes
dev-agent reindex

# Update specifications
dev-agent spec update
```

### 4. Cost Management
Monitor costs throughout development:
```bash
# Check costs before operations
dev-agent cost estimate

# View detailed cost report
dev-agent cost report

# Set budget limits
dev-agent config set preferences.budget_threshold 10.0
```

### 5. Version Control
Commit regularly with meaningful messages:
```bash
# After each task
git add .
git commit -m "feat: implement task CRUD operations"

# Include dev-agent documents
git add .dev_agent/documents/
git commit -m "docs: update specifications and design"
```

## Common Workflows

### Adding a New Feature

```bash
# 1. Create specification
dev-agent spec create "User notifications feature"

# 2. Generate design
dev-agent design generate

# 3. Create tasks
dev-agent tasks generate

# 4. Implement
dev-agent implement all
```

### Modifying Existing Feature

```bash
# 1. Update specification
dev-agent spec update "Add email notifications to tasks"

# 2. Regenerate affected design
dev-agent design regenerate

# 3. Generate new tasks
dev-agent tasks generate --incremental

# 4. Implement changes
dev-agent implement new
```

## Troubleshooting

See the [Troubleshooting Guide](troubleshooting.md) for common issues and solutions.

## Next Steps

- **Deploy**: Follow deployment guides for your platform
- **Monitor**: Set up logging and monitoring
- **Scale**: Optimize performance as needed
- **Maintain**: Use dev-agent for ongoing development

## Example Projects

Check out example projects in the `examples/` directory:
- `examples/fastapi-todo/` - Complete task management API
- `examples/cli-tool/` - CLI application example
- `examples/data-pipeline/` - Data processing example

## Support

For help with new projects:
- Review [documentation](../index.md)
- Check [examples](../examples/)
- Open an issue on GitHub
