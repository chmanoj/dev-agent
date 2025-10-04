# Best Practices Guide

## Overview

This guide provides proven best practices for using dev-agent effectively. Following these recommendations will help you get better results, reduce costs, and integrate dev-agent smoothly into your development workflow.

## Project Setup

### Initial Configuration

#### 1. Clean Your Codebase First

Before indexing, remove unnecessary files:

```bash
# Remove build artifacts
rm -rf dist/ build/ *.egg-info/

# Remove cache files
find . -type d -name "__pycache__" -exec rm -rf {} +
find . -type f -name "*.pyc" -delete

# Remove coverage reports
rm -rf htmlcov/ .coverage

# Remove documentation builds
rm -rf docs/site/
```

**Why**: Reduces indexing time and cost, improves pattern detection

#### 2. Configure Exclusions

Create `.dev_agent/config.json`:

```json
{
  "exclude_patterns": [
    "node_modules/",
    "venv/",
    ".venv/",
    "dist/",
    "build/",
    "*.egg-info/",
    "__pycache__/",
    "*.pyc",
    ".pytest_cache/",
    ".mypy_cache/",
    "htmlcov/",
    ".coverage",
    "docs/site/",
    "*.min.js",
    "*.min.css",
    "migrations/",
    "*.log"
  ],
  "include_patterns": [
    "*.py",
    "*.md",
    "*.txt",
    "*.yaml",
    "*.yml",
    "*.toml"
  ]
}
```

**Why**: Focuses indexing on relevant source code

#### 3. Set Budget Limits

```bash
# Set reasonable budget limits
dev-agent config set daily_budget 10.00
dev-agent config set feature_budget 2.00
dev-agent config set budget_warnings true
```

**Why**: Prevents unexpected costs

#### 4. Enable Caching

```bash
# Enable embedding cache (default)
dev-agent config set embedding_cache true

# Enable incremental indexing
dev-agent config set incremental_indexing true
```

**Why**: Reduces costs on repeated operations

### Azure OpenAI Configuration

#### Use Environment Variables

```bash
# .env file (add to .gitignore)
AZURE_OPENAI_ENDPOINT=https://your-resource.openai.azure.com/
AZURE_OPENAI_API_KEY=your-api-key-here
AZURE_OPENAI_API_VERSION=2024-02-15-preview
AZURE_OPENAI_DEPLOYMENT_NAME=gpt-4
AZURE_OPENAI_EMBEDDING_DEPLOYMENT=text-embedding-ada-002
```

**Why**: Keeps credentials secure and out of version control

#### Validate Configuration

```bash
# Test Azure OpenAI connection
dev-agent validate

# Expected output:
✅ Azure OpenAI Configuration Valid
✅ API Connection Successful
✅ Deployment Accessible
✅ Embedding Model Available
```

**Why**: Catches configuration issues early

## Workflow Best Practices

### Indexing Phase

#### 1. Index Once, Use Multiple Times

```bash
# Index your project
dev-agent init /path/to/project

# Work on multiple features without re-indexing
dev-agent resume /path/to/project
# Work on feature 1

dev-agent resume /path/to/project
# Work on feature 2
```

**Why**: Saves indexing costs

#### 2. Use Incremental Indexing

```bash
# After making changes to codebase
dev-agent index --incremental

# Only changed files are re-indexed
```

**Why**: 80-95% faster and cheaper than full re-index

#### 3. Review Indexing Summary

```bash
# After indexing completes, review:
# - Number of files indexed
# - Patterns detected
# - Languages found
# - Token usage
```

**Why**: Ensures indexing captured your codebase correctly

### Specification Phase

#### 1. Be Specific and Detailed

❌ **Bad**:
```
"Add authentication"
```

✅ **Good**:
```
"Add JWT-based user authentication with the following requirements:
- Email/password login with bcrypt hashing
- Access token (15 min expiry) and refresh token (7 day expiry)
- Role-based access control (admin, user, guest)
- Password reset via email with secure tokens
- Rate limiting on login attempts (5 attempts per 15 minutes)
- Follow existing authentication patterns in auth/session_manager.py
- Use existing User model in models/user.py
- Integrate with existing FastAPI middleware"
```

**Why**: Detailed requirements lead to better specifications on first try

#### 2. Reference Existing Code

```
"Implement user notifications similar to the email notification system
in notifications/email_notifier.py, but for in-app notifications.
Follow the same pattern of:
- NotificationService base class
- Async delivery
- Template-based messages
- Retry logic with exponential backoff"
```

**Why**: Helps dev-agent understand your patterns and conventions

#### 3. Include Edge Cases

```
"Handle edge cases:
- User already exists during registration
- Invalid credentials during login
- Expired tokens
- Concurrent login attempts
- Password reset token expiration
- Email delivery failures"
```

**Why**: Comprehensive specifications reduce implementation issues

