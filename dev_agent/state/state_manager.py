"""State management for project state persistence and recovery."""

import json
import os
from datetime import datetime
from pathlib import Path
from typing import Optional, Dict, Any
from dataclasses import asdict, is_dataclass

from ..models.project_state import ProjectState, SessionData, IndexMetadata
from ..models.documents import SpecificationDocument, DesignDocument, TaskList
from ..models.enums import DocumentType, PhaseType, TaskStatus


class StateManager:
    """Manages project state persistence and document storage."""
    
    def __init__(self, project_path: str):
        """Initialize StateManager for a specific project.
        
        Args:
            project_path: Path to the project directory
        """
        self.project_path = Path(project_path)
        self.dev_agent_dir = self.project_path / '.dev_agent'
        self.state_file = self.dev_agent_dir / 'state.json'
        self.documents_dir = self.dev_agent_dir / 'documents'
        
        # Ensure directories exist
        self._ensure_directories()
    
    def _ensure_directories(self) -> None:
        """Create necessary directories if they don't exist."""
        self.dev_agent_dir.mkdir(exist_ok=True)
        self.documents_dir.mkdir(exist_ok=True)
    
    def _serialize_dataclass(self, obj: Any) -> Any:
        """Recursively serialize dataclass objects to dictionaries."""
        if is_dataclass(obj):
            result = {}
            for field_name, field_value in asdict(obj).items():
                result[field_name] = self._serialize_dataclass(field_value)
            return result
        elif isinstance(obj, list):
            return [self._serialize_dataclass(item) for item in obj]
        elif isinstance(obj, dict):
            return {key: self._serialize_dataclass(value) for key, value in obj.items()}
        elif isinstance(obj, datetime):
            return obj.isoformat()
        elif hasattr(obj, 'value'):  # Handle enums
            return obj.value
        else:
            return obj
    
    def _deserialize_datetime(self, date_str: str) -> datetime:
        """Deserialize ISO format datetime string."""
        return datetime.fromisoformat(date_str)
    
    def save_project_state(self, state: ProjectState) -> bool:
        """Save project state to JSON file.
        
        Args:
            state: ProjectState object to save
            
        Returns:
            True if successful, False otherwise
        """
        try:
            # Update the updated_at timestamp
            state.updated_at = datetime.now()
            
            # Serialize the state
            state_dict = self._serialize_dataclass(state)
            
            # Write to file with proper formatting
            with open(self.state_file, 'w', encoding='utf-8') as f:
                json.dump(state_dict, f, indent=2, ensure_ascii=False)
            
            return True
        except Exception as e:
            print(f"Error saving project state: {e}")
            return False
    
    def load_project_state(self) -> Optional[ProjectState]:
        """Load project state from JSON file.
        
        Returns:
            ProjectState object if successful, None otherwise
        """
        if not self.state_file.exists():
            return None
        
        try:
            with open(self.state_file, 'r', encoding='utf-8') as f:
                state_dict = json.load(f)
            
            # Reconstruct the ProjectState object
            return self._reconstruct_project_state(state_dict)
        except Exception as e:
            print(f"Error loading project state: {e}")
            return None
    
    def _reconstruct_project_state(self, state_dict: Dict[str, Any]) -> ProjectState:
        """Reconstruct ProjectState from dictionary."""
        # Handle datetime fields
        created_at = self._deserialize_datetime(state_dict['created_at'])
        updated_at = self._deserialize_datetime(state_dict['updated_at'])
        
        # Handle session data
        session_data_dict = state_dict['session_data']
        session_data = SessionData(
            session_id=session_data_dict['session_id'],
            started_at=self._deserialize_datetime(session_data_dict['started_at']),
            last_activity=self._deserialize_datetime(session_data_dict['last_activity']),
            user_approvals=session_data_dict['user_approvals'],
            pending_approvals=session_data_dict['pending_approvals']
        )
        
        # Handle index metadata
        index_metadata = None
        if state_dict['index_metadata']:
            idx_dict = state_dict['index_metadata']
            index_metadata = IndexMetadata(
                total_files=idx_dict['total_files'],
                total_lines=idx_dict['total_lines'],
                languages_detected=idx_dict['languages_detected'],
                index_size_mb=idx_dict['index_size_mb'],
                last_indexed=self._deserialize_datetime(idx_dict['last_indexed']),
                index_version=idx_dict['index_version']
            )
        
        # Handle documents (these will be loaded separately)
        specification = None
        if state_dict['specification']:
            specification = self._reconstruct_specification(state_dict['specification'])
        
        design = None
        if state_dict['design']:
            design = self._reconstruct_design(state_dict['design'])
        
        tasks = None
        if state_dict['tasks']:
            tasks = self._reconstruct_tasks(state_dict['tasks'])
        
        # Handle implementation progress
        implementation_progress = {}
        for task_id, status_str in state_dict['implementation_progress'].items():
            implementation_progress[task_id] = TaskStatus(status_str)
        
        return ProjectState(
            project_path=state_dict['project_path'],
            current_phase=PhaseType(state_dict['current_phase']),
            indexing_complete=state_dict['indexing_complete'],
            specification=specification,
            design=design,
            tasks=tasks,
            implementation_progress=implementation_progress,
            index_metadata=index_metadata,
            session_data=session_data,
            created_at=created_at,
            updated_at=updated_at
        )   
 
    def _reconstruct_specification(self, spec_dict: Dict[str, Any]) -> SpecificationDocument:
        """Reconstruct SpecificationDocument from dictionary."""
        from ..models.documents import Requirement, CodeAnalysisRef
        from ..models.enums import Priority, SpecificationSource
        
        # Reconstruct requirements
        requirements = []
        for req_dict in spec_dict['functional_requirements']:
            source_analysis = None
            if req_dict['source_analysis']:
                sa_dict = req_dict['source_analysis']
                source_analysis = CodeAnalysisRef(
                    file_paths=sa_dict['file_paths'],
                    functions=sa_dict['functions'],
                    confidence_score=sa_dict['confidence_score']
                )
            
            requirement = Requirement(
                id=req_dict['id'],
                user_story=req_dict['user_story'],
                acceptance_criteria=req_dict['acceptance_criteria'],
                priority=Priority(req_dict['priority']),
                source_analysis=source_analysis
            )
            requirements.append(requirement)
        
        approval_timestamp = None
        if spec_dict['approval_timestamp']:
            approval_timestamp = self._deserialize_datetime(spec_dict['approval_timestamp'])
        
        return SpecificationDocument(
            introduction=spec_dict['introduction'],
            key_features=spec_dict['key_features'],
            functional_requirements=requirements,
            source=SpecificationSource(spec_dict['source']),
            version=spec_dict['version'],
            approved=spec_dict['approved'],
            approval_timestamp=approval_timestamp
        )
    
    def _reconstruct_design(self, design_dict: Dict[str, Any]) -> DesignDocument:
        """Reconstruct DesignDocument from dictionary."""
        from ..models.documents import (
            ArchitectureDescription, ComponentSpec, DataModel, 
            InterfaceSpec, ErrorHandlingStrategy, TestingStrategy
        )
        
        # Reconstruct architecture
        arch_dict = design_dict['architecture']
        architecture = ArchitectureDescription(
            overview=arch_dict['overview'],
            patterns=arch_dict['patterns'],
            components=arch_dict['components']
        )
        
        # Reconstruct components
        components = []
        for comp_dict in design_dict['components']:
            component = ComponentSpec(
                name=comp_dict['name'],
                description=comp_dict['description'],
                interfaces=comp_dict['interfaces'],
                dependencies=comp_dict['dependencies']
            )
            components.append(component)
        
        # Reconstruct data models
        data_models = []
        for dm_dict in design_dict['data_models']:
            data_model = DataModel(
                name=dm_dict['name'],
                fields=dm_dict['fields'],
                relationships=dm_dict['relationships']
            )
            data_models.append(data_model)
        
        # Reconstruct interfaces
        interfaces = []
        for int_dict in design_dict['interfaces']:
            interface = InterfaceSpec(
                name=int_dict['name'],
                methods=int_dict['methods'],
                description=int_dict['description']
            )
            interfaces.append(interface)
        
        # Reconstruct error handling
        eh_dict = design_dict['error_handling']
        error_handling = ErrorHandlingStrategy(
            error_categories=eh_dict['error_categories'],
            recovery_mechanisms=eh_dict['recovery_mechanisms'],
            logging_strategy=eh_dict['logging_strategy']
        )
        
        # Reconstruct testing strategy
        ts_dict = design_dict['testing_strategy']
        testing_strategy = TestingStrategy(
            unit_testing=ts_dict['unit_testing'],
            integration_testing=ts_dict['integration_testing'],
            performance_testing=ts_dict['performance_testing'],
            test_coverage_target=ts_dict['test_coverage_target']
        )
        
        return DesignDocument(
            overview=design_dict['overview'],
            architecture=architecture,
            components=components,
            data_models=data_models,
            interfaces=interfaces,
            error_handling=error_handling,
            testing_strategy=testing_strategy,
            version=design_dict['version'],
            approved=design_dict['approved']
        )
    
    def _reconstruct_tasks(self, tasks_dict: Dict[str, Any]) -> TaskList:
        """Reconstruct TaskList from dictionary."""
        from ..models.documents import Task
        
        # Reconstruct tasks
        tasks = []
        for task_dict in tasks_dict['tasks']:
            task = Task(
                id=task_dict['id'],
                title=task_dict['title'],
                description=task_dict['description'],
                requirements_refs=task_dict['requirements_refs'],
                subtasks=task_dict['subtasks'],
                status=TaskStatus(task_dict['status']),
                target_language=task_dict['target_language'],
                context_requirements=task_dict['context_requirements'],
                implementation_notes=task_dict['implementation_notes'],
                generated_files=task_dict['generated_files']
            )
            tasks.append(task)
        
        return TaskList(
            tasks=tasks,
            dependencies=tasks_dict['dependencies'],
            estimated_effort=tasks_dict['estimated_effort'],
            version=tasks_dict['version'],
            approved=tasks_dict['approved']
        )
    
    def update_phase_status(self, phase: PhaseType, status: str) -> bool:
        """Update the current phase in the project state.
        
        Args:
            phase: The phase to update to
            status: Status information (for logging/tracking)
            
        Returns:
            True if successful, False otherwise
        """
        try:
            state = self.load_project_state()
            if state is None:
                return False
            
            state.current_phase = phase
            state.updated_at = datetime.now()
            
            return self.save_project_state(state)
        except Exception as e:
            print(f"Error updating phase status: {e}")
            return False
    
    def save_document(self, document: str, doc_type: DocumentType) -> bool:
        """Save a document to the appropriate file.
        
        Args:
            document: Document content as string
            doc_type: Type of document (SPECIFICATION, DESIGN, TASKS)
            
        Returns:
            True if successful, False otherwise
        """
        try:
            filename_map = {
                DocumentType.SPECIFICATION: 'SPECIFICATION.md',
                DocumentType.DESIGN: 'DESIGN.md',
                DocumentType.TASKS: 'TASKS.md'
            }
            
            filename = filename_map.get(doc_type)
            if not filename:
                return False
            
            file_path = self.documents_dir / filename
            
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(document)
            
            return True
        except Exception as e:
            print(f"Error saving document {doc_type}: {e}")
            return False
    
    def load_document(self, doc_type: DocumentType) -> Optional[str]:
        """Load a document from file.
        
        Args:
            doc_type: Type of document to load
            
        Returns:
            Document content as string if successful, None otherwise
        """
        try:
            filename_map = {
                DocumentType.SPECIFICATION: 'SPECIFICATION.md',
                DocumentType.DESIGN: 'DESIGN.md',
                DocumentType.TASKS: 'TASKS.md'
            }
            
            filename = filename_map.get(doc_type)
            if not filename:
                return None
            
            file_path = self.documents_dir / filename
            
            if not file_path.exists():
                return None
            
            with open(file_path, 'r', encoding='utf-8') as f:
                return f.read()
        except Exception as e:
            print(f"Error loading document {doc_type}: {e}")
            return None
    
    def track_task_progress(self, task_id: str, progress: TaskStatus) -> bool:
        """Track progress of a specific implementation task.
        
        Args:
            task_id: ID of the task to update
            progress: New status of the task
            
        Returns:
            True if successful, False otherwise
        """
        try:
            state = self.load_project_state()
            if state is None:
                return False
            
            state.implementation_progress[task_id] = progress
            state.updated_at = datetime.now()
            
            return self.save_project_state(state)
        except Exception as e:
            print(f"Error tracking task progress: {e}")
            return False
    
    def create_initial_state(self, project_path: str, session_id: str) -> ProjectState:
        """Create initial project state for a new project.
        
        Args:
            project_path: Path to the project
            session_id: Unique session identifier
            
        Returns:
            New ProjectState object
        """
        now = datetime.now()
        
        session_data = SessionData(
            session_id=session_id,
            started_at=now,
            last_activity=now,
            user_approvals={},
            pending_approvals=[]
        )
        
        return ProjectState(
            project_path=project_path,
            current_phase=PhaseType.INDEXING,
            indexing_complete=False,
            specification=None,
            design=None,
            tasks=None,
            implementation_progress={},
            index_metadata=None,
            session_data=session_data,
            created_at=now,
            updated_at=now
        )
    
    def get_project_info(self) -> Optional[Dict[str, Any]]:
        """Get basic project information from state.
        
        Returns:
            Dictionary with project info or None if no state exists
        """
        state = self.load_project_state()
        if state is None:
            return None
        
        return {
            'project_path': state.project_path,
            'current_phase': state.current_phase.value,
            'indexing_complete': state.indexing_complete,
            'created_at': state.created_at.isoformat(),
            'updated_at': state.updated_at.isoformat(),
            'has_specification': state.specification is not None,
            'has_design': state.design is not None,
            'has_tasks': state.tasks is not None,
            'total_tasks': len(state.implementation_progress) if state.implementation_progress else 0
        }