(function() {
    const vscode = acquireVsCodeApi();

    // Button click handlers
    window.analyzeProject = function() {
        vscode.postMessage({ type: 'analyzeProject' });
        showLoading('Analyzing project...');
    };

    window.generateSpec = function() {
        vscode.postMessage({ type: 'generateSpec' });
        showLoading('Generating specification...');
    };

    window.generateDesign = function() {
        vscode.postMessage({ type: 'generateDesign' });
        showLoading('Generating design document...');
    };

    window.generateTasks = function() {
        vscode.postMessage({ type: 'generateTasks' });
        showLoading('Generating implementation tasks...');
    };

    window.startWorkflow = function() {
        vscode.postMessage({ type: 'startWorkflow' });
        showStatus('Starting new workflow...');
    };

    window.resumeWorkflow = function() {
        vscode.postMessage({ type: 'resumeWorkflow' });
        showStatus('Resuming workflow...');
    };

    // Listen for messages from the extension
    window.addEventListener('message', event => {
        const message = event.data;
        
        switch (message.type) {
            case 'analysisResults':
                displayAnalysisResults(message.data);
                break;
            case 'workflowStatus':
                displayWorkflowStatus(message.data);
                break;
            case 'error':
                showError(message.message);
                break;
            case 'success':
                showSuccess(message.message);
                break;
        }
    });

    function showLoading(message) {
        const statusContent = document.getElementById('status-content');
        statusContent.innerHTML = `
            <div class="status-item">
                <span class="status-label">${message}</span>
                <span class="loading"></span>
            </div>
        `;
    }

    function showStatus(message) {
        const statusContent = document.getElementById('status-content');
        statusContent.innerHTML = `
            <div class="status-item">
                <span class="status-label">${message}</span>
                <span class="status-value">In Progress</span>
            </div>
        `;
    }

    function showError(message) {
        const statusContent = document.getElementById('status-content');
        statusContent.innerHTML = `
            <div class="error-message">
                <strong>Error:</strong> ${message}
            </div>
        `;
    }

    function showSuccess(message) {
        const statusContent = document.getElementById('status-content');
        statusContent.innerHTML = `
            <div class="success-message">
                <strong>Success:</strong> ${message}
            </div>
        `;
    }

    function displayAnalysisResults(results) {
        const resultsContent = document.getElementById('results-content');
        
        if (!results || !results.success) {
            resultsContent.innerHTML = `
                <div class="error-message">
                    Analysis failed: ${results?.error || 'Unknown error'}
                </div>
            `;
            return;
        }

        let html = '<div class="result-item">';
        html += '<div class="result-title">✅ Project Analysis Complete</div>';
        html += '<div class="result-description">Analysis completed successfully</div>';
        html += '</div>';

        if (results.result) {
            const result = results.result;
            
            if (result.file_count) {
                html += `
                    <div class="result-item">
                        <div class="result-title">📁 Files Analyzed</div>
                        <div class="result-description">${result.file_count} files processed</div>
                    </div>
                `;
            }

            if (result.languages) {
                html += `
                    <div class="result-item">
                        <div class="result-title">🔤 Languages Detected</div>
                        <div class="result-description">${result.languages.join(', ')}</div>
                    </div>
                `;
            }

            if (result.frameworks) {
                html += `
                    <div class="result-item">
                        <div class="result-title">🛠️ Frameworks Found</div>
                        <div class="result-description">${result.frameworks.join(', ')}</div>
                    </div>
                `;
            }

            if (result.complexity_score) {
                html += `
                    <div class="result-item">
                        <div class="result-title">📊 Complexity Score</div>
                        <div class="result-description">${result.complexity_score}/10</div>
                    </div>
                `;
            }
        }

        resultsContent.innerHTML = html;
        showSuccess('Analysis completed successfully');
    }

    function displayWorkflowStatus(status) {
        const statusContent = document.getElementById('status-content');
        
        let html = '';
        
        if (status.current_phase) {
            html += `
                <div class="status-item">
                    <span class="status-label">Current Phase</span>
                    <span class="status-value">${status.current_phase}</span>
                </div>
            `;
        }

        if (status.progress !== undefined) {
            html += `
                <div class="status-item">
                    <span class="status-label">Progress</span>
                    <span class="status-value">${status.progress}%</span>
                </div>
                <div class="progress-bar">
                    <div class="progress-fill" style="width: ${status.progress}%"></div>
                </div>
            `;
        }

        if (status.next_action) {
            html += `
                <div class="status-item">
                    <span class="status-label">Next Action</span>
                    <span class="status-value">${status.next_action}</span>
                </div>
            `;
        }

        if (status.estimated_time) {
            html += `
                <div class="status-item">
                    <span class="status-label">Estimated Time</span>
                    <span class="status-value">${status.estimated_time}</span>
                </div>
            `;
        }

        statusContent.innerHTML = html || '<p>No workflow status available</p>';
    }

    // Initialize the panel
    function initialize() {
        showStatus('Ready to start development workflow');
        
        // Add keyboard shortcuts info
        const statusContent = document.getElementById('status-content');
        statusContent.innerHTML += `
            <div style="margin-top: 15px; padding-top: 15px; border-top: 1px solid var(--vscode-panel-border);">
                <small style="color: var(--vscode-descriptionForeground);">
                    <strong>Keyboard Shortcuts:</strong><br>
                    Ctrl+Shift+A: Analyze Project<br>
                    Ctrl+Shift+S: Generate Specification<br>
                    Ctrl+Shift+D: Generate Design<br>
                    Ctrl+Shift+T: Generate Tasks
                </small>
            </div>
        `;
    }

    // Initialize when the page loads
    initialize();
})();