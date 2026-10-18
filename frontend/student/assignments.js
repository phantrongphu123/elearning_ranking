let allAssignments = [];
let studentSubmissionsMap = new Map(); // assignment_id -> submission object
let currentFilter = 'all';
let currentExamAssignmentId = null;

document.addEventListener('DOMContentLoaded', () => {
    if (!requireAuth(['student'])) return;
    initMobileNav('assignments');
    initAssignments();

    const form = document.getElementById('submissionForm');
    if (form) {
        form.addEventListener('submit', async (e) => {
            e.preventDefault();
            await submitExam();
        });
    }
});

async function initAssignments() {
    await loadSubmissions();
    await loadAssignments();
}

async function loadSubmissions() {
    try {
        const subs = await fetchAPI('/submissions');
        studentSubmissionsMap.clear();
        (subs || []).forEach(s => {
            studentSubmissionsMap.set(String(s.assignment_id), s);
        });
    } catch (e) {
        console.warn('Lỗi tải bài nộp:', e);
    }
}

async function loadAssignments() {
    const container = document.getElementById('assignmentsListContainer');
    if (!container) return;

    try {
        allAssignments = await fetchAPI('/assignments');
        renderAssignments();
    } catch (error) {
        container.innerHTML = `<p class="text-center" style="color: var(--crimson); padding: 3rem;">Lỗi tải bài tập: ${error.message}</p>`;
    }
}

function setAssignmentFilter(filterType, btnEl) {
    currentFilter = filterType;
    document.querySelectorAll('.tab-btn').forEach(b => b.classList.remove('active'));
    if (btnEl) btnEl.classList.add('active');
    renderAssignments();
}

function renderAssignments() {
    const container = document.getElementById('assignmentsListContainer');
    if (!container) return;

    let filtered = allAssignments;
    if (currentFilter === 'pending') {
        filtered = allAssignments.filter(a => !studentSubmissionsMap.has(String(a.assignment_id)));
    } else if (currentFilter === 'submitted') {
        filtered = allAssignments.filter(a => studentSubmissionsMap.has(String(a.assignment_id)));
    }

    if (!filtered || filtered.length === 0) {
        const emptyTexts = {
            all: 'Học viện hiện chưa ban bố tấu chương nào.',
            pending: 'Đại cát! Bạn đã hoàn thành tất cả tấu chương được giao.',
            submitted: 'Bạn chưa dâng trình bài tập nào.'
        };
        container.innerHTML = `
            <div class="glass-panel text-center" style="padding: 3.5rem 1rem;">
                <div style="font-size: 3rem; margin-bottom: 1rem;">📜</div>
                <p style="color: var(--text-muted); font-size: 1rem;">${emptyTexts[currentFilter] || 'Không có bài tập.'}</p>
            </div>
        `;
        return;
    }

    container.innerHTML = filtered.map(a => {
        const sub = studentSubmissionsMap.get(String(a.assignment_id));
        const isSubmitted = !!sub;
        
        let statusBadge = '';
        if (isSubmitted) {
            const scoreText = sub.score !== undefined ? `${sub.score}đ` : 'Đã nộp';
            statusBadge = `<span class="badge badge-success">✓ Đã dâng trình: ${scoreText}</span>`;
        } else {
            statusBadge = a.is_past_deadline
                ? `<span class="badge badge-danger">⚠️ Quá hạn chót</span>`
                : `<span class="badge badge-warning">⏳ Cần hoàn thành</span>`;
        }

        const bonusBadge = a.bonus_score > 0 
            ? `<span class="badge badge-gold">+${a.bonus_score}đ thưởng đúng hạn</span>` 
            : '';

        let actionBtn = '';
        if (isSubmitted) {
            actionBtn = `
                <button class="btn btn-secondary btn-sm" onclick="openSubmissionReview(${sub.submission_id}, '${escapeHtml(a.title)}', ${sub.score})">
                    <span>🔍 Xem Kết Quả & Lời Phê</span>
                </button>
            `;
        } else {
            actionBtn = `
                <button class="btn btn-primary" onclick="openExam(${a.assignment_id}, '${escapeHtml(a.title)}', '${escapeHtml(a.description || '')}', '${escapeHtml(a.subject || 'Tiếng Trung')}')">
                    <span>✍️ Làm Bài Thi</span>
                </button>
            `;
        }

        return `
            <div class="assignment-card">
                <div class="assignment-header">
                    <div>
                        <h3 style="font-size: 1.25rem; display: flex; align-items: center; gap: 0.65rem; flex-wrap: wrap;">
                            ${escapeHtml(a.title)}
                            ${statusBadge}
                            ${bonusBadge}
                        </h3>
                        <div class="assignment-meta">
                            <span>📚 Môn: <strong style="color: var(--gold-light);">${escapeHtml(a.subject || 'Tiếng Trung')}</strong></span>
                            <span>⏰ Hạn nộp: <strong style="color: ${a.is_past_deadline ? 'var(--crimson)' : 'var(--gold-light)'};">${formatDate(a.deadline)}</strong></span>
                            <span>👥 Đã dâng trình: <strong>${a.submission_count || 0}</strong> bài</span>
                        </div>
                    </div>
                    <div>
                        ${actionBtn}
                    </div>
                </div>

                ${a.description ? `<p class="assignment-desc">${escapeHtml(a.description)}</p>` : ''}
            </div>
        `;
    }).join('');
}

