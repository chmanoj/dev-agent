"""Collaborative editing and conflict resolution system."""

from __future__ import annotations

import logging
from datetime import datetime, timezone
from typing import Any
from uuid import uuid4

from pydantic import BaseModel, Field

from dev_agent.api.websocket_manager import WebSocketManager, WebSocketMessage
from dev_agent.errors.exceptions import CollaborationError

logger = logging.getLogger(__name__)


class EditOperation(BaseModel):
    """Represents a single edit operation."""
    
    id: str = Field(default_factory=lambda: str(uuid4()))
    user_id: str
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    operation_type: str  # "insert", "delete", "replace"
    position: int
    content: str = ""
    length: int = 0  # For delete operations


class DocumentVersion(BaseModel):
    """Represents a version of a document."""
    
    version: int
    content: str
    checksum: str
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    author: str


class CollaborativeDocument(BaseModel):
    """Represents a document being collaboratively edited."""
    
    id: str
    project_id: str
    file_path: str
    current_version: int = 0
    content: str = ""
    checksum: str = ""
    locked_by: str | None = None
    locked_at: datetime | None = None
    versions: list[DocumentVersion] = Field(default_factory=list)
    pending_operations: list[EditOperation] = Field(default_factory=list)
    active_editors: set[str] = Field(default_factory=set)


