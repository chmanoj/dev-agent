"""Workflow orchestration system that coordinates all four phases."""

import uuid
from datetime import datetime
from typing import Optional, Dict, Any
from pathlib import Path

from ..interfaces.workflow_interface import IWorkflowManager
from ..interfaces.cli_interface import ICLIInterface
from ..models.enums import PhaseType, PhaseStatus
from ..models.project_state import ProjectState, SessionData
from ..models.results import PhaseResult
from ..models.context import ProjectContext
from ..state.state_manager import StateManager
from .phase_manager import PhaseManager


class WorkflowManager(IWorkflowManager):
    """Orchestrates the complete four-phase development workflow."""
    
    def __init__(self, cli_interface: ICLIInterface):
        """Initialize the workflow manager.
        
        Args:
            cli_interface: CLI interface for user interaction
        """
        self.cli_interface = cli_interface
        self.state_manager: Optional[StateManager] = None
        self.phase_manager: Optional[PhaseManager] = None
        self.current_project_state: Optional[ProjectState] = None
        self.error_handler = WorkflowErrorHandler(cli_interface)
        
        # Workflow configuration
        self.max_retry_attempts = 3
        self.require_explicit_approval = True
    
    def start_new_project(self, project_path: str) -> ProjectState:
        """Start a new project workflow.
        
        Args:
            project_path: Path to the project directory
            
        Returns:
            Initial project state
        """
        try:
            self.cli_interface.display_message(f"Initializing new project at: {project_path}")
            
            # Initialize state manager
            self.state_manager = StateManager(project_path)
            
            # Create initial project state
            session_id = str(uuid.uuid4())
            project_state = self.state_manager.create_initial_state(project_path, session_id)
            
            # Save initial state first
            if not self.state_manager.save_project_state(project_state):
                raise Exception("Failed to save initial project state")
            
            self.current_project_state = project_state
            
            # Initialize phase manager after state is set
            self.phase_manager = PhaseManager(
                cli_interface=self.cli_interface,
                state_manager=self.state_manager
            )
            
            self.cli_interface.display_message("Project initialized successfully!")
            self.cli_interface.display_message(f"Starting with {project_state.current_phase.value} phase")
            
            return project_state
            
        except Exception as e:
            error_msg = f"Failed to start new project: {e}"
            self.cli_interface.display_message(f"Error: {error_msg}")
            raise WorkflowException(error_msg) from e
    
    def resume_project(self, project_path: str) -> ProjectState:
        """Resume an existing project workflow.
        
        Args:
            project_path: Path to the project directory
            
        Returns:
            Loaded project state
        """
        try:
            self.cli_interface.display_message(f"Resuming project at: {project_path}")
            
            # Initialize state manager
            self.state_manager = StateManager(project_path)
            
            # Load existing project state
            project_state = self.state_manager.load_project_state()
            if not project_state:
                raise Exception("No existing project state found. Use start_new_project instead.")
            
            # Update session data
            project_state.session_data.last_activity = datetime.now()
            self.state_manager.save_project_state(project_state)
            
            self.current_project_state = project_state
            
            # Initialize phase manager after state is set
            self.phase_manager = PhaseManager(
                cli_interface=self.cli_interface,
                state_manager=self.state_manager
            )
            
            self.cli_interface.display_message("Project resumed successfully!")
            self.cli_interface.display_message(f"Current phase: {project_state.current_phase.value}")
            
            # Display progress summary
            self._display_progress_summary(project_state)
            
            return project_state
            
        except Exception as e:
            error_msg = f"Failed to resume project: {e}"
            self.cli_interface.display_message(f"Error: {error_msg}")
            raise WorkflowException(error_msg) from e
    
    def transition_to_phase(self, phase: PhaseType) -> bool:
        """Transition to the specified phase.
        
        Args:
            phase: Target phase to transition to
            
        Returns:
            True if transition successful
        """
        if not self.current_project_state:
            self.cli_interface.display_message("Error: No active project. Start or resume a project first.")
            return False
        
        # Ensure phase manager is initialized
        if not self.phase_manager:
            self.phase_manager = PhaseManager(
                cli_interface=self.cli_interface,
                state_manager=self.state_manager
            )
        
        try:
            current_phase = self.current_project_state.current_phase
            
            # Validate phase transition
            if not self._validate_phase_transition(current_phase, phase):
                return False
            
            self.cli_interface.display_message(f"Transitioning from {current_phase.value} to {phase.value} phase...")
            
            # Execute the target phase
            result = self._execute_phase(phase)
            
            if result.status == PhaseStatus.COMPLETED:
                # Update project state
                self.current_project_state.current_phase = phase
                self.state_manager.save_project_state(self.current_project_state)
                
                self.cli_interface.display_message(f"Successfully transitioned to {phase.value} phase!")
                return True
            else:
                self.cli_interface.display_message(f"Phase transition failed: {result.message}")
                return False
                
        except Exception as e:
            error_msg = f"Error during phase transition: {e}"
            self.cli_interface.display_message(f"Error: {error_msg}")
            self.error_handler.handle_phase_transition_error(current_phase, phase, e)
            return False
    
    def require_user_approval(self, content: str, phase: PhaseType) -> bool:
        """Require user approval for phase completion.
        
        Args:
            content: Content to show user for approval
            phase: Phase requesting approval
            
        Returns:
            True if user approves
        """
        if not self.require_explicit_approval:
            return True
        
        try:
            self.cli_interface.display_message(f"\n=== {phase.value.title()} Phase Approval Required ===")
            self.cli_interface.display_message(content)
            self.cli_interface.display_message("=" * 50)
            
            # Request approval through CLI
            approved = self.cli_interface.request_approval(content, phase.value)
            
            # Track approval in session data
            if self.current_project_state:
                self.current_project_state.session_data.user_approvals[phase.value] = approved
                self.state_manager.save_project_state(self.current_project_state)
            
            if approved:
                self.cli_interface.display_message(f"{phase.value.title()} phase approved!")
            else:
                self.cli_interface.display_message(f"{phase.value.title()} phase not approved.")
            
            return approved
            
        except Exception as e:
            self.cli_interface.display_message(f"Error during approval process: {e}")
            return False
    
    def get_current_phase(self) -> PhaseType:
        """Get the current workflow phase.
        
        Returns:
            Current phase type
        """
        if self.current_project_state:
            return self.current_project_state.current_phase
        else:
            return PhaseType.INDEXING  # Default phase
    
    def execute_complete_workflow(self) -> bool:
        """Execute the complete four-phase workflow.
        
        Returns:
            True if entire workflow completed successfully
        """
        if not self.current_project_state:
            self.cli_interface.display_message("Error: No active project. Start or resume a project first.")
            return False
        
        # Ensure phase manager is initialized
        if not self.phase_manager:
            self.phase_manager = PhaseManager(
                cli_interface=self.cli_interface,
                state_manager=self.state_manager
            )
        
        phases = [PhaseType.INDEXING, PhaseType.SPECIFICATION, PhaseType.DESIGN, PhaseType.IMPLEMENTATION]
        current_phase_index = phases.index(self.current_project_state.current_phase)
        
        self.cli_interface.display_message("Starting complete workflow execution...")
        
        # Execute remaining phases
        for phase in phases[current_phase_index:]:
            self.cli_interface.display_message(f"\n{'='*60}")
            self.cli_interface.display_message(f"EXECUTING {phase.value.upper()} PHASE")
            self.cli_interface.display_message(f"{'='*60}")
            
            if not self.transition_to_phase(phase):
                self.cli_interface.display_message(f"Workflow stopped at {phase.value} phase due to failure.")
                return False
        
        self.cli_interface.display_message("\n🎉 Complete workflow executed successfully!")
        self._display_final_summary()
        return True
    
    def _validate_phase_transition(self, current_phase: PhaseType, target_phase: PhaseType) -> bool:
        """Validate that phase transition is allowed.
        
        Args:
            current_phase: Current phase
            target_phase: Target phase
            
        Returns:
            True if transition is valid
        """
        # Define valid phase transitions
        valid_transitions = {
            PhaseType.INDEXING: [PhaseType.SPECIFICATION],
            PhaseType.SPECIFICATION: [PhaseType.DESIGN, PhaseType.INDEXING],  # Allow going back
            PhaseType.DESIGN: [PhaseType.IMPLEMENTATION, PhaseType.SPECIFICATION],  # Allow going back
            PhaseType.IMPLEMENTATION: [PhaseType.DESIGN]  # Allow going back to refine
        }
        
        if target_phase in valid_transitions.get(current_phase, []):
            return True
        
        # Allow staying in the same phase (for re-execution)
        if current_phase == target_phase:
            return True
        
        self.cli_interface.display_message(
            f"Error: Invalid phase transition from {current_phase.value} to {target_phase.value}"
        )
        return False
    
    def _execute_phase(self, phase: PhaseType) -> PhaseResult:
        """Execute a specific phase.
        
        Args:
            phase: Phase to execute
            
        Returns:
            Phase execution result
        """
        if not self.phase_manager:
            raise Exception("Phase manager not initialized")
        
        # Create project context
        context = self._create_project_context()
        
        # Execute phase based on type
        if phase == PhaseType.INDEXING:
            return self.phase_manager.execute_indexing_phase(self.current_project_state.project_path)
        elif phase == PhaseType.SPECIFICATION:
            return self.phase_manager.execute_specification_phase(context)
        elif phase == PhaseType.DESIGN:
            return self.phase_manager.execute_design_phase(context)
        elif phase == PhaseType.IMPLEMENTATION:
            return self.phase_manager.execute_implementation_phase(context)
        else:
            raise Exception(f"Unknown phase: {phase}")
    
    def _create_project_context(self) -> ProjectContext:
        """Create project context for phase execution.
        
        Returns:
            ProjectContext object
        """
        return ProjectContext(
            project_state=self.current_project_state,
            ast_index=None,  # Will be loaded by phase manager if needed
            codebase_patterns=None,  # Will be analyzed by phase manager if needed
            user_preferences={}  # Could be loaded from config in future
        )
    
    def _display_progress_summary(self, project_state: ProjectState) -> None:
        """Display a summary of project progress.
        
        Args:
            project_state: Current project state
        """
        self.cli_interface.display_message("\n=== Project Progress Summary ===")
        self.cli_interface.display_message(f"Project Path: {project_state.project_path}")
        self.cli_interface.display_message(f"Current Phase: {project_state.current_phase.value}")
        self.cli_interface.display_message(f"Indexing Complete: {'Yes' if project_state.indexing_complete else 'No'}")
        self.cli_interface.display_message(f"Has Specification: {'Yes' if project_state.specification else 'No'}")
        self.cli_interface.display_message(f"Has Design: {'Yes' if project_state.design else 'No'}")
        self.cli_interface.display_message(f"Has Tasks: {'Yes' if project_state.tasks else 'No'}")
        
        if project_state.implementation_progress:
            completed_tasks = sum(1 for status in project_state.implementation_progress.values() 
                                if status.value == 'completed')
            total_tasks = len(project_state.implementation_progress)
            self.cli_interface.display_message(f"Implementation Progress: {completed_tasks}/{total_tasks} tasks completed")
        
        self.cli_interface.display_message(f"Last Updated: {project_state.updated_at.strftime('%Y-%m-%d %H:%M:%S')}")
        self.cli_interface.display_message("=" * 35)
    
    def _display_final_summary(self) -> None:
        """Display final workflow completion summary."""
        if not self.current_project_state:
            return
        
        self.cli_interface.display_message("\n🎯 Workflow Completion Summary")
        self.cli_interface.display_message("=" * 40)
        
        # Index summary
        if self.current_project_state.index_metadata:
            meta = self.current_project_state.index_metadata
            self.cli_interface.display_message(f"📊 Indexed: {meta.total_files} files, {meta.total_lines} lines")
            self.cli_interface.display_message(f"🔍 Languages: {', '.join(meta.languages_detected)}")
        
        # Specification summary
        if self.current_project_state.specification:
            spec = self.current_project_state.specification
            self.cli_interface.display_message(f"📋 Specification: {len(spec.functional_requirements)} requirements")
        
        # Design summary
        if self.current_project_state.design:
            design = self.current_project_state.design
            self.cli_interface.display_message(f"🏗️  Design: {len(design.components)} components, {len(design.data_models)} models")
        
        # Implementation summary
        if self.current_project_state.tasks:
            tasks = self.current_project_state.tasks
            self.cli_interface.display_message(f"✅ Tasks: {len(tasks.tasks)} implementation tasks ready")
        
        self.cli_interface.display_message("\n🚀 Your project is ready for development!")
        self.cli_interface.display_message("Check the .dev_agent/documents/ folder for generated documents.")


