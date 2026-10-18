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
    {"assignment_id": 1, "title": "Tấu Chương Toán Số 1", "description": "Phép tính cơ bản",
     "subject": "Toán", "class_id": 1, "teacher_id": 2,
     "created_at": now.isoformat(), "start_time": now.isoformat(),
     "deadline": (now + timedelta(days=7)).isoformat(),
     "max_score": 100, "bonus_score": 10, "penalty_score": 5, "status": "active"},
    {"assignment_id": 2, "title": "Tấu Chương Văn Số 1", "description": "Phân tích đoạn văn",
     "subject": "Ngữ Văn", "class_id": 1, "teacher_id": 2,
     "created_at": now.isoformat(), "start_time": now.isoformat(),
     "deadline": (now + timedelta(days=5)).isoformat(),
     "max_score": 100, "bonus_score": 5, "penalty_score": 10, "status": "active"},
    {"assignment_id": 3, "title": "Tấu Chương Lý Số 1", "description": "Định luật Newton",
     "subject": "Vật Lý", "class_id": 1, "teacher_id": 2,
     "created_at": now.isoformat(), "start_time": now.isoformat(),
     "deadline": (now + timedelta(days=3)).isoformat(),
     "max_score": 100, "bonus_score": 5, "penalty_score": 5, "status": "active"},
]
write_sheet("BaiTap", bai_tap)

# ══════════════════════════════════════════════════════════════
# 5. CAU HOI
# ══════════════════════════════════════════════════════════════
print("\n📋 Đang ghi sheet CauHoi...")
cau_hoi = [
    # BaiTap 1
    {"question_id": 1, "assignment_id": 1, "question_type": "multiple_choice",
     "question_text": "2 + 2 = ?", "option_a": "3", "option_b": "4", "option_c": "5", "option_d": "6",
     "correct_answer": "b", "score": 25},
    {"question_id": 2, "assignment_id": 1, "question_type": "multiple_choice",
     "question_text": "10 × 10 = ?", "option_a": "10", "option_b": "100", "option_c": "1000", "option_d": "110",
     "correct_answer": "b", "score": 25},
    {"question_id": 3, "assignment_id": 1, "question_type": "true_false",
     "question_text": "Số nguyên tố là số chỉ chia hết cho 1 và chính nó?", "option_a": "Đúng", "option_b": "Sai",
     "option_c": "", "option_d": "", "correct_answer": "a", "score": 50},
    # BaiTap 2
    {"question_id": 4, "assignment_id": 2, "question_type": "multiple_choice",
     "question_text": "Tác giả Truyện Kiều là ai?", "option_a": "Nguyễn Trãi", "option_b": "Nguyễn Du",
     "option_c": "Hồ Xuân Hương", "option_d": "Đoàn Thị Điểm", "correct_answer": "b", "score": 50},
    {"question_id": 5, "assignment_id": 2, "question_type": "multiple_choice",
     "question_text": "Truyện Kiều có bao nhiêu câu thơ lục bát?", "option_a": "2254", "option_b": "3254",
     "option_c": "1254", "option_d": "4254", "correct_answer": "b", "score": 50},
    # BaiTap 3
    {"question_id": 6, "assignment_id": 3, "question_type": "multiple_choice",
     "question_text": "Định luật 1 Newton phát biểu về điều gì?", "option_a": "Quán tính", "option_b": "Gia tốc",
     "option_c": "Lực phản lực", "option_d": "Hấp dẫn", "correct_answer": "a", "score": 50},
    {"question_id": 7, "assignment_id": 3, "question_type": "true_false",
     "question_text": "F = ma là biểu thức định luật 2 Newton?", "option_a": "Đúng", "option_b": "Sai",
     "option_c": "", "option_d": "", "correct_answer": "a", "score": 50},
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
