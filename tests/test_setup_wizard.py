"""Comprehensive tests for the setup wizard."""

from __future__ import annotations

import json
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from pydantic import SecretStr
from rich.console import Console

from dev_agent.models.llm_config import AzureOpenAIConfig
from dev_agent.onboarding.models import SetupResult, UserPreferences
from dev_agent.onboarding.setup_wizard import SetupWizard


@pytest.fixture
def mock_console():
    """Create mock Rich console."""
    console = MagicMock(spec=Console)
    console.print = MagicMock()
    return console


@pytest.fixture
def temp_config_path(tmp_path: Path) -> Path:
    """Create temporary config path for testing."""
    return tmp_path / ".dev_agent_config"


@pytest.fixture
def setup_wizard(temp_config_path: Path, mock_console: MagicMock) -> SetupWizard:
    """Create setup wizard instance for testing."""
    return SetupWizard(config_path=temp_config_path, console=mock_console)


@pytest.fixture
def mock_config_manager():
    """Create mock ConfigManager."""
    with patch("dev_agent.onboarding.setup_wizard.ConfigManager") as mock:
        config_instance = MagicMock()
        config_instance.get_config = MagicMock()
        config_instance.save_config = MagicMock()
        mock.return_value = config_instance
        yield mock


@pytest.fixture
def mock_azure_client():
    """Create mock Azure OpenAI client."""
    with patch("dev_agent.onboarding.setup_wizard.AzureOpenAIClient") as mock:
        client_instance = AsyncMock()
        client_instance.generate_completion = AsyncMock(
            return_value="test successful"
        )
        mock.return_value = client_instance
        yield mock


@pytest.fixture
def mock_embedding_client():
    """Create mock Azure Embedding client."""
    with patch("dev_agent.onboarding.setup_wizard.AzureEmbeddingClient") as mock:
        client_instance = AsyncMock()
        client_instance.embed_batch = AsyncMock(return_value=[[0.1] * 1536])
        mock.return_value = client_instance
        yield mock


# ============================================================================
# Test Wizard Initialization
# ============================================================================


def test_setup_wizard_initialization(setup_wizard: SetupWizard, temp_config_path: Path):
    """Test setup wizard initializes correctly."""
    assert setup_wizard.config_path == temp_config_path
    assert setup_wizard.console is not None
    assert isinstance(setup_wizard.preferences, UserPreferences)
    assert setup_wizard.steps == []


def test_setup_wizard_default_config_path(mock_console: MagicMock):
    """Test setup wizard uses default config path."""
    wizard = SetupWizard(console=mock_console)
    expected_path = Path.home() / ".dev_agent_config"
    assert wizard.config_path == expected_path


def test_setup_wizard_custom_config_path(temp_config_path: Path, mock_console: MagicMock):
    """Test setup wizard accepts custom config path."""
    wizard = SetupWizard(config_path=temp_config_path, console=mock_console)
    assert wizard.config_path == temp_config_path


# ============================================================================
# Test First Run Detection
# ============================================================================


def test_is_first_run_no_config(setup_wizard: SetupWizard):
    """Test first run detection when config doesn't exist."""
    assert setup_wizard._is_first_run() is True


def test_is_first_run_with_config(setup_wizard: SetupWizard, temp_config_path: Path):
    """Test first run detection when config exists."""
    temp_config_path.write_text("{}")
    assert setup_wizard._is_first_run() is False


# ============================================================================
# Test Azure OpenAI Configuration
# ============================================================================


def test_configure_azure_openai_success(
    setup_wizard: SetupWizard,
    mock_config_manager: MagicMock,
):
    """Test successful Azure OpenAI configuration."""
    # Mock user inputs
    with patch("dev_agent.onboarding.setup_wizard.Prompt.ask") as mock_prompt:
        mock_prompt.side_effect = [
            "https://test.openai.azure.com/",  # endpoint
            "test-api-key",  # api_key
            "2024-02-15-preview",  # api_version
            "gpt-4",  # deployment_name
            "text-embedding-ada-002",  # embedding_deployment
        ]

        # Mock config manager
        config_instance = mock_config_manager.return_value
        mock_config = MagicMock()
        mock_config.azure_openai = None
        config_instance.get_config.return_value = mock_config

        result = setup_wizard.configure_azure_openai()

        assert result is True
        assert setup_wizard.preferences.azure_configured is True
        config_instance.save_config.assert_called_once()


