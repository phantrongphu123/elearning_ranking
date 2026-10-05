from fastapi import APIRouter, Depends, Query
from typing import Optional

from ..core.dependencies import get_current_user
from ..services.excel_service import ExcelService
from ..services.rank_service import calculate_rank

router = APIRouter(prefix="/api/leaderboard", tags=["Leaderboard"])
excel_service = ExcelService()


@router.get("")
def get_leaderboard(
    class_id: Optional[int] = Query(None),
    limit: int = Query(50, ge=1, le=200),
    current_user: dict = Depends(get_current_user)
):
    """Get leaderboard, sorted by total_score descending."""
    df = excel_service.read_sheet("HocSinh")
    df = df[df["status"] != "inactive"]
    
    if class_id:
        df = df[df["class_id"].astype(str) == str(class_id)]
    
    students = df.to_dict(orient="records")
    
    # Get class names
    classes_df = excel_service.read_sheet("LopHoc")
    class_map = {str(r["class_id"]): r.get("class_name", "") for _, r in classes_df.iterrows()}
    
    for s in students:
        total = float(s.get("total_score", 0))
        gender = s.get("gender", "female")
        rank_info = calculate_rank(total, gender)
        s.update(rank_info)
        s["class_name"] = class_map.get(str(s.get("class_id", "")), "")
        # Remove sensitive info
        s.pop("avatar", None)
    
    # Sort by score
    students.sort(key=lambda x: float(x.get("total_score", 0)), reverse=True)
    
    # Add position number
    for i, s in enumerate(students[:limit]):
        s["position"] = i + 1
    
    return students[:limit]


@router.get("/classes")
def get_class_leaderboard(current_user: dict = Depends(get_current_user)):
    """Leaderboard grouped by class - average score per class."""
    students_df = excel_service.read_sheet("HocSinh")
    classes_df = excel_service.read_sheet("LopHoc")
    
    result = []
    for _, cls in classes_df.iterrows():
        class_students = students_df[
            (students_df["class_id"].astype(str) == str(cls["class_id"])) &
            (students_df["status"] != "inactive")
        ]
        if not class_students.empty:
            avg = class_students["total_score"].astype(float).mean()
            result.append({
                "class_id": cls["class_id"],
                "class_name": cls.get("class_name", ""),
                "student_count": len(class_students),
                "avg_score": round(avg, 2),
            })
    
    return sorted(result, key=lambda x: x["avg_score"], reverse=True)
