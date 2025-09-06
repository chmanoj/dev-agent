"""Session management for CLI interactions."""

import json
import os
from datetime import datetime
from typing import Optional, Dict, Any
from dataclasses import dataclass, asdict
from ..models.enums import PhaseType


@dataclass
class SessionData:
    """Data structure for CLI session information."""
    session_id: str
    project_path: str
    current_phase: PhaseType
    start_time: datetime
    last_activity: datetime
    user_preferences: Dict[str, Any]
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        data = asdict(self)
        data['current_phase'] = self.current_phase.value
        data['start_time'] = self.start_time.isoformat()
        data['last_activity'] = self.last_activity.isoformat()
        return data
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'SessionData':
        """Create from dictionary loaded from JSON."""
        return cls(
            session_id=data['session_id'],
            project_path=data['project_path'],
            current_phase=PhaseType(data['current_phase']),
            start_time=datetime.fromisoformat(data['start_time']),
            last_activity=datetime.fromisoformat(data['last_activity']),
            user_preferences=data.get('user_preferences', {})
        )


class SessionManager:
    """Manages CLI session state and persistence."""
    
    def __init__(self, project_path: str):
        """Initialize session manager for a project.
        
        Args:
            project_path: Path to the project directory
        """
        self.project_path = project_path
        self.session_file = os.path.join(project_path, '.dev_agent', 'session.json')
        self.current_session: Optional[SessionData] = None
    
    def start_session(self, phase: PhaseType = PhaseType.INDEXING) -> SessionData:
        """Start a new CLI session.
        
        Args:
            phase: Initial phase for the session
            
        Returns:
            New session data
        """
        import uuid
        
        session_id = str(uuid.uuid4())
        now = datetime.now()
        
        self.current_session = SessionData(
            session_id=session_id,
            project_path=self.project_path,
            current_phase=phase,
            start_time=now,
            last_activity=now,
            user_preferences={}
        )
        
        self.save_session()
        return self.current_session
    
    def resume_session(self) -> Optional[SessionData]:
        """Resume an existing session from saved state.
        
        Returns:
            Restored session data or None if no session exists
        """
        if not os.path.exists(self.session_file):
            return None
        
        try:
            with open(self.session_file, 'r') as f:
                data = json.load(f)
            
            self.current_session = SessionData.from_dict(data)
            self.update_activity()
            return self.current_session
            
        except (json.JSONDecodeError, KeyError, ValueError) as e:
            print(f"Warning: Could not restore session: {e}")
            return None
    
    def save_session(self) -> bool:
        """Save current session state to disk.
        
        Returns:
            True if saved successfully, False otherwise
        """
        if not self.current_session:
            return False
        
        try:
            # Ensure directory exists
            os.makedirs(os.path.dirname(self.session_file), exist_ok=True)
            
            with open(self.session_file, 'w') as f:
                json.dump(self.current_session.to_dict(), f, indent=2)
            
            return True
            
        except (OSError, json.JSONEncodeError) as e:
            print(f"Warning: Could not save session: {e}")
            return False
    
    def update_activity(self) -> None:
        """Update the last activity timestamp."""
        if self.current_session:
            self.current_session.last_activity = datetime.now()
            self.save_session()
    
    def update_phase(self, phase: PhaseType) -> None:
        """Update the current phase.
        
        Args:
            phase: New phase to set
        """
        if self.current_session:
            self.current_session.current_phase = phase
            self.update_activity()
    
    def set_preference(self, key: str, value: Any) -> None:
        """Set a user preference.
        
        Args:
            key: Preference key
            value: Preference value
        """
        if self.current_session:
            self.current_session.user_preferences[key] = value
            self.save_session()
    
    def get_preference(self, key: str, default: Any = None) -> Any:
        """Get a user preference.
        
        Args:
            key: Preference key
            default: Default value if key not found
            
        Returns:
            Preference value or default
        """
        if self.current_session:
            return self.current_session.user_preferences.get(key, default)
        return default
    
    def end_session(self) -> None:
        """End the current session and clean up."""
        if self.current_session:
            self.save_session()
            self.current_session = None
    
    def get_session_info(self) -> Optional[Dict[str, Any]]:
        """Get current session information.
        
        Returns:
            Session information dictionary or None
        """
        if not self.current_session:
            return None
        
        return {
            'session_id': self.current_session.session_id,
            'project_path': self.current_session.project_path,
            'current_phase': self.current_session.current_phase.value,
            'duration': (datetime.now() - self.current_session.start_time).total_seconds(),
            'last_activity': self.current_session.last_activity.isoformat()
        }