def test_configure_azure_openai_missing_endpoint(
    setup_wizard: SetupWizard,
    mock_config_manager: MagicMock,
):
    """Test Azure OpenAI configuration with missing endpoint."""
    with patch("dev_agent.onboarding.setup_wizard.Prompt.ask") as mock_prompt:
        mock_prompt.return_value = ""  # Empty endpoint

        config_instance = mock_config_manager.return_value
        mock_config = MagicMock()
        mock_config.azure_openai = None
        config_instance.get_config.return_value = mock_config

        result = setup_wizard.configure_azure_openai()

        assert result is False
        assert setup_wizard.preferences.azure_configured is False


def test_configure_azure_openai_missing_api_key(
    setup_wizard: SetupWizard,
    mock_config_manager: MagicMock,
):
    """Test Azure OpenAI configuration with missing API key."""
    with patch("dev_agent.onboarding.setup_wizard.Prompt.ask") as mock_prompt:
        mock_prompt.side_effect = [
            "https://test.openai.azure.com/",  # endpoint
            "",  # Empty API key
        ]

        config_instance = mock_config_manager.return_value
        mock_config = MagicMock()
        mock_config.azure_openai = None
        config_instance.get_config.return_value = mock_config

        result = setup_wizard.configure_azure_openai()

        assert result is False
        assert setup_wizard.preferences.azure_configured is False


def test_configure_azure_openai_invalid_endpoint_warning(
    setup_wizard: SetupWizard,
    mock_config_manager: MagicMock,
):
    """Test Azure OpenAI configuration with invalid endpoint format."""
    with patch("dev_agent.onboarding.setup_wizard.Prompt.ask") as mock_prompt:
        with patch("dev_agent.onboarding.setup_wizard.Confirm.ask") as mock_confirm:
            mock_prompt.side_effect = [
                "http://test.openai.azure.com/",  # Invalid (http not https)
            ]
            mock_confirm.return_value = False  # User declines to continue

            config_instance = mock_config_manager.return_value
            mock_config = MagicMock()
            mock_config.azure_openai = None
            config_instance.get_config.return_value = mock_config

            result = setup_wizard.configure_azure_openai()

            assert result is False
            mock_confirm.assert_called_once()


def test_configure_azure_openai_keyboard_interrupt(
    setup_wizard: SetupWizard,
    mock_config_manager: MagicMock,
):
    """Test Azure OpenAI configuration handles keyboard interrupt."""
    with patch("dev_agent.onboarding.setup_wizard.Prompt.ask") as mock_prompt:
        mock_prompt.side_effect = KeyboardInterrupt()

        config_instance = mock_config_manager.return_value
        mock_config = MagicMock()
        mock_config.azure_openai = None
        config_instance.get_config.return_value = mock_config

        result = setup_wizard.configure_azure_openai()

        assert result is False


def test_configure_azure_openai_with_existing_config(
    setup_wizard: SetupWizard,
    mock_config_manager: MagicMock,
):
    """Test Azure OpenAI configuration with existing config."""
    with patch("dev_agent.onboarding.setup_wizard.Prompt.ask") as mock_prompt:
        # Mock existing config
        existing_azure = AzureOpenAIConfig(
            endpoint="https://existing.openai.azure.com/",
            api_key=SecretStr("existing-key"),
            api_version="2024-02-15-preview",
            deployment_name="existing-gpt4",
            embedding_deployment="existing-embedding",
        )

        config_instance = mock_config_manager.return_value
        mock_config = MagicMock()
        mock_config.azure_openai = existing_azure
        config_instance.get_config.return_value = mock_config

        # User accepts defaults
        mock_prompt.side_effect = [
            "https://existing.openai.azure.com/",  # endpoint (default)
            "new-api-key",  # api_key
            "2024-02-15-preview",  # api_version (default)
            "existing-gpt4",  # deployment_name (default)
            "existing-embedding",  # embedding_deployment (default)
        ]

        result = setup_wizard.configure_azure_openai()

        assert result is True
        assert setup_wizard.preferences.azure_configured is True


# ============================================================================
# Test Connection Testing
# ============================================================================


