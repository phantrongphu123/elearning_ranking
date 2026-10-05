from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from typing import Optional
from datetime import datetime

from ..core.dependencies import get_current_user, require_admin
from ..core.security import hash_password
from ..services.excel_service import ExcelService

router = APIRouter(prefix="/api/teachers", tags=["Teachers"])
excel_service = ExcelService()


class TeacherCreate(BaseModel):
    full_name: str
    username: str
    password: str


class TeacherUpdate(BaseModel):
    full_name: Optional[str] = None
    status: Optional[str] = None


@router.get("")
def list_teachers(current_user: dict = Depends(require_admin)):
    df = excel_service.read_sheet("Users")
    teachers = df[df["role"] == "teacher"].to_dict(orient="records")
    return [{k: v for k, v in t.items() if k != "password_hash"} for t in teachers]


@router.post("", status_code=201)
def create_teacher(data: TeacherCreate, current_user: dict = Depends(require_admin)):
    existing = excel_service.find_one("Users", "username", data.username)
    if existing:
        raise HTTPException(status_code=400, detail="Tên đăng nhập đã tồn tại")
    
    user_id = excel_service.get_next_id("Users", "user_id")
    excel_service.insert_row("Users", {
        "user_id": user_id,
        "username": data.username,
        "password_hash": hash_password(data.password),
        "full_name": data.full_name,
        "role": "teacher",
        "student_id": "",
        "class_id": "",
        "status": "active",
        "created_at": datetime.now().isoformat(),
    })
    return {"message": "Tạo giáo viên thành công", "user_id": user_id}


@router.put("/{user_id}")
def update_teacher(user_id: int, data: TeacherUpdate, current_user: dict = Depends(require_admin)):
    teacher = excel_service.find_one("Users", "user_id", user_id)
    if not teacher or teacher["role"] != "teacher":
        raise HTTPException(status_code=404, detail="Giáo viên không tồn tại")
    updates = {k: v for k, v in data.dict().items() if v is not None}
    excel_service.update_row("Users", "user_id", user_id, updates)
    return {"message": "Cập nhật thành công"}


@router.delete("/{user_id}")
def delete_teacher(user_id: int, current_user: dict = Depends(require_admin)):
    teacher = excel_service.find_one("Users", "user_id", user_id)
    if not teacher or teacher["role"] != "teacher":
        raise HTTPException(status_code=404, detail="Giáo viên không tồn tại")
    excel_service.update_row("Users", "user_id", user_id, {"status": "inactive"})
    return {"message": "Xóa giáo viên thành công"}
