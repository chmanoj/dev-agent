"""API update propagation for maintaining consistency across client code.

This module handles updating client code and documentation when APIs change.
"""

from __future__ import annotations

import ast
import json
import re
from pathlib import Path
from typing import Any

from ..interfaces.analysis_interface import ICodebaseAnalyzer
from ..models.results import GeneratedCode


class APIChange:
    """Represents a change to an API."""

    def __init__(
        self,
        change_type: str,  # 'added', 'modified', 'removed', 'deprecated'
        api_type: str,     # 'function', 'class', 'method', 'endpoint'
        name: str,
        old_signature: str | None = None,
        new_signature: str | None = None,
        description: str = "",
        breaking_change: bool = False,
    ):
        """Initialize an API change."""
        self.change_type = change_type
        self.api_type = api_type
        self.name = name
        self.old_signature = old_signature
        self.new_signature = new_signature
        self.description = description
        self.breaking_change = breaking_change


class APIUpdatePropagator:
    """Propagates API changes to client code and documentation."""

    def __init__(self, codebase_analyzer: ICodebaseAnalyzer):
        """Initialize the API update propagator."""
        self.codebase_analyzer = codebase_analyzer

    def propagate_api_changes(
        self, primary_code: GeneratedCode, context: Any
    ) -> list[dict[str, Any]]:
        """Propagate API changes to client code and documentation."""
        # Detect API changes in the generated code
        api_changes = self._detect_api_changes(primary_code, context)

        if not api_changes:
            return []

        propagation_results = []

        # Update client code
        client_updates = self._update_client_code(api_changes, context)
        if client_updates:
            propagation_results.extend(client_updates)

        # Update API documentation
        doc_updates = self._update_api_documentation(api_changes, context)
        if doc_updates:
            propagation_results.extend(doc_updates)

        # Update OpenAPI specifications
        openapi_updates = self._update_openapi_specs(api_changes, context)
        if openapi_updates:
            propagation_results.extend(openapi_updates)

        # Generate migration guides for breaking changes
        migration_guides = self._generate_migration_guides(api_changes, context)
        if migration_guides:
            propagation_results.extend(migration_guides)

        return propagation_results

    def _detect_api_changes(
        self, primary_code: GeneratedCode, context: Any
    ) -> list[APIChange]:
        """Detect API changes in the generated code."""
        changes = []

        try:
            tree = ast.parse(primary_code.code)

            # Detect new functions and classes
            for node in ast.walk(tree):
                if isinstance(node, ast.FunctionDef):
                    if not node.name.startswith('_'):  # Public function
                        change = APIChange(
                            change_type='added',
                            api_type='function',
                            name=node.name,
                            new_signature=self._extract_function_signature(node),
                            description=f"New function: {node.name}",
                        )
                        changes.append(change)

                elif isinstance(node, ast.ClassDef):
                    if not node.name.startswith('_'):  # Public class
                        change = APIChange(
                            change_type='added',
                            api_type='class',
                            name=node.name,
                            new_signature=self._extract_class_signature(node),
                            description=f"New class: {node.name}",
                        )
                        changes.append(change)

                        # Detect public methods
                        for item in node.body:
                            if isinstance(item, ast.FunctionDef) and not item.name.startswith('_'):
                                method_change = APIChange(
                                    change_type='added',
                                    api_type='method',
                                    name=f"{node.name}.{item.name}",
                                    new_signature=self._extract_function_signature(item),
                                    description=f"New method: {node.name}.{item.name}",
                                )
                                changes.append(method_change)

        except SyntaxError:
            pass

        # Detect web API endpoints if using FastAPI or similar
        endpoint_changes = self._detect_endpoint_changes(primary_code.code)
        changes.extend(endpoint_changes)

        return changes

    def _detect_endpoint_changes(self, code: str) -> list[APIChange]:
        """Detect web API endpoint changes."""
        changes = []

        try:
            tree = ast.parse(code)

            for node in ast.walk(tree):
                if isinstance(node, ast.FunctionDef):
                    # Look for FastAPI decorators
                    for decorator in node.decorator_list:
                        if isinstance(decorator, ast.Call):
                            if hasattr(decorator.func, 'attr') and decorator.func.attr in [
                                'get', 'post', 'put', 'delete', 'patch'
                            ]:
                                endpoint_path = self._extract_endpoint_path(decorator)
                                change = APIChange(
                                    change_type='added',
                                    api_type='endpoint',
                                    name=f"{decorator.func.attr.upper()} {endpoint_path}",
                                    new_signature=self._extract_function_signature(node),
                                    description=f"New API endpoint: {decorator.func.attr.upper()} {endpoint_path}",
                                )
                                changes.append(change)

        except SyntaxError:
            pass

        return changes

    def _extract_function_signature(self, node: ast.FunctionDef) -> str:
        """Extract function signature as string."""
        try:
            # Build parameter list
            params = []
            
            # Regular parameters
            for arg in node.args.args:
                param_str = arg.arg
                if arg.annotation:
                    param_str += f": {ast.unparse(arg.annotation)}"
                params.append(param_str)

            # Default values
            defaults_start = len(params) - len(node.args.defaults)
            for i, default in enumerate(node.args.defaults):
                if defaults_start + i < len(params):
                    params[defaults_start + i] += f" = {ast.unparse(default)}"

            # Return type
            return_type = ""
            if node.returns:
                return_type = f" -> {ast.unparse(node.returns)}"

            return f"{node.name}({', '.join(params)}){return_type}"

        except Exception:
            return f"{node.name}(...)"

    def _extract_class_signature(self, node: ast.ClassDef) -> str:
        """Extract class signature as string."""
        try:
            base_classes = [ast.unparse(base) for base in node.bases]
            if base_classes:
                return f"{node.name}({', '.join(base_classes)})"
            else:
                return node.name
        except Exception:
            return node.name

    def _extract_endpoint_path(self, decorator: ast.Call) -> str:
        """Extract endpoint path from FastAPI decorator."""
        try:
            if decorator.args and isinstance(decorator.args[0], ast.Constant):
                return decorator.args[0].value
        except Exception:
            pass
        return "/"

    def _update_client_code(
        self, api_changes: list[APIChange], context: Any
    ) -> list[dict[str, Any]]:
        """Update client code that uses the changed APIs."""
        updates = []

        # Find files that might be using the APIs
        client_files = self._find_client_files(api_changes, context)

        for file_path in client_files:
            if Path(file_path).exists():
                try:
                    with open(file_path, "r", encoding="utf-8") as f:
                        content = f.read()

                    updated_content = self._update_file_for_api_changes(content, api_changes)
                    
                    if updated_content != content:
                        updates.append({
                            'type': 'client_code_update',
                            'file_path': file_path,
                            'old_content': content,
                            'new_content': updated_content,
                            'changes': [change.name for change in api_changes],
                        })

                except Exception:
                    continue

        return updates

    def _update_api_documentation(
        self, api_changes: list[APIChange], context: Any
    ) -> list[dict[str, Any]]:
        """Update API documentation with new changes."""
        updates = []

        # Find documentation files
        doc_files = self._find_documentation_files()

        for doc_file in doc_files:
            try:
                with open(doc_file, "r", encoding="utf-8") as f:
                    content = f.read()

                updated_content = self._add_api_documentation(content, api_changes)
                
                if updated_content != content:
                    updates.append({
                        'type': 'documentation_update',
                        'file_path': doc_file,
                        'old_content': content,
                        'new_content': updated_content,
                        'changes': [change.name for change in api_changes],
                    })

            except Exception:
                continue

        return updates

    def _update_openapi_specs(
        self, api_changes: list[APIChange], context: Any
    ) -> list[dict[str, Any]]:
        """Update OpenAPI specifications with new endpoints."""
        updates = []

        # Find OpenAPI spec files
        openapi_files = list(Path(".").glob("**/openapi.json")) + list(Path(".").glob("**/swagger.json"))

        for spec_file in openapi_files:
            try:
                with open(spec_file, "r", encoding="utf-8") as f:
                    spec_data = json.load(f)

                updated_spec = self._update_openapi_spec(spec_data, api_changes)
                
                if updated_spec != spec_data:
                    with open(spec_file, "w", encoding="utf-8") as f:
                        json.dump(updated_spec, f, indent=2)

                    updates.append({
                        'type': 'openapi_spec_update',
                        'file_path': str(spec_file),
                        'changes': [change.name for change in api_changes if change.api_type == 'endpoint'],
                    })

            except Exception:
                continue

        return updates

    def _generate_migration_guides(
        self, api_changes: list[APIChange], context: Any
    ) -> list[dict[str, Any]]:
        """Generate migration guides for breaking changes."""
        breaking_changes = [change for change in api_changes if change.breaking_change]
        
        if not breaking_changes:
            return []

        migration_guide = self._create_migration_guide(breaking_changes)
        
        # Save migration guide
        migration_file = Path("MIGRATION.md")
        try:
            existing_content = ""
            if migration_file.exists():
                with open(migration_file, "r", encoding="utf-8") as f:
                    existing_content = f.read()

            new_content = existing_content + "\n\n" + migration_guide

            with open(migration_file, "w", encoding="utf-8") as f:
                f.write(new_content)

            return [{
                'type': 'migration_guide',
                'file_path': str(migration_file),
                'changes': [change.name for change in breaking_changes],
            }]

        except Exception:
            return []

    def _find_client_files(
        self, api_changes: list[APIChange], context: Any
    ) -> list[str]:
        """Find files that might be using the changed APIs."""
        client_files = []

        # Look for Python files that might import or use the APIs
        for py_file in Path(".").glob("**/*.py"):
            if py_file.name.startswith("test_"):
                continue  # Skip test files for now

            try:
                with open(py_file, "r", encoding="utf-8") as f:
                    content = f.read()

                # Check if any of the changed APIs are referenced
                for change in api_changes:
                    if change.name in content:
                        client_files.append(str(py_file))
                        break

            except Exception:
                continue

        return client_files

    def _find_documentation_files(self) -> list[str]:
        """Find documentation files that might need updating."""
        doc_files = []

        # Common documentation patterns
        patterns = [
            "**/README.md",
            "**/API.md",
            "**/docs/**/*.md",
            "**/documentation/**/*.md",
        ]

        for pattern in patterns:
            doc_files.extend([str(f) for f in Path(".").glob(pattern)])

        return doc_files

    def _update_file_for_api_changes(
        self, content: str, api_changes: list[APIChange]
    ) -> str:
        """Update file content for API changes."""
        updated_content = content

        for change in api_changes:
            if change.change_type == 'added':
                # For new APIs, we might want to add usage examples or imports
                # This is a simplified implementation
                continue
            elif change.change_type == 'modified':
                # Update function calls to match new signature
                updated_content = self._update_function_calls(updated_content, change)
            elif change.change_type == 'removed':
                # Add deprecation warnings or remove usage
                updated_content = self._handle_removed_api(updated_content, change)

        return updated_content

    def _update_function_calls(self, content: str, change: APIChange) -> str:
        """Update function calls to match new API signature."""
        # This is a simplified implementation
        # In practice, you'd need more sophisticated AST manipulation
        
        if change.old_signature and change.new_signature:
            # Extract function name
            old_name = change.old_signature.split('(')[0]
            new_name = change.new_signature.split('(')[0]
            
            if old_name != new_name:
                # Function was renamed
                content = re.sub(rf'\b{re.escape(old_name)}\b', new_name, content)

        return content

    def _handle_removed_api(self, content: str, change: APIChange) -> str:
        """Handle removed API by adding warnings or comments."""
        # Add deprecation comments
        api_name = change.name
        
        # Find usage and add warning comments
        lines = content.split('\n')
        updated_lines = []
        
        for line in lines:
            if api_name in line and not line.strip().startswith('#'):
                # Add warning comment above the line
                indent = len(line) - len(line.lstrip())
                warning = ' ' * indent + f"# WARNING: {api_name} has been removed"
                updated_lines.append(warning)
            
            updated_lines.append(line)

        return '\n'.join(updated_lines)

    def _add_api_documentation(self, content: str, api_changes: list[APIChange]) -> str:
        """Add documentation for new APIs."""
        new_sections = []

        for change in api_changes:
            if change.change_type == 'added':
                section = self._generate_api_doc_section(change)
                new_sections.append(section)

        if new_sections:
            # Add new sections to the documentation
            api_docs = "\n\n".join(new_sections)
            
            # Try to find an appropriate place to insert
            if "## API Reference" in content:
                content = content.replace("## API Reference", f"## API Reference\n\n{api_docs}")
            elif "# API" in content:
                content = content.replace("# API", f"# API\n\n{api_docs}")
            else:
                # Add at the end
                content += f"\n\n## New APIs\n\n{api_docs}"

        return content

    def _generate_api_doc_section(self, change: APIChange) -> str:
        """Generate documentation section for an API change."""
        if change.api_type == 'function':
            return f"""### {change.name}

```python
{change.new_signature}
```

{change.description}
"""
        elif change.api_type == 'class':
            return f"""### {change.name}

```python
class {change.new_signature}
```

{change.description}
"""
        elif change.api_type == 'endpoint':
            return f"""### {change.name}

**Endpoint**: `{change.name}`

{change.description}
"""
        else:
            return f"### {change.name}\n\n{change.description}\n"

    def _update_openapi_spec(
        self, spec_data: dict[str, Any], api_changes: list[APIChange]
    ) -> dict[str, Any]:
        """Update OpenAPI specification with new endpoints."""
        updated_spec = spec_data.copy()

        for change in api_changes:
            if change.api_type == 'endpoint' and change.change_type == 'added':
                # Parse endpoint information
                method, path = self._parse_endpoint_name(change.name)
                
                if method and path:
                    # Add to paths
                    paths = updated_spec.setdefault('paths', {})
                    path_obj = paths.setdefault(path, {})
                    
                    path_obj[method.lower()] = {
                        'summary': change.description,
                        'description': change.description,
                        'responses': {
                            '200': {
                                'description': 'Successful response'
                            }
                        }
                    }

        return updated_spec

    def _parse_endpoint_name(self, endpoint_name: str) -> tuple[str | None, str | None]:
        """Parse endpoint name into method and path."""
        try:
            parts = endpoint_name.split(' ', 1)
            if len(parts) == 2:
                return parts[0], parts[1]
        except Exception:
            pass
        
        return None, None

    def _create_migration_guide(self, breaking_changes: list[APIChange]) -> str:
        """Create a migration guide for breaking changes."""
        guide_parts = [
            "# Migration Guide",
            "",
            "This guide helps you migrate your code to work with the latest API changes.",
            "",
        ]

        for change in breaking_changes:
            guide_parts.extend([
                f"## {change.name}",
                "",
                f"**Change Type**: {change.change_type}",
                f"**Description**: {change.description}",
                "",
            ])

            if change.old_signature and change.new_signature:
                guide_parts.extend([
                    "**Before**:",
                    f"```python",
                    change.old_signature,
                    "```",
                    "",
                    "**After**:",
                    f"```python",
                    change.new_signature,
                    "```",
                    "",
                ])

        return "\n".join(guide_parts)