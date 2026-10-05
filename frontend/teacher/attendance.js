document.addEventListener('DOMContentLoaded', () => {
    // Set default date to today
    document.getElementById('dateSelect').valueAsDate = new Date();
    
    document.getElementById('attendanceForm').addEventListener('submit', async (e) => {
        e.preventDefault();
        
        const classId = document.getElementById('classSelect').value;
        const dateStr = document.getElementById('dateSelect').value;
        if (!classId || !dateStr) {
            alert('Vui lòng chọn lớp và ngày'); return;
        }

        const formData = new FormData(e.target);
        const records = [];
        
        // Group by student_id
        const studentIds = new Set();
        for (let key of formData.keys()) {
            if (key.startsWith('status_')) {
                studentIds.add(key.split('_')[1]);
            }
        }
        
        studentIds.forEach(id => {
            records.push({
                student_id: parseInt(id),
                status: formData.get(`status_${id}`),
                note: formData.get(`note_${id}`) || ''
            });
        });
        
        try {
            await fetchAPI('/attendance', {
                method: 'POST',
                body: JSON.stringify({
                    class_id: parseInt(classId),
                    date: dateStr,
                    records: records
                })
            });
            alert('Đã lưu điểm danh thành công!');
        } catch(err) {
            alert(err.message);
        }
    });
});

async function loadStudents() {
    const classId = document.getElementById('classSelect').value;
    if (!classId) return;
    
    try {
        const students = await fetchAPI(`/students?class_id=${classId}`);
        const tbody = document.getElementById('studentsTable');
        
        if (students.length === 0) {
            tbody.innerHTML = '<tr><td colspan="4" class="text-center">Lớp không có học sinh hoặc không tồn tại.</td></tr>';
            document.getElementById('attendancePanel').style.display = 'block';
            return;
        }
        
        tbody.innerHTML = '';
        students.forEach(s => {
            tbody.innerHTML += `
                <tr>
                    <td>${s.student_code}</td>
                    <td><strong>${s.full_name}</strong></td>
                    <td>
                        <select name="status_${s.student_id}" required style="padding: 0.5rem;">
                            <option value="present">Có mặt</option>
                            <option value="late">Đi trễ</option>
                            <option value="absent_excused">Nghỉ có phép</option>
                            <option value="absent_unexcused">Nghỉ KHÔNG phép</option>
                        </select>
                    </td>
                    <td>
                        <input type="text" name="note_${s.student_id}" placeholder="Ghi chú...">
                    </td>
                </tr>
            `;
        });
        
        document.getElementById('attendancePanel').style.display = 'block';
    } catch (error) {
        alert("Lỗi: " + error.message);
    }
}
