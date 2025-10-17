"""Enhanced task templates with language and framework pattern support.

This module provides language-agnostic task templates that can be customized
based on detected language and framework patterns.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from typing import Any

from ..llm.prompt_templates import PromptTemplate

logger = logging.getLogger(__name__)


@dataclass
class LanguageAwareTaskTemplate:
    """Task template that adapts to language and framework patterns.
    
    This template uses placeholders that get replaced with language-specific
    patterns during rendering.
    """
    
    base_template: PromptTemplate
    language_placeholders: dict[str, str] = field(default_factory=dict)
    framework_placeholders: dict[str, str] = field(default_factory=dict)
    
    def render_with_patterns(
        self,
        context: dict[str, Any],
        language_patterns: Any | None = None,
        framework_patterns: Any | None = None,
        token_counter: Any | None = None,
    ) -> tuple[str, str]:
        """Render template with language and framework patterns applied.
        
        Args:
            context: Base context dictionary
            language_patterns: Language-specific patterns to apply
            framework_patterns: Framework-specific patterns to apply
            token_counter: Optional token counter for truncation
            
        Returns:
            Tuple of (system_prompt, rendered_user_prompt)
        """
        # Create enhanced context with pattern information
        enhanced_context = context.copy()
        
        # Add language pattern context
        if language_patterns:
            enhanced_context.update({
                "class_naming_convention": language_patterns.class_naming,
                "method_naming_convention": language_patterns.method_naming,
                "file_naming_convention": language_patterns.file_naming,
                "file_extension": language_patterns.file_extension,
                "test_file_suffix": language_patterns.test_file_suffix,
                "service_suffix": language_patterns.service_suffix,
                "interface_prefix": language_patterns.interface_prefix,
                "source_directory": language_patterns.source_directory,
                "test_directory": language_patterns.test_directory,
                "import_style": language_patterns.import_style,
            })
        
        # Add framework pattern context
        if framework_patterns:
            enhanced_context.update({
                "framework_name": framework_patterns.framework.value,
                "component_suffix": framework_patterns.component_suffix or "",
                "common_dependencies": ", ".join(framework_patterns.common_dependencies[:5]),
                "entry_point_files": ", ".join(framework_patterns.entry_point_files),
                "config_files": ", ".join(framework_patterns.config_file_patterns),
                "test_patterns": ", ".join(framework_patterns.test_file_patterns),
            })
        
        # Apply language-specific placeholder replacements
        system_prompt = self.base_template.system_prompt
        user_template = self.base_template.user_prompt_template
        
        if language_patterns:
            for placeholder, replacement in self.language_placeholders.items():
                if hasattr(language_patterns, replacement):
                    value = getattr(language_patterns, replacement)
                    system_prompt = system_prompt.replace(placeholder, str(value))
                    user_template = user_template.replace(placeholder, str(value))
        
        if framework_patterns:
            for placeholder, replacement in self.framework_placeholders.items():
                if hasattr(framework_patterns, replacement):
                    value = getattr(framework_patterns, replacement)
                    system_prompt = system_prompt.replace(placeholder, str(value))
                    user_template = user_template.replace(placeholder, str(value))
        
        # Create temporary template with enhanced prompts
        temp_template = PromptTemplate(
            system_prompt=system_prompt,
            user_prompt_template=user_template,
            required_context=self.base_template.required_context,
            max_context_tokens=self.base_template.max_context_tokens,
            temperature=self.base_template.temperature,
            max_tokens=self.base_template.max_tokens,
        )
        
        return temp_template.render(enhanced_context, token_counter)


# Enhanced Task Generation Template with Language Patterns
ENHANCED_TASK_GENERATION_TEMPLATE = LanguageAwareTaskTemplate(
    base_template=PromptTemplate(
        system_prompt="""You are a technical project manager breaking down work into incremental tasks.
Your task breakdowns should be actionable, testable, and build incrementally.

LANGUAGE AND FRAMEWORK CONTEXT:
You are generating tasks for software development. Follow these conventions:
- Use appropriate naming conventions for the target language
- Create files in proper directory structure  
- Follow framework-specific patterns when applicable
- Generate clean, maintainable code structure

Key principles:
1. Break work into small, manageable coding tasks
2. Each task should be independently testable
3. Tasks should build incrementally on previous work
4. Prioritize core functionality first
5. Include testing as part of implementation tasks
6. Reference specific requirements
7. Focus ONLY on coding activities (no deployment, user testing, etc.)
8. Use proper naming conventions for the target language
9. Follow framework patterns and directory structure
10. Generate appropriate file paths and extensions""",
        
        user_prompt_template="""## Specification
{specification}

## Design Document
{design}

