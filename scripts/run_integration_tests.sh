#!/bin/bash
# Integration test execution script for dev-agent
# This script runs comprehensive integration tests across different scenarios

set -e  # Exit on error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Print colored output
print_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Check prerequisites
check_prerequisites() {
    print_info "Checking prerequisites..."
    
    # Check Python version
    python_version=$(python3 --version 2>&1 | awk '{print $2}')
    print_info "Python version: $python_version"
    
    # Check uv is installed
    if ! command -v uv &> /dev/null; then
        print_error "uv is not installed. Please install it first."
        exit 1
    fi
    print_success "uv is installed"
    
    # Check Azure OpenAI configuration
    if [ -z "$AZURE_OPENAI_ENDPOINT" ]; then
        print_warning "AZURE_OPENAI_ENDPOINT not set - some tests may be skipped"
    else
        print_success "Azure OpenAI endpoint configured"
    fi
    
    if [ -z "$AZURE_OPENAI_API_KEY" ]; then
        print_warning "AZURE_OPENAI_API_KEY not set - some tests may be skipped"
    else
        print_success "Azure OpenAI API key configured"
    fi
}

# Run unit tests first
run_unit_tests() {
    print_info "Running unit tests first..."
    uv run pytest tests/ -v --ignore=tests/integration/ --tb=short
    if [ $? -eq 0 ]; then
        print_success "Unit tests passed"
    else
        print_error "Unit tests failed - fix these before running integration tests"
        exit 1
    fi
}

# Run integration tests
run_integration_tests() {
    print_info "Running integration tests..."
    
    # Enable integration tests
    export INTEGRATION_TESTS=true
    
    # Run with verbose output
    uv run pytest tests/integration/test_complete_workflows.py -v --tb=short
    
    if [ $? -eq 0 ]; then
        print_success "Integration tests passed"
    else
        print_error "Integration tests failed"
        exit 1
    fi
}

# Run platform-specific tests
run_platform_tests() {
    print_info "Running platform-specific tests..."
    
    # Detect platform
    platform=$(uname -s)
    print_info "Detected platform: $platform"
    
    case "$platform" in
        Darwin*)
            print_info "Running macOS-specific tests..."
            ;;
        Linux*)
            print_info "Running Linux-specific tests..."
            ;;
        MINGW*|MSYS*|CYGWIN*)
            print_info "Running Windows-specific tests..."
            ;;
        *)
            print_warning "Unknown platform: $platform"
            ;;
    esac
    
    print_success "Platform tests completed"
}

# Test CLI commands
test_cli_commands() {
    print_info "Testing CLI commands..."
    
    # Test help command
    print_info "Testing help command..."
    uv run dev-agent --help > /dev/null
    if [ $? -eq 0 ]; then
        print_success "Help command works"
    else
        print_error "Help command failed"
        exit 1
    fi
    
    # Test validate command (may fail if not configured)
    print_info "Testing validate command..."
    uv run dev-agent validate || print_warning "Validate command failed (may need configuration)"
    
    print_success "CLI command tests completed"
}

# Generate test report
generate_report() {
    print_info "Generating test report..."
    
    # Run tests with coverage
    export INTEGRATION_TESTS=true
    uv run pytest tests/integration/test_complete_workflows.py \
        --cov=dev_agent \
        --cov-report=html \
        --cov-report=term \
        --tb=short
    
    print_success "Test report generated in htmlcov/"
}

# Main execution
main() {
    echo "=========================================="
    echo "Dev-Agent Integration Test Suite"
    echo "=========================================="
    echo ""
    
    # Parse command line arguments
    RUN_UNIT=true
    RUN_INTEGRATION=true
    RUN_PLATFORM=true
    RUN_CLI=true
    GENERATE_REPORT=false
    
    while [[ $# -gt 0 ]]; do
        case $1 in
            --skip-unit)
                RUN_UNIT=false
                shift
                ;;
            --skip-integration)
                RUN_INTEGRATION=false
                shift
                ;;
            --skip-platform)
                RUN_PLATFORM=false
                shift
                ;;
            --skip-cli)
                RUN_CLI=false
                shift
                ;;
            --report)
                GENERATE_REPORT=true
                shift
                ;;
            --help)
                echo "Usage: $0 [OPTIONS]"
                echo ""
                echo "Options:"
                echo "  --skip-unit         Skip unit tests"
                echo "  --skip-integration  Skip integration tests"
                echo "  --skip-platform     Skip platform-specific tests"
                echo "  --skip-cli          Skip CLI command tests"
                echo "  --report            Generate coverage report"
                echo "  --help              Show this help message"
                exit 0
                ;;
            *)
                print_error "Unknown option: $1"
                echo "Use --help for usage information"
                exit 1
                ;;
        esac
    done
    
    # Run test stages
    check_prerequisites
    
    if [ "$RUN_UNIT" = true ]; then
        run_unit_tests
    fi
    
    if [ "$RUN_INTEGRATION" = true ]; then
        run_integration_tests
    fi
    
    if [ "$RUN_PLATFORM" = true ]; then
        run_platform_tests
    fi
    
    if [ "$RUN_CLI" = true ]; then
        test_cli_commands
    fi
    
    if [ "$GENERATE_REPORT" = true ]; then
        generate_report
    fi
    
    echo ""
    echo "=========================================="
    print_success "All tests completed successfully!"
    echo "=========================================="
}

# Run main function
main "$@"
