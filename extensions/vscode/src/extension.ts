import * as vscode from 'vscode';
import { DevAgentClient } from './devAgentClient';
import { DevAgentPanel } from './devAgentPanel';
import { SuggestionProvider } from './suggestionProvider';
import { FileEventHandler } from './fileEventHandler';

let devAgentClient: DevAgentClient;
let devAgentPanel: DevAgentPanel;
let suggestionProvider: SuggestionProvider;
let fileEventHandler: FileEventHandler;

export function activate(context: vscode.ExtensionContext) {
    console.log('Dev-Agent extension is now active');

    // Initialize components
    devAgentClient = new DevAgentClient();
    devAgentPanel = new DevAgentPanel(context.extensionUri);
    suggestionProvider = new SuggestionProvider(devAgentClient);
    fileEventHandler = new FileEventHandler(devAgentClient);

    // Connect to dev-agent server
    devAgentClient.connect();

    // Register commands
    registerCommands(context);

    // Register providers
    registerProviders(context);

    // Setup file event handling
    setupFileEventHandling(context);

    // Show welcome message if first time
    showWelcomeMessage(context);
}

export function deactivate() {
    if (devAgentClient) {
        devAgentClient.disconnect();
    }
}

function registerCommands(context: vscode.ExtensionContext) {
    // Analyze Project command
    const analyzeProjectCommand = vscode.commands.registerCommand(
        'dev-agent.analyzeProject',
        async () => {
            const workspaceFolder = vscode.workspace.workspaceFolders?.[0];
            if (!workspaceFolder) {
                vscode.window.showErrorMessage('No workspace folder found');
                return;
            }

            try {
                vscode.window.showInformationMessage('Starting project analysis...');
                
                const result = await devAgentClient.sendCommand('analyze_project', {
                    project_path: workspaceFolder.uri.fsPath
                });

                if (result.success) {
                    vscode.window.showInformationMessage('Project analysis completed successfully');
                    devAgentPanel.updateAnalysisResults(result);
                } else {
                    vscode.window.showErrorMessage(`Analysis failed: ${result.error}`);
                }
            } catch (error) {
                vscode.window.showErrorMessage(`Analysis error: ${error}`);
            }
        }
    );

    // Generate Specification command
    const generateSpecCommand = vscode.commands.registerCommand(
        'dev-agent.generateSpecification',
        async () => {
            try {
                vscode.window.showInformationMessage('Generating specification...');
                
                const result = await devAgentClient.sendCommand('generate_specification', {});
                
                if (result.success) {
                    vscode.window.showInformationMessage('Specification generated successfully');
                    // Open the generated specification file
                    const specPath = vscode.workspace.workspaceFolders?.[0]?.uri.fsPath + '/.dev_agent/documents/specification.md';
                    const specUri = vscode.Uri.file(specPath);
                    vscode.window.showTextDocument(specUri);
                } else {
                    vscode.window.showErrorMessage(`Specification generation failed: ${result.error}`);
                }
            } catch (error) {
                vscode.window.showErrorMessage(`Specification error: ${error}`);
            }
        }
    );

    // Generate Design command
    const generateDesignCommand = vscode.commands.registerCommand(
        'dev-agent.generateDesign',
        async () => {
            try {
                vscode.window.showInformationMessage('Generating design document...');
                
                const result = await devAgentClient.sendCommand('generate_design', {});
                
                if (result.success) {
                    vscode.window.showInformationMessage('Design document generated successfully');
                    // Open the generated design file
                    const designPath = vscode.workspace.workspaceFolders?.[0]?.uri.fsPath + '/.dev_agent/documents/design.md';
                    const designUri = vscode.Uri.file(designPath);
                    vscode.window.showTextDocument(designUri);
                } else {
                    vscode.window.showErrorMessage(`Design generation failed: ${result.error}`);
                }
            } catch (error) {
                vscode.window.showErrorMessage(`Design error: ${error}`);
            }
        }
    );

    // Generate Tasks command
    const generateTasksCommand = vscode.commands.registerCommand(
        'dev-agent.generateTasks',
        async () => {
            try {
                vscode.window.showInformationMessage('Generating implementation tasks...');
                
                const result = await devAgentClient.sendCommand('generate_tasks', {});
                
                if (result.success) {
                    vscode.window.showInformationMessage('Implementation tasks generated successfully');
                    // Open the generated tasks file
                    const tasksPath = vscode.workspace.workspaceFolders?.[0]?.uri.fsPath + '/.dev_agent/documents/tasks.md';
                    const tasksUri = vscode.Uri.file(tasksPath);
                    vscode.window.showTextDocument(tasksUri);
                } else {
                    vscode.window.showErrorMessage(`Task generation failed: ${result.error}`);
                }
            } catch (error) {
                vscode.window.showErrorMessage(`Task error: ${error}`);
            }
        }
    );

    // Suggest Improvements command
    const suggestImprovementsCommand = vscode.commands.registerCommand(
        'dev-agent.suggestImprovements',
        async () => {
            const editor = vscode.window.activeTextEditor;
            if (!editor) {
                vscode.window.showErrorMessage('No active editor found');
                return;
            }

            try {
                const document = editor.document;
                const selection = editor.selection;
                
                const context = {
                    file_path: document.uri.fsPath,
                    language: document.languageId,
                    content: document.getText(selection.isEmpty ? undefined : selection),
                    cursor_position: {
                        line: selection.active.line,
                        character: selection.active.character
                    },
                    selection: selection.isEmpty ? null : {
                        start: { line: selection.start.line, character: selection.start.character },
                        end: { line: selection.end.line, character: selection.end.character }
                    }
                };

                const result = await devAgentClient.sendCommand('suggest_improvements', context);
                
                if (result.success && result.suggestions) {
                    suggestionProvider.showSuggestions(result.suggestions, editor);
                } else {
                    vscode.window.showInformationMessage('No suggestions available for this code');
                }
            } catch (error) {
                vscode.window.showErrorMessage(`Suggestion error: ${error}`);
            }
        }
    );

    // Open Panel command
    const openPanelCommand = vscode.commands.registerCommand(
        'dev-agent.openPanel',
        () => {
            devAgentPanel.show();
        }
    );

    // Start Workflow command
    const startWorkflowCommand = vscode.commands.registerCommand(
        'dev-agent.startWorkflow',
        async () => {
            const workspaceFolder = vscode.workspace.workspaceFolders?.[0];
            if (!workspaceFolder) {
                vscode.window.showErrorMessage('No workspace folder found');
                return;
            }

            try {
                // Start the dev-agent workflow in terminal
                const terminal = vscode.window.createTerminal('Dev-Agent');
                terminal.sendText(`cd "${workspaceFolder.uri.fsPath}"`);
                terminal.sendText('dev-agent init');
                terminal.show();
            } catch (error) {
                vscode.window.showErrorMessage(`Workflow start error: ${error}`);
            }
        }
    );

    // Resume Workflow command
    const resumeWorkflowCommand = vscode.commands.registerCommand(
        'dev-agent.resumeWorkflow',
        async () => {
            const workspaceFolder = vscode.workspace.workspaceFolders?.[0];
            if (!workspaceFolder) {
                vscode.window.showErrorMessage('No workspace folder found');
                return;
            }

            try {
                // Resume the dev-agent workflow in terminal
                const terminal = vscode.window.createTerminal('Dev-Agent');
                terminal.sendText(`cd "${workspaceFolder.uri.fsPath}"`);
                terminal.sendText('dev-agent resume');
                terminal.show();
            } catch (error) {
                vscode.window.showErrorMessage(`Workflow resume error: ${error}`);
            }
        }
    );

    // Register all commands
    context.subscriptions.push(
        analyzeProjectCommand,
        generateSpecCommand,
        generateDesignCommand,
        generateTasksCommand,
        suggestImprovementsCommand,
        openPanelCommand,
        startWorkflowCommand,
        resumeWorkflowCommand
    );
}

