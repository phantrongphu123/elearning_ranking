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
            "title": "Khảo Thí Hán Ngữ 1 - Ngữ Âm Pinyin & Chào Hỏi Sơ Cấp",
            "description": "Kiểm tra ngữ âm Pinyin, thanh điệu, các nét cơ bản và câu chào hỏi thường nhật trong Tiếng Trung.",
            "subject": "Tiếng Trung",
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
            "title": "Khảo Thí Hán Ngữ 2 - Giới Thiệu Bản Thân & Gia Đình",
            "description": "Khảo hạch từ vựng xưng hô, quốc tịch, tuổi tác và các thành viên gia đình trong Tiếng Trung.",
            "subject": "Tiếng Trung",
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
            "title": "Khảo Thí Hán Ngữ 3 - Số Đếm, Thời Gian & Mua Sắm",
            "description": "Kiểm tra kỹ năng diễn đạt giờ giấc, ngày tháng, đếm số và hỏi giá khi mua sắm bằng Tiếng Trung.",
            "subject": "Tiếng Trung",
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
            "title": "Khảo Thí Hán Ngữ 4 - Ngữ Pháp & Văn Hóa Cung Đình",
            "description": "Kiểm tra ngữ pháp câu chữ 在, phương vị từ và xưng hô kinh điển trong hoàng cung Trung Hoa.",
            "subject": "Tiếng Trung",
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
        # ── Bài 1: Ngữ Âm Pinyin & Chào Hỏi Sơ Cấp (6 câu) ──
        {"question_id": 1, "assignment_id": 1, "question_type": "multiple_choice", "question_text": "Phiên âm Pinyin chính xác của chữ '你好' (Xin chào) là gì?", "option_a": "nǐ hǎo", "option_b": "nǐ hào", "option_c": "ní hāo", "option_d": "nì hǎo", "correct_answer": "a", "score": 15},
        {"question_id": 2, "assignment_id": 1, "question_type": "multiple_choice", "question_text": "Khi hai âm tiết mang thanh 3 đi liền nhau (ví dụ: 你好 nǐ hǎo), thanh thứ nhất sẽ biến điệu thành thanh mấy?", "option_a": "Thanh 1 (âm cao bằng)", "option_b": "Thanh 2 (dấu sắc)", "option_c": "Thanh 4 (hạ giọng dứt khoát)", "option_d": "Giữ nguyên thanh 3", "correct_answer": "b", "score": 15},
        {"question_id": 3, "assignment_id": 1, "question_type": "multiple_choice", "question_text": "Câu 'Cảm ơn bạn' trong tiếng Trung viết bằng chữ Hán là:", "option_a": "对不起", "option_b": "谢谢你", "option_c": "再见", "option_d": "没关系", "correct_answer": "b", "score": 15},
        {"question_id": 4, "assignment_id": 1, "question_type": "multiple_choice", "question_text": "Khi đối phương nói '对不起' (Duìbuqǐ - Xin lỗi), cách đáp lại lịch sự nhất là:", "option_a": "不客气 (Bú kèqi)", "option_b": "没关系 (Méi guānxi)", "option_c": "谢谢 (Xièxie)", "option_d": "再见 (Zàijiàn)", "correct_answer": "b", "score": 15},
        {"question_id": 5, "assignment_id": 1, "question_type": "true_false", "question_text": "Các chữ Hán '一' (số 1), '二' (số 2), '三' (số 3) đều được cấu tạo từ nét ngang (横 - héng).", "option_a": "Đúng", "option_b": "Sai", "option_c": "", "option_d": "", "correct_answer": "a", "score": 20},
        {"question_id": 6, "assignment_id": 1, "question_type": "true_false", "question_text": "Tiếng Trung phổ thông (Mandarin) có tất cả 6 thanh điệu cơ bản.", "option_a": "Đúng", "option_b": "Sai", "option_c": "", "option_d": "", "correct_answer": "b", "score": 20},

        # ── Bài 2: Giới Thiệu Bản Thân & Gia Đình (6 câu) ──
        {"question_id": 7, "assignment_id": 2, "question_type": "multiple_choice", "question_text": "Để hỏi tên đối phương một cách tự nhiên và lịch sự, câu nào sau đây là đúng nhất?", "option_a": "你叫什么名字？ (Nǐ jiào shénme míngzi?)", "option_b": "你是谁的名字？ (Nǐ shì shéi de míngzi?)", "option_c": "你名字叫哪儿？ (Nǐ míngzi jiào nǎr?)", "option_d": "你叫谁名字？ (Nǐ jiào shéi míngzi?)", "correct_answer": "a", "score": 15},
        {"question_id": 8, "assignment_id": 2, "question_type": "multiple_choice", "question_text": "Câu '我是越南人' (Wǒ shì Yuènán rén) có nghĩa tiếng Việt là gì?", "option_a": "Tôi là người Trung Quốc", "option_b": "Tôi là người Việt Nam", "option_c": "Tôi học tiếng Việt Nam", "option_d": "Tôi sống ở Việt Nam", "correct_answer": "b", "score": 15},
        {"question_id": 9, "assignment_id": 2, "question_type": "multiple_choice", "question_text": "Từ nào sau đây có nghĩa là 'Thầy cô giáo' trong tiếng Trung?", "option_a": "学生 (xuésheng)", "option_b": "医生 (yīshēng)", "option_c": "老师 (lǎoshī)", "option_d": "朋友 (péngyou)", "correct_answer": "c", "score": 15},
        {"question_id": 10, "assignment_id": 2, "question_type": "multiple_choice", "question_text": "Từ chỉ người 'Mẹ' trong gia đình viết bằng chữ Hán là:", "option_a": "爸爸 (bàba)", "option_b": "妈妈 (māma)", "option_c": "哥哥 (gēge)", "option_d": "姐姐 (jiějie)", "correct_answer": "b", "score": 15},
        {"question_id": 11, "assignment_id": 2, "question_type": "true_false", "question_text": "Đại từ nghi vấn '几' (jǐ - mấy) thường dùng để hỏi số lượng nhỏ hơn 10 (ví dụ: 你家有几口人？).", "option_a": "Đúng", "option_b": "Sai", "option_c": "", "option_d": "", "correct_answer": "a", "score": 20},
        {"question_id": 12, "assignment_id": 2, "question_type": "true_false", "question_text": "Từ '他们' (tāmen) chỉ dùng riêng cho nhóm toàn nữ giới.", "option_a": "Đúng", "option_b": "Sai", "option_c": "", "option_d": "", "correct_answer": "b", "score": 20},

        # ── Bài 3: Số Đếm, Thời Gian & Mua Sắm (6 câu) ──
        {"question_id": 13, "assignment_id": 3, "question_type": "multiple_choice", "question_text": "Câu hỏi 'Bao nhiêu tiền một cân?' khi mua hoa quả trong tiếng Trung là:", "option_a": "多少钱一斤？ (Duōshao qián yì jīn?)", "option_b": "几块钱一点？ (Jǐ kuài qián yì diǎn?)", "option_c": "怎么钱一斤？ (Zěnme qián yì jīn?)", "option_d": "为什么多少钱？ (Wèishénme duōshao qián?)", "correct_answer": "a", "score": 15},
        {"question_id": 14, "assignment_id": 3, "question_type": "multiple_choice", "question_text": "Câu '现在八点半' (Xiànzài bā diǎn bàn) biểu thị mấy giờ?", "option_a": "Hiện tại 7 giờ 30 phút", "option_b": "Hiện tại 8 giờ 30 phút", "option_c": "Hiện tại 8 giờ 15 phút", "option_d": "Hiện tại 9 giờ kém 15 phút", "correct_answer": "b", "score": 15},
        {"question_id": 15, "assignment_id": 3, "question_type": "multiple_choice", "question_text": "Thứ tự biểu đạt thời gian (năm, tháng, ngày, giờ) trong tiếng Trung tuân theo quy tắc nào?", "option_a": "Đơn vị nhỏ đứng trước, lớn đứng sau (Giờ -> Ngày -> Tháng -> Năm)", "option_b": "Đơn vị lớn đứng trước, nhỏ đứng sau (Năm -> Tháng -> Ngày -> Giờ)", "option_c": "Hoàn toàn giống thứ tự tiếng Việt (Ngày -> Tháng -> Năm)", "option_d": "Sắp xếp ngẫu nhiên không có quy tắc", "correct_answer": "b", "score": 15},
        {"question_id": 16, "assignment_id": 3, "question_type": "multiple_choice", "question_text": "Số 88 trong tiếng Trung được đọc và viết là:", "option_a": "二十八 (èr shí bā)", "option_b": "八十八 (bā shí bā)", "option_c": "八百八 (bā bǎi bā)", "option_d": "十八八 (shí bā bā)", "correct_answer": "b", "score": 15},
        {"question_id": 17, "assignment_id": 3, "question_type": "true_false", "question_text": "Lượng từ thông dụng và đa năng nhất trong tiếng Trung là chữ '个' (gè).", "option_a": "Đúng", "option_b": "Sai", "option_c": "", "option_d": "", "correct_answer": "a", "score": 20},
        {"question_id": 18, "assignment_id": 3, "question_type": "true_false", "question_text": "Khi muốn mặc cả xin bớt giá, ta có thể nói: '太贵了，便宜一点儿吧！' (Tài guì le, piányi yìdiǎnr ba!).", "option_a": "Đúng", "option_b": "Sai", "option_c": "", "option_d": "", "correct_answer": "a", "score": 20},

        # ── Bài 4: Ngữ Pháp & Văn Hóa Cung Đình (6 câu) ──
        {"question_id": 19, "assignment_id": 4, "question_type": "multiple_choice", "question_text": "Trong hoàng cung triều đình Trung Hoa xưa, Hoàng đế thường tự xưng là gì?", "option_a": "奴才 (Núcai)", "option_b": "朕 (Zhèn)", "option_c": "微臣 (Wēichén)", "option_d": "本宫 (Běngōng)", "correct_answer": "b", "score": 15},
        {"question_id": 20, "assignment_id": 4, "question_type": "multiple_choice", "question_text": "Câu chúc tụng Hoàng đế vạn thọ vô cương kinh điển trong hoàng triều là:", "option_a": "岁岁平安 (Suì suì píng'ān)", "option_b": "吾皇万岁万岁万万岁 (Wú huáng wànsuì wànsuì wànwànsuì)", "option_c": "恭喜发财 (Gōngxǐ fācái)", "option_d": "一路顺风 (Yílù shùnfēng)", "correct_answer": "b", "score": 15},
        {"question_id": 21, "assignment_id": 4, "question_type": "multiple_choice", "question_text": "Điền giới từ thích hợp vào chỗ trống: '我 ______ 图书馆看书。' (Tôi đọc sách ở thư viện).", "option_a": "在 (zài)", "option_b": "有 (yǒu)", "option_c": "是 (shì)", "option_d": "从 (cóng)", "correct_answer": "a", "score": 15},
        {"question_id": 22, "assignment_id": 4, "question_type": "multiple_choice", "question_text": "Chữ '吃' (chī - Ăn) có bộ thủ nào ở phía bên trái liên quan đến miệng?", "option_a": "Bộ Khẩu (口)", "option_b": "Bộ Thủy (氵)", "option_c": "Bộ Mộc (木)", "option_d": "Bộ Hỏa (火)", "correct_answer": "a", "score": 15},
        {"question_id": 23, "assignment_id": 4, "question_type": "true_false", "question_text": "Cấu trúc câu biểu đạt địa điểm hành động trong tiếng Trung là: 'Chủ ngữ + 在 + Nơi chốn + Động từ' (ví dụ: 我在学校学汉语).", "option_a": "Đúng", "option_b": "Sai", "option_c": "", "option_d": "", "correct_answer": "a", "score": 20},
        {"question_id": 24, "assignment_id": 4, "question_type": "true_false", "question_text": "Chữ '国' trong '中国' (Trung Quốc) có bộ Vi (囗) bao bọc xung quanh, biểu thị biên giới bờ cõi bờ cõi lãnh thổ.", "option_a": "Đúng", "option_b": "Sai", "option_c": "", "option_d": "", "correct_answer": "a", "score": 20},
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
