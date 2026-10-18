let allSubmissions = [];
let currentFilter = 'all';
let currentSubmittingSubId = null;

document.addEventListener('DOMContentLoaded', () => {
    if (!requireAuth(['teacher'])) return;
    initMobileNav('submissions');
    loadTeacherSubmissions();
    initGradeForm();
});

async function loadTeacherSubmissions() {
    const tbody = document.getElementById('subsTableBody');
    if (!tbody) return;

    try {
        allSubmissions = await fetchAPI('/submissions');
        filterSubmissions();
    } catch (e) {
        tbody.innerHTML = `<tr><td colspan="7" class="text-center" style="color: var(--crimson);">Lỗi tải bài nộp: ${e.message}</td></tr>`;
    }
}

function setSubFilter(filterType, btnEl) {
    currentFilter = filterType;
    document.querySelectorAll('.tabs-nav .tab-btn').forEach(b => b.classList.remove('active'));
    if (btnEl) btnEl.classList.add('active');
    filterSubmissions();
}

function filterSubmissions() {
    const tbody = document.getElementById('subsTableBody');
    if (!tbody) return;

    const searchTerm = (document.getElementById('subSearchInput')?.value || '').toLowerCase();

    let filtered = allSubmissions;

    if (currentFilter === 'pending') {
        filtered = filtered.filter(s => s.status !== 'graded');
    } else if (currentFilter === 'graded') {
        filtered = filtered.filter(s => s.status === 'graded');
    }

    if (searchTerm) {
        filtered = filtered.filter(s => 
            (s.student_name && s.student_name.toLowerCase().includes(searchTerm)) ||
            (s.assignment_title && s.assignment_title.toLowerCase().includes(searchTerm))
        );
    }

    if (filtered.length === 0) {
        tbody.innerHTML = '<tr><td colspan="7" class="text-center" style="padding: 2.5rem; color: var(--text-muted)">Không tìm thấy bài nộp nào phù hợp.</td></tr>';
        return;
    }

    tbody.innerHTML = filtered.map(s => {
        const isLate = s.is_late === 'True' || s.is_late === true;
        const isGraded = s.status === 'graded';

        const lateBadge = isLate
            ? `<span class="badge badge-danger">Trễ hạn</span>`
            : `<span class="badge badge-success">Đúng hạn</span>`;

        const statusBadge = isGraded
            ? `<span class="badge badge-success">✓ Đã phê duyệt</span>`
            : `<span class="badge badge-warning">⏳ Chờ xử lý</span>`;

        return `
            <tr>
                <td><strong>${escapeHtml(s.assignment_title || 'Tấu chương')}</strong></td>
                <td><strong style="color: var(--gold-light);">${escapeHtml(s.student_name || 'Học tử')}</strong></td>
                <td style="font-size: 0.85rem; color: var(--text-muted);">${formatDate(s.submitted_at)}</td>
                <td>${lateBadge}</td>
                <td style="font-family: 'Cinzel', serif; font-weight: 700; color: var(--gold-light); font-size: 1.05rem;">
                    ${s.score ?? 0}đ
                </td>
                <td>${statusBadge}</td>
                <td>
                    <button class="btn btn-primary btn-sm" onclick="openGradeModal(${s.submission_id}, '${escapeHtml(s.student_name)}', '${escapeHtml(s.assignment_title)}', ${s.score}, '${escapeHtml(s.teacher_comment || '')}')">
                        <span>✍️ Phê Duyệt</span>
                    </button>
                </td>
            </tr>
        `;
    }).join('');
}

// ----------------------------------------------------
// GRADE MODAL
// ----------------------------------------------------
async function openGradeModal(submissionId, studentName, assignmentTitle, currentScore, currentComment) {
    currentSubmittingSubId = submissionId;

    document.getElementById('gradeModalTitle').textContent = `Phê Duyệt: ${assignmentTitle}`;
    document.getElementById('gradeModalSubtitle').textContent = `Học tử: ${studentName}`;
    document.getElementById('gradeScore').value = currentScore ?? 0;
    document.getElementById('gradeComment').value = currentComment || '';

    const container = document.getElementById('gradeQuestionsContainer');
    container.innerHTML = '<p class="text-center" style="padding: 1rem; color: var(--text-muted)">Đang tải chi tiết câu trả lời của học tử...</p>';

    document.getElementById('gradeModal').style.display = 'flex';

    try {
        const subData = await fetchAPI(`/submissions/${submissionId}`);
        const details = subData.details || [];

        if (details.length === 0) {
            container.innerHTML = '<p class="text-center" style="padding: 1.5rem; color: var(--text-muted)">Không có chi tiết từng câu hỏi cho bài này.</p>';
            return;
        }

        container.innerHTML = details.map((d, idx) => {
            const isCorrect = d.is_correct === 'True' || d.is_correct === true || String(d.student_answer).toLowerCase() === String(d.correct_answer).toLowerCase();

            return `
                <div class="review-q-card ${isCorrect ? 'correct' : 'wrong'}">
                    <div class="d-flex justify-between align-center mb-1">
                        <strong style="color: var(--gold-light);">Câu ${idx + 1}: ${escapeHtml(d.question_text || '')}</strong>
                        <span class="badge ${isCorrect ? 'badge-success' : 'badge-danger'}">
                            ${isCorrect ? '✓ Đúng' : '✕ Sai'} (${d.score || 0}đ)
                        </span>
                    </div>
                    <div style="font-size: 0.88rem; display: flex; flex-direction: column; gap: 0.25rem;">
                        <div>Học tử chọn: <strong style="color: ${isCorrect ? 'var(--jade)' : 'var(--crimson)'};">${escapeHtml(d.student_answer || 'Không trả lời')}</strong></div>
                        <div>Đáp án chuẩn: <strong style="color: var(--gold-light);">${escapeHtml(d.correct_answer || '')}</strong></div>
                    </div>
                </div>
            `;
        }).join('');

    } catch (e) {
        container.innerHTML = `<p class="text-center" style="color: var(--crimson);">Lỗi: ${e.message}</p>`;
    }
}

function closeGradeModal() {
    document.getElementById('gradeModal').style.display = 'none';
    currentSubmittingSubId = null;
}

function initGradeForm() {
    const form = document.getElementById('gradeForm');
    if (!form) return;

    form.addEventListener('submit', async (e) => {
        e.preventDefault();
        if (!currentSubmittingSubId) return;

        const score = parseFloat(document.getElementById('gradeScore').value);
        const comment = document.getElementById('gradeComment').value.trim();

        const submitBtn = form.querySelector('button[type="submit"]');
        try {
            submitBtn.disabled = true;
            submitBtn.innerHTML = '<span>Đang lưu lời phê...</span>';

            await fetchAPI(`/submissions/${currentSubmittingSubId}/grade`, {
                method: 'PUT',
                body: JSON.stringify({
                    score: score,
                    teacher_comment: comment
                })
            });

            closeGradeModal();
            showToast('📜 Phê duyệt bài nộp thành công!', 'success');
            await loadTeacherSubmissions();
        } catch (err) {
            showToast('Lỗi phê duyệt: ' + err.message, 'error');
        } finally {
            submitBtn.disabled = false;
            submitBtn.innerHTML = '<span>📜 Lưu Phê Duyệt & Chấm Điểm</span>';
        }
    });
}

function escapeHtml(text) {
    if (!text) return '';
    return String(text).replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;').replace(/"/g, '&quot;');
}
