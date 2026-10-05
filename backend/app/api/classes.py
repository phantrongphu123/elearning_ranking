from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from typing import Optional

from ..core.dependencies import get_current_user, require_admin
from ..services.excel_service import ExcelService

router = APIRouter(prefix="/api/classes", tags=["Classes"])
excel_service = ExcelService()


class ClassCreate(BaseModel):
    class_code: str
    class_name: str
    teacher_id: Optional[int] = None
    school_year: Optional[str] = "2026-2027"


class ClassUpdate(BaseModel):
    class_name: Optional[str] = None
    teacher_id: Optional[int] = None
    school_year: Optional[str] = None
    status: Optional[str] = None


@router.get("")
def list_classes(current_user: dict = Depends(get_current_user)):
    df = excel_service.read_sheet("LopHoc")
    classes = df.to_dict(orient="records")
    
    # Enrich with teacher name
    users_df = excel_service.read_sheet("Users")
    for cls in classes:
        teacher_id = cls.get("teacher_id")
        if teacher_id:
            teacher = users_df[users_df["user_id"].astype(str) == str(teacher_id)]
            if not teacher.empty:
                cls["teacher_name"] = teacher.iloc[0].get("full_name", "")
    
    # Count students per class
    students_df = excel_service.read_sheet("HocSinh")
    for cls in classes:
        count = len(students_df[students_df["class_id"].astype(str) == str(cls.get("class_id", ""))])
        cls["student_count"] = count
    
    return classes


@router.post("", status_code=201)
def create_class(data: ClassCreate, current_user: dict = Depends(require_admin)):
    existing = excel_service.find_one("LopHoc", "class_code", data.class_code)
    if existing:
        raise HTTPException(status_code=400, detail="Mã lớp đã tồn tại")
    
    class_id = excel_service.get_next_id("LopHoc", "class_id")
    excel_service.insert_row("LopHoc", {
        "class_id": class_id,
        "class_code": data.class_code,
        "class_name": data.class_name,
        "teacher_id": data.teacher_id or "",
        "school_year": data.school_year,
        "status": "active",
    })
    return {"message": "Tạo lớp thành công", "class_id": class_id}


@router.put("/{class_id}")
def update_class(class_id: int, data: ClassUpdate, current_user: dict = Depends(require_admin)):
    cls = excel_service.find_one("LopHoc", "class_id", class_id)
    if not cls:
        raise HTTPException(status_code=404, detail="Lớp không tồn tại")
    updates = {k: v for k, v in data.dict().items() if v is not None}
    excel_service.update_row("LopHoc", "class_id", class_id, updates)
    return {"message": "Cập nhật thành công"}


@router.delete("/{class_id}")
def delete_class(class_id: int, current_user: dict = Depends(require_admin)):
    cls = excel_service.find_one("LopHoc", "class_id", class_id)
    if not cls:
        raise HTTPException(status_code=404, detail="Lớp không tồn tại")
    excel_service.update_row("LopHoc", "class_id", class_id, {"status": "inactive"})
    return {"message": "Xóa lớp thành công"}