## Complexity Analysis
{complexity_analysis}

## Language and Framework Context
**Target Language:** {target_language}
Generate tasks appropriate for software development:
- Use proper naming conventions (PascalCase for classes, snake_case for methods in Python)
- Create files with appropriate extensions (.py for Python, .js for JavaScript, etc.)
- Follow language-specific directory structures (src/, tests/, etc.)
- Include proper imports and dependencies

## Task Generation Requirements
Generate tasks that:
1. Use CORRECT naming conventions for the target language
2. Create files in appropriate directories (src/, tests/, etc.)
3. Follow language and framework-specific patterns
4. Include proper file extensions and naming
5. Reference appropriate dependencies and imports

## Task
Generate an implementation plan that breaks down the work into:
- Discrete, manageable coding tasks using CORRECT naming conventions
- Incremental steps that build on each other
- Tasks with clear objectives and acceptance criteria
- Each task references specific requirements
- Testing integrated into implementation tasks
- File paths that follow the language/framework conventions

## Requirements
1. Each task must involve writing, modifying, or testing code
2. Tasks should be ordered to validate core functionality early
3. Include specific file paths using CORRECT naming conventions
4. Reference granular requirements (not just user stories)
5. Mark optional testing tasks with "*" suffix
6. NO tasks for deployment, user testing, or non-coding activities
7. Use maximum two levels of hierarchy (parent task + subtasks)
8. ALL class names must follow {class_naming_convention}
9. ALL method names must follow {method_naming_convention}
10. ALL file names must follow {file_naming_convention}

## Output Format
You MUST follow this EXACT markdown format with correct naming conventions:

```
# Implementation Plan

## Overview
Brief description of the implementation approach.

## Task Breakdown

- [ ] 1. Create UserService class
  - Implement UserService in src/user_service.py
  - Use proper naming conventions (PascalCase for classes, snake_case for methods)
  - Include error handling and validation
  - _Requirements: X.X, Y.Y_

- [ ] 2. Implement get_user_data method
  - Add get_user_data() method with proper naming
  - Include proper error handling and validation
  - _Requirements: X.X_

- [ ] 3. Create unit tests for UserService
  - Create test file in tests/test_user_service.py
  - Test all public methods
  - _Requirements: X.X_

## Task Metadata
**Total Tasks:** X
**Estimated Effort:** Y hours
```

CRITICAL FORMATTING RULES:
1. Each task MUST start with "- [ ] " followed by a number and period
2. Each task MUST be on its own line
3. Sub-bullets MUST start with "  - " (two spaces + dash + space)
4. Do NOT merge multiple tasks on one line
5. Do NOT use extra asterisks or formatting in task titles
6. Keep task titles concise and clear
7. Always include the header sections exactly as shown
8. Use appropriate naming conventions for the target language
9. Generate proper file paths with correct extensions""",
        
        required_context=[
            "specification",
            "design",
            "target_language",
        ],
        max_context_tokens=8000,
        temperature=0.7,
        max_tokens=4000,
    ),
    
    language_placeholders={
        "{{CLASS_NAMING}}": "class_naming",
        "{{METHOD_NAMING}}": "method_naming", 
        "{{FILE_NAMING}}": "file_naming",
        "{{FILE_EXT}}": "file_extension",
        "{{TEST_SUFFIX}}": "test_file_suffix",
        "{{SERVICE_SUFFIX}}": "service_suffix",
        "{{SRC_DIR}}": "source_directory",
        "{{TEST_DIR}}": "test_directory",
    },
    
    framework_placeholders={
        "{{FRAMEWORK}}": "framework",
        "{{COMPONENT_SUFFIX}}": "component_suffix",
    }
)


# Python-specific Task Template
PYTHON_TASK_TEMPLATE = LanguageAwareTaskTemplate(
    base_template=PromptTemplate(
        system_prompt="""You are generating implementation tasks for a Python project.

PYTHON CONVENTIONS (MANDATORY):
- Classes: PascalCase (e.g., UserService, DataProcessor)
- Methods: snake_case (e.g., get_user_data, process_items)
- Files: snake_case with .py extension (e.g., user_service.py, data_processor.py)
- Constants: UPPER_CASE (e.g., MAX_RETRIES, DEFAULT_TIMEOUT)
- Modules: snake_case (e.g., user_management, data_processing)
- Tests: test_ prefix with _test.py suffix (e.g., test_user_service.py)

FRAMEWORK PATTERNS:
{framework_specific_patterns}

Key principles:
1. Follow PEP 8 naming conventions strictly
2. Use type hints for all function parameters and returns
3. Include docstrings for all public methods
4. Use pytest for testing
5. Follow the project's existing directory structure
6. Import statements should be organized (stdlib, third-party, local)""",
        
        user_prompt_template="""## Project Context
