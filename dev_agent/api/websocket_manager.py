"""WebSocket manager for real-time updates and collaboration."""

from __future__ import annotations

import json
import logging
from typing import Any
from uuid import uuid4

from fastapi import WebSocket, WebSocketDisconnect
from pydantic import BaseModel

from dev_agent.errors.exceptions import AuthenticationError

logger = logging.getLogger(__name__)


class WebSocketMessage(BaseModel):
    """WebSocket message model."""
    
    type: str
    data: dict[str, Any]
    timestamp: str
    sender_id: str | None = None
    project_id: str | None = None


class ConnectionInfo(BaseModel):
    """WebSocket connection information."""
    
    connection_id: str
    websocket: WebSocket
    user_id: str | None = None
    project_id: str | None = None
    is_authenticated: bool = False


class WebSocketManager:
    """Manager for WebSocket connections and real-time updates."""
    
    def __init__(self) -> None:
        """Initialize the WebSocket manager."""
        # Active connections by connection ID
        self.connections: dict[str, ConnectionInfo] = {}
        
        # Project-based connection groups
        self.project_connections: dict[str, set[str]] = {}
        
        # User-based connection groups
        self.user_connections: dict[str, set[str]] = {}
    
    async def connect(self, websocket: WebSocket, project_id: str) -> str:
        """Accept a new WebSocket connection.
        
        Args:
            websocket: WebSocket connection
            project_id: Project ID for the connection
            
        Returns:
            Connection ID
        """
        await websocket.accept()
        
        connection_id = str(uuid4())
        connection_info = ConnectionInfo(
            connection_id=connection_id,
            websocket=websocket,
            project_id=project_id,
        )
        
        self.connections[connection_id] = connection_info
        
        # Add to project group
        if project_id not in self.project_connections:
            self.project_connections[project_id] = set()
        self.project_connections[project_id].add(connection_id)
        
        logger.info(f"WebSocket connected: {connection_id} for project {project_id}")
        return connection_id
    
    def disconnect(self, connection_id: str) -> None:
        """Disconnect a WebSocket connection.
        
        Args:
            connection_id: Connection ID to disconnect
        """
        if connection_id not in self.connections:
            return
        
        connection_info = self.connections[connection_id]
        
        # Remove from project group
        if connection_info.project_id:
            project_connections = self.project_connections.get(connection_info.project_id)
            if project_connections:
                project_connections.discard(connection_id)
                if not project_connections:
                    del self.project_connections[connection_info.project_id]
        
        # Remove from user group
        if connection_info.user_id:
            user_connections = self.user_connections.get(connection_info.user_id)
            if user_connections:
                user_connections.discard(connection_id)
                if not user_connections:
                    del self.user_connections[connection_info.user_id]
        
        # Remove connection
        del self.connections[connection_id]
        
        logger.info(f"WebSocket disconnected: {connection_id}")
    
    async def authenticate_connection(
        self, 
        connection_id: str, 
        user_id: str
    ) -> None:
        """Authenticate a WebSocket connection.
        
        Args:
            connection_id: Connection ID
            user_id: User ID
            
        Raises:
            AuthenticationError: If connection not found
        """
        if connection_id not in self.connections:
            raise AuthenticationError("Connection not found")
        
        connection_info = self.connections[connection_id]
        connection_info.user_id = user_id
        connection_info.is_authenticated = True
        
        # Add to user group
        if user_id not in self.user_connections:
            self.user_connections[user_id] = set()
        self.user_connections[user_id].add(connection_id)
        
        logger.info(f"WebSocket authenticated: {connection_id} for user {user_id}")
    
    async def send_message(
        self, 
        connection_id: str, 
        message: WebSocketMessage
    ) -> None:
        """Send a message to a specific connection.
        
        Args:
            connection_id: Connection ID
            message: Message to send
        """
        if connection_id not in self.connections:
            logger.warning(f"Attempted to send message to unknown connection: {connection_id}")
            return
        
        connection_info = self.connections[connection_id]
        try:
            await connection_info.websocket.send_text(message.model_dump_json())
        except Exception as e:
            logger.error(f"Failed to send message to {connection_id}: {e}")
            self.disconnect(connection_id)
    
    async def broadcast_to_project(
        self, 
        project_id: str, 
        message: WebSocketMessage,
        exclude_connection: str | None = None,
    ) -> None:
        """Broadcast a message to all connections in a project.
        
        Args:
            project_id: Project ID
            message: Message to broadcast
            exclude_connection: Connection ID to exclude from broadcast
        """
        project_connections = self.project_connections.get(project_id, set())
        
        for connection_id in project_connections.copy():
            if exclude_connection and connection_id == exclude_connection:
                continue
            
            await self.send_message(connection_id, message)
    
    async def broadcast_to_user(
        self, 
        user_id: str, 
        message: WebSocketMessage
    ) -> None:
        """Broadcast a message to all connections for a user.
        
        Args:
            user_id: User ID
            message: Message to broadcast
        """
        user_connections = self.user_connections.get(user_id, set())
        
        for connection_id in user_connections.copy():
            await self.send_message(connection_id, message)
    
    async def handle_message(
        self, 
        connection_id: str, 
        message_data: dict[str, Any]
    ) -> None:
        """Handle an incoming WebSocket message.
        
        Args:
            connection_id: Connection ID
            message_data: Raw message data
        """
        try:
            message = WebSocketMessage(**message_data)
            
            # Handle different message types
            if message.type == "auth":
                await self._handle_auth_message(connection_id, message)
            elif message.type == "project_update":
                await self._handle_project_update(connection_id, message)
            elif message.type == "collaboration":
                await self._handle_collaboration_message(connection_id, message)
            elif message.type == "ping":
                await self._handle_ping_message(connection_id, message)
            else:
                logger.warning(f"Unknown message type: {message.type}")
        
        except Exception as e:
            logger.error(f"Error handling WebSocket message: {e}")
            error_message = WebSocketMessage(
                type="error",
                data={"error": str(e)},
                timestamp=message_data.get("timestamp", ""),
            )
            await self.send_message(connection_id, error_message)
    
    async def _handle_auth_message(
        self, 
        connection_id: str, 
        message: WebSocketMessage
    ) -> None:
        """Handle authentication message.
        
        Args:
            connection_id: Connection ID
            message: Authentication message
        """
        user_id = message.data.get("user_id")
        if user_id:
            await self.authenticate_connection(connection_id, user_id)
            
            response = WebSocketMessage(
                type="auth_success",
                data={"authenticated": True},
                timestamp=message.timestamp,
            )
            await self.send_message(connection_id, response)
    
    async def _handle_project_update(
        self, 
        connection_id: str, 
        message: WebSocketMessage
    ) -> None:
        """Handle project update message.
        
        Args:
            connection_id: Connection ID
            message: Project update message
        """
        if not message.project_id:
            return
        
        # Broadcast update to all project connections except sender
        await self.broadcast_to_project(
            message.project_id, 
            message, 
            exclude_connection=connection_id
        )
    
    async def _handle_collaboration_message(
        self, 
        connection_id: str, 
        message: WebSocketMessage
    ) -> None:
        """Handle collaboration message.
        
        Args:
            connection_id: Connection ID
            message: Collaboration message
        """
        if not message.project_id:
            return
        
        # Broadcast collaboration event to all project connections
        await self.broadcast_to_project(message.project_id, message)
    
    async def _handle_ping_message(
        self, 
        connection_id: str, 
        message: WebSocketMessage
    ) -> None:
        """Handle ping message.
        
        Args:
            connection_id: Connection ID
            message: Ping message
        """
        pong_message = WebSocketMessage(
            type="pong",
            data={"timestamp": message.timestamp},
            timestamp=message.timestamp,
        )
        await self.send_message(connection_id, pong_message)
    
    async def websocket_endpoint(self, websocket: WebSocket, project_id: str) -> None:
        """WebSocket endpoint handler.
        
        Args:
            websocket: WebSocket connection
            project_id: Project ID
        """
        connection_id = await self.connect(websocket, project_id)
        
        try:
            while True:
                # Receive message
                data = await websocket.receive_text()
                message_data = json.loads(data)
                
                # Handle message
                await self.handle_message(connection_id, message_data)
        
        except WebSocketDisconnect:
            logger.info(f"WebSocket disconnected: {connection_id}")
        except Exception as e:
            logger.error(f"WebSocket error: {e}")
        finally:
            self.disconnect(connection_id)
    
    def get_connection_count(self, project_id: str | None = None) -> int:
        """Get the number of active connections.
        
        Args:
            project_id: Optional project ID to filter by
            
        Returns:
            Number of active connections
        """
        if project_id:
            return len(self.project_connections.get(project_id, set()))
        return len(self.connections)
    
    def get_project_users(self, project_id: str) -> list[str]:
        """Get list of users connected to a project.
        
        Args:
            project_id: Project ID
            
        Returns:
            List of user IDs
        """
        project_connections = self.project_connections.get(project_id, set())
        users = set()
        
        for connection_id in project_connections:
            connection_info = self.connections.get(connection_id)
            if connection_info and connection_info.user_id:
                users.add(connection_info.user_id)
        
        return list(users)