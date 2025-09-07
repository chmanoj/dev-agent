"""Specification generator for creating SPECIFICATION.md documents."""

import re
from datetime import datetime
from typing import List, Dict, Any, Optional
from pathlib import Path

from ..interfaces.generation_interface import ISpecificationGenerator
from ..interfaces.cli_interface import ICLIInterface
from ..models.documents import (
    SpecificationDocument, Requirement, CodeAnalysisRef
)
from ..models.analysis import SpecificationAnalysis, RequirementEvidence
from ..models.enums import Priority, SpecificationSource


class SpecificationGenerator(ISpecificationGenerator):
    """Generates specification documents from codebase analysis or user input."""
    
    def __init__(self, cli_interface: Optional[ICLIInterface] = None):
        """Initialize the specification generator.
        
        Args:
            cli_interface: Optional CLI interface for user interaction
        """
        self.cli_interface = cli_interface
        self.version = "1.0"
    
    def generate_from_existing_code(self, analysis: SpecificationAnalysis) -> SpecificationDocument:
        """Generate specification from existing codebase analysis.
        
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
            approved=False
        )
    
    def generate_from_user_input(self, user_requirements: List[str]) -> SpecificationDocument:
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
        functional_requirements = self._generate_requirements_from_user_input(user_requirements)
        
        return SpecificationDocument(
            introduction=introduction,
            key_features=key_features,
            functional_requirements=functional_requirements,
            source=SpecificationSource.USER_INPUT,
            version=self.version,
            approved=False
        )
    
    def refine_specification(self, spec: SpecificationDocument, feedback: str) -> SpecificationDocument:
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
                lines.append(f"- **Files:** {', '.join(req.source_analysis.file_paths[:3])}")
                if len(req.source_analysis.file_paths) > 3:
                    lines.append(f"  (and {len(req.source_analysis.file_paths) - 3} more)")
                lines.append(f"- **Functions:** {', '.join(req.source_analysis.functions[:3])}")
                if len(req.source_analysis.functions) > 3:
                    lines.append(f"  (and {len(req.source_analysis.functions) - 3} more)")
                lines.append(f"- **Confidence:** {req.source_analysis.confidence_score:.1%}")
            
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
            lines.append(f"- **Approved:** {spec.approval_timestamp.strftime('%Y-%m-%d %H:%M:%S')}")
        
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
    
    # Private helper methods
    
    def _generate_introduction_from_analysis(self, analysis: SpecificationAnalysis) -> str:
        """Generate introduction from codebase analysis."""
        intro_parts = []
        
        intro_parts.append(f"This document outlines the requirements for {analysis.project_purpose.lower()}.")
        
        if analysis.main_features:
            features_text = ", ".join(analysis.main_features[:3])
            if len(analysis.main_features) > 3:
                features_text += f", and {len(analysis.main_features) - 3} other features"
            intro_parts.append(f"The system provides {features_text}.")
        
        if analysis.user_roles:
            roles_text = ", ".join(analysis.user_roles)
            intro_parts.append(f"The primary users are {roles_text}.")
        
        if analysis.technology_constraints:
            constraints_text = ", ".join(analysis.technology_constraints[:2])
            intro_parts.append(f"The system is built with {constraints_text}.")
        
        intro_parts.append(f"This specification is generated from analysis of the existing codebase with {analysis.confidence_score:.0%} confidence.")
        
        return " ".join(intro_parts)
    
    def _extract_key_features_from_analysis(self, analysis: SpecificationAnalysis) -> List[str]:
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
    
    def _generate_requirements_from_evidence(self, analysis: SpecificationAnalysis) -> List[Requirement]:
        """Generate functional requirements from analysis evidence."""
        requirements = []
        req_id_counter = 1
        
        # Generate requirements from evidence
        for evidence in analysis.requirement_evidence:
            user_story = self._generate_user_story_from_evidence(evidence, analysis.user_roles)
            acceptance_criteria = self._generate_acceptance_criteria_from_evidence(evidence)
            
            source_analysis = CodeAnalysisRef(
                file_paths=evidence.supporting_files,
                functions=evidence.supporting_functions,
                confidence_score=evidence.confidence
            )
            
            requirement = Requirement(
                id=f"FR-{req_id_counter}",
                user_story=user_story,
                acceptance_criteria=acceptance_criteria,
                priority=self._determine_priority_from_evidence(evidence),
                source_analysis=source_analysis
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
                    f"WHEN I use {area.lower()} features THEN the system SHALL respond within acceptable time limits"
                ]
                
                requirement = Requirement(
                    id=f"FR-{req_id_counter}",
                    user_story=user_story,
                    acceptance_criteria=acceptance_criteria,
                    priority=Priority.MEDIUM
                )
                
                requirements.append(requirement)
                req_id_counter += 1
        
        return requirements
    
    def _generate_introduction_from_user_input(self, user_requirements: List[str]) -> str:
        """Generate introduction from user input."""
        if not user_requirements:
            return "This document outlines the requirements for a new software project."
        
        # Try to infer project purpose from first requirement
        first_req = user_requirements[0].lower()
        
        if any(keyword in first_req for keyword in ['web', 'website', 'api']):
            project_type = "web application"
        elif any(keyword in first_req for keyword in ['cli', 'command', 'terminal']):
            project_type = "command-line application"
        elif any(keyword in first_req for keyword in ['data', 'analysis', 'process']):
            project_type = "data processing application"
        else:
            project_type = "software application"
        
        intro = f"This document outlines the requirements for a new {project_type}. "
        intro += f"The system will provide {len(user_requirements)} main functional areas "
        intro += "as specified by the user requirements."
        
        return intro
    
    def _extract_key_features_from_user_input(self, user_requirements: List[str]) -> List[str]:
        """Extract key features from user input."""
        features = []
        
        for req in user_requirements[:5]:
            # Extract key nouns and verbs as potential features
            words = re.findall(r'\b[a-zA-Z]{3,}\b', req.lower())
            action_words = [w for w in words if w in ['create', 'manage', 'process', 'handle', 'provide', 'support']]
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
    
    def _generate_requirements_from_user_input(self, user_requirements: List[str]) -> List[Requirement]:
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
                priority=Priority.MEDIUM
            )
            
            requirements.append(requirement)
        
        return requirements
    
    def _collect_user_requirements(self) -> List[str]:
        """Collect requirements from user through CLI interaction."""
        if not self.cli_interface:
            return ["Basic functionality requirement"]
        
        requirements = []
        self.cli_interface.display_message("Let's gather your requirements. Enter each requirement (press Enter twice when done):")
        
        while True:
            req = self.cli_interface.get_user_input(f"Requirement {len(requirements) + 1}: ").strip()
            if not req:
                if requirements:
                    break
                else:
                    self.cli_interface.display_message("Please enter at least one requirement.")
                    continue
            
            requirements.append(req)
            
            if len(requirements) >= 10:
                more = self.cli_interface.get_user_input("You've entered 10 requirements. Add more? (y/n): ")
                if more.lower().strip() not in ['y', 'yes']:
                    break
        
        return requirements
    
    def _generate_user_story_from_evidence(self, evidence: RequirementEvidence, user_roles: List[str]) -> str:
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
            f"As a {role.lower()}, I want {evidence.requirement_type.lower()} functionality, so that I can accomplish my goals"
        )
    
    def _generate_acceptance_criteria_from_evidence(self, evidence: RequirementEvidence) -> List[str]:
        """Generate acceptance criteria from requirement evidence."""
        criteria = []
        
        # Base criteria from evidence description
        criteria.append(f"WHEN I use the system THEN it SHALL provide {evidence.description.lower()}")
        
        # Add criteria based on supporting functions
        if evidence.supporting_functions:
            func_names = [func.lower() for func in evidence.supporting_functions[:2]]
            for func_name in func_names:
                if 'create' in func_name:
                    criteria.append("WHEN I create new items THEN the system SHALL validate and store them properly")
                elif 'update' in func_name:
                    criteria.append("WHEN I update existing items THEN the system SHALL preserve data integrity")
                elif 'delete' in func_name:
                    criteria.append("WHEN I delete items THEN the system SHALL confirm the action and clean up properly")
                elif 'get' in func_name or 'read' in func_name:
                    criteria.append("WHEN I retrieve items THEN the system SHALL return accurate and current data")
        
        # Ensure at least 2 criteria
        if len(criteria) < 2:
            criteria.append("WHEN I interact with this functionality THEN the system SHALL respond within acceptable time limits")
        
        return criteria
    
    def _convert_to_user_story(self, requirement_text: str) -> str:
        """Convert requirement text to user story format."""
        # Check if already in user story format
        if requirement_text.lower().startswith("as a"):
            return requirement_text
        
        # Extract key action and object from requirement
        words = requirement_text.lower().split()
        
        # Look for action verbs
        action_verbs = ['create', 'manage', 'process', 'handle', 'provide', 'support', 'allow', 'enable']
        action = next((word for word in words if word in action_verbs), 'use')
        
        # Create user story
        return f"As a user, I want to {action} {requirement_text.lower()}, so that I can accomplish my goals efficiently"
    
    def _generate_acceptance_criteria_from_text(self, requirement_text: str) -> List[str]:
        """Generate acceptance criteria from requirement text."""
        criteria = []
        
        # Extract key words for criteria generation
        words = requirement_text.lower().split()
        
        # Generate basic criteria
        criteria.append(f"WHEN I use this feature THEN the system SHALL {requirement_text.lower()}")
        criteria.append("WHEN I interact with this functionality THEN the system SHALL respond appropriately")
        
        # Add specific criteria based on keywords
        if any(word in words for word in ['create', 'add', 'new']):
            criteria.append("WHEN I create new items THEN the system SHALL validate input and provide confirmation")
        
        if any(word in words for word in ['update', 'modify', 'edit']):
            criteria.append("WHEN I modify existing items THEN the system SHALL preserve data integrity")
        
        if any(word in words for word in ['delete', 'remove']):
            criteria.append("WHEN I delete items THEN the system SHALL request confirmation and handle cleanup")
        
        if any(word in words for word in ['search', 'find', 'query']):
            criteria.append("WHEN I search for items THEN the system SHALL return relevant results quickly")
        
        return criteria[:3]  # Limit to 3 criteria
    
    def _determine_priority_from_evidence(self, evidence: RequirementEvidence) -> Priority:
        """Determine priority based on evidence confidence and type."""
        if evidence.confidence >= 0.8:
            return Priority.HIGH
        elif evidence.confidence >= 0.6:
            return Priority.MEDIUM
        else:
            return Priority.LOW
    
    def _parse_feedback(self, feedback: str) -> Dict[str, Any]:
        """Parse user feedback to understand requested changes."""
        feedback_lower = feedback.lower()
        refinements = {
            'add_requirements': [],
            'modify_requirements': [],
            'remove_requirements': [],
            'change_introduction': None,
            'add_features': [],
            'remove_features': []
        }
        
        # Simple keyword-based parsing
        if 'add' in feedback_lower and 'requirement' in feedback_lower:
            # Extract requirements to add (simplified)
            refinements['add_requirements'] = ['Additional requirement based on feedback']
        
        if 'remove' in feedback_lower:
            refinements['remove_requirements'] = ['Remove low priority items']
        
        if 'introduction' in feedback_lower or 'intro' in feedback_lower:
            refinements['change_introduction'] = feedback
        
        return refinements
    
    def _apply_refinements(self, spec: SpecificationDocument, refinements: Dict[str, Any]) -> SpecificationDocument:
        """Apply refinements to specification document."""
        # Create a copy of the specification
        refined_spec = SpecificationDocument(
            introduction=spec.introduction,
            key_features=spec.key_features.copy(),
            functional_requirements=spec.functional_requirements.copy(),
            source=spec.source,
            version=spec.version,
            approved=False
        )
        
        # Apply introduction changes
        if refinements['change_introduction']:
            refined_spec.introduction = f"{spec.introduction} {refinements['change_introduction']}"
        
        # Add new requirements
        for new_req_text in refinements['add_requirements']:
            req_id = f"FR-{len(refined_spec.functional_requirements) + 1}"
            new_req = Requirement(
                id=req_id,
                user_story=self._convert_to_user_story(new_req_text),
                acceptance_criteria=self._generate_acceptance_criteria_from_text(new_req_text),
                priority=Priority.MEDIUM
            )
            refined_spec.functional_requirements.append(new_req)
        
        # Remove requirements (simplified - remove last one)
        if refinements['remove_requirements'] and refined_spec.functional_requirements:
            refined_spec.functional_requirements.pop()
        
        return refined_spec
    
    def _increment_version(self, version: str) -> str:
        """Increment version number."""
        try:
            parts = version.split('.')
            if len(parts) >= 2:
                minor = int(parts[1]) + 1
                return f"{parts[0]}.{minor}"
            else:
                major = int(parts[0])
                return f"{major}.1"
        except (ValueError, IndexError):
            return "1.1"