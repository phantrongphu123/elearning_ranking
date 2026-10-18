from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from typing import Optional
from datetime import datetime

from ..core.dependencies import get_current_user, require_teacher_or_admin, require_admin
from ..services.excel_service import ExcelService
from ..services.score_service import add_score
from ..core.config import ATTENDANCE_SCORES

router = APIRouter(prefix="/api/attendance", tags=["Attendance"])
excel_service = ExcelService()


class AttendanceRecord(BaseModel):
    student_id: int
    class_id: int
    date: str
    status: str  # present, late, absent_excused, absent_unexcused
    note: Optional[str] = ""


class BulkAttendance(BaseModel):
    class_id: int
    date: str
    records: list  # [{student_id, status, note}]


@router.post("")
def mark_attendance(data: BulkAttendance, current_user: dict = Depends(require_teacher_or_admin)):
    """Mark attendance by recording ONLY absent/late students to optimize quota."""
    import pandas as pd
    
    df = excel_service.read_sheet("DiemDanh")
    c_id = int(float(data.class_id))
    date_str = str(data.date).strip()
    
    # Clean up any existing records for this class and date
    if not df.empty and "class_id" in df.columns:
        c_col = pd.to_numeric(df["class_id"], errors="coerce").fillna(0).astype(int)
        d_col = df["date"].astype(str).str.strip()
        existing_mask = (c_col == c_id) & (d_col == date_str)
        df_clean = df[~existing_mask].copy()
    else:
        df_clean = df.copy()
    
    # Filter to only keep absent or late students (default is present, no record needed)
    absent_records = [
        r for r in data.records 
        if r.get("status") in ["absent_unexcused", "absent_excused", "late"]
    ]
    
    max_id = 0
    if not df_clean.empty and "attendance_id" in df_clean.columns:
        max_id = int(pd.to_numeric(df_clean["attendance_id"], errors="coerce").fillna(0).max())
    
    new_rows = []
    results = []
    
    for r in absent_records:
        student_id = int(float(r.get("student_id")))
        status = r.get("status", "absent_unexcused")
        points = ATTENDANCE_SCORES.get(status, 0)
        max_id += 1
        
        row = {
            "attendance_id": max_id,
            "student_id": student_id,
            "class_id": c_id,
            "date": date_str,
            "status": status,
            "points": points,
            "note": str(r.get("note", "")).strip(),
            "created_by": current_user.get("username", ""),
        }
        new_rows.append(row)
        
        # Only add score adjustment if points != 0 (e.g. -10 for unexcused, +2 for late)
        if points != 0:
            status_label = {
                "late": "Đi học trễ",
                "absent_excused": "Nghỉ có phép",
                "absent_unexcused": "Nghỉ không phép",
            }.get(status, status)
            
            add_score(
                student_id,
                "attendance",
                f"Chuyên cần ngày {date_str}: {status_label}",
                points,
                None,
                current_user.get("username", "")
            )
        
        results.append({"student_id": student_id, "status": status, "points": points})
    
    # Batch write single time to prevent Google Sheets rate limiting
    if new_rows:
        final_df = pd.concat([df_clean, pd.DataFrame(new_rows)], ignore_index=True)
    else:
        final_df = df_clean
    excel_service.write_sheet("DiemDanh", final_df)
    
    absent_count = len(results)
    if absent_count == 0:
        msg = f"Đã lưu điểm danh ngày {date_str}: Cả lớp đều có mặt đầy đủ (0 học sinh vắng)."
    else:
        msg = f"Đã lưu điểm danh ngày {date_str}: Ghi nhận {absent_count} học sinh vắng/trễ."
    
    return {"message": msg, "results": results, "absent_count": absent_count}


@router.get("")
def get_attendance(
    class_id: Optional[int] = None,
    student_id: Optional[int] = None,
    date: Optional[str] = None,
    current_user: dict = Depends(get_current_user)
):
    import pandas as pd
    df = excel_service.read_sheet("DiemDanh")
    
    if current_user["role"] == "student":
        curr_sid = int(float(current_user.get("student_id") or 0))
        s_col = pd.to_numeric(df["student_id"], errors="coerce").fillna(0).astype(int)
        df = df[s_col == curr_sid]
    
    if class_id is not None:
        c_id = int(float(class_id))
        c_col = pd.to_numeric(df["class_id"], errors="coerce").fillna(0).astype(int)
        df = df[c_col == c_id]
    if student_id is not None:
        s_id = int(float(student_id))
        s_col = pd.to_numeric(df["student_id"], errors="coerce").fillna(0).astype(int)
        df = df[s_col == s_id]
    if date:
        df = df[df["date"].astype(str) == str(date)]
    
    if df.empty:
        return []
    
    return df.sort_values("date", ascending=False).to_dict(orient="records")


@router.get("/config")
def get_attendance_config(current_user: dict = Depends(get_current_user)):
    """Get current attendance score config."""
    return ATTENDANCE_SCORES