// ----------------------------------------------------
// EXAM SOLVER MODAL
// ----------------------------------------------------
async function openExam(assignmentId, title, description, subject) {
    currentExamAssignmentId = assignmentId;

    document.getElementById('modalExamTitle').textContent = title;
    document.getElementById('modalExamSubject').textContent = `Môn học: ${subject}`;
    document.getElementById('modalExamDescription').textContent = description || 'Hãy trả lời tất cả các câu hỏi cẩn thận.';
    
    const container = document.getElementById('questionsContainer');
    container.innerHTML = '<p class="text-center" style="padding: 2rem; color: var(--text-muted)">Đang tải câu hỏi trắc nghiệm tiếng Trung...</p>';
    
    document.getElementById('examModal').style.display = 'flex';
    document.getElementById('submitActionArea').style.display = 'block';

    try {
        const questions = await fetchAPI(`/assignments/${assignmentId}/questions`);
        if (!questions || questions.length === 0) {
            container.innerHTML = '<p class="text-center" style="padding: 2.5rem; color: var(--text-muted)">Bài tập này hiện chưa có câu hỏi nào từ Thái Phó.</p>';
            document.getElementById('submitActionArea').style.display = 'none';
            return;
        }

        container.innerHTML = questions.map((q, idx) => {
            let optionsHtml = '';
            
            if (q.question_type === 'multiple_choice') {
                const opts = [
                    { key: 'a', text: q.option_a },
                    { key: 'b', text: q.option_b },
                    { key: 'c', text: q.option_c },
                    { key: 'd', text: q.option_d }
                ].filter(o => o.text && o.text.trim() !== '');

                optionsHtml = `
                    <div class="options-list">
                        ${opts.map(opt => `
                            <label class="option-item">
                                <input type="radio" name="q_${q.question_id}" value="${opt.key}" required>
                                <span><strong>${opt.key.toUpperCase()}.</strong> ${escapeHtml(opt.text)}</span>
                            </label>
                        `).join('')}
                    </div>
                `;
            } else if (q.question_type === 'true_false') {
                optionsHtml = `
                    <div class="options-list">
                        <label class="option-item">
                            <input type="radio" name="q_${q.question_id}" value="a" required>
                            <span><strong>A.</strong> ${escapeHtml(q.option_a || 'Đúng (正确)')}</span>
                        </label>
                        <label class="option-item">
                            <input type="radio" name="q_${q.question_id}" value="b" required>
                            <span><strong>B.</strong> ${escapeHtml(q.option_b || 'Sai (错误)')}</span>
                        </label>
                    </div>
                `;
            } else {
                // Short answer
                optionsHtml = `
                    <div class="input-group" style="margin-top: 0.75rem;">
                        <input type="text" name="q_${q.question_id}" placeholder="Nhập câu trả lời Hán tự / Pinyin..." required>
                    </div>
                `;
            }

            return `
                <div class="question-card">
                    <div class="question-header">
                        <span style="color: var(--gold-light);">Câu hỏi ${idx + 1}</span>
                        <span class="badge badge-gold">${q.score || 10} điểm</span>
                    </div>
                    <div class="question-text">${escapeHtml(q.question_text)}</div>
                    ${optionsHtml}
                </div>
            `;
        }).join('');

    } catch (e) {
        container.innerHTML = `<p class="text-center" style="color: var(--crimson); padding: 2rem;">Lỗi tải câu hỏi: ${e.message}</p>`;
    }
}

function closeExamModal() {
    const modal = document.getElementById('examModal');
    if (modal) modal.style.display = 'none';
}