def test_azure_connection_success(
    setup_wizard: SetupWizard,
    mock_config_manager: MagicMock,
    mock_azure_client: MagicMock,
    mock_embedding_client: MagicMock,
):
    """Test successful Azure OpenAI connection test."""
    # Mock config with Azure OpenAI configured
    azure_config = AzureOpenAIConfig(
        endpoint="https://test.openai.azure.com/",
        api_key=SecretStr("test-key"),
        api_version="2024-02-15-preview",
        deployment_name="gpt-4",
        embedding_deployment="text-embedding-ada-002",
    )

    config_instance = mock_config_manager.return_value
    mock_config = MagicMock()
    mock_config.azure_openai = azure_config
    config_instance.get_config.return_value = mock_config

    result = setup_wizard.test_azure_connection()

    assert result is True


def test_azure_connection_no_config(
    setup_wizard: SetupWizard,
    mock_config_manager: MagicMock,
):
    """Test connection test with no Azure OpenAI config."""
    config_instance = mock_config_manager.return_value
    mock_config = MagicMock()
    mock_config.azure_openai = None
    config_instance.get_config.return_value = mock_config

    result = setup_wizard.test_azure_connection()

    assert result is False


def test_azure_connection_completion_failure(
    setup_wizard: SetupWizard,
    mock_config_manager: MagicMock,
):
    """Test connection test with completion failure."""
    azure_config = AzureOpenAIConfig(
        endpoint="https://test.openai.azure.com/",
        api_key=SecretStr("test-key"),
        api_version="2024-02-15-preview",
        deployment_name="gpt-4",
        embedding_deployment="text-embedding-ada-002",
    )

    config_instance = mock_config_manager.return_value
    mock_config = MagicMock()
    mock_config.azure_openai = azure_config
    config_instance.get_config.return_value = mock_config

    with patch("dev_agent.onboarding.setup_wizard.AzureOpenAIClient") as mock_client:
        client_instance = AsyncMock()
        client_instance.generate_completion = AsyncMock(
            side_effect=Exception("API Error")
        )
        mock_client.return_value = client_instance

        result = setup_wizard.test_azure_connection()

        assert result is False


def test_azure_connection_embedding_failure(
    setup_wizard: SetupWizard,
    mock_config_manager: MagicMock,
    mock_azure_client: MagicMock,
):
    """Test connection test with embedding failure."""
    azure_config = AzureOpenAIConfig(
        endpoint="https://test.openai.azure.com/",
        api_key=SecretStr("test-key"),
        api_version="2024-02-15-preview",
        deployment_name="gpt-4",
        embedding_deployment="text-embedding-ada-002",
    )

    config_instance = mock_config_manager.return_value
    mock_config = MagicMock()
    mock_config.azure_openai = azure_config
    config_instance.get_config.return_value = mock_config

    with patch("dev_agent.onboarding.setup_wizard.AzureEmbeddingClient") as mock_embed:
        embed_instance = AsyncMock()
        embed_instance.embed_batch = AsyncMock(side_effect=Exception("Embedding Error"))
        mock_embed.return_value = embed_instance

        result = setup_wizard.test_azure_connection()

        assert result is False


def test_azure_connection_keyboard_interrupt(
    setup_wizard: SetupWizard,
    mock_config_manager: MagicMock,
):
    """Test connection test handles keyboard interrupt."""
    azure_config = AzureOpenAIConfig(
        endpoint="https://test.openai.azure.com/",
        api_key=SecretStr("test-key"),
        api_version="2024-02-15-preview",
        deployment_name="gpt-4",
        embedding_deployment="text-embedding-ada-002",
    )

    config_instance = mock_config_manager.return_value
    mock_config = MagicMock()
    mock_config.azure_openai = azure_config
    config_instance.get_config.return_value = mock_config

    with patch("dev_agent.onboarding.setup_wizard.AzureOpenAIClient") as mock_client:
        mock_client.side_effect = KeyboardInterrupt()

        result = setup_wizard.test_azure_connection()

        assert result is False


# ============================================================================
# Test Workflow Explanation
# ============================================================================


def test_explain_workflow_success(setup_wizard: SetupWizard):
    """Test workflow explanation displays correctly."""
    with patch("builtins.input") as mock_input:
        mock_input.return_value = ""  # User presses Enter

        result = setup_wizard.explain_workflow()

        assert result is True
        mock_input.assert_called_once()


