"""AI-powered design generator using Azure OpenAI."""

from __future__ import annotations

import logging
from typing import Optional

from dev_agent.config.config_manager import DevAgentConfig
from dev_agent.interfaces.generation_interface import IDesignGenerator
from dev_agent.models.analysis import DesignAnalysis
from dev_agent.models.documents import DesignDocument, SpecificationDocument
from dev_agent.services.azure_openai_service import AzureOpenAIService, ChatMessage
from dev_agent.errors.exceptions import GenerationError

logger = logging.getLogger(__name__)


class AIDesignGenerator(IDesignGenerator):
    """AI-powered design generator using Azure OpenAI."""
    
    def __init__(self, config: DevAgentConfig):
        """Initialize AI design generator.
        
        Args:
            config: Dev agent configuration
        """
        self.config = config
        self.ai_service = AzureOpenAIService(config.azure_openai)
        self.version = "1.0"
    
    def generate_from_specification(
        self, spec: SpecificationDocument, analysis: DesignAnalysis
    ) -> DesignDocument:
        """Generate design document from specification using AI.
        
        Args:
            spec: Specification document
            analysis: Design analysis results
            
        Returns:
            Generated design document
            
        Raises:
            GenerationError: If design generation fails
        """
        try:
            logger.info("Generating design document from specification using Azure OpenAI")
            
            # Create system prompt for design generation
            system_prompt = self._create_system_prompt_for_design()
            
            # Create user prompt with specification and analysis
            user_prompt = self._create_design_prompt(spec, analysis)
            
            messages = [
                ChatMessage(role="system", content=system_prompt),
                ChatMessage(role="user", content=user_prompt),
            ]
            
            # Generate design using AI
            response = self.ai_service.chat_completion(
                messages=messages,
                temperature=0.2,  # Balanced temperature for structured creativity
                max_tokens=4000,
            )
            
            # Parse AI response into design document
            design_doc = self._parse_ai_response_to_design(response.content, spec, analysis)
            
            logger.info("Successfully generated design document from specification")
            return design_doc
            
        except Exception as e:
            logger.error(f"Failed to generate design from specification: {e}")
            raise GenerationError(f"Design generation failed: {e}") from e
    
    def refine_design(self, design: DesignDocument, feedback: str) -> DesignDocument:
        """Refine design based on user feedback using AI.
        
        Args:
            design: Current design document
            feedback: User feedback for refinement
            
        Returns:
            Refined design document
            
        Raises:
            GenerationError: If design refinement fails
        """
        try:
            logger.info("Refining design document based on user feedback using Azure OpenAI")
            
            # Create system prompt for refinement
            system_prompt = self._create_system_prompt_for_refinement()
            
            # Create user prompt with current design and feedback
            user_prompt = self._create_refinement_prompt(design, feedback)
            
            messages = [
                ChatMessage(role="system", content=system_prompt),
                ChatMessage(role="user", content=user_prompt),
            ]
            
            # Refine design using AI
            response = self.ai_service.chat_completion(
                messages=messages,
                temperature=0.1,  # Low temperature for consistent refinement
                max_tokens=4000,
            )
            
            # Parse AI response into refined design
            refined_design = self._parse_ai_response_to_design(
                response.content, base_design=design
            )
            
            logger.info("Successfully refined design document based on feedback")
            return refined_design
            
        except Exception as e:
            logger.error(f"Failed to refine design: {e}")
            raise GenerationError(f"Design refinement failed: {e}") from e
    
    def _create_system_prompt_for_design(self) -> str:
        """Create system prompt for design generation."""
        return """You are an expert software architect and system designer. Your task is to generate a comprehensive technical design document based on a software specification and codebase analysis.

Key requirements:
1. Create a detailed technical design that implements the specification
2. Consider existing codebase patterns and architecture
3. Use proper software architecture principles (SOLID, DRY, etc.)
4. Include system architecture, component design, and data models
5. Specify APIs, interfaces, and integration points
6. Consider scalability, performance, and security
7. Provide implementation guidance and best practices

Output format should be structured markdown with:
- System Architecture Overview
- Component Design
- Data Models and Database Design
- API Design and Interfaces
- Security Considerations
- Performance and Scalability
- Implementation Guidelines
- Testing Strategy

Be specific and actionable, providing concrete technical decisions and rationale."""
    
    def _create_system_prompt_for_refinement(self) -> str:
        """Create system prompt for design refinement."""
        return """You are an expert software architect and system designer. Your task is to refine an existing technical design document based on user feedback.

Key requirements:
1. Carefully analyze the provided feedback
2. Update the design to address all feedback points
3. Maintain architectural consistency and best practices
4. Preserve existing design elements that don't conflict with feedback
5. Ensure all changes are well-integrated and documented
6. Update related sections and dependencies as needed
7. Maintain professional technical documentation standards

Focus on:
- Addressing specific technical concerns
- Improving design clarity and completeness
- Ensuring architectural soundness
- Maintaining design coherence and consistency

Provide the complete refined design document."""
    
    def _create_design_prompt(
        self, spec: SpecificationDocument, analysis: DesignAnalysis
    ) -> str:
        """Create user prompt with specification and analysis data."""
        prompt_parts = [
            "Please generate a comprehensive technical design document based on the following specification and codebase analysis:",
            "",
            "## Specification Summary",
            f"**Title:** {spec.title}",
            f"**Introduction:** {spec.introduction}",
            "",
        ]
        
        if spec.key_features:
            prompt_parts.extend([
                "**Key Features:**",
                *[f"- {feature}" for feature in spec.key_features],
                "",
            ])
        
        if spec.functional_requirements:
            prompt_parts.extend([
                "**Functional Requirements:**",
            ])
            for req in spec.functional_requirements[:5]:  # Limit to avoid token overflow
                prompt_parts.extend([
                    f"- {req.id}: {req.user_story}",
                ])
            prompt_parts.append("")
        
        # Add analysis data
        prompt_parts.extend([
            "## Codebase Analysis",
            f"**Architecture Style:** {analysis.architecture_style}",
            f"**Technology Stack:** {', '.join(analysis.technology_stack)}",
            "",
        ])
        
        if analysis.existing_components:
            prompt_parts.extend([
                "**Existing Components:**",
                *[f"- {comp}" for comp in analysis.existing_components[:10]],
                "",
            ])
        
        if analysis.data_models:
            prompt_parts.extend([
                "**Existing Data Models:**",
                *[f"- {model}" for model in analysis.data_models[:10]],
                "",
            ])
        
        if analysis.integration_points:
            prompt_parts.extend([
                "**Integration Points:**",
                *[f"- {point}" for point in analysis.integration_points[:5]],
                "",
            ])
        
        prompt_parts.extend([
            "Generate a complete, detailed technical design document that:",
            "1. Implements all specification requirements",
            "2. Integrates with existing codebase architecture",
            "3. Follows established patterns and conventions",
            "4. Provides clear implementation guidance",
        ])
        
        return "\n".join(prompt_parts)
    
    def _create_refinement_prompt(self, design: DesignDocument, feedback: str) -> str:
        """Create user prompt for design refinement."""
        current_design = self._format_design_for_prompt(design)
        
        prompt_parts = [
            "Please refine the following technical design document based on the provided feedback:",
            "",
            "**Current Design:**",
            current_design,
            "",
            "**User Feedback:**",
            feedback,
            "",
            "Please provide the complete refined design document that addresses all feedback points.",
        ]
        
        return "\n".join(prompt_parts)
    
    def _format_design_for_prompt(self, design: DesignDocument) -> str:
        """Format design document for use in prompts."""
        parts = [
            f"# {design.title}",
            "",
            f"**Version:** {design.version}",
            f"**Created:** {design.created_at}",
            "",
            "## Overview",
            design.overview,
            "",
        ]
        
        if design.system_architecture:
            parts.extend([
                "## System Architecture",
                design.system_architecture,
                "",
            ])
        
        if design.component_design:
            parts.extend([
                "## Component Design",
                design.component_design,
                "",
            ])
        
        if design.data_models:
            parts.extend([
                "## Data Models",
                design.data_models,
                "",
            ])
        
        if design.api_design:
            parts.extend([
                "## API Design",
                design.api_design,
                "",
            ])
        
        return "\n".join(parts)
    
    def _parse_ai_response_to_design(
        self,
        ai_response: str,
        spec: Optional[SpecificationDocument] = None,
        analysis: Optional[DesignAnalysis] = None,
        base_design: Optional[DesignDocument] = None,
    ) -> DesignDocument:
        """Parse AI response into a design document.
        
        This is a simplified parser. In a production system, you might want
        to use more sophisticated parsing or ask the AI to return structured JSON.
        """
        from datetime import datetime
        
        # Extract title (look for first # heading)
        lines = ai_response.split('\n')
        title = spec.title + " - Technical Design" if spec else "Technical Design"
        for line in lines:
            if line.startswith('# '):
                title = line[2:].strip()
                break
        
        # Extract sections by looking for ## headings
        sections = {}
        current_section = None
        current_content = []
        
        for line in lines:
            if line.startswith('## '):
                if current_section:
                    sections[current_section] = '\n'.join(current_content).strip()
                current_section = line[3:].strip().lower()
                current_content = []
            elif current_section:
                current_content.append(line)
        
        # Add the last section
        if current_section and current_content:
            sections[current_section] = '\n'.join(current_content).strip()
        
        # Extract specific sections
        overview = sections.get('overview', sections.get('system architecture overview', 
                                'This design document was generated using AI analysis.'))
        system_architecture = sections.get('system architecture', sections.get('architecture', ''))
        component_design = sections.get('component design', sections.get('components', ''))
        data_models = sections.get('data models', sections.get('data models and database design', ''))
        api_design = sections.get('api design', sections.get('api design and interfaces', ''))
        security_considerations = sections.get('security considerations', sections.get('security', ''))
        performance_considerations = sections.get('performance and scalability', sections.get('performance', ''))
        implementation_guidelines = sections.get('implementation guidelines', sections.get('implementation', ''))
        testing_strategy = sections.get('testing strategy', sections.get('testing', ''))
        
        return DesignDocument(
            title=title,
            version=base_design.version if base_design else "1.0",
            created_at=base_design.created_at if base_design else datetime.now(),
            specification_reference=spec.title if spec else "",
            overview=overview,
            system_architecture=system_architecture,
            component_design=component_design,
            data_models=data_models,
            api_design=api_design,
            security_considerations=security_considerations,
            performance_considerations=performance_considerations,
            implementation_guidelines=implementation_guidelines,
            testing_strategy=testing_strategy,
            diagrams=[],
            appendices=[],
        )