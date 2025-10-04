# Existing Codebase Journey

This guide walks you through using dev-agent to analyze, document, and enhance an existing codebase.

## Overview

When working with an existing codebase, dev-agent helps you:

1. **Index** and understand the codebase structure
2. **Document** existing functionality
3. **Generate** specifications for new features
4. **Maintain** consistency with existing patterns

**Estimated Time**: 15-30 minutes for indexing, plus time for feature development

## Prerequisites

- Completed [First-Time Setup](first-time-setup.md)
- Azure OpenAI configured and tested
- Access to the codebase you want to analyze

## Step 1: Navigate to Your Project

```bash
# Navigate to your existing project
cd /path/to/your/project

# Verify it's a Python project
ls pyproject.toml  # or setup.py, requirements.txt
```

## Step 2: Initialize dev-agent

```bash
# Initialize dev-agent in the project
dev-agent init
```

### Automatic Detection

```
🔍 Analyzing project...

Detected: Existing Python codebase

Project Analysis:
- Language: Python 3.11
- Files: 247 Python files
- Lines of Code: ~15,000
- Frameworks: FastAPI, SQLAlchemy, Pydantic
- Test Framework: pytest

Estimated indexing time: 3-5 minutes
Estimated cost: $0.50 - $1.00

Proceed with indexing? (y/n): y
```

## Step 3: Indexing Phase

dev-agent analyzes your codebase:

```
📚 Indexing codebase...

[████████████████████░░░░] 80% (198/247 files)

Processing:
✓ src/api/routes/users.py
✓ src/api/routes/tasks.py
✓ src/services/user_service.py
→ src/services/task_service.py
  ...
```

### What's Being Analyzed

1. **Code Structure**
   - Classes and functions
   - Imports and dependencies
   - Type annotations
   - Docstrings

2. **Patterns**
   - Architectural patterns
   - Naming conventions
   - Error handling approaches
   - Testing patterns

3. **Relationships**
   - Module dependencies
   - Class hierarchies
   - Function call graphs
   - Data flow

### Indexing Progress

```
📊 Indexing Progress

Phase 1: Parsing (50%)
- Tree-sitter AST parsing
- Extracting code elements
- Building dependency graph

Phase 2: Embedding (30%)
- Generating semantic embeddings
- Batch processing (16 items/batch)
- Caching embeddings

Phase 3: Storage (20%)
- Storing in FAISS vector database
- Creating search indices
- Saving metadata
```

## Step 4: Indexing Complete

```
✅ Indexing Complete!

Summary:
- Files indexed: 247
- Functions found: 1,234
- Classes found: 156
- Test files: 89
- Documentation: 45 docstrings

Patterns Detected:
✓ Repository pattern for data access
✓ Service layer for business logic
✓ Pydantic models for validation
✓ FastAPI dependency injection
✓ pytest fixtures for testing

Frameworks:
- FastAPI 0.104.0
- SQLAlchemy 2.0.23
- Pydantic 2.5.0
- pytest 7.4.3

Cost: $0.75 (15,000 tokens)
Time: 4m 23s

Next steps:
1. Generate documentation: dev-agent docs generate
2. Add new feature: dev-agent spec create "feature description"
3. View project status: dev-agent status
```

## Step 5: Understanding Your Codebase

### View Project Structure

```bash
# View high-level structure
dev-agent analyze structure
```

```
📁 Project Structure

src/
├── api/              (FastAPI routes)
│   ├── routes/       15 route modules
│   ├── dependencies/ 8 dependency providers
│   └── middleware/   5 middleware components
├── services/         (Business logic)
│   ├── user_service.py
│   ├── task_service.py
│   └── ...          12 service modules
├── models/           (Data models)
│   ├── user.py
│   ├── task.py
│   └── ...          18 model files
├── repositories/     (Data access)
│   └── ...          12 repository classes
└── config/           (Configuration)
    └── settings.py

tests/
├── unit/            67 test files
├── integration/     22 test files
└── conftest.py      (Shared fixtures)
```

### Analyze Patterns

```bash
# View detected patterns
dev-agent analyze patterns
```

```
🔍 Detected Patterns

Architecture:
- Layered architecture (API → Service → Repository → Database)
- Dependency injection via FastAPI
- Repository pattern for data access
- Service layer for business logic

Code Style:
- Type hints on all functions
- Google-style docstrings
- Async/await for I/O operations
- Pydantic models for validation

Testing:
- pytest with fixtures
- Separate unit and integration tests
- Mock external dependencies
- 85% test coverage

Error Handling:
- Custom exception hierarchy
- Centralized error handler
- Structured error responses
- Logging with context
```

### Search Codebase

```bash
# Semantic search
dev-agent search "user authentication logic"
```

