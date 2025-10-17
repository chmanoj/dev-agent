"""Prompt templates for Azure OpenAI integration.

This module provides structured prompt templates for each workflow phase,
with context injection and intelligent truncation capabilities.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from typing import Any

logger = logging.getLogger(__name__)


@dataclass
class PromptTemplate:
    """Structured prompt template with context requirements.
    
    Attributes:
        system_prompt: System-level instructions for the LLM
        user_prompt_template: Template string with placeholders for context
        required_context: List of required context keys
        max_context_tokens: Maximum tokens allowed for context
        temperature: Temperature setting for generation
        max_tokens: Maximum tokens for completion
    """
    
    system_prompt: str
    user_prompt_template: str
    required_context: list[str] = field(default_factory=list)
    max_context_tokens: int = 6000
    temperature: float = 0.7
    max_tokens: int = 4000
    
    def render(self, context: dict[str, Any], token_counter: Any | None = None) -> tuple[str, str]:
        """Render the template with provided context.
        
        Args:
            context: Dictionary of context values to inject
            token_counter: Optional token counter for intelligent truncation
            
        Returns:
            Tuple of (system_prompt, rendered_user_prompt)
            
        Raises:
            ValueError: If required context keys are missing
        """
        # Validate required context
        missing_keys = [key for key in self.required_context if key not in context]
        if missing_keys:
            raise ValueError(f"Missing required context keys: {missing_keys}")
        
        # Apply intelligent truncation if token counter provided
        if token_counter:
            context = self._truncate_context(context, token_counter)
        
        # Render template with context
        try:
            rendered_prompt = self.user_prompt_template.format(**context)
        except KeyError as e:
            raise ValueError(f"Template references undefined context key: {e}") from e
        
        return self.system_prompt, rendered_prompt

    def _truncate_context(self, context: dict[str, Any], token_counter: Any) -> dict[str, Any]:
        """Intelligently truncate context to fit within token limits.
        
        Args:
            context: Original context dictionary
            token_counter: Token counter instance
            
        Returns:
            Truncated context dictionary
        """
        truncated = context.copy()
        
        # Calculate current token usage
        test_render = self.user_prompt_template.format(**context)
        current_tokens = token_counter.count_tokens(test_render)
        
        if current_tokens <= self.max_context_tokens:
            return truncated
        
        logger.warning(
            f"Context exceeds token limit ({current_tokens} > {self.max_context_tokens}), "
            "applying intelligent truncation"
        )
        
        # Truncate large context fields (prioritize keeping critical info)
        truncatable_keys = [
            "relevant_code_chunks",
            "code_patterns",
            "similar_code",
            "codebase_summary",
        ]
        
        for key in truncatable_keys:
            if key in truncated and isinstance(truncated[key], str):
                # Reduce by 30% each iteration
                while current_tokens > self.max_context_tokens:
                    original_length = len(truncated[key])
                    new_length = int(original_length * 0.7)
                    
                    if new_length < 100:  # Don't truncate too much
                        break
                    
                    truncated[key] = truncated[key][:new_length] + "\n... [truncated]"
                    
                    # Recalculate tokens
                    test_render = self.user_prompt_template.format(**truncated)
                    current_tokens = token_counter.count_tokens(test_render)
                    
                    if current_tokens <= self.max_context_tokens:
                        logger.info(f"Truncated {key} from {original_length} to {new_length} chars")
                        break
        
        return truncated



# Specification Generation Template
SPECIFICATION_TEMPLATE = PromptTemplate(
    system_prompt="""You are a technical specification writer analyzing a Python codebase.
Your task is to generate detailed, actionable specifications for the SPECIFIC FEATURE requested by the user.

CRITICAL: Focus ONLY on the feature described in the Feature Request section. Do NOT generate specifications for existing features or generic functionality like "data management" or "user authentication" unless explicitly requested.

COMPLETENESS REQUIREMENTS (MANDATORY):
- You MUST generate at least 3-5 detailed requirements with complete user stories and acceptance criteria
- Each requirement MUST have a user story in the format: "As a [role], I want [feature], so that [benefit]"
- Each requirement MUST have at least 2-3 acceptance criteria using EARS format (WHEN/THEN, IF/THEN, SHALL)
- Follow the format specified in dev_agent/REQUIREMENTS_FORMAT_GUIDE.md exactly
- Include error handling, edge cases, and performance requirements where applicable