class ConflictResolution(BaseModel):
    """Represents a conflict resolution strategy."""
    
    conflict_id: str
    strategy: str  # "merge", "overwrite", "manual"
    resolved_content: str
    resolver_id: str
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class CollaborationSession(BaseModel):
    """Represents an active collaboration session."""
    
    id: str = Field(default_factory=lambda: str(uuid4()))
    project_id: str
    participants: set[str] = Field(default_factory=set)
    documents: dict[str, CollaborativeDocument] = Field(default_factory=dict)
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    last_activity: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class CollaborationEngine:
    """Engine for managing collaborative editing and conflict resolution."""
    
    def __init__(self, websocket_manager: WebSocketManager) -> None:
        """Initialize the collaboration engine.
        
        Args:
            websocket_manager: WebSocket manager for real-time updates
        """
        self.websocket_manager = websocket_manager
        
        # Active collaboration sessions
        self.sessions: dict[str, CollaborationSession] = {}
        
        # Document locks
        self.document_locks: dict[str, str] = {}  # document_id -> user_id
    
    def create_session(self, project_id: str, user_id: str) -> CollaborationSession:
        """Create a new collaboration session.
        
        Args:
            project_id: Project ID
            user_id: User ID creating the session
            
        Returns:
            Created collaboration session
        """
        session = CollaborationSession(
            project_id=project_id,
            participants={user_id},
        )
        
        self.sessions[session.id] = session
        
        logger.info(f"Created collaboration session {session.id} for project {project_id}")
        return session
    
    def join_session(self, session_id: str, user_id: str) -> CollaborationSession:
        """Join an existing collaboration session.
        
        Args:
            session_id: Session ID
            user_id: User ID joining the session
            
        Returns:
            Collaboration session
            
        Raises:
            CollaborationError: If session not found
        """
        if session_id not in self.sessions:
            raise CollaborationError(f"Collaboration session {session_id} not found")
        
        session = self.sessions[session_id]
        session.participants.add(user_id)
        session.last_activity = datetime.now(timezone.utc)
        
        # Notify other participants
        self._broadcast_session_event(
            session_id,
            "user_joined",
            {"user_id": user_id},
            exclude_user=user_id,
        )
        
        logger.info(f"User {user_id} joined collaboration session {session_id}")
        return session
    
    def leave_session(self, session_id: str, user_id: str) -> None:
        """Leave a collaboration session.
        
        Args:
            session_id: Session ID
            user_id: User ID leaving the session
        """
        if session_id not in self.sessions:
            return
        
        session = self.sessions[session_id]
        session.participants.discard(user_id)
        
        # Release any document locks held by this user
        for doc_id, document in session.documents.items():
            if document.locked_by == user_id:
                self.release_document_lock(session_id, doc_id, user_id)
            document.active_editors.discard(user_id)
        
        # Notify other participants
        self._broadcast_session_event(
            session_id,
            "user_left",
            {"user_id": user_id},
            exclude_user=user_id,
        )
        
        # Clean up empty session
        if not session.participants:
            del self.sessions[session_id]
            logger.info(f"Deleted empty collaboration session {session_id}")
        
        logger.info(f"User {user_id} left collaboration session {session_id}")
    
    def add_document(
        self,
        session_id: str,
        file_path: str,
        content: str,
        user_id: str,
    ) -> CollaborativeDocument:
        """Add a document to a collaboration session.
        
        Args:
            session_id: Session ID
            file_path: File path
            content: Document content
            user_id: User ID adding the document
            
        Returns:
            Collaborative document
            
        Raises:
            CollaborationError: If session not found
        """
        if session_id not in self.sessions:
            raise CollaborationError(f"Collaboration session {session_id} not found")
        
        session = self.sessions[session_id]
        
        document = CollaborativeDocument(
            id=str(uuid4()),
            project_id=session.project_id,
            file_path=file_path,
            content=content,
            checksum=self._calculate_checksum(content),
        )
        
        # Create initial version
        initial_version = DocumentVersion(
            version=0,
            content=content,
            checksum=document.checksum,
            author=user_id,
        )
        document.versions.append(initial_version)
        
        session.documents[document.id] = document
        session.last_activity = datetime.now(timezone.utc)
        
        # Notify participants
        self._broadcast_session_event(
            session_id,
            "document_added",
            {
                "document_id": document.id,
                "file_path": file_path,
                "user_id": user_id,
            },
        )
        
        logger.info(f"Added document {file_path} to collaboration session {session_id}")
        return document
    
    def apply_edit_operation(
        self,
        session_id: str,
        document_id: str,
        operation: EditOperation,
    ) -> CollaborativeDocument:
        """Apply an edit operation to a document.
        
        Args:
            session_id: Session ID
            document_id: Document ID
            operation: Edit operation to apply
            
        Returns:
            Updated collaborative document
            
        Raises:
            CollaborationError: If session or document not found
        """
        if session_id not in self.sessions:
            raise CollaborationError(f"Collaboration session {session_id} not found")
        
        session = self.sessions[session_id]
        
        if document_id not in session.documents:
            raise CollaborationError(f"Document {document_id} not found in session")
        
        document = session.documents[document_id]
        
        # Check if document is locked by another user
        if document.locked_by and document.locked_by != operation.user_id:
            raise CollaborationError(
                f"Document is locked by user {document.locked_by}"
            )
        
        # Apply the operation
        try:
            new_content = self._apply_operation(document.content, operation)
            
            # Update document
            document.content = new_content
            document.checksum = self._calculate_checksum(new_content)
            document.current_version += 1
            document.active_editors.add(operation.user_id)
            
            # Create new version
            new_version = DocumentVersion(
                version=document.current_version,
                content=new_content,
                checksum=document.checksum,
                author=operation.user_id,
            )
            document.versions.append(new_version)
            
            # Keep only last 10 versions
            if len(document.versions) > 10:
                document.versions = document.versions[-10:]
            
            session.last_activity = datetime.now(timezone.utc)
            
            # Broadcast operation to other participants
            self._broadcast_session_event(
                session_id,
                "document_edited",
                {
                    "document_id": document_id,
                    "operation": operation.model_dump(),
                    "new_version": document.current_version,
                    "checksum": document.checksum,
                },
                exclude_user=operation.user_id,
            )
            
            logger.info(
                f"Applied {operation.operation_type} operation to document {document_id}"
            )
            return document
        
        except Exception as e:
            raise CollaborationError(f"Failed to apply operation: {e}") from e
    
    def lock_document(
        self,
        session_id: str,
        document_id: str,
        user_id: str,
    ) -> bool:
        """Lock a document for exclusive editing.
        
        Args:
            session_id: Session ID
            document_id: Document ID
            user_id: User ID requesting the lock
            
        Returns:
            True if lock acquired, False if already locked
            
        Raises:
            CollaborationError: If session or document not found
        """
        if session_id not in self.sessions:
            raise CollaborationError(f"Collaboration session {session_id} not found")
        
        session = self.sessions[session_id]
        
        if document_id not in session.documents:
            raise CollaborationError(f"Document {document_id} not found in session")
        
        document = session.documents[document_id]
        
        # Check if already locked
        if document.locked_by and document.locked_by != user_id:
            return False
        
        # Acquire lock
        document.locked_by = user_id
        document.locked_at = datetime.now(timezone.utc)
        
        # Broadcast lock event
        self._broadcast_session_event(
            session_id,
            "document_locked",
            {
                "document_id": document_id,
                "locked_by": user_id,
            },
            exclude_user=user_id,
        )
        
        logger.info(f"Document {document_id} locked by user {user_id}")
        return True
    
    def release_document_lock(
        self,
        session_id: str,
        document_id: str,
        user_id: str,
    ) -> bool:
        """Release a document lock.
        
        Args:
            session_id: Session ID
            document_id: Document ID
            user_id: User ID releasing the lock
            
        Returns:
            True if lock released, False if not locked by user
            
        Raises:
            CollaborationError: If session or document not found
        """
        if session_id not in self.sessions:
            raise CollaborationError(f"Collaboration session {session_id} not found")
        
        session = self.sessions[session_id]
        
        if document_id not in session.documents:
            raise CollaborationError(f"Document {document_id} not found in session")
        
        document = session.documents[document_id]
        
        # Check if locked by this user
        if document.locked_by != user_id:
            return False
        
        # Release lock
        document.locked_by = None
        document.locked_at = None
        
        # Broadcast unlock event
        self._broadcast_session_event(
            session_id,
            "document_unlocked",
            {
                "document_id": document_id,
                "unlocked_by": user_id,
            },
            exclude_user=user_id,
        )
        
        logger.info(f"Document {document_id} unlocked by user {user_id}")
        return True
    
    def resolve_conflict(
        self,
        session_id: str,
        document_id: str,
        resolution: ConflictResolution,
    ) -> CollaborativeDocument:
        """Resolve a document conflict.
        
        Args:
            session_id: Session ID
            document_id: Document ID
            resolution: Conflict resolution
            
        Returns:
            Updated collaborative document
            
        Raises:
            CollaborationError: If session or document not found
        """
        if session_id not in self.sessions:
            raise CollaborationError(f"Collaboration session {session_id} not found")
        
        session = self.sessions[session_id]
        
        if document_id not in session.documents:
            raise CollaborationError(f"Document {document_id} not found in session")
        
        document = session.documents[document_id]
        
        # Apply resolution
        document.content = resolution.resolved_content
        document.checksum = self._calculate_checksum(resolution.resolved_content)
        document.current_version += 1
        
        # Create new version
        new_version = DocumentVersion(
            version=document.current_version,
            content=resolution.resolved_content,
            checksum=document.checksum,
            author=resolution.resolver_id,
        )
        document.versions.append(new_version)
        
        # Clear pending operations
        document.pending_operations.clear()
        
        session.last_activity = datetime.now(timezone.utc)
        
        # Broadcast resolution
        self._broadcast_session_event(
            session_id,
            "conflict_resolved",
            {
                "document_id": document_id,
                "resolution_strategy": resolution.strategy,
                "resolver_id": resolution.resolver_id,
                "new_version": document.current_version,
            },
        )
        
        logger.info(f"Resolved conflict for document {document_id}")
        return document
    
    def _apply_operation(self, content: str, operation: EditOperation) -> str:
        """Apply an edit operation to content.
        
        Args:
            content: Original content
            operation: Edit operation
            
        Returns:
            Modified content
            
        Raises:
            CollaborationError: If operation is invalid
        """
        if operation.operation_type == "insert":
            if operation.position > len(content):
                raise CollaborationError("Insert position out of bounds")
            return content[:operation.position] + operation.content + content[operation.position:]
        
        elif operation.operation_type == "delete":
            if operation.position + operation.length > len(content):
                raise CollaborationError("Delete range out of bounds")
            return content[:operation.position] + content[operation.position + operation.length:]
        
        elif operation.operation_type == "replace":
            if operation.position + operation.length > len(content):
                raise CollaborationError("Replace range out of bounds")
            return (
                content[:operation.position] + 
                operation.content + 
                content[operation.position + operation.length:]
            )
        
        else:
            raise CollaborationError(f"Unknown operation type: {operation.operation_type}")
    
    def _calculate_checksum(self, content: str) -> str:
        """Calculate checksum for content.
        
        Args:
            content: Content to checksum
            
        Returns:
            Checksum string
        """
        import hashlib
        return hashlib.md5(content.encode()).hexdigest()
    
    async def _broadcast_session_event(
        self,
        session_id: str,
        event_type: str,
        data: dict[str, Any],
        exclude_user: str | None = None,
    ) -> None:
        """Broadcast an event to all session participants.
        
        Args:
            session_id: Session ID
            event_type: Event type
            data: Event data
            exclude_user: User ID to exclude from broadcast
        """
        if session_id not in self.sessions:
            return
        
        session = self.sessions[session_id]
        
        message = WebSocketMessage(
            type="collaboration",
            data={
                "event_type": event_type,
                "session_id": session_id,
                **data,
            },
            timestamp=datetime.now(timezone.utc).isoformat(),
        )
        
        # Broadcast to project (all session participants should be connected to the project)
        await self.websocket_manager.broadcast_to_project(
            session.project_id,
            message,
        )
    
    def get_session_info(self, session_id: str) -> dict[str, Any]:
        """Get information about a collaboration session.
        
        Args:
            session_id: Session ID
            
        Returns:
            Session information
            
        Raises:
            CollaborationError: If session not found
        """
        if session_id not in self.sessions:
            raise CollaborationError(f"Collaboration session {session_id} not found")
        
        session = self.sessions[session_id]
        
        return {
            "id": session.id,
            "project_id": session.project_id,
            "participants": list(session.participants),
            "document_count": len(session.documents),
            "created_at": session.created_at.isoformat(),
            "last_activity": session.last_activity.isoformat(),
        }
    
    def get_active_sessions(self, project_id: str | None = None) -> list[dict[str, Any]]:
        """Get list of active collaboration sessions.
        
        Args:
            project_id: Optional project ID to filter by
            
        Returns:
            List of session information
        """
        sessions = []
        
        for session in self.sessions.values():
            if project_id and session.project_id != project_id:
                continue
            
            sessions.append(self.get_session_info(session.id))
        
        return sessions