# Cleanup Module API Reference

The cleanup module identifies and removes unnecessary files from the repository while maintaining project integrity.

## Overview

The cleanup system manages:

- **Temporary Files**: `.coverage`, `*.pyc`, `__pycache__/`, cache directories
- **Generated Files**: `site/`, build artifacts, documentation builds
- **Development Artifacts**: `.development/` contents, task summaries
- **Obsolete Examples**: Non-functional or outdated example files
- **Unused Dependencies**: Dependencies not imported in codebase

## Safety Features

- **Dry-run Mode**: Preview changes before execution
- **Backup Creation**: Automatic backups before deletion
- **Category-based Cleanup**: Clean specific categories only
- **User Confirmation**: Prompts for destructive operations
- **Whitelist Protection**: Protected files/directories never removed

## Cleanup Manager

::: dev_agent.cleanup.cleanup_manager
    options:
      show_root_heading: true
      show_source: true
      members_order: source

## Cleanup Models

::: dev_agent.cleanup.models
    options:
      show_root_heading: true
      show_source: true
      members_order: source

## Usage Example

```python
from dev_agent.cleanup.cleanup_manager import CleanupManager
from pathlib import Path

# Create cleanup manager
manager = CleanupManager(project_path=Path("/path/to/project"))

# Scan for cleanup candidates
plan = manager.scan_for_cleanup_candidates()

print(f"Found {len(plan.files_to_remove)} files to remove")
print(f"Estimated size reduction: {plan.total_size_reduction / 1024 / 1024:.2f} MB")

# Execute cleanup in dry-run mode (safe)
result = manager.execute_cleanup(plan, dry_run=True)
print("Dry-run completed - no files were actually removed")

# Execute actual cleanup (after review)
result = manager.execute_cleanup(plan, dry_run=False)
print(f"Removed {len(result.removed_files)} files")
print(f"Actual size reduction: {result.size_reduction / 1024 / 1024:.2f} MB")

# Generate cleanup report
report = manager.generate_cleanup_report(result)
print(f"Report:\n{report}")
```

## CLI Usage

```bash
# Scan for cleanup candidates
dev-agent cleanup --scan

# Preview cleanup (dry-run)
dev-agent cleanup --dry-run

# Execute cleanup with confirmation
dev-agent cleanup --execute

# Clean specific category only
dev-agent cleanup --execute --category temporary

# Available categories:
# - temporary: Cache files, .pyc, __pycache__
# - generated: Build artifacts, documentation builds
# - development: Development artifacts and notes
# - examples: Obsolete example files
# - dependencies: Unused dependencies
```

## Cleanup Plan

A `CleanupPlan` contains:

- **files_to_remove**: List of files to delete
- **directories_to_remove**: List of directories to delete
- **dependencies_to_remove**: List of unused dependencies
- **files_to_move**: Dictionary of files to relocate
- **total_size_reduction**: Estimated space savings in bytes
- **estimated_time**: Estimated time to complete cleanup
- **safety_level**: "safe", "moderate", or "aggressive"

## Cleanup Result

A `CleanupResult` contains:

- **removed_files**: List of successfully removed files
- **removed_directories**: List of successfully removed directories
- **moved_files**: Dictionary of successfully moved files
- **removed_dependencies**: List of removed dependencies
- **errors**: List of errors encountered
- **size_reduction**: Actual space saved in bytes
- **execution_time**: Time taken to complete cleanup

## Safety Levels

### Safe (Default)
- Only removes clearly temporary files
- No risk to project functionality
- Includes: cache files, .pyc, __pycache__

### Moderate
- Removes generated files that can be rebuilt
- Low risk to project functionality
- Includes: safe + build artifacts, documentation builds

### Aggressive
- Removes development artifacts and obsolete examples
- Requires careful review
- Includes: moderate + development notes, unused examples

## Best Practices

1. **Always run --scan first** to review what will be cleaned
2. **Use --dry-run** to preview changes before execution
3. **Review the cleanup plan** carefully, especially for aggressive mode
4. **Backup important files** before running cleanup
5. **Test your project** after cleanup to ensure functionality
6. **Commit cleanup changes** with descriptive commit message
7. **Keep the cleanup report** for documentation
