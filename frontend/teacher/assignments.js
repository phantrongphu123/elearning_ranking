let currentManagingAssignmentId = null;
let teacherClassesMap = new Map();

document.addEventListener('DOMContentLoaded', async () => {
    if (!requireAuth(['teacher'])) return;
    initMobileNav('assignments');
    await loadTeacherClasses();
    await loadTeacherAssignments();
    initForms();
});

async function loadTeacherClasses() {
    try {
        const classes = await fetchAPI('/classes');
        const select = document.getElementById('createClassSelect');
        teacherClassesMap.clear();

        if (classes && select) {
            select.innerHTML = '<option value="">-- Chọn lớp học tiếp nhận --</option>';
            classes.forEach(c => {
                teacherClassesMap.set(String(c.class_id), c.class_name);
                const opt = document.createElement('option');
                opt.value = c.class_id;
                opt.textContent = `${c.class_name} (${c.class_code})`;
                select.appendChild(opt);
            });
        }
    } catch (e) {
        console.warn('Lỗi tải lớp:', e);
    }
}

async function loadTeacherAssignments() {
    const tbody = document.getElementById('assignmentsTableBody');
    if (!tbody) return;

    try {
        const assignments = await fetchAPI('/assignments');
        if (!assignments || assignments.length === 0) {
            tbody.innerHTML = '<tr><td colspan="6" class="text-center" style="padding: 2.5rem; color: var(--text-muted)">Thái Phó chưa ban bố tấu chương nào. Hãy nhấn "+ Ban Bố Tấu Chương Mới".</td></tr>';
            return;
        }

        tbody.innerHTML = assignments.map(a => {
            const className = teacherClassesMap.get(String(a.class_id)) || `Lớp #${a.class_id}`;
            const deadlineText = formatDate(a.deadline);
            const isPast = a.is_past_deadline;

            return `
                <tr>
                    <td>
                        <strong style="color: var(--gold-light); font-size: 0.95rem;">${escapeHtml(a.title)}</strong>
                        ${a.bonus_score > 0 ? `<span class="badge badge-gold" style="margin-left: 0.35rem;">+${a.bonus_score}đ thưởng</span>` : ''}
                    </td>
                    <td>${escapeHtml(a.subject || 'Tiếng Trung')}</td>
                    <td><span class="badge badge-info">${escapeHtml(className)}</span></td>
                    <td>
                        <span style="color: ${isPast ? 'var(--crimson)' : 'inherit'}; font-weight: ${isPast ? '600' : '400'};">
                            ${deadlineText} ${isPast ? '(Hết hạn)' : ''}
                        </span>
                    </td>
                    <td style="font-weight: 600; color: var(--gold-primary); text-align: center;">
                        ${a.submission_count || 0} bài
                    </td>
                    <td>
                        <div class="d-flex gap-1" style="align-items: center;">
                            <button class="btn btn-secondary btn-sm" onclick="openManageQuestions(${a.assignment_id}, '${escapeHtml(a.title)}')">
                                <span>Câu Hỏi</span>
                            </button>
                            <button class="btn btn-danger btn-sm" onclick="deleteAssignment(${a.assignment_id})">
                                <span>Thu Hồi</span>
                            </button>
                        </div>
                    </td>
                </tr>
            `;
        }).join('');

    } catch (error) {
        tbody.innerHTML = `<tr><td colspan="6" class="text-center" style="color: var(--crimson);">Lỗi tải tấu chương: ${error.message}</td></tr>`;
    }
}

