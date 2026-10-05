from ..services.excel_service import ExcelService
from ..core.config import DEFAULT_RANKS

excel_service = ExcelService()


def get_rank_config() -> list:
    """Return rank config from DB if exists, else use defaults."""
    df = excel_service.read_sheet("RankConfig")
    if not df.empty:
        return df.to_dict(orient="records")
    return DEFAULT_RANKS


def calculate_rank(total_score: float, gender: str = "female") -> dict:
    """Calculate rank name and level based on total score and gender."""
    ranks = get_rank_config()
    total_score = float(total_score)
    for rank in sorted(ranks, key=lambda x: float(x.get("min_score", 0))):
        min_s = float(rank.get("min_score", 0))
        max_s = float(rank.get("max_score", 999999))
        if min_s <= total_score <= max_s:
            # Support both DEFAULT_RANKS format and RankConfig sheet format
            if "male" in rank:
                rank_name = rank["male"] if gender == "male" else rank["female"]
                return {
                    "rank": rank_name,
                    "rank_level": rank.get("level", 1),
                    "color": rank.get("color", "#888"),
                    "icon": rank.get("icon", "📜"),
                }
            else:
                rank_name = rank.get("male_name") if gender == "male" else rank.get("female_name")
                return {
                    "rank": rank_name,
                    "rank_level": rank.get("level", 1),
                    "color": rank.get("color", "#888"),
                    "icon": rank.get("icon", "📜"),
                }
    # Default
    return {"rank": "Nô Tài" if gender == "male" else "Cung Nữ", "rank_level": 1, "color": "#8B7355", "icon": "🪨"}


def get_next_rank_info(total_score: float, gender: str = "female") -> dict:
    """Get info about the next rank level."""
    ranks = get_rank_config()
    total_score = float(total_score)
    sorted_ranks = sorted(ranks, key=lambda x: float(x.get("min_score", 0)))
    
    for i, rank in enumerate(sorted_ranks):
        min_s = float(rank.get("min_score", 0))
        max_s = float(rank.get("max_score", 999999))
        if min_s <= total_score <= max_s:
            if i + 1 < len(sorted_ranks):
                next_rank = sorted_ranks[i + 1]
                next_min = float(next_rank.get("min_score", 0))
                needed = max(0, next_min - total_score)
                progress_pct = ((total_score - min_s) / (next_min - min_s) * 100) if next_min > min_s else 100
                next_name = next_rank.get("male" if gender == "male" else "female") or next_rank.get("male_name" if gender == "male" else "female_name", "Tối cao")
                return {
                    "next_rank": next_name,
                    "next_min_score": next_min,
                    "points_needed": needed,
                    "progress_pct": min(100, round(progress_pct, 1)),
                }
            else:
                return {"next_rank": None, "next_min_score": None, "points_needed": 0, "progress_pct": 100}
    return {}


def update_student_rank(student_id: int, new_total_score: float, created_by: str = "system"):
    """Update student's total_score and rank. Log to RankHistory if rank changed."""
    student = excel_service.find_one("HocSinh", "student_id", student_id)
    if not student:
        return
    
    gender = student.get("gender", "female")
    old_rank = student.get("rank", "")
    rank_info = calculate_rank(new_total_score, gender)
    new_rank = rank_info["rank"]
    
    # Update student record
    excel_service.update_row("HocSinh", "student_id", student_id, {
        "total_score": new_total_score,
        "rank": new_rank,
        "rank_level": rank_info["rank_level"],
    })
    
    # Log rank change
    if old_rank != new_rank:
        from datetime import datetime
        history_id = excel_service.get_next_id("RankHistory", "history_id")
        excel_service.insert_row("RankHistory", {
            "history_id": history_id,
            "student_id": student_id,
            "old_rank": old_rank,
            "new_rank": new_rank,
            "total_score": new_total_score,
            "changed_at": datetime.now().isoformat(),
            "reason": f"Tổng điểm cập nhật: {new_total_score}",
        })
    
    return rank_info
