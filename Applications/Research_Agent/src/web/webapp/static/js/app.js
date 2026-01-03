/**
 * Research Agent Frontend - Main Application Logic
 */

class ResearchAgent {
    constructor() {
        this.apiBaseUrl = '/api';
        this.wsProtocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
        this.wsBase = `${this.wsProtocol}//${window.location.host}/ws`;
        this.settings = this.loadSettings();
        this.init();
    }

    init() {
        this.setupEventListeners();
        this.checkSystemStatus();
        this.loadDefaultSettings();
    }

    setupEventListeners() {
        // Tab navigation
        document.querySelectorAll('.nav-link').forEach(link => {
            link.addEventListener('click', (e) => {
                e.preventDefault();
                this.switchTab(link.dataset.tab);
            });
        });

        // Ingest Tab
        document.getElementById('start-ingest-btn').addEventListener('click', () => this.startIngestion());
        document.getElementById('cancel-ingest-btn').addEventListener('click', () => this.cancelIngestion());

        // Research Tab
        document.getElementById('execute-query-btn').addEventListener('click', () => this.executeQuery());
        document.getElementById('export-results-btn')?.addEventListener('click', () => this.exportResults());

        // Settings Tab
        document.getElementById('save-settings-btn').addEventListener('click', () => this.saveSettings());
        document.getElementById('clear-cache-btn').addEventListener('click', () => this.clearCache());

        // Keyboard shortcuts
        document.addEventListener('keydown', (e) => this.handleKeyboardShortcuts(e));
    }

    switchTab(tabName) {
        // Hide all tabs
        document.querySelectorAll('.tab-content').forEach(tab => {
            tab.classList.remove('active');
        });

        // Remove active from all nav links
        document.querySelectorAll('.nav-link').forEach(link => {
            link.classList.remove('active');
        });

        // Show selected tab
        document.getElementById(`${tabName}-tab`)?.classList.add('active');

        // Mark nav link as active
        document.querySelector(`[data-tab="${tabName}"]`)?.classList.add('active');
    }

