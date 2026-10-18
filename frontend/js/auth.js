document.addEventListener('DOMContentLoaded', () => {
    // If already logged in, redirect to corresponding dashboard
    const user = getUser();
    const token = getToken();
    if (user && token) {
        if (user.role === 'admin') window.location.href = 'admin/index.html';
        else if (user.role === 'teacher') window.location.href = 'teacher/index.html';
        else if (user.role === 'student') window.location.href = 'student/index.html';
        return;
    }

    const loginForm = document.getElementById('loginForm');
    const errorMsg = document.getElementById('errorMsg');

    if (loginForm) {
        loginForm.addEventListener('submit', async (e) => {
            e.preventDefault();
            
            const usernameInput = document.getElementById('username');
            const passwordInput = document.getElementById('password');
            const submitBtn = loginForm.querySelector('button[type="submit"]');

            const username = usernameInput.value.trim();
            const password = passwordInput.value;

            if (!username || !password) {
                showError('Vui lòng nhập đầy đủ Thẻ Bài (Tên đăng nhập) và Khẩu Quyết (Mật khẩu)!');
                return;
            }

            try {
                submitBtn.disabled = true;
                submitBtn.innerHTML = '<span>Đang Tiến Cung...</span>';
                if (errorMsg) errorMsg.style.display = 'none';

                const formData = new FormData();
                formData.append('username', username);
                formData.append('password', password);

                const response = await fetchAPI('/auth/login', {
                    method: 'POST',
                    body: formData
                });

                localStorage.setItem('token', response.access_token);
                localStorage.setItem('user', JSON.stringify(response.user));

                showToast(`Chào mừng ${response.user.full_name || response.user.username} đã tiến cung!`, 'success');

                setTimeout(() => {
                    const role = response.user.role;
                    if (role === 'admin') {
                        window.location.href = 'admin/index.html';
                    } else if (role === 'teacher') {
                        window.location.href = 'teacher/index.html';
                    } else {
                        window.location.href = 'student/index.html';
                    }
                }, 600);
                
            } catch (error) {
                showError(error.message || 'Tên đăng nhập hoặc mật khẩu không chính xác!');
            } finally {
                submitBtn.disabled = false;
                submitBtn.innerHTML = '<span>Tiến Cung (Đăng Nhập)</span>';
            }
        });
    }
});

function showError(msg) {
    const errorMsg = document.getElementById('errorMsg');
    if (errorMsg) {
        errorMsg.textContent = msg;
        errorMsg.style.display = 'block';
    } else {
        showToast(msg, 'error');
    }
}

// Quick Fill Demo Credentials
function quickLogin(username, password) {
    const u = document.getElementById('username');
    const p = document.getElementById('password');
    if (u && p) {
        u.value = username;
        p.value = password;
        const form = document.getElementById('loginForm');
        if (form) {
            form.dispatchEvent(new Event('submit', { cancelable: true }));
        }
    }
}

function togglePasswordVisibility() {
    const p = document.getElementById('password');
    const icon = document.getElementById('togglePassIcon');
    if (p) {
        if (p.type === 'password') {
            p.type = 'text';
            if (icon) icon.textContent = '👁️';
        } else {
            p.type = 'password';
            if (icon) icon.textContent = '🙈';
        }
    }
}
