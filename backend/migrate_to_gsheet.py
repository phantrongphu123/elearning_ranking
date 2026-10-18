"""
Script khởi tạo Google Sheet: tạo 14 tabs với header + seed mock data.
Chay: python migrate_to_gsheet.py
"""

import sys
import os
sys.stdout.reconfigure(encoding="utf-8")
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import json
import time
from datetime import datetime, timedelta

import gspread
from google.oauth2.service_account import Credentials
from app.core.security import hash_password
from app.services.excel_service import SHEET_COLUMNS

# ── Cấu hình ────────────────────────────────────────────────
SHEET_ID = "1Abfw5CMLtseRVwoXOgTjnkEpjGkzHhkg5nD4PcBOExk"
CREDENTIALS_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "service_account.json")
SCOPES = [
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive",
]

print("🏯 Khởi tạo Google Sheet cho Hoàng Cung Học Đường...\n")

# ── Kết nối ──────────────────────────────────────────────────
creds = Credentials.from_service_account_file(CREDENTIALS_FILE, scopes=SCOPES)
gc = gspread.authorize(creds)
ss = gc.open_by_key(SHEET_ID)
print(f"✅ Kết nối thành công tới: {ss.title}\n")


def get_or_create_worksheet(title: str, rows: int = 2000, cols: int = 30) -> gspread.Worksheet:
    try:
        return ss.worksheet(title)
    except gspread.exceptions.WorksheetNotFound:
        ws = ss.add_worksheet(title=title, rows=rows, cols=cols)
        time.sleep(1)  # tránh rate limit khi tạo nhiều sheet liên tiếp
        return ws


def write_sheet(title: str, rows_data: list):
    """Ghi header + data vào worksheet, xóa dữ liệu cũ trước."""
    headers = SHEET_COLUMNS[title]
    ws = get_or_create_worksheet(title)
    ws.clear()
    time.sleep(0.5)
    all_rows = [headers] + [[str(row.get(h, "")) for h in headers] for row in rows_data]
    ws.update(all_rows, value_input_option="RAW")
    print(f"  ✔  {title}: {len(rows_data)} dòng")
    time.sleep(1)  # 1s giữa mỗi request tránh quota


# ── Xóa sheet mặc định 'Trang tính1' nếu còn ────────────────
for ws in ss.worksheets():
    if ws.title in ("Trang tính1", "Sheet1"):
        try:
            ss.del_worksheet(ws)
            print(f"🗑  Đã xóa sheet mặc định: {ws.title}")
        except Exception:
            pass
time.sleep(1)

now = datetime.now()

# ══════════════════════════════════════════════════════════════
# 1. USERS
# ══════════════════════════════════════════════════════════════
print("\n📋 Đang ghi sheet Users...")
users = [
    {"user_id": 1, "username": "admin",      "password_hash": hash_password("admin123"),
     "full_name": "Hoàng Đế - Admin",  "role": "admin",   "student_id": "", "class_id": "", "status": "active", "created_at": now.isoformat()},
    {"user_id": 2, "username": "teacher01",  "password_hash": hash_password("teacher123"),
     "full_name": "Nguyễn Thị Lan (GVCN 10A4)", "role": "teacher", "student_id": "", "class_id": "1", "status": "active", "created_at": now.isoformat()},
]

from app.services.rank_service import calculate_rank

student_names = [
    ("Ngô Vĩnh Thái", "male"),
    ("Trương Quốc Tiến", "male"),
    ("Nguyễn Minh Anh", "female"),
    ("Hoàng Gia Hân", "female"),
    ("Lê Minh Tuệ", "female"),
    ("Trần Ngọc Phương Anh", "female"),
    ("Lê Phương Linh", "female"),
    ("Nguyễn Khánh Uyên", "female"),
    ("Phạm Gia Bách", "male"),
    ("Đinh Hoàng Bảo Linh", "female"),
    ("Nguyễn Ngân Nguyệt", "female"),
    ("Nguyễn Xuân Thủy", "male"),
    ("Hoàng Thanh Tùng", "male"),
    ("Dương Nguyễn Vân Khánh", "female"),
    ("Võ Minh Nam", "male"),
    ("Nguyễn Gia Khánh", "male"),
    ("Nguyễn Nhã Linh", "female"),
    ("Nguyễn Minh Khuê", "female"),
]