    // Ingestion Methods
    async startIngestion() {
        const categories = document.getElementById('arxiv-categories').value || 'cs.LG';
        const maxResults = parseInt(document.getElementById('arxiv-max-results').value) || 100;
        const daysBack = parseInt(document.getElementById('arxiv-days').value) || 7;

        const payload = {
            source: 'arxiv',
            categories: categories.split(',').map(c => c.trim()),
            max_results: maxResults,
            days_back: daysBack
        };

        try {
            // Hide form, show progress
            document.querySelector('.card').style.display = 'none';
            document.getElementById('ingest-progress-container').style.display = 'block';
            document.getElementById('ingest-stats-container').style.display = 'block';
            document.getElementById('start-ingest-btn').style.display = 'none';
            document.getElementById('cancel-ingest-btn').style.display = 'inline-flex';

            // Start ingestion via API
            const response = await fetch(`${this.apiBaseUrl}/ingest/start/`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(payload)
            });

            if (!response.ok) throw new Error(`HTTP ${response.status}`);

            // Connect WebSocket for progress updates
            this.connectIngestionWebSocket();

            // Poll for status updates
            this.pollIngestionStatus();

        } catch (error) {
            this.showToast(`Ingestion failed: ${error.message}`, 'error');
            this.resetIngestionUI();
        }
    }

    connectIngestionWebSocket() {
        const ws = new WebSocket(`${this.wsBase}/ingest/`);

        ws.onmessage = (event) => {
            const data = JSON.parse(event.data);
            this.updateIngestionProgress(data);
        };

        ws.onerror = (error) => {
            console.error('WebSocket error:', error);
        };

        ws.onclose = () => {
            console.log('WebSocket closed');
        };

        this.ingestionWs = ws;
    }

    async pollIngestionStatus() {
        const pollInterval = setInterval(async () => {
            try {
                const response = await fetch(`${this.apiBaseUrl}/ingest/status/`);
                if (!response.ok) throw new Error(`HTTP ${response.status}`);

                const status = await response.json();
                this.updateIngestionStats(status);

                if (status.status === 'completed' || status.status === 'failed') {
                    clearInterval(pollInterval);
                    this.completeIngestion(status);
                }
            } catch (error) {
                console.error('Status poll error:', error);
                clearInterval(pollInterval);
            }
        }, 1000);

        this.ingestionPollInterval = pollInterval;
    }

    updateIngestionProgress(data) {
        const progress = data.progress || 0;
        document.getElementById('ingest-progress-fill').style.width = `${progress}%`;
        document.getElementById('ingest-status').textContent = data.status || 'Processing...';

        // Add log entry
        if (data.message) {
            const logsContainer = document.getElementById('ingest-logs');
            const logEntry = document.createElement('div');
            logEntry.className = `log-entry ${data.level || 'info'}`;
            logEntry.textContent = `[${new Date().toLocaleTimeString()}] ${data.message}`;
            logsContainer.appendChild(logEntry);
            logsContainer.scrollTop = logsContainer.scrollHeight;
        }
    }

    updateIngestionStats(status) {
        document.getElementById('stat-fetched').textContent = status.papers_fetched || 0;
        document.getElementById('stat-processed').textContent = status.papers_processed || 0;
        document.getElementById('stat-indexed').textContent = status.papers_indexed || 0;
        document.getElementById('stat-duplicates').textContent = status.duplicates || 0;
    }

    completeIngestion(status) {
        this.showToast(`Ingestion ${status.status}!`, status.status === 'completed' ? 'success' : 'error');
    }

    cancelIngestion() {
        if (this.ingestionWs) {
            this.ingestionWs.close();
        }
        if (this.ingestionPollInterval) {
            clearInterval(this.ingestionPollInterval);
        }
        this.resetIngestionUI();
        this.showToast('Ingestion cancelled', 'info');
    }

    resetIngestionUI() {
        document.querySelector('.card').style.display = 'block';
        document.getElementById('ingest-progress-container').style.display = 'none';
        document.getElementById('ingest-stats-container').style.display = 'none';
        document.getElementById('start-ingest-btn').style.display = 'inline-flex';
        document.getElementById('cancel-ingest-btn').style.display = 'none';
        document.getElementById('ingest-logs').innerHTML = '';
        document.getElementById('ingest-progress-fill').style.width = '0%';
    }

    // Research Methods
    async executeQuery() {
        const query = document.getElementById('query-input').value.trim();
        const analysisType = document.getElementById('analysis-type').value;
        const topK = parseInt(document.getElementById('top-k').value) || 10;

        if (!query) {
            this.showToast('Please enter a query', 'warning');
            return;
        }

        try {
            // Show loading state
            document.getElementById('execute-query-btn').disabled = true;

            const payload = {
                query,
                analysis_type: analysisType,
                top_k: topK
            };

            const response = await fetch(`${this.apiBaseUrl}/research/query/`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(payload)
            });

            if (!response.ok) throw new Error(`HTTP ${response.status}`);

            // Stream NDJSON response
            this.processQueryResponse(response);

        } catch (error) {
            this.showToast(`Query failed: ${error.message}`, 'error');
        } finally {
            document.getElementById('execute-query-btn').disabled = false;
        }
    }

    async processQueryResponse(response) {
        const reader = response.body.getReader();
        const decoder = new TextDecoder();
        let buffer = '';

        while (true) {
            const { done, value } = await reader.read();
            if (done) break;

            buffer += decoder.decode(value, { stream: true });
            const lines = buffer.split('\n');
            buffer = lines.pop();

            for (const line of lines) {
                if (line.trim()) {
                    try {
                        const data = JSON.parse(line);
                        this.processQueryResult(data);
                    } catch (e) {
                        console.error('Parse error:', e);
                    }
                }
            }
        }

        document.getElementById('query-results-container').style.display = 'block';
        this.showToast('Query completed', 'success');
    }

    processQueryResult(data) {
        if (data.type === 'papers') {
            this.displayRetrievedPapers(data.papers);
        } else if (data.type === 'analysis') {
            this.displayAnalysis(data.analysis);
        }
    }

    displayRetrievedPapers(papers) {
        const container = document.getElementById('retrieved-papers');
        container.innerHTML = '';

        papers.forEach(paper => {
            const paperEl = document.createElement('div');
            paperEl.className = 'paper-item';
            paperEl.innerHTML = `
                <div class="paper-title">${this.escapeHtml(paper.title)}</div>
                <div class="paper-authors">${this.escapeHtml(paper.authors)}</div>
                <div class="paper-meta">
                    ${paper.arxiv_id} • ${paper.published_date}
                </div>
                <span class="paper-score">Score: ${(paper.score * 100).toFixed(1)}%</span>
            `;
            container.appendChild(paperEl);
        });
    }

    displayAnalysis(analysis) {
        const container = document.getElementById('analysis-output');
        container.innerHTML = this.formatAnalysisText(analysis);
    }

    formatAnalysisText(text) {
        // Basic formatting of analysis text
        return text
            .split('\n')
            .map(line => {
                if (line.startsWith('#')) {
                    const level = line.match(/^#+/)[0].length;
                    const content = line.replace(/^#+\s/, '');
                    return `<h${level}>${this.escapeHtml(content)}</h${level}>`;
                } else if (line.startsWith('-') || line.startsWith('•')) {
                    return `<li>${this.escapeHtml(line.replace(/^[-•]\s/, ''))}</li>`;
                } else if (line.trim()) {
                    return `<p>${this.escapeHtml(line)}</p>`;
                }
                return '';
            })
            .join('');
    }

    exportResults() {
        const timestamp = new Date().toISOString().slice(0, 10);
        const data = {
            query: document.getElementById('query-input').value,
            analysisType: document.getElementById('analysis-type').value,
            results: document.getElementById('query-results-container').innerText,
            timestamp
        };

        const json = JSON.stringify(data, null, 2);
        const blob = new Blob([json], { type: 'application/json' });
        const url = URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = `research-results-${timestamp}.json`;
        document.body.appendChild(a);
        a.click();
        document.body.removeChild(a);
        URL.revokeObjectURL(url);

        this.showToast('Results exported', 'success');
    }

    // Settings Methods
    loadSettings() {
        return JSON.parse(localStorage.getItem('settings')) || {};
    }

    saveSettings() {
        this.settings = {
            llmProvider: document.getElementById('llm-provider').value,
            rerankerStrategy: document.getElementById('rerank-strategy').value,
            topK: parseInt(document.getElementById('rerank-top-k').value),
            enableCache: document.getElementById('enable-cache').checked
        };

        localStorage.setItem('settings', JSON.stringify(this.settings));
        this.showToast('Settings saved', 'success');
    }

    loadDefaultSettings() {
        if (this.settings.llmProvider) {
            document.getElementById('llm-provider').value = this.settings.llmProvider;
        }
        if (this.settings.rerankerStrategy) {
            document.getElementById('rerank-strategy').value = this.settings.rerankerStrategy;
        }
        if (this.settings.topK) {
            document.getElementById('rerank-top-k').value = this.settings.topK;
        }
        document.getElementById('enable-cache').checked = this.settings.enableCache !== false;
    }

    async clearCache() {
        try {
            const response = await fetch(`${this.apiBaseUrl}/cache/clear/`, { method: 'POST' });
            if (response.ok) {
                this.showToast('Cache cleared', 'success');
            }
        } catch (error) {
            this.showToast(`Cache clear failed: ${error.message}`, 'error');
        }
    }

    // System Status
    async checkSystemStatus() {
        try {
            const response = await fetch(`${this.apiBaseUrl}/health/`);
            const status = await response.json();
            this.updateSystemStatus(status);
        } catch (error) {
            console.error('Status check failed:', error);
        }
    }

    updateSystemStatus(status) {
        const statusElements = document.querySelectorAll('.status-indicator');
        const labels = ['Database', 'Vector Store', 'Cache', 'LLM API'];

        statusElements.forEach((el, index) => {
            const componentStatus = status[labels[index].toLowerCase().replace(' ', '_')];
            el.className = `status-indicator ${componentStatus ? 'success' : 'error'}`;
        });
    }

    // Utility Methods
    handleKeyboardShortcuts(e) {
        if (e.ctrlKey || e.metaKey) {
            if (e.key === 'Enter') {
                e.preventDefault();
                document.getElementById('execute-query-btn').click();
            } else if (e.key === 'k') {
                e.preventDefault();
                document.getElementById('query-input').focus();
            } else if (e.key === 's') {
                e.preventDefault();
                document.getElementById('save-settings-btn').click();
            }
        }
    }

    showToast(message, type = 'info') {
        const container = document.getElementById('toast-container');
        const toast = document.createElement('div');
        toast.className = `toast ${type}`;
        toast.innerHTML = `
            <span>${this.escapeHtml(message)}</span>
        `;
        container.appendChild(toast);

        setTimeout(() => {
            toast.style.opacity = '0';
            setTimeout(() => toast.remove(), 300);
        }, 3000);
    }

    escapeHtml(text) {
        const div = document.createElement('div');
        div.textContent = text;
        return div.innerHTML;
    }
}

// Initialize app when DOM is ready
document.addEventListener('DOMContentLoaded', () => {
    window.app = new ResearchAgent();
});
