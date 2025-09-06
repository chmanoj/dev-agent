"""Integration tests for CLI functionality."""

import os
import tempfile
import unittest
from unittest.mock import patch, Mock
from dev_agent.cli.main import CLIApplication


class TestCLIIntegration(unittest.TestCase):
    """Integration test cases for CLI application."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.temp_dir = tempfile.mkdtemp()
        self.app = CLIApplication()
    
    def tearDown(self):
        """Clean up test fixtures."""
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    @patch('dev_agent.cli.interactive_cli.InteractiveCLI.start_chat_session')
    def test_cli_init_creates_project_structure(self, mock_chat_session):
        """Test that CLI init command creates proper project structure."""
        # Mock the chat session to avoid stdin issues
        mock_chat_session.return_value = None
        
        result = self.app.run(['init', self.temp_dir])
        
        # Should succeed
        self.assertEqual(result, 0)
        
        # Should create .dev_agent directory structure
        dev_agent_dir = os.path.join(self.temp_dir, '.dev_agent')
        self.assertTrue(os.path.exists(dev_agent_dir))
        self.assertTrue(os.path.exists(os.path.join(dev_agent_dir, 'documents')))
        self.assertTrue(os.path.exists(os.path.join(dev_agent_dir, 'index')))
        self.assertTrue(os.path.exists(os.path.join(dev_agent_dir, 'session.json')))
    
    @patch('dev_agent.cli.interactive_cli.InteractiveCLI.start_chat_session')
    def test_cli_resume_existing_project(self, mock_chat_session):
        """Test that CLI can resume an existing project."""
        # Mock the chat session to avoid stdin issues
        mock_chat_session.return_value = None
        
        # First initialize a project
        self.app.run(['init', self.temp_dir])
        
        # Create a new app instance to simulate restart
        new_app = CLIApplication()
        
        # Resume should work
        result = new_app.run(['resume', self.temp_dir])
        self.assertEqual(result, 0)
    
    def test_cli_resume_nonexistent_project(self):
        """Test that CLI handles resuming non-existent project gracefully."""
        result = self.app.run(['resume', '/nonexistent/path'])
        self.assertEqual(result, 1)
    
    @patch('dev_agent.cli.interactive_cli.InteractiveCLI.start_chat_session')
    def test_interactive_mode_startup(self, mock_chat_session):
        """Test that interactive mode starts correctly."""
        # Mock the chat session to avoid blocking
        mock_chat_session.return_value = None
        
        # Run without any command to trigger interactive mode
        result = self.app.run([])
        
        # Should start interactive mode
        self.assertEqual(result, 0)
        mock_chat_session.assert_called_once()
    
    def test_cli_help_display(self):
        """Test that CLI help is displayed correctly."""
        with patch('sys.argv', ['dev-agent', '--help']):
            with self.assertRaises(SystemExit) as cm:
                self.app.run(['--help'])
            # Help should exit with code 0
            self.assertEqual(cm.exception.code, 0)


if __name__ == '__main__':
    unittest.main()