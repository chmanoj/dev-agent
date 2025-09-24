"""Tests for the command bridge communication system."""

from __future__ import annotations

import json
import socket
import threading
import time
from unittest.mock import Mock, patch

import pytest

from dev_agent.plugins.bridge import CommandBridge, IDECommunicator


class TestCommandBridge:
    """Test cases for CommandBridge class."""
    
    @pytest.fixture
    def command_bridge(self):
        """Create a CommandBridge instance with a test port."""
        return CommandBridge(port=0)  # Use port 0 to get a random available port
    
    def test_initialization(self, command_bridge):
        """Test command bridge initialization."""
        assert command_bridge.port == 0
        assert command_bridge.server_socket is None
        assert command_bridge.clients == []
        assert command_bridge.command_handlers == {}
        assert command_bridge.event_handlers == {}
        assert command_bridge.is_running is False
    
    def test_start_success(self, command_bridge):
        """Test successful command bridge start."""
        result = command_bridge.start()
        
        assert result is True
        assert command_bridge.is_running is True
        assert command_bridge.server_socket is not None
        
        # Clean up
        command_bridge.stop()
    
    def test_start_failure_port_in_use(self):
        """Test command bridge start failure when port is in use."""
        # Create a socket to occupy a port
        blocking_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        blocking_socket.bind(("localhost", 0))
        port = blocking_socket.getsockname()[1]
        blocking_socket.listen(1)
        
        try:
            # Try to start command bridge on the same port
            bridge = CommandBridge(port=port)
            result = bridge.start()
            
            assert result is False
            assert bridge.is_running is False
        finally:
            blocking_socket.close()
    
    def test_stop(self, command_bridge):
        """Test command bridge stop."""
        # Start first
        command_bridge.start()
        assert command_bridge.is_running is True
        
        # Stop
        command_bridge.stop()
        assert command_bridge.is_running is False
        assert command_bridge.server_socket is None or command_bridge.server_socket.fileno() == -1
    
    def test_register_command_handler(self, command_bridge):
        """Test registering command handlers."""
        handler = Mock()
        command_bridge.register_command_handler("test_command", handler)
        
        assert "test_command" in command_bridge.command_handlers
        assert command_bridge.command_handlers["test_command"] == handler
    
    def test_register_event_handler(self, command_bridge):
        """Test registering event handlers."""
        handler = Mock()
        command_bridge.register_event_handler("test_event", handler)
        
        assert "test_event" in command_bridge.event_handlers
        assert handler in command_bridge.event_handlers["test_event"]
    
    def test_register_multiple_event_handlers(self, command_bridge):
        """Test registering multiple handlers for the same event."""
        handler1 = Mock()
        handler2 = Mock()
        
        command_bridge.register_event_handler("test_event", handler1)
        command_bridge.register_event_handler("test_event", handler2)
        
        assert len(command_bridge.event_handlers["test_event"]) == 2
        assert handler1 in command_bridge.event_handlers["test_event"]
        assert handler2 in command_bridge.event_handlers["test_event"]
    
    def test_send_to_ide_no_clients(self, command_bridge):
        """Test sending message when no clients are connected."""
        message = {"type": "test", "data": "hello"}
        
        # Should not raise an exception
        command_bridge.send_to_ide(message)
    
    @patch('socket.socket')
    def test_send_to_ide_with_clients(self, mock_socket_class, command_bridge):
        """Test sending message to connected clients."""
        # Create mock client sockets
        mock_client1 = Mock()
        mock_client2 = Mock()
        
        command_bridge.clients = [mock_client1, mock_client2]
        
        message = {"type": "test", "data": "hello"}
        command_bridge.send_to_ide(message)
        
        expected_message = json.dumps(message) + "\n"
        expected_bytes = expected_message.encode("utf-8")
        
        mock_client1.send.assert_called_once_with(expected_bytes)
        mock_client2.send.assert_called_once_with(expected_bytes)
    
    def test_process_command_message(self, command_bridge):
        """Test processing command messages."""
        # Register a command handler
        handler = Mock(return_value="test_result")
        command_bridge.register_command_handler("test_command", handler)
        
        # Mock send_to_ide to capture response
        command_bridge.send_to_ide = Mock()
        
        # Process command message
        message = {
            "type": "command",
            "command_id": "test_command",
            "args": {"param1": "value1"}
        }
        
        command_bridge._process_message(json.dumps(message))
        
        # Check that handler was called
        handler.assert_called_once_with(param1="value1")
        
        # Check that response was sent
        command_bridge.send_to_ide.assert_called_once()
        response = command_bridge.send_to_ide.call_args[0][0]
        assert response["type"] == "command_response"
        assert response["command_id"] == "test_command"
        assert response["success"] is True
        assert response["result"] == "test_result"
    
    def test_process_command_message_handler_error(self, command_bridge):
        """Test processing command message when handler raises an error."""
        # Register a command handler that raises an error
        handler = Mock(side_effect=Exception("Test error"))
        command_bridge.register_command_handler("test_command", handler)
        
        # Mock send_to_ide to capture response
        command_bridge.send_to_ide = Mock()
        
        # Process command message
        message = {
            "type": "command",
            "command_id": "test_command",
            "args": {}
        }
        
        command_bridge._process_message(json.dumps(message))
        
        # Check that error response was sent
        command_bridge.send_to_ide.assert_called_once()
        response = command_bridge.send_to_ide.call_args[0][0]
        assert response["type"] == "command_response"
        assert response["command_id"] == "test_command"
        assert response["success"] is False
        assert "Test error" in response["error"]
    
    def test_process_command_message_no_handler(self, command_bridge):
        """Test processing command message when no handler is registered."""
        # Mock send_to_ide to capture any response
        command_bridge.send_to_ide = Mock()
        
        # Process command message for non-existent command
        message = {
            "type": "command",
            "command_id": "nonexistent_command",
            "args": {}
        }
        
        command_bridge._process_message(json.dumps(message))
        
        # Should not send any response for unknown commands
        command_bridge.send_to_ide.assert_not_called()
    
    def test_process_event_message(self, command_bridge):
        """Test processing event messages."""
        # Register event handlers
        handler1 = Mock()
        handler2 = Mock()
        command_bridge.register_event_handler("test_event", handler1)
        command_bridge.register_event_handler("test_event", handler2)
        
        # Process event message
        message = {
            "type": "event",
            "event_type": "test_event",
            "data": {"key": "value"}
        }
        
        command_bridge._process_message(json.dumps(message))
        
        # Check that both handlers were called
        handler1.assert_called_once_with({"key": "value"})
        handler2.assert_called_once_with({"key": "value"})
    
    def test_process_event_message_handler_error(self, command_bridge):
        """Test processing event message when handler raises an error."""
        # Register event handlers, one that raises an error
        handler1 = Mock(side_effect=Exception("Handler error"))
        handler2 = Mock()
        command_bridge.register_event_handler("test_event", handler1)
        command_bridge.register_event_handler("test_event", handler2)
        
        # Process event message
        message = {
            "type": "event",
            "event_type": "test_event",
            "data": {"key": "value"}
        }
        
        # Should not raise an exception
        command_bridge._process_message(json.dumps(message))
        
        # Both handlers should have been called
        handler1.assert_called_once_with({"key": "value"})
        handler2.assert_called_once_with({"key": "value"})
    
    def test_process_invalid_json(self, command_bridge):
        """Test processing invalid JSON message."""
        # Should not raise an exception
        command_bridge._process_message("invalid json")
    
    def test_process_unknown_message_type(self, command_bridge):
        """Test processing message with unknown type."""
        message = {
            "type": "unknown_type",
            "data": "test"
        }
        
        # Should not raise an exception
        command_bridge._process_message(json.dumps(message))


