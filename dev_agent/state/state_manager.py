"""State management for project state persistence and recovery."""

import asyncio
import json
import logging
import os
import tempfile
from dataclasses import asdict, is_dataclass
from datetime import datetime
from pathlib import Path
from typing import Any

from rich.console import Console
from rich.panel import Panel

from ..errors.exceptions import (
    DatetimeDeserializationError,
    DatetimeSerializationError,
    ErrorCategory,
    ErrorContext,
    ErrorSeverity,
    StateLoadingError,
    StateSavingError,
)
from ..llm import ILLMClient, create_llm_client
from ..models.documents import DesignDocument, SpecificationDocument, TaskList
from ..models.enums import DocumentType, PhaseType, TaskStatus
from ..models.project_state import IndexMetadata, ProjectState, SessionData
from ..performance.monitor import PerformanceMonitor

logger = logging.getLogger(__name__)
console = Console()

# Global performance monitor for state operations
_perf_monitor = PerformanceMonitor()


class StateManager:
    """Manages project state persistence and document storage."""

    def __init__(
        self,
        project_path: str,
        enable_recovery: bool = False,
        llm_client: ILLMClient | None = None,
    ):
        """Initialize StateManager for a specific project.

        Args:
            project_path: Path to the project directory
            enable_recovery: Whether to enable automatic state recovery (default: False for testing compatibility)
            llm_client: Optional LLM client for spec folder naming
        """
        self.project_path = Path(project_path)
        self.dev_agent_dir = self.project_path / ".dev_agent"
        self.state_file = self.dev_agent_dir / "state.json"
        self.documents_dir = self.dev_agent_dir / "documents"
        self.enable_recovery = enable_recovery
        self.llm_client = llm_client

        # Ensure directories exist
        self._ensure_directories()

    def _ensure_directories(self) -> None:
        """Create necessary directories if they don't exist."""
        self.dev_agent_dir.mkdir(exist_ok=True)
        self.documents_dir.mkdir(exist_ok=True)

    def _display_error_panel(self, title: str, message: str, style: str = "red") -> None:
        """Display an error panel to the user using Rich.
        
        Args:
            title: Panel title
            message: Error message to display
            style: Panel border style (red, yellow, etc.)
        """
        try:
            console.print()
            console.print(
                Panel(
                    message,
                    title=title,
                    border_style=style,
                    expand=False
                )
            )
            console.print()
        except Exception as e:
            # Fallback to simple print if Rich fails
            logger.warning(f"Failed to display Rich panel: {e}")
            print(f"\n{title}")
            print(f"{message}\n")

    def _serialize_dataclass(self, obj: Any, field_path: str = "") -> Any:
        """Recursively serialize dataclass objects to dictionaries.
        
        Handles datetime objects FIRST before other type checks to ensure
        proper serialization to ISO format strings. This is critical for
        JSON serialization across all document types.
        
        Args:
            obj: Object to serialize
            field_path: Current field path for error context (e.g., "specification.approval_timestamp")
            
        Returns:
            Serialized object
            
        Raises:
            DatetimeSerializationError: If datetime serialization fails
        """
        try:
            # Debug logging for specification objects
            if field_path == "specification" or "specification" in field_path:
                logger.debug(f"Serializing specification object at path '{field_path}': {type(obj)}")
                if obj is not None:
                    logger.debug(f"Specification object is not None: {hasattr(obj, 'to_dict')}")
            
            # Check datetime FIRST before other type checks
            if isinstance(obj, datetime):
                try:
                    return obj.isoformat()
                except Exception as e:
                    logger.error(
                        f"Failed to serialize datetime at path '{field_path}': {e}",
                        exc_info=True,
                        extra={
                            "field_path": field_path,
                            "datetime_value": str(obj),
                            "operation": "datetime_serialization"
                        }
                    )
                    raise DatetimeSerializationError(
                        message=f"Cannot serialize datetime to ISO format: {e}",
                        field_name=field_path.split('.')[-1] if field_path else None,
                        field_path=field_path,
                        datetime_value=str(obj),
                        context=ErrorContext(
                            operation="serialize_datetime",
                            additional_info={"field_path": field_path, "datetime_value": str(obj)}
                        )
                    ) from e
            elif hasattr(obj, "value"):  # Handle enums
                return obj.value
            elif is_dataclass(obj):
                # Debug logging for SpecificationDocument
                if type(obj).__name__ == 'SpecificationDocument':
                    logger.info(f"🔍 Found SpecificationDocument at path '{field_path}'")
                    logger.info(f"🔍 Has to_dict: {hasattr(obj, 'to_dict')}")
                    logger.info(f"🔍 to_dict callable: {callable(getattr(obj, 'to_dict', None))}")
                
                # Check if the object has a custom to_dict method
                if hasattr(obj, 'to_dict') and callable(getattr(obj, 'to_dict')):
                    try:
                        logger.debug(f"Using to_dict() for {type(obj).__name__} at path '{field_path}'")
                        result = obj.to_dict()
                        logger.debug(f"to_dict() succeeded for {type(obj).__name__}, result type: {type(result)}")
                        if type(obj).__name__ == 'SpecificationDocument':
                            logger.info(f"✅ SpecificationDocument serialized successfully")
                        return result
                    except Exception as e:
                        logger.error(
                            f"Failed to serialize using to_dict() at path '{field_path}': {e}",
                            exc_info=True,
                            extra={
                                "field_path": field_path,
                                "object_type": type(obj).__name__,
                                "operation": "to_dict_serialization"
                            }
                        )
                        # Fall back to manual serialization
                
                # Manually iterate through fields to maintain recursive handling
                result = {}
                for field_name, field_value in asdict(obj).items():
                    current_path = f"{field_path}.{field_name}" if field_path else field_name
                    try:
                        result[field_name] = self._serialize_dataclass(field_value, current_path)
                    except DatetimeSerializationError:
                        # Re-raise datetime errors with proper context
                        raise
                    except Exception as e:
                        logger.error(
                            f"Failed to serialize field '{field_name}' at path '{current_path}': {e}",
                            exc_info=True,
                            extra={
                                "field_name": field_name,
                                "field_path": current_path,
                                "operation": "field_serialization"
                            }
                        )
                        # For non-datetime errors, continue with None value
                        result[field_name] = None
                
                # Ensure approval flags are included with backward compatibility
                # Use getattr() with default False for backward compatibility with older ProjectState objects
                if hasattr(obj, '__class__') and obj.__class__.__name__ == 'ProjectState':
                    result['specification_approved'] = getattr(obj, 'specification_approved', False)
                    result['design_approved'] = getattr(obj, 'design_approved', False)
                    result['tasks_approved'] = getattr(obj, 'tasks_approved', False)
                
                return result
            elif isinstance(obj, list):
                result = []
                for i, item in enumerate(obj):
                    current_path = f"{field_path}[{i}]" if field_path else f"[{i}]"
                    result.append(self._serialize_dataclass(item, current_path))
                return result
            elif isinstance(obj, dict):
                result = {}
                for key, value in obj.items():
                    current_path = f"{field_path}.{key}" if field_path else key
                    result[key] = self._serialize_dataclass(value, current_path)
                return result
            else:
                return obj
        except DatetimeSerializationError:
            # Re-raise datetime errors
            raise
        except Exception as e:
            logger.error(
                f"Unexpected error during serialization at path '{field_path}': {e}",
                exc_info=True,
                extra={
                    "field_path": field_path,
                    "object_type": type(obj).__name__,
                    "operation": "serialization"
                }
            )
            # For unexpected errors, return None to allow partial serialization
            return None

    def _deserialize_datetime(
        self, 
        date_str: str | None, 
        field_name: str | None = None, 
        field_path: str | None = None
    ) -> datetime | None:
        """Deserialize datetime string with multiple parsing strategies.
        
        Args:
            date_str: Datetime string or None
            field_name: Name of the field being deserialized (for error context)
            field_path: Full path to the field (for error context)
            
        Returns:
            datetime object if date_str is not None, otherwise None
            
        Raises:
            DatetimeDeserializationError: If all datetime parsing strategies fail
        """
        if date_str is None:
            return None
        
        # First try the multiple parsing strategies
        result = self._attempt_datetime_parsing_strategies(date_str, field_name or "unknown")
        if result is not None:
            return result
        
        # If all strategies failed, log error and raise exception
        logger.error(
            f"Failed to deserialize datetime from '{date_str}' "
            f"for field '{field_name or 'unknown'}' at path '{field_path or 'unknown'}' "
            f"using all available parsing strategies",
            extra={
                "field_name": field_name,
                "field_path": field_path,
                "datetime_string": date_str,
                "operation": "datetime_deserialization"
            }
        )
        raise DatetimeDeserializationError(
            message=f"Invalid datetime format '{date_str}': all parsing strategies failed",
            field_name=field_name,
            field_path=field_path,
            datetime_string=date_str,
            context=ErrorContext(
                operation="deserialize_datetime",
                additional_info={
                    "field_name": field_name,
                    "field_path": field_path,
                    "datetime_string": date_str
                }
            )
        )

    def _validate_state(self, state: ProjectState) -> list[str]:
        """Validate state consistency for approval tracking.
        
        Performs validation checks to ensure approval consistency:
        - Design phase has approved specification
        - Implementation phase has approved design  
        - Approved content exists (no approval without content)
        
        Args:
            state: ProjectState to validate
            
        Returns:
            List of validation warning messages
        """
        warnings = []
        
        # Check phase consistency - design phase should have approved specification
        if state.current_phase == PhaseType.DESIGN:
            if not state.specification:
                warnings.append("Design phase but no specification content")
            if not getattr(state, 'specification_approved', False):
                warnings.append("Design phase but specification not approved")
        
        # Check phase consistency - implementation phase should have approved design
        if state.current_phase == PhaseType.IMPLEMENTATION:
            if not state.design:
                warnings.append("Implementation phase but no design content")
            if not getattr(state, 'design_approved', False):
                warnings.append("Implementation phase but design not approved")
        
        # Check approval consistency - no approval without content
        if getattr(state, 'specification_approved', False) and not state.specification:
            warnings.append("Specification approved but no content")
        
        if getattr(state, 'design_approved', False) and not state.design:
            warnings.append("Design approved but no content")
        
        if getattr(state, 'tasks_approved', False) and not state.tasks:
            warnings.append("Tasks approved but no content")
        
        return warnings

    async def save_project_state(self, state: ProjectState) -> bool:
        """Save project state to JSON file with optimized performance.
        
        Uses atomic write with temporary file to ensure data integrity
        and optimized JSON serialization for <100ms save operations.

        Args:
            state: ProjectState object to save

        Returns:
            True if successful, False otherwise
            
        Raises:
            StateSavingError: If state saving fails with detailed error information
        """
        with _perf_monitor.measure("state_save", warn_threshold_ms=100):
            try:
                # Update the updated_at timestamp
                state.updated_at = datetime.now()

                # Validate state consistency before saving
                validation_warnings = self._validate_state(state)
                if validation_warnings:
                    logger.warning(
                        f"State validation warnings: {validation_warnings}",
                        extra={
                            "operation": "save_project_state",
                            "phase": "validation",
                            "warnings": validation_warnings,
                            "current_phase": state.current_phase.value if state.current_phase else "unknown"
                        }
                    )

                # Serialize the state with enhanced error handling
                try:
                    state_dict = self._serialize_dataclass(state, "project_state")
                except DatetimeSerializationError as e:
                    logger.error(
                        f"Datetime serialization failed during state save: {e.message}",
                        exc_info=True,
                        extra={
                            "operation": "save_project_state",
                            "phase": "serialization",
                            "field_path": e.field_path,
                            "field_name": e.field_name
                        }
                    )
                    self._display_error_panel(
                        title="❌ State Save Failed - Datetime Error",
                        message=(
                            f"Failed to serialize datetime field '{e.field_name or 'unknown'}'\n"
                            f"Path: {e.field_path or 'unknown'}\n\n"
                            f"Error: {e.message}\n\n"
                            "This may indicate corrupted data in the project state."
                        ),
                        style="red"
                    )
                    raise StateSavingError(
                        message=f"Datetime serialization failed: {e.message}",
                        error_type="serialization_error",
                        file_path=str(self.state_file),
                        context=ErrorContext(
                            operation="save_project_state",
                            file_path=str(self.state_file),
                            phase="serialization"
                        ),
                        original_error=e
                    ) from e
                except Exception as e:
                    logger.error(
                        f"General serialization error during state save: {e}",
                        exc_info=True,
                        extra={
                            "operation": "save_project_state",
                            "phase": "serialization"
                        }
                    )
                    self._display_error_panel(
                        title="❌ State Save Failed - Serialization Error",
                        message=(
                            f"Failed to serialize project state data.\n\n"
                            f"Error: {e}\n\n"
                            "The project state may contain invalid data."
                        ),
                        style="red"
                    )
                    raise StateSavingError(
                        message=f"State serialization failed: {e}",
                        error_type="serialization_error",
                        file_path=str(self.state_file),
                        context=ErrorContext(
                            operation="save_project_state",
                            file_path=str(self.state_file),
                            phase="serialization"
                        ),
                        original_error=e
                    ) from e

                def _sync_write():
                    # Write to temporary file first (atomic operation)
                    try:
                        temp_fd, temp_path = tempfile.mkstemp(
                            dir=self.dev_agent_dir,
                            prefix=".state_",
                            suffix=".json.tmp"
                        )
                    except OSError as e:
                        logger.error(
                            f"Failed to create temporary file for state save: {e}",
                            exc_info=True,
                            extra={
                                "operation": "save_project_state",
                                "phase": "temp_file_creation",
                                "directory": str(self.dev_agent_dir)
                            }
                        )
                        if e.errno == 28:  # No space left on device
                            self._display_error_panel(
                                title="❌ State Save Failed - Disk Full",
                                message=(
                                    f"Insufficient disk space to save project state.\n\n"
                                    f"Directory: {self.dev_agent_dir}\n\n"
                                    "Please free up disk space and try again."
                                ),
                                style="red"
                            )
                            raise StateSavingError(
                                message="Insufficient disk space",
                                error_type="disk_full",
                                file_path=str(self.state_file),
                                context=ErrorContext(
                                    operation="save_project_state",
                                    file_path=str(self.state_file),
                                    phase="temp_file_creation"
                                ),
                                original_error=e
                            ) from e
                        elif e.errno == 13:  # Permission denied
                            self._display_error_panel(
                                title="❌ State Save Failed - Permission Denied",
                                message=(
                                    f"Permission denied creating temporary file.\n\n"
                                    f"Directory: {self.dev_agent_dir}\n\n"
                                    "Check directory permissions and try again."
                                ),
                                style="red"
                            )
                            raise StateSavingError(
                                message="Permission denied creating temporary file",
                                error_type="permission_error",
                                file_path=str(self.state_file),
                                context=ErrorContext(
                                    operation="save_project_state",
                                    file_path=str(self.state_file),
                                    phase="temp_file_creation"
                                ),
                                original_error=e
                            ) from e
                        else:
                            self._display_error_panel(
                                title="❌ State Save Failed - I/O Error",
                                message=(
                                    f"I/O error creating temporary file: {e}\n\n"
                                    f"Directory: {self.dev_agent_dir}\n\n"
                                    "Check disk health and file system integrity."
                                ),
                                style="red"
                            )
                            raise StateSavingError(
                                message=f"I/O error creating temporary file: {e}",
                                error_type="io_error",
                                file_path=str(self.state_file),
                                context=ErrorContext(
                                    operation="save_project_state",
                                    file_path=str(self.state_file),
                                    phase="temp_file_creation"
                                ),
                                original_error=e
                            ) from e
                    
                    try:
                        # Write with minimal formatting for speed (no indent)
                        # Use separators to minimize whitespace
                        with os.fdopen(temp_fd, "w", encoding="utf-8") as f:
                            json.dump(
                                state_dict,
                                f,
                                ensure_ascii=False,
                                separators=(',', ':')  # Compact format for speed
                            )

                        # Atomic rename
                        os.replace(temp_path, self.state_file)

                        logger.info(
                            f"Successfully saved project state to {self.state_file}",
                            extra={
                                "operation": "save_project_state",
                                "file_path": str(self.state_file),
                                "phase": state.current_phase.value if state.current_phase else "unknown"
                            }
                        )

                    except Exception as e:
                        # Clean up temp file on error
                        try:
                            os.unlink(temp_path)
                        except OSError:
                            pass

                        logger.error(
                            f"Failed to write state file: {e}",
                            exc_info=True,
                            extra={
                                "operation": "save_project_state",
                                "phase": "file_write",
                                "temp_path": temp_path,
                                "target_path": str(self.state_file)
                            }
                        )

                        if isinstance(e, OSError):
                            if e.errno == 28:  # No space left on device
                                error_type = "disk_full"
                                title = "❌ State Save Failed - Disk Full"
                                message = (
                                    f"Insufficient disk space to write state file.\n\n"
                                    f"File: {self.state_file}\n\n"
                                    "Please free up disk space and try again."
                                )
                            elif e.errno == 13:  # Permission denied
                                error_type = "permission_error"
                                title = "❌ State Save Failed - Permission Denied"
                                message = (
                                    f"Permission denied writing state file.\n\n"
                                    f"File: {self.state_file}\n\n"
                                    "Check file permissions and try again."
                                )
                            else:
                                error_type = "io_error"
                                title = "❌ State Save Failed - I/O Error"
                                message = (
                                    f"I/O error writing state file: {e}\n\n"
                                    f"File: {self.state_file}\n\n"
                                    "Check disk health and file system integrity."
                                )
                        else:
                            error_type = "io_error"
                            title = "❌ State Save Failed - Write Error"
                            message = (
                                f"Failed to write state file: {e}\n\n"
                                f"File: {self.state_file}\n\n"
                                "Please check the file system and try again."
                            )

                        self._display_error_panel(title=title, message=message, style="red")

                        raise StateSavingError(
                            message=f"Failed to write state file: {e}",
                            error_type=error_type,
                            file_path=str(self.state_file),
                            context=ErrorContext(
                                operation="save_project_state",
                                file_path=str(self.state_file),
                                phase="file_write"
                            ),
                            original_error=e
                        ) from e

                await asyncio.to_thread(_sync_write)
                logger.info("Finished writing to file.")
                return True
                
            except (StateSavingError, DatetimeSerializationError):
                # Re-raise our custom errors
                raise
            except Exception as e:
                logger.error(
                    f"Unexpected error saving project state: {e}",
                    exc_info=True,
                    extra={
                        "operation": "save_project_state",
                        "file_path": str(self.state_file)
                    }
                )
                self._display_error_panel(
                    title="❌ State Save Failed - Unexpected Error",
                    message=(
                        f"An unexpected error occurred while saving project state.\n\n"
                        f"Error: {e}\n\n"
                        "Please check the logs for more details."
                    ),
                    style="red"
                )
                raise StateSavingError(
                    message=f"Unexpected error during state save: {e}",
                    error_type="io_error",
                    file_path=str(self.state_file),
                    context=ErrorContext(
                        operation="save_project_state",
                        file_path=str(self.state_file)
                    ),
                    original_error=e
                ) from e

    def _validate_state_dict(self, state_dict: dict[str, Any]) -> tuple[bool, list[str]]:
        """Validate that state dictionary contains all required fields.
        
        Args:
            state_dict: Dictionary loaded from state file
            
        Returns:
            Tuple of (is_valid, list_of_issues)
        """
        issues = []
        
        # Required top-level fields
        required_fields = [
            "project_path", "current_phase", "indexing_complete",
            "implementation_progress", "session_data", "created_at", "updated_at"
        ]
        
        for field in required_fields:
            if field not in state_dict:
                issues.append(f"Missing required field: {field}")
            elif state_dict[field] is None and field in ["project_path", "current_phase", "session_data"]:
                issues.append(f"Required field '{field}' cannot be None")
        
        # Validate session_data structure if present
        if "session_data" in state_dict and state_dict["session_data"]:
            session_required = ["session_id", "user_approvals", "pending_approvals"]
            for field in session_required:
                if field not in state_dict["session_data"]:
                    issues.append(f"Missing required session_data field: {field}")
        
        # Validate current_phase is valid enum value
        if "current_phase" in state_dict and state_dict["current_phase"]:
            try:
                PhaseType(state_dict["current_phase"])
            except ValueError:
                issues.append(f"Invalid current_phase value: {state_dict['current_phase']}")
        
        # Validate implementation_progress structure
        if "implementation_progress" in state_dict and state_dict["implementation_progress"]:
            if not isinstance(state_dict["implementation_progress"], dict):
                issues.append("implementation_progress must be a dictionary")
        
        return len(issues) == 0, issues

    def _attempt_state_recovery(self, original_error: Exception) -> ProjectState | None:
        """Attempt to recover from corrupted state by creating backup and fresh state.
        
        Args:
            original_error: The original error that triggered recovery
            
        Returns:
            Fresh ProjectState if recovery successful, None otherwise
        """
        try:
            # Create backup of corrupted state file
            backup_path = self.state_file.with_suffix(f".backup.{datetime.now().strftime('%Y%m%d_%H%M%S')}")
            
            if self.state_file.exists():
                try:
                    import shutil
                    shutil.copy2(self.state_file, backup_path)
                    logger.info(
                        f"Created backup of corrupted state file: {backup_path}",
                        extra={
                            "operation": "state_recovery",
                            "backup_path": str(backup_path),
                            "original_file": str(self.state_file)
                        }
                    )
                except Exception as backup_error:
                    logger.warning(
                        f"Failed to create backup during recovery: {backup_error}",
                        extra={
                            "operation": "state_recovery",
                            "phase": "backup_creation",
                            "backup_path": str(backup_path)
                        }
                    )
                    # Continue with recovery even if backup fails
            
            # Create fresh project state
            from ..models.project_state import ProjectState, SessionData
            import uuid
            
            fresh_state = ProjectState(
                project_path=str(self.project_path),
                current_phase=PhaseType.INDEXING,
                indexing_complete=False,
                specification=None,
                design=None,
                tasks=None,
                implementation_progress={},
                index_metadata=None,
                session_data=SessionData(
                    session_id=str(uuid.uuid4()),
                    started_at=datetime.now(),
                    last_activity=datetime.now(),
                    user_approvals=[],
                    pending_approvals=[]
                ),
                created_at=datetime.now(),
                updated_at=datetime.now()
            )
            
            # Save the fresh state
            if self.save_project_state(fresh_state):
                logger.info(
                    "Successfully created fresh project state during recovery",
                    extra={
                        "operation": "state_recovery",
                        "phase": "fresh_state_creation",
                        "backup_created": backup_path.exists()
                    }
                )
                
                # Notify user about recovery
                self._display_error_panel(
                    title="🔄 State Recovery Successful",
                    message=(
                        f"Project state was corrupted and has been recovered.\n\n"
                        f"Original error: {original_error}\n\n"
                        f"Actions taken:\n"
                        f"• Backup created: {backup_path.name if backup_path.exists() else 'Failed'}\n"
                        f"• Fresh state initialized\n"
                        f"• Project reset to indexing phase\n\n"
                        "You can continue with 'dev-agent init' to re-index your project."
                    ),
                    style="yellow"
                )
                
                return fresh_state
            else:
                logger.error(
                    "Failed to save fresh state during recovery",
                    extra={
                        "operation": "state_recovery",
                        "phase": "fresh_state_save"
                    }
                )
                return None
                
        except Exception as recovery_error:
            logger.error(
                f"State recovery failed: {recovery_error}",
                exc_info=True,
                extra={
                    "operation": "state_recovery",
                    "original_error": str(original_error),
                    "recovery_error": str(recovery_error)
                }
            )
            
            # Notify user that recovery failed
            self._display_error_panel(
                title="❌ State Recovery Failed",
                message=(
                    f"Failed to recover from corrupted project state.\n\n"
                    f"Original error: {original_error}\n"
                    f"Recovery error: {recovery_error}\n\n"
                    "Please manually remove the .dev_agent directory and run 'dev-agent init'."
                ),
                style="red"
            )
            return None

    def _attempt_datetime_parsing_strategies(self, date_str: str, field_name: str) -> datetime | None:
        """Attempt multiple parsing strategies for datetime fields.
        
        Args:
            date_str: String to parse as datetime
            field_name: Name of field for logging
            
        Returns:
            Parsed datetime or None if all strategies fail
        """
        if date_str is None:
            return None
        
        # Convert to string if it's a number (timestamp)
        if isinstance(date_str, (int, float)):
            date_str = str(date_str)
        elif not isinstance(date_str, str):
            return None
            
        strategies = [
            # ISO format (primary)
            lambda s: datetime.fromisoformat(s),
            # ISO format with Z suffix
            lambda s: datetime.fromisoformat(s.replace('Z', '+00:00')),
            # Unix timestamp (seconds since epoch)
            lambda s: datetime.fromtimestamp(float(s)),
            # Common formats
            lambda s: datetime.strptime(s, "%Y-%m-%d %H:%M:%S"),
            lambda s: datetime.strptime(s, "%Y-%m-%dT%H:%M:%S"),
            lambda s: datetime.strptime(s, "%Y-%m-%d %H:%M:%S.%f"),
            lambda s: datetime.strptime(s, "%Y-%m-%dT%H:%M:%S.%f"),
        ]
        
        for i, strategy in enumerate(strategies):
            try:
                result = strategy(date_str)
                if i > 0:  # Log if fallback strategy was used
                    logger.info(
                        f"Successfully parsed datetime '{date_str}' for field '{field_name}' using fallback strategy {i}",
                        extra={
                            "operation": "datetime_parsing",
                            "field_name": field_name,
                            "datetime_string": date_str,
                            "strategy_index": i
                        }
                    )
                return result
            except (ValueError, TypeError):
                continue
        
        logger.warning(
            f"All datetime parsing strategies failed for field '{field_name}': '{date_str}'",
            extra={
                "operation": "datetime_parsing",
                "field_name": field_name,
                "datetime_string": date_str,
                "strategies_attempted": len(strategies)
            }
        )
        return None

    def load_project_state(self) -> ProjectState | None:
        """Load project state from JSON file with validation and recovery.

        Returns:
            ProjectState object if successful, None otherwise
            
        Raises:
            StateLoadingError: If state loading fails with detailed error information
        """
        if not self.state_file.exists():
            logger.info(
                f"State file does not exist: {self.state_file}",
                extra={
                    "operation": "load_project_state",
                    "file_path": str(self.state_file),
                    "phase": "file_check"
                }
            )
            return None

        try:
            logger.info(f"Attempting to load state from {self.state_file}")
            # Attempt to read and parse the JSON file
            try:
                with open(self.state_file, encoding="utf-8") as f:
                    state_dict = json.load(f)
                logger.info("Successfully loaded and parsed state file.")
            except FileNotFoundError as e:
                logger.error(
                    f"State file not found: {self.state_file}",
                    exc_info=True,
                    extra={
                        "operation": "load_project_state",
                        "file_path": str(self.state_file),
                        "phase": "file_read"
                    }
                )
                self._display_error_panel(
                    title="❌ Project State Not Found",
                    message=(
                        f"Project state file not found.\n\n"
                        f"Expected location: {self.state_file}\n\n"
                        "Use 'dev-agent init' to initialize a new project."
                    ),
                    style="yellow"
                )
                raise StateLoadingError(
                    message=f"State file not found: {self.state_file}",
                    error_type="missing_file",
                    file_path=str(self.state_file),
                    context=ErrorContext(
                        operation="load_project_state",
                        file_path=str(self.state_file),
                        phase="file_read"
                    ),
                    original_error=e
                ) from e
            except PermissionError as e:
                logger.error(
                    f"Permission denied reading state file: {self.state_file}",
                    exc_info=True,
                    extra={
                        "operation": "load_project_state",
                        "file_path": str(self.state_file),
                        "phase": "file_read"
                    }
                )
                self._display_error_panel(
                    title="❌ Permission Denied",
                    message=(
                        f"Permission denied reading project state file.\n\n"
                        f"File: {self.state_file}\n\n"
                        "Check file permissions and try again."
                    ),
                    style="red"
                )
                raise StateLoadingError(
                    message=f"Permission denied reading state file: {e}",
                    error_type="permission_error",
                    file_path=str(self.state_file),
                    context=ErrorContext(
                        operation="load_project_state",
                        file_path=str(self.state_file),
                        phase="file_read"
                    ),
                    original_error=e
                ) from e
            except json.JSONDecodeError as e:
                logger.error(
                    f"Corrupted JSON in state file: {self.state_file} - {e}",
                    exc_info=True,
                    extra={
                        "operation": "load_project_state",
                        "file_path": str(self.state_file),
                        "phase": "json_parse",
                        "json_error_line": e.lineno,
                        "json_error_column": e.colno
                    }
                )
                self._display_error_panel(
                    title="❌ Corrupted Project State",
                    message=(
                        f"Project state file is corrupted or contains invalid JSON.\n\n"
                        f"File: {self.state_file}\n"
                        f"Error at line {e.lineno}, column {e.colno}: {e.msg}\n\n"
                        "Attempting automatic recovery..."
                    ),
                    style="yellow"
                )
                
                # Attempt recovery for JSON corruption if enabled
                if self.enable_recovery:
                    recovered_state = self._attempt_state_recovery(e)
                    if recovered_state:
                        return recovered_state
                
                # If recovery failed, raise error
                raise StateLoadingError(
                    message=f"Corrupted JSON in state file: {e.msg} at line {e.lineno}",
                    error_type="corrupted_data",
                    file_path=str(self.state_file),
                    context=ErrorContext(
                        operation="load_project_state",
                        file_path=str(self.state_file),
                        phase="json_parse",
                        additional_info={
                            "json_error_line": e.lineno,
                            "json_error_column": e.colno,
                            "json_error_msg": e.msg
                        }
                    ),
                    original_error=e
                ) from e
            except Exception as e:
                logger.error(
                    f"Unexpected error reading state file: {self.state_file} - {e}",
                    exc_info=True,
                    extra={
                        "operation": "load_project_state",
                        "file_path": str(self.state_file),
                        "phase": "file_read"
                    }
                )
                self._display_error_panel(
                    title="❌ Error Reading State File",
                    message=(
                        f"Unexpected error reading project state file.\n\n"
                        f"File: {self.state_file}\n"
                        f"Error: {e}\n\n"
                        "Check file integrity and permissions."
                    ),
                    style="red"
                )
                raise StateLoadingError(
                    message=f"Unexpected error reading state file: {e}",
                    error_type="corrupted_data",
                    file_path=str(self.state_file),
                    context=ErrorContext(
                        operation="load_project_state",
                        file_path=str(self.state_file),
                        phase="file_read"
                    ),
                    original_error=e
                ) from e

            # Validate state dictionary structure
            try:
                is_valid, validation_issues = self._validate_state_dict(state_dict)
                if not is_valid:
                    logger.error(
                        f"State validation failed with {len(validation_issues)} issues",
                        extra={
                            "operation": "load_project_state",
                            "phase": "validation",
                            "validation_issues": validation_issues,
                            "file_path": str(self.state_file)
                        }
                    )
                    
                    # Display validation errors to user
                    issues_text = "\n".join(f"• {issue}" for issue in validation_issues)
                    self._display_error_panel(
                        title="❌ State Validation Failed",
                        message=(
                            f"Project state file has validation errors:\n\n"
                            f"{issues_text}\n\n"
                            f"File: {self.state_file}\n\n"
                            "Attempting automatic recovery..."
                        ),
                        style="yellow"
                    )
                    
                    # Attempt recovery for validation failures if enabled
                    validation_error = ValueError(f"State validation failed: {', '.join(validation_issues)}")
                    if self.enable_recovery:
                        recovered_state = self._attempt_state_recovery(validation_error)
                        if recovered_state:
                            return recovered_state
                    
                    # If recovery failed, raise error
                    raise StateLoadingError(
                        message=f"State validation failed: {', '.join(validation_issues)}",
                        error_type="validation_error",
                        file_path=str(self.state_file),
                        context=ErrorContext(
                            operation="load_project_state",
                            file_path=str(self.state_file),
                            phase="validation",
                            additional_info={"validation_issues": validation_issues}
                        ),
                        original_error=validation_error
                    ) from validation_error
                
                logger.info(
                    "State validation passed successfully",
                    extra={
                        "operation": "load_project_state",
                        "phase": "validation",
                        "file_path": str(self.state_file)
                    }
                )
                
            except Exception as validation_error:
                logger.error(
                    f"Unexpected error during state validation: {validation_error}",
                    exc_info=True,
                    extra={
                        "operation": "load_project_state",
                        "phase": "validation",
                        "file_path": str(self.state_file)
                    }
                )
                
                # Attempt recovery for validation errors if enabled
                if self.enable_recovery:
                    recovered_state = self._attempt_state_recovery(validation_error)
                    if recovered_state:
                        return recovered_state
                
                # If recovery failed, raise error
                raise StateLoadingError(
                    message=f"State validation error: {validation_error}",
                    error_type="validation_error",
                    file_path=str(self.state_file),
                    context=ErrorContext(
                        operation="load_project_state",
                        file_path=str(self.state_file),
                        phase="validation"
                    ),
                    original_error=validation_error
                ) from validation_error

            # Reconstruct the ProjectState object with enhanced error handling
            try:
                project_state = self._reconstruct_project_state(state_dict)
                logger.info(
                    f"Successfully loaded project state from {self.state_file}",
                    extra={
                        "operation": "load_project_state",
                        "file_path": str(self.state_file),
                        "phase": project_state.current_phase.value if project_state.current_phase else "unknown"
                    }
                )
                return project_state
            except DatetimeDeserializationError as e:
                logger.error(
                    f"Datetime deserialization failed during state load: {e.message}",
                    exc_info=True,
                    extra={
                        "operation": "load_project_state",
                        "phase": "deserialization",
                        "field_path": e.field_path,
                        "field_name": e.field_name,
                        "datetime_string": e.datetime_string
                    }
                )
                self._display_error_panel(
                    title="❌ State Load Failed - Datetime Error",
                    message=(
                        f"Failed to deserialize datetime field '{e.field_name or 'unknown'}'\n"
                        f"Path: {e.field_path or 'unknown'}\n"
                        f"Value: '{e.datetime_string}'\n\n"
                        f"Error: {e.message}\n\n"
                        "Attempting automatic recovery..."
                    ),
                    style="yellow"
                )
                
                # Attempt recovery for datetime deserialization errors if enabled
                if self.enable_recovery:
                    recovered_state = self._attempt_state_recovery(e)
                    if recovered_state:
                        return recovered_state
                
                # If recovery failed, raise error
                raise StateLoadingError(
                    message=f"Datetime deserialization failed: {e.message}",
                    error_type="deserialization_error",
                    file_path=str(self.state_file),
                    context=ErrorContext(
                        operation="load_project_state",
                        file_path=str(self.state_file),
                        phase="deserialization"
                    ),
                    original_error=e
                ) from e
            except Exception as e:
                logger.error(
                    f"Failed to reconstruct project state: {e}",
                    exc_info=True,
                    extra={
                        "operation": "load_project_state",
                        "phase": "reconstruction",
                        "file_path": str(self.state_file)
                    }
                )
                self._display_error_panel(
                    title="❌ State Load Failed - Reconstruction Error",
                    message=(
                        f"Failed to reconstruct project state from file data.\n\n"
                        f"File: {self.state_file}\n"
                        f"Error: {e}\n\n"
                        "Attempting automatic recovery..."
                    ),
                    style="yellow"
                )
                
                # Attempt recovery for reconstruction errors if enabled
                if self.enable_recovery:
                    recovered_state = self._attempt_state_recovery(e)
                    if recovered_state:
                        return recovered_state
                
                # If recovery failed, raise error
                raise StateLoadingError(
                    message=f"Failed to reconstruct project state: {e}",
                    error_type="deserialization_error",
                    file_path=str(self.state_file),
                    context=ErrorContext(
                        operation="load_project_state",
                        file_path=str(self.state_file),
                        phase="reconstruction"
                    ),
                    original_error=e
                ) from e
                
        except (StateLoadingError, DatetimeDeserializationError):
            # Re-raise our custom errors
            raise
        except Exception as e:
            logger.error(
                f"Unexpected error loading project state: {e}",
                exc_info=True,
                extra={
                    "operation": "load_project_state",
                    "file_path": str(self.state_file)
                }
            )
            self._display_error_panel(
                title="❌ State Load Failed - Unexpected Error",
                message=(
                    f"An unexpected error occurred while loading project state.\n\n"
                    f"File: {self.state_file}\n"
                    f"Error: {e}\n\n"
                    "Please check the logs for more details."
                ),
                style="red"
            )
            raise StateLoadingError(
                message=f"Unexpected error during state load: {e}",
                error_type="deserialization_error",
                file_path=str(self.state_file),
                context=ErrorContext(
                    operation="load_project_state",
                    file_path=str(self.state_file)
                ),
                original_error=e
            ) from e

    def _reconstruct_project_state(self, state_dict: dict[str, Any]) -> ProjectState:
        """Reconstruct ProjectState from dictionary with enhanced datetime handling."""
        # Handle datetime fields with None checks and field context
        created_at = self._deserialize_datetime(
            state_dict.get("created_at"), 
            field_name="created_at", 
            field_path="project_state.created_at"
        )
        updated_at = self._deserialize_datetime(
            state_dict.get("updated_at"), 
            field_name="updated_at", 
            field_path="project_state.updated_at"
        )

        # Handle session data with None-safe datetime deserialization
        session_data_dict = state_dict["session_data"]
        session_data = SessionData(
            session_id=session_data_dict["session_id"],
            started_at=self._deserialize_datetime(
                session_data_dict.get("started_at"),
                field_name="started_at",
                field_path="project_state.session_data.started_at"
            ),
            last_activity=self._deserialize_datetime(
                session_data_dict.get("last_activity"),
                field_name="last_activity",
                field_path="project_state.session_data.last_activity"
            ),
            user_approvals=session_data_dict["user_approvals"],
            pending_approvals=session_data_dict["pending_approvals"],
        )

        # Handle index metadata with None-safe datetime deserialization
        index_metadata = None
        if state_dict["index_metadata"]:
            idx_dict = state_dict["index_metadata"]
            index_metadata = IndexMetadata(
                total_files=idx_dict["total_files"],
                total_lines=idx_dict["total_lines"],
                languages_detected=idx_dict["languages_detected"],
                index_size_mb=idx_dict["index_size_mb"],
                last_indexed=self._deserialize_datetime(
                    idx_dict.get("last_indexed"),
                    field_name="last_indexed",
                    field_path="project_state.index_metadata.last_indexed"
                ),
                index_version=idx_dict["index_version"],
            )

        # Handle documents (these will be loaded separately)
        specification = None
        if state_dict["specification"]:
            specification = self._reconstruct_specification(state_dict["specification"])

        design = None
        if state_dict["design"]:
            design = self._reconstruct_design(state_dict["design"])

        tasks = None
        if state_dict["tasks"]:
            tasks = self._reconstruct_tasks(state_dict["tasks"])

        # Handle implementation progress
        implementation_progress = {}
        for task_id, status_str in state_dict["implementation_progress"].items():
            implementation_progress[task_id] = TaskStatus(status_str)

        return ProjectState(
            project_path=state_dict["project_path"],
            current_phase=PhaseType(state_dict["current_phase"]),
            indexing_complete=state_dict["indexing_complete"],
            specification=specification,
            design=design,
            tasks=tasks,
            implementation_progress=implementation_progress,
            index_metadata=index_metadata,
            session_data=session_data,
            created_at=created_at,
            updated_at=updated_at,
            # Load approval flags with backward compatibility
            specification_approved=state_dict.get("specification_approved", False),
            design_approved=state_dict.get("design_approved", False),
            tasks_approved=state_dict.get("tasks_approved", False),
        )

    def _reconstruct_specification(
        self, spec_dict: dict[str, Any]
    ) -> SpecificationDocument:
        """Reconstruct SpecificationDocument from dictionary."""
        from ..models.documents import CodeAnalysisRef, Requirement
        from ..models.enums import Priority, SpecificationSource

        # Reconstruct requirements
        requirements = []
        for req_dict in spec_dict["functional_requirements"]:
            source_analysis = None
            if req_dict["source_analysis"]:
                sa_dict = req_dict["source_analysis"]
                source_analysis = CodeAnalysisRef(
                    file_paths=sa_dict["file_paths"],
                    functions=sa_dict["functions"],
                    confidence_score=sa_dict["confidence_score"],
                )

            requirement = Requirement(
                id=req_dict["id"],
                user_story=req_dict["user_story"],
                acceptance_criteria=req_dict["acceptance_criteria"],
                priority=Priority(req_dict["priority"]),
                source_analysis=source_analysis,
            )
            requirements.append(requirement)

        # Handle approval_timestamp - check if None before deserializing
        approval_timestamp = None
        if spec_dict.get("approval_timestamp") is not None:
            approval_timestamp = self._deserialize_datetime(
                spec_dict["approval_timestamp"],
                field_name="approval_timestamp",
                field_path="specification.approval_timestamp"
            )

        return SpecificationDocument(
            introduction=spec_dict["introduction"],
            key_features=spec_dict["key_features"],
            functional_requirements=requirements,
            source=SpecificationSource(spec_dict["source"]),
            version=spec_dict["version"],
            approved=spec_dict["approved"],
            approval_timestamp=approval_timestamp,
        )

    def _reconstruct_design(self, design_dict: dict[str, Any]) -> DesignDocument:
        """Reconstruct DesignDocument from dictionary."""
        from ..models.documents import (
            ArchitectureDescription,
            ComponentSpec,
            DataModel,
            ErrorHandlingStrategy,
            InterfaceSpec,
            TestingStrategy,
        )

        # Reconstruct architecture
        arch_dict = design_dict["architecture"]
        architecture = ArchitectureDescription(
            overview=arch_dict["overview"],
            patterns=arch_dict["patterns"],
            components=arch_dict["components"],
        )

        # Reconstruct components
        components = []
        for comp_dict in design_dict["components"]:
            component = ComponentSpec(
                name=comp_dict["name"],
                description=comp_dict["description"],
                interfaces=comp_dict["interfaces"],
                dependencies=comp_dict["dependencies"],
            )
            components.append(component)

        # Reconstruct data models
        data_models = []
        for dm_dict in design_dict["data_models"]:
            data_model = DataModel(
                name=dm_dict["name"],
                fields=dm_dict["fields"],
                relationships=dm_dict["relationships"],
            )
            data_models.append(data_model)

        # Reconstruct interfaces
        interfaces = []
        for int_dict in design_dict["interfaces"]:
            interface = InterfaceSpec(
                name=int_dict["name"],
                methods=int_dict["methods"],
                description=int_dict["description"],
            )
            interfaces.append(interface)

        # Reconstruct error handling
        eh_dict = design_dict["error_handling"]
        error_handling = ErrorHandlingStrategy(
            error_categories=eh_dict["error_categories"],
            recovery_mechanisms=eh_dict["recovery_mechanisms"],
            logging_strategy=eh_dict["logging_strategy"],
        )

        # Reconstruct testing strategy
        ts_dict = design_dict["testing_strategy"]
        testing_strategy = TestingStrategy(
            unit_testing=ts_dict["unit_testing"],
            integration_testing=ts_dict["integration_testing"],
            performance_testing=ts_dict["performance_testing"],
            test_coverage_target=ts_dict["test_coverage_target"],
        )

        # Handle approval_timestamp if field exists (future-proofing)
        approval_timestamp = None
        if "approval_timestamp" in design_dict and design_dict["approval_timestamp"] is not None:
            approval_timestamp = self._deserialize_datetime(
                design_dict["approval_timestamp"],
                field_name="approval_timestamp",
                field_path="design.approval_timestamp"
            )

        # Build DesignDocument (approval_timestamp not currently in model)
        return DesignDocument(
            overview=design_dict["overview"],
            architecture=architecture,
            components=components,
            data_models=data_models,
            interfaces=interfaces,
            error_handling=error_handling,
            testing_strategy=testing_strategy,
            version=design_dict["version"],
            approved=design_dict["approved"],
        )

    def _reconstruct_tasks(self, tasks_dict: dict[str, Any]) -> TaskList:
        """Reconstruct TaskList from dictionary."""
        from ..models.documents import Task

        # Reconstruct tasks
        tasks = []
        for task_dict in tasks_dict["tasks"]:
            task = Task(
                id=task_dict["id"],
                title=task_dict["title"],
                description=task_dict["description"],
                requirements_refs=task_dict["requirements_refs"],
                subtasks=task_dict["subtasks"],
                status=TaskStatus(task_dict["status"]),
                target_language=task_dict["target_language"],
                context_requirements=task_dict["context_requirements"],
                implementation_notes=task_dict["implementation_notes"],
                generated_files=task_dict["generated_files"],
            )
            tasks.append(task)

        # Handle approval_timestamp if field exists (future-proofing)
        approval_timestamp = None
        if "approval_timestamp" in tasks_dict and tasks_dict["approval_timestamp"] is not None:
            approval_timestamp = self._deserialize_datetime(
                tasks_dict["approval_timestamp"],
                field_name="approval_timestamp",
                field_path="tasks.approval_timestamp"
            )

        # Build TaskList (approval_timestamp not currently in model)
        return TaskList(
            tasks=tasks,
            dependencies=tasks_dict["dependencies"],
            estimated_effort=tasks_dict["estimated_effort"],
            version=tasks_dict["version"],
            approved=tasks_dict["approved"],
        )

    async def update_phase_status(self, phase: PhaseType, status: str) -> bool:
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
                logger.warning(
                    f"Cannot update phase status - no project state found",
                    extra={
                        "operation": "update_phase_status",
                        "target_phase": phase.value,
                        "status": status
                    }
                )
                return False

            old_phase = state.current_phase.value if state.current_phase else "unknown"
            state.current_phase = phase
            state.updated_at = datetime.now()

            success = await self.save_project_state(state)
            if success:
                logger.info(
                    f"Updated phase from {old_phase} to {phase.value}",
                    extra={
                        "operation": "update_phase_status",
                        "old_phase": old_phase,
                        "new_phase": phase.value,
                        "status": status
                    }
                )
            return success
        except (StateLoadingError, StateSavingError, DatetimeSerializationError, DatetimeDeserializationError):
            # These errors are already logged and displayed
            return False
        except Exception as e:
            logger.error(
                f"Unexpected error updating phase status: {e}",
                exc_info=True,
                extra={
                    "operation": "update_phase_status",
                    "target_phase": phase.value,
                    "status": status
                }
            )
            self._display_error_panel(
                title="❌ Phase Update Failed",
                message=(
                    f"Failed to update project phase to {phase.value}.\n\n"
                    f"Error: {e}\n\n"
                    "Please check the project state and try again."
                ),
                style="red"
            )
            return False

    async def save_document(self, document: str, doc_type: DocumentType) -> bool:
        """Save a document to the appropriate file.

        Args:
            document: Document content as string
            doc_type: Type of document (SPECIFICATION, DESIGN, TASKS)

        Returns:
            True if successful, False otherwise
        """
        try:
            if doc_type == DocumentType.SPECIFICATION:
                state = self.load_project_state()
                if not state:
                    logger.error("Cannot save specification without a project state.")
                    return False

                spec_folder = await self._get_spec_folder_name(document)
                state.spec_folder = spec_folder
                await self.save_project_state(state)

                filename = f"{spec_folder}/requirements.md"
            else:
                filename_map = {
                    DocumentType.DESIGN: "design.md",
                    DocumentType.TASKS: "tasks.md",
                }
                filename = filename_map.get(doc_type)

            if not filename:
                logger.error(
                    f"Unknown document type: {doc_type}",
                    extra={
                        "operation": "save_document",
                        "doc_type": doc_type.value if hasattr(doc_type, 'value') else str(doc_type)
                    }
                )
                return False

            file_path = self.documents_dir / filename
            file_path.parent.mkdir(parents=True, exist_ok=True)

            with open(file_path, "w", encoding="utf-8") as f:
                f.write(document)

            logger.info(
                f"Successfully saved {doc_type.value} document to {file_path}",
                extra={
                    "operation": "save_document",
                    "doc_type": doc_type.value,
                    "file_path": str(file_path),
                    "document_size": len(document)
                }
            )
            return True
        except PermissionError as e:
            logger.error(
                f"Permission denied saving document {doc_type.value}: {e}",
                exc_info=True,
                extra={
                    "operation": "save_document",
                    "doc_type": doc_type.value,
                    "file_path": str(file_path) if 'file_path' in locals() else "unknown"
                }
            )
            self._display_error_panel(
                title="❌ Document Save Failed - Permission Denied",
                message=(
                    f"Permission denied saving {doc_type.value.lower()} document.\n\n"
                    f"File: {file_path if 'file_path' in locals() else 'unknown'}\n\n"
                    "Check directory permissions and try again."
                ),
                style="red"
            )
            return False
        except OSError as e:
            logger.error(
                f"I/O error saving document {doc_type.value}: {e}",
                exc_info=True,
                extra={
                    "operation": "save_document",
                    "doc_type": doc_type.value,
                    "file_path": str(file_path) if 'file_path' in locals() else "unknown",
                    "errno": e.errno
                }
            )
            if e.errno == 28:  # No space left on device
                error_msg = (
                    f"Insufficient disk space to save {doc_type.value.lower()} document.\n\n"
                    f"File: {file_path if 'file_path' in locals() else 'unknown'}\n\n"
                    "Please free up disk space and try again."
                )
            else:
                error_msg = (
                    f"I/O error saving {doc_type.value.lower()} document: {e}\n\n"
                    f"File: {file_path if 'file_path' in locals() else 'unknown'}\n\n"
                    "Check disk health and file system integrity."
                )
            
            self._display_error_panel(
                title="❌ Document Save Failed - I/O Error",
                message=error_msg,
                style="red"
            )
            return False
        except Exception as e:
            logger.error(
                f"Unexpected error saving document {doc_type.value}: {e}",
                exc_info=True,
                extra={
                    "operation": "save_document",
                    "doc_type": doc_type.value,
                    "file_path": str(file_path) if 'file_path' in locals() else "unknown"
                }
            )
            self._display_error_panel(
                title="❌ Document Save Failed",
                message=(
                    f"Unexpected error saving {doc_type.value.lower()} document.\n\n"
                    f"Error: {e}\n\n"
                    "Please check the logs for more details."
                ),
                style="red"
            )
            return False

    async def _get_spec_folder_name(self, document: str) -> str:
        """Generate a folder name for the specification using an LLM.

        Args:
            document: The document content

        Returns:
            Folder name for the specification
        """
        import re
        from datetime import datetime

        # Initialize LLM client if not already available
        if self.llm_client is None:
            try:
                self.llm_client = create_llm_client()
            except Exception as e:
                logger.error(f"Failed to create LLM client: {e}", exc_info=True)
                # Fallback to default naming if LLM client fails
                return f"spec-{datetime.now().strftime('%Y%m%d-%H%M%S')}"

        try:
            # Prompt for generating a folder name
            prompt = (
                "Based on the following specification, generate a concise, "
                "kebab-case folder name (e.g., 'user-authentication' or 'payment-gateway'). "
                "The name should be a maximum of 50 characters.\n\n"
                f"Specification:\n---\n{document[:2000]}\n---\n\n"
                "Folder name:"
            )

            # Generate folder name using LLM
            folder_name = await self.llm_client.generate_completion(
                prompt,
                system_prompt="You are an expert at creating concise, descriptive, and valid folder names.",
                temperature=0.2,
                max_tokens=20,
            )

            # Clean up the generated name
            folder_name = folder_name.strip().lower()
            folder_name = re.sub(r"[^a-z0-9-]+", "", folder_name)
            folder_name = folder_name[:50]  # Enforce length limit

            if folder_name:
                return folder_name

        except Exception as e:
            logger.error(
                f"LLM-based folder name generation failed: {e}", exc_info=True
            )

        # Fallback to default naming
        return f"spec-{datetime.now().strftime('%Y%m%d-%H%M%S')}"

    def load_document(self, doc_type: DocumentType) -> str | None:
        """Load a document from file.

        Args:
            doc_type: Type of document to load

        Returns:
            Document content as string if successful, None otherwise
        """
        try:
            if doc_type == DocumentType.SPECIFICATION:
                state = self.load_project_state()
                if not state or not state.spec_folder:
                    logger.warning("Cannot load specification without a spec_folder in the project state.")
                    return None
                filename = f"{state.spec_folder}/requirements.md"
            else:
                filename_map = {
                    DocumentType.DESIGN: "design.md",
                    DocumentType.TASKS: "tasks.md",
                }
                filename = filename_map.get(doc_type)

            if not filename:
                logger.error(
                    f"Unknown document type: {doc_type}",
                    extra={
                        "operation": "load_document",
                        "doc_type": doc_type.value if hasattr(doc_type, 'value') else str(doc_type)
                    }
                )
                return None

            file_path = self.documents_dir / filename

            if not file_path.exists():
                logger.info(
                    f"Document file does not exist: {file_path}",
                    extra={
                        "operation": "load_document",
                        "doc_type": doc_type.value,
                        "file_path": str(file_path)
                    }
                )
                return None

            with open(file_path, encoding="utf-8") as f:
                content = f.read()
                
            logger.info(
                f"Successfully loaded {doc_type.value} document from {file_path}",
                extra={
                    "operation": "load_document",
                    "doc_type": doc_type.value,
                    "file_path": str(file_path),
                    "document_size": len(content)
                }
            )
            return content
        except PermissionError as e:
            logger.error(
                f"Permission denied loading document {doc_type.value}: {e}",
                exc_info=True,
                extra={
                    "operation": "load_document",
                    "doc_type": doc_type.value,
                    "file_path": str(file_path) if 'file_path' in locals() else "unknown"
                }
            )
            self._display_error_panel(
                title="❌ Document Load Failed - Permission Denied",
                message=(
                    f"Permission denied loading {doc_type.value.lower()} document.\n\n"
                    f"File: {file_path if 'file_path' in locals() else 'unknown'}\n\n"
                    "Check file permissions and try again."
                ),
                style="red"
            )
            return None
        except UnicodeDecodeError as e:
            logger.error(
                f"Encoding error loading document {doc_type.value}: {e}",
                exc_info=True,
                extra={
                    "operation": "load_document",
                    "doc_type": doc_type.value,
                    "file_path": str(file_path) if 'file_path' in locals() else "unknown"
                }
            )
            self._display_error_panel(
                title="❌ Document Load Failed - Encoding Error",
                message=(
                    f"Encoding error loading {doc_type.value.lower()} document.\n\n"
                    f"File: {file_path if 'file_path' in locals() else 'unknown'}\n\n"
                    "The file may be corrupted or in an unsupported encoding."
                ),
                style="red"
            )
            return None
        except Exception as e:
            logger.error(
                f"Unexpected error loading document {doc_type.value}: {e}",
                exc_info=True,
                extra={
                    "operation": "load_document",
                    "doc_type": doc_type.value,
                    "file_path": str(file_path) if 'file_path' in locals() else "unknown"
                }
            )
            self._display_error_panel(
                title="❌ Document Load Failed",
                message=(
                    f"Unexpected error loading {doc_type.value.lower()} document.\n\n"
                    f"Error: {e}\n\n"
                    "Please check the logs for more details."
                ),
                style="red"
            )
            return None

    async def track_task_progress(self, task_id: str, progress: TaskStatus) -> bool:
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
                logger.warning(
                    f"Cannot track task progress - no project state found",
                    extra={
                        "operation": "track_task_progress",
                        "task_id": task_id,
                        "progress": progress.value
                    }
                )
                return False

            old_status = state.implementation_progress.get(task_id)
            state.implementation_progress[task_id] = progress
            state.updated_at = datetime.now()

            success = await self.save_project_state(state)
            if success:
                logger.info(
                    f"Updated task {task_id} progress from {old_status.value if old_status else 'none'} to {progress.value}",
                    extra={
                        "operation": "track_task_progress",
                        "task_id": task_id,
                        "old_status": old_status.value if old_status else None,
                        "new_status": progress.value
                    }
                )
            return success
        except (StateLoadingError, StateSavingError, DatetimeSerializationError, DatetimeDeserializationError):
            # These errors are already logged and displayed
            return False
        except Exception as e:
            logger.error(
                f"Unexpected error tracking task progress: {e}",
                exc_info=True,
                extra={
                    "operation": "track_task_progress",
                    "task_id": task_id,
                    "progress": progress.value
                }
            )
            self._display_error_panel(
                title="❌ Task Progress Update Failed",
                message=(
                    f"Failed to update progress for task '{task_id}'.\n\n"
                    f"Error: {e}\n\n"
                    "Please check the project state and try again."
                ),
                style="red"
            )
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
            pending_approvals=[],
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
            updated_at=now,
        )

    def get_project_info(self) -> dict[str, Any] | None:
        """Get basic project information from state.

        Returns:
            Dictionary with project info or None if no state exists
        """
        state = self.load_project_state()
        if state is None:
            return None

        return {
            "project_path": state.project_path,
            "current_phase": state.current_phase.value,
            "indexing_complete": state.indexing_complete,
            "created_at": state.created_at.isoformat(),
            "updated_at": state.updated_at.isoformat(),
            "has_specification": state.specification is not None,
            "has_design": state.design is not None,
            "has_tasks": state.tasks is not None,
            "total_tasks": len(state.implementation_progress)
            if state.implementation_progress
            else 0,
        }

    @staticmethod
    def get_performance_stats() -> dict[str, dict[str, float]]:
        """Get performance statistics for state operations.
        
        Returns:
            Dictionary with performance statistics for state save/load operations
            
        Example:
            ```python
            stats = StateManager.get_performance_stats()
            save_stats = stats.get("state_save", {})
            print(f"Average save time: {save_stats.get('avg_ms', 0):.1f}ms")
            ```
        """
        return _perf_monitor.get_all_stats()
