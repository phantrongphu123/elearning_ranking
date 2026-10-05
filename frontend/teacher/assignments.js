document.addEventListener('DOMContentLoaded', () => {
    loadAssignments();
    
    document.getElementById('createForm').addEventListener('submit', async (e) => {
        e.preventDefault();
        const fd = new FormData(e.target);
        const data = Object.fromEntries(fd.entries());
        data.deadline = data.deadline ? new Date(data.deadline).toISOString() : null;
        
        try {
            await fetchAPI('/assignments', {
                method: 'POST',
                body: JSON.stringify(data)
            });
            alert('Tạo bài tập thành công! Bạn có thể thêm câu hỏi ở bước tiếp theo.');
            closeModal();
            loadAssignments();
        } catch(e) {
            alert('Lỗi: ' + e.message);
        }
    });
});

async function loadAssignments() {
    try {
        const assignments = await fetchAPI('/assignments');
        const tbody = document.getElementById('assignmentsTable');
        
        if (assignments.length === 0) {
            tbody.innerHTML = '<tr><td colspan="6" class="text-center">Chưa có bài tập nào.</td></tr>';
            return;
        }

        tbody.innerHTML = '';
        assignments.forEach(a => {
            const dateStr = a.deadline ? new Date(a.deadline).toLocaleString('vi-VN') : '';
            tbody.innerHTML += `
                <tr>
                    <td><strong>${a.title}</strong></td>
                    <td>${a.subject}</td>
                    <td>Lớp ID: ${a.class_id}</td>
                    <td><span style="color: ${a.is_past_deadline ? 'var(--danger)' : 'inherit'}">${dateStr}</span></td>
                    <td>${a.submission_count}</td>
                    <td>
                        <button class="btn btn-secondary" style="padding: 0.2rem 0.5rem; font-size: 0.8rem;" onclick="deleteAssignment(${a.assignment_id})">Thu Hồi</button>
                    </td>
                </tr>
            `;
        });
    } catch (e) {
        console.error(e);
    }
}

function openCreateModal() { document.getElementById('createModal').style.display = 'flex'; }
function closeModal() { document.getElementById('createModal').style.display = 'none'; }

async function deleteAssignment(id) {
    if(!confirm("Bạn có chắc chắn muốn thu hồi bài tập này?")) return;
    try {
        await fetchAPI(`/assignments/${id}`, { method: 'DELETE' });
        loadAssignments();
    } catch(e) {
        alert(e.message);
    }
}
