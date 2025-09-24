"""Sample dev-agent plugin implementation."""

from __future__ import annotations

from pathlib import Path
from typing import Any, Dict, List

from dev_agent.plugins.ide_plugin import BaseIDEPlugin
from dev_agent.plugins.models import (
    CodeContext,
    Command,
    CommandType,
    FileEvent,
    IDEType,
    PluginConfig,
    Suggestion,
)


def create_plugin(config: PluginConfig) -> SampleDevAgentPlugin:
    """Create and return the plugin instance.
    
    This function is called by the plugin loader to instantiate the plugin.
    
    Args:
        config: Plugin configuration
        
    Returns:
        Plugin instance
    """
    return SampleDevAgentPlugin(config)


class SampleDevAgentPlugin(BaseIDEPlugin):
    """Sample plugin that demonstrates dev-agent plugin capabilities."""
    
    def __init__(self, plugin_config: PluginConfig) -> None:
        """Initialize the sample plugin.
        
        Args:
            plugin_config: Plugin configuration
        """
        super().__init__(IDEType.VSCODE, plugin_config)
        self.suggestion_count = 0
        self.files_analyzed = set()
    
    def register_commands(self) -> List[Command]:
        """Register commands provided by this plugin.
        
        Returns:
            List of commands
        """
        return [
            Command(
                id="sample_analyze_code",
                title="Sample: Analyze Code Quality",
                description="Analyze code quality using sample metrics",
                command_type=CommandType.ANALYSIS,
                handler="handle_analyze_code",
            ),
            Command(
                id="sample_generate_docstring",
                title="Sample: Generate Docstring",
                description="Generate a sample docstring for the current function",
                command_type=CommandType.GENERATION,
                handler="handle_generate_docstring",
            ),
            Command(
                id="sample_refactor_suggestion",
                title="Sample: Suggest Refactoring",
                description="Provide sample refactoring suggestions",
                command_type=CommandType.ANALYSIS,
                handler="handle_refactor_suggestion",
            ),
        ]
    
    def handle_file_events(self, event: FileEvent) -> None:
        """Handle file events from the IDE.
        
        Args:
            event: File event to handle
        """
        if not self.is_active:
            return
        
        # Track analyzed files
        if event.event_type in ["file_opened", "file_saved"]:
            self.files_analyzed.add(str(event.file_path))
        
        # Provide real-time feedback for Python files
        if event.file_path.suffix == ".py":
            if event.event_type == "file_saved":
                self._analyze_python_file(event.file_path, event.content or "")
    
    def provide_inline_suggestions(self, context: CodeContext) -> List[Suggestion]:
        """Provide inline code suggestions.
        
        Args:
            context: Code context for suggestions
            
        Returns:
            List of suggestions
        """
        suggestions = []
        
        if context.language != "python":
            return suggestions
        
        # Sample suggestion: Add type hints
        if "def " in context.content and "->" not in context.content:
            self.suggestion_count += 1
            suggestions.append(Suggestion(
                id=f"sample_type_hint_{self.suggestion_count}",
                title="Add Type Hints",
                description="Consider adding type hints to improve code clarity and IDE support",
                code=self._generate_type_hint_suggestion(context.content),
                range={"start": 0, "end": len(context.content)},
                confidence=0.8,
                category="quality",
                priority=2,
            ))
        
        # Sample suggestion: Add docstring
        if "def " in context.content and '"""' not in context.content:
            self.suggestion_count += 1
            suggestions.append(Suggestion(
                id=f"sample_docstring_{self.suggestion_count}",
                title="Add Docstring",
                description="Add a docstring to document this function",
                code=self._generate_docstring_suggestion(context.content),
                range={"start": 0, "end": len(context.content)},
                confidence=0.9,
                category="documentation",
                priority=1,
            ))
        
        # Sample suggestion: Use pathlib
        if "import os" in context.content and "os.path" in context.content:
            self.suggestion_count += 1
            suggestions.append(Suggestion(
                id=f"sample_pathlib_{self.suggestion_count}",
                title="Use pathlib Instead of os.path",
                description="Consider using pathlib for more modern and readable path operations",
                code=self._generate_pathlib_suggestion(context.content),
                range={"start": 0, "end": len(context.content)},
                confidence=0.7,
                category="modernization",
                priority=3,
            ))
        
        return suggestions
    
    def handle_analyze_code(self, **kwargs: Any) -> Dict[str, Any]:
        """Handle code analysis command.
        
        Returns:
            Analysis results
        """
        file_path = kwargs.get("file_path")
        content = kwargs.get("content", "")
        
        if not file_path:
            return {"success": False, "error": "No file path provided"}
        
        try:
            analysis = self._perform_code_analysis(content)
            
            return {
                "success": True,
                "analysis": analysis,
                "message": f"Code analysis completed for {file_path}",
            }
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    def handle_generate_docstring(self, **kwargs: Any) -> Dict[str, Any]:
        """Handle docstring generation command.
        
        Returns:
            Generated docstring
        """
        content = kwargs.get("content", "")
        
        try:
            docstring = self._generate_function_docstring(content)
            
            return {
                "success": True,
                "docstring": docstring,
                "message": "Docstring generated successfully",
            }
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    def handle_refactor_suggestion(self, **kwargs: Any) -> Dict[str, Any]:
        """Handle refactoring suggestion command.
        
        Returns:
            Refactoring suggestions
        """
        content = kwargs.get("content", "")
        
        try:
            suggestions = self._generate_refactoring_suggestions(content)
            
            return {
                "success": True,
                "suggestions": suggestions,
                "message": f"Found {len(suggestions)} refactoring opportunities",
            }
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    def _analyze_python_file(self, file_path: Path, content: str) -> None:
        """Analyze a Python file for quality metrics.
        
        Args:
            file_path: Path to the file
            content: File content
        """
        # Simple analysis - count lines, functions, classes
        lines = content.split("\n")
        function_count = sum(1 for line in lines if line.strip().startswith("def "))
        class_count = sum(1 for line in lines if line.strip().startswith("class "))
        
        print(f"Analyzed {file_path}: {len(lines)} lines, {function_count} functions, {class_count} classes")
    
    def _generate_type_hint_suggestion(self, content: str) -> str:
        """Generate a type hint suggestion.
        
        Args:
            content: Code content
            
        Returns:
            Suggested code with type hints
        """
        # Simple example - add basic type hints
        lines = content.split("\n")
        for i, line in enumerate(lines):
            if line.strip().startswith("def ") and "->" not in line:
                if "(" in line and ")" in line:
                    # Add return type annotation
                    lines[i] = line.replace("):", ") -> Any:")
        
        return "\n".join(lines)
    
    def _generate_docstring_suggestion(self, content: str) -> str:
        """Generate a docstring suggestion.
        
        Args:
            content: Code content
            
        Returns:
            Suggested code with docstring
        """
        lines = content.split("\n")
        for i, line in enumerate(lines):
            if line.strip().startswith("def "):
                # Insert docstring after function definition
                indent = len(line) - len(line.lstrip())
                docstring = f'{" " * (indent + 4)}"""Add function description here."""'
                lines.insert(i + 1, docstring)
                break
        
        return "\n".join(lines)
    
    def _generate_pathlib_suggestion(self, content: str) -> str:
        """Generate a pathlib usage suggestion.
        
        Args:
            content: Code content
            
        Returns:
            Suggested code using pathlib
        """
        # Simple replacement example
        suggested = content.replace("import os", "from pathlib import Path")
        suggested = suggested.replace("os.path.join(", "Path(")
        suggested = suggested.replace("os.path.exists(", "Path(").replace(").exists(", ").exists()")
        
        return suggested
    
    def _perform_code_analysis(self, content: str) -> Dict[str, Any]:
        """Perform code analysis and return metrics.
        
        Args:
            content: Code content to analyze
            
        Returns:
            Analysis results
        """
        lines = content.split("\n")
        
        return {
            "line_count": len(lines),
            "function_count": sum(1 for line in lines if line.strip().startswith("def ")),
            "class_count": sum(1 for line in lines if line.strip().startswith("class ")),
            "import_count": sum(1 for line in lines if line.strip().startswith("import ") or line.strip().startswith("from ")),
            "comment_count": sum(1 for line in lines if line.strip().startswith("#")),
            "docstring_count": content.count('"""') // 2,
            "complexity_score": min(10, len(lines) // 10),  # Simple complexity metric
        }
    
    def _generate_function_docstring(self, content: str) -> str:
        """Generate a docstring for a function.
        
        Args:
            content: Function code
            
        Returns:
            Generated docstring
        """
        # Extract function name and parameters
        lines = content.split("\n")
        func_line = next((line for line in lines if line.strip().startswith("def ")), "")
        
        if not func_line:
            return '"""Add function description here."""'
        
        # Simple docstring template
        return f'"""Add description for this function.\n    \n    Returns:\n        Add return description here.\n    """'
    
    def _generate_refactoring_suggestions(self, content: str) -> List[Dict[str, Any]]:
        """Generate refactoring suggestions.
        
        Args:
            content: Code content
            
        Returns:
            List of refactoring suggestions
        """
        suggestions = []
        lines = content.split("\n")
        
        # Check for long functions
        in_function = False
        function_lines = 0
        for line in lines:
            if line.strip().startswith("def "):
                in_function = True
                function_lines = 0
            elif in_function and (line.strip().startswith("def ") or line.strip().startswith("class ")):
                in_function = False
            elif in_function:
                function_lines += 1
        
        if function_lines > 20:
            suggestions.append({
                "type": "function_length",
                "message": "Consider breaking down long functions into smaller ones",
                "severity": "medium",
            })
        
        # Check for missing type hints
        if "def " in content and "->" not in content:
            suggestions.append({
                "type": "type_hints",
                "message": "Add type hints to improve code clarity",
                "severity": "low",
            })
        
        # Check for old-style string formatting
        if "%" in content and "format" not in content:
            suggestions.append({
                "type": "string_formatting",
                "message": "Consider using f-strings or .format() for string formatting",
                "severity": "low",
            })
        
        return suggestions