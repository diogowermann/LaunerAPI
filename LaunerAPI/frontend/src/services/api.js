import axios from 'axios';

const api = axios.create({
    baseURL: 'http://localhost:8000/api', // Change this to your backend URL
    headers: {
        'Content-Type': 'application/json',
    },
    timeout: 10000,
});

api.interceptors.request.use((config) => {
    const token = localStorage.getItem('access_token');
    const expiresAt = localStorage.getItem('expires_at');
    const isExpired = new Date().getTime() > parseInt(expiresAt, 10);

    if (isExpired) {
        localStorage.removeItem('access_token');
        localStorage.removeItem('expires_at');
        window.location.href = '/'; // Redirect to login page
        return Promise.reject('Tempo excedido');
    }

    if (token) {
        config.headers.Authorization = `Bearer ${token}`;
    }
    return config;
});

export default api;