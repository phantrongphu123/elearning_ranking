// Tự động chọn URL backend phù hợp với môi trường:
// - Mở file trực tiếp (file://) hoặc localhost → backend local port 8000
// - Deploy trên Vercel / bất kỳ server nào → dùng /api relative (không cần cấu hình)
const API_BASE = (
    window.location.protocol === 'file:' ||
    window.location.hostname === 'localhost' ||
    window.location.hostname === '127.0.0.1'
)
    ? 'http://localhost:8000/api'
    : '/api';

async function fetchAPI(endpoint, options = {}) {
    const token = localStorage.getItem('token');

    const headers = {
        'Content-Type': 'application/json',
        'ngrok-skip-browser-warning': 'true',  // Bypass ngrok warning page
        ...options.headers
    };

    if (token) {
        headers['Authorization'] = `Bearer ${token}`;
    }

    // If body is FormData, fetch sets Content-Type automatically with boundary
    if (options.body instanceof FormData) {
        delete headers['Content-Type'];
    }

    try {
        const response = await fetch(`${API_BASE}${endpoint}`, {
            ...options,
            headers
        });

        const data = await response.json();

        if (!response.ok) {
            if (response.status === 401 && endpoint !== '/auth/login') {
                localStorage.removeItem('token');
                localStorage.removeItem('user');
                window.location.href = '../index.html';
            }
            throw new Error(data.detail || data.message || 'Lỗi kết nối API');
        }

        return data;
    } catch (error) {
        console.error('API Error:', error);
        throw error;
    }
}

function logout() {
    localStorage.removeItem('token');
    localStorage.removeItem('user');
    window.location.href = '../index.html';
}

function getUser() {
    const userStr = localStorage.getItem('user');
    return userStr ? JSON.parse(userStr) : null;
}
