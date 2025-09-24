"""Project management API routes."""

from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel

from dev_agent.api.auth import AuthenticationManager
from dev_agent.errors.exceptions import ProjectError
from dev_agent.workflow.workflow_manager import WorkflowManager

router = APIRouter()


class ProjectInfo(BaseModel):
    """Project information model."""
    
    id: str
    name: str
    path: str
    description: str | None = None
    status: str
    current_phase: str | None = None
    created_at: str
    last_modified: str


class CreateProjectRequest(BaseModel):
    """Create project request model."""
    
    name: str
    path: str
    description: str | None = None


class UpdateProjectRequest(BaseModel):
    """Update project request model."""
    
    name: str | None = None
    description: str | None = None


@router.get("/", response_model=list[ProjectInfo])
async def list_projects(
    workflow_manager: WorkflowManager = Depends(),
    auth_manager: AuthenticationManager = Depends(),
    current_user: dict[str, Any] = Depends(),
) -> list[ProjectInfo]:
    """List all projects.
    
    Args:
        workflow_manager: Workflow manager dependency
        auth_manager: Authentication manager dependency
        current_user: Current authenticated user
        
    Returns:
        List of projects
    """
    # Check permissions
    auth_manager.require_permission(current_user["roles"], "project:read")
    
    # TODO: Implement project listing from workflow manager
    # For now, return empty list
    return []


@router.post("/", response_model=ProjectInfo)
async def create_project(
    request: CreateProjectRequest,
    workflow_manager: WorkflowManager = Depends(),
    auth_manager: AuthenticationManager = Depends(),
    current_user: dict[str, Any] = Depends(),
) -> ProjectInfo:
    """Create a new project.
    
    Args:
        request: Create project request
        workflow_manager: Workflow manager dependency
        auth_manager: Authentication manager dependency
        current_user: Current authenticated user
        
    Returns:
        Created project information
        
    Raises:
        HTTPException: If project creation fails or access denied
    """
    # Check permissions
    auth_manager.require_permission(current_user["roles"], "project:write")
    
    try:
        # Initialize project
        project_state = workflow_manager.initialize_project(request.path)
        
        # TODO: Store project metadata (name, description, etc.)
        
        return ProjectInfo(
            id=request.path,
            name=request.name,
            path=request.path,
            description=request.description,
            status="initialized",
            current_phase=project_state.current_phase.value,
            created_at=project_state.created_at.isoformat(),
            last_modified=project_state.last_modified.isoformat(),
        )
    
    except ProjectError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        ) from e


@router.get("/{project_id}", response_model=ProjectInfo)
async def get_project(
    project_id: str,
    workflow_manager: WorkflowManager = Depends(),
    auth_manager: AuthenticationManager = Depends(),
    current_user: dict[str, Any] = Depends(),
) -> ProjectInfo:
    """Get project information.
    
    Args:
        project_id: Project ID
        workflow_manager: Workflow manager dependency
        auth_manager: Authentication manager dependency
        current_user: Current authenticated user
        
    Returns:
        Project information
        
    Raises:
        HTTPException: If project not found or access denied
    """
    # Check permissions
    auth_manager.require_permission(current_user["roles"], "project:read")
    
    try:
        # Get project state
        project_state = workflow_manager.get_project_state(project_id)
        
        # TODO: Get project metadata from storage
        
        return ProjectInfo(
            id=project_id,
            name=f"Project {project_id}",  # Placeholder
            path=project_id,
            description=None,
            status="active",
            current_phase=project_state.current_phase.value,
            created_at=project_state.created_at.isoformat(),
            last_modified=project_state.last_modified.isoformat(),
        )
    
    except ProjectError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e),
        ) from e


