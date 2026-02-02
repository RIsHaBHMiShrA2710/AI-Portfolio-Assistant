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
