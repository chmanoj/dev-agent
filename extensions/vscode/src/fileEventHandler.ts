import * as vscode from 'vscode';
import { DevAgentClient } from './devAgentClient';

export class FileEventHandler {
    private debounceTimers = new Map<string, NodeJS.Timeout>();
    private readonly debounceDelay = 500; // 500ms debounce

    constructor(private client: DevAgentClient) {}

    public handleFileOpened(document: vscode.TextDocument): void {
        if (!this.shouldHandleFile(document)) {
            return;
        }

        const event = {
            event_type: 'file_opened',
            file_path: document.uri.fsPath,
            content: document.getText(),
            timestamp: Date.now()
        };

        this.client.sendEvent('file_event', event);
    }

    public handleFileSaved(document: vscode.TextDocument): void {
        if (!this.shouldHandleFile(document)) {
            return;
        }

        const event = {
            event_type: 'file_saved',
            file_path: document.uri.fsPath,
            content: document.getText(),
            timestamp: Date.now()
        };

        this.client.sendEvent('file_event', event);

        // Trigger analysis for Python files
        if (document.languageId === 'python') {
            this.triggerFileAnalysis(document);
        }
    }

    public handleFileChanged(changeEvent: vscode.TextDocumentChangeEvent): void {
        const document = changeEvent.document;
        
        if (!this.shouldHandleFile(document)) {
            return;
        }

        // Debounce file change events to avoid spam
        const filePath = document.uri.fsPath;
        
        if (this.debounceTimers.has(filePath)) {
            clearTimeout(this.debounceTimers.get(filePath)!);
        }

        const timer = setTimeout(() => {
            const event = {
                event_type: 'file_changed',
                file_path: document.uri.fsPath,
                content: document.getText(),
                changes: changeEvent.contentChanges.map(change => ({
                    range: {
                        start: { line: change.range.start.line, character: change.range.start.character },
                        end: { line: change.range.end.line, character: change.range.end.character }
                    },
                    text: change.text
                })),
                timestamp: Date.now()
            };

            this.client.sendEvent('file_event', event);
            this.debounceTimers.delete(filePath);
        }, this.debounceDelay);

        this.debounceTimers.set(filePath, timer);
    }

    public handleSelectionChanged(event: vscode.TextEditorSelectionChangeEvent): void {
        const document = event.textEditor.document;
        
        if (!this.shouldHandleFile(document)) {
            return;
        }

        // Only send selection events for significant selections
        const selection = event.selections[0];
        if (selection.isEmpty) {
            return;
        }

        const selectionEvent = {
            event_type: 'selection_changed',
            file_path: document.uri.fsPath,
            selection: {
                start: { line: selection.start.line, character: selection.start.character },
                end: { line: selection.end.line, character: selection.end.character }
            },
            cursor_position: {
                line: selection.active.line,
                character: selection.active.character
            },
            timestamp: Date.now()
        };

        this.client.sendEvent('file_event', selectionEvent);
    }

    private shouldHandleFile(document: vscode.TextDocument): boolean {
        // Only handle files in the workspace
        if (document.uri.scheme !== 'file') {
            return false;
        }

        // Check if file is in workspace
        const workspaceFolder = vscode.workspace.getWorkspaceFolder(document.uri);
        if (!workspaceFolder) {
            return false;
        }

        // Skip certain file types
        const skipExtensions = ['.log', '.tmp', '.cache', '.git'];
        const fileName = document.uri.fsPath;
        
        if (skipExtensions.some(ext => fileName.includes(ext))) {
            return false;
        }

        // Skip very large files (> 1MB)
        if (document.getText().length > 1024 * 1024) {
            return false;
        }

        return true;
    }

    private async triggerFileAnalysis(document: vscode.TextDocument): Promise<void> {
        try {
            // Only analyze if dev-agent auto-analyze is enabled
            const config = vscode.workspace.getConfiguration('dev-agent');
            const autoAnalyze = config.get<boolean>('autoAnalyze', false);
            
            if (!autoAnalyze) {
                return;
            }

            // Send analysis request
            await this.client.sendCommand('analyze_file', {
                file_path: document.uri.fsPath,
                content: document.getText(),
                language: document.languageId
            });

        } catch (error) {
            console.error('Error triggering file analysis:', error);
        }
    }

    public dispose(): void {
        // Clear all debounce timers
        for (const timer of this.debounceTimers.values()) {
            clearTimeout(timer);
        }
        this.debounceTimers.clear();
    }
}