student_scores = [
    1350, 980, 380, 1550, 540, 1220, 870, 650, 720,
    250, 160, 320, 450, 120, 200, 80, 50, 30
]

for i, ((name, gender), score) in enumerate(zip(student_names, student_scores)):
    sid = i + 1
    uid = sid + 2  # user_id bắt đầu sau admin (1) và teacher01 (2)
    users.append({
        "user_id": uid, "username": f"student{sid:02d}", "password_hash": hash_password("student123"),
        "full_name": name, "role": "student", "student_id": sid, "class_id": 1,
        "status": "active", "created_at": now.isoformat(),
    })

write_sheet("Users", users)

# ══════════════════════════════════════════════════════════════
# 2. HOC SINH
# ══════════════════════════════════════════════════════════════
print("\n📋 Đang ghi sheet HocSinh...")
hoc_sinh = []
for i, ((name, gender), score) in enumerate(zip(student_names, student_scores)):
    sid = i + 1
    rank_info = calculate_rank(score, gender)
    hoc_sinh.append({
        "student_id": sid, "student_code": f"HS{sid:04d}", "full_name": name,
        "date_of_birth": "2009-01-01", "gender": gender, "class_id": 1,
        "total_score": score, "rank": rank_info["rank"], "rank_level": rank_info["rank_level"],
        "avatar": "", "status": "active", "created_at": now.isoformat(),
    })
write_sheet("HocSinh", hoc_sinh)

# ══════════════════════════════════════════════════════════════
# 3. LOP HOC
# ══════════════════════════════════════════════════════════════
print("\n📋 Đang ghi sheet LopHoc...")
lop_hoc = [
    {"class_id": 1, "class_code": "10A4", "class_name": "Lớp 10A4 - Càn Long Cung", "teacher_id": 2, "school_year": "2025-2026", "status": "active"},
]
write_sheet("LopHoc", lop_hoc)

