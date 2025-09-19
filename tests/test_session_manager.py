"""Tests for SessionManager class."""

import json
import os
import tempfile
import unittest
from datetime import datetime

from dev_agent.cli.session_manager import SessionData, SessionManager
from dev_agent.models.enums import PhaseType


class TestSessionData(unittest.TestCase):
    """Test cases for SessionData."""

    def test_session_data_creation(self):
        """Test SessionData creation."""
        now = datetime.now()
        session = SessionData(
            session_id="test-123",
            project_path="/test/path",
            current_phase=PhaseType.SPECIFICATION,
            start_time=now,
            last_activity=now,
            user_preferences={"theme": "dark"},
        )

        self.assertEqual(session.session_id, "test-123")
        self.assertEqual(session.project_path, "/test/path")
        self.assertEqual(session.current_phase, PhaseType.SPECIFICATION)
        self.assertEqual(session.start_time, now)
        self.assertEqual(session.last_activity, now)
        self.assertEqual(session.user_preferences, {"theme": "dark"})

    def test_session_data_to_dict(self):
        """Test SessionData to_dict conversion."""
        now = datetime.now()
        session = SessionData(
            session_id="test-123",
            project_path="/test/path",
            current_phase=PhaseType.DESIGN,
            start_time=now,
            last_activity=now,
            user_preferences={"theme": "dark"},
        )

        data = session.to_dict()

        self.assertEqual(data["session_id"], "test-123")
        self.assertEqual(data["project_path"], "/test/path")
        self.assertEqual(data["current_phase"], "design")
        self.assertEqual(data["start_time"], now.isoformat())
        self.assertEqual(data["last_activity"], now.isoformat())
        self.assertEqual(data["user_preferences"], {"theme": "dark"})

    def test_session_data_from_dict(self):
        """Test SessionData from_dict creation."""
        now = datetime.now()
        data = {
            "session_id": "test-123",
            "project_path": "/test/path",
            "current_phase": "implementation",
            "start_time": now.isoformat(),
            "last_activity": now.isoformat(),
            "user_preferences": {"theme": "light"},
        }

        session = SessionData.from_dict(data)

        self.assertEqual(session.session_id, "test-123")
        self.assertEqual(session.project_path, "/test/path")
        self.assertEqual(session.current_phase, PhaseType.IMPLEMENTATION)
        self.assertEqual(session.start_time, now)
        self.assertEqual(session.last_activity, now)
        self.assertEqual(session.user_preferences, {"theme": "light"})

    def test_session_data_from_dict_missing_preferences(self):
        """Test SessionData from_dict with missing user_preferences."""
        now = datetime.now()
        data = {
            "session_id": "test-123",
            "project_path": "/test/path",
            "current_phase": "indexing",
            "start_time": now.isoformat(),
            "last_activity": now.isoformat(),
        }

        session = SessionData.from_dict(data)
        self.assertEqual(session.user_preferences, {})


