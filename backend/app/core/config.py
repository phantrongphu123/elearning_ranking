import os
from pathlib import Path

# Base paths
BASE_DIR = Path(__file__).resolve().parent.parent.parent.parent
DATABASE_DIR = BASE_DIR / "database"
DB_PATH = DATABASE_DIR / "school_system.xlsx"
BACKUP_DIR = DATABASE_DIR / "backup"

# JWT Config
SECRET_KEY = "hoangcung_secret_key_2026_thpt_linh_chi"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60 * 8  # 8 hours

# Rank Configuration (can be overridden by admin)
DEFAULT_RANKS = [
    {"min_score": 0,    "max_score": 99,   "male": "Nô Tài",          "female": "Cung Nữ",          "level": 1, "color": "#8B7355", "icon": "🪨"},
    {"min_score": 100,  "max_score": 300,  "male": "Thường Tại",      "female": "Đáp Ứng",          "level": 2, "color": "#7B68EE", "icon": "💜"},
    {"min_score": 301,  "max_score": 500,  "male": "Quý Nhân",        "female": "Quý Nhân",          "level": 3, "color": "#4682B4", "icon": "💎"},
    {"min_score": 501,  "max_score": 800,  "male": "Tần",             "female": "Phi",               "level": 4, "color": "#3CB371", "icon": "🌺"},
    {"min_score": 801,  "max_score": 1200, "male": "Quý Phi",         "female": "Hoàng Quý Phi",     "level": 5, "color": "#FF8C00", "icon": "✨"},
    {"min_score": 1201, "max_score": 1500, "male": "Tể Tướng",        "female": "Hoàng Hậu",         "level": 6, "color": "#DC143C", "icon": "👑"},
    {"min_score": 1501, "max_score": 999999,"male": "Hoàng Đế",       "female": "Thái Hậu",          "level": 7, "color": "#FFD700", "icon": "🏆"},
]

# Attendance scoring config (configurable)
ATTENDANCE_SCORES = {
    "present": 5,
    "late": 2,
    "absent_excused": 0,
    "absent_unexcused": -10,
}

# App config
APP_NAME = "Hoàng Cung Học Đường"
APP_VERSION = "1.0.0"
CORS_ORIGINS = ["*"]