function initForms() {
    // Create Assignment Form
    const createForm = document.getElementById('createAssignmentForm');
    if (createForm) {
        // Set default deadline to 7 days from now
        const now = new Date();
        now.setDate(now.getDate() + 7);
        const deadlineInput = document.getElementById('createDeadline');
        if (deadlineInput) {
            deadlineInput.value = now.toISOString().slice(0, 16);
        }

        createForm.addEventListener('submit', async (e) => {
            e.preventDefault();
            const title = document.getElementById('createTitle').value.trim();
            const subject = document.getElementById('createSubject').value.trim();
            const classId = document.getElementById('createClassSelect').value;
            const deadline = document.getElementById('createDeadline').value;
            const bonus = parseFloat(document.getElementById('createBonus').value || 0);
            const desc = document.getElementById('createDesc').value.trim();

            if (!title || !classId || !deadline) {
                showToast('Vui lòng điền đủ các thông tin bắt buộc!', 'error');
                return;
            }

            const submitBtn = createForm.querySelector('button[type="submit"]');
            try {
                submitBtn.disabled = true;
                submitBtn.innerHTML = '<span>Đang ban bố bài tập...</span>';

                const res = await fetchAPI('/assignments', {
                    method: 'POST',
                    body: JSON.stringify({
                        title: title,
                        subject: subject || 'Tiếng Trung',
                        class_id: parseInt(classId),
                        deadline: new Date(deadline).toISOString(),
                        bonus_score: bonus,
                        penalty_score: 0,
                        description: desc,
                        questions: []
                    })
                });

                closeCreateAssignmentModal();
                showToast('Tạo bài tập thành công!', 'success');
                await loadTeacherAssignments();

                // Open Question Builder immediately for this assignment!
                if (res.assignment_id) {
                    openManageQuestions(res.assignment_id, title);
                }
            } catch (err) {
                showToast('Lỗi ban bố bài tập: ' + err.message, 'error');
            } finally {
                submitBtn.disabled = false;
                submitBtn.innerHTML = '<span>Ban Bố Bài Tập (Bước 1)</span>';
            }
        });
    }

    // Add Question Form
    const addQForm = document.getElementById('addQuestionForm');
    if (addQForm) {
        addQForm.addEventListener('submit', async (e) => {
            e.preventDefault();
            if (!currentManagingAssignmentId) return;

            const qType = document.getElementById('qTypeSelect').value;
            const qScore = parseFloat(document.getElementById('qScore').value || 10);
            const qText = document.getElementById('qText').value.trim();
            const qCorrect = document.getElementById('qCorrectAnswer').value.trim().toLowerCase();

            const optA = document.getElementById('qOptA').value.trim();
            const optB = document.getElementById('qOptB').value.trim();
            const optC = document.getElementById('qOptC').value.trim();
            const optD = document.getElementById('qOptD').value.trim();

            const submitBtn = addQForm.querySelector('button[type="submit"]');
            try {
                submitBtn.disabled = true;
                submitBtn.innerHTML = '<span>Đang lưu câu hỏi...</span>';

                await fetchAPI(`/assignments/${currentManagingAssignmentId}/questions`, {
                    method: 'POST',
                    body: JSON.stringify({
                        question_type: qType,
                        question_text: qText,
                        score: qScore,
                        correct_answer: qCorrect,
                        option_a: optA,
                        option_b: optB,
                        option_c: optC,
                        option_d: optD
                    })
                });

                showToast('Đã thêm câu hỏi thành công!', 'success');
                document.getElementById('qText').value = '';
                document.getElementById('qOptA').value = '';
                document.getElementById('qOptB').value = '';
                document.getElementById('qOptC').value = '';
                document.getElementById('qOptD').value = '';
                document.getElementById('qCorrectAnswer').value = '';

                await loadQuestionsForAssignment(currentManagingAssignmentId);
            } catch (err) {
                showToast('Lỗi thêm câu hỏi: ' + err.message, 'error');
            } finally {
                submitBtn.disabled = false;
                submitBtn.innerHTML = '<span>+ Thêm Câu Hỏi Vào Tấu Chương</span>';
            }
        });
    }
}

// ----------------------------------------------------
// CREATE MODAL
// ----------------------------------------------------
function openCreateAssignmentModal() {
    document.getElementById('createAssignmentModal').style.display = 'flex';
}

function closeCreateAssignmentModal() {
    document.getElementById('createAssignmentModal').style.display = 'none';
}

// ----------------------------------------------------
// MANAGE QUESTIONS MODAL
// ----------------------------------------------------
async function openManageQuestions(assignmentId, title) {
    currentManagingAssignmentId = assignmentId;
    document.getElementById('mqModalSubtitle').textContent = `Tấu chương: ${title}`;
    document.getElementById('manageQuestionsModal').style.display = 'flex';
    await loadQuestionsForAssignment(assignmentId);
}

function closeManageQuestionsModal() {
    document.getElementById('manageQuestionsModal').style.display = 'none';
    currentManagingAssignmentId = null;
    loadTeacherAssignments();
}

