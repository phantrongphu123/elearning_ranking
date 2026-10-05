let currentAssignmentId = null;
let submittedAssignmentIds = new Set();

document.addEventListener('DOMContentLoaded', () => {
    loadSubmissions().then(loadAssignments);
    
    document.getElementById('submissionForm').addEventListener('submit', async (e) => {
        e.preventDefault();
        await submitAssignment();
    });
});

async function loadSubmissions() {
    try {
        const subs = await fetchAPI('/submissions');
        subs.forEach(s => submittedAssignmentIds.add(String(s.assignment_id)));
    } catch (e) { console.error(e); }
}

async function loadAssignments() {
    try {
        const assignments = await fetchAPI('/assignments');
        const container = document.getElementById('assignmentsList');
        
        if (assignments.length === 0) {
            container.innerHTML = '<p class="text-center">Không có tấu chương nào.</p>';
            return;
        }

        container.innerHTML = '';
        assignments.forEach(a => {
            const isSubmitted = submittedAssignmentIds.has(String(a.assignment_id));
            const badge = isSubmitted 
                ? '<span class="badge badge-submitted">Đã nộp</span>'
                : '<span class="badge badge-pending">Chưa nộp</span>';
                
            const deadlineDate = a.deadline ? new Date(a.deadline).toLocaleString('vi-VN') : 'Không có';
            
            const btn = isSubmitted 
                ? `<button class="btn btn-secondary" disabled>Đã Dâng Trình</button>`
                : `<button class="btn btn-primary" onclick="openAssignment(${a.assignment_id}, '${a.title}', '${a.description}')">Làm Bài</button>`;

            container.innerHTML += `
                <div class="assignment-card">
                    <div class="d-flex justify-between align-center">
                        <div>
                            <h3 style="margin-bottom: 0.2rem;">${a.title} ${badge}</h3>
                            <div class="meta-info">
                                <span>Môn: ${a.subject}</span>
                                <span>Hạn chót: <span style="color: ${a.is_past_deadline ? 'var(--danger)' : 'inherit'}">${deadlineDate}</span></span>
                            </div>
                            <p style="font-size: 0.9rem;">${a.description || ''}</p>
                        </div>
                        <div>
                            ${btn}
                        </div>
                    </div>
                </div>
            `;
        });
    } catch (error) {
        document.getElementById('assignmentsList').innerHTML = `<p class="text-center" style="color: var(--danger)">Lỗi tải dữ liệu: ${error.message}</p>`;
    }
}

async function openAssignment(id, title, desc) {
    currentAssignmentId = id;
    document.getElementById('modalTitle').textContent = title;
    document.getElementById('modalDescription').textContent = desc || '';
    
    const qContainer = document.getElementById('questionsContainer');
    qContainer.innerHTML = '<p>Đang lấy đề bài...</p>';
    document.getElementById('assignmentModal').style.display = 'flex';
    document.getElementById('submitArea').style.display = 'block';

    try {
        const questions = await fetchAPI(`/assignments/${id}/questions`);
        if(questions.length === 0) {
            qContainer.innerHTML = '<p>Bài tập này chưa có câu hỏi.</p>';
            document.getElementById('submitArea').style.display = 'none';
            return;
        }
        
        qContainer.innerHTML = '';
        questions.forEach((q, idx) => {
            let inputsHtml = '';
            
            if (q.question_type === 'multiple_choice' || q.question_type === 'true_false') {
                const options = q.question_type === 'multiple_choice' 
                    ? [
                        {val: 'a', text: q.option_a},
                        {val: 'b', text: q.option_b},
                        {val: 'c', text: q.option_c},
                        {val: 'd', text: q.option_d}
                      ]
                    : [
                        {val: 'a', text: q.option_a || 'Đúng'},
                        {val: 'b', text: q.option_b || 'Sai'}
                      ];
                      
                inputsHtml = `<div class="options-grid">`;
                options.forEach(opt => {
                    if(!opt.text) return;
                    inputsHtml += `
                        <label class="option-label">
                            <input type="radio" name="q_${q.question_id}" value="${opt.val}" required>
                            <span>${opt.text}</span>
                        </label>
                    `;
                });
                inputsHtml += `</div>`;
            } else {
                inputsHtml = `<input type="text" name="q_${q.question_id}" placeholder="Nhập câu trả lời..." required style="margin-top: 1rem;">`;
            }
            
            qContainer.innerHTML += `
                <div class="question-block">
                    <h4>Câu ${idx + 1}: ${q.question_text}</h4>
                    <span style="font-size: 0.8rem; color: var(--text-muted)">(${q.score} điểm)</span>
                    ${inputsHtml}
                </div>
            `;
        });
        
    } catch (e) {
        qContainer.innerHTML = `<p style="color: var(--danger)">Lỗi: ${e.message}</p>`;
    }
}

function closeModal() {
    document.getElementById('assignmentModal').style.display = 'none';
}

async function submitAssignment() {
    const form = document.getElementById('submissionForm');
    const formData = new FormData(form);
    const answers = {};
    
    for (let [key, value] of formData.entries()) {
        if(key.startsWith('q_')) {
            const qId = key.split('_')[1];
            answers[qId] = value;
        }
    }
    
    try {
        const submitBtn = form.querySelector('button[type="submit"]');
        submitBtn.disabled = true;
        submitBtn.textContent = 'Đang Nộp...';
        
        const res = await fetchAPI('/submissions', {
            method: 'POST',
            body: JSON.stringify({
                assignment_id: currentAssignmentId,
                answers: answers
            })
        });
        
        alert(`Nộp bài thành công!\nĐiểm đạt được: ${res.score}\nCộng vào tổng điểm: ${res.points_added}`);
        closeModal();
        loadSubmissions().then(loadAssignments);
        
    } catch (error) {
        alert("Lỗi nộp bài: " + error.message);
    } finally {
        const submitBtn = form.querySelector('button[type="submit"]');
        submitBtn.disabled = false;
        submitBtn.textContent = 'Dâng Trình (Nộp Bài)';
    }
}
