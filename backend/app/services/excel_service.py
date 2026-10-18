"""
GoogleSheetService – Thay thế ExcelService, giữ nguyên toàn bộ interface cũ.

Cơ chế hoạt động:
  • Đọc  → Dùng In-Memory Cache (TTL 45 giây) để tránh vượt Google API quota
            (giới hạn 60 requests/phút/project).
  • Ghi  → append_row() trực tiếp lên sheet, sau đó xóa cache sheet đó.
  • Update/Delete → Ghi lại toàn bộ sheet (dùng threading.Lock để an toàn đồng thời).

Xác thực:
  • Vercel → đọc JSON từ biến môi trường GOOGLE_SERVICE_ACCOUNT_JSON
  • Local  → đọc từ file service_account.json
"""

import json
import threading
import time
from typing import Any, Optional

import gspread
import pandas as pd
from google.oauth2.service_account import Credentials

from ..core.config import (
    GOOGLE_SHEET_ID,
    GOOGLE_SERVICE_ACCOUNT_FILE,
    GOOGLE_SERVICE_ACCOUNT_JSON,
)

# ─────────────────────────────────────────────────────────────
# Scopes cần thiết để đọc & ghi Google Sheets
# ─────────────────────────────────────────────────────────────
_SCOPES = [
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive",
]

# ─────────────────────────────────────────────────────────────
# Định nghĩa cột của mỗi sheet (đồng bộ với schema cũ)
# ─────────────────────────────────────────────────────────────
SHEET_COLUMNS = {
    "Users":           ["user_id", "username", "password_hash", "full_name", "role", "student_id", "class_id", "status", "created_at"],
    "HocSinh":         ["student_id", "student_code", "full_name", "date_of_birth", "gender", "class_id", "total_score", "rank", "rank_level", "avatar", "status", "created_at"],
    "LopHoc":          ["class_id", "class_code", "class_name", "teacher_id", "school_year", "status"],
    "BaiTap":          ["assignment_id", "title", "description", "subject", "class_id", "teacher_id", "created_at", "start_time", "deadline", "max_score", "bonus_score", "penalty_score", "status"],
    "CauHoi":          ["question_id", "assignment_id", "question_type", "question_text", "option_a", "option_b", "option_c", "option_d", "correct_answer", "score"],
    "BaiNop":          ["submission_id", "assignment_id", "student_id", "submitted_at", "status", "score", "is_late", "teacher_comment"],
    "ChiTietBaiNop":   ["submission_detail_id", "submission_id", "question_id", "student_answer", "correct", "score"],
    "Diem":            ["score_id", "student_id", "type", "reason", "points", "assignment_id", "created_at", "created_by"],
    "LichSuNopBai":    ["history_id", "student_id", "assignment_id", "submitted_at", "deadline", "status", "score", "is_late"],
    "RankHistory":     ["history_id", "student_id", "old_rank", "new_rank", "total_score", "changed_at", "reason"],
    "DiemDanh":        ["attendance_id", "student_id", "class_id", "date", "status", "points", "note", "created_by"],
    "ThanhTich":       ["achievement_id", "student_id", "achievement_code", "achievement_name", "description", "icon", "unlocked_at"],
    "ThongBao":        ["notification_id", "user_id", "title", "message", "type", "is_read", "created_at"],
    "RankConfig":      ["rank_id", "min_score", "max_score", "male_name", "female_name", "level", "color", "icon"],
}

# Các cột cần chuyển về kiểu số
_NUMERIC_COLS = {
    "user_id", "student_id", "class_id", "teacher_id",
    "assignment_id", "question_id", "submission_id", "submission_detail_id",
    "score_id", "history_id", "attendance_id", "achievement_id",
    "notification_id", "rank_id",
    "total_score", "score", "points", "min_score", "max_score",
    "level", "rank_level", "bonus_score", "penalty_score", "max_score",
}

# TTL cache (giây)
_CACHE_TTL = 45


def _build_credentials() -> Credentials:
    """Xây dựng Google OAuth2 Credentials từ env (Vercel) hoặc file local."""
    if GOOGLE_SERVICE_ACCOUNT_JSON:
        info = json.loads(GOOGLE_SERVICE_ACCOUNT_JSON)
        return Credentials.from_service_account_info(info, scopes=_SCOPES)
    return Credentials.from_service_account_file(GOOGLE_SERVICE_ACCOUNT_FILE, scopes=_SCOPES)


