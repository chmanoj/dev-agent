"""Command bridge for IDE-to-CLI communication."""

from __future__ import annotations

import asyncio
import json
import logging
import socket
import threading
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional

from dev_agent.plugins.models import Command, FileEvent

logger = logging.getLogger(__name__)


class CommandBridge:
    """Bridge for communication between IDE plugins and dev-agent CLI."""
    
    def __init__(self, port: int = 8765) -> None:
        """Initialize the command bridge.
        
        Args:
            port: Port to listen on for connections
        """
        self.port = port
        self.server_socket: Optional[socket.socket] = None
        self.clients: List[socket.socket] = []
        self.command_handlers: Dict[str, Callable] = {}
        self.event_handlers: Dict[str, List[Callable]] = {}
        self.is_running = False
        self._server_thread: Optional[threading.Thread] = None
    
    def start(self) -> bool:
        """Start the command bridge server.
        
        Returns:
            True if server started successfully
        """
        try:
            self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            self.server_socket.bind(("localhost", self.port))
            self.server_socket.listen(5)
            
            self.is_running = True
            self._server_thread = threading.Thread(target=self._server_loop, daemon=True)
            self._server_thread.start()
            
            logger.info(f"Command bridge started on port {self.port}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to start command bridge: {e}")
            return False
    
    def stop(self) -> None:
        """Stop the command bridge server."""
        self.is_running = False
        
        if self.server_socket:
            self.server_socket.close()
        
        for client in self.clients:
            client.close()
        
        self.clients.clear()
        logger.info("Command bridge stopped")
    
    def register_command_handler(self, command_id: str, handler: Callable) -> None:
        """Register a command handler.
        
        Args:
            command_id: ID of the command
            handler: Function to handle the command
        """
        self.command_handlers[command_id] = handler
        logger.debug(f"Registered command handler: {command_id}")
    
    def register_event_handler(self, event_type: str, handler: Callable) -> None:
        """Register an event handler.
        
        Args:
            event_type: Type of event to handle
            handler: Function to handle the event
        """
        if event_type not in self.event_handlers:
            self.event_handlers[event_type] = []
        
        self.event_handlers[event_type].append(handler)
        logger.debug(f"Registered event handler for: {event_type}")
    
    def send_to_ide(self, message: Dict[str, Any]) -> None:
        """Send a message to connected IDE clients.
        
        Args:
            message: Message to send
        """
        message_json = json.dumps(message) + "\n"
        message_bytes = message_json.encode("utf-8")
        
        disconnected_clients = []
        
        for client in self.clients:
            try:
                client.send(message_bytes)
            except Exception as e:
                logger.warning(f"Failed to send message to client: {e}")
                disconnected_clients.append(client)
        
        # Remove disconnected clients
        for client in disconnected_clients:
            self.clients.remove(client)
            client.close()
    
    def _server_loop(self) -> None:
        """Main server loop."""
        while self.is_running and self.server_socket:
            try:
                client_socket, address = self.server_socket.accept()
                self.clients.append(client_socket)
                
                # Start client handler thread
                client_thread = threading.Thread(
                    target=self._handle_client,
                    args=(client_socket,),
                    daemon=True,
                )
                client_thread.start()
                
                logger.info(f"New client connected: {address}")
                
            except Exception as e:
                if self.is_running:
                    logger.error(f"Error in server loop: {e}")
    
    def _handle_client(self, client_socket: socket.socket) -> None:
        """Handle messages from a client.
        
        Args:
            client_socket: Client socket
        """
        buffer = ""
        
        while self.is_running:
            try:
                data = client_socket.recv(1024).decode("utf-8")
                if not data:
                    break
                
                buffer += data
                
                # Process complete messages (newline-delimited)
                while "\n" in buffer:
                    line, buffer = buffer.split("\n", 1)
                    if line.strip():
                        self._process_message(line.strip())
                
            except Exception as e:
                logger.warning(f"Error handling client: {e}")
                break
        
        # Clean up
        if client_socket in self.clients:
            self.clients.remove(client_socket)
        client_socket.close()
    
    def _process_message(self, message: str) -> None:
        """Process a message from the IDE.
        
        Args:
            message: JSON message string
        """
        try:
            data = json.loads(message)
            message_type = data.get("type")
            
            if message_type == "command":
                self._handle_command(data)
            elif message_type == "event":
                self._handle_event(data)
            else:
                logger.warning(f"Unknown message type: {message_type}")
                
        except Exception as e:
            logger.error(f"Error processing message: {e}")
    
    def _handle_command(self, data: Dict[str, Any]) -> None:
        """Handle a command from the IDE.
        
        Args:
            data: Command data
        """
        command_id = data.get("command_id")
        args = data.get("args", {})
        
        if command_id in self.command_handlers:
            try:
                result = self.command_handlers[command_id](**args)
                
                # Send response back to IDE
                response = {
                    "type": "command_response",
                    "command_id": command_id,
                    "success": True,
                    "result": result,
                }
                self.send_to_ide(response)
                
            except Exception as e:
                logger.error(f"Error executing command {command_id}: {e}")
                
                # Send error response
                response = {
                    "type": "command_response",
                    "command_id": command_id,
                    "success": False,
                    "error": str(e),
                }
                self.send_to_ide(response)
        else:
            logger.warning(f"No handler for command: {command_id}")
    
    def _handle_event(self, data: Dict[str, Any]) -> None:
        """Handle an event from the IDE.
        
        Args:
            data: Event data
        """
        event_type = data.get("event_type")
        event_data = data.get("data", {})
        
        if event_type in self.event_handlers:
            for handler in self.event_handlers[event_type]:
                try:
                    handler(event_data)
                except Exception as e:
                    logger.error(f"Error in event handler for {event_type}: {e}")


class IDECommunicator:
    """Handles communication with specific IDE types."""
    
    def __init__(self, bridge: CommandBridge) -> None:
        """Initialize the IDE communicator.
        
        Args:
            bridge: Command bridge instance
        """
        self.bridge = bridge
    
    def send_suggestion(self, suggestion_data: Dict[str, Any]) -> None:
        """Send a code suggestion to the IDE.
        
        Args:
            suggestion_data: Suggestion data
        """
        message = {
            "type": "suggestion",
            "data": suggestion_data,
        }
        self.bridge.send_to_ide(message)
    
    def send_notification(self, title: str, message: str, level: str = "info") -> None:
        """Send a notification to the IDE.
        
        Args:
            title: Notification title
            message: Notification message
            level: Notification level (info, warning, error)
        """
        notification = {
            "type": "notification",
            "data": {
                "title": title,
                "message": message,
                "level": level,
            },
        }
        self.bridge.send_to_ide(notification)
    
    def request_file_content(self, file_path: Path) -> None:
        """Request file content from the IDE.
        
        Args:
            file_path: Path to the file
        """
        request = {
            "type": "file_request",
            "data": {
                "file_path": str(file_path),
            },
        }
        self.bridge.send_to_ide(request)
    
    def send_progress_update(self, task_id: str, progress: float, message: str) -> None:
        """Send a progress update to the IDE.
        
        Args:
            task_id: ID of the task
            progress: Progress percentage (0-100)
            message: Progress message
        """
        update = {
            "type": "progress",
            "data": {
                "task_id": task_id,
                "progress": progress,
                "message": message,
            },
        }
        self.bridge.send_to_ide(update)