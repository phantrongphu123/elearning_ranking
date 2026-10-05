from fastapi import APIRouter, HTTPException, Depends
from fastapi.security import OAuth2PasswordRequestForm
from pydantic import BaseModel
from datetime import datetime

from ..core.security import verify_password, create_access_token
from ..core.dependencies import get_current_user
from ..services.excel_service import ExcelService

router = APIRouter(prefix="/api/auth", tags=["Authentication"])
excel_service = ExcelService()


class LoginResponse(BaseModel):
    access_token: str
    token_type: str
    user: dict


@router.post("/login")
def login(form_data: OAuth2PasswordRequestForm = Depends()):
    """Login and receive JWT token."""
    users_df = excel_service.read_sheet("Users")
    user_row = users_df[users_df["username"] == form_data.username]
    
    if user_row.empty:
        raise HTTPException(status_code=401, detail="Tên đăng nhập hoặc mật khẩu không đúng")
    
    user = user_row.iloc[0].to_dict()
    
    if not verify_password(form_data.password, user.get("password_hash", "")):
        raise HTTPException(status_code=401, detail="Tên đăng nhập hoặc mật khẩu không đúng")
    
    if user.get("status") != "active":
        raise HTTPException(status_code=403, detail="Tài khoản đã bị vô hiệu hóa")
    
    token_data = {
        "user_id": user["user_id"],
        "username": user["username"],
        "role": user["role"],
        "student_id": user.get("student_id", ""),
    }
    token = create_access_token(token_data)
    
    # Remove sensitive fields before returning
    safe_user = {k: v for k, v in user.items() if k != "password_hash"}
    return {"access_token": token, "token_type": "bearer", "user": safe_user}


@router.get("/me")
def get_me(current_user: dict = Depends(get_current_user)):
    """Get current user info."""
    safe_user = {k: v for k, v in current_user.items() if k != "password_hash"}
    return safe_user


@router.post("/logout")
def logout():
    """Logout (client-side - just a confirmation endpoint)."""
    return {"message": "Đăng xuất thành công"}
