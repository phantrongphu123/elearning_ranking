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
write_sheet("BaiTap", bai_tap)

# ══════════════════════════════════════════════════════════════
# 5. CAU HOI
# ══════════════════════════════════════════════════════════════
print("\n📋 Đang ghi sheet CauHoi...")
cau_hoi = [
    # ── Bài 1: Ngữ Âm Pinyin & Chào Hỏi Sơ Cấp (6 câu) ──
    {
        "question_id": 1, "assignment_id": 1, "question_type": "multiple_choice",
        "question_text": "Phiên âm Pinyin chính xác của chữ '你好' (Xin chào) là gì?",
        "option_a": "nǐ hǎo",
        "option_b": "nǐ hào",
        "option_c": "ní hāo",
        "option_d": "nì hǎo",
        "correct_answer": "a", "score": 15
    },
    {
        "question_id": 2, "assignment_id": 1, "question_type": "multiple_choice",
        "question_text": "Khi hai âm tiết mang thanh 3 đi liền nhau (ví dụ: 你好 nǐ hǎo), thanh thứ nhất sẽ biến điệu thành thanh mấy?",
        "option_a": "Thanh 1 (âm cao bằng)",
        "option_b": "Thanh 2 (dấu sắc)",
        "option_c": "Thanh 4 (hạ giọng dứt khoát)",
        "option_d": "Giữ nguyên thanh 3",
        "correct_answer": "b", "score": 15
    },
    {
        "question_id": 3, "assignment_id": 1, "question_type": "multiple_choice",
        "question_text": "Câu 'Cảm ơn bạn' trong tiếng Trung viết bằng chữ Hán là:",
        "option_a": "对不起",
        "option_b": "谢谢你",
        "option_c": "再见",
        "option_d": "没关系",
        "correct_answer": "b", "score": 15
    },
    {
        "question_id": 4, "assignment_id": 1, "question_type": "multiple_choice",
        "question_text": "Khi đối phương nói '对不起' (Duìbuqǐ - Xin lỗi), cách đáp lại lịch sự nhất là:",
        "option_a": "不客气 (Bú kèqi)",
        "option_b": "没关系 (Méi guānxi)",
        "option_c": "谢谢 (Xièxie)",
        "option_d": "再见 (Zàijiàn)",
        "correct_answer": "b", "score": 15
    },
    {
        "question_id": 5, "assignment_id": 1, "question_type": "true_false",
        "question_text": "Các chữ Hán '一' (số 1), '二' (số 2), '三' (số 3) đều được cấu tạo từ nét ngang (横 - héng).",
        "option_a": "Đúng", "option_b": "Sai", "option_c": "", "option_d": "",
        "correct_answer": "a", "score": 20
    },
    {
        "question_id": 6, "assignment_id": 1, "question_type": "true_false",
        "question_text": "Tiếng Trung phổ thông (Mandarin) có tất cả 6 thanh điệu cơ bản.",
        "option_a": "Đúng", "option_b": "Sai", "option_c": "", "option_d": "",
        "correct_answer": "b", "score": 20
    },

    # ── Bài 2: Giới Thiệu Bản Thân & Gia Đình (6 câu) ──
    {
        "question_id": 7, "assignment_id": 2, "question_type": "multiple_choice",
        "question_text": "Để hỏi tên đối phương một cách tự nhiên và lịch sự, câu nào sau đây là đúng nhất?",
        "option_a": "你叫什么名字？ (Nǐ jiào shénme míngzi?)",
        "option_b": "你是谁的名字？ (Nǐ shì shéi de míngzi?)",
        "option_c": "你名字叫哪儿？ (Nǐ míngzi jiào nǎr?)",
        "option_d": "你叫谁名字？ (Nǐ jiào shéi míngzi?)",
        "correct_answer": "a", "score": 15
    },
    {
        "question_id": 8, "assignment_id": 2, "question_type": "multiple_choice",
        "question_text": "Câu '我是越南人' (Wǒ shì Yuènán rén) có nghĩa tiếng Việt là gì?",
        "option_a": "Tôi là người Trung Quốc",
        "option_b": "Tôi là người Việt Nam",
        "option_c": "Tôi học tiếng Việt Nam",
        "option_d": "Tôi sống ở Việt Nam",
        "correct_answer": "b", "score": 15
    },
    {
        "question_id": 9, "assignment_id": 2, "question_type": "multiple_choice",
        "question_text": "Từ nào sau đây có nghĩa là 'Thầy cô giáo' trong tiếng Trung?",
        "option_a": "学生 (xuésheng)",
        "option_b": "医生 (yīshēng)",
        "option_c": "老师 (lǎoshī)",
        "option_d": "朋友 (péngyou)",
        "correct_answer": "c", "score": 15
    },
    {
        "question_id": 10, "assignment_id": 2, "question_type": "multiple_choice",
        "question_text": "Từ chỉ người 'Mẹ' trong gia đình viết bằng chữ Hán là:",
        "option_a": "爸爸 (bàba)",
        "option_b": "妈妈 (māma)",
        "option_c": "哥哥 (gēge)",
        "option_d": "姐姐 (jiějie)",
        "correct_answer": "b", "score": 15
    },
    {
        "question_id": 11, "assignment_id": 2, "question_type": "true_false",
        "question_text": "Đại từ nghi vấn '几' (jǐ - mấy) thường dùng để hỏi số lượng nhỏ hơn 10 (ví dụ: 你家有几口人？).",
        "option_a": "Đúng", "option_b": "Sai", "option_c": "", "option_d": "",
        "correct_answer": "a", "score": 20
    },
    {
        "question_id": 12, "assignment_id": 2, "question_type": "true_false",
        "question_text": "Từ '他们' (tāmen) chỉ dùng riêng cho nhóm toàn nữ giới.",
        "option_a": "Đúng", "option_b": "Sai", "option_c": "", "option_d": "",
        "correct_answer": "b", "score": 20
    },

    # ── Bài 3: Số Đếm, Thời Gian & Mua Sắm (6 câu) ──
    {
        "question_id": 13, "assignment_id": 3, "question_type": "multiple_choice",
        "question_text": "Câu hỏi 'Bao nhiêu tiền một cân?' khi mua hoa quả trong tiếng Trung là:",
        "option_a": "多少钱一斤？ (Duōshao qián yì jīn?)",
        "option_b": "几块钱一点？ (Jǐ kuài qián yì diǎn?)",
        "option_c": "怎么钱一斤？ (Zěnme qián yì jīn?)",
        "option_d": "为什么多少钱？ (Wèishénme duōshao qián?)",
        "correct_answer": "a", "score": 15
    },
    {
        "question_id": 14, "assignment_id": 3, "question_type": "multiple_choice",
        "question_text": "Câu '现在八点半' (Xiànzài bā diǎn bàn) biểu thị mấy giờ?",
        "option_a": "Hiện tại 7 giờ 30 phút",
        "option_b": "Hiện tại 8 giờ 30 phút",
        "option_c": "Hiện tại 8 giờ 15 phút",
        "option_d": "Hiện tại 9 giờ kém 15 phút",
        "correct_answer": "b", "score": 15
    },
    {
        "question_id": 15, "assignment_id": 3, "question_type": "multiple_choice",
        "question_text": "Thứ tự biểu đạt thời gian (năm, tháng, ngày, giờ) trong tiếng Trung tuân theo quy tắc nào?",
        "option_a": "Đơn vị nhỏ đứng trước, lớn đứng sau (Giờ -> Ngày -> Tháng -> Năm)",
        "option_b": "Đơn vị lớn đứng trước, nhỏ đứng sau (Năm -> Tháng -> Ngày -> Giờ)",
        "option_c": "Hoàn toàn giống thứ tự tiếng Việt (Ngày -> Tháng -> Năm)",
        "option_d": "Sắp xếp ngẫu nhiên không có quy tắc",
        "correct_answer": "b", "score": 15
    },
    {
        "question_id": 16, "assignment_id": 3, "question_type": "multiple_choice",
        "question_text": "Số 88 trong tiếng Trung được đọc và viết là:",
        "option_a": "二十八 (èr shí bā)",
        "option_b": "八十八 (bā shí bā)",
        "option_c": "八百八 (bā bǎi bā)",
        "option_d": "十八八 (shí bā bā)",
        "correct_answer": "b", "score": 15
    },
    {
        "question_id": 17, "assignment_id": 3, "question_type": "true_false",
        "question_text": "Lượng từ thông dụng và đa năng nhất trong tiếng Trung là chữ '个' (gè).",
        "option_a": "Đúng", "option_b": "Sai", "option_c": "", "option_d": "",
        "correct_answer": "a", "score": 20
    },
    {
        "question_id": 18, "assignment_id": 3, "question_type": "true_false",
        "question_text": "Khi muốn mặc cả xin bớt giá, ta có thể nói: '太贵了，便宜一点儿吧！' (Tài guì le, piányi yìdiǎnr ba!).",
        "option_a": "Đúng", "option_b": "Sai", "option_c": "", "option_d": "",
        "correct_answer": "a", "score": 20
    },

    # ── Bài 4: Ngữ Pháp & Văn Hóa Cung Đình (6 câu) ──
    {
        "question_id": 19, "assignment_id": 4, "question_type": "multiple_choice",
        "question_text": "Trong hoàng cung triều đình Trung Hoa xưa, Hoàng đế thường tự xưng là gì?",
        "option_a": "奴才 (Núcai)",
        "option_b": "朕 (Zhèn)",
        "option_c": "微臣 (Wēichén)",
        "option_d": "本宫 (Běngōng)",
        "correct_answer": "b", "score": 15
    },
    {
        "question_id": 20, "assignment_id": 4, "question_type": "multiple_choice",
        "question_text": "Câu chúc tụng Hoàng đế vạn thọ vô cương kinh điển trong hoàng triều là:",
        "option_a": "岁岁平安 (Suì suì píng'ān)",
        "option_b": "吾皇万岁万岁万万岁 (Wú huáng wànsuì wànsuì wànwànsuì)",
        "option_c": "恭喜发财 (Gōngxǐ fācái)",
        "option_d": "一路顺风 (Yílù shùnfēng)",
        "correct_answer": "b", "score": 15
    },
    {
        "question_id": 21, "assignment_id": 4, "question_type": "multiple_choice",
        "question_text": "Điền giới từ thích hợp vào chỗ trống: '我 ______ 图书馆看书。' (Tôi đọc sách ở thư viện).",
        "option_a": "在 (zài)",
        "option_b": "有 (yǒu)",
        "option_c": "是 (shì)",
        "option_d": "从 (cóng)",
        "correct_answer": "a", "score": 15
    },
    {
        "question_id": 22, "assignment_id": 4, "question_type": "multiple_choice",
        "question_text": "Chữ '吃' (chī - Ăn) có bộ thủ nào ở phía bên trái liên quan đến miệng?",
        "option_a": "Bộ Khẩu (口)",
        "option_b": "Bộ Thủy (氵)",
        "option_c": "Bộ Mộc (木)",
        "option_d": "Bộ Hỏa (火)",
        "correct_answer": "a", "score": 15
    },
    {
        "question_id": 23, "assignment_id": 4, "question_type": "true_false",
        "question_text": "Cấu trúc câu biểu đạt địa điểm hành động trong tiếng Trung là: 'Chủ ngữ + 在 + Nơi chốn + Động từ' (ví dụ: 我在学校学汉语).",
        "option_a": "Đúng", "option_b": "Sai", "option_c": "", "option_d": "",
        "correct_answer": "a", "score": 20
    },
    {
        "question_id": 24, "assignment_id": 4, "question_type": "true_false",
        "question_text": "Chữ '国' trong '中国' (Trung Quốc) có bộ Vi (囗) bao bọc xung quanh, biểu thị biên giới bờ cõi bờ cõi lãnh thổ.",
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
