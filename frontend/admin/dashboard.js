let currentAdminTab = 'dashboard';
let allStudentsCache = [];
let allClassesCache = [];
let allTeachersCache = [];

document.addEventListener('DOMContentLoaded', async () => {
    if (!requireAuth(['admin'])) return;
    initMobileNav('dashboard');

    // Handle hash route or default to dashboard
    const hash = window.location.hash.replace('#', '') || 'dashboard';
    const targetNavLink = document.querySelector(`.sidebar-nav a[href="#${hash}"]`);
    switchAdminTab(hash, targetNavLink);

    // Initial preload
    await loadAdminDashboard();
    await loadClassesCache();
    initModalsAndForms();
});

function switchAdminTab(tabName, navLinkEl) {
    currentAdminTab = tabName;

    // Update Nav active
    document.querySelectorAll('.sidebar-nav .nav-item').forEach(el => el.classList.remove('active'));
    if (navLinkEl) navLinkEl.classList.add('active');

    // Update Tab Sections
    document.querySelectorAll('.tab-content').forEach(el => el.classList.remove('active'));
    const targetSection = document.getElementById(`tab-${tabName}`);
    if (targetSection) targetSection.classList.add('active');

    // Update Header Titles
    const titleEl = document.getElementById('pageHeaderTitle');
    const subTitleEl = document.getElementById('pageHeaderSubtitle');

    const meta = {
        dashboard: { title: 'Toàn Cảnh Triều Đình · 皇城总览', sub: 'Báo cáo tình hình học viện Hán ngữ toàn diện' },
        students: { title: 'Quản Lý Học Tử · 学子管理', sub: 'Danh sách, xếp hạng và cấp phát tài khoản học sinh' },
        teachers: { title: 'Quản Lý Thái Phó · 太傅管理', sub: 'Danh sách và phân quyền đội ngũ giảng dạy' },
        classes: { title: 'Quản Lý Lớp Học · 班级管理', sub: 'Điều phối lớp học, niên khóa và sĩ số' },
        scores: { title: 'Chiếu Chỉ Triều Đình · 圣旨奖惩', sub: 'Ban thưởng hoặc xử phạt điểm tích lũy học tử' }
    };

    if (meta[tabName]) {
        if (titleEl) titleEl.textContent = meta[tabName].title;
        if (subTitleEl) subTitleEl.textContent = meta[tabName].sub;
    }

    // Load Data for Tab
    if (tabName === 'dashboard') loadAdminDashboard();
    else if (tabName === 'students') loadStudentsManagement();
    else if (tabName === 'teachers') loadTeachersManagement();
    else if (tabName === 'classes') loadClassesManagement();
    else if (tabName === 'scores') loadScoresTab();
}

