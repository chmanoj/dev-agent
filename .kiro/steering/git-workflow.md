# Git Workflow Standards

## MANDATORY Git Workflow

### Branch Strategy (ENFORCED)
We use **Git Flow** with these permanent branches:

- **`main`** - Production-ready code, always deployable
- **`develop`** - Integration branch for features, latest development state
- **`feature/*`** - Feature development branches
- **`hotfix/*`** - Critical production fixes
- **`release/*`** - Release preparation branches

### Branch Naming (REQUIRED)
```bash
# Feature branches
feature/user-authentication
feature/api-documentation
feature/performance-optimization

# Hotfix branches  
hotfix/security-vulnerability
hotfix/critical-bug-fix

# Release branches
release/v1.2.0
release/v2.0.0-beta
```

### Development Workflow (MANDATORY)

#### 1. Feature Development
```bash
# Start from develop
git checkout develop
git pull origin develop

# Create feature branch
git checkout -b feature/your-feature-name

# Work on feature with frequent commits
git add .
git commit -m "feat: add user authentication endpoint"

# Push feature branch
git push -u origin feature/your-feature-name

# Create Pull Request to develop
# After review and approval, merge to develop
```

#### 2. Release Process
```bash
# Create release branch from develop
git checkout develop
git pull origin develop
git checkout -b release/v1.2.0

# Finalize release (version bumps, changelog)
git add .
git commit -m "chore: prepare release v1.2.0"

# Merge to main
git checkout main
git merge --no-ff release/v1.2.0
git tag -a v1.2.0 -m "Release version 1.2.0"

# Merge back to develop
git checkout develop
git merge --no-ff release/v1.2.0

# Push everything
git push origin main develop --tags
```

#### 3. Hotfix Process
```bash
# Create hotfix from main
git checkout main
git pull origin main
git checkout -b hotfix/critical-fix

# Fix the issue
git add .
git commit -m "fix: resolve critical security issue"

# Merge to main
git checkout main
git merge --no-ff hotfix/critical-fix
git tag -a v1.2.1 -m "Hotfix version 1.2.1"

# Merge to develop
git checkout develop
git merge --no-ff hotfix/critical-fix

# Push everything
git push origin main develop --tags
```

## Commit Standards (ENFORCED)