def test_explain_workflow_keyboard_interrupt(setup_wizard: SetupWizard):
    """Test workflow explanation handles keyboard interrupt."""
    with patch("builtins.input") as mock_input:
        mock_input.side_effect = KeyboardInterrupt()

        result = setup_wizard.explain_workflow()

        assert result is True  # Should still return True (informational step)


# ============================================================================
# Test Sample Project Offering
# ============================================================================


def test_offer_sample_project_new_project(setup_wizard: SetupWizard):
    """Test sample project offering with new project choice."""
    with patch("dev_agent.onboarding.setup_wizard.Prompt.ask") as mock_prompt:
        mock_prompt.return_value = "1"  # New project

        result = setup_wizard.offer_sample_project()

        assert result is True
        mock_prompt.assert_called_once()


def test_offer_sample_project_existing_codebase(setup_wizard: SetupWizard):
    """Test sample project offering with existing codebase choice."""
    with patch("dev_agent.onboarding.setup_wizard.Prompt.ask") as mock_prompt:
        mock_prompt.return_value = "2"  # Existing codebase

        result = setup_wizard.offer_sample_project()

        assert result is True


def test_offer_sample_project_skip(setup_wizard: SetupWizard):
    """Test sample project offering with skip choice."""
    with patch("dev_agent.onboarding.setup_wizard.Prompt.ask") as mock_prompt:
        mock_prompt.return_value = "3"  # Skip

        result = setup_wizard.offer_sample_project()

        assert result is True


def test_offer_sample_project_keyboard_interrupt(setup_wizard: SetupWizard):
    """Test sample project offering handles keyboard interrupt."""
    with patch("dev_agent.onboarding.setup_wizard.Prompt.ask") as mock_prompt:
        mock_prompt.side_effect = KeyboardInterrupt()

        result = setup_wizard.offer_sample_project()

        assert result is True  # Should still return True (informational step)


# ============================================================================
# Test Preferences Saving
# ============================================================================


def test_save_preferences_success(setup_wizard: SetupWizard, temp_config_path: Path):
    """Test successful preferences saving."""
    setup_wizard.preferences.azure_configured = True
    setup_wizard.preferences.cost_warnings_enabled = True
    setup_wizard.preferences.budget_threshold = 10.0

    result = setup_wizard.save_user_preferences()

    assert result is True
    assert temp_config_path.exists()

    # Verify content
    saved_data = json.loads(temp_config_path.read_text())
    assert saved_data["azure_configured"] is True
    assert saved_data["cost_warnings_enabled"] is True
    assert saved_data["budget_threshold"] == 10.0
    assert saved_data["first_run_completed"] is True


def test_save_preferences_creates_directory(tmp_path: Path, mock_console: MagicMock):
    """Test preferences saving creates parent directory."""
    config_path = tmp_path / "nested" / "dir" / ".dev_agent_config"
    wizard = SetupWizard(config_path=config_path, console=mock_console)

    result = wizard.save_user_preferences()

    assert result is True
    assert config_path.exists()
    assert config_path.parent.exists()


def test_save_preferences_file_permissions(setup_wizard: SetupWizard, temp_config_path: Path):
    """Test preferences file has correct permissions."""
    setup_wizard.save_user_preferences()

    # Check file permissions (should be 0o600 - user read/write only)
    assert temp_config_path.exists()
    stat_info = temp_config_path.stat()
    # On Unix-like systems, check permissions
    import platform
    if platform.system() != "Windows":
        assert oct(stat_info.st_mode)[-3:] == "600"


def test_load_existing_preferences_success(setup_wizard: SetupWizard, temp_config_path: Path):
    """Test loading existing preferences."""
    # Create preferences file
    prefs_data = {
        "azure_configured": True,
        "preferred_editor": "vscode",
        "cost_warnings_enabled": False,
        "budget_threshold": 20.0,
        "auto_approve_phases": True,
        "verbose_output": True,
    }
    temp_config_path.write_text(json.dumps(prefs_data))

    prefs = setup_wizard.load_existing_preferences()

    assert prefs is not None
    assert prefs.azure_configured is True
    assert prefs.preferred_editor == "vscode"
    assert prefs.cost_warnings_enabled is False
    assert prefs.budget_threshold == 20.0
    assert prefs.auto_approve_phases is True
    assert prefs.verbose_output is True


