"""Workflow API routes."""

from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel

from dev_agent.api.auth import AuthenticationManager
from dev_agent.errors.exceptions import WorkflowError
from dev_agent.models.enums import PhaseType, PhaseStatus
from dev_agent.workflow.workflow_manager import WorkflowManager

router = APIRouter()


class WorkflowStatusResponse(BaseModel):
    """Workflow status response model."""
    
    project_path: str
    current_phase: PhaseType
    phase_status: PhaseStatus
    progress: float
    indexing_complete: bool
    can_proceed: bool


class PhaseTransitionRequest(BaseModel):
    """Phase transition request model."""
    
    target_phase: PhaseType
    force: bool = False


class WorkflowActionRequest(BaseModel):
    """Workflow action request model."""
    
    action: str  # "start", "pause", "resume", "reset"
    parameters: dict[str, Any] = {}


@router.get("/status/{project_path:path}", response_model=WorkflowStatusResponse)
async def get_workflow_status(
    project_path: str,
    workflow_manager: WorkflowManager = Depends(),
    auth_manager: AuthenticationManager = Depends(),
    current_user: dict[str, Any] = Depends(),
) -> WorkflowStatusResponse:
    """Get workflow status for a project.
    
    Args:
        project_path: Project path
        workflow_manager: Workflow manager dependency
        auth_manager: Authentication manager dependency
        current_user: Current authenticated user
        
    Returns:
        Workflow status
        
    Raises:
        HTTPException: If workflow not found or access denied
    """
    # Check permissions
    auth_manager.require_permission(current_user["roles"], "workflow:read")
    
    try:
        # Get workflow status
        state = workflow_manager.get_project_state(project_path)
        
        return WorkflowStatusResponse(
            project_path=project_path,
            current_phase=state.current_phase,
            phase_status=state.phase_status,
            progress=workflow_manager.get_phase_progress(state.current_phase),
            indexing_complete=state.indexing_complete,
            can_proceed=workflow_manager.can_proceed_to_next_phase(state),
        )
    
    except WorkflowError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e),
        ) from e


@router.post("/transition/{project_path:path}")
async def transition_phase(
    project_path: str,
    request: PhaseTransitionRequest,
    workflow_manager: WorkflowManager = Depends(),
    auth_manager: AuthenticationManager = Depends(),
    current_user: dict[str, Any] = Depends(),
) -> dict[str, Any]:
    """Transition workflow to a different phase.
    
    Args:
        project_path: Project path
        request: Phase transition request
        workflow_manager: Workflow manager dependency
        auth_manager: Authentication manager dependency
        current_user: Current authenticated user
        
    Returns:
        Transition result
        
    Raises:
        HTTPException: If transition fails or access denied
    """
    # Check permissions
    auth_manager.require_permission(current_user["roles"], "workflow:write")
    
    try:
        # Perform phase transition
        success = await workflow_manager.transition_to_phase(
            project_path,
            request.target_phase,
            force=request.force,
        )
        
        if success:
            return {
                "success": True,
                "message": f"Transitioned to {request.target_phase.value}",
                "current_phase": request.target_phase.value,
            }
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Phase transition failed",
            )
    
    except WorkflowError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        ) from e


@router.post("/action/{project_path:path}")
async def execute_workflow_action(
    project_path: str,
    request: WorkflowActionRequest,
    workflow_manager: WorkflowManager = Depends(),
    auth_manager: AuthenticationManager = Depends(),
    current_user: dict[str, Any] = Depends(),
) -> dict[str, Any]:
    """Execute a workflow action.
    
    Args:
        project_path: Project path
        request: Workflow action request
        workflow_manager: Workflow manager dependency
        auth_manager: Authentication manager dependency
        current_user: Current authenticated user
        
    Returns:
        Action result
        
    Raises:
        HTTPException: If action fails or access denied
    """
    # Check permissions
    auth_manager.require_permission(current_user["roles"], "workflow:execute")
    
    try:
        if request.action == "start":
            result = await workflow_manager.start_workflow(project_path)
        elif request.action == "pause":
            result = await workflow_manager.pause_workflow(project_path)
        elif request.action == "resume":
            result = await workflow_manager.resume_workflow(project_path)
        elif request.action == "reset":
            result = await workflow_manager.reset_workflow(project_path)
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Unknown action: {request.action}",
            )
        
        return {
            "success": True,
            "action": request.action,
            "result": result,
        }
    
    except WorkflowError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        ) from e


@router.get("/phases")
async def get_available_phases(
    auth_manager: AuthenticationManager = Depends(),
    current_user: dict[str, Any] = Depends(),
) -> dict[str, Any]:
    """Get available workflow phases.
    
    Args:
        auth_manager: Authentication manager dependency
        current_user: Current authenticated user
        
    Returns:
        Available phases
    """
    # Check permissions
    auth_manager.require_permission(current_user["roles"], "workflow:read")
    
    phases = [
        {
            "name": phase.value,
            "description": _get_phase_description(phase),
        }
        for phase in PhaseType
    ]
    
    return {"phases": phases}


@router.get("/history/{project_path:path}")
async def get_workflow_history(
    project_path: str,
    workflow_manager: WorkflowManager = Depends(),
    auth_manager: AuthenticationManager = Depends(),
    current_user: dict[str, Any] = Depends(),
) -> dict[str, Any]:
    """Get workflow execution history.
    
    Args:
        project_path: Project path
        workflow_manager: Workflow manager dependency
        auth_manager: Authentication manager dependency
        current_user: Current authenticated user
        
    Returns:
        Workflow history
        
    Raises:
        HTTPException: If project not found or access denied
    """
    # Check permissions
    auth_manager.require_permission(current_user["roles"], "workflow:read")
    
    try:
        # Get workflow history
        history = workflow_manager.get_workflow_history(project_path)
        
        return {
            "project_path": project_path,
            "history": history,
        }
    
    except WorkflowError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e),
        ) from e


def _get_phase_description(phase: PhaseType) -> str:
    """Get description for a workflow phase.
    
    Args:
        phase: Workflow phase
        
    Returns:
        Phase description
    """
    descriptions = {
        PhaseType.INDEXING: "Analyze and index the codebase",
        PhaseType.SPECIFICATION: "Generate or refine project specifications",
        PhaseType.DESIGN: "Create technical design documents",
        PhaseType.IMPLEMENTATION: "Generate code and implementation",
    }
    
    return descriptions.get(phase, "Unknown phase")