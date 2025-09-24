"""FastAPI-based REST API server for dev-agent."""

from __future__ import annotations

import logging
from contextlib import asynccontextmanager
from typing import Any

from fastapi import FastAPI, HTTPException, Depends, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel

from dev_agent.api.auth import AuthenticationManager
from dev_agent.api.routes import (
    workflow_router,
    project_router,
    analysis_router,
    generation_router,
    collaboration_router,
)
from dev_agent.api.websocket_manager import WebSocketManager
from dev_agent.config.config_manager import ConfigManager
from dev_agent.errors.exceptions import AuthenticationError, ConfigurationError
from dev_agent.workflow.workflow_manager import WorkflowManager

logger = logging.getLogger(__name__)

security = HTTPBearer()


class APIConfig(BaseModel):
    """Configuration for the API server."""
    
    host: str = "127.0.0.1"
    port: int = 8000
    debug: bool = False
    cors_origins: list[str] = ["http://localhost:3000", "http://localhost:8080"]
    cors_methods: list[str] = ["GET", "POST", "PUT", "DELETE", "PATCH"]
    cors_headers: list[str] = ["*"]
    jwt_secret_key: str = "dev-agent-secret-key-change-in-production"
    jwt_algorithm: str = "HS256"
    jwt_expiration_hours: int = 24


class APIServer:
    """FastAPI-based REST API server for dev-agent."""
    
    def __init__(
        self,
        workflow_manager: WorkflowManager,
        config_manager: ConfigManager,
        api_config: APIConfig | None = None,
    ) -> None:
        """Initialize the API server.
        
        Args:
            workflow_manager: The workflow manager instance
            config_manager: The configuration manager instance
            api_config: API-specific configuration
        """
        self.workflow_manager = workflow_manager
        self.config_manager = config_manager
        self.api_config = api_config or APIConfig()
        
        # Initialize components
        self.auth_manager = AuthenticationManager(
            secret_key=self.api_config.jwt_secret_key,
            algorithm=self.api_config.jwt_algorithm,
            expiration_hours=self.api_config.jwt_expiration_hours,
        )
        self.websocket_manager = WebSocketManager()
        
        # Create FastAPI app
        self.app = self._create_app()
    
    def _create_app(self) -> FastAPI:
        """Create and configure the FastAPI application."""
        
        @asynccontextmanager
        async def lifespan(app: FastAPI):
            """Application lifespan manager."""
            logger.info("Starting dev-agent API server")
            yield
            logger.info("Shutting down dev-agent API server")
        
        app = FastAPI(
            title="Dev-Agent API",
            description="REST API for the dev-agent development workflow assistant",
            version="0.1.0",
            lifespan=lifespan,
        )
        
        # Add CORS middleware
        app.add_middleware(
            CORSMiddleware,
            allow_origins=self.api_config.cors_origins,
            allow_credentials=True,
            allow_methods=self.api_config.cors_methods,
            allow_headers=self.api_config.cors_headers,
        )
        
        # Add dependency providers
        app.dependency_overrides[WorkflowManager] = lambda: self.workflow_manager
        app.dependency_overrides[ConfigManager] = lambda: self.config_manager
        app.dependency_overrides[AuthenticationManager] = lambda: self.auth_manager
        app.dependency_overrides[WebSocketManager] = lambda: self.websocket_manager
        
        # Include routers
        app.include_router(workflow_router, prefix="/api/v1/workflow", tags=["workflow"])
        app.include_router(project_router, prefix="/api/v1/projects", tags=["projects"])
        app.include_router(analysis_router, prefix="/api/v1/analysis", tags=["analysis"])
        app.include_router(generation_router, prefix="/api/v1/generation", tags=["generation"])
        app.include_router(collaboration_router, prefix="/api/v1/collaboration", tags=["collaboration"])
        
        # Add WebSocket endpoint
        app.add_websocket_route("/ws/{project_id}", self.websocket_manager.websocket_endpoint)
        
        # Health check endpoint
        @app.get("/health")
        async def health_check() -> dict[str, str]:
            """Health check endpoint."""
            return {"status": "healthy", "service": "dev-agent-api"}
        
        # Root endpoint
        @app.get("/")
        async def root() -> dict[str, str]:
            """Root endpoint with API information."""
            return {
                "message": "Dev-Agent API",
                "version": "0.1.0",
                "docs": "/docs",
                "health": "/health",
            }
        
        return app
    
    async def get_current_user(
        self,
        credentials: HTTPAuthorizationCredentials = Depends(security),
    ) -> dict[str, Any]:
        """Get the current authenticated user.
        
        Args:
            credentials: HTTP authorization credentials
            
        Returns:
            User information dictionary
            
        Raises:
            HTTPException: If authentication fails
        """
        try:
            user_info = await self.auth_manager.verify_token(credentials.credentials)
            return user_info
        except AuthenticationError as e:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail=str(e),
                headers={"WWW-Authenticate": "Bearer"},
            ) from e
    
    def run(self) -> None:
        """Run the API server."""
        import uvicorn
        
        try:
            uvicorn.run(
                self.app,
                host=self.api_config.host,
                port=self.api_config.port,
                log_level="debug" if self.api_config.debug else "info",
            )
        except Exception as e:
            logger.error(f"Failed to start API server: {e}")
            raise ConfigurationError(f"API server startup failed: {e}") from e