document.addEventListener('DOMContentLoaded', () => {
    // UI Elements
    const generateBtn = document.getElementById('generate-btn');
    const promptInput = document.getElementById('prompt-input');
    const logsContainer = document.getElementById('logs-container');
    const statusIndicator = document.querySelector('.status-indicator');
    const tabs = document.querySelectorAll('.tab');
    const panels = document.querySelectorAll('.panel');
    const previewIframe = document.getElementById('preview-iframe');
    const refreshPreviewBtn = document.getElementById('refresh-preview');
    const fileSelector = document.getElementById('file-selector');

    // State
    let isGenerating = false;
    let ws = null;
    let editor = null;
    let currentCode = {
        html: '',
        css: '',
        js: ''
    };

    // Initialize Monaco Editor
    require.config({ paths: { 'vs': 'https://cdnjs.cloudflare.com/ajax/libs/monaco-editor/0.38.0/min/vs' }});
    require(['vs/editor/editor.main'], function() {
        editor = monaco.editor.create(document.getElementById('editor-container'), {
            value: '',
            language: 'html',
            theme: 'vs-dark',
            automaticLayout: true,
            minimap: { enabled: false },
            fontSize: 14,
            padding: { top: 16 }
        });
    });

    // Event Listeners
    tabs.forEach(tab => {
        tab.addEventListener('click', () => {
            tabs.forEach(t => t.classList.remove('active'));
            panels.forEach(p => p.classList.remove('active'));
            
            tab.classList.add('active');
            document.getElementById(`${tab.dataset.target}-panel`).classList.add('active');
        });
    });

    fileSelector.addEventListener('change', (e) => {
        const type = e.target.value;
        const langMap = { 'html': 'html', 'css': 'css', 'js': 'javascript' };
        
        if (editor) {
            monaco.editor.setModelLanguage(editor.getModel(), langMap[type]);
            editor.setValue(currentCode[type] || '');
        }
    });

    refreshPreviewBtn.addEventListener('click', () => {
        previewIframe.src = previewIframe.src; // Reload
    });

    generateBtn.addEventListener('click', () => {
        const prompt = promptInput.value.trim();
        if (!prompt || isGenerating) return;

        startGeneration(prompt);
    });

    // Deployment Logic
    const deployBtn = document.getElementById('deploy-btn');
    const deployModal = document.getElementById('deploy-modal');
    const closeModalBtn = document.getElementById('close-modal-btn');
    const cancelDeployBtn = document.getElementById('cancel-deploy-btn');
    const confirmDeployBtn = document.getElementById('confirm-deploy-btn');
    const repoNameInput = document.getElementById('repo-name');
    const deployStatus = document.getElementById('deploy-status');
    const deployStatusText = deployStatus.querySelector('.status-text');

    function openDeployModal() {
        deployModal.classList.remove('hidden');
        repoNameInput.value = `ai-generated-app-${Math.floor(Math.random() * 10000)}`;
        deployStatus.classList.add('hidden');
        deployStatus.className = 'deploy-status hidden';
        confirmDeployBtn.disabled = false;
        cancelDeployBtn.disabled = false;
        closeModalBtn.disabled = false;
    }

    function closeDeployModal() {
        deployModal.classList.add('hidden');
    }

    deployBtn.addEventListener('click', openDeployModal);
    closeModalBtn.addEventListener('click', closeDeployModal);
    cancelDeployBtn.addEventListener('click', closeDeployModal);

    confirmDeployBtn.addEventListener('click', async () => {
        const repoName = repoNameInput.value.trim();
        if (!repoName) return;

        confirmDeployBtn.disabled = true;
        cancelDeployBtn.disabled = true;
        closeModalBtn.disabled = true;
        
        deployStatus.classList.remove('hidden');
        deployStatus.className = 'deploy-status';
        deployStatusText.textContent = 'Creating repository and pushing code...';

        try {
            const response = await fetch('/api/deploy', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ repo_name: repoName })
            });
            const data = await response.json();

            if (data.error) {
                deployStatus.className = 'deploy-status error';
                deployStatusText.textContent = data.error;
                confirmDeployBtn.disabled = false;
                cancelDeployBtn.disabled = false;
                closeModalBtn.disabled = false;
            } else {
                deployStatus.className = 'deploy-status success';
                deployStatusText.innerHTML = `Successfully deployed! <br>Repo: <a href="${data.repo_url}" target="_blank">View on GitHub</a><br>Pages: <a href="${data.url}" target="_blank">View Live Site</a> (Pages may take 1-2 mins to propagate)`;
                cancelDeployBtn.disabled = false;
                cancelDeployBtn.textContent = 'Close';
            }
        } catch (error) {
            deployStatus.className = 'deploy-status error';
            deployStatusText.textContent = 'Network error or server unreachable.';
            confirmDeployBtn.disabled = false;
            cancelDeployBtn.disabled = false;
            closeModalBtn.disabled = false;
        }
    });

    // Core Logic
    function startGeneration(prompt) {
        isGenerating = true;
        generateBtn.disabled = true;
        generateBtn.innerHTML = `<span>Generating...</span><svg class="spinner" viewBox="0 0 50 50" width="16" height="16"><circle class="path" cx="25" cy="25" r="20" fill="none" stroke-width="5"></circle></svg>`;
        statusIndicator.classList.add('busy');
        
        // Clear previous logs
        logsContainer.innerHTML = '';
        appendLog('System', 'Connecting to orchestrator...');

        // Connect WebSocket
        const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
        // Use relative path or explicit localhost depending on setup
        const wsUrl = `${protocol}//${window.location.host}/ws`;
        
        // Fallback for direct file opening (if not served by backend, which shouldn't happen here)
        ws = new WebSocket(wsUrl.includes('null') ? 'ws://localhost:8000/ws' : wsUrl);

        ws.onopen = () => {
            appendLog('System', 'Connected. Sending prompt to Agent A (Ideator).');
            ws.send(JSON.stringify({ type: 'generate', prompt: prompt, currentCode: currentCode }));
        };

        ws.onmessage = (event) => {
            const data = JSON.parse(event.data);
            
            if (data.type === 'log') {
                appendLog(data.agent, data.text, data.details);
            } else if (data.type === 'code_update') {
                currentCode.html = data.html || '';
                currentCode.css = data.css || '';
                currentCode.js = data.js || '';
                
                if (editor) {
                    const type = fileSelector.value;
                    editor.setValue(currentCode[type] || '');
                }
            } else if (data.type === 'preview_reload') {
                // cache buster to force reload
                previewIframe.src = `/preview/index.html?t=${Date.now()}`;
            } else if (data.type === 'done') {
                finishGeneration();
                appendLog('System', 'Generation complete.');
            } else if (data.type === 'error') {
                finishGeneration();
                appendLog('System', `Error: ${data.message}`);
            }
        };

        ws.onerror = (err) => {
            appendLog('System', 'WebSocket Error. Make sure backend is running.');
            finishGeneration();
        };
        
        ws.onclose = () => {
            if(isGenerating) finishGeneration();
        };
    }

    function finishGeneration() {
        isGenerating = false;
        generateBtn.disabled = false;
        generateBtn.innerHTML = `<span>Generate</span><svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M5 12h14M12 5l7 7-7 7"/></svg>`;
        statusIndicator.classList.remove('busy');
    }

    function appendLog(agent, text, details = null) {
        const entry = document.createElement('div');
        entry.className = `log-entry ${agent.toLowerCase()}-log`;
        
        let detailsHtml = '';
        if (details) {
            // format json nicely if it's an object
            let detailsStr = typeof details === 'string' ? details : JSON.stringify(details, null, 2);
            // truncate if too long
            if (detailsStr.length > 500) detailsStr = detailsStr.substring(0, 500) + '...';
            detailsHtml = `<pre style="font-size: 0.7rem; color: var(--text-muted); margin-top: 0.5rem; overflow-x: auto;">${detailsStr}</pre>`;
        }

        entry.innerHTML = `
            <strong>${agent}</strong>
            ${text}
            ${detailsHtml}
        `;
        logsContainer.appendChild(entry);
        logsContainer.scrollTop = logsContainer.scrollHeight;
    }

    // Add some spinner styles dynamically
    const style = document.createElement('style');
    style.innerHTML = `
        .spinner {
            animation: rotate 2s linear infinite;
        }
        .spinner .path {
            stroke: currentColor;
            stroke-linecap: round;
            animation: dash 1.5s ease-in-out infinite;
        }
        @keyframes rotate { 100% { transform: rotate(360deg); } }
        @keyframes dash {
            0% { stroke-dasharray: 1, 150; stroke-dashoffset: 0; }
            50% { stroke-dasharray: 90, 150; stroke-dashoffset: -35; }
            100% { stroke-dasharray: 90, 150; stroke-dashoffset: -124; }
        }
    `;
    document.head.appendChild(style);
});
