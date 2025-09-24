import * as vscode from 'vscode';

export class DevAgentPanel {
    public static currentPanel: DevAgentPanel | undefined;
    private readonly _panel: vscode.WebviewPanel;
    private _disposables: vscode.Disposable[] = [];

    public static createOrShow(extensionUri: vscode.Uri) {
        const column = vscode.window.activeTextEditor
            ? vscode.window.activeTextEditor.viewColumn
            : undefined;

        if (DevAgentPanel.currentPanel) {
            DevAgentPanel.currentPanel._panel.reveal(column);
            return;
        }

        const panel = vscode.window.createWebviewPanel(
            'devAgentPanel',
            'Dev-Agent',
            column || vscode.ViewColumn.One,
            {
                enableScripts: true,
                localResourceRoots: [
                    vscode.Uri.joinPath(extensionUri, 'media'),
                    vscode.Uri.joinPath(extensionUri, 'out')
                ]
            }
        );

        DevAgentPanel.currentPanel = new DevAgentPanel(panel, extensionUri);
    }

    constructor(panel: vscode.WebviewPanel, private readonly _extensionUri: vscode.Uri) {
        this._panel = panel;
        this._update();
        this._panel.onDidDispose(() => this.dispose(), null, this._disposables);
    }

    public show(): void {
        DevAgentPanel.createOrShow(this._extensionUri);
    }

    public updateAnalysisResults(results: any): void {
        this._panel.webview.postMessage({
            type: 'analysisResults',
            data: results
        });
    }

    public updateWorkflowStatus(status: any): void {
        this._panel.webview.postMessage({
            type: 'workflowStatus',
            data: status
        });
    }

    public dispose(): void {
        DevAgentPanel.currentPanel = undefined;
        this._panel.dispose();

        while (this._disposables.length) {
            const disposable = this._disposables.pop();
            if (disposable) {
                disposable.dispose();
            }
        }
    }

    private _update(): void {
        const webview = this._panel.webview;
        this._panel.title = 'Dev-Agent';
        this._panel.webview.html = this._getHtmlForWebview(webview);

        // Handle messages from the webview
        this._panel.webview.onDidReceiveMessage(
            message => {
                switch (message.type) {
                    case 'analyzeProject':
                        vscode.commands.executeCommand('dev-agent.analyzeProject');
                        break;
                    case 'generateSpec':
                        vscode.commands.executeCommand('dev-agent.generateSpecification');
                        break;
                    case 'generateDesign':
                        vscode.commands.executeCommand('dev-agent.generateDesign');
                        break;
                    case 'generateTasks':
                        vscode.commands.executeCommand('dev-agent.generateTasks');
                        break;
                    case 'startWorkflow':
                        vscode.commands.executeCommand('dev-agent.startWorkflow');
                        break;
                    case 'resumeWorkflow':
                        vscode.commands.executeCommand('dev-agent.resumeWorkflow');
                        break;
                }
            },
            null,
            this._disposables
        );
    }

    private _getHtmlForWebview(webview: vscode.Webview): string {
        // Get the local path to main script run in the webview
        const scriptPathOnDisk = vscode.Uri.joinPath(this._extensionUri, 'media', 'main.js');
        const scriptUri = webview.asWebviewUri(scriptPathOnDisk);

        // Get the local path to css file
        const stylePathOnDisk = vscode.Uri.joinPath(this._extensionUri, 'media', 'main.css');
        const styleUri = webview.asWebviewUri(stylePathOnDisk);

        // Use a nonce to only allow specific scripts to be run
        const nonce = getNonce();

        return `<!DOCTYPE html>
            <html lang="en">
            <head>
                <meta charset="UTF-8">
                <meta http-equiv="Content-Security-Policy" content="default-src 'none'; style-src ${webview.cspSource}; script-src 'nonce-${nonce}';">
                <meta name="viewport" content="width=device-width, initial-scale=1.0">
                <link href="${styleUri}" rel="stylesheet">
                <title>Dev-Agent</title>
            </head>
            <body>
                <div class="container">
                    <header>
                        <h1>🤖 Dev-Agent</h1>
                        <p>AI-powered development workflow assistant</p>
                    </header>

                    <section class="workflow-section">
                        <h2>Workflow Actions</h2>
                        <div class="button-grid">
                            <button class="action-button primary" onclick="analyzeProject()">
                                📊 Analyze Project
                            </button>
                            <button class="action-button" onclick="generateSpec()">
                                📝 Generate Specification
                            </button>
                            <button class="action-button" onclick="generateDesign()">
                                🎨 Generate Design
                            </button>
                            <button class="action-button" onclick="generateTasks()">
                                ✅ Generate Tasks
                            </button>
                        </div>
                    </section>

                    <section class="workflow-section">
                        <h2>Workflow Management</h2>
                        <div class="button-grid">
                            <button class="action-button secondary" onclick="startWorkflow()">
                                🚀 Start New Workflow
                            </button>
                            <button class="action-button secondary" onclick="resumeWorkflow()">
                                ▶️ Resume Workflow
                            </button>
                        </div>
                    </section>

                    <section class="status-section">
                        <h2>Status</h2>
                        <div id="status-content">
                            <p>Ready to start development workflow...</p>
                        </div>
                    </section>

                    <section class="results-section">
                        <h2>Analysis Results</h2>
                        <div id="results-content">
                            <p>No analysis results yet. Run project analysis to see results here.</p>
                        </div>
                    </section>
                </div>

                <script nonce="${nonce}" src="${scriptUri}"></script>
            </body>
            </html>`;
    }
}

function getNonce(): string {
    let text = '';
    const possible = 'ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789';
    for (let i = 0; i < 32; i++) {
        text += possible.charAt(Math.floor(Math.random() * possible.length));
    }
    return text;
}