function registerProviders(context: vscode.ExtensionContext) {
    // Register completion provider for inline suggestions
    const completionProvider = vscode.languages.registerCompletionItemProvider(
        { scheme: 'file', language: 'python' },
        suggestionProvider,
        '.'  // Trigger on dot
    );

    // Register code action provider for improvements
    const codeActionProvider = vscode.languages.registerCodeActionsProvider(
        { scheme: 'file', language: 'python' },
        suggestionProvider
    );

    context.subscriptions.push(completionProvider, codeActionProvider);
}

function setupFileEventHandling(context: vscode.ExtensionContext) {
    // File opened event
    const onDidOpenTextDocument = vscode.workspace.onDidOpenTextDocument(
        (document) => fileEventHandler.handleFileOpened(document)
    );

    // File saved event
    const onDidSaveTextDocument = vscode.workspace.onDidSaveTextDocument(
        (document) => fileEventHandler.handleFileSaved(document)
    );

    // File changed event
    const onDidChangeTextDocument = vscode.workspace.onDidChangeTextDocument(
        (event) => fileEventHandler.handleFileChanged(event)
    );

    // Selection changed event
    const onDidChangeTextEditorSelection = vscode.window.onDidChangeTextEditorSelection(
        (event) => fileEventHandler.handleSelectionChanged(event)
    );

    context.subscriptions.push(
        onDidOpenTextDocument,
        onDidSaveTextDocument,
        onDidChangeTextDocument,
        onDidChangeTextEditorSelection
    );
}

function showWelcomeMessage(context: vscode.ExtensionContext) {
    const hasShownWelcome = context.globalState.get('dev-agent.hasShownWelcome', false);
    
    if (!hasShownWelcome) {
        vscode.window.showInformationMessage(
            'Welcome to Dev-Agent! Start by analyzing your project.',
            'Analyze Project',
            'Open Panel'
        ).then(selection => {
            if (selection === 'Analyze Project') {
                vscode.commands.executeCommand('dev-agent.analyzeProject');
            } else if (selection === 'Open Panel') {
                vscode.commands.executeCommand('dev-agent.openPanel');
            }
        });
        
        context.globalState.update('dev-agent.hasShownWelcome', true);
    }
}