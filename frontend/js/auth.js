document.addEventListener('DOMContentLoaded', () => {
    const loginForm = document.getElementById('loginForm');
    const errorMsg = document.getElementById('errorMsg');

    if (loginForm) {
        loginForm.addEventListener('submit', async (e) => {
            e.preventDefault();
            
            const username = document.getElementById('username').value;
            const password = document.getElementById('password').value;
            const submitBtn = loginForm.querySelector('button[type="submit"]');

            try {
                submitBtn.disabled = true;
                submitBtn.textContent = 'Đang đăng nhập...';
                errorMsg.style.display = 'none';

                const formData = new FormData();
                formData.append('username', username);
                formData.append('password', password);

                const response = await fetchAPI('/auth/login', {
                    method: 'POST',
                    body: formData
                });

                localStorage.setItem('token', response.access_token);
                localStorage.setItem('user', JSON.stringify(response.user));

                // Redirect based on role
                const role = response.user.role;
                if (role === 'admin') {
                    window.location.href = 'admin/index.html';
                } else if (role === 'teacher') {
                    window.location.href = 'teacher/index.html';
                } else {
                    window.location.href = 'student/index.html';
                }
                
            } catch (error) {
                errorMsg.textContent = error.message;
                errorMsg.style.display = 'block';
            } finally {
                submitBtn.disabled = false;
                submitBtn.textContent = 'Đăng nhập';
            }
        });
    }
});
