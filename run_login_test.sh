#!/bin/bash
# Run the login page end-to-end test with Gemini provider

export GEMINI_API_KEY=AIzaSyB7b0svJ7VFJKiCVq5A1xylYjngGR0E-I0
export GEMINI_MODEL_NAME=gemini-2.5-flash
export GEMINI_EMBEDDING_MODEL=gemini-embedding-001
export PREFERRED_LLM_PROVIDER=gemini

echo "Running login page E2E test with Gemini provider..."
echo "Using direct workflow invocation for reliable testing..."
echo ""
uv run python test_login_page_direct.py