Language: Python
Framework: {framework_name}
{framework_specific_context}

## Specification
{specification}

## Design Document
{design}

## Task Generation
Generate Python implementation tasks that:

1. **Follow Python naming conventions:**
   - Classes: PascalCase (UserService, not user_service)
   - Methods: snake_case (get_user_data, not getUserData)
   - Files: snake_case.py (user_service.py, not UserService.py)
   - Tests: test_*.py in tests/ directory

2. **Include proper Python patterns:**
   - Type hints: `def get_user(user_id: int) -> User:`
   - Docstrings: Google-style docstrings
   - Error handling: Custom exception classes
   - Imports: Organized and explicit

3. **Framework-specific requirements:**
{framework_requirements}

## Output Format
- [ ] 1. Create UserService class
  - Implement UserService in src/user_service.py
  - Use PascalCase for class name, snake_case for methods
  - Include type hints and docstrings
  - _Requirements: 1.1, 1.2_

- [ ] 1.1 Implement get_user_data method
  - Add get_user_data(user_id: int) -> dict method
  - Include input validation and error handling
  - _Requirements: 1.1_

- [ ]* 1.2 Create unit tests
  - Create tests/test_user_service.py
  - Test all public methods with pytest
  - _Requirements: 1.1_""",
        
        required_context=[
            "specification",
            "design",
            "framework_name",
        ],
        max_context_tokens=6000,
        temperature=0.7,
        max_tokens=4000,
    )
)


# TypeScript-specific Task Template
TYPESCRIPT_TASK_TEMPLATE = LanguageAwareTaskTemplate(
    base_template=PromptTemplate(
        system_prompt="""You are generating implementation tasks for a TypeScript project.

TYPESCRIPT CONVENTIONS (MANDATORY):
- Classes: PascalCase (e.g., UserService, DataProcessor)
- Methods: camelCase (e.g., getUserData, processItems)
- Files: kebab-case with .ts extension (e.g., user-service.ts, data-processor.ts)
- Interfaces: PascalCase with I prefix (e.g., IUserService, IDataProcessor)
- Types: PascalCase (e.g., UserData, ProcessingResult)
- Constants: UPPER_CASE (e.g., MAX_RETRIES, DEFAULT_TIMEOUT)
- Tests: .spec.ts or .test.ts suffix

FRAMEWORK PATTERNS:
{framework_specific_patterns}

Key principles:
1. Use strict TypeScript configuration
2. Define interfaces for all data structures
3. Use proper type annotations
4. Follow ESLint and Prettier configurations
5. Use Jest for testing
6. Organize imports (external, internal, relative)""",
        
        user_prompt_template="""## Project Context
Language: TypeScript
Framework: {framework_name}
{framework_specific_context}

## Specification
{specification}

## Design Document
{design}

## Task Generation
Generate TypeScript implementation tasks that:

1. **Follow TypeScript naming conventions:**
   - Classes: PascalCase (UserService, not user_service)
   - Methods: camelCase (getUserData, not get_user_data)
   - Files: kebab-case.ts (user-service.ts, not UserService.ts)
   - Interfaces: PascalCase with I prefix (IUserService)

2. **Include proper TypeScript patterns:**
   - Type definitions: `interface UserData { id: number; name: string; }`
   - Method signatures: `getUserData(userId: number): Promise<UserData>`
   - Proper imports: `import { UserData } from './types';`
   - Error handling: Custom error classes

3. **Framework-specific requirements:**
{framework_requirements}

## Output Format
- [ ] 1. Create UserService class
  - Implement UserService in src/user-service.ts
  - Use PascalCase for class name, camelCase for methods
  - Define IUserService interface
  - _Requirements: 1.1, 1.2_

- [ ] 1.1 Implement getUserData method
  - Add getUserData(userId: number): Promise<UserData> method
  - Include proper type annotations and error handling
  - _Requirements: 1.1_

- [ ]* 1.2 Create unit tests
  - Create src/user-service.spec.ts
  - Test all public methods with Jest
  - _Requirements: 1.1_""",
        
        required_context=[
            "specification",
            "design",
            "framework_name",
        ],
        max_context_tokens=6000,
        temperature=0.7,
        max_tokens=4000,
    )
)


# Framework-specific template variations
FRAMEWORK_TASK_TEMPLATES = {
    "fastapi": LanguageAwareTaskTemplate(
        base_template=PromptTemplate(
            system_prompt="""You are generating tasks for a FastAPI Python project.

