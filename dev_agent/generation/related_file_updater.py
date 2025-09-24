"""Related file updater for maintaining consistency across the codebase.

This module handles updating imports, configurations, and dependencies
when new code is generated.
"""

from __future__ import annotations

import ast
import json
import re
from pathlib import Path
from typing import Any

from ..interfaces.analysis_interface import ICodebaseAnalyzer
from ..models.results import GeneratedCode


class RelatedFileUpdate:
    """Represents an update needed in a related file."""

    def __init__(
        self,
        file_path: str,
        update_type: str,
        old_content: str,
        new_content: str,
        line_number: int | None = None,
        reason: str = "",
    ):
        """Initialize a related file update."""
        self.file_path = file_path
        self.update_type = update_type
        self.old_content = old_content
        self.new_content = new_content
        self.line_number = line_number
        self.reason = reason


class RelatedFileUpdater:
    """Updates related files when new code is generated."""

    def __init__(self, codebase_analyzer: ICodebaseAnalyzer):
        """Initialize the related file updater."""
        self.codebase_analyzer = codebase_analyzer

    def update_related_files(
        self, primary_code: GeneratedCode, context: Any
    ) -> list[RelatedFileUpdate]:
        """Update related files based on generated code."""
        updates = []

        # Update import statements
        updates.extend(self._update_imports(primary_code, context))

        # Update configuration files
        updates.extend(self._update_configurations(primary_code, context))

        # Update dependency files
        updates.extend(self._update_dependencies(primary_code, context))

        # Update __init__.py files
        updates.extend(self._update_init_files(primary_code, context))

        return updates

    def _update_imports(
        self, primary_code: GeneratedCode, context: Any
    ) -> list[RelatedFileUpdate]:
        """Update import statements in related files."""
        updates = []

        # Find files that might need to import the new code
        related_files = self._find_files_needing_imports(primary_code, context)

        for file_path in related_files:
            if Path(file_path).exists():
                try:
                    with open(file_path, "r", encoding="utf-8") as f:
                        content = f.read()

                    new_import = self._generate_import_statement(primary_code, file_path)
                    if new_import and new_import not in content:
                        updated_content = self._add_import_to_file(content, new_import)
                        
                        updates.append(RelatedFileUpdate(
                            file_path=file_path,
                            update_type="import",
                            old_content=content,
                            new_content=updated_content,
                            reason=f"Add import for {primary_code.file_path}"
                        ))

                except Exception:
                    continue

        return updates 
   def _update_configurations(
        self, primary_code: GeneratedCode, context: Any
    ) -> list[RelatedFileUpdate]:
        """Update configuration files."""
        updates = []

        # Update pyproject.toml if new dependencies are added
        if primary_code.dependencies:
            pyproject_path = "pyproject.toml"
            if Path(pyproject_path).exists():
                update = self._update_pyproject_toml(primary_code, pyproject_path)
                if update:
                    updates.append(update)

        # Update requirements.txt if it exists
        requirements_path = "requirements.txt"
        if Path(requirements_path).exists() and primary_code.dependencies:
            update = self._update_requirements_txt(primary_code, requirements_path)
            if update:
                updates.append(update)

        return updates

    def _update_dependencies(
        self, primary_code: GeneratedCode, context: Any
    ) -> list[RelatedFileUpdate]:
        """Update dependency-related files."""
        updates = []

        # Update setup.py if it exists (legacy)
        setup_path = "setup.py"
        if Path(setup_path).exists() and primary_code.dependencies:
            update = self._update_setup_py(primary_code, setup_path)
            if update:
                updates.append(update)

        return updates

    def _update_init_files(
        self, primary_code: GeneratedCode, context: Any
    ) -> list[RelatedFileUpdate]:
        """Update __init__.py files to expose new modules."""
        updates = []

        # Determine the package directory
        file_path = Path(primary_code.file_path)
        package_dir = file_path.parent

        # Update __init__.py in the same directory
        init_path = package_dir / "__init__.py"
        if init_path.exists():
            update = self._update_init_py(primary_code, str(init_path))
            if update:
                updates.append(update)

        return updates

    def _find_files_needing_imports(
        self, primary_code: GeneratedCode, context: Any
    ) -> list[str]:
        """Find files that might need to import the new code."""
        files = []

        # Look for files in the same package
        file_path = Path(primary_code.file_path)
        package_dir = file_path.parent

        # Find Python files in the same directory
        for py_file in package_dir.glob("*.py"):
            if py_file.name != file_path.name and py_file.name != "__init__.py":
                files.append(str(py_file))

        # Look for test files
        test_patterns = [
            f"test_{file_path.stem}.py",
            f"tests/test_{file_path.stem}.py",
            f"test/test_{file_path.stem}.py",
        ]

        for pattern in test_patterns:
            test_path = Path(pattern)
            if test_path.exists():
                files.append(str(test_path))

        return files

    def _generate_import_statement(self, primary_code: GeneratedCode, target_file: str) -> str | None:
        """Generate appropriate import statement for the target file."""
        source_path = Path(primary_code.file_path)
        target_path = Path(target_file)

        # Extract module name and classes/functions to import
        importable_items = self._extract_importable_items(primary_code.code)
        
        if not importable_items:
            return None

        # Calculate relative import path
        try:
            # Convert file paths to module paths
            source_module = self._file_path_to_module(source_path)
            target_module = self._file_path_to_module(target_path)

            # Determine if we need relative or absolute import
            if source_module and target_module:
                # Use relative import if in same package
                source_parts = source_module.split('.')
                target_parts = target_module.split('.')

                # Find common prefix
                common_len = 0
                for i, (s, t) in enumerate(zip(source_parts, target_parts)):
                    if s == t:
                        common_len = i + 1
                    else:
                        break

                if common_len > 0:
                    # Use relative import
                    relative_parts = source_parts[common_len:]
                    if relative_parts:
                        module_path = '.'.join(relative_parts)
                        return f"from .{module_path} import {', '.join(importable_items)}"
                    else:
                        return f"from . import {', '.join(importable_items)}"

                # Use absolute import
                return f"from {source_module} import {', '.join(importable_items)}"

        except Exception:
            pass

        return None

    def _extract_importable_items(self, code: str) -> list[str]:
        """Extract classes and functions that can be imported."""
        items = []

        try:
            tree = ast.parse(code)

            for node in ast.walk(tree):
                if isinstance(node, ast.ClassDef):
                    if not node.name.startswith('_'):  # Skip private classes
                        items.append(node.name)
                elif isinstance(node, ast.FunctionDef):
                    if not node.name.startswith('_'):  # Skip private functions
                        items.append(node.name)

        except SyntaxError:
            pass

        return items

    def _file_path_to_module(self, file_path: Path) -> str | None:
        """Convert file path to Python module path."""
        try:
            # Remove .py extension
            parts = list(file_path.parts)
            if parts[-1].endswith('.py'):
                parts[-1] = parts[-1][:-3]

            # Find the package root (look for setup.py, pyproject.toml, or src/)
            package_root_idx = 0
            for i, part in enumerate(parts):
                if part in ['src', 'dev_agent']:  # Common package directories
                    package_root_idx = i
                    break

            # Extract module path from package root
            module_parts = parts[package_root_idx:]
            return '.'.join(module_parts)

        except Exception:
            return None

    def _add_import_to_file(self, content: str, new_import: str) -> str:
        """Add import statement to file content."""
        lines = content.split('\n')
        
        # Find the right place to insert the import
        insert_idx = 0
        
        # Skip module docstring
        in_docstring = False
        for i, line in enumerate(lines):
            stripped = line.strip()
            
            if stripped.startswith('"""') or stripped.startswith("'''"):
                if not in_docstring:
                    in_docstring = True
                elif stripped.endswith('"""') or stripped.endswith("'''"):
                    in_docstring = False
                    insert_idx = i + 1
            elif not in_docstring and (stripped.startswith('import ') or stripped.startswith('from ')):
                # Found existing imports, insert after the last import
                insert_idx = i + 1
            elif not in_docstring and stripped and not stripped.startswith('#'):
                # Found non-import, non-comment code
                break

        # Insert the new import
        lines.insert(insert_idx, new_import)
        
        return '\n'.join(lines)

    def _update_pyproject_toml(self, primary_code: GeneratedCode, file_path: str) -> RelatedFileUpdate | None:
        """Update pyproject.toml with new dependencies."""
        try:
            import tomli
            import tomli_w
            
            with open(file_path, "rb") as f:
                data = tomli.load(f)

            # Add new dependencies
            project = data.setdefault('project', {})
            dependencies = project.setdefault('dependencies', [])

            new_deps = []
            for dep in primary_code.dependencies:
                # Convert internal dependency names to actual package names
                package_name = self._map_dependency_to_package(dep)
                if package_name and package_name not in dependencies:
                    new_deps.append(package_name)

            if new_deps:
                dependencies.extend(new_deps)
                
                # Write back to file
                with open(file_path, "wb") as f:
                    tomli_w.dump(data, f)

                return RelatedFileUpdate(
                    file_path=file_path,
                    update_type="configuration",
                    old_content="",  # Would need to read original
                    new_content="",  # Would need to read updated
                    reason=f"Add dependencies: {', '.join(new_deps)}"
                )

        except Exception:
            pass

        return None

    def _update_requirements_txt(self, primary_code: GeneratedCode, file_path: str) -> RelatedFileUpdate | None:
        """Update requirements.txt with new dependencies."""
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                content = f.read()

            lines = content.strip().split('\n')
            existing_packages = {line.split('==')[0].split('>=')[0].split('<=')[0] for line in lines if line.strip()}

            new_deps = []
            for dep in primary_code.dependencies:
                package_name = self._map_dependency_to_package(dep)
                if package_name and package_name not in existing_packages:
                    new_deps.append(package_name)

            if new_deps:
                lines.extend(new_deps)
                new_content = '\n'.join(lines) + '\n'

                return RelatedFileUpdate(
                    file_path=file_path,
                    update_type="configuration",
                    old_content=content,
                    new_content=new_content,
                    reason=f"Add dependencies: {', '.join(new_deps)}"
                )

        except Exception:
            pass

        return None

    def _update_setup_py(self, primary_code: GeneratedCode, file_path: str) -> RelatedFileUpdate | None:
        """Update setup.py with new dependencies."""
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                content = f.read()

            # This is a simplified approach - in practice, you'd need more sophisticated parsing
            new_deps = []
            for dep in primary_code.dependencies:
                package_name = self._map_dependency_to_package(dep)
                if package_name and package_name not in content:
                    new_deps.append(package_name)

            if new_deps:
                # Find install_requires and add dependencies
                # This is a very basic implementation
                install_requires_pattern = r"install_requires\s*=\s*\[(.*?)\]"
                match = re.search(install_requires_pattern, content, re.DOTALL)
                
                if match:
                    existing_deps = match.group(1)
                    new_deps_str = ', '.join(f'"{dep}"' for dep in new_deps)
                    
                    if existing_deps.strip():
                        updated_deps = f"{existing_deps}, {new_deps_str}"
                    else:
                        updated_deps = new_deps_str
                    
                    new_content = content.replace(match.group(1), updated_deps)

                    return RelatedFileUpdate(
                        file_path=file_path,
                        update_type="configuration",
                        old_content=content,
                        new_content=new_content,
                        reason=f"Add dependencies: {', '.join(new_deps)}"
                    )

        except Exception:
            pass

        return None

    def _update_init_py(self, primary_code: GeneratedCode, file_path: str) -> RelatedFileUpdate | None:
        """Update __init__.py to expose new modules."""
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                content = f.read()

            # Extract importable items from the new code
            importable_items = self._extract_importable_items(primary_code.code)
            
            if not importable_items:
                return None

            # Generate import statement for __init__.py
            module_name = Path(primary_code.file_path).stem
            new_imports = []

            for item in importable_items:
                import_line = f"from .{module_name} import {item}"
                if import_line not in content:
                    new_imports.append(import_line)

            if new_imports:
                # Add imports to the file
                if content.strip():
                    new_content = content + '\n' + '\n'.join(new_imports) + '\n'
                else:
                    new_content = '\n'.join(new_imports) + '\n'

                return RelatedFileUpdate(
                    file_path=file_path,
                    update_type="import",
                    old_content=content,
                    new_content=new_content,
                    reason=f"Expose new module: {module_name}"
                )

        except Exception:
            pass

        return None

    def _map_dependency_to_package(self, dependency: str) -> str | None:
        """Map internal dependency names to actual package names."""
        mapping = {
            'database': 'sqlalchemy',
            'web_framework': 'fastapi',
            'json': None,  # Built-in, no package needed
            'pytest': 'pytest',
            'http': 'httpx',
            'requests': 'requests',
        }

        return mapping.get(dependency, dependency)