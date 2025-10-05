# Release Guide for dev-agent v1.0.0

This guide outlines the steps to complete the v1.0.0 release of dev-agent.

## Completed Steps ✅

1. **Version Update**: Updated `pyproject.toml` from v0.1.0 to v1.0.0
2. **Repository Cleanup**: Cleaned up 3,307 files and 316 directories (157.63 MB reduction)
3. **Changelog Update**: Updated `CHANGELOG.md` with all v1.0.0 changes

## Remaining Steps

### 1. Build and Test Documentation

Build the documentation locally to ensure everything works:

```bash
# Install documentation dependencies
uv sync --group docs

# Build documentation
uv run mkdocs build --strict

# Serve locally to review
uv run mkdocs serve
```

Visit http://127.0.0.1:8000 to review the documentation.

### 2. Deploy Documentation to GitHub Pages

Once documentation is verified:

```bash
# Deploy to GitHub Pages
uv run mkdocs gh-deploy
```

This will:
- Build the documentation
- Push to the `gh-pages` branch
- Make it available at your GitHub Pages URL

### 3. Run Final Quality Checks

Ensure all tests pass and code quality is maintained:

```bash
# Run all quality checks
make quality

# Run full test suite with coverage
make test

# Run CI checks locally
make ci
```

### 4. Commit and Push Changes

Commit the version bump and changelog updates:

```bash
# Stage changes
git add pyproject.toml CHANGELOG.md RELEASE_GUIDE.md

# Commit with conventional commit message
git commit -m "chore: prepare release v1.0.0

- Update version to 1.0.0
- Update CHANGELOG with all v1.0.0 changes
- Clean up repository (157.63 MB reduction)
- Add release guide documentation"

# Push to main branch
git push origin main
```

### 5. Create GitHub Release

1. Go to your GitHub repository
2. Click on "Releases" → "Draft a new release"
3. Create a new tag: `v1.0.0`
4. Release title: `v1.0.0 - Production Ready Release`
5. Copy the v1.0.0 section from CHANGELOG.md into the release notes
6. Attach any relevant files (optional)
7. Click "Publish release"

**Release Notes Template:**

```markdown
# dev-agent v1.0.0 - Production Ready Release

This is the first production-ready release of dev-agent, featuring comprehensive Azure OpenAI integration, enhanced CLI experience, and extensive documentation.

## 🎉 Highlights

- **Azure OpenAI Integration**: Full integration with GPT-4 and text-embedding-ada-002
- **Enhanced CLI**: Rich terminal output, progress indicators, and interactive feedback
- **Comprehensive Documentation**: Complete MkDocs documentation with guides and examples
- **Performance Optimizations**: 7x faster embedding generation, 10x faster vector search
- **Production Ready**: >90% test coverage, strict type checking, comprehensive error handling

## 📦 Installation

```bash
pip install dev-agent
```

Or with uv:

```bash
uv pip install dev-agent
```

## 🚀 Quick Start

```bash
# Configure Azure OpenAI
dev-agent setup

# Initialize a project
dev-agent init

# Run the workflow
dev-agent run
```

## 📚 Documentation

Full documentation is available at: [Your GitHub Pages URL]

## 🔧 Requirements

- Python 3.10 or higher
- Azure OpenAI account with API access
- GPT-4 and text-embedding-ada-002 deployments

## 📝 Full Changelog

[Copy the v1.0.0 section from CHANGELOG.md here]

## 🙏 Acknowledgments

Thank you to all contributors and users who provided feedback during development!
```

### 6. Build and Upload to PyPI

**Prerequisites:**
- PyPI account with API token
- `twine` installed: `uv pip install twine`

**Build the package:**

```bash
# Clean previous builds
rm -rf dist/ build/ *.egg-info

# Build wheel and source distribution
uv build

# Verify the build
ls -lh dist/
```

**Test on TestPyPI first (recommended):**

```bash
# Upload to TestPyPI
uv run twine upload --repository testpypi dist/*

# Test installation from TestPyPI
pip install --index-url https://test.pypi.org/simple/ dev-agent
```

**Upload to PyPI:**

```bash
# Upload to PyPI
uv run twine upload dist/*

# Verify installation
pip install dev-agent
```

### 7. Announce the Release

Share the release with the community:

#### GitHub
- Post in Discussions (if enabled)
- Update README badges if needed

#### Social Media
- Twitter/X: Share release highlights
- LinkedIn: Professional announcement
- Reddit: r/Python, r/MachineLearning (if relevant)

#### Developer Communities
- Hacker News: Submit the release
- Dev.to: Write a release blog post
- Medium: Detailed release article

**Announcement Template:**

```markdown
🎉 dev-agent v1.0.0 is now available!

dev-agent is an AI-powered development workflow assistant that uses Azure OpenAI to analyze codebases and generate specifications, designs, and implementation plans.

✨ Key Features:
- Azure OpenAI integration (GPT-4 + embeddings)
- Four-phase development workflow
- Context-aware code generation
- Rich CLI with progress indicators
- Comprehensive documentation

📦 Install: pip install dev-agent
📚 Docs: [Your GitHub Pages URL]
🔗 GitHub: [Your GitHub URL]

#Python #AI #DevTools #AzureOpenAI
```

## Post-Release Tasks

### 1. Monitor for Issues

- Watch GitHub issues for bug reports
- Monitor PyPI download statistics
- Check documentation feedback

### 2. Plan Next Release

- Create milestone for v1.1.0
- Gather feature requests
- Prioritize bug fixes

### 3. Update Development Branch

```bash
# Create develop branch if not exists
git checkout -b develop
git push -u origin develop

# Set up branch protection rules on GitHub
```

## Troubleshooting

### Documentation Build Fails

```bash
# Check for broken links
uv run mkdocs build --strict

# Fix any errors in docs/ directory
# Re-run build
```

### PyPI Upload Fails

```bash
# Check package metadata
uv run twine check dist/*

# Verify version doesn't already exist on PyPI
# Ensure API token is correct
```

### GitHub Release Issues

- Ensure you have write permissions to the repository
- Verify the tag doesn't already exist
- Check that all changes are pushed to main

## Rollback Procedure

If critical issues are discovered after release:

1. **Yank the PyPI release** (doesn't delete, just marks as unavailable):
   ```bash
   # Via PyPI web interface: Project → Releases → Yank
   ```

2. **Create hotfix release**:
   ```bash
   git checkout -b hotfix/v1.0.1
   # Fix the issue
   git commit -m "fix: critical issue description"
   # Follow release process for v1.0.1
   ```

3. **Update documentation** to reflect the hotfix

## Success Criteria

- ✅ Documentation builds without errors
- ✅ All tests pass
- ✅ Package installs successfully from PyPI
- ✅ GitHub release is published
- ✅ Documentation is live on GitHub Pages
- ✅ Announcement is posted

## Contact

For questions or issues with the release process, please open an issue on GitHub.

---

**Release Prepared By:** Kiro AI Assistant  
**Date:** October 4, 2025  
**Version:** 1.0.0