class TestSessionManager(unittest.TestCase):
    """Test cases for SessionManager."""

    def setUp(self):
        """Set up test fixtures."""
        self.temp_dir = tempfile.mkdtemp()
        self.project_path = self.temp_dir
        self.session_manager = SessionManager(self.project_path)

    def tearDown(self):
        """Clean up test fixtures."""
        import shutil

        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_session_manager_init(self):
        """Test SessionManager initialization."""
        self.assertEqual(self.session_manager.project_path, self.project_path)
        expected_session_file = os.path.join(
            self.project_path, ".dev_agent", "session.json"
        )
        self.assertEqual(self.session_manager.session_file, expected_session_file)
        self.assertIsNone(self.session_manager.current_session)

    def test_start_session(self):
        """Test starting a new session."""
        session = self.session_manager.start_session(PhaseType.SPECIFICATION)

        self.assertIsNotNone(session)
        self.assertEqual(session.project_path, self.project_path)
        self.assertEqual(session.current_phase, PhaseType.SPECIFICATION)
        self.assertIsNotNone(session.session_id)
        self.assertIsInstance(session.start_time, datetime)
        self.assertIsInstance(session.last_activity, datetime)
        self.assertEqual(session.user_preferences, {})

        # Check that session is saved
        self.assertEqual(self.session_manager.current_session, session)
        self.assertTrue(os.path.exists(self.session_manager.session_file))

    def test_start_session_default_phase(self):
        """Test starting session with default phase."""
        session = self.session_manager.start_session()
        self.assertEqual(session.current_phase, PhaseType.INDEXING)

    def test_save_and_resume_session(self):
        """Test saving and resuming a session."""
        # Start and save a session
        original_session = self.session_manager.start_session(PhaseType.DESIGN)
        original_session.user_preferences = {"test": "value"}
        self.session_manager.save_session()

        # Create new session manager and resume
        new_session_manager = SessionManager(self.project_path)
        resumed_session = new_session_manager.resume_session()

        self.assertIsNotNone(resumed_session)
        self.assertEqual(resumed_session.session_id, original_session.session_id)
        self.assertEqual(resumed_session.project_path, original_session.project_path)
        self.assertEqual(resumed_session.current_phase, PhaseType.DESIGN)
        self.assertEqual(resumed_session.user_preferences, {"test": "value"})

    def test_resume_session_no_file(self):
        """Test resuming session when no session file exists."""
        session = self.session_manager.resume_session()
        self.assertIsNone(session)

    def test_resume_session_invalid_json(self):
        """Test resuming session with invalid JSON file."""
        # Create invalid JSON file
        os.makedirs(os.path.dirname(self.session_manager.session_file), exist_ok=True)
        with open(self.session_manager.session_file, "w") as f:
            f.write("invalid json content")

        session = self.session_manager.resume_session()
        self.assertIsNone(session)

    def test_save_session_no_current_session(self):
        """Test saving when no current session exists."""
        result = self.session_manager.save_session()
        self.assertFalse(result)

    def test_update_activity(self):
        """Test updating activity timestamp."""
        session = self.session_manager.start_session()
        original_activity = session.last_activity

        # Wait a small amount to ensure timestamp difference
        import time

        time.sleep(0.01)

        self.session_manager.update_activity()

        self.assertGreater(session.last_activity, original_activity)

    def test_update_activity_no_session(self):
        """Test updating activity when no session exists."""
        # Should not raise an exception
        self.session_manager.update_activity()

    def test_update_phase(self):
        """Test updating the current phase."""
        session = self.session_manager.start_session(PhaseType.INDEXING)
        original_activity = session.last_activity

        # Wait a small amount to ensure timestamp difference
        import time

        time.sleep(0.01)

        self.session_manager.update_phase(PhaseType.SPECIFICATION)

        self.assertEqual(session.current_phase, PhaseType.SPECIFICATION)
        self.assertGreater(session.last_activity, original_activity)

    def test_set_and_get_preference(self):
        """Test setting and getting user preferences."""
        self.session_manager.start_session()

        self.session_manager.set_preference("theme", "dark")
        self.session_manager.set_preference("auto_save", True)

        self.assertEqual(self.session_manager.get_preference("theme"), "dark")
        self.assertEqual(self.session_manager.get_preference("auto_save"), True)
        self.assertIsNone(self.session_manager.get_preference("nonexistent"))
        self.assertEqual(
            self.session_manager.get_preference("nonexistent", "default"), "default"
        )

    def test_preferences_no_session(self):
        """Test preferences when no session exists."""
        self.session_manager.set_preference("test", "value")  # Should not crash
        result = self.session_manager.get_preference("test", "default")
        self.assertEqual(result, "default")

    def test_end_session(self):
        """Test ending a session."""
        session = self.session_manager.start_session()
        self.assertIsNotNone(self.session_manager.current_session)

        self.session_manager.end_session()
        self.assertIsNone(self.session_manager.current_session)

    def test_get_session_info(self):
        """Test getting session information."""
        session = self.session_manager.start_session(PhaseType.DESIGN)

        info = self.session_manager.get_session_info()

        self.assertIsNotNone(info)
        self.assertEqual(info["session_id"], session.session_id)
        self.assertEqual(info["project_path"], session.project_path)
        self.assertEqual(info["current_phase"], "design")
        self.assertIn("duration", info)
        self.assertIn("last_activity", info)

    def test_get_session_info_no_session(self):
        """Test getting session info when no session exists."""
        info = self.session_manager.get_session_info()
        self.assertIsNone(info)

    def test_session_file_creation(self):
        """Test that session file is created in correct location."""
        self.session_manager.start_session()

        expected_path = os.path.join(self.project_path, ".dev_agent", "session.json")
        self.assertTrue(os.path.exists(expected_path))

        # Verify file content
        with open(expected_path) as f:
            data = json.load(f)

        self.assertIn("session_id", data)
        self.assertIn("project_path", data)
        self.assertIn("current_phase", data)
        self.assertIn("start_time", data)
        self.assertIn("last_activity", data)
        self.assertIn("user_preferences", data)


if __name__ == "__main__":
    unittest.main()
