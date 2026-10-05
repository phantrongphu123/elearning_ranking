document.addEventListener('DOMContentLoaded', () => {
    const user = getUser();
    if (!user || user.role !== 'student') {
        window.location.href = '../index.html';
        return;
    }

    document.getElementById('userName').textContent = user.full_name;
    loadDashboard();
});

async function loadDashboard() {
    try {
        const data = await fetchAPI('/dashboard/student');
        
        // Update UI
        document.getElementById('rankIcon').textContent = data.icon || '📜';
        document.getElementById('rankName').textContent = data.rank || 'Nô Tài';
        
        document.getElementById('totalScore').textContent = data.total_score;
        document.getElementById('leaderboardPos').textContent = data.position;
        
        if (data.next_rank) {
            document.getElementById('nextRank').textContent = data.next_rank;
            document.getElementById('pointsNeeded').textContent = data.points_needed;
            document.getElementById('rankProgress').style.width = `${data.progress_pct}%`;
        } else {
            document.getElementById('nextRank').textContent = 'Đã đạt đỉnh cao';
            document.getElementById('pointsNeeded').textContent = '0';
            document.getElementById('rankProgress').style.width = '100%';
        }
        
        document.getElementById('pendingAssignments').textContent = data.pending_assignments;
        document.getElementById('totalSubmissions').textContent = data.total_submissions;
        document.getElementById('attendanceStreak').textContent = data.attendance_streak + ' ngày';
        
        if (data.score_breakdown) {
            document.getElementById('scoreHomework').textContent = data.score_breakdown.homework;
            document.getElementById('scoreAttendance').textContent = data.score_breakdown.attendance;
            document.getElementById('scoreBonus').textContent = data.score_breakdown.bonus;
        }

    } catch (error) {
        console.error("Failed to load dashboard:", error);
    }
}
