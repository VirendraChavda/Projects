/**
 * WebSocket Client for Research Agent
 * Handles real-time communication with backend
 */

class WebSocketClient {
    constructor() {
        this.wsProtocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
        this.wsBase = `${this.wsProtocol}//${window.location.host}/ws`;
        this.connections = {};
        this.handlers = {};
        this.reconnectAttempts = {};
        this.maxReconnectAttempts = 5;
        this.reconnectDelay = 3000;
    }

    /**
     * Connect to a WebSocket endpoint
     * @param {string} endpoint - The WebSocket endpoint (e.g., 'ingest', 'analysis')
     * @param {Object} handlers - Object with message handlers {onMessage, onError, onOpen, onClose}
     */
    connect(endpoint, handlers = {}) {
        try {
            const url = `${this.wsBase}/${endpoint}/`;
            const ws = new WebSocket(url);

            ws.onopen = () => {
                console.log(`WebSocket connected: ${endpoint}`);
                this.reconnectAttempts[endpoint] = 0;
                if (handlers.onOpen) handlers.onOpen();
            };

            ws.onmessage = (event) => {
                try {
                    const data = JSON.parse(event.data);
                    if (handlers.onMessage) handlers.onMessage(data);
                } catch (e) {
                    console.error('WebSocket message parse error:', e);
                    if (handlers.onError) handlers.onError(e);
                }
            };

            ws.onerror = (error) => {
                console.error(`WebSocket error on ${endpoint}:`, error);
                if (handlers.onError) handlers.onError(error);
            };

            ws.onclose = () => {
                console.log(`WebSocket closed: ${endpoint}`);
                if (handlers.onClose) handlers.onClose();
                this.attemptReconnect(endpoint, handlers);
            };

            this.connections[endpoint] = ws;
            this.handlers[endpoint] = handlers;

        } catch (error) {
            console.error(`Failed to connect to ${endpoint}:`, error);
            if (handlers.onError) handlers.onError(error);
        }
    }

    /**
     * Send a message through WebSocket
     * @param {string} endpoint - The endpoint to send to
     * @param {Object} data - Data to send
     */
    send(endpoint, data) {
        const ws = this.connections[endpoint];
        if (!ws || ws.readyState !== WebSocket.OPEN) {
            console.warn(`WebSocket not ready for ${endpoint}`);
            return false;
        }

        try {
            ws.send(JSON.stringify(data));
            return true;
        } catch (error) {
            console.error(`Failed to send message on ${endpoint}:`, error);
            return false;
        }
    }

    /**
     * Close WebSocket connection
     * @param {string} endpoint - The endpoint to close
     */
    close(endpoint) {
        const ws = this.connections[endpoint];
        if (ws) {
            ws.close();
            delete this.connections[endpoint];
            delete this.handlers[endpoint];
        }
    }

    /**
     * Close all connections
     */
    closeAll() {
        Object.keys(this.connections).forEach(endpoint => {
            this.close(endpoint);
        });
    }

    /**
     * Attempt to reconnect with exponential backoff
     */
    attemptReconnect(endpoint, handlers) {
        const attempts = this.reconnectAttempts[endpoint] || 0;

        if (attempts >= this.maxReconnectAttempts) {
            console.log(`Max reconnection attempts reached for ${endpoint}`);
            return;
        }

        const delay = this.reconnectDelay * Math.pow(2, attempts);
        console.log(`Attempting to reconnect to ${endpoint} in ${delay}ms...`);

        this.reconnectAttempts[endpoint] = attempts + 1;
        setTimeout(() => {
            this.connect(endpoint, handlers);
        }, delay);
    }

    /**
     * Check if WebSocket is connected
     */
    isConnected(endpoint) {
        const ws = this.connections[endpoint];
        return ws && ws.readyState === WebSocket.OPEN;
    }
}

// Global WebSocket client instance
const wsClient = new WebSocketClient();
