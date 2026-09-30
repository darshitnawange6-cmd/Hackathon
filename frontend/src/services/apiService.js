// Configurable API base URL: defaults to '/api' for local dev and reverse-proxy setups,
// or points to external backend if VITE_API_URL is specified in production (e.g. on Vercel).
export const API_BASE = import.meta.env.VITE_API_URL
  ? `${import.meta.env.VITE_API_URL.replace(/\/+$/, '')}/api`
  : '/api';

export const apiService = {
  async sendMessage(message, sessionId = 'default-student-session', isVoice = false) {
    const res = await fetch(`${API_BASE}/chat`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        message,
        session_id: sessionId,
        is_voice: isVoice,
      }),
    });
    if (!res.ok) {
      const err = await res.json().catch(() => ({}));
      throw new Error(err.detail || `Server error: ${res.status}`);
    }
    return res.json();
  },

  async sendMessageStream(message, sessionId = 'default-student-session', isVoice = false, { onMetadata, onDelta, onDone, onError } = {}) {
    const res = await fetch(`${API_BASE}/chat/stream`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        message,
        session_id: sessionId,
        is_voice: isVoice,
      }),
    });

    if (!res.ok) {
      const err = await res.json().catch(() => ({}));
      throw new Error(err.detail || `Server error: ${res.status}`);
    }

    if (!res.body) {
      throw new Error('ReadableStream not supported by this browser.');
    }

    const reader = res.body.getReader();
    const decoder = new TextDecoder('utf-8');
    let buffer = '';

    while (true) {
      const { done, value } = await reader.read();
      if (done) break;
      buffer += decoder.decode(value, { stream: true });
      const blocks = buffer.split('\n\n');
      buffer = blocks.pop(); // keep partial

      for (const block of blocks) {
        for (const line of block.split('\n')) {
          if (line.startsWith('data: ')) {
            try {
              const data = JSON.parse(line.slice(6));
              if (data.type === 'metadata' && onMetadata) {
                onMetadata(data);
              } else if (data.type === 'delta' && onDelta) {
                onDelta(data.delta);
              } else if (data.type === 'done' && onDone) {
                onDone(data);
              } else if (data.type === 'error' && onError) {
                onError(data.error);
              }
            } catch (e) {
              console.warn('Failed to parse SSE line:', line, e);
            }
          }
        }
      }
    }
  },

  async getSession(sessionId = 'default-student-session') {
    const res = await fetch(`${API_BASE}/session/${sessionId}`);
    if (!res.ok) throw new Error('Failed to fetch session');
    return res.json();
  },

  async clearSession(sessionId = 'default-student-session') {
    const res = await fetch(`${API_BASE}/session/clear`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({ session_id: sessionId }),
    });
    if (!res.ok) throw new Error('Failed to clear session');
    return res.json();
  },

  async getHealth() {
    const res = await fetch(`${API_BASE}/health`);
    if (!res.ok) throw new Error('Health check failed');
    return res.json();
  },

  async getCampusOverview() {
    const res = await fetch(`${API_BASE}/campus/overview`);
    if (!res.ok) throw new Error('Failed to load campus overview');
    return res.json();
  },

  async getCampusData(category) {
    const res = await fetch(`${API_BASE}/campus/${category}`);
    if (!res.ok) throw new Error(`Failed to load ${category}`);
    return res.json();
  },

  // Document Management Methods
  async listDocuments() {
    const res = await fetch(`${API_BASE}/documents`);
    if (!res.ok) throw new Error('Failed to fetch documents');
    return res.json();
  },

  async uploadDocument(formData) {
    const res = await fetch(`${API_BASE}/documents/upload`, {
      method: 'POST',
      body: formData,
    });
    const data = await res.json();
    if (!res.ok) throw new Error(data.detail || 'Upload failed');
    return data;
  },

  async deleteDocument(docId) {
    const res = await fetch(`${API_BASE}/documents/${docId}`, {
      method: 'DELETE',
    });
    if (!res.ok) throw new Error('Delete failed');
    return res.json();
  },

  async syncDocuments() {
    const res = await fetch(`${API_BASE}/documents/sync`, {
      method: 'POST',
    });
    if (!res.ok) throw new Error('Sync failed');
    return res.json();
  },
};
