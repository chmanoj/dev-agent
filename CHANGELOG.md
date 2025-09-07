# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added
- Comprehensive Git workflow standards and automation
- MkDocs documentation system with Material theme
- Modern Python tooling with uv, Ruff, and mypy strict mode
- Pre-commit hooks for code quality enforcement
- Conventional commit message validation
- Pull request templates and automation
- Release automation workflows

### Changed
- Migrated to modern Python 3.10+ requirements
- Updated all dependencies to latest versions
- Enhanced code quality standards with comprehensive Ruff rules
- Improved project structure and organization

### Fixed
- Cleaned up legacy files and build artifacts
- Resolved configuration inconsistencies

## [0.1.0] - 2024-01-XX

### Added
- Initial project structure
- Four-phase development workflow (Indexing, Specification, Design, Implementation)
- CLI interface with Typer and Rich
- Tree-sitter based code analysis
- Vector embeddings for code similarity
- Session management and state persistence
- Pydantic v2 data models
- FastAPI integration for future API features

### Features
- Interactive CLI with chat-based interface
- High-performance codebase indexing
- Context-aware code generation
- User approval workflows between phases
- Python-first development focus

---

## Release Types

- **Major**: Breaking changes, new architecture, API changes
- **Minor**: New features, enhancements, non-breaking changes  
- **Patch**: Bug fixes, documentation updates, minor improvements

## Commit Types

- `feat`: New features
- `fix`: Bug fixes
- `docs`: Documentation changes
- `style`: Code style changes
- `refactor`: Code refactoring
- `perf`: Performance improvements
- `test`: Test changes
- `chore`: Maintenance tasks
- `ci`: CI/CD changes
- `build`: Build system changes