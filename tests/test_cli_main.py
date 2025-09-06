"""Tests for CLI main application."""

import os
import tempfile
import unittest
from unittest.mock import Mock, patch, MagicMock
from dev_agent.cli.main import CLIApplication


class TestCLIApplication(unittest.TestCase):
    """Test cases for CLIApplication."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.app = CLIApplication()
        self.temp_dir = tempfile.mkdtemp()
    
    def tearDown(self):
        """Clean up test fixtures."""
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    def test_cli_application_init(self):
        """Test CLIApplication initialization."""
        self.assertIsNone(self.app.cli)
        self.assertIsNone(self.app.session_manager)
        self.assertIsNone(self.app.project_path)
    
    def test_parse_arguments_no_args(self):
        """Test parsing arguments with no command."""
        args = self.app._parse_arguments([])
        self.assertIsNone(args.command)
        self.assertEqual(args.project_path, os.getcwd())
        self.assertFalse(args.verbose)
    
    def test_parse_arguments_init_command(self):
        """Test parsing init command."""
        args = self.app._parse_arguments(['init', '/test/path'])
        self.assertEqual(args.command, 'init')
        self.assertEqual(args.project_path, '/test/path')
    
    def test_parse_arguments_init_no_path(self):
        """Test parsing init command without path."""
        args = self.app._parse_arguments(['init'])
        self.assertEqual(args.command, 'init')
        self.assertEqual(args.project_path, os.getcwd())
    
    def test_parse_arguments_resume_command(self):
        """Test parsing resume command."""
        args = self.app._parse_arguments(['resume', '/test/path'])
        self.assertEqual(args.command, 'resume')
        self.assertEqual(args.project_path, '/test/path')
    
    def test_parse_arguments_verbose_flag(self):
        """Test parsing with verbose flag."""
        args = self.app._parse_arguments(['--verbose', 'init'])
        self.assertTrue(args.verbose)
        self.assertEqual(args.command, 'init')
    
    @patch('dev_agent.cli.main.CLIApplication._handle_init_command')
    def test_run_init_command(self, mock_handle_init):
        """Test running with init command."""
        mock_handle_init.return_value = 0
        
        result = self.app.run(['init', self.temp_dir])
        
        self.assertEqual(result, 0)
        mock_handle_init.assert_called_once()
    
    @patch('dev_agent.cli.main.CLIApplication._handle_resume_command')
    def test_run_resume_command(self, mock_handle_resume):
        """Test running with resume command."""
        mock_handle_resume.return_value = 0
        
        result = self.app.run(['resume', self.temp_dir])
        
        self.assertEqual(result, 0)
        mock_handle_resume.assert_called_once()
    
    @patch('dev_agent.cli.main.CLIApplication._start_interactive_mode')
    def test_run_interactive_mode(self, mock_interactive):
        """Test running in interactive mode (no command)."""
        mock_interactive.return_value = 0
        
        result = self.app.run([self.temp_dir])
        
        self.assertEqual(result, 0)
        mock_interactive.assert_called_once_with(self.temp_dir)
    
    def test_run_keyboard_interrupt(self):
        """Test handling keyboard interrupt."""
        with patch('dev_agent.cli.main.CLIApplication._parse_arguments') as mock_parse:
            mock_parse.side_effect = KeyboardInterrupt()
            
            result = self.app.run([])
            self.assertEqual(result, 1)
    
    def test_run_exception(self):
        """Test handling general exception."""
        with patch('dev_agent.cli.main.CLIApplication._parse_arguments') as mock_parse:
            mock_parse.side_effect = Exception("Test error")
            
            result = self.app.run([])
            self.assertEqual(result, 1)
    
    def test_handle_init_command_nonexistent_path(self):
        """Test init command with nonexistent path."""
        from argparse import Namespace
        args = Namespace(project_path='/nonexistent/path', verbose=False)
        
        result = self.app._handle_init_command(args)
        self.assertEqual(result, 1)
    
    @patch('dev_agent.cli.main.CLIApplication._start_interactive_mode')
    @patch('dev_agent.cli.interactive_cli.InteractiveCLI')
    @patch('dev_agent.cli.session_manager.SessionManager')
    def test_handle_init_command_success(self, mock_session_manager_class, mock_cli_class, mock_interactive):
        """Test successful init command."""
        from argparse import Namespace
        
        # Setup mocks
        mock_session_manager = Mock()
        mock_session_manager.start_session.return_value = Mock(session_id='test-123')
        mock_session_manager_class.return_value = mock_session_manager
        
        mock_cli = Mock()
        mock_cli_class.return_value = mock_cli
        
        mock_interactive.return_value = 0
        
        args = Namespace(project_path=self.temp_dir, verbose=False)
        
        result = self.app._handle_init_command(args)
        
        self.assertEqual(result, 0)
        mock_cli.init_command.assert_called_once_with(os.path.abspath(self.temp_dir))
        mock_session_manager.start_session.assert_called_once()
        mock_interactive.assert_called_once()
    
    @patch('dev_agent.cli.interactive_cli.InteractiveCLI')
    def test_handle_init_command_init_failure(self, mock_cli_class):
        """Test init command with initialization failure."""
        from argparse import Namespace
        
        mock_cli = Mock()
        mock_cli.init_command.side_effect = Exception("Init failed")
        mock_cli_class.return_value = mock_cli
        
        args = Namespace(project_path=self.temp_dir, verbose=False)
        
        result = self.app._handle_init_command(args)
        self.assertEqual(result, 1)
    
    def test_handle_resume_command_nonexistent_path(self):
        """Test resume command with nonexistent path."""
        from argparse import Namespace
        args = Namespace(project_path='/nonexistent/path', verbose=False)
        
        result = self.app._handle_resume_command(args)
        self.assertEqual(result, 1)
    
    def test_handle_resume_command_no_dev_agent_dir(self):
        """Test resume command with no .dev_agent directory."""
        from argparse import Namespace
        args = Namespace(project_path=self.temp_dir, verbose=False)
        
        result = self.app._handle_resume_command(args)
        self.assertEqual(result, 1)
    
    @patch('dev_agent.cli.main.CLIApplication._start_interactive_mode')
    @patch('dev_agent.cli.session_manager.SessionManager')
    def test_handle_resume_command_existing_session(self, mock_session_manager_class, mock_interactive):
        """Test resume command with existing session."""
        from argparse import Namespace
        
        # Create .dev_agent directory
        dev_agent_dir = os.path.join(self.temp_dir, '.dev_agent')
        os.makedirs(dev_agent_dir)
        
        # Setup mocks
        mock_session_manager = Mock()
        mock_session = Mock(session_id='test-123', current_phase=Mock(value='specification'))
        mock_session_manager.resume_session.return_value = mock_session
        mock_session_manager_class.return_value = mock_session_manager
        
        mock_interactive.return_value = 0
        
        args = Namespace(project_path=self.temp_dir, verbose=False)
        
        result = self.app._handle_resume_command(args)
        
        self.assertEqual(result, 0)
        mock_session_manager.resume_session.assert_called_once()
        mock_interactive.assert_called_once()
    
    @patch('dev_agent.cli.main.CLIApplication._start_interactive_mode')
    @patch('dev_agent.cli.session_manager.SessionManager')
    def test_handle_resume_command_no_session(self, mock_session_manager_class, mock_interactive):
        """Test resume command with no existing session."""
        from argparse import Namespace
        
        # Create .dev_agent directory
        dev_agent_dir = os.path.join(self.temp_dir, '.dev_agent')
        os.makedirs(dev_agent_dir)
        
        # Setup mocks
        mock_session_manager = Mock()
        mock_session_manager.resume_session.return_value = None
        mock_new_session = Mock(session_id='new-123')
        mock_session_manager.start_session.return_value = mock_new_session
        mock_session_manager_class.return_value = mock_session_manager
        
        mock_interactive.return_value = 0
        
        args = Namespace(project_path=self.temp_dir, verbose=False)
        
        result = self.app._handle_resume_command(args)
        
        self.assertEqual(result, 0)
        mock_session_manager.resume_session.assert_called_once()
        mock_session_manager.start_session.assert_called_once()
        mock_interactive.assert_called_once()
    
    @patch('dev_agent.cli.interactive_cli.InteractiveCLI')
    @patch('dev_agent.cli.session_manager.SessionManager')
    def test_start_interactive_mode_success(self, mock_session_manager_class, mock_cli_class):
        """Test successful interactive mode start."""
        mock_session_manager = Mock()
        mock_session_manager_class.return_value = mock_session_manager
        
        mock_cli = Mock()
        mock_cli_class.return_value = mock_cli
        
        result = self.app._start_interactive_mode(self.temp_dir)
        
        self.assertEqual(result, 0)
        mock_cli.start_chat_session.assert_called_once()
        mock_session_manager.end_session.assert_called_once()
    
    @patch('dev_agent.cli.interactive_cli.InteractiveCLI')
    @patch('dev_agent.cli.session_manager.SessionManager')
    def test_start_interactive_mode_exception(self, mock_session_manager_class, mock_cli_class):
        """Test interactive mode with exception."""
        mock_session_manager = Mock()
        mock_session_manager_class.return_value = mock_session_manager
        
        mock_cli = Mock()
        mock_cli.start_chat_session.side_effect = Exception("Test error")
        mock_cli_class.return_value = mock_cli
        
        result = self.app._start_interactive_mode(self.temp_dir)
        
        self.assertEqual(result, 1)
        mock_session_manager.end_session.assert_called_once()
    
    @patch('dev_agent.cli.main.CLIApplication')
    def test_main_function(self, mock_app_class):
        """Test main function."""
        from dev_agent.cli.main import main
        
        mock_app = Mock()
        mock_app.run.return_value = 0
        mock_app_class.return_value = mock_app
        
        result = main()
        
        self.assertEqual(result, 0)
        mock_app.run.assert_called_once()


if __name__ == '__main__':
    unittest.main()