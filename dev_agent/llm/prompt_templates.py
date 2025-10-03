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
Your task is to generate detailed, actionable specifications based on codebase analysis.

Key principles:
1. Follow existing architectural patterns shown in the code examples
2. Use the same naming conventions and code style
3. Maintain consistency with current dependencies
4. Include clear acceptance criteria
5. Specify error handling requirements
6. Consider edge cases and user experience""",
    
    user_prompt_template="""## Codebase Context
{codebase_summary}

## Relevant Code Examples
{relevant_code_chunks}

## Existing Patterns
{detected_patterns}

## Feature Request
{feature_description}

## Task
Generate a detailed specification for the requested feature that:
- Follows the existing architectural patterns
- Uses the same naming conventions and code style
- Maintains consistency with current dependencies
- Includes functional and technical requirements
- Provides clear acceptance criteria
- Specifies error handling requirements

## Output Format
Provide a structured specification with:
1. **Overview**: Brief description of the feature
2. **Functional Requirements**: What the feature should do
3. **Technical Requirements**: How it should be implemented
4. **Acceptance Criteria**: Testable conditions for completion
5. **Dependencies**: Required libraries or components
6. **Error Handling**: Expected error scenarios and handling
7. **Testing Strategy**: How to verify the implementation""",
    
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
Create a comprehensive technical design document that:
- Aligns with the existing architecture
- Follows established design patterns
- Defines clear component interfaces
- Documents data models and flow
- Addresses error handling
- Includes testing strategy

## Output Format
Provide a structured design document with:
1. **Overview**: High-level design summary
2. **Architecture**: Component structure and relationships
3. **Components and Interfaces**: Detailed component specifications
4. **Data Models**: Data structures and schemas
5. **Data Flow**: How data moves through the system
6. **Error Handling**: Error scenarios and recovery strategies
7. **Testing Strategy**: Unit, integration, and end-to-end testing approach
8. **Security Considerations**: Authentication, authorization, data protection""",
    
    required_context=[
        "specification",
        "existing_architecture",
        "code_patterns",
    ],
    max_context_tokens=6000,
    temperature=0.7,
    max_tokens=4000,
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
Provide a numbered task list with:
- [ ] 1. Parent task description
  - Specific details about what to implement
  - File paths to create or modify
  - _Requirements: X.X, Y.Y_

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



# Template registry for easy access
TEMPLATES = {
    "specification": SPECIFICATION_TEMPLATE,
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
