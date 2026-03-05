import axios from 'axios';

const API_BASE_URL = 'http://localhost:8000';

const api = axios.create({
    baseURL: API_BASE_URL,
    headers: {
        'Content-Type': 'application/json',
    },
});

// Portfolio APIs
export const uploadPortfolio = async (file) => {
    const formData = new FormData();
    formData.append('file', file);

    const response = await api.post('/upload', formData, {
        headers: { 'Content-Type': 'multipart/form-data' },
    });
    return response.data;
};

export const getPortfolio = async () => {
    const response = await api.get('/portfolio');
    return response.data;
};

export const getPortfolioSummary = async () => {
    const response = await api.get('/portfolio/summary');
    return response.data;
};

export const refreshPortfolio = async () => {
    const response = await api.post('/portfolio/refresh');
    return response.data;
};

// Chat APIs
export const sendMessage = async (message, sessionId = null) => {
    const response = await api.post('/chat', {
        message,
        session_id: sessionId,
    });
    return response.data;
};

/**
 * Stream a chat message via SSE, receiving real-time tool-call events.
 * @param {string} message - User's message
 * @param {string|null} sessionId - Current session ID
 * @param {function} onToolCall - Callback invoked with tool name string when a tool is used
 * @param {function} onComplete - Callback invoked with (response, toolsUsed, sessionId) when done
 * @param {function} onError - Callback invoked with error message on failure
 */
export const sendMessageStream = async (message, sessionId, onToolCall, onComplete, onError) => {
    try {
        const response = await fetch(`${API_BASE_URL}/chat/stream`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ message, session_id: sessionId }),
        });

        if (!response.ok) {
            throw new Error(`HTTP error: ${response.status}`);
        }

        const reader = response.body.getReader();
        const decoder = new TextDecoder();
        let buffer = '';

        while (true) {
            const { done, value } = await reader.read();
            if (done) break;

            buffer += decoder.decode(value, { stream: true });
            const lines = buffer.split('\n');
            buffer = lines.pop(); // Keep incomplete last line in buffer

            for (const line of lines) {
                const trimmed = line.trim();
                if (!trimmed.startsWith('data: ')) continue;

                try {
                    const payload = JSON.parse(trimmed.slice(6));

                    if (payload.event === 'tool') {
                        onToolCall(payload.tool_name);
                    } else if (payload.event === 'done') {
                        onComplete(payload.response, payload.tools_used || [], payload.session_id);
                    } else if (payload.event === 'error') {
                        onError(payload.response);
                    }
                } catch (parseErr) {
                    console.warn('SSE parse error:', parseErr);
                }
            }
        }
    } catch (err) {
        console.error('Stream request failed:', err);
        onError('Connection error. Please try again.');
    }
};

export const getSessions = async () => {
    const response = await api.get('/chat/sessions');
    return response.data;
};

export const createSession = async () => {
    const response = await api.post('/chat/sessions');
    return response.data;
};

export const getSessionMessages = async (sessionId) => {
    const response = await api.get(`/chat/sessions/${sessionId}`);
    return response.data;
};

export const deleteSession = async (sessionId) => {
    const response = await api.delete(`/chat/sessions/${sessionId}`);
    return response.data;
};

export const resetSession = async (sessionId) => {
    const response = await api.post('/chat/reset', { session_id: sessionId });
    return response.data;
};

export default api;
