/**
 * API Client for Research Agent
 * Provides methods for all backend API calls
 */

class APIClient {
    constructor(baseUrl = '/api') {
        this.baseUrl = baseUrl;
        this.timeout = 30000;
        this.defaultHeaders = {
            'Content-Type': 'application/json'
        };
    }

    /**
     * Make a fetch request with error handling and timeout
     */
    async request(method, endpoint, data = null, options = {}) {
        const url = `${this.baseUrl}${endpoint}`;
        const config = {
            method,
            headers: { ...this.defaultHeaders, ...options.headers },
            timeout: options.timeout || this.timeout,
        };

        if (data && (method === 'POST' || method === 'PUT' || method === 'PATCH')) {
            config.body = JSON.stringify(data);
        }

        try {
            const controller = new AbortController();
            const timeoutId = setTimeout(() => controller.abort(), config.timeout);

            const response = await fetch(url, {
                ...config,
                signal: controller.signal
            });

            clearTimeout(timeoutId);

            if (!response.ok) {
                throw new APIError(response.status, `HTTP ${response.status}`);
            }

            // Handle different response types
            const contentType = response.headers.get('content-type');
            if (contentType?.includes('application/json')) {
                return await response.json();
            } else if (contentType?.includes('text')) {
                return await response.text();
            } else {
                return response;
            }

        } catch (error) {
            if (error instanceof APIError) {
                throw error;
            }
            throw new APIError(0, error.message);
        }
    }

    /**
     * Stream NDJSON response
     */
    async streamNDJSON(endpoint, data = null, onData, onError, onComplete) {
        const url = `${this.baseUrl}${endpoint}`;

        try {
            const response = await fetch(url, {
                method: 'POST',
                headers: this.defaultHeaders,
                body: JSON.stringify(data)
            });

            if (!response.ok) {
                throw new APIError(response.status, `HTTP ${response.status}`);
            }

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
                            onData(data);
                        } catch (e) {
                            console.error('NDJSON parse error:', e);
                            if (onError) onError(e);
                        }
                    }
                }
            }

            if (onComplete) onComplete();

        } catch (error) {
            if (onError) onError(error);
            throw error;
        }
    }

    // ============ Health & Status ============

    async checkHealth() {
        return this.request('GET', '/health/');
    }

    // ============ Ingestion Endpoints ============

    async startIngestion(config) {
        return this.request('POST', '/ingest/start/', config);
    }

    async getIngestionStatus() {
        return this.request('GET', '/ingest/status/');
    }

    async cancelIngestion() {
        return this.request('POST', '/ingest/cancel/');
    }

    // ============ Research Endpoints ============

    async executeQuery(query, analysisType, topK = 10) {
        return this.streamNDJSON('/research/query/', {
            query,
            analysis_type: analysisType,
            top_k: topK
        });
    }

    async executeQueryStream(query, analysisType, topK, onData, onError, onComplete) {
        return this.streamNDJSON(
            '/research/query/',
            { query, analysis_type: analysisType, top_k: topK },
            onData,
            onError,
            onComplete
        );
    }

    async getResearchResults(queryId) {
        return this.request('GET', `/research/get/?query_id=${queryId}`);
    }

    // ============ Cache Endpoints ============

    async clearCache() {
        return this.request('POST', '/cache/clear/');
    }

    async getCacheStatus() {
        return this.request('GET', '/cache/status/');
    }

    // ============ Settings Endpoints ============

    async getSettings() {
        return this.request('GET', '/settings/');
    }

    async saveSettings(settings) {
        return this.request('POST', '/settings/', settings);
    }

    // ============ Papers Endpoints ============

    async getPaperById(arxivId) {
        return this.request('GET', `/papers/${arxivId}/`);
    }

    async searchPapers(query, limit = 20) {
        return this.request('GET', `/papers/search/?q=${encodeURIComponent(query)}&limit=${limit}`);
    }

    async getPaperStats() {
        return this.request('GET', '/papers/stats/');
    }

    // ============ Admin Endpoints ============

    async getSystemStats() {
        return this.request('GET', '/admin/stats/');
    }

    async getDatabaseStatus() {
        return this.request('GET', '/admin/database-status/');
    }

    async getVectorStoreStatus() {
        return this.request('GET', '/admin/vector-store-status/');
    }
}

/**
 * Custom error class for API errors
 */
class APIError extends Error {
    constructor(status, message) {
        super(message);
        this.name = 'APIError';
        this.status = status;
    }

    toString() {
        return `${this.name} [${this.status}]: ${this.message}`;
    }
}

// Create global API client instance
const apiClient = new APIClient('/api');
