/**
 * frontend/src/services/websocket.js
 * 
 * Resilient WebSocket client with automatic reconnect and status events.
 */

class TrafficWebSocket {
  constructor() {
    this.ws = null;
    this.listeners = new Set();
    this.statusListeners = new Set();
    this.status = 'DISCONNECTED'; // 'CONNECTING', 'CONNECTED', 'DISCONNECTED'
    this.reconnectTimeout = null;
    this.pingInterval = null;
    this.reconnectAttempts = 0;
  }

  connect() {
    if (this.ws && (this.ws.readyState === WebSocket.OPEN || this.ws.readyState === WebSocket.CONNECTING)) {
      return;
    }

    this._setStatus('CONNECTING');
    const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
    // Use host from window.location in dev (proxied by Vite) or direct
    const wsUrl = `${protocol}//${window.location.host}/ws/traffic`;

    try {
      this.ws = new WebSocket(wsUrl);

      this.ws.onopen = () => {
        this.reconnectAttempts = 0;
        this._setStatus('CONNECTED');
        this._startHeartbeat();
      };

      this.ws.onmessage = (event) => {
        try {
          const data = JSON.parse(event.data);
          this.listeners.forEach((fn) => fn(data));
        } catch (e) {
          console.warn('[WS] Parse error:', e);
        }
      };

      this.ws.onclose = () => {
        this._stopHeartbeat();
        this._setStatus('DISCONNECTED');
        this._scheduleReconnect();
      };

      this.ws.onerror = () => {
        this._setStatus('DISCONNECTED');
      };
    } catch (err) {
      console.warn('[WS] Connection exception:', err);
      this._scheduleReconnect();
    }
  }

  disconnect() {
    this._stopHeartbeat();
    clearTimeout(this.reconnectTimeout);
    if (this.ws) {
      this.ws.close();
      this.ws = null;
    }
    this._setStatus('DISCONNECTED');
  }

  subscribe(listener) {
    this.listeners.add(listener);
    return () => this.listeners.delete(listener);
  }

  onStatusChange(listener) {
    this.statusListeners.add(listener);
    listener(this.status);
    return () => this.statusListeners.delete(listener);
  }

  _setStatus(status) {
    this.status = status;
    this.statusListeners.forEach((fn) => fn(status));
  }

  _scheduleReconnect() {
    clearTimeout(this.reconnectTimeout);
    const delay = Math.min(1000 * Math.pow(1.5, this.reconnectAttempts), 8000);
    this.reconnectAttempts++;
    this.reconnectTimeout = setTimeout(() => {
      this.connect();
    }, delay);
  }

  _startHeartbeat() {
    clearInterval(this.pingInterval);
    this.pingInterval = setInterval(() => {
      if (this.ws && this.ws.readyState === WebSocket.OPEN) {
        this.ws.send('ping');
      }
    }, 15000);
  }

  _stopHeartbeat() {
    clearInterval(this.pingInterval);
  }
}

export const trafficWS = new TrafficWebSocket();
