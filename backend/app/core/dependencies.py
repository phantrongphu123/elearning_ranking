from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from .security import decode_token
from ..services.excel_service import ExcelService

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/auth/login")
excel_service = ExcelService()


def get_current_user(token: str = Depends(oauth2_scheme)):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Token không hợp lệ hoặc đã hết hạn",
        headers={"WWW-Authenticate": "Bearer"},
    )
    payload = decode_token(token)
    if payload is None:
        raise credentials_exception
    
    user_id = payload.get("user_id")
    role = payload.get("role")
    if user_id is None or role is None:
        raise credentials_exception
    
    # Verify user still exists in DB
    users_df = excel_service.read_sheet("Users")
    user_row = users_df[users_df["user_id"] == user_id]
    if user_row.empty:
        raise credentials_exception
    
    user = user_row.iloc[0].to_dict()
    if user.get("status") != "active":
        raise HTTPException(status_code=403, detail="Tài khoản đã bị vô hiệu hóa")
    
    return user


def require_admin(current_user: dict = Depends(get_current_user)):
    if current_user.get("role") != "admin":
        raise HTTPException(status_code=403, detail="Bạn không có quyền Admin")
    return current_user


def require_teacher_or_admin(current_user: dict = Depends(get_current_user)):
    if current_user.get("role") not in ["admin", "teacher"]:
        raise HTTPException(status_code=403, detail="Chỉ giáo viên hoặc admin mới có quyền này")
    return current_user


def require_student(current_user: dict = Depends(get_current_user)):
    if current_user.get("role") != "student":
        raise HTTPException(status_code=403, detail="Chỉ học sinh mới có quyền này")
    return current_user
