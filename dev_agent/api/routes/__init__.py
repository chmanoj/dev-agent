"""API routes for dev-agent REST API."""

from __future__ import annotations

__all__ = [
    "workflow_router",
    "project_router", 
    "analysis_router",
    "generation_router",
    "collaboration_router",
]

from dev_agent.api.routes.workflow import router as workflow_router
from dev_agent.api.routes.projects import router as project_router
from dev_agent.api.routes.analysis import router as analysis_router
from dev_agent.api.routes.generation import router as generation_router
from dev_agent.api.routes.collaboration import router as collaboration_router