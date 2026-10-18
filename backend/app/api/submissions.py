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
    import pandas as pd
    df = excel_service.read_sheet("BaiNop")
    if df.empty:
        return []
    
    if current_user["role"] == "student":
        student_id = current_user.get("student_id")
        if not student_id:
            student = excel_service.find_one("HocSinh", "student_code", current_user.get("username", ""))
            if student:
                student_id = student.get("student_id")
        if not student_id:
            student = excel_service.find_one("HocSinh", "full_name", current_user.get("full_name", ""))
            if student:
                student_id = student.get("student_id")
                
        if student_id:
            s_id = int(float(student_id))
            sub_s_col = pd.to_numeric(df["student_id"], errors="coerce").fillna(0).astype(int)
            df = df[sub_s_col == s_id]
        else:
            return []
    elif current_user["role"] == "teacher":
        # Filter by teacher's assignments
        teacher_uid = int(float(current_user["user_id"]))
        assignments_df = excel_service.read_sheet("BaiTap")
        if not assignments_df.empty and "teacher_id" in assignments_df.columns:
            t_asg_col = pd.to_numeric(assignments_df["teacher_id"], errors="coerce").fillna(0).astype(int)
            teacher_asg_ids = [int(float(a)) for a in assignments_df[t_asg_col == teacher_uid]["assignment_id"].tolist() if pd.notna(a)]
            
            sub_asg_col = pd.to_numeric(df["assignment_id"], errors="coerce").fillna(0).astype(int)
            df = df[sub_asg_col.isin(teacher_asg_ids)]
        else:
            return []
    
    submissions = df.to_dict(orient="records")
    
    # Enrich with student name and assignment title
    students_df = excel_service.read_sheet("HocSinh")
    assignments_df = excel_service.read_sheet("BaiTap")
    
    students_map = {}
    if not students_df.empty and "student_id" in students_df.columns:
        for _, row in students_df.iterrows():
            try:
                sid = int(float(row["student_id"]))
                students_map[sid] = row.get("full_name", "")
            except Exception:
                pass
                
    assignments_map = {}
    if not assignments_df.empty and "assignment_id" in assignments_df.columns:
        for _, row in assignments_df.iterrows():
            try:
                aid = int(float(row["assignment_id"]))
                assignments_map[aid] = row.get("title", "")
            except Exception:
                pass
    
    for sub in submissions:
        sid = int(float(sub.get("student_id") or 0))
        aid = int(float(sub.get("assignment_id") or 0))
        sub["student_name"] = students_map.get(sid, f"Học tử #{sid}")
        sub["assignment_title"] = assignments_map.get(aid, f"Tấu chương #{aid}")
    
    return submissions


@router.get("/{submission_id}")
def get_submission(submission_id: int, current_user: dict = Depends(get_current_user)):
    import pandas as pd
    submission = excel_service.find_one("BaiNop", "submission_id", submission_id)
    if not submission:
        raise HTTPException(status_code=404, detail="Bài nộp không tồn tại")
    
    sub_sid = int(float(submission.get("student_id") or 0))
    user_sid = int(float(current_user.get("student_id") or 0))
    if current_user["role"] == "student" and sub_sid != user_sid:
        raise HTTPException(status_code=403, detail="Không có quyền xem")
    
    # Get details
    details_df = excel_service.read_sheet("ChiTietBaiNop")
    sub_id_int = int(float(submission_id))
    if not details_df.empty and "submission_id" in details_df.columns:
        d_sub_col = pd.to_numeric(details_df["submission_id"], errors="coerce").fillna(0).astype(int)
        details = details_df[d_sub_col == sub_id_int].to_dict(orient="records")
    else:
        details = []
    
    # Get questions for context
    questions_df = excel_service.read_sheet("CauHoi")
    if not questions_df.empty and "question_id" in questions_df.columns:
        q_id_col = pd.to_numeric(questions_df["question_id"], errors="coerce").fillna(0).astype(int)
        for d in details:
            qid = int(float(d.get("question_id") or 0))
            q = questions_df[q_id_col == qid]
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