```
🔎 Search Results

1. src/services/auth_service.py:45
   async def authenticate_user(username: str, password: str) -> User:
       """Authenticate user with username and password."""
       ...

2. src/api/dependencies/auth.py:12
   async def get_current_user(token: str = Depends(oauth2_scheme)) -> User:
       """Get current authenticated user from JWT token."""
       ...

3. tests/test_auth_service.py:23
   async def test_authenticate_user_success():
       """Test successful user authentication."""
       ...
```

## Step 6: Generate Documentation

Document your existing codebase:

```bash
# Generate comprehensive documentation
dev-agent docs generate
```

```
📝 Generating Documentation...

Creating:
✓ API documentation (OpenAPI/Swagger)
✓ Architecture overview
✓ Module documentation
✓ Database schema documentation
✓ Deployment guide

Output: docs/
```

### Generated Documentation

```
docs/
├── index.md              (Project overview)
├── architecture.md       (System architecture)
├── api/
│   ├── endpoints.md      (API endpoints)
│   └── authentication.md (Auth flow)
├── database/
│   └── schema.md         (Database schema)
└── development/
    ├── setup.md          (Development setup)
    └── testing.md        (Testing guide)
```

## Step 7: Adding New Features

Now that your codebase is indexed, add new features:

```bash
# Create specification for new feature
dev-agent spec create "Add task comments and attachments"
```

### Context-Aware Specification

```
📝 Analyzing existing codebase for context...

Found relevant code:
- Task model: src/models/task.py
- Task service: src/services/task_service.py
- Task repository: src/repositories/task_repository.py
- Task API: src/api/routes/tasks.py

Detected patterns:
- SQLAlchemy models with relationships
- Service layer with validation
- Repository pattern for data access
- FastAPI routes with Pydantic schemas

Generating specification that matches your existing patterns...
```

### Generated Specification

```markdown
# Task Comments and Attachments Specification

## Overview
Add support for comments and file attachments to tasks, following
existing architectural patterns.

## Data Models

### Comment Model (following existing pattern)
```python
class Comment(Base):
    """Task comment model - follows pattern from Task model."""
    
    __tablename__ = "comments"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    content = Column(Text, nullable=False)
    task_id = Column(UUID(as_uuid=True), ForeignKey("tasks.id"))
    author_id = Column(UUID(as_uuid=True), ForeignKey("users.id"))
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships (following existing pattern)
    task = relationship("Task", back_populates="comments")
    author = relationship("User", back_populates="comments")
```

### Service Layer (following existing pattern)
- CommentService with CRUD operations
- Validation using Pydantic schemas
- Error handling matching existing services
...
```

## Step 8: Implement New Feature

Generate implementation tasks:

```bash
# Generate tasks
dev-agent tasks generate
```

```
📋 Implementation Tasks

Based on your existing codebase patterns:

- [ ] 1. Create Comment and Attachment models
  - Follow existing SQLAlchemy model pattern
  - Add relationships to Task model
  - Create Alembic migration
  - Location: src/models/comment.py, src/models/attachment.py

- [ ] 2. Implement CommentRepository
  - Follow existing repository pattern
  - Add CRUD operations
  - Implement filtering and pagination
  - Location: src/repositories/comment_repository.py

- [ ] 3. Create CommentService
  - Follow existing service layer pattern
  - Add business logic and validation
  - Handle file uploads for attachments
  - Location: src/services/comment_service.py

- [ ] 4. Add API endpoints
  - Follow existing FastAPI route pattern
  - Use existing authentication dependency
  - Add Pydantic request/response schemas
  - Location: src/api/routes/comments.py
...
```

### Implement Tasks

```bash
# Implement first task
dev-agent implement task 1
```

```
✓ Generated code following your existing patterns

Created:
- src/models/comment.py (matches Task model style)
- src/models/attachment.py (matches Task model style)
- alembic/versions/002_add_comments.py (follows migration pattern)

The generated code:
✓ Uses your existing base model
✓ Follows your naming conventions
✓ Matches your type annotation style
✓ Uses your relationship patterns
✓ Includes docstrings in your format

Review the code and run:
  pytest tests/test_comment_model.py
  alembic upgrade head
```

## Step 9: Maintain Consistency

### Re-index After Changes

```bash
# Re-index to include your manual changes
dev-agent reindex
```

```
🔄 Re-indexing...

Detecting changes:
- Modified: 3 files
- Added: 5 files
- Deleted: 0 files

Incremental indexing:
✓ Processing only changed files
✓ Updating embeddings
✓ Refreshing patterns

Complete! (45 seconds, $0.05)
```

### Validate Consistency

```bash
# Check if new code matches existing patterns
dev-agent validate consistency
```

```
✅ Consistency Check

Code Style: ✓ Matches existing style
Type Hints: ✓ All functions annotated
Docstrings: ✓ Google-style format
Error Handling: ✓ Uses custom exceptions
Testing: ✓ Tests follow existing patterns
Imports: ✓ Organized correctly

Warnings:
⚠ New function missing docstring: src/services/comment_service.py:45
⚠ Consider adding integration test for comment API

Overall: 95% consistent with existing codebase
```

