document.addEventListener('DOMContentLoaded', () => {
    const user = getUser();
    if (!user || user.role !== 'admin') {
        window.location.href = '../index.html';
        return;
    }

    document.getElementById('userName').textContent = user.full_name;
    loadDashboard();
});

async function loadDashboard() {
    try {
        const data = await fetchAPI('/dashboard/admin');
        
        // Update Stats
        document.getElementById('totalStudents').textContent = data.total_students;
        document.getElementById('totalClasses').textContent = data.total_classes;
        document.getElementById('totalTeachers').textContent = data.total_teachers;
        document.getElementById('avgScore').textContent = data.avg_score;
        
        // Update Top Students Table
        const tbody = document.getElementById('topStudentsTable');
        if (data.top_students && data.top_students.length > 0) {
            tbody.innerHTML = '';
            data.top_students.forEach((student, index) => {
                const tr = document.createElement('tr');
                tr.innerHTML = `
                    <td>${index + 1}</td>
                    <td>${student.full_name} (${student.student_code})</td>
                    <td><span class="rank-badge">${student.icon || '📜'} ${student.rank}</span></td>
                    <td style="color: var(--primary-color); font-weight: bold;">${student.total_score}</td>
                `;
                tbody.appendChild(tr);
            });
        } else {
            tbody.innerHTML = '<tr><td colspan="4" class="text-center">Chưa có dữ liệu</td></tr>';
        }

    } catch (error) {
        console.error("Failed to load dashboard:", error);
    }
}
