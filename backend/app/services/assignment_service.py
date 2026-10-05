from datetime import datetime
from ..services.excel_service import ExcelService
from ..services.score_service import add_score, check_and_unlock_achievements

excel_service = ExcelService()


def process_submission(assignment_id: int, student_id: int, answers: dict) -> dict:
    """
    Full submission processing pipeline:
    1. Check deadline
    2. Grade answers
    3. Apply bonus/penalty
    4. Write to BaiNop, ChiTietBaiNop
    5. Call score_service to update Diem and rank
    """
    # Get assignment
    assignment = excel_service.find_one("BaiTap", "assignment_id", assignment_id)
    if not assignment:
        return {"error": "Bài tập không tồn tại"}

    # Check deadline
    now = datetime.now()
    deadline_str = str(assignment.get("deadline", ""))
    is_late = False
    if deadline_str:
        try:
            deadline = datetime.fromisoformat(deadline_str)
            is_late = now > deadline
        except:
            pass

    # Check if already submitted
    bainop_df = excel_service.read_sheet("BaiNop")
    existing = bainop_df[
        (bainop_df["assignment_id"].astype(str) == str(assignment_id)) &
        (bainop_df["student_id"].astype(str) == str(student_id))
    ]
    if not existing.empty:
        return {"error": "Bạn đã nộp bài này rồi"}

    # Get questions and grade
    questions_df = excel_service.read_sheet("CauHoi")
    assignment_questions = questions_df[questions_df["assignment_id"].astype(str) == str(assignment_id)]
    
    total_possible = 0
    earned_score = 0
    detail_rows = []
    
    for _, q in assignment_questions.iterrows():
        q_id = str(q["question_id"])
        student_ans = str(answers.get(q_id, "")).strip().lower()
        correct_ans = str(q.get("correct_answer", "")).strip().lower()
        q_score = float(q.get("score", 0))
        total_possible += q_score
        
        q_type = str(q.get("question_type", "multiple_choice"))
        
        is_correct = False
        if q_type in ["multiple_choice", "true_false"]:
            is_correct = student_ans == correct_ans
        elif q_type == "short_answer":
            is_correct = student_ans == correct_ans  # exact match for now

        scored = q_score if is_correct else 0
        earned_score += scored
        
        detail_id = excel_service.get_next_id("ChiTietBaiNop", "submission_detail_id")
        detail_rows.append({
            "submission_detail_id": detail_id,
            "submission_id": None,  # will fill after creating BaiNop
            "question_id": q["question_id"],
            "student_answer": answers.get(q_id, ""),
            "correct": str(is_correct),
            "score": scored,
        })

    # Calculate percentage score (out of max_score)
    max_score = float(assignment.get("max_score", 100))
    pct_score = (earned_score / total_possible * max_score) if total_possible > 0 else 0
    
    # Apply bonus/penalty
    bonus = float(assignment.get("bonus_score", 0))
    penalty = float(assignment.get("penalty_score", 0))
    
    # On-time bonus
    if not is_late:
        points_to_add = pct_score + bonus + 10  # +10 for on-time submission
    else:
        points_to_add = pct_score - penalty
    
    points_to_add = max(0, points_to_add)  # Cannot go negative from a submission
    
    # Write BaiNop
    submission_id = excel_service.get_next_id("BaiNop", "submission_id")
    excel_service.insert_row("BaiNop", {
        "submission_id": submission_id,
        "assignment_id": assignment_id,
        "student_id": student_id,
        "submitted_at": now.isoformat(),
        "status": "graded",
        "score": round(pct_score, 2),
        "is_late": str(is_late),
        "teacher_comment": "",
    })
    
    # Write ChiTietBaiNop
    for detail in detail_rows:
        detail["submission_id"] = submission_id
        excel_service.insert_row("ChiTietBaiNop", detail)
    
    # Write LichSuNopBai
    history_id = excel_service.get_next_id("LichSuNopBai", "history_id")
    excel_service.insert_row("LichSuNopBai", {
        "history_id": history_id,
        "student_id": student_id,
        "assignment_id": assignment_id,
        "submitted_at": now.isoformat(),
        "deadline": deadline_str,
        "status": "late" if is_late else "on_time",
        "score": round(pct_score, 2),
        "is_late": str(is_late),
    })
    
    # Update score
    reason = f"Nộp bài: {assignment.get('title', '')} {'(trễ hạn)' if is_late else '(đúng hạn)'}"
    score_result = add_score(student_id, "homework", reason, points_to_add, assignment_id, "system")
    
    # Check achievements
    check_and_unlock_achievements(student_id)
    
    return {
        "submission_id": submission_id,
        "score": round(pct_score, 2),
        "is_late": is_late,
        "points_added": round(points_to_add, 2),
        "new_total": score_result["new_total"],
        "rank_info": score_result.get("rank_info"),
    }
