#!/bin/bash
# Quick interactive test runner for dev-agent CLI

set -e

echo "🧪 dev-agent Interactive Test Runner"
echo "===================================="
echo ""

# Load Gemini environment variables from file
GEMINI_CONFIG_FILE="gemini.export.txt"

if [ ! -f "$GEMINI_CONFIG_FILE" ]; then
    echo "❌ Error: Gemini configuration file not found: $GEMINI_CONFIG_FILE"
    echo "Please ensure gemini.export.txt exists in the project root."
    exit 1
fi

echo "🔧 Loading Gemini configuration from $GEMINI_CONFIG_FILE"

# Source the gemini configuration file
source "$GEMINI_CONFIG_FILE"

echo "   Model: $GEMINI_MODEL_NAME"
echo "   Embedding Model: $GEMINI_EMBEDDING_MODEL"
echo "   Provider: $PREFERRED_LLM_PROVIDER"
echo ""

# Check if uv is available
if ! command -v uv &> /dev/null; then
    echo "❌ Error: 'uv' command not found. Please install uv first."
    echo "   Visit: https://docs.astral.sh/uv/getting-started/installation/"
    exit 1
fi

# Check if pexpect is available
if ! uv run python -c "import pexpect" &> /dev/null; then
    echo "📦 Installing pexpect for interactive testing..."
    uv sync --dev
fi

# Parse command line arguments
TEST_TYPE="smoke"
DEBUG=""

while [[ $# -gt 0 ]]; do
    case $1 in
        --full)
            TEST_TYPE="full"
            shift
            ;;
        --debug)
            DEBUG="--debug"
            shift
            ;;
        --help|-h)
            echo "Usage: $0 [--full] [--debug] [--help]"
            echo ""
            echo "Options:"
            echo "  --full    Run full workflow test (default: smoke test)"
            echo "  --debug   Enable debug output"
            echo "  --help    Show this help message"
            echo ""
            echo "Examples:"
            echo "  $0                # Run smoke test"
            echo "  $0 --full        # Run full workflow test"
            echo "  $0 --debug       # Run with debug output"
            echo "  $0 --full --debug # Run full test with debug"
            exit 0
            ;;
        *)
            echo "❌ Unknown option: $1"
            echo "Use --help for usage information"
            exit 1
            ;;
    esac
done

echo "🚀 Running ${TEST_TYPE} test on test-app/ directory..."
echo ""

# Run the test using the test-app directory
if uv run python scripts/test_interactive_e2e.py --test-type "$TEST_TYPE" $DEBUG; then
    echo ""
    echo "🎉 Interactive test completed successfully!"
    exit 0
else
    echo ""
    echo "💥 Interactive test failed!"
    echo ""
    echo "Troubleshooting tips:"
    echo "1. Make sure gemini.export.txt exists with valid configuration:"
    echo "   export GEMINI_API_KEY='your-api-key'"
    echo "   export GEMINI_MODEL_NAME='gemini-2.5-flash'"
    echo "   export GEMINI_EMBEDDING_MODEL='gemini-embedding-001'"
    echo "   export PREFERRED_LLM_PROVIDER='gemini'"
    echo ""
    echo "2. Test your configuration:"
    echo "   uv run dev-agent status"
    echo ""
    echo "3. Run with debug output:"
    echo "   $0 --debug"
    exit 1
fi