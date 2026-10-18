// =====================================================
// HOÀNG CUNG HỌC ĐƯỜNG - CORE API & UI ENGINE
// =====================================================

// Xác định API BASE URL tự động
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

// Core Fetch API
async function fetchAPI(endpoint, options = {}) {
    const token = localStorage.getItem('token');

    const headers = {
        'Content-Type': 'application/json',
        'ngrok-skip-browser-warning': 'true',
        ...options.headers
    };

    if (token) {
        headers['Authorization'] = `Bearer ${token}`;
    }

    if (options.body instanceof FormData) {
        delete headers['Content-Type'];
    }

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
                        throw new Error(`Không tìm thấy API (404 Not Found)`);
                    }
                    if (response.status === 500) {
                        throw new Error(`Lỗi máy chủ (500 Server Error)`);
                    }
                    throw new Error(`Lỗi máy chủ (${response.status}): ${response.statusText || rawText.slice(0, 100)}`);
                }
                throw new Error(`Phản hồi máy chủ không hợp lệ: ${rawText.slice(0, 100)}`);
            }
        }

        if (!response.ok) {
            if (response.status === 401 && !endpoint.includes('/auth/login')) {
                logout();
            }
            throw new Error(data.detail || data.message || 'Lỗi kết nối máy chủ');
        }

        return data;
    } catch (error) {
        console.error('Fetch Error:', error);
        throw error;
    }
}

// User Helpers
function getUser() {
    try {
        const userStr = localStorage.getItem('user');
        return userStr ? JSON.parse(userStr) : null;
    } catch (e) {
        return null;
    }
}

function getToken() {
    return localStorage.getItem('token');
}

function logout() {
    localStorage.removeItem('token');
    localStorage.removeItem('user');
    const isSubDir = window.location.pathname.includes('/student/') || 
                     window.location.pathname.includes('/teacher/') || 
                     window.location.pathname.includes('/admin/');
    window.location.href = isSubDir ? '../index.html' : 'index.html';
}

function requireAuth(allowedRoles = []) {
    const user = getUser();
    const token = getToken();
    const isSubDir = window.location.pathname.includes('/student/') || 
                     window.location.pathname.includes('/teacher/') || 
                     window.location.pathname.includes('/admin/');
    const loginPage = isSubDir ? '../index.html' : 'index.html';

    if (!token || !user) {
        window.location.href = loginPage;
        return false;
    }

    if (allowedRoles.length > 0 && !allowedRoles.includes(user.role)) {
        showToast('Bạn không có quyền truy cập trang này!', 'error');
        setTimeout(() => {
            if (user.role === 'admin') window.location.href = isSubDir ? '../admin/index.html' : 'admin/index.html';
            else if (user.role === 'teacher') window.location.href = isSubDir ? '../teacher/index.html' : 'teacher/index.html';
            else window.location.href = isSubDir ? '../student/index.html' : 'student/index.html';
        }, 1200);
        return false;
    }

    return true;
}

// Toast Notifications System
function showToast(message, type = 'info') {
    let container = document.getElementById('toastContainer');
    if (!container) {
        container = document.createElement('div');
        container.id = 'toastContainer';
        document.body.appendChild(container);
    }

    const toast = document.createElement('div');
    toast.className = `toast toast-${type}`;

    const icons = {
        success: '✓',
        error: '✕',
        info: '📜'
    };

    toast.innerHTML = `
        <span class="toast-icon" style="font-size: 1.2rem; font-weight: bold;">${icons[type] || '•'}</span>
        <div class="toast-body">${message}</div>
    `;

    container.appendChild(toast);

    setTimeout(() => {
        toast.style.opacity = '0';
        toast.style.transform = 'translateX(50px)';
        setTimeout(() => toast.remove(), 300);
    }, 3500);
}

// Format Date / Datetime
function formatDate(dateStr, includeTime = true) {
    if (!dateStr) return '—';
    try {
        const d = new Date(dateStr);
        if (isNaN(d.getTime())) return dateStr;
        const day = String(d.getDate()).padStart(2, '0');
        const month = String(d.getMonth() + 1).padStart(2, '0');
        const year = d.getFullYear();
        if (!includeTime) return `${day}/${month}/${year}`;
        const hours = String(d.getHours()).padStart(2, '0');
        const mins = String(d.getMinutes()).padStart(2, '0');
        return `${hours}:${mins} ${day}/${month}/${year}`;
    } catch (e) {
        return dateStr;
    }
}

