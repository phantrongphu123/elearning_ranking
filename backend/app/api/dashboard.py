from fastapi import APIRouter, Depends
from ..core.dependencies import get_current_user, require_admin
from ..services.excel_service import ExcelService
from ..services.rank_service import calculate_rank

router = APIRouter(prefix="/api/dashboard", tags=["Dashboard"])
excel_service = ExcelService()


@router.get("/admin")
def admin_dashboard(current_user: dict = Depends(require_admin)):
    students_df = excel_service.read_sheet("HocSinh")
    classes_df = excel_service.read_sheet("LopHoc")
    assignments_df = excel_service.read_sheet("BaiTap")
    submissions_df = excel_service.read_sheet("BaiNop")
    users_df = excel_service.read_sheet("Users")
    
    active_students = students_df[students_df["status"] != "inactive"]
    teachers = users_df[users_df["role"] == "teacher"]
    
    # Top students
    top_students = active_students.copy()
    top_students["total_score"] = top_students["total_score"].astype(float)
    top_5 = top_students.nlargest(5, "total_score").to_dict(orient="records")
    
    for s in top_5:
        rank_info = calculate_rank(float(s.get("total_score", 0)), s.get("gender", "female"))
        s.update(rank_info)
    
    # Rank distribution
    rank_counts = {}
    for _, s in active_students.iterrows():
        r = calculate_rank(float(s.get("total_score", 0)), s.get("gender", "female"))
        rank = r["rank"]
        rank_counts[rank] = rank_counts.get(rank, 0) + 1
    
    # Average score
    avg_score = active_students["total_score"].astype(float).mean() if not active_students.empty else 0
    
    # Submissions this week
    from datetime import datetime, timedelta
    week_ago = (datetime.now() - timedelta(days=7)).isoformat()
    recent_subs = submissions_df[submissions_df["submitted_at"] >= week_ago] if not submissions_df.empty else submissions_df
    
    return {
        "total_students": len(active_students),
        "total_classes": len(classes_df[classes_df["status"] != "inactive"]),
        "total_teachers": len(teachers[teachers["status"] == "active"]),
        "total_assignments": len(assignments_df[assignments_df["status"] != "inactive"]),
        "total_submissions": len(submissions_df),
        "avg_score": round(float(avg_score), 2),
        "submissions_this_week": len(recent_subs),
        "top_students": top_5,
        "rank_distribution": rank_counts,
    }


@router.get("/teacher")
def teacher_dashboard(current_user: dict = Depends(get_current_user)):
    if current_user["role"] not in ["admin", "teacher"]:
        from fastapi import HTTPException
        raise HTTPException(status_code=403, detail="Không có quyền")
    
    classes_df = excel_service.read_sheet("LopHoc")
    teacher_classes = classes_df[classes_df["teacher_id"].astype(str) == str(current_user["user_id"])]
    
    class_ids = teacher_classes["class_id"].tolist()
    
    students_df = excel_service.read_sheet("HocSinh")
    assignments_df = excel_service.read_sheet("BaiTap")
    submissions_df = excel_service.read_sheet("BaiNop")
    
    teacher_students = students_df[students_df["class_id"].isin([str(c) for c in class_ids])]
    teacher_assignments = assignments_df[
        (assignments_df["teacher_id"].astype(str) == str(current_user["user_id"])) &
        (assignments_df["status"] != "inactive")
    ]
    
    # Ungraded submissions
    if not teacher_assignments.empty:
        assignment_ids = teacher_assignments["assignment_id"].tolist()
        ungraded = submissions_df[
            (submissions_df["assignment_id"].isin([str(a) for a in assignment_ids])) &
            (submissions_df["status"] != "graded")
        ]
    else:
        ungraded = submissions_df.head(0)
    
    return {
        "teacher_name": current_user.get("full_name", ""),
        "classes": teacher_classes.to_dict(orient="records"),
        "total_students": len(teacher_students),
        "active_assignments": len(teacher_assignments),
        "ungraded_count": len(ungraded),
    }


@router.get("/student")
def student_dashboard(current_user: dict = Depends(get_current_user)):
    if current_user["role"] != "student":
        from fastapi import HTTPException
        raise HTTPException(status_code=403, detail="Không có quyền")
    
    student_id = current_user.get("student_id")
    student = excel_service.find_one("HocSinh", "student_id", student_id)
    
    if not student:
        from fastapi import HTTPException
        raise HTTPException(status_code=404, detail="Không tìm thấy học sinh")
    
    from ..services.rank_service import get_next_rank_info
    
    total_score = float(student.get("total_score", 0))
    gender = student.get("gender", "female")
    rank_info = calculate_rank(total_score, gender)
    next_rank = get_next_rank_info(total_score, gender)
    
    # Submissions stats
    subs_df = excel_service.read_sheet("BaiNop")
    student_subs = subs_df[subs_df["student_id"].astype(str) == str(student_id)]
    on_time = student_subs[student_subs["is_late"].astype(str) == "False"]
    late = student_subs[student_subs["is_late"].astype(str) == "True"]
    
    # Pending assignments
    class_id = student.get("class_id")
    assignments_df = excel_service.read_sheet("BaiTap")
    if class_id:
        class_assignments = assignments_df[
            (assignments_df["class_id"].astype(str) == str(class_id)) &
            (assignments_df["status"] != "inactive")
        ]
        submitted_ids = student_subs["assignment_id"].tolist()
        pending = class_assignments[~class_assignments["assignment_id"].isin(submitted_ids)]
    else:
        pending = assignments_df.head(0)
    
    # Score breakdown
    scores_df = excel_service.read_sheet("Diem")
    student_scores = scores_df[scores_df["student_id"].astype(str) == str(student_id)]
    homework_score = float(student_scores[student_scores["type"] == "homework"]["points"].sum())
    attendance_score = float(student_scores[student_scores["type"] == "attendance"]["points"].sum())
    bonus_score = float(student_scores[student_scores["type"].isin(["bonus", "manual"])]["points"].sum())
    
    # Leaderboard position
    all_students = excel_service.read_sheet("HocSinh")
    all_students = all_students[all_students["status"] != "inactive"]
    all_students["total_score"] = all_students["total_score"].astype(float)
    sorted_students = all_students.sort_values("total_score", ascending=False).reset_index()
    position_rows = sorted_students[sorted_students["student_id"].astype(str) == str(student_id)]
    position = int(position_rows.index[0]) + 1 if not position_rows.empty else "-"
    
    # Attendance streak
    attendance_df = excel_service.read_sheet("DiemDanh")
    student_att = attendance_df[
        (attendance_df["student_id"].astype(str) == str(student_id)) &
        (attendance_df["status"] == "present")
    ]
    streak = len(student_att)  # Simplified streak count
    
    return {
        "student": student,
        **rank_info,
        **next_rank,
        "total_score": total_score,
        "position": position,
        "total_submissions": len(student_subs),
        "on_time_submissions": len(on_time),
        "late_submissions": len(late),
        "pending_assignments": len(pending),
        "attendance_streak": streak,
        "score_breakdown": {
            "homework": homework_score,
            "attendance": attendance_score,
            "bonus": bonus_score,
        }
    }