async function submitExam() {
    const form = document.getElementById('submissionForm');
    const formData = new FormData(form);
    const answers = {};

    for (let [key, val] of formData.entries()) {
        if (key.startsWith('q_')) {
            const qId = key.replace('q_', '');
            answers[qId] = val.trim();
        }
    }

    const submitBtn = form.querySelector('button[type="submit"]');
    try {
        submitBtn.disabled = true;
        submitBtn.innerHTML = '<span>Đang dâng trình tấu chương...</span>';

        const res = await fetchAPI('/submissions', {
            method: 'POST',
            body: JSON.stringify({
                assignment_id: currentExamAssignmentId,
                answers: answers
            })
        });

        closeExamModal();
        showToast(`🎉 Dâng trình thành công! Điểm: ${res.score} (+${res.points_added}đ tổng)`, 'success');
        
        await loadSubmissions();
        await loadAssignments();
    } catch (err) {
        showToast('Lỗi dâng trình: ' + err.message, 'error');
    } finally {
        submitBtn.disabled = false;
        submitBtn.innerHTML = '<span>✍️ Dâng Trình Tấu Chương (Nộp Bài)</span>';
    }
}

// ----------------------------------------------------
// SUBMISSION REVIEW MODAL
// ----------------------------------------------------
async function openSubmissionReview(submissionId, assignmentTitle, score) {
    const modal = document.getElementById('reviewModal');
    const container = document.getElementById('reviewQuestionsContainer');
    const titleEl = document.getElementById('reviewModalTitle');
    const scoreEl = document.getElementById('reviewModalScore');
    const commentBox = document.getElementById('reviewTeacherCommentBox');
    const commentText = document.getElementById('reviewTeacherCommentText');

    titleEl.textContent = `Kết Quả: ${assignmentTitle}`;
    scoreEl.textContent = `Điểm bài thi: ${score ?? 0} điểm`;
    container.innerHTML = '<p class="text-center" style="padding: 2rem;">Đang tải chi tiết đáp án...</p>';
    if (commentBox) commentBox.style.display = 'none';
    modal.style.display = 'flex';

    try {
        const subData = await fetchAPI(`/submissions/${submissionId}`);
        
        if (subData.teacher_comment && commentBox && commentText) {
            commentText.textContent = subData.teacher_comment;
            commentBox.style.display = 'block';
        }

        const details = subData.details || [];
        if (details.length === 0) {
            container.innerHTML = '<p class="text-center" style="padding: 2rem; color: var(--text-muted)">Không có dữ liệu chi tiết cho bài nộp này.</p>';
            return;
        }

        container.innerHTML = details.map((d, idx) => {
            const isCorrect = d.is_correct === 'True' || d.is_correct === true || String(d.student_answer).toLowerCase() === String(d.correct_answer).toLowerCase();
            const borderClass = isCorrect ? 'review-correct' : 'review-wrong';
            const statusIcon = isCorrect ? '✓ Đúng' : '✕ Sai';
            const badgeClass = isCorrect ? 'badge-success' : 'badge-danger';

            return `
                <div class="question-card ${borderClass}">
                    <div class="question-header">
                        <span>Câu ${idx + 1}</span>
                        <span class="badge ${badgeClass}">${statusIcon} (${d.score || 0}đ)</span>
                    </div>
                    <div class="question-text">${escapeHtml(d.question_text || '')}</div>
                    <div style="font-size: 0.9rem; margin-top: 0.5rem; display: flex; flex-direction: column; gap: 0.35rem;">
                        <div>Đáp án của bạn: <strong style="color: ${isCorrect ? 'var(--jade)' : 'var(--crimson)'};">${escapeHtml(d.student_answer || 'Chưa trả lời')}</strong></div>
                        <div>Đáp án chuẩn triều đình: <strong style="color: var(--gold-light);">${escapeHtml(d.correct_answer || '')}</strong></div>
                    </div>
                </div>
            `;
        }).join('');

    } catch (e) {
        container.innerHTML = `<p class="text-center" style="color: var(--crimson); padding: 2rem;">Lỗi tải bài làm: ${e.message}</p>`;
    }
}

function closeReviewModal() {
    const modal = document.getElementById('reviewModal');
    if (modal) modal.style.display = 'none';
}

function escapeHtml(text) {
    if (!text) return '';
    return String(text)
        .replace(/&/g, '&amp;')
        .replace(/</g, '&lt;')
        .replace(/>/g, '&gt;')
        .replace(/"/g, '&quot;')
        .replace(/'/g, '&#039;');
}