// ----------------------------------------------------
// TAB 1: DASHBOARD
// ----------------------------------------------------
async function loadAdminDashboard() {
    try {
        const data = await fetchAPI('/dashboard/admin');

        document.getElementById('dashTotalStudents').textContent = data.total_students || 0;
        document.getElementById('dashTotalClasses').textContent = data.total_classes || 0;
        document.getElementById('dashTotalTeachers').textContent = data.total_teachers || 0;
        document.getElementById('dashAvgScore').textContent = data.avg_score || 0;

        const subStats = document.getElementById('dashSubmissionsStats');
        if (subStats) {
            subStats.textContent = `Bài nộp tuần này: ${data.submissions_this_week || 0} / Tổng: ${data.total_submissions || 0}`;
        }

        // Top 5 Students
        const topTable = document.getElementById('dashTopStudentsTable');
        if (topTable) {
            if (data.top_students && data.top_students.length > 0) {
                topTable.innerHTML = data.top_students.map((s, idx) => `
                    <tr>
                        <td style="font-family: 'Plus Jakarta Sans', 'Be Vietnam Pro', sans-serif; font-weight: 700; color: ${idx === 0 ? 'var(--gold-light)' : 'inherit'};">
                            #${idx + 1}
                        </td>
                        <td><strong>${escapeHtml(s.full_name)}</strong> (${escapeHtml(s.student_code)})</td>
                        <td>
                            <span class="rank-badge sm">${escapeHtml(s.rank || 'Học sinh')}</span>
                        </td>
                        <td style="font-family: 'Plus Jakarta Sans', 'Be Vietnam Pro', sans-serif; font-weight: 700; color: var(--gold-light);">
                            ${s.total_score}đ
                        </td>
                    </tr>
                `).join('');
            } else {
                topTable.innerHTML = '<tr><td colspan="4" class="text-center" style="padding: 1.5rem;">Chưa có dữ liệu</td></tr>';
            }
        }

        // Rank Distribution
        const distContainer = document.getElementById('dashRankDistribution');
        if (distContainer && data.rank_distribution) {
            const entries = Object.entries(data.rank_distribution);
            if (entries.length > 0) {
                distContainer.innerHTML = entries.map(([rank, count]) => `
                    <div class="rank-dist-card">
                        <span style="font-size: 0.9rem; font-weight: 600; color: var(--gold-light);">${escapeHtml(rank)}</span>
                        <span class="badge badge-gold">${count} học tử</span>
                    </div>
                `).join('');
            } else {
                distContainer.innerHTML = '<p style="color: var(--text-muted)">Chưa có dữ liệu phân bố tước vị.</p>';
            }
        }

    } catch (e) {
        console.error('Lỗi tải dashboard admin:', e);
    }
}

// ----------------------------------------------------
// TAB 2: STUDENTS
// ----------------------------------------------------
async function loadClassesCache() {
    try {
        allClassesCache = await fetchAPI('/classes');
        const filterSelect = document.getElementById('studentClassFilterSelect');
        const csClassSelect = document.getElementById('csClassSelect');

        if (filterSelect) {
            filterSelect.innerHTML = '<option value="">Tất Cả Lớp</option>';
            allClassesCache.forEach(c => {
                const opt = document.createElement('option');
                opt.value = c.class_id;
                opt.textContent = `${c.class_name} (${c.class_code})`;
                filterSelect.appendChild(opt);
            });
        }

        if (csClassSelect) {
            csClassSelect.innerHTML = '<option value="">-- Chọn lớp học --</option>';
            allClassesCache.forEach(c => {
                const opt = document.createElement('option');
                opt.value = c.class_id;
                opt.textContent = `${c.class_name} (${c.class_code})`;
                csClassSelect.appendChild(opt);
            });
        }
    } catch (e) {
        console.warn('Lỗi tải lớp:', e);
    }
}

async function loadStudentsManagement() {
    const classId = document.getElementById('studentClassFilterSelect')?.value || '';
    const tbody = document.getElementById('studentsManageTableBody');
    if (!tbody) return;

    try {
        const url = classId ? `/students?class_id=${classId}` : '/students';
        allStudentsCache = await fetchAPI(url);
        filterStudentsList();
    } catch (e) {
        tbody.innerHTML = `<tr><td colspan="7" class="text-center" style="color: var(--crimson);">Lỗi: ${e.message}</td></tr>`;
    }
}

