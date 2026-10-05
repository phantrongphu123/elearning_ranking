from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from typing import Optional

from ..core.dependencies import get_current_user, require_admin
from ..services.excel_service import ExcelService
from ..services.score_service import add_score

router = APIRouter(prefix="/api/scores", tags=["Scores"])
excel_service = ExcelService()


class ManualScore(BaseModel):
    student_id: int
    points: float
    reason: str
    score_type: str = "manual"  # bonus, penalty, manual


@router.post("")
def add_manual_score(data: ManualScore, current_user: dict = Depends(get_current_user)):
    """Manually add/subtract score (Admin or Teacher)."""
    if current_user["role"] not in ["admin", "teacher"]:
        raise HTTPException(status_code=403, detail="Không có quyền")
    
    result = add_score(
        data.student_id,
        data.score_type,
        data.reason,
        data.points,
        None,
        current_user["username"]
    )
    return {"message": "Cập nhật điểm thành công", **result}


@router.get("/notifications")
def get_notifications(current_user: dict = Depends(get_current_user)):
    """Get notifications for the current user."""
    df = excel_service.read_sheet("ThongBao")
    user_notifs = df[df["user_id"].astype(str) == str(current_user["user_id"])]
    notifs = user_notifs.sort_values("created_at", ascending=False).head(20).to_dict(orient="records")
    return notifs


@router.put("/notifications/{notif_id}/read")
def mark_notification_read(notif_id: int, current_user: dict = Depends(get_current_user)):
    excel_service.update_row("ThongBao", "notification_id", notif_id, {"is_read": "true"})
    return {"message": "Đã đọc"}


@router.put("/notifications/read-all")
def mark_all_read(current_user: dict = Depends(get_current_user)):
    df = excel_service.read_sheet("ThongBao")
    df.loc[df["user_id"].astype(str) == str(current_user["user_id"]), "is_read"] = "true"
    excel_service.write_sheet("ThongBao", df)
    return {"message": "Đã đọc tất cả"}