# ══════════════════════════════════════════════════════════════
# 4. BAI TAP
# ══════════════════════════════════════════════════════════════
print("\n📋 Đang ghi sheet BaiTap...")
bai_tap = [
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
write_sheet("BaiTap", bai_tap)

# ══════════════════════════════════════════════════════════════
# 5. CAU HOI
# ══════════════════════════════════════════════════════════════
print("\n📋 Đang ghi sheet CauHoi...")
cau_hoi = [
    # ── Bài 1: Toán (6 câu) ──
    {
        "question_id": 1, "assignment_id": 1, "question_type": "multiple_choice",
        "question_text": "Trong các câu sau, câu nào là một mệnh đề toán học?",
        "option_a": "Hôm nay trời đẹp quá!",
        "option_b": "15 là số nguyên tố.",
        "option_c": "Bạn học lớp nào vậy?",
        "option_d": "x + 1 > 0.",
        "correct_answer": "b", "score": 15
    },
    {
        "question_id": 2, "assignment_id": 1, "question_type": "multiple_choice",
        "question_text": "Mệnh đề phủ định của mệnh đề: '∀x ∈ ℝ, x² - x + 7 > 0' là:",
        "option_a": "∃x ∈ ℝ, x² - x + 7 ≤ 0",
        "option_b": "∀x ∈ ℝ, x² - x + 7 < 0",
        "option_c": "∃x ∈ ℝ, x² - x + 7 < 0",
        "option_d": "∃x ∈ ℝ, x² - x + 7 > 0",
        "correct_answer": "a", "score": 15
    },
    {
        "question_id": 3, "assignment_id": 1, "question_type": "multiple_choice",
        "question_text": "Cho tập hợp A = {1; 2; 3; 4} và B = {3; 4; 5; 6}. Phép giao A ∩ B là tập hợp nào?",
        "option_a": "{1; 2}",
        "option_b": "{3; 4}",
        "option_c": "{1; 2; 3; 4; 5; 6}",
        "option_d": "{5; 6}",
        "correct_answer": "b", "score": 15
    },
    {
        "question_id": 4, "assignment_id": 1, "question_type": "multiple_choice",
        "question_text": "Cho A = (-∞; 3] và B = (1; +∞). Tập hợp A ∩ B là nửa khoảng nào?",
        "option_a": "(-∞; 1)",
        "option_b": "(1; 3]",
        "option_c": "[1; 3)",
        "option_d": "(-∞; +∞)",
        "correct_answer": "b", "score": 15
    },
    {
        "question_id": 5, "assignment_id": 1, "question_type": "true_false",
        "question_text": "Tập hợp rỗng (∅) là tập hợp con của mọi tập hợp khác.",
        "option_a": "Đúng", "option_b": "Sai", "option_c": "", "option_d": "",
        "correct_answer": "a", "score": 20
    },
    {
        "question_id": 6, "assignment_id": 1, "question_type": "true_false",
        "question_text": "Nếu một số tự nhiên chia hết cho 6 thì chắc chắn nó chia hết cho cả 2 và 3.",
        "option_a": "Đúng", "option_b": "Sai", "option_c": "", "option_d": "",
        "correct_answer": "a", "score": 20
    },

    # ── Bài 2: Ngữ Văn (6 câu) ──
    {
        "question_id": 7, "assignment_id": 2, "question_type": "multiple_choice",
        "question_text": "Đoạn trích 'Chiến thắng Mtao Mxây' trích từ tác phẩm sử thi anh hùng nào sau đây?",
        "option_a": "Sử thi Đăm Săn (dân tộc Ê-đê)",
        "option_b": "Sử thi Đẻ đất đẻ nước (dân tộc Mường)",
        "option_c": "Sử thi Khinh Dú (dân tộc Thái)",
        "option_d": "Sử thi Ot Ndrông (dân tộc M'Nông)",
        "correct_answer": "a", "score": 15
    },
    {
        "question_id": 8, "assignment_id": 2, "question_type": "multiple_choice",
        "question_text": "Biện pháp tu từ nghệ thuật nổi bật nhất khi miêu tả sức mạnh và tài năng múa khiên của Đăm Săn là gì?",
        "option_a": "Ẩn dụ và hoán dụ tinh tế",
        "option_b": "Phóng đại (khoa trương) kết hợp so sánh trùng điệp",
        "option_c": "Tương phản đối lập gay gắt",
        "option_d": "Điệp từ kết hợp chơi chữ",
        "correct_answer": "b", "score": 15
    },
    {
        "question_id": 9, "assignment_id": 2, "question_type": "multiple_choice",
        "question_text": "Nhân vật dũng sĩ Hê-ra-clét (Hercules) trong Thần thoại Hy Lạp nổi tiếng với chiến công nào?",
        "option_a": "Lấy trộm ngọn lửa của thần Dớt trao cho loài người",
        "option_b": "Vượt qua 12 chiến công phi thường và đầy thử thách",
        "option_c": "Chém đầu nữ quỷ rắn Medusa",
        "option_d": "Mười năm vượt biển cả trở về quê hương I-thác",
        "correct_answer": "b", "score": 15
    },
    {
        "question_id": 10, "assignment_id": 2, "question_type": "multiple_choice",
        "question_text": "Phương thức sáng tác và lưu truyền chủ yếu của kho tàng Văn học dân gian Việt Nam là gì?",
        "option_a": "Khắc họa trên vách đá và trống đồng",
        "option_b": "Ghi chép cẩn trọng trong thư tịch cổ",
        "option_c": "Truyền miệng (truyền khẩu) từ thế hệ này sang thế hệ khác",
        "option_d": "In khắc trên mộc bản chữ Nôm",
        "correct_answer": "c", "score": 15
    },
    {
        "question_id": 11, "assignment_id": 2, "question_type": "true_false",
        "question_text": "Sử thi là thể loại tự sự dân gian quy mô đồ sộ, kể về biến cố trọng đại gắn liền vận mệnh cộng đồng.",
        "option_a": "Đúng", "option_b": "Sai", "option_c": "", "option_d": "",
        "correct_answer": "a", "score": 20
    },
    {
        "question_id": 12, "assignment_id": 2, "question_type": "true_false",
        "question_text": "'Thần Trụ Trời' là câu chuyện thần thoại suy nguyên giải thích nguồn gốc vũ trụ sơ khai của người Việt cổ.",
        "option_a": "Đúng", "option_b": "Sai", "option_c": "", "option_d": "",
        "correct_answer": "a", "score": 20
    },

    # ── Bài 3: Tiếng Anh (6 câu) ──
    {
        "question_id": 13, "assignment_id": 3, "question_type": "multiple_choice",
        "question_text": "In our family, everyone shares the ______ such as washing dishes, sweeping, and taking out the rubbish.",
        "option_a": "household chores",
        "option_b": "financial burdens",
        "option_c": "heavy lifting",
        "option_d": "breadwinner",
        "correct_answer": "a", "score": 15
    },
    {
        "question_id": 14, "assignment_id": 3, "question_type": "multiple_choice",
        "question_text": "Listen! Minh ______ the piano in his room while his mother is cooking in the kitchen.",
        "option_a": "plays",
        "option_b": "is playing",
        "option_c": "played",
        "option_d": "has played",
        "correct_answer": "b", "score": 15
    },
    {
        "question_id": 15, "assignment_id": 3, "question_type": "multiple_choice",
        "question_text": "My father is the main ______ in my family; he works hard every day to earn money and provide for us.",
        "option_a": "homemaker",
        "option_b": "breadwinner",
        "option_c": "housekeeper",
        "option_d": "babysitter",
        "correct_answer": "b", "score": 15
    },
    {
        "question_id": 16, "assignment_id": 3, "question_type": "multiple_choice",
        "question_text": "Water ______ at 100 degrees Celsius under standard atmospheric pressure.",
        "option_a": "boils",
        "option_b": "is boiling",
        "option_c": "boiled",
        "option_d": "will boil",
        "correct_answer": "a", "score": 15
    },
    {
        "question_id": 17, "assignment_id": 3, "question_type": "true_false",
        "question_text": "The sentence 'I am usually getting up early at 6 AM on weekdays' is grammatically correct for a daily routine.",
        "option_a": "Đúng", "option_b": "Sai", "option_c": "", "option_d": "",
        "correct_answer": "b", "score": 20
    },
    {
        "question_id": 18, "assignment_id": 3, "question_type": "true_false",
        "question_text": "The term 'homemaker' describes a person who primarily manages a home and takes care of family chores.",
        "option_a": "Đúng", "option_b": "Sai", "option_c": "", "option_d": "",
        "correct_answer": "a", "score": 20
    },

    # ── Bài 4: Vật Lý (6 câu) ──
    {
        "question_id": 19, "assignment_id": 4, "question_type": "multiple_choice",
        "question_text": "Hệ thức độc lập thời gian giữa gia tốc a, vận tốc ban đầu v₀, vận tốc sau v và quãng đường s là:",
        "option_a": "v² - v₀² = 2as",
        "option_b": "v - v₀ = 2as",
        "option_c": "v² + v₀² = 2as",
        "option_d": "v² - v₀² = as",
        "correct_answer": "a", "score": 15
    },
    {
        "question_id": 20, "assignment_id": 4, "question_type": "multiple_choice",
        "question_text": "Một vật rơi tự do không vận tốc đầu từ độ cao h. Thời gian rơi t chạm đất tính theo gia tốc trọng trường g là:",
        "option_a": "t = √(h / g)",
        "option_b": "t = √(2h / g)",
        "option_c": "t = 2h / g",
        "option_d": "t = √(gh)",
        "correct_answer": "b", "score": 15
    },
    {
        "question_id": 21, "assignment_id": 4, "question_type": "multiple_choice",
        "question_text": "Theo Định luật 2 Newton, độ lớn gia tốc a của một vật có khối lượng m chịu hợp lực F tác dụng là:",
        "option_a": "a = F / m",
        "option_b": "a = F × m",
        "option_c": "a = m / F",
        "option_d": "a = F² / m",
        "correct_answer": "a", "score": 15
    },
    {
        "question_id": 22, "assignment_id": 4, "question_type": "multiple_choice",
        "question_text": "Quán tính là tính chất của mọi vật có xu hướng bảo toàn:",
        "option_a": "Vận tốc của vật cả về hướng và độ lớn",
        "option_b": "Khối lượng riêng của vật",
        "option_c": "Gia tốc chuyển động của vật",
        "option_d": "Vị trí tương đối của vật trong không gian",
        "correct_answer": "a", "score": 15
    },
    {
        "question_id": 23, "assignment_id": 4, "question_type": "true_false",
        "question_text": "Lực tác dụng và lực phản lực trong Định luật 3 Newton cùng tác dụng lên một vật nên chúng triệt tiêu nhau.",
        "option_a": "Đúng", "option_b": "Sai", "option_c": "", "option_d": "",
        "correct_answer": "b", "score": 20
    },
    {
        "question_id": 24, "assignment_id": 4, "question_type": "true_false",
        "question_text": "Sự rơi tự do là chuyển động thẳng nhanh dần đều theo phương thẳng đứng với chiều từ trên xuống dưới.",
        "option_a": "Đúng", "option_b": "Sai", "option_c": "", "option_d": "",
        "correct_answer": "a", "score": 20
    },
]
write_sheet("CauHoi", cau_hoi)

# ══════════════════════════════════════════════════════════════
# 6 - 14. CÁC SHEET CÒN LẠI (khởi tạo rỗng, chỉ có header)
# ══════════════════════════════════════════════════════════════
empty_sheets = ["BaiNop", "ChiTietBaiNop", "Diem", "LichSuNopBai",
                "RankHistory", "DiemDanh", "ThanhTich", "ThongBao"]

print("\n📋 Đang khởi tạo các sheet còn lại (trống, chỉ header)...")
for sheet_name in empty_sheets:
    write_sheet(sheet_name, [])

# ── RankConfig ──────────────────────────────────────────────
print("\n📋 Đang ghi sheet RankConfig...")
rank_config = [
    {"rank_id": i+1, "min_score": r["min_score"], "max_score": r["max_score"],
     "male_name": r["male"], "female_name": r["female"],
     "level": r["level"], "color": r["color"], "icon": r["icon"]}
    for i, r in enumerate([
        {"min_score": 0,    "max_score": 99,    "male": "Nô Tài",      "female": "Cung Nữ",         "level": 1, "color": "#8B7355", "icon": "🪨"},
        {"min_score": 100,  "max_score": 300,   "male": "Thường Tại",  "female": "Đáp Ứng",          "level": 2, "color": "#7B68EE", "icon": "💜"},
        {"min_score": 301,  "max_score": 500,   "male": "Quý Nhân",    "female": "Quý Nhân",          "level": 3, "color": "#4682B4", "icon": "💎"},
        {"min_score": 501,  "max_score": 800,   "male": "Tần",         "female": "Phi",               "level": 4, "color": "#3CB371", "icon": "🌺"},
        {"min_score": 801,  "max_score": 1200,  "male": "Quý Phi",     "female": "Hoàng Quý Phi",     "level": 5, "color": "#FF8C00", "icon": "✨"},
        {"min_score": 1201, "max_score": 1500,  "male": "Tể Tướng",    "female": "Hoàng Hậu",         "level": 6, "color": "#DC143C", "icon": "👑"},
        {"min_score": 1501, "max_score": 999999,"male": "Hoàng Đế",    "female": "Thái Hậu",          "level": 7, "color": "#FFD700", "icon": "🏆"},
    ])
]
write_sheet("RankConfig", rank_config)

print("\n🎉 HOÀN THÀNH! Toàn bộ 14 sheets đã được khởi tạo trên Google Sheet.")
print(f"   Link: https://docs.google.com/spreadsheets/d/{SHEET_ID}/edit")
print("\nTài khoản đăng nhập mẫu:")
print("  Admin:    admin / admin123")
print("  Giáo viên: teacher01 / teacher123")
print("  Học sinh: student01 / student123")
