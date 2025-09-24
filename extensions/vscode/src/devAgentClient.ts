import * as vscode from 'vscode';
import * as WebSocket from 'ws';

export interface CommandResult {
    success: boolean;
    result?: any;
    error?: string;
    suggestions?: any[];
}

export class DevAgentClient {
    private ws: WebSocket | null = null;
    private isConnected = false;
    private reconnectAttempts = 0;
    private maxReconnectAttempts = 5;
    private reconnectDelay = 1000;
    private pendingCommands = new Map<string, { resolve: Function; reject: Function }>();
    private commandId = 0;

    constructor() {
        this.setupConfiguration();
    }

    private setupConfiguration() {
        // Listen for configuration changes
        vscode.workspace.onDidChangeConfiguration(event => {
            if (event.affectsConfiguration('dev-agent')) {
                this.reconnect();
            }
        });
    }

    public async connect(): Promise<boolean> {
        const config = vscode.workspace.getConfiguration('dev-agent');
        const port = config.get<number>('serverPort', 8765);
        const enabled = config.get<boolean>('enabled', true);

        if (!enabled) {
            console.log('Dev-Agent extension is disabled');
            return false;
        }

        try {
            this.ws = new WebSocket(`ws://localhost:${port}`);

            this.ws.on('open', () => {
                console.log('Connected to dev-agent server');
                this.isConnected = true;
                this.reconnectAttempts = 0;
                vscode.window.showInformationMessage('Connected to Dev-Agent server');
            });

            this.ws.on('message', (data: WebSocket.Data) => {
                try {
                    const message = JSON.parse(data.toString());
                    this.handleMessage(message);
                } catch (error) {
                    console.error('Error parsing message from server:', error);
                }
            });

            this.ws.on('close', () => {
                console.log('Disconnected from dev-agent server');
                this.isConnected = false;
                this.scheduleReconnect();
            });

            this.ws.on('error', (error) => {
                console.error('WebSocket error:', error);
                this.isConnected = false;
                
                if (this.reconnectAttempts === 0) {
                    vscode.window.showWarningMessage(
                        'Could not connect to Dev-Agent server. Make sure dev-agent is running.',
                        'Retry'
                    ).then(selection => {
                        if (selection === 'Retry') {
                            this.connect();
                        }
                    });
                }
            });

            return true;
        } catch (error) {
            console.error('Failed to connect to dev-agent server:', error);
            return false;
        }
    }

    public disconnect(): void {
        if (this.ws) {
            this.ws.close();
            this.ws = null;
        }
        this.isConnected = false;
    }

    public async reconnect(): Promise<void> {
        this.disconnect();
        await new Promise(resolve => setTimeout(resolve, 500));
        await this.connect();
    }

    private scheduleReconnect(): void {
        if (this.reconnectAttempts >= this.maxReconnectAttempts) {
            console.log('Max reconnection attempts reached');
            return;
        }

        this.reconnectAttempts++;
        const delay = this.reconnectDelay * Math.pow(2, this.reconnectAttempts - 1);

        setTimeout(() => {
            console.log(`Attempting to reconnect (${this.reconnectAttempts}/${this.maxReconnectAttempts})`);
            this.connect();
        }, delay);
    }

    public async sendCommand(commandId: string, args: any = {}): Promise<CommandResult> {
        if (!this.isConnected || !this.ws) {
            throw new Error('Not connected to dev-agent server');
        }

        return new Promise((resolve, reject) => {
            const id = (++this.commandId).toString();
            
            const message = {
                type: 'command',
                id: id,
                command_id: commandId,
                args: args
            };

            this.pendingCommands.set(id, { resolve, reject });

            // Set timeout for command
            setTimeout(() => {
                if (this.pendingCommands.has(id)) {
                    this.pendingCommands.delete(id);
                    reject(new Error('Command timeout'));
                }
            }, 30000); // 30 second timeout

            this.ws!.send(JSON.stringify(message));
        });
    }

    public sendEvent(eventType: string, data: any): void {
        if (!this.isConnected || !this.ws) {
            return;
        }

        const message = {
            type: 'event',
            event_type: eventType,
            data: data
        };

        this.ws.send(JSON.stringify(message));
    }

    private handleMessage(message: any): void {
        switch (message.type) {
            case 'command_response':
                this.handleCommandResponse(message);
                break;
            case 'suggestion':
                this.handleSuggestion(message);
                break;
            case 'notification':
                this.handleNotification(message);
                break;
            case 'progress':
                this.handleProgress(message);
                break;
            default:
                console.log('Unknown message type:', message.type);
        }
    }

    private handleCommandResponse(message: any): void {
        const { id, success, result, error } = message;
        
        if (this.pendingCommands.has(id)) {
            const { resolve } = this.pendingCommands.get(id)!;
            this.pendingCommands.delete(id);
            
            resolve({
                success,
                result,
                error,
                suggestions: result?.suggestions
            });
        }
    }

    private handleSuggestion(message: any): void {
        // Handle real-time suggestions from server
        const suggestionData = message.data;
        
        // Could trigger inline suggestions in the editor
        console.log('Received suggestion:', suggestionData);
    }

    private handleNotification(message: any): void {
        const { title, message: msg, level } = message.data;
        
        switch (level) {
            case 'error':
                vscode.window.showErrorMessage(`${title}: ${msg}`);
                break;
            case 'warning':
                vscode.window.showWarningMessage(`${title}: ${msg}`);
                break;
            default:
                vscode.window.showInformationMessage(`${title}: ${msg}`);
        }
    }

    private handleProgress(message: any): void {
        const { task_id, progress, message: msg } = message.data;
        
        // Could show progress in status bar or notification
        vscode.window.setStatusBarMessage(`Dev-Agent: ${msg} (${progress}%)`, 2000);
    }

    public isServerConnected(): boolean {
        return this.isConnected;
    }
}