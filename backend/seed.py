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
         "full_name": "Nguyễn Thị Lan (GVCN 10A4)", "role": "teacher", "student_id": "", "class_id": "1",
         "status": "active", "created_at": now.isoformat()},
    ]

    student_data = [
        ("Ngô Vĩnh Thái", "male", 1350),
        ("Trương Quốc Tiến", "male", 980),
        ("Nguyễn Minh Anh", "female", 380),
        ("Hoàng Gia Hân", "female", 1550),
        ("Lê Minh Tuệ", "female", 540),
        ("Trần Ngọc Phương Anh", "female", 1220),
        ("Lê Phương Linh", "female", 870),
        ("Nguyễn Khánh Uyên", "female", 650),
        ("Phạm Gia Bách", "male", 720),
        ("Đinh Hoàng Bảo Linh", "female", 250),
        ("Nguyễn Ngân Nguyệt", "female", 160),
        ("Nguyễn Xuân Thủy", "male", 320),
        ("Hoàng Thanh Tùng", "male", 450),
        ("Dương Nguyễn Vân Khánh", "female", 120),
        ("Võ Minh Nam", "male", 200),
        ("Nguyễn Gia Khánh", "male", 80),
        ("Nguyễn Nhã Linh", "female", 50),
        ("Nguyễn Minh Khuê", "female", 30),
    ]

    for i, (name, gender, score) in enumerate(student_data):
        sid = i + 1
        uid = sid + 2  # user_id starts after admin+teacher01
        class_id = 1
        
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
            "date_of_birth": "2009-01-01",
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
        {"class_id": 1, "class_code": "10A4", "class_name": "Lớp 10A4 - Càn Long Cung", "teacher_id": 2, "school_year": "2025-2026", "status": "active"},
    ]
    excel_service.write_sheet("LopHoc", pd.DataFrame(classes))
    print(f"  ✓ {len(classes)} lớp đã tạo")

    # ── 3. ASSIGNMENTS ────────────────────────────────────────────────────────
    print("📝 Tạo bài tập và câu hỏi...")
    assignments_data = [
        {
            "assignment_id": 1,
            "title": "Tấu Chương Toán Học - Mệnh Đề & Tập Hợp",
            "description": "Khảo hạch kiến thức Toán 10 chương Mệnh đề, Tập hợp và các phép toán giao, hợp, hiệu.",
            "subject": "Toán",
            "class_id": 1,
            "teacher_id": 2,
            "created_at": now.isoformat(),
            "start_time": now.isoformat(),
            "deadline": (now + timedelta(days=7)).isoformat(),
            "max_score": 100,
            "bonus_score": 10,
            "penalty_score": 5,
            "status": "active"
        },
        {
            "assignment_id": 2,
            "title": "Ngự Thí Ngữ Văn - Văn Học Dân Gian & Sử Thi",
            "description": "Kiểm tra kiến thức Ngữ Văn 10 về Thần thoại Hy Lạp, Sử thi Đăm Săn và Văn học dân gian.",
            "subject": "Ngữ Văn",
            "class_id": 1,
            "teacher_id": 2,
            "created_at": now.isoformat(),
            "start_time": now.isoformat(),
            "deadline": (now + timedelta(days=10)).isoformat(),
            "max_score": 100,
            "bonus_score": 10,
            "penalty_score": 5,
            "status": "active"
        },
        {
            "assignment_id": 3,
            "title": "Thi Đình Ngoại Ngữ - English Unit 1 & Grammar",
            "description": "English 10 Global Success: Family Life, Present Simple vs Continuous, and Vocabulary.",
            "subject": "Tiếng Anh",
            "class_id": 1,
            "teacher_id": 2,
            "created_at": now.isoformat(),
            "start_time": now.isoformat(),
            "deadline": (now + timedelta(days=12)).isoformat(),
            "max_score": 100,
            "bonus_score": 10,
            "penalty_score": 5,
            "status": "active"
        },
        {
            "assignment_id": 4,
            "title": "Khảo Thí Vật Lý - Động Học & Ba Định Luật Newton",
            "description": "Kiểm tra Vật lý 10 về Chuyển động biến đổi đều, Rơi tự do và Ba định luật Newton.",
            "subject": "Vật Lý",
            "class_id": 1,
            "teacher_id": 2,
            "created_at": now.isoformat(),
            "start_time": now.isoformat(),
            "deadline": (now + timedelta(days=14)).isoformat(),
            "max_score": 100,
            "bonus_score": 10,
            "penalty_score": 5,
            "status": "active"
        },
    ]
    excel_service.write_sheet("BaiTap", pd.DataFrame(assignments_data))

    # Questions for 4 Assignments (6 questions each)
    questions = [
        # ── Bài 1: Toán (6 câu) ──
        {"question_id": 1, "assignment_id": 1, "question_type": "multiple_choice", "question_text": "Trong các câu sau, câu nào là một mệnh đề toán học?", "option_a": "Hôm nay trời đẹp quá!", "option_b": "15 là số nguyên tố.", "option_c": "Bạn học lớp nào vậy?", "option_d": "x + 1 > 0.", "correct_answer": "b", "score": 15},
        {"question_id": 2, "assignment_id": 1, "question_type": "multiple_choice", "question_text": "Mệnh đề phủ định của mệnh đề: '∀x ∈ ℝ, x² - x + 7 > 0' là:", "option_a": "∃x ∈ ℝ, x² - x + 7 ≤ 0", "option_b": "∀x ∈ ℝ, x² - x + 7 < 0", "option_c": "∃x ∈ ℝ, x² - x + 7 < 0", "option_d": "∃x ∈ ℝ, x² - x + 7 > 0", "correct_answer": "a", "score": 15},
        {"question_id": 3, "assignment_id": 1, "question_type": "multiple_choice", "question_text": "Cho tập hợp A = {1; 2; 3; 4} và B = {3; 4; 5; 6}. Phép giao A ∩ B là tập hợp nào?", "option_a": "{1; 2}", "option_b": "{3; 4}", "option_c": "{1; 2; 3; 4; 5; 6}", "option_d": "{5; 6}", "correct_answer": "b", "score": 15},
        {"question_id": 4, "assignment_id": 1, "question_type": "multiple_choice", "question_text": "Cho A = (-∞; 3] và B = (1; +∞). Tập hợp A ∩ B là nửa khoảng nào?", "option_a": "(-∞; 1)", "option_b": "(1; 3]", "option_c": "[1; 3)", "option_d": "(-∞; +∞)", "correct_answer": "b", "score": 15},
        {"question_id": 5, "assignment_id": 1, "question_type": "true_false", "question_text": "Tập hợp rỗng (∅) là tập hợp con của mọi tập hợp khác.", "option_a": "Đúng", "option_b": "Sai", "option_c": "", "option_d": "", "correct_answer": "a", "score": 20},
        {"question_id": 6, "assignment_id": 1, "question_type": "true_false", "question_text": "Nếu một số tự nhiên chia hết cho 6 thì chắc chắn nó chia hết cho cả 2 và 3.", "option_a": "Đúng", "option_b": "Sai", "option_c": "", "option_d": "", "correct_answer": "a", "score": 20},

        # ── Bài 2: Ngữ Văn (6 câu) ──
        {"question_id": 7, "assignment_id": 2, "question_type": "multiple_choice", "question_text": "Đoạn trích 'Chiến thắng Mtao Mxây' trích từ tác phẩm sử thi anh hùng nào sau đây?", "option_a": "Sử thi Đăm Săn (dân tộc Ê-đê)", "option_b": "Sử thi Đẻ đất đẻ nước (dân tộc Mường)", "option_c": "Sử thi Khinh Dú (dân tộc Thái)", "option_d": "Sử thi Ot Ndrông (dân tộc M'Nông)", "correct_answer": "a", "score": 15},
        {"question_id": 8, "assignment_id": 2, "question_type": "multiple_choice", "question_text": "Biện pháp tu từ nghệ thuật nổi bật nhất khi miêu tả sức mạnh và tài năng múa khiên của Đăm Săn là gì?", "option_a": "Ẩn dụ và hoán dụ tinh tế", "option_b": "Phóng đại (khoa trương) kết hợp so sánh trùng điệp", "option_c": "Tương phản đối lập gay gắt", "option_d": "Điệp từ kết hợp chơi chữ", "correct_answer": "b", "score": 15},
        {"question_id": 9, "assignment_id": 2, "question_type": "multiple_choice", "question_text": "Nhân vật dũng sĩ Hê-ra-clét (Hercules) trong Thần thoại Hy Lạp nổi tiếng với chiến công nào?", "option_a": "Lấy trộm ngọn lửa của thần Dớt trao cho loài người", "option_b": "Vượt qua 12 chiến công phi thường và đầy thử thách", "option_c": "Chém đầu nữ quỷ rắn Medusa", "option_d": "Mười năm vượt biển cả trở về quê hương I-thác", "correct_answer": "b", "score": 15},
        {"question_id": 10, "assignment_id": 2, "question_type": "multiple_choice", "question_text": "Phương thức sáng tác và lưu truyền chủ yếu của kho tàng Văn học dân gian Việt Nam là gì?", "option_a": "Khắc họa trên vách đá và trống đồng", "option_b": "Ghi chép cẩn trọng trong thư tịch cổ", "option_c": "Truyền miệng (truyền khẩu) từ thế hệ này sang thế hệ khác", "option_d": "In khắc trên mộc bản chữ Nôm", "correct_answer": "c", "score": 15},
        {"question_id": 11, "assignment_id": 2, "question_type": "true_false", "question_text": "Sử thi là thể loại tự sự dân gian quy mô đồ sộ, kể về biến cố trọng đại gắn liền vận mệnh cộng đồng.", "option_a": "Đúng", "option_b": "Sai", "option_c": "", "option_d": "", "correct_answer": "a", "score": 20},
        {"question_id": 12, "assignment_id": 2, "question_type": "true_false", "question_text": "'Thần Trụ Trời' là câu chuyện thần thoại suy nguyên giải thích nguồn gốc vũ trụ sơ khai của người Việt cổ.", "option_a": "Đúng", "option_b": "Sai", "option_c": "", "option_d": "", "correct_answer": "a", "score": 20},

        # ── Bài 3: Tiếng Anh (6 câu) ──
        {"question_id": 13, "assignment_id": 3, "question_type": "multiple_choice", "question_text": "In our family, everyone shares the ______ such as washing dishes, sweeping, and taking out the rubbish.", "option_a": "household chores", "option_b": "financial burdens", "option_c": "heavy lifting", "option_d": "breadwinner", "correct_answer": "a", "score": 15},
        {"question_id": 14, "assignment_id": 3, "question_type": "multiple_choice", "question_text": "Listen! Minh ______ the piano in his room while his mother is cooking in the kitchen.", "option_a": "plays", "option_b": "is playing", "option_c": "played", "option_d": "has played", "correct_answer": "b", "score": 15},
        {"question_id": 15, "assignment_id": 3, "question_type": "multiple_choice", "question_text": "My father is the main ______ in my family; he works hard every day to earn money and provide for us.", "option_a": "homemaker", "option_b": "breadwinner", "option_c": "housekeeper", "option_d": "babysitter", "correct_answer": "b", "score": 15},
        {"question_id": 16, "assignment_id": 3, "question_type": "multiple_choice", "question_text": "Water ______ at 100 degrees Celsius under standard atmospheric pressure.", "option_a": "boils", "option_b": "is boiling", "option_c": "boiled", "option_d": "will boil", "correct_answer": "a", "score": 15},
        {"question_id": 17, "assignment_id": 3, "question_type": "true_false", "question_text": "The sentence 'I am usually getting up early at 6 AM on weekdays' is grammatically correct for a daily routine.", "option_a": "Đúng", "option_b": "Sai", "option_c": "", "option_d": "", "correct_answer": "b", "score": 20},
        {"question_id": 18, "assignment_id": 3, "question_type": "true_false", "question_text": "The term 'homemaker' describes a person who primarily manages a home and takes care of family chores.", "option_a": "Đúng", "option_b": "Sai", "option_c": "", "option_d": "", "correct_answer": "a", "score": 20},

        # ── Bài 4: Vật Lý (6 câu) ──
        {"question_id": 19, "assignment_id": 4, "question_type": "multiple_choice", "question_text": "Hệ thức độc lập thời gian giữa gia tốc a, vận tốc ban đầu v₀, vận tốc sau v và quãng đường s là:", "option_a": "v² - v₀² = 2as", "option_b": "v - v₀ = 2as", "option_c": "v² + v₀² = 2as", "option_d": "v² - v₀² = as", "correct_answer": "a", "score": 15},
        {"question_id": 20, "assignment_id": 4, "question_type": "multiple_choice", "question_text": "Một vật rơi tự do không vận tốc đầu từ độ cao h. Thời gian rơi t chạm đất tính theo gia tốc trọng trường g là:", "option_a": "t = √(h / g)", "option_b": "t = √(2h / g)", "option_c": "t = 2h / g", "option_d": "t = √(gh)", "correct_answer": "b", "score": 15},
        {"question_id": 21, "assignment_id": 4, "question_type": "multiple_choice", "question_text": "Theo Định luật 2 Newton, độ lớn gia tốc a của một vật có khối lượng m chịu hợp lực F tác dụng là:", "option_a": "a = F / m", "option_b": "a = F × m", "option_c": "a = m / F", "option_d": "a = F² / m", "correct_answer": "a", "score": 15},
        {"question_id": 22, "assignment_id": 4, "question_type": "multiple_choice", "question_text": "Quán tính là tính chất của mọi vật có xu hướng bảo toàn:", "option_a": "Vận tốc của vật cả về hướng và độ lớn", "option_b": "Khối lượng riêng của vật", "option_c": "Gia tốc chuyển động của vật", "option_d": "Vị trí tương đối của vật trong không gian", "correct_answer": "a", "score": 15},
        {"question_id": 23, "assignment_id": 4, "question_type": "true_false", "question_text": "Lực tác dụng và lực phản lực trong Định luật 3 Newton cùng tác dụng lên một vật nên chúng triệt tiêu nhau.", "option_a": "Đúng", "option_b": "Sai", "option_c": "", "option_d": "", "correct_answer": "b", "score": 20},
        {"question_id": 24, "assignment_id": 4, "question_type": "true_false", "question_text": "Sự rơi tự do là chuyển động thẳng nhanh dần đều theo phương thẳng đứng với chiều từ trên xuống dưới.", "option_a": "Đúng", "option_b": "Sai", "option_c": "", "option_d": "", "correct_answer": "a", "score": 20},
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
