// Tự động chọn URL backend phù hợp với môi trường:
// 1. Nếu có window._API_BASE tùy chỉnh (và không phải placeholder): ưu tiên dùng
// 2. Chạy local file:// hoặc localhost: dùng http://localhost:8000/api
// 3. Mặc định trên Vercel / server: dùng relative /api
const API_BASE = (
    window._API_BASE &&
    typeof window._API_BASE === 'string' &&
    window._API_BASE.trim() !== '' &&
    !window._API_BASE.includes('REPLACE_WITH')
)
    ? window._API_BASE.replace(/\/+$/, '')
    : (
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

    // Chuẩn hóa endpoint để tránh trùng /api/api
    let cleanEndpoint = endpoint.startsWith('/') ? endpoint : `/${endpoint}`;
    if (cleanEndpoint.startsWith('/api/') || cleanEndpoint === '/api') {
        cleanEndpoint = cleanEndpoint.slice(4) || '/';
    }
    const fullUrl = `${API_BASE}${cleanEndpoint.startsWith('/') ? cleanEndpoint : '/' + cleanEndpoint}`;

    try {
        const response = await fetch(fullUrl, {
            ...options,
            headers
        });

        let data;
        const contentType = response.headers.get('content-type') || '';
        if (contentType.includes('application/json')) {
            data = await response.json();
        } else {
            const rawText = await response.text();
            try {
                data = JSON.parse(rawText);
            } catch (e) {
                if (!response.ok) {
                    if (response.status === 404) {
                        throw new Error(`Không tìm thấy API (404 Not Found): Vercel chưa định tuyến được đến backend hoặc backend chưa khởi động.`);
                    }
                    if (response.status === 500) {
                        throw new Error(`Lỗi máy chủ (500 Server Error): Serverless Function gặp lỗi khi chạy. Kiểm tra Logs trên Vercel.`);
                    }
                    throw new Error(`Lỗi máy chủ (${response.status}): ${response.statusText || rawText.slice(0, 100)}`);
                }
                throw new Error(`Phản hồi máy chủ không hợp lệ: ${rawText.slice(0, 100)}`);
            }
        }

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
