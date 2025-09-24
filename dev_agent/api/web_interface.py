"""Web interface for dev-agent with dashboard and real-time updates."""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Any

from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from dev_agent.api.collaboration import CollaborationEngine
from dev_agent.api.websocket_manager import WebSocketManager
from dev_agent.config.config_manager import ConfigManager
from dev_agent.workflow.workflow_manager import WorkflowManager

logger = logging.getLogger(__name__)


class WebInterface:
    """Web interface for dev-agent with dashboard and real-time updates."""
    
    def __init__(
        self,
        workflow_manager: WorkflowManager,
        config_manager: ConfigManager,
        websocket_manager: WebSocketManager,
        collaboration_engine: CollaborationEngine,
    ) -> None:
        """Initialize the web interface.
        
        Args:
            workflow_manager: Workflow manager instance
            config_manager: Configuration manager instance
            websocket_manager: WebSocket manager instance
            collaboration_engine: Collaboration engine instance
        """
        self.workflow_manager = workflow_manager
        self.config_manager = config_manager
        self.websocket_manager = websocket_manager
        self.collaboration_engine = collaboration_engine
        
        # Setup templates and static files
        self.templates_dir = Path(__file__).parent / "templates"
        self.static_dir = Path(__file__).parent / "static"
        
        # Create directories if they don't exist
        self.templates_dir.mkdir(exist_ok=True)
        self.static_dir.mkdir(exist_ok=True)
        
        self.templates = Jinja2Templates(directory=str(self.templates_dir))
        
        # Create default templates if they don't exist
        self._create_default_templates()
    
    def setup_routes(self, app: FastAPI) -> None:
        """Setup web interface routes.
        
        Args:
            app: FastAPI application instance
        """
        # Mount static files
        app.mount("/static", StaticFiles(directory=str(self.static_dir)), name="static")
        
        # Dashboard routes
        @app.get("/dashboard", response_class=HTMLResponse)
        async def dashboard(request: Request) -> HTMLResponse:
            """Main dashboard page."""
            return await self.render_dashboard(request)
        
        @app.get("/dashboard/project/{project_id}", response_class=HTMLResponse)
        async def project_dashboard(request: Request, project_id: str) -> HTMLResponse:
            """Project-specific dashboard."""
            return await self.render_project_dashboard(request, project_id)
        
        @app.get("/dashboard/collaboration/{session_id}", response_class=HTMLResponse)
        async def collaboration_dashboard(request: Request, session_id: str) -> HTMLResponse:
            """Collaboration session dashboard."""
            return await self.render_collaboration_dashboard(request, session_id)
        
        # API endpoints for dashboard data
        @app.get("/api/v1/dashboard/stats")
        async def dashboard_stats() -> dict[str, Any]:
            """Get dashboard statistics."""
            return await self.get_dashboard_stats()
        
        @app.get("/api/v1/dashboard/projects")
        async def dashboard_projects() -> dict[str, Any]:
            """Get projects for dashboard."""
            return await self.get_dashboard_projects()
        
        @app.get("/api/v1/dashboard/activity")
        async def dashboard_activity() -> dict[str, Any]:
            """Get recent activity for dashboard."""
            return await self.get_dashboard_activity()
    
    async def render_dashboard(self, request: Request) -> HTMLResponse:
        """Render the main dashboard.
        
        Args:
            request: FastAPI request object
            
        Returns:
            HTML response with dashboard
        """
        context = {
            "request": request,
            "title": "Dev-Agent Dashboard",
            "stats": await self.get_dashboard_stats(),
            "projects": await self.get_dashboard_projects(),
            "activity": await self.get_dashboard_activity(),
        }
        
        return self.templates.TemplateResponse("dashboard.html", context)
    
    async def render_project_dashboard(
        self, 
        request: Request, 
        project_id: str
    ) -> HTMLResponse:
        """Render project-specific dashboard.
        
        Args:
            request: FastAPI request object
            project_id: Project ID
            
        Returns:
            HTML response with project dashboard
        """
        project_info = await self.get_project_info(project_id)
        
        context = {
            "request": request,
            "title": f"Project: {project_info.get('name', project_id)}",
            "project_id": project_id,
            "project": project_info,
            "workflow_status": await self.get_project_workflow_status(project_id),
            "collaboration_sessions": self.collaboration_engine.get_active_sessions(project_id),
            "connected_users": self.websocket_manager.get_project_users(project_id),
        }
        
        return self.templates.TemplateResponse("project_dashboard.html", context)
    
    async def render_collaboration_dashboard(
        self, 
        request: Request, 
        session_id: str
    ) -> HTMLResponse:
        """Render collaboration session dashboard.
        
        Args:
            request: FastAPI request object
            session_id: Collaboration session ID
            
        Returns:
            HTML response with collaboration dashboard
        """
        session_info = self.collaboration_engine.get_session_info(session_id)
        
        context = {
            "request": request,
            "title": f"Collaboration Session: {session_id}",
            "session_id": session_id,
            "session": session_info,
        }
        
        return self.templates.TemplateResponse("collaboration_dashboard.html", context)
    
    async def get_dashboard_stats(self) -> dict[str, Any]:
        """Get dashboard statistics.
        
        Returns:
            Dashboard statistics
        """
        # Get basic stats
        total_connections = self.websocket_manager.get_connection_count()
        active_sessions = len(self.collaboration_engine.get_active_sessions())
        
        # TODO: Add more stats from workflow manager
        # - Total projects
        # - Active workflows
        # - Completed tasks
        # - etc.
        
        return {
            "total_connections": total_connections,
            "active_sessions": active_sessions,
            "total_projects": 0,  # Placeholder
            "active_workflows": 0,  # Placeholder
        }
    
    async def get_dashboard_projects(self) -> dict[str, Any]:
        """Get projects for dashboard.
        
        Returns:
            Projects data
        """
        # TODO: Implement project listing from workflow manager
        return {
            "projects": [],
            "total": 0,
        }
    
    async def get_dashboard_activity(self) -> dict[str, Any]:
        """Get recent activity for dashboard.
        
        Returns:
            Recent activity data
        """
        # TODO: Implement activity tracking
        return {
            "recent_activity": [],
            "total": 0,
        }
    
    async def get_project_info(self, project_id: str) -> dict[str, Any]:
        """Get project information.
        
        Args:
            project_id: Project ID
            
        Returns:
            Project information
        """
        # TODO: Implement project info retrieval from workflow manager
        return {
            "id": project_id,
            "name": f"Project {project_id}",
            "status": "active",
        }
    
    async def get_project_workflow_status(self, project_id: str) -> dict[str, Any]:
        """Get project workflow status.
        
        Args:
            project_id: Project ID
            
        Returns:
            Workflow status
        """
        # TODO: Implement workflow status retrieval
        return {
            "current_phase": "indexing",
            "progress": 0.0,
            "tasks_completed": 0,
            "tasks_total": 0,
        }
    
    def _create_default_templates(self) -> None:
        """Create default HTML templates if they don't exist."""
        
        # Base template
        base_template = '''<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{{ title }} - Dev-Agent</title>
    <link href="https://cdn.jsdelivr.net/npm/tailwindcss@2.2.19/dist/tailwind.min.css" rel="stylesheet">
    <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
    <style>
        .sidebar { min-height: 100vh; }
        .main-content { min-height: 100vh; }
    </style>
</head>
<body class="bg-gray-100">
    <div class="flex">
        <!-- Sidebar -->
        <div class="sidebar w-64 bg-gray-800 text-white p-6">
            <h1 class="text-2xl font-bold mb-8">Dev-Agent</h1>
            <nav>
                <ul class="space-y-2">
                    <li><a href="/dashboard" class="block py-2 px-4 rounded hover:bg-gray-700">Dashboard</a></li>
                    <li><a href="/api/docs" class="block py-2 px-4 rounded hover:bg-gray-700">API Docs</a></li>
                </ul>
            </nav>
        </div>
        
        <!-- Main Content -->
        <div class="main-content flex-1 p-8">
            {% block content %}{% endblock %}
        </div>
    </div>
    
    <!-- WebSocket Connection -->
    <script>
        // WebSocket connection for real-time updates
        const projectId = '{{ project_id or "default" }}';
        const ws = new WebSocket(`ws://localhost:8000/ws/${projectId}`);
        
        ws.onopen = function(event) {
            console.log('WebSocket connected');
            // Authenticate if needed
            ws.send(JSON.stringify({
                type: 'auth',
                data: { user_id: 'current_user' },
                timestamp: new Date().toISOString()
            }));
        };
        
        ws.onmessage = function(event) {
            const message = JSON.parse(event.data);
            console.log('WebSocket message:', message);
            
            // Handle different message types
            if (message.type === 'project_update') {
                handleProjectUpdate(message.data);
            } else if (message.type === 'collaboration') {
                handleCollaborationEvent(message.data);
            }
        };
        
        ws.onclose = function(event) {
            console.log('WebSocket disconnected');
        };
        
        function handleProjectUpdate(data) {
            // Update UI based on project updates
            console.log('Project update:', data);
        }
        
        function handleCollaborationEvent(data) {
            // Update UI based on collaboration events
            console.log('Collaboration event:', data);
        }
    </script>
</body>
</html>'''
        
        # Dashboard template
        dashboard_template = '''{% extends "base.html" %}

{% block content %}
<div class="mb-8">
    <h2 class="text-3xl font-bold text-gray-900">Dashboard</h2>
    <p class="text-gray-600">Overview of your dev-agent projects and activity</p>
</div>

<!-- Stats Cards -->
<div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-8">
    <div class="bg-white p-6 rounded-lg shadow">
        <h3 class="text-lg font-semibold text-gray-900">Active Connections</h3>
        <p class="text-3xl font-bold text-blue-600">{{ stats.total_connections }}</p>
    </div>
    <div class="bg-white p-6 rounded-lg shadow">
        <h3 class="text-lg font-semibold text-gray-900">Collaboration Sessions</h3>
        <p class="text-3xl font-bold text-green-600">{{ stats.active_sessions }}</p>
    </div>
    <div class="bg-white p-6 rounded-lg shadow">
        <h3 class="text-lg font-semibold text-gray-900">Total Projects</h3>
        <p class="text-3xl font-bold text-purple-600">{{ stats.total_projects }}</p>
    </div>
    <div class="bg-white p-6 rounded-lg shadow">
        <h3 class="text-lg font-semibold text-gray-900">Active Workflows</h3>
        <p class="text-3xl font-bold text-orange-600">{{ stats.active_workflows }}</p>
    </div>
</div>

<!-- Projects Section -->
<div class="bg-white rounded-lg shadow mb-8">
    <div class="p-6 border-b">
        <h3 class="text-xl font-semibold text-gray-900">Recent Projects</h3>
    </div>
    <div class="p-6">
        {% if projects.projects %}
            <div class="space-y-4">
                {% for project in projects.projects %}
                <div class="border rounded-lg p-4">
                    <h4 class="font-semibold">{{ project.name }}</h4>
                    <p class="text-gray-600">{{ project.description or "No description" }}</p>
                    <div class="mt-2">
                        <span class="inline-block px-2 py-1 text-xs rounded-full bg-green-100 text-green-800">
                            {{ project.status }}
                        </span>
                    </div>
                </div>
                {% endfor %}
            </div>
        {% else %}
            <p class="text-gray-500">No projects found. Start by creating a new project.</p>
        {% endif %}
    </div>
</div>

<!-- Activity Section -->
<div class="bg-white rounded-lg shadow">
    <div class="p-6 border-b">
        <h3 class="text-xl font-semibold text-gray-900">Recent Activity</h3>
    </div>
    <div class="p-6">
        {% if activity.recent_activity %}
            <div class="space-y-4">
                {% for item in activity.recent_activity %}
                <div class="flex items-center space-x-4">
                    <div class="flex-shrink-0">
                        <div class="w-8 h-8 bg-blue-100 rounded-full flex items-center justify-center">
                            <span class="text-blue-600 text-sm">•</span>
                        </div>
                    </div>
                    <div>
                        <p class="text-gray-900">{{ item.description }}</p>
                        <p class="text-gray-500 text-sm">{{ item.timestamp }}</p>
                    </div>
                </div>
                {% endfor %}
            </div>
        {% else %}
            <p class="text-gray-500">No recent activity.</p>
        {% endif %}
    </div>
</div>
{% endblock %}'''
        
        # Project dashboard template
        project_dashboard_template = '''{% extends "base.html" %}

{% block content %}
<div class="mb-8">
    <h2 class="text-3xl font-bold text-gray-900">{{ project.name }}</h2>
    <p class="text-gray-600">Project ID: {{ project_id }}</p>
</div>

<!-- Workflow Status -->
<div class="bg-white rounded-lg shadow mb-8">
    <div class="p-6 border-b">
        <h3 class="text-xl font-semibold text-gray-900">Workflow Status</h3>
    </div>
    <div class="p-6">
        <div class="mb-4">
            <div class="flex justify-between items-center mb-2">
                <span class="text-sm font-medium text-gray-700">Current Phase: {{ workflow_status.current_phase }}</span>
                <span class="text-sm text-gray-500">{{ (workflow_status.progress * 100)|round }}%</span>
            </div>
            <div class="w-full bg-gray-200 rounded-full h-2">
                <div class="bg-blue-600 h-2 rounded-full" style="width: {{ (workflow_status.progress * 100)|round }}%"></div>
            </div>
        </div>
        <p class="text-gray-600">
            Tasks: {{ workflow_status.tasks_completed }} / {{ workflow_status.tasks_total }} completed
        </p>
    </div>
</div>

<!-- Collaboration -->
<div class="grid grid-cols-1 lg:grid-cols-2 gap-8">
    <!-- Active Sessions -->
    <div class="bg-white rounded-lg shadow">
        <div class="p-6 border-b">
            <h3 class="text-xl font-semibold text-gray-900">Collaboration Sessions</h3>
        </div>
        <div class="p-6">
            {% if collaboration_sessions %}
                <div class="space-y-4">
                    {% for session in collaboration_sessions %}
                    <div class="border rounded-lg p-4">
                        <h4 class="font-semibold">Session {{ session.id[:8] }}...</h4>
                        <p class="text-gray-600">{{ session.participants|length }} participants</p>
                        <p class="text-gray-600">{{ session.document_count }} documents</p>
                    </div>
                    {% endfor %}
                </div>
            {% else %}
                <p class="text-gray-500">No active collaboration sessions.</p>
            {% endif %}
        </div>
    </div>
    
    <!-- Connected Users -->
    <div class="bg-white rounded-lg shadow">
        <div class="p-6 border-b">
            <h3 class="text-xl font-semibold text-gray-900">Connected Users</h3>
        </div>
        <div class="p-6">
            {% if connected_users %}
                <div class="space-y-2">
                    {% for user in connected_users %}
                    <div class="flex items-center space-x-2">
                        <div class="w-2 h-2 bg-green-500 rounded-full"></div>
                        <span class="text-gray-900">{{ user }}</span>
                    </div>
                    {% endfor %}
                </div>
            {% else %}
                <p class="text-gray-500">No users currently connected.</p>
            {% endif %}
        </div>
    </div>
</div>
{% endblock %}'''
        
        # Collaboration dashboard template
        collaboration_dashboard_template = '''{% extends "base.html" %}

{% block content %}
<div class="mb-8">
    <h2 class="text-3xl font-bold text-gray-900">Collaboration Session</h2>
    <p class="text-gray-600">Session ID: {{ session_id }}</p>
</div>

<!-- Session Info -->
<div class="bg-white rounded-lg shadow mb-8">
    <div class="p-6 border-b">
        <h3 class="text-xl font-semibold text-gray-900">Session Information</h3>
    </div>
    <div class="p-6">
        <div class="grid grid-cols-2 gap-4">
            <div>
                <p class="text-gray-600">Project ID:</p>
                <p class="font-semibold">{{ session.project_id }}</p>
            </div>
            <div>
                <p class="text-gray-600">Participants:</p>
                <p class="font-semibold">{{ session.participants|length }}</p>
            </div>
            <div>
                <p class="text-gray-600">Documents:</p>
                <p class="font-semibold">{{ session.document_count }}</p>
            </div>
            <div>
                <p class="text-gray-600">Created:</p>
                <p class="font-semibold">{{ session.created_at }}</p>
            </div>
        </div>
    </div>
</div>

<!-- Participants -->
<div class="bg-white rounded-lg shadow">
    <div class="p-6 border-b">
        <h3 class="text-xl font-semibold text-gray-900">Participants</h3>
    </div>
    <div class="p-6">
        <div class="space-y-2">
            {% for participant in session.participants %}
            <div class="flex items-center space-x-2">
                <div class="w-2 h-2 bg-green-500 rounded-full"></div>
                <span class="text-gray-900">{{ participant }}</span>
            </div>
            {% endfor %}
        </div>
    </div>
</div>
{% endblock %}'''
        
        # Write templates to files
        templates = {
            "base.html": base_template,
            "dashboard.html": dashboard_template,
            "project_dashboard.html": project_dashboard_template,
            "collaboration_dashboard.html": collaboration_dashboard_template,
        }
        
        for filename, content in templates.items():
            template_path = self.templates_dir / filename
            if not template_path.exists():
                template_path.write_text(content)
                logger.info(f"Created template: {filename}")
    
    async def handle_real_time_updates(self, project_id: str) -> None:
        """Handle real-time updates for a project.
        
        Args:
            project_id: Project ID to handle updates for
        """
        # This method would be called when project state changes
        # to broadcast updates to connected clients
        
        # TODO: Implement real-time update logic
        pass
    
    async def manage_collaborative_sessions(self, session_id: str) -> None:
        """Manage collaborative editing sessions.
        
        Args:
            session_id: Session ID to manage
        """
        # This method would handle collaborative session management
        
        # TODO: Implement collaborative session management
        pass