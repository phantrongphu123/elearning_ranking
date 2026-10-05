document.addEventListener('DOMContentLoaded', () => {
    const user = getUser();
    if (!user || user.role !== 'teacher') {
        window.location.href = '../index.html';
        return;
    }

    document.getElementById('userName').textContent = user.full_name;
    loadDashboard();
});

async function loadDashboard() {
    try {
        const data = await fetchAPI('/dashboard/teacher');
        
        // Update Stats
        document.getElementById('totalClasses').textContent = data.classes ? data.classes.length : 0;
        document.getElementById('totalStudents').textContent = data.total_students;
        document.getElementById('activeAssignments').textContent = data.active_assignments;
        document.getElementById('ungradedCount').textContent = data.ungraded_count;
        
        // Update Table
        const tbody = document.getElementById('classesTableBody');
        if (data.classes && data.classes.length > 0) {
            tbody.innerHTML = '';
            data.classes.forEach(cls => {
                const tr = document.createElement('tr');
                tr.innerHTML = `
                    <td>${cls.class_code}</td>
                    <td>${cls.class_name}</td>
                    <td>${cls.school_year}</td>
                    <td><span class="rank-badge">${cls.status === 'active' ? 'Hoạt động' : 'Khóa'}</span></td>
                `;
                tbody.appendChild(tr);
            });
        } else {
            tbody.innerHTML = '<tr><td colspan="4" class="text-center">Chưa phụ trách lớp nào</td></tr>';
        }

    } catch (error) {
        console.error("Failed to load dashboard:", error);
    }
}
