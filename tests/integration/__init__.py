"""Integration tests for dev-agent.

These tests use real Azure OpenAI API calls and are gated by the
AZURE_OPENAI_INTEGRATION_TESTS environment variable.

To run integration tests:
    export AZURE_OPENAI_INTEGRATION_TESTS=true
    pytest tests/integration/
"""
