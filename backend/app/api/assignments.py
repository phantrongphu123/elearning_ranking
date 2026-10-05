from fastapi import APIRouter, HTTPException, Depends, Query
from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime

from ..core.dependencies import get_current_user, require_teacher_or_admin
from ..services.excel_service import ExcelService

router = APIRouter(prefix="/api/assignments", tags=["Assignments"])
excel_service = ExcelService()


class QuestionCreate(BaseModel):
    question_type: str = "multiple_choice"  # multiple_choice, true_false, short_answer
    question_text: str
    option_a: Optional[str] = ""
    option_b: Optional[str] = ""
    option_c: Optional[str] = ""
    option_d: Optional[str] = ""
    correct_answer: str
    score: float = 10.0


class AssignmentCreate(BaseModel):
    title: str
    description: Optional[str] = ""
    subject: str
    class_id: int
    start_time: Optional[str] = None
    deadline: str
    max_score: float = 100
    bonus_score: float = 0
    penalty_score: float = 0
    questions: Optional[List[QuestionCreate]] = []


class AssignmentUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    deadline: Optional[str] = None
    max_score: Optional[float] = None
    bonus_score: Optional[float] = None
    penalty_score: Optional[float] = None
    status: Optional[str] = None


@router.get("")
def list_assignments(
    class_id: Optional[int] = Query(None),
    current_user: dict = Depends(get_current_user)
):
    df = excel_service.read_sheet("BaiTap")
    
    if current_user["role"] == "teacher":
        df = df[df["teacher_id"].astype(str) == str(current_user["user_id"])]
    elif current_user["role"] == "student":
        # Get student's class
        student = excel_service.find_one("HocSinh", "student_id", current_user.get("student_id"))
        if student:
            df = df[df["class_id"].astype(str) == str(student.get("class_id", ""))]
            # Only show assignments that have started
            now_str = datetime.now().isoformat()
            df = df[(df["start_time"] <= now_str) | (df["start_time"] == "")]
    
    if class_id:
        df = df[df["class_id"].astype(str) == str(class_id)]
    
    df = df[df["status"] != "inactive"]
    assignments = df.to_dict(orient="records")
    
    # Enrich with submission count
    submissions_df = excel_service.read_sheet("BaiNop")
    for a in assignments:
        count = len(submissions_df[submissions_df["assignment_id"].astype(str) == str(a.get("assignment_id", ""))])
        a["submission_count"] = count
        # Deadline status
        deadline_str = str(a.get("deadline", ""))
        if deadline_str:
            try:
                a["is_past_deadline"] = datetime.now() > datetime.fromisoformat(deadline_str)
            except:
                a["is_past_deadline"] = False
    
    return assignments


@router.get("/{assignment_id}")
def get_assignment(assignment_id: int, current_user: dict = Depends(get_current_user)):
    assignment = excel_service.find_one("BaiTap", "assignment_id", assignment_id)
    if not assignment:
        raise HTTPException(status_code=404, detail="Bài tập không tồn tại")
    
    # Get questions (hide correct_answer for students before submission)
    questions_df = excel_service.read_sheet("CauHoi")
    questions = questions_df[questions_df["assignment_id"].astype(str) == str(assignment_id)].to_dict(orient="records")
    
    if current_user["role"] == "student":
        for q in questions:
            q.pop("correct_answer", None)
    
    assignment["questions"] = questions
    return assignment


@router.post("", status_code=201)
def create_assignment(data: AssignmentCreate, current_user: dict = Depends(require_teacher_or_admin)):
    assignment_id = excel_service.get_next_id("BaiTap", "assignment_id")
    now = datetime.now().isoformat()
    
    excel_service.insert_row("BaiTap", {
        "assignment_id": assignment_id,
        "title": data.title,
        "description": data.description,
        "subject": data.subject,
        "class_id": data.class_id,
        "teacher_id": current_user["user_id"],
        "created_at": now,
        "start_time": data.start_time or now,
        "deadline": data.deadline,
        "max_score": data.max_score,
        "bonus_score": data.bonus_score,
        "penalty_score": data.penalty_score,
        "status": "active",
    })
    
    # Save questions
    for q in (data.questions or []):
        q_id = excel_service.get_next_id("CauHoi", "question_id")
        excel_service.insert_row("CauHoi", {
            "question_id": q_id,
            "assignment_id": assignment_id,
            "question_type": q.question_type,
            "question_text": q.question_text,
            "option_a": q.option_a,
            "option_b": q.option_b,
            "option_c": q.option_c,
            "option_d": q.option_d,
            "correct_answer": q.correct_answer,
            "score": q.score,
        })
    
    return {"message": "Tạo bài tập thành công", "assignment_id": assignment_id}


@router.put("/{assignment_id}")
def update_assignment(assignment_id: int, data: AssignmentUpdate, current_user: dict = Depends(require_teacher_or_admin)):
    assignment = excel_service.find_one("BaiTap", "assignment_id", assignment_id)
    if not assignment:
        raise HTTPException(status_code=404, detail="Bài tập không tồn tại")
    
    # Teacher can only edit their own assignments
    if current_user["role"] == "teacher" and str(assignment.get("teacher_id")) != str(current_user["user_id"]):
        raise HTTPException(status_code=403, detail="Không có quyền sửa bài tập này")
    
    updates = {k: v for k, v in data.dict().items() if v is not None}
    excel_service.update_row("BaiTap", "assignment_id", assignment_id, updates)
    return {"message": "Cập nhật thành công"}


@router.delete("/{assignment_id}")
def delete_assignment(assignment_id: int, current_user: dict = Depends(require_teacher_or_admin)):
    assignment = excel_service.find_one("BaiTap", "assignment_id", assignment_id)
    if not assignment:
        raise HTTPException(status_code=404, detail="Bài tập không tồn tại")
    excel_service.update_row("BaiTap", "assignment_id", assignment_id, {"status": "inactive"})
    return {"message": "Xóa bài tập thành công"}


@router.get("/{assignment_id}/questions")
def get_questions(assignment_id: int, current_user: dict = Depends(get_current_user)):
    df = excel_service.read_sheet("CauHoi")
    questions = df[df["assignment_id"].astype(str) == str(assignment_id)].to_dict(orient="records")
    if current_user["role"] == "student":
        for q in questions:
            q.pop("correct_answer", None)
    return questions


@router.post("/{assignment_id}/questions", status_code=201)
def add_question(assignment_id: int, data: QuestionCreate, current_user: dict = Depends(require_teacher_or_admin)):
    q_id = excel_service.get_next_id("CauHoi", "question_id")
    excel_service.insert_row("CauHoi", {
        "question_id": q_id,
        "assignment_id": assignment_id,
        "question_type": data.question_type,
        "question_text": data.question_text,
        "option_a": data.option_a,
        "option_b": data.option_b,
        "option_c": data.option_c,
        "option_d": data.option_d,
        "correct_answer": data.correct_answer,
        "score": data.score,
    })
    return {"message": "Thêm câu hỏi thành công", "question_id": q_id}


@router.delete("/questions/{question_id}")
def delete_question(question_id: int, current_user: dict = Depends(require_teacher_or_admin)):
    excel_service.delete_row("CauHoi", "question_id", question_id)
    return {"message": "Xóa câu hỏi thành công"}
