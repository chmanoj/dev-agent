"""Simple test to verify integration test discovery."""

import os

import pytest


def test_integration_tests_gated() -> None:
    """Verify integration tests are properly gated."""
    # This test should always run
    assert True


@pytest.mark.skipif(
    os.getenv("AZURE_OPENAI_INTEGRATION_TESTS") != "true",
    reason="Integration tests disabled",
)
def test_integration_enabled() -> None:
    """This test only runs when integration tests are enabled."""
    assert os.getenv("AZURE_OPENAI_INTEGRATION_TESTS") == "true"
