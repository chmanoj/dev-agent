# Design Document

## Overview

This document designs fixes for critical bugs in the dev-agent system related to task generation, CLI command recognition, and language-specific patterns. The solution involves enhancing the language detection system, improving contextual help, and fixing command routing in the implementation phase.

## Architecture

### Current Issues Analysis

1. **Language Pattern Mismatch**: Task generator uses hardcoded TypeScript patterns regardless of project language
2. **Static Help System**: CLI help shows generic commands instead of phase-specific options
3. **Command Recognition Failure**: Implementation phase commands not properly registered or routed
4. **Framework Detection Gap**: System doesn't detect and apply framework-specific patterns

### Enhanced Architecture

```
Project Analysis → Language Detection → Framework Detection → Pattern Application
                                    ↓
CLI Request → Phase Detection → Contextual Command Router → Phase-Specific Handler
                                    ↓
Task Generation → Language Patterns → Framework Patterns → Validated Tasks
```

## Components and Interfaces

### 1. Language Detection Service

**Purpose**: Detect project language and apply appropriate patterns

**Location**: `dev_agent/analysis/language_detector.py`

**Methods**:
- `detect_primary_language(project_path: Path) -> Language`
- `get_language_patterns(language: Language) -> LanguagePatterns`
- `validate_naming_convention(name: str, language: Language) -> bool`

**Language Patterns**:
```python
@dataclass
class LanguagePatterns:
    file_extension: str
    class_naming: str  # "PascalCase" | "snake_case"
    method_naming: str  # "camelCase" | "snake_case"
    file_naming: str   # "kebab-case" | "snake_case" | "PascalCase"
    service_suffix: str  # "Service" | "_service" | ""
```

### 2. Framework Detection Service

**Purpose**: Detect framework and apply framework-specific patterns

**Location**: `dev_agent/analysis/framework_detector.py`

**Methods**:
- `detect_framework(project_path: Path, language: Language) -> Framework`
- `get_framework_patterns(framework: Framework) -> FrameworkPatterns`
- `get_directory_structure(framework: Framework) -> DirectoryStructure`

**Supported Frameworks**:
- Python: Streamlit, FastAPI, Django, Flask, Plain Python
- TypeScript: React, Next.js, Express, Plain TypeScript
- JavaScript: React, Vue, Express, Plain JavaScript

### 3. Contextual Help System

**Purpose**: Provide phase-specific help and command suggestions

**Location**: `dev_agent/cli/contextual_help.py`

**Methods**:
- `get_phase_commands(phase: PhaseType) -> list[Command]`
- `get_command_help(command: str, phase: PhaseType) -> str`
- `suggest_next_actions(phase: PhaseType, project_state: ProjectState) -> list[str]`

**Phase-Specific Commands**:
```python
PHASE_COMMANDS = {
    PhaseType.INDEXING: ["index", "status", "analyze"],
    PhaseType.SPECIFICATION: ["spec", "requirements", "validate"],
    PhaseType.DESIGN: ["design", "architecture", "review"],
    PhaseType.IMPLEMENTATION: ["tasks", "generate", "test", "review", "complete"]
}
```

### 4. Enhanced Task Generator

**Purpose**: Generate language and framework-appropriate tasks

**Location**: `dev_agent/generation/enhanced_task_generator.py`

**Methods**:
- `generate_tasks_with_patterns(spec: str, language: Language, framework: Framework) -> list[Task]`
- `apply_naming_conventions(task: Task, patterns: LanguagePatterns) -> Task`
- `validate_task_structure(task: Task, project_context: ProjectContext) -> bool`

### 5. Command Router Enhancement

**Purpose**: Route commands based on current phase and context

**Location**: `dev_agent/cli/enhanced_command_router.py`

**Methods**:
- `route_command(command: str, phase: PhaseType, args: list[str]) -> CommandResult`
- `register_phase_commands(phase: PhaseType, commands: dict[str, Callable])`
- `handle_unrecognized_command(command: str, phase: PhaseType) -> str`

## Data Models

### Language Enum
```python
class Language(Enum):
    PYTHON = "python"
    TYPESCRIPT = "typescript"
    JAVASCRIPT = "javascript"
    GO = "go"
    RUST = "rust"
```

### Framework Enum
```python
class Framework(Enum):
    # Python frameworks
    STREAMLIT = "streamlit"
    FASTAPI = "fastapi"
    DJANGO = "django"
    FLASK = "flask"
    PYTHON_PLAIN = "python_plain"
    
    # TypeScript/JavaScript frameworks
    REACT = "react"
    NEXTJS = "nextjs"
    EXPRESS = "express"
    TYPESCRIPT_PLAIN = "typescript_plain"
    JAVASCRIPT_PLAIN = "javascript_plain"
```

### Enhanced Task Model
```python
@dataclass
class EnhancedTask:
    id: str
    title: str
    description: str
    file_path: str
    language: Language
    framework: Framework
    naming_pattern: str
    dependencies: list[str]
    acceptance_criteria: list[str]
    estimated_effort: str
```

## Error Handling

### Language Detection Errors
- **Scenario**: Cannot determine project language
- **Strategy**: Default to most common language in project, prompt user for confirmation
- **Fallback**: Use generic patterns with user notification

### Framework Detection Errors
- **Scenario**: Multiple frameworks detected or none detected
- **Strategy**: Prompt user to select framework, save preference for project
- **Fallback**: Use plain language patterns

### Command Recognition Errors
- **Scenario**: Command not found in current phase
- **Strategy**: Suggest similar commands, show phase-appropriate help
- **Recovery**: Allow force execution with confirmation

### Pattern Application Errors
- **Scenario**: Generated patterns conflict with existing code
- **Strategy**: Analyze existing patterns, adapt generated tasks
- **Validation**: Check against existing codebase before task creation

## Testing Strategy

### Unit Tests
- Test language detection with various project structures
- Test framework detection accuracy
- Test naming convention transformations
- Test command routing logic
- Test pattern application

### Integration Tests
- Test end-to-end task generation with different languages/frameworks
- Test CLI command flow in each phase
- Test contextual help system
- Test error handling and recovery

### Validation Tests
- Test with real Python/Streamlit projects
- Test with TypeScript/React projects
- Test phase transitions and command availability
- Test pattern consistency across generated tasks

## Implementation Plan

### Phase 1: Language and Framework Detection
1. Implement `LanguageDetector` with file analysis
2. Implement `FrameworkDetector` with dependency analysis
3. Create pattern definition system
4. Add validation and testing

### Phase 2: Enhanced Task Generation
1. Modify task generator to use detected patterns
2. Implement pattern application logic
3. Add framework-specific task templates
4. Update task validation

### Phase 3: Contextual CLI System
1. Implement phase-aware command routing
2. Create contextual help system
3. Register implementation phase commands
4. Add command suggestion system

### Phase 4: Integration and Testing
1. Integrate all components
2. Update CLI entry points
3. Add comprehensive testing
4. Update documentation

---

## Document Metadata

- **Version:** 1.0
- **Status:** Draft
- **Created:** 2025-10-15