VALIDATION CHECKLIST (Self-Check Before Responding):
□ Does the specification have at least 3-5 requirements?
□ Does each requirement have a complete user story?
□ Does each requirement have at least 2-3 acceptance criteria?
□ Are acceptance criteria written in EARS format (WHEN/THEN, IF/THEN, SHALL)?
□ Are all acceptance criteria specific and testable?
□ Have I included error handling scenarios?
□ Does the specification focus ONLY on the requested feature?

Key principles:
1. Generate specifications ONLY for the requested feature
2. Follow existing architectural patterns shown in the code examples
3. Use the same naming conventions and code style
4. Maintain consistency with current dependencies
5. Include clear acceptance criteria in EARS format
6. Specify error handling requirements
7. Consider edge cases and user experience
8. Ensure completeness with minimum 3-5 requirements""",
    
    user_prompt_template="""## FEATURE REQUEST (PRIMARY FOCUS)
{feature_description}

IMPORTANT: Generate a specification ONLY for the feature described above. Do NOT include specifications for existing features or unrelated functionality.

## Requirements Format Reference
Follow the format specified in dev_agent/REQUIREMENTS_FORMAT_GUIDE.md exactly:
- User stories: "As a [role], I want [feature], so that [benefit]"
- Acceptance criteria using EARS format: WHEN/THEN, IF/THEN, WHERE, SHALL
- Minimum 3-5 requirements with complete user stories and acceptance criteria
- Each requirement must have at least 2-3 testable acceptance criteria

## Codebase Context (for reference only)
{codebase_summary}

## Relevant Code Examples (for pattern matching)
{relevant_code_chunks}

## Existing Patterns (to follow)
{detected_patterns}

## Task
Generate a detailed specification SPECIFICALLY for the requested feature above. The specification must:
- Address ONLY the feature described in the Feature Request
- Follow the existing architectural patterns shown in code examples
- Use the same naming conventions and code style
- Maintain consistency with current dependencies
- Include functional and technical requirements
- Provide clear acceptance criteria in EARS format (WHEN/THEN, IF/THEN, SHALL)
- Specify error handling requirements
- MUST contain at least 3-5 detailed requirements

## Output Format
Provide a structured specification with:

### Introduction
[Brief description of the REQUESTED FEATURE and its purpose]

