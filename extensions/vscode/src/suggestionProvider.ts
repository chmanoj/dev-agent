import * as vscode from 'vscode';
import { DevAgentClient } from './devAgentClient';

export class SuggestionProvider implements vscode.CompletionItemProvider, vscode.CodeActionProvider {
    constructor(private client: DevAgentClient) {}

    // CompletionItemProvider implementation
    public async provideCompletionItems(
        document: vscode.TextDocument,
        position: vscode.Position,
        token: vscode.CancellationToken,
        context: vscode.CompletionContext
    ): Promise<vscode.CompletionItem[]> {
        if (!this.client.isServerConnected()) {
            return [];
        }

        try {
            const config = vscode.workspace.getConfiguration('dev-agent');
            const suggestionLevel = config.get<string>('suggestionLevel', 'moderate');
            
            if (suggestionLevel === 'minimal') {
                return [];
            }

            const codeContext = this.buildCodeContext(document, position);
            const result = await this.client.sendCommand('get_suggestions', codeContext);

            if (result.success && result.suggestions) {
                return this.convertToCompletionItems(result.suggestions);
            }
        } catch (error) {
            console.error('Error getting completion suggestions:', error);
        }

        return [];
    }

    // CodeActionProvider implementation
    public async provideCodeActions(
        document: vscode.TextDocument,
        range: vscode.Range | vscode.Selection,
        context: vscode.CodeActionContext,
        token: vscode.CancellationToken
    ): Promise<vscode.CodeAction[]> {
        if (!this.client.isServerConnected()) {
            return [];
        }

        try {
            const codeContext = this.buildCodeContext(document, range.start, range);
            const result = await this.client.sendCommand('suggest_improvements', codeContext);

            if (result.success && result.suggestions) {
                return this.convertToCodeActions(result.suggestions, document, range);
            }
        } catch (error) {
            console.error('Error getting code actions:', error);
        }

        return [];
    }

    public async showSuggestions(suggestions: any[], editor: vscode.TextEditor): Promise<void> {
        if (!suggestions || suggestions.length === 0) {
            vscode.window.showInformationMessage('No suggestions available');
            return;
        }

        // Show suggestions in a quick pick
        const items = suggestions.map(suggestion => ({
            label: suggestion.title,
            description: suggestion.description,
            detail: `Confidence: ${(suggestion.confidence * 100).toFixed(0)}% | Category: ${suggestion.category}`,
            suggestion: suggestion
        }));

        const selected = await vscode.window.showQuickPick(items, {
            placeHolder: 'Select a suggestion to apply',
            matchOnDescription: true,
            matchOnDetail: true
        });

        if (selected) {
            await this.applySuggestion(selected.suggestion, editor);
        }
    }

    private buildCodeContext(
        document: vscode.TextDocument,
        position: vscode.Position,
        range?: vscode.Range
    ): any {
        const lineText = document.lineAt(position.line).text;
        const wordRange = document.getWordRangeAtPosition(position);
        const word = wordRange ? document.getText(wordRange) : '';

        // Get surrounding context (5 lines before and after)
        const startLine = Math.max(0, position.line - 5);
        const endLine = Math.min(document.lineCount - 1, position.line + 5);
        const surroundingRange = new vscode.Range(startLine, 0, endLine, document.lineAt(endLine).text.length);
        const surroundingCode = document.getText(surroundingRange);

        return {
            file_path: document.uri.fsPath,
            language: document.languageId,
            content: range ? document.getText(range) : lineText,
            cursor_position: {
                line: position.line,
                character: position.character
            },
            selection: range ? {
                start: { line: range.start.line, character: range.start.character },
                end: { line: range.end.line, character: range.end.character }
            } : null,
            surrounding_code: surroundingCode,
            current_word: word,
            project_context: {
                workspace_path: vscode.workspace.workspaceFolders?.[0]?.uri.fsPath
            }
        };
    }

    private convertToCompletionItems(suggestions: any[]): vscode.CompletionItem[] {
        return suggestions
            .filter(s => s.category === 'completion' || s.category === 'pattern')
            .map(suggestion => {
                const item = new vscode.CompletionItem(
                    suggestion.title,
                    vscode.CompletionItemKind.Snippet
                );

                item.detail = suggestion.description;
                item.documentation = new vscode.MarkdownString(suggestion.code);
                item.insertText = new vscode.SnippetString(suggestion.code);
                item.sortText = `${1000 - Math.floor(suggestion.confidence * 1000)}`;
                
                // Add confidence indicator
                if (suggestion.confidence > 0.8) {
                    item.label += ' ⭐';
                } else if (suggestion.confidence > 0.6) {
                    item.label += ' ✓';
                }

                return item;
            });
    }

    private convertToCodeActions(
        suggestions: any[],
        document: vscode.TextDocument,
        range: vscode.Range
    ): vscode.CodeAction[] {
        return suggestions
            .filter(s => s.category === 'quality' || s.category === 'refactor')
            .map(suggestion => {
                const action = new vscode.CodeAction(
                    suggestion.title,
                    vscode.CodeActionKind.Refactor
                );

                action.detail = suggestion.description;
                action.isPreferred = suggestion.confidence > 0.8;

                // Create edit for the suggestion
                const edit = new vscode.WorkspaceEdit();
                const suggestionRange = this.getSuggestionRange(suggestion, document, range);
                edit.replace(document.uri, suggestionRange, suggestion.code);
                action.edit = edit;

                return action;
            });
    }

    private getSuggestionRange(
        suggestion: any,
        document: vscode.TextDocument,
        defaultRange: vscode.Range
    ): vscode.Range {
        if (suggestion.range) {
            const start = new vscode.Position(suggestion.range.start.line || 0, suggestion.range.start.character || 0);
            const end = new vscode.Position(suggestion.range.end.line || 0, suggestion.range.end.character || 0);
            return new vscode.Range(start, end);
        }
        return defaultRange;
    }

    private async applySuggestion(suggestion: any, editor: vscode.TextEditor): Promise<void> {
        const document = editor.document;
        const selection = editor.selection;

        try {
            await editor.edit(editBuilder => {
                const range = this.getSuggestionRange(suggestion, document, selection);
                editBuilder.replace(range, suggestion.code);
            });

            vscode.window.showInformationMessage(`Applied suggestion: ${suggestion.title}`);
        } catch (error) {
            vscode.window.showErrorMessage(`Failed to apply suggestion: ${error}`);
        }
    }
}