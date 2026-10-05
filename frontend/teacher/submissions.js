let currentSubId = null;

document.addEventListener('DOMContentLoaded', () => {
    loadSubmissions();
    
    document.getElementById('gradeForm').addEventListener('submit', async (e) => {
        e.preventDefault();
        const score = document.getElementById('gradeScore').value;
        const comment = document.getElementById('gradeComment').value;
        
        try {
            await fetchAPI(`/submissions/${currentSubId}/grade`, {
                method: 'PUT',
                body: JSON.stringify({
                    score: parseFloat(score),
                    teacher_comment: comment
                })
            });
            alert('Chấm bài / Phê duyệt thành công!');
            closeModal();
            loadSubmissions();
        } catch(err) {
            alert(err.message);
        }
    });
});

async function loadSubmissions() {
    try {
        const subs = await fetchAPI('/submissions');
        const tbody = document.getElementById('subsTable');
        
        if (subs.length === 0) {
            tbody.innerHTML = '<tr><td colspan="6" class="text-center">Chưa có học sinh nào nộp bài.</td></tr>';
            return;
        }

        tbody.innerHTML = '';
        subs.forEach(s => {
            const isLate = s.is_late === 'True';
            const lateBadge = isLate ? '<span class="badge" style="background:var(--danger)">Trễ</span>' : '<span class="badge badge-graded">Đúng hạn</span>';
            const statusBadge = s.status === 'graded' 
                ? '<span class="badge badge-graded">Đã chấm</span>' 
                : '<span class="badge badge-pending">Chờ xử lý</span>';
                
            tbody.innerHTML += `
                <tr>
                    <td><strong>${s.assignment_title}</strong></td>
                    <td>${s.student_name}</td>
                    <td>${lateBadge}</td>
                    <td style="color: var(--primary-color); font-weight: bold;">${s.score}</td>
                    <td>${statusBadge}</td>
                    <td>
                        <button class="btn btn-secondary" style="padding: 0.2rem 0.5rem; font-size: 0.8rem;" onclick="openGradeModal(${s.submission_id}, '${s.student_name}', ${s.score}, '${s.teacher_comment || ''}')">Phê Duyệt</button>
                    </td>
                </tr>
            `;
        });
    } catch (e) {
        console.error(e);
    }
}

function openGradeModal(id, studentName, currentScore, currentComment) {
    currentSubId = id;
    document.getElementById('gradeDetails').textContent = `Học sinh: ${studentName}`;
    document.getElementById('gradeScore').value = currentScore;
    document.getElementById('gradeComment').value = currentComment || '';
    document.getElementById('gradeModal').style.display = 'flex';
}

function closeModal() {
    document.getElementById('gradeModal').style.display = 'none';
}
