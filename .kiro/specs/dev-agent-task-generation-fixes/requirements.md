# Requirements Document

## Introduction

This specification addresses critical bugs in the dev-agent system related to task generation, CLI command recognition, and language-specific code patterns. The system currently generates tasks with incorrect language patterns and fails to recognize implementation phase commands.

## Requirements

### Requirement 1

**User Story:** As a developer, I want task generation to use language-appropriate patterns and file naming conventions, so that generated tasks match my project's technology stack.

#### Acceptance Criteria

1. WHEN the system generates tasks for a Python project THEN it SHALL use Python naming conventions (snake_case files, .py extensions)
2. WHEN the system generates tasks for a Python project THEN it SHALL NOT use TypeScript/JavaScript patterns (PascalCase services, .ts extensions)
3. WHEN the system analyzes project structure THEN it SHALL detect the primary language from pyproject.toml, package.json, or file extensions
4. WHEN generating service classes THEN it SHALL use language-appropriate class and method naming (Python: snake_case methods, TypeScript: camelCase methods)

### Requirement 2

**User Story:** As a developer, I want contextual CLI help that shows commands relevant to my current project phase, so that I can see available actions for my current workflow state.

#### Acceptance Criteria

1. WHEN I run help commands in the indexing phase THEN the system SHALL show indexing-related commands
2. WHEN I run help commands in the specification phase THEN the system SHALL show specification-related commands  
3. WHEN I run help commands in the design phase THEN the system SHALL show design-related commands
4. WHEN I run help commands in the implementation phase THEN the system SHALL show implementation-related commands (tasks, generate, test, review)
5. WHEN no project is initialized THEN the system SHALL show general setup commands

### Requirement 3

**User Story:** As a developer, I want all implementation phase commands to be recognized and functional, so that I can execute tasks and manage my development workflow.

#### Acceptance Criteria

1. WHEN I run "tasks" command in implementation phase THEN the system SHALL display the current task list
2. WHEN I run "generate" command in implementation phase THEN the system SHALL start code generation for the current task
3. WHEN I run "test" command in implementation phase THEN the system SHALL run tests for the current implementation
4. WHEN I run "review" command in implementation phase THEN the system SHALL show code review options
5. WHEN commands are not recognized THEN the system SHALL provide helpful suggestions for valid commands

### Requirement 4

**User Story:** As a developer, I want the task generation to respect my project's existing patterns and dependencies, so that generated tasks integrate seamlessly with my codebase.

#### Acceptance Criteria

1. WHEN generating tasks for a Streamlit project THEN it SHALL use Streamlit-specific patterns and file structures
2. WHEN generating tasks for a FastAPI project THEN it SHALL use FastAPI-specific patterns and file structures
3. WHEN analyzing existing code THEN it SHALL detect framework patterns and apply them to new tasks
4. WHEN suggesting dependencies THEN it SHALL use the project's package manager (uv, pip, npm, yarn)
5. WHEN creating file paths THEN it SHALL follow the project's existing directory structure conventions

---

## Document Metadata

- **Version:** 1.0
- **Status:** Draft
- **Created:** 2025-10-15