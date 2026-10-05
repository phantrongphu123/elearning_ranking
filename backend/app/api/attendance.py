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
    """Mark attendance for a whole class on a given date."""
    results = []
    for record in data.records:
        student_id = record.get("student_id")
        status = record.get("status", "present")
        
        # Calculate points from config
        points = ATTENDANCE_SCORES.get(status, 0)
        
        attendance_id = excel_service.get_next_id("DiemDanh", "attendance_id")
        excel_service.insert_row("DiemDanh", {
            "attendance_id": attendance_id,
            "student_id": student_id,
            "class_id": data.class_id,
            "date": data.date,
            "status": status,
            "points": points,
            "note": record.get("note", ""),
            "created_by": current_user["username"],
        })
        
        # Add score if non-zero
        if points != 0:
            status_label = {
                "present": "Có mặt đúng giờ",
                "late": "Đi học trễ",
                "absent_excused": "Nghỉ có phép",
                "absent_unexcused": "Nghỉ không phép",
            }.get(status, status)
            
            add_score(
                int(student_id),
                "attendance",
                f"Chuyên cần ngày {data.date}: {status_label}",
                points,
                None,
                current_user["username"]
            )
        
        results.append({"student_id": student_id, "status": status, "points": points})
    
    return {"message": "Điểm danh thành công", "results": results}


@router.get("")
def get_attendance(
    class_id: Optional[int] = None,
    student_id: Optional[int] = None,
    date: Optional[str] = None,
    current_user: dict = Depends(get_current_user)
):
    df = excel_service.read_sheet("DiemDanh")
    
    if current_user["role"] == "student":
        df = df[df["student_id"].astype(str) == str(current_user.get("student_id"))]
    
    if class_id:
        df = df[df["class_id"].astype(str) == str(class_id)]
    if student_id:
        df = df[df["student_id"].astype(str) == str(student_id)]
    if date:
        df = df[df["date"] == date]
    
    return df.sort_values("date", ascending=False).to_dict(orient="records")


@router.get("/config")
def get_attendance_config(current_user: dict = Depends(get_current_user)):
    """Get current attendance score config."""
    return ATTENDANCE_SCORES