### Key Features
[List ONLY the features related to the user's request]
- Feature 1 related to request
- Feature 2 related to request
- Feature 3 related to request

### Requirements

For each requirement, use this EXACT format from dev_agent/REQUIREMENTS_FORMAT_GUIDE.md:

#### Requirement 1: [Brief Title]

**User Story:** As a [role], I want [specific feature from request], so that [benefit]

**Acceptance Criteria:**

1. WHEN [event] THEN the system SHALL [response]
2. IF [precondition] THEN the system SHALL [response]
3. WHERE [condition] THEN the system SHALL [response]

#### Requirement 2: [Brief Title]

**User Story:** As a [role], I want [another aspect of feature], so that [benefit]

**Acceptance Criteria:**

1. WHEN [event] THEN the system SHALL [response]
2. IF [precondition] THEN the system SHALL [response]

[Continue with additional requirements ONLY for the requested feature...]

MANDATORY COMPLETENESS CHECK:
Before submitting your response, verify:
□ I have included at least 3-5 requirements
□ Each requirement has a complete user story in the correct format
□ Each requirement has at least 2-3 acceptance criteria
□ All acceptance criteria use EARS format (WHEN/THEN, IF/THEN, SHALL)
□ All acceptance criteria are specific and testable
□ I have included error handling scenarios
□ The specification focuses ONLY on the requested feature

CRITICAL: You MUST include at least 3-5 detailed requirements with complete user stories and acceptance criteria. Each requirement must have:
- A clear user story in the format "As a [role], I want [feature], so that [benefit]"
- At least 2-3 acceptance criteria using WHEN/THEN, IF/THEN, WHERE, or SHALL format
- Specific, testable criteria that can be validated

REMEMBER: Focus exclusively on the feature described in the Feature Request section.""",
    
    required_context=[
        "codebase_summary",
        "relevant_code_chunks",
        "detected_patterns",
        "feature_description",
    ],
    max_context_tokens=6000,
    temperature=0.7,
    max_tokens=4000,
)



# Design Generation Template
DESIGN_TEMPLATE = PromptTemplate(
    system_prompt="""You are a software architect creating technical design documents.
Your task is to design solutions that are consistent with existing architecture.

Key principles:
1. Maintain architectural consistency with existing codebase
2. Follow established design patterns
3. Consider scalability and maintainability
4. Specify clear component interfaces
5. Document data flow and interactions
6. Address error handling and edge cases""",
    
    user_prompt_template="""## Specification
{specification}

## Existing Architecture
{existing_architecture}

## Code Patterns
{code_patterns}

## Similar Implementations
{similar_implementations}

## Task
Create a concise technical design document that:
- Aligns with the existing architecture
- Follows established design patterns
- Defines clear component interfaces
- Documents data models and flow
- Addresses error handling
- Includes testing strategy

## Output Format
Provide a structured design document with:
1. **Overview**: High-level design summary (2-3 sentences)
2. **Architecture**: Component structure and relationships (bullet points)
3. **Components and Interfaces**: Key component specifications (concise)
4. **Data Models**: Essential data structures only
5. **Error Handling**: Key error scenarios and recovery strategies
6. **Testing Strategy**: Brief testing approach

Keep each section concise and focused. Avoid lengthy explanations.""",
    
    required_context=[
        "specification",
        "existing_architecture",
        "code_patterns",
    ],
    max_context_tokens=6000,
    temperature=0.7,
    max_tokens=2000,
)



# Code Generation Template
CODE_GENERATION_TEMPLATE = PromptTemplate(
    system_prompt="""You are a Python developer generating code for an existing codebase.
Your code must match the existing style, patterns, and conventions EXACTLY.

Key principles:
1. Match the existing code style EXACTLY
2. Use the same type annotation patterns
3. Follow the same error handling approach
4. Use the same logging patterns
5. Include docstrings in the same format (Google style)
6. Add type hints to ALL functions
7. Use modern Python 3.10+ syntax
8. Follow the project's architectural patterns""",
    
    user_prompt_template="""## Specification
{specification}

## Design Document
{design}

## Existing Code Patterns
{code_patterns}

## Similar Implementations
{similar_code}

## Style Requirements
{style_requirements}

## Task
Generate Python code that:
- Implements the specification and design
- Matches the existing code style EXACTLY
- Uses the same patterns and conventions
- Includes comprehensive type hints
- Has Google-style docstrings
- Follows modern Python 3.10+ syntax
- Includes appropriate error handling
- Uses the same logging approach

## Output Format
Provide ONLY the Python code with:
- Module-level docstring
- Necessary imports (grouped: stdlib, third-party, local)
- Type annotations on all functions
- Google-style docstrings for all public functions/classes
- Appropriate error handling
- Logging where appropriate
- NO explanatory text outside the code""",
    
    required_context=[
        "specification",
        "design",
        "code_patterns",
        "similar_code",
    ],
    max_context_tokens=6000,
    temperature=0.7,
    max_tokens=4000,
)



# Task Generation Template
TASK_GENERATION_TEMPLATE = PromptTemplate(
    system_prompt="""You are a technical project manager breaking down work into incremental tasks.
Your task breakdowns should be actionable, testable, and build incrementally.

Key principles:
1. Break work into small, manageable coding tasks
2. Each task should be independently testable
3. Tasks should build incrementally on previous work
4. Prioritize core functionality first
5. Include testing as part of implementation tasks
6. Reference specific requirements
7. Focus ONLY on coding activities (no deployment, user testing, etc.)""",
    
    user_prompt_template="""## Specification
{specification}

## Design Document
{design}

## Complexity Analysis
{complexity_analysis}

## Task
Generate an implementation plan that breaks down the work into:
- Discrete, manageable coding tasks
- Incremental steps that build on each other
- Tasks with clear objectives and acceptance criteria
- Each task references specific requirements
- Testing integrated into implementation tasks

## Requirements
1. Each task must involve writing, modifying, or testing code
2. Tasks should be ordered to validate core functionality early
3. Include specific file paths and components to create/modify
4. Reference granular requirements (not just user stories)
5. Mark optional testing tasks with "*" suffix
6. NO tasks for deployment, user testing, or non-coding activities
7. Use maximum two levels of hierarchy (parent task + subtasks)

## Output Format
You MUST follow this EXACT markdown format. Do NOT deviate from this structure:

```
# Implementation Plan

## Overview
Brief description of the implementation approach.

## Task Breakdown

- [ ] 1. First task title
  - Implementation details and what to create
  - File paths to create or modify
  - _Requirements: X.X, Y.Y_

- [ ] 2. Second task title  
  - Implementation details and what to create
  - File paths to create or modify
  - _Requirements: X.X, Y.Y_

- [ ] 3. Third task title
  - Implementation details and what to create
  - File paths to create or modify
  - _Requirements: X.X, Y.Y_

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

- [ ] 1.1 Subtask description
  - Implementation details
  - _Requirements: X.X_

- [ ]* 1.2 Optional testing subtask
  - Test details
  - _Requirements: X.X_

Use simple, clear task descriptions focused on coding activities.""",
    
    required_context=[
        "specification",
        "design",
    ],
    max_context_tokens=6000,
    temperature=0.7,
    max_tokens=4000,
)