async function loadQuestionsForAssignment(assignmentId) {
    const container = document.getElementById('questionsListContainer');
    if (!container) return;

    container.innerHTML = '<p class="text-center" style="padding: 1rem; color: var(--text-muted)">Đang tải câu hỏi...</p>';

    try {
        const questions = await fetchAPI(`/assignments/${assignmentId}/questions`);
        if (!questions || questions.length === 0) {
            container.innerHTML = '<p class="text-center" style="padding: 1.5rem; color: var(--text-muted)">Chưa có câu hỏi nào. Hãy thêm câu hỏi bên dưới.</p>';
            return;
        }

        container.innerHTML = questions.map((q, idx) => `
            <div class="question-item">
                <div style="flex: 1;">
                    <div style="font-weight: 600; color: var(--gold-light); margin-bottom: 0.25rem;">
                        Câu ${idx + 1}: ${escapeHtml(q.question_text)}
                    </div>
                    <div style="font-size: 0.85rem; color: var(--text-muted); margin-bottom: 0.35rem;">
                        <span>Dạng: <strong>${q.question_type}</strong></span> · 
                        <span>Điểm: <strong>${q.score}đ</strong></span> · 
                        <span>Đáp án chuẩn: <strong style="color: var(--jade);">${escapeHtml(q.correct_answer)}</strong></span>
                    </div>
                    ${q.question_type === 'multiple_choice' ? `
                        <div style="font-size: 0.82rem; color: var(--text-secondary); display: grid; grid-template-columns: 1fr 1fr; gap: 0.25rem;">
                            <span>A: ${escapeHtml(q.option_a || '—')}</span>
                            <span>B: ${escapeHtml(q.option_b || '—')}</span>
                            <span>C: ${escapeHtml(q.option_c || '—')}</span>
                            <span>D: ${escapeHtml(q.option_d || '—')}</span>
                        </div>
                    ` : ''}
                </div>
                <button class="btn btn-danger btn-sm" onclick="deleteQuestion(${q.question_id})">
                    <span>Xóa</span>
                </button>
            </div>
        `).join('');

    } catch (e) {
        container.innerHTML = `<p class="text-center" style="color: var(--crimson);">Lỗi: ${e.message}</p>`;
    }
}

async function deleteQuestion(questionId) {
    if (!confirm('Bạn có chắc chắn muốn xóa câu hỏi này khỏi đề thi?')) return;
    try {
        await fetchAPI(`/assignments/questions/${questionId}`, { method: 'DELETE' });
        showToast('Đã xóa câu hỏi!', 'success');
        if (currentManagingAssignmentId) {
            await loadQuestionsForAssignment(currentManagingAssignmentId);
        }
    } catch (e) {
        showToast('Lỗi xóa câu hỏi: ' + e.message, 'error');
    }
}

function toggleQuestionOptionsUI() {
    const type = document.getElementById('qTypeSelect').value;
    const optionsUI = document.getElementById('optionsUI');
    const correctInput = document.getElementById('qCorrectAnswer');

    if (type === 'multiple_choice') {
        optionsUI.style.display = 'block';
        correctInput.placeholder = "Nhập 'a', 'b', 'c', hoặc 'd'";
    } else if (type === 'true_false') {
        optionsUI.style.display = 'none';
        correctInput.placeholder = "Nhập 'a' cho Đúng (正确), 'b' cho Sai (错误)";
    } else {
        optionsUI.style.display = 'none';
        correctInput.placeholder = "Nhập đáp án chuẩn xác";
    }
}

async function deleteAssignment(assignmentId) {
    if (!confirm('CẢNH BÁO: Thu hồi bài tập sẽ ẩn bài này khỏi học sinh. Bạn có chắc chắn muốn thu hồi?')) return;
    try {
        await fetchAPI(`/assignments/${assignmentId}`, { method: 'DELETE' });
        showToast('Đã thu hồi bài tập thành công!', 'success');
        await loadTeacherAssignments();
    } catch (e) {
        showToast('Lỗi thu hồi: ' + e.message, 'error');
    }
}

function escapeHtml(text) {
    if (!text) return '';
    return String(text).replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;').replace(/"/g, '&quot;');
}
