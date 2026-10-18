let currentStudents = [];

document.addEventListener('DOMContentLoaded', async () => {
    if (!requireAuth(['teacher'])) return;
    initMobileNav('attendance');

    const dateInput = document.getElementById('dateSelect');
    if (dateInput) {
        dateInput.value = new Date().toISOString().split('T')[0];
        dateInput.addEventListener('change', () => {
            const classSelect = document.getElementById('classSelect');
            if (classSelect && classSelect.value) {
                loadClassStudents();
            }
        });
    }

    const classSelect = document.getElementById('classSelect');
    if (classSelect) {
        classSelect.addEventListener('change', () => {
            if (classSelect.value) {
                loadClassStudents();
            }
        });
    }

    await loadTeacherClassesForAttendance();
    initAttendanceForm();

    // Check if class_id is passed in URL query
    const params = new URLSearchParams(window.location.search);
    const paramClassId = params.get('class_id');
    if (paramClassId && classSelect) {
        classSelect.value = paramClassId;
    }

    // Automatically load students if a class is selected
    if (classSelect && classSelect.value) {
        loadClassStudents();
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
        tbody.innerHTML = '<tr><td colspan="6" class="text-center" style="padding: 2.5rem; color: var(--text-muted)">Đang nạp danh sách học tử...</td></tr>';
        rosterPanel.style.display = 'block';

        // Load students of this class
        currentStudents = await fetchAPI(`/students?class_id=${classId}`);

        if (!currentStudents || currentStudents.length === 0) {
            tbody.innerHTML = '<tr><td colspan="6" class="text-center" style="padding: 2.5rem; color: var(--text-muted)">Lớp này chưa có học tử nào.</td></tr>';
            rosterPanel.style.display = 'block';
            updateAttendanceSummary();
            return;
        }

        // Load any existing absent/late records for this class & date
        let existingMap = new Map();
        try {
            const existing = await fetchAPI(`/attendance?class_id=${classId}&date=${dateStr}`);
            (existing || []).forEach(r => existingMap.set(String(r.student_id), r));
        } catch (e) {
            console.warn('Không tải được lịch sử điểm danh ngày này:', e);
        }

        tbody.innerHTML = currentStudents.map(s => {
            const saved = existingMap.get(String(s.student_id));
            const isAbsent = !!(saved && saved.status && saved.status !== 'present');
            const absenceType = isAbsent ? saved.status : 'absent_unexcused';
            const savedNote = isAbsent ? (saved.note || '') : '';

            return `
                <tr id="row_${s.student_id}" class="${isAbsent ? 'row-absent' : ''}">
                    <td style="font-size: 0.85rem; color: var(--text-muted); font-family: monospace;">${escapeHtml(s.student_code)}</td>
                    <td>
                        <strong style="color: var(--gold-light); font-size: 0.95rem;">${escapeHtml(s.full_name)}</strong>
                    </td>
                    <td>
                        <span class="rank-badge sm">${escapeHtml(s.rank || 'Học sinh')}</span>
                    </td>
                    <td>
                        <label class="absent-toggle-box ${isAbsent ? 'is-absent' : ''}" id="toggle_box_${s.student_id}">
                            <input type="checkbox" id="check_absent_${s.student_id}" ${isAbsent ? 'checked' : ''} onchange="onAbsentToggle(${s.student_id})">
                            <span id="label_absent_${s.student_id}">${isAbsent ? 'Vắng mặt' : 'Có mặt'}</span>
                        </label>
                    </td>
                    <td>
                        <select class="absence-type-select" id="type_${s.student_id}" ${isAbsent ? '' : 'disabled'} onchange="updateAttendanceSummary()">
                            <option value="absent_unexcused" ${absenceType === 'absent_unexcused' ? 'selected' : ''}>Vắng không phép (-10đ)</option>
                            <option value="absent_excused" ${absenceType === 'absent_excused' ? 'selected' : ''}>Vắng có phép (0đ)</option>
                            <option value="late" ${absenceType === 'late' ? 'selected' : ''}>Đi học muộn (+2đ)</option>
                        </select>
                    </td>
                    <td>
                        <input type="text" class="absence-note-input" id="note_${s.student_id}" value="${escapeHtml(savedNote)}" placeholder="Lý do (nếu vắng)..." ${isAbsent ? '' : 'disabled'}>
                    </td>
                </tr>
            `;
        }).join('');

        rosterPanel.style.display = 'block';
        updateAttendanceSummary();

        if (existingMap.size > 0) {
            showToast(`Đã nạp dữ liệu ngày ${formatDate(dateStr, false)}: Có ${existingMap.size} học sinh ghi nhận vắng/trễ`, 'info');
        }

    } catch (e) {
        showToast('Lỗi tải danh sách học sinh: ' + e.message, 'error');
    }
}

function onAbsentToggle(studentId) {
    const chk = document.getElementById(`check_absent_${studentId}`);
    const row = document.getElementById(`row_${studentId}`);
    const toggleBox = document.getElementById(`toggle_box_${studentId}`);
    const label = document.getElementById(`label_absent_${studentId}`);
    const typeSelect = document.getElementById(`type_${studentId}`);
    const noteInput = document.getElementById(`note_${studentId}`);

    if (!chk) return;

    if (chk.checked) {
        if (row) row.classList.add('row-absent');
        if (toggleBox) toggleBox.classList.add('is-absent');
        if (label) label.textContent = 'Vắng mặt';
        if (typeSelect) typeSelect.disabled = false;
        if (noteInput) {
            noteInput.disabled = false;
            noteInput.focus();
        }
    } else {
        if (row) row.classList.remove('row-absent');
        if (toggleBox) toggleBox.classList.remove('is-absent');
        if (label) label.textContent = 'Có mặt';
        if (typeSelect) typeSelect.disabled = true;
        if (noteInput) noteInput.disabled = true;
    }

    updateAttendanceSummary();
}

function updateAttendanceSummary() {
    const totalCount = currentStudents.length;
    let absentCount = 0;

    currentStudents.forEach(s => {
        const chk = document.getElementById(`check_absent_${s.student_id}`);
        if (chk && chk.checked) {
            absentCount++;
        }
    });

    const presentCount = Math.max(0, totalCount - absentCount);

    const totalEl = document.getElementById('statTotalCount');
    const presentEl = document.getElementById('statPresentCount');
    const absentEl = document.getElementById('statAbsentCount');
    const submitBtn = document.getElementById('submitAttendanceBtn');

    if (totalEl) totalEl.textContent = totalCount;
    if (presentEl) presentEl.textContent = presentCount;
    if (absentEl) absentEl.textContent = absentCount;

    if (submitBtn) {
        if (absentCount === 0) {
            submitBtn.innerHTML = '<span>Lưu Điểm Danh (Cả lớp có mặt)</span>';
        } else {
            submitBtn.innerHTML = `<span>Lưu Điểm Danh (${absentCount} học sinh vắng/trễ)</span>`;
        }
    }
}

function markAllPresent() {
    if (!currentStudents || currentStudents.length === 0) {
        showToast('Vui lòng tải danh sách học sinh trước!', 'error');
        return;
    }

    currentStudents.forEach(s => {
        const chk = document.getElementById(`check_absent_${s.student_id}`);
        const row = document.getElementById(`row_${s.student_id}`);
        const toggleBox = document.getElementById(`toggle_box_${s.student_id}`);
        const label = document.getElementById(`label_absent_${s.student_id}`);
        const typeSelect = document.getElementById(`type_${s.student_id}`);
        const noteInput = document.getElementById(`note_${s.student_id}`);

        if (chk) chk.checked = false;
        if (row) row.classList.remove('row-absent');
        if (toggleBox) toggleBox.classList.remove('is-absent');
        if (label) label.textContent = 'Có mặt';
        if (typeSelect) typeSelect.disabled = true;
        if (noteInput) noteInput.disabled = true;
    });

    updateAttendanceSummary();
    showToast('Đã đặt toàn bộ học sinh là Có mặt!', 'success');
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

        // Only collect records for students marked absent or late
        const absentRecords = [];

        currentStudents.forEach(s => {
            const chk = document.getElementById(`check_absent_${s.student_id}`);
            if (chk && chk.checked) {
                const typeSelect = document.getElementById(`type_${s.student_id}`);
                const noteInput = document.getElementById(`note_${s.student_id}`);
                absentRecords.push({
                    student_id: parseInt(s.student_id),
                    status: typeSelect ? typeSelect.value : 'absent_unexcused',
                    note: noteInput ? noteInput.value.trim() : ''
                });
            }
        });

        const submitBtn = document.getElementById('submitAttendanceBtn');
        try {
            submitBtn.disabled = true;
            submitBtn.innerHTML = '<span>Đang ghi sổ điểm danh...</span>';

            const res = await fetchAPI('/attendance', {
                method: 'POST',
                body: JSON.stringify({
                    class_id: parseInt(classId),
                    date: dateStr,
                    records: absentRecords
                })
            });

            showToast(res.message || 'Lưu điểm danh thành công!', 'success');
            updateAttendanceSummary();
        } catch (err) {
            showToast('Lỗi lưu điểm danh: ' + err.message, 'error');
        } finally {
            submitBtn.disabled = false;
            updateAttendanceSummary();
        }
    });
}

function escapeHtml(text) {
    if (!text) return '';
    return String(text).replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;').replace(/"/g, '&quot;');
}
