import os
import shutil
import threading
from datetime import datetime
from pathlib import Path
from typing import Optional, Any
import pandas as pd
import openpyxl
from openpyxl import load_workbook

from ..core.config import DB_PATH, BACKUP_DIR


# All column definitions per sheet
SHEET_COLUMNS = {
    "Users": ["user_id", "username", "password_hash", "full_name", "role", "student_id", "class_id", "status", "created_at"],
    "HocSinh": ["student_id", "student_code", "full_name", "date_of_birth", "gender", "class_id", "total_score", "rank", "rank_level", "avatar", "status", "created_at"],
    "LopHoc": ["class_id", "class_code", "class_name", "teacher_id", "school_year", "status"],
    "BaiTap": ["assignment_id", "title", "description", "subject", "class_id", "teacher_id", "created_at", "start_time", "deadline", "max_score", "bonus_score", "penalty_score", "status"],
    "CauHoi": ["question_id", "assignment_id", "question_type", "question_text", "option_a", "option_b", "option_c", "option_d", "correct_answer", "score"],
    "BaiNop": ["submission_id", "assignment_id", "student_id", "submitted_at", "status", "score", "is_late", "teacher_comment"],
    "ChiTietBaiNop": ["submission_detail_id", "submission_id", "question_id", "student_answer", "correct", "score"],
    "Diem": ["score_id", "student_id", "type", "reason", "points", "assignment_id", "created_at", "created_by"],
    "LichSuNopBai": ["history_id", "student_id", "assignment_id", "submitted_at", "deadline", "status", "score", "is_late"],
    "RankHistory": ["history_id", "student_id", "old_rank", "new_rank", "total_score", "changed_at", "reason"],
    "DiemDanh": ["attendance_id", "student_id", "class_id", "date", "status", "points", "note", "created_by"],
    "ThanhTich": ["achievement_id", "student_id", "achievement_code", "achievement_name", "description", "icon", "unlocked_at"],
    "ThongBao": ["notification_id", "user_id", "title", "message", "type", "is_read", "created_at"],
    "RankConfig": ["rank_id", "min_score", "max_score", "male_name", "female_name", "level", "color", "icon"],
}


class ExcelService:
    """
    Centralized service for all Excel read/write operations.
    Uses a threading lock to prevent race conditions on file writes.
    """
    _instance = None
    _lock = threading.Lock()

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def _ensure_db_exists(self):
        """Create the Excel file with all sheets if it doesn't exist."""
        if not os.path.exists(DB_PATH):
            os.makedirs(DB_PATH.parent, exist_ok=True)
            os.makedirs(BACKUP_DIR, exist_ok=True)
            with pd.ExcelWriter(str(DB_PATH), engine="openpyxl") as writer:
                for sheet_name, columns in SHEET_COLUMNS.items():
                    pd.DataFrame(columns=columns).to_excel(writer, sheet_name=sheet_name, index=False)

    def read_sheet(self, sheet_name: str) -> pd.DataFrame:
        """Read a sheet from the Excel database."""
        self._ensure_db_exists()
        try:
            df = pd.read_excel(str(DB_PATH), sheet_name=sheet_name, dtype=str)
            # Fill NaN with empty string for string columns
            df = df.fillna("")
            # Convert numeric-looking columns
            for col in df.columns:
                if col.endswith("_id") or col in ["total_score", "score", "points", "min_score", "max_score", "level", "rank_level", "max_score", "bonus_score", "penalty_score"]:
                    df[col] = pd.to_numeric(df[col], errors="coerce").fillna(0)
            return df
        except Exception as e:
            # Return empty DataFrame with correct columns
            return pd.DataFrame(columns=SHEET_COLUMNS.get(sheet_name, []))

    def write_sheet(self, sheet_name: str, df: pd.DataFrame, backup: bool = False):
        """Write a DataFrame to a specific sheet, preserving all other sheets."""
        self._ensure_db_exists()
        with self._lock:
            if backup:
                self._backup()
            
            # Load all existing sheets
            all_sheets = {}
            for sheet in SHEET_COLUMNS.keys():
                try:
                    all_sheets[sheet] = pd.read_excel(str(DB_PATH), sheet_name=sheet, dtype=str).fillna("")
                except:
                    all_sheets[sheet] = pd.DataFrame(columns=SHEET_COLUMNS[sheet])
            
            # Replace the target sheet
            all_sheets[sheet_name] = df
            
            # Write everything back
            with pd.ExcelWriter(str(DB_PATH), engine="openpyxl", mode="w") as writer:
                for s_name, s_df in all_sheets.items():
                    s_df.to_excel(writer, sheet_name=s_name, index=False)

    def insert_row(self, sheet_name: str, row_data: dict) -> dict:
        """Insert a new row into a sheet."""
        df = self.read_sheet(sheet_name)
        new_row = pd.DataFrame([row_data])
        df = pd.concat([df, new_row], ignore_index=True)
        self.write_sheet(sheet_name, df)
        return row_data

    def update_row(self, sheet_name: str, id_column: str, id_value: Any, updates: dict):
        """Update fields in a row by ID."""
        df = self.read_sheet(sheet_name)
        # Compare as same type
        mask = df[id_column].astype(str) == str(id_value)
        if not mask.any():
            return False
        for key, value in updates.items():
            if key in df.columns:
                df.loc[mask, key] = value
        self.write_sheet(sheet_name, df)
        return True

    def delete_row(self, sheet_name: str, id_column: str, id_value: Any):
        """Delete a row by ID."""
        df = self.read_sheet(sheet_name)
        df = df[df[id_column].astype(str) != str(id_value)]
        self.write_sheet(sheet_name, df, backup=True)
        return True

    def get_next_id(self, sheet_name: str, id_column: str) -> int:
        """Get the next available integer ID for a sheet."""
        df = self.read_sheet(sheet_name)
        if df.empty or id_column not in df.columns:
            return 1
        ids = pd.to_numeric(df[id_column], errors="coerce").dropna()
        return int(ids.max()) + 1 if not ids.empty else 1

    def find_one(self, sheet_name: str, column: str, value: Any) -> Optional[dict]:
        """Find the first row where column == value."""
        df = self.read_sheet(sheet_name)
        result = df[df[column].astype(str) == str(value)]
        if result.empty:
            return None
        return result.iloc[0].to_dict()

    def _backup(self):
        """Create a timestamped backup of the database."""
        if os.path.exists(DB_PATH):
            os.makedirs(BACKUP_DIR, exist_ok=True)
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            backup_path = BACKUP_DIR / f"school_system_{timestamp}.xlsx"
            shutil.copy2(str(DB_PATH), str(backup_path))
