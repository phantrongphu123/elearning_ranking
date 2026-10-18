"""Script cập nhật các bài tập và câu hỏi thuần Tiếng Trung cho Lớp 10A4 trên Google Sheet."""
import os
import sys
from datetime import datetime, timedelta
import gspread
from google.oauth2.service_account import Credentials

BACKEND_DIR = os.path.dirname(os.path.abspath(__file__))
SERVICE_ACCOUNT_FILE = os.path.join(BACKEND_DIR, "service_account.json")
SPREADSHEET_ID = "1Abfw5CMLtseRVwoXOgTjnkEpjGkzHhkg5nD4PcBOExk"

SCOPES = [
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive",
]

def main():
    creds = Credentials.from_service_account_file(SERVICE_ACCOUNT_FILE, scopes=SCOPES)
    client = gspread.authorize(creds)
    ss = client.open_by_key(SPREADSHEET_ID)

    now = datetime.now()

    # 4 bài tập duy nhất môn Tiếng Trung cho Lớp 10A4
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

    # Các câu hỏi môn Tiếng Trung (mỗi bài đúng 6 câu, tổng điểm 100đ/bài)
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

    # Cập nhật sheet BaiTap
    bai_tap_cols = ["assignment_id", "title", "description", "subject", "class_id", "teacher_id", "created_at", "start_time", "deadline", "max_score", "bonus_score", "penalty_score", "status"]
    ws_bt = ss.worksheet("BaiTap")
    bt_rows = [bai_tap_cols]
    for b in bai_tap:
        bt_rows.append([b.get(col, "") for col in bai_tap_cols])
    ws_bt.clear()
    ws_bt.update(values=bt_rows, range_name="A1")
    print("SUCCESS: Updated BaiTap with 4 Chinese assignments.")

    # Cập nhật sheet CauHoi
    cau_hoi_cols = ["question_id", "assignment_id", "question_type", "question_text", "option_a", "option_b", "option_c", "option_d", "correct_answer", "score"]
    ws_ch = ss.worksheet("CauHoi")
    ch_rows = [cau_hoi_cols]
    for q in cau_hoi:
        ch_rows.append([q.get(col, "") for col in cau_hoi_cols])
    ws_ch.clear()
    ws_ch.update(values=ch_rows, range_name="A1")
    print("SUCCESS: Updated CauHoi with 24 Chinese questions (6 per assignment).")

if __name__ == "__main__":
    if sys.stdout.encoding.lower() != 'utf-8':
        sys.stdout.reconfigure(encoding='utf-8')
    main()
