"""AI-powered specification generator using Azure OpenAI."""

from __future__ import annotations

import logging

from dev_agent.config.config_manager import DevAgentConfig
from dev_agent.errors.exceptions import GenerationError
from dev_agent.interfaces.cli_interface import ICLIInterface
from dev_agent.interfaces.generation_interface import ISpecificationGenerator
from dev_agent.models.analysis import SpecificationAnalysis
from dev_agent.models.documents import SpecificationDocument
from dev_agent.services.azure_openai_service import AzureOpenAIService, ChatMessage

logger = logging.getLogger(__name__)


class AISpecificationGenerator(ISpecificationGenerator):
    """AI-powered specification generator using Azure OpenAI."""

    def __init__(
        self,
        config: DevAgentConfig,
        cli_interface: ICLIInterface | None = None,
    ):
        """Initialize AI specification generator.

        Args:
            config: Dev agent configuration
            cli_interface: Optional CLI interface for user interaction
        """
        self.config = config
        self.cli_interface = cli_interface
        self.ai_service = AzureOpenAIService(config.azure_openai)
        self.version = "1.0"

    def generate_from_existing_code(
        self, analysis: SpecificationAnalysis
    ) -> SpecificationDocument:
        """Generate specification from existing codebase analysis using AI.

        Args:
            analysis: Codebase analysis results

        Returns:
            Generated specification document

        Raises:
            GenerationError: If specification generation fails
        """
        try:
            logger.info(
                "Generating specification from codebase analysis using Azure OpenAI"
            )

            # Create system prompt for specification generation
            system_prompt = self._create_system_prompt_for_analysis()

            # Create user prompt with analysis data
            user_prompt = self._create_analysis_prompt(analysis)

            messages = [
                ChatMessage(role="system", content=system_prompt),
                ChatMessage(role="user", content=user_prompt),
            ]

            # Generate specification using AI
            response = self.ai_service.chat_completion(
                messages=messages,
                temperature=0.1,  # Low temperature for consistent, factual output
                max_tokens=4000,
            )

            # Parse AI response into specification document
            spec_doc = self._parse_ai_response_to_specification(
                response.content, analysis
            )

            logger.info("Successfully generated specification from codebase analysis")
            return spec_doc

        except Exception as e:
            logger.error(f"Failed to generate specification from analysis: {e}")
            raise GenerationError(f"Specification generation failed: {e}") from e

    def generate_from_user_input(
        self, user_requirements: list[str]
    ) -> SpecificationDocument:
        """Generate specification from user input using AI.

        Args:
            user_requirements: List of user requirements

        Returns:
            Generated specification document

        Raises:
            GenerationError: If specification generation fails
        """
        try:
            logger.info("Generating specification from user input using Azure OpenAI")

            if not user_requirements:
                user_requirements = self._collect_user_requirements()

            # Create system prompt for user requirements
            system_prompt = self._create_system_prompt_for_user_input()

            # Create user prompt with requirements
            user_prompt = self._create_user_requirements_prompt(user_requirements)

            messages = [
                ChatMessage(role="system", content=system_prompt),
                ChatMessage(role="user", content=user_prompt),
            ]

            # Generate specification using AI
            response = self.ai_service.chat_completion(
                messages=messages,
                temperature=0.2,  # Slightly higher temperature for creativity
                max_tokens=4000,
            )

            # Parse AI response into specification document
            spec_doc = self._parse_ai_response_to_specification(
                response.content, user_requirements=user_requirements
            )

            logger.info("Successfully generated specification from user input")
            return spec_doc

        except Exception as e:
            logger.error(f"Failed to generate specification from user input: {e}")
            raise GenerationError(f"Specification generation failed: {e}") from e

    def refine_specification(
        self, spec: SpecificationDocument, feedback: str
    ) -> SpecificationDocument:
        """Refine specification based on user feedback using AI.

        Args:
            spec: Current specification document
            feedback: User feedback for refinement

        Returns:
            Refined specification document

        Raises:
            GenerationError: If specification refinement fails
        """
        try:
            logger.info(
                "Refining specification based on user feedback using Azure OpenAI"
            )

            # Create system prompt for refinement
            system_prompt = self._create_system_prompt_for_refinement()

            # Create user prompt with current spec and feedback
            user_prompt = self._create_refinement_prompt(spec, feedback)

            messages = [
                ChatMessage(role="system", content=system_prompt),
                ChatMessage(role="user", content=user_prompt),
            ]

            # Refine specification using AI
            response = self.ai_service.chat_completion(
                messages=messages,
                temperature=0.1,  # Low temperature for consistent refinement
                max_tokens=4000,
            )

            # Parse AI response into refined specification
            refined_spec = self._parse_ai_response_to_specification(
                response.content, base_spec=spec
            )

            logger.info("Successfully refined specification based on feedback")
            return refined_spec

        except Exception as e:
            logger.error(f"Failed to refine specification: {e}")
            raise GenerationError(f"Specification refinement failed: {e}") from e

    def _create_system_prompt_for_analysis(self) -> str:
        """Create system prompt for analysis-based generation."""
        return """You are an expert software architect and technical writer. Your task is to generate a comprehensive software specification document based on codebase analysis.

Key requirements:
1. Create a clear, professional specification document
2. Base all content on the provided codebase analysis data
3. Use proper software engineering terminology
4. Structure the document with clear sections
5. Include functional and non-functional requirements
6. Provide acceptance criteria for each requirement
7. Maintain consistency with existing codebase patterns

Output format should be structured markdown with:
- Project Overview
- Key Features
- Functional Requirements (with user stories and acceptance criteria)
- Non-Functional Requirements
- Technical Constraints
- Dependencies

Be factual and avoid speculation beyond what the analysis provides."""

    def _create_system_prompt_for_user_input(self) -> str:
        """Create system prompt for user input-based generation."""
        return """You are an expert software architect and technical writer. Your task is to generate a comprehensive software specification document based on user requirements.

Key requirements:
1. Create a clear, professional specification document
2. Transform user requirements into well-structured specifications
3. Use proper software engineering terminology
4. Include both functional and non-functional requirements
5. Provide user stories and acceptance criteria
6. Consider scalability, security, and maintainability
7. Identify potential technical constraints and dependencies

Output format should be structured markdown with:
- Project Overview
- Key Features
- Functional Requirements (with user stories and acceptance criteria)
- Non-Functional Requirements
- Technical Constraints
- Dependencies

Ask clarifying questions if requirements are ambiguous, but provide a complete specification based on available information."""

    def _create_system_prompt_for_refinement(self) -> str:
        """Create system prompt for specification refinement."""
        return """You are an expert software architect and technical writer. Your task is to refine an existing software specification document based on user feedback.

Key requirements:
1. Carefully analyze the provided feedback
2. Update the specification to address all feedback points
3. Maintain document structure and consistency
4. Preserve existing content that doesn't conflict with feedback
5. Ensure all changes are well-integrated
6. Update related sections as needed
7. Maintain professional technical writing standards

Focus on:
- Addressing specific feedback points
- Improving clarity and completeness
- Ensuring technical accuracy
- Maintaining document coherence

Provide the complete refined specification document."""

    def _create_analysis_prompt(self, analysis: SpecificationAnalysis) -> str:
        """Create user prompt with codebase analysis data."""
        prompt_parts = [
            "Please generate a comprehensive software specification document based on the following codebase analysis:",
            "",
            f"**Project Purpose:** {analysis.project_purpose}",
            f"**Confidence Score:** {analysis.confidence_score:.1%}",
            "",
        ]

        if analysis.main_features:
            prompt_parts.extend(
                [
                    "**Main Features:**",
                    *[f"- {feature}" for feature in analysis.main_features],
                    "",
                ]
            )

        if analysis.functional_areas:
            prompt_parts.extend(
                [
                    "**Functional Areas:**",
                    *[f"- {area}" for area in analysis.functional_areas],
                    "",
                ]
            )

        if analysis.user_roles:
            prompt_parts.extend(
                [
                    "**User Roles:**",
                    *[f"- {role}" for role in analysis.user_roles],
                    "",
                ]
            )

        if analysis.technology_constraints:
            prompt_parts.extend(
                [
                    "**Technology Constraints:**",
                    *[
                        f"- {constraint}"
                        for constraint in analysis.technology_constraints
                    ],
                    "",
                ]
            )

        if analysis.requirement_evidence:
            prompt_parts.extend(
                [
                    "**Requirement Evidence:**",
                ]
            )
            for evidence in analysis.requirement_evidence[
                :10
            ]:  # Limit to avoid token overflow
                prompt_parts.extend(
                    [
                        f"- **{evidence.requirement_type}:** {evidence.description}",
                        f"  - Confidence: {evidence.confidence:.1%}",
                        f"  - Supporting files: {', '.join(evidence.supporting_files[:3])}",
                        "",
                    ]
                )

        prompt_parts.append(
            "Generate a complete, professional specification document based on this analysis."
        )

        return "\n".join(prompt_parts)

    def _create_user_requirements_prompt(self, user_requirements: list[str]) -> str:
        """Create user prompt with user requirements."""
        prompt_parts = [
            "Please generate a comprehensive software specification document based on the following user requirements:",
            "",
        ]

        for i, requirement in enumerate(user_requirements, 1):
            prompt_parts.append(f"{i}. {requirement}")

        prompt_parts.extend(
            [
                "",
                "Generate a complete, professional specification document that addresses all these requirements.",
                "Include user stories, acceptance criteria, and technical considerations.",
            ]
        )

        return "\n".join(prompt_parts)

    def _create_refinement_prompt(
        self, spec: SpecificationDocument, feedback: str
    ) -> str:
        """Create user prompt for specification refinement."""
        current_spec = self._format_specification_for_prompt(spec)

        prompt_parts = [
            "Please refine the following specification document based on the provided feedback:",
            "",
            "**Current Specification:**",
            current_spec,
            "",
            "**User Feedback:**",
            feedback,
            "",
            "Please provide the complete refined specification document that addresses all feedback points.",
        ]

        return "\n".join(prompt_parts)

    def _format_specification_for_prompt(self, spec: SpecificationDocument) -> str:
        """Format specification document for use in prompts."""
        parts = [
            f"# {spec.title}",
            "",
            f"**Version:** {spec.version}",
            f"**Created:** {spec.created_at}",
            "",
            "## Introduction",
            spec.introduction,
            "",
        ]

        if spec.key_features:
            parts.extend(
                [
                    "## Key Features",
                    *[f"- {feature}" for feature in spec.key_features],
                    "",
                ]
            )

        if spec.functional_requirements:
            parts.extend(
                [
                    "## Functional Requirements",
                ]
            )
            for req in spec.functional_requirements:
                parts.extend(
                    [
                        f"### {req.id}: {req.user_story}",
                        "",
                        "**Acceptance Criteria:**",
                        *[f"- {criteria}" for criteria in req.acceptance_criteria],
                        "",
                    ]
                )

        return "\n".join(parts)

    def _parse_ai_response_to_specification(
        self,
        ai_response: str,
        analysis: SpecificationAnalysis | None = None,
        user_requirements: list[str] | None = None,
        base_spec: SpecificationDocument | None = None,
    ) -> SpecificationDocument:
        """Parse AI response into a specification document.

        This is a simplified parser. In a production system, you might want
        to use more sophisticated parsing or ask the AI to return structured JSON.
        """
        from datetime import datetime

        from dev_agent.models.documents import Requirement
        from dev_agent.models.enums import Priority, SpecificationSource

        # Extract title (look for first # heading)
        lines = ai_response.split("\n")
        title = "Generated Specification"
        for line in lines:
            if line.startswith("# "):
                title = line[2:].strip()
                break

        # Extract introduction (content after "Introduction" or similar)
        introduction = "This specification was generated using AI analysis."
        intro_start = -1
        for i, line in enumerate(lines):
            if any(
                keyword in line.lower()
                for keyword in ["introduction", "overview", "purpose"]
            ):
                intro_start = i + 1
                break

        if intro_start > 0:
            intro_lines = []
            for i in range(intro_start, len(lines)):
                line = lines[i].strip()
                if line.startswith("#") and i > intro_start:
                    break
                if line and not line.startswith("**"):
                    intro_lines.append(line)
            if intro_lines:
                introduction = " ".join(intro_lines)

        # Extract key features (look for bullet points under features section)
        key_features = []
        features_start = -1
        for i, line in enumerate(lines):
            if any(
                keyword in line.lower()
                for keyword in ["key features", "features", "capabilities"]
            ):
                features_start = i + 1
                break

        if features_start > 0:
            for i in range(features_start, len(lines)):
                line = lines[i].strip()
                if line.startswith("#") and i > features_start:
                    break
                if line.startswith("- ") or line.startswith("* "):
                    key_features.append(line[2:].strip())

        # Create basic functional requirements
        # In a production system, you'd parse these more carefully from the AI response
        functional_requirements = []
        if analysis and analysis.requirement_evidence:
            for i, evidence in enumerate(analysis.requirement_evidence[:5], 1):
                req = Requirement(
                    id=f"REQ-{i:03d}",
                    user_story=f"As a user, I want {evidence.description.lower()}",
                    acceptance_criteria=[
                        f"GIVEN the system is operational WHEN I {evidence.description.lower()} THEN the system SHALL respond appropriately",
                        "WHEN I interact with this functionality THEN the system SHALL provide feedback",
                    ],
                    priority=Priority.MEDIUM,
                    source=SpecificationSource.CODEBASE_ANALYSIS,
                )
                functional_requirements.append(req)
        elif user_requirements:
            for i, req_text in enumerate(user_requirements[:5], 1):
                req = Requirement(
                    id=f"REQ-{i:03d}",
                    user_story=f"As a user, I want to {req_text.lower()}",
                    acceptance_criteria=[
                        f"GIVEN the system is operational WHEN I {req_text.lower()} THEN the system SHALL respond appropriately",
                        "WHEN I interact with this functionality THEN the system SHALL provide feedback",
                    ],
                    priority=Priority.MEDIUM,
                    source=SpecificationSource.USER_INPUT,
                )
                functional_requirements.append(req)

        return SpecificationDocument(
            title=title,
            version=base_spec.version if base_spec else "1.0",
            created_at=base_spec.created_at if base_spec else datetime.now(),
            introduction=introduction,
            key_features=key_features,
            functional_requirements=functional_requirements,
            non_functional_requirements=[],
            glossary={},
            appendices=[],
        )

    def _collect_user_requirements(self) -> list[str]:
        """Collect requirements from user via CLI interface."""
        if not self.cli_interface:
            return [
                "Implement core functionality",
                "Provide user interface",
                "Ensure data persistence",
            ]

        requirements = []
        self.cli_interface.display_info(
            "Please provide your requirements (enter empty line to finish):"
        )

        while True:
            requirement = self.cli_interface.get_user_input("Requirement: ")
            if not requirement.strip():
                break
            requirements.append(requirement.strip())

        return requirements or [
            "Implement core functionality",
            "Provide user interface",
            "Ensure data persistence",
        ]