function filterStudentsList() {
    const tbody = document.getElementById('studentsManageTableBody');
    if (!tbody) return;

    const term = (document.getElementById('studentSearchInput')?.value || '').toLowerCase();
    const filtered = allStudentsCache.filter(s => 
        (s.full_name && s.full_name.toLowerCase().includes(term)) ||
        (s.student_code && s.student_code.toLowerCase().includes(term))
    );

    if (filtered.length === 0) {
        tbody.innerHTML = '<tr><td colspan="7" class="text-center" style="padding: 2.5rem; color: var(--text-muted)">Không tìm thấy học tử nào.</td></tr>';
        return;
    }

    const classMap = new Map();
    allClassesCache.forEach(c => classMap.set(String(c.class_id), c.class_name));

    tbody.innerHTML = filtered.map(s => {
        const className = classMap.get(String(s.class_id)) || (s.class_id ? `Lớp #${s.class_id}` : 'Chưa xếp lớp');
        const genderLabel = s.gender === 'male' ? 'Nam' : 'Nữ';

        return `
            <tr>
                <td style="font-family: monospace; font-size: 0.88rem; color: var(--text-muted);">${escapeHtml(s.student_code)}</td>
                <td><strong style="color: var(--gold-light);">${escapeHtml(s.full_name)}</strong></td>
                <td>${genderLabel}</td>
                <td><span class="badge badge-info">${escapeHtml(className)}</span></td>
                <td>
                    <span class="rank-badge sm" style="border-color:${s.color || 'var(--gold-primary)'}; color:${s.color || 'var(--gold-light)'};">
                        ${escapeHtml(s.rank || 'Học sinh')}
                    </span>
                </td>
                <td style="font-family: 'Plus Jakarta Sans', 'Be Vietnam Pro', sans-serif; font-weight: 700; color: var(--gold-light);">
                    ${s.total_score}đ
                </td>
                <td>
                    <div class="d-flex gap-1" style="align-items: center;">
                        <button class="btn btn-secondary btn-sm" onclick="openQuickScoreForStudent(${s.student_id})">
                            <span>Cộng/Trừ Điểm</span>
                        </button>
                        <button class="btn btn-danger btn-sm" onclick="deleteStudent(${s.student_id})">
                            <span>Vô hiệu hóa</span>
                        </button>
                    </div>
                </td>
            </tr>
        `;
    }).join('');
}

async function deleteStudent(studentId) {
    if (!confirm('Bạn có chắc chắn muốn vô hiệu hóa học tử này khỏi học viện?')) return;
    try {
        await fetchAPI(`/students/${studentId}`, { method: 'DELETE' });
        showToast('Đã vô hiệu hóa học sinh thành công!', 'success');
        await loadStudentsManagement();
    } catch (e) {
        showToast('Lỗi: ' + e.message, 'error');
    }
}

// ----------------------------------------------------
// TAB 3: TEACHERS
// ----------------------------------------------------
async function loadTeachersManagement() {
    const tbody = document.getElementById('teachersManageTableBody');
    if (!tbody) return;

    try {
        allTeachersCache = await fetchAPI('/teachers');
        if (!allTeachersCache || allTeachersCache.length === 0) {
            tbody.innerHTML = '<tr><td colspan="6" class="text-center" style="padding: 2.5rem; color: var(--text-muted)">Chưa có giáo viên nào được tạo.</td></tr>';
            return;
        }

        tbody.innerHTML = allTeachersCache.map(t => `
            <tr>
                <td style="font-family: monospace; color: var(--text-muted);">#${t.user_id}</td>
                <td><strong style="color: var(--gold-light);">${escapeHtml(t.username)}</strong></td>
                <td>${escapeHtml(t.full_name || '—')}</td>
                <td>
                    <span class="badge ${t.status === 'active' ? 'badge-success' : 'badge-danger'}">
                        ${t.status === 'active' ? 'Hoạt động' : 'Tạm khóa'}
                    </span>
                </td>
                <td style="font-size: 0.82rem; color: var(--text-muted);">${formatDate(t.created_at)}</td>
                <td>
                    <button class="btn btn-danger btn-sm" onclick="deleteTeacher(${t.user_id})">
                        <span>Vô hiệu</span>
                    </button>
                </td>
            </tr>
        `).join('');

        // Also update class teacher dropdown
        const ccSelect = document.getElementById('ccTeacherSelect');
        if (ccSelect) {
            ccSelect.innerHTML = '<option value="">-- Chưa phân công --</option>' + allTeachersCache.map(t => `
                <option value="${t.user_id}">${escapeHtml(t.full_name)} (${escapeHtml(t.username)})</option>
            `).join('');
        }

    } catch (e) {
        tbody.innerHTML = `<tr><td colspan="6" class="text-center" style="color: var(--crimson);">Lỗi: ${e.message}</td></tr>`;
    }
}