class TestIDECommunicator:
    """Test cases for IDECommunicator class."""
    
    @pytest.fixture
    def mock_bridge(self):
        """Create a mock CommandBridge."""
        return Mock()
    
    @pytest.fixture
    def ide_communicator(self, mock_bridge):
        """Create an IDECommunicator instance."""
        return IDECommunicator(mock_bridge)
    
    def test_initialization(self, ide_communicator, mock_bridge):
        """Test IDE communicator initialization."""
        assert ide_communicator.bridge == mock_bridge
    
    def test_send_suggestion(self, ide_communicator, mock_bridge):
        """Test sending code suggestions."""
        suggestion_data = {
            "id": "test_suggestion",
            "title": "Test Suggestion",
            "code": "print('hello')"
        }
        
        ide_communicator.send_suggestion(suggestion_data)
        
        mock_bridge.send_to_ide.assert_called_once()
        message = mock_bridge.send_to_ide.call_args[0][0]
        assert message["type"] == "suggestion"
        assert message["data"] == suggestion_data
    
    def test_send_notification_info(self, ide_communicator, mock_bridge):
        """Test sending info notification."""
        ide_communicator.send_notification("Test Title", "Test message", "info")
        
        mock_bridge.send_to_ide.assert_called_once()
        message = mock_bridge.send_to_ide.call_args[0][0]
        assert message["type"] == "notification"
        assert message["data"]["title"] == "Test Title"
        assert message["data"]["message"] == "Test message"
        assert message["data"]["level"] == "info"
    
    def test_send_notification_default_level(self, ide_communicator, mock_bridge):
        """Test sending notification with default level."""
        ide_communicator.send_notification("Test Title", "Test message")
        
        mock_bridge.send_to_ide.assert_called_once()
        message = mock_bridge.send_to_ide.call_args[0][0]
        assert message["data"]["level"] == "info"
    
    def test_request_file_content(self, ide_communicator, mock_bridge):
        """Test requesting file content."""
        from pathlib import Path
        file_path = Path("/test/file.py")
        
        ide_communicator.request_file_content(file_path)
        
        mock_bridge.send_to_ide.assert_called_once()
        message = mock_bridge.send_to_ide.call_args[0][0]
        assert message["type"] == "file_request"
        assert message["data"]["file_path"] == str(file_path)
    
    def test_send_progress_update(self, ide_communicator, mock_bridge):
        """Test sending progress updates."""
        ide_communicator.send_progress_update("task_123", 75.5, "Processing files...")
        
        mock_bridge.send_to_ide.assert_called_once()
        message = mock_bridge.send_to_ide.call_args[0][0]
        assert message["type"] == "progress"
        assert message["data"]["task_id"] == "task_123"
        assert message["data"]["progress"] == 75.5
        assert message["data"]["message"] == "Processing files..."