#### 4. Review Before Approving

Checklist:
- [ ] All functional requirements covered
- [ ] Technical requirements match your stack
- [ ] Security considerations included
- [ ] Error handling specified
- [ ] Testing requirements clear
- [ ] Dependencies listed
- [ ] Acceptance criteria defined

**Why**: Approval locks in the specification for subsequent phases

### Design Phase

#### 1. Verify Architecture Alignment

Check that the design:
- Follows your existing architecture patterns
- Uses your current tech stack
- Integrates with existing components
- Maintains consistency with your conventions

**Why**: Prevents architectural drift

#### 2. Review Data Models

Ensure data models:
- Match your database schema conventions
- Use your ORM patterns (SQLAlchemy, Django ORM, etc.)
- Include proper validation
- Handle relationships correctly

**Why**: Data model issues are expensive to fix later

#### 3. Check API Design

For API endpoints, verify:
- URL patterns match your conventions
- Request/response formats are consistent
- Authentication/authorization is included
- Error responses follow your standards

**Why**: API consistency is critical for maintainability

#### 4. Validate Security Design

Review:
- Authentication mechanisms
- Authorization checks
- Input validation
- Data encryption
- Secure defaults

**Why**: Security issues are critical and hard to retrofit

### Implementation Phase

#### 1. Review Task Order

Ensure tasks:
- Build on each other logically
- Can be completed independently
- Have clear dependencies
- Include testing at each step

**Why**: Proper task order enables smooth implementation

#### 2. Verify Task Granularity

Each task should:
- Take 1-4 hours to complete
- Have clear acceptance criteria
- Be testable independently
- Produce working code

**Why**: Small tasks are easier to complete and verify

#### 3. Check Test Coverage

Ensure tasks include:
- Unit tests for core logic
- Integration tests for components
- End-to-end tests for workflows
- Edge case testing

**Why**: Testing catches issues early

## Code Generation Best Practices

### 1. Generate One Task at a Time

```bash
# ✅ Good: Focus on one task
dev-agent generate --task 1
# Review, test, commit

dev-agent generate --task 2
# Review, test, commit

# ❌ Bad: Generate everything at once
dev-agent generate --all
```

**Why**: Easier to review and debug

### 2. Always Review Generated Code

Never commit generated code without review:

```bash
# Generate code
dev-agent generate --task 1

# Review the code
git diff

# Test the code
pytest tests/test_new_feature.py

# Make necessary adjustments
# Then commit
git add .
git commit -m "feat: implement user authentication (task 1)"
```

**Why**: AI-generated code may need adjustments

### 3. Test Incrementally

```bash
# After each task
pytest tests/test_current_task.py

# Run full test suite periodically
pytest

# Check coverage
pytest --cov=your_package
```

**Why**: Catches issues early when they're easier to fix

### 4. Commit Frequently

```bash
# Commit after each completed task
git add .
git commit -m "feat: add User model and validation (task 1)"

# Push regularly
git push origin feature/user-authentication
```

**Why**: Creates clear history and enables easy rollback

## Code Quality

### 1. Run Linters and Formatters

```bash
# Format code
ruff format .

# Check for issues
ruff check .

# Fix auto-fixable issues
ruff check --fix .

# Type checking
mypy your_package
```

**Why**: Maintains code quality standards

### 2. Update Documentation

```bash
# Update docstrings
# Update README.md
# Update API documentation
# Update CHANGELOG.md
```

**Why**: Keeps documentation in sync with code

### 3. Review Type Hints

Ensure generated code has:
- Type hints on all functions
- Proper return type annotations
- Generic types properly parameterized
- No `Any` types unless necessary

**Why**: Type safety prevents bugs

## Cost Optimization

### 1. Approve on First Try

**Strategy**: Invest time in detailed requirements

```bash
# Spend 10 minutes writing detailed requirements
# Save 50% on regeneration costs
```

**Why**: Each regeneration doubles phase cost

### 2. Use Embedding Cache

```bash
# Verify cache is enabled
dev-agent config show | grep embedding_cache

# Check cache hit rate
dev-agent status --detailed
```

**Why**: Eliminates redundant embedding generation

### 3. Batch Related Features

```bash
# Work on related features in one session
dev-agent init project

# Feature 1: User authentication
dev-agent resume project
# Complete feature 1

# Feature 2: User profile (related)
dev-agent resume project
# Complete feature 2 (reuses index)
```

**Why**: Shares indexing cost across features

### 4. Monitor Costs Regularly

```bash
# Check costs during development
dev-agent status

# Review detailed costs
dev-agent cost --detailed

# Analyze trends
dev-agent cost --trends
```

**Why**: Identifies optimization opportunities

## Security Best Practices

### 1. Never Commit API Keys