### Conventional Commits (REQUIRED)
All commits MUST follow [Conventional Commits](https://www.conventionalcommits.org/) format:

```
<type>[optional scope]: <description>

[optional body]

[optional footer(s)]
```

#### Commit Types (MANDATORY)
- **`feat:`** - New feature
- **`fix:`** - Bug fix
- **`docs:`** - Documentation changes
- **`style:`** - Code style changes (formatting, no logic change)
- **`refactor:`** - Code refactoring (no feature change or bug fix)
- **`perf:`** - Performance improvements
- **`test:`** - Adding or updating tests
- **`chore:`** - Maintenance tasks, dependency updates
- **`ci:`** - CI/CD configuration changes
- **`build:`** - Build system changes

#### Examples (CORRECT)
```bash
git commit -m "feat: add JWT authentication middleware"
git commit -m "fix: resolve memory leak in indexing engine"
git commit -m "docs: update API documentation for v2.0"
git commit -m "refactor: extract user service into separate module"
git commit -m "test: add integration tests for workflow phases"
git commit -m "chore: update dependencies to latest versions"
```

#### Examples (WRONG)
```bash
git commit -m "updated stuff"           # ❌ No type, vague
git commit -m "Fixed bug"               # ❌ No type, not descriptive
git commit -m "WIP"                     # ❌ Not descriptive
git commit -m "feat added new feature"  # ❌ Wrong format
```

### Commit Message Rules (ENFORCED)
1. **Use imperative mood** - "add feature" not "added feature"
2. **Start with lowercase** after the type
3. **No period at the end** of the description
4. **Keep description under 50 characters**
5. **Use body for detailed explanation** if needed
6. **Reference issues** in footer: "Closes #123"

#### Good Commit Example
```
feat(auth): add JWT token refresh mechanism

Implement automatic token refresh for expired JWT tokens.
This prevents users from being logged out unexpectedly
during long sessions.

- Add refresh token endpoint
- Update client-side token handling
- Add tests for token refresh flow

Closes #456
```

## Pull Request Standards (MANDATORY)

### PR Title Format
```
<type>[scope]: <description>
```

Examples:
- `feat(cli): add interactive configuration wizard`
- `fix(indexing): resolve file parsing errors`
- `docs: update installation guide for Windows`

### PR Description Template (REQUIRED)
```markdown
## Description
Brief description of changes

## Type of Change
- [ ] Bug fix (non-breaking change which fixes an issue)
- [ ] New feature (non-breaking change which adds functionality)
- [ ] Breaking change (fix or feature that would cause existing functionality to not work as expected)
- [ ] Documentation update

## Testing
- [ ] Tests pass locally
- [ ] Added tests for new functionality
- [ ] Updated documentation

## Checklist
- [ ] Code follows project style guidelines
- [ ] Self-review completed
- [ ] Documentation updated
- [ ] No breaking changes (or breaking changes documented)

## Related Issues
Closes #123
```

### PR Review Requirements (ENFORCED)
- **At least 1 approval** required for merge
- **All CI checks** must pass
- **No merge conflicts** allowed
- **Branch must be up-to-date** with target
- **Squash and merge** for feature branches

## Git Configuration (REQUIRED)

### Global Git Setup
```bash
# Set user information
git config --global user.name "Your Name"
git config --global user.email "your.email@example.com"

# Set default branch name
git config --global init.defaultBranch main

# Set pull strategy
git config --global pull.rebase false

# Enable automatic cleanup
git config --global fetch.prune true

# Set default editor
git config --global core.editor "code --wait"  # VS Code
# or
git config --global core.editor "vim"          # Vim
```

### Project-Specific Hooks
```bash
# Install pre-commit hooks (MANDATORY)
uv run pre-commit install

# Install commit message hook
uv run pre-commit install --hook-type commit-msg
```

## Branch Protection Rules (ENFORCED)

### Main Branch Protection
- **Require pull request reviews** (1 reviewer minimum)
- **Require status checks** to pass before merging
- **Require branches to be up to date** before merging
- **Restrict pushes** that create merge commits
- **Do not allow force pushes**
- **Do not allow deletions**

### Develop Branch Protection
- **Require pull request reviews** (1 reviewer minimum)
- **Require status checks** to pass before merging
- **Allow force pushes** (for maintainers only)

## Git Commands Reference

### Daily Workflow
```bash
# Start new feature
git checkout develop
git pull origin develop
git checkout -b feature/my-feature

# Regular commits
git add .
git commit -m "feat: implement user authentication"

# Push feature branch
git push -u origin feature/my-feature

# Update feature branch with latest develop
git checkout develop
git pull origin develop
git checkout feature/my-feature
git rebase develop

# Clean up after merge
git checkout develop
git pull origin develop
git branch -d feature/my-feature
git push origin --delete feature/my-feature
```

### Useful Git Aliases
Add to `~/.gitconfig`:
```ini
[alias]
    co = checkout
    br = branch
    ci = commit
    st = status
    unstage = reset HEAD --
    last = log -1 HEAD
    visual = !gitk
    tree = log --graph --pretty=format:'%Cred%h%Creset -%C(yellow)%d%Creset %s %Cgreen(%cr) %C(bold blue)<%an>%Creset' --abbrev-commit
    cleanup = "!git branch --merged | grep -v '\\*\\|main\\|develop' | xargs -n 1 git branch -d"
```

## Troubleshooting

### Common Issues

#### Merge Conflicts
```bash
# Resolve conflicts manually, then:
git add .
git commit -m "resolve: merge conflicts with develop"
```

#### Wrong Branch
```bash
# Move commits to correct branch
git checkout correct-branch
git cherry-pick <commit-hash>
git checkout wrong-branch
git reset --hard HEAD~1
```

#### Accidental Commit to Main
```bash
# Create feature branch from current state
git checkout -b feature/accidental-commits

# Reset main to origin
git checkout main
git reset --hard origin/main
```

### Recovery Commands
```bash
# Undo last commit (keep changes)
git reset --soft HEAD~1

# Undo last commit (discard changes)
git reset --hard HEAD~1

# Recover deleted branch
git reflog
git checkout -b recovered-branch <commit-hash>

# Clean up local branches
git remote prune origin
git branch -vv | grep ': gone]' | awk '{print $1}' | xargs git branch -d
```

## Automation and Tools

### Pre-commit Configuration
Already configured in `.pre-commit-config.yaml`:
- Conventional commit message validation
- Code formatting with Ruff
- Type checking with mypy
- Documentation validation

### GitHub Actions
CI/CD pipeline automatically:
- Runs tests on all PRs
- Validates commit messages
- Checks code quality
- Builds documentation
- Creates releases from tags

### Release Automation
```bash
# Automated release process
make release-patch   # 1.0.0 -> 1.0.1
make release-minor   # 1.0.0 -> 1.1.0
make release-major   # 1.0.0 -> 2.0.0
```

Remember: These are not suggestions - they are REQUIREMENTS for all development work on this project.