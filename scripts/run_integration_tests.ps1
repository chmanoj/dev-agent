# Integration test execution script for dev-agent (Windows PowerShell)
# This script runs comprehensive integration tests across different scenarios

# Set error action preference
$ErrorActionPreference = "Stop"

# Color functions
function Write-Info {
    param([string]$Message)
    Write-Host "[INFO] $Message" -ForegroundColor Blue
}

function Write-Success {
    param([string]$Message)
    Write-Host "[SUCCESS] $Message" -ForegroundColor Green
}

function Write-Warning {
    param([string]$Message)
    Write-Host "[WARNING] $Message" -ForegroundColor Yellow
}

function Write-Error {
    param([string]$Message)
    Write-Host "[ERROR] $Message" -ForegroundColor Red
}

# Check prerequisites
function Test-Prerequisites {
    Write-Info "Checking prerequisites..."
    
    # Check Python version
    try {
        $pythonVersion = python --version 2>&1
        Write-Info "Python version: $pythonVersion"
    }
    catch {
        Write-Error "Python is not installed or not in PATH"
        exit 1
    }
    
    # Check uv is installed
    try {
        $uvVersion = uv --version 2>&1
        Write-Success "uv is installed: $uvVersion"
    }
    catch {
        Write-Error "uv is not installed. Please install it first."
        exit 1
    }
    
    # Check Azure OpenAI configuration
    if (-not $env:AZURE_OPENAI_ENDPOINT) {
        Write-Warning "AZURE_OPENAI_ENDPOINT not set - some tests may be skipped"
    }
    else {
        Write-Success "Azure OpenAI endpoint configured"
    }
    
    if (-not $env:AZURE_OPENAI_API_KEY) {
        Write-Warning "AZURE_OPENAI_API_KEY not set - some tests may be skipped"
    }
    else {
        Write-Success "Azure OpenAI API key configured"
    }
}

# Run unit tests first
function Invoke-UnitTests {
    Write-Info "Running unit tests first..."
    
    try {
        uv run pytest tests/ -v --ignore=tests/integration/ --tb=short
        Write-Success "Unit tests passed"
    }
    catch {
        Write-Error "Unit tests failed - fix these before running integration tests"
        exit 1
    }
}

# Run integration tests
function Invoke-IntegrationTests {
    Write-Info "Running integration tests..."
    
    # Enable integration tests
    $env:INTEGRATION_TESTS = "true"
    
    try {
        uv run pytest tests/integration/test_complete_workflows.py -v --tb=short
        Write-Success "Integration tests passed"
    }
    catch {
        Write-Error "Integration tests failed"
        exit 1
    }
}

# Run platform-specific tests
function Invoke-PlatformTests {
    Write-Info "Running platform-specific tests..."
    
    # Detect Windows version
    $osInfo = Get-CimInstance Win32_OperatingSystem
    Write-Info "Detected OS: $($osInfo.Caption) $($osInfo.Version)"
    
    # Check Windows Terminal
    if (Get-Command wt -ErrorAction SilentlyContinue) {
        Write-Success "Windows Terminal is installed"
    }
    else {
        Write-Warning "Windows Terminal not found - recommended for best experience"
    }
    
    # Check PowerShell version
    Write-Info "PowerShell version: $($PSVersionTable.PSVersion)"
    if ($PSVersionTable.PSVersion.Major -ge 7) {
        Write-Success "PowerShell 7+ detected"
    }
    else {
        Write-Warning "PowerShell 5.1 detected - consider upgrading to PowerShell 7+"
    }
    
    Write-Success "Platform tests completed"
}

# Test CLI commands
function Test-CLICommands {
    Write-Info "Testing CLI commands..."
    
    # Test help command
    Write-Info "Testing help command..."
    try {
        uv run dev-agent --help | Out-Null
        Write-Success "Help command works"
    }
    catch {
        Write-Error "Help command failed"
        exit 1
    }
    
    # Test validate command (may fail if not configured)
    Write-Info "Testing validate command..."
    try {
        uv run dev-agent validate
    }
    catch {
        Write-Warning "Validate command failed (may need configuration)"
    }
    
    Write-Success "CLI command tests completed"
}

# Generate test report
function New-TestReport {
    Write-Info "Generating test report..."
    
    # Enable integration tests
    $env:INTEGRATION_TESTS = "true"
    
    try {
        uv run pytest tests/integration/test_complete_workflows.py `
            --cov=dev_agent `
            --cov-report=html `
            --cov-report=term `
            --tb=short
        
        Write-Success "Test report generated in htmlcov/"
    }
    catch {
        Write-Error "Failed to generate test report"
        exit 1
    }
}

# Main execution
function Main {
    param(
        [switch]$SkipUnit,
        [switch]$SkipIntegration,
        [switch]$SkipPlatform,
        [switch]$SkipCLI,
        [switch]$Report,
        [switch]$Help
    )
    
    if ($Help) {
        Write-Host @"
Dev-Agent Integration Test Suite (Windows)

Usage: .\run_integration_tests.ps1 [OPTIONS]

Options:
  -SkipUnit         Skip unit tests
  -SkipIntegration  Skip integration tests
  -SkipPlatform     Skip platform-specific tests
  -SkipCLI          Skip CLI command tests
  -Report           Generate coverage report
  -Help             Show this help message

Examples:
  .\run_integration_tests.ps1
  .\run_integration_tests.ps1 -SkipUnit
  .\run_integration_tests.ps1 -Report
"@
        exit 0
    }
    
    Write-Host "=========================================="
    Write-Host "Dev-Agent Integration Test Suite (Windows)"
    Write-Host "=========================================="
    Write-Host ""
    
    # Run test stages
    Test-Prerequisites
    
    if (-not $SkipUnit) {
        Invoke-UnitTests
    }
    
    if (-not $SkipIntegration) {
        Invoke-IntegrationTests
    }
    
    if (-not $SkipPlatform) {
        Invoke-PlatformTests
    }
    
    if (-not $SkipCLI) {
        Test-CLICommands
    }
    
    if ($Report) {
        New-TestReport
    }
    
    Write-Host ""
    Write-Host "=========================================="
    Write-Success "All tests completed successfully!"
    Write-Host "=========================================="
}

# Run main function with parameters
Main @args