# Specification Generation for New Projects Template
SPECIFICATION_NEW_PROJECT_TEMPLATE = PromptTemplate(
    system_prompt="""You are a technical specification writer creating specifications for new projects.
Your task is to generate detailed, actionable specifications for the SPECIFIC FEATURE requested by the user.

CRITICAL: Focus ONLY on the feature described in the Feature Request. Do NOT add generic features like "data management", "user authentication", or "file management" unless explicitly mentioned in the request.

COMPLETENESS REQUIREMENTS (MANDATORY):
- You MUST generate at least 3-5 detailed requirements with complete user stories and acceptance criteria
- Each requirement MUST have a user story in the format: "As a [role], I want [feature], so that [benefit]"
- Each requirement MUST have at least 2-3 acceptance criteria using EARS format (WHEN/THEN, IF/THEN, SHALL)
- Follow the format specified in dev_agent/REQUIREMENTS_FORMAT_GUIDE.md exactly
- Include error handling, edge cases, and performance requirements where applicable

VALIDATION CHECKLIST (Self-Check Before Responding):
□ Does the specification have at least 3-5 requirements?
□ Does each requirement have a complete user story?
□ Does each requirement have at least 2-3 acceptance criteria?
□ Are acceptance criteria written in EARS format (WHEN/THEN, IF/THEN, SHALL)?
□ Are all acceptance criteria specific and testable?
□ Have I included error handling scenarios?
□ Does the specification focus ONLY on the requested feature?

Key principles:
1. Generate specifications ONLY for the requested feature
2. Create clear, testable requirements
3. Use EARS format for acceptance criteria (WHEN/THEN, IF/THEN, SHALL)
4. Include user stories for each requirement
5. Consider edge cases and error scenarios
6. Specify clear acceptance criteria
7. Focus on functional and technical requirements
8. Ensure completeness with minimum 3-5 requirements""",
    
    user_prompt_template="""## FEATURE REQUEST (PRIMARY FOCUS)
{feature_description}

IMPORTANT: Generate a specification ONLY for the feature described above. Do NOT add generic features or functionality not mentioned in the request.

## Requirements Format Reference
Follow the format specified in dev_agent/REQUIREMENTS_FORMAT_GUIDE.md exactly:
- User stories: "As a [role], I want [feature], so that [benefit]"
- Acceptance criteria using EARS format: WHEN/THEN, IF/THEN, WHERE, SHALL
- Minimum 3-5 requirements with complete user stories and acceptance criteria
- Each requirement must have at least 2-3 testable acceptance criteria

## Project Type
{project_type}

## Task
Generate a detailed specification that implements ONLY the requested feature above.

The specification must:
1. Address ONLY what is described in the Feature Request
2. NOT include generic features like authentication, data management, or file handling unless explicitly requested
3. Focus on the specific functionality the user wants
4. Include clear, testable requirements
5. Use EARS format for acceptance criteria
6. MUST contain at least 3-5 detailed requirements

## Output Format
Provide a structured specification with:

### Introduction
[Brief overview of the REQUESTED FEATURE and its purpose - do not add unrelated features]

### Key Features
[List ONLY features directly related to the user's request]
- Feature 1 from request
- Feature 2 from request
- Feature 3 from request

### Requirements

For each requirement, use this EXACT format from dev_agent/REQUIREMENTS_FORMAT_GUIDE.md:

#### Requirement 1: [Brief Title]

**User Story:** As a [role], I want [specific feature from request], so that [benefit]

**Acceptance Criteria:**

1. WHEN [event related to request] THEN the system SHALL [response]
2. IF [precondition related to request] THEN the system SHALL [response]
3. WHERE [condition related to request] THEN the system SHALL [response]

#### Requirement 2: [Brief Title]

**User Story:** As a [role], I want [another aspect of feature], so that [benefit]

**Acceptance Criteria:**

1. WHEN [event] THEN the system SHALL [response]
2. IF [precondition] THEN the system SHALL [response]

[Continue with additional requirements ONLY for the requested feature...]

MANDATORY COMPLETENESS CHECK:
Before submitting your response, verify:
□ I have included at least 3-5 requirements
□ Each requirement has a complete user story in the correct format
□ Each requirement has at least 2-3 acceptance criteria
□ All acceptance criteria use EARS format (WHEN/THEN, IF/THEN, SHALL)
□ All acceptance criteria are specific and testable
□ I have included error handling scenarios
□ The specification focuses ONLY on the requested feature

CRITICAL: You MUST include at least 3-5 detailed requirements with complete user stories and acceptance criteria. Each requirement must have:
- A clear user story in the format "As a [role], I want [feature], so that [benefit]"
- At least 2-3 acceptance criteria using WHEN/THEN, IF/THEN, WHERE, or SHALL format
- Specific, testable criteria that can be validated

REMEMBER: Focus exclusively on what the user requested. Do not add generic features.""",
    
    required_context=[
        "feature_description",
        "project_type",
    ],
    max_context_tokens=4000,
    temperature=0.7,
    max_tokens=3000,
)


