# Platform-Specific Issues and Compatibility Notes

This document tracks platform-specific issues, workarounds, and compatibility notes for dev-agent across different operating systems.

## Overview

dev-agent is designed to work across macOS, Linux, and Windows. This document tracks any platform-specific behaviors, issues, or workarounds needed.

## Platform Support Matrix

| Feature | macOS | Linux | Windows | Notes |
|---------|-------|-------|---------|-------|
| Core CLI | ✅ | ✅ | ✅ | Fully supported |
| File Indexing | ✅ | ✅ | ✅ | Uses pathlib for cross-platform paths |
| Azure OpenAI | ✅ | ✅ | ✅ | Platform-independent |
| Vector Database (FAISS) | ✅ | ✅ | ✅ | Binary wheels available |
| Tree-sitter Parsing | ✅ | ✅ | ✅ | Binary wheels available |
| Interactive CLI | ✅ | ✅ | ⚠️ | Windows terminal may need configuration |
| Rich Terminal Output | ✅ | ✅ | ⚠️ | Windows Terminal recommended |
| File Permissions | ✅ | ✅ | ⚠️ | Windows uses different permission model |
| Environment Variables | ✅ | ✅ | ✅ | Different syntax for setting |

Legend:
- ✅ Fully supported
- ⚠️ Supported with notes/workarounds
- ❌ Not supported
- 🔄 In progress

---

## macOS

### Tested Versions
- macOS 12 (Monterey)
- macOS 13 (Ventura)
- macOS 14 (Sonoma)

### Known Issues
None currently identified.

### Installation Notes
```bash
# Install using uv (recommended)
curl -LsSf https://astral.sh/uv/install.sh | sh
uv sync --dev

# Or using Homebrew
brew install uv
```

### Environment Variables
```bash
# Set in ~/.zshrc or ~/.bash_profile
export AZURE_OPENAI_ENDPOINT="https://your-resource.openai.azure.com/"
export AZURE_OPENAI_API_KEY="your-api-key"
```

### Terminal Compatibility
- ✅ Terminal.app: Fully supported
- ✅ iTerm2: Fully supported
- ✅ VS Code integrated terminal: Fully supported

---

## Linux

### Tested Distributions
- Ubuntu 20.04 LTS
- Ubuntu 22.04 LTS
- Debian 11
- Fedora 38
- Arch Linux (latest)

### Known Issues
None currently identified.

### Installation Notes
```bash
# Install uv
curl -LsSf https://astral.sh/uv/install.sh | sh

# Or using package manager (if available)
# Ubuntu/Debian
sudo apt install python3-pip
pip install uv

# Fedora
sudo dnf install python3-pip
pip install uv

# Arch
sudo pacman -S python-pip
pip install uv
```

### Environment Variables
```bash
# Set in ~/.bashrc or ~/.zshrc
export AZURE_OPENAI_ENDPOINT="https://your-resource.openai.azure.com/"
export AZURE_OPENAI_API_KEY="your-api-key"
```

### Terminal Compatibility
- ✅ GNOME Terminal: Fully supported
- ✅ Konsole: Fully supported
- ✅ xterm: Basic support (limited colors)
- ✅ VS Code integrated terminal: Fully supported

### File System Notes
- File permissions work as expected
- Case-sensitive file systems supported
- Symbolic links handled correctly

---

## Windows

### Tested Versions
- Windows 10 (21H2 and later)
- Windows 11

### Known Issues

#### 1. Terminal Color Support
**Issue**: Older Windows terminals (cmd.exe, older PowerShell) may not display colors correctly.

**Workaround**: Use Windows Terminal (recommended) or update PowerShell to 7+.

```powershell
# Install Windows Terminal from Microsoft Store
# Or download from: https://aka.ms/terminal
```

**Status**: ⚠️ Workaround available

