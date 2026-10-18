document.addEventListener('DOMContentLoaded', () => {
    if (!requireAuth(['teacher'])) return;
    initMobileNav('dashboard');
    loadTeacherDashboard();
    initQuickScoreForm();
});

let teacherClasses = [];

async function loadTeacherDashboard() {
    try {
        const data = await fetchAPI('/dashboard/teacher');
        teacherClasses = data.classes || [];

        // Stats
        document.getElementById('totalClasses').textContent = teacherClasses.length;
        document.getElementById('totalStudents').textContent = data.total_students || 0;
        document.getElementById('activeAssignments').textContent = data.active_assignments || 0;
        document.getElementById('ungradedCount').textContent = data.ungraded_count || 0;

        // Class List
        const container = document.getElementById('classesListContainer');
        if (!container) return;

        if (teacherClasses.length === 0) {
            container.innerHTML = '<p class="text-center" style="color: var(--text-muted); padding: 2rem;">Thái Phó hiện chưa được phân công lớp học nào.</p>';
            return;
        }

        container.innerHTML = teacherClasses.map(cls => `
            <div class="class-card">
                <div>
                    <h4 style="font-size: 1.15rem; margin-bottom: 0.35rem; color: var(--gold-light);">
                        ${escapeHtml(cls.class_name)} (${escapeHtml(cls.class_code)})
                    </h4>
                    <div style="font-size: 0.85rem; color: var(--text-muted);">
                        <span>Niên khóa: ${escapeHtml(cls.school_year || '2026-2027')}</span> · 
                        <span>Trạng thái: <span class="badge ${cls.status === 'active' ? 'badge-success' : 'badge-danger'}">${cls.status === 'active' ? 'Đang hoạt động' : 'Đã khóa'}</span></span>
                    </div>
                </div>

                <div class="quick-actions">
                    <a href="attendance.html?class_id=${cls.class_id}" class="btn btn-secondary btn-sm">
                        <span>Điểm Danh</span>
                    </a>
                    <a href="assignments.html?class_id=${cls.class_id}" class="btn btn-secondary btn-sm">
                        <span>Giao Bài</span>
                    </a>
                    <a href="submissions.html" class="btn btn-primary btn-sm">
                        <span>Chấm Bài</span>
                    </a>
                </div>
            </div>
        `).join('');

    } catch (e) {
        console.error('Lỗi tải dashboard giáo viên:', e);
        showToast('Không thể tải thông tin: ' + e.message, 'error');
    }
}

// ----------------------------------------------------
// QUICK SCORE MODAL (Thưởng / Phạt)
// ----------------------------------------------------
async function openQuickScoreModal() {
    const modal = document.getElementById('quickScoreModal');
    const select = document.getElementById('quickScoreStudentSelect');
    if (!modal || !select) return;

    modal.style.display = 'flex';
    select.innerHTML = '<option value="">Đang tải danh sách học sinh...</option>';

    try {
        const students = await fetchAPI('/students');
        if (!students || students.length === 0) {
            select.innerHTML = '<option value="">Không có học sinh nào</option>';
            return;
        }

        select.innerHTML = '<option value="">-- Chọn học tử triều đình --</option>' + students.map(s => `
            <option value="${s.student_id}">${escapeHtml(s.full_name)} (${s.student_code}) · ${s.rank || 'Học tử'} (${s.total_score}đ)</option>
        `).join('');

        updatePresetReasons();
    } catch (e) {
        select.innerHTML = `<option value="">Lỗi: ${e.message}</option>`;
    }
}

function closeQuickScoreModal() {
    const modal = document.getElementById('quickScoreModal');
    if (modal) modal.style.display = 'none';
}

function updatePresetReasons() {
    const type = document.getElementById('quickScoreType').value;
    const pointsInput = document.getElementById('quickScorePoints');
    const reasonInput = document.getElementById('quickScoreReason');
    const container = document.getElementById('presetReasonsContainer');
    if (!container) return;

    let presets = [];
    if (type === 'bonus') {
        pointsInput.value = 10;
        presets = [
            { text: '+10đ Phát biểu hăng hái', pts: 10, reason: 'Phát biểu hăng hái, xây dựng bài' },
            { text: '+5đ Thuộc từ vựng Hán tự', pts: 5, reason: 'Kiểm tra từ vựng tiếng Trung đạt chuẩn' },
            { text: '+15đ Bài kiểm tra xuất sắc', pts: 15, reason: 'Thành tích vượt trội trong kỳ khảo hạch' },
            { text: '+5đ Giúp đỡ đồng môn', pts: 5, reason: 'Tinh thần tương trợ học tập trong lớp' }
        ];
    } else if (type === 'penalty') {
        pointsInput.value = -5;
        presets = [
            { text: '-5đ Quên vở bài tập', pts: -5, reason: 'Không mang theo tập vở Hán ngữ' },
            { text: '-10đ Mất trật tự trong giờ', pts: -10, reason: 'Gây mất trật tự trong giảng đường' },
            { text: '-5đ Đi muộn không phép', pts: -5, reason: 'Tiến cung muộn giờ học' },
            { text: '-10đ Chưa làm bài tập về nhà', pts: -10, reason: 'Không hoàn thành tấu chương được giao' }
        ];
    } else {
        presets = [];
    }

    container.innerHTML = presets.map(p => `
        <button type="button" class="btn btn-secondary btn-sm" onclick="applyPreset(${p.pts}, '${escapeHtml(p.reason)}')">
            <span>${p.text}</span>
        </button>
    `).join('');
}

function applyPreset(pts, reason) {
    document.getElementById('quickScorePoints').value = pts;
    document.getElementById('quickScoreReason').value = reason;
}

function initQuickScoreForm() {
    const form = document.getElementById('quickScoreForm');
    if (!form) return;

    form.addEventListener('submit', async (e) => {
        e.preventDefault();
        const studentId = document.getElementById('quickScoreStudentSelect').value;
        const type = document.getElementById('quickScoreType').value;
        const points = parseFloat(document.getElementById('quickScorePoints').value);
        const reason = document.getElementById('quickScoreReason').value.trim();

        if (!studentId) {
            showToast('Vui lòng chọn học sinh!', 'error');
            return;
        }

        const submitBtn = form.querySelector('button[type="submit"]');
        try {
            submitBtn.disabled = true;
            submitBtn.innerHTML = '<span>Đang ban bố quyết định...</span>';

            await fetchAPI('/scores', {
                method: 'POST',
                body: JSON.stringify({
                    student_id: parseInt(studentId),
                    points: points,
                    reason: reason,
                    score_type: type
                })
            });

            closeQuickScoreModal();
            showToast(`⭐ Đã cập nhật điểm thành công (${points >= 0 ? '+' : ''}${points}đ)!`, 'success');
            loadTeacherDashboard();
        } catch (err) {
            showToast('Lỗi ban chiếu: ' + err.message, 'error');
        } finally {
            submitBtn.disabled = false;
            submitBtn.innerHTML = '<span>Xác Nhận Ban Chiếu</span>';
        }
    });
}

function escapeHtml(text) {
    if (!text) return '';
    return String(text).replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;').replace(/"/g, '&quot;');
}