# Specification Refinement Template
SPECIFICATION_REFINEMENT_TEMPLATE = PromptTemplate(
    system_prompt="""You are a technical specification writer refining specifications based on user feedback.
Your task is to improve the specification by incorporating the user's requested changes.

Key principles:
1. Carefully analyze the user's feedback
2. Make specific changes requested by the user
3. Maintain the overall structure and format
4. Preserve good parts of the original specification
5. Ensure acceptance criteria remain in EARS format
6. Keep user stories clear and actionable
7. Address all feedback points comprehensively""",
    
    user_prompt_template="""## Current Specification
{current_specification}

## User Feedback
{user_feedback}

## Original Feature Description
{feature_description}

## Task
Refine the specification by incorporating the user's feedback while maintaining quality and structure.

Requirements:
1. Address ALL points in the user feedback
2. Maintain the specification format (Introduction, Key Features, Requirements)
3. Keep user stories in proper format: "As a [role], I want [feature], so that [benefit]"
4. Keep acceptance criteria in EARS format (WHEN/THEN, IF/THEN, SHALL)
5. Preserve good aspects of the original specification
6. Make the changes specific and actionable
7. Ensure the refined specification is complete and coherent

## Output Format
Provide the complete refined specification with the same structure:

### Introduction
[Updated introduction incorporating feedback]

### Key Features
- Updated feature 1
- Updated feature 2
- Updated feature 3

### Requirements

#### Requirement 1
**User Story:** As a [role], I want [feature], so that [benefit]

**Acceptance Criteria:**
1. WHEN [event] THEN [system] SHALL [response]
2. IF [precondition] THEN [system] SHALL [response]

[Continue with all requirements, incorporating feedback...]""",
    
    required_context=[
        "current_specification",
        "user_feedback",
        "feature_description",
    ],
    max_context_tokens=6000,
    temperature=0.7,
    max_tokens=4000,
)


# Template registry for easy access
TEMPLATES = {
    "specification": SPECIFICATION_TEMPLATE,
    "specification_new_project": SPECIFICATION_NEW_PROJECT_TEMPLATE,
    "specification_refinement": SPECIFICATION_REFINEMENT_TEMPLATE,
    "design": DESIGN_TEMPLATE,
    "code_generation": CODE_GENERATION_TEMPLATE,
    "task_generation": TASK_GENERATION_TEMPLATE,
}


def get_template(template_name: str) -> PromptTemplate:
    """Get a prompt template by name.
    
    Args:
        template_name: Name of the template to retrieve
        
    Returns:
        PromptTemplate instance
        
    Raises:
        ValueError: If template name is not found
    """
    if template_name not in TEMPLATES:
        raise ValueError(
            f"Unknown template: {template_name}. "
            f"Available templates: {list(TEMPLATES.keys())}"
        )
    
    return TEMPLATES[template_name]


def inject_context(
    template: PromptTemplate,
    context: dict[str, Any],
    token_counter: Any | None = None,
) -> tuple[str, str]:
    """Inject context into a prompt template.
    
    Args:
        template: PromptTemplate to use
        context: Context dictionary with values to inject
        token_counter: Optional token counter for truncation
        
    Returns:
        Tuple of (system_prompt, rendered_user_prompt)
        
    Raises:
        ValueError: If required context is missing
    """
    return template.render(context, token_counter)