@router.put("/{project_id}", response_model=ProjectInfo)
async def update_project(
    project_id: str,
    request: UpdateProjectRequest,
    workflow_manager: WorkflowManager = Depends(),
    auth_manager: AuthenticationManager = Depends(),
    current_user: dict[str, Any] = Depends(),
) -> ProjectInfo:
    """Update project information.
    
    Args:
        project_id: Project ID
        request: Update project request
        workflow_manager: Workflow manager dependency
        auth_manager: Authentication manager dependency
        current_user: Current authenticated user
        
    Returns:
        Updated project information
        
    Raises:
        HTTPException: If project not found or access denied
    """
    # Check permissions
    auth_manager.require_permission(current_user["roles"], "project:write")
    
    try:
        # Get current project state
        project_state = workflow_manager.get_project_state(project_id)
        
        # TODO: Update project metadata in storage
        
        return ProjectInfo(
            id=project_id,
            name=request.name or f"Project {project_id}",
            path=project_id,
            description=request.description,
            status="active",
            current_phase=project_state.current_phase.value,
            created_at=project_state.created_at.isoformat(),
            last_modified=project_state.last_modified.isoformat(),
        )
    
    except ProjectError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e),
        ) from e


@router.delete("/{project_id}")
async def delete_project(
    project_id: str,
    workflow_manager: WorkflowManager = Depends(),
    auth_manager: AuthenticationManager = Depends(),
    current_user: dict[str, Any] = Depends(),
) -> dict[str, str]:
    """Delete a project.
    
    Args:
        project_id: Project ID
        workflow_manager: Workflow manager dependency
        auth_manager: Authentication manager dependency
        current_user: Current authenticated user
        
    Returns:
        Deletion confirmation
        
    Raises:
        HTTPException: If project not found or access denied
    """
    # Check permissions
    auth_manager.require_permission(current_user["roles"], "project:delete")
    
    try:
        # TODO: Implement project deletion
        # This should remove project state, documents, and metadata
        
        return {"message": f"Project {project_id} deleted successfully"}
    
    except ProjectError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e),
        ) from e


@router.get("/{project_id}/files")
async def list_project_files(
    project_id: str,
    workflow_manager: WorkflowManager = Depends(),
    auth_manager: AuthenticationManager = Depends(),
    current_user: dict[str, Any] = Depends(),
) -> dict[str, Any]:
    """List files in a project.
    
    Args:
        project_id: Project ID
        workflow_manager: Workflow manager dependency
        auth_manager: Authentication manager dependency
        current_user: Current authenticated user
        
    Returns:
        Project files
        
    Raises:
        HTTPException: If project not found or access denied
    """
    # Check permissions
    auth_manager.require_permission(current_user["roles"], "project:read")
    
    try:
        # TODO: Implement file listing from indexing engine
        
        return {
            "project_id": project_id,
            "files": [],
            "total": 0,
        }
    
    except ProjectError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e),
        ) from e


@router.get("/{project_id}/documents")
async def list_project_documents(
    project_id: str,
    workflow_manager: WorkflowManager = Depends(),
    auth_manager: AuthenticationManager = Depends(),
    current_user: dict[str, Any] = Depends(),
) -> dict[str, Any]:
    """List generated documents for a project.
    
    Args:
        project_id: Project ID
        workflow_manager: Workflow manager dependency
        auth_manager: Authentication manager dependency
        current_user: Current authenticated user
        
    Returns:
        Project documents
        
    Raises:
        HTTPException: If project not found or access denied
    """
    # Check permissions
    auth_manager.require_permission(current_user["roles"], "project:read")
    
    try:
        # Get project state
        project_state = workflow_manager.get_project_state(project_id)
        
        documents = []
        
        if project_state.specification:
            documents.append({
                "type": "specification",
                "title": "Project Specification",
                "content": project_state.specification.content,
                "created_at": project_state.specification.created_at.isoformat(),
            })
        
        if project_state.design:
            documents.append({
                "type": "design",
                "title": "Technical Design",
                "content": project_state.design.content,
                "created_at": project_state.design.created_at.isoformat(),
            })
        
        if project_state.tasks:
            documents.append({
                "type": "tasks",
                "title": "Implementation Tasks",
                "content": "\n".join([
                    f"- {task.description}" 
                    for task in project_state.tasks.tasks
                ]),
                "created_at": project_state.tasks.created_at.isoformat(),
            })
        
        return {
            "project_id": project_id,
            "documents": documents,
            "total": len(documents),
        }
    
    except ProjectError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e),
        ) from e