```bash
# Add to .gitignore
echo ".env" >> .gitignore
echo ".dev_agent/credentials.json" >> .gitignore

# Use environment variables
export AZURE_OPENAI_API_KEY=your-key-here
```

**Why**: Prevents credential leaks

### 2. Review Generated Security Code

Pay special attention to:
- Authentication logic
- Authorization checks
- Input validation
- SQL queries (injection prevention)
- Password handling
- Token generation

**Why**: Security bugs are critical

### 3. Use Secure Defaults

Ensure generated code:
- Uses HTTPS
- Validates all inputs
- Sanitizes outputs
- Implements rate limiting
- Logs security events

**Why**: Security should be built-in, not added later

### 4. Audit Generated Code

```bash
# Run security checks
ruff check --select S .

# Check for common vulnerabilities
bandit -r your_package

# Review dependencies
pip-audit
```

**Why**: Catches security issues early

## Team Collaboration

### 1. Share Configuration

```bash
# Commit shared configuration
git add .dev_agent/config.json
git commit -m "chore: add dev-agent configuration"

# Document in README
```

**Why**: Ensures consistent behavior across team

### 2. Document Workflow

```markdown
# In your README.md

## Using dev-agent

1. Set up Azure OpenAI credentials (see docs/azure-setup.md)
2. Index the project: `dev-agent init .`
3. Work on features: `dev-agent resume .`
4. Follow the four-phase workflow
5. Review and test all generated code
```

**Why**: Helps team members get started

### 3. Review Generated Code

```bash
# Create PR for generated code
git checkout -b feature/user-auth
# Generate and test code
git push origin feature/user-auth

# Request code review
# Treat AI-generated code like any other code
```

**Why**: Maintains code quality standards

### 4. Share Best Practices

```bash
# Document team-specific practices
docs/dev-agent-practices.md

# Include:
# - Common patterns to reference
# - Typical feature costs
# - Approval criteria
# - Testing requirements
```

**Why**: Improves team efficiency

## Troubleshooting

### Common Issues and Solutions

#### Issue: Indexing Takes Too Long

**Solutions**:
1. Add exclusion patterns for large directories
2. Remove generated files before indexing
3. Use incremental indexing for updates
4. Check for large binary files

#### Issue: Generated Code Doesn't Match Style

**Solutions**:
1. Ensure codebase is well-indexed
2. Reference specific files in requirements
3. Include style guide in project
4. Review and adjust generated code

#### Issue: High Costs

**Solutions**:
1. Enable embedding cache
2. Reduce regenerations (better requirements)
3. Optimize exclusion patterns
4. Batch related features

#### Issue: Specifications Too Generic

**Solutions**:
1. Provide more detailed requirements
2. Reference specific code examples
3. Include edge cases and constraints
4. Specify technical requirements

## Performance Tips

### 1. Optimize Indexing

```bash
# Use parallel processing
dev-agent config set parallel_indexing true

# Adjust batch size
dev-agent config set embedding_batch_size 16

# Use incremental indexing
dev-agent config set incremental_indexing true
```

### 2. Optimize Context Retrieval

```json
{
  "max_context_chunks": 5,
  "max_chunk_size": 500,
  "similarity_threshold": 0.7
}
```

### 3. Use Appropriate Models

```bash
# Use GPT-3.5 for simple tasks
dev-agent config set simple_task_model gpt-35-turbo

# Use GPT-4 for complex tasks
dev-agent config set complex_task_model gpt-4
```

## Maintenance

### Regular Tasks

#### Weekly

- [ ] Review cost reports
- [ ] Update exclusion patterns if needed
- [ ] Clear old cache entries
- [ ] Update Azure OpenAI credentials if rotated

#### Monthly

- [ ] Analyze cost trends
- [ ] Review and optimize configuration
- [ ] Update dev-agent to latest version
- [ ] Review and update documentation

#### Quarterly

- [ ] Full codebase re-index
- [ ] Review and update best practices
- [ ] Train team on new features
- [ ] Audit security practices

## Checklist for Success

### Before Starting a Feature

- [ ] Codebase is clean and up-to-date
- [ ] Azure OpenAI credentials are valid
- [ ] Budget limits are set
- [ ] Exclusion patterns are configured
- [ ] Embedding cache is enabled

### During Development

- [ ] Requirements are detailed and specific
- [ ] Each phase is reviewed before approval
- [ ] Generated code is tested incrementally
- [ ] Costs are monitored regularly
- [ ] Code is committed frequently

### After Completion

- [ ] All tests pass
- [ ] Code quality checks pass
- [ ] Documentation is updated
- [ ] Cost report is reviewed
- [ ] Code is reviewed by team

## Next Steps

- Review [Four-Phase Workflow](four-phase-workflow.md)
- Learn about [Cost Management](cost-management.md)
- Explore [Advanced Usage](advanced-usage.md)
- Check [CLI Reference](../cli-reference/commands.md)
