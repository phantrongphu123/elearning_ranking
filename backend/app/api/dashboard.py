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
    
    import pandas as pd
    classes_df = excel_service.read_sheet("LopHoc")
    t_uid = int(float(current_user["user_id"]))
    t_col = pd.to_numeric(classes_df["teacher_id"], errors="coerce").fillna(0).astype(int)
    teacher_classes = classes_df[t_col == t_uid]
    
    class_ids = [int(float(c)) for c in teacher_classes["class_id"].tolist() if pd.notna(c)]
    
    students_df = excel_service.read_sheet("HocSinh")
    assignments_df = excel_service.read_sheet("BaiTap")
    submissions_df = excel_service.read_sheet("BaiNop")
    
    s_class_col = pd.to_numeric(students_df["class_id"], errors="coerce").fillna(0).astype(int)
    teacher_students = students_df[s_class_col.isin(class_ids)]
    
    a_teacher_col = pd.to_numeric(assignments_df["teacher_id"], errors="coerce").fillna(0).astype(int)
    teacher_assignments = assignments_df[
        (a_teacher_col == t_uid) &
        (assignments_df["status"] != "inactive")
    ]
    
    # Ungraded submissions
    if not teacher_assignments.empty:
        assignment_ids = [int(float(a)) for a in teacher_assignments["assignment_id"].tolist() if pd.notna(a)]
        sub_asg_col = pd.to_numeric(submissions_df["assignment_id"], errors="coerce").fillna(0).astype(int)
        ungraded = submissions_df[
            (sub_asg_col.isin(assignment_ids)) &
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
    
    import pandas as pd
    student_id = current_user.get("student_id")
    student = None
    if student_id:
        student = excel_service.find_one("HocSinh", "student_id", student_id)
    
    # Fallback to search by username or full_name if not found by student_id
    if not student:
        username = current_user.get("username")
        if username:
            student = excel_service.find_one("HocSinh", "student_code", username)
    if not student:
        full_name = current_user.get("full_name")
        if full_name:
            student = excel_service.find_one("HocSinh", "full_name", full_name)
    
    if not student:
        from fastapi import HTTPException
        raise HTTPException(status_code=404, detail="Không tìm thấy học sinh")
    
    s_id = int(float(student.get("student_id")))
    from ..services.rank_service import get_next_rank_info
    
    total_score = float(student.get("total_score", 0))
    gender = student.get("gender", "female")
    rank_info = calculate_rank(total_score, gender)
    next_rank = get_next_rank_info(total_score, gender)
    
    # Submissions stats
    subs_df = excel_service.read_sheet("BaiNop")
    sub_s_col = pd.to_numeric(subs_df["student_id"], errors="coerce").fillna(0).astype(int)
    student_subs = subs_df[sub_s_col == s_id]
    on_time = student_subs[student_subs["is_late"].astype(str).str.lower().isin(["false", "0"])]
    late = student_subs[student_subs["is_late"].astype(str).str.lower().isin(["true", "1"])]
    
    # Pending assignments
    class_id = student.get("class_id")
    assignments_df = excel_service.read_sheet("BaiTap")
    if class_id:
        c_id = int(float(class_id))
        asg_c_col = pd.to_numeric(assignments_df["class_id"], errors="coerce").fillna(0).astype(int)
        class_assignments = assignments_df[
            (asg_c_col == c_id) &
            (assignments_df["status"] != "inactive")
        ]
        submitted_ids = [int(float(x)) for x in student_subs["assignment_id"].tolist() if pd.notna(x)]
        asg_id_col = pd.to_numeric(class_assignments["assignment_id"], errors="coerce").fillna(0).astype(int)
        pending = class_assignments[~asg_id_col.isin(submitted_ids)]
    else:
        pending = assignments_df.head(0)
    
    # Score breakdown
    scores_df = excel_service.read_sheet("Diem")
    score_s_col = pd.to_numeric(scores_df["student_id"], errors="coerce").fillna(0).astype(int)
    student_scores = scores_df[score_s_col == s_id]
    scores_pts = pd.to_numeric(student_scores["points"], errors="coerce").fillna(0)
    homework_score = float(scores_pts[student_scores["type"] == "homework"].sum())
    attendance_score = float(scores_pts[student_scores["type"] == "attendance"].sum())
    bonus_score = float(scores_pts[student_scores["type"].isin(["bonus", "manual"])].sum())
    
    # Leaderboard position
    all_students = excel_service.read_sheet("HocSinh")
    all_students = all_students[all_students["status"] != "inactive"]
    all_students["total_score"] = pd.to_numeric(all_students["total_score"], errors="coerce").fillna(0).astype(float)
    sorted_students = all_students.sort_values("total_score", ascending=False).reset_index(drop=True)
    sorted_s_col = pd.to_numeric(sorted_students["student_id"], errors="coerce").fillna(0).astype(int)
    position_rows = sorted_students[sorted_s_col == s_id]
    position = int(position_rows.index[0]) + 1 if not position_rows.empty else "-"
    
    # Attendance streak / absence calculation
    attendance_df = excel_service.read_sheet("DiemDanh")
    if not attendance_df.empty and "student_id" in attendance_df.columns:
        att_s_col = pd.to_numeric(attendance_df["student_id"], errors="coerce").fillna(0).astype(int)
        student_absent = attendance_df[
            (att_s_col == s_id) &
            (attendance_df["status"].isin(["absent_unexcused", "absent_excused"]))
        ]
        absent_count = len(student_absent)
        present_count = len(attendance_df[(att_s_col == s_id) & (attendance_df["status"] == "present")])
        
        if present_count > 0:
            streak = present_count
        else:
            c_col = pd.to_numeric(attendance_df["class_id"], errors="coerce").fillna(0).astype(int)
            total_sessions = attendance_df[c_col == int(float(class_id or 0))]["date"].nunique() if class_id else 0
            streak = max(0, total_sessions - absent_count)
    else:
        streak = 0
    
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
