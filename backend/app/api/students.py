from fastapi import APIRouter, HTTPException, Depends, Query
from pydantic import BaseModel
from typing import Optional
from datetime import datetime

from ..core.dependencies import get_current_user, require_admin, require_teacher_or_admin
from ..core.security import hash_password
from ..services.excel_service import ExcelService
from ..services.rank_service import calculate_rank

router = APIRouter(prefix="/api/students", tags=["Students"])
excel_service = ExcelService()


class StudentCreate(BaseModel):
    student_code: str
    full_name: str
    date_of_birth: Optional[str] = ""
    gender: str = "female"
    class_id: Optional[int] = None
    username: str
    password: str
    avatar: Optional[str] = ""


class StudentUpdate(BaseModel):
    full_name: Optional[str] = None
    date_of_birth: Optional[str] = None
    gender: Optional[str] = None
    class_id: Optional[int] = None
    avatar: Optional[str] = None
    status: Optional[str] = None


@router.get("")
def list_students(
    class_id: Optional[int] = Query(None),
    current_user: dict = Depends(get_current_user)
):
    """Get all students. Teacher sees only their class, admin sees all."""
    df = excel_service.read_sheet("HocSinh")
    
    if current_user["role"] == "teacher":
        # Only students in teacher's class
        classes_df = excel_service.read_sheet("LopHoc")
        teacher_classes = classes_df[classes_df["teacher_id"].astype(str) == str(current_user["user_id"])]["class_id"].tolist()
        df = df[df["class_id"].isin([str(c) for c in teacher_classes])]
    
    if class_id:
        df = df[df["class_id"].astype(str) == str(class_id)]
    
    students = df.to_dict(orient="records")
    
    # Enrich with rank info
    for s in students:
        rank_info = calculate_rank(float(s.get("total_score", 0)), s.get("gender", "female"))
        s.update(rank_info)
    
    return sorted(students, key=lambda x: float(x.get("total_score", 0)), reverse=True)


@router.get("/{student_id}")
def get_student(student_id: int, current_user: dict = Depends(get_current_user)):
    """Get a specific student."""
    student = excel_service.find_one("HocSinh", "student_id", student_id)
    if not student:
        raise HTTPException(status_code=404, detail="Học sinh không tồn tại")
    
    # Students can only view their own profile
    if current_user["role"] == "student":
        if str(current_user.get("student_id")) != str(student_id):
            raise HTTPException(status_code=403, detail="Không có quyền xem thông tin này")
    
    rank_info = calculate_rank(float(student.get("total_score", 0)), student.get("gender", "female"))
    student.update(rank_info)
    return student


@router.post("", status_code=201)
def create_student(data: StudentCreate, current_user: dict = Depends(require_admin)):
    """Create a new student (Admin only)."""
    # Check unique student_code
    existing = excel_service.find_one("HocSinh", "student_code", data.student_code)
    if existing:
        raise HTTPException(status_code=400, detail="Mã học sinh đã tồn tại")
    
    # Check unique username
    existing_user = excel_service.find_one("Users", "username", data.username)
    if existing_user:
        raise HTTPException(status_code=400, detail="Tên đăng nhập đã tồn tại")
    
    student_id = excel_service.get_next_id("HocSinh", "student_id")
    now = datetime.now().isoformat()
    
    # Create HocSinh record
    excel_service.insert_row("HocSinh", {
        "student_id": student_id,
        "student_code": data.student_code,
        "full_name": data.full_name,
        "date_of_birth": data.date_of_birth,
        "gender": data.gender,
        "class_id": data.class_id or "",
        "total_score": 0,
        "rank": "Cung Nữ" if data.gender == "female" else "Nô Tài",
        "rank_level": 1,
        "avatar": data.avatar or "",
        "status": "active",
        "created_at": now,
    })
    
    # Create user account
    user_id = excel_service.get_next_id("Users", "user_id")
    excel_service.insert_row("Users", {
        "user_id": user_id,
        "username": data.username,
        "password_hash": hash_password(data.password),
        "full_name": data.full_name,
        "role": "student",
        "student_id": student_id,
        "class_id": data.class_id or "",
        "status": "active",
        "created_at": now,
    })
    
    return {"message": "Tạo học sinh thành công", "student_id": student_id}


@router.put("/{student_id}")
def update_student(student_id: int, data: StudentUpdate, current_user: dict = Depends(require_admin)):
    """Update student info (Admin only)."""
    student = excel_service.find_one("HocSinh", "student_id", student_id)
    if not student:
        raise HTTPException(status_code=404, detail="Học sinh không tồn tại")
    
    updates = {k: v for k, v in data.dict().items() if v is not None}
    excel_service.update_row("HocSinh", "student_id", student_id, updates)
    return {"message": "Cập nhật thành công"}


@router.delete("/{student_id}")
def delete_student(student_id: int, current_user: dict = Depends(require_admin)):
    """Soft-delete a student (Admin only)."""
    student = excel_service.find_one("HocSinh", "student_id", student_id)
    if not student:
        raise HTTPException(status_code=404, detail="Học sinh không tồn tại")
    
    excel_service.update_row("HocSinh", "student_id", student_id, {"status": "inactive"})
    excel_service.update_row("Users", "student_id", student_id, {"status": "inactive"})
    return {"message": "Xóa học sinh thành công"}


@router.get("/{student_id}/scores")
def get_student_scores(
    student_id: int,
    score_type: Optional[str] = Query(None),
    current_user: dict = Depends(get_current_user)
):
    """Get score history for a student."""
    if current_user["role"] == "student" and str(current_user.get("student_id")) != str(student_id):
        raise HTTPException(status_code=403, detail="Không có quyền xem")
    
    df = excel_service.read_sheet("Diem")
    df = df[df["student_id"].astype(str) == str(student_id)]
    
    if score_type:
        df = df[df["type"] == score_type]
    
    df = df.sort_values("created_at", ascending=False)
    return df.to_dict(orient="records")


@router.get("/{student_id}/rank")
def get_student_rank(student_id: int, current_user: dict = Depends(get_current_user)):
    """Get current rank info for a student."""
    from ..services.rank_service import get_next_rank_info
    
    student = excel_service.find_one("HocSinh", "student_id", student_id)
    if not student:
        raise HTTPException(status_code=404, detail="Học sinh không tồn tại")
    
    total_score = float(student.get("total_score", 0))
    gender = student.get("gender", "female")
    rank_info = calculate_rank(total_score, gender)
    next_info = get_next_rank_info(total_score, gender)
    
    return {**student, **rank_info, **next_info}


@router.get("/{student_id}/achievements")
def get_achievements(student_id: int, current_user: dict = Depends(get_current_user)):
    df = excel_service.read_sheet("ThanhTich")
    result = df[df["student_id"].astype(str) == str(student_id)]
    return result.to_dict(orient="records")
