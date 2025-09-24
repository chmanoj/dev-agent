# Dev-Agent IDE Extensions

This directory contains IDE extensions and plugins for dev-agent, providing seamless integration with popular development environments.

## VS Code Extension

The VS Code extension provides comprehensive integration with dev-agent, including:

### Features

- **Project Analysis**: Analyze your codebase directly from VS Code
- **Workflow Integration**: Start and resume dev-agent workflows
- **Inline Suggestions**: Get AI-powered code suggestions as you type
- **Command Palette**: Access all dev-agent features via VS Code commands
- **Side Panel**: Dedicated dev-agent panel for workflow management
- **File Event Handling**: Automatic analysis on file save and open
- **Real-time Communication**: WebSocket-based communication with dev-agent server

### Installation

1. **Build the Extension**:
   ```bash
   cd extensions/vscode
   npm install
   npm run compile
   ```

2. **Install in VS Code**:
   - Open VS Code
   - Go to Extensions view (Ctrl+Shift+X)
   - Click "..." menu and select "Install from VSIX..."
   - Select the generated .vsix file

3. **Configure Dev-Agent**:
   - Open VS Code settings (Ctrl+,)
   - Search for "dev-agent"
   - Configure the Python path and server port

### Usage

#### Commands

- **Ctrl+Shift+A**: Analyze Project
- **Ctrl+Shift+S**: Generate Specification
- **Ctrl+Shift+D**: Generate Design Document
- **Ctrl+Shift+T**: Generate Implementation Tasks

#### Command Palette

Open the command palette (Ctrl+Shift+P) and search for "Dev-Agent" to see all available commands:

- `Dev-Agent: Analyze Project`
- `Dev-Agent: Generate Specification`
- `Dev-Agent: Generate Design Document`
- `Dev-Agent: Generate Implementation Tasks`
- `Dev-Agent: Suggest Code Improvements`
- `Dev-Agent: Open Dev-Agent Panel`
- `Dev-Agent: Start Dev-Agent Workflow`
- `Dev-Agent: Resume Dev-Agent Workflow`

#### Side Panel

Click the Dev-Agent icon in the activity bar to open the side panel, which provides:

- Quick access to workflow actions
- Real-time status updates
- Analysis results display
- Progress tracking

### Configuration

The extension can be configured through VS Code settings:

```json
{
  "dev-agent.enabled": true,
  "dev-agent.autoAnalyze": false,
  "dev-agent.suggestionLevel": "moderate",
  "dev-agent.serverPort": 8765,
  "dev-agent.pythonPath": "python"
}
```

### Development

To develop the VS Code extension:

1. **Setup Development Environment**:
   ```bash
   cd extensions/vscode
   npm install
   ```

2. **Watch Mode**:
   ```bash
   npm run watch
   ```

3. **Debug**:
   - Open the extension folder in VS Code
   - Press F5 to launch Extension Development Host
   - Test your changes in the new VS Code window

## Plugin Architecture

Dev-agent supports a plugin architecture that allows third-party developers to create custom integrations and extensions.

### Plugin Structure

A dev-agent plugin consists of:

```
my-plugin/
├── plugin.json          # Plugin configuration
├── main.py             # Main plugin implementation
├── README.md           # Plugin documentation
└── requirements.txt    # Python dependencies (optional)
```

### Plugin Configuration (plugin.json)

```json
{
  "name": "my-plugin",
  "version": "1.0.0",
  "description": "My custom dev-agent plugin",
  "author": "Your Name",
  "ide_type": "vscode",
  "security_level": "sandboxed",
  "permissions": [
    "ide_integration",
    "workspace_access"
  ],
  "dependencies": [],
  "settings": {},
  "enabled": true
}
```

### Plugin Implementation (main.py)

