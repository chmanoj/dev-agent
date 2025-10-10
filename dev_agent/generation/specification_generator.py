"""Specification generator for creating SPECIFICATION.md documents."""

from __future__ import annotations

import logging
import re
from datetime import datetime
from typing import TYPE_CHECKING, Any

from rich.panel import Panel

from ..errors.llm_exceptions import (
    LLMAPIError,
    LLMAuthenticationError,
    LLMBadRequestError,
    LLMError,
    LLMRateLimitError,
    LLMTimeoutError,
    LLMTokenLimitError,
)
from ..interfaces.cli_interface import ICLIInterface
from ..interfaces.generation_interface import ISpecificationGenerator
from ..llm import create_llm_client, get_preferred_provider
from ..llm.prompt_templates import get_template
from ..models.analysis import RequirementEvidence, SpecificationAnalysis
from ..models.documents import CodeAnalysisRef, Requirement, SpecificationDocument
from ..models.enums import LLMProvider, Priority, SpecificationSource

if TYPE_CHECKING:
    from ..indexing.vector_database import VectorDatabase
    from ..llm.base import ILLMClient
    from ..llm.cost_tracker import CostTracker
    from ..llm.token_counter import TokenCounter

logger = logging.getLogger(__name__)


class SpecificationGenerator(ISpecificationGenerator):
    """Generates specification documents from codebase analysis or user input.
    
    This generator uses Azure OpenAI (GPT-4) to create detailed specifications
    based on codebase analysis and vector search for relevant code examples.
    It integrates with cost tracking and token management for efficient API usage.
    
    Example:
        ```python
        from dev_agent.llm.azure_client import AzureOpenAIClient
        from dev_agent.llm.cost_tracker import CostTracker
        from dev_agent.llm.token_counter import TokenCounter
        from dev_agent.indexing.vector_database import VectorDatabase
        
        llm_client = AzureOpenAIClient(config)
        cost_tracker = CostTracker()
        token_counter = TokenCounter()
        vector_db = VectorDatabase(index_path, embedding_client)
        
        generator = SpecificationGenerator(
            llm_client=llm_client,
            cost_tracker=cost_tracker,
            token_counter=token_counter,
            vector_db=vector_db,
        )
        
        spec = await generator.generate_from_existing_code(analysis)
        ```
    """

    def __init__(
        self,
        cli_interface: ICLIInterface | None = None,
        llm_client: ILLMClient | None = None,
        cost_tracker: CostTracker | None = None,
        token_counter: TokenCounter | None = None,
        vector_db: VectorDatabase | None = None,
        provider: LLMProvider | str | None = None,
    ):
        """Initialize the specification generator.

        Args:
            cli_interface: Optional CLI interface for user interaction
            llm_client: LLM client for AI-powered generation (optional for backward compatibility)
            cost_tracker: Cost tracker for monitoring API usage (optional)
            token_counter: Token counter for validation (optional)
            vector_db: Vector database for context retrieval (optional)
            provider: LLM provider to use (optional, defaults to preferred provider)
        """
        self.cli_interface = cli_interface
        self.cost_tracker = cost_tracker
        self.token_counter = token_counter
        self.vector_db = vector_db
        self.version = "1.0"
        
        # Initialize LLM client using factory pattern
        if llm_client is not None:
            # Use provided client for backward compatibility
            self.llm_client = llm_client
            logger.info("SpecificationGenerator initialized with provided LLM client")
        else:
            # Create client using factory pattern
            try:
                self.llm_client = create_llm_client(provider=provider)
                current_provider = get_preferred_provider()
                logger.info(f"SpecificationGenerator initialized with {current_provider.value} LLM client")
            except (ValueError, ImportError) as e:
                logger.warning(f"Failed to create LLM client: {e}")
                self.llm_client = None
                logger.warning(
                    "SpecificationGenerator initialized without LLM client - "
                    "AI-powered generation will not be available"
                )

    async def generate_from_existing_code_ai(
        self,
        analysis: SpecificationAnalysis,
        feature_description: str,
    ) -> SpecificationDocument:
        """Generate specification using AI from existing codebase analysis.
        
        This method uses Azure OpenAI (GPT-4) to generate a comprehensive
        specification based on codebase analysis and relevant code examples
        retrieved via vector search.

        Args:
            analysis: Results from codebase analysis
            feature_description: Description of the feature to specify

        Returns:
            Generated specification document
            
        Raises:
            ValueError: If LLM client is not configured
            LLMError: If AI generation fails
        """
        if not self.llm_client:
            error_message = (
                "LLM client not configured. Initialize SpecificationGenerator "
                "with an ILLMClient instance for AI-powered generation.\n\n"
                "To configure Azure OpenAI:\n"
                "  1. Run: dev-agent azure configure\n"
                "  2. Or set environment variables:\n"
                "     AZURE_OPENAI_ENDPOINT\n"
                "     AZURE_OPENAI_API_KEY\n"
                "     AZURE_OPENAI_DEPLOYMENT_NAME\n"
                "     AZURE_OPENAI_EMBEDDING_DEPLOYMENT"
            )
            if self.cli_interface:
                self.cli_interface.display_message(
                    Panel(
                        f"[red]{error_message}[/red]",
                        title="❌ LLM Client Not Configured",
                        border_style="red",
                    )
                )
            raise ValueError(error_message)
        
        logger.info(f"Generating AI-powered specification for: {feature_description}")
        
        try:
            # Retrieve relevant code chunks via vector search
            if self.cli_interface:
                self.cli_interface.display_message("  📚 Retrieving relevant code examples...")
            relevant_chunks = await self._retrieve_relevant_context(feature_description)
            
            # Build context for prompt template
            context = self._build_specification_context(
                analysis=analysis,
                feature_description=feature_description,
                relevant_chunks=relevant_chunks,
            )
            
            # Get specification template
            template = get_template("specification")
            
            # Validate token limits before generation
            if self.token_counter:
                system_prompt, user_prompt = template.render(context, self.token_counter)
                prompt_tokens = self.token_counter.count_tokens(user_prompt)
                system_tokens = self.token_counter.count_tokens(system_prompt)
                total_prompt_tokens = prompt_tokens + system_tokens
                
                is_valid, error_msg = self.token_counter.validate_context_window(
                    prompt_tokens=total_prompt_tokens,
                    max_completion_tokens=template.max_tokens,
                )
                
                if not is_valid:
                    raise LLMTokenLimitError(error_msg)
                
                logger.info(
                    f"Token validation passed: {total_prompt_tokens} prompt tokens, "
                    f"{template.max_tokens} max completion tokens"
                )
            else:
                system_prompt, user_prompt = template.render(context)
            
            # Generate specification using LLM
            if self.cli_interface:
                self.cli_interface.display_message("  🧠 Calling Azure OpenAI API...")
            logger.info("Calling Azure OpenAI for specification generation...")
            spec_content = await self.llm_client.generate_completion(
                prompt=user_prompt,
                system_prompt=system_prompt,
                temperature=template.temperature,
                max_tokens=template.max_tokens,
            )
            
            # Track cost if tracker available
            if self.cost_tracker and self.token_counter:
                prompt_tokens = self.token_counter.count_tokens(user_prompt + system_prompt)
                completion_tokens = self.token_counter.count_tokens(spec_content)
                cost = self.cost_tracker.record_completion(
                    prompt_tokens=prompt_tokens,
                    completion_tokens=completion_tokens,
                    model=self.token_counter.get_model_name(),
                    provider=self.token_counter.get_provider_enum(),
                )
                logger.info(
                    f"Specification generation cost: ${cost:.4f} "
                    f"({prompt_tokens} + {completion_tokens} tokens)"
                )
            
            # Parse AI-generated content into structured document
            if self.cli_interface:
                self.cli_interface.display_message("  📝 Parsing specification...")
            spec_doc = self._parse_ai_specification(spec_content, analysis)
            
            logger.info("AI-powered specification generated successfully")
            return spec_doc
            
        except LLMAuthenticationError as e:
            logger.error(f"Authentication failed: {e}")
            raise
        except LLMRateLimitError as e:
            logger.warning(f"Rate limit hit: {e}")
            raise
        except LLMTimeoutError as e:
            logger.error(f"Request timed out: {e}")
            raise
        except LLMBadRequestError as e:
            logger.error(f"Bad request: {e}")
            raise
        except LLMTokenLimitError as e:
            logger.error(f"Token limit exceeded: {e}")
            raise
        except LLMAPIError as e:
            logger.error(f"API error: {e}")
            raise
        except LLMError as e:
            logger.error(f"LLM error: {e}")
            raise
        except Exception as e:
            logger.error(f"Unexpected error during AI generation: {e}")
            raise LLMAPIError(
                f"Failed to generate specification: {e}",
                "Check logs for details and verify Azure OpenAI configuration"
            ) from e

    def generate_from_existing_code(
        self, analysis: SpecificationAnalysis
    ) -> SpecificationDocument:
        """Generate specification from existing codebase analysis.
        
        This is the legacy method that uses rule-based generation.
        For AI-powered generation, use generate_from_existing_code_ai().

        Args:
            analysis: Results from codebase analysis

        Returns:
            Generated specification document
        """
        # Generate introduction based on analysis
        introduction = self._generate_introduction_from_analysis(analysis)

        # Extract key features from analysis
        key_features = self._extract_key_features_from_analysis(analysis)

        # Generate functional requirements from evidence
        functional_requirements = self._generate_requirements_from_evidence(analysis)

        return SpecificationDocument(
            introduction=introduction,
            key_features=key_features,
            functional_requirements=functional_requirements,
            source=SpecificationSource.EXISTING_CODE,
            version=self.version,
            approved=False,
        )

    def generate_from_user_input(
        self, user_requirements: list[str]
    ) -> SpecificationDocument:
        """Generate specification from user input and requirements.

        Args:
            user_requirements: List of user-provided requirements

        Returns:
            Generated specification document
        """
        if not user_requirements:
            user_requirements = self._collect_user_requirements()

        # Generate introduction from user input
        introduction = self._generate_introduction_from_user_input(user_requirements)

        # Extract key features from user requirements
        key_features = self._extract_key_features_from_user_input(user_requirements)

        # Generate functional requirements from user input
        functional_requirements = self._generate_requirements_from_user_input(
            user_requirements
        )

        return SpecificationDocument(
            introduction=introduction,
            key_features=key_features,
            functional_requirements=functional_requirements,
            source=SpecificationSource.USER_INPUT,
            version=self.version,
            approved=False,
        )

    async def generate_from_user_input_ai(
        self,
        feature_description: str,
    ) -> SpecificationDocument:
        """Generate specification from user input using AI.
        
        For new projects without existing code, this generates a specification
        based solely on the user's feature description using Azure OpenAI.

        Args:
            feature_description: Description of the feature to build

        Returns:
            Generated specification document
            
        Raises:
            ValueError: If LLM client is not configured
            LLMError: If AI generation fails
        """
        if not self.llm_client:
            error_message = (
                "LLM client not configured. Initialize SpecificationGenerator "
                "with an ILLMClient instance for AI-powered generation.\n\n"
                "To configure Azure OpenAI:\n"
                "  1. Run: dev-agent azure configure\n"
                "  2. Or set environment variables:\n"
                "     AZURE_OPENAI_ENDPOINT\n"
                "     AZURE_OPENAI_API_KEY\n"
                "     AZURE_OPENAI_DEPLOYMENT_NAME\n"
                "     AZURE_OPENAI_EMBEDDING_DEPLOYMENT"
            )
            if self.cli_interface:
                self.cli_interface.display_message(
                    Panel(
                        f"[red]{error_message}[/red]",
                        title="❌ LLM Client Not Configured",
                        border_style="red",
                    )
                )
            raise ValueError(error_message)
        
        logger.info(f"Generating AI-powered specification for new project: {feature_description}")
        
        try:
            # Build context for new project template
            context = {
                "feature_description": feature_description,
                "project_type": "new",
            }
            
            # Get template and generate
            template = get_template("specification_new_project")
            
            # Validate token limits before generation
            if self.token_counter:
                system_prompt, user_prompt = template.render(context, self.token_counter)
                prompt_tokens = self.token_counter.count_tokens(user_prompt)
                system_tokens = self.token_counter.count_tokens(system_prompt)
                total_prompt_tokens = prompt_tokens + system_tokens
                
                is_valid, error_msg = self.token_counter.validate_context_window(
                    prompt_tokens=total_prompt_tokens,
                    max_completion_tokens=template.max_tokens,
                )
                
                if not is_valid:
                    raise LLMTokenLimitError(error_msg)
                
                logger.info(
                    f"Token validation passed: {total_prompt_tokens} prompt tokens, "
                    f"{template.max_tokens} max completion tokens"
                )
            else:
                system_prompt, user_prompt = template.render(context)
            
            # Generate specification using LLM
            if self.cli_interface:
                self.cli_interface.display_message("  🧠 Calling Azure OpenAI API...")
            logger.info("Calling Azure OpenAI for new project specification generation...")
            spec_content = await self.llm_client.generate_completion(
                prompt=user_prompt,
                system_prompt=system_prompt,
                temperature=template.temperature,
                max_tokens=template.max_tokens,
            )
            
            # Track cost if tracker available
            if self.cost_tracker and self.token_counter:
                prompt_tokens = self.token_counter.count_tokens(user_prompt + system_prompt)
                completion_tokens = self.token_counter.count_tokens(spec_content)
                cost = self.cost_tracker.record_completion(
                    prompt_tokens=prompt_tokens,
                    completion_tokens=completion_tokens,
                    model=self.token_counter.get_model_name(),
                    provider=self.token_counter.get_provider_enum(),
                )
                logger.info(
                    f"Specification generation cost: ${cost:.4f} "
                    f"({prompt_tokens} + {completion_tokens} tokens)"
                )
            
            # Parse AI-generated content into structured document
            if self.cli_interface:
                self.cli_interface.display_message("  📝 Parsing specification...")
            spec_doc = self._parse_ai_specification(spec_content, None)
            
            # Set source to USER_INPUT for new projects
            spec_doc.source = SpecificationSource.USER_INPUT
            
            logger.info("AI-powered specification for new project generated successfully")
            return spec_doc
            
        except LLMAuthenticationError as e:
            logger.error(f"Authentication failed: {e}")
            raise
        except LLMRateLimitError as e:
            logger.warning(f"Rate limit hit: {e}")
            raise
        except LLMTimeoutError as e:
            logger.error(f"Request timed out: {e}")
            raise
        except LLMBadRequestError as e:
            logger.error(f"Bad request: {e}")
            raise
        except LLMTokenLimitError as e:
            logger.error(f"Token limit exceeded: {e}")
            raise
        except LLMAPIError as e:
            logger.error(f"API error: {e}")
            raise
        except LLMError as e:
            logger.error(f"LLM error: {e}")
            raise
        except Exception as e:
            logger.error(f"Unexpected error during AI generation: {e}")
            raise LLMAPIError(
                f"Failed to generate specification: {e}",
                "Check logs for details and verify Azure OpenAI configuration"
            ) from e

    def refine_specification(
        self, spec: SpecificationDocument, feedback: str
    ) -> SpecificationDocument:
        """Refine specification based on user feedback.

        Args:
            spec: Original specification document
            feedback: User feedback for refinement

        Returns:
            Refined specification document
        """
        # Parse feedback to understand what needs to be changed
        refinements = self._parse_feedback(feedback)

        # Apply refinements to the specification
        refined_spec = self._apply_refinements(spec, refinements)

        # Update version and reset approval status
        refined_spec.version = self._increment_version(spec.version)
        refined_spec.approved = False
        refined_spec.approval_timestamp = None

        return refined_spec

    async def refine_specification_ai(
        self,
        spec: SpecificationDocument,
        feedback: str,
        feature_description: str,
    ) -> SpecificationDocument:
        """Refine specification using AI based on user feedback.
        
        This method uses the LLM to understand the feedback and generate
        an improved version of the specification that incorporates the
        requested changes.

        Args:
            spec: Original specification document
            feedback: User feedback for refinement
            feature_description: Original feature description

        Returns:
            Refined specification document
            
        Raises:
            ValueError: If LLM client is not configured
            LLMError: If AI refinement fails
        """
        if not self.llm_client:
            error_message = (
                "LLM client not configured. Initialize SpecificationGenerator "
                "with an ILLMClient instance for AI-powered refinement.\n\n"
                "To configure Azure OpenAI:\n"
                "  1. Run: dev-agent azure configure\n"
                "  2. Or set environment variables:\n"
                "     AZURE_OPENAI_ENDPOINT\n"
                "     AZURE_OPENAI_API_KEY\n"
                "     AZURE_OPENAI_DEPLOYMENT_NAME\n"
                "     AZURE_OPENAI_EMBEDDING_DEPLOYMENT"
            )
            if self.cli_interface:
                self.cli_interface.display_message(
                    Panel(
                        f"[red]{error_message}[/red]",
                        title="❌ LLM Client Not Configured",
                        border_style="red",
                    )
                )
            raise ValueError(error_message)
        
        logger.info("Refining specification using AI based on user feedback")
        
        try:
            # Format current specification as text
            current_spec_text = self.format_specification_document(spec)
            
            # Build context for refinement
            context = {
                "current_specification": current_spec_text,
                "user_feedback": feedback,
                "feature_description": feature_description,
            }
            
            # Get refinement template
            template = get_template("specification_refinement")
            
            # Validate token limits before generation
            if self.token_counter:
                system_prompt, user_prompt = template.render(context, self.token_counter)
                prompt_tokens = self.token_counter.count_tokens(user_prompt)
                system_tokens = self.token_counter.count_tokens(system_prompt)
                total_prompt_tokens = prompt_tokens + system_tokens
                
                is_valid, error_msg = self.token_counter.validate_context_window(
                    prompt_tokens=total_prompt_tokens,
                    max_completion_tokens=template.max_tokens,
                )
                
                if not is_valid:
                    raise LLMTokenLimitError(error_msg)
                
                logger.info(
                    f"Token validation passed: {total_prompt_tokens} prompt tokens, "
                    f"{template.max_tokens} max completion tokens"
                )
            else:
                system_prompt, user_prompt = template.render(context)
            
            # Generate refined specification using LLM
            if self.cli_interface:
                self.cli_interface.display_message("  🧠 Calling Azure OpenAI API...")
            logger.info("Calling Azure OpenAI for specification refinement...")
            refined_content = await self.llm_client.generate_completion(
                prompt=user_prompt,
                system_prompt=system_prompt,
                temperature=template.temperature,
                max_tokens=template.max_tokens,
            )
            
            # Track cost if tracker available
            if self.cost_tracker and self.token_counter:
                prompt_tokens = self.token_counter.count_tokens(user_prompt + system_prompt)
                completion_tokens = self.token_counter.count_tokens(refined_content)
                cost = self.cost_tracker.record_completion(
                    prompt_tokens=prompt_tokens,
                    completion_tokens=completion_tokens,
                    model=self.token_counter.get_model_name(),
                    provider=self.token_counter.get_provider_enum(),
                )
                logger.info(
                    f"Specification refinement cost: ${cost:.4f} "
                    f"({prompt_tokens} + {completion_tokens} tokens)"
                )
            
            # Parse refined specification
            if self.cli_interface:
                self.cli_interface.display_message("  📝 Parsing refined specification...")
            refined_spec = self._parse_ai_specification(refined_content, None)
            
            # Preserve source from original spec
            refined_spec.source = spec.source
            
            # Update version and reset approval
            refined_spec.version = self._increment_version(spec.version)
            refined_spec.approved = False
            refined_spec.approval_timestamp = None
            
            logger.info("AI-powered specification refinement completed successfully")
            return refined_spec
            
        except LLMAuthenticationError as e:
            logger.error(f"Authentication failed: {e}")
            raise
        except LLMRateLimitError as e:
            logger.warning(f"Rate limit hit: {e}")
            raise
        except LLMTimeoutError as e:
            logger.error(f"Request timed out: {e}")
            raise
        except LLMBadRequestError as e:
            logger.error(f"Bad request: {e}")
            raise
        except LLMTokenLimitError as e:
            logger.error(f"Token limit exceeded: {e}")
            raise
        except LLMAPIError as e:
            logger.error(f"API error: {e}")
            raise
        except LLMError as e:
            logger.error(f"LLM error: {e}")
            raise
        except Exception as e:
            logger.error(f"Unexpected error during AI refinement: {e}")
            raise LLMAPIError(
                f"Failed to refine specification: {e}",
                "Check logs for details and verify Azure OpenAI configuration"
            ) from e

    def format_specification_document(self, spec: SpecificationDocument) -> str:
        """Format specification document as markdown.

        Args:
            spec: Specification document to format

        Returns:
            Formatted markdown string
        """
        lines = []

        # Header
        lines.append("# Requirements Document")
        lines.append("")

        # Introduction
        lines.append("## Introduction")
        lines.append("")
        lines.append(spec.introduction)
        lines.append("")

        # Key Features
        if spec.key_features:
            lines.append("## Key Features")
            lines.append("")
            for feature in spec.key_features:
                lines.append(f"- {feature}")
            lines.append("")

        # Functional Requirements
        lines.append("## Requirements")
        lines.append("")

        for i, req in enumerate(spec.functional_requirements, 1):
            lines.append(f"### Requirement {i}")
            lines.append("")
            lines.append(f"**User Story:** {req.user_story}")
            lines.append("")
            lines.append("#### Acceptance Criteria")
            lines.append("")

            for j, criteria in enumerate(req.acceptance_criteria, 1):
                lines.append(f"{j}. {criteria}")

            # Add source analysis if available
            if req.source_analysis:
                lines.append("")
                lines.append("#### Supporting Code Analysis")
                lines.append("")
                lines.append(
                    f"- **Files:** {', '.join(req.source_analysis.file_paths[:3])}"
                )
                if len(req.source_analysis.file_paths) > 3:
                    lines.append(
                        f"  (and {len(req.source_analysis.file_paths) - 3} more)"
                    )
                lines.append(
                    f"- **Functions:** {', '.join(req.source_analysis.functions[:3])}"
                )
                if len(req.source_analysis.functions) > 3:
                    lines.append(
                        f"  (and {len(req.source_analysis.functions) - 3} more)"
                    )
                lines.append(
                    f"- **Confidence:** {req.source_analysis.confidence_score:.1%}"
                )

            lines.append("")

        # Metadata
        lines.append("---")
        lines.append("")
        lines.append("## Document Metadata")
        lines.append("")
        lines.append(f"- **Source:** {spec.source.value}")
        lines.append(f"- **Version:** {spec.version}")
        lines.append(f"- **Status:** {'Approved' if spec.approved else 'Draft'}")
        if spec.approval_timestamp:
            lines.append(
                f"- **Approved:** {spec.approval_timestamp.strftime('%Y-%m-%d %H:%M:%S')}"
            )

        return "\n".join(lines)

    def request_user_approval(self, spec: SpecificationDocument) -> bool:
        """Request user approval for the specification.

        Args:
            spec: Specification document to approve

        Returns:
            True if approved, False otherwise
        """
        if not self.cli_interface:
            # Auto-approve if no CLI interface
            spec.approved = True
            spec.approval_timestamp = datetime.now()
            return True

        formatted_spec = self.format_specification_document(spec)
        approved = self.cli_interface.request_approval(formatted_spec, "specification")

        if approved:
            spec.approved = True
            spec.approval_timestamp = datetime.now()

        return approved

    # Private helper methods for AI-powered generation

    async def _retrieve_relevant_context(
        self,
        feature_description: str,
        top_k: int = 5,
    ) -> list[str]:
        """Retrieve relevant code chunks via vector search.
        
        Args:
            feature_description: Description of the feature
            top_k: Number of relevant chunks to retrieve
            
        Returns:
            List of relevant code chunk contents
        """
        if not self.vector_db:
            logger.warning("Vector database not available, skipping context retrieval")
            return []
        
        try:
            matches = await self.vector_db.query_similar(
                query_text=feature_description,
                k=top_k,
                min_similarity=0.5,
            )
            
            # Format chunks with file paths and line numbers
            formatted_chunks = []
            for match in matches:
                chunk_info = (
                    f"File: {match.chunk.file_path}\n"
                    f"Lines: {match.chunk.start_line}-{match.chunk.end_line}\n"
                    f"Similarity: {match.similarity_score:.2f}\n"
                    f"```{match.chunk.language}\n"
                    f"{match.chunk.content}\n"
                    f"```"
                )
                formatted_chunks.append(chunk_info)
            
            logger.info(f"Retrieved {len(formatted_chunks)} relevant code chunks")
            return formatted_chunks
            
        except Exception as e:
            logger.warning(f"Failed to retrieve context from vector DB: {e}")
            return []

    def _build_specification_context(
        self,
        analysis: SpecificationAnalysis,
        feature_description: str,
        relevant_chunks: list[str],
    ) -> dict[str, str]:
        """Build context dictionary for specification prompt template.
        
        Args:
            analysis: Codebase analysis results
            feature_description: Feature to specify
            relevant_chunks: Relevant code chunks from vector search
            
        Returns:
            Context dictionary for template rendering
        """
        # Build codebase summary - FOCUSED on context, not features
        codebase_summary = (
            f"Project Purpose: {analysis.project_purpose}\n\n"
            f"Technology Stack:\n"
        )
        for tech in analysis.technology_constraints[:5]:
            codebase_summary += f"- {tech}\n"
        
        # Only include user roles if relevant
        if analysis.user_roles:
            codebase_summary += f"\nUser Roles: {', '.join(analysis.user_roles)}\n"
        
        # Format relevant code chunks - these should be MOST relevant to the feature request
        relevant_code_chunks = "\n\n---\n\n".join(relevant_chunks) if relevant_chunks else "No relevant code examples found."
        
        # Extract detected patterns - focus on architectural patterns, not features
        detected_patterns = "Architectural and coding patterns detected:\n"
        if analysis.requirement_evidence:
            for evidence in analysis.requirement_evidence[:3]:
                detected_patterns += f"- {evidence.requirement_type}: {evidence.description}\n"
        else:
            detected_patterns += "- No specific patterns detected\n"
        
        return {
            "codebase_summary": codebase_summary,
            "relevant_code_chunks": relevant_code_chunks,
            "detected_patterns": detected_patterns,
            "feature_description": feature_description,
        }

    def _parse_ai_specification(
        self,
        ai_content: str,
        analysis: SpecificationAnalysis | None,
    ) -> SpecificationDocument:
        """Parse AI-generated specification content into structured document.
        
        This method extracts structured information from the AI-generated
        markdown content and creates a SpecificationDocument with enhanced
        parsing and validation.
        
        Args:
            ai_content: AI-generated specification content
            analysis: Original codebase analysis (None for new projects)
            
        Returns:
            Structured SpecificationDocument
        """
        try:
            # Extract sections from AI-generated content
            sections = self._extract_sections(ai_content)
            
            # Extract introduction (Overview section)
            introduction = sections.get("overview", sections.get("introduction", ""))
            if not introduction:
                # Fallback to first paragraph
                paragraphs = [p.strip() for p in ai_content.split("\n\n") if p.strip()]
                introduction = paragraphs[0] if paragraphs else "AI-generated specification"
            
            # Extract key features
            key_features = self._extract_list_items(
                sections.get("functional requirements", sections.get("key features", ""))
            )
            if not key_features and analysis:
                key_features = analysis.main_features[:5]
            elif not key_features:
                # For new projects without analysis, extract from content
                key_features = ["Feature implementation"]
            
            # Extract functional requirements with enhanced parsing
            functional_requirements = self._extract_requirements_from_ai_content_enhanced(
                ai_content,
                sections,
            )
            
            # If no requirements extracted and we have analysis, fall back to analysis-based generation
            if not functional_requirements and analysis:
                logger.warning("No requirements extracted from AI content, using analysis-based generation")
                functional_requirements = self._generate_requirements_from_evidence(analysis)
            elif not functional_requirements:
                # For new projects, create a basic requirement
                logger.warning("No requirements extracted from AI content for new project")
                functional_requirements = [
                    Requirement(
                        id="FR-1",
                        user_story="As a user, I want the system to implement the requested feature",
                        acceptance_criteria=["WHEN the feature is implemented THEN it SHALL work as specified"],
                        priority=Priority.HIGH,
                    )
                ]
            
            spec_doc = SpecificationDocument(
                introduction=introduction,
                key_features=key_features,
                functional_requirements=functional_requirements,
                source=SpecificationSource.EXISTING_CODE,
                version=self.version,
                approved=False,
            )
            
            # Validate the parsed specification
            is_valid, validation_issues = self._validate_specification(spec_doc)
            if not is_valid:
                logger.warning(f"Specification validation issues: {validation_issues}")
                # Log detailed parsing failure information
                self._log_parsing_details(ai_content, sections, functional_requirements, validation_issues)
            
            return spec_doc
            
        except Exception as e:
            logger.error(f"Failed to parse AI specification: {e}")
            self._log_parsing_failure(ai_content, str(e))
            raise

    def _extract_sections(self, content: str) -> dict[str, str]:
        """Extract sections from markdown content.
        
        Args:
            content: Markdown content
            
        Returns:
            Dictionary mapping section names to content
        """
        sections = {}
        current_section = None
        current_content = []
        
        for line in content.split("\n"):
            # Check for section headers (## or ###)
            if line.startswith("##"):
                # Save previous section
                if current_section:
                    sections[current_section.lower()] = "\n".join(current_content).strip()
                
                # Start new section
                current_section = line.lstrip("#").strip()
                current_content = []
            elif current_section:
                current_content.append(line)
        
        # Save last section
        if current_section:
            sections[current_section.lower()] = "\n".join(current_content).strip()
        
        return sections

    def _extract_list_items(self, content: str) -> list[str]:
        """Extract list items from markdown content.
        
        Args:
            content: Markdown content with list items
            
        Returns:
            List of extracted items
        """
        items = []
        for line in content.split("\n"):
            line = line.strip()
            if line.startswith("-") or line.startswith("*"):
                item = line.lstrip("-*").strip()
                if item:
                    items.append(item)
        return items

    def _extract_requirements_from_ai_content_enhanced(
        self,
        content: str,
        sections: dict[str, str],
    ) -> list[Requirement]:
        """Extract requirements from AI-generated content with enhanced parsing.
        
        This method uses improved regex patterns to handle format variations
        and provides better error handling and logging.
        
        Args:
            content: Full AI-generated content
            sections: Extracted sections
            
        Returns:
            List of Requirement objects
        """
        requirements = []
        req_id_counter = 1
        
        # Look for requirements in various sections with enhanced patterns
        req_sections = [
            "requirements",
            "functional requirements", 
            "acceptance criteria",
            "technical requirements",
            "system requirements",
            "business requirements",
        ]
        
        for section_name in req_sections:
            if section_name in sections:
                section_content = sections[section_name]
                logger.debug(f"Processing section '{section_name}' with {len(section_content)} characters")
                
                # Extract requirement blocks using enhanced parsing
                req_blocks = self._split_requirement_blocks_enhanced(section_content)
                logger.debug(f"Found {len(req_blocks)} requirement blocks in section '{section_name}'")
                
                for i, block in enumerate(req_blocks):
                    logger.debug(f"Processing requirement block {i+1}: {block[:100]}...")
                    
                    # Try to extract user story and acceptance criteria with enhanced patterns
                    user_story = self._extract_user_story_enhanced(block)
                    acceptance_criteria = self._extract_acceptance_criteria_enhanced(block)
                    
                    logger.debug(f"Extracted user story: {user_story[:50] if user_story else 'None'}...")
                    logger.debug(f"Extracted {len(acceptance_criteria)} acceptance criteria")
                    
                    # Only add if we have meaningful content
                    if user_story and acceptance_criteria:
                        requirement = Requirement(
                            id=f"FR-{req_id_counter}",
                            user_story=user_story,
                            acceptance_criteria=acceptance_criteria,
                            priority=Priority.MEDIUM,
                        )
                        requirements.append(requirement)
                        req_id_counter += 1
                        logger.debug(f"Added requirement FR-{req_id_counter-1}")
                    elif user_story:
                        # At least we have a user story - create minimal acceptance criteria
                        requirement = Requirement(
                            id=f"FR-{req_id_counter}",
                            user_story=user_story,
                            acceptance_criteria=["WHEN using this feature THEN it SHALL work as expected"],
                            priority=Priority.MEDIUM,
                        )
                        requirements.append(requirement)
                        req_id_counter += 1
                        logger.debug(f"Added requirement FR-{req_id_counter-1} with minimal acceptance criteria")
                    else:
                        logger.warning(f"Skipped requirement block {i+1} - no valid user story or acceptance criteria found")
        
        # If no requirements found in sections, try parsing the entire content
        if not requirements:
            logger.warning("No requirements found in sections, attempting full content parsing")
            requirements = self._extract_requirements_from_full_content(content)
        
        logger.info(f"Total requirements extracted: {len(requirements)}")
        return requirements

    def _extract_requirements_from_ai_content(
        self,
        content: str,
        sections: dict[str, str],
    ) -> list[Requirement]:
        """Extract requirements from AI-generated content.
        
        Legacy method - kept for backward compatibility.
        Use _extract_requirements_from_ai_content_enhanced for new implementations.
        
        Args:
            content: Full AI-generated content
            sections: Extracted sections
            
        Returns:
            List of Requirement objects
        """
        return self._extract_requirements_from_ai_content_enhanced(content, sections)

    def _split_requirement_blocks(self, content: str) -> list[str]:
        """Split content into requirement blocks.
        
        Args:
            content: Section content
            
        Returns:
            List of requirement blocks
        """
        blocks = []
        current_block = []
        
        for line in content.split("\n"):
            line = line.strip()
            
            # New block starts with number or bullet
            if line and (line[0].isdigit() or line.startswith("-") or line.startswith("*")):
                if current_block:
                    blocks.append("\n".join(current_block))
                current_block = [line]
            elif line:
                current_block.append(line)
        
        if current_block:
            blocks.append("\n".join(current_block))
        
        return blocks

    def _split_requirement_blocks_enhanced(self, content: str) -> list[str]:
        """Split content into requirement blocks with enhanced parsing patterns.
        
        This method uses multiple regex patterns to handle format variations
        and provides better error handling.
        
        Args:
            content: Section content
            
        Returns:
            List of requirement blocks
        """
        blocks = []
        
        # Pattern 1: Look for "#### Requirement" or "### Requirement" headers
        requirement_header_pattern = re.compile(
            r'^(#{3,4})\s*requirement\s*\d*[:\s]*.*$',
            re.IGNORECASE | re.MULTILINE
        )
        
        # Split by requirement headers
        parts = requirement_header_pattern.split(content)
        if len(parts) > 1:
            # Reconstruct blocks with headers
            for i in range(1, len(parts), 2):
                if i + 1 < len(parts):
                    header_level = parts[i]
                    block_content = parts[i + 1]
                    # Find the actual header line
                    lines = content.split('\n')
                    for line in lines:
                        if requirement_header_pattern.match(line):
                            full_block = line + '\n' + block_content
                            blocks.append(full_block.strip())
                            break
        
        # Pattern 2: Look for numbered requirements (1., 2., etc.)
        if not blocks:
            numbered_pattern = re.compile(r'^(\d+\.)\s+', re.MULTILINE)
            parts = numbered_pattern.split(content)
            if len(parts) > 1:
                for i in range(1, len(parts), 2):
                    if i + 1 < len(parts):
                        number = parts[i]
                        block_content = parts[i + 1]
                        blocks.append(f"{number} {block_content}".strip())
        
        # Pattern 3: Look for "Requirement N:" patterns
        if not blocks:
            req_colon_pattern = re.compile(
                r'^requirement\s*\d*\s*:.*$',
                re.IGNORECASE | re.MULTILINE
            )
            parts = req_colon_pattern.split(content)
            if len(parts) > 1:
                lines = content.split('\n')
                current_block = []
                for line in lines:
                    if req_colon_pattern.match(line):
                        if current_block:
                            blocks.append('\n'.join(current_block))
                        current_block = [line]
                    elif current_block:
                        current_block.append(line)
                if current_block:
                    blocks.append('\n'.join(current_block))
        
        # Pattern 4: Look for user story patterns as block separators
        if not blocks:
            user_story_pattern = re.compile(
                r'^.*as\s+a\s+.*,\s*i\s+want.*$',
                re.IGNORECASE | re.MULTILINE
            )
            lines = content.split('\n')
            current_block = []
            for line in lines:
                if user_story_pattern.match(line.strip()):
                    if current_block:
                        blocks.append('\n'.join(current_block))
                    current_block = [line]
                elif current_block:
                    current_block.append(line)
                elif line.strip():  # Start new block with non-empty line
                    current_block = [line]
            if current_block:
                blocks.append('\n'.join(current_block))
        
        # Fallback: Use original method
        if not blocks:
            logger.warning("Enhanced parsing failed, falling back to original method")
            return self._split_requirement_blocks_improved(content)
        
        # Filter out empty blocks
        blocks = [block.strip() for block in blocks if block.strip()]
        
        logger.debug(f"Enhanced parsing found {len(blocks)} requirement blocks")
        return blocks

    def _split_requirement_blocks_improved(self, content: str) -> list[str]:
        """Split content into requirement blocks with improved parsing.
        
        This method looks for "#### Requirement" headers to split blocks,
        which is more reliable than looking for numbered items.
        
        Args:
            content: Section content
            
        Returns:
            List of requirement blocks
        """
        blocks = []
        current_block = []
        
        for line in content.split("\n"):
            # Check if this is a requirement header
            if line.strip().startswith("####") and "requirement" in line.lower():
                # Save previous block if it exists
                if current_block:
                    blocks.append("\n".join(current_block))
                # Start new block with this header
                current_block = [line]
            elif current_block:
                # Add line to current block
                current_block.append(line)
        
        # Add the last block
        if current_block:
            blocks.append("\n".join(current_block))
        
        # If no blocks found with headers, fall back to old method
        if not blocks:
            return self._split_requirement_blocks(content)
        
        return blocks

    def _extract_user_story_enhanced(self, block: str) -> str:
        """Extract user story from requirement block with enhanced patterns.
        
        Args:
            block: Requirement block text
            
        Returns:
            User story or empty string
        """
        # Pattern 1: Look for "User Story:" label with various formats
        user_story_patterns = [
            re.compile(r'\*\*user\s+story:\*\*\s*(.*?)(?=\*\*|$)', re.IGNORECASE | re.DOTALL),
            re.compile(r'user\s+story:\s*(.*?)(?=\n\s*\*\*|\n\s*acceptance|\n\s*####|$)', re.IGNORECASE | re.DOTALL),
            re.compile(r'\*\*story:\*\*\s*(.*?)(?=\*\*|$)', re.IGNORECASE | re.DOTALL),
            re.compile(r'story:\s*(.*?)(?=\n\s*\*\*|\n\s*acceptance|\n\s*####|$)', re.IGNORECASE | re.DOTALL),
        ]
        
        for pattern in user_story_patterns:
            match = pattern.search(block)
            if match:
                user_story = match.group(1).strip()
                # Clean up the extracted text
                user_story = re.sub(r'\s+', ' ', user_story)  # Normalize whitespace
                user_story = user_story.strip('*').strip()  # Remove markdown formatting
                if user_story and len(user_story) > 10:  # Ensure it's substantial
                    logger.debug(f"Found user story with pattern: {user_story[:50]}...")
                    return user_story
        
        # Pattern 2: Look for "As a" pattern with enhanced matching
        as_a_patterns = [
            re.compile(r'(as\s+a\s+.*?(?:so\s+that|in\s+order\s+to).*?)(?=\n|$)', re.IGNORECASE | re.DOTALL),
            re.compile(r'(as\s+a\s+.*?)(?=\n\s*\*\*|\n\s*acceptance|\n\s*when|\n\s*if|$)', re.IGNORECASE | re.DOTALL),
        ]
        
        for pattern in as_a_patterns:
            match = pattern.search(block)
            if match:
                user_story = match.group(1).strip()
                # Clean up formatting
                user_story = re.sub(r'^\s*[-*•]\s*', '', user_story)  # Remove bullet points
                user_story = re.sub(r'^\s*\d+\.\s*', '', user_story)  # Remove numbering
                user_story = re.sub(r'\s+', ' ', user_story)  # Normalize whitespace
                user_story = user_story.strip('*').strip()
                if user_story and len(user_story) > 10:
                    logger.debug(f"Found 'As a' pattern: {user_story[:50]}...")
                    return user_story
        
        # Pattern 3: Fallback to any line containing "as a" (legacy method)
        for line in block.split("\n"):
            if "as a" in line.lower():
                cleaned = line.strip().lstrip("-*0123456789. ").lstrip("*").strip()
                if cleaned and len(cleaned) > 10:
                    logger.debug(f"Found fallback user story: {cleaned[:50]}...")
                    return cleaned
        
        logger.debug("No user story found in block")
        return ""

    def _extract_user_story(self, block: str) -> str:
        """Extract user story from requirement block.
        
        Legacy method - kept for backward compatibility.
        Use _extract_user_story_enhanced for new implementations.
        
        Args:
            block: Requirement block text
            
        Returns:
            User story or empty string
        """
        return self._extract_user_story_enhanced(block)

    def _extract_acceptance_criteria_enhanced(self, block: str) -> list[str]:
        """Extract acceptance criteria from requirement block with enhanced patterns.
        
        Args:
            block: Requirement block text
            
        Returns:
            List of acceptance criteria
        """
        criteria = []
        
        # Pattern 1: Look for "Acceptance Criteria:" section with various formats
        criteria_section_patterns = [
            re.compile(r'\*\*acceptance\s+criteria:\*\*\s*(.*?)(?=\*\*|####|$)', re.IGNORECASE | re.DOTALL),
            re.compile(r'acceptance\s+criteria:\s*(.*?)(?=\n\s*\*\*|\n\s*####|$)', re.IGNORECASE | re.DOTALL),
            re.compile(r'\*\*criteria:\*\*\s*(.*?)(?=\*\*|$)', re.IGNORECASE | re.DOTALL),
            re.compile(r'criteria:\s*(.*?)(?=\n\s*\*\*|\n\s*####|$)', re.IGNORECASE | re.DOTALL),
        ]
        
        for pattern in criteria_section_patterns:
            match = pattern.search(block)
            if match:
                criteria_text = match.group(1).strip()
                logger.debug(f"Found criteria section: {criteria_text[:100]}...")
                
                # Extract individual criteria from the section
                section_criteria = self._extract_criteria_from_text(criteria_text)
                if section_criteria:
                    criteria.extend(section_criteria)
                    break
        
        # Pattern 2: Look for EARS patterns anywhere in the block if no section found
        if not criteria:
            logger.debug("No criteria section found, searching for EARS patterns in full block")
            criteria = self._extract_criteria_from_text(block)
        
        # Validate and clean criteria
        validated_criteria = []
        for criterion in criteria:
            if self._is_valid_acceptance_criterion(criterion):
                validated_criteria.append(criterion)
            else:
                logger.debug(f"Rejected invalid criterion: {criterion[:50]}...")
        
        logger.debug(f"Extracted {len(validated_criteria)} valid acceptance criteria")
        return validated_criteria

    def _extract_criteria_from_text(self, text: str) -> list[str]:
        """Extract individual criteria from text using EARS patterns.
        
        Args:
            text: Text to search for criteria
            
        Returns:
            List of criteria strings
        """
        criteria = []
        
        # EARS patterns for acceptance criteria
        ears_patterns = [
            # WHEN ... THEN ... SHALL pattern
            re.compile(r'(when\s+.*?\s+then\s+.*?\s+shall\s+.*?)(?=\n|when\s+|if\s+|where\s+|$)', re.IGNORECASE | re.DOTALL),
            # IF ... THEN ... SHALL pattern  
            re.compile(r'(if\s+.*?\s+then\s+.*?\s+shall\s+.*?)(?=\n|when\s+|if\s+|where\s+|$)', re.IGNORECASE | re.DOTALL),
            # WHERE ... SHALL pattern
            re.compile(r'(where\s+.*?\s+shall\s+.*?)(?=\n|when\s+|if\s+|where\s+|$)', re.IGNORECASE | re.DOTALL),
            # Simple WHEN ... THEN pattern
            re.compile(r'(when\s+.*?\s+then\s+.*?)(?=\n|when\s+|if\s+|where\s+|$)', re.IGNORECASE | re.DOTALL),
            # Simple IF ... THEN pattern
            re.compile(r'(if\s+.*?\s+then\s+.*?)(?=\n|when\s+|if\s+|where\s+|$)', re.IGNORECASE | re.DOTALL),
            # Standalone SHALL pattern
            re.compile(r'([^.]*?\s+shall\s+[^.]*?)(?=\n|when\s+|if\s+|where\s+|$)', re.IGNORECASE | re.DOTALL),
        ]
        
        for pattern in ears_patterns:
            matches = pattern.findall(text)
            for match in matches:
                criterion = match.strip()
                # Clean up the criterion
                criterion = re.sub(r'^\s*[-*•]\s*', '', criterion)  # Remove bullet points
                criterion = re.sub(r'^\s*\d+\.\s*', '', criterion)  # Remove numbering
                criterion = re.sub(r'\s+', ' ', criterion)  # Normalize whitespace
                criterion = criterion.strip()
                
                if criterion and len(criterion) > 10:  # Ensure substantial content
                    criteria.append(criterion)
        
        # Remove duplicates while preserving order
        seen = set()
        unique_criteria = []
        for criterion in criteria:
            criterion_lower = criterion.lower()
            if criterion_lower not in seen:
                seen.add(criterion_lower)
                unique_criteria.append(criterion)
        
        return unique_criteria

    def _is_valid_acceptance_criterion(self, criterion: str) -> bool:
        """Validate if a string is a valid acceptance criterion.
        
        Args:
            criterion: Criterion string to validate
            
        Returns:
            True if valid, False otherwise
        """
        if not criterion or len(criterion.strip()) < 10:
            return False
        
        criterion_lower = criterion.lower()
        
        # Must contain at least one EARS keyword
        ears_keywords = ['when', 'then', 'if', 'where', 'shall']
        has_ears_keyword = any(keyword in criterion_lower for keyword in ears_keywords)
        
        # Should not be just a fragment
        has_substance = len(criterion.split()) >= 5
        
        return has_ears_keyword and has_substance

    def _extract_acceptance_criteria(self, block: str) -> list[str]:
        """Extract acceptance criteria from requirement block.
        
        Legacy method - kept for backward compatibility.
        Use _extract_acceptance_criteria_enhanced for new implementations.
        
        Args:
            block: Requirement block text
            
        Returns:
            List of acceptance criteria
        """
        return self._extract_acceptance_criteria_enhanced(block)

    def _extract_requirements_from_full_content(self, content: str) -> list[Requirement]:
        """Extract requirements from full content when section-based parsing fails.
        
        Args:
            content: Full AI-generated content
            
        Returns:
            List of Requirement objects
        """
        requirements = []
        req_id_counter = 1
        
        # Try to find user stories in the full content
        user_story_pattern = re.compile(
            r'(as\s+a\s+.*?(?:so\s+that|in\s+order\s+to).*?)(?=\n|$)',
            re.IGNORECASE | re.DOTALL
        )
        
        user_stories = user_story_pattern.findall(content)
        
        for user_story in user_stories:
            user_story = user_story.strip()
            if len(user_story) > 10:
                # Try to find acceptance criteria near this user story
                # Look for criteria in the next few lines after the user story
                story_index = content.lower().find(user_story.lower())
                if story_index != -1:
                    # Get text after the user story (next 500 characters)
                    following_text = content[story_index + len(user_story):story_index + len(user_story) + 500]
                    criteria = self._extract_criteria_from_text(following_text)
                    
                    if not criteria:
                        # Create minimal acceptance criteria
                        criteria = ["WHEN using this feature THEN it SHALL work as expected"]
                    
                    requirement = Requirement(
                        id=f"FR-{req_id_counter}",
                        user_story=user_story,
                        acceptance_criteria=criteria,
                        priority=Priority.MEDIUM,
                    )
                    requirements.append(requirement)
                    req_id_counter += 1
        
        return requirements

    def _validate_specification(self, spec: SpecificationDocument) -> tuple[bool, list[str]]:
        """Validate specification completeness and quality.
        
        This method checks that each requirement has a user story and at least
        2 acceptance criteria, as specified in the requirements.
        
        Args:
            spec: Specification document to validate
            
        Returns:
            Tuple of (is_valid, list_of_issues)
        """
        issues = []
        
        # Check minimum number of requirements (should have at least 3)
        req_count = len(spec.functional_requirements)
        if req_count < 3:
            issues.append(f"Specification has only {req_count} requirement(s), should have at least 3")
        
        # Check each requirement
        for i, req in enumerate(spec.functional_requirements, 1):
            req_issues = []
            
            # Check user story presence and quality
            if not req.user_story:
                req_issues.append("missing user story")
            elif len(req.user_story.strip()) < 20:
                req_issues.append("user story too short (less than 20 characters)")
            elif "as a" not in req.user_story.lower():
                req_issues.append("user story doesn't follow 'As a...' format")
            
            # Check acceptance criteria presence and quality
            if not req.acceptance_criteria:
                req_issues.append("missing acceptance criteria")
            elif len(req.acceptance_criteria) < 2:
                req_issues.append(f"only {len(req.acceptance_criteria)} acceptance criterion, should have at least 2")
            else:
                # Check quality of acceptance criteria
                valid_criteria = 0
                for criterion in req.acceptance_criteria:
                    if self._is_valid_acceptance_criterion(criterion):
                        valid_criteria += 1
                
                if valid_criteria < 2:
                    req_issues.append(f"only {valid_criteria} valid acceptance criteria (using EARS format)")
            
            # Add requirement-specific issues
            if req_issues:
                issues.append(f"Requirement {i} ({req.id}): {', '.join(req_issues)}")
        
        # Check introduction quality
        if not spec.introduction or len(spec.introduction.strip()) < 50:
            issues.append("Introduction is missing or too short (less than 50 characters)")
        
        # Check key features
        if not spec.key_features:
            issues.append("No key features identified")
        elif len(spec.key_features) < 2:
            issues.append(f"Only {len(spec.key_features)} key feature(s), should have at least 2")
        
        is_valid = len(issues) == 0
        
        if not is_valid:
            logger.warning(f"Specification validation failed with {len(issues)} issues")
        else:
            logger.info("Specification validation passed")
        
        return is_valid, issues

    def _log_parsing_details(
        self,
        ai_content: str,
        sections: dict[str, str],
        requirements: list[Requirement],
        validation_issues: list[str],
    ) -> None:
        """Log detailed parsing information for debugging.
        
        Args:
            ai_content: Original AI content
            sections: Extracted sections
            requirements: Parsed requirements
            validation_issues: Validation issues found
        """
        logger.info("=== SPECIFICATION PARSING DETAILS ===")
        logger.info(f"AI content length: {len(ai_content)} characters")
        logger.info(f"Sections found: {list(sections.keys())}")
        logger.info(f"Requirements extracted: {len(requirements)}")
        
        for i, req in enumerate(requirements, 1):
            logger.info(f"Requirement {i}:")
            logger.info(f"  ID: {req.id}")
            logger.info(f"  User Story: {req.user_story[:100]}...")
            logger.info(f"  Acceptance Criteria: {len(req.acceptance_criteria)} items")
            for j, criterion in enumerate(req.acceptance_criteria, 1):
                logger.info(f"    {j}. {criterion[:80]}...")
        
        if validation_issues:
            logger.warning("Validation issues:")
            for issue in validation_issues:
                logger.warning(f"  - {issue}")
        
        logger.info("=== END PARSING DETAILS ===")

    def _log_parsing_failure(self, ai_content: str, error_message: str) -> None:
        """Log detailed information about parsing failures.
        
        Args:
            ai_content: Original AI content that failed to parse
            error_message: Error message from the exception
        """
        logger.error("=== SPECIFICATION PARSING FAILURE ===")
        logger.error(f"Error: {error_message}")
        logger.error(f"AI content length: {len(ai_content)} characters")
        logger.error("AI content preview:")
        
        # Log first 500 characters of content
        preview = ai_content[:500]
        for i, line in enumerate(preview.split('\n')[:10], 1):
            logger.error(f"  {i:2d}: {line}")
        
        if len(ai_content) > 500:
            logger.error(f"  ... (truncated, {len(ai_content) - 500} more characters)")
        
        # Try to identify what sections were found
        try:
            sections = self._extract_sections(ai_content)
            logger.error(f"Sections that were extracted: {list(sections.keys())}")
        except Exception as e:
            logger.error(f"Failed to extract sections: {e}")
        
        logger.error("=== END PARSING FAILURE ===")

    # Private helper methods for rule-based generation

    def _generate_introduction_from_analysis(
        self, analysis: SpecificationAnalysis
    ) -> str:
        """Generate introduction from codebase analysis."""
        intro_parts = []

        intro_parts.append(
            f"This document outlines the requirements for {analysis.project_purpose.lower()}."
        )

        if analysis.main_features:
            features_text = ", ".join(analysis.main_features[:3])
            if len(analysis.main_features) > 3:
                features_text += (
                    f", and {len(analysis.main_features) - 3} other features"
                )
            intro_parts.append(f"The system provides {features_text}.")

        if analysis.user_roles:
            roles_text = ", ".join(analysis.user_roles)
            intro_parts.append(f"The primary users are {roles_text}.")

        if analysis.technology_constraints:
            constraints_text = ", ".join(analysis.technology_constraints[:2])
            intro_parts.append(f"The system is built with {constraints_text}.")

        intro_parts.append(
            f"This specification is generated from analysis of the existing codebase with {analysis.confidence_score:.0%} confidence."
        )

        return " ".join(intro_parts)

    def _extract_key_features_from_analysis(
        self, analysis: SpecificationAnalysis
    ) -> list[str]:
        """Extract key features from analysis."""
        features = []

        # Add main features from analysis
        features.extend(analysis.main_features[:5])

        # Add features inferred from functional areas
        for area in analysis.functional_areas[:3]:
            if area not in features:
                features.append(f"{area} functionality")

        # Add features from requirement evidence
        for evidence in analysis.requirement_evidence:
            feature_name = evidence.requirement_type
            if feature_name not in features and len(features) < 8:
                features.append(feature_name)

        return features

    def _generate_requirements_from_evidence(
        self, analysis: SpecificationAnalysis
    ) -> list[Requirement]:
        """Generate functional requirements from analysis evidence."""
        requirements = []
        req_id_counter = 1

        # Generate requirements from evidence
        for evidence in analysis.requirement_evidence:
            user_story = self._generate_user_story_from_evidence(
                evidence, analysis.user_roles
            )
            acceptance_criteria = self._generate_acceptance_criteria_from_evidence(
                evidence
            )

            source_analysis = CodeAnalysisRef(
                file_paths=evidence.supporting_files,
                functions=evidence.supporting_functions,
                confidence_score=evidence.confidence,
            )

            requirement = Requirement(
                id=f"FR-{req_id_counter}",
                user_story=user_story,
                acceptance_criteria=acceptance_criteria,
                priority=self._determine_priority_from_evidence(evidence),
                source_analysis=source_analysis,
            )

            requirements.append(requirement)
            req_id_counter += 1

        # Generate additional requirements from functional areas if needed
        if len(requirements) < 3:
            for area in analysis.functional_areas[:3]:
                if len(requirements) >= 5:
                    break

                user_story = f"As a user, I want to use {area.lower()} features, so that I can accomplish my tasks efficiently"
                acceptance_criteria = [
                    f"WHEN I access {area.lower()} functionality THEN the system SHALL provide appropriate interface",
                    f"WHEN I use {area.lower()} features THEN the system SHALL respond within acceptable time limits",
                ]

                requirement = Requirement(
                    id=f"FR-{req_id_counter}",
                    user_story=user_story,
                    acceptance_criteria=acceptance_criteria,
                    priority=Priority.MEDIUM,
                )

                requirements.append(requirement)
                req_id_counter += 1

        return requirements

    def _generate_introduction_from_user_input(
        self, user_requirements: list[str]
    ) -> str:
        """Generate introduction from user input."""
        if not user_requirements:
            return "This document outlines the requirements for a new software project."

        # Try to infer project purpose from first requirement
        first_req = user_requirements[0].lower()

        if any(keyword in first_req for keyword in ["web", "website", "api"]):
            project_type = "web application"
        elif any(keyword in first_req for keyword in ["cli", "command", "terminal"]):
            project_type = "command-line application"
        elif any(keyword in first_req for keyword in ["data", "analysis", "process"]):
            project_type = "data processing application"
        else:
            project_type = "software application"

        intro = f"This document outlines the requirements for a new {project_type}. "
        intro += (
            f"The system will provide {len(user_requirements)} main functional areas "
        )
        intro += "as specified by the user requirements."

        return intro

    def _extract_key_features_from_user_input(
        self, user_requirements: list[str]
    ) -> list[str]:
        """Extract key features from user input."""
        features = []

        for req in user_requirements[:5]:
            # Extract key nouns and verbs as potential features
            words = re.findall(r"\b[a-zA-Z]{3,}\b", req.lower())
            action_words = [
                w
                for w in words
                if w in ["create", "manage", "process", "handle", "provide", "support"]
            ]
            noun_words = [w for w in words if w not in action_words and len(w) > 3]

            if action_words and noun_words:
                feature = f"{action_words[0].title()} {noun_words[0]}"
                if feature not in features:
                    features.append(feature)

        # If no features extracted, create generic ones
        if not features:
            for i, req in enumerate(user_requirements[:3], 1):
                features.append(f"Feature {i}: {req[:30]}...")

        return features

    def _generate_requirements_from_user_input(
        self, user_requirements: list[str]
    ) -> list[Requirement]:
        """Generate functional requirements from user input."""
        requirements = []

        for i, req_text in enumerate(user_requirements, 1):
            # Convert user requirement to user story format
            user_story = self._convert_to_user_story(req_text)

            # Generate acceptance criteria
            acceptance_criteria = self._generate_acceptance_criteria_from_text(req_text)

            requirement = Requirement(
                id=f"FR-{i}",
                user_story=user_story,
                acceptance_criteria=acceptance_criteria,
                priority=Priority.MEDIUM,
            )

            requirements.append(requirement)

        return requirements

    def _collect_user_requirements(self) -> list[str]:
        """Collect requirements from user through CLI interaction."""
        if not self.cli_interface:
            return ["Basic functionality requirement"]

        requirements = []
        self.cli_interface.display_message(
            "Let's gather your requirements. Enter each requirement (press Enter twice when done):"
        )

        while True:
            req = self.cli_interface.get_user_input(
                f"Requirement {len(requirements) + 1}: "
            ).strip()
            if not req:
                if requirements:
                    break
                else:
                    self.cli_interface.display_message(
                        "Please enter at least one requirement."
                    )
                    continue

            requirements.append(req)

            if len(requirements) >= 10:
                more = self.cli_interface.get_user_input(
                    "You've entered 10 requirements. Add more? (y/n): "
                )
                if more.lower().strip() not in ["y", "yes"]:
                    break

        return requirements

    def _generate_user_story_from_evidence(
        self, evidence: RequirementEvidence, user_roles: list[str]
    ) -> str:
        """Generate user story from requirement evidence."""
        role = user_roles[0] if user_roles else "user"

        # Map evidence types to user story templates
        story_templates = {
            "Data Management": f"As a {role.lower()}, I want to manage data efficiently, so that I can store, retrieve, and modify information as needed",
            "Authentication & Authorization": f"As a {role.lower()}, I want secure access to the system, so that my data and actions are protected",
            "API Operations": f"As a {role.lower()}, I want to interact with the system through APIs, so that I can integrate with other applications",
            "User Interface": f"As a {role.lower()}, I want an intuitive interface, so that I can accomplish tasks efficiently",
        }

        return story_templates.get(
            evidence.requirement_type,
            f"As a {role.lower()}, I want {evidence.requirement_type.lower()} functionality, so that I can accomplish my goals",
        )

    def _generate_acceptance_criteria_from_evidence(
        self, evidence: RequirementEvidence
    ) -> list[str]:
        """Generate acceptance criteria from requirement evidence."""
        criteria = []

        # Base criteria from evidence description
        criteria.append(
            f"WHEN I use the system THEN it SHALL provide {evidence.description.lower()}"
        )

        # Add criteria based on supporting functions
        if evidence.supporting_functions:
            func_names = [func.lower() for func in evidence.supporting_functions[:2]]
            for func_name in func_names:
                if "create" in func_name:
                    criteria.append(
                        "WHEN I create new items THEN the system SHALL validate and store them properly"
                    )
                elif "update" in func_name:
                    criteria.append(
                        "WHEN I update existing items THEN the system SHALL preserve data integrity"
                    )
                elif "delete" in func_name:
                    criteria.append(
                        "WHEN I delete items THEN the system SHALL confirm the action and clean up properly"
                    )
                elif "get" in func_name or "read" in func_name:
                    criteria.append(
                        "WHEN I retrieve items THEN the system SHALL return accurate and current data"
                    )

        # Ensure at least 2 criteria
        if len(criteria) < 2:
            criteria.append(
                "WHEN I interact with this functionality THEN the system SHALL respond within acceptable time limits"
            )

        return criteria

    def _convert_to_user_story(self, requirement_text: str) -> str:
        """Convert requirement text to user story format."""
        # Check if already in user story format
        if requirement_text.lower().startswith("as a"):
            return requirement_text

        # Extract key action and object from requirement
        words = requirement_text.lower().split()

        # Look for action verbs
        action_verbs = [
            "create",
            "manage",
            "process",
            "handle",
            "provide",
            "support",
            "allow",
            "enable",
        ]
        action = next((word for word in words if word in action_verbs), "use")

        # Create user story
        return f"As a user, I want to {action} {requirement_text.lower()}, so that I can accomplish my goals efficiently"

    def _generate_acceptance_criteria_from_text(
        self, requirement_text: str
    ) -> list[str]:
        """Generate acceptance criteria from requirement text."""
        criteria = []

        # Extract key words for criteria generation
        words = requirement_text.lower().split()

        # Generate basic criteria
        criteria.append(
            f"WHEN I use this feature THEN the system SHALL {requirement_text.lower()}"
        )
        criteria.append(
            "WHEN I interact with this functionality THEN the system SHALL respond appropriately"
        )

        # Add specific criteria based on keywords
        if any(word in words for word in ["create", "add", "new"]):
            criteria.append(
                "WHEN I create new items THEN the system SHALL validate input and provide confirmation"
            )

        if any(word in words for word in ["update", "modify", "edit"]):
            criteria.append(
                "WHEN I modify existing items THEN the system SHALL preserve data integrity"
            )

        if any(word in words for word in ["delete", "remove"]):
            criteria.append(
                "WHEN I delete items THEN the system SHALL request confirmation and handle cleanup"
            )

        if any(word in words for word in ["search", "find", "query"]):
            criteria.append(
                "WHEN I search for items THEN the system SHALL return relevant results quickly"
            )

        return criteria[:3]  # Limit to 3 criteria

    def _determine_priority_from_evidence(
        self, evidence: RequirementEvidence
    ) -> Priority:
        """Determine priority based on evidence confidence and type."""
        if evidence.confidence >= 0.8:
            return Priority.HIGH
        elif evidence.confidence >= 0.6:
            return Priority.MEDIUM
        else:
            return Priority.LOW

    def _parse_feedback(self, feedback: str) -> dict[str, Any]:
        """Parse user feedback to understand requested changes."""
        feedback_lower = feedback.lower()
        refinements = {
            "add_requirements": [],
            "modify_requirements": [],
            "remove_requirements": [],
            "change_introduction": None,
            "add_features": [],
            "remove_features": [],
        }

        # Simple keyword-based parsing
        if "add" in feedback_lower and "requirement" in feedback_lower:
            # Extract requirements to add (simplified)
            refinements["add_requirements"] = [
                "Additional requirement based on feedback"
            ]

        if "remove" in feedback_lower:
            refinements["remove_requirements"] = ["Remove low priority items"]

        if "introduction" in feedback_lower or "intro" in feedback_lower:
            refinements["change_introduction"] = feedback

        return refinements

    def _apply_refinements(
        self, spec: SpecificationDocument, refinements: dict[str, Any]
    ) -> SpecificationDocument:
        """Apply refinements to specification document."""
        # Create a copy of the specification
        refined_spec = SpecificationDocument(
            introduction=spec.introduction,
            key_features=spec.key_features.copy(),
            functional_requirements=spec.functional_requirements.copy(),
            source=spec.source,
            version=spec.version,
            approved=False,
        )

        # Apply introduction changes
        if refinements["change_introduction"]:
            refined_spec.introduction = (
                f"{spec.introduction} {refinements['change_introduction']}"
            )

        # Add new requirements
        for new_req_text in refinements["add_requirements"]:
            req_id = f"FR-{len(refined_spec.functional_requirements) + 1}"
            new_req = Requirement(
                id=req_id,
                user_story=self._convert_to_user_story(new_req_text),
                acceptance_criteria=self._generate_acceptance_criteria_from_text(
                    new_req_text
                ),
                priority=Priority.MEDIUM,
            )
            refined_spec.functional_requirements.append(new_req)

        # Remove requirements (simplified - remove last one)
        if refinements["remove_requirements"] and refined_spec.functional_requirements:
            refined_spec.functional_requirements.pop()

        return refined_spec

    def _increment_version(self, version: str) -> str:
        """Increment version number."""
        try:
            parts = version.split(".")
            if len(parts) >= 2:
                minor = int(parts[1]) + 1
                return f"{parts[0]}.{minor}"
            else:
                major = int(parts[0])
                return f"{major}.1"
        except (ValueError, IndexError):
            return "1.1"