async function deleteTeacher(userId) {
    if (!confirm('Bạn có chắc muốn vô hiệu hóa tài khoản Thái Phó này?')) return;
    try {
        await fetchAPI(`/teachers/${userId}`, { method: 'DELETE' });
        showToast('Đã vô hiệu hóa giảng viên!', 'success');
        await loadTeachersManagement();
    } catch (e) {
        showToast('Lỗi: ' + e.message, 'error');
    }
}

// ----------------------------------------------------
// TAB 4: CLASSES
// ----------------------------------------------------
async function loadClassesManagement() {
    const tbody = document.getElementById('classesManageTableBody');
    if (!tbody) return;

    try {
        allClassesCache = await fetchAPI('/classes');
        if (!allClassesCache || allClassesCache.length === 0) {
            tbody.innerHTML = '<tr><td colspan="7" class="text-center" style="padding: 2.5rem; color: var(--text-muted)">Chưa có lớp học nào. Hãy mở lớp mới.</td></tr>';
            return;
        }

        tbody.innerHTML = allClassesCache.map(c => `
            <tr>
                <td style="font-family: monospace; font-weight: 700; color: var(--gold-light);">${escapeHtml(c.class_code)}</td>
                <td><strong>${escapeHtml(c.class_name)}</strong></td>
                <td>${escapeHtml(c.teacher_name || 'Chưa phân công')}</td>
                <td style="font-weight: 600; color: var(--gold-primary); text-align: center;">${c.student_count || 0} học sinh</td>
                <td>${escapeHtml(c.school_year || '2026-2027')}</td>
                <td>
                    <span class="badge ${c.status === 'active' ? 'badge-success' : 'badge-danger'}">
                        ${c.status === 'active' ? 'Đang mở' : 'Đã khóa'}
                    </span>
                </td>
                <td>
                    <button class="btn btn-danger btn-sm" onclick="deleteClass(${c.class_id})">
                        <span>Đóng lớp</span>
                    </button>
                </td>
            </tr>
        `).join('');

    } catch (e) {
        tbody.innerHTML = `<tr><td colspan="7" class="text-center" style="color: var(--crimson);">Lỗi: ${e.message}</td></tr>`;
    }
}

async function deleteClass(classId) {
    if (!confirm('Bạn có chắc muốn đóng lớp học này?')) return;
    try {
        await fetchAPI(`/classes/${classId}`, { method: 'DELETE' });
        showToast('Đã đóng lớp học!', 'success');
        await loadClassesManagement();
        await loadClassesCache();
    } catch (e) {
        showToast('Lỗi: ' + e.message, 'error');
    }
}

// ----------------------------------------------------
// TAB 5: SCORES & DECREES
// ----------------------------------------------------
async function loadScoresTab() {
    const select = document.getElementById('adminScoreStudentSelect');
    if (!select) return;

    select.innerHTML = '<option value="">Đang tải danh sách học tử...</option>';
    try {
        const students = await fetchAPI('/students');
        select.innerHTML = '<option value="">-- Chọn học tử tiếp nhận chiếu chỉ --</option>' + students.map(s => `
            <option value="${s.student_id}">${escapeHtml(s.full_name)} (${s.student_code}) · ${s.rank || 'Học tử'} (${s.total_score}đ)</option>
        `).join('');

        updateAdminPresetReasons();
    } catch (e) {
        select.innerHTML = `<option value="">Lỗi: ${e.message}</option>`;
    }
}

