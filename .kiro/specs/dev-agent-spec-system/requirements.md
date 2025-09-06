# Revised MVP Requirements for dev-agent (With Existing Codebase Support)

## Introduction

This document outlines the requirements for a more advanced MVP of dev-agent. The primary goal is to build the core three-phase workflow on top of a high-performance indexing engine capable of handling large, existing repositories locally.

The system implements a Specify -> Design -> Implement loop with an initial indexing phase for existing projects. The agent will build a local, on-disk index to analyze repositories with millions of lines of code quickly, focusing on Python-first implementation while deferring advanced security, automated Git integration, and cross-platform installers.

## Key MVP Features

✅ **End-to-End Workflow**: The core Specify -> Design -> Implement loop remains central  
⚡️ **High-Performance Indexing**: The agent will build a local, on-disk index to analyze repositories with millions of lines of code quickly  
🔍 **Existing Project Analysis**: The agent's first step on an existing repo is to analyze it and generate the initial Specification and Design documents  
🐍 **Python-First**: The agent will implement new code in Python  
🚫 **Non-Core Features Deferred**: Advanced security, automated Git integration, and cross-platform installers are deferred to keep scope focused

## High-Level MVP Workflow

The workflow includes an initial indexing phase for existing projects:

- **Phase 0: Indexing** (For Existing Repos): The agent performs a one-time, intensive analysis of the codebase to build its local index
- **Phase 1: Specification**: The agent generates a SPECIFICATION.md file. For existing repos, this is based on its analysis. For new projects, it's guided by the user
- **Phase 2: Design**: The agent uses the spec to generate a DESIGN.md file, reflecting the current or proposed architecture  
- **Phase 3: Implementation**: The agent creates a TASKS.md list and writes Python code as directed by the user, using the full codebase index for context

## Functional Requirements (Revised MVP)

### FR-1: Core System & Interaction

**User Story:** As a software developer, I want an interactive CLI system that manages project state and requires my approval at key decision points.

#### Acceptance Criteria

1. WHEN I use the system THEN it SHALL provide a basic, interactive chat-based command-line interface
2. WHEN the system generates documents (Specification, Design, Task List) THEN it SHALL require explicit user approval (y/n) before proceeding
3. WHEN I run the init command THEN the system SHALL prepare the project folder and begin indexing if code exists
4. WHEN I work across sessions THEN the system SHALL save its state (current phase, etc.) in a local file to allow resuming
5. WHEN I need to resume work THEN the system SHALL restore the exact state from the last session

### FR-2: Phase 0: High-Performance Codebase Indexing

**User Story:** As a software developer working with large existing codebases, I want the system to quickly build a comprehensive index so it can understand my project without consuming excessive resources.

#### Acceptance Criteria

1. WHEN working with existing code THEN the system SHALL create a persistent, on-disk index within the project's .dev_agent directory
2. WHEN indexing code THEN the system SHALL use Tree-sitter to parse the entire codebase into an Abstract Syntax Tree (AST), creating a searchable map of all functions, classes, and symbols
3. WHEN performing semantic analysis THEN the system SHALL implement a Retrieval-Augmented Generation pipeline by chunking code, generating vector embeddings, and storing them in a local vector database (e.g., Qdrant, LanceDB)
4. WHEN handling large repositories THEN the system SHALL be architected to handle at least one million lines of code on a standard developer machine without consuming excessive RAM
5. WHEN optimizing performance THEN the system SHALL leverage memory-mapped files and on-disk data structures
6. WHEN indexing is complete THEN the expensive analysis SHALL only be done once, with the index persisting across sessions

### FR-3: Phase 1: Specification Generation

**User Story:** As a software developer, I want the system to generate comprehensive specifications either from existing code analysis or through guided prompts for new projects.

#### Acceptance Criteria

1. WHEN working with existing repos THEN the system SHALL use its index to perform full-codebase analysis and generate a SPECIFICATION.md file documenting the application's likely requirements and features
2. WHEN working with new (empty) projects THEN the system SHALL prompt the user with questions to create the specification
3. WHEN a specification is generated THEN the system SHALL present it to the user for approval
4. WHEN I request changes THEN the system SHALL allow for at least one round of feedback and regeneration
5. WHEN specification is approved THEN the system SHALL save it as a structured document and proceed to design phase

### FR-4: Phase 2: Design Generation

**User Story:** As a software developer, I want the system to create detailed design documents that reflect either my existing architecture or a proposed new architecture.

#### Acceptance Criteria

1. WHEN working with existing repos THEN the system SHALL generate a DESIGN.md file documenting the current architecture, data models, and key components based on its index
2. WHEN working with new projects THEN the system SHALL generate a technical design based on the user-created specification
3. WHEN design is complete THEN the system SHALL seek user approval for the design
4. WHEN I provide feedback THEN the system SHALL allow for design revision and re-approval
5. WHEN design is approved THEN the system SHALL proceed to implementation phase

### FR-5: Phase 3: Implementation

**User Story:** As a software developer, I want the system to generate task lists and implement Python code using full codebase context to ensure consistency with existing patterns.

#### Acceptance Criteria

1. WHEN design is approved THEN the system SHALL generate a TASKS.md checklist based on the design document
2. WHEN implementing a task THEN the system SHALL use its entire codebase index to inform the new Python code, ensuring consistency with existing patterns, classes, and functions
3. WHEN generating code THEN the system SHALL write the generated Python code and tests directly to files in the project directory
4. WHEN code is generated THEN it SHALL be consistent with existing codebase patterns and architecture
5. WHEN implementation is complete THEN the system SHALL present results for user review

## Deferred Features (Post-MVP Roadmap)

The following features are intentionally deferred to keep the MVP scope focused and achievable:

### Security
- Sandboxed command execution
- Secure code analysis and validation
- Protection against malicious code injection

### Advanced Git Integration  
- Automated commits and branching
- The /undo command for reverting changes
- Advanced merge conflict resolution

### Full Iteration Support
- The ability to go back and modify previous phases with changes propagating forward
- Complex dependency tracking between phases
- Advanced rollback capabilities

### Multi-Language Support
- Expanding beyond Python to support multiple programming languages
- Language-specific best practices and patterns
- Framework-specific code generation

### Distribution & Installers
- Creating cross-platform binaries
- Package management integration
- Automated deployment and distribution

### Advanced Features
- Visual diagram generation for complex architectures
- Integration with external development tools and IDEs
- Advanced error handling and recovery mechanisms
- Performance optimization and profiling capabilities