// Format Rank Badge
function renderRankBadge(rank, icon = '📜', color = null) {
    const customStyle = color ? `style="border-color:${color}; color:${color};"` : '';
    return `<span class="rank-badge" ${customStyle}>${icon} ${rank || 'Học viên'}</span>`;
}

// Shared Mobile Navigation & Topbar Initialization
function initMobileNav(activePage = '') {
    const user = getUser();
    if (!user) return;

    // Set Topbar User Info if elements exist
    const userNameEl = document.getElementById('userName');
    if (userNameEl) userNameEl.textContent = user.full_name || user.username;

    const userRoleEl = document.querySelector('.user-role');
    if (userRoleEl) {
        const roleLabels = {
            admin: 'Quản Trị Triều Đình',
            teacher: 'Thái Phó (Giáo Viên)',
            student: 'Học Tử (Học Sinh)'
        };
        userRoleEl.textContent = roleLabels[user.role] || user.role;
    }

    // Insert Mobile Drawer Backdrop
    let backdrop = document.querySelector('.drawer-backdrop');
    if (!backdrop) {
        backdrop = document.createElement('div');
        backdrop.className = 'drawer-backdrop';
        document.body.appendChild(backdrop);
    }

    // Setup Hamburger Toggle
    const toggleBtn = document.querySelector('.menu-toggle');
    const sidebar = document.querySelector('.sidebar');
    if (toggleBtn && sidebar) {
        toggleBtn.addEventListener('click', () => {
            sidebar.classList.toggle('open');
            backdrop.classList.toggle('active');
        });

        backdrop.addEventListener('click', () => {
            sidebar.classList.remove('open');
            backdrop.classList.remove('active');
        });
    }

    // Build Mobile Bottom Navigation Bar if not already present
    let bottomNav = document.querySelector('.mobile-bottom-nav');
    if (!bottomNav) {
        bottomNav = document.createElement('nav');
        bottomNav.className = 'mobile-bottom-nav';

        let navItems = [];
        if (user.role === 'student') {
            navItems = [
                { id: 'dashboard', label: 'Tổng Quan', icon: '🏯', href: 'index.html' },
                { id: 'assignments', label: 'Tấu Chương', icon: '📝', href: 'assignments.html' },
                { id: 'leaderboard', label: 'Bảng Vàng', icon: '🏆', href: 'leaderboard.html' },
                { id: 'notifications', label: 'Thông Báo', icon: '🔔', href: '#', onClick: 'openNotificationsModal()' }
            ];
        } else if (user.role === 'teacher') {
            navItems = [
                { id: 'dashboard', label: 'Tổng Quan', icon: '🏯', href: 'index.html' },
                { id: 'assignments', label: 'Bài Tập', icon: '📜', href: 'assignments.html' },
                { id: 'submissions', label: 'Chấm Điểm', icon: '✍️', href: 'submissions.html' },
                { id: 'attendance', label: 'Điểm Danh', icon: '📅', href: 'attendance.html' }
            ];
        } else if (user.role === 'admin') {
            navItems = [
                { id: 'dashboard', label: 'Tổng Quan', icon: '🏯', href: 'index.html#dashboard' },
                { id: 'students', label: 'Học Sinh', icon: '👥', href: 'index.html#students' },
                { id: 'teachers', label: 'Thái Phó', icon: '🎓', href: 'index.html#teachers' },
                { id: 'classes', label: 'Lớp Học', icon: '🏛️', href: 'index.html#classes' }
            ];
        }

        bottomNav.innerHTML = navItems.map(item => `
            <a href="${item.href}" class="mobile-nav-link ${activePage === item.id ? 'active' : ''}" 
               ${item.onClick ? `onclick="${item.onClick}; return false;"` : ''}>
                <span class="nav-icon">${item.icon}</span>
                <span>${item.label}</span>
            </a>
        `).join('');

        document.body.appendChild(bottomNav);
    }

    // Initialize Notifications
    initNotificationBell();
}

