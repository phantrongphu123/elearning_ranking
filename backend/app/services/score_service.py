from datetime import datetime
from ..services.excel_service import ExcelService
from ..services.rank_service import update_student_rank

excel_service = ExcelService()


def add_score(student_id: int, score_type: str, reason: str, points: float,
              assignment_id: int = None, created_by: str = "system") -> dict:
    """
    Add a score entry to the Diem sheet and update student total_score.
    This is the ONLY safe way to change a student's score.
    """
    score_id = excel_service.get_next_id("Diem", "score_id")
    score_entry = {
        "score_id": score_id,
        "student_id": student_id,
        "type": score_type,
        "reason": reason,
        "points": points,
        "assignment_id": assignment_id or "",
        "created_at": datetime.now().isoformat(),
        "created_by": created_by,
    }
    excel_service.insert_row("Diem", score_entry)
    
    # Recalculate total score from all Diem entries for safety
    diem_df = excel_service.read_sheet("Diem")
    student_scores = diem_df[diem_df["student_id"].astype(str) == str(student_id)]
    new_total = float(student_scores["points"].sum())
    
    # Update rank
    rank_info = update_student_rank(student_id, new_total, created_by)
    
    # Create notification
    _create_score_notification(student_id, points, reason)
    
    return {"new_total": new_total, "rank_info": rank_info}


def _create_score_notification(student_id: int, points: float, reason: str):
    """Create a notification for the student about their score change."""
    # Find user_id from student_id
    users_df = excel_service.read_sheet("Users")
    user_row = users_df[users_df["student_id"].astype(str) == str(student_id)]
    if user_row.empty:
        return
    user_id = user_row.iloc[0]["user_id"]
    
    direction = "+" if float(points) >= 0 else ""
    notif_id = excel_service.get_next_id("ThongBao", "notification_id")
    excel_service.insert_row("ThongBao", {
        "notification_id": notif_id,
        "user_id": user_id,
        "title": "Điểm cập nhật",
        "message": f"🔔 {direction}{points} điểm - {reason}",
        "type": "score",
        "is_read": "false",
        "created_at": datetime.now().isoformat(),
    })


def check_and_unlock_achievements(student_id: int):
    """Check and auto-unlock achievements for a student."""
    submissions_df = excel_service.read_sheet("BaiNop")
    scores_df = excel_service.read_sheet("Diem")
    achieved_df = excel_service.read_sheet("ThanhTich")
    
    student_subs = submissions_df[submissions_df["student_id"].astype(str) == str(student_id)]
    student_achieved = achieved_df[achieved_df["student_id"].astype(str) == str(student_id)]
    already_unlocked = set(student_achieved["achievement_code"].tolist())
    
    achievements_to_check = [
        {
            "code": "dung_han_10",
            "name": "Học Sinh Chăm Chỉ",
            "desc": "Nộp 10 bài đúng hạn",
            "icon": "🏆",
            "condition": lambda: len(student_subs[student_subs["is_late"].astype(str) == "False"]) >= 10
        },
        {
            "code": "perfect_score",
            "name": "Không Sai Câu Nào",
            "desc": "Đạt 100 điểm trong một bài",
            "icon": "💯",
            "condition": lambda: any(float(s) >= 100 for s in student_subs["score"].dropna().tolist())
        },
    ]
    
    for ach in achievements_to_check:
        if ach["code"] not in already_unlocked:
            try:
                if ach["condition"]():
                    ach_id = excel_service.get_next_id("ThanhTich", "achievement_id")
                    excel_service.insert_row("ThanhTich", {
                        "achievement_id": ach_id,
                        "student_id": student_id,
                        "achievement_code": ach["code"],
                        "achievement_name": ach["name"],
                        "description": ach["desc"],
                        "icon": ach["icon"],
                        "unlocked_at": datetime.now().isoformat(),
                    })
                    # Notify
                    _notify_achievement(student_id, ach["name"], ach["icon"])
            except:
                pass


def _notify_achievement(student_id: int, ach_name: str, icon: str):
    users_df = excel_service.read_sheet("Users")
    user_row = users_df[users_df["student_id"].astype(str) == str(student_id)]
    if user_row.empty:
        return
    user_id = user_row.iloc[0]["user_id"]
    notif_id = excel_service.get_next_id("ThongBao", "notification_id")
    excel_service.insert_row("ThongBao", {
        "notification_id": notif_id,
        "user_id": user_id,
        "title": "Thành tích mới!",
        "message": f"{icon} Bạn đã mở khóa thành tích: {ach_name}",
        "type": "achievement",
        "is_read": "false",
        "created_at": datetime.now().isoformat(),
    })