FASTAPI CONVENTIONS:
- API routes: Use FastAPI router patterns
- Models: Pydantic models for request/response
- Dependencies: Use FastAPI dependency injection
- File structure: routers/, models/, services/, dependencies/
- Testing: Use TestClient for API testing

Follow Python naming conventions with FastAPI-specific patterns.""",
            
            user_prompt_template="""## FastAPI Project Context
{specification}

{design}

Generate FastAPI-specific tasks:

1. **API Routes:**
   - Create router files in routers/ directory
   - Use snake_case for file names (user_router.py)
   - Use kebab-case for endpoint paths (/api/v1/user-data)

2. **Pydantic Models:**
   - Create models in models/ directory
   - Use PascalCase for model names (UserCreateModel)
   - Include proper validation

3. **Services:**
   - Business logic in services/ directory
   - Use dependency injection patterns

Example tasks:
- [ ] 1. Create user API router
  - Implement routers/user_router.py
  - Define CRUD endpoints with proper HTTP methods
  - Use Pydantic models for request/response
  - _Requirements: 1.1_""",
            
            required_context=["specification", "design"],
            max_context_tokens=6000,
            temperature=0.7,
            max_tokens=4000,
        )
    ),
    
    "react": LanguageAwareTaskTemplate(
        base_template=PromptTemplate(
            system_prompt="""You are generating tasks for a React TypeScript project.

REACT CONVENTIONS:
- Components: PascalCase with .tsx extension (UserProfile.tsx)
- Hooks: camelCase starting with 'use' (useUserData)
- Files: PascalCase for components, kebab-case for utilities
- Props: Define interfaces for all component props
- State: Use proper TypeScript types for state

Follow React best practices and TypeScript conventions.""",
            
            user_prompt_template="""## React Project Context
{specification}

{design}

Generate React-specific tasks:

1. **Components:**
   - Create components in src/components/
   - Use PascalCase.tsx naming (UserProfile.tsx)
   - Define prop interfaces

2. **Hooks:**
   - Custom hooks in src/hooks/
   - Use camelCase with 'use' prefix (useUserData.ts)

3. **Services:**
   - API services in src/services/
   - Use kebab-case naming (user-service.ts)

Example tasks:
- [ ] 1. Create UserProfile component
  - Implement src/components/UserProfile.tsx
  - Define UserProfileProps interface
  - Use proper TypeScript types
  - _Requirements: 1.1_""",
            
            required_context=["specification", "design"],
            max_context_tokens=6000,
            temperature=0.7,
            max_tokens=4000,
        )
    ),
    
    "streamlit": LanguageAwareTaskTemplate(
        base_template=PromptTemplate(
            system_prompt="""You are generating tasks for a Streamlit Python project.

STREAMLIT CONVENTIONS:
- Main app: app.py or main.py in root directory
- Pages: Use pages/ directory for multi-page apps
- Components: Custom components in components/ directory
- Utils: Utility functions in utils/ directory
- Data: Data processing in data/ directory

Follow Python naming conventions with Streamlit-specific patterns.""",
            
            user_prompt_template="""## Streamlit Project Context
{specification}

{design}

Generate Streamlit-specific tasks:

1. **App Structure:**
   - Main app file (app.py or main.py)
   - Page files in pages/ directory
   - Use snake_case for all Python files

2. **Components:**
   - Reusable components in components/
   - Data processing in data/ or utils/

3. **Streamlit Features:**
   - Use st.cache_data for data caching
   - Implement proper session state management
   - Create interactive widgets

Example tasks:
- [ ] 1. Create main Streamlit app
  - Implement app.py with main interface
  - Set up page navigation and layout
  - Use proper Streamlit patterns
  - _Requirements: 1.1_""",
            
            required_context=["specification", "design"],
            max_context_tokens=6000,
            temperature=0.7,
            max_tokens=4000,
        )
    )
}


def get_template_for_language_and_framework(
    language: str,
    framework: str | None = None
) -> LanguageAwareTaskTemplate:
    """Get the appropriate task template for language and framework.
    
    Args:
        language: Programming language (python, typescript, etc.)
        framework: Optional framework (fastapi, react, etc.)
        
    Returns:
        Appropriate task template
    """
    # Check for framework-specific template first
    if framework and framework.lower() in FRAMEWORK_TASK_TEMPLATES:
        return FRAMEWORK_TASK_TEMPLATES[framework.lower()]
    
    # Fall back to language-specific templates
    if language.lower() == "python":
        return PYTHON_TASK_TEMPLATE
    elif language.lower() in ("typescript", "javascript"):
        return TYPESCRIPT_TASK_TEMPLATE
    
    # Default to enhanced template
    return ENHANCED_TASK_GENERATION_TEMPLATE