#### 2. Path Separators
**Issue**: Windows uses backslashes (`\`) while Unix uses forward slashes (`/`).

**Solution**: dev-agent uses `pathlib.Path` which handles this automatically. No user action needed.

**Status**: ✅ Resolved in code

#### 3. Environment Variables
**Issue**: Different syntax for setting environment variables.

**Solution**: Use appropriate syntax for your shell.

```powershell
# PowerShell
$env:AZURE_OPENAI_ENDPOINT = "https://your-resource.openai.azure.com/"
$env:AZURE_OPENAI_API_KEY = "your-api-key"

# Or set permanently
[System.Environment]::SetEnvironmentVariable('AZURE_OPENAI_ENDPOINT', 'https://your-resource.openai.azure.com/', 'User')

# Command Prompt (cmd.exe)
set AZURE_OPENAI_ENDPOINT=https://your-resource.openai.azure.com/
set AZURE_OPENAI_API_KEY=your-api-key

# Or set permanently
setx AZURE_OPENAI_ENDPOINT "https://your-resource.openai.azure.com/"
```

**Status**: ✅ Documented

#### 4. File Permissions
**Issue**: Windows uses a different permission model (ACLs) than Unix.

**Solution**: dev-agent checks file readability/writability which works across platforms. Advanced permission checks may behave differently.

**Status**: ⚠️ Basic operations work, advanced permissions may differ

#### 5. Long Path Support
**Issue**: Windows has a 260-character path limit by default.

**Solution**: Enable long path support in Windows 10/11:

```powershell
# Run as Administrator
New-ItemProperty -Path "HKLM:\SYSTEM\CurrentControlSet\Control\FileSystem" -Name "LongPathsEnabled" -Value 1 -PropertyType DWORD -Force
```

Or via Group Policy:
1. Open `gpedit.msc`
2. Navigate to: Computer Configuration > Administrative Templates > System > Filesystem
3. Enable "Enable Win32 long paths"

**Status**: ⚠️ Requires Windows configuration

### Installation Notes

#### Using PowerShell (Recommended)
```powershell
# Install uv
irm https://astral.sh/uv/install.ps1 | iex

# Install dev-agent
uv sync --dev
```

#### Using Windows Subsystem for Linux (WSL)
```bash
# If using WSL, follow Linux instructions
# WSL provides full Linux compatibility
```

### Terminal Compatibility
- ✅ Windows Terminal: Fully supported (recommended)
- ⚠️ PowerShell 7+: Fully supported
- ⚠️ PowerShell 5.1: Basic support (limited colors)
- ⚠️ Command Prompt (cmd.exe): Basic support (no colors)
- ✅ VS Code integrated terminal: Fully supported
- ✅ WSL terminal: Fully supported

### Recommended Setup for Windows
1. Install Windows Terminal from Microsoft Store
2. Install PowerShell 7+ from Microsoft Store or GitHub
3. Use Windows Terminal with PowerShell 7+ as default shell
4. Enable long path support (see above)
5. Set environment variables permanently using `setx` or System Properties

---

## Python Version Compatibility

### Supported Versions
- Python 3.10 ✅
- Python 3.11 ✅
- Python 3.12 ✅
- Python 3.13 ✅

### Minimum Version
Python 3.10 is the minimum required version due to:
- Modern type hints (`list[str]` instead of `List[str]`)
- Pattern matching (if used)
- Performance improvements
- Security updates

### Installation by Platform

#### macOS
```bash
# Using Homebrew
brew install python@3.11

# Using pyenv
pyenv install 3.11.0
pyenv global 3.11.0
```

#### Linux
```bash
# Ubuntu/Debian
sudo apt install python3.11

# Fedora
sudo dnf install python3.11

# Using pyenv
pyenv install 3.11.0
pyenv global 3.11.0
```

#### Windows
```powershell
# Download from python.org
# Or use Microsoft Store
# Or use pyenv-win
```

---

## Dependency Compatibility

### FAISS (Vector Database)
- ✅ macOS: Binary wheels available via PyPI
- ✅ Linux: Binary wheels available via PyPI
- ✅ Windows: Binary wheels available via PyPI

**Note**: FAISS-CPU is used (no GPU required). GPU version (faiss-gpu) is not supported.

### Tree-sitter
- ✅ macOS: Binary wheels available
- ✅ Linux: Binary wheels available
- ✅ Windows: Binary wheels available

**Note**: May require C++ compiler for some platforms if binary wheel not available.

### Azure OpenAI SDK
- ✅ All platforms: Pure Python, no platform-specific issues

---

## File System Considerations

### Case Sensitivity
- **macOS**: Case-insensitive by default (but case-preserving)
- **Linux**: Case-sensitive
- **Windows**: Case-insensitive

**Impact**: File and directory names should be treated as case-insensitive for maximum compatibility.

### Path Length Limits
- **macOS**: 1024 characters
- **Linux**: 4096 characters
- **Windows**: 260 characters (without long path support), 32,767 with long path support

**Recommendation**: Keep project paths reasonably short (<200 characters) for maximum compatibility.

### Special Characters in Filenames
- **macOS**: Most characters allowed except `/` and null
- **Linux**: Most characters allowed except `/` and null
- **Windows**: Restricted characters: `< > : " / \ | ? *`

**Recommendation**: Use alphanumeric characters, hyphens, and underscores for maximum compatibility.

---

## Network and API Considerations

### Azure OpenAI Connectivity
All platforms connect to Azure OpenAI the same way. No platform-specific issues.

### Proxy Support
If behind a corporate proxy:

```bash
# macOS/Linux
export HTTP_PROXY="http://proxy.example.com:8080"
export HTTPS_PROXY="http://proxy.example.com:8080"

# Windows PowerShell
$env:HTTP_PROXY = "http://proxy.example.com:8080"
$env:HTTPS_PROXY = "http://proxy.example.com:8080"
```

---

## Performance Considerations

### Indexing Performance by Platform
Based on testing with 1000+ file codebase:

| Platform | Files/Second | Notes |
|----------|--------------|-------|
| macOS (M1/M2) | 150-200 | Excellent performance |
| macOS (Intel) | 100-150 | Good performance |
| Linux (Modern CPU) | 120-180 | Good performance |
| Windows (Modern CPU) | 100-150 | Good performance |
| Windows (Older CPU) | 80-120 | Acceptable performance |

**Note**: Performance depends heavily on CPU, disk speed, and file system.

### Memory Usage
- Typical: 200-500 MB for medium projects
- Large projects (10K+ files): 500 MB - 1 GB
- No significant platform differences

---

## Testing Recommendations

### Per-Platform Testing Checklist

#### macOS
- [ ] Test on both Intel and Apple Silicon
- [ ] Test with both zsh and bash
- [ ] Test in Terminal.app and iTerm2
- [ ] Verify file permissions work correctly
- [ ] Test with case-insensitive file system

#### Linux
- [ ] Test on Ubuntu LTS (most common)
- [ ] Test on at least one other distribution
- [ ] Test with different terminal emulators
- [ ] Verify file permissions work correctly
- [ ] Test with case-sensitive file system

#### Windows
- [ ] Test on Windows 10 and Windows 11
- [ ] Test in Windows Terminal with PowerShell 7+
- [ ] Test with long path support enabled and disabled
- [ ] Verify environment variable handling
- [ ] Test path handling (backslashes vs forward slashes)
- [ ] Test in WSL for comparison

---

## Troubleshooting

### Common Issues Across Platforms

#### Issue: "Command not found: dev-agent"
**Solution**: Ensure uv installed correctly and PATH updated.

```bash
# macOS/Linux
which uv
uv run dev-agent --help

# Windows
where uv
uv run dev-agent --help
```

#### Issue: "Azure OpenAI authentication failed"
**Solution**: Check environment variables are set correctly.

```bash
# macOS/Linux
echo $AZURE_OPENAI_ENDPOINT
echo $AZURE_OPENAI_API_KEY

# Windows PowerShell
echo $env:AZURE_OPENAI_ENDPOINT
echo $env:AZURE_OPENAI_API_KEY
```

#### Issue: "Permission denied" errors
**Solution**: Check file permissions and ownership.

```bash
# macOS/Linux
ls -la .dev_agent/
chmod -R u+rw .dev_agent/

# Windows
icacls .dev_agent /grant %USERNAME%:F /T
```

---

## Reporting Platform-Specific Issues

When reporting platform-specific issues, include:

1. **Operating System**: Name and version
2. **Python Version**: Output of `python --version`
3. **Terminal**: Which terminal emulator
4. **Shell**: bash, zsh, PowerShell, etc.
5. **Installation Method**: uv, pip, etc.
6. **Error Message**: Full error output
7. **Steps to Reproduce**: Exact commands run

---

## Future Platform Support

### Planned
- 🔄 Better Windows Terminal integration
- 🔄 Improved color support detection
- 🔄 Platform-specific optimizations

### Under Consideration
- Docker container support (platform-independent)
- Cloud-based execution (platform-independent)

---

## Summary

dev-agent is designed to work across all major platforms with minimal platform-specific issues. The main considerations are:

1. **Windows**: Use Windows Terminal and PowerShell 7+ for best experience
2. **All Platforms**: Use pathlib (handled automatically)
3. **All Platforms**: Set environment variables using platform-appropriate syntax
4. **All Platforms**: Ensure Python 3.10+ installed

Most functionality is platform-independent thanks to:
- Python's cross-platform nature
- pathlib for path handling
- Azure OpenAI (cloud-based, platform-independent)
- Modern dependencies with binary wheels

---

**Last Updated**: 2025-01-04
**Status**: Active tracking
