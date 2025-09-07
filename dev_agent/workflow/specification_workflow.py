"""Workflow integration for specification generation phase."""

from typing import Optional
from ..generation.specification_generator import SpecificationGenerator
from ..interfaces.cli_interface import ICLIInterface
from ..interfaces.analysis_interface import ICodebaseAnalyzer
from ..models.documents import SpecificationDocument
from ..models.analysis import SpecificationAnalysis
from ..models.enums import SpecificationSource
from ..state.state_manager import StateManager


class SpecificationWorkflow:
    """Manages the specification generation workflow phase."""
    
    def __init__(
        self,
        cli_interface: ICLIInterface,
        codebase_analyzer: Optional[ICodebaseAnalyzer] = None,
        state_manager: Optional[StateManager] = None
    ):
        """Initialize the specification workflow.
        
        Args:
            cli_interface: CLI interface for user interaction
            codebase_analyzer: Optional codebase analyzer for existing projects
            state_manager: Optional state manager for persistence
        """
        self.cli_interface = cli_interface
        self.codebase_analyzer = codebase_analyzer
        self.state_manager = state_manager
        self.generator = SpecificationGenerator(cli_interface)
    
    def execute_specification_phase(self, project_path: str) -> SpecificationDocument:
        """Execute the specification generation phase.
        
        Args:
            project_path: Path to the project directory
            
        Returns:
            Approved specification document
        """
        self.cli_interface.display_message("Starting specification generation phase...")
        
        # Determine if this is an existing codebase or new project
        if self.codebase_analyzer and self._has_existing_code(project_path):
            spec = self._generate_from_existing_code()
        else:
            spec = self._generate_from_user_input()
        
        # Request approval and handle refinements
        spec = self._approval_workflow(spec)
        
        # Save the specification
        if self.state_manager:
            self._save_specification(spec)
        
        self.cli_interface.display_message("Specification phase completed successfully!")
        return spec
    
    def _generate_from_existing_code(self) -> SpecificationDocument:
        """Generate specification from existing codebase analysis."""
        self.cli_interface.display_message("Analyzing existing codebase...")
        
        # Perform codebase analysis
        analysis = self.codebase_analyzer.analyze_for_specification()
        
        self.cli_interface.display_message(
            f"Analysis complete with {analysis.confidence_score:.0%} confidence. "
            f"Found {len(analysis.main_features)} main features and "
            f"{len(analysis.requirement_evidence)} requirement areas."
        )
        
        # Generate specification from analysis
        spec = self.generator.generate_from_existing_code(analysis)
        
        return spec
    
    def _generate_from_user_input(self) -> SpecificationDocument:
        """Generate specification from user input."""
        self.cli_interface.display_message("No existing codebase detected. Let's create a specification from your requirements.")
        
        # Generate specification from user input (will prompt user)
        spec = self.generator.generate_from_user_input([])
        
        return spec
    
    def _approval_workflow(self, spec: SpecificationDocument) -> SpecificationDocument:
        """Handle the approval workflow with potential refinements.
        
        Args:
            spec: Initial specification document
            
        Returns:
            Final approved specification document
        """
        current_spec = spec
        max_iterations = 3
        iteration = 0
        
        while iteration < max_iterations:
            iteration += 1
            
            # Request user approval
            approved = self.generator.request_user_approval(current_spec)
            
            if approved:
                self.cli_interface.display_message("Specification approved!")
                return current_spec
            
            # Get feedback for refinement
            if iteration < max_iterations:
                feedback = self.cli_interface.get_user_input(
                    "Please provide feedback for improving the specification: "
                )
                
                if feedback.strip():
                    self.cli_interface.display_message("Refining specification based on your feedback...")
                    current_spec = self.generator.refine_specification(current_spec, feedback)
                else:
                    self.cli_interface.display_message("No feedback provided. Using current specification.")
                    current_spec.approved = True
                    return current_spec
            else:
                self.cli_interface.display_message(
                    "Maximum refinement iterations reached. Using current specification."
                )
                current_spec.approved = True
                return current_spec
        
        return current_spec
    
    def _has_existing_code(self, project_path: str) -> bool:
        """Check if the project has existing code to analyze.
        
        Args:
            project_path: Path to the project directory
            
        Returns:
            True if existing code is found, False otherwise
        """
        import os
        from pathlib import Path
        
        project_dir = Path(project_path)
        
        # Look for common code file extensions
        code_extensions = {'.py', '.js', '.ts', '.java', '.cpp', '.c', '.cs', '.rb', '.go', '.rs'}
        
        for file_path in project_dir.rglob('*'):
            if file_path.is_file() and file_path.suffix.lower() in code_extensions:
                # Skip common non-source directories
                if any(part.startswith('.') or part in ['node_modules', '__pycache__', 'build', 'dist'] 
                       for part in file_path.parts):
                    continue
                return True
        
        return False
    
    def _save_specification(self, spec: SpecificationDocument) -> None:
        """Save the specification document.
        
        Args:
            spec: Specification document to save
        """
        try:
            # Format the specification as markdown
            formatted_spec = self.generator.format_specification_document(spec)
            
            # Save using state manager
            self.state_manager.save_document(formatted_spec, "specification")
            
            self.cli_interface.display_message("Specification saved to SPECIFICATION.md")
            
        except Exception as e:
            self.cli_interface.display_message(f"Warning: Could not save specification: {e}")


class SpecificationWorkflowResult:
    """Result of specification workflow execution."""
    
    def __init__(
        self,
        specification: SpecificationDocument,
        success: bool,
        message: str = ""
    ):
        """Initialize the result.
        
        Args:
            specification: Generated specification document
            success: Whether the workflow completed successfully
            message: Optional message about the result
        """
        self.specification = specification
        self.success = success
        self.message = message