function updateAdminPresetReasons() {
    const type = document.getElementById('adminScoreType').value;
    const ptsInput = document.getElementById('adminScorePoints');
    const container = document.getElementById('adminPresetReasons');
    if (!container) return;

    let presets = [];
    if (type === 'bonus') {
        ptsInput.value = 20;
        presets = [
            { text: '+20đ Chiếu chỉ biểu dương Hán tự', pts: 20, reason: 'Chiếu chỉ hoàng gia biểu dương tinh thần hiếu học' },
            { text: '+50đ Đạt giải học sinh giỏi', pts: 50, reason: 'Đạt thành tích giải thưởng Hán ngữ xuất sắc' },
            { text: '+30đ Tiến bộ vượt bậc', pts: 30, reason: 'Nỗ lực rèn luyện, thăng tiến vượt bậc' }
        ];
    } else if (type === 'penalty') {
        ptsInput.value = -20;
        presets = [
            { text: '-20đ Vi phạm nội quy triều đình', pts: -20, reason: 'Vi phạm nghiêm trọng quy chế học đường' },
            { text: '-50đ Gian lận khảo hạch', pts: -50, reason: 'Gian lận trong kỳ thi trắc nghiệm tiếng Trung' }
        ];
    } else {
        presets = [];
    }

    container.innerHTML = presets.map(p => `
        <button type="button" class="btn btn-secondary btn-sm" onclick="document.getElementById('adminScorePoints').value=${p.pts}; document.getElementById('adminScoreReason').value='${escapeHtml(p.reason)}';">
            <span>${p.text}</span>
        </button>
    `).join('');
}

function openQuickScoreForStudent(studentId) {
    switchAdminTab('scores', document.querySelector('.sidebar-nav a[href="#scores"]'));
    setTimeout(() => {
        const select = document.getElementById('adminScoreStudentSelect');
        if (select) select.value = studentId;
    }, 400);
}

