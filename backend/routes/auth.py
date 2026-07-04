"""Auth routes"""

from fastapi import APIRouter, HTTPException, Depends
from models import RegisterRequest, LoginRequest
from auth_service import AuthService
from deps import get_current_user

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/register")
async def register_user(request: RegisterRequest):
    result = await AuthService.register_user(
        telegram_id=request.telegram_id,
        username=request.username,
        email=request.email
    )
    if not result["ok"]:
        raise HTTPException(status_code=400, detail=result.get("error", "Registration failed"))
    return {"success": True, "user_id": result["user_id"], "token": result["token"]}


@router.post("/login")
async def login_user(request: LoginRequest):
    result = await AuthService.login_telegram(request.telegram_id)
    if not result["ok"]:
        raise HTTPException(status_code=401, detail=result.get("error", "Login failed"))
    return {"success": True, "user_id": result["user_id"], "token": result["token"]}


@router.get("/me")
async def get_current_user_info(user: dict = Depends(get_current_user)):
    return {
        "user_id": user["id"],
        "telegram_id": user["telegram_id"],
        "username": user["username"],
        "kyc_status": user["kyc_status"],
        "risk_level": user["risk_level"],
        "status": user["status"],
        "created_at": user["created_at"]
    }