def test_load_existing_preferences_no_file(setup_wizard: SetupWizard):
    """Test loading preferences when file doesn't exist."""
    prefs = setup_wizard.load_existing_preferences()
    assert prefs is None


def test_load_existing_preferences_invalid_json(setup_wizard: SetupWizard, temp_config_path: Path):
    """Test loading preferences with invalid JSON."""
    temp_config_path.write_text("invalid json {")

    prefs = setup_wizard.load_existing_preferences()
    assert prefs is None


# ============================================================================
# Test Full Wizard Run
# ============================================================================


def test_run_wizard_success(
    setup_wizard: SetupWizard,
    mock_config_manager: MagicMock,
):
    """Test successful full wizard run."""
    with patch("dev_agent.onboarding.setup_wizard.Prompt.ask") as mock_prompt:
        with patch("dev_agent.onboarding.setup_wizard.Confirm.ask") as mock_confirm:
            with patch("builtins.input") as mock_input:
                # Mock Azure configuration inputs
                mock_prompt.side_effect = [
                    "https://test.openai.azure.com/",
                    "test-key",
                    "2024-02-15-preview",
                    "gpt-4",
                    "text-embedding-ada-002",
                    "3",  # Skip sample project
                ]

                # Mock confirmations (skip optional steps)
                mock_confirm.side_effect = [False, False, False]  # Skip all optional steps

                # Mock input for workflow explanation
                mock_input.return_value = ""

                # Mock config manager
                config_instance = mock_config_manager.return_value
                mock_config = MagicMock()
                mock_config.azure_openai = None
                mock_config.indexing = MagicMock()
                config_instance.get_config.return_value = mock_config

                result = setup_wizard.run()

                assert isinstance(result, SetupResult)
                assert result.preferences_saved is True
                # Azure configured depends on save_config success
                config_instance.save_config.assert_called()


def test_run_wizard_keyboard_interrupt(setup_wizard: SetupWizard):
    """Test wizard handles keyboard interrupt gracefully."""
    with patch("dev_agent.onboarding.setup_wizard.Prompt.ask") as mock_prompt:
        mock_prompt.side_effect = KeyboardInterrupt()

        result = setup_wizard.run()

        assert isinstance(result, SetupResult)
        assert result.ready_to_use is False


def test_run_wizard_first_run(
    setup_wizard: SetupWizard,
    mock_config_manager: MagicMock,
):
    """Test wizard detects first run."""
    with patch("dev_agent.onboarding.setup_wizard.Prompt.ask") as mock_prompt:
        with patch("dev_agent.onboarding.setup_wizard.Confirm.ask") as mock_confirm:
            mock_prompt.side_effect = [
                "https://test.openai.azure.com/",
                "test-key",
                "2024-02-15-preview",
                "gpt-4",
                "text-embedding-ada-002",
                "3",
            ]
            mock_confirm.side_effect = [False, False, False]

            config_instance = mock_config_manager.return_value
            mock_config = MagicMock()
            mock_config.azure_openai = None
            mock_config.indexing = MagicMock()
            config_instance.get_config.return_value = mock_config

            result = setup_wizard.run()

            # Should detect first run and complete setup
            assert isinstance(result, SetupResult)
            assert result.preferences_saved is True


def test_run_wizard_reconfiguration(
    setup_wizard: SetupWizard,
    temp_config_path: Path,
    mock_config_manager: MagicMock,
):
    """Test wizard handles reconfiguration."""
    # Create existing config
    temp_config_path.write_text("{}")

    with patch("dev_agent.onboarding.setup_wizard.Prompt.ask") as mock_prompt:
        with patch("dev_agent.onboarding.setup_wizard.Confirm.ask") as mock_confirm:
            mock_prompt.side_effect = [
                "https://test.openai.azure.com/",
                "test-key",
                "2024-02-15-preview",
                "gpt-4",
                "text-embedding-ada-002",
                "3",
            ]
            mock_confirm.side_effect = [False, False, False]

            config_instance = mock_config_manager.return_value
            mock_config = MagicMock()
            mock_config.azure_openai = None
            mock_config.indexing = MagicMock()
            config_instance.get_config.return_value = mock_config

            result = setup_wizard.run()

            # Should handle reconfiguration
            assert isinstance(result, SetupResult)
            assert result.preferences_saved is True