class WorkflowErrorHandler:
    """Handles errors and recovery mechanisms for workflow operations."""
    
    def __init__(self, cli_interface: ICLIInterface):
        """Initialize error handler.
        
        Args:
            cli_interface: CLI interface for user communication
        """
        self.cli_interface = cli_interface
        self.error_log = []
    
    def handle_phase_transition_error(self, current_phase: PhaseType, target_phase: PhaseType, error: Exception) -> None:
        """Handle errors during phase transitions.
        
        Args:
            current_phase: Phase transitioning from
            target_phase: Phase transitioning to
            error: Exception that occurred
        """
        error_info = {
            'timestamp': datetime.now(),
            'current_phase': current_phase.value,
            'target_phase': target_phase.value,
            'error': str(error),
            'error_type': type(error).__name__
        }
        
        self.error_log.append(error_info)
        
        self.cli_interface.display_message(f"\n⚠️  Phase Transition Error")
        self.cli_interface.display_message(f"From: {current_phase.value} → To: {target_phase.value}")
        self.cli_interface.display_message(f"Error: {error}")
        
        # Suggest recovery actions
        recovery_suggestions = self._get_recovery_suggestions(current_phase, target_phase, error)
        if recovery_suggestions:
            self.cli_interface.display_message("\n💡 Suggested Recovery Actions:")
            for suggestion in recovery_suggestions:
                self.cli_interface.display_message(f"  • {suggestion}")
    
    def handle_phase_execution_error(self, phase: PhaseType, error: Exception) -> None:
        """Handle errors during phase execution.
        
        Args:
            phase: Phase that failed
            error: Exception that occurred
        """
        error_info = {
            'timestamp': datetime.now(),
            'phase': phase.value,
            'error': str(error),
            'error_type': type(error).__name__
        }
        
        self.error_log.append(error_info)
        
        self.cli_interface.display_message(f"\n❌ {phase.value.title()} Phase Error")
        self.cli_interface.display_message(f"Error: {error}")
        
        # Suggest recovery actions
        recovery_suggestions = self._get_phase_recovery_suggestions(phase, error)
        if recovery_suggestions:
            self.cli_interface.display_message("\n💡 Suggested Recovery Actions:")
            for suggestion in recovery_suggestions:
                self.cli_interface.display_message(f"  • {suggestion}")
    
    def _get_recovery_suggestions(self, current_phase: PhaseType, target_phase: PhaseType, error: Exception) -> list:
        """Get recovery suggestions for phase transition errors.
        
        Args:
            current_phase: Current phase
            target_phase: Target phase
            error: Error that occurred
            
        Returns:
            List of recovery suggestions
        """
        suggestions = []
        
        if "state" in str(error).lower():
            suggestions.append("Check if project state file is corrupted and try resuming the project")
            suggestions.append("If state is corrupted, you may need to restart from the indexing phase")
        
        if "permission" in str(error).lower():
            suggestions.append("Check file permissions in the project directory")
            suggestions.append("Ensure you have write access to the .dev_agent directory")
        
        if "memory" in str(error).lower() or "resource" in str(error).lower():
            suggestions.append("Try closing other applications to free up memory")
            suggestions.append("Consider processing the project in smaller chunks")
        
        # Phase-specific suggestions
        if target_phase == PhaseType.INDEXING:
            suggestions.append("Check if the project directory contains valid source files")
            suggestions.append("Ensure Tree-sitter parsers are properly installed")
        
        elif target_phase == PhaseType.SPECIFICATION:
            suggestions.append("Verify that indexing completed successfully")
            suggestions.append("Check if codebase analysis produced valid results")
        
        elif target_phase == PhaseType.DESIGN:
            suggestions.append("Ensure specification was approved and saved")
            suggestions.append("Check if specification contains valid requirements")
        
        elif target_phase == PhaseType.IMPLEMENTATION:
            suggestions.append("Verify that design document was approved")
            suggestions.append("Check if design contains valid components and interfaces")
        
        return suggestions
    
    def _get_phase_recovery_suggestions(self, phase: PhaseType, error: Exception) -> list:
        """Get recovery suggestions for phase execution errors.
        
        Args:
            phase: Phase that failed
            error: Error that occurred
            
        Returns:
            List of recovery suggestions
        """
        suggestions = []
        error_str = str(error).lower()
        
        # Common suggestions
        if "timeout" in error_str:
            suggestions.append("Increase timeout settings for long-running operations")
            suggestions.append("Try processing smaller chunks of the codebase")
        
        if "network" in error_str or "connection" in error_str:
            suggestions.append("Check internet connection for external dependencies")
            suggestions.append("Retry the operation after network issues are resolved")
        
        # Phase-specific suggestions
        if phase == PhaseType.INDEXING:
            suggestions.extend([
                "Check if all source files are readable",
                "Verify Tree-sitter language parsers are installed",
                "Try excluding problematic files or directories",
                "Ensure sufficient disk space for index storage"
            ])
        
        elif phase == PhaseType.SPECIFICATION:
            suggestions.extend([
                "Verify codebase analysis completed successfully",
                "Check if project contains recognizable code patterns",
                "Try providing more explicit user input for specification"
            ])
        
        elif phase == PhaseType.DESIGN:
            suggestions.extend([
                "Ensure specification document is valid and complete",
                "Check if architecture analysis found valid patterns",
                "Try simplifying the specification requirements"
            ])
        
        elif phase == PhaseType.IMPLEMENTATION:
            suggestions.extend([
                "Verify design document contains actionable components",
                "Check if task generation produced valid tasks",
                "Ensure target directory has write permissions"
            ])
        
        return suggestions


class WorkflowException(Exception):
    """Exception raised during workflow operations."""
    pass