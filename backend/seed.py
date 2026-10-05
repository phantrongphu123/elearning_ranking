"""
Seed script - tạo dữ liệu mẫu đầy đủ cho hệ thống Hoàng Cung Học Đường.
Chạy: python seed.py
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from datetime import datetime, timedelta
import random

from app.core.security import hash_password
from app.services.excel_service import ExcelService

excel_service = ExcelService()


def seed_all():
    print("🏯 Đang tạo dữ liệu mẫu Hoàng Cung Học Đường...\n")
    
    now = datetime.now()

    # ── 1. USERS ──────────────────────────────────────────────────────────────
    print("👤 Tạo tài khoản...")
    users = [
        # Admin
        {"user_id": 1, "username": "admin", "password_hash": hash_password("admin123"),
         "full_name": "Hoàng Đế - Admin", "role": "admin", "student_id": "", "class_id": "",
         "status": "active", "created_at": now.isoformat()},
        # Teachers
        {"user_id": 2, "username": "teacher01", "password_hash": hash_password("teacher123"),
         "full_name": "Nguyễn Thị Lan", "role": "teacher", "student_id": "", "class_id": "",
         "status": "active", "created_at": now.isoformat()},
        {"user_id": 3, "username": "teacher02", "password_hash": hash_password("teacher123"),
         "full_name": "Trần Văn Minh", "role": "teacher", "student_id": "", "class_id": "",
         "status": "active", "created_at": now.isoformat()},
    ]

    # Students (20 students)
    student_names_female = [
        "Nguyễn Thị Hoa", "Trần Thị Mai", "Lê Thị Lan", "Phạm Thị Hương",
        "Vũ Thị Ngọc", "Đặng Thị Thủy", "Bùi Thị Linh", "Hoàng Thị Yến",
        "Phan Thị Trang", "Ngô Thị Thu",
    ]
    student_names_male = [
        "Nguyễn Văn An", "Trần Văn Bình", "Lê Văn Cường", "Phạm Văn Dũng",
        "Vũ Văn Em", "Đặng Văn Phúc", "Bùi Văn Giang", "Hoàng Văn Hải",
        "Phan Văn Ích", "Ngô Văn Khoa",
    ]

    student_scores = [1820, 1650, 1520, 1380, 1250, 1100, 980, 850, 720, 600,
                      480, 380, 290, 210, 150, 90, 60, 35, 15, 5]

    for i, (score, name) in enumerate(zip(student_scores, student_names_female + student_names_male)):
        sid = i + 1
        uid = sid + 3  # user_id starts after admin+teachers
        gender = "female" if i < 10 else "male"
        class_id = 1 if i < 7 else (2 if i < 14 else 3)
        
        from app.services.rank_service import calculate_rank
        rank_info = calculate_rank(score, gender)
        
        users.append({
            "user_id": uid,
            "username": f"student{sid:02d}",
            "password_hash": hash_password("student123"),
            "full_name": name,
            "role": "student",
            "student_id": sid,
            "class_id": class_id,
            "status": "active",
            "created_at": now.isoformat(),
        })

        excel_service.insert_row("HocSinh", {
            "student_id": sid,
            "student_code": f"HS{sid:04d}",
            "full_name": name,
            "date_of_birth": f"{2008 + random.randint(0, 2)}-{random.randint(1,12):02d}-{random.randint(1,28):02d}",
            "gender": gender,
            "class_id": class_id,
            "total_score": score,
            "rank": rank_info["rank"],
            "rank_level": rank_info["rank_level"],
            "avatar": "",
            "status": "active",
            "created_at": now.isoformat(),
        })

    import pandas as pd
    excel_service.write_sheet("Users", pd.DataFrame(users))
    print(f"  ✓ {len(users)} tài khoản đã tạo")

    # ── 2. CLASSES ────────────────────────────────────────────────────────────
    print("🏫 Tạo lớp học...")
    classes = [
        {"class_id": 1, "class_code": "12A1", "class_name": "Lớp 12A1", "teacher_id": 2, "school_year": "2026-2027", "status": "active"},
        {"class_id": 2, "class_code": "12A2", "class_name": "Lớp 12A2", "teacher_id": 3, "school_year": "2026-2027", "status": "active"},
        {"class_id": 3, "class_code": "11A1", "class_name": "Lớp 11A1", "teacher_id": 2, "school_year": "2026-2027", "status": "active"},
    ]
    excel_service.write_sheet("LopHoc", pd.DataFrame(classes))
    print(f"  ✓ {len(classes)} lớp đã tạo")

    # ── 3. ASSIGNMENTS ────────────────────────────────────────────────────────
    print("📝 Tạo bài tập và câu hỏi...")
    assignments_data = [
        {"assignment_id": 1, "title": "Bài Tập Python - Vòng Lặp", "description": "Ôn tập các vòng lặp for, while trong Python", "subject": "Tin học", "class_id": 1, "teacher_id": 2, "created_at": (now - timedelta(days=10)).isoformat(), "start_time": (now - timedelta(days=10)).isoformat(), "deadline": (now - timedelta(days=7)).isoformat(), "max_score": 100, "bonus_score": 20, "penalty_score": 10, "status": "active"},
        {"assignment_id": 2, "title": "Toán - Giải Tích", "description": "Các bài tập đạo hàm và tích phân", "subject": "Toán", "class_id": 1, "teacher_id": 2, "created_at": (now - timedelta(days=5)).isoformat(), "start_time": (now - timedelta(days=5)).isoformat(), "deadline": (now + timedelta(days=2)).isoformat(), "max_score": 100, "bonus_score": 15, "penalty_score": 5, "status": "active"},
        {"assignment_id": 3, "title": "Vật Lý - Điện Học", "description": "Bài tập về mạch điện và định luật Ohm", "subject": "Vật lý", "class_id": 2, "teacher_id": 3, "created_at": (now - timedelta(days=3)).isoformat(), "start_time": (now - timedelta(days=3)).isoformat(), "deadline": (now + timedelta(days=4)).isoformat(), "max_score": 100, "bonus_score": 10, "penalty_score": 8, "status": "active"},
        {"assignment_id": 4, "title": "Hóa Học - Phản Ứng Hóa Học", "description": "Nhận biết các loại phản ứng hóa học", "subject": "Hóa học", "class_id": 3, "teacher_id": 2, "created_at": (now - timedelta(days=1)).isoformat(), "start_time": (now - timedelta(days=1)).isoformat(), "deadline": (now + timedelta(days=6)).isoformat(), "max_score": 100, "bonus_score": 10, "penalty_score": 5, "status": "active"},
        {"assignment_id": 5, "title": "Văn - Phân Tích Tác Phẩm", "description": "Phân tích bài thơ Đây Thôn Vĩ Dạ", "subject": "Ngữ văn", "class_id": 1, "teacher_id": 2, "created_at": now.isoformat(), "start_time": now.isoformat(), "deadline": (now + timedelta(days=10)).isoformat(), "max_score": 100, "bonus_score": 5, "penalty_score": 5, "status": "active"},
    ]
    excel_service.write_sheet("BaiTap", pd.DataFrame(assignments_data))

    # Questions for Assignment 1 (Python)
    questions = [
        {"question_id": 1, "assignment_id": 1, "question_type": "multiple_choice", "question_text": "Python dùng từ khóa nào để tạo vòng lặp đếm?", "option_a": "if", "option_b": "for", "option_c": "switch", "option_d": "loop", "correct_answer": "b", "score": 10},
        {"question_id": 2, "assignment_id": 1, "question_type": "multiple_choice", "question_text": "Hàm range(5) tạo ra dãy số nào?", "option_a": "1,2,3,4,5", "option_b": "0,1,2,3,4", "option_c": "0,1,2,3,4,5", "option_d": "1,2,3,4", "correct_answer": "b", "score": 10},
        {"question_id": 3, "assignment_id": 1, "question_type": "true_false", "question_text": "Vòng lặp while có thể tạo vòng lặp vô tận nếu điều kiện luôn đúng.", "option_a": "Đúng", "option_b": "Sai", "option_c": "", "option_d": "", "correct_answer": "a", "score": 10},
        {"question_id": 4, "assignment_id": 1, "question_type": "multiple_choice", "question_text": "Từ khóa nào dùng để thoát khỏi vòng lặp?", "option_a": "exit", "option_b": "stop", "option_c": "break", "option_d": "end", "correct_answer": "c", "score": 10},
        {"question_id": 5, "assignment_id": 1, "question_type": "multiple_choice", "question_text": "Từ khóa nào bỏ qua lần lặp hiện tại và tiếp tục lần sau?", "option_a": "skip", "option_b": "continue", "option_c": "pass", "option_d": "next", "correct_answer": "b", "score": 10},
        # Assignment 2 questions
        {"question_id": 6, "assignment_id": 2, "question_type": "multiple_choice", "question_text": "Đạo hàm của x² là gì?", "option_a": "x", "option_b": "2x", "option_c": "x²", "option_d": "2", "correct_answer": "b", "score": 10},
        {"question_id": 7, "assignment_id": 2, "question_type": "multiple_choice", "question_text": "∫x dx bằng?", "option_a": "x²/2 + C", "option_b": "x² + C", "option_c": "2x + C", "option_d": "x/2 + C", "correct_answer": "a", "score": 10},
        {"question_id": 8, "assignment_id": 2, "question_type": "true_false", "question_text": "Đạo hàm của hằng số bằng 0.", "option_a": "Đúng", "option_b": "Sai", "option_c": "", "option_d": "", "correct_answer": "a", "score": 10},
        # Assignment 3 questions
        {"question_id": 9, "assignment_id": 3, "question_type": "multiple_choice", "question_text": "Định luật Ohm: I = ?", "option_a": "U × R", "option_b": "U / R", "option_c": "R / U", "option_d": "U + R", "correct_answer": "b", "score": 10},
        {"question_id": 10, "assignment_id": 3, "question_type": "multiple_choice", "question_text": "Đơn vị của điện trở là?", "option_a": "Ampe", "option_b": "Volt", "option_c": "Ohm", "option_d": "Watt", "correct_answer": "c", "score": 10},
    ]
    excel_service.write_sheet("CauHoi", pd.DataFrame(questions))
    print(f"  ✓ {len(assignments_data)} bài tập, {len(questions)} câu hỏi đã tạo")

    # ── 4. SCORE HISTORY (Diem) ───────────────────────────────────────────────
    print("💰 Tạo lịch sử điểm...")
    diem_records = []
    score_id = 1
    for sid in range(1, 21):
        score = student_scores[sid - 1]
        # Create enough score entries to equal the student's total score
        # Attendance
        for d in range(30):
            day = (now - timedelta(days=d)).isoformat()
            pts = 5 if random.random() > 0.2 else (2 if random.random() > 0.5 else -10)
            diem_records.append({
                "score_id": score_id, "student_id": sid, "type": "attendance",
                "reason": "Điểm danh chuyên cần", "points": pts,
                "assignment_id": "", "created_at": day, "created_by": "system"
            })
            score_id += 1
    
    # Add dummy homework scores to approximate total
    for sid in range(1, 21):
        diem_records.append({
            "score_id": score_id, "student_id": sid, "type": "homework",
            "reason": "Tổng điểm BTVN tích lũy", "points": max(0, student_scores[sid-1] - 150),
            "assignment_id": "", "created_at": (now - timedelta(days=60)).isoformat(), "created_by": "system"
        })
        score_id += 1

    excel_service.write_sheet("Diem", pd.DataFrame(diem_records))
    print(f"  ✓ {len(diem_records)} bản ghi điểm đã tạo")

    # ── 5. ATTENDANCE ─────────────────────────────────────────────────────────
    print("📅 Tạo dữ liệu điểm danh...")
    attendance_records = []
    att_id = 1
    for d in range(10):
        date = (now - timedelta(days=d)).strftime("%Y-%m-%d")
        for sid in range(1, 21):
            status_choices = ["present"] * 7 + ["late"] * 2 + ["absent_excused"]
            status = random.choice(status_choices)
            attendance_records.append({
                "attendance_id": att_id, "student_id": sid,
                "class_id": 1 if sid <= 7 else (2 if sid <= 14 else 3),
                "date": date, "status": status,
                "points": {"present": 5, "late": 2, "absent_excused": 0, "absent_unexcused": -10}[status],
                "note": "", "created_by": "teacher01"
            })
            att_id += 1
    
    excel_service.write_sheet("DiemDanh", pd.DataFrame(attendance_records))
    print(f"  ✓ {len(attendance_records)} bản ghi điểm danh đã tạo")

    # ── 6. RANK HISTORY ──────────────────────────────────────────────────────
    print("👑 Tạo lịch sử rank...")
    rank_history = []
    rh_id = 1
    from app.services.rank_service import calculate_rank
    for sid in range(1, 6):  # Top 5 students with rank history
        score = student_scores[sid - 1]
        steps = [score // 4, score // 2, score * 3 // 4, score]
        prev_rank = ""
        for s in steps:
            rinfo = calculate_rank(s, "female" if sid <= 10 else "male")
            new_rank = rinfo["rank"]
            if new_rank != prev_rank:
                rank_history.append({
                    "history_id": rh_id, "student_id": sid,
                    "old_rank": prev_rank, "new_rank": new_rank,
                    "total_score": s, "changed_at": (now - timedelta(days=60 - rh_id * 5)).isoformat(),
                    "reason": f"Tổng điểm đạt {s}"
                })
                rh_id += 1
                prev_rank = new_rank
    
    excel_service.write_sheet("RankHistory", pd.DataFrame(rank_history))
    print(f"  ✓ {len(rank_history)} bản ghi lịch sử rank đã tạo")

    # ── 7. ACHIEVEMENTS ──────────────────────────────────────────────────────
    print("🏆 Tạo thành tích mẫu...")
    achievements = []
    ach_id = 1
    predefined = [
        ("dung_han_10", "Học Sinh Chăm Chỉ", "Nộp 10 bài đúng hạn", "🏆"),
        ("perfect_score", "Không Sai Câu Nào", "Đạt 100 điểm trong một bài", "💯"),
        ("rank_up", "Vươn Tới Đỉnh Cao", "Đạt rank Quý Nhân trở lên", "👑"),
    ]
    for sid in range(1, 11):  # Top 10 students get achievements
        for code, name, desc, icon in predefined[:min(3, 4 - sid // 3)]:
            achievements.append({
                "achievement_id": ach_id, "student_id": sid,
                "achievement_code": code, "achievement_name": name,
                "description": desc, "icon": icon,
                "unlocked_at": (now - timedelta(days=random.randint(1, 30))).isoformat()
            })
            ach_id += 1
    
    excel_service.write_sheet("ThanhTich", pd.DataFrame(achievements))
    print(f"  ✓ {len(achievements)} thành tích đã tạo")

    # ── 8. NOTIFICATIONS ─────────────────────────────────────────────────────
    print("🔔 Tạo thông báo mẫu...")
    notifs = []
    nid = 1
    for uid in range(4, 24):  # student users
        sid = uid - 3
        notifs.append({
            "notification_id": nid, "user_id": uid,
            "title": "Chào mừng", "message": f"🔔 Chào mừng đến Hoàng Cung Học Đường! Điểm hiện tại: {student_scores[sid-1]}",
            "type": "info", "is_read": "false", "created_at": now.isoformat()
        })
        nid += 1
        notifs.append({
            "notification_id": nid, "user_id": uid,
            "title": "Rank của bạn", "message": f"👑 Rank hiện tại: {calculate_rank(student_scores[sid-1], 'female')['rank']}",
            "type": "rank", "is_read": "false", "created_at": now.isoformat()
        })
        nid += 1
    
    excel_service.write_sheet("ThongBao", pd.DataFrame(notifs))
    print(f"  ✓ {len(notifs)} thông báo đã tạo")

    print("\n✅ SEED DATA HOÀN TẤT!\n")
    print("=" * 50)
    print("📋 TÀI KHOẢN DEMO:")
    print("=" * 50)
    print("👑 ADMIN:")
    print("   Username: admin | Password: admin123")
    print("\n👨‍🏫 TEACHER:")
    print("   Username: teacher01 | Password: teacher123")
    print("   Username: teacher02 | Password: teacher123")
    print("\n👨‍🎓 STUDENT:")
    print("   Username: student01 | Password: student123  (Hoàng Đế - 1820đ)")
    print("   Username: student05 | Password: student123  (Hoàng Hậu - 1250đ)")
    print("   Username: student10 | Password: student123  (Phi - 600đ)")
    print("   Username: student15 | Password: student123  (Thường Tại - 150đ)")
    print("=" * 50)
    print("\n🚀 Khởi chạy server:")
    print("   cd backend")
    print("   uvicorn app.main:app --reload --port 8000")


if __name__ == "__main__":
    seed_all()