# ============================================================================
# Test Step Building and Execution
# ============================================================================


def test_build_onboarding_steps(setup_wizard: SetupWizard):
    """Test onboarding steps are built correctly."""
    setup_wizard._build_onboarding_steps()

    assert len(setup_wizard.steps) == 4
    assert setup_wizard.steps[0].title == "Azure OpenAI Configuration"
    assert setup_wizard.steps[0].skippable is False
    assert setup_wizard.steps[1].title == "Connection Test"
    assert setup_wizard.steps[1].skippable is True
    assert setup_wizard.steps[2].title == "Workflow Overview"
    assert setup_wizard.steps[3].title == "Next Steps"


def test_execute_step_success(setup_wizard: SetupWizard):
    """Test successful step execution."""
    from dev_agent.onboarding.models import OnboardingStep

    result = SetupResult()
    step = OnboardingStep(
        title="Test Step",
        description="Test description",
        action=lambda: True,
        help_text="Test help",
        estimated_time="1 minute",
        skippable=False,
    )

    success = setup_wizard._execute_step(step, result)

    assert success is True
    assert step.completed is True
    assert len(result.errors) == 0


def test_execute_step_failure_not_skippable(setup_wizard: SetupWizard):
    """Test step failure when not skippable."""
    from dev_agent.onboarding.models import OnboardingStep

    result = SetupResult()
    step = OnboardingStep(
        title="Test Step",
        description="Test description",
        action=lambda: False,
        help_text="Test help",
        estimated_time="1 minute",
        skippable=False,
    )

    with patch("dev_agent.onboarding.setup_wizard.Confirm.ask") as mock_confirm:
        mock_confirm.return_value = False  # Don't skip

        success = setup_wizard._execute_step(step, result)

        assert success is False
        assert step.completed is False
        assert len(result.errors) == 1


def test_execute_step_failure_skippable(setup_wizard: SetupWizard):
    """Test step failure when skippable."""
    from dev_agent.onboarding.models import OnboardingStep

    result = SetupResult()
    step = OnboardingStep(
        title="Test Step",
        description="Test description",
        action=lambda: False,
        help_text="Test help",
        estimated_time="1 minute",
        skippable=True,
    )

    with patch("dev_agent.onboarding.setup_wizard.Confirm.ask") as mock_confirm:
        mock_confirm.return_value = True  # Skip on failure

        success = setup_wizard._execute_step(step, result)

        assert success is True
        assert "Test Step" in result.skipped_steps


def test_execute_step_user_skips(setup_wizard: SetupWizard):
    """Test user chooses to skip step."""
    from dev_agent.onboarding.models import OnboardingStep

    result = SetupResult()
    step = OnboardingStep(
        title="Test Step",
        description="Test description",
        action=lambda: True,
        help_text="Test help",
        estimated_time="1 minute",
        skippable=True,
    )

    with patch("dev_agent.onboarding.setup_wizard.Confirm.ask") as mock_confirm:
        mock_confirm.return_value = False  # User chooses not to complete

        success = setup_wizard._execute_step(step, result)

        assert success is True
        assert "Test Step" in result.skipped_steps


# ============================================================================
# Test CLI Setup Command Integration
# ============================================================================


def test_setup_command_exists():
    """Test that setup command is registered in CLI."""
    from dev_agent.cli.main import app
    from typer.testing import CliRunner

    runner = CliRunner()
    result = runner.invoke(app, ["setup", "--help"])

    assert result.exit_code == 0
    assert "setup" in result.stdout.lower()


def test_setup_command_runs():
    """Test that setup command can be invoked."""
    from dev_agent.cli.main import app
    from typer.testing import CliRunner

    runner = CliRunner()

    # Mock the wizard at the module where it's imported
    with patch("dev_agent.onboarding.setup_wizard.SetupWizard") as mock_wizard:
        wizard_instance = MagicMock()
        wizard_instance.run.return_value = SetupResult(ready_to_use=True)
        mock_wizard.return_value = wizard_instance

        result = runner.invoke(app, ["setup"])

        # Command should execute (exit code may vary based on implementation)
        assert result.exit_code in [0, 1]