## Best Practices for Existing Codebases

### 1. Index Before Making Changes

Always index first to understand the codebase:
```bash
# Index before starting work
dev-agent init

# Analyze patterns
dev-agent analyze patterns

# Search for similar code
dev-agent search "similar functionality"
```

### 2. Use Semantic Search

Find relevant code quickly:
```bash
# Find authentication code
dev-agent search "user authentication"

# Find error handling examples
dev-agent search "error handling"

# Find test examples
dev-agent search "test fixtures"
```

### 3. Generate Documentation

Keep documentation up-to-date:
```bash
# Generate after major changes
dev-agent docs generate

# Update specific sections
dev-agent docs update api

# Generate architecture diagrams
dev-agent docs diagrams
```

### 4. Maintain Context

Keep dev-agent's understanding current:
```bash
# Re-index after pulling changes
git pull
dev-agent reindex

# Update after refactoring
dev-agent reindex --full

# Verify patterns still detected
dev-agent analyze patterns
```

### 5. Incremental Development

Add features incrementally:
```bash
# Small, focused features
dev-agent spec create "Add email notifications"

# Build on existing features
dev-agent spec create "Extend task filtering"

# Refactor existing code
dev-agent spec create "Refactor user service"
```

## Common Workflows

### Understanding Legacy Code

```bash
# 1. Index the codebase
dev-agent init

# 2. Generate documentation
dev-agent docs generate

# 3. Analyze architecture
dev-agent analyze structure

# 4. Search for specific functionality
dev-agent search "payment processing"

# 5. View dependencies
dev-agent analyze dependencies
```

### Adding Feature to Existing Module

```bash
# 1. Search for similar features
dev-agent search "similar feature"

# 2. Create specification
dev-agent spec create "New feature description"

# 3. Review generated design
# (will match existing patterns)

# 4. Implement incrementally
dev-agent implement task 1
```

### Refactoring Existing Code

```bash
# 1. Document current state
dev-agent docs generate

# 2. Create refactoring spec
dev-agent spec create "Refactor user service to use repository pattern"

# 3. Generate refactoring tasks
dev-agent tasks generate

# 4. Implement with tests
dev-agent implement all --with-tests
```

### Onboarding New Team Members

```bash
# 1. Generate comprehensive docs
dev-agent docs generate --comprehensive

# 2. Create architecture overview
dev-agent docs architecture

# 3. Generate code examples
dev-agent docs examples

# 4. Create development guide
dev-agent docs development-guide
```

## Working with Large Codebases

### Performance Optimization

For large codebases (10,000+ files):

```bash
# Index with filters
dev-agent init --exclude "tests/*,docs/*,build/*"

# Index specific directories
dev-agent init --include "src/*"

# Use incremental indexing
dev-agent reindex --incremental
```

### Managing Costs

```bash
# Estimate before indexing
dev-agent cost estimate

# Set budget limits
dev-agent config set preferences.budget_threshold 5.0

# Use caching
dev-agent config set preferences.cache_embeddings true

# Monitor costs
dev-agent cost report
```

## Troubleshooting

### Indexing Issues

```bash
# If indexing fails
dev-agent init --verbose

# Skip problematic files
dev-agent init --skip-errors

# Re-index specific files
dev-agent reindex src/specific/file.py
```

### Pattern Detection Issues

```bash
# Force pattern re-detection
dev-agent analyze patterns --refresh

# View detailed pattern analysis
dev-agent analyze patterns --verbose

# Manually specify patterns
dev-agent config set patterns.architecture "layered"
```

### Search Not Finding Code

```bash
# Re-index to update embeddings
dev-agent reindex

# Use more specific search terms
dev-agent search "exact function name"

# Search by file path
dev-agent search --path "src/services/*"
```

## Integration with Existing Tools

### Git Integration

```bash
# Index only changed files
git diff --name-only | xargs dev-agent reindex

# Generate docs on commit
git commit -m "feat: add comments" && dev-agent docs generate
```

### CI/CD Integration

```yaml
# .github/workflows/dev-agent.yml
name: dev-agent Documentation

on: [push]

jobs:
  docs:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
      - name: Generate docs
        run: |
          dev-agent reindex
          dev-agent docs generate
      - name: Deploy docs
        run: mkdocs gh-deploy
```

### IDE Integration

```bash
# VS Code: Add to tasks.json
{
  "label": "dev-agent: Search",
  "type": "shell",
  "command": "dev-agent search '${input:searchQuery}'"
}
```

## Next Steps

- **Explore**: Use semantic search to understand the codebase
- **Document**: Generate comprehensive documentation
- **Enhance**: Add new features maintaining consistency
- **Maintain**: Keep dev-agent context updated

## Support

For help with existing codebases:
- Review [Troubleshooting Guide](troubleshooting.md)
- Check [documentation](../index.md)
- Open an issue on GitHub