```python
from dev_agent.plugins.ide_plugin import BaseIDEPlugin
from dev_agent.plugins.models import Command, FileEvent, CodeContext, Suggestion

def create_plugin(config):
    return MyPlugin(config)

class MyPlugin(BaseIDEPlugin):
    def register_commands(self):
        return [
            Command(
                id="my_command",
                title="My Custom Command",
                description="Does something useful",
                command_type="utility",
                handler="handle_my_command"
            )
        ]
    
    def handle_file_events(self, event):
        # Handle file events from IDE
        pass
    
    def provide_inline_suggestions(self, context):
        # Provide code suggestions
        return []
    
    def handle_my_command(self, **kwargs):
        return {"success": True, "message": "Command executed"}
```

### Security Model

Plugins operate under a security model with three levels:

1. **Trusted**: Full access to all APIs and system resources
2. **Sandboxed**: Limited access to safe operations only
3. **Restricted**: No permissions granted, read-only access

### Available Permissions

- `ide_integration`: Access to IDE APIs and commands
- `workspace_access`: Read/write access to workspace files
- `file_read`: Read access to file system
- `file_write`: Write access to file system
- `network_access`: Access to network resources
- `system_commands`: Execute system commands
- `ai_services`: Access to AI/ML services

### Plugin Installation

1. **Manual Installation**:
   ```python
   from dev_agent.plugins import PluginArchitecture
   
   arch = PluginArchitecture(config_dir)
   arch.install_plugin(plugin_path)
   ```

2. **CLI Installation** (future):
   ```bash
   dev-agent plugin install my-plugin
   dev-agent plugin enable my-plugin
   ```

### Example Plugins

See the `examples/sample_plugin/` directory for a complete example plugin that demonstrates:

- Command registration
- File event handling
- Inline suggestions
- Code analysis
- Docstring generation
- Refactoring suggestions

## Communication Protocol

The IDE extensions communicate with dev-agent through a WebSocket-based protocol:

### Message Types

1. **Commands**: Execute dev-agent functionality
   ```json
   {
     "type": "command",
     "id": "unique_id",
     "command_id": "analyze_project",
     "args": {"project_path": "/path/to/project"}
   }
   ```

2. **Events**: Notify dev-agent of IDE events
   ```json
   {
     "type": "event",
     "event_type": "file_saved",
     "data": {"file_path": "/path/to/file.py", "content": "..."}
   }
   ```

3. **Responses**: Results from command execution
   ```json
   {
     "type": "command_response",
     "id": "unique_id",
     "success": true,
     "result": {...}
   }
   ```

4. **Notifications**: Status updates and messages
   ```json
   {
     "type": "notification",
     "data": {"title": "Analysis Complete", "message": "...", "level": "info"}
   }
   ```

## Future Extensions

Planned extensions for other IDEs:

- **IntelliJ IDEA**: Java-based plugin for JetBrains IDEs
- **Vim/Neovim**: Lua/Vimscript plugin for terminal-based editing
- **Emacs**: Elisp package for Emacs integration
- **Sublime Text**: Python plugin for Sublime Text

## Contributing

To contribute to the IDE extensions:

1. Fork the repository
2. Create a feature branch
3. Implement your changes
4. Add tests for new functionality
5. Submit a pull request

### Development Guidelines

- Follow the existing code style and patterns
- Add comprehensive tests for new features
- Update documentation for any API changes
- Ensure security best practices for plugin development
- Test with multiple IDE versions when possible

## Troubleshooting

### Common Issues

1. **Connection Failed**: Ensure dev-agent server is running on the configured port
2. **Plugin Not Loading**: Check plugin.json syntax and security validation
3. **Commands Not Working**: Verify command registration and handler implementation
4. **Performance Issues**: Review plugin code for blocking operations

### Debug Mode

Enable debug logging in VS Code:

1. Open Developer Tools (Help > Toggle Developer Tools)
2. Check Console for error messages
3. Enable dev-agent debug logging in settings

### Support

For issues and questions:

- Check the documentation
- Search existing GitHub issues
- Create a new issue with detailed information
- Join the community discussions