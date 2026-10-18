document.addEventListener('DOMContentLoaded', () => {
    if (!requireAuth(['student'])) return;
    initMobileNav('dashboard');
    loadStudentDashboard();
});

let currentStudentId = null;

async function loadStudentDashboard() {
    try {
        const data = await fetchAPI('/dashboard/student');
        const student = data.student || {};
        currentStudentId = student.student_id;

        // Rank Info
        const rankIconEl = document.getElementById('rankIcon');
        const rankNameEl = document.getElementById('rankName');
        const rankLevelBadgeEl = document.getElementById('rankLevelBadge');
        const totalScoreEl = document.getElementById('totalScore');
        const lbPositionEl = document.getElementById('leaderboardPosition');

        if (rankIconEl) rankIconEl.textContent = data.icon || '📜';
        if (rankNameEl) {
            rankNameEl.textContent = data.rank || 'Nô Tài';
            if (data.color) rankNameEl.style.color = data.color;
        }

        if (rankLevelBadgeEl && data.rank_level) {
            rankLevelBadgeEl.innerHTML = `<span class="badge badge-gold">Cấp ${data.rank_level}</span>`;
        }

        if (totalScoreEl) totalScoreEl.textContent = data.total_score ?? 0;
        if (lbPositionEl) lbPositionEl.textContent = data.position ? `#${data.position}` : '#-';

        // Next Rank Progress
        const nextRankNameEl = document.getElementById('nextRankName');
        const pointsNeededEl = document.getElementById('pointsNeeded');
        const progressBarEl = document.getElementById('rankProgressBar');

        if (data.next_rank) {
            if (nextRankNameEl) nextRankNameEl.textContent = data.next_rank;
            if (pointsNeededEl) pointsNeededEl.textContent = data.points_needed ?? 0;
            if (progressBarEl) progressBarEl.style.width = `${Math.min(100, Math.max(0, data.progress_pct || 0))}%`;
        } else {
            if (nextRankNameEl) nextRankNameEl.textContent = 'Đã Đạt Đỉnh Cao Triều Đình';
            if (pointsNeededEl) pointsNeededEl.textContent = '0';
            if (progressBarEl) progressBarEl.style.width = '100%';
        }

        // Stats Cards
        const pendingEl = document.getElementById('pendingAssignmentsCount');
        const subsEl = document.getElementById('totalSubmissionsCount');
        const streakEl = document.getElementById('attendanceStreakDays');

        if (pendingEl) pendingEl.textContent = data.pending_assignments ?? 0;
        if (subsEl) subsEl.textContent = data.total_submissions ?? 0;
        if (streakEl) streakEl.textContent = `${data.attendance_streak ?? 0} ngày`;

        // Breakdown
        if (data.score_breakdown) {
            const hw = document.getElementById('scoreHomework');
            const att = document.getElementById('scoreAttendance');
            const bon = document.getElementById('scoreBonus');
            if (hw) hw.textContent = `${data.score_breakdown.homework ?? 0} đ`;
            if (att) att.textContent = `${data.score_breakdown.attendance ?? 0} đ`;
            if (bon) bon.textContent = `${data.score_breakdown.bonus ?? 0} đ`;
        }

    } catch (error) {
        console.error('Lỗi tải dữ liệu học sinh:', error);
        showToast('Không thể tải thông tin học sinh: ' + error.message, 'error');
    }
}

async function openScoreHistoryModal() {
    const modal = document.getElementById('scoreHistoryModal');
    const container = document.getElementById('scoreHistoryList');
    if (!modal || !container) return;

    modal.style.display = 'flex';
    container.innerHTML = '<p class="text-center" style="color: var(--text-muted); padding: 2rem;">Đang tra cứu sổ lưu trữ điểm số...</p>';

    const user = getUser();
    const studentId = currentStudentId || user.student_id;

    if (!studentId) {
        container.innerHTML = '<p class="text-center" style="color: var(--crimson);">Không tìm thấy mã học sinh.</p>';
        return;
    }

    try {
        const scores = await fetchAPI(`/students/${studentId}/scores`);
        if (!scores || scores.length === 0) {
            container.innerHTML = '<p class="text-center" style="color: var(--text-muted); padding: 2rem;">Chưa có bản ghi điểm nào trong sổ bộ.</p>';
            return;
        }

        container.innerHTML = `
            <div class="table-container">
                <table>
                    <thead>
                        <tr>
                            <th>Thời Gian</th>
                            <th>Hạng Mục</th>
                            <th>Lý Do / Chiếu Chỉ</th>
                            <th>Điểm</th>
                        </tr>
                    </thead>
                    <tbody>
                        ${scores.map(s => {
                            const pts = parseFloat(s.points || 0);
                            const isPositive = pts >= 0;
                            const pointClass = isPositive ? 'var(--jade)' : 'var(--crimson)';
                            const pointSign = isPositive ? `+${pts}` : `${pts}`;
                            
                            const typeLabels = {
                                homework: 'Bài tập',
                                attendance: 'Chuyên cần',
                                bonus: 'Thưởng',
                                penalty: 'Phạt',
                                manual: 'Điều chỉnh'
                            };

                            return `
                                <tr>
                                    <td style="font-size: 0.82rem; color: var(--text-muted);">${formatDate(s.created_at)}</td>
                                    <td><span class="badge ${isPositive ? 'badge-success' : 'badge-danger'}">${typeLabels[s.type] || s.type}</span></td>
                                    <td>${s.reason || 'Cập nhật điểm số'}</td>
                                    <td style="font-weight: 700; color: ${pointClass}; font-family: 'Plus Jakarta Sans', 'Be Vietnam Pro', sans-serif;">${pointSign}</td>
                                </tr>
                            `;
                        }).join('')}
                    </tbody>
                </table>
            </div>
        `;
    } catch (e) {
        container.innerHTML = `<p class="text-center" style="color: var(--crimson);">Lỗi: ${e.message}</p>`;
    }
}

function closeScoreHistoryModal() {
    const modal = document.getElementById('scoreHistoryModal');
    if (modal) modal.style.display = 'none';
}