# ─────────────────────────────────────────────────────────────
# ExcelService – giữ tên cũ để không cần đổi import ở bất cứ đâu
# ─────────────────────────────────────────────────────────────
class ExcelService:
    """
    Singleton service đọc/ghi Google Sheet.
    Interface giữ nguyên hoàn toàn so với phiên bản Excel cũ.
    """

    _instance = None
    _lock = threading.Lock()

    # Cache structure: {sheet_name: {"data": DataFrame, "ts": float}}
    _cache: dict = {}
    _cache_lock = threading.Lock()

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._client = None
            cls._instance._spreadsheet = None
        return cls._instance

    # ── Internal helpers ──────────────────────────────────────

    def _get_spreadsheet(self):
        """Lấy spreadsheet object, tự kết nối lại nếu chưa có."""
        if self._spreadsheet is None:
            creds = _build_credentials()
            gc = gspread.authorize(creds)
            self._spreadsheet = gc.open_by_key(GOOGLE_SHEET_ID)
        return self._spreadsheet

    def _get_worksheet(self, sheet_name: str) -> gspread.Worksheet:
        """Lấy worksheet, tự tạo nếu chưa tồn tại."""
        ss = self._get_spreadsheet()
        try:
            return ss.worksheet(sheet_name)
        except gspread.exceptions.WorksheetNotFound:
            # Tự tạo sheet mới với header
            ws = ss.add_worksheet(title=sheet_name, rows=1000, cols=30)
            headers = SHEET_COLUMNS.get(sheet_name, [])
            if headers:
                ws.append_row(headers, value_input_option="RAW")
            return ws

    def _invalidate_cache(self, sheet_name: str):
        with self._cache_lock:
            self._cache.pop(sheet_name, None)

    def _normalize_df(self, df: pd.DataFrame, sheet_name: str) -> pd.DataFrame:
        """Chuẩn hóa kiểu dữ liệu: cột ID và số về numeric, còn lại là string."""
        df = df.fillna("")
        for col in df.columns:
            if col in _NUMERIC_COLS:
                df[col] = pd.to_numeric(df[col], errors="coerce").fillna(0)
        return df

    # ── Public API (giữ nguyên interface cũ) ─────────────────

    def read_sheet(self, sheet_name: str) -> pd.DataFrame:
        """Đọc sheet, kết quả được cache 45 giây."""
        now = time.time()
        with self._cache_lock:
            cached = self._cache.get(sheet_name)
            if cached and (now - cached["ts"]) < _CACHE_TTL:
                return cached["data"].copy()

        try:
            ws = self._get_worksheet(sheet_name)
            records = ws.get_all_records(
                expected_headers=SHEET_COLUMNS.get(sheet_name, []),
                value_render_option="UNFORMATTED_VALUE",
                default_blank="",
            )
            df = pd.DataFrame(records) if records else pd.DataFrame(
                columns=SHEET_COLUMNS.get(sheet_name, [])
            )
            df = self._normalize_df(df, sheet_name)
        except Exception:
            df = pd.DataFrame(columns=SHEET_COLUMNS.get(sheet_name, []))

        with self._cache_lock:
            self._cache[sheet_name] = {"data": df.copy(), "ts": time.time()}
        return df

    def write_sheet(self, sheet_name: str, df: pd.DataFrame, backup: bool = False):
        """Ghi đè toàn bộ nội dung 1 sheet (dùng cho update/delete)."""
        with self._lock:
            ws = self._get_worksheet(sheet_name)
            # Xóa dữ liệu cũ (giữ lại header ở row 1)
            ws.clear()
            headers = list(df.columns)
            rows = [headers] + [[str(v) if v != "" else "" for v in row]
                                 for row in df.itertuples(index=False, name=None)]
            ws.update(rows, value_input_option="RAW")
            self._invalidate_cache(sheet_name)

    def insert_row(self, sheet_name: str, row_data: dict) -> dict:
        """Thêm 1 dòng mới vào cuối sheet (dùng append_row - nhanh nhất)."""
        with self._lock:
            ws = self._get_worksheet(sheet_name)
            headers = SHEET_COLUMNS.get(sheet_name, list(row_data.keys()))
            row = [str(row_data.get(h, "")) if row_data.get(h, "") != "" else ""
                   for h in headers]
            ws.append_row(row, value_input_option="RAW")
            self._invalidate_cache(sheet_name)
        return row_data

    def update_row(self, sheet_name: str, id_column: str, id_value: Any, updates: dict) -> bool:
        """Cập nhật trường trong 1 dòng xác định bởi id_column == id_value."""
        df = self.read_sheet(sheet_name)
        mask = df[id_column].astype(str) == str(id_value)
        if not mask.any():
            return False
        for key, value in updates.items():
            if key in df.columns:
                df.loc[mask, key] = value
        self.write_sheet(sheet_name, df)
        return True

    def delete_row(self, sheet_name: str, id_column: str, id_value: Any) -> bool:
        """Xóa dòng xác định bởi id_column == id_value."""
        df = self.read_sheet(sheet_name)
        df = df[df[id_column].astype(str) != str(id_value)]
        self.write_sheet(sheet_name, df)
        return True

    def get_next_id(self, sheet_name: str, id_column: str) -> int:
        """Lấy ID tiếp theo (max hiện tại + 1). Được bảo vệ bằng lock."""
        with self._lock:
            df = self.read_sheet(sheet_name)
            if df.empty or id_column not in df.columns:
                return 1
            ids = pd.to_numeric(df[id_column], errors="coerce").dropna()
            return int(ids.max()) + 1 if not ids.empty else 1

    def find_one(self, sheet_name: str, column: str, value: Any) -> Optional[dict]:
        """Tìm dòng đầu tiên thoả mãn column == value."""
        df = self.read_sheet(sheet_name)
        result = df[df[column].astype(str) == str(value)]
        if result.empty:
            return None
        return result.iloc[0].to_dict()