// ----------------------------------------------------
// MODALS & FORMS INITIALIZATION
// ----------------------------------------------------
function initModalsAndForms() {
    // Student Form
    const sForm = document.getElementById('createStudentForm');
    if (sForm) {
        sForm.addEventListener('submit', async (e) => {
            e.preventDefault();
            const code = document.getElementById('csStudentCode').value.trim();
            const name = document.getElementById('csFullName').value.trim();
            const gender = document.getElementById('csGender').value;
            const classId = document.getElementById('csClassSelect').value;
            const username = document.getElementById('csUsername').value.trim();
            const password = document.getElementById('csPassword').value;

            const btn = sForm.querySelector('button[type="submit"]');
            try {
                btn.disabled = true;
                btn.innerHTML = '<span>Đang ghi sổ học bộ...</span>';

                await fetchAPI('/students', {
                    method: 'POST',
                    body: JSON.stringify({
                        student_code: code,
                        full_name: name,
                        gender: gender,
                        class_id: classId ? parseInt(classId) : null,
                        username: username,
                        password: password
                    })
                });

                closeCreateStudentModal();
                showToast(`Đã thêm học sinh ${name} thành công!`, 'success');
                sForm.reset();
                await loadStudentsManagement();
            } catch (err) {
                showToast('Lỗi thêm học tử: ' + err.message, 'error');
            } finally {
                btn.disabled = false;
                btn.innerHTML = '<span>Tạo Học Tử & Cấp Tài Khoản</span>';
            }
        });
    }

    // Teacher Form
    const tForm = document.getElementById('createTeacherForm');
    if (tForm) {
        tForm.addEventListener('submit', async (e) => {
            e.preventDefault();
            const name = document.getElementById('ctFullName').value.trim();
            const username = document.getElementById('ctUsername').value.trim();
            const password = document.getElementById('ctPassword').value;

            const btn = tForm.querySelector('button[type="submit"]');
            try {
                btn.disabled = true;
                btn.innerHTML = '<span>Đang bổ nhiệm...</span>';

                await fetchAPI('/teachers', {
                    method: 'POST',
                    body: JSON.stringify({
                        full_name: name,
                        username: username,
                        password: password
                    })
                });

                closeCreateTeacherModal();
                showToast(`Đã bổ nhiệm giảng viên ${name} thành công!`, 'success');
                tForm.reset();
                await loadTeachersManagement();
            } catch (err) {
                showToast('Lỗi: ' + err.message, 'error');
            } finally {
                btn.disabled = false;
                btn.innerHTML = '<span>Bổ Nhiệm Thái Phó</span>';
            }
        });
    }

    // Class Form
    const cForm = document.getElementById('createClassForm');
    if (cForm) {
        cForm.addEventListener('submit', async (e) => {
            e.preventDefault();
            const code = document.getElementById('ccClassCode').value.trim();
            const name = document.getElementById('ccClassName').value.trim();
            const teacherId = document.getElementById('ccTeacherSelect').value;
            const year = document.getElementById('ccSchoolYear').value.trim();

            const btn = cForm.querySelector('button[type="submit"]');
            try {
                btn.disabled = true;
                btn.innerHTML = '<span>Đang thiết lập lớp...</span>';

                await fetchAPI('/classes', {
                    method: 'POST',
                    body: JSON.stringify({
                        class_code: code,
                        class_name: name,
                        teacher_id: teacherId ? parseInt(teacherId) : null,
                        school_year: year || '2026-2027'
                    })
                });

                closeCreateClassModal();
                showToast(`Đã mở lớp học ${name} thành công!`, 'success');
                cForm.reset();
                await loadClassesManagement();
                await loadClassesCache();
            } catch (err) {
                showToast('Lỗi: ' + err.message, 'error');
            } finally {
                btn.disabled = false;
                btn.innerHTML = '<span>Thành Lập Lớp Học</span>';
            }
        });
    }

    // Admin Score Form
    const scoreForm = document.getElementById('adminScoreForm');
    if (scoreForm) {
        scoreForm.addEventListener('submit', async (e) => {
            e.preventDefault();
            const sId = document.getElementById('adminScoreStudentSelect').value;
            const type = document.getElementById('adminScoreType').value;
            const pts = parseFloat(document.getElementById('adminScorePoints').value);
            const reason = document.getElementById('adminScoreReason').value.trim();

            if (!sId) {
                showToast('Vui lòng chọn học tử!', 'error');
                return;
            }

            const btn = scoreForm.querySelector('button[type="submit"]');
            try {
                btn.disabled = true;
                btn.innerHTML = '<span>Đang ban bố chiếu chỉ...</span>';

                await fetchAPI('/scores', {
                    method: 'POST',
                    body: JSON.stringify({
                        student_id: parseInt(sId),
                        points: pts,
                        reason: reason,
                        score_type: type
                    })
                });

                showToast(`⭐ Chiếu chỉ đã ban hành: ${pts >= 0 ? '+' : ''}${pts} điểm cho học tử!`, 'success');
                scoreForm.reset();
                updateAdminPresetReasons();
            } catch (err) {
                showToast('Lỗi ban chiếu: ' + err.message, 'error');
            } finally {
                btn.disabled = false;
                btn.innerHTML = '<span>Ban Bố Chiếu Chỉ</span>';
            }
        });
    }
}

// Modal open/close helpers
function openCreateStudentModal() { document.getElementById('createStudentModal').style.display = 'flex'; }
function closeCreateStudentModal() { document.getElementById('createStudentModal').style.display = 'none'; }
function openCreateTeacherModal() { document.getElementById('createTeacherModal').style.display = 'flex'; }
function closeCreateTeacherModal() { document.getElementById('createTeacherModal').style.display = 'none'; }
function openCreateClassModal() { document.getElementById('createClassModal').style.display = 'flex'; }
function closeCreateClassModal() { document.getElementById('createClassModal').style.display = 'none'; }

function escapeHtml(text) {
    if (!text) return '';
    return String(text).replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;').replace(/"/g, '&quot;');
}
