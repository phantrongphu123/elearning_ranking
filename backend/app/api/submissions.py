from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from typing import Optional, Dict

from ..core.dependencies import get_current_user, require_teacher_or_admin
from ..services.excel_service import ExcelService
from ..services.assignment_service import process_submission
from ..services.score_service import add_score

router = APIRouter(prefix="/api/submissions", tags=["Submissions"])
excel_service = ExcelService()


class SubmissionCreate(BaseModel):
    assignment_id: int
    answers: Dict[str, str]  # {question_id: answer}


class GradeSubmission(BaseModel):
    score: Optional[float] = None
    teacher_comment: Optional[str] = ""


@router.post("", status_code=201)
def submit_assignment(data: SubmissionCreate, current_user: dict = Depends(get_current_user)):
    """Student submits an assignment."""
    if current_user["role"] != "student":
        raise HTTPException(status_code=403, detail="Chỉ học sinh mới có thể nộp bài")
    
    student_id = int(current_user.get("student_id", 0))
    if not student_id:
        raise HTTPException(status_code=400, detail="Không tìm thấy thông tin học sinh")
    
    result = process_submission(data.assignment_id, student_id, data.answers)
    
    if "error" in result:
        raise HTTPException(status_code=400, detail=result["error"])
    
    return result


@router.get("")
def list_submissions(current_user: dict = Depends(get_current_user)):
    """List submissions. Students see their own, teachers see their class."""
    df = excel_service.read_sheet("BaiNop")
    
    if current_user["role"] == "student":
        df = df[df["student_id"].astype(str) == str(current_user.get("student_id"))]
    elif current_user["role"] == "teacher":
        # Filter by teacher's assignments
        assignments_df = excel_service.read_sheet("BaiTap")
        teacher_assignments = assignments_df[assignments_df["teacher_id"].astype(str) == str(current_user["user_id"])]["assignment_id"].tolist()
        df = df[df["assignment_id"].isin([str(a) for a in teacher_assignments])]
    
    submissions = df.to_dict(orient="records")
    
    # Enrich with student name and assignment title
    students_df = excel_service.read_sheet("HocSinh")
    assignments_df = excel_service.read_sheet("BaiTap")
    
    for sub in submissions:
        s_row = students_df[students_df["student_id"].astype(str) == str(sub.get("student_id", ""))]
        if not s_row.empty:
            sub["student_name"] = s_row.iloc[0].get("full_name", "")
        
        a_row = assignments_df[assignments_df["assignment_id"].astype(str) == str(sub.get("assignment_id", ""))]
        if not a_row.empty:
            sub["assignment_title"] = a_row.iloc[0].get("title", "")
    
    return submissions


@router.get("/{submission_id}")
def get_submission(submission_id: int, current_user: dict = Depends(get_current_user)):
    submission = excel_service.find_one("BaiNop", "submission_id", submission_id)
    if not submission:
        raise HTTPException(status_code=404, detail="Bài nộp không tồn tại")
    
    if current_user["role"] == "student" and str(submission.get("student_id")) != str(current_user.get("student_id")):
        raise HTTPException(status_code=403, detail="Không có quyền xem")
    
    # Get details
    details_df = excel_service.read_sheet("ChiTietBaiNop")
    details = details_df[details_df["submission_id"].astype(str) == str(submission_id)].to_dict(orient="records")
    
    # Get questions for context
    questions_df = excel_service.read_sheet("CauHoi")
    for d in details:
        q = questions_df[questions_df["question_id"].astype(str) == str(d.get("question_id", ""))]
        if not q.empty:
            d["question_text"] = q.iloc[0].get("question_text", "")
            d["correct_answer"] = q.iloc[0].get("correct_answer", "")  # Reveal after submission
    
    submission["details"] = details
    return submission


@router.put("/{submission_id}/grade")
def grade_submission(submission_id: int, data: GradeSubmission, current_user: dict = Depends(require_teacher_or_admin)):
    """Teacher manually grades or adjusts a submission."""
    submission = excel_service.find_one("BaiNop", "submission_id", submission_id)
    if not submission:
        raise HTTPException(status_code=404, detail="Bài nộp không tồn tại")
    
    updates = {"status": "graded"}
    if data.score is not None:
        updates["score"] = data.score
    if data.teacher_comment:
        updates["teacher_comment"] = data.teacher_comment
    
    excel_service.update_row("BaiNop", "submission_id", submission_id, updates)
    
    # If score was adjusted, add a manual score entry
    if data.score is not None:
        old_score = float(submission.get("score", 0))
        diff = data.score - old_score
        if diff != 0:
            add_score(
                int(submission["student_id"]),
                "manual",
                f"Điều chỉnh điểm bài nộp #{submission_id}",
                diff,
                submission.get("assignment_id"),
                current_user["username"]
            )
    
    return {"message": "Chấm bài thành công"}
