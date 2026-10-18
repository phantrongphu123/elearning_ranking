let currentStudents = [];

document.addEventListener('DOMContentLoaded', async () => {
    if (!requireAuth(['teacher'])) return;
    initMobileNav('attendance');

    const dateInput = document.getElementById('dateSelect');
    if (dateInput) {
        dateInput.value = new Date().toISOString().split('T')[0];
    }

    await loadTeacherClassesForAttendance();
    initAttendanceForm();

    // Check if class_id is passed in URL query
    const params = new URLSearchParams(window.location.search);
    const paramClassId = params.get('class_id');
    if (paramClassId) {
        const select = document.getElementById('classSelect');
        if (select) {
            select.value = paramClassId;
            loadClassStudents();
        }
    }
});

async function loadTeacherClassesForAttendance() {
    try {
        const classes = await fetchAPI('/classes');
        const select = document.getElementById('classSelect');
        if (select && classes) {
            select.innerHTML = '<option value="">-- Chọn lớp học điểm danh --</option>';
            classes.forEach(c => {
                const opt = document.createElement('option');
                opt.value = c.class_id;
                opt.textContent = `${c.class_name} (${c.class_code})`;
                select.appendChild(opt);
            });
            if (classes.length > 0 && !select.value) {
                select.value = classes[0].class_id;
            }
        }
    } catch (e) {
        console.warn('Lỗi tải danh sách lớp:', e);
    }
}

async function loadClassStudents() {
    const classId = document.getElementById('classSelect').value;
    const dateStr = document.getElementById('dateSelect').value;

    if (!classId) {
        showToast('Vui lòng chọn lớp học!', 'error');
        return;
    }

    const rosterPanel = document.getElementById('rosterPanel');
    const tbody = document.getElementById('rosterTableBody');

    try {
        // Load students of this class
        currentStudents = await fetchAPI(`/students?class_id=${classId}`);

        if (!currentStudents || currentStudents.length === 0) {
            tbody.innerHTML = '<tr><td colspan="5" class="text-center" style="padding: 2.5rem; color: var(--text-muted)">Lớp này chưa có học tử nào.</td></tr>';
            rosterPanel.style.display = 'block';
            return;
        }

        // Try to load any existing attendance for this class & date
        let existingMap = new Map();
        try {
            const existing = await fetchAPI(`/attendance?class_id=${classId}&date=${dateStr}`);
            (existing || []).forEach(r => existingMap.set(String(r.student_id), r));
        } catch (e) {
            console.warn('Không tải được lịch sử điểm danh ngày này:', e);
        }

        tbody.innerHTML = currentStudents.map(s => {
            const saved = existingMap.get(String(s.student_id));
            const currentStatus = saved ? saved.status : 'present';
            const savedNote = saved ? (saved.note || '') : '';

            return `
                <tr>
                    <td style="font-size: 0.85rem; color: var(--text-muted); font-family: monospace;">${escapeHtml(s.student_code)}</td>
                    <td>
                        <strong style="color: var(--gold-light); font-size: 0.95rem;">${escapeHtml(s.full_name)}</strong>
                    </td>
                    <td>
                        <span class="rank-badge sm">${escapeHtml(s.rank || 'Học sinh')}</span>
                    </td>
                    <td>
                        <div class="attendance-status-radios">
                            <label class="status-radio-label status-present">
                                <input type="radio" name="status_${s.student_id}" value="present" ${currentStatus === 'present' ? 'checked' : ''}>
                                <span>Có mặt (+5đ)</span>
                            </label>
                            <label class="status-radio-label status-late">
                                <input type="radio" name="status_${s.student_id}" value="late" ${currentStatus === 'late' ? 'checked' : ''}>
                                <span>Đi trễ (+2đ)</span>
                            </label>
                            <label class="status-radio-label status-excused">
                                <input type="radio" name="status_${s.student_id}" value="absent_excused" ${currentStatus === 'absent_excused' ? 'checked' : ''}>
                                <span>Có phép (0đ)</span>
                            </label>
                            <label class="status-radio-label status-unexcused">
                                <input type="radio" name="status_${s.student_id}" value="absent_unexcused" ${currentStatus === 'absent_unexcused' ? 'checked' : ''}>
                                <span>Không phép (-10đ)</span>
                            </label>
                        </div>
                    </td>
                    <td>
                        <input type="text" name="note_${s.student_id}" value="${escapeHtml(savedNote)}" placeholder="Ghi chú (nếu có)..." style="font-size: 0.85rem; padding: 0.45rem 0.75rem;">
                    </td>
                </tr>
            `;
        }).join('');

        rosterPanel.style.display = 'block';

        if (existingMap.size > 0) {
            showToast(`ℹ️ Đã nạp dữ liệu điểm danh đã lưu ngày ${formatDate(dateStr, false)}`, 'info');
        }

    } catch (e) {
        showToast('Lỗi tải danh sách học sinh: ' + e.message, 'error');
    }
}

function markAllPresent() {
    if (!currentStudents || currentStudents.length === 0) {
        showToast('Vui lòng tải danh sách học sinh trước!', 'error');
        return;
    }

    currentStudents.forEach(s => {
        const radios = document.getElementsByName(`status_${s.student_id}`);
        for (let r of radios) {
            if (r.value === 'present') r.checked = true;
        }
    });

    showToast('Đã chọn "Có mặt (+5đ)" cho tất cả học sinh!', 'success');
}

function initAttendanceForm() {
    const form = document.getElementById('attendanceForm');
    if (!form) return;

    form.addEventListener('submit', async (e) => {
        e.preventDefault();

        const classId = document.getElementById('classSelect').value;
        const dateStr = document.getElementById('dateSelect').value;

        if (!classId || !dateStr) {
            showToast('Vui lòng chọn lớp và ngày!', 'error');
            return;
        }

        const formData = new FormData(form);
        const records = [];

        currentStudents.forEach(s => {
            const status = formData.get(`status_${s.student_id}`) || 'present';
            const note = formData.get(`note_${s.student_id}`) || '';
            records.push({
                student_id: parseInt(s.student_id),
                status: status,
                note: note.trim()
            });
        });

        const submitBtn = form.querySelector('button[type="submit"]');
        try {
            submitBtn.disabled = true;
            submitBtn.innerHTML = '<span>Đang ghi sổ điểm danh...</span>';

            await fetchAPI('/attendance', {
                method: 'POST',
                body: JSON.stringify({
                    class_id: parseInt(classId),
                    date: dateStr,
                    records: records
                })
            });

            showToast(`Đã lưu điểm danh ngày ${formatDate(dateStr, false)} thành công! Điểm đã được cập nhật.`, 'success');
        } catch (err) {
            showToast('Lỗi lưu điểm danh: ' + err.message, 'error');
        } finally {
            submitBtn.disabled = false;
            submitBtn.innerHTML = '<span>Lưu Điểm Danh & Cập Nhật Điểm</span>';
        }
    });
}

function escapeHtml(text) {
    if (!text) return '';
    return String(text).replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;').replace(/"/g, '&quot;');
}