// Global Notification Modal System
async function initNotificationBell() {
    const notifBtn = document.getElementById('notifBtn');
    if (!notifBtn) return;

    try {
        const notifs = await fetchAPI('/scores/notifications');
        const unreadCount = notifs.filter(n => n.is_read !== 'true' && n.is_read !== true).length;
        
        let badge = notifBtn.querySelector('.notif-badge');
        if (unreadCount > 0) {
            if (!badge) {
                badge = document.createElement('span');
                badge.className = 'notif-badge';
                notifBtn.appendChild(badge);
            }
            badge.textContent = unreadCount > 99 ? '99+' : unreadCount;
        } else if (badge) {
            badge.remove();
        }

        notifBtn.onclick = () => openNotificationsModal(notifs);
    } catch (e) {
        console.warn('Could not load notifications:', e);
    }
}

function openNotificationsModal(notifsData) {
    let modal = document.getElementById('globalNotifModal');
    if (!modal) {
        modal = document.createElement('div');
        modal.id = 'globalNotifModal';
        modal.className = 'modal-overlay';
        modal.innerHTML = `
            <div class="modal-content">
                <div class="modal-header">
                    <h2>📜 Chiếu Chỉ & Thông Báo</h2>
                    <button class="modal-close-btn" onclick="closeNotificationsModal()">&times;</button>
                </div>
                <div class="d-flex justify-between align-center mb-1">
                    <span style="font-size: 0.85rem; color: var(--text-muted)">Thông báo gần đây</span>
                    <button class="btn btn-secondary btn-sm" onclick="markAllNotificationsRead()">Đọc tất cả</button>
                </div>
                <div id="notifListContainer" style="max-height: 400px; overflow-y: auto; display: flex; flex-direction: column; gap: 0.75rem;">
                    <p class="text-center" style="color: var(--text-muted); padding: 2rem;">Đang tải thông báo...</p>
                </div>
            </div>
        `;
        document.body.appendChild(modal);
    }

    modal.style.display = 'flex';
    renderNotifList(notifsData);
}

function closeNotificationsModal() {
    const modal = document.getElementById('globalNotifModal');
    if (modal) modal.style.display = 'none';
}

async function renderNotifList(preloadedNotifs) {
    const container = document.getElementById('notifListContainer');
    if (!container) return;

    try {
        const notifs = preloadedNotifs || await fetchAPI('/scores/notifications');
        if (!notifs || notifs.length === 0) {
            container.innerHTML = '<p class="text-center" style="color: var(--text-muted); padding: 2rem;">Triều đình hiện không có chiếu chỉ mới.</p>';
            return;
        }

        container.innerHTML = notifs.map(n => {
            const isUnread = n.is_read !== 'true' && n.is_read !== true;
            return `
                <div style="padding: 0.85rem; border-radius: var(--radius-md); background: ${isUnread ? 'rgba(212, 175, 55, 0.1)' : 'rgba(255,255,255,0.03)'}; border: 1px solid ${isUnread ? 'var(--border-color)' : 'var(--border-subtle)'}; display: flex; gap: 0.75rem; align-items: flex-start;">
                    <span style="font-size: 1.3rem;">📜</span>
                    <div style="flex: 1;">
                        <div style="font-size: 0.92rem; font-weight: ${isUnread ? '600' : '400'}; color: var(--text-primary);">${n.message || n.title || 'Thông báo mới'}</div>
                        <div style="font-size: 0.75rem; color: var(--text-muted); margin-top: 0.2rem;">${formatDate(n.created_at)}</div>
                    </div>
                    ${isUnread ? `<button class="btn btn-secondary btn-sm" onclick="markSingleNotifRead(${n.notification_id}, this)">Đã đọc</button>` : ''}
                </div>
            `;
        }).join('');
    } catch (e) {
        container.innerHTML = `<p class="text-center" style="color: var(--crimson);">Lỗi tải thông báo: ${e.message}</p>`;
    }
}

async function markAllNotificationsRead() {
    try {
        await fetchAPI('/scores/notifications/read-all', { method: 'PUT' });
        showToast('Đã đánh dấu tất cả thông báo là đã đọc', 'success');
        initNotificationBell();
        renderNotifList();
    } catch (e) {
        showToast('Lỗi: ' + e.message, 'error');
    }
}

async function markSingleNotifRead(id, btn) {
    try {
        await fetchAPI(`/scores/notifications/${id}/read`, { method: 'PUT' });
        if (btn) btn.remove();
        initNotificationBell();
    } catch (e) {
        showToast('Lỗi: ' + e.message, 'error');
    }
}
