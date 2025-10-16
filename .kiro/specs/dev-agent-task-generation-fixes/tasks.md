# Implementation Plan

- [x] 1. Implement Language Detection System
  - Create language detection service that analyzes project files and configuration
  - Implement pattern definitions for different programming languages
  - Add validation for naming conventions and file structures
  - _Requirements: 1.1, 1.3, 1.4_

- [x] 1.1 Create LanguageDetector class
  - Write `dev_agent/analysis/language_detector.py` with file extension analysis
  - Implement detection logic for pyproject.toml, package.json, and source files
  - Add language pattern definitions (naming conventions, file extensions)
  - _Requirements: 1.1, 1.3_

- [x] 1.2 Create LanguagePatterns data model
  - Define LanguagePatterns dataclass with naming conventions
  - Implement pattern validation methods
  - Add language-specific configuration loading
  - _Requirements: 1.1, 1.4_

- [ ]* 1.3 Write unit tests for language detection
  - Create test cases for different project structures
  - Test pattern validation logic
  - Mock file system interactions for testing
  - _Requirements: 1.1, 1.3_

- [x] 2. Implement Framework Detection System
  - Create framework detection service that identifies project frameworks
  - Implement framework-specific pattern application
  - Add directory structure analysis and recommendations
  - _Requirements: 4.1, 4.2, 4.3, 4.5_

- [x] 2.1 Create FrameworkDetector class
  - Write `dev_agent/analysis/framework_detector.py` with dependency analysis
  - Implement detection for Streamlit, FastAPI, React, Express frameworks
  - Add framework pattern definitions and directory structures
  - _Requirements: 4.1, 4.2, 4.3_

- [x] 2.2 Create Framework and FrameworkPatterns models
  - Define Framework enum with supported frameworks
  - Create FrameworkPatterns dataclass for framework-specific conventions
  - Implement framework validation and pattern application
  - _Requirements: 4.1, 4.2, 4.5_

- [ ]* 2.3 Write unit tests for framework detection
  - Test framework detection accuracy with sample projects
  - Test pattern application for different frameworks
  - Validate directory structure recommendations
  - _Requirements: 4.1, 4.2, 4.3_

- [x] 3. Enhance Task Generation with Language Patterns
  - Modify existing task generator to use detected language and framework patterns
  - Implement pattern-aware task creation and validation
  - Update task templates to be language-agnostic
  - _Requirements: 1.1, 1.2, 1.4, 4.4_

- [x] 3.1 Update TaskGenerator class
  - Modify `dev_agent/generation/task_generator.py` to accept language/framework context
  - Implement pattern application in task generation
  - Add naming convention transformation logic
  - _Requirements: 1.1, 1.2, 1.4_

- [x] 3.2 Create enhanced task templates
  - Design language-agnostic task templates with pattern placeholders
  - Implement template rendering with language-specific patterns
  - Add framework-specific task variations
  - _Requirements: 1.4, 4.1, 4.2_

- [x] 3.3 Update Task data model
  - Enhance Task model with language and framework fields
  - Add pattern validation to task creation
  - Implement task naming convention enforcement
  - _Requirements: 1.1, 1.4_

- [ ]* 3.4 Write integration tests for enhanced task generation
  - Test task generation with different language/framework combinations
  - Validate generated task naming conventions
  - Test pattern consistency across multiple tasks
  - _Requirements: 1.1, 1.2, 1.4, 4.1_

- [-] 4. Implement Contextual CLI Help System
  - Create phase-aware help system that shows relevant commands
  - Implement command suggestions based on current project state
  - Add contextual error messages and guidance
  - _Requirements: 2.1, 2.2, 2.3, 2.4, 2.5_

- [x] 4.1 Create ContextualHelp class
  - Write `dev_agent/cli/contextual_help.py` with phase-specific command mapping
  - Implement help text generation based on current phase
  - Add command suggestion logic for unrecognized commands
  - _Requirements: 2.1, 2.2, 2.3, 2.4_

- [x] 4.2 Define phase-specific command mappings
  - Create command definitions for each workflow phase
  - Implement command availability validation
  - Add help text and usage examples for each command
  - _Requirements: 2.1, 2.2, 2.3, 2.4_

- [ ]* 4.3 Write unit tests for contextual help
  - Test help text generation for different phases
  - Test command suggestion accuracy
  - Validate phase-specific command filtering
  - _Requirements: 2.1, 2.2, 2.3, 2.4_

- [x] 5. Fix Implementation Phase Command Recognition
  - Update CLI command router to properly handle implementation phase commands
  - Register missing commands (tasks, generate, test, review)
  - Implement proper command delegation and error handling
  - _Requirements: 3.1, 3.2, 3.3, 3.4, 3.5_

- [x] 5.1 Update CLI command router
  - Modify `dev_agent/cli/main.py` to include implementation phase commands
  - Implement proper command routing based on project phase
  - Add command registration system for phase-specific handlers
  - _Requirements: 3.1, 3.2, 3.3, 3.4_

- [x] 5.2 Implement implementation phase command handlers
  - Create handlers for tasks, generate, test, and review commands
  - Implement command validation and execution logic
  - Add proper error handling and user feedback
  - _Requirements: 3.1, 3.2, 3.3, 3.4_

- [x] 5.3 Update command help and documentation
  - Add help text for implementation phase commands
  - Update CLI documentation with command usage examples
  - Implement command auto-completion support
  - _Requirements: 3.1, 3.2, 3.3, 3.4, 3.5_

- [ ]* 5.4 Write integration tests for command routing
  - Test command recognition in different phases
  - Test command execution and error handling
  - Validate help system integration
  - _Requirements: 3.1, 3.2, 3.3, 3.4, 3.5_

- [x] 6. Integration and System Testing
  - Integrate all components and test end-to-end functionality
  - Validate fixes with real project scenarios
  - Update existing tests and documentation
  - _Requirements: All requirements_

- [x] 6.1 Integrate language and framework detection into workflow
  - Update workflow manager to use language/framework detection
  - Integrate pattern application into task generation pipeline
  - Add detection results to project state management
  - _Requirements: 1.3, 4.3, 4.4_

- [x] 6.2 Update existing task generation to use new system
  - Modify existing task generation calls to include language context
  - Update task validation to use new pattern system
  - Ensure backward compatibility with existing projects
  - _Requirements: 1.1, 1.2, 1.4, 4.4_

- [ ]* 6.3 Create end-to-end integration tests
  - Test complete workflow with Python/Streamlit project
  - Test complete workflow with TypeScript/React project
  - Validate command recognition and help system
  - _Requirements: All requirements_

- [x] 6.4 Update documentation and examples
  - Update CLI documentation with new commands and help system
  - Add examples of language-specific task generation
  - Update troubleshooting guide with common issues
  - _Requirements: 2.5, 3.5_